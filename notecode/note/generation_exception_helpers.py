"""生成失敗 / output guard retry に関する thin delegate を集約する sibling module。

`note_writer_app.py` から切り出した delegate のみを置く。
- すべて `output_guard_mod` もしくは `current_mainline_ui_result_adapter` の core 関数への 1 行 delegate。
- 実ロジックは core 側で維持し、ここは UI 側からの命名規約 (アンダースコア接頭辞) を保つ目的で残す。
"""

from __future__ import annotations

from typing import Any, Dict, List

from note.current_mainline_ui_result_adapter import (
    classify_generation_exception as _classify_generation_exception_core,
    is_transient_exception as _is_transient_exception_core,
)
from note.newalgorithm_pipeline import output_guard as _output_guard_mod


def _extract_guard_forbidden_topics(reasons: List[Any]) -> List[str]:
    return _output_guard_mod._extract_guard_forbidden_topics(reasons)


def _resolve_guard_retry_category(article_type_key: str, writing_focus_key: str) -> str:
    return _output_guard_mod._resolve_guard_retry_category(article_type_key, writing_focus_key)


def _is_guard_auto_repair_candidate(guard: Dict[str, Any]) -> bool:
    return _output_guard_mod.is_guard_auto_repair_candidate(guard)


def _build_guard_retry_prompt(
    base_prompt: str,
    guard: Dict[str, Any],
    *,
    article_type_key: str = "",
    writing_focus_key: str = "",
) -> str:
    return _output_guard_mod.build_guard_retry_prompt(
        base_prompt,
        guard,
        article_type_key=article_type_key,
        writing_focus_key=writing_focus_key,
    )


def _is_transient_exception(exc: Exception) -> bool:
    return _is_transient_exception_core(exc)


def _classify_generation_exception(exc: Exception) -> Dict[str, Any]:
    return _classify_generation_exception_core(exc)
