"""Lazy current-mainline compatibility wrappers for note_writer_app."""
from __future__ import annotations

import importlib
import os
from typing import Any, Dict, Iterable, Mapping


CURRENT_MAINLINE_UI_MODE = (os.environ.get("CURRENT_MAINLINE_UI_MODE", "journey") or "journey").strip().lower()


class _LazyModule:
    def __init__(self, module_name: str) -> None:
        object.__setattr__(self, "_module_name", module_name)

    def __getattr__(self, name: str) -> Any:
        return getattr(importlib.import_module(self._module_name), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_module_name":
            object.__setattr__(self, name, value)
            return
        setattr(importlib.import_module(self._module_name), name, value)


def _lazy_call(module_name: str, attribute_name: str, *args: Any, **kwargs: Any) -> Any:
    try:
        return getattr(importlib.import_module(module_name), attribute_name)(*args, **kwargs)
    except ModuleNotFoundError as exc:
        if module_name.startswith("note.current_mainline_") and exc.name == module_name:
            return _current_mainline_disabled_adapter_call(module_name, attribute_name, *args, **kwargs)
        raise


def _current_mainline_runner_module() -> Any:
    return importlib.import_module("note.current_mainline_runner")


def _normalize_disabled_current_mainline_article_type(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    allowed = {
        "announcement",
        "branding",
        "case_study",
        "comparative_review",
        "daily_story",
        "explanatory_article",
        "industry_analysis",
    }
    return normalized if normalized in allowed else "explanatory_article"


def _resolve_disabled_current_mainline_selection(
    *,
    article_type: Any = "explanatory_article",
    ui_journey: Mapping[str, Any] | None = None,
    comparison_axes: Iterable[Any] | None = None,
) -> Dict[str, Any]:
    journey = dict(ui_journey or {})
    purpose_key = str(journey.get("purpose_key") or "").strip()
    target_key = str(journey.get("target_key") or "").strip()
    journey_map = {
        ("explain", "know_how"): ("explanatory_article", "know_how"),
        ("explain", "industry"): ("industry_analysis", "industry_analysis"),
        ("brand", "company"): ("branding", "company_introduction"),
        ("brand", "service"): ("branding", "service_introduction"),
        ("brand", "product"): ("branding", "product_introduction"),
        ("case", "case_study"): ("case_study", "case_study"),
        ("news", "announcement"): ("announcement", "announcement"),
        ("compare", "comparison"): ("comparative_review", "comparative_review"),
    }
    resolved_article_type, semantic_key = journey_map.get(
        (purpose_key, target_key),
        (_normalize_disabled_current_mainline_article_type(article_type), ""),
    )
    if not semantic_key:
        semantic_key = {
            "announcement": "announcement",
            "branding": "company_introduction",
            "case_study": "case_study",
            "comparative_review": "comparative_review",
            "daily_story": "daily_story",
            "explanatory_article": "know_how",
            "industry_analysis": "industry_analysis",
        }.get(resolved_article_type, resolved_article_type)
    axes = [str(item).strip() for item in (comparison_axes or journey.get("comparison_axes") or []) if str(item).strip()]
    return {
        "article_type": resolved_article_type,
        "semantic_article_key": semantic_key,
        "ui_journey": journey,
        "comparison_axes": axes if resolved_article_type == "comparative_review" else [],
    }


def _current_mainline_disabled_adapter_call(
    module_name: str,
    attribute_name: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    del module_name, args
    if attribute_name == "resolve_compact_writing_profile":
        article_type = _normalize_disabled_current_mainline_article_type(kwargs.get("article_type"))
        semantic_key = str(kwargs.get("semantic_article_key") or "").strip()
        return {
            "article_type": article_type,
            "semantic_article_key": semantic_key or article_type,
            "writing_focus": str(kwargs.get("writing_focus_key") or "auto"),
            "tone_profile": str(kwargs.get("tone_profile_key") or "auto"),
            "perspective": str(kwargs.get("perspective_key") or "auto"),
            "system_hint_items": list(kwargs.get("system_hint_items") or []),
        }
    if attribute_name == "build_invalidate_journey_confirmation":
        return {
            "signature": "",
            "preview": {},
            "source_fit_text": "",
            "status_text": "writer-only UI では旧生成確認は無効です。",
            "grounding_status_text": "",
            "missing_content": "",
            "reason_code": "CURRENT_MAINLINE_DISABLED",
            "error_class": "disabled_legacy_route",
            "needs_input_items": [],
            "event_extra": {"current_mainline_disabled": True},
        }
    if attribute_name == "build_journey_confirm_summary":
        return "writer-only UI"
    if attribute_name == "build_journey_selection_summary":
        return {
            "ui_mode": str(kwargs.get("ui_mode") or CURRENT_MAINLINE_UI_MODE),
            "purpose_key": str(kwargs.get("purpose_key") or ""),
            "purpose_label": str(kwargs.get("purpose_label") or ""),
            "target_key": str(kwargs.get("target_key") or ""),
            "target_label": str(kwargs.get("target_label") or ""),
            "semantic_article_key": str(kwargs.get("semantic_article_key") or ""),
            "semantic_label": str(kwargs.get("semantic_label") or ""),
            "article_type_key": str(kwargs.get("article_type_key") or ""),
            "article_type_label": str(kwargs.get("article_type_label") or ""),
            "confirmed": bool(kwargs.get("confirmed")),
        }
    if attribute_name == "build_journey_signature":
        parts = [
            str(kwargs.get("purpose_key") or ""),
            str(kwargs.get("target_key") or ""),
            str(kwargs.get("detail_key") or ""),
        ]
        return "|".join(parts)
    if attribute_name in {
        "build_journey_confirm_blocked_view",
        "build_journey_confirm_preview_view",
        "build_journey_confirmed_view",
    }:
        return {
            "summary_content": "writer-only UI",
            "source_fit_text": "",
            "grounding_status_text": "",
            "missing_content": "",
            "status_text": "writer-only UI では旧生成確認は無効です。",
            "allow_confirm": False,
            "reason_code": "CURRENT_MAINLINE_DISABLED",
            "error_class": "disabled_legacy_route",
            "needs_input_items": [],
            "event_extra": {"current_mainline_disabled": True},
        }
    if attribute_name.startswith("build_current_mainline_generation_"):
        return {}
    if attribute_name.startswith("build_current_mainline_"):
        return {
            "status_text": "旧 current-mainline は writer-only UI で無効です。",
            "source_error_content": "writer-only の「記事を生成」を使用してください。",
            "notify_text": "writer-only の「記事を生成」を使用してください。",
            "reason_code": "CURRENT_MAINLINE_DISABLED",
            "error_class": "disabled_legacy_route",
        }
    if attribute_name.startswith("append_"):
        return None
    if attribute_name == "build_latest_quality_report_payload":
        return {}
    if attribute_name == "collect_runtime_config_snapshot":
        return {"current_mainline_disabled": True}
    if attribute_name == "persist_latest_generation_snapshot":
        return None
    return {}


def assess_current_mainline_question_policy(*args: Any, **kwargs: Any) -> Any:
    try:
        return _current_mainline_runner_module().assess_current_mainline_question_policy(*args, **kwargs)
    except ModuleNotFoundError as exc:
        if exc.name == "note.current_mainline_runner":
            return {
                "should_ask": False,
                "blocked": False,
                "question_items": [],
                "needs_input_items": [],
                "reason_code": "CURRENT_MAINLINE_DISABLED",
            }
        raise


def build_omakase_preflight(*args: Any, **kwargs: Any) -> Any:
    try:
        return _current_mainline_runner_module().build_omakase_preflight(*args, **kwargs)
    except ModuleNotFoundError as exc:
        if exc.name == "note.current_mainline_runner":
            return {"status": "DISABLED", "reason_code": "CURRENT_MAINLINE_DISABLED"}
        raise


def build_current_mainline_confirm_preview(*args: Any, **kwargs: Any) -> Any:
    try:
        return _current_mainline_runner_module().build_current_mainline_confirm_preview(*args, **kwargs)
    except ModuleNotFoundError as exc:
        if exc.name == "note.current_mainline_runner":
            return {"input_decision": {"action": "stop"}, "source_fit": {}, "ui_journey": {}}
        raise


def build_fail_closed_generation_result(*args: Any, **kwargs: Any) -> Any:
    try:
        return _current_mainline_runner_module().build_fail_closed_generation_result(*args, **kwargs)
    except ModuleNotFoundError as exc:
        if exc.name == "note.current_mainline_runner":
            return {
                "success": False,
                "blocked": True,
                "reason_code": str(kwargs.get("reason_code") or "CURRENT_MAINLINE_DISABLED"),
                "error_class": str(kwargs.get("error_class") or "disabled_legacy_route"),
            }
        raise


def resolve_current_mainline_ui_selection(*args: Any, **kwargs: Any) -> Any:
    try:
        return _current_mainline_runner_module().resolve_current_mainline_ui_selection(*args, **kwargs)
    except ModuleNotFoundError as exc:
        if exc.name == "note.current_mainline_runner":
            return _resolve_disabled_current_mainline_selection(*args, **kwargs)
        raise


def resolve_compact_writing_profile(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_profile_resolver", "resolve_compact_writing_profile", *args, **kwargs)


def runtime_append_generation_audit_record(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_runtime_logging", "append_generation_audit_record", *args, **kwargs)


def runtime_append_ui_journey_event(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_runtime_logging", "append_ui_journey_event", *args, **kwargs)


def runtime_build_latest_quality_report_payload(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_runtime_logging", "build_latest_quality_report_payload", *args, **kwargs)


def runtime_collect_runtime_config_snapshot(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_runtime_logging", "collect_runtime_config_snapshot", *args, **kwargs)


def runtime_persist_latest_generation_snapshot(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_runtime_logging", "persist_latest_generation_snapshot", *args, **kwargs)


runtime_logging_mod = _LazyModule("note.current_mainline_runtime_logging")


def build_invalidate_journey_confirmation_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_confirm_adapter", "build_invalidate_journey_confirmation", *args, **kwargs)


def build_journey_confirm_blocked_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_confirm_adapter", "build_journey_confirm_blocked_view", *args, **kwargs)


def build_journey_confirm_preview_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_confirm_adapter", "build_journey_confirm_preview_view", *args, **kwargs)


def build_journey_confirm_summary_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_confirm_adapter", "build_journey_confirm_summary", *args, **kwargs)


def build_journey_confirmed_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_confirm_adapter", "build_journey_confirmed_view", *args, **kwargs)


def build_journey_selection_summary_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_confirm_adapter", "build_journey_selection_summary", *args, **kwargs)


def build_journey_signature_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_confirm_adapter", "build_journey_signature", *args, **kwargs)


def build_current_mainline_generation_cleanup_plan_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_generation_state_adapter", "build_current_mainline_generation_cleanup_plan", *args, **kwargs)


def build_current_mainline_generation_complete_plan_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_generation_state_adapter", "build_current_mainline_generation_complete_plan", *args, **kwargs)


def build_current_mainline_generation_exception_plan_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_generation_state_adapter", "build_current_mainline_generation_exception_plan", *args, **kwargs)


def build_current_mainline_generation_prerun_plan_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_generation_state_adapter", "build_current_mainline_generation_prerun_plan", *args, **kwargs)


def build_current_mainline_generation_event_request_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_generation_telemetry_adapter", "build_current_mainline_generation_event_request", *args, **kwargs)


def build_current_mainline_generation_gate_extra_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_generation_telemetry_adapter", "build_current_mainline_generation_gate_extra", *args, **kwargs)


def build_current_mainline_generation_snapshot_request_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_generation_telemetry_adapter", "build_current_mainline_generation_snapshot_request", *args, **kwargs)


def build_current_mainline_generation_telemetry_context_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_generation_telemetry_adapter", "build_current_mainline_generation_telemetry_context", *args, **kwargs)


def attach_prompt_context_to_result_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "attach_prompt_context_to_result", *args, **kwargs)


def build_current_mainline_ambiguity_confirmation_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_ambiguity_confirmation_view", *args, **kwargs)


def build_current_mainline_completion_payload_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_completion_payload", *args, **kwargs)


def build_current_mainline_confirmation_required_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_confirmation_required_view", *args, **kwargs)


def build_current_mainline_fetch_failure_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_fetch_failure_view", *args, **kwargs)


def build_current_mainline_generation_error_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_generation_error_view", *args, **kwargs)


def build_current_mainline_generation_busy_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_generation_busy_view", *args, **kwargs)


def build_current_mainline_legal_postcheck_payload_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_legal_postcheck_payload", *args, **kwargs)


def build_current_mainline_generation_no_sources_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_generation_no_sources_view", *args, **kwargs)


def build_current_mainline_guard_retry_exception_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_guard_retry_exception_view", *args, **kwargs)


def build_current_mainline_invalid_article_type_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_invalid_article_type_view", *args, **kwargs)


def build_current_mainline_missing_required_inputs_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_missing_required_inputs_view", *args, **kwargs)


def build_current_mainline_no_valid_sources_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_no_valid_sources_view", *args, **kwargs)


def build_current_mainline_output_guard_blocked_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_output_guard_blocked_view", *args, **kwargs)


def build_current_mainline_success_view_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_success_view", *args, **kwargs)


def build_current_mainline_user_input_feedback_core(*args: Any, **kwargs: Any) -> Any:
    return _lazy_call("note.current_mainline_ui_result_adapter", "build_current_mainline_user_input_feedback", *args, **kwargs)
