"""Tests for human_resonance2 Phase 04 style drift guard."""

import pytest

from core.app_config import QualityPipelineConfig

from human_resonance2.phase04_style_drift import Phase04StyleDrift, SUDACHI_AVAILABLE
from human_resonance2.quality_pipeline import QualityPipelineRunner


def test_phase04_source_profile_flags_out_of_domain_terms() -> None:
    phase = Phase04StyleDrift(
        style_alignment_min_score=0.72,
        domain_guard_strictness="normal",
    )
    text = (
        "## 本文\n\n"
        "この取り組みは医療従事者と患者への価値提供を強化し、診療現場の改善を進めます。"
    )
    context = {
        "topic_hint": "食品会社の物流改善",
        "source_urls": ["https://www.sanrei-foods.co.jp/company/"],
        "writing_intent": "解説記事として説明する",
        "writing_focus": "explanation",
        "source_text": "食品物流の品質管理と在庫改善を進める。食品店舗の運用改善を行う。",
    }

    first = phase.analyze(text, context=context)
    rewritten, correction_ratio, applied = phase.apply_minimal_corrections(text, first.style_corrections)
    second = phase.analyze(rewritten, context=context)

    assert first.inferred_domain == "food"
    assert any(alert.alert_type == "domain" for alert in first.drift_alerts)
    assert applied
    assert "医療従事者" not in rewritten
    assert "患者" not in rewritten
    assert second.style_alignment_score > first.style_alignment_score
    assert correction_ratio > 0.0


def test_phase04_not_limited_to_food_medical_pair() -> None:
    phase = Phase04StyleDrift(
        style_alignment_min_score=0.72,
        domain_guard_strictness="normal",
    )
    text = (
        "## 本文\n\n"
        "この施策では病院向けの診療計画を主軸に進めます。"
    )
    context = {
        "topic_hint": "技術ブログのAPI設計",
        "source_urls": ["https://example-tech.jp/engineering/api-design"],
        "writing_intent": "技術解説",
        "writing_focus": "analysis",
        "source_text": "API設計とクラウド運用、データ処理基盤の実装方針を説明する。",
    }

    result = phase.analyze(text, context=context)

    assert result.inferred_domain == "technical"
    assert any(alert.alert_type == "domain" for alert in result.drift_alerts)
    assert any("outside source profile" in alert.reason for alert in result.drift_alerts)


def test_phase04_medical_source_keeps_medical_terms() -> None:
    phase = Phase04StyleDrift(
        style_alignment_min_score=0.72,
        domain_guard_strictness="normal",
    )
    text = (
        "## 本文\n\n"
        "医療従事者と患者への情報提供を改善し、診療現場での判断を支援します。"
    )
    context = {
        "topic_hint": "病院向け情報提供の改善",
        "source_urls": ["https://example-medical-hospital.jp/"],
        "writing_intent": "医療業界向けの解説",
        "writing_focus": "explanation",
        "source_text": "医療現場で患者対応を支える診療支援の改善について解説する。",
    }

    result = phase.analyze(text, context=context)
    rewritten, _, applied = phase.apply_minimal_corrections(text, result.style_corrections)

    assert result.inferred_domain == "medical"
    assert not any(alert.alert_type == "domain" for alert in result.drift_alerts)
    assert rewritten == text
    assert applied == []


def test_phase04_explanation_intent_neutralizes_hype_tone() -> None:
    phase = Phase04StyleDrift(
        style_alignment_min_score=0.72,
        domain_guard_strictness="normal",
    )
    text = "## 本文\n\nぶっちゃけこの施策は最強です。"
    context = {
        "topic_hint": "業務改善のポイント",
        "writing_intent": "解説記事",
        "writing_focus": "explanation",
        "source_text": "運用改善の実施手順と比較観点を説明する。",
    }

    result = phase.analyze(text, context=context)
    rewritten, _, applied = phase.apply_minimal_corrections(text, result.style_corrections)

    assert result.inferred_purpose == "explain"
    assert any(alert.alert_type == "tone" for alert in result.drift_alerts)
    assert applied
    assert "ぶっちゃけ" not in rewritten
    assert "最強" not in rewritten


@pytest.mark.skipif(not SUDACHI_AVAILABLE, reason="Sudachi unavailable")
def test_phase04_lemma_matching_reduces_false_domain_alerts() -> None:
    phase = Phase04StyleDrift(
        style_alignment_min_score=0.72,
        domain_guard_strictness="normal",
    )
    text = "## 本文\n\n患者への説明を標準化し、運用手順を整理します。"
    context = {
        "topic_hint": "食品物流の改善",
        "source_urls": ["https://www.sanrei-foods.co.jp/company/"],
        "writing_intent": "食品物流の解説記事",
        "writing_focus": "explanation",
        "source_text": (
            "食品物流の品質管理と在庫改善を進める。"
            "患者対応の手順を見直した事例を紹介する。"
            "患者対応の記録方法もあわせて整理する。"
        ),
    }

    result = phase.analyze(text, context=context)
    domain_alert_terms = {alert.drift_term for alert in result.drift_alerts if alert.alert_type == "domain"}
    assert "患者" not in domain_alert_terms


def test_quality_pipeline_shadow_mode_phase04_keeps_output_unchanged() -> None:
    config = QualityPipelineConfig(
        enabled=True,
        mode="shadow",
        rollout_percent=100,
        fail_open=True,
        phase01_lexical_enabled=False,
        phase01_tokenizer="auto",
        phase02_burstiness_enabled=False,
        phase03_nominalization_enabled=False,
        phase04_style_drift_enabled=True,
        phase05_layout_guard_enabled=False,
        phase06_orchestrator_enabled=False,
        phase07_rollout_enabled=False,
        lexical_threshold=0.32,
        burstiness_target_min=0.18,
        burstiness_target_max=0.52,
        nominalization_alert_threshold=0.18,
        style_alignment_min_score=0.72,
        domain_guard_strictness="normal",
        supplement_min_position_ratio=0.45,
        intro_max_length_ratio=0.35,
        section_coherence_min_score=0.4,
        global_rewrite_ratio_cap=0.2,
        conflict_resolution_policy="safe_first",
        quality_gate_min_score=0.55,
        max_rewrite_ratio=0.15,
        max_sentence_split_ratio=0.12,
        max_nominalization_rewrite_ratio=0.12,
        fingerprint_enabled=False,
        resonance_tuning_enabled=False,
    )
    runner = QualityPipelineRunner(config=config)
    text = "## 本文\n\nこの取り組みは医療従事者と患者への価値提供を強化します。"
    context = {
        "topic_hint": "食品会社の物流改善",
        "source_urls": ["https://www.sanrei-foods.co.jp/company/"],
        "writing_intent": "解説記事",
        "writing_focus": "explanation",
        "source_text": "食品物流の品質管理と在庫改善を進める。",
    }

    result = runner.process(text, context=context)

    assert result.text == text
    assert result.phase_reports
    report = result.phase_reports[0]
    assert report["phase"] == "phase04_style_drift"
    assert report["mode"] == "shadow"
    assert report["applied"] is False
    assert report["drift_alerts"]
