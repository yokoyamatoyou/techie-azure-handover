"""Tests for human_resonance2 Phase 07 rollout controller."""

from core.app_config import QualityPipelineConfig

from human_resonance2.phase07_rollout import Phase07IntegrationRollout
from human_resonance2.quality_pipeline import QualityPipelineRunner


def test_phase07_rollout_percent_zero_downgrades_enforce() -> None:
    phase = Phase07IntegrationRollout()
    decision = phase.select_effective_mode(
        requested_mode="enforce",
        rollout_percent=0,
        text="## 本文\n\nテスト",
        context={"topic_hint": "テスト", "source_urls": ["https://example.com"]},
    )

    assert decision.requested_mode == "enforce"
    assert decision.effective_mode == "shadow"
    assert decision.selected_for_enforce is False


def test_phase07_rollout_decision_is_deterministic_for_same_input() -> None:
    phase = Phase07IntegrationRollout()
    kwargs = {
        "requested_mode": "enforce",
        "rollout_percent": 37,
        "text": "## 本文\n\n同じ入力",
        "context": {"topic_hint": "同じ", "source_urls": ["https://example.com/a"]},
    }
    first = phase.select_effective_mode(**kwargs)
    second = phase.select_effective_mode(**kwargs)

    assert first.request_bucket == second.request_bucket
    assert first.effective_mode == second.effective_mode
    assert first.selected_for_enforce == second.selected_for_enforce


def test_quality_pipeline_phase07_zero_rollout_keeps_output_unchanged() -> None:
    config = QualityPipelineConfig(
        enabled=True,
        mode="enforce",
        rollout_percent=0,
        fail_open=True,
        phase01_lexical_enabled=False,
        phase01_tokenizer="auto",
        phase02_burstiness_enabled=False,
        phase03_nominalization_enabled=False,
        phase04_style_drift_enabled=False,
        phase05_layout_guard_enabled=True,
        phase06_orchestrator_enabled=True,
        phase07_rollout_enabled=True,
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

    result = runner.process(text, context={"topic_hint": "配置改善"})

    assert result.text == text
    phase07_report = next(r for r in result.phase_reports if r.get("phase") == "phase07_rollout")
    assert phase07_report["mode"] == "shadow"
    assert phase07_report["requested_mode"] == "enforce"
    assert phase07_report["decision"]["selected_for_enforce"] is False


def test_quality_pipeline_phase07_full_rollout_applies_enforce_path() -> None:
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
        phase06_orchestrator_enabled=True,
        phase07_rollout_enabled=True,
        lexical_threshold=0.32,
        burstiness_target_min=0.18,
        burstiness_target_max=0.52,
        nominalization_alert_threshold=0.18,
        style_alignment_min_score=0.72,
        domain_guard_strictness="normal",
        supplement_min_position_ratio=0.6,
        intro_max_length_ratio=0.35,
        section_coherence_min_score=0.4,
        global_rewrite_ratio_cap=1.0,
        conflict_resolution_policy="safe_first",
        quality_gate_min_score=0.0,
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

    result = runner.process(text, context={"topic_hint": "配置改善"})

    assert result.text != text
    phase07_report = next(r for r in result.phase_reports if r.get("phase") == "phase07_rollout")
    assert phase07_report["mode"] == "enforce"
    assert phase07_report["decision"]["selected_for_enforce"] is True
    assert phase07_report["telemetry"]["phase_report_count"] >= 2


def test_quality_pipeline_phase07_disabled_ignores_rollout_percent() -> None:
    config = QualityPipelineConfig(
        enabled=True,
        mode="enforce",
        rollout_percent=0,
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

    result = runner.process(text, context={"topic_hint": "配置改善"})

    assert result.text != text
    assert all(report.get("mode") == "enforce" for report in result.phase_reports)
    assert not any(report.get("phase") == "phase07_rollout" for report in result.phase_reports)
