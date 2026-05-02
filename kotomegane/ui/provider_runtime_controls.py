from __future__ import annotations

from typing import Any

from nicegui import ui

from config import (
    AppConfig,
    ProviderOption,
    get_effective_enabled_provider_keys,
    get_provider_catalog,
    get_provider_effective_model,
    get_provider_option,
    provider_is_enabled,
)
from ui.runtime_copy_builders import build_cost_policy_text, build_runtime_microcopy

VISIBLE_PROVIDER_KEYS = ("openai", "gemini", "claude")


def get_visible_provider_catalog(config: AppConfig | None = None) -> list[ProviderOption]:
    enabled_keys = set(get_effective_enabled_provider_keys(config))
    return [
        provider
        for provider in get_provider_catalog()
        if provider.key in VISIBLE_PROVIDER_KEYS and provider.key in enabled_keys
    ]


def get_default_live_provider(config: AppConfig) -> ProviderOption:
    for provider in get_visible_provider_catalog(config):
        if provider.implemented and provider.supports_live_requests:
            return provider
    return get_provider_option("openai")


def normalize_provider_config(config: AppConfig) -> AppConfig:
    next_config = config
    provider = get_provider_option(next_config.provider)
    fallback = get_default_live_provider(next_config)
    if (
        provider.key not in VISIBLE_PROVIDER_KEYS
        or not provider_is_enabled(next_config, provider.key)
        or not provider.implemented
        or not provider.supports_live_requests
    ):
        next_model = get_provider_effective_model(fallback.key, next_config.model)
        return next_config.model_copy(update={"provider": fallback.key, "model": next_model})
    next_updates: dict[str, Any] = {
        "model": get_provider_effective_model(provider.key, next_config.model),
    }
    if provider.key == "openai":
        if str(next_config.prompt_cache_retention or "").strip().lower() != "24h":
            next_updates["prompt_cache_retention"] = "24h"
    else:
        next_updates["prompt_cache_retention"] = "in_memory"
    if (
        next_updates.get("model") != next_config.model
        or next_updates.get("prompt_cache_retention", next_config.prompt_cache_retention)
        != next_config.prompt_cache_retention
    ):
        return next_config.model_copy(update=next_updates)
    return next_config


def refresh_provider_controls(
    config: AppConfig,
    provider_buttons: dict[str, ui.button],
) -> AppConfig:
    next_config = normalize_provider_config(config)

    for key, button in provider_buttons.items():
        option = get_provider_option(key)
        if not provider_is_enabled(next_config, key) or not option.implemented:
            tone = "provider-chip-button provider-chip-button-disabled"
            button.disable()
        elif key == next_config.provider:
            tone = "provider-chip-button provider-chip-button-active"
            button.enable()
        else:
            tone = "provider-chip-button provider-chip-button-ready"
            button.enable()
        button.classes(replace=tone)
        button.update()

    return next_config


def select_provider_config(
    config: AppConfig,
    provider_key: str,
) -> AppConfig:
    provider = get_provider_option(provider_key)
    visible_provider_keys = {item.key for item in get_visible_provider_catalog(config)}
    if provider.key not in visible_provider_keys or not provider.implemented or not provider.supports_live_requests:
        return normalize_provider_config(config)
    next_model = config.model if config.model in provider.models else provider.models[0] if provider.models else config.model
    return normalize_provider_config(config.model_copy(update={"provider": provider_key, "model": next_model}))


def refresh_runtime_panels(
    config: AppConfig,
    runtime_micro_label: ui.label,
    cost_policy_label: ui.label,
) -> None:
    runtime_micro_label.text = build_runtime_microcopy(config)
    cost_policy_label.text = build_cost_policy_text(config)
    runtime_micro_label.update()
    cost_policy_label.update()
