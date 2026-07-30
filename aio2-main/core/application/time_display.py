from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

JST = timezone(timedelta(hours=9), "JST")


def _clean_datetime_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_datetime(value: Any, *, assume_naive_utc: bool = True) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = _clean_datetime_text(value)
        if not text:
            return None
        normalized = text
        explicit_tz: timezone | None = None
        upper = normalized.upper()
        if upper.endswith(" JST"):
            explicit_tz = JST
            normalized = normalized[:-4].strip()
        elif upper.endswith(" UTC"):
            explicit_tz = timezone.utc
            normalized = normalized[:-4].strip()
        elif upper.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if explicit_tz is not None and parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=explicit_tz)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc if assume_naive_utc else JST)
    return parsed.astimezone(JST)


def format_jst_datetime(value: Any, *, seconds: bool = False, assume_naive_utc: bool = True) -> str:
    """Format persisted analysis timestamps as an explicit JST display string."""
    parsed = _parse_datetime(value, assume_naive_utc=assume_naive_utc)
    if parsed is None:
        return _clean_datetime_text(value)
    pattern = "%Y-%m-%d %H:%M:%S JST" if seconds else "%Y-%m-%d %H:%M JST"
    return parsed.strftime(pattern)


def format_jst_datetime_compact(value: Any, *, assume_naive_utc: bool = True) -> str:
    parsed = _parse_datetime(value, assume_naive_utc=assume_naive_utc)
    if parsed is None:
        return _clean_datetime_text(value)
    return parsed.strftime("%m/%d %H:%M JST")


def current_jst_datetime_text(*, seconds: bool = False) -> str:
    return format_jst_datetime(datetime.now(timezone.utc), seconds=seconds)


def current_jst_filename_timestamp() -> str:
    return datetime.now(timezone.utc).astimezone(JST).strftime("%Y%m%d-%H%M%S")
