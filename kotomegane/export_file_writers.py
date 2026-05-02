from __future__ import annotations

import csv
import json
import secrets
import time
from pathlib import Path
from typing import Any, Callable

from analysis_lib import build_raw_results_export_rows, build_weekly_summary_rows, format_timestamp
from config import AppConfig
from report_summary_builders import build_report_summary_markdown

_LEGACY_EXPORT_FILENAMES = (
    "raw_results.csv",
    "weekly_summary.csv",
    "report_summary.md",
    "raw_results.json",
)


def archive_legacy_export_files(
    exports_dir: Path,
    archive_dir: Path,
) -> None:
    if not exports_dir.exists():
        return
    for filename in _LEGACY_EXPORT_FILENAMES:
        legacy_path = exports_dir / filename
        if not legacy_path.exists() or not legacy_path.is_file():
            continue
        archive_dir.mkdir(parents=True, exist_ok=True)
        archived_name = f"{legacy_path.stem}_{legacy_path.stat().st_mtime_ns}{legacy_path.suffix}"
        legacy_path.replace(archive_dir / archived_name)


def write_export_files(
    rows: list[dict[str, Any]],
    config: AppConfig,
    exports_dir: Path,
    source_loader: Callable[[str], list[dict[str, Any]]],
) -> tuple[list[dict[str, str]], str]:
    raw_rows = build_raw_results_export_rows(rows, config)
    weekly_rows = build_weekly_summary_rows(rows, config)
    generated_at = format_timestamp(time.time())
    report_summary = build_report_summary_markdown(rows, config, source_loader)
    export_bundle_id = secrets.token_urlsafe(12)
    export_dir = exports_dir / export_bundle_id
    export_dir.mkdir(parents=True, exist_ok=True)
    files = [
        ("raw_results.csv", raw_rows),
        ("weekly_summary.csv", weekly_rows),
        ("report_summary.md", report_summary),
        (
            "raw_results.json",
            {
                "generated_at": generated_at,
                "scope": {
                    "analysis_mode": config.analysis_mode,
                    "keywords": config.keywords,
                    "target_domain": config.target_domain,
                },
                "rows": raw_rows,
            },
        ),
    ]
    metadata: list[dict[str, str]] = []
    for filename, payload in files:
        path = export_dir / filename
        if filename.endswith(".csv"):
            rows_payload = payload if isinstance(payload, list) else []
            fieldnames = list(rows_payload[0].keys()) if rows_payload else ["generated_at"]
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                if rows_payload:
                    writer.writerows(rows_payload)
                else:
                    writer.writerow({"generated_at": generated_at})
        elif filename.endswith(".json"):
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            path.write_text(str(payload), encoding="utf-8")
        metadata.append(
            {
                "label": filename,
                "path": f"/exports/{export_bundle_id}/{filename}",
                "generated_at": generated_at,
            }
        )
    return metadata, report_summary
