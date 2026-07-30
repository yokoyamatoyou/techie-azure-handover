from __future__ import annotations

import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE_ROOT = (REPO_ROOT / "note").resolve()
LEGACY_CURRENT_ROOT = (NOTE_ROOT / "legacy_current").resolve()


def test_slice9_root_style_persona_is_same_name_shim() -> None:
    path = NOTE_ROOT / "article_style_persona_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert (
        "from note.legacy_current.article_style_persona_mixin import "
        "ArticleStylePersonaMixin"
    ) in content
    assert "from note.article_generator import" not in content
    assert "from note.article_helper_facade import" not in content
    assert content.count("note.legacy_current") == 1


def test_slice9_article_generator_style_persona_methods_resolve_to_quarantine() -> None:
    expected = (LEGACY_CURRENT_ROOT / "article_style_persona_mixin.py").resolve()
    method_names = [
        "_resolve_editor_persona_profile",
        "_snapshot_editor_personas",
        "_get_editor_persona_profile",
        "_build_editor_persona_block",
        "set_allow_experience",
        "_normalize_tone_profile",
        "set_tone_profile_preference",
        "_resolve_effective_tone_profile",
        "_resolve_style_profile_from_tone",
        "_apply_tone_profile_preference",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).resolve() == expected


def test_slice9_quarantined_style_persona_has_no_reverse_import_or_runtime_symbol_dependency() -> None:
    path = LEGACY_CURRENT_ROOT / "article_style_persona_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert "from note import article_generator as" not in content
    assert "from note.article_generator import" not in content
    assert "note.legacy_current.article_runtime_symbols" not in content
