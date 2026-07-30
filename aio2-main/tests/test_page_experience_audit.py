from __future__ import annotations

from bs4 import BeautifulSoup

from core.engine.orchestrator import SEOAIOAnalyzer
from core.seo.page_experience_audit import audit_page_experience


def test_audit_page_experience_flags_mobile_parity_and_cls_risk() -> None:
    soup = BeautifulSoup(
        """
        <html>
          <head>
            <title>Example</title>
          </head>
          <body>
            <div class="desktop-only">desktop hero</div>
            <img src="/hero.jpg" alt="hero" />
            <img src="/gallery.jpg" alt="gallery" />
          </body>
        </html>
        """,
        "html.parser",
    )

    result = audit_page_experience(
        soup,
        "https://example.com/page",
        page_size_kb=950.0,
        has_viewport=False,
        image_count=2,
        script_count=18,
        stylesheet_count=6,
    )

    assert result["mobile_parity"]["status"] == "fail"
    assert result["core_web_vitals"]["lcp_grade"] in {"needs_improvement", "poor"}
    assert result["core_web_vitals"]["cls_grade"] in {"good", "needs_improvement", "poor"}
    assert result["core_web_vitals"]["cls_score"] >= 0.09
    parity_messages = [issue["message"] for issue in result["mobile_parity"]["issues"]]
    assert any("viewport" in message for message in parity_messages)


def test_analyze_seo_adds_lcp_cls_and_mobile_parity(monkeypatch) -> None:
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
        lambda url: ({"inp_ms": 210.0, "inp_grade": "needs_improvement", "inp_note": "measured"}, None),
    )
    monkeypatch.setattr(analyzer, "_compute_domain_theme_similarity", lambda url, text: 0.9)

    soup = BeautifulSoup(
        """
        <html lang="ja">
          <head>
            <title>テストページ</title>
            <meta name="description" content="説明文です" />
          </head>
          <body>
            <div class="desktop-only">desktop only content</div>
            <h1>見出し</h1>
            <p>本文です。</p>
            <img src="/hero.jpg" alt="hero" />
            <script src="/bundle.js"></script>
            <script src="/extra.js"></script>
            <script src="/extra2.js"></script>
            <script src="/extra3.js"></script>
            <script src="/extra4.js"></script>
            <script src="/extra5.js"></script>
            <script src="/extra6.js"></script>
            <script src="/extra7.js"></script>
            <script src="/extra8.js"></script>
            <script src="/extra9.js"></script>
            <script src="/extra10.js"></script>
            <script src="/extra11.js"></script>
            <script src="/extra12.js"></script>
            <script src="/extra13.js"></script>
            <a href="/about">会社概要</a>
          </body>
        </html>
        """,
        "html.parser",
    )

    result = SEOAIOAnalyzer._analyze_seo(analyzer, soup, "https://example.com/page")

    assert result["technical"]["mobile_parity"]["status"] in {"warn", "fail"}
    assert result["technical"]["page_experience"]["measurement"] == "heuristic"
    assert result["web_vitals"]["inp_ms"] == 210.0
    assert result["web_vitals"]["lcp_ms"] is not None
    assert result["web_vitals"]["cls_score"] is not None
    assert any("viewport" in warning or "parity" in warning for warning in analyzer._warnings)
