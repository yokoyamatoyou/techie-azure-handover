import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_image_prompt_methods_live_in_mixin() -> None:
    expected_name = "image_prompt_mixin.py"
    method_names = [
        "generate_image_prompt",
        "generate_image_prompts",
        "to_japanese_image_prompt",
        "to_english_image_prompt",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_generation_owner_remains_article_generator_after_image_prompt_split() -> None:
    source_file = inspect.getsourcefile(ArticleGenerator.generate)
    assert source_file is not None
    assert Path(source_file).name == "article_generator.py"
