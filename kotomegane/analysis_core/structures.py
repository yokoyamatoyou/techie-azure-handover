from __future__ import annotations

from typing import Any

from analysis_core.common import *
from analysis_core.common import _candidate_aliases, _contains_named_term

def parse_citations_json(raw_value: Any) -> list[dict[str, str]]:
    if isinstance(raw_value, list):
        items = raw_value
    else:
        try:
            items = json.loads(str(raw_value or "[]"))
        except Exception:
            items = []
    normalized_items: list[dict[str, str]] = []
    for item in items or []:
        if isinstance(item, dict):
            url = str(item.get("url") or "").strip()
            title = str(item.get("title") or "").strip()
        else:
            url = str(item or "").strip()
            title = ""
        if not url:
            continue
        normalized_items.append({"url": url, "title": title})
    return normalized_items


def parse_string_list_json(raw_value: Any) -> list[str]:
    if isinstance(raw_value, list):
        items = raw_value
    else:
        try:
            items = json.loads(str(raw_value or "[]"))
        except Exception:
            items = []
    values: list[str] = []
    for item in items or []:
        value = normalize_text(str(item or ""))
        if value:
            values.append(value)
    return dedupe_preserve_order(values)


def _build_brand_candidates(payload: dict[str, Any], analysis_context: dict[str, Any], config: AppConfig | None) -> list[str]:
    brand_terms = analysis_context.get("brand_terms") or (config.brand_terms if config else [])
    competitor_terms = analysis_context.get("competitor_terms") or (config.competitor_terms if config else [])
    competitor_mentions = payload.get("competitor_mentions") or []
    candidates = [str(item or "") for item in [*brand_terms, *competitor_terms, *competitor_mentions]]
    return dedupe_preserve_order(candidates)


def _build_brand_alias_map(
    payload: dict[str, Any],
    analysis_context: dict[str, Any],
    config: AppConfig | None,
) -> dict[str, list[str]]:
    alias_map: dict[str, list[str]] = {}
    for candidate in _build_brand_candidates(payload, analysis_context, config):
        aliases = _candidate_aliases(candidate)
        if aliases:
            alias_map[candidate] = aliases
    return alias_map


def _build_owned_hosts(analysis_context: dict[str, Any], config: AppConfig | None) -> list[str]:
    target_domain = analysis_context.get("target_domain") or (config.target_domain if config else "")
    allowed_domains = analysis_context.get("allowed_domains") or (config.allowed_domains if config else [])
    owned_only_domains = analysis_context.get("owned_only_domains") or []
    hosts = [
        normalize_domain_host(target_domain),
        *[normalize_domain_host(item) for item in allowed_domains],
        *[normalize_domain_host(item) for item in owned_only_domains],
    ]
    return dedupe_preserve_order([host for host in hosts if host])


def infer_answer_structure(
    *,
    keyword: str,
    answer_text: str,
    citations: list[dict[str, str]],
    source_items: list[dict[str, str]] | None = None,
    payload: dict[str, Any] | None = None,
    analysis_context: dict[str, Any] | None = None,
    config: AppConfig | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    analysis_context = analysis_context or {}
    source_items = source_items or []
    normalized_answer = normalize_text(answer_text)
    citation_domains_all = [normalize_citation_domain(item.get("url") or "") for item in citations if normalize_citation_domain(item.get("url") or "")]
    citation_domains = dedupe_preserve_order(citation_domains_all)
    source_domains_all = [
        normalize_citation_domain(item.get("url") or "")
        for item in source_items
        if normalize_citation_domain(item.get("url") or "")
    ]
    source_domains = dedupe_preserve_order(source_domains_all)
    citation_titles = " ".join(normalize_text(item.get("title") or "") for item in [*citations, *source_items])
    haystack = normalize_text(
        " ".join(
            [
                normalized_answer,
                citation_titles,
                " ".join(citation_domains),
                " ".join(source_domains),
                " ".join(str(item or "") for item in (payload.get("competitor_mentions") or [])),
            ]
        )
    ).lower()

    mentioned_brands = [
        candidate
        for candidate, aliases in _build_brand_alias_map(payload, analysis_context, config).items()
        if any(_contains_named_term(haystack, alias) for alias in aliases)
    ]
    owned_hosts = _build_owned_hosts(analysis_context, config)
    preset_competitor_terms = [
        term
        for preset in (config.competitor_presets if config else [])
        for term in [preset.display_name, *preset.aliases]
    ]
    competitor_terms = dedupe_preserve_order(
        [
            str(item or "")
            for item in [
                *(analysis_context.get("competitor_terms") or (config.competitor_terms if config else [])),
                *preset_competitor_terms,
                *(payload.get("competitor_mentions") or []),
            ]
        ]
    )
    answer_type = classify_answer_type(
        keyword,
        normalized_answer,
        citation_titles,
        citation_domains,
        brand_terms=analysis_context.get("brand_terms") or (config.brand_terms if config else []),
    )

    own_brand_terms = dedupe_preserve_order(
        [str(item or "") for item in (analysis_context.get("brand_terms") or (config.brand_terms if config else []))]
    )
    own_brand_present = any(
        _contains_named_term(haystack, alias)
        for term in own_brand_terms
        for alias in _candidate_aliases(term)
    )
    own_domain_present = any(
        domain == host or domain.endswith(f".{host}") or host.endswith(f".{domain}")
        for domain in [*citation_domains, *source_domains]
        for host in owned_hosts
        if domain and host
    )
    owned_citation_count = sum(
        1
        for domain in citation_domains_all
        for host in owned_hosts
        if domain and host and (domain == host or domain.endswith(f".{host}") or host.endswith(f".{domain}"))
    )
    owned_citation_share = (owned_citation_count / len(citation_domains_all)) if citation_domains_all else 0.0
    competitor_present = any(
        _contains_named_term(haystack, alias)
        for term in competitor_terms
        for alias in _candidate_aliases(term)
    )

    return {
        "mentioned_brands": dedupe_preserve_order(mentioned_brands),
        "citation_domains": citation_domains,
        "owned_domain_hit": bool(own_domain_present),
        "owned_brand_hit": bool(own_brand_present),
        "owned_mention_hit": bool(own_brand_present or own_domain_present),
        "owned_citation_count": owned_citation_count,
        "owned_citation_share": round(owned_citation_share, 4),
        "competitor_mention_hit": bool(competitor_present),
        "external_only_result": bool(not own_domain_present and not own_brand_present and owned_citation_count == 0),
        "answer_type_key": answer_type["primary"],
        "answer_type_label": ANSWER_TYPE_LABELS.get(answer_type["primary"], "探索回答"),
    }


def build_answer_structure_fields(row: dict[str, Any], config: AppConfig | None = None) -> dict[str, Any]:
    payload = parse_json_object(row.get("output_json"))
    analysis_context = payload.get("analysis_context") or {}
    answer_text = str(row.get("answer_text") or payload.get("answer_text") or "")
    citations = parse_citations_json(row.get("citations_json") or payload.get("citations") or [])

    stored_brands = parse_string_list_json(row.get("mentioned_brands_json"))
    stored_domains = parse_string_list_json(row.get("citation_domains_json"))
    stored_answer_type_key = normalize_text(str(row.get("answer_type_key") or ""))
    stored_answer_type_label = normalize_text(str(row.get("answer_type_label") or ""))
    stored_owned = row.get("owned_mention_hit")
    stored_competitor = row.get("competitor_mention_hit")
    stored_owned_domain = row.get("target_domain_hit")
    stored_owned_brand = row.get("brand_mention_hit")
    stored_owned_citation_count = row.get("owned_citation_count")
    stored_owned_citation_share = row.get("owned_citation_share")
    stored_external_only = row.get("external_only_result")

    inferred = infer_answer_structure(
        keyword=str(row.get("keyword_raw") or payload.get("keyword_raw") or ""),
        answer_text=answer_text,
        citations=citations,
        source_items=[],
        payload=payload,
        analysis_context=analysis_context,
        config=config,
    )

    return {
        "mentioned_brands": stored_brands or inferred["mentioned_brands"],
        "citation_domains": stored_domains or inferred["citation_domains"],
        "owned_domain_hit": bool(int(stored_owned_domain)) if stored_owned_domain is not None else bool(inferred["owned_domain_hit"]),
        "owned_brand_hit": bool(int(stored_owned_brand)) if stored_owned_brand is not None else bool(inferred["owned_brand_hit"]),
        "owned_mention_hit": bool(int(stored_owned)) if stored_owned is not None else bool(inferred["owned_mention_hit"]),
        "owned_citation_count": (
            int(stored_owned_citation_count)
            if stored_owned_citation_count is not None
            else int(inferred["owned_citation_count"])
        ),
        "owned_citation_share": (
            float(stored_owned_citation_share)
            if stored_owned_citation_share is not None
            else float(inferred["owned_citation_share"])
        ),
        "competitor_mention_hit": (
            bool(int(stored_competitor)) if stored_competitor is not None else bool(inferred["competitor_mention_hit"])
        ),
        "external_only_result": (
            bool(int(stored_external_only)) if stored_external_only is not None else bool(inferred["external_only_result"])
        ),
        "answer_type_key": stored_answer_type_key or str(inferred["answer_type_key"]),
        "answer_type_label": stored_answer_type_label or str(inferred["answer_type_label"]),
    }


