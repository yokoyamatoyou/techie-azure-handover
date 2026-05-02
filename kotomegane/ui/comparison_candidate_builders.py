from __future__ import annotations

import re
import unicodedata
from typing import Any

from analysis_lib import normalize_text, parse_json_object
from config import AppConfig

_TITLE_SPLIT_RE = re.compile(r"[|｜/／]+")
_ORG_RE = re.compile(r"((?:株式会社|合同会社|有限会社)\s*[一-龯ぁ-んァ-ヶーA-Za-z0-9・&._-]{2,28})")
_GROUP_RE = re.compile(r"([一-龯ぁ-んァ-ヶーA-Za-z0-9・&._-]{2,28}(?:協会|連盟|機構|学会|財団|会議所))")
_ASCII_NAME_RE = re.compile(r"\b([A-Z][A-Za-z0-9&.+_-]{2,24})\b")


def _normalize_token(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip(" 　|｜-‐/／")


def _normalize_lookup(value: Any) -> str:
    return normalize_text(_normalize_token(value)).lower()


def _dedupe_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    ordered: list[dict[str, Any]] = []
    for item in items:
        key = _normalize_lookup(item.get("name"))
        if key and key not in seen:
            ordered.append(item)
            seen.add(key)
    return ordered


def _should_skip_name(name: str, config: AppConfig, own_names: set[str]) -> bool:
    lookup = _normalize_lookup(name)
    if not lookup or len(lookup) <= 1:
        return True
    if lookup in own_names:
        return True
    if lookup in {"公式", "ホーム", "トップ", "詳細", "比較", "料金", "faq", "導入事例", "事例"}:
        return True
    if "の" in lookup and len(lookup) >= 10:
        return True
    if any(marker in lookup for marker in {"評判", "料金", "比較", "事例", "実績", "方法", "使い方"}) and len(lookup) >= 8:
        return True
    for brand in config.brand_terms or []:
        brand_lookup = _normalize_lookup(brand)
        if brand_lookup and (lookup == brand_lookup or brand_lookup in lookup or lookup in brand_lookup):
            return True
    return False


def _extract_title_segments(title: str) -> list[str]:
    segments = [_normalize_token(part) for part in _TITLE_SPLIT_RE.split(_normalize_token(title))]
    return [segment for segment in segments if segment]


def _classify_candidate_kind(name: str, item: dict[str, Any] | None = None) -> str:
    lookup = _normalize_lookup(name)
    host = _normalize_lookup((item or {}).get("host"))
    if any(marker in lookup for marker in {"比較", "ランキング", "レビュー", "口コミ", "ナビ", "幹事"}):
        return "比較サイト"
    if any(marker in lookup for marker in {"協会", "連盟", "機構", "学会", "財団", "会議所"}):
        return "団体"
    if any(marker in lookup for marker in {"株式会社", "合同会社", "有限会社", "inc", "corp", "llc"}):
        return "法人"
    if any(marker in host for marker in {"news", "media", "magazine", "journal"}) or any(marker in lookup for marker in {"メディア", "ニュース"}):
        return "媒体"
    if (item or {}).get("owner_bucket") == "competitor":
        return "法人"
    return "媒体"


def _extract_names_from_text(text: str) -> list[str]:
    normalized = _normalize_token(text)
    if not normalized:
        return []
    names: list[str] = []
    names.extend(_ORG_RE.findall(normalized))
    names.extend(_GROUP_RE.findall(normalized))
    for match in _ASCII_NAME_RE.findall(normalized):
        if match.lower() in {"faq", "web", "chatgpt"}:
            continue
        names.append(match)
    return [_normalize_token(name) for name in names if _normalize_token(name)]


def build_comparison_candidate_summary(
    rows: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
    config: AppConfig,
) -> dict[str, list[dict[str, Any]]]:
    own_names = {_normalize_lookup(item) for item in config.brand_terms or [] if _normalize_lookup(item)}
    own_names.update({_normalize_lookup(config.target_domain)})

    manual_targets = _dedupe_candidates(
        [
            {"name": _normalize_token(term), "kind": "比較対象", "source": "手入力"}
            for term in config.competitor_terms or []
            if _normalize_token(term)
        ]
    )

    observed: list[dict[str, Any]] = []
    manual_lookups = {_normalize_lookup(item.get("name")) for item in manual_targets}

    for item in evidence_items:
        if str(item.get("owner_bucket") or "") == "self":
            continue
        candidate_names = _extract_title_segments(str(item.get("title") or ""))
        candidate_names.extend(_extract_names_from_text(str(item.get("title") or "")))
        for name in candidate_names[:4]:
            if _should_skip_name(name, config, own_names):
                continue
            if _normalize_lookup(name) in manual_lookups:
                continue
            observed.append(
                {
                    "name": name,
                    "kind": _classify_candidate_kind(name, item),
                    "source": "引用URL" if str(item.get("status") or "") == "cited" else "候補URL",
                }
            )

    for row in rows:
        payload = parse_json_object(row.get("output_json"))
        for name in _extract_names_from_text(str(payload.get("answer_text") or payload.get("answer_snapshot") or "")):
            if _should_skip_name(name, config, own_names):
                continue
            if _normalize_lookup(name) in manual_lookups:
                continue
            observed.append({"name": name, "kind": _classify_candidate_kind(name), "source": "回答"})

    observed = _dedupe_candidates(observed)
    return {
        "manual_targets": manual_targets[:4],
        "observed_candidates": observed[:6],
    }
