from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from dotenv import load_dotenv  # noqa: E402
from openai import OpenAI  # noqa: E402

import run_persona_anchor_trigger_shadow_route as anchor_route  # noqa: E402
import run_reasoning_effort_minimal_shadow_route as base  # noqa: E402
from core.app_config import get_llm_config  # noqa: E402


ROUTE_ID = "compact_persona_surface_writer_shadow_v1"
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "logs"
    / "shadow_autonomous_20260504-233916"
    / "routes"
    / "compact_persona_surface_writer_live_20260506"
)


def _now_jst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S JST")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protected_hashes() -> dict[str, str]:
    return {rel: _sha256(PROJECT_ROOT / rel) for rel in base.PROTECTED_FILES}


def _model() -> str:
    config = get_llm_config()
    return str(dict(config.task_models or {}).get("section") or config.model_name or "")


def _sdk_capability() -> dict[str, bool]:
    sig = inspect.signature(OpenAI(api_key="dummy").chat.completions.create)
    return {
        "has_reasoning_effort": "reasoning_effort" in sig.parameters,
        "has_extra_body": "extra_body" in sig.parameters,
    }


def _prompt(contract: dict[str, Any]) -> str:
    return f"""voice:
会社運営ブログの編集者。会社を代弁しない。読者の手元の作業から書く。会社名は取材対象として扱う。

write:
保存済みsourceだけで、company_introduction のブログ記事を1本。
JSONやtitle/bodyラベルを出さず、普通のMarkdown本文として出力。
会社の一人称は使わない。
長い見出しで事業紹介を並べない。
最後は、相談前に何を決めると話が進むかで終える。

source:
{anchor_route._source_brief(contract)}
""".strip()


def _extract_text(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""
    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", "")
    return content.strip() if isinstance(content, str) else str(content or "").strip()


def _call(prompt: str, model: str, capability: dict[str, bool]) -> str:
    params: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 3200,
    }
    if capability["has_reasoning_effort"]:
        params["reasoning_effort"] = "none"
    elif capability["has_extra_body"]:
        params["extra_body"] = {"reasoning_effort": "none"}
    return _extract_text(OpenAI(timeout=120).chat.completions.create(**params))


def _visual_issues(text: str) -> list[str]:
    issues: list[str] = []
    if any(x in text for x in ("私たち", "弊社", "自社")):
        issues.append("company_first_person")
    if any(x in text for x in ("効く", "第一歩", "重要です", "大切です", "と言えるでしょう", "以下では")):
        issues.append("gpt_frequent_phrase")
    if any(x in text for x in ("について紹介", "選ばれる理由", "信頼されています")):
        issues.append("brochure_phrase")
    stripped = text.lstrip()
    if stripped.startswith("{") or '"title"' in stripped[:200] or "title:" in stripped[:80] or "body:" in stripped[:160]:
        issues.append("structured_envelope")
    return issues


def _write_compare(root: Path, report: dict[str, Any]) -> None:
    score = report.get("score") or {}
    lines = [
        "# Route A Visual Compare: compact_persona_surface_writer_shadow_v1",
        "",
        f"Date: {report['date_jst']}",
        "",
        "## Decision",
        "",
        report.get("decision", "blocked"),
        "",
        "## Scope",
        "",
        f"- Shadow route: `{ROUTE_ID}`",
        f"- Case: `{report['case_id']}`",
        f"- Source snapshot hash: `{report['source_snapshot_hash']}`",
        "- Route A/default route: unchanged",
        "- Adoption: not started",
        "- Editor/repair/regeneration: not used",
        "",
        "## Score",
        "",
        f"- body char count: `{score.get('body_char_count')}`",
        f"- GPT frequent term hits: `{score.get('gpt_frequent_term_hits')}`",
        f"- first-person company hits: `{score.get('first_person_company_hits')}`",
        f"- ending bucket max run: `{score.get('ending_bucket_max_run')}`",
        f"- body length target result: `{score.get('body_length_target_result')}`",
        f"- visual issues: `{report.get('visual_issues')}`",
        "",
        "## Judgment",
        "",
        "This route tests whether a compact persona voice card can improve the single-pass writer without Route A changes.",
    ]
    base._write_text(root / "route_a_visual_compare_20260506.md", "\n".join(lines) + "\n")


def _write_failure_note(root: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Failure Note: compact_persona_surface_writer_shadow_v1",
        "",
        f"Date: {report['date_jst']}",
        "",
        "## Decision",
        "",
        "reject",
        "",
        "## Why It Failed",
        "",
        f"- score: `{report.get('score')}`",
        f"- visual_issues: `{report.get('visual_issues')}`",
        "- accepted clean shadow route remains absent",
        "",
        "## Do Not Repeat",
        "",
        "- Do not add more persona text to rescue this route.",
        "- Do not add editor, regeneration, Best-of-N, threshold relaxation, fallback, mock, or dummy output.",
        "- Do not move this into Route A.",
    ]
    base._write_text(root / "failure_note.md", "\n".join(lines) + "\n")


def run(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    case = anchor_route._load_case()
    contract = case["contract"]
    source_path = base._write_json(root / "source_snapshot.json", contract)
    base._write_json(root / "route_a_snapshot.json", case["route_a"])
    prompt = _prompt(contract)
    base._write_text(root / "writer_prompt_preview.txt", prompt)
    model = _model()
    capability = _sdk_capability()
    issues = []
    if case["case_id"] != "latest_ui_route_a_gen-453da287":
        issues.append("case_id_not_latest_ui_route_a_gen-453da287")
    if contract.get("article_type") != "branding":
        issues.append("article_type_not_branding")
    if contract.get("semantic_article_key") != "company_introduction":
        issues.append("semantic_article_key_not_company_introduction")
    report: dict[str, Any] = {
        "route_id": ROUTE_ID,
        "date_jst": _now_jst(),
        "mode": "one-source compact-persona single-pass live validation",
        "status": "blocked" if issues else "started",
        "case_id": case["case_id"],
        "source_snapshot_hash": _sha256(source_path),
        "writer_prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "writer_prompt_chars": len(prompt),
        "configured_generation_model": model,
        "validation_issues": issues,
        "external_llm_send": False,
        "live_generation_started": False,
        "adoption_started": False,
        "route_a_changed": False,
        "default_route_changed": False,
        "repair_added_to_route_a": False,
        "editor_added_to_route_a": False,
        "threshold_relaxed": False,
        "fallback_mock_dummy_used": False,
        "best_of_n_used": False,
        "free_prose_first_used": False,
        "protected_hashes": _protected_hashes(),
    }
    if issues:
        base._write_json(root / "live_report.json", report)
        return report
    try:
        load_dotenv(PROJECT_ROOT / ".env")
        text = _call(prompt, model, capability)
    except Exception as exc:
        report.update(
            {
                "status": "blocked",
                "blocked_reason": str(exc),
                "external_llm_send": True,
                "live_generation_started": True,
            }
        )
        base._write_json(root / "live_report.json", report)
        return report
    score = base._score_body(text)
    visual_issues = _visual_issues(text)
    clean = (
        score["body_length_target_result"] == "ok"
        and not score["gpt_frequent_term_hits"]
        and not score["first_person_company_hits"]
        and not score["ending_bucket_monotony"]
        and not score["third_party_intro_tone"]
        and not score["textbook_explanation_tone"]
        and not visual_issues
    )
    report.update(
        {
            "status": "completed",
            "decision": "continue_shadow" if clean else "reject",
            "external_llm_send": True,
            "live_generation_started": True,
            "score": score,
            "visual_issues": visual_issues,
        }
    )
    base._write_text(root / "latest_generation_output.txt", text + "\n")
    base._write_json(root / "latest_generation_output.json", {"text": text})
    _write_compare(root, report)
    if report["decision"] == "reject":
        _write_failure_note(root, report)
    base._write_json(root / "live_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in compact persona surface writer shadow route.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run(Path(args.output_root))
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"{report['status']}: {args.output_root}")
    return 0 if report["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
