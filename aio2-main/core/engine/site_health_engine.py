# -*- coding: utf-8 -*-
"""Site health check orchestrator."""

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from core.faq_detection import build_faq_detection
from core.industry_detector import detect_business_type
from core.legal_checks import (
    CommercialTransactionChecker,
    ECDetector,
    PremiumsLabelingChecker,
    StealthMarketingChecker,
    find_tokushoho_page,
    format_check_result,
    format_commercial_transaction_result,
    format_stealth_marketing_result,
    generate_template_suggestion,
)
from core.legal_checks.commercial_transaction import (
    augment_html_with_embedded_docs,
    augment_html_with_related_pages,
)
from core.legal_checks.consumer_protection import ConsumerProtectionChecker
from core.site_health import (
    AccessibilityChecker,
    OGPChecker,
    SecurityChecker,
    format_accessibility_result,
    format_ogp_result,
    format_security_result,
    get_platform_specific_suggestions,
    get_wcag_compliance_level,
)
from core.site_health.browser_accessibility_scanner import (
    build_browser_accessibility_payload,
    browser_accessibility_enabled,
    run_browser_accessibility_scan,
)
from core.structured_data import (
    SchemaSuggester,
    analyze_existing_schema,
    generate_schema_template,
    get_schema_explanation,
    get_schema_faq,
)
from core.structured_data.checker import StructuredDataChecker
from core.aio.schema_validator import infer_schema_site_type, validate_schema


def _extract_json_ld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    json_ld: List[Dict[str, Any]] = []
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        raw = script.string
        if not raw or not raw.strip():
            continue
        try:
            parsed = json.loads(raw)
        except Exception:
            continue

        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    json_ld.append(item)
        elif isinstance(parsed, dict):
            json_ld.append(parsed)

    return json_ld


def _run_ogp_check(html: str, url: str, mode: str) -> Dict[str, Any]:
    ogp_checker = OGPChecker(html or "", url)
    ogp_raw = ogp_checker.run_all_checks()
    ogp_formatted = format_ogp_result(ogp_raw, mode=mode)
    return {
        "raw": ogp_raw,
        "formatted": ogp_formatted,
        "platform_suggestions": get_platform_specific_suggestions(ogp_raw.get("ogp", {})),
    }


def _run_security_check(
    url: str,
    headers: Dict[str, Any],
    html: str,
    mode: str,
    sitemap_info: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    security_checker = SecurityChecker(url, dict(headers), html or "", sitemap_info=sitemap_info)
    security_raw = security_checker.run_all_checks()
    return {
        "raw": security_raw,
        "formatted": format_security_result(security_raw, mode=mode),
    }


def _run_accessibility_check(html: str, url: str, mode: str) -> Dict[str, Any]:
    browser_accessibility = None
    if browser_accessibility_enabled():
        browser_report = run_browser_accessibility_scan(url)
        if browser_report:
            browser_accessibility = build_browser_accessibility_payload(browser_report, mode=mode)

    if browser_accessibility:
        return {
            "raw": browser_accessibility["raw"],
            "formatted": browser_accessibility["formatted"],
            "wcag": browser_accessibility["wcag"],
            "source": "browser",
        }

    accessibility_checker = AccessibilityChecker(html or "")
    accessibility_raw = accessibility_checker.run_all_checks()
    return {
        "raw": accessibility_raw,
        "formatted": format_accessibility_result(accessibility_raw, mode=mode),
        "wcag": get_wcag_compliance_level(accessibility_raw),
        "source": "html",
    }


def run_full_site_health_check(
    url: str,
    html: str,
    mode: str = "simple",
    headers: Optional[Dict[str, Any]] = None,
    force_is_ec: Optional[bool] = None,
    sitemap_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """全チェック（法的、OGP、セキュリティ、アクセシビリティ、構造化データ）を統合実行"""
    headers = headers or {}
    soup = BeautifulSoup(html or "", "html.parser")

    json_ld = _extract_json_ld(soup)

    # 事業タイプ判定
    business_type_result = detect_business_type(html or "", url, json_ld)
    business_type = business_type_result.get("primary_type", "article")
    schema_site_type = infer_schema_site_type(html or "", url, schemas=json_ld, hinted_type=business_type)

    # These checks only read the fetched HTML/headers (plus bounded public endpoint
    # checks inside SecurityChecker), so they can run in parallel without changing
    # scoring or issue semantics.
    with ThreadPoolExecutor(max_workers=3) as executor:
        ogp_future = executor.submit(_run_ogp_check, html or "", url, mode)
        security_future = executor.submit(
            _run_security_check,
            url,
            dict(headers),
            html or "",
            mode,
            sitemap_info,
        )
        accessibility_future = executor.submit(_run_accessibility_check, html or "", url, mode)

        ogp_result = ogp_future.result()
        security_result = security_future.result()
        accessibility_result = accessibility_future.result()

    site_health = {
        "ogp": ogp_result,
        "security": security_result,
        "accessibility": accessibility_result,
    }

    # 構造化データサマリー
    try:
        structured_checker = StructuredDataChecker()
        site_health["structured_data"] = structured_checker.check(html or "", url)
    except Exception:
        site_health["structured_data"] = {}
    try:
        site_health["structured_data"]["schema_validation"] = validate_schema(json_ld, schema_site_type)
    except Exception:
        site_health["structured_data"]["schema_validation"] = {}
    site_health["structured_data"]["schema_site_type"] = schema_site_type

    # 構造化データ提案
    schema_suggester = SchemaSuggester()
    schema_suggestions = schema_suggester.suggest_schemas(
        business_type,
        {"json_ld": json_ld},
    )
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()
    og_image = ogp_result.get("formatted", {}).get("preview", {}).get("image") or "https://example.com/ogp-image.jpg"
    page_data = {
        "title": title,
        "description": meta_desc,
        "url": url,
        "image": og_image,
    }
    for item in schema_suggestions:
        schema_type = item.get("schema_type")
        item["template"] = generate_schema_template(schema_type, page_data)
        item["explanation"] = get_schema_explanation(schema_type, mode=mode)

    schema_existing = analyze_existing_schema(json_ld)
    schema_faq = get_schema_faq()
    faq_detection = build_faq_detection(json_ld, soup)

    # 法的チェック
    legal_checks: Dict[str, Any] = {}
    visibility_issues: List[Dict[str, Any]] = []
    best_practice_issues: List[Dict[str, Any]] = []
    lawyer_report: List[Dict[str, Any]] = []
    ec_detection: Dict[str, Any] = {
        "score": 0,
        "is_ec": True,
        "confidence": "unknown",
        "detected_indicators": [],
        "recommendation": "",
    }
    try:
        ec_detector = ECDetector(html or "", url, json_ld)
        ec_detection = ec_detector.calculate_ec_score()
    except Exception:
        pass
    if force_is_ec is not None:
        ec_detection["is_ec"] = force_is_ec
        ec_detection["confidence"] = "forced"
        if not force_is_ec:
            ec_detection["recommendation"] = ""
    try:
        consumer_checker = ConsumerProtectionChecker()
        consumer_result = consumer_checker.check(
            html or "",
            url,
            is_ec=bool(ec_detection.get("is_ec", True)),
        )
        visibility_issues = consumer_result.get("visibility", [])
        best_practice_issues = consumer_result.get("best_practices", [])
        lawyer_report = consumer_result.get("lawyer_report", [])
        legal_checks["consumer_protection"] = consumer_result
    except Exception:
        legal_checks["consumer_protection"] = {
            "visibility": visibility_issues,
            "best_practices": best_practice_issues,
            "lawyer_report": lawyer_report,
        }

    try:
        premiums_checker = PremiumsLabelingChecker(html or "", business_type=business_type)
        premiums_result = premiums_checker.run_all_checks()
        legal_checks["premiums_labeling"] = {
            "raw": premiums_result,
            "formatted": format_check_result(premiums_result, mode=mode),
        }
    except Exception:
        legal_checks["premiums_labeling"] = {}

    try:
        stealth_checker = StealthMarketingChecker(html or "", url)
        stealth_result = stealth_checker.evaluate_compliance()
        legal_checks["stealth_marketing"] = {
            "raw": stealth_result,
            "formatted": format_stealth_marketing_result(stealth_result, mode=mode),
        }
    except Exception:
        legal_checks["stealth_marketing"] = {}

    if force_is_ec is False:
        legal_checks["commercial_transaction"] = {"ec_detection": ec_detection}
    else:
        try:
            legal_html, frame_sources = augment_html_with_embedded_docs(html or "", url)
            legal_html, related_sources = augment_html_with_related_pages(legal_html, url)
            legal_soup = BeautifulSoup(legal_html, "html.parser")
            tokushoho_link = find_tokushoho_page(legal_soup, url)
            commercial_checker = CommercialTransactionChecker(legal_html, url, is_ec=ec_detection.get("is_ec"))
            commercial_result = commercial_checker.generate_compliance_report()
            commercial_formatted = format_commercial_transaction_result(
                commercial_result,
                ec_detection,
                mode=mode,
                visibility_issues=visibility_issues,
            )
            legal_checks["commercial_transaction"] = {
                "ec_detection": ec_detection,
                "tokushoho_page": tokushoho_link,
                "raw": commercial_result,
                "formatted": commercial_formatted,
                "template": generate_template_suggestion(commercial_result.get("check_result", {})),
                "frame_sources": frame_sources,
                "related_sources": related_sources,
            }
        except Exception:
            legal_checks["commercial_transaction"] = {}

    return {
        "site_health": site_health,
        "schema_suggestions": schema_suggestions,
        "schema_existing": schema_existing,
        "schema_faq": schema_faq,
        "faq_detection": faq_detection,
        "business_type_detection": business_type_result,
        "legal_checks": legal_checks,
    }
