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
        "helper": "主題を見やすく保ちながら、情報量はGPT Image 2が記事内容に合わせて調整します。",
        "ja_style": "シンプル、落ち着いた色、視認性と文脈の両立",
        "ja_composition": "横長、最低15%以上の余白を確保",
        "ja_detail": "記事内容に応じて必要な補助要素を入れるが、主題を見失わせない",
        "ja_density": "情報量はGPT Image 2が記事内容に合わせて控えめ〜中くらいに調整",
        "en_hint": (
            "Pattern: clear subject with model-adaptive context. Let GPT Image 2 choose the amount "
            "of supporting detail needed for the article; avoid clutter and keep at least 15% clean breathing room."
        ),
    },
    "balanced": {
        "label": "バランス",
        "helper": "主題に補助要素を足して、何の記事か伝わりやすくします。",
        "ja_style": "整ったビジュアル、色数は控えめ、主題と補助要素を両立",
        "ja_composition": "横長、主題の周辺に記事内容へ合う補助要素を加える",
        "ja_detail": "GPT Image 2が記事内容に応じて補助要素の量を調整する",
        "ja_density": "情報量はGPT Image 2が記事内容に合わせて調整",
        "en_hint": (
            "Pattern: balanced model-adaptive detail. Let GPT Image 2 choose enough coherent context "
            "to explain the article; keep at least 15% clean breathing room."
        ),
    },
    "rich": {
        "label": "世界観重視",
        "helper": "背景や空気感まで含めて、印象に残るカバーに寄せます。",
        "ja_style": "文脈が伝わるリッチ構図、要素は増やすが雑然とさせない",
        "ja_composition": "横長、前景と背景にレイヤー感を持たせる",
        "ja_detail": "世界観や背景は増やしてよいが、主題の読み取りを最優先する",
        "ja_density": "情報量はGPT Image 2が記事内容に合わせて多めまで調整",
        "en_hint": (
            "Pattern: rich model-adaptive context. Let GPT Image 2 add layered article-specific detail "
            "as useful, while keeping the layout readable, uncluttered, and with at least 15% clean breathing room."
        ),
    },
}

IMAGE_PATTERN_LABEL_TO_KEY = {
    option["label"]: key for key, option in IMAGE_PATTERN_OPTIONS.items()
}


def _normalize_image_pattern_key(pattern_key: str) -> str:
    normalized = str(pattern_key or "").strip().lower()
    if normalized in IMAGE_PATTERN_OPTIONS:
        return normalized
    return DEFAULT_IMAGE_PATTERN_KEY


def _build_image_pattern_suffix(pattern_key: str, *, language: str) -> str:
    option = IMAGE_PATTERN_OPTIONS[_normalize_image_pattern_key(pattern_key)]
    if str(language or "").strip().lower() == "en":
        return option["en_hint"]
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
