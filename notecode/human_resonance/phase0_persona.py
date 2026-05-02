"""Phase 0: Persona Lock - 一人称・口癖の固定

記事全体で一貫した「人格」を維持するためのモジュール。
一人称の統一と、個人の語彙癖（口癖）を設定・注入する。
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Persona:
    """執筆者のペルソナ（人格）を定義するデータクラス"""

    # 一人称（記事全体で統一）
    pronoun: str = "私"

    # 口癖（2〜3個を自然に散りばめる）
    verbal_tics: List[str] = field(default_factory=list)

    # 視点タイプ
    perspective: str = "auto"

    # 文体の傾向
    tone: str = "polite"  # polite, casual, formal

    # 感情表現の頻度（0.0〜1.0）
    emotionality: float = 0.5


# 視点タイプごとのデフォルト設定
PERSPECTIVE_DEFAULTS: Dict[str, Dict] = {
    "blogger": {
        "pronoun": "わたし",
        "verbal_tics": ["正直なところ", "実感として", "個人的には"],
        "tone": "casual",
        "emotionality": 0.7,
    },
    "expert": {
        "pronoun": "私",
        "verbal_tics": ["実務で見ると", "見落としやすいのは", "確認したいのは"],
        "tone": "polite",
        "emotionality": 0.3,
    },
    "corporate": {
        "pronoun": "私たち",
        # 文中挿入でも崩れにくい接続型の口癖を採用する。
        "verbal_tics": ["実務では", "要点としては", "背景としては"],
        "tone": "polite",
        "emotionality": 0.4,
    },
    "educator": {
        "pronoun": "私",
        "verbal_tics": ["先に押さえたいのは", "覚えておきたい点は", "よくあるのは"],
        "tone": "polite",
        "emotionality": 0.5,
    },
    "journalist": {
        "pronoun": "",  # 一人称を使わない
        "verbal_tics": ["取材によると", "関係者によれば", "明らかになったのは"],
        "tone": "formal",
        "emotionality": 0.2,
    },
    "friend": {
        "pronoun": "わたし",
        "verbal_tics": ["ねえ、", "実はさ、", "知ってる？"],
        "tone": "casual",
        "emotionality": 0.8,
    },
}

# 一人称の変換マッピング（統一用）
# NOTE: 長い表現を優先して置換するため、正規化は正規表現で行う。
# NOTE: 「当社/弊社/自社」は組織名詞としても使われるため、ここでは置換しない。
PRONOUN_VARIANTS: Dict[str, List[str]] = {
    "僕": ["ぼく", "ボク"],
    "僕たち": ["僕達", "僕ら", "ぼくたち", "ぼく達", "ぼくら"],
    "私": ["わたし", "ワタシ"],
    "私たち": ["私達", "わたしたち", "わたし達", "我々"],
    "わたし": ["ワタシ"],
}


class Phase0Persona:
    """Phase 0: ペルソナ固定処理"""

    def __init__(self, persona: Optional[Persona] = None):
        self.persona = persona or Persona()

    @classmethod
    def from_perspective(cls, perspective: str) -> "Phase0Persona":
        """視点タイプからPhase0Personaインスタンスを生成"""
        defaults = PERSPECTIVE_DEFAULTS.get(perspective, PERSPECTIVE_DEFAULTS["blogger"])
        persona = Persona(
            pronoun=defaults["pronoun"],
            verbal_tics=defaults["verbal_tics"].copy(),
            perspective=perspective,
            tone=defaults["tone"],
            emotionality=defaults["emotionality"],
        )
        return cls(persona)

    def process(self, text: str) -> str:
        """テキストにペルソナを適用する

        1. 一人称の統一
        2. 口癖の自然な注入（既存の口癖がない場合）
        """
        if not text:
            return ""

        result = text

        # Step 1: 一人称の統一
        result = self._unify_pronoun(result)

        # Step 2: 口癖の注入（必要に応じて）
        result = self._inject_verbal_tics(result)

        return result

    def _unify_pronoun(self, text: str) -> str:
        """一人称を統一する"""
        if not self.persona.pronoun:
            return text  # ジャーナリスト視点など一人称不使用の場合

        result = text
        target_pronoun = self.persona.pronoun

        # 置換対象のトークンを収集（長いものを優先）
        tokens: List[str] = []
        for pronoun, variants in PRONOUN_VARIANTS.items():
            tokens.append(pronoun)
            tokens.extend(variants)
        tokens = sorted(set(tokens), key=len, reverse=True)

        # 正規表現で一括正規化（部分一致の誤変換を回避）
        pattern = re.compile("|".join(re.escape(t) for t in tokens))

        def _repl(match: re.Match) -> str:
            token = match.group(0)
            if token == target_pronoun:
                return token
            return target_pronoun

        result = pattern.sub(_repl, result)
        return result

    def _inject_verbal_tics(self, text: str) -> str:
        """口癖を自然に注入する

        既に口癖が含まれている場合はスキップ。
        含まれていない場合、適切な位置に1〜2個挿入。
        """
        if not self.persona.verbal_tics:
            return text

        # 既存の口癖をカウント
        existing_count = sum(1 for tic in self.persona.verbal_tics if tic in text)

        # 既に2個以上あればスキップ
        if existing_count >= 2:
            return text

        # 注入が必要な数
        needed = min(2 - existing_count, len(self.persona.verbal_tics))
        if needed <= 0:
            return text

        # 使用可能な口癖を選択
        available_tics = [tic for tic in self.persona.verbal_tics if tic not in text]
        if not available_tics:
            return text

        selected_tics = random.sample(available_tics, min(needed, len(available_tics)))

        # 段落の冒頭に自然に挿入
        result = self._insert_tics_naturally(text, selected_tics)

        return result

    def _insert_tics_naturally(self, text: str, tics: List[str]) -> str:
        """口癖を自然な位置に挿入する"""
        if not tics:
            return text

        paragraphs = text.split("\n\n")

        if len(paragraphs) < 2:
            return text

        # 挿入対象の段落インデックス（冒頭と末尾は避ける）
        candidate_indices = list(range(1, len(paragraphs) - 1))

        if not candidate_indices:
            return text

        # ランダムに段落を選んで挿入
        for tic in tics:
            if not candidate_indices:
                break

            idx = random.choice(candidate_indices)
            candidate_indices.remove(idx)

            paragraph = paragraphs[idx]

            # 見出し行はスキップ
            if paragraph.strip().startswith("##"):
                continue

            # 段落の最初の文の後に挿入を試みる
            sentences = re.split(r'(?<=[。！？])', paragraph, maxsplit=1)

            if len(sentences) >= 2:
                # 2文目の前に口癖を挿入
                paragraphs[idx] = f"{sentences[0]}{tic}、{sentences[1]}"
            else:
                # 1文しかない場合は冒頭に
                paragraphs[idx] = f"{tic}、{paragraph}"

        return "\n\n".join(paragraphs)

    def analyze(self, text: str) -> Dict[str, any]:
        """テキストのペルソナ一貫性を分析する"""
        if not text:
            return {"consistent": True, "issues": []}

        issues = []

        # 一人称の一貫性チェック
        pronoun_issues = self._check_pronoun_consistency(text)
        issues.extend(pronoun_issues)

        # 口癖の存在チェック
        tic_count = sum(1 for tic in self.persona.verbal_tics if tic in text)
        if tic_count == 0 and len(text) > 500:
            issues.append("口癖が一度も使用されていません")

        return {
            "consistent": len(issues) == 0,
            "issues": issues,
            "pronoun_count": text.count(self.persona.pronoun),
            "verbal_tic_count": tic_count,
        }

    def _check_pronoun_consistency(self, text: str) -> List[str]:
        """一人称の一貫性をチェック"""
        issues = []
        target = self.persona.pronoun

        if not target:
            return issues

        for pronoun, variants in PRONOUN_VARIANTS.items():
            if pronoun == target:
                continue

            if pronoun in text:
                issues.append(f"一人称の不統一: 「{pronoun}」が使用されています（期待: 「{target}」）")

            for variant in variants:
                if variant in text:
                    issues.append(f"一人称の不統一: 「{variant}」が使用されています（期待: 「{target}」）")

        return issues


def create_persona_from_context(
    perspective: str,
    custom_tics: Optional[List[str]] = None,
    pronoun_override: Optional[str] = None,
) -> Persona:
    """コンテキストからペルソナを生成するヘルパー関数"""
    defaults = PERSPECTIVE_DEFAULTS.get(perspective, PERSPECTIVE_DEFAULTS["blogger"])

    return Persona(
        pronoun=pronoun_override or defaults["pronoun"],
        verbal_tics=custom_tics or defaults["verbal_tics"].copy(),
        perspective=perspective,
        tone=defaults["tone"],
        emotionality=defaults["emotionality"],
    )
