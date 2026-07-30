from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from note.route_v_0506_adapter import (  # noqa: E402
    DEFAULT_ROUTE_V_0506_ROOT,
    ROUTE_V_0506_ROUTE_ID,
    RouteV0506Error,
    extract_route_v_source_records,
    inspect_route_v_0506_workspace,
    route_v_source_snapshot_hash,
    run_route_v_0506_candidate,
)


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _write_json(path: Path, payload: Mapping[str, Any] | list[Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _safe_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    text = re.sub(r"sk-[A-Za-z0-9_-]{8,}", "[REDACTED_OPENAI_KEY]", text)
    return text[:1200]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_fixture(name: str) -> dict[str, Any]:
    candidates = (
        PROJECT_ROOT / "note" / "tests" / "fixtures" / "vnext_materialization" / name,
        PROJECT_ROOT
        / "archive"
        / "route_experiments_rejected_2026-05-08"
        / "note"
        / "tests"
        / "fixtures"
        / "vnext_materialization"
        / name,
    )
    for path in candidates:
        if path.exists():
            return _load_json(path)
    raise FileNotFoundError(str(candidates[0]))


def _load_source_mode(source_mode: str) -> tuple[dict[str, Any], dict[str, Any] | None, str]:
    mode = str(source_mode or "").strip()
    if mode == "latest-ui-saved":
        latest = _load_json(PROJECT_ROOT / "logs" / "latest_generation_output.json")
        contract = dict(latest.get("input_contract") or {})
        if not contract:
            raise ValueError("latest_generation_output.json has no input_contract")
        return contract, latest, "saved_latest_ui"
    if mode == "fixture-company":
        payload = _load_fixture("company_introduction.json")
        return {
            **payload,
            "article_type": "branding",
            "semantic_article_key": "company_introduction",
            "prompt_raw": payload.get("topic_statement", ""),
            "length_mode": "adaptive",
        }, None, "fixture_company_introduction_v1"
    if mode == "fixture-product":
        payload = _load_fixture("product_introduction.json")
        return {
            **payload,
            "article_type": "branding",
            "semantic_article_key": "product_introduction",
            "prompt_raw": payload.get("topic_statement", ""),
            "length_mode": "adaptive",
        }, None, "fixture_product_introduction_v1"
    raise ValueError(
        "unsupported source_mode: "
        f"{mode}; valid values: latest-ui-saved, fixture-company, fixture-product"
    )


def _format_saved_baseline_text(result: Mapping[str, Any]) -> str:
    parts = [
        str(result.get("title") or "").strip(),
        "",
        str(result.get("lead") or "").strip(),
        "",
        str(result.get("body") or "").strip(),
        "",
        str(result.get("references") or "").strip(),
        "",
        str(result.get("hashtags") or "").strip(),
    ]
    return "\n".join(part for part in parts if part is not None).strip() + "\n"


def _saved_baseline_summary(result: Mapping[str, Any] | None) -> dict[str, Any]:
    if result is None:
        return {
            "executed": False,
            "source": "not_run",
            "reason": "Retired legacy generation is intentionally not run in local Route V preflight",
        }
    body = str(result.get("body") or "")
    full_text = str(result.get("full_text") or "")
    return {
        "executed": False,
        "source": "saved_latest_generation_output",
        "attempt_id": str(result.get("attempt_id") or ""),
        "runtime_reason_code": str(result.get("runtime_reason_code") or result.get("reason_code") or ""),
        "blocked_or_review_required": bool(result.get("runtime_reason_code")),
        "title": str(result.get("title") or ""),
        "body_char_count": len(body),
        "full_text_char_count": len(full_text),
        "semantic_article_key": str(result.get("semantic_article_key") or ""),
    }


def _route_v_summary(result: Mapping[str, Any] | None, error: str = "") -> dict[str, Any]:
    if result is None:
        return {
            "executed": False,
            "route_id": ROUTE_V_0506_ROUTE_ID,
            "blocked": True,
            "blocked_reason": error,
        }
    quality = dict(result.get("quality_check") or {})
    quality_check = dict(quality.get("quality_check") or quality)
    final_article = str(result.get("final_article") or "")
    return {
        "executed": True,
        "route_id": str(result.get("route_id") or ROUTE_V_0506_ROUTE_ID),
        "blocked": False,
        "external_llm_send": bool(result.get("external_llm_send")),
        "genre_id": str(result.get("genre_id") or ""),
        "artifact_dir": str(result.get("artifact_dir") or ""),
        "final_article_char_count": len(final_article),
        "quality_pass": bool(quality_check.get("pass", False)),
        "quality_score": quality_check.get("score"),
        "issue_count": len(list(quality_check.get("issues") or [])),
    }


def run_compare(
    output_root: Path,
    *,
    route_v_root: Path = DEFAULT_ROUTE_V_0506_ROOT,
    source_mode: str = "latest-ui-saved",
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    workspace_report = inspect_route_v_0506_workspace(route_v_root)
    try:
        input_contract, saved_baseline, source_set_id = _load_source_mode(source_mode)
        records = extract_route_v_source_records(input_contract)
        if not records:
            raise RouteV0506Error("selected_source_mode_has_no_source_documents_with_content")
        source_snapshot = [
            {
                "title": record.title,
                "content": record.content,
                "locator": record.locator,
                "source_type": record.source_type,
            }
            for record in records
        ]
        _write_json(output_root / "source_snapshot.json", source_snapshot)
        if saved_baseline is not None:
            baseline_dir = output_root / "baseline_current_saved"
            _write_json(baseline_dir / "latest_generation_output.json", saved_baseline)
            _write_text(baseline_dir / "latest_generation_output.txt", _format_saved_baseline_text(saved_baseline))

        route_v_result = run_route_v_0506_candidate(
            input_contract,
            route_v_root=route_v_root,
            artifacts_dir=output_root / "route_v_0506_artifacts",
            run_id="route_v_0506",
        )
        route_v_dir = output_root / "route_v_0506"
        _write_json(route_v_dir / "latest_generation_output.json", route_v_result)
        _write_text(route_v_dir / "latest_generation_output.md", str(route_v_result.get("final_article") or ""))
        _write_json(route_v_dir / "latest_generation_quality_report.json", dict(route_v_result.get("quality_check") or {}))
        route_v_error = ""
    except Exception as exc:
        route_v_result = None
        route_v_error = _safe_error(exc)

    route_v_status = _route_v_summary(route_v_result, route_v_error)
    status = "preflight_ready" if route_v_result is not None else "blocked"
    decision = "continue_shadow" if route_v_result is not None else "blocked"
    summary = {
        "run_id": output_root.name,
        "status": status,
        "mode": "route_v_0506_local_preflight",
        "source_mode": source_mode,
        "source_set_id": source_set_id if "source_set_id" in locals() else "",
        "source_snapshot_hash": route_v_source_snapshot_hash(records) if "records" in locals() else "",
        "saved_baseline": _saved_baseline_summary(saved_baseline if "saved_baseline" in locals() else None),
        "route_v": route_v_status,
        "workspace_report": workspace_report,
        "guardrails": {
            "current_default_route_changed": False,
            "legacy_runtime_touched": False,
            "legacy_fallback_used": False,
            "external_llm_send": False,
            "threshold_relaxed": False,
            "repair_acceptance_relaxed": False,
        },
        "decision": decision,
        "next_required_step": (
            "manual_read_route_v_output_then_request_1case_live_compare_approval"
            if route_v_result is not None
            else "fix_blocker_before_live_compare"
        ),
    }
    _write_json(output_root / "compare_summary.json", summary)
    _write_text(output_root / "manual_ab_notes.md", _manual_notes(summary))
    if route_v_result is None:
        _write_json(output_root / "blocked.json", {"blocked_reason": route_v_error, "workspace_report": workspace_report})
    return summary


def _manual_notes(summary: Mapping[str, Any]) -> str:
    route_v = dict(summary.get("route_v") or {})
    saved_baseline = dict(summary.get("saved_baseline") or {})
    lines = [
        "# Route V 0506 Manual Notes",
        "",
        f"- status: {summary.get('status')}",
        f"- decision: {summary.get('decision')}",
        "- external_llm_send: false",
        "- current_default_route_changed: false",
        "- legacy_fallback_used: false",
        "",
        "## Saved Baseline",
        "",
        f"- source: {saved_baseline.get('source')}",
        f"- runtime_reason_code: {saved_baseline.get('runtime_reason_code', '')}",
        f"- body_char_count: {saved_baseline.get('body_char_count', '')}",
        "",
        "## Route V 0506",
        "",
        f"- executed: {route_v.get('executed')}",
        f"- genre_id: {route_v.get('genre_id', '')}",
        f"- artifact_dir: {route_v.get('artifact_dir', '')}",
        f"- final_article_char_count: {route_v.get('final_article_char_count', '')}",
        f"- quality_pass: {route_v.get('quality_pass', '')}",
        f"- quality_score: {route_v.get('quality_score', '')}",
        "",
        "## Human Review",
        "",
        "- preferred: TBD",
        "- naturalness_note: TBD",
        "- source_faithfulness_note: TBD",
    ]
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route-v-root", default=str(DEFAULT_ROUTE_V_0506_ROOT))
    parser.add_argument("--source-mode", default="latest-ui-saved")
    parser.add_argument("--output-root", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    output_root = Path(args.output_root) if args.output_root else PROJECT_ROOT / "logs" / f"route_v_0506_compare_{_now_stamp()}"
    summary = run_compare(
        output_root,
        route_v_root=Path(args.route_v_root),
        source_mode=args.source_mode,
    )
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {output_root}")
    return 0 if summary.get("status") == "preflight_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
