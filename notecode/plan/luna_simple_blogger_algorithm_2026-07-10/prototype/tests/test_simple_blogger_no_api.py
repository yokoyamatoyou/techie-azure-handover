from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "simple_blogger_no_api.py"
SPEC = importlib.util.spec_from_file_location("simple_blogger_no_api", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SimpleBloggerNoApiTests(unittest.TestCase):
    def test_contract_is_compact_and_keeps_one_role(self) -> None:
        contract = MODULE.render_contract()
        self.assertEqual(contract["role_id"], MODULE.ROLE_ID)
        self.assertIn(MODULE.ROLE_ID, contract["stage_1"]["prompt"])
        self.assertIn(MODULE.ROLE_ID, contract["stage_2"]["prompt"])
        self.assertLess(contract["stage_1"]["chars"], 900)
        self.assertLess(contract["stage_2"]["chars"], 900)
        self.assertFalse(contract["raw_full_source_handoff"])

    def test_call_shape_is_one_vs_two(self) -> None:
        contract = MODULE.render_contract()
        self.assertEqual(contract["arm_a_fixed_calls"], 1)
        self.assertEqual(contract["arm_b_fixed_calls"], 2)

    def test_metrics_find_structure_meta_and_narrator(self) -> None:
        article = "# 題名\n\n導入です。\n\n## 場面\n\n私たちは作業します。確認します。"
        metrics = MODULE.analyze(article, "作業を行う会社です。", 10)
        self.assertEqual(metrics["h1_count"], 1)
        self.assertEqual(metrics["h2_count"], 1)
        self.assertEqual(metrics["narrator_counts"]["私たち"], 1)
        self.assertEqual(metrics["phrase_counts"]["確認"], 1)
        self.assertEqual(metrics["source_overlap"]["unsupported_claim_status"], "not_evaluable_statically")

    def test_zero_anaphora_is_manual_candidate_only(self) -> None:
        candidates = MODULE.zero_candidates("お客様が相談しました。対応します。")
        self.assertEqual(len(candidates), 1)
        self.assertTrue(candidates[0]["competing_entity_in_previous_sentence"])
        self.assertEqual(candidates[0]["status"], "manual_review_candidate")

    def test_saved_artifact_replay_stays_no_api(self) -> None:
        manifest = Path(__file__).parents[1] / "fixtures" / "replay_manifest.json"
        with tempfile.TemporaryDirectory() as tmp:
            summary = MODULE.run(manifest, Path(tmp))
            self.assertEqual(summary["api_send_count"], 0)
            self.assertEqual(summary["case_count"], 9)
            saved = json.loads((Path(tmp) / "replay_metrics.json").read_text(encoding="utf-8"))
            self.assertFalse(saved["route_v_product_code_changed"])
            self.assertFalse(saved["limits"]["same_blogger_luna_output_present"])


if __name__ == "__main__":
    unittest.main()
