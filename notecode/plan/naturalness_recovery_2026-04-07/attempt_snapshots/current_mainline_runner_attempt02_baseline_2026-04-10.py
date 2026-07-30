"""Helpers for invoking the current mainline from the UI shell."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Protocol
from urllib.parse import urlparse

from note.generation_request_builder import build_pipeline_payload, build_raw_input_contract
from note.input_contract_v1 import InputContractValidationError, normalize_article_type, normalize_input_contract_v1
from note.newalgorithm_pipeline.input_contract import resolve_input_contract
from note.newalgorithm_pipeline.output_guard import apply_generation_output_guard
from note.current_mainline_profile_resolver import resolve_compact_writing_profile
from note.vnext.pipeline import VNextPipeline
from note.vnext_adapters.current_ui_contract_adapter import adapt_current_contract_to_vnext
from note.vnext_adapters.runtime_projection_adapter import build_vnext_shadow_projection
from note.vnext_current_boundary import build_vnext_current_boundary_summary


class CurrentMainlinePipeline(Protocol):
    def generate(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        ...


_CANONICAL_UI_JOURNEY_ROUTE_MAP: Dict[tuple[str, str], Dict[str, str]] = {
    ("explain", "concept"): {
        "article_type": "explanatory_article",
        "semantic_article_key": "explanatory_article",
    },
    ("explain", "industry"): {
        "article_type": "industry_analysis",
        "semantic_article_key": "industry_analysis",
    },
    ("introduce", "company"): {
        "article_type": "branding",
        "semantic_article_key": "company_introduction",
    },
    ("introduce", "product_service"): {
        "article_type": "branding",
        "semantic_article_key": "product_introduction",
    },
    ("announce", "standard"): {
        "article_type": "announcement",
        "semantic_article_key": "announcement",
    },
    ("case", "implementation"): {
        "article_type": "case_study",
        "semantic_article_key": "implementation_case",
    },
    ("compare", "tool_service"): {
        "article_type": "comparative_review",
        "semantic_article_key": "comparative_review",
    },
    ("daily", "day_to_day"): {
        "article_type": "daily_story",
        "semantic_article_key": "daily_story",
    },
}

_COMPAT_UI_JOURNEY_ROUTE_MAP: Dict[tuple[str, str], Dict[str, str]] = {
    ("introduce", "activity_project"): {
        "article_type": "branding",
        "semantic_article_key": "activity_introduction",
    },
    ("introduce", "recruit_culture"): {
        "article_type": "branding",
        "semantic_article_key": "recruit_culture",
    },
    ("case", "improvement"): {
        "article_type": "case_study",
        "semantic_article_key": "improvement_case",
    },
    ("case", "incident"): {
        "article_type": "case_study",
        "semantic_article_key": "incident_case",
    },
    ("case", "learning"): {
        "article_type": "case_study",
        "semantic_article_key": "learning_case",
    },
    ("compare", "method"): {
        "article_type": "comparative_review",
        "semantic_article_key": "comparative_review",
    },
    ("compare", "vendor"): {
        "article_type": "comparative_review",
        "semantic_article_key": "comparative_review",
    },
    ("daily", "behind_the_scenes"): {
        "article_type": "daily_story",
        "semantic_article_key": "daily_story",
    },
}
_JOURNEY_ROUTE_MAP: Dict[tuple[str, str], Dict[str, str]] = {
    **_CANONICAL_UI_JOURNEY_ROUTE_MAP,
    **_COMPAT_UI_JOURNEY_ROUTE_MAP,
}

_LEGACY_DEFAULT_SEMANTIC_KEYS: Dict[str, str] = {
    "explanatory_article": "explanatory_article",
    "daily_story": "daily_story",
    "branding": "branding",
    "announcement": "announcement",
    "case_study": "case_study",
    "industry_analysis": "industry_analysis",
    "comparative_review": "comparative_review",
}

_PERSPECTIVE_MODE_FIELD = "perspective_mode"
_PERSPECTIVE_MODE_COMPANY_INTRO = "company_intro"
_PERSPECTIVE_MODE_GENERAL_EXPLAINER = "general_explainer"
_PERSPECTIVE_CONFIRMATION_OPTIONS: tuple[Dict[str, str], ...] = (
    {
        "value": _PERSPECTIVE_MODE_COMPANY_INTRO,
        "label": "この会社として紹介する",
        "description": "会社の立場で紹介記事として書きます。",
    },
    {
        "value": _PERSPECTIVE_MODE_GENERAL_EXPLAINER,
        "label": "この会社を例に解説する",
        "description": "会社は事例として扱い、一般論の解説記事として書きます。",
    },
)
_PERSPECTIVE_COMPANY_INTRO_SPEAKER_RESETS = {
    "編集担当として語る",
    "解説担当として語る",
    "専門家として語る",
    "アナリストとして語る",
    "比較検証担当として語る",
}
_COMPANY_INTRO_AUTO_SPEAKER_PROFILE = "自動判定"
_COMPANY_INTRO_AUTO_SPEAKER_SOURCE = "company_intro_auto_neutral"


def _normalize_unique_string_list(values: Iterable[Any] | None, *, limit: int = 4) -> list[str]:
    normalized: list[str] = []
    if values is None:
        return normalized
    for item in values:
        text = str(item or "").strip()
        if not text or text in normalized:
            continue
        normalized.append(text[:40])
        if len(normalized) >= limit:
            break
    return normalized


def _normalize_perspective_mode(interview_answers: Mapping[str, Any] | None) -> str:
    value = str(dict(interview_answers or {}).get(_PERSPECTIVE_MODE_FIELD) or "").strip().lower()
    if value in {
        _PERSPECTIVE_MODE_COMPANY_INTRO,
        _PERSPECTIVE_MODE_GENERAL_EXPLAINER,
    }:
        return value
    return ""


def _normalize_source_hosts(source_documents: Iterable[Any] | None) -> list[str]:
    hosts: list[str] = []
    for item in source_documents or []:
        if not isinstance(item, Mapping):
            continue
        locator = str(item.get("locator") or item.get("url") or "").strip()
        if not locator.lower().startswith(("http://", "https://")):
            continue
        host = urlparse(locator).hostname or ""
        host = host.strip().lower()
        if host.startswith("www."):
            host = host[4:]
        if host and host not in hosts:
            hosts.append(host)
    return hosts


def _apply_confirmed_perspective_selection(
    resolved_selection: Mapping[str, Any],
    *,
    interview_answers: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_selection = dict(resolved_selection or {})
    if _normalize_perspective_mode(interview_answers) != _PERSPECTIVE_MODE_COMPANY_INTRO:
        return normalized_selection
    normalized_selection["article_type"] = "branding"
    normalized_selection["semantic_article_key"] = "company_introduction"
    normalized_selection["comparison_axes"] = []
    ui_journey = dict(normalized_selection.get("ui_journey") or {})
    if ui_journey:
        ui_journey["purpose_key"] = "introduce"
        ui_journey["target_key"] = "company"
        ui_journey["comparison_axes"] = []
        normalized_selection["ui_journey"] = ui_journey
    return normalized_selection


def _normalize_speaker_profile_for_confirmed_perspective(
    speaker_profile_input: str,
    *,
    interview_answers: Mapping[str, Any] | None,
) -> str:
    normalized = str(speaker_profile_input or "").strip()
    if _normalize_perspective_mode(interview_answers) != _PERSPECTIVE_MODE_COMPANY_INTRO:
        return normalized
    if normalized in _PERSPECTIVE_COMPANY_INTRO_SPEAKER_RESETS:
        return ""
    return normalized


def _neutralize_company_intro_auto_speaker_profile(
    contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_contract = dict(contract or {})
    if str(normalized_contract.get("semantic_article_key") or "").strip() != "company_introduction":
        return normalized_contract
    field_sources = dict(normalized_contract.get("field_sources") or {})
    if str(field_sources.get("speaker_profile") or "") != "ui_auto_default":
        return normalized_contract
    normalized_contract["speaker_profile"] = _COMPANY_INTRO_AUTO_SPEAKER_PROFILE
    field_sources["speaker_profile"] = _COMPANY_INTRO_AUTO_SPEAKER_SOURCE
    normalized_contract["field_sources"] = field_sources
    return normalized_contract


def _build_perspective_confirmation_question_item(
    contract: Mapping[str, Any] | None,
    *,
    interview_answers: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    normalized_contract = dict(contract or {})
    if _normalize_perspective_mode(interview_answers):
        return None
    ui_journey = dict(normalized_contract.get("ui_journey") or {})
    if (
        str(ui_journey.get("purpose_key") or "") != "explain"
        or str(ui_journey.get("target_key") or "") != "concept"
        or str(normalized_contract.get("semantic_article_key") or "") != "explanatory_article"
    ):
        return None
    source_documents = [
        dict(item)
        for item in list(normalized_contract.get("source_documents") or [])
        if isinstance(item, Mapping)
    ]
    if not source_documents:
        return None
    source_fit = dict(normalized_contract.get("source_fit") or {})
    candidate_targets = {
        str(item or "").strip()
        for item in list(source_fit.get("candidate_targets") or [])
        if str(item or "").strip()
    }
    matched_signals = dict(source_fit.get("matched_signals") or {})
    company_signal = int(matched_signals.get("company") or 0)
    if "company_introduction" not in candidate_targets and company_signal < 2:
        return None
    source_hosts = _normalize_source_hosts(source_documents)
    if source_hosts and len(source_hosts) > 1:
        return None
    return {
        "field": _PERSPECTIVE_MODE_FIELD,
        "issue_type": "route_confirmation",
        "required_format": "選択肢から1つ選ぶ",
        "question_template": "このソースは会社紹介としても読めます。この記事はどの視点で書きますか？",
        "example_answer": str(_PERSPECTIVE_CONFIRMATION_OPTIONS[0]["label"] or ""),
        "options": [dict(option) for option in _PERSPECTIVE_CONFIRMATION_OPTIONS],
    }


def _build_current_mainline_raw_input_contract(
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
    speaker_profile_input: str = "",
    audience_profile_input: str = "",
    core_message_input: str = "",
    branding_subtype_key: str = "",
    branding_focus_key: str = "",
    pattern_key: str = "auto",
    system_hint_items: Iterable[Any] | None = None,
    retry_memo: Iterable[Any] | None = None,
    strict_saas_mode: str = "medium",
    ui_journey: Mapping[str, Any] | None = None,
    comparison_axes: Iterable[Any] | None = None,
    body_generation_experiment: str = "",
) -> Dict[str, Any]:
    resolved_selection = resolve_current_mainline_ui_selection(
        article_type=article_type,
        ui_journey=ui_journey,
        comparison_axes=comparison_axes,
    )
    adjusted_selection = _apply_confirmed_perspective_selection(
        resolved_selection,
        interview_answers=interview_answers,
    )
    profiled_selection = _resolve_profiled_selection(
        resolved_selection=adjusted_selection,
        content_goal_key=content_goal_key,
        writing_focus_key=writing_focus_key,
        tone_profile_key=tone_profile_key,
        perspective_key=perspective_key,
        relationship_mode=relationship_mode,
        branding_subtype_key=branding_subtype_key,
        branding_focus_key=branding_focus_key,
        pattern_key=pattern_key,
        system_hint_items=system_hint_items,
    )
    normalized_speaker_profile_input = _normalize_speaker_profile_for_confirmed_perspective(
        speaker_profile_input,
        interview_answers=interview_answers,
    )
    raw_input_contract = build_raw_input_contract(
        source_values=source_values,
        source_documents=source_documents,
        article_type=str(profiled_selection.get("article_type") or article_type),
        user_prompt_text=user_prompt_text,
        content_goal_key=content_goal_key,
        writing_focus_key=writing_focus_key,
        structure_key=structure_key,
        length_mode_key=length_mode_key,
        tone_profile_key=tone_profile_key,
        perspective_key=perspective_key,
        allow_experience=allow_experience,
        interview_answers=interview_answers,
        media=media,
        relationship_mode=relationship_mode,
        speaker_profile_input=normalized_speaker_profile_input,
        audience_profile_input=audience_profile_input,
        core_message_input=core_message_input,
        system_hint_items=profiled_selection.get("system_hint_items"),
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        ui_journey=profiled_selection.get("ui_journey"),
        semantic_article_key=str(profiled_selection.get("semantic_article_key") or ""),
        comparison_axes=profiled_selection.get("comparison_axes"),
        body_generation_experiment=body_generation_experiment,
    )
    raw_input_contract = _neutralize_company_intro_auto_speaker_profile(raw_input_contract)
    return {
        "resolved_selection": adjusted_selection,
        "profiled_selection": profiled_selection,
        "raw_input_contract": raw_input_contract,
    }


def _build_direct_input_refinement_items(
    contract: Mapping[str, Any] | None,
    *,
    reason: str,
) -> list[dict[str, str]]:
    article_type = str(dict(contract or {}).get("article_type") or "").strip().lower()
    if reason not in {"default_needs_clarification", "category_requires_clarification", "announcement_missing_detail"}:
        return []
    example_by_article_type = {
        "explanatory_article": "実務担当者向けに、AI活用の基本と判断軸を解説したい",
        "industry_analysis": "意思決定者向けに、市場の変化と見るべき論点を整理したい",
        "comparative_review": "比較検討中の担当者向けに、選定軸ごとの差を整理したい",
        "branding": "初めて会社を知る読者向けに、事業内容と強みを紹介したい",
        "announcement": "既存ユーザー向けに、変更点と対応の要否を明確に伝えたい",
        "case_study": "同じ課題を持つ担当者向けに、改善前後の違いと再現条件を共有したい",
        "daily_story": "普段の取り組みに関心がある読者向けに、現場の気づきを共有したい",
    }
    return [
        {
            "field": "topic",
            "issue_type": "ambiguous",
            "required_format": "指示内容に、誰向けか・何を伝えるかを1文で補う",
            "question_template": "指示内容に、誰向けかと何を伝えたいかをもう少し具体的に書けますか？",
            "example_answer": example_by_article_type.get(
                article_type,
                "誰向けかと何を伝えたいかを1文で具体化する",
            ),
        }
    ]


def _normalize_ui_journey(ui_journey: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(ui_journey, Mapping):
        return {}
    normalized: Dict[str, Any] = {}
    for key in ("purpose_key", "target_key", "detail_key"):
        value = str(ui_journey.get(key) or "").strip().lower()
        if value:
            normalized[key] = value
    normalized["comparison_axes"] = _normalize_unique_string_list(ui_journey.get("comparison_axes"))
    return normalized


def _merge_system_hint_items(*item_groups: Iterable[Any] | None) -> list[str]:
    merged: list[str] = []
    for group in item_groups:
        for item in group or []:
            text = str(item or "").strip()
            if not text or text in merged:
                continue
            merged.append(text[:120])
            if len(merged) >= 4:
                return merged
    return merged


def _resolve_profiled_selection(
    *,
    resolved_selection: Mapping[str, Any],
    content_goal_key: str,
    writing_focus_key: str,
    tone_profile_key: str,
    perspective_key: str,
    relationship_mode: str,
    branding_subtype_key: str,
    branding_focus_key: str,
    pattern_key: str,
    system_hint_items: Iterable[Any] | None,
) -> Dict[str, Any]:
    profiled_selection = dict(resolved_selection or {})
    writing_profile = resolve_compact_writing_profile(
        article_type=str(profiled_selection.get("article_type") or ""),
        semantic_article_key=str(profiled_selection.get("semantic_article_key") or ""),
        content_goal_key=content_goal_key,
        writing_focus_key=writing_focus_key,
        tone_profile_key=tone_profile_key,
        perspective_key=perspective_key,
        relationship_mode=relationship_mode,
        branding_subtype_key=branding_subtype_key,
        branding_focus_key=branding_focus_key,
        pattern_key=pattern_key,
        system_hint_items=system_hint_items,
    )
    profiled_selection["semantic_article_key"] = str(
        writing_profile.get("semantic_article_key") or profiled_selection.get("semantic_article_key") or ""
    )
    profiled_selection["writing_profile"] = writing_profile
    profiled_selection["system_hint_items"] = _merge_system_hint_items(
        system_hint_items,
        writing_profile.get("system_hint_items"),
    )
    return profiled_selection


def resolve_current_mainline_ui_selection(
    *,
    article_type: str,
    ui_journey: Mapping[str, Any] | None = None,
    comparison_axes: Iterable[Any] | None = None,
) -> Dict[str, Any]:
    build_vnext_current_boundary_summary()
    normalized_journey = _normalize_ui_journey(ui_journey)
    normalized_axes = _normalize_unique_string_list(
        comparison_axes if comparison_axes is not None else normalized_journey.get("comparison_axes")
    )
    if normalized_journey:
        purpose_key = str(normalized_journey.get("purpose_key") or "")
        target_key = str(normalized_journey.get("target_key") or "")
        route = _JOURNEY_ROUTE_MAP.get((purpose_key, target_key))
        if route is None:
            raise InputContractValidationError(
                "unsupported ui_journey target",
                reason_code="INP_UNSUPPORTED_CHOICE",
                field="ui_journey",
            )
        normalized_journey["comparison_axes"] = (
            list(normalized_axes) if route["article_type"] == "comparative_review" else []
        )
        return {
            "article_type": route["article_type"],
            "semantic_article_key": route["semantic_article_key"],
            "ui_journey": normalized_journey,
            "comparison_axes": list(normalized_journey.get("comparison_axes") or []),
        }

    normalized_article_type = normalize_article_type(article_type, allow_legacy_aliases=False)
    return {
        "article_type": normalized_article_type,
        "semantic_article_key": _LEGACY_DEFAULT_SEMANTIC_KEYS.get(
            normalized_article_type,
            normalized_article_type,
        ),
        "ui_journey": {},
        "comparison_axes": list(normalized_axes) if normalized_article_type == "comparative_review" else [],
    }


def build_current_mainline_input_contract(
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
    speaker_profile_input: str = "",
    audience_profile_input: str = "",
    core_message_input: str = "",
    branding_subtype_key: str = "",
    branding_focus_key: str = "",
    pattern_key: str = "auto",
    system_hint_items: Iterable[Any] | None = None,
    retry_memo: Iterable[Any] | None = None,
    strict_saas_mode: str = "medium",
    ui_journey: Mapping[str, Any] | None = None,
    comparison_axes: Iterable[Any] | None = None,
    body_generation_experiment: str = "",
) -> Dict[str, Any]:
    raw_input_contract_bundle = _build_current_mainline_raw_input_contract(
        source_values=source_values,
        source_documents=source_documents,
        article_type=article_type,
        user_prompt_text=user_prompt_text,
        content_goal_key=content_goal_key,
        writing_focus_key=writing_focus_key,
        structure_key=structure_key,
        length_mode_key=length_mode_key,
        tone_profile_key=tone_profile_key,
        perspective_key=perspective_key,
        allow_experience=allow_experience,
        interview_answers=interview_answers,
        media=media,
        relationship_mode=relationship_mode,
        speaker_profile_input=speaker_profile_input,
        audience_profile_input=audience_profile_input,
        core_message_input=core_message_input,
        branding_subtype_key=branding_subtype_key,
        branding_focus_key=branding_focus_key,
        pattern_key=pattern_key,
        system_hint_items=system_hint_items,
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        ui_journey=ui_journey,
        comparison_axes=comparison_axes,
        body_generation_experiment=body_generation_experiment,
    )
    raw_input_contract = dict(raw_input_contract_bundle.get("raw_input_contract") or {})
    return normalize_input_contract_v1(raw_input_contract, allow_legacy_aliases=False)


def assess_current_mainline_question_policy(
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
    speaker_profile_input: str = "",
    audience_profile_input: str = "",
    core_message_input: str = "",
    branding_subtype_key: str = "",
    branding_focus_key: str = "",
    pattern_key: str = "auto",
    system_hint_items: Iterable[Any] | None = None,
    retry_memo: Iterable[Any] | None = None,
    strict_saas_mode: str = "medium",
    ui_journey: Mapping[str, Any] | None = None,
    comparison_axes: Iterable[Any] | None = None,
    body_generation_experiment: str = "",
) -> Dict[str, Any]:
    raw_input_contract_bundle = _build_current_mainline_raw_input_contract(
        source_values=source_values,
        source_documents=source_documents,
        article_type=article_type,
        user_prompt_text=user_prompt_text,
        content_goal_key=content_goal_key,
        writing_focus_key=writing_focus_key,
        structure_key=structure_key,
        length_mode_key=length_mode_key,
        tone_profile_key=tone_profile_key,
        perspective_key=perspective_key,
        allow_experience=allow_experience,
        interview_answers=interview_answers,
        media=media,
        relationship_mode=relationship_mode,
        speaker_profile_input=speaker_profile_input,
        audience_profile_input=audience_profile_input,
        core_message_input=core_message_input,
        branding_subtype_key=branding_subtype_key,
        branding_focus_key=branding_focus_key,
        pattern_key=pattern_key,
        system_hint_items=system_hint_items,
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        ui_journey=ui_journey,
        comparison_axes=comparison_axes,
        body_generation_experiment=body_generation_experiment,
    )
    raw_input_contract = dict(raw_input_contract_bundle.get("raw_input_contract") or {})
    resolved = resolve_input_contract(raw_input_contract)
    contract = dict(resolved.contract or {})
    need_question_decision = dict(contract.get("need_question", {}) or {})
    input_decision = dict(contract.get("input_decision", {}) or {})
    needs_input_items = list(input_decision.get("needs_input_items", []) or [])
    question_items = [
        dict(item)
        for item in list(input_decision.get("question_items", []) or [])
        if str(dict(item).get("field") or "").strip()
    ]
    action = str(input_decision.get("action") or "accept")
    need_question_ask = bool(need_question_decision.get("ask"))
    perspective_confirmation_item = _build_perspective_confirmation_question_item(
        contract,
        interview_answers=interview_answers,
    )
    if action == "accept" and need_question_ask and not question_items and perspective_confirmation_item is None:
        needs_input_items = _build_direct_input_refinement_items(
            contract,
            reason=str(need_question_decision.get("reason") or ""),
        )
    if (
        perspective_confirmation_item is not None
        and action != "block"
        and not any(str(item.get("field") or "") == _PERSPECTIVE_MODE_FIELD for item in question_items)
    ):
        question_items = [perspective_confirmation_item, *question_items]
    should_ask = bool(question_items) and (
        action == "clarify"
        or (
            action == "accept"
            and (need_question_ask or perspective_confirmation_item is not None)
        )
    )
    reason = str(input_decision.get("reason") or "unknown")
    reason_code = str(input_decision.get("reason_code") or "")
    if action == "accept" and perspective_confirmation_item is not None:
        reason = "perspective_confirmation_required"
        reason_code = "INP_NEEDS_CLARIFICATION"
    if action == "accept" and need_question_ask and needs_input_items and not question_items:
        reason = str(need_question_decision.get("reason") or reason)
        reason_code = "INP_NEEDS_CLARIFICATION"
    return {
        "should_ask": should_ask,
        "blocked": action == "block",
        "reason": reason,
        "reason_code": reason_code,
        "need_question_decision": need_question_decision,
        "needs_input_items": needs_input_items,
        "question_items": question_items,
        "answerable_missing_items": question_items,
        "contract": contract,
        "writing_profile": dict(raw_input_contract_bundle.get("profiled_selection", {}).get("writing_profile") or {}),
    }


def build_current_mainline_confirm_preview(
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
    speaker_profile_input: str = "",
    audience_profile_input: str = "",
    core_message_input: str = "",
    branding_subtype_key: str = "",
    branding_focus_key: str = "",
    pattern_key: str = "auto",
    system_hint_items: Iterable[Any] | None = None,
    retry_memo: Iterable[Any] | None = None,
    strict_saas_mode: str = "medium",
    ui_journey: Mapping[str, Any] | None = None,
    comparison_axes: Iterable[Any] | None = None,
    body_generation_experiment: str = "",
) -> Dict[str, Any]:
    contract = build_current_mainline_input_contract(
        source_values=source_values,
        source_documents=source_documents,
        article_type=article_type,
        user_prompt_text=user_prompt_text,
        content_goal_key=content_goal_key,
        writing_focus_key=writing_focus_key,
        structure_key=structure_key,
        length_mode_key=length_mode_key,
        tone_profile_key=tone_profile_key,
        perspective_key=perspective_key,
        allow_experience=allow_experience,
        interview_answers=interview_answers,
        media=media,
        relationship_mode=relationship_mode,
        speaker_profile_input=speaker_profile_input,
        audience_profile_input=audience_profile_input,
        core_message_input=core_message_input,
        branding_subtype_key=branding_subtype_key,
        branding_focus_key=branding_focus_key,
        pattern_key=pattern_key,
        system_hint_items=system_hint_items,
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        ui_journey=ui_journey,
        comparison_axes=comparison_axes,
        body_generation_experiment=body_generation_experiment,
    )
    resolved = resolve_input_contract(contract)
    resolved_contract = dict(resolved.contract or {})
    input_decision = dict(resolved_contract.get("input_decision") or {})
    source_fit = dict(resolved_contract.get("source_fit") or {})
    perspective_confirmation_item = _build_perspective_confirmation_question_item(
        resolved_contract,
        interview_answers=interview_answers,
    )
    needs_input_items = list(input_decision.get("needs_input_items", []) or [])
    if perspective_confirmation_item is not None and str(input_decision.get("action") or "accept") == "accept":
        input_decision = dict(input_decision)
        input_decision["action"] = "clarify"
        input_decision["reason"] = "perspective_confirmation_required"
        input_decision["reason_code"] = "INP_NEEDS_CLARIFICATION"
        needs_input_items = [perspective_confirmation_item]
    return {
        "article_type": str(resolved_contract.get("article_type") or ""),
        "semantic_article_key": str(resolved_contract.get("semantic_article_key") or ""),
        "ui_journey": dict(resolved_contract.get("ui_journey") or {}),
        "comparison_axes": list(resolved_contract.get("comparison_axes") or []),
        "source_fit": source_fit,
        "input_decision": input_decision,
        "needs_input_items": needs_input_items,
        "allow_generate": str(input_decision.get("action") or "accept") == "accept",
        "contract": resolved_contract,
        "writing_profile": resolve_compact_writing_profile(
            article_type=str(resolved_contract.get("article_type") or ""),
            semantic_article_key=str(resolved_contract.get("semantic_article_key") or ""),
            content_goal_key=str(resolved_contract.get("content_goal") or ""),
            writing_focus_key=str(resolved_contract.get("writing_focus") or ""),
            tone_profile_key=str(resolved_contract.get("tone_profile") or ""),
            perspective_key=str(resolved_contract.get("perspective") or ""),
            relationship_mode=str(resolved_contract.get("relationship_mode") or ""),
            branding_subtype_key=branding_subtype_key,
            branding_focus_key=branding_focus_key,
            pattern_key=pattern_key,
            system_hint_items=resolved_contract.get("system_hint_items"),
        ),
    }


def _normalize_pipeline_error_result(
    result: Mapping[str, Any] | None,
    *,
    input_contract: Mapping[str, Any] | None,
    reason_code: str,
    error_class: str,
) -> Dict[str, Any]:
    normalized = build_fail_closed_generation_result(
        input_contract=input_contract,
        reason_code=reason_code,
        error_class=error_class,
    )
    incoming = dict(result or {})
    normalized.update(incoming)
    normalized["success"] = False
    normalized["pipeline_source"] = "newalgorithm_mainline"
    normalized["reason_code"] = str(incoming.get("reason_code") or reason_code or "SYS_PIPELINE_FAILURE")
    normalized["runtime_reason_code"] = str(
        incoming.get("runtime_reason_code")
        or incoming.get("reason_code")
        or reason_code
        or "SYS_PIPELINE_FAILURE"
    )
    normalized["runtime_error_class"] = str(
        incoming.get("runtime_error_class") or error_class or "system"
    )
    pipeline_check = dict(normalized.get("pipeline_check") or {})
    incoming_pipeline_check = incoming.get("pipeline_check")
    if isinstance(incoming_pipeline_check, Mapping):
        pipeline_check.update(dict(incoming_pipeline_check))
    pipeline_check.setdefault("input_contract", dict(input_contract or {}))
    normalized["pipeline_check"] = pipeline_check
    return normalized


def _attach_vnext_shadow_projection(result: Mapping[str, Any] | None) -> Dict[str, Any]:
    normalized_result = dict(result or {})
    pipeline_check = dict(normalized_result.get("pipeline_check") or {})
    current_contract = pipeline_check.get("input_contract")
    if not isinstance(current_contract, Mapping):
        return normalized_result
    try:
        thin_contract = adapt_current_contract_to_vnext(current_contract)
        vnext_result = VNextPipeline().generate(thin_contract)
        shadow_projection = build_vnext_shadow_projection(
            vnext_result=vnext_result,
            current_result=normalized_result,
        )
    except Exception as exc:
        shadow_projection = {
            "enabled": True,
            "mode": "shadow",
            "success": False,
            "owner": "note.vnext.pipeline.VNextPipeline",
            "error": str(exc),
        }
    pipeline_check["vnext_shadow"] = shadow_projection
    normalized_result["pipeline_check"] = pipeline_check
    normalized_result["vnext_shadow"] = shadow_projection
    return normalized_result


def _build_phase04_cutover_rehearsal_summary(
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    if not isinstance(input_contract, Mapping):
        return {}
    article_type = str(input_contract.get("article_type") or "").strip()
    semantic_article_key = str(input_contract.get("semantic_article_key") or "").strip()
    if article_type != "branding" or semantic_article_key != "company_introduction":
        return {}
    return {
        "route_key": "branding/company_introduction",
        "approval_state": "approved",
        "selected_engine": "current_mainline",
        "candidate_engine": "vnext_shadow",
        "selection_reason": "phase04_rehearsal_keeps_current_control_plane_until_phase05_promotion",
        "fallback_engine": "current_mainline",
        "fallback_reason": "phase04_rehearsal_is_not_route_promotion",
    }


def _attach_phase04_cutover_rehearsal_summary(
    result: Mapping[str, Any] | None,
    *,
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_result = dict(result or {})
    summary = _build_phase04_cutover_rehearsal_summary(input_contract)
    if not summary:
        return normalized_result
    pipeline_check = dict(normalized_result.get("pipeline_check") or {})
    pipeline_check["cutover_rehearsal"] = summary
    normalized_result["pipeline_check"] = pipeline_check
    return normalized_result


def _apply_user_prompt_to_input_contract(
    input_contract: Mapping[str, Any] | None,
    *,
    user_prompt_text: str,
) -> Dict[str, Any]:
    normalized_input_contract = dict(input_contract or {})
    prompt_raw = str(
        user_prompt_text
        or normalized_input_contract.get("prompt_raw")
        or normalized_input_contract.get("topic")
        or ""
    ).strip()
    if prompt_raw:
        normalized_input_contract["prompt_raw"] = prompt_raw
        normalized_input_contract["topic"] = prompt_raw
    return normalized_input_contract


def _hydrate_compatibility_source_documents(
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_input_contract = dict(input_contract or {})
    input_decision = dict(normalized_input_contract.get("input_decision") or {})
    if str(input_decision.get("action") or "accept").strip().lower() != "accept":
        return normalized_input_contract
    if list(normalized_input_contract.get("source_documents") or []):
        return normalized_input_contract
    source_inputs = [
        str(item or "").strip()
        for item in list(normalized_input_contract.get("source_inputs") or [])
        if str(item or "").strip()
    ]
    if not source_inputs:
        return normalized_input_contract
    compatibility_seed = str(
        normalized_input_contract.get("topic_statement")
        or normalized_input_contract.get("prompt_raw")
        or normalized_input_contract.get("topic")
        or "参照URLをもとに主題を整理するための互換コンテキストです。"
    ).strip()
    normalized_input_contract["source_documents"] = [
        {
            "title": f"Compatibility Source {index}",
            "locator": locator,
            "source_type": "url" if locator.lower().startswith(("http://", "https://")) else "text",
            "content": compatibility_seed,
        }
        for index, locator in enumerate(source_inputs[:4], start=1)
    ]
    compatibility_bridge = dict(normalized_input_contract.get("compatibility_bridge") or {})
    compatibility_bridge["hydrated_source_documents"] = True
    compatibility_bridge["hydrated_source_count"] = len(normalized_input_contract["source_documents"])
    normalized_input_contract["compatibility_bridge"] = compatibility_bridge
    return normalized_input_contract


def _normalize_execution_input_contract(
    input_contract: Mapping[str, Any] | None,
    *,
    user_prompt_text: str,
) -> Dict[str, Any]:
    normalized_input_contract = _apply_user_prompt_to_input_contract(
        input_contract,
        user_prompt_text=user_prompt_text,
    )
    if "input_decision" not in normalized_input_contract or "need_question" not in normalized_input_contract:
        try:
            normalized_input_contract = dict(
                resolve_input_contract(normalized_input_contract).contract or normalized_input_contract
            )
        except Exception:
            normalized_input_contract = _apply_user_prompt_to_input_contract(
                input_contract,
                user_prompt_text=user_prompt_text,
            )
    normalized_input_contract.pop("body_generation_experiment", None)
    field_sources = dict(normalized_input_contract.get("field_sources") or {})
    if "body_generation_experiment" in field_sources:
        field_sources.pop("body_generation_experiment", None)
        normalized_input_contract["field_sources"] = field_sources
    return _hydrate_compatibility_source_documents(normalized_input_contract)


def _run_current_mainline_pipeline(
    pipeline: CurrentMainlinePipeline,
    *,
    payload: Mapping[str, Any],
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    try:
        return dict(pipeline.generate(payload))
    except Exception as exc:
        return _normalize_pipeline_error_result(
            {
                "pipeline_check": {
                    "input_contract": dict(input_contract or {}),
                    "error": {
                        "message": str(exc),
                        "reason_code": "SYS_PIPELINE_FAILURE",
                    },
                }
            },
            input_contract=input_contract,
            reason_code="SYS_PIPELINE_FAILURE",
            error_class="system",
        )


def _finalize_current_mainline_result(
    result: Mapping[str, Any] | None,
    *,
    input_contract: Mapping[str, Any] | None,
    boundary_summary: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_result = dict(result or {})
    if bool(normalized_result.get("success", False)):
        normalized_result = apply_generation_output_guard(normalized_result)
        normalized_result = _attach_vnext_shadow_projection(normalized_result)
    if not bool(normalized_result.get("success", False)):
        normalized_result = _normalize_pipeline_error_result(
            normalized_result,
            input_contract=input_contract,
            reason_code=str(normalized_result.get("reason_code") or "SYS_PIPELINE_FAILURE"),
            error_class=str(normalized_result.get("runtime_error_class") or "system"),
        )
    normalized_result = _attach_phase04_cutover_rehearsal_summary(
        normalized_result,
        input_contract=input_contract,
    )
    pipeline_check = dict(normalized_result.get("pipeline_check") or {})
    pipeline_check["boundary_freeze"] = dict(boundary_summary or {})
    normalized_result["pipeline_check"] = pipeline_check
    normalized_result["pipeline_source"] = "newalgorithm_mainline"
    return normalized_result


def execute_current_mainline_generation(
    pipeline: CurrentMainlinePipeline,
    input_contract: Mapping[str, Any] | None,
    user_prompt_text: str,
) -> Dict[str, Any]:
    boundary_summary = build_vnext_current_boundary_summary()
    normalized_input_contract = _normalize_execution_input_contract(
        input_contract,
        user_prompt_text=user_prompt_text,
    )
    payload = build_pipeline_payload(
        normalized_input_contract,
        user_prompt_text=user_prompt_text,
    )
    result = _run_current_mainline_pipeline(
        pipeline,
        payload=payload,
        input_contract=normalized_input_contract,
    )
    return _finalize_current_mainline_result(
        result,
        input_contract=normalized_input_contract,
        boundary_summary=boundary_summary,
    )


def build_fail_closed_generation_result(
    *,
    input_contract: Mapping[str, Any] | None,
    reason_code: str,
    error_class: str,
) -> Dict[str, Any]:
    return {
        "success": False,
        "title": "",
        "lead": "",
        "body": "",
        "references": "",
        "hashtags": "",
        "full_text": "",
        "reason_code": str(reason_code or "SYS_PIPELINE_FAILURE"),
        "pipeline_source": "newalgorithm_mainline",
        "pipeline_check": {
            "input_contract": dict(input_contract or {}),
        },
        "runtime_error_class": str(error_class or "system"),
        "runtime_reason_code": str(reason_code or "SYS_PIPELINE_FAILURE"),
    }
