"""Phase07 shadow/A-B evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from statistics import mean
from typing import Any, Dict, Iterable, List, Tuple

DEFAULT_PHASE07_THRESHOLDS: Dict[str, float] = {
    "category_consistency_score_min": 0.95,
    "question_reflection_rate_min": 0.85,
    "semantic_duplicate_improvement_min": 0.20,
}

REQUIRED_METRICS = (
    "semantic_duplicate_rate",
    "coherence_score",
    "subject_explicit_rate",
    "category_consistency_score",
    "question_reflection_rate",
    "latency_ms",
    "token_cost",
)


@dataclass
class ShadowSample:
    sample_id: str
    article_type: str
    has_questions: bool
    legacy_metrics: Dict[str, float]
    zero_base_metrics: Dict[str, float]
    fallback_ok: bool = True


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _avg(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return float(mean(items))


def validate_shadow_samples(samples: List[ShadowSample]) -> List[str]:
    errors: List[str] = []
    for sample in samples:
        if not sample.sample_id.strip():
            errors.append("sample_id is empty")
        if not sample.article_type.strip():
            errors.append(f"{sample.sample_id}: article_type is empty")
        for name in REQUIRED_METRICS:
            if name not in sample.legacy_metrics:
                errors.append(f"{sample.sample_id}: legacy missing metric {name}")
            if name not in sample.zero_base_metrics:
                errors.append(f"{sample.sample_id}: zero_base missing metric {name}")
    return errors


def aggregate_shadow_metrics(samples: List[ShadowSample]) -> Dict[str, Any]:
    if not samples:
        return {
            "sample_count": 0,
            "article_types": [],
            "question_path_coverage": {"with_questions": 0, "without_questions": 0},
            "legacy": {},
            "zero_base": {},
            "semantic_duplicate_improvement_rate": 0.0,
            "fallback_failure_count": 0,
        }

    legacy_summary: Dict[str, float] = {}
    zero_summary: Dict[str, float] = {}
    for metric in REQUIRED_METRICS:
        legacy_summary[metric] = _avg(_safe_float(s.legacy_metrics.get(metric)) for s in samples)
        zero_summary[metric] = _avg(_safe_float(s.zero_base_metrics.get(metric)) for s in samples)

    legacy_dup = max(1e-9, legacy_summary["semantic_duplicate_rate"])
    zero_dup = max(0.0, zero_summary["semantic_duplicate_rate"])
    duplicate_improvement = max(0.0, (legacy_dup - zero_dup) / legacy_dup)

    article_types = sorted({s.article_type for s in samples if s.article_type})
    with_questions = sum(1 for s in samples if s.has_questions)
    without_questions = sum(1 for s in samples if not s.has_questions)
    fallback_failure_count = sum(1 for s in samples if not s.fallback_ok)

    return {
        "sample_count": len(samples),
        "article_types": article_types,
        "question_path_coverage": {
            "with_questions": with_questions,
            "without_questions": without_questions,
        },
        "legacy": legacy_summary,
        "zero_base": zero_summary,
        "semantic_duplicate_improvement_rate": duplicate_improvement,
        "fallback_failure_count": fallback_failure_count,
    }


def evaluate_phase07_gate(
    samples: List[ShadowSample],
    *,
    thresholds: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    resolved_thresholds = dict(DEFAULT_PHASE07_THRESHOLDS)
    if isinstance(thresholds, dict):
        resolved_thresholds.update(thresholds)

    validation_errors = validate_shadow_samples(samples)
    metrics = aggregate_shadow_metrics(samples)
    reasons: List[str] = []

    sample_count_ok = metrics["sample_count"] >= 15
    article_type_ok = len(metrics["article_types"]) >= 3
    question_path = metrics["question_path_coverage"]
    question_path_ok = question_path["with_questions"] > 0 and question_path["without_questions"] > 0
    fallback_ok = metrics["fallback_failure_count"] == 0

    category_score = _safe_float(metrics.get("zero_base", {}).get("category_consistency_score"))
    question_reflection = _safe_float(metrics.get("zero_base", {}).get("question_reflection_rate"))
    duplicate_improvement = _safe_float(metrics.get("semantic_duplicate_improvement_rate"))

    category_ok = category_score >= _safe_float(resolved_thresholds["category_consistency_score_min"])
    question_reflection_ok = question_reflection >= _safe_float(
        resolved_thresholds["question_reflection_rate_min"]
    )
    duplicate_ok = duplicate_improvement >= _safe_float(
        resolved_thresholds["semantic_duplicate_improvement_min"]
    )

    if validation_errors:
        reasons.extend(validation_errors)
    if not sample_count_ok:
        reasons.append("sample_count < 15")
    if not article_type_ok:
        reasons.append("article_type coverage < 3")
    if not question_path_ok:
        reasons.append("question path coverage is incomplete")
    if not fallback_ok:
        reasons.append("fallback path failure detected")
    if not category_ok:
        reasons.append("category_consistency_score below threshold")
    if not question_reflection_ok:
        reasons.append("question_reflection_rate below threshold")
    if not duplicate_ok:
        reasons.append("semantic duplicate improvement below threshold")

    all_required_ok = (
        not validation_errors
        and sample_count_ok
        and article_type_ok
        and question_path_ok
        and fallback_ok
        and category_ok
        and question_reflection_ok
        and duplicate_ok
    )

    if all_required_ok:
        decision = "go"
    else:
        severe_failure = (
            not fallback_ok
            or category_score < 0.80
            or question_reflection < 0.70
            or (metrics["sample_count"] >= 15 and duplicate_improvement < 0.0)
        )
        decision = "rollback" if severe_failure else "hold"

    return {
        "decision": decision,
        "thresholds": resolved_thresholds,
        "checks": {
            "sample_count_ok": sample_count_ok,
            "article_type_ok": article_type_ok,
            "question_path_ok": question_path_ok,
            "fallback_ok": fallback_ok,
            "category_ok": category_ok,
            "question_reflection_ok": question_reflection_ok,
            "duplicate_ok": duplicate_ok,
        },
        "metrics": metrics,
        "reasons": reasons,
        "validation_errors": validation_errors,
    }


def render_ab_report_markdown(evaluation: Dict[str, Any]) -> str:
    metrics = evaluation.get("metrics", {})
    legacy = metrics.get("legacy", {})
    zero_base = metrics.get("zero_base", {})
    checks = evaluation.get("checks", {})
    reasons = evaluation.get("reasons", [])
    question_cov = metrics.get("question_path_coverage", {})
    decision = evaluation.get("decision", "hold")

    lines = [
        "# A/B Shadow Report (Phase07)",
        "",
        "## Decision",
        f"- decision: {decision}",
        "",
        "## Coverage",
        f"- sample_count: {metrics.get('sample_count', 0)}",
        f"- article_types: {metrics.get('article_types', [])}",
        f"- with_questions: {question_cov.get('with_questions', 0)}",
        f"- without_questions: {question_cov.get('without_questions', 0)}",
        "",
        "## Metrics (avg)",
        "| metric | legacy | zero_base |",
        "|---|---:|---:|",
    ]

    for metric in REQUIRED_METRICS:
        lines.append(
            f"| {metric} | {legacy.get(metric, 0.0):.4f} | {zero_base.get(metric, 0.0):.4f} |"
        )

    lines.extend(
        [
            "",
            "## Gate Checks",
            f"- sample_count_ok: {checks.get('sample_count_ok', False)}",
            f"- article_type_ok: {checks.get('article_type_ok', False)}",
            f"- question_path_ok: {checks.get('question_path_ok', False)}",
            f"- fallback_ok: {checks.get('fallback_ok', False)}",
            f"- category_ok: {checks.get('category_ok', False)}",
            f"- question_reflection_ok: {checks.get('question_reflection_ok', False)}",
            f"- duplicate_ok: {checks.get('duplicate_ok', False)}",
            "",
            "## Reasons",
        ]
    )

    if reasons:
        for reason in reasons:
            lines.append(f"- {reason}")
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def build_shadow_sample(data: Dict[str, Any]) -> ShadowSample:
    return ShadowSample(
        sample_id=str(data.get("sample_id", "")),
        article_type=str(data.get("article_type", "")),
        has_questions=bool(data.get("has_questions", False)),
        legacy_metrics=dict(data.get("legacy_metrics", {})),
        zero_base_metrics=dict(data.get("zero_base_metrics", {})),
        fallback_ok=bool(data.get("fallback_ok", True)),
    )


def to_dict_list(samples: List[ShadowSample]) -> List[Dict[str, Any]]:
    return [asdict(sample) for sample in samples]


def split_by_category(samples: List[ShadowSample]) -> Dict[str, List[ShadowSample]]:
    grouped: Dict[str, List[ShadowSample]] = {}
    for sample in samples:
        grouped.setdefault(sample.article_type or "unknown", []).append(sample)
    return grouped


def compare_category_metrics(samples: List[ShadowSample]) -> Dict[str, Dict[str, float]]:
    grouped = split_by_category(samples)
    result: Dict[str, Dict[str, float]] = {}
    for category, category_samples in grouped.items():
        category_metrics = aggregate_shadow_metrics(category_samples)
        result[category] = {
            "legacy_category_consistency_score": _safe_float(
                category_metrics.get("legacy", {}).get("category_consistency_score")
            ),
            "zero_base_category_consistency_score": _safe_float(
                category_metrics.get("zero_base", {}).get("category_consistency_score")
            ),
            "legacy_question_reflection_rate": _safe_float(
                category_metrics.get("legacy", {}).get("question_reflection_rate")
            ),
            "zero_base_question_reflection_rate": _safe_float(
                category_metrics.get("zero_base", {}).get("question_reflection_rate")
            ),
        }
    return result
