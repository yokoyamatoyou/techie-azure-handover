from __future__ import annotations

from bs4 import BeautifulSoup

from core.engine.orchestrator import SEOAIOAnalyzer
from core.seo.link_quality_audit import audit_link_quality


def test_audit_link_quality_detects_empty_generic_and_scripted_links() -> None:
    soup = BeautifulSoup(
        """
        <html>
          <body>
            <a href="#section"></a>
            <a href="/details">詳しくはこちら</a>
            <a href="/image-only"><img src="/hero.jpg" /></a>
            <button onclick="location.href='/contact'">お問い合わせ</button>
          </body>
        </html>
        """,
        "html.parser",
    )

    result = audit_link_quality(soup)

    assert result["status"] == "fail"
    assert result["non_crawlable_count"] == 1
    assert result["empty_anchor_count"] == 2
    assert result["generic_anchor_count"] == 1
    assert result["image_only_missing_alt_count"] == 1
    assert result["scripted_navigation_count"] == 1


def test_analyze_seo_surfaces_link_quality(monkeypatch) -> None:
    analyzer = object.__new__(SEOAIOAnalyzer)
    analyzer._warnings = []
    analyzer._latest_response_headers = {}

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
          </head>
          <body>
            <h1>見出し</h1>
            <a href="#top"></a>
            <a href="/about">詳しくはこちら</a>
            <a href="/contact"><img src="/hero.jpg" /></a>
          </body>
        </html>
        """,
        "html.parser",
    )

    result = SEOAIOAnalyzer._analyze_seo(analyzer, soup, "https://example.com/page")

    link_quality = result["structure"]["link_quality"]
    assert link_quality["status"] == "fail"
    assert link_quality["empty_anchor_count"] == 2
    assert link_quality["generic_anchor_count"] == 1
    assert any("アンカー" in warning or "リンク" in warning for warning in analyzer._warnings)
