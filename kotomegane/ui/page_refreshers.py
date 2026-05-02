from __future__ import annotations

import json
from typing import Any, Callable

from config import AppConfig
from storage import Storage
from ui import admin_views, dashboard_views


def refresh_question_set_admin_views(
    db: Storage,
    question_set_select: Any,
    question_set_table: Any,
    schedule_question_set_select: Any,
    selected_question_set_id: str = "",
    selected_schedule_question_set_id: str | None = None,
) -> None:
    admin_views.refresh_question_set_views(db, question_set_select, question_set_table, schedule_question_set_select)
    if selected_question_set_id and question_set_select is not None:
        question_set_select.value = selected_question_set_id
        question_set_select.update()
    if selected_schedule_question_set_id is not None and schedule_question_set_select is not None:
        schedule_question_set_select.value = selected_schedule_question_set_id
        schedule_question_set_select.update()


def sync_question_set_name_from_selection(
    db: Storage,
    question_set_select: Any,
    question_set_name_input: Any,
    schedule_question_set_select: Any,
) -> None:
    selected = db.get_question_set(str(question_set_select.value or "")) if question_set_select and question_set_select.value else None
    if not selected:
        return
    question_set_name_input.value = str(selected.get("name") or "")
    question_set_name_input.update()
    if schedule_question_set_select is not None:
        schedule_question_set_select.value = str(selected.get("question_set_id") or "")
        schedule_question_set_select.update()


def refresh_schedule_admin_views(
    db: Storage,
    scheduler_service: Any,
    schedule_table: Any,
    scheduler_status_label: Any,
    schedule_manage_select: Any,
    compare_target_select: Any,
    compare_mode_select: Any,
    selected_schedule_id: str = "",
) -> None:
    admin_views.refresh_schedule_views(
        db,
        scheduler_service,
        schedule_table,
        scheduler_status_label,
        schedule_manage_select,
        compare_target_select,
        compare_mode_select,
    )
    if selected_schedule_id and schedule_manage_select is not None:
        schedule_manage_select.value = selected_schedule_id
        schedule_manage_select.update()


def refresh_batch_job_admin_views(
    db: Storage,
    batch_job_select: Any,
    batch_job_table: Any,
    batch_status_label: Any,
    batch_summary_label: Any,
    selected_batch_job_id: str = "",
) -> None:
    admin_views.refresh_batch_job_views(
        db,
        batch_job_select,
        batch_job_table,
        batch_status_label,
        batch_summary_label,
    )
    if selected_batch_job_id and batch_job_select is not None:
        batch_job_select.value = selected_batch_job_id
        batch_job_select.update()


def update_batch_status_panel(
    batch_status_label: Any,
    batch_summary_label: Any,
    status_text: str,
    summary_text: str,
) -> None:
    batch_status_label.text = status_text
    batch_summary_label.text = summary_text
    batch_status_label.update()
    batch_summary_label.update()


def refresh_dashboard_surface(
    db: Storage,
    config: AppConfig,
    show_primary_results: bool,
    current_result_run_id: str,
    result_stage_container: Any,
    metric_refs: dict[str, Any],
    decision_refs: dict[str, Any],
    rows_table: Any,
    run_table: Any,
    question_heatmap_plot: Any,
    query_drilldown_plot: Any,
    intent_trend_plot: Any,
    page_gap_trend_plot: Any,
    query_select: Any,
    detail_select: Any,
    detail_container: Any,
    latest_result_container: Any,
    summary_refs: dict[str, Any],
    source_container: Any,
    dashboard_status: Any,
    source_loader: Callable[[str], list[dict[str, Any]]],
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return dashboard_views.refresh_dashboard(
        db,
        config,
        show_primary_results,
        current_result_run_id,
        result_stage_container,
        metric_refs,
        decision_refs,
        rows_table,
        run_table,
        question_heatmap_plot,
        query_drilldown_plot,
        intent_trend_plot,
        page_gap_trend_plot,
        query_select,
        detail_select,
        detail_container,
        latest_result_container,
        summary_refs,
        source_container,
        dashboard_status,
        source_loader,
        payload=payload,
    )


def refresh_cluster_and_outcome_sections(
    db: Storage,
    config: AppConfig,
    cluster_kind_select: Any,
    cluster_target_select: Any,
    saved_cluster_brief_select: Any,
    cluster_brief_table: Any,
    outcome_scope_kind_select: Any,
    outcome_scope_target_select: Any,
    outcome_run_a_select: Any,
    outcome_run_b_select: Any,
) -> None:
    scoped_rows = dashboard_views.filter_rows_for_active_scope(db.list_recent_results(limit=2000), config)
    if (
        cluster_kind_select is not None
        and cluster_target_select is not None
        and saved_cluster_brief_select is not None
        and cluster_brief_table is not None
    ):
        admin_views.refresh_cluster_brief_views(
            db,
            scoped_rows,
            config,
            cluster_kind_select,
            cluster_target_select,
            saved_cluster_brief_select,
            cluster_brief_table,
        )
    if (
        outcome_scope_kind_select is not None
        and outcome_scope_target_select is not None
        and outcome_run_a_select is not None
        and outcome_run_b_select is not None
    ):
        admin_views.refresh_outcome_compare_views(
            db,
            outcome_scope_kind_select,
            outcome_scope_target_select,
            outcome_run_a_select,
            outcome_run_b_select,
        )


def refresh_cluster_brief_admin_views(
    db: Storage,
    scoped_rows: list[dict[str, Any]],
    config: AppConfig,
    cluster_kind_select: Any,
    cluster_target_select: Any,
    saved_cluster_brief_select: Any,
    cluster_brief_table: Any,
    selected_brief_id: str = "",
) -> None:
    admin_views.refresh_cluster_brief_views(
        db,
        scoped_rows,
        config,
        cluster_kind_select,
        cluster_target_select,
        saved_cluster_brief_select,
        cluster_brief_table,
    )
    if selected_brief_id and saved_cluster_brief_select is not None:
        saved_cluster_brief_select.value = selected_brief_id
        saved_cluster_brief_select.update()


def _build_saved_cluster_brief_payload(
    db: Storage,
    brief_id: str,
) -> dict[str, Any] | None:
    row = db.get_cluster_brief(brief_id)
    if not row:
        return None
    try:
        brief_payload = json.loads(str(row.get("brief_json") or "{}"))
    except Exception:
        brief_payload = {}
    if not isinstance(brief_payload, dict):
        return None
    brief_payload.setdefault("generated_title", str(row.get("generated_title") or ""))
    brief_payload.setdefault("cluster_kind", str(row.get("cluster_kind") or ""))
    brief_payload.setdefault("cluster_kind_label", admin_views.localize_cluster_kind(str(row.get("cluster_kind") or "")))
    return brief_payload


def render_active_cluster_and_outcome_panels(
    db: Storage,
    config: AppConfig,
    cluster_brief_container: Any,
    saved_cluster_brief_select: Any,
    outcome_compare_container: Any,
    outcome_scope_kind_select: Any,
    outcome_scope_target_select: Any,
    outcome_run_a_select: Any,
    outcome_run_b_select: Any,
) -> None:
    if cluster_brief_container is not None:
        brief_payload = None
        if saved_cluster_brief_select is not None and saved_cluster_brief_select.value:
            brief_payload = _build_saved_cluster_brief_payload(db, str(saved_cluster_brief_select.value))
        admin_views.render_cluster_brief_payload(brief_payload, cluster_brief_container)
    if outcome_compare_container is not None:
        render_outcome_compare_panel(
            db,
            config,
            outcome_compare_container,
            outcome_scope_kind_select,
            outcome_scope_target_select,
            outcome_run_a_select,
            outcome_run_b_select,
        )


def render_cluster_brief_payload_by_id(
    db: Storage,
    brief_id: str,
    cluster_brief_container: Any,
) -> None:
    brief_payload = _build_saved_cluster_brief_payload(db, brief_id)
    admin_views.render_cluster_brief_payload(brief_payload, cluster_brief_container)


def render_outcome_compare_panel(
    db: Storage,
    config: AppConfig,
    outcome_compare_container: Any,
    outcome_scope_kind_select: Any,
    outcome_scope_target_select: Any,
    outcome_run_a_select: Any,
    outcome_run_b_select: Any,
) -> None:
    admin_views.render_outcome_compare(
        db,
        str(outcome_scope_kind_select.value or "schedule") if outcome_scope_kind_select is not None else "schedule",
        str(outcome_scope_target_select.value or "") if outcome_scope_target_select is not None else "",
        str(outcome_run_a_select.value or "") if outcome_run_a_select is not None else "",
        str(outcome_run_b_select.value or "") if outcome_run_b_select is not None else "",
        outcome_compare_container,
        config,
    )


def refresh_export_panel(
    export_table: Any,
    export_status_label: Any,
    export_rows: list[dict[str, str]],
    report_preview_label: Any,
    report_preview: str,
) -> None:
    admin_views.refresh_export_views(
        export_table,
        export_status_label,
        export_rows,
        report_preview_label,
        report_preview,
    )
