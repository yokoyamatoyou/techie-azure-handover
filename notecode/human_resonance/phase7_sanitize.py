"""Phase 7: Sanitize - 禁止フレーズ・インジェクション除去

AI特有の定型句、プロンプトインジェクション、不要なメタ情報を除去するモジュール。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from human_resonance.style_policy import (
    AI_LIKE_ENDING_REWRITES,
    AI_LIKE_OPENING_PATTERNS,
    BANNED_PHRASES,
    DISCOURSE_LEADIN_VARIANTS,
    LOGICAL_REQUIRED_OPENING_PREFIXES,
    SUPPRESSIBLE_TEMPLATE_OPENING_PREFIXES,
)


@dataclass
class SanitizeResult:
    """サニタイズ結果を表すデータクラス"""

    original_length: int = 0
    sanitized_length: int = 0
    removed_phrases: List[str] = field(default_factory=list)
    removed_injections: List[str] = field(default_factory=list)
    changes_made: int = 0


# プロンプトインジェクション検出パターン
# 注意: 正常なコンテンツを誤削除しないよう、メタ指示・システムタグに限定
INJECTION_PATTERNS: List[str] = [
    r"AIとしては[、。]",  # 「AIとしては、」のメタ混入（「AIは〜」は正常コンテンツの可能性あり）
    r"出力は.+?のみ[。．]?",  # 「出力は〜のみ」のプロンプト混入
    r"ユーザー指示[：:].+?(?=\n)",  # ユーザー指示ラベルの混入
    r"^(?:Note|注意)[：:].*$",  # メタ注釈の混入（「注：」は広すぎるため除外）
    r"\[(?:内部|システム|指示)\].+?\]",  # 内部指示タグ
    r"出力フォーマット[：:].*?(?=\n|$)",  # 出力形式指示の混入
]

# フォーマット正規化パターン
FORMAT_PATTERNS: Dict[str, str] = {
    r"\n{3,}": "\n\n",  # 過剰な改行を2つに
    r" +\n": "\n",  # 行末の空白を除去
    r"【\s*】": "",  # 空のブラケット
    r"（\s*）": "",  # 空の括弧
    r"「\s*」": "",  # 空の鉤括弧
    r"^\s+$": "",  # 空白のみの行
    r"――": "、",  # R14: ダッシュ（――）をnote記事では使わない
    r"—": "、",  # R14: emダッシュも同様
}

# R14: フリガナ括弧パターン（漢字（ひらがな/カタカナ）→ 漢字のみに）
_RE_FURIGANA = re.compile(r"([\u4e00-\u9fff]{1,6})（([ぁ-ん]{1,12}|[ァ-ヶー]{1,12})）")

# 文末の不自然な句読点: 「。」の直後に「、」「が、」「と、」が来ることはない（人間は文末で。と、を併置しない）
PUNCTUATION_FIX_PATTERNS: List[Tuple[str, str]] = [
    (r"。\s*と、", "と、"),  # 。と、 → と、
    (r"。\s*が、", "が、"),  # 。が、 → が、
    (r"。\s*、", "、"),      # 。、 → 、
]

# AIっぽさ検出パターン（テンプレ感・機械的表現）
AI_NOISE_PATTERNS: Dict[str, Dict] = {
    # 冗長な表現（簡潔に書き換え）
    "verbose_expressions": {
        "patterns": [
            (r"することができます", "できます"),
            (r"することが可能です", "できます"),
            (r"することが重要です", "が大切です"),
            (r"することが必要です", "が必要です"),
            (r"ということが言えます", "と言えます"),
            (r"ということになります", "になります"),
            (r"という点において", "という点で"),
            (r"という観点から見ると", "から見ると"),
            (r"という観点から", "の観点で"),
            (r"において", "で"),
            (r"における", "の"),
            (r"ことに起因している", "ことが原因です"),
            (r"ことが背景にある", "背景にある"),
            # 接続語の語幹破壊を補正（phase5語彙揺らぎの安全網）
            (r"ただながら", "ただ"),
            (r"そのためこそ", "そのため"),
            (r"というわけでこそ", "というわけで"),
            (r"和らげるになります", "和らぐことにつながります"),
            # R35: 7種分散 + 省略候補（句点読点を内包）
            (r"ここで(?:大切|重要|大事)なのは(?:、|,)?\s*", DISCOURSE_LEADIN_VARIANTS),
            (r"ここで押さえたいのは(?:、|,)?\s*", DISCOURSE_LEADIN_VARIANTS),
            # AIらしいカタカナ業務語・定型句は自然な和文へ寄せる
            (r"データドリブン", "データにもとづく"),
            (r"ベストプラクティス", "実践例"),
            (r"最初の一歩", "まず試すこと"),
            (r"さいしょの一歩", "まず試すこと"),
            (r"第一歩", "手始め"),
        ],
        "enabled": True,
    },
    # 過剰に構造的な表現（連続使用を抑制）
    "overly_structured": {
        "patterns": [
            r"(?:第一|1つ目)に.+?(?:第二|2つ目)に.+?(?:第三|3つ目)に",
            r"まず.+?次に.+?そして.+?最後に",
        ],
        "enabled": False,  # 検出のみ（置換はしない）
    },
    # 同じ接続詞の連続（3回以上）
    "repeated_connectors": {
        "connectors": ["そして", "また", "さらに", "しかし", "ただし"],
        "max_consecutive": 2,
        "enabled": True,
    },
}

# 「次の一歩」は禁止せず、頻度だけ抑える（2回目以降を言い換え）。
NEXT_STEP_ALTERNATIVES: Tuple[str, ...] = (
    "次に試すこと",
    "次の手",
    "次に取る行動",
)

# 追加の除去対象（オプション）
OPTIONAL_REMOVALS: Dict[str, List[str]] = {
    "excessive_emoji": [
        r"[😀😃😄😁😆😅🤣😂🙂🙃😉😊😇]{3,}",  # 絵文字3つ以上連続
    ],
    "placeholder": [
        r"\[TODO\]",
        r"\[TBD\]",
        r"\[要確認\]",
        r"\[仮\]",
    ],
    "debug": [
        r"console\.log\(.+?\)",
        r"print\(.+?\)",
        r"DEBUG:",
    ],
}


class Phase7Sanitize:
    """Phase 7: サニタイズ処理"""

    def __init__(
        self,
        remove_emoji_excess: bool = True,
        remove_placeholders: bool = True,
        reduce_ai_noise: bool = True,
        custom_banned_phrases: Optional[List[str]] = None,
    ):
        """
        Args:
            remove_emoji_excess: 過剰な絵文字を除去するか
            remove_placeholders: プレースホルダーを除去するか
            reduce_ai_noise: AIっぽい表現を抑制するか
            custom_banned_phrases: 追加の禁止フレーズ
        """
        self.remove_emoji_excess = remove_emoji_excess
        self.remove_placeholders = remove_placeholders
        self.reduce_ai_noise = reduce_ai_noise
        self.custom_banned_phrases = custom_banned_phrases or []

    def process(self, text: str) -> str:
        """テキストをサニタイズする

        Args:
            text: 入力テキスト

        Returns:
            サニタイズ済みテキスト
        """
        if not text:
            return ""

        result = text

        # Step 1: 禁止フレーズの除去
        result = self._remove_banned_phrases(result)

        # Step 2: プロンプトインジェクションの除去
        result = self._remove_injections(result)

        # Step 3: フォーマットの正規化
        result = self._normalize_format(result)

        # Step 4: オプションの除去
        if self.remove_emoji_excess:
            result = self._remove_excessive_emoji(result)

        if self.remove_placeholders:
            result = self._remove_placeholders(result)

        # Step 5: AIっぽさの抑制
        if self.reduce_ai_noise:
            result = self._reduce_ai_noise(result)

        return result.strip()

    def _remove_banned_phrases(self, text: str) -> str:
        """禁止フレーズを除去する（削除後の孤立句読点も処理）"""
        result = text

        all_banned = BANNED_PHRASES + self.custom_banned_phrases
        # 長いフレーズから先に処理（部分一致の誤削除を防ぐ）
        all_banned_sorted = sorted(all_banned, key=len, reverse=True)

        for phrase in all_banned_sorted:
            if phrase in result:
                result = result.replace(phrase, "")

        # 削除後のクリーンアップ
        # 孤立した助詞+句点を修正: 行頭や空白直後の「は。」「を。」等 → 句点のみ
        # ※「こと。」「もと。」等の正当な文末を破壊しないよう、直前が非文字の場合のみ
        result = re.sub(r'(?<=\s)([はをがにでと])\s*([。！？])', r'\2', result)
        result = re.sub(r'^([はをがにでと])\s*([。！？])', r'\2', result, flags=re.MULTILINE)
        # 句読点の重複を修正: 「。。」→「。」、「、。」→「。」
        result = re.sub(r'[、。]+([。！？])', r'\1', result)
        # 行頭の孤立句読点を除去
        result = re.sub(r'^\s*[。、！？]\s*$', '', result, flags=re.MULTILINE)

        return result

    def _remove_injections(self, text: str) -> str:
        """プロンプトインジェクションを除去する"""
        result = text

        for pattern in INJECTION_PATTERNS:
            result = re.sub(pattern, "", result, flags=re.MULTILINE)

        return result

    def _normalize_format(self, text: str) -> str:
        """フォーマットを正規化する"""
        result = text

        # R14: フリガナ括弧を除去（漢字（ひらがな）→ 漢字のみ）
        result = _RE_FURIGANA.sub(r"\1", result)

        # 文末の不自然な句読点を修正（。の直後の、／が、／と、を削除）
        for pattern, replacement in PUNCTUATION_FIX_PATTERNS:
            result = re.sub(pattern, replacement, result)

        for pattern, replacement in FORMAT_PATTERNS.items():
            result = re.sub(pattern, replacement, result, flags=re.MULTILINE)

        # 見出し後の改行を確保
        result = re.sub(r"(## .+)\n([^\n])", r"\1\n\n\2", result)

        return result

    def _remove_excessive_emoji(self, text: str) -> str:
        """過剰な絵文字を除去する"""
        result = text

        for pattern in OPTIONAL_REMOVALS["excessive_emoji"]:
            result = re.sub(pattern, "", result)

        return result

    def _remove_placeholders(self, text: str) -> str:
        """プレースホルダーを除去する"""
        result = text

        for pattern in OPTIONAL_REMOVALS["placeholder"]:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)

        return result

    def _reduce_ai_noise(self, text: str) -> str:
        """AIっぽい表現を抑制する（冗長表現の簡潔化）"""
        result = text

        # 冗長な表現を簡潔に
        verbose_config = AI_NOISE_PATTERNS.get("verbose_expressions", {})
        if verbose_config.get("enabled", False):
            for pattern, replacement in verbose_config.get("patterns", []):
                if isinstance(replacement, tuple):
                    result = self._replace_with_variants(result, pattern, replacement)
                else:
                    result = re.sub(pattern, replacement, result)

        # 省略時に残る先頭句読点・空白を軽く整える
        result = re.sub(r"([。！？]\s*)[、,]\s*", r"\1", result)
        result = re.sub(r"^\s*[、,]\s*", "", result, flags=re.MULTILINE)
        result = self._trim_connective_openings(result)

        for pattern, replacement in AI_LIKE_ENDING_REWRITES:
            result = re.sub(pattern, replacement, result)

        # 禁止ではなく頻度制御: 「次の一歩」は最初の1回のみ残す
        result = self._soft_limit_phrase_frequency(
            result,
            phrase="次の一歩",
            max_allowed=1,
            replacements=NEXT_STEP_ALTERNATIVES,
        )

        return result

    def _trim_connective_openings(self, text: str, max_openers_per_paragraph: int = 2) -> str:
        """段落内の文頭導入を調整する（必要接続は保持、弱い導入のみ抑制）。"""
        if not text:
            return text

        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        rebuilt: List[str] = []
        for paragraph in paragraphs:
            stripped = paragraph.strip()
            if stripped.startswith("## ") or re.match(r"^\s*(?:-|\*|\d+\.)\s+", stripped):
                rebuilt.append(paragraph)
                continue

            sentences = [s.strip() for s in re.split(r"(?<=[。！？])\s*", paragraph) if s.strip()]
            if len(sentences) <= 1:
                rebuilt.append(paragraph)
                continue

            opener_hits = 0
            prev_opener = ""
            edited: List[str] = []
            for sentence in sentences:
                current = sentence
                opener_removed = False
                opener_text = ""
                for pattern in AI_LIKE_OPENING_PATTERNS:
                    matched = re.match(pattern, current)
                    if not matched:
                        continue
                    opener_text = self._normalize_opening_token(matched.group(0))
                    same_as_prev = bool(opener_text) and opener_text == prev_opener
                    is_logical = self._is_logical_required_opener(opener_text)
                    is_template = self._is_suppressible_template_opener(opener_text)

                    # 論理接続（しかし/ただし等）は優先保持。
                    # 抑制するのはテンプレ導入のみ（連続または過多）。
                    if is_template and (same_as_prev or opener_hits >= max_openers_per_paragraph):
                        candidate = re.sub(pattern, "", current, count=1).lstrip("、, \t")
                        if candidate and not re.match(
                            r"^(?:は|が|を|に|で|と|も|へ|から|まで|だけ|ばかり)(?:[、,]|$)",
                            candidate,
                        ):
                            current = candidate
                            opener_removed = True
                    elif is_template:
                        opener_hits += 1
                    elif is_logical:
                        # 論理接続はカウントしない（必要導入として扱う）
                        pass
                    else:
                        opener_hits += 1
                    break
                if opener_text and not opener_removed:
                    prev_opener = opener_text
                elif not opener_text:
                    prev_opener = ""
                if opener_removed and not current:
                    continue
                edited.append(current or sentence)

            rebuilt.append("".join(edited).strip() if edited else paragraph.strip())

        return "\n\n".join(p for p in rebuilt if p.strip()).strip()

    @staticmethod
    def _normalize_opening_token(token: str) -> str:
        return re.sub(r"[、,\s]+$", "", str(token or "").strip())

    @staticmethod
    def _is_logical_required_opener(token: str) -> bool:
        return any(token.startswith(prefix) for prefix in LOGICAL_REQUIRED_OPENING_PREFIXES)

    @staticmethod
    def _is_suppressible_template_opener(token: str) -> bool:
        return any(token.startswith(prefix) for prefix in SUPPRESSIBLE_TEMPLATE_OPENING_PREFIXES)

    @staticmethod
    def _soft_limit_phrase_frequency(
        text: str,
        phrase: str,
        max_allowed: int,
        replacements: Tuple[str, ...],
    ) -> str:
        """フレーズを禁止せず、規定回数を超えた分だけ言い換える。"""
        if not text or not phrase:
            return text
        max_allowed = max(0, int(max_allowed))
        escaped = re.escape(phrase)
        state = {"count": 0, "rep_idx": 0}

        def _repl(match: re.Match) -> str:
            state["count"] += 1
            if state["count"] <= max_allowed:
                return match.group(0)
            if replacements:
                replacement = replacements[state["rep_idx"] % len(replacements)]
                state["rep_idx"] += 1
                return replacement
            return match.group(0)

        return re.sub(escaped, _repl, text)

    @staticmethod
    def _replace_with_variants(text: str, pattern: str, variants: Tuple[str, ...]) -> str:
        """同一パターンの置換語を循環させて分散する（決定的でテスト可能）。"""
        if not variants:
            return text
        state = {"i": 0}

        def _repl(_: re.Match) -> str:
            current = variants[state["i"] % len(variants)]
            state["i"] += 1
            return current

        return re.sub(pattern, _repl, text)

    def analyze(self, text: str) -> SanitizeResult:
        """テキストを分析し、除去対象を検出する"""
        result = SanitizeResult(original_length=len(text))

        # 禁止フレーズの検出
        all_banned = BANNED_PHRASES + self.custom_banned_phrases
        for phrase in all_banned:
            if phrase in text:
                result.removed_phrases.append(phrase)

        # インジェクションの検出
        for pattern in INJECTION_PATTERNS:
            matches = re.findall(pattern, text, flags=re.MULTILINE)
            result.removed_injections.extend(matches)

        # 変更数を計算
        result.changes_made = len(result.removed_phrases) + len(result.removed_injections)

        # サニタイズ後の長さ
        sanitized = self.process(text)
        result.sanitized_length = len(sanitized)

        return result

    def get_banned_phrases_found(self, text: str) -> List[str]:
        """テキスト内の禁止フレーズを検出する"""
        found = []
        all_banned = BANNED_PHRASES + self.custom_banned_phrases

        for phrase in all_banned:
            if phrase in text:
                found.append(phrase)

        return found

    def get_injections_found(self, text: str) -> List[str]:
        """テキスト内のインジェクションを検出する"""
        found = []

        for pattern in INJECTION_PATTERNS:
            matches = re.findall(pattern, text, flags=re.MULTILINE)
            found.extend(matches)

        return found

    def add_banned_phrase(self, phrase: str) -> None:
        """禁止フレーズを追加する"""
        if phrase not in self.custom_banned_phrases:
            self.custom_banned_phrases.append(phrase)

    def remove_banned_phrase(self, phrase: str) -> bool:
        """禁止フレーズを削除する"""
        if phrase in self.custom_banned_phrases:
            self.custom_banned_phrases.remove(phrase)
            return True
        return False


def sanitize_text(text: str) -> str:
    """テキストをサニタイズするヘルパー関数"""
    sanitizer = Phase7Sanitize()
    return sanitizer.process(text)


def analyze_sanitize_needs(text: str) -> Dict:
    """サニタイズの必要性を分析するヘルパー関数"""
    sanitizer = Phase7Sanitize()
    result = sanitizer.analyze(text)

    return {
        "original_length": result.original_length,
        "sanitized_length": result.sanitized_length,
        "characters_removed": result.original_length - result.sanitized_length,
        "banned_phrases_found": result.removed_phrases,
        "injections_found": result.removed_injections,
        "total_issues": result.changes_made,
    }
