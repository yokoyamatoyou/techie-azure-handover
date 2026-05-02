from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Mapping

BOUNDARY_MANIFEST_PATH = (
    Path(__file__).resolve().parents[1] / "vnext_current_integration" / "boundary_manifest.json"
)

ALLOWED_LANES = [
    "current-control",
    "vnext-engine",
    "shared-eval",
]

EXPECTED_ROUTE_MAPPING_SOURCE_OF_TRUTH = (
    "note.current_mainline_runner.resolve_current_mainline_ui_selection"
)

EXPECTED_CURRENT_OWNER_FILES = [
    "note/current_mainline_runner.py",
    "note/generation_request_builder.py",
    "note/current_mainline_runtime_logging.py",
    "note/note_writer_app.py",
]

EXPECTED_TEST_MAPPING = {
    "current-control": [
        "note/tests/test_current_mainline_runner.py",
        "note/tests/test_current_mainline_ui_matrix.py",
    ],
    "vnext-engine": [
        "note/tests/test_vnext_overlap_calibration.py",
    ],
    "shared-eval": [
        "note/tests/test_vnext_current_shared_eval.py",
    ],
    "boundary-freeze": [
        "note/tests/test_vnext_current_boundary_freeze.py",
    ],
}


@lru_cache(maxsize=1)
def load_vnext_current_boundary_manifest() -> Dict[str, Any]:
    return json.loads(BOUNDARY_MANIFEST_PATH.read_text(encoding="utf-8"))


def validate_vnext_current_boundary_manifest(
    manifest: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = dict(manifest or load_vnext_current_boundary_manifest())
    allowed_lanes = list(payload.get("allowed_lanes") or [])
    if allowed_lanes != ALLOWED_LANES:
        raise RuntimeError(f"boundary freeze lane drift: {allowed_lanes}")

    lane_rule = dict(payload.get("lane_rule") or {})
    if list(lane_rule.keys()) != ALLOWED_LANES:
        raise RuntimeError(f"boundary freeze lane rule keys drift: {list(lane_rule.keys())}")
    if any(not list(lane_rule.get(lane) or []) for lane in ALLOWED_LANES):
        raise RuntimeError("boundary freeze lane rule is incomplete")

    boundary = dict(payload.get("boundary_freeze") or {})
    route_mapping_source = str(boundary.get("route_mapping_source_of_truth") or "")
    if route_mapping_source != EXPECTED_ROUTE_MAPPING_SOURCE_OF_TRUTH:
        raise RuntimeError(
            "boundary freeze route mapping source drift: "
            f"{route_mapping_source or '<missing>'}"
        )

    current_owner_files = list(boundary.get("current_owner_files") or [])
    if current_owner_files != EXPECTED_CURRENT_OWNER_FILES:
        raise RuntimeError(f"boundary freeze current owner drift: {current_owner_files}")

    current_owner_count = int(boundary.get("current_owner_count") or 0)
    if current_owner_count != len(EXPECTED_CURRENT_OWNER_FILES):
        raise RuntimeError(f"boundary freeze current owner count drift: {current_owner_count}")

    non_targets = list(boundary.get("non_targets") or [])
    if "quarantine_only_slice10" not in non_targets:
        raise RuntimeError("boundary freeze lost quarantine_only_slice10 non-target")

    quarantine_rule = dict(boundary.get("quarantine_only_slice10") or {})
    if quarantine_rule.get("default_next_action_allowed") is not False:
        raise RuntimeError("boundary freeze reopened quarantine_only_slice10 by default")
    if str(quarantine_rule.get("reopen_condition") or "") != "shared_eval_blocker_only":
        raise RuntimeError("boundary freeze quarantine reopen condition drifted")

    test_mapping = dict(boundary.get("test_mapping") or {})
    if test_mapping != EXPECTED_TEST_MAPPING:
        raise RuntimeError("boundary freeze test mapping drifted")

    return payload


def build_vnext_current_boundary_summary(
    manifest: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = validate_vnext_current_boundary_manifest(manifest)
    boundary = dict(payload.get("boundary_freeze") or {})
    return {
        "manifest_version": str(payload.get("manifest_version") or ""),
        "generated_on": str(payload.get("generated_on") or ""),
        "allowed_lanes": list(payload.get("allowed_lanes") or []),
        "route_mapping_source_of_truth": str(boundary.get("route_mapping_source_of_truth") or ""),
        "current_owner_files": list(boundary.get("current_owner_files") or []),
        "current_owner_count": int(boundary.get("current_owner_count") or 0),
        "quarantine_only_slice10": dict(boundary.get("quarantine_only_slice10") or {}),
        "test_mapping": dict(boundary.get("test_mapping") or {}),
    }
