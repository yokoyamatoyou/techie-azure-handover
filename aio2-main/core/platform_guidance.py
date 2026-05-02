"""
Platform guidance (single source of truth).

- Deterministic guidance shown in UI / PDF
- Also reused to build LLM prompt hints to avoid drift
"""

from __future__ import annotations

from typing import Any, Dict, Optional


PLATFORM_GUIDANCE_MAP: Dict[str, Dict[str, Any]] = {
    "WordPress": {
        "business": [
            "Yoast SEO/Rank Mathによる全ページのメタ要素個別最適化",
            "記事冒頭への要約（Answer First）配置による引用可能性の向上",
            "画像の代替テキスト(alt)とOGPタグのテンプレ・個別設定の徹底",
        ],
        "technical": [
            "JSON-LD（Organization/Article/FAQPage）の自動生成と動的挿入",
            "キャッシュプラグイン・画像最適化によるLCP/INPの改善（速度スコア向上）",
            "テーマのheader.php/functions.phpにおけるセマンティックタグの整備",
        ],
        "caveats": [
            "WordPress.com はプランや権限によって、プラグイン利用・ヘッダー編集の可否が変わります。",
        ],
        "help_links": [
            {"label": "WordPress.org サポート", "url": "https://wordpress.org/support/"},
            {"label": "WordPress.com ヘルプ", "url": "https://wordpress.com/support/"},
        ],
        "source_links": [
            {"label": "WordPress.com: Add code to headers", "url": "https://wordpress.com/support/adding-code-to-headers/"},
            {"label": "WordPress.com: SEO tools", "url": "https://wordpress.com/support/seo-tools/"},
            {"label": "WordPress.org: wp_head hook", "url": "https://developer.wordpress.org/reference/hooks/wp_head/"},
        ],
        "verified_at": "2026-02-27",
        "capabilities": {
            "can_edit_head": True,
            "can_add_jsonld": True,
        },
    },
    "Wix": {
        "business": [
            "SEOダッシュボードによるページ毎のユニークなメタ情報設計",
            "Wixエディタを用いたFAQ/比較表の構造化配置による情報密度の強化",
            "AIクローラーに配慮した簡潔なテキスト量と構造の維持",
        ],
        "technical": [
            "カスタム構造化データ機能を用いた詳細なJSON-LDの実装",
            "Wixサイト速度ツールを用いた画像軽量化と遅延読み込みの最適化",
            "各ページ単位でのOGP/ソーシャルシェア設定の最適化",
        ],
        "caveats": [
            "FAQ/HowTo などのリッチリザルトは、検索エンジン側の最新ポリシーで表示対象が限定される場合があります。",
        ],
        "help_links": [
            {"label": "Wixヘルプセンター", "url": "https://support.wix.com/"},
        ],
        "source_links": [
            {"label": "Wix: Structured data markup", "url": "https://support.wix.com/en/article/adding-structured-data-markup-to-your-sites-pages-2546962"},
            {"label": "Wix: robots.txt editor", "url": "https://support.wix.com/en/article/editing-your-sites-robotstxt-file"},
        ],
        "verified_at": "2026-02-27",
        "capabilities": {
            "can_edit_head": True,
            "can_add_jsonld": True,
        },
    },
    "Shopify": {
        "business": [
            "商品/コレクションの説明のAnswer First構造へのリライト",
            "検索エンジンリスティングプレビューを用いたメタ情報の精密制御",
            "購入判断を助けるFAQ/比較表の商品ページへの追加",
        ],
        "technical": [
            "Shopify APIまたはアプリを用いた商品情報のJSON-LD完全同期",
            "LiquidテンプレートのセマンティックHTML化と不要レガシースクリプトの削除",
            "画像alt属性の網羅とテーマ設定によるOGP画像品質の底上げ",
        ],
        "help_links": [
            {"label": "Shopify ヘルプセンター", "url": "https://help.shopify.com/ja"},
        ],
        "source_links": [
            {"label": "Shopify Dev: SEO metadata", "url": "https://shopify.dev/docs/storefronts/themes/seo/metadata"},
            {"label": "Shopify Dev: robots.txt.liquid", "url": "https://shopify.dev/docs/storefronts/themes/architecture/templates/robots-txt-liquid"},
        ],
        "verified_at": "2026-02-27",
        "capabilities": {
            "can_edit_head": True,
            "can_add_jsonld": True,
        },
    },
    "Amazonマーケットプレイス": {
        "business": [
            "商品名冒頭に主要キーワードと結論（最大のベネフィット）を集約",
            "箇条書き（Bullet）に利用シーン・比較優位・注意点を整理して追記",
            "レビュー要約やFAQ情報を商品説明に反映し、購入判断を支援",
        ],
        "technical": [
            "カテゴリ属性（仕様/サイズ/素材等）を欠損なく入力し検索精度を向上",
            "商品画像の解像度と白背景ルールを遵守しCTRと信頼性を改善",
            "検索キーワード（バックエンド）は上限（約250bytes）と禁止事項（ASIN/ブランド乱用等）を守り、重複回避で最適化",
        ],
        "help_links": [
            {"label": "Amazonセラーセントラル ヘルプ", "url": "https://sellercentral.amazon.co.jp/help/hub"},
        ],
        "capabilities": {
            "can_edit_head": False,
            "can_add_jsonld": False,
        },
    },
    "楽天市場": {
        "business": [
            "商品名・キャッチコピー・商品説明の冒頭に結論と主要キーワードを集約",
            "レビュー要約・FAQ・比較表を商品説明内に配置し、迷いを減らす",
            "送料・納期・保証/返品条件を明確化し、信頼性を高める",
        ],
        "technical": [
            "RMSのSEO項目（タイトル/説明文）を商品・カテゴリ単位で最適化",
            "商品説明は使用可能な範囲のHTML（改行/表/リンク等）で、見出し相当・箇条書き・表を使い情報構造を明確化",
            "商品画像の解像度・容量を最適化し表示速度とCTRを両立",
        ],
        "help_links": [
            {"label": "楽天市場 出店者様向けヘルプ", "url": "https://navi-manual.faq.rakuten.net/"},
        ],
        "capabilities": {
            "can_edit_head": False,
            "can_add_jsonld": False,
        },
    },
    "Yahoo!ショッピング": {
        "business": [
            "商品名・キャッチ・説明文の冒頭に結論とベネフィットを配置",
            "比較表/FAQ/利用シーンを商品説明に追加し、購入判断を支援",
            "配送・在庫・返品条件を簡潔に提示し、信頼性を補強",
        ],
        "technical": [
            "ストアクリエイターProのSEO項目（タイトル/説明文）を商品/カテゴリで最適化",
            "商品説明（HTML可の欄）で、見出し相当・箇条書き・表を使い情報構造を明確化（禁止タグ回避などの抜け道は使わない）",
            "画像ファイルの軽量化と高品質化を両立し、表示速度を改善",
        ],
        "help_links": [
            {"label": "Yahoo!ショッピング ストアクリエイターPro", "url": "https://support.yahoo-net.jp/PccShopping/s/"},
        ],
        "capabilities": {
            "can_edit_head": False,
            "can_add_jsonld": False,
        },
    },
    "BASE": {
        "business": [
            "SEO設定Appによる説明文主導のインデックス最適化",
            "商品説明冒頭320文字への主要キーワードと結論の集約",
            "ショップの信頼性(E-E-A-T)を補強する運営者情報の詳細提示",
        ],
        "technical": [
            "カスタムHTML Appを用いた商品個別のJSON-LD埋め込み",
            "画像登録時のファイル名最適化とalt属性の100%補完",
            "テンプレートの見出しタグ(H1-H3)階層の内部構造反映",
        ],
        "help_links": [
            {"label": "BASE ヘルプ", "url": "https://help.thebase.in/"},
        ],
        "capabilities": {
            "can_edit_head": False,
            "can_add_jsonld": "limited",
        },
    },
    "STUDIO": {
        "business": [
            "全ページのSEOタイトル・キーワード・説明文の個別記述化",
            "STUDIOエディタでのHタグ(H1-H4)の意味に基づいた正確な割り当て",
            "導線設計と連動したFAQブロックの戦略的配置",
        ],
        "technical": [
            "Embed Code機能を用いたhead内へのJSON-LD(Organization等)挿入",
            "アセット最適化による画像ファイルの軽量化と読み込み順序の制御",
            "サイト設定でのカスタムドメインとOGP/ファビコンの完全整合",
        ],
        "help_links": [
            {"label": "STUDIO ヘルプ", "url": "https://help.studio.design/"},
        ],
        "capabilities": {
            "can_edit_head": True,
            "can_add_jsonld": True,
        },
    },
    "ペライチ": {
        "business": [
            "基本設定によるメタタグ最適化と検索意図の合致確認",
            "1ページ完結型(LP)に最適化された結論ファーストのリード文構成",
            "ユーザーの不安を解消するFAQセクションの追加による引用率向上",
        ],
        "technical": [
            "カスタムHTML設定を用いたFAQ/Organizationスキーマの追加",
            "編集画面での画像alt情報の完全補完とファイル名設計",
            "ページ設定によるSNS共有用画像(OGP)の最適化",
        ],
        "help_links": [
            {"label": "ペライチ ヘルプ", "url": "https://help.peraichi.com/"},
        ],
        "capabilities": {
            "can_edit_head": "limited",
            "can_add_jsonld": "limited",
        },
    },
    "Jimdo": {
        "business": [
            "SEO設定メニューによる全階層のメタタグ更新と整合性確保",
            "エディタによる見出し(Heading)タグの厳格な階層化",
            "情報の抜けを補完するFAQコンポーネントの網羅的導入",
        ],
        "technical": [
            "共通設定によるOGP画像の解像度とアスペクト比の最適化",
            "画像詳細設定からの代替テキスト入力による機械可読性の担保",
            "レスポンス改善のための巨大画像ファイルの事前リサイズ",
        ],
        "help_links": [
            {"label": "Jimdo サポート", "url": "https://support.jimdo.com/"},
        ],
        "capabilities": {
            "can_edit_head": "limited",
            "can_add_jsonld": "limited",
        },
    },
    "Google Sites": {
        "business": [
            "ページ冒頭への目次(ToC)配置による構造化情報の提示",
            "テキストボックススタイル設定による見出し階層の明確化",
            "AIが認識しやすい具体的かつ簡潔な要約文の先頭配置",
        ],
        "technical": [
            "全画像への詳細な代替テキスト(alt)付与の徹底",
            "カスタムドメイン適用による信頼性スコアの向上",
            "アンカーリンク活用による内部構造のクローラビリティ改善",
        ],
        "help_links": [
            {"label": "Google Sites ヘルプ", "url": "https://support.google.com/sites/"},
        ],
        "capabilities": {
            "can_edit_head": False,
            "can_add_jsonld": False,
        },
    },
    "STORES": {
        "business": [
            "ストア全体・個別商品のメタ情報バリエーションの確保",
            "商品説明1行目への最大ベネフィット配置による引用優先度向上",
            "購入判断指標となる比較表・FAQの網羅的配置",
        ],
        "technical": [
            "商品登録時のalt情報補完による画像検索・AI検索への適合",
            "ストア設定からの高性能なOGP画像のアップロードと管理",
            "デザイン設定の見直しによる不要な読み込み要素の削減",
        ],
        "help_links": [
            {"label": "STORES ヘルプ", "url": "https://help.stores.jp/"},
        ],
        "capabilities": {
            "can_edit_head": False,
            "can_add_jsonld": False,
        },
    },
    "カラーミーショップ": {
        "business": [
            "SEO設定画面によるカテゴリ・商品別メタタグの多角化",
            "カテゴリページ冒頭への動向・選定基準情報の追加",
            "特商法ページの充実によるE-E-A-T(信頼性)の根拠強化",
        ],
        "technical": [
            "HTMLテンプレートへのJSON-LDタグ直接追記による高度な構造化",
            "商品画像タイトル属性への日本語キーワードの戦略的配置",
            "OGP画像テンプレートの最適化と個別ページでの反映",
        ],
        "help_links": [
            {"label": "カラーミーショップ ヘルプ", "url": "https://help.shop-pro.jp/"},
        ],
        "capabilities": {
            "can_edit_head": True,
            "can_add_jsonld": True,
        },
    },
    "MakeShop": {
        "business": [
            "独自デザイン機能を用いた、商品詳細ページ冒頭への訴求ポイント(結論)の集約",
            "MakeShop独自タグを活用した、競合比較表やスペック一覧のコンテンツ化",
            "独自ページ作成機能を活用した「よくある質問(FAQ)」の独立・網羅による信頼性強化",
        ],
        "technical": [
            "内部SEO設定画面での「全ページ共通/個別ページ」メタ要素の精密な使い分け",
            "テンプレートへの直接記述による、スマホ最適化を意識したOGP画像解像度の調整",
            "商品登録インターフェースにおけるalt属性およびサブ画像情報の100%補完",
        ],
        "help_links": [
            {"label": "MakeShop サポート", "url": "https://support.makeshop.jp/"},
        ],
        "capabilities": {
            "can_edit_head": True,
            "can_add_jsonld": True,
        },
    },
    "ショップサーブ": {
        "business": [
            "管理画面の「デザイン設定 > ヘッダとSEOの設定」でタイトル・ディスクリプション・キーワードを最適化",
            "商品ページ編集画面でメタ情報を個別に最適化し、冒頭に結論とベネフィットを配置",
            "特定商取引法・会社情報への導線を明確化し、信頼性指標(E-E-A-T)を強化",
        ],
        "technical": [
            "カスタムHTML編集でJSON-LD（Organization/Product/BreadcrumbList）を埋め込み",
            "画像登録時の代替テキスト（全角64文字）を網羅し、画像台帳で一括管理",
            "ヘッダーロゴのH1重複を確認し、商品名との重複を避ける",
        ],
        "help_links": [
            {"label": "ショップサーブ ヘルプ", "url": "https://help.shopserve.jp/"},
            {"label": "SEO設定", "url": "https://help.shopserve.jp/help/headfooter.php"},
        ],
        "capabilities": {
            "can_edit_head": True,
            "can_add_jsonld": True,
        },
    },
    "フューチャーショップ": {
        "business": [
            "「構築メニュー > ページ設定 > SEO管理」でタイトル（50文字）・説明文（125文字）を最適化",
            "商品詳細ページ冒頭にFAQ/比較表を配置し、引用されやすい構成に調整",
            "レビューや保証情報を明示し、信頼性シグナルを補強",
        ],
        "technical": [
            "「設定 > プロモーション > 構造化データ設定」でJSON-LD自動出力を有効化",
            "商品画像のALTテキストを運用メニューから一括設定",
            "OGP画像・タイトルの個別最適化でSNS共有時のCTRを改善",
        ],
        "help_links": [
            {"label": "フューチャーショップ マニュアル", "url": "https://manual.future-shop.jp/"},
            {"label": "構造化データ設定", "url": "https://manual.future-shop.jp/settings/promotion/analyticsStructuredData/"},
        ],
        "capabilities": {
            "can_edit_head": True,
            "can_add_jsonld": True,
        },
    },
    "カスタム/その他": {
        "business": [
            "セマンティックHTML5による文書構造の意味論的定義",
            "AI検索の引用源(Source)として選ばれやすい信頼性の高い執筆構成",
            "出典・エビデンス・数値根拠のリスト化による情報の真正性強化",
        ],
        "technical": [
            "JSON-LD(Organization/WebSite/FAQ)の完全な手動実装",
            "robots.txt/sitemap.xmlの高度な制御によるクロール最適化",
            "LCP/INPを極限まで高めるSSR/静的化/CDNの技術導入",
        ],
        "help_links": [],
        "capabilities": {
            "can_edit_head": True,
            "can_add_jsonld": True,
        },
    },
}


def normalize_platform_label(platform_label: Optional[str]) -> Optional[str]:
    if not platform_label:
        return None
    if platform_label == "自動判定":
        return None
    return str(platform_label).strip() or None


def get_platform_guidance(platform_label: Optional[str]) -> Dict[str, Any]:
    """Return deterministic platform guidance shown in UI/PDF."""
    label = normalize_platform_label(platform_label) or "カスタム/その他"
    guidance = PLATFORM_GUIDANCE_MAP.get(label, PLATFORM_GUIDANCE_MAP["カスタム/その他"])
    help_links = guidance.get("help_links", []) or []
    source_links = guidance.get("source_links", []) or help_links
    return {
        "label": label,
        "business_steps": guidance.get("business", []) or [],
        "technical_steps": guidance.get("technical", []) or [],
        "caveats": guidance.get("caveats", []) or [],
        "help_links": help_links,
        "source_links": source_links,
        "verified_at": guidance.get("verified_at"),
        "capabilities": guidance.get("capabilities", {}) or {},
    }


def format_platform_advice_for_llm(platform_label: Optional[str]) -> str:
    """Build concise, accurate instructions for LLM prompt."""
    g = get_platform_guidance(platform_label)
    label = g.get("label") or "カスタム/その他"
    biz = g.get("business_steps", []) or []
    tech = g.get("technical_steps", []) or []
    caveats = g.get("caveats", []) or []
    caps = g.get("capabilities", {}) or {}
    can_jsonld = caps.get("can_add_jsonld")
    can_head = caps.get("can_edit_head")

    lines = [f"【{label}向けの改善方法（実務で実行できる範囲）】"]
    if can_head is False or can_jsonld is False:
        lines.append("※ 出品プラットフォーム側のテンプレート制約があり、head編集やJSON-LD埋め込みはできない前提で提案してください。")
    for caveat in caveats[:2]:
        lines.append(f"※ 注意: {caveat}")

    if biz:
        lines.append("【運用/コンテンツ】")
        lines.extend([f"- {s}" for s in biz[:6]])

    if tech:
        lines.append("【設定/技術】")
        lines.extend([f"- {s}" for s in tech[:6]])

    return "\n".join(lines)


COMMON_SECURITY_RISKS = [
    {
        "term": "中間者攻撃",
        "plain": "通信の途中で第三者にのぞき見・改ざんされる攻撃です。",
        "risk": "ログイン情報や入力内容が漏えいする可能性",
        "action": "HTTPSを強制し、HSTS（Strict-Transport-Security）を設定する",
    },
    {
        "term": "クリックジャッキング",
        "plain": "見えないボタンを重ねて、意図しないクリックを誘導する攻撃です。",
        "risk": "ユーザーが気づかず操作してしまう可能性",
        "action": "X-Frame-Options: DENY または SAMEORIGIN を設定する",
    },
    {
        "term": "MIMEスニッフィング",
        "plain": "ブラウザがファイル種類を推測し、想定外に実行してしまうリスクです。",
        "risk": "不正スクリプトが実行される可能性",
        "action": "X-Content-Type-Options: nosniff を設定する",
    },
]


LLMS_TXT_BEST_PRACTICES = [
    "配置場所: サイトルートに配置（例: https://example.com/llms.txt）",
    "配信条件: 200 OK で直接アクセス可能にする（認証ページ配下に置かない）",
    "形式: text/plain で配信し、UTF-8で保存する",
    "内容: 重要ページURLと1-2行の要約を記載する",
    "運用: 更新日を記載し、サイト更新時に内容も更新する",
]


def _build_platform_specific_risks(label: str, capabilities: Dict[str, Any]) -> list[Dict[str, str]]:
    """Build platform-specific risk/action guidance from capability flags."""
    can_head = capabilities.get("can_edit_head")
    can_jsonld = capabilities.get("can_add_jsonld")

    risks: list[Dict[str, str]] = []

    if can_head is False:
        risks.append({
            "term": "head編集の制限",
            "plain": "ヘッダーに自由なコードを入れられない可能性があります。",
            "risk": "セキュリティヘッダーや検証タグの柔軟な実装が難しい",
            "action": "プラットフォーム標準設定、またはCDN/WAF（Cloudflare等）で補完する",
        })
    elif can_head == "limited":
        risks.append({
            "term": "head編集の一部制限",
            "plain": "編集できる範囲が限定されます。",
            "risk": "一部ページで同じ対策を適用できない可能性",
            "action": "共通設定で最低限を担保し、不足分は外部サービスで補う",
        })

    if can_jsonld is False:
        risks.append({
            "term": "構造化データの直接実装不可",
            "plain": "JSON-LDを自由に埋め込めない可能性があります。",
            "risk": "検索結果での情報表示がプラットフォーム仕様に依存",
            "action": "商品/店舗情報の入力品質を上げ、必要に応じて自社サイトで補完する",
        })
    elif can_jsonld == "limited":
        risks.append({
            "term": "構造化データの実装制限",
            "plain": "一部タイプのみ設定可能な場合があります。",
            "risk": "必要なSchemaタイプを十分に出せない可能性",
            "action": "優先度の高いOrganization/Article/Productから実装する",
        })

    if label in {"Amazonマーケットプレイス", "楽天市場", "Yahoo!ショッピング"}:
        risks.append({
            "term": "マーケットプレイス依存",
            "plain": "ページ仕様や表示ルールが外部プラットフォーム主導です。",
            "risk": "技術改善の自由度が低く、反映タイミングを制御しづらい",
            "action": "説明文の構造化・画像品質・FAQ充実を優先し、自社サイトで補完する",
        })

    if not risks:
        risks.append({
            "term": "設定変更の副作用",
            "plain": "自由度が高い分、設定ミスの影響が広がりやすいです。",
            "risk": "テンプレート変更で全ページに不具合が出る可能性",
            "action": "ステージング環境で検証し、変更後に主要ページを再チェックする",
        })

    return risks


def build_platform_risk_profile(platform_label: Optional[str]) -> Dict[str, Any]:
    """Return common/platform-specific risks with plain explanations and actions."""
    guidance = get_platform_guidance(platform_label)
    label = guidance.get("label") or "カスタム/その他"
    capabilities = guidance.get("capabilities", {}) or {}

    return {
        "label": label,
        "common_risks": COMMON_SECURITY_RISKS,
        "platform_specific_risks": _build_platform_specific_risks(label, capabilities),
        "llms_txt_best_practices": LLMS_TXT_BEST_PRACTICES,
    }

