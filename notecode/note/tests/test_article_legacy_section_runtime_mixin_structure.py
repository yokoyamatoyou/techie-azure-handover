import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_legacy_section_runtime_methods_live_in_mixin() -> None:
    expected_name = "article_legacy_section_runtime_mixin.py"
    method_names = [
        "_resolve_context_overlap_ratio",
        "_slice_context_for_section",
        "_summarize_prior_section_memory",
        "_build_section_brief",
        "_trim_prompt_anchor_for_question",
        "_build_reader_question_guideline",
        "_build_style_invariants",
        "_distribute_elements_to_paragraphs",
        "_generate_paragraph",
        "_generate_section",
        "_generate_section_paragraph_mode",
        "_should_verify_section_content",
        "_verify_section_content",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_shared_helpers_remain_article_generator() -> None:
    method_names = [
        "generate",
        "_merge_contexts",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == "article_generator.py"
