from __future__ import annotations

import asyncio
import csv
import json
import time
from collections import Counter
from typing import Any
from urllib.parse import urlparse

import plotly.graph_objects as go
from nicegui import app as fastapi_app
from nicegui import ui

from analysis_lib import (
    build_answer_structure_fields,
    build_budget_guardrail,
    build_cluster_brief_candidates,
    build_cluster_brief_draft,
    build_intent_cluster_series,
    build_overview_metrics,
    build_overall_visibility_series,
    build_previous_delta_summary,
    build_query_rollup_rows,
    build_visibility_focus_series,
    build_page_brief_draft,
    build_page_gap_trend_series,
    build_query_drilldown_series,
    build_keyword_stability_map,
    build_run_outcome_compare,
    compute_next_schedule_run,
    classify_keyword_intent,
    classify_visibility_verdict,
    dedupe_preserve_order,
    estimate_cost_usd,
    format_schedule_slot,
    format_timestamp,
    format_weekdays_label,
    infer_page_gap,
    is_extended_prompt_cache_supported,
    join_csv,
    normalize_domain_host,
    normalize_query_text,
    normalize_text,
    normalize_schedule_weekdays,
    parse_json_object,
    parse_weekdays_csv,
    parse_citations_json,
    build_raw_results_export_rows,
    build_weekly_summary_rows,
    resolve_analysis_mode,
    resolve_prompt_cache_retention,
    resolve_latest_due_schedule_slot,
    split_csv,
    split_multiline_keywords,
)
from config import (
    ANALYSIS_MODE_MARKET,
    ANALYSIS_MODE_OWNED_ONLY,
    ASSETS_DIR,
    AppConfig,
    EXPORTS_DIR,
    ProviderOption,
    get_api_key_status,
    get_provider_catalog,
    get_provider_effective_model,
    get_provider_option,
    get_provider_total_question_budget,
    load_config,
    provider_supports_batch,
    provider_supports_prompt_cache,
    save_config,
)
from llmo_client import AnalysisResult, build_provider_client
from query_planning import ExecutionPlan, QueryPlanner, build_execution_plan
from run_planning import prepare_query_plans_for_run
from scheduler_runtime import ScheduledMonitorService
from storage import Storage

db = Storage()
config_state = load_config().model_copy(update={"analysis_mode": ANALYSIS_MODE_MARKET, "repeat_count": 20})
scheduler_service = ScheduledMonitorService(db)
query_planner = QueryPlanner()

if ASSETS_DIR.exists():
    fastapi_app.add_static_files("/branding", str(ASSETS_DIR))
if EXPORTS_DIR.exists():
    fastapi_app.add_static_files("/exports", str(EXPORTS_DIR))
fastapi_app.on_startup(lambda: scheduler_service.start())
fastapi_app.on_shutdown(scheduler_service.stop)

TABLE_BASE_PROPS = 'flat wrap-cells rows-per-page-label="表示件数" no-data-label="データなし"'

THEME_TEXT_MAIN = "#3E2C22"
THEME_TEXT_SOFT = "#6B5648"
THEME_TEXT_HELPER = "#8C7668"
THEME_GRID_SOFT = "rgba(107, 86, 72, 0.10)"
THEME_GRID_STRONG = "rgba(107, 86, 72, 0.16)"
THEME_BRAND = "#D96B1F"
THEME_BRAND_DEEP = "#A84A14"
THEME_SERIES_BLUE = "#A76637"
THEME_SERIES_TEAL = "#6F8B67"
THEME_SERIES_AMBER = "#C29246"
THEME_SERIES_CORAL = "#BE6B4A"
THEME_SERIES_SLATE = "#8B776A"
VISIBLE_PROVIDER_KEYS = ("openai", "gemini", "claude")


def add_global_style() -> None:
    ui.add_head_html(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
          <style>
          :root {
            --bg: #f6efe8;
            --bg-deep: #eadccf;
            --surface: #fffdf9;
            --surface-muted: #f7f0e8;
            --surface-raised: rgba(255, 253, 249, 0.98);
            --text: #35241a;
            --text-soft: #5c483b;
            --muted: #786252;
            --brand: #d96b1f;
            --brand-deep: #a84a14;
            --brand-soft: rgba(217, 107, 31, 0.14);
            --self: #6f8b67;
            --self-soft: rgba(111, 139, 103, 0.12);
            --competitive: #c29246;
            --competitive-soft: rgba(194, 146, 70, 0.16);
            --external: #be6b4a;
            --external-soft: rgba(190, 107, 74, 0.13);
            --border: rgba(122, 98, 83, 0.14);
            --border-strong: rgba(122, 98, 83, 0.22);
            --shadow: 0 18px 42px rgba(84, 60, 46, 0.10);
            --shadow-hover: 0 20px 46px rgba(84, 60, 46, 0.14);
            --nav-bg: #3d2a1f;
            --nav-text: #f3e8dc;
            --nav-text-active: #f5ba71;
            --bg-soft: rgba(250, 244, 237, 0.92);
            --panel: rgba(255, 251, 246, 0.94);
            --panel-strong: var(--surface-raised);
            --panel-muted: rgba(250, 244, 237, 0.90);
            --line: var(--border);
            --line-strong: var(--border-strong);
            --accent: var(--brand);
            --accent-deep: var(--brand-deep);
            --accent-soft: var(--brand-soft);
            --brown: var(--nav-bg);
            --brown-soft: #6b5648;
            --neutral-soft: rgba(122, 98, 83, 0.10);
            --green-mist: rgba(245, 227, 205, 0.44);
            --shadow-soft: 0 18px 40px rgba(84, 60, 46, 0.08);
            --q-primary: #d96b1f;
            --q-secondary: #6b5648;
            --q-accent: #a84a14;
            --q-info: #a76637;
          }
          html, body {
            font-size: 16px;
          }
          body {
            font-family: "Noto Sans JP", sans-serif;
            background:
              radial-gradient(circle at 80% 18%, rgba(244, 222, 198, 0.24), transparent 18%),
              radial-gradient(circle at 18% 12%, rgba(255, 255, 255, 0.80), transparent 24%),
              linear-gradient(160deg, #f8f1ea 0%, var(--bg-deep) 52%, #e3d1c3 100%);
            color: var(--text);
          }
          .brand-font,
          .metric-font,
          .section-font,
          .step-font {
            font-family: "Sora", sans-serif;
          }
          .top-shell {
            background: linear-gradient(180deg, var(--nav-bg) 0%, #362419 100%);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 10px 28px rgba(54, 36, 25, 0.24);
          }
          .top-logo-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            padding: 8px 0;
          }
          .top-logo-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            border-radius: 12px;
            background: rgba(255, 248, 241, 0.12);
            border: 1px solid rgba(255, 248, 241, 0.18);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.10);
          }
          .top-logo-icon {
            width: 22px;
            height: 22px;
            object-fit: contain;
          }
          .top-logo-wordmark {
            color: var(--nav-text);
            font-size: 1.1rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            line-height: 1;
            text-transform: uppercase;
          }
          .nav-link {
            color: var(--nav-text);
            font-weight: 700;
            letter-spacing: 0.04em;
          }
          .nav-link-active {
            color: var(--nav-text-active);
          }
          .hero-service-name {
            color: var(--brand-deep);
            font-size: clamp(2rem, 2.6vw, 2.5rem);
            line-height: 1.0;
            font-weight: 700;
          }
          .hero-card {
            background:
              radial-gradient(circle at 84% 18%, rgba(247, 233, 214, 0.34), transparent 24%),
              linear-gradient(135deg, rgba(255, 254, 251, 0.99) 0%, rgba(249, 242, 234, 0.95) 100%);
            border: 1px solid rgba(137, 111, 92, 0.12);
            border-radius: 22px;
            box-shadow: 0 16px 36px rgba(84, 60, 46, 0.08);
          }
          .hero-copy-card {
            max-width: 760px;
          }
          .card-primary,
          .section-card {
            background: var(--panel-strong);
            border: 1px solid var(--line-strong);
            border-radius: 28px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(14px);
          }
          .card-secondary,
          .panel-card {
            background: var(--panel-muted);
            border: 1px solid rgba(137, 111, 92, 0.12);
            border-radius: 24px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
          }
          .card-detail {
            background: var(--surface-muted);
            border: 1px solid var(--border);
            border-radius: 20px;
            box-shadow: none;
          }
          .soft-chip {
            border-radius: 999px;
            padding: 10px 16px;
            background: rgba(255, 251, 247, 0.84);
            border: 1px solid rgba(197, 150, 117, 0.18);
            color: var(--text-soft);
            font-weight: 600;
          }
          .provider-card {
            min-height: 208px;
            position: relative;
            overflow: hidden;
          }
          .provider-active {
            background:
              linear-gradient(160deg, rgba(252, 248, 241, 0.98) 0%, rgba(247, 243, 236, 0.94) 100%);
            border: 1px solid rgba(240, 138, 36, 0.24);
            box-shadow: 0 18px 44px rgba(240, 138, 36, 0.10);
          }
          .provider-planned {
            background:
              linear-gradient(160deg, rgba(244, 249, 253, 0.94) 0%, rgba(238, 245, 251, 0.86) 100%);
            border: 1px dashed rgba(94, 124, 154, 0.22);
          }
          .provider-strip {
            position: absolute;
            inset: 0 auto auto 0;
            width: 100%;
            height: 4px;
          }
          .provider-strip-active {
            background: linear-gradient(90deg, #f6a44a 0%, #f08a24 100%);
          }
          .provider-strip-planned {
            background: linear-gradient(90deg, rgba(123, 144, 165, 0.35) 0%, rgba(177, 198, 216, 0.28) 100%);
          }
          .provider-meta {
            margin-top: auto;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }
          .provider-meta-chip {
            border-radius: 999px;
            padding: 8px 12px;
            background: rgba(255, 252, 248, 0.82);
            border: 1px solid rgba(108, 82, 67, 0.10);
            color: var(--text-soft);
            font-size: 0.84rem;
            font-weight: 600;
          }
          .provider-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-top: 18px;
          }
          .provider-state-pill {
            border-radius: 999px;
            padding: 9px 14px;
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.03em;
          }
          .provider-state-live {
            background: var(--accent-soft);
            color: var(--accent-deep);
          }
          .provider-state-disabled {
            background: var(--neutral-soft);
            color: var(--text-soft);
          }
          .status-badge {
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.04em;
          }
          .status-active {
            background: var(--accent-soft);
            color: var(--accent-deep);
          }
          .status-planned {
            background: var(--neutral-soft);
            color: var(--text-soft);
          }
          .metric-card {
            min-width: 220px;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(245, 250, 254, 0.92) 100%);
          }
          .insight-card {
            min-height: 236px;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 249, 253, 0.94) 100%);
          }
          .metric-value {
            color: var(--accent-deep);
          }
          .insight-headline {
            color: var(--text);
            line-height: 1.2;
          }
          .soft-label {
            color: var(--text-soft);
          }
          .eyebrow-label {
            color: var(--text-soft);
            letter-spacing: 0.18em;
            text-transform: uppercase;
          }
          .section-title {
            color: var(--brown);
          }
          .accent-button,
          .q-btn.accent-button {
            background: linear-gradient(180deg, #f6a44a 0%, var(--accent) 100%) !important;
            background-color: var(--accent) !important;
            border: 1px solid var(--accent-deep) !important;
            color: white !important;
            box-shadow: 0 10px 22px rgba(240, 138, 36, 0.18) !important;
            border-radius: 16px;
            min-height: 52px;
            padding: 0 26px;
          }
          .q-btn.accent-button .q-btn__content {
            color: white !important;
          }
          .q-btn.accent-button::before,
          .q-btn.accent-button .q-focus-helper {
            background: transparent !important;
            opacity: 0 !important;
          }
          .secondary-button,
          .q-btn.secondary-button {
            background: rgba(245, 250, 254, 0.96) !important;
            border: 1px solid rgba(94, 124, 154, 0.18) !important;
            color: var(--text) !important;
            box-shadow: none !important;
            border-radius: 16px;
            min-height: 52px;
            padding: 0 24px;
          }
          .q-btn.secondary-button .q-btn__content {
            color: var(--text) !important;
          }
          .q-btn.secondary-button::before,
          .q-btn.secondary-button .q-focus-helper {
            background: transparent !important;
            opacity: 0 !important;
          }
          .provider-runtime-card {
            background: linear-gradient(180deg, rgba(255, 251, 246, 0.98) 0%, rgba(247, 240, 232, 0.94) 100%);
            border: 1px solid rgba(122, 98, 83, 0.14);
            border-radius: 18px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.48);
          }
          .provider-chip-rail {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
          }
          .provider-chip-button,
          .q-btn.provider-chip-button {
            min-height: 38px;
            padding: 0 14px;
            border-radius: 999px;
            border: 1px solid rgba(122, 98, 83, 0.16) !important;
            background: rgba(255, 251, 246, 0.98) !important;
            color: var(--text-soft) !important;
            box-shadow: none !important;
            font-weight: 700;
          }
          .provider-chip-button .q-btn__content {
            color: inherit !important;
          }
          .provider-chip-button-active,
          .q-btn.provider-chip-button-active {
            background: linear-gradient(180deg, rgba(251, 236, 214, 0.98) 0%, rgba(245, 225, 196, 0.96) 100%) !important;
            border-color: rgba(217, 107, 31, 0.36) !important;
            color: var(--accent-deep) !important;
            box-shadow: 0 8px 16px rgba(217, 107, 31, 0.10) !important;
          }
          .provider-chip-button-ready,
          .q-btn.provider-chip-button-ready {
            background: rgba(255, 251, 246, 0.96) !important;
            border-color: rgba(122, 98, 83, 0.18) !important;
            color: var(--text-soft) !important;
          }
          .provider-chip-button-disabled,
          .q-btn.provider-chip-button-disabled {
            background: rgba(234, 229, 224, 0.96) !important;
            border-color: rgba(157, 145, 136, 0.22) !important;
            color: #8e837a !important;
            box-shadow: none !important;
          }
          .provider-chip-button-disabled .q-btn__content {
            color: #8e837a !important;
          }
          .q-btn.provider-chip-button::before,
          .q-btn.provider-chip-button .q-focus-helper {
            background: transparent !important;
            opacity: 0 !important;
          }
          .step-rail {
            background: rgba(240, 247, 252, 0.64);
            border: 1px solid rgba(94, 124, 154, 0.16);
            border-radius: 20px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
          }
          .step-chip-active {
            background: linear-gradient(180deg, #f6a44a 0%, var(--accent) 100%);
            color: white;
            box-shadow: 0 10px 18px rgba(240, 138, 36, 0.20);
          }
          .step-chip-muted {
            background: rgba(233, 242, 249, 0.94);
            color: var(--muted);
          }
          .source-pill {
            border-radius: 18px;
            padding: 12px 14px;
            background: rgba(255, 255, 255, 0.90);
            border: 1px solid rgba(94, 124, 154, 0.10);
          }
          .result-highlight-card {
            min-height: 204px;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(245, 250, 254, 0.94) 100%);
          }
          .chart-shell {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 249, 253, 0.94) 100%);
          }
          .summary-eyebrow {
            color: var(--text-soft);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: none;
          }
          .summary-mainline {
            color: var(--text);
            font-size: clamp(1.45rem, 2vw, 1.9rem);
            line-height: 1.2;
            font-weight: 700;
          }
          .mini-stat-card {
            border-radius: 18px;
            padding: 14px 14px 12px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(94, 124, 154, 0.10);
            min-width: 128px;
          }
          .workflow-lane-card {
            border-radius: 18px;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(94, 124, 154, 0.10);
            min-width: 180px;
          }
          .workflow-stage-card {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 249, 253, 0.94) 100%);
            border: 1px solid rgba(94, 124, 154, 0.14);
            border-radius: 22px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
          }
          .workflow-step-pill {
            border-radius: 999px;
            padding: 8px 14px;
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            width: fit-content;
          }
          .workflow-step-pill-active {
            background: linear-gradient(180deg, #f6a44a 0%, var(--accent) 100%);
            color: white;
            box-shadow: 0 10px 18px rgba(240, 138, 36, 0.18);
          }
          .workflow-step-pill-muted {
            background: rgba(233, 242, 249, 0.94);
            color: var(--text-soft);
          }
          .stage-note-card {
            border-radius: 20px;
            padding: 16px;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(94, 124, 154, 0.10);
          }
          .detail-tabs-shell {
            background: rgba(240, 247, 252, 0.68);
            border: 1px solid rgba(94, 124, 154, 0.18);
            border-radius: 20px;
            padding: 6px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
          }
          .detail-tabs-shell .q-tab {
            border-radius: 16px;
            color: var(--text-soft);
            font-weight: 700;
            letter-spacing: 0.04em;
            min-height: 48px;
          }
          .detail-tabs-shell .q-tab--active {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(245, 250, 254, 0.96) 100%);
            color: var(--accent-deep);
            box-shadow: 0 10px 20px rgba(240, 138, 36, 0.10);
          }
          .detail-tabs-shell .q-tab__indicator {
            display: none;
          }
          .detail-tab-panels {
            background: transparent;
          }
          .signal-chip {
            border-radius: 999px;
            padding: 8px 12px;
            font-size: 0.84rem;
            font-weight: 700;
          }
          .signal-positive {
            background: var(--self-soft);
            color: var(--self);
          }
          .signal-negative {
            background: var(--external-soft);
            color: var(--external);
          }
          .signal-neutral {
            background: var(--competitive-soft);
            color: var(--competitive);
          }
          .action-item {
            border-radius: 18px;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(94, 124, 154, 0.12);
          }
          .status-row {
            border-radius: 20px;
            background: rgba(245, 250, 254, 0.92);
            border: 1px solid rgba(94, 124, 154, 0.12);
          }
          .source-group-card {
            border-radius: 20px;
            padding: 16px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(94, 124, 154, 0.12);
          }
          .source-group-positive {
            background: rgba(241, 250, 245, 0.96);
            border-color: rgba(47, 138, 87, 0.22);
          }
          .source-group-negative {
            background: rgba(255, 246, 242, 0.96);
            border-color: rgba(180, 74, 43, 0.20);
          }
          .source-group-neutral {
            background: rgba(255, 248, 239, 0.96);
            border-color: rgba(182, 122, 53, 0.18);
          }
          .evidence-link {
            color: var(--accent-deep);
            word-break: break-all;
          }
          .text-main {
            color: var(--text);
          }
          .text-support {
            color: var(--text-soft);
          }
          .text-helper {
            color: var(--muted);
          }
          .text-brand {
            color: var(--accent-deep);
          }
          .text-self {
            color: var(--self);
          }
          .text-competitive {
            color: var(--competitive);
          }
          .text-external {
            color: var(--external);
          }
          .text-runtime-ready {
            color: var(--self);
          }
          .text-runtime-pending {
            color: var(--external);
          }
          .text-runtime-planned {
            color: var(--competitive);
          }
          .ui-divider {
            color: rgba(122, 79, 48, 0.44);
          }
          .q-field__label,
          .q-field__native,
          .q-field__input,
          .q-item__label,
          .q-select__dropdown-icon {
            font-size: 16px !important;
          }
          .q-textarea textarea,
          .q-field input {
            line-height: 1.55 !important;
          }
          .q-table thead th {
            font-size: 14px !important;
            font-weight: 700 !important;
            color: var(--text-soft) !important;
            background: rgba(236, 245, 251, 0.94);
          }
          .q-table tbody td {
            font-size: 15px !important;
            line-height: 1.55 !important;
            vertical-align: top;
          }
          .q-table th,
          .q-table td {
            padding: 12px 14px !important;
          }
          .q-expansion-item__container {
            border-radius: 18px;
            overflow: hidden;
          }
          .chart-shell .js-plotly-plot,
          .chart-shell > div {
            width: 100% !important;
          }
          @media (max-width: 1100px) {
            .nav-link {
              font-size: 1.1rem !important;
            }
            .hero-card {
              border-radius: 22px;
            }
          }
          @media (max-width: 760px) {
            .nav-link {
              font-size: 1rem !important;
            }
            .top-logo-badge {
              width: 32px;
              height: 32px;
            }
            .top-logo-icon {
              width: 19px;
              height: 19px;
            }
            .top-logo-wordmark {
              font-size: 1rem;
              letter-spacing: 0.12em;
            }
            .hero-card,
            .section-card,
            .card-primary,
            .workflow-stage-card,
            .workflow-lane-card,
            .step-rail,
            .panel-card,
            .result-highlight-card {
              min-width: 0 !important;
              border-radius: 20px;
            }
            .source-group-card,
            .mini-stat-card {
              min-width: 0 !important;
            }
            .result-highlight-card,
            .insight-card,
            .workflow-lane-card {
              width: 100% !important;
              flex: 1 1 100% !important;
            }
            .summary-mainline {
              font-size: clamp(1.28rem, 6vw, 1.55rem);
            }
            .q-table th,
            .q-table td {
              padding: 10px 12px !important;
            }
          }
        </style>
        """
    )


def build_score_chart(rows: list[dict[str, Any]], config: AppConfig) -> go.Figure:
    series = build_citation_share_series(rows, config)
    if not series:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin={"l": 24, "r": 18, "t": 18, "b": 24},
            font={"color": THEME_TEXT_MAIN, "size": 14},
            annotations=[
                {
                    "text": "まだ引用シェアを出せる根拠URLがありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ],
        )
        return fig

    color_map = {"self": THEME_SERIES_TEAL, "competitor": THEME_SERIES_AMBER, "third_party": THEME_SERIES_CORAL}
    label_map = {"self": "自社", "competitor": "競合", "third_party": "外部"}
    fig = go.Figure(
        go.Bar(
            x=[row["count"] for row in series],
            y=[wrap_chart_question_label(row["host"], chunk_size=18, max_chars=36) for row in series],
            orientation="h",
            marker={"color": [color_map[row["category"]] for row in series]},
            text=[f'{row["count"]}件' for row in series],
            textposition="outside",
            customdata=[[row["host"], label_map[row["category"]]] for row in series],
            hovertemplate="%{customdata[0]}<br>区分 %{customdata[1]}<br>引用登場 %{x}件<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 220, "r": 18, "t": 18, "b": 24},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"title": "引用登場回数", "gridcolor": THEME_GRID_STRONG},
        yaxis={"automargin": True},
    )
    fig.update_traces(cliponaxis=False)
    return fig


def build_visibility_focus_chart(rows: list[dict[str, Any]], config: AppConfig) -> go.Figure:
    series = build_visibility_focus_series(rows, config)
    fig = go.Figure()
    if series:
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in series],
                y=[point["visible_rate"] for point in series],
                mode="lines+markers",
                name="自社露出率",
                line={"width": 3, "color": THEME_SERIES_TEAL},
                marker={"size": 8},
                customdata=[[localize_run_mode(point["run_mode"]), point["question_set_name"], point["total_questions"]] for point in series],
                hovertemplate="%{x}<br>自社露出率 %{y}%<br>%{customdata[0]} / %{customdata[1]}<br>質問数 %{customdata[2]}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in series],
                y=[point["external_lead_rate"] for point in series],
                mode="lines+markers",
                name="外部サイト優勢率",
                line={"width": 3, "color": THEME_SERIES_CORAL},
                marker={"size": 8},
                customdata=[[localize_run_mode(point["run_mode"]), point["question_set_name"], point["total_questions"]] for point in series],
                hovertemplate="%{x}<br>外部サイト優勢率 %{y}%<br>%{customdata[0]} / %{customdata[1]}<br>質問数 %{customdata[2]}<extra></extra>",
            )
        )
    else:
        fig.update_layout(
            annotations=[
                {
                    "text": "まだ履歴の推移を描ける結果がありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ]
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 24, "r": 18, "t": 18, "b": 24},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"gridcolor": THEME_GRID_STRONG},
        yaxis={"title": "割合 (%)", "gridcolor": THEME_GRID_STRONG, "rangemode": "tozero"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
    )
    fig.update_traces(cliponaxis=False)
    return fig


def build_history_chart(rows: list[dict[str, Any]]) -> go.Figure:
    series = build_keyword_volatility_series(rows)
    fig = go.Figure()
    palette = [THEME_BRAND, THEME_SERIES_BLUE, THEME_SERIES_TEAL, THEME_SERIES_AMBER, THEME_SERIES_SLATE]
    for index, item in enumerate(series):
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in item["points"]],
                y=[point["score"] for point in item["points"]],
                mode="lines+markers",
                name=shorten_question_label(item["keyword"], limit=16),
                line={"width": 3, "color": palette[index % len(palette)]},
                marker={"size": 8},
                customdata=[[point["verdict"], point["label"]] for point in item["points"]],
                hovertemplate="%{x}<br>参考スコア %{y}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
            )
        )
    if not series:
        fig.update_layout(
            annotations=[
                {
                    "text": "まだ揺れ幅を出せる履歴がありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ]
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 18, "r": 18, "t": 18, "b": 42},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"title": "確認時刻", "gridcolor": THEME_GRID_SOFT},
        yaxis={"title": "参考スコア", "range": [0, 100], "gridcolor": THEME_GRID_STRONG},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    return fig


def build_overall_visibility_chart(rows: list[dict[str, Any]], config: AppConfig) -> go.Figure:
    series = build_overall_visibility_series(rows, config)
    fig = go.Figure()
    if series:
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in series],
                y=[point["avg_score"] for point in series],
                mode="lines+markers",
                name="全体の見えやすさ",
                line={"width": 3, "color": THEME_BRAND},
                marker={"size": 8},
                customdata=[[point["visible_rate"], localize_run_mode(point["run_mode"]), point["question_set_name"]] for point in series],
                hovertemplate="%{x}<br>平均スコア %{y}<br>自社可視率 %{customdata[0]}%<br>%{customdata[1]} / %{customdata[2]}<extra></extra>",
            )
        )
    else:
        fig.update_layout(
            annotations=[
                {
                    "text": "まだ全体トレンドを描ける履歴がありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ]
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 18, "r": 18, "t": 18, "b": 42},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"title": "実行時刻", "gridcolor": THEME_GRID_SOFT},
        yaxis={"title": "平均スコア", "range": [0, 100], "gridcolor": THEME_GRID_STRONG},
    )
    return fig


def build_intent_cluster_chart(rows: list[dict[str, Any]], config: AppConfig) -> go.Figure:
    series = build_intent_cluster_series(rows, config)
    fig = go.Figure()
    palette = [THEME_BRAND, THEME_SERIES_BLUE, THEME_SERIES_TEAL, THEME_SERIES_AMBER]
    for index, item in enumerate(series):
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in item["points"]],
                y=[point["score"] for point in item["points"]],
                mode="lines+markers",
                name=item["label"],
                line={"width": 3, "color": palette[index % len(palette)]},
                marker={"size": 7},
                customdata=[[localize_run_mode(point["run_mode"])] for point in item["points"]],
                hovertemplate="%{x}<br>%{fullData.name} %{y}<br>%{customdata[0]}<extra></extra>",
            )
        )
    if not series:
        fig.update_layout(
            annotations=[
                {
                    "text": "まだ意図クラスタの時系列がありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ]
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 18, "r": 18, "t": 18, "b": 42},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"title": "実行時刻", "gridcolor": THEME_GRID_SOFT},
        yaxis={"title": "意図別スコア", "range": [0, 100], "gridcolor": THEME_GRID_STRONG},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    return fig


def build_page_gap_trend_chart(rows: list[dict[str, Any]], config: AppConfig) -> go.Figure:
    series = build_page_gap_trend_series(rows, config)
    fig = go.Figure()
    palette = [THEME_SERIES_CORAL, THEME_SERIES_AMBER, THEME_SERIES_SLATE, THEME_BRAND]
    for index, item in enumerate(series):
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in item["points"]],
                y=[point["count"] for point in item["points"]],
                mode="lines+markers",
                name=item["label"],
                line={"width": 3, "color": palette[index % len(palette)]},
                marker={"size": 7},
                customdata=[[localize_run_mode(point["run_mode"])] for point in item["points"]],
                hovertemplate="%{x}<br>%{fullData.name} 未解消 %{y}件<br>%{customdata[0]}<extra></extra>",
            )
        )
    if not series:
        fig.update_layout(
            annotations=[
                {
                    "text": "まだ不足ページの推移を描ける履歴がありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ]
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 18, "r": 18, "t": 18, "b": 42},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"title": "実行時刻", "gridcolor": THEME_GRID_SOFT},
        yaxis={"title": "未解消ページ件数", "gridcolor": THEME_GRID_STRONG},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    return fig


def build_query_drilldown_chart(rows: list[dict[str, Any]], keyword: str) -> go.Figure:
    series = build_query_drilldown_series(rows, keyword)
    fig = go.Figure()
    if series:
        fig.add_trace(
            go.Scatter(
                x=[point["timestamp"] for point in series],
                y=[point["score"] for point in series],
                mode="lines+markers",
                name="質問別推移",
                line={"width": 3, "color": THEME_SERIES_BLUE},
                marker={"size": 8},
                customdata=[[point["verdict"], localize_run_mode(point["run_mode"])] for point in series],
                hovertemplate="%{x}<br>スコア %{y}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
            )
        )
    else:
        fig.update_layout(
            annotations=[
                {
                    "text": "まだこの質問の履歴がありません",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 15, "color": THEME_TEXT_HELPER},
                }
            ]
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 18, "r": 18, "t": 18, "b": 42},
        font={"color": THEME_TEXT_MAIN, "size": 14},
        xaxis={"title": "確認時刻", "gridcolor": THEME_GRID_SOFT},
        yaxis={"title": "質問別スコア", "range": [0, 100], "gridcolor": THEME_GRID_STRONG},
    )
    return fig


def metric_card(label: str, value: str, detail: str) -> tuple[ui.label, ui.label]:
    with ui.card().classes("section-card metric-card p-5 flex-1"):
        ui.label(label).classes("text-[12px] uppercase tracking-[0.22em] soft-label")
        value_label = ui.label(value).classes("metric-font metric-value text-[34px] font-bold mt-3")
        detail_label = ui.label(detail).classes("text-[14px] leading-6 text-support mt-2")
    return value_label, detail_label


def insight_card(label: str, headline: str, detail: str) -> tuple[ui.label, ui.label]:
    with ui.card().classes("card-secondary insight-card p-4 flex-1 min-w-[240px]"):
        ui.label(label).classes("text-[12px] uppercase tracking-[0.22em] soft-label")
        headline_label = ui.label(headline).classes(
            "section-font insight-headline text-[26px] font-bold mt-3"
        )
        detail_label = ui.label(detail).classes("text-[15px] leading-7 text-support mt-3")
    return headline_label, detail_label


def localize_confidence_label(confidence: str) -> str:
    mapping = {"high": "高め", "medium": "中くらい", "low": "低め"}
    return mapping.get(str(confidence or "").lower(), "低め")


def normalize_host(raw_value: Any) -> str:
    return normalize_domain_host(raw_value)


def localize_analysis_mode(mode: str) -> str:
    return "自社監査" if mode == ANALYSIS_MODE_OWNED_ONLY else "市場観測"


def localize_cache_retention_label(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == "24h":
        return "24時間"
    if normalized == "in_memory":
        return "メモリ内"
    return str(value or "-")


def describe_analysis_mode(mode: str) -> str:
    if mode == ANALYSIS_MODE_OWNED_ONLY:
        return "自社または許可したドメインだけで、この質問に答え切れるかを見ます。"
    return "実際の市場で、自社・競合・外部サイトのどこがAI回答の根拠に入るかを見ます。"


def resolve_row_analysis_mode(row: dict[str, Any], payload: dict[str, Any] | None = None) -> str:
    effective_payload = payload or parse_json_object(row.get("output_json"))
    return resolve_analysis_mode(effective_payload)


def build_intent_map_rows(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    latest_rows = get_latest_rows_by_keyword(rows)
    stability_map = build_keyword_stability_map(rows)
    grouped: dict[str, dict[str, Any]] = {}

    for row in latest_rows:
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
        verdict = build_visibility_state_label(
            int(row.get("visibility_score") or 0),
            bool(row.get("target_domain_hit")),
            bool(row.get("brand_mention_hit")),
        )
        key = intent["primary"]
        bucket = grouped.setdefault(
            key,
            {
                "intent_label": intent["label"],
                "question_count": 0,
                "needs_fix_count": 0,
                "visible_count": 0,
                "score_total": 0,
                "stability_scores": [],
                "page_types": [],
                "keywords": [],
            },
        )
        bucket["question_count"] += 1
        bucket["score_total"] += int(row.get("visibility_score") or 0)
        bucket["visible_count"] += 1 if row.get("target_domain_hit") else 0
        bucket["needs_fix_count"] += 1 if verdict in {"外部サイト優勢", "未露出"} else 0
        bucket["page_types"].append(page_gap["page_type_label"])
        bucket["keywords"].append(shorten_question_label(str(row.get("keyword_raw") or ""), limit=14))
        stability = stability_map.get(normalize_text(str(row.get("keyword_raw") or "")), {})
        if stability:
            bucket["stability_scores"].append(float(stability.get("stability_score") or 0.0))

    intent_rows: list[dict[str, Any]] = []
    for item in grouped.values():
        avg_score = round(item["score_total"] / item["question_count"], 1) if item["question_count"] else 0.0
        avg_stability = (
            round(sum(item["stability_scores"]) / len(item["stability_scores"]), 1) if item["stability_scores"] else 0.0
        )
        if avg_stability >= 75:
            stability_label = "安定"
        elif avg_stability >= 50:
            stability_label = "やや揺れる"
        else:
            stability_label = "揺れ大"
        top_page_type = Counter(item["page_types"]).most_common(1)[0][0] if item["page_types"] else "-"
        urgency_score = item["needs_fix_count"] * 2 + max(0, item["question_count"] - item["visible_count"])
        intent_rows.append(
            {
                "intent_label": item["intent_label"],
                "question_count": item["question_count"],
                "needs_fix_count": item["needs_fix_count"],
                "avg_score": avg_score,
                "stability_label": stability_label,
                "top_page_type": top_page_type,
                "sample_questions": " / ".join(dedupe_preserve_order(item["keywords"])[:2]) or "-",
                "urgency_score": urgency_score,
            }
        )

    return sorted(intent_rows, key=lambda row: (-row["urgency_score"], row["avg_score"], -row["question_count"]))


def build_page_gap_rows(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    latest_rows = get_latest_rows_by_keyword(rows)
    grouped: dict[str, dict[str, Any]] = {}

    for row in latest_rows:
        payload = parse_json_object(row.get("output_json"))
        analysis_context = payload.get("analysis_context") or {}
        page_gap = infer_page_gap(
            str(row.get("keyword_raw") or ""),
            payload,
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
            target_hit=bool(row.get("target_domain_hit")),
            brand_hit=bool(row.get("brand_mention_hit")),
        )
        verdict = build_visibility_state_label(
            int(row.get("visibility_score") or 0),
            bool(row.get("target_domain_hit")),
            bool(row.get("brand_mention_hit")),
        )
        key = page_gap["page_type_key"]
        bucket = grouped.setdefault(
            key,
            {
                "page_type_label": page_gap["page_type_label"],
                "gap_label": page_gap["gap_label"],
                "question_count": 0,
                "needs_fix_count": 0,
                "priority_score": 0,
                "reasons": [],
                "next_steps": [],
                "keywords": [],
            },
        )
        bucket["question_count"] += 1
        bucket["reasons"].extend(page_gap["gap_reasons"])
        bucket["next_steps"].append(page_gap["next_step"])
        bucket["keywords"].append(shorten_question_label(str(row.get("keyword_raw") or ""), limit=14))
        if verdict in {"外部サイト優勢", "未露出"}:
            bucket["needs_fix_count"] += 1
            bucket["priority_score"] += 2
        if not row.get("target_domain_hit"):
            bucket["priority_score"] += 1

    gap_rows: list[dict[str, Any]] = []
    for item in grouped.values():
        if item["priority_score"] >= 4:
            priority_label = "最優先"
        elif item["priority_score"] >= 2:
            priority_label = "優先"
        else:
            priority_label = "監視"
        next_step = Counter(item["next_steps"]).most_common(1)[0][0] if item["next_steps"] else "-"
        reasons = dedupe_preserve_order(item["reasons"])[:2]
        gap_rows.append(
            {
                "page_type_label": item["page_type_label"],
                "gap_label": item["gap_label"],
                "question_count": item["question_count"],
                "needs_fix_count": item["needs_fix_count"],
                "priority_label": priority_label,
                "reason_summary": " / ".join(reasons) if reasons else "-",
                "next_step": next_step,
                "sample_questions": " / ".join(dedupe_preserve_order(item["keywords"])[:2]) or "-",
                "priority_score": item["priority_score"],
            }
        )

    return sorted(gap_rows, key=lambda row: (-row["priority_score"], -row["question_count"], row["page_type_label"]))


def build_guardrail_text_class(status: str) -> str:
    if status == "ok":
        return "text-self"
    if status in {"warning", "blocked"}:
        return "text-external"
    return "text-support"


def get_latest_rows_by_keyword(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if rows and any(row.get("internal_query_count") is not None or row.get("executed_queries_json") for row in rows):
        return rows
    return build_query_rollup_rows(rows)


def wrap_chart_question_label(text: Any, chunk_size: int = 16, max_chars: int = 32) -> str:
    value = str(text or "").strip()
    if not value:
        return "-"
    compact = value[:max_chars]
    chunks = [compact[index : index + chunk_size] for index in range(0, len(compact), chunk_size)]
    label = "<br>".join(chunks)
    if len(value) > max_chars:
        label += "…"
    return label


def filter_rows_for_active_scope(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    keyword_set = {normalize_text(keyword) for keyword in config.keywords if normalize_text(keyword)}
    target_host = normalize_host(config.target_domain)
    active_mode = normalize_text(config.analysis_mode) or ANALYSIS_MODE_MARKET
    if not keyword_set and not target_host:
        filtered_rows = rows
    else:
        filtered_rows: list[dict[str, Any]] = []
        for row in rows:
            row_keyword = normalize_text(str(row.get("keyword_raw") or row.get("keyword_norm") or ""))
            if keyword_set and row_keyword not in keyword_set:
                continue

            if target_host:
                payload = parse_json_object(row.get("output_json"))
                analysis_context = payload.get("analysis_context") or {}
                row_target_host = normalize_host(analysis_context.get("target_domain") or "")
                if not row_target_host:
                    continue
                if not (row_target_host == target_host or row_target_host.endswith(f".{target_host}")):
                    continue

            filtered_rows.append(row)

    return [
        row
        for row in filtered_rows
        if (resolve_row_analysis_mode(row) or ANALYSIS_MODE_MARKET) == active_mode
    ]


def extract_competitor_mentions(payload: dict[str, Any]) -> list[str]:
    seen: list[str] = []
    for item in payload.get("competitor_mentions") or []:
        value = str(item or "").strip()
        if value and value not in seen:
            seen.append(value)
    return seen


def extract_competitor_terms(payload: dict[str, Any], config: AppConfig) -> list[str]:
    analysis_context = payload.get("analysis_context") or {}
    raw_terms = analysis_context.get("competitor_terms") or config.competitor_terms
    seen: list[str] = []
    for item in raw_terms or []:
        value = str(item or "").strip()
        if value and value not in seen:
            seen.append(value)
    return seen


def build_visibility_state_label(score: int, target_hit: bool, brand_hit: bool) -> str:
    return classify_visibility_verdict(score, target_hit, brand_hit)


def build_verdict_text_class(verdict: str) -> str:
    if verdict == "自社優勢":
        return "text-self"
    if verdict in {"外部サイト優勢", "未露出"}:
        return "text-external"
    return "text-competitive"


def build_verdict_chip_class(verdict: str) -> str:
    if verdict == "自社優勢":
        return "signal-positive"
    if verdict in {"外部サイト優勢", "未露出"}:
        return "signal-negative"
    return "signal-neutral"


def build_keyword_verdict_summary(row: dict[str, Any], payload: dict[str, Any]) -> str:
    score = int(row.get("visibility_score") or 0)
    target_hit = bool(row.get("target_domain_hit"))
    brand_hit = bool(row.get("brand_mention_hit"))
    competitors = extract_competitor_mentions(payload)
    verdict = build_visibility_state_label(score, target_hit, brand_hit)
    analysis_mode = resolve_analysis_mode(payload)

    if analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
        if target_hit and score >= 70:
            return "自社サイトだけで、この質問に答える根拠を十分に出せています。"
        if target_hit:
            return "自社サイトだけでも答えは返せますが、根拠や見出しの厚みはまだ弱めです。"
        return "自社サイトだけでは、この質問に答える根拠をまだ作れていません。"

    if verdict == "自社優勢":
        if competitors:
            return (
                f"自社URLが根拠に入り、{', '.join(competitors[:2])} も見えていますが、"
                "この質問では自社が先に見つかっています。"
            )
        return "自社URLが根拠に入り、この質問では自社が先に見つかっています。"
    if verdict == "自社あり":
        if competitors:
            return f"自社URLやブランド名は出ていますが、{', '.join(competitors[:2])} や外部サイトと並ぶ状態です。"
        return "自社URLやブランド名は出ていますが、外部サイトと並ぶ状態です。"
    if verdict == "外部サイト優勢":
        if competitors:
            return f"{', '.join(competitors[:2])} や外部サイトが先に見られ、自社はまだ前に出ていません。"
        return "外部サイトが先に見られ、自社はまだ前に出ていません。"
    if competitors:
        return f"この質問では自社URLもブランド名も確認できず、{', '.join(competitors[:2])} や外部サイトが中心です。"
    return "この質問では自社URLもブランド名も確認できず、まだ露出を作れていません。"


def build_visibility_plain_summary(row: dict[str, Any], payload: dict[str, Any]) -> str:
    score = int(row.get("visibility_score") or 0)
    target_hit = bool(row.get("target_domain_hit"))
    brand_hit = bool(row.get("brand_mention_hit"))
    confidence = localize_confidence_label(str(payload.get("confidence") or "low"))
    competitor_mentions = extract_competitor_mentions(payload)
    verdict = build_visibility_state_label(score, target_hit, brand_hit)
    analysis_mode = resolve_analysis_mode(payload)

    if analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
        parts = [
            "この結果は自社監査です。",
            "自社URLだけで根拠を作れています。" if target_hit else "自社URLだけでは根拠を作れていません。",
            "ブランド名の言及は確認できています。" if brand_hit else "ブランド想起もまだ弱い状態です。",
            f"見つかりやすさは {score}/100、判定の確からしさは {confidence} です。",
        ]
        return " ".join(parts)

    parts: list[str] = []
    if target_hit:
        parts.append("自社URLはAIの回答や引用に入っています。")
    else:
        parts.append("自社URLはAIの回答や引用に入っていません。")

    if brand_hit:
        parts.append("ブランド名の言及は確認できています。")
    else:
        parts.append("ブランド名の言及も弱い状態です。")

    if competitor_mentions:
        parts.append(f"目立った競合は {', '.join(competitor_mentions[:2])} です。")
    elif verdict == "外部サイト優勢":
        parts.append("外部サイトや一般的な解説ページが先に使われています。")
    elif verdict == "未露出":
        parts.append("今回の回答では自社の露出を確認できませんでした。")

    parts.append(f"見つかりやすさは {score}/100、判定の確からしさは {confidence} です。")
    return " ".join(parts)


def build_result_digest(row: dict[str, Any], payload: dict[str, Any]) -> str:
    score = int(row.get("visibility_score") or 0)
    target_hit = bool(row.get("target_domain_hit"))
    brand_hit = bool(row.get("brand_mention_hit"))
    competitors = extract_competitor_mentions(payload)
    verdict = build_visibility_state_label(score, target_hit, brand_hit)
    analysis_mode = resolve_analysis_mode(payload)
    if analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
        if target_hit and score >= 70:
            return "自社資産だけで答え切れています"
        if target_hit:
            return "自社資産だけでも一部は答えられます"
        return "自社資産だけでは答え切れていません"
    if verdict == "自社優勢":
        if competitors:
            return f"{', '.join(competitors[:2])} より前に出ています"
        return "外部サイトより前に出ています"
    if verdict == "自社あり":
        if competitors:
            return f"{', '.join(competitors[:2])} や外部サイトと並んでいます"
        return "外部サイトと並んでいます"
    if verdict == "外部サイト優勢":
        if competitors:
            return f"{', '.join(competitors[:2])} や外部サイトが先行しています"
        return "外部サイトが先行しています"
    if competitors:
        return f"{', '.join(competitors[:2])} に対して自社未露出です"
    return "自社の露出を確認できません"


def format_list_or_dash(items: list[str] | None) -> str:
    values = [str(item).strip() for item in (items or []) if str(item).strip()]
    return ", ".join(values) if values else "-"


def build_source_groups(
    sources: list[dict[str, Any]],
    payload: dict[str, Any],
    config: AppConfig,
) -> dict[str, list[dict[str, Any]]]:
    target_host = normalize_host((payload.get("analysis_context") or {}).get("target_domain") or config.target_domain)
    competitor_terms = [term.lower() for term in extract_competitor_terms(payload, config)]
    grouped: dict[str, list[dict[str, Any]]] = {"self": [], "competitor": [], "third_party": []}
    seen_urls: set[str] = set()

    for raw_source in sources:
        url = str(raw_source.get("url") or "").strip()
        title = str(raw_source.get("title") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        host = normalize_host(url)
        haystack = f"{title} {url}".lower()
        source = {"url": url, "title": title or url, "host": host}
        if target_host and host and (host == target_host or host.endswith(f".{target_host}")):
            grouped["self"].append(source)
        elif any(term and term in haystack for term in competitor_terms):
            grouped["competitor"].append(source)
        else:
            grouped["third_party"].append(source)
    return grouped


def extract_cited_sources(row: dict[str, Any], payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    payload = payload or parse_json_object(row.get("output_json"))
    raw_citations = parse_citations_json(row.get("citations_json") or payload.get("citations") or [])
    deduped: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for citation in raw_citations:
        url = str(citation.get("url") or "").strip()
        title = str(citation.get("title") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append({"url": url, "title": title or url})
    return deduped


def build_source_group_summary(grouped_sources: dict[str, list[dict[str, Any]]], payload: dict[str, Any]) -> str:
    competitors = extract_competitor_mentions(payload)
    self_count = len(grouped_sources["self"])
    competitor_count = len(grouped_sources["competitor"])
    third_party_count = len(grouped_sources["third_party"])
    analysis_mode = resolve_analysis_mode(payload)
    if analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
        if self_count:
            return f"自社監査では、自社URLの根拠が {self_count}件確認できました。"
        return "自社監査では、まだ根拠として使われる自社URLを確認できませんでした。"
    if competitors and competitor_count:
        return (
            f"自社 {self_count}件、競合 {competitor_count}件、外部サイト {third_party_count}件。"
            f" {', '.join(competitors[:2])} と並んで見られています。"
        )
    if self_count and third_party_count:
        return f"自社 {self_count}件、外部サイト {third_party_count}件。自社も見えますが、外部サイトの根拠も多い状態です。"
    if self_count:
        return f"自社の根拠URLが {self_count}件で、今回の結論を支えています。"
    if competitors:
        return f"自社URLは見えず、{', '.join(competitors[:2])} や外部サイトが根拠に使われています。"
    return "今回は外部サイトの根拠が中心で、自社URLは確認できませんでした。"


def build_citation_share_series(rows: list[dict[str, Any]], config: AppConfig, limit: int = 8) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        payload = parse_json_object(row.get("output_json"))
        grouped_sources = build_source_groups(extract_cited_sources(row, payload), payload, config)
        for category in ("self", "competitor", "third_party"):
            seen_hosts: set[str] = set()
            for source in grouped_sources[category]:
                host = normalize_host(source.get("host") or source.get("url"))
                if not host or host in seen_hosts:
                    continue
                seen_hosts.add(host)
                counts[(category, host)] += 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0][1]))[:limit]
    return [
        {"category": category, "host": host, "count": count}
        for (category, host), count in ordered
    ]


def build_keyword_volatility_series(rows: list[dict[str, Any]], limit: int = 4) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        keyword = str(row.get("keyword_raw") or "").strip()
        if not keyword:
            continue
        grouped.setdefault(keyword, []).append(row)

    ordered_keywords = sorted(
        grouped.items(),
        key=lambda item: max(float(entry.get("analyzed_at") or 0.0) for entry in item[1]),
        reverse=True,
    )[:limit]

    series: list[dict[str, Any]] = []
    for keyword, items in ordered_keywords:
        ordered_items = sorted(items, key=lambda row: float(row.get("analyzed_at") or 0.0))
        points = []
        for item in ordered_items:
            score = int(item.get("visibility_score") or 0)
            verdict = build_visibility_state_label(
                score,
                bool(item.get("target_domain_hit")),
                bool(item.get("brand_mention_hit")),
            )
            points.append(
                {
                    "timestamp": format_timestamp(item.get("analyzed_at")),
                    "score": score,
                    "verdict": verdict,
                    "label": str(item.get("keyword_raw") or keyword),
                }
            )
        series.append({"keyword": keyword, "points": points})
    return series


def build_analysis_context_lines(payload: dict[str, Any]) -> list[str]:
    analysis_context = payload.get("analysis_context") or {}
    if not analysis_context:
        return []
    return [
        f"監査モード: {localize_analysis_mode(str(analysis_context.get('analysis_mode') or ANALYSIS_MODE_MARKET))}",
        f"自社URL: {analysis_context.get('target_domain') or '-'}",
        f"ブランド名: {format_list_or_dash(analysis_context.get('brand_terms'))}",
        f"競合語: {format_list_or_dash(analysis_context.get('competitor_terms'))}",
        f"元質問: {analysis_context.get('user_query_raw') or analysis_context.get('question') or '-'}",
        f"内部で使った質問: {analysis_context.get('executed_query') or analysis_context.get('question') or '-'}",
        f"優先ドメイン: {format_list_or_dash(analysis_context.get('allowed_domains'))}",
        f"自社監査の対象ドメイン: {format_list_or_dash(analysis_context.get('owned_only_domains'))}",
        (
            f"推論: {analysis_context.get('reasoning_effort') or '-'} / "
            f"検索: {analysis_context.get('search_context_size') or '-'}"
        ),
        (
            "キャッシュ: "
            f"{analysis_context.get('prompt_cache_retention_effective') or 'in_memory'} "
            f"(設定値 {analysis_context.get('prompt_cache_retention_requested') or 'in_memory'})"
        ),
    ]


def localize_action_text(action: Any) -> str:
    text = str(action or "").strip()
    if not text:
        return "改善案はまだありません。"

    lower = text.lower()
    patterns = [
        ("comparison", "比較ページを作るか、比較ページの内容を強くする"),
        ("best for", "比較・選定系の質問に答えるページを用意する"),
        ("case stud", "導入事例や実績ページを増やす"),
        ("faq", "FAQでこの質問に直接答える"),
        ("pricing", "料金やプランの説明を分かりやすくする"),
        ("proof", "実績・根拠・数字を入れて信頼を強くする"),
        ("explainer", "用語解説ページを作り、見出しで答えを明確にする"),
        ("landing page", "この質問に近いLPの情報を厚くする"),
        ("buyer", "想定顧客ごとのページを分けて用意する"),
        ("workflow", "利用シーンや使い方を具体的に説明する"),
        ("publish", "新しいページを公開して答えを増やす"),
        ("optimiz", "既存ページの答え方を見直す"),
        ("citation", "引用されやすいように根拠と出典を明記する"),
    ]
    for needle, localized in patterns:
        if needle in lower:
            return localized
    return text


def shorten_action_headline(action: str) -> str:
    text = str(action or "").strip()
    if not text:
        return "優先アクションなし"
    mapping = [
        ("比較", "比較ページを強化"),
        ("FAQ", "FAQを強化"),
        ("料金", "料金説明を補強"),
        ("事例", "導入事例を増やす"),
        ("LP", "LPを強化"),
        ("引用", "根拠を明記"),
        ("見直す", "既存ページを見直す"),
        ("追加", "新規ページを追加"),
    ]
    for needle, headline in mapping:
        if needle in text:
            return headline
    return text[:18] + ("…" if len(text) > 18 else "")


def shorten_question_label(keyword: str, limit: int = 18) -> str:
    text = " ".join(str(keyword or "").split())
    if not text:
        return "この質問"
    return text[:limit] + ("…" if len(text) > limit else "")


def format_scoped_action(keyword: str, action: str) -> str:
    label = shorten_question_label(keyword, limit=20)
    return f"「{label}」: {action}"


def build_scoped_action_headline(keyword: str, action: str) -> str:
    action_label = shorten_action_headline(action)
    keyword_label = shorten_question_label(keyword, limit=12)
    if not keyword or keyword_label == "この質問":
        return action_label
    return f"「{keyword_label}」で {action_label}"


def build_priority_actions(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    ordered: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        keyword = str(row.get("keyword_raw") or "").strip()
        payload = parse_json_object(row.get("output_json"))
        for action in payload.get("recommended_actions") or []:
            localized = localize_action_text(action)
            dedupe_key = (keyword, localized)
            if localized and dedupe_key not in seen:
                seen.add(dedupe_key)
                ordered.append(
                    {
                        "keyword": keyword,
                        "action": localized,
                        "headline": build_scoped_action_headline(keyword, localized),
                        "summary": format_scoped_action(keyword, localized),
                    }
                )
            if len(ordered) >= 3:
                return ordered
    return ordered


def build_portfolio_story(rows: list[dict[str, Any]], config: AppConfig) -> dict[str, Any]:
    latest_rows = get_latest_rows_by_keyword(rows)
    total_topics = len(latest_rows)
    is_owned_only = config.analysis_mode == ANALYSIS_MODE_OWNED_ONLY
    if total_topics == 0:
        return {
            "overall_label": "未確認" if not is_owned_only else "監査前",
            "overall_summary": (
                "まだ分析結果がありません。まずは 1 回実行して、いまの見え方を作ってください。"
                if not is_owned_only
                else "まだ自社監査の結果がありません。まずは 1 回実行して、自社サイトだけで答えられるかを確認してください。"
            ),
            "competition_label": "外部情報は未確認" if not is_owned_only else "自社監査前",
            "competition_summary": (
                "よく出る外部サイト名や一緒に語られる名前は、結果が保存されるとここに出ます。"
                if not is_owned_only
                else "自社監査では、どの自社URLが根拠になるかをここに出します。"
            ),
            "action_headline": "分析を実行" if not is_owned_only else "自社監査を実行",
            "action_summary": (
                "結果ができると、次に直すことを 3 点以内でここに出します。"
                if not is_owned_only
                else "結果ができると、どのページ種別を先に補強すべきかをここに出します。"
            ),
            "priority_actions": [],
            "total_topics": 0,
            "visible_topics": 0,
            "competitor_topics": 0,
            "needs_fix_topics": 0,
            "third_party_topics": 0,
            "wins": 0,
            "ties": 0,
            "losses": 0,
        }

    wins = 0
    ties = 0
    losses = 0
    no_visibility = 0
    visible_topics = 0
    competitor_topics = 0
    third_party_topics = 0
    competitor_counter: Counter[str] = Counter()

    for row in latest_rows:
        payload = parse_json_object(row.get("output_json"))
        verdict = build_visibility_state_label(
            int(row.get("visibility_score") or 0),
            bool(row.get("target_domain_hit")),
            bool(row.get("brand_mention_hit")),
        )
        if verdict == "自社優勢":
            wins += 1
        elif verdict == "自社あり":
            ties += 1
        elif verdict == "外部サイト優勢":
            losses += 1
        else:
            no_visibility += 1
        if row.get("target_domain_hit"):
            visible_topics += 1
        competitors = extract_competitor_mentions(payload)
        if competitors:
            competitor_topics += 1
            competitor_counter.update(competitors)
        if not row.get("target_domain_hit"):
            third_party_topics += 1

    needs_fix_topics = losses + no_visibility

    if is_owned_only:
        if visible_topics == total_topics and needs_fix_topics == 0:
            overall_label = "自社資産で回答可能"
            overall_summary = (
                f"直近 {total_topics} 件の質問では、自社サイトだけで答えられる質問が揃っています。"
                " 現状の情報設計で、Owned-only 監査は通過できています。"
            )
        elif visible_topics == 0:
            overall_label = "自社根拠不足"
            overall_summary = (
                f"直近 {total_topics} 件の質問では、自社サイトだけで根拠を返せた質問がまだありません。"
                " FAQ、比較、料金など答えを直接置くページの補強が必要です。"
            )
        else:
            overall_label = "一部は回答可能"
            overall_summary = (
                f"直近 {total_topics} 件の質問では {visible_topics} 件で自社サイトだけでも答えられますが、"
                f" {needs_fix_topics} 件はまだ不足しています。"
            )
    elif wins * 3 >= total_topics * 2 and needs_fix_topics == 0:
        overall_label = "自社優勢"
        overall_summary = (
            f"直近 {total_topics} 件の質問では {wins} 件で自社が明確に前に出ています。"
            f" 自社ありの質問も {ties} 件あり、全体として露出を確保できています。"
        )
    elif no_visibility * 3 >= total_topics * 2:
        overall_label = "未露出"
        overall_summary = (
            f"直近 {total_topics} 件の質問では {no_visibility} 件で自社URLもブランド名も確認できていません。"
            " まずは露出を作るためのFAQや比較ページの補強が必要です。"
        )
    elif needs_fix_topics * 2 >= total_topics and wins == 0:
        overall_label = "外部サイト優勢"
        overall_summary = (
            f"直近 {total_topics} 件の質問では {losses} 件で外部サイトが先行し、"
            f" 未露出も {no_visibility} 件あります。自社はまだ前に出ていません。"
        )
    else:
        overall_label = "自社あり"
        overall_summary = (
            f"直近 {total_topics} 件では、自社優勢 {wins} 件、自社あり {ties} 件です。"
            " 自社の露出はありますが、まだ外部サイトに押し切れていない質問が残っています。"
        )

    top_competitors = [name for name, _count in competitor_counter.most_common(2)]
    configured_competitors = config.competitor_terms or []
    if is_owned_only:
        competition_label = "自社サイトだけで回答可能" if visible_topics else "自社サイトだけでは不足"
        competition_summary = (
            f"自社監査では {visible_topics}/{total_topics} 件で自社URLが根拠に入りました。"
            f" まだ不足している質問は {needs_fix_topics} 件です。"
        )
    elif top_competitors:
        lead_name = " / ".join(top_competitors)
        if overall_label == "自社優勢":
            competition_label = f"{lead_name} が一緒に出やすい"
        elif overall_label == "自社あり":
            competition_label = f"{lead_name} もよく出る"
        elif overall_label == "外部サイト優勢":
            competition_label = f"{lead_name} が目立つ"
        else:
            competition_label = f"{lead_name} が先に見つかる"
        competition_summary = (
            f"{competitor_topics}/{total_topics} 件で外部名や外部サイト名が根拠に入りました。"
            f" 自社がまだ弱い質問は {needs_fix_topics} 件あります。"
        )
    elif configured_competitors:
        competition_label = "比較語は設定済み"
        competition_summary = (
            "比較したい名前は設定されていますが、直近結果ではその名前の出現は強くありません。"
            f" 自社がまだ弱い質問は {needs_fix_topics} 件です。"
        )
    else:
        competition_label = "外部サイト中心"
        competition_summary = (
            "比較したい名前が未設定のため、いまは自社と外部サイトの出方だけを見ています。"
            " 必要なら後から比較したい名前を追加できます。"
        )

    action_rows = sorted(
        latest_rows,
        key=lambda row: (
            {"未露出": 0, "外部サイト優勢": 1, "自社あり": 2, "自社優勢": 3}.get(
                build_visibility_state_label(
                    int(row.get("visibility_score") or 0),
                    bool(row.get("target_domain_hit")),
                    bool(row.get("brand_mention_hit")),
                ),
                9,
            ),
            row.get("keyword_raw") or "",
        ),
    )
    priority_actions = build_priority_actions(action_rows)
    first_action = priority_actions[0] if priority_actions else None
    action_headline = (
        first_action["headline"] if first_action else "まずは分析を実行して負け筋を特定する"
    )
    action_summary = (
        " / ".join(item["summary"] for item in priority_actions[:3])
        if priority_actions
        else "改善案は結果作成後に表示されます。"
    )

    return {
        "overall_label": overall_label,
        "overall_summary": overall_summary,
        "competition_label": competition_label,
        "competition_summary": competition_summary,
        "action_headline": action_headline,
        "action_summary": action_summary,
        "priority_actions": priority_actions,
        "total_topics": total_topics,
        "visible_topics": visible_topics,
        "competitor_topics": competitor_topics,
        "needs_fix_topics": needs_fix_topics,
        "third_party_topics": third_party_topics,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "no_visibility": no_visibility,
    }


def build_runtime_microcopy(config: AppConfig) -> str:
    provider_option = get_provider_option(config.provider)
    provider = provider_display_label(provider_option)
    effective_cache_retention = (
        resolve_prompt_cache_retention(config.model, config.prompt_cache_retention)
        if provider_supports_prompt_cache(provider_option.key)
        else "in_memory"
    )
    cache_note = (
        "（使えない条件では自動でメモリ内へ切り替え）"
        if provider_supports_prompt_cache(provider_option.key)
        and config.prompt_cache_retention == "24h"
        and effective_cache_retention != "24h"
        else ""
    )
    batch_note = (
        f"まとめ確認は {provider_option.partial_display_after_hours}時間で暫定表示 / "
        if provider_option.supports_batch
        else "まとめ確認は provider 実装後に有効化 / "
    )
    return (
        f"現在の接続: {provider} / 推論 {config.reasoning_effort} / "
        f"検索 {config.search_context_size} / キャッシュ {localize_cache_retention_label(effective_cache_retention)}{cache_note} / "
        f"{batch_note}"
        f"内部質問上限 {get_provider_total_question_budget(provider_option.key)}件 / "
        f"実行ガード {('上限で停止' if config.budget_guardrail_mode == 'stop' else '上限前に警告')}"
    )


def localize_run_mode(run_mode: Any) -> str:
    mode = str(run_mode or "").lower()
    if mode == "scheduled":
        return "定期"
    if mode == "batch":
        return "まとめ確認"
    return "手動"


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


def build_batch_job_option_label(row: dict[str, Any]) -> str:
    imported = int(row.get("imported_result_count") or 0) + int(row.get("imported_error_count") or 0)
    return (
        f"{localize_run_mode(row.get('run_mode'))} | {row.get('question_set_name') or row.get('batch_job_id')} | "
        f"{localize_batch_status(row.get('status'))} | {imported}/{int(row.get('request_count') or 0)}件取込"
    )


def build_batch_table_columns() -> list[dict[str, str]]:
    return [
        {"name": "submitted_at", "label": "投入", "field": "submitted_at"},
        {"name": "run_mode", "label": "方式", "field": "run_mode"},
        {"name": "question_set_name", "label": "確認内容", "field": "question_set_name"},
        {"name": "status_label", "label": "状態", "field": "status_label"},
        {"name": "request_count", "label": "件数", "field": "request_count"},
        {"name": "progress_label", "label": "進み具合", "field": "progress_label"},
        {"name": "import_label", "label": "取込", "field": "import_label"},
    ]


def provider_display_label(provider: ProviderOption) -> str:
    return "ChatGPT" if provider.key == "openai" else provider.label


def get_visible_provider_catalog() -> list[ProviderOption]:
    return [provider for provider in get_provider_catalog() if provider.key in VISIBLE_PROVIDER_KEYS]


def normalize_provider_config(config: AppConfig) -> AppConfig:
    next_config = config
    provider = get_provider_option(next_config.provider)
    fallback = get_provider_option("openai")
    if provider.key not in VISIBLE_PROVIDER_KEYS or not provider.implemented or not provider.supports_live_requests:
        next_model = get_provider_effective_model(fallback.key, next_config.model)
        return next_config.model_copy(update={"provider": fallback.key, "model": next_model})
    next_updates: dict[str, Any] = {
        "model": get_provider_effective_model(provider.key, next_config.model),
    }
    if provider.supports_prompt_cache:
        if str(next_config.prompt_cache_retention or "").strip().lower() != "24h":
            next_updates["prompt_cache_retention"] = "24h"
    else:
        next_updates["prompt_cache_retention"] = "in_memory"
    if (
        next_updates.get("model") != next_config.model
        or next_updates.get("prompt_cache_retention", next_config.prompt_cache_retention)
        != next_config.prompt_cache_retention
    ):
        return next_config.model_copy(update=next_updates)
    return next_config


def refresh_provider_controls(
    config: AppConfig,
    provider_buttons: dict[str, ui.button],
) -> AppConfig:
    next_config = normalize_provider_config(config)

    for key, button in provider_buttons.items():
        option = get_provider_option(key)
        if not option.implemented:
            tone = "provider-chip-button provider-chip-button-disabled"
            button.disable()
        elif key == next_config.provider:
            tone = "provider-chip-button provider-chip-button-active"
            button.enable()
        else:
            tone = "provider-chip-button provider-chip-button-ready"
            button.enable()
        button.classes(replace=tone)
        button.update()

    return next_config


def build_scope_markdown(config: AppConfig) -> str:
    return (
        f"- 実行先: `{provider_display_label(get_provider_option(config.provider))}`\n"
        "- API: Responses API + `web_search`\n"
        "- プロンプトキャッシュの効き方を画面で確認\n"
        "- `allowed_domains` は優先参照として扱います\n"
        f"- 実行ガード: `{('上限で停止' if config.budget_guardrail_mode == 'stop' else '上限前に警告')}`\n"
        "- 履歴は SQLite に保存"
    )


def build_runtime_markdown(config: AppConfig) -> str:
    return (
        f"- 接続先: `{provider_display_label(get_provider_option(config.provider))}`\n"
        f"- 推論の深さ: `{config.reasoning_effort}`\n"
        f"- キャッシュ識別キー: `{config.prompt_cache_key}`\n"
        f"- キャッシュ保持: `{localize_cache_retention_label(config.prompt_cache_retention)}`\n"
        f"- 検索深度: `{config.search_context_size}`\n"
        f"- 実行ガード: `{('上限で停止' if config.budget_guardrail_mode == 'stop' else '上限前に警告')}`\n"
        "- `allowed_domains`: 強制ではない優先参照"
    )


def build_result_table_columns(show_costs: bool) -> list[dict[str, str]]:
    return [
        {"name": "analyzed_at", "label": "確認時刻", "field": "analyzed_at"},
        {"name": "run_mode", "label": "実行方式", "field": "run_mode"},
        {"name": "keyword_raw", "label": "調べた質問", "field": "keyword_raw"},
        {"name": "intent_label", "label": "意図", "field": "intent_label"},
        {"name": "page_gap_label", "label": "不足ページ", "field": "page_gap_label"},
        {"name": "visibility_label", "label": "現状判定", "field": "visibility_label"},
        {"name": "result_digest", "label": "競合との位置", "field": "result_digest"},
        {"name": "target_domain_hit", "label": "自社URL", "field": "target_domain_hit"},
        {"name": "brand_mention_hit", "label": "ブランド名", "field": "brand_mention_hit"},
        {"name": "answer_type_label", "label": "返答タイプ", "field": "answer_type_label"},
    ]


def build_intent_table_columns() -> list[dict[str, str]]:
    return [
        {"name": "intent_label", "label": "意図", "field": "intent_label"},
        {"name": "question_count", "label": "質問数", "field": "question_count"},
        {"name": "needs_fix_count", "label": "負け筋", "field": "needs_fix_count"},
        {"name": "avg_score", "label": "平均スコア", "field": "avg_score"},
        {"name": "stability_label", "label": "揺れ幅", "field": "stability_label"},
        {"name": "top_page_type", "label": "不足ページ", "field": "top_page_type"},
    ]


def build_gap_table_columns() -> list[dict[str, str]]:
    return [
        {"name": "page_type_label", "label": "ページ種別", "field": "page_type_label"},
        {"name": "priority_label", "label": "優先度", "field": "priority_label"},
        {"name": "question_count", "label": "対象質問", "field": "question_count"},
        {"name": "needs_fix_count", "label": "未解消", "field": "needs_fix_count"},
        {"name": "reason_summary", "label": "不足理由", "field": "reason_summary"},
        {"name": "next_step", "label": "制作着手", "field": "next_step"},
    ]


def build_run_table_columns(show_costs: bool) -> list[dict[str, str]]:
    return [
        {"name": "started_at", "label": "開始", "field": "started_at"},
        {"name": "finished_at", "label": "終了", "field": "finished_at"},
        {"name": "run_mode", "label": "実行方式", "field": "run_mode"},
        {"name": "question_set_name", "label": "確認内容", "field": "question_set_name"},
        {"name": "repeat_count", "label": "繰り返し", "field": "repeat_count"},
        {"name": "result_count", "label": "結果件数", "field": "result_count"},
    ]


def build_question_set_option_label(row: dict[str, Any]) -> str:
    last_run = format_timestamp(row.get("last_run_at"))
    last_mode = localize_run_mode(row.get("last_run_mode")) if row.get("last_run_mode") else "未実行"
    return f"{row.get('name')} | 最終 {last_run} | {last_mode}"


def build_question_set_table_columns() -> list[dict[str, str]]:
    return [
        {"name": "name", "label": "確認内容", "field": "name"},
        {"name": "updated_at", "label": "更新", "field": "updated_at"},
        {"name": "last_run_at", "label": "最終実行", "field": "last_run_at"},
        {"name": "last_run_mode", "label": "方式", "field": "last_run_mode"},
    ]


def build_schedule_table_columns() -> list[dict[str, str]]:
    return [
        {"name": "name", "label": "定期チェック", "field": "name"},
        {"name": "question_set_name", "label": "確認内容", "field": "question_set_name"},
        {"name": "schedule_label", "label": "曜日 / 時刻", "field": "schedule_label"},
        {"name": "weekly_run_count", "label": "週回数", "field": "weekly_run_count"},
        {"name": "next_run_label", "label": "次回", "field": "next_run_label"},
        {"name": "status_label", "label": "状態", "field": "status_label"},
    ]


def build_schedule_option_label(row: dict[str, Any]) -> str:
    status_label = localize_schedule_status(row.get("last_status") or ("enabled" if row.get("enabled") else "disabled"))
    return (
        f"{row.get('name')} | {row.get('question_set_name') or '確認内容なし'} | "
        f"{format_weekdays_label(parse_weekdays_csv(row.get('weekdays_csv')))} {row.get('time_of_day')} | {status_label}"
    )


def build_question_set_snapshot(question_set: dict[str, Any]) -> dict[str, Any]:
    cfg = AppConfig.model_validate_json(question_set["config_json"])
    queries = dedupe_preserve_order(cfg.keywords)
    return {
        "kind": "question_set",
        "label": str(question_set.get("name") or "確認内容"),
        "queries": queries,
        "query_count": len(queries),
        "analysis_mode": localize_analysis_mode(cfg.analysis_mode),
        "repeat_count": int(cfg.repeat_count or 0),
        "reasoning_effort": cfg.reasoning_effort,
        "target_domain": normalize_text(cfg.target_domain) or "-",
        "brand_terms": join_csv(dedupe_preserve_order(cfg.brand_terms)) or "-",
        "competitor_terms": join_csv(dedupe_preserve_order(cfg.competitor_terms)) or "-",
        "allowed_domains": join_csv(dedupe_preserve_order(cfg.allowed_domains)) or "-",
        "weekdays_label": "-",
        "time_of_day": "-",
        "timezone": cfg.timezone or "-",
        "enabled_label": "-",
    }


def build_schedule_snapshot(schedule: dict[str, Any]) -> dict[str, Any]:
    linked_question_set = db.get_question_set(str(schedule.get("question_set_id") or ""))
    if linked_question_set:
        snapshot = build_question_set_snapshot(linked_question_set)
    else:
        snapshot = {
            "kind": "schedule",
            "label": str(schedule.get("name") or "定期チェック"),
            "queries": [],
            "query_count": 0,
            "analysis_mode": "-",
            "repeat_count": 0,
            "reasoning_effort": "-",
            "target_domain": "-",
            "brand_terms": "-",
            "competitor_terms": "-",
            "allowed_domains": "-",
            "timezone": "-",
        }
    snapshot.update(
        {
            "kind": "schedule",
            "label": str(schedule.get("name") or "定期チェック"),
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
        ("repeat_count", "繰り返し"),
        ("reasoning_effort", "推論"),
        ("target_domain", "自社URL"),
        ("brand_terms", "ブランド語"),
        ("competitor_terms", "競合語"),
        ("allowed_domains", "追加ドメイン"),
        ("weekdays_label", "曜日"),
        ("time_of_day", "時刻"),
        ("timezone", "タイムゾーン"),
        ("enabled_label", "有効状態"),
    ]
    field_diffs: list[dict[str, str]] = []
    for key, label in field_specs:
        left_value = normalize_text(str(left.get(key) or "-")) or "-"
        right_value = normalize_text(str(right.get(key) or "-")) or "-"
        if left_value == right_value:
            continue
        field_diffs.append({"label": label, "left": left_value, "right": right_value})

    left_queries = dedupe_preserve_order([str(item or "") for item in left.get("queries") or []])
    right_queries = dedupe_preserve_order([str(item or "") for item in right.get("queries") or []])
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
        "question_set": "確認内容単位",
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


def build_scheduler_status_text() -> str:
    snapshot = scheduler_service.status_snapshot()
    if not snapshot["active"]:
        return "定期チェックは停止中です"
    return (
        f"定期チェック 稼働中 | 最終確認 {format_timestamp(snapshot['last_tick_at'])} | "
        f"{snapshot['last_message']}"
    )


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
        "missing_question_set": "確認内容欠落",
        "invalid_scope": "監査条件不足",
        "empty_keywords": "質問なし",
    }
    return mapping.get(str(status or "").lower(), str(status or "-") or "-")


def write_export_files(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, str]]:
    raw_rows = build_raw_results_export_rows(rows, config)
    weekly_rows = build_weekly_summary_rows(rows, config)
    generated_at = format_timestamp(time.time())
    files = [
        ("raw_results.csv", raw_rows),
        ("weekly_summary.csv", weekly_rows),
        (
            "raw_results.json",
            {
                "generated_at": generated_at,
                "scope": {
                    "analysis_mode": config.analysis_mode,
                    "keywords": config.keywords,
                    "target_domain": config.target_domain,
                },
                "rows": raw_rows,
            },
        ),
    ]
    metadata: list[dict[str, str]] = []
    for filename, payload in files:
        path = EXPORTS_DIR / filename
        if filename.endswith(".csv"):
            rows_payload = payload if isinstance(payload, list) else []
            fieldnames = list(rows_payload[0].keys()) if rows_payload else ["generated_at"]
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                if rows_payload:
                    writer.writerows(rows_payload)
                else:
                    writer.writerow({"generated_at": generated_at})
        else:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        metadata.append(
            {
                "label": filename,
                "path": f"/exports/{filename}",
                "generated_at": generated_at,
            }
        )
    return metadata


def refresh_runtime_panels(
    config: AppConfig,
    runtime_micro_label: ui.label,
    cost_policy_label: ui.label,
) -> None:
    runtime_micro_label.text = build_runtime_microcopy(config)
    cost_policy_label.text = (
        "実行ガードは内部で維持しつつ、金額は画面に出しません。"
        f" 現在は実行件数が多いときに {('停止' if config.budget_guardrail_mode == 'stop' else '警告')} します。"
    )
    runtime_micro_label.update()
    cost_policy_label.update()


def refresh_latest_result_cards(
    recent_rows: list[dict[str, Any]],
    config: AppConfig,
    latest_result_container: ui.column,
    previous_delta_summary: dict[str, Any],
) -> None:
    latest_result_container.clear()
    with latest_result_container:
        if not recent_rows:
            with ui.card().classes("section-card p-5 w-full"):
                ui.label("最新結果").classes("section-font section-title text-[28px] font-bold")
                ui.label("まだ保存された分析はありません。まずは 1 回実行して結果を作成してください。").classes(
                    "text-[15px] leading-7 soft-label mt-2"
                )
            return

        latest = recent_rows[0]
        latest_payload = parse_json_object(latest.get("output_json"))
        grouped_sources = build_source_groups(extract_cited_sources(latest, latest_payload)[:5], latest_payload, config)
        analysis_context = latest_payload.get("analysis_context") or {}
        analysis_mode = resolve_analysis_mode(latest_payload)
        page_gap = infer_page_gap(
            str(latest.get("keyword_raw") or ""),
            latest_payload,
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
            target_hit=bool(latest.get("target_domain_hit")),
            brand_hit=bool(latest.get("brand_mention_hit")),
        )
        visibility_state = build_visibility_state_label(
            int(latest.get("visibility_score") or 0),
            bool(latest.get("target_domain_hit")),
            bool(latest.get("brand_mention_hit")),
        )
        verdict_summary = build_keyword_verdict_summary(latest, latest_payload)
        source_summary = build_source_group_summary(grouped_sources, latest_payload)
        competitor_mentions = extract_competitor_mentions(latest_payload)
        target_chip_class = "signal-positive" if latest.get("target_domain_hit") else "signal-negative"
        target_chip_text = "自社URLあり" if latest.get("target_domain_hit") else "自社URLなし"
        brand_chip_class = "signal-positive" if latest.get("brand_mention_hit") else "signal-neutral"
        brand_chip_text = "ブランド名あり" if latest.get("brand_mention_hit") else "ブランド名が弱い"
        verdict_text_class = build_verdict_text_class(visibility_state)
        rollup_meta = latest_payload.get("query_rollup") or {}
        query_notice_lines = []
        if latest.get("query_was_shortened"):
            query_notice_lines.append("この質問は内部で短く整えて計測しました。")
        if int(rollup_meta.get("executed_query_count") or latest.get("internal_query_count") or 0) > 1:
            query_notice_lines.append("この質問は関連する派生質問も含めて確認しました。")
        if analysis_mode == ANALYSIS_MODE_OWNED_ONLY:
            competition_headline = "自社サイトの根拠あり" if grouped_sources["self"] else "自社サイトの根拠が不足"
        elif competitor_mentions:
            if visibility_state == "自社優勢":
                competition_headline = f"{', '.join(competitor_mentions[:2])} より前"
            elif visibility_state == "自社あり":
                competition_headline = f"{', '.join(competitor_mentions[:2])} と並走"
            elif visibility_state == "外部サイト優勢":
                competition_headline = f"{', '.join(competitor_mentions[:2])} が先行"
            else:
                competition_headline = f"{', '.join(competitor_mentions[:2])} に対して未露出"
        elif grouped_sources["third_party"]:
            if visibility_state == "自社優勢":
                competition_headline = "外部サイトより前"
            elif visibility_state == "自社あり":
                competition_headline = "外部サイトと併存"
            elif visibility_state == "外部サイト優勢":
                competition_headline = "外部サイトが先行"
            else:
                competition_headline = "外部サイトに対して未露出"
        else:
            competition_headline = "外部情報は少なめ"

        with ui.row().classes("w-full gap-5 flex-wrap items-start"):
            with ui.card().classes("section-card result-highlight-card p-5 flex-1 min-w-[360px]"):
                ui.label("自社が出たか").classes("section-font section-title text-[24px] font-bold")
                ui.label("質問").classes("summary-eyebrow mt-4")
                ui.label(str(latest.get("keyword_raw") or "-")).classes(
                    "text-[16px] font-bold text-main mt-2 leading-7"
                )
                ui.label(visibility_state).classes(f"summary-mainline mt-4 {verdict_text_class}")
                ui.label(verdict_summary).classes(
                    "text-[16px] leading-7 text-support mt-3"
                )
                for notice in query_notice_lines:
                    ui.label(notice).classes("text-[13px] leading-6 text-helper mt-2")
                with ui.row().classes("w-full gap-2 mt-4 flex-wrap"):
                    ui.label(target_chip_text).classes(f"signal-chip {target_chip_class}")
                    ui.label(brand_chip_text).classes(f"signal-chip {brand_chip_class}")
                    if latest.get("target_domain_hit_rate") is not None:
                        ui.label(f"自社露出率 {float(latest.get('target_domain_hit_rate') or 0.0):.1f}%").classes("signal-chip signal-neutral")
            with ui.card().classes("section-card result-highlight-card p-5 flex-1 min-w-[320px]"):
                ui.label("外部名・外部サイト").classes("section-font section-title text-[24px] font-bold")
                ui.label(competition_headline).classes(
                    f"summary-mainline mt-5 {build_verdict_text_class(visibility_state)}"
                )
                ui.label(source_summary).classes("text-[16px] leading-7 text-support mt-3")
                with ui.row().classes("w-full gap-2 mt-4 flex-wrap"):
                    ui.label(f"自社 {len(grouped_sources['self'])}件").classes("signal-chip signal-positive")
                    ui.label(f"競合 {len(grouped_sources['competitor'])}件").classes("signal-chip signal-neutral")
                    ui.label(f"外部 {len(grouped_sources['third_party'])}件").classes("signal-chip signal-negative")
            with ui.card().classes("section-card result-highlight-card p-5 flex-1 min-w-[320px]"):
                ui.label("次に見直す").classes("section-font section-title text-[24px] font-bold")
                ui.label("優先ページ").classes("summary-eyebrow mt-4")
                ui.label(page_gap["page_type_label"]).classes("summary-mainline mt-2 text-brand")
                ui.label("次アクション").classes("summary-eyebrow mt-5")
                ui.label(page_gap["next_step"]).classes("text-[15px] leading-7 text-support mt-2")
                ui.label(page_gap["summary"]).classes("text-[14px] leading-6 text-helper mt-4")
        with ui.card().classes("section-card p-5 w-full mt-5"):
            ui.label("前回比サマリ").classes("section-font section-title text-[24px] font-bold")
            if not previous_delta_summary.get("available"):
                ui.label(str(previous_delta_summary.get("reason") or "前回比はまだありません。")).classes("text-[15px] leading-7 soft-label mt-3")
            else:
                def delta_label(value: float) -> str:
                    return f"{value:+.1f}pt"

                ui.label("同じ拡張条件の直近2 run を比較しています。").classes("text-[14px] leading-6 text-helper mt-2")
                with ui.row().classes("w-full gap-3 mt-4 flex-wrap"):
                    metric_specs = [
                        (
                            "自社露出率",
                            previous_delta_summary["previous"]["target_hit_rate"],
                            previous_delta_summary["current"]["target_hit_rate"],
                            previous_delta_summary["target_hit_rate_delta"],
                            "text-self",
                        ),
                        (
                            "平均 visibility スコア",
                            previous_delta_summary["previous"]["avg_visibility_score"],
                            previous_delta_summary["current"]["avg_visibility_score"],
                            previous_delta_summary["avg_visibility_score_delta"],
                            "text-brand",
                        ),
                        (
                            "外部サイト優勢率",
                            previous_delta_summary["previous"]["external_lead_rate"],
                            previous_delta_summary["current"]["external_lead_rate"],
                            previous_delta_summary["external_lead_rate_delta"],
                            "text-external",
                        ),
                    ]
                    for title, left_value, right_value, delta_value, tone in metric_specs:
                        with ui.column().classes("mini-stat-card flex-1 gap-1 min-w-[200px]"):
                            ui.label(title).classes("text-[12px] tracking-[0.18em] soft-label")
                            ui.label(f"{left_value:.1f} → {right_value:.1f}").classes("metric-font text-[18px] font-bold text-main")
                            ui.label(delta_label(delta_value)).classes(f"text-[13px] font-bold {tone}")


def refresh_dashboard(
    config: AppConfig,
    show_primary_results: bool,
    result_stage_container: ui.column,
    metric_refs: dict[str, tuple[ui.label, ui.label]],
    decision_refs: dict[str, dict[str, Any]],
    rows_table: ui.table,
    run_table: ui.table,
    overall_visibility_plot: Any,
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
) -> None:
    all_recent_rows = db.list_recent_results(limit=500)
    recent_rows = filter_rows_for_active_scope(all_recent_rows, config)
    query_rollup_rows = build_query_rollup_rows(recent_rows)
    metrics = build_overview_metrics(query_rollup_rows, config.pricing.usd_to_jpy)
    portfolio_story = build_portfolio_story(query_rollup_rows, config)
    intent_rows = build_intent_map_rows(query_rollup_rows, config)
    page_gap_rows = build_page_gap_rows(query_rollup_rows, config)
    previous_delta_summary = resolve_previous_delta_summary(config, recent_rows)
    budget_guardrail = build_budget_guardrail(all_recent_rows, config)

    metric_refs["overall"][0].text = portfolio_story["overall_label"]
    metric_refs["overall"][1].text = portfolio_story["overall_summary"]
    metric_refs["competition"][0].text = portfolio_story["competition_label"]
    metric_refs["competition"][1].text = portfolio_story["competition_summary"]
    metric_refs["action"][0].text = portfolio_story["action_headline"]
    metric_refs["action"][1].text = portfolio_story["action_summary"]

    summary_refs["kpis"]["target_hit_rate"][0].text = f"{metrics['target_hit_rate']:.1f}%"
    summary_refs["kpis"]["target_hit_rate"][1].text = "回答で自社URLが引用に入った割合"
    summary_refs["kpis"]["avg_score"][0].text = f"{metrics['avg_score']:.1f}/100"
    summary_refs["kpis"]["avg_score"][1].text = "保存済み結果の平均 visibility スコア"
    summary_refs["kpis"]["external_lead_rate"][0].text = f"{metrics['external_lead_rate']:.1f}%"
    summary_refs["kpis"]["external_lead_rate"][1].text = "外部サイトが先行した質問の割合"
    summary_refs["kpis"]["cache_hit_rate"][0].text = f"{metrics['cache_hit_rate']:.1f}%"
    summary_refs["kpis"]["cache_hit_rate"][1].text = "入力トークン再利用の効き具合"
    summary_refs["kpis"]["total_runs"][0].text = f"{int(metrics['total_runs'])}件"
    summary_refs["kpis"]["total_runs"][1].text = f"累積検索呼び出し {int(metrics['total_search_calls'])} 回"
    for value_label, detail_label in summary_refs["kpis"].values():
        value_label.update()
        detail_label.update()

    summary_refs["plots"]["visibility"].figure = build_overall_visibility_chart(recent_rows, config)
    summary_refs["plots"]["visibility"].update()
    summary_refs["plots"]["history_focus"].figure = build_visibility_focus_chart(recent_rows, config)
    summary_refs["plots"]["history_focus"].update()

    if intent_rows:
        weakest_intent = intent_rows[0]
        decision_refs["intent"]["headline"].text = f"{weakest_intent['intent_label']}意図が弱い"
        decision_refs["intent"]["summary"].text = (
            f"{weakest_intent['needs_fix_count']}/{weakest_intent['question_count']}件が外部サイト優勢または未露出です。"
            f" まずは {weakest_intent['top_page_type']} を補強してください。"
        )
    else:
        decision_refs["intent"]["headline"].text = "弱い意図は未判定"
        decision_refs["intent"]["summary"].text = "結果が保存されると、どの意図クラスタで負けているかをここで示します。"
    decision_refs["intent"]["headline"].update()
    decision_refs["intent"]["summary"].update()
    decision_refs["intent"]["table"].rows = intent_rows
    decision_refs["intent"]["table"].update()

    if page_gap_rows:
        top_gap = page_gap_rows[0]
        decision_refs["gap"]["headline"].text = f"先に作るのは {top_gap['page_type_label']}"
        decision_refs["gap"]["summary"].text = (
            f"{top_gap['priority_label']}。{top_gap['needs_fix_count']}/{top_gap['question_count']}件で不足しています。"
            f" {top_gap['next_step']}"
        )
    else:
        decision_refs["gap"]["headline"].text = "不足ページは未判定"
        decision_refs["gap"]["summary"].text = "結果が保存されると、制作着手すべきページ種別をここに出します。"
    decision_refs["gap"]["headline"].update()
    decision_refs["gap"]["summary"].update()
    decision_refs["gap"]["table"].rows = page_gap_rows
    decision_refs["gap"]["table"].update()

    decision_refs["budget"]["headline"].text = budget_guardrail["headline"]
    decision_refs["budget"]["headline"].classes(replace=f"summary-mainline mt-2 {build_guardrail_text_class(budget_guardrail['status'])}")
    decision_refs["budget"]["summary"].text = budget_guardrail["summary"]
    decision_refs["budget"]["today"].text = f"{int(budget_guardrail['today_result_count'] or 0)}件"
    decision_refs["budget"]["estimate"].text = f"{int(budget_guardrail['request_count'] or 0)}件"
    decision_refs["budget"]["remaining"].text = budget_guardrail["guardrail_mode_label"]
    decision_refs["budget"]["efficiency"].text = localize_cache_retention_label(
        resolve_prompt_cache_retention(config.model, config.prompt_cache_retention)
    )
    cache_retention_note = (
        "24時間キャッシュが使えない条件では、自動でメモリ内へ切り替えています。"
        if config.prompt_cache_retention == "24h" and budget_guardrail["effective_prompt_cache_retention"] != "24h"
        else "キャッシュと一括割引を優先しつつ、金額は非表示のまま内部の実行ガードだけ維持しています。"
    )
    decision_refs["budget"]["note"].text = cache_retention_note
    for key in ("headline", "summary", "today", "estimate", "remaining", "efficiency", "note"):
        decision_refs["budget"][key].update()

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

    rows_table.rows = table_rows
    rows_table.update()

    run_table.rows = [
        {
            **row,
            "started_at": format_timestamp(row["started_at"]),
            "finished_at": format_timestamp(row["finished_at"]),
            "run_mode": localize_run_mode(row.get("run_mode")),
            "question_set_name": str(row.get("question_set_name") or "ad-hoc"),
        }
        for row in db.list_run_history()
    ]
    run_table.update()

    query_options = {
        keyword: shorten_question_label(keyword, limit=28)
        for keyword in dedupe_preserve_order([str(row.get("keyword_raw") or "") for row in query_rollup_rows if row.get("keyword_raw")])
    }
    query_select.options = query_options
    if query_select.value not in query_options and query_options:
        query_select.value = next(iter(query_options))
    query_select.update()

    overall_visibility_plot.figure = build_overall_visibility_chart(recent_rows, config)
    overall_visibility_plot.update()
    query_drilldown_plot.figure = build_query_drilldown_chart(recent_rows, str(query_select.value or ""))
    query_drilldown_plot.update()
    intent_trend_plot.figure = build_intent_cluster_chart(recent_rows, config)
    intent_trend_plot.update()
    page_gap_trend_plot.figure = build_page_gap_trend_chart(recent_rows, config)
    page_gap_trend_plot.update()

    weakest_intent_label = intent_rows[0]["intent_label"] if intent_rows else "-"
    top_gap_label = page_gap_rows[0]["page_type_label"] if page_gap_rows else "-"
    dashboard_status.text = (
        f"{localize_analysis_mode(config.analysis_mode)} | 総評 {portfolio_story['overall_label']} | "
        f"弱い意図 {weakest_intent_label} | 優先ページ {top_gap_label} | "
        f"自社が見える質問 {portfolio_story['visible_topics']}/{portfolio_story['total_topics']}件 | "
        f"外部名が見える質問 {portfolio_story['competitor_topics']}/{portfolio_story['total_topics']}件 | "
        f"返答分析 {budget_guardrail['today_result_count']}件蓄積"
    )

    result_stage_container.set_visibility(show_primary_results and bool(query_rollup_rows))
    latest_result_container.set_visibility(show_primary_results and bool(query_rollup_rows))
    summary_refs["container"].set_visibility(show_primary_results and bool(query_rollup_rows))
    if show_primary_results and query_rollup_rows:
        refresh_latest_result_cards(query_rollup_rows, config, latest_result_container, previous_delta_summary)
    else:
        latest_result_container.clear()
    refresh_result_detail_views(query_rollup_rows, detail_select, detail_container, config)

    source_container.clear()
    with source_container:
        ui.label("回答で使われた引用URL").classes("section-font section-title text-[24px] font-bold")
        if not query_rollup_rows:
            ui.label("まだ保存された引用URLはありません").classes("text-[15px] soft-label mt-2")
            return
        latest = query_rollup_rows[0]
        latest_payload = parse_json_object(latest.get("output_json"))
        grouped_sources = build_source_groups(extract_cited_sources(latest, latest_payload)[:8], latest_payload, config)
        section_specs = [
            ("自社", grouped_sources["self"], "source-group-positive", "text-self"),
            ("競合", grouped_sources["competitor"], "source-group-neutral", "text-competitive"),
            ("外部サイト", grouped_sources["third_party"], "source-group-negative", "text-external"),
        ]
        with ui.row().classes("w-full gap-4 mt-4 flex-wrap items-start"):
            for title, items, card_class, count_class in section_specs:
                with ui.column().classes(f"source-group-card {card_class} flex-1 min-w-[240px] gap-3"):
                    ui.label(title).classes("text-[12px] tracking-[0.18em] soft-label")
                    ui.label(f"{len(items)}件").classes(f"metric-font text-[28px] font-bold {count_class}")
                    if items:
                        for source in items[:3]:
                            ui.link(source["title"] or source["url"], source["url"], new_tab=True).classes(
                                "evidence-link text-[14px]"
                            )
                    else:
                        ui.label("今回ここに入るURLはありません。").classes("text-[14px] soft-label")


def refresh_batch_job_views(
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
            **row,
            "submitted_at": format_timestamp(row.get("submitted_at") or row.get("created_at")),
            "run_mode": localize_run_mode(row.get("run_mode")),
            "question_set_name": str(row.get("question_set_name") or "ad-hoc"),
            "status_label": localize_batch_status(row.get("status")),
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
        batch_status_label.text = "まだまとめて確認はありません"
        batch_summary_label.text = "まとめて回すときだけ使います。通常は「分析を実行」を使います。"
        batch_status_label.update()
        batch_summary_label.update()
        return

    imported_total = int(selected.get("imported_result_count") or 0) + int(selected.get("imported_error_count") or 0)
    batch_status_label.text = (
        f"選択中: {localize_batch_status(selected.get('status'))} | "
        f"ChatGPT {int(selected.get('request_counts_completed') or 0)}/{int(selected.get('request_counts_total') or 0)} 成功"
    )
    if selected.get("last_error"):
        batch_summary_label.text = str(selected.get("last_error"))
    else:
        batch_summary_label.text = (
            f"まとめ確認ID: {selected.get('batch_job_id')} | "
            f"取込 {imported_total}/{int(selected.get('request_count') or 0)} 件"
        )
    batch_status_label.update()
    batch_summary_label.update()


def refresh_question_set_views(
    question_set_select: ui.select,
    question_set_table: ui.table,
    schedule_question_set_select: ui.select | None = None,
) -> None:
    question_sets = db.list_question_sets()
    options = {row["question_set_id"]: build_question_set_option_label(row) for row in question_sets}
    current_value = question_set_select.value if question_set_select.value in options else None
    if current_value is None and options:
        current_value = next(iter(options))
    question_set_select.options = options
    question_set_select.value = current_value
    question_set_select.update()
    if schedule_question_set_select is not None:
        schedule_question_set_select.options = options
        if schedule_question_set_select.value not in options:
            schedule_question_set_select.value = current_value
        schedule_question_set_select.update()

    question_set_table.rows = [
        {
            **row,
            "updated_at": format_timestamp(row.get("updated_at")),
            "last_run_at": format_timestamp(row.get("last_run_at")),
            "last_run_mode": localize_run_mode(row.get("last_run_mode")),
        }
        for row in question_sets
    ]
    question_set_table.update()


def refresh_schedule_views(
    schedule_table: ui.table,
    scheduler_status_label: ui.label,
    schedule_select: ui.select | None = None,
    compare_target_select: ui.select | None = None,
    compare_mode_select: ui.select | None = None,
) -> None:
    schedules = db.list_schedules(limit=50)
    schedule_table.rows = [
        {
            **row,
            "schedule_label": (
                f"{format_weekdays_label(parse_weekdays_csv(row.get('weekdays_csv')))} / {row.get('time_of_day')}"
            ),
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
            compare_options = {
                row["question_set_id"]: build_question_set_option_label(row)
                for row in question_sets
            }
        current_compare = compare_target_select.value if compare_target_select.value in compare_options else None
        if current_compare is None and compare_options:
            current_compare = next(iter(compare_options))
        compare_target_select.options = compare_options
        compare_target_select.value = current_compare
        compare_target_select.update()
    scheduler_status_label.text = build_scheduler_status_text()
    scheduler_status_label.update()


def render_schedule_diff(
    schedule_id: str,
    compare_mode: str,
    compare_target_id: str,
    diff_container: ui.column,
) -> None:
    diff_container.clear()
    with diff_container:
        if not schedule_id:
            ui.label("比較元の定期チェックを選ぶと差分を表示します。").classes("text-[14px] soft-label")
            return
        left_schedule = db.get_schedule(schedule_id)
        if not left_schedule:
            ui.label("比較元の定期チェックが見つかりません。").classes("text-[14px] soft-label")
            return
        left_snapshot = build_schedule_snapshot(left_schedule)

        right_snapshot: dict[str, Any] | None = None
        if compare_mode == "schedule":
            if not compare_target_id:
                ui.label("比較先の定期チェックを選択してください。").classes("text-[14px] soft-label")
                return
            if compare_target_id == schedule_id:
                ui.label("同じ定期チェック同士は比較できません。別の定期チェックを選択してください。").classes("text-[14px] soft-label")
                return
            right_schedule = db.get_schedule(compare_target_id)
            if not right_schedule:
                ui.label("比較先の定期チェックが見つかりません。").classes("text-[14px] soft-label")
                return
            right_snapshot = build_schedule_snapshot(right_schedule)
        else:
            if not compare_target_id:
                ui.label("比較先の確認内容を選択してください。").classes("text-[14px] soft-label")
                return
            question_set = db.get_question_set(compare_target_id)
            if not question_set:
                ui.label("比較先の確認内容が見つかりません。").classes("text-[14px] soft-label")
                return
            right_snapshot = build_question_set_snapshot(question_set)

        diff = build_plan_diff(left_snapshot, right_snapshot)
        ui.label("差分比較").classes("summary-eyebrow")
        ui.label(f"{left_snapshot['label']} ↔ {right_snapshot['label']}").classes("text-[16px] font-bold text-main mt-2")
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
    rows: list[dict[str, Any]],
    config: AppConfig,
    cluster_kind_select: ui.select,
    cluster_target_select: ui.select,
    saved_brief_select: ui.select,
    cluster_brief_table: ui.table,
) -> None:
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
            **row,
            "updated_at": format_timestamp(row.get("updated_at")),
            "cluster_kind": localize_cluster_kind(str(row.get("cluster_kind") or "")),
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
                ui.label(str(brief.get("cluster_kind_label") or localize_cluster_kind(str(brief.get("cluster_kind") or "")))).classes(
                    "signal-chip signal-neutral"
                )
                ui.label(str(brief.get("page_type") or "-")).classes("signal-chip signal-positive")
            ui.label(str(brief.get("brief_title") or brief.get("generated_title") or "-")).classes(
                "text-[17px] font-bold text-main mt-3"
            )
            ui.label(str(brief.get("brief_summary") or "-")).classes("text-[14px] leading-7 text-support mt-3")
            ui.label("対象意図のまとまり").classes("summary-eyebrow mt-5")
            ui.label(str(brief.get("intent_cluster_summary") or "-")).classes("text-[14px] leading-6 text-support mt-2")
            ui.label("代表質問").classes("summary-eyebrow mt-5")
            for query in brief.get("representative_queries") or []:
                ui.label(f"- {query}").classes("text-[14px] leading-6 text-support mt-1")
            if not (brief.get("representative_queries") or []):
                ui.label("代表質問はまだありません。").classes("text-[14px] soft-label mt-2")
            ui.label("代表引用ドメイン").classes("summary-eyebrow mt-5")
            ui.label(join_csv(brief.get("representative_citation_domains") or []) or "なし").classes(
                "text-[14px] leading-6 text-support mt-2"
            )
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
    scope_kind: str,
    scope_id: str,
    run_a_id: str,
    run_b_id: str,
    container: ui.column,
    config: AppConfig,
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
                ("競合言及", compare["left"]["competitor_mention_rate"], compare["right"]["competitor_mention_rate"], compare["competitor_mention_delta"], "text-competitive"),
                ("平均スコア", compare["left"]["avg_visibility_score"], compare["right"]["avg_visibility_score"], round(compare["right"]["avg_visibility_score"] - compare["left"]["avg_visibility_score"], 1), "text-main"),
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


def refresh_export_views(export_table: ui.table, export_status_label: ui.label, export_rows: list[dict[str, str]]) -> None:
    export_table.rows = export_rows
    export_table.update()
    export_status_label.text = (
        f"最新 export は {export_rows[0]['generated_at']} に更新しました。"
        if export_rows
        else "まだ export を生成していません。"
    )
    export_status_label.update()


def refresh_result_detail_views(
    rows: list[dict[str, Any]],
    detail_select: ui.select,
    detail_container: ui.column,
    config: AppConfig,
) -> None:
    options = {
        row["result_id"]: f"{format_timestamp(row.get('analyzed_at'))} | {row.get('keyword_raw')}"
        for row in rows[:80]
    }
    current_value = detail_select.value if detail_select.value in options else None
    if current_value is None and options:
        current_value = next(iter(options))
    detail_select.options = options
    detail_select.value = current_value
    detail_select.update()

    selected_row = next((row for row in rows if row.get("result_id") == current_value), None)
    detail_container.clear()
    with detail_container:
        if not selected_row:
            ui.label("結果詳細はまだありません").classes("text-[15px] soft-label")
            return
        payload = parse_json_object(selected_row.get("output_json"))
        answer_text = str(selected_row.get("answer_text") or payload.get("answer_text") or "").strip()
        citations = extract_cited_sources(selected_row, payload)
        analysis_context_lines = build_analysis_context_lines(payload)
        recommended_actions = payload.get("recommended_actions") or []
        answer_structure = build_answer_structure_fields(selected_row, config)
        verdict = build_visibility_state_label(
            int(selected_row.get("visibility_score") or 0),
            bool(selected_row.get("target_domain_hit")),
            bool(selected_row.get("brand_mention_hit")),
        )
        try:
            expanded_queries = json.loads(str(selected_row.get("expanded_queries_json") or "[]"))
        except Exception:
            expanded_queries = []
        with ui.card().classes("card-detail p-5 w-full"):
            ui.label("結果詳細").classes("section-font section-title text-[24px] font-bold")
            ui.label(f"{selected_row.get('keyword_raw')}").classes("text-[18px] font-bold text-main mt-2")
            with ui.row().classes("w-full gap-2 mt-3 flex-wrap"):
                ui.label(localize_run_mode(selected_row.get("run_mode"))).classes("signal-chip signal-neutral")
                ui.label(verdict).classes(f"signal-chip {build_verdict_chip_class(verdict)}")
                ui.label(str(selected_row.get("question_set_name") or "ad-hoc")).classes("signal-chip signal-neutral")
                ui.label(str(answer_structure.get("answer_type_label") or "返答分析未分類")).classes("signal-chip signal-neutral")
            ui.label(str(selected_row.get("answer_snapshot") or payload.get("answer_snapshot") or "-")).classes(
                "text-[15px] leading-7 text-support mt-4"
            )
            if selected_row.get("query_was_shortened"):
                ui.label("この質問は内部で短く整えて計測しました。").classes("text-[13px] leading-6 text-helper mt-2")
            if len(expanded_queries) > 1:
                ui.label("この質問は関連する派生質問も含めて確認しました。").classes("text-[13px] leading-6 text-helper mt-1")
            ui.label("返答分析").classes("summary-eyebrow mt-5")
            with ui.row().classes("w-full gap-3 mt-2 flex-wrap"):
                with ui.column().classes("mini-stat-card flex-1 gap-1"):
                    ui.label("返答タイプ").classes("text-[12px] tracking-[0.18em] soft-label")
                    ui.label(str(answer_structure.get("answer_type_label") or "-")).classes("metric-font text-[18px] font-bold text-main")
                with ui.column().classes("mini-stat-card flex-1 gap-1"):
                    ui.label("自社出現").classes("text-[12px] tracking-[0.18em] soft-label")
                    ui.label("あり" if answer_structure.get("owned_mention_hit") else "なし").classes(
                        f"metric-font text-[18px] font-bold {'text-self' if answer_structure.get('owned_mention_hit') else 'text-support'}"
                    )
                with ui.column().classes("mini-stat-card flex-1 gap-1"):
                    ui.label("競合出現").classes("text-[12px] tracking-[0.18em] soft-label")
                    ui.label("あり" if answer_structure.get("competitor_mention_hit") else "なし").classes(
                        f"metric-font text-[18px] font-bold {'text-competitive' if answer_structure.get('competitor_mention_hit') else 'text-support'}"
                    )
            ui.label(
                f"言及ブランド: {join_csv(answer_structure['mentioned_brands']) if answer_structure['mentioned_brands'] else '検出なし'}"
            ).classes("text-[14px] leading-6 text-support mt-3")
            ui.label(
                f"引用ドメイン: {join_csv(answer_structure['citation_domains']) if answer_structure['citation_domains'] else '検出なし'}"
            ).classes("text-[14px] leading-6 text-support mt-2")
            ui.label("実行条件").classes("summary-eyebrow mt-5")
            if analysis_context_lines:
                for line in analysis_context_lines:
                    ui.label(line).classes("text-[14px] leading-6 text-support mt-2")
            else:
                ui.label("保存された条件はありません。").classes("text-[14px] soft-label mt-2")
            ui.label("拡張条件").classes("summary-eyebrow mt-5")
            if expanded_queries:
                ui.label(
                    f"要約あり / なし: {'あり' if selected_row.get('query_was_shortened') else 'なし'}"
                ).classes("text-[14px] leading-6 text-support mt-2")
                if selected_row.get("user_query_short"):
                    ui.label(f"内部の短文化: {selected_row.get('user_query_short')}").classes("text-[14px] leading-6 text-support mt-2")
                if selected_row.get("shortening_note"):
                    ui.label(f"保持した要素: {selected_row.get('shortening_note')}").classes("text-[14px] leading-6 text-support mt-2")
                ui.label("内部で使った質問").classes("text-[14px] font-bold text-main mt-3")
                for index, item in enumerate(expanded_queries, start=1):
                    ui.label(f"{index}. {item}").classes("text-[14px] leading-6 text-support mt-1")
                ui.label(
                    "前回と同じ拡張条件で比較"
                    if selected_row.get("expansion_signature")
                    else "比較条件の署名はまだありません。"
                ).classes("text-[13px] leading-6 text-helper mt-3")
            else:
                ui.label("内部で使った質問はまだ保存されていません。").classes("text-[14px] soft-label mt-2")
            if recommended_actions:
                ui.label("改善メモ").classes("summary-eyebrow mt-5")
                for action in recommended_actions[:3]:
                    ui.label(localize_action_text(action)).classes("text-[14px] leading-6 text-support mt-2")
            ui.label("生返答").classes("summary-eyebrow mt-5")
            ui.label(answer_text or "保存された answer_text はありません。").classes("text-[15px] leading-7 text-main mt-2")
            ui.label("回答で使われた引用元").classes("summary-eyebrow mt-5")
            if citations:
                for citation in citations[:8]:
                    ui.link(citation.get("title") or citation.get("url") or "-", citation.get("url") or "#", new_tab=True).classes(
                        "evidence-link text-[14px] block mt-2"
                    )
            else:
                ui.label("保存された引用元はありません。").classes("text-[14px] soft-label mt-2")
            ui.label("ページ下書き").classes("summary-eyebrow mt-5")
            ui.label("手動ボタンで、この質問の制作着手メモを 1 件ずつ作ります。").classes(
                "text-[14px] leading-6 text-support mt-2"
            )
            brief_container = ui.column().classes("w-full mt-4 gap-3")

            def render_brief() -> None:
                brief = build_page_brief_draft(selected_row, config)
                brief_container.clear()
                with brief_container:
                    with ui.card().classes("card-detail p-4 w-full"):
                        ui.label("下書きメモ").classes("section-font section-title text-[20px] font-bold")
                        with ui.row().classes("w-full gap-2 mt-3 flex-wrap"):
                            ui.label(str(brief["page_type"])).classes("signal-chip signal-positive")
                            ui.label(str(brief["answer_type_label"])).classes("signal-chip signal-neutral")
                        ui.label("仮タイトル案").classes("summary-eyebrow mt-5")
                        ui.label(str(brief["title"])).classes("text-[16px] font-bold text-main mt-2")
                        ui.label("想定読者").classes("summary-eyebrow mt-5")
                        ui.label(str(brief["audience"])).classes("text-[14px] leading-6 text-support mt-2")
                        ui.label("検索意図の要約").classes("summary-eyebrow mt-5")
                        ui.label(str(brief["intent_summary"])).classes("text-[14px] leading-7 text-support mt-2")
                        ui.label("想定見出し構成").classes("summary-eyebrow mt-5")
                        for index, heading in enumerate(brief["headings"], start=1):
                            ui.label(f"{index}. {heading}").classes("text-[14px] leading-6 text-support mt-1")
                        ui.label("想定FAQ").classes("summary-eyebrow mt-5")
                        for item in brief["faqs"]:
                            ui.label(f"Q. {item['question']}").classes("text-[14px] font-bold text-main mt-2")
                            ui.label(f"A. {item['answer_hint']}").classes("text-[14px] leading-6 text-support mt-1")
                        ui.label("推奨CTA").classes("summary-eyebrow mt-5")
                        ui.label(str(brief["cta"])).classes("text-[14px] leading-6 text-support mt-2")
                        ui.label("参考にした情報").classes("summary-eyebrow mt-5")
                        ui.label(f"質問: {brief['reference_query']}").classes("text-[14px] leading-6 text-support mt-1")
                        if brief["reference_answer_summary"]:
                            ui.label(f"返答要約: {brief['reference_answer_summary']}").classes("text-[14px] leading-6 text-support mt-1")
                        ui.label(
                            f"引用ドメイン: {join_csv(brief['reference_citation_domains']) if brief['reference_citation_domains'] else 'なし'}"
                        ).classes("text-[14px] leading-6 text-support mt-1")
                        ui.label(
                            f"ブランド言及: {join_csv(brief['reference_brands']) if brief['reference_brands'] else 'なし'}"
                        ).classes("text-[14px] leading-6 text-support mt-1")

            ui.button("下書きを生成", on_click=render_brief).props("unelevated no-caps color=deep-orange-7 text-color=white").classes("accent-button text-[15px] font-bold mt-3")
            if selected_row.get("error_text"):
                ui.label("エラー").classes("summary-eyebrow mt-5")
                ui.label(str(selected_row.get("error_text") or "")).classes("text-[14px] leading-6 text-external mt-2")


def build_config_from_inputs(inputs: dict[str, Any], current: AppConfig) -> AppConfig:
    keyword_inputs = inputs.get("keyword_inputs") or []
    if keyword_inputs:
        keywords = [
            str(control.value or "").strip()
            for control in keyword_inputs[:3]
            if str(control.value or "").strip()
        ]
    else:
        keywords = split_multiline_keywords(inputs["keywords"].value)
    return AppConfig(
        analysis_mode=ANALYSIS_MODE_MARKET,
        provider=current.provider,
        model=current.model,
        reasoning_effort=current.reasoning_effort,
        prompt_cache_key=current.prompt_cache_key,
        prompt_cache_retention=current.prompt_cache_retention,
        max_output_tokens=current.max_output_tokens,
        repeat_count=20,
        keywords=keywords,
        target_domain=inputs["target_domain"].value.strip(),
        brand_terms=split_csv(inputs["brand_terms"].value),
        competitor_terms=split_csv(inputs["competitor_terms"].value),
        allowed_domains=current.allowed_domains,
        search_context_size=current.search_context_size,
        user_location_country=current.user_location_country,
        user_location_city=current.user_location_city,
        user_location_region=current.user_location_region,
        timezone=current.timezone,
        run_budget_guardrail_usd=current.run_budget_guardrail_usd,
        daily_budget_usd=current.daily_budget_usd,
        budget_guardrail_mode=current.budget_guardrail_mode,
        ui_port=current.ui_port,
        ui_host=current.ui_host,
        pricing=current.pricing,
    )


def get_missing_required_fields(cfg: AppConfig) -> list[str]:
    missing: list[str] = []
    if not [keyword for keyword in cfg.keywords if normalize_text(keyword)]:
        missing.append("質問")
    if not normalize_text(cfg.target_domain):
        missing.append("自社URL")
    if not [term for term in cfg.brand_terms if normalize_text(term)]:
        missing.append("ブランド名")
    return missing


def notify_missing_required_fields(cfg: AppConfig, *, context: str) -> bool:
    missing = get_missing_required_fields(cfg)
    if not missing:
        return False
    ui.notify(f"{context}前に {', '.join(missing)} を入力してください。", color="warning")
    return True


def resolve_previous_delta_summary(config: AppConfig, filtered_rows: list[dict[str, Any]]) -> dict[str, Any]:
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


def build_error_result(keyword: str, error_text: str, config: AppConfig | None = None) -> AnalysisResult:
    message = str(error_text).strip()
    analysis_context = {}
    if config is not None:
        analysis_context = {
            "analysis_mode": config.analysis_mode,
            "target_domain": config.target_domain,
            "brand_terms": config.brand_terms,
            "competitor_terms": config.competitor_terms,
            "allowed_domains": config.allowed_domains,
            "owned_only_domains": dedupe_preserve_order(
                [normalize_host(config.target_domain), *[normalize_host(item) for item in config.allowed_domains]]
            ),
            "model": config.model,
            "reasoning_effort": config.reasoning_effort,
            "search_context_size": config.search_context_size,
            "prompt_cache_retention_requested": config.prompt_cache_retention,
            "prompt_cache_retention_effective": resolve_prompt_cache_retention(
                config.model,
                config.prompt_cache_retention,
            ),
        }
    return AnalysisResult(
        keyword_raw=keyword,
        keyword_norm=keyword,
        output_text=message,
        output_json={
            "keyword_raw": keyword,
            "keyword_norm": keyword,
            "answer_snapshot": "実行エラー。設定またはAPI応答を確認してください。",
            "answer_text": message or "エラー内容を確認してから再実行してください。",
            "visibility_score": 0,
            "target_domain_hit": False,
            "brand_mention_hit": False,
            "competitor_mentions": [],
            "confidence": "low",
            "recommended_actions": [
                "APIキーと接続設定を確認する",
                "質問か優先ドメインを絞る",
                "検索応答を再実行して確認する",
            ],
            "citations": [],
            "citation_urls": [],
            "analysis_context": analysis_context,
        },
        usage={},
        web_search_calls=0,
        sources=[],
        estimated_cost_usd=0.0,
    )


def render_top_nav() -> None:
    with ui.header().classes("top-shell items-center px-5 py-3"):
        with ui.row().classes("w-full max-w-7xl mx-auto items-center justify-between gap-4 flex-wrap"):
            with ui.link("", "http://127.0.0.1:8090", new_tab=True).classes("top-logo-link"):
                with ui.element("span").classes("top-logo-badge"):
                    ui.image("/branding/favicon_v2.png").classes("top-logo-icon")
                ui.label("TECHIE").classes("brand-font top-logo-wordmark")
            with ui.row().classes("items-center gap-4 flex-wrap"):
                ui.link("コトメイク", "http://127.0.0.1:8080", new_tab=True).classes("nav-link text-[17px]")
                ui.link("コトミガキ", "http://127.0.0.1:8081", new_tab=True).classes("nav-link text-[17px]")
                ui.label("コトメガネ").classes("nav-link nav-link-active text-[17px]")


def render_workflow_rail() -> None:
    with ui.card().classes("step-rail p-3 w-full"):
        with ui.row().classes("w-full gap-3 flex-wrap"):
            for step, title, tone in [
                ("1", "入力する", "workflow-step-pill-active"),
                ("2", "結果を見る", "workflow-step-pill-muted"),
                ("3", "詳細", "workflow-step-pill-muted"),
            ]:
                with ui.column().classes("workflow-lane-card flex-1 gap-2"):
                    ui.label(f"手順 {step}").classes(f"workflow-step-pill {tone}")
                    ui.label(title).classes("section-font text-[22px] font-bold text-main")


def render_stage_header(step: str, title: str, description: str) -> None:
    with ui.row().classes("w-full gap-4 items-center flex-wrap px-1"):
        with ui.row().classes("w-full gap-4 items-center flex-wrap"):
            ui.label(f"手順 {step}").classes("workflow-step-pill workflow-step-pill-active")
            with ui.column().classes("gap-2 flex-1 min-w-[260px]"):
                ui.label(title).classes("section-font section-title text-[24px] font-bold")
                if description:
                    ui.label(description).classes("text-[13px] leading-5 text-support")


def render_page() -> None:
    add_global_style()
    state = {
        "config": normalize_provider_config(config_state),
        "busy": False,
        "batch_busy": False,
        "export_rows": [],
        "show_primary_results": bool(db.list_recent_results(limit=1)),
    }
    inputs: dict[str, Any] = {}
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
    provider_buttons: dict[str, ui.button] = {}
    keyword_inputs: list[Any] = []
    keyword_rows: list[Any] = []

    def refresh_provider_ui() -> None:
        nonlocal state
        next_config = refresh_provider_controls(
            state["config"],
            provider_buttons,
        )
        state["config"] = next_config
        if runtime_micro_label is not None and cost_policy_label is not None:
            refresh_runtime_panels(state["config"], runtime_micro_label, cost_policy_label)

    def set_provider(provider_key: str) -> None:
        provider = get_provider_option(provider_key)
        if provider.key not in VISIBLE_PROVIDER_KEYS or not provider.implemented:
            return
        next_model = (
            state["config"].model
            if state["config"].model in provider.models
            else provider.models[0]
            if provider.models
            else state["config"].model
        )
        state["config"] = state["config"].model_copy(update={"provider": provider_key, "model": next_model})
        refresh_provider_ui()

    render_top_nav()

    with ui.column().classes("w-full max-w-7xl mx-auto px-5 pb-12 gap-8"):
        with ui.card().classes("hero-card w-full px-5 py-3 mt-4"):
            with ui.row().classes("w-full items-start justify-between gap-4 flex-wrap"):
                with ui.column().classes("hero-copy-card gap-1 justify-center flex-1 min-w-[300px]"):
                    ui.label("コトメガネ").classes("brand-font hero-service-name")
                with ui.card().classes("provider-runtime-card p-3 w-[280px] max-w-full"):
                    ui.label("接続AI").classes("summary-eyebrow")
                    with ui.row().classes("provider-chip-rail w-full mt-3"):
                        for provider in get_visible_provider_catalog():
                            button = ui.button(
                                provider_display_label(provider),
                                on_click=lambda _=None, provider_key=provider.key: set_provider(provider_key),
                            ).props("unelevated no-caps").classes("provider-chip-button")
                            provider_buttons[provider.key] = button
                    refresh_provider_ui()

        metric_refs: dict[str, tuple[ui.label, ui.label]] = {}
        summary_refs: dict[str, Any] = {"kpis": {}, "plots": {}}
        decision_refs: dict[str, dict[str, Any]] = {"intent": {}, "gap": {}, "budget": {}}

        render_stage_header("1", "入力する", "")
        with ui.card().classes("section-card p-6 w-full"):
                ui.label("質問").classes("section-font section-title text-[30px] font-bold")
                initial_keywords = list(state["config"].keywords[:3]) or [""]
                visible_keyword_count = max(1, min(3, len([item for item in initial_keywords if str(item).strip()]) or 1))

                def refresh_keyword_input_visibility() -> None:
                    active_rows = 0
                    for index, row in enumerate(keyword_rows):
                        should_show = index < visible_keyword_count
                        row.set_visibility(should_show)
                        if should_show:
                            active_rows += 1
                    add_keyword_button.visible = active_rows < 3
                    remove_keyword_button.visible = active_rows > 1

                def add_keyword_input() -> None:
                    nonlocal visible_keyword_count
                    visible_keyword_count = min(3, visible_keyword_count + 1)
                    refresh_keyword_input_visibility()

                def remove_keyword_input() -> None:
                    nonlocal visible_keyword_count
                    if visible_keyword_count <= 1:
                        return
                    visible_keyword_count -= 1
                    keyword_inputs[visible_keyword_count].value = ""
                    keyword_inputs[visible_keyword_count].update()
                    refresh_keyword_input_visibility()

                for index in range(3):
                    default_value = initial_keywords[index] if index < len(initial_keywords) else ""
                    row = ui.row().classes("w-full gap-3 mt-3 items-start")
                    with row:
                        ui.label(f"{index + 1}.").classes("metric-font text-[18px] font-bold text-brand mt-3 w-[20px]")
                        keyword_input = ui.input(
                            f"質問 {index + 1}",
                            value=default_value,
                            placeholder="例: コトメガネとは\n例: AI検索で自社名を出すには",
                        ).props("outlined").classes("flex-1")
                    keyword_rows.append(row)
                    keyword_inputs.append(keyword_input)
                inputs["keyword_inputs"] = keyword_inputs
                inputs["keywords"] = keyword_inputs[0]

                with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
                    add_keyword_button = ui.button("＋追加", on_click=add_keyword_input).props("outline").classes(
                        "secondary-button text-[15px]"
                    )
                    remove_keyword_button = ui.button("1つ減らす", on_click=remove_keyword_input).props("outline").classes(
                        "secondary-button text-[15px]"
                    )
                refresh_keyword_input_visibility()

                with ui.row().classes("w-full gap-3 mt-4 flex-wrap"):
                    inputs["target_domain"] = ui.input(
                        "自社URL *",
                        value=state["config"].target_domain,
                        placeholder="example.com",
                    ).props("outlined").classes("w-[320px] flex-1")
                with ui.row().classes("w-full gap-3 mt-1 flex-wrap"):
                    inputs["brand_terms"] = ui.input(
                        "ブランド名 *",
                        value=join_csv(state["config"].brand_terms),
                        placeholder="TECHIE, コトメガネ",
                    ).props("outlined").classes("w-[320px] flex-1")
                ui.label("質問 / 自社URL / ブランド名は必須です。競合語は必要なときだけ入れてください。").classes(
                    "text-[13px] leading-6 text-helper mt-2"
                )

                with ui.expansion("競合を比べる").classes("w-full mt-5 panel-card"):
                    with ui.column().classes("p-4 gap-4 w-full"):
                        inputs["competitor_terms"] = ui.input(
                            "競合語",
                            value=join_csv(state["config"].competitor_terms),
                            placeholder="競合A, 競合B",
                        ).props("outlined").classes("w-full")

                progress = ui.linear_progress(value=0).props("color=deep-orange-7 track-color=amber-1 rounded").classes("w-full mt-5")
                progress.visible = False
                with ui.column().classes("status-row w-full gap-1 px-4 py-4 mt-4"):
                    step_label = ui.label("まだ分析していません").classes("text-[18px] font-bold text-main")
                    summary_label = ui.label("実行後に結果が出ます。").classes("text-[14px] text-helper mt-1")

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
                    inputs["competitor_terms"].value = join_csv(cfg.competitor_terms)
                    for control in inputs.values():
                        if isinstance(control, list):
                            continue
                        control.update()
                    refresh_provider_ui()

                def refresh_cluster_and_outcome_sections() -> None:
                    scoped_rows = filter_rows_for_active_scope(db.list_recent_results(limit=2000), state["config"])
                    if (
                        cluster_kind_select is not None
                        and cluster_target_select is not None
                        and saved_cluster_brief_select is not None
                        and cluster_brief_table is not None
                    ):
                        refresh_cluster_brief_views(
                            scoped_rows,
                            state["config"],
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
                        refresh_outcome_compare_views(
                            outcome_scope_kind_select,
                            outcome_scope_target_select,
                            outcome_run_a_select,
                            outcome_run_b_select,
                        )

                def render_active_cluster_and_outcome_panels() -> None:
                    if cluster_brief_container is not None:
                        if saved_cluster_brief_select is not None and saved_cluster_brief_select.value:
                            saved_row = db.get_cluster_brief(str(saved_cluster_brief_select.value))
                            if saved_row:
                                try:
                                    saved_payload = json.loads(str(saved_row.get("brief_json") or "{}"))
                                except Exception:
                                    saved_payload = {}
                                if isinstance(saved_payload, dict):
                                    saved_payload.setdefault("generated_title", str(saved_row.get("generated_title") or ""))
                                    saved_payload.setdefault("cluster_kind", str(saved_row.get("cluster_kind") or ""))
                                    saved_payload.setdefault(
                                        "cluster_kind_label",
                                        localize_cluster_kind(str(saved_row.get("cluster_kind") or "")),
                                    )
                                render_cluster_brief_payload(
                                    saved_payload if isinstance(saved_payload, dict) else None,
                                    cluster_brief_container,
                                )
                            else:
                                render_cluster_brief_payload(None, cluster_brief_container)
                        else:
                            render_cluster_brief_payload(None, cluster_brief_container)
                    if outcome_compare_container is not None:
                        render_outcome_compare(
                            str(outcome_scope_kind_select.value or "schedule") if outcome_scope_kind_select is not None else "schedule",
                            str(outcome_scope_target_select.value or "") if outcome_scope_target_select is not None else "",
                            str(outcome_run_a_select.value or "") if outcome_run_a_select is not None else "",
                            str(outcome_run_b_select.value or "") if outcome_run_b_select is not None else "",
                            outcome_compare_container,
                            state["config"],
                        )

                async def on_save() -> None:
                    state["config"] = build_config_from_inputs(inputs, state["config"])
                    save_config(state["config"])
                    refresh_runtime_panels(
                        state["config"],
                        runtime_micro_label,
                        cost_policy_label,
                    )
                    ui.notify("設定を保存しました", color="positive")
                    refresh_dashboard(
                        state["config"],
                        state["show_primary_results"],
                        result_stage_container,
                        metric_refs,
                        decision_refs,
                        rows_table,
                        run_table,
                        overall_visibility_plot,
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
                    )
                    refresh_cluster_and_outcome_sections()
                    render_active_cluster_and_outcome_panels()

                async def on_question_set_save() -> None:
                    cfg = build_config_from_inputs(inputs, state["config"])
                    if notify_missing_required_fields(cfg, context="確認内容保存"):
                        return
                    name = question_set_name_input.value.strip() or f"確認内容 {time.strftime('%Y-%m-%d %H:%M')}"
                    selected_id = question_set_select.value if question_set_select.value else None
                    saved_id = db.upsert_question_set(
                        question_set_id=selected_id,
                        name=name,
                        config_json=json.dumps(cfg.model_dump(), ensure_ascii=False),
                    )
                    question_set_name_input.value = name
                    refresh_question_set_views(question_set_select, question_set_table, schedule_question_set_select)
                    question_set_select.value = saved_id
                    schedule_question_set_select.value = saved_id
                    question_set_select.update()
                    schedule_question_set_select.update()
                    refresh_cluster_and_outcome_sections()
                    render_active_cluster_and_outcome_panels()
                    ui.notify("確認内容を保存しました", color="positive")

                async def on_question_set_load() -> None:
                    question_set_id = question_set_select.value
                    if not question_set_id:
                        ui.notify("読み込む確認内容を選択してください。", color="warning")
                        return
                    question_set = db.get_question_set(question_set_id)
                    if not question_set:
                        ui.notify("確認内容が見つかりません。", color="warning")
                        return
                    cfg = AppConfig.model_validate_json(question_set["config_json"]).model_copy(
                        update={"analysis_mode": ANALYSIS_MODE_MARKET, "repeat_count": 20}
                    )
                    state["config"] = cfg
                    question_set_name_input.value = str(question_set.get("name") or "")
                    schedule_question_set_select.value = question_set_id
                    apply_config_to_inputs(cfg)
                    refresh_runtime_panels(
                        state["config"],
                        runtime_micro_label,
                        cost_policy_label,
                    )
                    refresh_dashboard(
                        state["config"],
                        state["show_primary_results"],
                        result_stage_container,
                        metric_refs,
                        decision_refs,
                        rows_table,
                        run_table,
                        overall_visibility_plot,
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
                    )
                    refresh_cluster_and_outcome_sections()
                    render_active_cluster_and_outcome_panels()
                    ui.notify("確認内容を読み込みました", color="positive")

                async def on_schedule_save() -> None:
                    question_set_id = schedule_question_set_select.value or question_set_select.value
                    if not question_set_id:
                        ui.notify("先に保存済みの確認内容を選択してください。", color="warning")
                        return
                    requested_weekly_runs = max(1, int(schedule_weekly_runs_input.value or 1))
                    weekdays = normalize_schedule_weekdays(
                        schedule_weekdays_select.value or [],
                        requested_weekly_runs,
                    )
                    if not weekdays:
                        ui.notify("曜日を1つ以上選択してください。", color="warning")
                        return
                    effective_weekly_runs = min(requested_weekly_runs, len(set(schedule_weekdays_select.value or [])) or len(weekdays))
                    question_set = db.get_question_set(question_set_id)
                    if not question_set:
                        ui.notify("選択した確認内容が見つかりません。", color="warning")
                        return
                    question_set_cfg = AppConfig.model_validate_json(question_set["config_json"]).model_copy(
                        update={"analysis_mode": ANALYSIS_MODE_MARKET, "repeat_count": 20}
                    )
                    if notify_missing_required_fields(question_set_cfg, context="定期チェック保存"):
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
                    refresh_schedule_views(
                        schedule_table,
                        scheduler_status_label,
                        schedule_manage_select,
                        compare_target_select,
                        compare_mode_select,
                    )
                    if schedule_manage_select is not None:
                        schedule_manage_select.value = saved_id
                        schedule_manage_select.update()
                    refresh_cluster_and_outcome_sections()
                    render_active_cluster_and_outcome_panels()
                    ui.notify("定期チェックを保存しました", color="positive")

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
                    schedule_weekdays_select.value = weekdays
                    schedule_weekdays_select.update()
                    schedule_weekly_runs_input.value = int(schedule.get("weekly_run_count") or max(1, len(weekdays) or 1))
                    schedule_weekly_runs_input.update()
                    schedule_enabled_switch.value = bool(schedule.get("enabled"))
                    schedule_enabled_switch.update()

                async def on_schedule_load() -> None:
                    if schedule_manage_select is None or not schedule_manage_select.value:
                        ui.notify("読み込む定期チェックを選択してください。", color="warning")
                        return
                    schedule = db.get_schedule(str(schedule_manage_select.value))
                    if not schedule:
                        ui.notify("選択した定期チェックが見つかりません。", color="warning")
                        return
                    load_schedule_into_form(schedule)
                    ui.notify("定期チェックをフォームへ読み込みました。", color="positive")

                async def on_schedule_duplicate() -> None:
                    if schedule_manage_select is None or not schedule_manage_select.value:
                        ui.notify("複製する定期チェックを選択してください。", color="warning")
                        return
                    schedule = db.get_schedule(str(schedule_manage_select.value))
                    if not schedule:
                        ui.notify("選択した定期チェックが見つかりません。", color="warning")
                        return
                    duplicate_name = f"{str(schedule.get('name') or '定期チェック')} 複製"
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
                    refresh_schedule_views(
                        schedule_table,
                        scheduler_status_label,
                        schedule_manage_select,
                        compare_target_select,
                        compare_mode_select,
                    )
                    if schedule_manage_select is not None:
                        schedule_manage_select.value = duplicate_id
                        schedule_manage_select.update()
                    duplicate_schedule = db.get_schedule(duplicate_id)
                    if duplicate_schedule:
                        load_schedule_into_form(duplicate_schedule)
                    refresh_cluster_and_outcome_sections()
                    render_active_cluster_and_outcome_panels()
                    ui.notify("定期チェックを複製し、停止状態で保存しました。", color="positive")

                async def confirm_schedule_delete() -> None:
                    if schedule_manage_select is None or not schedule_manage_select.value:
                        return
                    schedule = db.get_schedule(str(schedule_manage_select.value))
                    if not schedule:
                        ui.notify("削除対象の定期チェックが見つかりません。", color="warning")
                        if schedule_delete_dialog is not None:
                            schedule_delete_dialog.close()
                        return
                    db.delete_schedule(str(schedule_manage_select.value))
                    if schedule_delete_dialog is not None:
                        schedule_delete_dialog.close()
                    refresh_schedule_views(
                        schedule_table,
                        scheduler_status_label,
                        schedule_manage_select,
                        compare_target_select,
                        compare_mode_select,
                    )
                    if schedule_diff_container is not None:
                        render_schedule_diff("", str(compare_mode_select.value or "schedule"), "", schedule_diff_container)
                    refresh_cluster_and_outcome_sections()
                    render_active_cluster_and_outcome_panels()
                    ui.notify(f"{schedule.get('name')} を削除しました。", color="positive")

                async def on_schedule_delete() -> None:
                    if schedule_manage_select is None or not schedule_manage_select.value:
                        ui.notify("削除する定期チェックを選択してください。", color="warning")
                        return
                    if schedule_delete_dialog is not None:
                        schedule_delete_dialog.open()

                async def on_schedule_diff_refresh() -> None:
                    if schedule_diff_container is None or schedule_manage_select is None or compare_mode_select is None or compare_target_select is None:
                        return
                    render_schedule_diff(
                        str(schedule_manage_select.value or ""),
                        str(compare_mode_select.value or "schedule"),
                        str(compare_target_select.value or ""),
                        schedule_diff_container,
                    )

                async def on_cluster_brief_generate() -> None:
                    if (
                        cluster_kind_select is None
                        or cluster_target_select is None
                        or cluster_brief_container is None
                        or saved_cluster_brief_select is None
                        or cluster_brief_table is None
                    ):
                        return
                    selected_token = str(cluster_target_select.value or "")
                    cluster_kind, _, cluster_key = selected_token.partition("::")
                    if not cluster_kind or not cluster_key:
                        ui.notify("下書きを作るクラスタを選択してください。", color="warning")
                        return
                    scoped_rows = filter_rows_for_active_scope(db.list_recent_results(limit=2000), state["config"])
                    candidates = build_cluster_brief_candidates(scoped_rows, state["config"])
                    candidate = next(
                        (
                            item
                            for item in candidates
                            if item["cluster_kind"] == cluster_kind and str(item["cluster_key"]) == cluster_key
                        ),
                        None,
                    )
                    if not candidate:
                        ui.notify("選択した cluster が見つかりません。", color="warning")
                        return
                    row_by_id = {str(row.get("result_id") or ""): row for row in scoped_rows}
                    cluster_rows = [
                        row_by_id[result_id]
                        for result_id in candidate.get("source_result_ids") or []
                        if result_id in row_by_id
                    ]
                    brief = build_cluster_brief_draft(
                        cluster_rows,
                        cluster_kind,
                        str(candidate.get("cluster_key") or ""),
                        str(candidate.get("cluster_label") or ""),
                        state["config"],
                    )
                    saved_id = db.save_cluster_brief(
                        cluster_kind=str(brief.get("cluster_kind") or cluster_kind),
                        cluster_key=str(brief.get("cluster_key") or cluster_key),
                        cluster_label=str(brief.get("cluster_label") or candidate.get("cluster_label") or ""),
                        source_run_ids_json=json.dumps(brief.get("source_run_ids") or [], ensure_ascii=False),
                        source_result_ids_json=json.dumps(brief.get("source_result_ids") or [], ensure_ascii=False),
                        query_count=int(brief.get("source_query_count") or candidate.get("query_count") or 0),
                        generated_title=str(brief.get("brief_title") or ""),
                        brief_json=json.dumps(brief, ensure_ascii=False),
                    )
                    refresh_cluster_brief_views(
                        scoped_rows,
                        state["config"],
                        cluster_kind_select,
                        cluster_target_select,
                        saved_cluster_brief_select,
                        cluster_brief_table,
                    )
                    saved_cluster_brief_select.value = saved_id
                    saved_cluster_brief_select.update()
                    render_cluster_brief_payload(brief, cluster_brief_container)
                    ui.notify("クラスタ下書きを生成して保存しました。", color="positive")

                async def on_saved_cluster_brief_load() -> None:
                    if saved_cluster_brief_select is None or cluster_brief_container is None:
                        return
                    brief_id = str(saved_cluster_brief_select.value or "")
                    if not brief_id:
                        ui.notify("表示する保存済み下書きを選択してください。", color="warning")
                        return
                    row = db.get_cluster_brief(brief_id)
                    if not row:
                        ui.notify("保存済み下書きが見つかりません。", color="warning")
                        return
                    try:
                        brief_payload = json.loads(str(row.get("brief_json") or "{}"))
                    except Exception:
                        brief_payload = {}
                    if isinstance(brief_payload, dict):
                        brief_payload.setdefault("generated_title", str(row.get("generated_title") or ""))
                        brief_payload.setdefault("cluster_kind", str(row.get("cluster_kind") or ""))
                        brief_payload.setdefault("cluster_kind_label", localize_cluster_kind(str(row.get("cluster_kind") or "")))
                    render_cluster_brief_payload(brief_payload if isinstance(brief_payload, dict) else None, cluster_brief_container)

                async def on_outcome_compare_show() -> None:
                    if (
                        outcome_scope_kind_select is None
                        or outcome_scope_target_select is None
                        or outcome_run_a_select is None
                        or outcome_run_b_select is None
                        or outcome_compare_container is None
                    ):
                        return
                    render_outcome_compare(
                        str(outcome_scope_kind_select.value or "schedule"),
                        str(outcome_scope_target_select.value or ""),
                        str(outcome_run_a_select.value or ""),
                        str(outcome_run_b_select.value or ""),
                        outcome_compare_container,
                        state["config"],
                    )

                async def on_export() -> None:
                    cfg = build_config_from_inputs(inputs, state["config"])
                    rows = filter_rows_for_active_scope(db.list_recent_results(limit=2000), cfg)
                    state["export_rows"] = write_export_files(rows, cfg)
                    refresh_export_views(export_table, export_status_label, state["export_rows"])
                    ui.notify("CSV / JSON export を更新しました", color="positive")

                async def on_run() -> None:
                    if state["busy"] or state["batch_busy"]:
                        return
                    cfg = build_config_from_inputs(inputs, state["config"])
                    if notify_missing_required_fields(cfg, context="分析実行"):
                        return
                    provider = get_provider_option(cfg.provider)
                    api_key_status = get_api_key_status(cfg.provider)
                    if not provider.implemented:
                        ui.notify(f"{provider.label} は未実装です。現時点では ChatGPT を利用してください。", color="warning")
                        return
                    if not api_key_status.present:
                        ui.notify(f"{api_key_status.env_var} が未設定です。.env または環境変数に設定してください。", color="negative")
                        return
                    budget_guardrail = build_budget_guardrail(db.list_recent_results(limit=500), cfg)
                    if budget_guardrail["should_block"]:
                        ui.notify(
                            "日次上限を超える見込みです。質問数、回数、または上限設定を見直してください。",
                            color="negative",
                        )
                        return
                    if budget_guardrail["status"] == "warning" and budget_guardrail["daily_budget_usd"] > 0:
                        ui.notify(
                            "今回の設定は日次上限に近いか超える見込みです。必要なら回数を絞ってください。",
                            color="warning",
                        )
                    if (
                        cfg.run_budget_guardrail_usd > 0
                        and budget_guardrail["estimated_run_cost_usd"] > cfg.run_budget_guardrail_usd
                    ):
                        ui.notify(
                            "今回の設定は 1 回の実行あたりの内部上限を超える見込みです。質問数か回数を絞ってください。",
                            color="warning",
                        )

                    state["config"] = cfg
                    save_config(cfg)
                    refresh_runtime_panels(
                        state["config"],
                        runtime_micro_label,
                        cost_policy_label,
                    )
                    state["busy"] = True
                    progress.visible = True
                    progress.value = 0
                    step_label.text = "分析を開始します"
                    summary_label.text = "同じ質問を続けて確認します。"
                    set_action_button_states(False)

                    completed = 0
                    failures = 0
                    run_spend_usd = 0.0
                    stopped_by_budget = False
                    current_question_set = db.get_question_set(question_set_select.value) if question_set_select.value else None
                    run_id = db.create_run_session(
                        cfg.repeat_count,
                        cfg.model,
                        cfg.prompt_cache_key,
                        run_mode="manual",
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
                            run_mode="manual",
                        )
                        execution_plan: ExecutionPlan = build_execution_plan(query_plans, cfg)
                        total_steps = max(1, execution_plan.total_request_count)
                        summary_label.text = (
                            f"元質問 {len(query_plans)} 件を、内部では {execution_plan.total_unique_queries} 件の関連質問に広げて確認します。"
                        )
                        provider_client = build_provider_client(cfg.provider)
                        for request in execution_plan.requests:
                            keyword = request.executed_query
                            if (
                                cfg.daily_budget_usd > 0
                                and cfg.budget_guardrail_mode == "stop"
                                and budget_guardrail["today_spend_usd"] + run_spend_usd + budget_guardrail["avg_request_cost_usd"]
                                > cfg.daily_budget_usd
                            ):
                                stopped_by_budget = True
                                summary_label.text = (
                                    "日次上限に達する見込みのため、残りの実行を停止しました。"
                                    " 回数か質問数を絞って再開してください。"
                                )
                                break
                            step_label.text = "同じ質問を続けて確認中"
                            summary_label.text = (
                                f"いま処理している元質問: {request.user_query_raw} / "
                                f"内部質問 {request.executed_query_index}: {keyword}"
                            )
                            await asyncio.sleep(0)
                            try:
                                result = await asyncio.to_thread(provider_client.analyze_keyword, keyword, cfg)
                                result.output_json["analysis_context"] = {
                                    **(result.output_json.get("analysis_context") or {}),
                                    "question": request.executed_query,
                                    "user_query_raw": request.user_query_raw,
                                    "executed_query": request.executed_query,
                                }
                                result.estimated_cost_usd = estimate_cost_usd(result.usage, result.web_search_calls, cfg)
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
                                cached_tokens = (result.usage.get("input_tokens_details") or {}).get("cached_tokens", 0)
                                summary_label.text = f"キャッシュ入力 {cached_tokens} トークンを再利用しながら処理しています。"
                            except Exception as exc:
                                failures += 1
                                error_result = build_error_result(keyword, str(exc), cfg)
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
                                    error_text=str(exc),
                                    query_plan_id=request.query_plan_id,
                                    display_query_raw=request.user_query_raw,
                                    executed_query=request.executed_query,
                                    executed_query_index=int(request.executed_query_index),
                                )
                                summary_label.text = f"一部失敗 {failures}件 | 最新エラー: {exc}"
                            completed += 1
                            progress.value = completed / total_steps
                            await asyncio.sleep(0)
                    finally:
                        db.finish_run_session(run_id)
                        if current_question_set:
                            db.touch_question_set_run(
                                str(current_question_set.get("question_set_id") or ""),
                                run_mode="manual",
                            )
                        state["busy"] = False
                        set_action_button_states(True)

                    step_label.text = "予算停止" if stopped_by_budget else "分析完了"
                    summary_label.text = (
                        f"実行ID: {run_id} | 失敗 {failures}件。"
                        + (" 日次上限に達する前で停止しました。" if stopped_by_budget else " 直近結果と結果一覧を更新しました。")
                    )
                    state["show_primary_results"] = True
                    refresh_dashboard(
                        state["config"],
                        state["show_primary_results"],
                        result_stage_container,
                        metric_refs,
                        decision_refs,
                        rows_table,
                        run_table,
                        overall_visibility_plot,
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
                    )
                    refresh_cluster_and_outcome_sections()
                    render_active_cluster_and_outcome_panels()
                    if failures:
                        ui.notify(f"分析完了。ただし {failures} 件は失敗しました", color="warning")
                    else:
                        ui.notify("分析が完了しました", color="positive")

                async def on_batch_submit() -> None:
                    if state["busy"] or state["batch_busy"]:
                        return
                    cfg = build_config_from_inputs(inputs, state["config"])
                    if notify_missing_required_fields(cfg, context="まとめて確認"):
                        return
                    provider = get_provider_option(cfg.provider)
                    api_key_status = get_api_key_status(cfg.provider)
                    if not provider_supports_batch(provider.key):
                        ui.notify("まとめて確認は現在この接続先では未対応です。", color="warning")
                        return
                    if not api_key_status.present:
                        ui.notify(f"{api_key_status.env_var} が未設定です。.env または環境変数に設定してください。", color="negative")
                        return
                    budget_guardrail = build_budget_guardrail(db.list_recent_results(limit=500), cfg)
                    if budget_guardrail["should_block"]:
                        ui.notify(
                            "日次上限を超える見込みのため、まとめて確認を止めました。質問数、回数、または上限設定を見直してください。",
                            color="negative",
                        )
                        return
                    if budget_guardrail["status"] == "warning" and budget_guardrail["daily_budget_usd"] > 0:
                        ui.notify(
                            "今回のまとめて確認は日次上限に近いか超える見込みです。必要なら回数を絞ってください。",
                            color="warning",
                        )
                    if (
                        cfg.run_budget_guardrail_usd > 0
                        and budget_guardrail["estimated_run_cost_usd"] > cfg.run_budget_guardrail_usd
                    ):
                        ui.notify(
                            "今回のまとめて確認は 1 回の実行あたりの内部上限を超える見込みです。質問数か回数を絞ってください。",
                            color="warning",
                        )

                    state["config"] = cfg
                    save_config(cfg)
                    refresh_runtime_panels(
                        state["config"],
                        runtime_micro_label,
                        cost_policy_label,
                    )
                    state["batch_busy"] = True
                    batch_status_label.text = "まとめて確認を開始しています"
                    batch_summary_label.text = "質問ごとにまとめた順で処理を作成しています。"
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
                        refresh_batch_job_views(
                            batch_job_select,
                            batch_job_table,
                            batch_status_label,
                            batch_summary_label,
                        )
                        batch_job_select.value = batch_handle.batch_job_id
                        batch_job_select.update()
                        if current_question_set:
                            db.touch_question_set_run(
                                str(current_question_set.get("question_set_id") or ""),
                                run_mode="batch",
                            )
                        ui.notify("まとめて確認を開始しました。進み具合を更新するか、結果を反映してください。", color="positive")
                    except Exception as exc:
                        db.finish_run_session(run_id)
                        batch_status_label.text = "まとめて確認の開始に失敗しました"
                        batch_summary_label.text = str(exc)
                        batch_status_label.update()
                        batch_summary_label.update()
                        ui.notify(f"まとめて確認の開始に失敗しました: {exc}", color="negative")
                    finally:
                        state["batch_busy"] = False
                        set_action_button_states(True)

                async def on_batch_refresh() -> None:
                    if state["busy"] or state["batch_busy"]:
                        return
                    batch_job_id = batch_job_select.value
                    if not batch_job_id:
                        ui.notify("進み具合を見る対象を選択してください。", color="warning")
                        return
                    batch_job = db.get_batch_job(batch_job_id)
                    if not batch_job:
                        ui.notify("選択したまとめ確認がローカルDBにありません。", color="warning")
                        return

                    state["batch_busy"] = True
                    batch_status_label.text = "ChatGPT の進み具合を更新しています"
                    batch_summary_label.text = f"まとめ確認ID: {batch_job_id}"
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
                        refresh_batch_job_views(
                            batch_job_select,
                            batch_job_table,
                            batch_status_label,
                            batch_summary_label,
                        )
                        ui.notify("まとめて確認の進み具合を更新しました。", color="positive")
                    except Exception as exc:
                        batch_status_label.text = "進み具合の更新に失敗しました"
                        batch_summary_label.text = str(exc)
                        batch_status_label.update()
                        batch_summary_label.update()
                        ui.notify(f"進み具合の更新に失敗しました: {exc}", color="negative")
                    finally:
                        state["batch_busy"] = False
                        set_action_button_states(True)

                async def on_batch_import() -> None:
                    if state["busy"] or state["batch_busy"]:
                        return
                    batch_job_id = batch_job_select.value
                    if not batch_job_id:
                        ui.notify("結果を反映する対象を選択してください。", color="warning")
                        return
                    batch_job = db.get_batch_job(batch_job_id)
                    if not batch_job:
                        ui.notify("選択したまとめ確認がローカルDBにありません。", color="warning")
                        return

                    state["batch_busy"] = True
                    batch_status_label.text = "結果を反映しています"
                    batch_summary_label.text = "ChatGPT の結果ファイルを確認しています。"
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
                        if not batch_handle.output_file_id and not batch_handle.error_file_id:
                            refresh_batch_job_views(
                                batch_job_select,
                                batch_job_table,
                                batch_status_label,
                                batch_summary_label,
                            )
                            ui.notify("まだ取り込める結果ファイルがありません。状態確認後に再度お試しください。", color="warning")
                            return

                        cfg_snapshot = AppConfig.model_validate_json(batch_job["config_json"])
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

                            error_result = build_error_result(
                                str(item_row.get("executed_query") or item_row["keyword_raw"]),
                                record.error_text,
                                cfg_snapshot,
                            )
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
                                error_text=record.error_text,
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
                                error_text=record.error_text,
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

                        refresh_batch_job_views(
                            batch_job_select,
                            batch_job_table,
                            batch_status_label,
                            batch_summary_label,
                        )
                        state["show_primary_results"] = True
                        refresh_dashboard(
                            state["config"],
                            state["show_primary_results"],
                            result_stage_container,
                            metric_refs,
                            decision_refs,
                            rows_table,
                            run_table,
                            overall_visibility_plot,
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
                        )
                        refresh_cluster_and_outcome_sections()
                        render_active_cluster_and_outcome_panels()
                        if new_successes or new_errors:
                            ui.notify(
                                f"まとめて確認の結果を反映しました。成功 {new_successes} 件 / エラー {new_errors} 件。",
                                color="positive" if new_errors == 0 else "warning",
                            )
                        else:
                            ui.notify("新しく反映できるまとめ確認の結果はありませんでした。", color="warning")
                    except Exception as exc:
                        batch_status_label.text = "結果の反映に失敗しました"
                        batch_summary_label.text = str(exc)
                        batch_status_label.update()
                        batch_summary_label.update()
                        ui.notify(f"結果の反映に失敗しました: {exc}", color="negative")
                    finally:
                        state["batch_busy"] = False
                        set_action_button_states(True)

                batch_submit_button = None
                batch_status_button = None
                batch_import_button = None
                save_button = None

                with ui.row().classes("gap-3 mt-5"):
                    run_button = ui.button("分析を実行", on_click=on_run).props("unelevated no-caps color=deep-orange-7 text-color=white").classes("accent-button text-[18px] font-bold")

                def set_action_button_states(enabled: bool) -> None:
                    controls = [run_button]
                    if save_button is not None:
                        controls.append(save_button)
                    controls.extend(
                        control
                        for control in [batch_submit_button, batch_status_button, batch_import_button]
                        if control is not None
                    )
                    for control in controls:
                        if enabled:
                            control.enable()
                        else:
                            control.disable()

        all_recent_rows = db.list_recent_results(limit=500)
        recent_rows = filter_rows_for_active_scope(all_recent_rows, state["config"])
        portfolio_story = build_portfolio_story(recent_rows, state["config"])
        intent_rows = build_intent_map_rows(recent_rows, state["config"])
        page_gap_rows = build_page_gap_rows(recent_rows, state["config"])
        budget_guardrail = build_budget_guardrail(all_recent_rows, state["config"])

        with ui.column().classes("w-full order-20") as result_stage_container:
            render_stage_header("2", "結果を見る", "")
        latest_result_container = ui.column().classes("w-full gap-5 order-21")
        with ui.column().classes("w-full gap-5 order-22") as summary_container:
            with ui.card().classes("section-card p-5 w-full"):
                ui.label("ダッシュボード概要").classes("section-font section-title text-[26px] font-bold")
                ui.label("現行の可視性、引用、再利用効率をすぐ見ます。").classes("text-[14px] leading-6 soft-label mt-2")
                with ui.row().classes("w-full gap-4 mt-4 flex-wrap"):
                    summary_refs["kpis"]["target_hit_rate"] = metric_card("自社露出率", "0.0%", "回答で自社URLが引用に入った割合")
                    summary_refs["kpis"]["avg_score"] = metric_card("AI visibility", "0/100", "保存済み結果の平均 visibility スコア")
                    summary_refs["kpis"]["external_lead_rate"] = metric_card("外部サイト優勢率", "0.0%", "外部サイトが先行した質問の割合")
                    summary_refs["kpis"]["cache_hit_rate"] = metric_card("キャッシュ再利用", "0.0%", "入力トークン再利用の効き具合")
                    summary_refs["kpis"]["total_runs"] = metric_card("観測件数", "0件", "累積検索呼び出し 0 回")
            with ui.row().classes("w-full gap-5 flex-wrap"):
                with ui.card().classes("section-card p-5 flex-1 min-w-[430px] chart-shell"):
                    ui.label("AI visibility スコア推移").classes("section-font section-title text-[24px] font-bold")
                    summary_refs["plots"]["visibility"] = ui.plotly(
                        build_overall_visibility_chart(recent_rows, state["config"])
                    ).classes("w-full h-[320px] mt-3")
                with ui.card().classes("section-card p-5 flex-1 min-w-[430px] chart-shell"):
                    ui.label("自社露出率と外部サイト優勢率の推移").classes("section-font section-title text-[24px] font-bold")
                    summary_refs["plots"]["history_focus"] = ui.plotly(
                        build_visibility_focus_chart(recent_rows, state["config"])
                    ).classes("w-full h-[320px] mt-3")
        summary_refs["container"] = summary_container

        with ui.column().classes("w-full order-40"):
            render_stage_header("3", "詳細", "")
        with ui.card().classes("section-card p-5 w-full order-41"):
            with ui.expansion("詳細を見る").classes("w-full panel-card"):
                with ui.column().classes("p-4 gap-5 w-full"):
                    with ui.tabs().classes("detail-tabs-shell w-full") as support_tabs:
                        support_ops_tab = ui.tab("運用")
                        support_detail_tab = ui.tab("詳細")
                    with ui.tab_panels(support_tabs, value=support_ops_tab).classes("detail-tab-panels w-full mt-4"):
                        with ui.tab_panel(support_ops_tab).classes("px-0 py-2"):
                            with ui.row().classes("w-full gap-5 flex-wrap items-start"):
                                with ui.card().classes("section-card p-5 flex-1 min-w-[360px]"):
                                    ui.label("確認内容").classes("section-font section-title text-[26px] font-bold")
                                    ui.label("今の入力内容を名前つきで保存し、あとで再利用します。").classes("text-[14px] leading-6 soft-label mt-2")
                                    question_set_name_input = ui.input("確認内容の名前", value="").props("outlined").classes("w-full mt-4")
                                    with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
                                        question_set_select = ui.select({}, value=None, label="保存済みの確認内容").props("outlined").classes(
                                            "w-[280px] flex-1"
                                        )
                                        ui.button("保存 / 更新", on_click=on_question_set_save).props("unelevated no-caps color=deep-orange-7 text-color=white").classes("accent-button text-[16px] font-bold")
                                        ui.button("読み込み", on_click=on_question_set_load).props("outline").classes(
                                            "secondary-button text-[16px]"
                                        )
                                        save_button = ui.button("今の入力を保存", on_click=on_save).props("outline").classes(
                                            "secondary-button text-[16px]"
                                        )
                                    question_set_table = ui.table(
                                        columns=build_question_set_table_columns(),
                                        rows=[],
                                        row_key="question_set_id",
                                        pagination=5,
                                    ).props(TABLE_BASE_PROPS).classes("w-full mt-4")

                                with ui.card().classes("section-card p-5 flex-1 min-w-[420px]"):
                                    ui.label("定期チェック").classes("section-font section-title text-[26px] font-bold")
                                    ui.label("曜日と時刻で自動実行します。").classes("text-[14px] leading-6 soft-label mt-2")
                                    ui.label("この時刻から処理を開始します。結果の反映には最大24時間かかる場合があります。").classes(
                                        "text-[13px] leading-6 text-helper mt-2"
                                    )
                                    scheduler_status_label = ui.label(build_scheduler_status_text()).classes("text-[14px] leading-6 text-helper mt-3")
                                    schedule_question_set_select = ui.select({}, value=None, label="対象の確認内容").props("outlined").classes(
                                        "w-full mt-3"
                                    )
                                    with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
                                        schedule_name_input = ui.input("スケジュール名", value="").props("outlined").classes("w-[240px] flex-1")
                                        schedule_time_input = ui.input("時刻", value="09:00").props("outlined").classes("w-[120px]")
                                        schedule_timezone_input = ui.input("タイムゾーン", value=state["config"].timezone).props("outlined").classes("w-[180px]")
                                    with ui.row().classes("w-full gap-3 mt-3 flex-wrap items-end"):
                                        schedule_weekdays_select = ui.select(
                                            {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"},
                                            value=[0],
                                            label="曜日",
                                        ).props("multiple outlined use-chips").classes("w-[280px] flex-1")
                                        schedule_weekly_runs_input = ui.number("週あたり回数", value=1, min=1, max=7).props("outlined").classes(
                                            "w-[140px]"
                                        )
                                        schedule_enabled_switch = ui.switch("有効", value=True)
                                    with ui.row().classes("w-full gap-3 mt-4 flex-wrap"):
                                        ui.button("定期チェックを保存", on_click=on_schedule_save).props("unelevated no-caps color=deep-orange-7 text-color=white").classes("accent-button text-[16px] font-bold")
                                    schedule_table = ui.table(
                                        columns=build_schedule_table_columns(),
                                        rows=[],
                                        row_key="schedule_id",
                                        pagination=6,
                                    ).props(TABLE_BASE_PROPS).classes("w-full mt-4")
                                    ui.label("複製直後は停止状態で保存します。").classes("text-[13px] leading-6 text-helper mt-3")
                                    schedule_manage_select = ui.select({}, value=None, label="操作する定期チェック").props("outlined").classes("w-full mt-4")
                                    with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
                                        ui.button("フォームに読み込み", on_click=on_schedule_load).props("outline").classes(
                                            "secondary-button text-[15px]"
                                        )
                                        ui.button("複製して AB 用に作る", on_click=on_schedule_duplicate).props("outline").classes(
                                            "secondary-button text-[15px]"
                                        )
                                        ui.button("削除", on_click=on_schedule_delete).props("outline").classes(
                                            "secondary-button text-[15px]"
                                        )
                                    compare_mode_select = ui.select(
                                        {"schedule": "別の定期チェックと比較", "question_set": "別の確認内容と比較"},
                                        value="schedule",
                                        label="何と比べるか",
                                        on_change=lambda _: refresh_schedule_views(
                                            schedule_table,
                                            scheduler_status_label,
                                            schedule_manage_select,
                                            compare_target_select,
                                            compare_mode_select,
                                        ),
                                    ).props("outlined").classes("w-full mt-4")
                                    compare_target_select = ui.select({}, value=None, label="比較先").props("outlined").classes("w-full mt-3")
                                    with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
                                        ui.button("差分を表示", on_click=on_schedule_diff_refresh).props("outline").classes(
                                            "secondary-button text-[15px]"
                                        )
                                    schedule_diff_container = ui.column().classes("w-full mt-4 gap-3")
                                    with ui.dialog() as schedule_delete_dialog, ui.card().classes("card-detail p-5 w-[420px] max-w-full"):
                                        ui.label("この定期チェックを削除しますか").classes("section-font section-title text-[22px] font-bold")
                                        ui.label("定期設定だけを削除し、既存の実行履歴は残します。").classes(
                                            "text-[14px] leading-6 text-support mt-2"
                                        )
                                        with ui.row().classes("w-full justify-end gap-3 mt-5"):
                                            ui.button("キャンセル", on_click=schedule_delete_dialog.close).props("outline").classes(
                                                "secondary-button text-[15px]"
                                            )
                                            ui.button("削除する", on_click=confirm_schedule_delete).props("unelevated no-caps color=deep-orange-7 text-color=white").classes("accent-button text-[15px] font-bold")

                            with ui.card().classes("section-card p-5 w-full mt-5"):
                                ui.label("まとめて確認").classes("section-font section-title text-[24px] font-bold")
                                ui.label("件数が多いときだけ使います。").classes("text-[14px] leading-6 soft-label mt-2")
                                runtime_micro_label = ui.label(build_runtime_microcopy(state["config"])).classes(
                                    "text-[13px] leading-6 text-helper mt-4"
                                )
                                cost_policy_label = ui.label(
                                    "内部ガードは維持し、金額は画面に出しません。"
                                    f" 実行件数が多いときは {('停止' if state['config'].budget_guardrail_mode == 'stop' else '警告')} します。"
                                ).classes("text-[13px] leading-6 text-helper mt-2")
                                decision_refs["budget"]["headline"] = ui.label(budget_guardrail["headline"]).classes(
                                    f"summary-mainline mt-4 {build_guardrail_text_class(budget_guardrail['status'])}"
                                )
                                decision_refs["budget"]["summary"] = ui.label(budget_guardrail["summary"]).classes(
                                    "text-[14px] leading-6 text-support mt-3"
                                )
                                with ui.row().classes("w-full gap-3 mt-4 flex-wrap"):
                                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                                        ui.label("今日の実行").classes("text-[12px] tracking-[0.18em] soft-label")
                                        decision_refs["budget"]["today"] = ui.label(
                                            f"{int(budget_guardrail['today_result_count'] or 0)}件"
                                        ).classes("metric-font text-[20px] font-bold text-main")
                                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                                        ui.label("今回の投入予定").classes("text-[12px] tracking-[0.18em] soft-label")
                                        decision_refs["budget"]["estimate"] = ui.label(
                                            f"{int(budget_guardrail['request_count'] or 0)}件"
                                        ).classes("metric-font text-[20px] font-bold text-main")
                                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                                        ui.label("ガード挙動").classes("text-[12px] tracking-[0.18em] soft-label")
                                        decision_refs["budget"]["remaining"] = ui.label(
                                            budget_guardrail["guardrail_mode_label"]
                                        ).classes("metric-font text-[20px] font-bold text-main")
                                    with ui.column().classes("mini-stat-card flex-1 gap-1"):
                                        ui.label("キャッシュ保持").classes("text-[12px] tracking-[0.18em] soft-label")
                                        decision_refs["budget"]["efficiency"] = ui.label(
                                            localize_cache_retention_label(
                                                resolve_prompt_cache_retention(state["config"].model, state["config"].prompt_cache_retention)
                                            )
                                        ).classes("metric-font text-[20px] font-bold text-main")
                                decision_refs["budget"]["note"] = ui.label(
                                    (
                                        "24時間キャッシュが使えない条件では、自動でメモリ内へ切り替えています。"
                                        if state["config"].prompt_cache_retention == "24h"
                                        and budget_guardrail["effective_prompt_cache_retention"] != "24h"
                                        else "キャッシュと一括割引を優先しつつ、内部の実行ガードは維持し、金額は画面に出しません。"
                                    )
                                ).classes("text-[13px] leading-6 text-helper mt-4")
                                ui.label("通常は上の「分析を実行」で十分です。").classes("text-[13px] leading-6 text-helper mt-2")
                                batch_status_label = ui.label("まとめて確認はまだ使っていません").classes(
                                    "text-[15px] font-bold text-main mt-3"
                                )
                                batch_summary_label = ui.label(
                                    "たくさんの質問をまとめて回すときだけ使います。"
                                ).classes("text-[13px] text-helper mt-1")
                                with ui.row().classes("gap-3 mt-4 flex-wrap"):
                                    batch_submit_button = ui.button("まとめて開始", on_click=on_batch_submit).props("outline").classes(
                                        "secondary-button text-[16px]"
                                    )
                                    batch_status_button = ui.button("進み具合を更新", on_click=on_batch_refresh).props("outline").classes(
                                        "secondary-button text-[16px]"
                                    )
                                    batch_import_button = ui.button("結果を反映", on_click=on_batch_import).props("outline").classes(
                                        "secondary-button text-[16px]"
                                    )
                                batch_job_select = ui.select(
                                    {},
                                    value=None,
                                    label="対象のまとめ確認",
                                    on_change=lambda _: refresh_batch_job_views(
                                        batch_job_select,
                                        batch_job_table,
                                        batch_status_label,
                                        batch_summary_label,
                                    ),
                                ).props("outlined").classes("w-full mt-4")
                                batch_job_table = ui.table(
                                    columns=build_batch_table_columns(),
                                    rows=[],
                                    row_key="batch_job_id",
                                    pagination=8,
                                ).props(TABLE_BASE_PROPS).classes("w-full mt-4")

                            with ui.row().classes("w-full gap-5 mt-5 flex-wrap items-start"):
                                with ui.card().classes("section-card p-5 flex-1 min-w-[430px]"):
                                    with ui.expansion("実行履歴を見る").classes("w-full panel-card"):
                                        with ui.column().classes("p-4 gap-3 w-full"):
                                            run_table = ui.table(
                                                columns=build_run_table_columns(state["config"].pricing.show_poc_costs),
                                                rows=[],
                                                row_key="run_id",
                                                pagination=8,
                                            ).props(TABLE_BASE_PROPS).classes("w-full")
                                with ui.card().classes("section-card p-5 flex-1 min-w-[380px]"):
                                    ui.label("出力ファイル").classes("section-font section-title text-[24px] font-bold")
                                    ui.label("CSV / JSON を更新します。").classes("text-[14px] leading-6 soft-label mt-2")
                                    with ui.row().classes("w-full gap-3 mt-4 flex-wrap"):
                                        ui.button("CSV / JSON 出力を更新", on_click=on_export).props("unelevated no-caps color=deep-orange-7 text-color=white").classes(
                                            "accent-button text-[16px] font-bold"
                                        )
                                    export_status_label = ui.label("まだ export を生成していません。").classes(
                                        "text-[14px] text-helper mt-3"
                                    )
                                    export_table = ui.table(
                                        columns=build_export_table_columns(),
                                        rows=[],
                                        row_key="label",
                                        pagination=5,
                                    ).props(TABLE_BASE_PROPS).classes("w-full mt-3")
                        with ui.tab_panel(support_detail_tab).classes("px-0 py-2"):
                            with ui.column().classes("w-full gap-5"):
                                with ui.card().classes("card-secondary p-5 w-full"):
                                    ui.label("全体の傾向").classes("section-font section-title text-[26px] font-bold")
                                    with ui.row().classes("w-full gap-4 mt-4 flex-wrap"):
                                        metric_refs["overall"] = insight_card(
                                            "自社が出たか",
                                            portfolio_story["overall_label"],
                                            portfolio_story["overall_summary"],
                                        )
                                        metric_refs["competition"] = insight_card(
                                            "外部名・外部サイト",
                                            portfolio_story["competition_label"],
                                            portfolio_story["competition_summary"],
                                        )
                                        metric_refs["action"] = insight_card(
                                            "次に見直す質問",
                                            portfolio_story["action_headline"],
                                            portfolio_story["action_summary"],
                                        )
                                with ui.card().classes("section-card p-5 w-full"):
                                    source_container = ui.column().classes("w-full gap-3")
                                with ui.card().classes("section-card p-5 w-full"):
                                    dashboard_status = ui.label(
                                        f"総評 {portfolio_story['overall_label']} | "
                                        f"自社が見える質問 {portfolio_story['visible_topics']}/{portfolio_story['total_topics']}件 | "
                                        f"外部名が見える質問 {portfolio_story['competitor_topics']}/{portfolio_story['total_topics']}件 | "
                                        f"先に直す質問 {portfolio_story['needs_fix_topics']}/{portfolio_story['total_topics']}件"
                                    ).classes("text-[15px] text-helper")
                                    ui.label("質問ごとの判断一覧").classes("section-font section-title text-[28px] font-bold mt-4")
                                    rows_table = ui.table(
                                        columns=build_result_table_columns(state["config"].pricing.show_poc_costs),
                                        rows=[],
                                        row_key="result_id",
                                        pagination=10,
                                    ).props(TABLE_BASE_PROPS).classes("w-full mt-4")
                                    detail_select = ui.select({}, value=None, label="詳細で見る結果").props("outlined").classes("w-full mt-4")
                                    detail_container = ui.column().classes("w-full mt-4")
                                with ui.expansion("分析の広がりを見る").classes("w-full panel-card"):
                                    with ui.column().classes("p-4 gap-5 w-full"):
                                        with ui.row().classes("w-full gap-5 flex-wrap"):
                                            weakest_intent = intent_rows[0] if intent_rows else None
                                            with ui.card().classes("card-primary p-5 flex-1 min-w-[320px]"):
                                                ui.label("意図マップ").classes("section-font section-title text-[24px] font-bold")
                                                decision_refs["intent"]["headline"] = ui.label(
                                                    f"{weakest_intent['intent_label']}意図が弱い" if weakest_intent else "弱い意図は未判定"
                                                ).classes("summary-mainline mt-4 text-main")
                                                decision_refs["intent"]["summary"] = ui.label(
                                                    (
                                                        f"{weakest_intent['needs_fix_count']}/{weakest_intent['question_count']}件が外部サイト優勢または未露出です。"
                                                        f" まずは {weakest_intent['top_page_type']} を補強してください。"
                                                    )
                                                    if weakest_intent
                                                    else "結果が保存されると、どの意図クラスタが弱いかをここに出します。"
                                                ).classes("text-[14px] leading-6 text-support mt-3")
                                                decision_refs["intent"]["table"] = ui.table(
                                                    columns=build_intent_table_columns(),
                                                    rows=intent_rows,
                                                    row_key="intent_label",
                                                    pagination=5,
                                                ).props(TABLE_BASE_PROPS).classes("w-full mt-4")

                                            top_gap = page_gap_rows[0] if page_gap_rows else None
                                            with ui.card().classes("card-primary p-5 flex-1 min-w-[320px]"):
                                                ui.label("不足ページナビ").classes("section-font section-title text-[24px] font-bold")
                                                decision_refs["gap"]["headline"] = ui.label(
                                                    f"先に作るのは {top_gap['page_type_label']}" if top_gap else "不足ページは未判定"
                                                ).classes("summary-mainline mt-4 text-main")
                                                decision_refs["gap"]["summary"] = ui.label(
                                                    (
                                                        f"{top_gap['priority_label']}。{top_gap['needs_fix_count']}/{top_gap['question_count']}件で不足しています。"
                                                        f" {top_gap['next_step']}"
                                                    )
                                                    if top_gap
                                                    else "結果が保存されると、制作着手すべきページ種別をここに出します。"
                                                ).classes("text-[14px] leading-6 text-support mt-3")
                                                decision_refs["gap"]["table"] = ui.table(
                                                    columns=build_gap_table_columns(),
                                                    rows=page_gap_rows,
                                                    row_key="page_type_label",
                                                    pagination=5,
                                                ).props(TABLE_BASE_PROPS).classes("w-full mt-4")

                                        with ui.row().classes("w-full gap-5 flex-wrap"):
                                            with ui.card().classes("section-card p-5 flex-1 min-w-[430px] chart-shell"):
                                                ui.label("全体の推移").classes("section-font section-title text-[28px] font-bold")
                                                overall_visibility_plot = ui.plotly(build_overall_visibility_chart(recent_rows, state["config"])).classes("w-full h-[360px] mt-3")
                                            with ui.card().classes("section-card p-5 flex-1 min-w-[430px] chart-shell"):
                                                ui.label("質問別の推移").classes("section-font section-title text-[28px] font-bold")
                                                query_select = ui.select({}, value=None, label="質問を選択").props("outlined").classes("w-full mt-3")
                                                query_drilldown_plot = ui.plotly(build_query_drilldown_chart(recent_rows, "")).classes("w-full h-[320px] mt-3")

                                        with ui.row().classes("w-full gap-5 flex-wrap"):
                                            with ui.card().classes("section-card p-5 flex-1 min-w-[430px] chart-shell"):
                                                ui.label("意図クラスタの推移").classes("section-font section-title text-[28px] font-bold")
                                                intent_trend_plot = ui.plotly(build_intent_cluster_chart(recent_rows, state["config"])).classes("w-full h-[360px] mt-3")
                                            with ui.card().classes("section-card p-5 flex-1 min-w-[430px] chart-shell"):
                                                ui.label("不足ページの推移").classes("section-font section-title text-[28px] font-bold")
                                                page_gap_trend_plot = ui.plotly(build_page_gap_trend_chart(recent_rows, state["config"])).classes("w-full h-[360px] mt-3")

                                        with ui.row().classes("w-full gap-5 flex-wrap"):
                                            with ui.card().classes("section-card p-5 flex-1 min-w-[430px]"):
                                                ui.label("クラスタ下書き作成").classes("section-font section-title text-[26px] font-bold")
                                                cluster_kind_select = ui.select(
                                                    {
                                                        "intent": "意図クラスタ",
                                                        "page_gap": "不足ページクラスタ",
                                                        "question_set": "確認内容単位",
                                                    },
                                                    value="intent",
                                                    label="どのまとまりで作るか",
                                                    on_change=lambda _: (
                                                        refresh_cluster_brief_views(
                                                            filter_rows_for_active_scope(db.list_recent_results(limit=2000), state["config"]),
                                                            state["config"],
                                                            cluster_kind_select,
                                                            cluster_target_select,
                                                            saved_cluster_brief_select,
                                                            cluster_brief_table,
                                                        )
                                                        if cluster_target_select is not None and saved_cluster_brief_select is not None and cluster_brief_table is not None
                                                        else None
                                                    ),
                                                ).props("outlined").classes("w-full mt-4")
                                                cluster_target_select = ui.select({}, value=None, label="対象のまとまり").props("outlined").classes("w-full mt-3")
                                                with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
                                                    ui.button("クラスタ下書きを生成して保存", on_click=on_cluster_brief_generate).props("unelevated no-caps color=deep-orange-7 text-color=white").classes(
                                                        "accent-button text-[15px] font-bold"
                                                    )
                                                saved_cluster_brief_select = ui.select({}, value=None, label="保存済みの下書き").props("outlined").classes("w-full mt-4")
                                                with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
                                                    ui.button("保存済み下書きを表示", on_click=on_saved_cluster_brief_load).props("outline").classes(
                                                        "secondary-button text-[15px]"
                                                    )
                                                cluster_brief_table = ui.table(
                                                    columns=build_cluster_brief_table_columns(),
                                                    rows=[],
                                                    row_key="brief_id",
                                                    pagination=5,
                                                ).props(TABLE_BASE_PROPS).classes("w-full mt-4")
                                                cluster_brief_container = ui.column().classes("w-full mt-4 gap-3")

                                            with ui.card().classes("section-card p-5 flex-1 min-w-[430px]"):
                                                ui.label("実行結果比較").classes("section-font section-title text-[26px] font-bold")
                                                outcome_scope_kind_select = ui.select(
                                                    {"schedule": "定期チェックごと", "question_set": "確認内容ごと"},
                                                    value="schedule",
                                                    label="系列",
                                                    on_change=lambda _: (
                                                        refresh_outcome_compare_views(
                                                            outcome_scope_kind_select,
                                                            outcome_scope_target_select,
                                                            outcome_run_a_select,
                                                            outcome_run_b_select,
                                                        )
                                                        if outcome_scope_target_select is not None and outcome_run_a_select is not None and outcome_run_b_select is not None
                                                        else None
                                                    ),
                                                ).props("outlined").classes("w-full mt-4")
                                                outcome_scope_target_select = ui.select(
                                                    {},
                                                    value=None,
                                                    label="対象の定期チェック / 確認内容",
                                                    on_change=lambda _: (
                                                        refresh_outcome_compare_views(
                                                            outcome_scope_kind_select,
                                                            outcome_scope_target_select,
                                                            outcome_run_a_select,
                                                            outcome_run_b_select,
                                                        )
                                                        if outcome_scope_kind_select is not None and outcome_run_a_select is not None and outcome_run_b_select is not None
                                                        else None
                                                    ),
                                                ).props("outlined").classes("w-full mt-3")
                                                with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
                                                    outcome_run_a_select = ui.select({}, value=None, label="比較元").props("outlined").classes("w-[220px] flex-1")
                                                    outcome_run_b_select = ui.select({}, value=None, label="比較先").props("outlined").classes("w-[220px] flex-1")
                                                with ui.row().classes("w-full gap-3 mt-3 flex-wrap"):
                                                    ui.button("実行結果を比較する", on_click=on_outcome_compare_show).props("outline").classes(
                                                        "secondary-button text-[15px]"
                                                    )
                                                outcome_compare_container = ui.column().classes("w-full mt-4 gap-3")

        refresh_question_set_views(question_set_select, question_set_table, schedule_question_set_select)
        refresh_schedule_views(
            schedule_table,
            scheduler_status_label,
            schedule_manage_select,
            compare_target_select,
            compare_mode_select,
        )
        if schedule_diff_container is not None:
            render_schedule_diff("", str(compare_mode_select.value or "schedule"), "", schedule_diff_container)

        def sync_question_set_name_from_selection() -> None:
            selected = db.get_question_set(str(question_set_select.value or "")) if question_set_select.value else None
            if selected:
                question_set_name_input.value = str(selected.get("name") or "")
                question_set_name_input.update()
                schedule_question_set_select.value = str(selected.get("question_set_id") or "")
                schedule_question_set_select.update()

        sync_question_set_name_from_selection()

        def refresh_query_drilldown() -> None:
            query_drilldown_plot.figure = build_query_drilldown_chart(
                filter_rows_for_active_scope(db.list_recent_results(limit=500), state["config"]),
                str(query_select.value or ""),
            )
            query_drilldown_plot.update()

        def periodic_refresh() -> None:
            refresh_question_set_views(question_set_select, question_set_table, schedule_question_set_select)
            sync_question_set_name_from_selection()
            refresh_schedule_views(
                schedule_table,
                scheduler_status_label,
                schedule_manage_select,
                compare_target_select,
                compare_mode_select,
            )
            refresh_batch_job_views(batch_job_select, batch_job_table, batch_status_label, batch_summary_label)
            refresh_dashboard(
                state["config"],
                state["show_primary_results"],
                result_stage_container,
                metric_refs,
                decision_refs,
                rows_table,
                run_table,
                overall_visibility_plot,
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
            )
            refresh_cluster_and_outcome_sections()
            render_active_cluster_and_outcome_panels()

        refresh_dashboard(
            state["config"],
            state["show_primary_results"],
            result_stage_container,
            metric_refs,
            decision_refs,
            rows_table,
            run_table,
            overall_visibility_plot,
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
        )
        refresh_cluster_and_outcome_sections()
        render_active_cluster_and_outcome_panels()
        refresh_export_views(export_table, export_status_label, state["export_rows"])
        query_select.on("update:model-value", lambda _: refresh_query_drilldown())
        question_set_select.on("update:model-value", lambda _: sync_question_set_name_from_selection())
        detail_select.on(
            "update:model-value",
            lambda _: refresh_result_detail_views(
                filter_rows_for_active_scope(db.list_recent_results(limit=500), state["config"]),
                detail_select,
                detail_container,
                state["config"],
            ),
        )
        ui.timer(60.0, periodic_refresh)


@ui.page("/")
def index() -> None:
    render_page()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="コトメガネ",
        host=config_state.ui_host,
        port=config_state.ui_port,
        reload=False,
        show=False,
        favicon=str(ASSETS_DIR / "favicon_v2.png"),
    )
