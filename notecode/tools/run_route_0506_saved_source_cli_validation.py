from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from note.route_0506_security_gate import (  # noqa: E402
    evaluate_route_0506_security_gate,
    validate_source_card_schema_compatibility,
)
from note.route_0506_structured_blog_adapter import (  # noqa: E402
    DEFAULT_0506_ROOT,
    OPENAI_GENERATION_CANDIDATE,
    ROUTE_0506_ID,
    Route0506AdapterError,
    extract_route_0506_source_records,
    resolve_route_0506_client_mode,
    resolve_route_0506_genre,
    route_0506_source_snapshot,
    run_route_0506_local_scaffold,
)
from note.route_0506_structured_blog_result_adapter import (  # noqa: E402
    build_route_0506_blocked_result,
    write_route_0506_result_artifacts,
)
from note.route_0506_usage_ledger import (  # noqa: E402
    append_usage_ledger_row,
    build_not_sent_usage_row,
)


LATEST_ROUTE_A_JSON = PROJECT_ROOT / "logs" / "latest_generation_output.json"
LATEST_ROUTE_A_TXT = PROJECT_ROOT / "logs" / "latest_generation_output.txt"
LATEST_ROUTE_A_QUALITY = PROJECT_ROOT / "logs" / "latest_generation_quality_report.json"


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _write_json(path: Path, payload: Mapping[str, Any] | list[Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _format_route_a_text(saved_route_a: Mapping[str, Any]) -> str:
    if LATEST_ROUTE_A_TXT.exists():
        return LATEST_ROUTE_A_TXT.read_text(encoding="utf-8")
    parts = [
        str(saved_route_a.get("title") or "").strip(),
        "",
        str(saved_route_a.get("lead") or "").strip(),
        "",
        str(saved_route_a.get("body") or saved_route_a.get("full_text") or "").strip(),
        "",
        str(saved_route_a.get("references") or "").strip(),
        "",
        str(saved_route_a.get("hashtags") or "").strip(),
    ]
    return "\n".join(part for part in parts if part is not None).strip() + "\n"


def _safe_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    text = re.sub(r"sk-[A-Za-z0-9_-]{8,}", "[REDACTED_OPENAI_KEY]", text)
    text = re.sub(r"OPENAI_API_KEY\s*=\s*[^\s]+", "OPENAI_API_KEY=[REDACTED]", text, flags=re.IGNORECASE)
    return text[:1200]


def _build_schema_preflight_report(source_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    for source_index, source in enumerate(source_snapshot.get("sources") or []):
        if not isinstance(source, Mapping):
            continue
        payload = {
            "facts": [
                {
                    "fact_id": f"F{source_index + 1:03d}",
                    "claim": str(source.get("content") or "")[:120] or "source claim",
                    "importance": 5,
                }
            ]
        }
        report = validate_source_card_schema_compatibility(payload)
        if report.get("status") != "pass":
            errors.extend(list(report.get("errors") or []))
    return {
        "status": "pass" if not errors else "fail",
        "stage": "source_card_extraction",
        "checked": True,
        "fact_id_format": "F001",
        "importance_range": "1-5",
        "errors": errors,
    }


def _copy_route_a_artifacts(output_root: Path, saved_route_a: Mapping[str, Any]) -> dict[str, str]:
    route_a_dir = output_root / "route_a_saved"
    route_a_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LATEST_ROUTE_A_JSON, route_a_dir / "latest_generation_output.json")
    _write_text(route_a_dir / "latest_generation_output.txt", _format_route_a_text(saved_route_a))
    copied = {
        "latest_generation_output_json": str(route_a_dir / "latest_generation_output.json"),
        "latest_generation_output_txt": str(route_a_dir / "latest_generation_output.txt"),
    }
    if LATEST_ROUTE_A_QUALITY.exists():
        shutil.copy2(LATEST_ROUTE_A_QUALITY, route_a_dir / "latest_generation_quality_report.json")
        copied["latest_generation_quality_report_json"] = str(route_a_dir / "latest_generation_quality_report.json")
    return copied


def _write_usage_ledgers(output_root: Path, row: Mapping[str, Any]) -> dict[str, Any]:
    usage_ledger = output_root / "usage_ledger.jsonl"
    api_usage_ledger = output_root / "api_usage_ledger.jsonl"
    normalized = append_usage_ledger_row(usage_ledger, row)
    append_usage_ledger_row(api_usage_ledger, normalized)
    return normalized


def _build_validation_usage_row(
    *,
    output_root: Path,
    api_send_requested: bool,
    blocked_reason: str,
) -> dict[str, Any]:
    if api_send_requested and not blocked_reason:
        return {
            "stage": "window_3_saved_source_cli_validation",
            "artifact_root": str(output_root),
            "status": "requested_unmetered",
            "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
            "reasoning_effort": os.getenv("OPENAI_REASONING_EFFORT", "high"),
            "actual_usage_available": False,
        }
    return build_not_sent_usage_row(
        stage="window_3_saved_source_cli_validation",
        artifact_root=output_root,
        blocked_reason=blocked_reason or "api_send_not_required_local_validation",
    )


def _manual_notes(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Route 0506 Saved-Source CLI Manual Review Notes",
            "",
            f"- phase/window: {summary.get('phase_window')}",
            f"- route_0506_status: {summary.get('route_0506_status')}",
            f"- selected_route_a_artifact: {summary.get('selected_route_a_artifact')}",
            f"- semantic_article_key: {summary.get('semantic_article_key')}",
            f"- article_type: {summary.get('article_type')}",
            f"- genre_id: {summary.get('genre_id')}",
            f"- source_snapshot_hash: {summary.get('source_snapshot_hash')}",
            f"- security_gate_status: {summary.get('security_gate_status')}",
            f"- schema_compatibility_status: {summary.get('schema_compatibility_status')}",
            "- japanese_blog_naturalness_note: TBD",
            "- source_faithfulness_note: TBD",
            "- first_person_consistency_note: TBD",
        ]
    ).strip() + "\n"


def run_validation(
    output_root: Path,
    *,
    route_root: Path = DEFAULT_0506_ROOT,
    route_a_json: Path = LATEST_ROUTE_A_JSON,
    approved_root: Path | None = None,
    client_mode: str | None = None,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    resolved_client_mode = resolve_route_0506_client_mode(client_mode)
    api_send_requested = resolved_client_mode == OPENAI_GENERATION_CANDIDATE
    before_route_a_hash = _sha256_file(route_a_json)
    saved_route_a = _load_json(route_a_json)
    input_contract = dict(saved_route_a.get("input_contract") or {})
    article_type = str(input_contract.get("article_type") or saved_route_a.get("article_type") or "")
    semantic_article_key = str(
        input_contract.get("semantic_article_key") or saved_route_a.get("semantic_article_key") or ""
    )
    body = str(saved_route_a.get("body") or saved_route_a.get("full_text") or "")

    _copy_route_a_artifacts(output_root, saved_route_a)
    _write_json(output_root / "input_contract.json", input_contract)

    blocked_reason = ""
    source_snapshot: dict[str, Any] = {}
    schema_report: dict[str, Any] = {"status": "not_checked", "checked": False}
    approved = approved_root or (PROJECT_ROOT / "logs")
    security_gate = evaluate_route_0506_security_gate(input_contract, artifact_root=output_root, approved_root=approved)

    if article_type == "announcement" or semantic_article_key == "announcement":
        blocked_reason = "announcement_out_of_scope"
    elif not body.strip():
        blocked_reason = "route_a_saved_body_empty"
    else:
        try:
            records = extract_route_0506_source_records(input_contract)
            source_snapshot = route_0506_source_snapshot(records)
            schema_report = _build_schema_preflight_report(source_snapshot)
            security_gate = evaluate_route_0506_security_gate(
                input_contract,
                artifact_root=output_root,
                approved_root=approved,
                schema_report=schema_report,
            )
            if security_gate.get("decision") != "pass":
                blocked_reason = ",".join(security_gate.get("blocked_reasons") or [])
        except Exception as exc:
            blocked_reason = _safe_error(exc)

    _write_json(output_root / "source_snapshot.json", source_snapshot)
    _write_json(output_root / "schema_compatibility_report.json", schema_report)
    _write_json(output_root / "security_gate.json", security_gate)
    _write_json(output_root / "security_gate_report.json", security_gate)

    preflight_summary = {
        "phase_window": "Window 3 saved-source CLI validation only",
        "status": "blocked" if blocked_reason else "preflight_ready",
        "selected_route_a_artifact": str(route_a_json),
        "route_a_regenerated": False,
        "route_a_changed": False,
        "ui_changed": False,
        "api_send": api_send_requested,
        "client_mode": resolved_client_mode,
        "url_refetch": False,
        "local_file_fallback": False,
        "route_a_fallback_used": False,
        "old_rejected_routes_used": False,
        "semantic_article_key": semantic_article_key,
        "article_type": article_type,
        "genre_id": resolve_route_0506_genre(input_contract) if input_contract else "",
        "source_snapshot_hash": source_snapshot.get("canonical_hash", ""),
        "schema_compatibility_status": schema_report.get("status", "not_checked"),
        "security_gate_status": security_gate.get("decision", "blocked"),
        "blocked_reason": blocked_reason,
    }
    _write_json(output_root / "preflight_summary.json", preflight_summary)

    usage_row = _write_usage_ledgers(
        output_root,
        _build_validation_usage_row(
            output_root=output_root,
            api_send_requested=api_send_requested,
            blocked_reason=blocked_reason,
        ),
    )

    if blocked_reason:
        result = build_route_0506_blocked_result(
            input_contract=input_contract,
            artifact_root=output_root,
            reason_code="ROUTE_0506_SAVED_SOURCE_VALIDATION_BLOCKED",
            blocked_reason=blocked_reason,
            security_gate=security_gate,
            schema_report=schema_report,
        )
        write_route_0506_result_artifacts(
            output_root,
            result,
            input_contract=input_contract,
            source_snapshot=source_snapshot,
            security_gate=security_gate,
        )
    else:
        try:
            result = run_route_0506_local_scaffold(
                input_contract,
                artifact_root=output_root,
                route_root=route_root,
                run_id="route_0506_saved_source_cli_validation",
                client_mode=resolved_client_mode,
            )
        except Exception as exc:
            blocked_reason = _safe_error(exc)
            result = build_route_0506_blocked_result(
                input_contract=input_contract,
                artifact_root=output_root,
                reason_code="ROUTE_0506_LOCAL_SCAFFOLD_FAILED",
                blocked_reason=blocked_reason,
                security_gate=security_gate,
                schema_report=schema_report,
            )
            write_route_0506_result_artifacts(
                output_root,
                result,
                input_contract=input_contract,
                source_snapshot=source_snapshot,
                security_gate=security_gate,
            )

    after_route_a_hash = _sha256_file(route_a_json)
    body_char_count = len(str(result.get("body") or result.get("full_text") or ""))
    route_status = "blocked" if result.get("blocked") else "completed"
    validation_summary = {
        **preflight_summary,
        "status": "completed" if route_status == "completed" else "blocked",
        "route_0506_status": route_status,
        "body_char_count": body_char_count if route_status == "completed" else 0,
        "actual_api_call_count": 1 if api_send_requested and route_status == "completed" else 0,
        "estimated_cost_usd": 0.0,
        "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini") if api_send_requested else "",
        "reasoning_effort": os.getenv("OPENAI_REASONING_EFFORT", "high") if api_send_requested else "",
        "threshold_relaxed": False,
        "repair_acceptance_relaxed": False,
        "prompt_added_for_quality_tuning": False,
        "source_outside_claim_risk": "manual_review_required" if route_status == "completed" else "not_checked",
        "first_person_consistency": "manual_review_required" if route_status == "completed" else "not_checked",
        "mapping": {
            "semantic_article_key": semantic_article_key,
            "article_type": article_type,
            "ui_journey": input_contract.get("ui_journey") if isinstance(input_contract, Mapping) else {},
            "genre_id": preflight_summary["genre_id"],
        },
        "route_a_saved_artifact_sha256_before": before_route_a_hash,
        "route_a_saved_artifact_sha256_after": after_route_a_hash,
        "route_a_changed": before_route_a_hash != after_route_a_hash,
        "usage_ledger_row": usage_row,
        "artifact_completeness_status": "pending",
    }
    _write_text(output_root / "manual_review_notes.md", _manual_notes(validation_summary))
    required_artifacts = [
        output_root / "source_snapshot.json",
        output_root / "input_contract.json",
        output_root / "route_a_saved" / "latest_generation_output.json",
        output_root / "route_a_saved" / "latest_generation_output.txt",
        output_root / "preflight_summary.json",
        output_root / "security_gate_report.json",
        output_root / "api_usage_ledger.jsonl",
        output_root / "usage_ledger.jsonl",
        output_root / "route_0506" / "latest_generation_output.json",
        output_root / "route_0506" / "latest_generation_output.md",
        output_root / "route_0506" / "latest_generation_quality_report.json",
        output_root / "validation_summary.json",
        output_root / "manual_review_notes.md",
    ]
    if route_status == "blocked":
        required_artifacts.append(output_root / "blocked.json")
    validation_summary["artifact_completeness_status"] = (
        "complete" if all(path.exists() for path in required_artifacts if path.name != "validation_summary.json") else "incomplete"
    )
    _write_json(output_root / "validation_summary.json", validation_summary)
    return validation_summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="")
    parser.add_argument("--route-root", default=str(DEFAULT_0506_ROOT))
    parser.add_argument("--route-a-json", default=str(LATEST_ROUTE_A_JSON))
    parser.add_argument("--route-0506-client-mode", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    output_root = (
        Path(args.output_root)
        if args.output_root
        else PROJECT_ROOT / "logs" / f"route_0506_saved_source_cli_validation_{_now_stamp()}"
    )
    summary = run_validation(
        output_root,
        route_root=Path(args.route_root),
        route_a_json=Path(args.route_a_json),
        client_mode=args.route_0506_client_mode or None,
    )
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"wrote {output_root}")
    return 0 if summary.get("route_0506_status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
