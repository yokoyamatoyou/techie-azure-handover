"""Phase 5: Editor - 編集者校正 + ファクトチェック

プロの編集者視点での校正と、ハルシネーション対策のファクトチェックを行うモジュール。
"""
from __future__ import annotations

import logging
import re
import random
from difflib import SequenceMatcher
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from human_resonance.style_policy import PHRASE_VARIANTS

logger = logging.getLogger(__name__)

@dataclass
class EditorIssue:
    """編集上の問題を表すデータクラス"""

    category: str  # 問題のカテゴリ
    description: str  # 問題の説明
    location: str  # 問題箇所（抜粋）
    severity: str  # 重大度: high, medium, low
    suggestion: str  # 修正提案


@dataclass
class FactCheckResult:
    """ファクトチェック結果を表すデータクラス"""

    is_verified: bool = True
    unverified_claims: List[str] = field(default_factory=list)
    numbers_without_source: List[str] = field(default_factory=list)
    proper_nouns_without_source: List[str] = field(default_factory=list)


# 編集者チェックポイント
EDITOR_CHECK_POINTS: Dict[str, Dict[str, Any]] = {
    "pronoun_consistency": {
        "description": "一人称の一貫性",
        "patterns": {
            "私": ["僕", "俺", "わたし", "ワタシ", "僕たち", "僕ら"],
            "僕": ["私", "俺", "わたし", "僕たち", "僕ら"],
            "私たち": ["我々", "弊社", "当社", "私達", "わたしたち", "わたし達"],
            "僕たち": ["僕ら", "僕達", "ぼくたち", "ぼく達", "ぼくら"],
        },
        "severity": "high",
    },
    "honorific_error": {
        "description": "自社への敬称誤用",
        "patterns": [r"弊社様", r"当社様", r"自社様", r"我が社様"],
        "severity": "high",
    },
    "self_praise": {
        "description": "過度な自画自賛",
        "patterns": [
            r"最高の", r"他社にはない", r"業界No\.?1", r"唯一無二の",
            r"圧倒的", r"究極の", r"完璧な", r"最強の",
        ],
        "severity": "medium",
    },
    "stealth_marketing": {
        "description": "ステマ調の表現",
        "patterns": [
            r"実は私も愛用", r"実は僕も使っ", r"周りでも評判",
            r"友人に勧められ", r"話題の",
        ],
        "severity": "medium",
    },
    "style_consistency": {
        "description": "文体の一貫性",
        "check_type": "style_mix",
        "severity": "low",
    },
    "jargon_unexplained": {
        "description": "専門用語の説明不足",
        "check_type": "jargon",
        "severity": "low",
    },
}

# ファクトチェック用パターン
FACT_PATTERNS = {
    # 数字（年号、金額、割合など）
    "numbers": r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:円|万|億|%|％|年|月|日|人|件|回|倍|個|本|社|店))',
    # 固有名詞（カタカナ語、英字を含む）
    "proper_nouns": r'([A-Z][a-zA-Z]+|[ァ-ヶー]{3,}(?:株式会社|社|Inc\.|Co\.|Ltd\.)?)',
    # 引用符で囲まれた文
    "quotes": r'[「『"](.*?)[」』"]',
}

# 文末表現の揺らぎ（カジュアル寄り）
# 注意: 「です。」を「でしょう。」へ変えるようなモダリティ変更は避ける。
# 同系統の語尾（終助詞付与など）だけで揺らす。
ENDING_VARIANTS: Dict[str, List[str]] = {
    "です。": ["です。", "ですね。", "ですよね。", "です。"],
    "ます。": ["ます。", "ますね。", "ますよね。", "ます。"],
    "でしょう。": ["でしょう。", "でしょうね。", "でしょう。"],
    "ません。": ["ません。", "ませんね。", "ませんよね。"],
    "でした。": ["でした。", "でしたね。", "でしたよね。"],
    "ました。": ["ました。", "ましたね。", "ましたよね。"],
}

# 文末表現の揺らぎ（保守的: 企業記事/解説向け）
# 断定⇔推量・平叙⇔疑問を跨がず、近縁な丁寧終止のみ許可する。
ENDING_VARIANTS_CONSERVATIVE: Dict[str, List[str]] = {
    "です。": ["です。", "ですね。", "です。"],
    "ます。": ["ます。", "ますね。", "ます。"],
    "でしょう。": ["でしょう。", "でしょうね。"],
    "ません。": ["ません。", "ませんね。"],
    "でした。": ["でした。", "でしたね。"],
    "ました。": ["ました。", "ましたね。"],
}

# Zipf分布に基づく語彙選択（低頻度語を確率的に混入）
# 形式: 高頻度語 → [(代替語, 相対頻度), ...] 相対頻度が低いほど稀に使用
ZIPF_VOCABULARY: Dict[str, List[Tuple[str, float]]] = {
    # 接続詞の多様化（実コーパス寄りの偏り: 高頻度語を65%+に）
    "しかし": [("しかし", 0.65), ("ただ", 0.18), ("けれども", 0.10), ("とはいえ", 0.07)],
    "また": [("また", 0.60), ("加えて", 0.15), ("それに", 0.15), ("さらには", 0.10)],
    "そして": [("そして", 0.55), ("それから", 0.20), ("そのうえ", 0.15), ("しかも", 0.10)],
    "だから": [("だから", 0.50), ("そのため", 0.25), ("それゆえ", 0.15), ("というわけで", 0.10)],
    "なぜなら": [("なぜなら", 0.55), ("というのも", 0.30), ("その理由は", 0.15)],
    # 副詞の多様化
    "とても": [("とても", 0.50), ("非常に", 0.22), ("かなり", 0.18), ("すごく", 0.10)],
    "少し": [("少し", 0.50), ("やや", 0.22), ("ちょっと", 0.18), ("多少", 0.10)],
    "特に": [("特に", 0.60), ("とりわけ", 0.20), ("中でも", 0.15), ("なかんずく", 0.05)],
    # 動詞・表現の多様化
    "思います": [("思います", 0.55), ("考えます", 0.22), ("感じます", 0.15), ("思うんです", 0.08)],
    "必要です": [("必要です", 0.60), ("欠かせません", 0.20), ("大切です", 0.12), ("不可欠です", 0.08)],
    "可能です": [("可能です", 0.55), ("できます", 0.30), ("実現できます", 0.15)],
}

# 複合接続語の語幹を壊す置換を防ぐための接尾辞ガード
# 例: だからこそ / しかしながら
ZIPF_COMPOUND_SUFFIX_GUARDS: Dict[str, Tuple[str, ...]] = {
    "だから": ("こそ",),
    "しかし": ("ながら",),
}

# 連続しやすい構文の揺らぎ
STRUCTURE_VARIANTS: Dict[str, List[str]] = {
    "〜することで": ["〜すると", "〜するだけで", "〜する際に"],
    "〜するため": ["〜する目的で", "〜する際に", "〜を意識して"],
    "〜ということは": ["〜という点は", "〜という意味では", "〜という観点では"],
}

PRONOUN_PATTERNS: Dict[str, str] = {
    "私": r"私(?!たち|達)",
    "わたし": r"わたし(?!たち|達)",
    "僕": r"僕(?!たち|達|ら)",
    "俺": r"俺",
    "私たち": r"(私たち|私達|わたしたち|わたし達)",
    "僕たち": r"(僕たち|僕達|僕ら|ぼくたち|ぼく達|ぼくら)",
    "当社": r"当社",
    "弊社": r"弊社",
}



class Phase5Editor:
    """Phase 5: 編集者校正 + ファクトチェック処理"""

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        phrase_max_per_paragraph: int = 2,
        phrase_probability: float = 0.75,
        phrase_min_occurrences: int = 2,
        pronoun_reduction_ratio: float = 0.5,
        pronoun_reduction_min_count: int = 4,
        style_profile: str = "balanced",
    ):
        """
        Args:
            llm_client: LLMクライアント（ファクトチェック用、オプション）
            phrase_max_per_paragraph: 言い回し置換の1段落あたり最大回数（設計: 1段落1回まで）
            phrase_probability: 言い回し置換を実行する確率（0〜1）
            phrase_min_occurrences: 言い回し置換を発動させる最小出現回数（この回数以上で置換対象）
        """
        self.llm = llm_client
        self.phrase_max_per_paragraph = max(0, phrase_max_per_paragraph)
        self.phrase_probability = min(1.0, max(0.0, phrase_probability))
        self.phrase_min_occurrences = max(2, phrase_min_occurrences)
        self.pronoun_reduction_ratio = min(1.0, max(0.0, pronoun_reduction_ratio))
        self.pronoun_reduction_min_count = max(0, pronoun_reduction_min_count)
        self.style_profile = (style_profile or "balanced").lower()

    def _get_ending_variants(self) -> Dict[str, List[str]]:
        """文体プロファイルごとの文末揺らぎセットを返す。"""
        if self.style_profile == "casual":
            return ENDING_VARIANTS
        return ENDING_VARIANTS_CONSERVATIVE

    def process(
        self,
        text: str,
        source_text: Optional[str] = None,
        expected_pronoun: Optional[str] = None,
    ) -> str:
        """テキストを編集者視点で校正し、ファクトチェックを行う

        Args:
            text: 入力テキスト
            source_text: ファクトチェック用のソーステキスト
            expected_pronoun: 期待する一人称（None の場合は自動検出）

        Returns:
            校正済みテキスト
        """
        if not text:
            return ""

        result = text

        # Step 1: 編集者視点の校正
        issues = self.analyze_editorial_issues(result, expected_pronoun)

        for issue in issues:
            if issue.severity == "high":
                result = self._fix_issue(result, issue)

        # Step 1.5: 言い回しの反復を抑える（表現の揺らぎ）
        result = self._reduce_repetition(result)

        # Step 1.6: 一人称の過剰出現を抑制（主語の自然な省略）
        result = self._reduce_pronoun_frequency(result, expected_pronoun)

        # Step 1.7: Zipf分布に基づく語彙の多様化（人間らしい語彙選択）
        result = self._apply_zipf_vocabulary(result)

        # Step 1.8: 文末パターンの多様化（連続回避 + 自然な揺らぎ）
        result = self._diversify_sentence_endings(result)

        # Step 1.9: 文法の自然さを最小限で整える（人間味は保持）
        result = self._grammar_polish(result)

        # Step 2: ファクトチェック（ソースがある場合）
        if source_text:
            fact_result = self.fact_check(result, source_text)

            if not fact_result.is_verified:
                result = self._fix_unverified_claims(result, fact_result, source_text)

        return result

    def _reduce_repetition(self, text: str) -> str:
        """同一フレーズの反復を抑えて表現に揺らぎを出す（1段落1回まで・確率的・閾値）"""
        if not text:
            return ""

        result = text
        for phrase, variants in PHRASE_VARIANTS.items():
            if result.count(phrase) >= self.phrase_min_occurrences:
                result = self._replace_repeated_phrase_per_paragraph(
                    result,
                    phrase,
                    variants,
                    max_per_paragraph=self.phrase_max_per_paragraph,
                    probability=self.phrase_probability,
                )

        result = self._reduce_repeated_endings(result)
        result = self._reduce_repeated_structures(result)

        return result

    def _replace_repeated_phrase_per_paragraph(
        self,
        text: str,
        phrase: str,
        variants: List[str],
        max_per_paragraph: int = 2,
        probability: float = 0.75,
    ) -> str:
        """繰り返しフレーズを段落単位で置換する（段落をまたぐ反復も検出）"""
        if not variants or max_per_paragraph <= 0:
            return text

        escaped = re.escape(phrase)
        paragraphs = text.split("\n\n")
        result_paragraphs = []
        global_occurrence = 0  # テキスト全体での出現番号を追跡
        variant_idx = 0  # variants のローテーション用

        for para in paragraphs:
            if para.strip().startswith("##"):
                result_paragraphs.append(para)
                continue

            matches = list(re.finditer(escaped, para))
            if not matches:
                result_paragraphs.append(para)
                continue

            replaced_in_para = 0
            last_end = 0
            parts = []
            for m in matches:
                parts.append(para[last_end : m.start()])
                global_occurrence += 1
                # 全体で2回目以降 かつ 段落内の置換上限未満 なら確率で置換
                if global_occurrence >= 2 and replaced_in_para < max_per_paragraph and random.random() < probability:
                    alt = variants[variant_idx % len(variants)]
                    variant_idx += 1
                    parts.append(alt)
                    replaced_in_para += 1
                else:
                    parts.append(m.group(0))
                last_end = m.end()
            parts.append(para[last_end:])
            result_paragraphs.append("".join(parts))

        return "\n\n".join(result_paragraphs)

    def _reduce_repeated_endings(self, text: str) -> str:
        """連続する文末表現の揺らぎを控えめに作る"""
        ending_variants = self._get_ending_variants()
        paragraphs = text.split("\n\n")
        result_paragraphs = []
        replacement_prob = 0.55 if self.style_profile == "casual" else 0.4

        for para in paragraphs:
            if para.strip().startswith("##"):
                result_paragraphs.append(para)
                continue

            lines = para.split("\n")
            result_lines = []
            prev_ending = ""
            changed = False

            for line in lines:
                if line.strip().startswith("##"):
                    result_lines.append(line)
                    prev_ending = ""
                    continue

                replaced = False
                for ending, variants in ending_variants.items():
                    if line.endswith(ending) and prev_ending == ending:
                        # 過剰な揺らぎを抑制するため、確率を控えめに設定
                        if not changed and len(line) > 12 and random.random() < replacement_prob:
                            candidates = [v for v in variants if v != ending]
                            alt = random.choice(candidates) if candidates else variants[0]
                            line = line[:-len(ending)] + alt
                            replaced = True
                            changed = True
                            prev_ending = ending  # 置換成功時のみ状態を更新
                        # 置換しなかった場合は prev_ending を更新しない（次の行で再検出可能に）
                        break

                if not replaced:
                    for ending in ending_variants.keys():
                        if line.endswith(ending):
                            prev_ending = ending
                            break
                result_lines.append(line)

            result_paragraphs.append("\n".join(result_lines))

        return "\n\n".join(result_paragraphs)

    def _reduce_repeated_structures(self, text: str) -> str:
        """繰り返し構文の揺らぎを作る"""
        result = text
        for pattern, variants in STRUCTURE_VARIANTS.items():
            if result.count(pattern) >= 2:
                result = self._replace_repeated_phrase_probabilistic(
                    result, pattern, variants, probability=0.5, max_replacements=1
                )
        return result

    def _apply_zipf_vocabulary(self, text: str) -> str:
        """Zipf分布に基づく語彙の多様化（人間らしい低頻度語の混入）

        人間の語彙選択はZipf分布に従う。高頻度語ばかりだとAI的に見えるため、
        確率的に低頻度の同義語を選択して自然な揺らぎを作る。

        設計原則:
        - 文章破綻を防ぐため、意味が完全に同じ語のみ置換
        - 見出し・箇条書きは除外
        - テキスト全体で追跡し、段落をまたぐ反復も検出
        - 確率はZipf分布の相対頻度に従う
        """
        if not text:
            return ""

        result = text

        for base_word, variants_with_freq in ZIPF_VOCABULARY.items():
            count = result.count(base_word)
            if count < 2:
                continue

            # 段落ごとに処理（見出しは除外）、全体で出現を追跡
            paragraphs = result.split("\n\n")
            result_paragraphs = []

            replaced_total = 0
            max_replacements = max(1, count - 1)  # 最低1つは元の表現を残す
            global_occurrence = 0

            for para in paragraphs:
                if para.strip().startswith("##") or para.strip().startswith("- "):
                    result_paragraphs.append(para)
                    continue

                if base_word not in para or replaced_total >= max_replacements:
                    result_paragraphs.append(para)
                    continue

                new_para = self._zipf_replace_in_paragraph(
                    para, base_word, variants_with_freq,
                    max_in_para=2,
                    remaining=max_replacements - replaced_total,
                    global_occurrence=global_occurrence,
                )

                # 置換回数を算出
                replaced_in_para = para.count(base_word) - new_para.count(base_word)
                replaced_total += max(0, replaced_in_para)
                global_occurrence += para.count(base_word)
                result_paragraphs.append(new_para)

            result = "\n\n".join(result_paragraphs)

        return result

    def _zipf_replace_in_paragraph(
        self,
        para: str,
        base_word: str,
        variants_with_freq: List[Tuple[str, float]],
        max_in_para: int = 2,
        remaining: int = 2,
        global_occurrence: int = 0,
    ) -> str:
        """段落内でZipf分布に基づいて語彙を置換（段落またぎも考慮）"""
        if not para or base_word not in para:
            return para

        matches = list(re.finditer(re.escape(base_word), para))
        if not matches:
            return para

        replaced = 0
        parts = []
        last_end = 0

        for i, m in enumerate(matches):
            parts.append(para[last_end:m.start()])
            overall_idx = global_occurrence + i  # テキスト全体での出現番号

            # 「だからこそ」「しかしながら」などの複合表現は語幹だけ置換しない
            if self._should_skip_zipf_compound_replacement(para, base_word, m.end()):
                parts.append(m.group(0))
                last_end = m.end()
                continue

            # 全体で2回目以降 かつ 段落内上限未満 なら Zipf確率で置換
            if overall_idx >= 1 and replaced < max_in_para and replaced < remaining:
                alt = self._select_by_zipf(variants_with_freq, exclude=base_word)
                if alt and random.random() < 0.7:
                    parts.append(alt)
                    replaced += 1
                else:
                    parts.append(m.group(0))
            else:
                parts.append(m.group(0))

            last_end = m.end()

        parts.append(para[last_end:])
        return "".join(parts)

    def _should_skip_zipf_compound_replacement(self, text: str, base_word: str, end: int) -> bool:
        """複合接続語（例: だからこそ）を壊す置換を抑止する。"""
        suffixes = ZIPF_COMPOUND_SUFFIX_GUARDS.get(base_word, ())
        if not suffixes:
            return False
        tail = text[end : end + 6]
        return any(tail.startswith(suffix) for suffix in suffixes)

    def _select_by_zipf(
        self,
        variants_with_freq: List[Tuple[str, float]],
        exclude: str = "",
    ) -> Optional[str]:
        """Zipf分布の確率に基づいて語彙を選択（元の語を除外可能）"""
        candidates = [(w, f) for w, f in variants_with_freq if w != exclude]
        if not candidates:
            return None

        # 確率の正規化
        total = sum(f for _, f in candidates)
        if total <= 0:
            return candidates[0][0]

        r = random.random() * total
        cumulative = 0.0
        for word, freq in candidates:
            cumulative += freq
            if r <= cumulative:
                return word

        return candidates[-1][0]

    def _diversify_sentence_endings(self, text: str) -> str:
        """文末パターンの多様化（連続回避に加え、全体の分布を調整）

        AIは「です。」「ます。」を均等に使いがち。人間は文脈で使い分ける。
        - 同じ文末が2回以上連続したら、2回目以降を控えめに変化させる
        - ただし破綻を防ぐため、意味を変えない範囲で

        設計原則:
        - 見出しは除外
        - 短い文（12文字以下）は除外
        - 1段落につき最大3回まで変化
        """
        if not text:
            return ""

        ending_variants = self._get_ending_variants()
        paragraphs = text.split("\n\n")
        result_paragraphs = []
        change_probability = 0.8 if self.style_profile == "casual" else 0.6
        max_changes = 3 if self.style_profile == "casual" else 2

        for para in paragraphs:
            if para.strip().startswith("##"):
                result_paragraphs.append(para)
                continue

            # 文を分割（。！？で区切る）
            sentences = re.split(r'([。！？])', para)
            if len(sentences) < 3:  # 文が少なければスキップ
                result_paragraphs.append(para)
                continue

            # 文末パターンを分析
            endings_sequence = []
            for i in range(0, len(sentences) - 1, 2):
                sentence = sentences[i]
                punct = sentences[i + 1] if i + 1 < len(sentences) else ""
                if sentence and punct:
                    # 文末の「です」「ます」等を抽出
                    for ending in ending_variants.keys():
                        if (sentence + punct).endswith(ending):
                            endings_sequence.append((i, ending))
                            break

            # 2回以上同じ文末が連続していたら変化を加える
            result_sentences = sentences.copy()
            changes_made = 0

            for idx in range(1, len(endings_sequence)):
                if changes_made >= max_changes:
                    break

                curr = endings_sequence[idx]
                prev = endings_sequence[idx - 1]

                # 2連続検出
                if curr[1] == prev[1]:
                    sentence_idx = curr[0]
                    ending = curr[1]

                    if sentence_idx < len(result_sentences):
                        sentence = result_sentences[sentence_idx]
                        # 十分な長さがある場合のみ、確率で変化
                        if len(sentence) > 12 and random.random() < change_probability:
                            variants = ending_variants.get(ending, [])
                            candidates = [v for v in variants if v != ending]
                            if candidates:
                                alt = random.choice(candidates)
                                # 文末を置換（安全チェック付き）
                                old_part = ending.rstrip("。！？")
                                if old_part and sentence.endswith(old_part) and len(sentence) > len(old_part):
                                    new_ending = alt.rstrip("。！？")
                                    result_sentences[sentence_idx] = (
                                        sentence[:-len(old_part)] + new_ending
                                    )
                                    # endings_sequenceも更新（次の比較に影響）
                                    endings_sequence[idx] = (sentence_idx, alt)
                                    changes_made += 1

            result_paragraphs.append("".join(result_sentences))

        return "\n\n".join(result_paragraphs)

    def _reduce_pronoun_frequency(
        self,
        text: str,
        expected_pronoun: Optional[str] = None,
    ) -> str:
        """一人称の出現頻度を抑える（主語の自然な省略のみ）"""
        if not text:
            return ""

        if self.pronoun_reduction_ratio >= 0.999:
            return text

        pronoun_counts = self._count_pronouns(text)
        if expected_pronoun and expected_pronoun in pronoun_counts:
            main_pronoun = expected_pronoun
        else:
            main_pronoun = max(pronoun_counts, key=pronoun_counts.get)

        count = pronoun_counts.get(main_pronoun, 0)
        if count < self.pronoun_reduction_min_count:
            return text

        target = max(0, int(round(count * self.pronoun_reduction_ratio)))
        to_remove = count - target
        if to_remove <= 0:
            return text

        pronoun_pattern = PRONOUN_PATTERNS.get(main_pronoun)
        if not pronoun_pattern:
            return text

        candidate_pattern = re.compile(
            rf'(^|[。！？]\s*|\n+)\s*(?:{pronoun_pattern})(?:は|が)'
        )

        paragraphs = text.split("\n\n")
        para_matches: List[List[re.Match[str]]] = []
        flat: List[Tuple[int, int]] = []

        for i, para in enumerate(paragraphs):
            if para.strip().startswith("##"):
                para_matches.append([])
                continue
            matches = list(candidate_pattern.finditer(para))
            para_matches.append(matches)
            for j in range(len(matches)):
                flat.append((i, j))

        if not flat:
            return text

        to_remove = min(to_remove, len(flat))
        remove_set = set(random.sample(flat, to_remove))

        for i, matches in enumerate(para_matches):
            if not matches:
                continue
            if not any((i, j) in remove_set for j in range(len(matches))):
                continue

            para = paragraphs[i]
            parts: List[str] = []
            last = 0
            for j, m in enumerate(matches):
                if (i, j) not in remove_set:
                    continue
                parts.append(para[last:m.start()])
                parts.append(m.group(1))
                last = m.end()
            parts.append(para[last:])
            new_para = "".join(parts)
            new_para = re.sub(r'([。！？])\s+', r'\1', new_para)
            new_para = re.sub(r'^\s+', '', new_para)
            new_para = re.sub(r'\n{3,}', '\n\n', new_para)
            paragraphs[i] = new_para.strip()

        return "\n\n".join(paragraphs)

    def _grammar_polish(self, text: str) -> str:
        """LLMで文法の不自然さのみを整える（人間味は保持）"""
        if not text:
            return ""
        if not self.llm:
            return text

        prompt = f"""
あなたはプロの編集者です。以下の文章の文法の不自然さだけを最小限で修正してください。

【必須ルール】
- 内容・意味・語り口・感情・人間味の揺らぎは維持する
- 一人称の数を増やさない（削減された一人称は戻さない）
- 構成・段落数・見出しは変えない
- 口語・柔らかさを残す。過度に硬くしない
- 直すのは助詞抜け・主語述語の不一致・不自然な係り受けなど文法のみ
- 言い換え・要約・文体の均一化は禁止（変更は全体の15%以内を目安）

出力は修正後の本文のみ。説明は不要。

---
{text}
""".strip()

        max_tokens = min(5000, max(1200, int(len(text) * 0.9)))
        try:
            polished = self.llm.generate_text(
                prompt,
                max_tokens=max_tokens,
                task_type="editor_grammar",
            ).strip()
        except Exception as exc:
            logger.debug("Editor grammar LLM step failed. Returning original text.", exc_info=exc)
            return text

        polished = polished or text
        rewrite_ratio = self._estimate_rewrite_ratio(text, polished)
        if rewrite_ratio > 0.20:
            logger.info("Skip editor_grammar rewrite due high rewrite ratio: %.3f", rewrite_ratio)
            return text
        if self._looks_style_flattened(text, polished):
            logger.info("Skip editor_grammar rewrite due style flattening risk.")
            return text
        if self._heading_count(text) != self._heading_count(polished):
            logger.info("Skip editor_grammar rewrite due heading count change.")
            return text
        return polished

    def _estimate_rewrite_ratio(self, before: str, after: str) -> float:
        before_norm = re.sub(r"\s+", "", before or "")
        after_norm = re.sub(r"\s+", "", after or "")
        if not before_norm and not after_norm:
            return 0.0
        if not before_norm or not after_norm:
            return 1.0
        similarity = SequenceMatcher(None, before_norm[:12000], after_norm[:12000]).ratio()
        return max(0.0, 1.0 - similarity)

    def _sentence_length_stddev(self, text: str) -> float:
        sentences = [s.strip() for s in re.split(r"(?<=[。！？])\s*", text or "") if s.strip()]
        if len(sentences) < 4:
            return 0.0
        lengths = [len(s) for s in sentences]
        mean = sum(lengths) / len(lengths)
        variance = sum((ln - mean) ** 2 for ln in lengths) / len(lengths)
        return variance ** 0.5

    def _looks_style_flattened(self, before: str, after: str) -> bool:
        before_std = self._sentence_length_stddev(before)
        after_std = self._sentence_length_stddev(after)
        if before_std < 9.0:
            return False
        return after_std < before_std * 0.67 and (before_std - after_std) >= 5.0

    def _heading_count(self, text: str) -> int:
        return len(re.findall(r"^##\s+", text or "", re.MULTILINE))

    def _replace_repeated_phrase_probabilistic(
        self,
        text: str,
        phrase: str,
        variants: List[str],
        probability: float = 0.5,
        max_replacements: int = 1,
    ) -> str:
        if not variants or max_replacements <= 0:
            return text

        count = 0
        replaced = 0

        def _repl(match):
            nonlocal count, replaced
            count += 1
            if count == 1:
                return match.group(0)
            if replaced >= max_replacements:
                return match.group(0)
            if random.random() >= probability:
                return match.group(0)
            alt = variants[(count - 2) % len(variants)]
            replaced += 1
            return alt

        return re.sub(re.escape(phrase), _repl, text)

    def _replace_repeated_phrase(self, text: str, phrase: str, variants: List[str]) -> str:
        """繰り返しフレーズの2回目以降をバリエーションで置換"""
        if not variants:
            return text

        count = 0

        def _repl(match):
            nonlocal count
            count += 1
            if count == 1:
                return match.group(0)
            alt = variants[(count - 2) % len(variants)]
            return alt

        return re.sub(re.escape(phrase), _repl, text)

    def analyze_editorial_issues(
        self,
        text: str,
        expected_pronoun: Optional[str] = None,
    ) -> List[EditorIssue]:
        """編集上の問題を分析する"""
        issues = []

        # 一人称の一貫性チェック
        pronoun_issues = self._check_pronoun_consistency(text, expected_pronoun)
        issues.extend(pronoun_issues)

        # パターンベースのチェック
        for check_name, check_config in EDITOR_CHECK_POINTS.items():
            if "patterns" in check_config and isinstance(check_config["patterns"], list):
                for pattern in check_config["patterns"]:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        issues.append(EditorIssue(
                            category=check_name,
                            description=check_config["description"],
                            location=match if isinstance(match, str) else match[0],
                            severity=check_config["severity"],
                            suggestion=f"「{match}」を削除または修正してください",
                        ))

        # 文体の一貫性チェック
        style_issues = self._check_style_consistency(text)
        issues.extend(style_issues)

        return issues

    def _check_pronoun_consistency(
        self,
        text: str,
        expected_pronoun: Optional[str] = None,
    ) -> List[EditorIssue]:
        """一人称の一貫性をチェック"""
        issues = []
        # 一人称の出現をカウント
        pronoun_counts = self._count_pronouns(text)

        # 最も多い一人称を特定
        if expected_pronoun:
            main_pronoun = expected_pronoun
        else:
            main_pronoun = max(pronoun_counts, key=pronoun_counts.get)

        # 他の一人称が混在していないかチェック
        for pronoun, count in pronoun_counts.items():
            if pronoun != main_pronoun and count > 0:
                # 同じカテゴリは許容（私たちと当社など）
                corporate_pronouns = {"私たち", "当社", "弊社"}
                if main_pronoun in corporate_pronouns and pronoun in corporate_pronouns:
                    continue

                issues.append(EditorIssue(
                    category="pronoun_consistency",
                    description="一人称の不統一",
                    location=f"「{pronoun}」が{count}回使用",
                    severity="high",
                    suggestion=f"「{main_pronoun}」に統一してください",
                ))

        return issues

    def _count_pronouns(self, text: str) -> Dict[str, int]:
        return {p: len(re.findall(pattern, text)) for p, pattern in PRONOUN_PATTERNS.items()}

    def _check_style_consistency(self, text: str) -> List[EditorIssue]:
        """文体の一貫性をチェック（です・ます と だ・である の混在）"""
        issues = []

        # 見出し以外のテキストを抽出
        body_text = re.sub(r'^##.*$', '', text, flags=re.MULTILINE)

        # 文末パターンのカウント
        desu_masu_count = len(re.findall(r'(?:です|ます|でした|ました)[。！？]', body_text))
        da_dearu_count = len(re.findall(r'(?:だ|である|だった|であった)[。！？]', body_text))

        total = desu_masu_count + da_dearu_count

        if total > 5:
            minor_ratio = min(desu_masu_count, da_dearu_count) / total
            if minor_ratio > 0.2:  # 20%以上混在
                issues.append(EditorIssue(
                    category="style_consistency",
                    description="文体の混在",
                    location=f"です・ます: {desu_masu_count}回, だ・である: {da_dearu_count}回",
                    severity="low",
                    suggestion="文体を統一してください（です・ます調 推奨）",
                ))

        return issues

    def _fix_issue(self, text: str, issue: EditorIssue) -> str:
        """問題を修正する"""
        result = text

        if issue.category == "honorific_error":
            # 自社への敬称を削除
            result = re.sub(r'(弊社|当社|自社|我が社)様', r'\1', result)

        elif issue.category == "self_praise":
            # 過度な自画自賛表現を緩和
            replacements = {
                "最高の": "優れた",
                "他社にはない": "特徴的な",
                "業界No.1": "高い評価を得ている",
                "業界No1": "高い評価を得ている",
                "唯一無二の": "独自の",
                "圧倒的": "優れた",
                "究極の": "こだわりの",
                "完璧な": "質の高い",
                "最強の": "強力な",
            }
            for old, new in replacements.items():
                result = result.replace(old, new)

        return result

    def fact_check(self, text: str, source_text: str) -> FactCheckResult:
        """テキストの事実確認を行う

        ソーステキストと照合し、裏付けのない主張を検出する。
        """
        result = FactCheckResult()

        # 数字の検証
        numbers = re.findall(FACT_PATTERNS["numbers"], text)
        for num in numbers:
            if num not in source_text:
                # 数字がソースにない場合
                result.numbers_without_source.append(num)
                result.is_verified = False

        # 固有名詞の検証
        proper_nouns = re.findall(FACT_PATTERNS["proper_nouns"], text)
        for noun in proper_nouns:
            if len(noun) >= 3 and noun not in source_text:
                # 一般的すぎる単語は除外
                common_words = {"サービス", "システム", "アプリ", "ツール", "データ"}
                if noun not in common_words:
                    result.proper_nouns_without_source.append(noun)
                    result.is_verified = False

        return result

    def _fix_unverified_claims(
        self,
        text: str,
        fact_result: FactCheckResult,
        source_text: str,
    ) -> str:
        """裏付けのない主張を修正する"""
        result = text

        # ソースにない数字を抽象化
        for num in fact_result.numbers_without_source:
            # 「100万円」→「相当な金額」のような置換
            if "円" in num or "万" in num or "億" in num:
                result = result.replace(num, "一定の金額")
            elif "%" in num or "％" in num:
                result = result.replace(num, "一定の割合")
            elif "年" in num:
                # 年号は文脈を保持
                pass
            elif "人" in num or "件" in num or "社" in num:
                result = result.replace(num, "多くの" + num[-1])
            else:
                result = result.replace(num, "多くの")

        return result

    def get_editorial_summary(self, text: str) -> Dict[str, Any]:
        """編集上の分析サマリーを返す"""
        issues = self.analyze_editorial_issues(text)

        return {
            "total_issues": len(issues),
            "high_severity": len([i for i in issues if i.severity == "high"]),
            "medium_severity": len([i for i in issues if i.severity == "medium"]),
            "low_severity": len([i for i in issues if i.severity == "low"]),
            "issues_by_category": self._group_issues_by_category(issues),
        }

    def _group_issues_by_category(self, issues: List[EditorIssue]) -> Dict[str, int]:
        """問題をカテゴリ別にグループ化"""
        groups: Dict[str, int] = {}
        for issue in issues:
            groups[issue.category] = groups.get(issue.category, 0) + 1
        return groups


def run_editorial_check(text: str, source_text: Optional[str] = None) -> Dict[str, Any]:
    """編集チェックを実行するヘルパー関数"""
    editor = Phase5Editor()
    issues = editor.analyze_editorial_issues(text)

    result = {
        "issues": [
            {
                "category": i.category,
                "description": i.description,
                "location": i.location,
                "severity": i.severity,
                "suggestion": i.suggestion,
            }
            for i in issues
        ],
        "summary": editor.get_editorial_summary(text),
    }

    if source_text:
        fact_result = editor.fact_check(text, source_text)
        result["fact_check"] = {
            "is_verified": fact_result.is_verified,
            "unverified_numbers": fact_result.numbers_without_source,
            "unverified_nouns": fact_result.proper_nouns_without_source,
        }

    return result
