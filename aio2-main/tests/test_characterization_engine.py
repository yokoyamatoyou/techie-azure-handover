from __future__ import annotations

from types import SimpleNamespace

import core.engine.orchestrator as orchestrator_mod
from core.engine.orchestrator import SEOAIOAnalyzer


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
        self.pages = []

    def add_page(self, url: str, links) -> None:  # type: ignore[no-untyped-def]
        self.pages.append((url, list(links or [])))

    def get_summary(self) -> dict:
        return {"page_count": len(self.pages)}

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

    analyzer._check_scrape_permission = lambda url: {"allowed": True}  # type: ignore[method-assign]
    analyzer._extract_main_content = lambda soup, max_chars=5000: "本文の要約"  # type: ignore[method-assign]
    analyzer._classify_intent = lambda url, title, meta, body: {"intent": "informational"}  # type: ignore[method-assign]
    analyzer._determine_final_industry = lambda user_industry, analysis: {"primary": "一般"}  # type: ignore[method-assign]
    analyzer._analyze_seo = lambda soup, url, html="": {  # type: ignore[method-assign]
        "scores": {},
        "details": {"tech_stack": ["WordPress"]},
        "structure": {"headings": {"h1": "見出し"}, "internal_links_count": 1, "external_links_count": 0, "images_count": 0, "images_without_alt": 0},
        "personalization": {"structured_data_issues": [], "structured_data_types": []},
        "basics": {"title": "Example Title", "meta_description": "Example Description"},
        "content": {"word_count": 1200, "text_html_ratio": 0.42},
        "technical": {"canonical_url": "https://example.com", "has_viewport": True},
        "immediate_actions": [],
    }
    analyzer._create_seo_score_graph = lambda: None  # type: ignore[method-assign]
    analyzer._get_platform_guidance = lambda platform: {  # type: ignore[method-assign]
        "label": platform or "WordPress",
        "business_steps": ["基本設定を確認する"],
        "technical_steps": ["noindex設定を確認する"],
    }
    analyzer._build_platform_seo_actions = lambda guidance: []  # type: ignore[method-assign]
    analyzer._analyze_aio = lambda *args, **kwargs: {  # type: ignore[method-assign]
        "scores": {},
        "score_breakdown": {},
        "details": {},
        "immediate_actions": [],
        "penalties": [],
    }
    analyzer._create_aio_score_graph = lambda: None  # type: ignore[method-assign]
    analyzer._integrate_results = lambda *args, **kwargs: {  # type: ignore[method-assign]
        "improvements": ["見出し構造を明確にする"],
        "warnings": [],
        "integrated_score": 75.0,
    }
    analyzer._monitor_ai_search_performance = lambda url, integrated, aio: {  # type: ignore[method-assign]
        "history_count": 1,
        "recent_entries": [],
    }
    analyzer._generate_deep_recommendations = lambda *args, **kwargs: {  # type: ignore[method-assign]
        "business": [],
        "technical": [],
    }
    analyzer._apply_legal_context_adjustment = lambda **kwargs: kwargs["legal_checks"]  # type: ignore[method-assign]
    analyzer._run_output_gate = lambda **kwargs: {  # type: ignore[method-assign]
        "status": "warn",
        "reason": "characterization",
    }
    return analyzer


def test_analyze_url_returns_core_result_shape(monkeypatch) -> None:
    analyzer = _build_analyzer_stub()
    html = """
    <html>
      <head>
        <title>Example Title</title>
        <meta name="description" content="Example Description" />
      </head>
      <body>
        <h1>見出し</h1>
        <p>本文の例です。</p>
        <a href="/privacy">privacy</a>
      </body>
    </html>
    """

    monkeypatch.setattr(orchestrator_mod, "safe_fetch_url", lambda *args, **kwargs: _FakeResponse(html))
    monkeypatch.setattr(orchestrator_mod, "fetch_sitemap_urls", lambda url: {"total_urls": 1, "sampled_urls": []})
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

    assert result["url"] == "https://example.com"
    assert "seo_results" in result
    assert "aio_results" in result
    assert "integrated_results" in result
    assert "output_gate" in result
    assert "analysis_meta" in result
    assert result["analysis_meta"]["progress_log"]
    assert result["platform"]["effective"] == "WordPress"
    assert result["summary"]["improvements"] == ["見出し構造を明確にする"]

def test_monitoring_history_wrappers_delegate_to_store(monkeypatch, tmp_path) -> None:
    analyzer = object.__new__(SEOAIOAnalyzer)
    captured = {}
    monitoring_path = str(tmp_path / "aio_monitoring.json")

    monkeypatch.setattr(orchestrator_mod, "get_monitoring_history_path", lambda: monitoring_path)
    monkeypatch.setattr(
        orchestrator_mod,
        "load_monitoring_history",
        lambda *, path=None, cwd=None: captured.setdefault("load", {"path": path, "cwd": cwd}) or [{"url": "x"}],
    )
    monkeypatch.setattr(
        orchestrator_mod,
        "save_monitoring_history",
        lambda history, *, path=None, cwd=None: captured.setdefault("save", {"history": history, "path": path, "cwd": cwd}),
    )

    assert analyzer._get_monitoring_path() == monitoring_path
    analyzer._load_monitoring_history()
    analyzer._save_monitoring_history([{"url": "https://example.com"}])

    assert captured["load"]["path"] == monitoring_path
    assert captured["save"]["path"] == monitoring_path
    assert captured["save"]["history"] == [{"url": "https://example.com"}]
