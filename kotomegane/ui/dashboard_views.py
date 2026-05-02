from __future__ import annotations

from typing import Any, Callable

from nicegui import ui

from analysis_lib import build_query_rollup_rows
from config import AppConfig
from ui import detail_views, result_cards
from ui import dashboard_refreshers
from ui.dashboard_view_models import (
    build_dashboard_refresh_payload,
    build_result_table_rows as _build_result_table_rows,
    filter_rows_for_active_scope,
    filter_rows_for_tracking_series,
    resolve_current_result_run_id as _resolve_current_result_run_id,
)
from ui.result_story_builders import (
    build_current_result_story,
    build_intent_map_rows,
    build_page_gap_rows,
    build_portfolio_story,
    localize_analysis_mode,
)


def localize_confidence_label(confidence: str) -> str:
    mapping = {"high": "高め", "medium": "中くらい", "low": "低め"}
    return mapping.get(str(confidence or "").lower(), "低め")


def localize_cache_retention_label(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == "24h":
        return "24時間"
    if normalized == "in_memory":
        return "メモリ内"
    if normalized == "implicit":
        return "provider既定"
    if normalized == "automatic_5m":
        return "自動5分"
    return str(value or "-")


def refresh_latest_result_cards(
    recent_rows: list[dict[str, Any]],
    raw_rows: list[dict[str, Any]],
    config: AppConfig,
    latest_result_container: ui.column,
    previous_delta_summary: dict[str, Any],
    source_loader: Callable[[str], list[dict[str, Any]]] | None = None,
) -> None:
    result_cards.render_latest_result_cards(
        recent_rows,
        raw_rows,
        config,
        latest_result_container,
        previous_delta_summary,
        source_loader,
    )


def refresh_hero_observation_snapshot(
    recent_rows: list[dict[str, Any]],
    raw_rows: list[dict[str, Any]],
    config: AppConfig,
    container: ui.column,
    source_loader: Callable[[str], list[dict[str, Any]]] | None = None,
) -> None:
    result_cards.render_hero_observation_snapshot(
        recent_rows,
        raw_rows,
        config,
        container,
        source_loader,
    )


def resolve_current_result_run_id(
    rows: list[dict[str, Any]],
    config: AppConfig,
    *,
    preferred_run_id: str = "",
) -> str:
    return _resolve_current_result_run_id(rows, config, preferred_run_id=preferred_run_id)


def refresh_dashboard(
    db: Any,
    config: AppConfig,
    show_primary_results: bool,
    current_result_run_id: str,
    result_stage_container: ui.column,
    metric_refs: dict[str, tuple[ui.label, ui.label]],
    decision_refs: dict[str, dict[str, Any]],
    rows_table: ui.table,
    run_table: ui.table,
    question_heatmap_plot: Any,
    query_drilldown_plot: Any,
    intent_trend_plot: Any,
    page_gap_trend_plot: Any,
    query_select: ui.select,
    detail_select: ui.select,
    detail_container: ui.column,
    latest_result_container: ui.column,
    summary_refs: dict[str, Any],
    source_container: ui.column,
    dashboard_status: ui.label,
    source_loader: Callable[[str], list[dict[str, Any]]] | None = None,
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if payload is None:
        payload = build_dashboard_refresh_payload(db, config, source_loader, current_run_id=current_result_run_id)
    show_current_result = bool(payload["current_query_rollup_rows"]) and show_primary_results
    dashboard_refreshers.update_summary_refs(
        metric_refs,
        summary_refs,
        payload["current_result_story"],
        payload["portfolio_story"],
        payload["metrics"],
        payload["tracked_query_rollup_rows"],
        payload["tracked_delta_summary"],
        show_current_result=show_current_result,
    )
    dashboard_refreshers.update_decision_refs(
        decision_refs,
        payload["intent_rows"],
        payload["page_gap_rows"],
        int(payload["metrics"].get("trial_count") or 0),
        payload["budget_guardrail"],
        config,
    )

    rows_table.rows = _build_result_table_rows(payload["query_rollup_rows"], config)
    rows_table.update()

    run_table.rows = payload["run_table_rows"]
    run_table.update()

    dashboard_refreshers.update_tracking_widgets(
        summary_refs,
        payload["tracked_recent_rows"],
        payload["heatmap_rows"],
        payload["heatmap_raw_rows"],
        payload["drilldown_rows"],
        query_select,
        payload["drilldown_query_rows"],
        question_heatmap_plot,
        query_drilldown_plot,
        intent_trend_plot,
        page_gap_trend_plot,
        config,
        source_loader,
    )

    dashboard_status.text = (
        f"総評 {payload['portfolio_story']['overall_label']} | "
        f"自社が見えた試行 {payload['portfolio_story']['visible_trials']}/{payload['portfolio_story']['total_trials']}回 | "
        f"弱い質問タイプ {payload['weakest_intent_label']} | "
        f"不足情報 {payload['top_gap_label']}"
    )

    result_stage_container.set_visibility(True)
    latest_result_container.set_visibility(True)
    summary_refs["container"].set_visibility(True)
    if show_current_result:
        refresh_latest_result_cards(
            payload["current_query_rollup_rows"],
            payload["current_rows"],
            config,
            latest_result_container,
            payload["previous_delta_summary"],
            source_loader,
        )
    else:
        result_cards.render_waiting_latest_result_state(
            latest_result_container,
            has_saved_results=bool(payload["query_rollup_rows"]),
        )
    detail_rollup_rows = payload["current_query_rollup_rows"] if show_current_result else payload["query_rollup_rows"]
    detail_raw_rows = payload["current_rows"] if show_current_result else payload["recent_rows"]
    detail_views.refresh_result_detail_views(
        detail_rollup_rows,
        detail_raw_rows,
        detail_select,
        detail_container,
        config,
        db.list_sources,
        show_current_result=show_current_result,
    )

    result_cards.render_current_evidence_section(
        payload["current_query_rollup_rows"],
        payload["current_rows"],
        config,
        source_container,
        source_loader,
        show_current_result=show_current_result,
    )
    return payload
