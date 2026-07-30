"""SNS post helpers for writer-only generation."""
from __future__ import annotations

import re
from typing import Any, Dict


LINKEDIN_MAX_CHARS = 700
LINKEDIN_SHORT_MAX_CHARS = LINKEDIN_MAX_CHARS
COMPANY_FIRST_PERSON_TERMS = ("私たち", "当社", "わたしたち", "弊社")
VISIBLE_MEDIA_NAME_PATTERNS = (
    r"企業note",
    r"(?<![A-Za-z0-9_])note(?![A-Za-z0-9_])",
    r"はてなブログ",
    r"Hatena\s*Blog",
)


def build_linkedin_outputs_from_article(article_markdown: str, brief: Dict[str, Any]) -> Dict[str, Any]:
    """Recompose a LinkedIn post from generated article points without another API call."""
    article = str(article_markdown or "").strip()
    title = _extract_title(article)
    opening = _opening_text(article)
    sections = _section_points(article)
    persona = brief.get("persona") if isinstance(brief.get("persona"), dict) else {}
    problem = str(persona.get("reader_problem") or "").strip()
    goal = str(persona.get("article_goal") or "").strip()

    parts: list[str] = []
    hook = _first_sentence(opening) or title
    if hook:
        parts.append(hook)
    if problem and problem not in "\n".join(parts):
        parts.append(f"背景には、{problem}という迷いがあります。")
    if goal:
        parts.append(f"私たちは、{_goal_purpose(goal)}ために、記事本文の要点を会社側の視点で整理しています。")
    else:
        parts.append("私たちは、記事本文の要点を会社側の視点で整理しています。")

    if sections:
        point_lines = []
        for section in sections[:5]:
            line = section.get("point") or section.get("heading") or ""
            if line:
                point_lines.append(f"・{line}")
        if point_lines:
            parts.append("ブログ本文では、次の観点を整理しました。\n" + "\n".join(point_lines))

    parts.append("気になる点があれば、当社への相談や問い合わせで一緒に確認できます。")

    linkedin_short_text = _fit_post("\n\n".join(part for part in parts if part), LINKEDIN_SHORT_MAX_CHARS)
    return {
        "linkedin_text": linkedin_short_text,
        "linkedin_short_text": linkedin_short_text,
        "sns_generation_strategy": "extract_key_points_then_recompose",
        "sns_max_chars": LINKEDIN_MAX_CHARS,
        "sns_forced_padding_used": False,
    }


def evaluate_linkedin_post_smoke(linkedin_text: str, article_markdown: str) -> Dict[str, Any]:
    text = str(linkedin_text or "").strip()
    article_points = _article_point_terms(article_markdown)
    checks = {
        "linkedin_present": bool(text),
        "linkedin_max_700": len(text) <= LINKEDIN_MAX_CHARS,
        "linkedin_self_perspective": has_company_first_person(text),
        "key_points_preserved": _preserved_point_count(text, article_points) >= min(2, len(article_points)),
        "no_forced_padding_marker": "文字数調整" not in text and "詳しくは本文" not in text,
        "visible_media_name_absent": not _has_visible_media_name(text),
    }
    failed = [key for key, value in checks.items() if not value]
    return {
        "passed": not failed,
        "checks": checks,
        "failed": failed,
        "details": {
            "char_count": len(text),
            "article_point_terms": article_points,
            "preserved_point_count": _preserved_point_count(text, article_points),
            "max_chars": LINKEDIN_MAX_CHARS,
        },
    }


def _extract_title(markdown: str) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if match:
            return _plain(match.group(1))
    return ""


def has_company_first_person(text: str) -> bool:
    return any(term in str(text or "") for term in COMPANY_FIRST_PERSON_TERMS)


def _has_visible_media_name(text: str) -> bool:
    return any(re.search(pattern, str(text or ""), flags=re.IGNORECASE) for pattern in VISIBLE_MEDIA_NAME_PATTERNS)


def _goal_purpose(goal: str) -> str:
    clean = _plain(goal)
    if not clean:
        return "相談前の判断材料を届ける"
    if clean.endswith(("する", "伝える", "届ける", "示す", "整理する", "紹介する")):
        return clean
    return f"{clean}の"


def _opening_text(markdown: str) -> str:
    head = re.split(r"(?m)^##\s+", markdown, maxsplit=1)[0]
    lines = [
        _plain(line)
        for line in head.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return "\n".join(lines).strip()


def _section_points(markdown: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    for part in re.split(r"(?m)^##\s+", markdown)[1:]:
        lines = [_plain(line) for line in part.splitlines() if line.strip()]
        if not lines:
            continue
        heading = lines[0]
        body = "\n".join(lines[1:]).strip()
        sections.append({"heading": heading, "point": _leading_sentences(body, max_sentences=2) or heading})
    return sections


def _first_sentence(text: str) -> str:
    clean = _plain(text)
    if not clean:
        return ""
    chunks = [chunk.strip() for chunk in re.split(r"(?<=[。！？])", clean) if chunk.strip()]
    return chunks[0] if chunks else clean[:120].strip()


def _leading_sentences(text: str, *, max_sentences: int) -> str:
    clean = _plain(text)
    if not clean:
        return ""
    chunks = [chunk.strip() for chunk in re.split(r"(?<=[。！？])", clean) if chunk.strip()]
    if not chunks:
        return clean[:180].strip()
    return "".join(chunks[:max_sentences]).strip()


def _fit_post(text: str, max_chars: int) -> str:
    clean = re.sub(r"\n{3,}", "\n\n", str(text or "").strip())
    if len(clean) <= max_chars:
        return clean
    trimmed = clean[:max_chars].rstrip()
    cut = max(trimmed.rfind("。"), trimmed.rfind("！"), trimmed.rfind("？"), trimmed.rfind("\n\n"))
    if cut >= int(max_chars * 0.6):
        trimmed = trimmed[: cut + 1].rstrip()
    return trimmed


def _article_point_terms(markdown: str) -> list[str]:
    terms: list[str] = []
    title = _extract_title(markdown)
    terms.extend(_content_terms(title))
    for section in _section_points(markdown):
        terms.extend(_content_terms(section.get("heading", "")))
        terms.extend(_content_terms(section.get("point", "")))
    seen: set[str] = set()
    unique = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            unique.append(term)
    return unique[:10]


def _preserved_point_count(text: str, terms: list[str]) -> int:
    return sum(1 for term in terms if term and term in text)


def _content_terms(text: str) -> list[str]:
    candidates = re.split(r"[、。・\s/（）()「」『』]|を|に|が|で|と|か|の|は|へ", str(text or ""))
    stop_terms = {"こと", "ため", "よう", "する", "いる", "まず", "次", "私たち", "当社"}
    return [term for term in candidates if len(term) >= 2 and term not in stop_terms]


def _plain(text: str) -> str:
    clean = re.sub(r"^\s*[-*]\s+", "", str(text or ""), flags=re.MULTILINE)
    clean = re.sub(r"[*_`#>]+", "", clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()
