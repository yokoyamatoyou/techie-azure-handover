"""Pure journey confirmation state helpers for note_writer_app."""
from __future__ import annotations

from typing import Any, Dict, Mapping


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


def apply_source_session_gate_to_cta_state(
    *,
    cta_state: Mapping[str, Any],
    gate_surface: Mapping[str, Any],
    confirmation_ready: bool,
    source_session_state: Mapping[str, Any],
) -> Dict[str, Any]:
    source_session_requires_review = bool(source_session_state.get("requires_review"))
    next_gate_surface = dict(gate_surface)
    if source_session_requires_review:
        next_gate_surface = {
            **next_gate_surface,
            "enabled": False,
            "hint_text": str(source_session_state.get("hint_text") or ""),
            "hint_classes": "text-amber-700",
        }

    next_cta_state = dict(cta_state)
    gate_hint_text = str(next_gate_surface.get("hint_text") or "")
    if confirmation_ready and not bool(next_gate_surface.get("enabled")):
        next_cta_state = {
            **next_cta_state,
            "badge_text": "要入力",
            "badge_classes": "bg-amber-100 text-amber-700",
            "card_hint_text": gate_hint_text,
        }
    elif not bool(next_gate_surface.get("enabled")) and gate_hint_text.strip():
        next_cta_state = {
            **next_cta_state,
            "card_hint_text": gate_hint_text,
        }
    return {
        "cta_state": next_cta_state,
        "gate_surface": next_gate_surface,
        "source_session_requires_review": source_session_requires_review,
    }


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
