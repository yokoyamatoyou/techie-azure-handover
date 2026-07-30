from __future__ import annotations

import evaluate_newalgorithm_cases as eval_mod
from evaluate_newalgorithm_cases import FIXED_CASES, LEGAL_EVAL_CASES, _summarize_result


def test_fixed_cases_cover_mainline_regression_set() -> None:
    assert set(FIXED_CASES) == {
        "branding",
        "industry_analysis",
        "case_study",
        "announcement",
    }


def test_legal_eval_cases_cover_non_gate_legal_watch_set() -> None:
    assert set(LEGAL_EVAL_CASES) == {
        "legal_a_notice",
        "legal_b_compliance_explainer",
    }


def test_build_evaluation_pipeline_keeps_transitional_wrapper_for_offline() -> None:
    pipeline = eval_mod._build_evaluation_pipeline(live=False)

    assert isinstance(pipeline, eval_mod._TransitionalEvaluationPipeline)


def test_build_evaluation_pipeline_uses_llm_client_for_live(monkeypatch) -> None:
    sentinel_client = object()

    monkeypatch.setattr(eval_mod, "LLMClient", lambda: sentinel_client)

    pipeline = eval_mod._build_evaluation_pipeline(live=True)

    assert isinstance(pipeline, eval_mod._TransitionalEvaluationPipeline)
    assert getattr(pipeline, "_llm_client_missing", True) is False


def test_summarize_result_includes_case_specific_metrics() -> None:
    base_result = {
        "success": True,
        "reason_code": "OK",
        "title": "タイトル",
        "pipeline_check": {
            "runtime": {
                "primary_model": "gpt-5.4",
                "same_model_retry_count": 0,
                "model_fallback_attempted": False,
                "model_fallback_blocked": True,
            },
            "quality_metrics": {
                "body_chars": 4000,
                "topic_echo_ratio": 0.5,
                "topic_echo_body_only_ratio": 0.25,
                "topic_echo_long_span_count": 1,
                "section_opening_repetition_count": 0,
                "ending_distribution_top": {"です": 4},
                "example_specificity_count": 1,
                "abstract_example_fallback_count": 0,
                "unverified_legal_citation_count": 2,
                "case_result_abstract_summary_count": 0,
                "case_result_change_sentence_count": 2,
                "case_result_condition_sentence_count": 1,
                "fact_slot_coverage": 0.5,
                "fact_slot_reuse_count": 0,
                "announcement_invalid_modal_pattern_count": 0,
            },
        },
    }

    case_summary = _summarize_result("case_study", base_result)
    announcement_summary = _summarize_result("announcement", base_result)

    assert case_summary["metrics"]["case_result_change_sentence_count"] == 2
    assert case_summary["metrics"]["unverified_legal_citation_count"] == 2
    assert "fact_slot_coverage" not in case_summary["metrics"]
    assert announcement_summary["metrics"]["fact_slot_coverage"] == 0.5
    assert "case_result_change_sentence_count" not in announcement_summary["metrics"]
