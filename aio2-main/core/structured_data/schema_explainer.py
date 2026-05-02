# -*- coding: utf-8 -*-
"""構造化データの説明ヘルパー"""

from typing import Dict


SCHEMA_EXPLANATIONS = {
    "Product": {
        "what_is": {
            "simple": "商品の情報（名前、価格、在庫など）を検索エンジンに伝える設定",
            "detail": "Schema.orgのProduct型は、ECサイトの商品情報を伝えるための標準規格です。"
        },
        "benefit": {
            "simple": "Google検索結果に価格・評価・在庫状況が表示されるようになります",
            "visual": "検索結果の価格・評価が目立つ表示になります"
        },
        "how_to_add": {
            "wordpress": "Yoast SEOまたはRank Mathプラグインで設定可能",
            "shopify": "Shopifyテーマに標準搭載されていることが多い",
            "manual": "HTMLの<head>内等にJSON-LDを追加"
        }
    },
    "Article": {
        "what_is": {
            "simple": "記事のタイトル・著者・公開日を伝える設定",
            "detail": "Article型はニュースやブログ記事の情報を検索エンジンに伝えるための標準規格です。"
        },
        "benefit": {
            "simple": "記事の公開日や著者情報が表示されやすくなります",
            "visual": "検索結果で記事情報が分かりやすくなります"
        },
        "how_to_add": {
            "wordpress": "記事投稿時にSEOプラグインで自動設定されることが多い",
            "manual": "HTMLの<head>内等にJSON-LDを追加"
        }
    },
    "LocalBusiness": {
        "what_is": {
            "simple": "店舗の住所・営業時間・電話番号を伝える設定",
            "detail": "LocalBusiness型は店舗や施設の基本情報を検索エンジンに伝えます。"
        },
        "benefit": {
            "simple": "地図検索での視認性が上がります",
            "visual": "Googleマップや検索結果で情報が表示されます"
        },
        "how_to_add": {
            "manual": "HTMLの<head>内等にJSON-LDを追加"
        }
    }
}


def get_schema_explanation(schema_type: str, mode: str = "simple") -> Dict:
    """構造化データの説明を取得"""
    explanation = SCHEMA_EXPLANATIONS.get(schema_type, {})
    if not explanation:
        return {}

    return {
        "what_is": explanation.get("what_is", {}).get(mode, explanation.get("what_is", {}).get("simple", "")),
        "benefit": explanation.get("benefit", {}).get(mode, explanation.get("benefit", {}).get("simple", "")),
        "how_to_add": explanation.get("how_to_add", {})
    }
