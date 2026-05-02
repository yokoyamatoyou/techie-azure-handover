from __future__ import annotations

import statistics
from typing import Any

from config import AppConfig

from analysis_core.common_constants import PROMPT_CACHE_24H_SUPPORTED_MODELS
from analysis_core.common_io import parse_json_object
from analysis_core.text_utils import normalize_text


def is_extended_prompt_cache_supported(model: str) -> bool:
    return normalize_text(model) in PROMPT_CACHE_24H_SUPPORTED_MODELS


def resolve_prompt_cache_retention(model: str, requested: str) -> str:
    requested_value = normalize_text(requested) or "in_memory"
    if requested_value != "24h":
        return "in_memory"
    return "24h" if is_extended_prompt_cache_supported(model) else "in_memory"


def clamp_score(value: Any) -> int:
    try:
        resolved = int(round(float(value or 0)))
    except (TypeError, ValueError):
        resolved = 0
    return max(0, min(100, resolved))


def resolve_visibility_score(row: dict[str, Any], payload: dict[str, Any] | None = None) -> int:
    if row.get("deterministic_score") is not None:
        return clamp_score(row.get("deterministic_score"))
    effective_payload = payload or parse_json_object(row.get("output_json"))
    if effective_payload.get("deterministic_score") is not None:
        return clamp_score(effective_payload.get("deterministic_score"))
    return clamp_score(row.get("visibility_score"))


def resolve_raw_llm_score(row: dict[str, Any], payload: dict[str, Any] | None = None) -> int:
    if row.get("raw_llm_score") is not None:
        return clamp_score(row.get("raw_llm_score"))
    effective_payload = payload or parse_json_object(row.get("output_json"))
    raw_score = effective_payload.get("raw_llm_score")
    if raw_score is not None:
        return clamp_score(raw_score)
    return clamp_score(effective_payload.get("visibility_score"))


def build_variance_metrics(scores: list[float], *, owned_hit_rate: float = 0.0, config: AppConfig | None = None) -> dict[str, Any]:
    cfg = config or AppConfig()
    cleaned = [float(score) for score in scores if score is not None]
    if not cleaned:
        return {
            "sample_count": 0,
            "median_score": 0.0,
            "min_score": 0.0,
            "max_score": 0.0,
            "score_stddev": 0.0,
            "score_range": 0.0,
            "variance_flag": False,
            "variance_label": "観測なし",
        }
    median_score = round(float(statistics.median(cleaned)), 1)
    min_score = round(min(cleaned), 1)
    max_score = round(max(cleaned), 1)
    score_range = round(max_score - min_score, 1)
    score_stddev = round(statistics.pstdev(cleaned), 1) if len(cleaned) > 1 else 0.0
    variance_flag = bool(
        score_stddev >= float(cfg.variance.score_stddev_threshold)
        or score_range >= float(cfg.variance.score_range_threshold)
        or float(owned_hit_rate or 0.0) < float(cfg.variance.low_owned_hit_rate_threshold)
    )
    if len(cleaned) <= 1:
        variance_label = "観測1回"
    elif variance_flag and score_stddev >= float(cfg.variance.score_stddev_threshold):
        variance_label = "揺れ大"
    elif variance_flag:
        variance_label = "揺れ注意"
    else:
        variance_label = "安定"
    return {
        "sample_count": len(cleaned),
        "median_score": median_score,
        "min_score": min_score,
        "max_score": max_score,
        "score_stddev": score_stddev,
        "score_range": score_range,
        "variance_flag": variance_flag,
        "variance_label": variance_label,
    }


def build_deterministic_score_fields(
    payload: dict[str, Any],
    structured: dict[str, Any],
    *,
    config: AppConfig | None = None,
) -> dict[str, Any]:
    cfg = config or AppConfig()
    scoring = cfg.deterministic_scoring
    raw_llm_score = clamp_score(payload.get("visibility_score"))
    target_hit = bool(structured.get("owned_domain_hit"))
    brand_hit = bool(structured.get("owned_brand_hit"))
    owned_citation_count = max(0, int(structured.get("owned_citation_count") or 0))
    owned_citation_share = max(0.0, min(1.0, float(structured.get("owned_citation_share") or 0.0)))
    competitor_hit = bool(structured.get("competitor_mention_hit"))
    external_only_result = bool(structured.get("external_only_result"))
    answer_type_key = normalize_text(str(structured.get("answer_type_key") or "")) or "general"
    answer_type_bonus = int(scoring.answer_type_weights.get(answer_type_key, scoring.answer_type_weights.get("general", 0)) or 0)

    deterministic_score = 0
    if target_hit:
        deterministic_score += int(scoring.target_domain_hit_weight)
    if brand_hit:
        deterministic_score += int(scoring.brand_mention_hit_weight)
    deterministic_score += min(3, owned_citation_count) * int(scoring.owned_citation_weight)
    deterministic_score += int(round(owned_citation_share * float(scoring.owned_citation_share_weight)))
    deterministic_score += answer_type_bonus
    if competitor_hit:
        deterministic_score -= int(scoring.competitor_mention_penalty)
    if external_only_result:
        deterministic_score -= int(scoring.external_only_penalty)

    if not target_hit and not brand_hit:
        deterministic_score = min(int(scoring.no_owned_cap), deterministic_score)
    elif brand_hit and not target_hit:
        deterministic_score = min(int(scoring.brand_only_cap), deterministic_score)

    deterministic_score = clamp_score(deterministic_score)
    return {
        "raw_llm_score": raw_llm_score,
        "deterministic_score": deterministic_score,
        "visibility_score": deterministic_score,
    }


def classify_visibility_verdict(score: int, target_hit: bool, brand_hit: bool) -> str:
    if target_hit and brand_hit and score >= 70:
        return "自社優勢"
    if target_hit or brand_hit:
        return "自社あり"
    if score >= 45:
        return "外部サイト優勢"
    return "未露出"
