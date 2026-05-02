"""Length-planning helpers for ArticleGenerator."""
from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional, Tuple

from note.article_fetcher import FetchedContent

NOTE_MIN_CHARS = 2500
NOTE_MAX_CHARS = 6500

LENGTH_MODE_PROFILES = {
    "adaptive": {
        "min_chars": 900,
        "max_chars": 5200,
        "section_range": (4, 5),
        "lead_base": 110,
        "lead_span": 70,
        "min_body_chars": 700,
    },
    "short": {
        "min_chars": 700,
        "max_chars": 1800,
        "section_range": (2, 3),
        "lead_base": 95,
        "lead_span": 55,
        "min_body_chars": 380,
    },
    "normal": {
        "min_chars": NOTE_MIN_CHARS,
        "max_chars": NOTE_MAX_CHARS,
        "section_range": (4, 6),
        "lead_base": 140,
        "lead_span": 90,
        "min_body_chars": 1200,
    },
    "long": {
        "min_chars": 4500,
        "max_chars": 9000,
        "section_range": (5, 7),
        "lead_base": 190,
        "lead_span": 130,
        "min_body_chars": 2200,
    },
}


class ArticleLengthPlanningMixin:
    def _normalize_length_mode(self, length_mode: Optional[str]) -> str:
        key = (length_mode or "adaptive").strip().lower()
        if key in LENGTH_MODE_PROFILES:
            return key
        if key in {"auto", "default", "recommended"}:
            return "adaptive"
        return "adaptive"

    def _count_length_signal_items(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
    ) -> int:
        sample = " ".join(
            [
                (user_prompt or "")[:400],
                *[((ctx.title or "")[:120] + " " + (ctx.content or "")[:1800]) for ctx in contexts[:4]],
            ]
        )
        if not sample:
            return 0
        patterns = [
            r"\d{4}年\d{1,2}月\d{1,2}日",
            r"\d{1,2}月\d{1,2}日",
            r"(対象|変更点|開始時期|影響|確認事項|注意点|対応|手順|設定|切替|移行|更新)",
            r"(FAQ|よくある質問|問い合わせ|サポート|窓口|公式)",
            r"(RCS|SMS|MMS|Google|Android|アプリ|端末|OS)",
        ]
        score = sum(len(re.findall(pattern, sample, re.I)) for pattern in patterns)
        sentence_count = len(re.findall(r"[。！？!?]", sample))
        if self._safe_contract_value(article_type).lower() == "announcement":
            score += sentence_count // 2
        else:
            score += sentence_count // 4
        return min(24, max(0, score))

    def _resolve_adaptive_length_mode(
        self,
        *,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
    ) -> str:
        article_key = self._safe_contract_value(article_type).lower()
        source_chars = sum(len((ctx.content or "")[:6000]) for ctx in contexts[:4])
        prompt_chars = len((user_prompt or "").strip())
        fact_score = self._count_length_signal_items(contexts, user_prompt, article_type)
        source_count = len(contexts)

        if article_key == "announcement":
            if source_chars <= 2200 and fact_score <= 10:
                return "short"
            if source_chars <= 6500 and fact_score <= 18:
                return "normal"
            return "long"

        if article_key in {"branding", "corporate_culture"}:
            signal = source_chars + prompt_chars * 6 + source_count * 760 + fact_score * 180
            if signal < 3600:
                return "short"
            if signal < 9800:
                return "normal"
            return "long"

        if article_key == "ai":
            signal = source_chars + prompt_chars * 5 + source_count * 720 + fact_score * 220
            if signal < 4500:
                return "short"
            if signal < 10200:
                return "normal"
            return "long"

        signal = source_chars + prompt_chars * 5 + source_count * 700 + fact_score * 180
        if signal < 4200:
            return "short"
        if signal < 9800:
            return "normal"
        return "long"

    def _get_length_profile(self) -> Dict[str, Any]:
        mode = getattr(self, "_length_mode", "normal")
        return LENGTH_MODE_PROFILES.get(mode, LENGTH_MODE_PROFILES["normal"])

    def _get_note_length_range(self) -> Tuple[int, int]:
        profile = self._get_length_profile()
        return int(profile["min_chars"]), int(profile["max_chars"])

    def _get_outline_section_range(self) -> Tuple[int, int]:
        profile = self._get_length_profile()
        base_min, base_max = profile["section_range"]
        source_count = getattr(self, "_source_count", 0)
        if self._length_mode == "normal" and source_count >= 5:
            base_max = min(7, base_max + 1)
        if self._length_mode == "long" and source_count >= 6:
            base_max = min(8, base_max + 1)
        return int(base_min), int(base_max)

    def _estimate_note_target_chars(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
    ) -> int:
        min_chars, max_chars = self._get_note_length_range()
        prompt_len = len((user_prompt or "").strip())
        source_len = sum(len((c.content or "")[:2000]) for c in contexts[:4])
        title_len = sum(len((c.title or "")) for c in contexts[:4])
        source_count = len(contexts)

        signal = prompt_len + source_len + title_len + source_count * 120
        ratio = min(1.0, max(0.0, signal / 7000))

        base = min_chars + int((max_chars - min_chars) * ratio)

        type_bias = {
            "branding": 1.12,
            "ai": 1.05,
            "announcement": 0.72,
            "case_study": 1.08,
        }.get(article_type, 1.0)

        target = int(base * type_bias)
        target = int(target * random.uniform(0.93, 1.07))
        return max(min_chars, min(max_chars, target))

    def _estimate_note_lead_chars(self, note_target: int) -> int:
        profile = self._get_length_profile()
        min_chars, max_chars = self._get_note_length_range()
        denominator = max(1, max_chars - min_chars)
        ratio = (note_target - min_chars) / denominator
        ratio = max(0.0, min(1.0, ratio))
        base = int(profile["lead_base"] + profile["lead_span"] * ratio)
        return int(base * random.uniform(0.9, 1.1))

    def _allocate_section_targets(self, total_chars: int, section_count: int) -> List[int]:
        if section_count <= 0:
            return []
        base = max(380, int(total_chars / section_count))
        targets = [int(base * random.uniform(0.85, 1.15)) for _ in range(section_count)]
        diff = total_chars - sum(targets)
        targets[-1] = max(300, targets[-1] + diff)
        return targets
