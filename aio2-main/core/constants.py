# -*- coding: utf-8 -*-
"""Application-wide constants."""

APP_VERSION = "3.0.0"
APP_NAME = "SEO・AIO統合分析ツール"

# Premium blue/green palette for low cognitive load
COLOR_PALETTE = {
    "primary": "#12A594",        # Teal accent
    "secondary": "#0B1420",      # Deep navy
    "accent": "#1E5D6E",         # Blue-green
    "background": "#F8FAFB",     # Soft paper white
    "surface": "#FFFFFF",        # Clean surface
    "text_primary": "#0D1117",   # Near-black text
    "text_secondary": "#6C7A89", # Muted slate
    "success": "#12A594",        # Teal success
    "warning": "#E3A008",        # Warm amber
    "error": "#D64545",          # Deep red
    "info": "#2C7BB6",           # Blue info
    "gold": "#9B7A2F",           # Warm gold
    "divider": "rgba(13, 17, 23, 0.12)",
    # スコアインジケーター用
    "score_high": "#12A594",     # 80-100: teal
    "score_mid": "#E3A008",      # 50-79: amber
    "score_low": "#D64545",      # 0-49: red
}

# フォント設定（NiceGUI向けの可読性重視 + 日本語対応）
FONT_STACK = "'Sora', 'Noto Sans JP', 'Hiragino Sans', 'Meiryo', 'sans-serif'"

# AIOスコアマッピング
AIO_SCORE_MAP_JP_UPPER = {
    "experience": "経験 (Experience)",
    "expertise": "専門性 (Expertise)",
    "authoritativeness": "権威性 (Authoritativeness)",
    "trustworthiness": "信頼性 (Trustworthiness)",
    "structure": "構造化と整理",
    "qa_compatibility": "質問応答適合性",
    "citation_potential": "AIによる引用可能性",
    "multimodal": "マルチモーダル対応",
}

AIO_SCORE_MAP_JP_LOWER = {
    "search_intent": "検索意図マッチング",
    "personalization": "ーソナライズ可能性",
    "uniqueness": "情報の独自性",
    "completeness": "コンテンツの完全性",
    "readability": "読みやすさスコア",
    "mobile_friendly": "モバイル対応性",
    "page_speed": "ページ速度",
    "metadata": "メタデータ最適化",
}

AIO_SCORE_MAP_NEW_ALGO = {
    "pid_density": "命題密度 (PID)",
    "structure": "構造化・文書パース性",
    "entity_salience": "エンティティ重要度",
    "technical": "技術的AIO適合性",
}

AIO_SCORE_MAP_JP = {**AIO_SCORE_MAP_JP_UPPER, **AIO_SCORE_MAP_JP_LOWER, **AIO_SCORE_MAP_NEW_ALGO}

# SEOスコア項目ラベル（日本語）
SEO_SCORE_LABELS = {
    "title_score": "タイトル",
    "meta_description_score": "メタディスクリプション",
    "headings_score": "見出し構造",
    "content_score": "コンテンツ",
    "links_score": "リンク",
    "images_score": "画像",
    "technical_score": "技術要素",
}
