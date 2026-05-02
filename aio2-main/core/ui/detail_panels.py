# -*- coding: utf-8 -*-
"""詳細パネル用ユーティリティ（Phase 05強化版）"""

from typing import Dict, List, Optional


def summarize_issues(items: List[Dict], max_items: int = 3) -> List[str]:
    """問題点のサマリーを生成"""
    summaries = []
    for item in items[:max_items]:
        issue = item.get("issue") or item.get("text") or ""
        if issue:
            summaries.append(issue)
    return summaries


def format_issue_rows(items: List[Dict]) -> List[Dict]:
    """UI表示用に問題データを整形"""
    rows = []
    for item in items:
        rows.append({
            "title": item.get("issue") or item.get("text") or "項目",
            "detail": item.get("suggestion") or item.get("subtext") or "",
        })
    return rows


def render_detail_panel(title: str, items: List[Dict]):
    """詳細パネルを描画"""
    from nicegui import ui

    if not items:
        return

    with ui.expansion(title, icon="info").classes("w-full"):
        for row in format_issue_rows(items):
            ui.label(row["title"]).classes("card-sub")
            if row["detail"]:
                ui.label(row["detail"]).classes("card-hint")


# ============================================================
# Phase 05: 深掘り表示用コンポーネント
# ============================================================

SEVERITY_COLORS = {
    "high": "red-600",
    "medium": "orange-500",
    "low": "blue-500",
    "info": "gray-500",
}

SEVERITY_ICONS = {
    "high": "error",
    "medium": "warning",
    "low": "info",
    "info": "help",
}

SEVERITY_LABELS = {
    "high": "重要",
    "medium": "注意",
    "low": "参考",
    "info": "情報",
}


def render_deep_dive_issue(issue: Dict):
    """
    深掘り表示: 個別の問題を詳細表示（Phase 05）
    - 根拠スニペット
    - 位置情報
    - 信頼度
    - 改善提案
    """
    from nicegui import ui

    severity = issue.get("severity", "medium")
    color = SEVERITY_COLORS.get(severity, "gray-500")
    icon = SEVERITY_ICONS.get(severity, "info")
    label = SEVERITY_LABELS.get(severity, "情報")

    with ui.card().classes(f"w-full p-3 border-l-4 border-{color}"):
        # ヘッダー行: 重要度ラベル + テキスト
        with ui.row().classes("items-center gap-2"):
            ui.icon(icon).classes(f"text-{color}")
            ui.label(f"[{label}]").classes(f"text-{color} font-bold text-sm")
            matched = issue.get("matched_text", issue.get("text", ""))[:50]
            ui.label(matched).classes("font-semibold")
            category = issue.get("category", "")
            if category:
                ui.badge(category, color="gray").classes("text-xs")

        # 理由/問題の説明
        reason = issue.get("reason", issue.get("issue", ""))
        if reason:
            ui.label(reason).classes("text-sm text-gray-700 mt-1")

        # 根拠スニペット
        evidence = issue.get("evidence", "")
        if evidence:
            with ui.row().classes("items-start gap-1 mt-2"):
                ui.icon("format_quote", size="sm").classes("text-gray-400")
                ui.label(evidence).classes("text-xs text-gray-500 italic bg-gray-50 p-1 rounded")

        html_snippet = issue.get("html_snippet", "")
        if html_snippet:
            ui.label(html_snippet[:300]).classes("text-xs font-mono text-gray-600 bg-gray-50 p-1 rounded mt-1")

        # 位置情報 + 信頼度
        location = issue.get("location", "")
        confidence = issue.get("confidence", 0)
        if location or confidence:
            with ui.row().classes("items-center gap-4 mt-2 text-xs text-gray-500"):
                if location:
                    ui.label(f"検出位置: {location}")
                if confidence:
                    ui.label(f"信頼度: {int(confidence * 100)}%")

        # 改善提案
        suggestion = issue.get("suggestion", "")
        if suggestion:
            with ui.row().classes("items-start gap-1 mt-2 bg-blue-50 p-2 rounded"):
                ui.icon("lightbulb", size="sm").classes("text-blue-500")
                ui.label(suggestion).classes("text-sm text-blue-700")

        # 消費者庁注釈
        ca_note = issue.get("consumer_agency_note", "")
        if ca_note:
            with ui.row().classes("items-start gap-1 mt-2 bg-red-50 p-2 rounded"):
                ui.icon("gavel", size="sm").classes("text-red-500")
                ui.label(ca_note).classes("text-xs text-red-700")


def render_deep_dive_cluster(cluster: Dict):
    """
    深掘り表示: 統合されたクラスター表示（Phase 05）
    """
    from nicegui import ui

    representative = cluster.get("representative", {})
    member_count = cluster.get("member_count", 1)
    severity = cluster.get("severity", "medium")
    evidence_summary = cluster.get("evidence_summary", "")

    color = SEVERITY_COLORS.get(severity, "gray-500")

    with ui.card().classes(f"w-full p-3 border-l-4 border-{color}"):
        # ヘッダー
        with ui.row().classes("items-center justify-between"):
            with ui.row().classes("items-center gap-2"):
                ui.icon(SEVERITY_ICONS.get(severity, "info")).classes(f"text-{color}")
                matched = representative.get("matched_text", "")[:40]
                ui.label(matched).classes("font-semibold")

            if member_count > 1:
                ui.badge(f"+{member_count - 1}件", color="blue").classes("text-xs")

        # 証拠サマリ
        if evidence_summary:
            ui.label(evidence_summary).classes("text-sm text-gray-600 mt-1")

        # 代表問題の詳細を折りたたみ
        with ui.expansion("詳細を表示", icon="expand_more").classes("w-full mt-2"):
            render_deep_dive_issue(representative)


def render_legal_deep_dive_section(legal_checks: Dict):
    """
    法務チェックの深掘りセクション全体を描画（Phase 05）
    """
    from nicegui import ui
    from core.evidence_pipeline import aggregate_legal_check_results, generate_deep_dive_summary

    # 結果を集約
    aggregated = aggregate_legal_check_results(legal_checks)
    summary = generate_deep_dive_summary(aggregated)

    # ヘッドライン
    ui.label(summary["headline"]).classes("text-lg font-bold mb-2")

    # 統計
    with ui.row().classes("gap-4 mb-4"):
        ui.label(f"検出: {summary['total_issues']}件").classes("text-sm")
        for cat, count in summary["category_breakdown"].items():
            ui.badge(f"{cat}: {count}", color="gray").classes("text-xs")

    # 重要度別タブ
    with ui.tabs().classes("w-full") as tabs:
        high_tab = ui.tab("重要", icon="error")
        medium_tab = ui.tab("注意", icon="warning")
        low_tab = ui.tab("参考", icon="info")

    with ui.tab_panels(tabs, value=high_tab).classes("w-full"):
        with ui.tab_panel(high_tab):
            if summary["high_priority"]:
                for cluster in summary["high_priority"]:
                    render_deep_dive_cluster(cluster)
            else:
                ui.label("重要な問題は検出されませんでした").classes("text-gray-500")

        with ui.tab_panel(medium_tab):
            if summary["medium_priority"]:
                for cluster in summary["medium_priority"]:
                    render_deep_dive_cluster(cluster)
            else:
                ui.label("注意が必要な問題は検出されませんでした").classes("text-gray-500")

        with ui.tab_panel(low_tab):
            if summary["low_priority"]:
                for cluster in summary["low_priority"]:
                    render_deep_dive_cluster(cluster)
            else:
                ui.label("参考情報はありません").classes("text-gray-500")


def render_tokushoho_detection_info(commercial_result: Dict):
    """
    特商法ページ検出情報の表示（Phase 05）
    """
    from nicegui import ui

    tokushoho_page = commercial_result.get("tokushoho_page", {})

    if tokushoho_page.get("found"):
        with ui.card().classes("w-full p-3 bg-green-50 border border-green-200"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("check_circle").classes("text-green-600")
                ui.label("特定商取引法ページを検出").classes("font-semibold text-green-700")

            ui.label(f"リンク: {tokushoho_page.get('link_text', '')}").classes("text-sm mt-1")
            ui.label(f"位置: {tokushoho_page.get('location', '')}").classes("text-sm text-gray-600")

            url = tokushoho_page.get("url", "")
            if url:
                ui.link("ページを確認", url, new_tab=True).classes("text-blue-600 text-sm mt-2")
    else:
        with ui.card().classes("w-full p-3 bg-yellow-50 border border-yellow-200"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("warning").classes("text-yellow-600")
                ui.label("特定商取引法ページが見つかりません").classes("font-semibold text-yellow-700")

            ui.label("ECサイトの場合は専用ページを作成し、フッターからリンクしてください").classes("text-sm text-gray-600 mt-1")
