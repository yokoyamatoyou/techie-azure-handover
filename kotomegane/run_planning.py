from __future__ import annotations

import asyncio
import json
from typing import Any

from analysis_lib import normalize_query_text, normalize_text
from config import AppConfig, get_provider_total_question_budget
from query_planning import QueryPlanSpec, QueryPlanner
from storage import Storage


async def prepare_query_plans_for_run(
    db: Storage,
    query_planner: QueryPlanner,
    run_id: str,
    cfg: AppConfig,
    *,
    run_mode: str,
    scheduled_dispatch_at: float | None = None,
) -> list[dict[str, Any]]:
    scheduler_mode = "scheduled" if run_mode == "scheduled" else "immediate"
    provider_batch_mode = "provider_batch" if run_mode in {"batch", "scheduled"} else "none"
    provider_cache_policy = query_planner.build_provider_cache_policy(cfg)
    planner_signature = query_planner.build_planner_signature(cfg)
    saved_plans: list[dict[str, Any]] = []
    remaining_total_queries = get_provider_total_question_budget(
        cfg.provider,
        service_key=cfg.service_key,
        plan_key=cfg.plan_key,
    )
    for raw_query in cfg.keywords:
        normalized_raw_query = normalize_text(raw_query)
        if not normalized_raw_query:
            continue
        if remaining_total_queries <= 0:
            break
        previous_plan = db.get_latest_query_plan_for_query(
            normalize_query_text(normalized_raw_query),
            planner_signature,
        )
        planned: QueryPlanSpec = await asyncio.to_thread(
            query_planner.prepare_query_plan,
            normalized_raw_query,
            cfg,
            previous_plan,
            remaining_total_queries=remaining_total_queries,
        )
        remaining_total_queries = max(0, remaining_total_queries - len(planned.expanded_queries))
        query_plan_id = db.save_query_plan(
            run_id=run_id,
            user_query_raw=planned.user_query_raw,
            user_query_norm=normalize_query_text(planned.user_query_raw),
            user_query_short=planned.user_query_short,
            query_was_shortened=planned.query_was_shortened,
            shortening_note=planned.shortening_note,
            expanded_queries_json=json.dumps(planned.expanded_queries, ensure_ascii=False),
            prompt_taxonomy_json=json.dumps(planned.prompt_taxonomy_items, ensure_ascii=False),
            expansion_mode=planned.expansion_mode,
            expansion_signature=planned.expansion_signature,
            scheduler_mode=scheduler_mode,
            scheduled_dispatch_at=scheduled_dispatch_at,
            provider_batch_mode=provider_batch_mode,
            provider_batch_id="",
            provider_cache_policy=provider_cache_policy,
            planner_signature=planner_signature,
        )
        saved_plans.append(
            {
                "query_plan_id": query_plan_id,
                "user_query_raw": planned.user_query_raw,
                "user_query_short": planned.user_query_short,
                "query_was_shortened": planned.query_was_shortened,
                "shortening_note": planned.shortening_note,
                "expanded_queries_json": json.dumps(planned.expanded_queries, ensure_ascii=False),
                "prompt_taxonomy_json": json.dumps(planned.prompt_taxonomy_items, ensure_ascii=False),
                "expansion_mode": planned.expansion_mode,
                "expansion_signature": planned.expansion_signature,
                "planner_signature": planner_signature,
            }
        )
    return saved_plans
