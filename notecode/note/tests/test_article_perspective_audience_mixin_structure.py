import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_perspective_audience_methods_live_in_perspective_audience_mixin() -> None:
    expected_name = "article_perspective_audience_mixin.py"
    method_names = [
        "_get_persona_for_perspective",
        "_secondary_from_interview",
        "_normalize_perspective_key",
        "_detect_secondary_from_context",
        "_blend_persona",
        "_extract_pronoun",
        "_detect_target_audience",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_generation_and_zero_base_scaffold_owners_remain_article_generator() -> None:
    method_names = [
        "generate",
        "_generate_zero_base_scaffold",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == "article_generator.py"
