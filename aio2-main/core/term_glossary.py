# -*- coding: utf-8 -*-
"""
用語マッピングシステム
専門用語を非エンジニア向けに自動変換するシステム
"""

from typing import Dict, List, Optional

# =============================================================================
# 用語辞書データ
# =============================================================================

TERM_GLOSSARY = {
    # =========================================================================
    # SEO用語 (20語)
    # =========================================================================
    "canonical": {
        "simple": "正規URL設定",
        "detail": "「このページが本物です」という宣言。重複ページがある場合に検索エンジンに正しいURLを伝える",
        "category": "seo",
        "for_engineer": "rel=\"canonical\" で正規URLを指定。重複コンテンツのインデックス制御"
    },
    "robots.txt": {
        "simple": "検索エンジンへの指示書",
        "detail": "「このページは見ないで」等の設定ファイル。クロールを制御する",
        "category": "seo",
        "for_engineer": "User-agent/Disallow/Allow/Sitemap ディレクティブで構成"
    },
    "meta description": {
        "simple": "検索結果の説明文",
        "detail": "Google検索結果でタイトルの下に出る文章。クリック率に影響",
        "category": "seo",
        "for_engineer": "<meta name=\"description\" content=\"...\"> で設定。80-120文字推奨（121-160文字は許容）"
    },
    "sitemap.xml": {
        "simple": "サイトの地図ファイル",
        "detail": "検索エンジンにサイト内のページ一覧を伝えるファイル",
        "category": "seo",
        "for_engineer": "XML形式。<urlset>/<url>/<loc>/<lastmod>/<changefreq>/<priority>"
    },
    "noindex": {
        "simple": "検索結果に出さない設定",
        "detail": "このページは検索結果に表示しないでください、という指示",
        "category": "seo",
        "for_engineer": "<meta name=\"robots\" content=\"noindex\"> または X-Robots-Tag ヘッダー"
    },
    "alt属性": {
        "simple": "画像の説明文",
        "detail": "画像が見えない人向けのテキスト。SEOにも影響",
        "category": "seo",
        "for_engineer": "<img alt=\"説明\">。空のalt=\"\"は装飾画像に使用"
    },
    "内部リンク": {
        "simple": "サイト内のページ同士をつなぐリンク",
        "detail": "自分のサイト内の別ページへのリンク。SEO評価の分配に影響",
        "category": "seo",
        "for_engineer": "アンカーテキストの最適化、リンクジュースの分配を考慮"
    },
    "外部リンク": {
        "simple": "他のサイトへのリンク",
        "detail": "自分のサイトから他のサイトへのリンク",
        "category": "seo",
        "for_engineer": "rel=\"nofollow/sponsored/ugc\" の使い分けが重要"
    },
    "被リンク": {
        "simple": "他のサイトからもらうリンク",
        "detail": "他のサイトが自分のサイトを紹介してくれるリンク。信頼性の指標",
        "category": "seo",
        "for_engineer": "バックリンク。ドメインオーソリティに影響。質と量のバランスが重要"
    },
    "クロール": {
        "simple": "検索エンジンがページを読み取ること",
        "detail": "Googleなどがサイトの内容を自動で読み取る作業",
        "category": "seo",
        "for_engineer": "Googlebotによる巡回。クロールバジェットの最適化が大規模サイトで重要"
    },
    "インデックス": {
        "simple": "検索エンジンへの登録",
        "detail": "クロールされたページが検索結果に表示される状態になること",
        "category": "seo",
        "for_engineer": "Google Search Console の「インデックス登録をリクエスト」で手動申請可能"
    },
    "コアウェブバイタル": {
        "simple": "ページ表示の快適さ指標",
        "detail": "Googleが定めたページ体験の指標。表示速度やガタつきを測定",
        "category": "seo",
        "for_engineer": "LCP/FID(INP)/CLSの3指標。PageSpeed Insightsで測定"
    },
    "モバイルフレンドリー": {
        "simple": "スマホで見やすい設計",
        "detail": "スマートフォンでも快適に閲覧できるサイト設計",
        "category": "seo",
        "for_engineer": "レスポンシブデザイン、viewport設定、タップターゲットサイズ"
    },
    "SERP": {
        "simple": "検索結果ページ",
        "detail": "Search Engine Results Page。Googleで検索した時に表示される結果ページ",
        "category": "seo",
        "for_engineer": "オーガニック結果、広告、ナレッジパネル、リッチリザルト等で構成"
    },
    "検索意図": {
        "simple": "ユーザーが検索する目的",
        "detail": "そのキーワードで検索する人が本当に知りたいこと",
        "category": "seo",
        "for_engineer": "Informational/Navigational/Transactional/Commercial の4分類"
    },
    # --- 追加SEO用語 ---
    "タイトルタグ": {
        "simple": "ページのタイトル設定",
        "detail": "検索結果やブラウザのタブに表示されるページの名前",
        "category": "seo",
        "for_engineer": "<title>タグ。28-36文字推奨（20-40文字は許容）。キーワードを前方に配置"
    },
    "hreflang": {
        "simple": "多言語ページの関連付け",
        "detail": "同じ内容の別言語ページを検索エンジンに伝える設定",
        "category": "seo",
        "for_engineer": "rel=\"alternate\" hreflang=\"ja\" で言語・地域を指定。x-defaultで未指定時のデフォルト"
    },
    "301リダイレクト": {
        "simple": "ページの恒久的な転送",
        "detail": "古いURLから新しいURLへ永久に転送する設定。SEO評価も引き継がれる",
        "category": "seo",
        "for_engineer": "HTTPステータス301。.htaccess、nginx.conf、またはサーバーサイドで設定"
    },
    "サーチコンソール": {
        "simple": "Googleの無料分析ツール",
        "detail": "Google Search Console。検索パフォーマンスやインデックス状況を確認できる",
        "category": "seo",
        "for_engineer": "GSC。クロールエラー、検索クエリ、Core Web Vitals、構造化データの検証"
    },
    "ペナルティ": {
        "simple": "検索順位の低下措置",
        "detail": "Googleのガイドライン違反によって検索順位が大幅に下がること",
        "category": "seo",
        "for_engineer": "手動対策（Manual Action）と自動ペナルティ。GSCで手動対策を確認可能"
    },

    # =========================================================================
    # AIO用語 (15語)
    # =========================================================================
    "llms.txt": {
        "simple": "AI検索向けの指示書",
        "detail": "ChatGPT等のAIに読ませたい内容の設定ファイル",
        "category": "aio",
        "for_engineer": "robots.txtのAI版。/llms.txt, /llms-full.txt, /llms.md をサポート"
    },
    "SSR": {
        "simple": "サーバー側で画面生成",
        "detail": "AIや検索エンジンがページを読みやすくする技術",
        "category": "aio",
        "for_engineer": "Server-Side Rendering。Next.js/Nuxt.js等で実装。SEO/AIO両方に有効"
    },
    "エンティティ": {
        "simple": "固有の概念や物事",
        "detail": "人名、地名、会社名など、明確に識別できる概念",
        "category": "aio",
        "for_engineer": "ナレッジグラフのノード。Schema.orgでマークアップして明示化"
    },
    "引用準備性": {
        "simple": "AIに引用されやすさ",
        "detail": "AIチャットで回答として引用されやすいコンテンツの特性",
        "category": "aio",
        "for_engineer": "Citation Readiness Index。結論優先構造、データ密度、簡潔性で評価"
    },
    "AEO": {
        "simple": "AI検索エンジン最適化",
        "detail": "Answer Engine Optimization。AIに答えとして選ばれるための最適化",
        "category": "aio",
        "for_engineer": "定義文パターン「AとはBである」、FAQ構造、数値・統計の明示"
    },
    "ナレッジグラフ": {
        "simple": "知識の関連図",
        "detail": "Googleが持つ事実情報のデータベース。検索結果の右側パネルに表示",
        "category": "aio",
        "for_engineer": "エンティティ間の関係性を表現。構造化データでの接続が重要"
    },
    "マルチモーダル": {
        "simple": "複数の形式を組み合わせ",
        "detail": "テキスト、画像、動画など複数の形式を組み合わせたコンテンツ",
        "category": "aio",
        "for_engineer": "GPT-4V等のマルチモーダルAIに対応。alt属性、キャプションが重要"
    },
    "情報鮮度": {
        "simple": "情報の新しさ",
        "detail": "コンテンツがどれだけ最近更新されているか",
        "category": "aio",
        "for_engineer": "dateModified/datePublished のJSON-LD。6ヶ月以内が高評価"
    },
    "PID": {
        "simple": "情報密度",
        "detail": "文章にどれだけ有益な情報が詰まっているか",
        "category": "aio",
        "for_engineer": "Propositional Idea Density。内容語÷総語数で算出"
    },
    "AIクローラー": {
        "simple": "AIの情報収集プログラム",
        "detail": "ChatGPT等のAIがウェブの情報を集めるプログラム",
        "category": "aio",
        "for_engineer": "GPTBot, ClaudeBot, Bingbot等。robots.txtで制御可能"
    },
    # --- 追加AIO用語 ---
    "AI Overview": {
        "simple": "Google検索のAI回答",
        "detail": "Google検索結果の上部に表示されるAIが生成した要約回答",
        "category": "aio",
        "for_engineer": "旧SGE（Search Generative Experience）。構造化データとE-E-A-Tが引用に影響"
    },
    "GEO": {
        "simple": "生成AI検索最適化",
        "detail": "Generative Engine Optimization。AI生成の検索結果に表示されるための最適化",
        "category": "aio",
        "for_engineer": "SEOの進化形。引用元として選ばれるための権威性・信頼性・明確な定義が重要"
    },
    "会話型検索": {
        "simple": "対話形式の検索",
        "detail": "ChatGPTやPerplexityのように質問形式で情報を検索する方法",
        "category": "aio",
        "for_engineer": "Conversational Search。検索意図の深掘り、フォローアップクエリへの対応が重要"
    },
    "ゼロクリック検索": {
        "simple": "クリック不要で完結する検索",
        "detail": "検索結果ページ上で答えが表示され、サイトに訪問せずに情報が得られる検索",
        "category": "aio",
        "for_engineer": "Zero-Click Search。強調スニペット、AI Overview、ナレッジパネルで増加傾向"
    },
    "RAG": {
        "simple": "AIの情報検索付き回答",
        "detail": "AIが外部の情報源を検索して、その情報を元に回答を生成する技術",
        "category": "aio",
        "for_engineer": "Retrieval-Augmented Generation。ベクトル検索+LLMで構成。ハルシネーション軽減"
    },

    # =========================================================================
    # 構造化データ (10語)
    # =========================================================================
    "JSON-LD": {
        "simple": "検索エンジン向けの情報タグ",
        "detail": "Googleが内容を正確に理解するための設定",
        "category": "structured_data",
        "for_engineer": "JavaScript Object Notation for Linked Data。<script type=\"application/ld+json\">"
    },
    "構造化データ": {
        "simple": "検索エンジン向けの情報タグ",
        "detail": "ページの内容を検索エンジンが理解しやすい形式で記述したもの",
        "category": "structured_data",
        "for_engineer": "Schema.org語彙を使用。JSON-LD/Microdata/RDFa形式"
    },
    "Schema.org": {
        "simple": "情報タグの国際規格",
        "detail": "世界共通の書き方ルール。Google, Bing, Yahooが共同策定",
        "category": "structured_data",
        "for_engineer": "https://schema.org/ で定義。継承構造を持つ型システム"
    },
    "リッチリザルト": {
        "simple": "検索結果の豪華表示",
        "detail": "検索結果で画像、評価、価格などが表示される形式",
        "category": "structured_data",
        "for_engineer": "構造化データから生成。Rich Results Test で検証"
    },
    "Product": {
        "simple": "商品情報タグ",
        "detail": "商品の名前、価格、在庫などを検索エンジンに伝える設定",
        "category": "structured_data",
        "for_engineer": "Schema.org/Product。Offer, AggregateRating と組み合わせ"
    },
    "LocalBusiness": {
        "simple": "店舗情報タグ",
        "detail": "お店の住所、営業時間、電話番号などを検索エンジンに伝える設定",
        "category": "structured_data",
        "for_engineer": "Schema.org/LocalBusiness。GeoCoordinates, OpeningHoursSpecification"
    },
    "FAQPage": {
        "simple": "よくある質問タグ",
        "detail": "Q&A形式のコンテンツを検索エンジンに伝える設定",
        "category": "structured_data",
        "for_engineer": "Schema.org/FAQPage。Question/acceptedAnswer で構成"
    },
    "Article": {
        "simple": "記事情報タグ",
        "detail": "ブログや記事の情報を検索エンジンに伝える設定",
        "category": "structured_data",
        "for_engineer": "Schema.org/Article。headline, author, datePublished が必須級"
    },
    "BreadcrumbList": {
        "simple": "パンくずリストタグ",
        "detail": "現在のページ位置を示すナビゲーションの設定",
        "category": "structured_data",
        "for_engineer": "Schema.org/BreadcrumbList。ListItem の配列で構成"
    },
    "Organization": {
        "simple": "会社・組織情報タグ",
        "detail": "会社名、ロゴ、連絡先などを検索エンジンに伝える設定",
        "category": "structured_data",
        "for_engineer": "Schema.org/Organization。logo, contactPoint, sameAs"
    },

    # =========================================================================
    # パフォーマンス (5語)
    # =========================================================================
    "LCP": {
        "simple": "画面表示速度",
        "detail": "ページの主要部分が表示されるまでの時間。2.5秒以内が目標",
        "category": "performance",
        "for_engineer": "Largest Contentful Paint。2.5秒以内がGood、4秒超がPoor"
    },
    "CLS": {
        "simple": "画面のガタつき",
        "detail": "読込中にボタン等がズレる現象。0.1以下が目標",
        "category": "performance",
        "for_engineer": "Cumulative Layout Shift。width/height属性、フォント最適化で改善"
    },
    "FID": {
        "simple": "操作の反応速度",
        "detail": "ボタンを押してから反応するまでの時間",
        "category": "performance",
        "for_engineer": "First Input Delay。INP(Interaction to Next Paint)に移行中"
    },
    "INP": {
        "simple": "操作全体の反応速度",
        "detail": "ページ上の全ての操作の反応速度。200ms以内が目標",
        "category": "performance",
        "for_engineer": "Interaction to Next Paint。FIDの後継指標。2024年3月からCWV"
    },
    "TTFB": {
        "simple": "サーバー応答時間",
        "detail": "サーバーが応答を開始するまでの時間",
        "category": "performance",
        "for_engineer": "Time To First Byte。サーバー性能、CDN、キャッシュに依存"
    },

    # =========================================================================
    # セキュリティ (5語)
    # =========================================================================
    "HTTPS": {
        "simple": "通信の暗号化",
        "detail": "ブラウザとサーバー間の通信を暗号化して安全にする仕組み",
        "category": "security",
        "for_engineer": "TLS/SSL証明書。Let's Encryptで無料取得可能"
    },
    "CSP": {
        "simple": "スクリプト実行制限",
        "detail": "不正なプログラムの実行を防ぐブラウザの設定",
        "category": "security",
        "for_engineer": "Content-Security-Policy ヘッダー。XSS対策の重要な要素"
    },
    "X-Frame-Options": {
        "simple": "埋め込み防止設定",
        "detail": "他のサイトにページが埋め込まれるのを防ぐ設定",
        "category": "security",
        "for_engineer": "DENY/SAMEORIGIN/ALLOW-FROM。クリックジャッキング対策"
    },
    "混合コンテンツ": {
        "simple": "暗号化されていない要素",
        "detail": "HTTPSページ内にHTTPで読み込まれる画像等がある状態",
        "category": "security",
        "for_engineer": "Mixed Content。ブラウザ警告の原因。全リソースをHTTPS化"
    },
    "HSTS": {
        "simple": "常時HTTPS強制",
        "detail": "常にHTTPS通信を強制する設定",
        "category": "security",
        "for_engineer": "Strict-Transport-Security ヘッダー。max-age, includeSubDomains"
    },

    # =========================================================================
    # 法規制 (5語)
    # =========================================================================
    "YMYL": {
        "simple": "お金や健康に関わるページ",
        "detail": "Your Money Your Life の略。誤情報が人生に影響するジャンル",
        "category": "legal",
        "for_engineer": "金融、医療、法律、ニュース等。E-E-A-Tが特に重要視される"
    },
    "E-E-A-T": {
        "simple": "経験・専門性・権威性・信頼性",
        "detail": "Googleがページの信頼度を測る基準",
        "category": "legal",
        "for_engineer": "Experience, Expertise, Authoritativeness, Trustworthiness"
    },
    "景品表示法": {
        "simple": "誇大広告を禁止する法律",
        "detail": "商品やサービスの広告で嘘や大げさな表現を禁止する法律",
        "category": "legal",
        "for_engineer": "優良誤認、有利誤認、打消し表示。課徴金は売上の3%"
    },
    "薬機法": {
        "simple": "医薬品等の広告規制",
        "detail": "医薬品・化粧品・健康食品の効果効能の誇大表現を禁止",
        "category": "legal",
        "for_engineer": "旧薬事法。未承認医薬品の広告禁止、効能効果の標榜制限"
    },
    "ステマ規制": {
        "simple": "広告を隠す行為の規制",
        "detail": "広告であることを隠した宣伝（ステルスマーケティング）を禁止",
        "category": "legal",
        "for_engineer": "2023年10月施行。景品表示法の告示。PR/広告表記が必須"
    },

    # =========================================================================
    # OGP/SNS (5語) - 追加カテゴリ
    # =========================================================================
    "OGP": {
        "simple": "SNSシェア時の表示設定",
        "detail": "FacebookやXでシェアされた時の画像・タイトル・説明文の設定",
        "category": "ogp",
        "for_engineer": "Open Graph Protocol。og:title, og:description, og:image で設定"
    },
    "Twitterカード": {
        "simple": "X(Twitter)での表示設定",
        "detail": "X(Twitter)でURLをシェアした時の見え方を設定するタグ",
        "category": "ogp",
        "for_engineer": "twitter:card, twitter:title, twitter:image。summary/summary_large_image"
    },
    "og:image": {
        "simple": "シェア時の画像",
        "detail": "SNSでシェアされた時に表示される画像の設定",
        "category": "ogp",
        "for_engineer": "1200x630px推奨。絶対URL必須。JPG/PNG形式"
    },
    "og:title": {
        "simple": "シェア時のタイトル",
        "detail": "SNSでシェアされた時に表示されるタイトルの設定",
        "category": "ogp",
        "for_engineer": "60文字以内推奨。titleタグと別に設定可能"
    },
    "og:description": {
        "simple": "シェア時の説明文",
        "detail": "SNSでシェアされた時に表示される説明文の設定",
        "category": "ogp",
        "for_engineer": "80-120文字推奨（50-200文字は許容）。meta descriptionと別に設定可能"
    },
}


# =============================================================================
# 用語変換ユーティリティ関数
# =============================================================================

def get_term_display(term: str, mode: str = "simple") -> str:
    """
    用語の表示テキストを取得

    Args:
        term: 専門用語
        mode: "simple" | "detail" | "engineer"

    Returns:
        変換後のテキスト
        例: "検索エンジン向けの情報タグ（JSON-LD）"
    """
    if term not in TERM_GLOSSARY:
        return term

    entry = TERM_GLOSSARY[term]

    if mode == "engineer":
        return f"{term}: {entry['for_engineer']}"
    elif mode == "detail":
        return f"{entry['simple']}（{term}）- {entry['detail']}"
    else:  # simple
        return f"{entry['simple']}（{term}）"


def convert_text_with_glossary(
    text: str,
    mode: str = "simple",
    first_only: bool = True
) -> str:
    """
    テキスト内の専門用語を自動変換

    Args:
        text: 変換対象テキスト
        mode: 表示モード
        first_only: True=初出時のみ変換

    Returns:
        変換後テキスト
    """
    converted_terms = set()
    result = text

    # 長い用語から順に処理（部分一致を避ける）
    sorted_terms = sorted(TERM_GLOSSARY.keys(), key=len, reverse=True)

    for term in sorted_terms:
        if term in result:
            if first_only and term in converted_terms:
                continue

            display = get_term_display(term, mode)
            if first_only:
                # 最初の出現のみ置換
                result = result.replace(term, display, 1)
                converted_terms.add(term)
            else:
                result = result.replace(term, display)

    return result


def get_terms_by_category(category: str) -> List[Dict]:
    """
    カテゴリ別の用語リスト取得

    Args:
        category: "seo" | "aio" | "structured_data" | "performance" | "security" | "legal" | "ogp"

    Returns:
        [{"term": "JSON-LD", "simple": "...", ...}, ...]
    """
    return [
        {"term": term, **data}
        for term, data in TERM_GLOSSARY.items()
        if data.get("category") == category
    ]


def get_all_categories() -> List[str]:
    """全カテゴリ一覧を取得"""
    return list(set(data["category"] for data in TERM_GLOSSARY.values()))


# =============================================================================
# パーソナライズモード定義
# =============================================================================

DISPLAY_MODES = {
    "beginner": {
        "term_style": "simple",
        "show_explanation": True,
        "technical_depth": "low"
    },
    "intermediate": {
        "term_style": "detail",
        "show_explanation": True,
        "technical_depth": "medium"
    },
    "expert": {
        "term_style": "engineer",
        "show_explanation": False,
        "technical_depth": "high"
    }
}

# 業界別デフォルトモード
INDUSTRY_DEFAULT_MODES = {
    "ec_retail": "beginner",
    "healthcare": "intermediate",
    "cosmetics": "beginner",
    "food_supplement": "beginner",
    "finance": "intermediate",
    "affiliate_media": "intermediate",
    "it_saas": "expert",
    "corporate": "beginner"
}


def get_display_mode_for_industry(industry: str) -> str:
    """業界に応じたデフォルト表示モードを返す"""
    return INDUSTRY_DEFAULT_MODES.get(industry, "beginner")


def get_mode_config(mode: str) -> Dict:
    """モード設定を取得"""
    return DISPLAY_MODES.get(mode, DISPLAY_MODES["beginner"])


# =============================================================================
# FAQ生成テンプレート
# =============================================================================

TERM_FAQ_TEMPLATES = {
    "JSON-LD": {
        "question": "JSON-LDとは何ですか？設定しないとどうなりますか？",
        "answer_simple": "検索エンジンがページの内容を正しく理解するための設定です。設定しなくても検索には出ますが、検索結果での表示が地味になり、クリックされにくくなる可能性があります。",
        "answer_detail": "JSON-LD（JavaScript Object Notation for Linked Data）は、Schema.org語彙を使用してページの情報を構造化する形式です。これにより、検索エンジンはページの内容（商品情報、記事情報、会社情報など）を正確に理解でき、リッチリザルト（星評価、価格表示など）として検索結果に表示される可能性があります。"
    },
    "構造化データ": {
        "question": "構造化データを設定するメリットは？",
        "answer_simple": "検索結果で目立つ表示（星評価、価格、画像など）が出るようになり、クリック率が上がる可能性があります。",
        "answer_detail": "構造化データを設定すると、Google検索結果でリッチリザルト（リッチスニペット）として表示される可能性があります。例えば、商品ページなら価格・在庫・評価、レシピなら調理時間・カロリーなどが表示されます。Googleの調査によると、リッチリザルトはクリック率を最大30%向上させることがあります。"
    },
    "OGP": {
        "question": "OGPとは？設定しないとどうなる？",
        "answer_simple": "FacebookやXでシェアされた時の見え方を設定するものです。設定しないと、シェアした時に画像が出なかったり、タイトルが正しく表示されないことがあります。",
        "answer_detail": "OGP（Open Graph Protocol）は、SNSでURLがシェアされた際に表示されるタイトル、説明文、画像を制御するmetaタグです。設定がないと、SNSのクローラーがページから自動抽出した情報が表示され、意図しない見た目になることがあります。"
    },
    "HTTPS": {
        "question": "HTTPSに対応していないとどうなる？",
        "answer_simple": "ブラウザに「安全ではありません」と警告が出て、ユーザーが不安になります。また、SEOでも不利になります。",
        "answer_detail": "HTTPSに対応していない場合、Chrome等のブラウザでアドレスバーに「保護されていない通信」と警告が表示されます。これにより訪問者の離脱率が上がります。また、GoogleはHTTPSをランキング要因として公表しており、SEO面でも不利になります。"
    },
    "景品表示法": {
        "question": "景品表示法に違反するとどうなる？",
        "answer_simple": "消費者庁から措置命令が出て、会社名が公表されます。悪質な場合は売上の3%を課徴金として払う必要があります。",
        "answer_detail": "景品表示法違反が認定されると、措置命令（違反行為の差止め、再発防止策の実施命令等）が出されます。命令内容は消費者庁のウェブサイトで公表され、報道されることもあります。2016年の改正で課徴金制度が導入され、違反した表示に係る商品・サービスの売上額の3%が課徴金として課されます。"
    },
    "ステマ規制": {
        "question": "ステマ規制とは？何に気をつければいい？",
        "answer_simple": "広告であることを隠して宣伝する行為が禁止されました（2023年10月から）。アフィリエイトや商品提供を受けたレビューには「PR」「広告」等の表記が必要です。",
        "answer_detail": "2023年10月1日施行のステルスマーケティング規制は、景品表示法の告示として定められました。事業者が広告であることを隠して第三者に宣伝させる行為が不当表示として禁止されています。アフィリエイト記事、インフルエンサーマーケティング、商品提供を受けたレビューなどは、記事の冒頭等の分かりやすい位置に「PR」「広告」「プロモーション」等の表記が必要です。"
    },
    # --- 追加FAQ ---
    "AI Overview": {
        "question": "AI Overviewとは？対策は必要？",
        "answer_simple": "Google検索結果の上部に表示されるAIが作った要約です。ここに引用されると多くの人の目に触れますが、サイトへのクリックが減る可能性もあります。",
        "answer_detail": "AI Overview（旧SGE）はGoogle検索結果の最上部に表示されるAI生成の回答です。ここに情報源として引用されるためには、E-E-A-T（経験・専門性・権威性・信頼性）の高いコンテンツ、構造化データの適切な実装、明確な定義文（「〇〇とは△△です」形式）が重要です。"
    },
    "llms.txt": {
        "question": "llms.txtとは？設定した方がいい？",
        "answer_simple": "ChatGPTなどのAIに「このサイトの情報を使ってください」と伝えるファイルです。AIに情報を引用してもらいたい場合は設定すると効果的です。",
        "answer_detail": "llms.txtはrobots.txtのAI版として提案されている仕様です。/llms.txt, /llms-full.txt, /llms.md の形式でサイトルートに配置し、AIクローラーに読ませたいコンテンツの概要やリンクを記載します。AIによる引用を積極的に得たい場合は設定を推奨します。"
    },
    "canonical": {
        "question": "canonicalタグは必要？設定しないとどうなる？",
        "answer_simple": "同じ内容のページが複数ある場合に必要です。設定しないと、検索エンジンが勝手にどれが本物か決めてしまい、意図しないページが検索結果に出ることがあります。",
        "answer_detail": "canonicalタグは重複コンテンツ問題を解決するために使用します。例えば、http/https、www有無、パラメータ付きURLなどで同じ内容が複数URLで存在する場合、正規URLを指定しないとページの評価が分散したり、意図しないURLがインデックスされる可能性があります。"
    },
    "コアウェブバイタル": {
        "question": "コアウェブバイタルが悪いとどうなる？",
        "answer_simple": "ページの表示が遅かったりガタつくと、ユーザーが離脱しやすくなります。また、Googleの検索順位にも影響します。",
        "answer_detail": "コアウェブバイタル（LCP/INP/CLS）はGoogleのランキング要因の一つです。特にモバイル検索では、同程度の品質のページ同士ではコアウェブバイタルのスコアが高いページが優先される傾向があります。また、ユーザー体験に直結するため、直帰率やコンバージョン率にも影響します。"
    },
    "返品・交換": {
        "question": "返品・交換はできますか？",
        "answer_simple": "商品到着後○日以内かつ未使用・未開封の場合に返品・交換が可能です。返送料の負担や対象外条件は返品ポリシーをご確認ください。",
        "answer_detail": "返品・交換の可否、対象条件（未使用・未開封等）、期限、返送料の負担、返金方法を明記するとユーザーの不安が減ります。テンプレとしては「商品到着後○日以内・未使用品に限り可、返送料はお客様負担（不良品は当社負担）」などが一般的です。",
        "priority": "high",
    },
    "配送・送料": {
        "question": "送料はいくらですか？配送方法は？",
        "answer_simple": "配送方法は○○便、送料は地域別に○○円です。○○円以上のご注文で送料無料などの条件を明記します。",
        "answer_detail": "配送方法、送料、地域差、送料無料の条件、配送日時指定の可否を記載すると購入ハードルが下がります。例: 「全国一律○○円、○○円以上で送料無料、通常○-○営業日で発送」。",
        "priority": "high",
    },
    "支払い方法": {
        "question": "支払い方法は何が使えますか？",
        "answer_simple": "クレジットカード、銀行振込、代金引換、コンビニ払いなどに対応しています。利用可能ブランドと手数料の有無を記載してください。",
        "answer_detail": "支払い方法の種類、利用可能ブランド、手数料や支払期限を明記すると離脱を防げます。例: 「VISA/Master/JCB、振込は7日以内、代引手数料○○円」。",
        "priority": "high",
    },
    "キャンセル": {
        "question": "注文のキャンセルはできますか？",
        "answer_simple": "発送前であればキャンセル可能です。発送後は返品扱いとなるため、期限と手続き方法をご確認ください。",
        "answer_detail": "キャンセル可能なタイミング、手続き方法、手数料、返金の流れを明記します。例: 「発送前は○○まで連絡で可、発送後は返品規定に準拠」。",
        "priority": "medium",
    },
    "注文変更": {
        "question": "注文内容の変更はできますか？",
        "answer_simple": "発送前であれば変更可能な場合があります。変更希望は○○までご連絡ください。",
        "answer_detail": "変更可否、変更期限、連絡手段を記載すると問い合わせが減ります。例: 「発送前のみ変更可、マイページ/問い合わせフォームから連絡」。",
        "priority": "medium",
    },
    "お問い合わせ": {
        "question": "問い合わせ方法と対応時間は？",
        "answer_simple": "お問い合わせはフォーム/メール/電話で受け付けています。受付時間は平日○時〜○時です。",
        "answer_detail": "問い合わせ窓口、受付時間、返信目安を明記すると安心感が高まります。例: 「平日10-17時、1-2営業日以内に回答」。",
        "priority": "medium",
    },
}


def generate_faq_for_issues(issues: List[str], mode: str = "simple") -> List[Dict]:
    """
    検出された問題に基づいてFAQを動的生成

    Args:
        issues: 検出された問題のリスト（用語名）
        mode: "simple" | "detail"

    Returns:
        [{"question": "...", "answer": "..."}, ...]
    """
    faqs = []
    for issue in issues:
        if issue in TERM_FAQ_TEMPLATES:
            template = TERM_FAQ_TEMPLATES[issue]
            answer_key = "answer_simple" if mode == "simple" else "answer_detail"
            faqs.append({
                "question": template["question"],
                "answer": template[answer_key]
            })
    return faqs


EC_FAQ_TEMPLATE_KEYS = [
    "返品・交換",
    "配送・送料",
    "支払い方法",
    "キャンセル",
    "注文変更",
    "お問い合わせ",
]


def get_ec_faq_templates(mode: str = "simple") -> List[Dict]:
    """EC向けFAQテンプレートを取得"""
    answer_key = "answer_simple" if mode == "simple" else "answer_detail"
    templates = []
    for key in EC_FAQ_TEMPLATE_KEYS:
        template = TERM_FAQ_TEMPLATES.get(key)
        if not template:
            continue
        templates.append({
            "question": template.get("question", ""),
            "answer": template.get(answer_key, ""),
            "priority": template.get("priority", "medium"),
        })
    return templates


def get_all_faqs(mode: str = "simple") -> List[Dict]:
    """全FAQを取得"""
    answer_key = "answer_simple" if mode == "simple" else "answer_detail"
    return [
        {"question": t["question"], "answer": t[answer_key]}
        for t in TERM_FAQ_TEMPLATES.values()
    ]


# =============================================================================
# 用語検索・フィルタリング
# =============================================================================

def search_terms(query: str) -> List[Dict]:
    """
    用語を検索（部分一致）

    Args:
        query: 検索クエリ

    Returns:
        マッチした用語のリスト
    """
    query_lower = query.lower()
    results = []

    for term, data in TERM_GLOSSARY.items():
        # 用語名、simple、detail、for_engineer のいずれかにマッチ
        if (query_lower in term.lower() or
            query_lower in data["simple"] or
            query_lower in data["detail"] or
            query_lower in data["for_engineer"]):
            results.append({"term": term, **data})

    return results


def get_related_terms(term: str) -> List[str]:
    """
    関連用語を取得（同じカテゴリの用語）

    Args:
        term: 基準となる用語

    Returns:
        関連用語のリスト
    """
    if term not in TERM_GLOSSARY:
        return []

    category = TERM_GLOSSARY[term]["category"]
    return [
        t for t in TERM_GLOSSARY.keys()
        if TERM_GLOSSARY[t]["category"] == category and t != term
    ]


def get_glossary_stats() -> Dict:
    """用語辞書の統計情報を取得"""
    categories = {}
    for data in TERM_GLOSSARY.values():
        cat = data["category"]
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "total_terms": len(TERM_GLOSSARY),
        "categories": categories,
        "faq_count": len(TERM_FAQ_TEMPLATES)
    }


def extract_terms_from_text(text: str, max_terms: int = 10) -> List[Dict]:
    """
    テキストに含まれる専門用語を抽出（出現順）

    Args:
        text: 対象テキスト
        max_terms: 最大抽出数

    Returns:
        [{"term": "...", "simple": "...", "detail": "...", "category": "..."}]
    """
    if not text:
        return []

    text_lower = text.lower()
    hits = []
    for term, data in TERM_GLOSSARY.items():
        term_lower = term.lower()
        index = -1
        if term_lower in text_lower:
            index = text_lower.find(term_lower)
        elif term in text:
            index = text.find(term)
        if index >= 0:
            hits.append((index, term, data))

    if not hits:
        return []

    hits.sort(key=lambda x: x[0])
    results: List[Dict] = []
    seen = set()
    for _, term, data in hits:
        if term in seen:
            continue
        results.append({
            "term": term,
            "simple": data.get("simple", ""),
            "detail": data.get("detail", ""),
            "category": data.get("category", ""),
        })
        seen.add(term)
        if len(results) >= max_terms:
            break

    return results
