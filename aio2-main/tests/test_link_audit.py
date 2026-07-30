from __future__ import annotations

from dataclasses import dataclass, field

from core.seo.link_audit import audit_internal_urls, combine_link_health_reports


@dataclass
class _FakeResponse:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)
    safe_final_url: str = ""
    safe_redirect_count: int = 0
    safe_redirect_chain: list[str] = field(default_factory=list)


def test_audit_internal_urls_classifies_redirects_canonical_and_noindex() -> None:
    payloads = {
        "https://example.com/": _FakeResponse(
            status_code=200,
            text="<html><head><link rel='canonical' href='https://example.com/'></head><body></body></html>",
            safe_final_url="https://example.com/",
            safe_redirect_chain=["https://example.com/"],
        ),
        "https://example.com/old": _FakeResponse(
            status_code=200,
            text="<html><head><link rel='canonical' href='https://example.com/canonical-target'></head><body></body></html>",
            safe_final_url="https://example.com/new",
            safe_redirect_count=1,
            safe_redirect_chain=["https://example.com/old", "https://example.com/new"],
        ),
        "https://example.com/noindex": _FakeResponse(
            status_code=200,
            text="<html><head><meta name='robots' content='noindex'></head><body></body></html>",
            safe_final_url="https://example.com/noindex",
            safe_redirect_chain=["https://example.com/noindex"],
        ),
        "https://example.com/missing": _FakeResponse(
            status_code=404,
            text="<html><body>missing</body></html>",
            safe_final_url="https://example.com/missing",
            safe_redirect_chain=["https://example.com/missing"],
        ),
    }

    def fake_fetch(url: str, **kwargs):  # noqa: ANN001
        return payloads[url]

    result = audit_internal_urls(
        [
            "https://example.com/",
            "https://example.com/old#fragment",
            "https://example.com/noindex",
            "https://example.com/missing",
        ],
        fetcher=fake_fetch,
        max_urls=10,
    )

    assert result["audited_target_count"] == 4
    assert result["broken_target_count"] == 1
    assert result["redirected_target_count"] == 1
    assert result["canonical_mismatch_count"] == 1
    assert result["noindex_target_count"] == 1


def test_combine_link_health_reports_penalizes_target_issues() -> None:
    combined = combine_link_health_reports(
        {
            "health_score": 88.0,
            "diagnosis": "内部リンク構造は良好です。",
        },
        {
            "audited_target_count": 4,
            "broken_target_count": 1,
            "redirected_target_count": 1,
            "canonical_mismatch_count": 0,
            "noindex_target_count": 0,
        },
    )

    assert combined["health_score"] < 88.0
    assert combined["target_health_score"] < 100.0
    assert "エラー" in combined["diagnosis"]
