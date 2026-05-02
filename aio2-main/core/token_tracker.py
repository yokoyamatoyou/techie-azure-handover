"""
トークン消費追跡モジュール

API呼び出しのトークン消費とコストを記録・集計する
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class TokenUsage:
    """トークン使用量の記録"""
    timestamp: str
    model: str
    task_type: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    cost_jpy: float
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "task_type": self.task_type,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "cost_jpy": self.cost_jpy,
        }


@dataclass
class TokenTrackerSummary:
    """トークン使用量のサマリー"""
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_cost_jpy: float = 0.0
    by_model: Dict[str, Dict] = field(default_factory=dict)
    by_task_type: Dict[str, Dict] = field(default_factory=dict)
    usage_history: List[TokenUsage] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_cost_jpy": round(self.total_cost_jpy, 2),
            "by_model": self.by_model,
            "by_task_type": self.by_task_type,
            "usage_history": [u.to_dict() for u in self.usage_history],
        }


class TokenTracker:
    """トークン消費を追跡・集計するクラス"""
    
    def __init__(self):
        self.usage_history: List[TokenUsage] = []
    
    def record_usage(
        self,
        model: str,
        task_type: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        cost_jpy: float,
    ) -> TokenUsage:
        """
        トークン使用量を記録
        
        Args:
            model: 使用したモデル名
            task_type: タスクタイプ
            input_tokens: 入力トークン数
            output_tokens: 出力トークン数
            cost_usd: コスト（USD）
            cost_jpy: コスト（JPY）
        
        Returns:
            記録されたTokenUsageオブジェクト
        """
        usage = TokenUsage(
            timestamp=datetime.now().isoformat(),
            model=model,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost_usd,
            cost_jpy=cost_jpy,
        )
        self.usage_history.append(usage)
        return usage
    
    def add_usage(self, model: str, input_tokens: int, output_tokens: int, task_type: str = "deep_recommendations") -> TokenUsage:
        """
        シンプルなトークン使用量記録（コスト自動計算）
        
        Args:
            model: モデル名
            input_tokens: 入力トークン数
            output_tokens: 出力トークン数
            task_type: タスクタイプ
        
        Returns:
            TokenUsageオブジェクト
        """
        # モデル別のコスト概算（USD per 1K tokens）
        model_costs = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4.1-mini": {"input": 0.0004, "output": 0.0016},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4.1": {"input": 0.002, "output": 0.008},
        }
        
        costs = model_costs.get(model, {"input": 0.001, "output": 0.002})
        cost_usd = (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])
        cost_jpy = cost_usd * 150  # 概算レート
        
        return self.record_usage(
            model=model,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            cost_jpy=cost_jpy,
        )
    
    def get_summary(self) -> TokenTrackerSummary:
        """
        トークン使用量のサマリーを取得
        
        Returns:
            TokenTrackerSummaryオブジェクト
        """
        summary = TokenTrackerSummary()
        
        for usage in self.usage_history:
            # 全体集計
            summary.total_requests += 1
            summary.total_input_tokens += usage.input_tokens
            summary.total_output_tokens += usage.output_tokens
            summary.total_tokens += usage.total_tokens
            summary.total_cost_usd += usage.cost_usd
            summary.total_cost_jpy += usage.cost_jpy
            
            # モデル別集計
            if usage.model not in summary.by_model:
                summary.by_model[usage.model] = {
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "cost_jpy": 0.0,
                }
            summary.by_model[usage.model]["requests"] += 1
            summary.by_model[usage.model]["input_tokens"] += usage.input_tokens
            summary.by_model[usage.model]["output_tokens"] += usage.output_tokens
            summary.by_model[usage.model]["total_tokens"] += usage.total_tokens
            summary.by_model[usage.model]["cost_usd"] += usage.cost_usd
            summary.by_model[usage.model]["cost_jpy"] += usage.cost_jpy
            
            # タスクタイプ別集計
            if usage.task_type not in summary.by_task_type:
                summary.by_task_type[usage.task_type] = {
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "cost_jpy": 0.0,
                }
            summary.by_task_type[usage.task_type]["requests"] += 1
            summary.by_task_type[usage.task_type]["input_tokens"] += usage.input_tokens
            summary.by_task_type[usage.task_type]["output_tokens"] += usage.output_tokens
            summary.by_task_type[usage.task_type]["total_tokens"] += usage.total_tokens
            summary.by_task_type[usage.task_type]["cost_usd"] += usage.cost_usd
            summary.by_task_type[usage.task_type]["cost_jpy"] += usage.cost_jpy
        
        # 履歴も含める
        summary.usage_history = self.usage_history
        
        # 金額を丸める
        for model_stats in summary.by_model.values():
            model_stats["cost_usd"] = round(model_stats["cost_usd"], 6)
            model_stats["cost_jpy"] = round(model_stats["cost_jpy"], 2)
        
        for task_stats in summary.by_task_type.values():
            task_stats["cost_usd"] = round(task_stats["cost_usd"], 6)
            task_stats["cost_jpy"] = round(task_stats["cost_jpy"], 2)
        
        return summary
    
    def reset(self):
        """記録をリセット"""
        self.usage_history.clear()
    
    def export_to_json(self, filepath: str):
        """JSON形式でエクスポート"""
        summary = self.get_summary()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary.to_dict(), f, ensure_ascii=False, indent=2)
    
    def get_latest_usage(self) -> Optional[TokenUsage]:
        """最新のトークン使用量を取得"""
        if self.usage_history:
            return self.usage_history[-1]
        return None
