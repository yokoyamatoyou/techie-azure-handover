"""Plain-data helpers for current mainline generation UI state transitions."""
from __future__ import annotations

from typing import Any, Dict


def _normalize_exception_phase(phase: str = "") -> str:
    normalized = str(phase or "").strip()
    if normalized:
        return normalized
    return "generation"


def build_current_mainline_generation_prerun_plan(
    *,
    pre_delay_notice: str = "",
    preview_placeholder: str = "",
) -> Dict[str, Any]:
    normalized_notice = str(pre_delay_notice or "").strip()
    status_text = "現在準備中..."
    if normalized_notice:
        status_text = "現在準備中... (データ量が多いため時間がかかる場合があります)"

    return {
        "busy": True,
        "refresh_step_indicators": True,
        "disable_generate_button": True,
        "generate_button_text": "生成中...",
        "spinner_visible": True,
        "generation_progress_visible": True,
        "generation_progress_value": 0.0,
        "generation_progress_note_visible": True,
        "status_text": status_text,
        "source_error_content": "",
        "output_fields": {
            "title": "",
            "lead": "",
            "body": "",
            "references": "",
            "hashtags": "",
            "full_text": "",
            "note_body_text": "",
            "linkedin_text": "",
            "linkedin_short_text": "",
        },
        "preview": {
            "content": str(preview_placeholder or ""),
            "placeholder_active": True,
        },
        "stats_text": "",
        "generated_images": [],
        "refresh_generated_images": True,
        "activate_generation_progress_timer": True,
    }


def build_current_mainline_generation_exception_plan(*, phase: str = "") -> Dict[str, Any]:
    normalized_phase = _normalize_exception_phase(phase)
    return {
        "status_text": "生成に失敗しました。入力内容を確認後、もう一度『記事を生成』を押してください。",
        "generation_progress_note_text": f"失敗箇所: {normalized_phase}（ログを確認してください）",
        "generation_progress_note_visible": True,
        "notify_text": "生成に失敗しました。入力やAPI設定を確認してください。",
        "notify_color": "negative",
    }


def build_current_mainline_generation_cleanup_plan() -> Dict[str, Any]:
    return {
        "deactivate_generation_progress_timer": True,
        "spinner_visible": False,
        "generation_progress_visible": False,
        "generation_progress_value": 0.0,
        "busy": False,
        "refresh_step_indicators": True,
        "enable_generate_button": True,
        "generate_button_text": "記事を生成",
    }


def build_current_mainline_generation_complete_plan() -> Dict[str, Any]:
    return {
        "generation_progress_value": 1.0,
        "reset_pdf_assist": True,
        "pdf_assist_status_text": "",
        "refresh_pdf_assist_panel": True,
    }
