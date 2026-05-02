"""Tests for human_resonance2 Phase 06 orchestrator."""

from core.app_config import QualityPipelineConfig

from human_resonance2.phase06_orchestrator import Phase06Orchestrator
from human_resonance2.quality_pipeline import QualityPipelineRunner


def test_phase06_resolves_conflict_by_policy_priority() -> None:
    phase = Phase06Orchestrator(
        global_rewrite_ratio_cap=0.3,
        conflict_resolution_policy="safe_first",
        quality_gate_min_score=0.3,
    )
    original = "## 本文\n\n同じ文です。"
    current = "## 本文\n\n違う文です。"
    reports = [
        {
            "phase": "phase03_nominalization",
            "nominalization_score": 0.2,
            "nominalization_alerts": [{"paragraph_index": 1, "sentence_index": 1}],
            "rewrite_candidates": [{"paragraph_index": 1, "sentence_index": 1, "reason": "rewrite"}],
        },
        {
            "phase": "phase04_style_drift",
            "style_alignment_score": 0.6,
            "drift_alerts": [{"paragraph_index": 1, "sentence_index": 1}],
            "style_corrections": [{"paragraph_index": 1, "sentence_index": 1, "reason": "style"}],
        },
    ]

    result = phase.evaluate(
        original_text=original,
        current_text=current,
        phase_reports=reports,
        errors=[],
    )

    assert result.quality_bundle.conflicts
    assert result.final_adjustment_plan
    assert result.final_adjustment_plan[0].phase == "phase04_style_drift"
    assert result.gate_decision in ("pass", "hold", "fallback")


def test_quality_pipeline_shadow_mode_phase06_keeps_output_unchanged() -> None:
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
        phase06_orchestrator_enabled=True,
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
        global_rewrite_ratio_cap=0.1,
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
    assert len(result.phase_reports) >= 2
    phase06_report = next(r for r in result.phase_reports if r.get("phase") == "phase06_orchestrator")
    assert phase06_report["mode"] == "shadow"
    assert phase06_report["applied"] is False
    assert phase06_report["gate_decision"] in ("pass", "hold", "fallback")


def test_quality_pipeline_enforce_mode_phase06_fallbacks_when_cap_exceeded() -> None:
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
        global_rewrite_ratio_cap=0.0,
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

    result = runner.process(text)

    assert result.text == text
    phase06_report = next(r for r in result.phase_reports if r.get("phase") == "phase06_orchestrator")
    assert phase06_report["gate_decision"] == "fallback"
    assert phase06_report["gate_reason"] == "global_rewrite_ratio_cap_exceeded"
    assert "phase06_orchestrator" in result.applied
