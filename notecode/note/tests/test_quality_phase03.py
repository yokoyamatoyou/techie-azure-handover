"""Tests for human_resonance2 Phase 03 nominalization."""

import pytest

from core.app_config import QualityPipelineConfig

from human_resonance2.phase03_nominalization import Phase03Nominalization, SUDACHI_AVAILABLE
from human_resonance2.quality_pipeline import QualityPipelineRunner


def test_phase03_abstract_text_generates_alerts_and_rewrite_candidates() -> None:
    phase = Phase03Nominalization(
        nominalization_alert_threshold=0.18,
        max_nominalization_rewrite_ratio=0.6,
    )
    text = (
        "## 本文\n\n"
        "在庫最適化の推進と販売計画の調整の実施における検討を進めることが可能です。"
        "物流体制の改善の実施と判断基準の共有の推進を行うことができます。"
    )

    first = phase.analyze(text)
    rewritten, rewrite_ratio, applied = phase.apply_minimal_rewrites(text, first.rewrite_candidates)
    second = phase.analyze(rewritten)

    assert first.nominalization_alerts
    assert first.rewrite_candidates
    assert applied
    assert rewrite_ratio <= phase.max_nominalization_rewrite_ratio
    assert second.nominalization_score < first.nominalization_score


def test_phase03_technical_terms_have_low_false_positive_rate() -> None:
    phase = Phase03Nominalization(
        nominalization_alert_threshold=0.18,
        max_nominalization_rewrite_ratio=0.3,
    )
    text = (
        "## 技術メモ\n\n"
        "システムの信頼性と可用性を高める設計方針を共有します。"
        "品質管理と個人情報保護の要件を確認し、監査手順を定義します。"
        "互換性と再現性を満たすテストを継続して実行します。"
    )

    result = phase.analyze(text)

    assert result.nominalization_score < 0.18
    assert len(result.nominalization_alerts) <= 1


def test_phase03_preserves_disclaimer_section() -> None:
    phase = Phase03Nominalization(
        nominalization_alert_threshold=0.18,
        max_nominalization_rewrite_ratio=0.7,
    )
    text = (
        "## 本文\n\n"
        "在庫最適化の推進と販売計画の調整の実施における検討を進めることが可能です。\n\n"
        "## 免責事項\n\n"
        "本記事は一般情報を提供するものであり、法的助言ではありません。"
    )

    analysis = phase.analyze(text)
    rewritten, _, _ = phase.apply_minimal_rewrites(text, analysis.rewrite_candidates)

    assert "## 免責事項" in rewritten
    assert "本記事は一般情報を提供するものであり、法的助言ではありません。" in rewritten


@pytest.mark.skipif(not SUDACHI_AVAILABLE, reason="Sudachi unavailable")
def test_phase03_sudachi_sahen_nominal_detection_is_active() -> None:
    phase = Phase03Nominalization(
        nominalization_alert_threshold=0.15,
        max_nominalization_rewrite_ratio=0.4,
    )
    text = (
        "## 本文\n\n"
        "在庫管理の実施と販売計画の調整の推進を進めます。"
        "運用改善の検討と情報共有の実施を継続します。"
    )
    result = phase.analyze(text)
    assert result.nominalization_score > 0.15
    assert result.nominalization_alerts


def test_quality_pipeline_shadow_mode_phase03_keeps_output_unchanged() -> None:
    config = QualityPipelineConfig(
        enabled=True,
        mode="shadow",
        rollout_percent=100,
        fail_open=True,
        phase01_lexical_enabled=False,
        phase01_tokenizer="auto",
        phase02_burstiness_enabled=False,
        phase03_nominalization_enabled=True,
        phase04_style_drift_enabled=False,
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
        max_nominalization_rewrite_ratio=0.5,
        fingerprint_enabled=False,
        resonance_tuning_enabled=False,
    )
    runner = QualityPipelineRunner(config=config)
    text = (
        "## 本文\n\n"
        "在庫最適化の推進と販売計画の調整の実施における検討を進めることが可能です。"
        "物流体制の改善の実施と判断基準の共有の推進を行うことができます。"
    )

    result = runner.process(text)

    assert result.text == text
    assert result.phase_reports
    report = result.phase_reports[0]
    assert report["phase"] == "phase03_nominalization"
    assert report["mode"] == "shadow"
    assert report["applied"] is False
    assert report["nominalization_alerts"]
