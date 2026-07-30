from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_V_ARTICLE_BRIEF_ALGORITHM_ENV = "ROUTE_V_ARTICLE_BRIEF_ALGORITHM"
ROUTE_V_ARTICLE_BRIEF_ALGORITHM_VALUE = "v2"

ROUTE_V_VALIDATION_RETRY_ENV_DEFAULTS = {
    "ROUTE_0506_SOURCE_CARD_MAX_RETRIES": "0",
    "ROUTE_0506_JSON_STAGE_MAX_RETRIES": "0",
    "ROUTE_0506_DRAFT_WRITER_MAX_RETRIES": "0",
}


class RouteVValidationEnvContractError(RuntimeError):
    pass


@contextmanager
def route_v_validation_runtime_env(
    *,
    model: str | None = None,
    reasoning_effort: str | None = None,
    request_timeout_seconds: str | int | None = None,
    disable_retries: bool = True,
) -> Iterator[None]:
    env_values: dict[str, str] = {
        ROUTE_V_ARTICLE_BRIEF_ALGORITHM_ENV: ROUTE_V_ARTICLE_BRIEF_ALGORITHM_VALUE,
    }
    if model:
        env_values["OPENAI_MODEL"] = str(model)
    if reasoning_effort:
        env_values["OPENAI_REASONING_EFFORT"] = str(reasoning_effort)
    if request_timeout_seconds is not None:
        env_values["ROUTE_0506_OPENAI_REQUEST_TIMEOUT_SECONDS"] = str(request_timeout_seconds)
    if disable_retries:
        env_values.update(ROUTE_V_VALIDATION_RETRY_ENV_DEFAULTS)

    previous = {key: os.environ.get(key) for key in env_values}
    try:
        for key, value in env_values.items():
            os.environ[key] = value
        yield
    finally:
        for key, old_value in previous.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def build_route_v_runtime_env_preflight(
    *,
    owner: str,
    expected_genre_id: str = "daily_activity",
    artifact_root: Path | str | None = None,
) -> dict[str, Any]:
    active = os.environ.get(ROUTE_V_ARTICLE_BRIEF_ALGORITHM_ENV) == ROUTE_V_ARTICLE_BRIEF_ALGORITHM_VALUE
    daily_activity = expected_genre_id == "daily_activity"
    result = {
        "owner": owner,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_genre_id": expected_genre_id,
        "api_send_count": 0,
        "route_v_article_brief_algorithm_env": os.environ.get(ROUTE_V_ARTICLE_BRIEF_ALGORITHM_ENV),
        "route_v_article_brief_algorithm_active": active,
        "source_shape_v2_fields_expected": active,
        "daily_activity_source_role_contract_expected": active and daily_activity,
        "selected_source_excerpts_expected": active,
        "raw_full_source_handoff_expected": False,
        "raw_full_source_documents_passed": False,
        "raw_full_source_packets_passed": False,
        "raw_full_source_cards_passed": False,
        "legacy_body_route_fallback_used": False,
        "writer_only_fallback_used": False,
        "checks": {},
    }
    common_checks = {
        "route_v_article_brief_algorithm_active": result["route_v_article_brief_algorithm_active"],
        "source_shape_v2_fields_expected": result["source_shape_v2_fields_expected"],
        "selected_source_excerpts_expected": result["selected_source_excerpts_expected"],
        "raw_full_source_handoff_false": not result["raw_full_source_documents_passed"]
        and not result["raw_full_source_packets_passed"]
        and not result["raw_full_source_cards_passed"],
        "legacy_body_route_fallback_false": not result["legacy_body_route_fallback_used"],
        "writer_only_fallback_false": not result["writer_only_fallback_used"],
    }
    genre_specific_expectations = {
        "daily_activity_source_role_contract": {
            "expected": result["daily_activity_source_role_contract_expected"],
            "required_for_expected_genre": daily_activity,
            "required_check": "daily_activity_source_role_contract_expected" if daily_activity else None,
        }
    }
    result["genre_specific_expectations"] = genre_specific_expectations
    result["checks"] = dict(common_checks)
    if daily_activity:
        result["checks"]["daily_activity_source_role_contract_expected"] = result[
            "daily_activity_source_role_contract_expected"
        ]
    result["required_checks"] = list(result["checks"])
    result["pass"] = all(result["checks"].values())
    if artifact_root is not None:
        root = Path(artifact_root)
        root.mkdir(parents=True, exist_ok=True)
        (root / "preflight_no_api_results.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return result


def assert_route_v_runtime_env_before_api(
    *,
    owner: str,
    expected_genre_id: str = "daily_activity",
    artifact_root: Path | str | None = None,
) -> dict[str, Any]:
    result = build_route_v_runtime_env_preflight(
        owner=owner,
        expected_genre_id=expected_genre_id,
        artifact_root=artifact_root,
    )
    if not result["pass"]:
        failures = [name for name, passed in result["checks"].items() if not passed]
        raise RouteVValidationEnvContractError(
            "route_v_validation_runtime_env_preflight_failed:" + ",".join(failures)
        )
    return result
