# -*- coding: utf-8 -*-
"""Production usage ledger repository helpers."""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import psycopg2.extras

from shared.billing import repository as billing_repository

DEFAULT_INCLUDED_CREDITS = 15
GLOBAL_CREDIT_SERVICE_KEY = "techie"
ACTIVE_CONTRACT_STATUSES = ("active", "trialing", "checkout_completed")


def _plan_included_credits(plan_key: str | None) -> int:
    normalized = str(plan_key or "").strip().lower()
    if normalized in {"entry", "techie-entry"}:
        return int(os.environ.get("TECHIE_ENTRY_INCLUDED_CREDITS", "15"))
    if normalized in {"standard", "techie-standard"}:
        return int(os.environ.get("TECHIE_STANDARD_INCLUDED_CREDITS", "30"))
    if normalized in {"pro", "techie-pro"}:
        return int(os.environ.get("TECHIE_PRO_INCLUDED_CREDITS", "100"))
    return DEFAULT_INCLUDED_CREDITS


def _fetchone(cursor, query: str, params=()) -> Optional[Dict[str, Any]]:
    cursor.execute(query, params)
    row = cursor.fetchone()
    return dict(row) if row else None


def _get_active_contract_for_tenant(tenant_id: str) -> Optional[Dict[str, Any]]:
    return billing_repository._fetchone(
        """
        SELECT
            sc.subscription_contract_id,
            sc.contract_status,
            sc.metadata AS contract_metadata,
            pm.plan_code,
            pm.metadata AS plan_metadata
        FROM subscription_contract sc
        JOIN customer_account ca ON ca.customer_account_id = sc.customer_account_id
        LEFT JOIN plan_master pm ON pm.plan_id = sc.plan_id
        WHERE ca.tenant_id = %s::uuid
          AND sc.contract_status IN ('active', 'trialing', 'checkout_completed')
          AND (
              sc.metadata->>'current_period_end' IS NULL
              OR (sc.metadata->>'current_period_end') !~ '^[0-9]+$'
              OR (sc.metadata->>'current_period_end')::bigint >= EXTRACT(EPOCH FROM now())::bigint
          )
        ORDER BY
            CASE
                WHEN sc.contract_status IN ('active', 'trialing') THEN 0
                ELSE 1
            END,
            sc.updated_at DESC
        LIMIT 1
        """,
        (tenant_id,),
    )


def _get_contract_for_usage(subscription_contract_id: str) -> Optional[Dict[str, Any]]:
    return billing_repository._fetchone(
        """
        SELECT
            sc.subscription_contract_id,
            sc.contract_status,
            sc.metadata AS contract_metadata,
            pm.plan_code,
            pm.metadata AS plan_metadata
        FROM subscription_contract sc
        LEFT JOIN plan_master pm ON pm.plan_id = sc.plan_id
        WHERE sc.subscription_contract_id = %s::uuid
        LIMIT 1
        """,
        (subscription_contract_id,),
    )


def _contract_is_active(contract: Optional[Dict[str, Any]]) -> bool:
    if not contract:
        return False
    return str(contract.get("contract_status") or "").strip().lower() in ACTIVE_CONTRACT_STATUSES


def _contract_period_start(contract: Optional[Dict[str, Any]]) -> Optional[int]:
    metadata = dict((contract or {}).get("contract_metadata") or {})
    value = metadata.get("current_period_start")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _contract_period_end(contract: Optional[Dict[str, Any]]) -> Optional[int]:
    metadata = dict((contract or {}).get("contract_metadata") or {})
    value = metadata.get("current_period_end")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _contract_can_spend_included(contract: Optional[Dict[str, Any]]) -> bool:
    if not _contract_is_active(contract):
        return False
    period_end = _contract_period_end(contract)
    return period_end is None or period_end >= int(time.time())


def _included_credits_from_contract(contract: Optional[Dict[str, Any]]) -> int:
    if not contract:
        return 0

    plan_metadata = dict(contract.get("plan_metadata") or {})
    if plan_metadata.get("included_credits") is not None:
        try:
            return int(plan_metadata["included_credits"])
        except (TypeError, ValueError):
            pass

    contract_metadata = dict(contract.get("contract_metadata") or {})
    return _plan_included_credits(
        contract_metadata.get("plan_id")
        or contract_metadata.get("service_code")
        or plan_metadata.get("plan_key")
        or contract.get("plan_code")
    )


def _included_credits_used_for_period(cursor, account: Dict[str, Any], contract: Optional[Dict[str, Any]]) -> int:
    if not _contract_can_spend_included(contract):
        return 0

    period_start = _contract_period_start(contract)
    if period_start is None:
        return int(account["included_credits_used"])

    cursor.execute(
        """
        SELECT COALESCE(SUM(units), 0) AS used
        FROM usage_event_ledger
        WHERE usage_account_id = %s::uuid
          AND credit_bucket = 'included'
          AND direction = 'debit'
          AND created_at >= to_timestamp(%s)
        """,
        (account["usage_account_id"], period_start),
    )
    row = cursor.fetchone()
    return int((row or {}).get("used") or 0)


def _included_credit_state(account: Dict[str, Any]) -> Dict[str, int]:
    contract = _get_contract_for_usage(str(account["subscription_contract_id"])) if account.get("subscription_contract_id") else None
    if not _contract_can_spend_included(contract):
        return {"total": 0, "used": 0, "remaining": 0}

    total = int(account["included_credits_total"])
    with billing_repository.get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            used = _included_credits_used_for_period(cursor, account, contract)
    remaining = max(0, total - used)
    return {"total": total, "used": used, "remaining": remaining}


def ensure_usage_account(
    *,
    tenant_id: str,
    service_key: str,
    subscription_contract_id: Optional[str] = None,
    included_credits_total: int = DEFAULT_INCLUDED_CREDITS,
) -> Dict[str, Any]:
    contract: Optional[Dict[str, Any]] = None
    if subscription_contract_id is None:
        contract = _get_active_contract_for_tenant(tenant_id)
        subscription_contract_id = contract["subscription_contract_id"] if contract else None
    else:
        contract = _get_contract_for_usage(subscription_contract_id)
        if not _contract_is_active(contract):
            subscription_contract_id = None
            contract = None

    # Do not grant monthly included credits before Stripe/contract entitlement exists.
    if subscription_contract_id is None and included_credits_total == DEFAULT_INCLUDED_CREDITS:
        included_credits_total = 0
    elif subscription_contract_id is not None and included_credits_total == DEFAULT_INCLUDED_CREDITS:
        included_credits_total = _included_credits_from_contract(contract)

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
            SET subscription_contract_id = EXCLUDED.subscription_contract_id,
                included_credits_total = CASE
                    WHEN EXCLUDED.subscription_contract_id IS NULL THEN service_usage_account.included_credits_total
                    ELSE EXCLUDED.included_credits_total
                END,
                included_credits_used = CASE
                    WHEN EXCLUDED.subscription_contract_id IS NULL THEN service_usage_account.included_credits_used
                    ELSE LEAST(service_usage_account.included_credits_used, EXCLUDED.included_credits_total)
                END,
                updated_at = now()
        RETURNING usage_account_id, tenant_id, service_key, subscription_contract_id,
                  included_credits_total, included_credits_used, bonus_credits_total, bonus_credits_used
        """,
        (tenant_id, service_key, subscription_contract_id, included_credits_total),
    )


def has_active_entitlement(*, tenant_id: str, service_key: Optional[str] = None) -> bool:
    """Return True only when a tenant may use paid service apps.

    A signed-in user is not enough. Service access requires either an active
    Stripe-backed contract or already-granted/purchased credits.
    """
    contract = billing_repository._fetchone(
        """
        SELECT sc.subscription_contract_id
        FROM subscription_contract sc
        JOIN customer_account ca ON ca.customer_account_id = sc.customer_account_id
        WHERE ca.tenant_id = %s::uuid
          AND sc.contract_status IN ('active', 'trialing', 'checkout_completed')
          AND (
              sc.metadata->>'current_period_end' IS NULL
              OR (sc.metadata->>'current_period_end') !~ '^[0-9]+$'
              OR (sc.metadata->>'current_period_end')::bigint >= EXTRACT(EPOCH FROM now())::bigint
          )
        ORDER BY
            CASE
                WHEN sc.contract_status IN ('active', 'trialing') THEN 0
                ELSE 1
            END,
            sc.updated_at DESC
        LIMIT 1
        """,
        (tenant_id,),
    )
    if contract:
        return True

    accounts_to_check = [GLOBAL_CREDIT_SERVICE_KEY]
    if service_key and service_key != GLOBAL_CREDIT_SERVICE_KEY:
        accounts_to_check.insert(0, service_key)

    account = billing_repository._fetchone(
        """
        SELECT
            COALESCE(SUM(GREATEST(0, bonus_credits_total - bonus_credits_used)), 0) AS bonus_remaining
        FROM service_usage_account
        WHERE tenant_id = %s::uuid
          AND service_key = ANY(%s)
        """,
        (tenant_id, accounts_to_check),
    )
    if not account:
        return False

    return int(account.get("bonus_remaining") or 0) > 0


def get_usage_summary(*, tenant_id: str, service_key: str) -> Dict[str, Any]:
    # Monthly subscription credits are shared across all TECHIE services.
    # Service-specific accounts keep per-service bonus/debit history; the global
    # account owns the plan's included monthly bucket.
    account = ensure_usage_account(
        tenant_id=tenant_id,
        service_key=service_key,
        included_credits_total=DEFAULT_INCLUDED_CREDITS if service_key == GLOBAL_CREDIT_SERVICE_KEY else 0,
    )
    global_account = (
        account
        if service_key == GLOBAL_CREDIT_SERVICE_KEY
        else ensure_usage_account(tenant_id=tenant_id, service_key=GLOBAL_CREDIT_SERVICE_KEY)
    )
    service_included = _included_credit_state(account)
    global_included = _included_credit_state(global_account)
    service_included_remaining = service_included["remaining"]
    global_included_remaining = global_included["remaining"]
    included_remaining = (
        service_included_remaining
        if service_key == GLOBAL_CREDIT_SERVICE_KEY
        else service_included_remaining + global_included_remaining
    )
    service_bonus_remaining = max(0, int(account["bonus_credits_total"]) - int(account["bonus_credits_used"]))
    global_bonus_remaining = max(0, int(global_account["bonus_credits_total"]) - int(global_account["bonus_credits_used"]))
    bonus_remaining = service_bonus_remaining + (0 if service_key == GLOBAL_CREDIT_SERVICE_KEY else global_bonus_remaining)
    total_remaining = included_remaining + bonus_remaining
    return {
        "usage_account_id": account["usage_account_id"],
        "tenant_id": account["tenant_id"],
        "service_key": account["service_key"],
        "subscription_contract_id": account.get("subscription_contract_id"),
        "included_credits_total": service_included["total"],
        "included_credits_used": service_included["used"],
        "included_credits_remaining": included_remaining,
        "global_included_credits_total": global_included["total"],
        "global_included_credits_used": global_included["used"],
        "global_included_credits_remaining": global_included_remaining,
        "bonus_credits_total": int(account["bonus_credits_total"]),
        "bonus_credits_used": int(account["bonus_credits_used"]),
        "bonus_credits_remaining": bonus_remaining,
        "service_bonus_credits_remaining": service_bonus_remaining,
        "purchased_credits_remaining": bonus_remaining,
        "global_purchased_credits_remaining": global_bonus_remaining,
        "total_remaining": total_remaining,
        "remaining_credits": total_remaining,
        "used_credits": service_included["used"] + int(account["bonus_credits_used"]),
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

    replay_event: Optional[Dict[str, Any]] = None
    event: Optional[Dict[str, Any]] = None
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
                account = ensure_usage_account(
                    tenant_id=tenant_id,
                    service_key=service_key,
                    included_credits_total=0 if service_key == GLOBAL_CREDIT_SERVICE_KEY else DEFAULT_INCLUDED_CREDITS,
                )
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
                    replay_event = dict(existing)

            if replay_event is None:
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

    if replay_event is not None:
        return get_usage_summary(tenant_id=tenant_id, service_key=service_key) | {
            "usage_event_id": replay_event["usage_event_id"],
            "credit_bucket": replay_event["credit_bucket"],
            "units_consumed": int(replay_event["units"]),
            "granted": False,
            "idempotent_replay": True,
        }

    return get_usage_summary(tenant_id=tenant_id, service_key=service_key) | {
        "usage_event_id": event["usage_event_id"],
        "credit_bucket": event["credit_bucket"],
        "units_consumed": int(event["units"]),
        "granted": True,
        "idempotent_replay": False,
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

    replay_event: Optional[Dict[str, Any]] = None
    event: Optional[Dict[str, Any]] = None
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
                seeded = ensure_usage_account(tenant_id=tenant_id, service_key=service_key, included_credits_total=0)
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
            global_account = account
            if service_key != GLOBAL_CREDIT_SERVICE_KEY:
                seeded_global = ensure_usage_account(
                    tenant_id=tenant_id,
                    service_key=GLOBAL_CREDIT_SERVICE_KEY,
                )
                global_account = _fetchone(
                    cursor,
                    """
                    SELECT usage_account_id, subscription_contract_id,
                           included_credits_total, included_credits_used,
                           bonus_credits_total, bonus_credits_used
                    FROM service_usage_account
                    WHERE usage_account_id = %s::uuid
                    FOR UPDATE
                    """,
                    (seeded_global["usage_account_id"],),
                )

            if idempotency_key:
                existing = _fetchone(
                    cursor,
                    """
                    SELECT usage_event_id, credit_bucket, units
                    FROM usage_event_ledger
                    WHERE usage_account_id IN (%s::uuid, %s::uuid) AND idempotency_key = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (account["usage_account_id"], global_account["usage_account_id"], idempotency_key),
                )
                if existing:
                    replay_event = dict(existing)

            if replay_event is None:
                account_contract = (
                    _get_contract_for_usage(str(account["subscription_contract_id"]))
                    if account.get("subscription_contract_id")
                    else None
                )
                global_contract = (
                    _get_contract_for_usage(str(global_account["subscription_contract_id"]))
                    if global_account.get("subscription_contract_id")
                    else None
                )
                account_included_active = _contract_can_spend_included(account_contract)
                global_included_active = _contract_can_spend_included(global_contract)
                included_total = int(account["included_credits_total"]) if account_included_active else 0
                global_included_total = int(global_account["included_credits_total"]) if global_included_active else 0
                included_used = _included_credits_used_for_period(cursor, account, account_contract)
                global_included_used = _included_credits_used_for_period(cursor, global_account, global_contract)
                included_remaining = max(0, included_total - included_used)
                global_included_remaining = (
                    0
                    if service_key == GLOBAL_CREDIT_SERVICE_KEY
                    else max(0, global_included_total - global_included_used)
                )
                service_bonus_remaining = max(0, int(account["bonus_credits_total"]) - int(account["bonus_credits_used"]))
                global_bonus_remaining = max(0, int(global_account["bonus_credits_total"]) - int(global_account["bonus_credits_used"]))
                total_remaining = (
                    included_remaining
                    + global_included_remaining
                    + service_bonus_remaining
                    + (0 if service_key == GLOBAL_CREDIT_SERVICE_KEY else global_bonus_remaining)
                )
                if total_remaining < units:
                    raise RuntimeError("Insufficient credits")

                bucket = "included" if (included_remaining + global_included_remaining) >= units else "bonus"
                debit_account = account
                if bucket == "included":
                    if included_remaining < units and service_key != GLOBAL_CREDIT_SERVICE_KEY:
                        debit_account = global_account
                        debit_included_used = global_included_used
                    else:
                        debit_included_used = included_used
                    cursor.execute(
                        """
                        UPDATE service_usage_account
                        SET included_credits_used = LEAST(included_credits_total, %s),
                            updated_at = now()
                        WHERE usage_account_id = %s::uuid
                        """,
                        (debit_included_used + units, debit_account["usage_account_id"]),
                    )
                elif service_bonus_remaining >= units:
                    cursor.execute(
                        """
                        UPDATE service_usage_account
                        SET bonus_credits_used = bonus_credits_used + %s,
                            updated_at = now()
                        WHERE usage_account_id = %s::uuid
                        """,
                        (units, debit_account["usage_account_id"]),
                    )
                else:
                    debit_account = global_account
                    cursor.execute(
                        """
                        UPDATE service_usage_account
                        SET bonus_credits_used = bonus_credits_used + %s,
                            updated_at = now()
                        WHERE usage_account_id = %s::uuid
                        """,
                        (units, debit_account["usage_account_id"]),
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
                        debit_account["usage_account_id"],
                        tenant_id,
                        service_key,
                        debit_account.get("subscription_contract_id"),
                        actor_user_id,
                        action_key,
                        bucket,
                        units,
                        idempotency_key,
                        psycopg2.extras.Json(metadata or {}),
                    ),
                )
                event = dict(cursor.fetchone())

    if replay_event is not None:
        return get_usage_summary(tenant_id=tenant_id, service_key=service_key) | {
            "usage_event_id": replay_event["usage_event_id"],
            "credit_bucket": replay_event["credit_bucket"],
            "units_consumed": int(replay_event["units"]),
            "consumed": True,
            "idempotent_replay": True,
        }

    return get_usage_summary(tenant_id=tenant_id, service_key=service_key) | {
        "usage_event_id": event["usage_event_id"],
        "credit_bucket": event["credit_bucket"],
        "units_consumed": int(event["units"]),
        "consumed": True,
        "idempotent_replay": False,
    }
