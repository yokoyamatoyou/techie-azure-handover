from __future__ import annotations

import json
from typing import Any

from analysis_lib import build_cluster_brief_candidates
from config import AppConfig


def resolve_cluster_brief_candidate(
    scoped_rows: list[dict[str, Any]],
    config: AppConfig,
    selected_token: str,
) -> tuple[str, str, dict[str, Any] | None, list[dict[str, Any]]]:
    cluster_kind, _, cluster_key = str(selected_token or "").partition("::")
    if not cluster_kind or not cluster_key:
        return "", "", None, []
    candidates = build_cluster_brief_candidates(scoped_rows, config)
    candidate = next(
        (
            item
            for item in candidates
            if item["cluster_kind"] == cluster_kind and str(item["cluster_key"]) == cluster_key
        ),
        None,
    )
    if not candidate:
        return cluster_kind, cluster_key, None, []
    row_by_id = {str(row.get("result_id") or ""): row for row in scoped_rows}
    cluster_rows = [
        row_by_id[result_id]
        for result_id in candidate.get("source_result_ids") or []
        if result_id in row_by_id
    ]
    return cluster_kind, cluster_key, candidate, cluster_rows


def build_cluster_brief_save_payload(
    brief: dict[str, Any],
    cluster_kind: str,
    cluster_key: str,
    candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    candidate_data = candidate or {}
    return {
        "cluster_kind": str(brief.get("cluster_kind") or cluster_kind),
        "cluster_key": str(brief.get("cluster_key") or cluster_key),
        "cluster_label": str(brief.get("cluster_label") or candidate_data.get("cluster_label") or ""),
        "source_run_ids_json": json.dumps(brief.get("source_run_ids") or [], ensure_ascii=False),
        "source_result_ids_json": json.dumps(brief.get("source_result_ids") or [], ensure_ascii=False),
        "query_count": int(brief.get("source_query_count") or candidate_data.get("query_count") or 0),
        "generated_title": str(brief.get("brief_title") or ""),
        "brief_json": json.dumps(brief, ensure_ascii=False),
    }
