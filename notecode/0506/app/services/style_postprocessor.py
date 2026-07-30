from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.services.reader_meta_sentence import is_reader_meta_sentence
from app.services.stylometry import ending_bucket, split_sentences


DEFAULT_POLICY = {
    "preferred_sentences_per_paragraph": 2,
    "max_sentences_per_paragraph": 3,
    "line_break_policy": "topic_shift_or_two_sentences",
    "subject_omission_policy": "clear_context_only",
    "ending_bucket_policy": "structural_variation",
    "protected_subject_terms": ["年", "月", "日", "時", "円", "価格", "料金", "責任", "約束", "対象", "変更", "担当"],
}
ENDING_VARIATION_POLICIES = {"structural_variation", "avoid_late_half_bucket_concentration"}
FLOOR_PRESERVATION_MARGIN_CHARS = 40
SOURCE_BRIDGE_MARKERS = (
    "商品",
    "展示会",
    "業務",
    "食材",
    "サービス",
    "提供",
    "対応",
    "納品",
    "会社",
    "事業",
    "理念",
    "ページ",
    "現場",
)


def postprocess_style(text: str, article_brief: dict[str, Any] | None = None) -> str:
    policy = _resolve_policy(article_brief)
    narrator = _resolve_narrator(article_brief)
    preserved_reader_meta = _floor_preserved_reader_meta_counts(text, article_brief)
    preserve_surface_length = _is_floor_critical_surface(text, article_brief)
    blocks = [block.strip() for block in text.strip().split("\n\n") if block.strip()]
    output: list[str] = []
    section_sentences: list[str] = []
    narrator_is_clear = False

    for block in blocks:
        heading, body = _split_heading_block(block)
        if heading:
            _flush_section(output, section_sentences, policy)
            heading = _sanitize_title_heading(heading, narrator)
            output.append(heading)
            narrator_is_clear = False
            if not body:
                continue
            block = body
        for sentence in split_sentences(block):
            sentence = _rewrite_company_intro_page_summary_voice(sentence, article_brief, narrator)
            if is_reader_meta_sentence(sentence):
                if not _consume_preserved_reader_meta(preserved_reader_meta, sentence):
                    continue
            revised = (
                sentence
                if preserve_surface_length
                else _omit_repeated_narrator(sentence, narrator, narrator_is_clear, policy)
            )
            section_sentences.append(revised)
            if _starts_with_narrator(sentence, narrator):
                narrator_is_clear = True

    _flush_section(output, section_sentences, policy)
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


def _floor_preserved_reader_meta_counts(
    text: str,
    article_brief: dict[str, Any] | None,
) -> Counter[str]:
    floor_chars = _resolve_body_length_floor(article_brief)
    if floor_chars <= 0:
        return Counter()
    candidates = [sentence for sentence in _iter_body_sentences(text) if is_reader_meta_sentence(sentence)]
    if not candidates:
        return Counter()
    removable_chars = sum(_char_count(sentence) for sentence in candidates)
    safe_after_removal = _char_count(text) - removable_chars
    target_after_removal = floor_chars + FLOOR_PRESERVATION_MARGIN_CHARS
    if safe_after_removal >= target_after_removal:
        return Counter()

    needed_chars = target_after_removal - safe_after_removal
    preserved: list[str] = []
    for sentence in sorted(candidates, key=_reader_meta_preservation_rank):
        preserved.append(sentence)
        needed_chars -= _char_count(sentence)
        if needed_chars <= 0:
            break
    return Counter(preserved)


def _iter_body_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    for block in [block.strip() for block in str(text or "").strip().split("\n\n") if block.strip()]:
        heading, body = _split_heading_block(block)
        sentences.extend(split_sentences(body if heading else block))
    return sentences


def _reader_meta_preservation_rank(sentence: str) -> tuple[int, int]:
    text = re.sub(r"\s+", "", sentence)
    source_backed = bool(re.search(r"[0-9０-９]", text)) or any(marker in text for marker in SOURCE_BRIDGE_MARKERS)
    return (0 if source_backed else 1, -_char_count(sentence))


def _consume_preserved_reader_meta(preserved: Counter[str], sentence: str) -> bool:
    if preserved[sentence] <= 0:
        return False
    preserved[sentence] -= 1
    return True


def _is_floor_critical_surface(text: str, article_brief: dict[str, Any] | None) -> bool:
    floor_chars = _resolve_body_length_floor(article_brief)
    return floor_chars > 0 and _char_count(text) <= floor_chars + FLOOR_PRESERVATION_MARGIN_CHARS


def _resolve_body_length_floor(article_brief: dict[str, Any] | None) -> int:
    if not article_brief:
        return 0
    try:
        return int(article_brief.get("article_brief", {}).get("body_length_floor_chars") or 0)
    except (TypeError, ValueError):
        return 0


def _char_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def _sanitize_title_heading(heading: str, narrator: str) -> str:
    if not heading.startswith("# ") or heading.startswith("##"):
        return heading
    title = heading[2:].strip()
    original = title
    narrator_pattern = re.escape(narrator)
    viewpoint_intro_tail = rf"{narrator_pattern}の視点(?:で|から)(?:ご)?紹介(?:します)?"
    patterns = (
        rf"[、,]?\s*{viewpoint_intro_tail}$",
        rf"[、,]?\s*{narrator_pattern}からご紹介します$",
        rf"[、,]?\s*{narrator_pattern}がご紹介します$",
    )
    for pattern in patterns:
        title = re.sub(pattern, "", title).strip()
    title = re.sub(r"[、,]\s*$", "", title).strip()
    title = re.sub(r"を\s*$", "", title).strip()
    if not title:
        title = original
    return f"# {title}"


def _resolve_policy(article_brief: dict[str, Any] | None) -> dict[str, Any]:
    if not article_brief:
        return DEFAULT_POLICY.copy()
    brief = article_brief.get("article_brief", {})
    policy = DEFAULT_POLICY.copy()
    policy.update(brief.get("style_edit_policy", {}))
    return policy


def _resolve_narrator(article_brief: dict[str, Any] | None) -> str:
    if not article_brief:
        return "私たち"
    return str(article_brief.get("article_brief", {}).get("narrator", "私たち"))


def _rewrite_company_intro_page_summary_voice(
    sentence: str,
    article_brief: dict[str, Any] | None,
    narrator: str,
) -> str:
    if not _is_company_intro_self_viewpoint(article_brief) or "案内しています" not in sentence:
        return sentence
    stripped = sentence.rstrip()
    if narrator in stripped:
        for suffix in ("しているとも案内しています。", "すると案内しています。"):
            if stripped.endswith(suffix):
                return stripped.removesuffix(suffix) + "しています。"
    if stripped.endswith("と案内しています。"):
        return stripped.removesuffix("と案内しています。") + "という考え方です。"
    return sentence


def _is_company_intro_self_viewpoint(article_brief: dict[str, Any] | None) -> bool:
    if not article_brief:
        return False
    brief = article_brief.get("article_brief", {})
    return brief.get("genre_id") == "company_service_intro" and brief.get("viewpoint_mode") == "self_perspective"


def _flush_section(output: list[str], sentences: list[str], policy: dict[str, Any]) -> None:
    if not sentences:
        return
    revised = _vary_late_endings(sentences, policy)
    for group in _group_sentences(revised, policy):
        output.append("".join(group))
    sentences.clear()


def _group_sentences(sentences: list[str], policy: dict[str, Any]) -> list[list[str]]:
    preferred = max(1, int(policy.get("preferred_sentences_per_paragraph", 2)))
    maximum = max(preferred, int(policy.get("max_sentences_per_paragraph", 3)))
    groups: list[list[str]] = []
    index = 0
    while index < len(sentences):
        remaining = len(sentences) - index
        if remaining <= maximum:
            size = remaining
        elif len(groups) % 2 == 1 and remaining > preferred + 1:
            size = min(maximum, preferred + 1)
        else:
            size = preferred
        groups.append(sentences[index : index + size])
        index += size
    return groups


def _omit_repeated_narrator(
    sentence: str,
    narrator: str,
    narrator_is_clear: bool,
    policy: dict[str, Any],
) -> str:
    if policy.get("subject_omission_policy") != "clear_context_only":
        return sentence
    if not narrator_is_clear or _has_protected_subject_fact(sentence, policy):
        return sentence
    for prefix in (f"{narrator}は、", f"{narrator}は"):
        if sentence.startswith(prefix):
            return sentence[len(prefix) :].lstrip("、")
    return sentence


def _vary_late_endings(sentences: list[str], policy: dict[str, Any]) -> list[str]:
    if policy.get("ending_bucket_policy") not in ENDING_VARIATION_POLICIES:
        return list(sentences)
    if len(sentences) == 2:
        if ending_bucket(sentences[0]) == ending_bucket(sentences[1]) == "ます":
            revised = list(sentences)
            revised[1] = _convert_masu_sentence(revised[1])
            return revised
        return list(sentences)
    if len(sentences) < 3:
        return list(sentences)

    revised = list(sentences)
    half = len(sentences) // 2
    late_buckets = [ending_bucket(sentence) for sentence in sentences[half:]]
    if not late_buckets or late_buckets.count("ます") / len(late_buckets) < 0.75:
        return revised

    converted = 0
    for index in range(half, len(revised)):
        if converted >= 2:
            break
        if ending_bucket(revised[index]) != "ます" or _has_protected_subject_fact(revised[index], policy):
            continue
        candidate = _convert_masu_sentence(revised[index])
        if candidate != revised[index]:
            revised[index] = candidate
            converted += 1
    return revised


def _convert_masu_sentence(sentence: str) -> str:
    stripped = sentence.rstrip()
    if stripped.endswith("考える必要があると説明されています。"):
        return stripped.removesuffix("考える必要があると説明されています。") + "考える必要があります。"
    if stripped.endswith("として説明されています。"):
        return stripped.removesuffix("として説明されています。") + "です。"
    if stripped.endswith("として紹介されています。"):
        return stripped.removesuffix("として紹介されています。") + "です。"
    if stripped.endswith("と整理されています。"):
        return stripped.removesuffix("と整理されています。") + "という整理です。"
    if stripped.endswith("流れが示されています。"):
        return stripped.removesuffix("流れが示されています。") + "流れとしての整理です。"
    if stripped.endswith("考える必要があります。"):
        return stripped.removesuffix("考える必要があります。") + "考える必要があるという見方です。"
    if stripped.endswith("取得しています。"):
        return stripped.removesuffix("取得しています。") + "取得済みです。"
    if stripped.endswith("認定されています。"):
        return stripped.removesuffix("認定されています。") + "認定済みです。"
    passive_state = re.match(r"^(.*)(され|置かれ|示され|掲載され|案内され)ています。$", stripped)
    if passive_state:
        return f"{passive_state.group(1)}{passive_state.group(2)}ている内容です。"
    if stripped.endswith("しやすくなります。"):
        return stripped.removesuffix("しやすくなります。") + "しやすい形です。"
    if stripped.endswith("やすくなります。"):
        return stripped.removesuffix("やすくなります。") + "やすい形です。"
    if stripped.endswith("伝わります。"):
        return stripped.removesuffix("伝わります。") + "伝わる部分です。"
    if stripped.endswith("並びます。"):
        return stripped.removesuffix("並びます。") + "並ぶ構成です。"
    if stripped.endswith("しています。"):
        return stripped
    if stripped.endswith("できます。"):
        return stripped[:-5] + "できる内容です。"
    if stripped.endswith("します。"):
        return stripped
    match = re.match(r"^(.*[えけげせぜてでねへべめれ])ます。$", stripped)
    if match:
        return stripped
    return sentence


def _starts_with_narrator(sentence: str, narrator: str) -> bool:
    return sentence.startswith(f"{narrator}は") or sentence.startswith(f"{narrator}が")


def _has_protected_subject_fact(sentence: str, policy: dict[str, Any]) -> bool:
    if re.search(r"[0-9０-９]", sentence):
        return True
    return any(term in sentence for term in policy.get("protected_subject_terms", []))
