from __future__ import annotations

from bs4 import BeautifulSoup

from core.engine.orchestrator import SEOAIOAnalyzer
from core.seo.international_audit import audit_international_targeting, audit_x_robots_tag


def test_audit_international_targeting_flags_missing_lang_and_x_default() -> None:
    soup = BeautifulSoup(
        """
        <html>
          <head>
            <link rel="alternate" hreflang="ja" href="https://example.com/ja/page" />
            <link rel="alternate" hreflang="en" href="https://example.com/en/page" />
          </head>
          <body><p>example</p></body>
        </html>
        """,
        "html.parser",
    )

    result = audit_international_targeting(soup, "https://example.com/ja/page")

    assert result["status"] == "fail"
    assert result["alternate_count"] == 2
    assert result["has_x_default"] is False
    messages = [issue["message"] for issue in result["issues"]]
    assert any("html lang" in message for message in messages)
    assert any("x-default" in message for message in messages)


def test_audit_x_robots_tag_parses_major_values() -> None:
    result = audit_x_robots_tag(
        {
            "X-Robots-Tag": [
                "noimageindex, max-image-preview:none",
                "max-video-preview:0",
            ]
        }
    )

    assert result["status"] == "warn"
    assert "noimageindex" in result["directives"]
    assert "max-image-preview:none" in result["directives"]
    assert "max-video-preview:0" in result["directives"]
    messages = [issue["message"] for issue in result["issues"]]
    assert any("画像" in message for message in messages)
    assert any("動画" in message for message in messages)


def test_analyze_seo_surfaces_international_and_x_robots(monkeypatch) -> None:
    analyzer = object.__new__(SEOAIOAnalyzer)
    analyzer._warnings = []
    analyzer._latest_response_headers = {"X-Robots-Tag": "noindex, max-image-preview:large"}

    monkeypatch.setattr(analyzer, "_extract_main_content", lambda soup, max_chars=5000: "本文 テスト")
    monkeypatch.setattr(
        analyzer,
        "_check_ai_crawler_access",
        lambda url: {"bots": {"googlebot": True, "oai-searchbot": True, "perplexitybot": True, "claude-searchbot": True}},
    )
    monkeypatch.setattr(analyzer, "_detect_ssr_needs", lambda soup, html: {"is_ssr_needed": False, "reasons": []})
    monkeypatch.setattr(
        analyzer,
        "_measure_inp",
        lambda url: ({"inp_ms": 180.0, "inp_grade": "good", "inp_note": "measured"}, None),
    )
    monkeypatch.setattr(analyzer, "_compute_domain_theme_similarity", lambda url, text: 0.9)

    soup = BeautifulSoup(
        """
        <html lang="ja">
          <head>
            <title>テストページ</title>
            <meta name="description" content="説明文です" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <link rel="canonical" href="https://example.com/page" />
            <link rel="alternate" hreflang="ja" href="https://example.com/page" />
            <link rel="alternate" hreflang="en" href="https://example.com/en/page" />
            <link rel="alternate" hreflang="x-default" href="https://example.com/" />
          </head>
          <body>
            <h1>見出し</h1>
            <p>本文です。</p>
            <a href="/about">会社概要</a>
          </body>
        </html>
        """,
        "html.parser",
    )

    result = SEOAIOAnalyzer._analyze_seo(analyzer, soup, "https://example.com/page")

    technical = result["technical"]
    assert technical["international_targeting"]["status"] == "pass"
    assert technical["international_targeting"]["html_lang"] == "ja"
    assert technical["international_targeting"]["has_x_default"] is True
    assert technical["x_robots_tag"]["status"] == "fail"
    assert "noindex" in technical["x_robots_tag"]["directives"]
    assert any("noindex" in warning for warning in analyzer._warnings)
