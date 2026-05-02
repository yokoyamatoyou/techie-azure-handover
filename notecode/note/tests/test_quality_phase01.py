"""Tests for human_resonance2 Phase 01 lexical diversity."""

from core.app_config import QualityPipelineConfig
import pytest

from human_resonance2.phase01_lexical_diversity import (
    SUDACHI_AVAILABLE,
    Phase01LexicalDiversity,
)
from human_resonance2.quality_pipeline import QualityPipelineRunner


def test_phase01_high_repetition_reports_low_score_and_positions() -> None:
    phase = Phase01LexicalDiversity(lexical_threshold=0.32, max_rewrite_ratio=0.3)
    text = (
        "## 導入\n\n"
        "このサービスは重要です。このサービスは重要です。このサービスは重要です。"
        "価値を説明します。価値を説明します。価値を説明します。"
    )

    first = phase.analyze(text)
    second = phase.analyze(text)

    assert first.lexical_diversity_score == second.lexical_diversity_score
    assert first.lexical_diversity_score < 0.5
    assert first.repetition_signals
    assert all(signal.paragraph_index >= 1 for signal in first.repetition_signals)
    assert all(signal.occurrences >= 2 for signal in first.repetition_signals)
    assert len(first.rewrite_suggestions) <= first.rewrite_cap


def test_phase01_normal_text_avoids_over_alert() -> None:
    phase = Phase01LexicalDiversity(lexical_threshold=0.32, max_rewrite_ratio=0.3)
    text = (
        "## 背景\n\n"
        "食品会社では季節ごとに需要予測を更新します。"
        "物流計画と在庫管理の責任を分けると意思決定が明確になります。"
        "運用データを毎週レビューすると改善点を共有しやすくなります。"
    )

    result = phase.analyze(text)

    assert result.lexical_diversity_score > 0.32
    assert len(result.repetition_signals) <= 2


def test_phase01_rewrite_preserves_headings_and_respects_cap() -> None:
    phase = Phase01LexicalDiversity(lexical_threshold=0.32, max_rewrite_ratio=0.2)
    text = (
        "## 導入\n\n"
        "重要な改善を説明します。重要な改善を説明します。重要な改善を説明します。"
        "改善計画を説明します。改善計画を説明します。改善計画を説明します。\n\n"
        "## まとめ\n\n"
        "改善を継続して価値を高めます。"
    )

    analysis = phase.analyze(text)
    rewritten, rewrite_ratio = phase.apply_minimal_rewrites(text, analysis.rewrite_suggestions)

    assert "## 導入" in rewritten
    assert "## まとめ" in rewritten
    assert rewrite_ratio <= phase.max_rewrite_ratio


def test_quality_pipeline_shadow_mode_keeps_output_unchanged() -> None:
    config = QualityPipelineConfig(
        enabled=True,
        mode="shadow",
        rollout_percent=100,
        fail_open=True,
        phase01_lexical_enabled=True,
        phase01_tokenizer="auto",
        phase02_burstiness_enabled=False,
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
        max_rewrite_ratio=0.2,
        max_sentence_split_ratio=0.12,
        max_nominalization_rewrite_ratio=0.12,
        fingerprint_enabled=False,
        resonance_tuning_enabled=False,
    )
    runner = QualityPipelineRunner(config=config)
    text = (
        "## 本文\n\n"
        "この説明は重要です。この説明は重要です。この説明は重要です。"
        "価値を説明します。価値を説明します。価値を説明します。"
    )

    result = runner.process(text)

    assert result.text == text
    assert result.phase_reports
    report = result.phase_reports[0]
    assert report["phase"] == "phase01_lexical"
    assert report["mode"] == "shadow"
    assert report["applied"] is False
    assert len(report["rewrite_suggestions"]) <= report["rewrite_cap"]


@pytest.mark.skipif(not SUDACHI_AVAILABLE, reason="Sudachi is not installed")
def test_phase01_sudachi_mode_uses_morphological_split() -> None:
    phase = Phase01LexicalDiversity(
        lexical_threshold=0.32,
        max_rewrite_ratio=0.2,
        tokenizer_mode="sudachi",
    )
    tokens = phase._tokenize("食品会社の価値提供を説明します。", method="sudachi")
    assert "食品" in tokens
    assert "会社" in tokens
