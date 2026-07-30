from __future__ import annotations

import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE_ROOT = (REPO_ROOT / "note").resolve()
LEGACY_CURRENT_ROOT = (NOTE_ROOT / "legacy_current").resolve()


def test_slice7_root_zero_base_postprocess_guard_is_same_name_shim() -> None:
    path = NOTE_ROOT / "zero_base_postprocess_guard_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert (
        "from note.legacy_current.zero_base_postprocess_guard_mixin import "
        "ZeroBasePostprocessGuardMixin"
    ) in content
    assert "from note.article_generator import" not in content
    assert "from note.article_helper_facade import" not in content
    assert content.count("note.legacy_current") == 1


def test_slice7_article_generator_zero_base_postprocess_guard_methods_resolve_to_quarantine() -> None:
    expected = (LEGACY_CURRENT_ROOT / "zero_base_postprocess_guard_mixin.py").resolve()
    method_names = [
        "_zero_base_get_linebreak_profile",
        "_zero_base_apply_linebreak_profile",
        "_zero_base_semantic_dedupe",
        "_zero_base_minimal_postprocess",
        "_relax_note_quality_gate",
        "_zero_base_apply_minimal_legal_guard",
        "_count_zero_base_risk_markers",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).resolve() == expected


def test_slice7_quarantined_zero_base_postprocess_guard_does_not_reverse_import_article_generator() -> None:
    path = LEGACY_CURRENT_ROOT / "zero_base_postprocess_guard_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert "from note import article_generator as" not in content
    assert "from note.article_generator import" not in content
    assert "from note.zero_base.semantic_dedupe import semantic_dedupe_text" in content
