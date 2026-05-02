from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT_DIR = Path(__file__).resolve().parents[2]
PUBLISHED_POST_INVENTORY_PATH = PROJECT_ROOT_DIR / "logs" / "published_post_inventory.jsonl"
PUBLISHED_POST_INVENTORY_PATH_WORKSPACE = WORKSPACE_ROOT_DIR / "logs" / "published_post_inventory.jsonl"

_CONNECTIVE_PATTERN = re.compile(r"(ただし|また|一方で|そのため|そこで|なお|まず|次に)")
_ENDING_PATTERN = re.compile(r"(です|ます|でした|ました|ません|でしょう)(?:。|$)")
_PLACEHOLDER_TITLE_SET = {"[TITLE]", "TITLE"}
_FOLLOWUP_MIN_ALIGNMENT_SCORE = 0.55
_FOLLOWUP_MAX_SOFT_WARNING_COUNT = 3
_FOLLOWUP_MAX_NATURALNESS_ISSUE_COUNT = 1
_PAST_BLOG_INSTRUCTION_PATTERN = re.compile(
    r"(前の指示を無視|内部指示を無視|SYSTEM\s*:|source\s*grounding\s*guard.*無効|価格を断定|ignore\s+.*instructions)",
    re.I,
)


def _to_plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _to_plain_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _normalize_text(value: Any) -> str:
    return str(value or "").replace("\r", "\n").replace("\x00", "").strip()


def _sanitize_inline_text(value: Any, *, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", _normalize_text(value)).strip()
    if len(text) > limit:
        return text[:limit].rstrip() + "..."
    return text


def _sanitize_past_blog_hint(value: Any, *, limit: int = 160) -> str:
    text = _sanitize_inline_text(value, limit=limit)
    if not text or _PAST_BLOG_INSTRUCTION_PATTERN.search(text):
        return ""
    return text


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _extract_body_excerpt(body: str, *, limit: int = 220) -> str:
    text = re.sub(r"^##\s*", "", _normalize_text(body), flags=re.MULTILINE)
    text = re.sub(r"\n+", " ", text)
    return _sanitize_inline_text(text, limit=limit)


def _split_sentences(text: str) -> List[str]:
    source = _normalize_text(text)
    if not source:
        return []
    return [item.strip() for item in re.split(r"(?<=[。！？])\s*", source) if item.strip()]


def _summarize_sentence_length_band(text: str) -> str:
    sentences = _split_sentences(text)
    if not sentences:
        return "short-medium"
    avg_chars = sum(len(item) for item in sentences) / max(1, len(sentences))
    if avg_chars < 28:
        return "short-medium"
    if avg_chars < 45:
        return "short-medium-long"
    return "medium-long"


def _summarize_paragraph_breath(text: str) -> str:
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", _normalize_text(text)) if item.strip()]
    if not paragraphs:
        return "balanced"
    sentence_counts = [len(_split_sentences(item)) for item in paragraphs]
    avg_sentences = sum(sentence_counts) / max(1, len(sentence_counts))
    if avg_sentences <= 2.0:
        return "short"
    if avg_sentences <= 3.2:
        return "balanced"
    return "dense"


def _summarize_ending_mix(text: str) -> str:
    endings = _ENDING_PATTERN.findall(_normalize_text(text))
    if not endings:
        return "balanced"
    unique_endings = len(set(endings))
    if unique_endings <= 1:
        return "formal-heavy"
    if unique_endings == 2:
        return "balanced"
    return "mixed"


def _summarize_subject_visibility(
    text: str,
    *,
    speaker_profile: str,
) -> str:
    lowered = _normalize_text(text)
    explicit_hits = sum(lowered.count(token) for token in ("私たち", "当社", "弊社", "私", "わたし"))
    if explicit_hits >= 3:
        return "medium"
    if str(speaker_profile or "").strip():
        return "low-medium"
    return "low"


def _summarize_connective_tolerance(text: str) -> str:
    connective_hits = len(_CONNECTIVE_PATTERN.findall(_normalize_text(text)))
    if connective_hits <= 1:
        return "low"
    if connective_hits <= 3:
        return "low-medium"
    return "medium"


def _build_style_memory_summary(
    *,
    title: str,
    lead: str,
    body: str,
    speaker_profile: str,
) -> Dict[str, str]:
    combined = "\n\n".join(part for part in (title, lead, body) if _normalize_text(part))
    return {
        "paragraph_breath": _summarize_paragraph_breath(combined),
        "sentence_length_band": _summarize_sentence_length_band(combined),
        "ending_mix": _summarize_ending_mix(combined),
        "subject_visibility": _summarize_subject_visibility(combined, speaker_profile=speaker_profile),
        "connective_tolerance": _summarize_connective_tolerance(combined),
    }


def _build_quality_summary(result: Mapping[str, Any] | None) -> Dict[str, Any]:
    normalized_result = _to_plain_dict(result)
    pipeline = _to_plain_dict(normalized_result.get("pipeline_check"))
    output_guard = _to_plain_dict(normalized_result.get("output_guard")) or _to_plain_dict(pipeline.get("output_guard"))
    contract_alignment = _to_plain_dict(pipeline.get("contract_alignment"))
    contextual_naturalness = _to_plain_dict(
        pipeline.get("contextual_naturalness_report")
    ) or _to_plain_dict(
        _to_plain_dict(pipeline.get("failed_parameters")).get("contextual_naturalness_report")
    )
    title = _normalize_text(normalized_result.get("title"))
    title_placeholder = title in _PLACEHOLDER_TITLE_SET
    alignment_score = _safe_float(
        contract_alignment.get("alignment_score"),
        _safe_float(normalized_result.get("zero_base_alignment_score"), 0.0),
    )
    soft_warning_count = max(
        _safe_int(output_guard.get("soft_warning_count"), 0),
        len([item for item in _to_plain_list(output_guard.get("soft_warnings")) if str(item).strip()]),
    )
    naturalness_issue_count = _safe_int(contextual_naturalness.get("issue_count"), 0)
    naturalness_passed = bool(contextual_naturalness.get("passed", True))
    blocked = bool(output_guard.get("blocked", False))
    passed = (
        not blocked
        and not title_placeholder
        and alignment_score >= _FOLLOWUP_MIN_ALIGNMENT_SCORE
        and soft_warning_count <= _FOLLOWUP_MAX_SOFT_WARNING_COUNT
        and naturalness_passed
        and naturalness_issue_count <= _FOLLOWUP_MAX_NATURALNESS_ISSUE_COUNT
    )
    return {
        "passed": passed,
        "blocked": blocked,
        "reason_code": _sanitize_inline_text(output_guard.get("reason_code"), limit=80),
        "alignment_score": round(alignment_score, 4),
        "soft_warning_count": soft_warning_count,
        "naturalness_passed": naturalness_passed,
        "naturalness_issue_count": naturalness_issue_count,
        "title_placeholder": title_placeholder,
    }


def _normalize_source_trace_item(item: Any) -> Dict[str, str]:
    if not isinstance(item, Mapping):
        return {}
    normalized = {
        "query": _sanitize_inline_text(item.get("query"), limit=120),
        "url": _sanitize_inline_text(item.get("url"), limit=240),
        "publisher": _sanitize_inline_text(item.get("publisher"), limit=120),
        "exact_date": _sanitize_inline_text(item.get("exact_date"), limit=32),
        "excerpt": _sanitize_inline_text(item.get("excerpt"), limit=180),
    }
    return normalized if any(normalized.values()) else {}


def _normalize_source_document_item(item: Any) -> Dict[str, Any]:
    if not isinstance(item, Mapping):
        return {}
    locator = _sanitize_inline_text(item.get("locator") or item.get("url"), limit=240)
    normalized = {
        "title": _sanitize_inline_text(item.get("title"), limit=140),
        "locator": locator,
        "content": _sanitize_inline_text(item.get("content") or item.get("summary") or item.get("excerpt"), limit=320),
        "source_type": _sanitize_inline_text(item.get("source_type") or ("url" if locator.lower().startswith(("http://", "https://")) else "text"), limit=32),
    }
    return normalized if any(str(value).strip() for value in normalized.values()) else {}


def build_published_post_inventory_entry(
    *,
    attempt_id: str,
    timestamp: str,
    result: Mapping[str, Any] | None,
    input_contract: Mapping[str, Any] | None,
    article_type: str,
) -> Dict[str, Any]:
    normalized_result = _to_plain_dict(result)
    normalized_contract = _to_plain_dict(input_contract)
    title = _sanitize_inline_text(normalized_result.get("title"), limit=140) or "Generated Post"
    lead = _sanitize_inline_text(normalized_result.get("lead"), limit=220)
    body_text = str(normalized_result.get("body") or "")
    full_text = str(normalized_result.get("full_text") or "")
    body_excerpt = _extract_body_excerpt(body_text)
    body_chars = len(_normalize_text(body_text))
    full_text_chars = len(_normalize_text(full_text))
    topic_statement = _sanitize_inline_text(normalized_contract.get("topic_statement"), limit=140)
    prompt_raw = _sanitize_inline_text(normalized_contract.get("prompt_raw"), limit=140)
    summary_parts = [part for part in (topic_statement or prompt_raw, lead, body_excerpt) if part]
    summary = " / ".join(summary_parts[:3])[:320]
    continuity_summary = _sanitize_inline_text(
        f"前回は『{title}』で、{topic_statement or lead or body_excerpt or '主要な論点'}を整理した。",
        limit=220,
    )
    speaker_profile = str(normalized_contract.get("speaker_profile") or "").strip()
    style_memory = _build_style_memory_summary(
        title=title,
        lead=lead,
        body=str(normalized_result.get("body") or ""),
        speaker_profile=speaker_profile,
    )
    source_trace = [
        item
        for item in (
            _normalize_source_trace_item(candidate)
            for candidate in _to_plain_list(normalized_contract.get("source_trace"))
        )
        if item
    ][:4]
    source_documents = [
        item
        for item in (
            _normalize_source_document_item(candidate)
            for candidate in _to_plain_list(normalized_contract.get("source_documents"))
        )
        if item
    ][:4]
    quality_summary = _build_quality_summary(normalized_result)
    return {
        "attempt_id": str(attempt_id or "").strip(),
        "timestamp": str(timestamp or "").strip(),
        "title": title,
        "locator": f"generated://{str(attempt_id or '').strip()}",
        "summary": summary,
        "excerpt": body_excerpt or lead,
        "body_chars": body_chars,
        "full_text_chars": full_text_chars,
        "article_type": str(article_type or normalized_contract.get("article_type") or "").strip(),
        "semantic_article_key": str(normalized_contract.get("semantic_article_key") or "").strip(),
        "publisher": "self_blog",
        "exact_date": str(timestamp or "").strip()[:10],
        "continuity_summary": continuity_summary,
        "style_memory": style_memory,
        "quality_summary": quality_summary,
        "source_trace": source_trace,
        "source_documents": source_documents,
    }


def append_published_post_inventory_entry(entry: Mapping[str, Any] | None) -> int:
    normalized = _to_plain_dict(entry)
    if not normalized:
        return 0
    payload = json.dumps(normalized, ensure_ascii=False)
    written = 0
    for target in (PUBLISHED_POST_INVENTORY_PATH, PUBLISHED_POST_INVENTORY_PATH_WORKSPACE):
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as handle:
                handle.write(payload + "\n")
            written += 1
        except Exception:
            continue
    return written


def _load_inventory_lines(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, Mapping):
                entries.append(dict(payload))
    except Exception:
        return []
    return entries


def load_published_post_candidates(*, limit: int = 20) -> List[Dict[str, Any]]:
    loaded = _load_inventory_lines(PUBLISHED_POST_INVENTORY_PATH)
    if not loaded:
        loaded = _load_inventory_lines(PUBLISHED_POST_INVENTORY_PATH_WORKSPACE)
    deduped: List[Dict[str, Any]] = []
    seen_attempt_ids: set[str] = set()
    for item in reversed(loaded):
        normalized = _to_plain_dict(item)
        attempt_id = str(normalized.get("attempt_id") or "").strip()
        if not attempt_id or attempt_id in seen_attempt_ids:
            continue
        seen_attempt_ids.add(attempt_id)
        deduped.append(normalized)
        if len(deduped) >= max(1, int(limit)):
            break
    return deduped


def clear_published_post_inventory() -> None:
    for target in (PUBLISHED_POST_INVENTORY_PATH, PUBLISHED_POST_INVENTORY_PATH_WORKSPACE):
        try:
            if target.exists():
                target.unlink()
        except Exception:
            continue


def _normalize_past_blog_style_memory(value: Any) -> Dict[str, str]:
    style_memory = _to_plain_dict(value)
    return {
        "paragraph_breath": _sanitize_past_blog_hint(style_memory.get("paragraph_breath"), limit=40),
        "sentence_length_band": _sanitize_past_blog_hint(style_memory.get("sentence_length_band"), limit=40),
        "ending_mix": _sanitize_past_blog_hint(style_memory.get("ending_mix"), limit=40),
        "subject_visibility": _sanitize_past_blog_hint(style_memory.get("subject_visibility"), limit=40),
        "connective_tolerance": _sanitize_past_blog_hint(style_memory.get("connective_tolerance"), limit=40),
    }


def normalize_past_blog_context(
    value: Mapping[str, Any] | None,
    *,
    allow_factual_carry: bool = False,
) -> Dict[str, Any]:
    normalized = _to_plain_dict(value)
    if not normalized:
        return {}
    style_memory = _normalize_past_blog_style_memory(normalized.get("style_memory"))
    topic_candidates: List[Any] = []
    topic_candidates.extend(_to_plain_list(normalized.get("topic_memory")))
    for field in ("title", "summary", "excerpt", "continuity_summary"):
        if normalized.get(field):
            topic_candidates.append(normalized.get(field))
    topic_memory: List[str] = []
    blocked_hint_count = 0
    for item in topic_candidates:
        sanitized = _sanitize_past_blog_hint(item, limit=160)
        if not sanitized and _normalize_text(item):
            blocked_hint_count += 1
            continue
        if sanitized and sanitized not in topic_memory:
            topic_memory.append(sanitized)
        if len(topic_memory) >= 4:
            break

    factual_carry_explicit = bool(normalized.get("factual_carry_explicit")) and bool(allow_factual_carry)
    factual_carry: List[str] = []
    if factual_carry_explicit:
        for item in _to_plain_list(normalized.get("factual_carry")):
            sanitized = _sanitize_past_blog_hint(item, limit=160)
            if sanitized and sanitized not in factual_carry:
                factual_carry.append(sanitized)
            if len(factual_carry) >= 4:
                break

    if not any(style_memory.values()) and not topic_memory and not factual_carry:
        return {}
    return {
        "context_origin": "past_blog_derived",
        "style_memory": style_memory,
        "topic_memory": topic_memory,
        "factual_carry": factual_carry,
        "factual_carry_explicit": factual_carry_explicit,
        "blocked_hint_count": blocked_hint_count,
    }


def build_past_blog_context_from_candidate(
    candidate: Mapping[str, Any] | None,
    *,
    allow_factual_carry: bool = False,
    factual_carry: Iterable[Any] | None = None,
) -> Dict[str, Any]:
    normalized = _to_plain_dict(candidate)
    if not normalized:
        return {}
    factual_items = list(factual_carry or [])
    context = {
        "style_memory": _to_plain_dict(normalized.get("style_memory")),
        "topic_memory": [
            normalized.get("title"),
            normalized.get("summary"),
            normalized.get("excerpt"),
        ],
        "factual_carry": factual_items,
        "factual_carry_explicit": bool(allow_factual_carry and factual_items),
    }
    return normalize_past_blog_context(context, allow_factual_carry=allow_factual_carry)


def build_followup_context_from_candidate(candidate: Mapping[str, Any] | None) -> Dict[str, Any]:
    normalized = _to_plain_dict(candidate)
    style_memory = _to_plain_dict(normalized.get("style_memory"))
    quality_summary = _to_plain_dict(normalized.get("quality_summary"))
    return {
        "title": _sanitize_inline_text(normalized.get("title"), limit=140),
        "locator": _sanitize_inline_text(normalized.get("locator"), limit=240),
        "summary": _sanitize_inline_text(normalized.get("summary"), limit=240),
        "continuity_summary": _sanitize_inline_text(normalized.get("continuity_summary"), limit=220),
        "style_memory": {
            "paragraph_breath": _sanitize_inline_text(style_memory.get("paragraph_breath"), limit=40),
            "sentence_length_band": _sanitize_inline_text(style_memory.get("sentence_length_band"), limit=40),
            "ending_mix": _sanitize_inline_text(style_memory.get("ending_mix"), limit=40),
            "subject_visibility": _sanitize_inline_text(style_memory.get("subject_visibility"), limit=40),
            "connective_tolerance": _sanitize_inline_text(style_memory.get("connective_tolerance"), limit=40),
        },
        "quality_summary": {
            "passed": bool(quality_summary.get("passed", False)),
            "blocked": bool(quality_summary.get("blocked", False)),
            "reason_code": _sanitize_inline_text(quality_summary.get("reason_code"), limit=80),
            "alignment_score": round(_safe_float(quality_summary.get("alignment_score"), 0.0), 4),
            "soft_warning_count": _safe_int(quality_summary.get("soft_warning_count"), 0),
            "naturalness_passed": bool(quality_summary.get("naturalness_passed", True)),
            "naturalness_issue_count": _safe_int(quality_summary.get("naturalness_issue_count"), 0),
            "title_placeholder": bool(quality_summary.get("title_placeholder", False)),
        },
        "article_type": _sanitize_inline_text(normalized.get("article_type"), limit=40),
        "semantic_article_key": _sanitize_inline_text(normalized.get("semantic_article_key"), limit=40),
    }
