"""Usage ledger scaffold for route_0506_structured_blog_ui_v1."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ROUTE_0506_ID = "route_0506_structured_blog_ui_v1"

_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"OPENAI_API_KEY\s*=\s*[^\s]+", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*[:=]\s*[^\s]+", re.IGNORECASE),
)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_secret_like_text(value: Any) -> str:
    text = str(value or "")
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED_SECRET]", text)
    return text


def normalize_usage_row(row: Mapping[str, Any]) -> dict[str, Any]:
    normalized = {
        "timestamp": str(row.get("timestamp") or utc_timestamp()),
        "route_id": str(row.get("route_id") or ROUTE_0506_ID),
        "stage": str(row.get("stage") or "unknown"),
        "model": str(row.get("model") or ""),
        "reasoning_effort": str(row.get("reasoning_effort") or ""),
        "input_tokens": int(row.get("input_tokens") or 0),
        "cached_input_tokens": int(row.get("cached_input_tokens") or 0),
        "output_tokens": int(row.get("output_tokens") or 0),
        "total_tokens": int(row.get("total_tokens") or 0),
        "estimated_cost_usd": float(row.get("estimated_cost_usd") or 0.0),
        "actual_usage_available": bool(row.get("actual_usage_available")),
        "status": str(row.get("status") or "not_sent"),
        "blocked_reason_redacted": redact_secret_like_text(row.get("blocked_reason_redacted") or ""),
        "artifact_root": str(row.get("artifact_root") or ""),
    }
    return normalized


def build_not_sent_usage_row(
    *,
    stage: str,
    artifact_root: Path | str,
    blocked_reason: str = "api_send_not_requested",
) -> dict[str, Any]:
    return normalize_usage_row(
        {
            "stage": stage,
            "status": "not_sent",
            "blocked_reason_redacted": blocked_reason,
            "artifact_root": str(artifact_root),
        }
    )


def append_usage_ledger_row(path: Path | str, row: Mapping[str, Any]) -> dict[str, Any]:
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_usage_row(row)
    with ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(normalized, ensure_ascii=False, sort_keys=True))
        handle.write("\n")
    return normalized


def initialize_empty_usage_ledger(
    path: Path | str,
    *,
    artifact_root: Path | str,
    reason: str = "api_send_forbidden_in_window_2",
) -> dict[str, Any]:
    ledger_path = Path(path)
    if ledger_path.exists():
        ledger_path.unlink()
    return append_usage_ledger_row(
        ledger_path,
        build_not_sent_usage_row(
            stage="window_2_preflight",
            artifact_root=artifact_root,
            blocked_reason=reason,
        ),
    )
