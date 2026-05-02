"""Sanitize article preview content rendered as markdown in the UI."""
from __future__ import annotations

import html
import re

try:
    import bleach
except ImportError:  # pragma: no cover - fallback for environments missing optional dependency
    bleach = None

ALLOWED_TAGS = [
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "a",
    "blockquote",
    "code",
    "pre",
    "hr",
]
ALLOWED_ATTRIBUTES = {"a": ["href", "title", "rel", "target"]}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]
UNSAFE_PROTOCOLS = ("javascript:", "data:", "vbscript:")
MARKDOWN_LINK_PATTERN = re.compile(r"(!?\[[^\]]*\]\()([^)]+)(\))")


def _sanitize_markdown_links(text: str) -> str:
    """Replace markdown link targets that use unsafe protocols."""

    def _replace(match: re.Match[str]) -> str:
        prefix, raw_target, suffix = match.groups()
        target = raw_target.strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1].strip()
        target_url = target.split(maxsplit=1)[0].strip("\"'")
        if target_url.lower().startswith(UNSAFE_PROTOCOLS):
            return f"{prefix}#{suffix}"
        return match.group(0)

    return MARKDOWN_LINK_PATTERN.sub(_replace, text)


def sanitize_markdown_preview(content: str) -> str:
    """Sanitize preview text before passing it to ui.markdown()."""
    if not content:
        return ""

    cleaned = _sanitize_markdown_links(content)
    if bleach is None:
        return html.escape(cleaned)

    return bleach.clean(
        cleaned,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
