"""Human Resonance Pipeline - 統合実行エンジン

全Phaseを統合し、一貫したパイプライン処理を提供するモジュール。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .phase0_persona import Phase0Persona, Persona, create_persona_from_context
from .phase1_empathy import Phase1Empathy, EmpathyScore
from .phase2_curiosity import Phase2Curiosity, CuriosityScore
from .phase3_humanity import Phase3Humanity, HumanityScore
from .phase4_rhythm import Phase4Rhythm, RhythmScore
from .phase5_editor import Phase5Editor, EditorIssue
from .phase6_legal import Phase6Legal, LegalCheckResult, RiskLevel
from .phase7_sanitize import Phase7Sanitize, SanitizeResult
from .phase8_platform import Phase8Platform, Platform


# 文体プロファイル定義
# 各プロファイルは Phase3/4/5 の挙動を調整するパラメータを持つ
STYLE_PROFILES: Dict[str, Dict[str, Any]] = {
    "balanced": {
        # デフォルト: 既存挙動を維持
        "description": "バランスの取れた文体",
        "humanity_intensity": 0.5,
        "humanity_target": 0.35,
        "rhythm_target": 0.4,
        "phrase_probability": 0.75,
        "sentence_variance_target": 0.4,
        "casual_break_weight": 0.25,
    },
    "casual": {
        # カジュアル: 親しみやすく、短文多め
        "description": "カジュアルで親しみやすい文体",
        "humanity_intensity": 0.7,
        "humanity_target": 0.45,
        "rhythm_target": 0.5,
        "phrase_probability": 0.8,
        "sentence_variance_target": 0.5,
        "casual_break_weight": 0.35,
    },
    "formal": {
        # フォーマル: 落ち着いた、長文も許容
        "description": "フォーマルで落ち着いた文体",
        "humanity_intensity": 0.3,
        "humanity_target": 0.25,
        "rhythm_target": 0.35,
        "phrase_probability": 0.3,
        "sentence_variance_target": 0.3,
        "casual_break_weight": 0.15,
    },
}


@dataclass
class PipelineConfig:
    """パイプライン設定"""

    # Phase有効化フラグ
    enable_persona: bool = True
    enable_empathy: bool = True
    enable_curiosity: bool = True
    enable_humanity: bool = True
    enable_rhythm: bool = True
    enable_editor: bool = True
    enable_legal: bool = True
    enable_sanitize: bool = True
    enable_platform: bool = True

    # 各Phaseの目標スコア
    empathy_target: float = 0.4
    curiosity_target: float = 0.4
    humanity_target: float = 0.35
    rhythm_target: float = 0.4

    # 人間味の強度（Phase3）
    humanity_intensity: float = 0.5

    # Phase5 言い回しの揺らぎ（段落あたり最大2回・確率・閾値）
    phrase_max_per_paragraph: int = 2
    phrase_probability: float = 0.75
    phrase_min_occurrences: int = 2

    pronoun_reduction_ratio: float = 0.5
    pronoun_reduction_min_count: int = 4

    # LLM使用フラグ
    use_llm_for_legal: bool = False
    use_llm_for_editor: bool = False

    # プラットフォーム
    platform: str = "note"  # "note" or "linkedin"

    # 文体プロファイル（balanced / casual / formal）
    style_profile: str = "balanced"


@dataclass
class PipelineResult:
    """パイプライン処理結果"""

    text: str
    original_text: str
    platform: str
    phases_applied: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    issues_found: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    phase_effect_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)


def _measure_phase_effect(before: str, after: str) -> Dict[str, Any]:
    """Phase前後のテキスト差分を計測する（observe-only）。

    Returns:
        char_diff: 文字数変化量（正=増、負=減）
        char_ratio: 文字数変化率（|diff| / before_len）
        sentence_diff: 文数変化量
        vocab_diff: ユニーク語彙数変化量
    """
    before_len = len(before)
    after_len = len(after)
    char_diff = after_len - before_len
    char_ratio = abs(char_diff) / before_len if before_len > 0 else 0.0

    _split_re = re.compile(r"(?<=[。！？])\s*")
    before_sents = [s for s in _split_re.split(before) if s.strip()]
    after_sents = [s for s in _split_re.split(after) if s.strip()]
    sentence_diff = len(after_sents) - len(before_sents)

    _word_re = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\w]{2,}")
    before_vocab = set(_word_re.findall(before))
    after_vocab = set(_word_re.findall(after))
    vocab_diff = len(after_vocab) - len(before_vocab)

    return {
        "char_diff": char_diff,
        "char_ratio": round(char_ratio, 4),
        "sentence_diff": sentence_diff,
        "vocab_diff": vocab_diff,
    }


class HumanResonancePipeline:
    """Human Resonance パイプライン"""

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        llm_client: Optional[Any] = None,
    ):
        """
        Args:
            config: パイプライン設定
            llm_client: LLMクライアント（オプション）
        """
        self.config = config or PipelineConfig()
        self.llm = llm_client

        # 各Phaseを初期化
        self._init_phases()

    def _init_phases(self) -> None:
        """各Phaseを初期化（style_profileに応じてパラメータ調整）"""
        # プロファイルからパラメータを取得
        profile = STYLE_PROFILES.get(self.config.style_profile, STYLE_PROFILES["balanced"])

        # 明示的に設定されていない場合はプロファイルの値を使用
        humanity_intensity = self.config.humanity_intensity
        phrase_probability = self.config.phrase_probability

        # プロファイルが balanced 以外の場合、プロファイルの値で上書き
        if self.config.style_profile != "balanced":
            humanity_intensity = profile.get("humanity_intensity", humanity_intensity)
            phrase_probability = profile.get("phrase_probability", phrase_probability)

        self.phase0 = None  # Personaは process 時に設定
        self.phase1 = Phase1Empathy()
        self.phase2 = Phase2Curiosity()
        self.phase3 = Phase3Humanity(intensity=humanity_intensity)
        self.phase4 = Phase4Rhythm()
        self.phase5 = Phase5Editor(
            llm_client=self.llm if self.config.use_llm_for_editor else None,
            phrase_max_per_paragraph=self.config.phrase_max_per_paragraph,
            phrase_probability=phrase_probability,
            phrase_min_occurrences=self.config.phrase_min_occurrences,
            pronoun_reduction_ratio=self.config.pronoun_reduction_ratio,
            pronoun_reduction_min_count=self.config.pronoun_reduction_min_count,
            style_profile=self.config.style_profile,
        )
        self.phase6 = Phase6Legal(llm_client=self.llm if self.config.use_llm_for_legal else None)
        self.phase7 = Phase7Sanitize()

        # Phase8はプラットフォームに応じて設定
        platform = Platform.NOTE if self.config.platform == "note" else Platform.LINKEDIN
        self.phase8 = Phase8Platform(platform=platform)

        # プロファイル適用済みパラメータを保存（デバッグ用）
        self._applied_profile = profile

    def process(
        self,
        text: str,
        persona: Optional[Persona] = None,
        perspective: str = "blogger",
        source_text: Optional[str] = None,
        hashtags: Optional[str] = None,
    ) -> PipelineResult:
        """テキストをパイプライン処理する

        Args:
            text: 入力テキスト
            persona: ペルソナ設定（Noneの場合はperspectiveから生成）
            perspective: 視点タイプ（persona未指定時に使用）
            source_text: ファクトチェック用ソーステキスト
            hashtags: ハッシュタグ

        Returns:
            処理結果
        """
        result = PipelineResult(
            text=text,
            original_text=text,
            platform=self.config.platform,
        )

        current_text = text

        # Phase 0: Persona Lock
        if self.config.enable_persona:
            if persona:
                self.phase0 = Phase0Persona(persona)
            else:
                self.phase0 = Phase0Persona.from_perspective(perspective)

            # Phase1で使うpronounを設定
            self.phase1.pronoun = self.phase0.persona.pronoun

            current_text = self.phase0.process(current_text)
            result.phases_applied.append("phase0_persona")

        # Phase 1: Empathy
        if self.config.enable_empathy:
            _before_text = current_text
            score_before = self.phase1.analyze(current_text)
            current_text = self.phase1.process(current_text, self.config.empathy_target)
            score_after = self.phase1.analyze(current_text)

            result.scores["empathy_before"] = score_before.total
            result.scores["empathy_after"] = score_after.total
            result.phases_applied.append("phase1_empathy")
            result.phase_effect_metrics["phase1_empathy"] = _measure_phase_effect(_before_text, current_text)

        # Phase 2: Curiosity
        if self.config.enable_curiosity:
            _before_text = current_text
            score_before = self.phase2.analyze(current_text)
            current_text = self.phase2.process(current_text, self.config.curiosity_target)
            score_after = self.phase2.analyze(current_text)

            result.scores["curiosity_before"] = score_before.total
            result.scores["curiosity_after"] = score_after.total
            result.phases_applied.append("phase2_curiosity")
            result.phase_effect_metrics["phase2_curiosity"] = _measure_phase_effect(_before_text, current_text)

        # Phase 3: Humanity（プロファイルに応じた目標スコア）
        if self.config.enable_humanity:
            _before_text = current_text
            profile = self._applied_profile if hasattr(self, "_applied_profile") else STYLE_PROFILES["balanced"]
            humanity_target = profile.get("humanity_target", self.config.humanity_target)

            score_before = self.phase3.analyze(current_text)
            current_text = self.phase3.process(current_text, humanity_target)
            score_after = self.phase3.analyze(current_text)

            result.scores["humanity_before"] = score_before.total
            result.scores["humanity_after"] = score_after.total
            result.phases_applied.append("phase3_humanity")
            result.phase_effect_metrics["phase3_humanity"] = _measure_phase_effect(_before_text, current_text)

        # Phase 4: Rhythm（プロファイルに応じた目標スコア）
        if self.config.enable_rhythm:
            _before_text = current_text
            profile = self._applied_profile if hasattr(self, "_applied_profile") else STYLE_PROFILES["balanced"]
            rhythm_target = profile.get("rhythm_target", self.config.rhythm_target)

            score_before = self.phase4.analyze(current_text)
            current_text = self.phase4.process(current_text, rhythm_target)
            score_after = self.phase4.analyze(current_text)

            result.scores["rhythm_before"] = score_before.total
            result.scores["rhythm_after"] = score_after.total
            result.phases_applied.append("phase4_rhythm")
            result.phase_effect_metrics["phase4_rhythm"] = _measure_phase_effect(_before_text, current_text)

        # Phase 5: Editor
        if self.config.enable_editor:
            _before_text = current_text
            expected_pronoun = self.phase0.persona.pronoun if self.phase0 else None
            issues_before = self.phase5.analyze_editorial_issues(current_text, expected_pronoun)

            current_text = self.phase5.process(
                current_text,
                source_text=source_text,
                expected_pronoun=expected_pronoun,
            )

            result.issues_found["editorial"] = len(issues_before)
            result.phases_applied.append("phase5_editor")
            result.phase_effect_metrics["phase5_editor"] = _measure_phase_effect(_before_text, current_text)

        # Phase 6: Legal
        if self.config.enable_legal:
            _before_text = current_text
            legal_result = self.phase6.precheck(current_text)
            current_text = self.phase6.process(
                current_text,
                use_llm=self.config.use_llm_for_legal,
            )

            result.issues_found["legal"] = len(legal_result.issues)
            result.metadata["legal_risk_level"] = legal_result.risk_level.value
            result.phases_applied.append("phase6_legal")
            result.phase_effect_metrics["phase6_legal"] = _measure_phase_effect(_before_text, current_text)

        # Phase 7: Sanitize
        if self.config.enable_sanitize:
            _before_text = current_text
            sanitize_result = self.phase7.analyze(current_text)
            current_text = self.phase7.process(current_text)

            result.issues_found["sanitize"] = sanitize_result.changes_made
            result.phases_applied.append("phase7_sanitize")
            result.phase_effect_metrics["phase7_sanitize"] = _measure_phase_effect(_before_text, current_text)

        # Phase 8: Platform
        if self.config.enable_platform:
            current_text = self.phase8.process(current_text, hashtags=hashtags)
            result.phases_applied.append("phase8_platform")

        result.text = current_text
        return result

    def analyze_only(self, text: str) -> Dict[str, Any]:
        """テキストを分析のみ行う（変更は加えない）"""
        analysis = {
            "empathy": self.phase1.analyze(text).__dict__,
            "curiosity": self.phase2.analyze(text).__dict__,
            "humanity": self.phase3.analyze(text).__dict__,
            "rhythm": self.phase4.analyze(text).__dict__,
            "editorial": self.phase5.get_editorial_summary(text),
            "legal": self.phase6.analyze(text),
            "sanitize": self.phase7.analyze(text).__dict__,
            "platform": self.phase8.analyze(text),
        }

        # 総合スコアを計算
        total_score = (
            analysis["empathy"]["total"]
            + analysis["curiosity"]["total"]
            + analysis["humanity"]["total"]
            + analysis["rhythm"]["total"]
        ) / 4

        analysis["total_resonance_score"] = round(total_score, 3)

        return analysis

    def get_improvement_suggestions(self, text: str) -> List[str]:
        """テキストの改善提案を取得"""
        suggestions = []

        suggestions.extend(self.phase1.get_improvement_suggestions(text))
        suggestions.extend(self.phase2.get_improvement_suggestions(text))
        suggestions.extend(self.phase3.get_improvement_suggestions(text))
        suggestions.extend(self.phase4.get_improvement_suggestions(text))

        return suggestions

    def set_platform(self, platform: str) -> None:
        """プラットフォームを変更"""
        self.config.platform = platform
        platform_enum = Platform.NOTE if platform == "note" else Platform.LINKEDIN
        self.phase8 = Phase8Platform(platform=platform_enum)


def process_text(
    text: str,
    platform: str = "note",
    perspective: str = "blogger",
    hashtags: Optional[str] = None,
    llm_client: Optional[Any] = None,
) -> str:
    """テキストを処理するシンプルなヘルパー関数"""
    config = PipelineConfig(platform=platform)
    pipeline = HumanResonancePipeline(config=config, llm_client=llm_client)

    result = pipeline.process(
        text,
        perspective=perspective,
        hashtags=hashtags,
    )

    return result.text


def analyze_text(text: str) -> Dict[str, Any]:
    """テキストを分析するヘルパー関数"""
    pipeline = HumanResonancePipeline()
    return pipeline.analyze_only(text)
