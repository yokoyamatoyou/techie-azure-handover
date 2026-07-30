"""Adapter for running the local 0506 blog pipeline as Route V.

This module keeps the retired legacy runtime untouched. It imports the 0506
workspace only when explicitly called by Route V service or preflight tools.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping


ROUTE_V_0506_ROUTE_ID = "route_v_0506_structured_blog_v1"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROUTE_V_0506_ROOT = Path(os.getenv("NOTECODE_ROUTE_V_0506_ROOT", str(PROJECT_ROOT / "0506")))


class RouteV0506Error(RuntimeError):
    """Raised when the 0506 Route V candidate cannot be prepared."""


@dataclass(frozen=True)
class RouteVSourceRecord:
    title: str
    content: str
    locator: str
    source_type: str


def resolve_route_v_0506_genre(input_contract: Mapping[str, Any]) -> str:
    semantic_key = str(input_contract.get("semantic_article_key") or "").strip().lower()
    article_type = str(input_contract.get("article_type") or "").strip().lower()
    if semantic_key in {"announcement"} or article_type == "announcement":
        return "announcement"
    if semantic_key in {"implementation_case", "improvement_case", "case_study"} or article_type == "case_study":
        return "case_study"
    if semantic_key in {"comparative_review"} or article_type == "comparative_review":
        return "comparison_guide"
    if semantic_key in {"daily_story"} or article_type == "daily_story":
        return "daily_activity"
    if semantic_key in {"explanatory_article", "industry_analysis"} or article_type in {
        "explanatory_article",
        "industry_analysis",
    }:
        return "market_explanation"
    return "company_service_intro"


def resolve_route_v_0506_narrator(input_contract: Mapping[str, Any]) -> str | None:
    if resolve_route_v_0506_genre(input_contract) == "announcement":
        return "当社"
    allowed_pronouns = input_contract.get("self_reference_allowed_pronouns")
    if isinstance(allowed_pronouns, list):
        normalized = [str(item).strip() for item in allowed_pronouns]
        if "私たち" in normalized:
            return "私たち"
        if "当社" in normalized:
            return "当社"
    return "私たち"


def extract_route_v_source_records(
    input_contract: Mapping[str, Any],
    *,
    max_sources: int = 5,
) -> list[RouteVSourceRecord]:
    records: list[RouteVSourceRecord] = []
    source_documents = input_contract.get("source_documents")
    if not isinstance(source_documents, list):
        return records

    for index, item in enumerate(source_documents[:max_sources], start=1):
        if not isinstance(item, Mapping):
            continue
        title = str(
            item.get("title")
            or item.get("source_label")
            or item.get("url")
            or item.get("locator")
            or f"source {index}"
        ).strip()
        content = str(item.get("content") or item.get("text") or item.get("extracted_text") or "").strip()
        if not content:
            continue
        locator = str(item.get("locator") or item.get("url") or item.get("canonical_url") or f"source:{index}").strip()
        source_type = str(item.get("source_type") or "").strip().lower()
        if not source_type:
            source_type = "url" if locator.startswith(("http://", "https://")) else "manual"
        records.append(
            RouteVSourceRecord(
                title=title or f"source {index}",
                content=content,
                locator=locator or f"source:{index}",
                source_type=source_type,
            )
        )
    return records


def route_v_source_snapshot_hash(records: list[RouteVSourceRecord]) -> str:
    payload = [
        {
            "title": record.title,
            "content": record.content,
            "locator": record.locator,
            "source_type": record.source_type,
        }
        for record in records
    ]
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def inspect_route_v_0506_workspace(route_v_root: Path = DEFAULT_ROUTE_V_0506_ROOT) -> dict[str, Any]:
    root = Path(route_v_root)
    required_files = [
        "requirements.txt",
        "app/services/pipeline_runner.py",
        "app/services/stylometry.py",
        "app/services/llm_client.py",
        "app/services/source_acquisition.py",
        "app/services/pipeline_logging.py",
        "app/config/article_genres.yaml",
        "app/config/default_settings.yaml",
        "app/personas/persona_registry.yaml",
    ]
    missing = [relative for relative in required_files if not (root / relative).exists()]
    requirements_text = _read_text(root / "requirements.txt")
    stylometry_text = _read_text(root / "app" / "services" / "stylometry.py")
    hardcoded_risk_hits = _hardcoded_risk_hits(root)
    return {
        "route_id": ROUTE_V_0506_ROUTE_ID,
        "workspace": _workspace_label(root),
        "exists": root.exists(),
        "missing_required_files": missing,
        "requirements_has_sudachi": "SudachiPy" in requirements_text and "SudachiDict-core" in requirements_text,
        "stylometry_uses_sudachi": "sudachipy" in stylometry_text or "SplitMode" in stylometry_text,
        "hardcoded_risk_hits": hardcoded_risk_hits,
    }


def run_route_v_0506_candidate(
    input_contract: Mapping[str, Any],
    *,
    route_v_root: Path = DEFAULT_ROUTE_V_0506_ROOT,
    artifacts_dir: Path,
    run_id: str = "route_v_0506",
) -> dict[str, Any]:
    records = extract_route_v_source_records(input_contract)
    if not records:
        raise RouteV0506Error("route_v_0506_requires_source_documents_with_content")

    workspace_report = inspect_route_v_0506_workspace(route_v_root)
    if workspace_report["missing_required_files"]:
        raise RouteV0506Error(
            "route_v_0506_workspace_missing_required_files:"
            + ",".join(workspace_report["missing_required_files"])
        )

    modules = _load_route_v_0506_modules(Path(route_v_root))
    extracted_sources = [_build_0506_extracted_source(modules, record, index) for index, record in enumerate(records, 1)]
    genre_id = resolve_route_v_0506_genre(input_contract)
    target_reader = str(input_contract.get("audience_profile") or input_contract.get("target_reader") or "").strip()
    if not target_reader:
        target_reader = "初めて内容を知る読者"
    article_goal = str(
        input_contract.get("topic_statement")
        or input_contract.get("core_message")
        or input_contract.get("prompt_raw")
        or ""
    ).strip()
    if not article_goal:
        article_goal = "ソースに基づいて自然なブログ記事を作る"
    self_viewpoint_owner = str(
        input_contract.get("self_viewpoint_owner")
        or input_contract.get("speaker_entity")
        or resolve_route_v_0506_narrator(input_contract)
        or ""
    ).strip()
    blog_persona_profile = input_contract.get("blog_persona_profile")
    if not isinstance(blog_persona_profile, Mapping):
        blog_persona_profile = {}

    llm_client = modules["select_default_llm_client"]()
    if _is_local_pipeline_client(llm_client):
        raise RouteV0506Error("route_v_formal_ui_requires_external_llm_client")

    logger = modules["PipelineLogger"](run_id=run_id, artifacts_dir=Path(artifacts_dir))
    runner = modules["BlogPipelineRunner"](client=llm_client, logger=logger)
    result = runner.run_extracted_sources(
        extracted_sources,
        genre_id=genre_id,
        target_reader=target_reader,
        article_goal=article_goal,
        narrator=resolve_route_v_0506_narrator(input_contract),
        self_viewpoint_owner=self_viewpoint_owner,
        blog_persona_profile=dict(blog_persona_profile),
    )
    return {
        "route_id": ROUTE_V_0506_ROUTE_ID,
        "route_source_workspace": _workspace_label(Path(route_v_root)),
        "external_llm_send": True,
        "llm_client": type(llm_client).__name__,
        "source_count": len(records),
        "source_snapshot_hash": route_v_source_snapshot_hash(records),
        "genre_id": genre_id,
        "target_reader": target_reader,
        "article_goal": article_goal,
        "artifact_dir": str(result.artifact_dir),
        "api_send_count": _count_terminal_openai_sends(Path(result.artifact_dir)),
        "final_article": result.final_article,
        "quality_check": result.quality_check,
        "source_cards": result.source_cards,
        "knowledge_pack": result.knowledge_pack,
        "article_brief": result.article_brief,
        "workspace_report": workspace_report,
    }


def _load_route_v_0506_modules(route_v_root: Path) -> dict[str, Any]:
    root = route_v_root.resolve()
    existing_app = sys.modules.get("app")
    if existing_app is not None:
        app_file = str(getattr(existing_app, "__file__", "") or "")
        if app_file and not Path(app_file).resolve().is_relative_to(root):
            raise RouteV0506Error(f"python_module_app_already_loaded_from_other_root:{app_file}")
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    route_v_site_packages = root / ".venv" / "Lib" / "site-packages"
    route_v_site_packages_text = str(route_v_site_packages)
    if route_v_site_packages.exists() and route_v_site_packages_text not in sys.path:
        sys.path.insert(1, route_v_site_packages_text)
    try:
        pipeline_runner = import_module("app.services.pipeline_runner")
        pipeline_logging = import_module("app.services.pipeline_logging")
        llm_client = import_module("app.services.llm_client")
        source_acquisition = import_module("app.services.source_acquisition")
    except Exception as exc:  # pragma: no cover - exact dependency errors vary by host.
        raise RouteV0506Error(f"route_v_0506_import_failed:{type(exc).__name__}:{exc}") from exc
    return {
        "BlogPipelineRunner": pipeline_runner.BlogPipelineRunner,
        "PipelineLogger": pipeline_logging.PipelineLogger,
        "select_default_llm_client": llm_client.select_default_llm_client,
        "ExtractedSource": source_acquisition.ExtractedSource,
        "SourceSpan": source_acquisition.SourceSpan,
        "stable_source_id": source_acquisition.stable_source_id,
    }


def _build_0506_extracted_source(
    modules: Mapping[str, Any],
    record: RouteVSourceRecord,
    index: int,
) -> Any:
    source_id = modules["stable_source_id"](record.source_type, record.title, record.locator or record.content)
    confidence = "high" if len(record.content) >= 500 else "medium" if len(record.content) >= 120 else "low"
    location = record.locator if record.locator else f"notecode_source:{index}"
    span = modules["SourceSpan"](f"notecode_{index:03d}", record.content, location)
    return modules["ExtractedSource"](
        source_id=source_id,
        source_type=record.source_type,
        title=record.title,
        extracted_text=record.content,
        source_spans=[span],
        metadata={
            "source_label": record.title,
            "url": record.locator if record.locator.startswith(("http://", "https://")) else None,
            "canonical_url": record.locator if record.locator.startswith(("http://", "https://")) else None,
            "source_priority": 5,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "extraction_method": "notecode_saved_source_document",
        },
        warnings=[] if confidence != "low" else ["saved source text is thin"],
        extraction_confidence=confidence,
        can_proceed=confidence in {"high", "medium"},
    )


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _count_terminal_openai_sends(artifact_dir: Path) -> int:
    count = 0
    for ledger_path in Path(artifact_dir).rglob("openai_inflight_ledger.jsonl"):
        try:
            lines = ledger_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and bool(row.get("terminal")):
                count += 1
    return count


def _workspace_label(path: Path) -> str:
    try:
        resolved = Path(path).resolve()
        project_root = PROJECT_ROOT.resolve()
        if resolved == project_root / "0506":
            return "notecode/0506"
        if resolved.is_relative_to(project_root):
            return str(resolved.relative_to(project_root)).replace("\\", "/")
    except OSError:
        pass
    return "external_route_v_workspace"


def _is_local_pipeline_client(client: Any) -> bool:
    return type(client).__name__ == "LocalPipelineClient"


def _hardcoded_risk_hits(root: Path) -> dict[str, int]:
    patterns = (
        "京都工業",
        "kyotokogyo",
        "1371322",
        "Business Model Canvas",
        "Marketing",
        "Marketability",
        "市場性",
        "ビジネスモデル",
    )
    targets = [
        root / "app" / "services" / "local_draft_renderer.py",
        root / "app" / "services" / "local_source_card_builder.py",
        root / "app" / "services" / "global_consistency_editor.py",
        root / "app" / "services" / "opening_editor.py",
    ]
    counts = {pattern: 0 for pattern in patterns}
    for target in targets:
        text = _read_text(target)
        for pattern in patterns:
            counts[pattern] += text.count(pattern)
    return {pattern: count for pattern, count in counts.items() if count}
