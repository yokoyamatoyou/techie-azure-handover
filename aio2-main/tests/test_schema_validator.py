from __future__ import annotations

import threading
from types import SimpleNamespace

import core.engine.site_health_engine as site_health_mod
from core.aio.schema_validator import infer_schema_site_type, validate_schema


def test_infer_schema_site_type_detects_article() -> None:
    html = """
    <html>
      <head><meta property="og:type" content="article" /></head>
      <body><article><h1>記事タイトル</h1><time>2026-04-06</time></article></body>
    </html>
    """

    inferred = infer_schema_site_type(html, "https://example.com/blog/post")

    assert inferred == "article"


def test_validate_schema_flags_article_required_fields() -> None:
    schemas = [
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "記事タイトル",
        }
    ]

    result = validate_schema(schemas, site_type="article")

    assert result["site_type"] == "article"
    assert "BreadcrumbList" in result["missing_recommended"]
    assert result["has_required_fields"] is False
    assert any(issue["type"] == "Article" for issue in result["required_field_issues"])


def test_run_full_site_health_check_adds_schema_validation(monkeypatch) -> None:
    monkeypatch.setattr(site_health_mod, "detect_business_type", lambda html, url, json_ld: {"primary_type": "article"})
    monkeypatch.setattr(site_health_mod, "OGPChecker", lambda html, url: SimpleNamespace(run_all_checks=lambda: {"ogp": {}}))
    monkeypatch.setattr(site_health_mod, "format_ogp_result", lambda payload, mode="simple": {"preview": {}})
    monkeypatch.setattr(site_health_mod, "get_platform_specific_suggestions", lambda payload: [])
    monkeypatch.setattr(site_health_mod, "SecurityChecker", lambda url, headers, html, sitemap_info=None: SimpleNamespace(run_all_checks=lambda: {}))
    monkeypatch.setattr(site_health_mod, "format_security_result", lambda payload, mode="simple": {})
    monkeypatch.setattr(site_health_mod, "AccessibilityChecker", lambda html: SimpleNamespace(run_all_checks=lambda: {}))
    monkeypatch.setattr(site_health_mod, "format_accessibility_result", lambda payload, mode="simple": {})
    monkeypatch.setattr(site_health_mod, "get_wcag_compliance_level", lambda payload: {})
    monkeypatch.setattr(site_health_mod, "StructuredDataChecker", lambda: SimpleNamespace(check=lambda html, url: {"status": "ok"}))
    monkeypatch.setattr(site_health_mod, "SchemaSuggester", lambda: SimpleNamespace(suggest_schemas=lambda business_type, payload: []))
    monkeypatch.setattr(site_health_mod, "generate_schema_template", lambda schema_type, page_data: {})
    monkeypatch.setattr(site_health_mod, "get_schema_explanation", lambda schema_type, mode="simple": "")
    monkeypatch.setattr(site_health_mod, "analyze_existing_schema", lambda json_ld: {})
    monkeypatch.setattr(site_health_mod, "get_schema_faq", lambda: [])
    monkeypatch.setattr(site_health_mod, "build_faq_detection", lambda json_ld, soup: {"items": []})
    monkeypatch.setattr(site_health_mod, "ECDetector", lambda html, url, json_ld: SimpleNamespace(calculate_ec_score=lambda: {"is_ec": False}))
    monkeypatch.setattr(
        site_health_mod,
        "ConsumerProtectionChecker",
        lambda: SimpleNamespace(check=lambda html, url, is_ec=True: {"visibility": [], "best_practices": [], "lawyer_report": []}),
    )
    monkeypatch.setattr(
        site_health_mod,
        "PremiumsLabelingChecker",
        lambda html, business_type=None: SimpleNamespace(run_all_checks=lambda: {}),
    )
    monkeypatch.setattr(site_health_mod, "format_check_result", lambda payload, mode="simple": {})
    monkeypatch.setattr(
        site_health_mod,
        "StealthMarketingChecker",
        lambda html, url: SimpleNamespace(evaluate_compliance=lambda: {}),
    )
    monkeypatch.setattr(site_health_mod, "format_stealth_marketing_result", lambda payload, mode="simple": {})

    html = """
    <html>
      <head>
        <title>記事タイトル</title>
        <script type="application/ld+json">
        {"@context": "https://schema.org", "@type": "Article", "headline": "記事タイトル"}
        </script>
      </head>
      <body><article><h1>記事タイトル</h1></article></body>
    </html>
    """

    result = site_health_mod.run_full_site_health_check("https://example.com/blog/post", html, mode="simple", headers={})

    structured_data = result["site_health"]["structured_data"]
    assert structured_data["schema_site_type"] == "article"
    assert structured_data["schema_validation"]["site_type"] == "article"
    assert structured_data["schema_validation"]["has_required_fields"] is False


def test_run_full_site_health_check_runs_independent_health_checks_in_parallel(monkeypatch) -> None:
    started = set()
    started_lock = threading.Lock()
    all_started = threading.Event()

    def mark_started(name: str, payload):
        with started_lock:
            started.add(name)
            if len(started) == 3:
                all_started.set()
        assert all_started.wait(timeout=2), f"{name} did not overlap with the other health checks"
        return payload

    monkeypatch.setattr(site_health_mod, "detect_business_type", lambda html, url, json_ld: {"primary_type": "article"})
    monkeypatch.setattr(
        site_health_mod,
        "OGPChecker",
        lambda html, url: SimpleNamespace(run_all_checks=lambda: mark_started("ogp", {"ogp": {}})),
    )
    monkeypatch.setattr(site_health_mod, "format_ogp_result", lambda payload, mode="simple": {"preview": {}})
    monkeypatch.setattr(site_health_mod, "get_platform_specific_suggestions", lambda payload: [])
    monkeypatch.setattr(
        site_health_mod,
        "SecurityChecker",
        lambda url, headers, html, sitemap_info=None: SimpleNamespace(
            run_all_checks=lambda: mark_started("security", {})
        ),
    )
    monkeypatch.setattr(site_health_mod, "format_security_result", lambda payload, mode="simple": {})
    monkeypatch.setattr(site_health_mod, "browser_accessibility_enabled", lambda: False)
    monkeypatch.setattr(
        site_health_mod,
        "AccessibilityChecker",
        lambda html: SimpleNamespace(run_all_checks=lambda: mark_started("accessibility", {})),
    )
    monkeypatch.setattr(site_health_mod, "format_accessibility_result", lambda payload, mode="simple": {})
    monkeypatch.setattr(site_health_mod, "get_wcag_compliance_level", lambda payload: {})
    monkeypatch.setattr(site_health_mod, "StructuredDataChecker", lambda: SimpleNamespace(check=lambda html, url: {}))
    monkeypatch.setattr(site_health_mod, "SchemaSuggester", lambda: SimpleNamespace(suggest_schemas=lambda business_type, payload: []))
    monkeypatch.setattr(site_health_mod, "analyze_existing_schema", lambda json_ld: {})
    monkeypatch.setattr(site_health_mod, "get_schema_faq", lambda: [])
    monkeypatch.setattr(site_health_mod, "build_faq_detection", lambda json_ld, soup: {"items": []})
    monkeypatch.setattr(site_health_mod, "ECDetector", lambda html, url, json_ld: SimpleNamespace(calculate_ec_score=lambda: {"is_ec": False}))
    monkeypatch.setattr(
        site_health_mod,
        "ConsumerProtectionChecker",
        lambda: SimpleNamespace(check=lambda html, url, is_ec=True: {"visibility": [], "best_practices": [], "lawyer_report": []}),
    )
    monkeypatch.setattr(site_health_mod, "PremiumsLabelingChecker", lambda html, business_type=None: SimpleNamespace(run_all_checks=lambda: {}))
    monkeypatch.setattr(site_health_mod, "format_check_result", lambda payload, mode="simple": {})
    monkeypatch.setattr(site_health_mod, "StealthMarketingChecker", lambda html, url: SimpleNamespace(evaluate_compliance=lambda: {}))
    monkeypatch.setattr(site_health_mod, "format_stealth_marketing_result", lambda payload, mode="simple": {})

    result = site_health_mod.run_full_site_health_check("https://example.com/", "<html><head></head><body></body></html>")

    assert started == {"ogp", "security", "accessibility"}
    assert set(result["site_health"]) >= {"ogp", "security", "accessibility"}
