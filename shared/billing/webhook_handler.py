# -*- coding: utf-8 -*-
"""Stripe webhook router with DB-backed idempotency and Phase 2 ledger updates."""
from __future__ import annotations

import logging
import os
from typing import Any, Awaitable, Callable, Dict

from fastapi import APIRouter, Header, HTTPException, Request

from . import repository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["billing"])
_event_handlers: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Awaitable[None]]] = {}


def _get_webhook_secret() -> str:
    return os.environ.get("STRIPE_WEBHOOK_SECRET", "")


def _get_webhook_queue() -> str:
    return os.environ.get("STRIPE_WEBHOOK_QUEUE", "stripe-webhook-events")


def _subscription_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    metadata = dict(data.get("metadata") or {})
    for key in ("current_period_start", "current_period_end", "cancel_at", "cancel_at_period_end"):
        if data.get(key) is not None:
            metadata[key] = data.get(key)
    return metadata


def on_event(event_type: str):
    def decorator(func: Callable[[Dict[str, Any], Dict[str, Any]], Awaitable[None]]):
        _event_handlers[event_type] = func
        return func

    return decorator


def _minimize_stripe_event(event: Dict[str, Any]) -> Dict[str, Any]:
    obj = (event.get("data") or {}).get("object") or {}
    return {
        "id": event.get("id"),
        "type": event.get("type"),
        "created": event.get("created"),
        "livemode": event.get("livemode"),
        "object_id": obj.get("id"),
        "object_type": obj.get("object"),
        "customer": obj.get("customer"),
        "subscription": obj.get("subscription"),
        "invoice": obj.get("invoice"),
        "payment_intent": obj.get("payment_intent"),
        "amount_paid": obj.get("amount_paid"),
        "amount_due": obj.get("amount_due"),
        "currency": obj.get("currency"),
        "metadata": obj.get("metadata") or {},
    }


@router.post("/api/stripe/webhooks")
@router.post("/api/stripe/webhook")
@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default="", alias="Stripe-Signature"),
):
    import stripe

    body = await request.body()
    webhook_secret = _get_webhook_secret()
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload=body,
            sig_header=stripe_signature,
            secret=webhook_secret,
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}")

    event_id = event.get("id", "")
    event_type = event.get("type", "")
    existing = repository.get_webhook_event(event_id)
    if existing and existing.get("processing_status") == "processed":
        return {"status": "already_processed", "event_id": event_id, "event_type": event_type}

    repository.log_webhook_event(
        stripe_event_id=event_id,
        event_type=event_type,
        payload=_minimize_stripe_event(event),
        signature_verified=True,
        queue_name=_get_webhook_queue(),
    )

    handler = _event_handlers.get(event_type)
    try:
        if handler:
            await handler(event["data"]["object"], event)
        repository.mark_webhook_processed(event_id)
    except Exception as exc:
        repository.mark_webhook_failed(event_id, str(exc))
        logger.exception("Webhook handler failed for %s", event_type)
        raise HTTPException(status_code=500, detail=f"Handler error: {exc}")

    return {"status": "ok", "event_id": event_id, "event_type": event_type}


@on_event("checkout.session.completed")
async def handle_checkout_completed(data: Dict[str, Any], event: Dict[str, Any]) -> None:
    contract = repository.record_checkout_session(data)
    metadata = data.get("metadata") or {}
    if contract and data.get("subscription"):
        tenant_id = metadata.get("tenant_id")
        if tenant_id:
            from shared.usage import repository as usage_repository

            usage_repository.ensure_usage_account(
                tenant_id=tenant_id,
                service_key=usage_repository.GLOBAL_CREDIT_SERVICE_KEY,
                subscription_contract_id=contract["subscription_contract_id"],
            )

    if metadata.get("checkout_mode") == "payment":
        try:
            credit_grant_amount = int(metadata.get("credit_grant_amount") or 0)
        except (TypeError, ValueError):
            credit_grant_amount = 0
        tenant_id = metadata.get("tenant_id")
        if tenant_id and credit_grant_amount > 0:
            from shared.usage import repository as usage_repository

            usage_repository.grant_bonus_credits(
                tenant_id=tenant_id,
                service_key=usage_repository.GLOBAL_CREDIT_SERVICE_KEY,
                units=credit_grant_amount,
                actor_user_id=metadata.get("user_id") or metadata.get("user_email") or "stripe-webhook",
                reason="stripe_addon_credit_purchase",
                idempotency_key=f"stripe-checkout-credit:{data.get('id')}",
                metadata={
                    "stripe_checkout_session_id": data.get("id"),
                    "stripe_customer_id": data.get("customer"),
                    "stripe_payment_intent_id": data.get("payment_intent"),
                    "plan_id": metadata.get("plan_id"),
                    "user_email": metadata.get("user_email"),
                },
            )


@on_event("customer.subscription.created")
async def handle_subscription_created(data: Dict[str, Any], event: Dict[str, Any]) -> None:
    metadata = _subscription_metadata(data)
    tenant_id = metadata.get("tenant_id")
    if not tenant_id:
        customer = repository.get_customer_account_by_stripe_customer(data.get("customer", ""))
        tenant_id = customer["tenant_id"] if customer else ""
    if not tenant_id:
        return
    repository.upsert_subscription_contract(
        tenant_id=tenant_id,
        plan_id=metadata.get("plan_id"),
        stripe_customer_id=data.get("customer", ""),
        stripe_subscription_id=data.get("id", ""),
        stripe_checkout_session_id=metadata.get("checkout_session_id"),
        contract_status=data.get("status", "active"),
        metadata=metadata,
    )
    from shared.usage import repository as usage_repository

    usage_repository.ensure_usage_account(
        tenant_id=tenant_id,
        service_key=usage_repository.GLOBAL_CREDIT_SERVICE_KEY,
    )


@on_event("customer.subscription.updated")
async def handle_subscription_updated(data: Dict[str, Any], event: Dict[str, Any]) -> None:
    await handle_subscription_created(data, event)


@on_event("customer.subscription.deleted")
async def handle_subscription_deleted(data: Dict[str, Any], event: Dict[str, Any]) -> None:
    contract = repository._fetchone(
        """
        SELECT ca.tenant_id
        FROM subscription_contract sc
        JOIN customer_account ca ON ca.customer_account_id = sc.customer_account_id
        WHERE sc.stripe_subscription_id = %s
        """,
        (data.get("id", ""),),
    )
    repository._execute(
        """
        UPDATE subscription_contract
        SET contract_status = 'cancelled', cancelled_at = now(), updated_at = now()
        WHERE stripe_subscription_id = %s
        """,
        (data.get("id", ""),),
    )
    if contract and contract.get("tenant_id"):
        from shared.usage import repository as usage_repository

        usage_repository.ensure_usage_account(
            tenant_id=str(contract["tenant_id"]),
            service_key=usage_repository.GLOBAL_CREDIT_SERVICE_KEY,
        )


@on_event("invoice.paid")
async def handle_invoice_paid(data: Dict[str, Any], event: Dict[str, Any]) -> None:
    repository.record_billing_from_invoice(data, event_id=event.get("id", ""))
    repository.create_or_update_payout_ledger_from_invoice(data, event_id=event.get("id", ""))


@on_event("invoice.payment_succeeded")
async def handle_invoice_payment_succeeded(data: Dict[str, Any], event: Dict[str, Any]) -> None:
    await handle_invoice_paid(data, event)


@on_event("invoice.payment_failed")
async def handle_invoice_failed(data: Dict[str, Any], event: Dict[str, Any]) -> None:
    repository.mark_invoice_failed(data, event_id=event.get("id", ""))


@on_event("payment_intent.succeeded")
async def handle_payment_intent_succeeded(data: Dict[str, Any], event: Dict[str, Any]) -> None:
    repository._execute(
        """
        UPDATE payment_receipt_ledger prl
        SET receipt_status = 'settled',
            funds_status = 'available',
            available_for_payout_at = now(),
            settled_at = now(),
            updated_at = now()
        FROM billing_event_ledger bel
        WHERE bel.billing_event_ledger_id = prl.billing_event_ledger_id
          AND bel.stripe_payment_intent_id = %s
        """,
        (data.get("id", ""),),
    )


@on_event("payment_intent.payment_failed")
async def handle_payment_intent_failed(data: Dict[str, Any], event: Dict[str, Any]) -> None:
    logger.warning("Payment intent failed for %s", data.get("id", ""))


@on_event("charge.refunded")
async def handle_charge_refunded(data: Dict[str, Any], event: Dict[str, Any]) -> None:
    repository.record_refund_adjustment(data, event_id=event.get("id", ""), adjustment_type="refund")


@on_event("charge.dispute.created")
async def handle_charge_dispute_created(data: Dict[str, Any], event: Dict[str, Any]) -> None:
    charge = {"id": data.get("charge"), "invoice": data.get("invoice"), "amount": data.get("amount"), "currency": data.get("currency", "jpy")}
    repository.record_refund_adjustment(charge, event_id=event.get("id", ""), adjustment_type="chargeback")
