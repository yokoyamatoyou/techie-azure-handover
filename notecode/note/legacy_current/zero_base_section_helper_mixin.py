"""Zero-base section helper/compatibility helpers for ArticleGenerator."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from human_resonance.phase7_sanitize import Phase7Sanitize


class ZeroBaseSectionHelperMixin:
    def _zero_base_build_contract_retry_guidance(self, report: Optional[Dict[str, Any]]) -> str:
        report = report if isinstance(report, dict) else {}
        hints: List[str] = []
        if int(report.get("third_person_speaker_mentions", 0) or 0) > 0:
            hints.append("語り手を第三者として説明せず、当事者の声として書く")
        disallowed = report.get("disallowed_pronoun_hits", [])
        if isinstance(disallowed, list) and disallowed:
            hints.append("許容されない一人称を使わず、指定された語り口だけを使う")
        if int(report.get("advice_tone_count", 0) or 0) > 0:
            hints.append("一般論の助言に逃げず、見出しに必要な具体情報へ絞る")
        return " / ".join(hints[:3])

    def _zero_base_apply_sanitize_pass(self, text: str) -> str:
        if not text:
            return ""
        sanitizer = Phase7Sanitize(
            remove_emoji_excess=False,
            remove_placeholders=True,
            reduce_ai_noise=True,
        )
        return sanitizer.process(text)

    def _zero_base_build_section_prompt(
        self,
        *,
        heading: str,
        new_information: str,
        reader_question: str,
        previous_summary: str,
        recent_summaries: Optional[List[str]],
        audience: str,
        must_not_repeat: List[str],
        user_instruction: str = "",
        instruction_anchor_terms: Optional[List[str]] = None,
        forbidden_topics: Optional[List[str]] = None,
        section_plan: Optional[Dict[str, int]] = None,
        speaker_profile: str = "",
        relationship_mode: str = "",
        register_policy: Optional[Dict[str, Any]] = None,
        allowed_pronouns: Optional[List[str]] = None,
        retry_feedback: str = "",
    ) -> str:
        section_plan = section_plan or {}
        register_policy = register_policy if isinstance(register_policy, dict) else {}
        sentence_min = max(1, int(section_plan.get("sentence_min", 2) or 2))
        sentence_max = max(sentence_min, int(section_plan.get("sentence_max", 4) or 4))
        target_chars = max(120, int(section_plan.get("target_chars", 220) or 220))
        anchor_terms = [
            self._safe_contract_value(term)
            for term in (instruction_anchor_terms or [])
            if self._safe_contract_value(term)
        ]
        blocked_topics = [
            self._safe_contract_value(topic)
            for topic in (forbidden_topics or [])
            if self._safe_contract_value(topic)
        ]
        invariants = [
            f"- {sentence_min}〜{sentence_max}文、1段落1トピックで書く",
            f"- 目安文字数は{target_chars}字（不足時は具体例を1つ補う）",
            "- 見出し行（##）は出力しない",
            "- 推定は断定せず、誇張しない",
            "- 既出表現をそのまま繰り返さない",
            "- ユーザー指示の核心から外れる話題へ逸脱しない",
            "- 語り手は指定された話者本人の声で一貫させ、第三者解説へ逃げない",
            "- 定型句（まず/重要なのは/〜が期待されます）を連打しない",
            "- 接続詞（また/さらに/しかし）で文頭を連続させない",
            "- 同じ文末（です。/ます。）を3回以上連続させない",
            "- 読者像の語を連呼せず、必要な箇所以外は言い換える",
            "- 年代・家族形態など読者属性のラベルは原則本文に書かない（記事テーマとして明示が必要な場合のみ例外）",
            "- 一般論の運用アドバイスではなく、この見出しで必要な具体情報を優先する",
        ]
        audience_hint = self._build_audience_prompt_hint(audience)
        existing_summary = " / ".join(
            self._sanitize_contract_text(item, max_length=64)
            for item in (recent_summaries or [])[-3:]
            if self._sanitize_contract_text(item, max_length=64)
        )
        register_endings = ", ".join(
            self._safe_contract_value(item)
            for item in register_policy.get("allowed_endings", [])
            if self._safe_contract_value(item)
        )
        blocked_endings = ", ".join(
            self._safe_contract_value(item)
            for item in register_policy.get("banned_endings", [])
            if self._safe_contract_value(item)
        )
        variable_lines = [
            f"見出し: {heading or '補足'}",
            f"新情報: {new_information or 'なし'}",
            f"読者質問: {reader_question or 'なし'}",
            f"直前要約: {previous_summary or 'なし'}",
            f"既出要点: {existing_summary or 'なし'}",
            f"読者ニーズヒント: {audience_hint}",
            f"話者プロファイル: {speaker_profile or '未指定'}",
            f"話者と読者の関係: {relationship_mode or 'guide'}",
            f"許容一人称: {', '.join(self._safe_contract_value(item) for item in (allowed_pronouns or [])) or '省略優先'}",
            f"許容文末: {register_endings or 'です, ます'}",
            f"禁止文末: {blocked_endings or 'なし'}",
            f"反復禁止: {', '.join(self._safe_contract_value(item) for item in must_not_repeat[:4]) or '同義反復'}",
            f"ユーザー指示（最優先）: {self._sanitize_contract_text(user_instruction, max_length=180) or 'なし'}",
            f"指示キーワード: {', '.join(anchor_terms[:6]) or 'なし'}",
        ]
        if blocked_topics:
            variable_lines.append(f"無関係に以下の話題へ逸脱しない: {', '.join(blocked_topics[:6])}")
        if retry_feedback:
            variable_lines.append(f"再生成時の補正指示: {self._sanitize_contract_text(retry_feedback, max_length=180)}")
        return (
            "あなたは日本語ブログ編集者です。本文のみを出力してください。\n\n"
            "【不変ルール】\n"
            + "\n".join(invariants)
            + "\n\n【可変指示】\n"
            + "\n".join(variable_lines)
        )

    def _zero_base_extract_section_summary(
        self,
        *,
        section_text: str,
        fallback: str,
    ) -> str:
        body = re.sub(r"^##\s+.*$", "", section_text or "", flags=re.MULTILINE).strip()
        if not body:
            return self._safe_contract_value(fallback)[:84]
        sentences = [s.strip() for s in re.split(r"(?<=[。！？])\s*", body) if s.strip()]
        if not sentences:
            compact = re.sub(r"\s+", " ", body).strip()
            return compact[:84]
        summary = " ".join(sentences[:2])
        summary = re.sub(r"\s+", " ", summary).strip()
        return summary[:84]
