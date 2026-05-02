from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from pydantic import BaseModel, Field

from analysis_core.common_constants import PROMPT_CACHE_24H_SUPPORTED_MODELS
from plan_catalog import DEFAULT_PLAN_KEY, SERVICE_KOTOMEGANE, resolve_plan_question_budget

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
CONFIG_DIR = ROOT_DIR / "config"
DOCS_DIR = ROOT_DIR / "docs"
ASSETS_DIR = ROOT_DIR / "assets"
EXPORTS_DIR = ROOT_DIR / "exports"
DB_PATH = DATA_DIR / "llmo_poc.db"
CONFIG_PATH = CONFIG_DIR / "llmo_poc_settings.json"
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=False)

ALLOWED_DOMAINS_MODE_SOFT = "soft_preference"
ALLOWED_DOMAINS_MODE_HARD = "hard_filter"
ANALYSIS_MODE_MARKET = "market"
ANALYSIS_MODE_OWNED_ONLY = "owned_only"
ALLOWED_DOMAINS_SOFT_NOTE = (
    "Responses API の web_search tool では allowed_domains を hard filter として送らず、"
    "payload 内で優先参照先として案内する soft constraint 運用です。"
)
ALLOWED_DOMAINS_HARD_NOTE = (
    "Owned-only Audit では Responses API の web_search.filters.allowed_domains を使い、"
    "自社または許可したドメインだけに検索対象を絞ります。"
)
OPENAI_BATCH_ENDPOINT = "/v1/responses"
OPENAI_BATCH_COMPLETION_WINDOW = "24h"
OPENAI_BATCH_MODE_NOTE = (
    "Batch モードは OpenAI Batch API に JSONL を投入する非同期実行です。"
    "通常実行の prompt caching を置き換えず、大量投入だけを分離します。"
)
PROVIDER_ENABLEMENT_ENV_VAR = "KOTOMEGANE_ENABLED_PROVIDERS"
DEFAULT_ENABLED_PROVIDER_KEYS = ("openai", "gemini", "claude")


class PricingConfig(BaseModel):
    model: str = "gpt-5.4-nano"
    input_per_million: float = 0.20
    cached_input_per_million: float = 0.02
    output_per_million: float = 1.25
    web_search_call_per_1k: float = 10.0
    usd_to_jpy: float = 160.0
    show_poc_costs: bool = True

    def exchange_rate_label(self) -> str:
        return f"1 USD = {self.usd_to_jpy:,.0f} JPY"


class DeterministicScoringConfig(BaseModel):
    target_domain_hit_weight: int = 40
    brand_mention_hit_weight: int = 15
    owned_citation_weight: int = 12
    owned_citation_share_weight: int = 15
    competitor_mention_penalty: int = 12
    external_only_penalty: int = 18
    no_owned_cap: int = 44
    brand_only_cap: int = 64
    answer_type_weights: dict[str, int] = Field(
        default_factory=lambda: {
            "comparison": 4,
            "price": 3,
            "faq": 2,
            "case_study": 4,
            "local": 3,
            "branded": 6,
            "how_to": 2,
            "general": 1,
        }
    )


class VarianceConfig(BaseModel):
    score_stddev_threshold: float = 18.0
    score_range_threshold: float = 45.0
    low_owned_hit_rate_threshold: float = 50.0


class ProviderOption(BaseModel):
    key: str
    label: str
    status: str
    summary: str
    note: str
    default_model: str
    default_total_question_budget: int = 30
    env_var: str | None = None
    implemented: bool = False
    supports_live_requests: bool = False
    supports_batch: bool = False
    supports_prompt_cache: bool = False
    supports_extended_prompt_cache: bool = False
    supports_query_planner_reuse: bool = False
    preferred_batch_mode: str = "none"
    cache_policy_mode: str = "no_cache"
    expansion_mode: str = "llm_planner"
    max_expansion_queries: int = 4
    batch_endpoint: str = ""
    batch_completion_window: str = ""
    batch_timeout_hours: int = 24
    partial_display_after_hours: int = 24
    partial_display_policy: str = "hold_until_complete"
    cost_reduction_note: str = ""
    allowed_domains_mode: str | None = None
    allowed_domains_note: str | None = None
    models: list[str] = Field(default_factory=list)


class ApiKeyStatus(BaseModel):
    provider_key: str
    env_var: str
    present: bool
    source: str
    message: str


class AppConfig(BaseModel):
    service_key: str = SERVICE_KOTOMEGANE
    plan_key: str = DEFAULT_PLAN_KEY
    analysis_mode: str = ANALYSIS_MODE_MARKET
    enabled_provider_keys: list[str] = Field(default_factory=lambda: list(DEFAULT_ENABLED_PROVIDER_KEYS))
    provider: str = "openai"
    model: str = "gpt-5.4-nano"
    query_planner_model: str = "gpt-5.4-nano"
    query_planner_reasoning_effort: str = "medium"
    query_planner_max_output_tokens: int = 1200
    query_expansion_max_total_queries: int = 5
    query_expansion_shorten_threshold_chars: int = 50
    query_expansion_template_set: str = "business_ja"
    query_execution_order: str = "query_then_repeat"
    reasoning_effort: str = "low"
    prompt_cache_key: str = "llmo-poc-v1"
    prompt_cache_retention: str = "24h"
    max_output_tokens: int = 1200
    repeat_count: int = 20
    keywords: list[str] = Field(
        default_factory=lambda: [
            "B2B SaaS の AI検索可視性を改善する方法",
            "生成AI向けFAQ設計のベストプラクティス",
            "AI検索でブランド想起を高めるには",
        ]
    )
    target_domain: str = ""
    brand_terms: list[str] = Field(default_factory=list)
    market_context_terms: list[str] = Field(default_factory=list)
    competitor_terms: list[str] = Field(default_factory=list)
    allowed_domains: list[str] = Field(default_factory=list)
    search_context_size: str = "medium"
    user_location_country: str = "JP"
    user_location_city: str = "Tokyo"
    user_location_region: str = "Tokyo"
    timezone: str = "Asia/Tokyo"
    run_budget_guardrail_usd: float = 1.2
    daily_budget_usd: float = 1.0
    budget_guardrail_mode: str = "warn"
    ui_port: int = 8083
    ui_host: str = "127.0.0.1"
    pricing: PricingConfig = Field(default_factory=PricingConfig)
    deterministic_scoring: DeterministicScoringConfig = Field(default_factory=DeterministicScoringConfig)
    variance: VarianceConfig = Field(default_factory=VarianceConfig)
    enable_topic_signals: bool = True
    topic_signal_max_terms: int = 5
    topic_signal_max_doc_freq_ratio: float = 0.85


PROVIDER_CATALOG: tuple[ProviderOption, ...] = (
    ProviderOption(
        key="openai",
        label="ChatGPT",
        status="active",
        summary="Responses API と web_search で露出を測定",
        note="通常実行と一括実行に対応",
        default_model="gpt-5.4-nano",
        default_total_question_budget=30,
        env_var="OPENAI_API_KEY",
        implemented=True,
        supports_live_requests=True,
        supports_batch=True,
        supports_prompt_cache=True,
        supports_extended_prompt_cache=False,
        supports_query_planner_reuse=True,
        preferred_batch_mode="provider_batch",
        cache_policy_mode="responses_api_prompt_cache",
        expansion_mode="llm_planner",
        max_expansion_queries=4,
        batch_endpoint=OPENAI_BATCH_ENDPOINT,
        batch_completion_window=OPENAI_BATCH_COMPLETION_WINDOW,
        batch_timeout_hours=24,
        partial_display_after_hours=24,
        partial_display_policy="partial_after_timeout_gray_pending",
        cost_reduction_note="通常実行は prompt caching、定期リサーチは Batch API を優先します。",
        allowed_domains_mode=ALLOWED_DOMAINS_MODE_SOFT,
        allowed_domains_note=ALLOWED_DOMAINS_SOFT_NOTE,
        models=["gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"],
    ),
    ProviderOption(
        key="gemini",
        label="Gemini",
        status="active",
        summary="Google Search grounding で露出を測定",
        note="手動確認と Batch に対応。implicit caching を既定とし、explicit cache は後続で扱う",
        default_model="gemini-2.5-flash-lite",
        default_total_question_budget=30,
        env_var="GEMINI_API_KEY",
        implemented=True,
        supports_live_requests=True,
        supports_batch=True,
        supports_prompt_cache=False,
        supports_extended_prompt_cache=False,
        supports_query_planner_reuse=True,
        preferred_batch_mode="provider_batch",
        cache_policy_mode="implicit_context_cache",
        expansion_mode="llm_planner",
        max_expansion_queries=4,
        batch_endpoint="models/{model}:batchGenerateContent",
        batch_completion_window="24h",
        batch_timeout_hours=24,
        partial_display_after_hours=24,
        partial_display_policy="partial_after_timeout_gray_pending",
        cost_reduction_note="manual/live と Batch は稼働。2.5 系は implicit caching を既定で使い、Batch でも context caching が有効です。",
        models=["gemini-2.5-flash-lite", "gemini-2.5-flash"],
    ),
    ProviderOption(
        key="claude",
        label="Claude",
        status="active",
        summary="Messages API と web search tool で露出を測定",
        note="手動確認と Batch に対応。automatic caching は 5分前提、1時間 cache は未接続",
        default_model="claude-3-5-haiku-latest",
        default_total_question_budget=15,
        env_var="ANTHROPIC_API_KEY",
        implemented=True,
        supports_live_requests=True,
        supports_batch=True,
        supports_prompt_cache=False,
        supports_extended_prompt_cache=False,
        supports_query_planner_reuse=True,
        preferred_batch_mode="provider_batch",
        cache_policy_mode="automatic_prompt_cache",
        expansion_mode="llm_planner",
        max_expansion_queries=4,
        batch_endpoint="/v1/messages/batches",
        batch_completion_window="24h",
        batch_timeout_hours=24,
        partial_display_after_hours=24,
        partial_display_policy="partial_after_timeout_gray_pending",
        cost_reduction_note="manual/live と Batch は稼働。automatic caching は既定 5分で、Batch の cache hit は best-effort です。",
        models=["claude-3-5-haiku-latest", "claude-sonnet-4-20250514"],
    ),
)


def ensure_app_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> AppConfig:
    ensure_app_dirs()
    if CONFIG_PATH.exists():
        return AppConfig.model_validate_json(CONFIG_PATH.read_text(encoding="utf-8"))
    config = AppConfig()
    save_config(config)
    return config


def save_config(config: AppConfig) -> None:
    ensure_app_dirs()
    CONFIG_PATH.write_text(
        json.dumps(config.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_provider_catalog() -> list[ProviderOption]:
    return [provider.model_copy(deep=True) for provider in PROVIDER_CATALOG]


def get_provider_option(provider_key: str) -> ProviderOption:
    for provider in PROVIDER_CATALOG:
        if provider.key == provider_key:
            return provider.model_copy(deep=True)
    return PROVIDER_CATALOG[0].model_copy(deep=True)


def get_models_for_provider(provider_key: str) -> list[str]:
    return list(get_provider_option(provider_key).models)


def get_provider_default_model(provider_key: str) -> str:
    provider = get_provider_option(provider_key)
    return provider.default_model or (provider.models[0] if provider.models else "")


def get_provider_total_question_budget(
    provider_key: str,
    *,
    service_key: str = SERVICE_KOTOMEGANE,
    plan_key: str = DEFAULT_PLAN_KEY,
) -> int:
    provider = get_provider_option(provider_key)
    return resolve_plan_question_budget(
        provider.key,
        service_key=service_key,
        plan_key=plan_key,
        fallback_budget=provider.default_total_question_budget,
    )


def get_provider_effective_model(provider_key: str, requested_model: str) -> str:
    provider = get_provider_option(provider_key)
    requested = str(requested_model or "").strip()
    if requested and requested in provider.models:
        return requested
    if provider.default_model:
        return provider.default_model
    if provider.models:
        return provider.models[0]
    return requested


def provider_supports_batch(provider_key: str) -> bool:
    return bool(get_provider_option(provider_key).supports_batch)


def provider_supports_live_requests(provider_key: str) -> bool:
    return bool(get_provider_option(provider_key).supports_live_requests)


def provider_supports_prompt_cache(provider_key: str) -> bool:
    return bool(get_provider_option(provider_key).supports_prompt_cache)


def resolve_prompt_cache_retention_by_model(model: str, requested: str) -> str:
    requested_value = str(requested or "").strip().lower() or "in_memory"
    if requested_value != "24h":
        return "in_memory"
    return "24h" if str(model or "").strip().lower() in PROMPT_CACHE_24H_SUPPORTED_MODELS else "in_memory"


def resolve_provider_cache_policy(provider_key: str, model: str, requested: str) -> dict[str, str]:
    provider = get_provider_option(provider_key)
    requested_value = str(requested or "").strip().lower() or "in_memory"
    if provider.key == "openai":
        effective = resolve_prompt_cache_retention_by_model(model, requested_value)
        return {
            "mode": "responses_api_prompt_cache",
            "requested": requested_value,
            "effective": effective,
            "display_label": "24時間" if effective == "24h" else "メモリ内",
            "note": "OpenAI は prompt_cache_key を使う explicit prompt caching。24時間 retention は対応モデルのみ有効です。",
            "switch_note": (
                "24時間キャッシュが使えない条件では、自動でメモリ内へ切り替えています。"
                if requested_value == "24h" and effective != "24h"
                else ""
            ),
        }
    if provider.key == "gemini":
        return {
            "mode": "implicit_context_cache",
            "requested": requested_value,
            "effective": "implicit",
            "display_label": "provider既定",
            "note": "Gemini 2.5+ は implicit caching が既定です。explicit cache の既定 TTL は 1時間で、Batch でも context caching が有効です。",
            "switch_note": "",
        }
    if provider.key == "claude":
        return {
            "mode": "automatic_prompt_cache",
            "requested": requested_value,
            "effective": "automatic_5m",
            "display_label": "自動5分",
            "note": "Claude は automatic prompt caching が既定 5分です。1時間 cache は未接続で、Batch の cache hit は best-effort です。",
            "switch_note": "",
        }
    return {
        "mode": "no_cache",
        "requested": requested_value,
        "effective": "in_memory",
        "display_label": "未使用",
        "note": "この接続先では prompt cache を前提にしていません。",
        "switch_note": "",
    }


def get_provider_batch_endpoint(provider_key: str) -> str:
    return str(get_provider_option(provider_key).batch_endpoint or "")


def get_provider_batch_completion_window(provider_key: str) -> str:
    return str(get_provider_option(provider_key).batch_completion_window or "")


def get_provider_api_key(provider_key: str) -> str:
    provider = get_provider_option(provider_key)
    if not provider.env_var:
        return ""
    return os.getenv(provider.env_var, "").strip()


def _normalize_provider_key_list(keys: list[str] | tuple[str, ...] | str | None) -> list[str]:
    if keys is None:
        return []
    if isinstance(keys, str):
        raw_items = keys.split(",")
    else:
        raw_items = list(keys)
    catalog_keys = {provider.key for provider in PROVIDER_CATALOG}
    normalized: list[str] = []
    for item in raw_items:
        key = str(item or "").strip().lower()
        if key and key in catalog_keys and key not in normalized:
            normalized.append(key)
    return normalized


def get_effective_enabled_provider_keys(config: AppConfig | None = None) -> list[str]:
    env_keys = _normalize_provider_key_list(os.getenv(PROVIDER_ENABLEMENT_ENV_VAR, ""))
    if env_keys:
        return env_keys
    config_keys = _normalize_provider_key_list(config.enabled_provider_keys if config is not None else None)
    if config_keys:
        return config_keys
    return list(DEFAULT_ENABLED_PROVIDER_KEYS)


def provider_is_enabled(config: AppConfig | None, provider_key: str) -> bool:
    return str(provider_key or "").strip().lower() in set(get_effective_enabled_provider_keys(config))


def get_api_key_status(provider_key: str) -> ApiKeyStatus:
    provider = get_provider_option(provider_key)
    env_var = provider.env_var or ""
    env_values = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    env_file_value = str(env_values.get(env_var) or "").strip()
    active_value = os.getenv(env_var, "").strip()

    if env_file_value and active_value and env_file_value != active_value:
        return ApiKeyStatus(
            provider_key=provider.key,
            env_var=env_var,
            present=True,
            source="environment_override",
            message=f"{env_var} は環境変数を優先して使用します。.env の値は上書きしません。",
        )
    if env_file_value:
        return ApiKeyStatus(
            provider_key=provider.key,
            env_var=env_var,
            present=True,
            source="dot_env",
            message=f"{env_var} は .env から読み込みます。",
        )
    if active_value:
        return ApiKeyStatus(
            provider_key=provider.key,
            env_var=env_var,
            present=True,
            source="environment",
            message=f"{env_var} は process / user / machine 環境変数から利用できます。",
        )
    return ApiKeyStatus(
        provider_key=provider.key,
        env_var=env_var,
        present=False,
        source="missing",
        message=f"{env_var} は .env と環境変数のどちらにも見つかりません。",
    )
