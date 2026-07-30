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

from dotenv import load_dotenv  # noqa: E402
from openai import OpenAI  # noqa: E402

from core.app_config import get_llm_config  # noqa: E402


ROUTE_ID = "reasoning_effort_minimal_shadow_arm_v1"
SOURCE_LOG = PROJECT_ROOT / "logs" / "latest_generation_output.json"
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "logs"
    / "shadow_autonomous_20260504-233916"
    / "routes"
    / "reasoning_effort_minimal_preflight_20260506"
)
GPT_TERMS = ("効く", "第一歩", "重要です", "大切です", "と言えるでしょう", "以下では", "まとめると", "いかがでしたか")
FIRST_PERSON_COMPANY = ("私たち", "自社", "弊社")
PROTECTED_FILES = (
    "note/current_mainline_runner.py",
    "note/newalgorithm_pipeline/pipeline.py",
    "note/simple_note_pipeline/pipeline.py",
    "note/simple_note_pipeline/prompt_builder.py",
    "note/simple_note_pipeline/repair_acceptance.py",
    "note/simple_note_pipeline/quality_guard.py",
)


def _now_jst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S JST")


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protected_hashes() -> dict[str, str]:
    return {rel: _sha256(PROJECT_ROOT / rel) for rel in PROTECTED_FILES}


def _load_case() -> dict[str, Any]:
    payload = json.loads(SOURCE_LOG.read_text(encoding="utf-8"))
    contract = dict(payload.get("input_contract") or {})
    contract.setdefault("article_type", payload.get("article_type") or "")
    contract.setdefault("semantic_article_key", payload.get("semantic_article_key") or "")
    return {
        "case_id": f"latest_ui_route_a_{payload.get('attempt_id') or 'latest'}",
        "attempt_id": payload.get("attempt_id") or "",
        "contract": contract,
        "route_a": {
            "title": payload.get("title") or "",
            "lead": payload.get("lead") or "",
            "body": payload.get("body") or "",
            "hashtags": payload.get("hashtags") or "",
        },
    }


def _clean_line(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _source_brief(contract: dict[str, Any], *, per_source_chars: int = 2600) -> str:
    parts: list[str] = []
    for index, doc in enumerate(contract.get("source_documents") or [], start=1):
        title = _clean_line(doc.get("title") or f"source_{index}")
        locator = _clean_line(doc.get("locator") or "")
        content = _clean_line(doc.get("content") or "")
        if len(content) > per_source_chars:
            content = content[:per_source_chars].rstrip() + "..."
        parts.append(f"[{index}] {title}\nURL: {locator}\n{content}")
    return "\n\n".join(parts)


def _build_prompt(contract: dict[str, Any]) -> str:
    source = _source_brief(contract)
    return f"""保存済みsourceだけを根拠に、日本語のブログ記事を1本書いてください。
対象は branding / company_introduction です。

守ること:
- 会社を一人称にしない。「私たち」「自社」「弊社」は使わない。
- source外の事実を足さない。
- 会社紹介パンフレットではなく、読者が業務を考える時に読むブログとして書く。
- 見出しを使う場合も、歴史・信頼・価格・強みの列挙にしない。
- 参考情報は本文に混ぜず、最後に必要最小限で置く。

source:
{source}

出力はタイトル、リード、本文、ハッシュタグだけ。""".strip()


def _sdk_capability(model: str) -> dict[str, Any]:
    client = OpenAI(api_key="dummy")
    sig = inspect.signature(client.chat.completions.create)
    params = sig.parameters
    return {
        "openai_sdk_chat_create_has_extra_body": "extra_body" in params,
        "openai_sdk_chat_create_has_reasoning_effort": "reasoning_effort" in params,
        "configured_generation_model": model,
        "model_prefix_supports_reasoning": model.lower().startswith(("gpt-5", "o1", "o3")),
        "responses_api_available_in_sdk": hasattr(client, "responses"),
    }


def _configured_shadow_model() -> str:
    config = get_llm_config()
    task_models = dict(config.task_models or {})
    return str(task_models.get("section") or config.model_name or "")


def _score_body(text: str) -> dict[str, Any]:
    body = str(text or "")
    sentences = [s.strip() for s in re.split(r"[。！？]", body) if s.strip()]
    buckets: list[str] = []
    for sentence in sentences:
        tail = sentence[-5:]
        buckets.append("polite" if tail.endswith(("ます", "です", "ました", "でした")) else "other")
    max_run = 0
    run = 0
    prev = ""
    for bucket in buckets:
        run = run + 1 if bucket == prev else 1
        prev = bucket
        max_run = max(max_run, run)
    return {
        "body_char_count": len(body),
        "gpt_frequent_term_hits": [term for term in GPT_TERMS if term in body],
        "first_person_company_hits": [term for term in FIRST_PERSON_COMPANY if term in body],
        "ending_bucket_max_run": max_run,
        "ending_bucket_monotony": max_run >= 7,
        "body_length_target_result": "ok" if 1400 <= len(body) <= 2400 else ("short" if len(body) < 1400 else "long"),
        "third_party_intro_tone": any(x in body for x in ("について紹介", "強み", "選ばれて", "信頼されています")),
        "textbook_explanation_tone": any(x in body for x in ("重要です", "大切です", "ポイントです")),
    }


def _base_report(root: Path) -> tuple[dict[str, Any], str]:
    case = _load_case()
    contract = dict(case["contract"])
    prompt = _build_prompt(contract)
    source_path = _write_json(root / "source_snapshot.json", contract)
    _write_json(root / "route_a_snapshot.json", case["route_a"])
    _write_text(root / "writer_prompt_preview.txt", prompt)
    model = _configured_shadow_model()
    capability = _sdk_capability(model)
    issues: list[str] = []
    if case["case_id"] != "latest_ui_route_a_gen-453da287":
        issues.append("case_id_not_latest_ui_route_a_gen-453da287")
    if contract.get("article_type") != "branding":
        issues.append("article_type_not_branding")
    if contract.get("semantic_article_key") != "company_introduction":
        issues.append("semantic_article_key_not_company_introduction")
    if not capability["model_prefix_supports_reasoning"]:
        issues.append("configured_model_does_not_support_reasoning_prefix")
    if not capability["openai_sdk_chat_create_has_extra_body"] and not capability["openai_sdk_chat_create_has_reasoning_effort"]:
        issues.append("sdk_cannot_pass_reasoning_effort")
    report = {
        "route_id": ROUTE_ID,
        "date_jst": _now_jst(),
        "mode": "local preflight only; no LLM send",
        "status": "ready_for_live_approval" if not issues else "blocked",
        "case_id": case["case_id"],
        "source_snapshot_hash": _sha256(source_path),
        "writer_prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "writer_prompt_chars": len(prompt),
        "configured_generation_model": model,
        "requested_reasoning_effort": "minimal",
        "requested_verbosity": "medium",
        "sdk_capability": capability,
        "validation_issues": issues,
        "implementation_started": True,
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
    return report, prompt


def run_preflight(root: Path) -> dict[str, Any]:
    report, _ = _base_report(root)
    _write_json(root / "preflight_report.json", report)
    _write_text(
        root / "blocked_or_ready.md",
        "\n".join(
            [
                "# reasoning_effort_minimal_shadow_arm_v1 preflight",
                "",
                f"- status: `{report['status']}`",
                f"- route_id: `{ROUTE_ID}`",
                f"- case_id: `{report['case_id']}`",
                f"- configured_generation_model: `{report['configured_generation_model']}`",
                "- requested_reasoning_effort: `minimal`",
                "- live_generation_started: `false`",
                f"- validation_issues: `{', '.join(report['validation_issues']) if report['validation_issues'] else 'none'}`",
                "- next: explicit approval is required before one-source live validation",
            ]
        )
        + "\n",
    )
    return report


def _extract_text(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""
    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(str(getattr(item, "text", "") or item.get("text", "")) for item in content).strip()
    return str(content or "").strip()


def run_live(root: Path) -> dict[str, Any]:
    report, prompt = _base_report(root)
    report["mode"] = "one-source live validation"
    if report["status"] == "blocked":
        _write_json(root / "live_report.json", report)
        return report
    load_dotenv(PROJECT_ROOT / ".env")
    request_params = {
        "model": report["configured_generation_model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 3000,
    }
    if report["sdk_capability"]["openai_sdk_chat_create_has_reasoning_effort"]:
        request_params["reasoning_effort"] = "minimal"
        request_params["verbosity"] = "medium"
    else:
        request_params["extra_body"] = {"reasoning_effort": "minimal", "verbosity": "medium"}
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
        _write_json(root / "live_report.json", report)
        return report
    text = _extract_text(response)
    score = _score_body(text)
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
    _write_text(root / "latest_generation_output.txt", text + "\n")
    _write_json(root / "latest_generation_output.json", {"text": text})
    _write_json(root / "live_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in reasoning_effort=minimal shadow route.")
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
