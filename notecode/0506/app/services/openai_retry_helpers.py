from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from typing import Any


RETRYABLE_STATUS_CODES = {408, 500, 502, 503, 504, 520}


def is_transient_openai_error(exc: BaseException) -> bool:
    if is_timeout_error(exc):
        return True
    if type(exc).__name__ == "APIConnectionError":
        return True
    return status_code(exc) in RETRYABLE_STATUS_CODES


def is_timeout_error(exc: BaseException) -> bool:
    return isinstance(exc, TimeoutError) or type(exc).__name__ == "APITimeoutError"


def status_code(exc: BaseException) -> int:
    value = getattr(exc, "status_code", 0) or 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def request_id_from_response(response: Any) -> str:
    return str(getattr(response, "_request_id", "") or getattr(response, "request_id", "") or "")


def response_id(response: Any) -> str:
    return str(getattr(response, "id", "") or getattr(response, "response_id", "") or "")


def request_id_from_error(exc: BaseException) -> str:
    return str(getattr(exc, "request_id", "") or getattr(exc, "_request_id", "") or "")


def response_id_from_error(exc: BaseException) -> str:
    return str(getattr(exc, "response_id", "") or "")


def retry_after_seconds(exc: BaseException) -> float:
    candidates: list[Any] = [
        getattr(exc, "retry_after_seconds", None),
        getattr(exc, "retry_after", None),
    ]
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    header_get = getattr(headers, "get", None)
    if callable(header_get):
        candidates.extend([header_get("retry-after"), header_get("Retry-After")])

    text = str(exc or "")
    match = re.search(r"['\"]retry_after(?:_seconds)?['\"]\s*:\s*([0-9]+(?:\.[0-9]+)?)", text)
    if match:
        candidates.append(match.group(1))

    for value in candidates:
        try:
            seconds = float(value or 0.0)
        except (TypeError, ValueError):
            continue
        if seconds > 0:
            return seconds
    return 0.0


def redact_error_text(exc: BaseException) -> str:
    text = str(exc or "")
    text = re.sub(r"sk-[A-Za-z0-9_\-]{12,}", "[REDACTED_SECRET]", text)
    text = re.sub(r"OPENAI_API_KEY\s*=\s*[^\s]+", "OPENAI_API_KEY=[REDACTED_SECRET]", text, flags=re.IGNORECASE)
    return text[:500]


def packet_id(payload: dict[str, Any]) -> str:
    packet = payload.get("source_packet") if isinstance(payload, dict) else None
    if isinstance(packet, dict):
        return str(packet.get("source_id") or packet.get("title") or "").strip()
    return ""


def payload_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default
