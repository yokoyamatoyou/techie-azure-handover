import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_prompt_contract_methods_live_in_prompt_contract_mixin() -> None:
    expected_name = "article_prompt_contract_mixin.py"
    method_names = [
        "_safe_user_prompt",
        "_build_knowledge_expansion_guide",
        "_safe_contract_value",
        "_sanitize_contract_text",
        "_build_prompt_echo_references",
        "_normalize_must_cover_item",
        "_build_audience_prompt_hint",
        "_count_audience_label_mentions",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_generation_owner_remains_article_generator_after_prompt_contract_split() -> None:
    source_file = inspect.getsourcefile(ArticleGenerator.generate)
    assert source_file is not None
    assert Path(source_file).name == "article_generator.py"
