"""Pure display helpers for note writer generation delay notices."""
from __future__ import annotations

from typing import List


SLOW_SOURCE_COUNT_THRESHOLD = 5
SLOW_TOTAL_CHARS_THRESHOLD = 18000


def _build_generation_delay_notice(source_count: int, total_chars: int = 0) -> str:
    reasons: List[str] = []
    if source_count >= SLOW_SOURCE_COUNT_THRESHOLD:
        reasons.append(f"引用ソース{source_count}件")
    if total_chars >= SLOW_TOTAL_CHARS_THRESHOLD:
        reasons.append(f"抽出本文{total_chars}文字")
    if not reasons:
        return ""
    return f"{' / '.join(reasons)}のため、通常より生成に時間がかかる可能性があります。"
