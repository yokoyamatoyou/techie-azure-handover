from __future__ import annotations

import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE_ROOT = (REPO_ROOT / "note").resolve()
LEGACY_CURRENT_ROOT = (NOTE_ROOT / "legacy_current").resolve()


def test_slice8_root_length_planning_is_same_name_shim() -> None:
    path = NOTE_ROOT / "article_length_planning_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert (
        "from note.legacy_current.article_length_planning_mixin import "
        "ArticleLengthPlanningMixin"
    ) in content
    assert "from note.article_generator import" not in content
    assert "from note.article_helper_facade import" not in content
    assert content.count("note.legacy_current") == 1


def test_slice8_article_generator_length_planning_methods_resolve_to_quarantine() -> None:
    expected = (LEGACY_CURRENT_ROOT / "article_length_planning_mixin.py").resolve()
    method_names = [
        "_normalize_length_mode",
        "_count_length_signal_items",
        "_resolve_adaptive_length_mode",
        "_get_length_profile",
        "_get_note_length_range",
        "_get_outline_section_range",
        "_estimate_note_target_chars",
        "_estimate_note_lead_chars",
        "_allocate_section_targets",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).resolve() == expected


def test_slice8_quarantined_length_planning_has_no_reverse_import_or_runtime_symbol_dependency() -> None:
    path = LEGACY_CURRENT_ROOT / "article_length_planning_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert "from note import article_generator as" not in content
    assert "from note.article_generator import" not in content
    assert "note.legacy_current.article_runtime_symbols" not in content
