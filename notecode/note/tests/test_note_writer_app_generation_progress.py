from note.note_writer_app_generation_progress import (
    _coerce_display_generation_percent,
    _format_generation_progress_text,
    _generation_phase_progress,
    _resolve_display_generation_percent,
    _to_user_friendly_progress,
    build_generation_progress_display_state,
)


def test_coerce_display_generation_percent_bounds_and_fraction_inputs() -> None:
    assert _coerce_display_generation_percent(None) == 0
    assert _coerce_display_generation_percent("not-a-number") == 0
    assert _coerce_display_generation_percent(-5) == 0
    assert _coerce_display_generation_percent(150) == 100
    assert _coerce_display_generation_percent(42.4) == 42
    assert _coerce_display_generation_percent(0.42) == 42
    assert _coerce_display_generation_percent("0.42") == 42
    assert _coerce_display_generation_percent("1") == 1


def test_resolve_display_generation_percent_never_moves_backwards() -> None:
    assert _resolve_display_generation_percent(current_value=0.4, reported_percent=35) == 40
    assert _resolve_display_generation_percent(current_value=0.4, reported_percent=60) == 60
    assert _resolve_display_generation_percent(current_value="bad", reported_percent="0.25") == 25


def test_format_generation_progress_text_trims_optional_parts() -> None:
    assert (
        _format_generation_progress_text(
            percent=0.255,
            label_text="  下書きを生成中  ",
            detail="  詳細  ",
            elapsed="  （経過3秒）  ",
        )
        == "進行状況: 26% 下書きを生成中 詳細 （経過3秒）"
    )
    assert _format_generation_progress_text(percent=None, label_text="", detail="", elapsed="") == "進行状況: 0%"


def test_to_user_friendly_progress_maps_known_and_unknown_stages() -> None:
    assert _to_user_friendly_progress({"stage": "generate_article"}) == "本文を生成中..."
    assert _to_user_friendly_progress({"stage": "missing"}) == "現在処理中..."


def test_route_0506_progress_uses_injected_view_builder() -> None:
    def builder(stage: str) -> dict[str, object]:
        assert stage == "route_0506_fetch"
        return {"label_text": "Route view", "percent": 42}

    assert (
        _to_user_friendly_progress(
            {"stage": "route_0506_fetch"},
            route_progress_view_builder=builder,
        )
        == "Route view"
    )
    assert _generation_phase_progress(
        "route_0506_fetch",
        route_progress_view_builder=builder,
    ) == 42


def test_generation_phase_progress_maps_known_stages() -> None:
    assert _generation_phase_progress("validate") == 3
    assert _generation_phase_progress("completed") == 100
    assert _generation_phase_progress("unknown") == 0


def test_build_generation_progress_display_state_resolves_completed_and_elapsed() -> None:
    state = build_generation_progress_display_state(
        {"stage": "completed", "percent": 70},
        current_value=0.4,
        elapsed_seconds=3,
    )

    assert state["stage"] == "completed"
    assert state["label_text"] == "生成が完了しました。"
    assert state["display_percent"] == 100
    assert state["elapsed"] == "（経過3秒）"
