from __future__ import annotations

from typing import Any

from nicegui import ui

from config import ANALYSIS_MODE_MARKET, AppConfig
from runtime import common as runtime_common
from analysis_lib import split_csv, split_multiline_keywords
from ui.market_context_helpers import split_market_context_terms


def build_manual_runtime_config(config: AppConfig) -> AppConfig:
    base_repeat_count = max(1, int(config.repeat_count or 1))
    manual_repeat_count = max(1, (base_repeat_count + 1) // 2)
    return config.model_copy(update={"repeat_count": manual_repeat_count})


def _visible_keyword_limit(inputs: dict[str, Any]) -> int:
    visible_keyword_count = inputs.get("visible_keyword_count", 3)
    try:
        if callable(visible_keyword_count):
            visible_keyword_count = visible_keyword_count()
        return max(1, min(3, int(visible_keyword_count or 1)))
    except (TypeError, ValueError):
        return 3


def build_config_from_inputs(inputs: dict[str, Any], current: AppConfig) -> AppConfig:
    keyword_inputs = inputs.get("keyword_inputs") or []
    if keyword_inputs:
        visible_limit = _visible_keyword_limit(inputs)
        keywords = [
            str(control.value or "").strip()
            for control in keyword_inputs[:visible_limit]
            if str(control.value or "").strip()
        ]
    else:
        keywords = split_multiline_keywords(inputs["keywords"].value)
    return AppConfig(
        analysis_mode=ANALYSIS_MODE_MARKET,
        provider=current.provider,
        model=current.model,
        reasoning_effort=current.reasoning_effort,
        prompt_cache_key=current.prompt_cache_key,
        prompt_cache_retention=current.prompt_cache_retention,
        max_output_tokens=current.max_output_tokens,
        repeat_count=10,
        keywords=keywords,
        target_domain=inputs["target_domain"].value.strip(),
        brand_terms=split_csv(inputs["brand_terms"].value),
        market_context_terms=split_market_context_terms(inputs["market_context"].value),
        competitor_terms=split_csv(inputs["competitor_terms"].value),
        allowed_domains=current.allowed_domains,
        competitor_presets=current.competitor_presets,
        domain_scope_evaluation_axes=current.domain_scope_evaluation_axes,
        search_context_size=current.search_context_size,
        user_location_country=current.user_location_country,
        user_location_city=current.user_location_city,
        user_location_region=current.user_location_region,
        timezone=current.timezone,
        run_budget_guardrail_usd=current.run_budget_guardrail_usd,
        daily_budget_usd=current.daily_budget_usd,
        budget_guardrail_mode=current.budget_guardrail_mode,
        ui_port=current.ui_port,
        ui_host=current.ui_host,
        pricing=current.pricing,
    )


def notify_missing_required_fields(cfg: AppConfig, *, context: str) -> bool:
    missing = runtime_common.get_missing_required_fields(cfg)
    if not missing:
        return False
    ui.notify(f"{', '.join(missing)} を入力してください。", color="warning")
    return True
