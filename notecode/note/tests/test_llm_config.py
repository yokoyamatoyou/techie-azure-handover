"""Config parsing tests."""
import json

from core.app_config import (
    get_cognitive_drift_config,
    get_llm_config,
    get_postprocess_config,
    get_quality_pipeline_config,
    get_security_config,
    get_section_generation_config,
    get_semantic_dedupe_config,
    get_source_reading_config,
    get_vnext_overlap_runtime_config,
)


def test_llm_config_model_capability_lists_loaded() -> None:
    config = get_llm_config()
    assert "gpt-5" in config.disable_temperature_model_prefixes
    assert "gpt-5" in config.disable_top_p_model_prefixes
    assert "gpt-5" in config.disable_penalty_model_prefixes
    assert isinstance(config.task_models, dict)
    assert isinstance(config.article_type_params, dict)
    assert -2.0 <= config.presence_penalty <= 2.0
    assert -2.0 <= config.frequency_penalty <= 2.0
    assert config.allow_model_fallback is False
    assert config.max_same_model_retries == 2
    assert "upstream_5xx" in config.retryable_error_classes


def test_security_config_loaded() -> None:
    config = get_security_config()
    assert config.prompt_injection_mode == "block"
    assert "topic" in config.blocked_input_fields


def test_quality_pipeline_config_loaded() -> None:
    config = get_quality_pipeline_config()
    assert config.mode in ("off", "shadow", "enforce")
    assert config.phase01_tokenizer in ("auto", "regex", "sudachi")
    assert 0 <= config.rollout_percent <= 100
    assert 0.0 <= config.lexical_threshold <= 1.0
    assert 0.0 <= config.max_rewrite_ratio <= 1.0
    assert 0.0 <= config.burstiness_target_min <= 1.0
    assert 0.0 <= config.burstiness_target_max <= 1.0
    assert config.burstiness_target_min <= config.burstiness_target_max
    assert 0.0 <= config.nominalization_alert_threshold <= 1.0
    assert 0.0 <= config.style_alignment_min_score <= 1.0
    assert config.domain_guard_strictness in ("relaxed", "normal", "strict")
    assert 0.2 <= config.supplement_min_position_ratio <= 0.9
    assert 0.1 <= config.intro_max_length_ratio <= 0.8
    assert 0.0 <= config.section_coherence_min_score <= 1.0
    assert 0.0 <= config.global_rewrite_ratio_cap <= 1.0
    assert config.conflict_resolution_policy in ("safe_first", "readability_first", "diversity_first")
    assert 0.0 <= config.quality_gate_min_score <= 1.0
    assert isinstance(config.phase07_rollout_enabled, bool)
    assert 0.0 <= config.max_sentence_split_ratio <= 1.0
    assert 0.0 <= config.max_nominalization_rewrite_ratio <= 1.0


def test_generation_mode_loaded() -> None:
    from core.app_config import get_generation_mode
    mode = get_generation_mode()
    assert mode == "zero_base_v2"


def test_candidate_b_config_removed() -> None:
    config = get_llm_config()
    assert "section_candidate_b" not in config.task_models


def test_llm_config_honors_TECHIE_CONFIG_PATH(monkeypatch, tmp_path) -> None:
    temp_config = {
        "llm": {
            "model_name": "gpt-4.1-mini-custom",
            "fallback_model": "gpt-5-nano",
            "reasoning_effort": "low",
            "timeout": 45,
            "task_models": {"section": "gpt-5.4-mini"},
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(temp_config, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("TECHIE_CONFIG_PATH", str(config_path))

    config = get_llm_config()

    assert config.model_name == "gpt-4.1-mini-custom"
    assert config.timeout == 45.0
    assert config.task_models["section"] == "gpt-5.4-mini"


def test_cognitive_drift_config_loaded() -> None:
    config = get_cognitive_drift_config()
    assert isinstance(config["enabled"], bool)
    assert isinstance(config["paragraph_enabled"], bool)
    assert 2 <= config["paragraph_min_blocks"] <= 6
    assert config["paragraph_max_blocks"] >= config["paragraph_min_blocks"]
    assert 0.0 <= config["paragraph_temp_swing"] <= 0.20


def test_section_generation_config_loaded() -> None:
    cfg = get_section_generation_config()
    assert isinstance(cfg.get("parallel_sections"), bool)

    novelty = cfg.get("novelty_gate", {})
    assert isinstance(novelty.get("enabled"), bool)
    assert 1 <= novelty.get("max_retries", 0) <= 3
    assert 0.0 <= novelty.get("intro_novelty_min", 0.0) <= 1.0
    assert 0.0 <= novelty.get("middle_novelty_min", 0.0) <= 1.0
    assert 0.0 <= novelty.get("closing_novelty_min", 0.0) <= 1.0
    assert novelty.get("max_forbidden_terms", 0) >= 1

    overlap = cfg.get("context_overlap", {})
    assert isinstance(overlap.get("enabled"), bool)
    assert 0.0 <= overlap.get("min_ratio", 0.0) <= overlap.get("max_ratio", 1.0) <= 0.9

    hard_soft = cfg.get("hard_soft_thresholds", {})
    assert hard_soft.get("mode") in ("off", "shadow", "enforce")
    assert 0.0 <= hard_soft.get("hard_max_rewrite_ratio", 0.0) <= 1.0
    assert hard_soft.get("soft_max_flat_zone_count", 0) >= 1
    assert 0 <= hard_soft.get("soft_max_semantic_issue_count", -1) <= 24
    assert 1 <= hard_soft.get("soft_max_ai_template_ending_count", 0) <= 40

    lexical = cfg.get("lexical_policy", {})
    assert isinstance(lexical.get("enabled"), bool)
    assert isinstance(lexical.get("extra_banned_phrases"), list)


def test_postprocess_config_loaded() -> None:
    cfg = get_postprocess_config()
    repair = cfg.get("repair_only", {})
    assert isinstance(repair.get("enabled"), bool)
    assert repair.get("mode") in ("off", "shadow", "enforce")
    assert 0.0 <= repair.get("rewrite_ratio_cap", 0.0) <= 1.0
    assert repair.get("llm_trigger_severity") in ("off", "high", "mid")
    assert repair.get("min_chars_for_llm", 0) >= 80
    assert 0.0 <= repair.get("max_violations_per_1k", 0.0) <= 30.0

    concise = cfg.get("concise_compaction", {})
    assert isinstance(concise.get("enabled"), bool)
    assert 0.55 <= concise.get("dedupe_similarity_ratio", 0.0) <= 0.98
    assert 0.35 <= concise.get("dedupe_jaccard_ratio", 0.0) <= 0.95
    assert 0.35 <= concise.get("summary_overlap_ratio", 0.0) <= 0.95
    assert 60 <= concise.get("max_sentence_chars", 0) <= 140
    assert 0 <= concise.get("max_connective_openings_per_paragraph", -1) <= 3
    assert 1 <= concise.get("max_splits_per_sentence", 0) <= 3
    assert 0.0 <= concise.get("target_reduction_ratio", 0.0) <= 0.40
    assert 0.45 <= concise.get("aggressive_keep_ratio", 0.0) <= 0.90
    assert 3 <= concise.get("aggressive_min_sentences_per_paragraph", 0) <= 6
    assert 600 <= concise.get("aggressive_min_chars", 0) <= 12000
    assert 120 <= concise.get("paragraph_clog_min_chars", 0) <= 320
    assert 2 <= concise.get("paragraph_clog_min_sentences", 0) <= 8
    assert 0 <= concise.get("paragraph_clog_min_commas", -1) <= 16
    assert 0.0 <= concise.get("paragraph_clog_min_comma_density", -1.0) <= 0.08
    assert 0.0 <= concise.get("paragraph_clog_threshold_jitter", -1.0) <= 0.35


def test_source_reading_config_loaded() -> None:
    cfg = get_source_reading_config()
    assert 2000 <= cfg.get("max_chars_per_source", 0) <= 20000
    assert 2000 <= cfg.get("quality_context_source_text_max_chars", 0) <= 20000
    assert 2000 <= cfg.get("style_drift_source_text_max_chars", 0) <= 20000


def test_vnext_overlap_runtime_seed_is_promoted_without_changing_mainline_semantic_dedupe() -> None:
    semantic_dedupe = get_semantic_dedupe_config()
    vnext_overlap = get_vnext_overlap_runtime_config()

    assert semantic_dedupe["similarity_threshold"] == 0.84
    assert semantic_dedupe["content_overlap_threshold"] == 0.42
    assert semantic_dedupe["high_overlap_shortcut_threshold"] == 0.62

    assert vnext_overlap["similarity_threshold"] == 0.62
    assert vnext_overlap["content_overlap_threshold"] == 0.77
    assert vnext_overlap["high_overlap_shortcut_threshold"] == 0.83
