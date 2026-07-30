from __future__ import annotations

import re
from typing import Any

from app.services.reader_meta_sentence import ISSUE_REASONS, classify_reader_meta_sentence
from app.services.schema_validator import validate_payload
from app.services.stylometry import analyze_text
from app.services.human_visible_surface_gate import (
    is_human_visible_surface_gate_enabled,
    surface_gate_quality_issues,
)


RISKY_PHRASES = ["いかがでしたでしょうか", "〜と言えるでしょう", "ぜひ参考にしてみてください"]
OUTSIDE_REVIEW_MARKERS = (
    "公式サイトを見て",
    "公式サイトの記述",
    "公式サイト全体",
    "公式サイトを確認",
    "会社情報ページでは",
    "沿革では",
    "トップページでは",
    "と案内しています",
    "と記載されています",
    "と紹介しています",
)
class JapaneseQualityChecker:
    def check(
        self,
        article_text: str,
        article_brief: dict[str, Any],
        knowledge_pack: dict[str, Any],
    ) -> dict[str, Any]:
        brief = article_brief["article_brief"]
        stylometry = analyze_text(article_text)
        issues: list[dict[str, Any]] = []
        for candidate in stylometry["issue_candidates"]:
            issues.append(
                {
                    "type": candidate["type"],
                    "severity": candidate["severity"],
                    "text": "",
                    "reason": candidate["reason"],
                    "fix_instruction": "該当箇所だけを調整する",
                    "claim_ids": [],
                }
            )
        for phrase in RISKY_PHRASES:
            if phrase in article_text:
                issues.append(
                    {
                        "type": "ai_like_phrase",
                        "severity": "medium",
                        "text": phrase,
                        "reason": "定型的なAI風表現です",
                        "fix_instruction": "記事固有の表現に置き換える",
                        "claim_ids": [],
                    }
                )
        narrator = brief["narrator"]
        variants = [term for term in ("私たち", "当社", "弊社", "当店") if term in article_text]
        if narrator not in variants and variants:
            issues.append(
                {
                    "type": "first_person_inconsistency",
                    "severity": "high",
                    "text": ",".join(variants),
                    "reason": "brief の narrator と本文の一人称が一致していません",
                    "fix_instruction": f"一人称を{narrator}に統一する",
                    "claim_ids": [],
                }
            )
        owner = str(brief.get("self_viewpoint_owner") or "").strip()
        if brief.get("viewpoint_mode") == "self_perspective" and owner:
            mismatch_text = _viewpoint_owner_mismatch_text(article_text, narrator, owner)
            if mismatch_text:
                issues.append(
                    {
                        "type": "viewpoint_owner_mismatch",
                        "severity": "high",
                        "text": mismatch_text,
                        "reason": "会社本人の自己視点ではなく、対象会社を外から読んで紹介する文体になっています",
                        "fix_instruction": f"{narrator}を{owner}本人の声として書き直す",
                        "claim_ids": [],
                    }
                )
        for sentence in _sentences(article_text):
            for issue_type in classify_reader_meta_sentence(sentence):
                issues.append(
                    {
                        "type": issue_type,
                        "severity": "medium",
                        "text": sentence.strip(),
                        "reason": ISSUE_REASONS[issue_type],
                        "fix_instruction": "読者理解の案内だけの文を削り、隣接する事実文を残す",
                        "claim_ids": [],
                    }
                )
        if _has_route_v_floor(brief):
            body_chars = _body_char_count(article_text)
            floor_chars = int(brief.get("body_length_floor_chars") or 0)
            if body_chars < floor_chars:
                issues.append(
                    {
                        "type": "body_length_below_floor",
                        "severity": "high",
                        "text": f"{body_chars}/{floor_chars}",
                        "reason": "本文がarticle_briefのbody_length_floor_charsを下回っています",
                        "fix_instruction": "source-backedな段落展開を増やし、本文をfloor以上にする",
                        "claim_ids": [],
                    }
                )
            if not _has_h1(article_text):
                issues.append(
                    {
                        "type": "missing_h1",
                        "severity": "high",
                        "text": "",
                        "reason": "Markdown本文にH1見出しがありません",
                        "fix_instruction": "記事冒頭に1つだけH1見出しを置く",
                        "claim_ids": [],
                    }
                )
        if is_human_visible_surface_gate_enabled(article_brief):
            issues.extend(surface_gate_quality_issues(article_text))
        score = max(0, 100 - len(issues) * 8)
        result = {"quality_check": {"pass": not issues, "score": score, "issues": issues, "rewrite_needed": bool(issues), "stylometry": stylometry}}
        validate_payload("quality_check.schema.json", result)
        return result


def _viewpoint_owner_mismatch_text(article_text: str, narrator: str, owner: str) -> str:
    head = article_text[:2500]
    for marker in OUTSIDE_REVIEW_MARKERS:
        if marker in head:
            return marker
    owner_pattern = re.escape(owner)
    patterns = (
        rf"{re.escape(narrator)}が[^。]{{0,40}}{owner_pattern}[^。]{{0,30}}(?:紹介|整理|確認)",
        rf"{owner_pattern}について[^。]{{0,40}}{re.escape(narrator)}[^。]{{0,30}}(?:紹介|整理|確認)",
    )
    for pattern in patterns:
        match = re.search(pattern, head)
        if match:
            return match.group(0)
    return ""


def _sentences(text: str) -> list[str]:
    return [part for part in re.split(r"(?<=[。！？!?])", text) if part.strip()]


def _has_route_v_floor(brief: dict[str, Any]) -> bool:
    try:
        return int(brief.get("body_length_floor_chars") or 0) > 0
    except (TypeError, ValueError):
        return False


def _body_char_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def _has_h1(text: str) -> bool:
    return any(line.startswith("# ") for line in str(text or "").splitlines())
