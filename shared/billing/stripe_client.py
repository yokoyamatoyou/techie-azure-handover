# -*- coding: utf-8 -*-
"""Stripe Phase 2 client helpers."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

def _get_stripe():
    import stripe

    stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe_secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    stripe.api_key = stripe_secret_key
    return stripe


def _get_connect_account_type() -> str:
    return os.environ.get("STRIPE_CONNECT_ACCOUNT_TYPE", "express")


def _get_publishable_key() -> str:
    return os.environ.get("STRIPE_PUBLISHABLE_KEY", "")


def _get_webhook_secret() -> str:
    return os.environ.get("STRIPE_WEBHOOK_SECRET", "")


def _get_stripe_config() -> Dict[str, str]:
    return {
        "publishable_key": _get_publishable_key(),
        "webhook_secret": _get_webhook_secret(),
    }



def create_customer(email: str, name: str, tenant_id: str, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    stripe = _get_stripe()
    meta = {"tenant_id": tenant_id}
    if metadata:
        meta.update({key: str(value) for key, value in metadata.items() if value is not None})
    customer = stripe.Customer.create(email=email, name=name, metadata=meta)
    return {"customer_id": customer.id, "email": email}


def create_checkout_session(
    *,
    customer_id: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
    metadata: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    stripe = _get_stripe()
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata or {},
        allow_promotion_codes=True,
    )
    return {"session_id": session.id, "url": session.url}


def create_customer_portal_session(*, customer_id: str, return_url: str) -> Dict[str, Any]:
    stripe = _get_stripe()
    session = stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)
    return {"url": session.url}


def create_subscription(customer_id: str, price_id: str) -> Dict[str, Any]:
    stripe = _get_stripe()
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id}],
        payment_behavior="default_incomplete",
        expand=["latest_invoice.payment_intent"],
    )
    return {
        "subscription_id": subscription.id,
        "status": subscription.status,
        "client_secret": (
            subscription.latest_invoice.payment_intent.client_secret
            if subscription.latest_invoice and subscription.latest_invoice.payment_intent
            else None
        ),
    }


def cancel_subscription(subscription_id: str) -> Dict[str, Any]:
    stripe = _get_stripe()
    subscription = stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
    return {"subscription_id": subscription.id, "cancel_at_period_end": True}


def get_subscription_status(subscription_id: str) -> Dict[str, Any]:
    stripe = _get_stripe()
    sub = stripe.Subscription.retrieve(subscription_id)
    return {
        "subscription_id": sub.id,
        "status": sub.status,
        "current_period_end": sub.current_period_end,
        "cancel_at_period_end": sub.cancel_at_period_end,
    }


def report_usage(subscription_item_id: str, quantity: int, timestamp: Optional[int] = None) -> Dict[str, Any]:
    stripe = _get_stripe()
    import time

    record = stripe.SubscriptionItem.create_usage_record(
        subscription_item_id,
        quantity=quantity,
        timestamp=timestamp or int(time.time()),
        action="increment",
    )
    return {"usage_record_id": record.id, "quantity": quantity}


def create_connect_account(*, email: str, business_name: str, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    stripe = _get_stripe()
    account = stripe.Account.create(
        type=_get_connect_account_type(),
        email=email or None,
        business_type="company",
        company={"name": business_name},
        capabilities={"transfers": {"requested": True}},
        metadata=metadata or {},
    )
    return {"account_id": account.id, "type": account.type}


def create_connect_onboarding_link(*, account_id: str, refresh_url: str, return_url: str) -> Dict[str, Any]:
    stripe = _get_stripe()
    link = stripe.AccountLink.create(
        account=account_id,
        refresh_url=refresh_url,
        return_url=return_url,
        type="account_onboarding",
    )
    return {"url": link.url, "expires_at": link.expires_at}


def create_coupon_and_promotion_code(
    *,
    coupon_kind: str,
    percent_off: Optional[float],
    amount_off: Optional[float],
    currency: str,
    duration_kind: str,
    duration_months: Optional[int],
    code_prefix: str,
) -> Dict[str, Any]:
    stripe = _get_stripe()
    coupon_payload: Dict[str, Any] = {"duration": duration_kind}
    if duration_kind == "repeating":
        coupon_payload["duration_in_months"] = duration_months or 1
    if coupon_kind == "percent_off":
        coupon_payload["percent_off"] = percent_off
    else:
        coupon_payload["amount_off"] = int((amount_off or 0) * 100)
        coupon_payload["currency"] = currency
    coupon = stripe.Coupon.create(**coupon_payload)
    promotion_code = stripe.PromotionCode.create(coupon=coupon.id, code=f"{code_prefix}-{coupon.id[-6:]}".upper())
    return {"coupon_id": coupon.id, "promotion_code_id": promotion_code.id, "promotion_code": promotion_code.code}


def create_transfer(
    *,
    connected_account_id: str,
    amount: float,
    currency: str,
    transfer_group: str,
    metadata: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    stripe = _get_stripe()
    transfer = stripe.Transfer.create(
        amount=int(amount * 100),
        currency=currency,
        destination=connected_account_id,
        transfer_group=transfer_group,
        metadata=metadata or {},
    )
    return {"transfer_id": transfer.id, "amount": amount, "currency": currency, "destination": connected_account_id}
