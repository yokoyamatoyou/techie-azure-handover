# -*- coding: utf-8 -*-
"""違反事例データベース"""

from typing import List, Dict

VIOLATION_CASES = {
    "景品表示法": [
        {
            "year": 2024,
            "company_type": "健康食品メーカー",
            "violation_type": "優良誤認",
            "expression": "飲むだけで痩せる",
            "description": "ダイエットサプリメントの広告で「飲むだけで痩せる」と表示したが、合理的根拠を示す資料の提出がなかった",
            "penalty": "課徴金1億2000万円",
            "lesson": "効果効能の表示には合理的根拠が必須。「個人の感想」の打消し表示だけでは不十分"
        },
        {
            "year": 2024,
            "company_type": "通販サイト",
            "violation_type": "有利誤認",
            "expression": "通常価格10,000円→特別価格5,000円",
            "description": "「通常価格」として表示した価格での販売実績がほとんどなかった",
            "penalty": "課徴金5000万円",
            "lesson": "二重価格表示には、比較対照価格での販売実績（原則8週間以上）が必要"
        },
        {
            "year": 2023,
            "company_type": "美容クリニック",
            "violation_type": "優良誤認",
            "expression": "満足度98%",
            "description": "施術の満足度調査の方法が不適切で、実態を反映していなかった",
            "penalty": "措置命令",
            "lesson": "アンケート結果を表示する場合、調査方法・対象者・時期を明記"
        },
        {
            "year": 2023,
            "company_type": "化粧品メーカー",
            "violation_type": "優良誤認",
            "expression": "シミが消える",
            "description": "化粧品で「シミが消える」と表示したが、そのような効果の根拠がなかった",
            "penalty": "措置命令、課徴金8000万円",
            "lesson": "化粧品は薬機法の範囲内の効能効果のみ表示可能"
        },
        {
            "year": 2023,
            "company_type": "ECモール出店者",
            "violation_type": "有利誤認",
            "expression": "今だけ限定セール",
            "description": "「今だけ」と表示しながら、長期間同じ価格で販売していた",
            "penalty": "措置命令",
            "lesson": "期間限定表示は実際の期間と整合性が必要"
        }
    ]
}


def get_relevant_cases(violation_type: str = None, business_type: str = None, limit: int = 3) -> List[Dict]:
    """
    関連する違反事例を取得

    Args:
        violation_type: "優良誤認" | "有利誤認" など
        business_type: 業種で絞り込み
        limit: 取得件数
    """
    cases = VIOLATION_CASES.get("景品表示法", [])

    if violation_type:
        cases = [c for c in cases if c["violation_type"] == violation_type]

    if business_type:
        type_mapping = {
            "ec_retail": ["通販サイト", "ECモール"],
            "cosmetics": ["化粧品メーカー", "美容"],
            "food_supplement": ["健康食品メーカー"],
            "healthcare": ["美容クリニック", "クリニック"]
        }
        keywords = type_mapping.get(business_type, [])
        if keywords:
            cases = [c for c in cases if any(kw in c["company_type"] for kw in keywords)]

    return cases[:limit]


def get_case_lesson(expression: str) -> str:
    """表現に関連する事例の教訓を取得"""
    for case in VIOLATION_CASES.get("景品表示法", []):
        if expression in case.get("expression", ""):
            return case.get("lesson", "")
    return ""
