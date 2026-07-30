"""純粋な text / URL / 値整形 helper を集約する sibling module。

`note_writer_app.py` から切り出した pure function のみを置く。
- NiceGUI / AppState / pipeline には依存しない。
- `note_writer_app.py` 側は re-export してテスト (`app_mod._foo`) 互換を保つ。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


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
    source = (hashtags or "").strip()
    if not source:
        return ""
    tags = re.findall(r"#\S+", source)
    cleaned: List[str] = []
    if tags:
        for tag in tags:
            tag_body = tag.lstrip("#")
            tag_body = re.sub(r"[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+", "", tag_body)
            if tag_body:
                cleaned.append(tag_body)
    else:
        for token in re.split(r"\s+", source):
            token = token.strip().lstrip("#")
            if not token:
                continue
            token = re.sub(r"[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+", "", token)
            if token:
                cleaned.append(token)
    if limit and cleaned:
        cleaned = cleaned[:limit]
    return " ".join(cleaned)


def _replace_hashtags_for_preview(full_text: str, hashtags_plain: str) -> str:
    """プレビューだけハッシュタグをプレーン表示に差し替える。"""
    if not full_text:
        return ""
    if not hashtags_plain:
        return full_text
    marker = "\n---\n\n"
    if marker in full_text:
        head, _ = full_text.rsplit(marker, 1)
        return f"{head}{marker}{hashtags_plain}"
    return full_text


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
    source = (text or "").strip()
    if not source:
        return ""
    if len(source) <= target_chars:
        return source
    trimmed = source[:target_chars].rstrip()
    cut = max(trimmed.rfind("。"), trimmed.rfind("！"), trimmed.rfind("？"), trimmed.rfind("\n"))
    if cut >= int(target_chars * 0.55):
        trimmed = trimmed[: cut + 1].rstrip()
    if not trimmed.endswith("..."):
        trimmed += "..."
    return trimmed
