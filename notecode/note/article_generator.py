"""article_generator.py - Note-ready article generation."""
from __future__ import annotations

import json
import logging
import random
import re
import threading
from collections import Counter
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
from human_resonance.pipeline import HumanResonancePipeline, PipelineConfig, analyze_text
from human_resonance.phase0_persona import Persona, PERSPECTIVE_DEFAULTS
from human_resonance.style_policy import (
    AI_LIKE_OPENING_PATTERNS,
    BANNED_PHRASES,
)
from human_resonance2.quality_pipeline import QualityPipelineRunner
from human_resonance2.fingerprint_metrics import FingerprintAnalyzer

from core.app_config import (
    get_cognitive_drift_config, get_generation_mode,
    get_human_resonance_config, get_llm_config, get_quality_pipeline_config,
    get_postprocess_config,
    get_semantic_dedupe_config,
    get_section_generation_config,
    get_source_reading_config,
)
from note.article_fetcher import FetchedContent
from note.llm_client import LLMClient
from note import genre_manager
from note.policy_engine import (
    build_pipeline_policy,
    evaluate_title_quality,
    format_ambiguity_clarifications,
    policy_directives,
    resolve_category_policy,
)
from note.article_cognitive_drift_mixin import (
    ArticleCognitiveDriftMixin,
    COGNITIVE_ENERGY_PROFILES,
)
from note.article_legacy_addendum_mixin import ArticleLegacyAddendumMixin
from note.article_legacy_compatibility_mixin import ArticleLegacyCompatibilityMixin
from note.article_legacy_section_runtime_mixin import ArticleLegacySectionRuntimeMixin
from note.article_length_planning_mixin import ArticleLengthPlanningMixin
from note.article_output_mixin import ArticleOutputMixin
from note.article_perspective_audience_mixin import ArticlePerspectiveAudienceMixin
from note.article_prompt_contract_mixin import ArticlePromptContractMixin
from note.zero_base_section_helper_mixin import ZeroBaseSectionHelperMixin
from note.zero_base_postprocess_guard_mixin import ZeroBasePostprocessGuardMixin
from note.zero_base_contract_guard_mixin import ZeroBaseContractGuardMixin
from note.zero_base_contract_mixin import ZeroBaseContractMixin
from note.interview_mixin import InterviewMixin
from note.image_prompt_mixin import ImagePromptMixin
from note.natural_blog_core import (
    build_note4000_discourse_plan,
    build_note4000_length_plan,
    build_note4000_section_prompt,
    build_note4000_style_profile,
)
from note.article_style_persona_mixin import ArticleStylePersonaMixin
from note.article_similarity_feedback_mixin import ArticleSimilarityFeedbackMixin
from note.article_final_consistency_mixin import ArticleFinalConsistencyMixin
from note.article_quality_guard_mixin import ArticleQualityGuardMixin
from note.natural_blog_types import DiscourseSectionPlan, NaturalStyleProfile
from note.outline_mixin import OutlineMixin
from note.post_processor_mixin import PostProcessorMixin
from note.zero_base.semantic_dedupe import semantic_dedupe_text  # compatibility re-export for tests/legacy monkeypatches

logger = logging.getLogger(__name__)

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

# 編集者AIレビューで確認する観点（ルールではなくガイドライン）
EDITOR_REVIEW_POINTS = """
1. 一人称の不自然さ: 法人格（株式会社○○、合同会社○○等）が一人称として使われていないか。「私たち」「当社」に修正。
2. 自社への敬称: 「弊社様」「当社様」などは誤り。削除または修正。
3. 過度な自画自賛: 「最高の」「他社にはない」「業界No.1」「唯一無二」は押し売り感。控えめな表現に。
4. ステマ調: 「実は私も愛用していて…」のような嘘くさい導入。削除または自然な表現に。
5. 読者置いてけぼり: 専門用語が説明なしで使われていないか。必要なら補足を追加。
6. 文体の一貫性: 「です・ます」と「だ・である」が混在していないか。

【追加: 読みやすさの観点】
7. 一人称の統一: 記事全体で一人称（「私」「私たち」等）が統一されているか。途中で変わっている場合は修正。
8. **段落の意味的まとまり**: 段落は「1つのトピック」でまとめる。話題が変わったら改行。同じ話題なら改行しない。
9. 自然な段落構成: 4〜6文を1段落にまとめ、段落間のみ1行空ける。毎文改行はNG（機械的に見える）。
10. 表現の揺らぎ: 同じ接続詞（「そして」「また」など）が連続していないか。言い回しに自然な変化をつける。
11. 感情の表現: 「！」「？」「...」を適度に使い、読者との対話感を出す。ただし多用は避ける（全体の5〜10%程度）。
12. 人間らしい不完全性: あまりにも完璧で構造的すぎる文章は機械的。適度な砕けた表現や口語表現を残す。
"""

# プロンプトインジェクション検出パターン（出力フィルタリング用）
INJECTION_PATTERNS = [
    r"AI(?:として)?は[、。]",           # 「AIとしては」の混入
    r"(?:参考)?資料\d+[：:].+?(?=\n)",   # 資料番号表記の混入
    r"【.+?】(?=\n)",                    # メタ指示見出しの混入
    r"出力は.+?のみ[。．]?",             # 「出力は〜のみ」の混入
    r"ユーザー指示.+?(?=\n)",            # ユーザー指示ラベルの混入
    r"以下の(?:情報|内容)から",           # 「以下の〜から」の混入
]

CTA_PATTERNS = [
    "この記事が少しでも参考になれば、スキをぽちっと押してくれると嬉しいです。",
    "違う見方があれば、コメントで教えてください。議論できると助かります。",
    "次も読んでもらえると励みになります。フォローも気が向いたらぜひ。",
]

# 感情アークガイド（導入→展開→結びの感情変化）
EMOTION_ARC_GUIDE = """
【感情アーク: 読者の心を動かす3ステップ】
- 導入: 共感や驚きで「自分ごと」にする（問題提起、意外な事実、痛みへの寄り添い）
- 展開: 納得感と発見で「なるほど」を生む（具体例、ストーリー、データ）
- 結び: 希望や行動意欲で「やってみよう」を引き出す（具体策、温かいメッセージ）
""".strip()

# LinkedIn用CTA（プロフェッショナル向け）
LINKEDIN_CTA_PATTERNS = [
    "💡 この投稿が参考になったら、いいね＆保存をお願いします！",
    "🔔 フォローしていただくと、最新の投稿をお届けします。",
    "💬 ご意見やご質問があれば、コメント欄でお聞かせください。",
    "📩 もっと詳しく話したい方はDMでお気軽にどうぞ！",
]

# プラットフォーム別ベストプラクティス
PLATFORM_GUIDELINES = {
    "note": """
【note最適化ガイドライン】
1. 冒頭3行で「読者の痛み」か「意外な事実」を提示する。「今回は〜について」で始めるのは禁止。
2. 具体例または根拠を最低1つ示し、抽象論だけで終わらせない。
3. 4〜6文で1段落。見出しは「?」か「!」で終わると読みたくなる。
4. 共感要素は文脈に応じて挿入する。公式情報中心の記事では一人称体験談を無理に入れない。
5. 記事末尾のCTAは押し付けず、「参考になったらスキを」程度の軽さで。
6. 専門用語は必ず日常の例えに翻訳する。
7. 「いかがでしたか」「参考になれば幸いです」等のAI定型句は絶対に使わない。
""".strip(),
    "linkedin": """
【LinkedIn最適化ガイドライン】
1. 冒頭1行で強い主張 or 問いかけ（「〜を知っていますか？」「〜が変わります」）。
2. 400〜1600文字を目安に短めでまとめる。
3. 絵文字はセクション区切りに適度に使用（📌💡🔔✅等）。過度は禁物。
4. 業界知識や実績を示すデータを含め、専門性をアピール。
5. 末尾で「皆さんはどう思いますか？」等の問いかけで対話を促す。
6. 外部リンクは本文でなくコメント欄に記載する旨を示唆。
7. 個人的エピソードは任意。根拠重視の記事では事実整理を優先する。
""".strip(),
}

# リーガル・リスク監修プロンプト（生成パイプライン用：修正のみ）
LEGAL_CHECK_PROMPT = """
あなたは日本の上場企業で20年の経験を持つ「法務部長」兼「コンプライアンス責任者」です。
IT、金融、医療、不動産、教育、飲食、製造など様々な業界のクライアントにサービスを提供しています。

【あなたの専門知識】
以下の法規制に精通しています。記事の内容に応じて、関連する規制を適切にチェックしてください：

■ 広告・表示規制
- 景品表示法（優良誤認表示、有利誤認表示、二重価格表示）
- 特定商取引法（誇大広告、不実告知）

■ 医療・健康系
- 薬機法（旧薬事法）、健康増進法
- 医療広告ガイドライン、あはき法、柔整法

■ 金融・不動産
- 金融商品取引法（断定的判断の提供禁止）
- 宅地建物取引業法（誇大広告の禁止）
- 貸金業法

■ 知財・情報
- 著作権法、商標法
- 個人情報保護法、プライバシー配慮
- 不正競争防止法

■ リスク管理
- 炎上リスク、レピュテーションリスク
- ジェンダー・人種・宗教への配慮
- 過度な煽り、他社誹謗中傷

【判断基準】
1. 景表法：根拠のない「No.1」「最高」は断定NG、「目指す」「挑戦する」等の目標表現はOK
1-2. 比較広告：比較対象・条件・根拠が明記されていない優位表現はNG
2. 薬機法：効果効能の断定NG、「印象を整える」「健康維持に役立つ」等の表現に修正
3. 金商法：「絶対儲かる」「必ず上がる」等の断定的判断NG
4. 宅建法：「お買い得」「掘り出し物」などの誇大表現に注意
5. 炎上リスク：特定属性への決めつけ、政治・宗教の極端な偏りNG

【修正ルール】
- 問題がなければ、原文をそのまま出力する。
- 問題がある箇所のみを修正し、それ以外の文脈やトーンは維持する。
- 人間味のある表現（感情、主観、話し言葉）は維持し、削除しない。
- 記事全体の意味が変わるような大幅な削除は避ける。
- **修正後の記事本文のみ**を出力すること。説明は不要。

""".strip()

# リーガル校正プロンプト（簡易チェック用：根拠付き）
LEGAL_CHECK_WITH_RATIONALE_PROMPT = """
あなたは日本の上場企業で20年の経験を持つ「法務部長」兼「コンプライアンス責任者」です。
IT、金融、医療、不動産、教育、飲食、製造など様々な業界のクライアントにサービスを提供しています。

【あなたの専門知識】
以下の法規制に精通しています。記事の内容に応じて、関連する規制を適切にチェックしてください：
- 景品表示法、特定商取引法
- 薬機法、健康増進法、医療広告ガイドライン
- 金融商品取引法、宅地建物取引業法
- 著作権法、商標法、不正競争防止法
- 個人情報保護法
- 炎上リスク、レピュテーションリスク
 - 比較広告の適正な条件・根拠の明示

【出力形式】
以下のJSON形式で出力してください：
```json
{
  "has_issues": true/false,
  "issues": [
    {
      "original": "問題のある原文",
      "fixed": "修正後の表現",
      "law": "関連する法律名",
      "reason": "なぜ問題なのか、どう修正したか"
    }
  ],
  "checked_text": "修正後の全文"
}
```

【判断基準】
- 景表法：根拠のない「No.1」「最高」は断定NG、「目指す」等の目標表現はOK
- 比較広告：比較対象・条件・根拠の記載がない場合はNG（不明確な優良誤認）
- 薬機法：効果効能の断定NG
- 金商法：「絶対儲かる」等の断定的判断NG
- 炎上リスク：特定属性への決めつけ、政治・宗教の偏りNG

問題がなければ has_issues: false で、checked_text に原文をそのまま入れてください。
""".strip()


# 出力フォーマット定義
OUTPUT_FORMATS = {
    "note": {
        "max_chars": None,  # 制限なし
        "use_markdown": True,
        "use_emoji": False,
    },
    "linkedin": {
        "max_chars": 1568,  # 企業投稿は短め寄り
        "use_markdown": False,  # プレーンテキスト推奨
        "use_emoji": True,
    },
}

LINKEDIN_MIN_CHARS = 387
LINKEDIN_MAX_CHARS = 1568
EDITOR_CONSISTENCY_MAX_RETRIES = 2
EDITOR_CONSISTENCY_CONTEXT_LIMIT = 4500
READABILITY_POLISH_CONTEXT_LIMIT = 2800
READABILITY_POLISH_MAX_REWRITE_RATIO = 0.16
VERIFICATION_MAX_REWRITE_RATIO = 0.50
MAX_INLINE_SOURCE_LINKS = 4
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
NON_CASUAL_COLLOQUIAL_ENDING_MAX = 2
REDUNDANT_SUMMARY_MARKERS: Tuple[str, ...] = (
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
ABSTRACT_COMPRESSION_REWRITES: Tuple[Tuple[str, str], ...] = (
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

SOURCE_MATCH_STOPWORDS = {
    "こと",
    "ため",
    "これ",
    "それ",
    "もの",
    "よう",
    "です",
    "ます",
    "する",
    "した",
    "して",
    "いる",
    "なる",
    "ある",
    "ない",
    "note",
    "article",
}

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

# ── Compiled regex patterns (R4-T01) ──
_RE_HEADING_LINE = re.compile(r"^##\s+.+$", re.MULTILINE)
_RE_URL = re.compile(r"https?://\S+")
_RE_WHITESPACE_COLLAPSE = re.compile(r"\s+")
_RE_PUNCTUATION_STRIP = re.compile(
    r"[、。．，,！!？?…・「」『』（）()［］\[\]【】<>\"'`〜ー-]"
)
_RE_CJK_LATIN_TOKEN = re.compile(
    r"[一-龯ぁ-んァ-ヶー]{2,12}|[a-z][a-z0-9_-]{2,20}"
)
_RE_SENTENCE_SPLIT = re.compile(r"(?<=[。！？])\s*")
_RE_HEADING_COUNT = re.compile(r"^##\s+", re.MULTILINE)
_RE_SECTION_BLOCK = re.compile(
    r"^##\s*(.+?)\n+([\s\S]*?)(?=^##\s+|\Z)", re.MULTILINE
)
_RE_BRACKET_ANGLE = re.compile(r"[\[\]<>]+")
_RE_MULTI_SPACE = re.compile(r"\s{2,}")
_RE_STRUCTURE_LINE = re.compile(r"^(?:#{1,6}\s+|---+$|\s*(?:-|\*|\d+\.)\s+)")
_RE_HEADING_NEWLINE_FIX = re.compile(
    r"(^(?:#{1,6}\s+.+))\n(?!\n|#{1,6}\s+|---+$)", re.MULTILINE
)
_RE_TRIPLE_NEWLINE = re.compile(r"\n{3,}")
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
REGISTER_NORMALIZE_REWRITES: Tuple[Tuple[str, str], ...] = (
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
    (r"だ([。！？!?])", r"です\1"),
)

LEGAL_CONTEXT_TEMPERATURE = 0.1
LEGAL_REWRITE_TEMPERATURE = 0.2

# Human-first tuning (prioritize empathy/curiosity/humanity/rhythm; legal next)
HUMAN_FIRST_CONFIG = {
    "empathy_target": 0.5,
    "curiosity_target": 0.45,
    "humanity_target": 0.4,
    "rhythm_target": 0.5,
    "humanity_intensity": 0.45,
}

TITLE_QUALITY_RETRY_LIMIT = 2

# 心理学ベースの構造ガイド（アウトライン用）
BASE_STRUCTURE_GUIDE = """
- 共感フック: 読者の課題や痛みを言語化し、自己投影を促す
- 情報ギャップ: 「何が変わるのか」を予告して続きを読みたくさせる
- 価値提示: タイトルの約束に沿って、価値/理由/ポイントを順番に提示
- 具体化: 抽象論で終わらず、具体例やケースを必ず1つ入れる
- 行動促進: 試せる具体策を示して実行意図を作る
""".strip()

# 構造タイプ別ガイド（UI表示は専門用語を避ける）
PSYCHOLOGY_STRUCTURE_GUIDES = {
    "auto": "",
    "pain_to_solution": (
        "- 冒頭で読者の悩みや痛みを具体化\n"
        "- 共感を示して「自分ごと化」\n"
        "- 解決の方向性を示し、具体策へ\n"
        "- すぐ試せる具体策で行動につなげる"
    ),
    "value_then_action": (
        "- 冒頭で気づき・意外性を提示\n"
        "- 価値を3点などに分解して順番に提示\n"
        "- 読者の行動に落とし込む"
    ),
    "surprise_to_insight": (
        "- 先入観を崩す一言から入る\n"
        "- なぜそう言えるかを丁寧に説明\n"
        "- 最後に納得感と具体策"
    ),
    "decision_support": (
        "- まず前提条件と判断軸を整理\n"
        "- 次に理由/根拠を比較して優先順位を示す\n"
        "- リスクや注意点を添える\n"
        "- 最後に実行順序を短く示す"
    ),
}

WRITING_FOCUS_GUIDES = {
    "auto": "",
    "explanation": (
        "- 定義→背景→具体例→実践の順で、わかりやすく解説する\n"
        "- 専門用語は必ず言い換え、噛み砕いた例を添える\n"
        "- 読者の疑問に先回りして補足する"
    ),
    "experience": (
        "- 体験・観察・失敗談を中心に語る\n"
        "- 感情の揺れと気づきの瞬間を具体的に書く\n"
        "- 抽象論だけで終わらず、体験から得た実践知に落とし込む"
    ),
    "analysis": (
        "- 事実→解釈→示唆の順で論点を整理する\n"
        "- 数字・固有名詞は参考情報の範囲で扱い、断定しすぎない\n"
        "- 比較や反証の観点を入れ、判断材料を示す"
    ),
}

OPENING_STYLE_OPTIONS = {
    "auto": ["fact_first", "problem_first", "benefit_first", "scene_first", "question_first"],
    "explanation": ["benefit_first", "question_first", "myth_bust_first"],
    "experience": ["scene_first", "emotion_first", "micro_story_first"],
    "analysis": ["fact_first", "contrast_first", "problem_first"],
}

OPENING_STYLE_GUIDES = {
    "fact_first": "冒頭1文は具体的な事実や観測から始める。疑問文で始めない。",
    "problem_first": "冒頭1文で課題を端的に定義し、2文目で原因や背景へ接続する。",
    "benefit_first": "冒頭1文で読者の得られる価値を明示し、過剰な煽りを避ける。",
    "scene_first": "冒頭は短い場面描写（2文以内）で始め、すぐに論点へ接続する。",
    "question_first": "冒頭を問いかけで始めてもよいが、連続使用や定型表現を避ける。",
    "emotion_first": "冒頭は感情の動きから始める。独白調の定型句を避ける。",
    "micro_story_first": "冒頭2〜3文で小さな体験談を置き、その体験から論点へ接続する。",
    "contrast_first": "冒頭1文で一般的認識と実態のギャップを示し、次文で根拠を置く。",
    "myth_bust_first": "冒頭で誤解を短く提示し、直後に訂正する。",
}

FOCUS_SECTION_RULES = {
    "auto": "",
    "explanation": (
        "- 定義や概念は1段落目で短く明確にし、次段落で具体例に落とす\n"
        "- 同じ問いかけ導入を繰り返さない"
    ),
    "experience": (
        "- 体験を軸に書くが、毎回同じ書き出し（問いかけ/独白）を繰り返さない\n"
        "- 1セクションにつき体験要素は1つに絞り、冗長化を避ける"
    ),
    "analysis": (
        "- 事実→解釈→示唆の順序を明確に保つ\n"
        "- 冒頭で疑問文を多用しない。根拠のある叙述から入る\n"
        "- 「〜だと思っていたんですが」のような口語定型を避ける"
    ),
}

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

INTRO_HEADING_PATTERN = re.compile(r"(はじめに|導入|イントロ|背景|前提|問題提起|概要|全体像|とは何か|基本)")
SUPPLEMENT_HEADING_PATTERN = re.compile(r"(補足|注釈|注意点|FAQ|Q&A|よくある質問|豆知識|Tips)")
CLOSING_HEADING_PATTERN = re.compile(
    r"(まとめ|結論|おわり|最後に|総括|クロージング|要点|次の一歩|判断ポイント|実務ポイント|チェックリスト)"
)
def randomize_length(base: int) -> int:
    return int(base * random.uniform(0.8, 1.2))


class ArticleGenerator(
    ArticlePromptContractMixin,
    ArticlePerspectiveAudienceMixin,
    ArticleLengthPlanningMixin,
    ArticleCognitiveDriftMixin,
    ArticleStylePersonaMixin,
    ArticleSimilarityFeedbackMixin,
    ArticleLegacySectionRuntimeMixin,
    ArticleLegacyAddendumMixin,
    ArticleFinalConsistencyMixin,
    ArticleQualityGuardMixin,
    ArticleLegacyCompatibilityMixin,
    InterviewMixin,
    ImagePromptMixin,
    ArticleOutputMixin,
    OutlineMixin,
    PostProcessorMixin,
    ZeroBaseSectionHelperMixin,
    ZeroBasePostprocessGuardMixin,
    ZeroBaseContractGuardMixin,
    ZeroBaseContractMixin,
):
    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client or LLMClient()
        self._current_pronoun = "私"  # デフォルトの一人称
        self._interview_answers: Dict[str, str] = {}  # インタビュー回答を保持
        self._last_interview_mode = "not_run"
        self._last_interview_reason = ""
        self._current_perspective = "blogger"
        self._secondary_perspective: Optional[str] = None
        self._writing_focus = "auto"
        self._effective_writing_focus = "explanation"
        self._tone_profile_preference = "auto"
        self._effective_tone_profile = "auto"
        self._lead_opening_style = "benefit_first"
        self._allow_experience = False  # R14-T15: 経験談許可設定（デフォルトOFF）
        self._editor_consistency_failed = False
        self._length_mode = "normal"
        self._source_count = 0
        self._term_clarifications: Dict[str, str] = {}
        self._category_policy: Dict[str, Any] = {}
        self._pipeline_policy: Dict[str, Any] = {}
        self._structure_features: Dict[str, Any] = {}
        self._interview_constraints: Dict[str, str] = {}
        self._opening_variation_nonce = 0
        self._section_opening_sequence: List[str] = []
        self._quality_phase_reports: List[Dict[str, Any]] = []
        self._section_feedback_reports: List[Dict[str, Any]] = []
        self._fingerprint_analyzer = FingerprintAnalyzer()
        self._cognitive_drift_config: Dict[str, Any] = get_cognitive_drift_config()
        self._section_generation_config: Dict[str, Any] = get_section_generation_config()
        self._postprocess_config: Dict[str, Any] = get_postprocess_config()
        self._semantic_dedupe_config: Dict[str, Any] = get_semantic_dedupe_config()
        self._source_reading_config: Dict[str, Any] = get_source_reading_config()
        self._latest_user_prompt = ""
        self._prompt_echo_references: List[str] = []
        self._input_contract_seed: Dict[str, Any] = {}
        self._runtime_input_contract: Dict[str, Any] = {}
        self._enhanced_context = ""
        self._last_retry_telemetry: List[Dict[str, Any]] = []
        self._last_hard_soft_eval: Dict[str, Any] = {}
        self._last_final_quality_eval: Dict[str, Any] = {}
        self._last_repair_only_report: Dict[str, Any] = {}
        self._last_contextual_naturalness_report: Dict[str, Any] = {}
        self._editor_persona_snapshots: Dict[str, Dict[str, Any]] = {}
        self._last_generation_dispatch: Dict[str, Any] = {}
        self._zero_base_embedding_provider = None
        self._zero_base_dedupe_audit: Dict[str, Any] = {}
        self._zero_base_length_plan: Dict[str, Any] = {}
        self._last_contract_alignment: Dict[str, Any] = {}
        self._zero_base_rhythm_report: Dict[str, Any] = {}
        self._progress_lock = threading.Lock()
        self._generation_progress: Dict[str, Any] = {
            "stage": "prepare",
            "message": "",
            "current": 0,
            "total": 1,
            "partial_body": "",
        }
        self._section_block_cache: Dict[int, List[Tuple[str, str]]] = {}
        self._section_block_cache_hits = 0
        self._section_block_cache_misses = 0
        self._last_resonance_phase_effect_metrics: Dict[str, Any] = {}

    def set_input_contract(self, contract: Dict[str, Any]) -> None:
        """Legacy/compatibility path for ArticleGenerator.generate()."""
        if not isinstance(contract, dict):
            self._input_contract_seed = {}
            self._runtime_input_contract = {}
            return
        self._input_contract_seed = dict(contract)
        self._runtime_input_contract = dict(contract)

    def reset_generation_progress(self) -> None:
        self._set_generation_progress(
            stage="idle",
            message="",
            current=0,
            total=0,
            partial_body="",
        )

    def _set_generation_progress(
        self,
        *,
        stage: str,
        message: str,
        current: int = 0,
        total: int = 0,
        partial_body: str = "",
    ) -> None:
        current = max(0, int(current or 0))
        total = max(0, int(total or 0))
        percent = int((current / total) * 100) if total > 0 else 0
        with self._progress_lock:
            self._generation_progress = {
                "stage": stage,
                "message": message,
                "current": current,
                "total": total,
                "percent": max(0, min(100, percent)),
                "partial_body": partial_body or "",
            }

    def get_generation_progress(self) -> Dict[str, Any]:
        with self._progress_lock:
            return dict(self._generation_progress)

    def _trim_body_to_limit(self, text: str, limit: int) -> str:
        if limit <= 0 or len(text) <= limit:
            return text
        trimmed = text[:limit]
        # まず段落境界で切る（文中切断を避ける）
        para_break = trimmed.rfind("\n\n")
        min_length = int(limit * 0.6)
        if para_break >= min_length:
            return trimmed[:para_break].rstrip()
        last_break = max(
            trimmed.rfind("。"),
            trimmed.rfind("！"),
            trimmed.rfind("？"),
            trimmed.rfind("\n"),
        )
        if last_break >= min_length:
            return trimmed[: last_break + 1].rstrip()
        return trimmed.rstrip() + "..."

    def _get_section_generation_config(self) -> Dict[str, Any]:
        cfg = get_section_generation_config()
        if isinstance(cfg, dict) and cfg:
            self._section_generation_config = cfg
        return dict(getattr(self, "_section_generation_config", {}) or {})

    def _get_postprocess_config(self) -> Dict[str, Any]:
        cfg = get_postprocess_config()
        if isinstance(cfg, dict) and cfg:
            self._postprocess_config = cfg
        return dict(getattr(self, "_postprocess_config", {}) or {})

    def _get_source_reading_config(self) -> Dict[str, Any]:
        cfg = get_source_reading_config()
        if isinstance(cfg, dict) and cfg:
            self._source_reading_config = cfg
        return dict(getattr(self, "_source_reading_config", {}) or {})

    def _get_active_banned_phrases(self) -> List[str]:
        cfg = self._get_section_generation_config()
        lexical_cfg = cfg.get("lexical_policy", {}) if isinstance(cfg, dict) else {}
        if not isinstance(lexical_cfg, dict):
            lexical_cfg = {}
        enabled = bool(lexical_cfg.get("enabled", True))
        if not enabled:
            return list(BANNED_PHRASES)
        extra = lexical_cfg.get("extra_banned_phrases", [])
        if not isinstance(extra, list):
            extra = []
        merged = list(BANNED_PHRASES)
        for item in extra:
            if not isinstance(item, str):
                continue
            phrase = item.strip()
            if phrase and phrase not in merged:
                merged.append(phrase)
        return merged

    def _resolve_generation_dispatch(self, generation_mode: str) -> str:
        mode = (generation_mode or "zero_base_v2").strip().lower()
        if mode != "zero_base_v2":
            raise ValueError(f"INP_UNSUPPORTED_GENERATION_MODE:{mode}")
        return "zero_base_v2_path"

    def _zero_base_plan_outline(
        self,
        *,
        contract: Dict[str, Any],
        user_prompt: str,
        reader_question_candidates: List[str],
    ) -> List[Dict[str, str]]:
        must_cover = contract.get("must_cover", [])
        if not isinstance(must_cover, list):
            must_cover = []
        if not isinstance(reader_question_candidates, list):
            reader_question_candidates = []
        min_sections, max_sections = self._get_outline_section_range()
        source_count = max(0, int(getattr(self, "_source_count", 0) or 0))
        prompt_len = len((user_prompt or "").strip())
        signal_score = 0
        signal_score += min(2, max(0, len(must_cover) - 1))
        signal_score += min(2, source_count // 2)
        if prompt_len >= 120:
            signal_score += 1
        if prompt_len >= 260:
            signal_score += 1
        span = max(0, max_sections - min_sections)
        scaled = int(round((signal_score / 6.0) * span)) if span > 0 else 0
        section_count = min_sections + scaled
        if (
            self._length_mode == "long"
            and section_count < max_sections
            and (source_count >= 2 or len(must_cover) >= 2)
        ):
            section_count += 1
        section_count = max(min_sections, min(max_sections, section_count))

        article_type = self._safe_contract_value(contract.get("article_type")).lower()
        base_template = self._safe_contract_value(contract.get("category_base_template")).lower()
        is_branding_story = article_type in {"branding", "corporate_culture", "daily_happenings"} or base_template == "branding"
        is_product_branding = article_type == "branding"

        if section_count <= 1:
            headings = ["要点整理"]
        elif is_product_branding and section_count == 2:
            headings = ["読者課題と商品の価値", "選び方の判断軸と次の一歩"]
        elif is_product_branding and section_count == 3:
            headings = [
                "読者課題と商品の価値",
                "商品ラインアップと活用シーン",
                "選び方の判断軸と次の一歩",
            ]
        elif is_product_branding:
            middle_pool = [
                "商品ラインアップと選定ポイント",
                "活用シーンと導入メリット",
                "品質・供給・サポート体制",
                "導入時の比較観点と注意点",
                "導入後の運用と改善ポイント",
            ]
            needed_middle = max(0, section_count - 2)
            middle = list(middle_pool[:needed_middle])
            while len(middle) < needed_middle:
                middle.append(f"商品活用の実践ポイント {len(middle) + 1}")
            headings = ["読者課題と商品の価値", *middle, "選び方の判断軸と次の一歩"]
        elif is_branding_story and section_count == 2:
            headings = ["私たちが大切にしている価値", "これからの取り組み"]
        elif is_branding_story and section_count == 3:
            headings = ["私たちが大切にしている価値", "現場での工夫とチーム連携", "これからの取り組み"]
        elif is_branding_story:
            middle_pool = [
                "現場での工夫とチーム連携",
                "仕事の進め方と判断基準",
                "提供価値を支える仕組み",
                "導入後のサポートと改善",
                "これからの挑戦",
            ]
            needed_middle = max(0, section_count - 2)
            middle = list(middle_pool[:needed_middle])
            while len(middle) < needed_middle:
                middle.append(f"現場の実践 {len(middle) + 1}")
            headings = ["私たちが大切にしている価値", *middle, "これからの取り組み"]
        elif section_count == 2:
            headings = ["背景と論点整理", "まとめと次の一歩"]
        elif section_count == 3:
            headings = ["背景と論点整理", "実務で使う視点", "まとめと次の一歩"]
        else:
            middle_pool = [
                "現場で起きる課題",
                "実務で使う視点",
                "進め方のステップ",
                "運用時の注意点",
                "効果測定と改善",
                "実行時の判断基準",
            ]
            needed_middle = max(0, section_count - 2)
            middle = list(middle_pool[:needed_middle])
            while len(middle) < needed_middle:
                middle.append(f"実務補足 {len(middle) + 1}")
            headings = ["背景と論点整理", *middle, "まとめと次の一歩"]

        info_pool: List[str] = []
        user_instruction = self._sanitize_outline_seed(
            contract.get("user_instruction"),
            max_length=120,
        )
        if user_instruction and not self._is_low_signal_must_cover_item(user_instruction):
            info_pool.append(user_instruction)
        user_instruction_terms = contract.get("user_instruction_terms", [])
        if isinstance(user_instruction_terms, list):
            for term in user_instruction_terms[:3]:
                normalized_term = self._sanitize_outline_seed(term, max_length=60)
                if not normalized_term:
                    continue
                seed = self._sanitize_outline_seed(
                    f"{normalized_term}に関する具体策を示す",
                    max_length=120,
                )
                if seed and seed not in info_pool:
                    info_pool.append(seed)
        for item in must_cover:
            normalized = self._sanitize_outline_seed(
                self._normalize_must_cover_item(item, max_length=120),
                max_length=120,
            )
            if self._is_low_signal_must_cover_item(normalized):
                continue
            if normalized and normalized not in info_pool:
                info_pool.append(normalized)
        thesis = self._sanitize_outline_seed(contract.get("thesis"), max_length=120)
        if thesis and thesis not in info_pool:
            info_pool.append(thesis)
        if not info_pool:
            info_pool.append("主要論点を読者が実行できる形に分解する")

        outline: List[Dict[str, str]] = []
        for idx, heading in enumerate(headings):
            if idx < len(info_pool):
                new_information = info_pool[idx]
            else:
                new_information = f"{heading}で押さえる実務上の要点"
            new_information = self._sanitize_contract_text(new_information, max_length=120)
            if not new_information:
                new_information = "このセクションで押さえるべき要点を整理する"

            reader_question = ""
            if idx < len(reader_question_candidates):
                reader_question = self._sanitize_contract_text(
                    reader_question_candidates[idx],
                    max_length=120,
                )
            if not reader_question:
                reader_question = f"{heading}で読者が判断すべき点は何か？"

            outline.append(
                {
                    "heading": heading,
                    "new_information": new_information,
                    "reader_question": reader_question,
                }
            )
        return outline

    def _build_note4000_style_profile(self, contract: Dict[str, Any]) -> NaturalStyleProfile:
        policy = getattr(self, "_pipeline_policy", {}) or {}
        register_policy = self._normalize_register_policy(contract.get("register_policy"))
        return build_note4000_style_profile(
            article_type=self._safe_contract_value(contract.get("article_type")),
            focus=self._safe_contract_value(contract.get("focus")) or self._get_effective_writing_focus(),
            tone_profile=str(policy.get("tone_profile", "") or getattr(self, "_effective_tone_profile", "")),
            style_profile=str(policy.get("style_profile", "") or self._get_active_style_profile()),
            base_register=str(register_policy.get("base_register", "polite") or "polite"),
        )

    def _build_note4000_discourse_plan(
        self,
        *,
        contract: Dict[str, Any],
        user_prompt: str,
        reader_question_candidates: List[str],
        length_plan: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        must_cover = contract.get("must_cover", [])
        if not isinstance(must_cover, list):
            must_cover = []
        user_instruction_terms = contract.get("user_instruction_terms", [])
        if not isinstance(user_instruction_terms, list):
            user_instruction_terms = []
        discourse = build_note4000_discourse_plan(
            article_type=self._safe_contract_value(contract.get("article_type")).lower(),
            base_template=self._safe_contract_value(contract.get("category_base_template")).lower(),
            user_prompt=user_prompt,
            must_cover=[self._safe_contract_value(item) for item in must_cover if self._safe_contract_value(item)],
            user_instruction_terms=[
                self._safe_contract_value(item)
                for item in user_instruction_terms
                if self._safe_contract_value(item)
            ],
            thesis=self._safe_contract_value(contract.get("thesis")),
            reader_question_candidates=reader_question_candidates,
            length_plan=length_plan,
        )
        return [item.to_dict() if isinstance(item, DiscourseSectionPlan) else dict(item) for item in discourse]

    def _zero_base_build_length_plan(
        self,
        *,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
        section_count: int,
    ) -> Dict[str, Any]:
        _ = (contexts, user_prompt, article_type)
        return build_note4000_length_plan(
            length_mode=self._length_mode,
            section_count=section_count,
        )

    def _zero_base_get_section_plan(
        self,
        *,
        length_plan: Dict[str, Any],
        section_index: int,
    ) -> Dict[str, int]:
        section_plans = length_plan.get("section_plans", [])
        if isinstance(section_plans, list) and 0 <= section_index < len(section_plans):
            plan = section_plans[section_index]
            if isinstance(plan, dict):
                return {
                    "target_chars": int(plan.get("target_chars", 220) or 220),
                    "min_chars": int(plan.get("min_chars", 140) or 140),
                    "max_chars": int(plan.get("max_chars", 320) or 320),
                    "max_tokens": int(plan.get("max_tokens", 520) or 520),
                    "sentence_min": int(plan.get("sentence_min", 2) or 2),
                    "sentence_max": int(plan.get("sentence_max", 4) or 4),
                }
        sentence_range = length_plan.get("sentence_range", {})
        if not isinstance(sentence_range, dict):
            sentence_range = {}
        return {
            "target_chars": 220,
            "min_chars": 140,
            "max_chars": 320,
            "max_tokens": 520,
            "sentence_min": int(sentence_range.get("min", 2) or 2),
            "sentence_max": int(sentence_range.get("max", 4) or 4),
        }

    def _zero_base_expand_section_text(
        self,
        *,
        section_text: str,
        section_plan: Dict[str, int],
        new_information: str,
        reader_question: str,
        previous_summary: str,
    ) -> str:
        text = (section_text or "").strip()
        sentence_min = max(1, int(section_plan.get("sentence_min", 2) or 2))
        min_chars = max(80, int(section_plan.get("min_chars", 140) or 140))
        max_chars = max(min_chars + 40, int(section_plan.get("max_chars", 320) or 320))

        sentence_candidates = [s.strip() for s in re.split(r"(?<=[。！？!?])\s*", text) if s.strip()]
        safe_sentences: List[str] = []
        for sentence in sentence_candidates:
            if self._looks_instructional_fragment(sentence):
                continue
            cleaned_sentence = re.sub(r"[「『](?:[^」』]{0,120})$", "", sentence).strip()
            if not cleaned_sentence:
                continue
            if cleaned_sentence[-1] not in "。！？!?":
                cleaned_sentence = f"{cleaned_sentence}。"
            safe_sentences.append(cleaned_sentence)
        text = " ".join(safe_sentences).strip()
        sentences = [s.strip() for s in re.split(r"(?<=[。！？!?])\s*", text) if s.strip()]
        if not sentences and text:
            sentences = [text if text.endswith(("。", "！", "？")) else f"{text}。"]
        if not text:
            seed = self._sanitize_outline_seed(new_information, max_length=84)
            if seed:
                text = f"{seed}を補足します。"
                sentences = [text]
            else:
                return ""

        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > max_chars:
            text = self._trim_body_to_limit(text, max_chars).strip()
        return text

    def _stabilize_note4000_section_text(
        self,
        *,
        section_text: str,
        section_plan: Dict[str, int],
        topic_seed: str,
        reader_question: str,
        bridge_hint: str,
        announcement_like: bool = False,
    ) -> str:
        text = (section_text or "").strip()
        if not text:
            return text
        min_chars = max(180, int(section_plan.get("min_chars", 220) or 220))
        if len(text) >= min_chars:
            return text
        if announcement_like:
            max_chars = max(min_chars + 80, int(section_plan.get("max_chars", min_chars + 120) or (min_chars + 120)))
            if len(text) > max_chars:
                text = self._trim_body_to_limit(text, max_chars).strip()
            return text
        additions: List[str] = []
        if topic_seed:
            additions.append(f"{topic_seed}は、場面を一つ具体化すると読み手が意味を取り違えにくくなります。")
        if reader_question:
            prompt = re.sub(r"[？?。]+$", "", reader_question.strip())
            if prompt:
                additions.append(f"焦点は「{prompt}」です。答えを一つずつ分けると、論点が重なりにくくなります。")
        if bridge_hint:
            additions.append(f"この論点を押さえると、次は{bridge_hint}へ無理なくつながります。")
        if len(additions) > 1:
            selector = sum(ord(ch) for ch in f"{topic_seed}|{reader_question}|{bridge_hint}")
            additions = [additions[selector % len(additions)]]
        for sentence in additions:
            if not sentence or sentence in text:
                continue
            text = f"{text.rstrip()} {sentence}".strip()
            if len(text) >= min_chars:
                break
        max_chars = max(min_chars + 80, int(section_plan.get("max_chars", min_chars + 120) or (min_chars + 120)))
        if len(text) > max_chars:
            text = self._trim_body_to_limit(text, max_chars).strip()
        return text

    def _zero_base_adjust_cta_length(
        self,
        *,
        cta: str,
        target_chars: int,
        target_audience: str,
        announcement_like: bool = False,
    ) -> str:
        text = (cta or "").strip()
        if not text:
            return text

        target = max(60, int(target_chars or 0))
        max_chars = max(target + 35, int(target * 1.35))
        min_chars = max(48, int(target * 0.62))
        if len(text) > max_chars:
            text = self._trim_body_to_limit(text, max_chars).strip()

        if announcement_like:
            return text

        if len(text) >= min_chars:
            return text

        audience = self._normalize_cta_audience(target_audience)
        audience_clause = self._build_cta_audience_clause(audience)
        topic = self._extract_cta_topic(getattr(self, "_current_title", ""), self._latest_user_prompt)
        additions = [
            f"{audience_clause}まずは「{topic}」で一つだけ試す行動を決め、短い振り返りを残してみてください。",
            "小さな検証結果を積み上げると、次の改善ポイントが見えやすくなります。",
        ]
        for sentence in additions:
            sentence = sentence.strip()
            if not sentence:
                continue
            if sentence in text:
                continue
            text = f"{text.rstrip()} {sentence}".strip()
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) >= min_chars:
                break
        if len(text) > max_chars:
            text = self._trim_body_to_limit(text, max_chars).strip()
        return text

    def _zero_base_generate_section(
        self,
        *,
        outline_item: Dict[str, str],
        contract: Dict[str, Any],
        previous_summary: str,
        section_summaries: List[str],
        section_plan: Dict[str, int],
    ) -> str:
        heading = self._safe_contract_value(outline_item.get("heading")) or "補足"
        new_information = self._safe_contract_value(outline_item.get("new_information"))
        reader_question = self._safe_contract_value(outline_item.get("reader_question"))
        topic_seed = self._safe_contract_value(outline_item.get("topic_seed")) or new_information or heading
        bridge_hint = self._safe_contract_value(outline_item.get("bridge_hint"))
        section_intent = self._safe_contract_value(outline_item.get("intent")) or "practice"
        related_terms = outline_item.get("related_terms", [])
        if not isinstance(related_terms, list):
            related_terms = []
        section_must_cover = outline_item.get("must_cover", [])
        if not isinstance(section_must_cover, list):
            section_must_cover = []
        audience = self._safe_contract_value(contract.get("audience"))
        forbidden_topics = contract.get("forbidden_topics", [])
        if not isinstance(forbidden_topics, list):
            forbidden_topics = []
        section_max_tokens = max(300, int(section_plan.get("max_tokens", 520) or 520))
        speaker_profile = self._safe_contract_value(contract.get("speaker_profile"))
        relationship_mode = self._safe_contract_value(contract.get("relationship_mode")) or "guide"
        allowed_pronouns = self._zero_base_allowed_pronouns(contract)
        natural_style_payload = contract.get("natural_style_profile", {})
        if isinstance(natural_style_payload, NaturalStyleProfile):
            natural_style_profile = natural_style_payload
        else:
            natural_style_profile = self._build_note4000_style_profile(contract)
        retry_feedback = ""
        section_text = ""
        section_report: Dict[str, Any] = {"heading": heading}
        blocked_topics_lower = [
            self._safe_contract_value(topic).lower()
            for topic in forbidden_topics
            if self._safe_contract_value(topic)
        ]
        for attempt in range(1, 3):
            section_state = DiscourseSectionPlan(
                heading=heading,
                intent=section_intent,
                target_chars=int(section_plan.get("target_chars", 520) or 520),
                topic_seed=topic_seed,
                related_terms=[self._safe_contract_value(term) for term in related_terms if self._safe_contract_value(term)],
                reader_question=reader_question,
                bridge_hint=bridge_hint,
                must_cover=[self._safe_contract_value(item) for item in section_must_cover if self._safe_contract_value(item)],
                new_information=new_information or topic_seed,
            )
            prompt = build_note4000_section_prompt(
                section=section_state,
                speaker_profile=speaker_profile or "書き手",
                audience_profile=audience or self._safe_contract_value(contract.get("audience_profile")) or "読者",
                relationship_mode=relationship_mode,
                style_profile=natural_style_profile,
                previous_summary=previous_summary,
                recent_summaries=section_summaries,
                forbidden_topics=forbidden_topics,
                allowed_pronouns=allowed_pronouns,
                user_instruction=self._safe_contract_value(contract.get("user_instruction")),
                instruction_anchor_terms=contract.get("user_instruction_terms", []),
            )
            if retry_feedback:
                prompt = f"{prompt}\n\n【前回の修正メモ】\n{retry_feedback}"
            try:
                raw = self.llm.generate_text(
                    prompt,
                    max_tokens=section_max_tokens,
                    task_type="zero_base_section",
                ).strip()
            except Exception as exc:
                logger.warning("Zero-base section generation failed. Stop current attempt.")
                logger.debug("Zero-base section generation detail.", exc_info=exc)
                raise RuntimeError("TRN_SECTION_GENERATION_FAILED") from exc

            section_text = (raw or "").strip()
            section_text = re.sub(r"^#+\s*.*$", "", section_text, flags=re.MULTILINE).strip()
            section_text = self._clean_meta_output(section_text, audience)
            section_text = self._zero_base_expand_section_text(
                section_text=section_text,
                section_plan=section_plan,
                new_information=topic_seed,
                reader_question=reader_question,
                previous_summary=previous_summary,
            )
            section_text = self._stabilize_note4000_section_text(
                section_text=section_text,
                section_plan=section_plan,
                topic_seed=topic_seed,
                reader_question=reader_question,
                bridge_hint=bridge_hint,
                announcement_like=self._safe_contract_value(contract.get("article_type")).lower() == "announcement",
            )
            section_text = self._zero_base_apply_sanitize_pass(section_text)
            section_report = self._analyze_zero_base_speaker_contract(
                text=section_text,
                contract=contract,
            )
            forbidden_topic_hits = self._collect_forbidden_topic_hits(
                section_text,
                blocked_topics_lower,
            )
            section_report.update(
                {
                    "heading": heading,
                    "attempt": attempt,
                    "forbidden_topic_hits": forbidden_topic_hits[:6],
                }
            )
            blocking_issue_count = int(section_report.get("hard_issue_count", 0) or 0)
            if forbidden_topic_hits:
                blocking_issue_count += 1
            section_report["blocking_issue_count"] = blocking_issue_count
            if blocking_issue_count <= 0:
                break
            retry_feedback = self._zero_base_build_contract_retry_guidance(section_report)
        section_guard_reports = getattr(self, "_zero_base_section_guard_reports", None)
        if isinstance(section_guard_reports, list):
            section_guard_reports.append(dict(section_report))
        if not section_text.strip():
            logger.info("Zero-base section skipped due empty content after cleanup: heading=%s", heading)
            return ""
        return f"## {heading}\n\n{section_text}"

    def _generate_zero_base_scaffold(
        self,
        *,
        contexts: List[FetchedContent],
        merged_context: str,
        user_prompt: str,
        article_type: str,
        perspective: str,
        output_format: str,
        psychology_structure: str,
        writing_focus: str,
        length_mode: str,
        custom_prompt: str,
        custom_meta: Optional[Dict[str, Any]],
    ) -> Dict[str, str]:
        self._set_generation_progress(
            stage="zero_base_contract",
            message="zero_base: 契約を解決しています...",
            current=0,
            total=7,
            partial_body="",
        )
        self._current_type = article_type
        runtime_input_contract = dict(getattr(self, "_runtime_input_contract", {}) or {})
        if not runtime_input_contract.get("article_type"):
            runtime_input_contract["article_type"] = article_type
        if not runtime_input_contract.get("writing_focus"):
            runtime_input_contract["writing_focus"] = writing_focus
        if not runtime_input_contract.get("length_mode"):
            runtime_input_contract["length_mode"] = length_mode
        if not runtime_input_contract.get("structure"):
            runtime_input_contract["structure"] = psychology_structure or "auto"
        if not isinstance(runtime_input_contract.get("source_inputs"), list):
            runtime_input_contract["source_inputs"] = []
        if not runtime_input_contract["source_inputs"]:
            runtime_input_contract["source_inputs"] = list(getattr(self, "_source_urls", []) or [])

        self._writing_focus = self._normalize_writing_focus(
            self._safe_contract_value(runtime_input_contract.get("writing_focus")) or writing_focus
        )
        if self._writing_focus == "auto":
            self._effective_writing_focus = self._infer_writing_focus(user_prompt, merged_context)
        else:
            self._effective_writing_focus = self._writing_focus
        self._source_count = len(contexts)
        requested_length_mode = self._normalize_length_mode(
            self._safe_contract_value(runtime_input_contract.get("length_mode")) or length_mode
        )
        self._length_mode = (
            self._resolve_adaptive_length_mode(
                contexts=contexts,
                user_prompt=user_prompt,
                article_type=article_type,
            )
            if requested_length_mode == "adaptive"
            else requested_length_mode
        )
        runtime_input_contract["length_mode_requested"] = requested_length_mode
        runtime_input_contract["length_mode"] = self._length_mode
        self._runtime_input_contract = dict(runtime_input_contract)
        self._psychology_structure = (
            self._safe_contract_value(runtime_input_contract.get("structure")) or psychology_structure or "auto"
        )

        requested_perspective = self._safe_contract_value(runtime_input_contract.get("perspective")) or perspective
        resolved_perspective = self._normalize_perspective_key(requested_perspective)
        if resolved_perspective in ("", "auto"):
            resolved_perspective = self._secondary_from_interview() or "blogger"
        self._current_perspective = resolved_perspective
        self._current_persona = self._get_persona_for_perspective(resolved_perspective, contexts, user_prompt)
        self._current_pronoun = self._extract_pronoun(self._current_persona)
        target_audience = self._safe_contract_value(runtime_input_contract.get("audience_profile"))
        if not target_audience:
            target_audience = self._safe_contract_value(self._interview_answers.get("target"))
        if not target_audience:
            target_audience = self._detect_target_audience(contexts, user_prompt)

        # Step1: contract resolve
        contract = self._zero_base_contract_base(
            article_type=article_type,
            user_prompt=user_prompt,
            target_audience=target_audience,
            writing_focus=self._effective_writing_focus,
            input_contract=runtime_input_contract,
        )
        contract["forbidden_topics"] = self._build_zero_base_forbidden_topics(
            article_type=article_type,
            user_prompt=user_prompt,
            merged_context=merged_context,
            contract=contract,
        )

        # Step2: category resolve
        self._set_generation_progress(
            stage="zero_base_category",
            message="zero_base: カテゴリ方針を解決しています...",
            current=1,
            total=7,
            partial_body="",
        )
        category_policy = resolve_category_policy(
            article_type,
            custom_prompt=custom_prompt,
            custom_meta=custom_meta,
            user_prompt=user_prompt,
            writing_focus=self._writing_focus,
        )
        self._category_policy = category_policy.to_dict()
        resolved_base_template = self._safe_contract_value(category_policy.base_template)
        if not resolved_base_template:
            try:
                fallback_policy = resolve_category_policy(self._safe_contract_value(contract.get("article_type")) or article_type)
                resolved_base_template = self._safe_contract_value(fallback_policy.base_template)
            except Exception:
                resolved_base_template = ""
        if not resolved_base_template:
            resolved_base_template = "branding"
        contract["category_base_template"] = resolved_base_template
        contract["category_policy_source"] = (
            self._safe_contract_value(category_policy.source)
            or "fallback_category_policy"
        )
        contract["evidence_mode"] = self._safe_contract_value(category_policy.evidence_mode) or "normal"
        if self._writing_focus == "auto":
            self._effective_writing_focus = self._infer_writing_focus(user_prompt, merged_context)
        if not self._allow_experience and self._effective_writing_focus == "experience":
            explanatory_like = (
                article_type in {"ai", "announcement"}
                or category_policy.base_template == "ai"
                or category_policy.evidence_mode == "strict"
            )
            if explanatory_like:
                logger.info(
                    "Zero-base focus downgraded to explanation: allow_experience=%s article_type=%s base=%s evidence=%s",
                    self._allow_experience,
                    article_type,
                    category_policy.base_template,
                    category_policy.evidence_mode,
                )
                self._effective_writing_focus = "explanation"
        contract["focus"] = self._effective_writing_focus

        pipeline_policy = build_pipeline_policy(
            article_type=article_type,
            perspective=self._current_perspective,
            psychology_structure=self._psychology_structure,
            writing_focus=self._effective_writing_focus,
            length_mode=self._length_mode,
            user_prompt=user_prompt,
            category_policy=category_policy,
        )
        self._pipeline_policy = pipeline_policy.to_dict()
        self._effective_writing_focus = pipeline_policy.focus
        self._snapshot_editor_personas(
            article_type=article_type,
            focus=self._effective_writing_focus,
            evidence_mode=self._safe_contract_value(contract.get("evidence_mode")) or "normal",
        )

        # Step3: pre_generation_question resolve
        self._set_generation_progress(
            stage="zero_base_questions",
            message="zero_base: 生成前質問を解決しています...",
            current=2,
            total=7,
            partial_body="",
        )
        question_bundle = self._zero_base_resolve_pre_generation_questions(
            contexts=contexts,
            user_prompt=user_prompt,
            article_type=article_type,
            question_source_priority=contract.get("question_source_priority"),
        )
        reader_question_candidates = list(
            question_bundle.pop("reader_question_candidates", [])
            if isinstance(question_bundle.get("reader_question_candidates"), list)
            else []
        )
        resolved_audience = self._safe_contract_value(question_bundle.pop("resolved_audience", ""))
        resolved_question_sources = (
            question_bundle.pop("resolved_question_sources", {})
            if isinstance(question_bundle.get("resolved_question_sources"), dict)
            else {}
        )
        contract.update(question_bundle)
        self._prompt_echo_references = self._build_prompt_echo_references(contract)
        if resolved_audience:
            contract["audience"] = resolved_audience
            contract["audience_profile"] = resolved_audience
            target_audience = resolved_audience
        self._interview_constraints = self._derive_interview_constraints(user_prompt)
        self._apply_interview_constraints(self._interview_constraints)
        self._apply_tone_profile_preference(
            article_type=article_type,
            category_base_template=category_policy.base_template,
        )
        evidence_mode = self._safe_contract_value(contract.get("evidence_mode")) or "normal"
        category_guide = policy_directives(category_policy)
        evidence_guide = (
            "【根拠モード: strict】根拠が曖昧な断定は避ける。"
            if evidence_mode == "strict"
            else "【根拠モード: normal】読みやすさと根拠のバランスを保つ。"
        )
        interview_guide = self._build_interview_constraint_guide(self._interview_constraints)
        self._enhanced_context = "\n".join(
            part for part in [category_guide, evidence_guide, interview_guide] if part
        )
        preserved_user_instruction = self._safe_contract_value(contract.get("user_instruction"))
        preserved_user_instruction_terms = list(
            contract.get("user_instruction_terms", [])
            if isinstance(contract.get("user_instruction_terms"), list)
            else []
        )
        preserved_forbidden_topics = list(
            contract.get("forbidden_topics", [])
            if isinstance(contract.get("forbidden_topics"), list)
            else []
        )

        try:
            from note.zero_base.phase01_baseline_contract import build_intent_contract

            contract = build_intent_contract(contract)
        except Exception as exc:
            logger.debug("Zero-base contract normalization skipped (fail-open).", exc_info=exc)
        contract["user_instruction"] = preserved_user_instruction
        contract["user_instruction_terms"] = preserved_user_instruction_terms[:10]
        contract["forbidden_topics"] = preserved_forbidden_topics[:10]

        speaker_fields = self._resolve_zero_base_speaker_profile_fields(
            article_type=article_type,
            category_base_template=resolved_base_template,
            runtime_input_contract=runtime_input_contract,
            resolved_perspective=resolved_perspective,
        )
        resolved_speaker_profile = self._safe_contract_value(speaker_fields.get("speaker_profile"))
        current_contract_speaker = self._safe_contract_value(contract.get("speaker_profile"))
        if self._is_valid_zero_base_speaker_profile(current_contract_speaker):
            resolved_speaker_profile = current_contract_speaker
        resolved_writer_role = self._safe_contract_value(speaker_fields.get("writer_role"))
        resolved_article_viewpoint = self._safe_contract_value(speaker_fields.get("article_viewpoint")) or "auto"
        resolved_topic_statement = self._sanitize_outline_seed(speaker_fields.get("topic_statement"), max_length=180)
        profile_defaults = speaker_fields.get("profile", {})
        if not isinstance(profile_defaults, dict):
            profile_defaults = {}
        resolved_audience_profile = self._safe_contract_value(contract.get("audience_profile")) or target_audience
        relationship_mode = self._safe_contract_value(contract.get("relationship_mode")) or self._safe_contract_value(
            profile_defaults.get("default_relationship_mode")
        ) or "guide"
        register_policy_seed = contract.get("register_policy")
        if not isinstance(register_policy_seed, dict):
            register_policy_seed = profile_defaults.get("default_register_policy", {})
        contract["register_policy"] = self._normalize_register_policy(register_policy_seed)
        contract["contract_profile_key"] = self._safe_contract_value(profile_defaults.get("profile_key"))
        contract["allowed_pronouns_hint"] = list(profile_defaults.get("default_allowed_pronouns", []) or [])[:6]
        contract["speaker_profile"] = resolved_speaker_profile
        contract["writer_role"] = resolved_writer_role
        contract["article_viewpoint"] = resolved_article_viewpoint
        contract["topic_statement"] = resolved_topic_statement
        contract["audience_profile"] = resolved_audience_profile
        contract["relationship_mode"] = relationship_mode
        contract["forbidden_topics"] = self._build_zero_base_forbidden_topics(
            article_type=article_type,
            user_prompt=user_prompt,
            merged_context=merged_context,
            contract=contract,
        )
        if not contract["speaker_profile"]:
            raise ValueError("INP_MISSING_SPEAKER_PROFILE")
        if not contract["audience_profile"]:
            raise ValueError("INP_MISSING_AUDIENCE_PROFILE")

        # Step4: outline plan
        self._set_generation_progress(
            stage="zero_base_outline",
            message="zero_base: アウトラインを計画しています...",
            current=3,
            total=7,
            partial_body="",
        )
        title = self._generate_title(merged_context, user_prompt, article_type, target_audience, False)
        self._current_title = title
        zero_base_length_plan = self._zero_base_build_length_plan(
            contexts=contexts,
            user_prompt=user_prompt,
            article_type=article_type,
            section_count=0,
        )
        natural_style_profile = self._build_note4000_style_profile(contract)
        contract["natural_style_profile"] = natural_style_profile.to_dict()
        contract["discourse_plan_version"] = "note_4000_v1"
        detailed_outline = self._build_note4000_discourse_plan(
            contract=contract,
            user_prompt=user_prompt,
            reader_question_candidates=reader_question_candidates,
            length_plan=zero_base_length_plan,
        )
        outline = [
            {
                "heading": self._safe_contract_value(item.get("heading")),
                "new_information": self._safe_contract_value(item.get("new_information")),
                "reader_question": self._safe_contract_value(item.get("reader_question")),
            }
            for item in detailed_outline
            if isinstance(item, dict)
        ]
        self._note4000_discourse_plan = list(detailed_outline)
        zero_base_targets = zero_base_length_plan.get("targets", {})
        if not isinstance(zero_base_targets, dict):
            zero_base_targets = {}
        zero_base_targets["section_count_target"] = len(outline)
        zero_base_length_plan["targets"] = zero_base_targets
        self._zero_base_length_plan = dict(zero_base_length_plan)
        self._zero_base_section_guard_reports = []

        # Step5: section generate
        self._set_generation_progress(
            stage="zero_base_body",
            message="zero_base: セクションを生成しています...",
            current=4,
            total=7,
            partial_body="",
        )
        sections: List[str] = []
        previous_summary = ""
        section_summaries: List[str] = []
        for idx, item in enumerate(detailed_outline):
            section_plan = self._zero_base_get_section_plan(
                length_plan=zero_base_length_plan,
                section_index=idx,
            )
            section = self._zero_base_generate_section(
                outline_item=item,
                contract=contract,
                previous_summary=previous_summary,
                section_summaries=section_summaries,
                section_plan=section_plan,
            )
            if not section.strip():
                continue
            sections.append(section)
            previous_summary = self._zero_base_extract_section_summary(
                section_text=section,
                fallback=self._safe_contract_value(item.get("new_information")),
            )
            section_summaries.append(previous_summary)
            self._set_generation_progress(
                stage="zero_base_body",
                message=f"zero_base: セクション生成中 ({idx + 1}/{max(1, len(outline))})",
                current=4,
                total=7,
                partial_body=self._combine_sections(sections),
            )
        if not sections:
            fallback_heading = "補足"
            fallback_seed = ""
            if detailed_outline and isinstance(detailed_outline[0], dict):
                fallback_heading = self._safe_contract_value(detailed_outline[0].get("heading")) or fallback_heading
                fallback_seed = self._safe_contract_value(detailed_outline[0].get("new_information"))
            fallback_text = (fallback_seed or "重要な論点") + "を簡潔に共有します。"
            sections.append(f"## {fallback_heading}\n\n{fallback_text}")
        body = self._combine_sections(sections)

        # Step6: coherence / dedupe
        self._set_generation_progress(
            stage="zero_base_dedupe",
            message="zero_base: 重複を整理しています...",
            current=5,
            total=7,
            partial_body=body,
        )
        body, dedupe_audit = self._zero_base_semantic_dedupe(body=body, contract=contract)
        self._zero_base_dedupe_audit = dedupe_audit

        # Step7: minimal postprocess
        self._set_generation_progress(
            stage="zero_base_postprocess",
            message="zero_base: 最小後処理を適用しています...",
            current=6,
            total=7,
            partial_body=body,
        )
        lead_target_chars = int(zero_base_targets.get("lead_chars", 130) or 130)
        lead = self._generate_lead(
            merged_context,
            user_prompt,
            article_type,
            target_audience,
            target_chars=lead_target_chars,
            title=title,
        )
        lead_before_postprocess = lead
        body_before_postprocess = body
        hashtags = self._generate_hashtags(merged_context, article_type)
        lead, body, postprocess_audit = self._zero_base_minimal_postprocess(
            lead=lead,
            body=body,
            target_audience=target_audience,
            contract=contract,
        )
        lead = self._reduce_target_term_overuse(lead, target_audience=target_audience)
        body = self._reduce_target_term_overuse(body, target_audience=target_audience)
        body = self._zero_base_align_corporate_voice(body, contract)
        lead = self._zero_base_align_corporate_voice(lead, contract)
        lead, body = self._dedupe_lead_body(lead, body)
        body, linebreak_profile_report = self._zero_base_apply_linebreak_profile(
            body=body,
            contract=contract,
        )
        self._zero_base_rhythm_report = {
            "linebreak_profile": linebreak_profile_report,
        }
        body, legal_guard_report = self._zero_base_apply_minimal_legal_guard(
            body=body,
            contract=contract,
        )

        body_for_linkedin = body
        body_before_links = body
        hard_soft_eval = self._evaluate_hard_soft_thresholds(
            before_lead=lead_before_postprocess,
            before_body=body_before_postprocess,
            after_lead=lead,
            after_body=body_before_links,
        )
        hard_soft_eval = self._relax_note_quality_gate(hard_soft_eval)
        if not isinstance(hard_soft_eval, dict):
            hard_soft_eval = {}
        if hard_soft_eval.get("enabled"):
            naturalness_for_eval = dict(getattr(self, "_last_contextual_naturalness_report", {}) or {})
        else:
            naturalness_for_eval = self._check_contextual_naturalness(
                f"{lead or ''}\n\n{body_before_links or ''}"
            )
            self._last_contextual_naturalness_report = dict(naturalness_for_eval or {})
            semantic_layout = naturalness_for_eval.get("semantic_layout", {})
            if not isinstance(semantic_layout, dict):
                semantic_layout = {}
            semantic_issue_count = int(
                naturalness_for_eval.get(
                    "semantic_issue_count",
                    semantic_layout.get("semantic_issue_count", 0),
                )
                or 0
            )
            hard_soft_eval = {
                "enabled": False,
                "mode": str(hard_soft_eval.get("mode", "off") or "off"),
                "hard_failed": False,
                "hard_fail_reasons": [],
                "soft_warnings": [],
                "metrics": {
                    "rewrite_ratio": 0.0,
                    "heading_delta": 0,
                    "grammar_per_1k": 0.0,
                    "unpredictability": 0.0,
                    "flat_zone_count": 0,
                    "semantic_issue_count": semantic_issue_count,
                    "instructional_fragment_count": int(
                        naturalness_for_eval.get("instructional_fragment_count", 0) or 0
                    ),
                    "ai_template_ending_count": int(
                        naturalness_for_eval.get("ai_template_ending_count", 0) or 0
                    ),
                    "ai_template_ending_ratio": round(
                        float(naturalness_for_eval.get("ai_template_ending_ratio", 0.0) or 0.0),
                        4,
                    ),
                    "heading_alignment_mean": round(
                        float(semantic_layout.get("heading_alignment_mean", 0.0) or 0.0),
                        4,
                    ),
                    "transition_jaccard_mean": round(
                        float(semantic_layout.get("transition_jaccard_mean", 0.0) or 0.0),
                        4,
                    ),
                    "abrupt_opening_ratio": round(
                        float(semantic_layout.get("abrupt_opening_ratio", 0.0) or 0.0),
                        4,
                    ),
                },
            }
        self._last_hard_soft_eval = dict(hard_soft_eval)
        naturalness_layout = naturalness_for_eval.get("semantic_layout", {})
        if not isinstance(naturalness_layout, dict):
            naturalness_layout = {}
        semantic_issue_count = int(
            naturalness_for_eval.get(
                "semantic_issue_count",
                naturalness_layout.get("semantic_issue_count", 0),
            )
            or 0
        )
        soft_warnings = self._last_hard_soft_eval.get("soft_warnings", [])
        if not isinstance(soft_warnings, list):
            soft_warnings = []
        hard_fail_reasons = self._last_hard_soft_eval.get("hard_fail_reasons", [])
        if not isinstance(hard_fail_reasons, list):
            hard_fail_reasons = []
        self._last_final_quality_eval = {
            "evaluated": True,
            "mode": str(self._last_hard_soft_eval.get("mode", "off") or "off"),
            "hard_failed": bool(self._last_hard_soft_eval.get("hard_failed", False)),
            "hard_fail_reasons": list(hard_fail_reasons),
            "soft_warning_count": len(soft_warnings),
            "semantic_issue_count": semantic_issue_count,
            "instructional_fragment_count": int(
                naturalness_for_eval.get("instructional_fragment_count", 0) or 0
            ),
            "source": "zero_base_scaffold",
        }
        body = self._inject_contextual_source_links(body, contexts)
        references_md = self._format_references(contexts)
        cta = self._safe_contract_value(contract.get("cta")) or self._make_cta(
            title=title,
            user_prompt=user_prompt,
            target_audience=target_audience,
            platform="note",
        )
        cta = self._zero_base_adjust_cta_length(
            cta=cta,
            target_chars=int(zero_base_targets.get("cta_chars", 120) or 120),
            target_audience=target_audience,
            announcement_like=self._safe_contract_value(contract.get("article_type")).lower() == "announcement",
        )
        full_body_parts = [lead, body]
        if references_md:
            full_body_parts.append(references_md)
        full_body_parts.append(cta)
        full_body = "\n\n".join(part for part in full_body_parts if part)
        full_text = f"{title}\n\n{full_body}\n\n---\n\n{hashtags}".strip()
        linkedin_cta = self._make_cta(
            title=title,
            user_prompt=user_prompt,
            target_audience=target_audience,
            platform="linkedin",
        )
        linkedin_text = self._format_for_linkedin(lead, body_for_linkedin, linkedin_cta, hashtags)
        note_body_core = "\n\n".join(part for part in [lead, body_before_links, cta] if part)
        zero_base_actual = {
            "lead_chars": len(lead or ""),
            "body_chars_before_links": len(body_before_links or ""),
            "body_chars": len(body or ""),
            "cta_chars": len(cta or ""),
            "note_chars_without_refs": len(note_body_core or ""),
            "section_count": self._heading_count(body_before_links),
        }
        body_target = int(zero_base_targets.get("body_chars", 0) or 0)
        self._zero_base_length_plan = {
            **dict(zero_base_length_plan),
            "actual": zero_base_actual,
            "meets_body_target_85pct": bool(
                body_target <= 0 or zero_base_actual["body_chars_before_links"] >= int(body_target * 0.85)
            ),
        }
        contract_alignment = self._zero_base_compute_contract_alignment(
            contract=contract,
            body=body_before_links,
            question_sources=resolved_question_sources,
            source_text=merged_context,
        )
        contract_alignment["linebreak_profile"] = dict(linebreak_profile_report)
        contract_alignment["section_contract_reports"] = list(getattr(self, "_zero_base_section_guard_reports", []) or [])
        contract_alignment["section_contract_issue_count"] = sum(
            int(item.get("blocking_issue_count", 0) or 0)
            for item in contract_alignment["section_contract_reports"]
            if isinstance(item, dict)
        )
        self._last_contract_alignment = contract_alignment
        self._last_zero_base_contract = dict(contract)
        review_points = self._collect_review_points(f"{lead or ''}\n\n{body_before_links or ''}")

        result = {
            "title": title,
            "lead": lead,
            "body": body,
            "full_body": full_body,
            "hashtags": hashtags,
            "references": references_md,
            "full_text": full_text,
            "review_points": review_points,
            "user_prompt": user_prompt,
            "category_policy": self._category_policy,
            "pipeline_check": self._build_pipeline_check(platform="note"),
            "quality_pipeline_check": self._build_quality_pipeline_check(),
            "hard_failed": bool((self._last_hard_soft_eval or {}).get("hard_failed", False)),
            "hard_fail_reasons": list((self._last_hard_soft_eval or {}).get("hard_fail_reasons", []) or []),
            "hard_soft_mode": str((self._last_hard_soft_eval or {}).get("mode", "off") or "off"),
            "section_feedback_reports": list(getattr(self, "_zero_base_section_guard_reports", []) or []),
            "llm_check": self._build_llm_check(),
            "linkedin_text": linkedin_text,
            "pipeline_check_linkedin": self._build_pipeline_check(
                platform="linkedin",
                post_pipeline_skipped=True,
                skip_reason="zero_base_v2 scaffold path",
            ),
            "zero_base_contract": contract,
            "zero_base_outline": outline,
            "zero_base_discourse_plan": list(detailed_outline),
            "zero_base_section_summaries": section_summaries,
            "zero_base_question_sources": resolved_question_sources,
            "zero_base_dedupe_audit": dedupe_audit,
            "zero_base_postprocess_audit": postprocess_audit,
            "zero_base_legal_guard_report": legal_guard_report,
            "zero_base_length_plan": dict(self._zero_base_length_plan),
            "natural_style_profile": dict(contract.get("natural_style_profile", {}) or {}),
            "zero_base_alignment_score": float(contract_alignment.get("alignment_score", 0.0) or 0.0),
            "zero_base_must_cover_integration_report": {
                "mode": "outline_only",
                "integrated_count": 0,
            },
            "zero_base_rhythm_report": dict(self._zero_base_rhythm_report),
        }
        self._set_generation_progress(
            stage="completed",
            message="生成完了",
            current=7,
            total=7,
            partial_body=body,
        )
        return result

    def generate(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
        perspective: str = "auto",
        output_format: str = "note",
        psychology_structure: str = "auto",
        writing_focus: str = "auto",
        length_mode: str = "normal",
    ) -> Dict[str, str]:
        """記事を生成する。
        
        Args:
            output_format: "note" または "linkedin"。LinkedInの場合は短縮版を生成。
        """
        self.reset_generation_progress()
        self._set_generation_progress(
            stage="prepare",
            message="生成準備中...",
            current=0,
            total=1,
            partial_body="",
        )

        # Combine built-in and custom prompts
        combined_prompts = dict(ARTICLE_TYPE_PROMPTS)
        combined_prompts.update(genre_manager.get_all_prompts())
        
        if article_type not in combined_prompts:
            raise ValueError(f"Unsupported article_type: {article_type}")
        custom_genre = genre_manager.get_genre(article_type) if article_type not in ARTICLE_TYPE_PROMPTS else None
        custom_prompt = (custom_genre or {}).get("prompt", "")
        custom_meta = (custom_genre or {}).get("meta") if custom_genre else None
        
        # Store combined prompts for use in other methods
        self._current_prompts = combined_prompts
        self._current_type = article_type
        self._quality_phase_reports = []
        self._section_feedback_reports = []
        self._last_retry_telemetry = []
        self._last_hard_soft_eval = {}
        self._last_final_quality_eval = {}
        self._last_repair_only_report = {}
        self._last_contextual_naturalness_report = {}
        self._last_resonance_phase_effect_metrics = {}
        self._editor_persona_snapshots = {}
        self._zero_base_length_plan = {}
        self._note4000_discourse_plan = []
        self._last_contract_alignment = {}
        self._zero_base_rhythm_report = {}
        self._section_generation_config = get_section_generation_config()
        self._postprocess_config = get_postprocess_config()
        self._source_reading_config = get_source_reading_config()
        self._latest_user_prompt = user_prompt or ""
        self._runtime_input_contract = dict(getattr(self, "_input_contract_seed", {}) or {})
        self._prompt_echo_references = self._build_prompt_echo_references()

        contexts = self._enrich_image_contexts(contexts, user_prompt)
        if not contexts:
            raise ValueError("有効なソースを取得できませんでした。URLまたはファイルを確認してください。")
        self._source_urls = [ctx.url.strip() for ctx in contexts if getattr(ctx, "url", None) and str(ctx.url).strip()]
        merged_context = self._merge_contexts(contexts)
        generation_mode = get_generation_mode()
        dispatch_path = self._resolve_generation_dispatch(generation_mode)
        self._last_generation_dispatch = {
            "generation_mode": generation_mode,
            "dispatch_path": dispatch_path,
        }
        logger.info(
            "Generation dispatch: mode=%s path=%s",
            generation_mode,
            dispatch_path,
        )
        return self._generate_zero_base_scaffold(
            contexts=contexts,
            merged_context=merged_context,
            user_prompt=user_prompt,
            article_type=article_type,
            perspective=perspective,
            output_format=output_format,
            psychology_structure=psychology_structure,
            writing_focus=writing_focus,
            length_mode=length_mode,
            custom_prompt=custom_prompt,
            custom_meta=custom_meta,
        )
    def _article_generator_legacy_dedupe_body_repetition(self, body: str) -> str:
        """セクション間の重複導入句・重複段落を最終段で抑制する。"""
        sections = self._extract_section_blocks(body)
        if len(sections) < 2:
            return body

        seen_openings: List[str] = []
        seen_paragraphs: List[str] = []
        rebuilt_sections: List[str] = []
        removed_count = 0

        for heading, content in sections:
            raw_paragraphs = [p.strip() for p in re.split(r"\n{2,}", content or "") if p.strip()]
            if not raw_paragraphs:
                rebuilt_sections.append(f"## {heading}\n\n{(content or '').strip()}".strip())
                continue

            paragraphs = list(raw_paragraphs)
            first_para = paragraphs[0].strip()
            if first_para and not self._is_reference_or_list_paragraph(first_para):
                first_sentences = [s.strip() for s in _RE_SENTENCE_SPLIT.split(first_para) if s.strip()]
                if len(first_sentences) >= 2:
                    first_opening_norm = self._normalize_similarity_text(first_sentences[0])[:180]
                    if len(first_opening_norm) >= 18:
                        duplicated_opening = False
                        for prev in seen_openings:
                            ratio = SequenceMatcher(None, first_opening_norm, prev).ratio()
                            jaccard, containment = self._similarity_overlap_scores(first_opening_norm, prev)
                            if (
                                ratio >= SECTION_OPENING_SIMILARITY_THRESHOLD
                                or jaccard >= SECTION_OPENING_JACCARD_THRESHOLD
                                or containment >= SECTION_OPENING_CONTAINMENT_THRESHOLD
                            ):
                                duplicated_opening = True
                                break
                        if duplicated_opening:
                            paragraphs[0] = "".join(first_sentences[1:]).strip()
                            removed_count += 1

            kept: List[str] = []
            local_norms: List[str] = []
            substantive_paragraphs = [p for p in paragraphs if p and not self._is_reference_or_list_paragraph(p)]
            min_substantive = 1 if substantive_paragraphs else 0

            for para_idx, para in enumerate(paragraphs):
                para = para.strip()
                if not para:
                    continue

                is_reference_line = self._is_reference_or_list_paragraph(para)
                norm_para = self._normalize_similarity_text(para)
                remaining_substantive = sum(
                    1
                    for item in paragraphs[para_idx + 1 :]
                    if item and not self._is_reference_or_list_paragraph(item)
                )

                if is_reference_line:
                    kept.append(para)
                    if len(norm_para) >= 24 and not is_reference_line:
                        local_norms.append(norm_para[:SIMILARITY_NGRAM_MAX_LEN])
                    continue
                if len(norm_para) < 50:
                    kept.append(para)
                    if len(norm_para) >= 24:
                        local_norms.append(norm_para[:SIMILARITY_NGRAM_MAX_LEN])
                    continue
                if len(norm_para) < 90:
                    duplicate_short = False
                    for prev in seen_paragraphs:
                        jaccard, containment = self._similarity_overlap_scores(norm_para, prev)
                        if containment >= 0.93 or jaccard >= 0.74:
                            duplicate_short = True
                            break
                    if not duplicate_short:
                        for prev in local_norms:
                            jaccard, containment = self._similarity_overlap_scores(norm_para, prev)
                            if containment >= 0.94 or jaccard >= 0.76:
                                duplicate_short = True
                                break
                    kept_substantive = sum(
                        1 for item in kept if item and not self._is_reference_or_list_paragraph(item)
                    )
                    if duplicate_short and (kept_substantive + remaining_substantive) >= min_substantive:
                        removed_count += 1
                        continue
                    kept.append(para)
                    local_norms.append(norm_para[:SIMILARITY_NGRAM_MAX_LEN])
                    continue

                duplicate = False
                for prev in seen_paragraphs:
                    jaccard, containment = self._similarity_overlap_scores(norm_para, prev)
                    if (
                        containment >= BODY_PARAGRAPH_DEDUPE_CONTAINMENT_THRESHOLD
                        or jaccard >= BODY_PARAGRAPH_DEDUPE_JACCARD_THRESHOLD
                    ):
                        duplicate = True
                        break
                if not duplicate:
                    for prev in local_norms:
                        jaccard, containment = self._similarity_overlap_scores(norm_para, prev)
                        if containment >= 0.90 or jaccard >= 0.70:
                            duplicate = True
                            break

                kept_substantive = sum(1 for item in kept if item and not self._is_reference_or_list_paragraph(item))
                if duplicate and (kept_substantive + remaining_substantive) >= min_substantive:
                    removed_count += 1
                    continue

                kept.append(para)
                local_norms.append(norm_para[:SIMILARITY_NGRAM_MAX_LEN])

            if not kept:
                kept = [raw_paragraphs[0]]

            first_substantive = next((p for p in kept if p and not self._is_reference_or_list_paragraph(p)), "")
            if first_substantive:
                first_sentences = [s.strip() for s in _RE_SENTENCE_SPLIT.split(first_substantive) if s.strip()]
                if first_sentences:
                    opening_norm = self._normalize_similarity_text(first_sentences[0])
                    if len(opening_norm) >= 18:
                        seen_openings.append(opening_norm[:180])
                        if len(seen_openings) > 48:
                            seen_openings = seen_openings[-48:]

            for para in kept:
                if self._is_reference_or_list_paragraph(para):
                    continue
                norm_para = self._normalize_similarity_text(para)
                if len(norm_para) >= 60:
                    seen_paragraphs.append(norm_para[:SIMILARITY_NGRAM_MAX_LEN])
            if len(seen_paragraphs) > 160:
                seen_paragraphs = seen_paragraphs[-160:]

            merged_content = "\n\n".join(kept).strip()
            rebuilt_sections.append(f"## {heading}\n\n{merged_content}")

        if removed_count <= 0:
            return body

        logger.info(
            "Final body repetition guard applied: removed=%s sections=%s",
            removed_count,
            len(sections),
        )
        return "\n\n".join(block.strip() for block in rebuilt_sections if block.strip()).strip()

    def _article_generator_legacy_diversify_overused_phrases(self, text: str) -> str:
        """過剰反復しやすい定型語を2回目以降だけ自然な同義へ分散する。"""
        if not text:
            return text

        replacements = {
            "自分事": {"alternates": ("当事者意識", "自分ごと"), "keep_first": 1},
            "欠かせません": {"alternates": ("要になります", "外せません"), "keep_first": 1},
            "重要な一歩": {"alternates": ("有効な着手点", "前進の足がかり"), "keep_first": 1},
            "見逃せません": {"alternates": ("軽視できません", "注意が必要です"), "keep_first": 1},
            "必要があると考えます": {"alternates": ("必要があります", "必要だと見ています"), "keep_first": 1},
            "必要だと考えます": {"alternates": ("必要です", "必要だと見ています"), "keep_first": 1},
            "見えてきます": {"alternates": ("分かってきます", "浮かび上がります"), "keep_first": 1},
            "だけでなく": {"alternates": ("に加えて", "のみならず"), "keep_first": 3},
        }
        result = text
        for source, rule in replacements.items():
            if not isinstance(rule, dict):
                continue
            alternates = tuple(rule.get("alternates", ()))
            keep_first = int(rule.get("keep_first", 1) or 1)
            if not alternates:
                continue
            matches = list(re.finditer(re.escape(source), result))
            if len(matches) <= keep_first:
                continue
            rebuilt: List[str] = []
            last = 0
            for idx, match in enumerate(matches):
                rebuilt.append(result[last:match.start()])
                if idx < keep_first:
                    rebuilt.append(source)
                else:
                    alt = alternates[(idx - keep_first) % len(alternates)]
                    rebuilt.append(alt)
                last = match.end()
            rebuilt.append(result[last:])
            result = "".join(rebuilt)
        return result

    def _article_generator_legacy_clean_redundant_connectives(self, text: str) -> str:
        """接続語の重ね掛けを最小限で補正する。"""
        if not text:
            return text

        replacements = (
            (r"しかし一方で、?同時に", "一方で"),
            (r"しかし一方で", "一方で"),
            (r"一方で、?同時に", "一方で"),
            (r"さらに、?加えて", "さらに"),
            (r"加えて、?さらに", "さらに"),
            (r"また、?さらに", "さらに"),
            (r"さらに、?また", "さらに"),
            (r"そのため\s*こそ", "そのため"),
            (r"というわけで\s*こそ", "というわけで"),
            (r"ただながら", "ただ"),
            (r"和らげるになります", "和らぐことにつながります"),
            (r"。対してAIは", "。一方、AIは"),
            (
                r"(なのだ|のだ|なのです|のです|んです)、(?=(その|この|こうした|そうした|実務で|まずは|まず|次に|一方で|加えて|さらに))",
                r"\1。",
            ),
        )
        cleaned = text
        for pattern, replacement in replacements:
            cleaned = re.sub(pattern, replacement, cleaned)

        cleaned = re.sub(r"(一方で)([、,]\s*)\1", r"\1\2", cleaned)
        cleaned = re.sub(r"(さらに)([、,]\s*)\1", r"\1\2", cleaned)
        cleaned = re.sub(r"(また)([、,]\s*)\1", r"\1\2", cleaned)
        return cleaned

    @staticmethod
    @staticmethod
    def _article_generator_legacy_soften_assertive_expressions(text: str) -> str:
        """断定的な結果・保証表現をソフトに言い換える（ルールベース）。"""
        if not text:
            return text
        _ASSERTIVE_REWRITES = [
            (r"必ずしも", "常にとは限らず"),
            (r"必ず((?:ご確認|お確かめ)(?:ください|願います|をお願いします|いただきますようお願いいたします))", r"\1"),
            (r"必ず([^\s。、]{1,20})(ます|です|でしょう|しょう)", r"多くの場合\1\2"),
            (r"必ず", "原則として"),
            (r"確実に", "おおむね"),
            (r"絶対に([^\s。、]{1,20})(ます|です)", r"\1傾向があり\2"),
            (r"100%", "ほぼ確実に"),
        ]
        result = text
        for pattern, repl in _ASSERTIVE_REWRITES:
            result = re.sub(pattern, repl, result)
        return result

    @staticmethod
    def _article_generator_legacy_strip_heading_top_adversative(text: str) -> str:
        """見出し直後の逆接開始（しかし/ただし/ただ）を除去する。"""
        if not text:
            return text
        _adversative_after_heading = re.compile(
            r"(^##[^\n]*\n\n?)"
            r"(しかし|ただし|ただ)[、,]\s*",
            flags=re.MULTILINE,
        )
        return _adversative_after_heading.sub(r"\1", text)

    def _article_generator_legacy_get_concise_compaction_config(self) -> Dict[str, Any]:
        """冗長圧縮の設定を返す。"""
        defaults = {
            "enabled": True,
            "dedupe_similarity_ratio": 0.86,
            "dedupe_jaccard_ratio": 0.62,
            "summary_overlap_ratio": 0.58,
            "max_connective_openings_per_paragraph": 2,
        }
        cfg = self._get_postprocess_config()
        concise_cfg = cfg.get("concise_compaction", {}) if isinstance(cfg, dict) else {}
        if not isinstance(concise_cfg, dict):
            return defaults
        merged = dict(defaults)
        merged.update(concise_cfg)
        return merged

    @staticmethod
    def _article_generator_legacy_is_summary_marker_sentence(sentence: str) -> bool:
        stripped = (sentence or "").strip()
        return any(stripped.startswith(marker) for marker in REDUNDANT_SUMMARY_MARKERS)

    def _article_generator_legacy_apply_concise_rewrites(self, sentence: str) -> str:
        """抽象語の重ね書きと冗長終端を短くする。"""
        result = sentence.strip()
        if not result:
            return ""

        for pattern, replacement in ABSTRACT_COMPRESSION_REWRITES:
            result = re.sub(pattern, replacement, result)

        for pattern, replacement in AI_LIKE_ENDING_REWRITES:
            result = re.sub(pattern, replacement, result)

        result = re.sub(r"([。！？])\1+", r"\1", result)
        result = re.sub(r"[、,]{2,}", "、", result)
        return result.strip()

    def _article_generator_legacy_aggressive_sentence_pruning(
        self,
        text: str,
        *,
        keep_ratio: float,
        min_sentences_per_paragraph: int,
    ) -> str:
        """長文向けに段落内文数を抑え、情報量の低い重複説明を削る。"""
        if not text:
            return text

        keep_ratio = max(0.45, min(0.90, keep_ratio))
        min_sentences_per_paragraph = max(3, min(6, min_sentences_per_paragraph))

        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        rebuilt: List[str] = []
        for para in paragraphs:
            stripped = para.strip()
            if stripped.startswith("##") or self._is_reference_or_list_paragraph(stripped):
                rebuilt.append(para)
                continue

            sentences = [s.strip() for s in _RE_SENTENCE_SPLIT.split(para) if s.strip()]
            if len(sentences) < min_sentences_per_paragraph:
                rebuilt.append(para.strip())
                continue

            keep_count = int(round(len(sentences) * keep_ratio))
            keep_count = max(2, min(len(sentences) - 1, keep_count))

            term_sets: List[set[str]] = [
                set(self._extract_content_terms(sentence, max_chars=220))
                for sentence in sentences
            ]
            selected = [0]
            selected_terms: set[str] = set(term_sets[0])
            remaining = set(range(1, len(sentences)))

            while len(selected) < keep_count and remaining:
                best_idx = -1
                best_score = -10_000.0
                for idx in list(remaining):
                    terms = term_sets[idx]
                    new_terms = len(terms - selected_terms)
                    score = (new_terms * 2.1) + (len(terms) * 0.15)
                    if self._is_summary_marker_sentence(sentences[idx]):
                        score -= 1.4
                    if re.search(r"(?:\d|%|[A-Za-z]{3,}|「[^」]+」)", sentences[idx]):
                        score += 1.0
                    if idx == len(sentences) - 1:
                        score += 0.2
                    if score > best_score:
                        best_score = score
                        best_idx = idx
                if best_idx < 0:
                    break
                selected.append(best_idx)
                selected_terms.update(term_sets[best_idx])
                remaining.remove(best_idx)

            selected = sorted(set(selected))
            if len(selected) < keep_count:
                for idx in range(1, len(sentences)):
                    if idx in selected:
                        continue
                    selected.append(idx)
                    if len(selected) >= keep_count:
                        break
                selected = sorted(set(selected))

            rebuilt.append("".join(sentences[idx] for idx in selected if 0 <= idx < len(sentences)).strip())

        return "\n\n".join(p for p in rebuilt if p.strip()).strip()

    def _article_generator_legacy_compress_redundant_explanations(self, text: str) -> str:
        """段落内の同義反復と不要導入句を統合して圧縮する。"""
        if not text:
            return text

        cfg = self._get_concise_compaction_config()
        if not bool(cfg.get("enabled", True)):
            return text

        dedupe_similarity = float(cfg.get("dedupe_similarity_ratio", 0.86) or 0.86)
        dedupe_jaccard = float(cfg.get("dedupe_jaccard_ratio", 0.62) or 0.62)
        summary_overlap = float(cfg.get("summary_overlap_ratio", 0.58) or 0.58)
        max_connective = int(cfg.get("max_connective_openings_per_paragraph", 2) or 2)
        max_connective = max(0, min(3, max_connective))
        target_reduction_ratio = float(cfg.get("target_reduction_ratio", 0.22) or 0.22)
        aggressive_keep_ratio = float(cfg.get("aggressive_keep_ratio", 0.68) or 0.68)
        aggressive_min_sentences = int(cfg.get("aggressive_min_sentences_per_paragraph", 3) or 3)
        aggressive_min_chars = int(cfg.get("aggressive_min_chars", 1600) or 1600)
        summary_like_re = re.compile(
            r"(?:この(?:背景|違い|点|核心)|言い換えると|要するに|結果として|と捉えられます|と考えます)"
        )
        abstract_re = re.compile(r"(?:こと|ため|背景|理由|性質|傾向|特徴|構造)")
        fact_signal_re = re.compile(r"(?:\d|%|[A-Za-z]{3,}|「[^」]+」)")

        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        rebuilt: List[str] = []
        global_term_counter: Counter[str] = Counter()
        for para in paragraphs:
            stripped = para.strip()
            if stripped.startswith("##") or self._is_reference_or_list_paragraph(stripped):
                rebuilt.append(para)
                continue

            sentences = [s.strip() for s in _RE_SENTENCE_SPLIT.split(para) if s.strip()]
            if not sentences:
                rebuilt.append(para)
                continue

            opener_hits = 0
            prev_template_opener = ""
            local_terms: set[str] = set()
            kept: List[str] = []
            kept_norms: List[str] = []
            dropped: List[str] = []
            min_keep = 2 if len(sentences) >= 3 else 1
            for sentence_idx, sentence in enumerate(sentences):
                current = self._apply_concise_rewrites(sentence)
                if not current:
                    continue

                current, opener_hits, prev_template_opener = self._trim_redundant_template_opening(
                    current,
                    template_hits=opener_hits,
                    max_template_openers=max_connective,
                    prev_template_opener=prev_template_opener,
                )
                if not current:
                    continue
                if sentence_idx > 0 and len(sentences) >= 2 and self._is_summary_marker_sentence(current):
                    dropped.append(current)
                    continue

                norm_current = self._normalize_similarity_text(current)
                sentence_terms = set(self._extract_content_terms(current, max_chars=220))
                local_novelty = 1.0
                global_novelty = 1.0
                if sentence_terms:
                    local_novelty = len(sentence_terms - local_terms) / max(1, len(sentence_terms))
                    global_novelty = len(sentence_terms - set(global_term_counter.keys())) / max(1, len(sentence_terms))
                if len(norm_current) >= 18 and kept_norms:
                    redundant = False
                    for norm_prev in kept_norms[-3:]:
                        ratio = SequenceMatcher(None, norm_current, norm_prev).ratio()
                        jaccard, containment = self._similarity_overlap_scores(norm_current, norm_prev)
                        if ratio >= dedupe_similarity or (jaccard >= dedupe_jaccard and containment >= 0.72):
                            redundant = True
                            break

                    if not redundant and self._is_summary_marker_sentence(current):
                        norm_prev = kept_norms[-1]
                        ratio = SequenceMatcher(None, norm_current, norm_prev).ratio()
                        jaccard, containment = self._similarity_overlap_scores(norm_current, norm_prev)
                        if ratio >= summary_overlap or jaccard >= summary_overlap or containment >= 0.80:
                            redundant = True

                    summary_like = self._is_summary_marker_sentence(current) or bool(summary_like_re.search(current))
                    long_abstract_sentence = len(current) >= 58 and bool(abstract_re.search(current))
                    low_novelty = len(sentence_terms) >= 4 and local_novelty <= 0.45
                    global_overlap_heavy = len(sentence_terms) >= 5 and global_novelty <= 0.40
                    fact_signal = bool(fact_signal_re.search(current))

                    if sentence_idx > 0 and not fact_signal and (
                        redundant
                        or (
                            low_novelty
                            and (
                                summary_like
                                or long_abstract_sentence
                                or global_overlap_heavy
                            )
                        )
                        or (
                            long_abstract_sentence
                            and len(current) >= 82
                            and local_novelty <= 0.55
                        )
                    ):
                        dropped.append(current)
                        continue

                    if redundant and len(kept) >= 1:
                        dropped.append(current)
                        continue

                kept.append(current)
                if norm_current:
                    kept_norms.append(norm_current[:240])
                local_terms.update(sentence_terms)
                if sentence_terms:
                    global_term_counter.update(sentence_terms)

            if not kept:
                kept.append(self._apply_concise_rewrites(sentences[0]))
            elif len(kept) < min_keep and dropped:
                for sentence in dropped:
                    kept.append(sentence)
                    if len(kept) >= min_keep:
                        break

            rebuilt.append("".join(s for s in kept if s).strip())

        compressed = "\n\n".join(p for p in rebuilt if p.strip()).strip()
        baseline_len = max(1, len((text or "").strip()))
        reduction_ratio = (baseline_len - len(compressed)) / baseline_len
        if (
            len((text or "").strip()) >= aggressive_min_chars
            and reduction_ratio < target_reduction_ratio
        ):
            compressed = self._aggressive_sentence_pruning(
                compressed,
                keep_ratio=aggressive_keep_ratio,
                min_sentences_per_paragraph=aggressive_min_sentences,
            )
        return compressed

    def _article_generator_legacy_trim_nonclosing_section_tail_summaries(self, body: str) -> str:
        """非締めセクション末の機械的な要点1行を抑制する。"""
        if not body:
            return body
        sections = self._extract_section_blocks(body)
        if not sections:
            return body

        summary_start_re = re.compile(
            r"^(?:要点(?:は|としては)|要するに|まとめると|結論として|ひと言で言うと|"
            r"ここまで(?:を)?まとめると|ここまでの要点は|押さえておきたいのは)"
        )
        rebuilt: List[str] = []

        for idx, (heading, content) in enumerate(sections):
            section_text = (content or "").strip()
            if not section_text:
                rebuilt.append(f"## {heading}".strip())
                continue

            is_last_section = idx == len(sections) - 1
            if CLOSING_HEADING_PATTERN.search(heading or "") or is_last_section:
                rebuilt.append(f"## {heading}\n\n{section_text}".strip())
                continue

            paragraphs = [p.strip() for p in re.split(r"\n{2,}", section_text) if p.strip()]
            if len(paragraphs) < 2:
                rebuilt.append(f"## {heading}\n\n{section_text}".strip())
                continue

            last_para = paragraphs[-1]
            if self._is_reference_or_list_paragraph(last_para) or re.search(r"https?://", last_para):
                rebuilt.append(f"## {heading}\n\n{section_text}".strip())
                continue

            last_sentences = [s.strip() for s in _RE_SENTENCE_SPLIT.split(last_para) if s.strip()]
            section_sentence_count = len([s for s in _RE_SENTENCE_SPLIT.split(section_text) if s.strip()])
            first_sentence = last_sentences[0] if last_sentences else ""
            looks_summary = bool(
                first_sentence
                and (
                    self._is_summary_marker_sentence(first_sentence)
                    or summary_start_re.match(first_sentence)
                )
            )

            if (
                looks_summary
                and len(last_sentences) <= 2
                and len(last_para) <= 140
                and section_sentence_count >= 3
            ):
                paragraphs = paragraphs[:-1]

            merged = "\n\n".join(paragraphs).strip()
            rebuilt.append(f"## {heading}\n\n{merged}".strip())

        return "\n\n".join(block for block in rebuilt if block.strip()).strip()

    @staticmethod
    def _article_generator_legacy_normalize_opening_token(token: str) -> str:
        return re.sub(r"[、,\s]+$", "", str(token or "").strip())

    @staticmethod
    def _article_generator_legacy_is_logical_required_opening(token: str) -> bool:
        return any(token.startswith(prefix) for prefix in LOGICAL_REQUIRED_OPENING_PREFIXES)

    @staticmethod
    def _article_generator_legacy_is_suppressible_template_opening(token: str) -> bool:
        return any(token.startswith(prefix) for prefix in SUPPRESSIBLE_TEMPLATE_OPENING_PREFIXES)

    @staticmethod
    def _article_generator_legacy_strip_opening_safely(sentence: str, pattern: str) -> Tuple[str, bool]:
        candidate = re.sub(pattern, "", sentence, count=1).lstrip("、, \t")
        if not candidate:
            return sentence, False
        if re.match(
            r"^(?:は|が|を|に|で|と|も|へ|から|まで|だけ|ばかり)(?:[、,]|$)",
            candidate,
        ):
            return sentence, False
        return candidate, True

    def _article_generator_legacy_trim_redundant_template_opening(
        self,
        sentence: str,
        *,
        template_hits: int,
        max_template_openers: int,
        prev_template_opener: str,
    ) -> Tuple[str, int, str]:
        """必要接続は残し、弱いテンプレ導入のみ過多時に抑制する。"""
        current = sentence
        opener_token = ""
        for pattern in AI_LIKE_OPENING_PATTERNS:
            matched = re.match(pattern, current)
            if not matched:
                continue
            opener_token = self._normalize_opening_token(matched.group(0))
            is_logical = self._is_logical_required_opening(opener_token)
            is_template = self._is_suppressible_template_opening(opener_token)
            same_template = bool(opener_token) and opener_token == prev_template_opener

            if is_template and (same_template or template_hits >= max_template_openers):
                stripped, applied = self._strip_opening_safely(current, pattern)
                if applied:
                    current = stripped
                return current, template_hits, prev_template_opener

            if is_template:
                return current, template_hits + 1, opener_token
            if is_logical:
                return current, template_hits, ""
            return current, template_hits + 1, ""

        return current, template_hits, ""

    def _article_generator_legacy_reduce_ai_like_openings(self, text: str) -> str:
        """文頭導入を整える。必要接続は保持し、弱い定型の連続だけ抑える。"""
        if not text:
            return text

        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        rebuilt: List[str] = []
        prev_template_opener = ""
        for para in paragraphs:
            stripped = para.strip()
            if stripped.startswith("##") or self._is_reference_or_list_paragraph(stripped):
                rebuilt.append(para)
                prev_template_opener = ""
                continue

            sentences = [s.strip() for s in _RE_SENTENCE_SPLIT.split(para) if s.strip()]
            if not sentences:
                rebuilt.append(para)
                prev_template_opener = ""
                continue

            first = sentences[0]
            first, _, prev_template_opener = self._trim_redundant_template_opening(
                first,
                template_hits=0,
                max_template_openers=1,
                prev_template_opener=prev_template_opener,
            )
            if first:
                sentences[0] = first
            rebuilt.append("".join(sentences).strip())

        return "\n\n".join(block for block in rebuilt if block.strip()).strip()

    def _article_generator_legacy_reduce_ai_like_endings(self, text: str) -> str:
        """文末のAI定型を自然な終止へ寄せる。"""
        if not text:
            return text
        result = text
        for pattern, replacement in AI_LIKE_ENDING_REWRITES:
            result = re.sub(pattern, replacement, result)
        return result

    def _article_generator_legacy_reduce_target_term_overuse(self, text: str, *, target_audience: str, keep: int = 2) -> str:
        """ターゲット語の過剰反復を抑える。属性ラベルは必要に応じて非表示化する。"""
        if not text:
            return text
        audience = (target_audience or "").strip()
        result = text
        sensitive_audience = self._is_sensitive_audience_label(audience)
        demographic_topic_explicit = self._is_demographic_topic_explicit(audience)
        if demographic_topic_explicit:
            return result
        suppress_demographic_labels = bool(sensitive_audience and not demographic_topic_explicit)

        # 読者属性ラベルは原則本文に出さない（記事テーマとして明示が必要な場合は維持）。
        demographic_patterns = [
            r"(?:\d{2}代(?:前半|後半)?)(?:の)?(?:読者|世帯|家庭)?",
            r"共働き(?:の)?(?:世帯|家庭|読者)?",
            r"独身(?:世帯|者)?",
            r"単身(?:世帯|者)?",
            r"子育て(?:世帯|家庭)?",
            r"育児(?:世帯|家庭)?",
            r"高齢(?:者|世帯)?",
            r"学生(?:向け|層)?",
        ]
        if suppress_demographic_labels:
            for pattern in demographic_patterns:
                result = re.sub(pattern, "読者", result)
            result = re.sub(r"読者(?:の)?(?:読者|世帯|家庭)", "読者", result)
            result = re.sub(r"読者{2,}", "読者", result)

        if audience and suppress_demographic_labels:
            audience_label = re.escape(audience)
            result = re.sub(audience_label, "読者", result)

        kyodobataraki_pattern = re.compile(r"(?:\d{2}代の)?共働き(?:の)?(?:世帯|家庭|読者)?")
        kyodobataraki_hits = kyodobataraki_pattern.findall(result)
        if kyodobataraki_hits:
            keep_count = 0 if suppress_demographic_labels else max(0, keep)
            seen = 0

            def _replace_kyodobataraki(match: re.Match[str]) -> str:
                nonlocal seen
                seen += 1
                if suppress_demographic_labels:
                    return "読者"
                if seen <= keep_count:
                    return match.group(0)
                token = match.group(0)
                if "読者" in token:
                    return "読者"
                if "世帯" in token:
                    return "忙しい世帯"
                return "忙しい家庭"

            result = kyodobataraki_pattern.sub(_replace_kyodobataraki, result)

        if suppress_demographic_labels:
            result = re.sub(
                r"(?:20|30|40|50|60)代(?:の)?(?:読者|世帯|家庭)?",
                "読者",
                result,
            )

        return result

    def _article_generator_legacy_normalize_ai_like_heading_labels(self, text: str) -> str:
        """見出しのAIテンプレ語を自然なラベルへ寄せる。"""
        if not text:
            return text
        lines = text.splitlines()
        rewritten: List[str] = []
        for line in lines:
            updated = line
            if re.match(r"^\s*##\s+", line):
                for pattern, replacement in AI_LIKE_HEADING_REWRITES:
                    updated = re.sub(pattern, replacement, updated).strip()
                updated = re.sub(r"(を振り返る){2,}", "を振り返る", updated)
            rewritten.append(updated)
        return "\n".join(rewritten)

    def _article_generator_legacy_repair_subjectless_openings(self, text: str) -> str:
        """主語省略が過剰で意味が取りづらい冒頭文を最小補修する。"""
        if not text:
            return text

        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        rebuilt: List[str] = []
        for para in paragraphs:
            stripped = para.strip()
            if stripped.startswith("##") or self._is_reference_or_list_paragraph(stripped):
                rebuilt.append(para)
                continue

            sentences = [s.strip() for s in _RE_SENTENCE_SPLIT.split(para) if s.strip()]
            if not sentences:
                rebuilt.append(para)
                continue

            first = sentences[0]
            replacements = (
                (r"^万能な創造者ではありません。", "生成AIは万能な創造者ではありません。"),
                (r"^生み出すのは、", "生成AIが生み出すのは、"),
                (r"^大量のデータをもとにパターンを学び、", "生成AIは大量のデータをもとにパターンを学び、"),
                (r"^書く文章には、", "生成AIが書く文章には、"),
            )
            for pattern, replacement in replacements:
                first = re.sub(pattern, replacement, first)
            sentences[0] = first
            rebuilt.append("".join(sentences).strip())

        return "\n\n".join(block for block in rebuilt if block.strip()).strip()

    @staticmethod
    def _article_generator_legacy_extract_theme_entities(title: str, outline: object = None) -> List[str]:
        """タイトルとアウトラインからテーマ名詞句を1-3個抽出する。

        R19: テーマ語主語の段落横断追跡に使用。
        """
        candidates: List[str] = []
        title_clean = (title or "").strip()
        if not title_clean:
            return candidates

        # タイトルから主要名詞句を抽出（カタカナ語・漢字語・英字語・複合語）
        # R20: 「フィルターバブル」「情報リテラシー」等の複合名詞にも対応
        for m in re.finditer(
            r"[ァ-ヶー]{3,12}[一-龥々〆ヵヶ]{1,6}"  # カタカナ+漢字（エコーチェンバー現象）
            r"|[一-龥々〆ヵヶ]{1,6}[ァ-ヶー]{3,12}"  # 漢字+カタカナ（情報リテラシー）
            r"|[一-龥々〆ヵヶ]{2,8}"                  # 漢字（蒸留攻撃）
            r"|[ァ-ヶー]{3,12}"                       # カタカナ（フィルターバブル）
            r"|[A-Za-z][A-Za-z0-9\-]{2,15}",          # 英字（ChatGPT）
            title_clean,
        ):
            word = m.group()
            # ストップワード除外
            if word in ("について", "における", "としての", "のための", "に関する"):
                continue
            if word not in candidates:
                candidates.append(word)
            if len(candidates) >= 3:
                break

        return candidates

    def _article_generator_legacy_apply_prodrop_zero_anaphora(self, text: str, theme_entities: Optional[List[str]] = None) -> str:
        """段落内の主語反復を抑えて、ゼロ照応/項省略へ寄せる。

        R19: theme_entities が指定された場合、テーマ語は段落をまたいで追跡し、
        5文以内の再出現で連続2文目以降をドロップする。
        R20: 交互ドロップのバグ修正（dict キーのユニーク性で no-op だった）。
        出現回数を専用カウンタ theme_drop_counts で管理し、真の交互ドロップを実現。
        """
        if not text:
            return text

        theme_set = set(theme_entities or [])
        # テーマ語の段落横断カウンタ（最後に出現した文番号）
        theme_last_seen: Dict[str, int] = {}
        # R20: テーマ語の出現回数カウンタ（交互ドロップ用）
        theme_drop_counts: Dict[str, int] = {}
        global_sentence_idx = 0

        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        rebuilt: List[str] = []

        for para in paragraphs:
            stripped = para.strip()
            if stripped.startswith("##") or self._is_reference_or_list_paragraph(stripped):
                rebuilt.append(para)
                continue

            sentences = [s.strip() for s in _RE_SENTENCE_SPLIT.split(para) if s.strip()]
            if len(sentences) < 2:
                # 短い段落でもテーマ語カウントは更新
                if theme_set and sentences:
                    for sent in sentences:
                        subj_m = re.match(r"^([^、。！？\s]{1,20}?)(?:は|が)", sent)
                        if subj_m and subj_m.group(1) in theme_set:
                            theme_last_seen[subj_m.group(1)] = global_sentence_idx
                        global_sentence_idx += 1
                rebuilt.append(para)
                continue

            prev_subject = ""
            pronoun_subject_seen = 0
            edited: List[str] = []
            for sentence in sentences:
                subject_match = re.match(r"^([^、。！？\s]{1,20}?)(?:は|が)", sentence)
                subject = subject_match.group(1) if subject_match else ""
                updated = sentence

                # 段落内の同一主語反復ドロップ（従来ロジック）
                if subject and subject == prev_subject:
                    updated = re.sub(
                        rf"^{re.escape(subject)}(?:は|が)",
                        "",
                        updated,
                        count=1,
                    ).lstrip("、, \t")
                # R19+R20: テーマ語の段落横断ドロップ
                elif subject and subject in theme_set and subject != prev_subject:
                    last = theme_last_seen.get(subject)
                    if last is not None and (global_sentence_idx - last) <= 5:
                        # R20: 専用カウンタで交互ドロップ（偶数回目をドロップ）
                        theme_drop_counts[subject] = theme_drop_counts.get(subject, 0) + 1
                        if theme_drop_counts[subject] % 2 == 0:
                            updated = re.sub(
                                rf"^{re.escape(subject)}(?:は|が)",
                                "",
                                updated,
                                count=1,
                            ).lstrip("、, \t")

                if re.match(r"^(私|わたし|僕|私たち|当社|弊社)(?:は|が)", updated):
                    pronoun_subject_seen += 1
                    if pronoun_subject_seen >= 2:
                        updated = re.sub(r"^(私|わたし|僕|私たち|当社|弊社)(?:は|が)", "", updated, count=1).lstrip("、, \t")

                if updated:
                    edited.append(updated)
                else:
                    edited.append(sentence)
                if subject:
                    prev_subject = subject
                    if subject in theme_set:
                        theme_last_seen[subject] = global_sentence_idx
                global_sentence_idx += 1

            rebuilt.append("".join(edited).strip())

        return "\n\n".join(block for block in rebuilt if block.strip()).strip()

    def _article_generator_legacy_reduce_repeated_named_entity_openings(self, body: str) -> str:
        """セクション冒頭の同一固有名詞主語の連発を抑え、文脈省略へ寄せる。"""
        if not body:
            return body
        sections = self._extract_section_blocks(body)
        if len(sections) < 2:
            return body

        payloads: List[Dict[str, Any]] = []
        entity_sections: Dict[str, List[int]] = {}
        blocked_entities = {
            "これ",
            "それ",
            "この",
            "その",
            "私",
            "わたし",
            "僕",
            "あなた",
            "読者",
            "地域",
            "企業",
            "課題",
            "支援",
            "会員",
            "場合",
        }

        for section_idx, (heading, content) in enumerate(sections):
            paragraphs = [p.strip() for p in re.split(r"\n{2,}", content or "") if p.strip()]
            first_para_idx: Optional[int] = None
            first_sentence_idx: Optional[int] = None
            first_sentence = ""
            entity = ""

            for para_idx, para in enumerate(paragraphs):
                if self._is_reference_or_list_paragraph(para):
                    continue
                sentences = [s.strip() for s in _RE_SENTENCE_SPLIT.split(para) if s.strip()]
                if not sentences:
                    continue
                first_para_idx = para_idx
                first_sentence_idx = 0
                first_sentence = sentences[0]
                match = re.match(r"^([^、。！？\s]{4,24}?)(?:は|が)", first_sentence)
                if match:
                    candidate = match.group(1).strip()
                    if candidate not in blocked_entities and re.search(r"[一-龯ァ-ヶA-Za-z]", candidate):
                        entity = candidate
                break

            payload = {
                "heading": heading,
                "content": content,
                "paragraphs": paragraphs,
                "first_para_idx": first_para_idx,
                "first_sentence_idx": first_sentence_idx,
                "first_sentence": first_sentence,
                "entity": entity,
            }
            payloads.append(payload)
            if entity:
                entity_sections.setdefault(entity, []).append(section_idx)

        rewritten = 0
        rebuilt_sections: List[str] = []

        for section_idx, payload in enumerate(payloads):
            heading = str(payload.get("heading", "") or "")
            content = str(payload.get("content", "") or "")
            paragraphs = list(payload.get("paragraphs", []) or [])
            entity = str(payload.get("entity", "") or "")
            first_para_idx = payload.get("first_para_idx")

            if (
                entity
                and isinstance(first_para_idx, int)
                and 0 <= first_para_idx < len(paragraphs)
                and len(entity_sections.get(entity, [])) >= 2
                and section_idx > entity_sections[entity][0]
            ):
                sentences = [s.strip() for s in _RE_SENTENCE_SPLIT.split(paragraphs[first_para_idx]) if s.strip()]
                if sentences:
                    original = sentences[0]
                    updated = re.sub(rf"^{re.escape(entity)}(?:は|が)", "", original, count=1).lstrip("、, \t")
                    if updated and len(updated) >= 12:
                        sentences[0] = updated
                        paragraphs[first_para_idx] = "".join(sentences).strip()
                        rewritten += 1

            merged_content = "\n\n".join(p for p in paragraphs if p.strip()).strip() or content.strip()
            rebuilt_sections.append(f"## {heading}\n\n{merged_content}".strip())

        if rewritten <= 0:
            return body
        logger.info("Named-entity opening guard applied: rewritten=%s", rewritten)
        return "\n\n".join(block for block in rebuilt_sections if block.strip()).strip()

    def _article_generator_legacy_compress_repeated_subject_openings(self, body: str) -> str:
        """セクション冒頭の同型主語句（XのYは/が）の連発を圧縮する。"""
        if not body:
            return body
        sections = self._extract_section_blocks(body)
        if len(sections) < 2:
            return body

        blocked_subjects = {
            "これ",
            "それ",
            "この",
            "その",
            "私",
            "わたし",
            "私たち",
            "僕",
            "あなた",
            "読者",
        }
        subject_seen: Dict[str, int] = {}
        rewritten = 0
        rebuilt_sections: List[str] = []

        for heading, content in sections:
            paragraphs = [p.strip() for p in re.split(r"\n{2,}", content or "") if p.strip()]
            first_para_idx: Optional[int] = None
            first_sentence = ""
            subject_phrase = ""

            for para_idx, para in enumerate(paragraphs):
                if self._is_reference_or_list_paragraph(para):
                    continue
                sentences = [s.strip() for s in _RE_SENTENCE_SPLIT.split(para) if s.strip()]
                if not sentences:
                    continue
                first_para_idx = para_idx
                first_sentence = sentences[0]
                match = re.match(r"^([^、。！？\s]{2,24}?)(?:は|が)", first_sentence)
                if match:
                    candidate = match.group(1).strip()
                    if candidate not in blocked_subjects and re.search(r"[一-龯ァ-ヶA-Za-z]", candidate):
                        subject_phrase = candidate
                break

            if (
                subject_phrase
                and subject_seen.get(subject_phrase, 0) >= 1
                and isinstance(first_para_idx, int)
                and 0 <= first_para_idx < len(paragraphs)
            ):
                sentences = [s.strip() for s in _RE_SENTENCE_SPLIT.split(paragraphs[first_para_idx]) if s.strip()]
                if sentences:
                    updated = re.sub(
                        rf"^{re.escape(subject_phrase)}(?:は|が)",
                        "",
                        sentences[0],
                        count=1,
                    ).lstrip("、, \t")
                    if updated and len(updated) >= 10:
                        sentences[0] = updated
                        paragraphs[first_para_idx] = "".join(sentences).strip()
                        rewritten += 1

            if subject_phrase:
                subject_seen[subject_phrase] = subject_seen.get(subject_phrase, 0) + 1

            merged_content = "\n\n".join(p for p in paragraphs if p.strip()).strip() or content.strip()
            rebuilt_sections.append(f"## {heading}\n\n{merged_content}".strip())

        if rewritten <= 0:
            return body
        logger.info("Subject opening compression applied: rewritten=%s", rewritten)
        return "\n\n".join(block for block in rebuilt_sections if block.strip()).strip()

    @staticmethod
    def _article_generator_legacy_dedupe_similar_headings(body: str) -> str:
        """R20: 見出し間の類似度が高い場合、後方の見出しに差別化マーカーを付与。

        Jaccard類似度 > 0.6 の見出しペアを検知し、後方見出しの末尾語を差し替える。
        """
        lines = body.split("\n")
        heading_indices = [i for i, line in enumerate(lines) if line.strip().startswith("##")]
        if len(heading_indices) < 2:
            return body

        heading_texts = [(i, re.sub(r"^#+\s*", "", lines[i]).strip()) for i in heading_indices]
        suffix_variants = ["の要点", "の視点", "の背景", "の具体策", "の実践"]
        variant_idx = 0

        for a_pos in range(len(heading_texts)):
            for b_pos in range(a_pos + 1, len(heading_texts)):
                idx_a, text_a = heading_texts[a_pos]
                idx_b, text_b = heading_texts[b_pos]
                set_a = set(text_a)
                set_b = set(text_b)
                union = set_a | set_b
                if not union:
                    continue
                jaccard = len(set_a & set_b) / len(union)
                if jaccard > 0.6 and text_a != text_b:
                    # 後方の見出しを差別化
                    prefix = lines[idx_b].split(text_b)[0] if text_b in lines[idx_b] else "## "
                    # 末尾の「〜とは」「〜の実態」等を差し替え
                    core = re.sub(r"(?:とは[？?]?|の実態|のポイント|の要点|の特徴)$", "", text_b).strip()
                    if core and core != text_b:
                        new_suffix = suffix_variants[variant_idx % len(suffix_variants)]
                        variant_idx += 1
                        lines[idx_b] = f"{prefix}{core}{new_suffix}"
                        heading_texts[b_pos] = (idx_b, f"{core}{new_suffix}")

        return "\n".join(lines)

    def _article_generator_legacy_apply_unified_dedupe_pass(self, body: str) -> str:
        """重複除去の実書き換えをこの1パスに集約する。"""
        sample = body or ""
        if not sample:
            return sample
        after_paragraph = self._dedupe_body_repetition(sample)
        after_sentence = self._dedupe_cross_section_sentences(after_paragraph)
        return after_sentence

    def _article_generator_legacy_apply_final_consistency_guards(self, lead: str, body: str) -> Tuple[str, str]:
        """最終段で一貫性と人間らしさのバランスを整える。"""
        lead = (lead or "").strip()
        body = (body or "").strip()

        # R20: 見出し間の類似度チェック（cross-heading dedup）
        body = self._dedupe_similar_headings(body)

        lead, body = self._dedupe_lead_body(lead, body)
        body = self._apply_unified_dedupe_pass(body)
        body = self._reduce_repeated_named_entity_openings(body)
        body = self._compress_repeated_subject_openings(body)
        body = self._normalize_ai_like_heading_labels(body)
        lead = self._reduce_ai_like_openings(lead)
        body = self._reduce_ai_like_openings(body)
        lead = self._reduce_ai_like_endings(lead)
        body = self._reduce_ai_like_endings(body)
        theme_entities = self._extract_theme_entities(
            getattr(self, "_current_title", "") or ""
        )
        lead = self._apply_prodrop_zero_anaphora(lead, theme_entities=theme_entities)
        body = self._apply_prodrop_zero_anaphora(body, theme_entities=theme_entities)
        lead = self._repair_subjectless_openings(lead)
        body = self._repair_subjectless_openings(body)
        lead = self._diversify_overused_phrases(lead)
        body = self._diversify_overused_phrases(body)
        lead = self._clean_redundant_connectives(lead)
        body = self._clean_redundant_connectives(body)
        lead = self._compress_redundant_explanations(lead)
        body = self._compress_redundant_explanations(body)
        body = self._trim_nonclosing_section_tail_summaries(body)
        body = self._strip_heading_top_adversative(body)
        lead = self._soften_assertive_expressions(lead)
        body = self._soften_assertive_expressions(body)

        pronoun = (getattr(self, "_current_pronoun", "") or "").strip()
        if pronoun:
            lead = self._normalize_pronoun_usage(lead, pronoun)
            body = self._normalize_pronoun_usage(body, pronoun)

        if self._has_corporate_stance_anchor_gap(lead, body):
            lead = self._inject_corporate_stance_anchor(lead, body)

        if self._should_enforce_polite_register():
            register_report = self._analyze_style_register(f"{lead}\n\n{body}")
            if register_report.get("mixed"):
                lead = self._normalize_register_to_polite(lead)
                body = self._normalize_register_to_polite(body)
                logger.info(
                    "Final register normalization applied: polite=%s plain=%s ratio=%.3f",
                    register_report.get("polite_count", 0),
                    register_report.get("plain_count", 0),
                    float(register_report.get("minor_ratio", 0.0) or 0.0),
                )

        # 文末制御はシンプルに一本化:
        # 1) 同一終止の連続を最小限崩す 2) 非casualでは口語終助詞を上限で抑える
        lead = self._break_ending_monotony(lead)
        body = self._break_ending_monotony(body)
        if self._get_active_style_profile() != "casual":
            lead = self._cap_colloquial_endings(lead)
            body = self._cap_colloquial_endings(body)

        return lead.strip(), body.strip()

    @staticmethod
    def _is_emphasis_target_line(line: str) -> bool:
        stripped = (line or "").strip()
        if not stripped:
            return False
        if stripped.startswith("## "):
            return False
        if re.match(r"^(?:出典:|参考(?:文献|資料)?[:：]?|[-*]\s+|\d+\.\s+)", stripped):
            return False
        if re.match(r"^https?://", stripped):
            return False
        if "**" in stripped:
            return False
        return 18 <= len(stripped) <= 180

    def _select_emphasis_span(self, line: str) -> Optional[Tuple[int, int]]:
        text = (line or "").strip()
        if not text:
            return None

        numeric_match = re.search(
            r"\d+(?:\.\d+)?(?:%|％|件|人|倍|日|時間|秒|項目|文字|回|社|冊)",
            text,
        )
        if numeric_match:
            return numeric_match.span()

        # 引用符ごと太字化すると貼り付け先によっては `**` が生表示されるため、
        # 強調対象はカギ括弧の内側だけに限定する（「**語句**」形式）。
        quote_match = re.search(r"[「『]([^」』]{2,24})[」』]", text)
        if quote_match:
            return quote_match.span(1)

        keyword_match = re.search(
            r"(重要|要点|結論|ポイント|注意|リスク|必須|有効|対策|防御|根拠|信頼性|最優先|一次情報)",
            text,
        )
        if keyword_match:
            # 強調語は語頭を基点にし、語中（助詞開始など）の太字化を避ける。
            start = keyword_match.start(1)
            end = keyword_match.end(1)
            tail = re.match(r"[一-龥々〆ヵヶぁ-んァ-ヶA-Za-z0-9]{0,8}", text[end:])
            if tail:
                end += len(tail.group(0))
            phrase = text[start:end].strip(" 　、。")
            if 2 <= len(phrase) <= 20:
                return (start, start + len(phrase))
        return None

    def _apply_contextual_bold_emphasis(self, text: str, *, max_items: int) -> str:
        if not text or max_items <= 0:
            return text

        lines = text.splitlines()
        remaining = max_items
        rewritten: List[str] = []
        for raw_line in lines:
            if remaining <= 0:
                rewritten.append(raw_line)
                continue

            stripped = raw_line.strip()
            if not self._is_emphasis_target_line(stripped):
                rewritten.append(raw_line)
                continue

            span = self._select_emphasis_span(stripped)
            if not span:
                rewritten.append(raw_line)
                continue

            start, end = span
            if end <= start or start < 0:
                rewritten.append(raw_line)
                continue

            emphasized = f"{stripped[:start]}**{stripped[start:end]}**{stripped[end:]}"
            indent_len = len(raw_line) - len(raw_line.lstrip())
            indent = raw_line[:indent_len]
            rewritten.append(f"{indent}{emphasized}")
            remaining -= 1

        return "\n".join(rewritten)

    def _apply_note_contextual_emphasis(self, lead: str, body: str) -> Tuple[str, str]:
        emphasized_lead = self._apply_contextual_bold_emphasis(lead, max_items=1)
        emphasized_body = self._apply_contextual_bold_emphasis(body, max_items=2)
        return self._fix_broken_bold(emphasized_lead), self._fix_broken_bold(emphasized_body)

    def _apply_compacted_postprocess_pipeline(
        self,
        lead: str,
        body: str,
        *,
        merged_context: str = "",
        article_type: str = "",
        target_audience: str = "",
    ) -> Tuple[str, str]:
        """Phase05: 後段整形の重複適用を集約する。"""
        original_lead = lead
        original_body = body
        before = f"{lead or ''}\n\n{body or ''}"
        self._last_hard_soft_eval = {
            "enabled": False,
            "mode": "off",
            "hard_failed": False,
            "metrics": {},
            "hard_fail_reasons": [],
            "fallback_reason": "not_evaluated",
        }

        # R14: Markdown太字の片方閉じ忘れを修復
        lead = self._fix_broken_bold(lead)
        body = self._fix_broken_bold(body)

        # R27: 最終一貫性ガード（全体重複・一人称・文末揺らぎ）
        lead, body = self._apply_final_consistency_guards(lead, body)
        lead = self._reduce_target_term_overuse(lead, target_audience=target_audience)
        body = self._reduce_target_term_overuse(body, target_audience=target_audience)

        pre_layout_lead = lead
        pre_layout_body = body

        # 段落/句読点の整形は最終段で1回だけ適用
        lead = self._normalize_paragraphs(lead)
        body = self._normalize_paragraphs(body)
        # note.com 向け: 長段落のみ文単位改行を適用（毎文改行は避ける）
        lead = self._add_note_sentence_linebreaks(lead)
        body = self._add_note_sentence_linebreaks(body)
        lead = self._fix_punctuation(lead)
        body = self._fix_punctuation(body)
        lead = self._repair_contextual_sentence_breaks(lead)
        body = self._repair_contextual_sentence_breaks(body)
        lead = self._clean_redundant_connectives(lead)
        body = self._clean_redundant_connectives(body)
        lead = self._clean_meta_output(lead, target_audience)
        body = self._clean_meta_output(body, target_audience)

        naturalness_report = self._check_contextual_naturalness(f"{lead or ''}\n\n{body or ''}")
        if naturalness_report.get("issue_count", 0) > 0:
            fallback_lead = self._add_note_sentence_linebreaks(
                self._repair_contextual_sentence_breaks(self._fix_punctuation(pre_layout_lead))
            )
            fallback_body = self._add_note_sentence_linebreaks(
                self._repair_contextual_sentence_breaks(self._fix_punctuation(pre_layout_body))
            )
            fallback_lead = self._clean_meta_output(fallback_lead, target_audience)
            fallback_body = self._clean_meta_output(fallback_body, target_audience)
            fallback_report = self._check_contextual_naturalness(f"{fallback_lead or ''}\n\n{fallback_body or ''}")
            if fallback_report.get("issue_count", 0) <= naturalness_report.get("issue_count", 0):
                logger.info(
                    "Contextual naturalness fallback applied: issues %s -> %s",
                    naturalness_report.get("issue_count", 0),
                    fallback_report.get("issue_count", 0),
                )
                lead, body = fallback_lead, fallback_body
                naturalness_report = fallback_report
        if naturalness_report.get("soft_issue_count", 0) > 0:
            soft_fix_lead = self._clean_redundant_connectives(lead)
            soft_fix_body = self._clean_redundant_connectives(body)
            soft_report = self._check_contextual_naturalness(f"{soft_fix_lead or ''}\n\n{soft_fix_body or ''}")
            if soft_report.get("soft_issue_count", 0) < naturalness_report.get("soft_issue_count", 0):
                logger.info(
                    "Contextual naturalness soft-fix applied: soft_issues %s -> %s",
                    naturalness_report.get("soft_issue_count", 0),
                    soft_report.get("soft_issue_count", 0),
                )
                lead, body = soft_fix_lead, soft_fix_body
                naturalness_report = soft_report
        self._last_contextual_naturalness_report = dict(naturalness_report or {})

        after = f"{lead or ''}\n\n{body or ''}"
        before_len = max(1, len(before))
        rewrite_ratio = abs(len(after) - len(before)) / before_len
        logger.info("Postprocess compaction rewrite_ratio=%.4f (before=%s after=%s)", rewrite_ratio, len(before), len(after))

        # PLAN4 sequence contract:
        # detect -> repair_only -> soft warning light fix -> re-eval -> accept/reject
        detect_eval = self._evaluate_hard_soft_thresholds(
            before_lead=original_lead,
            before_body=original_body,
            after_lead=lead,
            after_body=body,
        )
        detect_hard_failed = (
            detect_eval.get("enabled")
            and detect_eval.get("mode") == "enforce"
            and detect_eval.get("hard_failed")
        )
        if detect_hard_failed:
            metrics = detect_eval.get("metrics", {})
            logger.info(
                "Postprocess hard gate detected before repair_only: %s | "
                "rewrite_ratio=%.4f heading_delta=%s grammar_per_1k=%.4f "
                "unpredictability=%.4f flat_zones=%s semantic_issues=%s",
                "; ".join(detect_eval.get("hard_fail_reasons", []) or ["unknown"]),
                float(metrics.get("rewrite_ratio", 0)),
                metrics.get("heading_delta", 0),
                float(metrics.get("grammar_per_1k", 0)),
                float(metrics.get("unpredictability", 0)),
                metrics.get("flat_zone_count", 0),
                metrics.get("semantic_issue_count", 0),
            )

        # P0-2: 文法のみ最小修復（設定で段階導入）
        lead, body = self._run_repair_only_pass(
            lead,
            body,
            merged_context=merged_context,
            article_type=article_type,
            target_audience=target_audience,
        )
        post_repair_eval = self._evaluate_hard_soft_thresholds(
            before_lead=original_lead,
            before_body=original_body,
            after_lead=lead,
            after_body=body,
        )
        try:
            soft_fix_result = self._try_soft_warning_fix_pass(
                before_lead=original_lead,
                before_body=original_body,
                current_lead=lead,
                current_body=body,
                current_eval=post_repair_eval,
            )
        except Exception as exc:
            logger.info(
                "soft warning fix pass failed. Keep post-repair text. (%s: %s)",
                type(exc).__name__,
                exc,
            )
            soft_fix_result = None
        if soft_fix_result is not None:
            lead, body, _ = soft_fix_result
        lead = self._clean_meta_output(lead, target_audience)
        body = self._clean_meta_output(body, target_audience)

        hard_soft_eval = self._evaluate_hard_soft_thresholds(
            before_lead=original_lead,
            before_body=original_body,
            after_lead=lead,
            after_body=body,
        )
        logger.debug("Setting _last_hard_soft_eval mode=%s", hard_soft_eval.get("mode", "off"))
        self._last_hard_soft_eval = hard_soft_eval
        if (
            hard_soft_eval.get("enabled")
            and hard_soft_eval.get("mode") == "enforce"
            and hard_soft_eval.get("hard_failed")
        ):
            metrics = hard_soft_eval.get("metrics", {})
            logger.info(
                "Postprocess hard guard enforce detected (fail-closed by UI): %s | "
                "rewrite_ratio=%.4f heading_delta=%s grammar_per_1k=%.4f "
                "unpredictability=%.4f flat_zones=%s semantic_issues=%s",
                "; ".join(hard_soft_eval.get("hard_fail_reasons", []) or ["unknown"]),
                float(metrics.get("rewrite_ratio", 0)),
                metrics.get("heading_delta", 0),
                float(metrics.get("grammar_per_1k", 0)),
                float(metrics.get("unpredictability", 0)),
                metrics.get("flat_zone_count", 0),
                metrics.get("semantic_issue_count", 0),
            )
            return lead, body

        return lead, body



    def _merge_contexts(self, contexts: List[FetchedContent]) -> str:
        if not contexts:
            return ""
        source_cfg = self._get_source_reading_config()
        max_chars_per_source = int(source_cfg.get("max_chars_per_source", 12000) or 12000)
        merged = []
        for i, ctx in enumerate(contexts, 1):
            title = ctx.title or f"参考{i}"
            content = (ctx.content or "")[:max_chars_per_source]
            merged.append(f"■{title}\n{content}")
        return "\n\n---\n\n".join(merged)

    def _article_generator_distribute_quotes(self, quote_candidates: List[str], total_sections: int) -> List[List[str]]:
        """引用候補をラウンドロビンで各セクションに配分する。"""
        if not quote_candidates or total_sections <= 0:
            return [[] for _ in range(max(1, total_sections))]
        buckets: List[List[str]] = [[] for _ in range(total_sections)]
        for i, q in enumerate(quote_candidates):
            buckets[i % total_sections].append(q)
        return buckets


    def _article_generator_prepare_section_opening_sequence(self, section_count: int) -> None:
        if section_count <= 0:
            self._section_opening_sequence = []
            return
        focus = self._get_effective_writing_focus()
        hints = list(SECTION_OPENING_HINTS.get(focus, SECTION_OPENING_HINTS["auto"]))
        if not hints:
            self._section_opening_sequence = ["論点提示から入る"] * section_count
            return

        seed_text = (
            f"{focus}|{getattr(self, '_current_type', '')}|"
            f"{getattr(self, '_opening_variation_nonce', 0)}|{section_count}"
        )
        seed = sum(ord(ch) for ch in seed_text)
        rng = random.Random(seed)
        rng.shuffle(hints)

        sequence: List[str] = []
        while len(sequence) < section_count:
            cycle = list(hints)
            rng.shuffle(cycle)
            if sequence and cycle and sequence[-1] == cycle[0] and len(cycle) > 1:
                cycle = cycle[1:] + cycle[:1]
            sequence.extend(cycle)
        self._section_opening_sequence = sequence[:section_count]

    def _kanji_to_int(self, kanji: str) -> Optional[int]:
        mapping = {
            "一": 1,
            "二": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
            "十": 10,
        }
        return mapping.get(kanji)

    def _count_numbered_value_sections(self, outline: List[Dict[str, str]]) -> int:
        count = 0
        for section in outline:
            heading = section.get("heading", "")
            if not heading:
                continue
            if not re.search(r"(価値|理由|ポイント|メリット|効果)", heading):
                continue
            if re.search(r"(\d+|[一二三四五六七八九十])", heading):
                count += 1
        return count

    def _enforce_numbered_outline(
        self,
        outline: List[Dict[str, str]],
        title: str,
        user_prompt: str,
        merged_context: str,
        article_type: str,
        target_audience: str,
        required_items: Optional[int],
    ) -> List[Dict[str, str]]:
        """タイトルの数とアウトラインの整合性を保証する。"""
        if not required_items:
            return outline
        if self._count_numbered_value_sections(outline) >= required_items:
            return outline

        # 厳密条件でアウトラインを再生成
        strict_outline = self._generate_outline_with_requirements(
            merged=merged_context,
            user_prompt=user_prompt,
            article_type=article_type,
            target_audience=target_audience,
            title=title,
            required_items=required_items,
        )
        if self._count_numbered_value_sections(strict_outline) >= required_items:
            return strict_outline

        # 最終フォールバック: 既存の見出しを番号付きにして整合性を担保
        adjusted = []
        value_index = 1
        label = None
        if title:
            if "価値" in title:
                label = "価値"
            elif "理由" in title:
                label = "理由"
            elif "ポイント" in title:
                label = "ポイント"
            elif "メリット" in title:
                label = "メリット"

        for section in outline:
            heading = section.get("heading", "")
            if value_index <= required_items and heading and "##" not in heading:
                section = dict(section)
                if label:
                    section["heading"] = f"{label}{value_index}: {heading}"
                else:
                    section["heading"] = f"{value_index}. {heading}"
                value_index += 1
            adjusted.append(section)

        if value_index > 1:
            return adjusted
        return outline

    # -- Editor consistency condition --

    def _has_pronoun_conflict(self, text: str) -> bool:
        pronoun = (getattr(self, "_current_pronoun", "") or "").strip()
        if not text or not pronoun:
            return False
        alt_pronouns = {
            "私": ["僕", "俺", "私たち", "当社", "弊社"],
            "わたし": ["私", "僕", "俺", "私たち", "当社", "弊社"],
            "私たち": ["私", "わたし", "僕", "俺"],
            "僕": ["私", "わたし", "私たち", "俺"],
            "当社": ["私", "わたし", "僕", "俺"],
            "弊社": ["私", "わたし", "僕", "俺"],
        }
        alts = alt_pronouns.get(pronoun, [])
        return any(alt in text for alt in alts)

    def _article_generator_editor_consistency_signals(self, lead: str, body: str) -> Dict[str, bool]:
        combined = f"{lead}\n\n{body}" if (lead or body) else ""
        if not combined:
            return {
                "missing_intro": False,
                "missing_closing": False,
                "duplicate_openings": False,
                "pronoun_conflict": False,
                "style_mixed": False,
                "stance_anchor_missing": False,
            }

        headings = re.findall(r"^##\s+(.+)$", combined, re.MULTILINE)
        content_headings = [
            h for h in headings if not re.search(r"(参考資料|参考文献|出典)", h, re.IGNORECASE)
        ]
        closing_pattern = (
            r"(まとめ|結論|おわり|最後に|要点|次の一歩|一歩|行動|これから|未来|"
            r"判断ポイント|実務ポイント|チェックリスト)"
        )
        intro_pattern = r"(はじめに|導入|背景|概要|問題提起|課題|出発点|きっかけ)"
        has_intro = any(
            re.search(intro_pattern, h, re.IGNORECASE) for h in content_headings[:2]
        ) if content_headings else False
        missing_intro = len(content_headings) >= 3 and not has_intro
        has_closing = any(
            re.search(closing_pattern, h, re.IGNORECASE) for h in content_headings[-2:]
        ) if content_headings else False
        missing_closing = len(content_headings) >= 3 and not has_closing

        duplicate_openings = False
        section_openings: List[str] = []
        for match in re.finditer(r"^##\s+.+\n+(.*?)(?=\n|$)", combined, re.MULTILINE):
            first_line = match.group(1).strip()
            if first_line:
                section_openings.append(re.sub(r"\s+", "", first_line)[:30])
        if len(section_openings) >= 3:
            for i in range(len(section_openings) - 1):
                for j in range(i + 1, len(section_openings)):
                    ratio = SequenceMatcher(None, section_openings[i], section_openings[j]).ratio()
                    if ratio >= 0.75:
                        duplicate_openings = True
                        break
                if duplicate_openings:
                    break

        pronoun_conflict = self._has_pronoun_conflict(combined)
        register_report = self._analyze_style_register(combined)
        style_mixed = bool(register_report.get("mixed"))
        stance_anchor_missing = self._has_corporate_stance_anchor_gap(lead, body)
        return {
            "missing_intro": missing_intro,
            "missing_closing": missing_closing,
            "duplicate_openings": duplicate_openings,
            "pronoun_conflict": pronoun_conflict,
            "style_mixed": style_mixed,
            "stance_anchor_missing": stance_anchor_missing,
        }

    def _article_generator_should_run_editor_consistency(self, lead: str, body: str) -> bool:
        """Run editor consistency only when structural issues are detected."""
        signals = self._editor_consistency_signals(lead, body)
        return any(signals.values())

    def _article_generator_run_editor_consistency_pass(
        self,
        lead: str,
        body: str,
        *,
        merged_context: str,
        article_type: str,
        target_audience: str,
        review_points: Optional[List[str]] = None,
        readability_focus: bool = False,
    ) -> Tuple[str, str]:
        """全体を一度だけ整合チェックし、並列生成由来の齟齬を吸収する。"""
        if not lead and not body:
            return lead, body

        self._editor_consistency_failed = False
        writing_focus_guide = self._get_writing_focus_guide()
        editor_persona_block = self._build_editor_persona_block(
            pass_type="editor_consistency",
            article_type=article_type,
        )
        review_text = " / ".join((review_points or [])[:3]) if review_points else "なし"
        readability_extra = ""
        if readability_focus:
            readability_extra = """
8. review_points に段落過密/文体混在/導入句反復がある場合、最小限で可読性を補正する
9. 不必要な要約・圧縮を避け、情報量と具体性を維持する"""
        prompt = f"""
あなたは編集者です。以下の lead/body を最小限だけ調整してください。
{editor_persona_block}

【最優先】
- 人間らしい語り口・感情の揺らぎ・読みやすさは維持する
- 一人称は「{self._current_pronoun}」を維持する
- 文体を硬くしすぎない
- セクションごとの文体の違い（語彙の難易度、文の複雑さ、勢い）は意図的な設計なので均一化しない
- 人間の記事は冒頭と中盤と終盤でテンションが違うのが自然。その揺らぎを保つ

【チェック観点】
1. セクション間の矛盾（結論の食い違い、時系列矛盾、重複）を解消する
2. 文法の不自然さ（助詞、係り受け、主語述語）だけ最小限で直す
3. 参考情報にない数字/固有名詞の断定を弱める（必要なら抽象化）
4. タイトルとターゲット読者への整合を保つ
5. 導入の定型反復（「〜ありませんか？」「〜だと思っていたんですが」）を避ける
6. まったく同じ結論を繰り返している段落のみ統合する
7. 「補足」「FAQ」「注意点」など補助セクションは、導入直後ではなく中盤以降に配置する
{readability_extra}

【禁止】
- セクション間で語彙レベルや文の長さを統一しようとすること
- あるセクションの文体を別セクションに合わせて書き換えること

【記事タイプ】
{ARTICLE_TYPE_LABELS.get(article_type, article_type)}

【ターゲット読者】
{target_audience}

【本文の重心】
{writing_focus_guide or "自動判定"}

【要修正ポイント（該当時のみ）】
{review_text}

【参考情報（抜粋）】
{merged_context[:EDITOR_CONSISTENCY_CONTEXT_LIMIT] if merged_context else "なし"}

【入力（そのまま保持したい本文）】
[LEAD]
{lead}

[BODY]
{body}

【出力形式】
JSONのみ:
{{"lead": "...", "body": "..."}}
        """.strip()

        max_tokens = min(5200, max(1300, int((len(lead) + len(body)) * 1.1)))
        guard_rejected = False
        last_failure_reason = ""
        for attempt in range(1, EDITOR_CONSISTENCY_MAX_RETRIES + 1):
            try:
                raw = self.llm.generate_text(
                    prompt,
                    max_tokens=max_tokens,
                    task_type="editor_consistency",
                ).strip()
            except Exception as exc:
                logger.debug(
                    "Editor consistency pass failed (attempt %s/%s).",
                    attempt,
                    EDITOR_CONSISTENCY_MAX_RETRIES,
                    exc_info=exc,
                )
                last_failure_reason = f"llm_error:{type(exc).__name__}:{exc}"
                continue

            try:
                match = re.search(r"\{.*\}", raw, re.S)
                if not match:
                    logger.debug(
                        "Editor consistency JSON block missing (attempt %s/%s).",
                        attempt,
                        EDITOR_CONSISTENCY_MAX_RETRIES,
                    )
                    last_failure_reason = "json_block_missing"
                    continue
                data = json.loads(match.group(0))
                new_lead = data.get("lead")
                new_body = data.get("body")
                if isinstance(new_lead, str) and isinstance(new_body, str):
                    resolved_lead = new_lead.strip() or lead
                    resolved_body = new_body.strip() or body
                    rejection = self._rewrite_guard_check(
                        lead, body, resolved_lead, resolved_body,
                        max_rewrite_ratio=0.24,
                        label="editor_consistency",
                    )
                    if rejection:
                        guard_rejected = True
                        logger.info("%s (attempt %s/%s).", rejection, attempt, EDITOR_CONSISTENCY_MAX_RETRIES)
                        continue
                    return resolved_lead, resolved_body
                logger.debug(
                    "Editor consistency payload invalid (attempt %s/%s).",
                    attempt,
                    EDITOR_CONSISTENCY_MAX_RETRIES,
                )
                last_failure_reason = "payload_invalid"
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.debug(
                    "Failed to parse editor consistency JSON (attempt %s/%s).",
                    attempt,
                    EDITOR_CONSISTENCY_MAX_RETRIES,
                    exc_info=exc,
                )
                last_failure_reason = f"json_parse_error:{type(exc).__name__}:{exc}"

        if guard_rejected:
            logger.info("Editor consistency skipped due to aggressive rewrite guard.")
            self._editor_consistency_failed = False
            return lead, body
        logger.warning(
            "Editor consistency all retries failed (%s/%s). Keep original text. reason=%s",
            EDITOR_CONSISTENCY_MAX_RETRIES,
            EDITOR_CONSISTENCY_MAX_RETRIES,
            last_failure_reason or "unknown",
        )
        self._editor_consistency_failed = True
        return lead, body

    def _article_generator_run_post_generation_polish_pass(
        self,
        lead: str,
        body: str,
        *,
        merged_context: str,
        article_type: str,
        target_audience: str,
        review_points: List[str],
    ) -> Tuple[str, str]:
        """後段の整合/可読性処理を必要時だけ実行する。"""
        signals = self._editor_consistency_signals(lead, body)
        needs_editor = self._should_run_editor_consistency(lead, body)
        needs_readability = self._should_run_readability_polish(review_points, body=body)

        # 長文・多見出しで「重複導入/可読性」だけが課題の場合は、
        # 後段LLM再編集でAI的に均される副作用を避け、規則ベース最終ガードへ委譲する。
        long_multisection = self._heading_count(body) >= 4 and len((body or "").strip()) >= 1600
        hard_consistency_risk = (
            bool(signals.get("missing_intro"))
            or bool(signals.get("missing_closing"))
            or bool(signals.get("pronoun_conflict"))
            or bool(signals.get("style_mixed"))
            or bool(signals.get("stance_anchor_missing"))
        )
        if long_multisection and not hard_consistency_risk and (bool(signals.get("duplicate_openings")) or needs_readability):
            logger.info(
                "Post polish skipped for long multi-section body to preserve voice (dup_openings=%s readability=%s).",
                bool(signals.get("duplicate_openings")),
                needs_readability,
            )
            self._editor_consistency_failed = False
            return lead, body

        if not needs_editor and not needs_readability:
            logger.info("Post polish skipped: no structural/readability issues detected.")
            self._editor_consistency_failed = False
            return lead, body

        if needs_editor and needs_readability:
            logger.info("Post polish: running combined editor+readability pass.")
            return self._run_editor_consistency_pass(
                lead,
                body,
                merged_context=merged_context,
                article_type=article_type,
                target_audience=target_audience,
                review_points=review_points,
                readability_focus=True,
            )

        if needs_editor:
            logger.info("Post polish: running editor consistency pass.")
            return self._run_editor_consistency_pass(
                lead,
                body,
                merged_context=merged_context,
                article_type=article_type,
                target_audience=target_audience,
            )

        logger.info("Post polish: running readability polish pass.")
        self._editor_consistency_failed = False
        return self._run_readability_polish_pass(
            lead,
            body,
            merged_context=merged_context,
            article_type=article_type,
            target_audience=target_audience,
            review_points=review_points,
        )

    def _article_generator_should_run_readability_polish(self, review_points: List[str], *, body: str = "") -> bool:
        if not review_points:
            return False
        high_impact_triggers = (
            "段落が長く論点が混在",
            "文体混在",
            "導入句の反復",
            "見出し順の一貫性不足",
            "結論見出しが早すぎる",
            "断定的な結果・保証表現",
        )
        trigger_hits = sum(
            1
            for point in review_points
            if any(trigger in point for trigger in high_impact_triggers)
        )
        heading_flow_risk = any("見出し順の一貫性不足" in point for point in review_points)
        required_hits = 1 if heading_flow_risk else 2
        if trigger_hits < required_hits:
            return False

        normalized_body = (body or "").strip()
        if len(normalized_body) < 1200:
            return False
        if self._heading_count(normalized_body) < 2:
            return False

        return True

    def _article_generator_run_readability_polish_pass(
        self,
        lead: str,
        body: str,
        *,
        merged_context: str,
        article_type: str,
        target_audience: str,
        review_points: List[str],
    ) -> Tuple[str, str]:
        if not lead and not body:
            return lead, body
        if not self._should_run_readability_polish(review_points, body=body):
            return lead, body

        writing_focus_guide = self._get_writing_focus_guide()
        editor_persona_block = self._build_editor_persona_block(
            pass_type="readability_polish",
            article_type=article_type,
        )
        review_text = " / ".join(review_points[:3]) if review_points else "なし"
        prompt = f"""
あなたは日本語編集者です。以下の lead/body を最小限だけ整えてください。
{editor_persona_block}

【目的】
- 読みやすさを上げる（段落過密・文体混在・不自然なつなぎの是正）
- 人間らしい語り口と主旨は維持する

【記事タイプ】
{ARTICLE_TYPE_LABELS.get(article_type, article_type)}

【ターゲット読者】
{target_audience}

【本文の重心】
{writing_focus_guide or "自動判定"}

【要修正ポイント】
{review_text}

【参考情報（抜粋）】
{merged_context[:READABILITY_POLISH_CONTEXT_LIMIT] if merged_context else "なし"}

【厳守ルール】
1. 事実・数値・固有名詞・見出しは勝手に追加しない。
2. 見出し構成は維持。順序変更は「結論が極端に早い場合」のみ最小限で許可。
3. 長い段落は意味単位で分割し、1段落1トピックを優先する。
4. 文体は原文の会話調・語り口の揺らぎをそのまま保持する。セクションごとのテンション差は意図的な設計。
5. 内容の削除は最小限。要約しすぎない。

【入力】
[LEAD]
{lead}

[BODY]
{body}

【出力形式】
JSONのみ:
{{"lead": "...", "body": "..."}}
""".strip()
        max_tokens = min(4600, max(1200, int((len(lead) + len(body)) * 1.05)))
        try:
            raw = self.llm.generate_text(
                prompt,
                max_tokens=max_tokens,
                task_type="readability_polish",
            ).strip()
        except Exception as exc:
            logger.warning(
                "Readability polish pass failed. Keep original text. (%s: %s)",
                type(exc).__name__,
                exc,
            )
            return lead, body

        if not raw:
            return lead, body
        try:
            match = re.search(r"\{.*\}", raw, re.S)
            if not match:
                logger.warning("Readability polish response missing JSON block. Keep original text.")
                return lead, body
            data = json.loads(match.group(0))
            new_lead = data.get("lead")
            new_body = data.get("body")
            if isinstance(new_lead, str) and isinstance(new_body, str):
                polished_lead = new_lead.strip() or lead
                polished_body = new_body.strip() or body
                if len(polished_body) < max(120, int(len(body) * 0.55)):
                    return lead, body
                rejection = self._rewrite_guard_check(
                    lead, body, polished_lead, polished_body,
                    max_rewrite_ratio=READABILITY_POLISH_MAX_REWRITE_RATIO,
                    label="readability_polish",
                )
                if rejection:
                    logger.info("%s", rejection)
                    return lead, body
                return polished_lead, polished_body
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning(
                "Readability polish JSON parse failed. Keep original text. (%s: %s)",
                type(exc).__name__,
                exc,
            )
        return lead, body

    def _should_use_llm_editor_in_resonance(self, text: str, platform: str, enabled_in_config: bool) -> bool:
        if not enabled_in_config:
            return False
        if not text:
            return False
        if platform != "note":
            return False

        heading_count = self._heading_count(text)
        drift_enabled = bool((getattr(self, "_cognitive_drift_config", {}) or {}).get("enabled", False))
        # 長文・多見出しの完成本文は、LLM文法磨きで文体が均されやすいため抑制する。
        if drift_enabled and heading_count >= 6 and len(text) >= 3000:
            return False
        # 短いテキスト（CTA/ハッシュタグ等）はスキップ
        if heading_count == 0 and len(text) < 200:
            return False
        # 本文セクション（見出し付き or 300文字以上）は積極的に有効化
        if heading_count >= 1 or len(text) >= 300:
            return True

        review_points = self._collect_review_points(text)
        if any(
            any(keyword in point for keyword in ("段落が長く論点が混在", "文体混在", "導入句の反復"))
            for point in review_points
        ):
            return True

        pronoun = getattr(self, "_current_pronoun", None)
        if pronoun:
            alt_pronouns = {"私": ["僕", "俺", "弊社"], "私たち": ["我々", "弊社"], "僕": ["私", "俺"]}
            alts = alt_pronouns.get(pronoun, [])
            if any(alt in text for alt in alts):
                return True
        return False

    def _should_use_llm_legal_in_resonance(self, text: str, platform: str, enabled_in_config: bool) -> bool:
        if not enabled_in_config:
            return False
        if not text:
            return False
        if platform != "note":
            return False

        heading_count = self._heading_count(text)
        # 長文本文はregexプレチェックを優先し、必要時のみ生成側の法務整合へ委ねる。
        if heading_count >= 4 and len(text) >= 1500:
            return False

        policy = getattr(self, "_pipeline_policy", {}) or {}
        evidence_mode = str(policy.get("evidence_mode", "normal")).lower()
        if evidence_mode == "strict":
            return True

        numeric_claims = len(
            re.findall(r"\d+(?:[.,]\d+)?(?:%|％|倍|件|年|月|日|人|社|回|円|万|億)", text)
        )
        if numeric_claims >= 3:
            return True

        legal_risk_patterns = [
            r"(No\.?1|ナンバーワン|世界一|日本一|唯一無二|最強|最高|最安|限定|今だけ)",
            r"(絶対|必ず|確実に|100%)",
            r"(治る|治療効果|痩せる|美白効果|効能)",
            r"(他社|競合).{0,10}より.{0,12}(優れ|高性能|高機能)",
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in legal_risk_patterns):
            return True
        return False

    def _apply_resonance(
        self,
        text: str,
        platform: str,
        perspective: str,
        source_text: Optional[str] = None,
    ) -> str:
        """Apply Human Resonance phases without platform formatting (single-source CTA/hashtags)."""
        hr_config = get_human_resonance_config()
        policy = getattr(self, "_pipeline_policy", {}) or {}
        focus = str(policy.get("focus") or self._get_effective_writing_focus())
        style_profile = str(
            policy.get("style_profile")
            or {
                "analysis": "formal",
                "experience": "casual",
                "explanation": "balanced",
            }.get(focus, "balanced")
        )
        use_llm_for_editor = self._should_use_llm_editor_in_resonance(
            text,
            platform,
            bool(hr_config["use_llm_for_editor"]),
        )
        use_llm_for_legal = self._should_use_llm_legal_in_resonance(
            text,
            platform,
            bool(hr_config["use_llm_for_legal"]),
        )
        if bool(hr_config["use_llm_for_editor"]) and not use_llm_for_editor:
            logger.info(
                "Resonance editor LLM step skipped to preserve section drift (platform=%s headings=%s chars=%s).",
                platform,
                self._heading_count(text),
                len(text or ""),
            )
        if bool(hr_config["use_llm_for_legal"]) and not use_llm_for_legal:
            logger.info(
                "Resonance legal LLM step skipped for long-form stability (platform=%s headings=%s chars=%s).",
                platform,
                self._heading_count(text),
                len(text or ""),
            )
        _resonance_scale = 1.0
        config = PipelineConfig(
            platform=platform,
            style_profile=style_profile,
            enable_platform=False,
            enable_empathy=True,
            enable_curiosity=True,
            enable_humanity=True,
            enable_rhythm=True,
            empathy_target=float(policy.get("empathy_target", HUMAN_FIRST_CONFIG["empathy_target"])) * _resonance_scale,
            curiosity_target=float(policy.get("curiosity_target", HUMAN_FIRST_CONFIG["curiosity_target"])) * _resonance_scale,
            humanity_target=float(policy.get("humanity_target", HUMAN_FIRST_CONFIG["humanity_target"])) * _resonance_scale,
            rhythm_target=float(policy.get("rhythm_target", HUMAN_FIRST_CONFIG["rhythm_target"])),
            humanity_intensity=HUMAN_FIRST_CONFIG["humanity_intensity"] * _resonance_scale,
            phrase_max_per_paragraph=hr_config["phrase_max_per_paragraph"],
            phrase_probability=hr_config["phrase_probability"],
            phrase_min_occurrences=hr_config["phrase_min_occurrences"],
            pronoun_reduction_ratio=float(policy.get("pronoun_reduction_ratio", hr_config["pronoun_reduction_ratio"])),
            pronoun_reduction_min_count=hr_config["pronoun_reduction_min_count"],
            use_llm_for_editor=use_llm_for_editor,
            use_llm_for_legal=use_llm_for_legal,
            enable_editor=True,
            enable_legal=True,
            enable_sanitize=True,
        )
        pipeline = HumanResonancePipeline(config=config, llm_client=self.llm)

        # 基本文体は個人の語り口を維持しつつ、一人称のみ反映
        perspective_key = self._normalize_perspective_key(perspective)
        defaults = PERSPECTIVE_DEFAULTS.get(perspective_key, PERSPECTIVE_DEFAULTS.get("blogger", {}))
        verbal_tics = defaults.get("verbal_tics", []).copy()
        tone = defaults.get("tone", "polite")
        emotionality = defaults.get("emotionality", 0.5)

        if focus == "analysis":
            # 分析記事では口癖注入を止め、定型句の増殖を抑える。
            verbal_tics = []
            tone = "formal"
            emotionality = min(emotionality, 0.45)
        elif focus == "experience":
            if tone == "formal":
                tone = "polite"
            emotionality = max(emotionality, 0.6)
        elif focus == "explanation":
            # 解説記事でも口癖注入を抑えて、前置きのテンプレ化を避ける。
            verbal_tics = []
            if tone == "casual":
                tone = "polite"
            emotionality = min(max(emotionality, 0.45), 0.6)

        persona = Persona(
            pronoun=self._current_pronoun,
            verbal_tics=verbal_tics,
            perspective=perspective_key,
            tone=tone,
            emotionality=emotionality,
        )

        resonance_result = pipeline.process(
            text,
            persona=persona,
            perspective=perspective_key,
            source_text=source_text,
        )
        resonance_text = resonance_result.text
        # R1: 計測結果をインスタンスに保存（pipeline_checkへ転記用）
        self._last_resonance_phase_effect_metrics = dict(resonance_result.phase_effect_metrics)
        return self._apply_quality_pipeline(
            resonance_text,
            platform=platform,
            perspective=perspective_key,
            focus=focus,
            source_text=source_text,
        )

    def _apply_quality_pipeline(
        self,
        text: str,
        platform: str,
        perspective: str,
        focus: str,
        source_text: Optional[str] = None,
    ) -> str:
        quality_config = get_quality_pipeline_config()
        if not text:
            return ""
        if not quality_config.enabled or quality_config.mode == "off":
            return text

        # R6-T10: fast path for announcements (skip post-processing)
        current_type = getattr(self, "_current_type", "")
        if current_type in ("④お知らせ", "お知らせ", "announcement"):
            logger.info("Announcement fast-path: skipping quality pipeline post-processing")
            return text

        try:
            runner = QualityPipelineRunner(config=quality_config)
            quality_context = self._build_quality_context(
                platform=platform,
                perspective=perspective,
                focus=focus,
                source_text=source_text,
            )
            quality_result = runner.process(text, context=quality_context)
        except Exception as exc:
            if quality_config.fail_open:
                logger.warning("Quality pipeline failed in fail-open mode: %s", exc)
                self._quality_phase_reports.append(
                    {
                        "platform": platform,
                        "mode": quality_config.mode,
                        "errors": [str(exc)],
                        "phase_reports": [],
                        "mode_resolution": {},
                    }
                )
                return text
            raise

        self._quality_phase_reports.append(
            {
                "platform": platform,
                "mode": quality_config.mode,
                "errors": quality_result.errors,
                "phase_reports": quality_result.phase_reports,
                "applied": quality_result.applied,
                "mode_resolution": dict(getattr(quality_result, "mode_resolution", {}) or {}),
            }
        )
        if quality_result.errors:
            logger.warning("Quality pipeline reported errors: %s", "; ".join(quality_result.errors))
        return quality_result.text

    def _build_pipeline_check(
        self,
        platform: str,
        *,
        post_pipeline_skipped: bool = False,
        skip_reason: str = "",
    ) -> Dict[str, Any]:
        policy = getattr(self, "_pipeline_policy", {}) or {}
        category_policy = getattr(self, "_category_policy", {}) or {}
        snapshots = getattr(self, "_editor_persona_snapshots", {}) or {}
        editor_persona_profiles: Dict[str, Dict[str, str]] = {}
        if isinstance(snapshots, dict):
            for pass_type, profile in snapshots.items():
                if not isinstance(profile, dict):
                    continue
                editor_persona_profiles[str(pass_type)] = {
                    "profile_key": str(profile.get("profile_key", "") or ""),
                    "role": str(profile.get("role", "") or ""),
                    "mission": str(profile.get("pass_mission", "") or ""),
                }
        section_cfg = self._get_section_generation_config()
        novelty_cfg = section_cfg.get("novelty_gate", {}) if isinstance(section_cfg, dict) else {}
        overlap_cfg = section_cfg.get("context_overlap", {}) if isinstance(section_cfg, dict) else {}
        hard_soft_cfg = section_cfg.get("hard_soft_thresholds", {}) if isinstance(section_cfg, dict) else {}
        semantic_dedupe_cfg = dict(getattr(self, "_semantic_dedupe_config", {}) or {})
        if not semantic_dedupe_cfg:
            semantic_dedupe_cfg = get_semantic_dedupe_config()
        post_cfg = self._get_postprocess_config()
        repair_cfg = post_cfg.get("repair_only", {}) if isinstance(post_cfg, dict) else {}
        runtime_input = dict(getattr(self, "_runtime_input_contract", {}) or {})
        resolved_contract = dict(getattr(self, "_last_zero_base_contract", {}) or {})
        runtime_article_type = str(
            runtime_input.get("article_type")
            or getattr(self, "_current_type", "")
            or ""
        ).strip().lower()
        runtime_media = str(runtime_input.get("media", "") or platform or "note").strip().lower() or "note"
        style_compact_seed = runtime_input.get("style_compact_for_seo")
        if isinstance(style_compact_seed, bool):
            style_compact_for_seo = style_compact_seed
        else:
            style_compact_for_seo = bool(runtime_article_type == "daily_story" and runtime_media == "seo")
        return {
            "platform": platform,
            "generation_dispatch": dict(getattr(self, "_last_generation_dispatch", {}) or {}),
            "phases_expected": [
                "contract_resolve",
                "discourse_plan",
                "section_generation",
                "coherence_dedupe",
                "minimal_postprocess",
                "quality_gate",
                "output_telemetry",
            ],
            "phase8_platform_in_generate": False,
            "input_contract": {
                "source_inputs": list(runtime_input.get("source_inputs", []))
                if isinstance(runtime_input.get("source_inputs"), list)
                else [],
                "article_type": str(
                    runtime_input.get("article_type")
                    or getattr(self, "_current_type", "")
                    or ""
                ),
                "media": runtime_media,
                "style_compact_for_seo": bool(style_compact_for_seo),
                "question_mode": str(runtime_input.get("question_mode", "") or ""),
                "contract_version": str(runtime_input.get("contract_version", "") or ""),
                "content_goal": str(runtime_input.get("content_goal", "") or "auto"),
                "writing_focus": str(runtime_input.get("writing_focus", "") or self._get_effective_writing_focus()),
                "structure": str(
                    runtime_input.get("structure", "")
                    or getattr(self, "_psychology_structure", "")
                    or "auto"
                ),
                "length_mode_requested": str(runtime_input.get("length_mode_requested", "") or ""),
                "length_mode": str(runtime_input.get("length_mode", "") or self._length_mode),
                "category_base_template": str(category_policy.get("base_template", "") or ""),
                "category_policy_source": str(category_policy.get("source", "") or ""),
                "focus": policy.get("focus", self._get_effective_writing_focus()),
                "evidence_mode": policy.get("evidence_mode", "normal"),
                "perspective": str(runtime_input.get("perspective", "") or self._current_perspective),
                "article_viewpoint": str(
                    runtime_input.get("article_viewpoint")
                    or resolved_contract.get("article_viewpoint")
                    or runtime_input.get("perspective")
                    or self._current_perspective
                    or "auto"
                ),
                "tone_profile": str(
                    runtime_input.get("tone_profile")
                    or policy.get("tone_profile", "")
                    or getattr(self, "_effective_tone_profile", "auto")
                ),
                "allow_experience": bool(runtime_input.get("allow_experience", getattr(self, "_allow_experience", False))),
                "interview_answers": dict(runtime_input.get("interview_answers", {}))
                if isinstance(runtime_input.get("interview_answers"), dict)
                else {},
                "speaker_profile": str(
                    runtime_input.get("speaker_profile")
                    or resolved_contract.get("speaker_profile")
                    or ""
                ),
                "audience_profile": str(
                    runtime_input.get("audience_profile")
                    or resolved_contract.get("audience_profile")
                    or ""
                ),
                "writer_role": str(
                    runtime_input.get("writer_role")
                    or resolved_contract.get("writer_role")
                    or ""
                ),
                "topic_statement": str(
                    runtime_input.get("topic_statement")
                    or resolved_contract.get("topic_statement")
                    or ""
                ),
                "relationship_mode": str(
                    runtime_input.get("relationship_mode")
                    or resolved_contract.get("relationship_mode")
                    or ""
                ),
                "register_policy": self._normalize_register_policy(
                    runtime_input.get("register_policy") or resolved_contract.get("register_policy")
                ),
                "style_profile": self._get_active_style_profile(),
                "discourse_plan_version": str(resolved_contract.get("discourse_plan_version", "") or ""),
                "natural_style_profile": dict(resolved_contract.get("natural_style_profile", {}) or {}),
            },
            "targets": {
                "empathy_target": policy.get("empathy_target", HUMAN_FIRST_CONFIG["empathy_target"]),
                "curiosity_target": policy.get("curiosity_target", HUMAN_FIRST_CONFIG["curiosity_target"]),
                "humanity_target": policy.get("humanity_target", HUMAN_FIRST_CONFIG["humanity_target"]),
                "rhythm_target": policy.get("rhythm_target", HUMAN_FIRST_CONFIG["rhythm_target"]),
            },
            "post_pipeline_skipped": bool(post_pipeline_skipped),
            "skip_reason": skip_reason if post_pipeline_skipped else "",
            "phase_effect_metrics": dict(getattr(self, "_last_resonance_phase_effect_metrics", {})),
            "zero_base_length_plan": dict(getattr(self, "_zero_base_length_plan", {}) or {}),
            "contract_alignment": dict(getattr(self, "_last_contract_alignment", {}) or {}),
            "zero_base_rhythm_report": dict(getattr(self, "_zero_base_rhythm_report", {}) or {}),
            "regex_cache": {
                "section_block_cache_hits": self._section_block_cache_hits,
                "section_block_cache_misses": self._section_block_cache_misses,
            },
            "section_generation": {
                "parallel_sections": bool(section_cfg.get("parallel_sections", False)),
                "novelty_gate_enabled": bool(getattr(novelty_cfg, "get", lambda *args, **kwargs: False)("enabled", False)),
                "context_overlap_enabled": bool(getattr(overlap_cfg, "get", lambda *args, **kwargs: False)("enabled", False)),
                "hard_soft_mode": str(getattr(hard_soft_cfg, "get", lambda *args, **kwargs: "off")("mode", "off")),
            },
            "semantic_dedupe": {
                "enabled": bool(semantic_dedupe_cfg.get("enabled", True)),
                "rewrite_enabled": bool(semantic_dedupe_cfg.get("rewrite_enabled", False)),
                "rewrite_owner": "coherence_dedupe_stage",
            },
            "postprocess": {
                "repair_only_enabled": bool(getattr(repair_cfg, "get", lambda *args, **kwargs: False)("enabled", False)),
                "repair_only_mode": str(getattr(repair_cfg, "get", lambda *args, **kwargs: "off")("mode", "off")),
            },
            "retry_telemetry": list(getattr(self, "_last_retry_telemetry", []) or []),
            "hard_soft_eval": dict(getattr(self, "_last_hard_soft_eval", {}) or {}),
            "final_quality_eval": dict(getattr(self, "_last_final_quality_eval", {}) or {}),
            "repair_only_report": dict(getattr(self, "_last_repair_only_report", {}) or {}),
            "contextual_naturalness_report": dict(getattr(self, "_last_contextual_naturalness_report", {}) or {}),
            "editor_persona": {
                "profiles": editor_persona_profiles,
            },
        }

    def _build_quality_pipeline_check(self) -> Dict[str, Any]:
        quality_config = get_quality_pipeline_config()
        return {
            "enabled": quality_config.enabled,
            "mode": quality_config.mode,
            "rollout_percent": quality_config.rollout_percent,
            "phase01_lexical_enabled": quality_config.phase01_lexical_enabled,
            "phase01_tokenizer": quality_config.phase01_tokenizer,
            "phase02_burstiness_enabled": quality_config.phase02_burstiness_enabled,
            "phase03_nominalization_enabled": quality_config.phase03_nominalization_enabled,
            "phase04_style_drift_enabled": quality_config.phase04_style_drift_enabled,
            "phase05_layout_guard_enabled": quality_config.phase05_layout_guard_enabled,
            "phase06_orchestrator_enabled": quality_config.phase06_orchestrator_enabled,
            "phase07_rollout_enabled": quality_config.phase07_rollout_enabled,
            "lexical_threshold": quality_config.lexical_threshold,
            "burstiness_target_min": quality_config.burstiness_target_min,
            "burstiness_target_max": quality_config.burstiness_target_max,
            "nominalization_alert_threshold": quality_config.nominalization_alert_threshold,
            "style_alignment_min_score": quality_config.style_alignment_min_score,
            "domain_guard_strictness": quality_config.domain_guard_strictness,
            "supplement_min_position_ratio": quality_config.supplement_min_position_ratio,
            "intro_max_length_ratio": quality_config.intro_max_length_ratio,
            "section_coherence_min_score": quality_config.section_coherence_min_score,
            "global_rewrite_ratio_cap": quality_config.global_rewrite_ratio_cap,
            "conflict_resolution_policy": quality_config.conflict_resolution_policy,
            "quality_gate_min_score": quality_config.quality_gate_min_score,
            "max_rewrite_ratio": quality_config.max_rewrite_ratio,
            "max_sentence_split_ratio": quality_config.max_sentence_split_ratio,
            "max_nominalization_rewrite_ratio": quality_config.max_nominalization_rewrite_ratio,
            "fingerprint_enabled": quality_config.fingerprint_enabled,
            "fail_open": quality_config.fail_open,
            "reports": list(getattr(self, "_quality_phase_reports", [])),
        }

    def _build_llm_check(self) -> Dict[str, Any]:
        llm_config = get_llm_config()
        return {
            "model": llm_config.model_name,
            "fallback_model": llm_config.fallback_model,
            "temperature_strategy": "0.8-1.1 random (disabled when top_p is set)",
            "top_p": llm_config.top_p,
            "max_tokens_default": 1200,
            "long_form_retry_max_tokens": 2400,
            "retry_policy": "max 3 attempts with parameter fallback + model fallback",
        }
    
    def quick_legal_check(self, text: str) -> dict:
        """簡易リーガルチェック（テキスト貼り付け用・根拠付き）
        Delegate to Phase 6 Legal module.
        """
        from human_resonance.phase6_legal import Phase6Legal
        
        if not text:
            return {"checked_text": "", "has_issues": False, "risk_level": "none", "issues": []}
            
        legal_phase = Phase6Legal(llm_client=self.llm)
        result = legal_phase.analyze_with_rationale(text, use_llm=True)
        
        return {
            "checked_text": result.checked_text,
            "has_issues": result.has_issues,
            "risk_level": result.risk_level.value,
            "issues": [i.__dict__ for i in result.issues]
        }

    def evaluate_resonance_score(self, text: str) -> dict:
        """Human Resonance Pipelineを使用してスコアを算出"""
        from human_resonance.pipeline import analyze_text
        
        if not text:
            return {
                "total_score": 0.0,
                "metrics": {
                    "empathy": 0.0,
                    "curiosity": 0.0,
                    "humanity": 0.0,
                    "rhythm": 0.0
                }
            }
            
        analysis = analyze_text(text)
        
        return {
            "total_score": analysis["total_resonance_score"],
            "metrics": {
                "empathy": analysis["empathy"]["total"],
                "curiosity": analysis["curiosity"]["total"],
                "humanity": analysis["humanity"]["total"],
                "rhythm": analysis["rhythm"]["total"]
            }
        }

    def _article_generator_extract_quote_candidates(self, merged: str) -> List[str]:
        """ストーリーの核となるエピソード、こだわり、具体的な事実を抽出する"""
        if not merged:
            return []
        sentences = re.split(r"(?<=[。！？])", merged)
        candidates = []
        for s in sentences:
            s = s.strip()
            # 短すぎる、または長すぎる文を除外
            if len(s) < 30 or len(s) > 200:
                continue
            # ストーリ性・事実性のあるキーワードを含む文を優先
            story_indicators = r"\d|％|%|とは|定義|研究|調査|実験|こだわ|想い|苦労|背景|きっかけ|気づい|発見|意外|実は"
            if re.search(story_indicators, s):
                candidates.append(s)
        
        random.shuffle(candidates)
        return candidates[:5]
