from __future__ import annotations

from dataclasses import dataclass, field

SERVICE_KOTOMEGANE = "kotomegane"
DEFAULT_PLAN_KEY = "upper"


@dataclass(frozen=True)
class PlanCatalogEntry:
    service_key: str
    key: str
    label: str
    manual_enabled: bool
    batch_enabled: bool
    scheduled_batch_enabled: bool
    provider_total_question_budgets: dict[str, int] = field(default_factory=dict)
    note: str = ""


PLAN_CATALOG: tuple[PlanCatalogEntry, ...] = (
    PlanCatalogEntry(
        service_key=SERVICE_KOTOMEGANE,
        key="poc",
        label="PoC",
        manual_enabled=True,
        batch_enabled=False,
        scheduled_batch_enabled=False,
        provider_total_question_budgets={"openai": 30},
        note="OpenAI の手動確認を中心に使う前提です。",
    ),
    PlanCatalogEntry(
        service_key=SERVICE_KOTOMEGANE,
        key="light",
        label="Light",
        manual_enabled=True,
        batch_enabled=True,
        scheduled_batch_enabled=True,
        provider_total_question_budgets={"openai": 50},
        note="週次運用を前提に、OpenAI を中心に使う軽量プランです。",
    ),
    PlanCatalogEntry(
        service_key=SERVICE_KOTOMEGANE,
        key="upper",
        label="Upper",
        manual_enabled=True,
        batch_enabled=True,
        scheduled_batch_enabled=True,
        provider_total_question_budgets={"openai": 30, "gemini": 30, "claude": 15},
        note="複数 provider の上限差を保持しつつ、batch と定期チェックを使う前提です。",
    ),
)


def get_plan_catalog(service_key: str = SERVICE_KOTOMEGANE) -> list[PlanCatalogEntry]:
    return [entry for entry in PLAN_CATALOG if entry.service_key == service_key]


def get_plan_entry(
    service_key: str = SERVICE_KOTOMEGANE,
    plan_key: str = DEFAULT_PLAN_KEY,
) -> PlanCatalogEntry:
    for entry in PLAN_CATALOG:
        if entry.service_key == service_key and entry.key == plan_key:
            return entry
    for entry in PLAN_CATALOG:
        if entry.service_key == service_key and entry.key == DEFAULT_PLAN_KEY:
            return entry
    return PLAN_CATALOG[0]


def resolve_plan_question_budget(
    provider_key: str,
    *,
    service_key: str = SERVICE_KOTOMEGANE,
    plan_key: str = DEFAULT_PLAN_KEY,
    fallback_budget: int = 1,
) -> int:
    entry = get_plan_entry(service_key, plan_key)
    planned_budget = entry.provider_total_question_budgets.get(provider_key)
    if planned_budget is None:
        return max(1, int(fallback_budget or 1))
    return max(1, int(planned_budget or fallback_budget or 1))


def plan_supports_run_mode(
    run_mode: str,
    *,
    service_key: str = SERVICE_KOTOMEGANE,
    plan_key: str = DEFAULT_PLAN_KEY,
) -> bool:
    entry = get_plan_entry(service_key, plan_key)
    mode = str(run_mode or "").strip().lower()
    if mode == "manual":
        return bool(entry.manual_enabled)
    if mode == "scheduled":
        return bool(entry.scheduled_batch_enabled)
    if mode == "batch":
        return bool(entry.batch_enabled)
    return False
