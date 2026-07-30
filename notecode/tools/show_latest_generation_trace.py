from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_PATH = PROJECT_ROOT / "logs" / "latest_generation_output.json"
DEFAULT_AUDIT_PATH = PROJECT_ROOT / "logs" / "generation_audit_log.jsonl"
STAGE_OWNERS = {
    "contract_resolve": "note.newalgorithm_pipeline.input_contract.resolve_input_contract",
    "discourse_plan": "note.newalgorithm_pipeline.discourse_planner.build_discourse_plan",
    "section_generation": "note.newalgorithm_pipeline.section_generator.generate_sections",
    "dedupe": "note.newalgorithm_pipeline.dedupe_adapter.run_semantic_dedupe",
    "editor_guard": "note.newalgorithm_pipeline.editor_guard.apply_minimal_editor_guard",
    "resonance": "human_resonance.pipeline.HumanResonancePipeline.process",
    "quality_pipeline": "human_resonance2.quality_pipeline.QualityPipeline.process",
    "legal_postcheck": "note.newalgorithm_pipeline.legal_postcheck.run_legal_postcheck",
    "output_format": "note.newalgorithm_pipeline.output_formatter.format_output",
    "telemetry": "note.newalgorithm_pipeline.telemetry_writer.build_pipeline_check",
}


def _to_plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _to_plain_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _load_json(path: Path) -> Dict[str, Any]:
    return _to_plain_dict(json.loads(path.read_text(encoding="utf-8")))


def _load_last_jsonl(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return {}
    return _to_plain_dict(json.loads(lines[-1]))


def _build_algorithm_trace(payload: Dict[str, Any]) -> Dict[str, Any]:
    trace = _to_plain_dict(payload.get("algorithm_trace"))
    if trace:
        return trace
    pipeline = _to_plain_dict(payload.get("pipeline_check"))
    io_contract = _to_plain_dict(pipeline.get("io_contract"))
    return {
        "stage_order": list(io_contract.keys()),
        "stages": [
            {
                "stage": str(stage_name),
                "owner": STAGE_OWNERS.get(str(stage_name), ""),
                "inputs": _to_plain_list(_to_plain_dict(io_shape).get("in")),
                "outputs": _to_plain_list(_to_plain_dict(io_shape).get("out")),
            }
            for stage_name, io_shape in io_contract.items()
        ],
        "discourse_section_count": len(_to_plain_list(pipeline.get("discourse_plan"))),
        "discourse_headings": [
            str(item.get("heading") or "")
            for item in _to_plain_list(pipeline.get("discourse_plan"))
            if isinstance(item, dict) and str(item.get("heading") or "").strip()
        ],
    }


def _print_stage_trace(trace: Dict[str, Any]) -> None:
    print("[algorithm_trace]")
    print("stage_order:", " -> ".join(str(item) for item in trace.get("stage_order", [])) or "-")
    for stage in _to_plain_list(trace.get("stages")):
        stage_dict = _to_plain_dict(stage)
        summary = _to_plain_dict(stage_dict.get("summary"))
        summary_text = ""
        if summary:
            compact_items = []
            for key, value in summary.items():
                compact_items.append(f"{key}={value}")
            summary_text = " summary=" + ", ".join(compact_items[:5])
        print(
            f"- {stage_dict.get('stage', '-')}: "
            f"owner={stage_dict.get('owner', '-') or '-'} "
            f"in={','.join(str(x) for x in _to_plain_list(stage_dict.get('inputs'))) or '-'} "
            f"out={','.join(str(x) for x in _to_plain_list(stage_dict.get('outputs'))) or '-'}"
            f"{summary_text}"
        )


def _print_discourse(payload: Dict[str, Any]) -> None:
    discourse = _to_plain_list(_to_plain_dict(payload.get("pipeline_check")).get("discourse_plan"))
    print("[discourse_plan]")
    for idx, item in enumerate(discourse, start=1):
        section = _to_plain_dict(item)
        heading = str(section.get("heading") or f"section_{idx}")
        intent = str(section.get("intent") or section.get("objective") or "")
        topic_seed = str(section.get("topic_seed") or "")
        must_cover = " / ".join(str(x) for x in _to_plain_list(section.get("must_cover"))[:3]) or "-"
        print(f"- {idx}. {heading} | intent={intent} | topic_seed={topic_seed or '-'} | must_cover={must_cover}")


def _print_metrics(payload: Dict[str, Any]) -> None:
    quality_metrics = _to_plain_dict(_to_plain_dict(payload.get("pipeline_check")).get("quality_metrics"))
    print("[quality_metrics]")
    for key in (
        "topic_echo_body_only_ratio",
        "section_opening_repetition_count",
        "sentence_integrity_warning_count",
        "case_result_change_sentence_count",
        "case_result_condition_sentence_count",
        "comparative_fit_sentence_count",
        "comparative_absolute_winner_claim_count",
        "comparative_axis_shift_count",
        "abstract_example_fallback_count",
        "example_specificity_count",
    ):
        if key in quality_metrics:
            print(f"- {key}: {quality_metrics.get(key)}")


def _print_audit_summary(audit: Dict[str, Any]) -> None:
    if not audit:
        print("[audit] -")
        return
    output_metrics = _to_plain_dict(audit.get("output_metrics"))
    print("[audit]")
    print(
        "reason_code:",
        str(audit.get("runtime_reason_code") or audit.get("reason_code") or "-"),
    )
    print("status:", str(audit.get("status") or "-"))
    print("body_chars:", int(output_metrics.get("body_chars", 0) or 0))
    algorithm_trace = _to_plain_dict(audit.get("algorithm_trace"))
    if algorithm_trace:
        stage_order = " -> ".join(str(x) for x in _to_plain_list(algorithm_trace.get("stage_order")))
        print("audit_stage_order:", stage_order or "-")


def main() -> int:
    parser = argparse.ArgumentParser(description="Show latest current mainline stage trace and audit summary.")
    parser.add_argument("--json-path", default=str(DEFAULT_JSON_PATH))
    parser.add_argument("--audit-path", default=str(DEFAULT_AUDIT_PATH))
    args = parser.parse_args()

    json_path = Path(args.json_path)
    audit_path = Path(args.audit_path)
    payload = _load_json(json_path)
    audit = _load_last_jsonl(audit_path)

    print("[latest_generation]")
    print("json_path:", json_path)
    print("audit_path:", audit_path)
    print("attempt_id:", str(payload.get("attempt_id") or "-"))
    print("article_type:", str(payload.get("article_type") or "-"))
    print("runtime_reason_code:", str(payload.get("runtime_reason_code") or "-"))
    print("runtime_error_class:", str(payload.get("runtime_error_class") or "-"))
    _print_stage_trace(_build_algorithm_trace(payload))
    _print_discourse(payload)
    _print_metrics(payload)
    _print_audit_summary(audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
