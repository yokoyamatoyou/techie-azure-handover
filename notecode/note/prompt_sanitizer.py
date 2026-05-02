"""Helpers to safely embed user-provided text into LLM prompts."""
from __future__ import annotations

import json
import re

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def sanitize_untrusted_text(value: str, max_length: int = 1200) -> str:
    """Normalize and trim untrusted user text before prompt embedding."""
    if not value:
        return ""

    cleaned = str(value).replace("\r\n", "\n").replace("\r", "\n")
    cleaned = CONTROL_CHARS.sub("", cleaned)
    cleaned = cleaned.strip()

    if max_length > 0 and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()
    return cleaned


def to_prompt_json_string(
    value: str,
    *,
    empty_value: str = "指定なし",
    max_length: int = 1200,
) -> str:
    """Return an escaped JSON string so user input is treated as plain data."""
    cleaned = sanitize_untrusted_text(value, max_length=max_length)
    if not cleaned:
        cleaned = empty_value
    return json.dumps(cleaned, ensure_ascii=False)
