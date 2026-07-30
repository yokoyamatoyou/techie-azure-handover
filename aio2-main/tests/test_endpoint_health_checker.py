from __future__ import annotations

from types import SimpleNamespace
from typing import Callable

import core.site_health.endpoint_health_checker as endpoint_mod
from core.application.technical_summary_builder import build_site_health_checks
from core.site_health.endpoint_health_checker import audit_endpoint_health
from core.site_health.security_checker import SecurityChecker


HOME_HTML = """
<html>
  <head><title>Example Co</title></head>
  <body><main><h1>Example Co</h1><p>会社案内とお問い合わせ</p></main></body>
</html>
"""


def _response(status: int, text: str = "", *, content_type: str = "text/plain", final_url: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        status_code=status,
        text=text,
        headers={"Content-Type": content_type},
        safe_final_url=final_url,
        safe_redirect_count=0,
        url=final_url,
    )


def _with_fake_fetch(fake_fetch: Callable[..., SimpleNamespace], callback: Callable[[], None]) -> None:
    original = endpoint_mod.safe_fetch_url
    endpoint_mod.safe_fetch_url = fake_fetch
    try:
        callback()
    finally:
        endpoint_mod.safe_fetch_url = original


def test_endpoint_health_detects_robots_html_200() -> None:
    def fake_fetch(url: str, **_: object) -> SimpleNamespace:
        if url.endswith("/robots.txt"):
            return _response(200, HOME_HTML, content_type="text/html", final_url=url)
        return _response(404, "", final_url=url)

    def run() -> None:
        result = audit_endpoint_health("https://example.com/", HOME_HTML, {}, missing_path="missing-one/")
        issue_ids = {item["id"] for item in result["issues"]}
        issue = next(item for item in result["issues"] if item["id"] == "robots_txt_html_fake_200")

        assert "robots_txt_html_fake_200" in issue_ids
        assert issue["http_status"] == 200
        assert issue["content_type"] == "text/html"
        assert "Example Co" in issue["excerpt"]

    _with_fake_fetch(fake_fetch, run)


def test_endpoint_health_detects_sitemap_html_and_unused_wp_endpoint_fake_200() -> None:
    def fake_fetch(url: str, **_: object) -> SimpleNamespace:
        if url.endswith("/sitemap.xml"):
            return _response(200, "<html><title>Not XML</title></html>", content_type="text/html", final_url=url)
        if url.endswith("/wp-sitemap.xml"):
            return _response(200, HOME_HTML, content_type="text/html", final_url=url)
        return _response(404, "", final_url=url)

    def run() -> None:
        result = audit_endpoint_health("https://example.com/", HOME_HTML, {}, missing_path="missing-two/")
        issue_ids = {item["id"] for item in result["issues"]}

        assert "sitemap_endpoint_html_fake_200" in issue_ids
        assert "unused_endpoint_fake_200" in issue_ids

    _with_fake_fetch(fake_fetch, run)


def test_endpoint_health_detects_soft_404_single_missing_url() -> None:
    def fake_fetch(url: str, **_: object) -> SimpleNamespace:
        if url.endswith("/missing-three/"):
            return _response(200, HOME_HTML, content_type="text/html", final_url=url)
        return _response(404, "", final_url=url)

    def run() -> None:
        result = audit_endpoint_health("https://example.com/", HOME_HTML, {}, missing_path="missing-three/")
        issue_ids = {item["id"] for item in result["issues"]}
        checked_missing = [row for row in result["checked_endpoints"] if row["url"].endswith("/missing-three/")]

        assert "soft_404_missing_url_200" in issue_ids
        assert len(checked_missing) == 1

    _with_fake_fetch(fake_fetch, run)


def test_endpoint_health_detects_php_and_plesklin_header_exposure() -> None:
    def fake_fetch(url: str, **_: object) -> SimpleNamespace:
        return _response(404, "", final_url=url)

    def run() -> None:
        result = audit_endpoint_health(
            "https://example.com/",
            HOME_HTML,
            {"X-Powered-By": "PHP/5.6.40, PleskLin"},
            missing_path="missing-four/",
        )
        issue = next(item for item in result["issues"] if item["id"] == "server_environment_header_exposed")

        assert issue["severity"] == "high"
        assert "PHP/5.6.40" in issue["detail"]
        assert "PleskLin" in issue["detail"]

    _with_fake_fetch(fake_fetch, run)


def test_public_technology_risks_detects_personal_form_without_public_protection_hints() -> None:
    html = """
    <html><body>
      <form method="post" action="/contact">
        <input name="name" placeholder="お名前">
        <input name="email" type="email">
        <textarea name="symptom" placeholder="症状や相談内容"></textarea>
        <button>送信</button>
      </form>
    </body></html>
    """

    result = SecurityChecker("https://example.com/", {}, html, sitemap_info={}, enable_endpoint_health=False).check_public_technology_risks()
    issue_ids = {item["id"] for item in result["issues"]}
    form_row = result["signals"]["forms"]["forms"][0]

    assert "personal_form_without_public_protection_hints" in issue_ids
    assert form_row["has_personal_fields"] is True
    assert form_row["has_sensitive_context"] is True
    assert form_row["has_csrf_hint"] is False
    assert form_row["has_captcha_hint"] is False
    assert form_row["has_privacy_consent"] is False


def test_public_technology_risks_detects_https_internal_http_link() -> None:
    html = '<html><body><a href="http://example.com/contact/">Contact</a></body></html>'

    result = SecurityChecker("https://example.com/", {}, html, sitemap_info={}, enable_endpoint_health=False).check_public_technology_risks()
    issue_ids = {item["id"] for item in result["issues"]}

    assert "internal_http_navigation_link" in issue_ids


def test_site_health_checks_include_endpoint_engineer_task_details() -> None:
    results = {
        "url": "https://example.com/",
        "site_health": {
            "security": {
                "formatted": {"score": 55, "status": "要改善", "items": []},
                "raw": {
                    "public_technology_risks": {
                        "issues": [
                            {
                                "id": "robots_txt_html_fake_200",
                                "severity": "medium",
                                "title": "robots.txt がHTMLを返している可能性があります",
                                "detail": "robots.txt が 200 OK ですがHTML相当です。",
                                "recommendation": "robots.txt として妥当なテキストを返してください。",
                                "evidence": "https://example.com/robots.txt",
                                "confirmation_url": "https://example.com/robots.txt",
                                "evidence_details": {
                                    "url": "https://example.com/robots.txt",
                                    "status_code": 200,
                                    "content_type": "text/html",
                                    "excerpt": "<html><title>Example</title>",
                                    "urgency": "すぐ確認",
                                },
                            }
                        ],
                        "signals": {},
                    }
                },
            }
        },
    }

    checks = build_site_health_checks(results)
    security = next(item for item in checks if item["key"] == "security")
    task = security["engineer_tasks"][0]

    assert task["source"] == "robots_txt_html_fake_200"
    assert task["target"] == "https://example.com/robots.txt"
    assert "HTTP 200" in task["work"]
    assert "Content-Type: text/html" in task["work"]
    assert "curl -i https://example.com/robots.txt" in task["commands"][0]
    assert "robots.txt" in task["pass_condition"]
