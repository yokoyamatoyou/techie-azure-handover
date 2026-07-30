from __future__ import annotations

import json
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


RUN_COUNT = 10
SOURCE_URLS = [
    "https://www.kyotokogyo.co.jp/",
    "https://www.kyotokogyo.co.jp/about/coprof/",
    "https://www.kyotokogyo.co.jp/about/history/",
    "https://www.kyotokogyo.co.jp/service/input_scaning/",
]
PROMPT = (
    "京都工業株式会社について、現在の事業内容、相談の入口、支援範囲、"
    "導入の流れ、相談前に見る点が分かる会社紹介記事を作成してください。"
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


def _output_text(result: Mapping[str, Any]) -> str:
    return "\n\n".join(
        str(result.get(key) or "").strip()
        for key in ("title", "lead", "body")
        if str(result.get(key) or "").strip()
    )


def _visible_eval(result: Mapping[str, Any], success: bool, reason_code: str) -> str:
    text = _output_text(result)
    if not success:
        return "false-positive疑い" if reason_code == "SYS_PIPELINE_FAILURE" else "bad"
    body_chars = len(str(result.get("body") or ""))
    if body_chars < 650:
        return "flat"
    if "お問い合わせください" in text and body_chars < 1000:
        return "acceptable"
    return "good" if body_chars >= 900 else "acceptable"


def _failure_classification(result: Mapping[str, Any], success: bool) -> str:
    if success:
        return "none"
    error = _plain_dict(_nested(result, "pipeline_check", "error"))
    message = str(error.get("message") or result.get("message") or "")
    final_validation = _plain_dict(error.get("company_introduction_final_hard_validation"))
    repair = _plain_dict(error.get("company_introduction_source_contract_repair"))
    if (
        "Company introduction hard source contract trigger remained after repair" in message
        and bool(repair.get("cleared"))
        and int(repair.get("after_failure_count") or -1) == 0
        and bool(final_validation.get("repair_trigger_ids"))
    ):
        return "old_source_clear_not_reflected"
    return "new_failure"


def _summarize_run(run_id: int, elapsed_sec: float, result: Mapping[str, Any]) -> dict[str, Any]:
    pipeline_check = _plain_dict(result.get("pipeline_check"))
    body_generation = _plain_dict(pipeline_check.get("body_generation"))
    repair_metadata = _plain_dict(body_generation.get("repair_call"))
    hard_soft_eval = _plain_dict(pipeline_check.get("hard_soft_eval"))
    output_guard = _plain_dict(pipeline_check.get("output_guard"))
    observability = _plain_dict(body_generation.get("company_intro_observability"))
    source_coverage = _plain_dict(
        observability.get("source_slot_coverage_final")
        or body_generation.get("company_introduction_source_contract_validation")
    )
    repair_entry = _plain_dict(body_generation.get("repair_entry"))
    error = _plain_dict(pipeline_check.get("error"))
    reason_code = str(result.get("runtime_reason_code") or result.get("reason_code") or "")
    success = bool(result.get("success"))
    reject_reason = str(
        repair_entry.get("acceptance_rejection_reason")
        or repair_metadata.get("acceptance_rejection_reason")
        or ""
    )
    return {
        "run_id": run_id,
        "elapsed_sec": round(elapsed_sec, 2),
        "success": success,
        "runtime_reason_code": reason_code,
        "repair_required": bool(repair_entry.get("repair_required") or hard_soft_eval.get("repair_required")),
        "repair_applied": bool(body_generation.get("repair_applied")),
        "repair_rejected": bool(repair_entry.get("repair_rejected") or (reject_reason and not body_generation.get("repair_applied"))),
        "repair_reject_reason": reject_reason,
        "output_guard_reasons": list(output_guard.get("reasons") or result.get("output_guard_reasons") or []),
        "soft_warning_count": len(list(hard_soft_eval.get("soft_warnings") or body_generation.get("soft_warnings") or [])),
        "source_slot_coverage": source_coverage,
        "codex_visible_eval": _visible_eval(result, success, reason_code),
        "failure_classification": _failure_classification(result, success),
        "message": str(error.get("message") or result.get("message") or ""),
        "title": str(result.get("title") or ""),
        "body_chars": len(str(result.get("body") or "")),
        "first_heading": str(body_generation.get("failure_candidate_summary", {}).get("first_heading") or ""),
        "company_intro_source_contract_repair": _plain_dict(error.get("company_introduction_source_contract_repair")),
    }


def main() -> int:
    created_at = datetime.now(ZoneInfo("Asia/Tokyo"))
    out_dir = ROOT / "logs" / f"pipeline_responsibility_split_live_validation_{created_at:%Y%m%d-%H%M%S}"
    out_dir.mkdir(parents=True, exist_ok=False)
    jsonl_path = out_dir / "company_intro_10run_summary.jsonl"
    summary_path = out_dir / "summary.json"
    pipeline = MinimalPipeline(llm_client=LLMClient())
    rows: list[dict[str, Any]] = []
    payload = {
        "article_type": "branding",
        "semantic_article_key": "company_introduction",
        "source_mode": "grounded",
        "source_inputs": SOURCE_URLS,
        "source_values": SOURCE_URLS,
        "prompt_raw": PROMPT,
        "topic": PROMPT,
        "length_mode": "short",
        "content_goal": "trust",
        "writing_focus": "explanation",
        "input_decision": {"action": "accept"},
    }
    for run_id in range(1, RUN_COUNT + 1):
        started = time.time()
        try:
            result = execute_current_mainline_generation(pipeline, payload, PROMPT)
        except Exception as exc:
            result = {
                "success": False,
                "runtime_reason_code": "EXCEPTION",
                "message": repr(exc),
                "pipeline_check": {"error": {"message": repr(exc)}},
            }
        row = _summarize_run(run_id, time.time() - started, result)
        rows.append(row)
        with jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        (out_dir / f"run_{run_id:02d}_result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        print(json.dumps(row, ensure_ascii=True, default=str), flush=True)
    summary = {
        "created_at": created_at.isoformat(),
        "source_urls": SOURCE_URLS,
        "run_count": RUN_COUNT,
        "success_count": sum(1 for row in rows if row["success"]),
        "old_failure_count": sum(1 for row in rows if row["failure_classification"].startswith("old_")),
        "new_failure_count": sum(1 for row in rows if row["failure_classification"] == "new_failure"),
        "rows": rows,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"SUMMARY {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
