from __future__ import annotations

from typing import Any

from analysis_lib import dedupe_preserve_order, normalize_domain_host, normalize_text, sanitize_runtime_error_message
from config import AppConfig, resolve_provider_cache_policy
from llmo_client import AnalysisResult


def get_missing_required_fields(config: AppConfig) -> list[str]:
    missing: list[str] = []
    if not [keyword for keyword in config.keywords if normalize_text(keyword)]:
        missing.append("質問")
    if not normalize_text(config.target_domain):
        missing.append("自社URL")
    return missing


def build_error_result(keyword: str, error_text: str, config: AppConfig | None = None) -> AnalysisResult:
    message = sanitize_runtime_error_message(error_text)
    analysis_context: dict[str, Any] = {}
    if config is not None:
        cache_policy = resolve_provider_cache_policy(config.provider, config.model, config.prompt_cache_retention)
        analysis_context = {
            "analysis_mode": config.analysis_mode,
            "target_domain": config.target_domain,
            "brand_terms": config.brand_terms,
            "market_context_terms": config.market_context_terms,
            "competitor_terms": config.competitor_terms,
            "allowed_domains": config.allowed_domains,
            "owned_only_domains": dedupe_preserve_order(
                [normalize_domain_host(config.target_domain), *[normalize_domain_host(item) for item in config.allowed_domains]]
            ),
            "model": config.model,
            "reasoning_effort": config.reasoning_effort,
            "search_context_size": config.search_context_size,
            "prompt_cache_retention_requested": config.prompt_cache_retention,
            "prompt_cache_retention_effective": cache_policy["effective"],
            "prompt_cache_policy_label": cache_policy["display_label"],
            "prompt_cache_policy_note": cache_policy["note"],
        }
    return AnalysisResult(
        keyword_raw=keyword,
        keyword_norm=keyword,
        output_text=message,
        output_json={
            "keyword_raw": keyword,
            "keyword_norm": keyword,
            "answer_snapshot": "実行エラー。設定またはAPI応答を確認してください。",
            "answer_text": message or "エラー内容を確認してから再実行してください。",
            "visibility_score": 0,
            "target_domain_hit": False,
            "brand_mention_hit": False,
            "competitor_mentions": [],
            "confidence": "low",
            "recommended_actions": [
                "APIキーと接続設定を確認する",
                "質問か優先ドメインを絞る",
                "検索応答を再実行して確認する",
            ],
            "citations": [],
            "citation_urls": [],
            "security_signals": {
                "suspicious_prompt_injection": False,
                "matched_patterns": [],
                "signal_count": 0,
                "low_trust_source_detected": False,
            },
            "analysis_context": analysis_context,
        },
        usage={},
        web_search_calls=0,
        sources=[],
        estimated_cost_usd=0.0,
    )
