"""Constants and regex symbols shared by quarantined legacy mixins."""
from __future__ import annotations

import re

ARTICLE_TYPE_LABELS = {
    "branding": "商品・サービスブランディング",
    "ai": "解説記事",
    "announcement": "お知らせ・アップデート",
    "case_study": "導入事例・ケーススタディ",
}

ARTICLE_TYPE_PROMPTS = {
    "branding": """
【内部ガイド】目的: 商品・サービスの価値を共感できる物語として伝える
【スタイル: Emotional & Visionary】
1. 導入(Origin): なぜこの商品・サービスが必要とされたのか、現場の課題から始める。
2. 展開(Struggle): 開発や提供までの試行錯誤、顧客理解のプロセスを具体的に描く。
3. 転換(Value): 使う人にどんな変化が生まれるかを、体験ベースで言語化する。
4. 結び(Action): 読者が試せる具体的な選択肢（体験・比較・相談）を示す。
【禁止】スペック羅列、誇大な最上級表現、押し売りの宣伝文句。
""".strip(),
    "ai": """
【内部ガイド】目的: 専門情報やトピックを、読者が行動できる理解に翻訳する
【スタイル: Informative & Story】
1. 導入(Hook): 何がわかる記事かを冒頭で明示し、読者の疑問と接続する。
2. 解説(PREP): 用語や仕組みを噛み砕き、具体例で理解を固定する。
3. 視点: メリットだけでなく注意点や前提条件も示し、判断材料を渡す。
4. 結び: 読者がすぐ試せる確認ポイントや具体例を示す。
【禁止】仕様書の要約のような無機質な文章。「〜です。〜ます。」の連続。
""".strip(),
    "announcement": """
【内部ガイド】目的: お知らせ・アップデート情報を、短く正確に、誤解なく伝える
【スタイル: Brief & Clear】
1. 導入(Summary): 何がいつ変わるのかを1〜2文で先に示す。
2. 本文(Details): 変更点を箇条書きではなく短段落で整理し、対象読者を明確にする。
3. 影響(Impact): 読者にとっての影響と、必要な対応を具体化する。
4. 結び(Action): 次のアクション（確認先・期限・問い合わせ）を明記する。
【禁止】曖昧な告知、過度な煽り、背景説明の長文化。
""".strip(),
    "case_study": """
【内部ガイド】目的: 導入事例を通じて、再現可能な学びを読者に渡す
【スタイル: Evidence & Narrative】
1. 導入(Context): どんな課題を持つ組織・担当者の事例かを短く定義する。
2. 実行(Process): 何をどう進めたかを時系列で整理し、意思決定ポイントを示す。
3. 成果(Result): 定量/定性の変化を示し、再現条件と限界も添える。
4. 結び(Action): 読者が自分の現場で試せる最小ステップに落とし込む。
【禁止】成功談の美化、背景条件を無視した断定。
""".strip(),
}

LINKEDIN_MIN_CHARS = 387
LINKEDIN_MAX_CHARS = 1568
EDITOR_CONSISTENCY_MAX_RETRIES = 2
EDITOR_CONSISTENCY_CONTEXT_LIMIT = 4500
READABILITY_POLISH_CONTEXT_LIMIT = 2800
READABILITY_POLISH_MAX_REWRITE_RATIO = 0.16
VERIFICATION_MAX_REWRITE_RATIO = 0.50
NON_CASUAL_COLLOQUIAL_ENDING_MAX = 2
SIMILARITY_NGRAM_SIZE = 3
SIMILARITY_NGRAM_MAX_LEN = 2200
REDUNDANT_SECTION_JACCARD_THRESHOLD = 0.48
REDUNDANT_SECTION_CONTAINMENT_THRESHOLD = 0.74
REDUNDANT_EXPANSION_JACCARD_THRESHOLD = 0.48
REDUNDANT_EXPANSION_CONTAINMENT_THRESHOLD = 0.74
BODY_PARAGRAPH_DEDUPE_JACCARD_THRESHOLD = 0.64
BODY_PARAGRAPH_DEDUPE_CONTAINMENT_THRESHOLD = 0.86
SECTION_OPENING_SIMILARITY_THRESHOLD = 0.82
SECTION_OPENING_JACCARD_THRESHOLD = 0.56
SECTION_OPENING_CONTAINMENT_THRESHOLD = 0.80

REDUNDANT_SUMMARY_MARKERS = (
    "つまり",
    "要するに",
    "要点は",
    "要点としては",
    "結論として",
    "まとめると",
    "ひと言で言うと",
    "ここまでをまとめると",
    "ここまでの要点は",
    "押さえておきたいのは",
    "言い換えると",
    "この違いは",
    "この現象の背景には",
    "この背景を理解すると",
    "この核心を押さえれば",
    "この核心を押さえると",
    "この点を理解すれば",
    "この点を理解すると",
    "平均的とは要するに",
)

ABSTRACT_COMPRESSION_REWRITES = (
    (r"という観点から見ると", "から見ると"),
    (r"という観点から", "の観点で"),
    (r"において", "で"),
    (r"における", "の"),
    (r"ことに起因している", "ことが原因です"),
    (r"ことが背景にある", "背景にある"),
    (r"^(?:心がけているのは|目指しているのは)(?:、|,)?(?:たとえば|例えば)(?:、|,)?", "たとえば、"),
    (r"^(?:心がけているのは|目指しているのは)(?:、|,)?", ""),
    (r"^その理由の一つは、", "理由の一つは、"),
)

LEXICAL_PRIMING_STOPWORDS = {
    "これ",
    "それ",
    "あれ",
    "この",
    "その",
    "あの",
    "ここ",
    "そこ",
    "ため",
    "こと",
    "もの",
    "よう",
    "ところ",
    "です",
    "ます",
    "した",
    "して",
    "いる",
    "ある",
    "なる",
    "また",
    "そして",
    "ただし",
    "さらに",
    "まず",
    "次に",
}

FINGERPRINT_PROMPT_HINTS = {
    "sentence_length_cv_flat": "文の長さを短・中・長で揺らし、同じリズムを3文以上続けない。",
    "paragraph_length_cv_flat": "段落の長短を固定せず、1〜2文段落と4文前後段落を混在させる。",
    "conjunction_rate_high": "段落冒頭の接続詞を減らし、無接続で始める段落を増やす。",
    "subject_explicit_high": "主語が明らかな文では主語を省略し、プロドロップを優先する。",
    "particle_entropy_low": "「は」「が」に偏らないよう助詞の分布を散らす。",
    "bigram_mono_low": "文頭パターンを分散し、同じ語順の連続を避ける。",
    "mtld_low": "同じ語を続けず、具体語と抽象語の語彙レンジを広げる。",
    "nominalization_rate_high": "「〜のため/こと/状態」連打を減らし、具体主語+動詞で言い切る。",
    "sentence_ending_entropy_low": "文末を固定せず、終止の型を段落内で分散させる。",
    "morphological_ngram_entropy_low": "語尾や助詞の連結パターンを固定せず、短文と複文を混在させる。",
    "pos_sequence_entropy_low": "品詞配列を単調化せず、修飾句と述部の位置を段落ごとに変える。",
    "inflection_entropy_low": "活用形（現在/過去/否定/推量）を偏らせず、時制とモダリティを分散させる。",
    "sentence_ending_fine_entropy_low": "語尾形態素（です/ます/た/ない等）の並びを単調にしない。",
    "sentence_opening_entropy_low": "文頭を主語開始に固定せず、副詞句や目的語先行を混ぜる。",
    "comma_position_cv_low": "読点位置を等間隔にせず、文の構造に合わせて強弱をつける。",
    "vocab_repetition": "頻出語の言い換えか文構造変更で、同一語の近接反復を抑える。",
    "syntactic_complexity_low": "単文の連打を避け、従属節や補足句を適度に混ぜる。",
    "ending_repetition": "同種の終止形が連続したら、意味を保って終止バリエーションを挿入する。",
    "comma_overuse": "読点でつなぎすぎず、文を分割して主述の対応を明確にする。",
    "abstract_tautology": "同義抽象語の反復説明を削り、具体例か固有情報に置き換える。",
}

FINGERPRINT_HINT_KEY_ALIASES = {
    "sentence_length_cv": "sentence_length_cv_flat",
    "paragraph_length_cv": "paragraph_length_cv_flat",
    "conjunction_repetition_rate_high": "conjunction_rate_high",
    "subject_explicit_rate_high": "subject_explicit_high",
    "pos_bigram_monotonicity_low": "bigram_mono_low",
}

_RE_HEADING_LINE = re.compile(r"^##\s+.+$", re.MULTILINE)
_RE_URL = re.compile(r"https?://\S+")
_RE_WHITESPACE_COLLAPSE = re.compile(r"\s+")
_RE_PUNCTUATION_STRIP = re.compile(
    r"[、。．，,！!？?…・「」『』（）()［］\[\]【】<>\"'`〜ー-]"
)
_RE_CJK_LATIN_TOKEN = re.compile(
    r"[一-龯ぁ-んァ-ヶー]{2,12}|[a-z][a-z0-9_-]{2,20}"
)
RE_HEADING_LINE = _RE_HEADING_LINE
RE_WHITESPACE_COLLAPSE = _RE_WHITESPACE_COLLAPSE
_RE_SENTENCE_SPLIT = re.compile(r"(?<=[。！？])\s*")
_RE_HEADING_COUNT = re.compile(r"^##\s+", re.MULTILINE)
_RE_NON_TERMINAL_SENTENCE_END = re.compile(
    r"(?:たり|て|で|が|は|を|に|へ|と|も|や|けど|けれど|ものの|ため|ので|から|し|つつ|ながら|には|では|とは|への|での|からの)$"
)
_RE_POLITE_REGISTER_ENDING = re.compile(
    r"(?:です|ます|でした|ました|ません|でしょう|ください)(?:[。！？!?])$"
)
_RE_PLAIN_REGISTER_ENDING = re.compile(
    r"(?:である|であった|だった|だ|している|していた|してきた|できる|できない|"
    r"となっている|となっていた|なっている|なっていた|となる|となった|なる|なった|"
    r"ある|ない|といえる|とされる|示唆される|果たしている)"
    r"(?:[。！？!?])$"
)

REGISTER_NORMALIZE_REWRITES = (
    (r"であった([。！？!?])", r"でした\1"),
    (r"である([。！？!?])", r"です\1"),
    (r"だった([。！？!?])", r"でした\1"),
    (r"してきた([。！？!?])", r"してきました\1"),
    (r"していた([。！？!?])", r"していました\1"),
    (r"している([。！？!?])", r"しています\1"),
    (r"果たしている([。！？!?])", r"果たしています\1"),
    (r"できない([。！？!?])", r"できません\1"),
    (r"できる([。！？!?])", r"できます\1"),
    (r"となった([。！？!?])", r"となりました\1"),
    (r"となる([。！？!?])", r"となります\1"),
    (r"なった([。！？!?])", r"なりました\1"),
    (r"なる([。！？!?])", r"なります\1"),
    (r"ない([。！？!?])", r"ありません\1"),
    (r"ある([。！？!?])", r"あります\1"),
)

SECTION_OPENING_HINTS = {
    "auto": ["論点提示から入る", "具体例から入る", "対比から入る", "短い問いから入る"],
    "explanation": ["定義から入る", "誤解の訂正から入る", "具体例から入る", "背景から入る"],
    "experience": ["場面描写から入る", "感情の動きから入る", "小さな失敗談から入る", "気づきから入る"],
    "analysis": ["事実提示から入る", "比較から入る", "因果整理から入る", "示唆から入る"],
}

IMAGE_STYLE_DIRECTIONS = [
    {
        "name": "paper_cut",
        "style": "paper-cut collage illustration with clean layered silhouettes",
        "palette": "muted warm palette, 3-4 colors only",
    },
    {
        "name": "editorial_flat",
        "style": "editorial flat illustration with simple geometric forms",
        "palette": "calm neutral palette with one accent color",
    },
    {
        "name": "soft_watercolor",
        "style": "soft watercolor-like illustration with gentle edges",
        "palette": "pastel palette, low saturation",
    },
    {
        "name": "minimal_photo",
        "style": "minimal photorealistic scene with one clear focal object",
        "palette": "natural tones with restrained contrast",
    },
]

IMAGE_ROLE_GUIDES = {
    "top": {
        "role_desc": "TOP cover image: represent the whole article theme and first impression.",
        "composition": [
            "wide hero composition with a single focal subject and clear surrounding whitespace",
            "subject placed on left third with clean empty area on right",
            "subject centered with generous margin around it",
        ],
        "safe_zone": ["right side", "upper right", "top center"],
    },
    "inline": {
        "role_desc": "In-article supporting image: match one concrete section in the body.",
        "composition": [
            "contextual close-up scene focused on one section concept",
            "single-scene narrative frame with minimal props",
            "two-element comparison composition with large blank area",
        ],
        "safe_zone": ["bottom area", "left side", "top area"],
    },
}

CLOSING_HEADING_PATTERN = re.compile(
    r"(まとめ|結論|おわり|最後に|総括|クロージング|要点|次の一歩|判断ポイント|実務ポイント|チェックリスト)"
)
