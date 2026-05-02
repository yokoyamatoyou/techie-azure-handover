"""article_final_consistency_mixin.py - Final consistency helpers for ArticleGenerator."""
from __future__ import annotations

import logging
import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from human_resonance.style_policy import (
    AI_LIKE_ENDING_REWRITES,
    AI_LIKE_HEADING_REWRITES,
    AI_LIKE_OPENING_PATTERNS,
    LOGICAL_REQUIRED_OPENING_PREFIXES,
    SUPPRESSIBLE_TEMPLATE_OPENING_PREFIXES,
)
from note.legacy_current import article_runtime_symbols as _runtime_symbols

logger = logging.getLogger(__name__)

_cached_ag: Dict[str, Any] = {}


def _ag(name: str) -> Any:
    """Lazy accessor to avoid hard dependencies on note.article_generator."""
    if name not in _cached_ag:
        _cached_ag[name] = getattr(_runtime_symbols, name)
    return _cached_ag[name]


class ArticleFinalConsistencyMixin:
    """Mixin providing final consistency, dedupe, and register-normalization helpers."""

    _ENDING_MASU_RE = re.compile(r"ます。(?:\*\*)?$")
    _ENDING_DESU_RE = re.compile(r"です。(?:\*\*)?$")

    def _dedupe_lead_body(self, lead: str, body: str) -> Tuple[str, str]:
        if not lead or not body:
            return lead, body

        paragraphs = [p for p in re.split(r"\n{2,}", body) if p.strip()]
        if not paragraphs:
            return lead, body

        first_para = paragraphs[0].strip()
        if not first_para:
            return lead, body

        def _normalize(text: str) -> str:
            text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
            text = re.sub(r"\s+", "", text)
            text = re.sub(r"[、。．，,！!？?…・「」『』（）()\[\]【】<>\"'`〜ー-]", "", text)
            return text

        norm_lead = _normalize(lead)
        norm_para = _normalize(first_para)
        if len(norm_lead) < 20 or len(norm_para) < 20:
            return lead, body

        if norm_para.startswith(norm_lead) or norm_lead.startswith(norm_para):
            paragraphs = paragraphs[1:]
        else:
            ratio = SequenceMatcher(None, norm_lead, norm_para).ratio()
            if ratio >= 0.92:
                paragraphs = paragraphs[1:]

        if not paragraphs:
            return lead, ""
        return lead, "\n\n".join(paragraphs).strip()

    @staticmethod
    def _is_reference_or_list_paragraph(paragraph: str) -> bool:
        stripped = (paragraph or "").strip()
        if not stripped:
            return False
        return bool(re.match(r"^(?:出典:|参考(?:文献|資料)?[:：]?|[-*]\s+|\d+\.\s+)", stripped))

    def _get_active_style_profile(self) -> str:
        policy = getattr(self, "_pipeline_policy", {}) or {}
        configured = str(policy.get("style_profile") or "").strip()
        if configured:
            return configured
        focus = str(policy.get("focus") or self._get_effective_writing_focus())
        return {
            "analysis": "formal",
            "experience": "casual",
            "explanation": "balanced",
        }.get(focus, "balanced")

    def _cap_colloquial_endings(self, text: str, max_allowed: Optional[int] = None) -> str:
        """非casual文体では「〜ですね/〜ますね」系の過剰出現を抑える。"""
        if max_allowed is None:
            max_allowed = int(_ag("NON_CASUAL_COLLOQUIAL_ENDING_MAX"))
        if not text or max_allowed < 0:
            return text

        replacement_map = {
            "ですよね。": "です。",
            "ですね。": "です。",
            "ますよね。": "ます。",
            "ますね。": "ます。",
            "ませんね。": "ません。",
        }
        pattern = re.compile("|".join(re.escape(k) for k in replacement_map.keys()))
        total = len(pattern.findall(text))
        if total <= max_allowed:
            return text

        budget = max_allowed

        def _repl(match: re.Match[str]) -> str:
            nonlocal budget
            token = match.group(0)
            if budget > 0:
                budget -= 1
                return token
            return replacement_map.get(token, token)

        return pattern.sub(_repl, text)

    @classmethod
    def _break_ending_monotony(cls, text: str, max_consecutive: int = 3) -> str:
        """同一文末パターンの連続や交互反復を最小差分で散らす。"""
        if not text:
            return text

        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        blocks: List[Dict[str, Any]] = []
        for para in paragraphs:
            stripped = para.strip()
            if stripped.startswith("##") or re.match(r"^\s*(?:[-*]|\d+\.)", stripped):
                blocks.append({"kind": "raw", "text": para})
                continue

            sentences = [s.strip() for s in re.split(r"(?<=[。！？])\s*", stripped) if s.strip()]
            if not sentences:
                blocks.append({"kind": "raw", "text": para})
                continue
            blocks.append({"kind": "sentences", "sentences": list(sentences)})

        run_cat: Optional[str] = None
        run_positions: List[Tuple[int, int]] = []

        def _try_rewrite_run() -> bool:
            if len(run_positions) < max_consecutive:
                return False
            mid = len(run_positions) // 2
            order = [mid]
            for offset in range(1, len(run_positions)):
                left = mid - offset
                right = mid + offset
                if left >= 0:
                    order.append(left)
                if right < len(run_positions):
                    order.append(right)
            for pos_index in order:
                block_index, sentence_index = run_positions[pos_index]
                target_sent = blocks[block_index]["sentences"][sentence_index]
                rewritten = cls._rewrite_ending_for_variety(target_sent)
                if rewritten != target_sent:
                    blocks[block_index]["sentences"][sentence_index] = rewritten
                    return True
            return False

        for block_index, block in enumerate(blocks):
            if block.get("kind") != "sentences":
                run_cat = None
                run_positions = []
                continue

            sentences = block.get("sentences", [])
            for sentence_index, sent in enumerate(sentences):
                if cls._ENDING_MASU_RE.search(sent):
                    cat = "masu"
                elif cls._ENDING_DESU_RE.search(sent):
                    cat = "desu"
                else:
                    cat = None

                if cat is None:
                    run_cat = None
                    run_positions = []
                    continue

                if cat != run_cat:
                    run_cat = cat
                    run_positions = [(block_index, sentence_index)]
                    continue

                run_positions.append((block_index, sentence_index))
                if len(run_positions) >= max_consecutive and _try_rewrite_run():
                    run_positions = [(block_index, sentence_index)]

        abab_history: List[Tuple[Optional[str], int, int]] = []
        for block_index, block in enumerate(blocks):
            if block.get("kind") != "sentences":
                abab_history = []
                continue
            for sentence_index, sent in enumerate(block.get("sentences", [])):
                if cls._ENDING_MASU_RE.search(sent):
                    cat = "masu"
                elif cls._ENDING_DESU_RE.search(sent):
                    cat = "desu"
                else:
                    cat = None
                    abab_history = []
                    continue
                abab_history.append((cat, block_index, sentence_index))
                if len(abab_history) >= 4:
                    recent = [c for c, _, _ in abab_history[-4:]]
                    if recent == ["masu", "desu", "masu", "desu"] or recent == ["desu", "masu", "desu", "masu"]:
                        _, bi, si = abab_history[-2]
                        target = blocks[bi]["sentences"][si]
                        rewritten = cls._rewrite_ending_for_variety(target)
                        if rewritten != target:
                            blocks[bi]["sentences"][si] = rewritten
                        abab_history = []

        rebuilt: List[str] = []
        for block in blocks:
            if block.get("kind") == "sentences":
                rebuilt.append("".join(block.get("sentences", [])).strip())
            else:
                rebuilt.append(str(block.get("text", "")).strip())
        return "\n\n".join(part for part in rebuilt if part.strip()).strip()

    @staticmethod
    def _rewrite_ending_for_variety(sentence: str) -> str:
        """文末を意味を崩さない最小差分で揺らす。"""
        if not sentence:
            return sentence
        if re.search(r"(?:ますね|ですよね|ですね|でしょう)。$", sentence):
            return sentence
        if re.search(r"ます。$", sentence):
            return re.sub(r"ます。$", "ますね。", sentence)
        if re.search(r"です。$", sentence):
            return re.sub(r"です。$", "ですね。", sentence)
        return sentence

    def _analyze_style_register(self, text: str) -> Dict[str, Any]:
        """丁寧体/常体の混在度を軽量分析する。"""
        if not text:
            return {
                "polite_count": 0,
                "plain_count": 0,
                "total_count": 0,
                "mixed": False,
                "minor_ratio": 0.0,
            }

        sentence_split_re = _ag("_RE_SENTENCE_SPLIT")
        polite_re = _ag("_RE_POLITE_REGISTER_ENDING")
        plain_re = _ag("_RE_PLAIN_REGISTER_ENDING")

        body_text = re.sub(r"^##.*$", "", text, flags=re.MULTILINE)
        polite_count = 0
        plain_count = 0

        paragraphs = [p for p in re.split(r"\n{2,}", body_text) if p.strip()]
        for paragraph in paragraphs:
            stripped = paragraph.strip()
            if (
                not stripped
                or self._is_reference_or_list_paragraph(stripped)
                or re.match(r"^https?://", stripped)
            ):
                continue
            sentences = [s.strip() for s in sentence_split_re.split(stripped) if s.strip()]
            for sentence in sentences:
                if polite_re.search(sentence):
                    polite_count += 1
                elif plain_re.search(sentence):
                    plain_count += 1

        total_count = polite_count + plain_count
        minor_ratio = min(polite_count, plain_count) / total_count if total_count else 0.0
        mixed = (
            total_count >= 6
            and polite_count >= 2
            and plain_count >= 2
            and minor_ratio >= 0.20
        )
        return {
            "polite_count": polite_count,
            "plain_count": plain_count,
            "total_count": total_count,
            "mixed": mixed,
            "minor_ratio": round(minor_ratio, 4),
        }

    def _should_enforce_polite_register(self) -> bool:
        """非casualかつ説明/分析/企業文脈では丁寧体を優先する。"""
        if self._get_active_style_profile() == "casual":
            return False

        perspective = self._normalize_perspective_key(getattr(self, "_current_perspective", ""))
        if perspective in {"corporate", "expert", "educator"}:
            return True

        focus = str(self._get_effective_writing_focus() or "")
        return focus in {"analysis", "explanation"}

    def _normalize_register_to_polite(self, text: str) -> str:
        """です・ます調へ寄せる最小変換（見出し/出典/URLは除外）。"""
        if not text:
            return text

        rewrites = _ag("REGISTER_NORMALIZE_REWRITES")

        rewritten: List[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if (
                not stripped
                or stripped.startswith("## ")
                or self._is_reference_or_list_paragraph(stripped)
                or re.match(r"^https?://", stripped)
            ):
                rewritten.append(line)
                continue

            updated = line
            for pattern, replacement in rewrites:
                updated = re.sub(pattern, replacement, updated)
            rewritten.append(updated)
        return "\n".join(rewritten)

    def _has_corporate_stance_anchor_gap(self, lead: str, body: str) -> bool:
        """企業視点なのに主体表現がない状態を検出する。"""
        perspective = self._normalize_perspective_key(getattr(self, "_current_perspective", ""))
        if perspective != "corporate":
            return False

        combined = f"{lead}\n\n{body}".strip()
        if not combined:
            return False
        return not bool(re.search(r"(私たち|当社|弊社)(?:は|が|として|にとって)", combined))

    def _extract_primary_org_name(self, text: str) -> str:
        """本文に現れる主要組織名を推定する。"""
        if not text:
            return ""
        match = re.search(
            r"([一-龯々〆ヵヶぁ-んァ-ヶA-Za-z0-9・ー]{2,24}"
            r"(?:銀行|信用金庫|信用組合|株式会社|グループ|社))",
            text,
        )
        return match.group(1) if match else ""

    def _inject_corporate_stance_anchor(self, lead: str, body: str) -> str:
        """導入に企業主体のアンカーを1箇所補う。"""
        stripped_lead = (lead or "").strip()
        if not stripped_lead:
            return lead
        if re.search(r"^(私たち|当社|弊社)(?:は|が)", stripped_lead):
            return stripped_lead

        source_text = "\n".join(
            [
                str(getattr(self, "_current_title", "") or ""),
                stripped_lead,
                (body or "").strip(),
            ]
        )
        org_name = self._extract_primary_org_name(source_text)
        if org_name:
            replaced = re.sub(
                rf"^{re.escape(org_name)}(?:は|が)",
                f"私たち{org_name}は",
                stripped_lead,
                count=1,
            )
            if replaced != stripped_lead:
                return replaced
            return f"私たち{org_name}は、{stripped_lead}"
        return f"私たちは、{stripped_lead}"

    def _normalize_pronoun_usage(self, text: str, target_pronoun: str) -> str:
        """一人称の最終統一（企業語は置換しない）。"""
        if not text or not target_pronoun:
            return text

        variant_map = {
            "私": ["わたし", "ワタシ", "僕", "ぼく", "ボク", "俺"],
            "わたし": ["私", "ワタシ", "僕", "ぼく", "ボク", "俺"],
            "僕": ["ぼく", "ボク", "私", "わたし", "俺"],
            "私たち": ["私達", "わたしたち", "わたし達", "我々", "私", "わたし", "僕", "ぼく", "俺"],
        }
        variants = variant_map.get(target_pronoun, [])
        if not variants:
            return text

        tail_pattern = r"(?=(?:は|が|を|に|へ|で|と|の|も|から|まで|って|では|には|として|、|。|！|？|!|\?|\s|$))"
        boundary = r"(?<![一-龯ぁ-んァ-ヶA-Za-z0-9_])"
        result = text
        for token in variants:
            result = re.sub(
                rf"{boundary}{re.escape(token)}{tail_pattern}",
                target_pronoun,
                result,
            )
        return result

    @staticmethod
    def _dedupe_cross_section_sentences(body: str, min_phrase_len: int = 14) -> str:
        """セクション間で繰り返される文を後方出現側で削除する。"""
        if not body:
            return body

        def _normalize_sentence_signature(sentence: str) -> str:
            normalized = sentence or ""
            normalized = re.sub(r"「[^」]{1,48}」", "引用語", normalized)
            normalized = re.sub(r"『[^』]{1,48}』", "引用語", normalized)
            normalized = re.sub(r"[、。！？!?「」『』（）()\[\]【】\s\u3000]", "", normalized)
            if not normalized:
                return ""
            normalized = re.sub(r"(重要|大切|鍵になる)", "重要", normalized)
            normalized = re.sub(r"(判断基準|基準)", "判断基準", normalized)
            normalized = re.sub(r"(具体化すること|具体化)", "具体化", normalized)
            normalized = re.sub(r"(?:20|30|40|50|60)代", "年代", normalized)
            normalized = re.sub(r"共働き(?:の)?(?:世帯|家庭|読者)?", "生活者", normalized)
            return normalized[:220]

        lines = body.split("\n")
        seen_phrases: set[str] = set()
        seen_signatures: List[str] = []
        result_lines: List[str] = []
        current_section_sentences = 0

        for line in lines:
            stripped = line.strip()
            if (
                not stripped
                or stripped.startswith("#")
                or stripped.startswith("- ")
                or stripped.startswith("出典:")
                or re.match(r"^https?://", stripped)
            ):
                result_lines.append(line)
                if stripped.startswith("##"):
                    current_section_sentences = 0
                continue

            sentences = [s.strip() for s in re.split(r"(?<=[。！？])", stripped) if s.strip()]
            kept_sentences: List[str] = []
            for sent in sentences:
                normalized = _normalize_sentence_signature(sent)
                if len(normalized) < min_phrase_len:
                    kept_sentences.append(sent)
                    current_section_sentences += 1
                    continue

                is_dup = False
                phrases_in_sent: List[str] = []
                for i in range(len(normalized) - min_phrase_len + 1):
                    phrase = normalized[i : i + min_phrase_len]
                    phrases_in_sent.append(phrase)

                if phrases_in_sent:
                    dup_count = sum(1 for phrase in phrases_in_sent if phrase in seen_phrases)
                    overlap_ratio = dup_count / len(phrases_in_sent)
                    if overlap_ratio >= 0.40:
                        is_dup = True
                if not is_dup and seen_signatures:
                    for prev in seen_signatures[-36:]:
                        ratio = SequenceMatcher(None, normalized, prev).ratio()
                        if ratio >= 0.90:
                            is_dup = True
                            break

                if is_dup and current_section_sentences >= 1:
                    continue

                kept_sentences.append(sent)
                current_section_sentences += 1
                seen_signatures.append(normalized)
                if len(seen_signatures) > 240:
                    seen_signatures = seen_signatures[-160:]
                for phrase in phrases_in_sent:
                    seen_phrases.add(phrase)

            if kept_sentences:
                result_lines.append("".join(kept_sentences))

        return "\n".join(result_lines)

    def _dedupe_body_repetition(self, body: str) -> str:
        """セクション間の重複導入句・重複段落を最終段で抑制する。"""
        sections = self._extract_section_blocks(body)
        if len(sections) < 2:
            return body

        sentence_split_re = _ag("_RE_SENTENCE_SPLIT")
        section_opening_similarity_threshold = float(_ag("SECTION_OPENING_SIMILARITY_THRESHOLD"))
        section_opening_jaccard_threshold = float(_ag("SECTION_OPENING_JACCARD_THRESHOLD"))
        section_opening_containment_threshold = float(_ag("SECTION_OPENING_CONTAINMENT_THRESHOLD"))
        body_paragraph_dedupe_jaccard_threshold = float(_ag("BODY_PARAGRAPH_DEDUPE_JACCARD_THRESHOLD"))
        body_paragraph_dedupe_containment_threshold = float(_ag("BODY_PARAGRAPH_DEDUPE_CONTAINMENT_THRESHOLD"))
        similarity_ngram_max_len = int(_ag("SIMILARITY_NGRAM_MAX_LEN"))

        seen_openings: List[str] = []
        seen_paragraphs: List[str] = []
        rebuilt_sections: List[str] = []
        removed_count = 0

        for heading, content in sections:
            raw_paragraphs = [p.strip() for p in re.split(r"\n{2,}", content or "") if p.strip()]
            if not raw_paragraphs:
                rebuilt_sections.append(f"## {heading}\n\n{(content or '').strip()}".strip())
                continue

            paragraphs = list(raw_paragraphs)
            first_para = paragraphs[0].strip()
            if first_para and not self._is_reference_or_list_paragraph(first_para):
                first_sentences = [s.strip() for s in sentence_split_re.split(first_para) if s.strip()]
                if len(first_sentences) >= 2:
                    first_opening_norm = self._normalize_similarity_text(first_sentences[0])[:180]
                    if len(first_opening_norm) >= 18:
                        duplicated_opening = False
                        for prev in seen_openings:
                            ratio = SequenceMatcher(None, first_opening_norm, prev).ratio()
                            jaccard, containment = self._similarity_overlap_scores(first_opening_norm, prev)
                            if (
                                ratio >= section_opening_similarity_threshold
                                or jaccard >= section_opening_jaccard_threshold
                                or containment >= section_opening_containment_threshold
                            ):
                                duplicated_opening = True
                                break
                        if duplicated_opening:
                            paragraphs[0] = "".join(first_sentences[1:]).strip()
                            removed_count += 1

            kept: List[str] = []
            local_norms: List[str] = []
            substantive_paragraphs = [p for p in paragraphs if p and not self._is_reference_or_list_paragraph(p)]
            min_substantive = 1 if substantive_paragraphs else 0

            for para_idx, para in enumerate(paragraphs):
                para = para.strip()
                if not para:
                    continue

                is_reference_line = self._is_reference_or_list_paragraph(para)
                norm_para = self._normalize_similarity_text(para)
                remaining_substantive = sum(
                    1
                    for item in paragraphs[para_idx + 1 :]
                    if item and not self._is_reference_or_list_paragraph(item)
                )

                if is_reference_line:
                    kept.append(para)
                    continue
                if len(norm_para) < 50:
                    kept.append(para)
                    if len(norm_para) >= 24:
                        local_norms.append(norm_para[:similarity_ngram_max_len])
                    continue
                if len(norm_para) < 90:
                    duplicate_short = False
                    for prev in seen_paragraphs:
                        jaccard, containment = self._similarity_overlap_scores(norm_para, prev)
                        if containment >= 0.93 or jaccard >= 0.74:
                            duplicate_short = True
                            break
                    if not duplicate_short:
                        for prev in local_norms:
                            jaccard, containment = self._similarity_overlap_scores(norm_para, prev)
                            if containment >= 0.94 or jaccard >= 0.76:
                                duplicate_short = True
                                break
                    kept_substantive = sum(
                        1 for item in kept if item and not self._is_reference_or_list_paragraph(item)
                    )
                    if duplicate_short and (kept_substantive + remaining_substantive) >= min_substantive:
                        removed_count += 1
                        continue
                    kept.append(para)
                    local_norms.append(norm_para[:similarity_ngram_max_len])
                    continue

                duplicate = False
                for prev in seen_paragraphs:
                    jaccard, containment = self._similarity_overlap_scores(norm_para, prev)
                    if (
                        containment >= body_paragraph_dedupe_containment_threshold
                        or jaccard >= body_paragraph_dedupe_jaccard_threshold
                    ):
                        duplicate = True
                        break
                if not duplicate:
                    for prev in local_norms:
                        jaccard, containment = self._similarity_overlap_scores(norm_para, prev)
                        if containment >= 0.90 or jaccard >= 0.70:
                            duplicate = True
                            break

                kept_substantive = sum(1 for item in kept if item and not self._is_reference_or_list_paragraph(item))
                if duplicate and (kept_substantive + remaining_substantive) >= min_substantive:
                    removed_count += 1
                    continue

                kept.append(para)
                local_norms.append(norm_para[:similarity_ngram_max_len])

            if not kept:
                kept = [raw_paragraphs[0]]

            first_substantive = next((p for p in kept if p and not self._is_reference_or_list_paragraph(p)), "")
            if first_substantive:
                first_sentences = [s.strip() for s in sentence_split_re.split(first_substantive) if s.strip()]
                if first_sentences:
                    opening_norm = self._normalize_similarity_text(first_sentences[0])
                    if len(opening_norm) >= 18:
                        seen_openings.append(opening_norm[:180])
                        if len(seen_openings) > 48:
                            seen_openings = seen_openings[-48:]

            for para in kept:
                if self._is_reference_or_list_paragraph(para):
                    continue
                norm_para = self._normalize_similarity_text(para)
                if len(norm_para) >= 60:
                    seen_paragraphs.append(norm_para[:similarity_ngram_max_len])
            if len(seen_paragraphs) > 160:
                seen_paragraphs = seen_paragraphs[-160:]

            merged_content = "\n\n".join(kept).strip()
            rebuilt_sections.append(f"## {heading}\n\n{merged_content}")

        if removed_count <= 0:
            return body

        logger.info(
            "Final body repetition guard applied: removed=%s sections=%s",
            removed_count,
            len(sections),
        )
        return "\n\n".join(block.strip() for block in rebuilt_sections if block.strip()).strip()

    def _diversify_overused_phrases(self, text: str) -> str:
        """過剰反復しやすい定型語を2回目以降だけ自然な同義へ分散する。"""
        if not text:
            return text

        replacements = {
            "自分事": {"alternates": ("当事者意識", "自分ごと"), "keep_first": 1},
            "欠かせません": {"alternates": ("要になります", "外せません"), "keep_first": 1},
            "重要な一歩": {"alternates": ("有効な着手点", "前進の足がかり"), "keep_first": 1},
            "見逃せません": {"alternates": ("軽視できません", "注意が必要です"), "keep_first": 1},
            "必要があると考えます": {"alternates": ("必要があります", "必要だと見ています"), "keep_first": 1},
            "必要だと考えます": {"alternates": ("必要です", "必要だと見ています"), "keep_first": 1},
            "見えてきます": {"alternates": ("分かってきます", "浮かび上がります"), "keep_first": 1},
            "だけでなく": {"alternates": ("に加えて", "のみならず"), "keep_first": 3},
        }
        result = text
        for source, rule in replacements.items():
            if not isinstance(rule, dict):
                continue
            alternates = tuple(rule.get("alternates", ()))
            keep_first = int(rule.get("keep_first", 1) or 1)
            if not alternates:
                continue
            matches = list(re.finditer(re.escape(source), result))
            if len(matches) <= keep_first:
                continue
            rebuilt: List[str] = []
            last = 0
            for idx, match in enumerate(matches):
                rebuilt.append(result[last:match.start()])
                if idx < keep_first:
                    rebuilt.append(source)
                else:
                    alt = alternates[(idx - keep_first) % len(alternates)]
                    rebuilt.append(alt)
                last = match.end()
            rebuilt.append(result[last:])
            result = "".join(rebuilt)
        return result

    def _clean_redundant_connectives(self, text: str) -> str:
        """接続語の重ね掛けを最小限で補正する。"""
        if not text:
            return text

        replacements = (
            (r"しかし一方で、?同時に", "一方で"),
            (r"しかし一方で", "一方で"),
            (r"一方で、?同時に", "一方で"),
            (r"さらに、?加えて", "さらに"),
            (r"加えて、?さらに", "さらに"),
            (r"また、?さらに", "さらに"),
            (r"さらに、?また", "さらに"),
            (r"そのため\s*こそ", "そのため"),
            (r"というわけで\s*こそ", "というわけで"),
            (r"ただながら", "ただ"),
            (r"和らげるになります", "和らぐことにつながります"),
            (r"。対してAIは", "。一方、AIは"),
            (
                r"(なのだ|のだ|なのです|のです|んです)、(?=(その|この|こうした|そうした|実務で|まずは|まず|次に|一方で|加えて|さらに))",
                r"\1。",
            ),
        )
        cleaned = text
        for pattern, replacement in replacements:
            cleaned = re.sub(pattern, replacement, cleaned)

        cleaned = re.sub(r"(一方で)([、,]\s*)\1", r"\1\2", cleaned)
        cleaned = re.sub(r"(さらに)([、,]\s*)\1", r"\1\2", cleaned)
        cleaned = re.sub(r"(また)([、,]\s*)\1", r"\1\2", cleaned)
        return cleaned

    @staticmethod
    def _soften_assertive_expressions(text: str) -> str:
        """断定的な結果・保証表現をソフトに言い換える。"""
        if not text:
            return text
        assertive_rewrites = [
            (r"必ずしも", "常にとは限らず"),
            (r"必ず((?:ご確認|お確かめ)(?:ください|願います|をお願いします|いただきますようお願いいたします))", r"\1"),
            (r"必ず([^\s。、]{1,20})(ます|です|でしょう|しょう)", r"多くの場合\1\2"),
            (r"必ず", "原則として"),
            (r"確実に", "おおむね"),
            (r"絶対に([^\s。、]{1,20})(ます|です)", r"\1傾向があり\2"),
            (r"100%", "ほぼ確実に"),
        ]
        result = text
        for pattern, repl in assertive_rewrites:
            result = re.sub(pattern, repl, result)
        return result

    @staticmethod
    def _strip_heading_top_adversative(text: str) -> str:
        """見出し直後の逆接開始を除去する。"""
        if not text:
            return text
        adversative_after_heading = re.compile(
            r"(^##[^\n]*\n\n?)"
            r"(しかし|ただし|ただ)[、,]\s*",
            flags=re.MULTILINE,
        )
        return adversative_after_heading.sub(r"\1", text)

    def _get_concise_compaction_config(self) -> Dict[str, Any]:
        """冗長圧縮の設定を返す。"""
        defaults = {
            "enabled": True,
            "dedupe_similarity_ratio": 0.86,
            "dedupe_jaccard_ratio": 0.62,
            "summary_overlap_ratio": 0.58,
            "max_connective_openings_per_paragraph": 2,
        }
        cfg = self._get_postprocess_config()
        concise_cfg = cfg.get("concise_compaction", {}) if isinstance(cfg, dict) else {}
        if not isinstance(concise_cfg, dict):
            return defaults
        merged = dict(defaults)
        merged.update(concise_cfg)
        return merged

    @staticmethod
    def _is_summary_marker_sentence(sentence: str) -> bool:
        stripped = (sentence or "").strip()
        markers = _ag("REDUNDANT_SUMMARY_MARKERS")
        return any(stripped.startswith(marker) for marker in markers)

    def _apply_concise_rewrites(self, sentence: str) -> str:
        """抽象語の重ね書きと冗長終端を短くする。"""
        result = sentence.strip()
        if not result:
            return ""

        for pattern, replacement in _ag("ABSTRACT_COMPRESSION_REWRITES"):
            result = re.sub(pattern, replacement, result)

        for pattern, replacement in AI_LIKE_ENDING_REWRITES:
            result = re.sub(pattern, replacement, result)

        result = re.sub(r"([。！？])\1+", r"\1", result)
        result = re.sub(r"[、,]{2,}", "、", result)
        return result.strip()

    def _aggressive_sentence_pruning(
        self,
        text: str,
        *,
        keep_ratio: float,
        min_sentences_per_paragraph: int,
    ) -> str:
        """長文向けに段落内文数を抑え、情報量の低い重複説明を削る。"""
        if not text:
            return text

        sentence_split_re = _ag("_RE_SENTENCE_SPLIT")

        keep_ratio = max(0.45, min(0.90, keep_ratio))
        min_sentences_per_paragraph = max(3, min(6, min_sentences_per_paragraph))

        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        rebuilt: List[str] = []
        for para in paragraphs:
            stripped = para.strip()
            if stripped.startswith("##") or self._is_reference_or_list_paragraph(stripped):
                rebuilt.append(para)
                continue

            sentences = [s.strip() for s in sentence_split_re.split(para) if s.strip()]
            if len(sentences) < min_sentences_per_paragraph:
                rebuilt.append(para.strip())
                continue

            keep_count = int(round(len(sentences) * keep_ratio))
            keep_count = max(2, min(len(sentences) - 1, keep_count))

            term_sets: List[set[str]] = [
                set(self._extract_content_terms(sentence, max_chars=220))
                for sentence in sentences
            ]
            selected = [0]
            selected_terms: set[str] = set(term_sets[0])
            remaining = set(range(1, len(sentences)))

            while len(selected) < keep_count and remaining:
                best_idx = -1
                best_score = -10_000.0
                for idx in list(remaining):
                    terms = term_sets[idx]
                    new_terms = len(terms - selected_terms)
                    score = (new_terms * 2.1) + (len(terms) * 0.15)
                    if self._is_summary_marker_sentence(sentences[idx]):
                        score -= 1.4
                    if re.search(r"(?:\d|%|[A-Za-z]{3,}|「[^」]+」)", sentences[idx]):
                        score += 1.0
                    if idx == len(sentences) - 1:
                        score += 0.2
                    if score > best_score:
                        best_score = score
                        best_idx = idx
                if best_idx < 0:
                    break
                selected.append(best_idx)
                selected_terms.update(term_sets[best_idx])
                remaining.remove(best_idx)

            selected = sorted(set(selected))
            if len(selected) < keep_count:
                for idx in range(1, len(sentences)):
                    if idx in selected:
                        continue
                    selected.append(idx)
                    if len(selected) >= keep_count:
                        break
                selected = sorted(set(selected))

            rebuilt.append("".join(sentences[idx] for idx in selected if 0 <= idx < len(sentences)).strip())

        return "\n\n".join(p for p in rebuilt if p.strip()).strip()

    def _compress_redundant_explanations(self, text: str) -> str:
        """段落内の同義反復と不要導入句を統合して圧縮する。"""
        if not text:
            return text

        sentence_split_re = _ag("_RE_SENTENCE_SPLIT")

        cfg = self._get_concise_compaction_config()
        if not bool(cfg.get("enabled", True)):
            return text

        dedupe_similarity = float(cfg.get("dedupe_similarity_ratio", 0.86) or 0.86)
        dedupe_jaccard = float(cfg.get("dedupe_jaccard_ratio", 0.62) or 0.62)
        summary_overlap = float(cfg.get("summary_overlap_ratio", 0.58) or 0.58)
        max_connective = int(cfg.get("max_connective_openings_per_paragraph", 2) or 2)
        max_connective = max(0, min(3, max_connective))
        target_reduction_ratio = float(cfg.get("target_reduction_ratio", 0.22) or 0.22)
        aggressive_keep_ratio = float(cfg.get("aggressive_keep_ratio", 0.68) or 0.68)
        aggressive_min_sentences = int(cfg.get("aggressive_min_sentences_per_paragraph", 3) or 3)
        aggressive_min_chars = int(cfg.get("aggressive_min_chars", 1600) or 1600)
        summary_like_re = re.compile(
            r"(?:この(?:背景|違い|点|核心)|言い換えると|要するに|結果として|と捉えられます|と考えます)"
        )
        abstract_re = re.compile(r"(?:こと|ため|背景|理由|性質|傾向|特徴|構造)")
        fact_signal_re = re.compile(r"(?:\d|%|[A-Za-z]{3,}|「[^」]+」)")

        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        rebuilt: List[str] = []
        global_term_counter: Counter[str] = Counter()
        for para in paragraphs:
            stripped = para.strip()
            if stripped.startswith("##") or self._is_reference_or_list_paragraph(stripped):
                rebuilt.append(para)
                continue

            sentences = [s.strip() for s in sentence_split_re.split(para) if s.strip()]
            if not sentences:
                rebuilt.append(para)
                continue

            opener_hits = 0
            prev_template_opener = ""
            local_terms: set[str] = set()
            kept: List[str] = []
            kept_norms: List[str] = []
            dropped: List[str] = []
            min_keep = 2 if len(sentences) >= 3 else 1
            for sentence_idx, sentence in enumerate(sentences):
                current = self._apply_concise_rewrites(sentence)
                if not current:
                    continue

                current, opener_hits, prev_template_opener = self._trim_redundant_template_opening(
                    current,
                    template_hits=opener_hits,
                    max_template_openers=max_connective,
                    prev_template_opener=prev_template_opener,
                )
                if not current:
                    continue
                if sentence_idx > 0 and len(sentences) >= 2 and self._is_summary_marker_sentence(current):
                    dropped.append(current)
                    continue

                norm_current = self._normalize_similarity_text(current)
                sentence_terms = set(self._extract_content_terms(current, max_chars=220))
                local_novelty = 1.0
                global_novelty = 1.0
                if sentence_terms:
                    local_novelty = len(sentence_terms - local_terms) / max(1, len(sentence_terms))
                    global_novelty = len(sentence_terms - set(global_term_counter.keys())) / max(1, len(sentence_terms))
                if len(norm_current) >= 18 and kept_norms:
                    redundant = False
                    for norm_prev in kept_norms[-3:]:
                        ratio = SequenceMatcher(None, norm_current, norm_prev).ratio()
                        jaccard, containment = self._similarity_overlap_scores(norm_current, norm_prev)
                        if ratio >= dedupe_similarity or (jaccard >= dedupe_jaccard and containment >= 0.72):
                            redundant = True
                            break

                    if not redundant and self._is_summary_marker_sentence(current):
                        norm_prev = kept_norms[-1]
                        ratio = SequenceMatcher(None, norm_current, norm_prev).ratio()
                        jaccard, containment = self._similarity_overlap_scores(norm_current, norm_prev)
                        if ratio >= summary_overlap or jaccard >= summary_overlap or containment >= 0.80:
                            redundant = True

                    summary_like = self._is_summary_marker_sentence(current) or bool(summary_like_re.search(current))
                    long_abstract_sentence = len(current) >= 58 and bool(abstract_re.search(current))
                    low_novelty = len(sentence_terms) >= 4 and local_novelty <= 0.45
                    global_overlap_heavy = len(sentence_terms) >= 5 and global_novelty <= 0.40
                    fact_signal = bool(fact_signal_re.search(current))

                    if sentence_idx > 0 and not fact_signal and (
                        redundant
                        or (
                            low_novelty
                            and (
                                summary_like
                                or long_abstract_sentence
                                or global_overlap_heavy
                            )
                        )
                        or (
                            long_abstract_sentence
                            and len(current) >= 82
                            and local_novelty <= 0.55
                        )
                    ):
                        dropped.append(current)
                        continue

                    if redundant and len(kept) >= 1:
                        dropped.append(current)
                        continue

                kept.append(current)
                if norm_current:
                    kept_norms.append(norm_current[:240])
                local_terms.update(sentence_terms)
                if sentence_terms:
                    global_term_counter.update(sentence_terms)

            if not kept:
                kept.append(self._apply_concise_rewrites(sentences[0]))
            elif len(kept) < min_keep and dropped:
                for sentence in dropped:
                    kept.append(sentence)
                    if len(kept) >= min_keep:
                        break

            rebuilt.append("".join(s for s in kept if s).strip())

        compressed = "\n\n".join(p for p in rebuilt if p.strip()).strip()
        baseline_len = max(1, len((text or "").strip()))
        reduction_ratio = (baseline_len - len(compressed)) / baseline_len
        if (
            len((text or "").strip()) >= aggressive_min_chars
            and reduction_ratio < target_reduction_ratio
        ):
            compressed = self._aggressive_sentence_pruning(
                compressed,
                keep_ratio=aggressive_keep_ratio,
                min_sentences_per_paragraph=aggressive_min_sentences,
            )
        return compressed

    def _trim_nonclosing_section_tail_summaries(self, body: str) -> str:
        """非締めセクション末の機械的な要点1行を抑制する。"""
        if not body:
            return body
        sections = self._extract_section_blocks(body)
        if not sections:
            return body

        sentence_split_re = _ag("_RE_SENTENCE_SPLIT")
        closing_heading_pattern = _ag("CLOSING_HEADING_PATTERN")

        summary_start_re = re.compile(
            r"^(?:要点(?:は|としては)|要するに|まとめると|結論として|ひと言で言うと|"
            r"ここまで(?:を)?まとめると|ここまでの要点は|押さえておきたいのは)"
        )
        rebuilt: List[str] = []

        for idx, (heading, content) in enumerate(sections):
            section_text = (content or "").strip()
            if not section_text:
                rebuilt.append(f"## {heading}".strip())
                continue

            is_last_section = idx == len(sections) - 1
            if closing_heading_pattern.search(heading or "") or is_last_section:
                rebuilt.append(f"## {heading}\n\n{section_text}".strip())
                continue

            paragraphs = [p.strip() for p in re.split(r"\n{2,}", section_text) if p.strip()]
            if len(paragraphs) < 2:
                rebuilt.append(f"## {heading}\n\n{section_text}".strip())
                continue

            last_para = paragraphs[-1]
            if self._is_reference_or_list_paragraph(last_para) or re.search(r"https?://", last_para):
                rebuilt.append(f"## {heading}\n\n{section_text}".strip())
                continue

            last_sentences = [s.strip() for s in sentence_split_re.split(last_para) if s.strip()]
            section_sentence_count = len([s for s in sentence_split_re.split(section_text) if s.strip()])
            first_sentence = last_sentences[0] if last_sentences else ""
            looks_summary = bool(
                first_sentence
                and (
                    self._is_summary_marker_sentence(first_sentence)
                    or summary_start_re.match(first_sentence)
                )
            )

            if (
                looks_summary
                and len(last_sentences) <= 2
                and len(last_para) <= 140
                and section_sentence_count >= 3
            ):
                paragraphs = paragraphs[:-1]

            merged = "\n\n".join(paragraphs).strip()
            rebuilt.append(f"## {heading}\n\n{merged}".strip())

        return "\n\n".join(block for block in rebuilt if block.strip()).strip()

    @staticmethod
    def _normalize_opening_token(token: str) -> str:
        return re.sub(r"[、,\s]+$", "", str(token or "").strip())

    @staticmethod
    def _is_logical_required_opening(token: str) -> bool:
        return any(token.startswith(prefix) for prefix in LOGICAL_REQUIRED_OPENING_PREFIXES)

    @staticmethod
    def _is_suppressible_template_opening(token: str) -> bool:
        return any(token.startswith(prefix) for prefix in SUPPRESSIBLE_TEMPLATE_OPENING_PREFIXES)

    @staticmethod
    def _strip_opening_safely(sentence: str, pattern: str) -> Tuple[str, bool]:
        candidate = re.sub(pattern, "", sentence, count=1).lstrip("、, \t")
        if not candidate:
            return sentence, False
        if re.match(
            r"^(?:は|が|を|に|で|と|も|へ|から|まで|だけ|ばかり)(?:[、,]|$)",
            candidate,
        ):
            return sentence, False
        return candidate, True

    def _trim_redundant_template_opening(
        self,
        sentence: str,
        *,
        template_hits: int,
        max_template_openers: int,
        prev_template_opener: str,
    ) -> Tuple[str, int, str]:
        """必要接続は残し、弱いテンプレ導入のみ過多時に抑制する。"""
        current = sentence
        opener_token = ""
        for pattern in AI_LIKE_OPENING_PATTERNS:
            matched = re.match(pattern, current)
            if not matched:
                continue
            opener_token = self._normalize_opening_token(matched.group(0))
            is_logical = self._is_logical_required_opening(opener_token)
            is_template = self._is_suppressible_template_opening(opener_token)
            same_template = bool(opener_token) and opener_token == prev_template_opener

            if is_template and (same_template or template_hits >= max_template_openers):
                stripped, applied = self._strip_opening_safely(current, pattern)
                if applied:
                    current = stripped
                return current, template_hits, prev_template_opener

            if is_template:
                return current, template_hits + 1, opener_token
            if is_logical:
                return current, template_hits, ""
            return current, template_hits + 1, ""

        return current, template_hits, ""

    def _reduce_ai_like_openings(self, text: str) -> str:
        """文頭導入を整える。必要接続は保持し、弱い定型の連続だけ抑える。"""
        if not text:
            return text

        sentence_split_re = _ag("_RE_SENTENCE_SPLIT")

        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        rebuilt: List[str] = []
        prev_template_opener = ""
        for para in paragraphs:
            stripped = para.strip()
            if stripped.startswith("##") or self._is_reference_or_list_paragraph(stripped):
                rebuilt.append(para)
                prev_template_opener = ""
                continue

            sentences = [s.strip() for s in sentence_split_re.split(para) if s.strip()]
            if not sentences:
                rebuilt.append(para)
                prev_template_opener = ""
                continue

            first = sentences[0]
            first, _, prev_template_opener = self._trim_redundant_template_opening(
                first,
                template_hits=0,
                max_template_openers=1,
                prev_template_opener=prev_template_opener,
            )
            if first:
                sentences[0] = first
            rebuilt.append("".join(sentences).strip())

        return "\n\n".join(block for block in rebuilt if block.strip()).strip()

    def _reduce_ai_like_endings(self, text: str) -> str:
        """文末のAI定型を自然な終止へ寄せる。"""
        if not text:
            return text
        result = text
        for pattern, replacement in AI_LIKE_ENDING_REWRITES:
            result = re.sub(pattern, replacement, result)
        return result

    def _reduce_target_term_overuse(self, text: str, *, target_audience: str, keep: int = 2) -> str:
        """ターゲット語の過剰反復を抑える。属性ラベルは必要に応じて非表示化する。"""
        if not text:
            return text
        audience = (target_audience or "").strip()
        result = text
        sensitive_audience = self._is_sensitive_audience_label(audience)
        demographic_topic_explicit = self._is_demographic_topic_explicit(audience)
        if demographic_topic_explicit:
            return result
        suppress_demographic_labels = bool(sensitive_audience and not demographic_topic_explicit)

        demographic_patterns = [
            r"(?:\d{2}代(?:前半|後半)?)(?:の)?(?:読者|世帯|家庭)?",
            r"共働き(?:の)?(?:世帯|家庭|読者)?",
            r"独身(?:世帯|者)?",
            r"単身(?:世帯|者)?",
            r"子育て(?:世帯|家庭)?",
            r"育児(?:世帯|家庭)?",
            r"高齢(?:者|世帯)?",
            r"学生(?:向け|層)?",
        ]
        if suppress_demographic_labels:
            for pattern in demographic_patterns:
                result = re.sub(pattern, "読者", result)
            result = re.sub(r"読者(?:の)?(?:読者|世帯|家庭)", "読者", result)
            result = re.sub(r"読者{2,}", "読者", result)

        if audience and suppress_demographic_labels:
            audience_label = re.escape(audience)
            result = re.sub(audience_label, "読者", result)

        kyodobataraki_pattern = re.compile(r"(?:\d{2}代の)?共働き(?:の)?(?:世帯|家庭|読者)?")
        kyodobataraki_hits = kyodobataraki_pattern.findall(result)
        if kyodobataraki_hits:
            keep_count = 0 if suppress_demographic_labels else max(0, keep)
            seen = 0

            def _replace_kyodobataraki(match: re.Match[str]) -> str:
                nonlocal seen
                seen += 1
                if suppress_demographic_labels:
                    return "読者"
                if seen <= keep_count:
                    return match.group(0)
                token = match.group(0)
                if "読者" in token:
                    return "読者"
                if "世帯" in token:
                    return "忙しい世帯"
                return "忙しい家庭"

            result = kyodobataraki_pattern.sub(_replace_kyodobataraki, result)

        if suppress_demographic_labels:
            result = re.sub(
                r"(?:20|30|40|50|60)代(?:の)?(?:読者|世帯|家庭)?",
                "読者",
                result,
            )

        return result

    def _normalize_ai_like_heading_labels(self, text: str) -> str:
        """見出しのAIテンプレ語を自然なラベルへ寄せる。"""
        if not text:
            return text
        lines = text.splitlines()
        rewritten: List[str] = []
        for line in lines:
            updated = line
            if re.match(r"^\s*##\s+", line):
                for pattern, replacement in AI_LIKE_HEADING_REWRITES:
                    updated = re.sub(pattern, replacement, updated).strip()
                updated = re.sub(r"(を振り返る){2,}", "を振り返る", updated)
            rewritten.append(updated)
        return "\n".join(rewritten)

    def _repair_subjectless_openings(self, text: str) -> str:
        """主語省略が過剰で意味が取りづらい冒頭文を最小補修する。"""
        if not text:
            return text

        sentence_split_re = _ag("_RE_SENTENCE_SPLIT")

        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        rebuilt: List[str] = []
        for para in paragraphs:
            stripped = para.strip()
            if stripped.startswith("##") or self._is_reference_or_list_paragraph(stripped):
                rebuilt.append(para)
                continue

            sentences = [s.strip() for s in sentence_split_re.split(para) if s.strip()]
            if not sentences:
                rebuilt.append(para)
                continue

            first = sentences[0]
            replacements = (
                (r"^万能な創造者ではありません。", "生成AIは万能な創造者ではありません。"),
                (r"^生み出すのは、", "生成AIが生み出すのは、"),
                (r"^大量のデータをもとにパターンを学び、", "生成AIは大量のデータをもとにパターンを学び、"),
                (r"^書く文章には、", "生成AIが書く文章には、"),
            )
            for pattern, replacement in replacements:
                first = re.sub(pattern, replacement, first)
            sentences[0] = first
            rebuilt.append("".join(sentences).strip())

        return "\n\n".join(block for block in rebuilt if block.strip()).strip()

    @staticmethod
    def _extract_theme_entities(title: str, outline: object = None) -> List[str]:
        """タイトルとアウトラインからテーマ名詞句を1-3個抽出する。"""
        candidates: List[str] = []
        title_clean = (title or "").strip()
        if not title_clean:
            return candidates

        for match in re.finditer(
            r"[ァ-ヶー]{3,12}[一-龥々〆ヵヶ]{1,6}"
            r"|[一-龥々〆ヵヶ]{1,6}[ァ-ヶー]{3,12}"
            r"|[一-龥々〆ヵヶ]{2,8}"
            r"|[ァ-ヶー]{3,12}"
            r"|[A-Za-z][A-Za-z0-9\-]{2,15}",
            title_clean,
        ):
            word = match.group()
            if word in ("について", "における", "としての", "のための", "に関する"):
                continue
            if word not in candidates:
                candidates.append(word)
            if len(candidates) >= 3:
                break

        return candidates

    def _apply_prodrop_zero_anaphora(self, text: str, theme_entities: Optional[List[str]] = None) -> str:
        """段落内の主語反復を抑えて、ゼロ照応/項省略へ寄せる。"""
        if not text:
            return text

        sentence_split_re = _ag("_RE_SENTENCE_SPLIT")

        theme_set = set(theme_entities or [])
        theme_last_seen: Dict[str, int] = {}
        theme_drop_counts: Dict[str, int] = {}
        global_sentence_idx = 0

        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        rebuilt: List[str] = []

        for para in paragraphs:
            stripped = para.strip()
            if stripped.startswith("##") or self._is_reference_or_list_paragraph(stripped):
                rebuilt.append(para)
                continue

            sentences = [s.strip() for s in sentence_split_re.split(para) if s.strip()]
            if len(sentences) < 2:
                if theme_set and sentences:
                    for sent in sentences:
                        subj_match = re.match(r"^([^、。！？\s]{1,20}?)(?:は|が)", sent)
                        if subj_match and subj_match.group(1) in theme_set:
                            theme_last_seen[subj_match.group(1)] = global_sentence_idx
                        global_sentence_idx += 1
                rebuilt.append(para)
                continue

            prev_subject = ""
            pronoun_subject_seen = 0
            edited: List[str] = []
            for sentence in sentences:
                subject_match = re.match(r"^([^、。！？\s]{1,20}?)(?:は|が)", sentence)
                subject = subject_match.group(1) if subject_match else ""
                updated = sentence

                if subject and subject == prev_subject:
                    updated = re.sub(
                        rf"^{re.escape(subject)}(?:は|が)",
                        "",
                        updated,
                        count=1,
                    ).lstrip("、, \t")
                elif subject and subject in theme_set and subject != prev_subject:
                    last = theme_last_seen.get(subject)
                    if last is not None and (global_sentence_idx - last) <= 5:
                        theme_drop_counts[subject] = theme_drop_counts.get(subject, 0) + 1
                        if theme_drop_counts[subject] % 2 == 0:
                            updated = re.sub(
                                rf"^{re.escape(subject)}(?:は|が)",
                                "",
                                updated,
                                count=1,
                            ).lstrip("、, \t")

                if re.match(r"^(私|わたし|僕|私たち|当社|弊社)(?:は|が)", updated):
                    pronoun_subject_seen += 1
                    if pronoun_subject_seen >= 2:
                        updated = re.sub(
                            r"^(私|わたし|僕|私たち|当社|弊社)(?:は|が)",
                            "",
                            updated,
                            count=1,
                        ).lstrip("、, \t")

                if updated:
                    edited.append(updated)
                else:
                    edited.append(sentence)
                if subject:
                    prev_subject = subject
                    if subject in theme_set:
                        theme_last_seen[subject] = global_sentence_idx
                global_sentence_idx += 1

            rebuilt.append("".join(edited).strip())

        return "\n\n".join(block for block in rebuilt if block.strip()).strip()

    def _reduce_repeated_named_entity_openings(self, body: str) -> str:
        """セクション冒頭の同一固有名詞主語の連発を抑える。"""
        if not body:
            return body
        sections = self._extract_section_blocks(body)
        if len(sections) < 2:
            return body

        sentence_split_re = _ag("_RE_SENTENCE_SPLIT")

        payloads: List[Dict[str, Any]] = []
        entity_sections: Dict[str, List[int]] = {}
        blocked_entities = {
            "これ",
            "それ",
            "この",
            "その",
            "私",
            "わたし",
            "僕",
            "あなた",
            "読者",
            "地域",
            "企業",
            "課題",
            "支援",
            "会員",
            "場合",
        }

        for section_idx, (heading, content) in enumerate(sections):
            paragraphs = [p.strip() for p in re.split(r"\n{2,}", content or "") if p.strip()]
            first_para_idx: Optional[int] = None
            first_sentence_idx: Optional[int] = None
            first_sentence = ""
            entity = ""

            for para_idx, para in enumerate(paragraphs):
                if self._is_reference_or_list_paragraph(para):
                    continue
                sentences = [s.strip() for s in sentence_split_re.split(para) if s.strip()]
                if not sentences:
                    continue
                first_para_idx = para_idx
                first_sentence_idx = 0
                first_sentence = sentences[0]
                match = re.match(r"^([^、。！？\s]{4,24}?)(?:は|が)", first_sentence)
                if match:
                    candidate = match.group(1).strip()
                    if candidate not in blocked_entities and re.search(r"[一-龯ァ-ヶA-Za-z]", candidate):
                        entity = candidate
                break

            payload = {
                "heading": heading,
                "content": content,
                "paragraphs": paragraphs,
                "first_para_idx": first_para_idx,
                "first_sentence_idx": first_sentence_idx,
                "first_sentence": first_sentence,
                "entity": entity,
            }
            payloads.append(payload)
            if entity:
                entity_sections.setdefault(entity, []).append(section_idx)

        rewritten = 0
        rebuilt_sections: List[str] = []

        for section_idx, payload in enumerate(payloads):
            heading = str(payload.get("heading", "") or "")
            content = str(payload.get("content", "") or "")
            paragraphs = list(payload.get("paragraphs", []) or [])
            entity = str(payload.get("entity", "") or "")
            first_para_idx = payload.get("first_para_idx")

            if (
                entity
                and isinstance(first_para_idx, int)
                and 0 <= first_para_idx < len(paragraphs)
                and len(entity_sections.get(entity, [])) >= 2
                and section_idx > entity_sections[entity][0]
            ):
                sentences = [s.strip() for s in sentence_split_re.split(paragraphs[first_para_idx]) if s.strip()]
                if sentences:
                    original = sentences[0]
                    updated = re.sub(rf"^{re.escape(entity)}(?:は|が)", "", original, count=1).lstrip("、, \t")
                    if updated and len(updated) >= 12:
                        sentences[0] = updated
                        paragraphs[first_para_idx] = "".join(sentences).strip()
                        rewritten += 1

            merged_content = "\n\n".join(p for p in paragraphs if p.strip()).strip() or content.strip()
            rebuilt_sections.append(f"## {heading}\n\n{merged_content}".strip())

        if rewritten <= 0:
            return body
        logger.info("Named-entity opening guard applied: rewritten=%s", rewritten)
        return "\n\n".join(block for block in rebuilt_sections if block.strip()).strip()

    def _compress_repeated_subject_openings(self, body: str) -> str:
        """セクション冒頭の同型主語句の連発を圧縮する。"""
        if not body:
            return body
        sections = self._extract_section_blocks(body)
        if len(sections) < 2:
            return body

        sentence_split_re = _ag("_RE_SENTENCE_SPLIT")

        blocked_subjects = {
            "これ",
            "それ",
            "この",
            "その",
            "私",
            "わたし",
            "私たち",
            "僕",
            "あなた",
            "読者",
        }
        subject_seen: Dict[str, int] = {}
        rewritten = 0
        rebuilt_sections: List[str] = []

        for heading, content in sections:
            paragraphs = [p.strip() for p in re.split(r"\n{2,}", content or "") if p.strip()]
            first_para_idx: Optional[int] = None
            subject_phrase = ""

            for para_idx, para in enumerate(paragraphs):
                if self._is_reference_or_list_paragraph(para):
                    continue
                sentences = [s.strip() for s in sentence_split_re.split(para) if s.strip()]
                if not sentences:
                    continue
                first_para_idx = para_idx
                first_sentence = sentences[0]
                match = re.match(r"^([^、。！？\s]{2,24}?)(?:は|が)", first_sentence)
                if match:
                    candidate = match.group(1).strip()
                    if candidate not in blocked_subjects and re.search(r"[一-龯ァ-ヶA-Za-z]", candidate):
                        subject_phrase = candidate
                break

            if (
                subject_phrase
                and subject_seen.get(subject_phrase, 0) >= 1
                and isinstance(first_para_idx, int)
                and 0 <= first_para_idx < len(paragraphs)
            ):
                sentences = [s.strip() for s in sentence_split_re.split(paragraphs[first_para_idx]) if s.strip()]
                if sentences:
                    updated = re.sub(
                        rf"^{re.escape(subject_phrase)}(?:は|が)",
                        "",
                        sentences[0],
                        count=1,
                    ).lstrip("、, \t")
                    if updated and len(updated) >= 10:
                        sentences[0] = updated
                        paragraphs[first_para_idx] = "".join(sentences).strip()
                        rewritten += 1

            if subject_phrase:
                subject_seen[subject_phrase] = subject_seen.get(subject_phrase, 0) + 1

            merged_content = "\n\n".join(p for p in paragraphs if p.strip()).strip() or content.strip()
            rebuilt_sections.append(f"## {heading}\n\n{merged_content}".strip())

        if rewritten <= 0:
            return body
        logger.info("Subject opening compression applied: rewritten=%s", rewritten)
        return "\n\n".join(block for block in rebuilt_sections if block.strip()).strip()

    @staticmethod
    def _dedupe_similar_headings(body: str) -> str:
        """見出し間の類似度が高い場合、後方の見出しを差別化する。"""
        lines = body.split("\n")
        heading_indices = [i for i, line in enumerate(lines) if line.strip().startswith("##")]
        if len(heading_indices) < 2:
            return body

        heading_texts = [(i, re.sub(r"^#+\s*", "", lines[i]).strip()) for i in heading_indices]
        suffix_variants = ["の要点", "の視点", "の背景", "の具体策", "の実践"]
        variant_idx = 0

        for a_pos in range(len(heading_texts)):
            for b_pos in range(a_pos + 1, len(heading_texts)):
                idx_a, text_a = heading_texts[a_pos]
                idx_b, text_b = heading_texts[b_pos]
                set_a = set(text_a)
                set_b = set(text_b)
                union = set_a | set_b
                if not union:
                    continue
                jaccard = len(set_a & set_b) / len(union)
                if jaccard > 0.6 and text_a != text_b:
                    prefix = lines[idx_b].split(text_b)[0] if text_b in lines[idx_b] else "## "
                    core = re.sub(r"(?:とは[？?]?|の実態|のポイント|の要点|の特徴)$", "", text_b).strip()
                    if core and core != text_b:
                        new_suffix = suffix_variants[variant_idx % len(suffix_variants)]
                        variant_idx += 1
                        lines[idx_b] = f"{prefix}{core}{new_suffix}"
                        heading_texts[b_pos] = (idx_b, f"{core}{new_suffix}")

        return "\n".join(lines)

    def _apply_unified_dedupe_pass(self, body: str) -> str:
        """重複除去の実書き換えを1パスに集約する。"""
        sample = body or ""
        if not sample:
            return sample
        after_paragraph = self._dedupe_body_repetition(sample)
        after_sentence = self._dedupe_cross_section_sentences(after_paragraph)
        return after_sentence

    def _apply_final_consistency_guards(self, lead: str, body: str) -> Tuple[str, str]:
        """最終段で一貫性と人間らしさのバランスを整える。"""
        lead = (lead or "").strip()
        body = (body or "").strip()

        body = self._dedupe_similar_headings(body)

        lead, body = self._dedupe_lead_body(lead, body)
        body = self._apply_unified_dedupe_pass(body)
        body = self._reduce_repeated_named_entity_openings(body)
        body = self._compress_repeated_subject_openings(body)
        body = self._normalize_ai_like_heading_labels(body)
        lead = self._reduce_ai_like_openings(lead)
        body = self._reduce_ai_like_openings(body)
        lead = self._reduce_ai_like_endings(lead)
        body = self._reduce_ai_like_endings(body)
        theme_entities = self._extract_theme_entities(
            getattr(self, "_current_title", "") or ""
        )
        lead = self._apply_prodrop_zero_anaphora(lead, theme_entities=theme_entities)
        body = self._apply_prodrop_zero_anaphora(body, theme_entities=theme_entities)
        lead = self._repair_subjectless_openings(lead)
        body = self._repair_subjectless_openings(body)
        lead = self._diversify_overused_phrases(lead)
        body = self._diversify_overused_phrases(body)
        lead = self._clean_redundant_connectives(lead)
        body = self._clean_redundant_connectives(body)
        lead = self._compress_redundant_explanations(lead)
        body = self._compress_redundant_explanations(body)
        body = self._trim_nonclosing_section_tail_summaries(body)
        body = self._strip_heading_top_adversative(body)
        lead = self._soften_assertive_expressions(lead)
        body = self._soften_assertive_expressions(body)

        pronoun = (getattr(self, "_current_pronoun", "") or "").strip()
        if pronoun:
            lead = self._normalize_pronoun_usage(lead, pronoun)
            body = self._normalize_pronoun_usage(body, pronoun)

        if self._has_corporate_stance_anchor_gap(lead, body):
            lead = self._inject_corporate_stance_anchor(lead, body)

        if self._should_enforce_polite_register():
            register_report = self._analyze_style_register(f"{lead}\n\n{body}")
            if register_report.get("mixed"):
                lead = self._normalize_register_to_polite(lead)
                body = self._normalize_register_to_polite(body)
                logger.info(
                    "Final register normalization applied: polite=%s plain=%s ratio=%.3f",
                    register_report.get("polite_count", 0),
                    register_report.get("plain_count", 0),
                    float(register_report.get("minor_ratio", 0.0) or 0.0),
                )

        lead = self._break_ending_monotony(lead)
        body = self._break_ending_monotony(body)
        if self._get_active_style_profile() != "casual":
            lead = self._cap_colloquial_endings(lead)
            body = self._cap_colloquial_endings(body)

        return lead.strip(), body.strip()
