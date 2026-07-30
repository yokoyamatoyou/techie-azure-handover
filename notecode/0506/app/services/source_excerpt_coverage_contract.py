from __future__ import annotations

import re
from typing import Any


MAX_FINAL_USAGE_SUPPORT_CLAIMS = 2


def build_assigned_claim_groups(brief: dict[str, Any]) -> list[tuple[str, list[str]]]:
    return _assigned_claims_by_section(brief)


def build_final_usage_support_claim_sections(
    brief: dict[str, Any],
    knowledge_pack: dict[str, Any],
    assigned_claim_ids: set[str],
) -> dict[str, list[str]]:
    assigned_by_section = _assigned_claims_by_section(brief)
    if not assigned_by_section:
        return {}
    final_section_id = assigned_by_section[-1][0]
    result: dict[str, list[str]] = {}
    for claim_id in _final_usage_support_claim_ids(brief, knowledge_pack, assigned_claim_ids):
        _append_unique(result, claim_id, final_section_id)
    return result


def _assigned_claims_by_section(brief: dict[str, Any]) -> list[tuple[str, list[str]]]:
    sections = brief.get("sections")
    if isinstance(sections, list):
        rows: list[tuple[str, list[str]]] = []
        for index, section in enumerate(sections, start=1):
            if not isinstance(section, dict):
                continue
            section_id = str(section.get("section_id") or f"s{index}")
            claim_ids = [str(claim_id) for claim_id in section.get("assigned_claim_ids") or [] if str(claim_id)]
            rows.append((section_id, claim_ids))
        if any(claim_ids for _section_id, claim_ids in rows):
            return rows

    allocations = brief.get("claim_allocation")
    if not isinstance(allocations, list):
        return []
    rows = []
    for index, allocation in enumerate(allocations, start=1):
        if not isinstance(allocation, dict):
            continue
        section_id = str(allocation.get("section_id") or f"s{index}")
        claim_ids = [str(claim_id) for claim_id in allocation.get("claim_ids") or [] if str(claim_id)]
        rows.append((section_id, claim_ids))
    return rows


def _final_usage_support_claim_ids(
    brief: dict[str, Any],
    knowledge_pack: dict[str, Any],
    assigned_ids: set[str],
) -> list[str]:
    unassigned_ids = [str(claim_id) for claim_id in brief.get("unassigned_claim_ids") or [] if str(claim_id)]
    if not unassigned_ids:
        return []
    claims = _claims_by_id(knowledge_pack)
    hints = _final_usage_hints(brief)
    assigned_text = _normalize(" ".join(str(claims[claim_id].get("claim") or "") for claim_id in assigned_ids if claim_id in claims))
    hints = [hint for hint in hints if hint not in assigned_text]
    if not hints:
        return []

    result: list[str] = []
    for claim_id in unassigned_ids:
        if claim_id in assigned_ids or claim_id not in claims:
            continue
        claim_text = _normalize(" ".join([str(claims[claim_id].get("claim") or ""), str(claims[claim_id].get("preferred_expression") or "")]))
        if any(hint and hint in claim_text for hint in hints):
            result.append(claim_id)
        if len(result) >= MAX_FINAL_USAGE_SUPPORT_CLAIMS:
            break
    return result


def _final_usage_hints(brief: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("article_goal", "interest_hook", "reading_reward", "self_authored_angle"):
        values.extend(_hint_terms(str(brief.get(key) or "")))
    for value in brief.get("protected_subject_terms") or []:
        text = str(value or "").strip()
        if len(text) >= 2:
            values.append(text)
        values.extend(_hint_terms(text))
    style_policy = brief.get("style_edit_policy")
    if isinstance(style_policy, dict):
        for value in style_policy.get("protected_subject_terms") or []:
            text = str(value or "").strip()
            if len(text) >= 2:
                values.append(text)
            values.extend(_hint_terms(text))
    return _unique_strings([_normalize(value) for value in values if value])


def _hint_terms(text: str) -> list[str]:
    terms = []
    for piece in re.split(r"[\s,，、。:：;；/|()（）\[\]「」『』]+", text):
        cleaned = piece.strip()
        if len(cleaned) >= 3:
            terms.append(cleaned[:32])
    return terms


def _claims_by_id(knowledge_pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pack = knowledge_pack.get("article_knowledge_pack", {}) if isinstance(knowledge_pack, dict) else {}
    claims = pack.get("confirmed_facts") if isinstance(pack, dict) else []
    return {str(claim["claim_id"]): claim for claim in claims if isinstance(claim, dict) and claim.get("claim_id")}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "")).strip()


def _append_unique(mapping: dict[str, list[str]], key: str, value: str) -> None:
    values = mapping.setdefault(str(key), [])
    if value not in values:
        values.append(value)


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
