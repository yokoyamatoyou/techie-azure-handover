"""R8-T11: ZeroStylus-like two-layer template extraction from past articles.

Layer 1 (structural): heading hierarchy, section count, paragraph-per-section distribution.
Layer 2 (stylistic): sentence-length pattern, ending-style distribution, persona markers.

Usage:
    extractor = TemplateExtractor()
    template = extractor.extract(article_text)
    similarity = extractor.structural_similarity(template_a, template_b)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ArticleTemplate:
    """Two-layer template extracted from an article."""
    # Layer 1: structural
    heading_count: int = 0
    heading_levels: List[int] = field(default_factory=list)
    section_count: int = 0
    paragraphs_per_section: List[int] = field(default_factory=list)
    total_paragraphs: int = 0
    # Layer 2: stylistic
    avg_sentence_length: float = 0.0
    sentence_length_pattern: List[int] = field(default_factory=list)  # bucketed
    ending_distribution: Dict[str, float] = field(default_factory=dict)
    has_conclusion: bool = False
    has_introduction: bool = False


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_TERMINAL_PUNCT = re.compile(r"[。！？!?]")
_ENDING_DESU = re.compile(r"です[。！？]?$")
_ENDING_MASU = re.compile(r"ます[。！？]?$")
_ENDING_DA = re.compile(r"(?:だ|である)[。！？]?$")
_ENDING_QUESTION = re.compile(r"[？?]$")

_INTRO_KEYWORDS = re.compile(r"はじめに|導入|イントロ|概要")
_CONCLUSION_KEYWORDS = re.compile(r"まとめ|結論|おわりに|結び|最後に")


class TemplateExtractor:
    """Extract two-layer templates from article text."""

    def extract(self, text: str) -> ArticleTemplate:
        if not text or len(text.strip()) < 50:
            return ArticleTemplate()

        headings = _HEADING_RE.findall(text)
        heading_levels = [len(h[0]) for h in headings]
        heading_texts = [h[1].strip() for h in headings]

        # Split into sections by headings
        sections = _HEADING_RE.split(text)
        # sections alternates: [pre-heading, level, title, body, level, title, body, ...]
        section_bodies: List[str] = []
        if sections:
            # First element is text before any heading
            if sections[0].strip():
                section_bodies.append(sections[0].strip())
            # Then groups of 3: (level_hashes, title, body)
            i = 1
            while i + 2 < len(sections):
                body = sections[i + 2].strip()
                if body:
                    section_bodies.append(body)
                i += 3

        # Paragraphs per section
        paragraphs_per_section: List[int] = []
        total_paragraphs = 0
        for body in section_bodies:
            paras = [p.strip() for p in body.split("\n\n") if p.strip()]
            paragraphs_per_section.append(len(paras))
            total_paragraphs += len(paras)

        # Sentence analysis
        all_sentences = [s.strip() for s in _TERMINAL_PUNCT.split(text) if s.strip() and len(s.strip()) >= 4]
        # Remove heading lines from sentences
        all_sentences = [s for s in all_sentences if not s.startswith("#")]

        avg_len = sum(len(s) for s in all_sentences) / max(1, len(all_sentences))

        # Bucket sentence lengths: short(<20), medium(20-50), long(>50)
        length_pattern: List[int] = []
        for s in all_sentences:
            if len(s) < 20:
                length_pattern.append(0)  # short
            elif len(s) <= 50:
                length_pattern.append(1)  # medium
            else:
                length_pattern.append(2)  # long

        # Ending distribution
        ending_counts: Dict[str, int] = {"desu": 0, "masu": 0, "da": 0, "question": 0, "other": 0}
        for s in all_sentences:
            if _ENDING_QUESTION.search(s):
                ending_counts["question"] += 1
            elif _ENDING_DESU.search(s):
                ending_counts["desu"] += 1
            elif _ENDING_MASU.search(s):
                ending_counts["masu"] += 1
            elif _ENDING_DA.search(s):
                ending_counts["da"] += 1
            else:
                ending_counts["other"] += 1
        total_endings = max(1, sum(ending_counts.values()))
        ending_dist = {k: round(v / total_endings, 3) for k, v in ending_counts.items()}

        # Intro/conclusion detection
        has_intro = any(_INTRO_KEYWORDS.search(t) for t in heading_texts)
        has_conclusion = any(_CONCLUSION_KEYWORDS.search(t) for t in heading_texts)

        return ArticleTemplate(
            heading_count=len(headings),
            heading_levels=heading_levels,
            section_count=len(section_bodies),
            paragraphs_per_section=paragraphs_per_section,
            total_paragraphs=total_paragraphs,
            avg_sentence_length=round(avg_len, 1),
            sentence_length_pattern=length_pattern,
            ending_distribution=ending_dist,
            has_conclusion=has_conclusion,
            has_introduction=has_intro,
        )

    def structural_similarity(self, a: ArticleTemplate, b: ArticleTemplate) -> float:
        """Compute structural similarity between two templates (R8-T12).

        Returns 0.0 (completely different) to 1.0 (identical structure).
        """
        scores: List[float] = []

        # Heading count similarity
        max_h = max(a.heading_count, b.heading_count, 1)
        scores.append(1.0 - abs(a.heading_count - b.heading_count) / max_h)

        # Section count similarity
        max_s = max(a.section_count, b.section_count, 1)
        scores.append(1.0 - abs(a.section_count - b.section_count) / max_s)

        # Paragraph distribution similarity (cosine-like)
        scores.append(self._list_similarity(a.paragraphs_per_section, b.paragraphs_per_section))

        # Sentence length pattern similarity
        scores.append(self._bucket_distribution_similarity(
            a.sentence_length_pattern, b.sentence_length_pattern, num_buckets=3
        ))

        # Ending distribution similarity
        scores.append(self._dict_cosine(a.ending_distribution, b.ending_distribution))

        # Intro/conclusion match
        intro_match = 1.0 if a.has_introduction == b.has_introduction else 0.0
        concl_match = 1.0 if a.has_conclusion == b.has_conclusion else 0.0
        scores.append((intro_match + concl_match) / 2.0)

        weights = [0.20, 0.20, 0.20, 0.15, 0.15, 0.10]
        total = sum(s * w for s, w in zip(scores, weights))
        return round(min(1.0, max(0.0, total)), 4)

    @staticmethod
    def _list_similarity(a: List[int], b: List[int]) -> float:
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        max_len = max(len(a), len(b))
        pa = a + [0] * (max_len - len(a))
        pb = b + [0] * (max_len - len(b))
        dot = sum(x * y for x, y in zip(pa, pb))
        mag_a = sum(x * x for x in pa) ** 0.5
        mag_b = sum(x * x for x in pb) ** 0.5
        if mag_a < 0.001 or mag_b < 0.001:
            return 0.0
        return dot / (mag_a * mag_b)

    @staticmethod
    def _bucket_distribution_similarity(a: List[int], b: List[int], num_buckets: int = 3) -> float:
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        dist_a = [0.0] * num_buckets
        dist_b = [0.0] * num_buckets
        for v in a:
            if 0 <= v < num_buckets:
                dist_a[v] += 1
        for v in b:
            if 0 <= v < num_buckets:
                dist_b[v] += 1
        total_a = max(1.0, sum(dist_a))
        total_b = max(1.0, sum(dist_b))
        dist_a = [x / total_a for x in dist_a]
        dist_b = [x / total_b for x in dist_b]
        diff = sum(abs(x - y) for x, y in zip(dist_a, dist_b))
        return max(0.0, 1.0 - diff / 2.0)

    @staticmethod
    def _dict_cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        keys = set(a.keys()) | set(b.keys())
        if not keys:
            return 1.0
        dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
        mag_a = sum(a.get(k, 0.0) ** 2 for k in keys) ** 0.5
        mag_b = sum(b.get(k, 0.0) ** 2 for k in keys) ** 0.5
        if mag_a < 0.001 or mag_b < 0.001:
            return 0.0
        return dot / (mag_a * mag_b)
