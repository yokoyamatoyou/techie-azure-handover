# -*- coding: utf-8 -*-
"""ステルスマーケティング規制チェッカー（Phase 03強化版）"""

from typing import Dict, List
from bs4 import BeautifulSoup
import re

from core.evidence_pipeline import (
    normalize_text, HTMLLocator, extract_evidence_snippet,
    generate_issue_id
)


# ============================================================
# パターン定義
# ============================================================

# PR表記の検出パターン
PR_DISCLOSURE_PATTERNS = [
    r"(?:^|\s|【)PR(?:\s|】|$)",
    r"(?:^|\s|【)広告(?:\s|】|$)",
    r"(?:^|\s|【)AD(?:\s|】|$)",
    r"(?:^|\s)sponsored(?:\s|$)",
    r"(?:^|\s|【)プロモーション(?:\s|】|$)",
    r"(?:^|\s|【)タイアップ(?:\s|】|$)",
    r"提供[:：]\s*\S+",
    r"(?:この記事|本記事).*?(?:広告|PR|プロモーション).*?含",
    r"アフィリエイト.*?(?:リンク|広告).*?含",
    r"(?:商品|サービス).*?提供.*?(?:受け|いただ)",
]

# アフィリエイトリンクの検出パターン
AFFILIATE_LINK_PATTERNS = [
    r"a8\.net",
    r"valuecommerce\.com",
    r"accesstrade\.net",
    r"felmat\.net",
    r"afb\.com",
    r"moshimo\.com",
    r"rentracks\.jp",
    r"link-a\.net",
    r"seedapp\.jp",
    r"/aff/",
    r"\?ref=",
    r"\?affiliate",
    r"amazon\.co\.jp.*?tag=",
    r"rakuten\.co\.jp.*?scid=",
]

# アフィリエイトコンテンツの特徴パターン
AFFILIATE_CONTENT_PATTERNS = [
    r"おすすめ\d+選",
    r"(?:人気|売れ筋)?ランキング",
    r"(?:徹底)?比較",
    r"口コミ.*?評判",
    r"実際に.*?(?:使って|試して)みた",
    r"メリット.*?デメリット",
    r"(?:選び方|選ぶポイント)",
    r"こんな人におすすめ",
    r"(?:公式サイト|詳細).*?(?:こちら|はこちら)",
]

# PR表記の位置評価
DISCLOSURE_POSITION_RULES = {
    "excellent": {
        "locations": ["title", "h1", "first_paragraph", "article_top"],
        "description": "最も分かりやすい位置"
    },
    "acceptable": {
        "locations": ["h2", "sidebar_top", "before_content"],
        "description": "許容される位置"
    },
    "insufficient": {
        "locations": ["footer", "small_text", "after_content", "sidebar_bottom"],
        "description": "視認性が不十分な可能性"
    }
}


# ============================================================
# 業界別リスク評価
# ============================================================

STEALTH_MARKETING_RISK_BY_INDUSTRY = {
    "affiliate_media": {"risk": "very_high", "note": "アフィリエイトメディアはステマ規制の主要対象"},
    "cosmetics": {"risk": "high", "note": "化粧品レビュー・体験談は要注意"},
    "food_supplement": {"risk": "high", "note": "健康食品の口コミ・体験談は要注意"},
    "ec_retail": {"risk": "medium", "note": "商品レビューにPR要素がある場合は表記必要"},
    "healthcare": {"risk": "medium", "note": "患者の声・体験談にPR要素がある場合は表記必要"},
    "corporate": {"risk": "low", "note": "コーポレートサイトは通常問題なし"}
}


# ============================================================
# PR表記テンプレート
# ============================================================

PR_DISCLOSURE_TEMPLATES = {
    "affiliate": {
        "recommended": "【PR】この記事には広告・プロモーションが含まれています",
        "minimal": "【PR】",
        "detailed": "※この記事にはアフィリエイトリンクが含まれています。商品をご購入いただくと、当サイトに報酬が発生する場合があります。なお、掲載内容は報酬の有無に関わらず、公平な視点で作成しています。",
        "position": "記事タイトル直下または記事冒頭"
    },
    "sponsored": {
        "recommended": "【タイアップ】この記事は〇〇社との提携により作成しています",
        "minimal": "提供：〇〇社",
        "detailed": "※この記事は〇〇社からの提供を受けて作成しています。記事内容は当サイト編集部の判断に基づいており、〇〇社による事前承認は受けていません。",
        "position": "記事タイトル直下"
    },
    "review": {
        "recommended": "【PR】商品の提供を受けてレビューしています",
        "minimal": "※商品提供あり",
        "detailed": "※この記事で紹介している商品は、〇〇社より無償で提供いただきました。レビュー内容は筆者の正直な感想であり、〇〇社からの指示は受けていません。",
        "position": "記事冒頭"
    },
    "ambassador": {
        "recommended": "【PR】〇〇社のアンバサダーとして投稿しています",
        "minimal": "〇〇社アンバサダー",
        "detailed": "※筆者は〇〇社のブランドアンバサダーとして活動しており、報酬を受け取っています。",
        "position": "記事冒頭またはプロフィール欄"
    }
}


# ============================================================
# メインチェッカークラス
# ============================================================

class StealthMarketingChecker:
    """ステルスマーケティング規制チェッカー（Phase 03強化版）"""

    def __init__(self, html: str, url: str):
        self.html = html
        self.soup = BeautifulSoup(html, 'html.parser')
        self.url = url
        self.text = self.soup.get_text()
        self.locator = HTMLLocator(self.soup)

    def detect_affiliate_content(self) -> Dict:
        """
        アフィリエイトコンテンツの検出（Phase 03強化版）

        Returns:
            {
                "is_affiliate": True,
                "confidence": 0.9,
                "indicators": ["アフィリエイトリンク検出", "比較ランキング形式"],
                "affiliate_links_count": 5,
                "detected_patterns": [...],
                "evidence": [...]
            }
        """
        indicators = []
        affiliate_links_count = 0
        detected_patterns = []
        evidence_list = []

        # アフィリエイトリンクの検出
        for pattern in AFFILIATE_LINK_PATTERNS:
            matches = re.findall(pattern, self.html, re.IGNORECASE)
            affiliate_links_count += len(matches)
            if matches:
                detected_patterns.append({
                    "type": "affiliate_link",
                    "pattern": pattern,
                    "count": len(matches)
                })

        if affiliate_links_count > 0:
            indicators.append(f"アフィリエイトリンク {affiliate_links_count}件検出")

        # コンテンツパターンの検出
        content_score = 0
        for pattern in AFFILIATE_CONTENT_PATTERNS:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                content_score += 1
                evidence = extract_evidence_snippet(self.text, match.group(), 30)
                detected_patterns.append({
                    "type": "content_pattern",
                    "pattern": pattern,
                    "matched_text": match.group()
                })
                evidence_list.append(evidence)

        if content_score >= 3:
            indicators.append(f"アフィリエイト記事の特徴 {content_score}個検出")

        # 信頼度計算
        confidence = 0.0
        if affiliate_links_count > 0:
            confidence += 0.5
        if content_score >= 2:
            confidence += 0.2
        if content_score >= 4:
            confidence += 0.2
        if affiliate_links_count >= 5:
            confidence += 0.1

        is_affiliate = confidence >= 0.5

        return {
            "is_affiliate": is_affiliate,
            "confidence": round(min(confidence, 1.0), 2),
            "indicators": indicators,
            "affiliate_links_count": affiliate_links_count,
            "content_pattern_count": content_score,
            "detected_patterns": detected_patterns,
            "evidence": evidence_list[:5],  # 最大5件
        }

    def check_pr_disclosure(self) -> Dict:
        """
        PR表記の有無と位置をチェック（Phase 03強化版）

        Returns:
            {
                "has_disclosure": True,
                "disclosure_text": "【PR】",
                "position": "h1直下",
                "position_quality": "excellent",
                "visibility_score": 0.95,
                "location_detail": {...},
                "evidence": "..."
            }
        """
        # 優先順位の高い場所から順に検索
        search_locations = [
            ("title", self.soup.find('title'), "titleタグ内", 1.0, "excellent"),
            ("h1", self.soup.find('h1'), "h1見出し内", 1.0, "excellent"),
            ("h2", self.soup.find('h2'), "h2見出し内", 0.9, "excellent"),
        ]

        # 最初の段落
        first_p = self.soup.find('p')
        if first_p:
            search_locations.append(("first_p", first_p, "記事冒頭", 0.9, "excellent"))

        # header内
        header = self.soup.find('header')
        if header:
            search_locations.append(("header", header, "ヘッダー内", 0.85, "acceptable"))

        # article冒頭
        article = self.soup.find('article')
        if article:
            # article内の最初のp
            article_first_p = article.find('p')
            if article_first_p:
                search_locations.append(("article_top", article_first_p, "記事本文冒頭", 0.85, "excellent"))

        for pattern in PR_DISCLOSURE_PATTERNS:
            # 優先順位の高い場所から検索
            for loc_type, element, position_name, base_score, quality in search_locations:
                if element is None:
                    continue

                text_to_search = element.get('content', '') if element.name == 'meta' else element.get_text()
                match = re.search(pattern, text_to_search, re.IGNORECASE)

                if match:
                    location_info = self.locator.locate_text(match.group())
                    evidence = extract_evidence_snippet(text_to_search, match.group(), 30)

                    return {
                        "has_disclosure": True,
                        "disclosure_text": match.group(),
                        "position": position_name,
                        "position_quality": quality,
                        "visibility_score": base_score,
                        "location_detail": location_info,
                        "evidence": evidence,
                        "issue_id": generate_issue_id("stealth_pr", match.group(), position_name),
                    }

            # 全体を検索
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                position = self._determine_position(match.group())
                quality = self._evaluate_position_quality(position)
                location_info = self.locator.locate_text(match.group())
                evidence = extract_evidence_snippet(self.text, match.group(), 30)

                return {
                    "has_disclosure": True,
                    "disclosure_text": match.group(),
                    "position": position,
                    "position_quality": quality,
                    "visibility_score": 0.5 if quality == "insufficient" else 0.8,
                    "location_detail": location_info,
                    "evidence": evidence,
                    "issue_id": generate_issue_id("stealth_pr", match.group(), position),
                }

        return {
            "has_disclosure": False,
            "disclosure_text": None,
            "position": None,
            "position_quality": None,
            "visibility_score": 0.0,
            "location_detail": None,
            "evidence": None,
            "issue_id": None,
        }

    def _determine_position(self, text: str) -> str:
        """テキストの位置を特定"""
        # 簡易的な位置判定
        full_text = self.text
        position = full_text.find(text)
        total_length = len(full_text)

        if total_length == 0:
            return "不明"

        if position < total_length * 0.1:
            return "記事冒頭"
        elif position < total_length * 0.3:
            return "記事前半"
        elif position > total_length * 0.8:
            return "記事末尾"
        else:
            return "記事中盤"

    def _evaluate_position_quality(self, position: str) -> str:
        """位置の品質を評価"""
        excellent_positions = ["titleタグ内", "h1見出し内", "記事冒頭"]
        acceptable_positions = ["記事前半"]

        if position in excellent_positions:
            return "excellent"
        elif position in acceptable_positions:
            return "acceptable"
        else:
            return "insufficient"

    def evaluate_compliance(self) -> Dict:
        """
        総合評価

        Returns:
            {
                "compliance_status": "warning",
                "risk_score": 60,
                "issues": [...],
                "recommendations": [...]
            }
        """
        affiliate_result = self.detect_affiliate_content()
        disclosure_result = self.check_pr_disclosure()

        issues = []
        recommendations = []

        # アフィリエイトコンテンツなのにPR表記がない
        if affiliate_result["is_affiliate"] and not disclosure_result["has_disclosure"]:
            issues.append({
                "severity": "high",
                "issue": "アフィリエイトコンテンツにPR表記がありません",
                "detail": f"アフィリエイトリンク {affiliate_result['affiliate_links_count']}件が検出されましたが、広告表記が見つかりません"
            })
            recommendations.append("記事冒頭に「【PR】」または「広告」の表記を追加してください")

        # PR表記があるが位置が不適切
        elif affiliate_result["is_affiliate"] and disclosure_result["has_disclosure"]:
            if disclosure_result["position_quality"] == "insufficient":
                issues.append({
                    "severity": "medium",
                    "issue": "PR表記の位置が分かりにくい可能性があります",
                    "detail": f"PR表記「{disclosure_result['disclosure_text']}」は{disclosure_result['position']}にありますが、記事冒頭への配置を推奨します"
                })
                recommendations.append("PR表記を記事タイトルまたは冒頭に移動することを推奨します")

        # アフィリエイトでない場合は問題なし
        if not affiliate_result["is_affiliate"]:
            compliance_status = "ok"
            risk_score = 0
        elif not disclosure_result["has_disclosure"]:
            compliance_status = "violation"
            risk_score = 90
        elif disclosure_result["position_quality"] == "insufficient":
            compliance_status = "warning"
            risk_score = 50
        else:
            compliance_status = "ok"
            risk_score = 10

        return {
            "compliance_status": compliance_status,
            "risk_score": risk_score,
            "affiliate_detection": affiliate_result,
            "disclosure_check": disclosure_result,
            "issues": issues,
            "recommendations": recommendations
        }


# ============================================================
# ヘルパー関数
# ============================================================

def get_stealth_marketing_guidance(business_type: str, check_result: Dict) -> Dict:
    """業界別のステマ規制ガイダンスを生成"""

    industry_info = STEALTH_MARKETING_RISK_BY_INDUSTRY.get(
        business_type,
        {"risk": "medium", "note": "業種に応じたPR表記の確認を推奨"}
    )

    guidance = {
        "industry_risk_level": industry_info["risk"],
        "industry_note": industry_info["note"],
        "guidance_simple": "",
        "guidance_detail": "",
        "best_practices": [],
        "violation_examples": []
    }

    if industry_info["risk"] in ["very_high", "high"]:
        guidance["guidance_simple"] = "この業界ではPR表記が特に重要です。アフィリエイトリンクや商品提供がある場合は必ず明記してください。"
        guidance["best_practices"] = [
            "記事タイトルまたは冒頭に「【PR】」を表示",
            "アフィリエイトリンクがある旨を明記",
            "商品提供を受けた場合は「提供：〇〇」を明記"
        ]
    else:
        guidance["guidance_simple"] = "広告・宣伝要素がある場合はPR表記を検討してください。"
        guidance["best_practices"] = [
            "広告要素がある場合は表記を追加",
            "判断に迷う場合は表記を追加（過剰表記は問題なし）"
        ]

    return guidance


def suggest_pr_disclosure(content_type: str, business_type: str = None) -> Dict:
    """適切なPR表記を提案"""

    template = PR_DISCLOSURE_TEMPLATES.get(content_type, PR_DISCLOSURE_TEMPLATES["affiliate"])

    return {
        "recommended_text": template["recommended"],
        "minimal_text": template["minimal"],
        "detailed_text": template["detailed"],
        "recommended_position": template["position"],
        "html_example": f'<p class="pr-notice">{template["recommended"]}</p>',
        "note": "表記は記事を読む前に目に入る位置に配置してください"
    }


def format_stealth_marketing_result(result: Dict, mode: str = "simple") -> Dict:
    """チェック結果のフォーマット"""

    compliance_status = result["compliance_status"]

    if compliance_status == "violation":
        status = "要対応"
        status_color = "danger"
    elif compliance_status == "warning":
        status = "要確認"
        status_color = "warning"
    else:
        status = "問題なし"
        status_color = "success"

    items = []

    # アフィリエイト検出結果
    affiliate = result["affiliate_detection"]
    if affiliate["is_affiliate"]:
        items.append({
            "icon": "ℹ",
            "text": f"PR表記確認が必要なアフィリエイト要素: 検出（信頼度 {int(affiliate['confidence']*100)}%）",
            "subtext": (
                "アフィリエイトがあるだけではなく、PR/広告表記の有無と見やすさを確認します。"
                + (f" 検出元: {'、'.join(affiliate['indicators'])}" if affiliate["indicators"] else "")
            )
        })
    else:
        content_pattern_count = int(affiliate.get("content_pattern_count") or 0)
        if content_pattern_count > 0:
            affiliate_note = (
                f"記事型の表現は{content_pattern_count}件ありますが、既知のASPリンクやアフィリエイトURLは未検出です。"
                "スコア低下/要対応になるのは、広告・PR要素があるのに表記が不足する場合です。"
            )
        else:
            affiliate_note = (
                "既知のASPリンクやアフィリエイトURLは未検出です。"
                "スコア低下/要対応になるのは、広告・PR要素があるのに表記が不足する場合です。"
            )
        items.append({
            "icon": "✓",
            "text": "PR表記が必要なアフィリエイト要素: 未検出",
            "subtext": affiliate_note
        })

    # PR表記結果
    disclosure = result["disclosure_check"]
    if disclosure["has_disclosure"]:
        icon = "✓" if disclosure["position_quality"] == "excellent" else "⚠"
        items.append({
            "icon": icon,
            "text": f"PR表記: 検出「{disclosure['disclosure_text']}」",
            "subtext": f"位置: {disclosure['position']}（{disclosure['position_quality']}）"
        })
    elif affiliate["is_affiliate"]:
        items.append({
            "icon": "✕",
            "text": "PR表記: 未検出",
            "subtext": "アフィリエイト要素があるため、広告であることが分かるPR/広告表記を記事冒頭などに追加してください"
        })

    # 問題点
    for issue in result["issues"]:
        items.append({
            "icon": "⚠" if issue["severity"] == "medium" else "✕",
            "text": issue["issue"],
            "subtext": issue["detail"]
        })

    # テンプレート提案
    template_suggestion = None
    if affiliate["is_affiliate"] and not disclosure["has_disclosure"]:
        template_suggestion = PR_DISCLOSURE_TEMPLATES["affiliate"]["recommended"]

    faq = [
        {
            "question": "ステマ規制とは何ですか？",
            "answer": "2023年10月に施行された規制で、広告であることを隠した宣伝（ステルスマーケティング）を禁止しています。アフィリエイトリンクや商品提供がある記事には「PR」等の表記が必要です。"
        },
        {
            "question": "どこにPR表記を入れればいいですか？",
            "answer": "記事を読む前に目に入る位置（タイトル直下や記事冒頭）に配置してください。記事末尾や小さな文字での表示は不十分とみなされる可能性があります。"
        }
    ]

    return {
        "title": "ステルスマーケティング規制チェック",
        "subtitle": "広告表記の確認（2023年10月施行）",
        "status": status,
        "status_color": status_color,
        "summary": "アフィリエイトの有無だけではなく、広告・PR要素に表記不足がないかを確認します。",
        "items": items,
        "recommendations": result["recommendations"],
        "template_suggestion": template_suggestion,
        "faq": faq if mode == "simple" else []
    }
