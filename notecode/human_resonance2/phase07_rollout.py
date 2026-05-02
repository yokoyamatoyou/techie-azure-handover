"""Phase 07 rollout controller for safe integration and telemetry."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from difflib import SequenceMatcher
from typing import Any, Dict, Sequence


@dataclass(frozen=True)
class RolloutDecision:
    requested_mode: str
    effective_mode: str
    rollout_percent: int
    request_bucket: int
    selected_for_enforce: bool
    reason: str


@dataclass(frozen=True)
class RolloutTelemetry:
    score_delta: float
    text_change_ratio: float
    drift_alert_count: int
    gate_decision: str
    phase_report_count: int
    error_count: int


class Phase07IntegrationRollout:
    """Control enforce rollout coverage and publish integration telemetry."""

    def select_effective_mode(
        self,
        requested_mode: str,
        rollout_percent: int,
        text: str,
        context: Dict[str, Any] | None,
    ) -> RolloutDecision:
        requested = str(requested_mode or "off").strip().lower()
        coverage = max(0, min(100, int(rollout_percent)))
        bucket = self._bucket_for_request(text=text, context=context)

        if requested != "enforce":
            return RolloutDecision(
                requested_mode=requested,
                effective_mode=requested,
                rollout_percent=coverage,
                request_bucket=bucket,
                selected_for_enforce=True,
                reason="non_enforce_mode_passthrough",
            )

        selected = bucket < coverage
        if selected:
            return RolloutDecision(
                requested_mode=requested,
                effective_mode="enforce",
                rollout_percent=coverage,
                request_bucket=bucket,
                selected_for_enforce=True,
                reason="selected_by_rollout_bucket",
            )

        return RolloutDecision(
            requested_mode=requested,
            effective_mode="shadow",
            rollout_percent=coverage,
            request_bucket=bucket,
            selected_for_enforce=False,
            reason="not_selected_for_enforce_fallback_to_shadow",
        )

    def build_telemetry(
        self,
        original_text: str,
        final_text: str,
        phase_reports: Sequence[Dict[str, Any]],
        errors: Sequence[str],
    ) -> RolloutTelemetry:
        score_delta = self._score_delta(phase_reports)
        text_change_ratio = self._text_change_ratio(original_text, final_text)
        drift_alert_count = 0
        gate_decision = "n/a"

        for report in phase_reports:
            phase = str(report.get("phase") or "")
            if phase == "phase04_style_drift":
                drift_alert_count += len(report.get("drift_alerts", []) or [])
            if phase == "phase06_orchestrator":
                gate_decision = str(report.get("gate_decision") or "n/a")

        return RolloutTelemetry(
            score_delta=score_delta,
            text_change_ratio=text_change_ratio,
            drift_alert_count=drift_alert_count,
            gate_decision=gate_decision,
            phase_report_count=len(phase_reports),
            error_count=len(errors),
        )

    def _bucket_for_request(self, text: str, context: Dict[str, Any] | None) -> int:
        topic = ""
        urls = ""
        if isinstance(context, dict):
            topic = str(context.get("topic_hint") or "")
            urls = "|".join(str(url) for url in (context.get("source_urls") or []) if str(url).strip())
        key = "|".join([text[:2000], topic[:200], urls[:500]])
        digest = hashlib.sha256(key.encode("utf-8", errors="ignore")).hexdigest()
        return int(digest[:8], 16) % 100

    def _text_change_ratio(self, original_text: str, final_text: str) -> float:
        if not original_text:
            return 0.0
        similarity = SequenceMatcher(a=original_text, b=final_text).ratio()
        return round(max(0.0, min(1.0, 1.0 - similarity)), 4)

    def _score_delta(self, phase_reports: Sequence[Dict[str, Any]]) -> float:
        deltas = []
        for report in phase_reports:
            phase = str(report.get("phase") or "")
            if phase == "phase02_burstiness":
                before = float(report.get("burstiness_score", 0.0))
                after = float(report.get("post_burstiness_score", before))
                deltas.append(after - before)
            elif phase == "phase03_nominalization":
                before = 1.0 - float(report.get("nominalization_score", 0.0))
                after = 1.0 - float(report.get("post_nominalization_score", report.get("nominalization_score", 0.0)))
                deltas.append(after - before)
            elif phase == "phase04_style_drift":
                before = float(report.get("style_alignment_score", 0.0))
                after = float(report.get("post_style_alignment_score", before))
                deltas.append(after - before)
            elif phase == "phase05_layout_guard":
                before = float(report.get("layout_score", 0.0))
                after = float(report.get("post_layout_score", before))
                deltas.append(after - before)
            elif phase == "phase06_orchestrator":
                bundle = report.get("quality_bundle") or {}
                score = float(bundle.get("quality_score", 0.0))
                deltas.append(score - 0.5)
        if not deltas:
            return 0.0
        return round(sum(deltas) / len(deltas), 4)

