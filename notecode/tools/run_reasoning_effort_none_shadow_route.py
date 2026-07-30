from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from dotenv import load_dotenv  # noqa: E402
from openai import OpenAI  # noqa: E402

import run_reasoning_effort_minimal_shadow_route as base  # noqa: E402


ROUTE_ID = "reasoning_effort_none_shadow_arm_v1"
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "logs"
    / "shadow_autonomous_20260504-233916"
    / "routes"
    / "reasoning_effort_none_live_20260506"
)
REQUESTED_REASONING_EFFORT = "none"
REQUESTED_VERBOSITY = "medium"


def _as_none_report(report: dict[str, Any]) -> dict[str, Any]:
    report["route_id"] = ROUTE_ID
    report["requested_reasoning_effort"] = REQUESTED_REASONING_EFFORT
    return report


def _base_report(root: Path) -> tuple[dict[str, Any], str]:
    report, prompt = base._base_report(root)
    return _as_none_report(report), prompt


def run_preflight(root: Path) -> dict[str, Any]:
    report, _ = _base_report(root)
    base._write_json(root / "preflight_report.json", report)
    base._write_text(
        root / "blocked_or_ready.md",
        "\n".join(
            [
                "# reasoning_effort_none_shadow_arm_v1 preflight",
                "",
                f"- status: `{report['status']}`",
                f"- route_id: `{ROUTE_ID}`",
                f"- case_id: `{report['case_id']}`",
                f"- configured_generation_model: `{report['configured_generation_model']}`",
                "- requested_reasoning_effort: `none`",
                "- live_generation_started: `false`",
                f"- validation_issues: `{', '.join(report['validation_issues']) if report['validation_issues'] else 'none'}`",
                "- next: one-source live validation may run under the user's standing approval",
            ]
        )
        + "\n",
    )
    return report


def run_live(root: Path) -> dict[str, Any]:
    report, prompt = _base_report(root)
    report["mode"] = "one-source live validation"
    if report["status"] == "blocked":
        base._write_json(root / "live_report.json", report)
        return report
    load_dotenv(PROJECT_ROOT / ".env")
    request_params = {
        "model": report["configured_generation_model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 3000,
    }
    if report["sdk_capability"]["openai_sdk_chat_create_has_reasoning_effort"]:
        request_params["reasoning_effort"] = REQUESTED_REASONING_EFFORT
        request_params["verbosity"] = REQUESTED_VERBOSITY
    else:
        request_params["extra_body"] = {
            "reasoning_effort": REQUESTED_REASONING_EFFORT,
            "verbosity": REQUESTED_VERBOSITY,
        }
    try:
        response = OpenAI(timeout=120).chat.completions.create(**request_params)
    except Exception as exc:
        report.update(
            {
                "status": "blocked",
                "blocked_reason": str(exc),
                "live_generation_started": True,
                "reasoning_effort_fallback_used": False,
            }
        )
        base._write_json(root / "live_report.json", report)
        return report
    text = base._extract_text(response)
    score = base._score_body(text)
    clean = (
        score["body_length_target_result"] == "ok"
        and not score["gpt_frequent_term_hits"]
        and not score["first_person_company_hits"]
        and not score["ending_bucket_monotony"]
        and not score["third_party_intro_tone"]
        and not score["textbook_explanation_tone"]
    )
    report.update(
        {
            "status": "completed",
            "live_generation_started": True,
            "decision": "continue_shadow" if clean else "reject",
            "score": score,
            "repair_call_executed": False,
            "shadow_editor_call_executed": False,
            "reasoning_effort_fallback_used": False,
        }
    )
    base._write_text(root / "latest_generation_output.txt", text + "\n")
    base._write_json(root / "latest_generation_output.json", {"text": text})
    base._write_json(root / "live_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in reasoning_effort=none shadow route.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.output_root)
    report = run_live(root) if args.live else run_preflight(root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['status']}: {root}")
    return 0 if report["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
