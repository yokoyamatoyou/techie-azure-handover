"""ScoringEngine: intent係数αと業界重みを適用し、統合スコアを算出するユーティリティ."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Intent係数α: α = SEO比率、(1-α) = AIO比率
# 数値自体は official primary source の係数ではなく、内部ヒューリスティックとして維持する。
INTENT_ALPHA = {
    "transactional": 0.7,   # 購買意図: SEO70% / AIO30%（旧値0.8）
    "informational": 0.2,   # 情報収集: SEO20% / AIO80%（旧値0.3）
    "navigational":  0.8,   # 指名検索: SEO80% / AIO20%（旧値1.0）
    "unknown":       0.5,   # 不明: 50:50
}

INDUSTRY_PROFILES = {
    "b2b saas": {"aio_boost": 1.2, "seo_boost": 1.0},
    "real estate": {"aio_boost": 1.1, "seo_boost": 1.1},
    "ecommerce": {"aio_boost": 1.0, "seo_boost": 1.3},
}

# YMYL業界キーワード（日本語）: 数値乗算ではなく注意喚起の判定に使う
YMYL_KEYWORDS = ["医療", "健康", "医薬", "金融", "保険", "投資", "法律", "弁護", "裁判"]

URL_TYPE_WEIGHTS = {
    "企業": {"trust": 0.3, "findability": 0.2, "a11y": 0.2, "seo": 0.15, "cwv": 0.1, "ui": 0.05},
    "EC": {"purchase": 0.3, "compliance": 0.25, "seo": 0.2, "cwv": 0.15, "a11y": 0.1},
    "企業（EC機能あり）": {"trust": 0.2, "purchase": 0.2, "compliance": 0.2, "seo": 0.2, "cwv": 0.1, "a11y": 0.1},
    "その他": {"seo": 0.25, "a11y": 0.25, "cwv": 0.2, "ui": 0.2, "trust": 0.1},
}

URL_TYPE_PRIORITY_LABELS = {
    "trust": "信頼性",
    "findability": "見つけやすさ",
    "a11y": "アクセシビリティ",
    "seo": "SEO",
    "cwv": "CWV",
    "ui": "UI",
    "purchase": "購入導線",
    "compliance": "法令対応",
}


@dataclass
class ScoreContext:
    intent: str = "unknown"
    industry: Optional[str] = None
    seo_weight: Optional[float] = None
    aio_weight: Optional[float] = None
    url_type: Optional[str] = None


class ScoringEngine:
    """統合スコア計算のハブ."""

    def __init__(self):
        self.intent_alpha = INTENT_ALPHA
        self.industry_profiles = INDUSTRY_PROFILES
        self.url_type_weights = URL_TYPE_WEIGHTS

    def _get_alpha(self, intent: str) -> float:
        return self.intent_alpha.get(intent or "unknown", 0.5)

    def _is_ymyl_industry(self, industry: Optional[str]) -> bool:
        text = str(industry or "")
        return any(keyword in text for keyword in YMYL_KEYWORDS)

    def _apply_industry_boost(
        self,
        seo_score: float,
        aio_score: float,
        industry: Optional[str],
        eeat_score: float = 0.0,
    ) -> tuple[float, float]:
        if not industry:
            return seo_score, aio_score
        key = industry.lower()

        # YMYL は数値乗算をやめ、注意喚起のみ行う
        if self._is_ymyl_industry(industry):
            return seo_score, aio_score

        # 通常業界（既存ロジック）
        profile = None
        for cand, cfg in self.industry_profiles.items():
            if cand in key:
                profile = cfg
                break
        if not profile:
            return seo_score, aio_score
        return seo_score * profile.get("seo_boost", 1.0), aio_score * profile.get("aio_boost", 1.0)

    def _apply_penalties(self, score: float, flags: Dict[str, Any]) -> tuple[float, List[str]]:
        warnings: List[str] = []
        penalized = score
        if flags.get("parasitic_content_flag"):
            penalized *= 0.85
            warnings.append("ドメインテーマと内容の乖離が大きいため軽減点（内部ヒューリスティック 0.85x）")
        return penalized, warnings

    def integrate(
        self,
        seo_results: Dict[str, Any],
        aio_results: Dict[str, Any],
        ctx: ScoreContext,
    ) -> Dict[str, Any]:
        """SEO/AIOスコアを統合して返す。"""
        seo_score = float(seo_results.get("total_score", 0.0))
        aio_score = float(aio_results.get("total_score", 0.0))

        # intent係数α
        alpha = self._get_alpha(ctx.intent)

        # P02 E-E-A-Tスコア取得
        eeat_score = float((aio_results.get("scores", {}).get("eeat") or {}).get("score", 0.0))

        # 業界ブースト（YMYL数値補正は適用しない）
        seo_score, aio_score = self._apply_industry_boost(seo_score, aio_score, ctx.industry, eeat_score)

        # ペナルティ / 注意喚起フラグ判定
        seo_eeat = seo_results.get("eeat", {}) or {}
        is_ymyl_context = bool(seo_eeat.get("is_ymyl")) or self._is_ymyl_industry(ctx.industry)
        flags = {
            "ymyl_attention_needed": is_ymyl_context and eeat_score < 4.0,
            "parasitic_content_flag": seo_results.get("risk", {}).get("parasitic_content_flag"),
        }

        # intent係数ベースの重みを優先し、明示指定があればそちらを使う
        seo_weight = ctx.seo_weight if ctx.seo_weight is not None else alpha
        aio_weight = ctx.aio_weight if ctx.aio_weight is not None else 1 - alpha
        # α適用
        if ctx.seo_weight is None and ctx.aio_weight is None:
            seo_weight = alpha
            aio_weight = 1 - alpha

        # ペナルティ適用
        aio_score_after_penalty, penalty_warnings = self._apply_penalties(aio_score, flags)
        heuristic_notes: List[str] = []
        if flags.get("ymyl_attention_needed"):
            heuristic_notes.append("YMYL領域では著者・資格・一次情報の補強を優先してください（内部ヒューリスティック警告、点数乗算なし）")

        logger.debug(
            "ScoringEngine統合: SEO=%.1f→%.1f AIO=%.1f→%.1f(penalty後=%.1f) "
            "weight=SEO%.2f/AIO%.2f penalties=%s",
            seo_results.get("total_score", 0.0), seo_score,
            aio_results.get("total_score", 0.0), aio_score,
            aio_score_after_penalty,
            seo_weight, aio_weight,
            penalty_warnings,
        )

        integrated_score = seo_score * seo_weight + aio_score_after_penalty * aio_weight

        # 推奨バランス
        total_gap = (100 - seo_score) + (100 - aio_score_after_penalty)
        recommended_seo_focus = round(alpha * 100) if total_gap == 0 else round((100 - aio_score_after_penalty) / total_gap * 100)
        recommended_aio_focus = 100 - recommended_seo_focus

        # 改善ポイント: 簡易的に低スコア順で提示
        improvements: List[str] = []
        seo_low = [(k, v) for k, v in (seo_results.get("scores") or {}).items() if isinstance(v, (int, float)) and v < 7]
        seo_low.sort(key=lambda x: x[1])
        for item_name, score in seo_low[:2]:
            readable = item_name.replace("_score", "").replace("_", " ").title()
            improvements.append(f"SEO優先: {readable} を改善（{score:.1f}/10）")

        aio_actions = aio_results.get("immediate_actions", [])
        for action in aio_actions[:3]:
            improvements.append(f"AIO優先: {action.get('action', '改善施策')}")  # 短文化

        url_type_weights = self.url_type_weights.get(ctx.url_type or "")
        url_type_priorities: List[str] = []
        if url_type_weights:
            sorted_keys = [k for k, _ in sorted(url_type_weights.items(), key=lambda x: x[1], reverse=True)]
            url_type_priorities = [URL_TYPE_PRIORITY_LABELS.get(k, k) for k in sorted_keys]
            if url_type_priorities:
                improvements.insert(0, f"URLタイプ優先: {', '.join(url_type_priorities[:3])}")

        # P04: GEOスコア計算（TL;DR 40% + 統計密度 35% + E-E-A-T 25%）
        geo_tldr_score  = float((aio_results.get("scores", {}).get("geo_tldr") or {}).get("score", 0.0))
        geo_stats_score = float((aio_results.get("scores", {}).get("geo_stats") or {}).get("score", 0.0))
        geo_score_100 = min(100.0, (
            (geo_tldr_score  / 5.0)  * 40.0 +   # TL;DR: 0〜5 → 40点満点
            (geo_stats_score / 10.0) * 35.0 +    # 統計密度: 0〜10 → 35点満点
            (eeat_score      / 10.0) * 25.0       # E-E-A-T: 0〜10 → 25点満点
        ))

        # warningsを集約
        warnings = penalty_warnings + heuristic_notes

        return {
            "integrated_score": integrated_score,
            "seo_score": seo_score,
            "aio_score": aio_score_after_penalty,
            "aio_score_before_penalty": aio_score,  # NEW: for UI consistency
            "applied_penalties": penalty_warnings,  # NEW: for UI display
            "alpha": alpha,
            "industry_profile": ctx.industry or "",
            "primary_focus": "AIO" if aio_score_after_penalty < seo_score else "SEO",
            "improvements": improvements,
            "seo_score_distribution": {k: v for k, v in (seo_results.get("scores") or {}).items()},
            "aio_score_distribution": {k: (v or {}).get("score", 0) for k, v in (aio_results.get("scores") or {}).items()},
            "recommended_balance": {"seo_focus": recommended_seo_focus, "aio_focus": recommended_aio_focus},
            "warnings": warnings,
            "heuristic_notes": heuristic_notes,
            "url_type_weights": url_type_weights or {},
            "url_type_priorities": url_type_priorities,
            "geo_score": round(geo_score_100, 1),
            "geo_role": "diagnostic",
            "geo_breakdown": {
                "tldr":         round(geo_tldr_score,  2),
                "stats_density": round(geo_stats_score, 2),
                "eeat":         round(eeat_score,      2),
            },
        }
