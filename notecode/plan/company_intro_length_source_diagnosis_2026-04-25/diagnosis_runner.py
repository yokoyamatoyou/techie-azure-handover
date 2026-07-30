from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

ROOT = Path(r"C:\tetie\notecode")
sys.path.insert(0, str(ROOT))

from note.current_mainline_runner import execute_current_mainline_generation
from note.llm_client import LLMClient
from note.simple_note_pipeline.pipeline import MinimalPipeline
from note.simple_note_pipeline.prompt_builder import target_chars


DEFAULT_LOG_PREFIX = "company_intro_length_source_diagnosis"
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
KYOTO_SOURCE_URLS = [
    "https://www.kyotokogyo.co.jp/",
    "https://www.kyotokogyo.co.jp/about/coprof/",
    "https://www.kyotokogyo.co.jp/about/history/",
    "https://www.kyotokogyo.co.jp/service/input_scaning/",
]
KYOTO_PROMPT = (
    "京都工業株式会社について、現在の事業内容、相談の入口、支援範囲、"
    "導入の流れ、相談前に見る点が分かる会社紹介記事を作成してください。"
)
YOSHINOMORE_SOURCE_URLS = [
    "https://yoshinomore-law.jp/",
    "https://yoshinomore-law.jp/company/",
    "https://yoshinomore-law.jp/service/",
    "https://yoshinomore-law.jp/arrangements/",
]
SOURCE_PROFILES: dict[str, dict[str, Any]] = {
    "kyotokogyo_source_rich_v1": {
        "urls": KYOTO_SOURCE_URLS,
        "prompt": KYOTO_PROMPT,
        "length_mode": "short",
        "content_goal": "trust",
        "writing_focus": "explanation",
    },
    "yoshinomore_law_source_rich_v1": {
        "urls": YOSHINOMORE_SOURCE_URLS,
        "prompt": "",
        "length_mode": "adaptive",
        "content_goal": "auto",
        "writing_focus": "auto",
    },
}


def _plain_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _nested(mapping: Mapping[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping):
            return {}
        current = current.get(key)
    return current


def _char_len(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return len(value)
    return len(json.dumps(value, ensure_ascii=False, default=str))


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _output_text(result: Mapping[str, Any]) -> str:
    return "\n\n".join(
        _safe_text(result.get(key))
        for key in ("title", "lead", "body")
        if _safe_text(result.get(key))
    )


def _body_text(result: Mapping[str, Any]) -> str:
    return str(result.get("body") or "")


def _paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    for part in re.split(r"\n\s*\n+", text):
        cleaned = "\n".join(
            line.strip()
            for line in part.splitlines()
            if line.strip() and not line.strip().startswith("##")
        ).strip()
        if cleaned:
            paragraphs.append(cleaned)
    return paragraphs


def _section_metrics(body: str) -> dict[str, Any]:
    lines = body.splitlines()
    sections: list[dict[str, Any]] = []
    heading: str | None = None
    buffer: list[str] = []
    for line in lines:
        if re.match(r"^##\s+", line):
            if heading and heading != "## 目次":
                text = "\n".join(buffer).strip()
                sections.append(
                    {
                        "heading": heading,
                        "chars": len(text),
                        "paragraph_count": len(_paragraphs(text)),
                    }
                )
            heading = line.strip()
            buffer = []
        elif heading:
            buffer.append(line)
    if heading and heading != "## 目次":
        text = "\n".join(buffer).strip()
        sections.append(
            {
                "heading": heading,
                "chars": len(text),
                "paragraph_count": len(_paragraphs(text)),
            }
        )
    if not sections and body.strip():
        sections.append(
            {
                "heading": "(no heading)",
                "chars": len(body.strip()),
                "paragraph_count": len(_paragraphs(body)),
            }
        )
    values = [int(item["chars"]) for item in sections]
    paragraphs = _paragraphs(body)
    return {
        "section_count": len(sections),
        "section_headings": [str(item["heading"]) for item in sections],
        "section_char_distribution": sections,
        "shortest_section_chars": min(values) if values else 0,
        "longest_section_chars": max(values) if values else 0,
        "final_section_chars": values[-1] if values else 0,
        "final_paragraph_chars": len(paragraphs[-1]) if paragraphs else 0,
    }


def _internal_leakage(text: str) -> dict[str, Any]:
    hits = [pattern for pattern in INTERNAL_TERM_PATTERNS if pattern in text]
    return {
        "visible_internal_term_leakage": "yes" if hits else "no",
        "visible_internal_term_hits": hits,
    }


def _find_values(value: Any, key_name: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) == key_name:
                found.append(child)
            found.extend(_find_values(child, key_name))
    elif isinstance(value, list):
        for child in value:
            found.extend(_find_values(child, key_name))
    return found


def _first_number(values: Iterable[Any]) -> int | str:
    for value in values:
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        text = str(value or "").strip()
        if text.isdigit():
            return int(text)
    return "not available"


def _source_packet_summary(source_packet: Any) -> dict[str, Any]:
    if not isinstance(source_packet, Mapping):
        return {
            "source_summary_chars": "not available",
            "source_packet_chars": "not available",
            "source_packet_fact_count": "not available",
            "source_packet_facts": [],
        }
    facts = [str(item).strip() for item in list(source_packet.get("source_facts") or []) if str(item).strip()]
    summary_chars = sum(
        _char_len(source_packet.get(key))
        for key in ("source_facts", "reader_friction", "must_cover", "late_return")
    )
    return {
        "source_summary_chars": summary_chars,
        "source_packet_chars": _char_len(source_packet),
        "source_packet_fact_count": len(facts),
        "source_packet_facts": facts,
    }


def _packet_fact_reflection(source_packet_facts: Iterable[str], body: str) -> dict[str, Any]:
    reflected: list[str] = []
    for fact in source_packet_facts:
        text = str(fact or "").strip()
        if text and text in body:
            reflected.append(text)
    return {
        "source_packet_facts_reflected_count": len(reflected),
        "source_packet_facts_reflected": reflected,
    }


def _source_documents(input_contract: Mapping[str, Any], payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    docs = input_contract.get("source_documents")
    if not isinstance(docs, list):
        docs = payload.get("source_documents")
    return [doc for doc in list(docs or []) if isinstance(doc, Mapping)]


def _company_intro_coverage(body_generation: Mapping[str, Any], error: Mapping[str, Any]) -> dict[str, Any]:
    observability = _plain_dict(body_generation.get("company_intro_observability"))
    coverage = _plain_dict(observability.get("source_slot_coverage_final"))
    if not coverage:
        coverage = _plain_dict(body_generation.get("company_introduction_source_contract_validation"))
    repair_payload = _plain_dict(error.get("company_introduction_source_contract_repair"))
    if not coverage and repair_payload:
        coverage = _plain_dict(repair_payload.get("after_validation"))
    return coverage


def _repair_payload(body_generation: Mapping[str, Any], error: Mapping[str, Any]) -> dict[str, Any]:
    observability = _plain_dict(body_generation.get("company_intro_observability"))
    repair = _plain_dict(observability.get("repair"))
    repair_entry = _plain_dict(body_generation.get("repair_entry"))
    repair_call = _plain_dict(body_generation.get("repair_call"))
    failure_repair = _plain_dict(error.get("company_introduction_source_contract_repair"))
    merged: dict[str, Any] = {}
    for item in (repair_call, repair_entry, repair, failure_repair):
        merged.update(item)
    return merged


def _slot_metrics(coverage: Mapping[str, Any]) -> dict[str, Any]:
    required_slots = list(coverage.get("required_slots") or [])
    visible_slot_presence = _plain_dict(
        coverage.get("visible_slot_presence") or coverage.get("slot_presence")
    )
    source_slot_presence = _plain_dict(coverage.get("source_slot_presence"))
    slot_lengths = _plain_dict(coverage.get("slot_text_lengths"))
    slot_excerpts = _plain_dict(coverage.get("slot_text_excerpts"))
    if not slot_lengths and slot_excerpts:
        slot_lengths = {key: len(str(value or "")) for key, value in slot_excerpts.items()}
    covered = sum(1 for slot in required_slots if visible_slot_presence.get(slot))
    return {
        "company_introduction_source_contract_slot_values_length": slot_lengths,
        "company_introduction_source_contract_slot_value_excerpts": slot_excerpts,
        "source_slot_presence": source_slot_presence,
        "visible_slot_presence": visible_slot_presence,
        "missing_required_slots": list(coverage.get("missing_required_slots") or []),
        "unbacked_required_slots": list(coverage.get("unbacked_required_slots") or []),
        "source_facts_reflected_count": covered if required_slots else "not available",
        "source_slot_coverage": {
            "covered": covered,
            "required": len(required_slots),
        }
        if required_slots
        else "not available",
    }


def _repair_required(body_generation: Mapping[str, Any], hard_soft_eval: Mapping[str, Any], repair: Mapping[str, Any]) -> bool:
    return bool(
        repair.get("repair_required")
        or _nested(body_generation, "repair_entry", "repair_required")
        or hard_soft_eval.get("repair_required")
    )


def _repair_rejected(body_generation: Mapping[str, Any], repair: Mapping[str, Any], repair_applied: bool) -> bool:
    reject_reason = str(
        repair.get("acceptance_rejection_reason")
        or repair.get("repair_reject_reason")
        or repair.get("scope_rejection_reason")
        or ""
    )
    return bool(
        repair.get("repair_rejected")
        or _nested(body_generation, "repair_entry", "repair_rejected")
        or (reject_reason and not repair_applied)
    )


def _visible_eval(metrics: Mapping[str, Any]) -> str:
    if not metrics.get("success"):
        return "false-positive疑い" if metrics.get("runtime_reason_code") == "SYS_PIPELINE_FAILURE" else "bad"
    body_chars = int(metrics.get("body_chars") or 0)
    target = metrics.get("target_chars")
    shortest = int(metrics.get("shortest_section_chars") or 0)
    section_count = int(metrics.get("section_count") or 0)
    if body_chars < 900:
        return "too_short"
    if body_chars < 1150 and shortest < 190:
        return "thin"
    if body_chars < 1350:
        return "acceptable"
    if isinstance(target, int) and body_chars > int(target * 1.15):
        return "verbose"
    if section_count >= 4:
        return "good"
    return "acceptable"


def _thinness_classification(metrics: Mapping[str, Any]) -> str:
    if not metrics.get("success"):
        return "fail_closed_ok"
    source_total = int(metrics.get("source_total_chars") or 0)
    packet_chars = metrics.get("source_packet_chars")
    target = metrics.get("target_chars")
    body_chars = int(metrics.get("body_chars") or 0)
    grounding_count = int(metrics.get("grounding_item_count") or 0)
    must_cover_count = int(metrics.get("must_cover_count") or 0)
    shortest = int(metrics.get("shortest_section_chars") or 0)
    repair_rejected = bool(metrics.get("repair_rejected"))
    candidate = _plain_dict(metrics.get("repair_candidate_summary"))
    candidate_chars = int(candidate.get("body_chars") or 0)
    if source_total < 500:
        return "source_thin"
    if isinstance(target, int) and target <= 1350 and body_chars <= int(target * 1.15):
        return "target_low_suspected"
    if (
        source_total >= 2500
        and isinstance(packet_chars, int)
        and (packet_chars < 800 or grounding_count <= 5 or must_cover_count <= 5)
    ):
        return "compression_loss_suspected"
    if repair_rejected and candidate_chars and candidate_chars >= body_chars + 180:
        return "repair_rejection_suspected"
    if isinstance(target, int) and target >= 1600 and body_chars <= 1250:
        return "realization_shallow_suspected"
    if shortest and shortest < 220 and body_chars < 1400:
        return "realization_shallow_suspected"
    return "none"


def _note_judgment(metrics: Mapping[str, Any]) -> str:
    if not metrics.get("success"):
        return "fail_closed_ok"
    classification = str(metrics.get("thinness_classification") or "")
    visible_eval = str(metrics.get("codex_visible_eval") or "")
    if classification in {"compression_loss_suspected", "realization_shallow_suspected", "target_low_suspected"}:
        return "acceptable_but_short" if visible_eval in {"good", "acceptable"} else "thin"
    if visible_eval == "too_short":
        return "thin"
    if visible_eval == "verbose":
        return "padded"
    if visible_eval == "good":
        return "sufficient"
    return "acceptable_but_short"


def _build_payload(source_profile_id: str, profile: Mapping[str, Any]) -> dict[str, Any]:
    prompt = str(profile.get("prompt") or "")
    length_mode = str(profile.get("length_mode") or "short")
    urls = [str(item) for item in list(profile.get("urls") or []) if str(item).strip()]
    return {
        "article_type": "branding",
        "semantic_article_key": "company_introduction",
        "source_mode": "grounded",
        "source_inputs": urls,
        "source_values": urls,
        "prompt_raw": prompt,
        "topic": prompt,
        "length_mode": length_mode,
        "length_mode_requested": length_mode,
        "content_goal": str(profile.get("content_goal") or "auto"),
        "writing_focus": str(profile.get("writing_focus") or "auto"),
        "structure": "auto",
        "source_profile_id": source_profile_id,
        "input_decision": {"action": "accept"},
    }


def _result_metrics(
    *,
    run_id: str,
    source_profile_id: str,
    result: Mapping[str, Any],
    payload: Mapping[str, Any],
    elapsed_sec: float,
) -> dict[str, Any]:
    pipeline_check = _plain_dict(result.get("pipeline_check"))
    input_contract = _plain_dict(pipeline_check.get("input_contract"))
    body_generation = _plain_dict(pipeline_check.get("body_generation"))
    hard_soft_eval = _plain_dict(pipeline_check.get("hard_soft_eval"))
    output_guard = _plain_dict(pipeline_check.get("output_guard"))
    error = _plain_dict(pipeline_check.get("error"))
    if not error:
        error = _plain_dict(result.get("error"))
    body = _body_text(result)
    output_text = _output_text(result)
    source_documents = _source_documents(input_contract, payload)
    source_packet = input_contract.get("_source_packet")
    packet_summary = _source_packet_summary(source_packet)
    coverage = _company_intro_coverage(body_generation, error)
    repair = _repair_payload(body_generation, error)
    repair_applied = bool(body_generation.get("repair_applied") or repair.get("repair_applied"))
    repair_reject_reason = str(
        repair.get("acceptance_rejection_reason")
        or repair.get("repair_reject_reason")
        or repair.get("scope_rejection_reason")
        or ""
    )
    length_mode = str(input_contract.get("length_mode") or payload.get("length_mode") or "")
    article_type = str(input_contract.get("article_type") or payload.get("article_type") or "")
    source_count = len(source_documents) or len(list(payload.get("source_values") or []))
    estimated_target = target_chars(length_mode, article_type, source_count=source_count)
    observed_target = _first_number(_find_values(result, "target_chars"))
    final_target = observed_target if isinstance(observed_target, int) else estimated_target
    observed_max_tokens = _first_number(_find_values(result, "max_tokens"))
    estimated_max_tokens = max(2800, min(7000, int(int(final_target) * 1.8)))
    soft_warnings = list(hard_soft_eval.get("soft_warnings") or body_generation.get("soft_warnings") or [])
    metrics: dict[str, Any] = {
        "run_id": run_id,
        "source_profile_id": source_profile_id,
        "elapsed_sec": round(elapsed_sec, 2),
        "success": bool(result.get("success")),
        "runtime_reason_code": str(result.get("runtime_reason_code") or result.get("reason_code") or ""),
        "fail_closed_reason": str(error.get("message") or result.get("message") or ""),
        "repair_required": _repair_required(body_generation, hard_soft_eval, repair),
        "repair_applied": repair_applied,
        "repair_rejected": _repair_rejected(body_generation, repair, repair_applied),
        "repair_reject_reason": repair_reject_reason,
        "output_guard_reasons": list(output_guard.get("reasons") or result.get("output_guard_reasons") or []),
        "soft_warning_count": len(soft_warnings),
        "soft_warnings": soft_warnings,
        "length_mode": length_mode,
        "target_chars": final_target,
        "target_chars_observed": observed_target,
        "target_chars_estimated": estimated_target,
        "max_tokens": observed_max_tokens if isinstance(observed_max_tokens, int) else estimated_max_tokens,
        "max_tokens_observed": observed_max_tokens,
        "max_tokens_estimated": estimated_max_tokens,
        "source_document_count": len(source_documents),
        "source_total_chars": sum(_char_len(doc.get("content")) for doc in source_documents),
        "grounding_item_count": len(list(input_contract.get("source_grounding_items") or [])),
        "must_cover_count": len(list(input_contract.get("must_cover") or [])),
        "body_chars": len(body),
        "body_chars_to_target_chars": round(len(body) / final_target, 4) if isinstance(final_target, int) and final_target else "not available",
        "title_chars": len(str(result.get("title") or "")),
        "lead_chars": len(str(result.get("lead") or "")),
        "repair_candidate_summary": dict(repair.get("repair_candidate_summary") or {}),
        "repair_candidate_source_slot_coverage": dict(repair.get("repair_candidate_source_slot_coverage") or {}),
    }
    metrics.update(packet_summary)
    metrics.update(_packet_fact_reflection(packet_summary.get("source_packet_facts") or [], body))
    metrics.update(_section_metrics(body))
    metrics.update(_slot_metrics(coverage))
    metrics.update(_internal_leakage(output_text))
    metrics["codex_visible_eval"] = _visible_eval(metrics)
    metrics["thinness_classification"] = _thinness_classification(metrics)
    metrics["note_article_judgment"] = _note_judgment(metrics)
    return metrics


def _write_run_files(out_dir: Path, run_id: str, result: Mapping[str, Any], metrics: Mapping[str, Any]) -> None:
    (out_dir / f"{run_id}.raw_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / f"{run_id}.metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    excerpt = _output_text(result)
    if len(excerpt) > 2600:
        excerpt = excerpt[:2600] + "\n...[truncated]\n"
    (out_dir / f"{run_id}.visible_excerpt.txt").write_text(excerpt, encoding="utf-8")
    if not metrics.get("success"):
        (out_dir / f"{run_id}.error.txt").write_text(
            str(metrics.get("fail_closed_reason") or metrics.get("runtime_reason_code") or ""),
            encoding="utf-8",
        )


def _write_summary(out_dir: Path, created_at: datetime, rows: list[dict[str, Any]]) -> None:
    body_lengths = [int(row["body_chars"]) for row in rows if row.get("success")]
    summary = {
        "created_at": created_at.isoformat(),
        "run_count": len(rows),
        "success_count": sum(1 for row in rows if row.get("success")),
        "failure_count": sum(1 for row in rows if not row.get("success")),
        "body_chars_success": body_lengths,
        "body_chars_success_avg": round(sum(body_lengths) / len(body_lengths), 2) if body_lengths else 0,
        "thinness_counts": {
            key: sum(1 for row in rows if row.get("thinness_classification") == key)
            for key in sorted({str(row.get("thinness_classification")) for row in rows})
        },
        "note_judgment_counts": {
            key: sum(1 for row in rows if row.get("note_article_judgment") == key)
            for key in sorted({str(row.get("note_article_judgment")) for row in rows})
        },
        "rows": rows,
    }
    (out_dir / "metrics.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    lines = [
        "# Company Intro Length Source Diagnosis",
        "",
        f"- Created: {created_at.isoformat()}",
        f"- Runs: {len(rows)}",
        f"- Success: {summary['success_count']}",
        f"- Failure: {summary['failure_count']}",
        f"- Success body chars avg: {summary['body_chars_success_avg']}",
        "",
        "| run_id | success | reason | target | body | ratio | packet | slots | sections | shortest/final | repair | eval | thinness | note |",
        "|---|---|---|---:|---:|---:|---:|---|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        slot_cov = row.get("source_slot_coverage")
        if isinstance(slot_cov, Mapping):
            slot_label = f"{slot_cov.get('covered')}/{slot_cov.get('required')}"
        else:
            slot_label = "n/a"
        repair = f"req={row.get('repair_required')}, applied={row.get('repair_applied')}, rejected={row.get('repair_rejected')}"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("run_id")),
                    str(row.get("success")),
                    str(row.get("runtime_reason_code")),
                    str(row.get("target_chars")),
                    str(row.get("body_chars")),
                    str(row.get("body_chars_to_target_chars")),
                    str(row.get("source_packet_chars")),
                    slot_label,
                    str(row.get("section_count")),
                    f"{row.get('shortest_section_chars')}/{row.get('final_section_chars')}",
                    repair,
                    str(row.get("codex_visible_eval")),
                    str(row.get("thinness_classification")),
                    str(row.get("note_article_judgment")),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## Thinness Counts")
    lines.append("")
    for key, count in summary["thinness_counts"].items():
        lines.append(f"- `{key}`: {count}")
    (out_dir / "metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose company introduction length/source adequacy.")
    parser.add_argument("--runs", type=int, default=15)
    parser.add_argument("--out-dir", type=str, default="")
    parser.add_argument("--source-profile-id", type=str, default="kyotokogyo_source_rich_v1")
    args = parser.parse_args()

    created_at = datetime.now(ZoneInfo("Asia/Tokyo"))
    out_dir = (
        Path(args.out_dir)
        if args.out_dir
        else ROOT / "logs" / f"{DEFAULT_LOG_PREFIX}_{created_at:%Y%m%d-%H%M%S}"
    )
    out_dir.mkdir(parents=True, exist_ok=False)
    if args.source_profile_id not in SOURCE_PROFILES:
        known = ", ".join(sorted(SOURCE_PROFILES))
        raise SystemExit(f"unknown source profile: {args.source_profile_id}; known: {known}")
    profile = SOURCE_PROFILES[args.source_profile_id]
    user_prompt = str(profile.get("prompt") or "")
    payload = _build_payload(args.source_profile_id, profile)
    pipeline = MinimalPipeline(llm_client=LLMClient())
    rows: list[dict[str, Any]] = []
    jsonl_path = out_dir / "metrics.jsonl"
    for index in range(1, max(0, int(args.runs)) + 1):
        run_id = f"{args.source_profile_id}__run{index:02d}"
        started = time.time()
        try:
            result = execute_current_mainline_generation(pipeline, dict(payload), user_prompt)
        except Exception as exc:  # noqa: BLE001 - diagnosis runner must preserve failed runs.
            result = {
                "success": False,
                "runtime_reason_code": "EXCEPTION",
                "message": repr(exc),
                "pipeline_check": {"input_contract": dict(payload), "error": {"message": repr(exc)}},
            }
        metrics = _result_metrics(
            run_id=run_id,
            source_profile_id=args.source_profile_id,
            result=result,
            payload=payload,
            elapsed_sec=time.time() - started,
        )
        rows.append(metrics)
        _write_run_files(out_dir, run_id, result, metrics)
        with jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(metrics, ensure_ascii=False, default=str) + "\n")
        print(json.dumps({
            "run_id": run_id,
            "success": metrics["success"],
            "reason": metrics["runtime_reason_code"],
            "body_chars": metrics["body_chars"],
            "target_chars": metrics["target_chars"],
            "thinness": metrics["thinness_classification"],
        }, ensure_ascii=True), flush=True)
    _write_summary(out_dir, created_at, rows)
    print(f"SUMMARY {out_dir / 'metrics.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
