import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_zero_base_contract_methods_live_in_contract_mixin() -> None:
    expected_name = "zero_base_contract_mixin.py"
    method_names = [
        "_resolve_zero_base_contract_profile",
        "_zero_base_extract_prompt_answer",
        "_zero_base_contract_base",
        "_zero_base_resolve_pre_generation_questions",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_zero_base_scaffold_owner_remains_article_generator() -> None:
    source_file = inspect.getsourcefile(ArticleGenerator._generate_zero_base_scaffold)
    assert source_file is not None
    assert Path(source_file).name == "article_generator.py"
