"""Zero-base alignment / contract guard utility helpers for ArticleGenerator."""
from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from note import genre_manager
from note.policy_engine import resolve_category_policy

logger = logging.getLogger(__name__)


class ZeroBaseContractGuardMixin:
    @staticmethod
    def _zero_base_detect_ending_monotony(text: str) -> Dict[str, Any]:
        sample = re.sub(r"^##\s+.*$", "", text or "", flags=re.MULTILINE).strip()
        sentences = [s.strip() for s in re.split(r"(?<=[。！？!?])\s*", sample) if s.strip()]
        if not sentences:
            return {
                "sentence_count": 0,
                "dominant_ending_ratio": 0.0,
                "repetition_triplets": 0,
                "ending_histogram": {},
            }

        endings: List[str] = []
        for sentence in sentences:
            if re.search(r"ます[。！？!?]$", sentence):
                endings.append("masu")
            elif re.search(r"です[。！？!?]$", sentence):
                endings.append("desu")
            elif re.search(r"(した|だった|た)[。！？!?]$", sentence):
                endings.append("past")
            elif re.search(r"ない[。！？!?]$", sentence):
                endings.append("negative")
            else:
                endings.append(re.sub(r"\s+", "", sentence)[-3:])

        histogram: Dict[str, int] = {}
        for key in endings:
            histogram[key] = histogram.get(key, 0) + 1

        repetition_triplets = 0
        for idx in range(2, len(endings)):
            if endings[idx] == endings[idx - 1] == endings[idx - 2]:
                repetition_triplets += 1

        dominant = max(histogram.values()) if histogram else 0
        ratio = dominant / max(1, len(endings))
        return {
            "sentence_count": len(sentences),
            "dominant_ending_ratio": round(ratio, 4),
            "repetition_triplets": repetition_triplets,
            "ending_histogram": histogram,
        }

    def _zero_base_protect_datetime_literals(self, text: str) -> Tuple[str, Dict[str, str]]:
        raw = text or ""
        if not raw:
            return "", {}
        pattern = re.compile(
            r"(\d{4}年\d{1,2}月\d{1,2}日(?:\s*\d{1,2}:\d{2})?"
            r"|\d{1,2}月\d{1,2}日(?:\s*\d{1,2}:\d{2})?"
            r"|\d{1,2}:\d{2})"
        )
        replacements: Dict[str, str] = {}
        index = 0

        def _replacer(match: re.Match[str]) -> str:
            nonlocal index
            literal = match.group(0)
            key = f"__ZB_DT_{index:03d}__"
            replacements[key] = literal
            index += 1
            return key

        protected = pattern.sub(_replacer, raw)
        return protected, replacements

    def _zero_base_restore_datetime_literals(
        self,
        *,
        text: str,
        replacements: Dict[str, str],
    ) -> str:
        restored = text or ""
        if not replacements:
            return restored
        for key, literal in replacements.items():
            if key in restored:
                restored = restored.replace(key, literal)
        for literal in replacements.values():
            if literal and literal not in restored:
                restored = restored.rstrip() + f"\n\n{literal}"
        return restored.strip()

    @staticmethod
    def _zero_base_dedupe_list(items: List[str], *, limit: int = 10) -> List[str]:
        unique: List[str] = []
        for item in items:
            normalized = str(item or "").strip()
            if not normalized or normalized in unique:
                continue
            unique.append(normalized)
            if len(unique) >= limit:
                break
        return unique

    def _build_zero_base_forbidden_topics(
        self,
        *,
        article_type: str,
        user_prompt: str,
        merged_context: str,
        contract: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        contract = contract if isinstance(contract, dict) else {}
        contract_profile = self._resolve_zero_base_contract_profile(
            article_type=article_type,
            category_base_template=self._safe_contract_value(contract.get("category_base_template")),
        )
        profile_key = self._safe_contract_value(contract_profile.get("profile_key"))
        topics = list(contract_profile.get("forbidden_topics_base", []) or [])
        topics.extend(
            self._build_branding_forbidden_topics(
                article_type=article_type,
                user_prompt=user_prompt,
                merged_context=merged_context,
            )
        )
        prompt_context = f"{user_prompt or ''}\n{(merged_context or '')[:1600]}"
        speaker_profile = self._safe_contract_value(contract.get("speaker_profile"))
        audience_profile = self._safe_contract_value(contract.get("audience_profile"))
        relationship_mode = self._safe_contract_value(contract.get("relationship_mode")) or "guide"
        article_type_key = self._safe_contract_value(article_type).lower()
        introduction_context = bool(
            re.search(
                r"(自社の紹介|会社紹介|会社の紹介|初めての投稿|知ってほしい|まだほとんど知られていない|まだあまり知られていない)",
                prompt_context,
                re.I,
            )
        )
        leadership_context = bool(
            re.search(r"(トップメッセージ|代表取締役|創業者|経営者視点|経営者の視点|社長)", prompt_context, re.I)
            or re.search(r"(代表|創業者|経営者|社長|取締役|トップ)", speaker_profile, re.I)
        )
        if (
            introduction_context
            and profile_key in {"branding", "corporate_culture", "case_study"}
            and not self._is_recruiting_context(prompt_context)
        ):
            topics.extend(
                [
                    "採用候補者",
                    "採用活動",
                    "採用広報",
                    "応募方法",
                    "福利厚生",
                    "社内制度",
                    "選考フロー",
                ]
            )
        if leadership_context and profile_key in {"branding", "corporate_culture", "case_study"}:
            topics.extend(
                [
                    "採用候補者",
                    "採用広報",
                    "応募方法",
                    "福利厚生",
                ]
            )
        if article_type_key in {"corporate_culture", "company_profile", "corporate"}:
            topics.extend(
                [
                    "採用候補者",
                    "採用活動",
                    "福利厚生",
                ]
            )
        if relationship_mode != "guide":
            topics.extend(["一般論としての運用ノウハウ", "読者への一律な助言"])
        if (
            audience_profile
            and "採用" not in audience_profile
            and profile_key in {"branding", "corporate_culture"}
            and not self._is_recruiting_context(prompt_context)
        ):
            topics.extend(["採用候補者", "就職活動", "面接対策"])
        extra_topics = contract.get("forbidden_topics", [])
        if isinstance(extra_topics, list):
            topics.extend(self._safe_contract_value(item) for item in extra_topics)
        return self._zero_base_dedupe_list([topic for topic in topics if topic], limit=10)

    def _zero_base_allowed_pronouns(self, contract: Optional[Dict[str, Any]] = None) -> List[str]:
        contract = contract if isinstance(contract, dict) else {}
        contract_profile = self._resolve_zero_base_contract_profile(
            article_type=self._safe_contract_value(contract.get("article_type")),
            category_base_template=self._safe_contract_value(contract.get("category_base_template")),
        )
        profile_key = self._safe_contract_value(contract_profile.get("profile_key"))
        allowed: List[str] = list(contract_profile.get("default_allowed_pronouns", []) or [])
        allowed_hint = contract.get("allowed_pronouns_hint", [])
        if isinstance(allowed_hint, list):
            allowed.extend(self._safe_contract_value(item) for item in allowed_hint if self._safe_contract_value(item))
        current_pronoun = (getattr(self, "_current_pronoun", "") or "").strip()
        if current_pronoun:
            allowed.append(current_pronoun)
        speaker_profile = self._safe_contract_value(contract.get("speaker_profile"))
        relationship_mode = self._safe_contract_value(contract.get("relationship_mode")) or "guide"
        if re.search(r"(会社|企業|ブランド|当社|弊社|自社|経営者|代表|創業者|取締役|社長|トップ)", speaker_profile):
            allowed.extend(["私たち", "当社", "弊社"])
        elif re.search(r"(担当者|運営|執筆者|筆者|解説者)", speaker_profile):
            allowed.extend(["私", "わたし"])
        if profile_key == "ai_explanatory":
            allowed = [pronoun for pronoun in allowed if pronoun in {"私", "わたし"}]
            if not allowed:
                allowed = ["私"]
        if relationship_mode == "guide" and profile_key != "ai_explanatory":
            allowed.append("私たち")
        if profile_key == "announcement":
            allowed = [pronoun for pronoun in allowed if pronoun in {"当社", "弊社", "私たち"}]
            if not allowed:
                allowed = ["当社", "弊社"]
        if "わたし" in allowed and "私" not in allowed:
            allowed.append("私")
        if "私" in allowed and "わたし" not in allowed:
            allowed.append("わたし")
        return self._zero_base_dedupe_list(allowed, limit=6)

    def _analyze_zero_base_speaker_contract(
        self,
        *,
        text: str,
        contract: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        sample = text or ""
        contract = contract if isinstance(contract, dict) else {}
        speaker_profile = self._safe_contract_value(contract.get("speaker_profile"))
        relationship_mode = self._safe_contract_value(contract.get("relationship_mode")) or "guide"
        allowed_pronouns = self._zero_base_allowed_pronouns(contract)
        all_pronouns = ["私", "わたし", "僕", "俺", "私たち", "当社", "弊社"]
        disallowed_pronoun_hits = [
            pronoun for pronoun in all_pronouns if pronoun not in allowed_pronouns and pronoun and pronoun in sample
        ]
        leader_profile = bool(re.search(r"(創業者|代表|取締役|経営者|トップ|社長)", speaker_profile))
        first_person_hits = sum(sample.count(pronoun) for pronoun in allowed_pronouns if pronoun)
        third_person_patterns: List[str] = []
        if leader_profile:
            third_person_patterns = [
                r"(代表取締役|創業者|経営者|トップ)(?:の|は|が)",
                r"トップメッセージ",
                r"経営者の目線から語られる",
            ]
        third_person_speaker_mentions = sum(len(re.findall(pattern, sample)) for pattern in third_person_patterns)
        advice_tone_count = sum(
            len(re.findall(pattern, sample))
            for pattern in (
                r"するとよいでしょう",
                r"すると良いでしょう",
                r"ことが重要です",
                r"ことが効果的です",
                r"ことが望ましいでしょう",
                r"が鍵になります",
            )
        )
        detected_modes: List[str] = []
        if first_person_hits > 0:
            detected_modes.append("first_person")
        if third_person_speaker_mentions > 0:
            detected_modes.append("third_person_speaker")
        if advice_tone_count > 0:
            detected_modes.append("advisory")

        speaker_consistency_score = 1.0
        if speaker_profile and leader_profile and first_person_hits == 0:
            speaker_consistency_score = min(speaker_consistency_score, 0.45)
        if speaker_profile and disallowed_pronoun_hits:
            speaker_consistency_score = min(speaker_consistency_score, 0.35)
        if speaker_profile and third_person_speaker_mentions > 0:
            speaker_consistency_score = min(speaker_consistency_score, 0.35)
        if speaker_profile and first_person_hits > 0 and third_person_speaker_mentions > 0:
            speaker_consistency_score = min(speaker_consistency_score, 0.2)

        pronoun_consistency_score = 1.0 if not disallowed_pronoun_hits else 0.0
        if leader_profile and first_person_hits == 0 and third_person_speaker_mentions > 0:
            pronoun_consistency_score = min(pronoun_consistency_score, 0.35)

        relationship_consistency_score = 1.0
        if relationship_mode != "guide" and advice_tone_count >= 2:
            relationship_consistency_score = 0.35
        elif relationship_mode == "guide" and advice_tone_count == 0:
            relationship_consistency_score = 0.85

        hard_issue_count = 0
        if disallowed_pronoun_hits:
            hard_issue_count += 1
        if third_person_speaker_mentions > 0:
            hard_issue_count += 1
        if relationship_consistency_score < 0.5:
            hard_issue_count += 1

        return {
            "speaker_profile": speaker_profile,
            "relationship_mode": relationship_mode,
            "allowed_pronouns": allowed_pronouns,
            "detected_speaker_modes": detected_modes,
            "disallowed_pronoun_hits": self._zero_base_dedupe_list(disallowed_pronoun_hits, limit=6),
            "first_person_hits": int(first_person_hits),
            "third_person_speaker_mentions": int(third_person_speaker_mentions),
            "advice_tone_count": int(advice_tone_count),
            "speaker_consistency_score": round(float(max(0.0, speaker_consistency_score)), 4),
            "pronoun_consistency_score": round(float(max(0.0, pronoun_consistency_score)), 4),
            "relationship_consistency_score": round(float(max(0.0, relationship_consistency_score)), 4),
            "hard_issue_count": int(hard_issue_count),
        }

    def _zero_base_integrate_missing_must_cover(
        self,
        *,
        body: str,
        contract: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        text = body or ""
        must_cover_raw = contract.get("must_cover", [])
        if not isinstance(must_cover_raw, list):
            must_cover_raw = []
        must_cover = [
            self._normalize_must_cover_item(item, max_length=96)
            for item in must_cover_raw
            if self._normalize_must_cover_item(item, max_length=96)
        ]
        must_cover_for_body = [
            item for item in must_cover if not self._is_low_signal_must_cover_item(item)
        ]
        if not must_cover_for_body:
            return text, {
                "missing_count": 0,
                "integrated_count": 0,
                "integrated_items": [],
                "skipped_reason": "no_actionable_must_cover",
            }

        missing_items: List[str] = []
        for item in must_cover_for_body:
            if item not in text:
                missing_items.append(item)
        if not missing_items:
            return text, {
                "missing_count": 0,
                "integrated_count": 0,
                "integrated_items": [],
                "skipped_reason": "none_missing",
            }

        skipped_reason = "disabled_to_preserve_naturalness"
        if len(missing_items) >= 2:
            skipped_reason = "multi_missing_skip_for_naturalness"

        report = {
            "missing_count": len(missing_items),
            "integrated_count": 0,
            "integrated_items": [],
            "missing_items": missing_items[:10],
            "skipped_reason": skipped_reason,
        }
        return text.strip(), report

    def _extract_alignment_anchor_terms(self, text: str, *, max_terms: int = 8) -> List[str]:
        source = self._safe_contract_value(text)
        if not source:
            return []

        def _normalize_candidate(raw: str) -> str:
            candidate = self._safe_contract_value(raw).lower()
            if not candidate:
                return ""
            candidate = re.sub(r"^[\W_]+|[\W_]+$", "", candidate)
            candidate = re.sub(
                r"(を作成してください|を作成する|を作成|について|に関する|してください|したい|します|です|ます|こと)$",
                "",
                candidate,
            )
            candidate = candidate.strip("のをにはがでとへからまでやも")
            return candidate

        stop_terms = {
            "記事",
            "ブログ",
            "作成",
            "生成",
            "説明",
            "紹介",
            "内容",
            "こと",
            "ため",
            "ます",
            "です",
            "ください",
            "ブランディング",
        }
        tokens = self._extract_content_terms(source, max_chars=320)
        token_pool: List[str] = []
        for token in tokens:
            token_pool.append(token)
            token_pool.extend(re.split(r"(?:の|を|に|は|が|で|と|へ|から|まで|や|も)", token))
        token_pool.extend(
            re.findall(r"[一-龥々ぁ-んァ-ヴーA-Za-z0-9]{2,20}", source)
        )
        anchors: List[str] = []
        for token in token_pool:
            normalized = _normalize_candidate(token)
            if len(normalized) < 2:
                continue
            if normalized in stop_terms:
                continue
            if normalized.isdigit():
                continue
            if re.fullmatch(r"[ぁ-ん]{1,5}", normalized):
                continue
            if normalized in anchors:
                continue
            anchors.append(normalized)
            if len(anchors) >= max_terms:
                break
        return anchors

    def _extract_source_alignment_terms(
        self,
        source_text: str,
        *,
        prompt_terms: List[str],
        max_terms: int = 8,
    ) -> List[str]:
        source = self._safe_contract_value(source_text)
        if not source:
            return []
        tokens = self._extract_content_terms(source, max_chars=3200)
        if not tokens:
            return []
        counter: Counter[str] = Counter()
        generic_terms = {
            "記事",
            "情報",
            "詳細",
            "内容",
            "ページ",
            "会社",
            "株式会社",
            "カテゴリ",
            "について",
            "など",
        }
        for token in tokens:
            normalized = self._safe_contract_value(token).lower()
            if len(normalized) < 2:
                continue
            if normalized in generic_terms:
                continue
            if normalized.isdigit():
                continue
            counter[normalized] += 1
        if not counter:
            return []
        ranked_terms = [term for term, _ in counter.most_common(40)]
        selected: List[str] = []
        for term in ranked_terms:
            if prompt_terms and not any((p in term or term in p) for p in prompt_terms):
                continue
            selected.append(term)
            if len(selected) >= max_terms:
                return selected
        if len(selected) < max_terms:
            for term in ranked_terms:
                if term in selected:
                    continue
                selected.append(term)
                if len(selected) >= max_terms:
                    break
        return selected

    @staticmethod
    def _compute_section_focus_coverage(body: str, anchor_terms: List[str]) -> Tuple[float, int, int]:
        sample = body or ""
        if not sample:
            return 1.0, 0, 0
        if not anchor_terms:
            return 1.0, 0, 0
        sections = re.split(r"(?m)^##\s+", sample)
        section_bodies: List[str] = []
        for block in sections:
            text = (block or "").strip()
            if not text:
                continue
            if "\n" in text:
                _, content = text.split("\n", 1)
            else:
                content = text
            if not content.strip():
                continue
            section_bodies.append(content.strip())
        if not section_bodies:
            return 1.0, 0, 0
        hits = 0
        for section_text in section_bodies:
            lowered = section_text.lower()
            if any(term and term in lowered for term in anchor_terms):
                hits += 1
        total = len(section_bodies)
        coverage = hits / total if total > 0 else 1.0
        return coverage, hits, total

    def _zero_base_compute_contract_alignment(
        self,
        *,
        contract: Dict[str, Any],
        body: str,
        question_sources: Optional[Dict[str, str]] = None,
        source_text: str = "",
    ) -> Dict[str, Any]:
        metrics: Dict[str, Any] = {
            "category_consistency_score": 0.0,
            "question_reflection_rate": 0.0,
        }
        try:
            from note.zero_base.phase01_baseline_contract import compute_contract_kpis

            metrics = dict(compute_contract_kpis(contract))
        except Exception as exc:
            logger.debug("Contract KPI computation skipped (fail-open).", exc_info=exc)

        article_type = self._safe_contract_value(contract.get("article_type")).lower()
        category_base_template = self._safe_contract_value(contract.get("category_base_template")).lower()
        category_policy_source = self._safe_contract_value(contract.get("category_policy_source")).lower()
        expected_base_template = ""
        custom_meta: Dict[str, Any] = {}
        if category_policy_source == "custom_meta" and category_base_template:
            expected_base_template = category_base_template
        elif article_type:
            try:
                custom_genre = genre_manager.get_genre(article_type)
                if isinstance(custom_genre, dict):
                    maybe_meta = custom_genre.get("meta")
                    if isinstance(maybe_meta, dict):
                        custom_meta = dict(maybe_meta)
            except Exception as exc:
                logger.debug("Custom genre resolve for alignment failed (fail-open).", exc_info=exc)
                custom_meta = {}
            try:
                expected_base_template = self._safe_contract_value(
                    resolve_category_policy(
                        article_type,
                        custom_meta=custom_meta or None,
                    ).base_template
                ).lower()
            except Exception as exc:
                logger.debug("Category policy resolve for alignment failed (fail-open).", exc_info=exc)
                expected_base_template = ""
        category_missing = not bool(category_base_template)
        category_mismatch = bool(
            expected_base_template
            and category_base_template
            and expected_base_template != category_base_template
        )
        category_consistency_score = (
            1.0
            if (
                expected_base_template
                and category_base_template
                and expected_base_template == category_base_template
            )
            else 0.0
        )
        if not expected_base_template and category_policy_source == "custom_meta" and category_base_template:
            category_consistency_score = 1.0
        metrics["category_consistency_score"] = category_consistency_score

        must_cover_raw = contract.get("must_cover", [])
        must_cover = [
            self._safe_contract_value(item)
            for item in (must_cover_raw if isinstance(must_cover_raw, list) else [])
            if self._safe_contract_value(item)
        ]
        must_cover_for_eval = [
            item for item in must_cover if not self._is_low_signal_must_cover_item(item)
        ]
        normalized_body = body or ""
        unresolved_raw = contract.get("unresolved_items", [])
        unresolved_items = [
            self._safe_contract_value(item)
            for item in (unresolved_raw if isinstance(unresolved_raw, list) else [])
            if self._safe_contract_value(item)
        ]
        reflected = 0
        normalized_body_lower = normalized_body.lower()
        for item in must_cover_for_eval:
            normalized_item = self._normalize_must_cover_item(item, max_length=120)
            if item and item in normalized_body:
                reflected += 1
                continue
            if normalized_item and normalized_item in normalized_body:
                reflected += 1
                continue
            item_terms = self._extract_alignment_anchor_terms(
                normalized_item or item,
                max_terms=4,
            )
            if item_terms and any(term and term in normalized_body_lower for term in item_terms):
                reflected += 1
        must_cover_reflection_rate = (
            reflected / len(must_cover_for_eval)
            if must_cover_for_eval
            else 1.0
        )
        questions_raw = contract.get("pre_generation_questions", [])
        question_ids: List[str] = []
        if isinstance(questions_raw, list):
            for item in questions_raw:
                if not isinstance(item, dict):
                    continue
                qid = self._safe_contract_value(item.get("id"))
                if qid:
                    question_ids.append(qid)

        source_map: Dict[str, str] = {}
        if isinstance(question_sources, dict):
            for qid, src in question_sources.items():
                question_id = self._safe_contract_value(qid)
                source_key = self._safe_contract_value(src)
                if question_id:
                    source_map[question_id] = source_key

        source_counts = {
            "interview_answers": 0,
            "user_prompt": 0,
            "unresolved_items": 0,
            "unknown": 0,
        }
        unknown_ids: List[str] = []
        for qid in question_ids:
            src = source_map.get(qid, "")
            if src in source_counts:
                source_counts[src] += 1
            else:
                source_counts["unknown"] += 1
                if qid:
                    unknown_ids.append(qid)

        missing_source_ids = [qid for qid in question_ids if qid not in source_map]
        mapped_question_count = max(
            0,
            len(question_ids) - len(missing_source_ids) - len(unknown_ids),
        )
        question_source_coverage = (
            mapped_question_count / len(question_ids)
            if question_ids
            else 1.0
        )
        unresolved_penalty = (
            min(1.0, len(unresolved_items) / max(1, len(question_ids)))
            if question_ids
            else 0.0
        )
        prompt_anchor_terms = self._extract_alignment_anchor_terms(
            getattr(self, "_latest_user_prompt", ""),
            max_terms=8,
        )
        must_cover_anchor_terms = [
            self._safe_contract_value(item).lower()
            for item in must_cover_for_eval
            if self._safe_contract_value(item)
        ]
        source_anchor_terms = self._extract_source_alignment_terms(
            source_text,
            prompt_terms=prompt_anchor_terms,
            max_terms=8,
        )
        anchor_terms: List[str] = []
        for term in [*prompt_anchor_terms, *must_cover_anchor_terms, *source_anchor_terms]:
            normalized = self._safe_contract_value(term).lower()
            if not normalized:
                continue
            if normalized in anchor_terms:
                continue
            anchor_terms.append(normalized)
        prompt_anchor_hits = sum(1 for term in prompt_anchor_terms if term and term in normalized_body_lower)
        prompt_anchor_coverage = (
            prompt_anchor_hits / len(prompt_anchor_terms)
            if prompt_anchor_terms
            else 1.0
        )
        anchor_term_hits = sum(1 for term in anchor_terms if term and term in normalized_body_lower)
        anchor_term_coverage = (
            anchor_term_hits / len(anchor_terms)
            if anchor_terms
            else 1.0
        )
        section_focus_coverage, section_focus_hits, section_focus_total = self._compute_section_focus_coverage(
            normalized_body,
            anchor_terms,
        )
        raw_alignment_score = (
            float(metrics.get("category_consistency_score", 0.0) or 0.0) * 0.40
            + float(metrics.get("question_reflection_rate", 0.0) or 0.0) * 0.30
            + float(must_cover_reflection_rate) * 0.30
            - unresolved_penalty * 0.15
        )
        if category_missing or category_mismatch:
            raw_alignment_score -= 0.15
        if anchor_term_coverage < 0.35:
            raw_alignment_score -= 0.15
        branding_like = article_type in {"branding", "case_study"} or category_base_template == "branding"
        if branding_like and section_focus_total >= 3 and section_focus_coverage < 0.75:
            raw_alignment_score -= 0.20
        alignment_score = max(0.0, min(1.0, raw_alignment_score))

        audience_label_mentions = self._count_audience_label_mentions(
            normalized_body,
            self._safe_contract_value(contract.get("audience")),
        )
        speaker_profile = self._safe_contract_value(contract.get("speaker_profile"))
        audience_profile = self._safe_contract_value(contract.get("audience_profile"))
        register_policy = self._normalize_register_policy(contract.get("register_policy"))
        register_report = self._analyze_style_register(normalized_body)
        register_drift_index = float(register_report.get("minor_ratio", 0.0) or 0.0)
        speaker_contract_report = self._analyze_zero_base_speaker_contract(
            text=normalized_body,
            contract=contract,
        )
        pronoun_conflict = bool(
            self._has_pronoun_conflict(normalized_body)
            or bool(speaker_contract_report.get("disallowed_pronoun_hits"))
        )
        speaker_consistency_score = float(speaker_contract_report.get("speaker_consistency_score", 0.0) or 0.0)
        audience_address_consistency = 1.0 if audience_profile else 0.0
        if audience_profile and audience_label_mentions > 4:
            audience_address_consistency = 0.7
        relationship_consistency_score = float(
            speaker_contract_report.get("relationship_consistency_score", 1.0) or 1.0
        )
        source_urls = list(getattr(self, "_source_urls", []) or [])
        source_trace_hits = sum(1 for url in source_urls if url and url in normalized_body)
        source_trace_coverage = (
            source_trace_hits / len(source_urls)
            if source_urls
            else 1.0
        )
        forbidden_topics_raw = contract.get("forbidden_topics", [])
        forbidden_topics = [
            self._safe_contract_value(item).lower()
            for item in (forbidden_topics_raw if isinstance(forbidden_topics_raw, list) else [])
            if self._safe_contract_value(item)
        ]
        forbidden_topic_hits = self._collect_forbidden_topic_hits(
            normalized_body,
            forbidden_topics,
        )
        if forbidden_topic_hits:
            raw_alignment_score -= min(0.45, 0.25 + 0.08 * (len(forbidden_topic_hits) - 1))
            alignment_score = max(0.0, min(1.0, raw_alignment_score))
        if speaker_consistency_score < 0.55:
            alignment_score = max(0.0, round(alignment_score - 0.30, 4))
        if float(speaker_contract_report.get("pronoun_consistency_score", 1.0) or 1.0) < 0.5:
            alignment_score = max(0.0, round(alignment_score - 0.20, 4))
        if relationship_consistency_score < 0.5:
            alignment_score = max(0.0, round(alignment_score - 0.15, 4))
        contract_alignment_reason_codes: List[str] = []
        if speaker_consistency_score < 0.55:
            contract_alignment_reason_codes.append("speaker_consistency")
        if float(speaker_contract_report.get("pronoun_consistency_score", 1.0) or 1.0) < 0.5:
            contract_alignment_reason_codes.append("pronoun_consistency")
        if relationship_consistency_score < 0.5:
            contract_alignment_reason_codes.append("relationship_consistency")
        if forbidden_topic_hits:
            contract_alignment_reason_codes.append("forbidden_topics")
        section_contract_reports = getattr(self, "_zero_base_section_guard_reports", [])
        section_contract_issue_count = sum(
            int(item.get("blocking_issue_count", 0) or 0)
            for item in section_contract_reports
            if isinstance(item, dict)
        )
        if section_contract_issue_count > 0:
            contract_alignment_reason_codes.append("section_contract_issue")
        contract_alignment_risk = bool(contract_alignment_reason_codes)

        return {
            "category_consistency_score": float(metrics.get("category_consistency_score", 0.0) or 0.0),
            "question_reflection_rate": float(metrics.get("question_reflection_rate", 0.0) or 0.0),
            "alignment_score": round(alignment_score, 4),
            "category_expected_base_template": expected_base_template,
            "category_base_template": category_base_template,
            "category_base_template_missing": category_missing,
            "category_mismatch_detected": category_mismatch,
            "must_cover_count": len(must_cover),
            "must_cover_eval_count": len(must_cover_for_eval),
            "must_cover_reflected_count": reflected,
            "must_cover_reflection_rate": round(must_cover_reflection_rate, 4),
            "must_cover_items": must_cover[:12],
            "prompt_anchor_terms": prompt_anchor_terms[:12],
            "source_anchor_terms": source_anchor_terms[:12],
            "anchor_terms": anchor_terms[:14],
            "prompt_anchor_coverage": round(float(prompt_anchor_coverage), 4),
            "anchor_term_coverage": round(float(anchor_term_coverage), 4),
            "section_focus_coverage": round(float(section_focus_coverage), 4),
            "section_focus_hits": int(section_focus_hits),
            "section_focus_total": int(section_focus_total),
            "unresolved_count": len(unresolved_items),
            "unresolved_items": unresolved_items[:12],
            "question_count": len(question_ids),
            "question_source_counts": source_counts,
            "question_source_coverage": round(question_source_coverage, 4),
            "question_source_missing_ids": missing_source_ids[:12],
            "question_source_unknown_ids": unknown_ids[:12],
            "resolved_question_sources": source_map,
            "audience_label_mentions": int(audience_label_mentions),
            "speaker_profile": speaker_profile,
            "audience_profile": audience_profile,
            "topic_statement": self._normalize_topic_statement_value(contract.get("topic_statement"), max_length=180),
            "relationship_mode": self._safe_contract_value(contract.get("relationship_mode")),
            "register_policy": register_policy,
            "speaker_consistency_score": round(float(speaker_consistency_score), 4),
            "relationship_consistency_score": round(float(relationship_consistency_score), 4),
            "audience_address_consistency": round(float(audience_address_consistency), 4),
            "register_drift_index": round(float(register_drift_index), 4),
            "pronoun_consistency_score": round(
                float(speaker_contract_report.get("pronoun_consistency_score", 0.0 if pronoun_conflict else 1.0) or 0.0),
                4,
            ),
            "source_trace_coverage": round(float(source_trace_coverage), 4),
            "forbidden_topic_hit_count": len(forbidden_topic_hits),
            "forbidden_topic_hits": forbidden_topic_hits[:12],
            "allowed_pronouns": list(speaker_contract_report.get("allowed_pronouns", []) or [])[:6],
            "detected_speaker_modes": list(speaker_contract_report.get("detected_speaker_modes", []) or [])[:6],
            "disallowed_pronoun_hits": list(speaker_contract_report.get("disallowed_pronoun_hits", []) or [])[:6],
            "speaker_third_person_mentions": int(speaker_contract_report.get("third_person_speaker_mentions", 0) or 0),
            "speaker_advice_tone_count": int(speaker_contract_report.get("advice_tone_count", 0) or 0),
            "section_contract_issue_count": int(section_contract_issue_count),
            "contract_alignment_risk": contract_alignment_risk,
            "contract_alignment_reason_codes": contract_alignment_reason_codes[:8],
        }

    @staticmethod
    def _collect_forbidden_topic_hits(text: str, topics: List[str]) -> List[str]:
        sample = (text or "").lower()
        if not sample or not topics:
            return []
        hits: List[str] = []
        for topic in topics:
            normalized = str(topic or "").strip().lower()
            if not normalized:
                continue
            if normalized in sample and normalized not in hits:
                hits.append(normalized)
        return hits

    @staticmethod
    def _is_recruiting_context(text: str) -> bool:
        sample = (text or "").strip()
        if not sample:
            return False
        return bool(
            re.search(
                r"(採用|応募|求職|就職|候補者|面接|人事|リクルート|カルチャー|社風|働き方|社員紹介)",
                sample,
                re.I,
            )
        )

    def _build_branding_forbidden_topics(
        self,
        *,
        article_type: str,
        user_prompt: str,
        merged_context: str,
    ) -> List[str]:
        if self._safe_contract_value(article_type).lower() != "branding":
            return []
        prompt_context = f"{user_prompt or ''}\n{(merged_context or '')[:1200]}"
        if self._is_recruiting_context(prompt_context):
            return []
        product_intent = bool(
            re.search(
                r"(商品|製品|サービス|メニュー|加工品|ブランド|価値|選び方|活用|導入|品質)",
                prompt_context,
                re.I,
            )
        )
        if not product_intent:
            return []
        return [
            "採用候補者",
            "採用広報",
            "企業カルチャー",
            "社内制度",
            "チーム連携",
            "福利厚生",
        ]
