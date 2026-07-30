from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from analysis_core.metrics import build_budget_guardrail, build_query_rollup_rows
from analysis_core.trends import build_raw_results_export_rows, build_weekly_summary_rows
from config import AppConfig
from export_file_writers import build_signed_export_path, validate_signed_export_path
from llmo_core.factory import build_provider_client
from runtime_mode import READONLY_DEMO_ENV_VAR, is_readonly_demo_mode
from ui.dashboard_view_models import filter_rows_for_active_scope, resolve_current_result_run_id


def _build_config(**overrides: object) -> AppConfig:
    base = AppConfig(
        keywords=["AI visibility"],
        repeat_count=1,
        daily_budget_usd=1.0,
        budget_guardrail_mode="stop",
        target_domain="https://example.com",
        brand_terms=["Example"],
    )
    return base.model_copy(update=overrides)


def _build_export_row(**overrides: object) -> dict[str, object]:
    payload = {
        "answer_text": "=dangerous answer",
        "answer_snapshot": "@snapshot",
        "citations": [{"url": "https://external.example.com/page", "title": "-external title"}],
        "citation_urls": ["https://external.example.com/page"],
        "competitor_mentions": ["+competitor"],
        "analysis_context": {"brand_terms": [], "analysis_mode": "market", "model": "gpt-5.4-nano"},
    }
    row: dict[str, object] = {
        "analyzed_at": time.time(),
        "run_id": "run_test",
        "question_set_name": "=question set",
        "schedule_id": "",
        "run_mode": "manual",
        "keyword_raw": "=SUM(1,1)",
        "keyword_norm": "sum",
        "executed_query": "+executed query",
        "user_query_short": "@short query",
        "query_was_shortened": False,
        "shortening_note": "-note",
        "expanded_queries_json": json.dumps(["=expanded"], ensure_ascii=False),
        "prompt_taxonomy_json": "[]",
        "expansion_mode": "",
        "expansion_signature": "",
        "provider_batch_mode": "",
        "provider_batch_id": "",
        "provider_cache_policy": "",
        "output_json": json.dumps(payload, ensure_ascii=False),
        "visibility_score": 0,
        "raw_llm_score": 0,
        "deterministic_score": 0,
        "target_domain_hit": False,
        "brand_mention_hit": False,
        "owned_citation_count": 0,
        "owned_citation_share": 0.0,
        "owned_mention_hit": False,
        "competitor_mention_hit": False,
        "external_only_result": True,
        "answer_type_key": "external_only",
        "answer_type_label": "@answer type",
        "mentioned_brands_json": "[]",
        "citation_domains_json": "[]",
        "answer_snapshot": "=snapshot",
        "answer_text": "=dangerous answer",
        "citations_json": json.dumps(payload["citations"], ensure_ascii=False),
        "error_text": "-error",
    }
    row.update(overrides)
    return row


class BudgetGuardrailTests(unittest.TestCase):
    def test_guardrail_counts_active_batch_reservations(self) -> None:
        config = _build_config()
        batch_job = {
            "submitted_at": time.time(),
            "created_at": time.time(),
            "request_count": 4,
            "imported_result_count": 0,
            "imported_error_count": 0,
            "request_counts_completed": 0,
            "request_counts_failed": 0,
            "status": "submitted",
            "output_file_id": "",
            "error_file_id": "",
            "reserved_cost_usd": 1.1,
            "config_json": json.dumps(config.model_dump(), ensure_ascii=False),
        }

        guardrail = build_budget_guardrail([], config, planned_request_count=1, batch_jobs=[batch_job])

        self.assertTrue(guardrail["should_block"])
        self.assertAlmostEqual(guardrail["today_reserved_cost_usd"], 1.1, places=6)
        self.assertGreater(guardrail["projected_total_usd"], config.daily_budget_usd)

    def test_failed_empty_batch_does_not_reserve_budget(self) -> None:
        config = _build_config()
        batch_job = {
            "submitted_at": time.time(),
            "created_at": time.time(),
            "request_count": 4,
            "imported_result_count": 0,
            "imported_error_count": 0,
            "request_counts_completed": 0,
            "request_counts_failed": 0,
            "status": "failed",
            "output_file_id": "",
            "error_file_id": "",
            "reserved_cost_usd": 1.1,
            "config_json": json.dumps(config.model_dump(), ensure_ascii=False),
        }

        guardrail = build_budget_guardrail([], config, planned_request_count=1, batch_jobs=[batch_job])

        self.assertEqual(guardrail["today_reserved_cost_usd"], 0.0)
        self.assertFalse(guardrail["should_block"])

    def test_run_guardrail_warn_mode_does_not_block_execution(self) -> None:
        config = _build_config(
            budget_guardrail_mode="warn",
            daily_budget_usd=0.0,
            run_budget_guardrail_usd=1.2,
        )

        guardrail = build_budget_guardrail([], config, planned_request_count=300, batch_jobs=[])

        self.assertTrue(guardrail["would_exceed_run_guardrail"])
        self.assertFalse(guardrail["run_guardrail_should_block"])
        self.assertFalse(guardrail["should_block"])

    def test_run_guardrail_stop_mode_blocks_execution(self) -> None:
        config = _build_config(
            budget_guardrail_mode="stop",
            daily_budget_usd=0.0,
            run_budget_guardrail_usd=1.2,
        )

        guardrail = build_budget_guardrail([], config, planned_request_count=300, batch_jobs=[])

        self.assertTrue(guardrail["would_exceed_run_guardrail"])
        self.assertTrue(guardrail["run_guardrail_should_block"])


class ReadonlyDemoModeTests(unittest.TestCase):
    def test_readonly_demo_env_flag_is_explicit(self) -> None:
        previous_value = os.environ.get(READONLY_DEMO_ENV_VAR)
        try:
            os.environ.pop(READONLY_DEMO_ENV_VAR, None)
            self.assertFalse(is_readonly_demo_mode())

            os.environ[READONLY_DEMO_ENV_VAR] = "1"
            self.assertTrue(is_readonly_demo_mode())
        finally:
            if previous_value is None:
                os.environ.pop(READONLY_DEMO_ENV_VAR, None)
            else:
                os.environ[READONLY_DEMO_ENV_VAR] = previous_value

    def test_readonly_demo_blocks_provider_client_creation(self) -> None:
        previous_value = os.environ.get(READONLY_DEMO_ENV_VAR)
        try:
            os.environ[READONLY_DEMO_ENV_VAR] = "1"
            with self.assertRaisesRegex(RuntimeError, "read-only/demo mode"):
                build_provider_client("openai")
        finally:
            if previous_value is None:
                os.environ.pop(READONLY_DEMO_ENV_VAR, None)
            else:
                os.environ[READONLY_DEMO_ENV_VAR] = previous_value


class CsvSanitizationTests(unittest.TestCase):
    def test_raw_results_export_sanitizes_formula_like_strings(self) -> None:
        export_rows = build_raw_results_export_rows([_build_export_row()], _build_config())
        export_row = export_rows[0]

        self.assertTrue(str(export_row["keyword_raw"]).startswith("'="))
        self.assertTrue(str(export_row["executed_query"]).startswith("'+"))
        self.assertTrue(str(export_row["user_query_short"]).startswith("'@"))
        self.assertTrue(str(export_row["answer_text"]).startswith("'="))
        self.assertTrue(str(export_row["error_text"]).startswith("'-"))

    def test_weekly_summary_export_sanitizes_scope_labels(self) -> None:
        summary_rows = build_weekly_summary_rows([_build_export_row()], _build_config())
        query_rows = [row for row in summary_rows if row["scope_type"] == "query"]

        self.assertEqual(len(query_rows), 1)
        self.assertTrue(str(query_rows[0]["scope_label"]).startswith("'="))


class ExportLinkSecurityTests(unittest.TestCase):
    def test_export_links_are_signed_and_direct_paths_are_rejected(self) -> None:
        signed_path = build_signed_export_path("abcDEF_123456", "raw_results.csv", now=1000)

        self.assertIn("expires=", signed_path)
        self.assertIn("token=", signed_path)
        self.assertIsNone(
            validate_signed_export_path(
                Path("exports"),
                "abcDEF_123456",
                "raw_results.csv",
                expires="",
                token="",
                now=1001,
            )
        )

    def test_validate_signed_export_path_rejects_expired_or_tampered_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "abcDEF_123456"
            bundle.mkdir()
            target = bundle / "raw_results.csv"
            target.write_text("ok", encoding="utf-8")
            signed_path = build_signed_export_path("abcDEF_123456", "raw_results.csv", now=1000)
            query = dict(part.split("=", 1) for part in signed_path.split("?", 1)[1].split("&"))

            self.assertEqual(
                validate_signed_export_path(
                    root,
                    "abcDEF_123456",
                    "raw_results.csv",
                    expires=query["expires"],
                    token=query["token"],
                    now=1001,
                ),
                target.resolve(strict=False),
            )
            self.assertIsNone(
                validate_signed_export_path(
                    root,
                    "abcDEF_123456",
                    "raw_results.csv",
                    expires=query["expires"],
                    token="tampered",
                    now=1001,
                )
            )
            self.assertIsNone(
                validate_signed_export_path(
                    root,
                    "abcDEF_123456",
                    "raw_results.csv",
                    expires=query["expires"],
                    token=query["token"],
                    now=int(query["expires"]) + 1,
                )
            )


class DashboardScopeRestoreTests(unittest.TestCase):
    def test_filter_rows_uses_user_query_and_run_config_target_scope(self) -> None:
        config = _build_config(keywords=["Original question"], target_domain="https://example.com")
        row = _build_export_row(
            keyword_raw="expanded query variant",
            run_config_json=json.dumps(config.model_dump(), ensure_ascii=False),
            output_json=json.dumps(
                {
                    "answer_text": "safe",
                    "analysis_context": {
                        "user_query_raw": "Original question",
                        "analysis_mode": config.analysis_mode,
                    },
                },
                ensure_ascii=False,
            ),
        )

        filtered_rows = filter_rows_for_active_scope([row], config)

        self.assertEqual(len(filtered_rows), 1)

    def test_current_result_restore_skips_all_error_latest_run(self) -> None:
        config = _build_config(keywords=["Original question"], target_domain="https://example.com")
        run_config_json = json.dumps(config.model_dump(), ensure_ascii=False)
        now = time.time()
        latest_error_row = _build_export_row(
            run_id="run_all_error",
            analyzed_at=now,
            run_finished_at=now,
            run_config_json=run_config_json,
            keyword_raw="Original question",
            error_text="Connection error.",
            output_json=json.dumps(
                {"answer_snapshot": "実行エラー。設定またはAPI応答を確認してください。"},
                ensure_ascii=False,
            ),
        )
        older_success_row = _build_export_row(
            run_id="run_success",
            analyzed_at=now - 60,
            run_finished_at=now - 60,
            run_config_json=run_config_json,
            keyword_raw="Original question",
            error_text="",
            output_json=json.dumps({"answer_snapshot": "自社URLが引用されています。"}, ensure_ascii=False),
        )

        restored_run_id = resolve_current_result_run_id([latest_error_row, older_success_row], config)

        self.assertEqual(restored_run_id, "run_success")

    def test_query_rollup_groups_expanded_queries_under_user_question(self) -> None:
        row_a = _build_export_row(
            run_id="run_scope",
            analyzed_at=100.0,
            keyword_raw="expanded query A",
            executed_query="expanded query A",
            expanded_queries_json=json.dumps(["expanded query A", "expanded query B"], ensure_ascii=False),
            output_json=json.dumps(
                {
                    "answer_text": "safe",
                    "analysis_context": {
                        "user_query_raw": "Original question",
                        "analysis_mode": "market",
                    },
                },
                ensure_ascii=False,
            ),
        )
        row_b = _build_export_row(
            run_id="run_scope",
            analyzed_at=101.0,
            keyword_raw="expanded query B",
            executed_query="expanded query B",
            expanded_queries_json=json.dumps(["expanded query A", "expanded query B"], ensure_ascii=False),
            output_json=json.dumps(
                {
                    "answer_text": "safe",
                    "analysis_context": {
                        "user_query_raw": "Original question",
                        "analysis_mode": "market",
                    },
                },
                ensure_ascii=False,
            ),
        )

        rollups = build_query_rollup_rows([row_a, row_b])

        self.assertEqual(len(rollups), 1)
        self.assertEqual(rollups[0]["keyword_raw"], "Original question")
        self.assertEqual(rollups[0]["internal_query_count"], 2)


if __name__ == "__main__":
    unittest.main()
