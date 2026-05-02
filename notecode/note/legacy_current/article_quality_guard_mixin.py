"""Quality guard utility helpers for ArticleGenerator."""
from __future__ import annotations

import json
import logging
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from human_resonance.style_policy import AI_LIKE_OPENING_PATTERNS
from note.legacy_current import article_runtime_symbols as _runtime_symbols

logger = logging.getLogger(__name__)

_cached_ag: Dict[str, Any] = {}


def _ag(name: str) -> Any:
    """Lazy accessor to avoid hard dependencies on note.article_generator."""
    if name not in _cached_ag:
        _cached_ag[name] = getattr(_runtime_symbols, name)
    return _cached_ag[name]


class ArticleQualityGuardMixin:
    """Rewrite guard, grammar repair, and quality-context utilities."""

    def _estimate_rewrite_ratio(self, before: str, after: str) -> float:
        before_norm = re.sub(r"\s+", "", before or "")
        after_norm = re.sub(r"\s+", "", after or "")
        if not before_norm and not after_norm:
            return 0.0
        if not before_norm or not after_norm:
            return 1.0
        similarity = SequenceMatcher(None, before_norm[:12000], after_norm[:12000]).ratio()
        return max(0.0, 1.0 - similarity)

    def _sentence_length_stddev(self, text: str) -> float:
        sentences = [s.strip() for s in _ag("_RE_SENTENCE_SPLIT").split(text or "") if s.strip()]
        if len(sentences) < 4:
            return 0.0
        lengths = [len(s) for s in sentences]
        mean = sum(lengths) / len(lengths)
        variance = sum((ln - mean) ** 2 for ln in lengths) / len(lengths)
        return variance ** 0.5

    def _looks_style_flattened(self, before: str, after: str) -> bool:
        before_std = self._sentence_length_stddev(before)
        after_std = self._sentence_length_stddev(after)
        if before_std < 9.0:
            return False
        return after_std < before_std * 0.67 and (before_std - after_std) >= 5.0

    def _heading_count(self, text: str) -> int:
        return len(_ag("_RE_HEADING_COUNT").findall(text or ""))

    def _rewrite_guard_check(
        self,
        before_lead: str,
        before_body: str,
        after_lead: str,
        after_body: str,
        max_rewrite_ratio: float = 0.24,
        label: str = "guard",
    ) -> Optional[str]:
        """Return rejection reason string, or None if acceptable."""
        merged_before = f"{before_lead}\n\n{before_body}"
        merged_after = f"{after_lead}\n\n{after_body}"
        rewrite_ratio = self._estimate_rewrite_ratio(merged_before, merged_after)
        if rewrite_ratio > max_rewrite_ratio:
            return f"{label} rejected: rewrite_ratio={rewrite_ratio:.3f}"
        if self._looks_style_flattened(before_body, after_body):
            return f"{label} rejected: style flattening risk"
        before_headings = self._heading_count(before_body)
        after_headings = self._heading_count(after_body)
        if before_headings and before_headings != after_headings:
            return f"{label} rejected: heading count {before_headings}->{after_headings}"
        return None

    def _detect_grammar_breaks(self, text: str) -> Dict[str, Any]:
        """軽量ルールで文法破綻シグナルを検出する。"""
        sample = (text or "").strip()
        if not sample:
            return {
                "violation_count": 0,
                "violations_per_1k_chars": 0.0,
                "severity": "low",
                "signals": {},
            }

        renyou_break = len(re.findall(r"([一-龥々〆ヵヶ]{1,12})し。(?=[^\n])", sample))
        ori_break = len(re.findall(r"おり。(?=\s*(?:[^\n#\-\*\d]))", sample))
        copula_comma_break = len(
            re.findall(
                r"(?:です|ます)、(?=(?:[一-龥々ぁ-んァ-ヶA-Za-z0-9「『（(]))",
                sample,
            )
        )
        particle_break = len(
            re.findall(
                r"(ことは|ため|ので|によって|として|から|は|が|を|に|で|と|も|へ|より)\。\s*(?:\n\s*)?[^\n#\-\*\d]",
                sample,
            )
        )
        particle_terminal_break = 0
        truncated_verb_break = 0
        non_terminal_sentence_break = 0
        paragraphs = [p for p in re.split(r"\n{2,}", sample) if p.strip()]
        noun_tail_re = re.compile(
            r"(?:こと|もの|ため|点|面|場面|風土|体制|状態|環境|仕組み|文化|課題|方針|傾向|理由|結果|実態|現状)$"
        )
        truncated_verb_re = re.compile(
            r"[一-龥々ぁ-んァ-ヶ]{1,16}(?:わ|ら|り|き|し|ち|み|え|け|せ|て|ね|め|れ|げ|べ|ぜ|で|じ|ぎ|び|ぴ|に|ひ)[。！？!?]$"
        )
        particle_tail_candidates = ("に", "を", "が", "は", "で", "と", "も", "へ", "の", "から", "より", "まで", "ので")
        for para in paragraphs:
            stripped_para = para.strip()
            if stripped_para.startswith("##") or self._is_reference_or_list_paragraph(stripped_para):
                continue
            sentences = [s.strip() for s in _ag("_RE_SENTENCE_SPLIT").split(stripped_para) if s.strip()]
            for sentence in sentences:
                if self._looks_non_terminal_sentence_ending(sentence):
                    non_terminal_sentence_break += 1
                core = sentence.rstrip("。！？!?").strip()
                if core:
                    for particle in particle_tail_candidates:
                        if not core.endswith(particle):
                            continue
                        stem = core[: -len(particle)].rstrip("、, ").strip()
                        if not stem:
                            break
                        if noun_tail_re.search(stem):
                            break
                        if re.search(
                            r"(?:る|た|ない|たい|れる|られる|している|していた|できる|できない|なった|なる|高い|低い|強い|弱い)$",
                            stem,
                        ):
                            particle_terminal_break += 1
                        break
                if (
                    truncated_verb_re.search(sentence)
                    and not re.search(r"(?:つつ|けど|けれど|ものの)[。！？!?]$", sentence)
                ):
                    truncated_verb_break += 1
        register_report = self._analyze_style_register(sample)
        polite_plain_mix_break = 0
        if (
            int(register_report.get("polite_count", 0) or 0) >= 3
            and int(register_report.get("plain_count", 0) or 0) >= 1
        ):
            polite_plain_mix_break = 1
        broken_bold = 1 if sample.count("**") % 2 == 1 else 0
        unbalanced_paren = abs(sample.count("（") - sample.count("）")) + abs(sample.count("(") - sample.count(")"))

        signals = {
            "renyou_break": renyou_break,
            "ori_break": ori_break,
            "copula_comma_break": copula_comma_break,
            "particle_break": particle_break,
            "particle_terminal_break": particle_terminal_break,
            "truncated_verb_break": truncated_verb_break,
            "non_terminal_sentence_break": non_terminal_sentence_break,
            "polite_plain_mix_break": polite_plain_mix_break,
            "broken_bold": broken_bold,
            "unbalanced_paren": unbalanced_paren,
        }
        violation_count = sum(int(v) for v in signals.values())
        normalized_len = max(1, len(re.sub(r"\s+", "", sample)))
        violations_per_1k = round((violation_count * 1000.0) / normalized_len, 4)

        if violation_count >= 4 or violations_per_1k >= 2.8:
            severity = "high"
        elif violation_count >= 2 or violations_per_1k >= 1.2:
            severity = "mid"
        else:
            severity = "low"
        return {
            "violation_count": violation_count,
            "violations_per_1k_chars": violations_per_1k,
            "severity": severity,
            "signals": signals,
        }

    @staticmethod
    def _looks_non_terminal_sentence_ending(sentence: str) -> bool:
        core = (sentence or "").strip()
        if not core:
            return False
        core = core.rstrip("。！？!?").rstrip("、,").strip()
        if len(core) <= 4:
            return False
        if re.search(r"とは違い$", core):
            return True
        return bool(_ag("_RE_NON_TERMINAL_SENTENCE_END").search(core))

    def _repair_sentence_flow_in_line(self, line: str) -> str:
        stripped_line = (line or "").strip()
        if not stripped_line:
            return ""
        # 文脈上つながるべき箇所の最小修復（意味は保持）
        stripped_line = re.sub(r"おり。(?=\s*(?:[^\n#\-\*\d]))", "おり、", stripped_line)
        stripped_line = re.sub(
            r"(です|ます)、(?=(?:[一-龥々ぁ-んァ-ヶA-Za-z0-9「『（(]))",
            r"\1。",
            stripped_line,
        )

        sentences = [s.strip() for s in _ag("_RE_SENTENCE_SPLIT").split(stripped_line) if s.strip()]
        if len(sentences) < 2:
            return stripped_line

        merged: List[str] = []
        idx = 0
        while idx < len(sentences):
            current = sentences[idx].strip()
            if idx < len(sentences) - 1 and self._looks_non_terminal_sentence_ending(current):
                nxt = re.sub(r"^[、,\s]+", "", sentences[idx + 1].strip())
                base = current.rstrip("。！？!?").rstrip("、,").strip()
                if base and nxt:
                    merged.append(f"{base}、{nxt}")
                    idx += 2
                    continue
            merged.append(current)
            idx += 1
        return "".join(seg for seg in merged if seg).strip()

    def _repair_contextual_sentence_breaks(self, text: str) -> str:
        """文脈上つながるべき文の誤分断を局所的に結合する。"""
        if not text:
            return text
        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        rebuilt: List[str] = []
        for para in paragraphs:
            stripped = para.strip()
            if stripped.startswith("##") or self._is_reference_or_list_paragraph(stripped):
                rebuilt.append(para)
                continue

            line_units = [line.strip() for line in para.splitlines() if line.strip()]
            if not line_units:
                rebuilt.append(para.strip())
                continue

            repaired_lines = [self._repair_sentence_flow_in_line(line) for line in line_units]
            repaired_lines = [line for line in repaired_lines if line]
            if not repaired_lines:
                rebuilt.append(para.strip())
                continue

            stabilized_lines: List[str] = []
            for line in repaired_lines:
                if not stabilized_lines:
                    stabilized_lines.append(line)
                    continue

                prev = stabilized_lines[-1].rstrip()
                should_merge = (
                    self._looks_non_terminal_sentence_ending(prev)
                    or self._looks_non_terminal_fragment(prev)
                    or (not self._is_terminal_line(prev) and len(prev) < 110)
                )
                if should_merge:
                    stabilized_lines[-1] = prev + line.lstrip()
                else:
                    stabilized_lines.append(line)

            rebuilt.append("\n".join(seg for seg in stabilized_lines if seg).strip())

        return "\n\n".join(block for block in rebuilt if block.strip()).strip()

    def _semantic_token_set(self, text: str, *, max_chars: int = 900, max_terms: int = 40) -> set:
        terms = self._extract_content_terms(text or "", max_chars=max_chars)
        if not terms:
            return set()
        unique: List[str] = []
        seen: set = set()
        for token in terms:
            if token in seen:
                continue
            seen.add(token)
            unique.append(token)
            if len(unique) >= max_terms:
                break
        return set(unique)

    def _compute_semantic_layout_metrics(self, text: str) -> Dict[str, Any]:
        """見出し整合・遷移自然性・唐突開始を定量化する。"""
        empty = {
            "section_count": 0,
            "heading_alignment_mean": 0.0,
            "heading_alignment_min": 0.0,
            "heading_alignment_low_count": 0,
            "transition_jaccard_mean": 0.0,
            "transition_jaccard_min": 0.0,
            "transition_low_count": 0,
            "abrupt_opening_count": 0,
            "abrupt_opening_ratio": 0.0,
            "heading_repetition_count": 0,
            "semantic_issue_count": 0,
        }

        sample = (text or "").strip()
        if not sample:
            return dict(empty)

        sections = self._extract_section_blocks(sample)
        if not sections:
            return dict(empty)

        heading_align_scores: List[float] = []
        transition_scores: List[float] = []
        heading_alignment_low_count = 0
        transition_low_count = 0
        abrupt_opening_count = 0
        heading_repetition_count = 0
        section_term_sets: List[set] = []

        abrupt_opening_re = re.compile(
            r"^[「『（(]*(?:生み出す|紡ぎ出す|見落としてはいけない|求められる|問われる|欠かせない|"
            r"[一-龥々〆ヵヶぁ-んァ-ヶ]{2,12}(?:し|して|した|する|できる|できない|なり|なる))"
        )
        heading_repeat_re = re.compile(r"(.{2,12})を\1")

        for heading, content in sections:
            body = (content or "").strip()
            sentences = [s.strip() for s in _ag("_RE_SENTENCE_SPLIT").split(body) if s.strip()]
            first_sentence = sentences[0] if sentences else ""

            heading_terms = self._semantic_token_set(heading, max_chars=120, max_terms=20)
            first_terms = self._semantic_token_set(first_sentence, max_chars=220, max_terms=24)
            if heading_terms and first_terms:
                overlap = len(heading_terms & first_terms)
                denom = max(1, min(len(heading_terms), len(first_terms)))
                align = overlap / denom
            else:
                align = 0.0
            heading_align_scores.append(align)
            if align < 0.08:
                heading_alignment_low_count += 1

            if first_sentence and abrupt_opening_re.match(first_sentence):
                abrupt_opening_count += 1

            if heading_repeat_re.search((heading or "").strip()):
                heading_repetition_count += 1

            section_term_sets.append(self._semantic_token_set(body, max_chars=1200, max_terms=48))

        for idx in range(len(section_term_sets) - 1):
            left = section_term_sets[idx]
            right = section_term_sets[idx + 1]
            union = left | right
            inter = left & right
            jaccard = (len(inter) / max(1, len(union))) if union else 0.0
            transition_scores.append(jaccard)
            if jaccard < 0.01:
                transition_low_count += 1

        section_count = len(sections)
        abrupt_opening_ratio = (
            abrupt_opening_count / max(1, section_count) if section_count > 0 else 0.0
        )
        semantic_issue_count = (
            heading_alignment_low_count + transition_low_count + heading_repetition_count
        )
        if section_count >= 3 and abrupt_opening_ratio > 0.34:
            semantic_issue_count += 1

        return {
            "section_count": section_count,
            "heading_alignment_mean": round(sum(heading_align_scores) / max(1, len(heading_align_scores)), 4),
            "heading_alignment_min": round(min(heading_align_scores), 4) if heading_align_scores else 0.0,
            "heading_alignment_low_count": heading_alignment_low_count,
            "transition_jaccard_mean": round(sum(transition_scores) / max(1, len(transition_scores)), 4),
            "transition_jaccard_min": round(min(transition_scores), 4) if transition_scores else 0.0,
            "transition_low_count": transition_low_count,
            "abrupt_opening_count": abrupt_opening_count,
            "abrupt_opening_ratio": round(abrupt_opening_ratio, 4),
            "heading_repetition_count": heading_repetition_count,
            "semantic_issue_count": semantic_issue_count,
        }

    def _check_contextual_naturalness(self, text: str) -> Dict[str, Any]:
        """非終止の文末分断が残っていないかをチェックする。"""
        sample = (text or "").strip()
        if not sample:
            return {
                "issue_count": 0,
                "issues": [],
                "instructional_fragment_count": 0,
                "soft_issue_count": 0,
                "soft_issues": [],
                "sentence_count": 0,
                "connective_opening_ratio": 0.0,
                "topic_opening_ratio": 0.0,
                "ellipsis_opening_ratio": 0.0,
                "awkward_ending_count": 0,
                "awkward_ending_ratio": 0.0,
                "ai_template_ending_count": 0,
                "ai_template_ending_ratio": 0.0,
                "connector_collision_count": 0,
                "semantic_layout": {
                    "section_count": 0,
                    "heading_alignment_mean": 0.0,
                    "heading_alignment_min": 0.0,
                    "heading_alignment_low_count": 0,
                    "transition_jaccard_mean": 0.0,
                    "transition_jaccard_min": 0.0,
                    "transition_low_count": 0,
                    "abrupt_opening_count": 0,
                    "abrupt_opening_ratio": 0.0,
                    "heading_repetition_count": 0,
                    "semantic_issue_count": 0,
                },
                "passed": True,
            }

        issues: List[Dict[str, Any]] = []
        soft_issues: List[Dict[str, Any]] = []
        awkward_leadin_re = re.compile(
            r"^(?:心がけているのは|目指しているのは)(?:、|,)?(?:たとえば|例えば)(?:、|,)?"
        )
        adversative_opening_re = re.compile(
            r"^(?:しかし|ただし|ただ|とはいえ|けれども|それでも)(?:、|,)?"
        )
        malformed_connector_re = re.compile(
            r"(?:ただながら|そのためこそ|というわけでこそ|和らげるになります)"
        )
        connector_collision_re = re.compile(
            r"(?:単に|ただ|あくまで|むしろ)[^。！？\n]{0,10}(?:そのため|しかし|ただし)"
        )
        awkward_ending_patterns = (
            ("awkward_adj_terminal", re.compile(r"(?:にくい|づらい)なの(?:です|だ)(?:[。！？!?])?$")),
            ("particle_topic_collision", re.compile(r"を[^。！？\n]{0,16}が(?:大切|重要|必要|不可欠)(?:です|だ)(?:[。！？!?])?$")),
        )
        ai_template_ending_patterns = (
            re.compile(r"(?:必要があると考えます|必要だと考えます)(?:[。！？!?])?$"),
            re.compile(r"(?:ことが)?見えてきます(?:[。！？!?])?$"),
            re.compile(r"欠かせません(?:[。！？!?])?$"),
            re.compile(r"見逃せません(?:[。！？!?])?$"),
        )
        topic_opening_re = re.compile(r"^[「『（(]*[一-龥々〆ヵヶぁ-んァ-ヶA-Za-z0-9]{1,12}(?:は|が)")
        ellipsis_opening_re = re.compile(
            r"^[「『（(]*(?:生み出す|紡ぎ出す|見落としてはいけない|求められる|問われる|欠かせない|"
            r"[一-龥々〆ヵヶぁ-んァ-ヶ]{2,12}(?:し|して|した|する|できる|できない|なり|なる))"
        )
        total_body_sentences = 0
        connective_opening_hits = 0
        topic_opening_hits = 0
        ellipsis_opening_hits = 0
        awkward_ending_hits = 0
        ai_template_ending_hits = 0
        connector_collision_hits = 0
        instructional_fragment_hits = 0
        paragraphs = [p for p in re.split(r"\n{2,}", sample) if p.strip()]
        prev_was_heading = False
        for para_idx, para in enumerate(paragraphs):
            stripped = para.strip()
            if stripped.startswith("##") or self._is_reference_or_list_paragraph(stripped):
                prev_was_heading = stripped.startswith("##")
                continue
            sentences = [s.strip() for s in _ag("_RE_SENTENCE_SPLIT").split(para) if s.strip()]
            if not sentences:
                prev_was_heading = False
                continue
            if (
                prev_was_heading
                and len(soft_issues) < 12
                and adversative_opening_re.match(sentences[0])
            ):
                soft_issues.append(
                    {
                        "paragraph_index": para_idx,
                        "sentence_index": 0,
                        "type": "adversative_opening_after_heading",
                        "sentence": sentences[0][:80],
                    }
                )
            for sent_idx, sentence in enumerate(sentences):
                total_body_sentences += 1
                prompt_echo_hits = self._detect_prompt_echo(sentence, max_hits=1)
                if prompt_echo_hits:
                    instructional_fragment_hits += 1
                    issues.append(
                        {
                            "paragraph_index": para_idx,
                            "sentence_index": sent_idx,
                            "type": "instructional_fragment",
                            "sentence": prompt_echo_hits[0],
                        }
                    )
                    if len(issues) >= 12:
                        break
                    continue
                if any(re.match(pattern, sentence) for pattern in AI_LIKE_OPENING_PATTERNS):
                    connective_opening_hits += 1
                if topic_opening_re.match(sentence):
                    topic_opening_hits += 1
                if ellipsis_opening_re.match(sentence):
                    ellipsis_opening_hits += 1
                if len(soft_issues) < 12 and awkward_leadin_re.match(sentence):
                    soft_issues.append(
                        {
                            "paragraph_index": para_idx,
                            "sentence_index": sent_idx,
                            "type": "awkward_leadin",
                            "sentence": sentence[:80],
                        }
                    )
                if len(soft_issues) < 12 and malformed_connector_re.search(sentence):
                    soft_issues.append(
                        {
                            "paragraph_index": para_idx,
                            "sentence_index": sent_idx,
                            "type": "malformed_connector",
                            "sentence": sentence[:80],
                        }
                    )
                if connector_collision_re.search(sentence):
                    connector_collision_hits += 1
                    if len(soft_issues) < 12:
                        soft_issues.append(
                            {
                                "paragraph_index": para_idx,
                                "sentence_index": sent_idx,
                                "type": "connector_collision",
                                "sentence": sentence[:80],
                            }
                        )
                for issue_type, pattern in awkward_ending_patterns:
                    if not pattern.search(sentence):
                        continue
                    awkward_ending_hits += 1
                    if len(soft_issues) < 12:
                        soft_issues.append(
                            {
                                "paragraph_index": para_idx,
                                "sentence_index": sent_idx,
                                "type": issue_type,
                                "sentence": sentence[:80],
                            }
                        )
                    break
                if any(pattern.search(sentence) for pattern in ai_template_ending_patterns):
                    ai_template_ending_hits += 1
                if (
                    sent_idx < len(sentences) - 1 or len(sentences) == 1
                ) and self._looks_non_terminal_sentence_ending(sentence):
                    issues.append(
                        {
                            "paragraph_index": para_idx,
                            "sentence_index": sent_idx,
                            "type": "non_terminal_sentence_ending",
                            "sentence": sentence[:80],
                        }
                    )
                    if len(issues) >= 12:
                        break
            if len(issues) >= 12:
                break
            prev_was_heading = False

        connective_ratio = (
            connective_opening_hits / max(1, total_body_sentences)
            if total_body_sentences > 0
            else 0.0
        )
        topic_opening_ratio = (
            topic_opening_hits / max(1, total_body_sentences)
            if total_body_sentences > 0
            else 0.0
        )
        ellipsis_opening_ratio = (
            ellipsis_opening_hits / max(1, total_body_sentences)
            if total_body_sentences > 0
            else 0.0
        )
        awkward_ending_ratio = (
            awkward_ending_hits / max(1, total_body_sentences)
            if total_body_sentences > 0
            else 0.0
        )
        ai_template_ending_ratio = (
            ai_template_ending_hits / max(1, total_body_sentences)
            if total_body_sentences > 0
            else 0.0
        )
        if total_body_sentences >= 8 and connective_ratio > 0.24 and len(soft_issues) < 12:
            soft_issues.append(
                {
                    "type": "connective_opening_high",
                    "connective_opening_ratio": round(connective_ratio, 4),
                    "sentence_count": total_body_sentences,
                }
            )
        template_ending_limit = max(2, int(total_body_sentences * 0.05) + 1)
        if (
            total_body_sentences >= 8
            and ai_template_ending_hits > template_ending_limit
            and len(soft_issues) < 12
        ):
            soft_issues.append(
                {
                    "type": "ai_template_ending_overuse",
                    "ai_template_ending_count": ai_template_ending_hits,
                    "ai_template_ending_ratio": round(ai_template_ending_ratio, 4),
                    "max_recommended": template_ending_limit,
                    "sentence_count": total_body_sentences,
                }
            )
        if total_body_sentences >= 8 and ellipsis_opening_ratio > 0.28 and len(soft_issues) < 12:
            soft_issues.append(
                {
                    "type": "ellipsis_opening_high",
                    "ellipsis_opening_ratio": round(ellipsis_opening_ratio, 4),
                    "sentence_count": total_body_sentences,
                }
            )

        semantic_layout = self._compute_semantic_layout_metrics(sample)
        semantic_issue_count = int(semantic_layout.get("semantic_issue_count", 0) or 0)
        if semantic_layout.get("heading_repetition_count", 0) > 0 and len(soft_issues) < 12:
            soft_issues.append(
                {
                    "type": "heading_repetition_detected",
                    "heading_repetition_count": int(
                        semantic_layout.get("heading_repetition_count", 0) or 0
                    ),
                }
            )
        if semantic_layout.get("heading_alignment_low_count", 0) > 0 and len(soft_issues) < 12:
            soft_issues.append(
                {
                    "type": "heading_alignment_low",
                    "heading_alignment_low_count": int(
                        semantic_layout.get("heading_alignment_low_count", 0) or 0
                    ),
                    "heading_alignment_mean": float(
                        semantic_layout.get("heading_alignment_mean", 0.0) or 0.0
                    ),
                }
            )
        if semantic_layout.get("transition_low_count", 0) > 0 and len(soft_issues) < 12:
            soft_issues.append(
                {
                    "type": "section_transition_low",
                    "transition_low_count": int(semantic_layout.get("transition_low_count", 0) or 0),
                    "transition_jaccard_mean": float(
                        semantic_layout.get("transition_jaccard_mean", 0.0) or 0.0
                    ),
                }
            )
        if (
            int(semantic_layout.get("section_count", 0) or 0) >= 3
            and float(semantic_layout.get("abrupt_opening_ratio", 0.0) or 0.0) > 0.34
            and len(soft_issues) < 12
        ):
            soft_issues.append(
                {
                    "type": "abrupt_opening_ratio_high",
                    "abrupt_opening_ratio": float(
                        semantic_layout.get("abrupt_opening_ratio", 0.0) or 0.0
                    ),
                }
            )

        return {
            "issue_count": len(issues),
            "issues": issues,
            "instructional_fragment_count": instructional_fragment_hits,
            "soft_issue_count": len(soft_issues),
            "soft_issues": soft_issues,
            "sentence_count": total_body_sentences,
            "connective_opening_ratio": round(connective_ratio, 4),
            "topic_opening_ratio": round(topic_opening_ratio, 4),
            "ellipsis_opening_ratio": round(ellipsis_opening_ratio, 4),
            "awkward_ending_count": awkward_ending_hits,
            "awkward_ending_ratio": round(awkward_ending_ratio, 4),
            "ai_template_ending_count": ai_template_ending_hits,
            "ai_template_ending_ratio": round(ai_template_ending_ratio, 4),
            "connector_collision_count": connector_collision_hits,
            "semantic_layout": semantic_layout,
            "semantic_issue_count": semantic_issue_count,
            "passed": len(issues) == 0,
        }

    def _build_repair_only_prompt(
        self,
        *,
        lead: str,
        body: str,
        merged_context: str,
        article_type: str,
        target_audience: str,
    ) -> str:
        writing_focus_guide = self._get_writing_focus_guide()
        editor_persona_block = self._build_editor_persona_block(
            pass_type="repair_only",
            article_type=article_type,
        )
        return f"""
あなたは日本語校正者です。lead/body を「文法の最小修復」だけ実行してください。
{editor_persona_block}

【記事タイプ】
{_ag("ARTICLE_TYPE_LABELS").get(article_type, article_type)}

【ターゲット読者】
{target_audience or "一般読者"}

【本文の重心】
{writing_focus_guide or "自動判定"}

【参考情報（抜粋）】
{(merged_context or "")[:1300] if merged_context else "なし"}

【許可される修正】
- 助詞抜け・係り受け崩れ・誤字脱字・句読点の明確な破綻
- 「調整し。次に〜」のような連用中止の誤切断修正
- 括弧や太字マーカーの明確な閉じ忘れ修正

【禁止】
- 要約、言い換え、主張の追加・削除
- 段落結合/分割や見出し改変
- 文体の均一化、口調の硬化

【入力】
[LEAD]
{lead}

[BODY]
{body}

【出力形式】
JSONのみ:
{{"lead":"...","body":"..."}}
""".strip()

    def _should_use_repair_only_llm(self, report: Dict[str, Any], *, body_chars: int, cfg: Dict[str, Any]) -> bool:
        trigger = str(cfg.get("llm_trigger_severity", "high"))
        if trigger == "off":
            return False
        if body_chars < int(cfg.get("min_chars_for_llm", 260) or 260):
            return False
        severity = str(report.get("severity", "low"))
        if trigger == "mid":
            return severity in ("mid", "high")
        return severity == "high"

    def _run_repair_only_pass(
        self,
        lead: str,
        body: str,
        *,
        merged_context: str,
        article_type: str,
        target_audience: str,
    ) -> Tuple[str, str]:
        cfg = self._get_postprocess_config()
        repair_cfg = cfg.get("repair_only", {}) if isinstance(cfg, dict) else {}
        if not isinstance(repair_cfg, dict):
            repair_cfg = {}

        enabled = bool(repair_cfg.get("enabled", False))
        mode = str(repair_cfg.get("mode", "shadow"))
        merged = f"{lead or ''}\n\n{body or ''}"
        report_before = self._detect_grammar_breaks(merged)
        self._last_repair_only_report = {
            "enabled": enabled,
            "mode": mode,
            "before": report_before,
            "applied": False,
            "guard_rejected": False,
            "error": "",
        }
        if not enabled or mode == "off":
            return lead, body

        should_call_llm = self._should_use_repair_only_llm(
            report_before,
            body_chars=len(body or ""),
            cfg=repair_cfg,
        )
        if mode == "shadow" or not should_call_llm:
            self._last_repair_only_report["would_call_llm"] = bool(should_call_llm)
            return lead, body

        prompt = self._build_repair_only_prompt(
            lead=lead,
            body=body,
            merged_context=merged_context,
            article_type=article_type,
            target_audience=target_audience,
        )
        rewrite_cap = float(repair_cfg.get("rewrite_ratio_cap", 0.08) or 0.08)
        try:
            raw = self.llm.generate_text(
                prompt,
                max_tokens=min(2200, max(800, int((len(lead) + len(body)) * 0.8))),
                task_type="repair_only",
            ).strip()
        except Exception as exc:
            logger.warning(
                "repair_only pass failed. Keep original text. (%s: %s)",
                type(exc).__name__,
                exc,
            )
            self._last_repair_only_report["error"] = str(exc)
            return lead, body

        if not raw:
            return lead, body
        try:
            match = re.search(r"\{.*\}", raw, re.S)
            if not match:
                return lead, body
            data = json.loads(match.group(0))
            new_lead = data.get("lead")
            new_body = data.get("body")
            if not (isinstance(new_lead, str) and isinstance(new_body, str)):
                return lead, body
            repaired_lead = new_lead.strip() or lead
            repaired_body = new_body.strip() or body
            rejection = self._rewrite_guard_check(
                lead,
                body,
                repaired_lead,
                repaired_body,
                max_rewrite_ratio=rewrite_cap,
                label="repair_only",
            )
            if rejection:
                logger.info("%s", rejection)
                self._last_repair_only_report["guard_rejected"] = True
                return lead, body
            after_report = self._detect_grammar_breaks(f"{repaired_lead}\n\n{repaired_body}")
            self._last_repair_only_report.update({
                "applied": True,
                "after": after_report,
            })
            return repaired_lead, repaired_body
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.debug("repair_only JSON parse failed. Keep original text.", exc_info=exc)
            self._last_repair_only_report["error"] = str(exc)
            return lead, body

    def _evaluate_hard_soft_thresholds(
        self,
        *,
        before_lead: str,
        before_body: str,
        after_lead: str,
        after_body: str,
    ) -> Dict[str, Any]:
        cfg = self._get_section_generation_config()
        hs_cfg = cfg.get("hard_soft_thresholds", {}) if isinstance(cfg, dict) else {}
        if not isinstance(hs_cfg, dict):
            hs_cfg = {}
        enabled = bool(hs_cfg.get("enabled", False))
        mode = str(hs_cfg.get("mode", "shadow"))
        if not enabled or mode == "off":
            return {"enabled": False, "mode": mode}

        merged_before = f"{before_lead or ''}\n\n{before_body or ''}"
        merged_after = f"{after_lead or ''}\n\n{after_body or ''}"
        rewrite_ratio = self._estimate_rewrite_ratio(merged_before, merged_after)
        heading_delta = self._heading_count(after_body) - self._heading_count(before_body)
        grammar_report = self._detect_grammar_breaks(merged_after)
        grammar_per_1k = float(grammar_report.get("violations_per_1k_chars", 0.0) or 0.0)
        naturalness_report = self._check_contextual_naturalness(merged_after)
        self._last_contextual_naturalness_report = dict(naturalness_report or {})
        semantic_layout = naturalness_report.get("semantic_layout", {})
        if not isinstance(semantic_layout, dict):
            semantic_layout = {}
        semantic_issue_count = int(
            naturalness_report.get(
                "semantic_issue_count",
                semantic_layout.get("semantic_issue_count", 0),
            )
            or 0
        )
        ai_template_ending_count = int(
            naturalness_report.get("ai_template_ending_count", 0) or 0
        )
        ai_template_ending_ratio = float(
            naturalness_report.get("ai_template_ending_ratio", 0.0) or 0.0
        )
        instructional_fragment_count = int(
            naturalness_report.get("instructional_fragment_count", 0) or 0
        )

        hard_fail_reasons: List[str] = []
        hard_max_rewrite = float(hs_cfg.get("hard_max_rewrite_ratio", 0.20) or 0.20)
        if rewrite_ratio > hard_max_rewrite:
            hard_fail_reasons.append(f"rewrite_ratio>{hard_max_rewrite:.2f}")

        hard_max_grammar = float(hs_cfg.get("hard_max_grammar_breaks_per_1k", 3.0) or 3.0)
        if grammar_per_1k > hard_max_grammar:
            hard_fail_reasons.append(f"grammar_per_1k>{hard_max_grammar:.2f}")

        preserve_headings = bool(hs_cfg.get("hard_preserve_headings", True))
        if preserve_headings and heading_delta != 0:
            hard_fail_reasons.append("heading_count_changed")
        if instructional_fragment_count > 0:
            hard_fail_reasons.append("instructional_fragment_detected")

        soft_unpredictability = 0.0
        soft_flat_zone_count = 0
        try:
            fp_report = self._fingerprint_analyzer.analyze(
                after_body or "",
                focus=self._get_effective_writing_focus(),
            )
            soft_unpredictability = float(fp_report.overall_unpredictability or 0.0)
            soft_flat_zone_count = int(len(fp_report.flat_zone_flags or []))
        except Exception as exc:
            logger.debug("Hard/soft fingerprint check failed (shadow keep).", exc_info=exc)

        soft_min_unpredictability = float(hs_cfg.get("soft_min_unpredictability", 0.45) or 0.45)
        soft_max_flat_zone_count = int(hs_cfg.get("soft_max_flat_zone_count", 6) or 6)
        soft_max_semantic_issue_count = max(
            0,
            int(hs_cfg.get("soft_max_semantic_issue_count", 2) or 2),
        )
        soft_max_ai_template_ending_count = max(
            1,
            int(hs_cfg.get("soft_max_ai_template_ending_count", 3) or 3),
        )
        soft_warnings: List[str] = []
        if soft_unpredictability < soft_min_unpredictability:
            soft_warnings.append(f"unpredictability<{soft_min_unpredictability:.2f}")
        if soft_flat_zone_count > soft_max_flat_zone_count:
            soft_warnings.append(f"flat_zone_count>{soft_max_flat_zone_count}")
        if semantic_issue_count > soft_max_semantic_issue_count:
            soft_warnings.append(f"semantic_issue_count>{soft_max_semantic_issue_count}")
        if ai_template_ending_count > soft_max_ai_template_ending_count:
            soft_warnings.append(
                f"ai_template_ending_count>{soft_max_ai_template_ending_count}"
            )

        return {
            "enabled": True,
            "mode": mode,
            "hard_failed": bool(hard_fail_reasons),
            "hard_fail_reasons": hard_fail_reasons,
            "soft_warnings": soft_warnings,
            "metrics": {
                "rewrite_ratio": round(rewrite_ratio, 4),
                "heading_delta": heading_delta,
                "grammar_per_1k": round(grammar_per_1k, 4),
                "unpredictability": round(soft_unpredictability, 4),
                "flat_zone_count": soft_flat_zone_count,
                "semantic_issue_count": semantic_issue_count,
                "instructional_fragment_count": instructional_fragment_count,
                "ai_template_ending_count": ai_template_ending_count,
                "ai_template_ending_ratio": round(ai_template_ending_ratio, 4),
                "heading_alignment_mean": round(
                    float(semantic_layout.get("heading_alignment_mean", 0.0) or 0.0),
                    4,
                ),
                "transition_jaccard_mean": round(
                    float(semantic_layout.get("transition_jaccard_mean", 0.0) or 0.0),
                    4,
                ),
                "abrupt_opening_ratio": round(
                    float(semantic_layout.get("abrupt_opening_ratio", 0.0) or 0.0),
                    4,
                ),
            },
        }

    @staticmethod
    def _soft_warning_eval_score(eval_payload: Dict[str, Any]) -> Tuple[int, int, int, int, float]:
        """Lower is better for warnings/issue counts; higher unpredictability is better."""
        warnings = eval_payload.get("soft_warnings", [])
        if not isinstance(warnings, list):
            warnings = []
        metrics = eval_payload.get("metrics", {})
        if not isinstance(metrics, dict):
            metrics = {}
        return (
            len(warnings),
            int(metrics.get("semantic_issue_count", 0) or 0),
            int(metrics.get("flat_zone_count", 0) or 0),
            int(metrics.get("ai_template_ending_count", 0) or 0),
            -float(metrics.get("unpredictability", 0.0) or 0.0),
        )

    def _try_soft_warning_fix_pass(
        self,
        *,
        before_lead: str,
        before_body: str,
        current_lead: str,
        current_body: str,
        current_eval: Dict[str, Any],
    ) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """Apply a conservative fix pass only when it improves soft-warning score."""
        if not isinstance(current_eval, dict) or not current_eval.get("enabled"):
            return None
        if current_eval.get("hard_failed"):
            return None

        soft_warnings = current_eval.get("soft_warnings", [])
        if not isinstance(soft_warnings, list) or not soft_warnings:
            return None

        cfg = self._get_section_generation_config()
        hs_cfg = cfg.get("hard_soft_thresholds", {}) if isinstance(cfg, dict) else {}
        if not isinstance(hs_cfg, dict):
            hs_cfg = {}
        if not bool(hs_cfg.get("soft_autofix_enabled", True)):
            return None

        fixed_lead = self._clean_redundant_connectives(current_lead)
        fixed_body = self._clean_redundant_connectives(current_body)
        fixed_body = self._strip_heading_top_adversative(fixed_body)
        fixed_lead = self._break_ending_monotony(fixed_lead)
        fixed_body = self._break_ending_monotony(fixed_body)
        if self._get_active_style_profile() != "casual":
            fixed_lead = self._cap_colloquial_endings(fixed_lead)
            fixed_body = self._cap_colloquial_endings(fixed_body)

        if fixed_lead == current_lead and fixed_body == current_body:
            return None

        rejection = self._rewrite_guard_check(
            current_lead,
            current_body,
            fixed_lead,
            fixed_body,
            max_rewrite_ratio=0.06,
            label="soft_warning_fix",
        )
        if rejection:
            logger.info("%s", rejection)
            return None

        fixed_eval = self._evaluate_hard_soft_thresholds(
            before_lead=before_lead,
            before_body=before_body,
            after_lead=fixed_lead,
            after_body=fixed_body,
        )
        if not isinstance(fixed_eval, dict) or fixed_eval.get("hard_failed"):
            return None

        current_score = self._soft_warning_eval_score(current_eval)
        fixed_score = self._soft_warning_eval_score(fixed_eval)
        if fixed_score < current_score:
            logger.info(
                "Soft-warning fix applied: warnings %s -> %s",
                len(soft_warnings),
                len(fixed_eval.get("soft_warnings", []) or []),
            )
            return fixed_lead, fixed_body, fixed_eval
        return None

    def _run_final_quality_eval_pass(
        self,
        *,
        before_lead: str,
        before_body: str,
        final_lead: str,
        final_body: str,
    ) -> None:
        """Deprecated: final_quality_eval is no longer used for guard decisions."""
        self._last_final_quality_eval = {}
        _ = (before_lead, before_body, final_lead, final_body)

    def _build_quality_context(
        self,
        platform: str,
        perspective: str,
        focus: str,
        source_text: Optional[str],
    ) -> Dict[str, Any]:
        policy = getattr(self, "_pipeline_policy", {}) or {}
        category_policy = getattr(self, "_category_policy", {}) or {}
        article_type = str(getattr(self, "_current_type", "") or "")
        is_custom_genre = article_type not in _ag("ARTICLE_TYPE_PROMPTS")
        source_cfg = self._get_source_reading_config()
        quality_source_max_chars = int(
            source_cfg.get("quality_context_source_text_max_chars", 12000) or 12000
        )
        return {
            "platform": platform,
            "perspective": perspective,
            "writing_focus": focus,
            "article_type": article_type,
            "category_base_template": str(category_policy.get("base_template", "") or ""),
            "category_policy_source": str(category_policy.get("source", "") or ""),
            "tone_profile_hint": str(
                policy.get("tone_profile", "") or getattr(self, "_effective_tone_profile", "")
            ),
            "style_profile_hint": str(policy.get("style_profile", "") or ""),
            "is_custom_genre": bool(is_custom_genre),
            "custom_genre_key": article_type if is_custom_genre else "",
            "allow_experience": bool(getattr(self, "_allow_experience", True)),
            "topic_hint": getattr(self, "_latest_user_prompt", ""),
            "writing_intent": self._interview_answers.get("message", "") or self._get_writing_focus_guide(),
            "target_audience": self._interview_answers.get("target", ""),
            "source_urls": list(getattr(self, "_source_urls", [])),
            "source_text": (source_text or "")[:quality_source_max_chars],
        }

    def _collect_review_points(self, text: str) -> List[str]:
        """Human review checkpoints (lightweight; no LLM)."""
        if not text:
            return []

        points: List[str] = []

        def _push(label: str) -> None:
            if label and label not in points:
                points.append(label)

        risk_patterns = [
            (r"(No\.?1|ナンバーワン|世界一|世界初|業界初|日本一|最高|最強|唯一|唯一無二|最安|限定|今だけ)", "最上級/限定の断定表現"),
            (r"(治る|治療効果|効果がある|効能|アンチエイジング|若返|痩せる|ダイエット効果|美白効果|シミが消)", "効果効能の断定表現"),
            (r"(絶対|必ず|確実|100%)", "断定的な結果・保証表現"),
            (r"(無料|0円|割引|返金|全額返金|永久保証|永年)", "価格/条件/保証の強い表現"),
            (r"(詐欺|インチキ|悪徳|ブラック企業)", "他社への否定的表現"),
        ]
        for pattern, label in risk_patterns:
            if re.search(pattern, text):
                _push(label)

        # 1) 見出し構成（導入→本論→結論）の最低限チェック
        headings = [h.strip() for h in re.findall(r"^##\s+(.+)$", text, re.MULTILINE)]
        content_headings = [
            h for h in headings if not re.search(r"(参考資料|参考文献|出典)", h, re.IGNORECASE)
        ]
        if len(content_headings) < 2:
            _push("見出し構成不足（導入・本論・結論の区切り）")
        else:
            intro_pattern = r"(はじめに|導入|背景|概要|問題提起|課題|出発点|きっかけ)"
            closing_pattern = (
                r"(まとめ|結論|おわり|最後に|要点|次の一歩|一歩|行動|これから|未来|"
                r"判断ポイント|実務ポイント|チェックリスト)"
            )
            has_intro = any(re.search(intro_pattern, h, re.IGNORECASE) for h in content_headings[:2])
            has_closing = any(
                re.search(closing_pattern, h, re.IGNORECASE) for h in content_headings[-2:]
            )
            if not has_intro or not has_closing:
                _push("見出し順の一貫性不足（導入→本論→結論）")

            first_closing_idx = next(
                (
                    idx
                    for idx, heading in enumerate(content_headings)
                    if re.search(closing_pattern, heading, re.IGNORECASE)
                ),
                None,
            )
            if first_closing_idx is not None and first_closing_idx < max(1, len(content_headings) // 2):
                _push("結論見出しが早すぎる可能性")

        # 2) 段落単位の論点過密チェック
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
        opening_phrases: List[str] = []
        for paragraph in paragraphs:
            normalized_paragraph = re.sub(r"^#+\s+.*$", "", paragraph, flags=re.MULTILINE).strip()
            if (
                not normalized_paragraph
                or normalized_paragraph.startswith("- ")
                or normalized_paragraph.startswith("出典:")
                or re.match(r"^https?://", normalized_paragraph)
            ):
                continue
            sentence_count = len(re.findall(r"[。！？]", normalized_paragraph))
            if len(normalized_paragraph) > 180 and sentence_count >= 5:
                _push("段落が長く論点が混在（1段落1トピック推奨）")
                break
            first_sentence = re.split(r"[。！？]", normalized_paragraph, maxsplit=1)[0].strip()
            first_sentence = re.sub(r"\s+", "", first_sentence)
            if len(first_sentence) >= 8:
                opening_phrases.append(first_sentence[:14])

        if opening_phrases:
            unique_openings = len(set(opening_phrases))
            duplicate_count = len(opening_phrases) - unique_openings
            if len(opening_phrases) >= 4 and duplicate_count >= 2:
                _push("導入句の反復（AI定型の可能性）")

        # 3) 文体混在チェック（丁寧体×常体 / 丁寧体×会話口調）
        register_report = self._analyze_style_register(text)
        polite_hits = len(re.findall(r"(です|ます|でした|ました)(。|、|$)", text))
        casual_hits = len(
            re.findall(r"(ですよね|ですね|だよね|じゃない|でしょうかね|かもです|かな[？?])", text)
        )
        if register_report.get("mixed"):
            _push("文体混在（です・ます調とだ・である調が混在）")
        elif polite_hits >= 3 and casual_hits >= 2:
            _push("文体混在（丁寧文と会話調が混在）")

        # 4) 曖昧な件数表現チェック
        if re.search(r"(多くの件|多数の件|複数の件|いくつかの件|数多くの件)", text):
            _push("数値表現が曖昧（件数を具体化）")

        # 5) 出典表記の文字化け・重複チェック
        reference_zone = ""
        heading_match = re.search(r"^##\s*(参考資料|参考文献|参考文献・出典).*$", text, re.MULTILINE)
        if heading_match:
            reference_zone = text[heading_match.start():]
        elif "出典:" in text:
            reference_zone = text[text.find("出典:") :]
        if reference_zone and re.search(r"(?:ã|ã|ã|ï¼|�)", reference_zone):
            _push("出典テキストに文字化けの可能性")

        if "出典:" in text and re.search(r"^##\s*(参考資料|参考文献|参考文献・出典).*$", text, re.MULTILINE):
            inline_zone = text.split("## 参考", 1)[0]
            inline_urls = set(re.findall(r"https?://[^\s)>]+", inline_zone))
            reference_urls = set(re.findall(r"https?://[^\s)>]+", reference_zone))
            duplicate_url_count = len(inline_urls & reference_urls)
            if duplicate_url_count >= 3:
                _push("出典表記の重複（本文出典と末尾参考）")

        return points[:5]
