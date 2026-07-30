"""Required-input wizard pure helpers for note_writer_app."""
from __future__ import annotations

from typing import Any, Callable, Dict, List


def _default_audience_profile_text() -> str:
    return "一般読者"


def _default_audience_profile_placeholder_text() -> str:
    return "例: 導入検討中の担当者"


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
    del article_type_key, content_goal_key
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
        1: "STEP2まで選ぶと、STEP3で誰向けかを入力できます。前の内容を変えると、後のステップは選び直しになります。",
        2: "STEP3: まず誰向けの記事かを短く入れてください。ここを変えると、STEP4は選び直しになります。",
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


def _apply_writer_role_value_change_state(
    *,
    current_label: str,
    writer_role_default_refresh_state: Dict[str, Any],
    required_input_wizard_state: Dict[str, Any],
    is_article_type_managed_writer_role_label: Callable[[str], bool],
) -> Dict[str, bool]:
    normalized_label = str(current_label or "")
    expected_default = str(writer_role_default_refresh_state.get("expected_value") or "")
    if expected_default and normalized_label == expected_default:
        writer_role_default_refresh_state["expected_value"] = ""
        return {"refresh_required_input": False, "invalidate_confirmation": False}
    if (
        not bool(writer_role_default_refresh_state.get("user_interacting"))
        and is_article_type_managed_writer_role_label(normalized_label)
    ):
        return {"refresh_required_input": False, "invalidate_confirmation": False}
    writer_role_default_refresh_state["user_interacting"] = False
    if not writer_role_default_refresh_state.get("active"):
        required_input_wizard_state["writer_role_user_overridden"] = True
    _apply_required_input_wizard_typing_reset(
        required_input_wizard_state,
        focused_step=3,
        clear_writer_commit=True,
    )
    return {"refresh_required_input": True, "invalidate_confirmation": True}


def _apply_writer_role_interaction_state(
    *,
    writer_role_default_refresh_state: Dict[str, Any],
    required_input_wizard_state: Dict[str, Any],
) -> bool:
    writer_role_default_refresh_state["user_interacting"] = True
    return _apply_required_input_wizard_typing_reset(
        required_input_wizard_state,
        focused_step=3,
        clear_writer_commit=True,
    )
