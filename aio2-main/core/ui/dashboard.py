# -*- coding: utf-8 -*-
"""分析履歴ダッシュボード"""
from typing import Any, Dict, List

from nicegui import ui

from core.storage.database import get_history, compare_runs


@ui.refreshable
def dashboard_panel() -> None:
    """履歴と比較の簡易ダッシュボード"""
    history = get_history(limit=20)

    ui.label("分析履歴").classes("card-title")
    if not history:
        ui.label("履歴がありません。分析を実行してください。").classes("card-sub")
        return

    columns = [
        {"name": "id", "label": "ID", "field": "id"},
        {"name": "analyzed_at", "label": "日時", "field": "analyzed_at"},
        {"name": "url", "label": "URL", "field": "url"},
        {"name": "is_ec", "label": "EC", "field": "is_ec"},
        {"name": "seo_score", "label": "SEO", "field": "seo_score"},
        {"name": "aio_score", "label": "AIO", "field": "aio_score"},
        {"name": "legal_score", "label": "法務", "field": "legal_score"},
        {"name": "total_issues", "label": "課題数", "field": "total_issues"},
    ]
    ui.table(columns=columns, rows=history, row_key="id").classes("w-full text-xs")

    ui.separator()
    ui.label("比較").classes("card-title")
    with ui.row().classes("items-center gap-2"):
        run_id_1 = ui.input("比較元ID", placeholder="例: 1").classes("w-32")
        run_id_2 = ui.input("比較先ID", placeholder="例: 2").classes("w-32")
        result_label = ui.label("").classes("card-sub")

        def _compare() -> None:
            try:
                id1 = int(run_id_1.value or 0)
                id2 = int(run_id_2.value or 0)
                result = compare_runs(id1, id2)
                if result.get("error"):
                    result_label.text = result["error"]
                    return
                result_label.text = (
                    f"SEO: {result['seo_diff']:+d}, "
                    f"AIO: {result['aio_diff']:+d}, "
                    f"法務: {result['legal_diff']:+d}, "
                    f"課題数: {result['issues_diff']:+d}"
                )
            except Exception as exc:
                result_label.text = f"比較エラー: {exc}"

        ui.button("比較する", on_click=_compare).classes("secondary-btn")

    with ui.row().classes("justify-end w-full"):
        ui.button("履歴を更新", on_click=dashboard_panel.refresh).classes("secondary-btn")
