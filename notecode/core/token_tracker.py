"""
トークン消費追跡モジュール

API呼び出しのトークン消費とコストを記録・集計する
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import csv
import json
import logging


logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """トークン使用量の記録"""
    timestamp: str
    model: str
    task_type: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_text_tokens: int
    input_image_tokens: int
    output_text_tokens: int
    output_image_tokens: int
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
            "input_text_tokens": self.input_text_tokens,
            "input_image_tokens": self.input_image_tokens,
            "output_text_tokens": self.output_text_tokens,
            "output_image_tokens": self.output_image_tokens,
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


def _load_poc_config() -> Dict:
    """PoC設定を読み込む（SaaS移行時に削除）"""
    config_path = Path(__file__).resolve().parent.parent / "config.json"
    if not config_path.exists():
        return {"enable_token_csv": False, "token_csv_path": "logs/token_usage.csv"}
    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
        return config.get("poc", {"enable_token_csv": False, "token_csv_path": "logs/token_usage.csv"})
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.debug("Failed to load PoC config. Using defaults.", exc_info=exc)
        return {"enable_token_csv": False, "token_csv_path": "logs/token_usage.csv"}


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
        input_text_tokens: int,
        input_image_tokens: int,
        output_text_tokens: int,
        output_image_tokens: int,
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
            input_text_tokens=input_text_tokens,
            input_image_tokens=input_image_tokens,
            output_text_tokens=output_text_tokens,
            output_image_tokens=output_image_tokens,
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
            "gpt-4.1-mini-2025-04-14": {"input": 0.0004, "output": 0.0016},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4.1": {"input": 0.002, "output": 0.008},
        }
        
        costs = model_costs.get(model, {"input": 0.001, "output": 0.002})
        cost_usd = (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])
        cost_jpy = cost_usd * 150  # 概算レート
        
        usage = self.record_usage(
            model=model,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_text_tokens=input_tokens,
            input_image_tokens=0,
            output_text_tokens=output_tokens,
            output_image_tokens=0,
            cost_usd=cost_usd,
            cost_jpy=cost_jpy,
        )

        # PoC: CSV追記（SaaS移行時に削除）
        self._append_to_csv_if_enabled(usage)

        return usage

    def add_image_usage(
        self,
        model: str,
        task_type: str,
        input_text_tokens: int,
        input_image_tokens: int,
        output_text_tokens: int,
        output_image_tokens: int,
    ) -> TokenUsage:
        """画像生成のトークン使用量を記録（コスト自動計算）"""
        input_tokens = input_text_tokens + input_image_tokens
        output_tokens = output_text_tokens + output_image_tokens
        cost_usd = self._calculate_image_cost(
            model=model,
            input_text_tokens=input_text_tokens,
            input_image_tokens=input_image_tokens,
            output_text_tokens=output_text_tokens,
            output_image_tokens=output_image_tokens,
        )
        cost_jpy = cost_usd * 150

        usage = self.record_usage(
            model=model,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_text_tokens=input_text_tokens,
            input_image_tokens=input_image_tokens,
            output_text_tokens=output_text_tokens,
            output_image_tokens=output_image_tokens,
            cost_usd=cost_usd,
            cost_jpy=cost_jpy,
        )

        self._append_to_csv_if_enabled(usage)
        return usage
    
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

    # === PoC用CSV出力機能（SaaS移行時に削除） ===

    def _append_to_csv_if_enabled(self, usage: TokenUsage) -> None:
        """PoC: 有効な場合のみCSVに追記"""
        poc_config = _load_poc_config()
        if not poc_config.get("enable_token_csv", False):
            return

        csv_path = poc_config.get("token_csv_path", "logs/token_usage.csv")
        self.append_to_csv(usage, csv_path)

    def append_to_csv(self, usage: TokenUsage, filepath: str = "logs/token_usage.csv") -> None:
        """トークン使用量をCSVに追記（PoC用）"""
        path = Path(filepath)

        # ディレクトリがなければ作成
        path.parent.mkdir(parents=True, exist_ok=True)

        headers = [
            "timestamp", "model", "task_type",
            "input_tokens", "output_tokens", "total_tokens",
            "input_text_tokens", "input_image_tokens",
            "output_text_tokens", "output_image_tokens",
            "cost_usd", "cost_jpy",
        ]

        self._ensure_csv_schema(path, headers)

        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                usage.timestamp,
                usage.model,
                usage.task_type,
                usage.input_tokens,
                usage.output_tokens,
                usage.total_tokens,
                usage.input_text_tokens,
                usage.input_image_tokens,
                usage.output_text_tokens,
                usage.output_image_tokens,
                round(usage.cost_usd, 6),
                round(usage.cost_jpy, 2),
            ])

    def _ensure_csv_schema(self, path: Path, headers: List[str]) -> None:
        if not path.exists():
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            return

        try:
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f))
        except OSError as exc:
            logger.debug("Failed to read token CSV schema. Keeping existing file.", exc_info=exc)
            return

        if not rows:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            return

        old_headers = rows[0]
        if old_headers == headers:
            return

        new_rows = []
        for row in rows[1:]:
            row_map = {k: v for k, v in zip(old_headers, row)}

            if "input_text_tokens" not in row_map:
                row_map["input_text_tokens"] = row_map.get("input_tokens", "0")
            if "input_image_tokens" not in row_map:
                row_map["input_image_tokens"] = "0"
            if "output_text_tokens" not in row_map:
                row_map["output_text_tokens"] = row_map.get("output_tokens", "0")
            if "output_image_tokens" not in row_map:
                row_map["output_image_tokens"] = "0"
            if "cost_jpy" not in row_map and "cost_usd" in row_map:
                try:
                    row_map["cost_jpy"] = str(round(float(row_map.get("cost_usd", "0")) * 150, 2))
                except ValueError:
                    row_map["cost_jpy"] = ""

            new_rows.append([row_map.get(h, "") for h in headers])

        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(new_rows)
        tmp_path.replace(path)

    def _calculate_image_cost(
        self,
        model: str,
        input_text_tokens: int,
        input_image_tokens: int,
        output_text_tokens: int,
        output_image_tokens: int,
    ) -> float:
        rates = self._get_image_rates(model)
        if not rates:
            return 0.0
        return (
            (input_text_tokens / 1_000_000) * rates["input_text"]
            + (input_image_tokens / 1_000_000) * rates["input_image"]
            + (output_text_tokens / 1_000_000) * rates["output_text"]
            + (output_image_tokens / 1_000_000) * rates["output_image"]
        )

    def _get_image_rates(self, model: str) -> Optional[Dict[str, float]]:
        name = (model or "").lower()
        if name.startswith("gpt-image-2"):
            return {
                "input_text": 5.0,
                "input_image": 8.0,
                "output_text": 0.0,
                "output_image": 30.0,
            }
        if name.startswith("gpt-image-1.5"):
            return {
                "input_text": 5.0,
                "input_image": 8.0,
                "output_text": 10.0,
                "output_image": 32.0,
            }
        return None
