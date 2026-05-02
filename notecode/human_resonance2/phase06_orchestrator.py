"""Phase 06 orchestrator for conflict resolution and quality gate decisions."""
from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Sequence, Tuple


PHASE_ORDER: Tuple[str, ...] = (
    "phase01_lexical",
    "phase02_burstiness",
    "phase03_nominalization",
    "phase04_style_drift",
    "phase05_layout_guard",
)

PRIORITY_MAP: Dict[str, Dict[str, int]] = {
    "safe_first": {
        "phase04_style_drift": 5,
        "phase05_layout_guard": 4,
        "phase03_nominalization": 3,
        "phase02_burstiness": 2,
        "phase01_lexical": 1,
    },
    "readability_first": {
        "phase05_layout_guard": 5,
        "phase02_burstiness": 4,
        "phase03_nominalization": 3,
        "phase04_style_drift": 2,
        "phase01_lexical": 1,
    },
    "diversity_first": {
        "phase01_lexical": 5,
        "phase02_burstiness": 4,
        "phase03_nominalization": 3,
        "phase04_style_drift": 2,
        "phase05_layout_guard": 1,
    },
}


@dataclass(frozen=True)
class OrchestratorAction:
    phase: str
    action_type: str
    location_key: str
    summary: str
    priority: int


@dataclass(frozen=True)
class OrchestratorConflict:
    location_key: str
    phases: Tuple[str, ...]
    resolved_phase: str
    policy: str
    reason: str


@dataclass
class QualityBundle:
    phase_order: Tuple[str, ...]
    scores: Dict[str, float]
    alerts: Dict[str, int]
    actions: List[OrchestratorAction] = field(default_factory=list)
    conflicts: List[OrchestratorConflict] = field(default_factory=list)
    rewrite_ratio_global: float = 0.0
    quality_score: float = 1.0


@dataclass
class OrchestratorResult:
    quality_bundle: QualityBundle
    final_adjustment_plan: List[OrchestratorAction]
    gate_decision: str
    gate_reason: str


class Phase06Orchestrator:
    """Aggregate phase reports, resolve conflicts, and decide quality gate."""

    def __init__(
        self,
        global_rewrite_ratio_cap: float = 0.2,
        conflict_resolution_policy: str = "safe_first",
        quality_gate_min_score: float = 0.55,
    ) -> None:
        self.global_rewrite_ratio_cap = max(0.0, min(1.0, float(global_rewrite_ratio_cap)))
        self.conflict_resolution_policy = self._normalize_policy(conflict_resolution_policy)
        self.quality_gate_min_score = max(0.0, min(1.0, float(quality_gate_min_score)))

    def evaluate(
        self,
        original_text: str,
        current_text: str,
        phase_reports: Sequence[Dict[str, Any]],
        errors: Sequence[str],
    ) -> OrchestratorResult:
        actions = self._collect_actions(phase_reports)
        resolved_actions, conflicts = self._resolve_conflicts(actions)

        score_map = self._collect_scores(phase_reports)
        alert_map = self._collect_alerts(phase_reports)
        rewrite_ratio_global = self._rewrite_ratio_global(original_text, current_text)
        quality_score = self._quality_score(score_map, alert_map, rewrite_ratio_global)

        bundle = QualityBundle(
            phase_order=PHASE_ORDER,
            scores=score_map,
            alerts=alert_map,
            actions=actions,
            conflicts=conflicts,
            rewrite_ratio_global=rewrite_ratio_global,
            quality_score=quality_score,
        )

        gate_decision, gate_reason = self._gate_decision(
            rewrite_ratio_global=rewrite_ratio_global,
            quality_score=quality_score,
            errors=errors,
        )
        return OrchestratorResult(
            quality_bundle=bundle,
            final_adjustment_plan=resolved_actions,
            gate_decision=gate_decision,
            gate_reason=gate_reason,
        )

    def _normalize_policy(self, policy: str) -> str:
        normalized = str(policy or "").strip().lower()
        if normalized in PRIORITY_MAP:
            return normalized
        return "safe_first"

    def _collect_actions(self, phase_reports: Sequence[Dict[str, Any]]) -> List[OrchestratorAction]:
        collected: List[OrchestratorAction] = []
        for report in phase_reports:
            phase = str(report.get("phase") or "")
            if phase not in PHASE_ORDER:
                continue
            priority = PRIORITY_MAP[self.conflict_resolution_policy].get(phase, 0)
            collected.extend(self._actions_for_phase(phase, report, priority))
        collected.sort(key=lambda item: (-item.priority, item.phase, item.location_key, item.action_type))
        return collected

    def _actions_for_phase(
        self,
        phase: str,
        report: Dict[str, Any],
        priority: int,
    ) -> List[OrchestratorAction]:
        actions: List[OrchestratorAction] = []

        if phase == "phase01_lexical":
            for item in report.get("rewrite_suggestions", []) or []:
                paragraph = int(item.get("paragraph_index", 0))
                location = f"p{paragraph}"
                actions.append(
                    OrchestratorAction(
                        phase=phase,
                        action_type="lexical_rewrite",
                        location_key=location,
                        summary=str(item.get("replacement") or ""),
                        priority=priority,
                    )
                )
        elif phase == "phase02_burstiness":
            for item in report.get("rhythm_adjustments", []) or []:
                paragraph = int(item.get("paragraph_index", 0))
                sentence = int(item.get("sentence_index", 0))
                location = f"p{paragraph}s{sentence}"
                actions.append(
                    OrchestratorAction(
                        phase=phase,
                        action_type=str(item.get("action_type") or "rhythm_adjust"),
                        location_key=location,
                        summary=str(item.get("reason") or ""),
                        priority=priority,
                    )
                )
        elif phase == "phase03_nominalization":
            for item in report.get("rewrite_candidates", []) or []:
                paragraph = int(item.get("paragraph_index", 0))
                sentence = int(item.get("sentence_index", 0))
                location = f"p{paragraph}s{sentence}"
                actions.append(
                    OrchestratorAction(
                        phase=phase,
                        action_type="nominalization_rewrite",
                        location_key=location,
                        summary=str(item.get("reason") or ""),
                        priority=priority,
                    )
                )
        elif phase == "phase04_style_drift":
            for item in report.get("style_corrections", []) or []:
                paragraph = int(item.get("paragraph_index", 0))
                sentence = int(item.get("sentence_index", 0))
                location = f"p{paragraph}s{sentence}"
                actions.append(
                    OrchestratorAction(
                        phase=phase,
                        action_type="style_correction",
                        location_key=location,
                        summary=str(item.get("reason") or ""),
                        priority=priority,
                    )
                )
        elif phase == "phase05_layout_guard":
            for item in report.get("reorder_plan", []) or []:
                section = int(item.get("section_index", 0))
                target = int(item.get("target_index", 0))
                location = f"section{section}->section{target}"
                actions.append(
                    OrchestratorAction(
                        phase=phase,
                        action_type="section_reorder",
                        location_key=location,
                        summary=str(item.get("reason") or ""),
                        priority=priority,
                    )
                )

        return actions

    def _resolve_conflicts(
        self,
        actions: Sequence[OrchestratorAction],
    ) -> Tuple[List[OrchestratorAction], List[OrchestratorConflict]]:
        by_location: Dict[str, List[OrchestratorAction]] = {}
        for action in actions:
            by_location.setdefault(action.location_key, []).append(action)

        resolved: List[OrchestratorAction] = []
        conflicts: List[OrchestratorConflict] = []

        for location_key in sorted(by_location.keys()):
            group = by_location[location_key]
            if len(group) == 1:
                resolved.append(group[0])
                continue

            winner = sorted(
                group,
                key=lambda item: (-item.priority, item.phase, item.action_type, item.summary),
            )[0]
            resolved.append(winner)
            conflicts.append(
                OrchestratorConflict(
                    location_key=location_key,
                    phases=tuple(sorted({item.phase for item in group})),
                    resolved_phase=winner.phase,
                    policy=self.conflict_resolution_policy,
                    reason="highest priority phase kept for shared location",
                )
            )

        resolved.sort(key=lambda item: (-item.priority, item.phase, item.location_key))
        return resolved, conflicts

    def _collect_scores(self, phase_reports: Sequence[Dict[str, Any]]) -> Dict[str, float]:
        score_map: Dict[str, float] = {}
        for report in phase_reports:
            phase = str(report.get("phase") or "")
            if phase == "phase01_lexical":
                score_map[phase] = float(report.get("lexical_diversity_score", 1.0))
            elif phase == "phase02_burstiness":
                score_map[phase] = float(report.get("burstiness_score", 1.0))
            elif phase == "phase03_nominalization":
                value = float(report.get("nominalization_score", 0.0))
                score_map[phase] = round(max(0.0, min(1.0, 1.0 - value)), 4)
            elif phase == "phase04_style_drift":
                score_map[phase] = float(report.get("style_alignment_score", 1.0))
            elif phase == "phase05_layout_guard":
                score_map[phase] = float(report.get("layout_score", 1.0))
        return score_map

    def _collect_alerts(self, phase_reports: Sequence[Dict[str, Any]]) -> Dict[str, int]:
        alert_map: Dict[str, int] = {}
        for report in phase_reports:
            phase = str(report.get("phase") or "")
            if phase == "phase01_lexical":
                alert_map[phase] = len(report.get("repetition_signals", []) or [])
            elif phase == "phase02_burstiness":
                alert_map[phase] = len(report.get("rhythm_adjustments", []) or [])
            elif phase == "phase03_nominalization":
                alert_map[phase] = len(report.get("nominalization_alerts", []) or [])
            elif phase == "phase04_style_drift":
                alert_map[phase] = len(report.get("drift_alerts", []) or [])
            elif phase == "phase05_layout_guard":
                alert_map[phase] = len(report.get("supplement_position_alerts", []) or [])
        return alert_map

    def _rewrite_ratio_global(self, original_text: str, current_text: str) -> float:
        if not original_text:
            return 0.0
        similarity = SequenceMatcher(a=original_text, b=current_text).ratio()
        return round(max(0.0, min(1.0, 1.0 - similarity)), 4)

    def _quality_score(
        self,
        score_map: Dict[str, float],
        alert_map: Dict[str, int],
        rewrite_ratio_global: float,
    ) -> float:
        if score_map:
            base = sum(score_map.values()) / len(score_map)
        else:
            base = 1.0
        alert_penalty = min(0.3, sum(alert_map.values()) * 0.01)
        rewrite_penalty = min(0.3, max(0.0, rewrite_ratio_global - self.global_rewrite_ratio_cap))
        return round(max(0.0, min(1.0, base - alert_penalty - rewrite_penalty)), 4)

    def _gate_decision(
        self,
        rewrite_ratio_global: float,
        quality_score: float,
        errors: Sequence[str],
    ) -> Tuple[str, str]:
        if errors:
            return "fallback", "phase_errors_detected"
        if rewrite_ratio_global > self.global_rewrite_ratio_cap:
            return "fallback", "global_rewrite_ratio_cap_exceeded"
        if quality_score < self.quality_gate_min_score:
            return "hold", "quality_score_below_gate"
        return "pass", "quality_gate_passed"

