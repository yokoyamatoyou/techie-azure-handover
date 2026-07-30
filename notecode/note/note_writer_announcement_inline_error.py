"""Announcement inline validation text helper for note_writer_app."""
from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, List


_ANNOUNCEMENT_DATE_PATTERN = re.compile(
    r"(20\d{2}[/-年]\s*\d{1,2}[/-月]\s*\d{1,2}日?(?:\s*\d{1,2}:\d{2})?)|"
    r"(\d{1,2}[/-月]\s*\d{1,2}日(?:\s*\d{1,2}:\d{2})?)"
)
_ANNOUNCEMENT_TARGET_HINTS = (
    "対象",
    "利用者",
    "会員",
    "参加者",
    "顧客",
    "ユーザー",
    "お客様",
    "受講者",
    "来場者",
)
_ANNOUNCEMENT_CHANGE_HINTS = (
    "変更",
    "開始",
    "終了",
    "停止",
    "再開",
    "公開",
    "更新",
    "移行",
    "休業",
    "改定",
    "メンテナンス",
    "リリース",
    "延期",
)


def _build_announcement_inline_error(
    *,
    article_type_key: str,
    source_mode_key: str,
    prompt_raw: str,
    source_values: Iterable[Any] | None,
) -> str:
    if str(article_type_key or "").strip() != "announcement":
        return ""
    if str(source_mode_key or "").strip() == "web":
        return "お知らせは資料ベースのみです。日付・対象・変更点が分かる資料を使ってください。"
    combined_text = " ".join(
        part
        for part in [
            str(prompt_raw or "").strip(),
            *[str(item or "").strip() for item in (source_values or []) if str(item or "").strip()],
        ]
        if part
    )
    missing: List[str] = []
    if not _ANNOUNCEMENT_DATE_PATTERN.search(combined_text):
        missing.append("日付")
    if not any(token in combined_text for token in _ANNOUNCEMENT_TARGET_HINTS):
        missing.append("対象")
    if not any(token in combined_text for token in _ANNOUNCEMENT_CHANGE_HINTS):
        missing.append("変更点")
    if not missing:
        return ""
    return f"お知らせは {' / '.join(missing)} を先に入れてください。"
