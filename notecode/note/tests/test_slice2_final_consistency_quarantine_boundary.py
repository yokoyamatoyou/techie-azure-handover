from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE_ROOT = (REPO_ROOT / "note").resolve()
LEGACY_CURRENT_ROOT = (NOTE_ROOT / "legacy_current").resolve()


def test_slice2_root_final_consistency_is_same_name_shim() -> None:
    path = NOTE_ROOT / "article_final_consistency_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert (
        "from note.legacy_current.article_final_consistency_mixin import "
        "ArticleFinalConsistencyMixin"
    ) in content
    assert "from note.article_generator import" not in content
    assert "from note.article_helper_facade import" not in content
    assert content.count("note.legacy_current") == 1


def test_slice2_quarantined_final_consistency_does_not_reverse_import_article_generator() -> None:
    path = LEGACY_CURRENT_ROOT / "article_final_consistency_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert "from note import article_generator as" not in content
    assert "from note.article_generator import" not in content


def test_slice2_legacy_compatibility_uses_quarantined_final_consistency_owner() -> None:
    path = LEGACY_CURRENT_ROOT / "article_legacy_compatibility_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert (
        "from note.legacy_current.article_final_consistency_mixin import "
        "ArticleFinalConsistencyMixin"
    ) in content
    assert "from note.article_final_consistency_mixin import ArticleFinalConsistencyMixin" not in content

