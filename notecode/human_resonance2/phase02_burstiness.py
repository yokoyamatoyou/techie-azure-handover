"""Phase 02 burstiness checks and minimal rhythm adjustments."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import re
from typing import Dict, List, Optional, Sequence, Tuple


TERMINAL_PUNCT = "。！？!?"
SPLIT_HINT_PATTERN = re.compile(r"[、,;；:：]")
LIST_LINE_PATTERN = re.compile(r"^\s*(?:[-*+]|[0-9]+[.)]|[・●◦▪])\s+")
JP_PATTERN = re.compile(r"[ぁ-んァ-ヶ一-龯]")
JP_NOUN_LIKE_ENDING_PATTERN = re.compile(r"[一-龯ァ-ヶA-Za-z0-9]$")
UNSAFE_SPLIT_LEFT_SUFFIXES = (
    "ではなく",
    "あり",
    "で",
    "が",
    "は",
    "と",
    "や",
    "も",
    "より",
    "ほうが",
    "方が",
    "たり",
    "のか",
    "なら",
    "ても",
    "やすく",
    "にくく",
    "づらく",
)


@dataclass(frozen=True)
class SentenceLengthStat:
    paragraph_index: int
    sentence_index: int
    length: int


@dataclass(frozen=True)
class ParagraphLengthStat:
    paragraph_index: int
    sentence_count: int
    mean_length: float
    std_length: float
    cv: float
    zone: str
    is_heading: bool
    is_list: bool


@dataclass(frozen=True)
class RhythmAdjustment:
    action: str
    paragraph_index: int
    sentence_index: int
    target_sentence_index: Optional[int]
    reason: str


@dataclass
class BurstinessResult:
    burstiness_score: float
    sentence_profile: List[SentenceLengthStat] = field(default_factory=list)
    paragraph_profile: List[ParagraphLengthStat] = field(default_factory=list)
    rhythm_adjustments: List[RhythmAdjustment] = field(default_factory=list)
    adjustment_cap: int = 0


@dataclass(frozen=True)
class _ParagraphBlock:
    index: int
    text: str
    is_heading: bool
    is_list: bool


class Phase02Burstiness:
    """Detect rhythm monotony and suggest capped split/merge adjustments."""

    MIN_SENTENCES_FOR_ADJUSTMENT = 4
    MIN_SPLIT_LENGTH = 26
    MIN_SEGMENT_LENGTH = 10
    SHORT_SENTENCE_MERGE_MAX = 20
    MERGE_COMBINED_MAX = 90

    def __init__(
        self,
        burstiness_target_min: float = 0.18,
        burstiness_target_max: float = 0.52,
        max_sentence_split_ratio: float = 0.12,
    ) -> None:
        min_value = max(0.0, min(1.0, float(burstiness_target_min)))
        max_value = max(0.0, min(1.0, float(burstiness_target_max)))
        self.burstiness_target_min = min(min_value, max_value)
        self.burstiness_target_max = max(min_value, max_value)
        self.max_sentence_split_ratio = max(0.0, min(1.0, float(max_sentence_split_ratio)))

    def analyze(self, text: str) -> BurstinessResult:
        if not text:
            return BurstinessResult(burstiness_score=0.0)

        blocks = self._split_blocks(text)
        sentence_profile: List[SentenceLengthStat] = []
        paragraph_profile: List[ParagraphLengthStat] = []
        sentence_lengths_by_paragraph: Dict[int, List[int]] = {}

        for block in blocks:
            if block.is_heading or block.is_list:
                paragraph_profile.append(
                    ParagraphLengthStat(
                        paragraph_index=block.index,
                        sentence_count=0,
                        mean_length=0.0,
                        std_length=0.0,
                        cv=0.0,
                        zone="heading" if block.is_heading else "list",
                        is_heading=block.is_heading,
                        is_list=block.is_list,
                    )
                )
                continue

            sentences = self._split_sentences(block.text)
            lengths: List[int] = []
            for sentence_index, sentence in enumerate(sentences, start=1):
                length = self._sentence_length(sentence)
                if length <= 0:
                    continue
                lengths.append(length)
                sentence_profile.append(
                    SentenceLengthStat(
                        paragraph_index=block.index,
                        sentence_index=sentence_index,
                        length=length,
                    )
                )

            sentence_lengths_by_paragraph[block.index] = lengths
            mean_length, std_length, cv = self._distribution(lengths)
            paragraph_profile.append(
                ParagraphLengthStat(
                    paragraph_index=block.index,
                    sentence_count=len(lengths),
                    mean_length=mean_length,
                    std_length=std_length,
                    cv=cv,
                    zone=self._classify_zone(cv, len(lengths)),
                    is_heading=False,
                    is_list=False,
                )
            )

        burstiness_score = self._weighted_cv(paragraph_profile)
        total_sentences = sum(
            profile.sentence_count
            for profile in paragraph_profile
            if not profile.is_heading and not profile.is_list
        )
        adjustment_cap = self._adjustment_cap(total_sentences)
        rhythm_adjustments = self._build_adjustments(
            blocks=blocks,
            paragraph_profile=paragraph_profile,
            sentence_lengths_by_paragraph=sentence_lengths_by_paragraph,
            adjustment_cap=adjustment_cap,
        )

        return BurstinessResult(
            burstiness_score=burstiness_score,
            sentence_profile=sentence_profile,
            paragraph_profile=paragraph_profile,
            rhythm_adjustments=rhythm_adjustments,
            adjustment_cap=adjustment_cap,
        )

    def apply_minimal_adjustments(
        self,
        text: str,
        adjustments: Sequence[RhythmAdjustment],
    ) -> Tuple[str, float, List[RhythmAdjustment]]:
        if not text or not adjustments:
            return text, 0.0, []

        blocks = self._split_blocks(text)
        total_sentences = sum(
            len(self._split_sentences(block.text))
            for block in blocks
            if not block.is_heading and not block.is_list
        )
        adjustment_cap = self._adjustment_cap(total_sentences)
        if adjustment_cap <= 0:
            return text, 0.0, []

        block_map: Dict[int, _ParagraphBlock] = {block.index: block for block in blocks}
        updated_texts: Dict[int, str] = {}
        applied: List[RhythmAdjustment] = []

        for adjustment in adjustments:
            if len(applied) >= adjustment_cap:
                break

            block = block_map.get(adjustment.paragraph_index)
            if block is None or block.is_heading or block.is_list:
                continue

            current_text = updated_texts.get(block.index, block.text)
            sentences = self._split_sentences(current_text)
            if not sentences:
                continue

            changed = False
            if adjustment.action == "split":
                split_index = adjustment.sentence_index - 1
                if 0 <= split_index < len(sentences):
                    split_result = self._split_sentence_once(sentences[split_index])
                    if split_result is not None:
                        sentences = (
                            sentences[:split_index]
                            + [split_result[0], split_result[1]]
                            + sentences[split_index + 1 :]
                        )
                        changed = True
            elif adjustment.action == "merge":
                first_index = adjustment.sentence_index - 1
                second_index = (
                    (adjustment.target_sentence_index - 1)
                    if adjustment.target_sentence_index is not None
                    else first_index + 1
                )
                if (
                    0 <= first_index < len(sentences)
                    and 0 <= second_index < len(sentences)
                    and second_index == first_index + 1
                ):
                    merged = self._merge_sentence_pair(sentences[first_index], sentences[second_index])
                    sentences = sentences[:first_index] + [merged] + sentences[second_index + 1 :]
                    changed = True

            if not changed:
                continue

            updated_texts[block.index] = self._compose_paragraph(sentences, current_text)
            applied.append(adjustment)

        rebuilt: List[str] = []
        for block in blocks:
            rebuilt.append(updated_texts.get(block.index, block.text))
        rewritten_text = "\n\n".join(segment for segment in rebuilt if segment.strip())
        adjustment_ratio = round(len(applied) / max(1, total_sentences), 4)
        return rewritten_text, adjustment_ratio, applied

    def _split_blocks(self, text: str) -> List[_ParagraphBlock]:
        chunks = [chunk.strip() for chunk in re.split(r"\n{2,}", text or "") if chunk.strip()]
        blocks: List[_ParagraphBlock] = []
        for index, chunk in enumerate(chunks, start=1):
            blocks.append(
                _ParagraphBlock(
                    index=index,
                    text=chunk,
                    is_heading=self._is_heading_block(chunk),
                    is_list=self._is_list_block(chunk),
                )
            )
        return blocks

    def _is_heading_block(self, block_text: str) -> bool:
        line = block_text.strip().splitlines()[0] if block_text.strip() else ""
        return bool(line.lstrip().startswith("#"))

    def _is_list_block(self, block_text: str) -> bool:
        lines = [line.strip() for line in block_text.splitlines() if line.strip()]
        if not lines:
            return False
        return all(bool(LIST_LINE_PATTERN.match(line)) for line in lines)

    def _split_sentences(self, text: str) -> List[str]:
        if not text:
            return []
        fragments = re.split(r"(?<=[。！？!?])\s*|(?<=\.)\s+(?=[A-Za-z0-9])|\n+", text.strip())
        return [fragment.strip() for fragment in fragments if fragment and fragment.strip()]

    def _sentence_length(self, sentence: str) -> int:
        return len(re.sub(r"\s+", "", sentence or ""))

    def _distribution(self, lengths: Sequence[int]) -> Tuple[float, float, float]:
        if not lengths:
            return 0.0, 0.0, 0.0
        mean_length = sum(lengths) / len(lengths)
        variance = sum((value - mean_length) ** 2 for value in lengths) / len(lengths)
        std_length = math.sqrt(variance)
        cv = std_length / mean_length if mean_length > 0 else 0.0
        return round(mean_length, 4), round(std_length, 4), round(min(1.0, cv), 4)

    def _classify_zone(self, cv: float, sentence_count: int) -> str:
        if sentence_count < 2:
            return "insufficient"
        if cv < self.burstiness_target_min:
            return "uniform"
        if cv > self.burstiness_target_max:
            return "fragmented"
        return "natural"

    def _weighted_cv(self, paragraph_profile: Sequence[ParagraphLengthStat]) -> float:
        weighted_sum = 0.0
        weight_total = 0
        for profile in paragraph_profile:
            if profile.is_heading or profile.is_list:
                continue
            if profile.sentence_count < 2:
                continue
            weighted_sum += profile.cv * profile.sentence_count
            weight_total += profile.sentence_count
        if weight_total <= 0:
            return 0.0
        return round(max(0.0, min(1.0, weighted_sum / weight_total)), 4)

    def _adjustment_cap(self, sentence_count: int) -> int:
        if sentence_count <= 0:
            return 0
        cap = int(sentence_count * self.max_sentence_split_ratio)
        if cap == 0 and self.max_sentence_split_ratio > 0 and sentence_count >= 3:
            cap = 1
        return max(0, min(sentence_count, cap))

    def _build_adjustments(
        self,
        blocks: Sequence[_ParagraphBlock],
        paragraph_profile: Sequence[ParagraphLengthStat],
        sentence_lengths_by_paragraph: Dict[int, List[int]],
        adjustment_cap: int,
    ) -> List[RhythmAdjustment]:
        if adjustment_cap <= 0:
            return []

        block_map = {block.index: block for block in blocks}
        sortable: List[Tuple[float, ParagraphLengthStat]] = []
        for profile in paragraph_profile:
            deviation = self._zone_deviation(profile)
            if deviation <= 0:
                continue
            sortable.append((deviation, profile))
        sortable.sort(key=lambda item: (-item[0], item[1].paragraph_index))

        adjustments: List[RhythmAdjustment] = []
        for _, profile in sortable:
            if len(adjustments) >= adjustment_cap:
                break
            if profile.sentence_count < self.MIN_SENTENCES_FOR_ADJUSTMENT:
                continue

            block = block_map.get(profile.paragraph_index)
            if block is None:
                continue
            if block.is_heading or block.is_list:
                continue

            lengths = sentence_lengths_by_paragraph.get(profile.paragraph_index, [])
            sentences = self._split_sentences(block.text)
            if not sentences or not lengths:
                continue

            if profile.zone == "uniform":
                split_index = self._find_split_candidate(sentences, lengths)
                if split_index is None:
                    continue
                adjustments.append(
                    RhythmAdjustment(
                        action="split",
                        paragraph_index=profile.paragraph_index,
                        sentence_index=split_index + 1,
                        target_sentence_index=None,
                        reason=(
                            f"paragraph {profile.paragraph_index} has low burstiness "
                            f"(cv={profile.cv} < {self.burstiness_target_min})"
                        ),
                    )
                )
            elif profile.zone == "fragmented":
                merge_pair = self._find_merge_candidate(lengths)
                if merge_pair is None:
                    continue
                adjustments.append(
                    RhythmAdjustment(
                        action="merge",
                        paragraph_index=profile.paragraph_index,
                        sentence_index=merge_pair[0] + 1,
                        target_sentence_index=merge_pair[1] + 1,
                        reason=(
                            f"paragraph {profile.paragraph_index} has high burstiness "
                            f"(cv={profile.cv} > {self.burstiness_target_max})"
                        ),
                    )
                )

        return adjustments[:adjustment_cap]

    def _zone_deviation(self, profile: ParagraphLengthStat) -> float:
        if profile.zone == "uniform":
            return round(self.burstiness_target_min - profile.cv, 6)
        if profile.zone == "fragmented":
            return round(profile.cv - self.burstiness_target_max, 6)
        return 0.0

    def _find_split_candidate(self, sentences: Sequence[str], lengths: Sequence[int]) -> Optional[int]:
        pairs = sorted(enumerate(lengths), key=lambda item: (-item[1], item[0]))
        for index, length in pairs:
            if length < self.MIN_SPLIT_LENGTH:
                continue
            split_index = self._find_split_index(sentences[index])
            if split_index is None:
                continue
            return index
        return None

    def _find_merge_candidate(self, lengths: Sequence[int]) -> Optional[Tuple[int, int]]:
        best_pair: Optional[Tuple[int, int]] = None
        best_combined = 10**9
        for idx in range(len(lengths) - 1):
            first = lengths[idx]
            second = lengths[idx + 1]
            combined = first + second
            if max(first, second) > self.SHORT_SENTENCE_MERGE_MAX:
                continue
            if combined > self.MERGE_COMBINED_MAX:
                continue
            if combined < best_combined:
                best_combined = combined
                best_pair = (idx, idx + 1)
        return best_pair

    def _split_sentence_once(self, sentence: str) -> Optional[Tuple[str, str]]:
        normalized = (sentence or "").strip()
        if self._sentence_length(normalized) < self.MIN_SPLIT_LENGTH:
            return None

        terminal = ""
        core = normalized
        if core and core[-1] in TERMINAL_PUNCT:
            terminal = core[-1]
            core = core[:-1].strip()

        split_index = self._find_split_index(core)
        if split_index is None:
            return None

        left = core[:split_index].strip(" 、,;；:：")
        right = core[split_index:].strip(" 、,;；:：")
        if not self._is_valid_split_parts(left, right, core):
            return None

        suffix = terminal or self._default_terminal(core)
        if left and left[-1] not in TERMINAL_PUNCT:
            left = f"{left}{suffix}"
        if right and right[-1] not in TERMINAL_PUNCT:
            right = f"{right}{suffix}"
        return left, right

    def _find_split_index(self, sentence: str) -> Optional[int]:
        content = (sentence or "").strip()
        if not content:
            return None

        target = len(content) // 2
        punct_candidates = [match.start() + 1 for match in SPLIT_HINT_PATTERN.finditer(content)]
        for index in sorted(punct_candidates, key=lambda value: abs(value - target)):
            left = content[:index]
            right = content[index:]
            if self._is_valid_split_parts(left, right, content):
                return index

        space_candidates = [match.start() + 1 for match in re.finditer(r"\s+", content)]
        for index in sorted(space_candidates, key=lambda value: abs(value - target)):
            left = content[:index]
            right = content[index:]
            if self._is_valid_split_parts(left, right, content):
                return index
        return None

    def _is_valid_split_parts(self, left: str, right: str, source: str) -> bool:
        left_core = (left or "").strip(" 、,;；:：")
        right_core = (right or "").strip(" 、,;；:：")
        if self._sentence_length(left_core) < self.MIN_SEGMENT_LENGTH:
            return False
        if self._sentence_length(right_core) < self.MIN_SEGMENT_LENGTH:
            return False
        if self._has_unsafe_split_left_suffix(left_core, source):
            return False
        if self._has_bare_noun_like_ending(left_core, source):
            return False
        return True

    def _has_unsafe_split_left_suffix(self, left: str, source: str) -> bool:
        left_core = (left or "").strip()
        if not left_core:
            return False
        if not self._contains_japanese(source):
            return False
        return any(left_core.endswith(suffix) for suffix in UNSAFE_SPLIT_LEFT_SUFFIXES)

    def _has_bare_noun_like_ending(self, left: str, source: str) -> bool:
        left_core = (left or "").strip()
        if not left_core:
            return False
        if not self._contains_japanese(source):
            return False
        return bool(JP_NOUN_LIKE_ENDING_PATTERN.search(left_core))

    def _merge_sentence_pair(self, first: str, second: str) -> str:
        left = (first or "").strip()
        right = (second or "").strip()
        if not left:
            return right
        if not right:
            return left

        left_core = re.sub(r"[。！？!?]+$", "", left).strip()
        right_core = right
        right_terminal = right_core[-1] if right_core and right_core[-1] in TERMINAL_PUNCT else ""
        if right_terminal:
            right_core = right_core[:-1].strip()

        connector = "、" if self._contains_japanese(left_core + right_core) else ", "
        merged = f"{left_core}{connector}{right_core}".strip()
        suffix = right_terminal or self._default_terminal(merged)
        if merged and merged[-1] not in TERMINAL_PUNCT:
            merged = f"{merged}{suffix}"
        return merged

    def _compose_paragraph(self, sentences: Sequence[str], original_text: str) -> str:
        cleaned = [sentence.strip() for sentence in sentences if sentence and sentence.strip()]
        if not cleaned:
            return original_text.strip()
        if self._contains_japanese(original_text):
            return "".join(cleaned)
        return " ".join(cleaned)

    def _default_terminal(self, text: str) -> str:
        return "。" if self._contains_japanese(text) else "."

    def _contains_japanese(self, text: str) -> bool:
        return bool(JP_PATTERN.search(text or ""))
