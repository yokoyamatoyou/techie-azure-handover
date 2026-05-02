"""Shared strict SaaS mode policy helpers."""
from __future__ import annotations

from typing import Any

STRICT_SAAS_MODES: tuple[str, ...] = ("small", "medium", "large")
DEFAULT_STRICT_SAAS_MODE = "small"
UI_DEFAULT_STRICT_SAAS_MODE = "medium"


def normalize_strict_saas_mode(value: Any, *, default: str = DEFAULT_STRICT_SAAS_MODE) -> str:
    candidate = str(value or "").strip().lower()
    if candidate in STRICT_SAAS_MODES:
        return candidate
    return default


def requires_explicit_profile_inputs(mode: Any) -> bool:
    return normalize_strict_saas_mode(mode) in {"medium", "large"}


def requires_llm_execution(mode: Any) -> bool:
    return normalize_strict_saas_mode(mode) in {"medium", "large"}


def blocks_prompt_intent_rewrite(mode: Any) -> bool:
    return normalize_strict_saas_mode(mode) == "large"


def allows_semantic_fallback(mode: Any) -> bool:
    return normalize_strict_saas_mode(mode) == "small"


def allows_guard_auto_repair(mode: Any) -> bool:
    return normalize_strict_saas_mode(mode) == "small"


def allows_quality_fail_open(mode: Any, *, config_fail_open: bool) -> bool:
    return bool(config_fail_open) and normalize_strict_saas_mode(mode) == "small"
