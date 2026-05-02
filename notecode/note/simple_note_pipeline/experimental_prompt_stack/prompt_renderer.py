"""Prompt renderer for the experimental prompt stack assets."""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from note.prompt_sanitizer import sanitize_untrusted_text


_WHOLE_LINE_PLACEHOLDER_RE = re.compile(r"^\{\{([A-Z0-9_]+)\}\}$")
_INLINE_VALUE_RE = re.compile(r"<<([a-z0-9_]+)>>", flags=re.IGNORECASE)


def _append_block(buffer: list[str], title: str, lines: Sequence[str]) -> None:
    clean_lines = [sanitize_untrusted_text(str(line), max_length=400).strip() for line in lines if str(line).strip()]
    if not clean_lines:
        return
    if buffer:
        buffer.append("")
    buffer.append(f"[{title}]")
    buffer.extend(clean_lines)


def _render_inline_values(text: str, inline_values: Mapping[str, Any] | None = None) -> str:
    if not inline_values:
        return str(text or "")

    def replace(match: re.Match[str]) -> str:
        key = str(match.group(1) or "").strip()
        return str(inline_values.get(key, ""))

    return _INLINE_VALUE_RE.sub(replace, str(text or ""))


def collect_asset_lines(
    sections: Mapping[str, Sequence[str]],
    *section_names: str,
    inline_values: Mapping[str, Any] | None = None,
) -> list[str]:
    lines: list[str] = []
    for section_name in section_names:
        for line in list(sections.get(section_name) or []):
            rendered = _render_inline_values(str(line), inline_values).strip()
            if rendered:
                lines.append(rendered)
    return lines


def _expand_asset_lines(
    lines: Sequence[str],
    *,
    line_placeholders: Mapping[str, Sequence[str]] | None = None,
    inline_values: Mapping[str, Any] | None = None,
) -> list[str]:
    expanded: list[str] = []
    placeholder_map = dict(line_placeholders or {})
    for raw_line in lines:
        line = str(raw_line or "").strip()
        if not line:
            continue
        matched = _WHOLE_LINE_PLACEHOLDER_RE.match(line)
        if matched:
            placeholder_key = str(matched.group(1) or "").strip()
            expanded.extend(str(item).strip() for item in list(placeholder_map.get(placeholder_key) or []) if str(item).strip())
            continue
        rendered = _render_inline_values(line, inline_values).strip()
        if rendered:
            expanded.append(rendered)
    return expanded


def render_stage_prompt(
    *,
    persona_sections: Mapping[str, Sequence[str]],
    ui_slot_lines: Sequence[str],
    dynamic_hint_bundle: Mapping[str, Any],
    source_lines: Sequence[str],
    line_placeholders: Mapping[str, Sequence[str]] | None = None,
    inline_values: Mapping[str, Any] | None = None,
) -> str:
    prompt_lines: list[str] = []
    _append_block(
        prompt_lines,
        "ROLE",
        _expand_asset_lines(
            persona_sections.get("ROLE") or [],
            line_placeholders=line_placeholders,
            inline_values=inline_values,
        ),
    )
    _append_block(prompt_lines, "UI_SLOTS", list(ui_slot_lines))
    dynamic_lines = [
        f"opening_strategy={sanitize_untrusted_text(str(dynamic_hint_bundle.get('opening_strategy') or ''), max_length=140).strip()}",
        f"title_intent={sanitize_untrusted_text(str(dynamic_hint_bundle.get('title_intent') or ''), max_length=140).strip()}",
        f"body_temperature={sanitize_untrusted_text(str(dynamic_hint_bundle.get('body_temperature') or ''), max_length=140).strip()}",
        f"section_opening={sanitize_untrusted_text(str(dynamic_hint_bundle.get('section_opening') or ''), max_length=140).strip()}",
        f"empathy_distance={sanitize_untrusted_text(str(dynamic_hint_bundle.get('empathy_distance') or ''), max_length=140).strip()}",
        f"sentence_rhythm={sanitize_untrusted_text(str(dynamic_hint_bundle.get('sentence_rhythm') or ''), max_length=140).strip()}",
        f"source_usage={sanitize_untrusted_text(str(dynamic_hint_bundle.get('source_usage') or ''), max_length=140).strip()}",
    ]
    dynamic_lines.extend(
        f"overlap_guard[{idx}]={sanitize_untrusted_text(str(line), max_length=140).strip()}"
        for idx, line in enumerate(dynamic_hint_bundle.get("overlap_guard") or [], start=1)
        if str(line or "").strip()
    )
    _append_block(prompt_lines, "DYNAMIC_HINTS", dynamic_lines)
    _append_block(prompt_lines, "SOURCE_GROUNDING", list(source_lines))
    _append_block(
        prompt_lines,
        "TASK",
        _expand_asset_lines(
            persona_sections.get("TASK") or [],
            line_placeholders=line_placeholders,
            inline_values=inline_values,
        ),
    )
    _append_block(
        prompt_lines,
        "OUTPUT",
        _expand_asset_lines(
            persona_sections.get("OUTPUT") or [],
            line_placeholders=line_placeholders,
            inline_values=inline_values,
        ),
    )
    return "\n".join(prompt_lines).strip()
