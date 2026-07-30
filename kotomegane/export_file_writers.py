from __future__ import annotations

import csv
import hashlib
import hmac
import json
import os
import re
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
_EXPORT_FILENAME_SET = frozenset(_LEGACY_EXPORT_FILENAMES)
_EXPORT_BUNDLE_RE = re.compile(r"^[A-Za-z0-9_-]{12,80}$")
_EXPORT_URL_TTL_SECONDS = int(os.getenv("KOTOMEGANE_EXPORT_URL_TTL_SECONDS", "900"))
_EXPORT_SIGNING_SECRET = (
    os.getenv("KOTOMEGANE_EXPORT_SIGNING_SECRET", "").strip()
    or secrets.token_urlsafe(32)
)


def _signature_payload(bundle_id: str, filename: str, expires_at: int) -> bytes:
    return f"{bundle_id}/{filename}:{expires_at}".encode("utf-8")


def _sign_export_path(bundle_id: str, filename: str, expires_at: int) -> str:
    return hmac.new(
        _EXPORT_SIGNING_SECRET.encode("utf-8"),
        _signature_payload(bundle_id, filename, expires_at),
        hashlib.sha256,
    ).hexdigest()


def build_signed_export_path(bundle_id: str, filename: str, *, now: float | None = None) -> str:
    expires_at = int((time.time() if now is None else now) + _EXPORT_URL_TTL_SECONDS)
    token = _sign_export_path(bundle_id, filename, expires_at)
    return f"/exports/{bundle_id}/{filename}?expires={expires_at}&token={token}"


def validate_signed_export_path(
    exports_dir: Path,
    bundle_id: str,
    filename: str,
    *,
    expires: str,
    token: str,
    now: float | None = None,
) -> Path | None:
    if not _EXPORT_BUNDLE_RE.fullmatch(str(bundle_id or "")):
        return None
    if filename not in _EXPORT_FILENAME_SET:
        return None
    try:
        expires_at = int(str(expires or "").strip())
    except ValueError:
        return None
    if expires_at < int(time.time() if now is None else now):
        return None
    expected = _sign_export_path(bundle_id, filename, expires_at)
    if not token or not hmac.compare_digest(str(token), expected):
        return None
    try:
        root = exports_dir.resolve(strict=False)
        candidate = (root / bundle_id / filename).resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return None
    if candidate != root and root not in candidate.parents:
        return None
    if not candidate.exists() or not candidate.is_file():
        return None
    return candidate


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
                "path": build_signed_export_path(export_bundle_id, filename),
                "generated_at": generated_at,
            }
        )
    return metadata, report_summary
