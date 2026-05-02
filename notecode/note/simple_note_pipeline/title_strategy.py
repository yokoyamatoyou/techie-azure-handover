"""Article-type title strategy helpers for the simple note pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class TitleStrategy:
    pattern: str
    avoid: str


_DEFAULT_TITLE_STRATEGY = TitleStrategy(
    pattern="問い+判断軸。",
    avoid="超要約を避ける。",
)

_TITLE_STRATEGIES: dict[str, TitleStrategy] = {
    "announcement": TitleStrategy(
        pattern="対象 + 変更/開始 + 日付/範囲。",
        avoid="誇張・未確認の日時や範囲を足さない。",
    ),
    "daily_story": TitleStrategy(
        pattern="小さな場面 + 気づき。",
        avoid="教訓だけ・一般論だけにしない。",
    ),
    "explanatory_article": TitleStrategy(
        pattern="問い+軸。",
        avoid="断定を避ける。",
    ),
    "comparative_review": TitleStrategy(
        pattern="条件 + 選び方/見分け方。",
        avoid="ランキング・最強・唯一のおすすめを避ける。",
    ),
    "case_study": TitleStrategy(
        pattern="変化前後 + 学び。",
        avoid="成功談だけ・効果誇張にしない。",
    ),
    "branding": TitleStrategy(
        pattern="読者の迷い + 価値の文脈。",
        avoid="理念だけ・強み列挙だけにしない。",
    ),
    "industry_analysis": TitleStrategy(
        pattern="変化の論点 + 判断条件。",
        avoid="トレンド感だけ・根拠なし予測を避ける。",
    ),
}

_SEMANTIC_TITLE_STRATEGIES: dict[str, TitleStrategy] = {
    "company_introduction": TitleStrategy(
        pattern="事業内容 + 扱う領域 + 会社の特徴。",
        avoid="創業・沿革だけ、理念だけ、強み列挙だけにしない。",
    ),
    "product_introduction": TitleStrategy(
        pattern="利用場面 + 負担 + 選定理由。",
        avoid="機能列挙だけ・万能感を避ける。",
    ),
}


def resolve_title_strategy(article_type: str, semantic_key: str = "") -> TitleStrategy:
    semantic = str(semantic_key or "").strip().lower()
    if semantic in _SEMANTIC_TITLE_STRATEGIES:
        return _SEMANTIC_TITLE_STRATEGIES[semantic]
    article = str(article_type or "").strip().lower()
    return _TITLE_STRATEGIES.get(article, _DEFAULT_TITLE_STRATEGY)


def build_title_strategy_lines(contract: Mapping[str, Any]) -> list[str]:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    strategy = resolve_title_strategy(article_type, semantic_key)
    return [
        f"- タイトル型: {strategy.pattern} {strategy.avoid}",
    ]
