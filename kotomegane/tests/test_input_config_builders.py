from __future__ import annotations

import unittest

from config import AppConfig
from ui.input_config_builders import build_config_from_inputs, build_manual_runtime_config


class _Control:
    def __init__(self, value: str) -> None:
        self.value = value


def _base_inputs() -> dict[str, object]:
    return {
        "target_domain": _Control("https://example.com"),
        "brand_terms": _Control("Example"),
        "market_context": _Control("Tokyo, manufacturing"),
        "competitor_terms": _Control("Competitor"),
    }


class BuildConfigFromInputsTests(unittest.TestCase):
    def test_uses_only_visible_keyword_inputs(self) -> None:
        current = AppConfig(keywords=["current"], target_domain="https://example.com")
        inputs = {
            **_base_inputs(),
            "keyword_inputs": [
                _Control("main question"),
                _Control("hidden question"),
                _Control("also hidden"),
            ],
            "visible_keyword_count": lambda: 1,
        }

        config = build_config_from_inputs(inputs, current)

        self.assertEqual(config.keywords, ["main question"])
        self.assertEqual(config.repeat_count, 10)

    def test_manual_runtime_uses_five_repeats_for_twenty_total_answers(self) -> None:
        config = AppConfig(repeat_count=10)

        manual_config = build_manual_runtime_config(config)

        self.assertEqual(manual_config.repeat_count, 5)
        self.assertEqual(4 * manual_config.repeat_count, 20)

    def test_visible_keyword_inputs_can_include_detail_questions(self) -> None:
        current = AppConfig(keywords=["current"], target_domain="https://example.com")
        inputs = {
            **_base_inputs(),
            "keyword_inputs": [
                _Control("main question"),
                _Control("detail question"),
                _Control("hidden question"),
            ],
            "visible_keyword_count": lambda: 2,
        }

        config = build_config_from_inputs(inputs, current)

        self.assertEqual(config.keywords, ["main question", "detail question"])


if __name__ == "__main__":
    unittest.main()
