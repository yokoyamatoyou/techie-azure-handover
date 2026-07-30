"""Result artifact adapter for route_0506_structured_blog_ui_v1."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from note.route_0506_usage_ledger import ROUTE_0506_ID, redact_secret_like_text


def build_route_0506_visible_result(
    pipeline_result: Mapping[str, Any],
    *,
    input_contract: Mapping[str, Any],
    artifact_root: Path | str,
) -> dict[str, Any]:
    body = str(pipeline_result.get("final_article") or pipeline_result.get("body") or "")
    parsed = _extract_title_lead(body)
    quality_report = dict(pipeline_result.get("quality_check") or {})
    return {
        "route_id": ROUTE_0506_ID,
        "blocked": False,
        "reason_code": "",
        "article_type": str(input_contract.get("article_type") or ""),
        "semantic_article_key": str(input_contract.get("semantic_article_key") or ""),
        "ui_journey": dict(input_contract.get("ui_journey") or {}),
        "genre_id": str(pipeline_result.get("genre_id") or ""),
        "title": str(pipeline_result.get("title") or parsed["title"]),
        "lead": str(pipeline_result.get("lead") or parsed["lead"]),
        "body": body,
        "full_text": body,
        "quality_report": quality_report,
        "source_snapshot_hash": str(pipeline_result.get("source_snapshot_hash") or ""),
        "usage_summary": dict(pipeline_result.get("usage_summary") or {"api_send": False}),
        "client_mode": str(pipeline_result.get("client_mode") or ""),
        "artifact_root": str(artifact_root),
    }


def build_route_0506_blocked_result(
    *,
    input_contract: Mapping[str, Any],
    artifact_root: Path | str,
    reason_code: str,
    blocked_reason: str,
    security_gate: Mapping[str, Any] | None = None,
    schema_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    reason = redact_secret_like_text(blocked_reason)
    return {
        "route_id": ROUTE_0506_ID,
        "blocked": True,
        "reason_code": str(reason_code or "ROUTE_0506_BLOCKED"),
        "blocked_reason_redacted": reason,
        "article_type": str(input_contract.get("article_type") or ""),
        "semantic_article_key": str(input_contract.get("semantic_article_key") or ""),
        "ui_journey": dict(input_contract.get("ui_journey") or {}),
        "body": "",
        "full_text": "",
        "quality_report": {
            "route_id": ROUTE_0506_ID,
            "blocked": True,
            "reason_code": str(reason_code or "ROUTE_0506_BLOCKED"),
            "schema_report": dict(schema_report or {}),
        },
        "security_gate": dict(security_gate or {}),
        "usage_summary": {"api_send": False, "status": "not_sent"},
        "artifact_root": str(artifact_root),
    }


def write_route_0506_result_artifacts(
    artifact_root: Path | str,
    result: Mapping[str, Any],
    *,
    input_contract: Mapping[str, Any],
    source_snapshot: Mapping[str, Any] | None = None,
    security_gate: Mapping[str, Any] | None = None,
) -> dict[str, Path]:
    root = Path(artifact_root)
    route_dir = root / "route_0506"
    route_dir.mkdir(parents=True, exist_ok=True)
    written = {
        "input_contract": root / "input_contract.json",
        "source_snapshot": root / "source_snapshot.json",
        "latest_generation_output_json": route_dir / "latest_generation_output.json",
        "latest_generation_output_md": route_dir / "latest_generation_output.md",
        "latest_generation_output_txt": route_dir / "latest_generation_output.txt",
        "latest_generation_quality_report": route_dir / "latest_generation_quality_report.json",
        "route_mapping": route_dir / "route_mapping.json",
    }
    _write_json(written["input_contract"], dict(input_contract))
    _write_json(written["source_snapshot"], dict(source_snapshot or {}))
    _write_json(written["latest_generation_output_json"], dict(result))
    body = str(result.get("full_text") or result.get("body") or "")
    written["latest_generation_output_md"].write_text(body, encoding="utf-8")
    written["latest_generation_output_txt"].write_text(body, encoding="utf-8")
    _write_json(written["latest_generation_quality_report"], dict(result.get("quality_report") or {}))
    _write_json(
        written["route_mapping"],
        {
            "route_id": ROUTE_0506_ID,
            "article_type": str(input_contract.get("article_type") or ""),
            "semantic_article_key": str(input_contract.get("semantic_article_key") or ""),
            "ui_journey": dict(input_contract.get("ui_journey") or {}),
            "genre_id": str(result.get("genre_id") or ""),
        },
    )
    if result.get("blocked"):
        blocked_path = root / "blocked.json"
        _write_json(blocked_path, dict(result))
        written["blocked"] = blocked_path
    if security_gate is not None:
        security_path = root / "security_gate.json"
        _write_json(security_path, dict(security_gate))
        written["security_gate"] = security_path
    return written


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _extract_title_lead(markdown_text: str) -> dict[str, str]:
    lines = [line.strip() for line in str(markdown_text or "").splitlines()]
    title = ""
    lead_parts: list[str] = []
    for line in lines:
        if not line:
            if lead_parts:
                break
            continue
        if not title and line.startswith("#"):
            title = line.lstrip("#").strip()
            continue
        if line.startswith("#"):
            if lead_parts:
                break
            continue
        if not lead_parts:
            lead_parts.append(line)
        elif len("".join(lead_parts)) < 180:
            lead_parts.append(line)
        else:
            break
    return {"title": title, "lead": "\n".join(lead_parts).strip()}
