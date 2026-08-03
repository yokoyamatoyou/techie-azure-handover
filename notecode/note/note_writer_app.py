"""note_writer_app.py - NiceGUI app for blog-ready articles."""
from __future__ import annotations

import json
import hashlib
import logging
import logging.handlers
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Set, Tuple

from fastapi.middleware.cors import CORSMiddleware
from nicegui import app, run, ui
from html_sanitizer import Sanitizer
import re

from dotenv import load_dotenv

from core.app_config import get_source_reading_config
from shared.auth.nicegui_auth import NiceGUIAuthMiddleware
from shared.auth.api import router as identity_linking_router
from shared.billing.api import router as phase2_billing_router
from shared.billing.webhook_handler import router as stripe_webhook_router
from shared.usage.api import router as usage_router

# Load environment variables from .env file
load_dotenv()

app.include_router(phase2_billing_router)
app.include_router(identity_linking_router)
app.include_router(stripe_webhook_router)
app.include_router(usage_router)
app.add_middleware(NiceGUIAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin
        for origin in dict.fromkeys(
            [
                os.environ.get("HUB_BASE_URL", "").rstrip("/"),
                os.environ.get("HUB_URL", "").rstrip("/"),
                "https://app.techie.jp",
                "https://techie-app-exdde6afb0aydgg8.japanwest-01.azurewebsites.net",
            ]
        )
        if origin
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

class _JSONFormatter(logging.Formatter):
    """ログをJSON形式にフォーマットする"""
    def format(self, record):
        data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": os.environ.get("SERVICE_NAME", "unknown"),
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            data["traceback"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


class _BenignNiceGUIErrorFilter(logging.Filter):
    """Suppress noisy framework disconnect errors that are not actionable."""

    _DROP_PATTERNS = (
        "The parent slot of the element has been deleted.",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            message = ""
        if any(pattern in message for pattern in self._DROP_PATTERNS):
            return False
        if record.exc_info and record.exc_info[1] is not None:
            exc_text = str(record.exc_info[1])
            if any(pattern in exc_text for pattern in self._DROP_PATTERNS):
                return False
        return True


def setup_app_logging() -> None:
    """アプリ起動時に呼び出して、ログを設定する"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    root = logging.getLogger()
    for handler in root.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler) and getattr(handler, "_techie_log", False):
            return

    handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,   # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(_JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))
    handler.addFilter(_BenignNiceGUIErrorFilter())
    handler._techie_log = True

    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root.setLevel(level)
    root.addHandler(handler)

    # 起動時のログ
    logging.info("アプリ起動 (LOG_LEVEL=%s)", level_name)

setup_app_logging()


async def _ensure_usage_credit_available(service_key: str) -> bool:
    try:
        summary = await get_usage_summary_for_current_user(service_key=service_key)
    except Exception:
        logging.exception("Usage credit check failed for service_key=%s", service_key)
        ui.notify("クレジット確認に失敗しました。時間をおいて再度お試しください。", color="negative")
        return False
    if int(summary.get("remaining_credits") or 0) <= 0:
        ui.notify("クレジットが不足しています。契約管理画面で残高をご確認ください。", color="warning")
        return False
    return True


async def _consume_usage_credit_after_success(*, service_key: str, action_key: str, attempt_id: str) -> bool:
    try:
        summary = await consume_usage_for_current_user(
            service_key=service_key,
            action_key=action_key,
            units=1,
            idempotency_key=f"{service_key}:{action_key}:{attempt_id}",
            metadata={"trigger": "post_success"},
        )
        logging.info(
            "Usage credit debited service_key=%s action_key=%s attempt_id=%s event_id=%s remaining=%s replay=%s",
            service_key,
            action_key,
            attempt_id,
            summary.get("usage_event_id"),
            summary.get("remaining_credits"),
            summary.get("idempotent_replay"),
        )
        return True
    except Exception:
        logging.exception("Usage credit debit failed for service_key=%s action_key=%s", service_key, action_key)
        ui.notify("処理は完了しましたが、クレジット消費の記録に失敗しました。管理者へ連絡してください。", color="negative")
        return False

_PREVIEW_PLACEHOLDER = """生成を始めると、ここに本文の冒頭が表示されます。"""

# 画像パターン定数 / helper は note.image_prompt_helpers に分離済み (ファイル後段の import 経由で参照)。

from note.article_fetcher import ArticleFetcher
from note import genre_manager
from note.current_mainline_runner import (
    assess_current_mainline_question_policy,
    build_omakase_preflight,
    build_current_mainline_confirm_preview,
    build_current_mainline_input_contract,
    build_fail_closed_generation_result,
    execute_current_mainline_generation,
    merge_omakase_seed_into_current_mainline_kwargs,
    resolve_current_mainline_ui_selection,
    validate_current_mainline_generation_gate,
)
from note.newalgorithm_pipeline import output_guard as output_guard_mod
from note.newalgorithm_pipeline.strict_saas import UI_DEFAULT_STRICT_SAAS_MODE, allows_guard_auto_repair
from note.newalgorithm_pipeline.legal_postcheck import run_legal_postcheck
from note.simple_note_pipeline.pipeline import MinimalPipeline
from note.input_contract_v1 import InputContractValidationError
from note.llm_client import LLMClient
from note.policy_engine import detect_ambiguous_terms, estimate_category_meta, normalize_category_meta
from note.preview_sanitizer import sanitize_markdown_preview
from note.current_mainline_profile_resolver import (
    BRANDING_FOCUS_LABELS,
    BRANDING_SUBTYPE_LABELS,
    PATTERN_SELECT_LABELS,
    resolve_compact_writing_profile,
)
from note.image_config import (
    NOTE_IMAGE_SIZE_LABEL,
    DEFAULT_IMAGE_COUNT,
    DEFAULT_IMAGE_MODEL,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_IMAGE_QUALITY,
    DEFAULT_TEXT_IMAGE_QUALITY,
    DEFAULT_IMAGE_OUTPUT_FORMAT,
    DEFAULT_IMAGE_BACKGROUND,
    DEFAULT_IMAGE_MODERATION,
    TEXT_OVERLAY_FONT_PATH,
    GENERATED_IMAGES_DIR,
)
from note.image_editing import (
    ImageAdjustment,
    PrivacyBlur,
    render_preview as render_image_edit_preview,
    save_edited_image as save_edited_image_core,
)
from note.blog_image_auto import generate_blog_images_for_article, successful_image_paths
from note.current_mainline_runtime_logging import (
    append_generation_audit_record as runtime_append_generation_audit_record,
    append_ui_journey_event as runtime_append_ui_journey_event,
    build_latest_quality_report_payload as runtime_build_latest_quality_report_payload,
    collect_runtime_config_snapshot as runtime_collect_runtime_config_snapshot,
    persist_latest_generation_snapshot as runtime_persist_latest_generation_snapshot,
)
from note.route_0506_ui_bridge import (
    ROUTE_0506_ID,
    UI_ROUTE_SELECTION_ENV,
    build_route_0506_progress_view,
    build_route_0506_user_facing_blocked_view,
    resolve_ui_body_route_selection,
    run_route_0506_ui_onecase,
)
from note.note_text_format_helpers import (
    _build_short_sns_text,
    _hashtags_to_plain,
    _replace_hashtags_for_preview,
    _safe_round_float,
    _safe_url,
    _sanitize_href_allow_file,
    _to_note_format,
    _to_plain_dict,
    _to_plain_list,
)
from note.proposition_density_helpers import (
    _analyze_proposition_density,
    _build_proposition_density_target_text,
    _classify_proposition_sentence,
    _count_proposition_content_terms,
    _count_sentences,
    _extract_proposition_sentences,
    _PROPOSITION_CONCRETE_SIGNAL_PATTERN,
    _PROPOSITION_LOW_SIGNAL_PATTERN,
    _PROPOSITION_STOP_TOKENS,
    _PROPOSITION_TOKEN_PATTERN,
)
from note.generation_exception_helpers import (
    _build_guard_retry_prompt,
    _classify_generation_exception,
    _extract_guard_forbidden_topics,
    _is_guard_auto_repair_candidate,
    _is_transient_exception,
    _resolve_guard_retry_category,
)
from note.image_prompt_helpers import (
    DEFAULT_IMAGE_PATTERN_KEY,
    IMAGE_PATTERN_LABEL_TO_KEY,
    IMAGE_PATTERN_OPTIONS,
    _apply_image_pattern_to_prompt,
    _build_image_pattern_suffix,
    _build_image_prompt,
    _normalize_image_pattern_key,
    _split_image_prompts,
)
from note.current_mainline_ui_confirm_adapter import (
    build_invalidate_journey_confirmation as build_invalidate_journey_confirmation_core,
    build_journey_confirm_blocked_view as build_journey_confirm_blocked_view_core,
    build_journey_confirm_preview_view as build_journey_confirm_preview_view_core,
    build_journey_confirm_summary as build_journey_confirm_summary_core,
    build_journey_confirmed_view as build_journey_confirmed_view_core,
    build_journey_selection_summary as build_journey_selection_summary_core,
    build_journey_signature as build_journey_signature_core,
)
from note.current_mainline_ui_generation_state_adapter import (
    build_current_mainline_generation_cleanup_plan as build_current_mainline_generation_cleanup_plan_core,
    build_current_mainline_generation_complete_plan as build_current_mainline_generation_complete_plan_core,
    build_current_mainline_generation_exception_plan as build_current_mainline_generation_exception_plan_core,
    build_current_mainline_generation_prerun_plan as build_current_mainline_generation_prerun_plan_core,
)
from note.current_mainline_ui_generation_telemetry_adapter import (
    build_current_mainline_generation_event_request as build_current_mainline_generation_event_request_core,
    build_current_mainline_generation_gate_extra as build_current_mainline_generation_gate_extra_core,
    build_current_mainline_generation_snapshot_request as build_current_mainline_generation_snapshot_request_core,
    build_current_mainline_generation_telemetry_context as build_current_mainline_generation_telemetry_context_core,
)
from note.current_mainline_ui_result_adapter import (
    attach_prompt_context_to_result as attach_prompt_context_to_result_core,
    build_current_mainline_ambiguity_confirmation_view as build_current_mainline_ambiguity_confirmation_view_core,
    build_current_mainline_completion_payload as build_current_mainline_completion_payload_core,
    build_current_mainline_confirmation_required_view as build_current_mainline_confirmation_required_view_core,
    build_current_mainline_fetch_failure_view as build_current_mainline_fetch_failure_view_core,
    build_current_mainline_generation_error_view as build_current_mainline_generation_error_view_core,
    build_current_mainline_generation_busy_view as build_current_mainline_generation_busy_view_core,
    build_current_mainline_legal_postcheck_payload as build_current_mainline_legal_postcheck_payload_core,
    build_current_mainline_generation_no_sources_view as build_current_mainline_generation_no_sources_view_core,
    build_current_mainline_guard_retry_exception_view as build_current_mainline_guard_retry_exception_view_core,
    build_current_mainline_invalid_article_type_view as build_current_mainline_invalid_article_type_view_core,
    build_current_mainline_missing_required_inputs_view as build_current_mainline_missing_required_inputs_view_core,
    build_current_mainline_no_valid_sources_view as build_current_mainline_no_valid_sources_view_core,
    build_current_mainline_output_guard_blocked_view as build_current_mainline_output_guard_blocked_view_core,
    build_current_mainline_success_view as build_current_mainline_success_view_core,
    build_current_mainline_user_input_feedback as build_current_mainline_user_input_feedback_core,
)
from note import current_mainline_runtime_logging as runtime_logging_mod
from note.interview_contract_mapper import (
    derive_knowledge_lenses_from_interview as _derive_knowledge_lenses_from_interview_shared,
    normalize_interview_list_value as _normalize_interview_list_value_shared,
    normalize_narrative_axis_from_interview as _normalize_narrative_axis_from_interview_shared,
    normalize_topic_statement_from_interview as _normalize_topic_statement_from_interview_shared,
)
from note.vnext_adapters.legacy_helper_adapter import LegacyHelperAdapter
from note.published_post_inventory import (
    load_published_post_candidates,
)
from note.omakase_seed_builder import (
    omakase_available as _omakase_inventory_available,
)
from note.note_writer_app_head_assets import (
    register_note_writer_app_base_head_html,
    register_note_writer_app_colors,
    register_note_writer_app_sticky_step_head_html,
)
from note.note_writer_app_source_helpers import (
    build_recent_uploaded_source_drafts,
    copy_local_pdf_to_uploads,
    extract_upload_payload,
    prepare_source_add,
    remove_source_by_id,
    remove_upload_paths,
    save_uploaded_payload,
    select_stale_upload_paths,
)
from note.note_writer_app_subviews import (
    CustomGenreEditPayload,
    build_copy_to_clipboard_script,
    build_scroll_to_anchor_script,
    open_custom_genre_delete_dialog,
    open_custom_genre_edit_dialog,
    open_privacy_blur_dialog_view,
    privacy_blur_targets_selected,
    render_custom_genres_subview,
    render_generated_images_subview,
    render_sources_subview,
    resolve_privacy_option_key,
)
from note.note_writer_app_manual_legal_helpers import (
    build_manual_legal_apply_payload,
    build_manual_legal_check_request,
    build_manual_legal_result_view,
    collect_current_legal_verified_texts,
)
from note.note_writer_app_main_page_sections import (
    build_article_type_descriptions,
    render_brand_header,
    render_journey_flow_sections,
    render_required_input_fields,
    render_result_output_sections,
    render_source_mode_choice_cards,
    render_step_track,
)
from shared.usage.nicegui import consume_usage_for_current_user, get_usage_summary_for_current_user

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
STATIC_DIR = Path(__file__).resolve().parent / "static"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT_DIR = Path(__file__).resolve().parents[2]
LATEST_GENERATION_TEXT_PATH = PROJECT_ROOT_DIR / "logs" / "latest_generation_output.txt"
LATEST_GENERATION_JSON_PATH = PROJECT_ROOT_DIR / "logs" / "latest_generation_output.json"
LATEST_GENERATION_QUALITY_REPORT_PATH = PROJECT_ROOT_DIR / "logs" / "latest_generation_quality_report.json"
# 既存運用との互換のため、workspace直下 logs にもミラーを残す。
LATEST_GENERATION_TEXT_PATH_WORKSPACE = WORKSPACE_ROOT_DIR / "logs" / "latest_generation_output.txt"
LATEST_GENERATION_JSON_PATH_WORKSPACE = WORKSPACE_ROOT_DIR / "logs" / "latest_generation_output.json"
LATEST_GENERATION_QUALITY_REPORT_PATH_WORKSPACE = WORKSPACE_ROOT_DIR / "logs" / "latest_generation_quality_report.json"
GENERATION_AUDIT_JSONL_PATH = PROJECT_ROOT_DIR / "logs" / "generation_audit_log.jsonl"
GENERATION_AUDIT_JSONL_PATH_WORKSPACE = WORKSPACE_ROOT_DIR / "logs" / "generation_audit_log.jsonl"

# Hub URL (top page) — _safe_url / _sanitize_href_allow_file は note_text_format_helpers に分離済み。
HUB_URL = _safe_url(os.environ.get("HUB_URL", "https://app.techie.jp"))
KOTOMAKE_URL = _safe_url(os.environ.get("KOTOMAKE_URL", "https://kotomake.ashymushroom-021a53c5.japanwest.azurecontainerapps.io"))
KOTOMIGAKI_URL = _safe_url(os.environ.get("KOTOMIGAKI_URL", "https://kotomigaki.ashymushroom-021a53c5.japanwest.azurecontainerapps.io"))
KOTOMEGANE_URL = _safe_url(os.environ.get("KOTOMEGANE_URL", "https://kotomegane.ashymushroom-021a53c5.japanwest.azurecontainerapps.io"))

# Allow only the tags/attrs we use in ui.html
HTML_SANITIZER = Sanitizer({
    "tags": {"nav", "a", "span", "img"},
    "attributes": {
        "a": ("href", "class"),
        "nav": ("class",),
        "span": ("class",),
        "img": ("src", "alt", "class"),
    },
    "empty": {"img"},
    "separate": {"a", "span", "nav", "img"},
    "sanitize_href": _sanitize_href_allow_file,
})

# 静的ファイル配信（favicon等）
app.add_static_files("/static", str(STATIC_DIR))
logger = logging.getLogger(__name__)


@dataclass
class SourceItem:
    id: str
    label: str
    value: str
    source_type: str
    blur_applied: bool = False


@dataclass
class AppState:
    sources: List[SourceItem] = field(default_factory=list)
    busy: bool = False
    result: Optional[dict] = None
    generated_images: List[str] = field(default_factory=list)
    generated_image_variants: List[Dict[str, Any]] = field(default_factory=list)
    image_generation_status: str = ""
    interview_answers: Dict[str, Any] = field(default_factory=dict)
    interview_questions_loaded: bool = False
    interview_context_signature: str = ""
    question_generation_owner: str = ""
    ambiguity_signature: str = ""
    ambiguity_resolutions: Dict[str, str] = field(default_factory=dict)
    blocked_403_urls: List[str] = field(default_factory=list)
    pdf_assist_candidates: List[str] = field(default_factory=list)
    pdf_assist_status: str = ""
    pdf_assist_since_ts: float = 0.0
    journey_confirmation_signature: str = ""
    journey_preview: Dict[str, Any] = field(default_factory=dict)
    step_refresh_callback: Optional[Callable[[], None]] = None
    source_session_article_type: str = ""
    source_session_signature: str = ""
    source_session_review_required: bool = False
    source_session_review_reason: str = ""
    source_session_restored: bool = False


_CLIENT_SCOPE_DEFAULT = "__global__"
_CLIENT_STATES: Dict[str, AppState] = {}
_CLIENT_HELPERS: Dict[str, LegacyHelperAdapter] = {}
_CLIENT_PIPELINES: Dict[str, MinimalPipeline] = {}
_CLIENT_TIMERS: Dict[str, List[Any]] = {}
_CLIENT_ACTIVE_KEYS: Set[str] = set()
_CLIENT_GENERATION_TOKENS: Dict[str, str] = {}
_COMMITTED_SOURCE_INVENTORY_SNAPSHOT: List[SourceItem] = []
_COMMITTED_SOURCE_SESSION_SNAPSHOT: Dict[str, Any] = {}
_DETACHED_NICEGUI_ERROR_TEXTS = (
    "The client this element belongs to has been deleted.",
    "The parent slot of the element has been deleted.",
    "The parent element this slot belongs to has been deleted.",
)


def _new_llm_client() -> LLMClient:
    return LLMClient()


def _current_client_key() -> str:
    try:
        client = ui.context.client
    except Exception:
        client = None
    if client and getattr(client, "id", None):
        return str(client.id)
    return _CLIENT_SCOPE_DEFAULT


def _normalize_client_key(client_key: Optional[str]) -> str:
    return str(client_key or _CLIENT_SCOPE_DEFAULT)


def _clone_source_item(source_item: SourceItem) -> SourceItem:
    return SourceItem(
        id=str(source_item.id),
        label=str(source_item.label),
        value=str(source_item.value),
        source_type=str(source_item.source_type),
        blur_applied=bool(getattr(source_item, "blur_applied", False)),
    )


def _snapshot_committed_source_inventory(
    source_items: Iterable[SourceItem],
    *,
    source_session: Optional[Mapping[str, Any]] = None,
) -> None:
    global _COMMITTED_SOURCE_INVENTORY_SNAPSHOT, _COMMITTED_SOURCE_SESSION_SNAPSHOT
    _COMMITTED_SOURCE_INVENTORY_SNAPSHOT = [
        _clone_source_item(item)
        for item in source_items
        if str(getattr(item, "value", "") or "").strip()
    ]
    if not _COMMITTED_SOURCE_INVENTORY_SNAPSHOT:
        _COMMITTED_SOURCE_SESSION_SNAPSHOT = {}
    elif source_session is not None:
        _COMMITTED_SOURCE_SESSION_SNAPSHOT = dict(source_session)


def _snapshot_current_source_session(
    state_obj: AppState,
    *,
    completed_run: bool = False,
) -> None:
    review_required = bool(getattr(state_obj, "source_session_review_required", False))
    review_reason = str(getattr(state_obj, "source_session_review_reason", "") or "").strip()
    if completed_run and state_obj.sources:
        review_required = True
        review_reason = "completed_previous_run"
    _snapshot_committed_source_inventory(
        state_obj.sources,
        source_session={
            "article_type": str(getattr(state_obj, "source_session_article_type", "") or ""),
            "signature": _source_session_signature(state_obj.sources),
            "review_required": review_required,
            "review_reason": review_reason,
            "restored": bool(getattr(state_obj, "source_session_restored", False)) and not completed_run,
        },
    )


def _source_session_signature(source_items: Iterable[Any]) -> str:
    values = [
        str(getattr(item, "value", "") or "").strip()
        for item in source_items
        if str(getattr(item, "value", "") or "").strip()
    ]
    return "\n".join(values)


def _mark_source_session_review_required(
    state_obj: AppState,
    *,
    reason: str,
) -> None:
    if not state_obj.sources:
        state_obj.source_session_review_required = False
        state_obj.source_session_review_reason = ""
        return
    state_obj.source_session_review_required = True
    state_obj.source_session_review_reason = str(reason or "needs_review").strip() or "needs_review"


def _accept_source_session_for_article_type(
    state_obj: AppState,
    *,
    article_type_key: str,
) -> None:
    state_obj.source_session_article_type = str(article_type_key or "").strip()
    state_obj.source_session_signature = _source_session_signature(state_obj.sources)
    state_obj.source_session_review_required = False
    state_obj.source_session_review_reason = ""
    state_obj.source_session_restored = False
    _snapshot_current_source_session(state_obj)


def _clear_source_session_sources(state_obj: AppState) -> int:
    removed_count = len(state_obj.sources)
    state_obj.sources = []
    state_obj.source_session_article_type = ""
    state_obj.source_session_signature = ""
    state_obj.source_session_review_required = False
    state_obj.source_session_review_reason = ""
    state_obj.source_session_restored = False
    _snapshot_committed_source_inventory([])
    return removed_count


def _build_source_session_review_state(
    state_obj: AppState,
    *,
    article_type_key: str,
) -> Dict[str, Any]:
    source_count = len([item for item in state_obj.sources if str(getattr(item, "value", "") or "").strip()])
    current_article_type = str(article_type_key or "").strip()
    previous_article_type = str(getattr(state_obj, "source_session_article_type", "") or "").strip()
    current_signature = _source_session_signature(state_obj.sources)
    previous_signature = str(getattr(state_obj, "source_session_signature", "") or "").strip()
    reason = str(getattr(state_obj, "source_session_review_reason", "") or "").strip()
    requires_review = bool(getattr(state_obj, "source_session_review_required", False) and source_count > 0)
    if source_count > 0 and bool(getattr(state_obj, "source_session_restored", False)):
        requires_review = True
        reason = reason or "restored_previous"
    if (
        source_count > 0
        and previous_article_type
        and current_article_type
        and previous_article_type != current_article_type
    ):
        requires_review = True
        reason = "article_type_changed"
    if source_count > 0 and previous_signature and previous_signature != current_signature:
        requires_review = True
        reason = reason or "source_changed_after_accept"
    if not source_count:
        requires_review = False
        reason = ""
    status_text = ""
    hint_text = ""
    if requires_review:
        status_text = f"前回の資料が{source_count}件残っています。使う資料を確認してください。"
        hint_text = "この資料を使うか、新しく始めるかを選ぶまで生成は始まりません。"
    elif source_count > 0:
        status_text = f"追加済みの資料が{source_count}件あります。"
        hint_text = "別の記事を作るときは、新しく始めるを選ぶと資料をクリアできます。"
    return {
        "requires_review": requires_review,
        "reason": reason,
        "source_count": source_count,
        "status_text": status_text,
        "hint_text": hint_text,
        "previous_article_type": previous_article_type,
        "current_article_type": current_article_type,
    }


def _sync_source_session_acceptance_for_fresh_confirmation(
    state_obj: AppState,
    *,
    article_type_key: str,
    current_journey_signature: str,
    confirmed_journey_signature: str,
) -> bool:
    current_article_type = str(article_type_key or "").strip()
    if not current_article_type:
        return False
    if bool(getattr(state_obj, "source_session_restored", False)):
        return False
    if bool(getattr(state_obj, "source_session_review_required", False)):
        return False
    accepted_article_type = str(getattr(state_obj, "source_session_article_type", "") or "").strip()
    accepted_signature = str(getattr(state_obj, "source_session_signature", "") or "").strip()
    current_source_signature = _source_session_signature(state_obj.sources)
    if not accepted_signature or not current_source_signature:
        return False
    if accepted_signature != current_source_signature:
        return False
    confirmation_state = _build_journey_generation_confirmation_state(
        current_signature=current_journey_signature,
        confirmed_signature=confirmed_journey_signature,
    )
    if not bool(confirmation_state.get("ready")):
        return False
    if accepted_article_type and accepted_article_type == current_article_type:
        return False
    _accept_source_session_for_article_type(state_obj, article_type_key=current_article_type)
    return True


def _source_session_confirmation_article_type_key(
    *,
    current_selection: Mapping[str, Any],
    preview: Mapping[str, Any],
) -> str:
    return str(current_selection.get("article_type") or preview.get("article_type") or "").strip()


def _source_session_article_type_for_review(
    selection: Mapping[str, Any],
    *,
    journey_target_committed: bool,
) -> str:
    if not journey_target_committed:
        return ""
    return str(selection.get("article_type") or "").strip()


def _build_source_session_cta_notice_state(
    review_state: Mapping[str, Any],
) -> Dict[str, Any]:
    source_count = int(review_state.get("source_count") or 0)
    visible = bool(review_state.get("requires_review")) and source_count > 0
    return {
        "visible": visible,
        "title_text": str(review_state.get("status_text") or "") if visible else "",
        "hint_text": str(review_state.get("hint_text") or "") if visible else "",
        "keep_button_text": "この資料を使う",
        "reset_button_text": "新しく始める",
    }


def _restore_committed_source_inventory_if_empty(state_obj: AppState) -> int:
    if state_obj.sources or not _COMMITTED_SOURCE_INVENTORY_SNAPSHOT:
        return 0
    state_obj.sources = [_clone_source_item(item) for item in _COMMITTED_SOURCE_INVENTORY_SNAPSHOT]
    snapshot = dict(_COMMITTED_SOURCE_SESSION_SNAPSHOT)
    if snapshot:
        state_obj.source_session_article_type = str(snapshot.get("article_type") or "")
        state_obj.source_session_signature = str(snapshot.get("signature") or _source_session_signature(state_obj.sources))
        state_obj.source_session_review_required = bool(snapshot.get("review_required", True))
        state_obj.source_session_review_reason = str(snapshot.get("review_reason") or "")
        state_obj.source_session_restored = bool(snapshot.get("restored", False))
        if state_obj.source_session_review_required and not state_obj.source_session_review_reason:
            state_obj.source_session_review_reason = "restored_previous"
    else:
        state_obj.source_session_restored = True
        _mark_source_session_review_required(state_obj, reason="restored_previous")
    return len(state_obj.sources)


def _get_or_create_state(client_key: Optional[str] = None) -> AppState:
    key = _normalize_client_key(client_key or _current_client_key())
    state_obj = _CLIENT_STATES.get(key)
    if state_obj is None:
        state_obj = AppState()
        restored_count = _restore_committed_source_inventory_if_empty(state_obj)
        _CLIENT_STATES[key] = state_obj
        if restored_count:
            logger.info("Restored committed source inventory: client_key=%s source_count=%s", key, restored_count)
    return state_obj


def _get_or_create_generator(client_key: Optional[str] = None) -> LegacyHelperAdapter:
    key = _normalize_client_key(client_key or _current_client_key())
    gen_obj = _CLIENT_HELPERS.get(key)
    if gen_obj is None:
        # UI retains only helper flows here. note本文の本流生成は
        # MinimalPipeline(simple_note_pipeline) に固定する。
        gen_obj = LegacyHelperAdapter(llm_client=_new_llm_client())
        _CLIENT_HELPERS[key] = gen_obj
    return gen_obj


def _get_or_create_current_mainline_pipeline(client_key: Optional[str] = None) -> MinimalPipeline:
    key = _normalize_client_key(client_key or _current_client_key())
    pipeline_obj = _CLIENT_PIPELINES.get(key)
    if pipeline_obj is None:
        pipeline_obj = MinimalPipeline(llm_client=_new_llm_client())
        _CLIENT_PIPELINES[key] = pipeline_obj
    return pipeline_obj


def _deactivate_client_timers(client_key: str) -> None:
    key = _normalize_client_key(client_key)
    timers = _CLIENT_TIMERS.pop(key, [])
    for timer_obj in timers:
        try:
            timer_obj.deactivate()
        except Exception:
            continue


def _register_client_timer(client_key: str, timer_obj: Any) -> Any:
    key = _normalize_client_key(client_key)
    _CLIENT_TIMERS.setdefault(key, []).append(timer_obj)
    return timer_obj


def _activate_client_scope(client_key: str) -> None:
    key = _normalize_client_key(client_key)
    _CLIENT_ACTIVE_KEYS.add(key)
    _CLIENT_GENERATION_TOKENS.pop(key, None)


def _release_client_scope(client_key: str) -> None:
    key = _normalize_client_key(client_key)
    _deactivate_client_timers(key)
    _CLIENT_ACTIVE_KEYS.discard(key)
    _CLIENT_GENERATION_TOKENS.pop(key, None)
    _CLIENT_STATES.pop(key, None)
    _CLIENT_HELPERS.pop(key, None)
    _CLIENT_PIPELINES.pop(key, None)


def _start_client_generation(client_key: str, generation_token: str) -> str:
    key = _normalize_client_key(client_key)
    token = str(generation_token or _new_operation_id("gen-token"))
    if key in _CLIENT_ACTIVE_KEYS:
        _CLIENT_GENERATION_TOKENS[key] = token
    return token


def _finish_client_generation(client_key: str, generation_token: str) -> None:
    key = _normalize_client_key(client_key)
    if generation_token and _CLIENT_GENERATION_TOKENS.get(key) == generation_token:
        _CLIENT_GENERATION_TOKENS.pop(key, None)


def _is_client_generation_attached(client_key: str, generation_token: str) -> bool:
    key = _normalize_client_key(client_key)
    return bool(generation_token) and key in _CLIENT_ACTIVE_KEYS and _CLIENT_GENERATION_TOKENS.get(key) == generation_token


def _is_detached_nicegui_error(exc: BaseException) -> bool:
    message = str(exc)
    return any(fragment in message for fragment in _DETACHED_NICEGUI_ERROR_TEXTS)


def _run_attached_ui_mutation(
    *,
    client_key: str,
    generation_token: str,
    mutation: Callable[[], None],
    action_name: str = "ui_mutation",
) -> bool:
    if not _is_client_generation_attached(client_key, generation_token):
        return False
    try:
        mutation()
        return True
    except RuntimeError as exc:
        if _is_detached_nicegui_error(exc):
            logger.info(
                "Skipped stale UI mutation after client detach client_key=%s action=%s",
                _normalize_client_key(client_key),
                action_name,
            )
            _release_client_scope(client_key)
            return False
        raise


class _StateProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(_get_or_create_state(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(_get_or_create_state(), name, value)


class _GeneratorProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(_get_or_create_generator(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(_get_or_create_generator(), name, value)


fetcher = ArticleFetcher()
state = _StateProxy()
generator = _GeneratorProxy()
LEGAL_POSTCHECK_AUTO_ENABLED = os.environ.get("LEGAL_POSTCHECK_AUTO_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Genre management state
genre_optimize_busy = False
pending_genre: Optional[dict] = None

BASE_TEMPLATE_LABELS = {
    "branding": "branding",
    "ai": "ai",
    "announcement": "announcement",
    "case_study": "case_study",
}
FOCUS_DEFAULT_LABELS = {
    "analysis": "analysis",
    "explanation": "explanation",
    "experience": "experience",
}
LEVEL_LABELS = {"low": "low", "med": "med", "high": "high"}
EVIDENCE_LABELS = {"strict": "strict", "normal": "normal"}
SLOW_SOURCE_COUNT_THRESHOLD = 5
SLOW_TOTAL_CHARS_THRESHOLD = 18000
SOURCE_READING_CONFIG = get_source_reading_config()
SOURCE_MAX_CHARS_PER_SOURCE = int(SOURCE_READING_CONFIG.get("max_chars_per_source", 12000) or 12000)
ENABLE_LIVE_DRAFT_STREAM = False
FIXED_ARTICLE_TYPE_LABELS = {
    "explanatory_article": "解説・ノウハウ",
    "daily_story": "日常のできごと",
    "branding": "紹介",
    "announcement": "お知らせ",
    "case_study": "事例・お客様の声",
    "industry_analysis": "業界・市場の話題",
    "comparative_review": "比較・選び方",
}

ARTICLE_TYPE_PRIORITY_KEYS = [
    "explanatory_article",
    "daily_story",
    "branding",
    "announcement",
    "case_study",
    "industry_analysis",
    "comparative_review",
]
TONE_PROFILE_LABELS = {
    "auto": "記事に合わせて自然に書く",
    "calm": "落ち着いて解説する",
    "warm": "やさしく寄り添う",
    "passionate": "熱意をもって伝える",
    "formal": "端正にまとめる",
}
CONTENT_GOAL_LABELS = {
    "auto": "自動（おすすめ）",
    "interest": "興味を惹く（読了率重視）",
    "explain": "説明したい（理解重視）",
    "action": "行動を促したい（CTA重視）",
    "trust": "信頼を高めたい（根拠重視）",
}
WRITING_FOCUS_LABELS = {
    "auto": "自動（おすすめ）",
    "explanation": "解説メイン（わかりやすさ重視）",
    "experience": "経験メイン（体験・感情重視）",
    "analysis": "分析メイン（根拠・比較重視）",
}
LENGTH_MODE_LABELS = {
    "adaptive": "自動（ソースに合わせる）",
    "short": "短め（お知らせ向け）",
    "normal": "普通（固定）",
    "long": "長め（深掘り）",
}
SOURCE_MODE_LABELS = {
    "grounded": "資料あり",
    "web": "お任せ",
    "prompt_only": "プロンプトのみ",
}
_PROMPT_ONLY_ALLOWED_ARTICLE_TYPES = {"daily_story"}
_SOURCE_MODE_INPUT_REQUIRED_MODES = {"grounded"}
_OMAKASE_STATUS_LABELS = {
    "READY": "このまま始められます",
    "AUTO_SOURCE_READY": "必要な材料を先に集めます",
    "NEEDS_INPUT": "テーマを1行入れてください",
    "OMAKASE_FALLBACK": "まだお任せで始められません",
}
SELF_REFERENCE_POLICY_LABELS = {
    "auto": "自動（おすすめ）",
    "watashi": "私",
    "watashitachi": "私たち",
    "tousha": "当社",
    "heisha": "弊社",
    "minimal": "一人称をなるべく使わない",
}
CURRENT_MAINLINE_STRICT_SAAS_MODE = UI_DEFAULT_STRICT_SAAS_MODE
CURRENT_MAINLINE_UI_MODE = (os.environ.get("CURRENT_MAINLINE_UI_MODE", "journey") or "journey").strip().lower()
WRITER_ROLE_AUTO_LABEL = "自動（おすすめ）"
WRITER_ROLE_COMPANY_INTRO_NEUTRAL_LABEL = "立場を前に出さない（おすすめ）"
ARTICLE_TYPE_HANDOFF_DEFAULTS: Dict[str, Dict[str, str]] = {
    "explanatory_article": {
        "writer_role": "自社の知見を持つ解説担当として語る",
        "perspective": "expert",
        "writing_focus": "explanation",
        "self_reference_policy": "watashitachi",
    },
    "industry_analysis": {
        "writer_role": "自社の観察を整理する分析担当として語る",
        "perspective": "expert",
        "writing_focus": "analysis",
        "self_reference_policy": "watashitachi",
    },
    "comparative_review": {
        "writer_role": "自社の知見を持つ編集担当として語る",
        "perspective": "expert",
        "writing_focus": "analysis",
        "self_reference_policy": "watashitachi",
    },
    "branding": {
        "writer_role": "自社の企業担当者として語る",
        "perspective": "corporate",
        "writing_focus": "explanation",
        "self_reference_policy": "watashitachi",
    },
    "announcement": {
        "writer_role": "運営担当として語る",
        "perspective": "corporate",
        "writing_focus": "explanation",
        "self_reference_policy": "watashitachi",
    },
    "case_study": {
        "writer_role": "導入支援担当として語る",
        "perspective": "corporate",
        "writing_focus": "explanation",
        "self_reference_policy": "watashitachi",
    },
    "daily_story": {
        "writer_role": "現場担当として語る",
        "perspective": "blogger",
        "writing_focus": "experience",
        "self_reference_policy": "watashitachi",
    },
    "default": {
        "writer_role": "編集担当として語る",
        "perspective": "expert",
        "writing_focus": "explanation",
        "self_reference_policy": "watashitachi",
    },
}
SEMANTIC_ARTICLE_HANDOFF_DEFAULTS: Dict[str, Dict[str, str]] = {
    "announcement": {
        "writer_role": "運営担当として語る",
        "perspective": "corporate",
        "writing_focus": "explanation",
        "self_reference_policy": "watashitachi",
    },
    "company_introduction": {
        "writer_role": "自社の企業担当者として語る",
        "perspective": "corporate",
        "writing_focus": "explanation",
        "self_reference_policy": "watashitachi",
    },
    "product_introduction": {
        "writer_role": "提供担当として語る",
        "perspective": "corporate",
        "writing_focus": "explanation",
        "self_reference_policy": "watashitachi",
    },
    "daily_story": {
        "writer_role": "現場担当として語る",
        "perspective": "blogger",
        "writing_focus": "experience",
        "self_reference_policy": "watashitachi",
    },
}
WRITER_ROLE_OPTIONS_BY_ARTICLE_TYPE: Dict[str, List[str]] = {
    "explanatory_article": [
        WRITER_ROLE_AUTO_LABEL,
        "編集担当として語る",
        "解説担当として語る",
        "専門家として語る",
    ],
    "industry_analysis": [
        WRITER_ROLE_AUTO_LABEL,
        "編集担当として語る",
        "アナリストとして語る",
        "専門家として語る",
    ],
    "comparative_review": [
        WRITER_ROLE_AUTO_LABEL,
        "自社の知見を持つ編集担当として語る",
        "編集担当として語る",
        "比較検証担当として語る",
        "専門家として語る",
    ],
    "branding": [
        WRITER_ROLE_AUTO_LABEL,
        "自社の企業担当者として語る",
        "企業広報として語る",
        "ブランド担当として語る",
        "導入支援担当として語る",
    ],
    "announcement": [
        WRITER_ROLE_AUTO_LABEL,
        "運営担当として語る",
        "広報担当として語る",
        "編集担当として語る",
    ],
    "case_study": [
        WRITER_ROLE_AUTO_LABEL,
        "導入支援担当として語る",
        "運営担当として語る",
        "編集担当として語る",
    ],
    "daily_story": [
        WRITER_ROLE_AUTO_LABEL,
        "運営担当として語る",
        "現場担当として語る",
        "編集担当として語る",
    ],
    "default": [
        WRITER_ROLE_AUTO_LABEL,
        "編集担当として語る",
        "運営担当として語る",
        "専門家として語る",
    ],
}
WRITER_ROLE_OPTIONS_BY_SEMANTIC_KEY: Dict[str, List[str]] = {
    "announcement": [
        WRITER_ROLE_AUTO_LABEL,
        "運営担当として語る",
        "編集担当として語る",
    ],
    "company_introduction": [
        "自社の企業担当者として語る",
        WRITER_ROLE_COMPANY_INTRO_NEUTRAL_LABEL,
        "企業広報として語る",
    ],
    "daily_story": [
        WRITER_ROLE_AUTO_LABEL,
        "現場担当として語る",
        "編集担当として語る",
    ],
    "product_introduction": [
        WRITER_ROLE_AUTO_LABEL,
        "ブランド担当として語る",
        "導入支援担当として語る",
    ],
}
WRITER_ROLE_DEFAULT_BY_SEMANTIC_KEY: Dict[str, str] = {
    "announcement": "運営担当として語る",
    "company_introduction": "自社の企業担当者として語る",
    "daily_story": "現場担当として語る",
    "product_introduction": "ブランド担当として語る",
}
WRITER_ROLE_ARTICLE_TYPE_MANAGED_DEFAULT_LABELS: Set[str] = {
    str(defaults.get("writer_role") or "").strip()
    for defaults in (
        list(ARTICLE_TYPE_HANDOFF_DEFAULTS.values())
        + list(SEMANTIC_ARTICLE_HANDOFF_DEFAULTS.values())
    )
    if str(defaults.get("writer_role") or "").strip()
} | set(WRITER_ROLE_DEFAULT_BY_SEMANTIC_KEY.values()) | {"企業担当者として語る"}
_THEME_LIKE_WRITER_ROLE_PATTERN = re.compile(
    r"(活用法|方法|とは|について|比較|ポイント|戦略|課題|テーマ|読者|するため|を維持|を高め|目的|記事構成)"
)
_CORPORATE_WRITER_ROLE_PATTERN = re.compile(
    r"(広報|運営|導入支援|ブランド|会社|企業|当社|弊社|代表|取締役|経営|人事|カルチャー)"
)
_PERSONAL_WRITER_ROLE_PATTERN = re.compile(
    r"(編集|筆者|解説|専門家|講師|記者|アナリスト|コンサル|監修|現場)"
)
JOURNEY_PURPOSE_LABELS = {
    "explain": "解説・市場を伝える",
    "introduce": "会社・サービスの紹介記事を書く",
    "announce": "お知らせを伝える",
    "case": "事例・お客様の声を伝える",
    "compare": "比較・選び方を整理する",
    "daily": "日常のできごとを伝える",
}
JOURNEY_TARGET_LABELS = {
    "explain": {
        "concept": "解説・ノウハウ",
        "industry": "業界・市場の話題",
    },
    "introduce": {
        "company": "自社・会社紹介",
        "product_service": "商品・サービス紹介記事",
    },
    "announce": {
        "standard": "お知らせ",
    },
    "case": {
        "implementation": "事例・お客様の声",
    },
    "compare": {
        "tool_service": "比較・選び方",
    },
    "daily": {
        "day_to_day": "日常のできごと",
    },
}
JOURNEY_TARGET_LABELS_ALL = {
    **JOURNEY_TARGET_LABELS,
    "introduce": {
        **JOURNEY_TARGET_LABELS["introduce"],
        "activity_project": "活動・プロジェクト紹介記事",
        "recruit_culture": "採用・カルチャー紹介記事",
    },
    "case": {
        **JOURNEY_TARGET_LABELS["case"],
        "improvement": "改善事例",
        "incident": "事故・障害・インシデント",
        "learning": "学習用ケーススタディ",
    },
    "compare": {
        **JOURNEY_TARGET_LABELS["compare"],
        "method": "方法・進め方の比較",
        "vendor": "会社・ベンダー比較",
    },
    "daily": {
        **JOURNEY_TARGET_LABELS["daily"],
        "behind_the_scenes": "舞台裏・裏側",
    },
}
JOURNEY_COMPARE_AXIS_OPTIONS = {
    "price": "価格",
    "performance": "性能",
    "use_case": "用途",
    "safety": "安全性",
    "overall": "総合",
}
JOURNEY_COMPARE_GOAL_LABELS = {
    "fit_explain": "条件別に選び分ける",
    "organize": "違いを整理する",
    "prioritize": "優先順位をつける",
}
SEMANTIC_ARTICLE_KEY_LABELS = {
    "explanatory_article": "解説・ノウハウ",
    "industry_analysis": "業界・市場の話題",
    "company_introduction": "会社紹介",
    "product_introduction": "商品・サービス紹介記事",
    "activity_introduction": "活動・プロジェクト紹介記事",
    "recruit_culture": "採用・カルチャー紹介記事",
    "announcement": "お知らせ",
    "implementation_case": "事例・お客様の声",
    "improvement_case": "改善事例",
    "incident_case": "事故・障害・インシデント",
    "learning_case": "学習用ケーススタディ",
    "comparative_review": "比較・選び方",
    "daily_story": "日常のできごと",
    "branding": "紹介",
    "case_study": "事例・お客様の声",
}

def _order_article_type_keys(keys: List[str]) -> List[str]:
    priority = {key: idx for idx, key in enumerate(ARTICLE_TYPE_PRIORITY_KEYS)}
    return sorted(keys, key=lambda key: (priority.get(key, 999), key))


def _get_combined_article_types() -> dict:
    """Get article type labels for current UI mode."""
    combined = dict(FIXED_ARTICLE_TYPE_LABELS)
    ordered_keys = _order_article_type_keys(list(combined.keys()))
    return {key: combined[key] for key in ordered_keys}


def _get_combined_prompts() -> dict:
    """Get prompt catalog keys used for UI validation."""
    combined = {key: f"fixed:{key}" for key in FIXED_ARTICLE_TYPE_LABELS}
    ordered_keys = _order_article_type_keys(list(combined.keys()))
    return {key: combined[key] for key in ordered_keys}


def _get_journey_target_options(purpose_key: str) -> Dict[str, str]:
    return dict(JOURNEY_TARGET_LABELS.get(str(purpose_key or "").strip(), {}))


def _normalize_journey_target_selection(purpose_key: str, selected_label: Any) -> Dict[str, Any]:
    normalized_purpose = str(purpose_key or "").strip()
    options = _get_journey_target_options(normalized_purpose)
    option_labels = list(options.values())
    selected_text = str(selected_label or "").strip()
    target_key = next((key for key, label in options.items() if label == selected_text), "")
    target_label = selected_text
    if not target_key and options:
        target_key, target_label = next(iter(options.items()))
    return {
        "purpose_key": normalized_purpose,
        "target_key": target_key,
        "target_label": target_label,
        "option_labels": option_labels,
    }


def _get_journey_compare_axis_labels(axis_keys: List[str]) -> List[str]:
    labels: List[str] = []
    for key in axis_keys:
        label = JOURNEY_COMPARE_AXIS_OPTIONS.get(str(key or "").strip(), str(key or "").strip())
        if label and label not in labels:
            labels.append(label)
    return labels


def _label_for_compare_goal_key(goal_key: str) -> str:
    key = str(goal_key or "").strip()
    return JOURNEY_COMPARE_GOAL_LABELS.get(key, key)


def _label_for_semantic_article_key(semantic_key: str) -> str:
    key = str(semantic_key or "").strip()
    return SEMANTIC_ARTICLE_KEY_LABELS.get(key, key)


def _is_prompt_only_allowed_article_type(article_type_key: str) -> bool:
    return str(article_type_key or "").strip().lower() in _PROMPT_ONLY_ALLOWED_ARTICLE_TYPES


def _past_blog_prompt_unlock_available(published_post_candidates: Any = None) -> bool:
    return bool(_omakase_inventory_available(list(published_post_candidates or [])))


def _prompt_only_ui_unlocked(
    *,
    article_type_key: str,
    past_blog_unlocked: bool = False,
) -> bool:
    return bool(
        _is_prompt_only_allowed_article_type(article_type_key)
        and bool(past_blog_unlocked)
    )


def _source_mode_options_for_article_type(
    article_type_key: str,
    *,
    past_blog_unlocked: bool = False,
) -> Dict[str, str]:
    options = {
        key: label
        for key, label in SOURCE_MODE_LABELS.items()
        if key != "prompt_only"
        or _prompt_only_ui_unlocked(
            article_type_key=article_type_key,
            past_blog_unlocked=past_blog_unlocked,
        )
    }
    return options or {"grounded": SOURCE_MODE_LABELS["grounded"]}


def _source_mode_allows_no_sources(
    *,
    article_type_key: str,
    source_mode_key: str,
    prompt_raw: str = "",
    past_blog_unlocked: bool = False,
) -> bool:
    return bool(
        _prompt_only_ui_unlocked(
            article_type_key=article_type_key,
            past_blog_unlocked=past_blog_unlocked,
        )
        and str(source_mode_key or "").strip().lower() == "prompt_only"
        and str(prompt_raw or "").strip()
    )


def _resolve_source_mode_selection(selected_label: Any) -> Dict[str, Any]:
    selected_text = str(selected_label or "").strip()
    source_mode_key = next(
        (key for key, label in SOURCE_MODE_LABELS.items() if label == selected_text),
        "grounded",
    )
    return {
        "source_mode_key": source_mode_key,
        "source_mode_label": SOURCE_MODE_LABELS[source_mode_key],
        "requires_source_inputs": source_mode_key == "grounded",
        "uses_web_research": source_mode_key == "web",
    }


def _build_source_mode_helper_text(
    *,
    article_type_key: str,
    source_mode_key: str,
    past_blog_unlocked: bool = False,
) -> str:
    normalized_article_type = str(article_type_key or "").strip()
    normalized_source_mode = str(source_mode_key or "").strip() or "grounded"
    if normalized_source_mode == "grounded":
        return "資料ありで始めます。先に URL / PDF / 画像 / テキストを追加し、その内容を土台に記事を組み立てます。1行テーマは使いません。"
    if normalized_source_mode == "prompt_only":
        if not _is_prompt_only_allowed_article_type(normalized_article_type):
            return "プロンプトのみは日常のできごとの記事だけで使えます。"
        if not past_blog_unlocked:
            return "プロンプトのみは、公開済みブログの蓄積条件を満たした日常のできごとだけで使えます。"
        return "プロンプトのみで始めます。1行テーマを体験メモとして使い、公開済みブログは書き味と関心領域の参考に限定します。統計・価格・法律・医療・金融・比較優位・会社実績は足しません。"
    if normalized_article_type in {"branding", "announcement", "case_study", "comparative_review"}:
        return "この種類は資料ありで進めます。先に資料をそろえると次に進めます。"
    if not past_blog_unlocked:
        return "お任せは公開済みブログの蓄積条件を満たすまで選べません。いまは資料ありで進めてください。"
    return "お任せで始めます。1行テーマと公開済みブログの蓄積がそろうと、生成前に外部ソースの材料集めへ進みます。公開済みブログ本文は今回の記事の事実ソースには使いません。"


def _build_source_mode_input_surface(
    *,
    article_type_key: str,
    source_mode_key: str,
    past_blog_unlocked: bool = False,
) -> Dict[str, Any]:
    normalized_source_mode = str(source_mode_key or "").strip().lower() or "grounded"
    helper_text = _build_source_mode_helper_text(
        article_type_key=article_type_key,
        source_mode_key=normalized_source_mode,
        past_blog_unlocked=past_blog_unlocked,
    )
    if normalized_source_mode == "grounded":
        return {
            "section_intro_text": "資料ありでは、先に材料をそろえます。URL / PDF / 画像 / テキストを追加すると、生成前チェックへ進めます。",
            "source_mode_helper_text": helper_text,
            "prompt_visible": False,
            "prompt_label": "",
            "prompt_placeholder": "",
            "prompt_helper_text": "",
            "source_title_text": "先にそろえる資料",
            "source_helper_text": "資料ありではここが開始条件です。URL / PDF / 画像 / テキストを1件以上追加してください。入力済みの方針や読者は保持します。",
        }
    if normalized_source_mode == "prompt_only":
        return {
            "section_intro_text": "公開済みブログの蓄積条件を満たした日常のできごとだけ、1行テーマから始められます。テーマは体験メモであり、外部事実の根拠にはしません。",
            "source_mode_helper_text": helper_text,
            "prompt_visible": bool(past_blog_unlocked),
            "prompt_label": "1行テーマ",
            "prompt_placeholder": "例: 夕方の打ち合わせで、言葉の受け取り方が少しズレた話",
            "prompt_helper_text": "起きた場面や引っかかりを短く入れます。公開済みブログは書き味の参考であり、今回記事の事実ソースではありません。",
            "source_title_text": "資料入力",
            "source_helper_text": "プロンプトのみでは資料を使いません。URL / PDF / 画像 / テキストを使う場合は資料ありへ切り替えます。",
        }
    if not past_blog_unlocked:
        return {
            "section_intro_text": "お任せは、公開済みブログの蓄積条件を満たすまで1行テーマから開始できません。いまは資料ありで材料を追加してください。",
            "source_mode_helper_text": helper_text,
            "prompt_visible": False,
            "prompt_label": "",
            "prompt_placeholder": "",
            "prompt_helper_text": "",
            "source_title_text": "資料入力",
            "source_helper_text": "公開済みブログが不足している場合は、URL / PDF / 画像 / テキストを使う資料ありで進めます。",
        }
    return {
        "section_intro_text": "必須入力を決めたあと、お任せでは1行テーマから始めます。公開済みブログの蓄積が十分なときだけ、外部ソースの材料集めへ進みます。",
        "source_mode_helper_text": helper_text,
        "prompt_visible": True,
        "prompt_label": "1行テーマ",
        "prompt_placeholder": "例: 選ぶ判断材料がすぐ伝わる記事にしたい",
        "prompt_helper_text": "何を書くか・何を重視するかだけを1行で入れます。タイトルは不要です。",
        "source_title_text": "必要に応じて足す資料",
        "source_helper_text": "手元の URL / PDF / 画像 / テキストを使いたい場合は、資料ありへ切り替えます。",
    }


def _build_omakase_surface_state(
    *,
    article_type_key: str,
    prompt_raw: str,
    source_mode_key: str,
    source_values: Iterable[Any] | None = None,
    source_documents: Iterable[Any] | None = None,
    published_post_candidates: Iterable[Any] | None = None,
) -> Dict[str, Any]:
    normalized_source_mode = str(source_mode_key or "").strip().lower()
    if normalized_source_mode != "web":
        return {
            "visible": False,
            "status": "",
            "title": "",
            "message": "",
            "inventory_text": "",
            "detail_text": "",
            "allow_generate": False,
            "preflight": {},
        }
    preflight = build_omakase_preflight(
        requested_article_type=article_type_key,
        user_prompt_text=str(prompt_raw or "").strip(),
        source_values=list(source_values or []),
        source_documents=list(source_documents or []),
        published_post_candidates=list(published_post_candidates or []),
        preferred_source_mode="auto",
        industry_hint="",
    )
    status = str(preflight.get("status") or "").strip()
    existing_count = int(preflight.get("existing_post_count") or 0)
    total_body_chars = int(preflight.get("total_body_chars") or 0)
    min_posts = int(preflight.get("inventory_min_posts") or 0)
    min_total_body_chars = int(preflight.get("inventory_min_total_body_chars") or 0)
    source_count = int(preflight.get("source_count") or 0)
    prompt_is_blank = not bool(str(prompt_raw or "").strip())
    inventory_locked_without_sources = bool(source_count <= 0 and not bool(preflight.get("omakase_available")))
    inventory_locked_without_prompt = bool(inventory_locked_without_sources and prompt_is_blank)
    if inventory_locked_without_sources:
        status = "OMAKASE_FALLBACK"
    fallback_options = [
        str(item.get("label") or "").strip()
        for item in _to_plain_list(preflight.get("fallback_options"))
        if isinstance(item, dict) and str(item.get("label") or "").strip()
    ]
    needs_items = [
        str(item.get("question_template") or "").strip()
        for item in _to_plain_list(preflight.get("needs_input_items"))
        if isinstance(item, dict) and str(item.get("question_template") or "").strip()
    ]
    detail_parts: List[str] = []
    if min_posts > 0 and min_total_body_chars > 0:
        detail_parts.append(f"利用条件: 公開済み{min_posts}件以上 / 合計本文{min_total_body_chars}字以上")
    if fallback_options:
        detail_parts.append("代替案: " + " / ".join(fallback_options[:3]))
    if needs_items and not inventory_locked_without_prompt:
        detail_parts.append("追加入力: " + " / ".join(needs_items[:2]))
    if status == "AUTO_SOURCE_READY":
        detail_parts.append("生成を押すと、本生成の前に外部ソースの材料収集可否の確認で止まります。")
    if status == "OMAKASE_FALLBACK" and not str(preflight.get("message") or "").strip():
        detail_parts.append("公開済みブログが不足しているため、1行テーマだけでは開始できません。")
    message_text = (
        "公開済みブログの蓄積が足りないため、お任せはまだ開始しません。資料ありで材料を追加してください。"
        if inventory_locked_without_prompt
        else str(preflight.get("message") or "").strip()
    )
    return {
        "visible": True,
        "status": status,
        "title": _OMAKASE_STATUS_LABELS.get(status, "状況を確認してください"),
        "message": message_text,
        "inventory_text": f"現在の公開済み記事: {existing_count}件 / 合計本文 {total_body_chars}字",
        "detail_text": " ".join(part for part in detail_parts if part).strip(),
        "allow_generate": status == "AUTO_SOURCE_READY",
        "preflight": dict(preflight),
    }


def _load_current_published_post_candidates(*, limit: int = 20) -> List[Dict[str, Any]]:
    return [
        dict(item)
        for item in load_published_post_candidates(limit=limit)
        if isinstance(item, dict)
    ]


def _build_generate_gate_surface(
    *,
    confirmation_ready: bool,
    source_mode_key: str,
    source_count: int,
    article_type_key: str = "",
    prompt_raw: str = "",
    omakase_state: Mapping[str, Any] | None = None,
    past_blog_unlocked: bool = False,
) -> Dict[str, Any]:
    normalized_source_mode = str(source_mode_key or "").strip().lower()
    normalized_omakase_state = dict(omakase_state or {})
    if normalized_source_mode in _SOURCE_MODE_INPUT_REQUIRED_MODES and source_count <= 0:
        return {
            "enabled": False,
            "button_text": "資料を追加する",
            "hint_text": "資料ありでは、URL / PDF / 画像 / テキストを1件以上そろえると進めます。入力済みの内容は保持したまま、資料入力へ戻ってください。",
            "hint_classes": "text-amber-700",
        }
    if normalized_source_mode == "prompt_only":
        if not _is_prompt_only_allowed_article_type(article_type_key):
            return {
                "enabled": False,
                "button_text": "資料ありで進める",
                "hint_text": "プロンプトのみは日常のできごとの記事だけで使えます。資料ありへ切り替えてください。",
                "hint_classes": "text-amber-700",
            }
        if not past_blog_unlocked:
            return {
                "enabled": False,
                "button_text": "資料ありで進める",
                "hint_text": "公開済みブログの蓄積が足りないため、1行テーマだけでは開始できません。資料ありで材料を追加してください。",
                "hint_classes": "text-amber-700",
            }
        if not str(prompt_raw or "").strip():
            return {
                "enabled": False,
                "button_text": "1行テーマを入力する",
                "hint_text": "プロンプトのみでは、まず何が起きたかを1行で入れると進めます。",
                "hint_classes": "text-amber-700",
            }
    omakase_status = str(normalized_omakase_state.get("status") or "").strip()
    if normalized_source_mode == "web":
        if not past_blog_unlocked:
            return {
                "enabled": False,
                "button_text": "資料ありで進める",
                "hint_text": str(
                    normalized_omakase_state.get("detail_text")
                    or normalized_omakase_state.get("message")
                    or "公開済みブログの蓄積が足りないため、お任せはまだ開始できません。資料ありで材料を追加してください。"
                ),
                "hint_classes": "text-amber-700",
            }
        if omakase_status == "NEEDS_INPUT":
            return {
                "enabled": False,
                "button_text": "1行テーマを入力する",
                "hint_text": "お任せでは、まず何について書くかを1行で入れると次に進めます。",
                "hint_classes": "text-amber-700",
            }
        if omakase_status == "OMAKASE_FALLBACK":
            return {
                "enabled": False,
                "button_text": "資料ありで進める",
                "hint_text": str(normalized_omakase_state.get("detail_text") or normalized_omakase_state.get("message") or ""),
                "hint_classes": "text-amber-700",
            }
        if omakase_status == "AUTO_SOURCE_READY":
            return {
                "enabled": True,
                "button_text": "材料集めの確認へ進む",
                "hint_text": "このボタンで材料集めの可否確認へ進みます。本生成はその確認のあとに始まります。",
                "hint_classes": "text-[#5D4A41]",
            }
    if not confirmation_ready:
        return {
            "enabled": False,
            "button_text": "方針を確認する",
            "hint_text": "入力は保持されています。生成前チェックで方針を確認すると、記事生成へ進めます。",
            "hint_classes": "text-amber-700",
        }
    return {
        "enabled": True,
        "button_text": "記事を生成",
        "hint_text": "この内容で記事生成に進めます。",
        "hint_classes": "text-green-700",
    }


_ANNOUNCEMENT_DATE_PATTERN = re.compile(
    r"(20\d{2}[/-年]\s*\d{1,2}[/-月]\s*\d{1,2}日?(?:\s*\d{1,2}:\d{2})?)|"
    r"(\d{1,2}[/-月]\s*\d{1,2}日(?:\s*\d{1,2}:\d{2})?)"
)
_ANNOUNCEMENT_TARGET_HINTS = (
    "対象",
    "利用者",
    "会員",
    "参加者",
    "顧客",
    "ユーザー",
    "お客様",
    "受講者",
    "来場者",
)
_ANNOUNCEMENT_CHANGE_HINTS = (
    "変更",
    "開始",
    "終了",
    "停止",
    "再開",
    "公開",
    "更新",
    "移行",
    "休業",
    "改定",
    "メンテナンス",
    "リリース",
    "延期",
)


def _build_announcement_inline_error(
    *,
    article_type_key: str,
    source_mode_key: str,
    prompt_raw: str,
    source_values: Iterable[Any] | None,
) -> str:
    if str(article_type_key or "").strip() != "announcement":
        return ""
    if str(source_mode_key or "").strip() == "web":
        return "お知らせは資料ベースのみです。日付・対象・変更点が分かる資料を使ってください。"
    combined_text = " ".join(
        part
        for part in [
            str(prompt_raw or "").strip(),
            *[str(item or "").strip() for item in (source_values or []) if str(item or "").strip()],
        ]
        if part
    )
    missing: List[str] = []
    if not _ANNOUNCEMENT_DATE_PATTERN.search(combined_text):
        missing.append("日付")
    if not any(token in combined_text for token in _ANNOUNCEMENT_TARGET_HINTS):
        missing.append("対象")
    if not any(token in combined_text for token in _ANNOUNCEMENT_CHANGE_HINTS):
        missing.append("変更点")
    if not missing:
        return ""
    return f"お知らせは {' / '.join(missing)} を先に入れてください。"


def _describe_note_output_shape(article_type_key: str) -> str:
    key = str(article_type_key or "").strip()
    if key == "announcement":
        return "出力形: リード→本文。案内文として短くまとめ、目次は入れません。"
    if key == "daily_story":
        return "出力形: リード→本文。長くても観察と内省の流れを優先し、目次は入れません。"
    if key in {"branding", "case_study"}:
        return "出力形: 中量は「この記事でわかること」のみ、かなり長い場合だけ目次を足します。"
    return "出力形: 長文では「この記事でわかること」→目次→本文の順に整えます。"


def _get_article_type_key(selected_label: str) -> Optional[str]:
    """Map UI label back to internal article type key (built-in or custom)."""
    combined = _get_combined_article_types()
    if selected_label in combined:
        return selected_label
    return next((k for k, v in combined.items() if v == selected_label), None)


def _resolve_article_type_key_with_fallback(selected_label: str) -> Tuple[str, bool]:
    """Resolve article_type key from UI label with safe fallback."""
    resolved = _get_article_type_key(selected_label)
    if resolved:
        return resolved, False
    combined = _get_combined_article_types()
    fallback_key = next(iter(combined.keys()), "ai")
    return fallback_key, True


def _prefer_explanatory_focus_for_interest(article_type_key: str) -> bool:
    """goal=interest時にexperience偏重を避けるべきカテゴリか判定する。"""
    key = (article_type_key or "").strip()
    if key in {"explanatory_article", "announcement", "industry_analysis", "comparative_review"}:
        return True

    custom_genre = genre_manager.get_genre(key)
    if not isinstance(custom_genre, dict):
        return False
    meta = custom_genre.get("meta")
    if not isinstance(meta, dict) or not meta:
        return False

    base_template = str(meta.get("base_template", "")).strip().lower()
    focus_default = str(meta.get("focus_default", "")).strip().lower()
    evidence_mode = str(meta.get("evidence_mode", "")).strip().lower()
    return (
        base_template == "ai"
        or focus_default in ("analysis", "explanation")
        or evidence_mode == "strict"
    )


def _get_writer_role_options(article_type_key: str, semantic_article_key: str = "") -> List[str]:
    """Return a compact role option set to minimize decision cost."""
    semantic_key = str(semantic_article_key or "").strip()
    semantic_options = WRITER_ROLE_OPTIONS_BY_SEMANTIC_KEY.get(semantic_key)
    if semantic_options:
        options = semantic_options
    else:
        key = _resolve_writer_role_option_key(article_type_key)
        options = WRITER_ROLE_OPTIONS_BY_ARTICLE_TYPE.get(key) or WRITER_ROLE_OPTIONS_BY_ARTICLE_TYPE["default"]
    unique_options: List[str] = []
    for item in options:
        text = str(item or "").strip()
        if not text or text in unique_options:
            continue
        unique_options.append(text)
    return unique_options[:4]


def _get_default_writer_role_label(article_type_key: str, semantic_article_key: str = "") -> str:
    options = _get_writer_role_options(article_type_key, semantic_article_key)
    semantic_default = WRITER_ROLE_DEFAULT_BY_SEMANTIC_KEY.get(str(semantic_article_key or "").strip())
    if semantic_default in options:
        return semantic_default
    for option in options:
        if option != WRITER_ROLE_AUTO_LABEL:
            return option
    return options[0] if options else WRITER_ROLE_AUTO_LABEL


def _is_article_type_managed_writer_role_label(label: str) -> bool:
    text = str(label or "").strip()
    return bool(text and text in WRITER_ROLE_ARTICLE_TYPE_MANAGED_DEFAULT_LABELS)


def _writer_role_label_to_profile(label: str) -> str:
    text = str(label or "").strip()
    if not text or text in {WRITER_ROLE_AUTO_LABEL, WRITER_ROLE_COMPANY_INTRO_NEUTRAL_LABEL}:
        return ""
    return text[:80]


def _build_core_message_placeholder(
    article_type_key: str,
    semantic_article_key: str = "",
    content_goal_key: str = "",
) -> str:
    semantic_key = str(semantic_article_key or "").strip()
    article_key = str(article_type_key or "").strip()
    goal_key = str(content_goal_key or "").strip()
    if semantic_key == "company_introduction":
        return "例: 事業内容と運用支援の姿勢を根拠付きで伝える"
    if article_key == "announcement":
        return "例: 変更点と必要な対応を迷わず把握できるようにする"
    if article_key == "case_study":
        return "例: どこで迷い、何を変え、どの条件で再現できるかを伝える"
    if goal_key == "trust":
        return "例: 判断材料と根拠が自然に伝わるようにする"
    return "例: 初期設定の負担を減らし、導入判断を進めやすくする価値を伝える"


def _build_core_message_helper_text(
    article_type_key: str,
    semantic_article_key: str = "",
    content_goal_key: str = "",
) -> str:
    semantic_key = str(semantic_article_key or "").strip()
    article_key = str(article_type_key or "").strip()
    goal_key = str(content_goal_key or "").strip()
    if semantic_key == "company_introduction":
        return "※会社紹介では必須です。事業内容の説明ではなく、この会社の何を伝え切るかを1文で入れてください。"
    if article_key == "announcement":
        return "※お知らせで目的を選んだ場合に入力してください。変更点の要約ではなく、読後に何を迷わせないかを1文で入れます。"
    if article_key == "case_study":
        return "※事例で目的を選んだ場合に入力してください。成功談ではなく、読者に残す学びや再現条件を1文で入れます。"
    if article_key == "branding" and goal_key:
        return "※ブランド記事で目的を選んだ場合に入力してください。紹介文全体で押し出す判断軸を1文で入れます。"
    return "※核メッセージは、ブランド / 事例 / お知らせで目的を選んだ場合だけ表示します。"


def _resolve_writer_role_auto_profile(article_type_key: str, semantic_article_key: str = "") -> str:
    semantic_key = str(semantic_article_key or "").strip()
    default = _resolve_article_type_handoff_defaults(article_type_key, semantic_key)
    default_role = str(default.get("writer_role") or "").strip()
    if default_role:
        return default_role
    fallback_label = _get_default_writer_role_label(article_type_key, semantic_key)
    return _writer_role_label_to_profile(fallback_label)


def _resolve_article_type_handoff_defaults(
    article_type_key: str,
    semantic_article_key: str = "",
) -> Dict[str, str]:
    article_key = str(article_type_key or "").strip()
    semantic_key = str(semantic_article_key or "").strip()
    defaults = dict(ARTICLE_TYPE_HANDOFF_DEFAULTS.get(article_key) or ARTICLE_TYPE_HANDOFF_DEFAULTS["default"])
    semantic_defaults = SEMANTIC_ARTICLE_HANDOFF_DEFAULTS.get(semantic_key)
    if semantic_defaults:
        defaults.update(semantic_defaults)
    return defaults


def _resolve_defaulted_handoff_value(
    selected_key: str,
    *,
    defaults: Mapping[str, str],
    field: str,
    auto_value: str = "auto",
) -> str:
    normalized = str(selected_key or auto_value).strip() or auto_value
    if normalized != auto_value:
        return normalized
    return str(defaults.get(field) or auto_value).strip() or auto_value


def _resolve_article_type_handoff_settings(
    *,
    article_type_key: str,
    semantic_article_key: str = "",
    writing_focus_key: str = "auto",
    perspective_key: str = "auto",
    self_reference_policy_key: str = "auto",
    writer_role_text: str = "",
) -> Dict[str, str]:
    defaults = _resolve_article_type_handoff_defaults(article_type_key, semantic_article_key)
    resolved_writer_role = str(writer_role_text or "").strip()
    if not resolved_writer_role:
        resolved_writer_role = str(defaults.get("writer_role") or "").strip()
    return {
        "writer_role": resolved_writer_role[:80],
        "perspective": _resolve_defaulted_handoff_value(
            perspective_key,
            defaults=defaults,
            field="perspective",
        ),
        "writing_focus": _resolve_defaulted_handoff_value(
            writing_focus_key,
            defaults=defaults,
            field="writing_focus",
        ),
        "self_reference_policy": _resolve_defaulted_handoff_value(
            self_reference_policy_key,
            defaults=defaults,
            field="self_reference_policy",
        ),
    }


def _looks_theme_like_writer_role(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    return bool(_THEME_LIKE_WRITER_ROLE_PATTERN.search(text))


def _requires_core_message_input(article_type_key: str, content_goal_key: str) -> bool:
    type_key = str(article_type_key or "").strip()
    goal_key = str(content_goal_key or "").strip()
    return type_key in {"branding", "case_study", "announcement"} and goal_key not in {"", "auto"}

def _resolve_writer_role_option_key(article_type_key: str) -> str:
    key = str(article_type_key or "").strip()
    legacy_aliases = {
        "ai": "explanatory_article",
        "company_introduction": "branding",
        "corporate_culture": "branding",
        "daily_happenings": "daily_story",
    }
    key = legacy_aliases.get(key, key)
    if key in WRITER_ROLE_OPTIONS_BY_ARTICLE_TYPE:
        return key
    custom_genre = genre_manager.get_genre(key)
    if isinstance(custom_genre, dict):
        meta = custom_genre.get("meta")
        if isinstance(meta, dict) and meta:
            base_template = str(meta.get("base_template", "")).strip().lower()
            if base_template == "ai":
                return "explanatory_article"
            if base_template in WRITER_ROLE_OPTIONS_BY_ARTICLE_TYPE:
                return base_template
    return "default"


def _label_for_self_reference_policy_key(policy_key: str) -> str:
    key = str(policy_key or "").strip().lower()
    return SELF_REFERENCE_POLICY_LABELS.get(key, SELF_REFERENCE_POLICY_LABELS["auto"])


def _resolve_self_reference_policy_key(label: Any) -> str:
    selected = str(label or "").strip()
    return next((key for key, value in SELF_REFERENCE_POLICY_LABELS.items() if value == selected), "auto")


def _describe_self_reference_hint(policy_key: str) -> str:
    key = str(policy_key or "").strip().lower()
    if key == "watashi":
        return "自己参照: 『私』を優先（必要な箇所だけ）"
    if key == "watashitachi":
        return "自己参照: 『私たち』を優先（必要な箇所だけ）"
    if key == "tousha":
        return "自己参照: 『当社』を優先（必要な箇所だけ）"
    if key == "heisha":
        return "自己参照: 『弊社』を優先（必要な箇所だけ）"
    if key == "minimal":
        return "自己参照: 一人称をなるべく使わない"
    return ""


def _predict_pronoun_hint(article_type_key: str, writer_role_text: str, self_reference_policy_key: str = "auto") -> str:
    explicit_hint = _describe_self_reference_hint(self_reference_policy_key)
    if explicit_hint:
        return explicit_hint
    role_text = str(writer_role_text or "").strip()
    if role_text:
        if _CORPORATE_WRITER_ROLE_PATTERN.search(role_text):
            return "推奨一人称: 私たち / 当社"
        if _PERSONAL_WRITER_ROLE_PATTERN.search(role_text):
            return "推奨一人称: 私"

    key = _resolve_writer_role_option_key(article_type_key)
    if key in {"explanatory_article", "industry_analysis", "comparative_review"}:
        return "推奨一人称: 私"
    if key in {"announcement", "branding", "case_study", "daily_story"}:
        return "推奨一人称: 私たち / 当社"
    return "推奨一人称: 自動判定"


def _normalize_topic_statement_from_interview(perspective_answer: str) -> str:
    """視点回答を topic_statement に転用してよいか判定する。"""
    return _normalize_topic_statement_from_interview_shared(perspective_answer)


def _normalize_narrative_axis_from_interview(perspective_answer: str) -> str:
    return _normalize_narrative_axis_from_interview_shared(perspective_answer)


def _normalize_interview_list_value(value: Any) -> List[str]:
    return _normalize_interview_list_value_shared(value)


def _derive_knowledge_lenses_from_interview(
    answers: Dict[str, Any],
    *,
    writer_role: str = "",
) -> List[str]:
    return _derive_knowledge_lenses_from_interview_shared(
        answers,
        writer_role=writer_role,
    )


def _build_interview_question_preview_entry(question: Dict[str, Any]) -> str:
    qid = str(question.get("id", "") or "").strip()
    prompt = str(question.get("question", "") or "").strip()[:60]
    options = question.get("options")
    option_preview = ""
    if isinstance(options, list) and options:
        option_preview = " [" + " / ".join(str(item)[:18] for item in options[:2]) + "]"
    return f"{qid}:{prompt}{option_preview}".strip()


def _new_operation_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _log_ui_usage(feature: str, action: str, **extra: Any) -> None:
    payload = {
        "feature": str(feature or "").strip(),
        "action": str(action or "").strip(),
    }
    payload.update({k: v for k, v in extra.items() if v is not None})
    logger.info("ui_usage %s", json.dumps(payload, ensure_ascii=False))


def _classify_reason_code(reason_code: str) -> str:
    code = str(reason_code or "").strip().upper()
    if code.startswith("INP_"):
        return "user_input"
    if code.startswith(("POL_", "SEC_")):
        return "policy"
    if code.startswith("TRN_"):
        return "transient"
    return "system"


def _format_fetch_failures(failures: List[Any]) -> str:
    if not failures:
        return ""
    labels = {
        "robots_blocked": ("E-ROBOTS", "robots.txtにより取得できません"),
        "invalid_or_unsafe_url": ("E-URL", "URL形式または安全性の検証で失敗しました"),
        "redirect_not_supported": ("E-REDIRECT", "リダイレクトURLは未対応です"),
        "http_403_forbidden": ("E-403", "アクセス拒否のため取得できません"),
        "http_error": ("E-HTTP", "HTTPエラーで取得できません"),
        "network_error": ("E-NET", "通信エラーで取得できません"),
        "unauthorized_file_path": ("E-PATH", "許可外のファイルパスです"),
        "file_not_found": ("E-FILE", "ファイルが見つかりません"),
        "pdf_extractor_missing": ("E-PDF-LIB", "PDF抽出ライブラリが見つかりません"),
        "pdf_no_text": ("E-PDF-TEXT", "PDFから抽出可能なテキストが見つかりません"),
        "pdf_parse_failed": ("E-PDF-PARSE", "PDFの解析に失敗しました"),
        "docx_extractor_missing": ("E-DOCX-LIB", "DOCX抽出ライブラリが見つかりません"),
        "docx_no_text": ("E-DOCX-TEXT", "DOCXから抽出可能なテキストが見つかりません"),
        "docx_parse_failed": ("E-DOCX-PARSE", "DOCXの解析に失敗しました"),
        "fetch_failed": ("E-FETCH", "ソース取得に失敗しました"),
    }
    recovery = {
        "robots_blocked": "公開資料を手動でPDF化してアップロードするか、取得可能な公式資料URLに変更してください。",
        "invalid_or_unsafe_url": "URLをコピーし直し、http/https・ホスト名・末尾記号を確認してください。",
        "redirect_not_supported": "最終到達URL（リダイレクト先）を直接入力してください。",
        "http_403_forbidden": "ブラウザで閲覧可能な場合は、必要箇所をPDF化してファイル入力してください。",
        "http_error": "URLが生きているか確認し、時間をおいて再試行してください。",
        "network_error": "ネットワーク状態を確認し、再試行してください。",
        "unauthorized_file_path": "アップロード機能からファイルを再選択してください。",
        "file_not_found": "ファイルの場所を確認し、再アップロードしてください。",
        "pdf_extractor_missing": "実行中のPython環境にpdfplumber/pypdfをインストールしてください。",
        "pdf_no_text": "OCR済みPDFかテキスト入りPDFを使用してください（スキャン画像PDFは不可）。",
        "pdf_parse_failed": "PDFを開き直して再保存するか、別形式（txt/md）で投入してください。",
        "docx_extractor_missing": "実行中のPython環境にpython-docxをインストールしてください。",
        "docx_no_text": "本文テキストを含むDOCXを使用してください（図のみ文書は不可）。",
        "docx_parse_failed": "DOCXを開き直して再保存するか、別形式（txt/md）で投入してください。",
        "fetch_failed": "入力ソースを見直して再試行してください。",
    }
    lines: List[str] = []
    for failure in failures[:5]:
        reason_key = getattr(failure, "reason", "")
        detail = getattr(failure, "detail", "") or ""
        # Defensive remap: if reason fell back to generic, infer from detail string.
        if reason_key in {"fetch_failed", "", None}:
            lowered = detail.lower()
            if "pdf extractor not available" in lowered:
                reason_key = "pdf_extractor_missing"
            elif "no extractable text found in pdf" in lowered:
                reason_key = "pdf_no_text"
            elif "pdf parsing failed" in lowered:
                reason_key = "pdf_parse_failed"
            elif "docx extractor not available" in lowered:
                reason_key = "docx_extractor_missing"
            elif "no extractable text found in docx" in lowered:
                reason_key = "docx_no_text"
            elif "docx parsing failed" in lowered:
                reason_key = "docx_parse_failed"
        code, reason = labels.get(reason_key, ("E-UNKNOWN", "取得失敗"))
        source = getattr(failure, "source", "unknown")
        step = recovery.get(reason_key, "入力を見直して再試行してください。")
        lines.append(f"- {reason}\n  対象: {source}\n  詳細: {detail}\n  対処: {step}")
    if len(failures) > 5:
        lines.append(f"- ...他 {len(failures) - 5} 件")
    return "\n".join(lines)


def _extract_403_urls(failures: List[Any]) -> List[str]:
    urls: List[str] = []
    for failure in failures or []:
        reason = getattr(failure, "reason", "")
        source = (getattr(failure, "source", "") or "").strip()
        if reason == "http_403_forbidden" and source.startswith(("http://", "https://")) and source not in urls:
            urls.append(source)
    return urls


def _collect_source_notices(contexts: List[Any]) -> List[str]:
    notices: List[str] = []
    for ctx in contexts or []:
        source_label = (
            getattr(ctx, "title", None)
            or getattr(ctx, "source_path", None)
            or getattr(ctx, "url", None)
            or "ソース"
        )
        for note in (getattr(ctx, "notices", None) or []):
            note_text = str(note).strip()
            if note_text:
                notices.append(f"{source_label}: {note_text}")
    return notices[:5]


def _notify_source_notices(contexts: List[Any]) -> None:
    notices = _collect_source_notices(contexts)
    if not notices:
        return
    ui.notify(notices[0], color="warning")
    if len(notices) > 1:
        ui.notify(f"取り込み上限調整の通知が他にも {len(notices) - 1} 件あります。", color="warning")


def _build_generation_delay_notice(source_count: int, total_chars: int = 0) -> str:
    reasons: List[str] = []
    if source_count >= SLOW_SOURCE_COUNT_THRESHOLD:
        reasons.append(f"引用ソース{source_count}件")
    if total_chars >= SLOW_TOTAL_CHARS_THRESHOLD:
        reasons.append(f"抽出本文{total_chars}文字")
    if not reasons:
        return ""
    return f"{' / '.join(reasons)}のため、通常より生成に時間がかかる可能性があります。"


def _find_recent_pdf_candidates(since_ts: float, limit: int = 8) -> List[str]:
    downloads = Path.home() / "Downloads"
    if not downloads.exists():
        return []
    candidates: List[Tuple[float, str]] = []
    for p in downloads.glob("*.pdf"):
        try:
            stat = p.stat()
        except OSError:
            continue
        if stat.st_size <= 0 or stat.st_size > 10 * 1024 * 1024:
            continue
        if stat.st_mtime < max(0.0, since_ts - 30):
            continue
        candidates.append((stat.st_mtime, str(p)))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [path for _, path in candidates[:limit]]


def _ingest_local_pdf_to_uploads(path: str) -> str:
    return str(copy_local_pdf_to_uploads(src_path=path, upload_dir=UPLOAD_DIR))


def _reset_pdf_assist() -> None:
    state.blocked_403_urls = []
    state.pdf_assist_candidates = []
    state.pdf_assist_status = ""
    state.pdf_assist_since_ts = 0.0


def _is_ambiguity_confirmed(check_result) -> bool:
    if not check_result.requires_confirmation:
        return True
    if state.ambiguity_signature != check_result.signature:
        return False
    for candidate in check_result.candidates:
        if not state.ambiguity_resolutions.get(candidate.term):
            return False
    return True


def _open_ambiguity_dialog(check_result) -> None:
    with ui.dialog() as dialog, ui.card().classes("p-4 w-[34rem]"):
        ui.label("語義確認が必要です").classes("text-lg font-bold mb-2")
        ui.label("曖昧語の意味を確定しないと生成に進めません。").classes("text-sm text-gray-600 mb-3")
        selects = {}
        for candidate in check_result.candidates:
            labels = [option["value"] for option in candidate.options]
            with ui.column().classes("w-full gap-1 mb-2"):
                ui.label(f"{candidate.question}").classes("text-sm font-semibold")
                select = ui.select(
                    options=labels,
                    value=labels[0] if labels else None,
                    label=candidate.term,
                ).classes("w-full")
                selects[candidate.term] = select

        def confirm_terms():
            confirmed: Dict[str, str] = {}
            for candidate in check_result.candidates:
                selected = (selects.get(candidate.term).value or "").strip() if selects.get(candidate.term) else ""
                if not selected:
                    ui.notify(f"「{candidate.term}」の意味を選択してください", color="warning")
                    return
                confirmed[candidate.term] = selected
            state.ambiguity_signature = check_result.signature
            state.ambiguity_resolutions = confirmed
            dialog.close()
            ui.notify("語義確認を保存しました。もう一度「記事を生成」を押してください。", color="info")

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("キャンセル", on_click=dialog.close).props("flat")
            ui.button("確認して保存", on_click=confirm_terms).classes("primary-btn")
    dialog.open()


@ui.refreshable
def sources_container() -> None:
    render_sources_subview(
        source_items=state.sources,
        on_open_privacy_blur_dialog=_open_privacy_blur_dialog,
        on_remove_source=_remove_source,
    )


@ui.refreshable
def custom_genres_container(article_type_select=None) -> None:
    render_custom_genres_subview(
        custom_genres=genre_manager.load_genres(),
        normalize_meta=normalize_category_meta,
        on_edit_genre=lambda genre: _open_edit_dialog(dict(genre), article_type_select),
        on_delete_genre=lambda genre: _confirm_delete_genre(dict(genre), article_type_select),
    )


def _refresh_custom_genre_article_type_select(article_type_select=None) -> None:
    if not article_type_select:
        return
    article_type_select.options = list(_get_combined_article_types().values())
    if article_type_select.options and article_type_select.value not in article_type_select.options:
        article_type_select.value = article_type_select.options[0]
    article_type_select.update()


def _open_edit_dialog(genre: dict, article_type_select=None) -> None:
    """Open edit dialog for a genre."""
    _log_ui_usage("custom_genre", "open_edit_dialog", key=str(genre.get("key", "") or ""))

    def _notify_validation(message: str) -> None:
        ui.notify(message, color="negative")

    def _save_edit(payload: CustomGenreEditPayload) -> None:
        genre_manager.update_genre(
            payload.key,
            payload.label,
            payload.prompt,
            meta=payload.meta,
        )
        ui.notify("更新しました", color="positive")
        _log_ui_usage("custom_genre", "save_edit", key=str(genre.get("key", "") or ""))
        custom_genres_container.refresh()
        _refresh_custom_genre_article_type_select(article_type_select)

    open_custom_genre_edit_dialog(
        genre=genre,
        normalize_meta=normalize_category_meta,
        base_template_options=list(BASE_TEMPLATE_LABELS.values()),
        focus_default_options=list(FOCUS_DEFAULT_LABELS.values()),
        level_options=list(LEVEL_LABELS.values()),
        evidence_options=list(EVIDENCE_LABELS.values()),
        on_validation_error=_notify_validation,
        on_save=_save_edit,
    )


def _confirm_delete_genre(genre: dict, article_type_select=None) -> None:
    """Show delete confirmation dialog."""

    def _delete_genre(genre_key: str) -> None:
        genre_manager.delete_genre(genre_key)
        ui.notify("削除しました", color="positive")
        _log_ui_usage("custom_genre", "delete", key=str(genre.get("key", "") or ""))
        custom_genres_container.refresh()
        _refresh_custom_genre_article_type_select(article_type_select)

    open_custom_genre_delete_dialog(
        genre=genre,
        on_confirm_delete=_delete_genre,
    )


def _open_privacy_blur_dialog(source_id: str) -> None:
    """アップロード画像向けプライバシーぼかし専用ダイアログを開く。"""
    _log_ui_usage("source_privacy_blur", "open_dialog", source_id=source_id)
    source_item = next((s for s in state.sources if s.id == source_id), None)
    if source_item is None:
        ui.notify("対象のソースが見つかりません", color="negative")
        return
    image_path = source_item.value

    privacy_strength_options = {"light": "弱", "medium": "標準", "strong": "強"}
    preview_paths: List[Path] = []
    dialog_controls: Dict[str, Any] = {}

    def _cleanup_preview_files(keep_latest: bool = False) -> None:
        targets = preview_paths[:-1] if keep_latest else list(preview_paths)
        for path in targets:
            try:
                if path.exists() and "_preview_" in path.stem:
                    path.unlink(missing_ok=True)
            except OSError:
                logger.debug("Failed to cleanup preview file path=%s", path)
        if keep_latest and preview_paths:
            preview_paths[:] = [preview_paths[-1]]
        elif not keep_latest:
            preview_paths.clear()

    def _get_dialog_controls() -> Any:
        return dialog_controls["view"]

    def _collect_privacy_blur() -> PrivacyBlur:
        controls = _get_dialog_controls()
        return PrivacyBlur(
            enabled=True,
            strength=resolve_privacy_option_key(
                options=privacy_strength_options,
                selected_label=str(controls.privacy_strength_select.value or ""),
                fallback="medium",
            ),
            blur_faces=bool(controls.blur_faces_cb.value),
            blur_license_plates=bool(controls.blur_plates_cb.value),
            blur_qr_codes=bool(controls.blur_qr_cb.value),
            blur_personal_text=bool(controls.blur_text_cb.value),
        )

    def _set_buttons_busy(busy: bool) -> None:
        controls = _get_dialog_controls()
        if busy:
            controls.preview_btn.disable()
            controls.save_btn.disable()
        else:
            controls.preview_btn.enable()
            controls.save_btn.enable()
            _update_save_btn_state()

    def _any_target_selected() -> bool:
        controls = _get_dialog_controls()
        return privacy_blur_targets_selected(
            blur_faces=bool(controls.blur_faces_cb.value),
            blur_license_plates=bool(controls.blur_plates_cb.value),
            blur_qr_codes=bool(controls.blur_qr_cb.value),
            blur_personal_text=bool(controls.blur_text_cb.value),
        )

    def _update_save_btn_state() -> None:
        controls = dialog_controls.get("view")
        if controls is None:
            return
        if _any_target_selected():
            controls.save_btn.enable()
            controls.save_btn.tooltip("")
        else:
            controls.save_btn.disable()
            controls.save_btn.tooltip("検出対象を1つ以上選択してください")

    async def _refresh_preview() -> None:
        controls = _get_dialog_controls()
        _set_buttons_busy(True)
        controls.preview_status.text = "プレビュー更新中..."
        controls.preview_status.classes(remove="text-red-500")
        privacy_blur = _collect_privacy_blur()
        preview_path, error = await run.io_bound(
            render_image_edit_preview,
            image_path,
            "none",
            "none",
            ImageAdjustment(),
            None,
            TEXT_OVERLAY_FONT_PATH,
            str(UPLOAD_DIR),
            privacy_blur,
        )
        _set_buttons_busy(False)
        if error or not preview_path:
            controls.preview_status.text = error or "プレビュー生成に失敗しました"
            controls.preview_status.classes(add="text-red-500")
            return
        preview_paths.append(preview_path)
        _cleanup_preview_files(keep_latest=True)
        try:
            controls.after_image.set_source(str(preview_path))
        except AttributeError:
            controls.after_image.source = str(preview_path)
            controls.after_image.update()
        controls.preview_status.text = "プレビュー更新済み"

    async def _save_privacy_blur() -> None:
        controls = _get_dialog_controls()
        _set_buttons_busy(True)
        controls.preview_status.text = "保存中..."
        privacy_blur = _collect_privacy_blur()
        result_path, error = await run.io_bound(
            save_edited_image_core,
            image_path,
            "none",
            "none",
            ImageAdjustment(),
            None,
            TEXT_OVERLAY_FONT_PATH,
            str(UPLOAD_DIR),
            privacy_blur,
        )
        if error or not result_path:
            _set_buttons_busy(False)
            ui.notify(error or "保存に失敗しました", color="negative")
            controls.preview_status.text = "保存に失敗しました"
            return
        source_item.value = str(result_path)
        source_item.blur_applied = True
        sources_container.refresh()
        _log_ui_usage("source_privacy_blur", "save", source_id=source_id)
        ui.notify("ぼかし処理を適用しました", color="positive")
        _cleanup_preview_files(keep_latest=False)
        controls.dialog.close()

    def _close_dialog() -> None:
        _cleanup_preview_files(keep_latest=False)
        controls = dialog_controls.get("view")
        if controls is not None:
            controls.dialog.close()

    dialog_controls["view"] = open_privacy_blur_dialog_view(
        image_path=image_path,
        privacy_strength_labels=list(privacy_strength_options.values()),
        on_close=_close_dialog,
        on_preview=_refresh_preview,
        on_save=_save_privacy_blur,
        on_toggle_selection=_update_save_btn_state,
    )
    _update_save_btn_state()
    dialog_controls["view"].dialog.open()


@ui.refreshable
def generated_images_container() -> None:
    render_generated_images_subview(
        generated_image_variants=getattr(state, "generated_image_variants", []),
        generated_images=state.generated_images,
        image_generation_status=str(getattr(state, "image_generation_status", "") or ""),
        on_download_image=ui.download,
    )


def _scroll_to_generation_result() -> None:
    ui.run_javascript(build_scroll_to_anchor_script("generation-result-anchor"))


def _copy_text(text: str) -> None:
    if not text:
        ui.notify("コピーする内容がありません", color="negative")
        return
    ui.run_javascript(build_copy_to_clipboard_script(text))
    ui.notify("コピーしました", color="positive")


# _to_note_format / _hashtags_to_plain / _replace_hashtags_for_preview / _to_plain_dict / _to_plain_list は
# note_text_format_helpers に分離済み (上部 import 経由で参照)。


def _build_current_mainline_user_input_feedback(
    *,
    reason_code: str,
    needs_input_items: Any = None,
) -> Tuple[str, str, str]:
    return build_current_mainline_user_input_feedback_core(
        reason_code=reason_code,
        needs_input_items=needs_input_items,
    )


# _count_sentences / _PROPOSITION_* / _build_proposition_density_target_text /
# _extract_proposition_sentences / _count_proposition_content_terms /
# _classify_proposition_sentence / _analyze_proposition_density は
# proposition_density_helpers.py に分離済み。


_OUTPUT_GUARD_MAX_SEMANTIC_ISSUES = 5
_OUTPUT_GUARD_MIN_ALIGNMENT_SCORE = 0.45
_OUTPUT_GUARD_MIN_MUST_COVER_REFLECTION = 0.50
_OUTPUT_GUARD_MIN_PROMPT_ANCHOR_COVERAGE = 0.34
_OUTPUT_GUARD_MIN_ANCHOR_TERM_COVERAGE = 0.30
_OUTPUT_GUARD_MIN_SECTION_FOCUS_COVERAGE = 0.60
_OUTPUT_GUARD_MIN_SPEAKER_CONSISTENCY = 0.55
_OUTPUT_GUARD_MIN_PRONOUN_CONSISTENCY = 0.50
_OUTPUT_GUARD_MIN_RELATIONSHIP_CONSISTENCY = 0.50
_OUTPUT_GUARD_MIN_HEADING_ALIGNMENT_MEAN = 0.12
_OUTPUT_GUARD_SOFT_MAX_TOPIC_OPENING_RATIO = 0.32
_OUTPUT_GUARD_SOFT_MAX_AWKWARD_ENDING_RATIO = 0.20
_OUTPUT_GUARD_SOFT_MAX_AI_TEMPLATE_ENDING_RATIO = 0.10
_OUTPUT_GUARD_MIN_PROPOSITION_SENTENCE_COUNT = 10
_OUTPUT_GUARD_ANNOUNCEMENT_MIN_PROPOSITION_INFORMATIVE_RATIO = 0.52
_OUTPUT_GUARD_ANNOUNCEMENT_MAX_PROPOSITION_LOW_INFO_RATIO = 0.28
_OUTPUT_GUARD_SOFT_MIN_PROPOSITION_INFORMATIVE_RATIO = 0.45
_OUTPUT_GUARD_SOFT_MAX_PROPOSITION_LOW_INFO_RATIO = 0.36
_TRANSIENT_AUTO_RETRY_MAX = 1
_OUTPUT_GUARD_AUTO_REPAIR_MAX = 1
_NEEDS_INPUT_MAX_ROUNDS = 2
def _build_interview_context_signature(
    *,
    source_values: List[str],
    article_type_key: str,
    content_goal_key: str,
    user_prompt_text: str,
) -> str:
    payload = {
        "article_type": str(article_type_key or "").strip(),
        "content_goal": str(content_goal_key or "").strip(),
        "user_prompt": str(user_prompt_text or "").strip(),
        "sources": sorted(
            str(value or "").strip()
            for value in source_values
            if str(value or "").strip()
        ),
    }
    normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _scan_instructional_fragments(
    *texts: str,
    references: Optional[List[str]] = None,
    max_hits: int = 5,
) -> List[str]:
    return output_guard_mod.scan_instructional_fragments(
        *texts,
        references=list(references or []),
        max_hits=max_hits,
    )


def _iter_quality_phase_reports(quality: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten report schema to phase-level entries (supports nested/legacy)."""
    flattened: List[Dict[str, Any]] = []
    for report in _to_plain_list(quality.get("reports")):
        if not isinstance(report, dict):
            continue
        nested = _to_plain_list(report.get("phase_reports"))
        if nested:
            flattened.extend([phase for phase in nested if isinstance(phase, dict)])
            continue
        if report.get("phase"):
            flattened.append(report)
    return flattened


def _extract_fingerprint_phase_report(quality: Dict[str, Any]) -> Dict[str, Any]:
    for phase_report in _iter_quality_phase_reports(quality):
        if str(phase_report.get("phase", "") or "") != "fingerprint":
            continue
        return {
            "flat_zone_flags": _to_plain_list(phase_report.get("flat_zone_flags")),
            "overall_unpredictability": _safe_round_float(
                phase_report.get("overall_unpredictability"),
                4,
                0.0,
            ),
            "correction_hints": _to_plain_list(phase_report.get("correction_hints")),
            "fingerprint_correction_applied": bool(
                phase_report.get("fingerprint_correction_applied", False)
            ),
            "nominalization_rate": _safe_round_float(
                phase_report.get("nominalization_rate"),
                4,
                0.0,
            ),
            "sentence_ending_entropy": _safe_round_float(
                phase_report.get("sentence_ending_entropy"),
                4,
                0.0,
            ),
            "sentence_ending_fine_entropy": _safe_round_float(
                phase_report.get("sentence_ending_fine_entropy"),
                4,
                0.0,
            ),
            "subject_explicit_rate": _safe_round_float(
                phase_report.get("subject_explicit_rate"),
                4,
                0.0,
            ),
            "mtld": _safe_round_float(phase_report.get("mtld"), 4, 0.0),
        }
    return {}


def _collect_runtime_config_snapshot(result: Dict[str, Any]) -> Dict[str, Any]:
    return runtime_collect_runtime_config_snapshot(result)


def _is_missing_alignment_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _derive_interview_answer_source_counts(input_contract: Dict[str, Any]) -> Dict[str, int]:
    interview_answers = _to_plain_dict(input_contract.get("interview_answers"))
    answered_count = sum(
        1
        for key in ("perspective", "target", "message")
        if str(interview_answers.get(key, "") or "").strip()
    )
    if answered_count <= 0:
        return {}
    return {
        "interview_answers": answered_count,
        "user_prompt": 0,
        "unresolved_items": 0,
        "unknown": 0,
    }


def _evaluate_generation_output_guard(result: Dict[str, Any]) -> Dict[str, Any]:
    existing_guard = output_guard_mod.extract_existing_output_guard(result)
    reevaluated_guard = output_guard_mod.evaluate_generation_output_guard(result)
    if not existing_guard:
        return reevaluated_guard
    existing_normalized = _to_plain_dict(existing_guard)
    if (
        bool(existing_normalized.get("blocked")) != bool(reevaluated_guard.get("blocked"))
        or str(existing_normalized.get("reason_code") or "") != str(reevaluated_guard.get("reason_code") or "")
        or int(existing_normalized.get("soft_warning_count") or 0) != int(reevaluated_guard.get("soft_warning_count") or 0)
    ):
        return reevaluated_guard
    return existing_normalized


# _extract_guard_forbidden_topics / _resolve_guard_retry_category / _is_guard_auto_repair_candidate /
# _build_guard_retry_prompt / _is_transient_exception / _classify_generation_exception は
# generation_exception_helpers.py に分離済み。


def _build_latest_quality_report_payload(
    *,
    timestamp: str,
    attempt_id: str,
    result: Dict[str, Any],
    config_snapshot: Dict[str, Any],
    failed_parameters: Dict[str, Any],
) -> Dict[str, Any]:
    return runtime_build_latest_quality_report_payload(
        timestamp=timestamp,
        attempt_id=attempt_id,
        result=result,
        config_snapshot=config_snapshot,
        failed_parameters=failed_parameters,
    )


def _append_generation_audit_record(record: Dict[str, Any]) -> int:
    _sync_runtime_logging_paths()
    return runtime_append_generation_audit_record(record)


def _sync_runtime_logging_paths() -> None:
    runtime_logging_mod.LATEST_GENERATION_TEXT_PATH = LATEST_GENERATION_TEXT_PATH
    runtime_logging_mod.LATEST_GENERATION_JSON_PATH = LATEST_GENERATION_JSON_PATH
    runtime_logging_mod.LATEST_GENERATION_QUALITY_REPORT_PATH = LATEST_GENERATION_QUALITY_REPORT_PATH
    runtime_logging_mod.LATEST_GENERATION_TEXT_PATH_WORKSPACE = LATEST_GENERATION_TEXT_PATH_WORKSPACE
    runtime_logging_mod.LATEST_GENERATION_JSON_PATH_WORKSPACE = LATEST_GENERATION_JSON_PATH_WORKSPACE
    runtime_logging_mod.LATEST_GENERATION_QUALITY_REPORT_PATH_WORKSPACE = LATEST_GENERATION_QUALITY_REPORT_PATH_WORKSPACE
    runtime_logging_mod.GENERATION_AUDIT_JSONL_PATH = GENERATION_AUDIT_JSONL_PATH
    runtime_logging_mod.GENERATION_AUDIT_JSONL_PATH_WORKSPACE = GENERATION_AUDIT_JSONL_PATH_WORKSPACE
    if "LATEST_UI_JOURNEY_PATH" in globals():
        runtime_logging_mod.LATEST_UI_JOURNEY_PATH = globals()["LATEST_UI_JOURNEY_PATH"]
    if "LATEST_UI_JOURNEY_PATH_WORKSPACE" in globals():
        runtime_logging_mod.LATEST_UI_JOURNEY_PATH_WORKSPACE = globals()["LATEST_UI_JOURNEY_PATH_WORKSPACE"]
    if "UI_JOURNEY_JSONL_PATH" in globals():
        runtime_logging_mod.UI_JOURNEY_JSONL_PATH = globals()["UI_JOURNEY_JSONL_PATH"]
    if "UI_JOURNEY_JSONL_PATH_WORKSPACE" in globals():
        runtime_logging_mod.UI_JOURNEY_JSONL_PATH_WORKSPACE = globals()["UI_JOURNEY_JSONL_PATH_WORKSPACE"]


def _append_ui_journey_event(
    *,
    attempt_id: str,
    event: str,
    article_type: str = "",
    phase: str = "",
    user_prompt_text: str = "",
    source_items: Any = None,
    selections: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    reason_code: str = "",
    error_class: str = "",
    status_text: str = "",
    needs_input_items: Optional[List[Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> int:
    return runtime_append_ui_journey_event(
        attempt_id=attempt_id,
        event=event,
        article_type=article_type,
        phase=phase,
        user_prompt_text=user_prompt_text,
        source_items=source_items,
        selections=selections,
        result=result,
        reason_code=reason_code,
        error_class=error_class,
        status_text=status_text,
        needs_input_items=needs_input_items,
        extra=extra,
    )


def _record_ui_journey_event(
    *,
    attempt_id: str,
    event: str,
    article_type: str = "",
    phase: str = "",
    user_prompt_text: str = "",
    source_items: Any = None,
    selections: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    reason_code: str = "",
    error_class: str = "",
    status_text: str = "",
    needs_input_items: Optional[List[Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        _append_ui_journey_event(
            attempt_id=attempt_id,
            event=event,
            article_type=article_type,
            phase=phase,
            user_prompt_text=user_prompt_text,
            source_items=source_items,
            selections=selections,
            result=result,
            reason_code=reason_code,
            error_class=error_class,
            status_text=status_text,
            needs_input_items=needs_input_items,
            extra=extra,
        )
    except Exception:
        logger.debug(
            "Failed to record ui journey event id=%s event=%s",
            attempt_id,
            event,
            exc_info=True,
        )


def _persist_latest_generation_snapshot(
    *,
    result: Dict[str, Any],
    attempt_id: str,
    article_type: str,
    writing_focus_key: str,
    perspective_key: str,
    prompt_raw: str,
    system_hint_items: Optional[List[str]],
    retry_memo: Optional[List[str]],
    strict_saas_mode: str,
    source_count: int,
    tone_profile_key: str = "auto",
    blocked: bool = False,
) -> None:
    _sync_runtime_logging_paths()
    runtime_persist_latest_generation_snapshot(
        result=result,
        attempt_id=attempt_id,
        article_type=article_type,
        writing_focus_key=writing_focus_key,
        perspective_key=perspective_key,
        prompt_raw=prompt_raw,
        system_hint_items=system_hint_items,
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        source_count=source_count,
        tone_profile_key=tone_profile_key,
        blocked=blocked,
    )


def _attach_prompt_context_to_result(
    result: Dict[str, Any],
    *,
    prompt_raw: str,
    system_hint_items: Optional[List[str]],
    retry_memo: Optional[List[str]],
    strict_saas_mode: str,
    question_generation_owner: str = "",
) -> Dict[str, Any]:
    return attach_prompt_context_to_result_core(
        result,
        prompt_raw=prompt_raw,
        system_hint_items=system_hint_items,
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        question_generation_owner=question_generation_owner,
        default_strict_saas_mode=CURRENT_MAINLINE_STRICT_SAAS_MODE,
    )


def _build_current_mainline_success_view(
    result: Dict[str, Any],
    *,
    quality_warning_only: bool,
    guard_retry_count: int = 0,
) -> Dict[str, Any]:
    return build_current_mainline_success_view_core(
        result,
        quality_warning_only=quality_warning_only,
        guard_retry_count=guard_retry_count,
    )


def _build_current_mainline_output_guard_blocked_view(
    output_guard: Dict[str, Any],
    *,
    guard_retry_count: int = 0,
) -> Dict[str, Any]:
    return build_current_mainline_output_guard_blocked_view_core(
        output_guard,
        guard_retry_count=guard_retry_count,
    )


def _build_current_mainline_generation_prerun_plan(*, pre_delay_notice: str = "") -> Dict[str, Any]:
    return build_current_mainline_generation_prerun_plan_core(
        pre_delay_notice=pre_delay_notice,
        preview_placeholder=_PREVIEW_PLACEHOLDER,
    )


def _build_current_mainline_generation_exception_plan(*, phase: str = "") -> Dict[str, Any]:
    return build_current_mainline_generation_exception_plan_core(phase=phase)


def _build_current_mainline_generation_cleanup_plan() -> Dict[str, Any]:
    return build_current_mainline_generation_cleanup_plan_core()


def _build_current_mainline_generation_complete_plan() -> Dict[str, Any]:
    return build_current_mainline_generation_complete_plan_core()


def _build_current_mainline_generation_telemetry_context(
    *,
    attempt_id: str,
    article_type: str,
    user_prompt_text: str = "",
    source_items: Any = None,
    selections: Optional[Dict[str, Any]] = None,
    writing_focus_key: str = "",
    perspective_key: str = "",
    tone_profile_key: str = "auto",
    prompt_raw: str = "",
    system_hint_items: Optional[List[str]] = None,
    retry_memo: Optional[List[str]] = None,
    strict_saas_mode: str = "medium",
    question_generation_owner: str = "",
) -> Dict[str, Any]:
    return build_current_mainline_generation_telemetry_context_core(
        attempt_id=attempt_id,
        article_type=article_type,
        user_prompt_text=user_prompt_text,
        source_items=source_items,
        selections=selections,
        writing_focus_key=writing_focus_key,
        perspective_key=perspective_key,
        tone_profile_key=tone_profile_key,
        prompt_raw=prompt_raw,
        system_hint_items=system_hint_items,
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        question_generation_owner=question_generation_owner,
    )


def _build_current_mainline_run_generation_telemetry_context(
    *,
    attempt_id: str,
    article_type: str,
    user_prompt_text: str,
    source_items: Any,
    selections: Optional[Dict[str, Any]] = None,
    question_generation_owner: str = "",
    writing_focus_key: str = "",
    perspective_key: str = "",
    tone_profile_key: str = "auto",
    prompt_raw: str = "",
    system_hint_items: Optional[List[str]] = None,
    retry_memo: Optional[List[str]] = None,
    strict_saas_mode: str = "",
) -> Dict[str, Any]:
    return _build_current_mainline_generation_telemetry_context(
        attempt_id=attempt_id,
        article_type=article_type,
        user_prompt_text=user_prompt_text,
        source_items=source_items,
        selections=selections,
        writing_focus_key=writing_focus_key,
        perspective_key=perspective_key,
        tone_profile_key=tone_profile_key,
        prompt_raw=prompt_raw,
        system_hint_items=system_hint_items,
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode or CURRENT_MAINLINE_STRICT_SAAS_MODE,
        question_generation_owner=question_generation_owner,
    )


def _build_current_mainline_generation_gate_extra(
    *,
    generation_gate_kind: str,
    required_action: str,
    semantic_article_key: str = "",
    allow_generate: bool | None = None,
    selection_confirmed: bool | None = None,
    confirmation_state: str = "",
    confirmed_signature_present: bool | None = None,
    required_step: str = "",
    required_journey_stage: int | None = None,
    selected_article_type_label: str = "",
    resolved_article_type: str = "",
    article_type_resolution_state: str = "",
    term_count: int | None = None,
) -> Dict[str, Any]:
    return build_current_mainline_generation_gate_extra_core(
        generation_gate_kind=generation_gate_kind,
        required_action=required_action,
        semantic_article_key=semantic_article_key,
        allow_generate=allow_generate,
        selection_confirmed=selection_confirmed,
        confirmation_state=confirmation_state,
        confirmed_signature_present=confirmed_signature_present,
        required_step=required_step,
        required_journey_stage=required_journey_stage,
        selected_article_type_label=selected_article_type_label,
        resolved_article_type=resolved_article_type,
        article_type_resolution_state=article_type_resolution_state,
        term_count=term_count,
    )


def _build_current_mainline_generation_busy_view() -> Dict[str, Any]:
    return build_current_mainline_generation_busy_view_core()


def _build_current_mainline_generation_no_sources_view() -> Dict[str, Any]:
    return build_current_mainline_generation_no_sources_view_core()


def _build_current_mainline_invalid_article_type_view(
    *,
    semantic_article_key: str,
    selection_confirmed: bool,
    selected_article_type_label: str,
    resolved_article_type: str,
    article_type_resolution_state: str,
) -> Dict[str, Any]:
    return build_current_mainline_invalid_article_type_view_core(
        extra=_build_current_mainline_generation_gate_extra(
            generation_gate_kind="invalid_article_type",
            required_action="reselect_article_type",
            semantic_article_key=semantic_article_key,
            allow_generate=False,
            selection_confirmed=selection_confirmed,
            selected_article_type_label=selected_article_type_label,
            resolved_article_type=resolved_article_type,
            article_type_resolution_state=article_type_resolution_state,
        ),
    )


def _build_current_mainline_confirmation_required_view(
    *,
    semantic_article_key: str,
    selection_confirmed: bool,
    confirmation_state: str,
    confirmed_signature_present: bool,
    required_journey_stage: int,
) -> Dict[str, Any]:
    return build_current_mainline_confirmation_required_view_core(
        extra=_build_current_mainline_generation_gate_extra(
            generation_gate_kind="confirmation_required",
            required_action="refresh_and_confirm_journey",
            semantic_article_key=semantic_article_key,
            allow_generate=False,
            selection_confirmed=selection_confirmed,
            confirmation_state=confirmation_state,
            confirmed_signature_present=confirmed_signature_present,
            required_step="confirm",
            required_journey_stage=required_journey_stage,
        ),
    )


def _build_journey_confirmation_cta_state(
    *,
    confirmation_ready: bool,
) -> Dict[str, Any]:
    if confirmation_ready:
        return {
            "badge_text": "確定済み",
            "badge_classes": "bg-green-100 text-green-700",
            "card_hint_text": "確認済みです。生成を始める場合は下のボタンを押してください。",
            "preview_button_text": "不足を確認",
            "confirm_button_enabled": True,
            "confirm_button_text": "内容を再確認",
            "generate_button_enabled": True,
            "generate_button_text": "この内容で生成を開始",
            "generate_hint_text": "このボタンを押すと記事生成が始まります。",
            "generate_hint_classes": "text-green-700",
        }
    return {
        "badge_text": "未確認",
        "badge_classes": "bg-amber-100 text-amber-700",
        "card_hint_text": "内容を確認すると、生成開始ボタンを押せるようになります。",
        "preview_button_text": "不足を確認",
        "confirm_button_enabled": True,
        "confirm_button_text": "内容を確認",
        "generate_button_enabled": False,
        "generate_button_text": "確認後に生成を開始",
        "generate_hint_text": "先に内容を確認してください。確認だけでは生成は始まりません。",
        "generate_hint_classes": "text-amber-700",
    }


def _resolve_journey_confirm_button_text(
    *,
    cta_state: Mapping[str, Any],
    gate_surface: Mapping[str, Any],
    confirmation_ready: bool,
    source_session_requires_review: bool,
) -> str:
    if bool(gate_surface.get("enabled")):
        return str(cta_state.get("confirm_button_text") or "内容を確認")
    confirmation_only_gate = (
        not confirmation_ready
        and not source_session_requires_review
        and str(gate_surface.get("button_text") or "") == "方針を確認する"
    )
    if confirmation_only_gate:
        return str(cta_state.get("confirm_button_text") or "内容を確認")
    return "不足を確認"


def _build_journey_generation_confirmation_state(
    *,
    current_signature: str,
    confirmed_signature: str,
) -> Dict[str, Any]:
    normalized_current = str(current_signature or "").strip()
    normalized_confirmed = str(confirmed_signature or "").strip()
    ready = bool(normalized_current and normalized_confirmed and normalized_confirmed == normalized_current)
    if ready:
        state = "confirmed"
    elif normalized_confirmed:
        state = "stale_signature"
    else:
        state = "missing_confirmation"
    return {
        "ready": ready,
        "confirmation_state": state,
        "confirmed_signature_present": bool(normalized_confirmed),
    }


def _build_source_session_acceptance_confirmation_plan(
    *,
    current_signature: str,
    confirmed_signature: str,
) -> Dict[str, Any]:
    confirmation_state = _build_journey_generation_confirmation_state(
        current_signature=current_signature,
        confirmed_signature=confirmed_signature,
    )
    preserve_confirmation = bool(confirmation_state.get("ready"))
    return {
        "preserve_confirmation": preserve_confirmation,
        "invalidate_confirmation": not preserve_confirmation,
        "confirmation_state": str(confirmation_state.get("confirmation_state") or ""),
        "confirmed_signature_present": bool(confirmation_state.get("confirmed_signature_present")),
    }


def _build_current_mainline_ambiguity_confirmation_view(
    *,
    semantic_article_key: str,
    selection_confirmed: bool,
    term_count: int,
) -> Dict[str, Any]:
    return build_current_mainline_ambiguity_confirmation_view_core(
        extra=_build_current_mainline_generation_gate_extra(
            generation_gate_kind="ambiguity_confirmation",
            required_action="confirm_ambiguity_terms",
            semantic_article_key=semantic_article_key,
            allow_generate=False,
            selection_confirmed=selection_confirmed,
            term_count=term_count,
        ),
    )


def _build_current_mainline_missing_required_inputs_view(
    *,
    missing_fields: List[str],
) -> Dict[str, Any]:
    return build_current_mainline_missing_required_inputs_view_core(
        missing_fields=missing_fields,
    )


def _record_current_mainline_generation_event(
    *,
    telemetry_context: Dict[str, Any],
    event: str,
    phase: str,
    result: Optional[Dict[str, Any]] = None,
    reason_code: str = "",
    error_class: str = "",
    status_text: str = "",
    needs_input_items: Optional[List[Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
    include_question_generation_owner: bool = False,
) -> None:
    event_request = build_current_mainline_generation_event_request_core(
        telemetry_context,
        event=event,
        phase=phase,
        result=result,
        reason_code=reason_code,
        error_class=error_class,
        status_text=status_text,
        needs_input_items=needs_input_items,
        extra=extra,
        include_question_generation_owner=include_question_generation_owner,
    )
    _record_ui_journey_event(**event_request)


def _persist_current_mainline_generation_snapshot_from_context(
    *,
    telemetry_context: Dict[str, Any],
    result: Dict[str, Any],
    source_count: int,
    blocked: bool = False,
) -> None:
    snapshot_request = build_current_mainline_generation_snapshot_request_core(
        telemetry_context,
        result=result,
        source_count=source_count,
        blocked=blocked,
    )
    _persist_latest_generation_snapshot(**snapshot_request)


def _attach_output_guard_to_result(result: Dict[str, Any], guard: Dict[str, Any]) -> Dict[str, Any]:
    return output_guard_mod.attach_output_guard_to_result(result, guard)


def _restore_current_mainline_warning_only_success_fields(result: Dict[str, Any]) -> Dict[str, Any]:
    restored = dict(result or {})
    lead = str(restored.get("lead") or "").strip()
    body = str(restored.get("body") or "").strip()
    references = str(restored.get("references") or "").strip()
    full_body = str(restored.get("full_body") or "").strip()
    if not full_body:
        full_body = "\n\n".join(part for part in (lead, body, references) if part).strip()
        restored["full_body"] = full_body
    full_text = str(restored.get("full_text") or "").strip()
    if not full_text or full_text == "[BLOCKED_OUTPUT_REDACTED]":
        title = str(restored.get("title") or "").strip()
        hashtags = str(restored.get("hashtags") or "").strip()
        full_text_parts = [title, full_body]
        if hashtags:
            full_text_parts.extend(["---", hashtags])
        restored["full_text"] = "\n\n".join(part for part in full_text_parts if part).strip()
    failed_parameters = _to_plain_dict(restored.get("failed_parameters"))
    if failed_parameters:
        failed_parameters["has_failure"] = False
        failed_parameters["runtime_error_class"] = "success"
        failed_parameters["runtime_reason_code"] = "OK"
        restored["failed_parameters"] = failed_parameters
    restored["blocked_output_redacted"] = False
    restored["success"] = True
    restored["runtime_error_class"] = "success"
    restored["runtime_reason_code"] = "OK"
    restored["reason_code"] = "OK"
    return restored


def _apply_current_mainline_fingerprint_only_warning_policy(
    result: Dict[str, Any],
    output_guard: Dict[str, Any],
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    if not output_guard_mod.is_fingerprint_only_warning_observable(result, output_guard):
        return result, output_guard
    warning_guard = output_guard_mod.demote_fingerprint_only_output_guard_to_warning(output_guard)
    warning_result = _attach_output_guard_to_result(result, warning_guard)
    warning_result = _restore_current_mainline_warning_only_success_fields(warning_result)
    return warning_result, warning_guard


# _build_short_sns_text は note_text_format_helpers に分離済み。


# _normalize_image_pattern_key / _build_image_pattern_suffix /
# _apply_image_pattern_to_prompt / _build_image_prompt は image_prompt_helpers.py に分離済み。


def _build_current_mainline_fetch_failure_view(
    *,
    details: str,
    blocked_urls: List[str],
    failure_count: int,
) -> Dict[str, Any]:
    return build_current_mainline_fetch_failure_view_core(
        details=details,
        blocked_urls=blocked_urls,
        failure_count=failure_count,
    )


def _build_current_mainline_no_valid_sources_view() -> Dict[str, Any]:
    return build_current_mainline_no_valid_sources_view_core()


def _build_current_mainline_generation_error_view(
    *,
    reason_code: str,
    error_class: str,
    error_message: str = "",
    needs_input_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return build_current_mainline_generation_error_view_core(
        reason_code=reason_code,
        error_class=error_class,
        error_message=error_message,
        needs_input_items=needs_input_items,
    )


def _build_current_mainline_guard_retry_exception_view(
    *,
    reason_code: str,
    error_class: str,
) -> Dict[str, Any]:
    return build_current_mainline_guard_retry_exception_view_core(
        reason_code=reason_code,
        error_class=error_class,
    )


def _build_current_mainline_input_contract_kwargs(
    *,
    source_items: List[Any],
    source_documents: List[Any],
    article_type: str,
    selection: Dict[str, Any],
    user_prompt_text: str,
    content_goal_key: str,
    writing_focus_key: str,
    structure_key: str,
    length_mode_key: str,
    tone_profile_key: str,
    perspective_key: str,
    allow_experience: bool,
    interview_answers: Dict[str, str],
    speaker_profile_input: str,
    audience_profile_input: str,
    core_message_input: str,
    self_reference_policy_key: str,
    branding_subtype_key: str,
    branding_focus_key: str,
    pattern_key: str,
    system_hint_items: List[str],
    retry_memo: List[str],
    strict_saas_mode: str,
    source_mode_key: str,
    industry_hint_input: str = "",
    source_trace: Optional[List[Any]] = None,
    followup_context: Optional[Mapping[str, Any]] = None,
    omakase_preflight_status: str = "",
    omakase_charge_ready: Optional[bool] = None,
    omakase_reason_code: str = "",
    omakase_message: str = "",
    omakase_fallback_options: Optional[List[Any]] = None,
    omakase_needs_input_items: Optional[List[Any]] = None,
    omakase_source_count: Optional[int] = None,
    omakase_existing_post_count: Optional[int] = None,
    omakase_usable_posts_count: Optional[int] = None,
    omakase_dominant_cluster_count: Optional[int] = None,
    omakase_available: Optional[bool] = None,
) -> Dict[str, Any]:
    return {
        "source_values": [
            source.value
            for source in source_items
            if str(getattr(source, "value", "") or "").strip()
        ],
        "source_documents": source_documents,
        "article_type": article_type,
        "ui_journey": selection.get("ui_journey"),
        "comparison_axes": selection.get("comparison_axes"),
        "user_prompt_text": user_prompt_text,
        "content_goal_key": content_goal_key,
        "writing_focus_key": writing_focus_key,
        "structure_key": structure_key,
        "length_mode_key": length_mode_key,
        "tone_profile_key": tone_profile_key,
        "perspective_key": perspective_key,
        "allow_experience": bool(allow_experience),
        "interview_answers": interview_answers,
        "speaker_profile_input": speaker_profile_input,
        "audience_profile_input": audience_profile_input,
        "core_message_input": core_message_input,
        "self_reference_policy_key": self_reference_policy_key,
        "branding_subtype_key": branding_subtype_key,
        "branding_focus_key": branding_focus_key,
        "pattern_key": pattern_key,
        "system_hint_items": system_hint_items,
        "retry_memo": retry_memo,
        "strict_saas_mode": strict_saas_mode,
        "source_mode": source_mode_key,
        "industry_hint": str(industry_hint_input or "").strip()[:120],
        "source_trace": list(source_trace or []),
        "followup_context": dict(followup_context or {}),
        "omakase_preflight_status": str(omakase_preflight_status or "").strip(),
        "omakase_charge_ready": omakase_charge_ready,
        "omakase_reason_code": str(omakase_reason_code or "").strip(),
        "omakase_message": str(omakase_message or "").strip(),
        "omakase_fallback_options": list(omakase_fallback_options or []),
        "omakase_needs_input_items": list(omakase_needs_input_items or []),
        "omakase_source_count": int(omakase_source_count or 0),
        "omakase_existing_post_count": int(omakase_existing_post_count or 0),
        "omakase_usable_posts_count": int(omakase_usable_posts_count or 0),
        "omakase_dominant_cluster_count": int(omakase_dominant_cluster_count or 0),
        "omakase_available": bool(omakase_available),
    }


def _prepare_current_mainline_generation_request_inputs(
    *,
    interview_answers: Optional[Dict[str, Any]],
    speaker_profile_input: str,
    prompt_raw: str,
) -> Dict[str, Any]:
    normalized_answers = {
        str(key): value
        for key, value in _to_plain_dict(interview_answers).items()
        if value
    }
    normalized_speaker_profile = str(speaker_profile_input or "").strip()
    writer_role_ignored_theme_like = False
    if normalized_speaker_profile and _looks_theme_like_writer_role(normalized_speaker_profile):
        writer_role_ignored_theme_like = True
        normalized_speaker_profile = ""
    return {
        "interview_answers": normalized_answers,
        "interview_answer_keys": sorted(normalized_answers.keys()),
        "interview_answer_count": len(normalized_answers),
        "speaker_profile_input": normalized_speaker_profile,
        "writer_role_ignored_theme_like": writer_role_ignored_theme_like,
        "prompt_raw": str(prompt_raw or "").strip(),
        "retry_memo": [],
    }


def _prepare_current_mainline_interview_state_for_generation(
    *,
    interview_answers: Optional[Dict[str, Any]],
    interview_questions_loaded: bool,
    stored_context_signature: str,
    current_context_signature: str,
) -> Dict[str, Any]:
    normalized_answers = _to_plain_dict(interview_answers)
    normalized_questions_loaded = bool(interview_questions_loaded)
    normalized_stored_signature = str(stored_context_signature or "")
    normalized_current_signature = str(current_context_signature or "")
    reset_required = bool(
        normalized_questions_loaded
        and normalized_stored_signature
        and normalized_stored_signature != normalized_current_signature
    )
    if reset_required:
        normalized_answers = {
            "perspective": None,
            "perspective_mode": None,
            "target": None,
            "message": None,
        }
        normalized_questions_loaded = False
        normalized_stored_signature = ""
    answered_count = 0
    if normalized_questions_loaded:
        interview_question_ids = {"perspective", "perspective_mode", "target", "message"}
        answered_count = sum(
            1
            for key, value in normalized_answers.items()
            if key in interview_question_ids and value
        )
    return {
        "interview_answers": normalized_answers,
        "interview_questions_loaded": normalized_questions_loaded,
        "stored_context_signature": normalized_stored_signature,
        "reset_required": reset_required,
        "answered_count": answered_count,
        "notify_unanswered": bool(normalized_questions_loaded and answered_count == 0),
    }


def _prepare_current_mainline_required_inputs(
    *,
    article_type_key: str,
    semantic_article_key: str = "",
    content_goal_key: str,
    speaker_profile_input: str,
    audience_profile_input: str,
    core_message_input: str,
    tone_profile_key: str,
) -> Dict[str, Any]:
    normalized_speaker_profile = str(speaker_profile_input or "").strip()[:80]
    normalized_audience_profile = (
        str(audience_profile_input or "").strip()
        or _default_audience_profile_text()
    )[:120]
    normalized_core_message = str(core_message_input or "").strip()[:160]
    normalized_tone_profile_key = str(tone_profile_key or "").strip() or "auto"
    normalized_semantic_key = str(semantic_article_key or "").strip()
    missing_required_fields: List[str] = []
    if not normalized_speaker_profile and normalized_semantic_key != "company_introduction":
        missing_required_fields.append("speaker_profile")
    if not normalized_audience_profile:
        missing_required_fields.append("audience_profile")
    return {
        "speaker_profile_input": normalized_speaker_profile,
        "audience_profile_input": normalized_audience_profile,
        "core_message_input": normalized_core_message,
        "tone_profile_key": normalized_tone_profile_key,
        "missing_required_fields": missing_required_fields,
    }


def _resolve_required_input_wizard_step(
    *,
    article_type_ready: bool,
    audience_ready: bool,
    writer_ready: bool,
) -> int:
    if not article_type_ready:
        return 1
    if not audience_ready:
        return 2
    if not writer_ready:
        return 3
    return 4


def _resolve_required_input_wizard_view_state(
    *,
    article_type_ready: bool,
    audience_ready: bool,
    writer_ready: bool,
    audience_committed: bool,
    writer_committed: bool,
    requested_focus: int = 0,
) -> Dict[str, Any]:
    advance_requested = bool(int(requested_focus or 0) >= 3 and article_type_ready and audience_ready)
    normalized_audience_committed = bool(
        (audience_committed or advance_requested) and article_type_ready and audience_ready
    )
    normalized_writer_committed = bool(writer_committed and normalized_audience_committed and writer_ready)
    focus = int(requested_focus or 0)
    if not article_type_ready:
        focused_step = 1
    elif focus == 2 and not normalized_audience_committed:
        focused_step = 2
    elif focus == 3 and normalized_audience_committed and not normalized_writer_committed:
        focused_step = 3
    elif not normalized_audience_committed:
        focused_step = 2
    elif not normalized_writer_committed:
        focused_step = 3
    else:
        focused_step = 4
    return {
        "focused_step": focused_step,
        "audience_committed": normalized_audience_committed,
        "writer_committed": normalized_writer_committed,
        "audience_editor_visible": bool(article_type_ready and focused_step == 2),
        "audience_summary_visible": bool(article_type_ready and normalized_audience_committed and focused_step != 2),
        "writer_editor_visible": bool(article_type_ready and normalized_audience_committed and focused_step == 3),
        "writer_summary_visible": bool(
            article_type_ready and normalized_audience_committed and normalized_writer_committed and focused_step != 3
        ),
    }


def _build_required_input_wizard_helper_text(current_step: int) -> str:
    step = max(1, min(4, int(current_step or 1)))
    messages = {
        1: "STEP2まで選ぶと、STEP3で誰向けかを入力できます。",
        2: "STEP3: まず誰向けの記事かを短く入れてください。",
        3: "STEP4: どの立場で書くかを選ぶと確認へ進めます。",
        4: "前提がそろいました。生成前チェックへ進めます。",
    }
    return messages.get(step, messages[1])


def _apply_required_input_wizard_typing_reset(
    state: Dict[str, Any],
    *,
    focused_step: int,
    clear_audience_commit: bool = False,
    clear_writer_commit: bool = False,
) -> bool:
    """入力中に commit 状態を確実に解除するための単一アトミック state mutator。

    - 実ブラウザの IME composition 中に `update:model-value` / `focus` が多重発火しても、
      STEP3/STEP4 の committed flag が勝手に True 側へ戻らないよう、state 書き換えを 1 経路に固定する。
    - 戻り値: state が変化した場合は True。変化がなければ False（refresh 側で no-op 判定に利用できる）。
    """
    changed = False
    normalized_step = int(focused_step or 0)
    if int(state.get("focused_step") or 0) != normalized_step:
        state["focused_step"] = normalized_step
        changed = True
    if clear_audience_commit and bool(state.get("audience_committed")):
        state["audience_committed"] = False
        changed = True
    if clear_writer_commit and bool(state.get("writer_committed")):
        state["writer_committed"] = False
        changed = True
    return changed


def _default_audience_profile_text() -> str:
    return "一般読者"


def _default_audience_profile_placeholder_text() -> str:
    return "例: 導入検討中の担当者"


def _filter_current_mainline_question_items_for_ui(
    question_items: Iterable[Any] | None,
) -> List[Dict[str, Any]]:
    allowed_fields = {"perspective_mode", "allow_experience"}
    filtered_items: List[Dict[str, Any]] = []
    for item in question_items or []:
        normalized_item = _to_plain_dict(item)
        field = str(normalized_item.get("field") or "").strip()
        if field not in allowed_fields:
            continue
        filtered_items.append(normalized_item)
    return filtered_items


def _build_current_mainline_generation_selection_payload(
    *,
    base_selections: Optional[Dict[str, Any]],
    article_type_key: str,
    selected_article_type_label: str,
    content_goal_key: str,
    writing_focus_key: str,
    structure_key: str,
    length_mode_key: str,
    tone_profile_key: str,
    perspective_key: str,
    allow_experience: bool,
    strict_saas_mode: str,
) -> Dict[str, Any]:
    payload = _to_plain_dict(base_selections)
    payload.update(
        {
            "article_type": str(article_type_key or ""),
            "selected_label": str(selected_article_type_label or ""),
            "content_goal": str(content_goal_key or "auto"),
            "writing_focus": str(writing_focus_key or "auto"),
            "structure": str(structure_key or "auto"),
            "length_mode": str(length_mode_key or "adaptive"),
            "tone_profile": str(tone_profile_key or "auto"),
            "perspective": str(perspective_key or "auto"),
            "allow_experience": bool(allow_experience),
            "strict_saas_mode": str(strict_saas_mode or CURRENT_MAINLINE_STRICT_SAAS_MODE),
        }
    )
    return payload


def _prepare_current_mainline_fetch_summary(
    *,
    contents: List[Any],
    failures: List[Any],
    elapsed_ms: int,
) -> Dict[str, Any]:
    total_source_chars = sum(len(getattr(content, "content", "") or "") for content in contents)
    return {
        "success_count": len(contents),
        "failure_count": len(failures),
        "elapsed_ms": int(elapsed_ms),
        "total_source_chars": total_source_chars,
        "event_extra": {
            "success_count": len(contents),
            "failure_count": len(failures),
            "elapsed_ms": int(elapsed_ms),
            "total_source_chars": total_source_chars,
        },
        "post_delay_notice": _build_generation_delay_notice(len(contents), total_source_chars),
        "failure_details": _format_fetch_failures(failures),
        "blocked_urls": _extract_403_urls(failures),
    }


def _prepare_current_mainline_guard_retry(
    *,
    output_guard: Dict[str, Any],
    guard_retry_count: int,
) -> Dict[str, Any]:
    reason_code = str(_to_plain_dict(output_guard).get("reason_code") or "-")
    retry_memo = [
        str(item).strip()
        for item in _to_plain_list(_to_plain_dict(output_guard).get("reasons"))
        if str(item or "").strip()
    ][:6]
    return {
        "guard_retry_count": int(guard_retry_count) + 1,
        "retry_memo": retry_memo,
        "phase": "auto_retry_guard_repair",
        "phase_detail": f"reason_code={reason_code}",
        "status_text": "品質ガード検知のため自動補修リトライ中...",
        "reason_code": reason_code,
    }


def _build_current_mainline_guard_retry_failure_result(
    *,
    input_contract: Dict[str, Any],
    reason_code: str,
    error_class: str,
    prompt_raw: str,
    system_hint_items: Optional[List[str]],
    retry_memo: Optional[List[str]],
    strict_saas_mode: str,
    question_generation_owner: str = "",
) -> Dict[str, Any]:
    result = build_fail_closed_generation_result(
        input_contract=input_contract,
        reason_code=reason_code,
        error_class=error_class,
    )
    return _attach_prompt_context_to_result(
        result,
        prompt_raw=prompt_raw,
        system_hint_items=system_hint_items,
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        question_generation_owner=question_generation_owner,
    )


_REVIEW_DRAFT_REDACTED_MARKER = "[BLOCKED_OUTPUT_REDACTED]"
_REVIEW_DRAFT_STATUS_TEXT = "確認が必要なドラフトです。公開前に資料と照らし合わせて確認してください。"
_REVIEW_DRAFT_NOTIFY_TEXT = "確認が必要なドラフトです。公開前に資料と照らし合わせて確認してください。"
_REVIEW_DRAFT_SOURCE_ERROR_CONTENT = (
    "- 確認が必要なドラフトです。\n"
    "- 本文は作成できましたが、資料の反映や説明の具体性に確認したい点があります。\n"
    "- コピーや保存はできますが、公開前の確認が必要です。"
)
_REVIEW_DRAFT_ALLOWED_WARNING_PREFIXES = (
    "ai:",
    "ending:",
    "fingerprint:",
    "rhythm:",
    "grammar:editor_repair_applied",
    "source_grounding:weak_reflection",
    "company_intro:fingerprint_flatness",
    "company_intro:naturalness_rescue",
)
_REVIEW_DRAFT_ALLOWED_WARNING_REASONS = (
    "contract_alignment_must_cover_reflection_rate<0.50",
)
_REVIEW_DRAFT_BLOCKED_REASON_MARKERS = (
    "legal",
    "guarantee",
    "unsupported",
    "outside_claim",
    "source_outside",
    "manual",
    "instruction",
    "prompt_injection",
    "contract",
    "must_cover",
    "missing",
    "required",
    "leak",
    "hidden_late_validation",
    "source_contract",
    "forbidden",
    "web_source",
    "speaker_contract",
    "low_proposition",
    "保証",
    "断定",
    "法務",
)
_REVIEW_DRAFT_INTERNAL_TEXT_MARKERS = (
    "source_grounding",
    "fingerprint",
    "SYS_",
    "must_cover",
    "contract_alignment",
    "PATCH_SCOPE",
)


def _extract_current_mainline_result_input_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    normalized_result = _to_plain_dict(result)
    direct_contract = _to_plain_dict(normalized_result.get("input_contract"))
    if direct_contract:
        return direct_contract
    pipeline_check = _to_plain_dict(normalized_result.get("pipeline_check"))
    return _to_plain_dict(pipeline_check.get("input_contract"))


def _current_mainline_result_has_source_input(result: Dict[str, Any]) -> bool:
    normalized_result = _to_plain_dict(result)
    try:
        if int(normalized_result.get("source_count") or 0) > 0:
            return True
    except (TypeError, ValueError):
        pass
    input_contract = _extract_current_mainline_result_input_contract(normalized_result)
    return bool(
        _to_plain_list(input_contract.get("source_documents"))
        or _to_plain_list(input_contract.get("source_inputs"))
        or _to_plain_list(input_contract.get("source"))
    )


def _current_mainline_result_route_matches_contract(result: Dict[str, Any]) -> bool:
    normalized_result = _to_plain_dict(result)
    input_contract = _extract_current_mainline_result_input_contract(normalized_result)
    expected_semantic_key = str(input_contract.get("semantic_article_key") or "").strip()
    actual_semantic_key = str(normalized_result.get("semantic_article_key") or "").strip()
    if expected_semantic_key and actual_semantic_key and expected_semantic_key != actual_semantic_key:
        return False
    return True


def _current_mainline_has_internal_text_marker(*texts: str) -> bool:
    joined = "\n".join(str(text or "") for text in texts)
    return any(marker in joined for marker in _REVIEW_DRAFT_INTERNAL_TEXT_MARKERS)


def _current_mainline_guard_reason_is_reviewable(reason: str) -> bool:
    normalized_reason = str(reason or "").strip()
    lowered = normalized_reason.lower()
    if not normalized_reason:
        return True
    if normalized_reason in _REVIEW_DRAFT_ALLOWED_WARNING_REASONS:
        return True
    if any(marker in lowered or marker in normalized_reason for marker in _REVIEW_DRAFT_BLOCKED_REASON_MARKERS):
        return False
    return any(
        lowered.startswith(prefix.lower()) or lowered == prefix.lower()
        for prefix in _REVIEW_DRAFT_ALLOWED_WARNING_PREFIXES
    )


def _current_mainline_source_reflection_ratio(result: Dict[str, Any], output_guard: Dict[str, Any]) -> Optional[float]:
    normalized_guard = _to_plain_dict(output_guard)
    failed_parameters = _to_plain_dict(normalized_guard.get("failed_parameters"))
    naturalness = _to_plain_dict(failed_parameters.get("contextual_naturalness_report"))
    final_quality = _to_plain_dict(failed_parameters.get("final_quality_eval"))
    final_metrics = _to_plain_dict(final_quality.get("metrics"))
    pipeline_check = _to_plain_dict(_to_plain_dict(result).get("pipeline_check"))
    contract_alignment = _to_plain_dict(
        failed_parameters.get("contract_alignment") or pipeline_check.get("contract_alignment")
    )
    candidates = (
        naturalness.get("source_grounding_reflection_ratio"),
        final_metrics.get("source_grounding_reflection_ratio"),
        contract_alignment.get("source_trace_coverage"),
    )
    for value in candidates:
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _classify_current_mainline_fail_closed_ux(
    result: Dict[str, Any],
    output_guard: Dict[str, Any],
) -> str:
    normalized_result = _to_plain_dict(result)
    normalized_guard = _to_plain_dict(output_guard)
    if not bool(normalized_guard.get("blocked")):
        return "publishable_success"
    if str(normalized_guard.get("reason_code") or "") != "SYS_QUALITY_WARNINGS_UNRESOLVED":
        return "input_required_block"
    if _to_plain_list(normalized_guard.get("hard_reasons")):
        return "input_required_block"
    if _to_plain_list(normalized_guard.get("manual_instructional_hits")):
        return "input_required_block"
    if _to_plain_list(normalized_guard.get("needs_input_items")):
        return "input_required_block"
    if not _current_mainline_result_route_matches_contract(normalized_result):
        return "input_required_block"
    if not _current_mainline_result_has_source_input(normalized_result):
        return "input_required_block"

    title = str(normalized_result.get("title") or "").strip()
    lead = str(normalized_result.get("lead") or "").strip()
    body = str(normalized_result.get("body") or "").strip()
    references = str(normalized_result.get("references") or "").strip()
    if not title or not body or body == _REVIEW_DRAFT_REDACTED_MARKER:
        return "input_required_block"
    if _current_mainline_has_internal_text_marker(title, lead, body, references):
        return "input_required_block"
    if _to_plain_list(normalized_result.get("visible_internal_term_leakage")):
        return "input_required_block"
    if _to_plain_list(normalized_result.get("body_internal_term_leakage")):
        return "input_required_block"
    if bool(normalized_result.get("source_outside_claim_observed")):
        return "input_required_block"

    reasons = [
        str(reason).strip()
        for reason in _to_plain_list(normalized_guard.get("reasons"))
        if str(reason or "").strip()
    ]
    soft_warnings = [
        str(reason).strip()
        for reason in _to_plain_list(normalized_guard.get("soft_warnings"))
        if str(reason or "").strip()
    ]
    review_reasons = reasons or soft_warnings
    if not review_reasons:
        return "input_required_block"
    if any(not _current_mainline_guard_reason_is_reviewable(reason) for reason in review_reasons):
        return "input_required_block"
    if any(str(reason).startswith("source_grounding:") for reason in review_reasons):
        reflection_ratio = _current_mainline_source_reflection_ratio(normalized_result, normalized_guard)
        if reflection_ratio is not None and reflection_ratio <= 0.0:
            return "input_required_block"
    return "review_required_draft"


def _build_current_mainline_review_required_draft_block(
    *,
    result: Dict[str, Any],
    output_guard: Dict[str, Any],
    guard_retry_count: int,
    guard_reasons: List[str],
    manual_hits: List[str],
) -> Dict[str, Any]:
    normalized_result = _to_plain_dict(result)
    normalized_guard = _to_plain_dict(output_guard)
    patched_result = dict(normalized_result)
    patched_result["success"] = bool(normalized_result.get("success", False))
    patched_result["ui_fail_closed_ux_classification"] = "review_required_draft"
    patched_result["ui_review_required_draft"] = True
    patched_result["runtime_error_class"] = str(normalized_guard.get("error_class") or "system")
    patched_result["runtime_reason_code"] = str(
        normalized_guard.get("reason_code")
        or normalized_result.get("runtime_reason_code")
        or "SYS_QUALITY_WARNINGS_UNRESOLVED"
    )
    patched_result["reason_code"] = patched_result["runtime_reason_code"]
    patched_result["output_guard_blocked"] = True
    patched_result["output_guard_warning_only"] = False
    patched_result["ui_quality_warnings"] = _to_plain_list(normalized_guard.get("soft_warnings"))
    patched_result["output_guard_warnings"] = _to_plain_list(normalized_guard.get("soft_warnings"))

    title = str(normalized_result.get("title") or "").strip()
    lead = str(normalized_result.get("lead") or "").strip()
    body = str(normalized_result.get("body") or "").strip()
    references = str(normalized_result.get("references") or "").strip()
    hashtags_plain = _hashtags_to_plain(str(normalized_result.get("hashtags") or ""))
    note_body_text = "\n\n".join(part for part in (lead, body, references) if part).strip()
    full_text_parts = [title, note_body_text]
    if hashtags_plain:
        full_text_parts.extend(["---", hashtags_plain])
    full_text = "\n\n".join(part for part in full_text_parts if part).strip()
    patched_result["full_body"] = note_body_text
    patched_result["full_text"] = full_text
    patched_result["blocked_output_redacted"] = False

    return {
        "result": patched_result,
        "render_fields": {
            "title": title,
            "lead": lead,
            "body": body,
            "references": references,
            "hashtags_plain": hashtags_plain,
            "full_text": full_text,
            "note_body_text": note_body_text,
            "preview_text": full_text,
            "linkedin_text": str(normalized_result.get("linkedin_text") or ""),
            "linkedin_short_text": _build_short_sns_text(str(normalized_result.get("linkedin_text") or "")),
        },
        "guard_reason_log_text": ",".join(guard_reasons) or "-",
        "manual_hit_count": len(manual_hits),
        "error_class": str(normalized_guard.get("error_class") or "system"),
        "reason_code": str(normalized_guard.get("reason_code") or "SYS_QUALITY_WARNINGS_UNRESOLVED"),
        "needs_input_items": [],
        "source_error_content": _REVIEW_DRAFT_SOURCE_ERROR_CONTENT,
        "status_text": _REVIEW_DRAFT_STATUS_TEXT,
        "outcome": "review_required_draft",
        "notify_text": _REVIEW_DRAFT_NOTIFY_TEXT,
        "notify_color": "warning",
        "event_extra": {
            "fail_closed_ux_classification": "review_required_draft",
            "guard_reason_count": len(guard_reasons),
            "manual_hit_count": len(manual_hits),
            "guard_retry_count": int(guard_retry_count),
            "copy_save_warning": True,
        },
    }


def _prepare_current_mainline_output_guard_block(
    *,
    result: Dict[str, Any],
    output_guard: Dict[str, Any],
    guard_retry_count: int,
    blocked_view_builder: Callable[..., Dict[str, Any]] = _build_current_mainline_output_guard_blocked_view,
) -> Dict[str, Any]:
    normalized_output_guard = _to_plain_dict(output_guard)
    error_class = str(normalized_output_guard.get("error_class") or "system")
    reason_code = str(normalized_output_guard.get("reason_code") or "SYS_QUALITY_GATE_HARD_FAIL")
    normalized_output_guard.setdefault("error_class", error_class)
    normalized_output_guard.setdefault("reason_code", reason_code)
    guard_reasons = [
        str(reason)
        for reason in _to_plain_list(normalized_output_guard.get("reasons"))
    ]
    manual_hits = [
        str(hit)
        for hit in _to_plain_list(normalized_output_guard.get("manual_instructional_hits"))
    ]
    fail_closed_ux_classification = _classify_current_mainline_fail_closed_ux(
        result,
        normalized_output_guard,
    )
    if fail_closed_ux_classification == "review_required_draft":
        return _build_current_mainline_review_required_draft_block(
            result=result,
            output_guard=normalized_output_guard,
            guard_retry_count=guard_retry_count,
            guard_reasons=guard_reasons,
            manual_hits=manual_hits,
        )
    blocked_view = _to_plain_dict(
        blocked_view_builder(
            normalized_output_guard,
            guard_retry_count=guard_retry_count,
        )
    )
    patched_result = dict(result)
    patched_result.update(_to_plain_dict(blocked_view.get("result_patch")))
    return {
        "result": patched_result,
        "guard_reason_log_text": ",".join(guard_reasons) or "-",
        "manual_hit_count": len(manual_hits),
        "error_class": str(blocked_view.get("error_class") or error_class),
        "reason_code": str(blocked_view.get("reason_code") or reason_code),
        "needs_input_items": _to_plain_list(blocked_view.get("needs_input_items")),
        "source_error_content": str(blocked_view.get("source_error_content") or ""),
        "status_text": str(blocked_view.get("status_text") or ""),
        "outcome": str(blocked_view.get("outcome") or "blocked_quality_guard"),
        "notify_text": str(
            blocked_view.get("notify_text") or "生成結果に重大な不整合があったため表示を停止しました。"
        ),
        "notify_color": str(blocked_view.get("notify_color") or "negative"),
        "event_extra": {
            **_to_plain_dict(blocked_view.get("event_extra")),
            "fail_closed_ux_classification": fail_closed_ux_classification,
        },
    }


def _prepare_current_mainline_completion_payload(
    *,
    success_view: Dict[str, Any],
    completion_view: Dict[str, Any],
    note_body_text: str,
    linkedin_text: str,
    quality_warning_only: bool,
    elapsed_ms: int,
) -> Dict[str, Any]:
    return build_current_mainline_completion_payload_core(
        success_view=success_view,
        completion_view=completion_view,
        note_body_text=note_body_text,
        linkedin_text=linkedin_text,
        quality_warning_only=quality_warning_only,
        elapsed_ms=elapsed_ms,
    )


def _apply_current_mainline_completion_payload(
    *,
    completion_payload: Dict[str, Any],
    stats_label: Any,
    quality_summary_card: Any,
    quality_summary_badge: Any,
    quality_summary_title: Any,
    quality_summary_note: Any,
    quality_summary_row_widgets: List[Dict[str, Any]],
    review_kousei_label: Any,
    review_row_kousei: Any,
    review_buntai_label: Any,
    review_row_buntai: Any,
    review_konkyo_label: Any,
    review_row_konkyo: Any,
    review_container: Any,
    status_label: Any,
) -> None:
    normalized_completion_payload = _to_plain_dict(completion_payload)
    stats_label.text = str(normalized_completion_payload.get("stats_text") or "")

    review_sections = _to_plain_dict(normalized_completion_payload.get("review_sections"))
    review_rows = _to_plain_dict(normalized_completion_payload.get("review_rows"))

    def _apply_review_row(row_key: str, label_widget: Any, row_widget: Any) -> None:
        review_row = _to_plain_dict(review_rows.get(row_key))
        fallback_text = str(review_sections.get(row_key) or "")
        label_widget.text = str(review_row.get("text") or fallback_text)
        row_widget.visible = bool(review_row.get("visible") if review_row else fallback_text)

    _apply_review_row("構成", review_kousei_label, review_row_kousei)
    _apply_review_row("文体", review_buntai_label, review_row_buntai)
    _apply_review_row("根拠", review_konkyo_label, review_row_konkyo)

    quality_warning_summary = _to_plain_dict(normalized_completion_payload.get("quality_warning_summary"))
    quality_summary_badge.text = str(quality_warning_summary.get("badge_text") or "")
    quality_summary_title.text = str(quality_warning_summary.get("title") or "")
    quality_summary_note.text = str(quality_warning_summary.get("note") or "")
    quality_summary_rows = [
        _to_plain_dict(item)
        for item in _to_plain_list(quality_warning_summary.get("rows"))
    ]
    for widget, row in zip(quality_summary_row_widgets, quality_summary_rows):
        widget["title"].text = str(row.get("headline") or "")
        widget["detail"].text = str(row.get("detail") or "")
        widget["codes"].text = str(row.get("codes") or "")
        widget["row"].visible = True
    for widget in quality_summary_row_widgets[len(quality_summary_rows):]:
        widget["title"].text = ""
        widget["detail"].text = ""
        widget["codes"].text = ""
        widget["row"].visible = False
    quality_summary_card.visible = bool(quality_warning_summary.get("visible"))
    review_container.visible = bool(normalized_completion_payload.get("review_visible"))
    status_label.text = str(normalized_completion_payload.get("status_text") or "")


def _apply_current_mainline_complete_plan(
    *,
    complete_plan: Dict[str, Any],
    generation_progress: Any,
    reset_pdf_assist: Callable[[], None],
    pdf_assist_status_label: Any,
    pdf_assist_panel: Any,
) -> None:
    normalized_complete_plan = _to_plain_dict(complete_plan)
    generation_progress.value = float(normalized_complete_plan.get("generation_progress_value", 1.0) or 1.0)
    if bool(normalized_complete_plan.get("reset_pdf_assist", False)):
        reset_pdf_assist()
    pdf_assist_status_label.text = str(normalized_complete_plan.get("pdf_assist_status_text") or "")
    if bool(normalized_complete_plan.get("refresh_pdf_assist_panel", False)):
        pdf_assist_panel.refresh()


def _format_generation_progress_text(
    *,
    percent: Any,
    label_text: str,
    detail: str = "",
    elapsed: str = "",
) -> str:
    bounded = _coerce_display_generation_percent(percent)
    parts = ["進行状況:", f"{bounded}%"]
    normalized_label = str(label_text or "").strip()
    normalized_detail = str(detail or "").strip()
    normalized_elapsed = str(elapsed or "").strip()
    if normalized_label:
        parts.append(normalized_label)
    if normalized_detail:
        parts.append(normalized_detail)
    if normalized_elapsed:
        parts.append(normalized_elapsed)
    return " ".join(parts).strip()


def _coerce_display_generation_percent(value: Any) -> int:
    try:
        numeric = float(value if value is not None else 0.0)
    except (TypeError, ValueError):
        numeric = 0.0
    if 0.0 <= numeric <= 1.0 and (
        isinstance(value, float) or "." in str(value)
    ):
        numeric *= 100.0
    return max(0, min(100, int(round(numeric))))


def _resolve_display_generation_percent(*, current_value: Any, reported_percent: Any) -> int:
    current_percent = _coerce_display_generation_percent(current_value)
    bounded_reported = _coerce_display_generation_percent(reported_percent)
    return max(current_percent, bounded_reported)


def _prepare_current_mainline_completion_terminal_payload(
    *,
    completion_payload: Dict[str, Any],
    status_label_text: str,
    note_body_char_count: int,
    linkedin_char_count: int,
    quality_warning_only: bool,
) -> Dict[str, Any]:
    normalized_completion_payload = _to_plain_dict(completion_payload)
    event_extra = _to_plain_dict(normalized_completion_payload.get("event_extra"))
    return {
        "outcome": str(normalized_completion_payload.get("outcome") or "success"),
        "log_note_body_chars": int(note_body_char_count),
        "log_linkedin_chars": int(linkedin_char_count),
        "log_quality_warning_only": bool(quality_warning_only),
        "log_elapsed_ms": int(event_extra.get("elapsed_ms") or 0),
        "event_status_text": str(
            status_label_text or normalized_completion_payload.get("status_text") or ""
        ),
        "event_extra": event_extra,
        "notify_text": str(normalized_completion_payload.get("notify_text") or "生成が完了しました"),
        "notify_color": str(normalized_completion_payload.get("notify_color") or "positive"),
    }


def _prepare_current_mainline_exception_terminal_payload(
    *,
    exception_plan: Dict[str, Any],
    exc: Exception,
    outcome: str,
) -> Dict[str, Any]:
    normalized_exception_plan = _to_plain_dict(exception_plan)
    status_text = str(normalized_exception_plan.get("status_text") or "")
    return {
        "outcome": str(outcome or "error_exception"),
        "status_text": status_text,
        "generation_progress_note_text": str(
            normalized_exception_plan.get("generation_progress_note_text") or ""
        ),
        "generation_progress_note_visible": bool(
            normalized_exception_plan.get("generation_progress_note_visible")
        ),
        "notify_text": str(normalized_exception_plan.get("notify_text") or ""),
        "notify_color": str(normalized_exception_plan.get("notify_color") or "negative"),
        "event_status_text": status_text,
        "event_extra": {"exception": str(exc)},
    }


def _apply_current_mainline_exception_terminal_payload(
    *,
    exception_terminal_payload: Dict[str, Any],
    status_label: Any,
    generation_progress_note: Any,
) -> None:
    normalized_exception_terminal_payload = _to_plain_dict(exception_terminal_payload)
    status_label.text = str(normalized_exception_terminal_payload.get("status_text") or "")
    generation_progress_note.text = str(
        normalized_exception_terminal_payload.get("generation_progress_note_text") or ""
    )
    generation_progress_note.visible = bool(
        normalized_exception_terminal_payload.get("generation_progress_note_visible")
    )


def _prepare_current_mainline_render_payload(
    *,
    success_view: Dict[str, Any],
    render_fields: Dict[str, Any],
) -> Dict[str, Any]:
    normalized_success_view = _to_plain_dict(success_view)
    normalized_render_fields = _to_plain_dict(render_fields)
    return {
        "title": str(normalized_render_fields.get("title") or normalized_success_view.get("title") or ""),
        "lead": str(normalized_render_fields.get("lead") or normalized_success_view.get("lead") or ""),
        "body": str(normalized_render_fields.get("body") or normalized_success_view.get("body") or ""),
        "references": str(
            normalized_render_fields.get("references") or normalized_success_view.get("references") or ""
        ),
        "hashtags_plain": str(
            normalized_render_fields.get("hashtags_plain")
            or normalized_success_view.get("hashtags_plain")
            or ""
        ),
        "full_text": str(
            normalized_render_fields.get("full_text") or normalized_success_view.get("full_text") or ""
        ),
        "note_body_text": str(
            normalized_render_fields.get("note_body_text")
            or normalized_success_view.get("note_body_text")
            or ""
        ),
        "preview_text": str(
            normalized_render_fields.get("preview_text")
            or normalized_success_view.get("preview_text")
            or ""
        ),
        "linkedin_text": str(
            normalized_render_fields.get("linkedin_text")
            or normalized_success_view.get("linkedin_text")
            or ""
        ),
        "linkedin_short_text": str(
            normalized_render_fields.get("linkedin_short_text")
            or normalized_success_view.get("linkedin_short_text")
            or ""
        ),
        "render_status_text": str(
            normalized_success_view.get("render_status_text") or "生成結果をUIに反映しました。"
        ),
        "render_event_extra": _to_plain_dict(normalized_success_view.get("render_event_extra")),
    }


def _prepare_current_mainline_legal_postcheck_payload(
    *,
    auto_legal_postcheck: Dict[str, Any],
    note_body_text: str,
) -> Dict[str, Any]:
    return build_current_mainline_legal_postcheck_payload_core(
        auto_legal_postcheck=auto_legal_postcheck,
        note_body_text=note_body_text,
    )


def _prepare_route_0506_post_success_result(
    *,
    route_0506_result: Mapping[str, Any],
    input_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    normalized_result = _to_plain_dict(route_0506_result)
    normalized_contract = dict(input_contract or {})
    body = str(normalized_result.get("body") or normalized_result.get("full_text") or "")
    full_text = str(normalized_result.get("full_text") or body)
    pipeline_check = _to_plain_dict(normalized_result.get("pipeline_check"))
    pipeline_check.setdefault("input_contract", normalized_contract)
    result = dict(normalized_result)
    result.update(
        {
            "route_id": str(normalized_result.get("route_id") or ROUTE_0506_ID),
            "article_type": str(
                normalized_result.get("article_type")
                or normalized_contract.get("article_type")
                or ""
            ),
            "semantic_article_key": str(
                normalized_result.get("semantic_article_key")
                or normalized_contract.get("semantic_article_key")
                or ""
            ),
            "ui_journey": dict(
                normalized_result.get("ui_journey")
                or normalized_contract.get("ui_journey")
                or {}
            ),
            "title": str(normalized_result.get("title") or ""),
            "lead": str(normalized_result.get("lead") or ""),
            "body": body,
            "full_text": full_text,
            "pipeline_check": pipeline_check,
            "post_success_downstream": {
                "source_route_id": ROUTE_0506_ID,
                "legal_postcheck_eligible": bool(body),
                "image_generation_eligible": bool(body),
                "route_a_fallback_used": False,
            },
        }
    )
    return result


def _prepare_current_mainline_cleanup_payload(
    *,
    cleanup_plan: Dict[str, Any],
    outcome: str,
    phase: str,
    elapsed_ms: int,
) -> Dict[str, Any]:
    normalized_cleanup_plan = _to_plain_dict(cleanup_plan)
    return {
        "deactivate_generation_progress_timer": bool(
            normalized_cleanup_plan.get("deactivate_generation_progress_timer", False)
        ),
        "spinner_visible": bool(normalized_cleanup_plan.get("spinner_visible", False)),
        "generation_progress_visible": bool(
            normalized_cleanup_plan.get("generation_progress_visible", False)
        ),
        "generation_progress_value": float(
            normalized_cleanup_plan.get("generation_progress_value", 0.0) or 0.0
        ),
        "busy": bool(normalized_cleanup_plan.get("busy", False)),
        "refresh_step_indicators": bool(
            normalized_cleanup_plan.get("refresh_step_indicators", False)
        ),
        "enable_generate_button": bool(normalized_cleanup_plan.get("enable_generate_button", False)),
        "generate_button_text": str(normalized_cleanup_plan.get("generate_button_text") or "記事を生成"),
        "finish_log": {
            "outcome": str(outcome or ""),
            "phase": str(phase or ""),
            "elapsed_ms": int(elapsed_ms),
        },
    }


def _apply_current_mainline_cleanup_payload(
    *,
    cleanup_payload: Dict[str, Any],
    generation_progress_timer: Any,
    spinner: Any,
    generation_progress: Any,
    state_obj: Any,
    refresh_step_indicators: Callable[[], None],
    generate_button: Any,
) -> None:
    normalized_cleanup_payload = _to_plain_dict(cleanup_payload)
    if bool(normalized_cleanup_payload.get("deactivate_generation_progress_timer")):
        generation_progress_timer.deactivate()
    spinner.visible = bool(normalized_cleanup_payload.get("spinner_visible"))
    generation_progress.visible = bool(normalized_cleanup_payload.get("generation_progress_visible"))
    generation_progress.value = float(normalized_cleanup_payload.get("generation_progress_value", 0.0) or 0.0)
    state_obj.busy = bool(normalized_cleanup_payload.get("busy"))
    if bool(normalized_cleanup_payload.get("refresh_step_indicators")):
        refresh_step_indicators()
    if bool(normalized_cleanup_payload.get("enable_generate_button")):
        generate_button.enable()
    generate_button.text = str(normalized_cleanup_payload.get("generate_button_text") or "記事を生成")


async def _execute_current_mainline_generation_with_context(
    *,
    io_bound_runner: Callable[..., Any],
    pipeline_instance: Any,
    input_contract: Dict[str, Any],
    prompt_raw: str,
    system_hint_items: Optional[List[str]],
    retry_memo: Optional[List[str]],
    strict_saas_mode: str,
    question_generation_owner: str = "",
    executor: Callable[..., Dict[str, Any]] = execute_current_mainline_generation,
) -> Dict[str, Any]:
    result = await io_bound_runner(
        executor,
        pipeline_instance,
        input_contract,
        prompt_raw,
    )
    return _attach_prompt_context_to_result(
        result,
        prompt_raw=prompt_raw,
        system_hint_items=system_hint_items,
        retry_memo=retry_memo,
        strict_saas_mode=strict_saas_mode,
        question_generation_owner=question_generation_owner,
    )


def _persist_current_mainline_generation_snapshot_fail_open(
    *,
    telemetry_context: Dict[str, Any],
    result: Dict[str, Any],
    source_count: int,
    blocked: bool = False,
    failure_kind: str = "latest_generation",
    persist_fn: Callable[..., Any] = _persist_current_mainline_generation_snapshot_from_context,
) -> None:
    try:
        persist_fn(
            telemetry_context=telemetry_context,
            result=result,
            source_count=source_count,
            blocked=blocked,
        )
    except Exception as exc:
        attempt_id = str(_to_plain_dict(telemetry_context).get("attempt_id") or "-")
        if failure_kind == "failed_generation":
            logger.warning("Failed to save failed generation snapshot id=%s: %s", attempt_id, exc)
        elif failure_kind == "blocked_generation":
            logger.warning("Failed to save blocked generation snapshot id=%s: %s", attempt_id, exc)
        elif failure_kind == "guard_retry_failure":
            logger.debug("Failed to persist guard retry failure snapshot", exc_info=True)
        else:
            logger.warning("Failed to save latest generation snapshot id=%s: %s", attempt_id, exc)


async def _build_generated_image_prompt_value(
    *,
    generator: Any,
    contents: List[Any],
    user_prompt_text: str,
    title: str,
    lead: str,
    body: str,
    io_bound_runner: Callable[..., Any],
    image_count: int = DEFAULT_IMAGE_COUNT,
    image_pattern_key: str = DEFAULT_IMAGE_PATTERN_KEY,
) -> str:
    try:
        image_prompts = await io_bound_runner(
            generator.generate_image_prompts,
            contents,
            user_prompt_text,
            title,
            lead,
            body,
            image_count,
            "initial_top_candidates",
        )
        if image_prompts:
            localized_prompts = []
            for prompt_text in image_prompts:
                localized = await io_bound_runner(generator.to_japanese_image_prompt, prompt_text)
                localized_prompts.append(
                    _apply_image_pattern_to_prompt(
                        localized or prompt_text,
                        image_pattern_key,
                        language="ja",
                    )
                )
            return "\n\n---\n\n".join(localized_prompts)
    except Exception:
        logger.debug("Failed to generate image prompts via LLM", exc_info=True)
    return _build_image_prompt(title, lead, pattern_key=image_pattern_key)


async def _run_current_mainline_image_prompt_step(
    *,
    image_prompt_input: Any,
    generator: Any,
    contents: List[Any],
    user_prompt_text: str,
    result: Dict[str, Any],
    io_bound_runner: Callable[..., Any],
    image_count: int = DEFAULT_IMAGE_COUNT,
    image_pattern_key: str = DEFAULT_IMAGE_PATTERN_KEY,
    image_prompt_builder: Optional[Callable[..., Any]] = None,
) -> str:
    normalized_result = _to_plain_dict(result)
    title = str(normalized_result.get("title") or "")
    lead = str(normalized_result.get("lead") or "")
    fallback_prompt = _build_image_prompt(title, lead, pattern_key=image_pattern_key)
    builder = image_prompt_builder or _build_generated_image_prompt_value

    try:
        prompt_value = await builder(
            generator=generator,
            contents=contents,
            user_prompt_text=user_prompt_text,
            title=title,
            lead=lead,
            body=str(normalized_result.get("body") or ""),
            io_bound_runner=io_bound_runner,
            image_count=image_count,
            image_pattern_key=image_pattern_key,
        )
    except Exception:
        logger.debug("Failed to resolve current mainline image prompt step", exc_info=True)
        prompt_value = fallback_prompt

    resolved_prompt_value = str(prompt_value or "").strip() or fallback_prompt
    image_prompt_input.value = resolved_prompt_value
    return resolved_prompt_value


async def _resolve_current_mainline_auto_legal_postcheck(
    *,
    result: Dict[str, Any],
    note_body_text: str,
    verified_texts: List[str],
    io_bound_runner: Callable[..., Any],
    auto_enabled: bool,
) -> Dict[str, Any]:
    note_body_value = str(note_body_text or "")
    if not auto_enabled:
        return {
            "legal_result": {},
            "legal_input_text": note_body_value,
            "legal_status_text": "生成後チェックは保守モードで自動実行を停止中（手動実行可）",
            "usage_action": "auto_run_skipped",
            "usage_reason": "maintenance_mode",
            "usage_risk_level": "",
        }

    legal_result = _to_plain_dict(result.get("legal_postcheck"))
    if legal_result:
        return {
            "legal_result": legal_result,
            "legal_input_text": note_body_value,
            "legal_status_text": "生成後チェック済み",
            "usage_action": "auto_run",
            "usage_reason": "",
            "usage_risk_level": str(legal_result.get("risk_level", "none") or "none"),
        }

    fallback_legal = await io_bound_runner(
        run_legal_postcheck,
        note_body_value,
        verified_texts,
    )
    fallback_result = _to_plain_dict(fallback_legal)
    return {
        "legal_result": fallback_result,
        "legal_input_text": note_body_value,
        "legal_status_text": "生成後チェック済み（再計算）",
        "usage_action": "auto_run",
        "usage_reason": "",
        "usage_risk_level": str(fallback_result.get("risk_level", "none") or "none"),
    }


# _split_image_prompts は image_prompt_helpers.py に分離済み。


def _add_source(label: str, value: str, source_type: str) -> bool:
    prepared = prepare_source_add(
        label=label,
        value=value,
        source_type=source_type,
        existing_values=[s.value for s in state.sources],
    )
    value = prepared.normalized_value
    if not prepared.accepted:
        if prepared.reason == "empty_value":
            logger.warning("Source add rejected: reason=empty_value source_type=%s", source_type)
            ui.notify("値を入力してください", color="negative")
            return False
        if prepared.reason == "invalid_url_scheme":
            logger.warning("Source add rejected: reason=invalid_url_scheme source_type=%s value=%s", source_type, value)
            ui.notify("有効なURLプロトコル(http/https)を入力してください", color="negative")
            return False
        if prepared.reason == "duplicate":
            logger.info("Source add skipped: reason=duplicate source_type=%s value=%s", source_type, value)
            ui.notify("同じソースが追加されています", color="warning")
            return False
        logger.warning("Source add rejected: reason=empty_value source_type=%s", source_type)
        return False

    if prepared.item is None:
        logger.warning("Source add rejected: reason=missing_item_payload source_type=%s value=%s", source_type, value)
        return False

    state.sources.append(
        SourceItem(
            id=prepared.item.id,
            label=prepared.item.label,
            value=prepared.item.value,
            source_type=prepared.item.source_type,
        )
    )
    state.source_session_restored = False
    _snapshot_current_source_session(state)
    logger.info("Source added: source_type=%s value=%s", source_type, value)
    sources_container.refresh()
    callback = getattr(state, "step_refresh_callback", None)
    if callable(callback):
        try:
            callback()
        except Exception:
            pass
    return True


def _remove_source(source_id: str) -> None:
    state.sources = remove_source_by_id(state.sources, source_id)
    if not state.sources:
        _clear_source_session_sources(_get_or_create_state())
    else:
        _snapshot_current_source_session(state)
    sources_container.refresh()
    callback = getattr(state, "step_refresh_callback", None)
    if callable(callback):
        try:
            callback()
        except Exception:
            pass


def _restore_recent_uploaded_sources(max_age_sec: int = 600) -> int:
    """Recover recently uploaded files when source list is unexpectedly empty."""
    if state.sources:
        return 0
    recovered_drafts = build_recent_uploaded_source_drafts(
        upload_dir=UPLOAD_DIR,
        existing_values=[s.value for s in state.sources],
        image_extensions=IMAGE_EXTENSIONS,
        max_age_sec=max_age_sec,
    )
    for draft in recovered_drafts:
        state.sources.append(
            SourceItem(
                id=draft.id,
                label=draft.label,
                value=draft.value,
                source_type=draft.source_type,
            )
        )

    if recovered_drafts:
        _mark_source_session_review_required(_get_or_create_state(), reason="restored_recent_uploads")
        _snapshot_current_source_session(_get_or_create_state())
        sources_container.refresh()
    return len(recovered_drafts)


def _cleanup_old_upload_files(max_age_sec: int = 24 * 60 * 60) -> int:
    """Delete stale upload artifacts to avoid reusing old sources across sessions."""
    stale_paths = select_stale_upload_paths(upload_dir=UPLOAD_DIR, max_age_sec=max_age_sec)
    return remove_upload_paths(stale_paths)


_removed_stale_uploads = _cleanup_old_upload_files()
if _removed_stale_uploads > 0:
    logger.info("Removed stale uploads on startup: %s", _removed_stale_uploads)


async def _handle_upload(e) -> None:
    try:
        payload = await extract_upload_payload(e)
    except Exception:
        logger.exception("Upload payload extraction failed")
        ui.notify("ファイル取り込みに失敗しました。ページ再読み込み後に再試行してください。", color="negative")
        return

    try:
        saved_upload = await save_uploaded_payload(
            upload_dir=UPLOAD_DIR,
            original_name=payload.original_name,
            data=payload.data,
            image_extensions=IMAGE_EXTENSIONS,
            io_bound_runner=run.io_bound,
        )
    except TypeError:
        ui.notify("アップロードデータ形式が不正です。", color="negative")
        return
    except ValueError as exc:
        ui.notify(str(exc), color="negative")
        return

    added = _add_source(payload.original_name, str(saved_upload.destination), saved_upload.source_type)
    if added:
        ui.notify(f"アップロード完了: {saved_upload.safe_name}（追加済みソースに登録しました）", color="primary")
    else:
        ui.notify(f"ファイル保存のみ完了: {saved_upload.safe_name}（ソース追加は未反映）", color="warning")


register_note_writer_app_colors(app)
register_note_writer_app_base_head_html(ui)
register_note_writer_app_sticky_step_head_html(ui)


@ui.page("/")
def main_page() -> None:
    client_key = _current_client_key()
    # Recreated pages can leave stale timers behind; clear them before mounting new UI.
    _deactivate_client_timers(client_key)
    _activate_client_scope(client_key)
    _get_or_create_state(client_key)
    _get_or_create_generator(client_key)
    client = getattr(ui.context, "client", None)
    if client:
        client.on_disconnect(lambda key=client_key: _release_client_scope(key))

    with ui.column().classes("app-shell"):
        ui.html(f'''
            <nav class="hub-nav">
              <a href="{HUB_URL}" class="hub-nav-home">HOME</a>
              <span class="hub-nav-sep">|</span>
              <a href="{KOTOMAKE_URL}" class="hub-nav-active">発信作成</a>
              <span class="hub-nav-sep">|</span>
              <a href="{KOTOMEGANE_URL}">見え方観測</a>
              <span class="hub-nav-sep">|</span>
              <a href="{KOTOMIGAKI_URL}">サイト改善</a>
            </nav>
        ''', sanitize=HTML_SANITIZER.sanitize)
        # API Key Validation Check
        if not os.getenv("OPENAI_API_KEY"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("error_outline").classes("text-red-500 text-xl")
                ui.label("Critical Error: OPENAI_API_KEY not found").classes("text-red-500 font-bold text-xl")
            ui.label("Please create a .env file with your API key.").classes("text-red-500")
            ui.label("Example: OPENAI_API_KEY=sk-...").classes("text-gray-600 text-sm")
            return

        render_brand_header(
            hub_url=HUB_URL,
            kotomegane_url=KOTOMEGANE_URL,
            sanitize_html=HTML_SANITIZER.sanitize,
        )

        source_mode_options = {
            key: label
            for key, label in SOURCE_MODE_LABELS.items()
        }
        source_mode_select = None
        source_mode_helper_label = None
        source_mode_choice_cards: Dict[str, Any] = {}
        input_stage_helper_label = None
        announcement_inline_error_label = None
        user_prompt = None
        user_prompt_helper_label = None
        prompt_input_section = None
        source_inputs_section = None
        source_inputs_title_label = None
        source_inputs_helper_label = None
        omakase_status_card = None
        omakase_status_title = None
        omakase_status_message = None
        omakase_status_inventory = None
        omakase_status_detail = None

        step_track_widgets = render_step_track(current_mainline_ui_mode=CURRENT_MAINLINE_UI_MODE)
        step_track = step_track_widgets["step_track"]
        sticky_step1 = step_track_widgets["sticky_step1"]
        sticky_step2 = step_track_widgets["sticky_step2"]
        sticky_step3 = step_track_widgets["sticky_step3"]

        with ui.card().classes("card p-5 w-full fade-in step-card-1 input-stage-card"):
            with ui.row().classes("items-center gap-2 mb-1"):
                step1_badge = ui.label("入力").classes("text-xs font-bold bg-orange-500 text-white px-2 py-0.5 rounded tracking-widest")
                ui.label("開始方式と材料").classes("section-title m-0")
            input_stage_helper_label = ui.label(
                "開始方式を選び、資料ありでは材料を先にそろえます。テーマは補足したいときだけ入れます。"
            ).classes("text-sm text-gray-600")

            ui.label("開始方式").classes("text-sm font-semibold text-gray-700 mt-1")
            source_mode_choice_cards = render_source_mode_choice_cards()

            source_mode_select = ui.select(
                options=list(source_mode_options.values()),
                value=source_mode_options["grounded"],
                label="開始方式",
            ).classes("w-full").props("outlined stack-label")
            source_mode_select.visible = False
            source_mode_helper_label = ui.label(
                "資料ありモードです。URL / PDF / 画像 / テキストをすぐ下から追加して使います。"
            ).classes("text-xs text-gray-600 -mt-1 pl-1")
            with ui.column().classes("w-full gap-1") as prompt_input_section:
                user_prompt = ui.input(
                    label="補足テーマ（任意）",
                    placeholder="例: 初回投稿向けに会社の輪郭が自然に伝わる記事にしたい",
                ).classes("w-full").props("outlined stack-label clearable")
                user_prompt_helper_label = ui.label(
                    "資料だけでも進められます。切り口や重視点を補足したいときだけ1行で入れます。"
                ).classes("text-xs text-gray-600")
                announcement_inline_error_label = ui.label("").classes("text-xs text-amber-700")
                announcement_inline_error_label.visible = False
            prompt_input_section.visible = False

            with ui.card().classes("w-full p-3 gap-1").style(
                "border: 1px solid rgba(72,58,50,0.10); background: #FFF9F5;"
            ) as omakase_status_card:
                ui.label("お任せの開始状況").classes("text-xs font-semibold text-[#7A5544]")
                omakase_status_title = ui.label("").classes("text-sm font-semibold text-[#5D4A41]")
                omakase_status_message = ui.label("").classes("text-xs text-gray-700")
                omakase_status_inventory = ui.label("").classes("text-xs text-gray-600")
                omakase_status_detail = ui.label("").classes("text-xs text-amber-700")
            omakase_status_card.visible = False

            with ui.column().classes("w-full gap-3 mt-2") as source_inputs_section:
                source_inputs_title_label = ui.label("必須の資料入力").classes("text-sm font-semibold text-gray-700")
                source_inputs_helper_label = ui.label(
                    "資料ありではこちらが必須です。URL / PDF / 画像 / テキストを1件以上追加してください。"
                ).classes("text-xs text-gray-600")

                with ui.row().classes("w-full items-center gap-2"):
                    url_input = ui.input(
                        "ソースURL",
                        placeholder="例: https://www.example.com/article"
                    ).classes("w-full").props("outlined stack-label")

                    async def add_url_and_clear():
                        """URL追加後に入力欄をクリア（robots.txtチェック付き）"""
                        attempt_id = _new_operation_id("urladd")
                        value = (url_input.value or "").strip()
                        logger.info("URL add requested id=%s url=%s", attempt_id, value)
                        if not value:
                            logger.warning("URL add rejected id=%s reason=empty_value", attempt_id)
                            ui.notify("値を入力してください", color="negative")
                            return
                        if not value.startswith(("http://", "https://")):
                            logger.warning("URL add rejected id=%s reason=invalid_url_scheme url=%s", attempt_id, value)
                            ui.notify("有効なURLプロトコル(http/https)を入力してください", color="negative")
                            return
                        if any(s.value == value for s in state.sources):
                            logger.info("URL add skipped id=%s reason=duplicate url=%s", attempt_id, value)
                            ui.notify("同じソースが追加されています", color="warning")
                            return

                        valid, reason = await run.io_bound(fetcher.validate_url, value)
                        if not valid:
                            logger.warning(
                                "URL add rejected id=%s reason=validation_failed url=%s detail=%s",
                                attempt_id,
                                value,
                                reason,
                            )
                            ui.notify(f"URLを追加できません: {reason}", color="negative")
                            return

                        if _add_source(value, value, "url"):
                            logger.info("URL add completed id=%s url=%s", attempt_id, value)
                            url_input.value = ""
                        else:
                            logger.warning("URL add failed after validation id=%s url=%s", attempt_id, value)

                    ui.button("+ 追加", on_click=add_url_and_clear).props("outline").classes("primary-btn")

                ui.upload(
                    on_upload=_handle_upload,
                    auto_upload=True,
                    label="ファイルを追加 (PDF/DOCX/txt/md/png/jpg/jpeg/webp)",
                ).classes("w-full kotomake-uploader")

                source_session_cta_card = None
                source_session_cta_title = None
                source_session_cta_hint = None
                source_session_cta_keep_button = None
                source_session_cta_reset_button = None

                with ui.column().classes("w-full mt-1 pt-3 gap-1").style("border-top: 1px solid #E5E7EB;") as added_sources_section:
                    added_sources_section.visible = bool(state.sources)
                    ui.label("追加済みソース").classes("text-sm font-semibold text-gray-600")
                    with ui.column().classes("w-full rounded-lg p-2").style("background: #FBF4EF;"):
                        sources_container()
                    with ui.card().classes("w-full p-3 gap-2").style(
                        "border: 1px solid rgba(217,119,6,0.24); background: #FFFBEB;"
                    ) as source_session_notice_card:
                        source_session_notice_title = ui.label("").classes("text-sm font-semibold text-amber-800")
                        source_session_notice_hint = ui.label("").classes("text-xs text-amber-700")
                        with ui.row().classes("w-full gap-2"):
                            source_session_keep_button = ui.button("この資料を使う").props("outline")
                            source_session_reset_button = ui.button("新しく始める").props("outline")
                    source_session_notice_card.visible = False

        with ui.card().classes("card p-6 w-full fade-in step-card-2 input-stage-card"):
            with ui.row().classes("items-center gap-2 mb-3"):
                step2_badge = ui.label("生成準備").classes("text-xs font-bold bg-gray-100 text-gray-500 px-2 py-0.5 rounded tracking-widest")
                ui.label("生成準備").classes("section-title m-0")

            _ARTICLE_TYPE_DESCRIPTIONS: dict[str, str] = build_article_type_descriptions()
            direct_article_type_values = list(_get_combined_article_types().values())
            article_type = ui.select(
                options=direct_article_type_values,
                value=direct_article_type_values[0],
                label="記事種類（7種固定）" if CURRENT_MAINLINE_UI_MODE == "direct" else "内部記事種類",
            ).classes("w-full").props("outlined stack-label")
            if CURRENT_MAINLINE_UI_MODE != "direct":
                article_type.visible = False
            article_type_desc = ui.label(
                _ARTICLE_TYPE_DESCRIPTIONS.get(direct_article_type_values[0], "")
            ).classes("text-xs text-gray-600 -mt-1 pl-1")
            initial_article_type_key = _get_article_type_key(article_type.value or "") or "explanatory_article"
            output_shape_label = ui.label(
                _describe_note_output_shape(initial_article_type_key)
            ).classes("text-xs text-gray-600 -mt-1 pl-1")

            journey_confirm_state: Dict[str, Any] = {"signature": "", "preview": {}}

            def _update_article_type_desc(selected_value: Any) -> None:
                selected_label = ""
                if isinstance(selected_value, str):
                    selected_label = selected_value
                else:
                    selected_label = str(getattr(selected_value, "value", "") or "")
                article_type_desc.text = _ARTICLE_TYPE_DESCRIPTIONS.get(selected_label or "", "")
                type_key = _get_article_type_key(selected_label or "") or "explanatory_article"
                output_shape_label.text = _describe_note_output_shape(type_key)

            article_type.on("update:model-value", lambda e: _update_article_type_desc(e))
            journey_back_button_style = (
                "color: #6B7280; border-color: rgba(107,114,128,0.28); background: #FFFFFF;"
            )
            journey_outline_action_style = (
                "color: #7A5544; border-color: rgba(122,85,68,0.24); background: #FFFDFC;"
            )
            content_goal_options = dict(CONTENT_GOAL_LABELS)
            content_goal = None
            writing_focus_options = dict(WRITING_FOCUS_LABELS)
            tone_profile_options = dict(TONE_PROFILE_LABELS)
            tone_profile_placeholder = "語り口を選択してください"
            tone_profile_choice_options = [tone_profile_placeholder, *list(tone_profile_options.values())]
            writer_role_select = None
            writer_role_status_label = None
            pronoun_hint_label = None
            required_input_summary_label = None
            required_article_type_label = None
            self_reference_policy_select = None
            audience_profile_input = None
            audience_profile_status_label = None
            writing_focus = None
            tone_profile = None
            core_message_input = None
            core_message_helper_label = None
            writer_role_custom_toggle = None
            writer_role_custom = None
            pattern_select = None
            branding_subtype_select = None
            branding_focus_select = None
            branding_profile_helper_label = None
            interview_followup_container = None
            interview_followup_note = None
            interview_followup_status = None
            interview_generate_button = None
            interview_questions_container = None

            def _build_prompt_raw() -> str:
                return (user_prompt.value or "").strip()

            def _build_system_hint_items(goal_key: str) -> List[str]:
                goal_guides = {
                    "interest": "読者の興味を惹き、最後まで読みたくなる構成を優先してください。",
                    "explain": "読者の理解が進むよう、背景と要点をわかりやすく説明してください。",
                    "action": "読後に具体的な行動を取りやすい構成とメッセージを優先してください。",
                    "trust": "断定を避け、根拠と整合性を重視して信頼感のある文章にしてください。",
                }
                guide = goal_guides.get(goal_key)
                return [guide] if guide else []

            def _render_required_input_fields(*, in_wizard: bool) -> Dict[str, Any]:
                initial_type_key = _get_article_type_key(article_type.value or "") or ""
                return render_required_input_fields(
                    in_wizard=in_wizard,
                    initial_type_key=initial_type_key,
                    default_audience_profile_text=_default_audience_profile_text(),
                    default_audience_profile_placeholder_text=_default_audience_profile_placeholder_text(),
                    get_writer_role_options=_get_writer_role_options,
                    get_default_writer_role_label=_get_default_writer_role_label,
                )

            journey_sections = render_journey_flow_sections(
                current_mainline_ui_mode=CURRENT_MAINLINE_UI_MODE,
                journey_purpose_labels=JOURNEY_PURPOSE_LABELS,
                initial_journey_target_options=_get_journey_target_options("explain"),
                journey_compare_axis_options=JOURNEY_COMPARE_AXIS_OPTIONS,
                journey_compare_goal_labels=JOURNEY_COMPARE_GOAL_LABELS,
                journey_outline_action_style=journey_outline_action_style,
                required_input_fields_renderer=_render_required_input_fields,
            )
            journey_flow_container = journey_sections["journey_flow_container"]
            journey_direction_card = journey_sections["journey_direction_card"]
            journey_purpose_step_card = journey_sections["journey_purpose_step_card"]
            journey_target_step_card = journey_sections["journey_target_step_card"]
            journey_purpose_summary_row = journey_sections["journey_purpose_summary_row"]
            journey_target_summary_row = journey_sections["journey_target_summary_row"]
            journey_purpose_summary_value = journey_sections["journey_purpose_summary_value"]
            journey_target_summary_value = journey_sections["journey_target_summary_value"]
            journey_purpose_next_button = journey_sections["journey_purpose_next_button"]
            journey_target_next_button = journey_sections["journey_target_next_button"]
            journey_purpose_edit_button = journey_sections["journey_purpose_edit_button"]
            journey_target_edit_button = journey_sections["journey_target_edit_button"]
            journey_purpose = journey_sections["journey_purpose"]
            journey_target = journey_sections["journey_target"]
            journey_target_hint = journey_sections["journey_target_hint"]
            journey_step3_card = journey_sections["journey_step3_card"]
            journey_detail_hint = journey_sections["journey_detail_hint"]
            compare_detail_container = journey_sections["compare_detail_container"]
            comparison_axis_checks = journey_sections["comparison_axis_checks"]
            custom_compare_axis_input = journey_sections["custom_compare_axis_input"]
            compare_goal_select = journey_sections["compare_goal_select"]
            journey_step4_card = journey_sections["journey_step4_card"]
            journey_confirm_action_hint = journey_sections["journey_confirm_action_hint"]
            journey_confirm_badge = journey_sections["journey_confirm_badge"]
            journey_confirm_summary = journey_sections["journey_confirm_summary"]
            journey_confirm_source_fit = journey_sections["journey_confirm_source_fit"]
            journey_confirm_grounding = journey_sections["journey_confirm_grounding"]
            journey_confirm_missing = journey_sections["journey_confirm_missing"]
            journey_confirm_status = journey_sections["journey_confirm_status"]
            journey_preview_button = journey_sections["journey_preview_button"]
            journey_confirm_button = journey_sections["journey_confirm_button"]
            interview_followup_container = journey_sections["interview_followup_container"]
            interview_followup_note = journey_sections["interview_followup_note"]
            interview_followup_status = journey_sections["interview_followup_status"]
            interview_generate_button = journey_sections["interview_generate_button"]
            interview_questions_container = journey_sections["interview_questions_container"]
            required_input_widgets = dict(journey_sections.get("required_input_widgets") or {})

            if CURRENT_MAINLINE_UI_MODE != "journey":
                required_input_widgets = _render_required_input_fields(in_wizard=False)

            required_input_summary_label = required_input_widgets["required_input_summary_label"]
            required_article_type_label = required_input_widgets["required_article_type_label"]
            writer_role_select = required_input_widgets["writer_role_select"]
            writer_role_status_label = required_input_widgets["writer_role_status_label"]
            pronoun_hint_label = required_input_widgets["pronoun_hint_label"]
            audience_profile_input = required_input_widgets["audience_profile_input"]
            audience_profile_status_label = required_input_widgets["audience_profile_status_label"]
            writer_role_custom_toggle = required_input_widgets["writer_role_custom_toggle"]
            writer_role_custom = required_input_widgets["writer_role_custom"]
            audience_step_card = required_input_widgets.get("audience_step_card")
            writer_step_card = required_input_widgets.get("writer_step_card")
            audience_summary_row = required_input_widgets.get("audience_summary_row")
            writer_summary_row = required_input_widgets.get("writer_summary_row")
            audience_summary_value_label = required_input_widgets.get("audience_summary_value_label")
            writer_summary_value_label = required_input_widgets.get("writer_summary_value_label")
            audience_next_button = required_input_widgets.get("audience_next_button")
            writer_done_button = required_input_widgets.get("writer_done_button")
            audience_edit_button = required_input_widgets.get("audience_edit_button")
            writer_edit_button = required_input_widgets.get("writer_edit_button")

            generate_button = None
            generate_gate_hint = None
            required_input_wizard_state: Dict[str, Any] = {
                "focused_step": 0,
                "audience_committed": False,
                "writer_committed": False,
                "writer_role_user_overridden": False,
            }
            writer_role_default_refresh_state: Dict[str, Any] = {
                "active": False,
                "expected_value": "",
                "user_interacting": False,
            }
            journey_direction_wizard_state: Dict[str, Any] = {"focused_step": 1}

            def _selected_journey_purpose_key() -> str:
                return next(
                    (key for key, label in JOURNEY_PURPOSE_LABELS.items() if label == str(journey_purpose.value or "")),
                    "explain",
                )

            def _selected_journey_target_state(*, sync_widget: bool = False) -> Dict[str, Any]:
                normalized = _normalize_journey_target_selection(
                    _selected_journey_purpose_key(),
                    journey_target.value,
                )
                if sync_widget:
                    option_labels = list(normalized.get("option_labels") or [])
                    journey_target.options = option_labels
                    resolved_label = str(normalized.get("target_label") or "")
                    current_label = str(journey_target.value or "")
                    if resolved_label != current_label:
                        journey_target.value = resolved_label
                    elif not resolved_label and current_label:
                        journey_target.value = ""
                    journey_target.update()
                return normalized

            def _selected_journey_target_key() -> str:
                return str(_selected_journey_target_state().get("target_key") or "")

            def _selected_journey_target_label() -> str:
                return str(_selected_journey_target_state().get("target_label") or "")

            def _selected_comparison_axes() -> List[str]:
                axes = [
                    axis_key
                    for axis_key, checkbox in comparison_axis_checks.items()
                    if bool(getattr(checkbox, "value", False))
                ]
                custom_axis = str(custom_compare_axis_input.value or "").strip()
                if custom_axis:
                    axes.append(custom_axis[:40])
                return axes[:2]

            def _selected_compare_goal_key() -> str:
                selected = str(compare_goal_select.value or "")
                return next((key for key, label in JOURNEY_COMPARE_GOAL_LABELS.items() if label == selected), "fit_explain")

            def _refresh_journey_direction_wizard_state() -> None:
                if CURRENT_MAINLINE_UI_MODE != "journey":
                    return
                focused_step = int(journey_direction_wizard_state.get("focused_step") or 1)
                if focused_step not in {1, 2, 3}:
                    focused_step = 1
                purpose_ready = bool(str(journey_purpose.value or "").strip())
                target_ready = bool(str(_selected_journey_target_label() or "").strip())
                if focused_step == 2 and not purpose_ready:
                    focused_step = 1
                if focused_step == 3 and (not purpose_ready or not target_ready):
                    focused_step = 1 if not purpose_ready else 2
                if journey_purpose_step_card is not None:
                    journey_purpose_step_card.visible = focused_step == 1
                    journey_purpose_step_card.update()
                if journey_purpose_summary_row is not None:
                    journey_purpose_summary_row.visible = purpose_ready and focused_step != 1
                    journey_purpose_summary_row.update()
                if journey_purpose_summary_value is not None:
                    journey_purpose_summary_value.text = str(journey_purpose.value or "")
                    journey_purpose_summary_value.update()
                if journey_purpose_next_button is not None:
                    if purpose_ready and focused_step == 1:
                        journey_purpose_next_button.enable()
                    else:
                        journey_purpose_next_button.disable()
                    journey_purpose_next_button.update()
                if journey_target_step_card is not None:
                    journey_target_step_card.visible = purpose_ready and focused_step == 2
                    journey_target_step_card.update()
                if journey_target_summary_row is not None:
                    journey_target_summary_row.visible = purpose_ready and target_ready and focused_step == 3
                    journey_target_summary_row.update()
                if journey_target_summary_value is not None:
                    journey_target_summary_value.text = str(_selected_journey_target_label() or "")
                    journey_target_summary_value.update()
                if journey_target_next_button is not None:
                    if purpose_ready and target_ready and focused_step == 2:
                        journey_target_next_button.enable()
                    else:
                        journey_target_next_button.disable()
                    journey_target_next_button.update()

            def _selected_source_mode_key() -> str:
                return str(_resolve_source_mode_selection(getattr(source_mode_select, "value", "")).get("source_mode_key") or "grounded")

            def _refresh_source_mode_choice_cards(
                published_post_candidates: Any = None,
            ) -> None:
                selection = _resolve_base_current_ui_selection()
                past_blog_unlocked = _past_blog_prompt_unlock_available(
                    published_post_candidates
                    if published_post_candidates is not None
                    else _load_current_published_post_candidates()
                )
                available_modes = _source_mode_options_for_article_type(
                    str(selection.get("article_type") or ""),
                    past_blog_unlocked=past_blog_unlocked,
                )
                selected_mode_key = _selected_source_mode_key()
                for mode_key, mode_card in source_mode_choice_cards.items():
                    mode_card.visible = mode_key in available_modes
                    if mode_key == selected_mode_key:
                        mode_card.classes(add="source-mode-choice-card-active")
                    else:
                        mode_card.classes(remove="source-mode-choice-card-active")
                    mode_card.update()

            def _apply_source_mode_choice(mode_key: str) -> None:
                normalized_mode_key = str(mode_key or "").strip()
                selection = _resolve_base_current_ui_selection()
                published_post_candidates = _load_current_published_post_candidates()
                past_blog_unlocked = _past_blog_prompt_unlock_available(published_post_candidates)
                if normalized_mode_key not in _source_mode_options_for_article_type(
                    str(selection.get("article_type") or ""),
                    past_blog_unlocked=past_blog_unlocked,
                ):
                    return
                selected_label = str(source_mode_options[normalized_mode_key])
                if getattr(source_mode_select, "value", "") == selected_label:
                    return
                source_mode_select.value = selected_label
                source_mode_select.update()
                _refresh_source_mode_status()
                if CURRENT_MAINLINE_UI_MODE == "journey":
                    _invalidate_journey_confirmation()

            for mode_key, mode_card in source_mode_choice_cards.items():
                mode_card.on("click", lambda _event, key=mode_key: _apply_source_mode_choice(key))

            def _build_journey_signature() -> str:
                detail_key = _selected_compare_goal_key() if _selected_journey_purpose_key() == "compare" else ""
                return build_journey_signature_core(
                    purpose_key=_selected_journey_purpose_key(),
                    target_key=_selected_journey_target_key(),
                    detail_key=detail_key,
                    comparison_axes=_selected_comparison_axes(),
                    source_values=[
                        str(item.value or "").strip()
                        for item in state.sources
                        if str(item.value or "").strip()
                    ],
                    prompt_raw=str(user_prompt.value or "").strip(),
                    audience_profile=str(audience_profile_input.value or "").strip(),
                    core_message=str(core_message_input.value or "").strip(),
                    perspective_mode=str(
                        _to_plain_dict(getattr(state, "interview_answers", {})).get("perspective_mode") or ""
                    ).strip(),
                )

            def _set_journey_direction_focus(step: int = 1) -> None:
                journey_direction_wizard_state["focused_step"] = int(step or 1)
                _refresh_journey_direction_wizard_state()

            def _source_session_journey_target_committed() -> bool:
                if CURRENT_MAINLINE_UI_MODE != "journey":
                    return True
                return int(journey_direction_wizard_state.get("focused_step") or 1) >= 3

            def _has_current_journey_confirmation() -> bool:
                if CURRENT_MAINLINE_UI_MODE != "journey":
                    return True
                confirmed_signature = str(
                    getattr(state, "journey_confirmation_signature", "")
                    or journey_confirm_state.get("signature")
                    or ""
                )
                return bool(
                    _build_journey_generation_confirmation_state(
                        current_signature=_build_journey_signature(),
                        confirmed_signature=confirmed_signature,
                    ).get("ready")
                )

            def _refresh_journey_confirmation_cta(*, force_confirmation_ready: bool = False) -> None:
                if CURRENT_MAINLINE_UI_MODE != "journey":
                    if generate_gate_hint is not None:
                        generate_gate_hint.visible = False
                        generate_gate_hint.text = ""
                        generate_gate_hint.update()
                    if generate_button is not None and not bool(getattr(state, "busy", False)):
                        generate_button.enable()
                        generate_button.text = "記事を生成"
                    return
                confirmation_ready = bool(force_confirmation_ready or _has_current_journey_confirmation())
                cta_state = _build_journey_confirmation_cta_state(
                    confirmation_ready=confirmation_ready,
                )
                journey_confirm_badge.text = str(cta_state.get("badge_text") or "")
                journey_confirm_badge.classes(
                    remove="bg-amber-100 text-amber-700 bg-green-100 text-green-700",
                    add=str(cta_state.get("badge_classes") or ""),
                )
                journey_confirm_badge.update()
                journey_confirm_action_hint.text = str(cta_state.get("card_hint_text") or "")
                journey_confirm_action_hint.update()
                selection = _resolve_base_current_ui_selection()
                source_mode_key = _selected_source_mode_key()
                published_post_candidates = _load_current_published_post_candidates()
                past_blog_unlocked = _past_blog_prompt_unlock_available(published_post_candidates)
                omakase_state = _build_omakase_surface_state(
                    article_type_key=str(selection.get("article_type") or ""),
                    prompt_raw=str(user_prompt.value or "").strip() if user_prompt is not None else "",
                    source_mode_key=source_mode_key,
                    source_values=[str(item.value or "").strip() for item in state.sources],
                    published_post_candidates=published_post_candidates,
                )
                gate_surface = _build_generate_gate_surface(
                    confirmation_ready=confirmation_ready,
                    article_type_key=str(selection.get("article_type") or ""),
                    source_mode_key=source_mode_key,
                    source_count=len([item for item in state.sources if str(item.value or "").strip()]),
                    prompt_raw=str(user_prompt.value or "").strip() if user_prompt is not None else "",
                    omakase_state=omakase_state,
                    past_blog_unlocked=past_blog_unlocked,
                )
                source_session_state = _build_source_session_review_state(
                    _get_or_create_state(client_key),
                    article_type_key=_source_session_article_type_for_review(
                        selection,
                        journey_target_committed=_source_session_journey_target_committed(),
                    ),
                )
                source_session_requires_review = bool(source_session_state.get("requires_review"))
                _apply_source_session_notice_state(source_session_state)
                if source_session_requires_review:
                    gate_surface = {
                        **gate_surface,
                        "enabled": False,
                        "hint_text": str(source_session_state.get("hint_text") or ""),
                        "hint_classes": "text-amber-700",
                    }
                if confirmation_ready and not bool(gate_surface.get("enabled")):
                    cta_state = {
                        **cta_state,
                        "badge_text": "要入力",
                        "badge_classes": "bg-amber-100 text-amber-700",
                        "card_hint_text": str(gate_surface.get("hint_text") or ""),
                    }
                    journey_confirm_badge.text = str(cta_state.get("badge_text") or "")
                    journey_confirm_badge.classes(
                        remove="bg-amber-100 text-amber-700 bg-green-100 text-green-700",
                        add=str(cta_state.get("badge_classes") or ""),
                    )
                    journey_confirm_badge.update()
                    journey_confirm_action_hint.text = str(cta_state.get("card_hint_text") or "")
                    journey_confirm_action_hint.update()
                elif not bool(gate_surface.get("enabled")) and str(gate_surface.get("hint_text") or "").strip():
                    journey_confirm_action_hint.text = str(gate_surface.get("hint_text") or "")
                    journey_confirm_action_hint.update()
                if generate_gate_hint is not None:
                    generate_gate_hint.visible = False
                    generate_gate_hint.text = ""
                    generate_gate_hint.update()
                if not bool(getattr(state, "busy", False)):
                    journey_preview_button.enable()
                    journey_preview_button.text = str(cta_state.get("preview_button_text") or "不足を確認")
                    journey_confirm_button.enable()
                    journey_confirm_button.text = _resolve_journey_confirm_button_text(
                        cta_state=cta_state,
                        gate_surface=gate_surface,
                        confirmation_ready=confirmation_ready,
                        source_session_requires_review=source_session_requires_review,
                    )
                else:
                    journey_preview_button.disable()
                    journey_preview_button.text = "確認中..."
                    journey_confirm_button.disable()
                    journey_confirm_button.text = "生成中..."
                if generate_button is not None and not bool(getattr(state, "busy", False)):
                    generate_button.visible = True
                    if bool(gate_surface.get("enabled")) and confirmation_ready:
                        generate_button.enable()
                    else:
                        generate_button.disable()
                    generate_button.text = str(cta_state.get("generate_button_text") or "この内容で生成を開始")
                    if generate_gate_hint is not None:
                        generate_gate_hint.visible = True
                        generate_gate_hint.text = str(
                            cta_state.get("generate_hint_text")
                            if bool(gate_surface.get("enabled"))
                            else gate_surface.get("hint_text")
                            or cta_state.get("generate_hint_text")
                            or ""
                        )
                        generate_gate_hint.classes(
                            remove="text-green-700 text-amber-700 text-[#5D4A41]",
                            add=str(
                                cta_state.get("generate_hint_classes")
                                if bool(gate_surface.get("enabled")) and confirmation_ready
                                else gate_surface.get("hint_classes")
                                or cta_state.get("generate_hint_classes")
                                or "text-amber-700"
                            ),
                        )
                        generate_gate_hint.update()

            def _invalidate_journey_confirmation(reason_text: str = "") -> None:
                existing_signature = str(
                    getattr(state, "journey_confirmation_signature", "")
                    or journey_confirm_state.get("signature")
                    or ""
                )
                existing_preview = _to_plain_dict(
                    getattr(state, "journey_preview", {}) or journey_confirm_state.get("preview") or {}
                )
                had_confirmation_state = bool(existing_signature or existing_preview)
                current_selection: Dict[str, Any] = {}
                if CURRENT_MAINLINE_UI_MODE == "journey":
                    try:
                        current_selection = _resolve_current_ui_selection()
                    except InputContractValidationError:
                        current_selection = {}
                reset_payload = build_invalidate_journey_confirmation_core(
                    ui_mode=CURRENT_MAINLINE_UI_MODE,
                    reason_text=reason_text,
                    semantic_article_key=str(current_selection.get("semantic_article_key") or ""),
                )
                journey_confirm_state["signature"] = str(reset_payload.get("signature") or "")
                state.journey_confirmation_signature = str(reset_payload.get("signature") or "")
                journey_confirm_state["preview"] = dict(reset_payload.get("preview") or {})
                state.journey_preview = dict(reset_payload.get("preview") or {})
                if CURRENT_MAINLINE_UI_MODE == "journey":
                    journey_confirm_summary.content = _build_current_journey_confirm_summary()
                    journey_confirm_source_fit.text = str(reset_payload.get("source_fit_text") or "")
                    _set_journey_confirm_status(str(reset_payload.get("status_text") or ""), tone="amber")
                    journey_confirm_grounding.text = str(reset_payload.get("grounding_status_text") or "")
                    journey_confirm_missing.content = str(reset_payload.get("missing_content") or "")
                    _refresh_journey_confirmation_cta()
                    if had_confirmation_state:
                        _record_ui_journey_event(
                            attempt_id=_new_operation_id("confirm"),
                            event="journey_confirm_invalidated",
                            article_type=str(current_selection.get("article_type") or "unknown"),
                            phase="confirm",
                            user_prompt_text=str(user_prompt.value or "").strip(),
                            source_items=state.sources,
                            selections=_build_journey_selection_summary(),
                            reason_code=str(reset_payload.get("reason_code") or "INP_MISSING_REQUIRED"),
                            error_class=str(reset_payload.get("error_class") or "user_input"),
                            status_text=journey_confirm_status.text,
                            needs_input_items=_to_plain_list(reset_payload.get("needs_input_items")),
                            extra=dict(reset_payload.get("event_extra") or {}),
                        )

            def _resolve_base_current_ui_selection() -> Dict[str, Any]:
                if CURRENT_MAINLINE_UI_MODE == "journey":
                    ui_journey_payload = {
                        "purpose_key": _selected_journey_purpose_key(),
                        "target_key": _selected_journey_target_key(),
                        "comparison_axes": _selected_comparison_axes(),
                    }
                    if _selected_journey_purpose_key() == "compare":
                        ui_journey_payload["detail_key"] = _selected_compare_goal_key()
                    return resolve_current_mainline_ui_selection(
                        article_type=_get_article_type_key(article_type.value or "") or "explanatory_article",
                        ui_journey=ui_journey_payload,
                    )
                return resolve_current_mainline_ui_selection(
                    article_type=_get_article_type_key(article_type.value or "") or "explanatory_article",
                )

            def _selected_pattern_key() -> str:
                selected = str(getattr(pattern_select, "value", "") or "")
                return next((key for key, label in PATTERN_SELECT_LABELS.items() if label == selected), "auto")

            def _selected_tone_profile_key() -> str:
                selected = str(getattr(tone_profile, "value", "") or "")
                return next((key for key, label in tone_profile_options.items() if label == selected), "")

            def _selected_self_reference_policy_key() -> str:
                return _resolve_self_reference_policy_key(getattr(self_reference_policy_select, "value", ""))

            def _selected_branding_subtype_key() -> str:
                selected = str(getattr(branding_subtype_select, "value", "") or "")
                return next((key for key, label in BRANDING_SUBTYPE_LABELS.items() if label == selected), "company")

            def _selected_branding_focus_key() -> str:
                selected = str(getattr(branding_focus_select, "value", "") or "")
                return next((key for key, label in BRANDING_FOCUS_LABELS.items() if label == selected), "awareness_build")

            def _resolve_current_writing_profile(
                selection: Optional[Dict[str, Any]] = None,
            ) -> Dict[str, Any]:
                current_selection = dict(selection or _resolve_base_current_ui_selection())
                goal_value = str(
                    getattr(content_goal, "value", content_goal_options["auto"]) or content_goal_options["auto"]
                )
                focus_value = str(
                    getattr(writing_focus, "value", writing_focus_options["auto"]) or writing_focus_options["auto"]
                )
                tone_value = str(
                    getattr(tone_profile, "value", tone_profile_options["auto"]) or tone_profile_options["auto"]
                )
                goal_key = next((k for k, v in content_goal_options.items() if v == goal_value), "auto")
                focus_key = next((k for k, v in writing_focus_options.items() if v == focus_value), "auto")
                tone_key = next((k for k, v in tone_profile_options.items() if v == tone_value), "auto")
                return resolve_compact_writing_profile(
                    article_type=str(current_selection.get("article_type") or "explanatory_article"),
                    semantic_article_key=str(current_selection.get("semantic_article_key") or ""),
                    content_goal_key=goal_key,
                    writing_focus_key=focus_key,
                    tone_profile_key=tone_key,
                    perspective_key="auto",
                    relationship_mode="guide",
                    branding_subtype_key=_selected_branding_subtype_key(),
                    branding_focus_key=_selected_branding_focus_key(),
                    pattern_key=_selected_pattern_key(),
                    system_hint_items=_build_system_hint_items(goal_key),
                )

            def _resolve_current_ui_selection() -> Dict[str, Any]:
                selection = _resolve_base_current_ui_selection()
                writing_profile = _resolve_current_writing_profile(selection)
                selection["semantic_article_key"] = str(
                    writing_profile.get("semantic_article_key") or selection.get("semantic_article_key") or ""
                )
                selection["writing_profile"] = writing_profile
                return selection

            def _build_journey_selection_summary() -> Dict[str, Any]:
                selection = _resolve_current_ui_selection()
                is_compare = str(selection.get("article_type") or "") == "comparative_review"
                return build_journey_selection_summary_core(
                    ui_mode=CURRENT_MAINLINE_UI_MODE,
                    purpose_key=_selected_journey_purpose_key(),
                    purpose_label=str(journey_purpose.value or ""),
                    target_key=_selected_journey_target_key(),
                    target_label=_selected_journey_target_label(),
                    detail_key=_selected_compare_goal_key() if is_compare else "",
                    detail_label=_label_for_compare_goal_key(_selected_compare_goal_key()) if is_compare else "",
                    comparison_axis_labels=_get_journey_compare_axis_labels(_selected_comparison_axes()),
                    semantic_article_key=str(selection.get("semantic_article_key") or ""),
                    semantic_label=_label_for_semantic_article_key(str(selection.get("semantic_article_key") or "")),
                    article_type_key=str(selection.get("article_type") or ""),
                    article_type_label=_get_combined_article_types().get(str(selection.get("article_type") or ""), ""),
                    confirmed=_build_journey_signature() == journey_confirm_state.get("signature"),
                ) | {
                    "source_mode_key": _selected_source_mode_key(),
                    "source_mode_label": str(getattr(source_mode_select, "value", "") or ""),
                }

            def _current_source_session_review_state() -> Dict[str, Any]:
                try:
                    selection = _resolve_current_ui_selection()
                except InputContractValidationError:
                    selection = {}
                return _build_source_session_review_state(
                    _get_or_create_state(client_key),
                    article_type_key=_source_session_article_type_for_review(
                        selection,
                        journey_target_committed=_source_session_journey_target_committed(),
                    ),
                )

            def _apply_source_session_notice_state(session_state: Mapping[str, Any]) -> None:
                cta_notice_state = _build_source_session_cta_notice_state(session_state)
                source_session_notice_card.visible = bool(cta_notice_state.get("visible"))
                if bool(cta_notice_state.get("visible")):
                    source_session_notice_title.text = str(session_state.get("status_text") or "")
                    source_session_notice_hint.text = str(session_state.get("hint_text") or "")
                else:
                    source_session_notice_title.text = ""
                    source_session_notice_hint.text = ""
                source_session_notice_title.update()
                source_session_notice_hint.update()
                source_session_notice_card.update()
                if source_session_cta_card is not None:
                    source_session_cta_card.visible = bool(cta_notice_state.get("visible"))
                    if source_session_cta_title is not None:
                        source_session_cta_title.text = str(cta_notice_state.get("title_text") or "")
                        source_session_cta_title.update()
                    if source_session_cta_hint is not None:
                        source_session_cta_hint.text = str(cta_notice_state.get("hint_text") or "")
                        source_session_cta_hint.update()
                    source_session_cta_card.update()

            def _refresh_source_session_notice() -> None:
                _apply_source_session_notice_state(_current_source_session_review_state())

            def _accept_current_source_session() -> None:
                try:
                    selection = _resolve_current_ui_selection()
                except InputContractValidationError:
                    selection = {}
                _accept_source_session_for_article_type(
                    _get_or_create_state(client_key),
                    article_type_key=_source_session_article_type_for_review(
                        selection,
                        journey_target_committed=_source_session_journey_target_committed(),
                    ),
                )
                confirmed_signature = str(
                    getattr(state, "journey_confirmation_signature", "")
                    or journey_confirm_state.get("signature")
                    or ""
                )
                confirmation_plan = _build_source_session_acceptance_confirmation_plan(
                    current_signature=_build_journey_signature(),
                    confirmed_signature=confirmed_signature,
                )
                if bool(confirmation_plan.get("invalidate_confirmation")):
                    _invalidate_journey_confirmation("source_session_confirmed")
                else:
                    _refresh_source_session_notice()
                    _refresh_journey_confirmation_cta()
                _refresh_source_mode_status()
                notify_text = (
                    "この資料で進めます。生成に進めます。"
                    if bool(confirmation_plan.get("preserve_confirmation"))
                    else "この資料で進めます。内容を確認してから生成してください。"
                )
                ui.notify(notify_text, color="info")

            def _reset_current_source_session() -> None:
                removed_count = _clear_source_session_sources(_get_or_create_state(client_key))
                sources_container.refresh()
                _invalidate_journey_confirmation("source_session_reset")
                _refresh_source_mode_status()
                ui.notify(f"資料を{removed_count}件クリアしました。新しい資料を追加してください。", color="info")

            source_session_keep_button.on("click", lambda _: _accept_current_source_session())
            source_session_reset_button.on("click", lambda _: _reset_current_source_session())

            def _build_current_journey_confirm_summary(
                candidate_target_labels: Optional[List[str]] = None,
            ) -> str:
                try:
                    selection = _resolve_current_ui_selection()
                except InputContractValidationError:
                    return "選択内容をまとめます。"
                is_compare = str(selection.get("article_type") or "") == "comparative_review"
                return build_journey_confirm_summary_core(
                    purpose_label=str(journey_purpose.value or ""),
                    target_label=_selected_journey_target_label(),
                    article_type_label=_get_combined_article_types().get(
                        str(selection.get("article_type") or ""),
                        str(selection.get("article_type") or ""),
                    ),
                    semantic_label=_label_for_semantic_article_key(str(selection.get("semantic_article_key") or "")),
                    compare_goal_label=_label_for_compare_goal_key(_selected_compare_goal_key()) if is_compare else "",
                    comparison_labels=_get_journey_compare_axis_labels(_selected_comparison_axes()),
                    candidate_target_labels=candidate_target_labels or [],
                )

            ui.label("出力形式: ブログ固定。媒体差分で迷わせず、まず本文品質を優先します。").classes("text-xs text-gray-600 -mt-1 pl-1")

            def _company_intro_writer_role_auto_mode() -> bool:
                if writer_role_custom_toggle.value:
                    return False
                selected_label = str(writer_role_select.value or "").strip()
                if selected_label not in {
                    WRITER_ROLE_AUTO_LABEL,
                    WRITER_ROLE_COMPANY_INTRO_NEUTRAL_LABEL,
                }:
                    return False
                try:
                    selection = _resolve_current_ui_selection()
                except InputContractValidationError:
                    return False
                return str(selection.get("semantic_article_key") or "") == "company_introduction"

            def _selected_writer_role() -> str:
                if writer_role_custom_toggle.value:
                    return str(writer_role_custom.value or "").strip()[:80]
                selected = _writer_role_label_to_profile(writer_role_select.value)
                if selected:
                    return selected
                if _company_intro_writer_role_auto_mode():
                    return ""
                try:
                    selection = _resolve_current_ui_selection()
                except InputContractValidationError:
                    selection = {}
                type_key = str(selection.get("article_type") or _get_article_type_key(article_type.value or "") or "")
                semantic_key = str(selection.get("semantic_article_key") or "")
                return _resolve_writer_role_auto_profile(type_key, semantic_key)

            def _refresh_writer_role_status() -> None:
                selected = _selected_writer_role()
                type_key = _get_article_type_key(article_type.value or "") or ""
                pronoun_hint_label.text = _predict_pronoun_hint(
                    type_key,
                    selected,
                    _selected_self_reference_policy_key(),
                )
                writer_role_status_label.classes(remove="text-red-600 text-gray-600")
                if not selected and _company_intro_writer_role_auto_mode():
                    writer_role_status_label.text = "話者: 自動（役割語を前面に出さない）"
                    writer_role_status_label.classes(add="text-gray-600")
                    _refresh_required_input_wizard_state()
                    return
                if not selected:
                    writer_role_status_label.text = "この内容では、書き手を選んでください。"
                    writer_role_status_label.classes(add="text-red-600")
                    _refresh_required_input_wizard_state()
                    return
                if _looks_theme_like_writer_role(selected):
                    writer_role_status_label.text = "書き手欄には肩書きだけを入れてください。記事の内容は上の入力欄へ入れてください。"
                    writer_role_status_label.classes(add="text-red-600")
                    _refresh_required_input_wizard_state()
                    return
                writer_role_status_label.text = f"書き手: {selected}"
                writer_role_status_label.classes(add="text-gray-600")
                _refresh_required_input_wizard_state()

            def _refresh_writer_role_options() -> None:
                selection = _resolve_current_ui_selection()
                type_key = str(selection.get("article_type") or _get_article_type_key(article_type.value or "") or "")
                semantic_key = str(selection.get("semantic_article_key") or "")
                options = _get_writer_role_options(type_key, semantic_key)
                current = str(writer_role_select.value or "")
                default_label = _get_default_writer_role_label(type_key, semantic_key)
                writer_role_select.options = options
                should_apply_default = current not in options or (
                    not bool(required_input_wizard_state.get("writer_role_user_overridden"))
                    and _is_article_type_managed_writer_role_label(current)
                    and current != default_label
                )
                if should_apply_default:
                    writer_role_default_refresh_state["active"] = True
                    writer_role_default_refresh_state["expected_value"] = default_label
                    writer_role_select.value = default_label
                try:
                    writer_role_select.update()
                finally:
                    writer_role_default_refresh_state["active"] = False
                _refresh_writer_role_status()

            def _refresh_required_input_wizard_state() -> None:
                if CURRENT_MAINLINE_UI_MODE != "journey":
                    return
                if audience_step_card is None or writer_step_card is None:
                    return
                article_type_ready = bool(_get_article_type_key(article_type.value or "") or _selected_journey_target_key())
                audience_ready = bool(str(audience_profile_input.value or "").strip())
                selected_writer_role = _selected_writer_role()
                writer_ready = bool(
                    _company_intro_writer_role_auto_mode()
                    or (selected_writer_role and not _looks_theme_like_writer_role(selected_writer_role))
                )
                view_state = _resolve_required_input_wizard_view_state(
                    article_type_ready=article_type_ready,
                    audience_ready=audience_ready,
                    writer_ready=writer_ready,
                    audience_committed=bool(required_input_wizard_state.get("audience_committed")),
                    writer_committed=bool(required_input_wizard_state.get("writer_committed")),
                    requested_focus=int(required_input_wizard_state.get("focused_step") or 0),
                )
                focused_step = int(view_state.get("focused_step") or 1)
                required_input_wizard_state["focused_step"] = focused_step
                required_input_wizard_state["audience_committed"] = bool(view_state.get("audience_committed"))
                required_input_wizard_state["writer_committed"] = bool(view_state.get("writer_committed"))
                step_styles = {
                    "done": "border-[rgba(82,145,96,0.28)] bg-[rgba(241,252,244,0.95)]",
                    "active": "border-[rgba(222,146,73,0.28)] bg-[rgba(255,248,242,0.98)]",
                    "pending": "border-[rgba(222,146,73,0.12)] bg-white",
                }

                def _apply_step_style(card: Any, state: str) -> None:
                    card.classes(
                        remove="border-[rgba(82,145,96,0.28)] bg-[rgba(241,252,244,0.95)] border-[rgba(222,146,73,0.28)] bg-[rgba(255,248,242,0.98)] border-[rgba(222,146,73,0.12)] bg-white",
                        add=step_styles.get(state, step_styles["pending"]),
                    )
                    card.update()

                audience_step_card.visible = bool(view_state.get("audience_editor_visible"))
                audience_step_card.update()
                if article_type_ready:
                    _apply_step_style(audience_step_card, "active")
                if audience_summary_row is not None:
                    audience_summary_row.visible = bool(view_state.get("audience_summary_visible"))
                    audience_summary_row.update()
                if audience_summary_value_label is not None:
                    audience_summary_value_label.text = str(audience_profile_input.value or "").strip()
                    audience_summary_value_label.update()
                if audience_next_button is not None:
                    if article_type_ready and focused_step == 2 and audience_ready:
                        audience_next_button.enable()
                    else:
                        audience_next_button.disable()
                    audience_next_button.update()
                writer_step_card.visible = bool(view_state.get("writer_editor_visible"))
                writer_step_card.update()
                if article_type_ready and audience_ready:
                    _apply_step_style(writer_step_card, "active")
                if writer_summary_row is not None:
                    writer_summary_row.visible = bool(view_state.get("writer_summary_visible"))
                    writer_summary_row.update()
                if writer_summary_value_label is not None:
                    writer_summary_value_label.text = selected_writer_role or "自動"
                    writer_summary_value_label.update()
                if writer_done_button is not None:
                    if (
                        article_type_ready
                        and bool(required_input_wizard_state.get("audience_committed"))
                        and focused_step == 3
                        and writer_ready
                    ):
                        writer_done_button.enable()
                    else:
                        writer_done_button.disable()
                    writer_done_button.update()
                if required_input_summary_label is not None:
                    helper_step = focused_step
                    required_input_summary_label.text = _build_required_input_wizard_helper_text(helper_step)
                    required_input_summary_label.update()
                if journey_step4_card is not None:
                    journey_step4_card.visible = bool(
                        focused_step == 4
                        and required_input_wizard_state.get("audience_committed")
                        and required_input_wizard_state.get("writer_committed")
                    )
                    journey_step4_card.update()

            def _refresh_required_input_status() -> None:
                selection = _resolve_base_current_ui_selection()
                type_key = str(selection.get("article_type") or _get_article_type_key(article_type.value or "") or "")
                semantic_key = str(selection.get("semantic_article_key") or "")
                article_type_label = _get_combined_article_types().get(type_key, type_key or "未選択")
                if required_article_type_label is not None:
                    semantic_label = _label_for_semantic_article_key(semantic_key)
                    suffix = f" / {semantic_label}" if semantic_label and semantic_label != article_type_label else ""
                    required_article_type_label.text = f"記事タイプ: {article_type_label}{suffix}"
                    required_article_type_label.update()
                if audience_profile_status_label is not None:
                    audience_profile_status_label.classes(remove="text-gray-600 text-red-600")
                    normalized_audience = str(audience_profile_input.value or "").strip()
                    if normalized_audience:
                        audience_profile_status_label.text = "読者指定あり。誰向けの記事かが明示されています。"
                        audience_profile_status_label.classes(add="text-gray-600")
                    else:
                        audience_profile_status_label.text = (
                            "誰向けが未入力です。"
                            f"{_default_audience_profile_placeholder_text()} のように短く入れてください。"
                        )
                        audience_profile_status_label.classes(add="text-red-600")
                    audience_profile_status_label.update()
                if required_input_summary_label is not None:
                    required_input_summary_label.text = (
                        _build_required_input_wizard_helper_text(1)
                        if CURRENT_MAINLINE_UI_MODE == "journey"
                        else "必須は記事タイプ・誰向け・誰視点の3つです。語り口や核メッセージは詳細設定で補えます。"
                    )
                    required_input_summary_label.update()
                _refresh_required_input_wizard_state()

            def _refresh_required_input_visibility() -> None:
                type_key = _get_article_type_key(article_type.value or "") or ""
                semantic_key = str(_resolve_base_current_ui_selection().get("semantic_article_key") or "")
                goal_key = next((k for k, v in content_goal_options.items() if v == content_goal.value), "auto")
                requires_core_message = _requires_core_message_input(type_key, goal_key)
                core_message_input.visible = requires_core_message
                core_message_input.placeholder = _build_core_message_placeholder(
                    type_key,
                    semantic_key,
                    goal_key,
                )
                core_message_helper_label.text = (
                    _build_core_message_helper_text(type_key, semantic_key, goal_key)
                    if requires_core_message
                    else _build_core_message_helper_text(type_key, semantic_key, "")
                )
                core_message_helper_label.update()
                core_message_input.update()
                _refresh_required_input_status()

            def _refresh_profile_control_visibility() -> None:
                selection = _resolve_base_current_ui_selection()
                type_key = str(selection.get("article_type") or "")
                semantic_key = str(selection.get("semantic_article_key") or "")
                branding_active = type_key == "branding"
                subtype_active = branding_active and semantic_key not in {"activity_introduction", "recruit_culture"}
                if branding_subtype_select is not None:
                    branding_subtype_select.visible = subtype_active
                    branding_subtype_select.update()
                if branding_focus_select is not None:
                    branding_focus_select.visible = branding_active
                    branding_focus_select.update()
                if branding_profile_helper_label is not None:
                    if branding_active:
                        branding_profile_helper_label.text = (
                            "ブランド記事では、紹介の軸と強めたい観点だけをここで補えます。細かい説明は上の入力欄や資料で伝えてください。"
                        )
                    else:
                        branding_profile_helper_label.text = "ブランド記事のときだけ、紹介の軸と強めたい観点を表示します。"
                    branding_profile_helper_label.update()

            def _refresh_source_mode_status() -> None:
                selection = _resolve_base_current_ui_selection()
                article_type_key = str(selection.get("article_type") or "")
                source_mode_key = _selected_source_mode_key()
                published_post_candidates = _load_current_published_post_candidates()
                past_blog_unlocked = _past_blog_prompt_unlock_available(published_post_candidates)
                available_modes = _source_mode_options_for_article_type(
                    article_type_key,
                    past_blog_unlocked=past_blog_unlocked,
                )
                if source_mode_key not in available_modes:
                    source_mode_select.value = source_mode_options["grounded"]
                    source_mode_select.update()
                    source_mode_key = "grounded"
                _refresh_source_mode_choice_cards(published_post_candidates)
                input_surface = _build_source_mode_input_surface(
                    article_type_key=article_type_key,
                    source_mode_key=source_mode_key,
                    past_blog_unlocked=past_blog_unlocked,
                )
                if input_stage_helper_label is not None:
                    input_stage_helper_label.text = str(input_surface.get("section_intro_text") or "")
                    input_stage_helper_label.update()
                source_mode_helper_label.text = str(input_surface.get("source_mode_helper_text") or "")
                source_mode_helper_label.update()
                if user_prompt is not None:
                    user_prompt.label = str(input_surface.get("prompt_label") or "1行テーマ")
                    user_prompt.placeholder = str(input_surface.get("prompt_placeholder") or "")
                    user_prompt.update()
                if user_prompt_helper_label is not None:
                    user_prompt_helper_label.text = str(input_surface.get("prompt_helper_text") or "")
                    user_prompt_helper_label.update()
                announcement_inline_error_label.text = _build_announcement_inline_error(
                    article_type_key=article_type_key,
                    source_mode_key=source_mode_key,
                    prompt_raw=str(user_prompt.value or "").strip(),
                    source_values=[str(item.value or "").strip() for item in state.sources],
                )
                announcement_inline_error_label.visible = bool(announcement_inline_error_label.text)
                announcement_inline_error_label.update()
                added_sources_section.visible = bool(state.sources)
                added_sources_section.update()
                _refresh_source_session_notice()
                omakase_state = _build_omakase_surface_state(
                    article_type_key=article_type_key,
                    prompt_raw=str(user_prompt.value or "").strip(),
                    source_mode_key=source_mode_key,
                    source_values=[str(item.value or "").strip() for item in state.sources],
                    published_post_candidates=published_post_candidates,
                )
                if source_inputs_section is not None:
                    source_inputs_section.visible = source_mode_key in _SOURCE_MODE_INPUT_REQUIRED_MODES
                    if source_inputs_title_label is not None:
                        source_inputs_title_label.text = str(input_surface.get("source_title_text") or "資料入力")
                        source_inputs_title_label.update()
                    if source_inputs_helper_label is not None:
                        source_inputs_helper_label.text = str(input_surface.get("source_helper_text") or "")
                        source_inputs_helper_label.update()
                    source_section_order = 2 if source_mode_key in _SOURCE_MODE_INPUT_REQUIRED_MODES else 4
                    source_inputs_section.style(f"order: {source_section_order};")
                    source_inputs_section.update()
                if prompt_input_section is not None:
                    prompt_input_section.visible = bool(input_surface.get("prompt_visible"))
                    prompt_section_order = 4 if source_mode_key in _SOURCE_MODE_INPUT_REQUIRED_MODES else 2
                    prompt_input_section.style(f"order: {prompt_section_order};")
                    prompt_input_section.update()
                if omakase_status_card is not None:
                    omakase_status_card.visible = bool(omakase_state.get("visible"))
                    if bool(omakase_state.get("visible")):
                        omakase_status_title.text = str(omakase_state.get("title") or "")
                        omakase_status_message.text = str(omakase_state.get("message") or "")
                        omakase_status_inventory.text = str(omakase_state.get("inventory_text") or "")
                        omakase_status_detail.text = str(omakase_state.get("detail_text") or "")
                        omakase_status_title.update()
                        omakase_status_message.update()
                        omakase_status_inventory.update()
                        omakase_status_detail.update()
                    omakase_status_card.update()
                _refresh_journey_confirmation_cta()

            def _refresh_journey_step_visibility() -> None:
                if CURRENT_MAINLINE_UI_MODE != "journey":
                    journey_flow_container.visible = False
                    return
                journey_flow_container.visible = True
                requires_detail = str(_resolve_current_ui_selection().get("article_type") or "") == "comparative_review"
                journey_direction_card.visible = True
                journey_step3_card.visible = requires_detail and int(journey_direction_wizard_state.get("focused_step") or 1) == 3
                journey_step4_card.visible = bool(
                    int(required_input_wizard_state.get("focused_step") or 0) == 4
                    and required_input_wizard_state.get("audience_committed")
                    and required_input_wizard_state.get("writer_committed")
                )
                compare_detail_container.visible = requires_detail
                compare_detail_container.update()
                _refresh_journey_direction_wizard_state()

            def _sync_article_type_from_journey(*, invalidate_confirmation: bool = True) -> None:
                _selected_journey_target_state(sync_widget=True)
                selection = _resolve_current_ui_selection()
                type_key = str(selection.get("article_type") or "explanatory_article")
                label = _get_combined_article_types().get(type_key, direct_article_type_values[0])
                article_type.value = label
                _update_article_type_desc(label)
                if invalidate_confirmation:
                    _invalidate_journey_confirmation()
                _refresh_writer_role_options()
                _refresh_required_input_visibility()
                _refresh_profile_control_visibility()
                requires_detail = type_key == "comparative_review"
                journey_detail_hint.text = (
                    "比較記事では、見る観点と比較のゴールをここで補います。"
                    if requires_detail
                    else "比較記事ではないため、この設定は不要です。"
                )
                _refresh_journey_step_visibility()
                _refresh_source_mode_status()
                if CURRENT_MAINLINE_UI_MODE == "journey":
                    _set_required_input_wizard_focus(0, audience_committed=False, writer_committed=False)
                    is_compare = type_key == "comparative_review"
                    journey_confirm_summary.content = build_journey_confirm_summary_core(
                        purpose_label=str(journey_purpose.value or ""),
                        target_label=_selected_journey_target_label(),
                        article_type_label=type_key,
                        semantic_label=_label_for_semantic_article_key(str(selection.get("semantic_article_key") or "")),
                        compare_goal_label=_label_for_compare_goal_key(_selected_compare_goal_key()) if is_compare else "",
                    )

            def _go_to_journey_stage(stage: int) -> None:
                del stage
                _refresh_journey_step_visibility()

            def _set_required_input_wizard_focus(
                step: int = 0,
                *,
                audience_committed: Optional[bool] = None,
                writer_committed: Optional[bool] = None,
            ) -> None:
                required_input_wizard_state["focused_step"] = int(step or 0)
                if audience_committed is not None:
                    required_input_wizard_state["audience_committed"] = bool(audience_committed)
                if writer_committed is not None:
                    required_input_wizard_state["writer_committed"] = bool(writer_committed)
                _refresh_required_input_wizard_state()

            def _on_writer_role_custom_toggle() -> None:
                writer_role_custom.visible = bool(writer_role_custom_toggle.value)
                if not writer_role_custom_toggle.value:
                    writer_role_custom.value = ""
                _refresh_writer_role_status()

            with ui.expansion("詳細設定", icon="tune").classes("w-full narrow-support-card"):
                structure_options = {"auto": "自動（おすすめ）"}

                content_goal = ui.select(
                    options=list(content_goal_options.values()),
                    value=content_goal_options["auto"],
                    label="この記事で重視すること",
                ).classes("w-full").props("outlined stack-label")
                ui.label(
                    "※必要なときだけ調整してください。迷う場合は自動のままで問題ありません。"
                ).classes("text-xs text-gray-600")

                self_reference_policy_select = ui.select(
                    options=list(SELF_REFERENCE_POLICY_LABELS.values()),
                    value=SELF_REFERENCE_POLICY_LABELS["auto"],
                    label="自分たちの呼び方",
                ).classes("w-full").props("outlined stack-label")
                ui.label(
                    "※強制ではなく優先設定です。比較中は『私たち』『当社』などの差を固定できます。"
                ).classes("text-xs text-gray-600")

                tone_profile = ui.select(
                    options=tone_profile_choice_options,
                    value=tone_profile_placeholder,
                    label="語り口",
                ).classes("w-full").props("outlined stack-label")
                ui.label(
                    "※読み手との距離感だけ選んでください。未選択でも自動判定を優先します。"
                ).classes("text-xs text-gray-600")

                core_message_input = ui.textarea(
                    "核メッセージ",
                    placeholder=_build_core_message_placeholder(""),
                ).classes("w-full").props("outlined stack-label autogrow")
                core_message_helper_label = ui.label("").classes("text-xs text-gray-600")

                writing_focus = ui.select(
                    options=list(writing_focus_options.values()),
                    value=list(writing_focus_options.values())[0],
                    label="本文の重心",
                ).classes("w-full").props("outlined stack-label")
                ui.label("※人間らしい語り口は維持したまま、解説/経験/分析の比重を調整します").classes("text-xs text-gray-600")

                pattern_select = ui.select(
                    options=list(PATTERN_SELECT_LABELS.values()),
                    value=PATTERN_SELECT_LABELS["auto"],
                    label="文章の運び",
                ).classes("w-full").props("outlined stack-label")
                ui.label("※上の入力だけで足りないときに、文章の流れだけを補います。").classes("text-xs text-gray-600")

                branding_subtype_select = ui.select(
                    options=list(BRANDING_SUBTYPE_LABELS.values()),
                    value=BRANDING_SUBTYPE_LABELS["company"],
                    label="紹介対象の軸",
                ).classes("w-full").props("outlined stack-label")
                branding_subtype_select.visible = False
                branding_focus_select = ui.select(
                    options=list(BRANDING_FOCUS_LABELS.values()),
                    value=BRANDING_FOCUS_LABELS["awareness_build"],
                    label="紹介で強める観点",
                ).classes("w-full").props("outlined stack-label")
                branding_focus_select.visible = False
                branding_profile_helper_label = ui.label("").classes("text-xs text-gray-600")
                
                # R14-T15: 経験談チェックボックスを追加
                allow_experience_checkbox = ui.checkbox(
                    "体験談・個人エピソードの挿入を許可（デフォルトOFF）",
                    value=False,
                ).classes("w-full")
                ui.label("※新サービス紹介等ではOFF、従来サービスや事例紹介ではONがおすすめ").classes("text-xs text-gray-600")

                length_mode_options = dict(LENGTH_MODE_LABELS)
                length_mode = ui.select(
                    options=list(length_mode_options.values()),
                    value=length_mode_options["adaptive"],
                    label="記事の長さ",
                ).classes("w-full").props("outlined stack-label")
                ui.label("※自動: ソース量に応じて調整 / 短め: 700-1800字 / 普通: 2500-6500字 / 長め: 4500-9000字").classes("text-xs text-gray-600")

                # Collapsible genre management section
                with ui.expansion("カスタムジャンル管理（Phase04では非表示運用）", icon="settings").classes("w-full") as custom_genre_expansion:
                    ui.label("AIが入力を最適化してジャンルを追加します").classes("text-xs text-gray-600 mb-2")
                
                    genre_input = ui.input("新しいジャンル", placeholder="例: 介護保険の解説記事").classes("w-full").props("outlined stack-label")
                    genre_status = ui.label("").classes("text-sm text-gray-600")
                    genre_spinner = ui.spinner(size="sm")
                    genre_spinner.visible = False
                    custom_genre_expansion.visible = False
                
                    async def add_genre_with_ai():
                        global pending_genre, genre_optimize_busy
                        if genre_optimize_busy:
                            return
                        if not genre_input.value.strip():
                            ui.notify("ジャンル名を入力してください", color="negative")
                            return
                    
                        genre_optimize_busy = True
                        genre_spinner.visible = True
                        genre_status.text = "AIで最適化中..."
                    
                        try:
                            optimized = await run.io_bound(_new_llm_client().optimize_genre_prompt, genre_input.value.strip())
                            pending_genre = optimized
                            genre_status.text = ""
                            focus_key = next((k for k, v in writing_focus_options.items() if v == writing_focus.value), "auto")
                            estimated_meta = estimate_category_meta(
                                optimized.get("label", ""),
                                optimized.get("prompt", ""),
                                user_prompt=user_prompt.value or "",
                                writing_focus=focus_key,
                            )
                        
                            # Show confirmation dialog
                            with ui.dialog() as confirm_dialog, ui.card().classes("p-4 w-96"):
                                ui.label("ジャンルの確認").classes("text-lg font-bold mb-2")
                                ui.label("AIが以下のように最適化しました。追加しますか？").classes("text-sm text-gray-600 mb-4")
                            
                                label_edit = ui.input("ラベル", value=optimized.get("label", "")).classes("w-full").props("outlined stack-label")
                                prompt_edit = ui.textarea("プロンプト", value=optimized.get("prompt", "")).classes("w-full").props("outlined stack-label")
                                ui.label("カテゴリ推定（必要なら修正）").classes("text-sm font-semibold mt-2")
                                base_template = ui.select(
                                    options=list(BASE_TEMPLATE_LABELS.values()),
                                    value=estimated_meta["base_template"],
                                    label="base_template",
                                ).classes("w-full")
                                focus_default = ui.select(
                                    options=list(FOCUS_DEFAULT_LABELS.values()),
                                    value=estimated_meta["focus_default"],
                                    label="focus_default",
                                ).classes("w-full")
                                empathy_level = ui.select(
                                    options=list(LEVEL_LABELS.values()),
                                    value=estimated_meta["empathy_level"],
                                    label="empathy_level",
                                ).classes("w-full")
                                humanity_level = ui.select(
                                    options=list(LEVEL_LABELS.values()),
                                    value=estimated_meta["humanity_level"],
                                    label="humanity_level",
                                ).classes("w-full")
                                evidence_mode = ui.select(
                                    options=list(EVIDENCE_LABELS.values()),
                                    value=estimated_meta["evidence_mode"],
                                    label="evidence_mode",
                                ).classes("w-full")
                                ui.label("追加で必ず守る運用ルール（必須）").classes("text-sm font-semibold mt-1")
                                required_rule = ui.textarea(
                                    "カテゴリ固有の必須ルール",
                                    placeholder="例: 一次情報の要約を中心にし、導入判断の観点を3つに限定する",
                                ).classes("w-full").props("outlined stack-label")
                                with ui.column().classes("w-full gap-1"):
                                    official_only = ui.checkbox(
                                        "公式情報ベースを優先（推測・未確認情報を抑制）",
                                        value=estimated_meta["evidence_mode"] == "strict",
                                    )
                                    allow_experience = ui.checkbox(
                                        "体験談・個人エピソードの挿入を許可",
                                        value=estimated_meta["focus_default"] == "experience",
                                    )
                                    allow_cta = ui.checkbox("強いCTA（行動喚起）を許可", value=False)
                                    confirm_policy = ui.checkbox(
                                        "上記ルールを確認し、このカテゴリに適用する（必須）",
                                        value=False,
                                    )
                            
                                def confirm_add():
                                    label_text = (label_edit.value or "").strip()
                                    base_prompt = (prompt_edit.value or "").strip()
                                    if not label_text:
                                        ui.notify("ラベルを入力してください", color="negative")
                                        return
                                    if not base_prompt:
                                        ui.notify("プロンプトを入力してください", color="negative")
                                        return
                                    rule_text = (required_rule.value or "").strip()
                                    if not rule_text:
                                        ui.notify("カテゴリ固有の必須ルールを入力してください", color="negative")
                                        return
                                    if not confirm_policy.value:
                                        ui.notify("適用確認チェックをONにしてください", color="negative")
                                        return
                                    if not allow_experience.value and focus_default.value == "experience":
                                        ui.notify(
                                            "体験談を許可しない場合、focus_defaultはexperience以外を選択してください",
                                            color="warning",
                                        )
                                        return
                                    extra_lines = [
                                        "【カテゴリ運用ルール】",
                                        f"- 必須: {rule_text}",
                                        "- 方針: 公式情報・一次情報を最優先"
                                        if official_only.value
                                        else "- 方針: 参考情報と一般知識を分離して扱う",
                                        "- 体験談: 許可"
                                        if allow_experience.value
                                        else "- 体験談: 原則使わない（実体験の断定を避ける）",
                                        "- CTA: 強めにしてよい" if allow_cta.value else "- CTA: 押し付けない",
                                    ]
                                    merged_prompt = base_prompt
                                    if merged_prompt:
                                        merged_prompt += "\n\n"
                                    merged_prompt += "\n".join(extra_lines)
                                    genre_manager.add_genre(
                                        label_text,
                                        merged_prompt,
                                        meta={
                                            "base_template": base_template.value,
                                            "focus_default": focus_default.value,
                                            "empathy_level": empathy_level.value,
                                            "humanity_level": humanity_level.value,
                                            "evidence_mode": evidence_mode.value,
                                        },
                                    )
                                    ui.notify("ジャンルを追加しました", color="positive")
                                    confirm_dialog.close()
                                    genre_input.value = ""
                                    custom_genres_container.refresh()
                                    article_type.options = list(_get_combined_article_types().values())
                                    if article_type.options and article_type.value not in article_type.options:
                                        article_type.value = article_type.options[0]
                                    article_type.update()
                            
                                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                                    ui.button("キャンセル", on_click=confirm_dialog.close).props("flat")
                                    ui.button("追加", on_click=confirm_add).classes("primary-btn")
                            confirm_dialog.open()
                        
                        except Exception:
                            logger.exception("Genre optimization failed")
                            genre_status.text = "エラーが発生しました（詳細はログを確認してください）"
                            ui.notify("最適化に失敗しました", color="negative")
                        finally:
                            genre_optimize_busy = False
                            genre_spinner.visible = False
                
                    ui.button("AIで最適化して追加", on_click=add_genre_with_ai).classes("primary-btn mt-2")
                
                    ui.separator()
                    ui.label("登録済みカスタムジャンル").classes("text-sm text-gray-600")
                    custom_genres_container(article_type)

            writer_role_select.on("update:model-value", lambda _: _refresh_writer_role_status())
            writer_role_custom_toggle.on("update:model-value", lambda _: _on_writer_role_custom_toggle())
            writer_role_custom.on("update:model-value", lambda _: _refresh_writer_role_status())
            self_reference_policy_select.on("update:model-value", lambda _: _refresh_writer_role_status())
            article_type.on("update:model-value", lambda _: _refresh_writer_role_options())
            article_type.on("update:model-value", lambda _: _refresh_required_input_visibility())
            article_type.on("update:model-value", lambda _: _refresh_profile_control_visibility())
            content_goal.on("update:model-value", lambda _: _refresh_required_input_visibility())
            if CURRENT_MAINLINE_UI_MODE == "journey":
                journey_purpose.on("update:model-value", lambda _: _sync_article_type_from_journey())
                journey_target.on("update:model-value", lambda _: _sync_article_type_from_journey())
                source_mode_select.on("update:model-value", lambda _: _refresh_source_mode_status())
                custom_compare_axis_input.on("update:model-value", lambda _: _sync_article_type_from_journey())
                compare_goal_select.on("update:model-value", lambda _: _sync_article_type_from_journey())
                for checkbox in comparison_axis_checks.values():
                    checkbox.on("update:model-value", lambda _: _sync_article_type_from_journey())
                journey_purpose_next_button.on("click", lambda _: _set_journey_direction_focus(2))
                journey_target_next_button.on("click", lambda _: _set_journey_direction_focus(3))
                journey_purpose_edit_button.on("click", lambda _: _set_journey_direction_focus(1))
                journey_target_edit_button.on("click", lambda _: _set_journey_direction_focus(2))
            if audience_next_button is not None:
                audience_next_button.on(
                    "click",
                    lambda _: _set_required_input_wizard_focus(3, audience_committed=True, writer_committed=False),
                )
            if writer_done_button is not None:
                writer_done_button.on(
                    "click",
                    lambda _: _set_required_input_wizard_focus(4, audience_committed=True, writer_committed=True),
                )
            if audience_edit_button is not None:
                audience_edit_button.on(
                    "click",
                    lambda _: _set_required_input_wizard_focus(2, audience_committed=False, writer_committed=False),
                )
            if writer_edit_button is not None:
                writer_edit_button.on(
                    "click",
                    lambda _: _set_required_input_wizard_focus(3, writer_committed=False),
                )
            _refresh_writer_role_status()
            _refresh_required_input_visibility()
            _refresh_profile_control_visibility()
            _refresh_journey_step_visibility()
            _refresh_source_mode_status()

            if CURRENT_MAINLINE_UI_MODE == "journey":
                _sync_article_type_from_journey(invalidate_confirmation=False)

            def _set_interview_followup_state(
                *,
                visible: bool,
                note_text: str = "",
                status_text: str = "",
                tone: str = "gray",
                clear_questions: bool = False,
            ) -> None:
                if interview_followup_note is not None:
                    interview_followup_note.text = str(note_text or "")
                    interview_followup_note.update()
                if interview_followup_status is not None:
                    interview_followup_status.text = str(status_text or "")
                    interview_followup_status.classes(
                        remove="text-gray-600 text-amber-700 text-green-700 text-red-500",
                        add={
                            "amber": "text-amber-700",
                            "green": "text-green-700",
                            "red": "text-red-500",
                        }.get(str(tone or "").strip(), "text-gray-600"),
                    )
                    interview_followup_status.update()
                if clear_questions and interview_questions_container is not None:
                    interview_questions_container.clear()
                if interview_followup_container is not None:
                    interview_followup_container.visible = bool(visible)
                    interview_followup_container.update()

            def _set_journey_confirm_status(
                text: str,
                *,
                tone: str = "gray",
            ) -> None:
                if journey_confirm_status is None:
                    return
                journey_confirm_status.text = str(text or "")
                journey_confirm_status.classes(
                    remove=(
                        "text-gray-600 text-amber-700 text-green-700 text-red-500 "
                        "font-semibold bg-green-50 bg-amber-50 bg-red-50 rounded-lg px-3 py-2"
                    ),
                    add={
                        "amber": "text-amber-700 font-semibold bg-amber-50 rounded-lg px-3 py-2",
                        "green": "text-green-700 font-semibold bg-green-50 rounded-lg px-3 py-2",
                        "red": "text-red-500 font-semibold bg-red-50 rounded-lg px-3 py-2",
                    }.get(str(tone or "").strip(), "text-gray-600"),
                )
                journey_confirm_status.update()

            def _render_current_mainline_question_items(
                question_items: Iterable[Any] | None,
            ) -> int:
                current_question_items = _filter_current_mainline_question_items_for_ui(question_items)
                if not current_question_items:
                    return 0
                state.question_generation_owner = "current_mainline"
                interview_answers = dict(getattr(state, "interview_answers", {}) or {})
                answer_key_map = {
                    "speaker_profile": "writer_role",
                    "audience_profile": "target",
                    "core_message": "message",
                }
                interview_questions_container.clear()
                with interview_questions_container:
                    for item in current_question_items:
                        normalized_item = _to_plain_dict(item)
                        field = str(normalized_item.get("field", "") or "")
                        answer_key = answer_key_map.get(field, field or "message")
                        question_text = str(normalized_item.get("question_template", "") or field)
                        example_answer = str(normalized_item.get("example_answer", "") or "")
                        option_items = [
                            _to_plain_dict(option)
                            for option in _to_plain_list(normalized_item.get("options"))
                            if str(_to_plain_dict(option).get("value") or "").strip()
                            and str(_to_plain_dict(option).get("label") or "").strip()
                        ]
                        with ui.card().classes("w-full p-3"):
                            ui.label(question_text).classes("font-semibold mb-2 w-full").style(
                                "white-space: normal; overflow-wrap: anywhere;"
                            )
                            if option_items:
                                option_map = {
                                    str(option.get("value") or ""): str(option.get("label") or "")
                                    for option in option_items
                                }
                                select_field = ui.select(
                                    options=option_map,
                                    value=str(interview_answers.get(answer_key) or "").strip() or None,
                                    label="選択してください",
                                ).classes("w-full").props("outlined stack-label")
                                select_field.bind_value_to(interview_answers, answer_key)
                                select_field.on(
                                    "update:model-value",
                                    lambda _: _invalidate_journey_confirmation(),
                                )
                                for option in option_items:
                                    description = str(option.get("description") or "").strip()
                                    if description:
                                        ui.label(
                                            f"{str(option.get('label') or '').strip()}: {description}"
                                        ).classes("text-xs text-gray-600")
                            else:
                                input_field = ui.input(
                                    label="自由入力",
                                    placeholder=example_answer or "入力してください",
                                ).classes("w-full").props("outlined stack-label")
                                input_field.bind_value_to(interview_answers, answer_key)
                                input_field.on(
                                    "update:model-value",
                                    lambda _: _invalidate_journey_confirmation(),
                                )
                state.interview_questions_loaded = True
                state.interview_answers = interview_answers
                return len(current_question_items)

            async def _refresh_journey_confirm_preview() -> None:
                if CURRENT_MAINLINE_UI_MODE != "journey":
                    return
                confirm_attempt_id = _new_operation_id("confirm")
                selection = _resolve_current_ui_selection()
                source_mode_key = _selected_source_mode_key()
                past_blog_unlocked = _past_blog_prompt_unlock_available(
                    _load_current_published_post_candidates()
                )
                current_summary_content = _build_current_journey_confirm_summary()
                _set_journey_confirm_status("確認内容を更新中です...", tone="gray")
                contexts = []
                failures = []
                if (
                    not state.sources
                    and source_mode_key != "web"
                    and not _source_mode_allows_no_sources(
                        article_type_key=str(selection.get("article_type") or ""),
                        source_mode_key=source_mode_key,
                        prompt_raw=str(user_prompt.value or "").strip(),
                        past_blog_unlocked=past_blog_unlocked,
                    )
                ):
                    blocked_view = build_journey_confirm_blocked_view_core(
                        kind="no_sources",
                        semantic_article_key=str(selection.get("semantic_article_key") or ""),
                    )
                    _set_interview_followup_state(visible=False, clear_questions=True)
                    journey_confirm_state["preview"] = {}
                    state.journey_preview = {}
                    journey_confirm_summary.content = current_summary_content
                    journey_confirm_source_fit.text = str(blocked_view.get("source_fit_text") or "")
                    journey_confirm_grounding.text = str(blocked_view.get("grounding_status_text") or "")
                    journey_confirm_missing.content = str(blocked_view.get("missing_content") or "")
                    _set_journey_confirm_status(str(blocked_view.get("status_text") or ""), tone="amber")
                    _refresh_journey_confirmation_cta()
                    _record_ui_journey_event(
                        attempt_id=confirm_attempt_id,
                        event="journey_confirm_blocked_no_sources",
                        article_type=str(selection.get("article_type") or "unknown"),
                        phase="confirm",
                        user_prompt_text=str(user_prompt.value or "").strip(),
                        source_items=state.sources,
                        selections=_build_journey_selection_summary(),
                        reason_code=str(blocked_view.get("reason_code") or "INP_MISSING_REQUIRED"),
                        error_class=str(blocked_view.get("error_class") or "user_input"),
                        status_text=journey_confirm_status.text,
                        needs_input_items=_to_plain_list(blocked_view.get("needs_input_items")),
                        extra=dict(blocked_view.get("event_extra") or {}),
                    )
                    return
                if state.sources:
                    contexts, failures = await run.io_bound(
                        fetcher.fetch_multiple_with_errors,
                        [s.value for s in state.sources],
                        confirm_attempt_id,
                    )
                if state.sources and (failures or not contexts):
                    blocked_view = build_journey_confirm_blocked_view_core(
                        kind="fetch_failed",
                        semantic_article_key=str(selection.get("semantic_article_key") or ""),
                    )
                    _set_interview_followup_state(visible=False, clear_questions=True)
                    journey_confirm_state["preview"] = {}
                    state.journey_preview = {}
                    journey_confirm_summary.content = current_summary_content
                    journey_confirm_source_fit.text = str(blocked_view.get("source_fit_text") or "")
                    journey_confirm_grounding.text = str(blocked_view.get("grounding_status_text") or "")
                    journey_confirm_missing.content = str(blocked_view.get("missing_content") or "")
                    _set_journey_confirm_status(str(blocked_view.get("status_text") or ""), tone="amber")
                    _refresh_journey_confirmation_cta()
                    _record_ui_journey_event(
                        attempt_id=confirm_attempt_id,
                        event="journey_confirm_fetch_failed",
                        article_type=str(selection.get("article_type") or "unknown"),
                        phase="confirm",
                        user_prompt_text=str(user_prompt.value or "").strip(),
                        source_items=state.sources,
                        selections=_build_journey_selection_summary(),
                        reason_code=str(blocked_view.get("reason_code") or "INP_SOURCE_CONTEXT_INSUFFICIENT"),
                        error_class=str(blocked_view.get("error_class") or "user_input"),
                        status_text=journey_confirm_status.text,
                        needs_input_items=_to_plain_list(blocked_view.get("needs_input_items")),
                        extra=dict(blocked_view.get("event_extra") or {}),
                    )
                    return
                preview_content_goal_key = next((k for k, v in content_goal_options.items() if v == content_goal.value), "auto")
                preview_writing_focus_key = next((k for k, v in writing_focus_options.items() if v == writing_focus.value), "auto")
                preview_handoff_settings = _resolve_article_type_handoff_settings(
                    article_type_key=str(selection.get("article_type") or "explanatory_article"),
                    semantic_article_key=str(selection.get("semantic_article_key") or ""),
                    writing_focus_key=preview_writing_focus_key,
                    perspective_key="auto",
                    self_reference_policy_key=_selected_self_reference_policy_key(),
                    writer_role_text=_selected_writer_role(),
                )
                preview = build_current_mainline_confirm_preview(
                    source_values=[s.value for s in state.sources],
                    source_documents=contexts,
                    article_type=str(selection.get("article_type") or "explanatory_article"),
                    ui_journey=selection.get("ui_journey"),
                    comparison_axes=selection.get("comparison_axes"),
                    user_prompt_text=_build_prompt_raw(),
                    content_goal_key=preview_content_goal_key,
                    writing_focus_key=str(preview_handoff_settings.get("writing_focus") or preview_writing_focus_key),
                    structure_key="auto",
                    length_mode_key=next((k for k, v in length_mode_options.items() if v == length_mode.value), "adaptive"),
                    tone_profile_key=_selected_tone_profile_key() or "auto",
                    perspective_key=str(preview_handoff_settings.get("perspective") or "auto"),
                    allow_experience=bool(allow_experience_checkbox.value),
                    interview_answers=dict(getattr(state, "interview_answers", {}) or {}),
                    speaker_profile_input=str(preview_handoff_settings.get("writer_role") or ""),
                    audience_profile_input=str(audience_profile_input.value or "").strip()[:120],
                    core_message_input=str(core_message_input.value or "").strip()[:160],
                    self_reference_policy_key=str(
                        preview_handoff_settings.get("self_reference_policy")
                        or _selected_self_reference_policy_key()
                    ),
                    branding_subtype_key=_selected_branding_subtype_key(),
                    branding_focus_key=_selected_branding_focus_key(),
                    pattern_key=_selected_pattern_key(),
                    system_hint_items=_build_system_hint_items(preview_content_goal_key),
                    retry_memo=[],
                    strict_saas_mode=CURRENT_MAINLINE_STRICT_SAAS_MODE,
                    source_mode=source_mode_key,
                    industry_hint="",
                )
                journey_confirm_state["preview"] = dict(preview)
                state.journey_preview = dict(preview)
                source_fit = _to_plain_dict(preview.get("source_fit"))
                preview_journey = _to_plain_dict(preview.get("ui_journey"))
                preview_purpose_key = str(preview_journey.get("purpose_key") or _selected_journey_purpose_key())
                preview_target_key = str(preview_journey.get("target_key") or _selected_journey_target_key())
                comparison_labels = _get_journey_compare_axis_labels(_selected_comparison_axes())
                candidate_targets = [
                    _label_for_semantic_article_key(str(item or ""))
                    for item in _to_plain_list(source_fit.get("candidate_targets"))
                    if str(item or "").strip()
                ]
                preview_view = build_journey_confirm_preview_view_core(
                    preview=preview,
                    purpose_label=JOURNEY_PURPOSE_LABELS.get(preview_purpose_key, str(journey_purpose.value or "")),
                    target_label=JOURNEY_TARGET_LABELS_ALL.get(
                        preview_purpose_key,
                        {},
                    ).get(preview_target_key, _selected_journey_target_label()),
                    article_type_label=_get_combined_article_types().get(
                        str(preview.get("article_type") or ""),
                        str(preview.get("article_type") or ""),
                    ),
                    semantic_label=_label_for_semantic_article_key(str(preview.get("semantic_article_key") or "")),
                    compare_goal_label=(
                        _label_for_compare_goal_key(_selected_compare_goal_key())
                        if str(preview.get("article_type") or "") == "comparative_review"
                        else ""
                    ),
                    comparison_labels=comparison_labels,
                    candidate_target_labels=candidate_targets,
                )
                journey_confirm_state["preview_view"] = dict(preview_view)
                journey_confirm_summary.content = str(preview_view.get("summary_content") or current_summary_content)
                journey_confirm_source_fit.text = str(preview_view.get("source_fit_text") or "")
                journey_confirm_grounding.text = str(preview_view.get("grounding_status_text") or "")
                journey_confirm_missing.content = str(preview_view.get("missing_content") or "")
                _set_journey_confirm_status(
                    str(preview_view.get("status_text") or ""),
                    tone="green" if bool(preview_view.get("allow_confirm")) else "amber",
                )
                _refresh_journey_confirmation_cta()
                needs_input_items = _to_plain_list(preview_view.get("needs_input_items"))
                question_items = _filter_current_mainline_question_items_for_ui(
                    _to_plain_dict(preview.get("input_decision")).get("question_items")
                )
                if bool(preview_view.get("allow_confirm")):
                    _set_interview_followup_state(visible=False, clear_questions=True)
                else:
                    question_count = _render_current_mainline_question_items(question_items)
                    _set_interview_followup_state(
                        visible=bool(needs_input_items or question_items),
                        note_text=(
                            "この画面で必要な確認項目を選べます。回答後にもう一度「内容を確認」を押してください。"
                            if question_count
                            else "不足情報があるときだけ、必要な確認項目を表示します。"
                        ),
                        status_text=(
                            "下の選択を入れると確定状態が更新されます。"
                            if question_count
                            else (
                                "質問で補える内容かどうかを判定します。不要なら上の入力欄を補ってください。"
                                if needs_input_items
                                else ""
                            )
                        ),
                        tone="gray",
                        clear_questions=not bool(question_count),
                    )
                _record_ui_journey_event(
                    attempt_id=confirm_attempt_id,
                    event="journey_confirm_preview_ready",
                    article_type=str(preview.get("article_type") or "unknown"),
                    phase="confirm",
                    user_prompt_text=str(user_prompt.value or "").strip(),
                    source_items=state.sources,
                    selections=_build_journey_selection_summary(),
                    reason_code=str(preview_view.get("reason_code") or "OK"),
                    error_class=str(preview_view.get("error_class") or "success"),
                    status_text=journey_confirm_status.text,
                    needs_input_items=needs_input_items,
                    extra=dict(preview_view.get("event_extra") or {}),
                )

            async def _confirm_journey_selection(*, notify_on_success: bool = True) -> None:
                if CURRENT_MAINLINE_UI_MODE != "journey":
                    return
                await _refresh_journey_confirm_preview()
                preview = _to_plain_dict(journey_confirm_state.get("preview"))
                preview_view = _to_plain_dict(journey_confirm_state.get("preview_view"))
                if not bool(preview_view.get("allow_confirm")):
                    _set_journey_confirm_status(
                        str(
                            preview_view.get("status_text")
                            or "足りない材料があります。補ってからもう一度確認してください。"
                        ),
                        tone="amber",
                    )
                    _refresh_journey_confirmation_cta(force_confirmation_ready=False)
                    ui.notify("足りない情報があるため、まだ確定できません。", color="warning")
                    return
                input_decision = _to_plain_dict(preview.get("input_decision"))
                if str(input_decision.get("action") or "accept") != "accept":
                    ui.notify("足りない情報があるため、まだ確定できません。", color="warning")
                    return
                signature = _build_journey_signature()
                journey_confirm_state["signature"] = signature
                state.journey_confirmation_signature = signature
                try:
                    source_session_current_selection = _resolve_base_current_ui_selection()
                except InputContractValidationError:
                    source_session_current_selection = {}
                source_session_article_type = _source_session_confirmation_article_type_key(
                    current_selection=source_session_current_selection,
                    preview=preview,
                )
                _sync_source_session_acceptance_for_fresh_confirmation(
                    state,
                    article_type_key=source_session_article_type,
                    current_journey_signature=signature,
                    confirmed_journey_signature=str(state.journey_confirmation_signature or ""),
                )
                confirmed_view = build_journey_confirmed_view_core(
                    semantic_article_key=str(preview.get("semantic_article_key") or ""),
                )
                _set_journey_confirm_status(str(confirmed_view.get("status_text") or ""), tone="green")
                _set_interview_followup_state(visible=False, clear_questions=True)
                _refresh_journey_confirmation_cta(force_confirmation_ready=True)
                _record_ui_journey_event(
                    attempt_id=_new_operation_id("confirm"),
                    event="journey_confirmed",
                    article_type=str(preview.get("article_type") or "unknown"),
                    phase="confirm",
                    user_prompt_text=str(user_prompt.value or "").strip(),
                    source_items=state.sources,
                    selections=_build_journey_selection_summary(),
                    status_text=journey_confirm_status.text,
                    extra=dict(confirmed_view.get("event_extra") or {}),
                )
                if notify_on_success:
                    ui.notify(str(confirmed_view.get("notify_text") or "記事の意味づけを確定しました。"), color="positive")

            journey_preview_button.on("click", lambda _: _refresh_journey_confirm_preview())
            journey_confirm_button.on("click", lambda _: _confirm_journey_selection())

            user_prompt.on("update:model-value", lambda _: _invalidate_journey_confirmation())
            user_prompt.on("update:model-value", lambda _: _refresh_source_mode_status())
            def _on_audience_profile_input_focus() -> None:
                # IME composition / blur-focus round-trip でも audience_committed を True 側へ戻さない。
                _apply_required_input_wizard_typing_reset(
                    required_input_wizard_state,
                    focused_step=2,
                    clear_audience_commit=True,
                    clear_writer_commit=True,
                )
                _refresh_required_input_wizard_state()

            def _on_audience_profile_input_changed() -> None:
                # 1 keystroke あたりの refresh を 1 回に抑えて DOM 再描画で IME 入力を乱さないようにする。
                _apply_required_input_wizard_typing_reset(
                    required_input_wizard_state,
                    focused_step=2,
                    clear_audience_commit=True,
                    clear_writer_commit=True,
                )
                _refresh_required_input_status()
                _invalidate_journey_confirmation()

            audience_profile_input.on("focus", lambda _: _on_audience_profile_input_focus())
            audience_profile_input.on("update:model-value", lambda _: _on_audience_profile_input_changed())
            core_message_input.on("update:model-value", lambda _: _invalidate_journey_confirmation())
            content_goal.on("update:model-value", lambda _: _invalidate_journey_confirmation())
            writing_focus.on("update:model-value", lambda _: _invalidate_journey_confirmation())
            tone_profile.on("update:model-value", lambda _: _invalidate_journey_confirmation())
            length_mode.on("update:model-value", lambda _: _invalidate_journey_confirmation())
            pattern_select.on("update:model-value", lambda _: _invalidate_journey_confirmation())
            branding_subtype_select.on("update:model-value", lambda _: _invalidate_journey_confirmation())
            branding_focus_select.on("update:model-value", lambda _: _invalidate_journey_confirmation())
            def _on_writer_role_interaction() -> None:
                writer_role_default_refresh_state["user_interacting"] = True
                # writer role を触っている間は確定状態に戻さないよう writer_committed を解除する。
                _apply_required_input_wizard_typing_reset(
                    required_input_wizard_state,
                    focused_step=3,
                    clear_writer_commit=True,
                )
                _refresh_required_input_wizard_state()

            def _on_writer_role_value_changed() -> None:
                current_label = str(writer_role_select.value or "")
                expected_default = str(writer_role_default_refresh_state.get("expected_value") or "")
                if expected_default and current_label == expected_default:
                    writer_role_default_refresh_state["expected_value"] = ""
                    return
                if (
                    not bool(writer_role_default_refresh_state.get("user_interacting"))
                    and _is_article_type_managed_writer_role_label(current_label)
                ):
                    return
                writer_role_default_refresh_state["user_interacting"] = False
                if not writer_role_default_refresh_state.get("active"):
                    required_input_wizard_state["writer_role_user_overridden"] = True
                _apply_required_input_wizard_typing_reset(
                    required_input_wizard_state,
                    focused_step=3,
                    clear_writer_commit=True,
                )
                _refresh_required_input_wizard_state()
                _invalidate_journey_confirmation()

            writer_role_select.on("click", lambda _: _on_writer_role_interaction())
            writer_role_select.on("update:model-value", lambda _: _on_writer_role_value_changed())
            writer_role_custom_toggle.on("click", lambda _: _on_writer_role_interaction())
            writer_role_custom_toggle.on("update:model-value", lambda _: _on_writer_role_value_changed())
            writer_role_custom.on("focus", lambda _: _on_writer_role_interaction())
            writer_role_custom.on("update:model-value", lambda _: _on_writer_role_value_changed())
            self_reference_policy_select.on("update:model-value", lambda _: _invalidate_journey_confirmation())
            allow_experience_checkbox.on("update:model-value", lambda _: _invalidate_journey_confirmation())
            if CURRENT_MAINLINE_UI_MODE == "journey":
                source_mode_select.on("update:model-value", lambda _: _invalidate_journey_confirmation())

            # 条件付き確認項目
            interview_answers: Dict[str, Any] = {
                "perspective": None,
                "perspective_mode": None,
                "target": None,
                "message": None,
            }
            interview_generate_busy = False

            async def load_interview_questions():
                """ソースと指示から質問を生成"""
                nonlocal interview_generate_busy
                if interview_generate_busy:
                    ui.notify("質問生成を実行中です。完了までお待ちください。", color="warning")
                    return
                interview_generate_busy = True
                interview_generate_button.disable()
                attempt_id = _new_operation_id("interview")
                started_at = time.monotonic()
                phase = "validate"
                source_mode_key = _selected_source_mode_key()
                current_selection = _resolve_current_ui_selection()
                past_blog_unlocked = _past_blog_prompt_unlock_available(
                    _load_current_published_post_candidates()
                )
                if (
                    not state.sources
                    and source_mode_key != "web"
                    and not _source_mode_allows_no_sources(
                        article_type_key=str(current_selection.get("article_type") or ""),
                        source_mode_key=source_mode_key,
                        prompt_raw=str(user_prompt.value or "").strip(),
                        past_blog_unlocked=past_blog_unlocked,
                    )
                ):
                    _set_interview_followup_state(
                        visible=True,
                        note_text="ソースがないため、確認項目を作れません。",
                        status_text="先にソースを追加してください。",
                        tone="amber",
                        clear_questions=True,
                    )
                    interview_generate_busy = False
                    interview_generate_button.enable()
                    logger.warning("Interview question generation rejected id=%s reason=no_sources", attempt_id)
                    ui.notify("先にソース（URL/ファイル）を追加してください", color="warning")
                    return
                logger.info("Interview question generation started id=%s source_count=%s", attempt_id, len(state.sources))
                interview_answers.clear()
                interview_answers.update(
                    {
                        "perspective": None,
                        "perspective_mode": None,
                        "target": None,
                        "message": None,
                    }
                )
                state.interview_answers = interview_answers
                state.interview_questions_loaded = False
                state.interview_context_signature = ""
                state.question_generation_owner = ""
                _set_interview_followup_state(
                    visible=True,
                    note_text="必要な確認項目を判定しています。",
                    status_text="確認項目を準備中です...",
                    tone="gray",
                    clear_questions=True,
                )
                with interview_questions_container:
                    ui.spinner(size="sm")
                    ui.label("質問を生成中...").classes("text-sm text-gray-600")
                        
                try:
                    fetcher = ArticleFetcher()
                    sources = [s.value for s in state.sources]
                    contexts = []
                    failures = []
                    if sources:
                        phase = "fetch_sources"
                        fetch_started = time.monotonic()
                        contexts, failures = await run.io_bound(fetcher.fetch_multiple_with_errors, sources, attempt_id)
                        fetch_summary = _prepare_current_mainline_fetch_summary(
                            contents=contexts,
                            failures=failures,
                            elapsed_ms=int((time.monotonic() - fetch_started) * 1000),
                        )
                        logger.info(
                            "Interview source fetch summary id=%s success=%s failure=%s elapsed_ms=%s",
                            attempt_id,
                            int(fetch_summary.get("success_count") or 0),
                            int(fetch_summary.get("failure_count") or 0),
                            int(fetch_summary.get("elapsed_ms") or 0),
                        )
                        if failures:
                            for failure in failures[:10]:
                                logger.warning(
                                    "Interview fetch failure id=%s source=%s reason=%s detail=%s",
                                    attempt_id,
                                    getattr(failure, "source", "unknown"),
                                    getattr(failure, "reason", "unknown"),
                                    getattr(failure, "detail", ""),
                                )
                            details = str(fetch_summary.get("failure_details") or "")
                            blocked = _to_plain_list(fetch_summary.get("blocked_urls"))
                            state.blocked_403_urls = blocked
                            state.pdf_assist_since_ts = time.time()
                            state.pdf_assist_candidates = []
                            state.pdf_assist_status = (
                                "403エラーを検出しました。下の『半自動PDF取り込み』から進めてください。"
                                if blocked
                                else "取得失敗を検出しました。入力ソースを修正して再試行してください。"
                            )
                            pdf_assist_status_label.text = state.pdf_assist_status
                            pdf_assist_panel.refresh()
                            _set_interview_followup_state(
                                visible=True,
                                note_text="取得できないソースがあるため、確認項目を出せません。",
                                status_text="取得できるソースへ修正してから再実行してください。",
                                tone="red",
                                clear_questions=True,
                            )
                            interview_questions_container.clear()
                            with interview_questions_container:
                                ui.label("質問生成を停止しました。取得できないソースがあります。").classes("text-red-500")
                                ui.markdown(details).classes("text-xs text-red-400")
                            logger.warning("Interview question generation blocked id=%s due_to_source_fetch_failures", attempt_id)
                            ui.notify("読み込めないソースがあります。修正後にもう一度確認項目を作成してください。", color="negative")
                            return
                        if not contexts:
                            state.pdf_assist_status = "有効なソースがありません。"
                            pdf_assist_status_label.text = state.pdf_assist_status
                            pdf_assist_panel.refresh()
                            _set_interview_followup_state(
                                visible=True,
                                note_text="有効なソースがないため、確認項目を出せません。",
                                status_text="URL/ファイルを見直してください。",
                                tone="red",
                                clear_questions=True,
                            )
                            interview_questions_container.clear()
                            with interview_questions_container:
                                ui.label("有効なソースを取得できませんでした。").classes("text-red-500")
                            logger.warning("Interview question generation blocked id=%s reason=no_valid_contents", attempt_id)
                            ui.notify("使えるソースがまだありません。URLやファイルを見直すと進めます。", color="negative")
                            return
                    _notify_source_notices(contexts)
                    phase = "generate_questions"
                    selection = _resolve_current_ui_selection()
                    type_key = str(selection.get("article_type") or "")
                    if not type_key:
                        _set_interview_followup_state(
                            visible=True,
                            note_text="選択内容が確定していないため、確認項目を出せません。",
                            status_text="目的または対象を見直してください。",
                            tone="red",
                            clear_questions=True,
                        )
                        interview_questions_container.clear()
                        with interview_questions_container:
                            ui.label("目的または対象を見直してから、もう一度質問生成してください。").classes("text-red-500")
                        logger.warning("Interview question generation blocked id=%s reason=invalid_article_type", attempt_id)
                        ui.notify("選択内容を確認してください。", color="negative")
                        return
                    content_goal_key = next((k for k, v in content_goal_options.items() if v == content_goal.value), "auto")
                    focus_key = next((k for k, v in writing_focus_options.items() if v == writing_focus.value), "auto")
                    handoff_settings = _resolve_article_type_handoff_settings(
                        article_type_key=type_key,
                        semantic_article_key=str(selection.get("semantic_article_key") or ""),
                        writing_focus_key=focus_key,
                        perspective_key="auto",
                        self_reference_policy_key=_selected_self_reference_policy_key(),
                        writer_role_text=_selected_writer_role(),
                    )
                    prompt_raw = _build_prompt_raw()
                    required_inputs = _prepare_current_mainline_required_inputs(
                        article_type_key=type_key,
                        semantic_article_key=str(selection.get("semantic_article_key") or ""),
                        content_goal_key=content_goal_key,
                        speaker_profile_input=str(handoff_settings.get("writer_role") or ""),
                        audience_profile_input=str(audience_profile_input.value or ""),
                        core_message_input=str(core_message_input.value or ""),
                        tone_profile_key=_selected_tone_profile_key(),
                    )
                    explicit_speaker_profile = str(required_inputs.get("speaker_profile_input") or "")
                    explicit_audience_profile = str(required_inputs.get("audience_profile_input") or "")
                    explicit_core_message = str(required_inputs.get("core_message_input") or "")
                    missing_required_fields = [
                        str(field)
                        for field in _to_plain_list(required_inputs.get("missing_required_fields"))
                        if str(field or "").strip()
                    ]
                    interview_context_signature = _build_interview_context_signature(
                        source_values=[s.value for s in state.sources],
                        article_type_key=type_key,
                        content_goal_key=content_goal_key,
                        user_prompt_text=prompt_raw,
                    )
                    if missing_required_fields:
                        state.question_generation_owner = "current_mainline"
                        missing_required_view = _build_current_mainline_missing_required_inputs_view(
                            missing_fields=missing_required_fields,
                        )
                        _set_interview_followup_state(
                            visible=True,
                            note_text="確認項目を増やす前に、上の必須入力を埋めてください。",
                            status_text=str(missing_required_view.get("notify_text") or ""),
                            tone="amber",
                            clear_questions=True,
                        )
                        interview_questions_container.clear()
                        with interview_questions_container:
                            ui.label("質問生成の前に、必須入力を埋めてください。").classes("text-amber-700")
                        logger.info(
                            "Interview question generation redirected to required inputs id=%s missing=%s",
                            attempt_id,
                            ",".join(missing_required_fields),
                        )
                        ui.notify(str(missing_required_view.get("notify_text") or "必須入力を埋めてください。"), color="warning")
                        return
                    question_policy: Dict[str, Any] = {}
                    try:
                        question_policy = assess_current_mainline_question_policy(
                            source_values=[s.value for s in state.sources],
                            source_documents=contexts,
                            article_type=type_key,
                            ui_journey=selection.get("ui_journey"),
                            comparison_axes=selection.get("comparison_axes"),
                            user_prompt_text=prompt_raw,
                            content_goal_key=content_goal_key,
                            writing_focus_key=str(handoff_settings.get("writing_focus") or focus_key),
                            structure_key="auto",
                            length_mode_key=next((k for k, v in length_mode_options.items() if v == length_mode.value), "adaptive"),
                            tone_profile_key=_selected_tone_profile_key() or "auto",
                            perspective_key=str(handoff_settings.get("perspective") or "auto"),
                            allow_experience=bool(allow_experience_checkbox.value),
                            interview_answers=interview_answers,
                            speaker_profile_input=explicit_speaker_profile,
                            audience_profile_input=explicit_audience_profile,
                            core_message_input=explicit_core_message,
                            self_reference_policy_key=str(
                                handoff_settings.get("self_reference_policy")
                                or _selected_self_reference_policy_key()
                            ),
                            branding_subtype_key=_selected_branding_subtype_key(),
                            branding_focus_key=_selected_branding_focus_key(),
                            pattern_key=_selected_pattern_key(),
                            strict_saas_mode=CURRENT_MAINLINE_STRICT_SAAS_MODE,
                            source_mode=source_mode_key,
                            industry_hint="",
                        )
                    except Exception as exc:
                        logger.warning(
                            "Interview question policy assessment failed id=%s error=%s",
                            attempt_id,
                            exc,
                        )
                    reason_map = {
                        "llm_exception": "LLM呼び出しエラー",
                        "empty_response": "LLM応答が空",
                        "json_array_not_found": "JSON配列が見つからない",
                        "json_parse_error": "JSON解析失敗",
                        "invalid_schema": "スキーマ不一致",
                        "announcement_sufficient_input": "入力が十分",
                        "category_sufficient_input": "入力が十分",
                        "default_sufficient_input": "入力が十分",
                        "prompt_intent_clear_company_intro": "入力が十分",
                        "missing_required_inputs": "補いたい入力があります",
                        "already_answered": "回答済み",
                        "unknown": "不明",
                    }
                    if question_policy and bool(question_policy.get("blocked")):
                        state.question_generation_owner = "current_mainline"
                        reason_code = str(question_policy.get("reason_code") or "INP_NON_GENERATION_REQUEST")
                        _set_interview_followup_state(
                            visible=True,
                            note_text="記事生成依頼ではないため、確認項目を停止しました。",
                            status_text="記事生成したい内容を入力してください。",
                            tone="red",
                            clear_questions=True,
                        )
                        interview_questions_container.clear()
                        with interview_questions_container:
                            ui.label("記事生成ではない依頼のため、質問生成を停止しました。").classes("text-red-500")
                        logger.info(
                            "Interview question generation blocked by current mainline policy id=%s reason_code=%s",
                            attempt_id,
                            reason_code,
                        )
                        ui.notify("記事生成依頼を入力してください。", color="warning")
                        return
                    current_question_items = _filter_current_mainline_question_items_for_ui(
                        question_policy.get("question_items")
                    )
                    if current_question_items:
                        state.question_generation_owner = "current_mainline"
                        answer_key_map = {
                            "speaker_profile": "writer_role",
                            "audience_profile": "target",
                            "core_message": "message",
                        }
                        interview_questions_container.clear()
                        with interview_questions_container:
                            for item in current_question_items:
                                normalized_item = _to_plain_dict(item)
                                field = str(normalized_item.get("field", "") or "")
                                answer_key = answer_key_map.get(field, field or "message")
                                question_text = str(normalized_item.get("question_template", "") or field)
                                example_answer = str(normalized_item.get("example_answer", "") or "")
                                option_items = [
                                    _to_plain_dict(option)
                                    for option in _to_plain_list(normalized_item.get("options"))
                                    if str(_to_plain_dict(option).get("value") or "").strip()
                                    and str(_to_plain_dict(option).get("label") or "").strip()
                                ]
                                with ui.card().classes("w-full p-3"):
                                    ui.label(question_text).classes("font-semibold mb-2 w-full").style("white-space: normal; overflow-wrap: anywhere;")
                                    if option_items:
                                        option_map = {
                                            str(option.get("value") or ""): str(option.get("label") or "")
                                            for option in option_items
                                        }
                                        select_field = ui.select(
                                            options=option_map,
                                            value=str(interview_answers.get(answer_key) or "").strip() or None,
                                            label="選択してください",
                                        ).classes("w-full").props("outlined stack-label")
                                        select_field.bind_value_to(interview_answers, answer_key)
                                        select_field.on(
                                            "update:model-value",
                                            lambda _: _invalidate_journey_confirmation(),
                                        )
                                        for option in option_items:
                                            description = str(option.get("description") or "").strip()
                                            if description:
                                                ui.label(
                                                    f"{str(option.get('label') or '').strip()}: {description}"
                                                ).classes("text-xs text-gray-600")
                                    else:
                                        input_field = ui.input(
                                            label="自由入力",
                                            placeholder=example_answer or "入力してください",
                                        ).classes("w-full").props("outlined stack-label")
                                        input_field.bind_value_to(interview_answers, answer_key)
                                        input_field.on(
                                            "update:model-value",
                                            lambda _: _invalidate_journey_confirmation(),
                                        )
                        state.interview_context_signature = interview_context_signature
                        state.interview_questions_loaded = True
                        state.interview_answers = interview_answers
                        logger.info(
                            "Interview question generation resolved by current mainline owner id=%s questions=%s",
                            attempt_id,
                            len(current_question_items),
                        )
                        _record_ui_journey_event(
                            attempt_id=attempt_id,
                            event="interview_questions_current_mainline_ready",
                            article_type=type_key,
                            phase=phase,
                            user_prompt_text=prompt_raw,
                            source_items=state.sources,
                            extra={
                                "question_generation_owner": state.question_generation_owner,
                                "question_count": len(current_question_items),
                            },
                        )
                        _set_interview_followup_state(
                            visible=True,
                            note_text="このケースで必要な確認項目です。回答後に、もう一度生成前チェックを確認してください。",
                            status_text="回答を入れると確定状態は解除されます。",
                            tone="gray",
                        )
                        ui.notify("現在の入力で確認したい項目を表示しました。回答後に記事を生成してください。", color="info")
                        return
                    if question_policy and (
                        not bool(question_policy.get("should_ask")) or not current_question_items
                    ):
                        state.question_generation_owner = "current_mainline"
                        pending_items = _to_plain_list(question_policy.get("needs_input_items"))
                        if pending_items:
                            _set_interview_followup_state(
                                visible=True,
                                note_text="質問ではなく、上の入力欄またはソース補足が必要です。",
                                status_text="入力欄またはソースを補ってから、もう一度生成前チェックを確認してください。",
                                tone="amber",
                                clear_questions=True,
                            )
                            interview_questions_container.clear()
                            with interview_questions_container:
                                ui.label("このケースは質問生成ではなく、入力欄またはソースの補足が必要です。").classes("text-amber-700")
                            logger.info(
                                "Interview question generation redirected to direct input update id=%s reason=%s",
                                attempt_id,
                                str(question_policy.get("reason") or "unknown"),
                            )
                            _record_ui_journey_event(
                                attempt_id=attempt_id,
                                event="interview_questions_redirected_current_mainline",
                                article_type=type_key,
                                phase=phase,
                                user_prompt_text=prompt_raw,
                                source_items=state.sources,
                                extra={
                                    "question_generation_owner": state.question_generation_owner,
                                    "reason": str(question_policy.get("reason") or "unknown"),
                                },
                            )
                            ui.notify("入力欄またはソースを補うと、確認項目の作成に進めます。", color="warning")
                            return
                        raw_reason = str(question_policy.get("reason") or "unknown")
                        reason_label = reason_map.get(raw_reason, raw_reason)
                        logger.info(
                            "Interview question generation skipped by current mainline policy id=%s reason=%s",
                            attempt_id,
                            raw_reason,
                        )
                        _set_interview_followup_state(visible=False, clear_questions=True)
                        interview_questions_container.clear()
                        with interview_questions_container:
                            ui.label("この入力内容なら、生成前質問なしで進められます。").classes("text-green-700")
                        state.interview_context_signature = interview_context_signature
                        state.interview_questions_loaded = False
                        state.interview_answers = interview_answers
                        _record_ui_journey_event(
                            attempt_id=attempt_id,
                            event="interview_questions_skipped_current_mainline",
                            article_type=type_key,
                            phase=phase,
                            user_prompt_text=prompt_raw,
                            source_items=state.sources,
                            extra={
                                "question_generation_owner": state.question_generation_owner,
                                "reason": raw_reason,
                            },
                        )
                        ui.notify(
                            f"質問は省略しました（理由: {reason_label}）",
                            color="info",
                        )
                        return
                    state.question_generation_owner = "current_mainline"
                    _set_interview_followup_state(
                        visible=True,
                        note_text="質問 UI は出さず、足りない情報だけを上の入力欄で補ってください。",
                        status_text="追加質問は unresolved slot のみ扱います。",
                        tone="amber",
                        clear_questions=True,
                    )
                    interview_questions_container.clear()
                    with interview_questions_container:
                        ui.label("追加質問は unresolved slot のみ扱います。必要なら上の入力欄で直接補ってください。").classes("text-amber-700")
                    logger.info(
                        "Interview question generation limited to unresolved slots id=%s reason=no_supported_question_items",
                        attempt_id,
                    )
                    _record_ui_journey_event(
                        attempt_id=attempt_id,
                        event="interview_questions_limited_to_unresolved_slots",
                        article_type=type_key,
                        phase=phase,
                        user_prompt_text=prompt_raw,
                        source_items=state.sources,
                        extra={
                            "question_generation_owner": state.question_generation_owner,
                            "reason": "no_supported_question_items",
                        },
                    )
                    ui.notify("足りない情報だけ入力してください。", color="info")
                    return
                except Exception:
                    logger.exception("Failed to generate interview questions id=%s phase=%s", attempt_id, phase)
                    _set_interview_followup_state(
                        visible=True,
                        note_text="確認項目の表示に失敗しました。",
                        status_text="時間をおいて再試行してください。",
                        tone="red",
                        clear_questions=True,
                    )
                    interview_questions_container.clear()
                    with interview_questions_container:
                        ui.label("質問生成に失敗しました。時間をおいて再試行してください。").classes("text-red-500")
                finally:
                    interview_generate_busy = False
                    interview_generate_button.enable()

            interview_generate_button.on("click", lambda _: load_interview_questions())

            with ui.row().classes("w-full mt-3"):
                generate_button = ui.button("記事を生成").classes("primary-btn w-full")
            generate_button.visible = True
            generate_gate_hint = ui.label(
                "上の生成前チェックで内容を確定すると、このボタンから進めます。"
            ).classes("text-sm font-medium text-amber-800")
            generate_gate_hint.visible = False
            with ui.card().classes("w-full p-3 gap-2").style(
                "border: 1px solid rgba(217,119,6,0.24); background: #FFFBEB;"
            ) as source_session_cta_card:
                source_session_cta_title = ui.label("").classes("text-sm font-semibold text-amber-800")
                source_session_cta_hint = ui.label("").classes("text-xs text-amber-700")
                with ui.row().classes("w-full gap-2"):
                    source_session_cta_keep_button = ui.button("この資料を使う").props("outline")
                    source_session_cta_reset_button = ui.button("新しく始める").props("outline")
            source_session_cta_card.visible = False
            source_session_cta_keep_button.on("click", lambda _: _accept_current_source_session())
            source_session_cta_reset_button.on("click", lambda _: _reset_current_source_session())
            _refresh_source_session_notice()
            status_label = ui.label("").classes("text-sm font-medium text-[#5D4A41]")
            generation_progress = ui.linear_progress(value=0.0).classes("w-full")
            generation_progress.visible = False
            generation_progress_note = ui.label("").classes("text-sm font-semibold text-[#7A3A16]")
            generation_progress_note.visible = False
            source_error_area = ui.markdown("").classes("text-xs text-red-500")
            pdf_assist_status_label = ui.label("").classes("text-xs text-amber-700")

            async def scan_recent_pdfs() -> None:
                since = state.pdf_assist_since_ts or (time.time() - 1800)
                state.pdf_assist_status = "ダウンロードフォルダを検索中..."
                pdf_assist_status_label.text = state.pdf_assist_status
                pdf_assist_panel.refresh()
                candidates = await run.io_bound(_find_recent_pdf_candidates, since)
                state.pdf_assist_candidates = candidates
                if candidates:
                    state.pdf_assist_status = f"PDF候補を{len(candidates)}件検出しました。必要なファイルを追加してください。"
                else:
                    state.pdf_assist_status = "候補PDFが見つかりませんでした。PDF保存後に再スキャンしてください。"
                pdf_assist_status_label.text = state.pdf_assist_status
                pdf_assist_panel.refresh()

            def open_source_in_new_tab(url: str) -> None:
                safe = json.dumps(url)
                ui.run_javascript(f"window.open({safe}, '_blank')")

            def import_pdf_candidate(path: str) -> None:
                try:
                    ingested = _ingest_local_pdf_to_uploads(path)
                    _add_source(Path(path).name, ingested, "file")
                except Exception as exc:
                    ui.notify(f"PDF取り込みに失敗しました: {exc}", color="negative")
                    return
                state.pdf_assist_candidates = [p for p in state.pdf_assist_candidates if p != path]
                state.pdf_assist_status = "PDFを取り込みました。再度「記事を生成」を実行してください。"
                pdf_assist_status_label.text = state.pdf_assist_status
                pdf_assist_panel.refresh()
                ui.notify("PDFをソースに追加しました。", color="positive")

            def clear_pdf_assist_ui() -> None:
                _reset_pdf_assist()
                pdf_assist_status_label.text = ""
                pdf_assist_panel.refresh()

            @ui.refreshable
            def pdf_assist_panel() -> None:
                should_show = bool(state.blocked_403_urls or state.pdf_assist_candidates or state.pdf_assist_status)
                if not should_show:
                    return
                with ui.card().classes("w-full bg-amber-50 p-3 mt-2"):
                    ui.label("403時の半自動PDF取り込み").classes("text-sm font-semibold text-amber-800")
                    ui.label(
                        "何が起きているか: URL取得が拒否されたため、手動PDF化したファイルを安全に取り込む補助を表示しています。"
                    ).classes("text-xs text-amber-700")
                    if state.blocked_403_urls:
                        ui.label("手順1: 対象URLを別タブで開く").classes("text-xs font-semibold mt-1")
                        for blocked_url in state.blocked_403_urls:
                            with ui.row().classes("w-full items-center gap-2"):
                                ui.label(blocked_url).classes("text-[11px] text-amber-700 break-all")
                                ui.button(
                                    "別タブで開く",
                                    on_click=lambda u=blocked_url: open_source_in_new_tab(u),
                                ).props("flat dense")
                        ui.label("手順2: ブラウザの印刷機能でPDF保存").classes("text-xs font-semibold mt-1")
                        ui.label("手順3: 下のボタンでダウンロードフォルダを再スキャン").classes("text-xs text-amber-700")
                        ui.button("PDF候補を再スキャン", on_click=scan_recent_pdfs).props("flat").classes("mt-1")
                    if state.pdf_assist_candidates:
                        ui.separator()
                        ui.label("手順4: 取り込みたいPDFを選択").classes("text-xs font-semibold")
                        for candidate in state.pdf_assist_candidates:
                            with ui.row().classes("w-full items-center gap-2"):
                                ui.label(Path(candidate).name).classes("text-[11px] text-gray-700 break-all")
                                ui.button(
                                    "このPDFを追加",
                                    on_click=lambda p=candidate: import_pdf_candidate(p),
                                ).props("flat dense")
                    ui.button("補助表示を閉じる", on_click=clear_pdf_assist_ui).props("flat dense").classes("mt-1")

            spinner = ui.spinner(size="md")
            spinner.visible = False
            generation_started_at: Optional[float] = None
            
            # インタビュー回答をstate経由でジェネレーターに渡すための準備
            state.interview_answers = interview_answers
            _refresh_journey_confirmation_cta()

        image_section_widgets: Dict[str, Any] = {}

        def _render_image_auto_panel() -> None:
            ui.separator()
            with ui.card().classes("w-full bg-[#FFF8F2] border border-[#E8D7C8] p-4 rounded-lg"):
                with ui.row().classes("items-center gap-2 mb-1"):
                    ui.icon("image").classes("text-[#8A4A1C]")
                    ui.label("記事に合わせた画像").classes("output-section-title text-[#5D4A41]")
                ui.label("記事生成後に、文字入り画像と文字なし画像を自動で作成します。").classes("section-muted-note mb-1")
                ui.label(f"推奨サイズに自動整形: {NOTE_IMAGE_SIZE_LABEL}").classes("text-xs text-gray-600 mb-2")
                with ui.row().classes("w-full mt-2 gap-2 items-center"):
                    image_section_widgets["image_spinner"] = ui.spinner(size="md")
                    image_section_widgets["image_spinner"].visible = False
                    image_section_widgets["image_status"] = ui.label("").classes("text-sm text-gray-600")
                image_section_widgets["image_progress"] = ui.linear_progress(value=0.0).classes("w-full")
                image_section_widgets["image_progress"].visible = False
                image_section_widgets["image_progress_note"] = ui.label("").classes("text-xs text-gray-600")
                image_section_widgets["image_progress_note"].visible = False
                image_section_widgets["image_elapsed"] = ui.label("").classes("text-xs text-gray-600")
                image_section_widgets["image_elapsed"].visible = False
                with ui.expansion("画像の設定を見る", icon="tune").classes("w-full mt-2 secondary-support-expansion"):
                    ui.label("仕上がりの方向を選びます。記事生成前に選んだ内容で画像を作ります。").classes("text-xs text-gray-600 mb-2")
                    image_section_widgets["image_pattern_select"] = ui.select(
                        options=[option["label"] for option in IMAGE_PATTERN_OPTIONS.values()],
                        value=IMAGE_PATTERN_OPTIONS[DEFAULT_IMAGE_PATTERN_KEY]["label"],
                        label="画像パターン",
                    ).classes("w-full").props("outlined stack-label")
                    ui.label("3パターンから選べます。既定はシンプルです。").classes(
                        "text-xs text-gray-600 mb-2"
                    )
                ui.label("保存ボタンを押すと、ブラウザの保存画面が開きます（保存先はブラウザ設定に従います）。").classes("text-xs text-gray-600 mt-2")
                generated_images_container()

        result_sections = render_result_output_sections(
            preview_placeholder=_PREVIEW_PLACEHOLDER,
            render_between_preview_and_details=_render_image_auto_panel,
        )
        output_stage_shell = result_sections["output_stage_shell"]
        step3_badge = result_sections["step3_badge"]
        stats_label = result_sections["stats_label"]
        preview = result_sections["preview"]
        note_body_text = result_sections["note_body_text"]
        title_area = result_sections["title_area"]
        hashtags_area = result_sections["hashtags_area"]
        lead_area = result_sections["lead_area"]
        body_area = result_sections["body_area"]
        references_area = result_sections["references_area"]
        full_text_area = result_sections["full_text_area"]
        linkedin_area = result_sections["linkedin_area"]
        linkedin_short_area = result_sections["linkedin_short_area"]
        result_sections["copy_note_format_button"].on(
            "click",
            lambda: _copy_text(_to_note_format(note_body_text.value)),
        )
        result_sections["copy_markdown_button"].on("click", lambda: _copy_text(note_body_text.value))
        result_sections["copy_title_button"].on("click", lambda: _copy_text(title_area.value))
        result_sections["copy_hashtags_button"].on("click", lambda: _copy_text(hashtags_area.value))
        result_sections["copy_lead_button"].on("click", lambda: _copy_text(lead_area.value))
        result_sections["copy_body_button"].on("click", lambda: _copy_text(body_area.value))
        result_sections["copy_references_button"].on("click", lambda: _copy_text(references_area.value))
        result_sections["copy_full_text_button"].on("click", lambda: _copy_text(full_text_area.value))
        result_sections["copy_linkedin_button"].on("click", lambda: _copy_text(linkedin_area.value))
        result_sections["copy_linkedin_short_button"].on(
            "click",
            lambda: _copy_text(linkedin_short_area.value),
        )
        image_spinner = image_section_widgets["image_spinner"]
        image_status = image_section_widgets["image_status"]
        image_progress = image_section_widgets["image_progress"]
        image_progress_note = image_section_widgets["image_progress_note"]
        image_elapsed = image_section_widgets["image_elapsed"]
        image_pattern_select = image_section_widgets["image_pattern_select"]

        def _refresh_output_stage_visibility() -> None:
            show_output_stage = bool(
                getattr(state, "busy", False) or str(getattr(note_body_text, "value", "") or "").strip()
            )
            output_stage_shell.visible = show_output_stage
            output_stage_shell.update()

        image_elapsed_start = None

        def _update_image_elapsed() -> None:
            current_token = _CLIENT_GENERATION_TOKENS.get(_normalize_client_key(client_key), "")
            if not _is_client_generation_attached(client_key, current_token):
                image_elapsed_timer.deactivate()
                return
            if image_elapsed_start is None:
                return
            elapsed = int(time.monotonic() - image_elapsed_start)
            updated = _run_attached_ui_mutation(
                client_key=client_key,
                generation_token=current_token,
                mutation=lambda: setattr(image_elapsed, "text", f"経過: {elapsed}秒"),
                action_name="image_elapsed",
            )
            if not updated:
                image_elapsed_timer.deactivate()

        def _set_image_progress(percent: int, status: str = "", generation_token: str = "") -> bool:
            bounded = max(0, min(100, int(percent)))
            token = generation_token or _CLIENT_GENERATION_TOKENS.get(_normalize_client_key(client_key), "")

            def _apply_image_progress() -> None:
                image_progress.value = bounded / 100.0
                image_progress_note.text = f"進行度: {bounded}%"
                if status:
                    image_status.text = status

            return _run_attached_ui_mutation(
                client_key=client_key,
                generation_token=token,
                mutation=_apply_image_progress,
                action_name="image_progress",
            )

        image_elapsed_timer = _register_client_timer(
            client_key,
            ui.timer(0.5, _update_image_elapsed, active=False),
        )
        ui.context.client.on_disconnect(lambda: image_elapsed_timer.deactivate())

        quality_summary_card = result_sections["quality_summary_card"]
        quality_summary_badge = result_sections["quality_summary_badge"]
        quality_summary_title = result_sections["quality_summary_title"]
        quality_summary_note = result_sections["quality_summary_note"]
        quality_summary_row_widgets = result_sections["quality_summary_row_widgets"]
        review_container = result_sections["review_container"]
        review_row_kousei = result_sections["review_row_kousei"]
        review_kousei_label = result_sections["review_kousei_label"]
        review_row_buntai = result_sections["review_row_buntai"]
        review_buntai_label = result_sections["review_buntai_label"]
        review_row_konkyo = result_sections["review_row_konkyo"]
        review_konkyo_label = result_sections["review_konkyo_label"]

        def _to_user_friendly_progress(progress: Dict[str, Any]) -> str:
            stage = str(progress.get("stage", "") or "").strip().lower()
            if stage.startswith("route_0506"):
                return str(build_route_0506_progress_view(stage).get("label_text") or "Route 0506 で処理中...")
            stage_labels = {
                "validate": "入力を確認中...",
                "prepare": "現在準備中...",
                "fetch_sources": "ソース取得中...",
                "outline": "現在執筆の準備中...",
                "body": "現在執筆中...",
                "polish": "現在編集中...",
                "generate_article": "本文を生成中...",
                "quality_output_guard": "品質を検証中...",
                "legal_postcheck": "リーガルチェック中...",
                "auto_retry_transient": "一時障害のため再試行中...",
                "render_output": "出力を整形中...",
                "generate_image_prompts": "画像用プロンプトを準備中...",
                "generate_images": "記事に合わせた画像を生成中...",
                "completed": "生成が完了しました。",
            }
            return stage_labels.get(stage, "現在処理中...")

        def _generation_phase_progress(phase_key: str) -> int:
            normalized_phase = str(phase_key or "").strip().lower()
            if normalized_phase.startswith("route_0506"):
                return int(build_route_0506_progress_view(normalized_phase).get("percent") or 0)
            phase_progress = {
                "validate": 3,
                "prepare": 8,
                "fetch_sources": 20,
                "generate_article": 65,
                "quality_output_guard": 82,
                "legal_postcheck": 88,
                "auto_retry_transient": 86,
                "render_output": 90,
                "generate_image_prompts": 94,
                "generate_images": 96,
                "complete": 100,
                "completed": 100,
            }
            return int(phase_progress.get(normalized_phase, 0))

        def _set_generation_phase_ui(phase_key: str, detail: str = "", generation_token: str = "") -> bool:
            nonlocal generation_started_at
            phase_norm = str(phase_key or "").strip().lower()
            label_text = _to_user_friendly_progress({"stage": phase_norm})
            base_percent = _generation_phase_progress(phase_norm)
            token = generation_token or _CLIENT_GENERATION_TOKENS.get(_normalize_client_key(client_key), "")

            def _apply_generation_phase() -> None:
                current_percent = int(round(float(generation_progress.value or 0.0) * 100))
                bounded = max(current_percent, max(0, min(100, base_percent)))
                generation_progress.value = bounded / 100.0
                elapsed = ""
                if generation_started_at is not None:
                    elapsed = f"（経過{int(time.monotonic() - generation_started_at)}秒）"
                suffix = f" {detail.strip()}" if detail and detail.strip() else ""
                status_label.text = f"{label_text} {bounded}%".strip()
                generation_progress_note.text = _format_generation_progress_text(
                    percent=bounded,
                    label_text=label_text,
                    detail=suffix,
                    elapsed=elapsed,
                )
                generation_progress_note.visible = True

            return _run_attached_ui_mutation(
                client_key=client_key,
                generation_token=token,
                mutation=_apply_generation_phase,
                action_name="generation_phase",
            )

        def _update_generation_progress() -> None:
            current_token = _CLIENT_GENERATION_TOKENS.get(_normalize_client_key(client_key), "")
            if not _is_client_generation_attached(client_key, current_token):
                generation_progress_timer.deactivate()
                return
            if not getattr(state, "busy", False):
                return
            try:
                progress = _get_or_create_current_mainline_pipeline(client_key).get_generation_progress()
            except Exception:
                return

            stage = str(progress.get("stage", "") or "").strip().lower()
            percent = progress.get("percent", 0)
            if stage == "completed":
                percent = 100

            label_text = _to_user_friendly_progress(progress)
            display_percent = _resolve_display_generation_percent(
                current_value=float(generation_progress.value or 0.0),
                reported_percent=percent,
            )
            elapsed = ""
            if generation_started_at is not None:
                elapsed = f"（経過{int(time.monotonic() - generation_started_at)}秒）"

            def _apply_generation_progress() -> None:
                if display_percent > 0 or stage == "completed":
                    status_label.text = f"{label_text} {display_percent}%".strip()
                else:
                    status_label.text = label_text
                generation_progress.value = display_percent / 100.0
                generation_progress_note.text = _format_generation_progress_text(
                    percent=display_percent,
                    label_text=label_text,
                    elapsed=elapsed,
                )
                generation_progress_note.visible = True

                if not ENABLE_LIVE_DRAFT_STREAM:
                    return

                partial_body = str(progress.get("partial_body", "") or "")
                if partial_body and partial_body != body_area.value:
                    body_area.value = partial_body
                    draft_parts = [lead_area.value, partial_body]
                    note_body_text.value = "\n\n".join(p for p in draft_parts if p)
                    draft_title = title_area.value or "生成中..."
                    preview.content = sanitize_markdown_preview(f"{draft_title}\n\n{note_body_text.value}")
                    stats_label.text = f"記事本文: {len(note_body_text.value)}文字"

            updated = _run_attached_ui_mutation(
                client_key=client_key,
                generation_token=current_token,
                mutation=_apply_generation_progress,
                action_name="generation_progress",
            )
            if not updated:
                generation_progress_timer.deactivate()

        generation_progress_timer = _register_client_timer(
            client_key,
            ui.timer(0.6, _update_generation_progress, active=False),
        )
        ui.context.client.on_disconnect(lambda: generation_progress_timer.deactivate())

        _STEP_ALL_COLORS = (
            "bg-orange-500 text-white "
            "bg-green-100 text-green-700 "
            "bg-gray-100 text-gray-400 "
            "bg-orange-50 text-orange-600"
        )

        def _set_step(badge, style: str, text: str) -> None:
            badge.classes(remove=_STEP_ALL_COLORS, add=style)
            badge.text = text
            badge.update()

        _STICKY_NOT_DONE = "step-track-active step-track-pending"

        def _mark_sticky_done(badge, text: str) -> None:
            """Python が done 状態を付与。JS は done 付きバッジを触らない。"""
            badge.classes(remove=_STICKY_NOT_DONE, add="step-track-done")
            badge.text = text
            badge.update()

        def _unmark_sticky_done(badge) -> None:
            """done 状態を外す。その後 JS が active/pending を付与。"""
            badge.classes(remove="step-track-done")
            badge.update()

        def _refresh_step_indicators() -> None:
            has_sources = len(getattr(state, "sources", [])) > 0
            has_result  = bool(getattr(note_body_text, "value", ""))
            is_busy     = getattr(state, "busy", False)
            _refresh_output_stage_visibility()
            if has_result:
                _set_step(step1_badge, "bg-green-100 text-green-700", "✓ 入力")
                _set_step(step2_badge, "bg-green-100 text-green-700", "✓ 生成準備")
                _set_step(step3_badge, "bg-orange-500 text-white",    "← 生成結果")
                _mark_sticky_done(sticky_step1, "✓ 入力")
                _mark_sticky_done(sticky_step2, "✓ 生成準備")
                _unmark_sticky_done(sticky_step3)
            elif is_busy or has_sources:
                _set_step(step1_badge, "bg-green-100 text-green-700", "✓ 入力")
                _set_step(step2_badge, "bg-orange-500 text-white",    "← 生成準備")
                _set_step(step3_badge, "bg-gray-100 text-gray-400",   "生成結果")
                _mark_sticky_done(sticky_step1, "✓ 入力")
                _unmark_sticky_done(sticky_step2)
                _unmark_sticky_done(sticky_step3)
            else:
                _set_step(step1_badge, "bg-orange-500 text-white",    "← 入力")
                _set_step(step2_badge, "bg-gray-100 text-gray-400",   "生成準備")
                _set_step(step3_badge, "bg-gray-100 text-gray-400",   "生成結果")
                _unmark_sticky_done(sticky_step1)
                _unmark_sticky_done(sticky_step2)
                _unmark_sticky_done(sticky_step3)

        def _refresh_step_and_invalidate() -> None:
            _refresh_step_indicators()
            _invalidate_journey_confirmation()
            _refresh_source_mode_status()

        state.step_refresh_callback = _refresh_step_and_invalidate
        _refresh_step_indicators()

        async def run_generation() -> None:
            nonlocal image_elapsed_start
            attempt_id = _new_operation_id("gen")
            generation_token = _start_client_generation(client_key, attempt_id)
            started_at = time.monotonic()
            phase = "validate"
            outcome = "rejected"
            if not await _ensure_usage_credit_available("kotomake"):
                _finish_client_generation(client_key, generation_token)
                return

            def _run_generation_ui_mutation(mutation: Callable[[], None], action_name: str) -> bool:
                return _run_attached_ui_mutation(
                    client_key=client_key,
                    generation_token=generation_token,
                    mutation=mutation,
                    action_name=action_name,
                )

            def _set_generation_phase_for_attempt(phase_key: str, detail: str = "") -> bool:
                return _set_generation_phase_ui(phase_key, detail, generation_token=generation_token)

            def _notify_generation(message: str, color: str = "info") -> bool:
                return _run_generation_ui_mutation(
                    lambda: ui.notify(message, color=color),
                    "generation_notify",
                )

            async def _run_post_success_downstream_phases(
                *,
                result: Dict[str, Any],
                render_note_body_text: str,
                article_type_for_image: str,
            ) -> str:
                nonlocal image_elapsed_start
                downstream_phase = "legal_postcheck"
                if LEGAL_POSTCHECK_AUTO_ENABLED:
                    _set_generation_phase_for_attempt(downstream_phase)
                auto_legal_postcheck = await _resolve_current_mainline_auto_legal_postcheck(
                    result=result,
                    note_body_text=render_note_body_text,
                    verified_texts=_current_legal_verified_texts(),
                    io_bound_runner=run.io_bound,
                    auto_enabled=LEGAL_POSTCHECK_AUTO_ENABLED,
                )
                legal_postcheck_payload = _prepare_current_mainline_legal_postcheck_payload(
                    auto_legal_postcheck=_to_plain_dict(auto_legal_postcheck),
                    note_body_text=render_note_body_text,
                )
                resolved_legal_result = _to_plain_dict(legal_postcheck_payload.get("legal_result"))
                _run_generation_ui_mutation(
                    lambda: (
                        _render_legal_result(resolved_legal_result) if resolved_legal_result else None,
                        setattr(
                            legal_input,
                            "value",
                            str(legal_postcheck_payload.get("legal_input_text") or render_note_body_text),
                        ),
                        setattr(
                            legal_status,
                            "text",
                            str(legal_postcheck_payload.get("legal_status_text") or ""),
                        ),
                    ),
                    "legal_postcheck_ui",
                )
                usage_action = str(legal_postcheck_payload.get("usage_action") or "")
                if usage_action:
                    usage_log_extra = _to_plain_dict(legal_postcheck_payload.get("usage_log_extra"))
                    _log_ui_usage(
                        "legal_postcheck",
                        usage_action,
                        **usage_log_extra,
                    )

                downstream_phase = "generate_images"
                _set_generation_phase_for_attempt(downstream_phase)
                image_pattern_key = IMAGE_PATTERN_LABEL_TO_KEY.get(
                    str(image_pattern_select.value or ""),
                    DEFAULT_IMAGE_PATTERN_KEY,
                )
                state.generated_images = []
                state.generated_image_variants = []
                state.image_generation_status = "running"
                image_elapsed_start = time.monotonic()
                _run_generation_ui_mutation(
                    lambda: (
                        generated_images_container.refresh(),
                        setattr(image_spinner, "visible", True),
                        setattr(image_progress, "visible", True),
                        setattr(image_progress_note, "visible", True),
                        setattr(image_elapsed, "visible", True),
                        setattr(image_elapsed, "text", "経過: 0秒"),
                        image_elapsed_timer.activate(),
                    ),
                    "image_generation_start_ui",
                )
                _set_image_progress(0, "画像生成の準備中...", generation_token=generation_token)
                try:
                    auto_image_result = await run.io_bound(
                        lambda: generate_blog_images_for_article(
                            llm=generator.llm,
                            title=str(result.get("title") or ""),
                            lead=str(result.get("lead") or ""),
                            body=str(result.get("body") or ""),
                            article_type=article_type_for_image,
                            pattern_key=image_pattern_key,
                            model=DEFAULT_IMAGE_MODEL,
                            size=DEFAULT_IMAGE_SIZE,
                            plain_quality=DEFAULT_IMAGE_QUALITY,
                            text_quality=DEFAULT_TEXT_IMAGE_QUALITY,
                            output_format=DEFAULT_IMAGE_OUTPUT_FORMAT,
                            background=DEFAULT_IMAGE_BACKGROUND,
                            moderation=DEFAULT_IMAGE_MODERATION,
                        )
                    )
                    state.generated_image_variants = _to_plain_list(auto_image_result.get("variants"))
                    state.generated_images = successful_image_paths(auto_image_result)
                    state.image_generation_status = str(auto_image_result.get("status") or "failed")
                    if state.image_generation_status == "success":
                        image_message = "画像を生成しました"
                    elif state.image_generation_status == "partial":
                        image_message = "一部の画像を生成しました"
                    else:
                        image_message = "画像生成に失敗しました。記事本文はそのまま使えます。"
                    _set_image_progress(100, image_message, generation_token=generation_token)
                    _log_ui_usage(
                        "image_generation",
                        "auto_complete",
                        status=state.image_generation_status,
                        image_count=len(state.generated_images),
                    )
                except Exception:
                    logger.exception("Automatic blog image generation failed open")
                    state.generated_images = []
                    state.generated_image_variants = []
                    state.image_generation_status = "failed"
                    _run_generation_ui_mutation(
                        lambda: setattr(image_status, "text", "画像生成に失敗しました。記事本文はそのまま使えます。"),
                        "image_generation_failed_ui",
                    )
                    _log_ui_usage("image_generation", "auto_failed_open")
                finally:
                    image_elapsed_timer.deactivate()
                    image_elapsed_start = None
                    _run_generation_ui_mutation(
                        lambda: (
                            setattr(image_spinner, "visible", False),
                            setattr(image_progress, "visible", False),
                            setattr(image_progress, "value", 0.0),
                            setattr(image_progress_note, "visible", False),
                            setattr(image_progress_note, "text", ""),
                            setattr(image_elapsed, "visible", False),
                            generated_images_container.refresh(),
                        ),
                        "image_generation_cleanup_ui",
                    )
                return downstream_phase

            selection = _resolve_current_ui_selection()
            selected_article_type = str(article_type.value or "")
            journey_article_type = str(selection.get("article_type") or selected_article_type or "unknown")
            journey_prompt_text = str(user_prompt.value or "").strip()
            journey_selections: Dict[str, Any] = _build_journey_selection_summary()
            telemetry_context = _build_current_mainline_run_generation_telemetry_context(
                attempt_id=attempt_id,
                article_type=journey_article_type,
                user_prompt_text=journey_prompt_text,
                source_items=state.sources,
                selections=journey_selections,
                question_generation_owner=getattr(state, "question_generation_owner", ""),
            )
            _set_generation_phase_for_attempt("validate")
            if state.busy:
                busy_view = _build_current_mainline_generation_busy_view()
                logger.info("Generation skipped id=%s reason=busy", attempt_id)
                _record_current_mainline_generation_event(
                    telemetry_context=telemetry_context,
                    event=str(busy_view.get("event_name") or "generation_rejected_busy"),
                    phase=phase,
                    reason_code=str(busy_view.get("reason_code") or "UI_BUSY"),
                    error_class=str(busy_view.get("error_class") or "ui"),
                    status_text=str(busy_view.get("status_text") or ""),
                )
                return
            # ソース必須バリデーション（URLかファイルのどちらかが必要）
            source_mode_key = _selected_source_mode_key()
            past_blog_unlocked = _past_blog_prompt_unlock_available(
                _load_current_published_post_candidates()
            )
            if (
                not state.sources
                and source_mode_key != "web"
                and not _source_mode_allows_no_sources(
                    article_type_key=str(selection.get("article_type") or ""),
                    source_mode_key=source_mode_key,
                    prompt_raw=journey_prompt_text,
                    past_blog_unlocked=past_blog_unlocked,
                )
            ):
                no_sources_view = _build_current_mainline_generation_no_sources_view()
                logger.warning("Generation rejected id=%s reason=no_sources", attempt_id)
                _notify_generation(
                    str(no_sources_view.get("notify_text") or ""),
                    str(no_sources_view.get("notify_color") or "negative"),
                )
                _record_current_mainline_generation_event(
                    telemetry_context=telemetry_context,
                    event=str(no_sources_view.get("event_name") or "generation_rejected_no_sources"),
                    phase=phase,
                    reason_code=str(no_sources_view.get("reason_code") or "INP_MISSING_REQUIRED"),
                    error_class=str(no_sources_view.get("error_class") or "user_input"),
                    status_text=str(no_sources_view.get("status_text") or ""),
                )
                return
            type_key = str(selection.get("article_type") or "")
            used_type_fallback = False
            journey_article_type = type_key or journey_article_type
            telemetry_context = _build_current_mainline_run_generation_telemetry_context(
                attempt_id=attempt_id,
                article_type=journey_article_type,
                user_prompt_text=journey_prompt_text,
                source_items=state.sources,
                selections=journey_selections,
                question_generation_owner=getattr(state, "question_generation_owner", ""),
            )
            _log_ui_usage(
                "generation",
                "run",
                article_type=type_key,
                selected_label=selected_article_type,
            )
            if not type_key or type_key not in _get_combined_prompts():
                article_type_resolution_state = "missing" if not type_key else "unsupported"
                invalid_type_view = _build_current_mainline_invalid_article_type_view(
                    semantic_article_key=str(selection.get("semantic_article_key") or ""),
                    selection_confirmed=bool(journey_selections.get("confirmed")),
                    selected_article_type_label=selected_article_type,
                    resolved_article_type=type_key,
                    article_type_resolution_state=article_type_resolution_state,
                )
                logger.warning(
                    "Generation rejected id=%s reason=invalid_article_type selected=%s resolved=%s",
                    attempt_id,
                    selected_article_type,
                    type_key,
                )
                _notify_generation(
                    str(invalid_type_view.get("notify_text") or ""),
                    str(invalid_type_view.get("notify_color") or "negative"),
                )
                _record_current_mainline_generation_event(
                    telemetry_context=telemetry_context,
                    event=str(invalid_type_view.get("event_name") or "generation_rejected_invalid_article_type"),
                    phase=phase,
                    reason_code=str(invalid_type_view.get("reason_code") or "INP_INVALID_ARTICLE_TYPE"),
                    error_class=str(invalid_type_view.get("error_class") or "user_input"),
                    status_text=str(invalid_type_view.get("status_text") or ""),
                    extra=_to_plain_dict(invalid_type_view.get("extra")),
                )
                return
            if CURRENT_MAINLINE_UI_MODE == "journey":
                _sync_source_session_acceptance_for_fresh_confirmation(
                    _get_or_create_state(client_key),
                    article_type_key=type_key,
                    current_journey_signature=_build_journey_signature(),
                    confirmed_journey_signature=str(
                        getattr(state, "journey_confirmation_signature", "")
                        or journey_confirm_state.get("signature")
                        or ""
                    ),
                )
            source_session_state = _build_source_session_review_state(
                _get_or_create_state(client_key),
                article_type_key=type_key,
            )
            if bool(source_session_state.get("requires_review")):
                source_session_status_text = str(source_session_state.get("status_text") or "")
                _run_generation_ui_mutation(
                    lambda: (
                        setattr(status_label, "text", source_session_status_text),
                        _refresh_source_session_notice(),
                        _refresh_journey_confirmation_cta(),
                    ),
                    "source_session_review_required_ui",
                )
                _notify_generation(
                    str(source_session_state.get("hint_text") or "使う資料を確認してください。"),
                    "warning",
                )
                _record_current_mainline_generation_event(
                    telemetry_context=telemetry_context,
                    event="generation_rejected_source_session_review_required",
                    phase=phase,
                    reason_code="INP_SOURCE_SESSION_REVIEW_REQUIRED",
                    error_class="user_input",
                    status_text=source_session_status_text,
                    extra={
                        "source_count": int(source_session_state.get("source_count") or 0),
                        "previous_article_type": str(source_session_state.get("previous_article_type") or ""),
                        "current_article_type": str(source_session_state.get("current_article_type") or ""),
                    },
                )
                return
            if CURRENT_MAINLINE_UI_MODE == "journey":
                current_signature = _build_journey_signature()
                confirmed_signature = str(getattr(state, "journey_confirmation_signature", "") or journey_confirm_state.get("signature") or "")
                generation_confirmation = _build_journey_generation_confirmation_state(
                    current_signature=current_signature,
                    confirmed_signature=confirmed_signature,
                )
                if not bool(generation_confirmation.get("ready")):
                    required_journey_stage = 4
                    confirmation_required_view = _build_current_mainline_confirmation_required_view(
                        semantic_article_key=str(selection.get("semantic_article_key") or ""),
                        selection_confirmed=bool(journey_selections.get("confirmed")),
                        confirmation_state=str(generation_confirmation.get("confirmation_state") or ""),
                        confirmed_signature_present=bool(generation_confirmation.get("confirmed_signature_present")),
                        required_journey_stage=required_journey_stage,
                    )
                    _run_generation_ui_mutation(
                        lambda: (
                            _go_to_journey_stage(required_journey_stage),
                            _set_journey_confirm_status(
                                str(confirmation_required_view.get("status_text") or ""),
                                tone="amber",
                            ),
                        ),
                        "confirmation_required_ui",
                    )
                    _notify_generation(
                        str(confirmation_required_view.get("notify_text") or ""),
                        str(confirmation_required_view.get("notify_color") or "warning"),
                    )
                    _record_current_mainline_generation_event(
                        telemetry_context=telemetry_context,
                        event=str(
                            confirmation_required_view.get("event_name")
                            or "generation_rejected_confirmation_required"
                        ),
                        phase=phase,
                        reason_code=str(confirmation_required_view.get("reason_code") or "INP_MISSING_REQUIRED"),
                        error_class=str(confirmation_required_view.get("error_class") or "user_input"),
                        status_text=journey_confirm_status.text,
                        extra=_to_plain_dict(confirmation_required_view.get("extra")),
                    )
                    return

            ambiguity_result = detect_ambiguous_terms(user_prompt.value or "")
            if ambiguity_result.requires_confirmation and not _is_ambiguity_confirmed(ambiguity_result):
                ambiguity_pause_view = _build_current_mainline_ambiguity_confirmation_view(
                    semantic_article_key=str(selection.get("semantic_article_key") or ""),
                    selection_confirmed=bool(journey_selections.get("confirmed")),
                    term_count=len(getattr(ambiguity_result, "candidates", []) or []),
                )
                logger.info(
                    "Generation paused id=%s reason=ambiguity_confirmation_required term_count=%s",
                    attempt_id,
                    len(getattr(ambiguity_result, "candidates", []) or []),
                )
                ambiguity_status_text = str(ambiguity_pause_view.get("status_text") or "")
                _run_generation_ui_mutation(
                    lambda: (
                        _open_ambiguity_dialog(ambiguity_result),
                        setattr(status_label, "text", ambiguity_status_text),
                    ),
                    "ambiguity_pause_ui",
                )
                _record_current_mainline_generation_event(
                    telemetry_context=telemetry_context,
                    event=str(
                        ambiguity_pause_view.get("event_name")
                        or "generation_paused_ambiguity_confirmation"
                    ),
                    phase=phase,
                    reason_code=str(
                        ambiguity_pause_view.get("reason_code") or "INP_AMBIGUITY_CONFIRMATION_REQUIRED"
                    ),
                    error_class=str(ambiguity_pause_view.get("error_class") or "user_input"),
                    status_text=ambiguity_status_text,
                    extra=_to_plain_dict(ambiguity_pause_view.get("extra")),
                )
                return
            if ambiguity_result.requires_confirmation:
                generator.set_term_clarifications(state.ambiguity_resolutions)
            else:
                state.ambiguity_signature = ""
                state.ambiguity_resolutions = {}
                generator.set_term_clarifications({})

            perspective_key = "auto"
            structure_key = "auto"
            writing_focus_key = next((k for k, v in writing_focus_options.items() if v == writing_focus.value), "auto")
            length_mode_key = next((k for k, v in length_mode_options.items() if v == length_mode.value), "adaptive")
            tone_profile_key = _selected_tone_profile_key() or "auto"
            
            # R14-T15: 経験談チェックボックスの値を取得
            allow_experience = bool(allow_experience_checkbox.value)
            content_goal_key = next((k for k, v in content_goal_options.items() if v == content_goal.value), "auto")
            semantic_article_key = str(selection.get("semantic_article_key") or "")
            handoff_settings = _resolve_article_type_handoff_settings(
                article_type_key=type_key,
                semantic_article_key=semantic_article_key,
                writing_focus_key=writing_focus_key,
                perspective_key=perspective_key,
                self_reference_policy_key=_selected_self_reference_policy_key(),
                writer_role_text=_selected_writer_role(),
            )
            selected_writer_role_for_handoff = str(handoff_settings.get("writer_role") or "")
            writing_focus_key = str(handoff_settings.get("writing_focus") or writing_focus_key)
            perspective_key = str(handoff_settings.get("perspective") or perspective_key)
            self_reference_policy_key = str(
                handoff_settings.get("self_reference_policy")
                or _selected_self_reference_policy_key()
            )
            prompt_raw = _build_prompt_raw()
            system_hint_items = _build_system_hint_items(content_goal_key)
            current_interview_signature = _build_interview_context_signature(
                source_values=[s.value for s in state.sources],
                article_type_key=type_key,
                content_goal_key=content_goal_key,
                user_prompt_text=prompt_raw,
            )
            interview_generation_state = _prepare_current_mainline_interview_state_for_generation(
                interview_answers=getattr(state, "interview_answers", {}) or {},
                interview_questions_loaded=getattr(state, "interview_questions_loaded", False),
                stored_context_signature=getattr(state, "interview_context_signature", ""),
                current_context_signature=current_interview_signature,
            )
            prepared_interview_answers = _to_plain_dict(
                interview_generation_state.get("interview_answers")
            )
            if bool(interview_generation_state.get("reset_required")):
                interview_answers.clear()
                interview_answers.update(prepared_interview_answers)
                state.interview_answers = interview_answers
                state.interview_questions_loaded = bool(
                    interview_generation_state.get("interview_questions_loaded")
                )
                state.interview_context_signature = str(
                    interview_generation_state.get("stored_context_signature") or ""
                )
                logger.info(
                    "Generation interview answers reset id=%s reason=context_signature_mismatch",
                    attempt_id,
                )
                _notify_generation("入力条件が変わったため、質問回答をリセットしました。必要なら再生成してください。", "warning")
            answered_count = int(interview_generation_state.get("answered_count") or 0)
            if bool(interview_generation_state.get("interview_questions_loaded")):
                logger.info(
                    "Generation interview answer summary id=%s questions_loaded=%s answered=%s",
                    attempt_id,
                    True,
                    answered_count,
                )
                if bool(interview_generation_state.get("notify_unanswered")):
                    _notify_generation("質問は未回答です。回答すると記事精度が上がります。", "warning")
            required_inputs = _prepare_current_mainline_required_inputs(
                article_type_key=type_key,
                semantic_article_key=semantic_article_key,
                content_goal_key=content_goal_key,
                speaker_profile_input=selected_writer_role_for_handoff,
                audience_profile_input=str(audience_profile_input.value or ""),
                core_message_input=str(core_message_input.value or ""),
                tone_profile_key=_selected_tone_profile_key(),
            )
            explicit_speaker_profile = str(required_inputs.get("speaker_profile_input") or "")
            explicit_audience_profile = str(required_inputs.get("audience_profile_input") or "")
            explicit_core_message = str(required_inputs.get("core_message_input") or "")
            missing_required_fields = [
                str(field)
                for field in _to_plain_list(required_inputs.get("missing_required_fields"))
            ]
            if missing_required_fields:
                missing_required_view = _build_current_mainline_missing_required_inputs_view(
                    missing_fields=missing_required_fields,
                )
                missing_status_text = str(missing_required_view.get("status_text") or "")
                _run_generation_ui_mutation(
                    lambda: setattr(status_label, "text", missing_status_text),
                    "missing_required_status",
                )
                _notify_generation(
                    str(missing_required_view.get("notify_text") or ""),
                    str(missing_required_view.get("notify_color") or "warning"),
                )
                _record_current_mainline_generation_event(
                    telemetry_context=telemetry_context,
                    event=str(
                        missing_required_view.get("event_name")
                        or "generation_rejected_missing_required_inputs"
                    ),
                    phase=phase,
                    reason_code=str(missing_required_view.get("reason_code") or "INP_MISSING_REQUIRED"),
                    error_class=str(missing_required_view.get("error_class") or "user_input"),
                    status_text=missing_status_text,
                    extra=_to_plain_dict(missing_required_view.get("extra")),
                )
                return
            journey_prompt_text = prompt_raw
            journey_selections = _build_current_mainline_generation_selection_payload(
                base_selections=journey_selections,
                article_type_key=type_key,
                selected_article_type_label=selected_article_type,
                content_goal_key=content_goal_key,
                writing_focus_key=writing_focus_key,
                structure_key=structure_key,
                length_mode_key=length_mode_key,
                tone_profile_key=tone_profile_key,
                perspective_key=perspective_key,
                allow_experience=bool(allow_experience),
                strict_saas_mode=CURRENT_MAINLINE_STRICT_SAAS_MODE,
            )
            telemetry_context = _build_current_mainline_run_generation_telemetry_context(
                attempt_id=attempt_id,
                article_type=journey_article_type,
                user_prompt_text=journey_prompt_text,
                source_items=state.sources,
                selections=journey_selections,
                writing_focus_key=writing_focus_key,
                perspective_key=perspective_key,
                tone_profile_key=tone_profile_key,
                prompt_raw=prompt_raw,
                system_hint_items=system_hint_items,
                retry_memo=[],
                strict_saas_mode=CURRENT_MAINLINE_STRICT_SAAS_MODE,
                question_generation_owner=getattr(state, "question_generation_owner", ""),
            )
            _record_current_mainline_generation_event(
                telemetry_context=telemetry_context,
                event="generation_submitted",
                phase=phase,
                extra={
                    "used_article_type_fallback": used_type_fallback,
                    "interview_answered_count": answered_count,
                },
                include_question_generation_owner=True,
            )
            _accept_source_session_for_article_type(_get_or_create_state(client_key), article_type_key=type_key)
            _snapshot_current_source_session(_get_or_create_state(client_key), completed_run=True)
            logger.info(
                "Generation started id=%s source_count=%s article_type=%s goal=%s perspective=%s structure=%s writing_focus=%s length_mode=%s tone_profile=%s",
                attempt_id,
                len(state.sources),
                type_key,
                content_goal_key,
                perspective_key,
                structure_key,
                writing_focus_key,
                length_mode_key,
                tone_profile_key,
            )
            for index, source_item in enumerate(state.sources, start=1):
                logger.info(
                    "Generation source id=%s index=%s source_type=%s value=%s",
                    attempt_id,
                    index,
                    source_item.source_type,
                    source_item.value,
                )

            pre_delay_notice = _build_generation_delay_notice(len(state.sources))
            if pre_delay_notice:
                logger.info("Generation delay notice id=%s phase=pre_fetch detail=%s", attempt_id, pre_delay_notice)
                _notify_generation(f"引用データが多いため、処理に時間がかかる可能性があります。({pre_delay_notice})", "warning")

            prerun_plan = _build_current_mainline_generation_prerun_plan(
                pre_delay_notice=pre_delay_notice,
            )
            state.busy = bool(prerun_plan.get("busy", True))
            generation_started_at = time.monotonic()
            pipeline_instance = _get_or_create_current_mainline_pipeline(client_key)
            pipeline_instance.reset_generation_progress()
            output_fields = _to_plain_dict(prerun_plan.get("output_fields"))
            preview_plan = _to_plain_dict(prerun_plan.get("preview"))
            state.generated_images = _to_plain_list(prerun_plan.get("generated_images"))
            state.generated_image_variants = []
            state.image_generation_status = ""

            def _apply_prerun_ui() -> None:
                if bool(prerun_plan.get("refresh_step_indicators", False)):
                    _refresh_step_indicators()
                _refresh_output_stage_visibility()
                _refresh_journey_confirmation_cta()
                if bool(prerun_plan.get("disable_generate_button", True)):
                    generate_button.disable()
                generate_button.text = str(prerun_plan.get("generate_button_text") or "生成中...")
                spinner.visible = bool(prerun_plan.get("spinner_visible", True))
                generation_progress.visible = bool(prerun_plan.get("generation_progress_visible", True))
                generation_progress.value = float(prerun_plan.get("generation_progress_value", 0.0) or 0.0)
                generation_progress_note.visible = bool(prerun_plan.get("generation_progress_note_visible", True))
                status_label.text = str(prerun_plan.get("status_text") or "")
                source_error_area.content = str(prerun_plan.get("source_error_content") or "")
                title_area.value = str(output_fields.get("title") or "")
                lead_area.value = str(output_fields.get("lead") or "")
                body_area.value = str(output_fields.get("body") or "")
                references_area.value = str(output_fields.get("references") or "")
                hashtags_area.value = str(output_fields.get("hashtags") or "")
                full_text_area.value = str(output_fields.get("full_text") or "")
                note_body_text.value = str(output_fields.get("note_body_text") or "")
                linkedin_area.value = str(output_fields.get("linkedin_text") or "")
                linkedin_short_area.value = str(output_fields.get("linkedin_short_text") or "")
                preview.content = str(preview_plan.get("content") or _PREVIEW_PLACEHOLDER)
                if bool(preview_plan.get("placeholder_active", False)):
                    preview.classes(add="article-preview-placeholder")
                stats_label.text = str(prerun_plan.get("stats_text") or "")
                image_status.text = ""
                if bool(prerun_plan.get("refresh_generated_images", False)):
                    generated_images_container.refresh()
                if bool(prerun_plan.get("activate_generation_progress_timer", False)):
                    generation_progress_timer.activate()

            _run_generation_ui_mutation(_apply_prerun_ui, "generation_prerun_ui")
            _set_generation_phase_for_attempt("prepare", pre_delay_notice or "")
            outcome = "running"
            guard_retry_count = 0
            quality_warning_only = False

            try:
                phase = "fetch_sources"
                _set_generation_phase_for_attempt(phase)
                sources = [s.value for s in state.sources]
                contents = []
                failures = []
                fetch_summary = {
                    "success_count": 0,
                    "failure_count": 0,
                    "elapsed_ms": 0,
                    "event_extra": {
                        "success_count": 0,
                        "failure_count": 0,
                        "elapsed_ms": 0,
                        "total_source_chars": 0,
                    },
                    "post_delay_notice": "",
                    "failure_details": "",
                    "blocked_urls": [],
                }
                if sources:
                    fetch_started = time.monotonic()
                    contents, failures = await run.io_bound(fetcher.fetch_multiple_with_errors, sources, attempt_id)
                    fetch_summary = _prepare_current_mainline_fetch_summary(
                        contents=contents,
                        failures=failures,
                        elapsed_ms=int((time.monotonic() - fetch_started) * 1000),
                    )
                logger.info(
                    "Generation fetch summary id=%s success=%s failure=%s elapsed_ms=%s",
                    attempt_id,
                    int(fetch_summary.get("success_count") or 0),
                    int(fetch_summary.get("failure_count") or 0),
                    int(fetch_summary.get("elapsed_ms") or 0),
                )
                _record_current_mainline_generation_event(
                    telemetry_context=telemetry_context,
                    event="source_fetch_completed",
                    phase=phase,
                    extra=_to_plain_dict(fetch_summary.get("event_extra")),
                )
                post_delay_notice = str(fetch_summary.get("post_delay_notice") or "")
                if post_delay_notice:
                    logger.info(
                        "Generation delay notice id=%s phase=post_fetch detail=%s",
                        attempt_id,
                        post_delay_notice,
                    )
                    _run_generation_ui_mutation(
                        lambda: setattr(generation_progress_note, "text", "引用データ量が多いため、処理に時間がかかっています。"),
                        "post_fetch_delay_note",
                    )
                    if not pre_delay_notice:
                        _notify_generation(
                            f"引用データ量の影響で処理に時間がかかる可能性があります。({post_delay_notice})",
                            "warning",
                        )
                if failures:
                    for failure in failures[:10]:
                        logger.warning(
                            "Generation fetch failure id=%s source=%s reason=%s detail=%s",
                            attempt_id,
                            getattr(failure, "source", "unknown"),
                            getattr(failure, "reason", "unknown"),
                            getattr(failure, "detail", ""),
                        )
                    details = str(fetch_summary.get("failure_details") or "")
                    blocked = _to_plain_list(fetch_summary.get("blocked_urls"))
                    fetch_failure_view = _build_current_mainline_fetch_failure_view(
                        details=details,
                        blocked_urls=blocked,
                        failure_count=int(fetch_summary.get("failure_count") or 0),
                    )
                    state.blocked_403_urls = blocked
                    state.pdf_assist_since_ts = time.time()
                    state.pdf_assist_candidates = []
                    state.pdf_assist_status = str(fetch_failure_view.get("pdf_assist_status") or "")
                    fetch_failure_status_text = str(fetch_failure_view.get("status_text") or "")
                    fetch_failure_source_error_content = str(fetch_failure_view.get("source_error_content") or "")

                    def _apply_fetch_failure_ui() -> None:
                        pdf_assist_status_label.text = state.pdf_assist_status
                        pdf_assist_panel.refresh()
                        status_label.text = fetch_failure_status_text
                        if details:
                            source_error_area.content = details
                        source_error_area.content = fetch_failure_source_error_content

                    if details:
                        logger.warning("Generation blocked due to source fetch failures id=%s\n%s", attempt_id, details)
                    _run_generation_ui_mutation(_apply_fetch_failure_ui, "fetch_failure_ui")
                    outcome = str(fetch_failure_view.get("outcome") or "needs_input_fetch_failures")
                    _notify_generation(
                        str(fetch_failure_view.get("notify_text") or ""),
                        str(fetch_failure_view.get("notify_color") or "warning"),
                    )
                    _record_current_mainline_generation_event(
                        telemetry_context=telemetry_context,
                        event=str(fetch_failure_view.get("event_name") or "generation_blocked_fetch_failures"),
                        phase=phase,
                        reason_code=str(fetch_failure_view.get("reason_code") or "INP_SOURCE_FETCH_FAILED"),
                        error_class=str(fetch_failure_view.get("error_class") or "user_input"),
                        status_text=fetch_failure_status_text,
                        extra=_to_plain_dict(fetch_failure_view.get("event_extra")),
                    )
                    return
                if (
                    not contents
                    and source_mode_key != "web"
                    and not _source_mode_allows_no_sources(
                        article_type_key=type_key,
                        source_mode_key=source_mode_key,
                        prompt_raw=prompt_raw,
                        past_blog_unlocked=past_blog_unlocked,
                    )
                ):
                    no_sources_view = _build_current_mainline_no_valid_sources_view()
                    state.pdf_assist_status = str(no_sources_view.get("pdf_assist_status") or "")
                    no_sources_status_text = str(no_sources_view.get("status_text") or "")
                    no_sources_source_error_content = str(no_sources_view.get("source_error_content") or "")
                    _run_generation_ui_mutation(
                        lambda: (
                            setattr(pdf_assist_status_label, "text", state.pdf_assist_status),
                            pdf_assist_panel.refresh(),
                            setattr(status_label, "text", no_sources_status_text),
                            setattr(source_error_area, "content", no_sources_source_error_content),
                        ),
                        "no_valid_sources_ui",
                    )
                    logger.warning(
                        "Generation blocked id=%s reason=%s",
                        attempt_id,
                        str(no_sources_view.get("reason_code") or "INP_MISSING_REQUIRED"),
                    )
                    outcome = str(no_sources_view.get("outcome") or "needs_input_no_contents")
                    _notify_generation(
                        str(no_sources_view.get("notify_text") or ""),
                        str(no_sources_view.get("notify_color") or "warning"),
                    )
                    _record_current_mainline_generation_event(
                        telemetry_context=telemetry_context,
                        event=str(no_sources_view.get("event_name") or "generation_blocked_no_valid_sources"),
                        phase=phase,
                        reason_code=str(no_sources_view.get("reason_code") or "INP_MISSING_REQUIRED"),
                        error_class=str(no_sources_view.get("error_class") or "user_input"),
                        status_text=no_sources_status_text,
                        extra=_to_plain_dict(no_sources_view.get("event_extra")),
                    )
                    return
                _run_generation_ui_mutation(
                    lambda: _notify_source_notices(contents),
                    "source_notices",
                )
                phase = "generate_article"
                _set_generation_phase_for_attempt(phase)

                generation_request_inputs = _prepare_current_mainline_generation_request_inputs(
                    interview_answers=prepared_interview_answers,
                    speaker_profile_input=explicit_speaker_profile,
                    prompt_raw=prompt_raw,
                )
                answers_dict = _to_plain_dict(generation_request_inputs.get("interview_answers"))
                selected_writer_role = str(generation_request_inputs.get("speaker_profile_input") or "")
                if bool(generation_request_inputs.get("writer_role_ignored_theme_like")):
                    logger.warning(
                        "Generation writer_role ignored id=%s reason=theme_like_input value=%s",
                        attempt_id,
                        explicit_speaker_profile,
                    )
                    _notify_generation("話者設定がテーマ文に見えるため、今回は自動判定で生成します。", "warning")
                logger.info(
                    "Generation interview answers prepared id=%s answered=%s keys=%s",
                    attempt_id,
                    int(generation_request_inputs.get("interview_answer_count") or 0),
                    ",".join(_to_plain_list(generation_request_inputs.get("interview_answer_keys"))) or "-",
                )

                logger.info(
                    "Generation experience setting prepared id=%s allow_experience=%s",
                    attempt_id,
                    allow_experience,
                )
                logger.info(
                    "Generation tone profile prepared id=%s tone_profile=%s",
                    attempt_id,
                    tone_profile_key,
                )
                normalized_prompt_raw = str(generation_request_inputs.get("prompt_raw") or "")
                published_post_candidates = _load_current_published_post_candidates()
                omakase_surface = _build_omakase_surface_state(
                    article_type_key=type_key,
                    prompt_raw=normalized_prompt_raw,
                    source_mode_key=source_mode_key,
                    source_values=[str(item.value or "").strip() for item in state.sources],
                    source_documents=contents,
                    published_post_candidates=published_post_candidates,
                )
                omakase_preflight = _to_plain_dict(omakase_surface.get("preflight"))
                effective_prompt_raw = normalized_prompt_raw
                retry_memo: List[str] = [
                    str(item)
                    for item in _to_plain_list(generation_request_inputs.get("retry_memo"))
                ]
                telemetry_context = _build_current_mainline_run_generation_telemetry_context(
                    attempt_id=attempt_id,
                    article_type=journey_article_type,
                    user_prompt_text=journey_prompt_text,
                    source_items=state.sources,
                    selections=journey_selections,
                    writing_focus_key=writing_focus_key,
                    perspective_key=perspective_key,
                    tone_profile_key=tone_profile_key,
                    prompt_raw=effective_prompt_raw,
                    system_hint_items=system_hint_items,
                    retry_memo=retry_memo,
                    strict_saas_mode=CURRENT_MAINLINE_STRICT_SAAS_MODE,
                    question_generation_owner=getattr(state, "question_generation_owner", ""),
                )
                try:
                    input_contract_kwargs = _build_current_mainline_input_contract_kwargs(
                        source_items=state.sources,
                        source_documents=contents,
                        article_type=type_key,
                        selection=selection,
                        user_prompt_text=effective_prompt_raw,
                        content_goal_key=content_goal_key,
                        writing_focus_key=writing_focus_key,
                        structure_key=structure_key,
                        length_mode_key=length_mode_key,
                        tone_profile_key=tone_profile_key,
                        perspective_key=perspective_key,
                        allow_experience=bool(allow_experience),
                        interview_answers=answers_dict,
                        speaker_profile_input=selected_writer_role,
                        audience_profile_input=explicit_audience_profile,
                        core_message_input=explicit_core_message,
                        self_reference_policy_key=self_reference_policy_key,
                        branding_subtype_key=_selected_branding_subtype_key(),
                        branding_focus_key=_selected_branding_focus_key(),
                        pattern_key=_selected_pattern_key(),
                        system_hint_items=system_hint_items,
                        retry_memo=retry_memo,
                        strict_saas_mode=CURRENT_MAINLINE_STRICT_SAAS_MODE,
                        source_mode_key=source_mode_key,
                        industry_hint_input="",
                        followup_context={},
                        omakase_preflight_status=str(omakase_preflight.get("status") or ""),
                        omakase_charge_ready=omakase_preflight.get("charge_ready"),
                        omakase_reason_code=str(omakase_preflight.get("reason_code") or ""),
                        omakase_message=str(omakase_preflight.get("message") or ""),
                        omakase_fallback_options=_to_plain_list(omakase_preflight.get("fallback_options")),
                        omakase_needs_input_items=_to_plain_list(omakase_preflight.get("needs_input_items")),
                        omakase_source_count=int(omakase_preflight.get("source_count") or 0),
                        omakase_existing_post_count=int(omakase_preflight.get("existing_post_count") or 0),
                        omakase_usable_posts_count=int(omakase_preflight.get("usable_posts_count") or 0),
                        omakase_dominant_cluster_count=int(omakase_preflight.get("dominant_cluster_count") or 0),
                        omakase_available=bool(omakase_preflight.get("omakase_available")),
                    )
                    if source_mode_key == "web":
                        input_contract_kwargs = merge_omakase_seed_into_current_mainline_kwargs(
                            input_contract_kwargs,
                            omakase_preflight,
                        )
                    input_contract = build_current_mainline_input_contract(
                        **input_contract_kwargs
                    )
                    validate_current_mainline_generation_gate(input_contract)
                except InputContractValidationError as exc:
                    reason_code = str(getattr(exc, "reason_code", "") or "validation_error")
                    logger.warning(
                        "Generation rejected id=%s reason=%s field=%s message=%s",
                        attempt_id,
                        reason_code,
                        str(getattr(exc, "field", "") or "-"),
                        str(exc),
                    )
                    outcome = "needs_input_contract_validation"
                    input_contract_status_text = "入力条件が不足または不正のため、生成を停止しました。"
                    if reason_code.startswith("OMK_"):
                        input_contract_source_error_content = (
                            f"- お任せ判定: {str(omakase_surface.get('title') or '要確認')}\n"
                            f"- 詳細: {str(omakase_surface.get('message') or '')}\n"
                            f"- inventory: {str(omakase_surface.get('inventory_text') or '')}\n"
                            f"- 次の一手: {str(omakase_surface.get('detail_text') or '開始方式か1行テーマを見直してください。')}"
                        )
                    else:
                        input_contract_source_error_content = (
                            "- 入力条件を確認してください。\n"
                            f"- reason_code: {reason_code}\n"
                            "- 対処: 記事タイプ/媒体/ソース/指示内容を見直して再実行してください。"
                        )
                    _run_generation_ui_mutation(
                        lambda: (
                            setattr(status_label, "text", input_contract_status_text),
                            setattr(source_error_area, "content", input_contract_source_error_content),
                        ),
                        "input_contract_validation_ui",
                    )
                    _notify_generation("入力契約の検証で停止しました。", "warning")
                    _record_current_mainline_generation_event(
                        telemetry_context=telemetry_context,
                        event="generation_rejected_input_contract",
                        phase=phase,
                        reason_code=reason_code,
                        error_class="user_input",
                        status_text=input_contract_status_text,
                        extra={"field": str(getattr(exc, "field", "") or "")},
                    )
                    return
                _record_current_mainline_generation_event(
                    telemetry_context=telemetry_context,
                    event="input_contract_ready",
                    phase=phase,
                    extra={
                        "primary_topic_source": str(input_contract.get("primary_topic_source", "") or ""),
                        "must_cover_count": len(_to_plain_list(input_contract.get("must_cover"))),
                        "source_documents": len(_to_plain_list(input_contract.get("source_documents"))),
                        "semantic_article_key": str(input_contract.get("semantic_article_key", "") or ""),
                        "source_fit_status": str(_to_plain_dict(input_contract.get("source_fit")).get("status") or ""),
                    },
                    include_question_generation_owner=True,
                )

                selected_body_route_id = resolve_ui_body_route_selection(os.getenv(UI_ROUTE_SELECTION_ENV, ""))
                if selected_body_route_id == ROUTE_0506_ID:
                    phase = "route_0506_ui_1case"
                    _set_generation_phase_for_attempt(phase)
                    _log_ui_usage(
                        "generation",
                        "pipeline_invoked",
                        phase="route_0506_ui_1case",
                        article_type=type_key,
                        media="note",
                    )
                    route_0506_result = await run.io_bound(
                        lambda: run_route_0506_ui_onecase(
                            input_contract,
                            enforce_onecase_lock=False,
                        )
                    )
                    route_0506_summary = _to_plain_dict(route_0506_result.get("validation_summary"))
                    state.result = _to_plain_dict(route_0506_result)
                    route_0506_body = str(
                        route_0506_result.get("body")
                        or route_0506_result.get("full_text")
                        or ""
                    )
                    route_0506_artifact_root = str(route_0506_summary.get("artifact_root") or "")
                    if bool(route_0506_result.get("blocked")):
                        blocked_view = _to_plain_dict(
                            route_0506_result.get("user_message_view")
                            or build_route_0506_user_facing_blocked_view(
                                route_0506_result,
                                security_gate=_to_plain_dict(route_0506_result.get("security_gate")),
                                artifact_root=route_0506_artifact_root,
                            )
                        )
                        blocked_status_text = str(blocked_view.get("status_text") or "Route 0506 は安全に停止しました。")
                        blocked_source_error_content = str(blocked_view.get("source_error_content") or "")
                        blocked_progress_note = str(blocked_view.get("generation_progress_note_text") or "")
                        blocked_reason_code = str(blocked_view.get("reason_code") or route_0506_result.get("reason_code") or "ROUTE_0506_UI_BLOCKED")
                        outcome = str(blocked_view.get("outcome") or "blocked_route_0506_ui_1case")
                        _run_generation_ui_mutation(
                            lambda: (
                                setattr(status_label, "text", blocked_status_text),
                                setattr(source_error_area, "content", blocked_source_error_content),
                                setattr(generation_progress_note, "text", blocked_progress_note),
                                setattr(generation_progress_note, "visible", bool(blocked_progress_note)),
                            ),
                            "route_0506_blocked_ui",
                        )
                        _notify_generation(
                            str(blocked_view.get("notify_text") or blocked_status_text),
                            str(blocked_view.get("notify_color") or "warning"),
                        )
                        _record_current_mainline_generation_event(
                            telemetry_context=telemetry_context,
                            event="route_0506_ui_1case_blocked",
                            phase=phase,
                            result=route_0506_result,
                            reason_code=blocked_reason_code,
                            error_class=str(blocked_view.get("error_class") or "route_0506"),
                            status_text=blocked_status_text,
                            extra={
                                "artifact_root": route_0506_artifact_root,
                                "blocked_cause_key": str(blocked_view.get("cause_key") or ""),
                                "route_a_fallback_used": False,
                            },
                        )
                        return

                    route_0506_post_success_result = _prepare_route_0506_post_success_result(
                        route_0506_result=route_0506_result,
                        input_contract=input_contract,
                    )
                    state.result = route_0506_post_success_result
                    route_0506_body = str(route_0506_post_success_result.get("body") or route_0506_body)

                    def _apply_route_0506_ui_result() -> None:
                        title_area.value = str(route_0506_post_success_result.get("title") or "")
                        lead_area.value = str(route_0506_post_success_result.get("lead") or "")
                        body_area.value = route_0506_body
                        references_area.value = ""
                        hashtags_area.value = ""
                        full_text_area.value = route_0506_body
                        note_body_text.value = route_0506_body
                        preview.content = sanitize_markdown_preview(route_0506_body)
                        preview.classes(remove="article-preview-placeholder")
                        linkedin_area.value = ""
                        linkedin_short_area.value = ""
                        stats_label.text = f"Route 0506 本文: {len(route_0506_body)}文字"
                        generation_progress.value = 1.0
                        status_label.text = "Route 0506 UI 1case の本文生成が完了しました。"
                        generation_progress_note.text = f"Route 0506 の本文生成が完了しました。 artifact: {route_0506_artifact_root}"
                        generation_progress_note.visible = True

                    _run_generation_ui_mutation(_apply_route_0506_ui_result, "route_0506_render_ui")
                    phase = await _run_post_success_downstream_phases(
                        result=route_0506_post_success_result,
                        render_note_body_text=route_0506_body,
                        article_type_for_image=str(
                            route_0506_post_success_result.get("article_type") or journey_article_type
                        ),
                    )
                    phase = "complete"
                    _set_generation_phase_for_attempt(phase)
                    outcome = "success_route_0506_ui_1case"
                    _record_current_mainline_generation_event(
                        telemetry_context=telemetry_context,
                        event="route_0506_ui_1case_completed",
                        phase=phase,
                        result=route_0506_post_success_result,
                        status_text="Route 0506 UI 1case completed.",
                        extra={
                            "artifact_root": route_0506_artifact_root,
                            "body_char_count": len(route_0506_body),
                            "route_a_fallback_used": False,
                            "api_send": bool(route_0506_summary.get("api_send")),
                            "post_success_downstream_evaluated": True,
                            "image_generation_status": str(getattr(state, "image_generation_status", "") or ""),
                        },
                    )
                    route_0506_credit_debited = await _consume_usage_credit_after_success(
                        service_key="kotomake",
                        action_key="generate",
                        attempt_id=attempt_id,
                    )
                    _run_generation_ui_mutation(_scroll_to_generation_result, "scroll_route_0506_result")
                    if not route_0506_credit_debited:
                        _notify_generation("生成は完了しましたが、クレジット消費を確認できませんでした。管理者へ連絡してください。", "warning")
                        return
                    _notify_generation("Route 0506 UI 1case の本文生成が完了しました。", "positive")
                    return

                result: Dict[str, Any] = {}
                phase = "generate_article_newpipeline"
                _set_generation_phase_for_attempt(phase)
                _log_ui_usage(
                    "generation",
                    "pipeline_invoked",
                    phase="newalgorithm_mainline",
                    article_type=type_key,
                    media="note",
                )
                result = await _execute_current_mainline_generation_with_context(
                    io_bound_runner=run.io_bound,
                    pipeline_instance=pipeline_instance,
                    input_contract=input_contract,
                    prompt_raw=normalized_prompt_raw,
                    system_hint_items=system_hint_items,
                    retry_memo=retry_memo,
                    strict_saas_mode=CURRENT_MAINLINE_STRICT_SAAS_MODE,
                    question_generation_owner=getattr(state, "question_generation_owner", ""),
                )
                existing_output_guard = output_guard_mod.extract_existing_output_guard(result)
                if not bool(result.get("success", False)) and not bool(existing_output_guard.get("blocked")):
                    reason_code = str(result.get("reason_code") or "SYS_PIPELINE_FAILURE")
                    error_class = _classify_reason_code(reason_code)
                    needs_input_items = _to_plain_list(result.get("needs_input_items", []))
                    pipeline_error = _to_plain_dict(_to_plain_dict(result.get("pipeline_check")).get("error"))
                    error_message = str(pipeline_error.get("message") or reason_code)
                    error_result = dict(result)
                    if needs_input_items:
                        error_result["needs_input_items"] = needs_input_items
                    generation_error_view = _build_current_mainline_generation_error_view(
                        reason_code=reason_code,
                        error_class=error_class,
                        error_message=error_message,
                        needs_input_items=[_to_plain_dict(item) for item in needs_input_items],
                    )
                    outcome = str(generation_error_view.get("outcome") or f"fail_closed_{error_class}")
                    generation_error_status_text = str(generation_error_view.get("status_text") or "")
                    generation_error_source_error_content = str(generation_error_view.get("source_error_content") or "")
                    _run_generation_ui_mutation(
                        lambda: (
                            setattr(status_label, "text", generation_error_status_text),
                            setattr(source_error_area, "content", generation_error_source_error_content),
                        ),
                        "generation_error_ui",
                    )
                    _notify_generation(
                        str(generation_error_view.get("notify_text") or ""),
                        str(generation_error_view.get("notify_color") or "negative"),
                    )
                    _record_current_mainline_generation_event(
                        telemetry_context=telemetry_context,
                        event="generation_returned_error",
                        phase=phase,
                        result=error_result,
                        reason_code=reason_code,
                        error_class=error_class,
                        status_text=generation_error_status_text,
                        needs_input_items=needs_input_items,
                        extra={"pipeline_source": "newalgorithm_mainline"},
                    )
                    _persist_current_mainline_generation_snapshot_fail_open(
                        telemetry_context=telemetry_context,
                        result=error_result,
                        source_count=len(contents),
                        blocked=True,
                        failure_kind="failed_generation",
                    )
                    logger.warning(
                        "Generation aborted id=%s error_class=%s reason_code=%s pipeline_source=%s",
                        attempt_id,
                        error_class,
                        reason_code,
                        "newalgorithm_mainline",
                    )
                    return
                logger.info(
                    "Generation core completed id=%s title_chars=%s lead_chars=%s body_chars=%s references_chars=%s",
                    attempt_id,
                    len(result.get("title", "")),
                    len(result.get("lead", "")),
                    len(result.get("body", "")),
                    len(result.get("references", "")),
                )
                _record_current_mainline_generation_event(
                    telemetry_context=telemetry_context,
                    event="generation_core_completed",
                    phase=phase,
                    result=result,
                )
                _set_generation_phase_for_attempt("quality_output_guard")
                pipeline_check = _to_plain_dict(result.get("pipeline_check"))
                output_guard = _evaluate_generation_output_guard(result)
                result = _attach_output_guard_to_result(result, output_guard)
                if (
                    output_guard.get("blocked")
                    and _is_guard_auto_repair_candidate(output_guard)
                    and allows_guard_auto_repair(CURRENT_MAINLINE_STRICT_SAAS_MODE)
                    and guard_retry_count < _OUTPUT_GUARD_AUTO_REPAIR_MAX
                ):
                    guard_retry = _prepare_current_mainline_guard_retry(
                        output_guard=_to_plain_dict(output_guard),
                        guard_retry_count=guard_retry_count,
                    )
                    guard_retry_count = int(guard_retry.get("guard_retry_count") or guard_retry_count + 1)
                    retry_memo = [
                        str(item)
                        for item in _to_plain_list(guard_retry.get("retry_memo"))
                    ]
                    phase = str(guard_retry.get("phase") or "auto_retry_guard_repair")
                    _set_generation_phase_for_attempt(
                        phase,
                        str(guard_retry.get("phase_detail") or ""),
                    )
                    telemetry_context = _build_current_mainline_run_generation_telemetry_context(
                        attempt_id=attempt_id,
                        article_type=journey_article_type,
                        user_prompt_text=journey_prompt_text,
                        source_items=state.sources,
                        selections=journey_selections,
                        writing_focus_key=writing_focus_key,
                        perspective_key=perspective_key,
                        tone_profile_key=tone_profile_key,
                        prompt_raw=normalized_prompt_raw,
                        system_hint_items=system_hint_items,
                        retry_memo=retry_memo,
                        strict_saas_mode=CURRENT_MAINLINE_STRICT_SAAS_MODE,
                        question_generation_owner=getattr(state, "question_generation_owner", ""),
                    )
                    guard_retry_status_text = str(
                        guard_retry.get("status_text") or "品質ガード検知のため自動補修リトライ中..."
                    )
                    _run_generation_ui_mutation(
                        lambda: setattr(status_label, "text", guard_retry_status_text),
                        "guard_retry_status",
                    )
                    logger.warning(
                        "Generation auto repair retry id=%s retry=%s reason_code=%s",
                        attempt_id,
                        guard_retry_count,
                        str(guard_retry.get("reason_code") or "-"),
                    )
                    try:
                        retry_input_contract = dict(input_contract)
                        retry_input_contract["retry_memo"] = retry_memo
                        result = await _execute_current_mainline_generation_with_context(
                            io_bound_runner=run.io_bound,
                            pipeline_instance=pipeline_instance,
                            input_contract=retry_input_contract,
                            prompt_raw=normalized_prompt_raw,
                            system_hint_items=system_hint_items,
                            retry_memo=retry_memo,
                            strict_saas_mode=CURRENT_MAINLINE_STRICT_SAAS_MODE,
                            question_generation_owner=getattr(state, "question_generation_owner", ""),
                        )
                        output_guard = _evaluate_generation_output_guard(result)
                        result = _attach_output_guard_to_result(result, output_guard)
                    except Exception as exc:
                        classification = _classify_generation_exception(exc)
                        reason_code = str(classification.get("reason_code") or "SYS_GENERATION_FAILURE")
                        error_class = str(classification.get("error_class") or "system")
                        guard_retry_exception_view = _build_current_mainline_guard_retry_exception_view(
                            reason_code=reason_code,
                            error_class=error_class,
                        )
                        guard_retry_exception_source_error_content = str(
                            guard_retry_exception_view.get("source_error_content") or ""
                        )
                        guard_retry_exception_status_text = str(guard_retry_exception_view.get("status_text") or "")
                        _run_generation_ui_mutation(
                            lambda: (
                                setattr(source_error_area, "content", guard_retry_exception_source_error_content),
                                setattr(status_label, "text", guard_retry_exception_status_text),
                            ),
                            "guard_retry_exception_ui",
                        )
                        _notify_generation(
                            str(guard_retry_exception_view.get("notify_text") or ""),
                            str(guard_retry_exception_view.get("notify_color") or "negative"),
                        )
                        outcome = str(
                            guard_retry_exception_view.get("outcome") or "fail_closed_guard_retry_exception"
                        )
                        result = _build_current_mainline_guard_retry_failure_result(
                            input_contract=input_contract,
                            reason_code=reason_code,
                            error_class=error_class,
                            prompt_raw=normalized_prompt_raw,
                            system_hint_items=system_hint_items,
                            retry_memo=retry_memo,
                            strict_saas_mode=CURRENT_MAINLINE_STRICT_SAAS_MODE,
                            question_generation_owner=getattr(state, "question_generation_owner", ""),
                        )
                        _persist_current_mainline_generation_snapshot_fail_open(
                            telemetry_context=telemetry_context,
                            result=result,
                            source_count=len(contents),
                            blocked=True,
                            failure_kind="guard_retry_failure",
                        )
                        return
                result, output_guard = _apply_current_mainline_fingerprint_only_warning_policy(
                    result,
                    output_guard,
                )
                if output_guard.get("blocked"):
                    phase = "quality_output_guard"
                    blocked_output = _prepare_current_mainline_output_guard_block(
                        result=result,
                        output_guard=_to_plain_dict(output_guard),
                        guard_retry_count=guard_retry_count,
                    )
                    error_class = str(blocked_output.get("error_class") or "system")
                    reason_code = str(
                        blocked_output.get("reason_code") or "SYS_QUALITY_GATE_HARD_FAIL"
                    )
                    needs_input_items = _to_plain_list(blocked_output.get("needs_input_items"))
                    logger.warning(
                        "Generation blocked by output guard id=%s error_class=%s reason_code=%s reasons=%s manual_hits=%s",
                        attempt_id,
                        error_class,
                        reason_code,
                        str(blocked_output.get("guard_reason_log_text") or "-"),
                        int(blocked_output.get("manual_hit_count") or 0),
                    )
                    result = _to_plain_dict(blocked_output.get("result")) or dict(result)
                    blocked_source_error_content = str(blocked_output.get("source_error_content") or "")
                    blocked_status_text = str(blocked_output.get("status_text") or "")
                    _run_generation_ui_mutation(
                        lambda: (
                            setattr(source_error_area, "content", blocked_source_error_content),
                            setattr(status_label, "text", blocked_status_text),
                        ),
                        "output_guard_block_ui",
                    )
                    outcome = str(blocked_output.get("outcome") or "blocked_quality_guard")
                    if outcome == "review_required_draft":
                        render_fields = _to_plain_dict(blocked_output.get("render_fields"))
                        state.result = result
                        review_note_body_text = str(render_fields.get("note_body_text") or "")
                        review_linkedin_text = str(render_fields.get("linkedin_text") or "")

                        def _apply_review_required_ui() -> None:
                            title_area.value = str(render_fields.get("title") or "")
                            lead_area.value = str(render_fields.get("lead") or "")
                            body_area.value = str(render_fields.get("body") or "")
                            references_area.value = str(render_fields.get("references") or "")
                            hashtags_area.value = str(render_fields.get("hashtags_plain") or "")
                            full_text_area.value = str(render_fields.get("full_text") or "")
                            note_body_text.value = review_note_body_text
                            linkedin_area.value = review_linkedin_text
                            linkedin_short_area.value = str(render_fields.get("linkedin_short_text") or "")
                            preview.content = sanitize_markdown_preview(str(render_fields.get("preview_text") or ""))
                            preview.classes(remove="article-preview-placeholder")
                            stats_label.text = f"記事本文: {len(review_note_body_text)}文字 / LinkedIn: {len(review_linkedin_text)}文字"
                            generation_progress_note.text = "コピーや保存はできますが、公開前の確認が必要です。"
                            generation_progress_note.visible = True

                        _run_generation_ui_mutation(_apply_review_required_ui, "review_required_draft_ui")
                        _notify_generation(
                            str(blocked_output.get("notify_text") or _REVIEW_DRAFT_NOTIFY_TEXT),
                            str(blocked_output.get("notify_color") or "warning"),
                        )
                        _record_current_mainline_generation_event(
                            telemetry_context=telemetry_context,
                            event="generation_review_required_draft",
                            phase=phase,
                            result=result,
                            reason_code=reason_code,
                            error_class=error_class,
                            status_text=blocked_status_text,
                            needs_input_items=needs_input_items,
                            extra={
                                **_to_plain_dict(blocked_output.get("event_extra")),
                            },
                            include_question_generation_owner=True,
                        )
                        _persist_current_mainline_generation_snapshot_fail_open(
                            telemetry_context=telemetry_context,
                            result=result,
                            source_count=len(contents),
                            blocked=False,
                            failure_kind="review_required_draft",
                        )
                        return
                    _notify_generation(
                        str(
                            blocked_output.get("notify_text")
                            or "生成結果に重大な不整合があったため表示を停止しました。"
                        ),
                        str(blocked_output.get("notify_color") or "negative"),
                    )
                    _record_current_mainline_generation_event(
                        telemetry_context=telemetry_context,
                        event="generation_blocked_output_guard",
                        phase=phase,
                        result=result,
                        reason_code=reason_code,
                        error_class=error_class,
                        status_text=blocked_status_text,
                        needs_input_items=needs_input_items,
                        extra={
                            **_to_plain_dict(blocked_output.get("event_extra")),
                        },
                        include_question_generation_owner=True,
                    )
                    _persist_current_mainline_generation_snapshot_fail_open(
                        telemetry_context=telemetry_context,
                        result=result,
                        source_count=len(contents),
                        blocked=True,
                        failure_kind="blocked_generation",
                    )
                    return

                soft_warnings = output_guard.get("soft_warnings", [])
                if isinstance(soft_warnings, list) and soft_warnings:
                    quality_warning_only = True
                    result["ui_quality_warnings"] = list(soft_warnings)
                    result["output_guard_warnings"] = list(soft_warnings)
                    _run_generation_ui_mutation(
                        lambda: (
                            setattr(generation_progress_note, "text", "記事完成へのアドバイスがあります。"),
                            setattr(generation_progress_note, "visible", True),
                        ),
                        "soft_warning_note_ui",
                    )

                phase = "render_output"
                _set_generation_phase_for_attempt(phase)
                success_view = _build_current_mainline_success_view(
                    result,
                    quality_warning_only=quality_warning_only,
                    guard_retry_count=guard_retry_count,
                )
                result = _to_plain_dict(success_view.get("result")) or dict(result)
                render_fields = _to_plain_dict(success_view.get("render_fields"))
                completion_view = _to_plain_dict(success_view.get("completion_view"))
                render_payload = _prepare_current_mainline_render_payload(
                    success_view=success_view,
                    render_fields=render_fields,
                )
                state.result = result
                hashtags_plain = str(render_payload.get("hashtags_plain") or "")
                render_note_body_text = str(render_payload.get("note_body_text") or "")
                render_linkedin_text = str(render_payload.get("linkedin_text") or "")
                render_linkedin_short_text = str(render_payload.get("linkedin_short_text") or "")
                preview_text = str(render_payload.get("preview_text") or "")

                def _apply_render_output_ui() -> None:
                    title_area.value = str(render_payload.get("title") or "")
                    lead_area.value = str(render_payload.get("lead") or "")
                    body_area.value = str(render_payload.get("body") or "")
                    references_area.value = str(render_payload.get("references") or "")
                    hashtags_area.value = hashtags_plain
                    full_text_area.value = str(render_payload.get("full_text") or "")
                    note_body_text.value = render_note_body_text
                    preview.content = sanitize_markdown_preview(preview_text)
                    preview.classes(remove="article-preview-placeholder")
                    linkedin_area.value = render_linkedin_text
                    linkedin_short_area.value = render_linkedin_short_text

                _run_generation_ui_mutation(_apply_render_output_ui, "render_output_ui")
                _record_current_mainline_generation_event(
                    telemetry_context=telemetry_context,
                    event="generation_rendered_output",
                    phase=phase,
                    result=result,
                    status_text=str(render_payload.get("render_status_text") or "生成結果をUIに反映しました。"),
                    extra=_to_plain_dict(render_payload.get("render_event_extra")),
                )
                _persist_current_mainline_generation_snapshot_fail_open(
                    telemetry_context=telemetry_context,
                    result=result,
                    source_count=len(contents),
                    failure_kind="latest_generation",
                )

                phase = await _run_post_success_downstream_phases(
                    result=result,
                    render_note_body_text=render_note_body_text,
                    article_type_for_image=journey_article_type,
                )

                phase = "complete"
                _set_generation_phase_for_attempt(phase)
                completion_payload = _prepare_current_mainline_completion_payload(
                    success_view=success_view,
                    completion_view=completion_view,
                    note_body_text=render_note_body_text,
                    linkedin_text=render_linkedin_text,
                    quality_warning_only=quality_warning_only,
                    elapsed_ms=int((time.monotonic() - started_at) * 1000),
                )
                note_body_char_count = int(completion_payload.get("note_body_chars") or 0)
                linkedin_char_count = int(completion_payload.get("linkedin_chars") or 0)
                complete_plan = _build_current_mainline_generation_complete_plan()
                _run_generation_ui_mutation(
                    lambda: (
                        _apply_current_mainline_completion_payload(
                            completion_payload=completion_payload,
                            stats_label=stats_label,
                            quality_summary_card=quality_summary_card,
                            quality_summary_badge=quality_summary_badge,
                            quality_summary_title=quality_summary_title,
                            quality_summary_note=quality_summary_note,
                            quality_summary_row_widgets=quality_summary_row_widgets,
                            review_kousei_label=review_kousei_label,
                            review_row_kousei=review_row_kousei,
                            review_buntai_label=review_buntai_label,
                            review_row_buntai=review_row_buntai,
                            review_konkyo_label=review_konkyo_label,
                            review_row_konkyo=review_row_konkyo,
                            review_container=review_container,
                            status_label=status_label,
                        ),
                        _apply_current_mainline_complete_plan(
                            complete_plan=complete_plan,
                            generation_progress=generation_progress,
                            reset_pdf_assist=_reset_pdf_assist,
                            pdf_assist_status_label=pdf_assist_status_label,
                            pdf_assist_panel=pdf_assist_panel,
                        ),
                    ),
                    "completion_ui",
                )
                terminal_payload = _prepare_current_mainline_completion_terminal_payload(
                    completion_payload=completion_payload,
                    status_label_text=str(completion_payload.get("status_text") or getattr(status_label, "text", "")),
                    note_body_char_count=note_body_char_count,
                    linkedin_char_count=linkedin_char_count,
                    quality_warning_only=quality_warning_only,
                )
                outcome = str(terminal_payload.get("outcome") or "success")
                logger.info(
                    "Generation completed id=%s note_body_chars=%s linkedin_chars=%s quality_warning_only=%s elapsed_ms=%s",
                    attempt_id,
                    int(terminal_payload.get("log_note_body_chars") or 0),
                    int(terminal_payload.get("log_linkedin_chars") or 0),
                    bool(terminal_payload.get("log_quality_warning_only")),
                    int(terminal_payload.get("log_elapsed_ms") or 0),
                )
                _record_current_mainline_generation_event(
                    telemetry_context=telemetry_context,
                    event="generation_completed",
                    phase=phase,
                    result=result,
                    status_text=str(terminal_payload.get("event_status_text") or ""),
                    extra=_to_plain_dict(terminal_payload.get("event_extra")),
                    include_question_generation_owner=True,
                )
                credit_debited = await _consume_usage_credit_after_success(
                    service_key="kotomake",
                    action_key="generate",
                    attempt_id=attempt_id,
                )
                _run_generation_ui_mutation(_scroll_to_generation_result, "scroll_generation_result")
                if not credit_debited:
                    _notify_generation("生成は完了しましたが、クレジット消費を確認できませんでした。管理者へ連絡してください。", "warning")
                    return
                _notify_generation(
                    str(terminal_payload.get("notify_text") or "生成が完了しました"),
                    str(terminal_payload.get("notify_color") or "positive"),
                )
            except Exception as exc:
                outcome = "error_exception"
                logger.exception("Article generation failed id=%s phase=%s", attempt_id, phase)
                exception_plan = _build_current_mainline_generation_exception_plan(phase=phase)
                exception_terminal_payload = _prepare_current_mainline_exception_terminal_payload(
                    exception_plan=exception_plan,
                    exc=exc,
                    outcome=outcome,
                )
                outcome = str(exception_terminal_payload.get("outcome") or "error_exception")
                exception_status_text = str(exception_terminal_payload.get("event_status_text") or "")
                _run_generation_ui_mutation(
                    lambda: _apply_current_mainline_exception_terminal_payload(
                        exception_terminal_payload=exception_terminal_payload,
                        status_label=status_label,
                        generation_progress_note=generation_progress_note,
                    ),
                    "generation_exception_ui",
                )
                _notify_generation(
                    str(exception_terminal_payload.get("notify_text") or ""),
                    str(exception_terminal_payload.get("notify_color") or "negative"),
                )
                _record_current_mainline_generation_event(
                    telemetry_context=telemetry_context,
                    event="generation_exception",
                    phase=phase,
                    reason_code="SYS_UI_GENERATION_EXCEPTION",
                    error_class="system",
                    status_text=exception_status_text,
                    extra=_to_plain_dict(exception_terminal_payload.get("event_extra")),
                )
            finally:
                generation_progress_timer.deactivate()
                image_elapsed_timer.deactivate()
                state_obj_for_cleanup = _CLIENT_STATES.get(_normalize_client_key(client_key))
                if state_obj_for_cleanup is not None:
                    state_obj_for_cleanup.busy = False
                cleanup_payload = _prepare_current_mainline_cleanup_payload(
                    cleanup_plan=_build_current_mainline_generation_cleanup_plan(),
                    outcome=outcome,
                    phase=phase,
                    elapsed_ms=int((time.monotonic() - started_at) * 1000),
                )
                _run_generation_ui_mutation(
                    lambda: (
                        _apply_current_mainline_cleanup_payload(
                            cleanup_payload=cleanup_payload,
                            generation_progress_timer=generation_progress_timer,
                            spinner=spinner,
                            generation_progress=generation_progress,
                            state_obj=state_obj_for_cleanup or state,
                            refresh_step_indicators=_refresh_step_indicators,
                            generate_button=generate_button,
                        ),
                        _refresh_journey_confirmation_cta(),
                    ),
                    "generation_cleanup_ui",
                )
                _finish_client_generation(client_key, generation_token)
                generation_started_at = None
                finish_log = _to_plain_dict(cleanup_payload.get("finish_log"))
                logger.info(
                    "Generation finished id=%s outcome=%s phase=%s elapsed_ms=%s",
                    attempt_id,
                    str(finish_log.get("outcome") or outcome),
                    str(finish_log.get("phase") or phase),
                    int(finish_log.get("elapsed_ms") or 0),
                )

        generate_button.on("click", run_generation)

        # ===== 生成後リーガルチェック（自動実行 + 任意再実行） =====
        with ui.expansion("生成後リーガルチェック", icon="gavel").classes("w-full mt-4 secondary-support-expansion"):
            ui.label("補助導線です。生成後に必要なときだけ開いて確認します。").classes(
                "text-sm text-gray-600"
            )

            legal_input = ui.textarea(
                label="チェック対象のテキスト",
                placeholder="本文を自動反映、または任意の文章を入力してください",
            ).classes("w-full generated-readonly").props("outlined stack-label rows=8")

            with ui.row().classes("w-full mt-3 gap-2"):
                legal_recheck_generated_button = ui.button("生成結果を再チェック", icon="refresh").classes("primary-btn")
                legal_check_button = ui.button("入力テキストをチェック", icon="policy").classes("primary-btn")
                legal_apply_button = ui.button("提案を本文に反映", icon="edit_note").props("outline").classes("primary-btn")
                legal_spinner = ui.spinner(size="md")
                legal_spinner.visible = False

            legal_status = ui.label("").classes("text-sm")

            # リスクレベル表示
            with ui.card().classes("w-full mt-4 p-4") as risk_card:
                risk_card.visible = False
                with ui.row().classes("items-center gap-2"):
                    risk_icon = ui.icon("info", size="sm")
                    risk_label = ui.label("").classes("font-bold text-lg")
                risk_desc = ui.label("").classes("text-sm text-gray-600")

            # 問題点と根拠の表示エリア
            issues_container = ui.column().classes("w-full mt-4 gap-2")
            issues_container.visible = False
            citation_guard_label = ui.label("").classes("text-sm text-gray-700 mt-2")
            citation_guard_label.visible = False

            legal_result_area = ui.textarea(
                label="提案後の本文（レビュー結果）",
                placeholder="チェック結果がここに表示されます",
            ).classes("w-full mt-4 generated-readonly").props("outlined stack-label rows=8 readonly")

            def _current_legal_verified_texts() -> list[str]:
                return collect_current_legal_verified_texts(getattr(state, "result", {}))

            def _render_legal_result(result: Dict[str, Any]) -> None:
                view = build_manual_legal_result_view(result)
                legal_result_area.value = str(view.get("checked_text", "") or "")

                risk_card.visible = True
                risk_icon._props["name"] = str(view.get("risk_icon_name") or "dangerous")
                risk_icon.classes(replace=str(view.get("risk_icon_class") or "text-red-600"))
                risk_icon.update()
                risk_label.text = str(view.get("risk_label_text") or "")
                risk_desc.text = str(view.get("risk_desc_text") or "")
                risk_card.classes(replace=str(view.get("risk_card_class") or "w-full mt-4 p-4 bg-red-50"))

                issues_container.clear()
                issues_container.visible = bool(view.get("issues_visible"))
                citation_guard_label.visible = bool(view.get("citation_guard_visible"))
                citation_guard_label.text = str(view.get("citation_guard_text") or "")
                issue_rows = _to_plain_list(view.get("issue_rows"))
                if issue_rows:
                    with issues_container:
                        with ui.row().classes("items-center gap-1"):
                            ui.icon("assignment", size="sm").classes("text-gray-700")
                            ui.label("検出された問題と修正根拠").classes("font-bold text-gray-700")
                        for issue in issue_rows:
                            issue_dict = _to_plain_dict(issue)
                            with ui.card().classes("w-full p-3 bg-gray-50"):
                                ui.label(str(issue_dict.get("title", ""))).classes("font-bold text-sm text-red-600")
                                with ui.row().classes("w-full gap-2 items-center"):
                                    ui.icon("close", size="sm").classes("text-red-500")
                                    ui.label(str(issue_dict.get("original", ""))).classes(
                                        "text-sm line-through text-gray-600"
                                    )
                                with ui.row().classes("w-full gap-2 items-center"):
                                    ui.icon("check_circle", size="sm").classes("text-green-500")
                                    ui.label(str(issue_dict.get("fixed", ""))).classes(
                                        "text-sm text-green-700 font-medium"
                                    )
                                with ui.row().classes("items-center gap-1 mt-1"):
                                    ui.icon("lightbulb", size="xs").classes("text-gray-600")
                                    ui.label(str(issue_dict.get("reason", ""))).classes("text-xs text-gray-600")

            async def run_legal_check(*, use_generated_body: bool = False) -> None:
                request = build_manual_legal_check_request(
                    use_generated_body=use_generated_body,
                    legal_input_text=legal_input.value,
                    generated_body_text=note_body_text.value,
                    current_result=getattr(state, "result", {}),
                )
                if use_generated_body:
                    legal_input.value = request.get("copied_legal_input_text") or ""
                if not request.get("has_text"):
                    ui.notify("チェック対象テキストを入力してください", color="warning")
                    return
                _log_ui_usage("manual_legal_check", "run", use_generated_body=use_generated_body)

                legal_spinner.visible = True
                legal_status.text = "チェック中..."
                risk_card.visible = False
                issues_container.clear()
                issues_container.visible = False

                try:
                    result = await run.io_bound(
                        run_legal_postcheck,
                        str(request.get("postcheck_text") or ""),
                        _to_plain_list(request.get("verified_texts")),
                    )
                    result_payload = _to_plain_dict(result)
                    _render_legal_result(result_payload)
                    legal_status.text = "チェック完了"
                    _log_ui_usage(
                        "manual_legal_check",
                        "completed",
                        risk_level=result_payload.get("risk_level", "none"),
                    )
                    ui.notify("リーガルチェックが完了しました", color="positive")
                except Exception:
                    logger.exception("Legal postcheck failed")
                    _log_ui_usage("manual_legal_check", "failed")
                    legal_status.text = "チェック中にエラーが発生しました（本文は保持されています）"
                    ui.notify("チェックに失敗しました（本文は保持されています）", color="negative")
                finally:
                    legal_spinner.visible = False

            def apply_legal_suggestion() -> None:
                payload = build_manual_legal_apply_payload(
                    checked_text=legal_result_area.value,
                    title_text=title_area.value,
                    lead_text=lead_area.value,
                    references_text=references_area.value,
                    hashtags_text=hashtags_area.value,
                )
                if not payload.get("has_checked_text"):
                    ui.notify("反映する提案がありません", color="warning")
                    return
                checked = str(payload.get("checked_text") or "")
                body_area.value = str(payload.get("body_text") or "")
                note_body_text.value = str(payload.get("note_body_text") or "")
                full_text_area.value = str(payload.get("full_text") or "")
                preview.content = sanitize_markdown_preview(
                    _replace_hashtags_for_preview(full_text_area.value, hashtags_area.value)
                )
                if isinstance(state.result, dict):
                    state.result["body"] = checked
                    state.result["full_text"] = full_text_area.value
                legal_status.text = "提案を本文へ反映しました"
                _log_ui_usage("manual_legal_check", "apply_suggestion")
                ui.notify("提案を本文へ反映しました", color="positive")

            async def rerun_generated_legal_check() -> None:
                await run_legal_check(use_generated_body=True)

            legal_recheck_generated_button.on("click", rerun_generated_legal_check)
            legal_check_button.on("click", run_legal_check)
            legal_apply_button.on("click", apply_legal_suggestion)


def run_app(host: str = "127.0.0.1", port: Optional[int] = None) -> None:
    import socket
    
    start_port = port or int(os.environ.get("PORT", "8080"))
    bind_host = os.environ.get("HOST") or os.environ.get("NICEGUI_HOST") or host
    if os.environ.get("CONTAINER_ENV"):
        bind_host = "0.0.0.0"
    
    def is_port_in_use(p):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((bind_host, p)) == 0

    final_port = start_port
    while is_port_in_use(final_port):
        print(f"[INFO] Port {final_port} is in use, trying next...")
        final_port += 1
        if final_port > start_port + 10:
            break

    from fastapi import Response

    @app.get("/health")
    def health_check():
        return Response(content='{"status":"ok"}', media_type="application/json")
            
    headless = os.environ.get("HEADLESS", "").lower() in ("1", "true", "yes")
    ui.run(
        host=bind_host,
        port=final_port,
        title="コトメイク | TECHIE",
        favicon=str(STATIC_DIR / "favicon_v2.png"),
        storage_secret=os.environ.get("NICEGUI_STORAGE_SECRET")
        or os.environ.get("SESSION_SECRET")
        or "techie-nicegui-storage-secret",
        reload=False,
        show=not headless,
    )


if __name__ in {"__main__", "__mp_main__"}:
    run_app()
