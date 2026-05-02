"""
プリセット別ペルソナ視点マッピングシステム
プリセットごとに適切なペルソナ視点を「○○分析」形式に変換
"""

from typing import Dict, List, Any, Optional
import re

# プリセット別ペルソナマッピング
PRESET_PERSONA_MAPPING = {
    "customer_satisfaction": {
        "marketing_perspective": "マーケティング分析",
        "user_perspective": "ユーザー分析", 
        "consultant_perspective": "コンサルタント分析",
        "marketing_section_title": "マーケティング分析",
        "user_section_title": "ユーザー分析",
        "consultant_section_title": "コンサルタント分析"
    },
    "employee_satisfaction": {
        "marketing_perspective": "HR戦略分析",
        "user_perspective": "従業員分析",
        "consultant_perspective": "組織開発分析",
        "marketing_section_title": "HR戦略分析",
        "user_section_title": "従業員分析", 
        "consultant_section_title": "組織開発分析"
    },
    "product_feedback": {
        "marketing_perspective": "プロダクトマーケティング分析",
        "user_perspective": "プロダクト分析",
        "consultant_perspective": "プロダクト戦略分析",
        "marketing_section_title": "プロダクトマーケティング分析",
        "user_section_title": "プロダクト分析",
        "consultant_section_title": "プロダクト戦略分析"
    },
    "market_research": {
        "marketing_perspective": "市場分析",
        "user_perspective": "顧客分析",
        "consultant_perspective": "競合分析",
        "marketing_section_title": "市場分析",
        "user_section_title": "顧客分析",
        "consultant_section_title": "競合分析"
    },
    "brand_research": {
        "marketing_perspective": "ブランド分析",
        "user_perspective": "認知分析",
        "consultant_perspective": "ブランド戦略分析",
        "marketing_section_title": "ブランド分析",
        "user_section_title": "認知分析",
        "consultant_section_title": "ブランド戦略分析"
    },
    "public_opinion": {
        "marketing_perspective": "政策分析",
        "user_perspective": "住民分析",
        "consultant_perspective": "行政戦略分析",
        "marketing_section_title": "政策分析",
        "user_section_title": "住民分析",
        "consultant_section_title": "行政戦略分析"
    },
    "hospitality": {
        "marketing_perspective": "マーケティング分析",
        "user_perspective": "企画分析",
        "consultant_perspective": "コンサルタント分析",
        "marketing_section_title": "マーケティング分析",
        "user_section_title": "企画分析",
        "consultant_section_title": "コンサルタント分析"
    }
}

def get_preset_persona_mapping(survey_type: str) -> Dict[str, str]:
    """
    プリセット別のペルソナマッピングを取得
    
    Args:
        survey_type: 調査タイプ
    
    Returns:
        ペルソナマッピング辞書
    """
    return PRESET_PERSONA_MAPPING.get(survey_type, PRESET_PERSONA_MAPPING["customer_satisfaction"])

def map_perspective_to_analysis_format(text: str, survey_type: str, perspective_type: str) -> str:
    """
    ペルソナ視点テキストを「○○分析」形式に変換
    
    Args:
        text: 元のテキスト
        survey_type: 調査タイプ
        perspective_type: 視点タイプ (marketing_perspective, user_perspective, consultant_perspective)
    
    Returns:
        変換されたテキスト
    """
    if not text:
        return text
    
    # プリセット別マッピングを取得
    mapping = get_preset_persona_mapping(survey_type)
    
    # 視点タイプに応じた分析名を取得
    analysis_name = mapping.get(perspective_type, "分析")
    
    # 「○○視点」を「○○分析」に置換
    patterns = [
        (r"マーケティング視点", analysis_name),
        (r"ユーザー視点", analysis_name),
        (r"コンサルタント視点", analysis_name),
        (r"HR視点", analysis_name),
        (r"従業員視点", analysis_name),
        (r"組織開発視点", analysis_name),
        (r"プロダクトマーケティング視点", analysis_name),
        (r"プロダクト視点", analysis_name),
        (r"プロダクト戦略視点", analysis_name),
        (r"市場視点", analysis_name),
        (r"顧客視点", analysis_name),
        (r"競合視点", analysis_name),
        (r"ブランド視点", analysis_name),
        (r"認知視点", analysis_name),
        (r"ブランド戦略視点", analysis_name),
        (r"サービス視点", analysis_name),
        (r"顧客体験視点", analysis_name),
        (r"サービス戦略視点", analysis_name)
    ]
    
    # パターンマッチングで置換
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    
    return text

def get_section_title(survey_type: str, perspective_type: str) -> str:
    """
    プリセット別のセクションタイトルを取得
    
    Args:
        survey_type: 調査タイプ
        perspective_type: 視点タイプ
    
    Returns:
        セクションタイトル
    """
    mapping = get_preset_persona_mapping(survey_type)
    return mapping.get(f"{perspective_type}_section_title", "分析")

def get_subsection_title(survey_type: str, perspective_type: str) -> str:
    """
    プリセット別のサブセクションタイトルを取得
    
    Args:
        survey_type: 調査タイプ
        perspective_type: 視点タイプ
    
    Returns:
        サブセクションタイトル
    """
    subsection_mapping = {
        "customer_satisfaction": {
            "marketing_perspective": "市場機会と戦略的提案",
            "user_perspective": "顧客ニーズと改善点",
            "consultant_perspective": "ビジネス戦略と実行計画"
        },
        "employee_satisfaction": {
            "marketing_perspective": "HR戦略と組織改善提案",
            "user_perspective": "従業員ニーズと改善点",
            "consultant_perspective": "組織開発戦略と実行計画"
        },
        "product_feedback": {
            "marketing_perspective": "プロダクトマーケティング戦略",
            "user_perspective": "プロダクト改善点とニーズ",
            "consultant_perspective": "プロダクト戦略と実行計画"
        },
        "market_research": {
            "marketing_perspective": "市場機会と競合戦略",
            "user_perspective": "顧客インサイトとニーズ",
            "consultant_perspective": "市場戦略と実行計画"
        },
        "brand_research": {
            "marketing_perspective": "ブランド戦略と認知向上",
            "user_perspective": "ブランド認知と改善点",
            "consultant_perspective": "ブランド戦略と実行計画"
        },
        "public_opinion": {
            "marketing_perspective": "政策戦略と住民満足度向上",
            "user_perspective": "住民ニーズと改善点",
            "consultant_perspective": "行政戦略と実行計画"
        },
        "hospitality": {
            "marketing_perspective": "宿泊業マーケティング戦略",
            "user_perspective": "宿泊体験と改善点",
            "consultant_perspective": "宿泊業戦略と実行計画"
        }
    }
    
    mapping = subsection_mapping.get(survey_type, subsection_mapping["customer_satisfaction"])
    return mapping.get(perspective_type, "分析と提案")

def transform_analysis_data_for_preset(summary_data: Dict[str, Any], survey_type: str) -> Dict[str, Any]:
    """
    プリセット別に分析データを変換
    
    Args:
        summary_data: 元の分析データ
        survey_type: 調査タイプ
    
    Returns:
        変換された分析データ
    """
    transformed_data = summary_data.copy()
    
    # 各視点のテキストを変換
    perspective_types = ["marketing_perspective", "user_perspective", "consultant_perspective"]
    
    for perspective_type in perspective_types:
        if perspective_type in transformed_data and transformed_data[perspective_type]:
            original_text = transformed_data[perspective_type]
            transformed_text = map_perspective_to_analysis_format(
                original_text, survey_type, perspective_type
            )
            transformed_data[perspective_type] = transformed_text
        else:
            # データが存在しない場合はデフォルト値を設定
            perspective_names = {
                "marketing_perspective": "マーケティング分析",
                "user_perspective": "ユーザー分析", 
                "consultant_perspective": "コンサルタント分析"
            }
            perspective_name = perspective_names.get(perspective_type, "分析")
            transformed_data[perspective_type] = f"{perspective_name}の詳細データを準備中です。分析結果が利用可能になり次第、更新いたします。"
    
    # セクションタイトルを追加
    for perspective_type in perspective_types:
        section_key = f"{perspective_type}_section_title"
        transformed_data[section_key] = get_section_title(survey_type, perspective_type)
        
        subsection_key = f"{perspective_type}_subsection_title"
        transformed_data[subsection_key] = get_subsection_title(survey_type, perspective_type)
    
    return transformed_data

def get_preset_specific_analysis_template(survey_type: str) -> Dict[str, str]:
    """
    プリセット別の分析テンプレートを取得
    
    Args:
        survey_type: 調査タイプ
    
    Returns:
        分析テンプレート
    """
    templates = {
        "customer_satisfaction": {
            "marketing_analysis": "顧客満足度調査の結果を基に、マーケティング戦略の最適化と顧客価値の向上を図ります。",
            "user_analysis": "顧客の声を分析し、ユーザーエクスペリエンスの改善と顧客満足度の向上を目指します。",
            "consultant_analysis": "データに基づく戦略的提言により、組織の競争力強化と持続的成長を実現します。"
        },
        "employee_satisfaction": {
            "marketing_analysis": "従業員満足度調査の結果を基に、HR戦略の最適化と組織価値の向上を図ります。",
            "user_analysis": "従業員の声を分析し、職場環境の改善と従業員満足度の向上を目指します。",
            "consultant_analysis": "データに基づく組織開発提言により、組織力強化と持続的成長を実現します。"
        },
        "brand_research": {
            "marketing_analysis": "ブランド調査の結果を基に、ブランド戦略の最適化とブランド価値の向上を図ります。",
            "user_analysis": "ブランド認知の現状を分析し、ブランド体験の改善とブランド価値の向上を目指します。",
            "consultant_analysis": "データに基づくブランド戦略提言により、ブランド競争力強化と持続的成長を実現します。"
        },
        "public_opinion": {
            "marketing_analysis": "世論調査の結果を基に、政策戦略の最適化と住民満足度の向上を図ります。",
            "user_analysis": "住民の声を分析し、行政サービスの改善と住民満足度の向上を目指します。",
            "consultant_analysis": "データに基づく行政戦略提言により、行政効率性強化と持続的改善を実現します。"
        },
        "hospitality": {
            "marketing_analysis": "宿泊業調査の結果を基に、マーケティング戦略の最適化と顧客価値の向上を図ります。",
            "user_analysis": "宿泊客の声を分析し、宿泊体験の改善と顧客満足度の向上を目指します。",
            "consultant_analysis": "データに基づく宿泊業戦略提言により、競争力強化と持続的成長を実現します。"
        }
    }
    
    return templates.get(survey_type, templates["customer_satisfaction"])

if __name__ == "__main__":
    # テスト用のサンプルデータ
    test_data = {
        "marketing_perspective": "マーケティング視点から見ると、商品の品質は競合優位性を発揮している。",
        "user_perspective": "ユーザー視点では、商品の使いやすさと機能性に高い評価を得ている。",
        "consultant_perspective": "コンサルタント視点では、組織の強みを活かした戦略的改善が可能。"
    }
    
    # プリセット別変換テスト
    survey_types = ["customer_satisfaction", "employee_satisfaction", "market_research", "brand_research", "public_opinion", "hospitality"]
    
    print("=== プリセット別ペルソナ視点変換テスト ===")
    
    for survey_type in survey_types:
        print(f"\\n【{survey_type}】")
        transformed = transform_analysis_data_for_preset(test_data, survey_type)
        
        print(f"マーケティング: {transformed['marketing_perspective']}")
        print(f"ユーザー: {transformed['user_perspective']}")
        print(f"コンサルタント: {transformed['consultant_perspective']}")
        
        print(f"セクションタイトル:")
        print(f"  - マーケティング: {transformed['marketing_perspective_section_title']}")
        print(f"  - ユーザー: {transformed['user_perspective_section_title']}")
        print(f"  - コンサルタント: {transformed['consultant_perspective_section_title']}")
    
    print("\\n=== テスト完了 ===")


