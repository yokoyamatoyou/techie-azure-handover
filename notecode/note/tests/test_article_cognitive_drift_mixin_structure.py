import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_cognitive_drift_methods_live_in_cognitive_drift_mixin() -> None:
    expected_name = "article_cognitive_drift_mixin.py"
    method_names = [
        "_resolve_cognitive_phase",
        "_estimate_paragraph_slot_count",
        "_resolve_information_density",
        "_build_paragraph_drift_plan",
        "_resolve_fatigue_profile",
        "_render_paragraph_drift_block",
        "_get_cognitive_profile",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_generate_owner_remains_article_generator() -> None:
    method_names = [
        "generate",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == "article_generator.py"
