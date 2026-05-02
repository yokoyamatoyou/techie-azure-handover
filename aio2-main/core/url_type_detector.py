import json
import re
from bs4 import BeautifulSoup


class URLTypeDetector:
    def __init__(self) -> None:
        self.corporate_keywords = [
            "about",
            "company",
            "ir",
            "careers",
            "recruit",
            "会社概要",
            "採用",
            "沿革",
            "プライバシー",
            "お問い合わせ",
            "企業情報",
            "事業内容",
            "法人",
        ]
        self.ec_platform_patterns = [
            r"shopify",
            r"cdn\.shopify",
            r"base\.shop",
            r"thebase\.in",
            r"stores\.jp",
            r"makeshop",
            r"colorme",
            r"futureshop",
            r"ec-cube",
        ]
        self.ec_link_text_patterns = [
            r"特定商取引法",
            r"特商法",
            r"特定商取引に基づく表記",
            r"カートに入れる",
            r"カートに追加",
            r"今すぐ購入",
            r"購入する",
            r"買い物かご",
            r"購入手続き",
            r"注文確認",
            r"お買い物ガイド",
            r"ショッピングガイド",
        ]
        self.ec_path_patterns = [
            r"/cart",
            r"/checkout",
            r"/products?/",
            r"/product/",
            r"/item/",
            r"/shop/",
            r"/store/",
            r"tokusho",
            r"tokutei",
        ]
        self.ec_support_terms = [
            "送料",
            "返品",
            "交換",
            "配送",
            "在庫",
            "sku",
            "shopping cart",
            "add to cart",
            "checkout",
        ]
        self.price_patterns = [
            r"[\u00a5￥][\d,]+",
            r"[\d,]+円(?:税込|税抜)?",
        ]
        self.non_ec_price_context_patterns = [
            r"希望小売価格",
            r"メーカー希望小売価格",
            r"参考価格",
            r"相談料",
            r"着手金",
            r"成功報酬",
            r"顧問料",
            r"料金表",
            r"手数料",
            r"月額",
            r"年額",
            r"年会費",
            r"利率",
            r"金利",
            r"診療報酬",
            r"自由診療",
        ]

    def _count_pattern_matches(self, text: str, patterns: list[str]) -> int:
        return sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in patterns)

    def _extract_json_ld(self, soup: BeautifulSoup) -> list[dict]:
        payloads: list[dict] = []
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            raw = script.string or script.get_text() or ""
            raw = raw.strip()
            if not raw:
                continue
            try:
                parsed = json.loads(raw)
            except Exception:
                continue
            if isinstance(parsed, list):
                payloads.extend(item for item in parsed if isinstance(item, dict))
            elif isinstance(parsed, dict):
                if isinstance(parsed.get("@graph"), list):
                    payloads.extend(item for item in parsed["@graph"] if isinstance(item, dict))
                payloads.append(parsed)
        return payloads

    def detect(self, html: str) -> str:
        html = html or ""
        html_lower = html.lower()
        soup = BeautifulSoup(html, "html.parser")
        visible_text = soup.get_text(" ", strip=True)
        visible_text_lower = visible_text.lower()

        corporate_score = sum(1 for keyword in self.corporate_keywords if keyword.lower() in html_lower)

        ec_score = 0

        # 明確なEC導線
        ec_score += self._count_pattern_matches(html_lower, self.ec_platform_patterns) * 4
        ec_score += self._count_pattern_matches(html_lower, self.ec_path_patterns) * 3
        ec_score += self._count_pattern_matches(visible_text_lower, self.ec_link_text_patterns) * 3

        # 送料/返品/配送などは補助証拠としてのみ扱う
        support_term_hits = sum(1 for term in self.ec_support_terms if term.lower() in html_lower)
        if support_term_hits >= 2:
            ec_score += 2

        # 金額表示はそれ単体でEC判定に使わない。
        price_hits = self._count_pattern_matches(visible_text, self.price_patterns)
        non_ec_price_hits = self._count_pattern_matches(visible_text, self.non_ec_price_context_patterns)
        if price_hits >= 5 and non_ec_price_hits == 0 and support_term_hits >= 2:
            ec_score += 1

        # 構造化データは強い証拠
        for payload in self._extract_json_ld(soup):
            schema_type = payload.get("@type", "")
            if isinstance(schema_type, list):
                schema_values = [str(item) for item in schema_type]
            else:
                schema_values = [str(schema_type)]
            if any(value in {"Product", "Offer", "AggregateOffer", "ShoppingCart"} for value in schema_values):
                ec_score += 4
                break

        # 実フォーム/ボタンも強い証拠
        button_text = " ".join(node.get_text(" ", strip=True) for node in soup.find_all(["button", "a"]))
        button_text_lower = button_text.lower()
        if any(term in button_text_lower for term in ["カートに入れる", "カートに追加", "今すぐ購入", "購入する", "add to cart", "buy now"]):
            ec_score += 4
        if any(term in button_text_lower for term in ["購入手続き", "注文確認", "checkout"]):
            ec_score += 3

        if ec_score >= 5 and corporate_score >= 2:
            return "企業（EC機能あり）"
        if ec_score >= 5:
            return "EC"
        if corporate_score >= 2:
            return "企業"
        return "その他"
