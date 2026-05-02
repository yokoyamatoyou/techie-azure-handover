"""Policy engine unit tests."""
from note.policy_engine import (
    build_pipeline_policy,
    detect_ambiguous_terms,
    estimate_category_meta,
    evaluate_title_quality,
    resolve_category_policy,
)


def test_detect_ambiguous_terms_requires_confirmation_for_fishing_term() -> None:
    result = detect_ambiguous_terms("釣りタイトルは避けたいです。釣りの意味を確認したい。")
    assert result.requires_confirmation is True
    assert any(c.term == "釣り" for c in result.candidates)


def test_detect_ambiguous_terms_skips_when_context_is_clear() -> None:
    result = detect_ambiguous_terms("週末に海で魚釣りをします。")
    assert result.requires_confirmation is False
    assert result.candidates == []


def test_estimate_category_meta_for_paper_topic() -> None:
    meta = estimate_category_meta(
        label="論文解説",
        prompt="査読論文の手法と実験結果を要約する",
        writing_focus="analysis",
    )
    assert meta["base_template"] == "ai"
    assert meta["evidence_mode"] == "strict"
    assert meta["empathy_level"] == "low"


def test_estimate_category_meta_for_corporate_branding_prefers_explanation() -> None:
    meta = estimate_category_meta(
        label="企業ブランディング",
        prompt="企業理念とブランドアイデンティティを紹介する",
        writing_focus="auto",
    )
    assert meta["base_template"] == "branding"
    assert meta["focus_default"] == "explanation"
    assert meta["evidence_mode"] == "strict"


def test_resolve_category_policy_prefers_custom_meta() -> None:
    policy = resolve_category_policy(
        "my_custom",
        custom_prompt="会社紹介",
        custom_meta={
            "base_template": "branding",
            "focus_default": "experience",
            "empathy_level": "high",
            "humanity_level": "high",
            "evidence_mode": "normal",
        },
    )
    assert policy.source == "custom_meta"
    assert policy.base_template == "branding"
    assert policy.focus_default == "experience"


def test_build_pipeline_policy_analysis_sets_strict_evidence() -> None:
    category = resolve_category_policy("ai")
    policy = build_pipeline_policy(
        article_type="ai",
        perspective="journalist",
        psychology_structure="decision_support",
        writing_focus="analysis",
        length_mode="short",
        user_prompt="研究手法の比較",
        category_policy=category,
    )
    assert policy.evidence_mode == "strict"
    assert policy.style_profile == "formal"
    assert policy.empathy_level == "low"
    assert policy.humanity_level == "low"


def test_build_pipeline_policy_corporate_experience_uses_balanced_style_guard() -> None:
    category = resolve_category_policy(
        "custom_branding",
        custom_meta={
            "base_template": "branding",
            "focus_default": "experience",
            "empathy_level": "high",
            "humanity_level": "high",
            "evidence_mode": "normal",
        },
    )
    policy = build_pipeline_policy(
        article_type="custom_branding",
        perspective="corporate",
        psychology_structure="auto",
        writing_focus="experience",
        length_mode="normal",
        user_prompt="企業紹介記事",
        category_policy=category,
    )
    assert policy.style_profile == "balanced"
    assert "style:corporate_guard" in policy.rationale


def test_evaluate_title_quality_flags_clickbait() -> None:
    issues = evaluate_title_quality("絶対にバズる最強の方法", focus="analysis", evidence_mode="strict")
    assert "clickbait_or_exaggeration" in issues
    assert "strict_mode_disallows_overclaim" in issues
