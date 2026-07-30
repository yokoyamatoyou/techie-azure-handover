from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import re
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


ROUTE_ID = "persona_anchor_trigger_shadow_v1"
SOURCE_LOG = PROJECT_ROOT / "logs" / "latest_generation_output.json"
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "logs"
    / "shadow_autonomous_20260504-233916"
    / "routes"
    / "persona_anchor_trigger_live_20260506"
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
        if len(content) > 1900:
            content = content[:1900].rstrip() + "..."
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


def _writer_prompt(contract: dict[str, Any]) -> str:
    return f"""persona:
会社運営ブログの編集者。会社を代弁しない。読者の手元の業務から考える。会社名は取材対象として扱う。

meaning anchors:
後半に、相談前に決めること、入力から納品までの流れ、データ化後の使い道を自然に残す。

task:
保存済みsourceだけで company_introduction のブログ記事を書く。私たち・弊社・自社は使わない。長い構成表やチェックリストは本文に出さない。

source:
{_source_brief(contract)}

output:
title, lead, body, reference, hashtags""".strip()


def _extract_text(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""
    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", "")
    return content.strip() if isinstance(content, str) else str(content or "").strip()


def _split_main_and_tail(text: str) -> tuple[str, list[str], str]:
    lines = [line.rstrip() for line in text.splitlines()]
    ref_index = next(
        (i for i, line in enumerate(lines) if line.strip().startswith(("参考", "## 参考", "# 参考"))),
        len(lines),
    )
    hash_index = next((i for i, line in enumerate(lines) if line.strip().startswith("#")), len(lines))
    split_index = min(ref_index, hash_index)
    main = "\n".join(lines[:split_index]).strip()
    tail = "\n".join(lines[split_index:]).strip()
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", main) if p.strip()]
    return main, paragraphs, tail


def _anchor_buckets(text: str) -> list[str]:
    buckets = []
    if any(x in text for x in ("相談前", "決めて", "先に", "用意", "確認しておく")):
        buckets.append("reader_preparation")
    if any(x in text for x in ("ヒアリング", "入力", "チェック", "納品", "改善")):
        buckets.append("workflow_continuity")
    if any(x in text for x in ("活用", "集計", "分析", "運用", "データ化後")):
        buckets.append("downstream_use")
    return buckets


def _trigger_report(text: str) -> dict[str, Any]:
    _, paragraphs, _ = _split_main_and_tail(text)
    rear = "\n\n".join(paragraphs[max(0, len(paragraphs) - 3) :])
    triggers = []
    buckets = _anchor_buckets(rear)
    if len(buckets) < 2:
        triggers.append("rear_half_anchor_drop")
    if any(x in rear for x in ("私たち", "弊社", "自社")):
        triggers.append("rear_half_company_first_person")
    if any(x in rear for x in ("信頼", "歴史", "選ばれ", "強み", "重要です", "大切です")):
        triggers.append("rear_half_brochure_summary")
    return {
        "rear_paragraph_count": min(3, len(paragraphs)),
        "rear_anchor_buckets": buckets,
        "triggers": triggers,
        "triggered": bool(triggers),
    }


def _regen_prompt(contract: dict[str, Any], text: str, trigger: dict[str, Any]) -> str:
    _, paragraphs, tail = _split_main_and_tail(text)
    keep = paragraphs[:-2]
    target = paragraphs[-2:]
    context = "\n\n".join(keep[-2:])
    return f"""persona:
後半だけを見る編集者。全文編集はしない。意味アンカーを戻す担当。

trigger:
{json.dumps(trigger, ensure_ascii=False)}

keep context:
{context}

rewrite only these last two body paragraphs:
{chr(10).join(target)}

rules:
- 最後の二つの本文段落だけを書き直す。
- source外の事実を足さない。
- 相談前に決めること、入力から納品までの流れ、データ化後の使い道を自然に残す。
- 私たち・弊社・自社は使わない。
- 参考情報とハッシュタグは出さない。

source:
{_source_brief(contract)}

output:
rewritten two paragraphs only""".strip()


def _replace_last_two_body_paragraphs(text: str, replacement: str) -> str:
    _, paragraphs, tail = _split_main_and_tail(text)
    if len(paragraphs) < 2:
        return text
    rebuilt = paragraphs[:-2] + [p.strip() for p in re.split(r"\n\s*\n", replacement) if p.strip()]
    body = "\n\n".join(rebuilt).strip()
    return f"{body}\n\n{tail.strip()}\n" if tail.strip() else f"{body}\n"


def _visual_issues(text: str) -> list[str]:
    issues = []
    if any(x in text for x in ("私たち", "弊社", "自社")):
        issues.append("company_first_person")
    if any(x in text for x in ("効く", "第一歩", "重要です", "大切です", "と言えるでしょう", "以下では")):
        issues.append("gpt_frequent_phrase")
    if any(x in text for x in ("について紹介", "選ばれる理由", "信頼されています")):
        issues.append("brochure_phrase")
    if "persona:" in text or "meaning anchors:" in text:
        issues.append("instruction_leak")
    return issues


def _call_chat(prompt: str, model: str, capability: dict[str, bool]) -> str:
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


def _write_compare(root: Path, report: dict[str, Any]) -> None:
    score = report.get("score") or {}
    lines = [
        "# Route A Visual Compare: persona_anchor_trigger_shadow_v1",
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
        f"- trigger fired: `{report.get('trigger_fired')}`",
        f"- regeneration call executed: `{report.get('regeneration_call_executed')}`",
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
        "This is a Route-A improvement proposal route only. Route A remains frozen.",
    ]
    base._write_text(root / "route_a_visual_compare_20260506.md", "\n".join(lines) + "\n")


def _write_failure_note(root: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Failure Note: persona_anchor_trigger_shadow_v1",
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
        f"- trigger_report: `{report.get('trigger_report')}`",
        f"- visual_issues: `{report.get('visual_issues')}`",
        "- accepted clean shadow route remains absent",
        "",
        "## Do Not Repeat",
        "",
        "- Do not widen this into a full editor pass.",
        "- Do not add repeated regeneration, threshold relaxation, Best-of-N, fallback, mock, or dummy output.",
        "- Do not move this into Route A.",
    ]
    base._write_text(root / "failure_note.md", "\n".join(lines) + "\n")


def run(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    case = _load_case()
    contract = case["contract"]
    source_path = base._write_json(root / "source_snapshot.json", contract)
    base._write_json(root / "route_a_snapshot.json", case["route_a"])
    writer_prompt = _writer_prompt(contract)
    base._write_text(root / "writer_prompt_preview.txt", writer_prompt)
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
        "mode": "one-source persona-anchor-trigger live validation",
        "status": "blocked" if issues else "started",
        "case_id": case["case_id"],
        "source_snapshot_hash": _sha256(source_path),
        "writer_prompt_sha256": hashlib.sha256(writer_prompt.encode("utf-8")).hexdigest(),
        "writer_prompt_chars": len(writer_prompt),
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
        "protected_hashes": _protected_hashes(),
    }
    if issues:
        base._write_json(root / "live_report.json", report)
        return report
    load_dotenv(PROJECT_ROOT / ".env")
    try:
        draft = _call_chat(writer_prompt, model, capability)
        trigger = _trigger_report(draft)
        final_text = draft
        regen_prompt_chars = 0
        regen_executed = False
        if trigger["triggered"]:
            regen_prompt = _regen_prompt(contract, draft, trigger)
            regen_prompt_chars = len(regen_prompt)
            base._write_text(root / "regeneration_prompt_preview.txt", regen_prompt)
            replacement = _call_chat(regen_prompt, model, capability)
            final_text = _replace_last_two_body_paragraphs(draft, replacement)
            regen_executed = True
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
    score = base._score_body(final_text)
    visual_issues = _visual_issues(final_text)
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
            "trigger_report": trigger,
            "trigger_fired": trigger["triggered"],
            "regeneration_call_executed": regen_executed,
            "regeneration_prompt_chars": regen_prompt_chars,
            "score": score,
            "visual_issues": visual_issues,
        }
    )
    base._write_text(root / "draft_before_trigger.txt", draft + "\n")
    base._write_text(root / "latest_generation_output.txt", final_text + "\n")
    base._write_json(root / "latest_generation_output.json", {"text": final_text})
    _write_compare(root, report)
    if report["decision"] == "reject":
        _write_failure_note(root, report)
    base._write_json(root / "live_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in persona anchor trigger shadow route.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run(Path(args.output_root))
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"{report['status']}: {args.output_root}")
    return 0 if report["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
