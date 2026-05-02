"""Phase 8: Platform - note/LinkedIn最適化

プラットフォーム固有の最適化を行うモジュール。
note向けとLinkedIn向けで異なるフォーマット、文字数、表現に調整。
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class Platform(Enum):
    """サポートするプラットフォーム"""
    NOTE = "note"
    LINKEDIN = "linkedin"


@dataclass
class PlatformConfig:
    """プラットフォーム設定"""

    name: str
    max_chars: Optional[int]  # None = 制限なし
    min_chars: Optional[int]
    use_markdown: bool
    use_emoji: bool
    emoji_style: str  # "none", "minimal", "moderate"
    cta_style: str  # "casual", "professional"


# プラットフォーム設定
PLATFORM_CONFIGS: Dict[Platform, PlatformConfig] = {
    Platform.NOTE: PlatformConfig(
        name="note",
        max_chars=None,
        min_chars=None,
        use_markdown=True,
        use_emoji=False,
        emoji_style="none",
        cta_style="casual",
    ),
    Platform.LINKEDIN: PlatformConfig(
        name="linkedin",
        max_chars=1568,
        min_chars=387,
        use_markdown=False,
        use_emoji=True,
        emoji_style="moderate",
        cta_style="professional",
    ),
}

# note用CTA
NOTE_CTA_PATTERNS: List[str] = [
    "この記事が少しでも参考になれば、スキをぽちっと押してくれると嬉しいです。",
    "違う見方があれば、コメントで教えてください。議論できると助かります。",
    "次も読んでもらえると励みになります。フォローも気が向いたらぜひ。",
    "読んでくれてありがとう。感想があれば気軽にコメントください。",
]

# LinkedIn用CTA
LINKEDIN_CTA_PATTERNS: List[str] = [
    "💡 この投稿が参考になったら、いいね＆保存をお願いします！",
    "🔔 フォローしていただくと、最新の投稿をお届けします。",
    "💬 ご意見やご質問があれば、コメント欄でお聞かせください。",
    "📩 もっと詳しく話したい方はDMでお気軽にどうぞ！",
    "👆 この投稿が役立ったら、ぜひシェアしてください！",
]

# LinkedIn用セクション絵文字
LINKEDIN_SECTION_EMOJI: List[str] = [
    "📌", "💡", "🔔", "✅", "📊", "🎯", "💪", "🚀",
]


class Phase8Platform:
    """Phase 8: プラットフォーム最適化処理"""

    def __init__(self, platform: Platform = Platform.NOTE):
        """
        Args:
            platform: 対象プラットフォーム
        """
        self.platform = platform
        self.config = PLATFORM_CONFIGS[platform]

    def process(
        self,
        text: str,
        hashtags: Optional[str] = None,
        custom_cta: Optional[str] = None,
    ) -> str:
        """テキストをプラットフォーム向けに最適化する

        Args:
            text: 入力テキスト
            hashtags: ハッシュタグ（スペース区切り）
            custom_cta: カスタムCTA（指定しない場合はランダム選択）

        Returns:
            最適化されたテキスト
        """
        if not text:
            return ""

        if self.platform == Platform.NOTE:
            return self._optimize_for_note(text, hashtags, custom_cta)
        elif self.platform == Platform.LINKEDIN:
            return self._optimize_for_linkedin(text, hashtags, custom_cta)
        else:
            return text

    def _optimize_for_note(
        self,
        text: str,
        hashtags: Optional[str] = None,
        custom_cta: Optional[str] = None,
    ) -> str:
        """note向けに最適化"""
        result = text

        # Markdownはそのまま維持

        # CTAを追加（末尾になければ）
        cta = custom_cta or random.choice(NOTE_CTA_PATTERNS)
        if not any(cta_part in result for cta_part in ["スキ", "フォロー", "コメント"]):
            result = f"{result.rstrip()}\n\n---\n\n{cta}"

        # ハッシュタグを追加
        if hashtags:
            normalized_tags = self._normalize_hashtags(hashtags)
            result = f"{result.rstrip()}\n\n{normalized_tags}"

        return result

    def _optimize_for_linkedin(
        self,
        text: str,
        hashtags: Optional[str] = None,
        custom_cta: Optional[str] = None,
    ) -> str:
        """LinkedIn向けに最適化"""
        result = text

        # Step 1: Markdownをプレーンテキストに変換
        result = self._convert_markdown_to_plain(result)

        # Step 2: 絵文字でセクションを装飾
        result = self._add_section_emoji(result)

        # Step 3: 文字数制限に合わせて調整
        result = self._adjust_length(result)

        # Step 4: CTAを追加
        cta = custom_cta or random.choice(LINKEDIN_CTA_PATTERNS)
        result = f"{result.rstrip()}\n\n{cta}"

        # Step 5: ハッシュタグを追加（3〜5個に制限）
        if hashtags:
            tags = hashtags.split()[:5]
            tag_str = " ".join(tags)
            result = f"{result.rstrip()}\n\n{tag_str}"

        # 最終的な文字数チェック
        if self.config.max_chars and len(result) > self.config.max_chars:
            result = self._trim_to_limit(result, self.config.max_chars)

        return result

    def _convert_markdown_to_plain(self, text: str) -> str:
        """MarkdownをLinkedIn向けプレーンテキストに変換"""
        result = text

        # 見出しを絵文字付きテキストに
        result = re.sub(r'^## (.+)$', r'📌 \1', result, flags=re.MULTILINE)
        result = re.sub(r'^### (.+)$', r'▸ \1', result, flags=re.MULTILINE)

        # 太字を【】に
        result = re.sub(r'\*\*(.+?)\*\*', r'【\1】', result)

        # リストをブレットに
        result = re.sub(r'^- ', '• ', result, flags=re.MULTILINE)
        result = re.sub(r'^\* ', '• ', result, flags=re.MULTILINE)

        # 水平線を除去
        result = re.sub(r'^---+$', '', result, flags=re.MULTILINE)

        # リンクをテキストのみに
        result = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', result)

        return result

    def _add_section_emoji(self, text: str) -> str:
        """セクションに絵文字を追加（既になければ）"""
        lines = text.split("\n")
        result_lines = []
        emoji_idx = 0

        for line in lines:
            # 既に絵文字で始まっている行はスキップ
            if line.strip() and not self._starts_with_emoji(line):
                # 段落の冒頭（空行の後の非空行）かつ見出し的な短い行
                if len(line.strip()) < 50 and not line.startswith("•"):
                    # 一定確率で絵文字を追加（過剰にならないよう）
                    pass  # 既に_convert_markdown_to_plainで追加済み

            result_lines.append(line)

        return "\n".join(result_lines)

    def _starts_with_emoji(self, text: str) -> bool:
        """テキストが絵文字で始まるかチェック"""
        if not text:
            return False
        # 簡易的な絵文字検出
        emoji_pattern = r'^[\U0001F300-\U0001F9FF\U00002600-\U000027BF]'
        return bool(re.match(emoji_pattern, text.strip()))

    def _adjust_length(self, text: str) -> str:
        """文字数を調整する"""
        if not self.config.max_chars:
            return text

        if len(text) <= self.config.max_chars:
            return text

        # 目標文字数（CTAとハッシュタグ用に余裕を持たせる）
        target = self.config.max_chars - 150

        return self._trim_to_limit(text, target)

    def _trim_to_limit(self, text: str, limit: int) -> str:
        """指定した文字数に収める"""
        if len(text) <= limit:
            return text

        trimmed = text[:limit]

        # 可能なら文末で切る
        last_break = max(
            trimmed.rfind("。"),
            trimmed.rfind("！"),
            trimmed.rfind("？"),
            trimmed.rfind("\n"),
        )

        # 最低でも60%は残す
        min_length = int(limit * 0.6)
        if last_break >= min_length:
            trimmed = trimmed[:last_break + 1]
        else:
            trimmed = trimmed.rstrip() + "..."

        return trimmed

    def _normalize_hashtags(self, hashtags: str) -> str:
        """ハッシュタグを正規化する"""
        tags = re.findall(r"#\S+", hashtags)

        cleaned = []
        for tag in tags:
            # 記号を除去
            tag = re.sub(r"[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF#]+", "", tag)
            if len(tag) > 1:
                cleaned.append(tag)

        # プラットフォームに応じた数に制限
        if self.platform == Platform.LINKEDIN:
            cleaned = cleaned[:5]
        else:
            cleaned = cleaned[:6]

        return " ".join(cleaned)

    def get_cta(self) -> str:
        """プラットフォームに適したCTAを取得"""
        if self.platform == Platform.NOTE:
            return random.choice(NOTE_CTA_PATTERNS)
        elif self.platform == Platform.LINKEDIN:
            return random.choice(LINKEDIN_CTA_PATTERNS)
        return ""

    def analyze(self, text: str) -> Dict:
        """テキストのプラットフォーム適合性を分析"""
        char_count = len(text)

        result = {
            "platform": self.platform.value,
            "char_count": char_count,
            "within_limit": True,
            "has_markdown": bool(re.search(r'\*\*|^##|^- ', text, re.MULTILINE)),
            "has_emoji": self._starts_with_emoji(text) or bool(re.search(r'[\U0001F300-\U0001F9FF]', text)),
            "has_cta": any(
                kw in text for kw in ["スキ", "フォロー", "いいね", "シェア", "コメント"]
            ),
            "has_hashtags": "#" in text,
        }

        if self.config.max_chars:
            result["within_limit"] = char_count <= self.config.max_chars
            result["over_by"] = max(0, char_count - self.config.max_chars)

        if self.config.min_chars:
            result["meets_minimum"] = char_count >= self.config.min_chars
            result["under_by"] = max(0, self.config.min_chars - char_count)

        return result


def optimize_for_note(text: str, hashtags: Optional[str] = None) -> str:
    """note向けに最適化するヘルパー関数"""
    optimizer = Phase8Platform(Platform.NOTE)
    return optimizer.process(text, hashtags)


def optimize_for_linkedin(text: str, hashtags: Optional[str] = None) -> str:
    """LinkedIn向けに最適化するヘルパー関数"""
    optimizer = Phase8Platform(Platform.LINKEDIN)
    return optimizer.process(text, hashtags)
