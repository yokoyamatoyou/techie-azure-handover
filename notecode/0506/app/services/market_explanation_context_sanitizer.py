from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


SPACED_ASCII_RUN_RE = re.compile(r"(?:\b[A-Za-z]\s+){3,}[A-Za-z]\b\s*")
JAPANESE_OR_DIGIT_SPACING_RE = re.compile(r"(?<=[一-龯ぁ-んァ-ン０-９])\s+(?=[一-龯ぁ-んァ-ン０-９])")


def sanitize_market_explanation_writer_context(
    article_brief: dict[str, Any],
    knowledge_pack: dict[str, Any],
    selected_source_excerpts: list[dict[str, Any]] | None,
) -> tuple[dict[str, Any], list[dict[str, Any]] | None]:
    brief = article_brief.get("article_brief", {}) if isinstance(article_brief, dict) else {}
    if str(brief.get("genre_id") or "") != "market_explanation":
        return knowledge_pack, selected_source_excerpts

    sanitized_knowledge = _sanitize_knowledge_pack(knowledge_pack)
    sanitized_excerpts = _sanitize_selected_source_excerpts(selected_source_excerpts)
    return sanitized_knowledge, sanitized_excerpts


def sanitize_market_explanation_context_text(text: str) -> str:
    lines = []
    for raw_line in str(text or "").replace("\r\n", "\n").splitlines():
        line = _sanitize_context_line(raw_line)
        if not line or _is_surface_only_line(line):
            continue
        lines.append(line)
    return "\n".join(_join_wrapped_lines(lines)).strip()


def _sanitize_selected_source_excerpts(
    selected_source_excerpts: list[dict[str, Any]] | None,
) -> list[dict[str, Any]] | None:
    if not selected_source_excerpts:
        return selected_source_excerpts
    sanitized = deepcopy(selected_source_excerpts)
    for excerpt in sanitized:
        if not isinstance(excerpt, dict):
            continue
        excerpt["text"] = sanitize_market_explanation_context_text(str(excerpt.get("text") or ""))
    return sanitized


def _sanitize_knowledge_pack(knowledge_pack: dict[str, Any]) -> dict[str, Any]:
    sanitized = deepcopy(knowledge_pack)
    pack = sanitized.get("article_knowledge_pack") if isinstance(sanitized, dict) else None
    facts = pack.get("confirmed_facts") if isinstance(pack, dict) else None
    if not isinstance(facts, list):
        return sanitized
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        for key in ("claim", "preferred_expression"):
            value = _sanitize_context_line(str(fact.get(key) or ""))
            if value:
                fact[key] = value
    return sanitized


def _sanitize_context_line(text: str) -> str:
    line = SPACED_ASCII_RUN_RE.sub("", str(text or ""))
    line = JAPANESE_OR_DIGIT_SPACING_RE.sub("", line)
    line = re.sub(r"ver\.\s*1\.0\s*令和([０-９0-9]+)年([０-９0-9]+)月", r"ver.1.0（令和\1年\2月）", line)
    line = re.sub(r"\s+", " ", line).strip(" \t.．…")
    if line.count("「") > line.count("」"):
        return ""
    return line


def _is_surface_only_line(line: str) -> bool:
    compact = re.sub(r"\s+", "", line)
    if not compact:
        return True
    if _mostly_spaced_ascii(line):
        return True
    if compact in {
        "生成AIに関する実態調査報告書",
        "生成AIに関する実態調査報告書ver.1.0（概要）",
        "公正取引委員会",
        "前回ペーパー",
        "実態調査報告書ver.1.0",
    }:
        return True
    if re.fullmatch(r"ver\.?1\.0(?:（?令和[０-９0-9]+年[０-９0-9]+月）?)?", compact):
        return True
    if re.fullmatch(r"令和[０-９0-9]+年[０-９0-9]+月", compact):
        return True
    if re.fullmatch(r"[０-９0-9一二三四五六七八九十]+[．.].{1,32}", compact):
        return True
    return False


def _join_wrapped_lines(lines: list[str]) -> list[str]:
    joined: list[str] = []
    buffer = ""
    for line in lines:
        if not buffer:
            buffer = line
            continue
        if _looks_wrapped(buffer, line):
            buffer += line
            continue
        joined.append(_ensure_sentence(buffer))
        buffer = line
    if buffer:
        joined.append(_ensure_sentence(buffer))
    return joined


def _looks_wrapped(previous: str, current: str) -> bool:
    if previous.endswith(("。", "！", "？", ".", "．")):
        return False
    return len(previous) >= 48 or len(current) <= 12 or previous.endswith(("更なる", "調", "ことと", "形で"))


def _ensure_sentence(line: str) -> str:
    text = line.strip()
    if not text or text.endswith(("。", "！", "？", ".", "．")):
        return text
    return text + "。"


def _mostly_spaced_ascii(text: str) -> bool:
    letters = sum(1 for char in text if char.isascii() and char.isalpha())
    spaces = sum(1 for char in text if char == " ")
    return letters >= 12 and spaces >= max(6, letters // 2)
