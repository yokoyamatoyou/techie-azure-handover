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

import run_reasoning_effort_minimal_shadow_route as base  # noqa: E402
from core.app_config import get_llm_config  # noqa: E402


ROUTE_ID = "referent_controller_blog_schema_shadow_v1"
SOURCE_LOG = PROJECT_ROOT / "logs" / "latest_generation_output.json"
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "logs"
    / "shadow_autonomous_20260504-233916"
    / "routes"
    / "referent_controller_blog_schema_live_20260506"
)


def _now_jst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S JST")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protected_hashes() -> dict[str, str]:
    return {rel: _sha256(PROJECT_ROOT / rel) for rel in base.PROTECTED_FILES}


def _load_case() -> dict[str, Any]:
    payload = json.loads(SOURCE_LOG.read_text(encoding="utf-8"))
    contract = dict(payload.get("input_contract") or {})
    contract.setdefault("article_type", payload.get("article_type") or "")
    contract.setdefault("semantic_article_key", payload.get("semantic_article_key") or "")
    return {
        "case_id": f"latest_ui_route_a_{payload.get('attempt_id') or 'latest'}",
        "contract": contract,
        "route_a": {
            "title": payload.get("title") or "",
            "lead": payload.get("lead") or "",
            "body": payload.get("body") or "",
            "hashtags": payload.get("hashtags") or "",
        },
    }


def _clean(text: Any) -> str:
    return " ".join(str(text or "").split())


def _source_brief(contract: dict[str, Any]) -> str:
    parts: list[str] = []
    for index, doc in enumerate(contract.get("source_documents") or [], start=1):
        title = _clean(doc.get("title") or f"source_{index}")
        locator = _clean(doc.get("locator") or "")
        content = _clean(doc.get("content") or "")
        if len(content) > 2200:
            content = content[:2200].rstrip() + "..."
        parts.append(f"[{index}] {title}\nURL: {locator}\n{content}")
    return "\n\n".join(parts)


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
    return f"""保存済みsourceだけを使って、日本語の会社運営ブログ記事を1本書く。
会社は話者ではなく、記事内のtopic entityとして扱う。会社名は必要な箇所だけ。私たち・弊社・自社は禁止。

内部の照応状態:
- lead: 読者の手元の紙や入力待ち情報をtopicにする。会社名を出さない。
- body: 直前段落のtopicを引き継げるときは主語を省く。会社名を連続主語にしない。
- workflow段落: ヒアリング、入力、チェック、納品、改善内容だけを扱う。
- concrete段落: アンケート、名刺、原稿、冊子、ハガキ、音声、スキャニング資料、市場調査、Webリサーチから自然につながるものだけを扱う。
- close: 相談前に何を決めるとよいかで静かに終える。歴史・信頼の総括で締めない。

出力条件:
- 内部状態や箇条書きは本文に出さない。
- 見出しは使わず、短めの段落で呼吸を作る。
- source外の事実は足さない。
- 「効く」「第一歩」「重要です」「大切です」「と言えるでしょう」「以下では」は使わない。
- 最後に参考情報とハッシュタグを置く。

source:
{_source_brief(contract)}""".strip()


def _extract_text(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""
    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", "")
    return content.strip() if isinstance(content, str) else str(content or "").strip()


def _visual_issues(text: str) -> list[str]:
    checks = {
        "internal_state_leaked": ("lead:" in text or "workflow段落" in text or "内部" in text),
        "company_first_person": any(x in text for x in ("私たち", "弊社", "自社")),
        "brochure_phrase": any(x in text for x in ("強み", "信頼されています", "選ばれる", "について紹介")),
        "gpt_frequent_phrase": any(x in text for x in ("効く", "第一歩", "重要です", "大切です", "と言えるでしょう", "以下では")),
    }
    return [key for key, value in checks.items() if value]


def _write_compare(root: Path, report: dict[str, Any]) -> None:
    score = report.get("score") or {}
    text = "\n".join(
        [
            "# Route A Visual Compare: referent_controller_blog_schema_shadow_v1",
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
            "- External LLM send: yes",
            "- Route A/default route: unchanged",
            "- Adoption: not started",
            "- Repair/editor/Best-of-N: not used",
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
            "## Comparison Judgment",
            "",
            "Route A remains the frozen reference. This shadow route is judged only as an opt-in candidate on the same saved source.",
        ]
    )
    base._write_text(root / "route_a_visual_compare_20260506.md", text + "\n")


def _write_failure_note(root: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Failure Note: referent_controller_blog_schema_shadow_v1",
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
        "- Do not rebrand this as another pronoun/self-perspective prompt.",
        "- Do not add repair, editor, threshold relaxation, Best-of-N, fallback, mock, or dummy output.",
        "- Do not move this into Route A.",
    ]
    base._write_text(root / "failure_note.md", "\n".join(lines) + "\n")


def run(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    case = _load_case()
    contract = case["contract"]
    source_path = base._write_json(root / "source_snapshot.json", contract)
    base._write_json(root / "route_a_snapshot.json", case["route_a"])
    prompt = _prompt(contract)
    base._write_text(root / "writer_prompt_preview.txt", prompt)
    issues: list[str] = []
    if case["case_id"] != "latest_ui_route_a_gen-453da287":
        issues.append("case_id_not_latest_ui_route_a_gen-453da287")
    if contract.get("article_type") != "branding":
        issues.append("article_type_not_branding")
    if contract.get("semantic_article_key") != "company_introduction":
        issues.append("semantic_article_key_not_company_introduction")
    capability = _sdk_capability()
    report: dict[str, Any] = {
        "route_id": ROUTE_ID,
        "date_jst": _now_jst(),
        "mode": "one-source referent-controller blog-schema live validation",
        "status": "blocked" if issues else "started",
        "case_id": case["case_id"],
        "source_snapshot_hash": _sha256(source_path),
        "writer_prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "writer_prompt_chars": len(prompt),
        "configured_generation_model": _model(),
        "sdk_capability": capability,
        "validation_issues": issues,
        "external_llm_send": False,
        "live_generation_started": False,
        "adoption_started": False,
        "route_a_changed": False,
        "default_route_changed": False,
        "repair_added": False,
        "editor_added": False,
        "threshold_relaxed": False,
        "fallback_mock_dummy_used": False,
        "best_of_n_used": False,
        "free_prose_first_used": False,
        "protected_hashes": _protected_hashes(),
    }
    if issues:
        base._write_json(root / "live_report.json", report)
        return report
    load_dotenv(PROJECT_ROOT / ".env")
    params: dict[str, Any] = {
        "model": report["configured_generation_model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 3000,
    }
    if capability["has_reasoning_effort"]:
        params["reasoning_effort"] = "none"
    elif capability["has_extra_body"]:
        params["extra_body"] = {"reasoning_effort": "none"}
    try:
        response = OpenAI(timeout=120).chat.completions.create(**params)
    except Exception as exc:
        report.update({"status": "blocked", "blocked_reason": str(exc), "external_llm_send": True, "live_generation_started": True})
        base._write_json(root / "live_report.json", report)
        return report
    text = _extract_text(response)
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
    parser = argparse.ArgumentParser(description="Opt-in referent-controller blog-schema shadow route.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run(Path(args.output_root))
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"{report['status']}: {args.output_root}")
    return 0 if report["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
