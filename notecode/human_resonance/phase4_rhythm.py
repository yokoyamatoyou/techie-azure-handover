"""Phase 4: Rhythm - リズム・テンポ調整

読みやすく、息継ぎのあるテンポを作るモジュール。
散文リズム論、認知負荷理論の知見を活用。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import statistics
import random


@dataclass
class RhythmScore:
    """リズムスコアを表すデータクラス"""

    sentence_variance: float = 0.0  # 文長の分散（揺らぎ）
    paragraph_balance: float = 0.0  # 段落のバランス
    breathing_room: float = 0.0  # 息継ぎの余白
    flow: float = 0.0  # 文の流れ
    total: float = 0.0

    def calculate_total(self) -> float:
        """総合スコアを計算"""
        weights = {
            "sentence_variance": 0.35,
            "paragraph_balance": 0.25,
            "breathing_room": 0.2,
            "flow": 0.2,
        }
        self.total = (
            self.sentence_variance * weights["sentence_variance"]
            + self.paragraph_balance * weights["paragraph_balance"]
            + self.breathing_room * weights["breathing_room"]
            + self.flow * weights["flow"]
        )
        return self.total


# 理想的な文長の範囲
SENTENCE_LENGTH_TARGETS = {
    "short": (20, 40),  # 短文：強調・余韻
    "medium": (50, 70),  # 中文：説明・展開
    "long": (80, 100),  # 長文：複雑な論理
}

# 理想的な段落の文数
PARAGRAPH_SENTENCE_RANGE = (3, 6)


class Phase4Rhythm:
    """Phase 4: リズム調整処理"""

    def __init__(self):
        pass

    def process(self, text: str, target_score: float = 0.5) -> str:
        """テキストのリズムを調整する

        Args:
            text: 入力テキスト
            target_score: 目標とするリズムスコア（0.0〜1.0）

        Returns:
            リズムが調整されたテキスト
        """
        if not text:
            return ""

        current_score = self.analyze(text)

        if current_score.total >= target_score:
            return text

        result = text

        # 文長の揺らぎが少ない場合は調整
        if current_score.sentence_variance < 0.4:
            result = self._adjust_sentence_variance(result)

        # 段落バランスが悪い場合は調整
        if current_score.paragraph_balance < 0.4:
            result = self._adjust_paragraph_balance(result)

        # 息継ぎの余白が少ない場合
        if current_score.breathing_room < 0.3:
            result = self._add_breathing_room(result)

        # 接続詞の連続を抑える（単調さの軽減）
        if self._has_repeated_connectors(result):
            result = self._reduce_connector_repetition(result)

        return result

    def analyze(self, text: str) -> RhythmScore:
        """テキストのリズムスコアを分析する"""
        if not text:
            return RhythmScore()

        score = RhythmScore()

        # 文長の分散を計算
        sentences = self._extract_sentences(text)
        if len(sentences) >= 3:
            lengths = [len(s) for s in sentences]
            try:
                std_dev = statistics.stdev(lengths)
                # 標準偏差が15〜40の範囲が理想（人間の実文章に近い）
                if 15 <= std_dev <= 40:
                    score.sentence_variance = 1.0
                elif std_dev < 15:
                    score.sentence_variance = std_dev / 15
                else:
                    score.sentence_variance = max(0, 1 - (std_dev - 40) / 50)
            except statistics.StatisticsError:
                score.sentence_variance = 0.5

        # 段落バランスを計算
        paragraphs = self._extract_paragraphs(text)
        if paragraphs:
            sentence_counts = []
            for para in paragraphs:
                if not para.strip().startswith("##"):
                    sents = self._extract_sentences(para)
                    if sents:
                        sentence_counts.append(len(sents))

            if sentence_counts:
                avg_count = sum(sentence_counts) / len(sentence_counts)
                # 3〜6文が理想
                if 3 <= avg_count <= 6:
                    score.paragraph_balance = 1.0
                elif avg_count < 3:
                    score.paragraph_balance = avg_count / 3
                else:
                    score.paragraph_balance = max(0, 1 - (avg_count - 6) / 6)

        # 息継ぎの余白（短い段落や改行の存在）
        short_para_ratio = sum(1 for p in paragraphs if len(p) < 100) / max(len(paragraphs), 1)
        score.breathing_room = min(1.0, short_para_ratio * 3)

        # 文の流れ（接続詞の多様性）
        connectors = ["そして", "また", "さらに", "しかし", "ところが", "だから", "なので", "ただ", "むしろ"]
        connector_variety = len(set(c for c in connectors if c in text))
        score.flow = min(1.0, connector_variety / 5)

        score.calculate_total()
        return score

    def _extract_sentences(self, text: str) -> List[str]:
        """テキストから文を抽出する"""
        # 見出しを除外
        clean_text = re.sub(r'^##.*$', '', text, flags=re.MULTILINE)
        sentences = re.split(r'[。！？]', clean_text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]

    def _extract_paragraphs(self, text: str) -> List[str]:
        """テキストから段落を抽出する"""
        paragraphs = text.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]

    def _adjust_sentence_variance(self, text: str) -> str:
        """文長の揺らぎを調整する（分割＋結合の両方向で対応）"""
        paragraphs = text.split("\n\n")
        result_paragraphs = []

        for para in paragraphs:
            if para.strip().startswith("##"):
                result_paragraphs.append(para)
                continue

            sentences = re.split(r'(?<=[。！？])', para)
            sentences = [s for s in sentences if s.strip()]

            if len(sentences) < 2:
                result_paragraphs.append(para)
                continue

            # 均一な長さの文が続いていないかチェック
            adjusted_sentences = []
            prev_len = 0
            changes_made = 0

            i = 0
            while i < len(sentences):
                sent = sentences[i]
                curr_len = len(sent)

                if abs(curr_len - prev_len) < 15 and prev_len > 0 and changes_made < 3:
                    # 長い文（45文字超）なら読点で分割
                    if curr_len > 45 and "、" in sent:
                        parts = sent.split("、", 1)
                        if len(parts) == 2 and len(parts[0]) > 12:
                            adjusted_sentences.append(parts[0] + "。")
                            adjusted_sentences.append(parts[1])
                            prev_len = len(parts[1])
                            changes_made += 1
                            i += 1
                            continue
                    # 短い文（40文字以下）が連続 → 次の文と結合を試みる
                    elif curr_len <= 40 and i + 1 < len(sentences):
                        next_sent = sentences[i + 1].strip()
                        # 次の文も短ければ結合
                        if len(next_sent) <= 40 and next_sent:
                            # 句点を読点に変えて結合
                            merged = sent.rstrip("。！？") + "、" + next_sent.lstrip()
                            adjusted_sentences.append(merged)
                            prev_len = len(merged)
                            changes_made += 1
                            i += 2
                            continue

                adjusted_sentences.append(sent)
                prev_len = curr_len
                i += 1

            result_paragraphs.append("".join(adjusted_sentences))

        return "\n\n".join(result_paragraphs)

    def _adjust_paragraph_balance(self, text: str) -> str:
        """段落のバランスを調整する"""
        paragraphs = text.split("\n\n")
        result_paragraphs = []

        for para in paragraphs:
            if para.strip().startswith("##"):
                result_paragraphs.append(para)
                continue

            sentences = re.split(r'(?<=[。！？])', para)
            sentences = [s for s in sentences if s.strip()]

            # 文が多すぎる段落は分割
            if len(sentences) > 7:
                mid = len(sentences) // 2
                first_para = "".join(sentences[:mid])
                second_para = "".join(sentences[mid:])
                result_paragraphs.append(first_para)
                result_paragraphs.append(second_para)
            # 文が1つだけで長い段落は分割を試みる
            elif len(sentences) == 1 and len(para) > 150:
                # 読点で分割を試みる
                if para.count("、") >= 2:
                    parts = para.split("、")
                    if len(parts) >= 3:
                        mid = len(parts) // 2
                        first = "、".join(parts[:mid]) + "。"
                        second = "、".join(parts[mid:])
                        result_paragraphs.append(first)
                        result_paragraphs.append(second)
                        continue
                result_paragraphs.append(para)
            else:
                result_paragraphs.append(para)

        return "\n\n".join(result_paragraphs)

    def _add_breathing_room(self, text: str) -> str:
        """息継ぎの余白を追加する（固定フレーズは挿入しない）"""
        paragraphs = text.split("\n\n")

        if len(paragraphs) < 3:
            return text

        result_paragraphs = []
        consecutive_long = 0

        for i, para in enumerate(paragraphs):
            if para.strip().startswith("##"):
                result_paragraphs.append(para)
                consecutive_long = 0
                continue

            # 長い段落が続いたら、文境界で段落を分割して余白を作る
            if len(para) > 200:
                consecutive_long += 1
            else:
                consecutive_long = 0

            if consecutive_long >= 2:
                sentences = [s for s in re.split(r'(?<=[。！？])', para) if s]
                if len(sentences) >= 4:
                    mid = len(sentences) // 2
                    first = "".join(sentences[:mid]).strip()
                    second = "".join(sentences[mid:]).strip()
                    if first and second:
                        result_paragraphs.append(first)
                        result_paragraphs.append(second)
                        consecutive_long = 0
                        continue

            result_paragraphs.append(para)

        return "\n\n".join(result_paragraphs)

    def _has_repeated_connectors(self, text: str) -> bool:
        """段落内＋段落またぎの接続詞連続を検出（段落冒頭の接続詞を追跡）"""
        connectors = ["そして", "また", "さらに", "しかし", "だから", "なので", "ただ", "むしろ"]
        connector_pattern = re.compile(r"^(%s)(、)?" % "|".join(connectors))
        last_leading_connector = ""  # 各段落の先頭接続詞を追跡

        paragraphs = text.split("\n\n")
        for para in paragraphs:
            if para.strip().startswith("##"):
                last_leading_connector = ""
                continue
            sentences = re.split(r'(?<=[。！？])', para)
            para_leading = ""  # この段落の先頭接続詞
            prev = ""
            for sent in sentences:
                s = sent.strip()
                if not s:
                    continue
                m = connector_pattern.match(s)
                if m:
                    curr = m.group(1)
                    if not para_leading:
                        para_leading = curr
                    # 段落内の連続チェック
                    if curr == prev and prev:
                        return True
                    prev = curr
                else:
                    prev = ""
            # 段落またぎチェック: 前の段落の先頭接続詞と同じなら連続
            if para_leading and para_leading == last_leading_connector:
                return True
            if para_leading:
                last_leading_connector = para_leading
        return False

    def _reduce_connector_repetition(self, text: str) -> str:
        """段落内＋段落またぎの接続詞連続を置換"""
        replacements = {
            "そして": ["それに", "そのうえ", "加えて"],
            "また": ["さらに", "別の観点では", "もう一つ"],
            "さらに": ["加えて", "そのうえ", "続けて"],
            "しかし": ["ただし", "とはいえ", "けれども"],
            "だから": ["そのため", "なので", "結果として"],
            "なので": ["そのため", "だから", "結果として"],
            "ただ": ["もっと言うと", "とはいえ", "一方で"],
            "むしろ": ["どちらかというと", "逆に", "実際には"],
        }
        connector_pattern = re.compile(r"^(%s)(、)?" % "|".join(replacements.keys()))

        paragraphs = text.split("\n\n")
        result_paragraphs = []
        last_leading_connector = ""  # 前の段落の先頭接続詞

        for para in paragraphs:
            if para.strip().startswith("##"):
                result_paragraphs.append(para)
                last_leading_connector = ""
                continue

            sentences = re.split(r'(?<=[。！？])', para)
            adjusted = []
            para_leading = ""
            prev = ""
            for sent in sentences:
                s = sent.strip()
                if not s:
                    adjusted.append(sent)
                    continue
                m = connector_pattern.match(s)
                if m:
                    connector = m.group(1)
                    if not para_leading:
                        para_leading = connector
                    # 段落内連続 or 段落またぎ（先頭同士）の場合に置換
                    should_replace = (connector == prev and prev) or (connector == last_leading_connector and not prev and para_leading == connector)
                    if should_replace and replacements.get(connector):
                        replacement = random.choice(replacements[connector])
                        s = re.sub(r"^%s" % re.escape(connector), replacement, s, count=1)
                    prev = connector
                    adjusted.append(s)
                else:
                    prev = ""
                    adjusted.append(sent)

            result_paragraphs.append("".join(adjusted))
            if para_leading:
                last_leading_connector = para_leading

        return "\n\n".join(result_paragraphs)

    def get_sentence_length_distribution(self, text: str) -> Dict[str, int]:
        """文長の分布を取得する"""
        sentences = self._extract_sentences(text)

        distribution = {"short": 0, "medium": 0, "long": 0, "very_long": 0}

        for sent in sentences:
            length = len(sent)
            if length < 40:
                distribution["short"] += 1
            elif length < 70:
                distribution["medium"] += 1
            elif length < 100:
                distribution["long"] += 1
            else:
                distribution["very_long"] += 1

        return distribution

    def get_improvement_suggestions(self, text: str) -> List[str]:
        """リズム改善の提案を返す"""
        score = self.analyze(text)
        suggestions = []

        if score.sentence_variance < 0.4:
            distribution = self.get_sentence_length_distribution(text)
            if distribution["short"] < distribution["medium"]:
                suggestions.append(
                    "短い文（20〜40字）を増やすと、リズムに変化が生まれます"
                )
            elif distribution["long"] < distribution["short"]:
                suggestions.append(
                    "やや長めの文（80〜100字）も混ぜると、説得力が増します"
                )

        if score.paragraph_balance < 0.4:
            suggestions.append(
                "段落は3〜6文程度にまとめると読みやすくなります"
            )

        if score.breathing_room < 0.3:
            suggestions.append(
                "長い段落が続いたら、短い段落（1〜2文）で息継ぎを入れてください"
            )

        if score.flow < 0.4:
            suggestions.append(
                "接続詞を「そして」「また」だけでなく「だから」「ただ」なども使ってください"
            )

        return suggestions


def calculate_rhythm_score(text: str) -> float:
    """テキストのリズムスコアを計算するヘルパー関数"""
    phase = Phase4Rhythm()
    score = phase.analyze(text)
    return score.total
