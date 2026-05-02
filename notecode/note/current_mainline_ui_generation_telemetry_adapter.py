"""Plain-data helpers for current mainline generation telemetry inside the UI shell."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Dict, List


def _to_plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _to_plain_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _normalize_string_list(values: Iterable[Any] | None) -> List[str]:
    normalized: List[str] = []
    if values is None:
        return normalized
    for item in values:
        text = str(item or "").strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_selection_summary(selections: Mapping[str, Any] | None) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    if not isinstance(selections, Mapping):
        return normalized
    for key, value in selections.items():
        normalized_key = str(key or "").strip()
        if not normalized_key:
            continue
        if isinstance(value, bool):
            normalized[normalized_key] = value
            continue
        if isinstance(value, (int, float)):
            normalized[normalized_key] = value
            continue
        text = str(value or "").strip()
        if text:
            normalized[normalized_key] = text
    return normalized


def _normalize_source_items(source_items: Iterable[Any] | None) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    if source_items is None:
        return normalized
    for item in source_items:
        if isinstance(item, Mapping):
            source_type = str(item.get("source_type", "") or "")
            value = str(item.get("value", "") or item.get("locator", "") or "")
            label = str(item.get("label", "") or "")
        else:
            source_type = str(getattr(item, "source_type", "") or "")
            value = str(getattr(item, "value", "") or getattr(item, "locator", "") or "")
            label = str(getattr(item, "label", "") or "")
        entry: Dict[str, Any] = {}
        if source_type:
            entry["source_type"] = source_type
        if value:
            entry["value"] = value
        if label:
            entry["label"] = label
        if entry:
            normalized.append(entry)
    return normalized


def _normalize_needs_input_items(items: Iterable[Any] | None) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    if items is None:
        return normalized
    for item in items:
        if isinstance(item, Mapping):
            entry = {str(key): value for key, value in item.items() if str(key or "").strip()}
        else:
            entry = {}
            for field_name in ("field", "issue_type", "required_format", "question_template", "example_answer"):
                value = str(getattr(item, field_name, "") or "").strip()
                if value:
                    entry[field_name] = value
        if entry:
            normalized.append(entry)
    return normalized


def _normalize_extra(extra: Mapping[str, Any] | None) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    if not isinstance(extra, Mapping):
        return normalized
    for key, value in extra.items():
        normalized_key = str(key or "").strip()
        if not normalized_key:
            continue
        if isinstance(value, Mapping):
            normalized[normalized_key] = {str(sub_key): sub_value for sub_key, sub_value in value.items()}
        elif isinstance(value, list):
            normalized[normalized_key] = list(value)
        else:
            normalized[normalized_key] = value
    return normalized


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_current_mainline_generation_gate_extra(
    *,
    generation_gate_kind: str,
    required_action: str,
    semantic_article_key: str = "",
    allow_generate: bool | None = None,
    selection_confirmed: bool | None = None,
    confirmation_state: str = "",
    confirmed_signature_present: bool | None = None,
    required_step: str = "",
    required_journey_stage: int | None = None,
    selected_article_type_label: str = "",
    resolved_article_type: str = "",
    article_type_resolution_state: str = "",
    term_count: int | None = None,
) -> Dict[str, Any]:
    extra: Dict[str, Any] = {
        "decision_origin": "ui_generation_guard",
        "generation_gate_kind": str(generation_gate_kind or "").strip(),
        "required_action": str(required_action or "").strip(),
    }
    normalized_semantic_key = str(semantic_article_key or "").strip()
    if normalized_semantic_key:
        extra["semantic_article_key"] = normalized_semantic_key
    if allow_generate is not None:
        extra["allow_generate"] = bool(allow_generate)
    if selection_confirmed is not None:
        extra["selection_confirmed"] = bool(selection_confirmed)
    normalized_confirmation_state = str(confirmation_state or "").strip()
    if normalized_confirmation_state:
        extra["confirmation_state"] = normalized_confirmation_state
    if confirmed_signature_present is not None:
        extra["confirmed_signature_present"] = bool(confirmed_signature_present)
    normalized_required_step = str(required_step or "").strip()
    if normalized_required_step:
        extra["required_step"] = normalized_required_step
    if required_journey_stage is not None:
        extra["required_journey_stage"] = _safe_int(required_journey_stage, 0)
    normalized_selected_label = str(selected_article_type_label or "").strip()
    if normalized_selected_label:
        extra["selected_article_type_label"] = normalized_selected_label
    normalized_resolved_article_type = str(resolved_article_type or "").strip()
    if normalized_resolved_article_type:
        extra["resolved_article_type"] = normalized_resolved_article_type
    normalized_resolution_state = str(article_type_resolution_state or "").strip()
    if normalized_resolution_state:
        extra["article_type_resolution_state"] = normalized_resolution_state
    if term_count is not None:
        extra["term_count"] = max(_safe_int(term_count, 0), 0)
    return extra


def build_current_mainline_generation_telemetry_context(
    *,
    attempt_id: str,
    article_type: str,
    user_prompt_text: str = "",
    source_items: Iterable[Any] | None = None,
    selections: Mapping[str, Any] | None = None,
    writing_focus_key: str = "",
    perspective_key: str = "",
    tone_profile_key: str = "auto",
    prompt_raw: str = "",
    system_hint_items: Iterable[Any] | None = None,
    retry_memo: Iterable[Any] | None = None,
    strict_saas_mode: str = "medium",
    question_generation_owner: str = "",
) -> Dict[str, Any]:
    normalized_owner = str(question_generation_owner or "").strip() or "none"
    return {
        "attempt_id": str(attempt_id or "").strip(),
        "article_type": str(article_type or "unknown").strip() or "unknown",
        "user_prompt_text": str(user_prompt_text or "").strip(),
        "source_items": _normalize_source_items(source_items),
        "selections": _normalize_selection_summary(selections),
        "writing_focus_key": str(writing_focus_key or "").strip(),
        "perspective_key": str(perspective_key or "").strip(),
        "tone_profile_key": str(tone_profile_key or "auto").strip() or "auto",
        "prompt_raw": str(prompt_raw or "").strip(),
        "system_hint_items": _normalize_string_list(system_hint_items),
        "retry_memo": _normalize_string_list(retry_memo),
        "strict_saas_mode": str(strict_saas_mode or "medium").strip() or "medium",
        "question_generation_owner": normalized_owner,
    }


def build_current_mainline_generation_event_request(
    context: Mapping[str, Any] | None,
    *,
    event: str,
    phase: str,
    result: Mapping[str, Any] | None = None,
    reason_code: str = "",
    error_class: str = "",
    status_text: str = "",
    needs_input_items: Iterable[Any] | None = None,
    extra: Mapping[str, Any] | None = None,
    include_question_generation_owner: bool = False,
) -> Dict[str, Any]:
    normalized_context = _to_plain_dict(context)
    normalized_extra = _normalize_extra(extra)
    if include_question_generation_owner:
        normalized_extra["question_generation_owner"] = str(
            normalized_context.get("question_generation_owner") or "none"
        )
    request: Dict[str, Any] = {
        "attempt_id": str(normalized_context.get("attempt_id") or "").strip(),
        "event": str(event or "").strip(),
        "article_type": str(normalized_context.get("article_type") or "unknown").strip() or "unknown",
        "phase": str(phase or "").strip(),
        "user_prompt_text": str(normalized_context.get("user_prompt_text") or "").strip(),
        "source_items": _normalize_source_items(normalized_context.get("source_items")),
        "selections": _normalize_selection_summary(normalized_context.get("selections")),
        "result": dict(result) if isinstance(result, Mapping) else None,
        "reason_code": str(reason_code or "").strip(),
        "error_class": str(error_class or "").strip(),
        "status_text": str(status_text or "").strip(),
        "needs_input_items": _normalize_needs_input_items(needs_input_items),
        "extra": normalized_extra,
    }
    return request


def build_current_mainline_generation_snapshot_request(
    context: Mapping[str, Any] | None,
    *,
    result: Mapping[str, Any] | None,
    source_count: int,
    blocked: bool = False,
) -> Dict[str, Any]:
    normalized_context = _to_plain_dict(context)
    return {
        "result": dict(result) if isinstance(result, Mapping) else {},
        "attempt_id": str(normalized_context.get("attempt_id") or "").strip(),
        "article_type": str(normalized_context.get("article_type") or "").strip(),
        "writing_focus_key": str(normalized_context.get("writing_focus_key") or "").strip(),
        "perspective_key": str(normalized_context.get("perspective_key") or "").strip(),
        "tone_profile_key": str(normalized_context.get("tone_profile_key") or "auto").strip() or "auto",
        "prompt_raw": str(normalized_context.get("prompt_raw") or "").strip(),
        "system_hint_items": _normalize_string_list(normalized_context.get("system_hint_items")),
        "retry_memo": _normalize_string_list(normalized_context.get("retry_memo")),
        "strict_saas_mode": str(normalized_context.get("strict_saas_mode") or "medium").strip() or "medium",
        "source_count": _safe_int(source_count, 0),
        "blocked": bool(blocked),
    }
