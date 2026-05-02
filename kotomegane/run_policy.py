from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from config import AppConfig, get_provider_option, provider_is_enabled
from plan_catalog import DEFAULT_PLAN_KEY, SERVICE_KOTOMEGANE, plan_supports_run_mode


@dataclass(frozen=True)
class RunPolicy:
    service_key: str
    plan_key: str
    run_mode: str
    provider_key: str
    allowed: bool
    progressive_display: bool
    batch_timeout_hours: int
    partial_display_after_hours: int
    partial_display_policy: str
    mode_summary: str
    blocked_reason: str = ""


def resolve_run_policy(config: AppConfig, run_mode: str) -> RunPolicy:
    provider = get_provider_option(config.provider)
    normalized_mode = str(run_mode or "").strip().lower() or "manual"
    service_key = str(config.service_key or SERVICE_KOTOMEGANE)
    plan_key = str(config.plan_key or DEFAULT_PLAN_KEY)
    plan_allows_mode = plan_supports_run_mode(normalized_mode, service_key=service_key, plan_key=plan_key)

    if normalized_mode == "manual":
        provider_ready = bool(provider_is_enabled(config, provider.key) and provider.implemented and provider.supports_live_requests)
        allowed = bool(plan_allows_mode and provider_ready)
        blocked_reason = "" if allowed else "手動確認は現在この接続先では使えません。"
        mode_summary = "返答が来た順に結果を反映します。"
        return RunPolicy(
            service_key=service_key,
            plan_key=plan_key,
            run_mode=normalized_mode,
            provider_key=provider.key,
            allowed=allowed,
            progressive_display=True,
            batch_timeout_hours=0,
            partial_display_after_hours=0,
            partial_display_policy="sequential_progressive",
            mode_summary=mode_summary,
            blocked_reason=blocked_reason,
        )

    provider_ready = bool(provider_is_enabled(config, provider.key) and provider.implemented and provider.supports_batch)
    allowed = bool(plan_allows_mode and provider_ready)
    blocked_reason = "" if allowed else "定期リサーチは現在この接続先では使えません。"
    mode_summary = (
        f"定期リサーチは全件待機し、{int(provider.partial_display_after_hours or provider.batch_timeout_hours or 24)}時間後に未完 provider を灰色表示します。"
        if allowed
        else "定期リサーチは未対応です。"
    )
    return RunPolicy(
        service_key=service_key,
        plan_key=plan_key,
        run_mode=normalized_mode,
        provider_key=provider.key,
        allowed=allowed,
        progressive_display=False,
        batch_timeout_hours=max(0, int(provider.batch_timeout_hours or 0)),
        partial_display_after_hours=max(0, int(provider.partial_display_after_hours or 0)),
        partial_display_policy=str(provider.partial_display_policy or "hold_until_complete"),
        mode_summary=mode_summary,
        blocked_reason=blocked_reason,
    )


def build_runtime_policy_microcopy(config: AppConfig) -> str:
    manual_policy = resolve_run_policy(config, "manual")
    batch_policy = resolve_run_policy(config, "batch")
    scheduled_policy = resolve_run_policy(config, "scheduled")
    policy_entries = [
        ("手動", manual_policy),
        ("定期リサーチ（今すぐ）", batch_policy),
        ("定期リサーチ（自動）", scheduled_policy),
    ]
    parts: list[str] = []
    for label, policy in policy_entries:
        message = policy.mode_summary if policy.allowed else (policy.blocked_reason or "未対応")
        parts.append(f"{label}: {message}")
    return " / ".join(parts)


def should_allow_batch_import(
    batch_job: dict[str, Any],
    config: AppConfig,
    *,
    now_timestamp: float | None = None,
) -> bool:
    policy = resolve_run_policy(config, str(batch_job.get("run_mode") or "batch"))
    if not policy.allowed:
        return False
    request_count = max(0, int(batch_job.get("request_count") or 0))
    completed_count = int(batch_job.get("request_counts_completed") or 0) + int(batch_job.get("request_counts_failed") or 0)
    if request_count and completed_count >= request_count:
        return True
    status = str(batch_job.get("status") or "").strip().lower()
    if status == "completed":
        return True
    if policy.partial_display_policy == "hold_until_complete":
        return False
    submitted_at = float(batch_job.get("submitted_at") or batch_job.get("batch_submitted_at") or 0.0)
    if submitted_at <= 0:
        return status in {"expired", "cancelled", "failed"}
    now_value = float(now_timestamp or time.time())
    elapsed_hours = max(0.0, (now_value - submitted_at) / 3600.0)
    return status in {"expired", "cancelled", "failed"} and elapsed_hours >= float(policy.partial_display_after_hours or 0)
