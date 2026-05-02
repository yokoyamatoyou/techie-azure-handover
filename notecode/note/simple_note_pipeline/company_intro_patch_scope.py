from __future__ import annotations

import re
from typing import Any, Mapping

from note.simple_note_pipeline.postprocess import DraftSections


_ROUTE_DRIFT_PHRASE_RE = re.compile(
    r"(?:相談の入口|相談入口|相談前|相談窓口|導入手順|最初の接点|読者の立場で見ると|この会社は|公開情報では)"
)
_INTERNAL_VISIBLE_RE = re.compile(
    r"(?:SYS_[A-Z0-9_]+|source_grounding|contract_alignment|must_cover|PATCH_SCOPE|persona|trial|hidden)",
    re.IGNORECASE,
)
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[一-龥ぁ-んァ-ヶー]{2,}")


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _surface(value: Any) -> str:
    return _clean_text(value).lower()


def _route_phrase_count(value: Any) -> int:
    return len(_ROUTE_DRIFT_PHRASE_RE.findall(str(value or "")))


def has_company_intro_route_drift_phrase(value: Any) -> bool:
    return bool(_ROUTE_DRIFT_PHRASE_RE.search(str(value or "")))


def _extract_sections(body: Any) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    for matched in re.finditer(r"^##\s+(.+?)\s*\n(.*?)(?=^##\s+|\Z)", str(body or ""), flags=re.MULTILINE | re.DOTALL):
        heading = _clean_text(matched.group(1))
        section_body = str(matched.group(2) or "").strip()
        if heading:
            sections.append((heading, section_body))
    return sections


def _slot_presence(validation: Mapping[str, Any], slot: str) -> bool:
    slot_presence = validation.get("slot_presence")
    if isinstance(slot_presence, Mapping) and slot in slot_presence:
        return bool(slot_presence.get(slot))
    source_slot_presence = validation.get("source_slot_presence")
    if isinstance(source_slot_presence, Mapping) and slot in source_slot_presence:
        return bool(source_slot_presence.get(slot))
    return True


def _hard_guard_clear(validation: Mapping[str, Any]) -> bool:
    if not validation:
        return True
    if validation.get("unsupported_claim_added"):
        return False
    if validation.get("source_limit_visible_leakage"):
        return False
    if validation.get("visible_leakage_hits"):
        return False
    if validation.get("hard_trigger_ids"):
        return False
    return True


def _alignment_not_worse(
    current: Mapping[str, Any],
    repaired: Mapping[str, Any],
) -> bool:
    tolerances = {
        "must_cover_reflection_rate": 0.01,
        "prompt_anchor_coverage": 0.01,
        "section_focus_coverage": 0.01,
        "source_trace_coverage": 0.01,
        "source_grounding_score": 0.01,
    }
    for key, tolerance in tolerances.items():
        if key not in current or key not in repaired:
            continue
        try:
            before = float(current.get(key) or 0.0)
            after = float(repaired.get(key) or 0.0)
        except (TypeError, ValueError):
            continue
        if after + tolerance < before:
            return False
    return True


def _section_overlap_ok(current_body: str, repaired_body: str) -> bool:
    current_surface = _surface(current_body)
    repaired_surface = _surface(repaired_body)
    if not current_surface or not repaired_surface:
        return False
    length_ratio = len(repaired_surface) / max(1, len(current_surface))
    if length_ratio < 0.55 or length_ratio > 2.5:
        return False
    current_tokens = set(_TOKEN_RE.findall(current_surface))
    repaired_tokens = set(_TOKEN_RE.findall(repaired_surface))
    if not current_tokens or not repaired_tokens:
        return False
    return (len(current_tokens & repaired_tokens) / max(1, len(current_tokens))) >= 0.45


def build_company_intro_patch_scope_prompt_lines(
    *,
    article_type: str,
    semantic_key: str,
    lead: str,
    body: str,
    flagged_spans: list[Mapping[str, Any]] | None = None,
) -> list[str]:
    if str(article_type or "").strip().lower() != "branding":
        return []
    if str(semantic_key or "").strip().lower() != "company_introduction":
        return []
    issue_types = {
        str(item.get("issue_type") or "").strip()
        for item in flagged_spans or []
        if str(item.get("issue_type") or "").strip()
    }
    if "company_intro_fingerprint_flatness" not in issue_types:
        return []
    headings = [heading for heading, _body in _extract_sections(body)]
    if len(headings) < 2:
        return []
    affected_headings = [heading for heading in headings if has_company_intro_route_drift_phrase(heading)]
    lead_has_route_drift = has_company_intro_route_drift_phrase(lead)
    if not lead_has_route_drift and not affected_headings:
        return [
            "surface_rhythm_patch=TITLE / LEAD / HASHTAGS は一字一句そのまま保持する。",
            "surface_rhythm_patch=見出し列をこの順番で固定する: " + " / ".join(headings[:6]),
            "surface_rhythm_patch=見出し名は一字一句変えない。見出しの改名・追加・削除・並べ替えをしない。",
            "surface_rhythm_patch=本文だけを直し、資料にない成果・価格・顧客名・比較優位・手順を足さない。",
            "surface_rhythm_patch=対象見出しでは文長、段落長、文末、読点位置だけを散らし、論点を別見出しへ移動しない。",
        ]

    lines = [
        "surface_rhythm_patch=TITLE / HASHTAGS は一字一句そのまま保持する。",
        "surface_rhythm_patch=見出し列の順番と数は固定する: " + " / ".join(headings[:6]),
        "surface_rhythm_patch=本文は対象見出し内だけを直し、資料にない成果・価格・顧客名・比較優位・手順を足さない。",
        "surface_rhythm_patch=会社紹介の主軸は事業内容、製品サービス、対応範囲、事業の特徴に戻す。",
    ]
    if lead_has_route_drift:
        lines.append("surface_rhythm_patch=LEAD は事業内容と対応範囲が残る範囲で、相談導線中心にならない短いリードへ直してよい。")
    if affected_headings:
        lines.append("surface_rhythm_patch=改名してよい見出しは相談導線中心の見出しだけ: " + " / ".join(affected_headings[:4]))
    return lines


def evaluate_company_intro_patch_scope(
    *,
    contract: Mapping[str, Any],
    current_draft: DraftSections,
    repaired_draft: DraftSections,
    current_diagnostics: Mapping[str, Any],
    repaired_diagnostics: Mapping[str, Any],
    target_headings: list[str] | None = None,
    max_changed_headings: int = 4,
) -> dict[str, Any]:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    scope_match = article_type == "branding" and semantic_key == "company_introduction"
    decision: dict[str, Any] = {
        "scope_match": scope_match,
        "allowed": False,
        "reason": "",
        "lead_route_drift_before": has_company_intro_route_drift_phrase(current_draft.lead),
        "lead_changed": _surface(current_draft.lead) != _surface(repaired_draft.lead),
        "changed_heading_count": 0,
        "route_phrase_count_before": 0,
        "route_phrase_count_after": 0,
    }
    if not scope_match:
        decision["reason"] = "inactive_scope"
        return decision
    if _surface(current_draft.title) != _surface(repaired_draft.title):
        decision["reason"] = "title_changed"
        return decision
    if _surface(current_draft.hashtags) != _surface(repaired_draft.hashtags):
        decision["reason"] = "hashtags_changed"
        return decision
    if not _clean_text(repaired_draft.body):
        decision["reason"] = "empty_body"
        return decision
    if _INTERNAL_VISIBLE_RE.search("\n".join([repaired_draft.title, repaired_draft.lead, repaired_draft.body])):
        decision["reason"] = "internal_leakage"
        return decision

    current_sections = _extract_sections(current_draft.body)
    repaired_sections = _extract_sections(repaired_draft.body)
    if not current_sections or len(current_sections) != len(repaired_sections):
        decision["reason"] = "section_count_changed"
        return decision

    current_headings = [heading for heading, _body in current_sections]
    repaired_headings = [heading for heading, _body in repaired_sections]
    current_route_surface = "\n".join([current_draft.lead, *current_headings])
    repaired_route_surface = "\n".join([repaired_draft.lead, *repaired_headings])
    route_count_before = _route_phrase_count(current_route_surface)
    route_count_after = _route_phrase_count(repaired_route_surface)
    decision["route_phrase_count_before"] = route_count_before
    decision["route_phrase_count_after"] = route_count_after
    if route_count_before <= 0:
        decision["reason"] = "no_lead_heading_route_drift"
        return decision
    if route_count_after >= route_count_before:
        decision["reason"] = "route_phrase_not_reduced"
        return decision

    target_set = {_clean_text(item) for item in target_headings or [] if _clean_text(item)}
    changed_heading_indices: list[int] = []
    changed_body_indices: list[int] = []
    for index, ((current_heading, current_body), (repaired_heading, repaired_body)) in enumerate(
        zip(current_sections, repaired_sections)
    ):
        if _surface(current_heading) != _surface(repaired_heading):
            changed_heading_indices.append(index)
            if not has_company_intro_route_drift_phrase(current_heading):
                decision["reason"] = "unflagged_heading_changed"
                return decision
            if target_set and current_heading not in target_set:
                decision["reason"] = "changed_heading_outside_target"
                return decision
            if has_company_intro_route_drift_phrase(repaired_heading):
                decision["reason"] = "changed_heading_still_route_centered"
                return decision
        if _surface(current_body) != _surface(repaired_body):
            changed_body_indices.append(index)
            scoped_heading = current_heading
            if target_set and scoped_heading not in target_set:
                decision["reason"] = "body_change_outside_target"
                return decision
            if not _section_overlap_ok(current_body, repaired_body):
                decision["reason"] = "section_overlap_too_low"
                return decision

    decision["changed_heading_count"] = len(changed_heading_indices)
    if decision["lead_changed"] and not decision["lead_route_drift_before"]:
        decision["reason"] = "lead_changed_without_route_drift"
        return decision
    if decision["lead_changed"] and has_company_intro_route_drift_phrase(repaired_draft.lead):
        decision["reason"] = "lead_still_route_centered"
        return decision
    if not decision["lead_changed"] and not changed_heading_indices:
        decision["reason"] = "no_lead_or_heading_patch"
        return decision
    if len(set(changed_heading_indices + changed_body_indices)) > max(1, int(max_changed_headings)):
        decision["reason"] = "too_many_changed_headings"
        return decision

    repaired_validation = dict(repaired_diagnostics.get("company_introduction_source_contract_validation") or {})
    if not _hard_guard_clear(repaired_validation):
        decision["reason"] = "hard_guard_not_clear"
        return decision
    if not _slot_presence(repaired_validation, "current_business"):
        decision["reason"] = "current_business_missing"
        return decision
    if not _slot_presence(repaired_validation, "support_scope_boundary"):
        decision["reason"] = "support_scope_missing"
        return decision
    if not _alignment_not_worse(current_diagnostics, repaired_diagnostics):
        decision["reason"] = "source_grounding_worse"
        return decision

    decision["allowed"] = True
    decision["reason"] = "lead_heading_route_drift_reduced"
    return decision
