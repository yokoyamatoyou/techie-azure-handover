import inspect
from pathlib import Path

from note.article_generator import ArticleGenerator


def test_zero_base_contract_guard_methods_live_in_mixin() -> None:
    expected_name = "zero_base_contract_guard_mixin.py"
    method_names = [
        "_zero_base_dedupe_list",
        "_build_zero_base_forbidden_topics",
        "_zero_base_allowed_pronouns",
        "_analyze_zero_base_speaker_contract",
        "_extract_alignment_anchor_terms",
        "_extract_source_alignment_terms",
        "_compute_section_focus_coverage",
        "_zero_base_compute_contract_alignment",
        "_collect_forbidden_topic_hits",
        "_is_recruiting_context",
        "_build_branding_forbidden_topics",
        "_zero_base_detect_ending_monotony",
        "_zero_base_protect_datetime_literals",
        "_zero_base_restore_datetime_literals",
        "_zero_base_integrate_missing_must_cover",
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == expected_name


def test_zero_base_orchestration_shell_owners_remain_article_generator() -> None:
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
    ]

    for method_name in method_names:
        source_file = inspect.getsourcefile(getattr(ArticleGenerator, method_name))
        assert source_file is not None
        assert Path(source_file).name == "article_generator.py"
