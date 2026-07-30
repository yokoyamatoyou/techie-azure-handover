from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from dotenv import load_dotenv  # noqa: E402
from openai import OpenAI  # noqa: E402

import run_reasoning_effort_minimal_shadow_route as base  # noqa: E402


ROUTE_ID = "voice_first_fact_second_shadow_v1"
MODEL_NAME = "gpt-5.4-mini"
REQUESTED_REASONING_EFFORT = "none"
REQUESTED_VERBOSITY = "medium"
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "logs"
    / "shadow_autonomous_20260504-233916"
    / "routes"
    / "voice_first_fact_second_live_20260506"
)
FIRST_PERSON_COMPANY = ("私たち", "自社", "弊社")
UNSUPPORTED_VOICE_TERMS = ("京都工業", "自治体", "大学", "1885", "1968", "RPA", "ISMS", "プライバシーマーク")


def _route_report(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    report, _ = base._base_report(root)
    report["route_id"] = ROUTE_ID
    report["configured_generation_model"] = MODEL_NAME
    report["requested_reasoning_effort"] = REQUESTED_REASONING_EFFORT
    report["requested_verbosity"] = REQUESTED_VERBOSITY
    report["sdk_capability"] = base._sdk_capability(MODEL_NAME)
    report["status"] = "ready_for_live_approval" if not report["validation_issues"] else "blocked"
    case = base._load_case()
    return report, case["contract"]


def _voice_prompt() -> str:
    return (
        "次に書く会社ブログの冒頭の声だけを、120〜160字で作ってください。\n"
        "まだ会社名・実績・サービス名・数字・固有名詞は出さない。\n"
        "紙や入力作業を、次の業務で使える形に整える話題です。\n"
        "会社を一人称にしない。読者に近すぎず、少し話しかける距離で。\n"
        "出力は本文だけ。"
    )


def _source_brief(contract: dict[str, Any], *, per_source_chars: int = 2600) -> str:
    return base._source_brief(contract, per_source_chars=per_source_chars)


def _article_prompt(contract: dict[str, Any], voice: str) -> str:
    source = _source_brief(contract)
    return f"""保存済みsourceだけを根拠に、日本語のブログ記事を1本書いてください。
対象は branding / company_introduction です。

先に作った声:
{voice}

声の扱い:
- これは文体と距離感の anchor であり、事実根拠ではない。
- 同じ語句をコピーしなくてよい。
- 会社を一人称にしない。「私たち」「自社」「弊社」は使わない。

守ること:
- source外の事実を足さない。
- 会社紹介パンフレットではなく、読者が業務を考える時に読むブログとして書く。
- 参考情報は本文に混ぜず、最後に必要最小限で置く。

source:
{source}

出力はタイトル、リード、本文、ハッシュタグだけ。""".strip()


def _request_text(prompt: str, *, max_tokens: int) -> str:
    params = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": max_tokens,
        "extra_body": {
            "reasoning_effort": REQUESTED_REASONING_EFFORT,
            "verbosity": REQUESTED_VERBOSITY,
        },
    }
    response = OpenAI(timeout=120).chat.completions.create(**params)
    return base._extract_text(response)


def _voice_issues(voice: str) -> list[str]:
    issues: list[str] = []
    if len(voice) < 80 or len(voice) > 220:
        issues.append("voice_length_out_of_range")
    if any(term in voice for term in FIRST_PERSON_COMPANY):
        issues.append("voice_contains_company_first_person")
    if any(term in voice for term in UNSUPPORTED_VOICE_TERMS):
        issues.append("voice_contains_specific_fact_or_name")
    if re.search(r"https?://|#|タイトル|リード|本文", voice):
        issues.append("voice_contains_format_artifact")
    return issues


def run_preflight(root: Path) -> dict[str, Any]:
    report, contract = _route_report(root)
    base._write_json(root / "source_snapshot.json", contract)
    base._write_json(root / "preflight_report.json", report)
    base._write_text(root / "voice_prompt_preview.txt", _voice_prompt())
    base._write_text(root / "article_prompt_preview.txt", _article_prompt(contract, "<voice sample>"))
    base._write_text(
        root / "blocked_or_ready.md",
        f"# {ROUTE_ID} preflight\n\n- status: `{report['status']}`\n- case_id: `{report['case_id']}`\n- live_generation_started: `false`\n",
    )
    return report


def run_live(root: Path) -> dict[str, Any]:
    report, contract = _route_report(root)
    report["mode"] = "one-source live validation"
    base._write_json(root / "source_snapshot.json", contract)
    if report["status"] == "blocked":
        base._write_json(root / "live_report.json", report)
        return report
    load_dotenv(PROJECT_ROOT / ".env")
    try:
        voice = _request_text(_voice_prompt(), max_tokens=260).strip()
    except Exception as exc:
        report.update({"status": "blocked", "blocked_reason": str(exc), "live_generation_started": True, "stage": "voice"})
        base._write_json(root / "live_report.json", report)
        return report
    base._write_text(root / "voice_sample.txt", voice + "\n")
    issues = _voice_issues(voice)
    if issues:
        report.update({"status": "blocked", "blocked_reason": ",".join(issues), "live_generation_started": True, "stage": "voice_validation"})
        base._write_json(root / "live_report.json", report)
        return report
    article_prompt = _article_prompt(contract, voice)
    base._write_text(root / "article_prompt_live.txt", article_prompt)
    try:
        text = _request_text(article_prompt, max_tokens=3000).strip()
    except Exception as exc:
        report.update({"status": "blocked", "blocked_reason": str(exc), "live_generation_started": True, "stage": "article"})
        base._write_json(root / "live_report.json", report)
        return report
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
            "voice_sample_chars": len(voice),
            "article_prompt_chars": len(article_prompt),
            "decision": "continue_shadow" if clean else "reject",
            "score": score,
            "repair_call_executed": False,
            "shadow_editor_call_executed": False,
            "fallback_used": False,
        }
    )
    base._write_text(root / "latest_generation_output.txt", text + "\n")
    base._write_json(root / "latest_generation_output.json", {"text": text})
    base._write_json(root / "live_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in voice-first/fact-second shadow route.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run_live(Path(args.output_root)) if args.live else run_preflight(Path(args.output_root))
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"{report['status']}: {args.output_root}")
    return 0 if report["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
