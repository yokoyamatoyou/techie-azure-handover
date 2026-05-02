"""
Knowledge Graph Entity List for Entity Linking.
Contains well-known entities from various categories.
This is a simplified approach without external API calls.

Phase 3 (2026-01-29): 静的辞書の役割変更
- KNOWN_ENTITIES: 旧辞書（後方互換性のため残す、将来削除予定）
- SUPPLEMENTARY_ENTITIES: 新しい補完辞書（Sudachi未対応の新語用）
"""

import warnings

# Well-known entities in Japanese
# Categories: Historical Figures, Places, Companies, Concepts, etc.

KNOWN_ENTITIES = {
    # ========== Technology & Programming ==========
    # プログラミング言語
    "AI", "人工知能", "機械学習", "深層学習", "ディープラーニング",
    "Python", "JavaScript", "Java", "C++", "Go", "TypeScript", "Rust", "Kotlin", "Swift", "Ruby", "PHP", "C#", "Scala", "R", "MATLAB",
    "Perl", "Haskell", "Elixir", "Clojure", "Dart", "Lua", "Julia", "Fortran", "COBOL", "Assembly",

    # フレームワーク・ライブラリ
    "React", "Vue", "Angular", "Django", "Flask", "FastAPI", "Express", "Spring", "Laravel", "Rails",
    "TensorFlow", "PyTorch", "Keras", "scikit-learn", "NumPy", "Pandas", "jQuery", "Bootstrap",

    # AI/ML用語
    "自然言語処理", "NLP", "コンピュータビジョン", "強化学習", "教師あり学習", "教師なし学習",
    "ニューラルネットワーク", "CNN", "RNN", "LSTM", "GAN", "Transformer", "BERT", "GPT",
    "データサイエンス", "ビッグデータ", "クラウドコンピューティング", "エッジコンピューティング",
    "ブロックチェーン", "量子コンピューティング", "IoT", "5G", "AR", "VR", "メタバース",
    "インターネット", "クラウド", "暗号通貨", "ビットコイン",
    "SEO", "マーケティング", "SNS", "Twitter", "Facebook", "Instagram", "YouTube", "TikTok",

    # ========== Business & Economics ==========
    # 経営理論
    "SWOT分析", "5フォース分析", "PDCA", "KPI", "OKR", "ブルーオーシャン戦略",
    "破壊的イノベーション", "リーンスタートアップ", "アジャイル", "スクラム",
    "デザイン思考", "カスタマージャーニー", "ペルソナ", "MVP",

    # マーケティング用語
    "コンテンツマーケティング", "インバウンドマーケティング",
    "グロースハック", "A/Bテスト", "コンバージョン率", "LTV", "CAC", "ROI",
    "ファネル", "リードジェネレーション", "ナーチャリング",

    # 経済用語
    "GDP", "インフレ", "デフレ", "金融政策", "財政政策", "サプライチェーン",
    "ESG", "SDGs", "カーボンニュートラル", "DX", "働き方改革",
    "政府", "経済", "政治", "社会", "文化", "教育",
    "健康", "医療", "病院", "大学", "学校", "企業",
    "ビジネス", "市場", "株式", "投資", "銀行",

    # ========== Geography - Cities ==========
    # 日本の都市
    "東京", "大阪", "京都", "名古屋", "福岡", "札幌", "横浜", "千葉", "埼玉",
    "神戸", "広島", "仙台", "新潟", "浜松", "静岡", "岡山", "熊本", "鹿児島",
    "金沢", "富山", "長野", "松本", "岐阜", "奈良", "和歌山", "大津", "津",
    "高松", "松山", "高知", "那覇", "宮崎", "長崎", "佐賀", "大分",

    # 世界の主要都市
    "ニューヨーク", "ロサンゼルス", "シカゴ", "サンフランシスコ", "ボストン",
    "ロンドン", "パリ", "ベルリン", "ローマ", "マドリード", "バルセロナ",
    "モスクワ", "サンクトペテルブルク",
    "北京", "上海", "深セン", "広州", "香港", "台北", "バンコク", "シンガポール",
    "ソウル", "釜山", "ムンバイ", "デリー", "バンガロール",
    "シドニー", "メルボルン", "オークランド",
    "ドバイ", "イスタンブール", "カイロ",
    "サンパウロ", "リオデジャネイロ", "メキシコシティ",
    "トロント", "バンクーバー",

    # 観光地
    "富士山", "京都タワー", "東京スカイツリー", "東京タワー", "大阪城",
    "姫路城", "金閣寺", "銀閣寺", "清水寺", "厳島神社", "出雲大社",
    "エッフェル塔", "自由の女神", "ビッグベン", "コロッセオ", "サグラダファミリア",
    "万里の長城", "タージマハル", "アンコールワット", "マチュピチュ",

    # ========== Countries ==========
    "日本", "アメリカ", "中国", "韓国", "台湾", "イギリス",
    "フランス", "ドイツ", "イタリア", "スペイン", "カナダ",
    "オーストラリア", "ブラジル", "インド", "ロシア",

    # ========== Historical Figures ==========
    # 日本史
    "徳川家康", "織田信長", "豊臣秀吉", "坂本龍馬", "西郷隆盛",
    "聖徳太子", "源頼朝", "源義経", "北条時宗", "足利尊氏", "足利義満",
    "武田信玄", "上杉謙信", "伊達政宗", "真田幸村", "石田三成", "明智光秀",
    "福沢諭吉", "夏目漱石", "芥川龍之介", "太宰治", "手塚治虫",
    "平清盛", "卑弥呼", "紫式部", "清少納言", "松尾芭蕉",

    # 世界史
    "ソクラテス", "プラトン", "アリストテレス", "孔子", "釈迦", "イエス", "ムハンマド",
    "アレクサンダー大王", "カエサル", "ナポレオン", "チンギスハン",
    "レオナルド・ダ・ヴィンチ", "ミケランジェロ", "ピカソ", "ゴッホ", "モネ",
    "ニュートン", "アインシュタイン", "ダーウィン", "ガリレオ", "エジソン", "テスラ",
    "シェイクスピア", "ゲーテ", "ドストエフスキー", "トルストイ",
    "ワシントン", "リンカーン", "ケネディ", "チャーチル", "ガンジー", "マンデラ",

    # ========== Companies ==========
    # 日本企業
    "トヨタ", "ソニー", "任天堂", "パナソニック", "日立",
    "三菱", "三井", "住友", "ホンダ", "日産", "マツダ", "スズキ", "ダイハツ",
    "富士通", "NEC", "東芝", "シャープ", "キヤノン", "リコー", "エプソン",
    "ユニクロ", "ニトリ", "無印良品", "セブンイレブン", "ローソン", "ファミリーマート",
    "イオン", "セブン&アイ", "楽天", "ヤフー", "LINE", "メルカリ", "サイバーエージェント",
    "DeNA", "グリー", "コナミ", "バンダイナムコ", "スクエアエニックス", "カプコン",
    "JR東日本", "JR西日本", "ANA", "JAL", "NTT", "KDDI", "ソフトバンク",

    # 海外企業
    "Apple", "Microsoft", "Google", "Amazon", "Meta", "Facebook", "Tesla", "Netflix", "Uber",
    "IBM", "Intel", "AMD", "NVIDIA", "Cisco", "Oracle", "Salesforce", "Adobe", "Zoom",
    "Samsung", "LG", "Huawei", "Xiaomi", "Alibaba", "Tencent", "Baidu",
    "Volkswagen", "BMW", "Mercedes-Benz", "Ferrari", "Porsche",
    "Coca-Cola", "Pepsi", "McDonald's", "Starbucks", "KFC",
    "Nike", "Adidas", "ZARA", "H&M", "IKEA",

    # ========== Science & Medicine ==========
    "DNA", "RNA", "遺伝子", "ゲノム", "タンパク質", "細胞", "幹細胞", "iPS細胞",
    "ワクチン", "抗生物質", "免疫", "ウイルス", "バクテリア",
    "がん", "糖尿病", "高血圧", "認知症", "アルツハイマー", "パーキンソン病",
    "MRI", "CT", "X線", "超音波", "内視鏡",
    "再生医療", "遺伝子治療", "免疫療法", "分子標的薬", "オーダーメイド医療",
    "地球", "太陽", "月", "火星", "木星", "銀河",
    "気候変動", "温暖化", "環境", "エネルギー", "再生可能エネルギー",

    # ========== Sports & Entertainment ==========
    "野球", "サッカー", "テニス", "ゴルフ", "バスケットボール", "ラグビー",
    "フィギュアスケート", "体操", "水泳", "陸上競技", "マラソン",
    "オリンピック", "ワールドカップ", "パラリンピック",
    "FIFA", "NBA", "MLB",
    "大谷翔平", "羽生結弦", "錦織圭", "メッシ", "ロナウド", "ジョーダン", "タイガーウッズ",
    "映画", "音楽", "アニメ", "漫画", "ゲーム",
    "アカデミー賞", "グラミー賞", "カンヌ映画祭",

    # ========== Food & Culture ==========
    "寿司", "ラーメン", "天ぷら", "うどん", "そば",
    "ピザ", "パスタ", "ハンバーガー", "カレー",
    "茶道", "華道", "書道", "歌舞伎", "能", "狂言",
}


def is_known_entity(entity: str) -> bool:
    """
    [DEPRECATED] Use Sudachi pos[1]=='固有名詞' or is_supplementary_entity() instead.

    Check if an entity is in the known entities list.

    Args:
        entity: Entity string to check

    Returns:
        True if entity is known, False otherwise
    """
    warnings.warn(
        "is_known_entity() is deprecated. Use Sudachi proper noun detection or is_supplementary_entity().",
        DeprecationWarning,
        stacklevel=2
    )
    return entity in KNOWN_ENTITIES


def calculate_entity_recognition_score(entities: list) -> dict:
    """
    [DEPRECATED] Use AIOContentAnalyzer.calculate_entity_linking() instead.

    Calculate knowledge graph entity recognition score with weighted importance.

    Args:
        entities: List of entity strings

    Returns:
        dict with:
        - score: 0.0-1.0 (ratio of known entities)
        - weighted_score: 0.0-1.0 (weighted score for future expansion)
        - known_entities: List of recognized entities (top 20)
        - unknown_entities: List of unrecognized entities (top 10)
        - total_entities: Total number of entities
        - known_count: Number of known entities
        - unknown_count: Number of unknown entities
    """
    warnings.warn(
        "calculate_entity_recognition_score() is deprecated. Use AIOContentAnalyzer.calculate_entity_linking().",
        DeprecationWarning,
        stacklevel=2
    )
    if not entities:
        return {
            "score": 0.0,
            "weighted_score": 0.0,
            "known_entities": [],
            "unknown_entities": [],
            "total_entities": 0,
            "known_count": 0,
            "unknown_count": 0,
            "diagnosis": "本文から固有名詞が検出できません"
        }

    known = [e for e in entities if is_known_entity(e)]
    unknown = [e for e in entities if not is_known_entity(e)]

    total = len(entities)
    basic_score = len(known) / total if total > 0 else 0.0

    if total == 0:
        diagnosis = "本文から固有名詞が検出できません"
    elif len(known) == 0:
        diagnosis = "一般的に知られた固有名詞が少なく、独自用語が多い可能性があります"
    elif basic_score < 0.2:
        diagnosis = "既知エンティティが少なめです。一般名称や公式名称を明示すると改善します"
    elif basic_score < 0.5:
        diagnosis = "既知エンティティが一部のみ検出されています"
    else:
        diagnosis = "良好（一般的に認知された固有名詞が含まれています）"

    # Weighted score (将来的な拡張: エンティティタイプ別の重み付け)
    weighted_score = basic_score  # 現時点では同じ

    return {
        "score": round(basic_score, 2),
        "weighted_score": round(weighted_score, 2),
        "known_entities": known[:20],  # 上位20件のみ返す
        "unknown_entities": unknown[:10],  # 上位10件のみ返す
        "total_entities": total,
        "known_count": len(known),
        "unknown_count": len(unknown),
        "diagnosis": diagnosis
    }


# =============================================
# Phase 2: エンティティカテゴリ別の重み付け
# Sudachi品詞体系: pos[2] の値に対応
# Added: 2026-01-29
# =============================================

ENTITY_CATEGORY_WEIGHTS = {
    # 組織系（E-E-A-Tの権威性に直結）
    "一般": 1.0,       # 組織名（会社、団体等）

    # 人名系（著者・専門家の言及）
    "人名": 1.2,       # 人名全般（権威性に重要）
    "姓": 1.1,
    "名": 1.0,

    # 地名系（ローカルSEOに有効）
    "地名": 1.0,
    "国": 1.0,

    # その他
    "固有名詞": 0.9,   # 一般的な固有名詞
    "default": 0.8     # 分類不明
}


def get_category_weight(category: str) -> float:
    """
    エンティティカテゴリから重みを取得

    Args:
        category: Sudachi品詞のpos[2]値

    Returns:
        重み係数 (0.8-1.2)
    """
    return ENTITY_CATEGORY_WEIGHTS.get(category, ENTITY_CATEGORY_WEIGHTS["default"])


# =============================================
# Phase 3: 補完用エンティティ辞書
# Sudachi辞書に含まれない可能性のある新語・専門用語
# Added: 2026-01-29
# =============================================

# AI/テクノロジー関連の新語（2024年以降）
AI_TECH_ENTITIES = {
    # LLM/生成AI
    "ChatGPT", "GPT-4", "GPT-4o", "GPT-4.5", "Claude", "Gemini", "Perplexity",
    "Copilot", "Midjourney", "DALL-E", "Stable Diffusion", "Sora",
    "RAG", "LangChain", "LlamaIndex", "LLM", "SLM",
    "Llama", "Mistral", "Mixtral", "Phi", "Qwen",

    # AI検索/SEO新概念
    "AIO", "GEO", "llms.txt", "AI Overview", "SGE",
    "E-E-A-T", "EEAT", "YMYL",
    "AEO", "Answer Engine Optimization",

    # 技術トレンド
    "Web3", "DePIN", "RWA", "Layer2", "zkEVM", "zkSync",
    "Rust", "Bun", "Deno", "htmx", "Astro",
}

# マーケティング/ビジネス新語
MARKETING_ENTITIES = {
    "コンテンツマーケティング", "インフルエンサーマーケティング",
    "ゼロクリック検索", "フィーチャードスニペット",
    "Core Web Vitals", "INP", "LCP", "CLS", "FID",
    "GA4", "GTM", "GSC",
    "リスティング広告", "ディスプレイ広告", "P-MAX",
    "MQL", "SQL", "ABM",
}

# 法規制/コンプライアンス用語
LEGAL_ENTITIES = {
    "特商法", "景表法", "ステマ規制",
    "GDPR", "個人情報保護法", "電気通信事業法",
    "Cookie規制", "オプトアウト", "オプトイン",
    "AI規制法", "著作権法",
}

# 補完辞書の統合
SUPPLEMENTARY_ENTITIES = (
    AI_TECH_ENTITIES |
    MARKETING_ENTITIES |
    LEGAL_ENTITIES
)


def is_supplementary_entity(entity: str) -> bool:
    """
    補完辞書に含まれるエンティティかどうかを判定

    Args:
        entity: エンティティ文字列

    Returns:
        True if entity is in supplementary dictionary
    """
    return entity in SUPPLEMENTARY_ENTITIES


# =============================================
# Phase 4: 正規化ルール
# Sudachi正規化で対応しきれないケースの補完
# Added: 2026-01-29
# =============================================

# 大文字小文字の統一（英語エンティティ用）
CASE_NORMALIZATION = {
    "toyota": "トヨタ",
    "sony": "ソニー",
    "honda": "ホンダ",
    "nissan": "日産",
    "panasonic": "パナソニック",
    "nintendo": "任天堂",
    "google": "Google",
    "apple": "Apple",
    "microsoft": "Microsoft",
    "amazon": "Amazon",
    "facebook": "Facebook",
    "meta": "Meta",
}

# 表記ゆれパターン（カタカナ→英語統一）
VARIANT_MAP = {
    "グーグル": "Google",
    "アップル": "Apple",
    "マイクロソフト": "Microsoft",
    "アマゾン": "Amazon",
    "フェイスブック": "Facebook",
    "ツイッター": "X",
    "インスタグラム": "Instagram",
    "ユーチューブ": "YouTube",
    "ネットフリックス": "Netflix",
    "テスラ": "Tesla",
}


def normalize_entity(surface: str, sudachi_normalized: str = None) -> str:
    """
    エンティティ表記を正規化

    Args:
        surface: 表層形
        sudachi_normalized: Sudachiの正規化形（あれば）

    Returns:
        正規化されたエンティティ名
    """
    # 1. Sudachi正規化形があればそれを使用
    if sudachi_normalized and sudachi_normalized != surface:
        return sudachi_normalized

    # 2. 小文字化してマッピング確認
    lower = surface.lower()
    if lower in CASE_NORMALIZATION:
        return CASE_NORMALIZATION[lower]

    # 3. 表記ゆれマップ確認
    if surface in VARIANT_MAP:
        return VARIANT_MAP[surface]

    # 4. 変換なし
    return surface


def group_entities_by_normalized(entities: list) -> dict:
    """
    正規化形でエンティティをグループ化

    Args:
        entities: [{"surface": "...", "normalized": "...", ...}, ...]

    Returns:
        {
            "正規化形": {
                "count": 出現回数,
                "variants": ["表記1", "表記2", ...],
                "category": カテゴリ
            }
        }
    """
    groups = {}

    for entity in entities:
        surface = entity.get("surface", "")
        sudachi_norm = entity.get("normalized", surface)
        category = entity.get("category", "一般")

        # 正規化
        normalized = normalize_entity(surface, sudachi_norm)

        if normalized not in groups:
            groups[normalized] = {
                "count": 0,
                "variants": [],
                "category": category
            }

        groups[normalized]["count"] += 1
        if surface not in groups[normalized]["variants"]:
            groups[normalized]["variants"].append(surface)

    return groups
