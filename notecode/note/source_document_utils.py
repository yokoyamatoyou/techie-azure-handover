"""Shared source document normalization helpers for current mainline."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict

from core.app_config import get_source_reading_config

_DEFAULT_SOURCE_DOCUMENT_MAX_CHARS = 12000


def get_source_document_max_chars() -> int:
    source_cfg = get_source_reading_config()
    if not isinstance(source_cfg, dict):
        return _DEFAULT_SOURCE_DOCUMENT_MAX_CHARS
    try:
        configured = int(
            source_cfg.get("max_chars_per_source", _DEFAULT_SOURCE_DOCUMENT_MAX_CHARS)
            or _DEFAULT_SOURCE_DOCUMENT_MAX_CHARS
        )
    except (TypeError, ValueError):
        return _DEFAULT_SOURCE_DOCUMENT_MAX_CHARS
    return max(1, configured)


def truncate_source_document_content(content: Any) -> str:
    return str(content or "").strip()[: get_source_document_max_chars()]


def _coerce_source_document_mapping(item: Any) -> Mapping[str, Any]:
    if isinstance(item, Mapping):
        return item
    return {
        "title": getattr(item, "title", ""),
        "content": getattr(item, "content", ""),
        "url": getattr(item, "url", ""),
        "source_type": getattr(item, "source_type", ""),
        "source_path": getattr(item, "source_path", ""),
        "content_type": getattr(item, "content_type", ""),
        "notices": getattr(item, "notices", []),
    }


def normalize_source_document_entry(
    item: Any,
    *,
    include_content_type: bool = False,
) -> Dict[str, Any]:
    raw = _coerce_source_document_mapping(item)
    title = str(raw.get("title") or "").strip()
    content = truncate_source_document_content(raw.get("content") or "")
    url = str(raw.get("url") or "").strip()
    source_path = str(raw.get("source_path") or "").strip()
    locator = str(raw.get("locator") or url or source_path or title).strip()
    notices_raw = raw.get("notices", [])
    notices = []
    if isinstance(notices_raw, list):
        for notice in notices_raw:
            text = str(notice or "").strip()
            if text:
                notices.append(text)
    if not title and not content and not locator:
        return {}
    normalized: Dict[str, Any] = {
        "title": title[:200],
        "content": content,
        "locator": locator[:400],
        "source_type": str(raw.get("source_type") or "url").strip()[:40] or "url",
        "notices": notices[:6],
    }
    if include_content_type:
        normalized["content_type"] = str(raw.get("content_type") or "").strip()[:80]
    return normalized
