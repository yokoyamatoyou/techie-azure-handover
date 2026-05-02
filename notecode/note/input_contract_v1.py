"""Input contract v1 normalizer/validator for newalgorithm Phase01."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

FIXED_ARTICLE_TYPES: tuple[str, ...] = (
    "explanatory_article",
    "daily_story",
    "branding",
    "announcement",
    "case_study",
    "industry_analysis",
    "comparative_review",
)
FIXED_ARTICLE_TYPE_SET = set(FIXED_ARTICLE_TYPES)

SUPPORTED_MEDIA: tuple[str, ...] = ("note", "hatena", "seo")
SUPPORTED_MEDIA_SET = set(SUPPORTED_MEDIA)
PROMPT_ONLY_SOURCE_MODE = "prompt_only"
PROMPT_ONLY_ALLOWED_ARTICLE_TYPES: tuple[str, ...] = ("daily_story",)
PROMPT_ONLY_ALLOWED_ARTICLE_TYPE_SET = set(PROMPT_ONLY_ALLOWED_ARTICLE_TYPES)
SOURCE_MODES: tuple[str, ...] = ("grounded", "web", "followup", PROMPT_ONLY_SOURCE_MODE)
SOURCE_MODE_SET = set(SOURCE_MODES)
WEB_RESEARCH_ALLOWED_ARTICLE_TYPES: tuple[str, ...] = (
    "daily_story",
    "explanatory_article",
    "industry_analysis",
)
WEB_RESEARCH_ALLOWED_ARTICLE_TYPE_SET = set(WEB_RESEARCH_ALLOWED_ARTICLE_TYPES)

LEGACY_ARTICLE_TYPE_ALIASES: Dict[str, str] = {
    "ai": "explanatory_article",
    "daily_happenings": "daily_story",
    "corporate_culture": "branding",
    "company_profile": "branding",
    "company_introduction": "branding",
    "corporate": "branding",
}


class InputContractValidationError(ValueError):
    """Validation error for input contract v1."""

    def __init__(
        self,
        message: str,
        *,
        reason_code: str = "validation_error",
        field: str = "",
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.field = field


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_source_list(value: Any) -> List[str]:
    if isinstance(value, str):
        text = _normalize_text(value)
        return [text] if text else []
    if not isinstance(value, Iterable):
        return []
    normalized: List[str] = []
    for item in value:
        text = _normalize_text(item)
        if not text:
            continue
        normalized.append(text)
    return normalized


def _normalize_source_document_markers(value: Any) -> List[str]:
    if isinstance(value, str):
        text = _normalize_text(value)
        return [text] if text else []
    if not isinstance(value, Iterable):
        return []
    normalized: List[str] = []
    for item in value:
        if isinstance(item, Mapping):
            text = _normalize_text(
                item.get("content")
                or item.get("text")
                or item.get("summary")
                or item.get("excerpt")
                or item.get("locator")
                or item.get("url")
                or item.get("title")
            )
        else:
            text = _normalize_text(item)
        if text:
            normalized.append(text)
    return normalized


def prompt_only_seed_text(payload: Mapping[str, Any] | None) -> str:
    normalized = dict(payload or {})
    for field in ("prompt_raw", "topic", "topic_statement", "user_instruction"):
        text = _normalize_text(normalized.get(field))
        if text:
            return text
    return ""


def prompt_only_has_source_conflict(payload: Mapping[str, Any] | None) -> bool:
    normalized = dict(payload or {})
    source_list = _normalize_source_list(normalized.get("source_inputs"))
    if not source_list:
        source_list = _normalize_source_list(normalized.get("source"))
    return bool(source_list or _normalize_source_document_markers(normalized.get("source_documents")))


def is_prompt_only_source_less_generation_allowed(payload: Mapping[str, Any] | None) -> bool:
    normalized = dict(payload or {})
    return bool(
        _normalize_text(normalized.get("source_mode")).lower() == PROMPT_ONLY_SOURCE_MODE
        and _normalize_text(normalized.get("article_type")).lower() in PROMPT_ONLY_ALLOWED_ARTICLE_TYPE_SET
        and prompt_only_seed_text(normalized)
        and not prompt_only_has_source_conflict(normalized)
    )


def normalize_article_type(article_type: Any, *, allow_legacy_aliases: bool = True) -> str:
    key = _normalize_text(article_type).lower()
    if key in FIXED_ARTICLE_TYPE_SET:
        return key
    if allow_legacy_aliases and key in LEGACY_ARTICLE_TYPE_ALIASES:
        return LEGACY_ARTICLE_TYPE_ALIASES[key]
    raise InputContractValidationError(
        "unsupported article_type",
        reason_code="INP_UNSUPPORTED_ARTICLE_TYPE",
        field="article_type",
    )


def normalize_media(media: Any) -> str:
    key = _normalize_text(media).lower() or "note"
    if key in SUPPORTED_MEDIA_SET:
        return key
    raise InputContractValidationError(
        "unsupported media",
        reason_code="INP_UNSUPPORTED_MEDIA",
        field="media",
    )


def normalize_source_mode(source_mode: Any) -> str:
    key = _normalize_text(source_mode).lower() or "grounded"
    if key in SOURCE_MODE_SET:
        return key
    raise InputContractValidationError(
        "unsupported source_mode",
        reason_code="INP_UNSUPPORTED_CHOICE",
        field="source_mode",
    )


def normalize_input_contract_v1(
    payload: Optional[Dict[str, Any]],
    *,
    allow_legacy_aliases: bool = True,
) -> Dict[str, Any]:
    """Normalize and validate input contract to v1 schema."""
    if not isinstance(payload, dict):
        raise InputContractValidationError(
            "input_contract must be a dict",
            reason_code="INP_MISSING_REQUIRED",
            field="input_contract",
        )

    normalized = dict(payload)
    source_list = _normalize_source_list(payload.get("source_inputs"))
    if not source_list:
        source_list = _normalize_source_list(payload.get("source"))

    prompt_raw = _normalize_text(payload.get("prompt_raw"))
    topic = _normalize_text(payload.get("topic"))
    if not topic:
        topic = prompt_raw
    if not topic:
        topic = _normalize_text(payload.get("topic_statement"))
    if not topic:
        topic = _normalize_text(payload.get("user_instruction"))

    article_type = normalize_article_type(
        payload.get("article_type"),
        allow_legacy_aliases=allow_legacy_aliases,
    )
    media = normalize_media(payload.get("media"))
    source_mode = normalize_source_mode(payload.get("source_mode"))
    source_document_markers = _normalize_source_document_markers(payload.get("source_documents"))

    if source_mode == PROMPT_ONLY_SOURCE_MODE:
        if article_type not in PROMPT_ONLY_ALLOWED_ARTICLE_TYPE_SET:
            raise InputContractValidationError(
                "prompt_only source mode is allowed only for daily_story",
                reason_code="INP_PROMPT_ONLY_ARTICLE_TYPE_BLOCKED",
                field="source_mode",
            )
        if source_list or source_document_markers:
            raise InputContractValidationError(
                "prompt_only cannot be combined with source inputs",
                reason_code="INP_PROMPT_ONLY_SOURCE_CONFLICT",
                field="source",
            )
        if not topic:
            raise InputContractValidationError(
                "prompt_only requires prompt/topic",
                reason_code="INP_MISSING_REQUIRED",
                field="prompt_raw",
            )

    if not source_list and not topic:
        raise InputContractValidationError(
            "source/topic missing",
            reason_code="INP_MISSING_REQUIRED",
            field="source,topic",
        )

    style_compact_for_seo = bool(article_type == "daily_story" and media == "seo")
    question_mode = "skip_default" if article_type == "announcement" else "standard"
    web_research_allowed = bool(
        source_mode == "web"
        and article_type in WEB_RESEARCH_ALLOWED_ARTICLE_TYPE_SET
    )
    if source_mode == PROMPT_ONLY_SOURCE_MODE:
        source_trace_policy = "prompt_context_not_source"
    else:
        source_trace_policy = (
            "web_trace_required"
            if web_research_allowed
            else "source_documents_required"
        )
    industry_hint = _normalize_text(payload.get("industry_hint"))[:120]

    normalized["source"] = list(source_list)
    normalized["source_inputs"] = list(source_list)
    normalized["prompt_raw"] = prompt_raw or topic
    normalized["topic"] = topic
    normalized["article_type"] = article_type
    normalized["media"] = media
    normalized["source_mode"] = source_mode
    normalized["web_research_allowed"] = web_research_allowed
    normalized["industry_hint"] = industry_hint
    normalized["source_trace_policy"] = source_trace_policy
    normalized["prompt_context_is_source"] = (
        False if source_mode == PROMPT_ONLY_SOURCE_MODE else bool(source_list or source_document_markers)
    )
    normalized["prompt_only_allowed"] = bool(
        source_mode == PROMPT_ONLY_SOURCE_MODE
        and article_type in PROMPT_ONLY_ALLOWED_ARTICLE_TYPE_SET
    )
    normalized["style_compact_for_seo"] = style_compact_for_seo
    normalized["question_mode"] = question_mode
    normalized["contract_version"] = "input_contract_v1"

    return normalized


def validate_input_contract_v1(payload: Optional[Dict[str, Any]]) -> None:
    """Raise InputContractValidationError when payload is invalid."""
    normalize_input_contract_v1(payload)
