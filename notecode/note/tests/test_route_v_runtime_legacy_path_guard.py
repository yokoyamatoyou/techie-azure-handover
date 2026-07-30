from __future__ import annotations

import asyncio
import ast
import inspect
import sys
from importlib.abc import MetaPathFinder
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping

import note.note_writer_app_route_v_ui as writer_ui
import note.route_v_0506_adapter as adapter
import note.route_v_generation_service as service
from note.route_v_0506_adapter import ROUTE_V_0506_ROUTE_ID


NOTE_ROOT = Path(__file__).resolve().parents[1]

ALLOWLISTED_BODY_GENERATION_SHELL = {
    NOTE_ROOT / "note_writer_app_route_v_ui.py",
    NOTE_ROOT / "route_v_generation_service.py",
    NOTE_ROOT / "route_v_0506_adapter.py",
}

ALLOWLISTED_NOTE_IMPORTS = {
    "note.blog_image_auto",
    "note.preview_sanitizer",
    "note.route_v_0506_adapter",
    "note.route_v_generation_service",
    "note.route_v_speaker_entity",
    "note.writer_only_brief",
    "note.writer_only_image_handoff",
    "note.writer_only_sns",
    "note.writer_only_source_bundle",
}

ALLOWLISTED_0506_DYNAMIC_IMPORTS = {
    "app.services.pipeline_runner",
    "app.services.pipeline_logging",
    "app.services.llm_client",
    "app.services.source_acquisition",
}

BANNED_LEGACY_BODY_RUNTIME_PREFIXES = (
    "note.current_mainline_runner",
    "note.newalgorithm_pipeline",
    "note.simple_note_pipeline",
    "note.writer_only_service",
    "note.vnext",
    "note.zero_base",
    "note.legacy_current",
)

BANNED_LEGACY_BODY_RUNTIME_TOKENS = (
    "current_mainline_runner",
    "newalgorithm_pipeline",
    "simple_note_pipeline",
    "writer_only_service",
    "note.vnext",
    "note.zero_base",
    "note.legacy_current",
)


class FakeElement:
    def __init__(self, value: Any = "") -> None:
        self.value = value
        self.text = ""
        self.content = ""
        self.visible = False
        self.enabled = True

    def classes(self, *args: Any, **kwargs: Any) -> "FakeElement":
        return self

    def disable(self) -> None:
        self.enabled = False

    def enable(self) -> None:
        self.enabled = True


class ForbiddenLegacyRuntimeImportFinder(MetaPathFinder):
    def __init__(self) -> None:
        self.hits: list[str] = []

    def find_spec(self, fullname: str, path: object | None, target: object | None = None) -> None:
        if _is_banned_legacy_runtime(fullname):
            self.hits.append(fullname)
            raise AssertionError(f"legacy body-generation runtime import attempted: {fullname}")
        return None


def test_normal_ui_default_body_generation_stays_on_route_v_0506(monkeypatch, tmp_path: Path) -> None:
    default_callable = inspect.signature(writer_ui.run_route_v_generation_click).parameters[
        "generation_callable"
    ].default
    assert default_callable is service.run_route_v_generation
    assert service.ROUTE_V_0506_ROUTE_ID == ROUTE_V_0506_ROUTE_ID
    assert adapter.ROUTE_V_0506_ROUTE_ID == "route_v_0506_structured_blog_v1"

    observed: dict[str, Any] = {}

    def fake_fetch(sources: list[str], *, run_id: str) -> dict[str, Any]:
        assert sources == ["https://example.com/source"]
        assert run_id == "route_v_guard"
        return {
            "source_bundle": {"source_count": 1, "sources": [{"char_count": 1800}]},
            "stored_sources": [
                {
                    "url": "https://example.com/source",
                    "normalized_url": "https://example.com/source",
                    "title": "source",
                    "full_text": "私たちは資料に基づいてサービス内容を説明します。" * 40,
                    "source_type": "url",
                }
            ],
        }

    def fake_route_v_candidate(
        input_contract: Mapping[str, Any],
        *,
        artifacts_dir: Path,
        run_id: str,
    ) -> dict[str, Any]:
        observed["input_contract"] = dict(input_contract)
        observed["artifacts_dir"] = artifacts_dir
        observed["run_id"] = run_id
        return {
            "route_id": ROUTE_V_0506_ROUTE_ID,
            "route_source_workspace": "notecode/0506",
            "external_llm_send": False,
            "source_count": 1,
            "source_snapshot_hash": "guard",
            "genre_id": "company_service_intro",
            "artifact_dir": str(artifacts_dir / run_id),
            "final_article": "# Route V Guard\n\n私たちは資料に基づいて本文を作成します。",
            "quality_check": {"quality_check": {"pass": True, "score": 100, "issues": []}},
            "article_brief": {
                "article_brief": {
                    "target_length_chars": 1400,
                    "source_thickness": "thick",
                    "section_count": 2,
                }
            },
            "api_send_count": 0,
        }

    _patch_route_v_log_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(service, "fetch_and_store_sources", fake_fetch)
    monkeypatch.setattr(service, "run_route_v_0506_candidate", fake_route_v_candidate)
    monkeypatch.setattr(writer_ui, "new_route_v_run_id", lambda: "route_v_guard")
    monkeypatch.setattr(writer_ui.ui, "notify", lambda *_args, **_kwargs: None)

    state = SimpleNamespace(sources=["https://example.com/source"], busy=False, result={})
    import_guard = ForbiddenLegacyRuntimeImportFinder()
    sys.meta_path.insert(0, import_guard)
    try:
        asyncio.run(
            writer_ui.run_route_v_generation_click(
                state=state,
                controls=_controls(),
                status_targets=_status_targets(),
                result_targets=_result_targets(),
                fallback_instruction=lambda: "guard",
                refresh_output_stage_visibility=lambda: None,
                refresh_step_indicators=lambda: None,
                to_plain_dict=dict,
                io_bound=_immediate_io_bound,
                sanitize_preview=lambda text: text,
            )
        )
    finally:
        sys.meta_path.remove(import_guard)

    assert import_guard.hits == []
    assert observed["run_id"] == "route_v_guard"
    assert observed["input_contract"]["route_id"] == ROUTE_V_0506_ROUTE_ID
    assert state.result["route_id"] == ROUTE_V_0506_ROUTE_ID
    assert state.result["route_v_used"] is True
    assert state.result["legacy_body_route_used"] is False
    assert state.result["fallback_used"] is False
    assert state.result["writer_only"] is False
    assert state.result["route_0506_used"] is False
    assert state.result["repair_used"] is False
    assert state.result["quality_pipeline_used"] is False
    assert state.result["old_routes_reopened"] is False
    assert state.result["api_send_count"] == 0


def test_route_v_body_generation_shell_imports_match_runtime_allowlist() -> None:
    note_imports: set[str] = set()
    dynamic_0506_imports: set[str] = set()
    banned_tokens: dict[str, list[str]] = {}

    for path in ALLOWLISTED_BODY_GENERATION_SHELL:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        note_imports.update(_note_imports(tree))
        dynamic_0506_imports.update(_dynamic_imports(tree))
        hits = [token for token in BANNED_LEGACY_BODY_RUNTIME_TOKENS if token in source]
        if hits:
            banned_tokens[path.name] = hits

    assert note_imports <= ALLOWLISTED_NOTE_IMPORTS
    assert dynamic_0506_imports == ALLOWLISTED_0506_DYNAMIC_IMPORTS
    assert banned_tokens == {}


def test_route_v_flags_keep_legacy_fallbacks_closed() -> None:
    assert service._route_flags() == {
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


def _note_imports(tree: ast.AST) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names if alias.name.startswith("note."))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("note."):
                imports.add(module)
    banned = {name for name in imports if _is_banned_legacy_runtime(name)}
    assert banned == set()
    return imports


def _dynamic_imports(tree: ast.AST) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "import_module":
            continue
        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            imports.add(node.args[0].value)
    return imports


def _is_banned_legacy_runtime(module_name: str) -> bool:
    return any(
        module_name == prefix or module_name.startswith(prefix + ".")
        for prefix in BANNED_LEGACY_BODY_RUNTIME_PREFIXES
    )


async def _immediate_io_bound(fn: Any) -> Mapping[str, Any]:
    return fn()


def _patch_route_v_log_paths(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.setattr(service, "LOG_ROOT", tmp_path / "route_v_generation")
    monkeypatch.setattr(service, "LATEST_GENERATION_TEXT_PATH", tmp_path / "latest_generation_output.txt")
    monkeypatch.setattr(service, "LATEST_GENERATION_JSON_PATH", tmp_path / "latest_generation_output.json")
    monkeypatch.setattr(
        service,
        "LATEST_GENERATION_QUALITY_REPORT_PATH",
        tmp_path / "latest_generation_quality_report.json",
    )
    monkeypatch.setattr(service, "LATEST_GENERATION_TEXT_PATH_WORKSPACE", tmp_path / "workspace_output.txt")
    monkeypatch.setattr(service, "LATEST_GENERATION_JSON_PATH_WORKSPACE", tmp_path / "workspace_output.json")
    monkeypatch.setattr(
        service,
        "LATEST_GENERATION_QUALITY_REPORT_PATH_WORKSPACE",
        tmp_path / "workspace_quality.json",
    )
    monkeypatch.setattr(service, "GENERATION_AUDIT_JSONL_PATH", tmp_path / "audit.jsonl")
    monkeypatch.setattr(service, "GENERATION_AUDIT_JSONL_PATH_WORKSPACE", tmp_path / "workspace_audit.jsonl")


def _controls() -> writer_ui.RouteVControls:
    return writer_ui.RouteVControls(
        category=FakeElement("会社・サービス紹介"),
        tone=FakeElement("まじめな広報"),
        instruction=FakeElement("guard"),
        target_reader=FakeElement("reader"),
        reader_problem=FakeElement("problem"),
        article_goal=FakeElement("goal"),
        company_speaker=FakeElement("company"),
        button=FakeElement(),
    )


def _status_targets() -> writer_ui.RouteVStatusTargets:
    return writer_ui.RouteVStatusTargets(
        generate_button=FakeElement(),
        route_v_button=FakeElement(),
        spinner=FakeElement(),
        generation_progress=FakeElement(),
        generation_progress_note=FakeElement(),
        missing_source_alert=FakeElement(),
        source_error_area=FakeElement(),
        status_label=FakeElement(),
    )


def _result_targets() -> writer_ui.RouteVResultTargets:
    return writer_ui.RouteVResultTargets(
        title_area=FakeElement(),
        lead_area=FakeElement(),
        body_area=FakeElement(),
        references_area=FakeElement(),
        hashtags_area=FakeElement(),
        full_text_area=FakeElement(),
        note_body_text=FakeElement(),
        linkedin_area=FakeElement(),
        linkedin_short_area=FakeElement(),
        preview=FakeElement(),
        stats_label=FakeElement(),
    )
