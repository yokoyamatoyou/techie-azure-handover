import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_style_persona_methods_live_in_style_persona_mixin() -> None:
    expected_name = "article_style_persona_mixin.py"
    method_names = [
        "set_allow_experience",
        "set_tone_profile_preference",
        "_resolve_editor_persona_profile",
        "_build_editor_persona_block",
        "_apply_tone_profile_preference",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_generation_owner_remains_article_generator_after_style_persona_split() -> None:
    source_file = inspect.getsourcefile(ArticleGenerator.generate)
    assert source_file is not None
    assert Path(source_file).name == "article_generator.py"
