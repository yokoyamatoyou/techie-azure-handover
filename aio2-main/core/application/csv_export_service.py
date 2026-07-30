from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from core.application.time_display import format_jst_datetime
from core.config import config

EXPORTS_DIR = config.POC_OUTPUT_DIR / "exports"


def sanitize_csv_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{text}"
    return text


def _structured_csv_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return "" if value is None else str(value)


def _write_csv(filename_prefix: str, fieldnames: List[str], rows: Iterable[Dict[str, Any]]) -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = EXPORTS_DIR / f"{filename_prefix}-{timestamp}.csv"
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: sanitize_csv_cell(row.get(field, "")) for field in fieldnames})
    return output_path


def export_priority_actions_csv(snapshot: Dict[str, Any], run_row: Dict[str, Any]) -> Path:
    actions = ((snapshot.get("exports") or {}).get("priority_actions") or [])[:50]
    rows = []
    for index, action in enumerate(actions, 1):
        rows.append(
            {
                "run_id": run_row.get("id"),
                "analyzed_at": format_jst_datetime(run_row.get("analyzed_at")),
                "url": run_row.get("url"),
                "priority_rank": index,
                "action_id": action.get("action_id"),
                "area": action.get("area"),
                "category": action.get("category"),
                "label": action.get("label"),
                "title": action.get("title"),
                "action": action.get("action"),
                "detail": action.get("detail"),
                "role": action.get("role"),
                "effort": action.get("effort"),
                "urgency": action.get("urgency"),
                "kpi": action.get("kpi"),
                "impact": action.get("impact"),
                "audience": _structured_csv_value(action.get("audience")),
                "evidence": _structured_csv_value(action.get("evidence")),
                "status": action.get("status"),
            }
        )

    fieldnames = [
        "run_id",
        "analyzed_at",
        "url",
        "priority_rank",
        "action_id",
        "area",
        "category",
        "label",
        "title",
        "action",
        "detail",
        "role",
        "effort",
        "urgency",
        "kpi",
        "impact",
        "audience",
        "evidence",
        "status",
    ]
    return _write_csv("priority-actions", fieldnames, rows)


def export_history_csv(rows: List[Dict[str, Any]]) -> Path:
    fieldnames = [
        "id",
        "analyzed_at",
        "url",
        "site_type",
        "industry",
        "seo_score",
        "aio_score",
        "legal_score",
        "integrated_score",
        "priority_level",
        "total_issues",
        "top_action",
        "result_path",
    ]
    display_rows = []
    for row in rows:
        display_row = dict(row)
        display_row["analyzed_at"] = format_jst_datetime(row.get("analyzed_at"))
        display_rows.append(display_row)
    return _write_csv("analysis-history", fieldnames, display_rows)
