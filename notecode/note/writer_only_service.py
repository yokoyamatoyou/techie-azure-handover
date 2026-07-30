"""End-to-end writer-only generation service for the notecode UI."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable

from note.writer_only_brief import build_writer_only_brief
from note.writer_only_evaluator import evaluate_writer_only_smoke
from note.writer_only_openai_adapter import write_openai_draft
from note.writer_only_sns import (
    LINKEDIN_MAX_CHARS,
    build_linkedin_outputs_from_article,
    evaluate_linkedin_post_smoke,
    has_company_first_person,
)
from note.writer_only_source_bundle import SourceIntakeError, fetch_and_store_sources


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_ROOT = PROJECT_ROOT / "logs" / "writer_only_generation"


def run_writer_only_generation(
    *,
    sources: Iterable[Any],
    category_label: str,
    tone_label: str,
    target_reader: str,
    reader_problem: str,
    article_goal: str,
    company_speaker: str,
    instruction: str,
    writer: Callable[[Dict[str, Any]], Dict[str, Any]] = write_openai_draft,
    run_id: str | None = None,
) -> Dict[str, Any]:
    resolved_run_id = run_id or _new_run_id()
    log_root = LOG_ROOT / resolved_run_id
    log_root.mkdir(parents=True, exist_ok=True)
    route_flags = {
        "writer_only": True,
        "route_0506_used": False,
        "route_a_used": False,
        "repair_used": False,
        "quality_pipeline_used": False,
        "image_generation_used": False,
    }
    urls = [_source_value(item) for item in sources if _source_value(item)]
    try:
        intake = fetch_and_store_sources(urls, run_id=resolved_run_id)
    except SourceIntakeError as exc:
        result = {
            "success": False,
            "blocked": True,
            "reason_code": "WRITER_ONLY_SOURCE_POLICY_BLOCKED",
            "message": str(exc),
            "policy_results": [item.__dict__ for item in exc.policy_results],
            "run_id": resolved_run_id,
            "artifact_root": str(log_root),
            **route_flags,
        }
        _write_json(log_root / "run.json", result)
        return result

    brief = build_writer_only_brief(
        urls=[item.get("normalized_url") or item.get("url") for item in intake["source_bundle"].get("sources", [])],
        instruction=instruction,
        category_label=category_label,
        tone_label=tone_label,
        target_reader=target_reader,
        reader_problem=reader_problem,
        article_goal=article_goal,
        company_speaker=company_speaker,
        source_bundle=intake["source_bundle"],
    )
    _write_json(log_root / "brief.json", brief)
    _write_json(log_root / "source_bundle.json", intake["source_bundle"])

    writer_result = writer(brief)
    markdown = str(writer_result.get("markdown") or "").strip()
    fallback_linkedin_outputs = build_linkedin_outputs_from_article(markdown, brief)
    linkedin_text = str(writer_result.get("linkedin_text") or "").strip()
    linkedin_short_text = str(writer_result.get("linkedin_short_text") or "").strip()
    primary_linkedin_text = linkedin_short_text or linkedin_text
    if (
        not primary_linkedin_text
        or len(primary_linkedin_text) > LINKEDIN_MAX_CHARS
        or not has_company_first_person(primary_linkedin_text)
    ):
        primary_linkedin_text = str(
            fallback_linkedin_outputs.get("linkedin_short_text")
            or fallback_linkedin_outputs.get("linkedin_text")
            or ""
        ).strip()
    linkedin_outputs = {
        "linkedin_text": primary_linkedin_text,
        "linkedin_short_text": primary_linkedin_text,
    }
    evaluation = evaluate_writer_only_smoke(markdown, brief, route_flags)
    sns_evaluation = evaluate_linkedin_post_smoke(linkedin_outputs["linkedin_text"], markdown)
    title = _extract_title(markdown)
    result = {
        "success": bool(evaluation.get("passed")) and bool(sns_evaluation.get("passed")),
        "blocked": False,
        "run_id": resolved_run_id,
        "artifact_root": str(log_root),
        "source_root": str(intake.get("source_root") or ""),
        "draft_path": str(log_root / "draft.md"),
        "linkedin_text_path": str(log_root / "linkedin_post.md"),
        "linkedin_short_text_path": str(log_root / "linkedin_short_post.md"),
        "title": title,
        "body": markdown,
        "full_text": markdown,
        "linkedin_text": linkedin_outputs["linkedin_text"],
        "linkedin_short_text": linkedin_outputs["linkedin_short_text"],
        "smoke_evaluator": evaluation,
        "sns_evaluator": sns_evaluation,
        "sns_post_contract": brief.get("sns_post_contract"),
        "writer_model": writer_result.get("model"),
        "writer_family": writer_result.get("family"),
        "api": writer_result.get("api"),
        "api_send_count": int(writer_result.get("api_send_count") or 0),
        "created_at": datetime.now(timezone.utc).isoformat(),
        **route_flags,
    }
    (log_root / "draft.md").write_text(markdown, encoding="utf-8")
    (log_root / "linkedin_post.md").write_text(linkedin_outputs["linkedin_text"], encoding="utf-8")
    (log_root / "linkedin_short_post.md").write_text(linkedin_outputs["linkedin_short_text"], encoding="utf-8")
    _write_json(log_root / "evaluation.json", evaluation)
    _write_json(log_root / "sns_evaluation.json", sns_evaluation)
    _write_json(log_root / "run.json", result)
    return result


def _source_value(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    return str(getattr(item, "value", "") or "").strip()


def _extract_title(markdown: str) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return "writer-only draft"


def _new_run_id() -> str:
    return "writer_only_" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
