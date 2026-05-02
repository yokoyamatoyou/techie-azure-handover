"""Pure repair acceptance predicates used by the simple note pipeline."""
from __future__ import annotations

from typing import Any, Mapping


def _repair_preserves_alignment(
    current: Mapping[str, Any],
    repaired: Mapping[str, Any],
    *,
    tolerance_by_key: Mapping[str, float] | None = None,
) -> bool:
    tolerance_by_key = dict(
        tolerance_by_key
        or {
            "must_cover_reflection_rate": 0.01,
            "prompt_anchor_coverage": 0.05,
            "section_focus_coverage": 0.05,
        }
    )
    for key, tolerance in tolerance_by_key.items():
        current_value = float(current.get(key) or 0.0)
        repaired_value = float(repaired.get(key) or 0.0)
        if repaired_value + tolerance < current_value:
            return False
    return True


def _repair_improves_ending_monotony(current: Mapping[str, Any], repaired: Mapping[str, Any]) -> bool:
    current_max_run = int(current.get("ending_bucket_max_run", 0) or 0)
    current_score = float(current.get("ending_bucket_monotony_score", 0.0) or 0.0)
    if current_max_run < 3 and current_score < 0.45:
        return True
    repaired_max_run = int(repaired.get("ending_bucket_max_run", 0) or 0)
    repaired_score = float(repaired.get("ending_bucket_monotony_score", 0.0) or 0.0)
    if repaired_max_run < current_max_run:
        return True
    return repaired_score + 0.03 < current_score


def _repair_improves_explanatory_longform(current: Mapping[str, Any], repaired: Mapping[str, Any]) -> bool:
    current_body = int(current.get("body_chars", 0) or 0)
    repaired_body = int(repaired.get("body_chars", 0) or 0)
    if repaired_body <= current_body:
        return False
    target = int(current.get("target_chars", 0) or repaired.get("target_chars", 0) or 0)
    if target <= 0:
        return repaired_body >= current_body + 240
    current_ratio = current_body / max(1, target)
    repaired_ratio = repaired_body / max(1, target)
    if repaired_ratio >= 0.82 and repaired_body >= current_body + 180:
        return True
    return repaired_ratio >= current_ratio + 0.12 and repaired_body >= current_body + 320


def _repair_improves_explanatory_fingerprint(current: Mapping[str, Any], repaired: Mapping[str, Any]) -> bool:
    current_state = dict(current.get("explanatory_fingerprint_repair") or {})
    if not bool(current_state.get("activated")):
        return True
    current_flags = {
        str(item or "").strip()
        for item in list(current_state.get("flat_zone_flags") or [])
        if str(item or "").strip()
    }
    if not current_flags:
        return True
    repaired_state = dict(repaired.get("explanatory_fingerprint_repair") or {})
    if not bool(repaired_state.get("activated")):
        return True
    repaired_flags = {
        str(item or "").strip()
        for item in list(repaired_state.get("flat_zone_flags") or [])
        if str(item or "").strip()
    }
    return len(repaired_flags) < len(current_flags) or repaired_flags < current_flags


def _repair_improves_company_intro_fingerprint(current: Mapping[str, Any], repaired: Mapping[str, Any]) -> bool:
    current_state = dict(current.get("company_intro_fingerprint_repair") or {})
    if not bool(current_state.get("activated")):
        return True
    current_flags = {
        str(item or "").strip()
        for item in list(current_state.get("flat_zone_flags") or [])
        if str(item or "").strip()
    }
    if not current_flags:
        return True
    repaired_state = dict(repaired.get("company_intro_fingerprint_repair") or {})
    if not bool(repaired_state.get("activated")):
        return True
    repaired_flags = {
        str(item or "").strip()
        for item in list(repaired_state.get("flat_zone_flags") or [])
        if str(item or "").strip()
    }
    return len(repaired_flags) < len(current_flags) or repaired_flags < current_flags
