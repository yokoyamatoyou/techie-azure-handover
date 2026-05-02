# -*- coding: utf-8 -*-
"""Schema.org (JSON-LD) validation helpers."""
import json
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


SCHEMA_RECOMMENDATIONS = {
    "ec": [
        {"label": "Product", "types": ["Product"]},
        {"label": "Offer", "types": ["Offer", "AggregateOffer"]},
        {"label": "BreadcrumbList", "types": ["BreadcrumbList"]},
        {"label": "Organization", "types": ["Organization"]},
    ],
    "company": [
        {"label": "Organization", "types": ["Organization"]},
        {"label": "WebSite", "types": ["WebSite"]},
    ],
    "article": [
        {"label": "Article", "types": ["Article", "NewsArticle", "BlogPosting"]},
        {"label": "BreadcrumbList", "types": ["BreadcrumbList"]},
    ],
    "local": [
        {"label": "LocalBusiness", "types": ["LocalBusiness", "Store", "Restaurant"]},
        {"label": "Organization", "types": ["Organization"]},
    ],
}

REQUIRED_FIELDS = {
    "Organization": ["name", "url"],
    "WebSite": ["name", "url"],
    "Article": ["headline", "author", "datePublished"],
    "NewsArticle": ["headline", "author", "datePublished"],
    "BlogPosting": ["headline", "author", "datePublished"],
    "Product": ["name", "offers"],
    "Offer": ["price", "priceCurrency", "availability"],
    "AggregateOffer": ["offerCount"],
    "LocalBusiness": ["name", "address", "telephone"],
    "Store": ["name", "address", "telephone"],
    "Restaurant": ["name", "address", "telephone"],
    "BreadcrumbList": ["itemListElement"],
}

SITE_TYPE_ALIASES = {
    "ec": "ec",
    "ecommerce": "ec",
    "product": "ec",
    "company": "company",
    "corporate": "company",
    "article": "article",
    "blog": "article",
    "news": "article",
    "local": "local",
    "store": "local",
    "restaurant": "local",
}


def extract_json_ld(html: str) -> List[Dict[str, Any]]:
    """Extract JSON-LD blobs from HTML."""
    soup = BeautifulSoup(html or "", "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")
    schemas: List[Dict[str, Any]] = []
    for script in scripts:
        raw = script.string
        if not raw or not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            schemas.extend([item for item in data if isinstance(item, dict)])
        elif isinstance(data, dict):
            schemas.append(data)
    return schemas


def normalize_site_type(site_type: Optional[str]) -> str:
    normalized = str(site_type or "").strip().lower()
    return SITE_TYPE_ALIASES.get(normalized, "company")


def infer_schema_site_type(
    html: str,
    url: str = "",
    schemas: Optional[List[Dict[str, Any]]] = None,
    hinted_type: Optional[str] = None,
) -> str:
    normalized_hint = normalize_site_type(hinted_type)
    if normalized_hint != "company":
        return normalized_hint

    schemas = schemas or extract_json_ld(html)
    found_types = set(_collect_types(schemas))
    if {"Product", "Offer", "AggregateOffer"} & found_types:
        return "ec"
    if {"Article", "NewsArticle", "BlogPosting"} & found_types:
        return "article"
    if {"LocalBusiness", "Store", "Restaurant"} & found_types:
        return "local"

    html_lower = (html or "").lower()
    url_lower = (url or "").lower()
    soup = BeautifulSoup(html or "", "html.parser")

    if soup.find("article") or soup.find("time") or "og:type" in html_lower and "article" in html_lower:
        return "article"
    if any(token in html_lower for token in ["add to cart", "カートに追加", "price", "価格", "sku", "在庫"]):
        return "ec"
    if any(token in html_lower for token in ["営業時間", "アクセス", "店舗情報", "address", "tel"]) or re.search(r"/(shop|store|access|location)", url_lower):
        return "local"
    return "company"


def validate_schema(schemas: List[Dict[str, Any]], site_type: str = "company") -> Dict[str, Any]:
    """Validate schema coverage and required fields for a page type."""
    normalized_site_type = normalize_site_type(site_type)
    recommendations = SCHEMA_RECOMMENDATIONS.get(normalized_site_type, SCHEMA_RECOMMENDATIONS["company"])
    found_types = _collect_types(schemas or [])
    unique_types = sorted(set(found_types))

    result = {
        "site_type": normalized_site_type,
        "found_types": unique_types,
        "recommended_types": [rule["label"] for rule in recommendations],
        "missing_recommended": [],
        "matched_recommended": [],
        "has_required_fields": True,
        "required_field_issues": [],
        "issues": [],
        "score": 0,
    }

    missing_recommended: List[str] = []
    matched_recommended: List[str] = []
    for rule in recommendations:
        if any(schema_type in unique_types for schema_type in rule["types"]):
            matched_recommended.append(rule["label"])
        else:
            missing_recommended.append(rule["label"])

    required_field_issues: List[Dict[str, Any]] = []
    for schema in schemas or []:
        schema_types = schema.get("@type", [])
        if isinstance(schema_types, str):
            schema_types = [schema_types]
        for schema_type in [item for item in schema_types if isinstance(item, str)]:
            required_fields = REQUIRED_FIELDS.get(schema_type, [])
            missing_fields = [field for field in required_fields if not _has_value(schema.get(field))]
            if missing_fields:
                required_field_issues.append({"type": schema_type, "missing": missing_fields})

    presence_ratio = 0.0
    if recommendations:
        presence_ratio = len(matched_recommended) / len(recommendations)
    required_ratio = 1.0
    if schemas:
        schemas_with_rules = [schema for schema in schemas if any(t in REQUIRED_FIELDS for t in _ensure_list(schema.get("@type")))]
        if schemas_with_rules:
            valid_count = len(schemas_with_rules) - len(required_field_issues)
            required_ratio = max(0.0, valid_count / len(schemas_with_rules))
    elif recommendations:
        required_ratio = 0.0

    result["missing_recommended"] = missing_recommended
    result["matched_recommended"] = matched_recommended
    result["required_field_issues"] = required_field_issues
    result["has_required_fields"] = len(required_field_issues) == 0

    if not schemas:
        result["score"] = 0
    else:
        result["score"] = int((presence_ratio * 70) + (required_ratio * 30))

    for item in missing_recommended:
        result["issues"].append(f"推奨スキーマが不足しています: {item}")
    for item in required_field_issues:
        joined = ", ".join(item["missing"])
        result["issues"].append(f"{item['type']} の必須プロパティ不足: {joined}")

    return result


def _collect_types(schemas: List[Dict[str, Any]]) -> List[str]:
    found_types: List[str] = []
    for schema in schemas or []:
        schema_type = schema.get("@type", "")
        if isinstance(schema_type, list):
            found_types.extend([item for item in schema_type if isinstance(item, str)])
        elif isinstance(schema_type, str):
            found_types.append(schema_type)
    return found_types


def _ensure_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _has_value(value: Any) -> bool:
    return value not in (None, "", [])


if __name__ == "__main__":
    test_html = """
    <html>
    <head>
        <script type="application/ld+json">
        {"@context": "https://schema.org", "@type": "Organization", "name": "Test Corp", "url": "https://example.com"}
        </script>
    </head>
    </html>
    """
    schemas = extract_json_ld(test_html)
    inferred = infer_schema_site_type(test_html, "https://example.com")
    result = validate_schema(schemas, site_type=inferred)
    print(f"Site type: {inferred}")
    print(f"Found: {result['found_types']}")
    print(f"Missing: {result['missing_recommended']}")
    print(f"Score: {result['score']}")
