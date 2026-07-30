from __future__ import annotations

import unittest

from config import AppConfig, get_provider_effective_model, resolve_provider_cache_policy
from ui.provider_runtime_controls import normalize_provider_config, select_provider_config


class ProviderModelConfigTests(unittest.TestCase):
    def test_openai_custom_model_from_config_survives_normalization(self) -> None:
        config = AppConfig(provider="openai", model="gpt-5.6-luna")

        normalized = normalize_provider_config(config)

        self.assertEqual(normalized.provider, "openai")
        self.assertEqual(normalized.model, "gpt-5.6-luna")
        self.assertEqual(get_provider_effective_model("openai", "gpt-5.6-luna"), "gpt-5.6-luna")

    def test_switching_provider_uses_that_provider_default_model(self) -> None:
        config = AppConfig(provider="openai", model="gpt-5.6-luna")

        selected = select_provider_config(config, "gemini")

        self.assertEqual(selected.provider, "gemini")
        self.assertEqual(selected.model, "gemini-2.5-flash-lite")

    def test_unknown_openai_model_uses_safe_prompt_cache_fallback(self) -> None:
        cache_policy = resolve_provider_cache_policy("openai", "gpt-5.6-luna", "24h")

        self.assertEqual(cache_policy["requested"], "24h")
        self.assertEqual(cache_policy["effective"], "in_memory")


if __name__ == "__main__":
    unittest.main()
