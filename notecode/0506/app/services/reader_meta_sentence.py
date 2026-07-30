from __future__ import annotations

import re


ISSUE_REASONS = {
    "reader_instruction_meta_commentary": "読者がどう理解するかを案内するだけで、ソース事実を増やしていません",
    "low_density_bridge_sentence": "橋渡し文が抽象的で、工程・体制・提供内容などの事実密度が不足しています",
    "abstract_navigation_phrase": "輪郭・入口・見えやすさなどの抽象ナビゲーション表現に寄っています",
}

_READER_OR_DELIVERY_MARKERS = (
    "知りたい方",
    "まず知りたい",
    "読者が",
    "読者に",
    "お伝えしたい",
    "紹介したい",
    "説明したい",
)
_ABSTRACT_NAVIGATION_MARKERS = (
    "輪郭",
    "手がかりになります",
    "見えやすくなります",
    "つながりが見え",
    "つかみやすくなります",
)
_ABSTRACT_NAVIGATION_PATTERNS = (
    r"入口(?:です|になります|となります)",
)
_LOW_DENSITY_BRIDGE_MARKERS = (
    "思い浮かべる",
    "目を向けると",
    "場面を想像",
    "場面を思い浮か",
    "理解しやすくなります",
    "追いやすくなります",
)
_FACTUAL_PREDICATE_MARKERS = (
    "提供しています",
    "納品しています",
    "対応しています",
    "支援しています",
    "行っています",
    "展開しています",
    "取得しています",
    "認定されています",
    "創業",
    "設立",
    "所在地",
)


def classify_reader_meta_sentence(sentence: str) -> list[str]:
    text = _normalize_sentence(sentence)
    if not text:
        return []
    issues: list[str] = []
    reader_meta = _is_reader_instruction_meta(text)
    low_density = _is_low_density_bridge(text)
    abstract_navigation = _has_abstract_navigation(text)
    if reader_meta:
        issues.append("reader_instruction_meta_commentary")
    if low_density:
        issues.append("low_density_bridge_sentence")
    if abstract_navigation and (reader_meta or low_density or not _has_factual_predicate(text)):
        issues.append("abstract_navigation_phrase")
    return issues


def is_reader_meta_sentence(sentence: str) -> bool:
    return bool(classify_reader_meta_sentence(sentence))


def _normalize_sentence(sentence: str) -> str:
    return re.sub(r"\s+", "", sentence.strip())


def _is_reader_instruction_meta(text: str) -> bool:
    return (
        any(marker in text for marker in _READER_OR_DELIVERY_MARKERS)
        and not _has_factual_predicate(text)
        and (_has_abstract_navigation(text) or "理解" in text)
    )


def _is_low_density_bridge(text: str) -> bool:
    if any(marker in text for marker in _LOW_DENSITY_BRIDGE_MARKERS):
        return not _has_factual_predicate(text) or _has_abstract_navigation(text)
    return _has_abstract_navigation(text) and not _has_factual_predicate(text)


def _has_abstract_navigation(text: str) -> bool:
    return any(marker in text for marker in _ABSTRACT_NAVIGATION_MARKERS) or any(
        re.search(pattern, text) for pattern in _ABSTRACT_NAVIGATION_PATTERNS
    )


def _has_factual_predicate(text: str) -> bool:
    if re.search(r"\d{2,4}年|[0-9０-９]+(?:件|社|名|円|ページ|％|%)", text):
        return True
    return any(marker in text for marker in _FACTUAL_PREDICATE_MARKERS)
