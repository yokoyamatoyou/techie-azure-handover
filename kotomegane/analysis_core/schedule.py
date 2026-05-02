from __future__ import annotations

import datetime as dt
import time
from typing import Any
from zoneinfo import ZoneInfo

from analysis_core.common import normalize_text

WEEKDAY_LABELS = {
    0: "月",
    1: "火",
    2: "水",
    3: "木",
    4: "金",
    5: "土",
    6: "日",
}
TIMEZONE_FALLBACK_HOURS = {
    "Asia/Tokyo": 9,
    "Etc/UTC": 0,
    "UTC": 0,
}


def parse_weekdays_csv(raw_value: Any) -> list[int]:
    values: list[int] = []
    for item in str(raw_value or "").split(","):
        token = normalize_text(item)
        if not token:
            continue
        try:
            weekday = int(token)
        except ValueError:
            continue
        if 0 <= weekday <= 6 and weekday not in values:
            values.append(weekday)
    return sorted(values)


def normalize_schedule_weekdays(weekdays: list[Any], weekly_run_count: int) -> list[int]:
    parsed: list[int] = []
    for item in weekdays:
        try:
            weekday = int(item)
        except (TypeError, ValueError):
            continue
        if 0 <= weekday <= 6 and weekday not in parsed:
            parsed.append(weekday)
    if not parsed:
        return []
    parsed = sorted(parsed)
    effective_count = max(1, min(int(weekly_run_count or 0) or len(parsed), len(parsed)))
    return parsed[:effective_count]


def format_weekdays_label(weekdays: list[int]) -> str:
    if not weekdays:
        return "-"
    return " / ".join(WEEKDAY_LABELS.get(day, str(day)) for day in weekdays)


def _parse_time_of_day(time_of_day: str) -> tuple[int, int]:
    raw = normalize_text(time_of_day or "09:00")
    if ":" not in raw:
        return 9, 0
    hour_text, minute_text = raw.split(":", 1)
    try:
        hour = max(0, min(23, int(hour_text)))
        minute = max(0, min(59, int(minute_text)))
    except ValueError:
        return 9, 0
    return hour, minute


def _resolve_timezone(timezone_name: str) -> dt.tzinfo:
    resolved_name = normalize_text(timezone_name or "Asia/Tokyo") or "Asia/Tokyo"
    try:
        return ZoneInfo(resolved_name)
    except Exception:
        fallback_hours = TIMEZONE_FALLBACK_HOURS.get(resolved_name, 0)
        return dt.timezone(dt.timedelta(hours=fallback_hours), name=resolved_name)


def compute_next_schedule_run(
    weekdays: list[int],
    weekly_run_count: int,
    time_of_day: str,
    timezone_name: str,
    *,
    base_timestamp: float | None = None,
) -> float | None:
    active_days = normalize_schedule_weekdays(weekdays, weekly_run_count)
    if not active_days:
        return None
    tz = _resolve_timezone(timezone_name)
    base_dt = dt.datetime.fromtimestamp(base_timestamp or time.time(), tz)
    hour, minute = _parse_time_of_day(time_of_day)
    for offset in range(0, 14):
        candidate_date = base_dt.date() + dt.timedelta(days=offset)
        if candidate_date.weekday() not in active_days:
            continue
        candidate = dt.datetime.combine(
            candidate_date,
            dt.time(hour=hour, minute=minute),
            tzinfo=tz,
        )
        if candidate.timestamp() > base_dt.timestamp():
            return candidate.timestamp()
    return None


def resolve_latest_due_schedule_slot(
    weekdays: list[int],
    weekly_run_count: int,
    time_of_day: str,
    timezone_name: str,
    *,
    now_timestamp: float | None = None,
) -> tuple[str, float] | None:
    active_days = normalize_schedule_weekdays(weekdays, weekly_run_count)
    if not active_days:
        return None
    tz = _resolve_timezone(timezone_name)
    now_dt = dt.datetime.fromtimestamp(now_timestamp or time.time(), tz)
    hour, minute = _parse_time_of_day(time_of_day)
    for offset in range(0, 8):
        candidate_date = now_dt.date() - dt.timedelta(days=offset)
        if candidate_date.weekday() not in active_days:
            continue
        candidate = dt.datetime.combine(
            candidate_date,
            dt.time(hour=hour, minute=minute),
            tzinfo=tz,
        )
        if candidate.timestamp() <= now_dt.timestamp():
            slot_key = candidate.strftime("%G-W%V-%u-%H%M")
            return slot_key, candidate.timestamp()
    return None


def format_schedule_slot(timestamp_value: float | None, timezone_name: str) -> str:
    if not timestamp_value:
        return "-"
    tz = _resolve_timezone(timezone_name)
    return dt.datetime.fromtimestamp(float(timestamp_value), tz).strftime("%Y-%m-%d %H:%M")


