from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

from config import AppConfig

from analysis_core.common import dedupe_preserve_order, normalize_domain_host, normalize_text, parse_json_object
from analysis_core.structures import parse_citations_json

_PARSE_FAIL_PREFIX = "応答を読み取れませんでした。"


def normalize_url_for_match(raw_value: Any) -> str:
    url = str(raw_value or "").strip()
    if not url:
        return ""
    try:
        parts = urlsplit(url)
    except Exception:
        return normalize_text(url).lower()
    scheme = (parts.scheme or "https").lower()
    netloc = (parts.netloc or "").lower()
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    if scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def resolve_citation_records(row: dict[str, Any], payload: dict[str, Any] | None = None) -> list[dict[str, str]]:
    payload = payload or parse_json_object(row.get("output_json"))
    citations = parse_citations_json(row.get("citations_json") or payload.get("citations") or [])
    if not citations:
        citations = [
            {"url": str(item).strip(), "title": ""}
            for item in (payload.get("citation_urls") or [])
            if str(item or "").strip()
        ]
    deduped: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for item in citations:
        url = str(item.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append({"url": url, "title": str(item.get("title") or "").strip()})
    return deduped


def _resolve_citation_origin(row: dict[str, Any], payload: dict[str, Any]) -> str:
    if row.get("citations_json") or payload.get("citations"):
        return "citations"
    if payload.get("citation_urls"):
        return "citation_urls"
    return ""


def _parse_source_rows(source_rows: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for raw_source in source_rows or []:
        url = str((raw_source or {}).get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(
            {
                "url": url,
                "title": str((raw_source or {}).get("title") or "").strip(),
                "kind": str((raw_source or {}).get("kind") or "source").strip() or "source",
            }
        )
    return deduped


def _build_competitor_terms(payload: dict[str, Any], config: AppConfig) -> list[str]:
    analysis_context = payload.get("analysis_context") or {}
    preset_terms = [
        term
        for preset in config.competitor_presets or []
        for term in [preset.display_name, *preset.aliases]
    ]
    terms = [
        str(item or "")
        for item in [
            *(analysis_context.get("competitor_terms") or config.competitor_terms),
            *preset_terms,
            *(payload.get("competitor_mentions") or []),
        ]
    ]
    return [term for term in dedupe_preserve_order(terms) if term]


def _resolve_owner_bucket(
    url: str,
    title: str,
    payload: dict[str, Any],
    config: AppConfig,
) -> str:
    analysis_context = payload.get("analysis_context") or {}
    target_host = normalize_domain_host(analysis_context.get("target_domain") or config.target_domain)
    host = normalize_domain_host(url)
    if target_host and host and (host == target_host or host.endswith(f".{target_host}") or target_host.endswith(f".{host}")):
        return "self"
    haystack = normalize_text(f"{title} {url}").lower()
    for competitor in _build_competitor_terms(payload, config):
        normalized = normalize_text(competitor).lower()
        if normalized and normalized in haystack:
            return "competitor"
    return "external"


def build_result_url_evidence(
    row: dict[str, Any],
    source_rows: list[dict[str, Any]] | None,
    config: AppConfig,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or parse_json_object(row.get("output_json"))
    citation_records = resolve_citation_records(row, payload)
    source_records = _parse_source_rows(source_rows)
    citation_origin = _resolve_citation_origin(row, payload)
    parse_failed = _PARSE_FAIL_PREFIX in str(payload.get("answer_snapshot") or "")
    citation_map = {normalize_url_for_match(item["url"]): item for item in citation_records if normalize_url_for_match(item["url"])}
    source_map = {normalize_url_for_match(item["url"]): item for item in source_records if normalize_url_for_match(item["url"])}
    citation_missing_from_sources = [key for key in citation_map if key not in source_map]
    can_mark_searched_only = bool(source_map) and bool(citation_map) and not parse_failed and not citation_missing_from_sources

    items: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for normalized_url, citation in citation_map.items():
        owner_bucket = _resolve_owner_bucket(citation["url"], citation.get("title") or "", payload, config)
        source_match = source_map.get(normalized_url)
        title = str(citation.get("title") or (source_match or {}).get("title") or citation["url"]).strip()
        items.append(
            {
                "url": citation["url"],
                "normalized_url": normalized_url,
                "title": title or citation["url"],
                "host": normalize_domain_host(citation["url"]),
                "status": "cited",
                "owner_bucket": owner_bucket,
                "evidence_origin": citation_origin or "citations",
                "is_confident": bool(source_match) and not parse_failed,
            }
        )
        seen_urls.add(normalized_url)

    for normalized_url, source in source_map.items():
        if normalized_url in seen_urls:
            continue
        owner_bucket = _resolve_owner_bucket(source["url"], source.get("title") or "", payload, config)
        items.append(
            {
                "url": source["url"],
                "normalized_url": normalized_url,
                "title": str(source.get("title") or source["url"]).strip() or source["url"],
                "host": normalize_domain_host(source["url"]),
                "status": "searched_only" if can_mark_searched_only else "unknown",
                "owner_bucket": owner_bucket,
                "evidence_origin": "source_url",
                "is_confident": can_mark_searched_only,
            }
        )

    return {
        "items": items,
        "citation_count": len(citation_map),
        "source_count": len(source_map),
        "can_mark_searched_only": can_mark_searched_only,
        "parse_failed": parse_failed,
        "has_unknown": any(item["status"] == "unknown" for item in items),
        "citation_missing_from_sources": len(citation_missing_from_sources),
    }


def aggregate_url_evidence(
    rows: list[dict[str, Any]],
    source_loader: Callable[[str], list[dict[str, Any]]] | None,
    config: AppConfig,
) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        payload = parse_json_object(row.get("output_json"))
        source_rows = source_loader(str(row.get("result_id") or "")) if source_loader and row.get("result_id") else []
        evidence = build_result_url_evidence(row, source_rows, config, payload)
        for item in evidence["items"]:
            key = str(item.get("normalized_url") or item.get("url") or "")
            if not key:
                continue
            bucket = buckets.setdefault(
                key,
                {
                    "url": item["url"],
                    "normalized_url": item["normalized_url"],
                    "title": item["title"],
                    "host": item["host"],
                    "owner_bucket": item["owner_bucket"],
                    "status_counts": Counter(),
                    "origins": set(),
                    "confidence_hits": 0,
                    "observation_count": 0,
                },
            )
            if len(str(item.get("title") or "")) > len(str(bucket.get("title") or "")):
                bucket["title"] = item["title"]
            bucket["status_counts"][str(item["status"])] += 1
            bucket["origins"].add(str(item.get("evidence_origin") or ""))
            bucket["confidence_hits"] += 1 if item.get("is_confident") else 0
            bucket["observation_count"] += 1

    aggregated: list[dict[str, Any]] = []
    for bucket in buckets.values():
        if bucket["status_counts"]["cited"] > 0:
            status = "cited"
        elif bucket["status_counts"]["searched_only"] > 0:
            status = "searched_only"
        else:
            status = "unknown"
        aggregated.append(
            {
                "url": bucket["url"],
                "normalized_url": bucket["normalized_url"],
                "title": bucket["title"],
                "host": bucket["host"],
                "owner_bucket": bucket["owner_bucket"],
                "status": status,
                "observation_count": bucket["observation_count"],
                "status_counts": dict(bucket["status_counts"]),
                "evidence_origin": ", ".join(sorted(item for item in bucket["origins"] if item)),
                "is_confident": bucket["confidence_hits"] > 0,
            }
        )
    return sorted(
        aggregated,
        key=lambda item: (
            {"cited": 0, "searched_only": 1, "unknown": 2}.get(str(item.get("status") or ""), 9),
            {"external": 0, "self": 1, "competitor": 2}.get(str(item.get("owner_bucket") or ""), 9),
            -int(item.get("observation_count") or 0),
            str(item.get("host") or item.get("url") or ""),
        ),
    )


def split_url_evidence_sections(items: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    sections: dict[str, dict[str, list[dict[str, Any]]]] = {
        "cited": {"external": [], "self": [], "competitor": []},
        "searched_only": {"external": [], "self": [], "competitor": []},
        "unknown": {"external": [], "self": [], "competitor": []},
    }
    for item in items:
        status = str(item.get("status") or "")
        owner_bucket = str(item.get("owner_bucket") or "")
        if status not in sections or owner_bucket not in sections[status]:
            continue
        sections[status][owner_bucket].append(item)
    return sections


def build_evidence_stats(items: list[dict[str, Any]]) -> dict[str, Any]:
    owners = ("self", "competitor", "external")
    statuses = ("cited", "searched_only", "unknown")
    owner_totals = {owner: 0 for owner in owners}
    status_totals = {status: 0 for status in statuses}
    stats: dict[str, Any] = {
        "owner_totals": owner_totals,
        "status_totals": status_totals,
        "total_urls": len(items),
    }
    for owner in owners:
        for status in statuses:
            stats[f"{owner}_{status}"] = 0

    for item in items:
        owner = str(item.get("owner_bucket") or "")
        status = str(item.get("status") or "")
        if owner in owner_totals:
            owner_totals[owner] += 1
        if status in status_totals:
            status_totals[status] += 1
        key = f"{owner}_{status}"
        if key in stats:
            stats[key] += 1

    stats["competitive_cited_total"] = int(stats["competitor_cited"]) + int(stats["external_cited"])
    stats["self_visible_but_not_cited"] = int(stats["self_searched_only"])
    return stats


def _build_fallback_prompt_taxonomy_entry(row: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    from prompt_catalog import PROMPT_KEY_METADATA, infer_prompt_key

    query = str(row.get("executed_query") or row.get("keyword_raw") or "").strip()
    if not query:
        return {}
    analysis_context = payload.get("analysis_context") or {}
    prompt_key = infer_prompt_key(
        query,
        brand_terms=analysis_context.get("brand_terms") or [],
    )
    metadata = PROMPT_KEY_METADATA.get(prompt_key, PROMPT_KEY_METADATA["general"])
    return {
        "query": query,
        "query_norm": normalize_text(query),
        "query_index": int(row.get("executed_query_index") or 1),
        "role": "base" if int(row.get("executed_query_index") or 1) <= 1 else "expansion",
        "prompt_key": prompt_key,
        "prompt_label": metadata["label"],
        "prompt_family": metadata["family"],
        "purpose": metadata["purpose"],
        "inferred": True,
    }


def resolve_prompt_taxonomy_entry(row: dict[str, Any]) -> dict[str, Any]:
    payload = parse_json_object(row.get("output_json"))
    try:
        entries = json.loads(str(row.get("prompt_taxonomy_json") or payload.get("prompt_taxonomy_json") or "[]"))
    except Exception:
        entries = []
    entries = [item for item in entries if isinstance(item, dict)]
    executed_query_norm = normalize_text(str(row.get("executed_query") or row.get("keyword_raw") or ""))
    executed_query_index = int(row.get("executed_query_index") or 0)
    for entry in entries:
        if executed_query_index and int(entry.get("query_index") or 0) == executed_query_index:
            return entry
        if executed_query_norm and normalize_text(str(entry.get("query") or "")) == executed_query_norm:
            return entry
    if entries:
        return entries[0]
    return _build_fallback_prompt_taxonomy_entry(row, payload)


def _group_latest_rows_by_query(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    ordered_rows = sorted(rows, key=lambda row: float(row.get("analyzed_at") or 0.0), reverse=True)
    latest_run_by_query: dict[str, str] = {}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in ordered_rows:
        query_key = normalize_text(str(row.get("keyword_raw") or ""))
        if not query_key:
            continue
        run_id = str(row.get("run_id") or "")
        selected_run_id = latest_run_by_query.setdefault(query_key, run_id or query_key)
        if (run_id or query_key) != selected_run_id:
            continue
        grouped[(query_key, selected_run_id)].append(row)
    return list(grouped.values())


def _build_prompt_dominance_label(
    *,
    cited_external_count: int,
    cited_self_count: int,
    searched_only_self_count: int,
    searched_only_external_count: int,
    unknown_count: int,
) -> str:
    if cited_external_count > max(cited_self_count, 0):
        return "外部引用優勢"
    if searched_only_self_count > 0 and cited_self_count == 0:
        return "自社は出るが未引用"
    if cited_self_count > 0 and cited_external_count == 0:
        return "自社引用あり"
    if unknown_count > 0 and cited_self_count == 0 and cited_external_count == 0:
        return "判定不明"
    if cited_external_count > 0 and cited_self_count > 0:
        return "引用が混在"
    if searched_only_external_count > 0 and cited_external_count == 0 and cited_self_count == 0:
        return "検索ソースのみ"
    return "情報不足"


def _build_prompt_family_summary(
    *,
    prompt_family: str,
    dominance_label: str,
    unknown_rate: float,
) -> str:
    if dominance_label == "外部引用優勢":
        return f"{prompt_family}系は外部サイトが先に引用されやすく、自社の根拠が弱い状態です。"
    if dominance_label == "自社は出るが未引用":
        return f"{prompt_family}系は自社URLが検索ソースに出ますが、引用までは届いていません。"
    if dominance_label == "自社引用あり":
        return f"{prompt_family}系は自社URLが根拠として使われています。"
    if dominance_label == "判定不明":
        return f"{prompt_family}系は判定保留のURLが多く、未引用とは断定しない方が安全です。"
    if dominance_label == "引用が混在":
        return f"{prompt_family}系は自社と外部サイトの引用が混ざっています。"
    if dominance_label == "検索ソースのみ":
        return f"{prompt_family}系は検索ソースには出ますが、引用はまだ確認できていません。"
    if unknown_rate >= 0.5:
        return f"{prompt_family}系は判定保留が多く、まず根拠URLの状態確認が必要です。"
    return f"{prompt_family}系は観測数が少なく、引き続き確認が必要です。"


def build_prompt_family_source_rollups(
    rows: list[dict[str, Any]],
    source_loader: Callable[[str], list[dict[str, Any]]] | None,
    config: AppConfig,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        taxonomy = resolve_prompt_taxonomy_entry(row)
        prompt_label = str(taxonomy.get("prompt_label") or "探索").strip() or "探索"
        prompt_family = str(taxonomy.get("prompt_family") or "探索").strip() or "探索"
        purpose = str(taxonomy.get("purpose") or "").strip()
        payload = parse_json_object(row.get("output_json"))
        source_rows = source_loader(str(row.get("result_id") or "")) if source_loader and row.get("result_id") else []
        evidence = build_result_url_evidence(row, source_rows, config, payload)
        bucket = grouped.setdefault(
            prompt_family,
            {
                "prompt_family": prompt_family,
                "query_count": 0,
                "sample_queries": [],
                "prompt_labels": set(),
                "purposes": set(),
                "cited_external_hosts": set(),
                "cited_self_hosts": set(),
                "cited_competitor_hosts": set(),
                "searched_only_self_hosts": set(),
                "searched_only_external_hosts": set(),
                "searched_only_competitor_hosts": set(),
                "unknown_hosts": set(),
                "observed_hosts": set(),
            },
        )
        bucket["query_count"] += 1
        bucket["sample_queries"].append(str(row.get("executed_query") or row.get("keyword_raw") or "").strip())
        bucket["prompt_labels"].add(prompt_label)
        if purpose:
            bucket["purposes"].add(purpose)
        for item in evidence["items"]:
            host = str(item.get("host") or item.get("url") or "").strip()
            if not host:
                continue
            owner_bucket = str(item.get("owner_bucket") or "")
            status = str(item.get("status") or "")
            bucket["observed_hosts"].add(host)
            if status == "cited" and owner_bucket == "external":
                bucket["cited_external_hosts"].add(host)
            elif status == "cited" and owner_bucket == "self":
                bucket["cited_self_hosts"].add(host)
            elif status == "cited" and owner_bucket == "competitor":
                bucket["cited_competitor_hosts"].add(host)
            elif status == "searched_only" and owner_bucket == "self":
                bucket["searched_only_self_hosts"].add(host)
            elif status == "searched_only" and owner_bucket == "external":
                bucket["searched_only_external_hosts"].add(host)
            elif status == "searched_only" and owner_bucket == "competitor":
                bucket["searched_only_competitor_hosts"].add(host)
            elif status == "unknown":
                bucket["unknown_hosts"].add(host)

    rollups: list[dict[str, Any]] = []
    for bucket in grouped.values():
        cited_external_count = len(bucket["cited_external_hosts"])
        cited_self_count = len(bucket["cited_self_hosts"])
        searched_only_self_count = len(bucket["searched_only_self_hosts"])
        searched_only_external_count = len(bucket["searched_only_external_hosts"])
        searched_only_competitor_count = len(bucket["searched_only_competitor_hosts"])
        unknown_count = len(bucket["unknown_hosts"])
        observed_url_count = len(bucket["observed_hosts"])
        primary_prompt_label = (
            sorted(str(label) for label in bucket["prompt_labels"] if str(label).strip())[0]
            if bucket["prompt_labels"]
            else "探索"
        )
        unknown_rate = round(unknown_count / max(observed_url_count, 1), 3)
        dominance_label = _build_prompt_dominance_label(
            cited_external_count=cited_external_count,
            cited_self_count=cited_self_count,
            searched_only_self_count=searched_only_self_count,
            searched_only_external_count=searched_only_external_count,
            unknown_count=unknown_count,
        )
        family_summary = _build_prompt_family_summary(
            prompt_family=str(bucket["prompt_family"]),
            dominance_label=dominance_label,
            unknown_rate=unknown_rate,
        )
        rollups.append(
            {
                "prompt_family": bucket["prompt_family"],
                "prompt_labels": sorted(str(label) for label in bucket["prompt_labels"] if str(label).strip()),
                "primary_prompt_label": primary_prompt_label,
                "purpose_summary": " / ".join(sorted(str(item) for item in bucket["purposes"] if str(item).strip())),
                "query_count": int(bucket["query_count"]),
                "sample_queries": dedupe_preserve_order(bucket["sample_queries"])[:2],
                "cited_external_count": cited_external_count,
                "cited_self_count": cited_self_count,
                "cited_competitor_count": len(bucket["cited_competitor_hosts"]),
                "searched_only_self_count": searched_only_self_count,
                "searched_only_external_count": searched_only_external_count,
                "searched_only_competitor_count": searched_only_competitor_count,
                "unknown_count": unknown_count,
                "observed_url_count": observed_url_count,
                "unknown_rate": unknown_rate,
                "dominance_label": dominance_label,
                "family_summary": family_summary,
            }
        )
    return sorted(
        rollups,
        key=lambda item: (
            {"外部引用優勢": 0, "自社は出るが未引用": 1, "判定不明": 2, "引用が混在": 3, "自社引用あり": 4}.get(
                str(item.get("dominance_label") or ""),
                9,
            ),
            str(item.get("prompt_family") or ""),
        ),
    )


def build_prompt_label_source_rollups(
    rows: list[dict[str, Any]],
    source_loader: Callable[[str], list[dict[str, Any]]] | None,
    config: AppConfig,
) -> list[dict[str, Any]]:
    return build_prompt_family_source_rollups(rows, source_loader, config)


def build_source_priority_actions(
    rows: list[dict[str, Any]],
    source_loader: Callable[[str], list[dict[str, Any]]] | None,
    config: AppConfig,
    *,
    limit: int = 3,
) -> list[dict[str, Any]]:
    aggregated: dict[str, dict[str, Any]] = {}
    for group_rows in _group_latest_rows_by_query(rows):
        for rollup in build_prompt_family_source_rollups(group_rows, source_loader, config):
            bucket = aggregated.setdefault(
                str(rollup["prompt_family"]),
                {
                    "prompt_family": rollup["prompt_family"],
                    "query_count": 0,
                    "prompt_labels": set(),
                    "cited_external_count": 0,
                    "cited_self_count": 0,
                    "searched_only_self_count": 0,
                    "unknown_count": 0,
                },
            )
            bucket["query_count"] += int(rollup["query_count"] or 0)
            for label in rollup.get("prompt_labels") or []:
                if str(label).strip():
                    bucket["prompt_labels"].add(str(label).strip())
            bucket["cited_external_count"] += int(rollup["cited_external_count"] or 0)
            bucket["cited_self_count"] += int(rollup["cited_self_count"] or 0)
            bucket["searched_only_self_count"] += int(rollup["searched_only_self_count"] or 0)
            bucket["unknown_count"] += int(rollup["unknown_count"] or 0)

    actions: list[dict[str, Any]] = []
    for bucket in aggregated.values():
        prompt_family = str(bucket["prompt_family"] or "探索")
        prompt_labels = sorted(str(label) for label in bucket["prompt_labels"] if str(label).strip())
        external = int(bucket["cited_external_count"] or 0)
        owned = int(bucket["cited_self_count"] or 0)
        searched_only_owned = int(bucket["searched_only_self_count"] or 0)
        unknown = int(bucket["unknown_count"] or 0)
        if external > max(owned, 0):
            weight = external * 30 + bucket["query_count"]
            summary = f"{prompt_family}系では外部サイトが先に引用され、自社が根拠として弱い状態です。"
            headline = f"{prompt_family}系で外部根拠が先行"
        elif searched_only_owned > 0 and owned == 0:
            weight = searched_only_owned * 24 + bucket["query_count"]
            summary = f"{prompt_family}系では自社URLが検索ソースに出ますが、引用までは届いていません。"
            headline = f"{prompt_family}系を引用される形に整える"
        elif unknown > 0 and owned == 0 and external == 0:
            weight = unknown * 12 + bucket["query_count"]
            summary = f"{prompt_family}系は判定保留が多く、根拠URLの状態確認が必要です。"
            headline = f"{prompt_family}系の判定保留を減らす"
        else:
            continue
        actions.append(
            {
                "prompt_family": prompt_family,
                "prompt_labels": prompt_labels,
                "headline": headline,
                "summary": summary,
                "weight": weight,
            }
        )
    return sorted(actions, key=lambda item: (-int(item["weight"]), str(item["prompt_family"])))[:limit]
