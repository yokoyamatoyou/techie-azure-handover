from __future__ import annotations

from datetime import datetime, timezone

from core.application.time_display import format_jst_datetime, format_jst_datetime_compact


def test_format_jst_datetime_treats_naive_values_as_utc() -> None:
    assert format_jst_datetime("2026-04-02 12:00:00") == "2026-04-02 21:00 JST"
    assert format_jst_datetime("2026-04-02T12:00:00") == "2026-04-02 21:00 JST"


def test_format_jst_datetime_keeps_explicit_timezone_meaning() -> None:
    assert format_jst_datetime("2026-04-02T12:00:00+00:00") == "2026-04-02 21:00 JST"
    assert format_jst_datetime("2026-04-02T12:00:00+09:00") == "2026-04-02 12:00 JST"
    assert format_jst_datetime("2026-04-02 12:00:00 JST") == "2026-04-02 12:00 JST"


def test_format_jst_datetime_compact_adds_timezone_label() -> None:
    value = datetime(2026, 4, 2, 12, 0, tzinfo=timezone.utc)
    assert format_jst_datetime_compact(value) == "04/02 21:00 JST"
