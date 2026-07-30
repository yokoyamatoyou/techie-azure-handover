import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_article_quality_guard_methods_live_in_mixin() -> None:
    expected_name = "article_quality_guard_mixin.py"
    method_names = [
        "_estimate_rewrite_ratio",
        "_sentence_length_stddev",
        "_looks_style_flattened",
        "_heading_count",
        "_rewrite_guard_check",
        "_detect_grammar_breaks",
        "_looks_non_terminal_sentence_ending",
        "_repair_sentence_flow_in_line",
        "_repair_contextual_sentence_breaks",
        "_semantic_token_set",
        "_compute_semantic_layout_metrics",
        "_check_contextual_naturalness",
        "_build_repair_only_prompt",
        "_should_use_repair_only_llm",
        "_run_repair_only_pass",
        "_evaluate_hard_soft_thresholds",
        "_soft_warning_eval_score",
        "_try_soft_warning_fix_pass",
        "_run_final_quality_eval_pass",
        "_build_quality_context",
        "_collect_review_points",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_quality_shell_owners_remain_article_generator() -> None:
    method_names = [
        "generate",
        "_generate_zero_base_scaffold",
        "_apply_compacted_postprocess_pipeline",
        "_apply_resonance",
        "_apply_quality_pipeline",
        "_build_pipeline_check",
        "_build_quality_pipeline_check",
        "_build_llm_check",
        "_merge_contexts",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == "article_generator.py"
