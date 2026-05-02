"""Deterministic note postprocess helpers for the simple note pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

TAG_NAMES = ("TITLE", "LEAD", "BODY", "HASHTAGS")
TAG_BLOCK_RE = re.compile(r"\[(TITLE|LEAD|BODY|HASHTAGS)\]\s*([\s\S]*?)\s*\[/\1\]", re.IGNORECASE)
TAG_OPEN_RE = re.compile(r"^\[(TITLE|LEAD|BODY|HASHTAGS)\]\s*$", re.IGNORECASE)
TAG_CLOSE_RE = re.compile(r"^\[/\s*(TITLE|LEAD|BODY|HASHTAGS)\]\s*$", re.IGNORECASE)
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
HASHTAG_LINE_RE = re.compile(r"^(?:#[A-Za-z0-9_一-龥ぁ-んァ-ヴー]{2,24}(?:\s+|$)){1,8}$")
LIST_LINE_RE = re.compile(r"^(?:[-*]\s+|\d+\.\s+)")
TAG_ECHO_RE = re.compile(r"^\[/?(?:TITLE|LEAD|BODY|HASHTAGS)\].*$", re.MULTILINE)


@dataclass
class DraftSections:
    title: str
    lead: str
    body: str
    hashtags: str


@dataclass
class NoteRuleCheck:
    passed: bool
    failures: List[str]
    fixes_applied: List[str]


@dataclass
class TaggedOutputContract:
    draft: DraftSections
    parse_mode: str
    missing_sections: List[str]
    complete_article: bool
    tag_names_seen: List[str]


def _clean_multiline_text(value: str) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_paragraphs(text: str) -> List[str]:
    return [chunk.strip() for chunk in re.split(r"\n\s*\n", _clean_multiline_text(text)) if chunk.strip()]


def _clean_title(value: str) -> str:
    return re.sub(r"^#+\s*", "", str(value or "")).strip(" 「」『』")


def _clean_lead(value: str) -> str:
    return re.sub(r"\s+", " ", _clean_multiline_text(value)).strip()


def _heading_titles(body: str) -> List[str]:
    titles: List[str] = []
    for line in str(body or "").splitlines():
        stripped = line.strip()
        match = HEADING_RE.match(stripped)
        if not match:
            continue
        title = match.group(1).strip()
        if title != "目次":
            titles.append(title)
    return titles


def _strip_existing_toc(body: str) -> Tuple[str, bool]:
    lines = str(body or "").splitlines()
    kept: List[str] = []
    removed = False
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped != "## 目次":
            kept.append(lines[index].rstrip())
            index += 1
            continue
        removed = True
        index += 1
        while index < len(lines):
            current = lines[index].strip()
            if not current:
                index += 1
                continue
            if HEADING_RE.match(current):
                break
            if LIST_LINE_RE.match(current):
                index += 1
                continue
            break
    return _clean_multiline_text("\n".join(kept)), removed


def _normalize_body_spacing(body: str) -> str:
    lines = [line.rstrip() for line in str(body or "").splitlines()]
    normalized: List[str] = []
    previous_was_list = False
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            if normalized and normalized[-1] != "":
                normalized.append("")
            previous_was_list = False
            continue
        is_heading = bool(HEADING_RE.match(stripped)) and stripped != "## 目次"
        is_list = bool(LIST_LINE_RE.match(stripped))
        if is_heading and normalized and normalized[-1] != "":
            normalized.append("")
        if previous_was_list and not is_list and normalized and normalized[-1] != "":
            normalized.append("")
        if is_list and normalized and normalized[-1] != "" and not previous_was_list:
            normalized.append("")
        normalized.append(stripped)
        if is_heading:
            normalized.append("")
        previous_was_list = is_list
    compacted: List[str] = []
    for line in normalized:
        if line == "" and (not compacted or compacted[-1] == ""):
            continue
        compacted.append(line)
    while compacted and compacted[-1] == "":
        compacted.pop()
    return "\n".join(compacted).strip()


def _build_toc_section(headings: List[str]) -> str:
    return "\n".join(["## 目次", *[f"- {title}" for title in headings]])


def _should_include_toc(body: str, headings: List[str]) -> bool:
    return len(_clean_multiline_text(body)) >= 2500 and len(headings) >= 4


def _extract_toc_items(body: str) -> List[str]:
    lines = str(body or "").splitlines()
    items: List[str] = []
    inside_toc = False
    for line in lines:
        stripped = line.strip()
        if stripped == "## 目次":
            inside_toc = True
            continue
        if not inside_toc:
            continue
        if not stripped:
            continue
        if HEADING_RE.match(stripped):
            break
        if LIST_LINE_RE.match(stripped):
            item = re.sub(r"^(?:[-*]\s+|\d+\.\s+)", "", stripped).strip()
            if item:
                items.append(item)
            continue
        break
    return items


def _detect_list_issues(body_without_toc: str) -> List[str]:
    failures: List[str] = []
    current_length = 0
    current_markers: set[str] = set()
    for line in list(str(body_without_toc or "").splitlines()) + [""]:
        stripped = line.strip()
        if not stripped or HEADING_RE.match(stripped):
            if current_length > 8 and "list_block_too_long" not in failures:
                failures.append("list_block_too_long")
            if len(current_markers) > 1 and "list_marker_mixed" not in failures:
                failures.append("list_marker_mixed")
            current_length = 0
            current_markers = set()
            continue
        if not LIST_LINE_RE.match(stripped):
            if current_length > 8 and "list_block_too_long" not in failures:
                failures.append("list_block_too_long")
            if len(current_markers) > 1 and "list_marker_mixed" not in failures:
                failures.append("list_marker_mixed")
            current_length = 0
            current_markers = set()
            continue
        current_length += 1
        current_markers.add("ordered" if re.match(r"^\d+\.\s+", stripped) else "unordered")
    return failures


def parse_tagged_output(raw: str) -> DraftSections:
    return inspect_tagged_output_contract(raw).draft


def inspect_tagged_output_contract(raw: str) -> TaggedOutputContract:
    raw_text = str(raw or "")
    matches = {name.upper(): "" for name in TAG_NAMES}
    tag_names_seen: List[str] = []
    for tag_name, body in TAG_BLOCK_RE.findall(raw_text):
        normalized_name = str(tag_name).upper()
        matches[normalized_name] = _clean_multiline_text(body)
        if normalized_name not in tag_names_seen:
            tag_names_seen.append(normalized_name)
    if matches["BODY"]:
        draft = DraftSections(
            title=matches["TITLE"],
            lead=matches["LEAD"],
            body=matches["BODY"],
            hashtags=matches["HASHTAGS"],
        )
        missing_sections = [
            name.lower()
            for name, value in (
                ("TITLE", draft.title),
                ("LEAD", draft.lead),
                ("BODY", draft.body),
                ("HASHTAGS", draft.hashtags),
            )
            if not _clean_multiline_text(value)
        ]
        return TaggedOutputContract(
            draft=draft,
            parse_mode="tag_blocks",
            missing_sections=missing_sections,
            complete_article=not missing_sections,
            tag_names_seen=tag_names_seen,
        )

    line_parsed = _parse_tagged_output_by_lines(raw_text)
    if line_parsed is not None and line_parsed.body:
        for match in re.finditer(r"\[(TITLE|LEAD|BODY|HASHTAGS)\]", raw_text, flags=re.IGNORECASE):
            normalized_name = str(match.group(1) or "").upper()
            if normalized_name not in tag_names_seen:
                tag_names_seen.append(normalized_name)
        missing_sections = [
            name.lower()
            for name, value in (
                ("TITLE", line_parsed.title),
                ("LEAD", line_parsed.lead),
                ("BODY", line_parsed.body),
                ("HASHTAGS", line_parsed.hashtags),
            )
            if not _clean_multiline_text(value)
        ]
        return TaggedOutputContract(
            draft=line_parsed,
            parse_mode="line_recovery",
            missing_sections=missing_sections,
            complete_article=not missing_sections,
            tag_names_seen=tag_names_seen,
        )

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    title = lines[0] if lines else ""
    rest = "\n".join(lines[1:]).strip()
    paragraphs = _split_paragraphs(rest)
    lead = paragraphs[0] if paragraphs else ""
    body = "\n\n".join(paragraphs[1:] if len(paragraphs) > 1 else paragraphs)
    draft = DraftSections(title=title, lead=lead, body=body, hashtags="")
    missing_sections = [
        name.lower()
        for name, value in (
            ("TITLE", draft.title),
            ("LEAD", draft.lead),
            ("BODY", draft.body),
            ("HASHTAGS", draft.hashtags),
        )
        if not _clean_multiline_text(value)
    ]
    return TaggedOutputContract(
        draft=draft,
        parse_mode="plain_fallback",
        missing_sections=missing_sections,
        complete_article=False,
        tag_names_seen=tag_names_seen,
    )


def _parse_tagged_output_by_lines(raw: str) -> DraftSections | None:
    sections = {name.upper(): [] for name in TAG_NAMES}
    current_tag = ""
    saw_tag = False

    for raw_line in str(raw or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        stripped = raw_line.strip()
        open_match = TAG_OPEN_RE.match(stripped)
        if open_match:
            saw_tag = True
            current_tag = str(open_match.group(1) or "").upper()
            continue

        close_match = TAG_CLOSE_RE.match(stripped)
        if close_match:
            saw_tag = True
            if current_tag == str(close_match.group(1) or "").upper():
                current_tag = ""
            continue

        if current_tag:
            sections[current_tag].append(raw_line.rstrip())

    if not saw_tag:
        return None

    parsed = {
        name: _clean_multiline_text("\n".join(lines))
        for name, lines in sections.items()
    }
    if not any(parsed.values()):
        return None
    return DraftSections(
        title=parsed["TITLE"],
        lead=parsed["LEAD"],
        body=parsed["BODY"],
        hashtags=parsed["HASHTAGS"],
    )


def apply_note_local_edits(draft: DraftSections, *, title_hint: str = "") -> tuple[DraftSections, List[str]]:
    fixes: List[str] = []
    title = _clean_title(draft.title)
    lead = _clean_lead(draft.lead)
    body = str(draft.body or "").strip()
    hashtags = _clean_multiline_text(draft.hashtags)

    cleaned_body = TAG_ECHO_RE.sub("", body).strip()
    if cleaned_body != body:
        fixes.append("strip_tag_echoes")
        body = cleaned_body

    single_hash_body = re.sub(r"^#(?!#)\s*", "", body, flags=re.MULTILINE).strip()
    if single_hash_body != body:
        fixes.append("strip_single_hash_prefix")
        body = single_hash_body

    body_lines: List[str] = []
    removed_title_echo = False
    removed_hashtag_echo = False
    for line in body.splitlines():
        stripped = line.strip()
        if title and stripped == title:
            removed_title_echo = True
            continue
        if HASHTAG_LINE_RE.match(stripped):
            removed_hashtag_echo = True
            continue
        body_lines.append(stripped if stripped else "")
    if removed_title_echo:
        fixes.append("remove_body_title_echo")
    if removed_hashtag_echo:
        fixes.append("remove_body_hashtag_echo")
    body = "\n".join(body_lines)

    body_without_toc, removed_toc = _strip_existing_toc(body)
    if removed_toc:
        fixes.append("normalize_toc")
    normalized_body = _normalize_body_spacing(body_without_toc)
    if normalized_body != body_without_toc:
        fixes.append("normalize_spacing")
    body = normalized_body

    headings = _heading_titles(body)
    if _should_include_toc(body, headings):
        body = f"{_build_toc_section(headings)}\n\n{body}".strip()
        fixes.append("rebuild_toc")

    if not lead:
        content_body, _ = _strip_existing_toc(body)
        paragraphs = [paragraph for paragraph in _split_paragraphs(content_body) if not paragraph.startswith("## ")]
        if paragraphs:
            lead = paragraphs[0][:180].rstrip("、, ")
            fixes.append("derive_lead")

    if not title:
        title = _clean_title(title_hint)

    return DraftSections(
        title=title,
        lead=lead,
        body=_clean_multiline_text(body),
        hashtags=hashtags,
    ), fixes


def validate_note_rules(draft: DraftSections) -> NoteRuleCheck:
    failures: List[str] = []
    title = _clean_title(draft.title)
    body = _clean_multiline_text(draft.body)
    body_without_toc, toc_present = _strip_existing_toc(body)
    headings = _heading_titles(body_without_toc)
    should_have_toc = _should_include_toc(body_without_toc, headings)
    toc_items = _extract_toc_items(body) if toc_present else []

    if should_have_toc and not toc_present:
        failures.append("toc_missing")
    if not should_have_toc and toc_present:
        failures.append("toc_unexpected")
    if toc_present and toc_items != headings:
        failures.append("toc_heading_mismatch")
    if title and re.search(rf"(?m)^{re.escape(title)}$", body):
        failures.append("body_title_mixed")
    if re.search(r"(?m)^(?!## )(?:#[A-Za-z0-9_一-龥ぁ-んァ-ヴー]{2,24}(?:\s+|$)){1,8}$", body):
        failures.append("body_hashtags_mixed")
    failures.extend(_detect_list_issues(body_without_toc))

    if "\n\n\n" in body:
        failures.append("paragraph_break_unstable")
    lines = body_without_toc.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not HEADING_RE.match(stripped):
            continue
        if index > 0 and lines[index - 1].strip():
            failures.append("paragraph_break_unstable")
            break
        if index + 1 < len(lines) and lines[index + 1].strip():
            failures.append("paragraph_break_unstable")
            break

    deduped_failures: List[str] = []
    for item in failures:
        if item not in deduped_failures:
            deduped_failures.append(item)
    return NoteRuleCheck(passed=not deduped_failures, failures=deduped_failures, fixes_applied=[])


def finalize_note_draft(draft: DraftSections, *, title_hint: str = "") -> tuple[DraftSections, NoteRuleCheck]:
    normalized_draft, fixes = apply_note_local_edits(draft, title_hint=title_hint)
    rule_check = validate_note_rules(normalized_draft)
    rule_check.fixes_applied.extend(fixes)
    return normalized_draft, rule_check
