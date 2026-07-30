import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_output_assembly_methods_live_in_output_mixin() -> None:
    expected_name = "article_output_mixin.py"
    method_names = [
        "_generate_title",
        "_generate_lead",
        "_generate_hashtags",
        "_format_references",
        "_make_cta",
        "_format_for_linkedin",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_generation_owner_remains_article_generator() -> None:
    source_file = inspect.getsourcefile(ArticleGenerator.generate)
    assert source_file is not None
    assert Path(source_file).name == "article_generator.py"
