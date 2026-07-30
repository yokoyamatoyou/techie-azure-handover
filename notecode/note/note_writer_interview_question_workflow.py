"""UI-free interview question workflow helpers for note_writer_app."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any, Dict, List

from note.note_text_format_helpers import _to_plain_dict, _to_plain_list
from note.note_writer_role_handoff_helpers import _looks_theme_like_writer_role


QUESTION_POLICY_REASON_LABELS = {
    "llm_exception": "LLM呼び出しエラー",
    "empty_response": "LLM応答が空",
    "json_array_not_found": "JSON配列が見つからない",
    "json_parse_error": "JSON解析失敗",
    "invalid_schema": "スキーマ不一致",
    "announcement_sufficient_input": "入力が十分",
    "category_sufficient_input": "入力が十分",
    "default_sufficient_input": "入力が十分",
    "prompt_intent_clear_company_intro": "入力が十分",
    "missing_required_inputs": "補いたい入力があります",
    "already_answered": "回答済み",
    "unknown": "不明",
}


def label_for_question_policy_reason(reason: Any) -> str:
    normalized = str(reason or "unknown")
    return QUESTION_POLICY_REASON_LABELS.get(normalized, normalized)


def project_missing_required_fields(required_inputs: Mapping[str, Any]) -> List[str]:
    return [
        str(field)
        for field in _to_plain_list(required_inputs.get("missing_required_fields"))
        if str(field or "").strip()
    ]


def build_question_policy_request_kwargs(
    *,
    source_values: Sequence[Any],
    source_documents: Sequence[Any],
    article_type: str,
    selection: Mapping[str, Any],
    user_prompt_text: str,
    content_goal_key: str,
    writing_focus_key: str,
    length_mode_key: str,
    tone_profile_key: str,
    perspective_key: str,
    allow_experience: bool,
    interview_answers: Mapping[str, Any],
    speaker_profile_input: str,
    audience_profile_input: str,
    core_message_input: str,
    self_reference_policy_key: str,
    branding_subtype_key: str,
    branding_focus_key: str,
    pattern_key: str,
    strict_saas_mode: str,
    source_mode_key: str,
    industry_hint: str = "",
) -> Dict[str, Any]:
    return {
        "source_values": list(source_values),
        "source_documents": list(source_documents),
        "article_type": str(article_type or ""),
        "ui_journey": selection.get("ui_journey"),
        "comparison_axes": selection.get("comparison_axes"),
        "user_prompt_text": str(user_prompt_text or ""),
        "content_goal_key": str(content_goal_key or "auto"),
        "writing_focus_key": str(writing_focus_key or "auto"),
        "structure_key": "auto",
        "length_mode_key": str(length_mode_key or "adaptive"),
        "tone_profile_key": str(tone_profile_key or "auto"),
        "perspective_key": str(perspective_key or "auto"),
        "allow_experience": bool(allow_experience),
        "interview_answers": dict(interview_answers),
        "speaker_profile_input": str(speaker_profile_input or ""),
        "audience_profile_input": str(audience_profile_input or ""),
        "core_message_input": str(core_message_input or ""),
        "self_reference_policy_key": str(self_reference_policy_key or "auto"),
        "branding_subtype_key": str(branding_subtype_key or ""),
        "branding_focus_key": str(branding_focus_key or ""),
        "pattern_key": str(pattern_key or ""),
        "strict_saas_mode": str(strict_saas_mode or ""),
        "source_mode": str(source_mode_key or ""),
        "industry_hint": str(industry_hint or ""),
    }


def build_confirm_preview_request_kwargs(
    *,
    source_values: Sequence[Any],
    source_documents: Sequence[Any],
    article_type: str,
    selection: Mapping[str, Any],
    user_prompt_text: str,
    content_goal_key: str,
    writing_focus_key: str,
    length_mode_key: str,
    tone_profile_key: str,
    perspective_key: str,
    allow_experience: bool,
    interview_answers: Mapping[str, Any],
    speaker_profile_input: str,
    audience_profile_input: str,
    core_message_input: str,
    self_reference_policy_key: str,
    branding_subtype_key: str,
    branding_focus_key: str,
    pattern_key: str,
    system_hint_items: Sequence[Any],
    retry_memo: Sequence[Any],
    strict_saas_mode: str,
    source_mode_key: str,
    industry_hint: str = "",
) -> Dict[str, Any]:
    kwargs = build_question_policy_request_kwargs(
        source_values=source_values,
        source_documents=source_documents,
        article_type=article_type,
        selection=selection,
        user_prompt_text=user_prompt_text,
        content_goal_key=content_goal_key,
        writing_focus_key=writing_focus_key,
        length_mode_key=length_mode_key,
        tone_profile_key=tone_profile_key,
        perspective_key=perspective_key,
        allow_experience=allow_experience,
        interview_answers=interview_answers,
        speaker_profile_input=speaker_profile_input,
        audience_profile_input=audience_profile_input,
        core_message_input=core_message_input,
        self_reference_policy_key=self_reference_policy_key,
        branding_subtype_key=branding_subtype_key,
        branding_focus_key=branding_focus_key,
        pattern_key=pattern_key,
        strict_saas_mode=strict_saas_mode,
        source_mode_key=source_mode_key,
        industry_hint=industry_hint,
    )
    kwargs["system_hint_items"] = list(system_hint_items)
    kwargs["retry_memo"] = list(retry_memo)
    return kwargs


def build_interview_context_signature(
    *,
    source_values: Sequence[Any],
    article_type_key: str,
    content_goal_key: str,
    user_prompt_text: str,
) -> str:
    payload = {
        "article_type": str(article_type_key or "").strip(),
        "content_goal": str(content_goal_key or "").strip(),
        "user_prompt": str(user_prompt_text or "").strip(),
        "sources": sorted(
            str(value or "").strip()
            for value in source_values
            if str(value or "").strip()
        ),
    }
    normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def prepare_current_mainline_generation_request_inputs(
    *,
    interview_answers: Mapping[str, Any] | None,
    speaker_profile_input: str,
    prompt_raw: str,
) -> Dict[str, Any]:
    normalized_answers = {
        str(key): value
        for key, value in _to_plain_dict(interview_answers).items()
        if value
    }
    normalized_speaker_profile = str(speaker_profile_input or "").strip()
    writer_role_ignored_theme_like = False
    if normalized_speaker_profile and _looks_theme_like_writer_role(normalized_speaker_profile):
        writer_role_ignored_theme_like = True
        normalized_speaker_profile = ""
    return {
        "interview_answers": normalized_answers,
        "interview_answer_keys": sorted(normalized_answers.keys()),
        "interview_answer_count": len(normalized_answers),
        "speaker_profile_input": normalized_speaker_profile,
        "writer_role_ignored_theme_like": writer_role_ignored_theme_like,
        "prompt_raw": str(prompt_raw or "").strip(),
        "retry_memo": [],
    }


def prepare_current_mainline_interview_state_for_generation(
    *,
    interview_answers: Mapping[str, Any] | None,
    interview_questions_loaded: bool,
    stored_context_signature: str,
    current_context_signature: str,
) -> Dict[str, Any]:
    normalized_answers = _to_plain_dict(interview_answers)
    normalized_questions_loaded = bool(interview_questions_loaded)
    normalized_stored_signature = str(stored_context_signature or "")
    normalized_current_signature = str(current_context_signature or "")
    reset_required = bool(
        normalized_questions_loaded
        and normalized_stored_signature
        and normalized_stored_signature != normalized_current_signature
    )
    if reset_required:
        normalized_answers = {
            "perspective": None,
            "perspective_mode": None,
            "target": None,
            "message": None,
        }
        normalized_questions_loaded = False
        normalized_stored_signature = ""
    answered_count = 0
    if normalized_questions_loaded:
        interview_question_ids = {"perspective", "perspective_mode", "target", "message"}
        answered_count = sum(
            1
            for key, value in normalized_answers.items()
            if key in interview_question_ids and value
        )
    return {
        "interview_answers": normalized_answers,
        "interview_questions_loaded": normalized_questions_loaded,
        "stored_context_signature": normalized_stored_signature,
        "reset_required": reset_required,
        "answered_count": answered_count,
        "notify_unanswered": bool(normalized_questions_loaded and answered_count == 0),
    }


def filter_current_mainline_question_items_for_ui(
    question_items: Sequence[Any] | None,
) -> List[Dict[str, Any]]:
    allowed_fields = {"perspective_mode", "allow_experience"}
    filtered_items: List[Dict[str, Any]] = []
    for item in question_items or []:
        normalized_item = _to_plain_dict(item)
        field = str(normalized_item.get("field") or "").strip()
        if field not in allowed_fields:
            continue
        filtered_items.append(normalized_item)
    return filtered_items


def build_current_mainline_generation_selection_payload(
    *,
    base_selections: Mapping[str, Any] | None,
    article_type_key: str,
    selected_article_type_label: str,
    content_goal_key: str,
    writing_focus_key: str,
    structure_key: str,
    length_mode_key: str,
    tone_profile_key: str,
    perspective_key: str,
    allow_experience: bool,
    strict_saas_mode: str,
    default_strict_saas_mode: str = "medium",
) -> Dict[str, Any]:
    payload = _to_plain_dict(base_selections)
    payload.update(
        {
            "article_type": str(article_type_key or ""),
            "selected_label": str(selected_article_type_label or ""),
            "content_goal": str(content_goal_key or "auto"),
            "writing_focus": str(writing_focus_key or "auto"),
            "structure": str(structure_key or "auto"),
            "length_mode": str(length_mode_key or "adaptive"),
            "tone_profile": str(tone_profile_key or "auto"),
            "perspective": str(perspective_key or "auto"),
            "allow_experience": bool(allow_experience),
            "strict_saas_mode": str(strict_saas_mode or default_strict_saas_mode),
        }
    )
    return payload
