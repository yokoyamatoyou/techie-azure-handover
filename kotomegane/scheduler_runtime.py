from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from analysis_lib import (
    build_budget_guardrail,
    compute_next_schedule_run,
    estimate_cost_usd,
    normalize_text,
    parse_weekdays_csv,
    resolve_latest_due_schedule_slot,
    normalize_domain_host,
)
from config import (
    ANALYSIS_MODE_OWNED_ONLY,
    AppConfig,
    get_api_key_status,
    get_provider_option,
)
from llmo_client import build_provider_client
from query_planning import ExecutionPlan, QueryPlanner, build_execution_plan
from run_planning import prepare_query_plans_for_run
from run_policy import resolve_run_policy
from runtime.common import build_error_result, get_missing_required_fields, sanitize_runtime_error_message
from storage import Storage


class ScheduledMonitorService:
    def __init__(self, db: Storage) -> None:
        self.db = db
        self.query_planner = QueryPlanner()
        self._task: asyncio.Task[Any] | None = None
        self._running = False
        self.last_tick_at: float | None = None
        self.last_message = "定期バッチ実行はまだ起動していません。"

    def start(self) -> None:
        if self._task is not None:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        self.last_message = "定期バッチ実行の監視を開始しました。"

    async def stop(self) -> None:
        self._running = False
        task = self._task
        self._task = None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    def status_snapshot(self) -> dict[str, Any]:
        return {
            "active": self._task is not None and not self._task.done(),
            "last_tick_at": self.last_tick_at,
            "last_message": self.last_message,
        }

    async def _loop(self) -> None:
        while self._running:
            try:
                await self.tick()
            except Exception as exc:
                self.last_message = f"定期監視でエラーが発生しました: {exc}"
            await asyncio.sleep(60.0)

    async def tick(self) -> None:
        self.last_tick_at = time.time()
        await self._dispatch_due_schedules()
        await self._poll_scheduled_batches()

    async def _dispatch_due_schedules(self) -> None:
        schedules = self.db.list_schedules(limit=100, enabled_only=True)
        now = time.time()
        recent_rows = self.db.list_recent_results(limit=500)
        for schedule in schedules:
            weekdays = parse_weekdays_csv(schedule.get("weekdays_csv"))
            next_run_at = compute_next_schedule_run(
                weekdays,
                int(schedule.get("weekly_run_count") or 0),
                str(schedule.get("time_of_day") or "09:00"),
                str(schedule.get("timezone") or "Asia/Tokyo"),
                base_timestamp=now,
            )
            if next_run_at:
                self.db.update_schedule_runtime(schedule["schedule_id"], next_run_at=next_run_at)

            due_slot = resolve_latest_due_schedule_slot(
                weekdays,
                int(schedule.get("weekly_run_count") or 0),
                str(schedule.get("time_of_day") or "09:00"),
                str(schedule.get("timezone") or "Asia/Tokyo"),
                now_timestamp=now,
            )
            if not due_slot:
                continue
            slot_key, scheduled_for = due_slot
            created_at = float(schedule.get("created_at") or 0.0)
            last_scheduled_slot = str(schedule.get("last_scheduled_slot") or "")
            # A newly created future schedule should not immediately backfill a prior-week slot.
            if not last_scheduled_slot and created_at and scheduled_for + 60.0 < created_at:
                continue
            if last_scheduled_slot == slot_key:
                continue
            if not self.db.claim_schedule_dispatch(str(schedule["schedule_id"]), slot_key, scheduled_for=scheduled_for):
                continue

            question_set = self.db.get_question_set(str(schedule.get("question_set_id") or ""))
            if not question_set:
                error_text = "質問セットが見つからないため定期実行を開始できませんでした。"
                self.db.update_schedule_runtime(
                    schedule["schedule_id"],
                    last_scheduled_slot=slot_key,
                    last_run_at=now,
                    last_status="missing_question_set",
                    last_error=error_text,
                )
                self.db.update_schedule_dispatch(str(schedule["schedule_id"]), slot_key, status="missing_question_set", error_text=error_text)
                continue

            cfg = AppConfig.model_validate_json(question_set["config_json"])
            provider = get_provider_option(cfg.provider)
            scheduled_policy = resolve_run_policy(cfg, "scheduled")
            api_key_status = get_api_key_status(cfg.provider)
            run_guardrail = float(schedule.get("cost_guardrail_usd") or cfg.run_budget_guardrail_usd or 0.0)
            budget_guardrail = build_budget_guardrail(
                recent_rows,
                cfg,
                batch_jobs=self.db.list_active_batch_job_reservations(limit=200),
            )
            missing_required_fields = get_missing_required_fields(cfg)

            if cfg.analysis_mode == ANALYSIS_MODE_OWNED_ONLY and not (
                normalize_domain_host(cfg.target_domain)
                or any(normalize_domain_host(item) for item in cfg.allowed_domains)
            ):
                error_text = "自社監査には自社URLか追加ドメインが必要です。"
                self.db.update_schedule_runtime(
                    schedule["schedule_id"],
                    last_scheduled_slot=slot_key,
                    last_run_at=now,
                    last_status="invalid_scope",
                    last_error=error_text,
                )
                self.db.update_schedule_dispatch(str(schedule["schedule_id"]), slot_key, status="invalid_scope", error_text=error_text)
                continue
            if not cfg.keywords:
                error_text = "質問セットにキーワードがありません。"
                self.db.update_schedule_runtime(
                    schedule["schedule_id"],
                    last_scheduled_slot=slot_key,
                    last_run_at=now,
                    last_status="empty_keywords",
                    last_error=error_text,
                )
                self.db.update_schedule_dispatch(str(schedule["schedule_id"]), slot_key, status="empty_keywords", error_text=error_text)
                continue
            if missing_required_fields:
                error_text = f"{', '.join(missing_required_fields)} が不足しているため定期実行を開始できませんでした。"
                self.db.update_schedule_runtime(
                    schedule["schedule_id"],
                    last_scheduled_slot=slot_key,
                    last_run_at=now,
                    last_status="missing_required_fields",
                    last_error=error_text,
                )
                self.db.update_schedule_dispatch(str(schedule["schedule_id"]), slot_key, status="missing_required_fields", error_text=error_text)
                continue
            if not scheduled_policy.allowed:
                error_text = scheduled_policy.blocked_reason or "定期実行は現在この接続先では使えません。"
                self.db.update_schedule_runtime(
                    schedule["schedule_id"],
                    last_scheduled_slot=slot_key,
                    last_run_at=now,
                    last_status="provider_unavailable",
                    last_error=error_text,
                )
                self.db.update_schedule_dispatch(str(schedule["schedule_id"]), slot_key, status="provider_unavailable", error_text=error_text)
                continue
            if not api_key_status.present:
                error_text = f"{api_key_status.env_var} が見つかりません。"
                self.db.update_schedule_runtime(
                    schedule["schedule_id"],
                    last_scheduled_slot=slot_key,
                    last_run_at=now,
                    last_status="missing_api_key",
                    last_error=error_text,
                )
                self.db.update_schedule_dispatch(str(schedule["schedule_id"]), slot_key, status="missing_api_key", error_text=error_text)
                continue
            if budget_guardrail["should_block"]:
                error_text = "日次上限を超える見込みのため定期実行の投入を止めました。質問数、回数、または上限設定を見直してください。"
                self.db.update_schedule_runtime(
                    schedule["schedule_id"],
                    last_scheduled_slot=slot_key,
                    last_run_at=now,
                    last_status="cost_blocked",
                    last_error=error_text,
                )
                self.db.update_schedule_dispatch(str(schedule["schedule_id"]), slot_key, status="cost_blocked", error_text=error_text)
                continue
            if run_guardrail > 0 and budget_guardrail["estimated_run_cost_usd"] > run_guardrail:
                error_text = (
                    f"見積 ${budget_guardrail['estimated_run_cost_usd']:.4f} が "
                    f"1 回の実行上限 ${run_guardrail:.2f} を超えるため投入を止めました。"
                )
                self.db.update_schedule_runtime(
                    schedule["schedule_id"],
                    last_scheduled_slot=slot_key,
                    last_run_at=now,
                    last_status="cost_blocked",
                    last_error=error_text,
                )
                self.db.update_schedule_dispatch(str(schedule["schedule_id"]), slot_key, status="cost_blocked", error_text=error_text)
                continue

            run_id = self.db.create_run_session(
                cfg.repeat_count,
                cfg.model,
                cfg.prompt_cache_key,
                run_mode="scheduled",
                config_json=json.dumps(cfg.model_dump(), ensure_ascii=False),
                question_set_id=str(question_set.get("question_set_id") or ""),
                question_set_name=str(question_set.get("name") or ""),
                schedule_id=str(schedule.get("schedule_id") or ""),
                scheduled_for=scheduled_for,
                batch_submitted_at=now,
            )
            try:
                query_plans = await prepare_query_plans_for_run(
                    self.db,
                    self.query_planner,
                    run_id,
                    cfg,
                    run_mode="scheduled",
                    scheduled_dispatch_at=scheduled_for,
                )
                self.db.update_schedule_dispatch(str(schedule["schedule_id"]), slot_key, status="run_created", run_id=run_id, error_text="")
                execution_plan: ExecutionPlan = build_execution_plan(query_plans, cfg)
                budget_guardrail = build_budget_guardrail(
                    recent_rows,
                    cfg,
                    planned_request_count=execution_plan.total_request_count,
                    batch_jobs=self.db.list_active_batch_job_reservations(limit=200),
                )
                if budget_guardrail["should_block"]:
                    error_text = "実際の送信件数で見積もると日次上限を超える見込みのため定期実行の投入を止めました。"
                    self.db.finish_run_session(run_id)
                    self.db.update_schedule_runtime(
                        schedule["schedule_id"],
                        last_scheduled_slot=slot_key,
                        last_run_at=now,
                        last_status="cost_blocked",
                        last_error=error_text,
                    )
                    self.db.update_schedule_dispatch(
                        str(schedule["schedule_id"]),
                        slot_key,
                        status="cost_blocked",
                        run_id=run_id,
                        error_text=error_text,
                    )
                    continue
                if run_guardrail > 0 and budget_guardrail["estimated_run_cost_usd"] > run_guardrail:
                    error_text = (
                        f"実際の送信件数での見積 ${budget_guardrail['estimated_run_cost_usd']:.4f} が "
                        f"1 回の実行上限 ${run_guardrail:.2f} を超えるため投入を止めました。"
                    )
                    self.db.finish_run_session(run_id)
                    self.db.update_schedule_runtime(
                        schedule["schedule_id"],
                        last_scheduled_slot=slot_key,
                        last_run_at=now,
                        last_status="cost_blocked",
                        last_error=error_text,
                    )
                    self.db.update_schedule_dispatch(
                        str(schedule["schedule_id"]),
                        slot_key,
                        status="cost_blocked",
                        run_id=run_id,
                        error_text=error_text,
                    )
                    continue
                batch_cfg = cfg.model_copy(
                    update={
                        "keywords": [request.executed_query for request in execution_plan.requests],
                        "repeat_count": 1,
                    }
                )
                request_contexts = [
                    {
                        "query_plan_id": request.query_plan_id,
                        "user_query_raw": request.user_query_raw,
                        "executed_query": request.executed_query,
                        "executed_query_index": request.executed_query_index,
                        "iteration_index": request.iteration_index,
                    }
                    for request in execution_plan.requests
                ]
                provider_client = build_provider_client(cfg.provider)
                batch_handle, request_items = await asyncio.to_thread(
                    provider_client.submit_batch,
                    batch_cfg,
                    request_contexts,
                )
                self.db.update_query_plans_batch_context(
                    run_id,
                    provider_batch_id=batch_handle.batch_job_id,
                    provider_batch_mode="provider_batch",
                )
                self.db.create_batch_job(
                    batch_job_id=batch_handle.batch_job_id,
                    run_id=run_id,
                    provider_key=cfg.provider,
                    status=batch_handle.status,
                    endpoint=batch_handle.endpoint,
                    completion_window=batch_handle.completion_window,
                    model_name=cfg.model,
                    repeat_count=cfg.repeat_count,
                    request_count=len(request_items),
                    input_file_id=batch_handle.input_file_id,
                    output_file_id=batch_handle.output_file_id,
                    error_file_id=batch_handle.error_file_id,
                    config_json=json.dumps(cfg.model_dump(), ensure_ascii=False),
                    metadata_json=json.dumps((batch_handle.raw_batch or {}).get("metadata") or {}, ensure_ascii=False),
                    reserved_cost_usd=budget_guardrail["estimated_run_cost_usd"],
                    request_counts_total=batch_handle.request_counts_total or len(request_items),
                    request_counts_completed=batch_handle.request_counts_completed,
                    request_counts_failed=batch_handle.request_counts_failed,
                    items=[
                        {
                            "custom_id": item.custom_id,
                            "keyword_raw": context["user_query_raw"],
                            "keyword_norm": normalize_text(context["user_query_raw"]),
                            "iteration_index": context["iteration_index"],
                            "query_plan_id": context["query_plan_id"],
                            "user_query_raw": context["user_query_raw"],
                            "executed_query": context["executed_query"],
                            "executed_query_index": context["executed_query_index"],
                            "request_body_json": json.dumps(item.request_line.get("body") or {}, ensure_ascii=False),
                        }
                        for item, context in zip(request_items, request_contexts, strict=False)
                    ],
                )
                self.db.update_schedule_dispatch(
                    str(schedule["schedule_id"]),
                    slot_key,
                    status="submitted",
                    run_id=run_id,
                    batch_job_id=batch_handle.batch_job_id,
                    error_text="",
                )
                self.db.touch_question_set_run(str(question_set.get("question_set_id") or ""), run_mode="scheduled", run_at=now)
                next_after_submission = compute_next_schedule_run(
                    weekdays,
                    int(schedule.get("weekly_run_count") or 0),
                    str(schedule.get("time_of_day") or "09:00"),
                    str(schedule.get("timezone") or "Asia/Tokyo"),
                    base_timestamp=scheduled_for + 60.0,
                )
                self.db.update_schedule_runtime(
                    schedule["schedule_id"],
                    next_run_at=next_after_submission or next_run_at,
                    last_scheduled_slot=slot_key,
                    last_run_at=now,
                    last_status="submitted",
                    last_error="",
                )
                self.last_message = (
                    f"定期バッチ実行を投入しました: {question_set.get('name')} / "
                    f"{len(request_items)} 件 / {batch_handle.batch_job_id}"
                )
            except Exception as exc:
                sanitized_error = sanitize_runtime_error_message(exc)
                self.db.finish_run_session(run_id)
                self.db.update_schedule_runtime(
                    schedule["schedule_id"],
                    last_scheduled_slot=slot_key,
                    last_run_at=now,
                    last_status="submit_error",
                    last_error=sanitized_error,
                )
                self.db.update_schedule_dispatch(
                    str(schedule["schedule_id"]),
                    slot_key,
                    status="submit_error",
                    run_id=run_id,
                    error_text=sanitized_error,
                )
                self.last_message = f"定期バッチ実行の投入に失敗しました: {sanitized_error}"

    async def _poll_scheduled_batches(self) -> None:
        batch_jobs = self.db.list_scheduled_batch_jobs_for_poll(limit=30)
        for batch_job in batch_jobs:
            batch_job_id = str(batch_job.get("batch_job_id") or "")
            if not batch_job_id:
                continue
            try:
                provider_client = build_provider_client(str(batch_job.get("provider_key") or "openai"))
                batch_handle = await asyncio.to_thread(provider_client.retrieve_batch, batch_job_id)
                error_messages = []
                raw_errors = ((batch_handle.raw_batch or {}).get("errors") or {}).get("data") or []
                for item in raw_errors:
                    if isinstance(item, dict) and item.get("message"):
                        error_messages.append(str(item["message"]))
                self.db.update_batch_job_status(
                    batch_job_id,
                    status=batch_handle.status,
                    output_file_id=batch_handle.output_file_id,
                    error_file_id=batch_handle.error_file_id,
                    request_counts_total=batch_handle.request_counts_total or int(batch_job.get("request_count") or 0),
                    request_counts_completed=batch_handle.request_counts_completed,
                    request_counts_failed=batch_handle.request_counts_failed,
                    last_error=" / ".join(error_messages[:2]),
                )
                if not batch_handle.output_file_id and not batch_handle.error_file_id:
                    continue

                cfg_snapshot = AppConfig.model_validate_json(batch_job["config_json"])
                item_rows = self.db.list_batch_job_items(batch_job_id)
                item_map = {row["custom_id"]: row for row in item_rows}
                import_records = await asyncio.to_thread(
                    provider_client.import_batch_results,
                    batch_handle,
                    cfg_snapshot,
                    item_map,
                )
                new_successes = 0
                new_errors = 0
                for record in import_records:
                    item_row = item_map.get(record.custom_id)
                    if not item_row or item_row.get("imported_result_id"):
                        continue
                    if record.result is not None:
                        record.result.estimated_cost_usd = estimate_cost_usd(
                            record.result.usage,
                            record.result.web_search_calls,
                            cfg_snapshot,
                        )
                        result_id = self.db.save_keyword_result(
                            run_id=batch_job["run_id"],
                            iteration_index=int(item_row["iteration_index"]),
                            result=record.result,
                            query_plan_id=str(item_row.get("query_plan_id") or ""),
                            display_query_raw=str(item_row.get("user_query_raw") or item_row["keyword_raw"]),
                            executed_query=str(item_row.get("executed_query") or item_row["keyword_raw"]),
                            executed_query_index=int(item_row.get("executed_query_index") or 1),
                        )
                        self.db.mark_batch_job_item_processed(
                            batch_job_id,
                            record.custom_id,
                            status="imported",
                            response_status_code=record.response_status_code,
                            remote_request_id=record.remote_request_id,
                            imported_result_id=result_id,
                        )
                        new_successes += 1
                        continue
                    error_result = build_error_result(
                        str(item_row.get("executed_query") or item_row["keyword_raw"]),
                        record.error_text,
                        cfg_snapshot,
                    )
                    safe_error = sanitize_runtime_error_message(record.error_text)
                    error_result.output_json["analysis_context"] = {
                        **(error_result.output_json.get("analysis_context") or {}),
                        "question": str(item_row.get("executed_query") or item_row["keyword_raw"]),
                        "user_query_raw": str(item_row.get("user_query_raw") or item_row["keyword_raw"]),
                        "executed_query": str(item_row.get("executed_query") or item_row["keyword_raw"]),
                    }
                    result_id = self.db.save_keyword_result(
                        run_id=batch_job["run_id"],
                        iteration_index=int(item_row["iteration_index"]),
                        result=error_result,
                        error_text=safe_error,
                        query_plan_id=str(item_row.get("query_plan_id") or ""),
                        display_query_raw=str(item_row.get("user_query_raw") or item_row["keyword_raw"]),
                        executed_query=str(item_row.get("executed_query") or item_row["keyword_raw"]),
                        executed_query_index=int(item_row.get("executed_query_index") or 1),
                    )
                    self.db.mark_batch_job_item_processed(
                        batch_job_id,
                        record.custom_id,
                        status="imported_error",
                        response_status_code=record.response_status_code,
                        remote_request_id=record.remote_request_id,
                        imported_result_id=result_id,
                        error_text=safe_error,
                    )
                    new_errors += 1

                final_items = self.db.list_batch_job_items(batch_job_id)
                imported_result_count = sum(1 for row in final_items if row.get("status") == "imported")
                imported_error_count = sum(1 for row in final_items if row.get("status") == "imported_error")
                self.db.mark_batch_job_imported(
                    batch_job_id,
                    imported_result_count=imported_result_count,
                    imported_error_count=imported_error_count,
                )
                if (
                    batch_handle.status in {"completed", "expired", "cancelled", "failed"}
                    and imported_result_count + imported_error_count >= int(batch_job.get("request_count") or 0)
                ):
                    self.db.finish_run_session(batch_job["run_id"])
                    self.db.touch_question_set_run(
                        str(batch_job.get("question_set_id") or ""),
                        run_mode="scheduled",
                        run_at=time.time(),
                    )
                    if batch_job.get("schedule_id"):
                        self.db.update_schedule_runtime(
                            str(batch_job["schedule_id"]),
                            last_run_at=time.time(),
                            last_status="imported",
                            last_error="",
                        )
                if new_successes or new_errors:
                    self.last_message = (
                        f"定期バッチ実行を取り込みました: {batch_job_id} / "
                        f"成功 {new_successes} 件 / エラー {new_errors} 件"
                    )
            except Exception as exc:
                sanitized_error = sanitize_runtime_error_message(exc)
                if batch_job.get("schedule_id"):
                    self.db.update_schedule_runtime(
                        str(batch_job["schedule_id"]),
                        last_status="poll_error",
                        last_error=sanitized_error,
                    )
                self.last_message = f"定期バッチ実行の状態確認に失敗しました: {sanitized_error}"
