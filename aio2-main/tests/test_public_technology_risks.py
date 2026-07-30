from __future__ import annotations

from types import SimpleNamespace

import core.site_health.security_checker as security_checker_mod
from core.sitemap_analyzer import _parse_sitemap_xml
from core.site_health.security_checker import SecurityChecker


def test_public_technology_risks_detects_wordpress_surface(monkeypatch) -> None:
    html = """
    <html>
      <head>
        <meta name="generator" content="WordPress 6.1" />
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.2.4/jquery.min.js"></script>
        <script src="//cdnjs.cloudflare.com/ajax/libs/html5shiv/3.7.2/html5shiv.min.js"></script>
        <script async src="https://www.googletagmanager.com/gtag/js?id=UA-221006340-1"></script>
      </head>
      <body><h1>Example</h1></body>
    </html>
    """
    headers = {"Link": '<https://example.com/wp-json/>; rel="https://api.w.org/"'}
    sitemap_info = {
        "total_urls": 43,
        "lastmod_dates": ["2022-03-01T01:43:27+00:00"],
        "parsed_sitemaps": 1,
        "generator_hint": "xml-sitemaps.com",
    }

    monkeypatch.setattr(
        security_checker_mod,
        "safe_fetch_url",
        lambda *args, **kwargs: SimpleNamespace(
            status_code=200,
            text='[{"id":1,"name":"admin","slug":"admin"}]',
        ),
    )

    result = SecurityChecker(
        "https://example.com/",
        headers,
        html,
        sitemap_info=sitemap_info,
        enable_endpoint_health=False,
    ).check_public_technology_risks()

    issue_ids = {item["id"] for item in result["issues"]}

    assert result["status"] == "warning"
    assert "cms_generator_public" in issue_ids
    assert "jquery_before_3_5" in issue_ids
    assert "external_cdn_without_sri" in issue_ids
    assert "universal_analytics_tag" in issue_ids
    assert "legacy_ie_polyfills" in issue_ids
    assert "wordpress_rest_users_public" in issue_ids
    assert "stale_or_static_sitemap" in issue_ids
    assert result["signals"]["wordpress_rest"]["public_users"][0]["slug"] == "admin"


def test_public_technology_risks_reuses_url_checker_static_asset_signals() -> None:
    html = """
    <html>
      <head>
        <script src="https://cdn.polyfill.io/v3/polyfill.min.js"></script>
        <link rel="stylesheet" href="https://staticfile.org/theme.css">
      </head>
      <body>
        <a href="https://external.example/" target="_blank">external</a>
        <a href="https://safe.example/" target="_blank" rel="noopener noreferrer">safe</a>
      </body>
    </html>
    """

    result = SecurityChecker("https://example.com/", {}, html, sitemap_info={}, enable_endpoint_health=False).check_public_technology_risks()
    issue_ids = {item["id"] for item in result["issues"]}

    assert "suspicious_external_asset_domain" in issue_ids
    assert "target_blank_without_noopener" in issue_ids
    assert "polyfill.io" in {
        item["matched_domain"]
        for item in result["signals"]["suspicious_external_assets"]
    }
    assert result["signals"]["target_blank_without_noopener"] == ["https://external.example/"]


def test_public_technology_risks_detects_frontend_asset_inventory() -> None:
    html = """
    <html>
      <head>
        <script src="https://cdn.example.com/bootstrap/3.4.1/js/bootstrap.min.js"></script>
        <script src="https://cdn.example.com/slick-carousel/1.8.1/slick.min.js"></script>
        <script src="https://cdn.example.com/modernizr-2.8.3.min.js"></script>
      </head>
      <body><h1>Example</h1></body>
    </html>
    """

    result = SecurityChecker("https://example.com/", {}, html, sitemap_info={}, enable_endpoint_health=False).check_public_technology_risks()
    issue_ids = {item["id"] for item in result["issues"]}

    assert "outdated_frontend_asset" in issue_ids
    labels = {item["label"] for item in result["signals"]["frontend_asset_inventory"]}
    assert {"bootstrap", "slick", "modernizr"}.issubset(labels)


def test_public_technology_risks_detects_versionless_jquery_asset_header(monkeypatch) -> None:
    html = """
    <html>
      <head>
        <script src="/js/jquery.js"></script>
        <script src="/js/jqueryAutoHeight.js"></script>
      </head>
      <body><h1>Example</h1></body>
    </html>
    """

    def fake_fetch(url: str, **_: object) -> SimpleNamespace:
        if url.endswith("/js/jquery.js"):
            return SimpleNamespace(
                status_code=200,
                text="/*! jQuery v1.7.1 jquery.com | jquery.org/license */\n(function(){})",
                headers={"Content-Type": "application/javascript"},
            )
        if url.endswith("/js/jqueryAutoHeight.js"):
            raise AssertionError("jQuery plugin should not be fetched as core jQuery")
        raise AssertionError(f"unexpected fetch: {url}")

    monkeypatch.setattr(security_checker_mod, "safe_fetch_url", fake_fetch)

    result = SecurityChecker("https://example.com/", {}, html, sitemap_info={}, enable_endpoint_health=False).check_public_technology_risks()
    issue_ids = {item["id"] for item in result["issues"]}

    assert "jquery_before_3_5" in issue_ids
    assert {
        "library": "jquery",
        "version": "1.7.1",
        "url": "https://example.com/js/jquery.js",
        "source": "asset_header",
    } in result["signals"]["library_versions"]


def test_public_technology_risks_detects_form_and_internal_http_risks() -> None:
    html = """
    <html>
      <body>
        <a href="http://example.com/contact/">Contact</a>
        <form id="contact" method="post" action="http://example.com/mail.php">
          <label>お名前 <input name="name"></label>
          <label>メール <input name="email" type="email"></label>
          <textarea name="message"></textarea>
          <button>送信</button>
        </form>
        <form id="upload" method="post" action="/upload">
          <input type="file" name="attachment">
        </form>
      </body>
    </html>
    """

    result = SecurityChecker("https://example.com/", {}, html, sitemap_info={}, enable_endpoint_health=False).check_public_technology_risks()
    issue_ids = {item["id"] for item in result["issues"]}

    assert "internal_http_navigation_link" in issue_ids
    assert "form_action_http" in issue_ids
    assert "personal_form_without_privacy_consent_hint" in issue_ids
    assert "personal_form_without_public_protection_hints" in issue_ids
    assert "post_form_without_csrf_hint" in issue_ids
    assert "file_upload_form_without_captcha_hint" in issue_ids
    assert result["signals"]["forms"]["form_count"] == 2
    assert result["signals"]["forms"]["forms"][0]["is_external_action"] is False


def test_public_technology_risks_does_not_treat_safe_search_form_as_contact_risk() -> None:
    html = """
    <html>
      <body>
        <form role="search" method="get" action="/search">
          <input type="search" name="q" placeholder="サイト内検索">
          <button>検索</button>
        </form>
      </body>
    </html>
    """

    result = SecurityChecker("https://example.com/", {}, html, sitemap_info={}, enable_endpoint_health=False).check_public_technology_risks()
    issue_ids = {item["id"] for item in result["issues"]}

    assert "personal_form_without_privacy_consent_hint" not in issue_ids
    assert "post_form_without_csrf_hint" not in issue_ids
    assert "form_action_http" not in issue_ids


def test_public_technology_risks_surfaces_sitemap_unavailable() -> None:
    result = SecurityChecker(
        "https://example.com/",
        {},
        "<html><body><h1>Example</h1></body></html>",
        sitemap_info={"error": "sitemap.xml が見つかりません（404）", "total_urls": 0},
        enable_endpoint_health=False,
    ).check_public_technology_risks()

    issue_ids = {item["id"] for item in result["issues"]}

    assert "sitemap_unavailable_or_invalid" in issue_ids
    assert result["signals"]["sitemap_availability"]["error"] == "sitemap.xml が見つかりません（404）"


def test_public_technology_risks_detects_old_visible_update_date() -> None:
    html = """
    <html>
      <body>
        <section class="news">
          <p>2022.03.01 重要なお知らせ</p>
          <p>2021年12月15日 過去のお知らせ</p>
        </section>
      </body>
    </html>
    """

    result = SecurityChecker("https://example.com/", {}, html, sitemap_info={}, enable_endpoint_health=False).check_public_technology_risks()
    issue_ids = {item["id"] for item in result["issues"]}

    assert "visible_update_date_old" in issue_ids
    assert result["signals"]["visible_update_freshness"]["newest_visible_date"] == "2022-03-01"


def test_public_technology_risks_keeps_recent_visible_date_as_signal_only() -> None:
    html = """
    <html>
      <body>
        <section class="news">
          <p>2026.05.01 新着情報</p>
        </section>
      </body>
    </html>
    """

    result = SecurityChecker("https://example.com/", {}, html, sitemap_info={}, enable_endpoint_health=False).check_public_technology_risks()
    issue_ids = {item["id"] for item in result["issues"]}

    assert "visible_update_date_old" not in issue_ids
    assert result["signals"]["visible_update_freshness"]["newest_visible_date"] == "2026-05-01"


def test_public_technology_risks_detects_update_signal_mismatch() -> None:
    html = """
    <html><body><p>2026.05.01 新着情報</p></body></html>
    """
    sitemap_info = {
        "total_urls": 3,
        "lastmod_dates": ["2022-03-01T01:43:27+00:00"],
        "parsed_sitemaps": 1,
    }

    result = SecurityChecker("https://example.com/", {}, html, sitemap_info=sitemap_info, enable_endpoint_health=False).check_public_technology_risks()
    issue_ids = {item["id"] for item in result["issues"]}

    assert "update_signal_mismatch" in issue_ids
    signal = result["signals"]["update_signal_consistency"]
    assert signal["status"] == "要確認"
    assert signal["visible_date"] == "2026-05-01"
    assert signal["sitemap_lastmod"] == "2022-03-01"


def test_public_technology_risks_avoids_rest_probe_without_wordpress_hint(monkeypatch) -> None:
    html = "<html><head><title>Clean</title></head><body><h1>Clean</h1></body></html>"

    def fail_fetch(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("REST endpoint should not be fetched without a WordPress hint")

    monkeypatch.setattr(security_checker_mod, "safe_fetch_url", fail_fetch)

    result = SecurityChecker("https://example.com/", {}, html, sitemap_info={}, enable_endpoint_health=False).check_public_technology_risks()

    assert result["status"] == "ok"
    assert result["issues"] == []


def test_sitemap_analyzer_keeps_static_generator_hint() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <!-- created with Free Online Sitemap Generator www.xml-sitemaps.com -->
      <url>
        <loc>https://example.com/</loc>
        <lastmod>2022-03-01T01:43:27+00:00</lastmod>
      </url>
    </urlset>
    """

    result = _parse_sitemap_xml(
        xml,
        root_url="https://example.com",
        depth=0,
        visited={"https://example.com/sitemap.xml"},
        fetch_queue_count=1,
    )

    assert result["generator_hint"] == "xml-sitemaps.com"
