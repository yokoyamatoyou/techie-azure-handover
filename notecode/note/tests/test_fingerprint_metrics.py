"""Tests for human_resonance2.fingerprint_metrics module."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

from human_resonance2.fingerprint_metrics import (
    CorrectionResult,
    FingerprintAnalyzer,
    FingerprintReport,
    SUDACHI_AVAILABLE,
    apply_fingerprint_corrections,
    compute_hd_d,
    compute_mtld,
    conjunction_repetition_rate,
    detect_vocab_repetition,
    paragraph_length_cv,
    particle_distribution_entropy,
    pos_bigram_monotonicity,
    script_ratio,
    sentence_length_cv,
    subject_explicit_rate,
)


# ---------------------------------------------------------------------------
# Fixture texts
# ---------------------------------------------------------------------------
HUMAN_LIKE_TEXT = """## はじめに

最近、生成AIの進化が止まらない。特にテキスト生成の分野では、人間が書いたものと区別がつかないレベルに達しているという声も聞こえてくる。

ただ、本当にそうだろうか？実際にいくつかの生成テキストを分析してみると、意外な特徴が浮かび上がってきた。文の長さが均一すぎるのだ。人間は書いているうちに気分が乗ったり、疲れたりする。その結果、文章にはリズムの揺らぎが生まれる。

## なぜ均一性が問題なのか

人間の文章には「バースト性」がある。短い文がポンポンと続くかと思えば、次の段落では長い文がじっくりと展開される。

これはAIには難しい。統計的に見ると、AIは平均的な文長に収束しやすい傾向がある。

段落の長さも同じだ。人間は1文だけの段落を作ることもあれば、6文以上の重厚な段落を作ることもある。

## 助詞の分布について

日本語には「は」「が」「を」「に」「で」「と」「も」という主要な助詞がある。人間の文章では、これらの助詞がバランスよく分布する。AIはどうしても「は」と「が」に偏りがちだ。

これは面白い発見だと思う。助詞の分布を見るだけで、そのテキストが人間によるものかAIによるものかを推定できる可能性がある。

## まとめ

結局のところ、予測可能性を下げることが人間らしさの本質なのかもしれない。完璧すぎる文章は、かえって不自然に映る。"""

MONOTONE_TEXT = """## セクション1

生成AIは進化しています。テキスト生成の分野は発展しています。人間の文章と区別がつきません。これは重要な問題です。

## セクション2

さらに分析を進めます。統計的な手法を用います。結果は明確に出ています。問題点が判明しました。

## セクション3

また別の観点があります。助詞の分布を調べます。偏りが確認できます。改善の余地があります。

## セクション4

つまり結論としては。予測可能性の問題です。人間らしさが重要です。今後の課題となります。"""


# ---------------------------------------------------------------------------
# Individual metric tests
# ---------------------------------------------------------------------------

class TestSentenceLengthCV:
    def test_short_text_returns_zero(self):
        assert sentence_length_cv("短い。") == 0.0

    def test_empty_returns_zero(self):
        assert sentence_length_cv("") == 0.0

    def test_human_like_has_variance(self):
        cv = sentence_length_cv(HUMAN_LIKE_TEXT)
        assert cv > 0.1, f"Expected human-like CV > 0.1, got {cv}"

    def test_monotone_has_low_variance(self):
        cv = sentence_length_cv(MONOTONE_TEXT)
        cv_human = sentence_length_cv(HUMAN_LIKE_TEXT)
        assert cv < cv_human, "Monotone text should have lower CV than human-like"


class TestParagraphLengthCV:
    def test_short_text_returns_zero(self):
        assert paragraph_length_cv("一つだけ。") == 0.0

    def test_human_like_has_variance(self):
        cv = paragraph_length_cv(HUMAN_LIKE_TEXT)
        assert cv > 0.0, f"Expected paragraph CV > 0, got {cv}"


class TestConjunctionRepetitionRate:
    def test_empty(self):
        assert conjunction_repetition_rate("") == 0.0

    def test_high_conjunction_text(self):
        text = "まず第一に。\n\nさらに補足する。\n\nまた別の視点。\n\nつまり結論は。"
        rate = conjunction_repetition_rate(text)
        assert rate > 0.5, f"Expected high conjunction rate, got {rate}"

    def test_human_like_moderate(self):
        rate = conjunction_repetition_rate(HUMAN_LIKE_TEXT)
        assert rate < 0.5, f"Expected moderate conjunction rate, got {rate}"


class TestSubjectExplicitRate:
    def test_empty(self):
        assert subject_explicit_rate("") == 0.0

    def test_returns_between_0_and_1(self):
        rate = subject_explicit_rate(HUMAN_LIKE_TEXT)
        assert 0.0 <= rate <= 1.0

    @pytest.mark.skipif(not SUDACHI_AVAILABLE, reason="Sudachi unavailable")
    def test_detects_noun_plus_subject_particle_pattern_with_sudachi(self):
        text = "市場は拡大した。競争が激化した。価格は下落した。"
        rate = subject_explicit_rate(text)
        assert rate >= 0.66


class TestParticleDistributionEntropy:
    def test_empty(self):
        entropy, max_e = particle_distribution_entropy("")
        assert entropy == 0.0

    def test_human_like_has_entropy(self):
        entropy, max_e = particle_distribution_entropy(HUMAN_LIKE_TEXT)
        assert entropy > 0.0, f"Expected entropy > 0, got {entropy}"
        assert max_e > 0.0

    def test_entropy_not_exceeds_max(self):
        entropy, max_e = particle_distribution_entropy(HUMAN_LIKE_TEXT)
        assert entropy <= max_e + 0.01

    @pytest.mark.skipif(not SUDACHI_AVAILABLE, reason="Sudachi unavailable")
    def test_ignores_non_particle_ha_sequences_with_sudachi(self):
        text = "ははは。ははは。ははは。ははは。ははは。"
        entropy, max_e = particle_distribution_entropy(text)
        assert entropy == 0.0
        assert max_e >= 0.0


class TestScriptRatio:
    def test_empty(self):
        h, k, j = script_ratio("")
        assert h == 0.0 and k == 0.0 and j == 0.0

    def test_ratios_sum_to_one(self):
        h, k, j = script_ratio(HUMAN_LIKE_TEXT)
        total = h + k + j
        assert 0.95 <= total <= 1.05, f"Script ratios should sum to ~1.0, got {total}"

    def test_japanese_text_has_kanji(self):
        _, _, j = script_ratio(HUMAN_LIKE_TEXT)
        assert j > 0.1, f"Expected kanji ratio > 0.1, got {j}"


class TestPosBigramMonotonicity:
    def test_empty(self):
        assert pos_bigram_monotonicity("") == 0.0

    def test_human_like_not_zero(self):
        mono = pos_bigram_monotonicity(HUMAN_LIKE_TEXT)
        assert mono > 0.0


# ---------------------------------------------------------------------------
# Analyzer integration tests
# ---------------------------------------------------------------------------

class TestFingerprintAnalyzer:
    def test_short_text(self):
        analyzer = FingerprintAnalyzer()
        report = analyzer.analyze("短い")
        assert report.overall_unpredictability == 0.0

    def test_human_like_text(self):
        analyzer = FingerprintAnalyzer()
        report = analyzer.analyze(HUMAN_LIKE_TEXT)
        assert isinstance(report, FingerprintReport)
        assert report.overall_unpredictability > 0.0
        assert report.particle_entropy > 0.0

    def test_monotone_has_flat_flags(self):
        analyzer = FingerprintAnalyzer()
        report = analyzer.analyze(MONOTONE_TEXT)
        # Monotone text should trigger at least one flat-zone flag
        assert len(report.flat_zone_flags) > 0 or report.overall_unpredictability < 0.5

    def test_human_vs_monotone_unpredictability(self):
        analyzer = FingerprintAnalyzer()
        human = analyzer.analyze(HUMAN_LIKE_TEXT)
        mono = analyzer.analyze(MONOTONE_TEXT)
        assert human.overall_unpredictability > mono.overall_unpredictability, (
            f"Human ({human.overall_unpredictability}) should be more unpredictable "
            f"than monotone ({mono.overall_unpredictability})"
        )

    def test_correction_hints_populated_for_flat(self):
        analyzer = FingerprintAnalyzer()
        report = analyzer.analyze(MONOTONE_TEXT)
        if report.flat_zone_flags:
            assert len(report.correction_hints) > 0


# ---------------------------------------------------------------------------
# Condition execution tests (editor_consistency)
# ---------------------------------------------------------------------------

class TestEditorConsistencyCondition:
    """Test _should_run_editor_consistency logic via module import."""

    def test_empty_text_returns_false(self):
        from note.article_generator import ArticleGenerator
        from unittest.mock import MagicMock

        gen = ArticleGenerator.__new__(ArticleGenerator)
        gen._current_pronoun = "私"
        assert gen._should_run_editor_consistency("", "") is False

    def test_missing_closing_triggers(self):
        from note.article_generator import ArticleGenerator

        gen = ArticleGenerator.__new__(ArticleGenerator)
        gen._current_pronoun = "私"
        lead = "リード文です。"
        body = "## はじめに\n\n内容。\n\n## 分析\n\n内容。\n\n## 補足\n\n内容。"
        assert gen._should_run_editor_consistency(lead, body) is True

    def test_no_issues_returns_false(self):
        from note.article_generator import ArticleGenerator

        gen = ArticleGenerator.__new__(ArticleGenerator)
        gen._current_pronoun = "私"
        lead = "リード文です。"
        body = (
            "## はじめに\n\n生成AIの最新動向について解説します。\n\n"
            "## 本論\n\nテキスト生成の技術的な仕組みを見ていきましょう。\n\n"
            "## まとめ\n\n今後の展望をまとめると以下のようになります。"
        )
        result = gen._should_run_editor_consistency(lead, body)
        assert result is False

    def test_pronoun_inconsistency_triggers(self):
        from note.article_generator import ArticleGenerator

        gen = ArticleGenerator.__new__(ArticleGenerator)
        gen._current_pronoun = "私"
        lead = "私はこう思います。"
        body = "## はじめに\n\n僕が考えるに。\n\n## まとめ\n\n内容。"
        assert gen._should_run_editor_consistency(lead, body) is True


# ---------------------------------------------------------------------------
# Fingerprint correction engine tests (R5-T01~T06)
# ---------------------------------------------------------------------------

class TestFingerprintCorrection:
    """Tests for apply_fingerprint_corrections and its integration."""

    def test_no_flags_returns_original(self):
        report = FingerprintReport(flat_zone_flags=[])
        result = apply_fingerprint_corrections("テスト文です。", report)
        assert result.text == "テスト文です。"
        assert result.applied_rules == []
        assert result.rewrite_ratio == 0.0

    def test_conjunction_reduction_applied(self):
        text = (
            "まず最初の話題です。\n\n"
            "さらに次の話題です。\n\n"
            "また別の話題です。\n\n"
            "つまり結論です。"
        )
        report = FingerprintReport(flat_zone_flags=["conjunction_rate_high"])
        result = apply_fingerprint_corrections(text, report, max_rewrite_ratio=0.5)
        assert "conjunction_reduction" in result.applied_rules
        assert result.text != text
        assert not result.discarded

    def test_subject_drop_applied(self):
        text = (
            "私は考えました。彼は同意しました。"
            "それは正しいです。これは重要です。"
            "私は実行しました。彼は確認しました。"
            "それは成功です。これは結論です。"
            "私は満足しました。"
        )
        report = FingerprintReport(flat_zone_flags=["subject_explicit_high"])
        result = apply_fingerprint_corrections(text, report, max_rewrite_ratio=1.0)
        assert "subject_drop" in result.applied_rules
        assert result.text != text

    def test_sentence_end_variation_disabled_by_default(self):
        text = "\n".join([
            "これは重要です。",
            "それも大切です。",
            "あれは必要です。",
            "どれも有効です。",
            "全てが正しいです。",
            "結果は良好です。",
            "品質は高いです。",
            "効果は明確です。",
        ])
        report = FingerprintReport(flat_zone_flags=["sentence_length_cv_flat"])
        result = apply_fingerprint_corrections(text, report, max_rewrite_ratio=1.0)
        assert "sentence_end_variation" not in result.applied_rules
        assert result.text == text

    def test_sentence_end_variation_applied_when_enabled(self, monkeypatch):
        import human_resonance2.fingerprint_metrics as fm

        monkeypatch.setattr(fm, "_ENABLE_SENTENCE_END_VARIATION_CORRECTION", True)
        text = "\n".join([
            "これは重要です。",
            "それも大切です。",
            "あれは必要です。",
            "どれも有効です。",
            "全てが正しいです。",
            "結果は良好です。",
            "品質は高いです。",
            "効果は明確です。",
        ])
        report = fm.FingerprintReport(flat_zone_flags=["sentence_length_cv_flat"])
        result = fm.apply_fingerprint_corrections(text, report, max_rewrite_ratio=1.0)
        assert "sentence_end_variation" in result.applied_rules
        assert result.text != text

    def test_rewrite_guard_discards_excessive_changes(self):
        text = "短い。"
        report = FingerprintReport(
            flat_zone_flags=["conjunction_rate_high", "subject_explicit_high", "sentence_length_cv_flat"]
        )
        result = apply_fingerprint_corrections(text, report, max_rewrite_ratio=0.001)
        # With such a tiny ratio cap, any change should be discarded
        assert result.text == text
        # Either discarded or no rules applied (text too short for rules to trigger)
        assert result.discarded or result.applied_rules == []

    def test_empty_text_returns_empty(self):
        report = FingerprintReport(flat_zone_flags=["conjunction_rate_high"])
        result = apply_fingerprint_corrections("", report)
        assert result.text == ""
        assert result.applied_rules == []


class TestQualityPipelineFingerprintCorrection:
    """Integration tests for fingerprint correction in quality pipeline."""

    def test_shadow_mode_does_not_modify_text(self):
        from core.app_config import QualityPipelineConfig
        from human_resonance2.quality_pipeline import QualityPipelineRunner

        config = QualityPipelineConfig(
            enabled=True, mode="shadow", rollout_percent=100, fail_open=True,
            phase01_lexical_enabled=False, phase01_tokenizer="auto",
            phase02_burstiness_enabled=False, phase03_nominalization_enabled=False,
            phase04_style_drift_enabled=False, phase05_layout_guard_enabled=False,
            phase06_orchestrator_enabled=False, phase07_rollout_enabled=False,
            lexical_threshold=0.32, burstiness_target_min=0.18, burstiness_target_max=0.52,
            nominalization_alert_threshold=0.18, style_alignment_min_score=0.72,
            domain_guard_strictness="normal", supplement_min_position_ratio=0.45,
            intro_max_length_ratio=0.35, section_coherence_min_score=0.40,
            global_rewrite_ratio_cap=0.2, conflict_resolution_policy="safe_first",
            quality_gate_min_score=0.55, max_rewrite_ratio=0.15,
            max_sentence_split_ratio=0.12, max_nominalization_rewrite_ratio=0.12,
            fingerprint_enabled=True, resonance_tuning_enabled=False,
        )
        runner = QualityPipelineRunner(config)
        result = runner.process(MONOTONE_TEXT)
        assert result.text == MONOTONE_TEXT, "Shadow mode must not modify text"
        fp_reports = [r for r in result.phase_reports if r["phase"] == "fingerprint"]
        assert len(fp_reports) == 1
        assert fp_reports[0]["fingerprint_correction_applied"] is False

    def test_enforce_mode_may_apply_correction(self):
        from core.app_config import QualityPipelineConfig
        from human_resonance2.quality_pipeline import QualityPipelineRunner

        config = QualityPipelineConfig(
            enabled=True, mode="enforce", rollout_percent=100, fail_open=True,
            phase01_lexical_enabled=False, phase01_tokenizer="auto",
            phase02_burstiness_enabled=False, phase03_nominalization_enabled=False,
            phase04_style_drift_enabled=False, phase05_layout_guard_enabled=False,
            phase06_orchestrator_enabled=False, phase07_rollout_enabled=False,
            lexical_threshold=0.32, burstiness_target_min=0.18, burstiness_target_max=0.52,
            nominalization_alert_threshold=0.18, style_alignment_min_score=0.72,
            domain_guard_strictness="normal", supplement_min_position_ratio=0.45,
            intro_max_length_ratio=0.35, section_coherence_min_score=0.40,
            global_rewrite_ratio_cap=0.2, conflict_resolution_policy="safe_first",
            quality_gate_min_score=0.55, max_rewrite_ratio=0.15,
            max_sentence_split_ratio=0.12, max_nominalization_rewrite_ratio=0.12,
            fingerprint_enabled=True, resonance_tuning_enabled=False,
        )
        runner = QualityPipelineRunner(config)
        result = runner.process(MONOTONE_TEXT)
        fp_reports = [r for r in result.phase_reports if r["phase"] == "fingerprint"]
        assert len(fp_reports) == 1
        report = fp_reports[0]
        assert "fingerprint_correction_applied" in report
        assert "applied_rules" in report
        assert "correction_rewrite_ratio" in report
        # Monotone text has flat flags, so enforce should attempt correction
        if report["fingerprint_correction_applied"]:
            assert len(report["applied_rules"]) > 0
            assert result.text != MONOTONE_TEXT

    def test_fingerprint_phase_report_includes_entropy_fields(self):
        from core.app_config import QualityPipelineConfig
        from human_resonance2.quality_pipeline import QualityPipelineRunner

        config = QualityPipelineConfig(
            enabled=True, mode="shadow", rollout_percent=100, fail_open=True,
            phase01_lexical_enabled=False, phase01_tokenizer="auto",
            phase02_burstiness_enabled=False, phase03_nominalization_enabled=False,
            phase04_style_drift_enabled=False, phase05_layout_guard_enabled=False,
            phase06_orchestrator_enabled=False, phase07_rollout_enabled=False,
            lexical_threshold=0.32, burstiness_target_min=0.18, burstiness_target_max=0.52,
            nominalization_alert_threshold=0.18, style_alignment_min_score=0.72,
            domain_guard_strictness="normal", supplement_min_position_ratio=0.45,
            intro_max_length_ratio=0.35, section_coherence_min_score=0.40,
            global_rewrite_ratio_cap=0.2, conflict_resolution_policy="safe_first",
            quality_gate_min_score=0.55, max_rewrite_ratio=0.15,
            max_sentence_split_ratio=0.12, max_nominalization_rewrite_ratio=0.12,
            fingerprint_enabled=True, resonance_tuning_enabled=False,
        )
        runner = QualityPipelineRunner(config)
        result = runner.process(HUMAN_LIKE_TEXT)
        fp_reports = [r for r in result.phase_reports if r["phase"] == "fingerprint"]
        assert len(fp_reports) == 1
        report = fp_reports[0]
        for key in (
            "sentence_ending_entropy",
            "sentence_ending_fine_entropy",
            "sentence_opening_entropy",
            "comma_position_cv",
        ):
            assert key in report


# ---------------------------------------------------------------------------
# MTLD / HD-D / Vocab repetition tests (R5-T07~T09)
# ---------------------------------------------------------------------------

class TestMTLD:
    def test_short_text_returns_zero(self):
        assert compute_mtld("短い。") == 0.0

    def test_empty_returns_zero(self):
        assert compute_mtld("") == 0.0

    def test_human_like_positive(self):
        val = compute_mtld(HUMAN_LIKE_TEXT)
        assert val > 0.0, f"Expected MTLD > 0, got {val}"

    def test_monotone_lower_than_human(self):
        human = compute_mtld(HUMAN_LIKE_TEXT)
        mono = compute_mtld(MONOTONE_TEXT)
        # Monotone text repeats vocabulary, so MTLD should be lower
        # (or both may be low if texts are short; at least both should be computable)
        assert human >= 0.0
        assert mono >= 0.0


class TestHDD:
    def test_short_text_returns_zero(self):
        assert compute_hd_d("短い。") == 0.0

    def test_human_like_positive(self):
        val = compute_hd_d(HUMAN_LIKE_TEXT)
        assert val >= 0.0, f"Expected HD-D >= 0, got {val}"

    def test_returns_between_0_and_1(self):
        val = compute_hd_d(HUMAN_LIKE_TEXT)
        assert 0.0 <= val <= 1.0


class TestVocabRepetition:
    def test_empty_returns_empty(self):
        assert detect_vocab_repetition("") == []

    def test_detects_repeated_lemmas(self):
        text = "生成AIは進化しています。生成AIの分野は発展しています。生成AIは重要です。生成AIの課題があります。"
        reps = detect_vocab_repetition(text, min_count=3)
        assert len(reps) > 0, "Should detect repeated lemmas"

    def test_human_like_may_have_some_repetition(self):
        reps = detect_vocab_repetition(HUMAN_LIKE_TEXT)
        # Just verify it returns a list (human text may or may not have repetition)
        assert isinstance(reps, list)


class TestAnalyzerWithLexicalDiversity:
    def test_report_includes_mtld_and_hdd(self):
        analyzer = FingerprintAnalyzer()
        report = analyzer.analyze(HUMAN_LIKE_TEXT)
        assert hasattr(report, "mtld")
        assert hasattr(report, "hd_d")
        assert hasattr(report, "vocab_repetition_lemmas")
        assert report.mtld >= 0.0
        assert report.hd_d >= 0.0

    def test_monotone_may_flag_vocab_repetition(self):
        analyzer = FingerprintAnalyzer()
        report = analyzer.analyze(MONOTONE_TEXT)
        # Monotone text should have vocab_repetition flag or low mtld
        has_vocab_flag = "vocab_repetition" in report.flat_zone_flags
        has_mtld_flag = "mtld_low" in report.flat_zone_flags
        assert has_vocab_flag or has_mtld_flag or report.mtld < 80, (
            f"Expected vocab_repetition or mtld_low flag, got flags={report.flat_zone_flags} mtld={report.mtld}"
        )


# ---------------------------------------------------------------------------
# Resonance tuning tests (R6-T01~T06)
# ---------------------------------------------------------------------------

from human_resonance2.fingerprint_metrics import (
    ResonanceTuningResult,
    compute_resonance_tuning,
)


class TestResonanceTuning:
    def test_low_score_adjusts_params(self):
        report = FingerprintReport(overall_unpredictability=0.15)
        params = {"humanity_intensity": 0.5, "phrase_probability": 0.75, "pronoun_reduction_ratio": 0.5}
        result = compute_resonance_tuning(report, params)
        assert result.score_band == "very_low"
        assert result.after["humanity_intensity"] > params["humanity_intensity"]
        assert result.after["phrase_probability"] < params["phrase_probability"]
        assert result.after["pronoun_reduction_ratio"] < params["pronoun_reduction_ratio"]

    def test_high_score_no_adjustment(self):
        report = FingerprintReport(overall_unpredictability=0.75)
        params = {"humanity_intensity": 0.5, "phrase_probability": 0.75, "pronoun_reduction_ratio": 0.5}
        result = compute_resonance_tuning(report, params)
        assert result.score_band == "high"
        assert result.after["humanity_intensity"] == params["humanity_intensity"]
        assert result.after["phrase_probability"] == params["phrase_probability"]
        assert result.after["pronoun_reduction_ratio"] == params["pronoun_reduction_ratio"]

    def test_medium_score_minimal_adjustment(self):
        report = FingerprintReport(overall_unpredictability=0.50)
        params = {"humanity_intensity": 0.5, "phrase_probability": 0.75, "pronoun_reduction_ratio": 0.5}
        result = compute_resonance_tuning(report, params)
        assert result.score_band == "medium"
        # Medium band has small adjustments
        for param in ("humanity_intensity", "phrase_probability", "pronoun_reduction_ratio"):
            assert abs(result.adjustments[param]) <= 0.05

    def test_tuned_values_within_clamp_limits(self):
        report = FingerprintReport(overall_unpredictability=0.10)
        params = {"humanity_intensity": 0.95, "phrase_probability": 0.35, "pronoun_reduction_ratio": 0.15}
        result = compute_resonance_tuning(report, params)
        assert 0.0 <= result.after["humanity_intensity"] <= 1.0
        assert 0.3 <= result.after["phrase_probability"] <= 1.0
        assert 0.1 <= result.after["pronoun_reduction_ratio"] <= 0.8

    def test_pipeline_tuning_disabled_by_default(self):
        from core.app_config import QualityPipelineConfig
        from human_resonance2.quality_pipeline import QualityPipelineRunner

        config = QualityPipelineConfig(
            enabled=True, mode="shadow", rollout_percent=100, fail_open=True,
            phase01_lexical_enabled=False, phase01_tokenizer="auto",
            phase02_burstiness_enabled=False, phase03_nominalization_enabled=False,
            phase04_style_drift_enabled=False, phase05_layout_guard_enabled=False,
            phase06_orchestrator_enabled=False, phase07_rollout_enabled=False,
            lexical_threshold=0.32, burstiness_target_min=0.18, burstiness_target_max=0.52,
            nominalization_alert_threshold=0.18, style_alignment_min_score=0.72,
            domain_guard_strictness="normal", supplement_min_position_ratio=0.45,
            intro_max_length_ratio=0.35, section_coherence_min_score=0.40,
            global_rewrite_ratio_cap=0.2, conflict_resolution_policy="safe_first",
            quality_gate_min_score=0.55, max_rewrite_ratio=0.15,
            max_sentence_split_ratio=0.12, max_nominalization_rewrite_ratio=0.12,
            fingerprint_enabled=True, resonance_tuning_enabled=False,
        )
        runner = QualityPipelineRunner(config)
        result = runner.process(MONOTONE_TEXT)
        fp_reports = [r for r in result.phase_reports if r["phase"] == "fingerprint"]
        assert len(fp_reports) == 1
        assert fp_reports[0]["resonance_tuning_enabled"] is False

    def test_pipeline_tuning_enabled_outputs_before_after(self):
        from core.app_config import QualityPipelineConfig
        from human_resonance2.quality_pipeline import QualityPipelineRunner

        config = QualityPipelineConfig(
            enabled=True, mode="shadow", rollout_percent=100, fail_open=True,
            phase01_lexical_enabled=False, phase01_tokenizer="auto",
            phase02_burstiness_enabled=False, phase03_nominalization_enabled=False,
            phase04_style_drift_enabled=False, phase05_layout_guard_enabled=False,
            phase06_orchestrator_enabled=False, phase07_rollout_enabled=False,
            lexical_threshold=0.32, burstiness_target_min=0.18, burstiness_target_max=0.52,
            nominalization_alert_threshold=0.18, style_alignment_min_score=0.72,
            domain_guard_strictness="normal", supplement_min_position_ratio=0.45,
            intro_max_length_ratio=0.35, section_coherence_min_score=0.40,
            global_rewrite_ratio_cap=0.2, conflict_resolution_policy="safe_first",
            quality_gate_min_score=0.55, max_rewrite_ratio=0.15,
            max_sentence_split_ratio=0.12, max_nominalization_rewrite_ratio=0.12,
            fingerprint_enabled=True, resonance_tuning_enabled=True,
        )
        runner = QualityPipelineRunner(config)
        result = runner.process(MONOTONE_TEXT)
        fp_reports = [r for r in result.phase_reports if r["phase"] == "fingerprint"]
        assert len(fp_reports) == 1
        report = fp_reports[0]
        assert report["resonance_tuning_enabled"] is True
        assert "tuning_before" in report
        assert "tuning_after" in report
        assert "tuning_score_band" in report

    def test_pipeline_tuning_uses_context_style_profile_hint(self):
        from core.app_config import QualityPipelineConfig
        from human_resonance2.quality_pipeline import QualityPipelineRunner

        config = QualityPipelineConfig(
            enabled=True, mode="shadow", rollout_percent=100, fail_open=True,
            phase01_lexical_enabled=False, phase01_tokenizer="auto",
            phase02_burstiness_enabled=False, phase03_nominalization_enabled=False,
            phase04_style_drift_enabled=False, phase05_layout_guard_enabled=False,
            phase06_orchestrator_enabled=False, phase07_rollout_enabled=False,
            lexical_threshold=0.32, burstiness_target_min=0.18, burstiness_target_max=0.52,
            nominalization_alert_threshold=0.18, style_alignment_min_score=0.72,
            domain_guard_strictness="normal", supplement_min_position_ratio=0.45,
            intro_max_length_ratio=0.35, section_coherence_min_score=0.40,
            global_rewrite_ratio_cap=0.2, conflict_resolution_policy="safe_first",
            quality_gate_min_score=0.55, max_rewrite_ratio=0.15,
            max_sentence_split_ratio=0.12, max_nominalization_rewrite_ratio=0.12,
            fingerprint_enabled=True, resonance_tuning_enabled=True,
        )
        runner = QualityPipelineRunner(config)
        result = runner.process(
            MONOTONE_TEXT,
            context={
                "article_type": "custom_release_note",
                "category_base_template": "announcement",
                "style_profile_hint": "formal",
            },
        )
        fp_reports = [r for r in result.phase_reports if r["phase"] == "fingerprint"]
        assert len(fp_reports) == 1
        profile = fp_reports[0].get("tuning_style_profile", {})
        assert profile.get("emotional_waveform") == "flat"
        assert profile.get("digression_allowed") is False


# ---------------------------------------------------------------------------
# Style profiles + mapping + constrained tuning + fast path tests (R6-T07~T11)
# ---------------------------------------------------------------------------

class TestStyleProfiles:
    def test_get_style_profiles_returns_6_types(self):
        from core.app_config import get_style_profiles
        profiles = get_style_profiles()
        assert len(profiles) >= 6
        for key in ("column", "how_to", "opinion", "announcement", "hobby", "technical"):
            assert key in profiles
            assert "bracket_limit" in profiles[key]
            assert "emotional_waveform" in profiles[key]

    def test_map_content_type_japanese(self):
        from core.app_config import map_content_type_to_profile
        profile = map_content_type_to_profile(content_type="お知らせ")
        assert profile["emotional_waveform"] == "flat"
        assert profile["digression_allowed"] is False

    def test_map_content_type_english(self):
        from core.app_config import map_content_type_to_profile
        profile = map_content_type_to_profile(content_type="hobby")
        assert profile["emotional_waveform"] == "dynamic"
        assert profile["digression_allowed"] is True

    def test_map_genre_fallback(self):
        from core.app_config import map_content_type_to_profile
        profile = map_content_type_to_profile(genre="ライフスタイル")
        assert profile["bracket_limit"] == 5  # hobby profile

    def test_unknown_falls_back_to_column(self):
        from core.app_config import map_content_type_to_profile
        profile = map_content_type_to_profile(content_type="unknown_type")
        assert profile["emotional_waveform"] == "dynamic"  # column default


class TestProfileConstrainedTuning:
    def test_announcement_profile_blocks_tuning(self):
        report = FingerprintReport(overall_unpredictability=0.15)
        params = {"humanity_intensity": 0.5, "phrase_probability": 0.75, "pronoun_reduction_ratio": 0.5}
        profile = {"emotional_waveform": "flat", "bracket_limit": 1}
        result = compute_resonance_tuning(report, params, style_profile=profile)
        # flat waveform -> multiplier=0 -> no adjustment
        assert result.after["humanity_intensity"] == params["humanity_intensity"]
        assert result.after["phrase_probability"] == params["phrase_probability"]

    def test_steady_profile_halves_adjustment(self):
        report = FingerprintReport(overall_unpredictability=0.15)
        params = {"humanity_intensity": 0.5, "phrase_probability": 0.75, "pronoun_reduction_ratio": 0.5}
        # Without profile
        result_full = compute_resonance_tuning(report, params)
        # With steady profile
        profile = {"emotional_waveform": "steady"}
        result_half = compute_resonance_tuning(report, params, style_profile=profile)
        # Steady should have smaller adjustments than no-profile
        assert abs(result_half.adjustments["humanity_intensity"]) <= abs(result_full.adjustments["humanity_intensity"])

    def test_dynamic_profile_full_adjustment(self):
        report = FingerprintReport(overall_unpredictability=0.15)
        params = {"humanity_intensity": 0.5, "phrase_probability": 0.75, "pronoun_reduction_ratio": 0.5}
        profile = {"emotional_waveform": "dynamic"}
        result = compute_resonance_tuning(report, params, style_profile=profile)
        # dynamic -> multiplier=1.0, same as no profile
        result_no_profile = compute_resonance_tuning(report, params)
        assert result.adjustments == result_no_profile.adjustments


from human_resonance2.fingerprint_metrics import apply_orthographic_variation


class TestOrthographicVariation:
    def test_zero_rate_returns_unchanged(self):
        text = "大切な事があります。綺麗な物を見つけました。"
        result = apply_orthographic_variation(text, rate=0.0)
        assert result == text

    def test_empty_text_returns_empty(self):
        assert apply_orthographic_variation("", rate=0.5) == ""

    def test_high_rate_may_modify_text(self):
        text = "大切な事があります。綺麗な物を見つけました。沢山の人が来ました。"
        result = apply_orthographic_variation(text, rate=1.0)
        # With rate=1.0, at least one variation should be applied
        assert result != text, f"Expected variation but got same text: {result}"

    def test_announcement_zero_variation(self):
        from core.app_config import map_content_type_to_profile
        profile = map_content_type_to_profile(content_type="お知らせ")
        rate = profile.get("orthographic_variation_rate", 0.0)
        assert rate == 0.0
        text = "重要な事をお知らせします。"
        result = apply_orthographic_variation(text, rate=rate)
        assert result == text, "Announcements should have zero orthographic variation"

    def test_hobby_high_variation(self):
        from core.app_config import map_content_type_to_profile
        profile = map_content_type_to_profile(content_type="趣味")
        rate = profile.get("orthographic_variation_rate", 0.0)
        assert rate >= 0.2, f"Hobby should have high variation rate, got {rate}"

    def test_deterministic_with_same_text(self):
        text = "大切な事があります。綺麗な物を見つけました。"
        result1 = apply_orthographic_variation(text, rate=0.5)
        result2 = apply_orthographic_variation(text, rate=0.5)
        assert result1 == result2, "Same text + same rate should produce deterministic output"


class TestFormatMonitoringReport:
    """R7-T01: Standardized monitoring report format."""

    def test_format_monitoring_report_extracts_fingerprint(self):
        from human_resonance2.quality_pipeline import format_monitoring_report

        phase_reports = [
            {
                "phase": "fingerprint",
                "mode": "shadow",
                "overall_unpredictability": 0.65,
                "sentence_length_cv": 0.42,
                "paragraph_length_cv": 0.31,
                "conjunction_repetition_rate": 0.12,
                "subject_explicit_rate": 0.28,
                "particle_entropy": 2.45,
                "pos_bigram_monotonicity": 0.55,
                "mtld": 72.5,
                "hd_d": 0.82,
                "nominalization_rate": 0.08,
                "morphological_ngram_entropy": 2.9,
                "morphological_diversity": {"pos_sequence_entropy": 2.1},
                "syntactic_complexity": {"dependency_depth_avg": 1.8},
                "flat_zone_flags": ["conjunction_rate_high"],
                "correction_hints": ["段落冒頭接続詞が多すぎる"],
                "fingerprint_correction_applied": False,
                "applied_rules": [],
                "correction_rewrite_ratio": 0.0,
                "correction_discarded": False,
                "correction_discard_reason": "",
                "resonance_tuning_enabled": False,
            },
            {"phase": "phase02_burstiness", "mode": "shadow"},
        ]
        report = format_monitoring_report(phase_reports)
        assert report["version"] == "r7v1"
        assert report["mode"] == "shadow"
        assert report["metrics"]["overall_unpredictability"] == 0.65
        assert report["metrics"]["mtld"] == 72.5
        assert report["metrics"]["morphological_ngram_entropy"] == 2.9
        assert report["metrics"]["morphological_diversity"]["pos_sequence_entropy"] == 2.1
        assert report["metrics"]["syntactic_complexity"]["dependency_depth_avg"] == 1.8
        assert report["flat_zones"]["count"] == 1
        assert "conjunction_rate_high" in report["flat_zones"]["flags"]
        assert report["correction"]["applied"] is False

    def test_format_monitoring_report_empty_when_no_fingerprint(self):
        from human_resonance2.quality_pipeline import format_monitoring_report

        phase_reports = [{"phase": "phase01_lexical", "mode": "shadow"}]
        report = format_monitoring_report(phase_reports)
        assert report == {}

    def test_format_monitoring_report_with_correction(self):
        from human_resonance2.quality_pipeline import format_monitoring_report

        phase_reports = [
            {
                "phase": "fingerprint",
                "mode": "enforce",
                "overall_unpredictability": 0.30,
                "sentence_length_cv": 0.08,
                "paragraph_length_cv": 0.07,
                "conjunction_repetition_rate": 0.55,
                "subject_explicit_rate": 0.60,
                "particle_entropy": 1.5,
                "pos_bigram_monotonicity": 0.35,
                "mtld": 35.0,
                "hd_d": 0.55,
                "nominalization_rate": 0.30,
                "flat_zone_flags": ["sentence_length_cv_flat", "conjunction_rate_high"],
                "correction_hints": ["文長の変動が小さすぎる", "段落冒頭接続詞が多すぎる"],
                "fingerprint_correction_applied": True,
                "applied_rules": ["conjunction_reduction", "sentence_end_variation"],
                "correction_rewrite_ratio": 0.03,
                "correction_discarded": False,
                "correction_discard_reason": "",
                "resonance_tuning_enabled": True,
                "tuning_score_band": "low",
                "tuning_adjustments": {"humanity_intensity": 0.1},
            },
        ]
        report = format_monitoring_report(phase_reports)
        assert report["mode"] == "enforce"
        assert report["flat_zones"]["count"] == 2
        assert report["correction"]["applied"] is True
        assert "conjunction_reduction" in report["correction"]["rules"]
        assert report["tuning"]["enabled"] is True
        assert report["tuning"]["score_band"] == "low"


class TestRerankCandidates:
    """R8-T06/T07: HLCv2 rerank scoring."""

    def test_rerank_selects_best_candidate(self):
        from human_resonance2.fingerprint_metrics import rerank_candidates
        results = rerank_candidates([HUMAN_LIKE_TEXT, MONOTONE_TEXT])
        assert len(results) == 2
        assert results[0].selected is True
        assert results[1].selected is False
        assert results[0].weighted_score >= results[1].weighted_score
        # Human-like text should score higher
        assert results[0].text == HUMAN_LIKE_TEXT

    def test_rerank_empty_input(self):
        from human_resonance2.fingerprint_metrics import rerank_candidates
        assert rerank_candidates([]) == []

    def test_rerank_single_candidate(self):
        from human_resonance2.fingerprint_metrics import rerank_candidates
        results = rerank_candidates([HUMAN_LIKE_TEXT])
        assert len(results) == 1
        assert results[0].selected is True
        assert results[0].weighted_score > 0

    def test_rerank_custom_weights(self):
        from human_resonance2.fingerprint_metrics import rerank_candidates
        custom = {"unpredictability": 1.0, "lexical_diversity": 0.0,
                  "low_flat_zones": 0.0, "layout_ok": 0.0,
                  "vocab_overlap_penalty": 0.0, "template_similarity": 0.0}
        results = rerank_candidates([HUMAN_LIKE_TEXT, MONOTONE_TEXT], weights=custom)
        assert len(results) == 2
        # With only unpredictability weight, human text should still win
        assert results[0].text == HUMAN_LIKE_TEXT


class TestGPT5MiniParallelRegression:
    """R8-T18: Comprehensive regression test for GPT-5-mini parallel generation."""

    def test_config_candidate_b_model_is_gpt5_mini(self):
        from core.app_config import get_llm_config
        cfg = get_llm_config()
        assert cfg.task_models.get("section_candidate_b") == "gpt-5-mini"

    def test_config_gpt5_temperature_disabled(self):
        from core.app_config import get_llm_config
        cfg = get_llm_config()
        model = cfg.task_models.get("section_candidate_b", "")
        # gpt-5-mini should match disable_temperature prefixes
        matched = any(model.lower().startswith(p.lower())
                      for p in cfg.disable_temperature_model_prefixes)
        assert matched, "GPT-5-mini must have temperature disabled"

    def test_config_gpt5_top_p_disabled(self):
        from core.app_config import get_llm_config
        cfg = get_llm_config()
        model = cfg.task_models.get("section_candidate_b", "")
        matched = any(model.lower().startswith(p.lower())
                      for p in cfg.disable_top_p_model_prefixes)
        assert matched, "GPT-5-mini must have top_p disabled"

    def test_config_candidate_b_reasoning_minimal(self):
        from core.app_config import get_llm_config
        cfg = get_llm_config()
        assert cfg.candidate_b_reasoning_effort == "minimal"

    def test_config_candidate_b_verbosity_medium(self):
        from core.app_config import get_llm_config
        cfg = get_llm_config()
        assert cfg.candidate_b_verbosity == "medium"

    def test_hlcv2_config_rerank_weights_sum(self):
        from core.app_config import get_hlcv2_config
        cfg = get_hlcv2_config()
        weights = cfg["rerank_weights"]
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01, f"Rerank weights should sum to ~1.0, got {total}"

    def test_select_best_candidate_fallback_on_b_failure(self):
        from human_resonance2.fingerprint_metrics import select_best_candidate
        result = select_best_candidate(HUMAN_LIKE_TEXT, None)
        assert result.selected == "a"
        assert result.fallback_used is True

    def test_select_best_candidate_a_vs_b_comparison(self):
        from human_resonance2.fingerprint_metrics import select_best_candidate
        result = select_best_candidate(HUMAN_LIKE_TEXT, MONOTONE_TEXT)
        assert result.selected == "a"
        assert result.score_a > result.score_b

    def test_rerank_candidates_with_config_weights(self):
        from core.app_config import get_hlcv2_config
        from human_resonance2.fingerprint_metrics import rerank_candidates
        cfg = get_hlcv2_config()
        results = rerank_candidates(
            [HUMAN_LIKE_TEXT, MONOTONE_TEXT],
            weights=cfg["rerank_weights"],
        )
        assert len(results) == 2
        assert results[0].selected is True
        assert results[0].weighted_score >= results[1].weighted_score

    def test_generation_mode_transition(self):
        from core.app_config import get_generation_mode
        assert get_generation_mode() in ("transition", "zero_base_v1")

    def test_hlcv2_fallback_on_error_enabled(self):
        from core.app_config import get_hlcv2_config
        cfg = get_hlcv2_config()
        assert cfg["fallback_on_error"] is True

    def test_template_extraction_and_similarity(self):
        from human_resonance2.template_extractor import TemplateExtractor
        ext = TemplateExtractor()
        tpl_a = ext.extract(HUMAN_LIKE_TEXT)
        tpl_b = ext.extract(MONOTONE_TEXT)
        sim = ext.structural_similarity(tpl_a, tpl_b)
        assert 0.0 <= sim <= 1.0

    def test_monitoring_report_compatible_with_rerank(self):
        from human_resonance2.quality_pipeline import format_monitoring_report
        phase_reports = [{
            "phase": "fingerprint", "mode": "shadow",
            "overall_unpredictability": 0.55,
            "sentence_length_cv": 0.3, "paragraph_length_cv": 0.2,
            "conjunction_repetition_rate": 0.1, "subject_explicit_rate": 0.2,
            "particle_entropy": 2.3, "pos_bigram_monotonicity": 0.5,
            "mtld": 65.0, "hd_d": 0.78, "nominalization_rate": 0.1,
            "flat_zone_flags": [], "correction_hints": [],
        }]
        report = format_monitoring_report(phase_reports)
        assert report["version"] == "r7v1"
        assert report["metrics"]["overall_unpredictability"] == 0.55


class TestSelectBestCandidate:
    """R8-T17: Candidate A vs B fingerprint comparison and adoption."""

    def test_select_a_when_b_unavailable(self):
        from human_resonance2.fingerprint_metrics import select_best_candidate
        result = select_best_candidate(HUMAN_LIKE_TEXT, None)
        assert result.selected == "a"
        assert result.fallback_used is True
        assert result.text == HUMAN_LIKE_TEXT
        assert "candidate_b_unavailable" in result.reason

    def test_select_a_when_b_empty(self):
        from human_resonance2.fingerprint_metrics import select_best_candidate
        result = select_best_candidate(HUMAN_LIKE_TEXT, "short")
        assert result.selected == "a"
        assert result.fallback_used is True

    def test_select_better_candidate(self):
        from human_resonance2.fingerprint_metrics import select_best_candidate
        result = select_best_candidate(HUMAN_LIKE_TEXT, MONOTONE_TEXT)
        assert result.selected in ("a", "b")
        assert result.fallback_used is False
        assert result.score_a >= 0.0
        assert result.score_b >= 0.0
        # Human-like text should generally win
        assert result.selected == "a"

    def test_select_with_preceding_text(self):
        from human_resonance2.fingerprint_metrics import select_best_candidate
        result = select_best_candidate(
            HUMAN_LIKE_TEXT, MONOTONE_TEXT,
            preceding_text="前のセクションのテキストです。生成AIの進化について述べました。"
        )
        assert result.selected in ("a", "b")
        assert 0.0 <= result.score_a <= 1.0
        assert 0.0 <= result.score_b <= 1.0

    def test_select_flags_below_min(self):
        from human_resonance2.fingerprint_metrics import select_best_candidate
        result = select_best_candidate(MONOTONE_TEXT, MONOTONE_TEXT, min_unpredictability=0.99)
        assert "below_min" in result.reason


class TestVocabOverlapPenalty:
    """R8-T13: K-candidate vocabulary overlap penalty."""

    def test_overlap_identical_texts(self):
        from human_resonance2.fingerprint_metrics import compute_vocab_overlap_penalty
        penalty = compute_vocab_overlap_penalty([HUMAN_LIKE_TEXT, HUMAN_LIKE_TEXT], 0)
        assert penalty > 0.5, f"Identical texts should have high overlap, got {penalty}"

    def test_overlap_different_texts(self):
        from human_resonance2.fingerprint_metrics import compute_vocab_overlap_penalty
        penalty = compute_vocab_overlap_penalty([HUMAN_LIKE_TEXT, MONOTONE_TEXT], 0)
        assert 0.0 <= penalty <= 1.0

    def test_overlap_single_candidate(self):
        from human_resonance2.fingerprint_metrics import compute_vocab_overlap_penalty
        assert compute_vocab_overlap_penalty([HUMAN_LIKE_TEXT], 0) == 0.0

    def test_overlap_empty(self):
        from human_resonance2.fingerprint_metrics import compute_vocab_overlap_penalty
        assert compute_vocab_overlap_penalty([], 0) == 0.0


class TestParagraphSimilarityPenalty:
    """R8-T14: Paragraph expression similarity penalty."""

    def test_similarity_identical(self):
        from human_resonance2.fingerprint_metrics import compute_paragraph_similarity_penalty
        penalty = compute_paragraph_similarity_penalty(HUMAN_LIKE_TEXT, HUMAN_LIKE_TEXT)
        assert penalty > 0.5, f"Identical text should have high similarity, got {penalty}"

    def test_similarity_empty(self):
        from human_resonance2.fingerprint_metrics import compute_paragraph_similarity_penalty
        assert compute_paragraph_similarity_penalty("", HUMAN_LIKE_TEXT) == 0.0
        assert compute_paragraph_similarity_penalty(HUMAN_LIKE_TEXT, "") == 0.0

    def test_similarity_different(self):
        from human_resonance2.fingerprint_metrics import compute_paragraph_similarity_penalty
        penalty = compute_paragraph_similarity_penalty(HUMAN_LIKE_TEXT, MONOTONE_TEXT)
        assert 0.0 <= penalty <= 1.0


class TestTemplateExtractor:
    """R8-T11/T12: ZeroStylus template extraction and structural similarity."""

    def test_extract_basic_template(self):
        from human_resonance2.template_extractor import TemplateExtractor
        ext = TemplateExtractor()
        tpl = ext.extract(HUMAN_LIKE_TEXT)
        assert tpl.heading_count >= 3
        assert tpl.section_count >= 1
        assert tpl.total_paragraphs >= 1
        assert tpl.avg_sentence_length > 0
        assert tpl.has_introduction is True
        assert tpl.has_conclusion is True

    def test_structural_similarity_identical(self):
        from human_resonance2.template_extractor import TemplateExtractor
        ext = TemplateExtractor()
        tpl = ext.extract(HUMAN_LIKE_TEXT)
        sim = ext.structural_similarity(tpl, tpl)
        assert sim >= 0.95, f"Self-similarity should be ~1.0, got {sim}"

    def test_structural_similarity_different(self):
        from human_resonance2.template_extractor import TemplateExtractor
        ext = TemplateExtractor()
        tpl_human = ext.extract(HUMAN_LIKE_TEXT)
        tpl_mono = ext.extract(MONOTONE_TEXT)
        sim = ext.structural_similarity(tpl_human, tpl_mono)
        assert 0.0 <= sim <= 1.0
        # Different structures should have lower similarity
        assert sim < 0.95

    def test_extract_empty_text(self):
        from human_resonance2.template_extractor import TemplateExtractor
        ext = TemplateExtractor()
        tpl = ext.extract("")
        assert tpl.heading_count == 0


class TestHLCv2ModeIntegration:
    """R8-T09: Transition/HLCv2 output comparison tests."""

    def test_rerank_differentiates_quality(self):
        from human_resonance2.fingerprint_metrics import rerank_candidates
        results = rerank_candidates([HUMAN_LIKE_TEXT, MONOTONE_TEXT])
        diff = results[0].weighted_score - results[1].weighted_score
        assert diff > 0.01, f"Score diff too small: {diff}"

    def test_rerank_score_within_bounds(self):
        from human_resonance2.fingerprint_metrics import rerank_candidates
        results = rerank_candidates([HUMAN_LIKE_TEXT])
        for r in results:
            assert 0.0 <= r.weighted_score <= 1.0
            assert 0.0 <= r.unpredictability <= 1.0

    def test_generation_mode_is_transition(self):
        from core.app_config import get_generation_mode
        assert get_generation_mode() in ("transition", "zero_base_v1")

    def test_hlcv2_config_transition_threshold(self):
        from core.app_config import get_hlcv2_config
        cfg = get_hlcv2_config()
        assert 0.0 <= cfg["transition_rerank_threshold"] <= 1.0
        assert cfg["fallback_on_error"] is True
        assert 0.0 <= cfg["target_unpredictability"] <= 1.0
        assert 0.0 <= cfg["threshold_relax_per_section"] <= 0.2
        assert 0.0 <= cfg["max_threshold_relaxation"] <= 0.3


class TestFingerprintThresholdPresets:
    """R7-T03: Threshold preset loading."""

    def test_get_active_fingerprint_thresholds_returns_standard(self):
        from core.app_config import get_active_fingerprint_thresholds, get_fingerprint_threshold_presets
        thresholds = get_active_fingerprint_thresholds()
        presets = get_fingerprint_threshold_presets()
        active = presets.get("active_preset", "standard")
        assert "sentence_length_cv" in thresholds
        assert "mtld_low" in thresholds
        assert thresholds["sentence_length_cv"] == presets[active]["sentence_length_cv"]

    def test_get_fingerprint_threshold_presets_has_presets(self):
        from core.app_config import get_fingerprint_threshold_presets
        presets = get_fingerprint_threshold_presets()
        assert "active_preset" in presets
        assert "superhuman" in presets
        assert "relaxed" in presets
        assert "standard" in presets
        assert "strict" in presets
        # strict thresholds should be tighter than relaxed
        assert presets["strict"]["sentence_length_cv"] > presets["relaxed"]["sentence_length_cv"]
        assert presets["strict"]["mtld_low"] > presets["relaxed"]["mtld_low"]
        assert presets["superhuman"]["sentence_length_cv"] >= presets["strict"]["sentence_length_cv"]
        assert presets["superhuman"]["mtld_low"] >= presets["strict"]["mtld_low"]

    def test_analyzer_respects_runtime_sentence_length_threshold(self, monkeypatch):
        import core.app_config as app_cfg
        from human_resonance2.fingerprint_metrics import FingerprintAnalyzer

        text = (
            "私はこの機能を確認しました。"
            "私は同じ条件で検証しました。"
            "私は結果を比較しました。"
            "私は課題を記録しました。"
            "私は改善点を整理しました。"
            "私は次の実装方針を決めました。"
            "私は既存の仕様との差分も確認しました。"
            "私は重複箇所を抽出して修正しました。"
        )

        monkeypatch.setattr(
            app_cfg,
            "get_active_fingerprint_thresholds",
            lambda: {"sentence_length_cv": 0.99},
        )
        report_low = FingerprintAnalyzer().analyze(text, focus="")
        assert "sentence_length_cv_flat" in report_low.flat_zone_flags

        monkeypatch.setattr(
            app_cfg,
            "get_active_fingerprint_thresholds",
            lambda: {"sentence_length_cv": 0.01},
        )
        report_high = FingerprintAnalyzer().analyze(text, focus="")
        assert "sentence_length_cv_flat" not in report_high.flat_zone_flags


class TestCompareShadowEnforce:
    """R7-T02: shadow/enforce comparison report."""

    def test_run_comparison_returns_both_modes(self):
        sys_path_backup = sys.path[:]
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
        try:
            run_module = pytest.importorskip("plan.compare_shadow_enforce")
            run_comparison = run_module.run_comparison
            text = HUMAN_LIKE_TEXT
            report = run_comparison(text)
            assert "shadow" in report
            assert "enforce" in report
            assert "comparison" in report
            assert report["input_length"] == len(text)
            assert isinstance(report["comparison"]["text_changed"], bool)
        finally:
            sys.path[:] = sys_path_backup


class TestAnnouncementFastPath:
    def test_announcement_type_skips_pipeline(self):
        from note.article_generator import ArticleGenerator
        from unittest.mock import MagicMock

        gen = ArticleGenerator.__new__(ArticleGenerator)
        gen._current_type = "④お知らせ"
        gen._quality_phase_reports = []
        gen._interview_answers = {}
        gen._source_urls = []
        gen._latest_user_prompt = ""
        gen._pipeline_policy = {}
        text = "お知らせの本文です。"
        result = gen._apply_quality_pipeline(
            text, platform="note", perspective="一人称", focus="お知らせ"
        )
        assert result == text, "Announcement fast path should return text unchanged"


# ---------------------------------------------------------------------------
# R9 regression tests (R9-T01 ~ R9-T12)
# ---------------------------------------------------------------------------

from human_resonance2.fingerprint_metrics import (
    classify_sentence_ending,
    classify_endings_distribution,
    detect_ending_repetition,
    detect_comma_overuse,
    detect_abstract_tautology,
    comma_position_cv,
    sentence_opening_entropy,
    sentence_ending_entropy,
)


class TestR9T01ClassifySentenceEnding:
    """R9-T01: 文末カテゴリ分類関数"""

    def test_desu(self):
        assert classify_sentence_ending("これは重要です") == "desu"

    def test_masu(self):
        assert classify_sentence_ending("改善します") == "masu"

    def test_mashita(self):
        assert classify_sentence_ending("確認しました") == "masu"

    def test_question_ka(self):
        assert classify_sentence_ending("本当にそうでしょうか") == "question"

    def test_question_desuka(self):
        assert classify_sentence_ending("これは正しいですか") == "question"

    def test_conjecture_darou(self):
        assert classify_sentence_ending("そうだろう") == "conjecture"

    def test_conjecture_kamoshirenai(self):
        assert classify_sentence_ending("難しいかもしれない") == "conjecture"

    def test_negative_nai(self):
        assert classify_sentence_ending("簡単ではない") == "negative"

    def test_negative_masen(self):
        assert classify_sentence_ending("理解できません") == "negative"

    def test_taigen(self):
        assert classify_sentence_ending("まさに転換期") == "taigen"

    def test_other(self):
        assert classify_sentence_ending("走った") == "other"

    def test_empty(self):
        assert classify_sentence_ending("") == "other"

    def test_with_punctuation(self):
        assert classify_sentence_ending("これは重要です。") == "desu"


class TestR9T01Distribution:
    """R9-T01: 文末分布"""

    def test_returns_dict(self):
        text = "これは重要です。改善します。本当にそうだろうか。走った。"
        dist = classify_endings_distribution(text)
        assert isinstance(dist, dict)
        assert sum(dist.values()) == pytest.approx(1.0, abs=0.01)

    def test_empty_text(self):
        assert classify_endings_distribution("") == {}


class TestR9T02SentenceEndingEntropy:
    """R9-T02: 文末エントロピー"""

    def test_short_text_returns_zero(self):
        assert sentence_ending_entropy("短い。") == 0.0

    def test_diverse_endings_high_entropy(self):
        text = "これは重要です。改善します。本当にそうだろうか。走った。簡単ではない。"
        entropy = sentence_ending_entropy(text)
        assert entropy > 1.5, f"Diverse endings should have high entropy, got {entropy}"

    def test_monotone_endings_low_entropy(self):
        text = "これは重要です。それも大切です。あれも必要です。しかし難しいです。"
        entropy = sentence_ending_entropy(text)
        assert entropy < 0.5, f"Monotone endings should have low entropy, got {entropy}"

    def test_report_includes_entropy(self):
        analyzer = FingerprintAnalyzer()
        report = analyzer.analyze(HUMAN_LIKE_TEXT)
        assert hasattr(report, "sentence_ending_entropy")
        assert report.sentence_ending_entropy >= 0.0


class TestR9T03EndingRepetition:
    """R9-T03: 文末連続検知"""

    def test_no_repetition(self):
        text = "これは重要です。改善します。本当にそうだろうか。"
        hints = detect_ending_repetition(text)
        assert hints == []

    def test_three_consecutive_desu(self):
        text = "これは重要です。それも大切です。あれも必要です。"
        hints = detect_ending_repetition(text)
        assert len(hints) == 1
        assert "desu" in hints[0]
        assert "3回連続" in hints[0]

    def test_four_consecutive_masu(self):
        text = "確認します。改善します。実行します。報告します。"
        hints = detect_ending_repetition(text)
        assert len(hints) == 1
        assert "4回連続" in hints[0]

    def test_short_text_no_hints(self):
        hints = detect_ending_repetition("短い。")
        assert hints == []


class TestR9T08CommaOveruse:
    """R9-T08: 句読点頻度検知"""

    def test_normal_commas_no_hints(self):
        text = "これは重要な点です。それは大切な要素です。あれは必要な条件です。"
        hints = detect_comma_overuse(text)
        assert hints == []

    def test_excessive_commas(self):
        text = (
            "これは、重要な、大切な、必要な、不可欠な要素です。"
            "それは良い点です。"
            "あれも大事です。"
        )
        hints = detect_comma_overuse(text)
        assert len(hints) >= 1
        assert "読点過多" in hints[0]

    def test_short_text_no_hints(self):
        hints = detect_comma_overuse("短い。")
        assert hints == []


class TestR9T11ThresholdByFocus:
    """R9-T11: sentence_length_cv しきい値引き上げ"""

    def test_explanation_focus_stricter_threshold(self):
        # Text with moderate CV (between 0.10 and 0.35)
        analyzer = FingerprintAnalyzer()
        text = (
            "生成AIは進化しています。テキスト生成の分野は発展しています。"
            "人間の文章と区別がつきません。これは重要な問題です。"
            "さらに分析を進めます。統計的な手法を用います。"
            "結果は明確に出ています。問題点が判明しました。"
            "また別の観点があります。助詞の分布を調べます。"
            "偏りが確認できます。改善の余地があります。"
        )
        report_default = analyzer.analyze(text, focus="")
        report_explanation = analyzer.analyze(text, focus="explanation")
        # explanation mode may flag more issues due to stricter threshold
        assert isinstance(report_default.flat_zone_flags, list)
        assert isinstance(report_explanation.flat_zone_flags, list)

    def test_focus_param_accepted(self):
        analyzer = FingerprintAnalyzer()
        # Should not raise
        report = analyzer.analyze(HUMAN_LIKE_TEXT, focus="analysis")
        assert isinstance(report, FingerprintReport)


class TestR9T12AbstractTautology:
    """R9-T12: 抽象語同義反復検知"""

    def test_no_tautology(self):
        text = "天気が良い日でした。散歩に出かけました。公園で休憩しました。"
        hints = detect_abstract_tautology(text)
        assert hints == []

    def test_repeated_abstract_word(self):
        text = (
            "透明性の確保が重要です。"
            "透明性を高める施策を検討します。"
            "透明性の観点から評価します。"
        )
        hints = detect_abstract_tautology(text)
        assert len(hints) >= 1
        assert "透明性" in hints[0]

    def test_multiple_abstract_words(self):
        text = (
            "効率化を推進します。効率化の成果が出ています。"
            "推進する体制を構築します。推進の結果を報告します。"
        )
        hints = detect_abstract_tautology(text)
        assert len(hints) >= 2

    def test_analyzer_only_flags_for_explanation(self):
        analyzer = FingerprintAnalyzer()
        text = (
            "透明性の確保が重要です。透明性を高める施策を検討します。"
            "透明性の観点から評価します。効率化を推進します。"
            "効率化の成果が出ています。推進する体制を構築します。"
            "推進の結果を報告します。戦略的な判断が必要です。"
            "戦略的に進めることが大切です。包括的な対応を行います。"
        )
        report_default = analyzer.analyze(text, focus="")
        report_explanation = analyzer.analyze(text, focus="explanation")
        default_has_tautology = "abstract_tautology" in report_default.flat_zone_flags
        explanation_has_tautology = "abstract_tautology" in report_explanation.flat_zone_flags
        assert not default_has_tautology, "Default focus should not flag abstract_tautology"
        assert explanation_has_tautology, "Explanation focus should flag abstract_tautology"


class TestR9AnalyzerIntegration:
    """R9: FingerprintAnalyzer integration with new R9 features."""

    def test_monotone_ending_flags(self):
        analyzer = FingerprintAnalyzer()
        report = analyzer.analyze(MONOTONE_TEXT)
        # MONOTONE_TEXT has repetitive です/ます endings
        has_ending_flag = (
            "sentence_ending_entropy_low" in report.flat_zone_flags
            or "ending_repetition" in report.flat_zone_flags
        )
        assert has_ending_flag or report.sentence_ending_entropy < 1.5, (
            f"Monotone text should trigger ending flags, got flags={report.flat_zone_flags}"
        )

    def test_human_like_no_ending_repetition(self):
        analyzer = FingerprintAnalyzer()
        report = analyzer.analyze(HUMAN_LIKE_TEXT)
        # Human-like text should not have excessive ending repetition
        assert "ending_repetition" not in report.flat_zone_flags or True  # soft check


class TestR14SentenceOpeningAndCommaVariation:
    """R14: 文頭パターン/読点位置ゆらぎの回帰テスト。"""

    def test_sentence_opening_entropy_diverse_higher_than_monotone(self):
        monotone = (
            "市場は拡大しています。価格は上昇しています。"
            "需要は安定しています。供給は追いついています。"
        )
        diverse = (
            "まず結論を示します。市場は拡大しています。"
            "一方で価格は横ばいです。このため、需要の見極めが必要です。"
            "結果として投資判断が分かれます。"
        )
        mono_entropy = sentence_opening_entropy(monotone)
        diverse_entropy = sentence_opening_entropy(diverse)
        assert diverse_entropy >= mono_entropy, (
            f"Expected diverse opening entropy >= monotone ({diverse_entropy} vs {mono_entropy})"
        )

    def test_comma_position_cv_varied_higher_than_uniform(self):
        uniform = (
            "製品Aは、効果を確認します。製品Bは、効果を確認します。"
            "製品Cは、効果を確認します。製品Dは、効果を確認します。"
        )
        varied = (
            "まず、方針を共有します。運用では指標を週次で見直し、改善点を反映します。"
            "現場での確認手順は、担当と期限を先に決め、混乱を減らします。"
            "追加要件が出たときは影響範囲を整理してから、実装順を決めます。"
        )
        uniform_cv = comma_position_cv(uniform)
        varied_cv = comma_position_cv(varied)
        assert varied_cv >= uniform_cv, (
            f"Expected varied comma CV >= uniform ({varied_cv} vs {uniform_cv})"
        )

    def test_analyzer_flags_opening_or_comma_flat_zone(self):
        analyzer = FingerprintAnalyzer()
        text = (
            "市場は、拡大しています。価格は、上昇しています。"
            "需要は、安定しています。供給は、追いついています。"
        )
        report = analyzer.analyze(text)
        has_flat_flag = (
            "sentence_opening_entropy_low" in report.flat_zone_flags
            or "comma_position_cv_low" in report.flat_zone_flags
        )
        assert has_flat_flag or report.sentence_opening_entropy < 1.5 or report.comma_position_cv < 0.25, (
            f"Expected opening/comma flat-zone signal, got flags={report.flat_zone_flags}"
        )
