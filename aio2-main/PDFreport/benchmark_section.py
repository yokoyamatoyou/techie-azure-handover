# -*- coding: utf-8 -*-
"""
PDF Benchmark Section - 業界平均比較/代替コンテンツ

競合分析が未選択の場合でも価値を提供するため、
業界平均や一般的なベストプラクティスを表示する。
"""

from typing import Dict, List, Any, Optional

# 業界別の平均スコア目安（参考値）
# 実データに基づく改善が必要だが、初期値として設定
INDUSTRY_BENCHMARKS: Dict[str, Dict[str, float]] = {
    "EC・小売": {
        "seo_score": 65,
        "aio_score": 55,
        "integrated_score": 60,
        "description": "商品ページの構造化データとE-E-A-Tが重要",
    },
    "サービス・BtoB": {
        "seo_score": 60,
        "aio_score": 50,
        "integrated_score": 55,
        "description": "専門性の明示と事例の充実が差別化要因",
    },
    "メディア・ニュース": {
        "seo_score": 70,
        "aio_score": 65,
        "integrated_score": 68,
        "description": "鮮度と引用可能性が高く求められる",
    },
    "飲食・店舗": {
        "seo_score": 55,
        "aio_score": 45,
        "integrated_score": 50,
        "description": "ローカルSEOとGoogleビジネスプロフィール連携が重要",
    },
    "医療・健康": {
        "seo_score": 60,
        "aio_score": 55,
        "integrated_score": 58,
        "description": "YMYL領域のためE-E-A-T要件が極めて厳格",
    },
    "教育・学習": {
        "seo_score": 62,
        "aio_score": 58,
        "integrated_score": 60,
        "description": "コンテンツの深さと信頼性が重視される",
    },
    "一般": {
        "seo_score": 58,
        "aio_score": 48,
        "integrated_score": 53,
        "description": "業界特化の対策よりも基本対策の徹底が有効",
    },
}

# 競合未選択時の一般的なベストプラクティス
GENERAL_BEST_PRACTICES: List[Dict[str, str]] = [
    {
        "title": "結論ファースト構成",
        "description": "各ページの冒頭に結論・要約を配置し、AI検索での引用可能性を高める",
        "impact": "AIOスコア +10-15%",
        "difficulty": "低（コンテンツ編集のみ）",
    },
    {
        "title": "構造化データの導入",
        "description": "Organization、Article、FAQPageスキーマを実装し、検索結果でのリッチリザルト表示を狙う",
        "impact": "SEO/AIOスコア +15-20%",
        "difficulty": "中（技術対応が必要）",
    },
    {
        "title": "E-E-A-T情報の明示",
        "description": "著者情報、会社概要、専門資格などを明確に記載し、信頼性を向上",
        "impact": "全体スコア +5-10%",
        "difficulty": "低（コンテンツ追加のみ）",
    },
    {
        "title": "FAQ/比較表の追加",
        "description": "よくある質問や競合比較表を追加し、ユーザーの疑問に直接回答",
        "impact": "AIOスコア +10-15%",
        "difficulty": "低（コンテンツ追加のみ）",
    },
    {
        "title": "メタ情報の個別最適化",
        "description": "各ページのタイトル・説明文を固有のものに設定し、クリック率を改善",
        "impact": "SEOスコア +5-10%",
        "difficulty": "低（管理画面で設定可能）",
    },
]


def get_industry_benchmark(industry: str) -> Dict[str, Any]:
    """
    業界の平均スコア目安を取得する。
    
    Args:
        industry: 業界名
    
    Returns:
        業界平均スコアと説明
    """
    # 業界名の部分一致で検索
    for key, data in INDUSTRY_BENCHMARKS.items():
        if key in industry or industry in key:
            return {
                "industry": key,
                "benchmarks": data,
                "found": True,
            }
    
    # 見つからない場合は一般カテゴリ
    return {
        "industry": "一般",
        "benchmarks": INDUSTRY_BENCHMARKS["一般"],
        "found": False,
    }


def calculate_benchmark_comparison(
    actual_scores: Dict[str, float],
    industry: str,
) -> Dict[str, Any]:
    """
    実スコアと業界平均を比較する。
    
    Args:
        actual_scores: 実際のスコア（seo_score, aio_score, integrated_score）
        industry: 業界名
    
    Returns:
        比較結果
    """
    benchmark = get_industry_benchmark(industry)
    bench_data = benchmark["benchmarks"]
    
    comparisons = []
    for key in ["seo_score", "aio_score", "integrated_score"]:
        actual = actual_scores.get(key, 0)
        expected = bench_data.get(key, 50)
        diff = actual - expected
        
        if diff >= 10:
            status = "優良"
            color = "green"
        elif diff >= 0:
            status = "平均以上"
            color = "blue"
        elif diff >= -10:
            status = "平均以下"
            color = "orange"
        else:
            status = "要改善"
            color = "red"
        
        comparisons.append({
            "metric": key.replace("_score", "").upper(),
            "actual": round(actual, 1),
            "benchmark": expected,
            "diff": round(diff, 1),
            "status": status,
            "color": color,
        })
    
    return {
        "industry": benchmark["industry"],
        "industry_note": bench_data.get("description", ""),
        "comparisons": comparisons,
        "is_above_average": all(c["diff"] >= 0 for c in comparisons),
    }


def get_best_practices(
    max_items: int = 5,
    difficulty_filter: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    一般的なベストプラクティスを取得する。
    
    Args:
        max_items: 最大項目数
        difficulty_filter: 難易度フィルター（"低", "中", "高"）
    
    Returns:
        ベストプラクティスのリスト
    """
    practices = GENERAL_BEST_PRACTICES
    
    if difficulty_filter:
        practices = [p for p in practices if difficulty_filter in p.get("difficulty", "")]
    
    return practices[:max_items]


def render_benchmark_section(
    pdf,
    actual_scores: Dict[str, float],
    industry: str,
    has_competitor: bool = False,
) -> None:
    """
    PDFに業界ベンチマーク比較セクションを描画する。
    
    Args:
        pdf: HighQualityReportPDF インスタンス
        actual_scores: 実際のスコア
        industry: 業界名
        has_competitor: 競合分析があるかどうか
    """
    # 競合分析がある場合はこのセクションをスキップ
    if has_competitor:
        return
    
    pdf.add_page()
    pdf.add_section_title("業界ベンチマーク比較")
    
    # 比較データを取得
    comparison = calculate_benchmark_comparison(actual_scores, industry)
    
    # 業界説明
    pdf.add_info_card(
        f"業界: {comparison['industry']}",
        comparison.get("industry_note", ""),
        card_color=(245, 245, 245),
        max_chars=200,
        allow_split=False,
    )
    
    # スコア比較
    for comp in comparison["comparisons"]:
        diff_sign = "+" if comp["diff"] >= 0 else ""
        content = f"あなたのスコア: {comp['actual']}点 / 業界平均: {comp['benchmark']}点（差: {diff_sign}{comp['diff']}）"
        
        # 色をステータスに応じて変更
        if comp["status"] == "優良":
            card_color = (220, 255, 220)  # 薄い緑
        elif comp["status"] == "要改善":
            card_color = (255, 220, 220)  # 薄い赤
        else:
            card_color = (245, 245, 245)  # グレー
        
        pdf.add_info_card(
            f"{comp['metric']}スコア: {comp['status']}",
            content,
            card_color=card_color,
            max_chars=150,
            allow_split=False,
        )
    
    # ベストプラクティス
    pdf.add_subsection_title("一般的な改善ベストプラクティス")
    
    practices = get_best_practices(max_items=4)
    for practice in practices:
        content = f"{practice['description']}\n期待効果: {practice['impact']} / 難易度: {practice['difficulty']}"
        pdf.add_info_card(
            practice["title"],
            content,
            card_color=(240, 248, 255),
            max_chars=250,
            allow_split=False,
        )


def render_non_ec_trust_section(pdf, trust_data: Dict[str, Any]) -> None:
    """
    非ECサイト向けの信頼性チェックセクションを描画する。
    
    Args:
        pdf: HighQualityReportPDF インスタンス
        trust_data: 信頼性チェック結果
    """
    pdf.add_page()
    pdf.add_section_title("企業サイト信頼性チェック")
    
    # 概要説明
    pdf.add_info_card(
        "なぜ重要？",
        "企業サイトでは、EC機能がなくても「会社が実在し、信頼できる」ことを示す情報が検索エンジン評価に影響します。",
        card_color=(245, 250, 255),
        max_chars=200,
        allow_split=False,
    )
    
    # チェック項目
    check_items = [
        ("会社概要ページ", trust_data.get("has_company_info", False)),
        ("お問い合わせフォーム/連絡先", trust_data.get("has_contact", False)),
        ("プライバシーポリシー", trust_data.get("has_privacy", False)),
        ("利用規約", trust_data.get("has_terms", False)),
        ("代表者/責任者情報", trust_data.get("has_representative", False)),
        ("実績/事例ページ", trust_data.get("has_case_studies", False)),
    ]
    
    for item_name, is_present in check_items:
        status = "✓ 確認済み" if is_present else "△ 未検出"
        card_color = (220, 255, 220) if is_present else (255, 250, 230)
        
        pdf.add_info_card(
            item_name,
            status,
            card_color=card_color,
            max_chars=100,
            allow_split=False,
        )
