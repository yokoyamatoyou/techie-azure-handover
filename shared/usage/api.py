# -*- coding: utf-8 -*-
"""Authenticated usage summary and consumption APIs."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from shared.auth.fastapi_auth import require_auth

from . import repository

router = APIRouter(tags=["usage"])


class UsageConsumePayload(BaseModel):
    service_key: str
    action_key: str
    units: int = Field(default=1, ge=1)
    idempotency_key: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UsageGrantPayload(BaseModel):
    service_key: str
    units: int = Field(ge=1)
    reason: str
    idempotency_key: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.get("/api/usage/summary")
async def usage_summary(service_key: str, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    return repository.get_usage_summary(tenant_id=user["tenant_id"], service_key=service_key)


@router.post("/api/usage/consume")
async def usage_consume(payload: UsageConsumePayload, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    try:
        return repository.consume_credits(
            tenant_id=user["tenant_id"],
            service_key=payload.service_key,
            actor_user_id=user["user_id"],
            action_key=payload.action_key,
            units=payload.units,
            idempotency_key=payload.idempotency_key,
            metadata=payload.metadata,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=402, detail=str(exc))


@router.post("/api/usage/grant")
async def usage_grant(payload: UsageGrantPayload, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    roles = {role.strip() for role in str(user.get("roles", "")).split(",") if role.strip()}
    if "admin" not in roles and "platform_admin" not in roles:
        raise HTTPException(status_code=403, detail="Admin role required")
    return repository.grant_bonus_credits(
        tenant_id=user["tenant_id"],
        service_key=payload.service_key,
        units=payload.units,
        actor_user_id=user["user_id"],
        reason=payload.reason,
        idempotency_key=payload.idempotency_key,
        metadata=payload.metadata,
    )
