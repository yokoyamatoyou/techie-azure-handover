"""Helpers for invoking the current mainline from the UI shell."""
from __future__ import annotations

import json
import re
from types import SimpleNamespace
from typing import Any, Dict, Iterable, Mapping, Protocol
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from note.article_fetcher import ArticleFetcher
from note.generation_request_builder import build_pipeline_payload, build_raw_input_contract
from note.input_contract_v1 import (
    InputContractValidationError,
    PROMPT_ONLY_ALLOWED_ARTICLE_TYPE_SET,
    PROMPT_ONLY_SOURCE_MODE,
    WEB_RESEARCH_ALLOWED_ARTICLE_TYPE_SET,
    is_prompt_only_source_less_generation_allowed,
    normalize_article_type,
    normalize_input_contract_v1,
    prompt_only_has_source_conflict,
    prompt_only_seed_text,
)
from note.newalgorithm_pipeline.input_contract import resolve_input_contract
from note.newalgorithm_pipeline.output_guard import apply_generation_output_guard
from note.newalgorithm_pipeline.quality_observability_mixin import QualityObservabilityMixin
from note.current_mainline_profile_resolver import resolve_compact_writing_profile
from note.current_mainline_persona_trial import (
    build_persona_trial_telemetry,
    enrich_persona_trial_contract,
)
from note.omakase_seed_builder import (
    build_omakase_preflight as build_omakase_preflight_core,
    merge_omakase_seed_into_kwargs as merge_omakase_seed_into_kwargs_core,
)
from note.vnext.pipeline import VNextPipeline
from note.vnext_adapters.current_ui_contract_adapter import adapt_current_contract_to_vnext
from note.vnext_adapters.runtime_projection_adapter import build_vnext_shadow_projection
from note.vnext_current_boundary import build_vnext_current_boundary_summary


class CurrentMainlinePipeline(Protocol):
    def generate(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        ...


class _CurrentMainlineQualityBridge(QualityObservabilityMixin):
    def _build_quality_context(
        self,
        contract: Dict[str, Any],
        style_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        source_text = "\n".join(
            str(dict(item).get("content") or "")
            for item in list(contract.get("source_documents") or [])[:4]
            if isinstance(item, Mapping)
        )
        return {
            "platform": "note",
            "perspective": str(contract.get("perspective") or ""),
            "writing_focus": str(contract.get("writing_focus") or ""),
            "article_type": str(contract.get("article_type") or ""),
            "style_profile_hint": str(style_profile.get("profile_name") or ""),
            "tone_profile_hint": str(contract.get("tone_profile") or ""),
            "allow_experience": bool(contract.get("allow_experience")),
            "topic_hint": str(contract.get("topic_statement") or contract.get("topic") or ""),
            "writing_intent": str(contract.get("core_message") or contract.get("topic_statement") or ""),
            "target_audience": str(contract.get("audience_profile") or ""),
            "source_urls": list(contract.get("source_inputs") or contract.get("source") or []),
            "source_text": source_text,
        }

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
_WEB_RESEARCH_SEARCH_ENDPOINT = "https://html.duckduckgo.com/html/"
_WEB_RESEARCH_HEADERS = {"User-Agent": "Mozilla/5.0"}
_WEB_RESEARCH_MAX_QUERIES = 5
_WEB_RESEARCH_MAX_RESULTS_PER_QUERY = 5
_WEB_RESEARCH_MAX_DOCUMENTS = 4
_WEB_RESEARCH_MIN_DOCUMENTS = 2
_WEB_RESEARCH_AGGREGATOR_HOST_KEYWORDS = (
    "note.com",
    "togetter.com",
    "matome",
    "ameblo.jp",
    "hatenablog.com",
    "livedoor.blog",
    "fc2.com",
    "wikipedia.org",
)
_WEB_RESEARCH_OFFICIAL_HOST_SUFFIXES = (
    ".go.jp",
    ".gov",
    ".gov.jp",
    ".ac.jp",
    ".edu",
    ".or.jp",
    ".org",
)
_WEB_RESEARCH_ARTICLE_HINTS: Dict[str, tuple[str, ...]] = {
    "daily_story": ("最新", "発表", "事例"),
    "explanatory_article": ("最新", "解説", "発表"),
    "industry_analysis": ("市場動向", "調査", "統計"),
}
_WEB_TRACE_REQUIRED_FIELDS: tuple[str, ...] = ("query", "url", "publisher", "exact_date", "excerpt")
_GROUNDED_PROMPT_META_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"公開済みの投稿もありますが、?"),
    re.compile(r"過去の公開記事やお任せ候補がある場合でも、?"),
    re.compile(r"過去の公開記事がある場合でも、?"),
    re.compile(r"お任せ候補がある場合でも、?"),
    re.compile(r"今回の整理では添付資料を優先して考える必要があります。?"),
    re.compile(r"今回は添付した現場メモを中心に見直しています。?"),
)
_OMAKASE_PREFLIGHT_FIELDS: tuple[str, ...] = (
    "omakase_preflight_status",
    "omakase_charge_ready",
    "omakase_reason_code",
    "omakase_message",
    "omakase_fallback_options",
    "omakase_needs_input_items",
    "omakase_source_count",
    "omakase_existing_post_count",
    "omakase_usable_posts_count",
    "omakase_dominant_cluster_count",
    "omakase_available",
)


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


def _normalize_exact_date(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    for pattern in (
        r"((?:19|20)\d{2})[/-](\d{1,2})[/-](\d{1,2})",
        r"((?:19|20)\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日",
    ):
        match = re.search(pattern, text)
        if not match:
            continue
        year, month, day = match.groups()
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    return ""


def _extract_web_source_exact_date(soup: BeautifulSoup | None, html_text: str, fallback_text: str) -> str:
    if soup is not None:
        meta_candidates = [
            ('meta[property="article:published_time"]', "content"),
            ('meta[property="article:modified_time"]', "content"),
            ('meta[name="pubdate"]', "content"),
            ('meta[name="publish-date"]', "content"),
            ('meta[name="date"]', "content"),
            ('meta[itemprop="datePublished"]', "content"),
            ('meta[itemprop="dateModified"]', "content"),
            ("time[datetime]", "datetime"),
        ]
        for selector, attribute in meta_candidates:
            tag = soup.select_one(selector)
            if tag is None:
                continue
            exact_date = _normalize_exact_date(tag.get(attribute) or tag.get_text(" ", strip=True))
            if exact_date:
                return exact_date
    for pattern in (
        r'"datePublished"\s*:\s*"([^"]+)"',
        r'"dateModified"\s*:\s*"([^"]+)"',
    ):
        match = re.search(pattern, html_text)
        if not match:
            continue
        exact_date = _normalize_exact_date(match.group(1))
        if exact_date:
            return exact_date
    return _normalize_exact_date(fallback_text)


def _extract_web_source_publisher(soup: BeautifulSoup | None, locator: str) -> str:
    if soup is not None:
        for selector, attribute in (
            ('meta[property="og:site_name"]', "content"),
            ('meta[name="publisher"]', "content"),
            ('meta[property="article:publisher"]', "content"),
        ):
            tag = soup.select_one(selector)
            if tag is None:
                continue
            text = str(tag.get(attribute) or "").strip()
            if text:
                return text[:120]
        for pattern in (
            r'"publisher"\s*:\s*\{\s*"@type"\s*:\s*"[^"]+"\s*,\s*"name"\s*:\s*"([^"]+)"',
            r'"publisher"\s*:\s*\{\s*"name"\s*:\s*"([^"]+)"',
        ):
            match = re.search(pattern, str(soup))
            if match:
                return str(match.group(1) or "").strip()[:120]
    host = str(urlparse(locator).hostname or "").strip().lower()
    return host[:120]


def _build_web_research_queries(
    *,
    article_type: str,
    prompt_raw: str,
    industry_hint: str,
) -> list[str]:
    base_prompt = re.sub(r"\s+", " ", str(prompt_raw or "").strip())
    normalized_industry_hint = re.sub(r"\s+", " ", str(industry_hint or "").strip())
    article_hints = _WEB_RESEARCH_ARTICLE_HINTS.get(article_type, ("最新", "発表", "調査"))
    candidates = [
        " ".join(part for part in (base_prompt, normalized_industry_hint) if part),
        " ".join(part for part in (base_prompt, article_hints[0]) if part),
        " ".join(part for part in (base_prompt, article_hints[1]) if part),
        " ".join(part for part in (base_prompt, article_hints[2]) if part),
        " ".join(part for part in (normalized_industry_hint, base_prompt, "公式") if part),
    ]
    normalized_queries: list[str] = []
    for item in candidates:
        text = re.sub(r"\s+", " ", str(item or "").strip())
        if not text or text in normalized_queries:
            continue
        normalized_queries.append(text[:120])
        if len(normalized_queries) >= _WEB_RESEARCH_MAX_QUERIES:
            break
    return normalized_queries


def _hydrate_web_source_documents(
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_input_contract = dict(input_contract or {})
    if str(normalized_input_contract.get("source_mode") or "").strip().lower() != "web":
        return normalized_input_contract
    if list(normalized_input_contract.get("source_documents") or []):
        return normalized_input_contract
    if not bool(normalized_input_contract.get("web_research_allowed")):
        raise InputContractValidationError(
            "web research blocked for article_type",
            reason_code="INP_WEB_SOURCE_MODE_BLOCKED",
            field="source_mode",
        )

    article_type = str(normalized_input_contract.get("article_type") or "").strip().lower()
    prompt_raw = str(
        normalized_input_contract.get("prompt_raw")
        or normalized_input_contract.get("topic")
        or ""
    ).strip()
    industry_hint = str(normalized_input_contract.get("industry_hint") or "").strip()
    queries = _build_web_research_queries(
        article_type=article_type,
        prompt_raw=prompt_raw,
        industry_hint=industry_hint,
    )
    if not queries:
        raise InputContractValidationError(
            "web research query missing",
            reason_code="INP_SOURCE_CONTEXT_INSUFFICIENT",
            field="topic",
        )

    fetcher = ArticleFetcher()
    search_results: list[dict[str, str]] = []
    seen_locators: set[str] = set()
    for query in queries:
        try:
            response = requests.post(
                _WEB_RESEARCH_SEARCH_ENDPOINT,
                data={"q": query},
                headers=_WEB_RESEARCH_HEADERS,
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException:
            continue
        soup = BeautifulSoup(response.text, "html.parser")
        for result in soup.select(".result"):
            anchor = result.select_one("a.result__a") or result.select_one(".result__title a")
            if anchor is None:
                continue
            locator = str(anchor.get("href") or "").strip()
            if not locator or locator in seen_locators:
                continue
            host = str(urlparse(locator).hostname or "").strip().lower()
            if not host:
                continue
            if any(keyword in host for keyword in _WEB_RESEARCH_AGGREGATOR_HOST_KEYWORDS):
                continue
            snippet = str((result.select_one(".result__snippet") or {}).get_text(" ", strip=True) if result.select_one(".result__snippet") else "").strip()
            title = anchor.get_text(" ", strip=True)
            seen_locators.add(locator)
            search_results.append(
                {
                    "query": query,
                    "locator": locator[:400],
                    "title": str(title or "").strip()[:200],
                    "snippet": snippet[:240],
                    "host": host[:120],
                }
            )
            if len(search_results) >= _WEB_RESEARCH_MAX_QUERIES * _WEB_RESEARCH_MAX_RESULTS_PER_QUERY:
                break
        if len(search_results) >= _WEB_RESEARCH_MAX_QUERIES * _WEB_RESEARCH_MAX_RESULTS_PER_QUERY:
            break

    hydrated_documents: list[dict[str, Any]] = []
    source_trace: list[dict[str, str]] = []
    seen_document_locators: set[str] = set()
    for result in search_results:
        locator = str(result.get("locator") or "").strip()
        if not locator or locator in seen_document_locators:
            continue
        if not fetcher._is_safe_url(locator):
            continue
        allowed, _ = fetcher._robots_allows(locator)
        if not allowed:
            continue
        try:
            data, content_type, header_encoding, apparent_encoding = fetcher._fetch_url_payload(locator)
            parsed_content, _ = fetcher._parse_url_payload(
                url=locator,
                data=data,
                content_type=content_type,
                header_encoding=header_encoding,
                apparent_encoding=apparent_encoding,
                persist_image=False,
            )
        except (
            ValueError,
            RuntimeError,
            OSError,
            requests.RequestException,
        ):
            continue
        if parsed_content.source_type == "image":
            continue
        html_text = ""
        soup: BeautifulSoup | None = None
        is_html = "application/pdf" not in str(content_type or "").lower() and not locator.lower().endswith(".pdf")
        if is_html:
            try:
                html_text, _ = fetcher._decode_html_bytes(
                    data,
                    header_encoding=header_encoding,
                    apparent_encoding=apparent_encoding,
                )
                soup = BeautifulSoup(html_text, "html.parser")
            except Exception:
                html_text = ""
                soup = None
        exact_date = _extract_web_source_exact_date(
            soup,
            html_text,
            str(result.get("snippet") or "") or str(parsed_content.content or "")[:1200],
        )
        if not exact_date:
            continue
        publisher = _extract_web_source_publisher(soup, locator)
        excerpt_source = str(result.get("snippet") or "").strip() or str(parsed_content.content or "").strip()
        excerpt = re.sub(r"\s+", " ", excerpt_source).strip()[:200]
        content = str(parsed_content.content or "").strip()
        if len(content) < 120 or not excerpt:
            continue
        seen_document_locators.add(locator)
        hydrated_documents.append(
            {
                "title": str(parsed_content.title or result.get("title") or locator)[:200],
                "content": content,
                "locator": locator[:400],
                "source_type": "url",
                "content_type": str(content_type or "").strip()[:80],
                "publisher": publisher,
                "exact_date": exact_date,
                "excerpt": excerpt,
            }
        )
        source_trace.append(
            {
                "query": str(result.get("query") or "").strip()[:120],
                "url": locator[:400],
                "publisher": publisher,
                "exact_date": exact_date,
                "excerpt": excerpt,
                "title": str(parsed_content.title or result.get("title") or locator)[:200],
            }
        )
        if len(hydrated_documents) >= _WEB_RESEARCH_MAX_DOCUMENTS:
            break

    if len(hydrated_documents) < _WEB_RESEARCH_MIN_DOCUMENTS or len(source_trace) < _WEB_RESEARCH_MIN_DOCUMENTS:
        raise InputContractValidationError(
            "web source trace insufficient",
            reason_code="INP_SOURCE_CONTEXT_INSUFFICIENT",
            field="source_documents",
        )

    normalized_input_contract["source_documents"] = hydrated_documents
    normalized_input_contract["source_inputs"] = [
        str(item.get("locator") or "").strip()
        for item in hydrated_documents
        if str(item.get("locator") or "").strip()
    ]
    normalized_input_contract["source"] = list(normalized_input_contract["source_inputs"])
    normalized_input_contract["source_trace"] = source_trace
    field_sources = dict(normalized_input_contract.get("field_sources") or {})
    field_sources["source_documents"] = "web_research"
    field_sources["source_trace"] = "web_research"
    normalized_input_contract["field_sources"] = field_sources
    compatibility_bridge = dict(normalized_input_contract.get("compatibility_bridge") or {})
    compatibility_bridge["web_source_research_hydrated"] = True
    compatibility_bridge["web_source_queries"] = list(queries)
    compatibility_bridge["web_source_count"] = len(hydrated_documents)
    normalized_input_contract["compatibility_bridge"] = compatibility_bridge
    return normalized_input_contract


def _extract_omakase_preflight_context(
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized = dict(input_contract or {})
    return {
        field: normalized.get(field)
        for field in _OMAKASE_PREFLIGHT_FIELDS
        if field in normalized
    }


def _restore_omakase_preflight_context(
    input_contract: Mapping[str, Any] | None,
    *,
    omakase_context: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    restored = dict(input_contract or {})
    for field, value in dict(omakase_context or {}).items():
        restored[field] = value
    return restored


def _summarize_web_source_trace(
    source_trace: Iterable[Any] | None,
) -> Dict[str, Any]:
    valid_trace_count = 0
    missing_trace_fields = False
    trace_publishers: set[str] = set()
    for item in list(source_trace or []):
        if not isinstance(item, Mapping):
            missing_trace_fields = True
            continue
        missing_fields = [
            field for field in _WEB_TRACE_REQUIRED_FIELDS if not str(item.get(field) or "").strip()
        ]
        if missing_fields:
            missing_trace_fields = True
            continue
        valid_trace_count += 1
        publisher = str(item.get("publisher") or "").strip()
        if publisher:
            trace_publishers.add(publisher)
    return {
        "valid_trace_count": valid_trace_count,
        "missing_trace_fields": missing_trace_fields,
        "publisher_count": len(trace_publishers),
    }


_CURRENT_MAINLINE_UI_OPTIONAL_INPUT_FIELDS = frozenset({"core_message"})


def _apply_current_mainline_ui_input_policy(
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_contract = dict(input_contract or {})
    input_decision = dict(normalized_contract.get("input_decision") or {})
    if not input_decision:
        return normalized_contract

    def _keep_required_item(item: Any) -> bool:
        field = str(dict(item or {}).get("field") or "").strip()
        return field not in _CURRENT_MAINLINE_UI_OPTIONAL_INPUT_FIELDS

    filtered_needs_input_items = [
        dict(item)
        for item in list(input_decision.get("needs_input_items") or [])
        if _keep_required_item(item)
    ]
    filtered_question_items = [
        dict(item)
        for item in list(input_decision.get("question_items") or [])
        if _keep_required_item(item)
    ]
    normalized_action = str(input_decision.get("action") or "accept")
    if (
        normalized_action == "clarify"
        and not filtered_needs_input_items
        and not filtered_question_items
        and str(input_decision.get("reason") or "") == "missing_required_inputs"
    ):
        normalized_action = "accept"
        input_decision["reason"] = "ui_required_inputs_satisfied"
        input_decision["reason_code"] = ""

    input_decision["action"] = normalized_action
    input_decision["needs_input_items"] = filtered_needs_input_items
    input_decision["question_items"] = filtered_question_items
    normalized_contract["input_decision"] = input_decision
    return normalized_contract


def _resolve_current_mainline_contract_for_ui(
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    resolve_seed = _strip_derived_contract_fields_for_reresolve(input_contract)
    resolve_seed = _hydrate_grounded_url_source_documents(resolve_seed)
    try:
        resolved_contract = dict(resolve_input_contract(resolve_seed).contract or resolve_seed)
    except Exception:
        resolved_contract = dict(resolve_seed)
    resolved_contract = _apply_current_mainline_ui_input_policy(resolved_contract)
    return enrich_persona_trial_contract(resolved_contract)


def _collect_current_mainline_ui_missing_required_fields(
    input_contract: Mapping[str, Any] | None,
) -> list[str]:
    normalized_input_contract = dict(input_contract or {})
    preserved_missing_fields = [
        str(field)
        for field in list(normalized_input_contract.get("ui_missing_required_fields") or [])
        if str(field or "").strip()
    ]
    if preserved_missing_fields:
        return preserved_missing_fields

    missing_required_fields: list[str] = []
    semantic_article_key = str(normalized_input_contract.get("semantic_article_key") or "").strip().lower()
    speaker_profile = str(normalized_input_contract.get("speaker_profile") or "").strip()
    audience_profile = str(normalized_input_contract.get("audience_profile") or "").strip()
    if (
        "speaker_profile" in normalized_input_contract
        and not speaker_profile
        and semantic_article_key != "company_introduction"
    ):
        missing_required_fields.append("speaker_profile")
    if not audience_profile and "audience_profile" in normalized_input_contract:
        missing_required_fields.append("audience_profile")
    return missing_required_fields


def validate_current_mainline_generation_gate(
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_input_contract = dict(input_contract or {})
    missing_required_fields = _collect_current_mainline_ui_missing_required_fields(normalized_input_contract)
    if missing_required_fields:
        raise InputContractValidationError(
            "generation blocked by missing ui required inputs",
            reason_code="INP_MISSING_REQUIRED",
            field=str(missing_required_fields[0]),
        )
    if normalized_input_contract.get("input_decision"):
        normalized_input_contract = _apply_current_mainline_ui_input_policy(normalized_input_contract)
        input_decision = dict(normalized_input_contract.get("input_decision") or {})
        input_action = str(input_decision.get("action") or "accept")
        if input_action != "accept":
            needs_input_items = list(input_decision.get("needs_input_items") or [])
            first_item = dict(needs_input_items[0] or {}) if needs_input_items else {}
            normalized_reason = str(input_decision.get("reason") or "")
            semantic_article_key = str(normalized_input_contract.get("semantic_article_key") or "").strip().lower()
            if normalized_reason == "source_context_insufficient":
                source_fit = dict(normalized_input_contract.get("source_fit") or {})
                source_context_required = bool(normalized_input_contract.get("source_grounding_required")) or (
                    str(source_fit.get("status") or "").strip().lower() == "block"
                )
                has_user_source = bool(
                    list(normalized_input_contract.get("source_inputs") or [])
                    or list(normalized_input_contract.get("source_documents") or [])
                    or list(normalized_input_contract.get("source_document_markers") or [])
                )
                # Production UX: a readable user-provided source should not trap the
                # user in the confirmation screen. Keep the guard for no-source cases,
                # but allow generation to continue with downstream quality checks.
                if has_user_source and bool(normalized_input_contract.get("_explicit_topic_present")):
                    input_action = "accept"
                elif bool(normalized_input_contract.get("_explicit_topic_present")) and not source_context_required:
                    input_action = "accept"
                elif (
                    semantic_article_key == "company_introduction"
                    and str(normalized_input_contract.get("_incoming_input_decision_action") or "").strip().lower() == "accept"
                    and not source_context_required
                ):
                    input_action = "accept"
            if input_action == "accept":
                input_decision["action"] = "accept"
                normalized_input_contract["input_decision"] = input_decision
            else:
                raise InputContractValidationError(
                    "generation blocked by unresolved input decision",
                    reason_code=str(
                        input_decision.get("reason_code")
                        or (
                            "INP_MISSING_REQUIRED"
                            if normalized_reason == "missing_required_inputs"
                            else "INP_NEEDS_CLARIFICATION"
                        )
                    ),
                    field=str(first_item.get("field") or "input_decision"),
                )
    source_mode = str(normalized_input_contract.get("source_mode") or "").strip().lower()
    has_explicit_grounded_sources = bool(
        list(normalized_input_contract.get("source_inputs") or [])
        or list(normalized_input_contract.get("source_documents") or [])
    )
    if source_mode == PROMPT_ONLY_SOURCE_MODE:
        article_type = str(normalized_input_contract.get("article_type") or "").strip().lower()
        if article_type not in PROMPT_ONLY_ALLOWED_ARTICLE_TYPE_SET:
            raise InputContractValidationError(
                "prompt_only source mode blocked for article_type",
                reason_code="INP_PROMPT_ONLY_ARTICLE_TYPE_BLOCKED",
                field="source_mode",
            )
        if prompt_only_has_source_conflict(normalized_input_contract):
            raise InputContractValidationError(
                "prompt_only cannot be combined with source inputs",
                reason_code="INP_PROMPT_ONLY_SOURCE_CONFLICT",
                field="source",
            )
        if not prompt_only_seed_text(normalized_input_contract):
            raise InputContractValidationError(
                "prompt_only requires prompt/topic",
                reason_code="INP_MISSING_REQUIRED",
                field="prompt_raw",
            )
        if not is_prompt_only_source_less_generation_allowed(normalized_input_contract):
            raise InputContractValidationError(
                "prompt_only source-less generation is not allowed",
                reason_code="INP_MISSING_REQUIRED",
                field="source_mode",
            )
    omakase_status = str(normalized_input_contract.get("omakase_preflight_status") or "").strip()
    omakase_charge_ready = normalized_input_contract.get("omakase_charge_ready")
    if (
        omakase_status
        and not (source_mode == "grounded" and has_explicit_grounded_sources)
        and (omakase_status != "READY" or omakase_charge_ready is False)
    ):
        raise InputContractValidationError(
            "omakase preflight not ready for generation",
            reason_code=str(
                normalized_input_contract.get("omakase_reason_code")
                or "INP_OMAKASE_PREFLIGHT_NOT_READY"
            ),
            field="omakase_preflight_status",
        )

    if source_mode == "followup":
        followup_context = dict(normalized_input_contract.get("followup_context") or {})
        quality_summary = dict(followup_context.get("quality_summary") or {})
        if quality_summary and (
            not bool(quality_summary.get("passed", False))
            or bool(quality_summary.get("blocked", False))
            or bool(quality_summary.get("title_placeholder", False))
        ):
            raise InputContractValidationError(
                "followup source quality below threshold",
                reason_code=str(
                    normalized_input_contract.get("omakase_reason_code")
                    or "INP_FOLLOWUP_SOURCE_QUALITY_LOW"
                ),
                field="followup_context",
            )

    if source_mode != "web":
        return normalized_input_contract

    article_type = str(normalized_input_contract.get("article_type") or "").strip().lower()
    if article_type not in WEB_RESEARCH_ALLOWED_ARTICLE_TYPE_SET:
        raise InputContractValidationError(
            "web source mode blocked for article_type",
            reason_code="INP_WEB_SOURCE_MODE_BLOCKED",
            field="source_mode",
        )

    source_documents = list(normalized_input_contract.get("source_documents") or [])
    if not source_documents:
        return normalized_input_contract

    source_trace_policy = str(normalized_input_contract.get("source_trace_policy") or "").strip().lower()
    if source_trace_policy != "web_trace_required":
        raise InputContractValidationError(
            "web source trace policy missing",
            reason_code="INP_WEB_SOURCE_TRACE_REQUIRED",
            field="source_trace_policy",
        )

    trace_summary = _summarize_web_source_trace(normalized_input_contract.get("source_trace"))
    if bool(trace_summary.get("missing_trace_fields")):
        raise InputContractValidationError(
            "web source trace missing required fields",
            reason_code="INP_WEB_SOURCE_TRACE_REQUIRED",
            field="source_trace",
        )
    if int(trace_summary.get("valid_trace_count") or 0) < 2:
        raise InputContractValidationError(
            "web source trace count insufficient",
            reason_code="INP_WEB_SOURCE_TRACE_REQUIRED",
            field="source_trace",
        )
    if int(trace_summary.get("publisher_count") or 0) < 2:
        raise InputContractValidationError(
            "web source trace publishers insufficient",
            reason_code="INP_WEB_SOURCE_TRACE_REQUIRED",
            field="source_trace",
        )
    return normalized_input_contract


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
    self_reference_policy_key: str = "auto",
    branding_subtype_key: str = "",
    branding_focus_key: str = "",
    pattern_key: str = "auto",
    system_hint_items: Iterable[Any] | None = None,
    retry_memo: Iterable[Any] | None = None,
    strict_saas_mode: str = "medium",
    ui_journey: Mapping[str, Any] | None = None,
    comparison_axes: Iterable[Any] | None = None,
    body_generation_experiment: str = "",
    source_mode: str = "grounded",
    industry_hint: str = "",
    source_trace: Iterable[Any] | None = None,
    followup_context: Mapping[str, Any] | None = None,
    past_blog_context: Mapping[str, Any] | None = None,
    omakase_preflight_status: str = "",
    omakase_charge_ready: bool | None = None,
    omakase_reason_code: str = "",
    omakase_message: str = "",
    omakase_fallback_options: Iterable[Any] | None = None,
    omakase_needs_input_items: Iterable[Any] | None = None,
    omakase_source_count: int | None = None,
    omakase_existing_post_count: int | None = None,
    omakase_usable_posts_count: int | None = None,
    omakase_dominant_cluster_count: int | None = None,
    omakase_available: bool | None = None,
) -> Dict[str, Any]:
    sanitized_user_prompt_text = _sanitize_grounded_priority_prompt(
        user_prompt_text,
        source_mode=source_mode,
        source_values=source_values,
        source_documents=source_documents,
    )
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
        user_prompt_text=sanitized_user_prompt_text,
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
        self_reference_policy_key=self_reference_policy_key,
        system_hint_items=profiled_selection.get("system_hint_items"),
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        ui_journey=profiled_selection.get("ui_journey"),
        semantic_article_key=str(profiled_selection.get("semantic_article_key") or ""),
        comparison_axes=profiled_selection.get("comparison_axes"),
        body_generation_experiment=body_generation_experiment,
    )
    raw_input_contract = _neutralize_company_intro_auto_speaker_profile(raw_input_contract)
    raw_input_contract["source_mode"] = str(source_mode or "").strip() or "grounded"
    raw_input_contract["industry_hint"] = str(industry_hint or "").strip()[:120]
    raw_input_contract["source_trace"] = [
        dict(item)
        for item in list(source_trace or [])
        if isinstance(item, Mapping)
    ]
    raw_input_contract["followup_context"] = dict(followup_context or {})
    raw_input_contract["past_blog_context"] = dict(past_blog_context or {})
    raw_input_contract["omakase_preflight_status"] = str(omakase_preflight_status or "").strip()
    raw_input_contract["omakase_charge_ready"] = (
        None if omakase_charge_ready is None else bool(omakase_charge_ready)
    )
    raw_input_contract["omakase_reason_code"] = str(omakase_reason_code or "").strip()
    raw_input_contract["omakase_message"] = str(omakase_message or "").strip()
    raw_input_contract["omakase_fallback_options"] = [
        dict(item)
        for item in list(omakase_fallback_options or [])
        if isinstance(item, Mapping)
    ]
    raw_input_contract["omakase_needs_input_items"] = [
        dict(item)
        for item in list(omakase_needs_input_items or [])
        if isinstance(item, Mapping)
    ]
    raw_input_contract["omakase_source_count"] = int(omakase_source_count or 0)
    raw_input_contract["omakase_existing_post_count"] = int(omakase_existing_post_count or 0)
    raw_input_contract["omakase_usable_posts_count"] = int(omakase_usable_posts_count or 0)
    raw_input_contract["omakase_dominant_cluster_count"] = int(omakase_dominant_cluster_count or 0)
    raw_input_contract["omakase_available"] = bool(omakase_available)
    return {
        "resolved_selection": adjusted_selection,
        "profiled_selection": profiled_selection,
        "raw_input_contract": raw_input_contract,
    }


def _build_current_mainline_contract_bundle(
    **kwargs: Any,
) -> Dict[str, Any]:
    raw_input_contract_bundle = _build_current_mainline_raw_input_contract(**kwargs)
    normalized_contract = normalize_input_contract_v1(
        dict(raw_input_contract_bundle.get("raw_input_contract") or {}),
        allow_legacy_aliases=False,
    )
    normalized_contract = _hydrate_web_source_documents(normalized_contract)
    normalized_contract = enrich_persona_trial_contract(normalized_contract)
    return {
        **raw_input_contract_bundle,
        "contract": normalized_contract,
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
    self_reference_policy_key: str = "auto",
    branding_subtype_key: str = "",
    branding_focus_key: str = "",
    pattern_key: str = "auto",
    system_hint_items: Iterable[Any] | None = None,
    retry_memo: Iterable[Any] | None = None,
    strict_saas_mode: str = "medium",
    ui_journey: Mapping[str, Any] | None = None,
    comparison_axes: Iterable[Any] | None = None,
    body_generation_experiment: str = "",
    source_mode: str = "grounded",
    industry_hint: str = "",
    source_trace: Iterable[Any] | None = None,
    followup_context: Mapping[str, Any] | None = None,
    past_blog_context: Mapping[str, Any] | None = None,
    omakase_preflight_status: str = "",
    omakase_charge_ready: bool | None = None,
    omakase_reason_code: str = "",
    omakase_message: str = "",
    omakase_fallback_options: Iterable[Any] | None = None,
    omakase_needs_input_items: Iterable[Any] | None = None,
    omakase_source_count: int | None = None,
    omakase_existing_post_count: int | None = None,
    omakase_usable_posts_count: int | None = None,
    omakase_dominant_cluster_count: int | None = None,
    omakase_available: bool | None = None,
) -> Dict[str, Any]:
    contract_bundle = _build_current_mainline_contract_bundle(
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
        self_reference_policy_key=self_reference_policy_key,
        branding_subtype_key=branding_subtype_key,
        branding_focus_key=branding_focus_key,
        pattern_key=pattern_key,
        system_hint_items=system_hint_items,
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        ui_journey=ui_journey,
        comparison_axes=comparison_axes,
        body_generation_experiment=body_generation_experiment,
        source_mode=source_mode,
        industry_hint=industry_hint,
        source_trace=source_trace,
        followup_context=followup_context,
        past_blog_context=past_blog_context,
        omakase_preflight_status=omakase_preflight_status,
        omakase_charge_ready=omakase_charge_ready,
        omakase_reason_code=omakase_reason_code,
        omakase_message=omakase_message,
        omakase_fallback_options=omakase_fallback_options,
        omakase_needs_input_items=omakase_needs_input_items,
        omakase_source_count=omakase_source_count,
        omakase_existing_post_count=omakase_existing_post_count,
        omakase_usable_posts_count=omakase_usable_posts_count,
        omakase_dominant_cluster_count=omakase_dominant_cluster_count,
        omakase_available=omakase_available,
    )
    return dict(contract_bundle.get("contract") or {})


def build_omakase_preflight(
    *,
    requested_article_type: str = "",
    user_prompt_text: str = "",
    source_values: Iterable[Any] | None = None,
    source_documents: Iterable[Any] | None = None,
    published_post_candidates: Iterable[Any] | None = None,
    preferred_source_mode: str = "auto",
    industry_hint: str = "",
) -> Dict[str, Any]:
    return build_omakase_preflight_core(
        requested_article_type=requested_article_type,
        user_prompt_text=user_prompt_text,
        source_values=source_values,
        source_documents=source_documents,
        published_post_candidates=published_post_candidates,
        preferred_source_mode=preferred_source_mode,
        industry_hint=industry_hint,
    )


def merge_omakase_seed_into_current_mainline_kwargs(
    base_kwargs: Mapping[str, Any] | None,
    preflight_result: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    return merge_omakase_seed_into_kwargs_core(base_kwargs, preflight_result)


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
    self_reference_policy_key: str = "auto",
    branding_subtype_key: str = "",
    branding_focus_key: str = "",
    pattern_key: str = "auto",
    system_hint_items: Iterable[Any] | None = None,
    retry_memo: Iterable[Any] | None = None,
    strict_saas_mode: str = "medium",
    ui_journey: Mapping[str, Any] | None = None,
    comparison_axes: Iterable[Any] | None = None,
    body_generation_experiment: str = "",
    source_mode: str = "grounded",
    industry_hint: str = "",
    source_trace: Iterable[Any] | None = None,
    omakase_preflight_status: str = "",
    omakase_charge_ready: bool | None = None,
    omakase_reason_code: str = "",
    omakase_message: str = "",
    omakase_fallback_options: Iterable[Any] | None = None,
    omakase_needs_input_items: Iterable[Any] | None = None,
    omakase_source_count: int | None = None,
    omakase_existing_post_count: int | None = None,
    omakase_usable_posts_count: int | None = None,
    omakase_dominant_cluster_count: int | None = None,
    omakase_available: bool | None = None,
) -> Dict[str, Any]:
    contract_bundle = _build_current_mainline_contract_bundle(
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
        self_reference_policy_key=self_reference_policy_key,
        branding_subtype_key=branding_subtype_key,
        branding_focus_key=branding_focus_key,
        pattern_key=pattern_key,
        system_hint_items=system_hint_items,
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        ui_journey=ui_journey,
        comparison_axes=comparison_axes,
        body_generation_experiment=body_generation_experiment,
        source_mode=source_mode,
        industry_hint=industry_hint,
        source_trace=source_trace,
        omakase_preflight_status=omakase_preflight_status,
        omakase_charge_ready=omakase_charge_ready,
        omakase_reason_code=omakase_reason_code,
        omakase_message=omakase_message,
        omakase_fallback_options=omakase_fallback_options,
        omakase_needs_input_items=omakase_needs_input_items,
        omakase_source_count=omakase_source_count,
        omakase_existing_post_count=omakase_existing_post_count,
        omakase_usable_posts_count=omakase_usable_posts_count,
        omakase_dominant_cluster_count=omakase_dominant_cluster_count,
        omakase_available=omakase_available,
    )
    contract = _resolve_current_mainline_contract_for_ui(dict(contract_bundle.get("contract") or {}))
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
        "writing_profile": dict(contract_bundle.get("profiled_selection", {}).get("writing_profile") or {}),
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
    self_reference_policy_key: str = "auto",
    branding_subtype_key: str = "",
    branding_focus_key: str = "",
    pattern_key: str = "auto",
    system_hint_items: Iterable[Any] | None = None,
    retry_memo: Iterable[Any] | None = None,
    strict_saas_mode: str = "medium",
    ui_journey: Mapping[str, Any] | None = None,
    comparison_axes: Iterable[Any] | None = None,
    body_generation_experiment: str = "",
    source_mode: str = "grounded",
    industry_hint: str = "",
    source_trace: Iterable[Any] | None = None,
    omakase_preflight_status: str = "",
    omakase_charge_ready: bool | None = None,
    omakase_reason_code: str = "",
    omakase_message: str = "",
    omakase_fallback_options: Iterable[Any] | None = None,
    omakase_needs_input_items: Iterable[Any] | None = None,
    omakase_source_count: int | None = None,
    omakase_existing_post_count: int | None = None,
    omakase_usable_posts_count: int | None = None,
    omakase_dominant_cluster_count: int | None = None,
    omakase_available: bool | None = None,
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
        self_reference_policy_key=self_reference_policy_key,
        branding_subtype_key=branding_subtype_key,
        branding_focus_key=branding_focus_key,
        pattern_key=pattern_key,
        system_hint_items=system_hint_items,
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        ui_journey=ui_journey,
        comparison_axes=comparison_axes,
        body_generation_experiment=body_generation_experiment,
        source_mode=source_mode,
        industry_hint=industry_hint,
        source_trace=source_trace,
        omakase_preflight_status=omakase_preflight_status,
        omakase_charge_ready=omakase_charge_ready,
        omakase_reason_code=omakase_reason_code,
        omakase_message=omakase_message,
        omakase_fallback_options=omakase_fallback_options,
        omakase_needs_input_items=omakase_needs_input_items,
        omakase_source_count=omakase_source_count,
        omakase_existing_post_count=omakase_existing_post_count,
        omakase_usable_posts_count=omakase_usable_posts_count,
        omakase_dominant_cluster_count=omakase_dominant_cluster_count,
        omakase_available=omakase_available,
    )
    resolved_contract = _resolve_current_mainline_contract_for_ui(contract)
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


def _extract_body_generation_summary(result: Mapping[str, Any] | None) -> Dict[str, Any]:
    normalized_result = dict(result or {})
    projected_summary = normalized_result.get("body_generation_summary")
    if isinstance(projected_summary, Mapping):
        return dict(projected_summary)
    pipeline_check = normalized_result.get("pipeline_check")
    if not isinstance(pipeline_check, Mapping):
        return {}
    body_generation = pipeline_check.get("body_generation")
    if not isinstance(body_generation, Mapping):
        return {}
    experimental_prompt_stack = body_generation.get("experimental_prompt_stack")
    if not isinstance(experimental_prompt_stack, Mapping):
        return {}
    visibility_summary = experimental_prompt_stack.get("visibility_summary")
    if not isinstance(visibility_summary, Mapping):
        return {}
    return dict(visibility_summary)


def _sanitize_grounded_priority_prompt(
    user_prompt_text: str,
    *,
    source_mode: str,
    source_values: Iterable[Any] | None = None,
    source_documents: Iterable[Any] | None = None,
) -> str:
    prompt_raw = str(user_prompt_text or "").strip()
    if not prompt_raw:
        return ""
    if str(source_mode or "").strip().lower() != "grounded":
        return prompt_raw
    has_sources = bool(
        [str(item or "").strip() for item in list(source_values or []) if str(item or "").strip()]
        or [item for item in list(source_documents or []) if isinstance(item, Mapping)]
    )
    if not has_sources:
        return prompt_raw
    sanitized = prompt_raw
    changed = False
    for pattern in _GROUNDED_PROMPT_META_PATTERNS:
        updated = pattern.sub("", sanitized)
        if updated != sanitized:
            changed = True
        sanitized = updated
    if not changed:
        return prompt_raw
    sanitized = re.sub(r"[ \t]+", " ", sanitized)
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized).strip(" 、。")
    return sanitized


def _clear_grounded_priority_runtime_context(
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_input_contract = dict(input_contract or {})
    source_mode = str(normalized_input_contract.get("source_mode") or "").strip().lower()
    has_sources = bool(
        list(normalized_input_contract.get("source_inputs") or [])
        or list(normalized_input_contract.get("source_documents") or [])
    )
    if source_mode == PROMPT_ONLY_SOURCE_MODE:
        pass
    elif source_mode != "grounded" or not has_sources:
        return normalized_input_contract
    normalized_input_contract["source_trace"] = []
    normalized_input_contract["omakase_preflight_status"] = ""
    normalized_input_contract["omakase_charge_ready"] = None
    normalized_input_contract["omakase_reason_code"] = ""
    normalized_input_contract["omakase_message"] = ""
    normalized_input_contract["omakase_fallback_options"] = []
    normalized_input_contract["omakase_needs_input_items"] = []
    normalized_input_contract["omakase_source_count"] = 0
    normalized_input_contract["omakase_existing_post_count"] = 0
    normalized_input_contract["omakase_usable_posts_count"] = 0
    normalized_input_contract["omakase_dominant_cluster_count"] = 0
    normalized_input_contract["omakase_available"] = False
    field_sources = dict(normalized_input_contract.get("field_sources") or {})
    field_sources.pop("source_trace", None)
    if field_sources:
        normalized_input_contract["field_sources"] = field_sources
    elif "field_sources" in normalized_input_contract:
        normalized_input_contract["field_sources"] = {}
    compatibility_bridge = dict(normalized_input_contract.get("compatibility_bridge") or {})
    for key in ("web_source_research_hydrated", "web_source_queries", "web_source_count"):
        compatibility_bridge.pop(key, None)
    if compatibility_bridge:
        normalized_input_contract["compatibility_bridge"] = compatibility_bridge
    elif "compatibility_bridge" in normalized_input_contract:
        normalized_input_contract.pop("compatibility_bridge", None)
    return normalized_input_contract


def _apply_user_prompt_to_input_contract(
    input_contract: Mapping[str, Any] | None,
    *,
    user_prompt_text: str,
) -> Dict[str, Any]:
    normalized_input_contract = dict(input_contract or {})
    source_mode = str(normalized_input_contract.get("source_mode") or "").strip().lower()
    source_values = list(normalized_input_contract.get("source_inputs") or normalized_input_contract.get("source_values") or [])
    source_documents = list(normalized_input_contract.get("source_documents") or [])
    prompt_raw = str(
        _sanitize_grounded_priority_prompt(
            user_prompt_text,
            source_mode=source_mode,
            source_values=source_values,
            source_documents=source_documents,
        )
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


def _hydrate_grounded_url_source_documents(
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_input_contract = dict(input_contract or {})
    source_mode = str(normalized_input_contract.get("source_mode") or "").strip().lower()
    if source_mode not in {"", "grounded"}:
        return normalized_input_contract
    article_type = str(normalized_input_contract.get("article_type") or "").strip().lower()
    semantic_key = str(normalized_input_contract.get("semantic_article_key") or "").strip().lower()
    if article_type == "announcement" or semantic_key == "announcement":
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
    if not all(locator.lower().startswith(("http://", "https://")) for locator in source_inputs):
        return normalized_input_contract

    fetcher = ArticleFetcher()
    hydrated_documents: list[dict[str, Any]] = []
    fetch_failures: list[dict[str, str]] = []
    for locator in source_inputs[:4]:
        try:
            fetched = fetcher.fetch_url(locator)
        except Exception as exc:
            fetch_failures.append(
                {
                    "locator": locator,
                    "reason": str(exc)[:240],
                }
            )
            continue

        content = str(getattr(fetched, "content", "") or "").strip()
        if not content:
            fetch_failures.append(
                {
                    "locator": locator,
                    "reason": "empty_content",
                }
            )
            continue

        document: dict[str, Any] = {
            "title": str(getattr(fetched, "title", "") or locator).strip()[:200] or locator,
            "locator": locator,
            "source_type": str(getattr(fetched, "source_type", "url") or "url").strip()[:40] or "url",
            "content": content,
        }
        content_type = str(getattr(fetched, "content_type", "") or "").strip()
        if content_type:
            document["content_type"] = content_type[:80]
        notices = [
            str(item or "").strip()
            for item in list(getattr(fetched, "notices", []) or [])
            if str(item or "").strip()
        ]
        if notices:
            document["notices"] = notices[:6]
        hydrated_documents.append(document)

    if not hydrated_documents and fetch_failures:
        hydrated_documents = [
            {
                "title": str(urlparse(locator).path or urlparse(locator).netloc or locator).strip("/") or locator,
                "locator": locator,
                "source_type": "url",
                "content": "",
                "notices": [f"source_fetch_failed: {reason}"],
            }
            for locator, reason in (
                (failure.get("locator") or "", failure.get("reason") or "fetch_failed")
                for failure in fetch_failures
            )
            if locator
        ]

    if hydrated_documents:
        normalized_input_contract["source_documents"] = hydrated_documents

    compatibility_bridge = dict(normalized_input_contract.get("compatibility_bridge") or {})
    compatibility_bridge["grounded_source_fetch_hydrated"] = bool(
        hydrated_documents and any(str(item.get("content") or "").strip() for item in hydrated_documents)
    )
    compatibility_bridge["grounded_source_fetch_count"] = len(
        [
            item
            for item in hydrated_documents
            if str(item.get("content") or "").strip()
        ]
    )
    if fetch_failures:
        compatibility_bridge["grounded_source_fetch_failures"] = fetch_failures[:4]
    normalized_input_contract["compatibility_bridge"] = compatibility_bridge
    return normalized_input_contract


def _ensure_company_intro_topic_statement(
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_input_contract = dict(input_contract or {})
    if str(normalized_input_contract.get("article_type") or "").strip() != "branding":
        return normalized_input_contract
    if str(normalized_input_contract.get("semantic_article_key") or "").strip() != "company_introduction":
        return normalized_input_contract
    if str(normalized_input_contract.get("topic_statement") or "").strip():
        return normalized_input_contract
    fallback_topic = str(
        dict(normalized_input_contract.get("focus_bundle") or {}).get("main_focus")
        or normalized_input_contract.get("topic")
        or normalized_input_contract.get("prompt_raw")
        or "自社の全体像を紹介する"
    ).strip()
    if not fallback_topic:
        return normalized_input_contract
    normalized_input_contract["topic_statement"] = fallback_topic
    if not str(normalized_input_contract.get("primary_topic_source") or "").strip():
        normalized_input_contract["primary_topic_source"] = "execution_fallback"
    field_sources = dict(normalized_input_contract.get("field_sources") or {})
    field_sources["topic_statement"] = str(
        normalized_input_contract.get("primary_topic_source") or "execution_fallback"
    )
    normalized_input_contract["field_sources"] = field_sources
    return normalized_input_contract


_DERIVED_CONTRACT_FIELDS_FOR_RERESOLVE = {
    "input_decision",
    "need_question",
    "source_grounding_required",
    "source_grounding_items",
    "source_grounding_status",
    "source_fit",
    "focus_bundle",
    "prompt_surface_items",
    "must_cover",
    "_shadow_spec_inputs",
    "topic_statement",
    "primary_topic_source",
    "_persona_contract",
    "_source_packet",
    "_persona_trial",
}


def _strip_derived_contract_fields_for_reresolve(
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    cleaned = dict(input_contract or {})
    for field in _DERIVED_CONTRACT_FIELDS_FOR_RERESOLVE:
        cleaned.pop(field, None)
    field_sources = dict(cleaned.get("field_sources") or {})
    if field_sources:
        for field in _DERIVED_CONTRACT_FIELDS_FOR_RERESOLVE:
            field_sources.pop(field, None)
        cleaned["field_sources"] = field_sources
    return cleaned


def _normalize_execution_input_contract(
    input_contract: Mapping[str, Any] | None,
    *,
    user_prompt_text: str,
) -> Dict[str, Any]:
    omakase_context = _extract_omakase_preflight_context(input_contract)
    ui_missing_required_fields = _collect_current_mainline_ui_missing_required_fields(input_contract)
    explicit_topic_present = bool(str(dict(input_contract or {}).get("topic") or "").strip())
    incoming_input_decision_action = str(
        dict(dict(input_contract or {}).get("input_decision") or {}).get("action") or ""
    ).strip().lower()
    normalized_input_contract = _apply_user_prompt_to_input_contract(
        input_contract,
        user_prompt_text=user_prompt_text,
    )
    resolve_seed = _strip_derived_contract_fields_for_reresolve(normalized_input_contract)
    try:
        normalized_input_contract = dict(
            _resolve_current_mainline_contract_for_ui(resolve_seed)
        )
    except Exception:
        normalized_input_contract = _apply_user_prompt_to_input_contract(
            input_contract,
            user_prompt_text=user_prompt_text,
        )
    normalized_input_contract = _restore_omakase_preflight_context(
        normalized_input_contract,
        omakase_context=omakase_context,
    )
    if ui_missing_required_fields:
        normalized_input_contract["ui_missing_required_fields"] = list(ui_missing_required_fields)
    else:
        normalized_input_contract.pop("ui_missing_required_fields", None)
    normalized_input_contract["_explicit_topic_present"] = explicit_topic_present
    normalized_input_contract["_incoming_input_decision_action"] = incoming_input_decision_action
    normalized_input_contract = _clear_grounded_priority_runtime_context(normalized_input_contract)
    normalized_input_contract = _ensure_company_intro_topic_statement(normalized_input_contract)
    normalized_input_contract = _hydrate_compatibility_source_documents(normalized_input_contract)
    return enrich_persona_trial_contract(normalized_input_contract)


def _run_current_mainline_pipeline(
    pipeline: CurrentMainlinePipeline,
    *,
    payload: Mapping[str, Any],
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    pipeline_class_path = f"{type(pipeline).__module__}.{type(pipeline).__qualname__}"
    path_telemetry = {
        "runner": "note.current_mainline_runner.execute_current_mainline_generation",
        "pipeline_class": pipeline_class_path,
        "pipeline_module": type(pipeline).__module__,
    }
    try:
        result = dict(pipeline.generate(dict(payload or {})))
        pipeline_check = dict(result.get("pipeline_check") or {})
        body_generation = dict(pipeline_check.get("body_generation") or {})
        formatter_telemetry = dict(body_generation.get("output_formatter") or {})
        path_telemetry["formatter_applied"] = bool(formatter_telemetry.get("formatter_applied"))
        path_telemetry["formatter_status"] = "reported" if formatter_telemetry else "not_reported_by_pipeline"
        pipeline_check["current_mainline_path"] = path_telemetry
        if body_generation:
            body_generation.setdefault("runner_pipeline_class", pipeline_class_path)
            body_generation.setdefault("runner_pipeline_module", type(pipeline).__module__)
            body_generation.setdefault("formatter_applied", bool(formatter_telemetry.get("formatter_applied")))
            pipeline_check["body_generation"] = body_generation
        result["pipeline_check"] = pipeline_check
        return result
    except Exception as exc:
        result = _normalize_pipeline_error_result(
            {
                "pipeline_check": {
                    "input_contract": dict(input_contract or {}),
                    "current_mainline_path": {
                        **path_telemetry,
                        "formatter_applied": False,
                        "formatter_status": "pipeline_exception",
                    },
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
        return result

def _finalize_current_mainline_result(
    result: Mapping[str, Any] | None,
    *,
    input_contract: Mapping[str, Any] | None,
    boundary_summary: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_result = dict(result or {})
    if bool(normalized_result.get("success", False)):
        normalized_result = _attach_current_mainline_quality_observability(
            normalized_result,
            input_contract=input_contract,
        )
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
    telemetry_contract = dict(pipeline_check.get("input_contract") or input_contract or {})
    pipeline_check["persona_trial"] = build_persona_trial_telemetry(
        telemetry_contract,
        result=normalized_result,
    )
    normalized_result["pipeline_check"] = pipeline_check
    body_generation_summary = _extract_body_generation_summary(normalized_result)
    if body_generation_summary:
        normalized_result["body_generation_summary"] = body_generation_summary
    normalized_result["pipeline_source"] = "newalgorithm_mainline"
    return normalized_result


def _attach_current_mainline_quality_observability(
    result: Mapping[str, Any] | None,
    *,
    input_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_result = dict(result or {})
    pipeline_check = dict(normalized_result.get("pipeline_check") or {})
    if pipeline_check.get("hard_soft_eval") and pipeline_check.get("final_quality_eval"):
        return normalized_result

    contract = dict(pipeline_check.get("input_contract") or input_contract or {})
    body = str(normalized_result.get("body") or "")
    if not contract or not body:
        return normalized_result

    style_profile = resolve_compact_writing_profile(
        article_type=str(contract.get("article_type") or ""),
        semantic_article_key=str(contract.get("semantic_article_key") or ""),
        content_goal_key=str(contract.get("content_goal") or ""),
        writing_focus_key=str(contract.get("writing_focus") or ""),
        tone_profile_key=str(contract.get("tone_profile") or ""),
        perspective_key=str(contract.get("perspective") or contract.get("perspective_key") or "auto"),
        relationship_mode=str(contract.get("relationship_mode") or "guide"),
        branding_subtype_key=str(contract.get("branding_subtype_key") or ""),
        branding_focus_key=str(contract.get("branding_focus_key") or ""),
        pattern_key=str(contract.get("pattern_key") or "auto"),
    )
    bridge = _CurrentMainlineQualityBridge()
    sections = _build_current_mainline_quality_sections(pipeline_check)
    _, quality_check = bridge._apply_quality_pass(body, contract, style_profile)
    derived_metrics = bridge._build_quality_metrics(
        body,
        sections,
        contract,
        style_profile,
        legal_result=dict(normalized_result.get("legal_postcheck") or {}),
        editor_report=dict(pipeline_check.get("editor_report") or {}),
    )
    quality_metrics = dict(pipeline_check.get("quality_metrics") or {})
    quality_metrics.update(derived_metrics)
    hard_soft_eval, contextual_naturalness_report, final_quality_eval = (
        bridge._build_quality_evaluations(quality_check, quality_metrics)
    )

    pipeline_check["quality_metrics"] = quality_metrics
    contract_alignment = dict(pipeline_check.get("contract_alignment") or {})
    must_cover_items = [
        str(item or "").strip()
        for item in list(contract.get("must_cover") or [])
        if str(item or "").strip()
    ]
    if must_cover_items:
        contract_alignment["must_cover_count"] = int(
            contract_alignment.get("must_cover_count") or len(must_cover_items)
        )
        contract_alignment["must_cover_reflection_rate"] = float(
            quality_metrics.get("must_cover_reflection_ratio")
            or contract_alignment.get("must_cover_reflection_rate")
            or 0.0
        )
    if bool(contract.get("source_grounding_required")):
        contract_alignment["source_trace_coverage"] = float(
            quality_metrics.get("source_grounding_reflection_ratio")
            or contract_alignment.get("source_trace_coverage")
            or 0.0
        )
    if contract_alignment:
        pipeline_check["contract_alignment"] = contract_alignment
    pipeline_check["hard_soft_eval"] = hard_soft_eval
    pipeline_check["contextual_naturalness_report"] = contextual_naturalness_report
    pipeline_check["final_quality_eval"] = final_quality_eval
    output_guard_inputs = dict(pipeline_check.get("output_guard_inputs") or {})
    output_guard_inputs["hard_soft_eval"] = hard_soft_eval
    output_guard_inputs["contextual_naturalness_report"] = contextual_naturalness_report
    output_guard_inputs["final_quality_eval"] = final_quality_eval
    output_guard_inputs["contract_alignment"] = contract_alignment
    pipeline_check["output_guard_inputs"] = output_guard_inputs
    normalized_result["pipeline_check"] = pipeline_check
    normalized_result["quality_pipeline_check"] = quality_check
    return normalized_result


def _build_current_mainline_quality_sections(
    pipeline_check: Mapping[str, Any] | None,
) -> list[Any]:
    entries = list(dict(pipeline_check or {}).get("semantic_plan", {}).get("entries") or [])
    sections: list[Any] = []
    for entry in entries[:8]:
        if not isinstance(entry, Mapping):
            continue
        sections.append(
            SimpleNamespace(
                heading=str(entry.get("heading") or ""),
                topic_seed=str(entry.get("anchor") or entry.get("claim") or ""),
                must_cover=[str(entry.get("claim") or "")] if str(entry.get("claim") or "").strip() else [],
                intent=str(entry.get("purpose") or ""),
            )
        )
    return sections


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
    try:
        validate_current_mainline_generation_gate(normalized_input_contract)
    except InputContractValidationError as exc:
        fail_closed_result = build_fail_closed_generation_result(
            input_contract=normalized_input_contract,
            reason_code=str(getattr(exc, "reason_code", "") or "INP_MISSING_REQUIRED"),
            error_class="user_input",
        )
        input_decision = dict(normalized_input_contract.get("input_decision") or {})
        fail_closed_result["needs_input_items"] = list(
            input_decision.get("needs_input_items")
            or normalized_input_contract.get("omakase_needs_input_items")
            or []
        )
        if not fail_closed_result["needs_input_items"]:
            fail_closed_result["needs_input_items"] = [
                {"field": str(field)}
                for field in _collect_current_mainline_ui_missing_required_fields(normalized_input_contract)
            ]
        fail_closed_result["fallback_options"] = list(
            normalized_input_contract.get("omakase_fallback_options") or []
        )
        fail_closed_result["message"] = str(normalized_input_contract.get("omakase_message") or "")
        return _finalize_current_mainline_result(
            fail_closed_result,
            input_contract=normalized_input_contract,
            boundary_summary=boundary_summary,
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
