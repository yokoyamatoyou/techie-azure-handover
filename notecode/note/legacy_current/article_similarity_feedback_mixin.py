"""article_similarity_feedback_mixin.py - Similarity, novelty, and feedback helpers."""
from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from core.app_config import get_fingerprint_threshold_presets
from note.legacy_current import article_runtime_symbols as _runtime_symbols

_cached_ag: Dict[str, Any] = {}


def _ag(name: str) -> Any:
    """Lazy accessor to avoid hard dependencies on note.article_generator."""
    if name not in _cached_ag:
        _cached_ag[name] = getattr(_runtime_symbols, name)
    return _cached_ag[name]


class ArticleSimilarityFeedbackMixin:
    """Mixin providing similarity, redundancy, novelty, and feedback utilities."""

    @staticmethod
    def _strip_headings_and_urls(text: str, url_replacement: str = "") -> str:
        cleaned = _ag("_RE_HEADING_LINE").sub("", text or "")
        return _ag("_RE_URL").sub(url_replacement, cleaned)

    def _normalize_similarity_text(self, text: str) -> str:
        cleaned = self._strip_headings_and_urls(text)
        cleaned = _ag("_RE_WHITESPACE_COLLAPSE").sub("", cleaned)
        cleaned = _ag("_RE_PUNCTUATION_STRIP").sub("", cleaned)
        return cleaned.strip()

    def _to_char_ngram_set(self, normalized_text: str, n: Optional[int] = None) -> set:
        ngram_size = int(_ag("SIMILARITY_NGRAM_SIZE")) if n is None else max(1, int(n))
        text = (normalized_text or "")[: int(_ag("SIMILARITY_NGRAM_MAX_LEN"))]
        if not text:
            return set()
        if len(text) < ngram_size:
            return {text}
        return {text[i : i + ngram_size] for i in range(len(text) - ngram_size + 1)}

    def _similarity_overlap_scores(self, left: str, right: str) -> Tuple[float, float]:
        left_set = self._to_char_ngram_set(left)
        right_set = self._to_char_ngram_set(right)
        if not left_set or not right_set:
            return 0.0, 0.0
        overlap_size = len(left_set & right_set)
        if overlap_size == 0:
            return 0.0, 0.0
        union_size = len(left_set | right_set)
        jaccard = overlap_size / max(1, union_size)
        containment = overlap_size / max(1, min(len(left_set), len(right_set)))
        return jaccard, containment

    def _is_redundant_expansion(self, existing_body: str, expansion: str) -> bool:
        if not existing_body or not expansion:
            return False

        expansion_blocks = self._extract_section_blocks(expansion)
        expansion_text = expansion_blocks[0][1] if expansion_blocks else expansion
        norm_expansion = self._normalize_similarity_text(expansion_text)
        if len(norm_expansion) < 40:
            return True

        norm_body = self._normalize_similarity_text(existing_body)
        if not norm_body:
            return False
        if norm_expansion in norm_body:
            return True

        jaccard, containment = self._similarity_overlap_scores(norm_expansion, norm_body)
        if (
            jaccard >= float(_ag("REDUNDANT_EXPANSION_JACCARD_THRESHOLD"))
            or containment >= float(_ag("REDUNDANT_EXPANSION_CONTAINMENT_THRESHOLD"))
        ):
            return True

        for _, section_text in self._extract_section_blocks(existing_body):
            norm_section = self._normalize_similarity_text(section_text)
            if len(norm_section) < 50:
                continue
            sec_jaccard, sec_containment = self._similarity_overlap_scores(norm_expansion, norm_section)
            if (
                sec_jaccard >= float(_ag("REDUNDANT_EXPANSION_JACCARD_THRESHOLD"))
                or sec_containment >= float(_ag("REDUNDANT_EXPANSION_CONTAINMENT_THRESHOLD"))
            ):
                return True
        return False

    def _build_section_overlap_memory(self, existing_sections: List[str], keep_last: int = 6) -> str:
        if not existing_sections:
            return ""

        summaries: List[str] = []
        for section in existing_sections[-max(1, keep_last) :]:
            blocks = self._extract_section_blocks(section)
            if blocks:
                heading, content = blocks[0]
            else:
                heading, content = "本文", section

            sentences_for_memory: List[str] = []
            for part in _ag("_RE_SENTENCE_SPLIT").split((content or "").strip()):
                cleaned = _ag("_RE_WHITESPACE_COLLAPSE").sub(" ", part or "").strip()
                if len(cleaned) >= 12:
                    sentences_for_memory.append(cleaned)
                if len(sentences_for_memory) >= 2:
                    break
            if not sentences_for_memory:
                fallback = _ag("_RE_WHITESPACE_COLLAPSE").sub(" ", content or "").strip()
                if fallback:
                    sentences_for_memory.append(fallback)

            joined = " / ".join(s[:88].rstrip(" 、。") for s in sentences_for_memory if s)
            if joined:
                summaries.append(f"- {heading}: {joined}")
            else:
                summaries.append(f"- {heading}")

        return "\n".join(summaries)[:960]

    def _get_redundancy_thresholds(self) -> Dict[str, float]:
        """重複判定の閾値をモード別に返す。"""
        jaccard = float(_ag("REDUNDANT_SECTION_JACCARD_THRESHOLD"))
        containment = float(_ag("REDUNDANT_SECTION_CONTAINMENT_THRESHOLD"))
        first_ratio = 0.78

        try:
            presets = get_fingerprint_threshold_presets()
            active = str((presets or {}).get("active_preset", "standard"))
        except Exception:
            active = "standard"
        if active in ("strict", "superhuman"):
            jaccard = min(jaccard, 0.42)
            containment = min(containment, 0.68)
            first_ratio = min(first_ratio, 0.70)
        if active == "superhuman":
            jaccard = min(jaccard, 0.40)
            containment = min(containment, 0.66)
            first_ratio = min(first_ratio, 0.68)

        return {
            "jaccard": jaccard,
            "containment": containment,
            "first_sentence_ratio": first_ratio,
        }

    def _extract_content_terms(self, text: str, max_chars: int = 2200) -> List[str]:
        if not text:
            return []
        normalized = self._strip_headings_and_urls(text, url_replacement=" ")
        normalized = normalized[:max_chars]
        tokens = _ag("_RE_CJK_LATIN_TOKEN").findall(normalized.lower())
        stopwords = set(_ag("LEXICAL_PRIMING_STOPWORDS"))
        terms: List[str] = []
        for token in tokens:
            if token in stopwords:
                continue
            if token.isdigit():
                continue
            terms.append(token)
        return terms

    def _build_lexical_priming_feedback(self, existing_sections: List[str]) -> Dict[str, Any]:
        if not existing_sections:
            return {}
        latest_section = existing_sections[-1]
        latest_terms = self._extract_content_terms(latest_section, max_chars=1800)
        if not latest_terms:
            return {}
        latest_counter = Counter(latest_terms)
        carry_terms = [term for term, _ in latest_counter.most_common(2)]
        avoid_terms = [term for term, count in latest_counter.most_common(8) if count >= 2][:5]
        return {
            "carry_terms": carry_terms,
            "avoid_terms": avoid_terms,
        }

    def _build_fingerprint_feedback(self, existing_sections: List[str]) -> Dict[str, Any]:
        if not existing_sections:
            return {}
        analyzer = getattr(self, "_fingerprint_analyzer", None)
        if analyzer is None:
            return {}
        recent_text = self._combine_sections(existing_sections[-2:])
        focus = getattr(self, "_effective_writing_focus", "")
        report = analyzer.analyze(recent_text, focus=focus)
        hint_lines: List[str] = []
        for flag in (report.flat_zone_flags or []):
            mapped = self._lookup_fingerprint_prompt_hint(str(flag))
            if mapped and mapped not in hint_lines:
                hint_lines.append(mapped)
        section_cfg = self._get_section_generation_config()
        hard_soft_cfg = section_cfg.get("hard_soft_thresholds", {}) if isinstance(section_cfg, dict) else {}
        target_score = float(
            (hard_soft_cfg.get("soft_min_unpredictability") if isinstance(hard_soft_cfg, dict) else None) or 0.55
        )
        soft_floor = max(0.46, target_score - 0.18)
        if report.overall_unpredictability < soft_floor and not hint_lines:
            hint_lines.append("文頭・文末パターンを固定せず、段落ごとのテンション差を明確にする。")
        return {
            "overall_unpredictability": report.overall_unpredictability,
            "flat_zone_flags": list(report.flat_zone_flags or []),
            "hint_lines": hint_lines[:2],
            "correction_hints": list(report.correction_hints or [])[:2],
        }

    def _lookup_fingerprint_prompt_hint(self, flag: str) -> str:
        """Resolve hint text for fingerprint flags with backward-compatible aliases."""
        key = (flag or "").strip()
        if not key:
            return ""
        direct = _ag("FINGERPRINT_PROMPT_HINTS").get(key)
        if direct:
            return str(direct)
        alias_key = _ag("FINGERPRINT_HINT_KEY_ALIASES").get(key, "")
        if alias_key:
            return str(_ag("FINGERPRINT_PROMPT_HINTS").get(alias_key, "") or "")
        return ""

    def _build_section_generation_feedback(self, existing_sections: List[str]) -> Dict[str, Any]:
        if not existing_sections:
            return {}
        lexical = self._build_lexical_priming_feedback(existing_sections)
        fingerprint = self._build_fingerprint_feedback(existing_sections)
        if not lexical and not fingerprint:
            return {}
        feedback = {
            "lexical": lexical,
            "fingerprint": fingerprint,
        }
        self._section_feedback_reports.append(
            {
                "sections_seen": len(existing_sections),
                "fingerprint_overall_unpredictability": float(
                    (fingerprint or {}).get("overall_unpredictability", 0.0) or 0.0
                ),
                "fingerprint_flat_zone_flags": list((fingerprint or {}).get("flat_zone_flags", [])),
                "lexical_carry_terms": list((lexical or {}).get("carry_terms", [])),
                "lexical_avoid_terms": list((lexical or {}).get("avoid_terms", [])),
            }
        )
        return feedback

    def _render_section_feedback_block(self, section_feedback: Optional[Dict[str, Any]]) -> str:
        if not section_feedback:
            return ""

        lines: List[str] = ["【直前セクションのフィードバック（反映推奨）】"]
        fingerprint = section_feedback.get("fingerprint") if isinstance(section_feedback, dict) else None
        lexical = section_feedback.get("lexical") if isinstance(section_feedback, dict) else None

        if isinstance(fingerprint, dict):
            score = float(fingerprint.get("overall_unpredictability", 0.0) or 0.0)
            section_cfg = self._get_section_generation_config()
            hard_soft_cfg = section_cfg.get("hard_soft_thresholds", {}) if isinstance(section_cfg, dict) else {}
            target_score = float(
                (hard_soft_cfg.get("soft_min_unpredictability") if isinstance(hard_soft_cfg, dict) else None) or 0.55
            )
            lines.append(
                f"- 直近の指紋スコア（unpredictability）: {score:.2f}（目安: {target_score:.2f}以上）"
            )
            for hint in list(fingerprint.get("hint_lines", []))[:2]:
                lines.append(f"- {hint}")

        if isinstance(lexical, dict):
            carry_terms = [str(term) for term in lexical.get("carry_terms", []) if str(term).strip()]
            avoid_terms = [str(term) for term in lexical.get("avoid_terms", []) if str(term).strip()]
            if carry_terms:
                lines.append(
                    "- 連続性のため、前セクション語を1〜2語だけ自然に引き継ぐ: "
                    + " / ".join(carry_terms[:2])
                )
            if avoid_terms:
                lines.append(
                    "- 同一語の連発を避け、言い換えを使う: "
                    + " / ".join(avoid_terms[:5])
                )
            lines.append("- 同一レンマ相当の語を3回以上繰り返さない。")

        return "\n".join(lines)

    def _is_redundant_section(self, candidate_section: str, existing_sections: List[str]) -> bool:
        result = self._check_redundancy_with_reason(candidate_section, existing_sections)
        return result[0]

    def _check_redundancy_with_reason(
        self, candidate_section: str, existing_sections: List[str]
    ) -> tuple:
        """重複判定 + 重複理由と被り語彙を返す（R3-T01）。"""
        if not candidate_section or not existing_sections:
            return (False, [])

        candidate_blocks = self._extract_section_blocks(candidate_section)
        candidate_text = candidate_blocks[0][1] if candidate_blocks else candidate_section
        norm_candidate = self._normalize_similarity_text(candidate_text)
        if len(norm_candidate) < 80:
            return (True, [])

        candidate_terms = set(self._extract_content_terms(candidate_text, max_chars=1200))
        thresholds = self._get_redundancy_thresholds()
        first_sentence_ratio_threshold = float(thresholds.get("first_sentence_ratio", 0.78))
        jaccard_threshold = float(thresholds.get("jaccard", _ag("REDUNDANT_SECTION_JACCARD_THRESHOLD")))
        containment_threshold = float(
            thresholds.get("containment", _ag("REDUNDANT_SECTION_CONTAINMENT_THRESHOLD"))
        )

        for section in existing_sections:
            blocks = self._extract_section_blocks(section)
            section_text = blocks[0][1] if blocks else section
            norm_section = self._normalize_similarity_text(section_text)
            if len(norm_section) < 80:
                continue
            cand_first = next(
                (s.strip() for s in _ag("_RE_SENTENCE_SPLIT").split(candidate_text) if s.strip()),
                "",
            )
            sec_first = next(
                (s.strip() for s in _ag("_RE_SENTENCE_SPLIT").split(section_text) if s.strip()),
                "",
            )
            if cand_first and sec_first:
                first_ratio = SequenceMatcher(None, cand_first[:80], sec_first[:80]).ratio()
                if first_ratio >= first_sentence_ratio_threshold:
                    section_terms = set(self._extract_content_terms(section_text, max_chars=1200))
                    return (True, list(candidate_terms & section_terms)[:10])
            if norm_candidate in norm_section or norm_section in norm_candidate:
                section_terms = set(self._extract_content_terms(section_text, max_chars=1200))
                return (True, list(candidate_terms & section_terms)[:10])
            jaccard, containment = self._similarity_overlap_scores(norm_candidate, norm_section)
            if jaccard >= jaccard_threshold or containment >= containment_threshold:
                section_terms = set(self._extract_content_terms(section_text, max_chars=1200))
                return (True, list(candidate_terms & section_terms)[:10])
        return (False, [])

    @staticmethod
    def _dedupe_terms(terms: List[str], max_items: int = 10) -> List[str]:
        unique: List[str] = []
        for term in terms:
            cleaned = (term or "").strip()
            if not cleaned or cleaned in unique:
                continue
            unique.append(cleaned)
            if len(unique) >= max_items:
                break
        return unique

    def _compute_section_novelty_report(
        self,
        candidate_section: str,
        existing_sections: List[str],
        *,
        redundancy_result: Optional[Tuple[bool, List[str]]] = None,
    ) -> Dict[str, Any]:
        """既出セクションに対する新規性を軽量に算出する。"""
        if not candidate_section:
            return {
                "novelty_ratio": 1.0,
                "overlap_term_ratio": 0.0,
                "overlap_terms": [],
                "hard_redundant": False,
                "candidate_terms_count": 0,
                "effective_terms_count": 0,
            }

        candidate_blocks = self._extract_section_blocks(candidate_section)
        candidate_text = candidate_blocks[0][1] if candidate_blocks else candidate_section
        candidate_terms = self._dedupe_terms(
            self._extract_content_terms(candidate_text, max_chars=1400),
            max_items=120,
        )
        if not existing_sections:
            return {
                "novelty_ratio": 1.0,
                "overlap_term_ratio": 0.0,
                "overlap_terms": [],
                "hard_redundant": False,
                "candidate_terms_count": len(candidate_terms),
                "effective_terms_count": len(candidate_terms),
            }

        latest_terms = self._extract_content_terms(existing_sections[-1], max_chars=900)
        carry_terms = [term for term, _ in Counter(latest_terms).most_common(2)]
        candidate_effective = [term for term in candidate_terms if term not in carry_terms]

        history_text = self._combine_sections(existing_sections[-6:])
        history_terms = set(self._extract_content_terms(history_text, max_chars=2800))

        overlap_terms = [term for term in candidate_effective if term in history_terms]
        effective_count = len(candidate_effective)
        overlap_ratio = (len(overlap_terms) / effective_count) if effective_count > 0 else 0.0
        novelty_ratio = max(0.0, 1.0 - overlap_ratio)

        redundant, redundancy_terms = (
            redundancy_result
            if redundancy_result is not None
            else self._check_redundancy_with_reason(candidate_section, existing_sections)
        )
        merged_overlap_terms = self._dedupe_terms(
            list(overlap_terms) + list(redundancy_terms or []),
            max_items=14,
        )
        return {
            "novelty_ratio": round(novelty_ratio, 4),
            "overlap_term_ratio": round(overlap_ratio, 4),
            "overlap_terms": merged_overlap_terms,
            "hard_redundant": bool(redundant),
            "candidate_terms_count": len(candidate_terms),
            "effective_terms_count": effective_count,
        }

    def _get_novelty_threshold(self, section_index: int, total_sections: int, focus: str) -> float:
        cfg = self._get_section_generation_config()
        novelty_cfg = cfg.get("novelty_gate", {}) if isinstance(cfg, dict) else {}
        if not isinstance(novelty_cfg, dict):
            novelty_cfg = {}
        intro = float(novelty_cfg.get("intro_novelty_min", 0.20) or 0.20)
        middle = float(novelty_cfg.get("middle_novelty_min", 0.30) or 0.30)
        closing = float(novelty_cfg.get("closing_novelty_min", 0.35) or 0.35)
        relax = float(novelty_cfg.get("focus_relaxation", 0.03) or 0.03)

        if total_sections <= 1:
            threshold = middle
        else:
            ratio = section_index / max(1, total_sections - 1)
            if ratio <= 0.25:
                threshold = intro
            elif ratio >= 0.80:
                threshold = closing
            else:
                threshold = middle

        if focus in ("analysis", "explanation"):
            threshold -= relax
        return max(0.0, min(1.0, threshold))

    def _should_retry_due_to_low_novelty(
        self,
        report: Dict[str, Any],
        *,
        section_index: int,
        total_sections: int,
        focus: str,
        has_history: bool,
    ) -> bool:
        if not has_history:
            return False
        cfg = self._get_section_generation_config()
        novelty_cfg = cfg.get("novelty_gate", {}) if isinstance(cfg, dict) else {}
        if not isinstance(novelty_cfg, dict):
            novelty_cfg = {}
        if not bool(novelty_cfg.get("enabled", False)):
            return False
        if bool(report.get("hard_redundant", False)):
            return False
        min_terms = int(novelty_cfg.get("min_candidate_terms", 10) or 10)
        if int(report.get("candidate_terms_count", 0) or 0) < max(1, min_terms):
            return False

        threshold = self._get_novelty_threshold(section_index, total_sections, focus)
        novelty_ratio = float(report.get("novelty_ratio", 1.0) or 1.0)
        return novelty_ratio < threshold
