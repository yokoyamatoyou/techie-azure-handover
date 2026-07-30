import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_similarity_feedback_methods_live_in_mixin() -> None:
    expected_name = "article_similarity_feedback_mixin.py"
    method_names = [
        "_strip_headings_and_urls",
        "_normalize_similarity_text",
        "_to_char_ngram_set",
        "_similarity_overlap_scores",
        "_is_redundant_expansion",
        "_build_section_overlap_memory",
        "_get_redundancy_thresholds",
        "_extract_content_terms",
        "_build_lexical_priming_feedback",
        "_build_fingerprint_feedback",
        "_lookup_fingerprint_prompt_hint",
        "_build_section_generation_feedback",
        "_render_section_feedback_block",
        "_is_redundant_section",
        "_check_redundancy_with_reason",
        "_dedupe_terms",
        "_compute_section_novelty_report",
        "_get_novelty_threshold",
        "_should_retry_due_to_low_novelty",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_generation_retry_and_postprocess_owners_remain_article_generator() -> None:
    method_names = [
        "generate",
        "_generate_zero_base_scaffold",
        "_apply_compacted_postprocess_pipeline",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == "article_generator.py"
