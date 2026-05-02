"""Phase 2: Curiosity - 興味設計

「続きが読みたい」と感じさせるための構造を設計するモジュール。
認知心理学（情報ギャップ理論、ツァイガルニク効果）、修辞学、談話分析の知見を活用。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from human_resonance.style_policy import CURIOSITY_MARKERS


@dataclass
class CuriosityScore:
    """興味スコアを表すデータクラス"""

    information_gap: float = 0.0  # 情報ギャップの活用度
    pattern_break: float = 0.0  # パターン破壊の度合い
    open_loop: float = 0.0  # オープンループの活用度
    tension_release: float = 0.0  # 緊張と解放の構造
    total: float = 0.0

    def calculate_total(self) -> float:
        """総合スコアを計算"""
        weights = {
            "information_gap": 0.3,
            "pattern_break": 0.25,
            "open_loop": 0.2,
            "tension_release": 0.25,
        }
        self.total = (
            self.information_gap * weights["information_gap"]
            + self.pattern_break * weights["pattern_break"]
            + self.open_loop * weights["open_loop"]
            + self.tension_release * weights["tension_release"]
        )
        return self.total


# 興味を引く構造パターン
CURIOSITY_STRUCTURES: Dict[str, Dict[str, str]] = {
    # 数字を使った情報ギャップ
    "numbered_gap": {
        "pattern": r"\d+つの(理由|ポイント|秘訣|方法|コツ)",
        "description": "「3つの理由」のような数字でリスト化を予告",
    },
    # 逆説的な導入
    "paradox_intro": {
        "pattern": r"(実は|意外にも|驚くべきことに).{0,20}(ない|逆|違う)",
        "description": "常識を覆す導入",
    },
    # 問いかけ形式
    "question_hook": {
        "pattern": r".+[？?]$",
        "description": "疑問形で読者の思考を促す",
    },
}


class Phase2Curiosity:
    """Phase 2: 興味設計処理"""

    def __init__(self):
        pass

    def process(self, text: str, target_score: float = 0.5) -> str:
        """テキストに興味を引く構造を追加する

        Args:
            text: 入力テキスト
            target_score: 目標とする興味スコア（0.0〜1.0）

        Returns:
            興味構造が強化されたテキスト
        """
        if not text:
            return ""

        current_score = self.analyze(text)

        if current_score.total >= target_score:
            return text

        result = text

        # スコアが低い要素を強化
        if current_score.information_gap < 0.3:
            result = self._enhance_information_gap(result)

        if current_score.pattern_break < 0.2:
            result = self._inject_pattern_break(result)

        if current_score.tension_release < 0.3:
            result = self._enhance_tension_release(result)

        return result

    def analyze(self, text: str) -> CuriosityScore:
        """テキストの興味スコアを分析する"""
        if not text:
            return CuriosityScore()

        text_len = len(text)
        score = CuriosityScore()

        # 各カテゴリのマーカー出現をカウント
        for category, markers in CURIOSITY_MARKERS.items():
            count = sum(1 for marker in markers if marker in text)
            normalized = min(1.0, count * 1000 / max(text_len, 1) / 4)

            if category == "information_gap":
                score.information_gap = normalized
            elif category == "pattern_break":
                score.pattern_break = normalized
            elif category == "open_loop":
                score.open_loop = normalized
            elif category == "tension_release":
                score.tension_release = normalized

        # 構造パターンのボーナス
        for name, struct in CURIOSITY_STRUCTURES.items():
            if re.search(struct["pattern"], text):
                score.information_gap = min(1.0, score.information_gap + 0.1)

        score.calculate_total()
        return score

    def _enhance_information_gap(self, text: str) -> str:
        """情報ギャップを強調する（固定フレーズは挿入しない）"""
        paragraphs = text.split("\n\n")

        for i, para in enumerate(paragraphs):
            if para.strip().startswith("##"):
                continue

            sentences = [s for s in re.split(r'(?<=[。！？])', para) if s]
            if len(sentences) < 2:
                break

            # 既存の情報ギャップ文があれば前半に移動
            gap_idx = None
            for s_idx, sent in enumerate(sentences):
                if any(m in sent for m in CURIOSITY_MARKERS["information_gap"]):
                    gap_idx = s_idx
                    break
            if gap_idx is None or gap_idx <= 1:
                break

            gap_sent = sentences.pop(gap_idx)
            sentences.insert(1, gap_sent)
            paragraphs[i] = "".join(sentences)
            break

        return "\n\n".join(paragraphs)

    def _inject_pattern_break(self, text: str) -> str:
        """パターン破壊を強調する（固定フレーズは挿入しない）"""
        paragraphs = text.split("\n\n")

        mid_point = len(paragraphs) // 2

        for i in range(mid_point, min(mid_point + 3, len(paragraphs))):
            para = paragraphs[i]
            if para.strip().startswith("##"):
                continue

            sentences = [s for s in re.split(r'(?<=[。！？])', para) if s]
            if len(sentences) < 2:
                continue

            pb_idx = None
            for s_idx, sent in enumerate(sentences):
                if any(m in sent for m in CURIOSITY_MARKERS["pattern_break"]):
                    pb_idx = s_idx
                    break
            if pb_idx is None or pb_idx == 0:
                continue

            pb_sent = sentences.pop(pb_idx)
            sentences.insert(0, pb_sent)
            paragraphs[i] = "".join(sentences)
            break

        return "\n\n".join(paragraphs)

    def _enhance_tension_release(self, text: str) -> str:
        """緊張と解放の構造を整える（固定フレーズは挿入しない）"""
        paragraphs = text.split("\n\n")

        problem_markers = ["問題は", "課題は", "困った", "難し"]
        solution_markers = ["解決策は", "答えは", "そこで", "ポイントは"]

        for i, para in enumerate(paragraphs):
            if para.strip().startswith("##"):
                continue

            sentences = [s for s in re.split(r'(?<=[。！？])', para) if s]
            if len(sentences) < 2:
                continue

            problem_sents = [s for s in sentences if any(m in s for m in problem_markers)]
            solution_sents = [s for s in sentences if any(m in s for m in solution_markers)]

            if not problem_sents or not solution_sents:
                continue

            # 既に問題→解決の順ならそのまま
            first_problem = min(sentences.index(s) for s in problem_sents)
            first_solution = min(sentences.index(s) for s in solution_sents)
            if first_problem < first_solution:
                continue

            # 問題文を前に、解決文を後ろに寄せる
            reordered: List[str] = []
            reordered.extend(problem_sents)
            reordered.extend([s for s in sentences if s not in problem_sents and s not in solution_sents])
            reordered.extend(solution_sents)
            paragraphs[i] = "".join(reordered)
            break

        return "\n\n".join(paragraphs)

    def detect_curiosity_structure(self, text: str) -> Dict[str, bool]:
        """テキストに含まれる興味構造を検出する"""
        structures = {}

        for name, struct in CURIOSITY_STRUCTURES.items():
            structures[name] = bool(re.search(struct["pattern"], text))

        return structures

    def get_improvement_suggestions(self, text: str) -> List[str]:
        """興味構造の改善提案を返す"""
        score = self.analyze(text)
        suggestions = []

        if score.information_gap < 0.3:
            suggestions.append(
                "「3つの理由」「ポイントは」のような情報ギャップを作ると読み進めたくなります"
            )

        if score.pattern_break < 0.2:
            suggestions.append(
                "「しかし」「ところが」で予想を裏切る展開を入れると興味を維持できます"
            )

        if score.open_loop < 0.2:
            suggestions.append(
                "「詳しくは後ほど」のような伏線を張ると最後まで読んでもらいやすくなります"
            )

        if score.tension_release < 0.3:
            suggestions.append(
                "問題提起→解決の流れを明確にすると読者の満足感が高まります"
            )

        return suggestions


def calculate_curiosity_score(text: str) -> float:
    """テキストの興味スコアを計算するヘルパー関数"""
    phase = Phase2Curiosity()
    score = phase.analyze(text)
    return score.total
