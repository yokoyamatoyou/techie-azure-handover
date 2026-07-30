from __future__ import annotations

from typing import Any

from app.services.human_visible_surface_gate import check_human_visible_surface
from app.services.style_postprocessor import postprocess_style
from app.services.stylometry import ending_bucket
from app.services.stylometry import split_sentences


EDITOR_REPORT_MARKERS = (
    "全体を見ると",
    "気になる点を挙げる",
    "要するに",
    "必要なら次に",
    "記事全体の整合性",
    "briefで求められている",
    "構成案",
)
MODEL_FREQUENT_REPLACEMENTS = {
    "支える": "担う",
}
CONTINUATIVE_PREDICATE_COMPLETIONS = (
    ("講師となり", "講師となりました"),
    ("ニーズに応え", "ニーズに応えました"),
    ("することにより", "します"),
)


def guard_editor_output(
    stage_name: str,
    before_text: str,
    after_text: str,
    article_brief: dict[str, Any] | None = None,
) -> str:
    before = str(before_text or "").strip()
    after = str(after_text or "").strip()
    if not before or not after:
        return before
    if _adds_announcement_generic_local_opening(stage_name, before, after, article_brief):
        return before
    if _looks_like_editor_report(after):
        return before
    if _drops_floor_reaching_body_below_floor(before, after, article_brief):
        return before
    if _drops_required_announcement_h2_sections(before, after, article_brief):
        return before
    if _looks_like_substantial_content_loss(before, after):
        return before
    return after


def deterministic_targeted_rewrite(
    article_text: str,
    quality_check: dict[str, Any],
    article_brief: dict[str, Any],
) -> str:
    quality = quality_check.get("quality_check", {})
    if not quality.get("rewrite_needed"):
        return article_text

    revised = article_text.replace("いかがでしたでしょうか。", "")
    revised = revised.replace("第一歩", "具体的な準備")
    issue_types = {str(issue.get("type")) for issue in quality.get("issues", []) if isinstance(issue, dict)}
    if "model_frequent_word" in issue_types:
        revised = _reduce_repeated_model_frequent_words(revised, quality)
    if "sentence_too_long" in issue_types:
        revised = _split_overlong_sentences(revised)
    return postprocess_style(revised.strip(), article_brief)


def _reduce_repeated_model_frequent_words(article_text: str, quality: dict[str, Any]) -> str:
    revised = article_text
    stylometry = quality.get("stylometry", {})
    terms = stylometry.get("model_frequent_words", []) if isinstance(stylometry, dict) else []
    for item in terms:
        if not isinstance(item, dict) or item.get("risk") != "medium":
            continue
        term = str(item.get("term") or "")
        replacement = MODEL_FREQUENT_REPLACEMENTS.get(term)
        if term and replacement:
            revised = _replace_after_first(revised, term, replacement)
    return revised


def _replace_after_first(text: str, term: str, replacement: str) -> str:
    first = text.find(term)
    if first < 0:
        return text
    head_end = first + len(term)
    return text[:head_end] + text[head_end:].replace(term, replacement)


def _looks_like_editor_report(text: str) -> bool:
    head = text[:500]
    return any(marker in head for marker in EDITOR_REPORT_MARKERS)


def _looks_like_substantial_content_loss(before_text: str, after_text: str) -> bool:
    before_blocks = _content_block_count(before_text)
    after_blocks = _content_block_count(after_text)
    if before_blocks < 4 or after_blocks > max(1, before_blocks // 2):
        return False
    return len(after_text) < int(len(before_text) * 0.75)


def _drops_floor_reaching_body_below_floor(
    before_text: str,
    after_text: str,
    article_brief: dict[str, Any] | None,
) -> bool:
    floor_chars = _body_length_floor_chars(article_brief)
    if floor_chars <= 0:
        return False
    return (
        _body_chars_excluding_headings(before_text) >= floor_chars
        and _body_chars_excluding_headings(after_text) < floor_chars
    )


def _drops_required_announcement_h2_sections(
    before_text: str,
    after_text: str,
    article_brief: dict[str, Any] | None,
) -> bool:
    if _genre_id(article_brief) != "announcement":
        return False
    before_h2 = _h2_count(before_text)
    return before_h2 >= 2 and _h2_count(after_text) < before_h2


def _h2_count(markdown: str) -> int:
    count = 0
    for line in str(markdown or "").splitlines():
        stripped = line.lstrip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            count += 1
    return count


def _body_length_floor_chars(article_brief: dict[str, Any] | None) -> int:
    if not isinstance(article_brief, dict):
        return 0
    brief = article_brief.get("article_brief")
    if not isinstance(brief, dict):
        brief = article_brief
    try:
        return int(brief.get("body_length_floor_chars") or 0)
    except (TypeError, ValueError):
        return 0


def _adds_announcement_generic_local_opening(
    stage_name: str,
    before_text: str,
    after_text: str,
    article_brief: dict[str, Any] | None,
) -> bool:
    if stage_name != "opening_editor" or _genre_id(article_brief) != "announcement":
        return False
    before_codes = _human_visible_surface_codes(before_text, article_brief)
    after_codes = _human_visible_surface_codes(after_text, article_brief)
    return "generic_local_opening" in after_codes and "generic_local_opening" not in before_codes


def _human_visible_surface_codes(text: str, article_brief: dict[str, Any] | None) -> set[str]:
    gate = check_human_visible_surface(text, article_brief)["human_visible_surface_gate"]
    return {str(finding.get("code") or "") for finding in gate.get("findings", []) if isinstance(finding, dict)}


def _genre_id(article_brief: dict[str, Any] | None) -> str:
    if not isinstance(article_brief, dict):
        return ""
    brief = article_brief.get("article_brief")
    if not isinstance(brief, dict):
        brief = article_brief
    return str(brief.get("genre_id") or "")


def _body_chars_excluding_headings(markdown: str) -> int:
    return len(
        "".join(
            "".join(line.split())
            for line in str(markdown or "").splitlines()
            if not line.lstrip().startswith("#")
        )
    )


def _content_block_count(text: str) -> int:
    return len([block for block in text.split("\n\n") if block.strip()])


def _split_overlong_sentences(text: str, limit: int = 90) -> str:
    blocks = [block.strip() for block in text.strip().split("\n\n") if block.strip()]
    output: list[str] = []
    for block in blocks:
        heading, body = _split_heading_block(block)
        if heading:
            output.append(heading)
            if not body:
                continue
            block = body
        sentences: list[str] = []
        for sentence in split_sentences(block):
            sentences.extend(_split_one_sentence(sentence, limit))
        output.append("".join(sentences))
    return "\n\n".join(output)


def _split_heading_block(block: str) -> tuple[str, str]:
    if not block.startswith("#"):
        return "", block
    lines = block.splitlines()
    if not lines:
        return "", block
    heading = lines[0].strip()
    body = "\n".join(lines[1:]).strip()
    return heading, body


def _split_one_sentence(sentence: str, limit: int) -> list[str]:
    if len(sentence.rstrip("。！？!?")) <= limit:
        return [sentence]
    stripped = sentence.rstrip()
    punctuation = "。" if stripped.endswith("。") else ""
    body = stripped.removesuffix("。")
    continuative_event_split = _split_continuative_event_sentence(body, punctuation, limit)
    if continuative_event_split:
        return continuative_event_split
    continuative_predicate_split = _split_continuative_predicate_sentence(body, punctuation, limit)
    if continuative_predicate_split:
        return continuative_predicate_split
    split_at = _best_japanese_comma_split(body, limit)
    if split_at <= 0:
        return [sentence]
    first = body[:split_at].rstrip("、")
    second = body[split_at + 1 :].lstrip()
    if not first or not second:
        return [sentence]
    first_sentence = first + "。"
    if not _can_end_sentence(first_sentence):
        return [sentence]
    return [first_sentence, *_split_one_sentence(second + punctuation, limit)]


def _split_continuative_event_sentence(body: str, punctuation: str, limit: int) -> list[str]:
    marker = "発足し、"
    if marker not in body:
        return []
    first, second = body.split(marker, 1)
    if not first or not second:
        return []
    first_sentence = first + "発足しました。"
    if len(first_sentence.rstrip("。！？!?")) > limit or not _can_end_sentence(first_sentence):
        return []
    return [first_sentence, *_split_one_sentence(second.lstrip() + punctuation, limit)]


def _split_continuative_predicate_sentence(body: str, punctuation: str, limit: int) -> list[str]:
    candidates = [index for index, char in enumerate(body) if char == "、"]
    if not candidates:
        return []
    midpoint = min(max(35, len(body) // 2), limit)
    for index in sorted(candidates, key=lambda candidate: abs(candidate - midpoint)):
        first = body[:index].rstrip("、")
        second = body[index + 1 :].lstrip()
        if not first or not second:
            continue
        completed_first = _complete_continuative_predicate(first)
        if not completed_first:
            continue
        first_sentence = completed_first + "。"
        if len(first_sentence.rstrip("。！？!?")) > limit or not _can_end_sentence(first_sentence):
            continue
        return [first_sentence, *_split_one_sentence(second + punctuation, limit)]
    return []


def _complete_continuative_predicate(text: str) -> str:
    for suffix, completion in CONTINUATIVE_PREDICATE_COMPLETIONS:
        if text.endswith(suffix):
            return text[: -len(suffix)] + completion
    return ""


def _best_japanese_comma_split(text: str, limit: int) -> int:
    candidates = [index for index, char in enumerate(text) if char == "、"]
    if not candidates:
        return -1
    midpoint = min(max(35, len(text) // 2), limit)
    for index in sorted(candidates, key=lambda candidate: abs(candidate - midpoint)):
        first = text[:index].rstrip("、") + "。"
        if _can_end_sentence(first):
            return index
    return -1


def _can_end_sentence(sentence: str) -> bool:
    return ending_bucket(sentence) != "other"
