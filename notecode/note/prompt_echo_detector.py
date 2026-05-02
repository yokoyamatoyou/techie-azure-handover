"""Shared prompt-echo and instructional-fragment detection helpers."""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Iterable, List, Sequence

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")
_NORMALIZE_RE = re.compile(r"[、。．，,！!？?…・「」『』（）()［］\[\]【】<>\"'`〜ー\-\s]+")
_LABEL_STYLE_REFERENCE_RE = re.compile(
    r"(?:"
    r"の紹介|紹介|"
    r"の概要|概要|"
    r"について|とは|"
    r"の比較|比較|"
    r"事例|活用事例|"
    r"入門|ガイド|"
    r"まとめ"
    r")$"
)
_INSTRUCTION_REQUEST_RE = re.compile(
    r"(?:"
    r"して(?:ください|下さい)?|"
    r"してほしい|"
    r"してください|下さい|"
    r"教えて|知りたい|"
    r"含め(?:る|て)|"
    r"入れ(?:る|て)|"
    r"書い(?:て|た)|"
    r"作(?:る|成|って)|"
    r"生成(?:する|して)?|"
    r"お願いします|頼みます|"
    r"見出し|本文"
    r")"
)

_INSTRUCTIONAL_PATTERNS: Sequence[re.Pattern[str]] = tuple(
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in (
        r"【[^】]*(?:記事目的|内部ガイド|指示|ルール|プロンプト)[^】]*】",
        r"(?:ブログ|記事|本文|投稿|note投稿).{0,64}(?:作成|生成|執筆).{0,20}(?:して|してください|して下さい|する)",
        r"(?:ignore\s+previous\s+instructions|system\s+prompt)",
        r"(?:手順を分解して優先順位を決める|判断基準と確認項目を先に明文化|次の行動を具体化すると継続しやすくなる)",
        r"(?:自社(?:を)?知ってもらうことを目的として.{0,32}(?:作成|生成|執筆))",
        r"(?:を実際の場面に当てはめると、要点の使いどころが見えやすくなります)",
        r"(?:読み手が次の一歩を選びやすいよう|実行順を明確に(?:します|する)|"
        r"判断の根拠を(?:具体化|明確化)して伝え(?:ますね|ます|る)|"
        r"現場で再現しやすい形に整えることを意識(?:しますね|します|する)|"
        r"整えることを意識(?:します|する)|"
        r"まずはnote(?:にて|で).{0,24}(?:自己紹介|初投稿).{0,20}(?:効果的|有効)|"
        r"この段階で(?:重要|大切|鍵になる)(?:な)?のは.+判断基準として具体化すること)",
        r"(?:の観点で.{0,24}(?:整理|確認|検討|分析|解説)(?:します|する))",
        r"(?:要点を(?:短く)?(?:整理|確認)(?:します|する)|実務で迷いやすい場面を想定しながら)",
    )
)
_BROKEN_GRAMMAR_ECHO_RE = re.compile(r"(?:する|させる|あてる|当てる|向ける)(?:を|が|は|も)(?!の|ず)")


def _normalize(value: str) -> str:
    return _NORMALIZE_RE.sub("", value or "")


def _split_sentences(text: str) -> List[str]:
    return [seg.strip() for seg in _SENTENCE_SPLIT_RE.split(str(text or "")) if seg.strip()]


def _is_short_label_style_reference(reference: str) -> bool:
    text = str(reference or "").strip()
    compact = _normalize(text)
    if len(compact) < 8 or len(compact) > 24:
        return False
    if _split_sentences(text) != [text]:
        return False
    if any(ch in text for ch in "。！？!?"):
        return False
    if _INSTRUCTION_REQUEST_RE.search(text):
        return False
    return bool(_LABEL_STYLE_REFERENCE_RE.search(text))


def _has_reference_echo(
    sentence: str,
    references: Sequence[str],
    *,
    reference_coverage: float,
) -> bool:
    sent_norm = _normalize(sentence)
    if len(sent_norm) < 8:
        return False
    for ref in references:
        ref_norm = _normalize(ref)
        if len(ref_norm) < 8:
            continue
        if _is_short_label_style_reference(ref):
            continue
        if ref_norm in sent_norm:
            return True
        match = SequenceMatcher(None, ref_norm[:400], sent_norm[:400]).find_longest_match(
            0,
            min(len(ref_norm), 400),
            0,
            min(len(sent_norm), 400),
        )
        if len(ref_norm) > 0 and (match.size / len(ref_norm)) >= reference_coverage:
            return True
    return False


def _is_instructional_sentence(
    sentence: str,
    references: Sequence[str],
    *,
    reference_coverage: float,
) -> bool:
    if not sentence:
        return False
    if any(pattern.search(sentence) for pattern in _INSTRUCTIONAL_PATTERNS):
        return True
    if _BROKEN_GRAMMAR_ECHO_RE.search(sentence):
        return True
    return _has_reference_echo(
        sentence,
        references,
        reference_coverage=reference_coverage,
    )


def build_prompt_echo_references(
    *,
    must_cover: Iterable[Any] | None = None,
    user_prompt: str = "",
    extra: Iterable[Any] | None = None,
    min_len: int = 8,
    include_must_cover: bool = False,
) -> List[str]:
    refs: List[str] = []
    seen = set()

    def _append_raw(value: Any) -> None:
        text = str(value or "").strip()
        if not text:
            return
        candidates = [text]
        candidates.extend(_split_sentences(text))
        for candidate in candidates:
            compact = _normalize(candidate)
            if len(compact) < min_len:
                continue
            key = compact[:180]
            if key in seen:
                continue
            seen.add(key)
            refs.append(candidate.strip())

    if include_must_cover:
        for item in must_cover or []:
            _append_raw(item)
    if user_prompt:
        _append_raw(user_prompt)
    for item in extra or []:
        _append_raw(item)
    return refs


def detect_prompt_echo_sentences(
    text: str,
    *,
    references: Sequence[str] | None = None,
    max_hits: int = 5,
    reference_coverage: float = 0.8,
) -> List[str]:
    hits: List[str] = []
    refs = list(references or [])
    for sentence in _split_sentences(text):
        if not _is_instructional_sentence(
            sentence,
            refs,
            reference_coverage=reference_coverage,
        ):
            continue
        hits.append(sentence[:140])
        if len(hits) >= max_hits:
            break
    return hits


def contains_instructional_fragment(
    text: str,
    *,
    references: Sequence[str] | None = None,
    reference_coverage: float = 0.8,
) -> bool:
    return bool(
        detect_prompt_echo_sentences(
            text,
            references=references,
            max_hits=1,
            reference_coverage=reference_coverage,
        )
    )
