import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_length_planning_methods_live_in_length_planning_mixin() -> None:
    expected_name = "article_length_planning_mixin.py"
    method_names = [
        "_normalize_length_mode",
        "_count_length_signal_items",
        "_resolve_adaptive_length_mode",
        "_get_length_profile",
        "_get_note_length_range",
        "_get_outline_section_range",
        "_estimate_note_target_chars",
        "_estimate_note_lead_chars",
        "_allocate_section_targets",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_generation_and_length_enforcement_owners_remain_article_generator() -> None:
    method_names = [
        "generate",
        "_zero_base_build_length_plan",
        "_trim_body_to_limit",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == "article_generator.py"
