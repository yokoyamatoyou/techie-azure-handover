from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from core.config import config

EXPORTS_DIR = config.POC_OUTPUT_DIR / "exports"


def sanitize_csv_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{text}"
    return text


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
                "analyzed_at": run_row.get("analyzed_at"),
                "url": run_row.get("url"),
                "priority_rank": index,
                "area": action.get("area"),
                "label": action.get("label"),
                "title": action.get("title"),
                "action": action.get("action"),
                "detail": action.get("detail"),
                "role": action.get("role"),
                "effort": action.get("effort"),
                "kpi": action.get("kpi"),
                "impact": action.get("impact"),
            }
        )

    fieldnames = [
        "run_id",
        "analyzed_at",
        "url",
        "priority_rank",
        "area",
        "label",
        "title",
        "action",
        "detail",
        "role",
        "effort",
        "kpi",
        "impact",
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
    return _write_csv("analysis-history", fieldnames, rows)
