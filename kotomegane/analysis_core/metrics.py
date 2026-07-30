from __future__ import annotations

import datetime as dt
import json
from collections import Counter, defaultdict
from typing import Any

from config import AppConfig

from analysis_core.common import *
from analysis_core.source_evidence import resolve_citation_records


def _resolve_user_query_raw(row: dict[str, Any], payload: dict[str, Any] | None = None) -> str:
    effective_payload = payload if isinstance(payload, dict) else parse_json_object(row.get("output_json"))
    analysis_context = effective_payload.get("analysis_context") or {}
    if isinstance(analysis_context, dict):
        user_query_raw = str(analysis_context.get("user_query_raw") or "").strip()
        if user_query_raw:
            return user_query_raw
    return str(row.get("user_query_raw") or row.get("keyword_raw") or "").strip()


def _row_target_hit_rate(row: dict[str, Any]) -> float:
    if row.get("target_domain_hit_rate") is not None:
        try:
            return float(row.get("target_domain_hit_rate") or 0.0)
        except (TypeError, ValueError):
            return 0.0
    return 100.0 if row.get("target_domain_hit") else 0.0


def _row_external_lead_rate(row: dict[str, Any]) -> float:
    if row.get("external_lead_rate") is not None:
        try:
            return float(row.get("external_lead_rate") or 0.0)
        except (TypeError, ValueError):
            return 0.0
    verdict = classify_visibility_verdict(
        resolve_visibility_score(row),
        bool(row.get("target_domain_hit")),
        bool(row.get("brand_mention_hit")),
    )
    return 100.0 if verdict == "外部サイト優勢" else 0.0


def _row_brand_hit_rate(row: dict[str, Any]) -> float:
    if row.get("brand_mention_hit_rate") is not None:
        try:
            return float(row.get("brand_mention_hit_rate") or 0.0)
        except (TypeError, ValueError):
            return 0.0
    return 100.0 if row.get("brand_mention_hit") else 0.0


def build_query_rollup_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    ordered_rows = sorted(rows, key=lambda row: float(row.get("analyzed_at") or 0.0), reverse=True)
    latest_run_by_query: dict[str, str] = {}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for row in ordered_rows:
        payload = parse_json_object(row.get("output_json"))
        query_raw = _resolve_user_query_raw(row, payload)
        query_key = normalize_text(query_raw)
        if not query_key:
            continue
        run_id = str(row.get("run_id") or "")
        selected_run_id = latest_run_by_query.setdefault(query_key, run_id or query_key)
        if (run_id or query_key) != selected_run_id:
            continue
        grouped.setdefault((query_key, selected_run_id), []).append(row)

    rollups: list[dict[str, Any]] = []
    for _group_key, group_rows in grouped.items():
        latest_row = max(group_rows, key=lambda row: float(row.get("analyzed_at") or 0.0))
        payload = parse_json_object(latest_row.get("output_json"))
        merged_citations: list[dict[str, Any]] = []
        merged_competitors: list[str] = []
        try:
            planned_queries = json.loads(str(latest_row.get("expanded_queries_json") or "[]"))
        except Exception:
            planned_queries = []
        executed_queries = dedupe_preserve_order(
            [str(item).strip() for item in planned_queries if str(item).strip()]
            or [str(row.get("executed_query") or row.get("keyword_raw") or "").strip() for row in group_rows]
        )
        seen_urls: set[str] = set()
        query_hit_map: dict[str, bool] = {query: False for query in executed_queries}
        for row in group_rows:
            row_payload = parse_json_object(row.get("output_json"))
            executed_query = str(row.get("executed_query") or row.get("keyword_raw") or "").strip()
            if executed_query and row.get("target_domain_hit"):
                query_hit_map[executed_query] = True
            for citation in resolve_citation_records(row, row_payload):
                url = str(citation.get("url") or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                merged_citations.append({"url": url, "title": str(citation.get("title") or url).strip()})
            merged_competitors.extend(str(item).strip() for item in (row_payload.get("competitor_mentions") or []) if str(item).strip())

        result_count = len(group_rows)
        trial_count = result_count
        score_values = [resolve_visibility_score(row) for row in group_rows]
        raw_llm_values = [resolve_raw_llm_score(row) for row in group_rows]
        avg_score = round(sum(score_values) / result_count, 1) if result_count else 0.0
        avg_raw_llm_score = round(sum(raw_llm_values) / result_count, 1) if result_count else 0.0
        target_hit_count = sum(1 for row in group_rows if row.get("target_domain_hit"))
        target_hit_rate = round(target_hit_count / result_count * 100, 1) if result_count else 0.0
        owned_citation_result_count = sum(1 for row in group_rows if int(row.get("owned_citation_count") or 0) > 0)
        owned_citation_result_rate = round((owned_citation_result_count / result_count) * 100, 1) if result_count else 0.0
        external_lead_trial_count = sum(
            1
            for row in group_rows
            if classify_visibility_verdict(
                resolve_visibility_score(row),
                bool(row.get("target_domain_hit")),
                bool(row.get("brand_mention_hit")),
            )
            == "外部サイト優勢"
        )
        self_candidate_trial_count = sum(
            1
            for row in group_rows
            if row.get("target_domain_hit") and int(row.get("owned_citation_count") or 0) <= 0
        )
        executed_query_count = len(executed_queries)
        question_group_count = executed_query_count
        question_hit_count = sum(1 for hit in query_hit_map.values() if hit)
        question_coverage_rate = round((question_hit_count / question_group_count) * 100, 1) if question_group_count else target_hit_rate
        owned_citation_query_count = len(
            {
                str(row.get("executed_query") or row.get("keyword_raw") or "").strip()
                for row in group_rows
                if int(row.get("owned_citation_count") or 0) > 0
            }
        )
        owned_citation_question_rate = (
            round((owned_citation_query_count / question_group_count) * 100, 1) if question_group_count else owned_citation_result_rate
        )
        brand_hit_rate = round(sum(1 for row in group_rows if row.get("brand_mention_hit")) / result_count * 100, 1) if result_count else 0.0
        external_lead_rate = round((external_lead_trial_count / result_count) * 100, 1) if result_count else 0.0
        variance_metrics = build_variance_metrics(score_values, owned_hit_rate=target_hit_rate)

        rollup_payload = dict(payload)
        rollup_payload["citations"] = merged_citations
        rollup_payload["citation_urls"] = [item["url"] for item in merged_citations]
        rollup_payload["competitor_mentions"] = dedupe_preserve_order(merged_competitors)
        rollup_payload["raw_llm_score"] = avg_raw_llm_score
        rollup_payload["deterministic_score"] = avg_score
        rollup_payload["query_rollup"] = {
            "result_count": result_count,
            "trial_count": trial_count,
            "executed_query_count": executed_query_count,
            "question_group_count": question_group_count,
            "executed_queries": executed_queries,
            "target_hit_count": target_hit_count,
            "target_domain_hit_rate": target_hit_rate,
            "owned_citation_result_count": owned_citation_result_count,
            "owned_citation_result_rate": owned_citation_result_rate,
            "external_lead_trial_count": external_lead_trial_count,
            "self_candidate_trial_count": self_candidate_trial_count,
            "query_hit_count": question_hit_count,
            "question_hit_count": question_hit_count,
            "question_coverage_rate": question_coverage_rate,
            "owned_citation_query_count": owned_citation_query_count,
            "owned_citation_question_rate": owned_citation_question_rate,
            "brand_mention_hit_rate": brand_hit_rate,
            "external_lead_rate": external_lead_rate,
            "median_score": variance_metrics["median_score"],
            "min_score": variance_metrics["min_score"],
            "max_score": variance_metrics["max_score"],
            "score_stddev": variance_metrics["score_stddev"],
            "variance_label": variance_metrics["variance_label"],
        }

        rollup_row = dict(latest_row)
        rollup_row.update(
            {
                "keyword_raw": _resolve_user_query_raw(latest_row, payload),
                "keyword_norm": normalize_text(_resolve_user_query_raw(latest_row, payload)),
                "visibility_score": avg_score,
                "deterministic_score": avg_score,
                "raw_llm_score": avg_raw_llm_score,
                "target_domain_hit": 1 if target_hit_rate > 0 else 0,
                "target_hit_count": target_hit_count,
                "brand_mention_hit": 1 if brand_hit_rate > 0 else 0,
                "target_domain_hit_rate": target_hit_rate,
                "owned_citation_result_count": owned_citation_result_count,
                "owned_citation_result_rate": owned_citation_result_rate,
                "brand_mention_hit_rate": brand_hit_rate,
                "external_lead_rate": external_lead_rate,
                "median_score": variance_metrics["median_score"],
                "min_score": variance_metrics["min_score"],
                "max_score": variance_metrics["max_score"],
                "score_stddev": variance_metrics["score_stddev"],
                "variance_label": variance_metrics["variance_label"],
                "estimated_cost_usd": round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in group_rows), 4),
                "input_tokens": sum(int(row.get("input_tokens") or 0) for row in group_rows),
                "cached_tokens": sum(int(row.get("cached_tokens") or 0) for row in group_rows),
                "output_tokens": sum(int(row.get("output_tokens") or 0) for row in group_rows),
                "web_search_calls": sum(int(row.get("web_search_calls") or 0) for row in group_rows),
                "source_count": sum(int(row.get("source_count") or 0) for row in group_rows),
                "result_count": result_count,
                "answer_observation_count": result_count,
                "trial_count": trial_count,
                "internal_query_count": executed_query_count,
                "question_group_count": question_group_count,
                "visible_trial_count": target_hit_count,
                "owned_citation_trial_count": owned_citation_result_count,
                "external_lead_trial_count": external_lead_trial_count,
                "self_candidate_trial_count": self_candidate_trial_count,
                "question_coverage_rate": question_coverage_rate,
                "question_hit_count": question_hit_count,
                "owned_citation_query_count": owned_citation_query_count,
                "owned_citation_question_rate": owned_citation_question_rate,
                "executed_queries_json": json.dumps(executed_queries, ensure_ascii=False),
                "citations_json": json.dumps(merged_citations, ensure_ascii=False),
                "output_json": json.dumps(rollup_payload, ensure_ascii=False),
            }
        )
        rollups.append(rollup_row)
    return sorted(rollups, key=lambda row: float(row.get("analyzed_at") or 0.0), reverse=True)


def resolve_analysis_mode(payload: dict[str, Any]) -> str:
    analysis_context = payload.get("analysis_context") or {}
    return normalize_text(str(analysis_context.get("analysis_mode") or "")) or "market"


def build_keyword_stability_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        keyword = normalize_text(str(row.get("keyword_raw") or row.get("keyword_norm") or ""))
        if keyword:
            grouped[keyword].append(row)

    stability_map: dict[str, dict[str, Any]] = {}
    for keyword, items in grouped.items():
        ordered_items = sorted(items, key=lambda row: float(row.get("analyzed_at") or 0.0))
        scores = [resolve_visibility_score(item) for item in ordered_items]
        verdicts = [
            classify_visibility_verdict(
                resolve_visibility_score(item),
                bool(item.get("target_domain_hit")),
                bool(item.get("brand_mention_hit")),
            )
            for item in ordered_items
        ]
        owned_hit_rate = round(sum(1 for item in ordered_items if item.get("target_domain_hit")) / len(ordered_items) * 100, 1) if ordered_items else 0.0
        variance_metrics = build_variance_metrics(scores, owned_hit_rate=owned_hit_rate)
        dominant_ratio = (Counter(verdicts).most_common(1)[0][1] / len(verdicts)) if verdicts else 0.0
        stability_score = round(
            max(
                0.0,
                100.0
                - min(55.0, float(variance_metrics["score_range"]) * 1.15)
                - min(35.0, float(variance_metrics["score_stddev"]) * 1.2)
                - max(0.0, (1.0 - dominant_ratio) * 35.0),
            ),
            1,
        )
        stability_map[keyword] = {
            "score_range": variance_metrics["score_range"],
            "stability_score": stability_score,
            "stability_label": variance_metrics["variance_label"],
            "sample_count": len(verdicts),
            "median_score": variance_metrics["median_score"],
            "min_score": variance_metrics["min_score"],
            "max_score": variance_metrics["max_score"],
            "score_stddev": variance_metrics["score_stddev"],
            "owned_hit_rate": owned_hit_rate,
            "dominant_verdict": Counter(verdicts).most_common(1)[0][0] if verdicts else "未確認",
        }
    return stability_map


def build_budget_guardrail(
    rows: list[dict[str, Any]],
    config: AppConfig,
    *,
    planned_request_count: int | None = None,
    batch_jobs: list[dict[str, Any]] | None = None,
    run_guardrail_usd: float | None = None,
) -> dict[str, Any]:
    today = dt.datetime.now().date()
    today_rows = [
        row
        for row in rows
        if row.get("analyzed_at") and dt.datetime.fromtimestamp(float(row["analyzed_at"])).date() == today
    ]
    today_spend_usd = round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in today_rows), 6)

    def _matching_mode_rows(target_config: AppConfig) -> list[dict[str, Any]]:
        mode_rows: list[dict[str, Any]] = []
        normalized_target_model = normalize_text(target_config.model)
        for row in rows:
            payload = parse_json_object(row.get("output_json"))
            analysis_context = payload.get("analysis_context") or {}
            row_mode = normalize_text(str(analysis_context.get("analysis_mode") or "")) or "market"
            row_model = normalize_text(str(analysis_context.get("model") or row.get("model_name") or ""))
            if row_mode == target_config.analysis_mode and (not row_model or row_model == normalized_target_model):
                if float(row.get("estimated_cost_usd") or 0.0) > 0:
                    mode_rows.append(row)
        return mode_rows

    def _estimate_avg_request_cost_usd(target_config: AppConfig) -> tuple[float, str]:
        mode_rows = _matching_mode_rows(target_config)
        recent_samples = mode_rows[:12]
        if recent_samples:
            return (
                round(
                    sum(float(row.get("estimated_cost_usd") or 0.0) for row in recent_samples) / len(recent_samples),
                    6,
                ),
                "直近平均",
            )

        heuristic_input_tokens = max(1400, min(int(target_config.max_output_tokens) * 4, 3200))
        effective_retention = resolve_prompt_cache_retention(target_config.model, target_config.prompt_cache_retention)
        heuristic_cached_tokens = int(heuristic_input_tokens * 0.45) if target_config.repeat_count > 1 and effective_retention else 0
        heuristic_usage = {
            "input_tokens": heuristic_input_tokens,
            "output_tokens": min(max(int(target_config.max_output_tokens * 0.28), 280), 800),
            "input_tokens_details": {"cached_tokens": heuristic_cached_tokens},
        }
        return (estimate_cost_usd(heuristic_usage, 1, target_config), "簡易見積")

    def _resolve_batch_job_config(batch_job: dict[str, Any]) -> AppConfig:
        raw_config = batch_job.get("config_json")
        if isinstance(raw_config, str) and raw_config.strip():
            try:
                return AppConfig.model_validate_json(raw_config)
            except Exception:
                pass
        if isinstance(raw_config, dict):
            try:
                return AppConfig.model_validate(raw_config)
            except Exception:
                pass
        return config

    def _resolve_batch_job_remaining_count(batch_job: dict[str, Any]) -> int:
        request_count = max(0, int(batch_job.get("request_count") or 0))
        imported_count = int(batch_job.get("imported_result_count") or 0) + int(batch_job.get("imported_error_count") or 0)
        return max(0, request_count - imported_count)

    def _should_reserve_batch_cost(batch_job: dict[str, Any]) -> bool:
        remaining_count = _resolve_batch_job_remaining_count(batch_job)
        if remaining_count <= 0:
            return False
        status = normalize_text(str(batch_job.get("status") or ""))
        output_file_id = str(batch_job.get("output_file_id") or "").strip()
        error_file_id = str(batch_job.get("error_file_id") or "").strip()
        completed_count = int(batch_job.get("request_counts_completed") or 0) + int(batch_job.get("request_counts_failed") or 0)
        if status in {"failed", "cancelled", "expired"} and not output_file_id and not error_file_id and completed_count <= 0:
            return False
        submitted_at = float(batch_job.get("submitted_at") or batch_job.get("created_at") or 0.0)
        if submitted_at <= 0:
            return False
        return dt.datetime.fromtimestamp(submitted_at).date() == today

    def _resolve_remaining_reserved_cost_usd(batch_job: dict[str, Any]) -> float:
        request_count = max(0, int(batch_job.get("request_count") or 0))
        remaining_count = _resolve_batch_job_remaining_count(batch_job)
        if request_count <= 0 or remaining_count <= 0:
            return 0.0
        reserved_total_usd = float(batch_job.get("reserved_cost_usd") or 0.0)
        if reserved_total_usd <= 0:
            batch_config = _resolve_batch_job_config(batch_job)
            reserved_avg_cost_usd, _ = _estimate_avg_request_cost_usd(batch_config)
            reserved_total_usd = round(reserved_avg_cost_usd * request_count, 6)
        per_request_reserved_usd = reserved_total_usd / request_count
        return round(per_request_reserved_usd * remaining_count, 6)

    active_batch_jobs = [batch_job for batch_job in (batch_jobs or []) if _should_reserve_batch_cost(batch_job)]
    today_reserved_cost_usd = round(sum(_resolve_remaining_reserved_cost_usd(batch_job) for batch_job in active_batch_jobs), 6)
    today_reserved_request_count = sum(_resolve_batch_job_remaining_count(batch_job) for batch_job in active_batch_jobs)
    today_committed_usd = round(today_spend_usd + today_reserved_cost_usd, 6)

    avg_request_cost_usd, estimate_basis = _estimate_avg_request_cost_usd(config)

    if planned_request_count is not None:
        request_count = max(0, int(planned_request_count))
    else:
        request_count = len(config.keywords) * int(config.repeat_count or 0)
    estimated_run_cost_usd = round(avg_request_cost_usd * request_count, 6)
    daily_budget_usd = float(config.daily_budget_usd or 0.0)
    effective_run_guardrail_usd = float(
        config.run_budget_guardrail_usd if run_guardrail_usd is None else run_guardrail_usd
    )
    projected_total_usd = round(today_committed_usd + estimated_run_cost_usd, 6)
    remaining_budget_usd = round(max(0.0, daily_budget_usd - today_committed_usd), 6) if daily_budget_usd > 0 else 0.0
    projected_remaining_usd = round(max(0.0, daily_budget_usd - projected_total_usd), 6) if daily_budget_usd > 0 else 0.0
    would_exceed_budget = daily_budget_usd > 0 and projected_total_usd > daily_budget_usd
    would_exceed_run_guardrail = (
        effective_run_guardrail_usd > 0 and estimated_run_cost_usd > effective_run_guardrail_usd
    )
    guardrail_mode = normalize_text(config.budget_guardrail_mode) or "warn"
    run_guardrail_should_block = would_exceed_run_guardrail and guardrail_mode == "stop"

    if daily_budget_usd <= 0:
        status = "unlimited"
        headline = "日次上限は未設定"
        summary = "上限を決めていないため、今回は見積だけ表示します。"
    elif would_exceed_budget and guardrail_mode == "stop":
        status = "blocked"
        headline = "停止条件にかかる見込み"
        summary = "この設定のままでは今日の上限を超える見込みです。回数か質問数を先に絞ってください。"
    elif would_exceed_budget:
        status = "warning"
        headline = "上限超過見込み"
        summary = "今回は実行できますが、日次上限を超える見込みです。回数や質問数の調整を推奨します。"
    elif daily_budget_usd > 0 and projected_total_usd >= daily_budget_usd * 0.8:
        status = "warning"
        headline = "上限に近づいています"
        summary = "今回の実行は可能ですが、今日の残額は少なめです。重要な質問から先に回してください。"
    else:
        status = "ok"
        headline = "上限内で実行できます"
        summary = "現在の設定なら、今日の想定上限の範囲で回せます。"

    mode_rows = _matching_mode_rows(config)
    target_visible_count = sum(1 for row in mode_rows if row.get("target_domain_hit"))
    total_mode_cost_usd = round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in mode_rows), 6)
    cost_per_visible_topic_usd = (
        round(total_mode_cost_usd / target_visible_count, 6) if target_visible_count and total_mode_cost_usd else 0.0
    )

    return {
        "status": status,
        "headline": headline,
        "summary": summary,
        "today_result_count": len(today_rows),
        "today_spend_usd": today_spend_usd,
        "today_reserved_cost_usd": today_reserved_cost_usd,
        "today_reserved_request_count": today_reserved_request_count,
        "today_committed_usd": today_committed_usd,
        "projected_request_count": len(today_rows) + today_reserved_request_count + request_count,
        "estimated_run_cost_usd": estimated_run_cost_usd,
        "avg_request_cost_usd": avg_request_cost_usd,
        "estimate_basis": estimate_basis,
        "request_count": request_count,
        "run_guardrail_usd": round(effective_run_guardrail_usd, 6),
        "would_exceed_run_guardrail": would_exceed_run_guardrail,
        "run_guardrail_should_block": run_guardrail_should_block,
        "daily_budget_usd": daily_budget_usd,
        "remaining_budget_usd": remaining_budget_usd,
        "projected_total_usd": projected_total_usd,
        "projected_remaining_usd": projected_remaining_usd,
        "would_exceed_budget": would_exceed_budget,
        "should_block": status == "blocked",
        "budget_guardrail_mode": guardrail_mode,
        "guardrail_mode_label": "上限で停止" if guardrail_mode == "stop" else "上限前に警告",
        "cost_per_visible_topic_usd": cost_per_visible_topic_usd,
        "target_visible_count": target_visible_count,
        "effective_prompt_cache_retention": resolve_prompt_cache_retention(config.model, config.prompt_cache_retention),
    }


def format_timestamp(ts: float | None) -> str:
    if not ts:
        return "-"
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def build_overview_metrics(
    rows: list[dict[str, Any]],
    usd_to_jpy_rate: float = 160.0,
    config: AppConfig | None = None,
) -> dict[str, Any]:
    row_count = len(rows)
    if row_count == 0:
        return {
            "total_runs": 0,
            "trial_count": 0,
            "visible_trial_count": 0,
            "external_trial_count": 0,
            "owned_citation_trial_count": 0,
            "owned_citation_trial_rate": 0,
            "question_count": 0,
            "visible_question_count": 0,
            "external_question_count": 0,
            "owned_citation_question_count": 0,
            "owned_citation_question_rate": 0,
            "citation_total": 0,
            "owned_citation_total": 0,
            "target_hit_rate": 0,
            "brand_hit_rate": 0,
            "external_lead_rate": 0,
            "avg_answer_target_hit_rate": 0,
            "avg_answer_external_lead_rate": 0,
            "avg_score": 0,
            "median_score": 0,
            "score_stddev": 0.0,
            "variance_label": "観測なし",
            "total_cost": 0.0,
            "total_cost_jpy": 0.0,
            "cache_hit_rate": 0.0,
            "total_search_calls": 0,
        }
    trial_count = 0
    target_rate_total = 0.0
    brand_rate_total = 0.0
    external_rate_total = 0.0
    visible_trial_count = 0
    owned_citation_trial_count = 0
    external_trial_count = 0
    citation_total = 0
    owned_citation_total = 0
    score_sum = 0.0
    score_values: list[int | float] = []
    total_cost = 0.0
    total_input_tokens = 0
    cached_tokens = 0
    total_search_calls = 0
    for row in rows:
        row_trial_count = max(
            int(row.get("trial_count") or 0),
            int(row.get("answer_observation_count") or 0),
            int(row.get("result_count") or 0),
            1,
        )
        trial_count += row_trial_count
        target_rate_total += _row_target_hit_rate(row) * row_trial_count
        brand_rate_total += _row_brand_hit_rate(row) * row_trial_count
        external_rate_total += _row_external_lead_rate(row) * row_trial_count
        visible_trial_count += max(
            int(row.get("visible_trial_count") or 0),
            int(row.get("target_hit_count") or 0),
            row_trial_count if row.get("target_domain_hit") and row_trial_count == 1 else 0,
        )
        owned_citation_trial_count += max(
            int(row.get("owned_citation_trial_count") or 0),
            int(row.get("owned_citation_result_count") or 0),
            int(row.get("owned_citation_count") or 0),
        )
        external_trial_count += max(
            int(row.get("external_lead_trial_count") or 0),
            row_trial_count
            if classify_visibility_verdict(
                resolve_visibility_score(row),
                bool(row.get("target_domain_hit")),
                bool(row.get("brand_mention_hit")),
            )
            == "外部サイト優勢"
            and row_trial_count == 1
            else 0,
        )
        score = resolve_visibility_score(row)
        score_sum += score * row_trial_count
        score_values.extend([score] * row_trial_count)
        total_cost += float(row.get("estimated_cost_usd") or 0.0)
        total_input_tokens += int(row.get("input_tokens") or 0)
        cached_tokens += int(row.get("cached_tokens") or 0)
        total_search_calls += int(row.get("web_search_calls") or 0)
        owned_citation_total += max(0, int(row.get("owned_citation_count") or 0))
        citations_raw = row.get("citations_json")
        if not citations_raw:
            continue
        try:
            citations = json.loads(str(citations_raw))
        except Exception:
            citations = []
        if isinstance(citations, list):
            citation_total += len(citations)
    trial_visible_rate = round((visible_trial_count / trial_count) * 100, 1) if trial_count else 0.0
    owned_citation_trial_rate = round((owned_citation_trial_count / trial_count) * 100, 1) if trial_count else 0.0
    trial_external_rate = round((external_trial_count / trial_count) * 100, 1) if trial_count else 0.0
    variance_metrics = build_variance_metrics(score_values, owned_hit_rate=trial_visible_rate, config=config)
    return {
        "total_runs": row_count,
        "trial_count": trial_count,
        "visible_trial_count": visible_trial_count,
        "external_trial_count": external_trial_count,
        "owned_citation_trial_count": owned_citation_trial_count,
        "owned_citation_trial_rate": owned_citation_trial_rate,
        "question_count": trial_count,
        "visible_question_count": visible_trial_count,
        "external_question_count": external_trial_count,
        "owned_citation_question_count": owned_citation_trial_count,
        "owned_citation_question_rate": owned_citation_trial_rate,
        "citation_total": citation_total,
        "owned_citation_total": owned_citation_total,
        "target_hit_rate": trial_visible_rate,
        "brand_hit_rate": round((brand_rate_total / trial_count), 1) if trial_count else 0.0,
        "external_lead_rate": trial_external_rate,
        "avg_answer_target_hit_rate": round(target_rate_total / trial_count, 1) if trial_count else 0.0,
        "avg_answer_external_lead_rate": round(external_rate_total / trial_count, 1) if trial_count else 0.0,
        "avg_score": round(score_sum / trial_count, 1) if trial_count else 0.0,
        "median_score": variance_metrics["median_score"],
        "score_stddev": variance_metrics["score_stddev"],
        "variance_label": variance_metrics["variance_label"],
        "total_cost": round(total_cost, 4),
        "total_cost_jpy": usd_to_jpy(total_cost, usd_to_jpy_rate),
        "cache_hit_rate": round((cached_tokens / total_input_tokens) * 100, 1)
        if total_input_tokens
        else 0.0,
        "total_search_calls": total_search_calls,
    }


def build_keyword_score_series(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest_by_keyword: dict[str, dict[str, Any]] = {}
    for row in rows:
        keyword = row.get("keyword_raw") or ""
        if keyword not in latest_by_keyword:
            latest_by_keyword[keyword] = row
    return [
        {
            "keyword": keyword,
            "score": int(data.get("visibility_score") or 0),
            "cost": float(data.get("estimated_cost_usd") or 0.0),
        }
        for keyword, data in latest_by_keyword.items()
    ]


def build_daily_history(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    daily: dict[str, dict[str, float]] = defaultdict(
        lambda: {"runs": 0, "target_hits": 0, "cost": 0.0}
    )
    for row in rows:
        day = format_timestamp(row.get("analyzed_at"))[:10]
        entry = daily[day]
        entry["runs"] += 1
        entry["target_hits"] += 1 if row.get("target_domain_hit") else 0
        entry["cost"] += float(row.get("estimated_cost_usd") or 0.0)
    return [
        {
            "day": day,
            "runs": values["runs"],
            "target_hits": values["target_hits"],
            "cost": round(values["cost"], 4),
        }
        for day, values in sorted(daily.items())
    ]


