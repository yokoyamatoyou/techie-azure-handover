"""
モデル選択ロジック

モデル選択ロジック

運用方針:
- 予算優先のため、分析は gpt-4.1-mini に統一する
"""

from typing import Literal, Dict, Any
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """モデル設定"""
    name: str
    supports_web_search: bool
    context_window: int
    max_output: int
    cost_per_million_input: float  # USD
    cost_per_million_output: float  # USD
    reasoning_effort: str | None = None


class ModelSelector:
    """分析タスクに応じた最適なモデルを選択"""
    
    # モデル定義
    MODELS = {
        "gpt-4.1-mini": ModelConfig(
            name="gpt-4.1-mini",
            supports_web_search=False,
            context_window=128000,
            max_output=16384,
            cost_per_million_input=0.15,
            cost_per_million_output=0.60,
        ),
        # 互換のためキーは残すが、実体は mini に寄せる（gpt-4.1 は使用しない方針）
        "gpt-4.1": ModelConfig(
            name="gpt-4.1-mini",
            supports_web_search=False,
            context_window=128000,
            max_output=16384,
            cost_per_million_input=0.15,
            cost_per_million_output=0.60,
        ),
    }
    
    def __init__(self, default_analysis_mode: Literal["standard", "advanced"] = "standard"):
        """
        Args:
            default_analysis_mode: デフォルトの分析モード
                - "standard": 基本分析（60%のケース）
                - "advanced": 高度分析（40%のケース）
        """
        self.default_analysis_mode = default_analysis_mode
    
    def select_model(
        self, 
        task_type: Literal["aio_analysis", "web_search", "structured_validation"],
        complexity: Literal["standard", "advanced"] = None,
        user_preference: str = None
    ) -> ModelConfig:
        """
        タスクタイプと複雑度に応じてモデルを選択
        
        Args:
            task_type: タスクの種類
                - "aio_analysis": AIO分析（E-E-A-T、FAQ、構造化データ等）
                - "web_search": Web検索が必要なタスク
                - "structured_validation": 構造化データ検証のみ
            complexity: 分析の複雑度（Noneの場合はデフォルト使用）
            user_preference: ユーザーの明示的なモデル指定
        
        Returns:
            選択されたモデルの設定
        """
        # ユーザーが明示的にモデル指定した場合
        if user_preference and user_preference in self.MODELS:
            return self.MODELS[user_preference]
        
        # 複雑度が指定されていない場合はデフォルト使用
        if complexity is None:
            complexity = self.default_analysis_mode
        
        # タスクタイプ別のモデル選択
        if task_type == "web_search":
            # Web検索が必要な場合は常にsearch-preview
            return self.MODELS["gpt-4.1-mini"]
        
        elif task_type == "aio_analysis":
            if complexity == "standard":
                # 基本分析: E-E-A-T評価、FAQ検出、構造化データ検証
                return self.MODELS["gpt-4.1-mini"]
            elif complexity == "advanced":
                # 予算優先: 高度分析でも mini を使用
                return self.MODELS["gpt-4.1-mini"]
        
        elif task_type == "structured_validation":
            # 構造化タスクは高速・低コストモデル（検索不要）
            return self.MODELS["gpt-4.1-mini"]
        
        # デフォルトはsearch-preview
        return self.MODELS["gpt-4.1-mini"]
    
    def get_model_params(self, model_config: ModelConfig) -> Dict[str, Any]:
        """
        OpenAI APIに渡すパラメータを生成
        
        Args:
            model_config: モデル設定
        
        Returns:
            API呼び出し用のパラメータ辞書
        """
        params = {
            "model": model_config.name,
            "timeout": 180,
        }
        
        # 推論モデルはtemperatureとresponse_formatを除外する場合がある

        # ユーザーが「再現性」を求めているため、可能な限り決定論的な動作を強制
        # temperature=0.0でランダム性を排除
        # (APIがサポートしていない場合は無視されるかエラーになる可能性がある)
        
        # 【修正】推論モデル(o1 / o3等)はtemperatureをサポートしないため除外
        if "o1" not in model_config.name and "o3" not in model_config.name:
            params["temperature"] = 0.0
        
        # response_formatはモデルによってサポート状況が異なる
        if "o1" not in model_config.name and "o3" not in model_config.name:
             params["response_format"] = {"type": "json_object"}
        
        return params
    
    def estimate_cost(
        self, 
        model_config: ModelConfig, 
        input_tokens: int, 
        output_tokens: int
    ) -> Dict[str, float]:
        """
        コスト見積もり
        
        Args:
            model_config: モデル設定
            input_tokens: 入力トークン数
            output_tokens: 出力トークン数
        
        Returns:
            コスト情報（USD、JPY）
        """
        input_cost_usd = (input_tokens / 1_000_000) * model_config.cost_per_million_input
        output_cost_usd = (output_tokens / 1_000_000) * model_config.cost_per_million_output
        total_cost_usd = input_cost_usd + output_cost_usd
        
        # USD to JPY (仮レート: 1 USD = 150 JPY)
        USD_TO_JPY = 150.0
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost_usd": round(input_cost_usd, 6),
            "output_cost_usd": round(output_cost_usd, 6),
            "total_cost_usd": round(total_cost_usd, 6),
            "total_cost_jpy": round(total_cost_usd * USD_TO_JPY, 2),
            "model": model_config.name,
        }
    
    def get_complexity_recommendation(
        self, 
        industry: str, 
        content_length: int,
        has_technical_content: bool = False
    ) -> Literal["standard", "advanced"]:
        """
        コンテンツ特性に基づいて推奨複雑度を判定
        
        Args:
            industry: 業界
            content_length: コンテンツ長（文字数）
            has_technical_content: 技術的・専門的コンテンツか
        
        Returns:
            推奨される複雑度
        """
        # 高度分析を推奨するケース（40%想定）
        advanced_industries = ["B2B SaaS", "金融", "医療", "法律", "YMYL"]
        
        if industry in advanced_industries:
            return "advanced"
        
        if content_length > 5000 and has_technical_content:
            return "advanced"
        
        # デフォルトは標準分析（60%想定）
        return "standard"
