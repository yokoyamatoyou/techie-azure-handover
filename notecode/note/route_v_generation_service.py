"""Route V generation service for the normal notecode UI."""
from __future__ import annotations

import json
import os
import re
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from note.route_v_0506_adapter import ROUTE_V_0506_ROUTE_ID, run_route_v_0506_candidate
from note.route_v_speaker_entity import infer_speaker_entity
from note.writer_only_brief import CATEGORY_OPTIONS
from note.writer_only_sns import build_linkedin_outputs_from_article, evaluate_linkedin_post_smoke
from note.writer_only_source_bundle import SourceIntakeError, fetch_and_store_sources
from core.app_config import get_llm_config


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent
LOG_ROOT = PROJECT_ROOT / "logs" / "route_v_generation"
LATEST_GENERATION_TEXT_PATH = PROJECT_ROOT / "logs" / "latest_generation_output.txt"
LATEST_GENERATION_JSON_PATH = PROJECT_ROOT / "logs" / "latest_generation_output.json"
LATEST_GENERATION_QUALITY_REPORT_PATH = PROJECT_ROOT / "logs" / "latest_generation_quality_report.json"
LATEST_GENERATION_TEXT_PATH_WORKSPACE = WORKSPACE_ROOT / "logs" / "latest_generation_output.txt"
LATEST_GENERATION_JSON_PATH_WORKSPACE = WORKSPACE_ROOT / "logs" / "latest_generation_output.json"
LATEST_GENERATION_QUALITY_REPORT_PATH_WORKSPACE = WORKSPACE_ROOT / "logs" / "latest_generation_quality_report.json"
GENERATION_AUDIT_JSONL_PATH = PROJECT_ROOT / "logs" / "generation_audit_log.jsonl"
GENERATION_AUDIT_JSONL_PATH_WORKSPACE = WORKSPACE_ROOT / "logs" / "generation_audit_log.jsonl"
ROUTE_V_UI_OPENAI_ENV_DEFAULTS = {
    "ROUTE_0506_SOURCE_CARD_MAX_RETRIES": "1",
    "ROUTE_0506_JSON_STAGE_MAX_RETRIES": "1",
    "ROUTE_0506_DRAFT_WRITER_MAX_RETRIES": "1",
    "ROUTE_0506_EDITOR_STAGE_MAX_RETRIES": "1",
    "ROUTE_0506_OPENAI_REQUEST_TIMEOUT_SECONDS": "120",
    "ROUTE_0506_OPENAI_RETRY_INITIAL_BACKOFF_SECONDS": "10",
    "ROUTE_0506_OPENAI_RETRY_MAX_BACKOFF_SECONDS": "10",
    "ROUTE_0506_OPENAI_RETRY_JITTER_SECONDS": "0",
    "ROUTE_0506_OPENAI_RETRY_MAX_SERVER_HINT_SECONDS": "120",
    "ROUTE_V_SOURCE_CARD_MAX_WORKERS": "3",
}
ROUTE_V_DEFAULT_OPENAI_MODEL = "gpt-4.1"
ROUTE_V_FIXED_OPENAI_TEMPERATURE = 0.7
ROUTE_V_ARTICLE_BRIEF_ALGORITHM_ENV = "ROUTE_V_ARTICLE_BRIEF_ALGORITHM"
ROUTE_V_ARTICLE_BRIEF_ALGORITHM_VALUE = "v2"
ROUTE_V_BLOG_PERSONA_PROFILES = {
    "感情豊かな広報": {
        "profile_id": "emotional_pr",
        "style_rule": "感情の温度はやや高め。会社側の実感や背景を丁寧に添えるが、事実はsource claimsから出す。",
    },
    "ユーモアのあるサービス紹介担当": {
        "profile_id": "humorous_service_pr",
        "style_rule": "軽いユーモアは比喩や言い回しに限定。自己視点を崩さず、サービス説明は明瞭にする。",
    },
    "まじめな広報": {
        "profile_id": "serious_pr",
        "style_rule": "落ち着いた広報文体。事実・体制・読者への説明を端正に伝える。",
    },
}
ROUTE_V_API_REASON_CODES = {
    "ROUTE_V_OPENAI_TIMEOUT",
    "ROUTE_V_OPENAI_RATE_LIMIT",
    "ROUTE_V_OPENAI_AUTH_FAILED",
    "ROUTE_V_OPENAI_CONNECTION_FAILED",
    "ROUTE_V_OPENAI_API_ERROR",
}
ROUTE_V_IMAGE_ARTICLE_TYPE_ALIASES = {
    "company_introduction": "company_introduction",
    "company_service_intro": "company_introduction",
    "product_introduction": "company_introduction",
    "industry_analysis": "explanatory_article",
    "market_explanation": "explanatory_article",
    "comparison_guide": "comparative_review",
    "daily_activity": "daily_story",
}


def run_route_v_generation(
    *,
    sources: Iterable[Any],
    category_label: str,
    tone_label: str,
    target_reader: str,
    reader_problem: str,
    article_goal: str,
    company_speaker: str,
    instruction: str,
    run_id: str | None = None,
) -> Dict[str, Any]:
    resolved_run_id = run_id or _new_run_id()
    log_root = LOG_ROOT / resolved_run_id
    log_root.mkdir(parents=True, exist_ok=True)
    route_flags = _route_flags()
    source_values = [_source_value(item) for item in sources if _source_value(item)]
    _write_route_v_progress(log_root, "fetch_sources", 6, "ソースを確認しています。")
    try:
        intake = fetch_and_store_sources(source_values, run_id=resolved_run_id)
    except SourceIntakeError as exc:
        result = {
            "success": False,
            "blocked": True,
            "reason_code": "ROUTE_V_SOURCE_POLICY_BLOCKED",
            "message": str(exc),
            "policy_results": [item.__dict__ for item in exc.policy_results],
            "run_id": resolved_run_id,
            "artifact_root": _relative_label(log_root),
            "created_at": _utc_now(),
            **route_flags,
        }
        _persist_run(log_root, result, quality_report={"route_flags": route_flags, "blocked": True})
        _write_route_v_progress(log_root, "source_policy_blocked", 100, "使えるソースが不足しています。")
        return result

    _write_route_v_progress(log_root, "prepare_contract", 12, "生成条件を整理しています。")
    source_documents = _build_source_documents(intake.get("stored_sources") or [])
    input_contract = _build_input_contract(
        source_documents=source_documents,
        category_label=category_label,
        target_reader=target_reader,
        reader_problem=reader_problem,
        article_goal=article_goal,
        company_speaker=company_speaker,
        instruction=instruction,
        tone_label=tone_label,
    )
    _write_json(log_root / "input_contract.json", input_contract)
    _write_json(log_root / "source_bundle.json", dict(intake.get("source_bundle") or {}))

    try:
        _write_route_v_progress(log_root, "route_v_0506_source_card_extraction", 18, "ソースカードを作成しています。")
        with _route_v_ui_openai_runtime_env():
            route_v_result = run_route_v_0506_candidate(
                input_contract,
                artifacts_dir=log_root / "route_v_artifacts",
                run_id=resolved_run_id,
            )
    except Exception as exc:
        api_error = _classify_route_v_api_error(exc, log_root=log_root)
        reason_code = str(api_error.get("reason_code") or "ROUTE_V_GENERATION_FAILED")
        message = str(api_error.get("user_message") or _safe_error(exc))
        result = {
            "success": False,
            "blocked": True,
            "reason_code": reason_code,
            "message": message,
            "technical_message": _safe_error(exc),
            "api_error": api_error if reason_code in ROUTE_V_API_REASON_CODES else {},
            "api_send_count": int(api_error.get("api_send_count") or 0),
            "run_id": resolved_run_id,
            "artifact_root": _relative_label(log_root),
            "created_at": _utc_now(),
            **route_flags,
        }
        _persist_run(log_root, result, quality_report={"route_flags": route_flags, "blocked": True})
        _write_route_v_progress(log_root, reason_code.lower(), 100, message)
        return result

    _write_route_v_progress(log_root, "sns_generation", 92, "SNS用文章を作成しています。")
    markdown = str(route_v_result.get("final_article") or "").strip()
    source_bundle = dict(intake.get("source_bundle") or {})
    quality_report = _quality_report(route_v_result, route_flags=route_flags)
    length_observability = _length_observability(
        markdown=markdown,
        source_bundle=source_bundle,
        route_v_result=route_v_result,
    )
    success = bool(markdown) and _quality_pass(quality_report)
    title = _extract_title(markdown)
    sns_brief = {"persona": {"reader_problem": reader_problem, "article_goal": article_goal}}
    linkedin_outputs = build_linkedin_outputs_from_article(markdown, sns_brief)
    sns_evaluation = evaluate_linkedin_post_smoke(str(linkedin_outputs.get("linkedin_text") or ""), markdown)
    result = {
        "success": success and bool(sns_evaluation.get("passed")),
        "blocked": False,
        "run_id": resolved_run_id,
        "artifact_root": _relative_label(log_root),
        "draft_path": _relative_label(log_root / "draft.md"),
        "article_type": str(input_contract.get("article_type") or ""),
        "semantic_article_key": str(input_contract.get("semantic_article_key") or ""),
        "image_article_type": _image_article_type(input_contract),
        "title": title,
        "body": markdown,
        "full_text": markdown,
        "linkedin_text": linkedin_outputs.get("linkedin_text") or "",
        "linkedin_short_text": linkedin_outputs.get("linkedin_short_text") or linkedin_outputs.get("linkedin_text") or "",
        "quality_report": quality_report,
        "length_observability": length_observability,
        "sns_evaluator": sns_evaluation,
        "api_send_count": int(route_v_result.get("api_send_count") or 0),
        "created_at": _utc_now(),
        **route_flags,
    }
    _write_text(log_root / "draft.md", markdown)
    _write_text(log_root / "linkedin_post.md", str(result["linkedin_text"]))
    _write_text(log_root / "linkedin_short_post.md", str(result["linkedin_short_text"]))
    _write_json(log_root / "length_observability.json", length_observability)
    _write_json(log_root / "route_v_summary.json", _route_v_summary(route_v_result, length_observability=length_observability))
    _write_json(log_root / "sns_evaluation.json", sns_evaluation)
    _persist_run(log_root, result, quality_report=quality_report)
    _write_route_v_progress(log_root, "completed", 100, "ブログ本文とSNS用文章を作成しました。")
    return result


def new_route_v_run_id() -> str:
    return _new_run_id()


def read_route_v_progress(run_id: str) -> dict[str, Any]:
    safe_run_id = str(run_id or "").strip()
    if not safe_run_id or "/" in safe_run_id or "\\" in safe_run_id:
        return {}
    run_root = LOG_ROOT / safe_run_id
    nested = run_root / "route_v_artifacts" / safe_run_id / "progress.json"
    for path in (nested, run_root / "progress.json"):
        try:
            progress = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(progress, dict):
            return _with_retry_wait_progress(progress, path.parent / "openai_inflight_ledger.jsonl")
    return {}


def _with_retry_wait_progress(progress: Mapping[str, Any], ledger_path: Path) -> dict[str, Any]:
    resolved = dict(progress)
    try:
        lines = ledger_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return resolved
    latest: dict[str, Any] = {}
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            latest = row
            break
    retry_after = float(latest.get("retry_after_seconds") or 0.0)
    if not bool(latest.get("terminal")) or not bool(latest.get("will_retry")) or retry_after <= 0:
        return resolved
    resolved.update(
        {
            "retrying": True,
            "retry_after_seconds": retry_after,
            "retry_stage": str(latest.get("stage") or resolved.get("stage") or ""),
            "retry_attempt": int(latest.get("attempt") or 0),
            "message": f"一時的なAPIエラーのため、{retry_after:g}秒待って再試行します。",
        }
    )
    return resolved


def _route_flags() -> dict[str, Any]:
    return {
        "route_id": ROUTE_V_0506_ROUTE_ID,
        "route_v_used": True,
        "legacy_body_route_used": False,
        "fallback_used": False,
        "writer_only": False,
        "route_0506_used": False,
        "repair_used": False,
        "quality_pipeline_used": False,
        "old_routes_reopened": False,
    }


def _route_v_openai_model() -> str:
    configured = str(get_llm_config().task_models.get("route_v") or "").strip()
    return configured or ROUTE_V_DEFAULT_OPENAI_MODEL


@contextmanager
def _route_v_ui_openai_runtime_env() -> Any:
    previous: dict[str, str | None] = {}
    for key, default_value in ROUTE_V_UI_OPENAI_ENV_DEFAULTS.items():
        previous[key] = os.environ.get(key)
        if not os.environ.get(key):
            os.environ[key] = default_value
    for key, value in (
        (ROUTE_V_ARTICLE_BRIEF_ALGORITHM_ENV, ROUTE_V_ARTICLE_BRIEF_ALGORITHM_VALUE),
        ("OPENAI_MODEL", _route_v_openai_model()),
        ("ROUTE_0506_OPENAI_TEMPERATURE", f"{ROUTE_V_FIXED_OPENAI_TEMPERATURE:g}"),
    ):
        previous[key] = os.environ.get(key)
        os.environ[key] = value
    previous["OPENAI_REASONING_EFFORT"] = os.environ.get("OPENAI_REASONING_EFFORT")
    os.environ.pop("OPENAI_REASONING_EFFORT", None)
    timeout_override = os.environ.get("NOTECODE_ROUTE_V_UI_OPENAI_REQUEST_TIMEOUT_SECONDS", "").strip()
    if timeout_override and not previous.get("ROUTE_0506_OPENAI_REQUEST_TIMEOUT_SECONDS"):
        os.environ["ROUTE_0506_OPENAI_REQUEST_TIMEOUT_SECONDS"] = timeout_override
    try:
        yield
    finally:
        for key, old_value in previous.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def _classify_route_v_api_error(exc: BaseException, *, log_root: Path) -> dict[str, Any]:
    technical = _safe_error(exc)
    type_name = type(exc).__name__
    status = _error_status_code(exc)
    ledger = _route_v_openai_ledger_summary(log_root)
    ledger_error_type = str(ledger.get("error_type") or "")
    lower_text = f"{type_name} {technical} {ledger_error_type}".lower()
    if "timeout" in lower_text or type_name == "APITimeoutError":
        reason_code = "ROUTE_V_OPENAI_TIMEOUT"
        user_message = "OpenAI APIの応答が制限時間内に返らなかったため、記事生成を停止しました。本文は作成されていません。"
        api_kind = "timeout"
    elif status == 429 or "ratelimit" in lower_text or "rate limit" in lower_text:
        reason_code = "ROUTE_V_OPENAI_RATE_LIMIT"
        user_message = "OpenAI APIの利用制限に達したため、記事生成を停止しました。本文は作成されていません。"
        api_kind = "rate_limit"
    elif status in {401, 403} or "authentication" in lower_text or "permission" in lower_text:
        reason_code = "ROUTE_V_OPENAI_AUTH_FAILED"
        user_message = "OpenAI APIキーまたは権限の確認が必要なため、記事生成を停止しました。本文は作成されていません。"
        api_kind = "auth"
    elif type_name == "APIConnectionError" or "connection" in lower_text:
        reason_code = "ROUTE_V_OPENAI_CONNECTION_FAILED"
        user_message = "OpenAI APIへの接続に失敗したため、記事生成を停止しました。本文は作成されていません。"
        api_kind = "connection"
    elif status >= 400 or "api" in lower_text or ledger_error_type:
        reason_code = "ROUTE_V_OPENAI_API_ERROR"
        user_message = "OpenAI APIエラーにより記事生成を停止しました。本文は作成されていません。"
        api_kind = "api_error"
    else:
        reason_code = "ROUTE_V_GENERATION_FAILED"
        user_message = technical
        api_kind = "unknown"

    return {
        "reason_code": reason_code,
        "kind": api_kind,
        "error_type": ledger_error_type or type_name,
        "status_code": status or int(ledger.get("error_status_code") or 0),
        "stage": str(ledger.get("stage") or ""),
        "attempt": int(ledger.get("attempt") or 0),
        "max_retries": int(ledger.get("max_retries") or 0),
        "request_timeout_seconds": float(ledger.get("request_timeout_seconds") or 0.0),
        "elapsed_seconds": float(ledger.get("elapsed_seconds") or 0.0),
        "retry_after_seconds": _retry_after_seconds(exc, ledger),
        "api_send_count": int(ledger.get("api_send_count") or 0),
        "user_message": user_message,
        "technical_message": technical,
    }


def _route_v_openai_ledger_summary(log_root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for ledger_path in sorted(log_root.rglob("openai_inflight_ledger.jsonl")):
        try:
            lines = ledger_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    terminal_rows = [row for row in rows if bool(row.get("terminal"))]
    error_rows = [
        row
        for row in terminal_rows
        if str(row.get("status") or "") in {"timeout", "failed", "cancelled"}
        or str(row.get("error_type") or "").strip()
    ]
    last_error = error_rows[-1] if error_rows else {}
    return {
        **last_error,
        "elapsed_seconds": _ledger_elapsed_seconds(last_error),
        "api_send_count": len(terminal_rows),
    }


def _error_status_code(exc: BaseException) -> int:
    value = getattr(exc, "status_code", 0) or 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _ledger_elapsed_seconds(row: Mapping[str, Any]) -> float:
    started_at = str(row.get("started_at") or "").strip()
    ended_at = str(row.get("ended_at") or "").strip()
    if not started_at or not ended_at:
        return 0.0
    try:
        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    elapsed = (end - start).total_seconds()
    return round(elapsed, 3) if elapsed > 0 else 0.0


def _retry_after_seconds(exc: BaseException, ledger: Mapping[str, Any]) -> float:
    value = ledger.get("retry_after_seconds")
    try:
        retry_after = float(value or 0.0)
    except (TypeError, ValueError):
        retry_after = 0.0
    if retry_after > 0:
        return retry_after
    technical = _safe_error(exc)
    match = re.search(r"['\"]retry_after['\"]\s*:\s*([0-9]+(?:\.[0-9]+)?)", technical)
    if not match:
        return 0.0
    try:
        return float(match.group(1))
    except ValueError:
        return 0.0


def _build_input_contract(
    *,
    source_documents: list[dict[str, Any]],
    category_label: str,
    target_reader: str,
    reader_problem: str,
    article_goal: str,
    company_speaker: str,
    instruction: str,
    tone_label: str,
) -> dict[str, Any]:
    category = CATEGORY_OPTIONS.get(category_label) or CATEGORY_OPTIONS["課題解説・ノウハウ"]
    article_type = str(category.get("internal_category") or "explanatory_article")
    goal = str(article_goal or instruction or "ソースに基づいて自然なブログ記事を作る").strip()
    reader = str(target_reader or reader_problem or "初めて内容を知る読者").strip()
    speaker_entity = infer_speaker_entity(company_speaker, source_documents)
    blog_persona_profile = _resolve_blog_persona_profile(tone_label)
    return {
        "route_id": ROUTE_V_0506_ROUTE_ID,
        "article_type": article_type,
        "semantic_article_key": _semantic_key(article_type),
        "target_reader": reader,
        "audience_profile": reader,
        "article_goal": goal,
        "topic_statement": goal,
        "prompt_raw": str(instruction or goal).strip(),
        "speaker_entity": speaker_entity,
        "self_viewpoint_owner": speaker_entity,
        "source_documents": source_documents,
        "self_reference_allowed_pronouns": ["当社"] if article_type == "announcement" else ["私たち", "当社"],
        "blog_persona_profile": blog_persona_profile,
    }


def _resolve_blog_persona_profile(tone_label: str) -> dict[str, str]:
    label = str(tone_label or "").strip()
    if label in ROUTE_V_BLOG_PERSONA_PROFILES:
        profile = ROUTE_V_BLOG_PERSONA_PROFILES[label]
        return {"label": label, **profile}
    aliases = {
        "感情多め": "感情豊かな広報",
        "ユーモア": "ユーモアのあるサービス紹介担当",
        "真面目": "まじめな広報",
    }
    resolved = aliases.get(label, "まじめな広報")
    profile = ROUTE_V_BLOG_PERSONA_PROFILES[resolved]
    return {"label": resolved, **profile}


def _semantic_key(article_type: str) -> str:
    if article_type == "branding":
        return "company_introduction"
    if article_type == "industry_analysis":
        return "industry_analysis"
    return article_type


def _image_article_type(input_contract: Mapping[str, Any]) -> str:
    semantic_key = str(input_contract.get("semantic_article_key") or "").strip()
    article_type = str(input_contract.get("article_type") or "").strip()
    for key in (semantic_key, article_type):
        if key in ROUTE_V_IMAGE_ARTICLE_TYPE_ALIASES:
            return ROUTE_V_IMAGE_ARTICLE_TYPE_ALIASES[key]
    return semantic_key or article_type or "explanatory_article"


def _build_source_documents(stored_sources: list[Any]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for index, item in enumerate(stored_sources, start=1):
        if not isinstance(item, Mapping):
            continue
        content = str(item.get("full_text") or "").strip()
        if not content:
            continue
        locator = str(
            item.get("normalized_url")
            or item.get("requested_url")
            or item.get("source_path")
            or item.get("url")
            or f"stored_source:{index}"
        ).strip()
        source_type = str(item.get("source_type") or "").strip().lower()
        if not source_type:
            source_type = "url" if locator.startswith(("http://", "https://")) else "manual"
        documents.append(
            {
                "title": str(item.get("title") or item.get("url") or f"source {index}").strip(),
                "locator": locator,
                "source_type": source_type,
                "content": content,
            }
        )
    return documents


def _quality_report(route_v_result: Mapping[str, Any], *, route_flags: Mapping[str, Any]) -> dict[str, Any]:
    quality = route_v_result.get("quality_check")
    report = dict(quality) if isinstance(quality, Mapping) else {}
    report["route_flags"] = dict(route_flags)
    report["route_id"] = ROUTE_V_0506_ROUTE_ID
    report["route_source_workspace"] = str(route_v_result.get("route_source_workspace") or "notecode/0506")
    return report


def _quality_pass(report: Mapping[str, Any]) -> bool:
    quality = report.get("quality_check")
    if isinstance(quality, Mapping) and "pass" in quality:
        return bool(quality.get("pass"))
    if "pass" in report:
        return bool(report.get("pass"))
    return False


def _length_observability(
    *,
    markdown: str,
    source_bundle: Mapping[str, Any],
    route_v_result: Mapping[str, Any],
) -> dict[str, Any]:
    sources = source_bundle.get("sources")
    source_items = sources if isinstance(sources, list) else []
    source_chars = 0
    for item in source_items:
        if not isinstance(item, Mapping):
            continue
        try:
            source_chars += int(item.get("char_count") or 0)
        except (TypeError, ValueError):
            continue

    raw_brief = route_v_result.get("article_brief")
    brief = raw_brief.get("article_brief") if isinstance(raw_brief, Mapping) and isinstance(raw_brief.get("article_brief"), Mapping) else raw_brief
    brief_map = brief if isinstance(brief, Mapping) else {}
    target_length = _safe_int(brief_map.get("target_length_chars"))
    actual_chars = len(markdown)
    ratio = round(actual_chars / target_length, 3) if target_length else None
    return {
        "actual_chars": actual_chars,
        "actual_non_whitespace_chars": len("".join(str(markdown or "").split())),
        "target_length_chars": target_length,
        "target_coverage_ratio": ratio,
        "below_target": bool(target_length and actual_chars < target_length),
        "source_count": _safe_int(source_bundle.get("source_count")) or len(source_items),
        "source_chars": source_chars,
        "source_thickness": str(brief_map.get("source_thickness") or ""),
        "section_count": _safe_int(brief_map.get("section_count")),
    }


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _route_v_summary(route_v_result: Mapping[str, Any], *, length_observability: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "route_id": str(route_v_result.get("route_id") or ROUTE_V_0506_ROUTE_ID),
        "route_source_workspace": str(route_v_result.get("route_source_workspace") or "notecode/0506"),
        "external_llm_send": bool(route_v_result.get("external_llm_send")),
        "llm_client": str(route_v_result.get("llm_client") or ""),
        "source_count": int(route_v_result.get("source_count") or 0),
        "source_snapshot_hash": str(route_v_result.get("source_snapshot_hash") or ""),
        "genre_id": str(route_v_result.get("genre_id") or ""),
        "quality_check": route_v_result.get("quality_check") or {},
        "length_observability": dict(length_observability or {}),
    }


def _persist_run(log_root: Path, result: Dict[str, Any], *, quality_report: Mapping[str, Any]) -> None:
    _write_json(log_root / "run.json", result)
    _write_json(log_root / "latest_generation_quality_report.json", dict(quality_report))
    _write_latest(result, quality_report=dict(quality_report))
    _append_audit(result)


def _write_latest(result: Mapping[str, Any], *, quality_report: Mapping[str, Any]) -> None:
    body = str(result.get("body") or result.get("full_text") or "")
    for path, text in (
        (LATEST_GENERATION_TEXT_PATH, body),
        (LATEST_GENERATION_TEXT_PATH_WORKSPACE, body),
    ):
        _write_text(path, text)
    for path in (LATEST_GENERATION_JSON_PATH, LATEST_GENERATION_JSON_PATH_WORKSPACE):
        _write_json(path, dict(result))
    for path in (LATEST_GENERATION_QUALITY_REPORT_PATH, LATEST_GENERATION_QUALITY_REPORT_PATH_WORKSPACE):
        _write_json(path, dict(quality_report))


def _append_audit(result: Mapping[str, Any]) -> None:
    payload = {
        "created_at": _utc_now(),
        "run_id": str(result.get("run_id") or ""),
        "success": bool(result.get("success")),
        "route_id": str(result.get("route_id") or ROUTE_V_0506_ROUTE_ID),
        "route_v_used": bool(result.get("route_v_used")),
        "legacy_body_route_used": bool(result.get("legacy_body_route_used")),
        "fallback_used": bool(result.get("fallback_used")),
    }
    line = json.dumps(payload, ensure_ascii=False)
    for path in (GENERATION_AUDIT_JSONL_PATH, GENERATION_AUDIT_JSONL_PATH_WORKSPACE):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def _write_route_v_progress(log_root: Path, stage: str, percent: int, message: str) -> None:
    _write_json(
        log_root / "progress.json",
        {
            "stage": str(stage or ""),
            "percent": max(0, min(100, int(percent))),
            "message": str(message or ""),
        },
    )


def _source_value(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    return str(getattr(item, "value", "") or "").strip()


def _extract_title(markdown: str) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return "Route V draft"


def _new_run_id() -> str:
    return "route_v_" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _relative_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
    except OSError:
        return path.name
    except ValueError:
        try:
            return str(path.resolve().relative_to(WORKSPACE_ROOT.resolve())).replace("\\", "/")
        except (OSError, ValueError):
            return path.name


def _safe_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    text = re.sub(r"sk-[A-Za-z0-9_-]{8,}", "[REDACTED_OPENAI_KEY]", text)
    return text[:1200]


def _write_json(path: Path, payload: Mapping[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(text or ""), encoding="utf-8")
