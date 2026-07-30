"""画像プロンプト生成関連の pure helper / 定数を集約する sibling module。

`note_writer_app.py` から切り出した純粋ロジックのみを置く。
- NiceGUI / AppState / pipeline / PIL には依存しない (プロンプト文字列生成のみ)。
- PIL を使う画像加工 (`apply_filter_to_image` 等) は `image_editor` 側に残し、ここには移さない。
"""

from __future__ import annotations

import re
from typing import Dict, List


DEFAULT_IMAGE_PATTERN_KEY = "simple"

IMAGE_PATTERN_OPTIONS: Dict[str, Dict[str, str]] = {
    "simple": {
        "label": "シンプル",
        "helper": "主題を見やすく保つ、既定の方向性です。",
        "prompt_direction": "Clear cover with one recognizable subject, restrained color, and article-specific context only when useful.",
        "ja_style": "シンプル、落ち着いた色、主題が見える表現",
        "ja_composition": "横長、最低15%以上の余白を確保",
        "ja_detail": "記事内容に合う補助要素だけを加え、主題を上書きしない",
        "ja_density": "情報量は控えめ",
        "en_hint": (
            "Touch direction: simple, clear cover with one recognizable subject, restrained color, "
            "article-specific context only when useful, and at least 15% clean breathing room."
        ),
    },
    "blog_cover": {
        "label": "ブログ見出し画像風",
        "helper": "記事カバーらしい完成感に寄せます。",
        "prompt_direction": "Japanese blog eyecatch cover with a clean focal subject, negative space, and a finished article-cover feel.",
        "ja_style": "ブログ見出し画像風、整った見せ方、完成感のある表現",
        "ja_composition": "横長、主題と余白のバランスを保つ",
        "ja_detail": "記事内容に合う文脈を添えるが、広告やポスター風にしない",
        "ja_density": "情報量は中くらい",
        "en_hint": (
            "Touch direction: Japanese blog eyecatch cover with a clean focal subject, readable negative space, "
            "and a finished article-cover feel, not an ad or poster."
        ),
    },
    "flat_illustration": {
        "label": "フラットイラスト",
        "helper": "シンプルな図形と色面で、概念を分かりやすく見せます。",
        "prompt_direction": "Modern flat illustration with simple shapes, clean contrast, limited accents, and one clear article subject.",
        "ja_style": "フラットイラスト、簡潔な形、明快なコントラスト",
        "ja_composition": "横長、主題を中心に小さな文脈要素を配置",
        "ja_detail": "記事にない図表、数値、ラベルを作らない",
        "ja_density": "情報量は控えめから中くらい",
        "en_hint": (
            "Touch direction: modern flat illustration with simple shapes, clean contrast, limited accents, "
            "one clear article subject, and no invented charts or labels."
        ),
    },
    "warm_handdrawn": {
        "label": "温かい手描き風",
        "helper": "やわらかい線で、親しみやすさを出します。",
        "prompt_direction": "Warm hand-drawn illustration with soft lines, calm color, and a friendly professional mood grounded in the article topic.",
        "ja_style": "温かい手描き風、やわらかい線、落ち着いた色",
        "ja_composition": "横長、人の気配や身近な物を必要な範囲で使う",
        "ja_detail": "かわいすぎる漫画調や吹き出し、手書き文字を入れない",
        "ja_density": "情報量は控えめ",
        "en_hint": (
            "Touch direction: warm hand-drawn illustration with soft lines, calm color, "
            "and a friendly professional mood grounded in the article topic."
        ),
    },
}

_IMAGE_PATTERN_KEY_ALIASES: Dict[str, str] = {
    "balanced": "blog_cover",
    "rich": "blog_cover",
}

IMAGE_PATTERN_LABEL_TO_KEY = {
    option["label"]: key for key, option in IMAGE_PATTERN_OPTIONS.items()
}


def _normalize_image_pattern_key(pattern_key: str) -> str:
    normalized = str(pattern_key or "").strip().lower()
    if normalized in IMAGE_PATTERN_OPTIONS:
        return normalized
    if normalized in _IMAGE_PATTERN_KEY_ALIASES:
        return _IMAGE_PATTERN_KEY_ALIASES[normalized]
    return DEFAULT_IMAGE_PATTERN_KEY


def _build_image_pattern_suffix(pattern_key: str, *, language: str) -> str:
    option = IMAGE_PATTERN_OPTIONS[_normalize_image_pattern_key(pattern_key)]
    if str(language or "").strip().lower() == "en":
        return (
            f"{option['en_hint']} Touch is an expression direction only; "
            "do not override the article content or source claims."
        )
    return "\n".join(
        [
            f"スタイル補足: {option['ja_style']}",
            f"構図補足: {option['ja_composition']}",
            f"描写密度: {option['ja_density']}",
            f"補助要素の扱い: {option['ja_detail']}",
        ]
    )


def _apply_image_pattern_to_prompt(prompt_text: str, pattern_key: str, *, language: str) -> str:
    base_text = str(prompt_text or "").strip()
    if not base_text:
        return base_text
    suffix = _build_image_pattern_suffix(pattern_key, language=language)
    if suffix and suffix not in base_text:
        return f"{base_text}\n\n{suffix}".strip()
    return base_text


def _build_image_prompt(title: str, lead: str, pattern_key: str = DEFAULT_IMAGE_PATTERN_KEY) -> str:
    pattern = IMAGE_PATTERN_OPTIONS[_normalize_image_pattern_key(pattern_key)]
    title_text = (title or "").strip()
    lead_text = (lead or "").strip()
    lead_text = lead_text[:200] if lead_text else ""
    base = "記事内容に合う横長のカバー画像を作るための指示です。"
    details = [
        f"テーマ: {title_text}" if title_text else "テーマ: 指定なし",
        f"要約: {lead_text}" if lead_text else "要約: 指定なし",
        f"スタイル: {pattern['ja_style']}",
        f"構図: {pattern['ja_composition']}",
        f"描写密度: {pattern['ja_density']}",
        f"補助要素の扱い: {pattern['ja_detail']}",
        "禁止: 文字・ロゴ・透かし・有名キャラクターを入れない",
    ]
    return "\n".join([base, *details]).strip()


def _split_image_prompts(text: str) -> List[str]:
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"\n-{3,}\n", text) if p.strip()]
    return parts if parts else [text.strip()]
