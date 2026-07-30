from __future__ import annotations

import json
from pathlib import Path

import pytest

import note.route_v_0506_adapter as adapter
from note.route_v_0506_adapter import (
    DEFAULT_ROUTE_V_0506_ROOT,
    ROUTE_V_0506_ROUTE_ID,
    extract_route_v_source_records,
    run_route_v_0506_candidate,
    resolve_route_v_0506_genre,
    resolve_route_v_0506_narrator,
    route_v_source_snapshot_hash,
)
from tools import run_route_v_0506_compare as compare_tool


def test_route_v_0506_default_root_is_workspace_local_not_desktop() -> None:
    root_text = str(DEFAULT_ROUTE_V_0506_ROOT)

    assert root_text.endswith("notecode\\0506")
    assert "Desktop" not in root_text


def test_route_v_0506_maps_current_article_shapes_to_0506_genres() -> None:
    assert resolve_route_v_0506_genre({"semantic_article_key": "company_introduction"}) == "company_service_intro"
    assert resolve_route_v_0506_genre({"semantic_article_key": "product_introduction"}) == "company_service_intro"
    assert resolve_route_v_0506_genre({"article_type": "announcement"}) == "announcement"
    assert resolve_route_v_0506_genre({"semantic_article_key": "comparative_review"}) == "comparison_guide"
    assert resolve_route_v_0506_genre({"semantic_article_key": "daily_story"}) == "daily_activity"
    assert resolve_route_v_0506_genre({"article_type": "explanatory_article"}) == "market_explanation"


def test_route_v_0506_preserves_self_perspective_defaults() -> None:
    assert resolve_route_v_0506_narrator({"semantic_article_key": "company_introduction"}) == "私たち"
    assert resolve_route_v_0506_narrator({"article_type": "announcement"}) == "当社"
    assert (
        resolve_route_v_0506_narrator(
            {
                "semantic_article_key": "company_introduction",
                "self_reference_allowed_pronouns": ["当社"],
            }
        )
        == "当社"
    )


def test_route_v_0506_extracts_saved_source_documents_without_refetching() -> None:
    records = extract_route_v_source_records(
        {
            "source_documents": [
                {
                    "title": "会社概要",
                    "locator": "https://example.com/company",
                    "source_type": "url",
                    "content": "私たちは業務支援を行っています。",
                },
                {"title": "empty", "content": ""},
            ]
        }
    )

    assert len(records) == 1
    assert records[0].title == "会社概要"
    assert records[0].source_type == "url"
    assert records[0].locator == "https://example.com/company"
    assert route_v_source_snapshot_hash(records) == route_v_source_snapshot_hash(records)


def test_route_v_0506_workspace_preflight_does_not_require_work_docs(tmp_path: Path) -> None:
    root = tmp_path / "0506"
    required_runtime_files = [
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
    for relative in required_runtime_files:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    (root / "requirements.txt").write_text("SudachiPy==0.6.11\nSudachiDict-core==20260428\n", encoding="utf-8")
    (root / "app/services/stylometry.py").write_text("import sudachipy\n", encoding="utf-8")

    report = adapter.inspect_route_v_0506_workspace(root)

    assert report["missing_required_files"] == []


def test_route_v_0506_uses_configured_external_client(monkeypatch, tmp_path: Path) -> None:
    selected_client = FakeExternalClient()

    class FakeRunner:
        def __init__(self, *, client, logger):
            assert client is selected_client
            self.logger = logger

        def run_extracted_sources(self, extracted_sources, **kwargs):
            assert len(extracted_sources) == 1
            assert kwargs["genre_id"] == "company_service_intro"
            assert kwargs["self_viewpoint_owner"] == "株式会社A"
            self.logger.run_dir.mkdir(parents=True, exist_ok=True)
            (self.logger.run_dir / "openai_inflight_ledger.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"stage": "draft_writer", "terminal": True, "status": "success"}),
                        json.dumps({"stage": "structural_editor", "terminal": True, "status": "success"}),
                    ]
                ),
                encoding="utf-8",
            )
            return FakePipelineResult(self.logger.run_dir)

    monkeypatch.setattr(
        adapter,
        "inspect_route_v_0506_workspace",
        lambda route_v_root: {
            "route_id": ROUTE_V_0506_ROUTE_ID,
            "workspace": "notecode/0506",
            "exists": True,
            "missing_required_files": [],
            "requirements_has_sudachi": True,
            "stylometry_uses_sudachi": True,
            "hardcoded_risk_hits": {},
        },
    )
    monkeypatch.setattr(
        adapter,
        "_load_route_v_0506_modules",
        lambda route_v_root: _fake_0506_modules(
            runner_cls=FakeRunner,
            client_factory=lambda: selected_client,
        ),
    )

    result = run_route_v_0506_candidate(
                {
                    "semantic_article_key": "company_introduction",
                    "self_viewpoint_owner": "株式会社A",
                    "source_documents": [
                {
                    "title": "会社概要",
                    "locator": "https://example.com/company",
                    "source_type": "url",
                    "content": "私たちは資料整理と入力支援を行っています。" * 20,
                }
            ],
        },
        route_v_root=tmp_path / "0506",
        artifacts_dir=tmp_path / "artifacts",
        run_id="route_v_test",
    )

    assert result["route_id"] == ROUTE_V_0506_ROUTE_ID
    assert result["external_llm_send"] is True
    assert result["llm_client"] == "FakeExternalClient"
    assert result["api_send_count"] == 2


def test_route_v_0506_blocks_local_client_for_formal_ui(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        adapter,
        "inspect_route_v_0506_workspace",
        lambda route_v_root: {
            "route_id": ROUTE_V_0506_ROUTE_ID,
            "workspace": "notecode/0506",
            "exists": True,
            "missing_required_files": [],
            "requirements_has_sudachi": True,
            "stylometry_uses_sudachi": True,
            "hardcoded_risk_hits": {},
        },
    )
    monkeypatch.setattr(
        adapter,
        "_load_route_v_0506_modules",
        lambda route_v_root: _fake_0506_modules(
            runner_cls=object,
            client_factory=LocalPipelineClient,
        ),
    )

    with pytest.raises(adapter.RouteV0506Error, match="requires_external_llm_client"):
        run_route_v_0506_candidate(
            {
                "semantic_article_key": "company_introduction",
                "source_documents": [
                    {
                        "title": "会社概要",
                        "locator": "https://example.com/company",
                        "source_type": "url",
                        "content": "私たちは資料整理と入力支援を行っています。" * 20,
                    }
                ],
            },
            route_v_root=tmp_path / "0506",
            artifacts_dir=tmp_path / "artifacts",
            run_id="route_v_test",
        )


def test_route_v_0506_compare_preflight_keeps_saved_baseline_frozen(monkeypatch, tmp_path: Path) -> None:
    contract = {
        "semantic_article_key": "company_introduction",
        "source_documents": [
            {
                "title": "会社概要",
                "locator": "https://example.com/company",
                "source_type": "url",
                "content": "私たちは資料整理と入力支援を行っています。",
            }
        ],
    }
    saved_baseline = {
        "attempt_id": "gen-test",
        "semantic_article_key": "company_introduction",
        "title": "Saved baseline",
        "body": "Saved baseline body",
    }

    monkeypatch.setattr(
        compare_tool,
        "inspect_route_v_0506_workspace",
        lambda route_v_root: {
            "route_id": ROUTE_V_0506_ROUTE_ID,
            "workspace": str(route_v_root),
            "exists": True,
            "missing_required_files": [],
            "requirements_has_sudachi": True,
            "stylometry_uses_sudachi": False,
            "hardcoded_risk_hits": {},
        },
    )
    monkeypatch.setattr(
        compare_tool,
        "_load_source_mode",
        lambda source_mode: (contract, saved_baseline, "test_source_set"),
    )
    monkeypatch.setattr(
        compare_tool,
        "run_route_v_0506_candidate",
        lambda input_contract, route_v_root, artifacts_dir, run_id: {
            "route_id": ROUTE_V_0506_ROUTE_ID,
            "external_llm_send": False,
            "genre_id": "company_service_intro",
            "artifact_dir": str(tmp_path / "route_v_0506_artifacts" / "route_v_0506"),
            "final_article": "私たちは資料整理と入力支援を行っています。",
            "quality_check": {"quality_check": {"pass": True, "score": 100, "issues": []}},
        },
    )

    summary = compare_tool.run_compare(tmp_path, route_v_root=tmp_path / "0506", source_mode="latest-ui-saved")

    assert summary["status"] == "preflight_ready"
    assert summary["decision"] == "continue_shadow"
    assert summary["guardrails"]["current_default_route_changed"] is False
    assert summary["guardrails"]["legacy_runtime_touched"] is False
    assert summary["guardrails"]["legacy_fallback_used"] is False
    assert summary["guardrails"]["external_llm_send"] is False
    assert (tmp_path / "compare_summary.json").exists()
    assert (tmp_path / "baseline_current_saved" / "latest_generation_output.json").exists()
    assert (tmp_path / "route_v_0506" / "latest_generation_output.md").exists()


class FakeExternalClient:
    pass


class LocalPipelineClient:
    pass


class FakeLogger:
    def __init__(self, *, run_id: str, artifacts_dir: Path) -> None:
        self.run_dir = artifacts_dir / run_id


class FakePipelineResult:
    def __init__(self, artifact_dir: Path) -> None:
        self.artifact_dir = artifact_dir
        self.final_article = "# Route V\n\n私たちは資料整理と入力支援を行っています。"
        self.quality_check = {"quality_check": {"pass": True, "score": 100, "issues": []}}
        self.source_cards = []
        self.knowledge_pack = {}
        self.article_brief = {}


class FakeSourceSpan:
    def __init__(self, span_id: str, text: str, location: str) -> None:
        self.span_id = span_id
        self.text = text
        self.location = location


class FakeExtractedSource:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


def _fake_0506_modules(*, runner_cls, client_factory):
    return {
        "BlogPipelineRunner": runner_cls,
        "PipelineLogger": FakeLogger,
        "select_default_llm_client": client_factory,
        "ExtractedSource": FakeExtractedSource,
        "SourceSpan": FakeSourceSpan,
        "stable_source_id": lambda source_type, title, locator: f"{source_type}:{title}:{locator}",
    }
