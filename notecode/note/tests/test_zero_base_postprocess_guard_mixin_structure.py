import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_zero_base_postprocess_guard_methods_live_in_mixin() -> None:
    expected_name = "zero_base_postprocess_guard_mixin.py"
    method_names = [
        "_zero_base_get_linebreak_profile",
        "_zero_base_apply_linebreak_profile",
        "_zero_base_semantic_dedupe",
        "_zero_base_minimal_postprocess",
        "_relax_note_quality_gate",
        "_compute_rewrite_ratio",
        "_zero_base_normalize_layout_minimal",
        "_zero_base_light_grammar_fix",
        "_zero_base_collect_protected_items",
        "_zero_base_restore_protected_items",
        "_zero_base_align_corporate_voice",
        "_zero_base_apply_minimal_legal_guard",
        "_count_zero_base_risk_markers",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_zero_base_orchestration_and_postprocess_shell_owners_remain_article_generator() -> None:
    method_names = [
        "generate",
        "_generate_zero_base_scaffold",
        "_zero_base_generate_section",
        "_apply_compacted_postprocess_pipeline",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == "article_generator.py"
