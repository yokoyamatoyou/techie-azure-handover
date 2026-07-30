from __future__ import annotations

import json
from typing import Any

from nicegui import ui

from analysis_lib import (
    build_run_outcome_compare,
    format_schedule_slot,
    format_timestamp,
    format_weekdays_label,
    join_csv,
    parse_weekdays_csv,
)


def localize_run_mode(run_mode: Any) -> str:
    mode = str(run_mode or "").lower()
    if mode == "scheduled":
        return "自動チェック"
    if mode == "batch":
        return "まとめて分析"
    return "1回だけ確認"


def localize_batch_status(status: Any) -> str:
    mapping = {
        "validating": "検証中",
        "failed": "作成失敗",
        "in_progress": "実行中",
        "finalizing": "出力準備中",
        "completed": "完了",
        "expired": "時間切れ",
        "cancelling": "停止処理中",
        "cancelled": "停止済み",
    }
    return mapping.get(str(status or "").lower(), str(status or "-") or "-")


def count_config_keywords(config_json: Any) -> int:
    try:
        payload = json.loads(str(config_json or "{}"))
    except (TypeError, ValueError):
        return 0
    keywords = payload.get("keywords") if isinstance(payload, dict) else []
    if isinstance(keywords, list):
        return len([keyword for keyword in keywords if str(keyword or "").strip()])
    if isinstance(keywords, str):
        return len([line for line in keywords.splitlines() if line.strip()])
    return 0


def sanitize_saved_scope_label(value: Any, *, fallback: str) -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    normalized = text.upper()
    if normalized.startswith("__UI_TEST__") or "UI_TEST" in normalized:
        return fallback
    return text


def _truncate_preview(text: str, *, max_len: int = 36) -> str:
    normalized = str(text or "").strip()
    if not normalized:
        return "-"
    if len(normalized) <= max_len:
        return normalized
    return normalized[: max_len - 1] + "…"


def extract_question_set_display_meta(row: dict[str, Any]) -> dict[str, Any]:
    from config import AppConfig, get_provider_option
    from ui.runtime_copy_builders import provider_display_label

    try:
        cfg = AppConfig.model_validate_json(row.get("config_json") or "{}")
        keywords = [str(keyword).strip() for keyword in (cfg.keywords or []) if str(keyword).strip()]
        return {
            "question_count": len(keywords),
            "provider_label": provider_display_label(get_provider_option(cfg.provider)),
            "first_question_preview": _truncate_preview(keywords[0] if keywords else ""),
        }
    except Exception:
        return {
            "question_count": 0,
            "provider_label": "-",
            "first_question_preview": "-",
        }


def build_schedule_weekday_summary(selected_weekday_values: list[Any], *, time_of_day: str = "09:00") -> tuple[str, str]:
    weekday_keys = sorted({str(day) for day in selected_weekday_values if str(day).strip() != ""})
    weekday_labels = format_weekdays_label([int(day) for day in weekday_keys if str(day).isdigit()])
    weekly_count = len(weekday_keys)
    selection_text = f"曜日: {weekday_labels or '-'} / 週{weekly_count or 0}回"
    save_text = f"保存後の予定: {str(time_of_day or '09:00').strip() or '09:00'} に自動チェック"
    return selection_text, save_text


def build_schedule_setting_status_text(enabled: bool) -> str:
    return f"この予定: {'有効' if enabled else '停止'}"


def build_batch_job_option_label(row: dict[str, Any]) -> str:
    imported = int(row.get("imported_result_count") or 0) + int(row.get("imported_error_count") or 0)
    question_set_label = sanitize_saved_scope_label(row.get("question_set_name"), fallback="保存済み条件")
    return (
        f"{localize_run_mode(row.get('run_mode'))} | {question_set_label} | "
        f"{localize_batch_status(row.get('status'))} | 結果反映 {imported}/{int(row.get('request_count') or 0)}件"
    )


def build_batch_table_columns() -> list[dict[str, str]]:
    return [
        {"name": "submitted_at", "label": "開始", "field": "submitted_at"},
        {"name": "run_mode", "label": "方式", "field": "run_mode"},
        {"name": "question_set_name", "label": "保存済み条件", "field": "question_set_name"},
        {"name": "status_label", "label": "状態", "field": "status_label"},
        {"name": "request_count", "label": "件数", "field": "request_count"},
        {"name": "progress_label", "label": "進み具合", "field": "progress_label"},
        {"name": "import_label", "label": "結果反映", "field": "import_label"},
    ]


def build_result_table_columns(show_costs: bool) -> list[dict[str, str]]:
    return [
        {"name": "analyzed_at", "label": "確認時刻", "field": "analyzed_at"},
        {"name": "provider_label", "label": "対象AI", "field": "provider_label"},
        {"name": "keyword_raw", "label": "質問", "field": "keyword_raw"},
        {"name": "visibility_label", "label": "結論", "field": "visibility_label"},
        {"name": "result_digest", "label": "市場での位置", "field": "result_digest"},
        {"name": "page_gap_label", "label": "不足している情報タイプ", "field": "page_gap_label"},
    ]


def build_intent_table_columns() -> list[dict[str, str]]:
    return [
        {"name": "intent_label", "label": "質問タイプ", "field": "intent_label"},
        {"name": "needs_fix_count", "label": "要改善", "field": "needs_fix_count"},
        {"name": "needs_fix_rate_text", "label": "全試行比", "field": "needs_fix_rate_text"},
        {"name": "top_page_type", "label": "不足している情報", "field": "top_page_type"},
    ]


def build_gap_table_columns() -> list[dict[str, str]]:
    return [
        {"name": "page_type_label", "label": "ページ", "field": "page_type_label"},
        {"name": "needs_fix_count", "label": "要改善", "field": "needs_fix_count"},
        {"name": "needs_fix_rate_text", "label": "全試行比", "field": "needs_fix_rate_text"},
        {"name": "next_step", "label": "次の一手", "field": "next_step"},
    ]


def build_run_table_columns(show_costs: bool) -> list[dict[str, str]]:
    return [
        {"name": "started_at", "label": "開始", "field": "started_at"},
        {"name": "finished_at", "label": "終了", "field": "finished_at"},
        {"name": "run_mode", "label": "実行方式", "field": "run_mode"},
        {"name": "question_set_name", "label": "保存済み条件", "field": "question_set_name"},
        {"name": "result_count", "label": "結果件数", "field": "result_count"},
    ]


def build_question_set_option_label(row: dict[str, Any]) -> str:
    state_label = "アーカイブ済み" if bool(row.get("is_archived")) else "有効"
    question_set_label = sanitize_saved_scope_label(row.get("name"), fallback="保存済み条件")
    meta = extract_question_set_display_meta(row)
    return f"{question_set_label} / 質問{meta['question_count']}件 / {meta['provider_label']} / {state_label}"


def build_question_set_detail_text(row: dict[str, Any] | None) -> str:
    if not row:
        return "保存済み条件を選ぶと、質問数・対象AI・先頭質問・最後の結果保存時刻をここに表示します。"
    last_run = format_timestamp(row.get("last_run_at")) if row.get("last_run_at") else "未実行"
    last_mode = localize_run_mode(row.get("last_run_mode")) if row.get("last_run_mode") else "未実行"
    state_label = "アーカイブ済み" if bool(row.get("is_archived")) else "有効"
    meta = extract_question_set_display_meta(row)
    return (
        f"質問{meta['question_count']}件 / {meta['provider_label']} / {state_label} / "
        f"最後に結果を保存: {last_run}（{last_mode}） / 先頭質問: {meta['first_question_preview']}"
    )


def build_question_set_table_columns() -> list[dict[str, str]]:
    return [
        {"name": "name", "label": "保存名", "field": "name"},
        {"name": "question_count", "label": "質問数", "field": "question_count"},
        {"name": "provider_label", "label": "対象AI", "field": "provider_label"},
        {"name": "first_question_preview", "label": "先頭質問", "field": "first_question_preview"},
        {"name": "status_label", "label": "状態", "field": "status_label"},
        {"name": "last_run_at", "label": "最後に結果を保存", "field": "last_run_at"},
        {"name": "last_run_mode", "label": "方式", "field": "last_run_mode"},
    ]


def build_schedule_table_columns() -> list[dict[str, str]]:
    return [
        {"name": "name", "label": "自動チェック", "field": "name"},
        {"name": "question_set_name", "label": "対象の保存済み条件", "field": "question_set_name"},
        {"name": "schedule_label", "label": "曜日 / 時刻", "field": "schedule_label"},
        {"name": "weekly_run_count", "label": "週回数", "field": "weekly_run_count"},
        {"name": "next_run_label", "label": "次回", "field": "next_run_label"},
        {"name": "status_label", "label": "状態", "field": "status_label"},
    ]


def localize_schedule_status(status: Any) -> str:
    mapping = {
        "enabled": "有効",
        "disabled": "停止",
        "submitted": "開始済み",
        "imported": "反映済み",
        "cost_blocked": "実行上限で保留",
        "submit_error": "開始失敗",
        "poll_error": "更新失敗",
        "provider_unavailable": "未対応",
        "missing_api_key": "APIキー未設定",
        "missing_question_set": "保存済み条件欠落",
        "invalid_scope": "監査条件不足",
        "empty_keywords": "質問なし",
    }
    return mapping.get(str(status or "").lower(), str(status or "-") or "-")


def build_schedule_option_label(row: dict[str, Any]) -> str:
    status_label = localize_schedule_status(row.get("last_status") or ("enabled" if row.get("enabled") else "disabled"))
    schedule_label = sanitize_saved_scope_label(row.get("name"), fallback="自動チェック")
    return (
        f"{schedule_label} / "
        f"{format_weekdays_label(parse_weekdays_csv(row.get('weekdays_csv')))} {row.get('time_of_day')} / {status_label}"
    )


def build_question_set_snapshot(question_set: dict[str, Any]) -> dict[str, Any]:
    from config import AppConfig
    from ui.dashboard_views import localize_analysis_mode

    cfg = AppConfig.model_validate_json(question_set["config_json"])
    queries = list(dict.fromkeys(cfg.keywords))
    return {
        "kind": "question_set",
        "label": sanitize_saved_scope_label(question_set.get("name"), fallback="保存済み条件"),
        "queries": queries,
        "query_count": len(queries),
        "analysis_mode": localize_analysis_mode(cfg.analysis_mode),
        "repeat_count": int(cfg.repeat_count or 0),
        "reasoning_effort": cfg.reasoning_effort,
        "target_domain": str(cfg.target_domain or "-").strip() or "-",
        "brand_terms": join_csv(list(dict.fromkeys(cfg.brand_terms))) or "-",
        "market_context_terms": join_csv(list(dict.fromkeys(cfg.market_context_terms))) or "-",
        "competitor_terms": join_csv(list(dict.fromkeys(cfg.competitor_terms))) or "-",
        "allowed_domains": join_csv(list(dict.fromkeys(cfg.allowed_domains))) or "-",
        "weekdays_label": "-",
        "time_of_day": "-",
        "timezone": cfg.timezone or "-",
        "enabled_label": "-",
    }


def build_schedule_snapshot(db: Any, schedule: dict[str, Any]) -> dict[str, Any]:
    linked_question_set = db.get_question_set(str(schedule.get("question_set_id") or ""))
    if linked_question_set:
        snapshot = build_question_set_snapshot(linked_question_set)
    else:
        snapshot = {
            "kind": "schedule",
            "label": sanitize_saved_scope_label(schedule.get("name"), fallback="自動チェック"),
            "queries": [],
            "query_count": 0,
            "analysis_mode": "-",
            "repeat_count": 0,
            "reasoning_effort": "-",
            "target_domain": "-",
            "brand_terms": "-",
            "market_context_terms": "-",
            "competitor_terms": "-",
            "allowed_domains": "-",
            "timezone": "-",
        }
    snapshot.update(
        {
            "kind": "schedule",
            "label": sanitize_saved_scope_label(schedule.get("name"), fallback="自動チェック"),
            "weekdays_label": format_weekdays_label(parse_weekdays_csv(schedule.get("weekdays_csv"))),
            "time_of_day": str(schedule.get("time_of_day") or "-"),
            "timezone": str(schedule.get("timezone") or snapshot.get("timezone") or "-"),
            "enabled_label": "有効" if schedule.get("enabled") else "停止",
        }
    )
    return snapshot


def build_plan_diff(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    field_specs = [
        ("query_count", "質問数"),
        ("analysis_mode", "監査モード"),
        ("reasoning_effort", "推論"),
        ("target_domain", "自社URL"),
        ("brand_terms", "ブランド語"),
        ("market_context_terms", "重点テーマ"),
        ("competitor_terms", "比較対象"),
        ("allowed_domains", "追加ドメイン"),
        ("weekdays_label", "曜日"),
        ("time_of_day", "時刻"),
        ("timezone", "タイムゾーン"),
        ("enabled_label", "有効状態"),
    ]
    field_diffs: list[dict[str, str]] = []
    for key, label in field_specs:
        left_value = str(left.get(key) or "-").strip() or "-"
        right_value = str(right.get(key) or "-").strip() or "-"
        if left_value == right_value:
            continue
        field_diffs.append({"label": label, "left": left_value, "right": right_value})

    left_queries = list(dict.fromkeys([str(item or "") for item in left.get("queries") or []]))
    right_queries = list(dict.fromkeys([str(item or "") for item in right.get("queries") or []]))
    added_queries = [query for query in right_queries if query not in left_queries]
    removed_queries = [query for query in left_queries if query not in right_queries]
    shared_queries = [query for query in left_queries if query in right_queries]
    return {
        "field_diffs": field_diffs,
        "added_queries": added_queries,
        "removed_queries": removed_queries,
        "shared_query_count": len(shared_queries),
    }


def localize_cluster_kind(cluster_kind: str) -> str:
    return {
        "intent": "意図クラスタ",
        "page_gap": "不足ページクラスタ",
        "question_set": "保存済み条件単位",
    }.get(cluster_kind, cluster_kind)


def build_cluster_candidate_label(candidate: dict[str, Any]) -> str:
    queries = join_csv(candidate.get("representative_queries") or [])
    return (
        f"{candidate.get('cluster_label')} | {int(candidate.get('query_count') or 0)}質問 | "
        f"要改善 {int(candidate.get('needs_fix_count') or 0)}件 | "
        f"{candidate.get('recommended_page_type') or '-'}"
        + (f" | {queries}" if queries else "")
    )


def build_saved_cluster_brief_option_label(row: dict[str, Any]) -> str:
    return (
        f"{row.get('cluster_label')} | {localize_cluster_kind(str(row.get('cluster_kind') or ''))} | "
        f"{row.get('generated_title') or '-'} | {format_timestamp(row.get('updated_at'))}"
    )


def build_cluster_brief_table_columns() -> list[dict[str, str]]:
    return [
        {"name": "updated_at", "label": "生成", "field": "updated_at"},
        {"name": "cluster_kind", "label": "単位", "field": "cluster_kind"},
        {"name": "cluster_label", "label": "対象", "field": "cluster_label"},
        {"name": "query_count", "label": "質問数", "field": "query_count"},
        {"name": "generated_title", "label": "下書きタイトル", "field": "generated_title"},
    ]


def build_outcome_run_option_label(row: dict[str, Any]) -> str:
    return (
        f"{format_timestamp(row.get('started_at'))} | "
        f"{localize_run_mode(row.get('run_mode'))} | "
        f"{int(row.get('result_count') or 0)}件"
    )


def build_export_table_columns() -> list[dict[str, str]]:
    return [
        {"name": "label", "label": "出力ファイル", "field": "label"},
        {"name": "path", "label": "保存先", "field": "path"},
        {"name": "generated_at", "label": "生成", "field": "generated_at"},
    ]


def build_scheduler_status_text(scheduler_service: Any) -> str:
    snapshot = scheduler_service.status_snapshot()
    if not snapshot["active"]:
        return "アプリ側の監視: 停止中"
    return f"アプリ側の監視: 稼働中 | 最終確認 {format_timestamp(snapshot['last_tick_at'])} | {snapshot['last_message']}"


def refresh_batch_job_views(
    db: Any,
    batch_job_select: ui.select,
    batch_job_table: ui.table,
    batch_status_label: ui.label,
    batch_summary_label: ui.label,
) -> None:
    batch_jobs = db.list_batch_jobs()
    options = {row["batch_job_id"]: build_batch_job_option_label(row) for row in batch_jobs}
    current_value = batch_job_select.value if batch_job_select.value in options else None
    if current_value is None and options:
        current_value = next(iter(options))
    batch_job_select.options = options
    batch_job_select.value = current_value
    batch_job_select.update()

    batch_job_table.rows = [
        {
            "batch_job_id": row.get("batch_job_id"),
            "submitted_at": format_timestamp(row.get("submitted_at") or row.get("created_at")),
            "run_mode": localize_run_mode(row.get("run_mode")),
            "question_set_name": sanitize_saved_scope_label(row.get("question_set_name"), fallback="保存済み条件"),
            "status_label": localize_batch_status(row.get("status")),
            "request_count": int(row.get("request_count") or 0),
            "progress_label": (
                f"{int(row.get('request_counts_completed') or 0)}/{int(row.get('request_counts_total') or 0)} 成功"
                f" / {int(row.get('request_counts_failed') or 0)} 失敗"
            ),
            "import_label": (
                f"{int(row.get('imported_result_count') or 0)} 成功"
                f" / {int(row.get('imported_error_count') or 0)} エラー"
            ),
        }
        for row in batch_jobs
    ]
    batch_job_table.update()

    selected = next((row for row in batch_jobs if row["batch_job_id"] == current_value), None)
    if not selected:
        batch_status_label.text = "まだまとめて分析の履歴はありません"
        batch_summary_label.text = "保存済み条件を入力へ読み込み、複数質問を今回だけまとめて確認するときに使います。"
        batch_status_label.update()
        batch_summary_label.update()
        return

    imported_total = int(selected.get("imported_result_count") or 0) + int(selected.get("imported_error_count") or 0)
    request_total = int(selected.get("request_count") or 0)
    target_question_count = count_config_keywords(selected.get("config_json"))
    target_question_label = f"{target_question_count}件" if target_question_count > 0 else "-"
    from config import get_provider_option
    from ui.runtime_copy_builders import provider_display_label

    provider_label = provider_display_label(get_provider_option(str(selected.get("provider_key") or "openai")))
    batch_status_label.text = (
        f"履歴の選択中: {localize_batch_status(selected.get('status'))} | "
            f"{sanitize_saved_scope_label(selected.get('question_set_name'), fallback='保存済み条件')} | "
        f"開始 {format_timestamp(selected.get('submitted_at') or selected.get('created_at'))} | "
        f"{provider_label} | 対象質問 {target_question_label}"
    )
    if selected.get("last_error"):
        batch_summary_label.text = str(selected.get("last_error"))
    else:
        batch_summary_label.text = (
            f"実送信 {int(selected.get('request_counts_total') or request_total)}件 / "
            f"結果反映 {imported_total}/{request_total} 件"
        )
    batch_status_label.update()
    batch_summary_label.update()


def refresh_question_set_views(
    db: Any,
    question_set_select: ui.select,
    question_set_table: ui.table,
    schedule_question_set_select: ui.select | None = None,
) -> None:
    question_sets = db.list_question_sets()
    active_question_sets = [row for row in question_sets if not bool(row.get("is_archived"))]
    options = {row["question_set_id"]: build_question_set_option_label(row) for row in question_sets}
    current_value = question_set_select.value if question_set_select.value in options else None
    if current_value is None and options:
        current_value = next(iter(options))
    question_set_select.options = options
    question_set_select.value = current_value
    question_set_select.update()
    if schedule_question_set_select is not None:
        active_options = {row["question_set_id"]: build_question_set_option_label(row) for row in active_question_sets}
        schedule_question_set_select.options = active_options
        if schedule_question_set_select.value not in active_options:
            schedule_question_set_select.value = next(iter(active_options)) if active_options else None
        schedule_question_set_select.update()

    question_set_table.rows = [
        {
            "question_set_id": row.get("question_set_id"),
            "name": sanitize_saved_scope_label(row.get("name"), fallback="保存済み条件"),
            **extract_question_set_display_meta(row),
            "status_label": "アーカイブ済み" if bool(row.get("is_archived")) else "有効",
            "updated_at": format_timestamp(row.get("updated_at")),
            "last_run_at": format_timestamp(row.get("last_run_at")),
            "last_run_mode": localize_run_mode(row.get("last_run_mode")),
        }
        for row in question_sets
    ]
    question_set_table.update()


def refresh_schedule_views(
    db: Any,
    scheduler_service: Any,
    schedule_table: ui.table,
    scheduler_status_label: ui.label,
    schedule_select: ui.select | None = None,
    compare_target_select: ui.select | None = None,
    compare_mode_select: ui.select | None = None,
) -> None:
    schedules = db.list_schedules(limit=50)
    schedule_table.rows = [
        {
            "schedule_id": row.get("schedule_id"),
            "name": sanitize_saved_scope_label(row.get("name"), fallback="自動チェック"),
            "question_set_name": sanitize_saved_scope_label(row.get("question_set_name"), fallback="保存済み条件"),
            "schedule_label": f"{format_weekdays_label(parse_weekdays_csv(row.get('weekdays_csv')))} / {row.get('time_of_day')}",
            "weekly_run_count": int(row.get("weekly_run_count") or 0),
            "next_run_label": format_schedule_slot(row.get("next_run_at"), str(row.get("timezone") or "Asia/Tokyo")),
            "status_label": localize_schedule_status(row.get("last_status") or ("enabled" if row.get("enabled") else "disabled")),
        }
        for row in schedules
    ]
    schedule_table.update()
    if schedule_select is not None:
        schedule_options = {row["schedule_id"]: build_schedule_option_label(row) for row in schedules}
        current_value = schedule_select.value if schedule_select.value in schedule_options else None
        if current_value is None and schedule_options:
            current_value = next(iter(schedule_options))
        schedule_select.options = schedule_options
        schedule_select.value = current_value
        schedule_select.update()
    if compare_target_select is not None and compare_mode_select is not None:
        compare_mode = str(compare_mode_select.value or "schedule")
        if compare_mode == "schedule":
            compare_options = {row["schedule_id"]: build_schedule_option_label(row) for row in schedules}
        else:
            question_sets = db.list_question_sets(limit=100)
            compare_options = {row["question_set_id"]: build_question_set_option_label(row) for row in question_sets}
        current_compare = compare_target_select.value if compare_target_select.value in compare_options else None
        if current_compare is None and compare_options:
            current_compare = next(iter(compare_options))
        compare_target_select.options = compare_options
        compare_target_select.value = current_compare
        compare_target_select.update()
    scheduler_status_label.text = build_scheduler_status_text(scheduler_service)
    scheduler_status_label.update()


def render_schedule_diff(
    db: Any,
    schedule_id: str,
    compare_mode: str,
    compare_target_id: str,
    diff_container: ui.column,
) -> None:
    diff_container.clear()
    with diff_container:
        if not schedule_id:
            ui.label("比較元の自動チェックを選ぶと差分を表示します。").classes("text-[14px] soft-label")
            return
        left_schedule = db.get_schedule(schedule_id)
        if not left_schedule:
            ui.label("比較元の自動チェックが見つかりません。").classes("text-[14px] soft-label")
            return
        left_snapshot = build_schedule_snapshot(db, left_schedule)

        if compare_mode == "schedule":
            if not compare_target_id:
                ui.label("比較対象の自動チェックを選択してください。").classes("text-[14px] soft-label")
                return
            if compare_target_id == schedule_id:
                ui.label("同じ自動チェック同士は比較できません。別の自動チェックを選択してください。").classes("text-[14px] soft-label")
                return
            right_schedule = db.get_schedule(compare_target_id)
            if not right_schedule:
                ui.label("比較対象の自動チェックが見つかりません。").classes("text-[14px] soft-label")
                return
            right_snapshot = build_schedule_snapshot(db, right_schedule)
        else:
            if not compare_target_id:
                ui.label("比較対象の保存済み条件を選択してください。").classes("text-[14px] soft-label")
                return
            question_set = db.get_question_set(compare_target_id)
            if not question_set:
                ui.label("比較対象の保存済み条件が見つかりません。").classes("text-[14px] soft-label")
                return
            right_snapshot = build_question_set_snapshot(question_set)

        diff = build_plan_diff(left_snapshot, right_snapshot)
        ui.label("差分比較").classes("summary-eyebrow")
        ui.label(f"{left_snapshot['label']} / {right_snapshot['label']}").classes("text-[16px] font-bold text-main mt-2")
        with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
            with ui.column().classes("mini-stat-card flex-1 gap-1"):
                ui.label("共通質問").classes("text-[12px] tracking-[0.18em] soft-label")
                ui.label(f"{diff['shared_query_count']}件").classes("metric-font text-[20px] font-bold text-main")
            with ui.column().classes("mini-stat-card flex-1 gap-1"):
                ui.label("追加質問").classes("text-[12px] tracking-[0.18em] soft-label")
                ui.label(f"{len(diff['added_queries'])}件").classes("metric-font text-[20px] font-bold text-brand")
            with ui.column().classes("mini-stat-card flex-1 gap-1"):
                ui.label("削除質問").classes("text-[12px] tracking-[0.18em] soft-label")
                ui.label(f"{len(diff['removed_queries'])}件").classes("metric-font text-[20px] font-bold text-external")
        if diff["field_diffs"]:
            ui.label("設定差分").classes("summary-eyebrow mt-5")
            for item in diff["field_diffs"]:
                with ui.row().classes("w-full gap-3 mt-2 flex-wrap"):
                    ui.label(item["label"]).classes("signal-chip signal-neutral")
                    ui.label(f"{item['left']} → {item['right']}").classes("text-[14px] leading-6 text-support")
        else:
            ui.label("主な設定差分はありません。").classes("text-[14px] soft-label mt-4")
        if diff["added_queries"]:
            ui.label("追加される質問").classes("summary-eyebrow mt-5")
            for query in diff["added_queries"][:8]:
                ui.label(f"+ {query}").classes("text-[14px] leading-6 text-support mt-1")
        if diff["removed_queries"]:
            ui.label("抜ける質問").classes("summary-eyebrow mt-5")
            for query in diff["removed_queries"][:8]:
                ui.label(f"- {query}").classes("text-[14px] leading-6 text-support mt-1")


def refresh_cluster_brief_views(
    db: Any,
    rows: list[dict[str, Any]],
    config: Any,
    cluster_kind_select: ui.select,
    cluster_target_select: ui.select,
    saved_brief_select: ui.select,
    cluster_brief_table: ui.table,
) -> None:
    from analysis_lib import build_cluster_brief_candidates

    candidates = build_cluster_brief_candidates(rows, config)
    cluster_kind = str(cluster_kind_select.value or "intent")
    filtered_candidates = [item for item in candidates if item["cluster_kind"] == cluster_kind]
    target_options = {
        f"{item['cluster_kind']}::{item['cluster_key']}": build_cluster_candidate_label(item)
        for item in filtered_candidates
    }
    current_target = cluster_target_select.value if cluster_target_select.value in target_options else None
    if current_target is None and target_options:
        current_target = next(iter(target_options))
    cluster_target_select.options = target_options
    cluster_target_select.value = current_target
    cluster_target_select.update()

    saved_briefs = db.list_cluster_briefs(limit=40)
    saved_options = {row["brief_id"]: build_saved_cluster_brief_option_label(row) for row in saved_briefs}
    current_saved = saved_brief_select.value if saved_brief_select.value in saved_options else None
    if current_saved is None and saved_options:
        current_saved = next(iter(saved_options))
    saved_brief_select.options = saved_options
    saved_brief_select.value = current_saved
    saved_brief_select.update()
    cluster_brief_table.rows = [
        {
            "brief_id": row.get("brief_id"),
            "updated_at": format_timestamp(row.get("updated_at")),
            "cluster_kind": localize_cluster_kind(str(row.get("cluster_kind") or "")),
            "cluster_label": row.get("cluster_label"),
            "query_count": int(row.get("query_count") or 0),
            "generated_title": row.get("generated_title") or "-",
        }
        for row in saved_briefs
    ]
    cluster_brief_table.update()


def render_cluster_brief_payload(brief: dict[str, Any] | None, container: ui.column) -> None:
    container.clear()
    with container:
        if not brief:
            ui.label("クラスタ下書きはまだありません。").classes("text-[14px] soft-label")
            return
        with ui.card().classes("card-detail p-5 w-full"):
            ui.label("クラスタ下書き").classes("section-font section-title text-[22px] font-bold")
            with ui.row().classes("w-full gap-2 mt-3 flex-wrap"):
                ui.label(str(brief.get("cluster_kind_label") or localize_cluster_kind(str(brief.get("cluster_kind") or "")))).classes("signal-chip signal-neutral")
                ui.label(str(brief.get("page_type") or "-")).classes("signal-chip signal-positive")
            ui.label(str(brief.get("brief_title") or brief.get("generated_title") or "-")).classes("text-[17px] font-bold text-main mt-3")
            ui.label(str(brief.get("brief_summary") or "-")).classes("text-[14px] leading-7 text-support mt-3")
            ui.label("対象意図のまとまり").classes("summary-eyebrow mt-5")
            ui.label(str(brief.get("intent_cluster_summary") or "-")).classes("text-[14px] leading-6 text-support mt-2")
            ui.label("代表質問").classes("summary-eyebrow mt-5")
            for query in brief.get("representative_queries") or []:
                ui.label(f"- {query}").classes("text-[14px] leading-6 text-support mt-1")
            if not (brief.get("representative_queries") or []):
                ui.label("代表質問はまだありません。").classes("text-[14px] soft-label mt-2")
            ui.label("代表引用ドメイン").classes("summary-eyebrow mt-5")
            ui.label(join_csv(brief.get("representative_citation_domains") or []) or "なし").classes("text-[14px] leading-6 text-support mt-2")
            ui.label("推奨見出し構成").classes("summary-eyebrow mt-5")
            for index, heading in enumerate(brief.get("headings") or [], start=1):
                ui.label(f"{index}. {heading}").classes("text-[14px] leading-6 text-support mt-1")
            ui.label("FAQ").classes("summary-eyebrow mt-5")
            for item in brief.get("faqs") or []:
                ui.label(f"Q. {item['question']}").classes("text-[14px] font-bold text-main mt-2")
                ui.label(f"A. {item['answer_hint']}").classes("text-[14px] leading-6 text-support mt-1")
            ui.label("CTA").classes("summary-eyebrow mt-5")
            ui.label(str(brief.get("cta") or "-")).classes("text-[14px] leading-6 text-support mt-2")
            ui.label("補足").classes("summary-eyebrow mt-5")
            ui.label(
                f"返答タイプ: {join_csv(brief.get('answer_type_labels') or []) or 'なし'} / "
                f"ブランド言及: {join_csv(brief.get('reference_brands') or []) or 'なし'}"
            ).classes("text-[14px] leading-6 text-support mt-2")


def refresh_outcome_compare_views(
    db: Any,
    scope_kind_select: ui.select,
    scope_target_select: ui.select,
    run_a_select: ui.select,
    run_b_select: ui.select,
) -> None:
    scope_kind = str(scope_kind_select.value or "schedule")
    if scope_kind == "schedule":
        subjects = db.list_schedules(limit=100)
        subject_options = {row["schedule_id"]: build_schedule_option_label(row) for row in subjects}
    else:
        subjects = db.list_question_sets(limit=100)
        subject_options = {row["question_set_id"]: build_question_set_option_label(row) for row in subjects}
    current_subject = scope_target_select.value if scope_target_select.value in subject_options else None
    if current_subject is None and subject_options:
        current_subject = next(iter(subject_options))
    scope_target_select.options = subject_options
    scope_target_select.value = current_subject
    scope_target_select.update()

    runs = db.list_runs_for_scope(scope_kind=scope_kind, scope_id=str(current_subject or ""), limit=30) if current_subject else []
    run_options = {row["run_id"]: build_outcome_run_option_label(row) for row in runs}
    current_a = run_a_select.value if run_a_select.value in run_options else None
    current_b = run_b_select.value if run_b_select.value in run_options else None
    run_ids = list(run_options.keys())
    if current_a is None and run_ids:
        current_a = run_ids[0]
    if current_b is None:
        current_b = run_ids[1] if len(run_ids) > 1 else None
    if current_b == current_a and len(run_ids) > 1:
        current_b = next((run_id for run_id in run_ids if run_id != current_a), current_b)
    run_a_select.options = run_options
    run_a_select.value = current_a
    run_a_select.update()
    run_b_select.options = run_options
    run_b_select.value = current_b
    run_b_select.update()


def render_outcome_compare(
    db: Any,
    scope_kind: str,
    scope_id: str,
    run_a_id: str,
    run_b_id: str,
    container: ui.column,
    config: Any,
) -> None:
    container.clear()
    with container:
        if not scope_id:
            ui.label("比較対象の系列を選ぶと、実行結果の比較を表示します。").classes("text-[14px] soft-label")
            return
        if not run_a_id or not run_b_id:
            ui.label("比較する 2 回分の実行を選択してください。").classes("text-[14px] soft-label")
            return
        if run_a_id == run_b_id:
            ui.label("同じ実行同士は比較できません。").classes("text-[14px] soft-label")
            return
        run_rows = db.list_results_for_runs([run_a_id, run_b_id])
        left_rows = [row for row in run_rows if str(row.get("run_id") or "") == run_a_id]
        right_rows = [row for row in run_rows if str(row.get("run_id") or "") == run_b_id]
        if not left_rows or not right_rows:
            ui.label("選択した実行の結果が不足しています。").classes("text-[14px] soft-label")
            return
        run_meta = {row["run_id"]: row for row in db.list_runs_for_scope(scope_kind=scope_kind, scope_id=scope_id, limit=30)}
        left_meta = run_meta.get(run_a_id, {})
        right_meta = run_meta.get(run_b_id, {})
        left_label = build_outcome_run_option_label(left_meta) if left_meta else run_a_id
        right_label = build_outcome_run_option_label(right_meta) if right_meta else run_b_id
        compare = build_run_outcome_compare(left_rows, right_rows, config, left_label=left_label, right_label=right_label)

        def delta_label(value: float) -> str:
            return f"{value:+.1f}pt"

        ui.label("実行結果の比較").classes("summary-eyebrow")
        ui.label(compare["headline"]).classes("text-[16px] font-bold text-main mt-2")
        ui.label(compare["summary"]).classes("text-[14px] leading-6 text-support mt-2")
        with ui.row().classes("w-full gap-3 mt-4 flex-wrap"):
            for title, left_value, right_value, delta_value, tone in [
                ("可視率", compare["left"]["visibility_rate"], compare["right"]["visibility_rate"], compare["visibility_delta"], "text-brand"),
                ("自社言及", compare["left"]["owned_mention_rate"], compare["right"]["owned_mention_rate"], compare["owned_mention_delta"], "text-self"),
                ("比較対象言及", compare["left"]["competitor_mention_rate"], compare["right"]["competitor_mention_rate"], compare["competitor_mention_delta"], "text-competitive"),
                ("平均判定スコア", compare["left"]["avg_visibility_score"], compare["right"]["avg_visibility_score"], round(compare["right"]["avg_visibility_score"] - compare["left"]["avg_visibility_score"], 1), "text-main"),
                ("揺れ幅", compare["left"]["score_stddev"], compare["right"]["score_stddev"], round(compare["right"]["score_stddev"] - compare["left"]["score_stddev"], 1), "text-competitive"),
            ]:
                with ui.column().classes("mini-stat-card flex-1 gap-1 min-w-[180px]"):
                    ui.label(title).classes("text-[12px] tracking-[0.18em] soft-label")
                    ui.label(f"{left_value:.1f} → {right_value:.1f}").classes("metric-font text-[18px] font-bold text-main")
                    ui.label(delta_label(delta_value)).classes(f"text-[13px] font-bold {tone}")
        for title, rows_data, key_name in [
            ("意図の分布", compare["intent_rows"], "label"),
            ("不足ページの分布", compare["page_gap_rows"], "label"),
            ("引用ドメイン上位", compare["citation_domain_rows"], "domain"),
        ]:
            ui.label(title).classes("summary-eyebrow mt-5")
            if not rows_data:
                ui.label("比較できるデータがありません。").classes("text-[14px] soft-label mt-2")
                continue
            for item in rows_data:
                name = item[key_name]
                ui.label(
                    f"{name}: {item['left_rate']:.1f}% → {item['right_rate']:.1f}% ({delta_label(float(item['delta']))})"
                ).classes("text-[14px] leading-6 text-support mt-1")


def refresh_export_views(
    export_table: ui.table,
    export_status_label: ui.label,
    export_rows: list[dict[str, str]],
    report_preview_label: ui.label | None = None,
    report_preview: str = "",
) -> None:
    export_table.rows = export_rows
    export_table.update()
    export_status_label.text = (
        f"最新 export は {export_rows[0]['generated_at']} に更新しました。"
        if export_rows
        else "まだ export を生成していません。"
    )
    export_status_label.update()
    if report_preview_label is not None:
        report_preview_label.text = report_preview or "まだ報告用まとめはありません。"
        report_preview_label.update()
