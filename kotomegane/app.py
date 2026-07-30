from __future__ import annotations

import asyncio
import ipaddress
import json
import os
import time
from typing import Any, Callable

from fastapi import HTTPException
from fastapi.responses import FileResponse, Response
from nicegui import app as fastapi_app
from nicegui import background_tasks, context, ui

from analysis_lib import (
    build_budget_guardrail,
    build_cluster_brief_draft,
    build_query_rollup_rows,
    compute_next_schedule_run,
    estimate_cost_usd,
    format_timestamp,
    join_csv,
    normalize_text,
    normalize_schedule_weekdays,
    parse_weekdays_csv,
)
from config import (
    ANALYSIS_MODE_MARKET,
    ASSETS_DIR,
    AppConfig,
    DATA_DIR,
    EXPORTS_DIR,
    get_api_key_status,
    get_provider_option,
    load_config,
    save_config,
)
from export_file_writers import archive_legacy_export_files, validate_signed_export_path, write_export_files
from llmo_client import build_provider_client
from llmo_core.models import build_batch_item_custom_id
from query_planning import ExecutionPlan, QueryPlanner, build_execution_plan
from run_planning import prepare_query_plans_for_run
from run_policy import resolve_run_policy, should_allow_batch_import
from runtime import common as runtime_common
from runtime_mode import READONLY_DEMO_ENV_VAR, is_readonly_demo_mode, readonly_demo_block_message
from scheduler_runtime import ScheduledMonitorService
from shared.auth.nicegui_auth import NiceGUIAuthMiddleware
from shared.usage.api import router as usage_router
from shared.usage.nicegui import consume_usage_for_current_user, get_usage_summary_for_current_user
from storage import Storage
from ui import admin_views, charts, dashboard_refreshers, dashboard_views, detail_views, page_refreshers, styles
from ui.cluster_brief_builders import build_cluster_brief_save_payload, resolve_cluster_brief_candidate
from ui.input_config_builders import (
    build_config_from_inputs,
    build_manual_runtime_config,
    notify_missing_required_fields,
)
from ui.market_context_helpers import (
    classify_market_context_terms,
    infer_market_context_candidates,
    market_context_category_label,
    merge_market_context_terms,
    split_market_context_terms,
)
from ui.provider_runtime_controls import (
    get_visible_provider_catalog,
    normalize_provider_config,
    refresh_provider_controls,
    refresh_runtime_panels,
    select_provider_config,
)
from ui.runtime_copy_builders import (
    build_onboarding_markdown,
    build_runtime_markdown,
    build_scope_markdown,
    provider_display_label,
)

SUITE_ACCENT_BUTTON_STYLE = (
    "background: linear-gradient(135deg, #D96B1F 0%, #B95416 100%); "
    "color: #FFFFFF; border: 1px solid #B95416; "
    "box-shadow: 0 10px 22px rgba(217, 107, 31, 0.18);"
)
SUITE_SECONDARY_BUTTON_STYLE = (
    "background: rgba(255, 251, 246, 0.96); "
    "color: #7A3A16; border: 1px solid rgba(122, 98, 83, 0.18);"
)
LEGACY_FLUTTER_SERVICE_WORKER_CLEANUP = """
self.addEventListener('install', (event) => {
  self.skipWaiting();
});
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    try {
      const cacheKeys = await caches.keys();
      await Promise.all(cacheKeys.map((key) => caches.delete(key)));
    } catch (_) {
    }
    await self.registration.unregister();
    const clientsList = await self.clients.matchAll({type: 'window', includeUncontrolled: true});
    for (const client of clientsList) {
      client.navigate(client.url);
    }
  })());
});
self.addEventListener('fetch', () => {});
""".strip()

READONLY_DEMO_MODE = is_readonly_demo_mode()

db = Storage()
scheduler_service = ScheduledMonitorService(db, readonly_demo=READONLY_DEMO_MODE)
query_planner = QueryPlanner()
fastapi_app.include_router(usage_router)
fastapi_app.add_middleware(NiceGUIAuthMiddleware)

HUB_URL = os.environ.get("HUB_URL") or os.environ.get("HUB_BASE_URL") or "https://app.techie.jp"
KOTOMAKE_URL = os.environ.get("KOTOMAKE_URL", "https://kotomake.ashymushroom-021a53c5.japanwest.azurecontainerapps.io")
KOTOMIGAKI_URL = os.environ.get("KOTOMIGAKI_URL", "https://kotomigaki.ashymushroom-021a53c5.japanwest.azurecontainerapps.io")

LOOPBACK_UI_HOSTS = frozenset({"localhost"})


def _is_loopback_ui_host(raw_host: str) -> bool:
    host = str(raw_host or "").strip().lower()
    if not host:
        return False
    if host in LOOPBACK_UI_HOSTS:
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def _load_budget_guardrail(config: AppConfig, *, planned_request_count: int | None = None) -> dict[str, Any]:
    return build_budget_guardrail(
        db.list_recent_results(limit=500),
        config,
        planned_request_count=planned_request_count,
        batch_jobs=db.list_active_batch_job_reservations(limit=200),
    )


async def _ensure_usage_credit_available(service_key: str, *, units: int = 1) -> bool:
    try:
        summary = await get_usage_summary_for_current_user(service_key=service_key)
    except Exception as exc:
        print(f"[usage] credit check failed service_key={service_key}: {exc}", flush=True)
        ui.notify("クレジット確認に失敗しました。時間をおいて再度お試しください。", color="negative")
        return False
    if int(summary.get("remaining_credits") or 0) < units:
        ui.notify("クレジットが不足しています。契約管理画面で残高をご確認ください。", color="warning")
        return False
    return True


async def _consume_usage_credit_after_success(
    *,
    service_key: str,
    action_key: str,
    attempt_id: str,
    units: int = 1,
    metadata: dict[str, Any] | None = None,
) -> bool:
    try:
        summary = await consume_usage_for_current_user(
            service_key=service_key,
            action_key=action_key,
            units=units,
            idempotency_key=f"{service_key}:{action_key}:{attempt_id}",
            metadata={"trigger": "post_success", **(metadata or {})},
        )
        print(
            "[usage] credit debited "
            f"service_key={service_key} action_key={action_key} units={units} "
            f"event_id={summary.get('usage_event_id')} "
            f"remaining={summary.get('remaining_credits')} "
            f"replay={summary.get('idempotent_replay')}",
            flush=True,
        )
        return True
    except Exception as exc:
        print(f"[usage] credit debit failed service_key={service_key} action_key={action_key}: {exc}", flush=True)
        ui.notify("処理は完了しましたが、クレジット消費の記録に失敗しました。管理者へ連絡してください。", color="negative")
        return False


def _kotomegane_credit_units(provider_key: str) -> int:
    # Client rule: OpenAI single observation = 1 credit, Gemini/Claude or cross-provider observation = 2 credits.
    return 1 if str(provider_key or "").strip().lower() == "openai" else 2


def _validate_startup_host_or_raise(raw_host: str) -> None:
    if _is_loopback_ui_host(raw_host):
        return
    auth_required = str(os.environ.get("AUTH_ENFORCE_SERVICES") or "").strip().lower() in {"1", "true", "yes", "on"}
    environment_name = str(
        os.environ.get("ENVIRONMENT") or os.environ.get("CONTAINER_ENV") or ""
    ).strip().lower()
    if auth_required and environment_name in {"prod", "production", "staging"}:
        return
    raise RuntimeError(
        (
            f"ui_host が '{raw_host}' に設定されています。"
            " このアプリは認証なし公開を許可しないため、loopback 以外では起動できません。"
            " 127.0.0.1 / ::1 / localhost のいずれかに変更してください。"
        )
    )


class RunGuardrailBlockedError(RuntimeError):
    pass


archive_legacy_export_files(EXPORTS_DIR, DATA_DIR / "legacy_export_archive")

if ASSETS_DIR.exists():
    fastapi_app.add_static_files("/branding", str(ASSETS_DIR))


@fastapi_app.get("/exports/{bundle_id}/{filename}")
def download_export_file(bundle_id: str, filename: str, expires: str = "", token: str = "") -> FileResponse:
    path = validate_signed_export_path(
        EXPORTS_DIR,
        bundle_id,
        filename,
        expires=expires,
        token=token,
    )
    if path is None:
        raise HTTPException(status_code=403, detail="export link is invalid or expired")
    return FileResponse(path=str(path), filename=filename)


async def _run_startup_result_enrichment_maintenance() -> None:
    try:
        await asyncio.to_thread(db.run_result_enrichment_maintenance, 250)
    except Exception as exc:
        print(f"[kotomegane] result enrichment maintenance failed: {exc}")


def _start_background_services() -> None:
    if READONLY_DEMO_MODE:
        print(
            f"[kotomegane] read-only/demo mode active: {READONLY_DEMO_ENV_VAR}=1. "
            "startup scheduler and result enrichment maintenance skipped.",
            flush=True,
        )
        return
    scheduler_service.start()
    background_tasks.create(
        _run_startup_result_enrichment_maintenance(),
        name="kotomegane result enrichment maintenance",
    )


fastapi_app.on_startup(_start_background_services)
fastapi_app.on_shutdown(scheduler_service.stop)


@fastapi_app.get("/healthz")
@fastapi_app.get("/health")
def healthcheck() -> Response:
    return Response(
        content='{"status":"ok","service":"kotomegane"}',
        media_type="application/json",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-store, max-age=0",
        },
    )


@fastapi_app.get("/flutter_service_worker.js")
def legacy_flutter_service_worker() -> Response:
    return Response(
        content=LEGACY_FLUTTER_SERVICE_WORKER_CLEANUP,
        media_type="application/javascript",
        headers={"Cache-Control": "no-store, max-age=0"},
    )

TABLE_BASE_PROPS = 'flat wrap-cells rows-per-page-label="表示件数" no-data-label="データなし"'


def load_runtime_config_state() -> AppConfig:
    updates: dict[str, Any] = {"analysis_mode": ANALYSIS_MODE_MARKET, "repeat_count": 20}
    env_port = str(os.getenv("PORT") or os.getenv("KOTOMEGANE_PORT") or "").strip()
    if env_port:
        try:
            updates["ui_port"] = int(env_port)
        except ValueError:
            print(f"[kotomegane] ignored invalid PORT={env_port!r}", flush=True)
    env_host = str(os.getenv("HOST") or os.getenv("KOTOMEGANE_HOST") or "").strip()
    if env_host:
        updates["ui_host"] = env_host
    return load_config().model_copy(update=updates)


def render_page() -> None:
    styles.add_global_style()
    ui.add_head_html(
        """
        <script>
        const shouldSuppressPlotlyResizeError = (value) => {
          const message = String(value?.message || value || '');
          return message.includes('Resize must be passed a displayed plot div element');
        };
        window.addEventListener('error', (event) => {
          if (shouldSuppressPlotlyResizeError(event?.message || event?.error)) {
            event.preventDefault();
            event.stopImmediatePropagation();
            return true;
          }
        }, true);
        window.addEventListener('unhandledrejection', (event) => {
          if (shouldSuppressPlotlyResizeError(event?.reason)) {
            event.preventDefault();
            event.stopImmediatePropagation();
          }
        }, true);
        window.addEventListener('click', (event) => {
          const shortcut = event.target?.closest?.('[data-km-shortcut-target]');
          if (!shortcut) return;
          const targetId = shortcut.getAttribute('data-km-shortcut-target');
          if (!targetId) return;
          const scrollTarget = () => {
            document.getElementById(targetId)?.scrollIntoView({behavior: 'smooth', block: 'start'});
          };
          setTimeout(scrollTarget, 650);
          setTimeout(scrollTarget, 1150);
        }, true);
        (async () => {
          if (!('serviceWorker' in navigator)) return;
          try {
            const registrations = await navigator.serviceWorker.getRegistrations();
            await Promise.all(registrations.map((registration) => registration.unregister()));
            if ('caches' in window) {
              const cacheKeys = await caches.keys();
              await Promise.all(cacheKeys.map((key) => caches.delete(key)));
            }
          } catch (error) {
            console.warn('service worker cleanup failed', error);
          }
        })();
        </script>
        """
    )
    initial_config = normalize_provider_config(load_runtime_config_state())
    state = {
        "config": initial_config,
        "busy": False,
        "batch_busy": False,
        "cancel_requested": False,
        "export_rows": [],
        "report_preview": "",
        "show_primary_results": False,
        "current_result_run_id": "",
    }
    periodic_refresh_signature: tuple[Any, ...] = ()
    latest_dashboard_payload: dict[str, Any] | None = None
    analysis_plots_mounted = False
    question_set_admin_refreshed = False
    batch_admin_refreshed = False
    schedule_admin_refreshed = False
    export_panel_refreshed = False
    inputs: dict[str, Any] = {}

    class WeekdayCheckboxGroup:
        def __init__(self) -> None:
            self.checkboxes: dict[str, Any] = {}

        @property
        def value(self) -> list[str]:
            return [key for key, control in self.checkboxes.items() if bool(control.value)]

        @value.setter
        def value(self, weekdays: list[Any]) -> None:
            selected = {str(day) for day in weekdays}
            for key, control in self.checkboxes.items():
                control.value = key in selected

        def add(self, key: str, control: Any) -> None:
            self.checkboxes[key] = control

        def update(self) -> None:
            for control in self.checkboxes.values():
                control.update()

    schedule_manage_select: ui.select | None = None
    compare_mode_select: ui.select | None = None
    compare_target_select: ui.select | None = None
    schedule_diff_container: ui.column | None = None
    schedule_delete_dialog: ui.dialog | None = None
    cluster_kind_select: ui.select | None = None
    cluster_target_select: ui.select | None = None
    saved_cluster_brief_select: ui.select | None = None
    cluster_brief_table: ui.table | None = None
    cluster_brief_container: ui.column | None = None
    outcome_scope_kind_select: ui.select | None = None
    outcome_scope_target_select: ui.select | None = None
    outcome_run_a_select: ui.select | None = None
    outcome_run_b_select: ui.select | None = None
    outcome_compare_container: ui.column | None = None
    runtime_micro_label: ui.label | None = None
    cost_policy_label: ui.label | None = None
    batch_job_select: ui.select | None = None
    batch_job_table: ui.table | None = None
    batch_status_label: ui.label | None = None
    batch_summary_label: ui.label | None = None
    support_tabs: Any | None = None
    support_result_expansion: Any | None = None
    support_result_tab: Any | None = None
    support_analysis_tab: Any | None = None
    support_research_tab: Any | None = None
    support_settings_tab: Any | None = None
    batch_settings_expansion: Any | None = None
    schedule_settings_expansion: Any | None = None
    provider_buttons: dict[str, ui.button] = {}
    keyword_inputs: list[Any] = []
    keyword_rows: list[Any] = []
    hero_status_refs: dict[str, ui.label] = {}
    hero_trend_refs: dict[str, Any] = {}
    market_context_candidate_container: ui.column | None = None
    question_heatmap_plot: Any | None = None
    query_drilldown_plot: Any | None = None
    intent_trend_plot: Any | None = None
    page_gap_trend_plot: Any | None = None
    analysis_visibility_plot_container: ui.column | None = None
    analysis_history_focus_plot_container: ui.column | None = None
    question_heatmap_plot_container: ui.column | None = None
    query_drilldown_plot_container: ui.column | None = None
    intent_trend_plot_container: ui.column | None = None
    page_gap_trend_plot_container: ui.column | None = None

    def is_deleted_ui_runtime_error(exc: Exception) -> bool:
        return "has been deleted" in str(exc)

    def safely_run_ui(action: Callable[[], None]) -> bool:
        try:
            action()
        except RuntimeError as exc:
            if is_deleted_ui_runtime_error(exc):
                return False
            raise
        return True

    def readonly_demo_ui_block_message(action: str) -> str:
        return f"確認用モードのため{action}できません。"

    def block_readonly_demo_ui_action(action: str) -> bool:
        if not READONLY_DEMO_MODE:
            return False
        message = readonly_demo_ui_block_message(action)
        ui.notify(message, color="warning")
        print(f"[kotomegane] {message}", flush=True)
        return True

    def readonly_button_classes(base_classes: str) -> str:
        return f"{base_classes} readonly-disabled-action" if READONLY_DEMO_MODE else base_classes

    def readonly_button_style(base_style: str) -> str:
        if not READONLY_DEMO_MODE:
            return base_style
        return (
            f"{base_style};"
            "background:#E7E0D8 !important;"
            "border-color:rgba(116,102,88,0.28) !important;"
            "color:#75695F !important;"
            "box-shadow:none !important;"
            "filter:saturate(0.24) grayscale(0.18) !important;"
            "opacity:1 !important;"
            "cursor:not-allowed !important;"
        )

    def build_dashboard_payload(current_run_id: str = "") -> dict[str, Any]:
        return dashboard_views.build_dashboard_refresh_payload(
            db,
            state["config"],
            db.list_sources,
            current_run_id=current_run_id or str(state["current_result_run_id"] or ""),
        )

    def build_periodic_refresh_signature(payload: dict[str, Any] | None = None) -> tuple[Any, ...]:
        effective_payload = payload or build_dashboard_payload()
        return tuple(effective_payload.get("refresh_signature") or ())

    def run_preserving_scroll(action: Callable[[], None]) -> None:
        ui.run_javascript(
            """
            window.__kotomeganeRefreshScroll = {
              x: window.scrollX || document.documentElement.scrollLeft || 0,
              y: window.scrollY || document.documentElement.scrollTop || 0,
            };
            """
        )
        action()
        ui.run_javascript(
            """
            requestAnimationFrame(() => {
              requestAnimationFrame(() => {
                const saved = window.__kotomeganeRefreshScroll;
                if (!saved) return;
                window.scrollTo(saved.x || 0, saved.y || 0);
              });
            });
            """
        )

    def refresh_runtime_panels_if_visible() -> None:
        if runtime_micro_label is not None and cost_policy_label is not None:
            refresh_runtime_panels(state["config"], runtime_micro_label, cost_policy_label)

    def open_support_surface(target_tab: Any | None = None, target_section: str = "") -> None:
        if support_result_expansion is not None:
            support_result_expansion.value = True
            support_result_expansion.update()
        if support_tabs is not None and target_tab is not None:
            support_tabs.value = target_tab
            support_tabs.update()
        try:
            ensure_support_target_ready(target_tab, target_section)
        except NameError:
            pass
        if target_section == "batch" and batch_settings_expansion is not None:
            batch_settings_expansion.value = True
            batch_settings_expansion.update()
        if target_section == "schedule" and schedule_settings_expansion is not None:
            schedule_settings_expansion.value = True
            schedule_settings_expansion.update()
        if target_tab is not None and target_tab == support_analysis_tab:
            mount_analysis_plots()
        target_id = {
            "saved": "saved-condition-section",
            "batch": "batch-settings-section",
            "schedule": "schedule-settings-section",
        }.get(target_section, "detail-stage")
        ui.run_javascript(
            f"""
            const scrollKotomeganeTarget = () => {{
              document.getElementById({json.dumps(target_id)})?.scrollIntoView({{behavior: 'smooth', block: 'start'}});
            }};
            requestAnimationFrame(() => {{
              requestAnimationFrame(() => {{
                scrollKotomeganeTarget();
              }});
            }});
            setTimeout(scrollKotomeganeTarget, 160);
            setTimeout(scrollKotomeganeTarget, 420);
            """
        )

    def scroll_to_support_section(target_id: str) -> None:
        ui.run_javascript(
            f"""
            window.__kotomeganeLastShortcutTarget = {json.dumps(target_id)};
            var scrollKotomeganeSupportTarget = () => {{
              document.getElementById({json.dumps(target_id)})?.scrollIntoView({{behavior: 'smooth', block: 'start'}});
            }};
            requestAnimationFrame(() => {{
              requestAnimationFrame(() => {{
                scrollKotomeganeSupportTarget();
              }});
            }});
            setTimeout(scrollKotomeganeSupportTarget, 180);
            setTimeout(scrollKotomeganeSupportTarget, 520);
            """
        )

    def expand_current_result_surface() -> None:
        if support_result_expansion is not None:
            support_result_expansion.value = True
            support_result_expansion.update()
        if support_tabs is not None and support_result_tab is not None:
            support_tabs.value = support_result_tab
            support_tabs.update()

    def refresh_hero_status(payload: dict[str, Any] | None = None) -> None:
        if not hero_status_refs:
            return
        effective_payload = payload or build_dashboard_payload()
        scoped_rows = list(effective_payload.get("recent_rows") or [])
        latest_row = scoped_rows[0] if scoped_rows else None
        hero_status_refs["provider"].text = provider_display_label(get_provider_option(state["config"].provider))
        hero_status_refs["updated"].text = format_timestamp(latest_row.get("analyzed_at")) if latest_row else "まだありません"
        hero_status_refs["provider"].update()
        hero_status_refs["updated"].update()
        delta_ref = hero_status_refs.get("delta")
        if delta_ref is not None:
            try:
                from analysis_core.trends import build_previous_delta_summary

                if len(scoped_rows) >= 2:
                    current_row = scoped_rows[0]
                    previous_row = scoped_rows[1]
                    delta_summary = build_previous_delta_summary([current_row], [previous_row])
                    delta_value = float(delta_summary.get("target_hit_rate_delta") or 0.0)
                    delta_ref.text = f"{delta_value:+.1f}pt"
                else:
                    delta_ref.text = "まだありません"
            except Exception:
                delta_ref.text = "まだありません"
            delta_ref.update()

        if hero_trend_refs:
            try:
                tracked_rows = dashboard_views.filter_rows_for_tracking_series(scoped_rows)
                plot_ref = hero_trend_refs.get("plot")
                if plot_ref is not None:
                    plot_ref.figure = charts.build_visibility_focus_chart(tracked_rows, state["config"])
                    plot_ref.update()
                latest_rate_ref = hero_trend_refs.get("latest_rate")
                hint_ref = hero_trend_refs.get("hint")
                if tracked_rows:
                    first_row = tracked_rows[0]
                    rate = first_row.get("owned_citation_trial_rate")
                    if rate is None:
                        rate = first_row.get("target_hit_rate")
                    if latest_rate_ref is not None:
                        latest_rate_ref.text = (
                            f"{float(rate):.1f}%" if rate is not None else "--"
                        )
                        latest_rate_ref.update()
                    if hint_ref is not None:
                        hint_ref.text = (
                            f"直近の自動チェック {len(tracked_rows)} 件を表示しています。"
                        )
                        hint_ref.update()
                else:
                    if latest_rate_ref is not None:
                        latest_rate_ref.text = "--"
                        latest_rate_ref.update()
                    if hint_ref is not None:
                        hint_ref.text = "まだ自動チェックの履歴がありません。"
                        hint_ref.update()
            except Exception:
                pass

    def refresh_provider_ui(*, update_hero: bool = True) -> None:
        nonlocal state
        next_config = refresh_provider_controls(
            state["config"],
            provider_buttons,
        )
        state["config"] = next_config
        refresh_runtime_panels_if_visible()
        if update_hero:
            refresh_hero_status()

    def set_provider(provider_key: str) -> None:
        state["config"] = select_provider_config(state["config"], provider_key)
        refresh_provider_ui()
        refresh_runtime_panels_if_visible()
        mark_results_stale("対象AIを変えたため、前回の「今回の結果」は隠しています。もう一度分析してください。")

    drawer_nav_actions: dict[str, Any] = {}
    styles.render_dashboard_drawer(drawer_nav_actions)
    styles.render_top_nav()

    with ui.column().classes("w-full max-w-7xl mx-auto px-5 pb-12 gap-8"):
        if READONLY_DEMO_MODE:
            with ui.card().classes("w-full px-4 py-3 mt-4").style(
                "background:#FFF7E8;border:1px solid rgba(217,107,31,0.38);box-shadow:none;"
            ):
                with ui.row().classes("w-full items-start gap-3 flex-wrap"):
                    ui.icon("visibility").classes("text-[20px] text-orange-8 mt-1")
                    with ui.column().classes("gap-1 flex-1 min-w-[260px]"):
                        ui.label("確認用モード（保存・送信は行われません）").classes("summary-eyebrow")
                        ui.label(
                            "今は画面の確認だけができるモードです。AIへの質問送信や、内容の保存・更新は行われません。"
                        ).classes("text-[14px] leading-6 text-main")
        with ui.card().classes("hero-card w-full px-5 py-4 mt-4"):
            with ui.row().classes("w-full items-start justify-between gap-4 flex-wrap"):
                with ui.column().classes("hero-copy-card gap-2 justify-center flex-1 min-w-[320px]"):
                    ui.label("TECHIE").classes("summary-eyebrow")
                    with ui.row().classes("items-center gap-3 flex-wrap"):
                        ui.image("/branding/logo_mark_icon.png").classes("hero-logo-mark").style(
                            "width:44px;height:44px;flex-shrink:0;"
                        )
                        with ui.column().classes("gap-0"):
                            ui.html('<h1 class="brand-font hero-service-name">コトメガネ</h1>', sanitize=False)
                            ui.label("LLM見え方観測").classes("section-font text-[14px] font-bold text-support tracking-wide")
                    ui.label(
                        "AIが誰を引用し、何を根拠にしたかを観測します。"
                    ).classes("hero-summary text-wrap-anywhere mt-2")
                    with ui.row().classes("gap-2 flex-wrap mt-2"):
                        ui.link("サイト改善へ (コトミガキ)", KOTOMIGAKI_URL, new_tab=True).classes(
                            "hero-context-link text-[13px]"
                        )
                        ui.link("発信作成へ (コトメイク)", KOTOMAKE_URL, new_tab=True).classes(
                            "hero-context-link text-[13px]"
                        )
                with ui.row().classes("gap-3 flex-wrap items-start w-full mt-4"):
                    with ui.column().classes("input-field-card hero-status-card gap-1 min-w-[180px] flex-1"):
                        ui.label("対象AI").classes("ui-tone-chip")
                        hero_status_refs["provider"] = ui.label(provider_display_label(get_provider_option(state["config"].provider))).classes(
                            "section-font text-[18px] font-bold hero-status-value mt-2 text-wrap-anywhere"
                        )
                    with ui.column().classes("input-field-card hero-status-card gap-1 min-w-[180px] flex-1"):
                        ui.label("最後に結果を保存").classes("ui-tone-chip")
                        hero_status_refs["updated"] = ui.label("まだありません").classes(
                            "section-font text-[18px] font-bold hero-status-value mt-2 text-wrap-anywhere"
                        )
                    with ui.column().classes("input-field-card hero-status-card gap-1 min-w-[180px] flex-1"):
                        ui.label("前回の自動チェックとの差").classes("ui-tone-chip")
                        hero_status_refs["delta"] = ui.label("まだありません").classes(
                            "section-font text-[18px] font-bold hero-status-value mt-2 text-wrap-anywhere"
                        )

        metric_refs: dict[str, tuple[ui.label, ui.label]] = {}
        summary_refs: dict[str, Any] = {"kpis": {}, "plots": {}}
        decision_refs: dict[str, dict[str, Any]] = {"intent": {}, "gap": {}, "budget": {}}

        with ui.card().classes("section-card input-shell p-6 w-full").props("id=input-stage"):
                initial_keywords = list(state["config"].keywords[:3]) or [""]
                visible_keyword_count = 1
                current_input_boundary_label: ui.label | None = None

                def refresh_current_input_boundary_note() -> None:
                    if current_input_boundary_label is None:
                        return
                    active_rows = max(1, visible_keyword_count)
                    if active_rows > 1:
                        current_input_boundary_label.text = (
                            f"現在{active_rows}件の質問を使って分析します（最大3件）。保存済み条件にすると再利用できます。"
                        )
                    else:
                        current_input_boundary_label.text = (
                            "主質問と自社URLだけで始められます。質問追加や比較対象は詳細条件にあります。"
                        )
                    current_input_boundary_label.update()

                def refresh_keyword_input_visibility() -> None:
                    active_rows = 0
                    for index, row in enumerate(keyword_rows):
                        should_show = index < visible_keyword_count
                        row.set_visibility(should_show)
                        if should_show:
                            active_rows += 1
                    add_keyword_button.visible = active_rows < 3
                    remove_keyword_button.visible = active_rows > 1
                    try:
                        summary_label.text = (
                            f"この{active_rows}質問を今回だけ分析します。対象AIへ送信するのは下の「1回だけ分析」を押したときです。"
                            if active_rows > 1
                            else "主質問と自社URLを入れると、AI検索で自社が表示されるかを、合計20回答を目安に確認します。"
                        )
                        summary_label.update()
                    except NameError:
                        pass
                    refresh_current_input_boundary_note()

                def add_keyword_input() -> None:
                    nonlocal visible_keyword_count
                    visible_keyword_count = min(3, visible_keyword_count + 1)
                    refresh_keyword_input_visibility()
                    refresh_market_context_candidates()
                    mark_results_stale("質問を追加したため、前回の「今回の結果」は隠しています。もう一度分析してください。")

                def remove_keyword_input() -> None:
                    nonlocal visible_keyword_count
                    if visible_keyword_count <= 1:
                        return
                    visible_keyword_count -= 1
                    keyword_inputs[visible_keyword_count].value = ""
                    keyword_inputs[visible_keyword_count].update()
                    refresh_keyword_input_visibility()
                    refresh_market_context_candidates()
                    mark_results_stale("質問を変更したため、前回の「今回の結果」は隠しています。もう一度分析してください。")

                def get_active_keywords() -> list[str]:
                    return [
                        str(control.value or "").strip()
                        for control in keyword_inputs[:visible_keyword_count]
                        if str(control.value or "").strip()
                    ]

                def apply_market_context_terms(*terms: str) -> None:
                    existing_terms = split_market_context_terms(inputs["market_context"].value if "market_context" in inputs else "")
                    next_terms = merge_market_context_terms(existing_terms, [str(term or "").strip() for term in terms if str(term or "").strip()])
                    inputs["market_context"].value = ", ".join(next_terms)
                    inputs["market_context"].update()
                    refresh_market_context_candidates()
                    mark_results_stale("重点テーマを更新したため、前回の「今回の結果」は隠しています。もう一度分析してください。")

                def refresh_market_context_candidates() -> None:
                    if market_context_candidate_container is None or "market_context" not in inputs:
                        return
                    current_terms = classify_market_context_terms(split_market_context_terms(inputs["market_context"].value))
                    inferred_terms = infer_market_context_candidates(get_active_keywords())
                    market_context_candidate_container.clear()
                    with market_context_candidate_container:
                        if not any(current_terms.values()) and not any(inferred_terms.values()):
                            return
                        if any(current_terms.values()):
                            with ui.column().classes("w-full gap-2"):
                                ui.label("いまの重点テーマ").classes("summary-eyebrow")
                                for category in ("region", "industry", "use_case", "other"):
                                    values = current_terms.get(category) or []
                                    if not values:
                                        continue
                                    with ui.row().classes("w-full gap-2 flex-wrap items-center"):
                                        ui.label(market_context_category_label(category)).classes("text-[12px] tracking-[0.18em] soft-label")
                                        for value in values:
                                            ui.label(value).classes("signal-chip signal-positive")
                        if any(inferred_terms.values()):
                            with ui.column().classes("w-full gap-2 mt-3"):
                                ui.label("質問から見つけた候補").classes("summary-eyebrow")
                                for category in ("region", "industry", "use_case"):
                                    values = inferred_terms.get(category) or []
                                    if not values:
                                        continue
                                    with ui.row().classes("market-context-candidate-row w-full gap-2 flex-wrap items-center"):
                                        ui.label(market_context_category_label(category)).classes("market-context-category-label text-[12px] tracking-[0.18em] soft-label")
                                        for value in values:
                                            ui.button(
                                                f"重点テーマに「{value}」を追加",
                                                on_click=lambda _=None, selected=value: apply_market_context_terms(selected),
                                            ).props("outline color=brown-8").classes("market-context-candidate-button secondary-button text-[13px]").style(SUITE_SECONDARY_BUTTON_STYLE)
                                    if len(values) > 1:
                                        ui.button(
                                            "重点テーマ候補をまとめて追加",
                                            on_click=lambda _=None, selected=list(values): apply_market_context_terms(*selected),
                                        ).props("outline color=brown-8").classes("market-context-candidate-button secondary-button text-[13px] mt-1").style(SUITE_SECONDARY_BUTTON_STYLE)

                with ui.row().classes("w-full items-start justify-between gap-3 flex-wrap mb-2"):
                    with ui.column().classes("gap-1"):
                        ui.label("QUICK SETUP").classes("summary-eyebrow")
                        ui.label("市場観測を作る").classes("section-font section-title text-[22px] font-bold")
                    current_input_boundary_label = ui.label(
                        "主質問と自社URLだけで始められます。質問追加や比較対象は詳細条件にあります。"
                    ).classes("text-[13px] leading-6 text-helper max-w-[560px]")

                with ui.row().classes("input-main-grid w-full gap-5 mt-3 flex-wrap items-start"):
                    with ui.column().classes("input-main-column flex-[1.15] min-w-[440px] gap-4"):
                        with ui.column().classes("input-field-card gap-3 w-full"):
                            with ui.row().classes("w-full items-start gap-3 flex-wrap"):
                                ui.label("1").classes("workflow-step-pill workflow-step-pill-active")
                                with ui.column().classes("gap-1 flex-1 min-w-[260px]"):
                                    ui.label("何を観測するか").classes("section-font text-[20px] font-bold text-main")
                                    ui.label("AI検索で見え方を確認したい質問を1つ入れます。").classes("text-[13px] leading-5 text-helper")
                            default_value = initial_keywords[0] if initial_keywords else ""
                            row = ui.row().classes("w-full gap-3 mt-1 items-start")
                            with row:
                                ui.label("1.").classes("metric-font text-[18px] font-bold text-brand mt-3 w-[20px]")
                                keyword_input = ui.input(
                                    "観測したい質問 *",
                                    value=default_value,
                                    placeholder="例: 東京の製造業でAI検索に見える会社を知りたい",
                                ).props("outlined").classes("flex-1 min-w-[280px]")
                            keyword_rows.append(row)
                            keyword_inputs.append(keyword_input)
                            with ui.expansion("詳細条件").classes("w-full mt-1 panel-card"):
                                with ui.column().classes("p-4 gap-3 w-full"):
                                    ui.label("質問を増やす（最大3件まで） / 観測条件を絞る").classes("summary-eyebrow")
                                    for index in range(1, 3):
                                        default_value = initial_keywords[index] if index < len(initial_keywords) else ""
                                        detail_row = ui.row().classes("w-full gap-3 items-start")
                                        with detail_row:
                                            ui.label(f"{index + 1}.").classes("metric-font text-[18px] font-bold text-brand mt-3 w-[20px]")
                                            keyword_input = ui.input(
                                                f"追加質問 {index + 1} (任意)",
                                                value=default_value,
                                                placeholder="例: 比較したい地域や業界を変えた質問",
                                            ).props("outlined").classes("flex-1 min-w-[260px]")
                                        keyword_rows.append(detail_row)
                                        keyword_inputs.append(keyword_input)
                                    with ui.row().classes("w-full gap-3 flex-wrap"):
                                        add_keyword_button = ui.button("追加質問を表示", on_click=add_keyword_input).props("outline color=brown-8").classes(
                                            "secondary-button text-[15px]"
                                        ).style(SUITE_SECONDARY_BUTTON_STYLE)
                                        remove_keyword_button = ui.button("追加質問を1件減らす", on_click=remove_keyword_input).props("outline color=brown-8").classes(
                                            "secondary-button text-[15px]"
                                        ).style(SUITE_SECONDARY_BUTTON_STYLE)
                                    inputs["market_context"] = ui.input(
                                        "重点テーマ (任意)",
                                        value=join_csv(state["config"].market_context_terms),
                                        placeholder="例: 東京, 製造業, 導入事例",
                                    ).props("outlined").classes("w-full")
                                    ui.label("業界・用途・地域を絞りたいときだけ使います。").classes("text-[12px] leading-5 text-helper")
                                    market_context_candidate_container = ui.column().classes("w-full gap-2")
                                    inputs["competitor_terms"] = ui.input(
                                        "比較対象 (任意)",
                                        value=join_csv(state["config"].competitor_terms),
                                        placeholder="例: 比較したい会社名, サービス名",
                                    ).props("outlined").classes("w-full")
                                    with ui.expansion("入力例を見る").classes("w-full mt-1 panel-card"):
                                        with ui.column().classes("p-4 gap-2 w-full"):
                                            ui.label("入力例").classes("summary-eyebrow")
                                            ui.markdown(build_onboarding_markdown()).classes("text-[14px] leading-6 text-support")

                    with ui.column().classes("input-side-column flex-[0.95] min-w-[320px] gap-4"):
                        with ui.column().classes("input-field-card gap-3 w-full"):
                            with ui.row().classes("w-full items-start gap-3 flex-wrap"):
                                ui.label("2").classes("workflow-step-pill workflow-step-pill-muted")
                                with ui.column().classes("gap-1 flex-1 min-w-[220px]"):
                                    ui.label("自社をどう照合するか").classes("section-font text-[20px] font-bold text-main")
                                    ui.label("自社URLと名称を、結果の照合に使います。").classes("text-[13px] leading-5 text-helper")
                            inputs["target_domain"] = ui.input(
                                "自社URL *",
                                value=state["config"].target_domain,
                                placeholder="example.com",
                            ).props("outlined").classes("w-full")
                            inputs["brand_terms"] = ui.input(
                                "名称 (任意)",
                                value=join_csv(state["config"].brand_terms),
                                placeholder="会社名、サービス名、屋号など",
                            ).props("outlined").classes("w-full")
                            ui.label("自社名やサービス名の揺れを見つけるために使います。").classes("text-[12px] leading-5 text-helper")

                        with ui.column().classes("input-action-card w-full gap-3"):
                            with ui.row().classes("w-full items-start gap-3 flex-wrap"):
                                ui.label("3").classes("workflow-step-pill workflow-step-pill-muted")
                                with ui.column().classes("gap-1 flex-1 min-w-[220px]"):
                                    ui.label("結果を見る").classes("section-font text-[20px] font-bold text-main")
                                    ui.label("今回だけ確認するか、保存済み条件の結果へ進みます。").classes("text-[13px] leading-5 text-helper")
                            run_progress_percent_label = ui.label("").classes("text-[13px] font-semibold text-main").props("aria-live=polite")
                            run_progress_percent_label.visible = False
                            progress = ui.linear_progress(value=0).props("color=deep-orange-7 track-color=amber-1 rounded").classes("w-full")
                            progress.visible = False
                            with ui.row().classes("w-full items-center gap-2 min-h-[22px]") as run_activity_row:
                                ui.icon("autorenew").classes("text-[18px] text-orange-8 animate-spin shrink-0")
                                run_activity_phase_label = ui.label("").classes("text-[13px] text-helper")
                            run_activity_row.visible = False
                            with ui.column().classes("w-full gap-1") as run_copy_container:
                                step_label = ui.label("まずは合計20回答を確認").classes("text-[18px] font-bold text-main")
                                summary_label = ui.label(
                                    "主質問と自社URLを入れると、AI検索で自社が表示されるかを、合計20回答を目安に確認します。"
                                ).classes("text-[14px] text-helper mt-1")
                                recovery_hint_label = ui.label("").classes("text-[13px] leading-6 text-support mt-2")
                            action_button_row = ui.column().classes("w-full gap-3 mt-2")

                inputs["keyword_inputs"] = keyword_inputs
                inputs["keywords"] = keyword_inputs[0]
                inputs["visible_keyword_count"] = lambda: visible_keyword_count
                refresh_keyword_input_visibility()
                refresh_market_context_candidates()
                run_progress_tracker = {
                    "completed": 0,
                    "total_steps": 0,
                    "question_index": 0,
                    "question_total": 0,
                    "expansion_index": 0,
                    "expansion_total": 0,
                    "repeat_index": 0,
                    "repeat_total": 0,
                }

                def safely_update_controls(*controls: Any) -> bool:
                    def _update_controls() -> None:
                        for control in controls:
                            control.update()

                    return safely_run_ui(_update_controls)

                def set_run_status(step_text: str, summary_text: str, recovery_text: str) -> bool:
                    step_label.text = step_text
                    summary_label.text = summary_text
                    recovery_hint_label.text = recovery_text
                    return safely_update_controls(step_label, summary_label, recovery_hint_label)

                def safe_notify(message: str, *, color: str) -> bool:
                    return safely_run_ui(lambda: ui.notify(message, color=color))

                def set_progress_visibility(visible: bool) -> None:
                    progress.visible = visible
                    run_progress_percent_label.visible = visible
                    run_activity_row.visible = visible
                    safely_update_controls(
                        progress,
                        run_progress_percent_label,
                        run_activity_row,
                        run_copy_container,
                    )

                def set_progress_state(
                    completed_count: int,
                    total_count: int,
                    *,
                    question_index: int = 0,
                    question_total: int = 0,
                    expansion_index: int = 0,
                    expansion_total: int = 0,
                    repeat_index: int = 0,
                    repeat_total: int = 0,
                    current_label: str = "",
                    phase_label: str = "",
                    minimum_ratio: float = 0.0,
                ) -> None:
                    safe_total = max(0, int(total_count or 0))
                    safe_completed = max(0, int(completed_count or 0))
                    if safe_total > 0:
                        safe_completed = min(safe_completed, safe_total)
                    ratio = (safe_completed / safe_total) if safe_total > 0 else 0.0
                    minimum_ratio = max(0.0, min(1.0, float(minimum_ratio or 0.0)))
                    ratio = max(ratio, minimum_ratio)
                    run_progress_tracker["completed"] = safe_completed
                    run_progress_tracker["total_steps"] = safe_total
                    run_progress_tracker["question_index"] = max(0, int(question_index or 0))
                    run_progress_tracker["question_total"] = max(0, int(question_total or 0))
                    run_progress_tracker["expansion_index"] = max(0, int(expansion_index or 0))
                    run_progress_tracker["expansion_total"] = max(0, int(expansion_total or 0))
                    run_progress_tracker["repeat_index"] = max(0, int(repeat_index or 0))
                    run_progress_tracker["repeat_total"] = max(0, int(repeat_total or 0))
                    activity_text = " / ".join(part for part in [current_label.strip(), phase_label.strip()] if part and part.strip())
                    run_activity_phase_label.text = activity_text
                    progress.value = ratio
                    percent = int(ratio * 100)
                    if safe_total:
                        run_progress_percent_label.text = f"進捗: {percent}%（{safe_completed}/{safe_total}回答）"
                    else:
                        run_progress_percent_label.text = f"進捗: {percent}%（準備中）"
                    safely_update_controls(progress, run_progress_percent_label, run_activity_phase_label)

                def apply_config_to_inputs(cfg: AppConfig) -> None:
                    next_keywords = list(cfg.keywords[:3])
                    while len(next_keywords) < 3:
                        next_keywords.append("")
                    for index, control in enumerate(keyword_inputs):
                        control.value = next_keywords[index]
                        control.update()
                    nonlocal visible_keyword_count
                    visible_keyword_count = max(1, min(3, len([item for item in next_keywords if str(item).strip()])))
                    refresh_keyword_input_visibility()
                    inputs["target_domain"].value = cfg.target_domain
                    inputs["brand_terms"].value = join_csv(cfg.brand_terms)
                    inputs["market_context"].value = join_csv(cfg.market_context_terms)
                    inputs["competitor_terms"].value = join_csv(cfg.competitor_terms)
                    for control in inputs.values():
                        if isinstance(control, list) or not hasattr(control, "update"):
                            continue
                        control.update()
                    refresh_market_context_candidates()
                    refresh_provider_ui(update_hero=False)

                def mark_results_stale(reason_text: str = "") -> None:
                    had_current_results = bool(state["show_primary_results"] or state["current_result_run_id"])
                    if had_current_results:
                        state["show_primary_results"] = False
                        state["current_result_run_id"] = ""
                        refresh_dashboard_surface()
                    if reason_text and had_current_results:
                        step_label.text = "入力を更新しました"
                        summary_label.text = reason_text
                        recovery_hint_label.text = "前回結果を current のまま残さず、条件変更後は再実行を促します。"
                        step_label.update()
                        summary_label.update()
                        recovery_hint_label.update()

                stale_result_message = "入力条件を変えたため、前回の「今回の結果」は隠しています。もう一度分析してください。"
                for keyword_input in keyword_inputs:
                    keyword_input.on_value_change(
                        lambda _=None, reason=stale_result_message: (refresh_market_context_candidates(), mark_results_stale(reason))
                    )
                inputs["target_domain"].on_value_change(lambda _=None, reason=stale_result_message: mark_results_stale(reason))
                inputs["brand_terms"].on_value_change(lambda _=None, reason=stale_result_message: mark_results_stale(reason))
                inputs["market_context"].on_value_change(
                    lambda _=None, reason=stale_result_message: (refresh_market_context_candidates(), mark_results_stale(reason))
                )
                inputs["competitor_terms"].on_value_change(lambda _=None, reason=stale_result_message: mark_results_stale(reason))

                def refresh_cluster_and_outcome_sections() -> None:
                    page_refreshers.refresh_cluster_and_outcome_sections(
                        db,
                        state["config"],
                        cluster_kind_select,
                        cluster_target_select,
                        saved_cluster_brief_select,
                        cluster_brief_table,
                        outcome_scope_kind_select,
                        outcome_scope_target_select,
                        outcome_run_a_select,
                        outcome_run_b_select,
                    )

                def render_active_cluster_and_outcome_panels() -> None:
                    page_refreshers.render_active_cluster_and_outcome_panels(
                        db,
                        state["config"],
                        cluster_brief_container,
                        saved_cluster_brief_select,
                        outcome_compare_container,
                        outcome_scope_kind_select,
                        outcome_scope_target_select,
                        outcome_run_a_select,
                        outcome_run_b_select,
                    )

                def refresh_dashboard_surface(prebuilt_payload: dict[str, Any] | None = None) -> None:
                    nonlocal periodic_refresh_signature, latest_dashboard_payload
                    try:
                        payload = prebuilt_payload or build_dashboard_payload()
                        should_expand_current_result = False
                        if not state["busy"]:
                            had_current_result = bool(state["show_primary_results"] and state["current_result_run_id"])
                            restored_run_id = str(payload.get("current_run_id") or "")
                            state["current_result_run_id"] = restored_run_id
                            state["show_primary_results"] = bool(restored_run_id)
                            if restored_run_id and not had_current_result:
                                should_expand_current_result = True
                                restored_rows = list(payload.get("current_rows") or [])
                                latest_restored_row = restored_rows[0] if restored_rows else None
                                if latest_restored_row is not None:
                                    set_run_status(
                                        "直近の結果を表示しています",
                                        f"確認時刻: {format_timestamp(latest_restored_row.get('analyzed_at'))} | 同じ入力条件の直近 run を復元しました。",
                                        "質問 / provider / 自社URL / 名称 / 重点テーマ / 比較対象を変えると current 面は空状態に戻ります。",
                                    )
                        page_refreshers.refresh_dashboard_surface(
                            db,
                            state["config"],
                            state["show_primary_results"],
                            str(state["current_result_run_id"] or ""),
                            result_stage_container,
                            metric_refs,
                            decision_refs,
                            rows_table,
                            run_table,
                            question_heatmap_plot if support_tabs is not None and support_tabs.value == support_analysis_tab else None,
                            query_drilldown_plot if support_tabs is not None and support_tabs.value == support_analysis_tab else None,
                            intent_trend_plot if support_tabs is not None and support_tabs.value == support_analysis_tab else None,
                            page_gap_trend_plot if support_tabs is not None and support_tabs.value == support_analysis_tab else None,
                            query_select,
                            detail_select,
                            detail_container,
                            latest_result_container,
                            summary_refs,
                            source_container,
                            dashboard_status,
                            db.list_sources,
                            payload=payload,
                        )
                        latest_dashboard_payload = payload
                        periodic_refresh_signature = build_periodic_refresh_signature(payload)
                        refresh_hero_status(payload)
                        if should_expand_current_result:
                            expand_current_result_surface()
                    except RuntimeError as exc:
                        if is_deleted_ui_runtime_error(exc):
                            return
                        raise
                def refresh_result_sections() -> None:
                    refresh_dashboard_surface()
                    refresh_cluster_and_outcome_sections()
                    render_active_cluster_and_outcome_panels()

                async def on_save() -> None:
                    if block_readonly_demo_ui_action("画面の入力を保存"):
                        return
                    state["config"] = build_config_from_inputs(inputs, state["config"])
                    save_config(state["config"])
                    refresh_runtime_panels_if_visible()
                    mark_results_stale("入力条件を保存したため、前回の「今回の結果」は隠しています。もう一度分析してください。")
                    ui.notify("設定を保存しました", color="positive")
                    refresh_result_sections()

                async def on_question_set_save(*, force_new: bool = False) -> None:
                    if block_readonly_demo_ui_action("保存済み条件を保存・更新"):
                        return
                    cfg = build_config_from_inputs(inputs, state["config"])
                    if notify_missing_required_fields(cfg, context="保存済み条件保存"):
                        return
                    name = question_set_name_input.value.strip() or f"保存条件 {time.strftime('%Y-%m-%d %H:%M')}"
                    selected_id = None if force_new else (question_set_select.value if question_set_select.value else None)
                    saved_id = db.upsert_question_set(
                        question_set_id=selected_id,
                        name=name,
                        config_json=json.dumps(cfg.model_dump(), ensure_ascii=False),
                    )
                    question_set_name_input.value = name
                    page_refreshers.refresh_question_set_admin_views(
                        db,
                        question_set_select,
                        question_set_table,
                        schedule_question_set_select,
                        selected_question_set_id=str(saved_id),
                        selected_schedule_question_set_id=str(saved_id),
                    )
                    sync_question_set_name_from_selection()
                    refresh_cluster_and_outcome_sections()
                    render_active_cluster_and_outcome_panels()
                    refresh_saved_condition_helpers()
                    ui.notify("保存済み条件を保存しました", color="positive")

                async def on_question_set_new_save() -> None:
                    await on_question_set_save(force_new=True)

                async def on_question_set_load() -> None:
                    question_set_id = question_set_select.value
                    if not question_set_id:
                        ui.notify("読み込む保存済み条件を選択してください。", color="warning")
                        return
                    question_set = db.get_question_set(question_set_id)
                    if not question_set:
                        ui.notify("保存済み条件が見つかりません。", color="warning")
                        return
                    cfg = AppConfig.model_validate_json(question_set["config_json"]).model_copy(
                        update={"analysis_mode": ANALYSIS_MODE_MARKET, "repeat_count": 20}
                    )
                    state["config"] = cfg
                    question_set_name_input.value = str(question_set.get("name") or "")
                    schedule_question_set_select.value = question_set_id
                    apply_config_to_inputs(cfg)
                    refresh_runtime_panels_if_visible()
                    mark_results_stale("保存済み条件を読み込んだため、前回の「今回の結果」は隠しています。もう一度分析してください。")
                    refresh_result_sections()
                    refresh_saved_condition_helpers()
                    ui.notify("保存済み条件を読み込みました", color="positive")

                async def on_question_set_archive_toggle() -> None:
                    if block_readonly_demo_ui_action("保存済み条件をアーカイブ・再開"):
                        return
                    question_set_id = str(question_set_select.value or "")
                    if not question_set_id:
                        ui.notify("状態変更する保存済み条件を選択してください。", color="warning")
                        return
                    question_set = db.get_question_set(question_set_id)
                    if not question_set:
                        ui.notify("保存済み条件が見つかりません。", color="warning")
                        return
                    next_archived = not bool(question_set.get("is_archived"))
                    db.set_question_set_archived(question_set_id, next_archived)
                    page_refreshers.refresh_question_set_admin_views(
                        db,
                        question_set_select,
                        question_set_table,
                        schedule_question_set_select,
                        selected_question_set_id=question_set_id,
                    )
                    sync_question_set_name_from_selection()
                    action_label = "アーカイブ" if next_archived else "再開"
                    refresh_saved_condition_helpers()
                    ui.notify(f"保存済み条件を{action_label}しました", color="positive")

                schedule_weekday_summary_label: ui.label | None = None
                schedule_save_time_label: ui.label | None = None
                schedule_setting_status_label: ui.label | None = None
                schedule_enabled_helper_label: ui.label | None = None
                schedule_week_count_label: ui.label | None = None
                question_set_detail_label: ui.label | None = None
                schedule_target_summary_label: ui.label | None = None

                def refresh_saved_condition_helpers() -> None:
                    if question_set_detail_label is not None:
                        selected_question_set = (
                            db.get_question_set(str(question_set_select.value or ""))
                            if question_set_select is not None and question_set_select.value
                            else None
                        )
                        question_set_detail_label.text = admin_views.build_question_set_detail_text(selected_question_set)
                        question_set_detail_label.update()
                    if schedule_target_summary_label is not None:
                        selected_schedule_set = (
                            db.get_question_set(str(schedule_question_set_select.value or ""))
                            if schedule_question_set_select is not None and schedule_question_set_select.value
                            else None
                        )
                        if selected_schedule_set:
                            target_name = admin_views.sanitize_saved_scope_label(
                                selected_schedule_set.get("name"),
                                fallback="保存済み条件",
                            )
                            schedule_target_summary_label.text = (
                                f"対象: {target_name} / "
                                f"{admin_views.build_question_set_detail_text(selected_schedule_set)}"
                            )
                        else:
                            schedule_target_summary_label.text = (
                                "自動チェックは、上の「保存済み条件」から選んだ内容を曜日と時刻で実行します。"
                            )
                        schedule_target_summary_label.update()

                def refresh_schedule_form_summary() -> None:
                    if schedule_weekday_summary_label is None:
                        return
                    selected_weekdays = list(schedule_weekdays_select.value or [])
                    selection_text, save_text = admin_views.build_schedule_weekday_summary(
                        selected_weekdays,
                        time_of_day=str(schedule_time_input.value or "09:00"),
                    )
                    schedule_weekday_summary_label.text = selection_text
                    if schedule_week_count_label is not None:
                        schedule_week_count_label.text = (
                            f"週あたり回数: {len(set(selected_weekdays)) or 0}回（曜日選択から自動計算）"
                        )
                    schedule_save_time_label.text = save_text
                    if schedule_setting_status_label is not None:
                        schedule_setting_status_label.text = admin_views.build_schedule_setting_status_text(
                            bool(schedule_enabled_switch.value)
                        )
                    if schedule_enabled_helper_label is not None:
                        schedule_enabled_helper_label.text = (
                            "ON: 予定時刻に自動チェック"
                            if bool(schedule_enabled_switch.value)
                            else "OFF: 保存だけして実行しない"
                        )
                    for label in (
                        schedule_weekday_summary_label,
                        schedule_save_time_label,
                        schedule_setting_status_label,
                        schedule_enabled_helper_label,
                        schedule_week_count_label,
                    ):
                        if label is not None:
                            label.update()

                async def on_schedule_save() -> None:
                    if block_readonly_demo_ui_action("自動チェックを保存"):
                        return
                    question_set_id = schedule_question_set_select.value or question_set_select.value
                    if not question_set_id:
                        ui.notify("先に保存済み条件を選択してください。", color="warning")
                        return
                    selected_weekday_values = list(schedule_weekdays_select.value or [])
                    weekdays = normalize_schedule_weekdays(
                        selected_weekday_values,
                        max(1, len(set(selected_weekday_values)) or 1),
                    )
                    if not weekdays:
                        ui.notify("曜日を1つ以上選択してください。", color="warning")
                        return
                    effective_weekly_runs = len(weekdays)
                    question_set = db.get_question_set(question_set_id)
                    if not question_set:
                        ui.notify("選択した保存済み条件が見つかりません。", color="warning")
                        return
                    question_set_cfg = AppConfig.model_validate_json(question_set["config_json"]).model_copy(
                        update={"analysis_mode": ANALYSIS_MODE_MARKET, "repeat_count": 20}
                    )
                    if notify_missing_required_fields(question_set_cfg, context="自動チェック保存"):
                        return
                    schedule_name = schedule_name_input.value.strip() or f"{question_set['name']} 定期監視"
                    existing_schedule = next(
                        (
                            row
                            for row in db.list_schedules(limit=100)
                            if row.get("question_set_id") == question_set_id and row.get("name") == schedule_name
                        ),
                        None,
                    )
                    existing_schedule_data = existing_schedule or {}
                    saved_id = db.save_schedule(
                        schedule_id=str(existing_schedule_data.get("schedule_id") or "") or None,
                        question_set_id=question_set_id,
                        name=schedule_name,
                        weekdays_csv=",".join(str(day) for day in weekdays),
                        time_of_day=str(schedule_time_input.value or "09:00"),
                        weekly_run_count=effective_weekly_runs,
                        timezone=str(schedule_timezone_input.value or "Asia/Tokyo"),
                        cost_guardrail_usd=float(
                            existing_schedule_data.get("cost_guardrail_usd") or state["config"].run_budget_guardrail_usd or 0.0
                        ),
                        enabled=bool(schedule_enabled_switch.value),
                    )
                    next_run_at = compute_next_schedule_run(
                        weekdays,
                        effective_weekly_runs,
                        str(schedule_time_input.value or "09:00"),
                        str(schedule_timezone_input.value or "Asia/Tokyo"),
                    )
                    db.update_schedule_runtime(
                        saved_id,
                        next_run_at=next_run_at,
                        last_status="enabled" if schedule_enabled_switch.value else "disabled",
                        last_error="",
                    )
                    page_refreshers.refresh_schedule_admin_views(
                        db,
                        scheduler_service,
                        schedule_table,
                        scheduler_status_label,
                        schedule_manage_select,
                        compare_target_select,
                        compare_mode_select,
                        selected_schedule_id=str(saved_id),
                    )
                    refresh_schedule_form_summary()
                    refresh_cluster_and_outcome_sections()
                    render_active_cluster_and_outcome_panels()
                    ui.notify("自動チェックを保存しました", color="positive")

                def load_schedule_into_form(schedule: dict[str, Any]) -> None:
                    schedule_question_set_select.value = str(schedule.get("question_set_id") or "")
                    schedule_question_set_select.update()
                    schedule_name_input.value = str(schedule.get("name") or "")
                    schedule_name_input.update()
                    schedule_time_input.value = str(schedule.get("time_of_day") or "09:00")
                    schedule_time_input.update()
                    schedule_timezone_input.value = str(schedule.get("timezone") or state["config"].timezone)
                    schedule_timezone_input.update()
                    weekdays = parse_weekdays_csv(schedule.get("weekdays_csv"))
                    schedule_weekdays_select.value = [str(day) for day in weekdays]
                    schedule_weekdays_select.update()
                    schedule_enabled_switch.value = bool(schedule.get("enabled"))
                    schedule_enabled_switch.update()
                    refresh_schedule_form_summary()

                async def on_schedule_load() -> None:
                    if schedule_manage_select is None or not schedule_manage_select.value:
                        ui.notify("読み込む自動チェックを選択してください。", color="warning")
                        return
                    schedule = db.get_schedule(str(schedule_manage_select.value))
                    if not schedule:
                        ui.notify("選択した自動チェックが見つかりません。", color="warning")
                        return
                    load_schedule_into_form(schedule)
                    refresh_saved_condition_helpers()
                    ui.notify("自動チェックをフォームへ読み込みました。", color="positive")

                async def on_schedule_duplicate() -> None:
                    if block_readonly_demo_ui_action("自動チェックを複製"):
                        return
                    if schedule_manage_select is None or not schedule_manage_select.value:
                        ui.notify("複製する自動チェックを選択してください。", color="warning")
                        return
                    schedule = db.get_schedule(str(schedule_manage_select.value))
                    if not schedule:
                        ui.notify("選択した自動チェックが見つかりません。", color="warning")
                        return
                    duplicate_name = f"{str(schedule.get('name') or '自動チェック')} 複製"
                    duplicate_id = db.save_schedule(
                        question_set_id=str(schedule.get("question_set_id") or ""),
                        name=duplicate_name,
                        weekdays_csv=str(schedule.get("weekdays_csv") or ""),
                        time_of_day=str(schedule.get("time_of_day") or "09:00"),
                        weekly_run_count=int(schedule.get("weekly_run_count") or 1),
                        timezone=str(schedule.get("timezone") or state["config"].timezone),
                        cost_guardrail_usd=float(schedule.get("cost_guardrail_usd") or state["config"].run_budget_guardrail_usd or 0.0),
                        enabled=False,
                    )
                    next_run_at = compute_next_schedule_run(
                        parse_weekdays_csv(schedule.get("weekdays_csv")),
                        int(schedule.get("weekly_run_count") or 1),
                        str(schedule.get("time_of_day") or "09:00"),
                        str(schedule.get("timezone") or state["config"].timezone),
                    )
                    db.update_schedule_runtime(
                        duplicate_id,
                        next_run_at=next_run_at,
                        last_status="disabled",
                        last_error="複製直後は停止状態で保存しました。",
                    )
                    page_refreshers.refresh_schedule_admin_views(
                        db,
                        scheduler_service,
                        schedule_table,
                        scheduler_status_label,
                        schedule_manage_select,
                        compare_target_select,
                        compare_mode_select,
                        selected_schedule_id=str(duplicate_id),
                    )
                    duplicate_schedule = db.get_schedule(duplicate_id)
                    if duplicate_schedule:
                        load_schedule_into_form(duplicate_schedule)
                        refresh_saved_condition_helpers()
                    refresh_cluster_and_outcome_sections()
                    render_active_cluster_and_outcome_panels()
                    ui.notify("自動チェックを複製し、停止状態で保存しました。", color="positive")

                async def confirm_schedule_delete() -> None:
                    if block_readonly_demo_ui_action("自動チェックを削除"):
                        return
                    if schedule_manage_select is None or not schedule_manage_select.value:
                        return
                    schedule = db.get_schedule(str(schedule_manage_select.value))
                    if not schedule:
                        ui.notify("削除対象の自動チェックが見つかりません。", color="warning")
                        if schedule_delete_dialog is not None:
                            schedule_delete_dialog.close()
                        return
                    db.delete_schedule(str(schedule_manage_select.value))
                    if schedule_delete_dialog is not None:
                        schedule_delete_dialog.close()
                    page_refreshers.refresh_schedule_admin_views(
                        db,
                        scheduler_service,
                        schedule_table,
                        scheduler_status_label,
                        schedule_manage_select,
                        compare_target_select,
                        compare_mode_select,
                    )
                    if schedule_diff_container is not None:
                        admin_views.render_schedule_diff(db, "", str(compare_mode_select.value or "schedule"), "", schedule_diff_container)
                    refresh_cluster_and_outcome_sections()
                    render_active_cluster_and_outcome_panels()
                    ui.notify(f"{schedule.get('name')} を削除しました。", color="positive")

                async def on_schedule_delete() -> None:
                    if block_readonly_demo_ui_action("自動チェックを削除"):
                        return
                    if schedule_manage_select is None or not schedule_manage_select.value:
                        ui.notify("削除する自動チェックを選択してください。", color="warning")
                        return
                    if schedule_delete_dialog is not None:
                        schedule_delete_dialog.open()

                async def on_schedule_diff_refresh() -> None:
                    if schedule_diff_container is None or schedule_manage_select is None or compare_mode_select is None or compare_target_select is None:
                        return
                    admin_views.render_schedule_diff(
                        db,
                        str(schedule_manage_select.value or ""),
                        str(compare_mode_select.value or "schedule"),
                        str(compare_target_select.value or ""),
                        schedule_diff_container,
                    )

                async def on_cluster_brief_generate() -> None:
                    if block_readonly_demo_ui_action("クラスタ下書きを保存"):
                        return
                    if (
                        cluster_kind_select is None
                        or cluster_target_select is None
                        or cluster_brief_container is None
                        or saved_cluster_brief_select is None
                        or cluster_brief_table is None
                    ):
                        return
                    selected_token = str(cluster_target_select.value or "")
                    scoped_rows = dashboard_views.filter_rows_for_active_scope(db.list_recent_results(limit=2000), state["config"])
                    cluster_kind, cluster_key, candidate, cluster_rows = resolve_cluster_brief_candidate(
                        scoped_rows,
                        state["config"],
                        selected_token,
                    )
                    if not cluster_kind or not cluster_key:
                        ui.notify("下書きを作るクラスタを選択してください。", color="warning")
                        return
                    if not candidate:
                        ui.notify("選択した cluster が見つかりません。", color="warning")
                        return
                    brief = build_cluster_brief_draft(
                        cluster_rows,
                        cluster_kind,
                        str(candidate.get("cluster_key") or ""),
                        str(candidate.get("cluster_label") or ""),
                        state["config"],
                    )
                    saved_id = db.save_cluster_brief(
                        **build_cluster_brief_save_payload(brief, cluster_kind, cluster_key, candidate)
                    )
                    page_refreshers.refresh_cluster_brief_admin_views(
                        db,
                        scoped_rows,
                        state["config"],
                        cluster_kind_select,
                        cluster_target_select,
                        saved_cluster_brief_select,
                        cluster_brief_table,
                        selected_brief_id=str(saved_id),
                    )
                    admin_views.render_cluster_brief_payload(brief, cluster_brief_container)
                    ui.notify("クラスタ下書きを生成して保存しました。", color="positive")

                async def on_saved_cluster_brief_load() -> None:
                    if saved_cluster_brief_select is None or cluster_brief_container is None:
                        return
                    brief_id = str(saved_cluster_brief_select.value or "")
                    if not brief_id:
                        ui.notify("表示する保存済み下書きを選択してください。", color="warning")
                        return
                    if not db.get_cluster_brief(brief_id):
                        ui.notify("保存済み下書きが見つかりません。", color="warning")
                        return
                    page_refreshers.render_cluster_brief_payload_by_id(
                        db,
                        brief_id,
                        cluster_brief_container,
                    )

                async def on_outcome_compare_show() -> None:
                    if (
                        outcome_scope_kind_select is None
                        or outcome_scope_target_select is None
                        or outcome_run_a_select is None
                        or outcome_run_b_select is None
                        or outcome_compare_container is None
                    ):
                        return
                    page_refreshers.render_outcome_compare_panel(
                        db,
                        state["config"],
                        outcome_compare_container,
                        outcome_scope_kind_select,
                        outcome_scope_target_select,
                        outcome_run_a_select,
                        outcome_run_b_select,
                    )

                async def on_export() -> None:
                    if block_readonly_demo_ui_action("出力ファイルを更新"):
                        return
                    cfg = build_config_from_inputs(inputs, state["config"])
                    rows = dashboard_views.filter_rows_for_active_scope(db.list_recent_results(limit=2000), cfg)
                    state["export_rows"], state["report_preview"] = write_export_files(rows, cfg, EXPORTS_DIR, db.list_sources)
                    refresh_export_panel_if_ready(force=True)
                    ui.notify("出力ファイルを更新しました", color="positive")

                async def on_run() -> None:
                    if state["busy"] or state["batch_busy"]:
                        return
                    if READONLY_DEMO_MODE:
                        ui.notify(readonly_demo_block_message("manual LLM/API send"), color="warning")
                        print(f"[kotomegane] {readonly_demo_block_message('manual LLM/API send')}", flush=True)
                        return
                    manual_cfg = state["config"]
                    total_steps = 0
                    current_question_total = 0
                    current_expansion_total = 0
                    try:
                        cfg = build_config_from_inputs(inputs, state["config"])
                        manual_cfg = build_manual_runtime_config(cfg)
                        if notify_missing_required_fields(cfg, context="分析実行"):
                            return
                        manual_policy = resolve_run_policy(cfg, "manual")
                        provider = get_provider_option(cfg.provider)
                        api_key_status = get_api_key_status(cfg.provider)
                        if not manual_policy.allowed:
                            ui.notify(manual_policy.blocked_reason or f"{provider.label} は未対応です。", color="warning")
                            return
                        if not api_key_status.present:
                            ui.notify(f"{api_key_status.env_var} が未設定です。.env または環境変数に設定してください。", color="negative")
                            return
                        credit_units = _kotomegane_credit_units(manual_cfg.provider)
                        if not await _ensure_usage_credit_available("kotomegane", units=credit_units):
                            return
                        budget_guardrail = _load_budget_guardrail(manual_cfg)
                        if budget_guardrail["should_block"]:
                            ui.notify(
                                "日次上限を超える見込みです。質問数、回数、または上限設定を見直してください。",
                                color="negative",
                            )
                            return
                        state["config"] = cfg
                        save_config(cfg)
                        refresh_runtime_panels_if_visible()
                        refresh_hero_status()
                        state["busy"] = True
                        state["cancel_requested"] = False
                        state["show_primary_results"] = False
                        state["current_result_run_id"] = ""
                        total_steps = 0
                        current_question_total = 0
                        current_expansion_total = 0
                        set_progress_visibility(True)
                        set_progress_state(
                            0,
                            100,
                            current_label="現在: 実行計画を準備中",
                            phase_label=f"状態: {provider.label} へ送る前の準備中",
                            minimum_ratio=0.06,
                        )
                        set_run_status(
                            "分析中です",
                            f"1回だけ確認は 1 質問あたり {manual_cfg.repeat_count} 回で軽く確認しています。",
                            "数十秒から数分かかることがあります。進捗が止まって見えても、まずは完了か失敗の表示が出るまで待ってください。2分以上変化がなければ再実行を検討してください。",
                        )
                        safely_run_ui(lambda: set_run_button_busy(True))
                        set_action_button_states(False)
                        await asyncio.sleep(0.05)

                        completed = 0
                        failures = 0
                        run_spend_usd = 0.0
                        stopped_by_budget = False
                        canceled_by_user = False
                        run_blocked_message = ""
                        run_error_message = ""
                        last_request_error_message = ""
                        current_question_set = db.get_question_set(question_set_select.value) if question_set_select.value else None
                        run_id = db.create_run_session(
                            manual_cfg.repeat_count,
                            manual_cfg.model,
                            manual_cfg.prompt_cache_key,
                            run_mode="manual",
                            config_json=json.dumps(manual_cfg.model_dump(), ensure_ascii=False),
                            question_set_id=str(current_question_set.get("question_set_id") or "") if current_question_set else "",
                            question_set_name=str(current_question_set.get("name") or "") if current_question_set else "",
                        )
                        set_progress_state(
                            0,
                            100,
                            current_label="現在: 分析を準備しています",
                            phase_label="状態: 質問の展開計画を準備中",
                            minimum_ratio=0.10,
                        )
                        await asyncio.sleep(0.05)
                        try:
                            try:
                                query_plans = await prepare_query_plans_for_run(
                                    db,
                                    query_planner,
                                    run_id,
                                    manual_cfg,
                                    run_mode="manual",
                                )
                                execution_plan: ExecutionPlan = build_execution_plan(query_plans, manual_cfg)
                                budget_guardrail = _load_budget_guardrail(
                                    manual_cfg,
                                    planned_request_count=execution_plan.total_request_count,
                                )
                                if budget_guardrail["run_guardrail_should_block"]:
                                    run_blocked_message = (
                                        "今回の分析は実際の送信件数ベースで 1 回の実行上限を超える見込みです。"
                                        " 質問数か回数を絞ってください。"
                                    )
                                    summary_label.text = "実際の送信件数で見積もると、今回の分析は内部上限を超える見込みです。"
                                    recovery_hint_label.text = "質問数か回数を絞ってから再実行してください。"
                                    summary_label.update()
                                    recovery_hint_label.update()
                                    raise RunGuardrailBlockedError(run_blocked_message)
                                if budget_guardrail["would_exceed_run_guardrail"]:
                                    ui.notify(
                                        "1 回の実行上限を超える見込みです。現在の設定は「上限を超えても止めずに続ける」ため、このまま分析を続行します。",
                                        color="warning",
                                    )
                                query_plan_position_map = {
                                    str(plan.get("query_plan_id") or ""): index
                                    for index, plan in enumerate(query_plans, start=1)
                                }
                                total_steps = max(1, execution_plan.total_request_count)
                                current_question_total = max(1, len(query_plans))
                                set_progress_state(
                                    0,
                                    total_steps,
                                    question_index=0,
                                    question_total=current_question_total,
                                    expansion_index=0,
                                    expansion_total=max(1, execution_plan.total_unique_queries),
                                    repeat_index=0,
                                    repeat_total=max(1, manual_cfg.repeat_count),
                                    current_label="現在: 実行内容を準備しています",
                                    phase_label=f"状態: {provider.label} へ送る順番を組み立て中",
                                    minimum_ratio=0.14,
                                )
                                summary_label.text = (
                                    f"元質問 {len(query_plans)} 件を、内部では {execution_plan.total_unique_queries} 件の拡張質問（同じ意味の言い換え文）に広げ、"
                                    f" 各 {manual_cfg.repeat_count} 回ずつ確認します。表現を変えて複数回試すことで、AIの回答の傾向を安定して確認できます。合計 {total_steps} 回答です。"
                                )
                                summary_label.update()
                                recovery_hint_label.text = "途中で閉じずに待つと、そのまま今回の結果へ切り替わります。長く止まる場合だけ再実行を検討してください。"
                                recovery_hint_label.update()
                                grouped_request_map: dict[tuple[str, int], list[Any]] = {}
                                for request in execution_plan.requests:
                                    group_key = (str(request.query_plan_id or ""), int(request.iteration_index or 0))
                                    grouped_request_map.setdefault(group_key, []).append(request)

                                manual_request_groups: list[dict[str, Any]] = []
                                if execution_plan.execution_order == "repeat_then_query":
                                    for iteration_index in range(1, manual_cfg.repeat_count + 1):
                                        for plan in query_plans:
                                            plan_id = str(plan.get("query_plan_id") or "")
                                            group_requests = sorted(
                                                grouped_request_map.get((plan_id, iteration_index), []),
                                                key=lambda item: int(item.executed_query_index or 0),
                                            )
                                            if not group_requests:
                                                continue
                                            manual_request_groups.append(
                                                {
                                                    "query_plan_id": plan_id,
                                                    "question_index": int(query_plan_position_map.get(plan_id, 1)),
                                                    "question_total": max(1, len(query_plans)),
                                                    "repeat_index": iteration_index,
                                                    "requests": group_requests,
                                                    "user_query_raw": str(plan.get("user_query_raw") or ""),
                                                }
                                            )
                                else:
                                    for plan in query_plans:
                                        plan_id = str(plan.get("query_plan_id") or "")
                                        for iteration_index in range(1, manual_cfg.repeat_count + 1):
                                            group_requests = sorted(
                                                grouped_request_map.get((plan_id, iteration_index), []),
                                                key=lambda item: int(item.executed_query_index or 0),
                                            )
                                            if not group_requests:
                                                continue
                                            manual_request_groups.append(
                                                {
                                                    "query_plan_id": plan_id,
                                                    "question_index": int(query_plan_position_map.get(plan_id, 1)),
                                                    "question_total": max(1, len(query_plans)),
                                                    "repeat_index": iteration_index,
                                                    "requests": group_requests,
                                                    "user_query_raw": str(plan.get("user_query_raw") or ""),
                                                }
                                            )

                                async def execute_manual_request(request: Any) -> tuple[str, Any, Any, str]:
                                    try:
                                        request_provider_client = build_provider_client(manual_cfg.provider)
                                        result = await asyncio.to_thread(
                                            request_provider_client.analyze_keyword,
                                            request.executed_query,
                                            manual_cfg,
                                        )
                                        return ("ok", request, result, "")
                                    except Exception as exc:
                                        return ("error", request, None, runtime_common.sanitize_runtime_error_message(exc))

                                for request_group in manual_request_groups:
                                    if state["cancel_requested"]:
                                        canceled_by_user = True
                                        set_progress_state(
                                            completed,
                                            total_steps,
                                            question_index=current_question_total,
                                            question_total=current_question_total,
                                            expansion_index=0,
                                            expansion_total=max(1, current_expansion_total),
                                            repeat_index=0,
                                            repeat_total=max(1, manual_cfg.repeat_count),
                                            current_label="現在: 停止リクエストを反映しています",
                                            phase_label="状態: 次の処理には進みません",
                                        )
                                        summary_label.text = "停止リクエストを受け付けたため、次の処理には進みません。"
                                        recovery_hint_label.text = "途中結果は current 面に反映していません。必要なら同じ条件で再実行してください。"
                                        summary_label.update()
                                        recovery_hint_label.update()
                                        break
                                    current_question_index = int(request_group["question_index"])
                                    current_question_total = int(request_group["question_total"])
                                    current_expansion_total = len(request_group["requests"])
                                    current_repeat_index = int(request_group["repeat_index"])
                                    current_question_raw = str(request_group["user_query_raw"] or "")
                                    if (
                                        manual_cfg.daily_budget_usd > 0
                                        and manual_cfg.budget_guardrail_mode == "stop"
                                        and budget_guardrail["today_committed_usd"] + run_spend_usd + (
                                            budget_guardrail["avg_request_cost_usd"] * current_expansion_total
                                        )
                                        > manual_cfg.daily_budget_usd
                                    ):
                                        stopped_by_budget = True
                                        set_progress_state(
                                            completed,
                                            total_steps,
                                            question_index=current_question_index,
                                            question_total=current_question_total,
                                            expansion_index=0,
                                            expansion_total=max(1, current_expansion_total),
                                            repeat_index=current_repeat_index,
                                            repeat_total=max(1, manual_cfg.repeat_count),
                                            current_label="現在: 予算条件により停止します",
                                            phase_label="状態: ここまでの結果で終了します",
                                        )
                                        summary_label.text = (
                                            "日次上限に達する見込みのため、次の並列グループから先の実行を停止しました。"
                                            " 回数か質問数を絞って再開してください。"
                                        )
                                        summary_label.update()
                                        recovery_hint_label.text = "停止理由を見直して、質問数か回数を絞ってから再実行してください。"
                                        recovery_hint_label.update()
                                        break
                                    set_progress_state(
                                        completed,
                                        total_steps,
                                        question_index=current_question_index,
                                        question_total=current_question_total,
                                        expansion_index=0,
                                        expansion_total=current_expansion_total,
                                        repeat_index=current_repeat_index,
                                        repeat_total=max(1, manual_cfg.repeat_count),
                                        phase_label=f"状態: {provider.label} で拡張質問を並列実行中",
                                        minimum_ratio=0.01 if completed == 0 else 0.0,
                                    )
                                    await asyncio.sleep(0)
                                    group_completed = 0
                                    parallel_tasks: list[asyncio.Task] = []
                                    try:
                                        parallel_tasks = [
                                            asyncio.create_task(execute_manual_request(group_request))
                                            for group_request in request_group["requests"]
                                        ]
                                        for finished_task in asyncio.as_completed(parallel_tasks):
                                            status, request, result, safe_error = await finished_task
                                            latest_query = str(request.executed_query or "")
                                            if status == "ok" and result is not None:
                                                result.output_json["analysis_context"] = {
                                                    **(result.output_json.get("analysis_context") or {}),
                                                    "question": request.executed_query,
                                                    "user_query_raw": request.user_query_raw,
                                                    "executed_query": request.executed_query,
                                                }
                                                result.estimated_cost_usd = estimate_cost_usd(result.usage, result.web_search_calls, manual_cfg)
                                                db.save_keyword_result(
                                                    run_id=run_id,
                                                    iteration_index=request.iteration_index,
                                                    result=result,
                                                    query_plan_id=request.query_plan_id,
                                                    display_query_raw=request.user_query_raw,
                                                    executed_query=request.executed_query,
                                                    executed_query_index=int(request.executed_query_index),
                                                )
                                                run_spend_usd += result.estimated_cost_usd
                                            else:
                                                failures += 1
                                                last_request_error_message = safe_error
                                                error_result = runtime_common.build_error_result(
                                                    latest_query,
                                                    safe_error,
                                                    manual_cfg,
                                                )
                                                error_result.output_json["analysis_context"] = {
                                                    **(error_result.output_json.get("analysis_context") or {}),
                                                    "question": request.executed_query,
                                                    "user_query_raw": request.user_query_raw,
                                                    "executed_query": request.executed_query,
                                                }
                                                db.save_keyword_result(
                                                    run_id=run_id,
                                                    iteration_index=request.iteration_index,
                                                    result=error_result,
                                                    error_text=safe_error,
                                                    query_plan_id=request.query_plan_id,
                                                    display_query_raw=request.user_query_raw,
                                                    executed_query=request.executed_query,
                                                    executed_query_index=int(request.executed_query_index),
                                                )
                                            completed += 1
                                            group_completed += 1
                                            pending_count = max(0, current_expansion_total - group_completed)
                                            phase_text = (
                                                "状態: 停止リクエスト受付済み。現在の並列グループ完了待ち"
                                                if state["cancel_requested"] and pending_count > 0
                                                else (
                                                    f"状態: {provider.label} の並列応答待ち"
                                                    if pending_count > 0
                                                    else "状態: 並列グループを集約中"
                                                )
                                            )
                                            set_progress_state(
                                                completed,
                                                total_steps,
                                                question_index=current_question_index,
                                                question_total=current_question_total,
                                                expansion_index=group_completed,
                                                expansion_total=current_expansion_total,
                                                repeat_index=current_repeat_index,
                                                repeat_total=max(1, manual_cfg.repeat_count),
                                                phase_label=phase_text,
                                            )
                                    finally:
                                        if parallel_tasks:
                                            for pending_task in parallel_tasks:
                                                if not pending_task.done():
                                                    pending_task.cancel()
                                            await asyncio.gather(*parallel_tasks, return_exceptions=True)
                                    if state["cancel_requested"]:
                                        canceled_by_user = True
                                        set_progress_state(
                                            completed,
                                            total_steps,
                                            question_index=current_question_index,
                                            question_total=current_question_total,
                                            expansion_index=current_expansion_total,
                                            expansion_total=current_expansion_total,
                                            repeat_index=current_repeat_index,
                                            repeat_total=max(1, manual_cfg.repeat_count),
                                            current_label="現在: この実行はここで停止します",
                                            phase_label="状態: 現在の並列グループを終えて停止済み",
                                        )
                                        step_label.text = "停止を受け付けました"
                                        summary_label.text = "現在の並列グループが終わったため、ここで停止します。"
                                        recovery_hint_label.text = "途中結果は current 面に反映していません。必要なら同じ条件で再実行してください。"
                                        step_label.update()
                                        summary_label.update()
                                        recovery_hint_label.update()
                                        break
                                    await asyncio.sleep(0)
                            except RunGuardrailBlockedError as exc:
                                run_blocked_message = str(exc)
                            except Exception as exc:
                                run_error_message = runtime_common.sanitize_runtime_error_message(exc)
                        finally:
                            db.finish_run_session(run_id)
                            if current_question_set:
                                db.touch_question_set_run(
                                    str(current_question_set.get("question_set_id") or ""),
                                    run_mode="manual",
                                )
                            state["busy"] = False

                        if run_error_message:
                            set_progress_state(
                                completed,
                                total_steps,
                                question_index=current_question_total,
                                question_total=current_question_total,
                                expansion_index=0,
                                expansion_total=max(1, current_expansion_total),
                                repeat_index=0,
                                repeat_total=max(1, manual_cfg.repeat_count),
                                current_label="現在: エラー内容を反映しています",
                                phase_label="状態: 分析失敗",
                            )
                            set_run_status(
                                "分析に失敗しました",
                                run_error_message,
                                "時間をおいて再実行してください。入力条件を変えない場合も、もう一度「分析を実行」で再試行できます。",
                            )
                            safe_notify(f"分析に失敗しました: {run_error_message}", color="negative")
                            safely_run_ui(refresh_dashboard_surface)
                            set_progress_visibility(False)
                            safely_run_ui(lambda: set_run_button_busy(False))
                            safely_run_ui(lambda: set_action_button_states(True))
                            return

                        if run_blocked_message:
                            set_progress_state(
                                0,
                                total_steps,
                                question_index=0,
                                question_total=current_question_total,
                                expansion_index=0,
                                expansion_total=max(1, current_expansion_total) if current_expansion_total else 0,
                                repeat_index=0,
                                repeat_total=max(1, manual_cfg.repeat_count),
                                current_label="現在: 実行前ガードレールを反映しています",
                                phase_label="状態: 開始見送り",
                            )
                            set_run_status(
                                "分析を開始しませんでした",
                                run_blocked_message,
                                "入力内容と設定を見直してから再実行してください。",
                            )
                            safe_notify(run_blocked_message, color="negative")
                            safely_run_ui(refresh_dashboard_surface)
                            set_progress_visibility(False)
                            safely_run_ui(lambda: set_run_button_busy(False))
                            safely_run_ui(lambda: set_action_button_states(True))
                            return

                        if canceled_by_user:
                            set_progress_state(
                                completed,
                                total_steps,
                                question_index=current_question_total,
                                question_total=current_question_total,
                                expansion_index=0,
                                expansion_total=max(1, current_expansion_total),
                                repeat_index=0,
                                repeat_total=max(1, manual_cfg.repeat_count),
                                current_label="現在: 停止結果を反映しています",
                                phase_label="状態: 停止完了",
                            )
                            set_run_status(
                                "分析を停止しました",
                                f"{completed}件処理したところで停止しました。途中結果は現在の結果面に反映していません。",
                                "同じ条件で続けたいときは、そのまま再実行してください。",
                            )
                            state["show_primary_results"] = False
                            state["current_result_run_id"] = ""
                            state["cancel_requested"] = False
                            safely_run_ui(refresh_result_sections)
                            safe_notify("分析を停止しました。現在の並列グループが終わった時点で止めています。", color="warning")
                            set_progress_visibility(False)
                            safely_run_ui(lambda: set_run_button_busy(False))
                            safely_run_ui(lambda: set_action_button_states(True))
                            return

                        if total_steps > 0 and failures >= total_steps and completed == 0:
                            all_failed_message = (
                                last_request_error_message
                                or "すべてのAI接続が失敗しました。接続状況とAPIキーを確認してから再実行してください。"
                            )
                            set_progress_state(
                                0,
                                total_steps,
                                question_index=current_question_total,
                                question_total=current_question_total,
                                expansion_index=0,
                                expansion_total=max(1, current_expansion_total),
                                repeat_index=0,
                                repeat_total=max(1, manual_cfg.repeat_count),
                                current_label="現在: 全件失敗を反映しています",
                                phase_label="状態: 分析失敗",
                            )
                            set_run_status(
                                "分析に失敗しました",
                                f"送信した {failures} 件すべてが失敗しました。{all_failed_message}",
                                "接続状況とAPIキーを確認し、時間をおいて再実行してください。",
                            )
                            state["cancel_requested"] = False
                            state["show_primary_results"] = False
                            state["current_result_run_id"] = ""
                            safely_run_ui(refresh_result_sections)
                            set_progress_visibility(False)
                            safely_run_ui(lambda: set_run_button_busy(False))
                            safely_run_ui(lambda: set_action_button_states(True))
                            safe_notify(f"分析に失敗しました: {all_failed_message}", color="negative")
                            return

                        set_progress_state(
                            total_steps,
                            total_steps,
                            question_index=current_question_total,
                            question_total=current_question_total,
                            expansion_index=max(1, current_expansion_total) if total_steps else 0,
                            expansion_total=max(1, current_expansion_total),
                            repeat_index=max(1, manual_cfg.repeat_count) if total_steps else 0,
                            repeat_total=max(1, manual_cfg.repeat_count),
                            current_label="現在: 集計結果を画面へ反映中",
                            phase_label="状態: 集計中",
                        )
                        set_run_status(
                            "予算停止" if stopped_by_budget else "分析完了",
                            f"失敗 {failures}件。"
                            + (" 日次上限に達する前で停止しました。" if stopped_by_budget else " 直近結果と結果一覧を更新しました。"),
                            "入力を変えると current 結果はいったん隠れます。同じ条件で見直すときは、そのまま再実行してください。",
                        )
                        state["cancel_requested"] = False
                        state["show_primary_results"] = True
                        state["current_result_run_id"] = run_id
                        safely_run_ui(refresh_result_sections)
                        safely_run_ui(expand_current_result_surface)
                        set_progress_visibility(False)
                        safely_run_ui(lambda: set_run_button_busy(False))
                        safely_run_ui(lambda: set_action_button_states(True))
                        successful_results = max(0, completed - failures)
                        if successful_results > 0:
                            credit_debited = await _consume_usage_credit_after_success(
                                service_key="kotomegane",
                                action_key="manual_observation",
                                attempt_id=str(run_id),
                                units=credit_units,
                                metadata={
                                    "provider": manual_cfg.provider,
                                    "run_mode": "manual",
                                    "successful_results": successful_results,
                                    "failed_results": failures,
                                },
                            )
                            if not credit_debited:
                                safe_notify("分析は完了しましたが、クレジット消費を確認できませんでした。管理者へ連絡してください。", color="warning")
                                return
                        if failures:
                            safe_notify(f"分析完了。ただし {failures} 件は失敗しました", color="warning")
                        else:
                            safe_notify("分析が完了しました", color="positive")
                    except Exception as exc:
                        safe_error = runtime_common.sanitize_runtime_error_message(exc)
                        state["busy"] = False
                        state["cancel_requested"] = False
                        state["current_result_run_id"] = ""
                        set_progress_state(
                            0,
                            total_steps,
                            question_index=0,
                            question_total=current_question_total,
                            expansion_index=0,
                            expansion_total=max(1, current_expansion_total) if current_expansion_total else 0,
                            repeat_index=0,
                            repeat_total=max(1, manual_cfg.repeat_count),
                            current_label="現在: 実行開始前のエラーを反映しています",
                            phase_label="状態: 開始失敗",
                        )
                        set_run_status(
                            "分析を開始できませんでした",
                            safe_error,
                            "入力内容と設定を見直してから再実行してください。問題が続く場合はログも確認してください。",
                        )
                        safely_run_ui(refresh_dashboard_surface)
                        safe_notify(f"分析を開始できませんでした: {safe_error}", color="negative")
                        set_progress_visibility(False)
                        safely_run_ui(lambda: set_run_button_busy(False))
                        safely_run_ui(lambda: set_action_button_states(True))

                async def on_run_cancel() -> None:
                    if not state["busy"]:
                        return
                    if state["cancel_requested"]:
                        safe_notify("停止はすでに受け付けています。現在の並列グループが終わるまでお待ちください。", color="warning")
                        return
                    state["cancel_requested"] = True
                    set_progress_state(
                        int(run_progress_tracker.get("completed") or 0),
                        int(run_progress_tracker.get("total_steps") or 0),
                        question_index=int(run_progress_tracker.get("question_index") or 0),
                        question_total=int(run_progress_tracker.get("question_total") or 0),
                        expansion_index=int(run_progress_tracker.get("expansion_index") or 0),
                        expansion_total=int(run_progress_tracker.get("expansion_total") or 0),
                        repeat_index=int(run_progress_tracker.get("repeat_index") or 0),
                        repeat_total=int(run_progress_tracker.get("repeat_total") or 0),
                        current_label="現在: 停止リクエストを送信しました",
                        phase_label="状態: 現在の並列グループが終わるのを待っています",
                    )
                    set_run_status(
                        "停止を受け付けました",
                        "現在の並列グループが終わり次第、この実行を止めます。",
                        "途中結果は current 面に反映しません。完了後に必要なら同じ条件で再実行してください。",
                    )
                    set_action_button_states(False)
                    safe_notify("停止を受け付けました。現在の並列グループが終わるまで少しお待ちください。", color="warning")

                async def on_batch_submit() -> None:
                    if state["busy"] or state["batch_busy"]:
                        return
                    if READONLY_DEMO_MODE:
                        ui.notify(readonly_demo_block_message("provider batch submit"), color="warning")
                        print(f"[kotomegane] {readonly_demo_block_message('provider batch submit')}", flush=True)
                        return
                    cfg = build_config_from_inputs(inputs, state["config"])
                    if notify_missing_required_fields(cfg, context="まとめて分析"):
                        return
                    batch_policy = resolve_run_policy(cfg, "batch")
                    provider = get_provider_option(cfg.provider)
                    api_key_status = get_api_key_status(cfg.provider)
                    if not batch_policy.allowed:
                        ui.notify(batch_policy.blocked_reason or "まとめて分析は現在この接続先では未対応です。", color="warning")
                        return
                    if not api_key_status.present:
                        ui.notify(f"{api_key_status.env_var} が未設定です。.env または環境変数に設定してください。", color="negative")
                        return
                    credit_units = _kotomegane_credit_units(cfg.provider)
                    if not await _ensure_usage_credit_available("kotomegane", units=credit_units):
                        return
                    budget_guardrail = _load_budget_guardrail(cfg)
                    if budget_guardrail["should_block"]:
                        ui.notify(
                            "日次上限を超える見込みのため、まとめて分析を止めました。質問数、回数、または上限設定を見直してください。",
                            color="negative",
                        )
                        return
                    if budget_guardrail["status"] == "warning" and budget_guardrail["daily_budget_usd"] > 0:
                        ui.notify(
                            "今回のまとめて分析は日次上限に近いか超える見込みです。必要なら回数を絞ってください。",
                            color="warning",
                        )
                    if budget_guardrail["run_guardrail_should_block"]:
                        ui.notify(
                            "今回のまとめて分析は 1 回の実行あたりの内部上限を超える見込みです。質問数か回数を絞ってください。",
                            color="negative",
                        )
                        return

                    state["config"] = cfg
                    save_config(cfg)
                    refresh_runtime_panels_if_visible()
                    state["batch_busy"] = True
                    page_refreshers.update_batch_status_panel(
                        batch_status_label,
                        batch_summary_label,
                        "まとめて分析を開始しています",
                        "質問ごとにまとめた順で処理を作成しています。",
                    )
                    set_action_button_states(False)
                    current_question_set = db.get_question_set(question_set_select.value) if question_set_select.value else None
                    run_id = db.create_run_session(
                        cfg.repeat_count,
                        cfg.model,
                        cfg.prompt_cache_key,
                        run_mode="batch",
                        config_json=json.dumps(cfg.model_dump(), ensure_ascii=False),
                        question_set_id=str(current_question_set.get("question_set_id") or "") if current_question_set else "",
                        question_set_name=str(current_question_set.get("name") or "") if current_question_set else "",
                    )
                    try:
                        query_plans = await prepare_query_plans_for_run(
                            db,
                            query_planner,
                            run_id,
                            cfg,
                            run_mode="batch",
                        )
                        execution_plan: ExecutionPlan = build_execution_plan(query_plans, cfg)
                        budget_guardrail = _load_budget_guardrail(
                            cfg,
                            planned_request_count=execution_plan.total_request_count,
                        )
                        if budget_guardrail["should_block"]:
                            db.finish_run_session(run_id)
                            state["batch_busy"] = False
                            page_refreshers.update_batch_status_panel(
                                batch_status_label,
                                batch_summary_label,
                                "まとめて分析を開始しませんでした",
                                "実際の送信件数で見積もると日次上限を超える見込みのため、投入を止めました。",
                            )
                            set_action_button_states(True)
                            ui.notify(
                                "実際の送信件数で見積もると日次上限を超える見込みのため、まとめて分析を止めました。",
                                color="negative",
                            )
                            return
                        if budget_guardrail["run_guardrail_should_block"]:
                            db.finish_run_session(run_id)
                            state["batch_busy"] = False
                            page_refreshers.update_batch_status_panel(
                                batch_status_label,
                                batch_summary_label,
                                "まとめて分析を開始しませんでした",
                                "実際の送信件数で見積もると 1 回の実行上限を超える見込みのため、投入を止めました。",
                            )
                            set_action_button_states(True)
                            ui.notify(
                                "今回のまとめて分析は実際の送信件数ベースで 1 回の実行上限を超える見込みです。質問数か回数を絞ってください。",
                                color="negative",
                            )
                            return
                        if budget_guardrail["would_exceed_run_guardrail"]:
                            ui.notify(
                                "実際の送信件数では 1 回の実行上限を超える見込みです。現在の設定は「上限を超えても止めずに続ける」ため、このまま投入を続行します。",
                                color="warning",
                            )
                        batch_cfg = cfg.model_copy(
                            update={
                                "keywords": [request.executed_query for request in execution_plan.requests],
                                "repeat_count": 1,
                            }
                        )
                        request_contexts = [
                            {
                                "custom_id": build_batch_item_custom_id(
                                    run_id,
                                    request_index,
                                    request.iteration_index,
                                ),
                                "query_plan_id": request.query_plan_id,
                                "user_query_raw": request.user_query_raw,
                                "executed_query": request.executed_query,
                                "executed_query_index": request.executed_query_index,
                                "iteration_index": request.iteration_index,
                            }
                            for request_index, request in enumerate(execution_plan.requests, start=1)
                        ]
                        provider_client = build_provider_client(cfg.provider)
                        batch_handle, request_items = await asyncio.to_thread(
                            provider_client.submit_batch,
                            batch_cfg,
                            request_contexts,
                        )
                        db.update_query_plans_batch_context(
                            run_id,
                            provider_batch_id=batch_handle.batch_job_id,
                            provider_batch_mode="provider_batch",
                        )
                        db.create_batch_job(
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
                        page_refreshers.refresh_batch_job_admin_views(
                            db,
                            batch_job_select,
                            batch_job_table,
                            batch_status_label,
                            batch_summary_label,
                            selected_batch_job_id=str(batch_handle.batch_job_id),
                        )
                        if current_question_set:
                            db.touch_question_set_run(
                                str(current_question_set.get("question_set_id") or ""),
                                run_mode="batch",
                            )
                        batch_credit_debited = await _consume_usage_credit_after_success(
                            service_key="kotomegane",
                            action_key="batch_submit",
                            attempt_id=str(batch_handle.batch_job_id),
                            units=credit_units,
                            metadata={
                                "provider": cfg.provider,
                                "run_mode": "batch",
                                "provider_batch_id": str(batch_handle.batch_job_id),
                            },
                        )
                        if not batch_credit_debited:
                            page_refreshers.update_batch_status_panel(
                                batch_status_label,
                                batch_summary_label,
                                "まとめて分析を投入しましたが、クレジット消費を確認できませんでした",
                                "管理者へ連絡してください。",
                            )
                            return
                        ui.notify("まとめて分析を開始しました。進み具合を更新するか、完了結果を反映してください。", color="positive")
                    except Exception as exc:
                        db.finish_run_session(run_id)
                        safe_error = runtime_common.sanitize_runtime_error_message(exc)
                        page_refreshers.update_batch_status_panel(
                            batch_status_label,
                            batch_summary_label,
                            "まとめて分析の開始に失敗しました",
                            safe_error,
                        )
                        ui.notify(f"まとめて分析の開始に失敗しました: {safe_error}", color="negative")
                    finally:
                        state["batch_busy"] = False
                        set_action_button_states(True)

                async def on_batch_refresh() -> None:
                    if state["busy"] or state["batch_busy"]:
                        return
                    if READONLY_DEMO_MODE:
                        ui.notify(readonly_demo_block_message("provider batch retrieve"), color="warning")
                        print(f"[kotomegane] {readonly_demo_block_message('provider batch retrieve')}", flush=True)
                        return
                    batch_job_id = batch_job_select.value
                    if not batch_job_id:
                        ui.notify("進み具合を見る対象を選択してください。", color="warning")
                        return
                    batch_job = db.get_batch_job(batch_job_id)
                    if not batch_job:
                        ui.notify("選択したまとめて分析がローカルDBにありません。", color="warning")
                        return

                    state["batch_busy"] = True
                    provider_label = provider_display_label(get_provider_option(str(batch_job.get("provider_key") or "openai")))
                    page_refreshers.update_batch_status_panel(
                        batch_status_label,
                        batch_summary_label,
                        f"{provider_label} の進み具合を更新しています",
                        "選択したまとめて分析の進み具合を確認しています。",
                    )
                    set_action_button_states(False)
                    try:
                        provider_client = build_provider_client(batch_job["provider_key"])
                        batch_handle = await asyncio.to_thread(provider_client.retrieve_batch, batch_job_id)
                        error_messages = []
                        raw_errors = ((batch_handle.raw_batch or {}).get("errors") or {}).get("data") or []
                        for item in raw_errors:
                            if isinstance(item, dict) and item.get("message"):
                                error_messages.append(str(item["message"]))
                        db.update_batch_job_status(
                            batch_job_id,
                            status=batch_handle.status,
                            output_file_id=batch_handle.output_file_id,
                            error_file_id=batch_handle.error_file_id,
                            request_counts_total=batch_handle.request_counts_total or int(batch_job.get("request_count") or 0),
                            request_counts_completed=batch_handle.request_counts_completed,
                            request_counts_failed=batch_handle.request_counts_failed,
                            last_error=" / ".join(error_messages[:2]),
                        )
                        page_refreshers.refresh_batch_job_admin_views(
                            db,
                            batch_job_select,
                            batch_job_table,
                            batch_status_label,
                            batch_summary_label,
                        )
                        ui.notify("まとめて分析の進み具合を更新しました。", color="positive")
                    except Exception as exc:
                        safe_error = runtime_common.sanitize_runtime_error_message(exc)
                        page_refreshers.update_batch_status_panel(
                            batch_status_label,
                            batch_summary_label,
                            "進み具合の更新に失敗しました",
                            safe_error,
                        )
                        ui.notify(f"進み具合の更新に失敗しました: {safe_error}", color="negative")
                    finally:
                        state["batch_busy"] = False
                        set_action_button_states(True)

                async def on_batch_import() -> None:
                    if state["busy"] or state["batch_busy"]:
                        return
                    if READONLY_DEMO_MODE:
                        ui.notify(readonly_demo_block_message("provider batch retrieve/import"), color="warning")
                        print(f"[kotomegane] {readonly_demo_block_message('provider batch retrieve/import')}", flush=True)
                        return
                    batch_job_id = batch_job_select.value
                    if not batch_job_id:
                        ui.notify("結果を反映する対象を選択してください。", color="warning")
                        return
                    batch_job = db.get_batch_job(batch_job_id)
                    if not batch_job:
                        ui.notify("選択したまとめて分析がローカルDBにありません。", color="warning")
                        return

                    state["batch_busy"] = True
                    provider_label = provider_display_label(get_provider_option(str(batch_job.get("provider_key") or "openai")))
                    page_refreshers.update_batch_status_panel(
                        batch_status_label,
                        batch_summary_label,
                        "結果を反映しています",
                        f"{provider_label} の結果ファイルを確認しています。",
                    )
                    set_action_button_states(False)
                    try:
                        provider_client = build_provider_client(batch_job["provider_key"])
                        batch_handle = await asyncio.to_thread(provider_client.retrieve_batch, batch_job_id)
                        error_messages = []
                        raw_errors = ((batch_handle.raw_batch or {}).get("errors") or {}).get("data") or []
                        for item in raw_errors:
                            if isinstance(item, dict) and item.get("message"):
                                error_messages.append(str(item["message"]))
                        db.update_batch_job_status(
                            batch_job_id,
                            status=batch_handle.status,
                            output_file_id=batch_handle.output_file_id,
                            error_file_id=batch_handle.error_file_id,
                            request_counts_total=batch_handle.request_counts_total or int(batch_job.get("request_count") or 0),
                            request_counts_completed=batch_handle.request_counts_completed,
                            request_counts_failed=batch_handle.request_counts_failed,
                            last_error=" / ".join(error_messages[:2]),
                        )
                        cfg_snapshot = AppConfig.model_validate_json(batch_job["config_json"])
                        if not should_allow_batch_import(
                            {
                                **batch_job,
                                "status": batch_handle.status,
                                "request_counts_completed": batch_handle.request_counts_completed,
                                "request_counts_failed": batch_handle.request_counts_failed,
                            },
                            cfg_snapshot,
                        ):
                            page_refreshers.refresh_batch_job_admin_views(
                                db,
                                batch_job_select,
                                batch_job_table,
                                batch_status_label,
                                batch_summary_label,
                            )
                            ui.notify("まだ全件待機中です。時間切れ後の暫定表示か完了後に再度お試しください。", color="warning")
                            return
                        if not batch_handle.output_file_id and not batch_handle.error_file_id:
                            page_refreshers.refresh_batch_job_admin_views(
                                db,
                                batch_job_select,
                                batch_job_table,
                                batch_status_label,
                                batch_summary_label,
                            )
                            ui.notify("まだ取り込める結果ファイルがありません。状態確認後に再度お試しください。", color="warning")
                            return

                        item_rows = db.list_batch_job_items(batch_job_id)
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
                                result_id = db.save_keyword_result(
                                    run_id=batch_job["run_id"],
                                    iteration_index=int(item_row["iteration_index"]),
                                    result=record.result,
                                    query_plan_id=str(item_row.get("query_plan_id") or ""),
                                    display_query_raw=str(item_row.get("user_query_raw") or item_row["keyword_raw"]),
                                    executed_query=str(item_row.get("executed_query") or item_row["keyword_raw"]),
                                    executed_query_index=int(item_row.get("executed_query_index") or 1),
                                )
                                db.mark_batch_job_item_processed(
                                    batch_job_id,
                                    record.custom_id,
                                    status="imported",
                                    response_status_code=record.response_status_code,
                                    remote_request_id=record.remote_request_id,
                                    imported_result_id=result_id,
                                )
                                new_successes += 1
                                continue

                            error_result = runtime_common.build_error_result(
                                str(item_row.get("executed_query") or item_row["keyword_raw"]),
                                record.error_text,
                                cfg_snapshot,
                            )
                            safe_error = runtime_common.sanitize_runtime_error_message(record.error_text)
                            error_result.output_json["analysis_context"] = {
                                **(error_result.output_json.get("analysis_context") or {}),
                                "question": str(item_row.get("executed_query") or item_row["keyword_raw"]),
                                "user_query_raw": str(item_row.get("user_query_raw") or item_row["keyword_raw"]),
                                "executed_query": str(item_row.get("executed_query") or item_row["keyword_raw"]),
                            }
                            result_id = db.save_keyword_result(
                                run_id=batch_job["run_id"],
                                iteration_index=int(item_row["iteration_index"]),
                                result=error_result,
                                error_text=safe_error,
                                query_plan_id=str(item_row.get("query_plan_id") or ""),
                                display_query_raw=str(item_row.get("user_query_raw") or item_row["keyword_raw"]),
                                executed_query=str(item_row.get("executed_query") or item_row["keyword_raw"]),
                                executed_query_index=int(item_row.get("executed_query_index") or 1),
                            )
                            db.mark_batch_job_item_processed(
                                batch_job_id,
                                record.custom_id,
                                status="imported_error",
                                response_status_code=record.response_status_code,
                                remote_request_id=record.remote_request_id,
                                imported_result_id=result_id,
                                error_text=safe_error,
                            )
                            new_errors += 1

                        final_items = db.list_batch_job_items(batch_job_id)
                        imported_result_count = sum(1 for row in final_items if row.get("status") == "imported")
                        imported_error_count = sum(1 for row in final_items if row.get("status") == "imported_error")
                        db.mark_batch_job_imported(
                            batch_job_id,
                            imported_result_count=imported_result_count,
                            imported_error_count=imported_error_count,
                        )
                        if (
                            batch_handle.status in {"completed", "expired", "cancelled", "failed"}
                            and imported_result_count + imported_error_count >= int(batch_job.get("request_count") or 0)
                        ):
                            db.finish_run_session(batch_job["run_id"])

                        page_refreshers.refresh_batch_job_admin_views(
                            db,
                            batch_job_select,
                            batch_job_table,
                            batch_status_label,
                            batch_summary_label,
                        )
                        state["show_primary_results"] = True
                        state["current_result_run_id"] = str(batch_job["run_id"] or "")
                        refresh_result_sections()
                        expand_current_result_surface()
                        if new_successes or new_errors:
                            ui.notify(
                                f"まとめて分析の結果を反映しました。成功 {new_successes} 件 / エラー {new_errors} 件。",
                                color="positive" if new_errors == 0 else "warning",
                            )
                        else:
                            ui.notify("新しく反映できるまとめて分析の結果はありませんでした。", color="warning")
                    except Exception as exc:
                        safe_error = runtime_common.sanitize_runtime_error_message(exc)
                        page_refreshers.update_batch_status_panel(
                            batch_status_label,
                            batch_summary_label,
                            "結果の反映に失敗しました",
                            safe_error,
                        )
                        ui.notify(f"結果の反映に失敗しました: {safe_error}", color="negative")
                    finally:
                        state["batch_busy"] = False
                        set_action_button_states(True)

                batch_submit_button = None
                batch_status_button = None
                batch_import_button = None
                save_button = None
                run_button = None
                cancel_run_button = None
                quick_saved_open_button = None
                quick_batch_open_button = None
                quick_schedule_open_button = None
                question_set_new_save_button = None
                question_set_save_button = None
                question_set_archive_button = None
                schedule_save_button = None
                schedule_duplicate_button = None
                schedule_delete_button = None
                schedule_delete_confirm_button = None
                cluster_brief_generate_button = None
                export_button = None

                with action_button_row:
                    with ui.row().classes("w-full items-center justify-start gap-3 flex-wrap"):
                        run_button = ui.button("合計20回答を確認", on_click=on_run).props("unelevated no-caps color=orange-8 text-color=white").classes(
                            readonly_button_classes("accent-button primary-run-button text-[18px] font-bold")
                        ).style(readonly_button_style(SUITE_ACCENT_BUTTON_STYLE))
                        ui.label(
                            "確認用モードのため実行できません。"
                            if READONLY_DEMO_MODE
                            else "このボタンで対象AIへ、合計20回答を目安に質問を送信します。"
                        ).classes(
                            "readonly-demo-helper text-[13px] leading-5"
                            if READONLY_DEMO_MODE
                            else "text-[13px] leading-5 text-helper"
                        )
                        cancel_run_button = ui.button("分析を停止", on_click=on_run_cancel).props("outline no-caps color=brown-8").classes("text-[16px] font-bold")
                        cancel_run_button.visible = False
                    with ui.column().classes("followup-cta-panel w-full gap-2"):
                        with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                            ui.icon("timeline").classes("text-[18px] text-support")
                            ui.label("保存済み条件から見る").classes("followup-cta-title")
                            ui.label("画面を開くだけです。対象AIへ送信する操作ではありません。").classes("followup-cta-note")
                        with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                            quick_saved_open_button = ui.button(
                                "保存済み条件を見る",
                                on_click=lambda _=None: (
                                    open_support_surface(support_settings_tab, "saved"),
                                ),
                            ).props("outline no-caps color=brown-8 href=#saved-condition-section data-km-shortcut-target=saved-condition-section").classes("secondary-button followup-button text-[14px] font-bold").style(SUITE_SECONDARY_BUTTON_STYLE)
                            quick_saved_open_button.tooltip("保存しておいた質問条件を確認・編集します。ここではAIへの送信は行いません。")
                            quick_batch_open_button = ui.button(
                                "まとめて分析を見る",
                                on_click=lambda _=None: (
                                    open_support_surface(support_settings_tab, "batch"),
                                ),
                            ).props("outline no-caps color=brown-8 href=#batch-settings-section data-km-shortcut-target=batch-settings-section").classes("secondary-button followup-button text-[14px] font-bold").style(SUITE_SECONDARY_BUTTON_STYLE)
                            quick_batch_open_button.tooltip("保存済み条件の複数質問を、今回1回だけまとめて実行したいときに使います。")
                            quick_schedule_open_button = ui.button(
                                "曜日を決めて自動チェック",
                                on_click=lambda _=None: (
                                    open_support_surface(support_settings_tab, "schedule"),
                                ),
                            ).props("outline no-caps color=brown-8 href=#schedule-settings-section data-km-shortcut-target=schedule-settings-section").classes("secondary-button followup-button text-[14px] font-bold").style(SUITE_SECONDARY_BUTTON_STYLE)
                            quick_schedule_open_button.tooltip("保存済み条件を、指定した曜日・時刻に継続して自動実行したいときに使います。")

                def set_run_button_busy(is_busy: bool) -> None:
                    if run_button is None:
                        return
                    run_button.set_text("分析中..." if is_busy else "合計20回答を確認")
                    run_button.update()

                def set_action_button_states(enabled: bool) -> None:
                    def _apply_button_states() -> None:
                        controls = [run_button]
                        if save_button is not None:
                            controls.append(save_button)
                        controls.extend(
                            control
                            for control in [quick_saved_open_button, quick_batch_open_button, quick_schedule_open_button]
                            if control is not None
                        )
                        controls.extend(
                            control
                            for control in [batch_submit_button, batch_status_button, batch_import_button]
                            if control is not None
                        )
                        readonly_blocked_controls = [
                            control
                            for control in [
                                run_button,
                                batch_submit_button,
                                batch_status_button,
                                batch_import_button,
                                save_button,
                                question_set_new_save_button,
                                question_set_save_button,
                                question_set_archive_button,
                                schedule_save_button,
                                schedule_duplicate_button,
                                schedule_delete_button,
                                schedule_delete_confirm_button,
                                cluster_brief_generate_button,
                                export_button,
                            ]
                            if control is not None
                        ]
                        if READONLY_DEMO_MODE:
                            controls.extend(readonly_blocked_controls)
                        unique_controls = []
                        seen_control_ids: set[int] = set()
                        for control in controls:
                            if control is None or id(control) in seen_control_ids:
                                continue
                            seen_control_ids.add(id(control))
                            unique_controls.append(control)
                        for control in unique_controls:
                            if READONLY_DEMO_MODE and control in readonly_blocked_controls:
                                control.disable()
                            elif enabled:
                                control.enable()
                            else:
                                control.disable()
                        if cancel_run_button is not None:
                            cancel_run_button.visible = bool(state["busy"])
                            if state["busy"]:
                                cancel_run_button.enable()
                            else:
                                cancel_run_button.disable()
                            cancel_run_button.update()

                    safely_run_ui(_apply_button_states)

        recent_rows: list[dict[str, Any]] = []
        query_rollup_rows: list[dict[str, Any]] = []
        portfolio_story = dashboard_views.build_portfolio_story(query_rollup_rows, state["config"])
        intent_rows: list[dict[str, Any]] = []
        page_gap_rows: list[dict[str, Any]] = []
        current_result_story = dashboard_views.build_current_result_story(
            query_rollup_rows,
            recent_rows,
            state["config"],
            db.list_sources,
        )
        with ui.column().classes("w-full order-20").props("id=result-stage") as result_stage_container:
            pass
        latest_result_container = ui.column().classes("w-full gap-5 order-21")
        with ui.card().classes("section-card p-5 w-full order-30"):
            with ui.row().classes("w-full gap-3 items-start justify-between flex-wrap"):
                with ui.column().classes("gap-1 flex-1 min-w-[260px]"):
                    ui.label("観測の推移").classes("summary-eyebrow")
                    ui.label("自社引用率 / 外部先行率").classes(
                        "section-font section-title text-[22px] font-bold"
                    )
                with ui.column().classes("gap-1 items-end min-w-[180px]"):
                    hero_trend_refs["latest_rate"] = ui.label("--").classes(
                        "section-font text-[28px] font-bold text-brand"
                    )
                    ui.label("最新 自社引用率").classes("text-[12px] text-helper")
            tracked_seed_rows_initial = dashboard_views.filter_rows_for_tracking_series(recent_rows)
            hero_trend_refs["plot"] = ui.plotly(
                charts.build_visibility_focus_chart(
                    tracked_seed_rows_initial,
                    state["config"],
                )
            ).classes("w-full h-[240px] mt-2")
            with ui.row().classes("w-full gap-3 mt-2 flex-wrap items-center"):
                hero_trend_refs["hint"] = ui.label(
                    "まだ自動チェックの履歴がありません。"
                ).classes("text-[12px] leading-5 text-helper flex-1")
            ui.label("下部で自動チェックをセットすると時系列分析が可能になります。").classes(
                "text-[12px] leading-5 text-helper mt-1"
            )
        with ui.column().classes("w-full order-40").props("id=detail-stage"):
            pass
        with ui.card().classes("section-card p-5 w-full order-41"):
            with ui.expansion("詳細と設定を開く").classes("w-full panel-card semantic-settings-expansion") as support_result_expansion:
                with ui.column().classes("p-4 gap-5 w-full"):
                    with ui.tabs().classes("detail-tabs-shell w-full") as support_tabs:
                        support_result_tab = ui.tab("今回の結果")
                        support_analysis_tab = ui.tab("自動チェックの推移")
                        support_research_tab = ui.tab("まとめて分析")
                        support_settings_tab = ui.tab("設定")
                    with ui.tab_panels(support_tabs, value=support_result_tab).classes("detail-tab-panels w-full mt-4"):
                        with ui.tab_panel(support_settings_tab).classes("px-0 py-2"):
                            with ui.row().classes("settings-overview-row w-full gap-5 flex-wrap items-start"):
                                with ui.card().classes("section-card settings-provider-card p-5 flex-1 min-w-[260px]"):
                                    with ui.expansion("対象AIを設定").classes("w-full panel-card"):
                                        with ui.column().classes("p-4 gap-3 w-full"):
                                            ui.label("分析対象として使うAIを選びます。ここは結果の見え方とは分けて置いています。").classes(
                                                "text-[13px] leading-6 soft-label"
                                            )
                                            with ui.row().classes("provider-chip-rail w-full mt-2"):
                                                for provider in get_visible_provider_catalog(state["config"]):
                                                    button = ui.button(
                                                        provider_display_label(provider),
                                                        on_click=lambda _=None, provider_key=provider.key: set_provider(provider_key),
                                                    ).props("unelevated no-caps").classes("provider-chip-button")
                                                    provider_buttons[provider.key] = button
                                            refresh_provider_ui(update_hero=False)
                                with ui.card().classes("section-card settings-saved-card p-5 flex-1 min-w-[620px] semantic-saved-panel").props("id=saved-condition-section"):
                                    with ui.expansion("保存済み条件", value=True).classes("w-full panel-card"):
                                        with ui.column().classes("p-4 gap-3 w-full"):
                                            ui.label(
                                                "今の入力を再利用したいときは、ここで保存済み条件に登録します。"
                                                " まとめて分析と自動チェックは、この保存済み条件から対象を選びます。"
                                            ).classes("text-[13px] leading-6 soft-label")
                                            with ui.row().classes("w-full gap-3 flex-wrap"):
                                                with ui.column().classes("input-field-card flex-1 min-w-[220px] gap-1"):
                                                    ui.label("今の入力 -> 保存済み条件").classes("summary-eyebrow")
                                                    ui.label("入力内容を保存して、あとで再利用します。").classes("text-[13px] leading-5 text-helper")
                                                with ui.column().classes("input-field-card flex-1 min-w-[220px] gap-1"):
                                                    ui.label("保存済み条件 -> 今回だけ").classes("summary-eyebrow")
                                                    ui.label("まとめて分析で、保存した複数質問を今回だけ送信します。").classes("text-[13px] leading-5 text-helper")
                                                with ui.column().classes("input-field-card flex-1 min-w-[220px] gap-1"):
                                                    ui.label("保存済み条件 -> 自動チェック").classes("summary-eyebrow")
                                                    ui.label("曜日と時刻を決め、同じ条件を継続的に確認します。").classes("text-[13px] leading-5 text-helper")
                                            if READONLY_DEMO_MODE:
                                                ui.label(
                                                    "確認用モードのため保存・更新・アーカイブ・再開はできません。"
                                                ).classes("readonly-demo-helper text-[13px] leading-5")
                                            question_set_name_input = ui.input("保存名", value="").props("outlined").classes("w-full")
                                            with ui.row().classes("w-full gap-3 mt-1 flex-wrap"):
                                                question_set_select = ui.select({}, value=None, label="保存済み条件").props("outlined").classes(
                                                    "w-[280px] flex-1"
                                                )
                                                question_set_new_save_button = ui.button("今の入力を保存", on_click=on_question_set_new_save).props(
                                                    "unelevated no-caps color=orange-8 text-color=white"
                                                ).classes(readonly_button_classes("accent-button text-[16px] font-bold")).style(readonly_button_style(SUITE_ACCENT_BUTTON_STYLE))
                                                question_set_save_button = ui.button("選択中の保存済み条件を更新", on_click=on_question_set_save).props("outline color=brown-8").classes(
                                                    readonly_button_classes("secondary-button text-[16px]")
                                                ).style(readonly_button_style(SUITE_SECONDARY_BUTTON_STYLE))
                                                ui.button("保存済みを読み込む", on_click=on_question_set_load).props("outline color=brown-8").classes(
                                                    "secondary-button text-[16px]"
                                                ).style(SUITE_SECONDARY_BUTTON_STYLE)
                                                question_set_archive_button = ui.button("アーカイブ / 再開", on_click=on_question_set_archive_toggle).props("outline color=brown-8").classes(
                                                    readonly_button_classes("secondary-button text-[16px]")
                                                ).style(readonly_button_style(SUITE_SECONDARY_BUTTON_STYLE))
                                                save_button = ui.button("画面の入力だけ保持", on_click=on_save).props("outline color=brown-8").classes(
                                                    readonly_button_classes("secondary-button text-[16px]")
                                                ).style(readonly_button_style(SUITE_SECONDARY_BUTTON_STYLE))
                                            question_set_detail_label = ui.label(
                                                "保存済み条件を選ぶと、質問数・対象AI・最後の結果保存時刻をここに表示します。"
                                            ).classes("text-[12px] leading-5 text-helper")
                                            question_set_table = ui.table(
                                                columns=admin_views.build_question_set_table_columns(),
                                                rows=[],
                                                row_key="question_set_id",
                                                pagination=5,
                                            ).props(TABLE_BASE_PROPS).classes("w-full mt-2")

                            with ui.row().classes("w-full gap-5 mt-5 flex-wrap items-start"):
                                with ui.card().classes("section-card p-5 w-full"):
                                    with ui.expansion("今回だけまとめて分析｜保存済み条件を今回だけ実行").classes("w-full panel-card").props("id=batch-settings-section") as batch_settings_expansion:
                                        with ui.column().classes("p-4 gap-3 w-full"):
                                            ui.label(
                                                "上の保存済み条件を入力へ読み込んでから、複数質問を今回だけ実行します。"
                                                "1件だけなら上の「1回だけ分析」で十分です。"
                                            ).classes("text-[13px] leading-6 soft-label")
                                            if READONLY_DEMO_MODE:
                                                ui.label("確認用モードのため実行できません。").classes(
                                                    "readonly-demo-helper text-[13px] leading-5"
                                                )
                                            ui.label(
                                                "手順: 保存済み条件を選ぶ -> 保存済みを読み込む -> まとめて分析を開始。"
                                                " 下の一覧は過去のまとめて分析・自動チェック履歴です。"
                                            ).classes("text-[13px] leading-6 text-helper")
                                            ui.label("ここで出す割合はバッチジョブ数ではなく、対象質問数を分母にして読みます。").classes(
                                                "text-[13px] leading-6 text-helper"
                                            )
                                            batch_status_label = ui.label("まだまとめて分析の履歴はありません").classes(
                                                "text-[15px] font-bold text-main mt-1"
                                            )
                                            batch_summary_label = ui.label(
                                                "保存済み条件を入力へ読み込み、複数質問をまとめて対象AIへ送信します。"
                                            ).classes("text-[13px] text-helper mt-1")
                                            with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
                                                batch_submit_button = ui.button("まとめて分析を開始", on_click=on_batch_submit).props(
                                                    "unelevated no-caps color=orange-8 text-color=white"
                                                ).classes(readonly_button_classes("accent-button text-[16px] font-bold")).style(readonly_button_style(SUITE_ACCENT_BUTTON_STYLE))
                                                ui.label(
                                                    "確認用モードのため実行できません。"
                                                    if READONLY_DEMO_MODE
                                                    else "今の入力に読み込んだ保存済み条件を対象AIへまとめて送信します。"
                                                ).classes(
                                                    "readonly-demo-helper text-[13px] leading-5 self-center"
                                                    if READONLY_DEMO_MODE
                                                    else "text-[13px] leading-5 text-helper self-center"
                                                )
                                                batch_status_button = ui.button("進み具合を更新", on_click=on_batch_refresh).props(
                                                    "outline color=brown-8"
                                                ).classes(readonly_button_classes("secondary-button text-[16px]")).style(readonly_button_style(SUITE_SECONDARY_BUTTON_STYLE))
                                                batch_import_button = ui.button("完了結果を反映", on_click=on_batch_import).props(
                                                    "outline color=brown-8"
                                                ).classes(readonly_button_classes("secondary-button text-[16px]")).style(readonly_button_style(SUITE_SECONDARY_BUTTON_STYLE))
                                                ui.label(
                                                    "確認用モードのため状態確認・結果反映はできません。"
                                                    if READONLY_DEMO_MODE
                                                    else "完了した外部AI結果をこの画面へ反映します。"
                                                ).classes(
                                                    "readonly-demo-helper text-[13px] leading-5 self-center"
                                                    if READONLY_DEMO_MODE
                                                    else "text-[13px] leading-5 text-helper self-center"
                                                )
                                            batch_job_select = ui.select(
                                                {},
                                                value=None,
                                                label="過去のまとめて分析・自動チェック履歴",
                                                on_change=lambda _: admin_views.refresh_batch_job_views(
                                                    db,
                                                    batch_job_select,
                                                    batch_job_table,
                                                    batch_status_label,
                                                    batch_summary_label,
                                                ),
                                            ).props("outlined").classes("w-full mt-2")
                                            batch_job_table = ui.table(
                                                columns=admin_views.build_batch_table_columns(),
                                                rows=[],
                                                row_key="batch_job_id",
                                                pagination=8,
                                            ).props(TABLE_BASE_PROPS).classes("w-full mt-2")

                            with ui.row().classes("w-full gap-5 mt-5 flex-wrap items-start"):
                                with ui.card().classes("section-card p-5 flex-1 min-w-[420px] semantic-schedule-panel"):
                                    with ui.expansion("曜日を決めて自動チェック").classes("w-full panel-card").props("id=schedule-settings-section") as schedule_settings_expansion:
                                        with ui.column().classes("p-4 gap-3 w-full"):
                                            ui.label(
                                                "保存済み条件を、指定した曜日と時刻に自動チェックします。"
                                                " 順番は「対象 -> 曜日 -> 時刻 -> 有効 -> 保存」です。"
                                            ).classes("text-[13px] leading-6 soft-label")
                                            if READONLY_DEMO_MODE:
                                                ui.label("確認用モードのため自動チェックの保存・複製・削除はできません。").classes(
                                                    "readonly-demo-helper text-[13px] leading-5"
                                                )
                                            with ui.row().classes("w-full gap-2 flex-wrap"):
                                                scheduler_status_label = ui.label(admin_views.build_scheduler_status_text(scheduler_service)).classes(
                                                    "signal-chip signal-neutral"
                                                )
                                                schedule_setting_status_label = ui.label("この予定: 有効").classes("signal-chip signal-neutral")
                                            ui.label(
                                                "アプリ側の監視が停止中でも、保存した予定の有効/停止は別状態です。"
                                                " 停止中の予定はため込まず、次回起動後に直近1回分だけ実行します。"
                                            ).classes("text-[12px] leading-5 text-helper")
                                            with ui.column().classes("input-field-card w-full gap-2 mt-1"):
                                                ui.label("1. 対象").classes("summary-eyebrow")
                                                schedule_question_set_select = ui.select({}, value=None, label="自動チェックの対象").props("outlined").classes(
                                                    "w-full"
                                                )
                                                schedule_target_summary_label = ui.label(
                                                    "自動チェックは保存済み条件から選びます。"
                                                ).classes("text-[12px] leading-5 text-helper")
                                                schedule_name_input = ui.input("自動チェック名", value="").props("outlined").classes("w-full")
                                                ui.label("空欄なら対象の保存名から自動で名前を付けます。").classes("text-[12px] leading-5 text-helper")
                                            with ui.row().classes("w-full gap-3 mt-1 flex-wrap items-start"):
                                                with ui.column().classes("input-field-card flex-[1.2] min-w-[280px] gap-2"):
                                                    ui.label("2. 曜日").classes("summary-eyebrow")
                                                    schedule_weekdays_select = WeekdayCheckboxGroup()
                                                    with ui.row().classes("weekday-checkbox-row w-full gap-2 flex-wrap"):
                                                        for weekday_key, weekday_label in (
                                                            ("0", "月"),
                                                            ("1", "火"),
                                                            ("2", "水"),
                                                            ("3", "木"),
                                                            ("4", "金"),
                                                            ("5", "土"),
                                                            ("6", "日"),
                                                        ):
                                                            checkbox = ui.checkbox(weekday_label, value=weekday_key == "0").props("dense").classes(
                                                                "weekday-checkbox"
                                                            )
                                                            checkbox.on_value_change(lambda _=None: refresh_schedule_form_summary())
                                                            schedule_weekdays_select.add(weekday_key, checkbox)
                                                    schedule_week_count_label = ui.label("週あたり回数: 1回（曜日選択から自動計算）").classes(
                                                        "text-[13px] leading-5 text-main font-bold"
                                                    )
                                                with ui.column().classes("input-field-card flex-1 min-w-[220px] gap-2"):
                                                    ui.label("3. 時刻").classes("summary-eyebrow")
                                                    with ui.row().classes("w-full gap-3 flex-wrap"):
                                                        schedule_time_input = ui.input("時刻", value="09:00").props("outlined").classes("w-[120px] flex-1")
                                                        schedule_timezone_input = ui.input("タイムゾーン", value=state["config"].timezone).props("outlined").classes("w-[180px] flex-1")
                                                    schedule_save_time_label = ui.label("保存後の予定: 09:00 に自動チェック").classes(
                                                        "text-[13px] leading-5 text-helper"
                                                    )
                                                with ui.column().classes("input-field-card flex-1 min-w-[200px] gap-2"):
                                                    ui.label("4. 有効").classes("summary-eyebrow")
                                                    schedule_enabled_switch = ui.switch("有効", value=True)
                                                    schedule_enabled_switch.on_value_change(lambda _=None: refresh_schedule_form_summary())
                                                    schedule_enabled_helper_label = ui.label("ON: 予定時刻に自動チェック").classes("text-[12px] leading-5 text-helper")
                                            schedule_weekday_summary_label = ui.label("曜日: 月 / 週1回").classes("text-[14px] leading-6 text-main font-bold mt-1")
                                            schedule_time_input.on_value_change(lambda _=None: refresh_schedule_form_summary())
                                            with ui.row().classes("w-full gap-3 mt-2 flex-wrap"):
                                                schedule_save_button = ui.button("自動チェックを保存", on_click=on_schedule_save).props(
                                                    "unelevated no-caps color=orange-8 text-color=white"
                                                ).classes(readonly_button_classes("accent-button text-[16px] font-bold")).style(readonly_button_style(SUITE_ACCENT_BUTTON_STYLE))
                                                ui.label("5. 保存して、下の一覧で予定を確認します。").classes("text-[13px] leading-5 text-helper self-center")
                                            ui.label("保存済み自動チェック").classes("summary-eyebrow mt-3")
                                            schedule_table = ui.table(
                                                columns=admin_views.build_schedule_table_columns(),
                                                rows=[],
                                                row_key="schedule_id",
                                                pagination=6,
                                            ).props(TABLE_BASE_PROPS).classes("w-full mt-2")
                                            ui.label("複製直後は停止状態で保存します。").classes("text-[13px] leading-6 text-helper mt-2")
                                            schedule_manage_select = ui.select({}, value=None, label="保存済み自動チェックを管理").props("outlined").classes("w-full mt-2")
                                            with ui.row().classes("w-full gap-3 mt-2 flex-wrap"):
                                                ui.button("フォームに読み込み", on_click=on_schedule_load).props("outline color=brown-8").classes(
                                                    "secondary-button text-[15px]"
                                                ).style(SUITE_SECONDARY_BUTTON_STYLE)
                                                schedule_duplicate_button = ui.button("複製して AB 用に作る", on_click=on_schedule_duplicate).props("outline color=brown-8").classes(
                                                    readonly_button_classes("secondary-button text-[15px]")
                                                ).style(readonly_button_style(SUITE_SECONDARY_BUTTON_STYLE))
                                                schedule_delete_button = ui.button("削除", on_click=on_schedule_delete).props("outline color=brown-8").classes(
                                                    readonly_button_classes("secondary-button text-[15px]")
                                                ).style(readonly_button_style(SUITE_SECONDARY_BUTTON_STYLE))
                                            compare_mode_select = ui.select(
                                                {"schedule": "別の自動チェックと比較", "question_set": "別の保存済み条件と比較"},
                                                value="schedule",
                                                label="何と比べるか",
                                                on_change=lambda _: page_refreshers.refresh_schedule_admin_views(
                                                    db,
                                                    scheduler_service,
                                                    schedule_table,
                                                    scheduler_status_label,
                                                    schedule_manage_select,
                                                    compare_target_select,
                                                    compare_mode_select,
                                                ),
                                            ).props("outlined").classes("w-full mt-2")
                                            compare_target_select = ui.select({}, value=None, label="比較対象").props("outlined").classes("w-full mt-1")
                                            with ui.row().classes("w-full gap-3 mt-2 flex-wrap"):
                                                ui.button("差分を表示", on_click=on_schedule_diff_refresh).props("outline color=brown-8").classes(
                                                    "secondary-button text-[15px]"
                                                ).style(SUITE_SECONDARY_BUTTON_STYLE)
                                            schedule_diff_container = ui.column().classes("w-full mt-3 gap-3")
                                        with ui.dialog() as schedule_delete_dialog, ui.card().classes("card-detail p-5 w-[420px] max-w-full"):
                                            ui.label("この自動チェックを削除しますか").classes("section-font section-title text-[22px] font-bold")
                                            ui.label("定期設定だけを削除し、既存の実行履歴は残します。").classes(
                                                "text-[14px] leading-6 text-support mt-2"
                                            )
                                            with ui.row().classes("w-full justify-end gap-3 mt-5"):
                                                ui.button("キャンセル", on_click=schedule_delete_dialog.close).props("outline color=brown-8").classes(
                                                    "secondary-button text-[15px]"
                                                ).style(SUITE_SECONDARY_BUTTON_STYLE)
                                                schedule_delete_confirm_button = ui.button("削除する", on_click=confirm_schedule_delete).props(
                                                    "unelevated no-caps color=orange-8 text-color=white"
                                                ).classes(readonly_button_classes("accent-button text-[15px] font-bold")).style(readonly_button_style(SUITE_ACCENT_BUTTON_STYLE))

                            with ui.row().classes("w-full gap-5 mt-5 flex-wrap items-start"):
                                with ui.card().classes("section-card p-5 w-full"):
                                    with ui.expansion("レポート出力").classes("w-full panel-card"):
                                        with ui.column().classes("p-4 gap-3 w-full"):
                                            ui.label("共有したいときだけ CSV / JSON / 報告用Markdown を更新します。").classes("text-[13px] leading-6 soft-label")
                                            if READONLY_DEMO_MODE:
                                                ui.label("確認用モードのため出力ファイルは更新できません。").classes(
                                                    "readonly-demo-helper text-[13px] leading-5"
                                                )
                                            with ui.row().classes("w-full gap-3 mt-1 flex-wrap"):
                                                export_button = ui.button("レポートを更新", on_click=on_export).props("unelevated no-caps color=orange-8 text-color=white").classes(
                                                    readonly_button_classes("accent-button text-[16px] font-bold")
                                                ).style(readonly_button_style(SUITE_ACCENT_BUTTON_STYLE))
                                            export_status_label = ui.label("まだ export を生成していません。").classes(
                                                "text-[14px] text-helper mt-1"
                                            )
                                            export_table = ui.table(
                                                columns=admin_views.build_export_table_columns(),
                                                rows=[],
                                                row_key="label",
                                                pagination=5,
                                            ).props(TABLE_BASE_PROPS).classes("w-full mt-1")
                                            ui.label("報告用まとめプレビュー").classes("summary-eyebrow mt-3")
                                            report_preview_label = ui.label("まだ報告用まとめはありません。").classes(
                                                "text-[13px] leading-6 text-support whitespace-pre-wrap mt-1"
                                            )
                        with ui.tab_panel(support_research_tab).classes("px-0 py-2"):
                            with ui.column().classes("w-full gap-5"):
                                with ui.card().classes("section-card p-5 w-full"):
                                    ui.label("まとめて分析と自動チェック").classes("section-font section-title text-[26px] font-bold")
                                    ui.label(
                                        "LLMの見え方は日々揺れます。"
                                        "まとめて分析は保存済み条件を今回だけ確認し、自動チェックは曜日を決めて継続的に追う仕組みです。"
                                    ).classes("text-[14px] leading-6 soft-label mt-2")
                                    with ui.row().classes("w-full gap-4 mt-4 flex-wrap"):
                                        with ui.column().classes("input-field-card flex-1 min-w-[260px] gap-2"):
                                            ui.label("1回だけ確認").classes("ui-tone-chip")
                                            ui.label("1 問だけ、いま 1 回観測").classes(
                                                "section-font text-[16px] font-bold text-main"
                                            )
                                            ui.label("目の前の 1 質問で、AIが誰を引用しているかを今すぐ確認するときに使います。").classes(
                                                "text-[13px] leading-6 text-support"
                                            )
                                        with ui.column().classes("input-field-card flex-1 min-w-[260px] gap-2"):
                                            ui.label("まとめて分析").classes("ui-tone-chip")
                                            ui.label("保存した複数質問を、まとめて観測").classes(
                                                "section-font text-[16px] font-bold text-main"
                                            )
                                            ui.label("保存済み条件を一度に回し、いまの全体像を確認したいときに使います。").classes(
                                                "text-[13px] leading-6 text-support"
                                            )
                                        with ui.column().classes("input-field-card flex-1 min-w-[260px] gap-2"):
                                            ui.label("自動チェック").classes("ui-tone-chip")
                                            ui.label("曜日と時刻で、継続観測").classes(
                                                "section-font text-[16px] font-bold text-main"
                                            )
                                            ui.label("週次などの定点で予定し、自動チェックの推移タブで履歴を読むときに使います。").classes(
                                                "text-[13px] leading-6 text-support"
                                            )
                                    with ui.row().classes("w-full gap-3 mt-4 flex-wrap"):
                                        ui.button(
                                            "設定タブでまとめて分析を開く",
                                            on_click=lambda _=None: (
                                                open_support_surface(support_settings_tab, "batch"),
                                            ),
                                        ).props("unelevated no-caps color=orange-8 text-color=white href=#batch-settings-section data-km-shortcut-target=batch-settings-section").classes(
                                            "accent-button text-[16px] font-bold"
                                        ).style(SUITE_ACCENT_BUTTON_STYLE)
                                        ui.button(
                                            "自動チェックの推移を見る",
                                            on_click=lambda: open_support_surface(support_analysis_tab),
                                        ).props("outline color=brown-8").classes(
                                            "secondary-button text-[16px]"
                                        ).style(SUITE_SECONDARY_BUTTON_STYLE)
                                    ui.label(
                                        "まとめて分析と自動チェックの操作は設定タブに集約しています。"
                                        " 自動チェックの推移は専用タブのグラフに反映されます。"
                                    ).classes("text-[13px] leading-6 text-helper mt-4")
                        with ui.tab_panel(support_result_tab).classes("px-0 py-2"):
                            with ui.column().classes("w-full gap-5"):
                                with ui.card().classes("card-secondary current-scope-card p-5 w-full"):
                                    with ui.row().classes("w-full items-start justify-between gap-3 flex-wrap"):
                                        with ui.column().classes("gap-1 min-w-[260px]"):
                                            ui.label("今回の結果").classes("result-scope-eyebrow")
                                            ui.label("今回だけの整理").classes("section-font section-title text-[26px] font-bold")
                                        summary_refs["current_scope_status"] = ui.label("今の入力では未分析").classes("scope-status-chip current-status-chip")
                                    summary_refs["current_scope_note"] = ui.label(
                                        "今の入力ではまだ分析していません。これはエラーではありません。保存済み結果は下の累積傾向と履歴だけに置いています。"
                                    ).classes(
                                        "current-scope-note text-[13px] leading-5 mt-3"
                                    )
                                    with ui.row().classes("w-full gap-4 mt-4 flex-wrap"):
                                        metric_refs["overall"] = charts.insight_card(
                                            "AIは誰を薦めたか",
                                            current_result_story["overall_label"],
                                            current_result_story["overall_summary"],
                                        )
                                        metric_refs["competition"] = charts.insight_card(
                                            "主な参照元は何か",
                                            current_result_story["competition_label"],
                                            current_result_story["competition_summary"],
                                        )
                                        metric_refs["action"] = charts.insight_card(
                                            "次にどのページを直すか",
                                            "次の修正ページは未判定",
                                            "分析を実行すると、この質問で先に補うページタイプを表示します。",
                                        )
                                with ui.expansion("実URLと参照元を詳しく見る").classes("w-full panel-card"):
                                    with ui.column().classes("p-4 gap-3 w-full"):
                                        source_container = ui.column().classes("w-full gap-3")
                                with ui.card().classes("card-secondary saved-scope-card p-5 w-full"):
                                    with ui.row().classes("w-full items-start justify-between gap-3 flex-wrap"):
                                        with ui.column().classes("gap-1 min-w-[260px]"):
                                            ui.label("過去データ").classes("saved-scope-label")
                                            ui.label("保存済みの累積傾向").classes("section-font section-title text-[24px] font-bold")
                                        ui.label("今回の入力とは別集計").classes("scope-status-chip saved-status-chip")
                                    ui.label("ここから下は今の入力で実行した結果ではなく、保存済み条件をまとめた累積集計です。上の「今回の結果」と混ぜずに読めます。").classes(
                                        "text-[13px] leading-5 soft-label mt-2"
                                    )
                                    summary_refs["saved_scope"] = charts.insight_card(
                                        "保存済み条件の累積集計",
                                        portfolio_story["overall_label"],
                                        portfolio_story["overall_summary"],
                                    )
                                with ui.card().classes("section-card saved-history-list-card p-5 w-full"):
                                    dashboard_status = ui.label(
                                        f"総評 {portfolio_story['overall_label']} | "
                                        f"自社が見える質問 {portfolio_story['visible_topics']}/{portfolio_story['total_topics']}件 | "
                                        f"弱い質問タイプ {(intent_rows[0]['intent_label'] if intent_rows else '-')} | "
                                        f"不足情報 {(page_gap_rows[0]['page_type_label'] if page_gap_rows else '-')}"
                                    ).classes("text-[15px] text-helper")
                                    ui.label("保存済みの結果").classes("section-font section-title text-[28px] font-bold mt-4")
                                    ui.label("ここは今の入力の結果一覧ではなく、保存済みの結果を横に並べて見比べる一覧です。").classes(
                                        "text-[14px] leading-6 soft-label mt-2"
                                    )
                                    rows_table = ui.table(
                                                columns=admin_views.build_result_table_columns(state["config"].pricing.show_poc_costs),
                                                rows=[],
                                                row_key="result_id",
                                                pagination=10,
                                    ).props(TABLE_BASE_PROPS).classes("w-full mt-4")
                                    ui.label("質問一覧").classes("summary-eyebrow mt-4")
                                    detail_select = ui.select({}, value=None, label="下に表示する質問を選ぶ").props("outlined").classes("w-full mt-2")
                                    ui.label("選択中の質問の詳細").classes("summary-eyebrow mt-3")
                                    detail_container = ui.column().classes("w-full mt-2")
                        with ui.tab_panel(support_analysis_tab).classes("px-0 py-2"):
                            with ui.column().classes("w-full gap-5"):
                                with ui.column().classes("w-full gap-5") as summary_container:
                                    with ui.card().classes("section-card p-5 w-full"):
                                        ui.label("自動チェックの推移").classes("section-font section-title text-[26px] font-bold")
                                        summary_refs["tracking_note"] = ui.label(
                                            "ここでは自動チェックの結果だけを集計します。1回だけ確認は今回の結果と履歴、質問別推移で見ます。"
                                        ).classes("text-[14px] leading-6 soft-label mt-2")
                                        with ui.row().classes("w-full gap-4 mt-4 flex-wrap"):
                                            summary_refs["kpis"]["target_hit_rate"] = charts.metric_card(
                                                "回答試行ベースの自社露出率",
                                                "--",
                                                "観測した試行のうち自社URLが根拠に入った割合",
                                            )
                                            summary_refs["kpis"]["owned_citation_rate"] = charts.metric_card(
                                                "回答試行ベースの自社引用率",
                                                "--",
                                                "観測した試行のうち自社URLが引用された割合",
                                            )
                                            summary_refs["kpis"]["external_lead_rate"] = charts.metric_card(
                                                "回答試行ベースの外部先行率",
                                                "--",
                                                "観測した試行のうち外部サイトが先行した割合",
                                            )
                                            summary_refs["kpis"]["delta"] = charts.metric_card("前回の自動チェックとの差", "--", "前回の自動チェックとの差")
                                        with ui.row().classes("w-full gap-5 flex-wrap"):
                                            with ui.card().classes("section-card p-5 flex-1 min-w-[430px] chart-shell"):
                                                ui.label("見え方の推移").classes("section-font section-title text-[24px] font-bold")
                                                with ui.column().classes("w-full min-h-[320px] mt-3") as analysis_visibility_plot_container:
                                                    ui.label("タブを開いたときにグラフを読み込みます。").classes("text-[13px] text-helper")
                                            with ui.card().classes("section-card p-5 flex-1 min-w-[430px] chart-shell"):
                                                ui.label("自社露出率と外部先行率の推移").classes("section-font section-title text-[24px] font-bold")
                                                with ui.column().classes("w-full min-h-[320px] mt-3") as analysis_history_focus_plot_container:
                                                    ui.label("タブを開いたときにグラフを読み込みます。").classes("text-[13px] text-helper")
                                summary_refs["container"] = summary_container
                                with ui.expansion("見え方の内訳を見る").classes("w-full panel-card"):
                                    with ui.column().classes("p-4 gap-5 w-full"):
                                        with ui.row().classes("w-full gap-5 flex-wrap"):
                                            weakest_intent = intent_rows[0] if intent_rows else None
                                            with ui.card().classes("card-primary p-5 flex-1 min-w-[320px]"):
                                                ui.label("弱い質問タイプ").classes("section-font section-title text-[24px] font-bold")
                                                decision_refs["intent"]["headline"] = ui.label(
                                                    f"{weakest_intent['intent_label']} の露出が弱い" if weakest_intent else "弱い質問タイプは未判定"
                                                ).classes("summary-mainline mt-4 text-main")
                                                decision_refs["intent"]["summary"] = ui.label(
                                                    (
                                                        f"観測した {weakest_intent['total_trial_count']} 試行のうち {weakest_intent['needs_fix_count']} 回で見えにくい状態です。"
                                                        f" この質問タイプはまだ弱めです。"
                                                    )
                                                    if weakest_intent
                                                    else "自動チェックの結果が保存されると、どの質問タイプで弱いかをここに出します。"
                                                ).classes("text-[14px] leading-6 text-support mt-3")
                                                decision_refs["intent"]["table"] = ui.table(
                                                    columns=admin_views.build_intent_table_columns(),
                                                    rows=intent_rows,
                                                    row_key="intent_label",
                                                    pagination=5,
                                                ).props(TABLE_BASE_PROPS).classes("w-full mt-4")

                                            top_gap = page_gap_rows[0] if page_gap_rows else None
                                            with ui.card().classes("card-primary p-5 flex-1 min-w-[320px]"):
                                                ui.label("不足している情報タイプ").classes("section-font section-title text-[24px] font-bold")
                                                decision_refs["gap"]["headline"] = ui.label(
                                                    f"{top_gap['page_type_label']} が不足" if top_gap else "不足している情報タイプは未判定"
                                                ).classes("summary-mainline mt-4 text-main")
                                                decision_refs["gap"]["summary"] = ui.label(
                                                    (
                                                        f"観測した {top_gap['total_trial_count']} 試行のうち {top_gap['needs_fix_count']} 回でこの情報タイプが見えにくい状態です。"
                                                    )
                                                    if top_gap
                                                    else "自動チェックの結果が保存されると、どの情報タイプが不足しているかをここに出します。"
                                                ).classes("text-[14px] leading-6 text-support mt-3")
                                                decision_refs["gap"]["table"] = ui.table(
                                                    columns=admin_views.build_gap_table_columns(),
                                                    rows=page_gap_rows,
                                                    row_key="page_type_label",
                                                    pagination=5,
                                                ).props(TABLE_BASE_PROPS).classes("w-full mt-4")

                                        with ui.row().classes("w-full gap-5 flex-wrap"):
                                            with ui.card().classes("section-card p-5 flex-1 min-w-[430px] chart-shell"):
                                                ui.label("自動チェックの質問ごとの結果").classes("section-font section-title text-[28px] font-bold")
                                                ui.label("見えにくい質問が上に並びます。このヒートマップには自動チェックだけを入れ、1回だけ確認は混ぜません。").classes("text-[14px] leading-6 soft-label mt-2")
                                                ui.label("セルを押すと、今回の結果タブの「下に表示する質問を選ぶ」が切り替わります。").classes("text-[13px] leading-6 text-helper mt-1")
                                                with ui.column().classes("w-full min-h-[420px] mt-3") as question_heatmap_plot_container:
                                                    ui.label("タブを開いたときにグラフを読み込みます。").classes("text-[13px] text-helper")
                                            with ui.card().classes("section-card p-5 flex-1 min-w-[430px] chart-shell"):
                                                ui.label("質問別の履歴推移").classes("section-font section-title text-[28px] font-bold")
                                                ui.label("ここは自動チェックに加えて、1回だけ確認も折れ線で確認できます。hover で実行種別を見分けます。").classes("text-[14px] leading-6 soft-label mt-2")
                                                query_select = ui.select({}, value=None, label="質問を選択").props("outlined").classes("w-full mt-3")
                                                with ui.column().classes("w-full min-h-[320px] mt-3") as query_drilldown_plot_container:
                                                    ui.label("タブを開いたときにグラフを読み込みます。").classes("text-[13px] text-helper")

                                        with ui.row().classes("w-full gap-5 flex-wrap"):
                                            with ui.card().classes("section-card p-5 flex-1 min-w-[430px] chart-shell"):
                                                ui.label("質問タイプの変化").classes("section-font section-title text-[28px] font-bold")
                                                with ui.column().classes("w-full min-h-[360px] mt-3") as intent_trend_plot_container:
                                                    ui.label("タブを開いたときにグラフを読み込みます。").classes("text-[13px] text-helper")
                                            with ui.card().classes("section-card p-5 flex-1 min-w-[430px] chart-shell"):
                                                ui.label("不足情報の変化").classes("section-font section-title text-[28px] font-bold")
                                                with ui.column().classes("w-full min-h-[360px] mt-3") as page_gap_trend_plot_container:
                                                    ui.label("タブを開いたときにグラフを読み込みます。").classes("text-[13px] text-helper")
                                with ui.card().classes("section-card p-5 w-full"):
                                    ui.label("全実行履歴").classes("section-font section-title text-[26px] font-bold")
                                    ui.label("1回だけ確認と自動チェックをまとめて振り返ります。大きな推移グラフは自動チェックだけを使い、質問別推移だけ1回だけ確認も表示します。").classes(
                                        "text-[14px] leading-6 soft-label mt-2"
                                    )
                                    run_table = ui.table(
                                        columns=admin_views.build_run_table_columns(state["config"].pricing.show_poc_costs),
                                        rows=[],
                                        row_key="run_id",
                                        pagination=8,
                                    ).props(TABLE_BASE_PROPS).classes("w-full mt-4")

        def refresh_question_set_admin_views_if_ready(*, force: bool = False) -> None:
            nonlocal question_set_admin_refreshed
            if (
                question_set_select is None
                or question_set_table is None
                or schedule_question_set_select is None
            ):
                return
            if question_set_admin_refreshed and not force:
                return
            page_refreshers.refresh_question_set_admin_views(
                db,
                question_set_select,
                question_set_table,
                schedule_question_set_select,
            )
            refresh_saved_condition_helpers()
            question_set_admin_refreshed = True

        def refresh_batch_job_admin_views_if_ready(*, force: bool = False) -> None:
            nonlocal batch_admin_refreshed
            if (
                batch_job_select is None
                or batch_job_table is None
                or batch_status_label is None
                or batch_summary_label is None
            ):
                return
            if batch_admin_refreshed and not force:
                return
            page_refreshers.refresh_batch_job_admin_views(
                db,
                batch_job_select,
                batch_job_table,
                batch_status_label,
                batch_summary_label,
            )
            batch_admin_refreshed = True

        def refresh_schedule_admin_views_if_ready(*, force: bool = False) -> None:
            nonlocal schedule_admin_refreshed
            if (
                schedule_table is None
                or scheduler_status_label is None
                or schedule_manage_select is None
                or compare_target_select is None
                or compare_mode_select is None
            ):
                return
            if schedule_admin_refreshed and not force:
                return
            page_refreshers.refresh_schedule_admin_views(
                db,
                scheduler_service,
                schedule_table,
                scheduler_status_label,
                schedule_manage_select,
                compare_target_select,
                compare_mode_select,
            )
            if schedule_diff_container is not None:
                admin_views.render_schedule_diff(db, "", str(compare_mode_select.value or "schedule"), "", schedule_diff_container)
            schedule_admin_refreshed = True

        def refresh_export_panel_if_ready(*, force: bool = False) -> None:
            nonlocal export_panel_refreshed
            if export_table is None or export_status_label is None or report_preview_label is None:
                return
            if export_panel_refreshed and not force:
                return
            page_refreshers.refresh_export_panel(
                export_table,
                export_status_label,
                state["export_rows"],
                report_preview_label,
                state["report_preview"],
            )
            export_panel_refreshed = True

        def sync_question_set_name_from_selection() -> None:
            page_refreshers.sync_question_set_name_from_selection(
                db,
                question_set_select,
                question_set_name_input,
                schedule_question_set_select,
            )
            refresh_saved_condition_helpers()
            question_set_save_button.set_text("選択中の保存済み条件を更新")
            if READONLY_DEMO_MODE:
                question_set_save_button.disable()
            elif question_set_select.value:
                question_set_save_button.enable()
            else:
                question_set_save_button.disable()
            question_set_save_button.update()

        def support_tab_matches(target_tab: Any | None, tab: Any | None, label: str) -> bool:
            if target_tab is tab or target_tab == tab:
                return True
            return str(target_tab or "").strip() == label

        def ensure_settings_tab_ready(*, force: bool = False) -> None:
            refresh_question_set_admin_views_if_ready(force=force)
            sync_question_set_name_from_selection()
            refresh_saved_condition_helpers()
            refresh_export_panel_if_ready(force=force)

        def ensure_support_target_ready(target_tab: Any | None = None, target_section: str = "") -> None:
            if support_tab_matches(target_tab, support_settings_tab, "設定"):
                ensure_settings_tab_ready()
                if target_section == "batch":
                    refresh_batch_job_admin_views_if_ready()
                elif target_section == "schedule":
                    refresh_schedule_admin_views_if_ready()
            elif support_tab_matches(target_tab, support_analysis_tab, "自動チェックの推移"):
                mount_analysis_plots()

        sync_question_set_name_from_selection()
        refresh_saved_condition_helpers()
        refresh_current_input_boundary_note()
        refresh_schedule_form_summary()

        def refresh_detail_from_payload(payload: dict[str, Any] | None = None) -> None:
            effective_payload = payload or latest_dashboard_payload or build_dashboard_payload()
            show_current_result = bool(
                effective_payload.get("current_query_rollup_rows")
                and state["show_primary_results"]
                and str(state["current_result_run_id"] or "").strip()
            )
            detail_views.refresh_result_detail_views(
                effective_payload["current_query_rollup_rows"] if show_current_result else effective_payload["query_rollup_rows"],
                effective_payload["current_rows"] if show_current_result else effective_payload["recent_rows"],
                detail_select,
                detail_container,
                state["config"],
                db.list_sources,
                show_current_result=show_current_result,
            )

        def mount_analysis_plots(payload: dict[str, Any] | None = None) -> None:
            nonlocal analysis_plots_mounted
            nonlocal question_heatmap_plot, query_drilldown_plot, intent_trend_plot, page_gap_trend_plot
            if analysis_plots_mounted:
                effective_payload = payload or latest_dashboard_payload
                if effective_payload is not None:
                    dashboard_refreshers.update_tracking_widgets(
                        summary_refs,
                        effective_payload["tracked_recent_rows"],
                        effective_payload["heatmap_rows"],
                        effective_payload["heatmap_raw_rows"],
                        effective_payload["drilldown_rows"],
                        query_select,
                        effective_payload["drilldown_query_rows"],
                        question_heatmap_plot,
                        query_drilldown_plot,
                        intent_trend_plot,
                        page_gap_trend_plot,
                        state["config"],
                        db.list_sources,
                    )
                return

            if any(
                container is None
                for container in (
                    analysis_visibility_plot_container,
                    analysis_history_focus_plot_container,
                    question_heatmap_plot_container,
                    query_drilldown_plot_container,
                    intent_trend_plot_container,
                    page_gap_trend_plot_container,
                )
            ):
                return

            effective_payload = payload or latest_dashboard_payload or build_dashboard_payload()
            with analysis_visibility_plot_container:
                analysis_visibility_plot_container.clear()
                summary_refs["plots"]["visibility"] = ui.plotly(
                    charts.build_overall_visibility_chart(effective_payload["tracked_recent_rows"], state["config"])
                ).classes("w-full h-[320px]")
            with analysis_history_focus_plot_container:
                analysis_history_focus_plot_container.clear()
                summary_refs["plots"]["history_focus"] = ui.plotly(
                    charts.build_visibility_focus_chart(effective_payload["tracked_recent_rows"], state["config"])
                ).classes("w-full h-[320px]")
            with question_heatmap_plot_container:
                question_heatmap_plot_container.clear()
                question_heatmap_plot = ui.plotly(
                    charts.build_question_result_heatmap_chart(
                        effective_payload["heatmap_rows"],
                        effective_payload["heatmap_raw_rows"],
                        state["config"],
                        db.list_sources,
                    )
                ).classes("w-full h-[420px]")
                question_heatmap_plot.on("plotly_click", on_question_heatmap_click)
            with query_drilldown_plot_container:
                query_drilldown_plot_container.clear()
                query_drilldown_plot = ui.plotly(
                    charts.build_query_drilldown_chart(
                        effective_payload["drilldown_rows"],
                        str(query_select.value or ""),
                    )
                ).classes("w-full h-[320px]")
            with intent_trend_plot_container:
                intent_trend_plot_container.clear()
                intent_trend_plot = ui.plotly(
                    charts.build_intent_cluster_chart(effective_payload["tracked_recent_rows"], state["config"])
                ).classes("w-full h-[360px]")
            with page_gap_trend_plot_container:
                page_gap_trend_plot_container.clear()
                page_gap_trend_plot = ui.plotly(
                    charts.build_page_gap_trend_chart(effective_payload["tracked_recent_rows"], state["config"])
                ).classes("w-full h-[360px]")
            analysis_plots_mounted = True
            dashboard_refreshers.update_tracking_widgets(
                summary_refs,
                effective_payload["tracked_recent_rows"],
                effective_payload["heatmap_rows"],
                effective_payload["heatmap_raw_rows"],
                effective_payload["drilldown_rows"],
                query_select,
                effective_payload["drilldown_query_rows"],
                question_heatmap_plot,
                query_drilldown_plot,
                intent_trend_plot,
                page_gap_trend_plot,
                state["config"],
                db.list_sources,
            )

        def refresh_query_drilldown() -> None:
            if query_drilldown_plot is None:
                return
            payload = latest_dashboard_payload or build_dashboard_payload()
            query_drilldown_plot.figure = charts.build_query_drilldown_chart(
                payload["drilldown_rows"],
                str(query_select.value or ""),
            )
            query_drilldown_plot.update()

        def focus_question_detail_from_heatmap(selected_question: str = "", selected_result_id: str = "") -> None:
            payload = latest_dashboard_payload or build_dashboard_payload()
            raw_rows = payload["recent_rows"]
            rollup_rows = payload["query_rollup_rows"]
            if not rollup_rows:
                return

            normalized_question = normalize_text(selected_question)
            matched_row = None
            if selected_result_id:
                matched_row = next(
                    (row for row in rollup_rows if str(row.get("result_id") or "") == str(selected_result_id)),
                    None,
                )
            if matched_row is None and normalized_question:
                matched_row = next(
                    (
                        row
                        for row in rollup_rows
                        if normalize_text(str(row.get("keyword_raw") or row.get("keyword_norm") or "")) == normalized_question
                    ),
                    None,
                )
            if matched_row is None:
                return

            detail_select.value = matched_row.get("result_id")
            detail_views.refresh_result_detail_views(
                rollup_rows,
                raw_rows,
                detail_select,
                detail_container,
                state["config"],
                db.list_sources,
            )

            chosen_question = str(matched_row.get("keyword_raw") or "")
            if chosen_question and chosen_question in (query_select.options or {}):
                query_select.value = chosen_question
                query_select.update()
                refresh_query_drilldown()

            switch_detail_tab(support_result_tab)

        def on_question_heatmap_click(event: Any) -> None:
            points = ((getattr(event, "args", {}) or {}).get("points") or [])
            if not points:
                return
            point = points[0] or {}
            customdata = point.get("customdata") or []
            selected_question = str(customdata[0] or "").strip() if len(customdata) > 0 else ""
            selected_result_id = str(customdata[3] or "").strip() if len(customdata) > 3 else ""
            if not selected_question and not selected_result_id:
                return
            focus_question_detail_from_heatmap(selected_question, selected_result_id)

        def scroll_to_stage(stage_id: str) -> None:
            ui.run_javascript(
                f"""
                const el = document.getElementById('{stage_id}');
                if (el) {{
                    el.scrollIntoView({{behavior: 'smooth', block: 'start'}});
                }}
                """
            )

        def switch_detail_tab(tab: Any) -> None:
            support_tabs.value = tab
            support_tabs.update()
            if tab == support_analysis_tab:
                mount_analysis_plots()
            scroll_to_stage("detail-stage")

        drawer_nav_actions.update(
            {
                "input": lambda: scroll_to_stage("input-stage"),
                "result_stage": lambda: scroll_to_stage("result-stage"),
                "result_tab": lambda: switch_detail_tab(support_result_tab),
                "analysis_tab": lambda: switch_detail_tab(support_analysis_tab),
                "research_tab": lambda: switch_detail_tab(support_research_tab),
                "settings_tab": lambda: switch_detail_tab(support_settings_tab),
            }
        )

        page_client = context.client
        periodic_refresh_task: asyncio.Task | None = None
        periodic_refresh_active = True

        def periodic_refresh() -> None:
            nonlocal periodic_refresh_active, periodic_refresh_task, periodic_refresh_signature, latest_dashboard_payload
            try:
                payload = build_dashboard_payload()
                next_signature = build_periodic_refresh_signature(payload)
                is_reading_current_result = bool(
                    state["show_primary_results"] and str(state["current_result_run_id"] or "").strip()
                )
                if next_signature != periodic_refresh_signature and not is_reading_current_result:
                    run_preserving_scroll(lambda: refresh_dashboard_surface(payload))
                elif next_signature != periodic_refresh_signature:
                    latest_dashboard_payload = payload
                    periodic_refresh_signature = next_signature
                    refresh_hero_status(payload)
                    if (
                        analysis_plots_mounted
                        and support_tabs is not None
                        and support_tab_matches(support_tabs.value, support_analysis_tab, "自動チェックの推移")
                    ):
                        mount_analysis_plots(payload)
                else:
                    refresh_hero_status(payload)
            except RuntimeError as exc:
                if is_deleted_ui_runtime_error(exc):
                    periodic_refresh_active = False
                    if periodic_refresh_task is not None:
                        periodic_refresh_task.cancel()
                    return
                raise

        def pause_periodic_refresh(_client: Any = None) -> None:
            nonlocal periodic_refresh_active
            periodic_refresh_active = False

        def resume_periodic_refresh(_client: Any = None) -> None:
            nonlocal periodic_refresh_active
            periodic_refresh_active = True

        def cancel_periodic_refresh(_client: Any = None) -> None:
            nonlocal periodic_refresh_active, periodic_refresh_task
            periodic_refresh_active = False
            if periodic_refresh_task is not None:
                periodic_refresh_task.cancel()
                periodic_refresh_task = None

        async def periodic_refresh_loop() -> None:
            while True:
                try:
                    await asyncio.sleep(180.0)
                except asyncio.CancelledError:
                    break
                if not periodic_refresh_active:
                    continue
                if not page_client.has_socket_connection:
                    continue
                page_client.safe_invoke(periodic_refresh)

        refresh_dashboard_surface()
        refresh_cluster_and_outcome_sections()
        render_active_cluster_and_outcome_panels()
        if READONLY_DEMO_MODE:
            set_action_button_states(True)
        query_select.on("update:model-value", lambda _: refresh_query_drilldown())
        support_tabs.on("update:model-value", lambda _: ensure_support_target_ready(support_tabs.value))
        if batch_settings_expansion is not None:
            batch_settings_expansion.on_value_change(
                lambda _=None: refresh_batch_job_admin_views_if_ready() if batch_settings_expansion.value else None
            )
        if schedule_settings_expansion is not None:
            schedule_settings_expansion.on_value_change(
                lambda _=None: refresh_schedule_admin_views_if_ready() if schedule_settings_expansion.value else None
            )
        question_set_select.on("update:model-value", lambda _: sync_question_set_name_from_selection())
        schedule_question_set_select.on("update:model-value", lambda _: refresh_saved_condition_helpers())
        detail_select.on(
            "update:model-value",
            lambda _: refresh_detail_from_payload(),
        )
        periodic_refresh_task = background_tasks.create(
            periodic_refresh_loop(),
            name=f"kotomegane periodic refresh {page_client.id}",
        )
        page_client.on_disconnect(pause_periodic_refresh)
        page_client.on_connect(resume_periodic_refresh)
        page_client.on_delete(cancel_periodic_refresh)


@ui.page("/")
def index() -> None:
    render_page()


if __name__ == "__main__":
    startup_config = load_runtime_config_state()
    _validate_startup_host_or_raise(str(startup_config.ui_host or ""))
    ui.run(
        title="コトメガネ | TECHIE",
        host=startup_config.ui_host,
        port=startup_config.ui_port,
        reload=False,
        show=False,
        favicon=str(ASSETS_DIR / "favicon_v2.png"),
    )
