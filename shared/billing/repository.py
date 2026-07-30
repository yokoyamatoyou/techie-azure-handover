# -*- coding: utf-8 -*-
"""Phase 2 billing/re reseller repository helpers."""
from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Sequence

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

DATABASE_URL = os.environ.get("DATABASE_URL", "")
_POOL: Optional[ThreadedConnectionPool] = None


def _get_pool() -> ThreadedConnectionPool:
    global _POOL
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    if _POOL is None:
        _POOL = ThreadedConnectionPool(
            minconn=1,
            maxconn=int(os.environ.get("PHASE2_DB_POOL_SIZE", "10")),
            dsn=DATABASE_URL,
        )
    return _POOL


@contextmanager
def get_conn():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


@contextmanager
def get_cursor(*, tenant_id: Optional[str] = None):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            if tenant_id:
                cursor.execute("SELECT set_config('app.current_tenant', %s, false)", (tenant_id,))
            yield cursor


def _fetchone(query: str, params: Sequence[Any] = (), *, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_cursor(tenant_id=tenant_id) as cursor:
        cursor.execute(query, params)
        row = cursor.fetchone()
    return dict(row) if row else None


def _fetchall(query: str, params: Sequence[Any] = (), *, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_cursor(tenant_id=tenant_id) as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def _execute(query: str, params: Sequence[Any] = (), *, tenant_id: Optional[str] = None) -> None:
    with get_cursor(tenant_id=tenant_id) as cursor:
        cursor.execute(query, params)


def _execute_returning(query: str, params: Sequence[Any] = (), *, tenant_id: Optional[str] = None) -> Dict[str, Any]:
    with get_cursor(tenant_id=tenant_id) as cursor:
        cursor.execute(query, params)
        row = cursor.fetchone()
    if not row:
        raise RuntimeError("Expected a row to be returned")
    return dict(row)


def get_effective_roles(principal_id: str, email: str = "") -> List[str]:
    rows = _fetchall(
        """
        SELECT role_code
        FROM principal_role_assignment
        WHERE is_active = TRUE
          AND effective_to IS NULL
          AND principal_id IN (%s, %s)
        """,
        (principal_id, email or principal_id),
    )
    return sorted({row["role_code"] for row in rows})


def ensure_tenant(tenant_id: str, company_name: str) -> Dict[str, Any]:
    return _execute_returning(
        """
        INSERT INTO tenants (tenant_id, company_name, updated_at)
        VALUES (%s::uuid, %s, now())
        ON CONFLICT (tenant_id) DO UPDATE
            SET company_name = COALESCE(NULLIF(EXCLUDED.company_name, ''), tenants.company_name),
                updated_at = now()
        RETURNING tenant_id, company_name, plan_status
        """,
        (tenant_id, company_name),
    )


def ensure_customer_account(
    *,
    tenant_id: str,
    legal_name: str,
    display_name: str,
    billing_email: str,
    stripe_customer_id: Optional[str] = None,
) -> Dict[str, Any]:
    ensure_tenant(tenant_id, legal_name or display_name or billing_email or tenant_id)
    return _execute_returning(
        """
        INSERT INTO customer_account (
            tenant_id, legal_name, display_name, billing_email, stripe_customer_id, status
        )
        VALUES (%s::uuid, %s, %s, %s, %s, 'active')
        ON CONFLICT (tenant_id) DO UPDATE
            SET legal_name = COALESCE(NULLIF(EXCLUDED.legal_name, ''), customer_account.legal_name),
                display_name = COALESCE(NULLIF(EXCLUDED.display_name, ''), customer_account.display_name),
                billing_email = COALESCE(NULLIF(EXCLUDED.billing_email, ''), customer_account.billing_email),
                stripe_customer_id = COALESCE(EXCLUDED.stripe_customer_id, customer_account.stripe_customer_id),
                status = 'active',
                updated_at = now()
        RETURNING customer_account_id, tenant_id, stripe_customer_id, display_name, billing_email
        """,
        (tenant_id, legal_name, display_name, billing_email, stripe_customer_id),
    )


def get_customer_account_by_tenant(tenant_id: str) -> Optional[Dict[str, Any]]:
    return _fetchone(
        """
        SELECT customer_account_id, tenant_id, stripe_customer_id, display_name, billing_email
        FROM customer_account
        WHERE tenant_id = %s::uuid
        """,
        (tenant_id,),
    )


def get_customer_account_by_stripe_customer(stripe_customer_id: str) -> Optional[Dict[str, Any]]:
    return _fetchone(
        """
        SELECT customer_account_id, tenant_id, stripe_customer_id, display_name, billing_email
        FROM customer_account
        WHERE stripe_customer_id = %s
        """,
        (stripe_customer_id,),
    )


def ensure_default_plan() -> str:
    plan = _fetchone("SELECT plan_id FROM plan_master WHERE plan_code = 'default-plan'")
    if plan:
        return plan["plan_id"]
    _execute(
        """
        INSERT INTO plan_master (plan_code, plan_name, status)
        VALUES ('default-plan', 'Default plan', 'active')
        ON CONFLICT (plan_code) DO NOTHING
        """
    )
    plan = _fetchone("SELECT plan_id FROM plan_master WHERE plan_code = 'default-plan'")
    if not plan:
        raise RuntimeError("Could not ensure default plan")
    return plan["plan_id"]


def _plan_definitions() -> Dict[str, Dict[str, Any]]:
    return {
        "entry": {
            "plan_name": "TECHIE Entry",
            "stripe_price_id": os.environ.get("STRIPE_ENTRY_PRICE_ID", ""),
            "list_price_amount": 9000,
            "included_credits": int(os.environ.get("TECHIE_ENTRY_INCLUDED_CREDITS", "15")),
        },
        "standard": {
            "plan_name": "TECHIE Standard",
            "stripe_price_id": os.environ.get("STRIPE_STANDARD_PRICE_ID", ""),
            "list_price_amount": 18000,
            "included_credits": int(os.environ.get("TECHIE_STANDARD_INCLUDED_CREDITS", "30")),
        },
        "pro": {
            "plan_name": "TECHIE Pro",
            "stripe_price_id": os.environ.get("STRIPE_PRO_PRICE_ID", ""),
            "list_price_amount": 49800,
            "included_credits": int(os.environ.get("TECHIE_PRO_INCLUDED_CREDITS", "100")),
        },
    }


def resolve_plan_id(plan_identifier: Optional[str]) -> str:
    """Accept either a DB UUID or the public Hub plan key."""
    if not plan_identifier:
        return ensure_default_plan()

    try:
        uuid.UUID(str(plan_identifier))
        return str(plan_identifier)
    except (TypeError, ValueError):
        pass

    plan_code = str(plan_identifier).strip().lower()
    definitions = _plan_definitions()
    definition = definitions.get(plan_code)
    if not definition:
        return ensure_default_plan()

    return _execute_returning(
        """
        INSERT INTO plan_master (
            plan_code, plan_name, stripe_price_id, billing_interval,
            currency, list_price_amount, status, metadata, updated_at
        )
        VALUES (%s, %s, NULLIF(%s, ''), 'month', 'jpy', %s, 'active', %s::jsonb, now())
        ON CONFLICT (plan_code) DO UPDATE
            SET plan_name = EXCLUDED.plan_name,
                stripe_price_id = COALESCE(EXCLUDED.stripe_price_id, plan_master.stripe_price_id),
                list_price_amount = EXCLUDED.list_price_amount,
                status = 'active',
                metadata = EXCLUDED.metadata,
                updated_at = now()
        RETURNING plan_id
        """,
        (
            plan_code,
            definition["plan_name"],
            definition["stripe_price_id"],
            definition["list_price_amount"],
            psycopg2.extras.Json({"included_credits": definition["included_credits"], "plan_key": plan_code}),
        ),
    )["plan_id"]


def upsert_subscription_contract(
    *,
    tenant_id: str,
    plan_id: Optional[str],
    stripe_customer_id: str,
    stripe_subscription_id: str,
    stripe_checkout_session_id: Optional[str],
    contract_status: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    account = get_customer_account_by_tenant(tenant_id)
    if not account:
        raise RuntimeError(f"Customer account not found for tenant {tenant_id}")
    plan_id = resolve_plan_id(plan_id)
    return _execute_returning(
        """
        INSERT INTO subscription_contract (
            customer_account_id, plan_id, stripe_customer_id, stripe_subscription_id,
            stripe_checkout_session_id, contract_status, metadata, created_at, updated_at
        )
        VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s::jsonb, now(), now())
        ON CONFLICT (stripe_subscription_id) DO UPDATE
            SET stripe_customer_id = EXCLUDED.stripe_customer_id,
                stripe_checkout_session_id = COALESCE(EXCLUDED.stripe_checkout_session_id, subscription_contract.stripe_checkout_session_id),
                contract_status = EXCLUDED.contract_status,
                metadata = COALESCE(EXCLUDED.metadata, subscription_contract.metadata),
                updated_at = now()
        RETURNING subscription_contract_id, customer_account_id, reseller_id, plan_id, stripe_subscription_id, contract_status
        """,
        (
            account["customer_account_id"],
            plan_id,
            stripe_customer_id,
            stripe_subscription_id,
            stripe_checkout_session_id,
            contract_status,
            psycopg2.extras.Json(metadata or {}),
        ),
    )


def get_subscription_contract_by_stripe_subscription(stripe_subscription_id: str) -> Optional[Dict[str, Any]]:
    return _fetchone(
        """
        SELECT subscription_contract_id, customer_account_id, reseller_id, plan_id, stripe_subscription_id, contract_status
        FROM subscription_contract
        WHERE stripe_subscription_id = %s
        """,
        (stripe_subscription_id,),
    )


def log_webhook_event(
    *,
    stripe_event_id: str,
    event_type: str,
    payload: Dict[str, Any],
    signature_verified: bool,
    queue_name: str = "",
) -> Dict[str, Any]:
    return _execute_returning(
        """
        INSERT INTO webhook_event_log (
            provider, stripe_event_id, event_type, signature_verified,
            receive_status, processing_status, queue_name, payload, received_at, created_at
        )
        VALUES ('stripe', %s, %s, %s, 'received', 'processing', %s, %s::jsonb, now(), now())
        ON CONFLICT (provider, stripe_event_id) WHERE stripe_event_id IS NOT NULL DO UPDATE
            SET processing_attempts = webhook_event_log.processing_attempts + 1,
                processing_status = 'processing',
                queue_name = EXCLUDED.queue_name
        RETURNING webhook_event_log_id, processing_status, processing_attempts
        """,
        (stripe_event_id, event_type, signature_verified, queue_name, psycopg2.extras.Json(payload)),
    )


def get_webhook_event(stripe_event_id: str) -> Optional[Dict[str, Any]]:
    return _fetchone(
        """
        SELECT webhook_event_log_id, processing_status, processing_attempts
        FROM webhook_event_log
        WHERE provider = 'stripe' AND stripe_event_id = %s
        """,
        (stripe_event_id,),
    )


def mark_webhook_processed(stripe_event_id: str, status: str = "processed") -> None:
    _execute(
        """
        UPDATE webhook_event_log
        SET processing_status = %s, receive_status = 'received'
        WHERE provider = 'stripe' AND stripe_event_id = %s
        """,
        (status, stripe_event_id),
    )


def mark_webhook_failed(stripe_event_id: str, error_message: str) -> None:
    _execute(
        """
        UPDATE webhook_event_log
        SET processing_status = 'failed',
            next_retry_at = now() + interval '5 minutes',
            payload = COALESCE(payload, '{}'::jsonb) || jsonb_build_object('last_error', %s)
        WHERE provider = 'stripe' AND stripe_event_id = %s
        """,
        (error_message, stripe_event_id),
    )


def record_checkout_session(session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    metadata = session.get("metadata") or {}
    tenant_id = metadata.get("tenant_id")
    if not tenant_id:
        return None
    ensure_customer_account(
        tenant_id=tenant_id,
        legal_name=metadata.get("company_name") or metadata.get("display_name") or session.get("customer_email") or tenant_id,
        display_name=metadata.get("display_name") or metadata.get("company_name") or session.get("customer_email") or tenant_id,
        billing_email=session.get("customer_email") or "",
        stripe_customer_id=session.get("customer"),
    )
    if session.get("subscription"):
        return upsert_subscription_contract(
            tenant_id=tenant_id,
            plan_id=metadata.get("plan_id"),
            stripe_customer_id=session.get("customer") or "",
            stripe_subscription_id=session.get("subscription"),
            stripe_checkout_session_id=session.get("id"),
            contract_status="checkout_completed",
            metadata=metadata,
        )
    return None


def record_billing_from_invoice(invoice: Dict[str, Any], *, event_id: str) -> Dict[str, Any]:
    stripe_customer_id = invoice.get("customer")
    account = get_customer_account_by_stripe_customer(stripe_customer_id)
    if not account:
        metadata = invoice.get("lines", {}).get("data", [{}])[0].get("metadata", {}) if invoice.get("lines") else {}
        tenant_id = metadata.get("tenant_id") or str(uuid.uuid4())
        account = ensure_customer_account(
            tenant_id=tenant_id,
            legal_name=metadata.get("company_name") or invoice.get("customer_email") or tenant_id,
            display_name=metadata.get("display_name") or metadata.get("company_name") or invoice.get("customer_email") or tenant_id,
            billing_email=invoice.get("customer_email") or "",
            stripe_customer_id=stripe_customer_id,
        )
    contract = None
    if invoice.get("subscription"):
        contract = get_subscription_contract_by_stripe_subscription(invoice["subscription"])
    billing = _execute_returning(
        """
        INSERT INTO billing_event_ledger (
            customer_account_id, subscription_contract_id, tenant_id, event_source, external_event_id, event_type,
            stripe_invoice_id, stripe_payment_intent_id, amount_subtotal, amount_discount, amount_tax, amount_total,
            currency, billing_status, event_occurred_at, raw_payload, created_at
        )
        VALUES (
            %s::uuid, %s::uuid, %s::uuid, 'stripe', %s, 'invoice.paid',
            %s, %s, %s, %s, %s, %s, %s, 'paid', now(), %s::jsonb, now()
        )
        ON CONFLICT (event_source, external_event_id) DO UPDATE
            SET billing_status = 'paid',
                raw_payload = EXCLUDED.raw_payload
        RETURNING billing_event_ledger_id, customer_account_id, tenant_id
        """,
        (
            account["customer_account_id"],
            contract["subscription_contract_id"] if contract else None,
            account["tenant_id"],
            event_id,
            invoice.get("id"),
            invoice.get("payment_intent"),
            (invoice.get("subtotal") or 0) / 100.0,
            ((invoice.get("total_discount_amounts") or [{}])[0].get("amount", 0) if invoice.get("total_discount_amounts") else 0) / 100.0,
            (invoice.get("tax") or 0) / 100.0,
            (invoice.get("amount_paid") or 0) / 100.0,
            invoice.get("currency", "jpy"),
            psycopg2.extras.Json(invoice),
        ),
    )
    _execute(
        """
        INSERT INTO payment_receipt_ledger (
            billing_event_ledger_id, customer_account_id, tenant_id, receipt_status, funds_status,
            received_amount, fee_amount, net_amount, currency, available_for_payout_at, settled_at, created_at, updated_at
        )
        VALUES (%s::uuid, %s::uuid, %s::uuid, 'settled', 'available', %s, 0, %s, %s, now(), now(), now(), now())
        ON CONFLICT (billing_event_ledger_id) DO UPDATE
            SET receipt_status = 'settled',
                funds_status = 'available',
                received_amount = EXCLUDED.received_amount,
                net_amount = EXCLUDED.net_amount,
                available_for_payout_at = now(),
                settled_at = now(),
                updated_at = now()
        """,
        (
            billing["billing_event_ledger_id"],
            billing["customer_account_id"],
            billing["tenant_id"],
            (invoice.get("amount_paid") or 0) / 100.0,
            (invoice.get("amount_paid") or 0) / 100.0,
            invoice.get("currency", "jpy"),
        ),
    )
    return billing


def create_or_update_payout_ledger_from_invoice(invoice: Dict[str, Any], *, event_id: str) -> Optional[Dict[str, Any]]:
    if not invoice.get("subscription"):
        return None
    contract = get_subscription_contract_by_stripe_subscription(invoice["subscription"])
    if not contract or not contract.get("reseller_id"):
        return None
    billing = record_billing_from_invoice(invoice, event_id=event_id)
    receipt = _fetchone(
        """
        SELECT payment_receipt_ledger_id, net_amount, currency
        FROM payment_receipt_ledger
        WHERE billing_event_ledger_id = %s::uuid
        """,
        (billing["billing_event_ledger_id"],),
    )
    payout_rule = _fetchone(
        """
        SELECT reseller_payout_rule_id, rule_type, revenue_share_percent, fixed_share_amount
        FROM reseller_payout_rule
        WHERE plan_id = %s::uuid
          AND (reseller_id = %s::uuid OR reseller_id IS NULL)
          AND status = 'active'
          AND effective_to IS NULL
        ORDER BY reseller_id NULLS LAST, effective_from DESC
        LIMIT 1
        """,
        (contract["plan_id"], contract["reseller_id"]),
    )
    if not receipt or not payout_rule:
        return None
    payout_amount = float(payout_rule["fixed_share_amount"] or 0) if payout_rule["rule_type"] == "fixed" else float(receipt["net_amount"] or 0) * float(payout_rule["revenue_share_percent"] or 0) / 100.0
    return _execute_returning(
        """
        INSERT INTO reseller_payout_ledger (
            payment_receipt_ledger_id, billing_event_ledger_id, subscription_contract_id, reseller_id, reseller_payout_rule_id,
            gross_amount, net_bill_amount, payout_basis_amount, payout_amount, payout_currency,
            payout_status, hold_status, eligible_at, created_at, updated_at
        )
        VALUES (
            %s::uuid, %s::uuid, %s::uuid, %s::uuid, %s::uuid,
            %s, %s, %s, %s, %s, 'pending', 'ready', now(), now(), now()
        )
        RETURNING reseller_payout_ledger_id, payout_amount, payout_status
        """,
        (
            receipt["payment_receipt_ledger_id"],
            billing["billing_event_ledger_id"],
            contract["subscription_contract_id"],
            contract["reseller_id"],
            payout_rule["reseller_payout_rule_id"],
            receipt["net_amount"],
            receipt["net_amount"],
            receipt["net_amount"],
            payout_amount,
            receipt["currency"],
        ),
    )


def mark_invoice_failed(invoice: Dict[str, Any], *, event_id: str) -> None:
    stripe_customer_id = invoice.get("customer")
    account = get_customer_account_by_stripe_customer(stripe_customer_id)
    if not account:
        return
    _execute(
        """
        INSERT INTO billing_event_ledger (
            customer_account_id, tenant_id, event_source, external_event_id, event_type, stripe_invoice_id,
            stripe_payment_intent_id, amount_total, currency, billing_status, event_occurred_at, raw_payload, created_at
        )
        VALUES (%s::uuid, %s::uuid, 'stripe', %s, 'invoice.payment_failed', %s, %s, %s, %s, 'failed', now(), %s::jsonb, now())
        ON CONFLICT (event_source, external_event_id) DO UPDATE
            SET billing_status = 'failed',
                raw_payload = EXCLUDED.raw_payload
        """,
        (
            account["customer_account_id"],
            account["tenant_id"],
            event_id,
            invoice.get("id"),
            invoice.get("payment_intent"),
            (invoice.get("amount_due") or 0) / 100.0,
            invoice.get("currency", "jpy"),
            psycopg2.extras.Json(invoice),
        ),
    )


def record_refund_adjustment(charge: Dict[str, Any], *, event_id: str, adjustment_type: str) -> Optional[Dict[str, Any]]:
    invoice_id = charge.get("invoice")
    billing = _fetchone(
        """
        SELECT billing_event_ledger_id, customer_account_id
        FROM billing_event_ledger
        WHERE stripe_invoice_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (invoice_id,),
    )
    if not billing:
        return None
    payout = _fetchone(
        """
        SELECT reseller_payout_ledger_id
        FROM reseller_payout_ledger
        WHERE billing_event_ledger_id = %s::uuid
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (billing["billing_event_ledger_id"],),
    )
    return _execute_returning(
        """
        INSERT INTO refund_adjustment_ledger (
            reseller_payout_ledger_id, billing_event_ledger_id, customer_account_id,
            external_adjustment_id, adjustment_type, adjustment_status,
            gross_adjustment_amount, reseller_adjustment_amount, currency, occurred_at, notes, created_at
        )
        VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, 'open', %s, %s, %s, now(), %s, now())
        ON CONFLICT (adjustment_type, external_adjustment_id) DO UPDATE
            SET adjustment_status = 'open',
                notes = EXCLUDED.notes
        RETURNING refund_adjustment_ledger_id, adjustment_type, adjustment_status
        """,
        (
            payout["reseller_payout_ledger_id"] if payout else None,
            billing["billing_event_ledger_id"],
            billing["customer_account_id"],
            charge.get("id") or event_id,
            adjustment_type,
            (charge.get("amount_refunded") or charge.get("amount") or 0) / 100.0,
            (charge.get("amount_refunded") or charge.get("amount") or 0) / 100.0,
            charge.get("currency", "jpy"),
            adjustment_type,
        ),
    )


def create_or_update_reseller(
    *,
    reseller_code: str,
    legal_name: str,
    display_name: str,
    tenant_id: Optional[str] = None,
    stripe_connect_account_id: Optional[str] = None,
) -> Dict[str, Any]:
    if tenant_id:
        ensure_tenant(tenant_id, legal_name)
    return _execute_returning(
        """
        INSERT INTO reseller_master (
            tenant_id, reseller_code, legal_name, display_name, stripe_connect_account_id, status, created_at, updated_at
        )
        VALUES (%s::uuid, %s, %s, %s, %s, 'active', now(), now())
        ON CONFLICT (reseller_code) DO UPDATE
            SET legal_name = EXCLUDED.legal_name,
                display_name = EXCLUDED.display_name,
                tenant_id = COALESCE(EXCLUDED.tenant_id, reseller_master.tenant_id),
                stripe_connect_account_id = COALESCE(EXCLUDED.stripe_connect_account_id, reseller_master.stripe_connect_account_id),
                status = 'active',
                updated_at = now()
        RETURNING reseller_id, tenant_id, reseller_code, legal_name, display_name, stripe_connect_account_id, status
        """,
        (tenant_id, reseller_code, legal_name, display_name, stripe_connect_account_id),
    )


def get_reseller(reseller_id: str) -> Optional[Dict[str, Any]]:
    return _fetchone(
        """
        SELECT reseller_id, tenant_id, reseller_code, legal_name, display_name, stripe_connect_account_id, status
        FROM reseller_master
        WHERE reseller_id = %s::uuid
        """,
        (reseller_id,),
    )


def list_reseller_customers(principal_id: str, email: str = "") -> List[Dict[str, Any]]:
    return _fetchall(
        """
        SELECT ca.customer_account_id, ca.display_name, ca.billing_email, sc.contract_status, sc.stripe_subscription_id
        FROM principal_role_assignment pra
        JOIN reseller_master rm ON rm.reseller_id = pra.reseller_id
        JOIN customer_reseller_assignment cra ON cra.reseller_id = rm.reseller_id AND cra.effective_to IS NULL
        JOIN customer_account ca ON ca.customer_account_id = cra.customer_account_id
        LEFT JOIN subscription_contract sc ON sc.customer_account_id = ca.customer_account_id
        WHERE pra.is_active = TRUE
          AND pra.role_code = 'reseller'
          AND pra.principal_id IN (%s, %s)
        ORDER BY ca.created_at DESC
        """,
        (principal_id, email or principal_id),
    )


def get_reseller_customer_detail(customer_account_id: str, principal_id: str, email: str = "") -> Optional[Dict[str, Any]]:
    return _fetchone(
        """
        SELECT ca.customer_account_id, ca.display_name, ca.billing_email, ca.stripe_customer_id,
               sc.subscription_contract_id, sc.contract_status, sc.stripe_subscription_id, sc.metadata
        FROM principal_role_assignment pra
        JOIN reseller_master rm ON rm.reseller_id = pra.reseller_id
        JOIN customer_reseller_assignment cra ON cra.reseller_id = rm.reseller_id AND cra.effective_to IS NULL
        JOIN customer_account ca ON ca.customer_account_id = cra.customer_account_id
        LEFT JOIN subscription_contract sc ON sc.customer_account_id = ca.customer_account_id
        WHERE pra.is_active = TRUE
          AND pra.role_code = 'reseller'
          AND pra.principal_id IN (%s, %s)
          AND ca.customer_account_id = %s::uuid
        """,
        (principal_id, email or principal_id, customer_account_id),
    )


def list_reseller_payouts(principal_id: str, email: str = "") -> List[Dict[str, Any]]:
    return _fetchall(
        """
        SELECT rpl.reseller_payout_ledger_id, rpl.payout_amount, rpl.payout_currency, rpl.payout_status,
               rpl.hold_status, rpl.eligible_at, ca.display_name
        FROM principal_role_assignment pra
        JOIN reseller_master rm ON rm.reseller_id = pra.reseller_id
        JOIN reseller_payout_ledger rpl ON rpl.reseller_id = rm.reseller_id
        LEFT JOIN billing_event_ledger bel ON bel.billing_event_ledger_id = rpl.billing_event_ledger_id
        LEFT JOIN customer_account ca ON ca.customer_account_id = bel.customer_account_id
        WHERE pra.is_active = TRUE
          AND pra.role_code = 'reseller'
          AND pra.principal_id IN (%s, %s)
        ORDER BY rpl.created_at DESC
        """,
        (principal_id, email or principal_id),
    )


def create_coupon_request(
    *,
    reseller_id: Optional[str],
    customer_account_id: Optional[str],
    plan_id: Optional[str],
    requested_by_principal: str,
    request_scope: str,
    requested_coupon_kind: str,
    request_reason: str,
    requested_percent_off: Optional[float] = None,
    requested_amount_off: Optional[float] = None,
    requested_duration_kind: Optional[str] = None,
    requested_duration_months: Optional[int] = None,
) -> Dict[str, Any]:
    return _execute_returning(
        """
        INSERT INTO coupon_request (
            reseller_id, customer_account_id, plan_id, requested_by_principal, request_scope, request_status,
            requested_coupon_kind, requested_percent_off, requested_amount_off, requested_duration_kind,
            requested_duration_months, request_reason, created_at, updated_at
        )
        VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, 'submitted', %s, %s, %s, %s, %s, %s, now(), now())
        RETURNING coupon_request_id, request_status, requested_coupon_kind, request_reason
        """,
        (
            reseller_id,
            customer_account_id,
            plan_id,
            requested_by_principal,
            request_scope,
            requested_coupon_kind,
            requested_percent_off,
            requested_amount_off,
            requested_duration_kind,
            requested_duration_months,
            request_reason,
        ),
    )


def list_coupon_requests() -> List[Dict[str, Any]]:
    return _fetchall(
        """
        SELECT coupon_request_id, request_status, requested_coupon_kind, request_reason, requested_by_principal, created_at
        FROM coupon_request
        ORDER BY created_at DESC
        """
    )


def get_coupon_request(coupon_request_id: str) -> Optional[Dict[str, Any]]:
    return _fetchone("SELECT * FROM coupon_request WHERE coupon_request_id = %s::uuid", (coupon_request_id,))


def record_coupon_approval(coupon_request_id: str, approver_principal: str, decision: str, note: str = "") -> Dict[str, Any]:
    approval = _execute_returning(
        """
        INSERT INTO coupon_request_approval (
            coupon_request_id, approval_step, approver_principal, decision, decision_note, decided_at, created_at
        )
        VALUES (%s::uuid, 1, %s, %s, %s, now(), now())
        ON CONFLICT (coupon_request_id, approval_step) DO UPDATE
            SET approver_principal = EXCLUDED.approver_principal,
                decision = EXCLUDED.decision,
                decision_note = EXCLUDED.decision_note,
                decided_at = now()
        RETURNING coupon_request_approval_id, decision
        """,
        (coupon_request_id, approver_principal, decision, note),
    )
    _execute(
        "UPDATE coupon_request SET request_status = %s, updated_at = now() WHERE coupon_request_id = %s::uuid",
        ("approved" if decision == "approved" else "rejected", coupon_request_id),
    )
    return approval


def create_discount_grant(
    *,
    coupon_request_id: str,
    approved_by_principal: str,
    stripe_coupon_id: str,
    stripe_promotion_code_id: Optional[str],
    target_scope: str,
    discount_kind: str,
    percent_off: Optional[float],
    amount_off: Optional[float],
    currency: str,
    duration_kind: Optional[str],
    duration_months: Optional[int],
) -> Dict[str, Any]:
    request_row = get_coupon_request(coupon_request_id)
    if not request_row:
        raise RuntimeError("Coupon request not found")
    return _execute_returning(
        """
        INSERT INTO discount_grant (
            coupon_request_id, reseller_id, customer_account_id, plan_id, approved_by_principal,
            target_scope, discount_kind, stripe_coupon_id, stripe_promotion_code_id,
            percent_off, amount_off, currency, duration_kind, duration_months,
            grant_status, created_at, updated_at
        )
        VALUES (
            %s::uuid, %s::uuid, %s::uuid, %s::uuid, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', now(), now()
        )
        RETURNING discount_grant_id, stripe_coupon_id, stripe_promotion_code_id, grant_status
        """,
        (
            coupon_request_id,
            request_row["reseller_id"],
            request_row["customer_account_id"],
            request_row["plan_id"],
            approved_by_principal,
            target_scope,
            discount_kind,
            stripe_coupon_id,
            stripe_promotion_code_id,
            percent_off,
            amount_off,
            currency,
            duration_kind,
            duration_months,
        ),
    )


def add_coupon_audit_log(
    *,
    coupon_request_id: Optional[str],
    discount_grant_id: Optional[str],
    actor_principal: str,
    action_type: str,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    _execute(
        """
        INSERT INTO coupon_audit_log (
            coupon_request_id, discount_grant_id, actor_principal, action_type, action_payload, created_at
        )
        VALUES (%s::uuid, %s::uuid, %s, %s, %s::jsonb, now())
        """,
        (coupon_request_id, discount_grant_id, actor_principal, action_type, psycopg2.extras.Json(payload or {})),
    )


def list_admin_payouts() -> List[Dict[str, Any]]:
    return _fetchall(
        """
        SELECT reseller_payout_ledger_id, reseller_id, payout_amount, payout_currency, payout_status, hold_status, eligible_at
        FROM reseller_payout_ledger
        ORDER BY created_at DESC
        """
    )


def get_payout_ledger(payout_ledger_id: str) -> Optional[Dict[str, Any]]:
    return _fetchone("SELECT * FROM reseller_payout_ledger WHERE reseller_payout_ledger_id = %s::uuid", (payout_ledger_id,))


def queue_payout_execution(
    payout_ledger_id: str,
    reseller_id: str,
    *,
    status: str = "queued",
    request_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    existing = _fetchone(
        """
        SELECT COALESCE(MAX(attempt_number), 0) AS max_attempt
        FROM reseller_payout_execution
        WHERE reseller_payout_ledger_id = %s::uuid
        """,
        (payout_ledger_id,),
    )
    attempt = int(existing["max_attempt"] or 0) + 1
    return _execute_returning(
        """
        INSERT INTO reseller_payout_execution (
            reseller_payout_ledger_id, reseller_id, attempt_number, execution_status,
            request_payload, queued_at, created_at
        )
        VALUES (%s::uuid, %s::uuid, %s, %s, %s::jsonb, now(), now())
        RETURNING reseller_payout_execution_id, attempt_number, execution_status
        """,
        (payout_ledger_id, reseller_id, attempt, status, psycopg2.extras.Json(request_payload or {})),
    )


def mark_payout_execution_result(
    execution_id: str,
    *,
    execution_status: str,
    stripe_transfer_id: Optional[str] = None,
    stripe_payout_id: Optional[str] = None,
    response_payload: Optional[Dict[str, Any]] = None,
    failure_code: Optional[str] = None,
    failure_message: Optional[str] = None,
) -> Dict[str, Any]:
    return _execute_returning(
        """
        UPDATE reseller_payout_execution
        SET execution_status = %s,
            stripe_transfer_id = COALESCE(%s, stripe_transfer_id),
            stripe_payout_id = COALESCE(%s, stripe_payout_id),
            response_payload = COALESCE(%s::jsonb, response_payload),
            failure_code = %s,
            failure_message = %s,
            executed_at = now()
        WHERE reseller_payout_execution_id = %s::uuid
        RETURNING reseller_payout_execution_id, execution_status, stripe_transfer_id
        """,
        (
            execution_status,
            stripe_transfer_id,
            stripe_payout_id,
            psycopg2.extras.Json(response_payload) if response_payload is not None else None,
            failure_code,
            failure_message,
            execution_id,
        ),
    )


def mark_payout_ledger_status(payout_ledger_id: str, status: str, hold_status: Optional[str] = None) -> None:
    _execute(
        """
        UPDATE reseller_payout_ledger
        SET payout_status = %s,
            hold_status = COALESCE(%s, hold_status),
            updated_at = now()
        WHERE reseller_payout_ledger_id = %s::uuid
        """,
        (status, hold_status, payout_ledger_id),
    )
