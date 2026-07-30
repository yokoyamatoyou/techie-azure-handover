from __future__ import annotations

from config import get_provider_option
from runtime_mode import is_readonly_demo_mode, readonly_demo_block_message

from llmo_core.claude_client import ClaudeClient
from llmo_core.gemini_client import GeminiClient
from llmo_core.models import NotImplementedProviderClient, ProviderClient
from llmo_core.openai_client import LLMOClient

PROVIDER_CLIENT_FACTORIES: dict[str, type[ProviderClient]] = {
    "openai": LLMOClient,
    "gemini": GeminiClient,
    "claude": ClaudeClient,
}


def build_provider_client(provider_key: str) -> ProviderClient:
    if is_readonly_demo_mode():
        raise RuntimeError(readonly_demo_block_message("provider client creation"))
    provider = get_provider_option(provider_key)
    client_factory = PROVIDER_CLIENT_FACTORIES.get(provider.key)
    if client_factory is not None and provider.supports_live_requests:
        return client_factory()
    return NotImplementedProviderClient(provider.key)
