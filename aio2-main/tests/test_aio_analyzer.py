from __future__ import annotations

import json
from pathlib import Path

from bs4 import BeautifulSoup
import pytest

from core.aio_analyzer import AIOContentAnalyzer


class _FakeResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


def test_check_technical_aio_separates_official_and_informational_bots(monkeypatch) -> None:
    analyzer = AIOContentAnalyzer(enable_wikidata=False)

    def fake_fetch(url: str, **kwargs):  # noqa: ANN001
        if url.endswith("/llms.txt"):
            return _FakeResponse(404, "")
        return _FakeResponse(
            200,
            "\n".join(
                [
                    "User-agent: Googlebot",
                    "Allow: /",
                    "User-agent: OAI-SearchBot",
                    "Allow: /",
                    "User-agent: PerplexityBot",
                    "Allow: /",
                    "User-agent: Claude-SearchBot",
                    "Allow: /",
                    "User-agent: GPTBot",
                    "Disallow: /",
                    "User-agent: Google-Extended",
                    "Disallow: /",
                ]
            ),
        )

    monkeypatch.setattr("core.aio_analyzer.safe_fetch_url", fake_fetch)

    result = analyzer.check_technical_aio("https://example.com/article", response_time_ms=800)

    assert result["llms_txt"] is False
    assert result["ai_bots_blocked"] is False
    assert result["google_extended_disallowed"] is True
    assert result["bot_access"]["oai-searchbot"] is True
    assert result["bot_access"]["claude-searchbot"] is True
    assert result["bot_access"]["gptbot"] is False
    assert result["score"] == 0.9


def test_analyze_returns_provider_readiness_statuses(monkeypatch) -> None:
    analyzer = AIOContentAnalyzer(enable_wikidata=False)

    def fake_fetch(url: str, **kwargs):  # noqa: ANN001
        if url.endswith("/llms.txt"):
            return _FakeResponse(404, "")
        return _FakeResponse(
            200,
            "\n".join(
                [
                    "User-agent: Googlebot",
                    "Allow: /",
                    "User-agent: OAI-SearchBot",
                    "Allow: /",
                    "User-agent: PerplexityBot",
                    "Allow: /",
                    "User-agent: Claude-SearchBot",
                    "Allow: /",
                    "User-agent: GPTBot",
                    "Disallow: /",
                    "User-agent: Google-Extended",
                    "Disallow: /",
                ]
            ),
        )

    monkeypatch.setattr("core.aio_analyzer.safe_fetch_url", fake_fetch)

    html = """
    <html>
      <head>
        <title>テスト記事</title>
        <meta name="robots" content="noindex, nosnippet" />
      </head>
      <body>
        <main>
          <article>
            <h1>テスト記事</h1>
            <section><p>これは分析用の本文です。資格や著者情報は省略しています。</p></section>
          </article>
        </main>
      </body>
    </html>
    """

    result = analyzer.analyze("https://example.com/article", html, response_time_ms=800)
    provider_readiness = result["details"]["provider_readiness"]
    note_labels = {note.get("label") for note in provider_readiness.get("informational_notes", [])}

    assert result["penalty_multiplier"] == 1.0
    assert result["penalties"] == []
    assert provider_readiness["google"]["status"] == "fail"
    assert provider_readiness["openai_search"]["status"] == "fail"
    assert provider_readiness["perplexity"]["status"] == "fail"
    assert provider_readiness["claude_search"]["status"] == "fail"
    assert "overall" not in provider_readiness
    assert {"llms.txt", "GPTBot", "Google-Extended"} <= note_labels


def test_analyze_adds_commerce_and_perplexity_special_notes(monkeypatch) -> None:
    analyzer = AIOContentAnalyzer(enable_wikidata=False)

    def fake_fetch(url: str, **kwargs):  # noqa: ANN001
        if url.endswith("/llms.txt"):
            return _FakeResponse(404, "")
        return _FakeResponse(
            200,
            "\n".join(
                [
                    "User-agent: Googlebot",
                    "Allow: /",
                    "User-agent: OAI-SearchBot",
                    "Allow: /",
                    "User-agent: PerplexityBot",
                    "Allow: /",
                    "User-agent: Claude-SearchBot",
                    "Allow: /",
                ]
            ),
        )

    monkeypatch.setattr("core.aio_analyzer.safe_fetch_url", fake_fetch)

    html = """
    <html>
      <head>
        <title>Trail Running Shoe</title>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Product",
          "name": "Trail Running Shoe",
          "offers": {"@type": "Offer", "price": "7999"}
        }
        </script>
      </head>
      <body>
        <main>
          <h1>Trail Running Shoe</h1>
          <p>価格 7,999円 在庫あり</p>
          <button>カートに追加</button>
          <img src="/shoe.jpg" alt="running shoe" />
        </main>
      </body>
    </html>
    """

    result = analyzer.analyze("https://example.com/products/shoe", html, response_time_ms=800)
    special_notes = result["details"]["provider_readiness"]["special_notes"]

    assert special_notes["openai_commerce"]["applicable"] is True
    assert special_notes["openai_commerce"]["status"] in {"pass", "warn"}
    assert special_notes["perplexity_operational"]["status"] == "informational"
    assert any("WAF" in note or "allowlist" in note for note in special_notes["perplexity_operational"]["notes"])


def test_provider_readiness_fixture_contract() -> None:
    analyzer = AIOContentAnalyzer(enable_wikidata=False)
    fixture_path = Path(__file__).parent / "fixtures" / "provider_readiness_cases.json"
    cases = json.loads(fixture_path.read_text(encoding="utf-8"))

    for case in cases:
        agents = ["googlebot", "oai-searchbot", "perplexitybot", "claude-searchbot"]
        bot_access = analyzer._parse_robots_agent_access(
            case["robots_text"], agents, case["target_url"]
        ) if case["robots_status"] == "pass" else {}
        readiness = analyzer.assess_provider_readiness(
            soup=BeautifulSoup(case["html"], "html.parser"),
            tech_results={"robots_status": case["robots_status"], "bot_access": bot_access},
            structure_results={},
            inline_eeat={"combined_score": 5.0},
            response_headers=case["headers"],
        )
        assert {provider: readiness[provider]["status"] for provider in case["expected"]} == case["expected"], case["name"]


@pytest.mark.parametrize("robots_result", ["timeout", 503])
def test_robots_fetch_failure_never_becomes_provider_pass(monkeypatch, robots_result) -> None:  # noqa: ANN001
    analyzer = AIOContentAnalyzer(enable_wikidata=False)

    def fake_fetch(url: str, **kwargs):  # noqa: ANN001
        if url.endswith("/llms.txt"):
            return _FakeResponse(404, "")
        if robots_result == "timeout":
            raise TimeoutError("fixture timeout")
        return _FakeResponse(robots_result, "")

    monkeypatch.setattr("core.aio_analyzer.safe_fetch_url", fake_fetch)
    tech = analyzer.check_technical_aio("https://example.com/article")
    readiness = analyzer.assess_provider_readiness(
        soup=BeautifulSoup("<html><head></head><body>test</body></html>", "html.parser"),
        tech_results=tech,
        structure_results={},
        inline_eeat={"combined_score": 5.0},
    )

    assert tech["robots_status"] == "unverified"
    assert {readiness[name]["status"] for name in ("google", "openai_search", "perplexity", "claude_search")} == {"unverified"}
