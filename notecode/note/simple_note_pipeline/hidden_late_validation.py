"""Hidden late validation helpers for the simple note pipeline."""
from __future__ import annotations

import re
from typing import Any, Dict, Mapping

from note.simple_note_pipeline.postprocess import DraftSections


_HIDDEN_LATE_VALIDATION_HEADING_EXACT = {
    "後半で確認した戻り先",
    "比較上の読み",
    "最終確認",
    "実装へ戻す場合",
    "最小instruction",
}
_HIDDEN_LATE_VALIDATION_HEADING_CONTAINS = (
    "return target",
    "hidden checklist",
    "editor origin",
    "lead_only",
    "middle_onward",
    "late_35_only",
    "full_rewrite",
)
_HIDDEN_LATE_VALIDATION_BODY_WARNING_CONTAINS = (
    "return target",
    "hidden checklist",
    "editor origin",
    "lead_only",
    "middle_onward",
    "late_35_only",
    "full_rewrite",
    "戻り先",
    "ペルソナ",
    "persona",
    "hidden",
    "checklist",
)
_HIDDEN_LATE_COMPANY_INTRO_TOKEN_PATTERNS = {
    "current_business": re.compile(
        r"(?:事業|サービス|製品|商品|提供|供給|販売|施工|製造|開発|制作|運用|対応|業務|データ|入力|調査|分析|"
        r"SaaS|システム|扱っている|取り扱)"
    ),
    "support_scope": re.compile(
        r"(?:支援範囲|対応範囲|対応分野|支援|サポート|対象|領域|分野|用途|地域|エリア|家庭|法人|産業|医療|住宅)"
    ),
    "process_clue": re.compile(
        r"(?:体制|拠点|設備|営業所|事業所|店舗|工場|担当|部門|保安|検査|配送|販売|施工|製造|供給|"
        r"対応範囲|取扱(?:い|う)|取り扱|サービス説明|製品説明|初回ヒアリング|資料確認|作業範囲|"
        r"入力(?:と|・)?チェック|チェック(?:と|・)?納品|納品確認|運用ルール)"
    ),
    "case_signal": re.compile(r"(?:事例|実績|導入|公式|掲載|お客様|ケース|支援例)"),
    "pre_contact_decision": re.compile(r"(?:相談前|問い合わせ前|依頼前|確認点|確認して|見るべき|そろえ|準備)"),
}
_HIDDEN_LATE_ABSTRACT_CLOSING_RE = re.compile(
    r"(?:重要です|大切です|価値があります|可能性があります|全体像|役立ちます|期待できます|欠かせない|欠かせません)"
)
_HIDDEN_LATE_UNSUPPORTED_GENERAL_VALUE_RE = re.compile(
    r"(?:生活に欠かせ(?:ない|ません)|地域に欠かせ(?:ない|ません)|暮らしに欠かせ(?:ない|ません)|"
    r"欠かせない存在|欠かせません)"
)
_HIDDEN_LATE_COMPANY_INTRO_ROUTE_DRIFT_RE = re.compile(
    r"(?:読者の立場で見ると|最初の接点は|相談前|相談の入口|相談入口|相談窓口|導入手順|"
    r"この会社(?:は|の)|公開情報では)"
)
_HIDDEN_LATE_PRE_CONTACT_SOURCE_RE = re.compile(
    r"(?:相談前|問い合わせ前|依頼前|事前に(?:確認|準備|整理)|確認点|準備しておく|そろえておく)"
)


def _clean_inline_text(value: Any, *, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit > 0 and len(text) > limit:
        return text[:limit].rstrip()
    return text


def _extract_revision_sections(body: Any) -> list[tuple[str, str]]:
    text = str(body or "")
    sections: list[tuple[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("##"):
            if current_heading:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = re.sub(r"^\s*#+\s*", "", stripped).strip()
            current_lines = []
        elif current_heading:
            current_lines.append(line)
    if current_heading:
        sections.append((current_heading, "\n".join(current_lines).strip()))
    return sections


def _build_hidden_late_validation_contract(contract: Mapping[str, Any]) -> Dict[str, Any]:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    active = article_type == "branding" and semantic_key == "company_introduction"
    daily_future_branch = article_type == "daily_story"
    company_intro_operational_contract = contract.get("_company_introduction_source_contract")
    operational_source_contract_active = bool(
        active
        and isinstance(company_intro_operational_contract, Mapping)
        and company_intro_operational_contract.get("scope_match")
    )
    checklist = [
        "current_business",
        "support_scope",
        "process_clue",
        "pre_contact_decision",
    ]
    if active and not operational_source_contract_active:
        checklist.insert(3, "case_signal")
    return {
        "checked": True,
        "scope_match": bool(active),
        "article_type": article_type,
        "semantic_article_key": semantic_key,
        "editor_origin_preference": "full_rewrite_exception_candidate" if active else "",
        "repair_fallback": "late_35_only" if active or daily_future_branch else "",
        "hidden_late_checklist": checklist if active else [],
        "daily_future_branch": bool(daily_future_branch),
    }


def _normalize_hidden_late_heading(value: Any) -> str:
    text = re.sub(r"^\s*#+\s*", "", str(value or "").strip())
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _has_visible_forbidden_heading(body: Any) -> list[str]:
    hits: list[str] = []
    for heading, _section_body in _extract_revision_sections(body):
        normalized = _normalize_hidden_late_heading(heading)
        compact = re.sub(r"\s+", "", normalized).lower()
        if compact in _HIDDEN_LATE_VALIDATION_HEADING_EXACT and normalized not in hits:
            hits.append(normalized)
            continue
        lowered = normalized.lower()
        for marker in _HIDDEN_LATE_VALIDATION_HEADING_CONTAINS:
            if marker in lowered:
                hits.append(normalized)
                break
    return hits[:6]


def _hidden_late_body_leakage_warning_hits(draft: DraftSections) -> list[str]:
    heading_hits = set(_has_visible_forbidden_heading(draft.body))
    body_text = str(draft.body or "")
    body_without_headings = "\n".join(
        line for line in body_text.splitlines() if not line.strip().startswith("##")
    )
    lowered = body_without_headings.lower()
    hits: list[str] = []
    for marker in _HIDDEN_LATE_VALIDATION_BODY_WARNING_CONTAINS:
        if marker.lower() in lowered and marker not in hits:
            hits.append(marker)
    return [hit for hit in hits if hit not in heading_hits][:8]


def _hidden_late_company_intro_route_drift_hits(draft: DraftSections) -> list[str]:
    visible_text = "\n".join(
        [
            str(draft.title or ""),
            str(draft.lead or ""),
            str(draft.body or ""),
        ]
    )
    hits: list[str] = []
    for match in _HIDDEN_LATE_COMPANY_INTRO_ROUTE_DRIFT_RE.finditer(visible_text):
        hit = match.group(0)
        if hit and hit not in hits:
            hits.append(hit)
    return hits[:8]


def _hidden_late_company_intro_route_repair_lines(route_drift_hits: list[str]) -> list[str]:
    if not route_drift_hits:
        return []
    consultation_terms = {
        hit
        for hit in route_drift_hits
        if hit
        in {
            "相談の入口",
            "相談入口",
            "相談窓口",
            "相談前",
            "導入手順",
        }
    }
    lines = [
        "相談導線や読者向けの入口説明へ戻さず、会社紹介として現在の事業内容・扱う製品やサービス・対応範囲・事業の特徴へ戻す。",
        "本文後半の戻り先は、sourceにある範囲の体制・拠点・背景・扱う領域に置き、問い合わせ獲得記事や導入手順記事の流れにしない。",
    ]
    if consultation_terms:
        lines.append(
            "相談系の語が主見出しや段落の軸になっている箇所は、source-backed な問い合わせ窓口を短く触れる場合を除き、事業内容・対応範囲・扱う製品サービスの説明へ置き換える。"
        )
        lines.append(
            "見出しは相談・依頼・導入の手前ではなく、どの業務場面に対応するか、何を扱うか、どこまで支援するか、どんな体制や拠点で担うかを示す表現に戻す。"
        )
    if "この会社は" in route_drift_hits or "この会社の" in route_drift_hits:
        lines.append(
            "「この会社は」「この会社の」のような外側からの説明は、会社名または私たち視点の事業説明へ戻し、第三者レビュー調にしない。"
        )
    return lines[:4]


def _hidden_late_window_text(draft: DraftSections, *, start_ratio: float = 0.50) -> str:
    body = str(draft.body or "").strip()
    if not body:
        return ""
    start = int(len(body) * start_ratio)
    return body[start:].strip()


def _hidden_late_source_text(source_pack: Mapping[str, Any]) -> str:
    parts: list[str] = []
    for item in list(source_pack.get("grounding_items") or []):
        if isinstance(item, Mapping):
            parts.append(str(item.get("fact_text") or ""))
    for item in list(source_pack.get("source_summaries") or []):
        if isinstance(item, Mapping):
            parts.append(str(item.get("excerpt") or ""))
    for item in list(source_pack.get("source_documents") or []):
        if isinstance(item, Mapping):
            parts.append(str(item.get("content") or ""))
    return "\n".join(parts)


def _company_intro_late_operational_closing_rescued(late_tail: str, late_text: str) -> bool:
    window = str(late_text or "")[-360:]
    tail = str(late_tail or "")
    if not _HIDDEN_LATE_ABSTRACT_CLOSING_RE.search(tail):
        return False
    has_business = bool(
        re.search(r"(?:事業|サービス|製品|商品|供給|販売|施工|製造|業務|データ|入力|調査|分析|SaaS|支援)", window)
    )
    has_support = bool(re.search(r"(?:支援範囲|対応範囲|対応分野|対象|領域|用途|地域|家庭|法人|産業|医療|住宅)", window))
    has_operational_context = bool(
        re.search(
            r"(?:体制|拠点|設備|営業所|事業所|店舗|工場|保安|検査|配送|販売|施工|製造|供給|"
            r"資料確認|作業範囲|入力(?:と|・)?チェック|チェック(?:と|・)?納品|納品確認|運用ルール)",
            window,
        )
    )
    return bool(has_business and has_support and has_operational_context)


def _hidden_late_required_tokens(
    validation_contract: Mapping[str, Any],
    source_pack: Mapping[str, Any],
) -> list[str]:
    tokens = list(validation_contract.get("hidden_late_checklist") or [])
    source_text = _hidden_late_source_text(source_pack)
    source_optional_tokens = {"case_signal", "pre_contact_decision"}
    required: list[str] = []
    for token in tokens:
        pattern = _HIDDEN_LATE_COMPANY_INTRO_TOKEN_PATTERNS.get(str(token))
        if token == "case_signal" and not re.search(r"(?:事例|実績|ケース|支援例|掲載)", source_text):
            continue
        if token == "pre_contact_decision" and not _HIDDEN_LATE_PRE_CONTACT_SOURCE_RE.search(source_text):
            continue
        if token in source_optional_tokens and pattern and not pattern.search(source_text):
            continue
        required.append(str(token))
    return required


def _hidden_late_validation_failure_count(validation: Mapping[str, Any]) -> int:
    return len(list(validation.get("failed_tokens") or [])) + len(
        list(validation.get("visible_forbidden_heading_hits") or [])
    ) + len(list(validation.get("repair_trigger_ids") or []))


def _hidden_late_validation_improved(
    current: Mapping[str, Any],
    repaired: Mapping[str, Any],
) -> bool:
    if not bool(current.get("scope_match")):
        return True
    if list(repaired.get("visible_forbidden_heading_hits") or []):
        return False
    return _hidden_late_validation_failure_count(repaired) < _hidden_late_validation_failure_count(current)


def _evaluate_hidden_late_validation(
    contract: Mapping[str, Any],
    draft: DraftSections,
    diagnostics: Dict[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    validation_contract = _build_hidden_late_validation_contract(contract)
    validation: Dict[str, Any] = {
        "checked": bool(validation_contract.get("checked")),
        "scope_match": bool(validation_contract.get("scope_match")),
        "editor_origin_preference": str(validation_contract.get("editor_origin_preference") or ""),
        "repair_fallback": str(validation_contract.get("repair_fallback") or ""),
        "failed_tokens": [],
        "visible_forbidden_heading_hits": _has_visible_forbidden_heading(draft.body),
        "body_leakage_warning_hits": _hidden_late_body_leakage_warning_hits(draft),
        "repair_trigger_ids": [],
        "unsupported_general_value_hits": [],
        "company_intro_route_drift_hits": [],
        "abstract_closing_operational_rescued": False,
        "daily_future_branch": bool(validation_contract.get("daily_future_branch")),
    }
    if not bool(validation_contract.get("scope_match")):
        return validation

    late_text = _hidden_late_window_text(draft, start_ratio=0.35)
    failed_tokens: list[str] = []
    for token in _hidden_late_required_tokens(validation_contract, source_pack):
        pattern = _HIDDEN_LATE_COMPANY_INTRO_TOKEN_PATTERNS.get(str(token))
        if pattern and not pattern.search(late_text):
            failed_tokens.append(str(token))
    validation["failed_tokens"] = failed_tokens

    trigger_ids: list[str] = []
    if any(token in failed_tokens for token in ("current_business", "support_scope")):
        trigger_ids.append("late_source_fact_missing")
    if "process_clue" in failed_tokens:
        trigger_ids.append("concrete_process_missing")
    if "pre_contact_decision" in failed_tokens:
        trigger_ids.append("decision_condition_missing")
    if "case_signal" in failed_tokens:
        trigger_ids.append("case_evidence_missing")
    late_tail = late_text[-220:]
    unsupported_general_value_hits: list[str] = []
    source_text = _hidden_late_source_text(source_pack)
    for match in _HIDDEN_LATE_UNSUPPORTED_GENERAL_VALUE_RE.finditer(late_text):
        hit = match.group(0)
        if hit and hit not in source_text and hit not in unsupported_general_value_hits:
            unsupported_general_value_hits.append(hit)
    if unsupported_general_value_hits:
        validation["unsupported_general_value_hits"] = unsupported_general_value_hits[:6]
        trigger_ids.append("unsupported_general_value_phrase")
    route_drift_hits = _hidden_late_company_intro_route_drift_hits(draft)
    if route_drift_hits:
        validation["company_intro_route_drift_hits"] = route_drift_hits
        trigger_ids.append("company_intro_route_drift_phrase")
    if _HIDDEN_LATE_ABSTRACT_CLOSING_RE.search(late_tail):
        abstract_closing_rescued = _company_intro_late_operational_closing_rescued(late_tail, late_text)
        validation["abstract_closing_operational_rescued"] = bool(abstract_closing_rescued)
        if not abstract_closing_rescued:
            trigger_ids.append("abstract_closing_phrase_hit")
    if validation["visible_forbidden_heading_hits"]:
        trigger_ids.append("visible_forbidden_heading_hit")
    validation["repair_trigger_ids"] = trigger_ids

    if not trigger_ids:
        return validation

    repair_instructions: list[str] = []
    for item in list(diagnostics.get("repair_instructions") or []):
        text = str(item or "").strip()
        if text and text not in repair_instructions:
            repair_instructions.append(text)
    base_repair_lines = [
        "本文後半を、現在の事業内容・扱っている製品やサービス・対応範囲・事業の特徴・sourceにある範囲の体制や拠点、背景へ戻す。",
        *_hidden_late_company_intro_route_repair_lines(route_drift_hits),
        "sourceにない社会的価値や効能を足さず、一般価値語で会社を持ち上げない。",
        "検査用語や編集用語を見出しに出さず、自然な記事見出しと本文表現へ置き換える。",
    ]
    for line in base_repair_lines:
        if line not in repair_instructions:
            repair_instructions.append(line)
    diagnostics["repair_instructions"] = repair_instructions[:12]

    soft_warnings: list[str] = []
    for item in list(diagnostics.get("soft_warnings") or []):
        text = str(item or "").strip()
        if text and text not in soft_warnings:
            soft_warnings.append(text)
    if "hidden_late_validation:company_intro" not in soft_warnings:
        soft_warnings.append("hidden_late_validation:company_intro")
    diagnostics["soft_warnings"] = soft_warnings[:14]
    diagnostics["repair_trigger_score"] = max(float(diagnostics.get("repair_trigger_score") or 0.0), 0.61)
    diagnostics["repair_required"] = True
    diagnostics["issue_count"] = max(
        int(diagnostics.get("issue_count", 0) or 0),
        len(repair_instructions),
        len(soft_warnings),
        len(trigger_ids),
    )
    diagnostics["severity"] = max(int(diagnostics.get("severity", 0) or 0), 2)
    return validation
