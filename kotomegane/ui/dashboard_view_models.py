from __future__ import annotations

import time
from typing import Any, Callable

from analysis_lib import (
    build_answer_structure_fields,
    build_budget_guardrail,
    build_overview_metrics,
    build_previous_delta_summary,
    build_query_rollup_rows,
    classify_keyword_intent,
    format_timestamp,
    infer_page_gap,
    normalize_query_text,
    normalize_text,
    parse_json_object,
    resolve_analysis_mode,
)
from config import ANALYSIS_MODE_MARKET, AppConfig
from ui import detail_views
from ui.evidence_presenters import normalize_host
from ui.result_story_builders import (
    build_current_result_story,
    build_intent_map_rows,
    build_page_gap_rows,
    build_portfolio_story,
    build_result_digest,
    build_visibility_state_label,
)

CURRENT_RESULT_RESTORE_WINDOW_SECONDS = 30 * 60


def resolve_row_analysis_mode(row: dict[str, Any], payload: dict[str, Any] | None = None) -> str:
    effective_payload = payload or parse_json_object(row.get("output_json"))
    return resolve_analysis_mode(effective_payload)


def _normalize_scope_values(values: list[Any] | None) -> list[str]:
    normalized = {normalize_text(str(value or "")) for value in (values or []) if normalize_text(str(value or ""))}
    return sorted(normalized)


def _row_run_config(row: dict[str, Any]) -> dict[str, Any]:
    payload = parse_json_object(row.get("run_config_json"))
    return payload if isinstance(payload, dict) else {}


def _row_analysis_context(row: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    effective_payload = payload or parse_json_object(row.get("output_json"))
    context = effective_payload.get("analysis_context") or {}
    return context if isinstance(context, dict) else {}


def _row_scope_keyword(row: dict[str, Any], payload: dict[str, Any] | None = None) -> str:
    analysis_context = _row_analysis_context(row, payload)
    return normalize_text(
        str(
            analysis_context.get("user_query_raw")
            or row.get("user_query_raw")
            or row.get("keyword_raw")
            or row.get("keyword_norm")
            or ""
        )
    )


def _row_target_host(row: dict[str, Any], payload: dict[str, Any] | None = None) -> str:
    analysis_context = _row_analysis_context(row, payload)
    resolved_target = analysis_context.get("target_domain") or _row_run_config(row).get("target_domain") or ""
    return normalize_host(resolved_target)


def _run_scope_matches_config(row: dict[str, Any], config: AppConfig) -> bool:
    run_config = _row_run_config(row)
    if not run_config:
        return False

    if (normalize_text(str(run_config.get("analysis_mode") or "")) or ANALYSIS_MODE_MARKET) != (
        normalize_text(str(config.analysis_mode or "")) or ANALYSIS_MODE_MARKET
    ):
        return False

    stored_provider = normalize_text(str(run_config.get("provider") or ""))
    if stored_provider and stored_provider != normalize_text(str(config.provider or "")):
        return False

    stored_model = normalize_text(str(run_config.get("model") or row.get("run_model_name") or ""))
    if stored_model and stored_model != normalize_text(str(config.model or "")):
        return False

    if normalize_host(run_config.get("target_domain") or "") != normalize_host(config.target_domain):
        return False

    if _normalize_scope_values(run_config.get("keywords")) != _normalize_scope_values(config.keywords):
        return False

    if _normalize_scope_values(run_config.get("brand_terms")) != _normalize_scope_values(config.brand_terms):
        return False

    if _normalize_scope_values(run_config.get("market_context_terms")) != _normalize_scope_values(config.market_context_terms):
        return False

    if _normalize_scope_values(run_config.get("competitor_terms")) != _normalize_scope_values(config.competitor_terms):
        return False

    return True


def resolve_current_result_run_id(
    rows: list[dict[str, Any]],
    config: AppConfig,
    *,
    preferred_run_id: str = "",
) -> str:
    matching_rows = [row for row in rows if _run_scope_matches_config(row, config)]
    if not matching_rows:
        return ""

    preferred_run_id = str(preferred_run_id or "").strip()
    if preferred_run_id:
        preferred_rows = [row for row in matching_rows if str(row.get("run_id") or "") == preferred_run_id]
        if any(float(row.get("run_finished_at") or 0.0) > 0 for row in preferred_rows):
            return preferred_run_id
        return ""

    latest_row = matching_rows[0]
    finished_at = float(latest_row.get("run_finished_at") or 0.0)
    if finished_at <= 0:
        return ""

    if time.time() - finished_at > CURRENT_RESULT_RESTORE_WINDOW_SECONDS:
        return ""

    return str(latest_row.get("run_id") or "")


def filter_rows_for_active_scope(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    keyword_set = {normalize_text(keyword) for keyword in config.keywords if normalize_text(keyword)}
    target_host = normalize_host(config.target_domain)
    active_mode = normalize_text(config.analysis_mode) or ANALYSIS_MODE_MARKET
    if not keyword_set and not target_host:
        filtered_rows = rows
    else:
        filtered_rows: list[dict[str, Any]] = []
        for row in rows:
            payload = parse_json_object(row.get("output_json"))
            row_keyword = _row_scope_keyword(row, payload)
            if keyword_set and row_keyword not in keyword_set:
                continue

            if target_host:
                row_target_host = _row_target_host(row, payload)
                if not row_target_host:
                    continue
                if not (row_target_host == target_host or row_target_host.endswith(f".{target_host}")):
                    continue

            filtered_rows.append(row)

    return [row for row in filtered_rows if (resolve_row_analysis_mode(row) or ANALYSIS_MODE_MARKET) == active_mode]


def is_tracking_run_mode(run_mode: Any) -> bool:
    return str(run_mode or "").strip().lower() in {"batch", "scheduled"}


def filter_rows_for_tracking_series(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if is_tracking_run_mode(row.get("run_mode"))]


def build_refresh_signature(scoped_rows: list[dict[str, Any]]) -> tuple[Any, ...]:
    latest_row = scoped_rows[0] if scoped_rows else {}
    latest_run_id = str(latest_row.get("run_id") or "")
    latest_result_id = str(latest_row.get("result_id") or "")
    latest_analyzed_at = str(latest_row.get("analyzed_at") or "")
    return (len(scoped_rows), latest_run_id, latest_result_id, latest_analyzed_at)


def localize_run_mode(run_mode: Any) -> str:
    return detail_views.localize_run_mode(run_mode)


def resolve_previous_delta_summary(db: Any, config: AppConfig, filtered_rows: list[dict[str, Any]]) -> dict[str, Any]:
    run_ids: list[str] = []
    for row in filtered_rows:
        run_id = str(row.get("run_id") or "")
        if run_id and run_id not in run_ids:
            run_ids.append(run_id)
        if len(run_ids) >= 2:
            break
    if len(run_ids) < 2:
        return {"available": False, "reason": "前回比はまだありません。"}

    current_run_id, previous_run_id = run_ids[0], run_ids[1]
    query_plans = db.list_query_plans_for_runs([current_run_id, previous_run_id])
    current_plans = [plan for plan in query_plans if str(plan.get("run_id") or "") == current_run_id]
    previous_plans = [plan for plan in query_plans if str(plan.get("run_id") or "") == previous_run_id]
    if not current_plans or not previous_plans:
        return {"available": False, "reason": "前回比に必要な拡張条件がまだ保存されていません。"}

    current_scope_id = next((str(row.get("question_set_id") or "") for row in filtered_rows if str(row.get("run_id") or "") == current_run_id), "")
    previous_scope_id = next((str(row.get("question_set_id") or "") for row in filtered_rows if str(row.get("run_id") or "") == previous_run_id), "")
    if current_scope_id != previous_scope_id:
        return {"available": False, "reason": "比較条件が変わったため前回比なし"}

    previous_by_query = {
        normalize_query_text(plan.get("user_query_raw") or ""): plan
        for plan in previous_plans
        if normalize_query_text(plan.get("user_query_raw") or "")
    }
    matched_current_plan_ids: list[str] = []
    matched_previous_plan_ids: list[str] = []
    for plan in current_plans:
        query_key = normalize_query_text(plan.get("user_query_raw") or "")
        previous_plan = previous_by_query.get(query_key)
        if previous_plan is None:
            return {"available": False, "reason": "比較条件が変わったため前回比なし"}
        if str(plan.get("expansion_signature") or "") != str(previous_plan.get("expansion_signature") or ""):
            return {"available": False, "reason": "比較条件が変わったため前回比なし"}
        matched_current_plan_ids.append(str(plan.get("query_plan_id") or ""))
        matched_previous_plan_ids.append(str(previous_plan.get("query_plan_id") or ""))

    run_rows = db.list_results_for_runs([current_run_id, previous_run_id])
    current_rows = [row for row in run_rows if str(row.get("query_plan_id") or "") in matched_current_plan_ids]
    previous_rows = [row for row in run_rows if str(row.get("query_plan_id") or "") in matched_previous_plan_ids]
    if not current_rows or not previous_rows:
        return {"available": False, "reason": "前回比に必要な結果がまだ揃っていません。"}
    delta = build_previous_delta_summary(current_rows, previous_rows)
    delta.update({"available": True, "current_run_id": current_run_id, "previous_run_id": previous_run_id})
    return delta


def build_result_table_rows(query_rollup_rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    table_rows: list[dict[str, Any]] = []
    for row in query_rollup_rows:
        payload = parse_json_object(row.get("output_json"))
        analysis_context = payload.get("analysis_context") or {}
        intent = classify_keyword_intent(
            str(row.get("keyword_raw") or ""),
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
        )
        page_gap = infer_page_gap(
            str(row.get("keyword_raw") or ""),
            payload,
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
            target_hit=bool(row.get("target_domain_hit")),
            brand_hit=bool(row.get("brand_mention_hit")),
        )
        table_rows.append(
            {
                **row,
                "analyzed_at": format_timestamp(row["analyzed_at"]),
                "run_mode": localize_run_mode(row.get("run_mode")),
                "intent_label": intent["label"],
                "page_gap_label": page_gap["page_type_label"],
                "target_domain_hit": "あり" if row["target_domain_hit"] else "なし",
                "brand_mention_hit": "あり" if row.get("brand_mention_hit") else "なし",
                "visibility_label": build_visibility_state_label(
                    int(row.get("visibility_score") or 0),
                    bool(row.get("target_domain_hit")),
                    bool(row.get("brand_mention_hit")),
                ),
                "result_digest": build_result_digest(row, payload),
                "answer_type_label": build_answer_structure_fields(row, config)["answer_type_label"],
            }
        )
    return table_rows


def build_dashboard_refresh_payload(
    db: Any,
    config: AppConfig,
    source_loader: Callable[[str], list[dict[str, Any]]] | None = None,
    *,
    current_run_id: str = "",
    all_recent_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    loaded_recent_rows = list(all_recent_rows) if all_recent_rows is not None else db.list_recent_results(limit=500)
    recent_rows = filter_rows_for_active_scope(loaded_recent_rows, config)
    resolved_current_run_id = resolve_current_result_run_id(recent_rows, config, preferred_run_id=current_run_id)
    current_rows = (
        [row for row in recent_rows if str(row.get("run_id") or "") == resolved_current_run_id]
        if resolved_current_run_id
        else []
    )
    current_query_rollup_rows = build_query_rollup_rows(current_rows)
    tracked_recent_rows = filter_rows_for_tracking_series(recent_rows)
    query_rollup_rows = build_query_rollup_rows(recent_rows)
    tracked_query_rollup_rows = build_query_rollup_rows(tracked_recent_rows)
    metrics = build_overview_metrics(tracked_query_rollup_rows, config.pricing.usd_to_jpy, config)
    portfolio_story = build_portfolio_story(query_rollup_rows, config)
    current_result_story = build_current_result_story(current_query_rollup_rows, current_rows, config, source_loader)
    current_intent_rows = build_intent_map_rows(query_rollup_rows, config)
    current_page_gap_rows = build_page_gap_rows(query_rollup_rows, config)
    intent_rows = build_intent_map_rows(tracked_query_rollup_rows, config)
    page_gap_rows = build_page_gap_rows(tracked_query_rollup_rows, config)
    previous_delta_summary = resolve_previous_delta_summary(db, config, recent_rows)
    tracked_delta_summary = resolve_previous_delta_summary(db, config, tracked_recent_rows)
    budget_guardrail = build_budget_guardrail(
        loaded_recent_rows,
        config,
        batch_jobs=db.list_active_batch_job_reservations(limit=200),
    )
    run_table_rows = [
        {
            **row,
            "started_at": format_timestamp(row["started_at"]),
            "finished_at": format_timestamp(row["finished_at"]),
            "run_mode": localize_run_mode(row.get("run_mode")),
            "question_set_name": str(row.get("question_set_name") or "手動入力"),
        }
        for row in db.list_run_history()
    ]
    return {
        "all_recent_rows": loaded_recent_rows,
        "recent_rows": recent_rows,
        "current_rows": current_rows,
        "current_query_rollup_rows": current_query_rollup_rows,
        "current_run_id": resolved_current_run_id,
        "refresh_signature": build_refresh_signature(recent_rows),
        "tracked_recent_rows": tracked_recent_rows,
        "query_rollup_rows": query_rollup_rows,
        "tracked_query_rollup_rows": tracked_query_rollup_rows,
        "heatmap_rows": tracked_query_rollup_rows,
        "heatmap_raw_rows": tracked_recent_rows,
        "drilldown_rows": recent_rows,
        "drilldown_query_rows": query_rollup_rows,
        "metrics": metrics,
        "portfolio_story": portfolio_story,
        "current_result_story": current_result_story,
        "current_intent_rows": current_intent_rows,
        "current_page_gap_rows": current_page_gap_rows,
        "intent_rows": intent_rows,
        "page_gap_rows": page_gap_rows,
        "previous_delta_summary": previous_delta_summary,
        "tracked_delta_summary": tracked_delta_summary,
        "budget_guardrail": budget_guardrail,
        "run_table_rows": run_table_rows,
        "weakest_intent_label": current_intent_rows[0]["intent_label"] if current_intent_rows else "-",
        "top_gap_label": current_page_gap_rows[0]["page_type_label"] if current_page_gap_rows else "-",
    }
