from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from analysis_core.common import *
from analysis_core.structures import *


def _resolve_row_timestamp(row: dict[str, Any]) -> float:
    return float(
        row.get("scheduled_for")
        or row.get("run_started_at")
        or row.get("analyzed_at")
        or 0.0
    )

def _build_brief_headings(page_type: str, subject: str) -> list[str]:
    templates = BRIEF_HEADING_TEMPLATES.get(page_type, BRIEF_HEADING_TEMPLATES["論点整理ページ"])
    return [template.format(keyword=subject) for template in templates]


def _build_brief_faqs(intent_key: str) -> list[dict[str, str]]:
    faq_seed = BRIEF_FAQ_TEMPLATES.get(intent_key, BRIEF_FAQ_TEMPLATES["general"])
    return [{"question": item[0], "answer_hint": item[1]} for item in faq_seed]


def _build_row_planning_snapshot(row: dict[str, Any], config: AppConfig) -> dict[str, Any]:
    payload = parse_json_object(row.get("output_json"))
    analysis_context = payload.get("analysis_context") or {}
    keyword = normalize_text(str(row.get("keyword_raw") or payload.get("keyword_raw") or ""))
    answer_text = normalize_text(str(row.get("answer_text") or payload.get("answer_text") or ""))
    answer_structure = build_answer_structure_fields(row, config)
    score = resolve_visibility_score(row, payload)
    intent = classify_keyword_intent(keyword, brand_terms=analysis_context.get("brand_terms") or config.brand_terms)
    page_gap = infer_page_gap(
        keyword,
        payload,
        brand_terms=analysis_context.get("brand_terms") or config.brand_terms,
        target_hit=bool(answer_structure.get("owned_domain_hit")),
        brand_hit=bool(answer_structure.get("owned_brand_hit")),
    )
    verdict = classify_visibility_verdict(
        score,
        bool(answer_structure.get("owned_domain_hit")),
        bool(answer_structure.get("owned_brand_hit")),
    )
    return {
        "row": row,
        "payload": payload,
        "analysis_context": analysis_context,
        "keyword": keyword,
        "answer_text": answer_text,
        "answer_excerpt": answer_text[:160] + ("…" if len(answer_text) > 160 else ""),
        "answer_structure": answer_structure,
        "intent": intent,
        "page_gap": page_gap,
        "verdict": verdict,
        "score": score,
        "raw_llm_score": resolve_raw_llm_score(row, payload),
        "target_hit": bool(answer_structure.get("owned_domain_hit")),
        "brand_hit": bool(answer_structure.get("owned_brand_hit")),
    }


def _select_latest_rows_by_query(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest_by_query: dict[str, dict[str, Any]] = {}
    for row in rows:
        query_key = normalize_text(str(row.get("keyword_raw") or row.get("keyword_norm") or row.get("result_id") or ""))
        if not query_key:
            continue
        current = latest_by_query.get(query_key)
        if current is None or _resolve_row_timestamp(row) >= _resolve_row_timestamp(current):
            latest_by_query[query_key] = row
    return sorted(latest_by_query.values(), key=_resolve_row_timestamp, reverse=True)


def build_page_brief_draft(row: dict[str, Any], config: AppConfig) -> dict[str, Any]:
    snapshot = _build_row_planning_snapshot(row, config)
    page_type = snapshot["page_gap"]["page_type_label"]
    keyword = snapshot["keyword"]
    answer_signals = snapshot["answer_structure"]
    title = f"{BRIEF_TITLE_PREFIX_MAP.get(page_type, '判断材料を揃える')} | {keyword}"
    intent_summary = (
        f"この query は {snapshot['intent']['label']} 意図が強く、現状は {snapshot['verdict']} です。"
        f" AI 回答では {page_type} が不足しやすく、{snapshot['page_gap']['next_step']} を先に満たす構成が必要です。"
    )
    if snapshot["answer_excerpt"]:
        intent_summary += f" 保存された返答では「{snapshot['answer_excerpt']}」という方向で整理されています。"

    return {
        "page_type": page_type,
        "title": title,
        "audience": BRIEF_AUDIENCE_MAP.get(snapshot["intent"]["primary"], BRIEF_AUDIENCE_MAP["general"]),
        "intent_summary": intent_summary,
        "headings": _build_brief_headings(page_type, keyword),
        "faqs": _build_brief_faqs(snapshot["intent"]["primary"]),
        "cta": BRIEF_CTA_MAP.get(page_type, "条件を整理して相談する"),
        "reference_query": keyword,
        "reference_answer_summary": snapshot["answer_excerpt"] or str(snapshot["payload"].get("answer_snapshot") or ""),
        "reference_citation_domains": answer_signals["citation_domains"][:4],
        "reference_brands": answer_signals["mentioned_brands"][:5],
        "answer_type_label": answer_signals["answer_type_label"],
    }


def build_cluster_brief_candidates(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, Any]]:
    latest_rows = _select_latest_rows_by_query(rows)
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in latest_rows:
        snapshot = _build_row_planning_snapshot(row, config)
        grouped[("intent", snapshot["intent"]["primary"], snapshot["intent"]["label"])].append(snapshot)
        grouped[("page_gap", snapshot["page_gap"]["page_type_label"], snapshot["page_gap"]["page_type_label"])].append(snapshot)
        question_set_id = normalize_text(str(row.get("question_set_id") or "")) or "ad-hoc"
        question_set_label = str(row.get("question_set_name") or "ad-hoc")
        grouped[("question_set", question_set_id, question_set_label)].append(snapshot)

    candidates: list[dict[str, Any]] = []
    for (cluster_kind, cluster_key, cluster_label), items in grouped.items():
        unique_queries = dedupe_preserve_order([item["keyword"] for item in items if item["keyword"]])
        needs_fix_count = sum(1 for item in items if item["verdict"] in {"外部サイト優勢", "未露出"})
        page_type_counts = Counter(item["page_gap"]["page_type_label"] for item in items)
        recommended_page_type = page_type_counts.most_common(1)[0][0] if page_type_counts else "論点整理ページ"
        candidates.append(
            {
                "cluster_kind": cluster_kind,
                "cluster_kind_label": CLUSTER_KIND_LABELS.get(cluster_kind, cluster_kind),
                "cluster_key": cluster_key,
                "cluster_label": cluster_label,
                "query_count": len(unique_queries),
                "result_count": len(items),
                "needs_fix_count": needs_fix_count,
                "recommended_page_type": recommended_page_type,
                "representative_queries": unique_queries[:3],
                "source_result_ids": [str(item["row"].get("result_id") or "") for item in items if item["row"].get("result_id")],
            }
        )
    return sorted(
        candidates,
        key=lambda item: (
            {"intent": 0, "page_gap": 1, "question_set": 2}.get(item["cluster_kind"], 9),
            -int(item["needs_fix_count"]),
            -int(item["query_count"]),
            str(item["cluster_label"]),
        ),
    )


def build_cluster_brief_draft(
    rows: list[dict[str, Any]],
    cluster_kind: str,
    cluster_key: str,
    cluster_label: str,
    config: AppConfig,
) -> dict[str, Any]:
    insights = [_build_row_planning_snapshot(row, config) for row in _select_latest_rows_by_query(rows)]
    if not insights:
        return {
            "cluster_kind": cluster_kind,
            "cluster_kind_label": CLUSTER_KIND_LABELS.get(cluster_kind, cluster_kind),
            "cluster_key": cluster_key,
            "cluster_label": cluster_label,
            "page_type": "論点整理ページ",
            "brief_title": f"{cluster_label} brief",
            "intent_cluster_summary": "保存済みの cluster 行がありません。",
            "lead_query": "",
            "representative_queries": [],
            "representative_citation_domains": [],
            "headings": [],
            "faqs": [],
            "cta": "条件を整理して相談する",
            "brief_summary": "cluster brief を作るには結果が必要です。",
            "answer_type_labels": [],
            "source_run_ids": [],
            "source_result_ids": [],
            "source_query_count": 0,
            "source_result_count": 0,
        }

    intent_counts = Counter(item["intent"]["label"] for item in insights)
    intent_key_counts = Counter(item["intent"]["primary"] for item in insights)
    page_gap_counts = Counter(item["page_gap"]["page_type_label"] for item in insights)
    verdict_counts = Counter(item["verdict"] for item in insights)
    answer_type_counts = Counter(item["answer_structure"]["answer_type_label"] for item in insights)
    citation_domain_counts: Counter[str] = Counter()
    brand_counts: Counter[str] = Counter()
    for item in insights:
        citation_domain_counts.update(item["answer_structure"]["citation_domains"])
        brand_counts.update(item["answer_structure"]["mentioned_brands"])

    verdict_rank = {"未露出": 0, "外部サイト優勢": 1, "自社あり": 2, "自社優勢": 3}
    representative_queries = [
        item["keyword"]
        for item in sorted(
            insights,
            key=lambda item: (
                verdict_rank.get(item["verdict"], 9),
                item["score"],
                item["keyword"],
            ),
        )
        if item["keyword"]
    ][:4]
    top_intents = [label for label, _count in intent_counts.most_common(2)]
    top_domains = [domain for domain, _count in citation_domain_counts.most_common(5)]
    page_type = page_gap_counts.most_common(1)[0][0] if page_gap_counts else "論点整理ページ"
    primary_intent_key = intent_key_counts.most_common(1)[0][0] if intent_key_counts else "general"
    lead_query = representative_queries[0] if representative_queries else cluster_label
    needs_fix_count = verdict_counts.get("外部サイト優勢", 0) + verdict_counts.get("未露出", 0)
    total_queries = len(insights)
    intent_cluster_summary = (
        f"{cluster_label} は {join_csv(top_intents) if top_intents else '探索'} のまとまりで、"
        f" {total_queries}質問中 {needs_fix_count}質問が外部サイト優勢または未露出です。"
    )
    brief_summary = (
        f"{CLUSTER_KIND_LABELS.get(cluster_kind, cluster_kind)} の {cluster_label} では、"
        f" 代表 query は {join_csv(representative_queries[:3]) or '未設定'}、引用は {join_csv(top_domains[:3]) or '根拠不足'} が中心です。"
        f" まず {page_type} を1本作り、{needs_fix_count}件の負け筋をまとめて拾える構成に寄せます。"
    )
    title_prefix = BRIEF_TITLE_PREFIX_MAP.get(page_type, "判断材料を揃える")
    if cluster_kind == "question_set":
        brief_title = f"{cluster_label} 向け {page_type} brief"
    else:
        brief_title = f"{title_prefix} | {cluster_label}"

    return {
        "cluster_kind": cluster_kind,
        "cluster_kind_label": CLUSTER_KIND_LABELS.get(cluster_kind, cluster_kind),
        "cluster_key": cluster_key,
        "cluster_label": cluster_label,
        "page_type": page_type,
        "brief_title": brief_title,
        "intent_cluster_summary": intent_cluster_summary,
        "lead_query": lead_query,
        "representative_queries": representative_queries,
        "representative_citation_domains": top_domains,
        "headings": _build_brief_headings(page_type, lead_query or cluster_label),
        "faqs": _build_brief_faqs(primary_intent_key),
        "cta": BRIEF_CTA_MAP.get(page_type, "条件を整理して相談する"),
        "brief_summary": brief_summary,
        "answer_type_labels": [label for label, _count in answer_type_counts.most_common(3)],
        "reference_brands": [brand for brand, _count in brand_counts.most_common(5)],
        "source_run_ids": dedupe_preserve_order([str(item["row"].get("run_id") or "") for item in insights if item["row"].get("run_id")]),
        "source_result_ids": [str(item["row"].get("result_id") or "") for item in insights if item["row"].get("result_id")],
        "source_query_count": len({item["keyword"] for item in insights if item["keyword"]}),
        "source_result_count": len(insights),
    }


def build_run_outcome_snapshot(rows: list[dict[str, Any]], config: AppConfig, *, label: str = "") -> dict[str, Any]:
    if not rows:
        return {
            "label": label,
            "run_ids": [],
            "result_count": 0,
            "query_count": 0,
            "visibility_rate": 0.0,
            "avg_visibility_score": 0.0,
            "median_visibility_score": 0.0,
            "min_visibility_score": 0.0,
            "max_visibility_score": 0.0,
            "score_stddev": 0.0,
            "variance_label": "観測なし",
            "owned_mention_rate": 0.0,
            "competitor_mention_rate": 0.0,
            "intent_distribution": [],
            "page_gap_distribution": [],
            "top_citation_domains": [],
        }

    intent_counts: Counter[str] = Counter()
    page_gap_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    visible_count = 0
    owned_mention_count = 0
    competitor_mention_count = 0
    score_values: list[int] = []
    query_keys: set[str] = set()

    for row in rows:
        snapshot = _build_row_planning_snapshot(row, config)
        visible_count += 1 if row.get("target_domain_hit") else 0
        owned_mention_count += 1 if snapshot["answer_structure"]["owned_mention_hit"] else 0
        competitor_mention_count += 1 if snapshot["answer_structure"]["competitor_mention_hit"] else 0
        score_values.append(snapshot["score"])
        intent_counts.update([snapshot["intent"]["label"]])
        page_gap_counts.update([snapshot["page_gap"]["page_type_label"]])
        domain_counts.update(set(snapshot["answer_structure"]["citation_domains"]))
        if snapshot["keyword"]:
            query_keys.add(snapshot["keyword"])

    result_count = len(rows)
    visibility_rate = round((visible_count / result_count) * 100, 1) if result_count else 0.0
    variance_metrics = build_variance_metrics(score_values, owned_hit_rate=visibility_rate, config=config)
    return {
        "label": label,
        "run_ids": dedupe_preserve_order([str(row.get("run_id") or "") for row in rows if row.get("run_id")]),
        "result_count": result_count,
        "query_count": len(query_keys),
        "visibility_rate": visibility_rate,
        "avg_visibility_score": round(sum(score_values) / result_count, 1) if result_count else 0.0,
        "median_visibility_score": variance_metrics["median_score"],
        "min_visibility_score": variance_metrics["min_score"],
        "max_visibility_score": variance_metrics["max_score"],
        "score_stddev": variance_metrics["score_stddev"],
        "variance_label": variance_metrics["variance_label"],
        "owned_mention_rate": round((owned_mention_count / result_count) * 100, 1) if result_count else 0.0,
        "competitor_mention_rate": round((competitor_mention_count / result_count) * 100, 1) if result_count else 0.0,
        "intent_distribution": [
            {"label": label, "count": count, "rate": round((count / result_count) * 100, 1)}
            for label, count in intent_counts.most_common()
        ],
        "page_gap_distribution": [
            {"label": label, "count": count, "rate": round((count / result_count) * 100, 1)}
            for label, count in page_gap_counts.most_common()
        ],
        "top_citation_domains": [
            {"domain": domain, "count": count, "rate": round((count / result_count) * 100, 1)}
            for domain, count in domain_counts.most_common(6)
        ],
    }


def build_run_outcome_compare(
    left_rows: list[dict[str, Any]],
    right_rows: list[dict[str, Any]],
    config: AppConfig,
    *,
    left_label: str,
    right_label: str,
) -> dict[str, Any]:
    left = build_run_outcome_snapshot(left_rows, config, label=left_label)
    right = build_run_outcome_snapshot(right_rows, config, label=right_label)
    intent_counter = Counter()
    page_gap_counter = Counter()
    domain_counter = Counter()
    for item in left["intent_distribution"]:
        intent_counter.update({item["label"]: item["count"]})
    for item in right["intent_distribution"]:
        intent_counter.update({item["label"]: item["count"]})
    for item in left["page_gap_distribution"]:
        page_gap_counter.update({item["label"]: item["count"]})
    for item in right["page_gap_distribution"]:
        page_gap_counter.update({item["label"]: item["count"]})
    for item in left["top_citation_domains"]:
        domain_counter.update({item["domain"]: item["count"]})
    for item in right["top_citation_domains"]:
        domain_counter.update({item["domain"]: item["count"]})

    left_intent_map = {item["label"]: item for item in left["intent_distribution"]}
    right_intent_map = {item["label"]: item for item in right["intent_distribution"]}
    left_gap_map = {item["label"]: item for item in left["page_gap_distribution"]}
    right_gap_map = {item["label"]: item for item in right["page_gap_distribution"]}
    left_domain_map = {item["domain"]: item for item in left["top_citation_domains"]}
    right_domain_map = {item["domain"]: item for item in right["top_citation_domains"]}

    visibility_delta = round(right["visibility_rate"] - left["visibility_rate"], 1)
    owned_delta = round(right["owned_mention_rate"] - left["owned_mention_rate"], 1)
    competitor_delta = round(right["competitor_mention_rate"] - left["competitor_mention_rate"], 1)
    headline = (
        f"{right_label} は {left_label} 比で visibility {'改善' if visibility_delta > 0 else '悪化' if visibility_delta < 0 else '横ばい'}"
    )
    summary = (
        f"visibility {left['visibility_rate']}% → {right['visibility_rate']}%、"
        f" 自社出現 {left['owned_mention_rate']}% → {right['owned_mention_rate']}%、"
        f" 競合出現 {left['competitor_mention_rate']}% → {right['competitor_mention_rate']}% です。"
    )

    return {
        "left": left,
        "right": right,
        "headline": headline,
        "summary": summary,
        "visibility_delta": visibility_delta,
        "owned_mention_delta": owned_delta,
        "competitor_mention_delta": competitor_delta,
        "intent_rows": [
            {
                "label": label,
                "left_rate": float(left_intent_map.get(label, {}).get("rate", 0.0)),
                "right_rate": float(right_intent_map.get(label, {}).get("rate", 0.0)),
                "delta": round(
                    float(right_intent_map.get(label, {}).get("rate", 0.0))
                    - float(left_intent_map.get(label, {}).get("rate", 0.0)),
                    1,
                ),
            }
            for label, _count in intent_counter.most_common(5)
        ],
        "page_gap_rows": [
            {
                "label": label,
                "left_rate": float(left_gap_map.get(label, {}).get("rate", 0.0)),
                "right_rate": float(right_gap_map.get(label, {}).get("rate", 0.0)),
                "delta": round(
                    float(right_gap_map.get(label, {}).get("rate", 0.0))
                    - float(left_gap_map.get(label, {}).get("rate", 0.0)),
                    1,
                ),
            }
            for label, _count in page_gap_counter.most_common(5)
        ],
        "citation_domain_rows": [
            {
                "domain": domain,
                "left_rate": float(left_domain_map.get(domain, {}).get("rate", 0.0)),
                "right_rate": float(right_domain_map.get(domain, {}).get("rate", 0.0)),
                "delta": round(
                    float(right_domain_map.get(domain, {}).get("rate", 0.0))
                    - float(left_domain_map.get(domain, {}).get("rate", 0.0)),
                    1,
                ),
            }
            for domain, _count in domain_counter.most_common(6)
        ],
    }


