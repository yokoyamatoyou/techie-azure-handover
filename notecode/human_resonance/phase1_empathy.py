"""Phase 1: Empathy - 共感注入

「この人、わかってる」と感じさせるための共感要素を注入するモジュール。
感情心理学、ナラトロジー、語用論の知見を活用。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class EmpathyScore:
    """共感スコアを表すデータクラス"""

    vulnerability: float = 0.0  # 脆弱性の開示度
    mirror: float = 0.0  # 感情ミラーリング度
    direct_address: float = 0.0  # 読者への直接呼びかけ度
    self_disclosure: float = 0.0  # 自己開示度
    total: float = 0.0  # 総合スコア

    def calculate_total(self) -> float:
        """総合スコアを計算"""
        weights = {
            "vulnerability": 0.3,
            "mirror": 0.25,
            "direct_address": 0.2,
            "self_disclosure": 0.25,
        }
        self.total = (
            self.vulnerability * weights["vulnerability"]
            + self.mirror * weights["mirror"]
            + self.direct_address * weights["direct_address"]
            + self.self_disclosure * weights["self_disclosure"]
        )
        return self.total


# 共感マーカーの定義
EMPATHY_MARKERS: Dict[str, List[str]] = {
    # 脆弱性の開示（弱さを見せる）
    "vulnerability": [
        "失敗", "間違", "恥ずかし", "不安", "迷", "悩",
        "うまくいかな", "できなかった", "わからなかった",
        "苦労", "困った", "挫折", "諦め", "落ち込",
    ],
    # 感情ミラーリング（読者の感情を言語化）
    "mirror": [
        "ですよね", "ありますよね", "わかります", "ですもんね",
        "感じますよね", "思いますよね", "ありますもんね",
        "つらいですよね", "大変ですよね", "イライラ", "モヤモヤ",
    ],
    # 自己開示（本音を見せる）
    "self_disclosure": [
        "正直", "実は", "本音", "告白すると", "白状すると",
        "ぶっちゃけ", "本当のことを言うと", "隠さずに言うと",
        "打ち明けると", "内緒ですが",
    ],
    # 読者への直接呼びかけ
    "direct_address": [
        "あなた", "皆さん", "経験ありませんか", "思いませんか",
        "感じたことは", "覚えがある", "心当たり",
        "どうでしょう", "いかがですか",  # ただし文末の定型句は別途除外
    ],
}

class Phase1Empathy:
    """Phase 1: 共感注入処理"""

    def __init__(self, pronoun: str = "私"):
        self.pronoun = pronoun

    def process(self, text: str, target_score: float = 0.5) -> str:
        """テキストに共感要素を注入する

        Args:
            text: 入力テキスト
            target_score: 目標とする共感スコア（0.0〜1.0）

        Returns:
            共感要素が注入されたテキスト
        """
        if not text:
            return ""

        # 現在の共感スコアを分析
        current_score = self.analyze(text)

        # 目標スコアに達していれば何もしない
        if current_score.total >= target_score:
            return text

        result = text

        # スコアが低い要素を強化（固定フレーズは挿入せず、既存文の配置のみ調整）
        if current_score.vulnerability < 0.3:
            result = self._inject_vulnerability(result)

        if current_score.mirror < 0.3:
            result = self._inject_mirror(result)

        if current_score.direct_address < 0.2:
            result = self._inject_direct_address(result)

        return result

    def analyze(self, text: str) -> EmpathyScore:
        """テキストの共感スコアを分析する"""
        if not text:
            return EmpathyScore()

        text_len = len(text)
        score = EmpathyScore()

        # 各カテゴリのマーカー出現をカウント
        for category, markers in EMPATHY_MARKERS.items():
            count = sum(1 for marker in markers if marker in text)
            # 正規化（テキスト長1000文字あたりのスコア）
            normalized = min(1.0, count * 1000 / max(text_len, 1) / 5)

            if category == "vulnerability":
                score.vulnerability = normalized
            elif category == "mirror":
                score.mirror = normalized
            elif category == "self_disclosure":
                score.self_disclosure = normalized
            elif category == "direct_address":
                score.direct_address = normalized

        score.calculate_total()
        return score

    def _inject_vulnerability(self, text: str) -> str:
        """脆弱性の開示を強調する（固定フレーズは挿入しない）"""
        paragraphs = text.split("\n\n")

        if len(paragraphs) < 2:
            return text

        # 最初の本文段落を特定
        first_content_idx = None
        for i, p in enumerate(paragraphs):
            if not p.strip().startswith("##"):
                first_content_idx = i
                break
        if first_content_idx is None:
            return text

        # 既存の脆弱性文を探して先頭段落に移動
        for i, para in enumerate(paragraphs):
            if i == first_content_idx:
                continue
            if para.strip().startswith("##"):
                continue
            sentences = [s for s in re.split(r'(?<=[。！？])', para) if s]
            for s_idx, sent in enumerate(sentences):
                if any(m in sent for m in EMPATHY_MARKERS["vulnerability"]):
                    # 元の段落から削除
                    sentences.pop(s_idx)
                    if sentences:
                        paragraphs[i] = "".join(sentences)
                    else:
                        paragraphs[i] = ""
                    # 先頭段落の2文目に挿入（本文の内容のみ移動）
                    lead_para = paragraphs[first_content_idx]
                    lead_sents = [s for s in re.split(r'(?<=[。！？])', lead_para) if s]
                    insert_at = 1 if len(lead_sents) >= 1 else 0
                    lead_sents.insert(insert_at, sent)
                    paragraphs[first_content_idx] = "".join(lead_sents)
                    # 空段落を除去
                    return "\n\n".join(p for p in paragraphs if p.strip())

        return text

    def _inject_mirror(self, text: str) -> str:
        """感情ミラーリングを強調する（固定フレーズは挿入しない）"""
        paragraphs = text.split("\n\n")

        for i, para in enumerate(paragraphs):
            if para.strip().startswith("##"):
                continue
            sentences = [s for s in re.split(r'(?<=[。！？])', para) if s]
            mirror_idx = None
            for s_idx, sent in enumerate(sentences):
                if any(m in sent for m in EMPATHY_MARKERS["mirror"]):
                    mirror_idx = s_idx
                    break
            if mirror_idx is None:
                continue
            # ミラー文を段落末に移動
            if mirror_idx != len(sentences) - 1:
                mirror_sent = sentences.pop(mirror_idx)
                sentences.append(mirror_sent)
                paragraphs[i] = "".join(sentences)
            break

        return "\n\n".join(paragraphs)

    def _inject_direct_address(self, text: str) -> str:
        """読者への直接呼びかけを強調する（固定フレーズは挿入しない）"""
        paragraphs = text.split("\n\n")

        if len(paragraphs) < 2:
            return text

        for i, para in enumerate(paragraphs):
            if para.strip().startswith("##"):
                continue
            sentences = [s for s in re.split(r'(?<=[。！？])', para) if s]
            addr_idx = None
            for s_idx, sent in enumerate(sentences):
                if any(m in sent for m in EMPATHY_MARKERS["direct_address"]):
                    addr_idx = s_idx
                    break
            if addr_idx is None:
                continue
            # 呼びかけ文を段落末に移動
            if addr_idx != len(sentences) - 1:
                addr_sent = sentences.pop(addr_idx)
                sentences.append(addr_sent)
                paragraphs[i] = "".join(sentences)
            break

        return "\n\n".join(paragraphs)

    def get_improvement_suggestions(self, text: str) -> List[str]:
        """共感要素の改善提案を返す"""
        score = self.analyze(text)
        suggestions = []

        if score.vulnerability < 0.3:
            suggestions.append(
                "冒頭付近で「失敗談」や「迷った経験」を開示すると共感が生まれやすくなります"
            )

        if score.mirror < 0.3:
            suggestions.append(
                "読者の感情を言語化するフレーズ（「〜ですよね」「わかります」）を追加してください"
            )

        if score.direct_address < 0.2:
            suggestions.append(
                "読者に直接問いかける文（「経験ありませんか？」）を1〜2箇所入れてください"
            )

        if score.self_disclosure < 0.2:
            suggestions.append(
                "「正直」「実は」で始まる本音の開示を加えると信頼感が増します"
            )

        return suggestions


def calculate_empathy_score(text: str) -> float:
    """テキストの共感スコアを計算するヘルパー関数"""
    phase = Phase1Empathy()
    score = phase.analyze(text)
    return score.total
