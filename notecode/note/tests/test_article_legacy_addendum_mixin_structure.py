import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_legacy_addendum_methods_live_in_mixin() -> None:
    expected_name = "article_legacy_addendum_mixin.py"
    method_names = [
        "_generate_expansion_section",
        "_summarize_body_for_expansion",
        "_generate_linkedin_addendum",
        "_adjust_note_length",
        "_estimate_linkedin_target_chars",
        "_detect_linkedin_purpose",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_generation_and_zero_base_owners_remain_article_generator() -> None:
    method_names = [
        "generate",
        "_generate_zero_base_scaffold",
        "_apply_compacted_postprocess_pipeline",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == "article_generator.py"
