from note.note_writer_app_generation_delay_display import (
    SLOW_SOURCE_COUNT_THRESHOLD,
    SLOW_TOTAL_CHARS_THRESHOLD,
    _build_generation_delay_notice,
)


def test_build_generation_delay_notice_returns_empty_when_fast() -> None:
    assert _build_generation_delay_notice(1, 1000) == ""


def test_build_generation_delay_notice_for_source_count() -> None:
    assert (
        _build_generation_delay_notice(SLOW_SOURCE_COUNT_THRESHOLD, 1000)
        == "引用ソース5件のため、通常より生成に時間がかかる可能性があります。"
    )


def test_build_generation_delay_notice_for_total_chars() -> None:
    assert (
        _build_generation_delay_notice(1, SLOW_TOTAL_CHARS_THRESHOLD)
        == "抽出本文18000文字のため、通常より生成に時間がかかる可能性があります。"
    )


def test_build_generation_delay_notice_combines_reasons_in_existing_order() -> None:
    assert (
        _build_generation_delay_notice(
            SLOW_SOURCE_COUNT_THRESHOLD + 1,
            SLOW_TOTAL_CHARS_THRESHOLD + 100,
        )
        == "引用ソース6件 / 抽出本文18100文字のため、通常より生成に時間がかかる可能性があります。"
    )


def test_build_generation_delay_notice_threshold_boundaries() -> None:
    assert (
        _build_generation_delay_notice(
            SLOW_SOURCE_COUNT_THRESHOLD - 1,
            SLOW_TOTAL_CHARS_THRESHOLD - 1,
        )
        == ""
    )
    assert "引用ソース5件" in _build_generation_delay_notice(
        SLOW_SOURCE_COUNT_THRESHOLD,
        SLOW_TOTAL_CHARS_THRESHOLD - 1,
    )
    assert "抽出本文18000文字" in _build_generation_delay_notice(
        SLOW_SOURCE_COUNT_THRESHOLD - 1,
        SLOW_TOTAL_CHARS_THRESHOLD,
    )
