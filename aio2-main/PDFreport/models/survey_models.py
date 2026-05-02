"""Pydantic models for survey analysis results.

This module contains all data models used for structured analysis results.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, validator, model_validator


class SurveyResponseAnalysis(BaseModel):
    """Structured insight extracted from a single survey response.

    Attributes:
        sentiment: Overall sentiment classified into four categories.
        key_topics: List of key topics mentioned in the response.
        verbatim_quote: Representative sentence from the original text.
        actionable_insight: Whether the response includes actionable feedback.
    """

    sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
        description="回答全体のセンチメント（感情極性）を4つのカテゴリのいずれかで判定します。"
    )
    key_topics: List[str] = Field(
        description="回答で言及されている主要なトピックやテーマをリスト形式で抽出します。例：['価格', 'デザイン', 'サポート体制']",
        default=[],
    )
    verbatim_quote: str = Field(
        description="分析内容を最もよく表している、原文からの代表的な一文を抜き出します。",
        default=""
    )
    actionable_insight: bool = Field(
        description="この回答に、改善に繋がる具体的で実行可能な提案が含まれている場合はTrue、そうでなければFalseを返します。",
        default=False
    )


class ModerationCategories(BaseModel):
    """Flags indicating whether each moderation category was triggered."""

    hate: bool = Field(description="ヘイトコンテンツ")
    hate_threatening: bool = Field(description="脅迫的なヘイトコンテンツ")
    self_harm: bool = Field(description="自傷行為")
    sexual: bool = Field(description="性的コンテンツ")
    sexual_minors: bool = Field(description="未成年者への性的コンテンツ")
    violence: bool = Field(description="暴力")
    violence_graphic: bool = Field(description="グラフィックな暴力コンテンツ")


class ModerationScores(BaseModel):
    """Score values for each moderation category."""

    hate: float = Field(description="ヘイトスコア")
    hate_threatening: float = Field(description="脅迫的なヘイトスコア")
    self_harm: float = Field(description="自傷行為スコア")
    sexual: float = Field(description="性的コンテンツスコア")
    sexual_minors: float = Field(description="未成年者への性的コンテンツスコア")
    violence: float = Field(description="暴力スコア")
    violence_graphic: float = Field(description="グラフィックな暴力スコア")


class ModerationResult(BaseModel):
    """Moderation outcome returned by the OpenAI API."""

    flagged: bool = Field(description="フラグが立てられたか")
    categories: ModerationCategories
    category_scores: ModerationScores
    
    # 認知負荷軽減のための集約情報
    @property
    def risk_level(self) -> str:
        """リスクレベルを計算（高/中/低/なし）"""
        if not self.flagged:
            return "なし"
        
        # 各カテゴリの最大スコアを取得
        max_score = max([
            self.category_scores.hate,
            self.category_scores.hate_threatening,
            self.category_scores.self_harm,
            self.category_scores.sexual,
            self.category_scores.sexual_minors,
            self.category_scores.violence,
            self.category_scores.violence_graphic
        ])
        
        if max_score >= 0.8:
            return "高"
        elif max_score >= 0.5:
            return "中"
        elif max_score >= 0.3:
            return "低"
        else:
            return "なし"
    
    @property
    def main_concerns(self) -> list[str]:
        """主要な懸念事項を返す（最大2項目、0.3以上）"""
        concerns = []
        threshold = 0.3
        
        # スコアとカテゴリ名のマッピング
        scores = {
            "hate": self.category_scores.hate,
            "hate_threatening": self.category_scores.hate_threatening,
            "self_harm": self.category_scores.self_harm,
            "sexual": self.category_scores.sexual,
            "sexual_minors": self.category_scores.sexual_minors,
            "violence": self.category_scores.violence,
            "violence_graphic": self.category_scores.violence_graphic
        }
        
        # 日本語カテゴリ名マッピング
        jp_names = {
            "hate": "ヘイト",
            "hate_threatening": "脅迫的ヘイト",
            "self_harm": "自傷行為",
            "sexual": "性的コンテンツ",
            "sexual_minors": "未成年者への性的コンテンツ",
            "violence": "暴力",
            "violence_graphic": "グラフィック暴力"
        }
        
        # 0.3以上のカテゴリをスコア順でソート
        filtered_scores = {k: v for k, v in scores.items() if v >= threshold}
        sorted_concerns = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 最大2項目まで返す
        for category, score in sorted_concerns[:2]:
            concerns.append(jp_names.get(category, category))
        
        return concerns


class EmotionScores(BaseModel):
    """Basic emotion scores for Japanese text analysis (6 primary emotions)."""

    # 基本感情（一次感情6つ）- 0-5の6段階スケール
    joy: int = Field(ge=0, le=5, description="喜びのスコア (0-5の6段階)")
    sadness: int = Field(ge=0, le=5, description="悲しみのスコア (0-5の6段階)")
    fear: int = Field(ge=0, le=5, description="恐れのスコア (0-5の6段階)")
    surprise: int = Field(ge=0, le=5, description="驚きのスコア (0-5の6段階)")
    anger: int = Field(ge=0, le=5, description="怒りのスコア (0-5の6段階)")
    disgust: int = Field(ge=0, le=5, description="嫌悪のスコア (0-5の6段階)")
    
    reason: str = Field(description="感情全体の理由")
    
    @validator('joy', 'sadness', 'fear', 'surprise', 'anger', 'disgust')
    def validate_emotion_scores(cls, v):
        """感情スコアの厳密なバリデーション"""
        if not isinstance(v, int):
            raise ValueError(f"Emotion score must be integer, got {type(v)}: {v}")
        if v < 0 or v > 5:
            raise ValueError(f"Emotion score must be between 0-5, got {v}")
        return v
    
    @model_validator(mode='after')
    def validate_emotion_scale(self):
        """感情スコア全体のバリデーション"""
        emotion_fields = ['joy', 'sadness', 'fear', 'surprise', 'anger', 'disgust']
        for field in emotion_fields:
            score = getattr(self, field, None)
            if score is not None:
                if not isinstance(score, int):
                    raise ValueError(f"{field} must be integer, got {type(score)}: {score}")
                if score < 0 or score > 5:
                    raise ValueError(f"{field} must be between 0-5, got {score}")
        return self
    
    # 日本語表示用の感情名マッピング
    @property
    def emotion_names_jp(self) -> dict:
        return {
            "joy": "喜び",
            "sadness": "悲しみ", 
            "fear": "恐れ",
            "surprise": "驚き",
            "anger": "怒り",
            "disgust": "嫌悪"
        }
    
    # 感情の分類（ポジティブ/ネガティブ/ニュートラル）
    @property
    def emotion_categories(self) -> dict:
        return {
            "positive": ["joy", "surprise"],
            "negative": ["sadness", "anger", "fear", "disgust"],
            "neutral": []
        }
    
    # WordCloud用の感情分類（文脈依存）
    @property
    def wordcloud_categories(self) -> dict:
        return {
            "positive": ["joy", "surprise"],
            "negative": ["sadness", "anger", "fear", "disgust"]
        }


class ComprehensiveAnalysisResult(BaseModel):
    """Combined results from survey, moderation and emotion analyses."""

    survey_analysis: SurveyResponseAnalysis
    moderation_result: ModerationResult
    emotion_scores: EmotionScores


class DataQualityWarning(BaseModel):
    """データ品質に関する警告情報。"""
    
    sample_size: int = Field(description="分析対象データ件数")
    quality_level: Literal["high", "medium", "low"] = Field(description="データ品質レベル")
    warning_message: str = Field(description="品質に関する警告メッセージ")
    recommendations: List[str] = Field(description="データ品質向上のための推奨事項")


class KeyInsight(BaseModel):
    """注目すべき重要なインサイト。"""
    
    title: str = Field(description="インサイトのタイトル")
    description: str = Field(description="インサイトの詳細説明")
    impact_level: Literal["high", "medium", "low"] = Field(description="ビジネスインパクトレベル")
    data_evidence: str = Field(description="データに基づく根拠")
    recommended_action: str = Field(description="推奨されるアクション")


class ReportCommentary(BaseModel):
    """LLMによって生成されたレポートの解説文。"""

    summary_text: str = Field(
        description="分析結果全体を3つのポイントで要約した総括文（400-600文字）。"
    )
    comprehensive_analysis: Optional[str] = Field(
        default=None,
        description="アンケート全体の総合分析（強み・弱み・機会・脅威）を詳細に解説（800-1200文字）。省略可。"
    )
    action_items: List[str] = Field(
        description="分析結果から考えられる具体的なネクストアクションの提案リスト。5つ提案すること。"
    )
    sentiment_commentary: str = Field(
        description="感情分析の円グラフから読み取れるインサイトや注目点を解説する文章（400-600文字）。"
    )
    topics_commentary: str = Field(
        description="主要トピックの棒グラフから読み取れるインサイトや注目点を解説する文章（400-600文字）。"
    )
    marketing_perspective: str = Field(
        description="マーケティング目線のレポート本文（800-1200文字）。"
    )
    user_perspective: str = Field(
        description="ユーザー目線のレポート本文（800-1200文字）。"
    )
    consultant_perspective: str = Field(
        description="コンサルタント目線のレポート本文（800-1200文字）。"
    )
    data_quality_warning: Optional[DataQualityWarning] = Field(
        default=None,
        description="データ品質に関する警告情報。省略可。"
    )
    comprehensive_advice: Optional[str] = Field(
        default=None,
        description="アクセンチュアコンサルタントAIによる総合アドバイス（1000-1500文字）。省略可。"
    )
