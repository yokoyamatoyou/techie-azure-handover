"""Phase 01 lexical diversity checks and minimal rewrite planning."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import logging
import re
import unicodedata
from typing import Dict, List, Optional, Sequence, Tuple

try:
    from sudachipy import dictionary as sudachi_dictionary
    from sudachipy import tokenizer as sudachi_tokenizer

    SUDACHI_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    sudachi_dictionary = None
    sudachi_tokenizer = None
    SUDACHI_AVAILABLE = False


logger = logging.getLogger(__name__)

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+|[一-龯]+|[ぁ-ん]+|[ァ-ヶー]+")

STOP_TOKENS = {
    "の",
    "に",
    "は",
    "を",
    "が",
    "と",
    "で",
    "も",
    "へ",
    "や",
    "です",
    "ます",
    "した",
    "して",
    "する",
    "いる",
    "ある",
    "こと",
    "ため",
    "this",
    "that",
    "with",
    "from",
    "into",
}

DEFAULT_REPLACEMENTS: Dict[str, Tuple[str, ...]] = {
    "重要": ("大切", "鍵になる点"),
    "必要": ("欠かせない", "求められる"),
    "説明": ("解説", "紹介"),
    "改善": ("見直し", "向上"),
    "効果": ("変化", "手応え"),
    "活用": ("利用", "運用"),
    "非常": ("かなり", "とても"),
    "具体": ("明確", "実例ベース"),
    "価値": ("意義", "メリット"),
}


@dataclass(frozen=True)
class RepetitionSignal:
    token: str
    scope: str
    paragraph_index: int
    sentence_index: Optional[int]
    occurrences: int


@dataclass(frozen=True)
class RewriteSuggestion:
    token: str
    paragraph_index: int
    sentence_index: Optional[int]
    replacement_options: Tuple[str, ...]
    reason: str


@dataclass
class LexicalDiversityResult:
    lexical_diversity_score: float
    repetition_signals: List[RepetitionSignal] = field(default_factory=list)
    rewrite_suggestions: List[RewriteSuggestion] = field(default_factory=list)
    rewrite_cap: int = 0
    tokenization_method: str = "regex"


@dataclass(frozen=True)
class _ParagraphBlock:
    index: int
    text: str
    is_heading: bool


class Phase01LexicalDiversity:
    """Detect lexical repetition and provide capped minimal rewrite suggestions."""

    def __init__(
        self,
        lexical_threshold: float = 0.32,
        max_rewrite_ratio: float = 0.15,
        tokenizer_mode: str = "auto",
    ) -> None:
        self.lexical_threshold = max(0.0, min(1.0, float(lexical_threshold)))
        self.max_rewrite_ratio = max(0.0, min(1.0, float(max_rewrite_ratio)))
        self.tokenizer_mode = self._normalize_tokenizer_mode(tokenizer_mode)
        self._sudachi = None
        self._sudachi_mode = None
        self._sudachi_ready = False
        if self.tokenizer_mode in ("auto", "sudachi"):
            self._init_sudachi()

    def analyze(self, text: str) -> LexicalDiversityResult:
        if not text:
            return LexicalDiversityResult(lexical_diversity_score=1.0)

        tokenization_method = self._resolve_tokenization_method()
        blocks = self._split_blocks(text)
        all_tokens: List[str] = []
        signals: List[RepetitionSignal] = []

        for block in blocks:
            if block.is_heading:
                continue

            paragraph_tokens = self._tokenize(block.text, method=tokenization_method)
            all_tokens.extend(paragraph_tokens)
            paragraph_counter = Counter(paragraph_tokens)

            for token, count in paragraph_counter.items():
                if count >= 3:
                    signals.append(
                        RepetitionSignal(
                            token=token,
                            scope="paragraph",
                            paragraph_index=block.index,
                            sentence_index=None,
                            occurrences=count,
                        )
                    )

            for sentence_index, sentence in enumerate(self._split_sentences(block.text), start=1):
                sentence_tokens = self._tokenize(sentence, method=tokenization_method)
                if len(sentence_tokens) < 4:
                    continue
                sentence_counter = Counter(sentence_tokens)
                for token, count in sentence_counter.items():
                    if count >= 2:
                        signals.append(
                            RepetitionSignal(
                                token=token,
                                scope="sentence",
                                paragraph_index=block.index,
                                sentence_index=sentence_index,
                                occurrences=count,
                            )
                        )

        deduped_signals = self._dedupe_signals(signals)
        score = self._calculate_score(all_tokens, deduped_signals)
        rewrite_cap = self._rewrite_cap(len(all_tokens))
        suggestions = self._build_suggestions(deduped_signals, rewrite_cap)

        return LexicalDiversityResult(
            lexical_diversity_score=score,
            repetition_signals=deduped_signals,
            rewrite_suggestions=suggestions,
            rewrite_cap=rewrite_cap,
            tokenization_method=tokenization_method,
        )

    def apply_minimal_rewrites(
        self,
        text: str,
        suggestions: Sequence[RewriteSuggestion],
    ) -> Tuple[str, float]:
        if not text or not suggestions:
            return text, 0.0

        tokenization_method = self._resolve_tokenization_method()
        blocks = self._split_blocks(text)
        content_tokens = sum(
            len(self._tokenize(block.text, method=tokenization_method))
            for block in blocks
            if not block.is_heading
        )
        rewrite_cap = self._rewrite_cap(content_tokens)
        if rewrite_cap <= 0:
            return text, 0.0

        block_texts: Dict[int, str] = {block.index: block.text for block in blocks}
        changes = 0

        for suggestion in suggestions:
            if changes >= rewrite_cap:
                break

            current = block_texts.get(suggestion.paragraph_index)
            if not current:
                continue
            if self._is_heading_block(current):
                continue

            replacement = suggestion.replacement_options[0] if suggestion.replacement_options else ""
            if not replacement:
                continue

            updated, changed = self._replace_second_occurrence(current, suggestion.token, replacement)
            if not changed:
                continue

            block_texts[suggestion.paragraph_index] = updated
            changes += 1

        rebuilt: List[str] = []
        for block in blocks:
            rebuilt.append(block_texts.get(block.index, block.text))
        rewritten_text = "\n\n".join(segment for segment in rebuilt if segment.strip())
        rewrite_ratio = round(changes / max(1, content_tokens), 4)
        return rewritten_text, rewrite_ratio

    def _calculate_score(self, tokens: Sequence[str], signals: Sequence[RepetitionSignal]) -> float:
        if not tokens:
            return 1.0

        counter = Counter(tokens)
        total = len(tokens)
        unique_ratio = len(counter) / total
        dominant_ratio = max(counter.values()) / total
        length_factor = min(1.0, total / 100.0)

        signal_weight = sum(max(0, item.occurrences - 1) for item in signals)
        repetition_penalty = min(0.45, signal_weight / max(1, total))

        score = (unique_ratio * 0.78 + (1.0 - dominant_ratio) * 0.22) * (0.65 + 0.35 * length_factor)
        score = score - repetition_penalty
        return round(max(0.0, min(1.0, score)), 4)

    def _build_suggestions(
        self,
        signals: Sequence[RepetitionSignal],
        rewrite_cap: int,
    ) -> List[RewriteSuggestion]:
        if rewrite_cap <= 0:
            return []

        suggestions: List[RewriteSuggestion] = []
        seen: set[Tuple[str, int, Optional[int], str]] = set()

        for signal in self._sort_signals(signals):
            if len(suggestions) >= rewrite_cap:
                break

            key = (signal.token, signal.paragraph_index, signal.sentence_index, signal.scope)
            if key in seen:
                continue
            seen.add(key)

            replacements = self._replacement_candidates(signal.token)
            reason = (
                f"{signal.scope} repetition at paragraph {signal.paragraph_index}"
                f"{'' if signal.sentence_index is None else f', sentence {signal.sentence_index}'}"
                f": token '{signal.token}' appears {signal.occurrences} times."
            )
            suggestions.append(
                RewriteSuggestion(
                    token=signal.token,
                    paragraph_index=signal.paragraph_index,
                    sentence_index=signal.sentence_index,
                    replacement_options=replacements,
                    reason=reason,
                )
            )

        return suggestions

    def _split_blocks(self, text: str) -> List[_ParagraphBlock]:
        chunks = [chunk.strip() for chunk in re.split(r"\n{2,}", text or "") if chunk.strip()]
        blocks: List[_ParagraphBlock] = []
        for index, chunk in enumerate(chunks, start=1):
            blocks.append(
                _ParagraphBlock(
                    index=index,
                    text=chunk,
                    is_heading=self._is_heading_block(chunk),
                )
            )
        return blocks

    def _is_heading_block(self, block_text: str) -> bool:
        line = block_text.strip().splitlines()[0] if block_text.strip() else ""
        return bool(line.lstrip().startswith("#"))

    def _split_sentences(self, text: str) -> List[str]:
        fragments = re.split(r"(?<=[。！？!?])\s+|\n+", text.strip())
        return [fragment.strip() for fragment in fragments if fragment.strip()]

    def _tokenize(self, text: str, method: Optional[str] = None) -> List[str]:
        mode = method or self._resolve_tokenization_method()
        if mode == "sudachi":
            tokens = self._tokenize_sudachi(text)
            if tokens:
                return tokens
        return self._tokenize_regex(text)

    def _tokenize_regex(self, text: str) -> List[str]:
        tokens: List[str] = []
        for raw in TOKEN_PATTERN.findall(text or ""):
            normalized = self._normalize_token(raw)
            if normalized:
                tokens.append(normalized)
        return tokens

    def _tokenize_sudachi(self, text: str) -> List[str]:
        if not self._sudachi_ready or not self._sudachi:
            return []
        tokens: List[str] = []
        try:
            morphemes = self._sudachi.tokenize(text or "", self._sudachi_mode)
            for morpheme in morphemes:
                pos = morpheme.part_of_speech()
                pos_major = pos[0] if pos else ""
                if pos_major in {"補助記号", "助詞", "助動詞", "空白"}:
                    continue
                surface = morpheme.surface()
                normalized = self._normalize_token(surface)
                if normalized:
                    tokens.append(normalized)
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.debug("Sudachi tokenization failed, fallback to regex.", exc_info=exc)
            return []
        return tokens

    def _normalize_token(self, token: str) -> str:
        normalized = unicodedata.normalize("NFKC", token).strip().lower()
        if not normalized:
            return ""
        if normalized.isdigit():
            return ""
        if len(normalized) <= 1:
            return ""
        if normalized in STOP_TOKENS:
            return ""
        return normalized

    def _replacement_candidates(self, token: str) -> Tuple[str, ...]:
        for key, replacements in DEFAULT_REPLACEMENTS.items():
            if key in token:
                return replacements
        # Unknown tokens should not be force-replaced with placeholders.
        return ()

    def _dedupe_signals(self, signals: Sequence[RepetitionSignal]) -> List[RepetitionSignal]:
        unique: Dict[Tuple[str, str, int, Optional[int]], RepetitionSignal] = {}
        for signal in signals:
            key = (signal.token, signal.scope, signal.paragraph_index, signal.sentence_index)
            existing = unique.get(key)
            if existing is None or signal.occurrences > existing.occurrences:
                unique[key] = signal
        return self._sort_signals(list(unique.values()))

    def _sort_signals(self, signals: Sequence[RepetitionSignal]) -> List[RepetitionSignal]:
        return sorted(
            signals,
            key=lambda item: (
                -item.occurrences,
                item.paragraph_index,
                item.sentence_index if item.sentence_index is not None else 0,
                item.token,
            ),
        )

    def _rewrite_cap(self, token_count: int) -> int:
        if token_count <= 0:
            return 0
        return int(token_count * self.max_rewrite_ratio)

    def _replace_second_occurrence(self, text: str, token: str, replacement: str) -> Tuple[str, bool]:
        matches = list(re.finditer(re.escape(token), text))
        if len(matches) < 2:
            return text, False
        target = matches[1]
        updated = text[: target.start()] + replacement + text[target.end() :]
        return updated, True

    def _init_sudachi(self) -> None:
        if not SUDACHI_AVAILABLE or sudachi_dictionary is None or sudachi_tokenizer is None:
            return
        try:
            self._sudachi = sudachi_dictionary.Dictionary().create()
            self._sudachi_mode = sudachi_tokenizer.Tokenizer.SplitMode.B
            self._sudachi_ready = True
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.debug("Sudachi initialization failed, fallback to regex.", exc_info=exc)
            self._sudachi = None
            self._sudachi_mode = None
            self._sudachi_ready = False

    def _resolve_tokenization_method(self) -> str:
        if self.tokenizer_mode == "regex":
            return "regex"
        if self.tokenizer_mode == "sudachi":
            return "sudachi" if self._sudachi_ready else "regex"
        return "sudachi" if self._sudachi_ready else "regex"

    def _normalize_tokenizer_mode(self, mode: str) -> str:
        candidate = (mode or "auto").strip().lower()
        if candidate in {"auto", "regex", "sudachi"}:
            return candidate
        return "auto"
