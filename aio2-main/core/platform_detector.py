"""
プラットフォーム検出モジュール
HTMLやHTTPヘッダーからWebサイトのプラットフォームを検出
"""

from typing import Dict, Optional

from bs4 import BeautifulSoup


class PlatformDetector:
    """Webサイトのプラットフォームを検出するクラス"""

    PLATFORM_SIGNATURES = {
        "wordpress": [
            "wp-content",
            "wp-includes",
            "WordPress",
            "/wp-json/",
            "wp-embed.min.js",
        ],
        "wix": [
            "wix.com",
            "wixstatic.com",
            "wix-code-sdk",
            "_wix_",
            "wixsite.com",
        ],
        "shopify": [
            "cdn.shopify.com",
            "shopify.com/s/files",
            "Shopify.theme",
            "shopify-features",
        ],
        # Marketplace (seller-controlled fields only)
        "amazon_marketplace": [
            "amazon.co.jp",
            "amazon.com",
            "/dp/",
            "/gp/product/",
        ],
        "rakuten": [
            "rakuten.co.jp",
            "item.rakuten.co.jp",
            "search.rakuten.co.jp",
        ],
        "yahoo_shopping": [
            "shopping.yahoo.co.jp",
            "store.shopping.yahoo.co.jp",
        ],
        "base": [
            "thebase.in",
            "base.shop",
            "baseinc.jp",
        ],
        "studio": [
            "studio.site",
            "studio.design",
        ],
        "jimdo": [
            "jimdo.com",
            "jimdofree.com",
            "jimdosite.com",
        ],
        "peraichi": [
            "peraichi.com",
            "peraichi-user-resource",
        ],
        "stores": [
            "stores.jp",
            "st-hatena.com",
        ],
        "ameba_ownd": [
            "amebaownd.com",
            "ameba.jp/ownd",
        ],
        "goope": [
            "goope.jp",
            "goope-user",
        ],
    }

    def detect(self, html: str, headers: Optional[Dict[str, str]] = None) -> str:
        """
        HTMLとHTTPヘッダーからプラットフォームを検出

        Args:
            html: WebページのHTML
            headers: HTTPレスポンスヘッダー（オプション）

        Returns:
            検出されたプラットフォーム名（例: "wordpress"）
            検出できない場合は "custom"
        """
        if not html:
            return "custom"

        html_lower = html.lower()

        for platform, signatures in self.PLATFORM_SIGNATURES.items():
            for signature in signatures:
                if signature.lower() in html_lower:
                    return platform

        if headers:
            headers_str = " ".join(headers.values()).lower()
            for platform, signatures in self.PLATFORM_SIGNATURES.items():
                for signature in signatures:
                    if signature.lower() in headers_str:
                        return platform

        return "custom"

    def get_platform_info(self, platform: str) -> Dict[str, str]:
        """
        プラットフォームの基本情報を取得

        Args:
            platform: プラットフォーム名

        Returns:
            プラットフォーム情報（名前、難易度など）
        """
        platform_info = {
            "wordpress": {
                "name": "WordPress",
                "difficulty": "easy",
                "method": "プラグイン使用",
            },
            "wix": {
                "name": "Wix",
                "difficulty": "medium",
                "method": "設定画面から",
            },
            "shopify": {
                "name": "Shopify",
                "difficulty": "easy",
                "method": "テーマ編集",
            },
            "amazon_marketplace": {
                "name": "Amazonマーケットプレイス",
                "difficulty": "varies",
                "method": "出品情報の編集（構造化データ/HTMLは不可）",
            },
            "rakuten": {
                "name": "楽天市場",
                "difficulty": "varies",
                "method": "RMSで編集（HTML/CSS/JSは制限あり）",
            },
            "yahoo_shopping": {
                "name": "Yahoo!ショッピング",
                "difficulty": "varies",
                "method": "ストアクリエイターProで編集（HTMLは欄により可/不可）",
            },
            "base": {
                "name": "BASE",
                "difficulty": "hard",
                "method": "HTML編集（制限あり）",
            },
            "custom": {
                "name": "カスタム/不明",
                "difficulty": "varies",
                "method": "HTML直接編集",
            },
        }

        return platform_info.get(platform, platform_info["custom"])
