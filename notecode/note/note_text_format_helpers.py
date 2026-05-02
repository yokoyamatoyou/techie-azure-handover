"""純粋な text / URL / 値整形 helper を集約する sibling module。

`note_writer_app.py` から切り出した pure function のみを置く。
- NiceGUI / AppState / pipeline には依存しない。
- `note_writer_app.py` 側は re-export してテスト (`app_mod._foo`) 互換を保つ。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from note.current_mainline_ui_result_adapter import (
    build_short_sns_text as _build_short_sns_text_core,
    hashtags_to_plain as _hashtags_to_plain_core,
    replace_hashtags_for_preview as _replace_hashtags_for_preview_core,
)


def _safe_url(val: str) -> str:
    """Remove characters that could break HTML attribute context."""
    return val.replace('"', "").replace("'", "").replace("<", "").replace(">", "").strip()


def _sanitize_href_allow_file(href: str) -> str:
    if href.startswith(("/", "mailto:", "http:", "https:", "#", "tel:", "file:")):
        return href
    return "#"


def _to_note_format(text: str) -> str:
    """記事エディタに貼り付けた際に見栄えが良くなるよう、Markdownを変換する"""
    if not text:
        return ""
    # note の記事エディタは Markdown 記法 (## 見出しや **bold**) を一応サポートするため、
    # 独自記号 (■ / 【】) への変換はせず、Markdown のまま出力する。
    cleaned = re.sub(r"\n{3,}", "\n\n", text)
    return cleaned.strip()


def _hashtags_to_plain(hashtags: str, limit: int = 5) -> str:
    """ハッシュタグをプレーン表示用に整形 (# を外して並べる)。"""
    return _hashtags_to_plain_core(hashtags, limit=limit)


def _replace_hashtags_for_preview(full_text: str, hashtags_plain: str) -> str:
    """プレビューだけハッシュタグをプレーン表示に差し替える。"""
    return _replace_hashtags_for_preview_core(full_text, hashtags_plain)


def _to_plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _to_plain_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _safe_round_float(value: Any, digits: int = 4, default: float = 0.0) -> float:
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return default


def _build_short_sns_text(text: str, target_chars: int = 320) -> str:
    """長文 SNS 文面から短縮版を作る。"""
    return _build_short_sns_text_core(text, target_chars=target_chars)
