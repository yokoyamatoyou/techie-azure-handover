"""命題密度 / 文カウント関連の pure helper を集約する sibling module。

`note_writer_app.py` から切り出した純粋関数のみを置く。NiceGUI / AppState / pipeline には依存しない。
`note_writer_app.py` 側は re-export してテスト (`app_mod._foo`) 互換を保つ。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from note.note_text_format_helpers import _safe_round_float


_PROPOSITION_LOW_SIGNAL_PATTERN = re.compile(
    r"(?:"
    r"重要(?:です|だ)|"
    r"大切(?:です|だ)|"
    r"必要(?:です|だ)|"
    r"求められ(?:ます|る)|"
    r"期待できます|"
    r"と言(?:え|える)(?:ます|でしょう)?|"
    r"かもしれません|"
    r"ではないでしょうか|"
    r"と考えます|"
    r"につながります|"
    r"ことができます|"
    r"が挙げられます|"
    r"がポイントです"
    r")"
)
_PROPOSITION_CONCRETE_SIGNAL_PATTERN = re.compile(
    r"(?:"
    r"\d|%|％|年|月|日|時|分|秒|円|人|社|件|回|"
    r"「|」|『|』|https?://|"
    r"追加|更新|公開|開始|終了|廃止|改善|変更|対応|提供|導入|移行|修正|発表|告知"
    r")"
)
_PROPOSITION_TOKEN_PATTERN = re.compile(r"[一-龥]{2,}|[ァ-ヴー]{3,}|[A-Za-z]{3,}")
_PROPOSITION_STOP_TOKENS = {
    "こと",
    "もの",
    "ため",
    "よう",
    "それ",
    "これ",
    "今回",
    "記事",
    "内容",
    "情報",
    "視点",
    "読者",
    "自分",
    "相手",
    "必要",
    "重要",
    "可能",
    "状況",
    "場合",
}


def _count_sentences(text: str) -> int:
    source = (text or "").strip()
    if not source:
        return 0
    return len([s for s in re.split(r"(?<=[。！？])\s*", source) if s.strip()])


def _build_proposition_density_target_text(result: Dict[str, Any]) -> str:
    lead = str(result.get("lead", "") or "").strip()
    body = str(result.get("body", "") or "").strip()
    if lead or body:
        return "\n\n".join(part for part in (lead, body) if part)
    return str(result.get("full_text", "") or "").strip()


def _extract_proposition_sentences(text: str) -> List[str]:
    source = (text or "").strip()
    if not source:
        return []

    kept_lines: List[str] = []
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if re.match(r"^(?:[-*]|[0-9]+[.)])\s+", line):
            line = re.sub(r"^(?:[-*]|[0-9]+[.)])\s+", "", line, count=1).strip()
        if not line:
            continue
        kept_lines.append(line)
    if not kept_lines:
        return []

    merged = " ".join(kept_lines).strip()
    if not merged:
        return []

    raw_sentences = [s.strip() for s in re.split(r"(?<=[。！？!?])\s*", merged) if s.strip()]
    if not raw_sentences:
        raw_sentences = [merged]
    return raw_sentences


def _count_proposition_content_terms(sentence: str) -> int:
    tokens = []
    for token in _PROPOSITION_TOKEN_PATTERN.findall(sentence or ""):
        normalized = token.strip().lower()
        if not normalized:
            continue
        if normalized in _PROPOSITION_STOP_TOKENS:
            continue
        tokens.append(normalized)
    return len(set(tokens))


def _classify_proposition_sentence(sentence: str) -> str:
    normalized = re.sub(r"\s+", "", str(sentence or ""))
    if not normalized:
        return "skip"

    length = len(normalized)
    concrete_signal = bool(_PROPOSITION_CONCRETE_SIGNAL_PATTERN.search(normalized))
    low_signal = bool(_PROPOSITION_LOW_SIGNAL_PATTERN.search(normalized))
    content_terms = _count_proposition_content_terms(normalized)

    if concrete_signal:
        return "informative"
    if content_terms >= 3 and length >= 22:
        return "informative"
    if low_signal and content_terms <= 2:
        return "low"
    if content_terms <= 1 and length < 30:
        return "low"
    if length <= 10:
        return "low"
    if content_terms >= 2 and length >= 16:
        return "medium"
    return "low"


def _analyze_proposition_density(text: str) -> Dict[str, Any]:
    sentences = _extract_proposition_sentences(text)
    if not sentences:
        return {
            "sentence_count": 0,
            "informative_count": 0,
            "medium_count": 0,
            "low_info_count": 0,
            "informative_ratio": 0.0,
            "low_info_ratio": 0.0,
            "low_info_examples": [],
        }

    informative_count = 0
    medium_count = 0
    low_info_count = 0
    low_info_examples: List[str] = []
    for sentence in sentences:
        label = _classify_proposition_sentence(sentence)
        if label == "informative":
            informative_count += 1
        elif label == "medium":
            medium_count += 1
        elif label == "low":
            low_info_count += 1
            if len(low_info_examples) < 4:
                low_info_examples.append(sentence[:96])

    sentence_count = len(sentences)
    return {
        "sentence_count": sentence_count,
        "informative_count": informative_count,
        "medium_count": medium_count,
        "low_info_count": low_info_count,
        "informative_ratio": _safe_round_float(
            informative_count / max(1, sentence_count),
            4,
            0.0,
        ),
        "low_info_ratio": _safe_round_float(
            low_info_count / max(1, sentence_count),
            4,
            0.0,
        ),
        "low_info_examples": low_info_examples,
    }
