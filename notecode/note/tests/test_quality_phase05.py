"""Tests for human_resonance2 Phase 05 layout guard."""

from core.app_config import QualityPipelineConfig

from human_resonance2.phase05_layout_guard import Phase05LayoutGuard
from human_resonance2.quality_pipeline import QualityPipelineRunner


def test_phase05_detects_early_supplement_and_builds_reorder_plan() -> None:
    phase = Phase05LayoutGuard(
        supplement_min_position_ratio=0.6,
        intro_max_length_ratio=0.4,
        section_coherence_min_score=0.35,
    )
    text = (
        "## 導入\n\n"
        "本記事の前提を短く整理します。\n\n"
        "## 補足情報\n\n"
        "ここではFAQを先に説明します。\n\n"
        "## 現状整理\n\n"
        "現場で起きている課題を確認します。\n\n"
        "## 改善施策\n\n"
        "実施手順と判断基準を示します。\n\n"
        "## まとめ\n\n"
        "次に取る行動を示します。"
    )

    first = phase.analyze(text)
    rewritten, applied_steps = phase.apply_minimal_reordering(text, first.reorder_plan)
    second = phase.analyze(rewritten)

    assert first.supplement_position_alerts
    assert first.reorder_plan
    assert applied_steps
    assert "## 補足情報" in rewritten
    assert second.layout_validation_report.early_supplement_count < first.layout_validation_report.early_supplement_count


def test_phase05_well_structured_text_has_no_forced_reorder() -> None:
    phase = Phase05LayoutGuard(
        supplement_min_position_ratio=0.5,
        intro_max_length_ratio=0.45,
        section_coherence_min_score=0.30,
    )
    text = (
        "## 導入\n\n"
        "記事の目的を共有します。\n\n"
        "## 現状\n\n"
        "課題を確認します。\n\n"
        "## 施策\n\n"
        "対応方針を説明します。\n\n"
        "## 補足\n\n"
        "追加の注意点を示します。\n\n"
        "## まとめ\n\n"
        "次の一歩を提示します。"
    )

    result = phase.analyze(text)

    assert result.supplement_position_alerts == []
    assert result.reorder_plan == []
    assert result.layout_validation_report.overall_pass is True


def test_quality_pipeline_shadow_mode_phase05_keeps_output_unchanged() -> None:
    config = QualityPipelineConfig(
        enabled=True,
        mode="shadow",
        rollout_percent=100,
        fail_open=True,
        phase01_lexical_enabled=False,
        phase01_tokenizer="auto",
        phase02_burstiness_enabled=False,
        phase03_nominalization_enabled=False,
        phase04_style_drift_enabled=False,
        phase05_layout_guard_enabled=True,
        phase06_orchestrator_enabled=False,
        phase07_rollout_enabled=False,
        lexical_threshold=0.32,
        burstiness_target_min=0.18,
        burstiness_target_max=0.52,
        nominalization_alert_threshold=0.18,
        style_alignment_min_score=0.72,
        domain_guard_strictness="normal",
        supplement_min_position_ratio=0.6,
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
    text = (
        "## 導入\n\n"
        "記事の狙いを共有します。\n\n"
        "## 補足\n\n"
        "補足説明を先に書いています。\n\n"
        "## 本論\n\n"
        "本論の説明です。\n\n"
        "## まとめ\n\n"
        "結論です。"
    )

    result = runner.process(text)

    assert result.text == text
    assert result.phase_reports
    report = result.phase_reports[0]
    assert report["phase"] == "phase05_layout_guard"
    assert report["mode"] == "shadow"
    assert report["applied"] is False
    assert report["supplement_position_alerts"]


def test_quality_pipeline_enforce_mode_phase05_reorders_sections() -> None:
    config = QualityPipelineConfig(
        enabled=True,
        mode="enforce",
        rollout_percent=100,
        fail_open=True,
        phase01_lexical_enabled=False,
        phase01_tokenizer="auto",
        phase02_burstiness_enabled=False,
        phase03_nominalization_enabled=False,
        phase04_style_drift_enabled=False,
        phase05_layout_guard_enabled=True,
        phase06_orchestrator_enabled=False,
        phase07_rollout_enabled=False,
        lexical_threshold=0.32,
        burstiness_target_min=0.18,
        burstiness_target_max=0.52,
        nominalization_alert_threshold=0.18,
        style_alignment_min_score=0.72,
        domain_guard_strictness="normal",
        supplement_min_position_ratio=0.6,
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
    text = (
        "## 導入\n\n"
        "記事の狙いを共有します。\n\n"
        "## 補足\n\n"
        "補足説明を先に書いています。\n\n"
        "## 本論\n\n"
        "本論の説明です。\n\n"
        "## まとめ\n\n"
        "結論です。"
    )

    result = runner.process(text)

    assert result.text != text
    assert "phase05_layout_guard" in result.applied
    assert result.phase_reports
    report = result.phase_reports[0]
    assert report["phase"] == "phase05_layout_guard"
    assert report["mode"] == "enforce"
    assert report["applied"] is True
    assert report["applied_reorder_steps"]
