"""
PDFレポート用データマッピングシステム
既存の分析結果を高品質レポートに適切にマッピング
"""

from typing import Dict, List, Any, Optional
import re

def map_analysis_data_to_high_quality_pdf(summary_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    既存の分析結果を高品質PDFレポート用にマッピング
    
    Args:
        summary_data: 既存の分析結果データ
    
    Returns:
        高品質PDF用に最適化されたデータ
    """
    
    # 基本データの確保
    mapped_data = {
        "analysis_target": summary_data.get("analysis_target", "アンケート調査レポート"),
        "survey_type": summary_data.get("survey_type", "customer_satisfaction"),
        "summary_text": summary_data.get("summary_text", summary_data.get("executive_summary", "")),
        "key_insights": summary_data.get("key_insights", []),
        "business_impact": summary_data.get("business_impact", {}),
        "recommendations": summary_data.get("recommendations", []),
    }
    
    # マーケティング分析データのマッピング
    mapped_data.update(map_marketing_analysis(summary_data))
    
    # ユーザー分析データのマッピング
    mapped_data.update(map_user_analysis(summary_data))
    
    # コンサルタント分析データのマッピング
    mapped_data.update(map_consultant_analysis(summary_data))
    
    # AI総合解析データのマッピング
    mapped_data.update(map_ai_comprehensive_analysis(summary_data))
    
    # データ品質の検証と補完
    mapped_data = validate_and_complete_data(mapped_data)
    
    mapped_data["scorecard"] = compute_scorecard(summary_data)
    mapped_data["persona_views"] = build_persona_views(summary_data, mapped_data)
    return mapped_data

def map_marketing_analysis(summary_data: Dict[str, Any]) -> Dict[str, Any]:
    """マーケティング分析データのマッピング"""
    
    # マーケティング視点の分析
    marketing_perspective = summary_data.get("marketing_perspective", "")
    if not marketing_perspective:
        # 代替データから生成
        sentiment_data = summary_data.get("sentiment_analysis", {})
        topics_data = summary_data.get("topic_analysis", {})
        
        marketing_perspective = generate_marketing_analysis(
            sentiment_data, topics_data, summary_data
        )
    
    # 推奨施策の抽出
    recommendations = extract_marketing_recommendations(summary_data)
    
    # 市場分析データ
    market_analysis = extract_market_analysis(summary_data)
    
    return {
        "marketing_perspective": marketing_perspective,
        "recommendations": recommendations,
        "market_analysis": market_analysis
    }

def map_user_analysis(summary_data: Dict[str, Any]) -> Dict[str, Any]:
    """ユーザー分析データのマッピング"""
    
    # ユーザー視点の分析
    user_perspective = summary_data.get("user_perspective", "")
    if not user_perspective:
        # 代替データから生成
        user_perspective = generate_user_analysis(summary_data)
    
    # UX分析データ
    ux_analysis = extract_ux_analysis(summary_data)
    
    # 改善提案
    improvement_suggestions = extract_improvement_suggestions(summary_data)
    
    return {
        "user_perspective": user_perspective,
        "ux_analysis": ux_analysis,
        "improvement_suggestions": improvement_suggestions
    }

def map_consultant_analysis(summary_data: Dict[str, Any]) -> Dict[str, Any]:
    """コンサルタント分析データのマッピング"""
    
    # コンサルタント視点の分析
    consultant_perspective = summary_data.get("consultant_perspective", "")
    if not consultant_perspective:
        consultant_perspective = generate_consultant_analysis(summary_data)
    
    # 戦略的提言
    strategic_recommendations = extract_strategic_recommendations(summary_data)
    
    # ROI分析
    roi_analysis = extract_roi_analysis(summary_data)
    
    return {
        "consultant_perspective": consultant_perspective,
        "strategic_recommendations": strategic_recommendations,
        "roi_analysis": roi_analysis
    }

def map_ai_comprehensive_analysis(summary_data: Dict[str, Any]) -> Dict[str, Any]:
    """AI総合解析データのマッピング"""
    
    # 弱みの改善例
    weakness_improvements = extract_weakness_improvements(summary_data)
    
    # 強みの発展性
    strength_development = extract_strength_development(summary_data)
    
    # 総合アドバイス
    comprehensive_advice = generate_comprehensive_advice(summary_data)
    
    # 実行ロードマップ
    implementation_roadmap = generate_implementation_roadmap(summary_data)
    
    return {
        "weakness_improvements": weakness_improvements,
        "strength_development": strength_development,
        "comprehensive_advice": comprehensive_advice,
        "implementation_roadmap": implementation_roadmap
    }

def generate_marketing_analysis(sentiment_data: Dict, topics_data: Dict, summary_data: Dict) -> str:
    """マーケティング分析の自動生成"""
    
    analysis_parts = []
    
    # センチメント分析に基づく市場機会
    if sentiment_data:
        positive_rate = sentiment_data.get("positive_rate", 0)
        if positive_rate > 0.7:
            analysis_parts.append("顧客満足度が高い水準にあり、ブランド価値の向上が期待できます。")
        elif positive_rate < 0.4:
            analysis_parts.append("顧客満足度に改善の余地があり、市場機会の拡大が可能です。")
    
    # トピック分析に基づく戦略的提案
    if topics_data:
        top_topics = list(topics_data.keys())[:3]
        analysis_parts.append(f"主要な関心トピック（{', '.join(top_topics)}）を活用したマーケティング戦略の展開を推奨します。")
    
    # サンプルサイズに基づく信頼性
    sample_size = summary_data.get("sample_size", 0)
    if sample_size > 100:
        analysis_parts.append("十分なサンプルサイズにより、統計的に信頼性の高い分析結果が得られています。")
    
    return "\\n\\n".join(analysis_parts) if analysis_parts else "マーケティング分析データが不足しています。"

def generate_user_analysis(summary_data: Dict[str, Any]) -> str:
    """ユーザー分析の自動生成"""
    
    analysis_parts = []
    
    # 感情分析に基づくユーザーエクスペリエンス
    emotion_data = summary_data.get("emotion_analysis", {})
    if emotion_data:
        top_emotions = sorted(emotion_data.items(), key=lambda x: x[1], reverse=True)[:3]
        emotion_text = ", ".join([f"{emotion}({score:.1%})" for emotion, score in top_emotions])
        analysis_parts.append(f"主要な感情: {emotion_text}")
    
    # トピック分析に基づくユーザーニーズ
    topics = summary_data.get("topic_analysis", {})
    if topics:
        top_topics = list(topics.keys())[:3]
        analysis_parts.append(f"ユーザーの主要関心事: {', '.join(top_topics)}")
    
    # 改善提案
    analysis_parts.append("ユーザーエクスペリエンスの向上により、顧客満足度とロイヤルティの向上が期待できます。")
    
    return "\\n\\n".join(analysis_parts) if analysis_parts else "ユーザー分析データが不足しています。"

def generate_consultant_analysis(summary_data: Dict[str, Any]) -> str:
    """コンサルタント分析の自動生成"""
    
    analysis_parts = []
    
    # ビジネスインパクト分析
    business_impact = summary_data.get("business_impact", {})
    if business_impact:
        analysis_parts.append("ビジネスインパクト分析に基づく戦略的提言を行います。")
    
    # データ品質の評価
    sample_size = summary_data.get("sample_size", 0)
    if sample_size > 50:
        analysis_parts.append("十分なデータ量により、信頼性の高い分析結果が得られています。")
    else:
        analysis_parts.append("サンプルサイズが限定的なため、追加データの収集を推奨します。")
    
    # 戦略的提言
    analysis_parts.append("組織の強みを活かした戦略的改善により、競争優位性の構築が可能です。")
    
    return "\\n\\n".join(analysis_parts) if analysis_parts else "コンサルタント分析データが不足しています。"

def extract_marketing_recommendations(summary_data: Dict[str, Any]) -> List[str]:
    """マーケティング推奨施策の抽出"""
    
    recommendations = summary_data.get("recommendations", [])
    if not recommendations:
        # デフォルトの推奨施策を生成
        recommendations = [
            "ブランド認知度の向上",
            "顧客ロイヤルティプログラムの導入",
            "価格戦略の最適化"
        ]
    
    return recommendations[:5]  # 最大5つまで

def extract_market_analysis(summary_data: Dict[str, Any]) -> Dict[str, Any]:
    """市場分析データの抽出"""
    
    return {
        "market_size": summary_data.get("market_size", "未設定"),
        "competition_level": summary_data.get("competition_level", "中程度"),
        "growth_potential": summary_data.get("growth_potential", "有望")
    }

def extract_ux_analysis(summary_data: Dict[str, Any]) -> Dict[str, Any]:
    """UX分析データの抽出"""
    
    return {
        "usability_score": summary_data.get("usability_score", "良好"),
        "satisfaction_level": summary_data.get("satisfaction_level", "中程度"),
        "improvement_areas": summary_data.get("improvement_areas", ["ユーザビリティ", "パフォーマンス"])
    }

def extract_improvement_suggestions(summary_data: Dict[str, Any]) -> List[str]:
    """改善提案の抽出"""
    
    suggestions = summary_data.get("improvement_suggestions", [])
    if not suggestions:
        suggestions = [
            "ユーザーインターフェースの改善",
            "レスポンス時間の短縮",
            "ヘルプ機能の充実"
        ]
    
    return suggestions[:5]

def extract_strategic_recommendations(summary_data: Dict[str, Any]) -> List[str]:
    """戦略的提言の抽出"""
    
    recommendations = summary_data.get("strategic_recommendations", [])
    if not recommendations:
        recommendations = [
            "組織能力の強化",
            "プロセス効率化",
            "技術革新の推進"
        ]
    
    return recommendations[:5]

def extract_roi_analysis(summary_data: Dict[str, Any]) -> Dict[str, Any]:
    """ROI分析データの抽出"""
    
    return {
        "expected_roi": summary_data.get("expected_roi", "15-25%"),
        "payback_period": summary_data.get("payback_period", "6-12ヶ月"),
        "investment_required": summary_data.get("investment_required", "中程度")
    }

def extract_weakness_improvements(summary_data: Dict[str, Any]) -> List[str]:
    """弱みの改善例の抽出"""
    
    improvements = summary_data.get("weakness_improvements", [])
    if not improvements:
        # センチメント分析から弱みを特定
        sentiment_data = summary_data.get("sentiment_analysis", {})
        negative_rate = sentiment_data.get("negative_rate", 0)
        
        if negative_rate > 0.3:
            improvements.append("顧客満足度の向上")
        improvements.extend([
            "プロセス効率化",
            "品質管理の強化",
            "コスト最適化"
        ])
    
    return improvements[:5]

def extract_strength_development(summary_data: Dict[str, Any]) -> List[str]:
    """強みの発展性の抽出"""
    
    developments = summary_data.get("strength_development", [])
    if not developments:
        # センチメント分析から強みを特定
        sentiment_data = summary_data.get("sentiment_analysis", {})
        positive_rate = sentiment_data.get("positive_rate", 0)
        
        if positive_rate > 0.7:
            developments.append("顧客満足度の競合優位性拡大")
        developments.extend([
            "ブランド価値の向上",
            "技術革新の推進",
            "市場シェアの拡大"
        ])
    
    return developments[:5]

def generate_comprehensive_advice(summary_data: Dict[str, Any]) -> str:
    """総合アドバイスの生成"""
    
    advice_parts = []
    
    # 短期戦略
    advice_parts.append("【短期戦略（3-6ヶ月）】")
    advice_parts.append("• 即座に改善可能な課題への対応")
    advice_parts.append("• 顧客フィードバックの迅速な反映")
    advice_parts.append("• プロセス効率化の推進")
    
    # 中期戦略
    advice_parts.append("\\n【中期戦略（6-12ヶ月）】")
    advice_parts.append("• 組織能力の強化")
    advice_parts.append("• 技術基盤の整備")
    advice_parts.append("• 市場機会の活用")
    
    # 長期戦略
    advice_parts.append("\\n【長期戦略（1-2年）】")
    advice_parts.append("• 持続的成長の基盤構築")
    advice_parts.append("• 競争優位性の確立")
    advice_parts.append("• イノベーションの推進")
    
    return "\\n".join(advice_parts)

def generate_implementation_roadmap(summary_data: Dict[str, Any]) -> List[str]:
    """実行ロードマップの生成"""
    
    roadmap = [
        "Phase 1: 現状分析と課題特定（1ヶ月）",
        "Phase 2: 改善計画の策定（2週間）",
        "Phase 3: パイロット実施（2ヶ月）",
        "Phase 4: 本格展開（3ヶ月）",
        "Phase 5: 効果測定と改善（継続）"
    ]
    
    return roadmap

def build_persona_views(summary_data: Dict[str, Any], mapped_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """マーケター/サイト作成者向けのペルソナ別ビューを組み立てる"""
    scorecard = compute_scorecard(summary_data)
    base_actions = summary_data.get("action_items") or summary_data.get("recommendations") or []
    marketing_notes = summary_data.get("marketing_perspective") or mapped_data.get("marketing_perspective") or ""
    site_creator_notes = (
        summary_data.get("technical_notes")
        or summary_data.get("site_creator_perspective")
        or summary_data.get("engineer_perspective")
        or summary_data.get("user_perspective")
        or ""
    )
    
    marketing = {
        "title": "マーケター向けサマリ",
        "summary": summary_data.get("summary_text", ""),
        "actions": base_actions[:5],
        "kpi_focus": summary_data.get("kpi_focus") or ["CVR", "CTR", "リード数"],
        "notes": marketing_notes,
        "scorecard": scorecard,
    }
    site_creator = {
        "title": "サイト作成者向けサマリ",
        "summary": summary_data.get("summary_text", ""),
        "actions": (summary_data.get("technical_actions") or summary_data.get("improvement_suggestions") or base_actions)[:5],
        "kpi_focus": summary_data.get("technical_kpis") or ["INP/LCP (Core Web Vitals)", "構造化データエラー率", "Indexability"],
        "notes": site_creator_notes,
        "scorecard": scorecard,
        "dependencies": summary_data.get("dependencies") or ["OpenGraph", "JSON-LD", "robots.txt"],
    }
    return {"marketing": marketing, "site_creator": site_creator}

def compute_scorecard(summary_data: Dict[str, Any]) -> Dict[str, float]:
    """構造化度・エビデンス・明確性・技術/ビジネス深度の簡易スコア"""
    text = " ".join([
        str(summary_data.get("summary_text", "")),
        " ".join(summary_data.get("action_items") or []),
        " ".join(summary_data.get("recommendations") or []),
        str(summary_data.get("marketing_perspective", "")),
        str(summary_data.get("user_perspective", "")),
        str(summary_data.get("consultant_perspective", "")),
    ])
    tokens = text.split()
    length = max(len(tokens), 1)
    
    def ratio(count: int, denom: int, scale: float = 5.0) -> float:
        return round(min(scale, (count / max(denom, 1)) * scale), 2)
    
    bullet_like = text.count("・") + text.count("•") + text.count("- ")
    tables = text.count("|")
    urls = len(re.findall(r"https?://", text))
    numerics = len(re.findall(r"\d+", text))
    pronouns = len(re.findall(r"\b(it|this|that|これ|それ)\b", text, flags=re.IGNORECASE))
    entities = len(re.findall(r"[A-Z][a-z]+", text))
    
    structure = ratio(bullet_like + tables, length // 40 or 1)
    evidence = ratio(urls + numerics, length // 50 or 1)
    clarity = ratio(max(entities - pronouns, 0), length // 60 or 1)
    tech_depth = ratio(len(summary_data.get("technical_actions") or []) + numerics, length // 50 or 1)
    biz_value = ratio(len(summary_data.get("action_items") or []) + urls, length // 50 or 1)
    
    return {
        "structure": structure,
        "evidence": evidence,
        "clarity": clarity,
        "technical_depth": tech_depth,
        "business_value": biz_value,
    }

def validate_and_complete_data(mapped_data: Dict[str, Any]) -> Dict[str, Any]:
    """データの検証と補完"""
    
    # 必須フィールドの確認
    required_fields = [
        "analysis_target", "summary_text", "marketing_perspective",
        "user_perspective", "consultant_perspective", "comprehensive_advice"
    ]
    
    for field in required_fields:
        if not mapped_data.get(field):
            mapped_data[field] = f"{field}のデータが不足しています。"
    
    # リスト型フィールドの確認
    list_fields = [
        "key_insights", "recommendations", "weakness_improvements",
        "strength_development", "implementation_roadmap"
    ]
    
    for field in list_fields:
        if not isinstance(mapped_data.get(field), list):
            mapped_data[field] = []
    
    return mapped_data

def format_text_for_pdf(text: str) -> str:
    """PDF用テキストのフォーマット"""
    
    if not text:
        return ""
    
    # 改行文字の正規化
    text = text.replace("\\n", "\\n")
    
    # 長すぎる行の分割
    lines = text.split("\\n")
    formatted_lines = []
    
    for line in lines:
        if len(line) > 80:  # 80文字を超える場合は分割
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line + " " + word) > 80:
                    formatted_lines.append(current_line.strip())
                    current_line = word
                else:
                    current_line += " " + word if current_line else word
            if current_line:
                formatted_lines.append(current_line.strip())
        else:
            formatted_lines.append(line)
    
    return "\\n".join(formatted_lines)

if __name__ == "__main__":
    # テスト用のサンプルデータ
    sample_data = {
        "analysis_target": "顧客満足度調査レポート",
        "survey_type": "customer_satisfaction",
        "summary_text": "テストサマリー",
        "sentiment_analysis": {"positive_rate": 0.75, "negative_rate": 0.15},
        "topic_analysis": {"品質": 0.8, "価格": 0.6, "サービス": 0.7},
        "sample_size": 150
    }
    
    # マッピングテスト
    mapped_data = map_analysis_data_to_high_quality_pdf(sample_data)
    
    print("=== データマッピングテスト ===")
    print(f"マッピング結果: {len(mapped_data)} フィールド")
    print(f"マーケティング分析: {len(mapped_data.get('marketing_perspective', ''))} 文字")
    print(f"ユーザー分析: {len(mapped_data.get('user_perspective', ''))} 文字")
    print(f"コンサルタント分析: {len(mapped_data.get('consultant_perspective', ''))} 文字")
    print(f"AI総合解析: {len(mapped_data.get('comprehensive_advice', ''))} 文字")
    print("=== テスト完了 ===")







