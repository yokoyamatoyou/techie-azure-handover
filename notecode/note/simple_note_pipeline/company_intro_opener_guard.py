"""Visible opener guard helpers for company introduction output."""
from __future__ import annotations

import re
from typing import Any, Dict, Mapping

from note.simple_note_pipeline.company_intro_source_contract_guard import (
    _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS,
)
from note.simple_note_pipeline.postprocess import DraftSections


_SHADOW_TOKEN_RE = re.compile(r"[一-龥]{2,}|[ぁ-ん]{2,}|[ァ-ヴー]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}")
_OPENER_GUARD_STOP_TOKENS = {"会社", "企業", "紹介", "現在"}
_COMPANY_INTRO_HISTORY_MARKER_RE = re.compile(r"(?:創業|沿革|歩み|歴史|先代|代目|年超|年余り|受け継|明治|昭和|1885|1964|130年)")


def _clean_inline_text(value: Any, *, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit > 0 and len(text) > limit:
        return text[:limit].rstrip()
    return text


def _extract_shadow_tokens(value: Any, *, limit: int = 4) -> list[str]:
    tokens: list[str] = []
    for token in _SHADOW_TOKEN_RE.findall(_clean_inline_text(value or "", limit=240)):
        normalized = token.lower().strip()
        if re.fullmatch(r"[ぁ-ん]{2,}", normalized):
            continue
        if not normalized or normalized in tokens:
            continue
        tokens.append(normalized)
        if len(tokens) >= limit:
            break
    return tokens


def _text_hits_shadow(value: Any, tokens: list[str]) -> bool:
    normalized = _clean_inline_text(value or "", limit=1600).lower()
    return bool(tokens) and any(token in normalized for token in tokens)


def _split_heading_sections(body: Any) -> list[Dict[str, str]]:
    sections: list[Dict[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []
    for raw_line in str(body or "").replace("\r\n", "\n").replace("\r", "\n").splitlines():
        matched = re.match(r"^##\s+(.+)$", raw_line.strip())
        if matched:
            if current_heading:
                sections.append({"heading": current_heading, "body": "\n".join(current_lines).strip()})
            current_heading = matched.group(1).strip()
            current_lines = []
            continue
        if current_heading:
            current_lines.append(raw_line)
    if current_heading:
        sections.append({"heading": current_heading, "body": "\n".join(current_lines).strip()})
    return sections


def _build_section_shadow_entries(
    contract: Mapping[str, Any],
    compact_plan: list[Dict[str, str]] | None,
) -> list[Dict[str, str]]:
    shadow_spec_inputs = contract.get("_shadow_spec_inputs") if isinstance(contract.get("_shadow_spec_inputs"), Mapping) else None
    if not isinstance(shadow_spec_inputs, Mapping):
        return []
    main_focus = _clean_inline_text(shadow_spec_inputs.get("main_focus") or "", limit=72)
    support_points = [
        _clean_inline_text(item, limit=40)
        for item in list(shadow_spec_inputs.get("support_points") or [])[:3]
        if _clean_inline_text(item, limit=40)
    ]
    comparison_axes = [
        _clean_inline_text(item, limit=32)
        for item in list(shadow_spec_inputs.get("comparison_axes") or [])[:2]
        if _clean_inline_text(item, limit=32)
    ]
    source_fact_pool = [
        _clean_inline_text(item, limit=96)
        for item in list(shadow_spec_inputs.get("source_fact_pool") or [])[:6]
        if _clean_inline_text(item, limit=96)
    ]
    entries: list[Dict[str, str]] = []
    for index, item in enumerate(list(compact_plan or [])[:6], start=1):
        heading = _clean_inline_text(item.get("heading") or "", limit=40)
        claim = _clean_inline_text(item.get("claim") or item.get("key_message") or "", limit=72)
        if not heading:
            continue
        entries.append(
            {
                "heading": heading,
                "focus": main_focus,
                "claim": claim,
                "support": support_points[min(index - 1, len(support_points) - 1)] if support_points else "",
                "axes": " / ".join(comparison_axes[:2]) if comparison_axes else "",
                "fact": source_fact_pool[min(index - 1, len(source_fact_pool) - 1)] if source_fact_pool else "",
            }
        )
    return entries


def _company_intro_operational_identity_heading(heading: str) -> bool:
    text = _clean_inline_text(heading, limit=100)
    if not text or _COMPANY_INTRO_HISTORY_MARKER_RE.search(text):
        return False
    if not any(token in text for token in ("株式会社", "有限会社", "合同会社", "京都工業")):
        return False
    identity_descriptor_hit = bool(
        "とは" in text
        and re.search(r"(?:データ入力|入力支援|分析|センター|支援)", text)
    )
    if identity_descriptor_hit:
        return True
    if "会社" not in text:
        return False
    question_hit = any(token in text for token in ("何を", "なにを", "どんな", "どのような"))
    action_hit = any(
        token in text
        for token in ("担う", "支援", "している", "頼める", "任せられる", "できる")
    )
    return bool(question_hit and action_hit)


def _evaluate_company_intro_visible_opener_drift(
    contract: Mapping[str, Any],
    draft: DraftSections,
    compact_plan: list[Dict[str, str]] | None,
    diagnostics: Mapping[str, Any],
    controlled_realization: Mapping[str, Any],
) -> Dict[str, Any]:
    evaluation: Dict[str, Any] = {
        "failed": False,
        "scope_match": False,
        "title_history_first": False,
        "title_history_first_triggered": False,
        "first_section_history_first": False,
        "first_section_history_first_triggered": False,
        "global_focus_aligned": bool(controlled_realization.get("global_focus_aligned", True)),
        "opener_heading_drift": False,
        "shadow_opener_heading_drift": False,
        "visible_opener_heading_drift": False,
        "visible_opener_heading_operational_rescued": False,
        "opener_tokens_sample": [],
        "drift_headings": [],
        "lead_opening_opener_focus_hit": False,
        "first_heading": "",
        "shadow_first_heading": "",
        "visible_first_heading": "",
        "source_required_slots_covered": False,
        "visible_required_slots_covered": False,
        "global_focus_rescued": False,
        "global_focus_failed": False,
    }
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    if article_type != "branding" or semantic_key != "company_introduction":
        return evaluation
    evaluation["scope_match"] = True
    if not bool(controlled_realization.get("active")) or not bool(diagnostics.get("repair_required")):
        return evaluation
    if (
        int(diagnostics.get("shadow_drift_count", 0) or 0) <= 0
        and int(diagnostics.get("heading_reanchor_miss_count", 0) or 0) <= 0
    ):
        return evaluation

    shadow_entries = _build_section_shadow_entries(contract, compact_plan)
    first_entry = shadow_entries[0] if shadow_entries else {}
    opener_tokens: list[str] = []
    for value in (
        first_entry.get("focus"),
        first_entry.get("claim"),
        first_entry.get("support"),
        first_entry.get("fact"),
        first_entry.get("heading"),
    ):
        for token in _extract_shadow_tokens(value, limit=4):
            if token in _OPENER_GUARD_STOP_TOKENS:
                continue
            if token not in opener_tokens:
                opener_tokens.append(token)
            if len(opener_tokens) >= 8:
                break
        if len(opener_tokens) >= 8:
            break

    sections = _split_heading_sections(draft.body)
    first_section = sections[0] if sections else {}
    shadow_first_heading = str(first_entry.get("heading") or "").strip()
    visible_first_heading = str(first_section.get("heading") or "").strip()
    first_heading = visible_first_heading or shadow_first_heading
    drift_headings = [
        str(item or "").strip()
        for item in list(controlled_realization.get("drift_headings") or [])
        if str(item or "").strip()
    ]
    title_history_first = bool(_COMPANY_INTRO_HISTORY_MARKER_RE.search(str(draft.title or ""))) and (
        not opener_tokens or not _text_hits_shadow(draft.title, opener_tokens)
    )
    first_section_surface = f"{first_section.get('heading', '')}\n{str(first_section.get('body') or '')[:220]}"
    first_section_history_first = bool(_COMPANY_INTRO_HISTORY_MARKER_RE.search(first_section_surface)) and (
        not opener_tokens or not _text_hits_shadow(first_section_surface, opener_tokens)
    )
    visible_opener_heading_drift = bool(visible_first_heading) and visible_first_heading in drift_headings
    shadow_opener_heading_drift = bool(shadow_first_heading) and shadow_first_heading in drift_headings
    global_focus_aligned = bool(controlled_realization.get("global_focus_aligned", True))

    lead_text = str(getattr(draft, "lead", "") or "")
    opening_body = str(first_section.get("body") or "")[:280]
    lead_opening_surface = f"{lead_text}\n{opening_body}".strip()
    lead_opening_opener_focus_hit = bool(opener_tokens) and _text_hits_shadow(
        lead_opening_surface, opener_tokens
    )

    title_history_first_triggered = bool(title_history_first) and not lead_opening_opener_focus_hit
    first_section_history_first_triggered = (
        bool(first_section_history_first) and not lead_opening_opener_focus_hit
    )

    source_validation = dict(diagnostics.get("company_introduction_source_contract_validation") or {})
    required_slots = list(source_validation.get("required_slots") or _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS)
    source_slot_presence = dict(source_validation.get("source_slot_presence") or {})
    visible_slot_presence = dict(source_validation.get("slot_presence") or {})
    source_required_slots_covered = bool(required_slots) and all(
        bool(source_slot_presence.get(slot)) for slot in required_slots
    )
    visible_required_slots_covered = bool(required_slots) and all(
        bool(visible_slot_presence.get(slot)) for slot in required_slots
    )
    global_focus_rescued = bool(
        not global_focus_aligned
        and lead_opening_opener_focus_hit
        and source_required_slots_covered
        and visible_required_slots_covered
        and not title_history_first_triggered
        and not first_section_history_first_triggered
    )
    visible_opener_heading_operational_rescued = bool(
        visible_opener_heading_drift
        and _company_intro_operational_identity_heading(visible_first_heading)
        and lead_opening_opener_focus_hit
        and source_required_slots_covered
        and visible_required_slots_covered
        and not title_history_first_triggered
        and not first_section_history_first_triggered
    )
    opener_heading_drift = bool(
        visible_opener_heading_drift and not visible_opener_heading_operational_rescued
    )
    global_focus_failed = bool(not global_focus_aligned and not global_focus_rescued)

    failed = bool(
        opener_heading_drift
        or global_focus_failed
        or title_history_first_triggered
        or first_section_history_first_triggered
    )

    evaluation.update(
        {
            "failed": failed,
            "title_history_first": bool(title_history_first),
            "title_history_first_triggered": bool(title_history_first_triggered),
            "first_section_history_first": bool(first_section_history_first),
            "first_section_history_first_triggered": bool(first_section_history_first_triggered),
            "global_focus_aligned": bool(global_focus_aligned),
            "global_focus_rescued": bool(global_focus_rescued),
            "global_focus_failed": bool(global_focus_failed),
            "opener_heading_drift": bool(opener_heading_drift),
            "shadow_opener_heading_drift": bool(shadow_opener_heading_drift),
            "visible_opener_heading_drift": bool(visible_opener_heading_drift),
            "visible_opener_heading_operational_rescued": bool(
                visible_opener_heading_operational_rescued
            ),
            "opener_tokens_sample": list(opener_tokens[:6]),
            "drift_headings": list(drift_headings[:4]),
            "lead_opening_opener_focus_hit": bool(lead_opening_opener_focus_hit),
            "first_heading": first_heading,
            "shadow_first_heading": shadow_first_heading,
            "visible_first_heading": visible_first_heading,
            "source_required_slots_covered": bool(source_required_slots_covered),
            "visible_required_slots_covered": bool(visible_required_slots_covered),
        }
    )
    return evaluation


def _company_intro_visible_opener_drift_failed(
    contract: Mapping[str, Any],
    draft: DraftSections,
    compact_plan: list[Dict[str, str]] | None,
    diagnostics: Mapping[str, Any],
    controlled_realization: Mapping[str, Any],
) -> bool:
    evaluation = _evaluate_company_intro_visible_opener_drift(
        contract,
        draft,
        compact_plan,
        diagnostics,
        controlled_realization,
    )
    return bool(evaluation.get("failed"))
