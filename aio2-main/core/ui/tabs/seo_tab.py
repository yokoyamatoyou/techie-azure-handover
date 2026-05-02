# -*- coding: utf-8 -*-
"""SEO tab rendering logic."""

from typing import Any, Dict, Callable

from nicegui import ui


def render_seo_tab(
    seo_results: Dict[str, Any],
    trim_text: Callable[[str, int], str],
    format_reason_text_ui: Callable[[str], str],
) -> None:
    """Render the SEO tab."""
    if not seo_results:
        ui.label("SEO分析データがありません。分析を実行してください。").classes("card-hint text-gray-400")
        return

    basics = seo_results.get("basics", {})
    structure = seo_results.get("structure", {})
    seo_actions = seo_results.get("immediate_actions", [])
    if not basics and not structure and not seo_actions:
        ui.label("SEO分析データがありません。分析を実行してください。").classes("card-hint text-gray-400")
        return

    ui.label("基本SEO情報").classes("card-title")
    ui.label(f"タイトル: {basics.get('title', 'N/A')}").classes("card-sub")
    ui.label(f"説明文: {basics.get('meta_description', 'N/A')}").classes("card-sub")

    ui.label("ページ構造").classes("card-title")
    ui.label(f"内部リンク数: {structure.get('internal_links_count', 0)}").classes("card-sub")
    ui.label(f"外部リンク数: {structure.get('external_links_count', 0)}").classes("card-sub")
    ui.label(f"画像数: {structure.get('images_count', 0)}").classes("card-sub")

    if seo_actions:
        ui.label("SEO 即時改善アクション（プラットフォーム別）").classes("card-title")

        for action in seo_actions[:4]:
            ui.label(f"- {action.get('action', 'N/A')}").classes("card-sub")

            method = action.get("method", "")
            if method:
                ui.label(format_reason_text_ui(trim_text(method, 240))).classes("card-hint whitespace-pre-line")
