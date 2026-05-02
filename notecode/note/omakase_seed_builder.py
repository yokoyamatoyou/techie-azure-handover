"""Thin preflight/seed builder for omakase mode before current mainline execution."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Mapping

from note.input_contract_v1 import (
    InputContractValidationError,
    WEB_RESEARCH_ALLOWED_ARTICLE_TYPE_SET,
    normalize_article_type,
)

OMAKASE_PREFLIGHT_READY = "READY"
OMAKASE_PREFLIGHT_AUTO_SOURCE_READY = "AUTO_SOURCE_READY"
OMAKASE_PREFLIGHT_NEEDS_INPUT = "NEEDS_INPUT"
OMAKASE_PREFLIGHT_FALLBACK = "OMAKASE_FALLBACK"

_AUTO_SOURCE_DEFAULT_ARTICLE_TYPE = "explanatory_article"
_FALLBACK_WEB_ARTICLE_TYPES: tuple[str, ...] = (
    "explanatory_article",
    "industry_analysis",
    "daily_story",
)
_NO_SOURCE_FOLLOWUP_BLOCKED_ARTICLE_TYPES: frozenset[str] = frozenset(
    {"branding", "announcement", "case_study", "comparative_review"}
)
_WEB_TRACE_REQUIRED_FIELDS: tuple[str, ...] = ("query", "url", "publisher", "exact_date", "excerpt")
_OMAKASE_INVENTORY_MIN_POSTS = 3
_OMAKASE_MIN_TOTAL_BODY_CHARS = 4500
_OMAKASE_DOMINANT_CLUSTER_MIN_COUNT = 2
_OMAKASE_QUALITY_READY_CLUSTER_MIN_COUNT = 2
_FOLLOWUP_MIN_ALIGNMENT_SCORE = 0.55
_FOLLOWUP_MAX_SOFT_WARNING_COUNT = 3
_FOLLOWUP_MAX_NATURALNESS_ISSUE_COUNT = 1
_INVENTORY_TOKEN_PATTERNS: tuple[str, ...] = (
    r"[A-Za-z][A-Za-z0-9_-]{1,}",
    r"[0-9]{2,}",
    r"[ァ-ヶー]{2,}",
    r"[一-龠々]{2,}",
)
_INVENTORY_TOKEN_STOPWORDS: set[str] = {
    "お知らせ",
    "お任せ",
    "まとめ",
    "公式",
    "公開",
    "公開記事",
    "投稿",
    "記事",
    "会社",
    "会社紹介",
    "企業紹介",
    "紹介",
    "変更",
    "発表",
    "告知",
    "更新",
    "最新",
    "続編",
    "実務",
    "整理",
}


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _normalize_unique_texts(values: Iterable[Any] | None) -> list[str]:
    normalized: list[str] = []
    for item in values or []:
        text = _normalize_text(item)
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _normalize_source_documents(values: Iterable[Any] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in values or []:
        if not isinstance(item, Mapping):
            continue
        document = dict(item)
        title = _normalize_text(document.get("title") or document.get("name"))
        locator = _normalize_text(document.get("locator") or document.get("url"))
        content = _normalize_text(document.get("content") or document.get("summary") or document.get("excerpt"))
        if not any((title, locator, content)):
            continue
        normalized.append(
            {
                "title": title,
                "locator": locator,
                "content": content,
                "source_type": _normalize_text(document.get("source_type"))
                or ("url" if locator.lower().startswith(("http://", "https://")) else "text"),
            }
        )
    return normalized


def _normalize_post_candidates(values: Iterable[Any] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in values or []:
        if not isinstance(item, Mapping):
            continue
        candidate = dict(item)
        title = _normalize_text(candidate.get("title"))
        locator = _normalize_text(candidate.get("locator") or candidate.get("url"))
        summary = _normalize_text(
            candidate.get("summary") or candidate.get("excerpt") or candidate.get("content")
        )
        article_type = _normalize_article_type_or_blank(candidate.get("article_type"))
        if not any((title, locator, summary)):
            continue
        normalized.append(
            {
                "title": title,
                "locator": locator,
                "summary": summary,
                "article_type": article_type,
                "publisher": _normalize_text(candidate.get("publisher")),
                "exact_date": _normalize_text(candidate.get("exact_date")),
                "excerpt": _normalize_text(candidate.get("excerpt")),
                "continuity_summary": _normalize_text(candidate.get("continuity_summary")),
                "style_memory": dict(candidate.get("style_memory") or {})
                if isinstance(candidate.get("style_memory"), Mapping)
                else {},
                "semantic_article_key": _normalize_text(candidate.get("semantic_article_key")),
                "body_chars": _safe_int(candidate.get("body_chars"), 0),
                "full_text_chars": _safe_int(candidate.get("full_text_chars"), 0),
                "quality_summary": dict(candidate.get("quality_summary") or {})
                if isinstance(candidate.get("quality_summary"), Mapping)
                else {},
                "source_trace": _normalize_source_trace(candidate.get("source_trace")),
                "source_documents": _normalize_source_documents(candidate.get("source_documents")),
            }
        )
    return normalized


def _extract_inventory_tokens(*values: Any) -> list[str]:
    normalized: list[str] = []
    for raw_value in values:
        text = _normalize_text(raw_value)
        if not text:
            continue
        for pattern in _INVENTORY_TOKEN_PATTERNS:
            for token in re.findall(pattern, text):
                normalized_token = _normalize_text(token).lower()
                if (
                    not normalized_token
                    or normalized_token in _INVENTORY_TOKEN_STOPWORDS
                    or normalized_token in normalized
                ):
                    continue
                normalized.append(normalized_token)
    return normalized


def _candidate_inventory_tokens(candidate: Mapping[str, Any] | None) -> set[str]:
    normalized_candidate = dict(candidate or {})
    return set(
        _extract_inventory_tokens(
            normalized_candidate.get("title"),
            normalized_candidate.get("summary"),
            normalized_candidate.get("excerpt"),
        )
    )


def _is_usable_inventory_post(candidate: Mapping[str, Any] | None) -> bool:
    normalized_candidate = dict(candidate or {})
    article_type = _normalize_article_type_or_blank(normalized_candidate.get("article_type"))
    if article_type not in WEB_RESEARCH_ALLOWED_ARTICLE_TYPE_SET:
        return False
    if not _normalize_text(normalized_candidate.get("locator")):
        return False
    if not any(
        _normalize_text(normalized_candidate.get(field))
        for field in ("title", "summary", "excerpt")
    ):
        return False
    return True


def _posts_share_inventory_trend(
    left: Mapping[str, Any] | None,
    right: Mapping[str, Any] | None,
) -> bool:
    shared_tokens = _candidate_inventory_tokens(left) & _candidate_inventory_tokens(right)
    return len(shared_tokens) >= 2


def _build_inventory_clusters(
    usable_posts: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    if not usable_posts:
        return []
    clusters: list[list[dict[str, Any]]] = []
    visited_indexes: set[int] = set()
    for start_index, post in enumerate(usable_posts):
        if start_index in visited_indexes:
            continue
        stack = [start_index]
        cluster_indexes: list[int] = []
        while stack:
            current_index = stack.pop()
            if current_index in visited_indexes:
                continue
            visited_indexes.add(current_index)
            cluster_indexes.append(current_index)
            current_post = usable_posts[current_index]
            for neighbor_index, neighbor_post in enumerate(usable_posts):
                if neighbor_index in visited_indexes:
                    continue
                if _posts_share_inventory_trend(current_post, neighbor_post):
                    stack.append(neighbor_index)
        clusters.append([usable_posts[index] for index in cluster_indexes])
    return clusters


def _build_inventory_summary(normalized_posts: Iterable[Mapping[str, Any]] | None) -> dict[str, Any]:
    normalized_posts_list = [dict(candidate) for candidate in list(normalized_posts or [])]
    usable_posts = [
        dict(candidate)
        for candidate in normalized_posts_list
        if _is_usable_inventory_post(candidate)
    ]
    total_body_chars = sum(
        max(
            _safe_int(candidate.get("body_chars"), 0),
            _safe_int(candidate.get("full_text_chars"), 0),
        )
        for candidate in normalized_posts_list
    )
    clusters = _build_inventory_clusters(usable_posts)
    dominant_cluster = max(clusters, key=len, default=[])
    quality_ready_posts = [
        dict(candidate)
        for candidate in usable_posts
        if _has_followup_quality_floor(candidate)
    ]
    quality_ready_dominant_cluster = [
        dict(candidate)
        for candidate in dominant_cluster
        if _has_followup_quality_floor(candidate)
    ]
    strong_followup_candidate = next(
        (
            dict(candidate)
            for candidate in quality_ready_dominant_cluster
            if _has_followup_trace_strength(candidate)
        ),
        None,
    )
    return {
        "existing_posts_count": len(normalized_posts_list),
        "total_body_chars": total_body_chars,
        "inventory_min_posts": _OMAKASE_INVENTORY_MIN_POSTS,
        "inventory_min_total_body_chars": _OMAKASE_MIN_TOTAL_BODY_CHARS,
        "usable_posts": usable_posts,
        "usable_posts_count": len(usable_posts),
        "quality_ready_posts_count": len(quality_ready_posts),
        "quality_ready_dominant_cluster_count": len(quality_ready_dominant_cluster),
        "clusters": clusters,
        "dominant_cluster": dominant_cluster,
        "dominant_cluster_count": len(dominant_cluster),
        "strong_followup_candidate": strong_followup_candidate,
        "omakase_available": (
            len(normalized_posts_list) >= _OMAKASE_INVENTORY_MIN_POSTS
            and total_body_chars >= _OMAKASE_MIN_TOTAL_BODY_CHARS
        ),
    }


def _with_inventory_summary(
    result: Mapping[str, Any],
    *,
    inventory_summary: Mapping[str, Any],
) -> Dict[str, Any]:
    enriched = dict(result)
    enriched["existing_post_count"] = int(
        enriched.get("existing_post_count") or inventory_summary.get("existing_posts_count") or 0
    )
    enriched["total_body_chars"] = int(inventory_summary.get("total_body_chars") or 0)
    enriched["inventory_min_posts"] = int(inventory_summary.get("inventory_min_posts") or _OMAKASE_INVENTORY_MIN_POSTS)
    enriched["inventory_min_total_body_chars"] = int(
        inventory_summary.get("inventory_min_total_body_chars") or _OMAKASE_MIN_TOTAL_BODY_CHARS
    )
    enriched["usable_posts_count"] = int(inventory_summary.get("usable_posts_count") or 0)
    enriched["quality_ready_posts_count"] = int(inventory_summary.get("quality_ready_posts_count") or 0)
    enriched["quality_ready_dominant_cluster_count"] = int(
        inventory_summary.get("quality_ready_dominant_cluster_count") or 0
    )
    enriched["dominant_cluster_count"] = int(inventory_summary.get("dominant_cluster_count") or 0)
    enriched["omakase_available"] = bool(inventory_summary.get("omakase_available"))
    return enriched


def usable_posts_count(published_post_candidates: Iterable[Any] | None) -> int:
    normalized_posts = _normalize_post_candidates(published_post_candidates)
    inventory_summary = _build_inventory_summary(normalized_posts)
    return int(inventory_summary.get("usable_posts_count") or 0)


def dominant_cluster_count(published_post_candidates: Iterable[Any] | None) -> int:
    normalized_posts = _normalize_post_candidates(published_post_candidates)
    inventory_summary = _build_inventory_summary(normalized_posts)
    return int(inventory_summary.get("dominant_cluster_count") or 0)


def omakase_available(published_post_candidates: Iterable[Any] | None) -> bool:
    normalized_posts = _normalize_post_candidates(published_post_candidates)
    inventory_summary = _build_inventory_summary(normalized_posts)
    return bool(inventory_summary.get("omakase_available"))


def total_body_chars(published_post_candidates: Iterable[Any] | None) -> int:
    normalized_posts = _normalize_post_candidates(published_post_candidates)
    inventory_summary = _build_inventory_summary(normalized_posts)
    return int(inventory_summary.get("total_body_chars") or 0)


def _normalize_source_trace(values: Iterable[Any] | None) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in values or []:
        if not isinstance(item, Mapping):
            continue
        normalized_item = {
            field: _normalize_text(item.get(field))
            for field in _WEB_TRACE_REQUIRED_FIELDS
        }
        if any(normalized_item.values()):
            normalized.append(normalized_item)
    return normalized


def _normalize_article_type_or_blank(value: Any) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    try:
        return normalize_article_type(text, allow_legacy_aliases=False)
    except InputContractValidationError:
        return ""


def _infer_article_type_from_prompt(prompt_raw: str) -> str:
    text = _normalize_text(prompt_raw).lower()
    if not text:
        return _AUTO_SOURCE_DEFAULT_ARTICLE_TYPE
    if any(token in text for token in ("お知らせ", "告知", "変更", "リリース", "発表")):
        return "announcement"
    if any(token in text for token in ("会社紹介", "自社", "企業紹介", "沿革", "事業内容")):
        return "branding"
    if any(token in text for token in ("比較", "選び方", "違い", "比較検討")):
        return "comparative_review"
    if any(token in text for token in ("事例", "導入事例", "改善事例", "ケース")):
        return "case_study"
    if any(token in text for token in ("日報", "日々", "今日", "昨日", "現場メモ")):
        return "daily_story"
    if any(token in text for token in ("業界", "市場", "統計", "動向", "調査")):
        return "industry_analysis"
    return _AUTO_SOURCE_DEFAULT_ARTICLE_TYPE


def _resolve_article_type(
    *,
    requested_article_type: str,
    prompt_raw: str,
    allow_blocked_auto_source: bool,
) -> str:
    requested = _normalize_article_type_or_blank(requested_article_type)
    if requested:
        if allow_blocked_auto_source:
            return requested
        if requested in WEB_RESEARCH_ALLOWED_ARTICLE_TYPE_SET:
            return requested
        return ""
    inferred = _infer_article_type_from_prompt(prompt_raw)
    if allow_blocked_auto_source or inferred in WEB_RESEARCH_ALLOWED_ARTICLE_TYPE_SET:
        return inferred
    if inferred in {"branding", "announcement", "case_study", "comparative_review"}:
        return ""
    return _AUTO_SOURCE_DEFAULT_ARTICLE_TYPE


def _build_seed(
    *,
    article_type: str,
    source_mode: str,
    prompt_raw: str,
    source_values: Iterable[Any] | None = None,
    source_documents: Iterable[Any] | None = None,
    industry_hint: str = "",
    source_trace: Iterable[Any] | None = None,
    followup_context: Mapping[str, Any] | None = None,
    seed_reason: str,
) -> Dict[str, Any]:
    return {
        "article_type": article_type,
        "source_mode": source_mode,
        "user_prompt_text": _normalize_text(prompt_raw),
        "source_values": _normalize_unique_texts(source_values),
        "source_documents": _normalize_source_documents(source_documents),
        "industry_hint": _normalize_text(industry_hint)[:120],
        "source_trace": [
            dict(item)
            for item in list(source_trace or [])
            if isinstance(item, Mapping)
        ],
        "followup_context": dict(followup_context or {}),
        "seed_reason": seed_reason,
    }


def _build_needs_input_items() -> list[dict[str, str]]:
    return [
        {
            "field": "topic",
            "question_template": "何について書くかをひとことで入れてください。",
            "example_answer": "生成AI導入で最初に決めること",
            "required_format": "1テーマに絞る",
        }
    ]


def _build_fallback_options(
    *,
    requested_article_type: str,
    prompt_raw: str,
) -> list[dict[str, str]]:
    normalized_requested = _normalize_article_type_or_blank(requested_article_type)
    inferred_requested = normalized_requested or _normalize_article_type_or_blank(
        _infer_article_type_from_prompt(prompt_raw)
    )
    options: list[dict[str, str]] = []
    prompt_hint = _normalize_text(prompt_raw)
    if inferred_requested in {"branding", "announcement"}:
        options.append(
            {
                "label": "同じ種類を資料つきで進める",
                "article_type": inferred_requested,
                "source_mode": "grounded",
                "prompt_hint": "会社概要URL / お知らせURL / PDF を1件以上追加してください。",
            }
        )
    for article_type in _FALLBACK_WEB_ARTICLE_TYPES:
        label = {
            "explanatory_article": "判断材料の記事から始める",
            "industry_analysis": "業界の動きを整理する",
            "daily_story": "日々の気づきを1本にする",
        }[article_type]
        hint = prompt_hint or {
            "explanatory_article": "例: 生成AI導入で最初に決めること",
            "industry_analysis": "例: 中小企業の生成AI活用動向",
            "daily_story": "例: 今日の運用で見えた改善ポイント",
        }[article_type]
        options.append(
            {
                "label": label,
                "article_type": article_type,
                "source_mode": "web",
                "prompt_hint": hint,
            }
        )
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in options:
        key = (item["article_type"], item["source_mode"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:3]


def _has_followup_trace_strength(candidate: Mapping[str, Any] | None) -> bool:
    normalized_candidate = dict(candidate or {})
    article_type = _normalize_article_type_or_blank(normalized_candidate.get("article_type"))
    if article_type not in WEB_RESEARCH_ALLOWED_ARTICLE_TYPE_SET:
        return False
    if not _normalize_text(normalized_candidate.get("locator")):
        return False
    if not _normalize_text(normalized_candidate.get("summary")):
        return False
    trace = _normalize_source_trace(normalized_candidate.get("source_trace"))
    valid_trace_items = [
        item
        for item in trace
        if all(_normalize_text(item.get(field)) for field in _WEB_TRACE_REQUIRED_FIELDS)
    ]
    publisher_count = len(
        {
            _normalize_text(item.get("publisher"))
            for item in valid_trace_items
            if _normalize_text(item.get("publisher"))
        }
    )
    return len(valid_trace_items) >= 2 and publisher_count >= 2


def _has_followup_quality_floor(candidate: Mapping[str, Any] | None) -> bool:
    normalized_candidate = dict(candidate or {})
    quality_summary = dict(normalized_candidate.get("quality_summary") or {})
    if not quality_summary:
        return False
    alignment_score = float(quality_summary.get("alignment_score") or 0.0)
    soft_warning_count = int(quality_summary.get("soft_warning_count") or 0)
    naturalness_issue_count = int(quality_summary.get("naturalness_issue_count") or 0)
    if bool(quality_summary.get("blocked", False)):
        return False
    if bool(quality_summary.get("title_placeholder", False)):
        return False
    if not bool(quality_summary.get("passed", False)):
        return False
    if alignment_score < _FOLLOWUP_MIN_ALIGNMENT_SCORE:
        return False
    if soft_warning_count > _FOLLOWUP_MAX_SOFT_WARNING_COUNT:
        return False
    if not bool(quality_summary.get("naturalness_passed", True)):
        return False
    if naturalness_issue_count > _FOLLOWUP_MAX_NATURALNESS_ISSUE_COUNT:
        return False
    return True


def _has_strong_followup_candidate(candidate: Mapping[str, Any] | None) -> bool:
    return _has_followup_trace_strength(candidate) and _has_followup_quality_floor(candidate)


def _is_blocked_no_source_followup_article_type(article_type: str) -> bool:
    return _normalize_article_type_or_blank(article_type) in _NO_SOURCE_FOLLOWUP_BLOCKED_ARTICLE_TYPES


def _build_inventory_gate_block_result(
    *,
    requested_article_type: str,
    prompt_raw: str,
    inventory_summary: Mapping[str, Any],
) -> Dict[str, Any]:
    existing_post_count = int(inventory_summary.get("existing_posts_count") or 0)
    total_chars = int(inventory_summary.get("total_body_chars") or 0)
    min_posts = int(inventory_summary.get("inventory_min_posts") or _OMAKASE_INVENTORY_MIN_POSTS)
    min_total_chars = int(
        inventory_summary.get("inventory_min_total_body_chars") or _OMAKASE_MIN_TOTAL_BODY_CHARS
    )
    missing_posts = max(0, min_posts - existing_post_count)
    missing_chars = max(0, min_total_chars - total_chars)
    if missing_posts > 0 and missing_chars > 0:
        reason_code = "OMK_FALLBACK_INVENTORY_POSTS_AND_BODY_CHARS_INSUFFICIENT"
        message = (
            f"公開済み記事の蓄積が足りないため、お任せはまだ開始しません。"
            f"公開済み{min_posts}件以上かつ合計本文{min_total_chars}字以上で使えます。"
            f"現在は{existing_post_count}件・{total_chars}字です。"
        )
    elif missing_posts > 0:
        reason_code = "OMK_FALLBACK_INVENTORY_POSTS_INSUFFICIENT"
        message = (
            f"公開済み記事数が足りないため、お任せはまだ開始しません。"
            f"公開済み{min_posts}件以上で使えます。現在は{existing_post_count}件です。"
        )
    else:
        reason_code = "OMK_FALLBACK_TOTAL_BODY_CHARS_INSUFFICIENT"
        message = (
            f"公開済み記事の本文文字数が足りないため、お任せはまだ開始しません。"
            f"合計本文{min_total_chars}字以上で使えます。現在は{total_chars}字です。"
        )
    return _with_inventory_summary(
        {
            "status": OMAKASE_PREFLIGHT_FALLBACK,
            "reason_code": reason_code,
            "charge_ready": False,
            "message": message,
            "seed": {},
            "fallback_options": _build_fallback_options(
                requested_article_type=requested_article_type,
                prompt_raw=prompt_raw,
            ),
            "needs_input_items": [],
            "source_count": 0,
            "existing_post_count": existing_post_count,
        },
        inventory_summary=inventory_summary,
    )


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
    normalized_prompt = _normalize_text(user_prompt_text)
    normalized_source_values = _normalize_unique_texts(source_values)
    normalized_source_documents = _normalize_source_documents(source_documents)
    normalized_posts = _normalize_post_candidates(published_post_candidates)
    inventory_summary = _build_inventory_summary(normalized_posts)
    normalized_preferred_mode = _normalize_text(preferred_source_mode).lower() or "auto"

    if normalized_source_values or normalized_source_documents:
        article_type = _resolve_article_type(
            requested_article_type=requested_article_type,
            prompt_raw=normalized_prompt,
            allow_blocked_auto_source=True,
        )
        return _with_inventory_summary({
            "status": OMAKASE_PREFLIGHT_READY,
            "reason_code": "OMK_READY_SOURCE_PROVIDED",
            "charge_ready": True,
            "message": "資料があるため、そのまま生成に進めます。",
            "seed": _build_seed(
                article_type=article_type,
                source_mode="grounded",
                prompt_raw=normalized_prompt,
                source_values=normalized_source_values,
                source_documents=normalized_source_documents,
                industry_hint=industry_hint,
                seed_reason="grounded_sources_present",
            ),
            "fallback_options": [],
            "needs_input_items": [],
            "source_count": len(normalized_source_values) or len(normalized_source_documents),
            "existing_post_count": len(normalized_posts),
        }, inventory_summary=inventory_summary)

    if normalized_preferred_mode == "followup":
        return _with_inventory_summary({
            "status": OMAKASE_PREFLIGHT_FALLBACK,
            "reason_code": "OMK_FALLBACK_FOLLOWUP_DISABLED",
            "charge_ready": False,
            "message": "続編モードは current mainline では使いません。資料ありかお任せを選んでください。",
            "seed": {},
            "fallback_options": _build_fallback_options(
                requested_article_type=requested_article_type,
                prompt_raw=normalized_prompt,
            ),
            "needs_input_items": [],
            "source_count": 0,
            "existing_post_count": len(normalized_posts),
        }, inventory_summary=inventory_summary)

    if normalized_prompt:
        auto_source_article_type = _resolve_article_type(
            requested_article_type=requested_article_type,
            prompt_raw=normalized_prompt,
            allow_blocked_auto_source=False,
        )
        if auto_source_article_type:
            if not bool(inventory_summary.get("omakase_available")):
                return _build_inventory_gate_block_result(
                    requested_article_type=requested_article_type,
                    prompt_raw=normalized_prompt,
                    inventory_summary=inventory_summary,
                )
            return _with_inventory_summary({
                "status": OMAKASE_PREFLIGHT_AUTO_SOURCE_READY,
                "reason_code": "OMK_AUTO_SOURCE_READY",
                "charge_ready": False,
                "message": "自動で材料収集を始められます。生成クレジット消費前に source-backed 化します。",
                "seed": _build_seed(
                    article_type=auto_source_article_type,
                    source_mode="web",
                    prompt_raw=normalized_prompt,
                    industry_hint=industry_hint,
                    seed_reason="web_auto_source_seed",
                ),
                "fallback_options": [],
                "needs_input_items": [],
                "source_count": 0,
                "existing_post_count": len(normalized_posts),
            }, inventory_summary=inventory_summary)
        return _with_inventory_summary({
            "status": OMAKASE_PREFLIGHT_FALLBACK,
            "reason_code": "OMK_FALLBACK_SOURCE_REQUIRED",
            "charge_ready": False,
            "message": "この種類は材料不足のまま自動生成しません。先に safe な代替案を出します。",
            "seed": {},
            "fallback_options": _build_fallback_options(
                requested_article_type=requested_article_type,
                prompt_raw=normalized_prompt,
            ),
            "needs_input_items": [],
            "source_count": 0,
            "existing_post_count": len(normalized_posts),
        }, inventory_summary=inventory_summary)

    return _with_inventory_summary({
        "status": OMAKASE_PREFLIGHT_NEEDS_INPUT,
        "reason_code": "INP_NEEDS_CLARIFICATION",
        "charge_ready": False,
        "message": "お任せモードを始めるには、まず1行のテーマが必要です。",
        "seed": {},
        "fallback_options": _build_fallback_options(
            requested_article_type=requested_article_type,
            prompt_raw="",
        ),
        "needs_input_items": _build_needs_input_items(),
        "source_count": 0,
        "existing_post_count": len(normalized_posts),
    }, inventory_summary=inventory_summary)


def merge_omakase_seed_into_kwargs(
    base_kwargs: Mapping[str, Any] | None,
    preflight_result: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    merged = dict(base_kwargs or {})
    normalized_preflight = dict(preflight_result or {})
    merged["omakase_preflight_status"] = str(normalized_preflight.get("status") or "").strip()
    merged["omakase_charge_ready"] = normalized_preflight.get("charge_ready")
    merged["omakase_reason_code"] = str(normalized_preflight.get("reason_code") or "").strip()
    merged["omakase_message"] = str(normalized_preflight.get("message") or "").strip()
    merged["omakase_fallback_options"] = [
        dict(item)
        for item in list(normalized_preflight.get("fallback_options") or [])
        if isinstance(item, Mapping)
    ]
    merged["omakase_needs_input_items"] = [
        dict(item)
        for item in list(normalized_preflight.get("needs_input_items") or [])
        if isinstance(item, Mapping)
    ]
    merged["omakase_source_count"] = int(normalized_preflight.get("source_count") or 0)
    merged["omakase_existing_post_count"] = int(normalized_preflight.get("existing_post_count") or 0)
    merged["omakase_usable_posts_count"] = int(normalized_preflight.get("usable_posts_count") or 0)
    merged["omakase_dominant_cluster_count"] = int(normalized_preflight.get("dominant_cluster_count") or 0)
    merged["omakase_available"] = bool(normalized_preflight.get("omakase_available"))
    seed = normalized_preflight.get("seed")
    if not isinstance(seed, Mapping):
        return merged
    seed_dict = dict(seed)
    for key in (
        "article_type",
        "user_prompt_text",
        "source_mode",
        "industry_hint",
    ):
        value = seed_dict.get(key)
        if _normalize_text(value):
            merged[key] = value
    for key in ("source_values", "source_documents", "source_trace"):
        if key in seed_dict:
            merged[key] = list(seed_dict.get(key) or [])
    return merged
