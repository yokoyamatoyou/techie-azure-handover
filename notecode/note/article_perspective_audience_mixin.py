"""Perspective and audience resolution helpers for ArticleGenerator."""
from __future__ import annotations

import logging
import re
from typing import List, Optional

from note.article_fetcher import FetchedContent

logger = logging.getLogger(__name__)

BASE_PERSONA_TEMPLATE = """
一人称は「{pronoun}」。自分の言葉で、読者に伝わる具体性を優先して語りかける。
根拠のない断定は避け、実体験の断定は参考情報に裏付けがある場合のみ使う。
自分を肩書きで名乗らない。
""".strip()

SECONDARY_PERSONAS = {
    "expert": (
        "専門的な知見を背景に、論点整理・根拠・注意点を丁寧に示す。"
        "断定は根拠の範囲に留め、過度な煽りや誇張は避ける。"
    ),
    "corporate": (
        "企業のブランディング担当の視点で、価値の言語化、一貫性、信頼の作り方を意識する。"
        "宣伝臭は抑え、読者の納得と共感を優先する。"
    ),
    "educator": (
        "教える視点を添え、要点を噛み砕いて伝える。"
        "専門用語は必ず平易な言葉に言い換える。"
    ),
    "journalist": (
        "調査報告の視点を添え、事実・背景・一次情報への配慮を重視する。"
        "推測は控え、必要なら「〜とみられる」等で距離を取る。"
    ),
    "friend": (
        "友人の視点を添え、距離感の近い言葉選びにする。"
        "読み手の感情に寄り添い、堅さを和らげる。"
    ),
}

PERSPECTIVE_KEYS = {"auto", "blogger", "expert", "corporate", "educator", "journalist", "friend"}
PERSPECTIVE_LABELS = {
    "auto": "自動判定",
    "blogger": "個人の語り口",
    "expert": "専門家の知見",
    "corporate": "企業ブランディング担当の知見",
    "educator": "教育者の知見",
    "journalist": "記者の視点",
    "friend": "友人の視点",
}


class ArticlePerspectiveAudienceMixin:
    def _get_persona_for_perspective(
        self,
        perspective: str,
        contexts: List[FetchedContent],
        user_prompt: str,
    ) -> str:
        """基本は個人の語り口。必要に応じて第二ペルソナを合成する。"""
        perspective_key = self._normalize_perspective_key(perspective)
        secondary_key = self._resolve_secondary_perspective(perspective_key, contexts, user_prompt)
        self._secondary_perspective = secondary_key
        secondary = SECONDARY_PERSONAS.get(secondary_key) if secondary_key else None
        corporate_types = ("branding", "case_study", "announcement", "corporate_culture")
        user_chose_explicitly = perspective_key not in ("", "auto")
        if secondary_key == "corporate" or perspective_key == "corporate":
            base_pronoun = "私たち"
        elif not user_chose_explicitly and getattr(self, "_current_type", "") in corporate_types:
            base_pronoun = "私たち"
        else:
            base_pronoun = "わたし"
        base = BASE_PERSONA_TEMPLATE.format(pronoun=base_pronoun)
        return self._blend_persona(base, secondary)

    def _resolve_secondary_perspective(
        self,
        perspective: str,
        contexts: List[FetchedContent],
        user_prompt: str,
    ) -> Optional[str]:
        """第二ペルソナを決定する（UI選択 > インタビュー回答 > 自動判定）。"""
        perspective_key = self._normalize_perspective_key(perspective)
        if perspective_key and perspective_key != "auto":
            if perspective_key == "blogger":
                return None
            return perspective_key

        from_interview = self._secondary_from_interview()
        if from_interview:
            return from_interview

        return self._detect_secondary_from_context(contexts, user_prompt)

    def _secondary_from_interview(self) -> Optional[str]:
        """インタビュー回答から第二ペルソナを推定する。"""
        if not self._interview_answers:
            return None
        interview_key = self._normalize_perspective_key(self._interview_answers.get("perspective_key") or "")
        if interview_key:
            if interview_key in ("auto", "blogger"):
                return None
            return interview_key
        answer = (self._interview_answers.get("perspective") or "").strip()
        if not answer:
            return None

        if re.search(r"専門家|有資格|コンサル|アナリスト|監修", answer):
            return "expert"
        if re.search(r"ブランディング|ブランド|広報|PR|マーケ|マーケティング|企業", answer):
            return "corporate"
        if re.search(r"教育|先生|講師", answer):
            return "educator"
        if re.search(r"記者|ジャーナリスト|第三者", answer):
            return "journalist"
        if re.search(r"友人|カジュアル|フランク", answer):
            return "friend"

        return None

    def _normalize_perspective_key(self, perspective: Optional[str]) -> str:
        text = (perspective or "").strip()
        if not text:
            return "auto"
        lowered = text.lower()
        if lowered in PERSPECTIVE_KEYS:
            return lowered
        if re.search(r"(指定しない|任せる|おまかせ|自動判定|auto)", text, re.I):
            return "auto"
        if re.search(r"(企業|ブランディング|広報|pr|マーケ|コーポレート|顧客価値|会社紹介)", text, re.I):
            return "corporate"
        if re.search(r"(記者|ジャーナリスト|取材|第三者|一次情報)", text, re.I):
            return "journalist"
        if re.search(r"(教育|教育設計|先生|講師)", text, re.I):
            return "educator"
        if re.search(r"(友人|カジュアル|フランク|親しみ)", text, re.I):
            return "friend"
        if re.search(r"(専門家|有資格|コンサル|アナリスト|ir|財務|法務|コンプライアンス|技術実装|技術)", text, re.I):
            return "expert"
        if re.search(r"(個人|体験者|当事者|ブログ|ブロガー)", text, re.I):
            return "blogger"
        return "auto"

    def _label_for_perspective_key(self, perspective_key: str) -> str:
        return PERSPECTIVE_LABELS.get(perspective_key, perspective_key or "自動判定")

    def _detect_secondary_from_context(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
    ) -> Optional[str]:
        """コンテンツ/指示から第二ペルソナを自動推定する。"""
        corporate_keywords = ["企業視点", "弊社", "当社", "自社", "会社として", "ブランド", "ブランディング"]
        if user_prompt and any(kw in user_prompt for kw in corporate_keywords):
            return "corporate"

        executive_keywords = [
            "経営層", "経営者", "役員", "取締役", "CFO", "CEO", "COO", "CTO",
            "意思決定者", "ボード", "経営陣", "管理職", "エグゼクティブ",
        ]
        if user_prompt and any(kw in user_prompt for kw in executive_keywords):
            return "expert"

        educator_keywords = ["教育", "先生", "講師", "解説", "わかりやすく"]
        if user_prompt and any(kw in user_prompt for kw in educator_keywords):
            return "educator"

        journalist_keywords = ["記者", "ジャーナリスト", "取材", "調査報告", "第三者視点"]
        if user_prompt and any(kw in user_prompt for kw in journalist_keywords):
            return "journalist"

        if contexts:
            first_url = contexts[0].url or ""
            first_content = (contexts[0].content or "")[:500]
            corp_indicators = [
                "会社概要", "企業情報", "サービス紹介", "お問い合わせ",
                "事業内容", "製品情報", "co.jp", "inc", "corp",
            ]
            if any(ind in first_url.lower() or ind in first_content for ind in corp_indicators):
                return "corporate"

        return None

    def _blend_persona(self, base: str, secondary: Optional[str]) -> str:
        """ベース人格に第二ペルソナを合成する。"""
        if not secondary:
            return base
        if "私たち" in base:
            synthesis_rule = (
                "【合成ルール】主語は「私たち」（企業の一人称）を一貫して維持。"
                "第二ペルソナは情報の選び方・解釈・例示に反映する。"
                "本文で社名・肩書きを冒頭以外で繰り返さない。"
            )
        else:
            synthesis_rule = (
                "【合成ルール】主語は個人の語り口（私）を維持。"
                "第二ペルソナは情報の選び方・解釈・例示に反映する。"
                "本文で自分の肩書き（専門家/企業担当など）を名乗らない。"
            )
        return "\n".join(
            [
                base,
                f"【第二ペルソナ】{secondary}",
                synthesis_rule,
            ]
        )

    def _extract_pronoun(self, persona: str) -> str:
        """ペルソナから一人称を抽出する。"""
        if "僕" in persona:
            return "僕"
        if "わたし" in persona:
            return "わたし"
        if "私たち" in persona:
            return "私たち"
        if "当社" in persona:
            return "当社"
        if "私" in persona:
            return "私"
        return "私"

    def _detect_persona(self, contexts: List[FetchedContent], user_prompt: str) -> str:
        """URLやコンテンツから適切なペルソナを動的に生成する。"""
        corporate_keywords = ["企業視点", "私たち", "弊社", "当社", "自社", "会社として"]
        if user_prompt and any(kw in user_prompt for kw in corporate_keywords):
            return "私たちは事業を展開する企業の立場から、読者に価値を伝える。"

        executive_keywords = [
            "経営層", "経営者", "役員", "取締役", "CFO", "CEO", "COO", "CTO",
            "意思決定者", "ボード", "経営陣", "管理職", "エグゼクティブ",
        ]
        if user_prompt and any(kw in user_prompt for kw in executive_keywords):
            return (
                "専門家・第三者の立場から経営層向けに実務的な示唆を提示する。"
                "主観よりも根拠と具体性を重視し、読み手の意思決定に役立つ観点で書く。"
            )

        if contexts:
            first_url = contexts[0].url or ""
            first_content = (contexts[0].content or "")[:500]
            corp_indicators = [
                "会社概要", "企業情報", "サービス紹介", "お問い合わせ",
                "事業内容", "製品情報", "co.jp", "inc", "corp",
            ]
            if any(ind in first_url.lower() or ind in first_content for ind in corp_indicators):
                try:
                    prompt = f"""
以下の情報から記事執筆者のペルソナを1文で作成してください。
URL: {first_url}
概要: {first_content[:300]}
ユーザー指示（JSON文字列）: {self._safe_user_prompt(user_prompt, empty_value="なし")}

企業や組織の立場なら「私たちは〇〇として」、個人視点なら「わたしは〇〇として」の形式で。
出力はペルソナ文のみ（1文）。
""".strip()
                    return self.llm.generate_text(prompt, max_tokens=80, task_type="persona").strip()
                except Exception as exc:
                    logger.debug("Persona detection fallback triggered", exc_info=exc)
                    return "私たちは読者に価値を提供する立場として執筆する。"

        return "一人称は『わたし』。断定を避け、考察と具体例を中心に。"

    def _detect_target_audience(self, contexts: List[FetchedContent], user_prompt: str) -> str:
        """参考情報と指示からターゲット読者を推定する。"""
        content_text = contexts[0].content[:500] if contexts else ""
        prompt = f"""
以下の情報から、この記事の「ターゲット読者」を具体的に定義してください。
想定読者の悩み、年齢層、興味関心を推測すること。

参考情報: {content_text}
ユーザー指示（JSON文字列）: {self._safe_user_prompt(user_prompt, empty_value="なし")}

出力例: 「将来のキャリアに不安を感じている20代後半の社会人。効率化ツールに興味がある。」
出力はターゲット定義の文言のみ（50文字以内）。
""".strip()
        try:
            return self.llm.generate_text(prompt, max_tokens=100, task_type="audience").strip()
        except Exception as exc:
            logger.debug("Audience detection fallback triggered", exc_info=exc)
            return "特定の悩みを持つ一般読者"
