import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_zero_base_section_helper_methods_live_in_mixin() -> None:
    expected_name = "zero_base_section_helper_mixin.py"
    method_names = [
        "_zero_base_build_contract_retry_guidance",
        "_zero_base_apply_sanitize_pass",
        "_zero_base_build_section_prompt",
        "_zero_base_extract_section_summary",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_zero_base_orchestration_owners_remain_article_generator() -> None:
    method_names = [
        "_generate_zero_base_scaffold",
        "_zero_base_generate_section",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == "article_generator.py"
