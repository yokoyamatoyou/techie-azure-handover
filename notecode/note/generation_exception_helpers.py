"""生成失敗 / archived output guard retry に関する helper を集約する sibling module。

`note_writer_app.py` から切り出した delegate のみを置く。
- 現行 writer-only 経路で使う例外分類はローカル実装として残す。
- archived output guard retry helpers は呼ばれた時だけ旧moduleへ遅延delegateする。
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, List


def _output_guard_call(attribute_name: str, *args: Any, **kwargs: Any) -> Any:
    module = importlib.import_module("note.newalgorithm_pipeline.output_guard")
    return getattr(module, attribute_name)(*args, **kwargs)


def _extract_guard_forbidden_topics(reasons: List[Any]) -> List[str]:
    return _output_guard_call("_extract_guard_forbidden_topics", reasons)


def _resolve_guard_retry_category(article_type_key: str, writing_focus_key: str) -> str:
    return _output_guard_call("_resolve_guard_retry_category", article_type_key, writing_focus_key)


def _is_guard_auto_repair_candidate(guard: Dict[str, Any]) -> bool:
    return _output_guard_call("is_guard_auto_repair_candidate", guard)


def _build_guard_retry_prompt(
    base_prompt: str,
    guard: Dict[str, Any],
    *,
    article_type_key: str = "",
    writing_focus_key: str = "",
) -> str:
    return _output_guard_call(
        "build_guard_retry_prompt",
        base_prompt,
        guard,
        article_type_key=article_type_key,
        writing_focus_key=writing_focus_key,
    )


def _is_transient_exception(exc: Exception) -> bool:
    text = str(exc or "").upper()
    if text.startswith("TRN_"):
        return True
    transient_markers = (
        "RATE LIMIT",
        "RATE_LIMIT",
        "TIMEOUT",
        "TIMED OUT",
        "429",
        "503",
        "UPSTREAM",
        "NETWORK RESET",
        "CONNECTION RESET",
    )
    return any(marker in text for marker in transient_markers)


def _classify_generation_exception(exc: Exception) -> Dict[str, Any]:
    message = str(exc or "")
    normalized = message.strip().upper()
    reason_code = "SYS_GENERATION_FAILURE"
    error_class = "system"
    retryable = False
    if normalized.startswith(("INP_", "POL_", "SYS_", "TRN_")):
        reason_code = normalized.split(":", 1)[0]
        prefix = reason_code.split("_", 1)[0]
        error_class = {
            "INP": "user_input",
            "POL": "policy",
            "SYS": "system",
            "TRN": "transient",
        }.get(prefix, "system")
        retryable = error_class == "transient"
    elif _is_transient_exception(exc):
        if "429" in normalized or "RATE_LIMIT" in normalized or "RATE LIMIT" in normalized:
            reason_code = "TRN_RATE_LIMIT"
        elif "TIMEOUT" in normalized or "TIMED OUT" in normalized:
            reason_code = "TRN_TIMEOUT"
        elif "NETWORK RESET" in normalized or "CONNECTION RESET" in normalized:
            reason_code = "TRN_NETWORK_RESET"
        elif "503" in normalized or "UPSTREAM" in normalized:
            reason_code = "TRN_UPSTREAM_5XX"
        else:
            reason_code = "TRN_RETRYABLE_FAILURE"
        error_class = "transient"
        retryable = True
    return {
        "error_class": error_class,
        "reason_code": reason_code,
        "retryable": retryable,
        "message": message,
    }
