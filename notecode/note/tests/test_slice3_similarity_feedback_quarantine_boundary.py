from __future__ import annotations

from pathlib import Path

from note.legacy_current import article_runtime_symbols as runtime_symbols


REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE_ROOT = (REPO_ROOT / "note").resolve()
LEGACY_CURRENT_ROOT = (NOTE_ROOT / "legacy_current").resolve()


def test_slice3_root_similarity_feedback_is_same_name_shim() -> None:
    path = NOTE_ROOT / "article_similarity_feedback_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert (
        "from note.legacy_current.article_similarity_feedback_mixin import "
        "ArticleSimilarityFeedbackMixin"
    ) in content
    assert "from note.article_generator import" not in content
    assert "from note.article_helper_facade import" not in content
    assert content.count("note.legacy_current") == 1


def test_slice3_quarantined_similarity_feedback_does_not_reverse_import_article_generator() -> None:
    path = LEGACY_CURRENT_ROOT / "article_similarity_feedback_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert "from note import article_generator as" not in content
    assert "from note.article_generator import" not in content
    assert "from note.legacy_current import article_runtime_symbols as _runtime_symbols" in content


def test_slice3_runtime_symbols_expose_similarity_feedback_contract() -> None:
    expected_names = [
        "SIMILARITY_NGRAM_SIZE",
        "SIMILARITY_NGRAM_MAX_LEN",
        "REDUNDANT_SECTION_JACCARD_THRESHOLD",
        "REDUNDANT_SECTION_CONTAINMENT_THRESHOLD",
        "REDUNDANT_EXPANSION_JACCARD_THRESHOLD",
        "REDUNDANT_EXPANSION_CONTAINMENT_THRESHOLD",
        "LEXICAL_PRIMING_STOPWORDS",
        "FINGERPRINT_PROMPT_HINTS",
        "FINGERPRINT_HINT_KEY_ALIASES",
        "_RE_HEADING_LINE",
        "_RE_URL",
        "_RE_WHITESPACE_COLLAPSE",
        "_RE_PUNCTUATION_STRIP",
        "_RE_CJK_LATIN_TOKEN",
        "_RE_SENTENCE_SPLIT",
    ]

    for name in expected_names:
        assert hasattr(runtime_symbols, name), name
