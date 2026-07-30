"""Phase 1 tests for ArticleFetcher."""
import uuid

import requests

from note.article_fetcher import ArticleFetcher


def test_load_file():
    fetcher = ArticleFetcher()
    uploads_dir = fetcher._uploads_dir
    uploads_dir.mkdir(parents=True, exist_ok=True)

    p = uploads_dir / f"test_input_{uuid.uuid4().hex}.txt"
    p.write_text("テスト内容です", encoding="utf-8")

    try:
        result = fetcher.load_file(str(p))
    finally:
        if p.exists():
            p.unlink()

    assert "テスト" in result.content
    assert result.source_type == "file"


def test_parse_html_keeps_upfade_content():
    fetcher = ArticleFetcher()
    html = """
    <html><body>
      <article>
        <h3 class="upfade">企画をカタチに</h3>
        <p class="upfade">お客様に寄り添ったサービスを提供します。</p>
      </article>
    </body></html>
    """

    parsed = fetcher._parse_html(html, url="https://example.com/service", content_type="text/html")

    assert "企画をカタチに" in parsed.content
    assert "お客様に寄り添ったサービス" in parsed.content


def test_parse_html_removes_ad_banner_content():
    fetcher = ArticleFetcher()
    html = """
    <html><body>
      <article>
        <p class="ad-banner">広告</p>
        <p>本文だけ残る</p>
      </article>
    </body></html>
    """

    parsed = fetcher._parse_html(html, url="https://example.com/article", content_type="text/html")

    assert "広告" not in parsed.content
    assert "本文だけ残る" in parsed.content


def test_parse_html_prefers_information_dense_main_candidate():
    fetcher = ArticleFetcher()
    rich_text = (
        "データ連携の運用手順を整理し、現場担当者が迷わず実行できるようにする。"
        "入力から検証、エラー時の復旧までを段階的に設計すると、運用品質が安定しやすい。"
        "さらに、毎週の見直しポイントを明示すると改善サイクルが回りやすくなる。"
        "この流れを事前に共有しておくと、引き継ぎ時の品質低下を防ぎやすい。"
    )
    html = f"""
    <html><body>
      <article><p>短い要約です。</p></article>
      <main>
        <h2>本文</h2>
        <p>{rich_text}</p>
      </main>
    </body></html>
    """

    parsed = fetcher._parse_html(html, url="https://example.com/guide", content_type="text/html")

    assert "運用手順を整理" in parsed.content
    assert len(parsed.content) > 130


def test_parse_html_fallback_recovers_when_noise_marker_over_prunes_candidates():
    fetcher = ArticleFetcher()
    body_text = (
        "現場の問い合わせ対応を安定させるには、受付条件と回答フローを最初に定義することが有効です。"
        "あわせて、対応履歴をカテゴリ化して再利用可能な知見として蓄積すると、担当者ごとの差を抑えられます。"
    )
    html = f"""
    <html><body>
      <main class="ad-content">
        <p>{body_text}</p>
      </main>
    </body></html>
    """

    parsed = fetcher._parse_html(html, url="https://example.com/help", content_type="text/html")

    assert "問い合わせ対応を安定" in parsed.content
    assert any("代替抽出" in notice for notice in parsed.notices)


class _FakeResponse:
    def __init__(self, body: bytes, *, status_code: int = 200, content_type: str = "text/html; charset=utf-8"):
        self._body = body
        self.status_code = status_code
        self.headers = {
            "content-type": content_type,
            "content-length": str(len(body)),
        }
        self.encoding = "utf-8"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def iter_content(self, chunk_size: int = 65536):
        for i in range(0, len(self._body), chunk_size):
            yield self._body[i : i + chunk_size]

    @property
    def content(self) -> bytes:
        return self._body


def test_validate_url_and_fetch_url_use_equivalent_html_extraction(monkeypatch):
    fetcher = ArticleFetcher()
    url = "https://example.com/article"
    html = """
    <html><body>
      <article>
        <h2>業務改善の基本</h2>
        <p>入力ルールを統一し、確認工程を明確化すると、ミスの再発を抑えやすくなります。</p>
      </article>
    </body></html>
    """.encode("utf-8")

    monkeypatch.setattr(fetcher, "_is_safe_url", lambda _: True)
    monkeypatch.setattr(fetcher, "_robots_allows", lambda _: (True, ""))
    monkeypatch.setattr("note.article_fetcher.safe_fetch_url", lambda *args, **kwargs: _FakeResponse(html))

    captured_contents = []
    original_parse = fetcher._parse_html

    def _spy_parse(html_text, url=None, content_type=""):  # type: ignore[no-untyped-def]
        result = original_parse(html_text, url=url, content_type=content_type)
        captured_contents.append(result.content)
        return result

    monkeypatch.setattr(fetcher, "_parse_html", _spy_parse)

    fetched = fetcher.fetch_url(url)
    ok, message = fetcher.validate_url(url)

    assert ok is True
    assert message == ""
    assert len(captured_contents) == 2
    assert captured_contents[0] == captured_contents[1] == fetched.content


def test_parse_html_prefers_low_noise_article_over_noisy_main_candidate():
    fetcher = ArticleFetcher()
    meaningful_text = (
        "運用手順を段階化し、確認基準を明示すると、引き継ぎ時の判断差を抑えやすくなります。"
        "加えて、記録項目を固定すると、改善サイクルを安定して回しやすくなります。"
        "この設計により、担当者が変わっても品質を維持しやすくなります。"
    )
    noisy_main = "\n".join(["広告 バナー おすすめ 関連記事 シェア" for _ in range(18)])
    html = f"""
    <html><body>
      <main>
        <p>{noisy_main}</p>
      </main>
      <article>
        <h2>本文</h2>
        <p>{meaningful_text}</p>
      </article>
    </body></html>
    """

    parsed = fetcher._parse_html(html, url="https://example.com/noise", content_type="text/html")

    assert "運用手順を段階化" in parsed.content
    assert "品質を維持しやすくなります" in parsed.content
