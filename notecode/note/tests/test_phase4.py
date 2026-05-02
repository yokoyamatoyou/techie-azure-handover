"""Phase 4 minimal end-to-end test (API required)."""
import os
import pytest

from note.article_fetcher import FetchedContent
from note.article_generator import ArticleGenerator, ARTICLE_TYPE_LABELS, BANNED_PHRASES


def _should_run_e2e() -> bool:
    return bool(os.getenv("OPENAI_API_KEY")) and os.getenv("RUN_E2E", "0") == "1"


@pytest.mark.skipif(not _should_run_e2e(), reason="Set OPENAI_API_KEY and RUN_E2E=1")
def test_e2e_all_types():
    generator = ArticleGenerator()
    contexts = [FetchedContent(title="サンプル", content="科学的な検証には再現性が重要。")]

    for article_type in ARTICLE_TYPE_LABELS.keys():
        result = generator.generate(contexts, "初心者向け", article_type)

        assert result["title"]
        assert result["lead"]
        assert result["body"]
        assert len(result["hashtags"]) >= 3
        assert "##" in result["body"]

        for phrase in BANNED_PHRASES:
            assert phrase not in result["body"]
