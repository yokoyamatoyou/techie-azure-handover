"""Pure quality report projection helpers for note_writer_app."""
from __future__ import annotations

from typing import Any, Dict, List

from note.note_text_format_helpers import _safe_round_float, _to_plain_list


def _iter_quality_phase_reports(quality: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten report schema to phase-level entries (supports nested/legacy)."""
    flattened: List[Dict[str, Any]] = []
    for report in _to_plain_list(quality.get("reports")):
        if not isinstance(report, dict):
            continue
        nested = _to_plain_list(report.get("phase_reports"))
        if nested:
            flattened.extend([phase for phase in nested if isinstance(phase, dict)])
            continue
        if report.get("phase"):
            flattened.append(report)
    return flattened


def _extract_fingerprint_phase_report(quality: Dict[str, Any]) -> Dict[str, Any]:
    for phase_report in _iter_quality_phase_reports(quality):
        if str(phase_report.get("phase", "") or "") != "fingerprint":
            continue
        return {
            "flat_zone_flags": _to_plain_list(phase_report.get("flat_zone_flags")),
            "overall_unpredictability": _safe_round_float(
                phase_report.get("overall_unpredictability"),
                4,
                0.0,
            ),
            "correction_hints": _to_plain_list(phase_report.get("correction_hints")),
            "fingerprint_correction_applied": bool(
                phase_report.get("fingerprint_correction_applied", False)
            ),
            "nominalization_rate": _safe_round_float(
                phase_report.get("nominalization_rate"),
                4,
                0.0,
            ),
            "sentence_ending_entropy": _safe_round_float(
                phase_report.get("sentence_ending_entropy"),
                4,
                0.0,
            ),
            "sentence_ending_fine_entropy": _safe_round_float(
                phase_report.get("sentence_ending_fine_entropy"),
                4,
                0.0,
            ),
            "subject_explicit_rate": _safe_round_float(
                phase_report.get("subject_explicit_rate"),
                4,
                0.0,
            ),
            "mtld": _safe_round_float(phase_report.get("mtld"), 4, 0.0),
        }
    return {}
