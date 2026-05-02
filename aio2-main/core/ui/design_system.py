# -*- coding: utf-8 -*-
"""UI Design System for Site Health Tab."""

from typing import Dict


# アイコン定義（NiceGUI Material Icons用）
LEGAL_ICONS = {
    "compliant": "check_circle",
    "warning": "warning",
    "error": "cancel",
    "info": "info",
    "partial": "help",
}

# フォールバックアイコン（テキスト表示用）
LEGAL_ICONS_FALLBACK = {
    "compliant": "適合",
    "warning": "注意",
    "error": "要対応",
    "info": "情報",
    "partial": "一部",
}

# 色定義（TailwindCSS準拠）
SITE_HEALTH_COLORS = {
    "success": "green-600",
    "warning": "orange-500",
    "danger": "red-600",
    "info": "blue-500",
}

# タイポグラフィ定義
SITE_HEALTH_TYPOGRAPHY = {
    "section_title": "text-xl font-bold text-gray-800",
    "card_title": "text-lg font-semibold text-gray-700",
    "body": "text-base text-gray-600",
    "hint": "text-sm text-gray-500",
}

# スペーシング定義
SITE_HEALTH_SPACING = {
    "section_gap": "mb-6",
    "card_padding": "p-4",
    "item_gap": "gap-2",
}

# 既存UI向けのHEXカラー定義
COLORS: Dict[str, str] = {
    "primary": "#2563EB",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "info": "#3B82F6",
}

# 既存UI向けのステータスアイコン定義
STATUS_ICONS = {
    "success": "check_circle",
    "warning": "warning",
    "danger": "error",
    "info": "info",
}


def get_icon(status: str, use_fallback: bool = True) -> str:
    """ステータスに応じたアイコンを取得"""
    if use_fallback:
        return LEGAL_ICONS_FALLBACK.get(status, "情報")
    return LEGAL_ICONS.get(status, "help")


def get_color_class(status: str) -> str:
    """ステータスに応じた色クラスを取得"""
    return SITE_HEALTH_COLORS.get(status, "gray-500")


def resolve_color(key: str, fallback: str = "#2563EB") -> str:
    """カラーキーからHEXカラーを取得"""
    if not key:
        return fallback
    return COLORS.get(key, key)


def resolve_icon(key: str, fallback: str = "info") -> str:
    """ステータスキーからアイコン名を取得"""
    if not key:
        return fallback
    return STATUS_ICONS.get(key, fallback)
