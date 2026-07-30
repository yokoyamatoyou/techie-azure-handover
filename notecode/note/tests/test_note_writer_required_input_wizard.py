from note.note_writer_required_input_wizard import (
    _apply_required_input_wizard_typing_reset,
    _apply_writer_role_interaction_state,
    _apply_writer_role_value_change_state,
    _build_required_input_wizard_helper_text,
    _default_audience_profile_placeholder_text,
    _default_audience_profile_text,
    _prepare_current_mainline_required_inputs,
    _resolve_required_input_wizard_step,
    _resolve_required_input_wizard_view_state,
)


def test_prepare_required_inputs_defaults_audience_and_requires_writer_except_company_intro() -> None:
    prepared = _prepare_current_mainline_required_inputs(
        article_type_key="branding",
        semantic_article_key="",
        content_goal_key="auto",
        speaker_profile_input="",
        audience_profile_input="",
        core_message_input="  message  ",
        tone_profile_key="",
    )

    assert prepared["audience_profile_input"] == "一般読者"
    assert prepared["core_message_input"] == "message"
    assert prepared["tone_profile_key"] == "auto"
    assert prepared["missing_required_fields"] == ["speaker_profile"]

    company_intro = _prepare_current_mainline_required_inputs(
        article_type_key="branding",
        semantic_article_key="company_introduction",
        content_goal_key="auto",
        speaker_profile_input="",
        audience_profile_input="",
        core_message_input="",
        tone_profile_key="serious",
    )
    assert company_intro["missing_required_fields"] == []


def test_required_input_wizard_step_and_view_state() -> None:
    assert _resolve_required_input_wizard_step(
        article_type_ready=False,
        audience_ready=True,
        writer_ready=True,
    ) == 1
    assert _resolve_required_input_wizard_step(
        article_type_ready=True,
        audience_ready=True,
        writer_ready=False,
    ) == 3

    view = _resolve_required_input_wizard_view_state(
        article_type_ready=True,
        audience_ready=True,
        writer_ready=False,
        audience_committed=False,
        writer_committed=False,
        requested_focus=3,
    )
    assert view["focused_step"] == 3
    assert view["audience_committed"] is True
    assert view["writer_editor_visible"] is True


def test_required_input_wizard_text_and_typing_reset() -> None:
    assert _default_audience_profile_text() == "一般読者"
    assert _default_audience_profile_placeholder_text() == "例: 導入検討中の担当者"
    assert _build_required_input_wizard_helper_text(99) == "前提がそろいました。生成前チェックへ進めます。"

    state = {"focused_step": 4, "audience_committed": True, "writer_committed": True}
    changed = _apply_required_input_wizard_typing_reset(
        state,
        focused_step=2,
        clear_audience_commit=True,
        clear_writer_commit=True,
    )

    assert changed is True
    assert state == {"focused_step": 2, "audience_committed": False, "writer_committed": False}


def test_writer_role_value_change_state_clears_programmatic_default_without_override() -> None:
    refresh_state = {"expected_value": "自動", "user_interacting": False, "active": True}
    wizard_state = {"writer_role_user_overridden": False, "focused_step": 4, "writer_committed": True}

    plan = _apply_writer_role_value_change_state(
        current_label="自動",
        writer_role_default_refresh_state=refresh_state,
        required_input_wizard_state=wizard_state,
        is_article_type_managed_writer_role_label=lambda value: False,
    )

    assert plan == {"refresh_required_input": False, "invalidate_confirmation": False}
    assert refresh_state["expected_value"] == ""
    assert wizard_state["writer_role_user_overridden"] is False
    assert wizard_state["focused_step"] == 4


def test_writer_role_value_change_state_skips_managed_label_without_user_interaction() -> None:
    refresh_state = {"expected_value": "", "user_interacting": False, "active": False}
    wizard_state = {"writer_role_user_overridden": False}

    plan = _apply_writer_role_value_change_state(
        current_label="広報担当",
        writer_role_default_refresh_state=refresh_state,
        required_input_wizard_state=wizard_state,
        is_article_type_managed_writer_role_label=lambda value: value == "広報担当",
    )

    assert plan == {"refresh_required_input": False, "invalidate_confirmation": False}
    assert wizard_state["writer_role_user_overridden"] is False


def test_writer_role_value_change_state_marks_user_override_and_resets_writer_commit() -> None:
    refresh_state = {"expected_value": "", "user_interacting": True, "active": False}
    wizard_state = {"writer_role_user_overridden": False, "focused_step": 4, "writer_committed": True}

    plan = _apply_writer_role_value_change_state(
        current_label="編集担当",
        writer_role_default_refresh_state=refresh_state,
        required_input_wizard_state=wizard_state,
        is_article_type_managed_writer_role_label=lambda value: False,
    )

    assert plan == {"refresh_required_input": True, "invalidate_confirmation": True}
    assert refresh_state["user_interacting"] is False
    assert wizard_state["writer_role_user_overridden"] is True
    assert wizard_state["focused_step"] == 3
    assert wizard_state["writer_committed"] is False


def test_apply_writer_role_interaction_state_marks_interacting_and_resets_writer_commit() -> None:
    refresh_state = {"user_interacting": False}
    wizard_state = {"focused_step": 4, "writer_committed": True}

    changed = _apply_writer_role_interaction_state(
        writer_role_default_refresh_state=refresh_state,
        required_input_wizard_state=wizard_state,
    )

    assert changed is True
    assert refresh_state["user_interacting"] is True
    assert wizard_state["focused_step"] == 3
    assert wizard_state["writer_committed"] is False
