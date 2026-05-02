# -*- coding: utf-8 -*-
"""特定商取引法チェッカー（Phase 02強化版）"""

import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urljoin

import requests

from bs4 import BeautifulSoup

from core.ui.design_system import LEGAL_ICONS_FALLBACK
from core.config import config
from core.evidence_pipeline import (
    normalize_text, normalize_whitespace,
    HTMLLocator, LabelValueExtractor,
    extract_evidence_snippet, wrap_check_result,
    generate_issue_id, EvidenceItem
)
from core.safe_fetch import safe_fetch_url, SafeFetchError


def augment_html_with_embedded_docs(
    html: str, base_url: str, max_docs: int = 3, timeout: float = config.TIMEOUT_DEFAULT
) -> Tuple[str, List[str]]:
    """同一ドメインのiframe/frame内HTMLを補完して検索漏れを抑える"""
    if not html or not base_url:
        return html, []

    soup = BeautifulSoup(html, "html.parser")
    base = urlparse(base_url)
    sources: List[str] = []
    embedded_html: List[str] = []
    seen = set()

    for tag in soup.find_all(["iframe", "frame"]):
        src = (tag.get("src") or "").strip()
        if not src:
            continue
        if src.startswith("javascript:"):
            continue

        full_url = urljoin(base_url, src)
        parsed = urlparse(full_url)
        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc and parsed.netloc != base.netloc:
            continue
        if full_url in seen:
            continue
        seen.add(full_url)

        try:
            resp = safe_fetch_url(full_url, headers={"User-Agent": config.USER_AGENT}, timeout=timeout)
            if resp.ok and resp.text:
                embedded_html.append(resp.text[:120000])
                sources.append(full_url)
        except SafeFetchError:
            continue
        except Exception:
            continue

        if len(embedded_html) >= max_docs:
            break

    if not embedded_html:
        return html, []

    combined = html + "\n<!-- embedded_documents_start -->\n" + "\n".join(embedded_html) + "\n<!-- embedded_documents_end -->"
    return combined, sources


RELATED_LINK_PATTERNS: List[Tuple[str, int]] = [
    (r"特定商取引|特商法|特定商取引に基づく表記|特定商取引法に基づく表示|法定表記|販売条件", 100),
    (r"返品|返金|交換|キャンセル|返品特約|返品条件|返品ポリシー|返金ポリシー|クーリングオフ", 70),
    (r"配送|送料|お届け|納期|発送|配送方法|お届け日|出荷", 60),
    (r"支払い|決済|お支払い方法|payment|支払方法|支払手段", 60),
    (r"FAQ|よくある質問|Q&A|質問|ヘルプ|サポート", 50),
    (r"会社概要|店舗情報|ショップ情報|会社案内|運営会社|事業者情報|ご利用ガイド|ご利用案内|お買い物ガイド|ショッピングガイド|購入ガイド", 40),
]


def _collect_related_links(html: str, base_url: str, max_links: int = 3) -> List[str]:
    """EC関連リンク（特商法/返品/配送/FAQ等）を上位のみ抽出"""
    if not html or not base_url:
        return []

    soup = BeautifulSoup(html, "html.parser")
    base = urlparse(base_url)
    candidates = {}

    for link in soup.find_all("a", href=True):
        href = (link.get("href") or "").strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        text = normalize_whitespace(link.get_text()).strip()
        if not text:
            title = link.get("title", "") or ""
            text = title.strip()

        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc and parsed.netloc != base.netloc:
            continue

        score = 0
        for pattern, weight in RELATED_LINK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE) or re.search(pattern, full_url, re.IGNORECASE):
                score = max(score, weight)
        if score <= 0:
            continue

        if full_url not in candidates or score > candidates[full_url]:
            candidates[full_url] = score

    ranked = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
    return [url for url, _ in ranked[:max_links]]


def augment_html_with_related_pages(
    html: str, base_url: str, max_pages: int = 2, timeout: float = config.TIMEOUT_DEFAULT
) -> Tuple[str, List[str]]:
    """EC関連ページ（特商法/返品/配送/FAQ）を限定取得して補完"""
    links = _collect_related_links(html, base_url, max_links=max_pages)
    if not links:
        return html, []

    fetched_sources: List[str] = []
    extra_html: List[str] = []
    for link in links:
        try:
            resp = safe_fetch_url(link, headers={"User-Agent": config.USER_AGENT}, timeout=timeout)
            if resp.ok and resp.text:
                extra_html.append(resp.text[:120000])
                fetched_sources.append(link)
        except SafeFetchError:
            continue
        except Exception:
            continue

    if not extra_html:
        return html, []

    combined = html + "\n<!-- related_pages_start -->\n" + "\n".join(extra_html) + "\n<!-- related_pages_end -->"
    return combined, fetched_sources


# ============================================================
# ラベル辞書（Phase 02拡張）
# ============================================================

LABEL_ALIASES = {
    "seller_name": [
        "会社名", "販売業者", "販売業者名", "事業者名", "事業者の名称", "販売者", "販売者名",
        "運営会社", "運営会社名", "運営者", "運営", "販売事業者", "販売事業者名", "販売元",
        "ショップ名", "店舗名", "屋号", "商号", "社名", "法人名", "事業者", "seller", "company"
    ],
    "representative": [
        "代表者", "代表", "責任者", "運営責任者", "運営責任者氏名", "代表取締役", "代表取締役社長",
        "販売責任者", "運営統括責任者", "代表者氏名", "会社代表者", "店長", "管理者", "管理責任者",
        "代表者名", "責任者名", "representative"
    ],
    "address": [
        "住所", "所在地", "本社所在地", "事務所所在地", "本店所在地", "店舗所在地",
        "連絡先住所", "所在地住所", "address", "location"
    ],
    "phone": [
        "電話", "電話番号", "TEL", "Tel", "お電話", "連絡先電話", "連絡先電話番号",
        "お問い合わせ電話", "phone", "telephone"
    ],
    "email": [
        "メール", "メールアドレス", "E-mail", "Email", "Mail",
        "お問い合わせ", "お問い合わせ先", "連絡先メール", "連絡先メールアドレス", "email"
    ],
    "price": [
        "価格", "販売価格", "料金", "金額", "商品価格", "商品代金", "price"
    ],
    "shipping": [
        "送料", "配送料", "配送費", "発送料", "配送料金", "配送手数料", "送料について",
        "配送について", "shipping"
    ],
    "payment_method": [
        "支払方法", "お支払い", "決済方法", "お支払い方法", "お支払方法",
        "支払い方法", "支払手段", "決済手段", "payment"
    ],
    "payment_timing": [
        "支払時期", "支払い時期", "決済時期", "お支払い時期", "支払期限", "お支払い期限",
        "代金の支払時期", "代金支払時期", "payment timing"
    ],
    "delivery_time": [
        "引渡し時期", "引き渡し時期", "発送時期", "配送時期", "発送予定", "出荷時期",
        "お届け時期", "お届け予定", "お届け目安", "納期", "delivery"
    ],
    "return_policy": [
        "返品", "返金", "交換", "キャンセル", "返品特約", "返品条件", "返金条件",
        "返品について", "返品・交換", "返品・交換について", "返品規定", "交換規定",
        "キャンセルポリシー", "返品ポリシー", "返金ポリシー", "クーリングオフ", "return"
    ],
}


# ============================================================
# 必須表示項目定義（Phase 02拡張）
# ============================================================

REQUIRED_ITEMS = {
    "seller_name": {
        "name": "販売業者名",
        "name_simple": "販売者の名前",
        "required": True,
        "legal_basis": "特定商取引法第11条第1項第1号",
        "label_aliases": LABEL_ALIASES["seller_name"],
        "patterns": [
            r"(?:会社名|販売業者|事業者名|販売者|運営会社|運営者|運営|販売事業者|販売元)[:：\s]*(.+?)(?:\n|$|<)",
            r"(?:株式会社|有限会社|合同会社|一般社団法人|合資会社|NPO法人)[\w\u3040-\u30ff\u4e00-\u9fff]+",
        ],
        "ng_patterns": [],
        "hint": "法人名または個人事業主の氏名"
    },
    "representative": {
        "name": "代表者名",
        "name_simple": "責任者の名前",
        "required": False,
        "legal_basis": "特定商取引法第11条第1項第2号（個人の場合）",
        "label_aliases": LABEL_ALIASES["representative"],
        "patterns": [
            r"(?:代表者?|責任者|運営責任者|代表取締役|販売責任者|運営統括責任者|代表者氏名|会社代表者)[:：\s]*(.+?)(?:\n|$|<)",
            r"(?:代表者?|責任者)[:：\s]*([一-龯]{1,4}[\s　]*[一-龯]{1,4})",
        ],
        "name_patterns": [
            r"([一-龯]{1,4})[\s　]+([一-龯]{1,4})",  # 姓 名
            r"([一-龯]{2,4})([一-龯]{1,4})",         # 姓名（空白なし）
        ],
        "hint": "代表者または業務責任者の氏名"
    },
    "address": {
        "name": "所在地",
        "name_simple": "会社の住所",
        "required": True,
        "legal_basis": "特定商取引法第11条第1項第3号",
        "label_aliases": LABEL_ALIASES["address"],
        "patterns": [
            r"〒\d{3}-?\d{4}",
            r"(?:住所|所在地|本社所在地)[:：\s]*(.+?)(?:\n|$|<)",
            r"(?:東京都|北海道|(?:京都|大阪)府|.{2,3}県).+?(?:市|区|町|村).+?(?:\d+|丁目|番地|号)",
        ],
        "address_patterns": [
            r"〒?\d{3}-?\d{4}\s*(.+?)(?:\n|$)",
            r"(?:東京都|北海道|(?:京都|大阪)府|.{2,3}県)[^\n]{5,50}",
        ],
        "hint": "郵便番号を含む完全な住所"
    },
    "phone": {
        "name": "電話番号",
        "name_simple": "電話番号",
        "required": True,
        "legal_basis": "特定商取引法第11条第1項第4号",
        "label_aliases": LABEL_ALIASES["phone"],
        "patterns": [
            r"(?:電話|TEL|Tel|お電話|電話番号)[:：\s]*([\d\-\(\)ー]+)",
            r"0\d{1,4}[\-ー]\d{1,4}[\-ー]\d{4}",
            r"0\d{9,10}",
        ],
        "link_patterns": [
            r"tel:(\+?[\d\-]+)",
        ],
        "ng_patterns": [r"0120", r"0800"],
        "hint": "確実に連絡が取れる電話番号"
    },
    "email": {
        "name": "メールアドレス",
        "name_simple": "メールアドレス",
        "required": True,
        "legal_basis": "特定商取引法第11条第1項第4号",
        "label_aliases": LABEL_ALIASES["email"],
        "patterns": [
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
            r"(?:メール|E-?mail|Mail|お問い?合わせ)[:：\s]*(.+?)(?:\n|$|<)",
        ],
        "link_patterns": [
            r"mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
        ],
        "hint": "お問い合わせ用メールアドレス"
    },
    "price": {
        "name": "販売価格",
        "name_simple": "商品の値段",
        "required": True,
        "legal_basis": "特定商取引法第11条第1項第5号",
        "label_aliases": LABEL_ALIASES["price"],
        "patterns": [
            r"(?:価格|販売価格|料金|金額|商品価格)[:：\s]*",
            r"[\￥¥]\s*[\d,]+",
            r"[\d,]+\s*円",
        ],
        "hint": "税込価格を明示"
    },
    "shipping": {
        "name": "送料",
        "name_simple": "配送にかかる費用",
        "required": True,
        "legal_basis": "特定商取引法第11条第1項第6号",
        "label_aliases": LABEL_ALIASES["shipping"],
        "patterns": [
            r"(?:送料|配送料|配送費|発送料|配送手数料)[:：\s]*",
            r"(?:送料|配送料)(?:無料|込み|別|[\￥¥\d,]+円)",
            r"(?:送料|配送)(?:について|のご案内)",
        ],
        "hint": "送料無料の場合もその旨を明記"
    },
    "payment_method": {
        "name": "支払方法",
        "name_simple": "お支払い方法",
        "required": True,
        "legal_basis": "特定商取引法第11条第1項第7号",
        "label_aliases": LABEL_ALIASES["payment_method"],
        "patterns": [
            r"(?:支払方法|支払手段|お支払い|決済方法|お支払い方法|お支払方法|支払い方法)[:：\s]*",
            r"(?:クレジットカード|銀行振込|代金引換|コンビニ払い|後払い|PayPay|楽天ペイ|Amazon\s?Pay|d払い|au\s?PAY|LINE\s?Pay)",
        ],
        "hint": "利用可能な決済手段を全て列挙"
    },
    "payment_timing": {
        "name": "支払時期",
        "name_simple": "支払いのタイミング",
        "required": True,
        "legal_basis": "特定商取引法第11条第1項第8号",
        "label_aliases": LABEL_ALIASES["payment_timing"],
        "patterns": [
            r"(?:支払時期|支払い時期|決済時期|お支払い時期|支払期限|お支払い期限|代金の支払時期|代金支払時期)[:：\s]*",
            r"(?:注文時|発送時|商品到着後|代引き|後払い).*?(?:決済|支払|引き?落と?し)",
        ],
        "hint": "いつ代金が引き落とされるか"
    },
    "delivery_time": {
        "name": "引渡し時期",
        "name_simple": "届くまでの日数",
        "required": True,
        "legal_basis": "特定商取引法第11条第1項第9号",
        "label_aliases": LABEL_ALIASES["delivery_time"],
        "patterns": [
            r"(?:発送|お届け|配送|納期|引渡し|引き渡し|出荷).*?(?:\d+日|翌日|即日|営業日)",
            r"(?:引渡し時期|引き渡し時期|発送時期|配送時期|発送予定|お届け予定)[:：\s]*",
            r"ご注文.*?(?:\d+日|翌日|即日).*?(?:届|発送)",
        ],
        "hint": "注文からお届けまでの目安日数"
    },
    "return_policy": {
        "name": "返品・交換",
        "name_simple": "返品や交換の条件",
        "required": True,
        "legal_basis": "特定商取引法第15条の3",
        "label_aliases": LABEL_ALIASES["return_policy"],
        "patterns": [
            r"(?:返品|返金|交換|キャンセル).*?(?:可能|不可|できます|できません|条件|受け付け)",
            r"(?:クーリングオフ|返品特約|返品について|返品・交換|返品条件|返金条件|キャンセルポリシー)",
            r"(?:\d+日以内|到着後\d+日)",
        ],
        "hint": "返品可否、条件、期限を明記"
    },
}


# ============================================================
# EC判定
# ============================================================

class ECDetector:
    """ECサイト判定クラス"""

    EC_INDICATORS = {
        "cart_button": {
            "patterns": [
                r"カートに入れる",
                r"カートに追加",
                r"今すぐ購入",
                r"購入する",
                r"買い物かご",
                r"add.to.cart",
                r"add-to-cart",
            ],
            "score": 25
        },
        "price_display": {
            "patterns": [r"[\￥][\d,]+", r"[\d,]+円"],
            "threshold": 5,
            "score": 15
        },
        "product_indicators": {
            "patterns": [r"商品詳細", r"商品説明", r"product", r"item"],
            "score": 10
        },
        "checkout": {
            "patterns": [r"購入手続き", r"注文確認", r"checkout", r"決済", r"お支払い"],
            "score": 20
        },
        "ec_platform": {
            "patterns": [
                r"shopify",
                r"cdn\.shopify",
                r"base\.shop",
                r"thebase\.in",
                r"stores\.jp",
                r"makeshop",
                r"colorme",
                r"futureshop",
                r"ec-cube",
            ],
            "score": 30
        },
    }

    def __init__(self, html: str, url: str, json_ld: List[Dict] = None):
        self.html = html
        self.soup = BeautifulSoup(html, 'html.parser')
        self.url = url
        self.json_ld = json_ld or []
        self.text = self.soup.get_text()

    def calculate_ec_score(self) -> Dict:
        """EC可能性スコアを算出"""
        score = 0
        detected = []

        for indicator_name, config in self.EC_INDICATORS.items():
            patterns = config["patterns"]
            indicator_score = config["score"]
            threshold = config.get("threshold", 1)

            count = 0
            for pattern in patterns:
                matches = re.findall(pattern, self.html, re.IGNORECASE)
                count += len(matches)

            if count >= threshold:
                score += indicator_score
                detected.append(f"{indicator_name}（{count}件）")

        for ld in self.json_ld:
            ld_type = ld.get("@type", "")
            if isinstance(ld_type, list):
                ld_type = ld_type[0] if ld_type else ""
            if ld_type in ["Product", "Offer", "ShoppingCart"]:
                score += 25
                detected.append(f"{ld_type} schema検出")
                break

        if score >= 60:
            confidence = "high"
            is_ec = True
        elif score >= 35:
            confidence = "medium"
            is_ec = True
        else:
            confidence = "low"
            is_ec = False

        return {
            "score": score,
            "is_ec": is_ec,
            "confidence": confidence,
            "detected_indicators": detected,
            "recommendation": "特定商取引法の表示確認を推奨" if is_ec else ""
        }


# ============================================================
# 特商法ページ検出
# ============================================================

# Phase 02拡張: 特商法ページ検出パターン（リンクテキスト用）
TOKUSHOHO_LINK_TEXT_PATTERNS = [
    # 直接的な表現（高優先度）
    r"特定商取引法",
    r"特商法",
    r"特定商取引",
    r"特定商取引に基づく表記",
    r"特定商取引法に基づく表示",
    r"特商法に基づく表示",
    r"特商法に基づく表記",
    r"特商法表記",
    r"法定表記",
    r"販売に関する.*表示",
    r"通信販売.*表示",
    # 間接的な表現
    r"会社概要",
    r"会社情報",
    r"ショップ情報",
    r"店舗情報",
    r"販売者情報",
    r"お買い?物ガイド",
    r"ご利用ガイド",
    r"ご利用案内",
    r"ショッピングガイド",
    r"購入ガイド",
    r"お支払い.*配送",
    r"決済.*配送",
    # 楽天市場特有
    r"会社案内",
    r"店舗案内",
    r"運営会社",
    r"販売店情報",
    r"当店について",
    r"ストア情報",
    r"ショップについて",
    r"店舗概要",
    r"運営者情報",
    r"事業者情報",
    r"インフォメーション",
    r"INFO",
    # 部分一致用
    r"支払い?方法",
    r"配送.*送料",
    r"配送.*返品",
    r"返品.*交換",
    r"返品.*返金",
    # Yahoo!ショッピング特有
    r"返品条件.*販売.*重要事項",
    r"販売に関する.*重要事項",
    r"ストアインフォメーション",
    r"ストアについて",
]

# URL/hrefパターン用
TOKUSHOHO_URL_PATTERNS = [
    r"tokusho",
    r"tokusyo",
    r"tokushoho",
    r"tokutei",
    r"/legal",
    r"company/law",
    r"/law",
    r"/transaction",
    r"/commerce",
    # 楽天市場向け
    r"/info2/",
    r"/info/",
    r"gold/.*(?:company|info|guide|law)",
    r"r10s\.jp.*info",
    # Yahoo!ショッピング向け
    r"/info\.html",
    r"/guide",
    r"store\.shopping\.yahoo\.co\.jp/.+/info",
    r"shopping\.yahoo\.co\.jp/store/.+/info",
    r"_ylpinfo",  # Yahoo特有のinfoパラメータ
    r"/storeinfo",
    r"/sellerinfo",
    # その他モール
    r"/about",
    r"/shop[-_]?info",
]

# 楽天市場の特商法ページ直接URL検出
RAKUTEN_TOKUSHOHO_DIRECT_PATTERNS = [
    r"rakuten\.co\.jp/[^/]+/info2/",
    r"rakuten\.co\.jp/[^/]+/info/",
    r"item\.rakuten\.co\.jp/[^/]+/c/",
]

# Yahoo!ショッピングの特商法ページ直接URL検出
YAHOO_TOKUSHOHO_DIRECT_PATTERNS = [
    r"store\.shopping\.yahoo\.co\.jp/[^/]+/info\.html",
    r"shopping\.yahoo\.co\.jp/store/[^/]+/info",
    r"paypaymall\.yahoo\.co\.jp/store/[^/]+/info",
]


def find_tokushoho_page(soup: BeautifulSoup, base_url: str) -> Dict:
    """特定商取引法ページのリンクを検出（強化版）"""
    from urllib.parse import urljoin

    candidates = []

    # 全リンクを検索
    for link in soup.find_all('a', href=True):
        link_text = normalize_whitespace(link.get_text()).strip()
        href = link.get('href', '')

        # 画像リンクの場合、alt属性やtitle属性もチェック
        img = link.find('img')
        if img:
            alt_text = img.get('alt', '') or ''
            title_text = img.get('title', '') or ''
            link_text = link_text or alt_text or title_text
            # 画像リンクのsrcもヒントになる場合がある
            img_src = img.get('src', '') or ''
            if not link_text and ('info' in img_src.lower() or 'guide' in img_src.lower()):
                link_text = "情報ページ"

        # title属性もチェック
        if not link_text:
            link_text = link.get('title', '') or ''

        score = 0
        matched_pattern = None

        # リンクテキストでマッチ
        for pattern in TOKUSHOHO_LINK_TEXT_PATTERNS:
            if re.search(pattern, link_text, re.IGNORECASE):
                # 「特定商取引」「特商法」は高スコア
                if "特定商取引" in pattern or "特商法" in pattern:
                    score += 100
                else:
                    score += 50
                matched_pattern = pattern
                break

        # URLパターンでマッチ
        for pattern in TOKUSHOHO_URL_PATTERNS:
            if re.search(pattern, href, re.IGNORECASE):
                # info2は楽天の特商法ページなので高スコア
                if "info2" in pattern:
                    score += 90
                else:
                    score += 40
                if not matched_pattern:
                    matched_pattern = pattern
                break

        if score > 0:
            # URL正規化
            if href.startswith('/'):
                full_url = urljoin(base_url, href)
            elif href.startswith('http'):
                full_url = href
            elif href.startswith('#'):
                continue  # ページ内リンクはスキップ
            elif href:
                full_url = urljoin(base_url, href)
            else:
                continue

            candidates.append({
                "url": full_url,
                "link_text": link_text[:50],
                "location": _get_link_location(link),
                "score": score,
                "pattern": matched_pattern,
            })

    # 楽天市場/Yahoo!ショッピングの場合、HTML内に直接特商法URLが埋め込まれている場合もチェック
    html_str = str(soup)

    # 楽天市場
    for pattern in RAKUTEN_TOKUSHOHO_DIRECT_PATTERNS:
        match = re.search(pattern, html_str, re.IGNORECASE)
        if match:
            found_url = match.group()
            if not any(found_url in c.get("url", "") for c in candidates):
                candidates.append({
                    "url": f"https://www.{found_url}" if not found_url.startswith("http") else found_url,
                    "link_text": "特商法ページ（自動検出・楽天）",
                    "location": "HTML内",
                    "score": 80,
                    "pattern": pattern,
                })

    # Yahoo!ショッピング
    for pattern in YAHOO_TOKUSHOHO_DIRECT_PATTERNS:
        match = re.search(pattern, html_str, re.IGNORECASE)
        if match:
            found_url = match.group()
            if not any(found_url in c.get("url", "") for c in candidates):
                candidates.append({
                    "url": f"https://{found_url}" if not found_url.startswith("http") else found_url,
                    "link_text": "特商法ページ（自動検出・Yahoo）",
                    "location": "HTML内",
                    "score": 80,
                    "pattern": pattern,
                })

    # スコア順にソートして最も信頼性の高いものを返す
    if candidates:
        best = max(candidates, key=lambda x: x["score"])
        return {
            "found": True,
            "url": best["url"],
            "link_text": best["link_text"],
            "location": best["location"],
            "confidence": min(best["score"] / 100, 1.0),
            "all_candidates": candidates[:5],  # 上位5件
        }

    return {
        "found": False,
        "url": None,
        "link_text": None,
        "location": None,
        "confidence": 0.0,
        "all_candidates": [],
    }


def _get_link_location(link) -> str:
    """リンクの配置場所を特定（強化版）"""
    # サイドバー/左カラム検出用パターン
    SIDEBAR_PATTERNS = [
        "sidebar", "side-bar", "side_bar",
        "sidenav", "side-nav", "side_nav",
        "left", "leftcolumn", "left-column", "left_column",
        "leftside", "left-side", "left_side",
        "sub", "subcolumn", "sub-column", "sub_column",
        "aside", "secondary", "secondary-content",
        "menu", "shop-menu", "shop_menu", "shopmenu",
        "navi", "navigation", "nav-menu", "nav_menu",
        "category", "categories",
        # 楽天市場特有
        "rnkRanking", "item-navi", "item_navi",
        "shopinfo", "shop-info", "shop_info",
        "sideContents", "side-contents", "side_contents",
        "leftContents", "left-contents", "left_contents",
        # Yahoo!ショッピング特有
        "yjw", "yshopping", "elStore", "storeInfo",
        "mdLeftNavi", "mdRightNavi", "mdSubNavi",
        "yjShopping", "shpMain", "shpSide",
        "SearchHeader", "h_nav", "storeDesign",
        "StoreHeader", "StoreSide", "StoreNav",
    ]

    parent = link.parent
    depth = 0
    max_depth = 15  # 深すぎる探索を防止

    while parent and depth < max_depth:
        tag_name = parent.name if parent.name else ""
        classes = parent.get('class', []) or []
        element_id = parent.get('id', '') or ''

        # タグ名チェック
        if tag_name == 'footer':
            return "フッター"
        if tag_name == 'header':
            return "ヘッダー"
        if tag_name == 'nav':
            return "ナビゲーション"
        if tag_name == 'aside':
            return "サイドバー"

        # クラス名とIDでサイドバーパターンをチェック
        class_str = ' '.join(classes).lower() if classes else ''
        id_str = element_id.lower()

        for pattern in SIDEBAR_PATTERNS:
            if pattern in class_str or pattern in id_str:
                return "サイドバー（左カラム）"

        parent = parent.parent
        depth += 1

    return "本文内"


# ============================================================
# 特商法チェッカー
# ============================================================

class CommercialTransactionChecker:
    """特定商取引法チェッカー（Phase 02強化版）"""

    def __init__(self, html: str, url: str, is_ec: bool = None):
        self.html = html
        self.soup = BeautifulSoup(html, 'html.parser')
        self.url = url
        self.text = self.soup.get_text()
        self.is_ec = is_ec
        self.locator = HTMLLocator(self.soup)
        self.label_extractor = LabelValueExtractor(self.soup)
        self._dom_pairs = None  # キャッシュ

    def _get_dom_pairs(self) -> List[Dict]:
        """DOM構造からラベル-値ペアを取得（キャッシュ付き）"""
        if self._dom_pairs is None:
            self._dom_pairs = self.label_extractor.extract_all()
        return self._dom_pairs

    def check_required_items(self) -> Dict:
        """必須項目のチェック（Phase 02強化版）"""
        results = []
        dom_pairs = self._get_dom_pairs()

        for item_id, config in REQUIRED_ITEMS.items():
            # 複数の検出方法を試行し、最も信頼度の高い結果を採用
            candidates = []

            # 1. DOM構造からラベル-値で検索
            label_aliases = config.get("label_aliases", [])
            for pair in dom_pairs:
                label = normalize_text(pair['label']).lower()
                for alias in label_aliases:
                    if alias.lower() in label:
                        candidates.append({
                            "value": pair['value'],
                            "source": f"DOM({pair['source']})",
                            "confidence": 0.9 if pair['source'] == 'table' else 0.8
                        })
                        break

            # 2. 正規表現パターンで検索
            for pattern in config["patterns"]:
                matches = list(re.finditer(pattern, self.text, re.IGNORECASE | re.MULTILINE))
                for match in matches:
                    value = match.group()[:100] if match.group() else None
                    if value:
                        candidates.append({
                            "value": value,
                            "source": "regex",
                            "confidence": 0.7
                        })

            # 3. tel:/mailto:リンクから検索
            if "link_patterns" in config:
                for link_pattern in config["link_patterns"]:
                    for match in re.finditer(link_pattern, self.html, re.IGNORECASE):
                        value = match.group(1) if match.groups() else match.group()
                        candidates.append({
                            "value": value,
                            "source": "link",
                            "confidence": 0.85
                        })

            # 4. 特殊パターン（名前、住所など）
            if item_id == "representative" and "name_patterns" in config:
                for name_pattern in config["name_patterns"]:
                    for match in re.finditer(name_pattern, self.text):
                        candidates.append({
                            "value": match.group(),
                            "source": "name_pattern",
                            "confidence": 0.6
                        })

            if item_id == "address" and "address_patterns" in config:
                for addr_pattern in config["address_patterns"]:
                    for match in re.finditer(addr_pattern, self.text):
                        candidates.append({
                            "value": match.group(),
                            "source": "address_pattern",
                            "confidence": 0.75
                        })

            # 最も信頼度の高い候補を選択
            best_candidate = None
            if candidates:
                # NGパターンでフィルタ
                if "ng_patterns" in config:
                    candidates = [
                        c for c in candidates
                        if not any(re.search(ng, c["value"]) for ng in config["ng_patterns"])
                    ]

                if candidates:
                    best_candidate = max(candidates, key=lambda x: x["confidence"])

            # 結果を構築
            if best_candidate:
                status = "found"
                detected_value = best_candidate["value"]
                confidence = best_candidate["confidence"]
                source = best_candidate["source"]
            else:
                status = "not_found"
                detected_value = None
                confidence = 0.0
                source = None

            # 位置情報を取得
            location_info = self.locator.locate_text(detected_value) if detected_value else {}

            results.append({
                "id": item_id,
                "name": config["name"],
                "name_simple": config["name_simple"],
                "required": config["required"],
                "status": status,
                "detected_value": detected_value,
                "hint": config["hint"],
                "legal_basis": config.get("legal_basis", ""),
                # Phase 01/02 追加フィールド
                "confidence": confidence,
                "source": source,
                "location": location_info.get("location", ""),
                "evidence": extract_evidence_snippet(self.text, detected_value) if detected_value else "",
                "issue_id": generate_issue_id("tokushoho", item_id, detected_value or ""),
            })

        found_count = len([r for r in results if r["status"] == "found"])
        required_count = len([r for r in results if r["required"]])
        required_found = len([r for r in results if r["required"] and r["status"] == "found"])

        return {
            "items": results,
            "found_count": found_count,
            "total_count": len(results),
            "required_count": required_count,
            "required_found": required_found,
            "compliance_rate": round(required_found / required_count, 2) if required_count > 0 else 0
        }

    def generate_compliance_report(self) -> Dict:
        """コンプライアンスレポート生成"""
        check_result = self.check_required_items()

        missing_required = [
            item for item in check_result["items"]
            if item["required"] and item["status"] != "found"
        ]

        if len(missing_required) == 0:
            status = "compliant"
            risk_level = "low"
        elif len(missing_required) <= 2:
            status = "partial"
            risk_level = "medium"
        else:
            status = "non_compliant"
            risk_level = "high"

        recommendations = []
        for item in missing_required:
            recommendations.append(f"「{item['name_simple']}」を追加してください（{item['hint']}）")

        return {
            "status": status,
            "risk_level": risk_level,
            "missing_items": [item["name_simple"] for item in missing_required],
            "check_result": check_result,
            "recommendations": recommendations
        }


# ============================================================
# 改善提案テンプレート
# ============================================================

TOKUSHOHO_TEMPLATE = """【特定商取引法に基づく表記】

■ 販売業者名
{seller_name}

■ 運営責任者
{representative}

■ 所在地
{address}

■ 電話番号
{phone}

■ メールアドレス
{email}

■ 販売価格
各商品ページに記載

■ 商品代金以外の必要料金
送料: {shipping}
決済手数料: なし

■ お支払い方法
{payment_method}

■ お支払い時期
{payment_timing}

■ 商品の引渡し時期
{delivery_time}

■ 返品・交換について
{return_policy}
"""


def generate_template_suggestion(detected_items: Dict) -> str:
    """検出された情報を元にテンプレートを生成"""
    template_values = {
        "seller_name": "【販売業者名を入力】",
        "representative": "【責任者名を入力】",
        "address": "【住所を入力】",
        "phone": "【電話番号を入力】",
        "email": "【メールアドレスを入力】",
        "shipping": "全国一律○○円（税込）/ ○○円以上のご注文で送料無料",
        "payment_method": "クレジットカード（VISA, Mastercard, JCB, AMEX）、銀行振込、代金引換",
        "payment_timing": "クレジットカード: ご注文時 / 銀行振込: ご注文後7日以内 / 代金引換: 商品お届け時",
        "delivery_time": "ご注文から3-5営業日以内に発送",
        "return_policy": "商品到着後7日以内にご連絡ください。お客様都合の場合は送料をご負担いただきます。不良品の場合は送料当社負担で交換いたします。"
    }

    for item in detected_items.get("items", []):
        if item["status"] == "found" and item.get("detected_value"):
            item_id = item["id"]
            if item_id in template_values:
                template_values[item_id] = item["detected_value"]

    return TOKUSHOHO_TEMPLATE.format(**template_values)


# ============================================================
# 結果フォーマット
# ============================================================

def format_commercial_transaction_result(
    result: Dict,
    ec_detection: Dict,
    mode: str = "simple",
    visibility_issues: Optional[List[Dict]] = None,
) -> Dict:
    """表示用フォーマット"""
    compliance_status = result["status"]
    ec_confidence = ec_detection.get("confidence", "low")
    is_ec = ec_detection.get("is_ec", False)

    if compliance_status == "compliant":
        status = "問題なし"
        status_color = "success"
    elif compliance_status == "partial":
        status = "一部未記載"
        status_color = "warning"
    else:
        status = "要対応"
        status_color = "danger"

    ec_notice = ""
    if not is_ec and ec_confidence == "low":
        status = "参考"
        status_color = "info"
        ec_notice = "EC可能性が低いため参考表示です。EC運営の場合は確認してください。"

    items = []
    recommendations = list(result.get("recommendations", []) or [])
    if ec_notice:
        recommendations = []

    for item in result["check_result"]["items"]:
        if item["status"] == "found":
            icon = LEGAL_ICONS_FALLBACK["compliant"]
            text = f"{item['name_simple']}: 検出"
        elif item["status"] == "partial":
            icon = LEGAL_ICONS_FALLBACK["warning"]
            text = f"{item['name_simple']}: 条件付き検出"
        else:
            icon = LEGAL_ICONS_FALLBACK["error"] if item["required"] else LEGAL_ICONS_FALLBACK["info"]
            text = f"{item['name_simple']}: 未検出"

        items.append({
            "icon": icon,
            "text": text,
            "required": item["required"],
            "hint": item["hint"] if item["status"] != "found" else ""
        })

    legal_small_font = []
    for issue in (visibility_issues or []):
        if issue.get("type") == "small_font_legal":
            legal_small_font.append(issue)
    if legal_small_font:
        items.append(
            {
                "icon": LEGAL_ICONS_FALLBACK["warning"],
                "text": "規約・重要情報の文字サイズが小さい可能性",
                "required": False,
                "hint": "特商法/返品/配送/FAQの文字サイズを見直してください。",
            }
        )
        recommendations.append("規約・重要情報の文字サイズを12px以上に調整してください。")

    faq = [
        {
            "question": "特定商取引法の表示は必須ですか？",
            "answer": "通信販売を行う場合は法的に必須です。表示がない場合、業務改善指示や業務停止命令の対象となる可能性があります。"
        },
        {
            "question": "どこに表示すればいいですか？",
            "answer": "「特定商取引法に基づく表記」という専用ページを作成し、フッター等からリンクするのが一般的です。"
        }
    ]

    return {
        "title": "特定商取引法チェック",
        "subtitle": "ECサイトに必要な法定表示の確認",
        "ec_detection": {
            "is_ec": ec_detection.get("is_ec", False),
            "confidence": ec_detection.get("confidence", "low"),
            "note": "ECサイトの可能性が高いため、以下の表示が法的に必要です" if ec_detection.get("is_ec") else ""
        },
        "ec_notice": ec_notice,
        "status": status,
        "status_color": status_color,
        "compliance_rate": result["check_result"]["compliance_rate"],
        "items": items,
        "missing_items_simple": result["missing_items"],
        "recommendations": recommendations,
        "faq": faq if mode == "simple" else []
    }
