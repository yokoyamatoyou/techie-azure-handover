# -*- coding: utf-8 -*-
"""Phase 2 billing/admin/reseller API router."""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shared.auth.fastapi_auth import require_auth

from . import repository
from .stripe_client import (
    create_checkout_session,
    create_connect_account,
    create_connect_onboarding_link,
    create_coupon_and_promotion_code,
    create_customer,
    create_customer_portal_session,
    create_transfer,
    list_customer_subscriptions,
)

router = APIRouter(tags=["phase2-billing"])


def _bootstrap_admin_emails() -> List[str]:
    raw = os.environ.get("PLATFORM_ADMIN_EMAILS", "")
    return [value.strip().lower() for value in raw.split(",") if value.strip()]


def _normalize_roles(user: Dict[str, Any]) -> List[str]:
    raw_roles = user.get("roles", "")
    if isinstance(raw_roles, list):
        token_roles = [str(role) for role in raw_roles]
    elif isinstance(raw_roles, str):
        token_roles = [role.strip() for role in raw_roles.split(",") if role.strip()]
    else:
        token_roles = []
    db_roles = repository.get_effective_roles(user["user_id"], user.get("email", ""))
    bootstrap_roles: List[str] = []
    if user.get("email", "").strip().lower() in _bootstrap_admin_emails():
        bootstrap_roles.append("platform_admin")
    return sorted(set(token_roles + db_roles + bootstrap_roles))


def _require_any_role(user: Dict[str, Any], allowed_roles: List[str]) -> None:
    roles = _normalize_roles(user)
    if not any(role in roles for role in allowed_roles):
        raise HTTPException(status_code=403, detail=f"Required role missing. Allowed: {', '.join(allowed_roles)}")


def _allowed_return_hosts() -> set[str]:
    values = [
        os.environ.get("HUB_BASE_URL", ""),
        os.environ.get("HUB_URL", ""),
        os.environ.get("SERVICE_BASE_URL", ""),
        os.environ.get("API_BASE_URL", ""),
        os.environ.get("KOTOMAKE_URL", ""),
        os.environ.get("KOTOMIGAKI_URL", ""),
        os.environ.get("KOTOMEGANE_URL", ""),
    ]
    configured = os.environ.get("STRIPE_ALLOWED_RETURN_HOSTS", "")
    values.extend([item.strip() for item in configured.split(",") if item.strip()])
    hosts: set[str] = {"app.techie.jp", "api.techie.jp"}
    for value in values:
        parsed = urlparse(value)
        host = parsed.netloc or parsed.path
        if host:
            hosts.add(host.split("@")[-1].split(":")[0].lower())
    return hosts


def _assert_allowed_return_url(value: str, field_name: str) -> None:
    parsed = urlparse(value)
    host = parsed.hostname.lower() if parsed.hostname else ""
    if parsed.scheme != "https" or host not in _allowed_return_hosts():
        raise HTTPException(status_code=400, detail=f"{field_name} must use an allowed HTTPS TECHIE domain")


def _subscription_metadata(subscription: Dict[str, Any]) -> Dict[str, Any]:
    metadata = dict(subscription.get("metadata") or {})
    for key in ("current_period_start", "current_period_end", "cancel_at", "cancel_at_period_end"):
        if subscription.get(key) is not None:
            metadata[key] = subscription.get(key)
    return metadata


def _subscription_plan_from_price(subscription: Dict[str, Any], metadata: Dict[str, Any]) -> tuple[str, str]:
    first_item = ((subscription.get("items") or {}).get("data") or [{}])[0]
    price = first_item.get("price") or {}
    price_id = price.get("id") or ""
    return metadata.get("plan_id") or _plan_key_from_price_id(price_id), price_id


def _upsert_stripe_subscription_for_tenant(
    *,
    tenant_id: str,
    stripe_customer_id: str,
    subscription: Dict[str, Any],
) -> Dict[str, Any]:
    metadata = _subscription_metadata(subscription)
    plan_id, price_id = _subscription_plan_from_price(subscription, metadata)
    return repository.upsert_subscription_contract(
        tenant_id=tenant_id,
        plan_id=plan_id,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=subscription.get("id", ""),
        stripe_checkout_session_id=metadata.get("checkout_session_id"),
        contract_status=subscription.get("status", "canceled"),
        metadata=metadata | {
            "stripe_price_id": price_id,
            "synced_from": "stripe_subscription_api",
        },
    )


def _retire_unsynced_active_contracts(*, stripe_customer_id: str, active_subscription_ids: List[str]) -> None:
    if active_subscription_ids:
        repository._execute(
            """
            UPDATE subscription_contract
            SET contract_status = 'cancelled',
                cancelled_at = COALESCE(cancelled_at, now()),
                updated_at = now()
            WHERE stripe_customer_id = %s
              AND contract_status IN ('active', 'trialing', 'checkout_completed')
              AND (
                  stripe_subscription_id IS NULL
                  OR NOT (stripe_subscription_id = ANY(%s))
              )
            """,
            (stripe_customer_id, active_subscription_ids),
        )
    else:
        repository._execute(
            """
            UPDATE subscription_contract
            SET contract_status = 'cancelled',
                cancelled_at = COALESCE(cancelled_at, now()),
                updated_at = now()
            WHERE stripe_customer_id = %s
              AND contract_status IN ('active', 'trialing', 'checkout_completed')
            """,
            (stripe_customer_id,),
        )


def _allowed_stripe_price_ids() -> set[str]:
    env_names = [
        "STRIPE_ENTRY_PRICE_ID",
        "STRIPE_STANDARD_PRICE_ID",
        "STRIPE_PRO_PRICE_ID",
        "STRIPE_ADDON_10_CREDIT_PRICE_ID",
        "STRIPE_ADDON_1_CREDIT_PRICE_ID",
    ]
    return {os.environ.get(name, "").strip() for name in env_names if os.environ.get(name, "").strip()}


def _plan_key_from_price_id(price_id: str) -> str:
    mapping = {
        os.environ.get("STRIPE_ENTRY_PRICE_ID", "").strip(): "entry",
        os.environ.get("STRIPE_STANDARD_PRICE_ID", "").strip(): "standard",
        os.environ.get("STRIPE_PRO_PRICE_ID", "").strip(): "pro",
    }
    return mapping.get(str(price_id or "").strip(), "")


class CheckoutSessionRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str
    service_code: str
    service_name: str = ""
    company_name: str = ""
    display_name: str = ""
    customer_email: Optional[str] = None
    plan_id: Optional[str] = None
    checkout_mode: str = "subscription"
    credit_grant_amount: int = 0


class PortalRequest(BaseModel):
    return_url: str


class BillingSyncRequest(BaseModel):
    pass


class ResellerRequest(BaseModel):
    reseller_code: str
    legal_name: str
    display_name: str
    tenant_id: Optional[str] = None


class ResellerOnboardingRequest(BaseModel):
    return_url: str
    refresh_url: str


class CouponRequestPayload(BaseModel):
    reseller_id: Optional[str] = None
    customer_account_id: Optional[str] = None
    plan_id: Optional[str] = None
    request_scope: str = "customer"
    requested_coupon_kind: str = "percent_off"
    requested_percent_off: Optional[float] = None
    requested_amount_off: Optional[float] = None
    requested_duration_kind: Optional[str] = None
    requested_duration_months: Optional[int] = None
    request_reason: str


class CouponDecisionPayload(BaseModel):
    decision_note: str = ""


@router.post("/api/billing/checkout-session")
async def billing_checkout_session(payload: CheckoutSessionRequest, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    _assert_allowed_return_url(payload.success_url, "success_url")
    _assert_allowed_return_url(payload.cancel_url, "cancel_url")
    if payload.checkout_mode not in {"subscription", "payment"}:
        raise HTTPException(status_code=400, detail="checkout_mode must be subscription or payment")
    if payload.checkout_mode == "subscription" and payload.credit_grant_amount:
        raise HTTPException(status_code=400, detail="credit_grant_amount is only valid for payment checkout")
    allowed_price_ids = _allowed_stripe_price_ids()
    if allowed_price_ids and payload.price_id not in allowed_price_ids:
        raise HTTPException(status_code=400, detail="Unknown Stripe Price ID")
    tenant_id = user["tenant_id"]
    email = payload.customer_email or user.get("email", "")
    display_name = payload.display_name or user.get("name", "") or payload.company_name or email or tenant_id
    account = repository.ensure_customer_account(
        tenant_id=tenant_id,
        legal_name=payload.company_name or display_name,
        display_name=display_name,
        billing_email=email,
    )
    stripe_customer_id = account.get("stripe_customer_id")
    if not stripe_customer_id:
        customer = create_customer(
            email=email,
            name=display_name,
            tenant_id=tenant_id,
            metadata={
                "user_id": user["user_id"],
                "user_email": user.get("email", ""),
                "service_code": payload.service_code,
                "service_name": payload.service_name,
                "plan_id": payload.plan_id or "",
                "company_name": payload.company_name or display_name,
                "display_name": display_name,
            },
        )
        stripe_customer_id = customer["customer_id"]
        repository.ensure_customer_account(
            tenant_id=tenant_id,
            legal_name=payload.company_name or display_name,
            display_name=display_name,
            billing_email=email,
            stripe_customer_id=stripe_customer_id,
        )
    return create_checkout_session(
        customer_id=stripe_customer_id,
        price_id=payload.price_id,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
        mode=payload.checkout_mode,
        metadata={
            "tenant_id": tenant_id,
            "user_id": user["user_id"],
            "user_email": user.get("email", ""),
            "service_code": payload.service_code,
            "service_name": payload.service_name,
            "plan_id": payload.plan_id or "",
            "checkout_mode": payload.checkout_mode,
            "credit_grant_amount": str(payload.credit_grant_amount or 0),
            "company_name": payload.company_name or display_name,
            "display_name": display_name,
        },
        idempotency_key=f"checkout:{tenant_id}:{payload.checkout_mode}:{payload.price_id}:{uuid.uuid4()}",
    )


@router.post("/api/billing/customer-portal")
async def billing_customer_portal(payload: PortalRequest, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    _assert_allowed_return_url(payload.return_url, "return_url")
    account = repository.get_customer_account_by_tenant(user["tenant_id"])
    if not account or not account.get("stripe_customer_id"):
        raise HTTPException(status_code=404, detail="Stripe customer not found for this tenant")
    return create_customer_portal_session(customer_id=account["stripe_customer_id"], return_url=payload.return_url)


@router.post("/api/billing/sync-subscription")
async def billing_sync_subscription(payload: BillingSyncRequest, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    """Synchronize active Stripe subscription state into TECHIE DB.

    Stripe webhooks remain the primary path. This endpoint is a safe fallback
    for the account screen after Checkout/Portal redirects, so credits are not
    blocked by delayed webhook delivery.
    """
    account = repository.get_customer_account_by_tenant(user["tenant_id"])
    if not account or not account.get("stripe_customer_id"):
        return {"synced": False, "reason": "customer_not_found"}

    stripe_customer_id = account["stripe_customer_id"]
    subscriptions = list_customer_subscriptions(stripe_customer_id)
    all_subscriptions = list(subscriptions.get("data", []))
    synced_contracts: Dict[str, Dict[str, Any]] = {}
    for item in all_subscriptions:
        subscription_id = item.get("id", "")
        if not subscription_id:
            continue
        synced_contracts[subscription_id] = _upsert_stripe_subscription_for_tenant(
            tenant_id=user["tenant_id"],
            stripe_customer_id=stripe_customer_id,
            subscription=item,
        )

    candidates = [
        item for item in all_subscriptions
        if item.get("status") in {"active", "trialing", "past_due"}
    ]
    active_subscription_ids = [
        item.get("id", "")
        for item in candidates
        if item.get("id") and item.get("status") in {"active", "trialing"}
    ]
    _retire_unsynced_active_contracts(
        stripe_customer_id=stripe_customer_id,
        active_subscription_ids=active_subscription_ids,
    )
    if not candidates:
        latest_subscription = sorted(
            all_subscriptions,
            key=lambda item: int(item.get("created") or 0),
            reverse=True,
        )
        if not latest_subscription:
            return {"synced": False, "reason": "subscription_not_found"}

        subscription = latest_subscription[0]
        from shared.usage import repository as usage_repository

        usage_repository.ensure_usage_account(
            tenant_id=user["tenant_id"],
            service_key=usage_repository.GLOBAL_CREDIT_SERVICE_KEY,
        )
        return {
            "synced": True,
            "reason": "active_subscription_not_found",
            "subscription_id": subscription.get("id"),
            "status": subscription.get("status"),
        }

    subscription = sorted(candidates, key=lambda item: int(item.get("created") or 0), reverse=True)[0]
    metadata = _subscription_metadata(subscription)
    plan_id, _price_id = _subscription_plan_from_price(subscription, metadata)
    contract = synced_contracts.get(subscription.get("id", ""))
    if not contract:
        contract = _upsert_stripe_subscription_for_tenant(
            tenant_id=user["tenant_id"],
            stripe_customer_id=stripe_customer_id,
            subscription=subscription,
        )
    from shared.usage import repository as usage_repository

    usage_repository.ensure_usage_account(
        tenant_id=user["tenant_id"],
        service_key=usage_repository.GLOBAL_CREDIT_SERVICE_KEY,
        subscription_contract_id=contract["subscription_contract_id"],
    )
    return {
        "synced": True,
        "subscription_id": subscription.get("id"),
        "status": subscription.get("status"),
        "plan_id": plan_id,
    }


@router.post("/api/resellers")
async def create_reseller(payload: ResellerRequest, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    _require_any_role(user, ["platform_admin"])
    return repository.create_or_update_reseller(
        reseller_code=payload.reseller_code,
        legal_name=payload.legal_name,
        display_name=payload.display_name,
        tenant_id=payload.tenant_id,
    )


@router.post("/api/resellers/{reseller_id}/connect-onboarding")
async def create_reseller_connect_onboarding(
    reseller_id: str,
    payload: ResellerOnboardingRequest,
    user: Dict[str, Any] = Depends(require_auth),
) -> Dict[str, Any]:
    _require_any_role(user, ["platform_admin"])
    reseller = repository.get_reseller(reseller_id)
    if not reseller:
        raise HTTPException(status_code=404, detail="Reseller not found")
    stripe_account_id = reseller.get("stripe_connect_account_id")
    if not stripe_account_id:
        account = create_connect_account(
            email=user.get("email", ""),
            business_name=reseller["legal_name"],
            metadata={"reseller_id": reseller_id, "reseller_code": reseller["reseller_code"]},
        )
        stripe_account_id = account["account_id"]
        repository.create_or_update_reseller(
            reseller_code=reseller["reseller_code"],
            legal_name=reseller["legal_name"],
            display_name=reseller["display_name"],
            tenant_id=reseller.get("tenant_id"),
            stripe_connect_account_id=stripe_account_id,
        )
    return create_connect_onboarding_link(
        account_id=stripe_account_id,
        refresh_url=payload.refresh_url,
        return_url=payload.return_url,
    )


@router.get("/api/reseller-portal/customers")
async def reseller_portal_customers(user: Dict[str, Any] = Depends(require_auth)) -> List[Dict[str, Any]]:
    _require_any_role(user, ["reseller"])
    return repository.list_reseller_customers(user["user_id"], user.get("email", ""))


@router.get("/api/reseller-portal/customers/{customer_account_id}")
async def reseller_portal_customer_detail(customer_account_id: str, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    _require_any_role(user, ["reseller"])
    detail = repository.get_reseller_customer_detail(customer_account_id, user["user_id"], user.get("email", ""))
    if not detail:
        raise HTTPException(status_code=404, detail="Customer not found")
    return detail


@router.get("/api/reseller-portal/payouts")
async def reseller_portal_payouts(user: Dict[str, Any] = Depends(require_auth)) -> List[Dict[str, Any]]:
    _require_any_role(user, ["reseller"])
    return repository.list_reseller_payouts(user["user_id"], user.get("email", ""))


@router.post("/api/reseller-portal/coupon-requests")
async def reseller_coupon_request(payload: CouponRequestPayload, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    _require_any_role(user, ["reseller", "platform_admin", "platform_operator"])
    record = repository.create_coupon_request(
        reseller_id=payload.reseller_id,
        customer_account_id=payload.customer_account_id,
        plan_id=payload.plan_id,
        requested_by_principal=user["user_id"],
        request_scope=payload.request_scope,
        requested_coupon_kind=payload.requested_coupon_kind,
        request_reason=payload.request_reason,
        requested_percent_off=payload.requested_percent_off,
        requested_amount_off=payload.requested_amount_off,
        requested_duration_kind=payload.requested_duration_kind,
        requested_duration_months=payload.requested_duration_months,
    )
    repository.add_coupon_audit_log(
        coupon_request_id=record["coupon_request_id"],
        discount_grant_id=None,
        actor_principal=user["user_id"],
        action_type="coupon_request_created",
        payload=payload.model_dump(),
    )
    return record


@router.get("/api/admin/coupon-requests")
async def admin_coupon_requests(user: Dict[str, Any] = Depends(require_auth)) -> List[Dict[str, Any]]:
    _require_any_role(user, ["platform_admin", "platform_operator"])
    return repository.list_coupon_requests()


@router.post("/api/admin/coupon-requests/{coupon_request_id}/approve")
async def approve_coupon_request(coupon_request_id: str, payload: CouponDecisionPayload, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    _require_any_role(user, ["platform_admin", "platform_operator"])
    request_row = repository.get_coupon_request(coupon_request_id)
    if not request_row:
        raise HTTPException(status_code=404, detail="Coupon request not found")
    repository.record_coupon_approval(coupon_request_id, user["user_id"], "approved", payload.decision_note)
    created = create_coupon_and_promotion_code(
        coupon_kind=request_row["requested_coupon_kind"],
        percent_off=request_row.get("requested_percent_off"),
        amount_off=request_row.get("requested_amount_off"),
        currency="jpy",
        duration_kind=request_row.get("requested_duration_kind") or "once",
        duration_months=request_row.get("requested_duration_months"),
        code_prefix=f"TECHIE-{coupon_request_id[:8]}",
    )
    grant = repository.create_discount_grant(
        coupon_request_id=coupon_request_id,
        approved_by_principal=user["user_id"],
        stripe_coupon_id=created["coupon_id"],
        stripe_promotion_code_id=created.get("promotion_code_id"),
        target_scope=request_row["request_scope"],
        discount_kind=request_row["requested_coupon_kind"],
        percent_off=request_row.get("requested_percent_off"),
        amount_off=request_row.get("requested_amount_off"),
        currency="jpy",
        duration_kind=request_row.get("requested_duration_kind"),
        duration_months=request_row.get("requested_duration_months"),
    )
    repository.add_coupon_audit_log(
        coupon_request_id=coupon_request_id,
        discount_grant_id=grant["discount_grant_id"],
        actor_principal=user["user_id"],
        action_type="coupon_request_approved",
        payload={"coupon": created, "note": payload.decision_note},
    )
    return {"approval": "approved", "grant": grant, "stripe": created}


@router.post("/api/admin/coupon-requests/{coupon_request_id}/reject")
async def reject_coupon_request(coupon_request_id: str, payload: CouponDecisionPayload, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    _require_any_role(user, ["platform_admin", "platform_operator"])
    repository.record_coupon_approval(coupon_request_id, user["user_id"], "rejected", payload.decision_note)
    repository.add_coupon_audit_log(
        coupon_request_id=coupon_request_id,
        discount_grant_id=None,
        actor_principal=user["user_id"],
        action_type="coupon_request_rejected",
        payload={"note": payload.decision_note},
    )
    return {"approval": "rejected"}


@router.get("/api/admin/payouts")
async def admin_payouts(user: Dict[str, Any] = Depends(require_auth)) -> List[Dict[str, Any]]:
    _require_any_role(user, ["platform_admin", "platform_operator"])
    return repository.list_admin_payouts()


@router.post("/api/admin/payouts/{payout_ledger_id}/execute")
async def admin_execute_payout(payout_ledger_id: str, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    _require_any_role(user, ["platform_admin"])
    payout = repository.get_payout_ledger(payout_ledger_id)
    if not payout:
        raise HTTPException(status_code=404, detail="Payout ledger not found")
    if payout.get("payout_status") in {"processing", "transferred"}:
        raise HTTPException(status_code=409, detail=f"Payout is already {payout.get('payout_status')}")
    reseller = repository.get_reseller(payout["reseller_id"])
    if not reseller or not reseller.get("stripe_connect_account_id"):
        raise HTTPException(status_code=400, detail="Reseller Connect account is not configured")
    execution = repository.queue_payout_execution(
        payout_ledger_id,
        payout["reseller_id"],
        request_payload={"action": "execute", "payout_ledger_id": payout_ledger_id},
    )
    try:
        repository.mark_payout_ledger_status(payout_ledger_id, "processing")
        transfer = create_transfer(
            connected_account_id=reseller["stripe_connect_account_id"],
            amount=float(payout["payout_amount"]),
            currency=payout["payout_currency"],
            transfer_group=payout.get("transfer_group") or f"techie-{payout_ledger_id}",
            metadata={"payout_ledger_id": payout_ledger_id, "reseller_id": payout["reseller_id"]},
            idempotency_key=f"payout-transfer:{payout_ledger_id}",
        )
        repository.mark_payout_execution_result(
            execution["reseller_payout_execution_id"],
            execution_status="succeeded",
            stripe_transfer_id=transfer["transfer_id"],
            response_payload=transfer,
        )
        repository.mark_payout_ledger_status(payout_ledger_id, "transferred", "released")
        return {"status": "transferred", "execution": execution, "transfer": transfer}
    except Exception as exc:
        repository.mark_payout_execution_result(
            execution["reseller_payout_execution_id"],
            execution_status="failed",
            failure_message=str(exc),
        )
        repository.mark_payout_ledger_status(payout_ledger_id, "failed")
        raise HTTPException(status_code=500, detail=f"Payout execution failed: {exc}")


@router.post("/api/admin/payouts/{payout_ledger_id}/retry")
async def admin_retry_payout(payout_ledger_id: str, user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    _require_any_role(user, ["platform_admin"])
    return await admin_execute_payout(payout_ledger_id, user)
