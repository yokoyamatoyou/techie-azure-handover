"""Tests for phase07 shadow A/B evaluation and security gate."""

from __future__ import annotations

from note.zero_base.phase07_shadow_eval import (
    ShadowSample,
    compare_category_metrics,
    evaluate_phase07_gate,
    validate_shadow_samples,
)


def _build_samples(count: int = 15) -> list[ShadowSample]:
    article_types = ["ai", "announcement", "branding"]
    samples: list[ShadowSample] = []
    for idx in range(count):
        article_type = article_types[idx % len(article_types)]
        samples.append(
            ShadowSample(
                sample_id=f"s{idx + 1:02d}",
                article_type=article_type,
                has_questions=(idx % 2 == 0),
                legacy_metrics={
                    "semantic_duplicate_rate": 0.40,
                    "coherence_score": 0.86,
                    "subject_explicit_rate": 0.62,
                    "category_consistency_score": 0.93,
                    "question_reflection_rate": 0.78,
                    "latency_ms": 900.0,
                    "token_cost": 1.80,
                },
                zero_base_metrics={
                    "semantic_duplicate_rate": 0.28,
                    "coherence_score": 0.88,
                    "subject_explicit_rate": 0.66,
                    "category_consistency_score": 0.97,
                    "question_reflection_rate": 0.90,
                    "latency_ms": 760.0,
                    "token_cost": 1.55,
                },
                fallback_ok=True,
            )
        )
    return samples


def test_phase07_gate_go_with_passing_metrics() -> None:
    samples = _build_samples(15)
    evaluation = evaluate_phase07_gate(samples)
    assert evaluation["decision"] == "go"
    assert evaluation["checks"]["sample_count_ok"] is True
    assert evaluation["checks"]["article_type_ok"] is True
    assert evaluation["checks"]["question_path_ok"] is True


def test_phase07_gate_hold_when_sample_count_insufficient() -> None:
    samples = _build_samples(12)
    evaluation = evaluate_phase07_gate(samples)
    assert evaluation["decision"] == "hold"
    assert evaluation["checks"]["sample_count_ok"] is False


def test_phase07_gate_rollback_on_fallback_failure() -> None:
    samples = _build_samples(15)
    samples[0].fallback_ok = False
    evaluation = evaluate_phase07_gate(samples)
    assert evaluation["decision"] == "rollback"
    assert evaluation["checks"]["fallback_ok"] is False


def test_phase07_validation_detects_missing_metrics() -> None:
    broken = _build_samples(1)
    broken[0].zero_base_metrics.pop("coherence_score")
    errors = validate_shadow_samples(broken)
    assert errors
    assert "coherence_score" in errors[0]


def test_phase07_category_regression_set_covers_three_categories() -> None:
    samples = _build_samples(18)
    category_metrics = compare_category_metrics(samples)
    assert len(category_metrics.keys()) >= 3
    assert "announcement" in category_metrics
