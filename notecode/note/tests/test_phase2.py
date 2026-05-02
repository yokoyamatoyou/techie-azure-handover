"""Phase 2 tests for ArticleGenerator (API required)."""
import os
import pytest

from note.article_fetcher import FetchedContent
from note.article_generator import ArticleGenerator


def _should_run_e2e() -> bool:
    return bool(os.getenv("OPENAI_API_KEY")) and os.getenv("RUN_E2E", "0") == "1"


@pytest.mark.skipif(not _should_run_e2e(), reason="Set OPENAI_API_KEY and RUN_E2E=1")
def test_generate_smoke():
    generator = ArticleGenerator()
    contexts = [FetchedContent(title="テスト資料", content="AIは社会に影響を与える。倫理的な配慮が必要。")]
    result = generator.generate(contexts, "初心者向けに", "ai")

    assert result["title"]
    assert result["lead"]
    assert result["body"]
    assert result["hashtags"]
