import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_legacy_compatibility_methods_live_in_mixin() -> None:
    expected_name = "article_legacy_compatibility_mixin.py"
    method_names = [
        "_generate_single_section_task",
        "_build_even_summary_memory",
        "_generate_sections_parallel",
        "_generate_section_with_retry",
        "_distribute_quotes",
        "_prepare_section_opening_sequence",
        "_editor_consistency_signals",
        "_should_run_editor_consistency",
        "_run_editor_consistency_pass",
        "_run_post_generation_polish_pass",
        "_should_run_readability_polish",
        "_run_readability_polish_pass",
        "_extract_quote_candidates",
        "_legacy_generate_linkedin_addendum",
        "_legacy_adjust_note_length",
        "_legacy_estimate_linkedin_target_chars",
        "_legacy_detect_linkedin_purpose",
        "_legacy_dedupe_lead_body",
        "_legacy_is_reference_or_list_paragraph",
        "_legacy_get_active_style_profile",
        "_legacy_cap_colloquial_endings",
        "_legacy_break_ending_monotony",
        "_legacy_rewrite_ending_for_variety",
        "_legacy_analyze_style_register",
        "_legacy_should_enforce_polite_register",
        "_legacy_normalize_register_to_polite",
        "_legacy_has_corporate_stance_anchor_gap",
        "_legacy_extract_primary_org_name",
        "_legacy_inject_corporate_stance_anchor",
        "_legacy_normalize_pronoun_usage",
        "_legacy_dedupe_cross_section_sentences",
        "_legacy_dedupe_body_repetition",
        "_legacy_diversify_overused_phrases",
        "_legacy_clean_redundant_connectives",
        "_legacy_soften_assertive_expressions",
        "_legacy_strip_heading_top_adversative",
        "_legacy_get_concise_compaction_config",
        "_legacy_is_summary_marker_sentence",
        "_legacy_apply_concise_rewrites",
        "_legacy_aggressive_sentence_pruning",
        "_legacy_compress_redundant_explanations",
        "_legacy_trim_nonclosing_section_tail_summaries",
        "_legacy_normalize_opening_token",
        "_legacy_is_logical_required_opening",
        "_legacy_is_suppressible_template_opening",
        "_legacy_strip_opening_safely",
        "_legacy_trim_redundant_template_opening",
        "_legacy_reduce_ai_like_openings",
        "_legacy_reduce_ai_like_endings",
        "_legacy_reduce_target_term_overuse",
        "_legacy_normalize_ai_like_heading_labels",
        "_legacy_repair_subjectless_openings",
        "_legacy_extract_theme_entities",
        "_legacy_apply_prodrop_zero_anaphora",
        "_legacy_reduce_repeated_named_entity_openings",
        "_legacy_compress_repeated_subject_openings",
        "_legacy_dedupe_similar_headings",
        "_legacy_apply_unified_dedupe_pass",
        "_legacy_apply_final_consistency_guards",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_active_orchestration_owners_remain_article_generator() -> None:
    method_names = [
        "generate",
        "_generate_zero_base_scaffold",
        "_zero_base_generate_section",
        "_apply_compacted_postprocess_pipeline",
        "_apply_resonance",
        "_apply_quality_pipeline",
        "_build_pipeline_check",
        "_build_quality_pipeline_check",
        "_build_llm_check",
        "_merge_contexts",
        "quick_legal_check",
        "evaluate_resonance_score",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == "article_generator.py"
