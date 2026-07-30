from note.note_writer_journey_confirmation_helpers import (
    _build_journey_confirmation_cta_state,
    _build_journey_generation_confirmation_state,
    _build_source_session_acceptance_confirmation_plan,
    _resolve_journey_confirm_button_text,
    apply_source_session_gate_to_cta_state,
)


def test_build_journey_confirmation_cta_state_blocks_generation_until_confirmed() -> None:
    state = _build_journey_confirmation_cta_state(confirmation_ready=False)

    assert state["badge_text"] == "未確認"
    assert state["generate_button_enabled"] is False
    assert state["generate_button_text"] == "確認後に生成を開始"


def test_build_journey_confirmation_cta_state_enables_generation_after_confirmation() -> None:
    state = _build_journey_confirmation_cta_state(confirmation_ready=True)

    assert state["badge_text"] == "確定済み"
    assert state["generate_button_enabled"] is True
    assert state["generate_button_text"] == "この内容で生成を開始"


def test_resolve_journey_confirm_button_text_keeps_confirm_for_enabled_gate() -> None:
    cta_state = _build_journey_confirmation_cta_state(confirmation_ready=False)

    text = _resolve_journey_confirm_button_text(
        cta_state=cta_state,
        gate_surface={"enabled": True, "button_text": "方針を確認する"},
        confirmation_ready=False,
        source_session_requires_review=False,
    )

    assert text == "内容を確認"


def test_resolve_journey_confirm_button_text_keeps_missing_check_for_review_block() -> None:
    cta_state = _build_journey_confirmation_cta_state(confirmation_ready=False)

    text = _resolve_journey_confirm_button_text(
        cta_state=cta_state,
        gate_surface={"enabled": False, "button_text": "方針を確認する"},
        confirmation_ready=False,
        source_session_requires_review=True,
    )

    assert text == "不足を確認"


def test_apply_source_session_gate_to_cta_state_blocks_ready_generation_for_review() -> None:
    result = apply_source_session_gate_to_cta_state(
        cta_state=_build_journey_confirmation_cta_state(confirmation_ready=True),
        gate_surface={"enabled": True, "hint_text": ""},
        confirmation_ready=True,
        source_session_state={"requires_review": True, "hint_text": "資料確認が必要です"},
    )

    assert result["source_session_requires_review"] is True
    assert result["gate_surface"]["enabled"] is False
    assert result["gate_surface"]["hint_text"] == "資料確認が必要です"
    assert result["cta_state"]["badge_text"] == "要入力"
    assert result["cta_state"]["card_hint_text"] == "資料確認が必要です"


def test_apply_source_session_gate_to_cta_state_preserves_non_review_gate_hint() -> None:
    result = apply_source_session_gate_to_cta_state(
        cta_state=_build_journey_confirmation_cta_state(confirmation_ready=False),
        gate_surface={"enabled": False, "hint_text": "テーマを入力してください"},
        confirmation_ready=False,
        source_session_state={"requires_review": False},
    )

    assert result["source_session_requires_review"] is False
    assert result["gate_surface"]["hint_text"] == "テーマを入力してください"
    assert result["cta_state"]["card_hint_text"] == "テーマを入力してください"


def test_build_journey_generation_confirmation_state_accepts_matching_signature() -> None:
    state = _build_journey_generation_confirmation_state(
        current_signature="sig-1",
        confirmed_signature="sig-1",
    )

    assert state["ready"] is True
    assert state["confirmation_state"] == "confirmed"
    assert state["confirmed_signature_present"] is True


def test_build_journey_generation_confirmation_state_blocks_missing_signature() -> None:
    state = _build_journey_generation_confirmation_state(
        current_signature="sig-1",
        confirmed_signature="",
    )

    assert state["ready"] is False
    assert state["confirmation_state"] == "missing_confirmation"
    assert state["confirmed_signature_present"] is False


def test_build_source_session_acceptance_confirmation_plan_invalidates_stale_signature() -> None:
    plan = _build_source_session_acceptance_confirmation_plan(
        current_signature="sig-2",
        confirmed_signature="sig-1",
    )

    assert plan["preserve_confirmation"] is False
    assert plan["invalidate_confirmation"] is True
    assert plan["confirmation_state"] == "stale_signature"
    assert plan["confirmed_signature_present"] is True
