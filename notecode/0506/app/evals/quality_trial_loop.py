from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.evals.hardening import create_hardening_report
from app.evals.pipeline_diagnostics import build_pipeline_diagnostics
from app.evals.pipeline_observer import ObservedLLMClient, PipelineObserver
from app.evals.rubric import diagnose_issue_owners
from app.services.local_llm_client import LocalPipelineClient
from app.services.pipeline_logging import ARTIFACTS_DIR, PipelineLogger
from app.services.pipeline_runner import BlogPipelineRunner
from app.services.source_acquisition import ExtractedSource, extract_url_source


def run_url_quality_trial(
    urls: list[str],
    trial_id: str,
    artifacts_dir: Path = ARTIFACTS_DIR / "quality_trials",
    genre_id: str = "company_service_intro",
    target_reader: str = "データ入力やスキャニングの外部委託を検討している企業担当者",
    article_goal: str = "京都工業の事業内容、強み、相談の流れをソースに基づいて自然なブログ記事にする",
    narrator: str = "私たち",
    web_research: list[dict[str, str]] | None = None,
    hypothesis: str = "",
) -> dict[str, Any]:
    extracted = [extract_url_source(url) for url in urls]
    return run_extracted_quality_trial(
        extracted,
        trial_id=trial_id,
        artifacts_dir=artifacts_dir,
        genre_id=genre_id,
        target_reader=target_reader,
        article_goal=article_goal,
        narrator=narrator,
        web_research=web_research,
        hypothesis=hypothesis,
        input_urls=urls,
    )


def run_extracted_quality_trial(
    extracted: list[ExtractedSource],
    trial_id: str,
    artifacts_dir: Path = ARTIFACTS_DIR / "quality_trials",
    genre_id: str = "company_service_intro",
    target_reader: str = "データ入力やスキャニングの外部委託を検討している企業担当者",
    article_goal: str = "ソースに基づいて自然なブログ記事にする",
    narrator: str = "私たち",
    web_research: list[dict[str, str]] | None = None,
    hypothesis: str = "",
    input_urls: list[str] | None = None,
) -> dict[str, Any]:
    trial_dir = artifacts_dir / trial_id
    trial_dir.mkdir(parents=True, exist_ok=True)

    logger = PipelineLogger(trial_id, artifacts_dir=artifacts_dir)
    observer = PipelineObserver()
    runner = BlogPipelineRunner(client=ObservedLLMClient(LocalPipelineClient(), observer), logger=logger)
    result = runner.run_extracted_sources(
        extracted,
        genre_id=genre_id,
        target_reader=target_reader,
        article_goal=article_goal,
        narrator=narrator,
    )

    hardening = create_hardening_report(result.quality_check, result.knowledge_pack, result.article_brief)
    source_readiness = [_source_summary(source) for source in extracted]
    observer_report = observer.report()
    diagnostics = build_pipeline_diagnostics(result, observer_report, source_readiness)
    quality = result.quality_check["quality_check"]
    trial_log = {
        "trial_id": trial_id,
        "hypothesis": hypothesis,
        "input_urls": input_urls or [],
        "input_sources": [source.title for source in extracted],
        "web_research": web_research or [],
        "source_readiness": source_readiness,
        "source_totals": {
            "source_count": len(source_readiness),
            "included_text_chars": sum(item["extracted_text_chars"] for item in source_readiness),
            "low_confidence_count": sum(1 for item in source_readiness if item["extraction_confidence"] == "low"),
            "blocked_count": sum(1 for item in source_readiness if not item["can_proceed"]),
        },
        "quality": {
            "pass": quality["pass"],
            "score": quality["score"],
            "issue_types": [issue["type"] for issue in quality["issues"]],
            "owner_diagnosis": diagnose_issue_owners(result.quality_check),
            "final_article_chars": len(result.final_article),
        },
        "pipeline_diagnostics": diagnostics,
        "hardening": hardening,
        "artifacts": {
            "artifact_dir": str(result.artifact_dir),
            "trial_log": str(result.artifact_dir / "trial_log.json"),
            "latest_generation_output": str(result.artifact_dir / "latest_generation_output.md"),
            "latest_generation_quality_report": str(result.artifact_dir / "latest_generation_quality_report.json"),
            "pipeline_observer_report": str(result.artifact_dir / "pipeline_observer_report.json"),
            "pipeline_diagnostics": str(result.artifact_dir / "pipeline_diagnostics.json"),
        },
    }
    (result.artifact_dir / "trial_log.json").write_text(
        json.dumps(trial_log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (result.artifact_dir / "source_readiness.json").write_text(
        json.dumps(source_readiness, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    observer.write(result.artifact_dir / "pipeline_observer_report.json")
    (result.artifact_dir / "pipeline_diagnostics.json").write_text(
        json.dumps(diagnostics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return trial_log


def _source_summary(source: ExtractedSource) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "source_type": source.source_type,
        "title": source.title,
        "url": source.metadata.get("url"),
        "canonical_url": source.metadata.get("canonical_url"),
        "fetch_status": source.metadata.get("fetch_status"),
        "extraction_method": source.metadata.get("extraction_method"),
        "extraction_confidence": source.extraction_confidence,
        "can_proceed": source.can_proceed,
        "extracted_text_chars": len(source.extracted_text),
        "span_count": len(source.source_spans),
        "warnings": source.warnings,
        "metadata": source.metadata,
    }
