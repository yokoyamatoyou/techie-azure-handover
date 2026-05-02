# -*- coding: utf-8 -*-
"""Executive summary section rendering."""

from typing import Any, Dict, List, Callable

from nicegui import ui


def _build_sitemap_scope_text(sitemap_info: Dict[str, Any]) -> str:
    """Build business-facing sitemap scope text."""
    if not sitemap_info:
        return ""

    total_pages = int(sitemap_info.get("total_urls") or 0)
    if total_pages <= 0:
        return ""

    sampled_count = int(sitemap_info.get("sampled_count") or 0)
    freq = sitemap_info.get("update_frequency") or "不明"

    scope_text = (
        f"サイト規模: 全{total_pages:,}ページ中、メタデータ解析{sampled_count:,}件"
        f"（更新頻度: {freq}）"
    )
    if sitemap_info.get("is_large_site"):
        scope_text += " - 大規模サイトのため分析はサンプル4ページです"
    return scope_text


def _build_sitemap_note_text(sitemap_info: Dict[str, Any]) -> str:
    """Build non-technical sitemap note text."""
    if not sitemap_info:
        return ""
    error_text = str(sitemap_info.get("error") or "")
    if "同一ホストのみ許可" in error_text:
        return "補足: 安全のため、別サーバーにあるサイトマップは対象外にしています。"
    return ""


def render_executive_summary(
    integrated: Dict[str, Any],
    summary: Dict[str, Any],
    decision_actions: List[Dict[str, Any]],
    format_reason_text_ui: Callable[[str], str],
) -> None:
    """Render executive summary for non-technical stakeholders."""

    def _score_status(score: float) -> tuple[str, str]:
        if score >= 80:
            return ("良好", "🟢")
        if score >= 50:
            return ("要改善", "🟡")
        return ("要対応", "🔴")

    ui.label("経営サマリー（非エンジニア向け）").classes("card-title")
    business_goal = integrated.get("business_goal")
    if business_goal and business_goal != "自動判定":
        ui.label(f"目標: {business_goal}").classes("card-hint text-blue-600 font-bold")

    def _gauge_color(score: float) -> str:
        if score >= 80:
            return "green"
        if score >= 50:
            return "amber"
        return "red"

    # メインスコア 3枚（統合・SEO・AIO）— 円形ゲージ付き
    with ui.row().classes("section-grid"):
        for label, key in (
            ("統合スコア", "integrated_score"),
            ("SEOスコア", "seo_score"),
            ("AIOスコア", "aio_score"),
        ):
            value = float(integrated.get(key, 0))
            status_label, status_symbol = _score_status(value)
            with ui.column().classes("metric items-center gap-1"):
                gauge = ui.circular_progress(
                    value=value, min=0, max=100, size="80px",
                    show_value=False, color=_gauge_color(value),
                )
                gauge.props(f'aria-label="{label}: {value:.0f}点 ({status_label})"')
                with gauge:
                    ui.label(f"{value:.0f}").classes("text-base font-bold")
                ui.label(label).classes("metric-label text-center text-xs")
                ui.label(f"{status_symbol} {status_label}").classes("text-xs text-center").props(
                    f'aria-label="ステータス: {status_label}"'
                )

    # GEOスコア（生成AI最適化）— リニアバー付きサブ行
    geo_score = float(integrated.get("geo_score", 0))
    geo_bd = integrated.get("geo_breakdown") or {}
    if geo_score > 0 or geo_bd:
        geo_status_label, geo_status_symbol = _score_status(geo_score)
        with ui.row().classes("items-center gap-3 mt-2 w-full"):
            ui.linear_progress(
                value=geo_score / 100, size="6px", show_value=False,
                color=_gauge_color(geo_score),
            ).classes("w-20").props(f'aria-label="GEOスコア: {geo_score:.0f}点 ({geo_status_label})"')
            ui.label(
                f"生成AI最適化（GEO）: {geo_score:.0f}/100 {geo_status_symbol}{geo_status_label}"
            ).classes("card-sub font-bold")
            if geo_bd:
                ui.label(
                    f"TL;DR {geo_bd.get('tldr', 0):.1f}/5"
                    f" | 統計密度 {geo_bd.get('stats_density', 0):.1f}/10"
                    f" | E-E-A-T {geo_bd.get('eeat', 0):.1f}/10"
                ).classes("card-hint")

    sitemap_scope_text = _build_sitemap_scope_text(integrated.get("sitemap_info") or {})
    if sitemap_scope_text:
        ui.label(sitemap_scope_text).classes("card-hint")
    sitemap_note_text = _build_sitemap_note_text(integrated.get("sitemap_info") or {})
    if sitemap_note_text:
        ui.label(sitemap_note_text).classes("card-hint text-xs text-gray-500")

    # サマリー文（1行）
    summary_text = summary.get("summary_text") or summary.get("summary") or ""
    if not summary_text:
        summary_text = (
            f"統合スコアは{integrated.get('integrated_score', 0):.0f}点。"
            "最優先アクションを先に実行し、主要KPIの改善を狙います。"
        )
    ui.label(summary_text).classes("card-sub")

    # 最優先アクション（1件のみ — 詳細はレポートパネルで確認）
    if decision_actions:
        top = decision_actions[0]
        with ui.card().classes("card p-4 w-full"):
            ui.label(f"最優先: {top['title']}").classes("card-sub font-bold")
            ui.label(format_reason_text_ui(top.get("action", ""))).classes("card-sub whitespace-pre-line")
            ui.label(
                f"担当: {top.get('role', '運用/マーケ')} / 工数: {top.get('effort', '30〜90分')}"
                f" / KPI: {top.get('kpi', '検索流入/品質')}"
            ).classes("card-hint text-xs text-green-600")
        if len(decision_actions) > 1:
            ui.label(
                f"他 {len(decision_actions) - 1} 件の改善アクションは下の「改善レポート」で確認できます。"
            ).classes("card-hint")
