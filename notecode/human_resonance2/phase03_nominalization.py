"""Phase 03 nominalization checks and minimal verb-centered rewrites."""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional, Sequence, Tuple

try:
    from sudachipy import dictionary as sudachi_dictionary
    from sudachipy import tokenizer as sudachi_tokenizer

    SUDACHI_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    sudachi_dictionary = None
    sudachi_tokenizer = None
    SUDACHI_AVAILABLE = False


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+|[一-龯]+|[ぁ-ん]+|[ァ-ヶー]+")
JP_PATTERN = re.compile(r"[ぁ-んァ-ヶ一-龯]")
CASE_PARTICLES = {"の", "を", "が", "に", "へ", "で"}

NOMINAL_PATTERNS: Tuple[Tuple[str, re.Pattern[str], float], ...] = (
    ("noun_chain", re.compile(r"(?:実施|推進|検討|共有|改善|強化|最適化|管理|運用|導入|活用|実現|形成|評価|調整|連携|対応|提供)(?:の|を|が|に|へ|で)"), 1.0),
    ("ka_suffix", re.compile(r"[A-Za-z0-9一-龯ぁ-んァ-ヶー]+化(?:の|を|が|に|へ|で)"), 1.0),
    ("sei_suffix", re.compile(r"[A-Za-z0-9一-龯ぁ-んァ-ヶー]+性(?:の|を|が|に|へ|で)"), 0.8),
    ("niokeru", re.compile(r"における"), 0.7),
    ("kotoga", re.compile(r"こと(?:が|を|に|で)"), 0.25),
)

DOMAIN_TERMS: Tuple[str, ...] = (
    "安全性",
    "信頼性",
    "可用性",
    "互換性",
    "拡張性",
    "有効性",
    "再現性",
    "透明性",
    "個人情報保護",
    "品質管理",
    "在庫管理",
    "温度管理",
    "法令遵守",
)

REWRITE_RULES: Tuple[Tuple[str, str], ...] = (
    ("ことが可能です", "できます"),
    ("ことができます", "できます"),
    ("ことにより", "ことで"),
    ("における", "での"),
    ("の実施", "を実施する"),
    ("の推進", "を進める"),
    ("の検討", "を検討する"),
    ("の共有", "を共有する"),
    ("の改善", "を改善する"),
    ("の強化", "を強化する"),
    ("の最適化", "を最適化する"),
    ("の管理", "を管理する"),
    ("の運用", "を運用する"),
    ("の導入", "を導入する"),
    ("の活用", "を活用する"),
    ("の実現", "を実現する"),
    ("の形成", "を形成する"),
    ("の調整", "を調整する"),
    ("の連携", "と連携する"),
    ("の対応", "に対応する"),
    ("の提供", "を提供する"),
)

PROTECTED_BLOCK_KEYWORDS: Tuple[str, ...] = (
    "免責",
    "参考文献",
    "references",
    "disclaimer",
    "出典:",
)


@dataclass(frozen=True)
class NominalizationAlert:
    paragraph_index: int
    sentence_index: int
    sentence_excerpt: str
    nominalization_ratio: float
    matched_patterns: Tuple[str, ...]
    preserved_domain_terms: Tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class NominalizationRewriteCandidate:
    paragraph_index: int
    sentence_index: int
    original_sentence: str
    rewritten_sentence: str
    preserved_domain_terms: Tuple[str, ...]
    reason: str


@dataclass
class NominalizationResult:
    nominalization_score: float
    nominalization_alerts: List[NominalizationAlert] = field(default_factory=list)
    rewrite_candidates: List[NominalizationRewriteCandidate] = field(default_factory=list)
    rewrite_cap: int = 0


@dataclass(frozen=True)
class _ParagraphBlock:
    index: int
    text: str
    is_heading: bool
    is_protected: bool


class Phase03Nominalization:
    """Detect noun-heavy phrasing and provide minimal rewrite candidates."""

    def __init__(
        self,
        nominalization_alert_threshold: float = 0.18,
        max_nominalization_rewrite_ratio: float = 0.12,
    ) -> None:
        self.nominalization_alert_threshold = max(0.0, min(1.0, float(nominalization_alert_threshold)))
        self.max_nominalization_rewrite_ratio = max(0.0, min(1.0, float(max_nominalization_rewrite_ratio)))
        self._sudachi = None
        self._sudachi_mode = None
        self._sudachi_ready = False
        self._init_sudachi()

    def analyze(self, text: str) -> NominalizationResult:
        if not text:
            return NominalizationResult(nominalization_score=0.0)

        blocks = self._split_blocks(text)
        sentence_lookup: Dict[Tuple[int, int], str] = {}
        sentence_scores: List[float] = []
        alerts: List[NominalizationAlert] = []
        total_sentences = 0

        for block in blocks:
            if block.is_heading or block.is_protected:
                continue

            sentences = self._split_sentences(block.text)
            for sentence_index, sentence in enumerate(sentences, start=1):
                normalized = sentence.strip()
                if not normalized or normalized.startswith("※"):
                    continue
                total_sentences += 1
                sentence_lookup[(block.index, sentence_index)] = normalized

                ratio, matched_patterns, preserved_terms = self._sentence_nominalization_ratio(normalized)
                sentence_scores.append(ratio)
                if ratio < self.nominalization_alert_threshold:
                    continue
                if not matched_patterns:
                    continue

                reason = (
                    f"sentence {sentence_index} in paragraph {block.index} exceeds threshold "
                    f"({ratio:.3f} >= {self.nominalization_alert_threshold:.3f})"
                )
                alerts.append(
                    NominalizationAlert(
                        paragraph_index=block.index,
                        sentence_index=sentence_index,
                        sentence_excerpt=self._excerpt(normalized),
                        nominalization_ratio=ratio,
                        matched_patterns=tuple(matched_patterns),
                        preserved_domain_terms=tuple(preserved_terms),
                        reason=reason,
                    )
                )

        nominalization_score = round(sum(sentence_scores) / max(1, len(sentence_scores)), 4)
        rewrite_cap = self._rewrite_cap(total_sentences)
        rewrite_candidates = self._build_rewrite_candidates(alerts, sentence_lookup, rewrite_cap)
        return NominalizationResult(
            nominalization_score=nominalization_score,
            nominalization_alerts=alerts,
            rewrite_candidates=rewrite_candidates,
            rewrite_cap=rewrite_cap,
        )

    def apply_minimal_rewrites(
        self,
        text: str,
        candidates: Sequence[NominalizationRewriteCandidate],
    ) -> Tuple[str, float, List[NominalizationRewriteCandidate]]:
        if not text or not candidates:
            return text, 0.0, []

        blocks = self._split_blocks(text)
        block_map: Dict[int, _ParagraphBlock] = {block.index: block for block in blocks}
        block_texts: Dict[int, str] = {block.index: block.text for block in blocks}

        total_sentences = sum(
            len(self._split_sentences(block.text))
            for block in blocks
            if not block.is_heading and not block.is_protected
        )
        rewrite_cap = self._rewrite_cap(total_sentences)
        if rewrite_cap <= 0:
            return text, 0.0, []

        applied: List[NominalizationRewriteCandidate] = []

        for candidate in candidates:
            if len(applied) >= rewrite_cap:
                break

            block = block_map.get(candidate.paragraph_index)
            if block is None or block.is_heading or block.is_protected:
                continue

            current = block_texts.get(block.index, block.text)
            sentences = self._split_sentences(current)
            sentence_pos = candidate.sentence_index - 1
            if not (0 <= sentence_pos < len(sentences)):
                continue

            current_sentence = sentences[sentence_pos].strip()
            if current_sentence != candidate.original_sentence.strip():
                continue

            sentences[sentence_pos] = candidate.rewritten_sentence
            block_texts[block.index] = self._compose_paragraph(sentences, current)
            applied.append(candidate)

        rebuilt = [block_texts.get(block.index, block.text) for block in blocks]
        rewritten_text = "\n\n".join(segment for segment in rebuilt if segment.strip())
        rewrite_ratio = round(len(applied) / max(1, total_sentences), 4)
        return rewritten_text, rewrite_ratio, applied

    def _split_blocks(self, text: str) -> List[_ParagraphBlock]:
        chunks = [chunk.strip() for chunk in re.split(r"\n{2,}", text or "") if chunk.strip()]
        blocks: List[_ParagraphBlock] = []
        for index, chunk in enumerate(chunks, start=1):
            blocks.append(
                _ParagraphBlock(
                    index=index,
                    text=chunk,
                    is_heading=self._is_heading_block(chunk),
                    is_protected=self._is_protected_block(chunk),
                )
            )
        return blocks

    def _is_heading_block(self, block_text: str) -> bool:
        line = block_text.strip().splitlines()[0] if block_text.strip() else ""
        return bool(line.lstrip().startswith("#"))

    def _is_protected_block(self, block_text: str) -> bool:
        lowered = (block_text or "").lower()
        if any(keyword in lowered for keyword in PROTECTED_BLOCK_KEYWORDS):
            return True
        lines = [line.strip() for line in block_text.splitlines() if line.strip()]
        if lines and all(line.startswith("http://") or line.startswith("https://") for line in lines):
            return True
        return False

    def _split_sentences(self, text: str) -> List[str]:
        if not text:
            return []
        fragments = re.split(r"(?<=[。！？!?])\s*|(?<=\.)\s+(?=[A-Za-z0-9])|\n+", text.strip())
        return [fragment.strip() for fragment in fragments if fragment and fragment.strip()]

    def _sentence_nominalization_ratio(self, sentence: str) -> Tuple[float, List[str], List[str]]:
        sudachi_result = self._sentence_nominalization_ratio_sudachi(sentence)
        if sudachi_result is not None:
            return sudachi_result

        tokens = TOKEN_PATTERN.findall(sentence or "")
        token_count = len(tokens)
        pattern_hits: Dict[str, int] = {}
        weighted_hits = 0.0

        for name, pattern, weight in NOMINAL_PATTERNS:
            hits = pattern.findall(sentence)
            if not hits:
                continue
            pattern_hits[name] = len(hits)
            weighted_hits += len(hits) * weight

        preserved_terms = [term for term in DOMAIN_TERMS if term in sentence]
        weighted_hits = max(0.0, weighted_hits - 0.35 * len(preserved_terms))
        raw_ratio = weighted_hits / max(1, token_count)
        scaled_ratio = min(1.0, raw_ratio * 3.0)
        return round(scaled_ratio, 4), sorted(pattern_hits.keys()), preserved_terms

    def _sentence_nominalization_ratio_sudachi(
        self,
        sentence: str,
    ) -> Optional[Tuple[float, List[str], List[str]]]:
        morphemes = self._tokenize_sudachi(sentence)
        if not morphemes:
            return None

        content_count = 0
        pattern_hits: Dict[str, int] = {}
        weighted_hits = 0.0
        noun_chain_terms = {
            "実施",
            "推進",
            "検討",
            "共有",
            "改善",
            "強化",
            "最適化",
            "管理",
            "運用",
            "導入",
            "活用",
            "実現",
            "形成",
            "評価",
            "調整",
            "連携",
            "対応",
            "提供",
        }

        for index, morpheme in enumerate(morphemes):
            pos = morpheme.part_of_speech()
            pos_major = pos[0] if pos else ""
            if pos_major not in {"補助記号", "空白"}:
                content_count += 1

            if index + 1 >= len(morphemes):
                continue
            next_morpheme = morphemes[index + 1]
            if not self._is_case_particle(next_morpheme):
                continue

            surface = morpheme.surface()
            if self._is_sahen_nominal(morpheme):
                has_chain_neighbor = False
                if index >= 2 and self._is_case_particle(morphemes[index - 1]) and self._is_sahen_nominal(morphemes[index - 2]):
                    has_chain_neighbor = True
                if index + 2 < len(morphemes) and self._is_sahen_nominal(morphemes[index + 2]):
                    has_chain_neighbor = True
                if has_chain_neighbor or surface in noun_chain_terms:
                    pattern_hits["noun_chain"] = pattern_hits.get("noun_chain", 0) + 1
                    weighted_hits += 1.0

            if surface.endswith("化"):
                pattern_hits["ka_suffix"] = pattern_hits.get("ka_suffix", 0) + 1
                weighted_hits += 1.0
            if surface.endswith("性"):
                pattern_hits["sei_suffix"] = pattern_hits.get("sei_suffix", 0) + 1
                weighted_hits += 0.8

        for name, pattern, weight in NOMINAL_PATTERNS:
            if name not in {"niokeru", "kotoga"}:
                continue
            hits = pattern.findall(sentence)
            if not hits:
                continue
            pattern_hits[name] = pattern_hits.get(name, 0) + len(hits)
            weighted_hits += len(hits) * weight

        preserved_terms = [term for term in DOMAIN_TERMS if term in sentence]
        weighted_hits = max(0.0, weighted_hits - 0.35 * len(preserved_terms))
        raw_ratio = weighted_hits / max(1, content_count)
        scaled_ratio = min(1.0, raw_ratio * 3.0)
        return round(scaled_ratio, 4), sorted(pattern_hits.keys()), preserved_terms

    def _is_sahen_nominal(self, morpheme) -> bool:
        pos = morpheme.part_of_speech()
        if not pos:
            return False
        if pos[0] != "名詞":
            return False
        detail = pos[2] if len(pos) > 2 else ""
        return detail == "サ変可能"

    def _is_case_particle(self, morpheme) -> bool:
        pos = morpheme.part_of_speech()
        if not pos or pos[0] != "助詞":
            return False
        return morpheme.surface() in CASE_PARTICLES

    def _init_sudachi(self) -> None:
        if not SUDACHI_AVAILABLE or sudachi_dictionary is None or sudachi_tokenizer is None:
            return
        try:
            self._sudachi = sudachi_dictionary.Dictionary().create()
            self._sudachi_mode = sudachi_tokenizer.Tokenizer.SplitMode.B
            self._sudachi_ready = True
        except Exception:  # pragma: no cover - defensive fallback
            self._sudachi = None
            self._sudachi_mode = None
            self._sudachi_ready = False

    def _tokenize_sudachi(self, text: str):
        if not self._sudachi_ready or not self._sudachi:
            return []
        try:
            return list(self._sudachi.tokenize(text or "", self._sudachi_mode))
        except Exception:  # pragma: no cover - defensive fallback
            return []

    def _build_rewrite_candidates(
        self,
        alerts: Sequence[NominalizationAlert],
        sentence_lookup: Dict[Tuple[int, int], str],
        rewrite_cap: int,
    ) -> List[NominalizationRewriteCandidate]:
        if rewrite_cap <= 0:
            return []

        candidates: List[NominalizationRewriteCandidate] = []
        sorted_alerts = sorted(
            alerts,
            key=lambda alert: (
                -alert.nominalization_ratio,
                alert.paragraph_index,
                alert.sentence_index,
            ),
        )
        for alert in sorted_alerts:
            if len(candidates) >= rewrite_cap:
                break

            original = sentence_lookup.get((alert.paragraph_index, alert.sentence_index), "")
            if not original:
                continue

            rewritten = self._rewrite_sentence(original)
            if rewritten == original:
                continue

            candidates.append(
                NominalizationRewriteCandidate(
                    paragraph_index=alert.paragraph_index,
                    sentence_index=alert.sentence_index,
                    original_sentence=original,
                    rewritten_sentence=rewritten,
                    preserved_domain_terms=alert.preserved_domain_terms,
                    reason=(
                        f"reduce nominalization ratio from sentence {alert.sentence_index} "
                        f"in paragraph {alert.paragraph_index}"
                    ),
                )
            )

        return candidates

    def _rewrite_sentence(self, sentence: str) -> str:
        updated = sentence
        for before, after in REWRITE_RULES:
            updated = updated.replace(before, after)
        return updated

    def _compose_paragraph(self, sentences: Sequence[str], original_text: str) -> str:
        cleaned = [sentence.strip() for sentence in sentences if sentence and sentence.strip()]
        if not cleaned:
            return original_text.strip()
        if self._contains_japanese(original_text):
            return "".join(cleaned)
        return " ".join(cleaned)

    def _contains_japanese(self, text: str) -> bool:
        return bool(JP_PATTERN.search(text or ""))

    def _rewrite_cap(self, sentence_count: int) -> int:
        if sentence_count <= 0:
            return 0
        cap = int(sentence_count * self.max_nominalization_rewrite_ratio)
        if cap == 0 and self.max_nominalization_rewrite_ratio > 0 and sentence_count >= 3:
            cap = 1
        return max(0, min(sentence_count, cap))

    def _excerpt(self, sentence: str, max_chars: int = 80) -> str:
        clean = sentence.strip()
        if len(clean) <= max_chars:
            return clean
        return clean[: max_chars - 1] + "…"
