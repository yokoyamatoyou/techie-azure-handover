# -*- coding: utf-8 -*-
"""アプリケーション全体の設定定数"""
import os
from pathlib import Path


class Config:
    """グローバル設定"""

    # === ネットワーク設定 ===
    TIMEOUT_DEFAULT: float = float(os.getenv("TIMEOUT_DEFAULT", "5"))
    TIMEOUT_LONG: float = float(os.getenv("TIMEOUT_LONG", "30"))
    TIMEOUT_SHORT: float = float(os.getenv("TIMEOUT_SHORT", "3"))
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SEO-AIO-Analyzer/2.0",
    )

    # === LLMモデル設定 ===
    MODEL_DEFAULT: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini-2025-04-14")
    # 予算優先のため、高推論モデルも mini に統一（環境変数で上書きされても運用方針として非推奨）
    MODEL_HIGH_REASONING: str = os.getenv("OPENAI_HIGH_REASONING_MODEL", "gpt-4.1-mini-2025-04-14")
    OPENAI_TIMEOUT: float = float(os.getenv("OPENAI_TIMEOUT", "60"))

    # === 推論モデル設定 (Responses API / GPT-5系) ===
    # core/application/accessibility_improvement_builder.py で先行実装済みの
    # gpt-5.4-nano + reasoning_effort=low という組み合わせを全社共通デフォルトとして
    # core/llm_responses_client.py 経由の呼び出しへ展開する。個別タスクで上書きしたい
    # 場合は呼び出し側で OPENAI_<TASK>_MODEL / OPENAI_<TASK>_REASONING_EFFORT を定義する
    # (accessibility 側の OPENAI_ACCESSIBILITY_ACTION_MODEL と同じ命名慣習)。
    REASONING_MODEL_DEFAULT: str = os.getenv("OPENAI_REASONING_MODEL", "gpt-5.4-nano")
    REASONING_EFFORT_DEFAULT: str = os.getenv("OPENAI_REASONING_EFFORT", "low")

    # === クロール設定 ===
    CRAWL_INTERVAL_SECONDS: float = float(os.getenv("CRAWL_INTERVAL_SECONDS", "1.0"))
    MAX_CRAWL_DEPTH: int = int(os.getenv("MAX_CRAWL_DEPTH", "2"))
    MAX_PAGES_PER_DOMAIN: int = int(os.getenv("MAX_PAGES_PER_DOMAIN", "50"))

    # === パス設定 ===
    BASE_DIR: Path = Path(__file__).parent.parent
    ASSETS_DIR: Path = BASE_DIR / "assets"
    DATA_DIR: Path = BASE_DIR / "data"
    POC_OUTPUT_DIR: Path = DATA_DIR / "poc_outputs"

    # === PDF設定 ===
    PDF_FONT_REGULAR: str = os.getenv("PDF_FONT_REGULAR", "NotoSansJP-Regular.ttf")
    PDF_FONT_BOLD: str = os.getenv("PDF_FONT_BOLD", "NotoSansJP-Bold.ttf")


config = Config()
