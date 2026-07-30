from __future__ import annotations

from dataclasses import dataclass, field

from core.seo.legacy_page_probe import audit_legacy_html_pages


@dataclass
class _FakeResponse:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)
    safe_final_url: str = ""
    url: str = ""


def test_audit_legacy_html_pages_reports_only_indexable_html_without_canonical() -> None:
    payloads = {
        "https://example.com/data.html": _FakeResponse(
            status_code=200,
            text="<html><head><title>Old data</title><meta name='robots' content='index,follow'></head></html>",
            safe_final_url="https://example.com/data.html",
        ),
        "https://example.com/system.html": _FakeResponse(
            status_code=200,
            text="<html><head><meta name='robots' content='noindex'></head></html>",
            safe_final_url="https://example.com/system.html",
        ),
        "https://example.com/company.html": _FakeResponse(
            status_code=200,
            text="<html><head><link rel='canonical' href='https://example.com/about/'></head></html>",
            safe_final_url="https://example.com/about/",
        ),
    }

    def fake_fetch(url: str, **kwargs):  # noqa: ANN001
        return payloads.get(
            url,
            _FakeResponse(status_code=404, text="", safe_final_url=url),
        )

    result = audit_legacy_html_pages(
        "https://example.com/",
        fetcher=fake_fetch,
        max_candidates=3,
    )

    assert result["status"] == "fail"
    assert result["found_count"] == 1
    assert result["pages"][0]["final_url"] == "https://example.com/data.html"
    assert result["pages"][0]["reason"] == "200 / index可能 / canonicalなし"


def test_audit_legacy_html_pages_uses_slug_candidates_but_stays_bounded() -> None:
    checked = []

    def fake_fetch(url: str, **kwargs):  # noqa: ANN001
        checked.append(url)
        return _FakeResponse(status_code=404, text="", safe_final_url=url)

    result = audit_legacy_html_pages(
        "https://example.com/",
        known_urls=["https://example.com/service/rpa/"],
        fetcher=fake_fetch,
        max_candidates=21,
    )

    assert result["status"] == "pass"
    assert result["found_count"] == 0
    assert "https://example.com/rpa.html" in checked
