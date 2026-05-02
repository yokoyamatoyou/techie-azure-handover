# -*- coding: utf-8 -*-
"""Production usage ledger repository helpers."""
from __future__ import annotations

from typing import Any, Dict, Optional

import psycopg2.extras

from shared.billing import repository as billing_repository

DEFAULT_INCLUDED_CREDITS = 15


def _fetchone(cursor, query: str, params=()) -> Optional[Dict[str, Any]]:
    cursor.execute(query, params)
    row = cursor.fetchone()
    return dict(row) if row else None


def ensure_usage_account(
    *,
    tenant_id: str,
    service_key: str,
    subscription_contract_id: Optional[str] = None,
    included_credits_total: int = DEFAULT_INCLUDED_CREDITS,
) -> Dict[str, Any]:
    if subscription_contract_id is None:
        contract = billing_repository._fetchone(
            """
            SELECT sc.subscription_contract_id
            FROM subscription_contract sc
            JOIN customer_account ca ON ca.customer_account_id = sc.customer_account_id
            WHERE ca.tenant_id = %s::uuid
            ORDER BY
                CASE
                    WHEN sc.contract_status IN ('active', 'trialing', 'checkout_completed') THEN 0
                    ELSE 1
                END,
                sc.updated_at DESC
            LIMIT 1
            """,
            (tenant_id,),
        )
        subscription_contract_id = contract["subscription_contract_id"] if contract else None

    return billing_repository._execute_returning(
        """
        INSERT INTO service_usage_account (
            tenant_id, service_key, subscription_contract_id,
            included_credits_total, included_credits_used,
            bonus_credits_total, bonus_credits_used,
            created_at, updated_at
        )
        VALUES (%s::uuid, %s, %s::uuid, %s, 0, 0, 0, now(), now())
        ON CONFLICT (tenant_id, service_key) DO UPDATE
            SET subscription_contract_id = COALESCE(EXCLUDED.subscription_contract_id, service_usage_account.subscription_contract_id),
                included_credits_total = GREATEST(service_usage_account.included_credits_total, EXCLUDED.included_credits_total),
                updated_at = now()
        RETURNING usage_account_id, tenant_id, service_key, subscription_contract_id,
                  included_credits_total, included_credits_used, bonus_credits_total, bonus_credits_used
        """,
        (tenant_id, service_key, subscription_contract_id, included_credits_total),
    )


def get_usage_summary(*, tenant_id: str, service_key: str) -> Dict[str, Any]:
    account = ensure_usage_account(tenant_id=tenant_id, service_key=service_key)
    included_remaining = max(0, int(account["included_credits_total"]) - int(account["included_credits_used"]))
    bonus_remaining = max(0, int(account["bonus_credits_total"]) - int(account["bonus_credits_used"]))
    total_remaining = included_remaining + bonus_remaining
    return {
        "usage_account_id": account["usage_account_id"],
        "tenant_id": account["tenant_id"],
        "service_key": account["service_key"],
        "subscription_contract_id": account.get("subscription_contract_id"),
        "included_credits_total": int(account["included_credits_total"]),
        "included_credits_used": int(account["included_credits_used"]),
        "included_credits_remaining": included_remaining,
        "bonus_credits_total": int(account["bonus_credits_total"]),
        "bonus_credits_used": int(account["bonus_credits_used"]),
        "bonus_credits_remaining": bonus_remaining,
        "total_remaining": total_remaining,
    }


def grant_bonus_credits(
    *,
    tenant_id: str,
    service_key: str,
    units: int,
    actor_user_id: str,
    reason: str,
    idempotency_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if units <= 0:
        raise ValueError("units must be positive")

    with billing_repository.get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            account = _fetchone(
                cursor,
                """
                SELECT usage_account_id
                FROM service_usage_account
                WHERE tenant_id = %s::uuid AND service_key = %s
                FOR UPDATE
                """,
                (tenant_id, service_key),
            )
            if not account:
                account = ensure_usage_account(tenant_id=tenant_id, service_key=service_key)
                account = {"usage_account_id": account["usage_account_id"]}

            if idempotency_key:
                existing = _fetchone(
                    cursor,
                    """
                    SELECT usage_event_id, credit_bucket, units
                    FROM usage_event_ledger
                    WHERE usage_account_id = %s::uuid AND idempotency_key = %s
                    """,
                    (account["usage_account_id"], idempotency_key),
                )
                if existing:
                    return get_usage_summary(tenant_id=tenant_id, service_key=service_key) | {
                        "usage_event_id": existing["usage_event_id"],
                        "credit_bucket": existing["credit_bucket"],
                        "units_consumed": int(existing["units"]),
                        "granted": True,
                    }

            cursor.execute(
                """
                UPDATE service_usage_account
                SET bonus_credits_total = bonus_credits_total + %s,
                    updated_at = now()
                WHERE usage_account_id = %s::uuid
                """,
                (units, account["usage_account_id"]),
            )
            cursor.execute(
                """
                INSERT INTO usage_event_ledger (
                    usage_account_id, tenant_id, service_key, actor_user_id,
                    action_key, credit_bucket, units, direction, idempotency_key,
                    metadata, created_at
                )
                VALUES (%s::uuid, %s::uuid, %s, %s, %s, 'bonus', %s, 'credit', %s, %s::jsonb, now())
                RETURNING usage_event_id, credit_bucket, units
                """,
                (
                    account["usage_account_id"],
                    tenant_id,
                    service_key,
                    actor_user_id,
                    reason,
                    units,
                    idempotency_key,
                    psycopg2.extras.Json(metadata or {}),
                ),
            )
            event = dict(cursor.fetchone())

    return get_usage_summary(tenant_id=tenant_id, service_key=service_key) | {
        "usage_event_id": event["usage_event_id"],
        "credit_bucket": event["credit_bucket"],
        "units_consumed": int(event["units"]),
        "granted": True,
    }


def consume_credits(
    *,
    tenant_id: str,
    service_key: str,
    actor_user_id: str,
    action_key: str,
    units: int = 1,
    idempotency_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if units <= 0:
        raise ValueError("units must be positive")

    with billing_repository.get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            account = _fetchone(
                cursor,
                """
                SELECT usage_account_id, subscription_contract_id,
                       included_credits_total, included_credits_used,
                       bonus_credits_total, bonus_credits_used
                FROM service_usage_account
                WHERE tenant_id = %s::uuid AND service_key = %s
                FOR UPDATE
                """,
                (tenant_id, service_key),
            )
            if not account:
                seeded = ensure_usage_account(tenant_id=tenant_id, service_key=service_key)
                account = {
                    "usage_account_id": seeded["usage_account_id"],
                    "subscription_contract_id": seeded.get("subscription_contract_id"),
                    "included_credits_total": seeded["included_credits_total"],
                    "included_credits_used": seeded["included_credits_used"],
                    "bonus_credits_total": seeded["bonus_credits_total"],
                    "bonus_credits_used": seeded["bonus_credits_used"],
                }
                account = _fetchone(
                    cursor,
                    """
                    SELECT usage_account_id, subscription_contract_id,
                           included_credits_total, included_credits_used,
                           bonus_credits_total, bonus_credits_used
                    FROM service_usage_account
                    WHERE usage_account_id = %s::uuid
                    FOR UPDATE
                    """,
                    (account["usage_account_id"],),
                )

            if idempotency_key:
                existing = _fetchone(
                    cursor,
                    """
                    SELECT usage_event_id, credit_bucket, units
                    FROM usage_event_ledger
                    WHERE usage_account_id = %s::uuid AND idempotency_key = %s
                    """,
                    (account["usage_account_id"], idempotency_key),
                )
                if existing:
                    return get_usage_summary(tenant_id=tenant_id, service_key=service_key) | {
                        "usage_event_id": existing["usage_event_id"],
                        "credit_bucket": existing["credit_bucket"],
                        "units_consumed": int(existing["units"]),
                        "consumed": True,
                        "idempotent_replay": True,
                    }

            included_remaining = max(0, int(account["included_credits_total"]) - int(account["included_credits_used"]))
            bonus_remaining = max(0, int(account["bonus_credits_total"]) - int(account["bonus_credits_used"]))
            total_remaining = included_remaining + bonus_remaining
            if total_remaining < units:
                raise RuntimeError("Insufficient credits")

            bucket = "included" if included_remaining >= units else "bonus"
            if bucket == "included":
                cursor.execute(
                    """
                    UPDATE service_usage_account
                    SET included_credits_used = included_credits_used + %s,
                        updated_at = now()
                    WHERE usage_account_id = %s::uuid
                    """,
                    (units, account["usage_account_id"]),
                )
            else:
                cursor.execute(
                    """
                    UPDATE service_usage_account
                    SET bonus_credits_used = bonus_credits_used + %s,
                        updated_at = now()
                    WHERE usage_account_id = %s::uuid
                    """,
                    (units, account["usage_account_id"]),
                )

            cursor.execute(
                """
                INSERT INTO usage_event_ledger (
                    usage_account_id, tenant_id, service_key, subscription_contract_id,
                    actor_user_id, action_key, credit_bucket, units, direction,
                    idempotency_key, metadata, created_at
                )
                VALUES (
                    %s::uuid, %s::uuid, %s, %s::uuid,
                    %s, %s, %s, %s, 'debit',
                    %s, %s::jsonb, now()
                )
                RETURNING usage_event_id, credit_bucket, units
                """,
                (
                    account["usage_account_id"],
                    tenant_id,
                    service_key,
                    account.get("subscription_contract_id"),
                    actor_user_id,
                    action_key,
                    bucket,
                    units,
                    idempotency_key,
                    psycopg2.extras.Json(metadata or {}),
                ),
            )
            event = dict(cursor.fetchone())

    return get_usage_summary(tenant_id=tenant_id, service_key=service_key) | {
        "usage_event_id": event["usage_event_id"],
        "credit_bucket": event["credit_bucket"],
        "units_consumed": int(event["units"]),
        "consumed": True,
        "idempotent_replay": False,
    }

