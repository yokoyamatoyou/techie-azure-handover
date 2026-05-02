# -*- coding: utf-8 -*-
"""Industry detection and regulatory compliance utilities."""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from bs4 import BeautifulSoup
import re


# ============================================================
# Phase 2: 事業タイプ定義
# ============================================================

BUSINESS_TYPES = {
    "ec_retail": {
        "name": "EC・小売",
        "regulations": ["特定商取引法", "景品表示法", "消費者契約法"],
        "keywords": {
            "primary": ["カート", "購入", "注文", "商品"],
            "secondary": ["送料", "在庫", "配送", "決済"],
            "specialized": ["ショッピング", "お買い物", "通販"]
        },
        "schema_types": ["Product", "Offer", "ShoppingCart"],
        "platforms": ["shopify", "base", "stores", "makeshop", "colorme", "futureshop"]
    },
    "healthcare": {
        "name": "医療・ヘルスケア",
        "regulations": ["薬機法", "医療広告ガイドライン", "景品表示法"],
        "keywords": {
            "primary": ["治療", "診療", "クリニック", "医師"],
            "secondary": ["予約", "問診", "保険適用", "施術"],
            "specialized": ["内科", "外科", "歯科", "皮膚科", "整形外科"]
        },
        "schema_types": ["MedicalOrganization", "Physician", "MedicalClinic"],
        "platforms": []
    },
    "cosmetics": {
        "name": "化粧品・美容",
        "regulations": ["薬機法", "景品表示法", "ステマ規制"],
        "keywords": {
            "primary": ["美容", "化粧品", "スキンケア", "コスメ"],
            "secondary": ["美白", "保湿", "エイジングケア", "メイク"],
            "specialized": ["エステ", "サロン", "脱毛", "美顔"]
        },
        "schema_types": ["Product", "BeautySalon"],
        "platforms": []
    },
    "food_supplement": {
        "name": "健康食品・サプリメント",
        "regulations": ["薬機法", "健康増進法", "景品表示法", "ステマ規制"],
        "keywords": {
            "primary": ["サプリ", "健康食品", "栄養", "ダイエット"],
            "secondary": ["ビタミン", "ミネラル", "プロテイン", "酵素"],
            "specialized": ["機能性表示食品", "特定保健用食品", "栄養機能食品"]
        },
        "schema_types": ["Product"],
        "platforms": []
    },
    "finance": {
        "name": "金融・保険",
        "regulations": ["金融商品取引法", "景品表示法", "貸金業法", "保険業法"],
        "keywords": {
            "primary": ["投資", "保険", "ローン", "金利"],
            "secondary": ["融資", "審査", "返済", "運用"],
            "specialized": ["FX", "株式", "投資信託", "生命保険", "損害保険"]
        },
        "schema_types": ["FinancialProduct", "BankAccount"],
        "platforms": []
    },
    "real_estate": {
        "name": "不動産",
        "regulations": ["宅建業法", "景品表示法"],
        "keywords": {
            "primary": ["物件", "賃貸", "売買", "マンション"],
            "secondary": ["間取り", "築年数", "駅徒歩", "家賃"],
            "specialized": ["戸建て", "土地", "投資用", "仲介"]
        },
        "schema_types": ["RealEstateAgent", "Apartment", "House"],
        "platforms": ["suumo", "homes", "athome"]
    },
    "recruitment": {
        "name": "人材・求人",
        "regulations": ["職業安定法", "景品表示法"],
        "keywords": {
            "primary": ["求人", "転職", "採用", "年収"],
            "secondary": ["応募", "面接", "正社員", "アルバイト"],
            "specialized": ["エンジニア転職", "看護師求人", "派遣"]
        },
        "schema_types": ["JobPosting", "Organization"],
        "platforms": ["indeed", "rikunabi", "mynavi", "doda"]
    },
    "education": {
        "name": "教育・スクール",
        "regulations": ["景品表示法", "特定商取引法"],
        "keywords": {
            "primary": ["講座", "スクール", "資格", "学習"],
            "secondary": ["受講", "カリキュラム", "認定", "修了"],
            "specialized": ["プログラミングスクール", "英会話", "塾", "予備校"]
        },
        "schema_types": ["Course", "EducationalOrganization"],
        "platforms": []
    },
    "affiliate_media": {
        "name": "アフィリエイト・メディア",
        "regulations": ["景品表示法", "ステマ規制", "著作権法"],
        "keywords": {
            "primary": ["おすすめ", "ランキング", "比較", "口コミ"],
            "secondary": ["レビュー", "評判", "体験談", "選び方"],
            "specialized": ["徹底比較", "〇〇選", "人気ランキング"]
        },
        "schema_types": ["Article", "Review"],
        "platforms": []
    },
    "corporate": {
        "name": "コーポレート",
        "regulations": ["景品表示法"],
        "keywords": {
            "primary": ["会社概要", "事業内容", "採用情報", "お問い合わせ"],
            "secondary": ["代表挨拶", "沿革", "アクセス", "IR"],
            "specialized": ["企業理念", "CSR", "プレスリリース"]
        },
        "schema_types": ["Organization", "LocalBusiness"],
        "platforms": []
    }
}

@dataclass
class RegulatoryWarning:
    """規制違反の警告"""
    word: str
    category: str  # "薬機法", "景品表示法", "医療広告ガイドライン"など
    severity: str  # "high", "medium", "low"
    reason: str
    suggestion: str

@dataclass
class RegulatoryCheckResult:
    """規制チェック結果"""
    applicable_regulations: List[str] = field(default_factory=list)
    warnings: List[RegulatoryWarning] = field(default_factory=list)
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    passed: bool = True

@dataclass
class IndustryAnalysis:
    """業界分析結果"""
    primary_industry: str
    secondary_industries: List[str]
    confidence_score: float
    industry_keywords: List[str]
    specialized_terms: List[str]
    regulatory_indicators: List[str]
    target_audience_clues: List[str]

class IndustryDetector:
    """業界自動判定システム"""

    def __init__(self):
        # 業界キーワード（広告宣伝費比率が高い順＝SEO投資が大きい業界を上位に配置）
        self.industry_keywords = {
            "化粧品・美容": {  # 広告費10-15% ※薬機法対象
                "primary": ["化粧品", "美容", "スキンケア", "コスメ", "メイク", "エステ", "脱毛", "美容院", "ネイル"],
                "secondary": ["基礎化粧品", "美容液", "クレンジング", "ヘアケア", "ボディケア", "美容クリニック"],
                "specialized": ["薬機法", "INCI", "成分表示", "全成分表示", "医薬部外品", "パッチテスト"],
                "regulatory": ["薬機法"],
            },
            "健康食品・サプリメント": {  # 広告費10%+ ※薬機法対象
                "primary": ["サプリメント", "健康食品", "栄養補助", "プロテイン", "ビタミン", "ダイエット"],
                "secondary": ["機能性表示食品", "特定保健用食品", "トクホ", "栄養機能食品", "青汁", "酵素"],
                "specialized": ["薬機法", "景品表示法", "健康増進法", "機能性関与成分", "届出番号"],
                "regulatory": ["薬機法", "景品表示法", "健康増進法"],
            },
            "医療・クリニック": {  # 広告費5-10% ※薬機法対象
                "primary": ["診療", "治療", "医師", "クリニック", "病院", "歯科", "美容外科", "整形"],
                "secondary": ["予防医療", "遠隔診療", "健康診断", "内視鏡", "レーザー", "インプラント"],
                "specialized": ["医療法", "薬機法", "診療報酬", "保険適用", "自由診療", "医療広告ガイドライン"],
                "regulatory": ["医療法", "薬機法"],
            },
            "不動産・住宅": {  # 広告費5-10%
                "primary": ["物件", "賃貸", "売買", "マンション", "戸建て", "土地", "不動産投資", "住宅"],
                "secondary": ["リノベーション", "住宅ローン", "仲介", "賃貸管理", "注文住宅", "中古物件"],
                "specialized": ["重要事項説明", "宅建士", "建ぺい率", "容積率", "登記", "媒介契約"],
                "regulatory": ["宅建業法"],
            },
            "金融・保険": {  # 広告費5-10%
                "primary": ["融資", "投資", "保険", "資産運用", "ローン", "銀行", "証券", "FX"],
                "secondary": ["フィンテック", "ロボアドバイザー", "仮想通貨", "クレジットカード", "キャッシング"],
                "specialized": ["金融商品取引法", "保険業法", "AML", "KYC", "NISA", "iDeCo"],
                "regulatory": ["金融商品取引法", "保険業法"],
            },
            "人材・求人": {  # 広告費5-10%
                "primary": ["求人", "転職", "採用", "人材紹介", "派遣", "エージェント", "キャリア"],
                "secondary": ["新卒採用", "中途採用", "ヘッドハンティング", "リクルーティング", "面接"],
                "specialized": ["職業安定法", "労働者派遣法", "HRtech", "ATS", "リファラル採用"],
                "regulatory": ["職業安定法"],
            },
            "教育・スクール": {  # 広告費5-10%
                "primary": ["学習", "教育", "講座", "スクール", "塾", "資格", "オンライン学習", "予備校"],
                "secondary": ["eラーニング", "プログラミング教室", "英会話", "通信教育", "家庭教師"],
                "specialized": ["LMS", "学習指導要領", "教育訓練給付金", "受講料", "合格率"],
                "regulatory": [],
            },
            "法律・士業": {  # 広告費3-8%
                "primary": ["弁護士", "法律事務所", "弁護士法人", "税理士", "税理士事務所", "司法書士", "司法書士事務所", "行政書士", "行政書士事務所", "社労士", "社会保険労務士", "法律相談", "相続"],
                "secondary": ["債務整理", "離婚", "交通事故", "企業法務", "知的財産", "労務", "顧問弁護士", "法律顧問", "示談交渉"],
                "specialized": ["弁護士法", "税理士法", "着手金", "成功報酬", "法テラス", "受任通知", "内容証明"],
                "regulatory": ["弁護士法"],
            },
            "IT・SaaS": {  # 広告費3-8%
                "primary": ["SaaS", "クラウド", "システム開発", "ソフトウェア", "アプリ", "API", "DX"],
                "secondary": ["業務効率化", "自動化", "データ分析", "セキュリティ", "AI", "IoT"],
                "specialized": ["AWS", "Azure", "Docker", "Kubernetes", "マイクロサービス", "DevOps"],
                "regulatory": [],
            },
            "飲食・フード": {  # 広告費2-5%
                "primary": ["レストラン", "カフェ", "居酒屋", "メニュー", "予約", "テイクアウト", "デリバリー"],
                "secondary": ["グルメ", "食材", "ランチ", "ディナー", "コース", "食べ放題"],
                "specialized": ["HACCP", "食品衛生法", "アレルギー表示", "営業許可", "食品表示法"],
                "regulatory": ["食品衛生法"],
            },
            "小売・EC": {  # 広告費2-5%
                "primary": ["商品", "販売", "通販", "ショッピング", "EC", "ネットショップ", "オンラインストア"],
                "secondary": ["送料", "返品", "ポイント", "セール", "在庫", "配送", "決済"],
                "specialized": ["特定商取引法", "SKU", "LTV", "CVR", "カート離脱", "ROAS"],
                "regulatory": ["特定商取引法"],
            },
            "製造業": {  # 広告費1-3%
                "primary": ["製造", "生産", "工場", "品質管理", "部品", "設備", "加工"],
                "secondary": ["サプライチェーン", "スマートファクトリー", "予知保全", "自動化", "検査"],
                "specialized": ["ISO9001", "QMS", "TPM", "5S", "カイゼン", "JIT", "品質保証"],
                "regulatory": [],
            },
            "建設・建築": {  # 広告費1-3%
                "primary": ["建設", "建築", "施工", "設計", "リフォーム", "工務店", "ハウスメーカー"],
                "secondary": ["BIM", "省エネ", "耐震", "外壁", "屋根", "内装", "外構"],
                "specialized": ["建築基準法", "一級建築士", "施工管理技士", "建設業許可", "構造計算"],
                "regulatory": ["建築基準法"],
            },
        }

    def analyze_industries(self, title: str, content: str, meta_description: str = "") -> IndustryAnalysis:
        combined_text = f"{title} {meta_description} {content}".lower()
        industry_scores = {}
        matched_keywords = {}

        for industry, keywords in self.industry_keywords.items():
            score = 0
            matched = []
            for keyword in keywords["primary"]:
                count = combined_text.count(keyword.lower())
                score += count * 3
                if count > 0:
                    matched.append(keyword)
            for keyword in keywords["secondary"]:
                count = combined_text.count(keyword.lower())
                score += count * 2
                if count > 0:
                    matched.append(keyword)
            for keyword in keywords["specialized"]:
                count = combined_text.count(keyword.lower())
                score += count * 5
                if count > 0:
                    matched.append(keyword)
            industry_scores[industry] = score
            matched_keywords[industry] = matched

        sorted_industries = sorted(industry_scores.items(), key=lambda x: x[1], reverse=True)
        if not sorted_industries or sorted_industries[0][1] == 0:
            return IndustryAnalysis(
                primary_industry="指定なし（自動判定不可）",
                secondary_industries=[],
                confidence_score=0.0,
                industry_keywords=[],
                specialized_terms=[],
                regulatory_indicators=[],
                target_audience_clues=[],
            )

        primary_industry = sorted_industries[0][0]
        primary_score = sorted_industries[0][1]
        secondary_industries = []
        threshold = primary_score * 0.3
        for industry, score in sorted_industries[1:6]:
            if score >= threshold and score > 0:
                secondary_industries.append(f"{industry}({score:.0f})")

        total_words = len(combined_text.split())
        confidence = min(100, (primary_score / max(total_words * 0.1, 1)) * 100)

        target_clues = self._detect_target_audience(combined_text)
        regulatory_indicators = self._detect_regulatory_terms(combined_text)

        return IndustryAnalysis(
            primary_industry=primary_industry,
            secondary_industries=secondary_industries,
            confidence_score=confidence,
            industry_keywords=matched_keywords[primary_industry],
            specialized_terms=matched_keywords[primary_industry],
            regulatory_indicators=regulatory_indicators,
            target_audience_clues=target_clues,
        )

    def _detect_target_audience(self, text: str) -> List[str]:
        audience_patterns = {
            "法人向け": ["企業", "会社", "法人", "ビジネス", "B2B"],
            "個人向け": ["個人", "家庭", "一般", "消費者", "B2C"],
            "専門職向け": ["医師", "弁護士", "税理士", "エンジニア", "専門家"],
            "経営者向け": ["経営者", "社長", "CEO", "役員", "管理職"],
        }
        detected = []
        for audience_type, patterns in audience_patterns.items():
            if any(pattern in text for pattern in patterns):
                detected.append(audience_type)
        return detected

    def _detect_regulatory_terms(self, text: str) -> List[str]:
        regulatory_terms = [
            "薬機法", "医療法", "金融商品取引法", "宅建業法", "建築基準法",
            "個人情報保護法", "食品衛生法", "労働基準法", "GDPR", "ISO",
        ]
        detected = []
        for term in regulatory_terms:
            if term.lower() in text:
                detected.append(term)
        return detected

    def check_regulatory_compliance(self, content: str, industry: str) -> RegulatoryCheckResult:
        """
        業界別の規制コンプライアンスチェック（簡易版・緩め）
        薬機法・景品表示法・医療広告ガイドラインなどの違反可能性を検出
        """
        result = RegulatoryCheckResult()
        content_lower = content.lower()

        # 業界別に適用される規制を特定
        regulatory_industries = {
            "化粧品・美容": ["薬機法"],
            "健康食品・サプリメント": ["薬機法", "景品表示法", "健康増進法"],
            "医療・クリニック": ["医療法", "薬機法", "医療広告ガイドライン"],
        }

        for ind, regs in regulatory_industries.items():
            if ind in industry or industry in ind:
                result.applicable_regulations = regs
                break

        if not result.applicable_regulations:
            result.passed = True
            return result

        # 薬機法NGワード（緩めの判定：明らかに問題のある表現のみ）
        yakujiho_ng_words = {
            "high": [
                # 医薬品的な効能効果を標榜する表現（明確にNG）
                ("治る", "薬機法", "医薬品的な効能効果の標榜は禁止", "「改善が期待できる」等に言い換え"),
                ("治す", "薬機法", "医薬品的な効能効果の標榜は禁止", "「ケアする」等に言い換え"),
                ("完治", "薬機法", "医薬品的な効能効果の標榜は禁止", "使用を避ける"),
                ("根治", "薬機法", "医薬品的な効能効果の標榜は禁止", "使用を避ける"),
                ("万能", "薬機法", "誇大広告に該当する可能性", "使用を避ける"),
                ("奇跡", "薬機法", "誇大広告に該当する可能性", "使用を避ける"),
                ("医師も認めた", "薬機法", "権威付けによる誤認誘導", "具体的なエビデンスを提示"),
            ],
            "medium": [
                # 効能効果を暗示する表現（注意が必要）
                ("若返", "薬機法", "アンチエイジング効果の標榜に注意", "「ハリを与える」等に言い換え"),
                ("シワが消える", "薬機法", "効能効果の標榜に該当", "「シワを目立たなくする」に言い換え"),
                ("シミが消える", "薬機法", "効能効果の標榜に該当", "「シミを防ぐ」に言い換え"),
                ("毛が生える", "薬機法", "医薬品的な効能効果の標榜", "「頭皮環境を整える」に言い換え"),
                ("痩せる", "薬機法", "健康食品での痩身効果の標榜はNG", "「ダイエットをサポート」に言い換え"),
                ("脂肪が燃焼", "薬機法", "身体機能への影響を標榜", "「燃焼系成分配合」に言い換え"),
            ],
            "low": [
                # 注意が必要な表現（文脈によっては問題ない場合も）
                ("効果抜群", "景品表示法", "優良誤認の可能性", "具体的な数値・根拠を併記"),
                ("No.1", "景品表示法", "根拠なしの比較広告は禁止", "調査機関・調査方法を明記"),
                ("業界最高", "景品表示法", "根拠なしの比較広告は禁止", "客観的な根拠を明記"),
                ("絶対に", "景品表示法", "断定的表現は注意", "「多くの方に」等に言い換え"),
            ],
        }

        # 医療広告ガイドラインNGワード
        medical_ng_words = {
            "high": [
                ("100%成功", "医療広告ガイドライン", "誇大広告に該当", "成功率と症例数を正確に記載"),
                ("絶対安全", "医療広告ガイドライン", "リスクの過小表示", "リスク・副作用を適切に記載"),
                ("日本一の技術", "医療広告ガイドライン", "比較広告の禁止", "具体的な実績・資格を記載"),
            ],
            "medium": [
                ("ビフォーアフター", "医療広告ガイドライン", "条件付きで使用可能", "治療内容・リスク・費用を併記"),
                ("患者様の声", "医療広告ガイドライン", "体験談は原則禁止", "治療実績・症例数を使用"),
            ],
        }

        # チェック実行
        for severity, words in yakujiho_ng_words.items():
            for word_data in words:
                word, category, reason, suggestion = word_data
                if word in content_lower or word in content:
                    warning = RegulatoryWarning(
                        word=word,
                        category=category,
                        severity=severity,
                        reason=reason,
                        suggestion=suggestion,
                    )
                    result.warnings.append(warning)
                    if severity == "high":
                        result.high_risk_count += 1
                    elif severity == "medium":
                        result.medium_risk_count += 1
                    else:
                        result.low_risk_count += 1

        # 医療業界の場合は追加チェック
        if "医療" in industry or "クリニック" in industry:
            for severity, words in medical_ng_words.items():
                for word_data in words:
                    word, category, reason, suggestion = word_data
                    if word in content_lower or word in content:
                        warning = RegulatoryWarning(
                            word=word,
                            category=category,
                            severity=severity,
                            reason=reason,
                            suggestion=suggestion,
                        )
                        result.warnings.append(warning)
                        if severity == "high":
                            result.high_risk_count += 1
                        elif severity == "medium":
                            result.medium_risk_count += 1
                        else:
                            result.low_risk_count += 1

        # 判定結果（緩め：highが2つ以上、またはmediumが5つ以上で不合格）
        result.passed = result.high_risk_count < 2 and result.medium_risk_count < 5

        return result


# ============================================================
# Phase 2: 事業タイプ判定関数
# ============================================================

def detect_business_type(html: str, url: str, json_ld: List[Dict] = None) -> Dict:
    """
    サイトの事業タイプを判定

    Args:
        html: HTMLコンテンツ
        url: サイトURL
        json_ld: 検出されたJSON-LDリスト

    Returns:
        {
            "primary_type": "ec_retail",
            "confidence": 0.85,
            "secondary_types": ["affiliate_media"],
            "applicable_regulations": ["特定商取引法", "景品表示法"],
            "detection_reasons": ["Product schema検出", "カートボタン検出"]
        }
    """
    scores = {}
    reasons = {}

    for btype, config in BUSINESS_TYPES.items():
        score, type_reasons = calculate_business_type_score(html, url, json_ld, btype, config)
        scores[btype] = score
        reasons[btype] = type_reasons

    # スコアでソート
    sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if sorted_types[0][1] < 20:
        # スコアが低すぎる場合はcorporateにフォールバック
        return {
            "primary_type": "corporate",
            "confidence": 0.3,
            "secondary_types": [],
            "applicable_regulations": ["景品表示法"],
            "detection_reasons": ["明確な業種特定に至らず、コーポレートサイトとして扱います"]
        }

    primary = sorted_types[0][0]
    primary_score = sorted_types[0][1]

    # 信頼度を正規化（最大100点を想定）
    confidence = min(primary_score / 100, 1.0)

    # セカンダリタイプ（プライマリの70%以上のスコアがあれば）
    secondary = []
    threshold = primary_score * 0.7
    for btype, score in sorted_types[1:3]:
        if score >= threshold and score >= 30:
            secondary.append(btype)

    # 適用規制を収集
    regulations = list(BUSINESS_TYPES[primary]["regulations"])
    for sec_type in secondary:
        for reg in BUSINESS_TYPES[sec_type]["regulations"]:
            if reg not in regulations:
                regulations.append(reg)

    return {
        "primary_type": primary,
        "confidence": round(confidence, 2),
        "secondary_types": secondary,
        "applicable_regulations": regulations,
        "detection_reasons": reasons.get(primary, [])
    }


def calculate_business_type_score(
    html: str,
    url: str,
    json_ld: List[Dict],
    business_type: str,
    config: Dict
) -> Tuple[float, List[str]]:
    """
    特定の事業タイプのスコアを算出

    スコア配分:
    - primaryキーワード: 各+8点（最大32点）
    - secondaryキーワード: 各+4点（最大16点）
    - specializedキーワード: 各+3点（最大9点）
    - Schema.org検出: +20点
    - プラットフォーム検出: +15点
    - URL/ドメインパターン: +8点

    最大: 100点
    """
    score = 0
    reasons = []
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text().lower()
    url_lower = url.lower()

    keywords = config.get("keywords", {})

    # Primaryキーワード（各+8点、最大32点）
    primary_found = 0
    for kw in keywords.get("primary", []):
        if kw.lower() in text:
            primary_found += 1
            if primary_found <= 4:
                score += 8
    if primary_found > 0:
        reasons.append(f"主要キーワード {primary_found}個検出")

    # Secondaryキーワード（各+4点、最大16点）
    secondary_found = 0
    for kw in keywords.get("secondary", []):
        if kw.lower() in text:
            secondary_found += 1
            if secondary_found <= 4:
                score += 4
    if secondary_found > 0:
        reasons.append(f"関連キーワード {secondary_found}個検出")

    # Specializedキーワード（各+3点、最大9点）
    specialized_found = 0
    for kw in keywords.get("specialized", []):
        if kw.lower() in text:
            specialized_found += 1
            if specialized_found <= 3:
                score += 3
    if specialized_found > 0:
        reasons.append(f"専門キーワード {specialized_found}個検出")

    # Schema.org検出（+20点）
    if json_ld:
        schema_types = config.get("schema_types", [])
        for ld in json_ld:
            ld_type = ld.get("@type", "")
            if isinstance(ld_type, list):
                ld_type = ld_type[0] if ld_type else ""
            if ld_type in schema_types:
                score += 20
                reasons.append(f"{ld_type} schema検出")
                break

    # プラットフォーム検出（+15点）
    platforms = config.get("platforms", [])
    for platform in platforms:
        if platform.lower() in html.lower() or platform.lower() in url_lower:
            score += 15
            reasons.append(f"{platform}プラットフォーム検出")
            break

    # URL/ドメインパターン（+8点）
    url_patterns = {
        "ec_retail": [r"shop", r"store", r"cart", r"buy"],
        "healthcare": [r"clinic", r"hospital", r"medical"],
        "real_estate": [r"estate", r"realty", r"property"],
        "recruitment": [r"job", r"career", r"recruit"]
    }
    if business_type in url_patterns:
        for pattern in url_patterns[business_type]:
            if re.search(pattern, url_lower):
                score += 8
                reasons.append(f"URLパターン '{pattern}' 検出")
                break

    return score, reasons


def detect_multiple_business_types(html: str, url: str, json_ld: List[Dict] = None) -> List[Dict]:
    """
    複数の事業タイプを持つサイトに対応

    例: 化粧品ECサイト → [{"type": "cosmetics", ...}, {"type": "ec_retail", ...}]

    Returns:
        [
            {"type": "cosmetics", "confidence": 0.9, "regulations": [...]},
            {"type": "ec_retail", "confidence": 0.85, "regulations": [...]}
        ]
    """
    result = detect_business_type(html, url, json_ld)

    types = [
        {
            "type": result["primary_type"],
            "confidence": result["confidence"],
            "regulations": BUSINESS_TYPES[result["primary_type"]]["regulations"]
        }
    ]

    for sec_type in result.get("secondary_types", []):
        types.append({
            "type": sec_type,
            "confidence": result["confidence"] * 0.8,  # セカンダリは信頼度を下げる
            "regulations": BUSINESS_TYPES[sec_type]["regulations"]
        })

    return types


def merge_regulations(business_types: List[str]) -> List[str]:
    """複数事業タイプの規制を統合・重複排除"""
    regulations = []
    for btype in business_types:
        if btype in BUSINESS_TYPES:
            for reg in BUSINESS_TYPES[btype]["regulations"]:
                if reg not in regulations:
                    regulations.append(reg)
    return regulations
