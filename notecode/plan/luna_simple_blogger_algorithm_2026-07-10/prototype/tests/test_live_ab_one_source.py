from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "live_ab_one_source.py"
SPEC = importlib.util.spec_from_file_location("live_ab_one_source", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeUsage:
    def model_dump(self, mode: str = "json") -> dict:
        return {"input_tokens": 10, "output_tokens": 10, "input_tokens_details": {"cached_tokens": 0}}


class FakeResponse:
    status = "completed"
    id = "resp_fake"
    model = MODULE.MODEL
    usage = FakeUsage()
    output_text = "# test\n\nbody"

    def model_dump(self, mode: str = "json") -> dict:
        return {"id": self.id, "model": self.model, "status": self.status, "output_text": self.output_text}


class FakeResponses:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return FakeResponse()


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


class LiveAbOneSourceTests(unittest.TestCase):
    def test_role_and_reasoning_shape(self) -> None:
        self.assertEqual(MODULE.MODEL, "gpt-5.6-luna")
        self.assertEqual(MODULE.STAGE_A_EFFORT, "low")
        self.assertEqual(MODULE.STAGE_B_EFFORT, "medium")
        self.assertEqual(MODULE.MAX_RETRIES, 0)
        self.assertEqual(MODULE.MAX_SENDS, 2)
        self.assertTrue((MODULE.ROLE_PREFIX + MODULE.STAGE_A_TASK).startswith(MODULE.ROLE_PREFIX))
        self.assertTrue((MODULE.ROLE_PREFIX + MODULE.STAGE_B_TASK).startswith(MODULE.ROLE_PREFIX))

    def test_third_send_is_refused_with_fake_client(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake = FakeClient()
            cap = MODULE.SendCap(fake, Path(tmp))
            cap.call(arm="A", effort="low", instructions="a", input_text="a")
            cap.call(arm="B", effort="medium", instructions="b", input_text="b")
            with self.assertRaisesRegex(RuntimeError, "third"):
                cap.call(arm="C", effort="medium", instructions="c", input_text="c")
            self.assertEqual(cap.count, 2)
            self.assertEqual(fake.responses.calls, 2)


if __name__ == "__main__":
    unittest.main()
