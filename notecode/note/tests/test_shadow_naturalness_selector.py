from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_selector_module():
    tool_path = Path(__file__).resolve().parents[2] / "tools" / "select_shadow_naturalness_candidate.py"
    spec = importlib.util.spec_from_file_location("select_shadow_naturalness_candidate", tool_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _observation(**overrides: object) -> dict:
    base = {
        "variant_id": "fixture_clean",
        "blocked": False,
        "body_char_count": 1900,
        "body_length_target_result": "in_range",
        "ending_bucket_monotony": False,
        "ending_bucket_max_run": 5,
        "unsupported_claim_count": 0,
        "source_grounding_warning_count": 0,
        "must_cover_warning_count": 0,
        "legal_guarantee_warning": False,
        "first_person_safety": "safe",
        "closing_recall_success": True,
        "internal_term_leakage": False,
        "shape_flags": {
            "ai_summary_tone": False,
            "third_party_intro_tone": False,
            "textbook_explanation_tone": False,
            "generic_listicle_shape": False,
            "source_by_source_summary_shape": False,
        },
        "stylometry_metrics": {
            "gpt_frequent_term_total": 0,
            "abstract_terms_per_1000_chars": 0.5,
            "explicit_subject_count": 2,
            "connector_total": 4,
            "function_word_proxy_profile": {"method": "surface_substring_proxy_no_morphology"},
            "punctuation_profile": {"period_count": 20},
        },
    }
    base.update(overrides)
    return base


def test_score_marks_clean_in_range_observation_as_manual_review_candidate() -> None:
    module = _load_selector_module()

    scored = module.score_observation(_observation())

    assert scored["candidate_state"] == "candidate_for_manual_review"
    assert scored["hard_issues"] == []
    assert scored["score"] >= 90


def test_hard_issues_reject_legal_short_and_monotony() -> None:
    module = _load_selector_module()

    scored = module.score_observation(
        _observation(
            variant_id="fixture_rejected",
            body_char_count=1115,
            body_length_target_result="short",
            ending_bucket_monotony=True,
            ending_bucket_max_run=12,
            legal_guarantee_warning=True,
        )
    )

    assert scored["candidate_state"] == "not_candidate"
    assert "legal_guarantee_warning" in scored["hard_issues"]
    assert "body_length_not_in_range" in scored["hard_issues"]
    assert "ending_bucket_monotony" in scored["hard_issues"]


def test_selector_ranks_existing_summaries_without_generation(tmp_path) -> None:
    module = _load_selector_module()
    rejected = {
        "run_id": "rejected_run",
        "decision": "reject",
        "variant_observations": [
            _observation(
                variant_id="fixture_rejected",
                body_char_count=1000,
                body_length_target_result="short",
                ending_bucket_monotony=True,
                ending_bucket_max_run=12,
            )
        ],
    }
    clean = {
        "run_id": "clean_run",
        "decision": "continue_shadow",
        "variant_observations": [_observation(variant_id="fixture_clean")],
    }
    rejected_path = tmp_path / "rejected" / "compare_summary.json"
    clean_path = tmp_path / "clean" / "compare_summary.json"
    rejected_path.parent.mkdir()
    clean_path.parent.mkdir()
    rejected_path.write_text(json.dumps(rejected, ensure_ascii=False), encoding="utf-8")
    clean_path.write_text(json.dumps(clean, ensure_ascii=False), encoding="utf-8")

    result = module.select_naturalness_candidate(
        [
            {**module.load_compare_summary(rejected_path), "_artifact_source": str(rejected_path)},
            {**module.load_compare_summary(clean_path), "_artifact_source": str(clean_path)},
        ]
    )

    assert result["selection_policy"] == "artifact_only_no_generation_no_adoption"
    assert result["recommendation"] == "manual_review_candidate"
    assert result["best"]["variant_id"] == "fixture_clean"
    assert result["candidate_count"] == 2
    assert result["skipped_summary_count"] == 0


def test_selector_reports_summaries_without_variant_observations() -> None:
    module = _load_selector_module()

    result = module.select_naturalness_candidate(
        [
            {
                "_artifact_source": "preflight/compare_summary.json",
                "run_id": "preflight_run",
                "decision": "preflight_ready",
                "variant_observations": [],
            }
        ]
    )

    assert result["recommendation"] == "no_clean_candidate"
    assert result["candidate_count"] == 0
    assert result["skipped_summary_count"] == 1
    assert result["skipped_summaries"][0] == {
        "artifact_source": "preflight/compare_summary.json",
        "run_id": "preflight_run",
        "decision": "preflight_ready",
        "reason": "no_variant_observations",
    }
