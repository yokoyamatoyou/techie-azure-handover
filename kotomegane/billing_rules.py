from __future__ import annotations

from dataclasses import dataclass

SERVICE_KOTOMEGAKI = "aio2-main"
SERVICE_KOTOMEGANE = "kotomegane"
SERVICE_KOTOMAKE = "notecode"


@dataclass(frozen=True)
class BillingRule:
    service_key: str
    run_mode: str
    provider_count: int
    unit_kind: str
    units: int
    label: str
    note: str


BILLING_RULES: tuple[BillingRule, ...] = (
    BillingRule(
        service_key=SERVICE_KOTOMAKE,
        run_mode="manual",
        provider_count=1,
        unit_kind="credit",
        units=1,
        label="コトメイク手動",
        note="1回 1クレジットです。",
    ),
    BillingRule(
        service_key=SERVICE_KOTOMEGAKI,
        run_mode="manual",
        provider_count=1,
        unit_kind="credit",
        units=1,
        label="コトミガキ手動",
        note="1回 1クレジットです。",
    ),
    BillingRule(
        service_key=SERVICE_KOTOMEGANE,
        run_mode="manual",
        provider_count=1,
        unit_kind="credit",
        units=2,
        label="コトメガネ手動",
        note="手動確認は実行完了時に 1回 2クレジットを消費します。",
    ),
    BillingRule(
        service_key=SERVICE_KOTOMEGANE,
        run_mode="batch",
        provider_count=1,
        unit_kind="batch_unit",
        units=1,
        label="コトメガネ定期リサーチ",
        note="定期リサーチ（今すぐ）は結果反映完了時に 1 単位を消費します。",
    ),
    BillingRule(
        service_key=SERVICE_KOTOMEGANE,
        run_mode="scheduled",
        provider_count=1,
        unit_kind="batch_unit",
        units=1,
        label="コトメガネ定期リサーチ（自動）",
        note="定期リサーチ（自動）は結果反映完了時に 1 単位を消費します。",
    ),
)


def get_billing_rule(
    service_key: str,
    run_mode: str,
    *,
    provider_count: int = 1,
) -> BillingRule:
    normalized_mode = str(run_mode or "").strip().lower()
    normalized_provider_count = max(1, int(provider_count or 1))
    exact_match: BillingRule | None = None
    fallback_match: BillingRule | None = None
    for rule in BILLING_RULES:
        if rule.service_key != service_key or rule.run_mode != normalized_mode:
            continue
        if rule.provider_count == normalized_provider_count:
            exact_match = rule
            break
        if rule.provider_count == 1:
            fallback_match = rule
    if exact_match is not None:
        return exact_match
    if fallback_match is not None:
        return fallback_match
    return BillingRule(
        service_key=service_key,
        run_mode=normalized_mode,
        provider_count=normalized_provider_count,
        unit_kind="internal",
        units=0,
        label="未定義ルール",
        note="この実行方式の課金ルールは未定義です。",
    )


def describe_internal_billing_policy(service_key: str) -> str:
    manual_rule = get_billing_rule(service_key, "manual")
    batch_rule = get_billing_rule(service_key, "batch")
    return (
        "手動と定期リサーチは内部で別ルール管理です。"
        f" 手動は {manual_rule.units} 単位、定期リサーチは {batch_rule.units} 単位で扱います。"
    )


def describe_run_mode_billing_policy(service_key: str, run_mode: str) -> str:
    rule = get_billing_rule(service_key, run_mode)
    label_map = {
        "manual": "手動",
        "batch": "定期リサーチ（今すぐ）",
        "scheduled": "定期リサーチ（自動）",
    }
    mode_label = label_map.get(str(run_mode or "").strip().lower(), str(run_mode or "実行"))
    return f"{mode_label}: {rule.note}"


def build_billing_policy_microcopy(service_key: str) -> str:
    joined = " / ".join(
        [
            describe_run_mode_billing_policy(service_key, "manual"),
            describe_run_mode_billing_policy(service_key, "batch"),
            describe_run_mode_billing_policy(service_key, "scheduled"),
        ]
    )
    return f"{joined}（「クレジット」と「単位」は別々の残数として管理されています）"
