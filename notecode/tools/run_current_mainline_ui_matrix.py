from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(PROJECT_ROOT))

from note.current_mainline_ui_matrix import (  # noqa: E402
    build_promoted_long_cases,
    get_short_sweep_cases,
    run_ui_sweep_cases,
    summarize_promoted_case_ids,
)


def _default_output_path(phase: str) -> Path:
    return PROJECT_ROOT / "logs" / f"current_mainline_ui_{phase}_matrix_latest.json"


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _build_live_artifact_dir(phase: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return PROJECT_ROOT / "logs" / "current_mainline_ui_runs" / f"{timestamp}-{phase}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run current mainline UI selection matrix.")
    parser.add_argument("--phase", choices=("short", "long"), default="short")
    parser.add_argument("--live", action="store_true", help="Use live OpenAI execution.")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout.")
    parser.add_argument("--output", type=str, default="", help="Optional JSON output path.")
    parser.add_argument(
        "--promote-from",
        type=str,
        default="",
        help="Short phase result JSON path. Required for --phase long.",
    )
    args = parser.parse_args()

    short_cases = get_short_sweep_cases()
    artifact_dir = _build_live_artifact_dir(args.phase) if args.live else None
    if args.phase == "short":
        payload = run_ui_sweep_cases(short_cases, live=bool(args.live), artifact_dir=artifact_dir)
    else:
        if not args.promote_from:
            raise SystemExit("--phase long requires --promote-from <short_result.json>")
        short_results = _load_json(args.promote_from)
        promoted_bundle = build_promoted_long_cases(short_results, short_cases)
        if bool(promoted_bundle.get("promotion_blocked", False)):
            raise SystemExit(
                "long promotion blocked"
                f" (reason={promoted_bundle.get('block_reason') or 'unknown'}"
                f", owner={promoted_bundle.get('blocker_owner') or 'unknown'})"
            )
        promoted_cases = promoted_bundle["promoted_cases"]
        payload = run_ui_sweep_cases(promoted_cases, live=bool(args.live), artifact_dir=artifact_dir)
        payload["matrix"] = "ui_promoted_long_sweep"
        payload["promotion"] = {
            "source": str(args.promote_from),
            "promoted_case_ids": summarize_promoted_case_ids(promoted_cases),
            "skipped": list(promoted_bundle["skipped"]),
        }

    payload["phase"] = args.phase
    payload["generated_at"] = datetime.now().isoformat(timespec="seconds")

    output_path = Path(args.output) if args.output else _default_output_path(args.phase)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    payload["saved_to"] = str(output_path)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if payload.get("matrix_status") == "blocked_preflight":
            preflight = dict(payload.get("preflight") or {})
            print(f"phase={payload['phase']} cases=0 live={payload['live']} matrix_status=blocked_preflight")
            print(f"saved_to={output_path}")
            print(f"blocker_owner={preflight.get('blocker_owner') or 'unknown'}")
            print(
                "section_probe_reason="
                f"{dict(preflight.get('section_probe') or {}).get('reason_code') or 'unknown'}"
            )
            print(
                "base_probe_reason="
                f"{dict(preflight.get('base_probe') or {}).get('reason_code') or dict(preflight.get('base_probe') or {}).get('reason') or 'unknown'}"
            )
            return 2
        print(f"phase={payload['phase']} cases={len(payload['results'])} live={payload['live']}")
        print(f"saved_to={output_path}")
        passed = sum(1 for item in payload["results"] if bool(dict(item.get("short_gate", {}) or {}).get("passed", False)))
        print(f"short_gate_passed={passed}/{len(payload['results'])}")
        battery_summary = dict(payload.get("battery_summary") or {})
        if battery_summary:
            print(
                "battery_go_for_long_form="
                f"{bool(battery_summary.get('go_for_long_form', False))}"
            )
            print(
                "battery_rubric_mean_total="
                f"{battery_summary.get('rubric_mean_total')}"
            )
            runtime_contract = dict(battery_summary.get("runtime_contract") or {})
            if runtime_contract:
                print(
                    "runtime_models="
                    f"{','.join(runtime_contract.get('selected_models') or []) or 'unknown'}"
                )
            if battery_summary.get("go_no_go_reasons"):
                print(
                    "battery_blockers="
                    + " | ".join(str(item) for item in list(battery_summary.get("go_no_go_reasons") or []))
                )
        for item in payload["results"]:
            print(
                f"- {item['case_id']}: success={item['success']} "
                f"reason={item['reason_code']} short_gate={dict(item.get('short_gate', {}) or {}).get('passed', False)} "
                f"rubric={dict(item.get('rubric', {}) or {}).get('total_score', 0)}/10 "
                f"long_form={dict(item.get('long_form_case_gate', {}) or {}).get('passed', False)}"
            )
    if payload.get("matrix_status") == "blocked_preflight":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
