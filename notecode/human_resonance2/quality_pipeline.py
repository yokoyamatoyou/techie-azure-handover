"""Quality pipeline runner for human_resonance2 phased rollout."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.app_config import QualityPipelineConfig, map_content_type_to_profile
from .fingerprint_metrics import (
    CorrectionResult,
    FingerprintAnalyzer,
    FingerprintReport,
    ResonanceTuningResult,
    apply_fingerprint_corrections,
    compute_resonance_tuning,
)
from .phase01_lexical_diversity import Phase01LexicalDiversity
from .phase02_burstiness import Phase02Burstiness
from .phase03_nominalization import Phase03Nominalization
from .phase04_style_drift import Phase04StyleDrift
from .phase05_layout_guard import Phase05LayoutGuard
from .phase06_orchestrator import Phase06Orchestrator
from .phase07_rollout import Phase07IntegrationRollout, RolloutDecision


logger = logging.getLogger(__name__)


@dataclass
class QualityPipelineResult:
    text: str
    phase_reports: List[Dict[str, Any]] = field(default_factory=list)
    applied: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    mode_resolution: Dict[str, Any] = field(default_factory=dict)


def format_monitoring_report(phase_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Format fingerprint metrics into a standardized monitoring report (R7-T01).

    Extracts fingerprint phase data from *phase_reports* and returns a dict
    with three sections:
      - ``metrics``: key numeric indicators (overall, flat_flags count, etc.)
      - ``flat_zones``: list of detected flat-zone flags with hints
      - ``correction``: correction status (applied/discarded/rules)
      - ``tuning``: resonance tuning status if enabled

    Returns an empty dict if no fingerprint report is found.
    """
    fp_report: Optional[Dict[str, Any]] = None
    for pr in phase_reports:
        if pr.get("phase") == "fingerprint":
            fp_report = pr
            break
    if fp_report is None:
        return {}

    flat_flags = fp_report.get("flat_zone_flags", [])
    hints = fp_report.get("correction_hints", [])

    report: Dict[str, Any] = {
        "version": "r7v1",
        "mode": fp_report.get("mode", "unknown"),
        "metrics": {
            "overall_unpredictability": fp_report.get("overall_unpredictability", 0.0),
            "sentence_length_cv": fp_report.get("sentence_length_cv", 0.0),
            "paragraph_length_cv": fp_report.get("paragraph_length_cv", 0.0),
            "conjunction_repetition_rate": fp_report.get("conjunction_repetition_rate", 0.0),
            "subject_explicit_rate": fp_report.get("subject_explicit_rate", 0.0),
            "particle_entropy": fp_report.get("particle_entropy", 0.0),
            "pos_bigram_monotonicity": fp_report.get("pos_bigram_monotonicity", 0.0),
            "mtld": fp_report.get("mtld", 0.0),
            "hd_d": fp_report.get("hd_d", 0.0),
            "nominalization_rate": fp_report.get("nominalization_rate", 0.0),
            "morphological_ngram_entropy": fp_report.get("morphological_ngram_entropy", 0.0),
            "morphological_diversity": fp_report.get("morphological_diversity", {}),
            "syntactic_complexity": fp_report.get("syntactic_complexity", {}),
        },
        "flat_zones": {
            "count": len(flat_flags),
            "flags": list(flat_flags),
            "hints": list(hints),
        },
        "correction": {
            "applied": fp_report.get("fingerprint_correction_applied", False),
            "rules": fp_report.get("applied_rules", []),
            "rewrite_ratio": fp_report.get("correction_rewrite_ratio", 0.0),
            "discarded": fp_report.get("correction_discarded", False),
            "discard_reason": fp_report.get("correction_discard_reason", ""),
        },
        "tuning": {
            "enabled": fp_report.get("resonance_tuning_enabled", False),
            "score_band": fp_report.get("tuning_score_band", ""),
            "adjustments": fp_report.get("tuning_adjustments", {}),
        },
    }
    return report


class QualityPipelineRunner:
    """Execute quality phases in config-driven off/shadow/enforce modes."""

    _SAFE_ENFORCE_ROLLOUT_PERCENT = 20

    def __init__(self, config: QualityPipelineConfig) -> None:
        self.config = config
        self.phase01 = Phase01LexicalDiversity(
            lexical_threshold=config.lexical_threshold,
            max_rewrite_ratio=config.max_rewrite_ratio,
            tokenizer_mode=config.phase01_tokenizer,
        )
        self.phase02 = Phase02Burstiness(
            burstiness_target_min=config.burstiness_target_min,
            burstiness_target_max=config.burstiness_target_max,
            max_sentence_split_ratio=config.max_sentence_split_ratio,
        )
        self.phase03 = Phase03Nominalization(
            nominalization_alert_threshold=config.nominalization_alert_threshold,
            max_nominalization_rewrite_ratio=config.max_nominalization_rewrite_ratio,
        )
        self.phase04 = Phase04StyleDrift(
            style_alignment_min_score=config.style_alignment_min_score,
            domain_guard_strictness=config.domain_guard_strictness,
        )
        self.phase05 = Phase05LayoutGuard(
            supplement_min_position_ratio=config.supplement_min_position_ratio,
            intro_max_length_ratio=config.intro_max_length_ratio,
            section_coherence_min_score=config.section_coherence_min_score,
        )
        self.phase06 = Phase06Orchestrator(
            global_rewrite_ratio_cap=config.global_rewrite_ratio_cap,
            conflict_resolution_policy=config.conflict_resolution_policy,
            quality_gate_min_score=config.quality_gate_min_score,
        )
        self.phase07 = Phase07IntegrationRollout()
        self.fingerprint = FingerprintAnalyzer()

    def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> QualityPipelineResult:
        original_text = text or ""
        result = QualityPipelineResult(text=original_text)

        if not original_text:
            return result
        if not self.config.enabled:
            return result
        if self.config.mode == "off":
            return result
        if (
            not self.config.phase01_lexical_enabled
            and not self.config.phase02_burstiness_enabled
            and not self.config.phase03_nominalization_enabled
            and not self.config.phase04_style_drift_enabled
            and not self.config.phase05_layout_guard_enabled
            and not self.config.phase06_orchestrator_enabled
            and not self.config.phase07_rollout_enabled
            and not self.config.fingerprint_enabled
        ):
            return result

        if self.config.phase07_rollout_enabled:
            rollout_decision = self.phase07.select_effective_mode(
                requested_mode=self.config.mode,
                rollout_percent=self.config.rollout_percent,
                text=original_text,
                context=context if isinstance(context, dict) else None,
            )
        else:
            rollout_decision = RolloutDecision(
                requested_mode=self.config.mode,
                effective_mode=self.config.mode,
                rollout_percent=self.config.rollout_percent,
                request_bucket=-1,
                selected_for_enforce=True,
                reason="phase07_disabled_passthrough",
            )
        effective_mode = rollout_decision.effective_mode
        safe_start_active = (
            self.config.phase07_rollout_enabled
            and
            effective_mode == "enforce"
            and str(rollout_decision.requested_mode).lower() == "enforce"
            and int(rollout_decision.rollout_percent) <= self._SAFE_ENFORCE_ROLLOUT_PERCENT
        )
        downstream_mode = "shadow" if safe_start_active else effective_mode
        result.mode_resolution = {
            "requested_mode": self.config.mode,
            "effective_mode": effective_mode,
            "downstream_mode": downstream_mode,
            "safe_start_active": bool(safe_start_active),
            "rollout_percent": int(rollout_decision.rollout_percent),
            "request_bucket": int(rollout_decision.request_bucket),
            "selected_for_enforce": bool(rollout_decision.selected_for_enforce),
            "decision_reason": str(rollout_decision.reason),
        }
        logger.info(
            "Quality mode resolved: requested=%s effective=%s downstream=%s safe_start=%s rollout=%s bucket=%s reason=%s",
            self.config.mode,
            effective_mode,
            downstream_mode,
            safe_start_active,
            rollout_decision.rollout_percent,
            rollout_decision.request_bucket,
            rollout_decision.reason,
        )

        current_text = original_text

        # Fingerprint monitoring runs independently of phase01-07 toggles.
        # In shadow mode: observe-only. In enforce mode: may apply lightweight corrections.
        fingerprint_report: Optional[Dict[str, Any]] = None
        if self.config.fingerprint_enabled:
            fingerprint_report, current_text = self._run_fingerprint(
                current_text,
                result,
                effective_mode,
                context=context,
            )

        phase01_mode = effective_mode
        if safe_start_active:
            logger.info(
                "Phase06 safe-start rollout active: enforce is limited to fingerprint+phase01 (rollout_percent=%s).",
                rollout_decision.rollout_percent,
            )

        if self.config.phase01_lexical_enabled:
            current_text = self._run_phase01(current_text, result, phase01_mode)

        if self.config.phase02_burstiness_enabled:
            current_text = self._run_phase02(current_text, result, downstream_mode)

        if self.config.phase03_nominalization_enabled:
            current_text = self._run_phase03(current_text, result, downstream_mode)

        if self.config.phase04_style_drift_enabled:
            current_text = self._run_phase04(current_text, result, downstream_mode, context=context)

        if self.config.phase05_layout_guard_enabled:
            current_text = self._run_phase05(current_text, result, downstream_mode)

        if self.config.phase06_orchestrator_enabled:
            current_text = self._run_phase06(
                original_text=original_text,
                current_text=current_text,
                result=result,
                effective_mode=downstream_mode,
            )

        if self.config.phase07_rollout_enabled:
            self._run_phase07(
                original_text=original_text,
                current_text=current_text,
                result=result,
                rollout_decision=rollout_decision,
            )

        result.text = current_text
        return result

    def _run_fingerprint(
        self,
        text: str,
        result: QualityPipelineResult,
        effective_mode: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """Run fingerprint analysis and optional lightweight correction.

        In shadow mode: observe-only (no text changes).
        In enforce mode: apply lightweight corrections from correction_hints,
        guarded by rewrite_ratio cap.

        Returns (phase_report, possibly_corrected_text).
        """
        try:
            report = self.fingerprint.analyze(text)
        except Exception as exc:
            message = f"fingerprint_metrics failed: {exc}"
            logger.warning(message)
            result.errors.append(message)
            return None, text

        phase_report: Dict[str, Any] = {
            "phase": "fingerprint",
            "enabled": True,
            "mode": effective_mode,
            "applied": False,
            "sentence_length_cv": report.sentence_length_cv,
            "paragraph_length_cv": report.paragraph_length_cv,
            "conjunction_repetition_rate": report.conjunction_repetition_rate,
            "subject_explicit_rate": report.subject_explicit_rate,
            "particle_entropy": report.particle_entropy,
            "particle_max_entropy": report.particle_max_entropy,
            "script_ratio_hiragana": report.script_ratio_hiragana,
            "script_ratio_katakana": report.script_ratio_katakana,
            "script_ratio_kanji": report.script_ratio_kanji,
            "pos_bigram_monotonicity": report.pos_bigram_monotonicity,
            "mtld": report.mtld,
            "hd_d": report.hd_d,
            "nominalization_rate": report.nominalization_rate,
            "sentence_ending_entropy": report.sentence_ending_entropy,
            "sentence_ending_fine_entropy": report.sentence_ending_fine_entropy,
            "sentence_opening_entropy": report.sentence_opening_entropy,
            "comma_position_cv": report.comma_position_cv,
            "morphological_ngram_entropy": report.morphological_ngram_entropy,
            "morphological_diversity": report.morphological_diversity,
            "syntactic_complexity": report.syntactic_complexity,
            "vocab_repetition_lemmas": report.vocab_repetition_lemmas,
            "flat_zone_flags": report.flat_zone_flags,
            "correction_hints": report.correction_hints,
            "overall_unpredictability": report.overall_unpredictability,
            "fingerprint_correction_applied": False,
            "applied_rules": [],
            "correction_rewrite_ratio": 0.0,
            "correction_discarded": False,
            "correction_discard_reason": "",
        }

        corrected_text = text

        # R5-T02: enforce mode triggers lightweight correction
        if effective_mode == "enforce" and report.flat_zone_flags:
            try:
                correction = apply_fingerprint_corrections(text, report)
                phase_report["correction_rewrite_ratio"] = correction.rewrite_ratio
                phase_report["correction_discarded"] = correction.discarded
                phase_report["correction_discard_reason"] = correction.discard_reason
                if correction.applied_rules and not correction.discarded:
                    corrected_text = correction.text
                    phase_report["fingerprint_correction_applied"] = True
                    phase_report["applied_rules"] = list(correction.applied_rules)
                    phase_report["applied"] = True
                    result.applied.append("fingerprint_correction")
            except Exception as exc:
                message = f"fingerprint_correction failed: {exc}"
                logger.warning(message)
                result.errors.append(message)

        # R6-T05: resonance tuning output
        tuning_report: Dict[str, Any] = {"resonance_tuning_enabled": False}
        if self.config.resonance_tuning_enabled:
            try:
                current_params = {
                    "humanity_intensity": 0.5,
                    "phrase_probability": 0.75,
                    "pronoun_reduction_ratio": 0.5,
                }
                # Pull current values from context if available
                if hasattr(result, "_resonance_params") and result._resonance_params:
                    current_params.update(result._resonance_params)
                style_profile = self._resolve_style_profile_for_tuning(context)
                tuning = compute_resonance_tuning(report, current_params, style_profile=style_profile)
                tuning_report = {
                    "resonance_tuning_enabled": True,
                    "tuning_score_band": tuning.score_band,
                    "tuning_before": tuning.before,
                    "tuning_after": tuning.after,
                    "tuning_adjustments": tuning.adjustments,
                    "tuning_reason": tuning.reason,
                    "tuning_style_profile": style_profile,
                }
            except Exception as exc:
                message = f"resonance_tuning failed: {exc}"
                logger.warning(message)
                result.errors.append(message)
        phase_report.update(tuning_report)

        result.phase_reports.append(phase_report)

        if report.flat_zone_flags:
            logger.info(
                "Fingerprint flat-zone detected: flags=%s unpredictability=%.3f correction_applied=%s",
                report.flat_zone_flags,
                report.overall_unpredictability,
                phase_report["fingerprint_correction_applied"],
            )

        return phase_report, corrected_text

    @staticmethod
    def _normalize_category_base_template(value: str) -> str:
        key = (value or "").strip().lower()
        if key == "ai":
            return "technical"
        if key == "announcement":
            return "announcement"
        if key == "case_study":
            return "how_to"
        if key == "branding":
            return "column"
        return key

    def _resolve_style_profile_for_tuning(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """品質チューニング用のスタイルプロファイルを文脈から決定する。"""
        ctx = context if isinstance(context, dict) else {}
        article_type = str(ctx.get("article_type", "") or "")
        base_template = self._normalize_category_base_template(
            str(ctx.get("category_base_template", "") or "")
        )
        profile = map_content_type_to_profile(content_type=article_type, genre=base_template)
        if not profile:
            profile = map_content_type_to_profile(genre=base_template)
        if not profile:
            profile = map_content_type_to_profile(content_type=article_type)
        if not profile:
            profile = map_content_type_to_profile(content_type="column")

        style_hint = str(ctx.get("style_profile_hint", "") or "").strip().lower()
        if style_hint == "formal":
            profile = {**profile, "emotional_waveform": "flat", "digression_allowed": False}
        elif style_hint == "balanced":
            profile = {**profile, "emotional_waveform": "steady", "digression_allowed": False}
        elif style_hint == "casual":
            profile = {**profile, "emotional_waveform": "dynamic", "digression_allowed": True}
        return profile

    def _run_phase01(
        self,
        text: str,
        result: QualityPipelineResult,
        effective_mode: str,
    ) -> str:
        phase_result = self._run_with_retry(
            phase_name="phase01_lexical",
            text=text,
            result=result,
            analyzer=lambda candidate: self.phase01.analyze(candidate),
        )
        if phase_result is None:
            return text

        phase_report: Dict[str, Any] = {
            "phase": "phase01_lexical",
            "enabled": True,
            "mode": effective_mode,
            "requested_mode": self.config.mode,
            "applied": False,
            "lexical_diversity_score": phase_result.lexical_diversity_score,
            "lexical_threshold": self.config.lexical_threshold,
            "tokenization_method": phase_result.tokenization_method,
            "configured_tokenizer": self.config.phase01_tokenizer,
            "repetition_signals": [asdict(item) for item in phase_result.repetition_signals],
            "rewrite_suggestions": [asdict(item) for item in phase_result.rewrite_suggestions],
            "rewrite_cap": phase_result.rewrite_cap,
            "rewrite_ratio": 0.0,
        }

        updated_text = text
        if effective_mode == "enforce" and phase_result.lexical_diversity_score < self.config.lexical_threshold:
            rewritten_text, rewrite_ratio = self.phase01.apply_minimal_rewrites(
                text,
                phase_result.rewrite_suggestions,
            )
            updated_text = rewritten_text
            phase_report["rewrite_ratio"] = rewrite_ratio
            phase_report["applied"] = rewritten_text != text
            if rewritten_text != text:
                result.applied.append("phase01_lexical")

        result.phase_reports.append(phase_report)
        return updated_text

    def _run_phase06(
        self,
        original_text: str,
        current_text: str,
        result: QualityPipelineResult,
        effective_mode: str,
    ) -> str:
        phase_result = self._run_with_retry(
            phase_name="phase06_orchestrator",
            text=current_text,
            result=result,
            analyzer=lambda _: self.phase06.evaluate(
                original_text=original_text,
                current_text=current_text,
                phase_reports=result.phase_reports,
                errors=result.errors,
            ),
        )
        if phase_result is None:
            return current_text

        bundle = phase_result.quality_bundle
        phase_report: Dict[str, Any] = {
            "phase": "phase06_orchestrator",
            "enabled": True,
            "mode": effective_mode,
            "requested_mode": self.config.mode,
            "applied": False,
            "global_rewrite_ratio_cap": self.config.global_rewrite_ratio_cap,
            "conflict_resolution_policy": self.config.conflict_resolution_policy,
            "quality_gate_min_score": self.config.quality_gate_min_score,
            "quality_bundle": {
                "phase_order": list(bundle.phase_order),
                "scores": dict(bundle.scores),
                "alerts": dict(bundle.alerts),
                "actions": [asdict(item) for item in bundle.actions],
                "conflicts": [asdict(item) for item in bundle.conflicts],
                "rewrite_ratio_global": bundle.rewrite_ratio_global,
                "quality_score": bundle.quality_score,
            },
            "final_adjustment_plan": [asdict(item) for item in phase_result.final_adjustment_plan],
            "gate_decision": phase_result.gate_decision,
            "gate_reason": phase_result.gate_reason,
        }

        updated_text = current_text
        if effective_mode == "enforce":
            if phase_result.gate_decision == "fallback":
                updated_text = original_text
                phase_report["applied"] = updated_text != current_text
                if phase_report["applied"]:
                    result.applied.append("phase06_orchestrator")
            elif phase_result.gate_decision == "hold":
                # hold = これ以上の変更は控えるが、既に適用済みの軽微な修正は保持
                # (fallback と異なり original_text には戻さない)
                phase_report["applied"] = False

        result.phase_reports.append(phase_report)
        return updated_text

    def _run_phase05(
        self,
        text: str,
        result: QualityPipelineResult,
        effective_mode: str,
    ) -> str:
        phase_result = self._run_with_retry(
            phase_name="phase05_layout_guard",
            text=text,
            result=result,
            analyzer=lambda candidate: self.phase05.analyze(candidate),
        )
        if phase_result is None:
            return text

        phase_report: Dict[str, Any] = {
            "phase": "phase05_layout_guard",
            "enabled": True,
            "mode": effective_mode,
            "requested_mode": self.config.mode,
            "applied": False,
            "layout_score": phase_result.layout_score,
            "supplement_min_position_ratio": self.config.supplement_min_position_ratio,
            "intro_max_length_ratio": self.config.intro_max_length_ratio,
            "section_coherence_min_score": self.config.section_coherence_min_score,
            "layout_validation_report": asdict(phase_result.layout_validation_report),
            "supplement_position_alerts": [asdict(item) for item in phase_result.supplement_position_alerts],
            "reorder_plan": [asdict(item) for item in phase_result.reorder_plan],
            "applied_reorder_steps": [],
            "post_layout_score": phase_result.layout_score,
        }

        updated_text = text
        should_enforce = (
            effective_mode == "enforce"
            and bool(phase_result.reorder_plan)
        )
        if should_enforce:
            rewritten_text, applied_steps = self.phase05.apply_minimal_reordering(
                text,
                phase_result.reorder_plan,
            )
            updated_text = rewritten_text
            phase_report["applied_reorder_steps"] = [asdict(item) for item in applied_steps]
            phase_report["applied"] = rewritten_text != text
            if rewritten_text != text:
                result.applied.append("phase05_layout_guard")
                try:
                    post_result = self.phase05.analyze(rewritten_text)
                    phase_report["post_layout_score"] = post_result.layout_score
                except Exception as exc:  # pragma: no cover - defensive path
                    message = f"phase05_layout_guard post-check failed: {exc}"
                    logger.warning(message)
                    result.errors.append(message)

        result.phase_reports.append(phase_report)
        return updated_text

    def _run_phase02(
        self,
        text: str,
        result: QualityPipelineResult,
        effective_mode: str,
    ) -> str:
        phase_result = self._run_with_retry(
            phase_name="phase02_burstiness",
            text=text,
            result=result,
            analyzer=lambda candidate: self.phase02.analyze(candidate),
        )
        if phase_result is None:
            return text

        phase_report: Dict[str, Any] = {
            "phase": "phase02_burstiness",
            "enabled": True,
            "mode": effective_mode,
            "requested_mode": self.config.mode,
            "applied": False,
            "burstiness_score": phase_result.burstiness_score,
            "burstiness_target_min": self.config.burstiness_target_min,
            "burstiness_target_max": self.config.burstiness_target_max,
            "max_sentence_split_ratio": self.config.max_sentence_split_ratio,
            "length_profile": {
                "sentences": [asdict(item) for item in phase_result.sentence_profile],
                "paragraphs": [asdict(item) for item in phase_result.paragraph_profile],
            },
            "rhythm_adjustments": [asdict(item) for item in phase_result.rhythm_adjustments],
            "adjustment_cap": phase_result.adjustment_cap,
            "adjustment_ratio": 0.0,
            "applied_adjustments": [],
            "post_burstiness_score": phase_result.burstiness_score,
        }

        updated_text = text
        should_enforce = (
            effective_mode == "enforce"
            and bool(phase_result.rhythm_adjustments)
        )
        if should_enforce:
            rewritten_text, adjustment_ratio, applied_adjustments = self.phase02.apply_minimal_adjustments(
                text,
                phase_result.rhythm_adjustments,
            )
            updated_text = rewritten_text
            phase_report["adjustment_ratio"] = adjustment_ratio
            phase_report["applied_adjustments"] = [asdict(item) for item in applied_adjustments]
            phase_report["applied"] = rewritten_text != text
            if rewritten_text != text:
                result.applied.append("phase02_burstiness")
                try:
                    post_result = self.phase02.analyze(rewritten_text)
                    phase_report["post_burstiness_score"] = post_result.burstiness_score
                except Exception as exc:  # pragma: no cover - defensive path
                    message = f"phase02_burstiness post-check failed: {exc}"
                    logger.warning(message)
                    result.errors.append(message)

        result.phase_reports.append(phase_report)
        return updated_text

    def _run_phase03(
        self,
        text: str,
        result: QualityPipelineResult,
        effective_mode: str,
    ) -> str:
        phase_result = self._run_with_retry(
            phase_name="phase03_nominalization",
            text=text,
            result=result,
            analyzer=lambda candidate: self.phase03.analyze(candidate),
        )
        if phase_result is None:
            return text

        phase_report: Dict[str, Any] = {
            "phase": "phase03_nominalization",
            "enabled": True,
            "mode": effective_mode,
            "requested_mode": self.config.mode,
            "applied": False,
            "nominalization_score": phase_result.nominalization_score,
            "nominalization_alert_threshold": self.config.nominalization_alert_threshold,
            "max_nominalization_rewrite_ratio": self.config.max_nominalization_rewrite_ratio,
            "nominalization_alerts": [asdict(item) for item in phase_result.nominalization_alerts],
            "rewrite_candidates": [asdict(item) for item in phase_result.rewrite_candidates],
            "rewrite_cap": phase_result.rewrite_cap,
            "rewrite_ratio": 0.0,
            "applied_rewrites": [],
            "post_nominalization_score": phase_result.nominalization_score,
        }

        updated_text = text
        should_enforce = (
            effective_mode == "enforce"
            and phase_result.nominalization_score >= self.config.nominalization_alert_threshold
            and bool(phase_result.rewrite_candidates)
        )
        if should_enforce:
            rewritten_text, rewrite_ratio, applied_rewrites = self.phase03.apply_minimal_rewrites(
                text,
                phase_result.rewrite_candidates,
            )
            updated_text = rewritten_text
            phase_report["rewrite_ratio"] = rewrite_ratio
            phase_report["applied_rewrites"] = [asdict(item) for item in applied_rewrites]
            phase_report["applied"] = rewritten_text != text
            if rewritten_text != text:
                result.applied.append("phase03_nominalization")
                try:
                    post_result = self.phase03.analyze(rewritten_text)
                    phase_report["post_nominalization_score"] = post_result.nominalization_score
                except Exception as exc:  # pragma: no cover - defensive path
                    message = f"phase03_nominalization post-check failed: {exc}"
                    logger.warning(message)
                    result.errors.append(message)

        result.phase_reports.append(phase_report)
        return updated_text

    def _run_phase04(
        self,
        text: str,
        result: QualityPipelineResult,
        effective_mode: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        phase_result = self._run_with_retry(
            phase_name="phase04_style_drift",
            text=text,
            result=result,
            analyzer=lambda candidate: self.phase04.analyze(candidate, context=context),
        )
        if phase_result is None:
            return text

        phase_report: Dict[str, Any] = {
            "phase": "phase04_style_drift",
            "enabled": True,
            "mode": effective_mode,
            "requested_mode": self.config.mode,
            "applied": False,
            "style_alignment_score": phase_result.style_alignment_score,
            "style_alignment_min_score": self.config.style_alignment_min_score,
            "domain_guard_strictness": self.config.domain_guard_strictness,
            "inferred_domain": phase_result.inferred_domain,
            "inferred_purpose": phase_result.inferred_purpose,
            "active_source_domains": list(phase_result.active_source_domains),
            "drift_alerts": [asdict(item) for item in phase_result.drift_alerts],
            "style_corrections": [asdict(item) for item in phase_result.style_corrections],
            "correction_cap": phase_result.correction_cap,
            "correction_ratio": 0.0,
            "applied_corrections": [],
            "post_style_alignment_score": phase_result.style_alignment_score,
        }

        updated_text = text
        should_enforce = (
            effective_mode == "enforce"
            and phase_result.style_alignment_score < self.config.style_alignment_min_score
            and bool(phase_result.style_corrections)
        )
        if should_enforce:
            rewritten_text, correction_ratio, applied_corrections = self.phase04.apply_minimal_corrections(
                text,
                phase_result.style_corrections,
            )
            updated_text = rewritten_text
            phase_report["correction_ratio"] = correction_ratio
            phase_report["applied_corrections"] = [asdict(item) for item in applied_corrections]
            phase_report["applied"] = rewritten_text != text
            if rewritten_text != text:
                result.applied.append("phase04_style_drift")
                try:
                    post_result = self.phase04.analyze(rewritten_text, context=context)
                    phase_report["post_style_alignment_score"] = post_result.style_alignment_score
                except Exception as exc:  # pragma: no cover - defensive path
                    message = f"phase04_style_drift post-check failed: {exc}"
                    logger.warning(message)
                    result.errors.append(message)

        result.phase_reports.append(phase_report)
        return updated_text

    def _run_phase07(
        self,
        original_text: str,
        current_text: str,
        result: QualityPipelineResult,
        rollout_decision: Any,
    ) -> None:
        telemetry = self.phase07.build_telemetry(
            original_text=original_text,
            final_text=current_text,
            phase_reports=result.phase_reports,
            errors=result.errors,
        )
        phase_report: Dict[str, Any] = {
            "phase": "phase07_rollout",
            "enabled": True,
            "mode": rollout_decision.effective_mode,
            "requested_mode": rollout_decision.requested_mode,
            "applied": False,
            "rollout_percent": rollout_decision.rollout_percent,
            "decision": asdict(rollout_decision),
            "telemetry": asdict(telemetry),
        }
        result.phase_reports.append(phase_report)
        logger.info(
            "phase07_rollout request_bucket=%s selected=%s requested_mode=%s effective_mode=%s gate=%s",
            rollout_decision.request_bucket,
            rollout_decision.selected_for_enforce,
            rollout_decision.requested_mode,
            rollout_decision.effective_mode,
            telemetry.gate_decision,
        )

    def _run_with_retry(
        self,
        phase_name: str,
        text: str,
        result: QualityPipelineResult,
        analyzer: Callable[[str], Any],
    ) -> Optional[Any]:
        candidate_text = text
        last_error: Exception | None = None

        for attempt in range(2):
            try:
                return analyzer(candidate_text)
            except Exception as exc:  # pragma: no cover - defensive path
                last_error = exc
                if attempt == 0:
                    candidate_text = candidate_text.replace("\x00", "").replace("\r\n", "\n")
                    continue

        if self.config.fail_open:
            message = f"{phase_name} failed after retry: {last_error}"
            logger.warning(message)
            result.errors.append(message)
            return None

        if last_error is not None:
            raise last_error
        raise RuntimeError(f"{phase_name} failed without explicit error")
