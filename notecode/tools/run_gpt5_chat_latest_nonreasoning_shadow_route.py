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


ROUTE_ID = "gpt5_chat_latest_nonreasoning_shadow_v1"
MODEL_NAME = "gpt-5-chat-latest"
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "logs"
    / "shadow_autonomous_20260504-233916"
    / "routes"
    / "gpt5_chat_latest_nonreasoning_live_20260506"
)


def _as_route_report(report: dict[str, Any]) -> dict[str, Any]:
    report["route_id"] = ROUTE_ID
    report["configured_generation_model"] = MODEL_NAME
    report["requested_reasoning_effort"] = "not_sent"
    report["requested_verbosity"] = "not_sent"
    report["sdk_capability"] = base._sdk_capability(MODEL_NAME)
    report["validation_issues"] = [
        issue
        for issue in report.get("validation_issues", [])
        if issue != "configured_model_does_not_support_reasoning_prefix"
    ]
    report["status"] = "ready_for_live_approval" if not report["validation_issues"] else "blocked"
    return report


def _base_report(root: Path) -> tuple[dict[str, Any], str]:
    report, prompt = base._base_report(root)
    return _as_route_report(report), prompt


def run_preflight(root: Path) -> dict[str, Any]:
    report, _ = _base_report(root)
    base._write_json(root / "preflight_report.json", report)
    base._write_text(
        root / "blocked_or_ready.md",
        "\n".join(
            [
                "# gpt5_chat_latest_nonreasoning_shadow_v1 preflight",
                "",
                f"- status: `{report['status']}`",
                f"- route_id: `{ROUTE_ID}`",
                f"- case_id: `{report['case_id']}`",
                f"- configured_generation_model: `{MODEL_NAME}`",
                "- requested_reasoning_effort: `not_sent`",
                "- live_generation_started: `false`",
                f"- validation_issues: `{', '.join(report['validation_issues']) if report['validation_issues'] else 'none'}`",
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
    try:
        response = OpenAI(timeout=120).chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=3000,
        )
    except Exception as exc:
        report.update(
            {
                "status": "blocked",
                "blocked_reason": str(exc),
                "live_generation_started": True,
                "model_fallback_used": False,
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
            "model_fallback_used": False,
        }
    )
    base._write_text(root / "latest_generation_output.txt", text + "\n")
    base._write_json(root / "latest_generation_output.json", {"text": text})
    base._write_json(root / "live_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in gpt-5-chat-latest non-reasoning shadow route.")
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
