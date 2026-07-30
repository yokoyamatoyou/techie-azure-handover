from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\tetie\notecode")
PACKAGE_DIR = Path(__file__).resolve().parent
MANIFEST = PACKAGE_DIR / "source_snapshot_manifest.json"
BASE_SCRIPT = (
    ROOT
    / "logs"
    / "current_mainline_log_source_ui_regression_20260426-023257"
    / "run_log_source_ui_regression.py"
)
RUN_DIR = ROOT / "logs" / "current_mainline_full_flow_regression_from_manifest_20260426-000000"
MOVING_TARGET = ROOT / "logs" / "latest_generation_output.json"
IMAGE_VALIDATION_ATTEMPTS = {
    ("company_introduction_kyoto_latest_log", 1),
    ("bl-comparative-selection-criteria", 1),
}


def _load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("log_source_ui_regression_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load base harness: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_manifest() -> dict[str, Any]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("moving_target_allowed") is not False:
        raise RuntimeError("Manifest must set moving_target_allowed=false")
    return data


def _validate_record(record: dict[str, Any]) -> None:
    origin = Path(str(record.get("source_origin_artifact") or ""))
    try:
        same_moving_target = origin.resolve() == MOVING_TARGET.resolve()
    except Exception:
        same_moving_target = str(origin).lower() == str(MOVING_TARGET).lower()
    if same_moving_target:
        raise RuntimeError(f"Moving source target is forbidden: {origin}")
    if record.get("moving_target") is not False:
        raise RuntimeError(f"Record must set moving_target=false: {record.get('case_id')}")
    docs = list(record.get("source_documents") or [])
    if len(docs) != int(record.get("source_document_count") or -1):
        raise RuntimeError(f"source_document_count mismatch: {record.get('case_id')}")
    for index, doc in enumerate(docs, start=1):
        for key in ("title", "locator", "content", "source_type"):
            if key not in doc:
                raise RuntimeError(f"Missing {key} in {record.get('case_id')} source {index}")


def _manifest_source_inventory(module: Any) -> list[dict[str, Any]]:
    manifest = _read_manifest()
    records = list(manifest.get("records") or []) + list(manifest.get("excluded_records") or [])
    source_specs: list[dict[str, Any]] = []
    for record in records:
        _validate_record(record)
        source_caveat = record.get("source_caveat") or []
        if isinstance(source_caveat, str):
            source_caveats = [source_caveat]
        else:
            source_caveats = [str(item) for item in list(source_caveat)]
        validation_status = str(record.get("validation_status") or "active")
        spec = {
            "case_id": str(record["case_id"]),
            "article_type_target": str(record["article_type"]),
            "article_type_for_ui": str(record.get("article_type_for_ui") or record["article_type"]),
            "semantic_article_key_expected": str(record.get("semantic_article_key") or ""),
            "historical_source_path": str(record["source_origin_artifact"]),
            "source_origin": "source_snapshot_manifest.json",
            "source_documents": [dict(item) for item in list(record.get("source_documents") or [])],
            "source_values": [str(item) for item in list(record.get("source_values") or [])],
            "source_caveats": source_caveats,
            "controls": dict(record.get("controls") or {}),
            "historical_baseline": dict(record.get("historical_baseline") or {}),
            "validation_status": validation_status,
            "exclusion_reason": str(record.get("exclusion_reason") or ""),
            "route_mismatch_annotation": dict(record.get("route_mismatch_annotation") or {}),
            "moving_target": False,
            "source_origin_artifact": str(record["source_origin_artifact"]),
        }
        source_specs.append(spec)

    for spec in source_specs:
        spec["source_file_paths"] = module._write_source_files(
            str(spec["case_id"]), list(spec.get("source_documents") or [])
        )
        spec["source_document_count"] = len(list(spec.get("source_documents") or []))
        spec["source_total_chars"] = sum(
            len(str(doc.get("content") or ""))
            for doc in list(spec.get("source_documents") or [])
        )
        case_dir = module.UI_DIR / str(spec["case_id"])
        case_dir.mkdir(parents=True, exist_ok=True)
        source_packet = {
            "case_id": spec["case_id"],
            "article_type_target": spec["article_type_target"],
            "historical_source_path": spec["historical_source_path"],
            "source_origin": spec["source_origin"],
            "source_origin_artifact": spec["source_origin_artifact"],
            "source_values": spec.get("source_values", []),
            "source_documents": spec.get("source_documents", []),
            "source_caveats": spec.get("source_caveats", []),
            "source_document_count": spec["source_document_count"],
            "source_total_chars": spec["source_total_chars"],
            "validation_status": spec.get("validation_status", "active"),
            "exclusion_reason": spec.get("exclusion_reason", ""),
            "route_mismatch_annotation": spec.get("route_mismatch_annotation", {}),
            "moving_target": False,
        }
        (case_dir / "source_reconstructed_from_log.json").write_text(
            json.dumps(source_packet, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    (module.RUN_DIR / "source_inventory.json").write_text(
        json.dumps(source_specs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (module.RUN_DIR / "historical_baseline.json").write_text(
        json.dumps(
            [
                {
                    "case_id": item["case_id"],
                    "article_type_target": item["article_type_target"],
                    "historical_baseline": item["historical_baseline"],
                    "source_caveats": item["source_caveats"],
                    "validation_status": item.get("validation_status", "active"),
                    "exclusion_reason": item.get("exclusion_reason", ""),
                    "moving_target": False,
                }
                for item in source_specs
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return source_specs


def main() -> int:
    module = _load_base_module()
    module.RUN_DIR = RUN_DIR
    module.UI_DIR = RUN_DIR / "ui_live"
    module.SOURCE_FILE_DIR = RUN_DIR / "source_files"
    module.SUMMARY_DIR = RUN_DIR / "summaries"
    module._build_source_inventory = lambda: _manifest_source_inventory(module)
    base_run_attempt = module._run_attempt

    def _run_attempt_with_manifest_image_scope(case: dict[str, Any], attempt: int) -> dict[str, Any]:
        case_id = str(case.get("case_id") or "")
        if (case_id, int(attempt)) in IMAGE_VALIDATION_ATTEMPTS:
            module.IMAGE_VALIDATION_CASES = {case_id}
        else:
            module.IMAGE_VALIDATION_CASES = set()
        return base_run_attempt(case, attempt)

    module._run_attempt = _run_attempt_with_manifest_image_scope
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
