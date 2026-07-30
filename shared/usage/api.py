# -*- coding: utf-8 -*-
"""Authenticated usage summary and consumption APIs."""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from shared.auth.fastapi_auth import require_auth

from . import repository

router = APIRouter(tags=["usage"])
logger = logging.getLogger(__name__)


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


class CouponRedeemPayload(BaseModel):
    code: str


def _configured_free_credit_coupons() -> Dict[str, int]:
    """Return allowed TECHIE-side free-credit coupon codes.

    Format: TECHIE_FREE_CREDIT_COUPONS="TECHIE0001:1,OTHER2026:3".
    Defaults to the launch coupon requested by the client.
    """
    raw = os.environ.get("TECHIE_FREE_CREDIT_COUPONS", "TECHIE0001:1")
    coupons: Dict[str, int] = {}
    for item in raw.split(","):
        token = item.strip()
        if not token:
            continue
        code, _, units_text = token.partition(":")
        try:
            units = int(units_text or "1")
        except ValueError:
            units = 1
        if code.strip() and units > 0:
            coupons[code.strip().upper()] = units
    return coupons


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


@router.post("/api/usage/redeem-coupon")
async def redeem_coupon(payload: CouponRedeemPayload, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    code = payload.code.strip().upper()
    coupons = _configured_free_credit_coupons()
    units = coupons.get(code)
    if not units:
        logger.info(
            "Invalid free-credit coupon redemption attempt",
            extra={
                "tenant_id": user.get("tenant_id"),
                "user_id": user.get("user_id"),
                "coupon_code": code[:32],
            },
        )
        raise HTTPException(
            status_code=400,
            detail="クーポンコードが無効、または期限切れです。コードを確認して再入力してください。",
        )

    return repository.grant_bonus_credits(
        tenant_id=user["tenant_id"],
        service_key=repository.GLOBAL_CREDIT_SERVICE_KEY,
        units=units,
        actor_user_id=user["user_id"],
        reason="free_credit_coupon",
        idempotency_key=f"free-credit-coupon:{code}",
        metadata={
            "coupon_code": code,
            "user_email": user.get("email", ""),
        },
    ) | {"coupon_code": code, "coupon_units": units}
