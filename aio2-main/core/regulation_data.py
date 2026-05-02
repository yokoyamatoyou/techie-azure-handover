# -*- coding: utf-8 -*-
"""法規制データベース"""

from typing import Dict, List

# industry_detector からBUSINESS_TYPESをインポート
from core.industry_detector import BUSINESS_TYPES

REGULATIONS = {
    "景品表示法": {
        "formal_name": "不当景品類及び不当表示防止法",
        "overview_simple": "商品やサービスの広告で、嘘や大げさな表現を禁止する法律",
        "overview_detail": "消費者が商品・サービスを選ぶ際に、実際より良く見せたり、他社より有利に見せたりする不当な表示を禁止。消費者庁が所管。",
        "penalty": {
            "primary": "措置命令（違反行為の差止め、再発防止策等）",
            "secondary": "課徴金（違反表示に係る売上額の3%）",
            "criminal": "措置命令違反で2年以下の懲役または300万円以下の罰金"
        },
        "check_items": ["優良誤認", "有利誤認", "打消し表示", "二重価格"],
        "applicable_to": ["all"],  # 全業種
        "recent_cases": [
            {
                "year": 2024,
                "company_type": "健康食品メーカー",
                "violation": "優良誤認",
                "description": "「飲むだけで痩せる」との表示に合理的根拠なし",
                "penalty": "課徴金1億2000万円"
            },
            {
                "year": 2024,
                "company_type": "通販サイト",
                "violation": "有利誤認",
                "description": "実態のない「通常価格」からの割引表示",
                "penalty": "課徴金5000万円"
            },
            {
                "year": 2023,
                "company_type": "美容クリニック",
                "violation": "優良誤認",
                "description": "施術効果の誇大表示",
                "penalty": "措置命令"
            }
        ]
    },
    "薬機法": {
        "formal_name": "医薬品、医療機器等の品質、有効性及び安全性の確保等に関する法律",
        "overview_simple": "医薬品・化粧品・健康食品の広告で、効果効能を誇大に表現することを禁止",
        "overview_detail": "旧薬事法。医薬品等の品質・有効性・安全性を確保し、保健衛生の向上を図る。厚生労働省が所管。",
        "penalty": {
            "primary": "中止命令、回収命令",
            "secondary": "業務停止命令",
            "criminal": "2年以下の懲役または200万円以下の罰金（併科あり）"
        },
        "check_items": ["効能効果の標榜", "医薬品的表現", "ビフォーアフター", "体験談"],
        "applicable_to": ["cosmetics", "food_supplement", "healthcare"],
        "recent_cases": [
            {
                "year": 2024,
                "company_type": "化粧品メーカー",
                "violation": "効能効果の逸脱",
                "description": "「シワが消える」等の医薬品的効能を標榜",
                "penalty": "業務停止命令30日"
            }
        ]
    },
    "ステマ規制": {
        "formal_name": "景品表示法に基づくステルスマーケティング規制",
        "overview_simple": "広告であることを隠した宣伝（ステマ）を禁止する規制。2023年10月施行",
        "overview_detail": "事業者が表示内容の決定に関与しているにもかかわらず、第三者の表示であるかのように見せる行為を禁止。",
        "penalty": {
            "primary": "措置命令",
            "secondary": "課徴金の可能性",
            "criminal": "措置命令違反で罰則適用"
        },
        "check_items": ["PR表記の有無", "表記の視認性", "アフィリエイト表示"],
        "applicable_to": ["affiliate_media", "cosmetics", "food_supplement"],
        "recent_cases": []
    },
    "特定商取引法": {
        "formal_name": "特定商取引に関する法律",
        "overview_simple": "通信販売等で、販売者情報や返品条件の表示を義務付ける法律",
        "overview_detail": "訪問販売、通信販売、電話勧誘販売等の消費者トラブルを防止。経済産業省・消費者庁が所管。",
        "penalty": {
            "primary": "業務改善指示",
            "secondary": "業務停止命令（最長2年）",
            "criminal": "100万円以下の罰金、懲役3年以下"
        },
        "check_items": ["販売業者名", "所在地", "電話番号", "返品条件", "支払方法"],
        "applicable_to": ["ec_retail"],
        "recent_cases": []
    },
    "医療広告ガイドライン": {
        "formal_name": "医療広告ガイドライン",
        "overview_simple": "医療機関の広告で、誇大表示や比較広告などを制限する指針",
        "overview_detail": "医療法に基づく広告規制。厚生労働省が策定。ウェブサイトも規制対象。",
        "penalty": {
            "primary": "是正命令",
            "secondary": "6ヶ月以下の懲役または30万円以下の罰金",
            "criminal": ""
        },
        "check_items": ["ビフォーアフター写真", "患者の声", "最上級表現", "未承認治療"],
        "applicable_to": ["healthcare"],
        "recent_cases": []
    },
    "健康増進法": {
        "formal_name": "健康増進法",
        "overview_simple": "健康食品等で、病気の予防や治療効果をうたうことを禁止",
        "overview_detail": "国民の健康増進を目的とし、食品の虚偽・誇大広告を禁止。消費者庁が所管。",
        "penalty": {
            "primary": "勧告",
            "secondary": "措置命令",
            "criminal": "6ヶ月以下の懲役または100万円以下の罰金"
        },
        "check_items": ["疾病の治療・予防効果", "医学的根拠のない効果"],
        "applicable_to": ["food_supplement"],
        "recent_cases": []
    }
}


def get_applicable_regulations(business_type: str, content_analysis: Dict = None) -> List[Dict]:
    """
    事業タイプに適用される規制リストを取得

    Returns:
        [
            {
                "regulation": "景品表示法",
                "applicability": "high",
                "reason": "EC販売を行っているため",
                "check_items": ["優良誤認", "有利誤認", "二重価格"]
            }
        ]
    """
    results = []

    for reg_name, reg_data in REGULATIONS.items():
        applicable_to = reg_data.get("applicable_to", [])

        if "all" in applicable_to or business_type in applicable_to:
            applicability = "high"
            reason = f"{BUSINESS_TYPES.get(business_type, {}).get('name', business_type)}に適用される規制"
        elif any(bt in applicable_to for bt in ["ec_retail", "affiliate_media"]):
            # 関連性が中程度
            applicability = "medium"
            reason = "関連業種として確認推奨"
        else:
            continue

        results.append({
            "regulation": reg_name,
            "formal_name": reg_data["formal_name"],
            "applicability": applicability,
            "reason": reason,
            "check_items": reg_data.get("check_items", []),
            "overview_simple": reg_data["overview_simple"]
        })

    return results


def get_regulation_summary(regulation_name: str, mode: str = "simple") -> str:
    """規制の概要を取得"""
    if regulation_name not in REGULATIONS:
        return f"{regulation_name}の情報はありません"

    reg = REGULATIONS[regulation_name]

    if mode == "simple":
        return reg["overview_simple"]
    else:
        return reg["overview_detail"]


def get_violation_cases(regulation_name: str, limit: int = 3) -> List[Dict]:
    """違反事例を取得"""
    if regulation_name not in REGULATIONS:
        return []

    cases = REGULATIONS[regulation_name].get("recent_cases", [])
    return cases[:limit]
