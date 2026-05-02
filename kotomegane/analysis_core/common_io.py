from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from config import AppConfig

from analysis_core.text_utils import normalize_text


def usage_to_dict(usage: Any) -> dict[str, Any]:
    if usage is None:
        return {}
    if isinstance(usage, dict):
        return usage
    result = {}
    for name in ("input_tokens", "output_tokens", "total_tokens"):
        result[name] = getattr(usage, name, 0)
    input_details = getattr(usage, "input_tokens_details", None)
    if input_details is None:
        result["input_tokens_details"] = {}
    elif isinstance(input_details, dict):
        result["input_tokens_details"] = input_details
    else:
        result["input_tokens_details"] = {
            "cached_tokens": getattr(input_details, "cached_tokens", 0),
        }
    return result


def estimate_cost_usd(
    usage: dict[str, Any],
    web_search_calls: int,
    config: AppConfig,
) -> float:
    if normalize_text(config.provider) != "openai":
        return 0.0
    pricing = config.pricing
    input_tokens = float(usage.get("input_tokens") or 0)
    output_tokens = float(usage.get("output_tokens") or 0)
    cached_tokens = float((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
    uncached_tokens = max(0.0, input_tokens - cached_tokens)

    model_cost = (
        uncached_tokens * pricing.input_per_million
        + cached_tokens * pricing.cached_input_per_million
        + output_tokens * pricing.output_per_million
    ) / 1_000_000
    search_cost = web_search_calls * (pricing.web_search_call_per_1k / 1000)
    return round(model_cost + search_cost, 6)


def usd_to_jpy(amount_usd: float, rate: float) -> float:
    return round(float(amount_usd or 0.0) * float(rate or 0.0), 2)


def format_cost_pair(
    amount_usd: float,
    rate: float,
    *,
    compact: bool = False,
) -> str:
    usd = float(amount_usd or 0.0)
    jpy = usd_to_jpy(usd, rate)
    if compact:
        return f"${usd:.4f} / ¥{jpy:,.0f}"
    return f"${usd:.4f} (¥{jpy:,.0f})"


def format_exchange_rate(rate: float) -> str:
    return f"1 USD = {float(rate or 0.0):,.0f} JPY"


def parse_json_object(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        parsed = json.loads(str(raw))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def sanitize_external_url(raw: Any) -> str:
    url = str(raw or "").strip()
    if not url:
        return ""
    try:
        parts = urlsplit(url)
    except Exception:
        return ""
    scheme = str(parts.scheme or "").strip().lower()
    netloc = str(parts.netloc or "").strip()
    if scheme not in {"http", "https"} or not netloc:
        return ""
    path = parts.path or "/"
    safe_parts = (scheme, netloc, path, parts.query or "", "")
    return urlunsplit(safe_parts)


def sanitize_runtime_error_message(raw: Any, *, max_length: int = 180) -> str:
    message = normalize_text(str(raw or ""))
    if not message:
        return "実行中にエラーが発生しました。設定と接続状況を確認して再実行してください。"
    redacted = re.sub(r"sk-[A-Za-z0-9_-]{12,}", "[redacted-token]", message)
    redacted = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)[^\s,;]+", r"\1[redacted-token]", redacted)
    redacted = re.sub(r"(?i)\b([A-Z_]*API[_-]?KEY)\s*[:=]\s*[^\s,;]+", r"\1=[redacted]", redacted)
    redacted = re.sub(r"\s+", " ", redacted).strip()
    if not redacted:
        redacted = "実行中にエラーが発生しました。設定と接続状況を確認して再実行してください。"
    if len(redacted) > max_length:
        redacted = redacted[: max(0, max_length - 1)].rstrip() + "…"
    return redacted
