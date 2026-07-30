from __future__ import annotations

import json

import pytest

from tools.route_v_validation_runtime_env import (
    ROUTE_V_ARTICLE_BRIEF_ALGORITHM_ENV,
    RouteVValidationEnvContractError,
    assert_route_v_runtime_env_before_api,
    build_route_v_runtime_env_preflight,
    route_v_validation_runtime_env,
)


def test_route_v_validation_preflight_blocks_when_v2_env_is_missing(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv(ROUTE_V_ARTICLE_BRIEF_ALGORITHM_ENV, raising=False)

    result = build_route_v_runtime_env_preflight(owner="unit_owner", artifact_root=tmp_path)

    assert result["pass"] is False
    assert result["api_send_count"] == 0
    assert result["route_v_article_brief_algorithm_active"] is False
    assert result["daily_activity_source_role_contract_expected"] is False
    assert result["selected_source_excerpts_expected"] is False
    assert "daily_activity_source_role_contract_expected" in result["checks"]
    with pytest.raises(RouteVValidationEnvContractError, match="route_v_article_brief_algorithm_active"):
        assert_route_v_runtime_env_before_api(owner="unit_owner", artifact_root=tmp_path)


def test_route_v_validation_runtime_env_activates_v2_before_api_and_restores(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(ROUTE_V_ARTICLE_BRIEF_ALGORITHM_ENV, "legacy")
    monkeypatch.setenv("OPENAI_MODEL", "existing-model")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "low")

    with route_v_validation_runtime_env(
        model="gpt-5.4-mini",
        reasoning_effort="high",
        request_timeout_seconds=180,
    ):
        result = assert_route_v_runtime_env_before_api(owner="unit_owner", artifact_root=tmp_path)

        assert result["pass"] is True
        assert result["api_send_count"] == 0
        assert result["route_v_article_brief_algorithm_active"] is True
        assert result["source_shape_v2_fields_expected"] is True
        assert result["daily_activity_source_role_contract_expected"] is True
        assert result["selected_source_excerpts_expected"] is True
        assert result["genre_specific_expectations"]["daily_activity_source_role_contract"] == {
            "expected": True,
            "required_for_expected_genre": True,
            "required_check": "daily_activity_source_role_contract_expected",
        }
        assert result["checks"]["daily_activity_source_role_contract_expected"] is True

    assert result["raw_full_source_documents_passed"] is False
    assert result["raw_full_source_packets_passed"] is False
    assert result["raw_full_source_cards_passed"] is False
    assert result["legacy_body_route_fallback_used"] is False
    assert result["writer_only_fallback_used"] is False
    assert (tmp_path / "preflight_no_api_results.json").exists()
    written = json.loads((tmp_path / "preflight_no_api_results.json").read_text(encoding="utf-8"))
    assert written["pass"] is True
    assert written["api_send_count"] == 0
    assert written["checks"]["raw_full_source_handoff_false"] is True
    assert written["checks"]["legacy_body_route_fallback_false"] is True
    assert written["checks"]["writer_only_fallback_false"] is True

    import os

    assert os.environ[ROUTE_V_ARTICLE_BRIEF_ALGORITHM_ENV] == "legacy"
    assert os.environ["OPENAI_MODEL"] == "existing-model"
    assert os.environ["OPENAI_REASONING_EFFORT"] == "low"


def test_route_v_validation_preflight_keeps_daily_activity_expectation_metadata_for_market_explanation(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv(ROUTE_V_ARTICLE_BRIEF_ALGORITHM_ENV, "legacy")

    with route_v_validation_runtime_env():
        result = assert_route_v_runtime_env_before_api(
            owner="unit_owner",
            expected_genre_id="market_explanation",
            artifact_root=tmp_path,
        )

    assert result["pass"] is True
    assert result["api_send_count"] == 0
    assert result["expected_genre_id"] == "market_explanation"
    assert result["route_v_article_brief_algorithm_active"] is True
    assert result["source_shape_v2_fields_expected"] is True
    assert result["selected_source_excerpts_expected"] is True
    assert result["daily_activity_source_role_contract_expected"] is False
    assert result["genre_specific_expectations"]["daily_activity_source_role_contract"] == {
        "expected": False,
        "required_for_expected_genre": False,
        "required_check": None,
    }
    assert "daily_activity_source_role_contract_expected" not in result["checks"]
    assert "daily_activity_source_role_contract_expected" not in result["required_checks"]
    assert result["checks"]["raw_full_source_handoff_false"] is True
    assert result["checks"]["legacy_body_route_fallback_false"] is True
    assert result["checks"]["writer_only_fallback_false"] is True

    written = json.loads((tmp_path / "preflight_no_api_results.json").read_text(encoding="utf-8"))
    assert written["pass"] is True
    assert written["daily_activity_source_role_contract_expected"] is False
    assert "daily_activity_source_role_contract_expected" not in written["checks"]
