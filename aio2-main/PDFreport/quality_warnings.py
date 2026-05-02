"""Data quality warning badge system.

本モジュールは、サンプル数・欠損率・センチメント偏りに基づく
データ品質の判定と、GUI表示用のバッジ情報を生成します。

依存関係は標準ライブラリのみ（既存ライブラリのみ使用）。
"""

from __future__ import annotations

from typing import Dict, List, Tuple


def _calc_sentiment_skew(sentiment_counts: Dict[str, int]) -> Tuple[str, float]:
    """センチメントの偏りを計算する。

    Args:
        sentiment_counts: {label: count} の辞書（positive/neutral/negative/mixed）

    Returns:
        (max_label, max_ratio): 最多カテゴリ名と全体比率（0-1）。データなしは ("", 0.0)。
    """
    if not sentiment_counts:
        return "", 0.0
    total = sum(int(v) for v in sentiment_counts.values()) or 0
    if total <= 0:
        return "", 0.0
    max_label, max_val = max(sentiment_counts.items(), key=lambda kv: int(kv[1] or 0))
    return str(max_label), (int(max_val) / float(total))


def build_data_quality_warning(
    sample_size: int,
    missing_percentage: float,
    sentiment_counts: Dict[str, int] | None,
) -> Dict[str, object]:
    """データ品質の総合判定とGUI用バッジを生成する。

    判定基準（Phase 1.1 要件）:
    - サンプル数不足: sample_size < 30
    - 欠損過多: missing_percentage > 20%
    - センチメント偏り: 最多カテゴリが > 80%

    Args:
        sample_size: 有効データ件数
        missing_percentage: 欠損率（0-100）
        sentiment_counts: センチメント件数辞書

    Returns:
        dict: {quality_level, warning_message, recommendations, badges}
              badges は [{label, level, message}] の配列
    """
    badges: List[Dict[str, str]] = []

    # サンプル数バッジ
    if sample_size < 30:
        badges.append({
            "label": "サンプル数",
            "level": "error",
            "message": f"サンプル数が少ない（{sample_size}件 < 30件）"
        })
    elif sample_size < 100:
        badges.append({
            "label": "サンプル数",
            "level": "warning",
            "message": f"サンプル数がやや少ない（{sample_size}件 < 推奨100件）"
        })
    else:
        badges.append({
            "label": "サンプル数",
            "level": "success",
            "message": f"十分なサンプル数（{sample_size}件）"
        })

    # 欠損率バッジ
    if missing_percentage > 20.0:
        badges.append({
            "label": "欠損率",
            "level": "warning",
            "message": f"欠損率が高い（{missing_percentage:.1f}% > 20%）"
        })
    elif missing_percentage > 10.0:
        badges.append({
            "label": "欠損率",
            "level": "info",
            "message": f"欠損がやや多い（{missing_percentage:.1f}%）"
        })
    else:
        badges.append({
            "label": "欠損率",
            "level": "success",
            "message": f"欠損は軽微（{missing_percentage:.1f}%）"
        })

    # センチメント偏りバッジ
    max_label, max_ratio = _calc_sentiment_skew(sentiment_counts or {})
    if max_ratio > 0.8:
        badges.append({
            "label": "センチメント偏り",
            "level": "warning",
            "message": f"{max_label or '1カテゴリ'} に偏り（{max_ratio*100:.1f}% > 80%）"
        })
    elif max_ratio > 0.6:
        badges.append({
            "label": "センチメント偏り",
            "level": "info",
            "message": f"{max_label or '1カテゴリ'} が優勢（{max_ratio*100:.1f}%）"
        })
    elif max_ratio > 0.0:
        badges.append({
            "label": "センチメント偏り",
            "level": "success",
            "message": "バランス良好"
        })

    # 総合レベル
    levels = [b["level"] for b in badges]
    if "error" in levels or (sample_size < 30):
        quality_level = "low"
    elif "warning" in levels:
        quality_level = "medium"
    else:
        quality_level = "high"

    # メッセージと推奨事項
    recommendations: List[str] = []
    if sample_size < 30:
        recommendations.append("最低30件以上（推奨100件以上）の追加データ収集を推奨します")
    elif sample_size < 100:
        recommendations.append("サンプルを増やすことで統計的信頼性が向上します（推奨100件以上）")
    if missing_percentage > 20.0:
        recommendations.append("入力設計や必須化により欠損を抑制してください（欠損20%以下を目標）")
    if max_ratio > 0.8:
        recommendations.append("募集チャネル・設問の見直しで回答の偏りを低減してください")

    if not recommendations:
        recommendations.append("現状のデータで分析可能です。詳細セグメント分析を検討してください")

    if quality_level == "low":
        warning_message = "データ品質が低いため、結果の一般化は避け参考情報として扱ってください"
    elif quality_level == "medium":
        warning_message = "データ品質はおおむね許容範囲です。解釈時に留意点があります"
    else:
        warning_message = "データ品質は良好です。分析結果の信頼性は高いと考えられます"

    return {
        "quality_level": quality_level,
        "warning_message": warning_message,
        "recommendations": recommendations,
        "badges": badges,
    }


__all__ = ["build_data_quality_warning"]





