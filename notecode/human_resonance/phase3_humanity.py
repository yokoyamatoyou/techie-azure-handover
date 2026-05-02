"""Phase 3: Humanity - 人間味付与

「機械が書いたものではない」と感じさせるための人間らしい揺らぎを付与するモジュール。
心理言語学、発達心理学、社会言語学の知見を活用。
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class HumanityScore:
    """人間味スコアを表すデータクラス"""

    digression: float = 0.0  # 脱線と回帰
    self_correction: float = 0.0  # 言い直し
    uncertainty: float = 0.0  # 不完全性・曖昧さ
    casual_break: float = 0.0  # カジュアルな表現
    total: float = 0.0

    def calculate_total(self) -> float:
        """総合スコアを計算"""
        weights = {
            "digression": 0.2,
            "self_correction": 0.3,
            "uncertainty": 0.25,
            "casual_break": 0.25,
        }
        self.total = (
            self.digression * weights["digression"]
            + self.self_correction * weights["self_correction"]
            + self.uncertainty * weights["uncertainty"]
            + self.casual_break * weights["casual_break"]
        )
        return self.total


# 人間味マーカーの定義
HUMANITY_MARKERS: Dict[str, List[str]] = {
    # 脱線と回帰（話が逸れて戻る）
    "digression": [
        "ちなみに", "余談ですが", "話が逸れますが", "脱線するけど",
        "そういえば", "話を戻すと", "本題に戻ると", "ところで",
        "関係ないけど", "ついでに言うと",
    ],
    # 言い直し・自己訂正
    "self_correction": [
        "というか", "いや、", "正確には", "言い換えると",
        "むしろ", "というより", "訂正すると", "補足すると",
        "もっと言うと", "別の言い方をすると",
    ],
    # 不完全性・曖昧さ
    "uncertainty": [
        "たぶん", "だと思う", "かもしれない", "うまく言えないけど",
        "おそらく", "気がする", "ような", "っぽい",
        "はっきりとは", "断言はできないけど", "個人的な感覚だと",
    ],
    # カジュアルな表現（レジスター混在）
    "casual_break": [
        "なんですよね", "じゃないですか", "まあ、", "ぶっちゃけ",
        "なんだけど", "ってこと", "みたいな", "的な",
        "〜なわけで", "というわけで",
    ],
}

class Phase3Humanity:
    """Phase 3: 人間味付与処理"""

    def __init__(self, intensity: float = 0.5):
        """
        Args:
            intensity: 人間味の強度（0.0〜1.0）
                      高いほど多くの揺らぎを追加
        """
        self.intensity = min(1.0, max(0.0, intensity))

    def process(self, text: str, target_score: float = 0.4) -> str:
        """テキストに人間味を付与する

        Args:
            text: 入力テキスト
            target_score: 目標とする人間味スコア（0.0〜1.0）

        Returns:
            人間味が付与されたテキスト
        """
        if not text:
            return ""

        current_score = self.analyze(text)

        if current_score.total >= target_score:
            return text

        result = text

        text_len = len(result)

        # スコアが低い要素を強化（既存マーカーの配置調整＋軽量な挿入）
        if current_score.self_correction < 0.25 and text_len >= 400 and random.random() < self.intensity * 0.6:
            result = self._inject_self_correction(result)

        if current_score.uncertainty < 0.2 and random.random() < self.intensity * 0.8:
            result = self._inject_uncertainty(result)

        if current_score.casual_break < 0.2 and random.random() < self.intensity * 0.8:
            result = self._inject_casual_break(result)

        if current_score.digression < 0.15 and text_len >= 800 and random.random() < self.intensity * 0.4:
            result = self._inject_digression(result)

        return result

    def analyze(self, text: str) -> HumanityScore:
        """テキストの人間味スコアを分析する"""
        if not text:
            return HumanityScore()

        text_len = len(text)
        score = HumanityScore()

        for category, markers in HUMANITY_MARKERS.items():
            count = sum(1 for marker in markers if marker in text)
            normalized = min(1.0, count * 1000 / max(text_len, 1) / 3)

            if category == "digression":
                score.digression = normalized
            elif category == "self_correction":
                score.self_correction = normalized
            elif category == "uncertainty":
                score.uncertainty = normalized
            elif category == "casual_break":
                score.casual_break = normalized

        score.calculate_total()
        return score

    def _inject_self_correction(self, text: str) -> str:
        """言い直しを強調する（既存マーカーの再配置、なければ軽量挿入）"""
        paragraphs = text.split("\n\n")

        # 中盤の段落を探す
        candidates = [
            (i, p) for i, p in enumerate(paragraphs)
            if not p.strip().startswith("##") and len(p) > 50
        ]
        if not candidates:
            return text

        idx, para = random.choice(candidates)
        sentences = [s for s in re.split(r'(?<=[。！？])', para) if s]
        if len(sentences) < 2:
            return text

        sc_idx = None
        for s_idx, sent in enumerate(sentences):
            if any(m in sent for m in HUMANITY_MARKERS["self_correction"]):
                sc_idx = s_idx
                break

        if sc_idx is not None and sc_idx > 0:
            # 既存マーカー文を前半へ移動
            sc_sent = sentences.pop(sc_idx)
            sentences.insert(1, sc_sent)
            paragraphs[idx] = "".join(sentences)
        else:
            # マーカーがない場合: 2文目の冒頭に軽量な言い直し表現を付加
            prefixes = ["もっと言うと、", "正確には、", "むしろ、"]
            target_idx = 1 if len(sentences) > 1 else 0
            sent = sentences[target_idx].lstrip()
            if sent and not any(sent.startswith(p) for p in prefixes):
                sentences[target_idx] = random.choice(prefixes) + sent
                paragraphs[idx] = "".join(sentences)

        return "\n\n".join(paragraphs)

    def _inject_uncertainty(self, text: str) -> str:
        """不確実性を強調する（固定フレーズは挿入しない）"""
        paragraphs = text.split("\n\n")

        for i, para in enumerate(paragraphs):
            if para.strip().startswith("##"):
                continue
            sentences = [s for s in re.split(r'(?<=[。！？])', para) if s]
            if len(sentences) < 2:
                continue

            unc_idx = None
            for s_idx, sent in enumerate(sentences):
                if any(m in sent for m in HUMANITY_MARKERS["uncertainty"]):
                    unc_idx = s_idx
                    break
            if unc_idx is None:
                continue
            # 余韻として段落末に移動
            if unc_idx != len(sentences) - 1:
                unc_sent = sentences.pop(unc_idx)
                sentences.append(unc_sent)
                paragraphs[i] = "".join(sentences)
            break

        return "\n\n".join(paragraphs)

    def _inject_casual_break(self, text: str) -> str:
        """カジュアル表現を強調する（既存マーカーの再配置、なければ軽量挿入）"""
        paragraphs = text.split("\n\n")
        injected = False

        for i, para in enumerate(paragraphs):
            if para.strip().startswith("##"):
                continue
            sentences = [s for s in re.split(r'(?<=[。！？])', para) if s]
            if len(sentences) < 2:
                continue

            casual_idx = None
            for s_idx, sent in enumerate(sentences):
                if any(m in sent for m in HUMANITY_MARKERS["casual_break"]):
                    casual_idx = s_idx
                    break

            if casual_idx is not None:
                # 既存マーカー文を段落末に移動
                if casual_idx != len(sentences) - 1:
                    casual_sent = sentences.pop(casual_idx)
                    sentences.append(casual_sent)
                    paragraphs[i] = "".join(sentences)
                break
            elif not injected:
                # マーカーがない場合: 段落末の文末を柔らかい表現に差し替え
                last = sentences[-1].rstrip()
                replacements = [
                    ("です。", "ですね。"),
                    ("ます。", "ますよね。"),
                ]
                for old, new in replacements:
                    if last.endswith(old) and len(last) > 20:
                        sentences[-1] = last[:-len(old)] + new
                        paragraphs[i] = "".join(sentences)
                        injected = True
                        break
                if injected:
                    break

        return "\n\n".join(paragraphs)

    def _inject_digression(self, text: str) -> str:
        """脱線を強調する（固定フレーズは挿入しない）"""
        paragraphs = text.split("\n\n")

        if len(paragraphs) < 3:
            return text

        mid_point = len(paragraphs) // 2
        candidates = [
            (i, p) for i, p in enumerate(paragraphs)
            if i >= max(1, mid_point - 1)
            and not p.strip().startswith("##")
            and len(p) > 80
        ]
        if not candidates:
            return text

        idx, para = random.choice(candidates)
        sentences = [s for s in re.split(r'(?<=[。！？])', para) if s]
        if len(sentences) < 2:
            return text

        dig_idx = None
        for s_idx, sent in enumerate(sentences):
            if any(m in sent for m in HUMANITY_MARKERS["digression"]):
                dig_idx = s_idx
                break
        if dig_idx is None:
            return text

        dig_sent = sentences[dig_idx]
        before = "".join(sentences[:dig_idx]).strip()
        after = "".join(sentences[dig_idx + 1:]).strip()

        new_paragraphs = []
        if before:
            new_paragraphs.append(before)
        new_paragraphs.append(dig_sent.strip())
        if after:
            new_paragraphs.append(after)

        paragraphs[idx] = "\n\n".join(new_paragraphs)
        return "\n\n".join(paragraphs)

    def get_improvement_suggestions(self, text: str) -> List[str]:
        """人間味改善の提案を返す"""
        score = self.analyze(text)
        suggestions = []

        if score.self_correction < 0.2:
            suggestions.append(
                "「というか」「言い換えると」などの言い直しを加えると自然になります"
            )

        if score.uncertainty < 0.15:
            suggestions.append(
                "「たぶん」「〜だと思う」などの曖昧表現を適度に入れてください"
            )

        if score.casual_break < 0.15:
            suggestions.append(
                "「〜ですね」「〜ますよね」のような柔らかい文末を適度に混ぜると親しみが出ます"
            )

        if score.digression < 0.1 and len(text) > 1500:
            suggestions.append(
                "「ちなみに〜」で少し脱線して「話を戻すと」で戻ると人間らしくなります"
            )

        return suggestions


def calculate_humanity_score(text: str) -> float:
    """テキストの人間味スコアを計算するヘルパー関数"""
    phase = Phase3Humanity()
    score = phase.analyze(text)
    return score.total
