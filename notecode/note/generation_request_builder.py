"""UI-to-pipeline request builders for current mainline generation."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Iterable

from note.current_mainline_input_policy import resolve_effective_speaker_profile
from note.interview_contract_mapper import build_interview_contract_patch
from note.newalgorithm_pipeline.strict_saas import normalize_strict_saas_mode
from note import source_document_utils

DEFAULT_REGISTER_POLICY: Dict[str, Any] = {
    "base_register": "polite",
    "allowed_endings": ["です", "ます", "でした", "ました"],
    "banned_endings": [],
    "max_consecutive_same_ending": 2,
}
SELF_REFERENCE_POLICY_ALLOWED_PRONOUNS: Dict[str, list[str]] = {
    "auto": [],
    "watashi": ["私", "わたし"],
    "watashitachi": ["私たち"],
    "tousha": ["当社"],
    "heisha": ["弊社"],
    "minimal": [],
}


def _normalize_source_values(source_values: Iterable[Any]) -> list[str]:
    normalized: list[str] = []
    for item in source_values:
        text = str(item or "").strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_source_documents(source_documents: Iterable[Any] | None) -> list[Dict[str, Any]]:
    normalized: list[Dict[str, Any]] = []
    if source_documents is None:
        return normalized
    for item in source_documents:
        document = source_document_utils.normalize_source_document_entry(
            item,
            include_content_type=True,
        )
        if not document:
            continue
        normalized.append(document)
    return normalized


def _copy_register_policy(register_policy: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    source = register_policy if isinstance(register_policy, Mapping) else DEFAULT_REGISTER_POLICY
    allowed_endings = source.get("allowed_endings", [])
    banned_endings = source.get("banned_endings", [])
    return {
        "base_register": str(source.get("base_register") or "polite"),
        "allowed_endings": [str(item) for item in allowed_endings if str(item or "").strip()],
        "banned_endings": [str(item) for item in banned_endings if str(item or "").strip()],
        "max_consecutive_same_ending": int(source.get("max_consecutive_same_ending", 2) or 2),
    }


def _normalize_string_list(values: Iterable[Any] | None) -> list[str]:
    normalized: list[str] = []
    if values is None:
        return normalized
    for item in values:
        text = str(item or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _normalize_ui_journey(ui_journey: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(ui_journey, Mapping):
        return {}
    normalized: Dict[str, Any] = {}
    for key in ("purpose_key", "target_key", "detail_key"):
        value = str(ui_journey.get(key) or "").strip().lower()
        if value:
            normalized[key] = value
    comparison_axes = _normalize_string_list(ui_journey.get("comparison_axes"))
    if comparison_axes:
        normalized["comparison_axes"] = comparison_axes
    return normalized


def _normalize_self_reference_policy_key(value: Any) -> str:
    key = str(value or "").strip().lower()
    if key in SELF_REFERENCE_POLICY_ALLOWED_PRONOUNS:
        return key
    return "auto"


def _resolve_allowed_pronouns_from_self_reference_policy(policy_key: str) -> list[str]:
    return list(SELF_REFERENCE_POLICY_ALLOWED_PRONOUNS.get(policy_key, []))


def _resolve_field_source(explicit_value: str, fallback_value: str, *, explicit_source: str, fallback_source: str) -> str:
    if explicit_value:
        return explicit_source
    if fallback_value:
        return fallback_source
    return ""


def _merge_field_sources(
    base: Mapping[str, Any] | None,
    overrides: Mapping[str, str],
) -> Dict[str, str]:
    merged: Dict[str, str] = {}
    if isinstance(base, Mapping):
        for key, value in base.items():
            normalized_key = str(key or "").strip()
            normalized_value = str(value or "").strip()
            if normalized_key and normalized_value:
                merged[normalized_key] = normalized_value
    for key, value in overrides.items():
        normalized_key = str(key or "").strip()
        normalized_value = str(value or "").strip()
        if normalized_key and normalized_value:
            merged[normalized_key] = normalized_value
    return merged


def build_raw_input_contract(
    *,
    source_values: Iterable[Any],
    source_documents: Iterable[Any] | None = None,
    article_type: str,
    user_prompt_text: str,
    content_goal_key: str,
    writing_focus_key: str,
    structure_key: str,
    length_mode_key: str,
    tone_profile_key: str,
    perspective_key: str,
    allow_experience: bool,
    interview_answers: Mapping[str, Any] | None,
    media: str = "note",
    relationship_mode: str = "guide",
    register_policy: Mapping[str, Any] | None = None,
    speaker_profile_input: str = "",
    audience_profile_input: str = "",
    core_message_input: str = "",
    self_reference_policy_key: str = "auto",
    system_hint_items: Iterable[Any] | None = None,
    retry_memo: Iterable[Any] | None = None,
    strict_saas_mode: str = "medium",
    field_sources: Mapping[str, Any] | None = None,
    ui_journey: Mapping[str, Any] | None = None,
    semantic_article_key: str = "",
    comparison_axes: Iterable[Any] | None = None,
    body_generation_experiment: str = "",
) -> Dict[str, Any]:
    normalized_answers = dict(interview_answers or {})
    normalized_sources = _normalize_source_values(source_values)
    normalized_source_documents = _normalize_source_documents(source_documents)
    prompt_raw = str(user_prompt_text or "").strip()
    raw_writer_role = str(normalized_answers.get("writer_role") or "").strip()
    explicit_speaker_profile = str(speaker_profile_input or "").strip()
    effective_speaker_profile, speaker_field_source = resolve_effective_speaker_profile(
        article_type_key=article_type,
        speaker_profile_input=explicit_speaker_profile,
        interview_writer_role=raw_writer_role,
    )
    explicit_audience_profile = str(audience_profile_input or "").strip()
    explicit_core_message = str(core_message_input or "").strip()
    interview_audience_profile = str(normalized_answers.get("target") or "").strip()
    interview_core_message = str(
        normalized_answers.get("core_message")
        or normalized_answers.get("main_message")
        or normalized_answers.get("message")
        or ""
    ).strip()
    interview_contract_patch = build_interview_contract_patch(
        normalized_answers,
        writer_role=effective_speaker_profile or raw_writer_role,
    )
    normalized_system_hint_items = _normalize_string_list(system_hint_items)
    normalized_retry_memo = _normalize_string_list(retry_memo)
    normalized_ui_journey = _normalize_ui_journey(ui_journey)
    normalized_comparison_axes = _normalize_string_list(comparison_axes)
    normalized_self_reference_policy = _normalize_self_reference_policy_key(self_reference_policy_key)
    resolved_allowed_pronouns = _resolve_allowed_pronouns_from_self_reference_policy(
        normalized_self_reference_policy
    )
    merged_field_sources = _merge_field_sources(
        field_sources,
        {
            "article_type": "ui",
            "prompt_raw": "user_prompt",
            "topic": "user_prompt",
            "speaker_profile": _resolve_field_source(
                effective_speaker_profile,
                "",
                explicit_source=speaker_field_source,
                fallback_source="",
            ),
            "audience_profile": _resolve_field_source(
                explicit_audience_profile,
                interview_audience_profile,
                explicit_source="ui",
                fallback_source="interview_answers",
            ),
            "core_message": _resolve_field_source(
                explicit_core_message,
                interview_core_message,
                explicit_source="ui",
                fallback_source="interview_answers",
            ),
            "topic_statement": "interview_answers" if str(interview_contract_patch.get("topic_statement") or "").strip() else "",
            "narrative_axis": "interview_answers" if str(interview_contract_patch.get("narrative_axis") or "").strip() else "",
            "system_hint_items": "ui" if normalized_system_hint_items else "",
            "retry_memo": "system" if normalized_retry_memo else "",
            "strict_saas_mode": "system",
            "semantic_article_key": "ui_journey" if semantic_article_key else "",
            "comparison_axes": "ui_journey" if normalized_comparison_axes else "",
            "self_reference_policy": "ui" if normalized_self_reference_policy != "auto" else "",
            "allowed_pronouns": "ui" if resolved_allowed_pronouns else "",
            "body_generation_experiment": "ui" if str(body_generation_experiment or "").strip() else "",
        },
    )
    contract = {
        "source": list(normalized_sources),
        "source_inputs": list(normalized_sources),
        "source_documents": list(normalized_source_documents),
        "article_type": str(article_type or "").strip(),
        "media": str(media or "note").strip() or "note",
        "prompt_raw": prompt_raw,
        "topic": prompt_raw,
        "content_goal": str(content_goal_key or "").strip(),
        "writing_focus": str(writing_focus_key or "").strip(),
        "structure": "auto",
        "length_mode": str(length_mode_key or "").strip(),
        "length_mode_requested": str(length_mode_key or "").strip(),
        "tone_profile": str(tone_profile_key or "").strip(),
        "perspective": str(perspective_key or "").strip(),
        "article_viewpoint": str(perspective_key or "").strip(),
        "allow_experience": bool(allow_experience),
        "interview_answers": normalized_answers,
        "speaker_profile": effective_speaker_profile,
        "writer_role": raw_writer_role,
        "self_reference_policy": normalized_self_reference_policy,
        "allowed_pronouns": resolved_allowed_pronouns,
        "topic_statement": str(interview_contract_patch.get("topic_statement") or ""),
        "narrative_axis": str(interview_contract_patch.get("narrative_axis") or ""),
        "knowledge_lenses": list(interview_contract_patch.get("knowledge_lenses") or []),
        "audience_profile": explicit_audience_profile or interview_audience_profile,
        "core_message": explicit_core_message or interview_core_message,
        "relationship_mode": str(relationship_mode or "").strip() or "guide",
        "register_policy": _copy_register_policy(register_policy),
        "system_hint_items": normalized_system_hint_items,
        "retry_memo": normalized_retry_memo,
        "strict_saas_mode": normalize_strict_saas_mode(strict_saas_mode),
        "field_sources": merged_field_sources,
        "ui_journey": normalized_ui_journey,
        "semantic_article_key": str(semantic_article_key or "").strip(),
        "comparison_axes": normalized_comparison_axes,
        "body_generation_experiment": str(body_generation_experiment or "").strip(),
    }
    return contract


def build_pipeline_payload(
    input_contract: Mapping[str, Any] | None,
    *,
    user_prompt_text: str,
) -> Dict[str, Any]:
    payload = dict(input_contract or {})
    source_inputs = payload.get("source_inputs", [])
    if not isinstance(source_inputs, list):
        source_inputs = []
    prompt_raw = str(user_prompt_text or payload.get("prompt_raw") or "").strip()
    payload["source"] = list(source_inputs)
    payload["prompt_raw"] = prompt_raw
    payload["topic"] = prompt_raw
    return payload
