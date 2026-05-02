"""
プラットフォーム別の構造化データ実装ガイド
"""

SCHEMA_IMPLEMENTATION_GUIDES = {
    "Organization": {
        "rakuten": {
            "method": "不可（出店者側で構造化データは編集できない）",
            "difficulty": "not_applicable",
            "estimated_time": "N/A",
            "steps": [
                "楽天市場の商品ページは出店者がJSON-LDを埋め込めません",
                "代替として、店舗/商品説明の構造化（見出し相当・箇条書き・FAQ）と信頼情報（会社情報/返品/送料）を充実させてください",
            ],
            "limitations": [
                "HTMLや<head>の編集は不可（楽天側のテンプレートに依存）",
                "構造化データの出力は楽天側の仕様に依存",
            ],
            "alternative": "自社EC/公式サイトに同一情報のページを用意し、構造化データを実装（Organization/WebSite/Product等）",
        },
        "楽天市場": {
            "method": "不可（出店者側で構造化データは編集できない）",
            "difficulty": "not_applicable",
            "estimated_time": "N/A",
            "steps": [
                "楽天市場の商品ページは出店者がJSON-LDを埋め込めません",
                "代替として、店舗/商品説明の構造化（見出し・箇条書き・FAQ）と信頼情報（会社情報/返品/送料）を充実させてください",
            ],
            "limitations": [
                "HTMLや<head>の編集は不可（楽天側のテンプレートに依存）",
                "構造化データの出力は楽天側の仕様に依存",
            ],
            "alternative": "自社EC/公式サイトに同一情報のページを用意し、構造化データを実装（Organization/WebSite/Product等）",
        },
        "yahoo_shopping": {
            "method": "不可（ストア側で構造化データは編集できない）",
            "difficulty": "not_applicable",
            "estimated_time": "N/A",
            "steps": [
                "Yahoo!ショッピングの商品ページはストア側がJSON-LDを埋め込めません",
                "代替として、商品説明の構造化（見出し相当・箇条書き・FAQ）と信頼情報（配送/在庫/返品）を明確化してください",
            ],
            "limitations": [
                "HTMLや<head>の編集は不可（Yahoo側のテンプレートに依存）",
                "構造化データの出力はYahoo側の仕様に依存",
            ],
            "alternative": "自社EC/公式サイトに同一情報のページを用意し、構造化データを実装（Organization/WebSite/Product等）",
        },
        "yahoo!ショッピング": {
            "method": "不可（ストア側で構造化データは編集できない）",
            "difficulty": "not_applicable",
            "estimated_time": "N/A",
            "steps": [
                "Yahoo!ショッピングの商品ページはストア側がJSON-LDを埋め込めません",
                "代替として、商品説明の構造化（見出し・箇条書き・FAQ）と信頼情報（配送/在庫/返品）を明確化してください",
            ],
            "limitations": [
                "HTMLや<head>の編集は不可（Yahoo側のテンプレートに依存）",
                "構造化データの出力はYahoo側の仕様に依存",
            ],
            "alternative": "自社EC/公式サイトに同一情報のページを用意し、構造化データを実装（Organization/WebSite/Product等）",
        },
        "amazon_marketplace": {
            "method": "不可（出品者側で構造化データは編集できない）",
            "difficulty": "not_applicable",
            "estimated_time": "N/A",
            "steps": [
                "Amazonの商品詳細ページは出品者がJSON-LDを埋め込めません",
                "代替として、商品名/箇条書き/商品説明/画像の最適化で情報品質を担保",
            ],
            "limitations": [
                "HTMLや<head>の編集は不可",
                "構造化データの出力はAmazon側の仕様に依存",
            ],
            "alternative": "自社EC/公式サイトに同一商品ページを用意し構造化データを実装",
        },
        "amazonマーケットプレイス": {
            "method": "不可（出品者側で構造化データは編集できない）",
            "difficulty": "not_applicable",
            "estimated_time": "N/A",
            "steps": [
                "Amazonの商品詳細ページは出品者がJSON-LDを埋め込めません",
                "代替として、商品名/箇条書き/商品説明/画像の最適化で情報品質を担保",
            ],
            "limitations": [
                "HTMLや<head>の編集は不可",
                "構造化データの出力はAmazon側の仕様に依存",
            ],
            "alternative": "自社EC/公式サイトに同一商品ページを用意し構造化データを実装",
        },
        "wordpress": {
            "method": "プラグイン使用",
            "difficulty": "easy",
            "estimated_time": "5分",
            "steps": [
                "1. 「Yoast SEO」または「Rank Math」プラグインをインストール",
                "2. プラグイン設定画面を開く",
                "3. 「Schema」または「構造化データ」タブを選択",
                "4. 「Organization」を選択し、会社情報を入力",
                "5. 保存して完了",
            ],
            "limitations": [],
            "alternative": "テーマのfunctions.phpに直接コードを追加することも可能",
        },
        "wix": {
            "method": "設定画面から",
            "difficulty": "medium",
            "estimated_time": "3分",
            "steps": [
                "1. Wixエディタで「設定」→「SEO」を開く",
                "2. 「構造化データマークアップ」セクションを探す",
                "3. 「Organization」を選択",
                "4. 会社名、ロゴ、連絡先を入力",
                "5. 保存",
            ],
            "limitations": ["一部の高度な設定は不可"],
            "alternative": "Wix Codeでカスタムコードを追加",
        },
        "shopify": {
            "method": "テーマ編集",
            "difficulty": "easy",
            "estimated_time": "10分",
            "steps": [
                "1. 管理画面で「オンラインストア」→「テーマ」を開く",
                "2. 「アクションを実行」→「コードを編集」",
                "3. `theme.liquid` を開く",
                "4. `</head>` の直前に以下のコードを追加:",
                "   <script type=\"application/ld+json\">",
                "   {",
                "     \"@context\": \"https://schema.org\",",
                "     \"@type\": \"Organization\",",
                "     \"name\": \"あなたの会社名\"",
                "   }",
                "   </script>",
                "5. 保存",
            ],
            "limitations": [],
            "alternative": "アプリを使用（例: JSON-LD for SEO）",
        },
        "base": {
            "method": "HTML編集（制限あり）",
            "difficulty": "hard",
            "estimated_time": "15分",
            "steps": [
                "1. BASEの管理画面で「Apps」→「HTML編集」を開く",
                "2. ヘッダーHTMLセクションを探す",
                "3. 以下のコードを追加:",
                "   <script type=\"application/ld+json\">",
                "   { \"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"店舗名\" }",
                "   </script>",
                "4. 保存",
            ],
            "limitations": [
                "無料プランではHTML編集が制限される",
                "一部のタグが使用できない可能性",
            ],
            "alternative": "有料プランにアップグレード",
        },
        "custom": {
            "method": "HTML直接編集",
            "difficulty": "varies",
            "estimated_time": "5-30分",
            "steps": [
                "1. HTMLファイルの<head>セクションを開く",
                "2. </head>の直前に以下を追加:",
                "   <script type=\"application/ld+json\">",
                "   {",
                "     \"@context\": \"https://schema.org\",",
                "     \"@type\": \"Organization\",",
                "     \"name\": \"会社名\",",
                "     \"url\": \"https://example.com\",",
                "     \"logo\": \"https://example.com/logo.png\"",
                "   }",
                "   </script>",
                "3. ファイルを保存してアップロード",
            ],
            "limitations": ["サーバーへのアクセス権が必要"],
            "alternative": "Google Tag Managerを使用",
        },
    },
    "Product": {
        "shopify": {
            "method": "自動生成（標準機能）",
            "difficulty": "easy",
            "estimated_time": "0分（自動）",
            "steps": [
                "商品情報を入力すると自動的にProduct schemaが生成されます",
            ],
            "limitations": [],
            "alternative": "テーマ編集でカスタマイズ可能",
        },
        "wordpress": {
            "method": "WooCommerceプラグイン",
            "difficulty": "easy",
            "estimated_time": "5分",
            "steps": [
                "1. WooCommerceをインストール",
                "2. Yoast SEOまたはRank Mathをインストール",
                "3. 商品ページで自動的にProduct schemaが生成される",
            ],
            "limitations": [],
            "alternative": "手動でコードを追加",
        },
    },
}


def get_implementation_guide(schema_type: str, platform: str) -> dict:
    """
    指定されたスキーマタイプとプラットフォームの実装ガイドを取得

    Args:
        schema_type: スキーマタイプ（例: "Organization"）
        platform: プラットフォーム名（例: "wordpress"）

    Returns:
        実装ガイド辞書
    """
    return SCHEMA_IMPLEMENTATION_GUIDES.get(schema_type, {}).get(
        platform,
        SCHEMA_IMPLEMENTATION_GUIDES.get(schema_type, {}).get("custom", {}),
    )
