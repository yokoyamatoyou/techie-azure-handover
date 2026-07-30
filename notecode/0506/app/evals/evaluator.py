from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from app.evals.rubric import evaluate_rubric
from app.services.local_llm_client import LocalPipelineClient
from app.services.pipeline_logging import PipelineLogger
from app.services.pipeline_runner import BlogPipelineRunner


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES_PATH = ROOT / "app" / "evals" / "fixtures" / "phase6_cases.yaml"


def load_eval_cases(path: Path = DEFAULT_CASES_PATH) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cases = data.get("cases", [])
    if not isinstance(cases, list) or not cases:
        raise ValueError("eval cases must be a non-empty list")
    return cases


def run_eval_case(case: dict[str, Any], artifacts_dir: Path) -> dict[str, Any]:
    logger = PipelineLogger(case["case_id"], artifacts_dir=artifacts_dir)
    runner = BlogPipelineRunner(client=LocalPipelineClient(), logger=logger)
    sources = [(source["title"], source["text"]) for source in case["sources"]]
    result = runner.run_manual_sources(
        sources,
        genre_id=case["genre_id"],
        target_reader=case["target_reader"],
        article_goal=case["article_goal"],
        narrator=case["narrator"],
    )
    rubric_results = evaluate_rubric(result.final_article, result.quality_check, case["expected"])
    report = {
        "case_id": case["case_id"],
        "artifact_dir": str(result.artifact_dir),
        "score": result.quality_check["quality_check"]["score"],
        "pass": all(item.passed for item in rubric_results),
        "rubric": [asdict(item) for item in rubric_results],
        "unresolved_issues": result.quality_check["quality_check"]["issues"],
        "final_article_chars": len(result.final_article),
    }
    (result.artifact_dir / "phase6_quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def run_eval_suite(artifacts_dir: Path) -> dict[str, Any]:
    reports = [run_eval_case(case, artifacts_dir) for case in load_eval_cases()]
    suite = {
        "case_count": len(reports),
        "passed_count": sum(1 for report in reports if report["pass"]),
        "reports": reports,
    }
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / "phase6_suite_report.json").write_text(
        json.dumps(suite, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return suite
