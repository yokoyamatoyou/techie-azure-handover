import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_final_consistency_methods_live_in_mixin() -> None:
    expected_name = "article_final_consistency_mixin.py"
    method_names = [
        "_dedupe_lead_body",
        "_is_reference_or_list_paragraph",
        "_get_active_style_profile",
        "_cap_colloquial_endings",
        "_break_ending_monotony",
        "_rewrite_ending_for_variety",
        "_analyze_style_register",
        "_should_enforce_polite_register",
        "_normalize_register_to_polite",
        "_has_corporate_stance_anchor_gap",
        "_extract_primary_org_name",
        "_inject_corporate_stance_anchor",
        "_normalize_pronoun_usage",
        "_dedupe_cross_section_sentences",
        "_dedupe_body_repetition",
        "_diversify_overused_phrases",
        "_clean_redundant_connectives",
        "_soften_assertive_expressions",
        "_strip_heading_top_adversative",
        "_get_concise_compaction_config",
        "_is_summary_marker_sentence",
        "_apply_concise_rewrites",
        "_aggressive_sentence_pruning",
        "_compress_redundant_explanations",
        "_trim_nonclosing_section_tail_summaries",
        "_normalize_opening_token",
        "_is_logical_required_opening",
        "_is_suppressible_template_opening",
        "_strip_opening_safely",
        "_trim_redundant_template_opening",
        "_reduce_ai_like_openings",
        "_reduce_ai_like_endings",
        "_reduce_target_term_overuse",
        "_normalize_ai_like_heading_labels",
        "_repair_subjectless_openings",
        "_extract_theme_entities",
        "_apply_prodrop_zero_anaphora",
        "_reduce_repeated_named_entity_openings",
        "_compress_repeated_subject_openings",
        "_dedupe_similar_headings",
        "_apply_unified_dedupe_pass",
        "_apply_final_consistency_guards",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_generation_and_compacted_postprocess_owners_remain_article_generator() -> None:
    method_names = [
        "generate",
        "_generate_zero_base_scaffold",
        "_apply_compacted_postprocess_pipeline",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == "article_generator.py"
