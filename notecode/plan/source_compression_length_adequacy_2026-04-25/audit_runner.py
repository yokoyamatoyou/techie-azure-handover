from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

ROOT = Path(r"C:\tetie\notecode")
sys.path.insert(0, str(ROOT))

from note.current_mainline_runner import execute_current_mainline_generation
from note.llm_client import LLMClient
from note.simple_note_pipeline.pipeline import MinimalPipeline


PREVIOUS_DIR = ROOT / "logs" / "multi_type_current_mainline_validation_20260425-013935"
PREVIOUS_SUMMARY = PREVIOUS_DIR / "post_evaluation_summary.json"
DEFAULT_LOG_PREFIX = "source_compression_length_adequacy"
WATCH_RUN_IDS = {
    "bl-industry-evaluation-shift",
    "rerun-company-introduction-url-operational-source",
    "rerun-case-study-rich-source",
}

INPUT_KEYS = (
    "article_type",
    "semantic_article_key",
    "source_mode",
    "source_inputs",
    "source_values",
    "source_documents",
    "prompt_raw",
    "topic",
    "audience_profile",
    "content_goal",
    "writing_focus",
    "tone_profile",
    "speaker_profile",
    "core_message",
    "length_mode",
    "length_mode_requested",
    "structure",
    "comparison_axes",
    "interview_answers",
    "strict_saas_mode",
    "body_generation_experiment",
    "ui_journey",
    "allow_experience",
    "input_decision",
    "question_mode",
)

INTERNAL_TERM_PATTERNS = (
    "source_limit",
    "persona",
    "editor",
    "trial",
    "hidden",
    "PATCH_SCOPE",
    "SEMANTIC_LEDGER",
    "SECTION_SHADOW",
)


def _plain_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _nested(mapping: Mapping[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping):
            return {}
        current = current.get(key)
    return current


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _body_text(result: Mapping[str, Any]) -> str:
    return str(result.get("body") or "")


def _output_text(result: Mapping[str, Any]) -> str:
    return "\n\n".join(
        str(result.get(key) or "").strip()
        for key in ("title", "lead", "body")
        if str(result.get(key) or "").strip()
    )


def _char_len(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return len(value)
    return len(json.dumps(value, ensure_ascii=False))


def _section_metrics(body: str) -> dict[str, Any]:
    lines = body.splitlines()
    sections: list[dict[str, Any]] = []
    heading: str | None = None
    buffer: list[str] = []
    for line in lines:
        if re.match(r"^##\s+", line):
            if heading and heading != "## 目次":
                sections.append({"heading": heading, "chars": len("\n".join(buffer).strip())})
            heading = line.strip()
            buffer = []
        elif heading:
            buffer.append(line)
    if heading and heading != "## 目次":
        sections.append({"heading": heading, "chars": len("\n".join(buffer).strip())})
    if not sections and body.strip():
        sections.append({"heading": "(no heading)", "chars": len(body.strip())})
    values = [int(item["chars"]) for item in sections]
    return {
        "section_count": len(sections),
        "section_char_distribution": sections,
        "shortest_section_chars": min(values) if values else 0,
        "longest_section_chars": max(values) if values else 0,
    }


def _internal_leakage(text: str) -> dict[str, Any]:
    hits = [pattern for pattern in INTERNAL_TERM_PATTERNS if pattern in text]
    return {"visible_internal_term_leakage": bool(hits), "visible_internal_term_hits": hits}


def _build_payload_from_artifact(artifact_path: Path) -> tuple[dict[str, Any], str]:
    artifact = _load_json(artifact_path)
    input_contract = _plain_dict(_nested(artifact, "pipeline_check", "input_contract"))
    if not input_contract:
        input_contract = _plain_dict(_nested(artifact, "result", "pipeline_check", "input_contract"))
    payload = {key: input_contract.get(key) for key in INPUT_KEYS if key in input_contract}
    prompt = str(payload.get("prompt_raw") or payload.get("topic") or "")
    if "source_values" not in payload and payload.get("source_inputs"):
        payload["source_values"] = list(payload.get("source_inputs") or [])
    payload.setdefault("input_decision", {"action": "accept"})
    payload.setdefault("source_mode", "grounded")
    return payload, prompt


def _range_hint(article_type: str, semantic_key: str) -> dict[str, Any]:
    if article_type == "announcement":
        return {"min": 600, "max": 1000, "label": "announcement"}
    if article_type == "daily_story":
        return {"min": 700, "max": 1200, "label": "daily_story"}
    if semantic_key == "company_introduction" or article_type == "case_study":
        return {"min": 1200, "max": 1800, "label": "company_introduction_or_case_study"}
    return {"min": 1600, "max": 2400, "label": "longform_explanatory_industry_product_comparative"}


def _visible_eval(
    *,
    article_type: str,
    semantic_key: str,
    success: bool,
    body_chars: int,
    section_count: int,
    source_total_chars: int,
    soft_warning_count: int,
) -> str:
    if not success:
        return "false-positive疑い"
    hint = _range_hint(article_type, semantic_key)
    if body_chars < max(500, int(hint["min"] * 0.72)):
        return "too_short"
    if body_chars < hint["min"]:
        if article_type in {"announcement", "daily_story"}:
            return "good"
        if source_total_chars > 450:
            return "acceptable"
        return "acceptable"
    if section_count >= 3 and soft_warning_count <= 7:
        return "good"
    return "acceptable"


def _classification(
    *,
    article_type: str,
    semantic_key: str,
    success: bool,
    body_chars: int,
    source_total_chars: int,
    repair_rejected: bool,
    repair_reject_reason: str,
    visible_eval: str,
) -> tuple[str, str, str]:
    if not success:
        return "fail_closed_ok", "none", "no"
    hint = _range_hint(article_type, semantic_key)
    if body_chars < hint["min"]:
        if article_type in {"announcement", "daily_story"} and visible_eval in {"good", "acceptable"}:
            return "OK", "type_expected_short", "no"
        if repair_rejected and "short" in repair_reject_reason:
            return "thin_due_to_repair_rejection", "repair_rejected_short_candidate", "yes"
        if source_total_chars < 350:
            return "thin_due_to_source", "source_thin", "no"
        return "acceptable_but_watch", "target_chars_low", "no"
    if body_chars > int(hint["max"] * 1.15):
        return "verbose_or_padded", "none", "yes"
    if visible_eval == "good":
        return "OK", "none", "no"
    return "acceptable_but_watch", "none", "no"


def _result_metrics(run_id: str, result: Mapping[str, Any], payload: Mapping[str, Any], elapsed: float) -> dict[str, Any]:
    pipeline_check = _plain_dict(result.get("pipeline_check"))
    input_contract = _plain_dict(pipeline_check.get("input_contract"))
    body_generation = _plain_dict(pipeline_check.get("body_generation"))
    hard_soft_eval = _plain_dict(pipeline_check.get("hard_soft_eval"))
    output_guard = _plain_dict(pipeline_check.get("output_guard"))
    repair_entry = _plain_dict(body_generation.get("repair_entry"))
    repair_call = _plain_dict(body_generation.get("repair_call"))
    observability = _plain_dict(body_generation.get("company_intro_observability"))
    source_slot_coverage = _plain_dict(
        observability.get("source_slot_coverage_final")
        or body_generation.get("company_introduction_source_contract_validation")
    )
    if source_slot_coverage and source_slot_coverage.get("pattern") != "company_introduction_operational_source_contract_v1":
        source_slot_coverage = {}
    source_documents = list(input_contract.get("source_documents") or payload.get("source_documents") or [])
    source_total_chars = sum(
        _char_len(doc.get("content")) for doc in source_documents if isinstance(doc, Mapping)
    )
    source_packet = input_contract.get("_source_packet")
    source_summary_chars: int | str = "not available"
    if isinstance(source_packet, Mapping):
        source_summary_chars = sum(
            _char_len(source_packet.get(key))
            for key in ("source_facts", "reader_friction", "must_cover", "late_return")
        )
    source_packet_chars: int | str = (
        _char_len(source_packet) if isinstance(source_packet, Mapping) else "not available"
    )
    body = _body_text(result)
    section = _section_metrics(body)
    article_type = str(input_contract.get("article_type") or payload.get("article_type") or "")
    semantic_key = str(input_contract.get("semantic_article_key") or payload.get("semantic_article_key") or "")
    success = bool(result.get("success"))
    reason_code = str(result.get("runtime_reason_code") or result.get("reason_code") or "")
    soft_warnings = list(hard_soft_eval.get("soft_warnings") or body_generation.get("soft_warnings") or [])
    reject_reason = str(
        repair_entry.get("acceptance_rejection_reason")
        or repair_call.get("acceptance_rejection_reason")
        or ""
    )
    repair_required = bool(repair_entry.get("repair_required") or hard_soft_eval.get("repair_required"))
    repair_applied = bool(body_generation.get("repair_applied"))
    repair_rejected = bool(repair_entry.get("repair_rejected") or (reject_reason and not repair_applied))
    leakage = _internal_leakage(_output_text(result))
    visible_eval = _visible_eval(
        article_type=article_type,
        semantic_key=semantic_key,
        success=success,
        body_chars=len(body),
        section_count=int(section["section_count"]),
        source_total_chars=source_total_chars,
        soft_warning_count=len(soft_warnings),
    )
    classification, thinness_reason, improvement_need = _classification(
        article_type=article_type,
        semantic_key=semantic_key,
        success=success,
        body_chars=len(body),
        source_total_chars=source_total_chars,
        repair_rejected=repair_rejected,
        repair_reject_reason=reject_reason,
        visible_eval=visible_eval,
    )
    required_slot_coverage: Any = "not available"
    source_facts_reflected_count: Any = "not available"
    if source_slot_coverage and semantic_key == "company_introduction":
        required_slots = list(source_slot_coverage.get("required_slots") or [])
        visible_slots = _plain_dict(source_slot_coverage.get("visible_slot_presence"))
        source_facts_reflected_count = sum(1 for slot in required_slots if visible_slots.get(slot))
        required_slot_coverage = {
            "covered": source_facts_reflected_count,
            "required": len(required_slots),
            "missing_required_slots": list(source_slot_coverage.get("missing_required_slots") or []),
            "unbacked_required_slots": list(source_slot_coverage.get("unbacked_required_slots") or []),
        }
    return {
        "run_id": run_id,
        "elapsed_sec": round(elapsed, 2),
        "success": success,
        "runtime_reason_code": reason_code,
        "article_type": article_type,
        "semantic_article_key": semantic_key,
        "source_mode": str(input_contract.get("source_mode") or payload.get("source_mode") or ""),
        "source_document_count": len(source_documents),
        "source_total_chars": source_total_chars,
        "source_summary_chars": source_summary_chars,
        "source_packet_chars": source_packet_chars,
        "grounding_item_count": len(list(input_contract.get("source_grounding_items") or [])),
        "must_cover_count": len(list(input_contract.get("must_cover") or [])),
        "target_chars": input_contract.get("target_chars", "not available"),
        "body_chars": len(body),
        "body_chars_to_target_chars": "not available",
        **section,
        "source_facts_reflected_count": source_facts_reflected_count,
        "required_source_slot_coverage": required_slot_coverage,
        "soft_warning_count": len(soft_warnings),
        "soft_warnings": soft_warnings,
        "repair_required": repair_required,
        "repair_applied": repair_applied,
        "repair_rejected": repair_rejected,
        "repair_reject_reason": reject_reason,
        "output_guard_reasons": list(output_guard.get("reasons") or result.get("output_guard_reasons") or []),
        **leakage,
        "codex_visible_eval": visible_eval,
        "classification": classification,
        "thinness_reason": thinness_reason,
        "improvement_need": improvement_need,
        "old_new_regression_classification": "none",
        "title": str(result.get("title") or ""),
        "range_hint": _range_hint(article_type, semantic_key),
    }


def _case_rows(watch_repeats: int) -> list[dict[str, Any]]:
    summary = _load_json(PREVIOUS_SUMMARY)
    rows = list(summary.get("rows") or [])
    selected: list[dict[str, Any]] = []
    for row in rows:
        selected.append({**row, "_repeat": 0})
        if row.get("run_id") in WATCH_RUN_IDS:
            for repeat in range(1, watch_repeats + 1):
                selected.append({**row, "_repeat": repeat})
    return selected


def _write_markdown(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Source Compression Length Audit",
        "",
        f"- Created: {datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(timespec='seconds')}",
        f"- Rows: {len(rows)}",
        "",
        "| run_id | type | source chars | packet chars | body chars | sections | shortest/longest | warnings | repair | eval | class | thinness |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        repair = f"req={row['repair_required']}, applied={row['repair_applied']}, rejected={row['repair_rejected']}"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["run_id"]),
                    f"{row['article_type']}/{row['semantic_article_key']}",
                    str(row["source_total_chars"]),
                    str(row["source_packet_chars"]),
                    str(row["body_chars"]),
                    str(row["section_count"]),
                    f"{row['shortest_section_chars']}/{row['longest_section_chars']}",
                    str(row["soft_warning_count"]),
                    repair,
                    str(row["codex_visible_eval"]),
                    str(row["classification"]),
                    str(row["thinness_reason"]),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## Initial Classification")
    lines.append("")
    for classification in sorted({row["classification"] for row in rows}):
        count = sum(1 for row in rows if row["classification"] == classification)
        lines.append(f"- `{classification}`: {count}")
    (out_dir / "audit_metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit source compression versus body length adequacy.")
    parser.add_argument("--watch-repeats", type=int, default=2)
    parser.add_argument("--out-dir", type=str, default="")
    args = parser.parse_args()
    created = datetime.now(ZoneInfo("Asia/Tokyo"))
    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "logs" / f"{DEFAULT_LOG_PREFIX}_{created:%Y%m%d-%H%M%S}"
    out_dir.mkdir(parents=True, exist_ok=False)
    pipeline = MinimalPipeline(llm_client=LLMClient())
    rows: list[dict[str, Any]] = []
    jsonl_path = out_dir / "audit_metrics.jsonl"
    for case in _case_rows(max(0, int(args.watch_repeats))):
        base_id = str(case.get("run_id") or "run")
        repeat = int(case.get("_repeat") or 0)
        run_id = base_id if repeat == 0 else f"{base_id}__repeat{repeat}"
        artifact_path = Path(str(case.get("artifact_json") or ""))
        payload, prompt = _build_payload_from_artifact(artifact_path)
        started = time.time()
        try:
            result = execute_current_mainline_generation(pipeline, payload, prompt)
        except Exception as exc:  # noqa: BLE001 - audit runner must capture failures.
            result = {
                "success": False,
                "runtime_reason_code": "EXCEPTION",
                "message": repr(exc),
                "pipeline_check": {"error": {"message": repr(exc)}},
            }
        elapsed = time.time() - started
        metrics = _result_metrics(run_id, result, payload, elapsed)
        rows.append(metrics)
        with jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(metrics, ensure_ascii=False, default=str) + "\n")
        (out_dir / f"{run_id}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / f"{run_id}.txt").write_text(_output_text(result), encoding="utf-8")
        print(json.dumps(metrics, ensure_ascii=True, default=str), flush=True)
    summary = {
        "created_at": created.isoformat(),
        "watch_repeats": max(0, int(args.watch_repeats)),
        "run_count": len(rows),
        "success_count": sum(1 for row in rows if row["success"]),
        "visible_internal_term_leakage_count": sum(1 for row in rows if row["visible_internal_term_leakage"]),
        "classification_counts": {
            key: sum(1 for row in rows if row["classification"] == key)
            for key in sorted({row["classification"] for row in rows})
        },
        "thinness_reason_counts": {
            key: sum(1 for row in rows if row["thinness_reason"] == key)
            for key in sorted({row["thinness_reason"] for row in rows})
        },
        "rows": rows,
    }
    (out_dir / "audit_metrics.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    _write_markdown(out_dir, rows)
    print(f"SUMMARY {out_dir / 'audit_metrics.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
