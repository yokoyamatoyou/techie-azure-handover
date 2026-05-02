from __future__ import annotations

import datetime as dt
import json
from collections import Counter, defaultdict
from typing import Any

from analysis_core.common import *
from analysis_core.metrics import _row_external_lead_rate, _row_target_hit_rate, format_timestamp, resolve_analysis_mode
from analysis_core.source_evidence import resolve_citation_records, resolve_prompt_taxonomy_entry as resolve_prompt_taxonomy_entry_with_fallback
from analysis_core.structures import *


_CSV_FORMULA_PREFIXES = ("=", "+", "-", "@")


def _sanitize_csv_cell(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if not value:
        return value
    if value[0] in _CSV_FORMULA_PREFIXES or value[0] in {"\t", "\r", "\n"}:
        return f"'{value}"
    return value


def _sanitize_csv_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: _sanitize_csv_cell(value) for key, value in row.items()}


def _resolve_prompt_taxonomy_entry(row: dict[str, Any]) -> dict[str, Any]:
    return resolve_prompt_taxonomy_entry_with_fallback(row)


def _resolve_row_timestamp(row: dict[str, Any]) -> float:
    return float(
        row.get("scheduled_for")
        or row.get("run_started_at")
        or row.get("analyzed_at")
        or 0.0
    )


def _build_run_rollups(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        run_id = str(row.get("run_id") or "")
        if not run_id:
            continue
        payload = parse_json_object(row.get("output_json"))
        analysis_context = payload.get("analysis_context") or {}
        keyword = str(row.get("keyword_raw") or "")
        score = resolve_visibility_score(row)
        run_bucket = grouped.setdefault(
            run_id,
            {
                "run_id": run_id,
                "timestamp": _resolve_row_timestamp(row),
                "question_set_name": str(row.get("question_set_name") or ""),
                "run_mode": str(row.get("run_mode") or "manual"),
                "scores": [],
                "visible": 0,
                "external_lead": 0,
                "total": 0,
                "intent_scores": defaultdict(list),
                "page_gap_counts": Counter(),
            },
        )
        run_bucket["scores"].append(score)
        run_bucket["visible"] += 1 if row.get("target_domain_hit") else 0
        run_bucket["total"] += 1

        intent = classify_keyword_intent(
            keyword,
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
        )
        page_gap = infer_page_gap(
            keyword,
            payload,
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
            target_hit=bool(row.get("target_domain_hit")),
            brand_hit=bool(row.get("brand_mention_hit")),
        )
        verdict = classify_visibility_verdict(
            score,
            bool(row.get("target_domain_hit")),
            bool(row.get("brand_mention_hit")),
        )
        run_bucket["intent_scores"][intent["label"]].append(score)
        if verdict == "外部サイト優勢":
            run_bucket["external_lead"] += 1
        if verdict in {"外部サイト優勢", "未露出"}:
            run_bucket["page_gap_counts"][page_gap["page_type_label"]] += 1

    rollups: list[dict[str, Any]] = []
    for bucket in grouped.values():
        avg_score = round(sum(bucket["scores"]) / len(bucket["scores"]), 1) if bucket["scores"] else 0.0
        visible_rate = round((bucket["visible"] / bucket["total"]) * 100, 1) if bucket["total"] else 0.0
        external_lead_rate = round((bucket["external_lead"] / bucket["total"]) * 100, 1) if bucket["total"] else 0.0
        variance_metrics = build_variance_metrics(bucket["scores"], owned_hit_rate=visible_rate, config=config)
        intent_scores = {
            label: round(sum(values) / len(values), 1)
            for label, values in bucket["intent_scores"].items()
            if values
        }
        rollups.append(
            {
                "run_id": bucket["run_id"],
                "timestamp": bucket["timestamp"],
                "visible_rate": visible_rate,
                "external_lead_rate": external_lead_rate,
                "avg_score": avg_score,
                "median_score": variance_metrics["median_score"],
                "min_score": variance_metrics["min_score"],
                "max_score": variance_metrics["max_score"],
                "score_stddev": variance_metrics["score_stddev"],
                "variance_label": variance_metrics["variance_label"],
                "question_set_name": bucket["question_set_name"],
                "run_mode": bucket["run_mode"],
                "intent_scores": intent_scores,
                "page_gap_counts": dict(bucket["page_gap_counts"]),
                "total_trials": bucket["total"],
            }
        )
    return sorted(rollups, key=lambda item: item["timestamp"])


def build_overall_visibility_series(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    series = []
    for rollup in _build_run_rollups(rows, config):
        series.append(
            {
                "timestamp": format_timestamp(rollup["timestamp"]),
                "avg_score": rollup["avg_score"],
                "score_stddev": rollup["score_stddev"],
                "variance_label": rollup["variance_label"],
                "visible_rate": rollup["visible_rate"],
                "run_mode": rollup["run_mode"],
                "question_set_name": rollup["question_set_name"] or "-",
            }
        )
    return series


def build_visibility_focus_series(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    series = []
    for rollup in _build_run_rollups(rows, config):
        series.append(
            {
                "timestamp": format_timestamp(rollup["timestamp"]),
                "visible_rate": rollup["visible_rate"],
                "external_lead_rate": rollup["external_lead_rate"],
                "score_stddev": rollup["score_stddev"],
                "variance_label": rollup["variance_label"],
                "run_mode": rollup["run_mode"],
                "question_set_name": rollup["question_set_name"] or "-",
                "total_trials": rollup["total_trials"],
            }
        )
    return series


def build_intent_cluster_series(rows: list[dict[str, Any]], config: AppConfig, limit: int = 4) -> list[dict[str, Any]]:
    rollups = _build_run_rollups(rows, config)
    intent_frequency: Counter[str] = Counter()
    for rollup in rollups:
        intent_frequency.update(rollup["intent_scores"].keys())
    selected_intents = [label for label, _ in intent_frequency.most_common(limit)]
    series: list[dict[str, Any]] = []
    for intent_label in selected_intents:
        points = []
        for rollup in rollups:
            if intent_label not in rollup["intent_scores"]:
                continue
            points.append(
                {
                    "timestamp": format_timestamp(rollup["timestamp"]),
                    "score": rollup["intent_scores"][intent_label],
                    "run_mode": rollup["run_mode"],
                }
            )
        if points:
            series.append({"label": intent_label, "points": points})
    return series


def build_page_gap_trend_series(rows: list[dict[str, Any]], config: AppConfig, limit: int = 4) -> list[dict[str, Any]]:
    rollups = _build_run_rollups(rows, config)
    gap_frequency: Counter[str] = Counter()
    for rollup in rollups:
        gap_frequency.update(rollup["page_gap_counts"].keys())
    selected_gaps = [label for label, _ in gap_frequency.most_common(limit)]
    series: list[dict[str, Any]] = []
    for page_type_label in selected_gaps:
        points = []
        for rollup in rollups:
            points.append(
                {
                    "timestamp": format_timestamp(rollup["timestamp"]),
                    "count": int(rollup["page_gap_counts"].get(page_type_label) or 0),
                    "run_mode": rollup["run_mode"],
                }
            )
        if any(point["count"] > 0 for point in points):
            series.append({"label": page_type_label, "points": points})
    return series


def build_query_drilldown_series(rows: list[dict[str, Any]], keyword: str) -> list[dict[str, Any]]:
    target_keyword = normalize_text(keyword)
    if not target_keyword:
        return []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if normalize_text(str(row.get("keyword_raw") or "")) != target_keyword:
            continue
        run_id = str(row.get("run_id") or "")
        group_key = run_id or f"row::{row.get('result_id') or row.get('analyzed_at')}"
        grouped.setdefault(group_key, []).append(row)

    series: list[dict[str, Any]] = []
    for group_rows in sorted(grouped.values(), key=lambda items: _resolve_row_timestamp(max(items, key=_resolve_row_timestamp))):
        latest_row = max(group_rows, key=_resolve_row_timestamp)
        avg_score = round(sum(int(row.get("visibility_score") or 0) for row in group_rows) / len(group_rows), 1)
        target_rate = round(sum(1 for row in group_rows if row.get("target_domain_hit")) / len(group_rows) * 100, 1)
        brand_rate = round(sum(1 for row in group_rows if row.get("brand_mention_hit")) / len(group_rows) * 100, 1)
        verdict = classify_visibility_verdict(
            int(round(avg_score)),
            target_rate > 0,
            brand_rate > 0,
        )
        series.append(
            {
                "timestamp": format_timestamp(_resolve_row_timestamp(latest_row)),
                "score": avg_score,
                "verdict": verdict,
                "run_mode": str(latest_row.get("run_mode") or "manual"),
            }
        )
    return series


def build_previous_delta_summary(current_rows: list[dict[str, Any]], previous_rows: list[dict[str, Any]]) -> dict[str, Any]:
    def summarize(rows: list[dict[str, Any]]) -> dict[str, float]:
        if not rows:
            return {
                "target_hit_rate": 0.0,
                "avg_visibility_score": 0.0,
                "score_stddev": 0.0,
                "external_lead_rate": 0.0,
            }
        total = len(rows)
        score_values = [float(resolve_visibility_score(row)) for row in rows]
        variance_metrics = build_variance_metrics(score_values, owned_hit_rate=round(sum(_row_target_hit_rate(row) for row in rows) / total, 1))
        return {
            "target_hit_rate": round(sum(_row_target_hit_rate(row) for row in rows) / total, 1),
            "avg_visibility_score": round(sum(score_values) / total, 1),
            "score_stddev": float(variance_metrics["score_stddev"]),
            "external_lead_rate": round(sum(_row_external_lead_rate(row) for row in rows) / total, 1),
        }

    previous = summarize(previous_rows)
    current = summarize(current_rows)
    return {
        "previous": previous,
        "current": current,
        "target_hit_rate_delta": round(current["target_hit_rate"] - previous["target_hit_rate"], 1),
        "avg_visibility_score_delta": round(current["avg_visibility_score"] - previous["avg_visibility_score"], 1),
        "score_stddev_delta": round(current["score_stddev"] - previous["score_stddev"], 1),
        "external_lead_rate_delta": round(current["external_lead_rate"] - previous["external_lead_rate"], 1),
    }


def build_raw_results_export_rows(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    export_rows: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: float(item.get("analyzed_at") or 0.0)):
        payload = parse_json_object(row.get("output_json"))
        analysis_context = payload.get("analysis_context") or {}
        intent = classify_keyword_intent(
            str(row.get("keyword_raw") or ""),
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
        )
        page_gap = infer_page_gap(
            str(row.get("keyword_raw") or ""),
            payload,
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
            target_hit=bool(row.get("target_domain_hit")),
            brand_hit=bool(row.get("brand_mention_hit")),
        )
        answer_structure = build_answer_structure_fields(row, config)
        citations = resolve_citation_records(row, payload)
        deterministic_score = resolve_visibility_score(row, payload)
        raw_llm_score = resolve_raw_llm_score(row, payload)
        export_rows.append(
            _sanitize_csv_row(
                {
                    "analyzed_at": format_timestamp(row.get("analyzed_at")),
                    "run_id": str(row.get("run_id") or ""),
                    "question_set_name": str(row.get("question_set_name") or ""),
                    "schedule_id": str(row.get("schedule_id") or ""),
                    "run_mode": str(row.get("run_mode") or "manual"),
                    "analysis_mode": resolve_analysis_mode(payload),
                    "keyword_raw": str(row.get("keyword_raw") or ""),
                    "executed_query": str(row.get("executed_query") or row.get("keyword_raw") or ""),
                    "user_query_short": str(row.get("user_query_short") or ""),
                    "query_was_shortened": bool(row.get("query_was_shortened")),
                    "shortening_note": str(row.get("shortening_note") or ""),
                    "expanded_queries_json": str(row.get("expanded_queries_json") or "[]"),
                    "prompt_taxonomy_json": str(row.get("prompt_taxonomy_json") or "[]"),
                    "expansion_mode": str(row.get("expansion_mode") or ""),
                    "expansion_signature": str(row.get("expansion_signature") or ""),
                    "provider_batch_mode": str(row.get("provider_batch_mode") or ""),
                    "provider_batch_id": str(row.get("provider_batch_id") or ""),
                    "provider_cache_policy": str(row.get("provider_cache_policy") or ""),
                    "executed_prompt_label": str(_resolve_prompt_taxonomy_entry(row).get("prompt_label") or ""),
                    "executed_prompt_family": str(_resolve_prompt_taxonomy_entry(row).get("prompt_family") or ""),
                    "intent_label": intent["label"],
                    "page_type_label": page_gap["page_type_label"],
                    "raw_llm_score": raw_llm_score,
                    "deterministic_score": deterministic_score,
                    "visibility_score": deterministic_score,
                    "visibility_label": classify_visibility_verdict(
                        deterministic_score,
                        bool(row.get("target_domain_hit")),
                        bool(row.get("brand_mention_hit")),
                    ),
                    "target_domain_hit": bool(row.get("target_domain_hit")),
                    "brand_mention_hit": bool(row.get("brand_mention_hit")),
                    "owned_citation_count": int(answer_structure["owned_citation_count"]),
                    "owned_citation_share": round(float(answer_structure["owned_citation_share"]) * 100, 1),
                    "owned_mention_hit": bool(answer_structure["owned_mention_hit"]),
                    "competitor_mention_hit": bool(answer_structure["competitor_mention_hit"]),
                    "external_only_result": bool(answer_structure["external_only_result"]),
                    "answer_type_key": answer_structure["answer_type_key"],
                    "answer_type_label": answer_structure["answer_type_label"],
                    "mentioned_brands_json": json.dumps(answer_structure["mentioned_brands"], ensure_ascii=False),
                    "citation_domains_json": json.dumps(answer_structure["citation_domains"], ensure_ascii=False),
                    "answer_snapshot": str(row.get("answer_snapshot") or payload.get("answer_snapshot") or ""),
                    "answer_text": str(row.get("answer_text") or payload.get("answer_text") or ""),
                    "citations_json": json.dumps(citations, ensure_ascii=False),
                    "citation_urls": json.dumps(payload.get("citation_urls") or [item["url"] for item in citations], ensure_ascii=False),
                    "competitor_mentions": json.dumps(payload.get("competitor_mentions") or [], ensure_ascii=False),
                    "error_text": str(row.get("error_text") or ""),
                }
            )
        )
    return export_rows


def build_weekly_summary_rows(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        analyzed_at = float(row.get("analyzed_at") or 0.0)
        if not analyzed_at:
            continue
        week_start = dt.datetime.fromtimestamp(analyzed_at).date() - dt.timedelta(days=dt.datetime.fromtimestamp(analyzed_at).weekday())
        payload = parse_json_object(row.get("output_json"))
        analysis_context = payload.get("analysis_context") or {}
        intent = classify_keyword_intent(
            str(row.get("keyword_raw") or ""),
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
        )
        page_gap = infer_page_gap(
            str(row.get("keyword_raw") or ""),
            payload,
            brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
            target_hit=bool(row.get("target_domain_hit")),
            brand_hit=bool(row.get("brand_mention_hit")),
        )
        answer_structure = build_answer_structure_fields(row, config)
        deterministic_score = resolve_visibility_score(row, payload)
        raw_llm_score = resolve_raw_llm_score(row, payload)
        scopes = [
            ("overall", "overall"),
            ("intent", intent["label"]),
            ("page_type", page_gap["page_type_label"]),
            ("query", str(row.get("keyword_raw") or "")),
            ("answer_type", answer_structure["answer_type_label"]),
        ]
        for scope_type, scope_label in scopes:
            bucket = grouped.setdefault(
                (week_start.isoformat(), scope_type, scope_label),
                {
                    "week_start": week_start.isoformat(),
                    "scope_type": scope_type,
                    "scope_label": scope_label,
                    "result_count": 0,
                    "visible_count": 0,
                    "owned_answer_count": 0,
                    "competitor_answer_count": 0,
                    "score_total": 0,
                    "raw_score_total": 0,
                    "score_values": [],
                    "run_ids": set(),
                },
            )
            bucket["result_count"] += 1
            bucket["visible_count"] += 1 if row.get("target_domain_hit") else 0
            bucket["owned_answer_count"] += 1 if answer_structure["owned_mention_hit"] else 0
            bucket["competitor_answer_count"] += 1 if answer_structure["competitor_mention_hit"] else 0
            bucket["score_total"] += deterministic_score
            bucket["raw_score_total"] += raw_llm_score
            bucket["score_values"].append(float(deterministic_score))
            if row.get("run_id"):
                bucket["run_ids"].add(str(row["run_id"]))

    summary_rows: list[dict[str, Any]] = []
    for bucket in grouped.values():
        result_count = int(bucket["result_count"] or 0)
        visible_rate = round((bucket["visible_count"] / result_count) * 100, 1) if result_count else 0.0
        avg_score = round(bucket["score_total"] / result_count, 1) if result_count else 0.0
        variance_metrics = build_variance_metrics(bucket.get("score_values") or [], owned_hit_rate=visible_rate)
        summary_rows.append(
            _sanitize_csv_row(
                {
                    "week_start": bucket["week_start"],
                    "scope_type": bucket["scope_type"],
                    "scope_label": bucket["scope_label"],
                    "run_count": len(bucket["run_ids"]),
                    "result_count": result_count,
                    "visible_rate": visible_rate,
                    "owned_answer_rate": round((bucket["owned_answer_count"] / result_count) * 100, 1) if result_count else 0.0,
                    "competitor_answer_rate": (
                        round((bucket["competitor_answer_count"] / result_count) * 100, 1) if result_count else 0.0
                    ),
                    "avg_visibility_score": avg_score,
                    "avg_raw_llm_score": round(bucket["raw_score_total"] / result_count, 1) if result_count else 0.0,
                    "median_visibility_score": float(variance_metrics["median_score"]),
                    "min_visibility_score": float(variance_metrics["min_score"]),
                    "max_visibility_score": float(variance_metrics["max_score"]),
                    "score_stddev": float(variance_metrics["score_stddev"]),
                    "variance_label": str(variance_metrics["variance_label"]),
                }
            )
        )
    return sorted(summary_rows, key=lambda item: (item["week_start"], item["scope_type"], item["scope_label"]))
