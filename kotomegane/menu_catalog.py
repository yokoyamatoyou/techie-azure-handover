from __future__ import annotations

from dataclasses import dataclass

SERVICE_KOTOMEGANE = "kotomegane"
DEFAULT_EXECUTION_MENU_KEY = "openai_single_observation"


@dataclass(frozen=True)
class ExecutionMenu:
    key: str
    label: str
    provider_keys: tuple[str, ...]
    manual_units: int
    batch_units: int
    scheduled_units: int
    scheduled_interval_hours: int
    summary: str
    runtime_ready: bool = True
    blocked_reason: str = ""


EXECUTION_MENUS: tuple[ExecutionMenu, ...] = (
    ExecutionMenu(
        key="openai_single_observation",
        label="OpenAI単独観測",
        provider_keys=("openai",),
        manual_units=1,
        batch_units=1,
        scheduled_units=1,
        scheduled_interval_hours=72,
        summary="OpenAI のみで観測する軽量メニューです。",
        runtime_ready=True,
    ),
    ExecutionMenu(
        key="three_ai_cross_observation",
        label="3AI横断観測",
        provider_keys=("openai", "gemini", "claude"),
        manual_units=2,
        batch_units=2,
        scheduled_units=2,
        scheduled_interval_hours=48,
        summary="OpenAI / Gemini / Claude を横断して観測するメニューです。",
        runtime_ready=False,
        blocked_reason="3AI横断観測は最新UI/実行ロジック反映後に有効化します。",
    ),
)


def get_execution_menu_catalog() -> list[ExecutionMenu]:
    return list(EXECUTION_MENUS)


def get_execution_menu(menu_key: str | None) -> ExecutionMenu:
    resolved_key = str(menu_key or "").strip() or DEFAULT_EXECUTION_MENU_KEY
    for menu in EXECUTION_MENUS:
        if menu.key == resolved_key:
            return menu
    for menu in EXECUTION_MENUS:
        if menu.key == DEFAULT_EXECUTION_MENU_KEY:
            return menu
    return EXECUTION_MENUS[0]


def is_execution_menu_runtime_ready(menu_key: str | None) -> bool:
    return bool(get_execution_menu(menu_key).runtime_ready)

