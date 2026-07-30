from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analysis_lib import normalize_text
from llmo_core.models import build_batch_item_custom_id
from storage import Storage


class BatchCustomIdUniquenessTests(unittest.TestCase):
    def test_batch_item_custom_id_includes_run_attempt(self) -> None:
        first = build_batch_item_custom_id("run_first_attempt", 1, 1)
        second = build_batch_item_custom_id("run_second_attempt", 1, 1)

        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("run_first_attempt__item_000001__iter_001"))
        self.assertTrue(second.startswith("run_second_attempt__item_000001__iter_001"))

    def test_same_saved_condition_rerun_items_do_not_collide(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            db = Storage(Path(tmpdir) / "rerun.db")
            first_run_id = db.create_run_session(
                20,
                "gpt-5.4-nano",
                "",
                run_mode="batch",
                question_set_id="qs_same",
                question_set_name="same saved condition",
            )
            second_run_id = db.create_run_session(
                20,
                "gpt-5.4-nano",
                "",
                run_mode="batch",
                question_set_id="qs_same",
                question_set_name="same saved condition",
            )

            self._insert_job_with_one_logical_request(db, "batch_first", first_run_id)
            self._insert_job_with_one_logical_request(db, "batch_second", second_run_id)

            first_items = db.list_batch_job_items("batch_first")
            second_items = db.list_batch_job_items("batch_second")
            self.assertEqual(len(first_items), 1)
            self.assertEqual(len(second_items), 1)
            self.assertNotEqual(first_items[0]["custom_id"], second_items[0]["custom_id"])

    def _insert_job_with_one_logical_request(self, db: Storage, batch_job_id: str, run_id: str) -> None:
        keyword = "AI visibility same question"
        db.create_batch_job(
            batch_job_id=batch_job_id,
            run_id=run_id,
            provider_key="openai",
            status="submitted",
            endpoint="/v1/responses",
            completion_window="24h",
            model_name="gpt-5.4-nano",
            repeat_count=20,
            request_count=1,
            input_file_id=f"file_{batch_job_id}",
            config_json=json.dumps({"keywords": [keyword]}, ensure_ascii=False),
            metadata_json="{}",
            request_counts_total=1,
            items=[
                {
                    "custom_id": build_batch_item_custom_id(run_id, 1, 1),
                    "keyword_raw": keyword,
                    "keyword_norm": normalize_text(keyword),
                    "iteration_index": 1,
                    "query_plan_id": "qp_same",
                    "user_query_raw": keyword,
                    "executed_query": keyword,
                    "executed_query_index": 1,
                    "request_body_json": "{}",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
