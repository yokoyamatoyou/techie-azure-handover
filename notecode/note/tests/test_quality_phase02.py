"""Tests for human_resonance2 Phase 02 burstiness."""

from core.app_config import QualityPipelineConfig

from human_resonance2.phase02_burstiness import Phase02Burstiness
from human_resonance2.quality_pipeline import QualityPipelineRunner


def test_phase02_flat_text_improves_after_adjustments() -> None:
    phase = Phase02Burstiness(
        burstiness_target_min=0.18,
        burstiness_target_max=0.52,
        max_sentence_split_ratio=0.5,
    )
    text = (
        "## 本文\n\n"
        "この取り組みは地域の調達網を見直し、在庫計画を毎週更新し、欠品を抑える仕組みです。"
        "この取り組みは地域の調達網を見直し、在庫計画を毎週更新し、欠品を抑える仕組みです。"
        "この取り組みは地域の調達網を見直し、在庫計画を毎週更新し、欠品を抑える仕組みです。"
        "この取り組みは地域の調達網を見直し、在庫計画を毎週更新し、欠品を抑える仕組みです。"
    )

    first = phase.analyze(text)
    rewritten, adjustment_ratio, applied_adjustments = phase.apply_minimal_adjustments(
        text,
        first.rhythm_adjustments,
    )
    second = phase.analyze(rewritten)

    assert first.rhythm_adjustments
    assert applied_adjustments
    assert second.burstiness_score > first.burstiness_score
    assert adjustment_ratio <= phase.max_sentence_split_ratio


def test_phase02_natural_text_avoids_unnecessary_edits() -> None:
    phase = Phase02Burstiness(
        burstiness_target_min=0.18,
        burstiness_target_max=0.52,
        max_sentence_split_ratio=0.5,
    )
    text = (
        "## 背景\n\n"
        "需要を確認します。"
        "物流体制を毎週点検します。"
        "在庫計画を販売データで更新します。"
        "現場と本部で判断基準を共有します。"
    )

    analysis = phase.analyze(text)
    rewritten, adjustment_ratio, applied_adjustments = phase.apply_minimal_adjustments(
        text,
        analysis.rhythm_adjustments,
    )

    assert not analysis.rhythm_adjustments
    assert applied_adjustments == []
    assert rewritten == text
    assert adjustment_ratio == 0.0


def test_phase02_preserves_heading_and_list_blocks() -> None:
    phase = Phase02Burstiness(
        burstiness_target_min=0.18,
        burstiness_target_max=0.52,
        max_sentence_split_ratio=0.5,
    )
    text = (
        "## 手順\n\n"
        "- 在庫を確認する\n"
        "- 期限を確認する\n\n"
        "この取り組みは地域の調達網を見直し、在庫計画を毎週更新し、欠品を抑える仕組みです。"
        "この取り組みは地域の調達網を見直し、在庫計画を毎週更新し、欠品を抑える仕組みです。"
        "この取り組みは地域の調達網を見直し、在庫計画を毎週更新し、欠品を抑える仕組みです。"
        "この取り組みは地域の調達網を見直し、在庫計画を毎週更新し、欠品を抑える仕組みです。"
    )

    analysis = phase.analyze(text)
    rewritten, _, _ = phase.apply_minimal_adjustments(text, analysis.rhythm_adjustments)

    assert "## 手順" in rewritten
    assert "- 在庫を確認する\n- 期限を確認する" in rewritten


def test_quality_pipeline_shadow_mode_phase02_keeps_output_unchanged() -> None:
    config = QualityPipelineConfig(
        enabled=True,
        mode="shadow",
        rollout_percent=100,
        fail_open=True,
        phase01_lexical_enabled=False,
        phase01_tokenizer="auto",
        phase02_burstiness_enabled=True,
        phase03_nominalization_enabled=False,
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
        max_sentence_split_ratio=0.5,
        max_nominalization_rewrite_ratio=0.12,
        fingerprint_enabled=False,
        resonance_tuning_enabled=False,
    )
    runner = QualityPipelineRunner(config=config)
    text = (
        "## 本文\n\n"
        "この取り組みは地域の調達網を見直し、在庫計画を毎週更新し、欠品を抑える仕組みです。"
        "この取り組みは地域の調達網を見直し、在庫計画を毎週更新し、欠品を抑える仕組みです。"
        "この取り組みは地域の調達網を見直し、在庫計画を毎週更新し、欠品を抑える仕組みです。"
        "この取り組みは地域の調達網を見直し、在庫計画を毎週更新し、欠品を抑える仕組みです。"
    )

    result = runner.process(text)

    assert result.text == text
    assert result.phase_reports
    report = result.phase_reports[0]
    assert report["phase"] == "phase02_burstiness"
    assert report["mode"] == "shadow"
    assert report["applied"] is False
    assert report["length_profile"]["sentences"]
