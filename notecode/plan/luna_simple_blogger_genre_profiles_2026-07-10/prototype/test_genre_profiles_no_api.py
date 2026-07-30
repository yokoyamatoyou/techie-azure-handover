from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("genre_profiles_no_api", ROOT / "prototype" / "genre_profiles_no_api.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GenreProfilesNoApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads((ROOT / "prototype" / "replay_manifest.json").read_text(encoding="utf-8"))
        self.profiles = json.loads((ROOT / "prototype" / "profiles.json").read_text(encoding="utf-8"))

    def test_exactly_six_profiles_use_only_thin_schema(self) -> None:
        self.assertEqual(len(self.profiles["profiles"]), 6)
        for profile in self.profiles["profiles"]:
            MODULE.validate_profile(profile)
            self.assertFalse(set(profile) & MODULE.FORBIDDEN_PROFILE_KEYS)

    def test_common_core_identity_and_call_shape_do_not_vary(self) -> None:
        contracts = [MODULE.render_contract(p, c) for p, c in zip(self.profiles["profiles"], self.manifest["cases"])]
        self.assertEqual(len(MODULE.CORE_STAGE_1), 402)
        self.assertEqual(len(MODULE.CORE_STAGE_2), 404)
        self.assertEqual({c["role_id"] for c in contracts}, {"company_side_blogger_v1"})
        self.assertEqual({c["fixed_calls"] for c in contracts}, {2})
        self.assertEqual({c["core"]["stage_1_sha256"] for c in contracts}, {MODULE.digest(MODULE.CORE_STAGE_1)})
        self.assertEqual({c["core"]["stage_2_sha256"] for c in contracts}, {MODULE.digest(MODULE.CORE_STAGE_2)})
        self.assertTrue(all(c["stage_2_scope"] == "failed_paragraph_plus_adjacent_one_sentence_only" for c in contracts))

    def test_profiles_stay_compact_and_keep_type_risks_distinct(self) -> None:
        rendered = [MODULE.render_profile(p) for p in self.profiles["profiles"]]
        self.assertTrue(all(len(value) < 420 for value in rendered))
        self.assertEqual(len({p["major_risk"] for p in self.profiles["profiles"]}), 6)

    def test_fixture_paths_are_saved_artifacts(self) -> None:
        workspace = ROOT.parents[2]
        for case in self.manifest["cases"]:
            self.assertTrue((workspace / case["baseline_article"]).is_file())
            self.assertTrue((workspace / case["source_packet"]).is_file())

    def test_replay_writes_six_review_bundles_without_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = MODULE.run(ROOT / "prototype" / "replay_manifest.json", ROOT / "prototype" / "profiles.json", Path(tmp))
            self.assertEqual(report["api_send_count"], 0)
            self.assertTrue(report["same_role_all_types"])
            self.assertTrue(report["fixed_calls_all_types"])
            self.assertEqual(len(list((Path(tmp) / "human_review_bundle").glob("*.md"))), 7)
            self.assertFalse(report["route_v_ui_connected"])


if __name__ == "__main__":
    unittest.main()
