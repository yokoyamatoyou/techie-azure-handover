from __future__ import annotations

from pathlib import Path

from note.legacy_current import article_runtime_symbols as runtime_symbols


REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE_ROOT = (REPO_ROOT / "note").resolve()
LEGACY_CURRENT_ROOT = (NOTE_ROOT / "legacy_current").resolve()


def test_slice4_root_quality_guard_is_same_name_shim() -> None:
    path = NOTE_ROOT / "article_quality_guard_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert (
        "from note.legacy_current.article_quality_guard_mixin import "
        "ArticleQualityGuardMixin"
    ) in content
    assert "from note.article_generator import" not in content
    assert "from note.article_helper_facade import" not in content
    assert content.count("note.legacy_current") == 1


def test_slice4_quarantined_quality_guard_does_not_reverse_import_article_generator() -> None:
    path = LEGACY_CURRENT_ROOT / "article_quality_guard_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert "from note import article_generator as" not in content
    assert "from note.article_generator import" not in content
    assert "from note.legacy_current import article_runtime_symbols as _runtime_symbols" in content


def test_slice4_runtime_symbols_expose_quality_guard_contract() -> None:
    expected_names = [
        "ARTICLE_TYPE_LABELS",
        "ARTICLE_TYPE_PROMPTS",
        "_RE_SENTENCE_SPLIT",
        "_RE_HEADING_COUNT",
        "_RE_NON_TERMINAL_SENTENCE_END",
    ]

    for name in expected_names:
        assert hasattr(runtime_symbols, name), name
