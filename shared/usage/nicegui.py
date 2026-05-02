# -*- coding: utf-8 -*-
"""NiceGUI-oriented helpers for the shared usage ledger."""
from __future__ import annotations

from typing import Any, Dict, Optional

from nicegui import run

from shared.auth.nicegui_identity import get_current_nicegui_user

from . import repository


async def consume_usage_for_current_user(
    *,
    service_key: str,
    action_key: str,
    units: int = 1,
    idempotency_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    user = get_current_nicegui_user()
    return await run.io_bound(
        repository.consume_credits,
        tenant_id=user["tenant_id"],
        service_key=service_key,
        actor_user_id=user["user_id"],
        action_key=action_key,
        units=units,
        idempotency_key=idempotency_key,
        metadata=metadata or {},
    )


async def get_usage_summary_for_current_user(*, service_key: str) -> Dict[str, Any]:
    user = get_current_nicegui_user()
    return await run.io_bound(
        repository.get_usage_summary,
        tenant_id=user["tenant_id"],
        service_key=service_key,
    )


async def grant_usage_for_current_user(
    *,
    service_key: str,
    units: int,
    reason: str,
    idempotency_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    user = get_current_nicegui_user()
    return await run.io_bound(
        repository.grant_bonus_credits,
        tenant_id=user["tenant_id"],
        service_key=service_key,
        units=units,
        actor_user_id=user["user_id"],
        reason=reason,
        idempotency_key=idempotency_key,
        metadata=metadata or {},
    )
