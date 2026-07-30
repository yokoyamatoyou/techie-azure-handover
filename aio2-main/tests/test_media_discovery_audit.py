from __future__ import annotations

from types import SimpleNamespace

from bs4 import BeautifulSoup

import core.engine.orchestrator as orchestrator_mod
from core.engine.orchestrator import SEOAIOAnalyzer
from core.seo.media_discovery_audit import audit_media_discovery


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.status_code = 200
        self.text = text
        self.headers = {}
        self.ok = True
        self.apparent_encoding = "utf-8"
        self.elapsed = SimpleNamespace(total_seconds=lambda: 0.12)

    def raise_for_status(self) -> None:
        return None


class _FakeLinkGraph:
    def __init__(self, url: str) -> None:
        self.url = url

    def add_page(self, url: str, links) -> None:  # type: ignore[no-untyped-def]
        return None

    def get_summary(self) -> dict:
        return {"page_count": 1}

    def get_health_report(self, all_known_urls=None) -> dict:  # type: ignore[no-untyped-def]
        return {"known_urls": len(all_known_urls or [])}

    def build_audit_candidates(self, all_known_urls=None, limit=12) -> list[str]:  # type: ignore[no-untyped-def]
        return ["https://example.com/"]


class _FakeURLTypeDetector:
    def detect(self, html: str) -> str:
        return "コーポレートサイト"


def _build_analyzer_stub() -> SEOAIOAnalyzer:
    analyzer = object.__new__(SEOAIOAnalyzer)
    analyzer.client = SimpleNamespace(models=SimpleNamespace(list=lambda timeout=None: []))
    analyzer.industry_detector = SimpleNamespace(
        analyze_industries=lambda title, content, meta: {"primary": "一般"},
        check_regulatory_compliance=lambda content, industry: None,
    )
    analyzer.token_tracker = SimpleNamespace(get_summary=lambda: SimpleNamespace(total_requests=0))
    analyzer.last_analysis_results = None
    analyzer.seo_results = None
    analyzer.aio_results = None
    analyzer._warnings = []
    analyzer._latest_response_headers = {}

    analyzer._check_scrape_permission = lambda url: {"allowed": True}  # type: ignore[method-assign]
    analyzer._extract_main_content = lambda soup, max_chars=5000: "本文の要約"  # type: ignore[method-assign]
    analyzer._classify_intent = lambda url, title, meta, body: {"intent": "informational"}  # type: ignore[method-assign]
    analyzer._determine_final_industry = lambda user_industry, analysis: {"primary": "一般"}  # type: ignore[method-assign]
    analyzer._analyze_seo = lambda soup, url, html="": {  # type: ignore[method-assign]
        "scores": {},
        "details": {"tech_stack": ["WordPress"]},
        "structure": {"headings": {"h1": "見出し"}, "internal_links_count": 1, "external_links_count": 0, "images_count": 1, "images_without_alt": 0},
        "personalization": {"structured_data_issues": [], "structured_data_types": []},
        "basics": {"title": "Example Title", "meta_description": "Example Description"},
        "content": {"word_count": 1200, "text_html_ratio": 0.42},
        "technical": {"canonical_url": "https://example.com", "has_viewport": True},
        "immediate_actions": [],
    }
    analyzer._create_seo_score_graph = lambda: None  # type: ignore[method-assign]
    analyzer._get_platform_guidance = lambda platform: {"label": platform or "WordPress", "business_steps": [], "technical_steps": []}  # type: ignore[method-assign]
    analyzer._build_platform_seo_actions = lambda guidance: []  # type: ignore[method-assign]
    analyzer._analyze_aio = lambda *args, **kwargs: {"scores": {}, "score_breakdown": {}, "details": {}, "immediate_actions": [], "penalties": []}  # type: ignore[method-assign]
    analyzer._create_aio_score_graph = lambda: None  # type: ignore[method-assign]
    analyzer._integrate_results = lambda *args, **kwargs: {"improvements": [], "warnings": [], "integrated_score": 75.0}  # type: ignore[method-assign]
    analyzer._monitor_ai_search_performance = lambda url, integrated, aio: {"history_count": 1, "recent_entries": []}  # type: ignore[method-assign]
    analyzer._generate_deep_recommendations = lambda *args, **kwargs: {"business": [], "technical": []}  # type: ignore[method-assign]
    analyzer._apply_legal_context_adjustment = lambda **kwargs: kwargs["legal_checks"]  # type: ignore[method-assign]
    analyzer._run_output_gate = lambda **kwargs: {"status": "warn", "reason": "characterization"}  # type: ignore[method-assign]
    return analyzer


def test_audit_media_discovery_detects_missing_video_schema_and_sitemap() -> None:
    soup = BeautifulSoup(
        """
        <html>
          <body>
            <img data-src="/lazy.jpg" alt="" />
            <video controls><source src="/movie.mp4" type="video/mp4"></video>
          </body>
        </html>
        """,
        "html.parser",
    )

    result = audit_media_discovery(
        soup,
        sitemap_info={"media_hints": {"image_sitemap_detected": False, "video_sitemap_detected": False}},
    )

    assert result["status"] == "warn"
    assert result["image_discovery"]["deferred_images"] == 1
    assert result["video_discovery"]["video_count"] == 1
    messages = [issue["message"] for issue in result["issues"]]
    assert any("VideoObject" in message for message in messages)


def test_analyze_url_surfaces_media_discovery(monkeypatch) -> None:
    analyzer = _build_analyzer_stub()
    html = """
    <html>
      <head>
        <title>Example Title</title>
        <meta name="description" content="Example Description" />
      </head>
      <body>
        <h1>見出し</h1>
        <img data-src="/lazy.jpg" alt="" />
        <video controls><source src="/movie.mp4" type="video/mp4"></video>
        <a href="/privacy">privacy</a>
      </body>
    </html>
    """

    monkeypatch.setattr(orchestrator_mod, "safe_fetch_url", lambda *args, **kwargs: _FakeResponse(html))
    monkeypatch.setattr(
        orchestrator_mod,
        "fetch_sitemap_urls",
        lambda url: {
            "total_urls": 1,
            "sampled_urls": [],
            "media_hints": {"image_sitemap_detected": False, "video_sitemap_detected": False},
            "source_sitemaps": ["https://example.com/sitemap.xml"],
        },
    )
    monkeypatch.setattr(orchestrator_mod, "get_crawl_strategy", lambda soup, url: None)
    monkeypatch.setattr(orchestrator_mod, "InternalLinkGraph", _FakeLinkGraph)
    monkeypatch.setattr(orchestrator_mod, "URLTypeDetector", _FakeURLTypeDetector)
    monkeypatch.setattr(orchestrator_mod, "audit_internal_urls", lambda *args, **kwargs: {"audited_target_count": 1})
    monkeypatch.setattr(orchestrator_mod, "combine_link_health_reports", lambda base, audit: {**base, **audit})
    monkeypatch.setattr(orchestrator_mod, "extract_terms_from_text", lambda text, max_terms=10: ["用語"])
    monkeypatch.setattr(
        orchestrator_mod,
        "run_full_site_health_check",
        lambda *args, **kwargs: {
            "site_health": {},
            "schema_suggestions": [],
            "schema_existing": {},
            "schema_faq": [],
            "faq_detection": {"items": []},
            "business_type_detection": {},
            "legal_checks": {},
        },
    )
    monkeypatch.setattr(orchestrator_mod, "get_ec_faq_templates", lambda mode="simple": [])
    monkeypatch.setattr(orchestrator_mod, "extract_citation_snippets", lambda *args, **kwargs: {"snippets": []})
    monkeypatch.setattr(orchestrator_mod, "sort_texts_by_business_goal", lambda texts, goal: list(texts or []))
    monkeypatch.setattr(orchestrator_mod, "sort_actions_by_business_goal", lambda actions, *args, **kwargs: list(actions or []))
    monkeypatch.setattr(orchestrator_mod, "build_seo_reason_payload", None)
    monkeypatch.setattr(orchestrator_mod, "build_aio_reason_payload", None)

    result = analyzer.analyze_url(
        "example.com",
        "一般",
        50,
        deep_mode=False,
        platform_override=None,
        enable_question_simulation=False,
        url_type_selected="自動判定",
        business_goal="自動判定",
    )

    media_discovery = result["seo_results"]["technical"]["media_discovery"]
    assert media_discovery["status"] == "warn"
    assert media_discovery["video_discovery"]["video_count"] == 1
    assert media_discovery["sitemap_media"]["source_sitemaps"] == ["https://example.com/sitemap.xml"]
