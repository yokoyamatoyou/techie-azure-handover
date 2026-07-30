from __future__ import annotations

import json

import note.route_v_generation_service as service
from note.image_cover_strategy import _DEFAULT_COVER_STRATEGY, resolve_cover_strategy
from note.route_v_0506_adapter import ROUTE_V_0506_ROUTE_ID


def test_route_v_generation_service_logs_flags_and_latest_projection(monkeypatch, tmp_path) -> None:
    def fake_fetch(sources, *, run_id):
        assert sources == ["https://example.com/company"]
        assert run_id == "unit-route-v"
        return {
            "source_root": "data/writer_only_sources/unit-route-v",
            "policy_results": [],
            "source_bundle": {
                "source_count": 1,
                "sources": [
                    {
                        "title": "株式会社A 会社概要",
                        "excerpt": "資料整理と入力支援",
                        "claims": ["資料整理と入力支援を行います"],
                        "char_count": 2400,
                    }
                ],
            },
            "stored_sources": [
                {
                    "url": "https://example.com/company",
                    "normalized_url": "https://example.com/company",
                    "title": "株式会社A 会社概要",
                    "full_text": "私たちは資料整理と入力支援を行います。相談前に確認する観点を整理します。",
                    "source_type": "url",
                }
            ],
        }

    def fake_route_v_candidate(input_contract, *, artifacts_dir, run_id):
        assert input_contract["route_id"] == ROUTE_V_0506_ROUTE_ID
        assert input_contract["semantic_article_key"] == "company_introduction"
        assert input_contract["speaker_entity"] == "株式会社A"
        assert input_contract["self_viewpoint_owner"] == "株式会社A"
        assert input_contract["blog_persona_profile"]["label"] == "まじめな広報"
        assert input_contract["source_documents"][0]["content"].startswith("私たちは資料整理")
        assert service.os.environ.get("ROUTE_V_ARTICLE_BRIEF_ALGORITHM") == "v2"
        assert run_id == "unit-route-v"
        return {
            "route_id": ROUTE_V_0506_ROUTE_ID,
            "route_source_workspace": "notecode/0506",
            "external_llm_send": False,
            "source_count": 1,
            "source_snapshot_hash": "abc123",
            "genre_id": "company_service_intro",
            "artifact_dir": str(artifacts_dir / run_id),
            "final_article": (
                "# 相談前に資料を整理する\n\n"
                "私たちは資料整理と入力支援を行います。相談前に確認する観点を一緒に整理します。\n\n"
                "## 資料から確認できること\n\n"
                "私たちは、資料に書かれている内容から確認できることを分けて説明します。\n\n"
                "## 相談前に見ておきたいこと\n\n"
                "当社では、分からない点を先に言葉にしていただけるよう支援します。"
            ),
            "quality_check": {"quality_check": {"pass": True, "score": 100, "issues": []}},
            "article_brief": {
                "article_brief": {
                    "target_length_chars": 1800,
                    "source_thickness": "thick",
                    "section_count": 3,
                }
            },
        }

    monkeypatch.setattr(service, "LOG_ROOT", tmp_path / "route_v_generation")
    monkeypatch.setattr(service, "LATEST_GENERATION_TEXT_PATH", tmp_path / "latest_generation_output.txt")
    monkeypatch.setattr(service, "LATEST_GENERATION_JSON_PATH", tmp_path / "latest_generation_output.json")
    monkeypatch.setattr(service, "LATEST_GENERATION_QUALITY_REPORT_PATH", tmp_path / "latest_generation_quality_report.json")
    monkeypatch.setattr(service, "LATEST_GENERATION_TEXT_PATH_WORKSPACE", tmp_path / "workspace_latest_generation_output.txt")
    monkeypatch.setattr(service, "LATEST_GENERATION_JSON_PATH_WORKSPACE", tmp_path / "workspace_latest_generation_output.json")
    monkeypatch.setattr(
        service,
        "LATEST_GENERATION_QUALITY_REPORT_PATH_WORKSPACE",
        tmp_path / "workspace_latest_generation_quality_report.json",
    )
    monkeypatch.setattr(service, "GENERATION_AUDIT_JSONL_PATH", tmp_path / "generation_audit_log.jsonl")
    monkeypatch.setattr(service, "GENERATION_AUDIT_JSONL_PATH_WORKSPACE", tmp_path / "workspace_generation_audit_log.jsonl")
    monkeypatch.setattr(service, "fetch_and_store_sources", fake_fetch)
    monkeypatch.setattr(service, "run_route_v_0506_candidate", fake_route_v_candidate)

    result = service.run_route_v_generation(
        sources=["https://example.com/company"],
        category_label="会社・サービス紹介",
        tone_label="まじめな広報",
        target_reader="相談前の読者",
        reader_problem="確認点を整理したい",
        article_goal="相談前に見る観点を整理する",
        company_speaker="会社側の担当者",
        instruction="会社紹介を自己視点で書く",
        run_id="unit-route-v",
    )

    assert result["success"] is True
    assert result["route_v_used"] is True
    assert result["legacy_body_route_used"] is False
    assert result["fallback_used"] is False
    assert result["old_routes_reopened"] is False
    assert result["route_id"] == ROUTE_V_0506_ROUTE_ID
    assert result["article_type"] == "branding"
    assert result["semantic_article_key"] == "company_introduction"
    assert result["image_article_type"] == "company_introduction"
    latest = json.loads((tmp_path / "latest_generation_output.json").read_text(encoding="utf-8"))
    quality = json.loads((tmp_path / "latest_generation_quality_report.json").read_text(encoding="utf-8"))
    assert latest["route_v_used"] is True
    assert latest["image_article_type"] == "company_introduction"
    assert latest["legacy_body_route_used"] is False
    assert latest["fallback_used"] is False
    assert latest["length_observability"]["target_length_chars"] == 1800
    assert latest["length_observability"]["source_chars"] == 2400
    assert quality["route_flags"]["route_v_used"] is True
    summary = json.loads((tmp_path / "route_v_generation" / "unit-route-v" / "route_v_summary.json").read_text(encoding="utf-8"))
    assert summary["length_observability"]["source_thickness"] == "thick"
    assert (tmp_path / "route_v_generation" / "unit-route-v" / "length_observability.json").exists()
    assert "相談前に資料を整理する" in (tmp_path / "latest_generation_output.txt").read_text(encoding="utf-8")
    audit = (tmp_path / "generation_audit_log.jsonl").read_text(encoding="utf-8")
    assert '"route_v_used": true' in audit


def test_route_v_image_article_type_is_specific_for_all_ui_categories() -> None:
    source_documents = [
        {
            "title": "source",
            "locator": "manual",
            "source_type": "manual",
            "content": "会社 サービス 変更 事例 市場 比較",
        }
    ]
    expected = {
        "会社・サービス紹介": "company_introduction",
        "課題解説・ノウハウ": "explanatory_article",
        "導入事例・ケース": "case_study",
        "お知らせ": "announcement",
        "比較・業界分析": "explanatory_article",
    }

    for category_label, image_article_type in expected.items():
        contract = service._build_input_contract(
            source_documents=source_documents,
            category_label=category_label,
            target_reader="",
            reader_problem="",
            article_goal="",
            company_speaker="株式会社A",
            instruction="",
            tone_label="まじめな広報",
        )

        assert service._image_article_type(contract) == image_article_type
        assert resolve_cover_strategy(image_article_type) != _DEFAULT_COVER_STRATEGY


def test_route_v_image_article_type_normalizes_0506_genre_aliases() -> None:
    expected = {
        "company_service_intro": "company_introduction",
        "market_explanation": "explanatory_article",
        "comparison_guide": "comparative_review",
        "daily_activity": "daily_story",
    }

    for raw, normalized in expected.items():
        assert service._image_article_type({"semantic_article_key": raw}) == normalized
        assert resolve_cover_strategy(normalized) != _DEFAULT_COVER_STRATEGY


def test_route_v_generation_service_classifies_openai_timeout_and_uses_ui_retry_defaults(monkeypatch, tmp_path) -> None:
    class APITimeoutError(RuntimeError):
        pass

    observed_env = {}

    def fake_fetch(_sources, *, run_id):
        return {
            "source_bundle": {"source_count": 1, "sources": [{"char_count": 1200}]},
            "stored_sources": [
                {
                    "url": "https://example.com/company",
                    "normalized_url": "https://example.com/company",
                    "title": "株式会社A 会社概要",
                    "full_text": "私たちは資料整理と入力支援を行います。" * 30,
                    "source_type": "url",
                }
            ],
        }

    def timeout_route_v_candidate(_input_contract, *, artifacts_dir, run_id):
        observed_env.update(
            {
                "source_card_retries": service.os.environ.get("ROUTE_0506_SOURCE_CARD_MAX_RETRIES"),
                "json_retries": service.os.environ.get("ROUTE_0506_JSON_STAGE_MAX_RETRIES"),
                "draft_retries": service.os.environ.get("ROUTE_0506_DRAFT_WRITER_MAX_RETRIES"),
                "editor_retries": service.os.environ.get("ROUTE_0506_EDITOR_STAGE_MAX_RETRIES"),
                "timeout": service.os.environ.get("ROUTE_0506_OPENAI_REQUEST_TIMEOUT_SECONDS"),
                "initial_backoff": service.os.environ.get("ROUTE_0506_OPENAI_RETRY_INITIAL_BACKOFF_SECONDS"),
                "max_backoff": service.os.environ.get("ROUTE_0506_OPENAI_RETRY_MAX_BACKOFF_SECONDS"),
                "jitter": service.os.environ.get("ROUTE_0506_OPENAI_RETRY_JITTER_SECONDS"),
                "max_server_hint": service.os.environ.get("ROUTE_0506_OPENAI_RETRY_MAX_SERVER_HINT_SECONDS"),
                "article_brief_algorithm": service.os.environ.get("ROUTE_V_ARTICLE_BRIEF_ALGORITHM"),
                "model": service.os.environ.get("OPENAI_MODEL"),
                "reasoning": service.os.environ.get("OPENAI_REASONING_EFFORT"),
                "temperature": service.os.environ.get("ROUTE_0506_OPENAI_TEMPERATURE"),
            }
        )
        ledger_dir = artifacts_dir / run_id
        ledger_dir.mkdir(parents=True)
        (ledger_dir / "openai_inflight_ledger.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "stage": "knowledge_pack_integration",
                            "schema_name": "knowledge_pack.schema.json",
                            "attempt": 1,
                            "max_retries": 1,
                            "request_timeout_seconds": 120.0,
                            "status": "timeout",
                            "error_type": "APITimeoutError",
                            "error_status_code": 0,
                            "terminal": True,
                        },
                        ensure_ascii=False,
                    )
                ]
            ),
            encoding="utf-8",
        )
        raise APITimeoutError("Request timed out.")

    monkeypatch.setattr(service, "LOG_ROOT", tmp_path / "route_v_generation")
    monkeypatch.setattr(service, "LATEST_GENERATION_TEXT_PATH", tmp_path / "latest_generation_output.txt")
    monkeypatch.setattr(service, "LATEST_GENERATION_JSON_PATH", tmp_path / "latest_generation_output.json")
    monkeypatch.setattr(service, "LATEST_GENERATION_QUALITY_REPORT_PATH", tmp_path / "latest_generation_quality_report.json")
    monkeypatch.setattr(service, "LATEST_GENERATION_TEXT_PATH_WORKSPACE", tmp_path / "workspace_latest_generation_output.txt")
    monkeypatch.setattr(service, "LATEST_GENERATION_JSON_PATH_WORKSPACE", tmp_path / "workspace_latest_generation_output.json")
    monkeypatch.setattr(
        service,
        "LATEST_GENERATION_QUALITY_REPORT_PATH_WORKSPACE",
        tmp_path / "workspace_latest_generation_quality_report.json",
    )
    monkeypatch.setattr(service, "GENERATION_AUDIT_JSONL_PATH", tmp_path / "generation_audit_log.jsonl")
    monkeypatch.setattr(service, "GENERATION_AUDIT_JSONL_PATH_WORKSPACE", tmp_path / "workspace_generation_audit_log.jsonl")
    monkeypatch.setattr(service, "fetch_and_store_sources", fake_fetch)
    monkeypatch.setattr(service, "run_route_v_0506_candidate", timeout_route_v_candidate)
    for key in service.ROUTE_V_UI_OPENAI_ENV_DEFAULTS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "high")
    monkeypatch.setenv("ROUTE_0506_OPENAI_TEMPERATURE", "0.9")

    result = service.run_route_v_generation(
        sources=["https://example.com/company"],
        category_label="会社・サービス紹介",
        tone_label="真面目",
        target_reader="相談前の読者",
        reader_problem="確認点を整理したい",
        article_goal="相談前に見る観点を整理する",
        company_speaker="会社側の担当者",
        instruction="会社紹介を自己視点で書く",
        run_id="unit-timeout",
    )

    assert observed_env == {
        "source_card_retries": "1",
        "json_retries": "1",
        "draft_retries": "1",
        "editor_retries": "1",
        "timeout": "120",
        "initial_backoff": "10",
        "max_backoff": "10",
        "jitter": "0",
        "max_server_hint": "120",
        "article_brief_algorithm": "v2",
        "model": "gpt-4.1",
        "reasoning": None,
                "temperature": "0.7",
    }
    assert result["success"] is False
    assert result["blocked"] is True
    assert result["reason_code"] == "ROUTE_V_OPENAI_TIMEOUT"
    assert result["api_error"]["stage"] == "knowledge_pack_integration"
    assert result["api_error"]["max_retries"] == 1
    assert result["api_error"]["request_timeout_seconds"] == 120.0
    assert result["api_send_count"] == 1
    assert result["route_v_used"] is True
    assert result["legacy_body_route_used"] is False
    assert result["fallback_used"] is False
    latest = json.loads((tmp_path / "latest_generation_output.json").read_text(encoding="utf-8"))
    assert latest["reason_code"] == "ROUTE_V_OPENAI_TIMEOUT"
    assert (tmp_path / "latest_generation_output.txt").read_text(encoding="utf-8") == ""


def test_route_v_runtime_env_uses_configured_route_v_model(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"llm": {"task_models": {"route_v": "gpt-route-v-test"}}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("TECHIE_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("OPENAI_MODEL", "preexisting-model")

    with service._route_v_ui_openai_runtime_env():
        assert service.os.environ["OPENAI_MODEL"] == "gpt-route-v-test"

    assert service.os.environ["OPENAI_MODEL"] == "preexisting-model"


def test_route_v_runtime_env_contract_forces_source_shape_v2_and_restores(monkeypatch) -> None:
    monkeypatch.setenv("ROUTE_V_ARTICLE_BRIEF_ALGORITHM", "legacy")

    with service._route_v_ui_openai_runtime_env():
        assert service.os.environ["ROUTE_V_ARTICLE_BRIEF_ALGORITHM"] == "v2"

    assert service.os.environ["ROUTE_V_ARTICLE_BRIEF_ALGORITHM"] == "legacy"

    monkeypatch.delenv("ROUTE_V_ARTICLE_BRIEF_ALGORITHM", raising=False)

    with service._route_v_ui_openai_runtime_env():
        assert service.os.environ["ROUTE_V_ARTICLE_BRIEF_ALGORITHM"] == "v2"

    assert "ROUTE_V_ARTICLE_BRIEF_ALGORITHM" not in service.os.environ


def test_route_v_generation_service_classifies_openai_520_without_timeout(tmp_path) -> None:
    class InternalServerError(RuntimeError):
        status_code = 520

    log_root = tmp_path / "route_v_generation" / "unit-api-error"
    ledger_dir = log_root / "route_v_artifacts" / "unit-api-error"
    ledger_dir.mkdir(parents=True)
    (ledger_dir / "openai_inflight_ledger.jsonl").write_text(
        json.dumps(
            {
                "stage": "article_brief_builder",
                "schema_name": "article_brief.schema.json",
                "attempt": 1,
                "max_retries": 0,
                "request_timeout_seconds": 120.0,
                "started_at": "2026-06-18T14:40:11.935280+00:00",
                "ended_at": "2026-06-18T14:40:23.014025+00:00",
                "status": "failed",
                "error_type": "InternalServerError",
                "error_status_code": 520,
                "terminal": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = service._classify_route_v_api_error(
        InternalServerError("Error code: 520 - {'retry_after': 60}"),
        log_root=log_root,
    )

    assert result["reason_code"] == "ROUTE_V_OPENAI_API_ERROR"
    assert result["kind"] == "api_error"
    assert result["status_code"] == 520
    assert result["stage"] == "article_brief_builder"
    assert result["request_timeout_seconds"] == 120.0
    assert result["elapsed_seconds"] == 11.079
    assert result["retry_after_seconds"] == 60.0
    assert result["api_send_count"] == 1


def test_read_route_v_progress_prefers_nested_0506_progress(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(service, "LOG_ROOT", tmp_path / "route_v_generation")
    run_root = tmp_path / "route_v_generation" / "route_v_test"
    nested = run_root / "route_v_artifacts" / "route_v_test"
    run_root.mkdir(parents=True)
    nested.mkdir(parents=True)
    (run_root / "progress.json").write_text(
        json.dumps({"stage": "route_v_0506_source_card_extraction", "percent": 18}, ensure_ascii=False),
        encoding="utf-8",
    )
    (nested / "progress.json").write_text(
        json.dumps({"stage": "knowledge_pack_integration", "percent": 50}, ensure_ascii=False),
        encoding="utf-8",
    )

    progress = service.read_route_v_progress("route_v_test")

    assert progress["stage"] == "knowledge_pack_integration"
    assert progress["percent"] == 50
    assert service.read_route_v_progress("../bad") == {}


def test_read_route_v_progress_surfaces_retry_wait_from_ledger(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(service, "LOG_ROOT", tmp_path / "route_v_generation")
    nested = tmp_path / "route_v_generation" / "route_v_test" / "route_v_artifacts" / "route_v_test"
    nested.mkdir(parents=True)
    (nested / "progress.json").write_text(
        json.dumps({"stage": "structural_editor", "percent": 94, "message": "編集中です。"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (nested / "openai_inflight_ledger.jsonl").write_text(
        json.dumps(
            {
                "stage": "structural_editor",
                "attempt": 1,
                "terminal": True,
                "will_retry": True,
                "retry_after_seconds": 60.0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    progress = service.read_route_v_progress("route_v_test")

    assert progress["retrying"] is True
    assert progress["retry_stage"] == "structural_editor"
    assert progress["retry_after_seconds"] == 60.0
    assert progress["message"] == "一時的なAPIエラーのため、60秒待って再試行します。"
