# -*- coding: utf-8 -*-
"""景品表示法チェッカー（Phase 03強化版）"""

from typing import Dict, List, Tuple
from bs4 import BeautifulSoup
import re

from core.evidence_pipeline import (
    normalize_text, HTMLLocator, extract_evidence_snippet,
    wrap_check_result, generate_issue_id
)


# ============================================================
# 違反パターン定義（Phase 03拡張）
# ============================================================

# 優良誤認（商品の品質に関する不当表示）
SUPERIORITY_MISREPRESENTATION = {
    "high_risk": [
        {"pattern": r"業界No\.?1|業界ナンバーワン|業界トップ", "reason": "根拠なき最上級表現", "suggestion": "調査機関名・調査時期・調査対象を明記", "consumer_agency_note": "消費者庁が重点的に監視する表現"},
        {"pattern": r"世界初|日本初|業界初|国内初", "reason": "事実確認が必要な表現", "suggestion": "客観的な根拠資料を準備、または表現を変更", "consumer_agency_note": "事実と異なる場合は優良誤認"},
        {"pattern": r"最高級|最上級|最強|最高峰|最先端", "reason": "最上級表現", "suggestion": "具体的な根拠がなければ「高品質」等に変更", "consumer_agency_note": "消費者庁の重点監視対象"},
        {"pattern": r"完全|100%|絶対に?", "reason": "断定的表現", "suggestion": "「ほぼ」「多くの場合」等の表現に変更", "consumer_agency_note": "断定的表現は要注意"},
        {"pattern": r"唯一|オンリーワン|他にない|他社にない", "reason": "独自性の誇張", "suggestion": "「当社独自の」等の表現に変更"},
        {"pattern": r"満足度\s?\d+%", "reason": "調査根拠が必要", "suggestion": "調査方法・対象者数・調査時期を明記", "consumer_agency_note": "根拠資料の合理性を厳格に審査"},
        {"pattern": r"効果実感\s?\d+%", "reason": "調査根拠が必要", "suggestion": "調査方法・対象者数・調査時期を明記", "consumer_agency_note": "根拠資料の合理性を厳格に審査"},
        {"pattern": r"リピート率\s?\d+%", "reason": "調査根拠が必要", "suggestion": "集計方法・対象期間を明記"},
        {"pattern": r"(?:顧客|お客様)満足度\s?(?:第)?1位", "reason": "No.1表示には根拠が必要", "suggestion": "調査機関名・調査時期・調査対象を明記", "consumer_agency_note": "措置命令の対象となりやすい表現"},
    ],
    "medium_risk": [
        {"pattern": r"人気No\.?\d|売上No\.?\d|シェアNo\.?\d", "reason": "順位表現には根拠が必要", "suggestion": "調査出典を明記"},
        {"pattern": r"(?:で|として)話題|SNSで話題|インスタで話題", "reason": "話題性の根拠が必要", "suggestion": "具体的なメディア名・投稿数等を示す"},
        {"pattern": r"医師推奨|専門家推奨|(?:〇〇|.+?)推薦", "reason": "推奨者情報の明示が必要", "suggestion": "推奨者名・人数・資格を明記"},
        {"pattern": r"臨床試験済み|実証済み|科学的に証明", "reason": "試験内容の明示が必要", "suggestion": "試験機関・試験内容・結果を明記"},
        {"pattern": r"特許取得|特許成分|特許技術", "reason": "特許内容の確認が必要", "suggestion": "特許番号を明記"},
        {"pattern": r"(?:医療|美容)関係者.*?使用|愛用", "reason": "推奨表現の確認が必要", "suggestion": "具体的な人数・資格を明記"},
        {"pattern": r"モンドセレクション|○○賞受賞", "reason": "受賞内容の確認が必要", "suggestion": "受賞年度・部門を明記"},
    ],
    "low_risk": [
        {"pattern": r"大人気|好評|話題の", "reason": "曖昧な人気表現", "suggestion": "可能であれば具体的な数値に置き換え"},
        {"pattern": r"高品質|プレミアム|厳選", "reason": "品質表現", "suggestion": "品質基準を示せるとより良い"},
        {"pattern": r"こだわりの|職人の|匠の", "reason": "品質イメージ表現", "suggestion": "具体的なこだわりポイントを示すとより良い"},
    ]
}

# 有利誤認（価格に関する不当表示）- Phase 03拡張
ADVANTAGEOUS_MISREPRESENTATION = {
    "high_risk": [
        {"pattern": r"今だけ.*?(\d+%\s*OFF|割引)", "reason": "期間限定の二重価格", "suggestion": "セール期間を明示、通常販売実績を確認", "consumer_agency_note": "二重価格表示は重点監視対象"},
        {"pattern": r"通常価格.*?円.*?→.*?(?:特別価格|今なら)", "reason": "比較対照価格の適正性", "suggestion": "通常価格での販売実績（8週間以上）を確認", "consumer_agency_note": "有利誤認の典型パターン"},
        {"pattern": r"定価.*?円.*?→.*?円", "reason": "二重価格表示", "suggestion": "定価での販売実績があるか確認", "consumer_agency_note": "二重価格表示は要注意"},
        {"pattern": r"(?:半額|50%OFF|70%OFF|80%OFF)以下?", "reason": "大幅値引き表示の根拠", "suggestion": "元価格での販売実績を確認"},
        {"pattern": r"メーカー希望小売価格.*?円", "reason": "希望小売価格との比較", "suggestion": "実際のメーカー希望小売価格を確認"},
        {"pattern": r"(?:当店|弊社)通常価格", "reason": "自社通常価格の表示", "suggestion": "販売実績を確認（過去8週間以上）", "consumer_agency_note": "自社比較は特に厳格に審査"},
        {"pattern": r"限定\d+(?:個|名|セット).*?(?:価格|円)", "reason": "数量限定の価格表示", "suggestion": "数量制限の実態を確認"},
    ],
    "medium_risk": [
        {"pattern": r"お得|激安|格安|破格|超特価", "reason": "価格優位性の表現", "suggestion": "比較対象を明確に"},
        {"pattern": r"最安値?|底値|地域最安|どこよりも安い", "reason": "最安表現", "suggestion": "調査対象・調査時期を明記"},
        {"pattern": r"送料無料.*?(?:今だけ|期間限定)", "reason": "条件付き送料無料", "suggestion": "適用条件を明確に"},
        {"pattern": r"(?:初回|お試し).*?(?:限定|特別).*?(?:価格|円)", "reason": "初回限定価格", "suggestion": "2回目以降の価格を明確に"},
        {"pattern": r"(?:期間|数量)限定(?:セール|sale|SALE)", "reason": "限定セールの表示", "suggestion": "期間・数量を明確に"},
    ]
}

# 打消し表示の問題 - Phase 03拡張（視認性判定強化）
DISCLAIMER_ISSUES = [
    {"pattern": r"<small[^>]*>.*?(?:個人の感想|効果.*?保証.*?ない|結果.*?異なる).*?</small>", "issue": "打消し表示が小さすぎる可能性", "suggestion": "本文と同程度の文字サイズに", "severity": "high", "consumer_agency_note": "打消し表示の視認性は重点監視対象"},
    {"pattern": r"<span[^>]*(?:font-size:\s*(?:\d|10|11)px|class=\"[^\"]*small)[^>]*>.*?(?:個人の感想|効果|結果)", "issue": "打消し表示のフォントサイズが小さい可能性", "suggestion": "14px以上のフォントサイズを推奨", "severity": "high"},
    {"pattern": r"(?:※|＊)\s*(?:個人の感想|効果.*?保証.*?ない)", "issue": "打消し表示の視認性確認", "suggestion": "訴求表示の近くに、明確に表示", "severity": "medium"},
    {"pattern": r"(?:※|＊)\s*(?:条件|適用外|対象外|一部)", "issue": "条件の視認性確認", "suggestion": "重要な条件は目立つ位置に", "severity": "medium"},
    {"pattern": r"(?:個人差|個人の感想|あくまで個人)", "issue": "打消し表示の位置確認", "suggestion": "効果を訴求する表現の直近に配置", "severity": "low"},
]

# 消費者庁重点監視パターン（Phase 03追加）
CONSUMER_AGENCY_FOCUS_PATTERNS = {
    "no1_claims": {
        "patterns": [r"No\.?1", r"ナンバーワン", r"第1位", r"1位獲得"],
        "note": "No.1表示は消費者庁が特に重視。調査の合理性を厳格に確認される",
        "severity": "high"
    },
    "effect_guarantee": {
        "patterns": [r"確実に", r"必ず", r"100%", r"絶対", r"間違いなく"],
        "note": "効果を保証する表現は優良誤認の可能性が高い",
        "severity": "high"
    },
    "comparison_claims": {
        "patterns": [r"他社.*?(?:比較|より)", r"従来.*?(?:比|品)", r"(?:○○|.+?)社.*?比"],
        "note": "比較広告は比較対象の明示と客観性が必要",
        "severity": "medium"
    },
    "double_price": {
        "patterns": [r"通常.*?円.*?(?:→|⇒|が).*?円", r"定価.*?円.*?特別", r"\d+%\s*(?:OFF|オフ|off)"],
        "note": "二重価格表示は有利誤認の典型。販売実績の確認が必要",
        "severity": "high"
    },
}

# Phase 04追加: No.1表示の文脈判定用パターン
# 品番・型番として使われる場合は除外
SKU_EXCLUSION_PATTERNS = [
    r"(?:品番|型番|Model|SKU|製品番号|カタログ番号|Part\s*No|商品番号|JANコード|型式)\s*[:：]?\s*No\.?\s*\d+",
    r"No\.?\s*\d{2,}",  # No.123 など数字が2桁以上続く場合は品番
    r"[A-Z]{2,}-?No\.?\d+",  # AB-No.1 などのパターン
]

# 広告的文脈を示すキーワード（これらがあればNo.1は広告目的と判定）
ADVERTISING_CONTEXT_KEYWORDS = [
    "売上", "実績", "満足度", "シェア", "人気", "評価", "ランキング", "受賞",
    "顧客", "お客様", "利用者", "ユーザー", "業界", "調査", "部門",
    "獲得", "達成", "連続", "年間", "月間", "週間",
]


# ============================================================
# 業界別チェック強度設定（Phase 03強化）
# ============================================================

INDUSTRY_CHECK_INTENSITY = {
    "ec_retail": {
        "superiority": "strict",
        "price": "strict",
        "disclaimer": "normal",
        "double_price": "very_strict",
        "consumer_agency_focus": ["double_price", "no1_claims"]
    },
    "cosmetics": {
        "superiority": "strict",
        "effect_claims": "very_strict",
        "disclaimer": "strict",
        "consumer_agency_focus": ["effect_guarantee", "no1_claims"]
    },
    "food_supplement": {
        "superiority": "very_strict",
        "effect_claims": "very_strict",
        "disclaimer": "strict",
        "consumer_agency_focus": ["effect_guarantee", "no1_claims", "comparison_claims"]
    },
    "finance": {
        "superiority": "strict",
        "return_claims": "very_strict",
        "disclaimer": "strict",
        "consumer_agency_focus": ["effect_guarantee"]
    },
    "affiliate_media": {
        "superiority": "strict",
        "ranking": "strict",
        "comparison": "strict",
        "consumer_agency_focus": ["no1_claims", "comparison_claims"]
    },
    "healthcare": {
        "superiority": "very_strict",
        "effect_claims": "very_strict",
        "disclaimer": "strict",
        "consumer_agency_focus": ["effect_guarantee", "no1_claims"]
    },
    "corporate": {
        "superiority": "normal",
        "price": "normal",
        "disclaimer": "normal",
        "consumer_agency_focus": []
    }
}

# 強度別の重みづけ
INTENSITY_WEIGHTS = {
    "very_strict": 1.5,
    "strict": 1.2,
    "normal": 1.0,
    "relaxed": 0.8,
    "skip": 0.0
}


def get_check_intensity(business_type: str, check_type: str) -> str:
    """業界別のチェック強度を取得"""
    if business_type not in INDUSTRY_CHECK_INTENSITY:
        return "normal"
    return INDUSTRY_CHECK_INTENSITY[business_type].get(check_type, "normal")


def get_intensity_weight(business_type: str, check_type: str) -> float:
    """業界別の強度の重みを取得"""
    intensity = get_check_intensity(business_type, check_type)
    return INTENSITY_WEIGHTS.get(intensity, 1.0)


def should_check(business_type: str, check_type: str) -> bool:
    """該当チェックを実行すべきか判定"""
    intensity = get_check_intensity(business_type, check_type)
    return intensity != "skip"


def get_consumer_agency_focus(business_type: str) -> List[str]:
    """業界別の消費者庁重点監視項目を取得"""
    if business_type not in INDUSTRY_CHECK_INTENSITY:
        return []
    return INDUSTRY_CHECK_INTENSITY[business_type].get("consumer_agency_focus", [])


# ============================================================
# 改善提案データ
# ============================================================

IMPROVEMENT_SUGGESTIONS = {
    "no1_claim": {
        "simple": "「No.1」表現には調査機関と調査時期の記載が必要です",
        "detail": "景品表示法では、No.1表示には①調査機関名②調査時期③調査範囲の明示が必要とされています。第三者機関による調査結果を引用する場合も、調査方法が適切かどうか確認が必要です。",
        "example_before": "顧客満足度No.1",
        "example_after": "顧客満足度No.1（○○調査会社調べ、2024年1月、○○業界100社対象）"
    },
    "superlative": {
        "simple": "「最高」「最強」等の最上級表現には客観的根拠が必要です",
        "detail": "最上級表現は、客観的に証明できない場合は優良誤認となるリスクがあります。「当社比」「○○部門で」等の限定を加えるか、「高品質」等の表現に変更することを推奨します。",
        "example_before": "最高品質の素材",
        "example_after": "厳選した高品質素材"
    },
    "price_comparison": {
        "simple": "二重価格表示には、比較対照価格での販売実績が必要です",
        "detail": "「通常価格」「定価」等と比較する場合、原則としてその価格で8週間以上の販売実績が必要です。販売実績がない場合は、「メーカー希望小売価格」等との比較も検討してください。",
        "example_before": "通常価格10,000円→特別価格5,000円",
        "example_after": "メーカー希望小売価格10,000円（税込）のところ、5,000円（税込）"
    }
}


# ============================================================
# メインチェッカークラス
# ============================================================

class PremiumsLabelingChecker:
    """景品表示法チェッカー（Phase 03強化版）"""

    def __init__(self, html: str, business_type: str = None):
        self.html = html
        self.soup = BeautifulSoup(html, 'html.parser')
        self.business_type = business_type or "corporate"
        self.text = self.soup.get_text()
        self.locator = HTMLLocator(self.soup)
        self.consumer_agency_focus = get_consumer_agency_focus(self.business_type)

    def check_superiority_misrepresentation(self) -> List[Dict]:
        """
        優良誤認チェック（Phase 03強化版）

        Returns:
            [
                {
                    "risk_level": "high",
                    "matched_text": "業界No.1の実績",
                    "pattern": "業界No.1",
                    "reason": "根拠なき最上級表現",
                    "location": "h2見出し内",
                    "suggestion": "...",
                    "confidence": 0.9,
                    "evidence": "...",
                    "consumer_agency_note": "..."
                }
            ]
        """
        issues = []
        intensity_weight = get_intensity_weight(self.business_type, "superiority")

        for risk_level, patterns in SUPERIORITY_MISREPRESENTATION.items():
            for p in patterns:
                matches = re.finditer(p["pattern"], self.text, re.IGNORECASE)
                for match in matches:
                    location_info = self.locator.locate_text(match.group())
                    evidence = extract_evidence_snippet(self.text, match.group(), 40)

                    # 業種強度に応じて重要度を調整
                    adjusted_risk = self._adjust_risk_level(risk_level, intensity_weight)

                    # 信頼度計算
                    confidence = self._calculate_confidence(match.group(), location_info)

                    issues.append({
                        "issue_id": generate_issue_id("premiums_superiority", match.group(), location_info.get("location", "")),
                        "risk_level": adjusted_risk,
                        "severity": self._risk_to_severity(adjusted_risk),
                        "matched_text": match.group(),
                        "pattern": p["pattern"],
                        "reason": p["reason"],
                        "location": location_info.get("location", "本文内"),
                        "dom_path": location_info.get("dom_path", ""),
                        "suggestion": p["suggestion"],
                        "category": "優良誤認",
                        "confidence": confidence,
                        "evidence": evidence,
                        "consumer_agency_note": p.get("consumer_agency_note", ""),
                    })

        return issues

    def _adjust_risk_level(self, base_risk: str, weight: float) -> str:
        """業種強度に応じてリスクレベルを調整"""
        if weight >= 1.5 and base_risk == "medium_risk":
            return "high_risk"
        elif weight >= 1.2 and base_risk == "low_risk":
            return "medium_risk"
        elif weight <= 0.8 and base_risk == "high_risk":
            return "medium_risk"
        return base_risk

    def _risk_to_severity(self, risk_level: str) -> str:
        """リスクレベルをseverityに変換"""
        mapping = {
            "high_risk": "high",
            "high": "high",
            "medium_risk": "medium",
            "medium": "medium",
            "low_risk": "low",
            "low": "low",
        }
        return mapping.get(risk_level, "medium")

    def _calculate_confidence(self, matched_text: str, location_info: Dict) -> float:
        """検出の信頼度を計算"""
        base_confidence = 0.7

        # 位置による調整
        location_type = location_info.get("location_type", "unknown")
        if location_type in ["title", "h1", "h2"]:
            base_confidence += 0.2
        elif location_type in ["button", "link"]:
            base_confidence += 0.1

        # テキスト長による調整
        if len(matched_text) > 10:
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def check_advantageous_misrepresentation(self) -> List[Dict]:
        """有利誤認チェック（Phase 03強化版）"""
        issues = []
        intensity_weight = get_intensity_weight(self.business_type, "price")

        for risk_level, patterns in ADVANTAGEOUS_MISREPRESENTATION.items():
            for p in patterns:
                matches = re.finditer(p["pattern"], self.text, re.IGNORECASE)
                for match in matches:
                    location_info = self.locator.locate_text(match.group())
                    evidence = extract_evidence_snippet(self.text, match.group(), 40)
                    adjusted_risk = self._adjust_risk_level(risk_level, intensity_weight)

                    issues.append({
                        "issue_id": generate_issue_id("premiums_price", match.group(), location_info.get("location", "")),
                        "risk_level": adjusted_risk,
                        "severity": self._risk_to_severity(adjusted_risk),
                        "matched_text": match.group(),
                        "pattern": p["pattern"],
                        "reason": p["reason"],
                        "location": location_info.get("location", "本文内"),
                        "dom_path": location_info.get("dom_path", ""),
                        "suggestion": p["suggestion"],
                        "category": "有利誤認",
                        "confidence": self._calculate_confidence(match.group(), location_info),
                        "evidence": evidence,
                        "consumer_agency_note": p.get("consumer_agency_note", ""),
                    })

        return issues

    def check_disclaimer_visibility(self) -> List[Dict]:
        """打消し表示の視認性チェック（Phase 03強化版）"""
        issues = []
        intensity_weight = get_intensity_weight(self.business_type, "disclaimer")

        for d in DISCLAIMER_ISSUES:
            matches = re.finditer(d["pattern"], self.html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                matched_text = self._clean_html(match.group())[:100]
                base_severity = d.get("severity", "medium")

                # 視認性スコアを計算
                visibility_score = self._calculate_disclaimer_visibility(match.group())

                issues.append({
                    "issue_id": generate_issue_id("premiums_disclaimer", matched_text, ""),
                    "risk_level": base_severity,
                    "severity": base_severity,
                    "matched_text": matched_text,
                    "issue": d["issue"],
                    "suggestion": d["suggestion"],
                    "category": "打消し表示",
                    "confidence": 0.8,
                    "visibility_score": visibility_score,
                    "consumer_agency_note": d.get("consumer_agency_note", ""),
                })

        return issues

    def _calculate_disclaimer_visibility(self, html_text: str) -> float:
        """打消し表示の視認性スコアを計算"""
        score = 1.0

        # smallタグ内は視認性低
        if re.search(r"<small", html_text, re.IGNORECASE):
            score -= 0.3

        # フォントサイズが小さい
        size_match = re.search(r"font-size:\s*(\d+)px", html_text)
        if size_match and int(size_match.group(1)) < 12:
            score -= 0.3

        # 薄い色
        if re.search(r"color:\s*#[89a-f]{3,6}", html_text, re.IGNORECASE):
            score -= 0.2

        return max(score, 0.0)

    def check_consumer_agency_focus(self) -> List[Dict]:
        """消費者庁重点監視パターンのチェック（Phase 04強化版: 文脈判定追加）"""
        issues = []

        for focus_type in self.consumer_agency_focus:
            if focus_type not in CONSUMER_AGENCY_FOCUS_PATTERNS:
                continue

            focus_config = CONSUMER_AGENCY_FOCUS_PATTERNS[focus_type]
            for pattern in focus_config["patterns"]:
                matches = re.finditer(pattern, self.text, re.IGNORECASE)
                for match in matches:
                    # Phase 04: No.1表示の場合は文脈判定を実施
                    if focus_type == "no1_claims":
                        if self._is_sku_context(match, self.text):
                            continue  # 品番・型番として使われている場合はスキップ
                        if not self._has_advertising_context(match, self.text):
                            continue  # 広告的文脈がなければスキップ

                    location_info = self.locator.locate_text(match.group())
                    issues.append({
                        "issue_id": generate_issue_id(f"consumer_agency_{focus_type}", match.group(), ""),
                        "risk_level": "high_risk",
                        "severity": focus_config.get("severity", "high"),
                        "matched_text": match.group(),
                        "reason": f"消費者庁重点監視項目: {focus_type}",
                        "location": location_info.get("location", "本文内"),
                        "suggestion": focus_config["note"],
                        "category": "消費者庁重点",
                        "confidence": 0.9,
                        "consumer_agency_note": focus_config["note"],
                    })

        return issues

    def _is_sku_context(self, match, text: str) -> bool:
        """Phase 04: マッチが品番・型番の文脈かどうかを判定"""
        start = max(0, match.start() - 30)
        end = min(len(text), match.end() + 30)
        surrounding = text[start:end]

        for pattern in SKU_EXCLUSION_PATTERNS:
            if re.search(pattern, surrounding, re.IGNORECASE):
                return True
        return False

    def _has_advertising_context(self, match, text: str) -> bool:
        """Phase 04: マッチが広告的文脈にあるかどうかを判定"""
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        surrounding = text[start:end]

        for keyword in ADVERTISING_CONTEXT_KEYWORDS:
            if keyword in surrounding:
                return True
        return False

    def _find_location(self, text: str) -> str:
        """テキストの出現場所を特定"""
        # h1-h6内を検索
        for i in range(1, 7):
            for heading in self.soup.find_all(f'h{i}'):
                if text in heading.get_text():
                    return f"h{i}見出し内"

        # title内
        title = self.soup.find('title')
        if title and text in title.get_text():
            return "titleタグ内"

        # meta description内
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        if meta_desc and text in meta_desc.get('content', ''):
            return "meta description内"

        # button内
        for btn in self.soup.find_all(['button', 'a']):
            if text in btn.get_text():
                return "ボタン/リンク内"

        return "本文内"

    def _clean_html(self, html_text: str) -> str:
        """HTMLタグを除去"""
        return re.sub(r'<[^>]+>', '', html_text).strip()

    def run_all_checks(self) -> Dict:
        """
        全チェック実行（Phase 03強化版）

        Returns:
            {
                "risk_score": 75,
                "risk_level": "high",
                "issues": [...],
                "summary": {...},
                "recommendations": [...],
                "business_type": "...",
                "consumer_agency_alerts": [...]
            }
        """
        superiority = self.check_superiority_misrepresentation()
        advantageous = self.check_advantageous_misrepresentation()
        disclaimer = self.check_disclaimer_visibility()
        consumer_agency = self.check_consumer_agency_focus()

        all_issues = superiority + advantageous + disclaimer + consumer_agency

        # リスクスコア計算
        risk_score = self._calculate_risk_score(all_issues)

        # リスクレベル判定
        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"

        # サマリー
        summary = {
            "high_risk_count": len([i for i in all_issues if i.get("risk_level") == "high_risk" or i.get("severity") == "high"]),
            "medium_risk_count": len([i for i in all_issues if i.get("risk_level") == "medium_risk" or i.get("severity") == "medium"]),
            "low_risk_count": len([i for i in all_issues if i.get("risk_level") == "low_risk" or i.get("severity") == "low"]),
            "total_issues": len(all_issues),
            "consumer_agency_focus_count": len(consumer_agency),
        }

        # 推奨事項
        recommendations = self._generate_recommendations(all_issues)

        # 消費者庁アラート（重要な警告）
        consumer_agency_alerts = [
            i for i in all_issues
            if i.get("consumer_agency_note") and i.get("severity") == "high"
        ]

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "issues": all_issues,
            "summary": summary,
            "recommendations": recommendations,
            "business_type": self.business_type,
            "consumer_agency_alerts": consumer_agency_alerts,
        }

    def _calculate_risk_score(self, issues: List[Dict]) -> int:
        """リスクスコア算出（0-100）"""
        score = 0
        for issue in issues:
            risk = issue.get("risk_level", "")
            if risk in ["high", "high_risk"]:
                score += 20
            elif risk in ["medium", "medium_risk"]:
                score += 10
            else:
                score += 3
        return min(score, 100)

    def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """改善推奨事項を生成"""
        recommendations = []

        high_issues = [i for i in issues if i.get("risk_level") in ["high", "high_risk"]]
        if high_issues:
            recommendations.append("【優先対応】高リスクの表現が検出されました。法務・広告審査の確認を推奨します。")

        categories = set(i.get("category") for i in issues)
        if "優良誤認" in categories:
            recommendations.append("優良誤認の可能性がある表現には、客観的な根拠資料の準備をお勧めします。")
        if "有利誤認" in categories:
            recommendations.append("価格表示は、比較対照価格の販売実績を確認してください。")
        if "打消し表示" in categories:
            recommendations.append("打消し表示は訴求表示の近くに、明確に表示してください。")

        return recommendations


# ============================================================
# ヘルパー関数
# ============================================================

def generate_improvement_suggestion(issue: Dict, mode: str = "simple") -> Dict:
    """検出された問題に対する改善提案を生成"""
    matched_text = issue.get("matched_text", "")

    # パターンに基づいて提案を取得
    if re.search(r"No\.?1|ナンバーワン", matched_text, re.IGNORECASE):
        suggestion_data = IMPROVEMENT_SUGGESTIONS.get("no1_claim", {})
    elif re.search(r"最高|最強|最上級", matched_text, re.IGNORECASE):
        suggestion_data = IMPROVEMENT_SUGGESTIONS.get("superlative", {})
    elif re.search(r"通常価格|定価|→", matched_text, re.IGNORECASE):
        suggestion_data = IMPROVEMENT_SUGGESTIONS.get("price_comparison", {})
    else:
        return {
            "issue_summary": f"「{matched_text}」の表現にリスクあり",
            "explanation": issue.get("reason", ""),
            "suggestion": issue.get("suggestion", "法務・広告審査部門にご確認ください")
        }

    return {
        "issue_summary": f"「{matched_text}」の表現にリスクあり",
        "explanation": suggestion_data.get(mode, suggestion_data.get("simple", "")),
        "suggestion": suggestion_data.get("simple", ""),
        "before_after_example": {
            "before": suggestion_data.get("example_before", ""),
            "after": suggestion_data.get("example_after", "")
        }
    }


def format_check_result(result: Dict, mode: str = "simple") -> Dict:
    """チェック結果を表示モードに応じてフォーマット"""

    # Context-adjusted safe/review candidates remain in raw evidence for the
    # engineer view, but must not become a marketer-facing warning or score hit.
    actionable_issues = [
        issue for issue in result.get("issues", [])
        if issue.get("legal_decision", "action_required") == "action_required"
    ]

    # ステータス判定
    if result["risk_level"] == "high":
        status = "要対応"
        status_color = "danger"
    elif result["risk_level"] == "medium":
        status = "要確認"
        status_color = "warning"
    else:
        status = "問題なし"
        status_color = "success"

    # 項目リスト作成
    items = []
    for issue in actionable_issues[:10]:  # 上位10件
        risk = issue.get("risk_level", "")
        if risk in ["high", "high_risk"]:
            icon = "✕"
        elif risk in ["medium", "medium_risk"]:
            icon = "⚠"
        else:
            icon = "ℹ"
        items.append({
            "icon": icon,
            "text": f"「{issue.get('matched_text', '')[:30]}」",
            "subtext": issue.get("reason", issue.get("issue", "")),
            "location": issue.get("location", ""),
            "suggestion": issue.get("suggestion", "")
        })

    # FAQ生成（景品表示法関連）
    faq = [
        {
            "question": "景品表示法に違反するとどうなりますか？",
            "answer": "措置命令（違反の差止め等）が出され、会社名が公表されます。悪質な場合は売上の3%が課徴金として課されます。"
        },
        {
            "question": "「No.1」表現は使えないのですか？",
            "answer": "使えますが、調査機関名・調査時期・調査対象を明記する必要があります。根拠なき表示は優良誤認に該当します。"
        }
    ]

    return {
        "title": "広告表示の法的リスクチェック",
        "subtitle": "景品表示法に基づく確認",
        "status": status,
        "status_color": status_color,
        "score": 100 - result["risk_score"],  # 安全度として表示
        "summary": result["summary"],
        "review_needed_count": result.get("summary", {}).get("review_needed_count", 0),
        "safe_context_count": result.get("summary", {}).get("safe_context_count", 0),
        "items": items,
        "recommendations": result["recommendations"],
        "faq": faq if mode == "simple" else []
    }
