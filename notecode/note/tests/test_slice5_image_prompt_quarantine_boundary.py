from __future__ import annotations

from pathlib import Path

from note.legacy_current import article_runtime_symbols as runtime_symbols


REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE_ROOT = (REPO_ROOT / "note").resolve()
LEGACY_CURRENT_ROOT = (NOTE_ROOT / "legacy_current").resolve()


def test_slice5_root_image_prompt_is_same_name_shim() -> None:
    path = NOTE_ROOT / "image_prompt_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert (
        "from note.legacy_current.image_prompt_mixin import "
        "ImagePromptMixin"
    ) in content
    assert "from note.article_generator import" not in content
    assert "from note.article_helper_facade import" not in content
    assert content.count("note.legacy_current") == 1


def test_slice5_quarantined_image_prompt_does_not_reverse_import_article_generator() -> None:
    path = LEGACY_CURRENT_ROOT / "image_prompt_mixin.py"
    content = path.read_text(encoding="utf-8")

    assert "from note import article_generator as" not in content
    assert "from note.article_generator import" not in content
    assert "from note.legacy_current import article_runtime_symbols as _runtime_symbols" in content


def test_slice5_runtime_symbols_expose_image_prompt_contract() -> None:
    expected_names = [
        "IMAGE_STYLE_DIRECTIONS",
        "IMAGE_ROLE_GUIDES",
    ]

    for name in expected_names:
        assert hasattr(runtime_symbols, name), name
