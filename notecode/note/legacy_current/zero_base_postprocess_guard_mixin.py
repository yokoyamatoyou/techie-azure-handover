"""Zero-base postprocess/guard utility helpers for ArticleGenerator."""
from __future__ import annotations

import logging
import random
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

from core.app_config import get_semantic_dedupe_config
from note.zero_base.semantic_dedupe import semantic_dedupe_text

logger = logging.getLogger(__name__)


class ZeroBasePostprocessGuardMixin:
    def _zero_base_get_linebreak_profile(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        natural_style_profile = contract.get("natural_style_profile", {})
        if isinstance(natural_style_profile, dict):
            profile_name = self._safe_contract_value(natural_style_profile.get("linebreak_profile")).lower()
            if profile_name == "announcement_compact":
                return {
                    "profile": "announcement_compact",
                    "sentence_min": 1,
                    "sentence_max": 2,
                    "max_chars": 120,
                }
            if profile_name == "analysis_balanced":
                return {
                    "profile": "analysis_balanced",
                    "sentence_min": 2,
                    "sentence_max": 3,
                    "max_chars": 170,
                }
            if profile_name == "branding_story":
                return {
                    "profile": "branding_story",
                    "sentence_min": 2,
                    "sentence_max": 5,
                    "max_chars": 260,
                }
        article_type = self._safe_contract_value(contract.get("article_type")).lower()
        base_template = self._safe_contract_value(contract.get("category_base_template")).lower()
        if article_type == "announcement" or base_template == "announcement":
            return {
                "profile": "announcement_compact",
                "sentence_min": 1,
                "sentence_max": 2,
                "max_chars": 120,
            }
        if article_type in {"ai", "explanatory_article"} or base_template == "ai":
            return {
                "profile": "analysis_balanced",
                "sentence_min": 2,
                "sentence_max": 3,
                "max_chars": 170,
            }
        if article_type in {"branding", "corporate_culture"} or base_template == "branding":
            return {
                "profile": "branding_story",
                "sentence_min": 2,
                "sentence_max": 5,
                "max_chars": 260,
            }
        return {
            "profile": "default_balanced",
            "sentence_min": 2,
            "sentence_max": 3,
            "max_chars": 160,
        }

    def _zero_base_apply_linebreak_profile(
        self,
        *,
        body: str,
        contract: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        if not body:
            return "", {"profile": "none", "paragraph_before": 0, "paragraph_after": 0}

        profile = self._zero_base_get_linebreak_profile(contract)
        sentence_min = max(1, int(profile.get("sentence_min", 2) or 2))
        sentence_max = max(sentence_min, int(profile.get("sentence_max", 3) or 3))
        max_chars = max(100, int(profile.get("max_chars", 160) or 160))

        normalized = self._normalize_paragraphs(body)
        paragraph_before = len([p for p in re.split(r"\n{2,}", normalized) if p.strip()])
        sections = self._extract_section_blocks(normalized)
        if not sections:
            lined = self._add_note_sentence_linebreaks(normalized)
            paragraph_after = len([p for p in re.split(r"\n{2,}", lined) if p.strip()])
            return lined, {
                "profile": str(profile.get("profile", "default_balanced")),
                "sentence_min": sentence_min,
                "sentence_max": sentence_max,
                "max_chars": max_chars,
                "paragraph_before": paragraph_before,
                "paragraph_after": paragraph_after,
            }

        rebuilt_sections: List[str] = []
        for sec_idx, (heading, content) in enumerate(sections):
            paragraphs = [p.strip() for p in re.split(r"\n{2,}", content) if p.strip()]
            rebuilt_paragraphs: List[str] = []
            for para_idx, paragraph in enumerate(paragraphs):
                stripped = paragraph.strip()
                if (
                    not stripped
                    or stripped.startswith("##")
                    or self._is_reference_or_list_paragraph(stripped)
                    or re.match(r"^https?://", stripped)
                ):
                    rebuilt_paragraphs.append(stripped)
                    continue
                sentences = [s for s in re.split(r"(?<=[。！？!?])\s*", stripped) if s.strip()]
                if len(sentences) <= sentence_min:
                    rebuilt_paragraphs.append(stripped)
                    continue
                if (
                    len(sentences) <= (sentence_max + 1)
                    and len(stripped) <= int(max_chars * 1.18)
                ):
                    rebuilt_paragraphs.append(stripped)
                    continue

                chunks: List[str] = []
                index = 0
                para_seed = self._stable_text_seed(stripped)
                rng = random.Random((para_seed + sec_idx * 17 + para_idx * 31) & 0xFFFFFFFF)
                while index < len(sentences):
                    span_range = sentence_max - sentence_min + 1
                    target_sentences = sentence_min + (
                        rng.randint(0, max(0, span_range - 1))
                    )
                    remaining = len(sentences) - index
                    if remaining <= sentence_max:
                        target_sentences = remaining
                    bucket: List[str] = []
                    paragraph_limit = int(max_chars * (1.0 + rng.uniform(-0.06, 0.12)))
                    while index < len(sentences):
                        candidate = sentences[index].strip()
                        if not candidate:
                            index += 1
                            continue
                        tentative = "".join(bucket + [candidate]).strip()
                        if (
                            bucket
                            and len(tentative) > paragraph_limit
                            and len(bucket) >= sentence_min
                        ):
                            break
                        bucket.append(candidate)
                        index += 1
                        if len(bucket) >= target_sentences:
                            break
                    if not bucket and index < len(sentences):
                        bucket = [sentences[index].strip()]
                        index += 1
                    chunk = "".join(bucket).strip()
                    if chunk:
                        chunks.append(chunk)
                if chunks:
                    rebuilt_paragraphs.extend(chunks)
                else:
                    rebuilt_paragraphs.append(stripped)
            rebuilt_content = "\n\n".join(p for p in rebuilt_paragraphs if p).strip()
            rebuilt_sections.append(f"## {heading}\n\n{rebuilt_content}".strip())

        profiled_body = "\n\n".join(rebuilt_sections).strip()
        paragraph_after = len([p for p in re.split(r"\n{2,}", profiled_body) if p.strip()])
        return profiled_body, {
            "profile": str(profile.get("profile", "default_balanced")),
            "sentence_min": sentence_min,
            "sentence_max": sentence_max,
            "max_chars": max_chars,
            "paragraph_before": paragraph_before,
            "paragraph_after": paragraph_after,
        }

    def _zero_base_semantic_dedupe(
        self,
        *,
        body: str,
        contract: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        dedupe_config = dict(getattr(self, "_semantic_dedupe_config", {}) or {})
        if not dedupe_config:
            dedupe_config = get_semantic_dedupe_config()
        rewrite_enabled = bool(dedupe_config.get("rewrite_enabled", False))

        if not dedupe_config.get("enabled", True):
            return body or "", {
                "model": str(dedupe_config.get("model") or "text-embedding-3-small"),
                "rewrite_enabled": rewrite_enabled,
                "rewrite_applied": False,
                "sentence_count": 0,
                "compared_pairs": 0,
                "duplicate_pairs": 0,
                "merged_pairs": 0,
                "fail_open": False,
                "fail_reason": "disabled",
                "must_cover_protected_count": 0,
                "category_protected_count": 0,
                "regenerated_paragraphs": 0,
                "redaction_applied_count": 0,
            }

        try:
            deduped, audit = semantic_dedupe_text(
                body or "",
                contract,
                config=dedupe_config,
                embedder=getattr(self, "_zero_base_embedding_provider", None),
            )
            if not isinstance(audit, dict):
                audit = {}
            audit["rewrite_enabled"] = rewrite_enabled
            if rewrite_enabled:
                audit["rewrite_applied"] = True
                return deduped, audit
            audit["rewrite_applied"] = False
            return body or "", audit
        except Exception as exc:
            logger.warning("Zero-base semantic dedupe failed. Continue with fail-open body.")
            logger.debug("Zero-base semantic dedupe detail.", exc_info=exc)
            return body or "", {
                "model": str(dedupe_config.get("model") or "text-embedding-3-small"),
                "rewrite_enabled": rewrite_enabled,
                "rewrite_applied": False,
                "sentence_count": 0,
                "compared_pairs": 0,
                "duplicate_pairs": 0,
                "merged_pairs": 0,
                "fail_open": True,
                "fail_reason": f"unexpected_exception:{type(exc).__name__}",
                "must_cover_protected_count": 0,
                "category_protected_count": 0,
                "regenerated_paragraphs": 0,
                "redaction_applied_count": 0,
            }

    def _zero_base_minimal_postprocess(
        self,
        *,
        lead: str,
        body: str,
        target_audience: str,
        contract: Dict[str, Any],
    ) -> Tuple[str, str, Dict[str, Any]]:
        protected_items = self._zero_base_collect_protected_items(contract=contract, body=body)
        heading_before = self._heading_count(body)

        processed_lead = self._clean_meta_output(lead, target_audience)
        processed_body = self._clean_meta_output(body, target_audience)
        processed_lead = self._zero_base_normalize_layout_minimal(processed_lead)
        processed_body = self._zero_base_normalize_layout_minimal(processed_body)
        processed_lead = self._zero_base_light_grammar_fix(processed_lead)
        processed_body = self._zero_base_light_grammar_fix(processed_body)
        processed_lead = self._zero_base_apply_sanitize_pass(processed_lead)
        processed_body = self._zero_base_apply_sanitize_pass(processed_body)
        processed_body = self._zero_base_restore_protected_items(
            text=processed_body,
            protected_items=protected_items,
        )
        processed_body = self._zero_base_enforce_announcement_fact_consistency(
            processed_body,
            contract,
        )

        heading_after = self._heading_count(processed_body)
        if heading_before and heading_after != heading_before:
            processed_body = body
            heading_after = heading_before

        audit = {
            "applied_steps": [
                "line_level_meta_cleanup",
                "layout_normalization",
                "light_grammar_fix",
                "phase7_sanitize",
            ],
            "disabled_paths": [
                "resonance_multi_phase_corrections",
                "quality_rewrite_path",
                "repair_only_large_rewrite",
            ],
            "rewrite_ratio_lead": self._compute_rewrite_ratio(lead, processed_lead),
            "rewrite_ratio_body": self._compute_rewrite_ratio(body, processed_body),
            "heading_preserved": heading_before == heading_after,
            "must_cover_protected_count": len(protected_items.get("must_cover", [])),
            "category_required_protected_count": len(protected_items.get("category_required", [])),
        }
        return processed_lead.strip(), processed_body.strip(), audit

    @staticmethod
    def _relax_note_quality_gate(hard_soft_eval: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(hard_soft_eval, dict):
            return {"enabled": False, "mode": "off"}
        relaxed = dict(hard_soft_eval)
        reasons = list(relaxed.get("hard_fail_reasons", []) or [])
        warnings = list(relaxed.get("soft_warnings", []) or [])
        for reason in reasons:
            reason_text = str(reason or "").strip()
            if not reason_text:
                continue
            warnings.append(f"observe_only:{reason_text}")
        relaxed["hard_failed"] = False
        relaxed["hard_fail_reasons"] = []
        relaxed["soft_warnings"] = warnings
        if relaxed.get("enabled"):
            relaxed["mode"] = "observe_only"
        return relaxed

    @staticmethod
    def _compute_rewrite_ratio(before: str, after: str) -> float:
        before_text = before or ""
        after_text = after or ""
        if not before_text and not after_text:
            return 0.0
        if not before_text:
            return 1.0
        return round(max(0.0, min(1.0, 1.0 - SequenceMatcher(None, before_text, after_text).ratio())), 4)

    @staticmethod
    def _zero_base_normalize_layout_minimal(text: str) -> str:
        normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        normalized = re.sub(r"(?m)^(#{2,}[^\n]*)\n(?!\n)", r"\1\n\n", normalized)
        return normalized.strip()

    @staticmethod
    def _zero_base_light_grammar_fix(text: str) -> str:
        fixed = text or ""
        fixed = re.sub(r"\s+([、。！？!?])", r"\1", fixed)
        fixed = re.sub(r"、{2,}", "、", fixed)
        fixed = re.sub(r"。{2,}", "。", fixed)
        fixed = re.sub(r"！{2,}", "！", fixed)
        fixed = re.sub(r"？{2,}", "？", fixed)
        fixed = re.sub(r"([。！？!?])\s*([。！？!?])", r"\1", fixed)
        return fixed

    def _zero_base_collect_protected_items(
        self,
        *,
        contract: Dict[str, Any],
        body: str,
    ) -> Dict[str, List[str]]:
        protected_must_cover: List[str] = []
        must_cover = contract.get("must_cover", [])
        if isinstance(must_cover, list):
            for item in must_cover:
                normalized = self._safe_contract_value(item)
                if normalized:
                    protected_must_cover.append(normalized)

        protected_category: List[str] = []
        article_type = self._safe_contract_value(contract.get("article_type")).lower()
        category_template = self._safe_contract_value(contract.get("category_base_template")).lower()
        is_announcement = article_type == "announcement" or category_template == "announcement"
        if is_announcement:
            datetime_re = re.compile(
                r"(\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}月\d{1,2}日|\d{1,2}:\d{2}|午前|午後|\d{1,2}時)"
            )
            for sentence in re.split(r"(?<=[。！？!?])\s*", body or ""):
                sentence = sentence.strip()
                if sentence and datetime_re.search(sentence):
                    protected_category.append(sentence)

        return {
            "must_cover": protected_must_cover,
            "category_required": protected_category,
        }

    def _zero_base_restore_protected_items(
        self,
        *,
        text: str,
        protected_items: Dict[str, List[str]],
    ) -> str:
        restored = text or ""
        category_required = protected_items.get("category_required", [])
        if isinstance(category_required, list):
            has_any_category_line = any(
                self._safe_contract_value(item) and self._safe_contract_value(item) in restored
                for item in category_required
            )
            if category_required and not has_any_category_line:
                restored = restored.rstrip() + "\n\n" + self._safe_contract_value(category_required[0])
        return restored.strip()

    def _zero_base_align_corporate_voice(self, text: str, contract: Dict[str, Any]) -> str:
        sample = text or ""
        if not sample:
            return sample
        article_type = self._safe_contract_value(contract.get("article_type")).lower()
        base_template = self._safe_contract_value(contract.get("category_base_template")).lower()
        if article_type not in {"corporate_culture", "daily_happenings"} and base_template != "branding":
            return sample
        normalized = sample
        normalized = re.sub(r"(?<!たち)わたし(?=の|は|が|を|に|で|へ|と|も|から|より|には|では|、|。)", "私たち", normalized)
        normalized = re.sub(r"(?<!たち)私(?=の|は|が|を|に|で|へ|と|も|から|より|には|では|、|。)", "私たち", normalized)
        return normalized

    def _zero_base_apply_minimal_legal_guard(
        self,
        *,
        body: str,
        contract: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        text = body or ""
        report: Dict[str, Any] = {
            "risk_hits": 0,
            "rewritten_lines": 0,
            "protected_risk_hits": 0,
            "caution_appended": 0,
            "fail_open": False,
        }

        must_cover = contract.get("must_cover", [])
        must_cover_items = []
        if isinstance(must_cover, list):
            must_cover_items = [self._safe_contract_value(item) for item in must_cover if self._safe_contract_value(item)]

        guarantee_replacements = [
            (re.compile(r"100%\s*"), "高い確率で"),
            (re.compile(r"絶対に"), "原則として"),
            (re.compile(r"必ず((?:ご確認|お確かめ)(?:ください|願います|をお願いします|いただきますようお願いいたします))"), r"\1"),
            (re.compile(r"必ず"), "多くの場合"),
            (re.compile(r"確実に"), "可能性が高く"),
            (re.compile(r"保証します"), "目標としています"),
        ]
        strong_assertion = re.compile(r"(問題ありません|心配ありません|断言できます|絶対に|必ず|100%)")
        sensitive_domain = re.compile(r"(医療|治療|診断|薬|法令|法律|違法|合法)")

        try:
            rewritten_lines: List[str] = []
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("- "):
                    rewritten_lines.append(line)
                    continue

                if any(marker and marker in stripped for marker in must_cover_items):
                    if sensitive_domain.search(stripped) and strong_assertion.search(stripped):
                        report["protected_risk_hits"] += 1
                    rewritten_lines.append(line)
                    continue

                rewritten = line
                replaced = False
                for pattern, replacement in guarantee_replacements:
                    if pattern.search(rewritten):
                        rewritten = pattern.sub(replacement, rewritten)
                        replaced = True
                        report["risk_hits"] += 1

                if sensitive_domain.search(rewritten) and strong_assertion.search(rewritten):
                    rewritten = rewritten.rstrip() + "（個別事情で結論が変わるため、専門家確認を推奨します。）"
                    replaced = True
                    report["risk_hits"] += 1
                    report["caution_appended"] += 1

                if replaced and rewritten != line:
                    report["rewritten_lines"] += 1
                rewritten_lines.append(rewritten)

            return "\n".join(rewritten_lines).strip(), report
        except Exception as exc:
            logger.warning("Zero-base minimal legal guard failed. Continue with fail-open body.")
            logger.debug("Zero-base minimal legal guard detail.", exc_info=exc)
            report["fail_open"] = True
            report["error"] = type(exc).__name__
            return text, report

    @staticmethod
    def _count_zero_base_risk_markers(text: str) -> int:
        if not text:
            return 0
        pattern = re.compile(r"(100%|絶対に|必ず|確実に|保証します|問題ありません|心配ありません|断言できます)")
        return len(pattern.findall(text))
