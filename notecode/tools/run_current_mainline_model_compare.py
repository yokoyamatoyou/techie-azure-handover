from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG_PATH = PROJECT_ROOT / "config.json"
UI_MATRIX_SCRIPT = PROJECT_ROOT / "tools" / "run_current_mainline_ui_matrix.py"
DEFAULT_MODELS = ["gpt-5.4-mini", "gpt-4.1-mini-2025-04-14"]
DEFAULT_SENTINEL_CASE_IDS = [
    "ui-short-announcement-dense-must-cover",
    "ui-short-comparative-axis-lock",
]
DEFAULT_COMPARE_VERBOSITY = "medium"
DEFAULT_POSTPROCESS_NEUTRAL = True
COMBINED_SUMMARY_SCHEMA_VERSION = "dual_lane_postprocess_compare_v1"
COMBINED_WATCH_CASE_IDS = [
    "ui-short-branding-company-grounded",
    "ui-short-announcement-dense-must-cover",
]
COMBINED_WATCH_QUALITY_METRICS = [
    "connective_opening_rate",
    "single_sentence_paragraph_ratio",
    "paragraph_sentence_count_cv",
]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def _slugify_model_name(model_name: str) -> str:
    safe = []
    for char in str(model_name or "").strip().lower():
        if char.isalnum():
            safe.append(char)
        elif char in {".", "-", "_"}:
            safe.append("-")
    slug = "".join(safe).strip("-")
    return slug or "model"


def _append_prefix(values: Sequence[Any], prefix: str) -> List[str]:
    items = [str(item or "").strip() for item in values if str(item or "").strip()]
    if prefix not in items:
        items.append(prefix)
    return items


def _build_compare_config(
    base_config: Mapping[str, Any],
    *,
    section_model: str,
    reasoning_effort: str,
    matched_runtime: bool,
    compare_verbosity: str,
    postprocess_neutral: bool,
) -> Dict[str, Any]:
    config = deepcopy(dict(base_config or {}))
    llm = dict(config.get("llm") or {})
    task_models = dict(llm.get("task_models") or {})
    task_models["section"] = str(section_model)
    llm["task_models"] = task_models
    llm["reasoning_effort"] = str(reasoning_effort or "")
    requested_compare_verbosity = str(compare_verbosity or "").strip()
    article_type_params = dict(llm.get("article_type_params") or {})
    if requested_compare_verbosity:
        normalized_article_type_params: Dict[str, Any] = {}
        for article_type, params in article_type_params.items():
            current = dict(params) if isinstance(params, Mapping) else {}
            current["verbosity"] = requested_compare_verbosity
            normalized_article_type_params[str(article_type)] = current
        llm["article_type_params"] = normalized_article_type_params
    if matched_runtime:
        llm["disable_temperature_model_prefixes"] = _append_prefix(
            list(llm.get("disable_temperature_model_prefixes") or []),
            "gpt-4.1",
        )
        llm["disable_top_p_model_prefixes"] = _append_prefix(
            list(llm.get("disable_top_p_model_prefixes") or []),
            "gpt-4.1",
        )
        llm["disable_penalty_model_prefixes"] = _append_prefix(
            list(llm.get("disable_penalty_model_prefixes") or []),
            "gpt-4.1",
        )
    config["llm"] = llm
    if postprocess_neutral:
        # Keep compare runs closer to model behavior by avoiding heavy downstream rewrites.
        quality_pipeline = dict(config.get("quality_pipeline") or {})
        quality_pipeline["mode"] = "shadow"
        config["quality_pipeline"] = quality_pipeline

        semantic_dedupe = dict(config.get("semantic_dedupe") or {})
        semantic_dedupe["rewrite_enabled"] = False
        config["semantic_dedupe"] = semantic_dedupe
    return config


def _build_sentinel_short_manifest(case_ids: Sequence[str]) -> Dict[str, Any]:
    return {
        "matrix_status": "ready",
        "results": [
            {
                "case_id": str(case_id or ""),
                "short_gate": {"passed": True},
            }
            for case_id in case_ids
            if str(case_id or "").strip()
        ],
    }


def _run_matrix_phase(
    *,
    config_path: Path,
    phase: str,
    output_path: Path,
    timeout_sec: int,
    promote_from: Path | None = None,
) -> Dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(UI_MATRIX_SCRIPT),
        "--phase",
        str(phase),
        "--live",
        "--output",
        str(output_path),
    ]
    if promote_from is not None:
        command.extend(["--promote-from", str(promote_from)])
    env = dict(os.environ)
    env["TECHIE_CONFIG_PATH"] = str(config_path)
    completed = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=max(60, int(timeout_sec)),
    )
    payload = _load_json(output_path)
    payload["process_returncode"] = int(completed.returncode)
    payload["process_stdout"] = str(completed.stdout or "")
    payload["process_stderr"] = str(completed.stderr or "")
    payload["config_path"] = str(config_path)
    payload["phase"] = str(phase)
    payload["saved_to"] = str(output_path)
    return payload


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _build_short_run_summary(payload: Mapping[str, Any]) -> Dict[str, Any]:
    battery_summary = dict(payload.get("battery_summary") or {})
    runtime_contract = dict(battery_summary.get("runtime_contract") or {})
    return {
        "matrix_status": str(payload.get("matrix_status") or ""),
        "rubric_mean_total": _safe_float(battery_summary.get("rubric_mean_total")),
        "go_for_long_form": bool(battery_summary.get("go_for_long_form", False)),
        "hard_fail_case_count": len(list(battery_summary.get("hard_fail_case_ids") or [])),
        "retry_case_count": len(list(runtime_contract.get("retry_case_ids") or [])),
        "fallback_case_count": len(list(runtime_contract.get("fallback_case_ids") or [])),
        "selected_models": list(runtime_contract.get("selected_models") or []),
        "go_no_go_reasons": list(battery_summary.get("go_no_go_reasons") or []),
        "output_path": str(payload.get("saved_to") or ""),
        "process_returncode": int(payload.get("process_returncode", 0) or 0),
    }


def _build_long_run_summary(payload: Mapping[str, Any]) -> Dict[str, Any]:
    battery_summary = dict(payload.get("battery_summary") or {})
    results = list(payload.get("results") or [])
    return {
        "matrix_status": str(payload.get("matrix_status") or ""),
        "rubric_mean_total": _safe_float(battery_summary.get("rubric_mean_total")),
        "success_count": sum(1 for item in results if bool(dict(item).get("success", False))),
        "result_count": len(results),
        "short_gate_passed_count": sum(
            1 for item in results if bool(dict(dict(item).get("short_gate") or {}).get("passed", False))
        ),
        "output_path": str(payload.get("saved_to") or ""),
        "process_returncode": int(payload.get("process_returncode", 0) or 0),
    }


def _aggregate_runs(run_summaries: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    rubric_values = [_safe_float(item.get("rubric_mean_total")) for item in run_summaries]
    return {
        "run_count": len(run_summaries),
        "blocked_count": sum(1 for item in run_summaries if str(item.get("matrix_status") or "") != "ready"),
        "rubric_mean_total_mean": round(sum(rubric_values) / len(rubric_values), 2) if rubric_values else 0.0,
        "rubric_mean_total_min": round(min(rubric_values), 2) if rubric_values else 0.0,
        "rubric_mean_total_max": round(max(rubric_values), 2) if rubric_values else 0.0,
        "go_for_long_form_count": sum(1 for item in run_summaries if bool(item.get("go_for_long_form", False))),
        "hard_fail_case_total": sum(int(item.get("hard_fail_case_count", 0) or 0) for item in run_summaries),
        "retry_case_total": sum(int(item.get("retry_case_count", 0) or 0) for item in run_summaries),
        "fallback_case_total": sum(int(item.get("fallback_case_count", 0) or 0) for item in run_summaries),
    }


def _compare_models(model_payloads: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    if len(model_payloads) != 2:
        return {
            "material_difference_detected": False,
            "reasons": [],
            "preferred_primary_model": "",
        }
    left, right = model_payloads
    left_short = dict(left.get("short_aggregate") or {})
    right_short = dict(right.get("short_aggregate") or {})
    left_long = dict(left.get("long_aggregate") or {})
    right_long = dict(right.get("long_aggregate") or {})
    reasons: List[str] = []
    short_delta = abs(
        _safe_float(left_short.get("rubric_mean_total_mean")) - _safe_float(right_short.get("rubric_mean_total_mean"))
    )
    if short_delta >= 0.5:
        reasons.append(f"short_rubric_delta={round(short_delta, 2)}")
    long_delta = abs(
        _safe_float(left_long.get("rubric_mean_total_mean")) - _safe_float(right_long.get("rubric_mean_total_mean"))
    )
    if long_delta >= 0.5:
        reasons.append(f"long_rubric_delta={round(long_delta, 2)}")
    if int(left_short.get("hard_fail_case_total", 0) or 0) != int(right_short.get("hard_fail_case_total", 0) or 0):
        reasons.append("short_hard_fail_total_diff")
    if int(left_short.get("retry_case_total", 0) or 0) != int(right_short.get("retry_case_total", 0) or 0):
        reasons.append("short_retry_total_diff")
    if int(left_short.get("blocked_count", 0) or 0) > 0 or int(right_short.get("blocked_count", 0) or 0) > 0:
        reasons.append("blocked_preflight_present")

    preferred_primary_model = ""
    left_score = (
        _safe_float(left_short.get("rubric_mean_total_mean")),
        _safe_float(left_long.get("rubric_mean_total_mean")),
        -int(left_short.get("hard_fail_case_total", 0) or 0),
        -int(left_short.get("retry_case_total", 0) or 0),
    )
    right_score = (
        _safe_float(right_short.get("rubric_mean_total_mean")),
        _safe_float(right_long.get("rubric_mean_total_mean")),
        -int(right_short.get("hard_fail_case_total", 0) or 0),
        -int(right_short.get("retry_case_total", 0) or 0),
    )
    if left_score != right_score:
        preferred_primary_model = str(
            left.get("model_name") if left_score > right_score else right.get("model_name")
        )

    return {
        "material_difference_detected": len(reasons) > 0,
        "reasons": reasons,
        "preferred_primary_model": preferred_primary_model,
    }


def _build_compare_summary(
    *,
    base_config: Mapping[str, Any],
    models: Sequence[str],
    reasoning_effort: str,
    compare_verbosity: str,
    matched_runtime: bool,
    postprocess_neutral: bool,
    short_repeats: int,
    long_repeats: int,
    sentinel_case_ids: Sequence[str],
    short_timeout_sec: int,
    long_timeout_sec: int,
    run_root: Path,
    output_path: Path,
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "reasoning_effort": str(reasoning_effort or ""),
        "compare_verbosity": str(compare_verbosity or ""),
        "matched_runtime": bool(matched_runtime),
        "postprocess_neutral": bool(postprocess_neutral),
        "short_repeats": int(short_repeats),
        "long_repeats": int(long_repeats),
        "sentinel_case_ids": list(sentinel_case_ids or []),
        "models": [],
    }

    with tempfile.TemporaryDirectory(prefix="techie-config-") as temp_dir:
        temp_root = Path(temp_dir)
        for model_name in models:
            slug = _slugify_model_name(model_name)
            temp_config_path = temp_root / f"{slug}.json"
            compare_config = _build_compare_config(
                base_config,
                section_model=model_name,
                reasoning_effort=str(reasoning_effort or ""),
                matched_runtime=bool(matched_runtime),
                compare_verbosity=str(compare_verbosity or ""),
                postprocess_neutral=bool(postprocess_neutral),
            )
            _write_json(temp_config_path, compare_config)
            model_root = run_root / slug
            short_runs: List[Dict[str, Any]] = []
            long_runs: List[Dict[str, Any]] = []

            for repeat_index in range(1, max(0, int(short_repeats)) + 1):
                short_output_path = model_root / "short" / f"repeat-{repeat_index:02d}.json"
                short_payload = _run_matrix_phase(
                    config_path=temp_config_path,
                    phase="short",
                    output_path=short_output_path,
                    timeout_sec=int(short_timeout_sec),
                )
                short_runs.append(_build_short_run_summary(short_payload))

            for repeat_index in range(1, max(0, int(long_repeats)) + 1):
                sentinel_manifest_path = model_root / "manifests" / f"long-sentinel-{repeat_index:02d}.json"
                _write_json(sentinel_manifest_path, _build_sentinel_short_manifest(sentinel_case_ids))
                long_output_path = model_root / "long" / f"repeat-{repeat_index:02d}.json"
                long_payload = _run_matrix_phase(
                    config_path=temp_config_path,
                    phase="long",
                    output_path=long_output_path,
                    timeout_sec=int(long_timeout_sec),
                    promote_from=sentinel_manifest_path,
                )
                long_runs.append(_build_long_run_summary(long_payload))

            summary["models"].append(
                {
                    "model_name": str(model_name),
                    "config_path": str(temp_config_path),
                    "short_runs": short_runs,
                    "short_aggregate": _aggregate_runs(short_runs),
                    "long_runs": long_runs,
                    "long_aggregate": _aggregate_runs(long_runs),
                }
            )

    summary["comparison"] = _compare_models(list(summary.get("models") or []))
    _write_json(output_path, summary)
    summary["saved_to"] = str(output_path)
    return summary


def _build_lane_model_brief(model_payload: Mapping[str, Any]) -> Dict[str, Any]:
    short_aggregate = dict(model_payload.get("short_aggregate") or {})
    long_aggregate = dict(model_payload.get("long_aggregate") or {})
    return {
        "model_name": str(model_payload.get("model_name") or ""),
        "short_mean": round(_safe_float(short_aggregate.get("rubric_mean_total_mean")), 2),
        "short_hard_fail_total": int(short_aggregate.get("hard_fail_case_total", 0) or 0),
        "short_retry_total": int(short_aggregate.get("retry_case_total", 0) or 0),
        "short_fallback_total": int(short_aggregate.get("fallback_case_total", 0) or 0),
        "long_mean": round(_safe_float(long_aggregate.get("rubric_mean_total_mean")), 2),
        "long_hard_fail_total": int(long_aggregate.get("hard_fail_case_total", 0) or 0),
        "long_retry_total": int(long_aggregate.get("retry_case_total", 0) or 0),
        "long_fallback_total": int(long_aggregate.get("fallback_case_total", 0) or 0),
    }


def _build_lane_brief(summary: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "summary_path": str(summary.get("saved_to") or ""),
        "postprocess_neutral": bool(summary.get("postprocess_neutral", False)),
        "models": [_build_lane_model_brief(item) for item in list(summary.get("models") or [])],
        "comparison": dict(summary.get("comparison") or {}),
    }


def _first_short_repeat_path(model_payload: Mapping[str, Any]) -> str:
    for run in list(model_payload.get("short_runs") or []):
        path = str(run.get("output_path") or "").strip()
        if path:
            return path
    return ""


def _load_case_quality_metrics_from_artifact(artifact_path: str) -> Dict[str, Any]:
    artifact = str(artifact_path or "").strip()
    if not artifact:
        return {}
    path = Path(artifact)
    if not path.exists():
        return {}
    try:
        payload = _load_json(path)
    except (OSError, json.JSONDecodeError):
        return {}
    result = dict(payload.get("result") or {})
    pipeline_check = dict(result.get("pipeline_check") or {})
    return dict(pipeline_check.get("quality_metrics") or {})


def _classify_comparative_axis_state(axis_shift_count: Any, absolute_winner_count: Any) -> Dict[str, Any]:
    axis_shift = int(axis_shift_count or 0)
    absolute_winner = int(absolute_winner_count or 0)
    if absolute_winner > 0 or axis_shift > 4:
        score = 0
        reason = "comparative_axis_broken"
    elif axis_shift > 1:
        score = 1
        reason = "comparative_axis_soft_shift"
    else:
        score = 2
        reason = "comparative_axis_locked"
    return {
        "score": score,
        "reason": reason,
        "comparative_axis_shift_count": axis_shift,
        "comparative_absolute_winner_claim_count": absolute_winner,
    }


def _extract_comparative_stage_payload(pipeline_check: Mapping[str, Any], stage_name: str) -> Dict[str, Any]:
    diagnostic = dict(pipeline_check.get("comparative_stage_diagnostic") or {})
    for item in list(diagnostic.get("stages") or []):
        stage = dict(item or {})
        if str(stage.get("stage") or "") == str(stage_name or ""):
            return stage
    return {}


def _build_comparative_stability_from_pipeline_check(
    pipeline_check: Mapping[str, Any],
    article_type_fit_reason: str,
) -> Dict[str, Any]:
    diagnostic = dict(pipeline_check.get("comparative_stage_diagnostic") or {})
    quality_metrics = dict(pipeline_check.get("quality_metrics") or {})
    stage_payload = _extract_comparative_stage_payload(pipeline_check, "section_generation")
    stage_metrics = dict(stage_payload.get("metrics") or stage_payload or quality_metrics)
    has_comparative_metrics = any(
        metric_name in stage_metrics or metric_name in quality_metrics
        for metric_name in (
            "comparative_axis_shift_count",
            "comparative_absolute_winner_claim_count",
        )
    )
    enabled = bool(diagnostic) or has_comparative_metrics or str(article_type_fit_reason or "").startswith("comparative_")
    if not enabled:
        return {"enabled": False}
    stage_eval = _classify_comparative_axis_state(
        stage_metrics.get("comparative_axis_shift_count"),
        stage_metrics.get("comparative_absolute_winner_claim_count"),
    )
    return {
        "enabled": True,
        "primary_stage": "section_generation",
        "section_generation_available": bool(stage_payload),
        "axis_shift_count": stage_eval["comparative_axis_shift_count"],
        "absolute_winner_claim_count": stage_eval["comparative_absolute_winner_claim_count"],
        "stage_bucket": stage_eval["reason"],
        "stage_score": stage_eval["score"],
        "rubric_reason": str(article_type_fit_reason or ""),
        "bucket_matches_rubric": stage_eval["reason"] == str(article_type_fit_reason or ""),
        "first_changed_stage": str(diagnostic.get("first_changed_stage") or ""),
        "changed_stage_names": list(diagnostic.get("changed_stage_names") or []),
        "section_generation_metrics": {
            "body_chars": stage_metrics.get("body_chars"),
            "comparative_axis_shift_count": stage_eval["comparative_axis_shift_count"],
            "comparative_absolute_winner_claim_count": stage_eval["comparative_absolute_winner_claim_count"],
            "topic_echo_body_only_ratio": stage_metrics.get("topic_echo_body_only_ratio"),
            "paragraph_break_semantic_score": stage_metrics.get("paragraph_break_semantic_score"),
            "connective_opening_rate": stage_metrics.get("connective_opening_rate"),
            "paragraph_sentence_count_cv": stage_metrics.get("paragraph_sentence_count_cv"),
        },
    }


def _load_case_artifact_projection(artifact_path: str) -> Dict[str, Any]:
    artifact = str(artifact_path or "").strip()
    if not artifact:
        return {"quality_metrics": {}, "comparative_stability": {}}
    path = Path(artifact)
    if not path.exists():
        return {"quality_metrics": {}, "comparative_stability": {}}
    try:
        payload = _load_json(path)
    except (OSError, json.JSONDecodeError):
        return {"quality_metrics": {}, "comparative_stability": {}}
    result = dict(payload.get("result") or {})
    pipeline_check = dict(payload.get("pipeline_check") or result.get("pipeline_check") or {})
    quality_metrics = dict((result.get("pipeline_check") or {}).get("quality_metrics") or pipeline_check.get("quality_metrics") or {})
    rubric = dict(payload.get("rubric") or {})
    axis_scores = {
        str(key): dict(value)
        for key, value in dict(rubric.get("axis_scores") or {}).items()
    }
    article_type_fit_reason = str(dict(axis_scores.get("article_type_fit") or {}).get("reason") or "")
    comparative_stability = dict(payload.get("comparative_stability") or {})
    if not comparative_stability:
        comparative_stability = _build_comparative_stability_from_pipeline_check(pipeline_check, article_type_fit_reason)
    return {
        "quality_metrics": quality_metrics,
        "comparative_stability": comparative_stability,
    }


def _extract_case_snapshot(case_payload: Mapping[str, Any]) -> Dict[str, Any]:
    rubric = dict(case_payload.get("rubric") or {})
    axis_scores = {
        str(key): dict(value)
        for key, value in dict(rubric.get("axis_scores") or {}).items()
    }
    result = dict(case_payload.get("result") or {})
    pipeline_check = dict(case_payload.get("pipeline_check") or result.get("pipeline_check") or {})
    quality_metrics = dict(pipeline_check.get("quality_metrics") or {})
    artifact_path = str(case_payload.get("artifact_path") or "")
    article_type_fit_reason = str(dict(axis_scores.get("article_type_fit") or {}).get("reason") or "")
    comparative_stability = dict(case_payload.get("comparative_stability") or {})
    if not comparative_stability:
        comparative_stability = _build_comparative_stability_from_pipeline_check(pipeline_check, article_type_fit_reason)
    if artifact_path and (not quality_metrics or not comparative_stability):
        artifact_projection = _load_case_artifact_projection(artifact_path)
        if not quality_metrics:
            quality_metrics = dict(artifact_projection.get("quality_metrics") or {})
        if not comparative_stability:
            comparative_stability = dict(artifact_projection.get("comparative_stability") or {})
    if not quality_metrics and artifact_path:
        quality_metrics = _load_case_quality_metrics_from_artifact(artifact_path)
    runtime_summary = dict(case_payload.get("runtime_summary") or {})
    short_gate = dict(case_payload.get("short_gate") or {})
    return {
        "case_id": str(case_payload.get("case_id") or ""),
        "artifact_path": artifact_path,
        "artifact_text_path": str(case_payload.get("artifact_text_path") or ""),
        "total_score": int(rubric.get("total_score", 0) or 0),
        "short_gate_passed": bool(short_gate.get("passed", False)),
        "fallback_used": bool(short_gate.get("fallback_used", False)),
        "short_gate_failures": list(short_gate.get("failures") or []),
        "same_model_retry_count": int(runtime_summary.get("same_model_retry_count", 0) or 0),
        "model_fallback_attempted": bool(runtime_summary.get("model_fallback_attempted", False)),
        "article_type_fit_reason": article_type_fit_reason,
        "human_visible_ai_reason": str(
            dict(axis_scores.get("human_visible_ai_feel") or {}).get("reason") or ""
        ),
        "quality_metrics": quality_metrics,
        "comparative_stability": comparative_stability,
    }


def _build_quality_metric_delta(
    neutral_metrics: Mapping[str, Any],
    preserve_metrics: Mapping[str, Any],
    metric_name: str,
) -> Dict[str, Any] | None:
    neutral_value = neutral_metrics.get(metric_name)
    preserve_value = preserve_metrics.get(metric_name)
    if neutral_value is None and preserve_value is None:
        return None
    delta = None
    if neutral_value is not None and preserve_value is not None:
        delta = round(_safe_float(preserve_value) - _safe_float(neutral_value), 4)
    return {
        "neutral": neutral_value,
        "preserve_postprocess": preserve_value,
        "delta": delta,
    }


def _build_case_difference_entry(
    case_id: str,
    neutral_case: Mapping[str, Any],
    preserve_case: Mapping[str, Any],
) -> Dict[str, Any] | None:
    score_delta = int(preserve_case.get("total_score", 0) or 0) - int(neutral_case.get("total_score", 0) or 0)
    highlights: List[str] = []
    neutral_comparative = dict(neutral_case.get("comparative_stability") or {})
    preserve_comparative = dict(preserve_case.get("comparative_stability") or {})
    comparative_case = bool(neutral_comparative.get("enabled") or preserve_comparative.get("enabled"))
    if score_delta != 0:
        highlights.append(
            f"rubric_total {neutral_case.get('total_score', 0)} -> {preserve_case.get('total_score', 0)}"
        )
    if bool(neutral_case.get("short_gate_passed", False)) != bool(preserve_case.get("short_gate_passed", False)):
        highlights.append(
            "short_gate "
            f"{bool(neutral_case.get('short_gate_passed', False))}"
            f" -> {bool(preserve_case.get('short_gate_passed', False))}"
        )
    if bool(neutral_case.get("fallback_used", False)) != bool(preserve_case.get("fallback_used", False)):
        highlights.append(
            "fallback_used "
            f"{bool(neutral_case.get('fallback_used', False))}"
            f" -> {bool(preserve_case.get('fallback_used', False))}"
        )
    if str(neutral_case.get("human_visible_ai_reason") or "") != str(preserve_case.get("human_visible_ai_reason") or ""):
        highlights.append(
            "human_visible_ai_reason "
            f"{neutral_case.get('human_visible_ai_reason', '')}"
            f" -> {preserve_case.get('human_visible_ai_reason', '')}"
        )
    if str(neutral_case.get("article_type_fit_reason") or "") != str(
        preserve_case.get("article_type_fit_reason") or ""
    ):
        highlights.append(
            "article_type_fit_reason "
            f"{neutral_case.get('article_type_fit_reason', '')}"
            f" -> {preserve_case.get('article_type_fit_reason', '')}"
        )
    if comparative_case:
        neutral_bucket = str(neutral_comparative.get("stage_bucket") or "")
        preserve_bucket = str(preserve_comparative.get("stage_bucket") or "")
        neutral_shift = neutral_comparative.get("axis_shift_count")
        preserve_shift = preserve_comparative.get("axis_shift_count")
        neutral_label = f"{neutral_bucket}({neutral_shift})" if neutral_bucket else "n/a"
        preserve_label = f"{preserve_bucket}({preserve_shift})" if preserve_bucket else "n/a"
        if (
            neutral_bucket != preserve_bucket
            or neutral_shift != preserve_shift
            or neutral_comparative.get("absolute_winner_claim_count")
            != preserve_comparative.get("absolute_winner_claim_count")
        ):
            highlights.append(f"comparative_stage {neutral_label} -> {preserve_label}")
        else:
            highlights.append(f"comparative_stage {neutral_label} maintained")

    quality_metric_deltas: Dict[str, Any] = {}
    for metric_name in COMBINED_WATCH_QUALITY_METRICS:
        delta_payload = _build_quality_metric_delta(
            dict(neutral_case.get("quality_metrics") or {}),
            dict(preserve_case.get("quality_metrics") or {}),
            metric_name,
        )
        if delta_payload is None:
            continue
        quality_metric_deltas[metric_name] = delta_payload
        if case_id in COMBINED_WATCH_CASE_IDS and delta_payload.get("delta") not in {None, 0, 0.0}:
            highlights.append(
                f"{metric_name} {delta_payload.get('neutral')} -> {delta_payload.get('preserve_postprocess')}"
            )

    if not highlights and case_id not in COMBINED_WATCH_CASE_IDS and not comparative_case:
        return None
    if not highlights:
        highlights.append("watch_case")

    return {
        "case_id": str(case_id or ""),
        "neutral_artifact_path": str(neutral_case.get("artifact_path") or ""),
        "preserve_artifact_path": str(preserve_case.get("artifact_path") or ""),
        "neutral_artifact_text_path": str(neutral_case.get("artifact_text_path") or ""),
        "preserve_artifact_text_path": str(preserve_case.get("artifact_text_path") or ""),
        "neutral_total_score": int(neutral_case.get("total_score", 0) or 0),
        "preserve_total_score": int(preserve_case.get("total_score", 0) or 0),
        "total_score_delta": score_delta,
        "neutral_short_gate_passed": bool(neutral_case.get("short_gate_passed", False)),
        "preserve_short_gate_passed": bool(preserve_case.get("short_gate_passed", False)),
        "neutral_short_gate_failures": list(neutral_case.get("short_gate_failures") or []),
        "preserve_short_gate_failures": list(preserve_case.get("short_gate_failures") or []),
        "neutral_human_visible_ai_reason": str(neutral_case.get("human_visible_ai_reason") or ""),
        "preserve_human_visible_ai_reason": str(preserve_case.get("human_visible_ai_reason") or ""),
        "neutral_article_type_fit_reason": str(neutral_case.get("article_type_fit_reason") or ""),
        "preserve_article_type_fit_reason": str(preserve_case.get("article_type_fit_reason") or ""),
        "neutral_comparative_stability": neutral_comparative,
        "preserve_comparative_stability": preserve_comparative,
        "quality_metric_deltas": quality_metric_deltas,
        "highlights": highlights,
    }


def _build_case_difference_groups(
    neutral_summary: Mapping[str, Any],
    preserve_summary: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    groups: List[Dict[str, Any]] = []
    neutral_models = {
        str(item.get("model_name") or ""): dict(item)
        for item in list(neutral_summary.get("models") or [])
    }
    preserve_models = {
        str(item.get("model_name") or ""): dict(item)
        for item in list(preserve_summary.get("models") or [])
    }

    for model_name in sorted(set(neutral_models) & set(preserve_models)):
        neutral_repeat_path = _first_short_repeat_path(neutral_models[model_name])
        preserve_repeat_path = _first_short_repeat_path(preserve_models[model_name])
        if not neutral_repeat_path or not preserve_repeat_path:
            continue
        neutral_repeat = _load_json(Path(neutral_repeat_path))
        preserve_repeat = _load_json(Path(preserve_repeat_path))
        neutral_cases = {
            str(item.get("case_id") or ""): _extract_case_snapshot(dict(item))
            for item in list(neutral_repeat.get("results") or [])
            if str(dict(item).get("case_id") or "").strip()
        }
        preserve_cases = {
            str(item.get("case_id") or ""): _extract_case_snapshot(dict(item))
            for item in list(preserve_repeat.get("results") or [])
            if str(dict(item).get("case_id") or "").strip()
        }

        case_entries: List[Dict[str, Any]] = []
        for case_id in sorted(set(neutral_cases) & set(preserve_cases)):
            entry = _build_case_difference_entry(case_id, neutral_cases[case_id], preserve_cases[case_id])
            if entry is not None:
                case_entries.append(entry)
        if not case_entries:
            continue
        case_entries.sort(
            key=lambda item: (
                0 if str(item.get("case_id") or "") in COMBINED_WATCH_CASE_IDS else 1,
                -abs(int(item.get("total_score_delta", 0) or 0)),
                str(item.get("case_id") or ""),
            )
        )
        groups.append(
            {
                "model_name": model_name,
                "repeat_index": 1,
                "neutral_repeat_path": str(neutral_repeat_path),
                "preserve_repeat_path": str(preserve_repeat_path),
                "neutral_artifact_dir": str(neutral_repeat.get("artifact_dir") or ""),
                "preserve_artifact_dir": str(preserve_repeat.get("artifact_dir") or ""),
                "cases": case_entries,
            }
        )
    return groups


def _build_lane_model_deltas(
    neutral_summary: Mapping[str, Any],
    preserve_summary: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    neutral_models = {
        str(item.get("model_name") or ""): _build_lane_model_brief(dict(item))
        for item in list(neutral_summary.get("models") or [])
    }
    preserve_models = {
        str(item.get("model_name") or ""): _build_lane_model_brief(dict(item))
        for item in list(preserve_summary.get("models") or [])
    }

    deltas: List[Dict[str, Any]] = []
    for model_name in sorted(set(neutral_models) & set(preserve_models)):
        neutral_model = neutral_models[model_name]
        preserve_model = preserve_models[model_name]
        deltas.append(
            {
                "model_name": model_name,
                "neutral": neutral_model,
                "preserve_postprocess": preserve_model,
                "delta": {
                    "short_mean": round(
                        _safe_float(preserve_model.get("short_mean"))
                        - _safe_float(neutral_model.get("short_mean")),
                        2,
                    ),
                    "short_hard_fail_total": int(
                        preserve_model.get("short_hard_fail_total", 0) or 0
                    )
                    - int(neutral_model.get("short_hard_fail_total", 0) or 0),
                    "short_retry_total": int(preserve_model.get("short_retry_total", 0) or 0)
                    - int(neutral_model.get("short_retry_total", 0) or 0),
                    "short_fallback_total": int(
                        preserve_model.get("short_fallback_total", 0) or 0
                    )
                    - int(neutral_model.get("short_fallback_total", 0) or 0),
                    "long_mean": round(
                        _safe_float(preserve_model.get("long_mean"))
                        - _safe_float(neutral_model.get("long_mean")),
                        2,
                    ),
                },
            }
        )
    return deltas


def _build_combined_verdict(
    lane_model_deltas: Sequence[Mapping[str, Any]],
    case_difference_groups: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    signals: List[str] = []
    for entry in lane_model_deltas:
        model_name = str(entry.get("model_name") or "")
        delta = dict(entry.get("delta") or {})
        short_mean_delta = round(_safe_float(delta.get("short_mean")), 2)
        if short_mean_delta != 0:
            signals.append(f"{model_name}: preserve short_mean delta={short_mean_delta:+.2f}")
        if int(delta.get("short_hard_fail_total", 0) or 0) != 0:
            signals.append(
                f"{model_name}: preserve hard_fail delta={int(delta.get('short_hard_fail_total', 0) or 0):+d}"
            )
        if int(delta.get("short_retry_total", 0) or 0) != 0:
            signals.append(
                f"{model_name}: preserve retry delta={int(delta.get('short_retry_total', 0) or 0):+d}"
            )
        if int(delta.get("short_fallback_total", 0) or 0) != 0:
            signals.append(
                f"{model_name}: preserve fallback delta={int(delta.get('short_fallback_total', 0) or 0):+d}"
            )
    for group in case_difference_groups:
        model_name = str(group.get("model_name") or "")
        for case_entry in list(group.get("cases") or []):
            case_id = str(case_entry.get("case_id") or "")
            if case_id not in COMBINED_WATCH_CASE_IDS and int(case_entry.get("total_score_delta", 0) or 0) == 0:
                continue
            signals.append(
                f"{model_name}: {case_id} highlights="
                + ", ".join(str(item) for item in list(case_entry.get("highlights") or [])[:2])
            )
            if len(signals) >= 8:
                break
        if len(signals) >= 8:
            break

    if not signals:
        summary = (
            "neutral と preserve-postprocess の headline 差は小さい。lane choice を固定せず、"
            "paired artifact review を補助情報として使う状態です。"
        )
    else:
        summary = (
            "neutral と preserve-postprocess は一部 case と retry/hard-fail で差が出る。"
            "combined summary は observe-only で、lane 採否は artifact を見て人手で判断する前提です。"
        )
    return {
        "observe_only": True,
        "summary": summary,
        "signals": signals,
    }


def _build_combined_lane_summary(
    neutral_summary: Mapping[str, Any],
    preserve_summary: Mapping[str, Any],
) -> Dict[str, Any]:
    lane_model_deltas = _build_lane_model_deltas(neutral_summary, preserve_summary)
    case_difference_groups = _build_case_difference_groups(neutral_summary, preserve_summary)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary_type": COMBINED_SUMMARY_SCHEMA_VERSION,
        "observe_only": True,
        "reasoning_effort": str(neutral_summary.get("reasoning_effort") or ""),
        "compare_verbosity": str(neutral_summary.get("compare_verbosity") or ""),
        "matched_runtime": bool(neutral_summary.get("matched_runtime", False)),
        "short_repeats": int(neutral_summary.get("short_repeats", 0) or 0),
        "long_repeats": int(neutral_summary.get("long_repeats", 0) or 0),
        "sentinel_case_ids": list(neutral_summary.get("sentinel_case_ids") or []),
        "neutral_summary_path": str(neutral_summary.get("saved_to") or ""),
        "preserve_summary_path": str(preserve_summary.get("saved_to") or ""),
        "lanes": {
            "neutral": _build_lane_brief(neutral_summary),
            "preserve_postprocess": _build_lane_brief(preserve_summary),
        },
        "lane_model_deltas": lane_model_deltas,
        "case_level_differences": case_difference_groups,
        "verdict": _build_combined_verdict(lane_model_deltas, case_difference_groups),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run current mainline model compare with matched config overrides.")
    parser.add_argument("--model", dest="models", action="append", help="Section model to compare. Repeatable.")
    parser.add_argument("--short-repeats", type=int, default=5)
    parser.add_argument("--long-repeats", type=int, default=2)
    parser.add_argument("--reasoning-effort", type=str, default="low")
    parser.add_argument("--compare-verbosity", type=str, default=DEFAULT_COMPARE_VERBOSITY)
    parser.add_argument("--sentinel-case-id", dest="sentinel_case_ids", action="append", default=[])
    parser.add_argument("--matched-runtime", dest="matched_runtime", action="store_true", default=True)
    parser.add_argument("--raw-runtime", dest="matched_runtime", action="store_false")
    parser.add_argument(
        "--postprocess-neutral",
        dest="postprocess_neutral",
        action="store_true",
        default=DEFAULT_POSTPROCESS_NEUTRAL,
    )
    parser.add_argument("--preserve-postprocess", dest="postprocess_neutral", action="store_false")
    parser.add_argument("--short-timeout-sec", type=int, default=900)
    parser.add_argument("--long-timeout-sec", type=int, default=1200)
    parser.add_argument(
        "--dual-lane",
        action="store_true",
        help="Run neutral and preserve-postprocess lanes together and write a combined observe-only summary.",
    )
    parser.add_argument("--output", type=str, default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    models = list(args.models or DEFAULT_MODELS)
    sentinel_case_ids = list(args.sentinel_case_ids or DEFAULT_SENTINEL_CASE_IDS)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_root = PROJECT_ROOT / "logs" / "current_mainline_model_compare" / timestamp
    output_path = Path(args.output) if args.output else (
        run_root / "combined_summary.json" if args.dual_lane else run_root / "summary.json"
    )
    base_config = _load_json(BASE_CONFIG_PATH)

    if args.dual_lane:
        neutral_summary = _build_compare_summary(
            base_config=base_config,
            models=models,
            reasoning_effort=str(args.reasoning_effort or ""),
            compare_verbosity=str(args.compare_verbosity or ""),
            matched_runtime=bool(args.matched_runtime),
            postprocess_neutral=True,
            short_repeats=int(args.short_repeats),
            long_repeats=int(args.long_repeats),
            sentinel_case_ids=sentinel_case_ids,
            short_timeout_sec=int(args.short_timeout_sec),
            long_timeout_sec=int(args.long_timeout_sec),
            run_root=run_root / "neutral",
            output_path=run_root / "neutral" / "summary.json",
        )
        preserve_summary = _build_compare_summary(
            base_config=base_config,
            models=models,
            reasoning_effort=str(args.reasoning_effort or ""),
            compare_verbosity=str(args.compare_verbosity or ""),
            matched_runtime=bool(args.matched_runtime),
            postprocess_neutral=False,
            short_repeats=int(args.short_repeats),
            long_repeats=int(args.long_repeats),
            sentinel_case_ids=sentinel_case_ids,
            short_timeout_sec=int(args.short_timeout_sec),
            long_timeout_sec=int(args.long_timeout_sec),
            run_root=run_root / "preserve_postprocess",
            output_path=run_root / "preserve_postprocess" / "summary.json",
        )
        combined_summary = _build_combined_lane_summary(neutral_summary, preserve_summary)
        _write_json(output_path, combined_summary)
        combined_summary["saved_to"] = str(output_path)
        if args.json:
            print(json.dumps(combined_summary, ensure_ascii=False, indent=2))
        else:
            print(f"saved_to={output_path}")
            print(f"neutral_summary_path={combined_summary.get('neutral_summary_path')}")
            print(f"preserve_summary_path={combined_summary.get('preserve_summary_path')}")
            for entry in list(combined_summary.get("lane_model_deltas") or []):
                delta = dict(entry.get("delta") or {})
                neutral = dict(entry.get("neutral") or {})
                preserve = dict(entry.get("preserve_postprocess") or {})
                print(
                    f"{entry.get('model_name')}:"
                    f" neutral_short_mean={neutral.get('short_mean')}"
                    f" preserve_short_mean={preserve.get('short_mean')}"
                    f" short_mean_delta={delta.get('short_mean'):+.2f}"
                    f" preserve_hard_fail_delta={int(delta.get('short_hard_fail_total', 0) or 0):+d}"
                    f" preserve_retry_delta={int(delta.get('short_retry_total', 0) or 0):+d}"
                )
            verdict = dict(combined_summary.get("verdict") or {})
            print("verdict=" + str(verdict.get("summary") or ""))
        return 0

    summary = _build_compare_summary(
        base_config=base_config,
        models=models,
        reasoning_effort=str(args.reasoning_effort or ""),
        compare_verbosity=str(args.compare_verbosity or ""),
        matched_runtime=bool(args.matched_runtime),
        postprocess_neutral=bool(args.postprocess_neutral),
        short_repeats=int(args.short_repeats),
        long_repeats=int(args.long_repeats),
        sentinel_case_ids=sentinel_case_ids,
        short_timeout_sec=int(args.short_timeout_sec),
        long_timeout_sec=int(args.long_timeout_sec),
        run_root=run_root,
        output_path=output_path,
    )

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"saved_to={output_path}")
        for item in list(summary.get("models") or []):
            short_aggregate = dict(item.get("short_aggregate") or {})
            long_aggregate = dict(item.get("long_aggregate") or {})
            print(
                f"{item['model_name']}:"
                f" short_mean={short_aggregate.get('rubric_mean_total_mean')}"
                f" short_hard_fail_total={short_aggregate.get('hard_fail_case_total')}"
                f" long_mean={long_aggregate.get('rubric_mean_total_mean')}"
                f" long_blocked={long_aggregate.get('blocked_count')}"
            )
        print(f"postprocess_neutral={bool(summary.get('postprocess_neutral', False))}")
        comparison = dict(summary.get("comparison") or {})
        print(
            "material_difference_detected="
            f"{bool(comparison.get('material_difference_detected', False))}"
        )
        if comparison.get("reasons"):
            print("comparison_reasons=" + " | ".join(str(item) for item in list(comparison.get("reasons") or [])))
        if comparison.get("preferred_primary_model"):
            print(f"preferred_primary_model={comparison.get('preferred_primary_model')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
