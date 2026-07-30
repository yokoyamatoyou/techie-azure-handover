from __future__ import annotations

from typing import Any

from analysis_lib import normalize_domain_host, normalize_text, parse_json_object, resolve_citation_records
from config import AppConfig


def normalize_host(raw_value: Any) -> str:
    return normalize_domain_host(raw_value)


def extract_competitor_terms(payload: dict[str, Any], config: AppConfig) -> list[str]:
    analysis_context = payload.get("analysis_context") or {}
    raw_terms = analysis_context.get("competitor_terms") or config.competitor_terms
    seen: list[str] = []
    for item in raw_terms or []:
        value = str(item or "").strip()
        if value and value not in seen:
            seen.append(value)
    return seen


def build_source_groups(
    sources: list[dict[str, Any]],
    payload: dict[str, Any],
    config: AppConfig,
) -> dict[str, list[dict[str, Any]]]:
    target_host = normalize_host((payload.get("analysis_context") or {}).get("target_domain") or config.target_domain)
    competitor_terms = [term.lower() for term in extract_competitor_terms(payload, config)]
    grouped: dict[str, list[dict[str, Any]]] = {"self": [], "competitor": [], "third_party": []}
    seen_urls: set[str] = set()

    for raw_source in sources:
        url = str(raw_source.get("url") or "").strip()
        title = str(raw_source.get("title") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        host = normalize_host(url)
        haystack = f"{title} {url}".lower()
        source = {"url": url, "title": title or url, "host": host}
        if target_host and host and (host == target_host or host.endswith(f".{target_host}")):
            grouped["self"].append(source)
        elif any(term and term in haystack for term in competitor_terms):
            grouped["competitor"].append(source)
        else:
            grouped["third_party"].append(source)
    return grouped


def extract_cited_sources(row: dict[str, Any], payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    payload = payload or parse_json_object(row.get("output_json"))
    raw_citations = resolve_citation_records(row, payload)
    deduped: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for citation in raw_citations:
        url = str(citation.get("url") or "").strip()
        title = str(citation.get("title") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append({"url": url, "title": title or url})
    return deduped


def find_group_rows(selected_row: dict[str, Any], raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    target_query = normalize_text(str(selected_row.get("keyword_raw") or selected_row.get("keyword_norm") or ""))
    target_run_id = str(selected_row.get("run_id") or "")
    matched = [
        row
        for row in raw_rows
        if normalize_text(str(row.get("keyword_raw") or row.get("keyword_norm") or "")) == target_query
        and str(row.get("run_id") or "") == target_run_id
    ]
    return matched or [selected_row]


def localize_owner_bucket(owner_bucket: str) -> str:
    return {
        "self": "自社",
        "competitor": "比較対象",
        "external": "外部",
    }.get(str(owner_bucket or ""), "外部")


def localize_url_action_label(status: str) -> str:
    return {
        "cited": "優先して見る",
        "searched_only": "参考程度",
        "unknown": "確認が必要",
    }.get(str(status or ""), "参考程度")


def localize_status_bucket(status: str) -> str:
    return {
        "cited": "根拠に使われた",
        "searched_only": "見つかったが未採用",
        "unknown": "確認が必要",
    }.get(str(status or ""), "見つかったが未採用")


def build_evidence_meaning_label(item: dict[str, Any]) -> str:
    status = str(item.get("status") or "")
    owner_label = localize_owner_bucket(str(item.get("owner_bucket") or ""))
    action_label = localize_url_action_label(status)
    return f"{owner_label} / {action_label} ({localize_status_bucket(status)})"


def build_evidence_chip_class(item: dict[str, Any]) -> str:
    status = str(item.get("status") or "")
    if status == "unknown":
        return "signal-neutral"
    return {
        "self": "signal-positive",
        "competitor": "signal-neutral",
        "external": "signal-negative",
    }.get(str(item.get("owner_bucket") or ""), "signal-neutral")


def build_evidence_highlights(
    items: list[dict[str, Any]],
    limit: int = 4,
    preferred_owner: str | None = None,
) -> list[dict[str, Any]]:
    def rank(item: dict[str, Any]) -> tuple[int, int, int, str]:
        status = str(item.get("status") or "")
        owner_bucket = str(item.get("owner_bucket") or "")
        owner_orders = {
            "self": {"self": 0, "external": 1, "competitor": 2},
            "external": {"external": 0, "competitor": 1, "self": 2},
            "competitor": {"competitor": 0, "external": 1, "self": 2},
        }
        owner_order = owner_orders.get(str(preferred_owner or "").strip().lower(), {"external": 0, "competitor": 1, "self": 2})
        status_order = {"cited": 0, "searched_only": 1, "unknown": 2}
        priority = (status_order.get(status, 9) * 10) + owner_order.get(owner_bucket, 9)
        counts = item.get("status_counts") or {}
        cited_count = int(counts.get("cited", 0))
        searched_only_count = int(counts.get("searched_only", 0))
        observed_count = int(item.get("observation_count") or 0)
        return (priority, -(cited_count + searched_only_count), -observed_count, str(item.get("host") or item.get("url") or ""))

    return sorted(items, key=rank)[:limit]


def build_cited_evidence_highlights(
    items: list[dict[str, Any]],
    limit: int = 3,
    preferred_owner: str | None = None,
) -> list[dict[str, Any]]:
    cited_items = [item for item in items if int((item.get("status_counts") or {}).get("cited", 0)) > 0]
    return build_evidence_highlights(cited_items, limit=limit, preferred_owner=preferred_owner)


def filter_evidence_items_by_status(items: list[dict[str, Any]], status: str) -> list[dict[str, Any]]:
    status_key = str(status or "").strip().lower()
    filtered: list[dict[str, Any]] = []
    for item in items:
        counts = item.get("status_counts") or {}
        if int(counts.get(status_key, 0)) > 0:
            filtered.append(item)
    return build_evidence_highlights(filtered, limit=max(1, len(filtered)))


def build_evidence_table_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        counts = item.get("status_counts") or {}
        cited_count = int(counts.get("cited", 0))
        candidate_count = int(counts.get("searched_only", 0))
        unknown_count = int(counts.get("unknown", 0))
        if cited_count > 0:
            reading = "AIが答えを作るときに、実際に根拠として使ったURLです。"
        elif candidate_count > 0:
            reading = "見つかってはいましたが、今回は根拠には使われなかったURLです。"
        else:
            reading = "保存状況の都合で、使われたかどうかを今すぐ断定しにくいURLです。"
        rows.append(
            {
                "meaning_label": build_evidence_meaning_label(item),
                "title": str(item.get("title") or item.get("url") or "-"),
                "host": str(item.get("host") or item.get("url") or "-"),
                "observation_label": f"根拠 {cited_count} / 未採用 {candidate_count} / 要確認 {unknown_count}",
                "reading": reading,
            }
        )
    return rows
