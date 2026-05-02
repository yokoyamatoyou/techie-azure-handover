"""article_legacy_addendum_mixin.py - Legacy addendum helpers for ArticleGenerator."""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

from note.article_fetcher import FetchedContent
from note.legacy_current.article_runtime_symbols import (
    LINKEDIN_MAX_CHARS,
    LINKEDIN_MIN_CHARS,
    RE_HEADING_LINE,
    RE_WHITESPACE_COLLAPSE,
)

logger = logging.getLogger(__name__)


class ArticleLegacyAddendumMixin:
    """Mixin providing legacy addendum, note-length adjustment, and LinkedIn helper utilities."""

    def _generate_expansion_section(
        self,
        merged: str,
        user_prompt: str,
        article_type: str,
        target_audience: str,
        target_chars: int,
        title: Optional[str] = None,
        existing_body: str = "",
        force_non_overlap: bool = False,
    ) -> str:
        """不足分を埋める補足セクションを生成する。"""
        target = max(300, min(1200, target_chars))
        writing_focus_guide = self._get_writing_focus_guide()
        focus = self._get_effective_writing_focus()
        evidence_mode = str(self._pipeline_policy.get("evidence_mode", "normal"))
        body_brief = self._summarize_body_for_expansion(existing_body)
        heading_label = "## 補足"
        if re.search(r"^##\s*(補足|FAQ|Q&A|注意点|豆知識|Tips)\b", existing_body or "", flags=re.MULTILINE):
            heading_label = "## 追加の視点"
        if focus == "experience" and evidence_mode != "strict":
            addendum_rule = "必要に応じて短い体験要素か具体例を1つ含める"
        else:
            addendum_rule = "具体例か根拠を1つ含める（実体験を装わない）"
        non_overlap_rule = (
            "- 既存本文と同じ主張の言い換え・反復を避け、未カバーの論点を1つだけ補う"
            if force_non_overlap
            else "- 既存本文と同じ主張の言い換え・反復を避ける"
        )
        stage_role_label = ""
        transition_from_prev = ""
        stage_role_line = f"段階台本上の役割: {stage_role_label}" if stage_role_label else ""
        transition_line = (
            f"【直前セクションからの接続】\n{transition_from_prev}"
            if transition_from_prev
            else ""
        )
        prompt = f"""
【執筆者の立ち位置】
{self._current_persona}

【記事タイトル】
{title or "指定なし"}

【ターゲット読者】
{target_audience}

【執筆方針】
{self._current_prompts[article_type]}

【テーマ】
{self._safe_user_prompt(user_prompt)}

【参考情報（抜粋）】
{merged[:1500] if merged else "なし"}

【追加ガイド】
{self._enhanced_context or "なし"}

【本文の重心】
{writing_focus_guide or "自動判定"}

【既存本文（重複禁止の要点）】
{body_brief or "なし"}

本文に追加する「補足セクション」を1つだけ作成してください。

【ルール】
- 一人称は「{self._current_pronoun}」で統一
- 読者に語りかける「です・ます」調
- {addendum_rule}
- {non_overlap_rule}
- 長さは{target}文字前後
- 見出しは `{heading_label}` で開始
- 禁止語: {", ".join(self._get_active_banned_phrases())}
{stage_role_line}
{transition_line}

本文のみ出力。
""".strip()
        section = self.llm.generate_text(prompt, max_tokens=min(1400, int(target * 1.2)), task_type="section")
        section = self._apply_resonance(
            section,
            platform="note",
            perspective=self._current_perspective,
            source_text=merged,
        )
        section = self._clean_meta_output(section, target_audience)
        if section and not section.strip().startswith("##"):
            section = f"{heading_label}\n\n{section.strip()}"
        return section

    def _summarize_body_for_expansion(self, body: str) -> str:
        if not body:
            return ""

        lines: List[str] = []
        for heading, content in self._extract_section_blocks(body)[:4]:
            sentence = ""
            if content:
                sentence = re.split(r"(?<=[。！？])\s*", content.strip(), maxsplit=1)[0].strip()
            sentence = re.sub(r"\s+", " ", sentence)
            if sentence:
                sentence = sentence[:70].rstrip(" 、。")
                lines.append(f"- {heading}: {sentence}")
            else:
                lines.append(f"- {heading}")

        if not lines:
            paragraphs = [p.strip() for p in re.split(r"\n{2,}", body) if p.strip()]
            for paragraph in paragraphs[:3]:
                cleaned = RE_HEADING_LINE.sub("", paragraph).strip()
                if not cleaned:
                    continue
                cleaned = RE_WHITESPACE_COLLAPSE.sub(" ", cleaned)[:70].rstrip(" 、。")
                lines.append(f"- {cleaned}")

        return "\n".join(lines)[:500]

    def _generate_linkedin_addendum(
        self,
        merged: str,
        user_prompt: str,
        article_type: str,
        target_audience: str,
        target_chars: int,
        title: Optional[str] = None,
    ) -> str:
        """LinkedInの不足分を補う短い補足文を生成する。"""
        target = max(120, min(420, target_chars))
        prompt = f"""
【ターゲット読者】
{target_audience}

【記事タイトル】
{title or "指定なし"}

【執筆方針】
{self._current_prompts[article_type]}

【テーマ】
{self._safe_user_prompt(user_prompt)}

【参考情報（抜粋）】
{merged[:1200] if merged else "なし"}

【追加ガイド】
{self._enhanced_context or "なし"}

LinkedIn投稿に追記する「短い補足文」を作成してください。

【ルール】
- 2〜4文、{target}文字前後
- 見出しや番号は使わない
- CTAやハッシュタグは含めない
- 具体的な行動提案か小さな気づきを1つ入れる

本文のみ出力。
""".strip()
        text = self.llm.generate_text(prompt, max_tokens=min(500, int(target * 1.3)), task_type="section").strip()
        return self._clean_meta_output(text, target_audience)

    def _adjust_note_length(
        self,
        lead: str,
        body: str,
        references_md: str,
        merged_context: str,
        user_prompt: str,
        article_type: str,
        target_audience: str,
        title: Optional[str] = None,
    ) -> Tuple[str, str]:
        min_chars, max_chars = self._get_note_length_range()
        profile = self._get_length_profile()
        note_parts = [lead, body]
        if references_md:
            note_parts.append(references_md)
        note_text = "\n\n".join(p for p in note_parts if p)

        if len(note_text) < min_chars:
            deficit = min_chars - len(note_text)
            extra = self._generate_expansion_section(
                merged_context,
                user_prompt,
                article_type,
                target_audience,
                deficit,
                title=title,
                existing_body=body,
            )
            if extra and self._is_redundant_expansion(body, extra):
                extra = self._generate_expansion_section(
                    merged_context,
                    user_prompt,
                    article_type,
                    target_audience,
                    deficit,
                    title=title,
                    existing_body=body,
                    force_non_overlap=True,
                )
            if extra and self._is_redundant_expansion(body, extra):
                logger.info("Skip redundant expansion section due high overlap with existing body")
                extra = ""
            if not extra:
                return lead, body
            body = f"{body}\n\n{extra}".strip()
            return lead, body

        if len(note_text) > max_chars:
            overhead = len(lead)
            if references_md:
                overhead += len(references_md) + len("\n\n")
            max_body_len = max(int(profile["min_body_chars"] * 0.55), max_chars - overhead - len("\n\n"))
            body = self._trim_body_to_limit(body, max_body_len)
        return lead, body

    def _estimate_linkedin_target_chars(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
    ) -> int:
        """ユーザー指示とソース量からLinkedIn本文の目安文字数を推定する。"""
        prompt_len = len((user_prompt or "").strip())
        source_len = sum(len((c.content or "")[:1200]) for c in contexts[:3])
        source_len += sum(len((c.title or "")) for c in contexts[:3])

        signal = prompt_len + source_len
        ratio = min(1.0, max(0.0, signal / 3500))
        ratio = min(1.0, ratio + min(0.1, 0.03 * len(contexts)))

        linkedin_min_chars = int(LINKEDIN_MIN_CHARS)
        linkedin_max_chars = int(LINKEDIN_MAX_CHARS)
        target = int(linkedin_min_chars + (linkedin_max_chars - linkedin_min_chars) * ratio)

        purpose = self._detect_linkedin_purpose(contexts, user_prompt, article_type)
        purpose_bias = {
            "new_service": 0.88,
            "service_intro": 0.95,
            "engineer": 1.08,
            "daily": 0.8,
            "default": 0.95,
        }.get(purpose, 0.95)

        target = int(target * purpose_bias)
        return max(linkedin_min_chars, min(linkedin_max_chars, target))

    def _detect_linkedin_purpose(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
    ) -> str:
        """ユーザー指示やソースからLinkedIn投稿の目的を推定する。"""
        titles = " ".join((c.title or "") for c in contexts[:3])
        snippets = " ".join((c.content or "")[:400] for c in contexts[:2])
        text = f"{user_prompt or ''} {titles} {snippets}"

        keyword_sets = {
            "new_service": [
                "新サービス", "新製品", "新機能", "リリース", "ローンチ", "β版", "ベータ",
                "アップデート", "告知", "公開", "提供開始",
            ],
            "service_intro": [
                "サービス紹介", "製品紹介", "プロダクト紹介", "サービスの特徴", "料金", "プラン",
                "導入", "使い方", "機能", "メリット", "導入事例",
            ],
            "engineer": [
                "エンジニア", "開発", "技術", "技術者", "アーキテクチャ", "インフラ",
                "SRE", "DevOps", "API", "SDK", "OSS", "バックエンド", "フロントエンド",
                "プログラミング", "コード", "実装", "設計", "レビュー", "テック", "技術ブログ",
            ],
            "daily": [
                "日々", "日記", "雑談", "近況", "今日", "今週", "最近", "ふと思った",
                "気づき", "振り返り", "出来事",
            ],
        }

        scores = {key: 0 for key in keyword_sets}
        for key, keywords in keyword_sets.items():
            scores[key] = sum(1 for kw in keywords if kw in text)

        best = max(scores, key=scores.get)
        if scores.get(best, 0) > 0:
            return best
        return "default"
