"""interview_mixin.py - Interview question generation mixin for ArticleGenerator."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from note.article_fetcher import FetchedContent
from note.intent_profile import build_source_excerpt, decide_need_question
from note.prompt_sanitizer import sanitize_untrusted_text

logger = logging.getLogger(__name__)

INTERVIEW_OPTION_MAX = 5
INTERVIEW_THEME_TITLE_MAX_LEN = 40
INTERVIEW_THEME_PROMPT_MAX_LEN = 56
INTERVIEW_THEME_DISPLAY_MAX_LEN = 56
INTERVIEW_THEME_QUOTE_MAX_LEN = 36
INTERVIEW_QUESTION_TOPIC_MAX_LEN = 24


def _article_type_labels() -> Dict[str, str]:
    """Lazy accessor to avoid circular import with article_generator."""
    from note.article_generator import ARTICLE_TYPE_LABELS
    return ARTICLE_TYPE_LABELS


class InterviewMixin:
    """Mixin providing interview question generation and constraint derivation."""

    def generate_interview_questions(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
        force_questions: bool = False,
    ) -> List[Dict[str, str]]:
        """ユーザーの意図を明確にするための質問を生成する（1回のみ）。
        
        Returns:
            List of {"id": str, "question": str, "options": List[str] or None}
        """
        self._last_interview_mode = "fallback"
        self._last_interview_reason = "unknown"
        self._last_need_question_decision = self.should_ask_pre_generation_questions(
            contexts,
            user_prompt,
            article_type,
        )

        # ソース情報を要約（固有名詞・数値・組織名が質問に反映されるよう十分な長さを確保）
        source_summary = ""
        for ctx in contexts[:4]:
            title = ctx.title or "無題"
            content_preview = (ctx.content or "")[:800]
            source_summary += f"- {title}: {content_preview}...\n"
        fallback_questions = self._build_dynamic_interview_fallback(contexts, user_prompt, article_type)
        if not force_questions and not bool(self._last_need_question_decision.get("ask", True)):
            self._last_interview_mode = "policy_skip"
            self._last_interview_reason = str(
                self._last_need_question_decision.get("reason") or "sufficient_input"
            )
            return []
        if str(article_type or "").strip().lower() == "announcement":
            self._last_interview_mode = "fallback"
            self._last_interview_reason = "category_locked_announcement"
            return fallback_questions
        fallback_contract = [
            {"id": "perspective", "options": "2-5個の選択肢"},
            {"id": "target", "options": "2-5個の選択肢"},
            {"id": "message", "options": None},
        ]
        
        prompt = f"""
あなたは優秀なライターのインタビュアーです。
以下の情報から、より良い記事を書くために必要な質問を3つだけ生成してください。

【ユーザーの依頼（JSON文字列）】
{self._safe_user_prompt(user_prompt)}

【記事タイプ】
{_article_type_labels().get(article_type, article_type)}

【参考情報の概要】
{source_summary or "なし"}

【質問の観点】
1. 第二ペルソナ: 必要なら専門家や企業ブランディング担当の知見を混ぜるか
2. ターゲット読者: 誰に向けて書くか（初心者、同業者、経営者など）
3. 核心メッセージ: 読後に残したい1つのメッセージは何か

【質問作成ルール】
- 参考情報の固有名詞・具体要素（会社名、商品名、方針、数値など）を必ず質問に含める
- 「どの視点で書きますか？」のような汎用テンプレは避け、具体的な視点を提案する
- 「誰に向けて書きますか？」ではなく、具体的な読者層を想定して質問する
- 各質問は1文で簡潔にするが、具体性を失わない
- 例：「〇〇（会社名）の△△（サービス）について、現場のエンジニア視点で書きますか？」

【参考（内部テンプレートの制約のみ。文面の流用は禁止）】
{json.dumps(fallback_contract, ensure_ascii=False)}

【出力形式】
以下のJSON形式で出力。説明は不要。
[
  {{"id": "perspective", "question": "質問文", "options": ["選択肢1", "選択肢2", "選択肢3"]}},
  {{"id": "target", "question": "質問文", "options": ["選択肢1", "選択肢2", "選択肢3"]}},
  {{"id": "message", "question": "質問文", "options": null}}
]
""".strip()
        
        response = ""
        try:
            response = self.llm.generate_text(prompt, max_tokens=500, task_type="interview")
        except Exception as exc:
            logger.warning("Failed to generate interview questions via LLM: %s", exc)
            self._last_interview_reason = "llm_exception"

        if response:
            json_text = self._extract_first_json_array(response)
            if json_text:
                try:
                    questions = json.loads(json_text)
                    normalized = self._normalize_interview_questions(questions, fallback_questions)
                    if normalized and self._validate_interview_questions(normalized):
                        self._last_interview_mode = "llm"
                        self._last_interview_reason = "normalized" if normalized != questions else "ok"
                        return normalized
                    self._last_interview_reason = "invalid_schema"
                    logger.info("Interview question generation fallback triggered: invalid_schema")
                except (json.JSONDecodeError, TypeError, ValueError) as exc:
                    logger.debug("Interview question JSON parse failed", exc_info=exc)
                    self._last_interview_reason = "json_parse_error"
                    logger.info("Interview question generation fallback triggered: json_parse_error")
            else:
                self._last_interview_reason = "json_array_not_found"
                logger.info("Interview question generation fallback triggered: json_array_not_found")
        else:
            if self._last_interview_reason == "unknown":
                self._last_interview_reason = "empty_response"
            logger.info("Interview question generation fallback triggered: empty_response")
        
        # フォールバック: ソース内容に応じた質問を返す
        return fallback_questions

    def get_last_interview_generation_status(self) -> Dict[str, str]:
        return {
            "mode": self._last_interview_mode,
            "reason": self._last_interview_reason,
        }

    def should_ask_pre_generation_questions(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
    ) -> Dict[str, Any]:
        source_chars = sum(len((ctx.content or "")[:4000]) for ctx in contexts[:4])
        source_count = len(contexts or [])
        fact_score = 0
        try:
            fact_score = int(self._count_length_signal_items(contexts, user_prompt, article_type))  # type: ignore[attr-defined]
        except Exception:
            fact_score = 0

        answered = 0
        raw_answers = getattr(self, "_interview_answers", {}) or {}
        if isinstance(raw_answers, dict):
            answered = sum(
                1 for key in ("perspective", "target", "message")
                if str(raw_answers.get(key) or "").strip()
            )
        source_excerpt = build_source_excerpt(
            [
                f"{ctx.title or ''} {(ctx.content or '')[:280]}".strip()
                for ctx in contexts[:3]
            ]
        )
        return decide_need_question(
            article_type=article_type,
            user_prompt=user_prompt,
            source_count=source_count,
            source_chars=source_chars,
            fact_score=fact_score,
            answered=answered,
            source_excerpt=source_excerpt,
        )

    def _extract_first_json_array(self, text: str) -> str:
        start = text.find("[")
        if start < 0:
            return ""
        depth = 0
        in_string = False
        escape = False
        for idx in range(start, len(text)):
            ch = text[idx]
            if in_string:
                if escape:
                    escape = False
                    continue
                if ch == "\\":
                    escape = True
                    continue
                if ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
                continue
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return text[start: idx + 1]
        return ""

    def _normalize_interview_questions(
        self,
        questions: Any,
        fallback_questions: List[Dict[str, Any]],
    ) -> Optional[List[Dict[str, Any]]]:
        if not isinstance(questions, list) or len(questions) < 3:
            return None

        fallback_by_id: Dict[str, Dict[str, Any]] = {}
        for item in fallback_questions:
            qid = str(item.get("id", "")).strip()
            if qid:
                fallback_by_id[qid] = item

        id_order = ["perspective", "target", "message"]
        id_aliases = {
            "perspective": {"perspective", "persona", "viewpoint", "second_persona", "視点", "立場", "ペルソナ"},
            "target": {"target", "audience", "reader", "ターゲット", "読者"},
            "message": {"message", "core_message", "main_message", "核心", "メッセージ"},
        }

        normalized: List[Dict[str, Any]] = []
        used: set[str] = set()

        for idx, raw in enumerate(questions[:3]):
            item = raw if isinstance(raw, dict) else {}
            raw_id = str(item.get("id", "")).strip().lower()
            qid = ""
            for key in id_order:
                if raw_id in id_aliases[key]:
                    qid = key
                    break
            if not qid or qid in used:
                for fallback_id in id_order:
                    if fallback_id not in used:
                        qid = fallback_id
                        break
            if not qid:
                return None
            used.add(qid)

            fallback = fallback_by_id.get(qid, {})
            source_question = self._sanitize_interview_question_text(item.get("question", ""))
            fallback_question = self._sanitize_interview_question_text(fallback.get("question", ""))
            chosen_question = source_question or fallback_question
            if not chosen_question:
                return None
            if not self._is_natural_interview_question(chosen_question, qid):
                chosen_question = fallback_question or chosen_question
            if not self._is_natural_interview_question(chosen_question, qid):
                return None
            question_text = self._build_user_friendly_interview_question(
                qid=qid,
                source_question=chosen_question,
                fallback_question=fallback_question,
            )
            if not question_text:
                return None
            if (
                qid != "message"
                and question_text
                and not question_text.endswith(("？", "?"))
                and re.search(r"(ですか|でしょうか|ますか)$", question_text)
            ):
                question_text += "？"

            if qid == "message":
                options: Optional[List[str]] = None
            else:
                raw_options = item.get("options")
                cleaned_options: List[str] = []
                fallback_opts_raw = fallback.get("options") or []
                fallback_opts: List[str] = []
                if isinstance(fallback_opts_raw, list):
                    for opt in fallback_opts_raw:
                        opt_text = str(opt).strip()
                        if opt_text and opt_text not in fallback_opts:
                            fallback_opts.append(opt_text)

                if isinstance(raw_options, list):
                    for opt in raw_options:
                        opt_text = str(opt).strip()
                        if opt_text and opt_text not in cleaned_options:
                            cleaned_options.append(opt_text)

                options = self._select_interview_options(
                    qid=qid,
                    llm_options=cleaned_options,
                    fallback_options=fallback_opts,
                )
                if len(options) < 2:
                    return None

            normalized.append(
                {
                    "id": qid,
                    "question": question_text,
                    "options": options,
                }
            )

        return normalized

    def _select_interview_options(
        self,
        *,
        qid: str,
        llm_options: List[str],
        fallback_options: List[str],
    ) -> List[str]:
        normalized_llm_options: List[str] = []
        for opt in llm_options:
            option_text = self._sanitize_interview_option_text(opt, qid=qid)
            if option_text and option_text not in normalized_llm_options:
                normalized_llm_options.append(option_text)
        normalized_llm_options = self._sort_interview_options_for_question(
            qid=qid,
            options=normalized_llm_options,
        )

        normalized_fallback_options: List[str] = []
        for opt in fallback_options:
            option_text = self._sanitize_interview_option_text(opt, qid=qid)
            if option_text and option_text not in normalized_fallback_options:
                normalized_fallback_options.append(option_text)
        normalized_fallback_options = self._sort_interview_options_for_question(
            qid=qid,
            options=normalized_fallback_options,
        )

        compatible_llm_options = [
            opt for opt in normalized_llm_options
            if self._interview_option_matches_question_role(opt, qid=qid)
        ]
        specific_options = [opt for opt in compatible_llm_options if self._has_specific_content(opt)]
        if len(specific_options) >= 2:
            base_options = specific_options[:INTERVIEW_OPTION_MAX]
        elif len(compatible_llm_options) >= 2 and not normalized_fallback_options:
            base_options = compatible_llm_options[:INTERVIEW_OPTION_MAX]
        else:
            base_options = normalized_fallback_options[:INTERVIEW_OPTION_MAX]

        normalized: List[str] = []
        for opt in base_options:
            option_text = str(opt).strip()
            if option_text and option_text not in normalized:
                normalized.append(option_text)

        if len(normalized) < 2:
            for opt in compatible_llm_options:
                option_text = str(opt).strip()
                if option_text and option_text not in normalized:
                    normalized.append(option_text)
                if len(normalized) >= 2:
                    break
        if len(normalized) < 2:
            for opt in normalized_fallback_options:
                option_text = str(opt).strip()
                if option_text and option_text not in normalized:
                    normalized.append(option_text)
                if len(normalized) >= 2:
                    break

        normalized = self._ensure_interview_escape_option(
            qid=qid,
            options=normalized,
            fallback_options=normalized_fallback_options,
        )
        return normalized[:INTERVIEW_OPTION_MAX]

    def _sort_interview_options_for_question(self, *, qid: str, options: List[str]) -> List[str]:
        if qid != "perspective":
            return options
        indexed = list(enumerate(options))
        indexed.sort(
            key=lambda item: (-self._perspective_option_priority(item[1]), item[0]),
        )
        return [option for _, option in indexed]

    def _perspective_option_priority(self, text: str) -> int:
        candidate = self._sanitize_interview_question_text(text)
        if not candidate:
            return -100
        if "指定しない" in candidate:
            return -10
        score = 0
        if re.search(r"(利用シーン|導入初期|判断軸|現場|変更点|対象者|注意点|限界|安心感)", candidate):
            score += 4
        if re.search(r"(法務|コンプライアンス|技術実装|企業ブランディング|教育設計|医療)", candidate):
            score += 4
        if "知見を混ぜる" in candidate:
            score += 3
        if re.search(r"(伝える|示す|整理する|切り分ける|補う|前面に出す)", candidate):
            score += 1
        if candidate == "価値の違いを具体化する":
            score -= 1
        return score

    def _replace_last_or_append_option(self, options: List[str], candidate: str) -> List[str]:
        candidate_text = str(candidate).strip()
        if not candidate_text or candidate_text in options:
            return options
        if len(options) >= INTERVIEW_OPTION_MAX:
            if INTERVIEW_OPTION_MAX == 0:
                return options
            return options[: INTERVIEW_OPTION_MAX - 1] + [candidate_text]
        return options + [candidate_text]

    def _ensure_interview_escape_option(
        self,
        *,
        qid: str,
        options: List[str],
        fallback_options: List[str],
    ) -> List[str]:
        normalized: List[str] = []
        for opt in options:
            option_text = str(opt).strip()
            if option_text and option_text not in normalized:
                normalized.append(option_text)

        if qid == "perspective":
            has_escape = any("指定しない" in opt for opt in normalized)
            if not has_escape:
                escape = next((opt for opt in fallback_options if "指定しない" in str(opt)), "指定しない")
                normalized = self._replace_last_or_append_option(normalized, escape)
        elif qid == "target":
            has_escape = any(
                re.search(r"(一般読者|このテーマに関心のある読者|幅広い読者)", opt)
                for opt in normalized
            )
            if not has_escape:
                escape = next(
                    (
                        opt
                        for opt in fallback_options
                        if re.search(r"(一般読者|このテーマに関心のある読者|幅広い読者)", str(opt))
                    ),
                    "一般読者",
                )
                normalized = self._replace_last_or_append_option(normalized, escape)
        return normalized

    def _sanitize_interview_question_text(self, text: Any) -> str:
        cleaned = re.sub(r"[\r\n\t]+", " ", str(text or ""))
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if (
            cleaned.startswith("「")
            and cleaned.endswith("」")
            and cleaned.count("「") == 1
            and cleaned.count("」") == 1
        ):
            cleaned = cleaned[1:-1].strip()
        return cleaned

    def _sanitize_interview_option_text(self, text: Any, *, qid: str) -> str:
        cleaned = self._sanitize_interview_question_text(text)
        if not cleaned:
            return ""

        # LLMが二択風の文を返した場合の先頭ノイズを除去
        cleaned = re.sub(r"^(?:はい|いいえ|yes|no)(?:[、,，:：\-\s]+)", "", cleaned, flags=re.I)
        cleaned = re.sub(r"^[・\-*]\s*", "", cleaned)
        cleaned = cleaned.strip(" 、。:：,")

        # 単独の二択語は候補として無効
        if re.fullmatch(r"(?:はい|いいえ|yes|no)", cleaned, re.I):
            return ""

        # target は対象語のみ残す（例: 「対象: 一般読者」）
        if qid == "target":
            cleaned = re.sub(r"^(?:対象(?:読者)?(?:は)?|読者(?:層)?)(?:[：:]\s*)", "", cleaned)
            cleaned = cleaned.strip(" 、。:：,")

        return cleaned

    def _interview_option_matches_question_role(self, text: str, *, qid: str) -> bool:
        candidate = str(text or "").strip()
        if not candidate:
            return False
        if qid == "target":
            return self._looks_audience_option(candidate)
        if qid == "perspective":
            return self._looks_perspective_option(candidate)
        return True

    def _looks_audience_option(self, text: str) -> bool:
        candidate = self._sanitize_interview_question_text(text)
        if not candidate:
            return False
        compact = re.sub(r"\s+", "", candidate)
        if re.search(r"(メッセージ|核心|読後|残したい|一文)", compact):
            return False
        if re.search(r"(効果|削減|安心感|価値|メリット|強み|実績|優位性)$", compact):
            return False
        audience_markers = (
            r"(向け|読者|利用者|ユーザー|顧客|候補者|担当者|管理職|経営者|意思決定者|"
            r"初心者|開発者|エンジニア|医療従事者|患者|家族|投資家|株主|メンバー|"
            r"受講者|学習者|既存顧客|既存利用者|一般読者|幅広い読者)"
        )
        if re.search(audience_markers, candidate):
            return True
        if re.fullmatch(r"(?:一般|幅広い)?(?:層|人たち|人)", candidate):
            return True
        return False

    def _looks_perspective_option(self, text: str) -> bool:
        candidate = self._sanitize_interview_question_text(text)
        if not candidate:
            return False
        if "指定しない" in candidate:
            return True
        if self._looks_audience_option(candidate):
            return False
        perspective_markers = (
            r"(視点|知見|重視|示す|伝える|補う|整理する|説明する|具体化する|"
            r"中心にする|優先する|混ぜる|前面に出す|切り分ける|先に示す|言い換える)"
        )
        return bool(re.search(perspective_markers, candidate))

    def _extract_interview_question_theme(self, text: str) -> str:
        candidate = self._sanitize_interview_question_text(text)
        if not candidate:
            return ""
        match = re.search(fr"「([^」]{{2,{INTERVIEW_THEME_QUOTE_MAX_LEN}}})」", candidate)
        if not match:
            return ""
        theme = self._normalize_interview_display_theme(match.group(1).strip())
        if not theme or theme == "このテーマ":
            return ""
        return theme

    def _extract_interview_message_tail(self, text: str) -> str:
        candidate = self._sanitize_interview_question_text(text)
        if not candidate:
            return ""
        snippets = re.findall(r"（[^）]{4,90}）", candidate)
        for snippet in snippets:
            if re.search(r"(体験談|公式情報|一次情報|事実|データ)", snippet):
                return snippet
        return ""

    def _build_user_friendly_interview_question(
        self,
        *,
        qid: str,
        source_question: str,
        fallback_question: str,
    ) -> str:
        def _compact_topic(theme_text: str) -> str:
            normalized = self._normalize_interview_display_theme(theme_text)
            if not normalized or normalized == "このテーマ":
                return "この記事"
            normalized = self._sanitize_interview_theme_candidate(
                normalized,
                max_len=INTERVIEW_QUESTION_TOPIC_MAX_LEN,
            ).rstrip(" 、。・:：,，")
            if len(normalized) < 4:
                return "この記事"
            if re.search(r"(?:で|に|を|が|と|は|も|へ|や|の|な|し|て|た)$", normalized):
                return "この記事"
            return f"「{normalized}」"

        # message は文面を固定して、質問品質と引用一貫性を優先する
        if qid == "message":
            tail = self._extract_interview_message_tail(fallback_question) or self._extract_interview_message_tail(source_question)
            base = "この記事で読後に最も残したい核心メッセージを1文で教えてください。"
            return f"{base}{tail}" if tail else base

        theme = self._extract_interview_question_theme(fallback_question) or self._extract_interview_question_theme(source_question)
        topic = _compact_topic(theme)

        if qid == "perspective":
            return f"{topic}をわかりやすく伝えるため、どの視点で書きますか？"
        if qid == "target":
            target_subject = "この記事は" if topic == "この記事" else f"{topic}の記事は"
            return f"{target_subject}、主に誰に向けて書きますか？"
        return source_question or fallback_question

    # R14: 汎用的な漢字語（固有名詞ではない）を除外するセット
    _GENERIC_KANJI_WORDS = {
        "視点", "背景", "記者", "教育", "技術", "専門", "意義", "読者",
        "経営", "管理", "実装", "知見", "立場", "対象", "意思", "決定",
        "一般", "関心", "核心", "補強", "解説", "実務", "影響", "整理",
        "指定", "質問", "選択", "回答", "企業", "担当", "導入", "検討",
        "意思決定者", "経営者", "教育者", "技術者", "一般読者",
        "初心者", "実務担当者", "医療従事者",
    }

    def _has_specific_content(self, text: str) -> bool:
        """テキストがソース固有の具体要素（固有名詞・数値・組織名等）を含むか判定する。"""
        if not text:
            return False
        # カタカナ3文字以上の連続（ブランド名・サービス名等）
        if re.search(r"[ァ-ヶー]{3,}", text):
            return True
        # 数値2桁以上（年度・金額・統計等）
        if re.search(r"\d{2,}", text):
            return True
        # 鉤括弧内の具体語（固有名詞・専門用語等）
        if re.search(r"「[^」]{3,20}」", text):
            return True
        # 漢字4文字以上の連続で汎用語でないもの（組織名・制度名等）
        kanji_matches = re.findall(r"[\u4e00-\u9fff]{4,}", text)
        for km in kanji_matches:
            if km not in self._GENERIC_KANJI_WORDS:
                return True
        return False

    def _is_natural_interview_question(self, text: str, qid: str) -> bool:
        candidate = self._sanitize_interview_question_text(text)
        if not candidate:
            return False
        if len(candidate) < 10 or len(candidate) > 90:
            return False
        if re.search(r"https?://|[A-Za-z]:\\|[/\\\\].{3,}", candidate):
            return False
        if re.search(r"\.(pdf|docx?|pptx?|xlsx?|csv|txt|md)\b", candidate, re.I):
            return False
        if re.search(r"(system prompt|developer message|ignore)", candidate, re.I):
            return False

        keyword_patterns = {
            "perspective": r"(視点|立場|知見|切り口|補強)",
            "target": r"(誰|読者|対象|向け|主に)",
            "message": r"(メッセージ|核心|読後|伝えたい|残したい|一文)",
        }
        pattern = keyword_patterns.get(qid, "")
        if pattern and not re.search(pattern, candidate):
            return False

        if qid != "message" and not re.search(r"(？|\?|ですか|でしょうか|ますか)$", candidate):
            return False
        return True

    def _validate_interview_questions(self, questions: Any) -> bool:
        if not isinstance(questions, list) or len(questions) != 3:
            return False
        required = {"perspective", "target", "message"}
        actual = set()
        for item in questions:
            if not isinstance(item, dict):
                return False
            qid = str(item.get("id", "")).strip()
            qtext = str(item.get("question", "")).strip()
            if not qid or not qtext:
                return False
            if qid not in required:
                return False
            actual.add(qid)
            options = item.get("options")
            if qid == "message":
                if options not in (None, []):
                    return False
            else:
                if not isinstance(options, list) or len(options) < 2:
                    return False
        return actual == required

    def _build_dynamic_interview_fallback(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
    ) -> List[Dict[str, Any]]:
        context_text = " ".join(
            [
                " ".join((ctx.title or "") for ctx in contexts[:4]),
                " ".join(((ctx.content or "")[:800]) for ctx in contexts[:3]),
            ]
        )
        text = " ".join([user_prompt or "", context_text])
        theme_hint = self._extract_interview_theme_hint(contexts, user_prompt, article_type)
        display_theme = self._normalize_interview_display_theme(theme_hint)
        is_prelaunch = bool(
            re.search(r"(発売前|リリース前|ローンチ前|未発売|提供前|準備中|開発中|ベータ|β|beta)", text, re.I)
        )
        wants_no_experience = bool(
            re.search(
                r"(体験談|経験談|エピソード|実体験).{0,12}(不要|なし|避け|入れない|控え|使わない)|"
                r"(公式情報|一次情報|事実ベース|客観的|解説中心)",
                text,
                re.I,
            )
        )
        wants_experience = bool(
            re.search(
                r"(体験談|経験談|エピソード|実体験).{0,12}(入れたい|入れる|重視|使いたい|欲しい)|"
                r"(共感重視|ストーリー重視)",
                text,
                re.I,
            )
        ) and not wants_no_experience and not is_prelaunch
        is_recruiting_intent = bool(
            re.search(
                r"(採用|応募|求職|就職|候補者|面接|人事|リクルート|カルチャー|社風|働き方|社員紹介)",
                text,
                re.I,
            )
        )

        article_key = str(article_type or "").strip().lower()
        announcement_like = article_key == "announcement"
        perspective_options: List[str] = ["指定しない"]

        def _add_unique(items: List[str], candidate: str) -> None:
            if candidate and candidate not in items:
                items.append(candidate)

        def _count_hits(pattern: str) -> int:
            return len(re.findall(pattern, context_text, re.I))

        def _domain_score(
            pattern: str,
            *,
            strong_pattern: str = "",
            exclude_pattern: str = "",
            weight: int = 1,
            strong_bonus: int = 3,
            exclude_penalty: int = 2,
        ) -> int:
            score = _count_hits(pattern) * max(1, weight)
            if strong_pattern and re.search(strong_pattern, context_text, re.I):
                score += max(1, strong_bonus)
            if exclude_pattern:
                score -= _count_hits(exclude_pattern) * max(1, exclude_penalty)
            return max(0, score)

        # 単発の語彙ノイズでは専門ドメイン判定しない（例: 食品企業ページ内の「病院」「システム」）
        corporate_score = _domain_score(
            r"(企業|ブランド|サービス|導入|顧客|事例|企業情報|理念|ビジョン|ミッション|事業概要)",
            strong_pattern=r"(会社概要|トップメッセージ|企業理念|ミッション|ビジョン|事業内容)",
            strong_bonus=2,
        )
        finance_score = _domain_score(
            r"(IR|決算|有価証券報告書|財務|バランスシート|BS|PL|CF|株主|投資家|収益|利益|KPI)",
            strong_pattern=r"(有価証券報告書|決算短信|株主総会|投資家向け資料|IR情報)",
        )
        legal_score = _domain_score(
            r"(法令|法務|コンプライアンス|規制|ガイドライン|薬機法|景表法|個人情報)",
            strong_pattern=r"(薬機法|景表法|個人情報保護法|コンプライアンス)",
        )
        technical_score = _domain_score(
            r"(エンジニア|技術者|IT|DX|API|実装|設計|インフラ|アーキテクチャ|SRE|DevOps|SDK|ソフトウェア|システム開発|クラウド|データ基盤|コードベース)",
            strong_pattern=r"(API|アーキテクチャ|SRE|DevOps|SDK|ソフトウェア|システム開発|クラウド|データ基盤|コードベース)",
            exclude_pattern=r"(製造技術|加工技術|調理技術|技術指導|職人技)",
        )
        medical_score = _domain_score(
            r"(医療|患者|治療|臨床|医薬品|薬剤|副作用|疾患|病院|医師)",
            strong_pattern=r"(臨床|医薬品|薬剤|副作用|疾患|製薬|治験|医療機関)",
            exclude_pattern=r"(病院向け配送|病院向け食品|介護食|学校給食)",
        )
        education_score = _domain_score(
            r"(教育|研修|学習|初心者向け|入門|教材|講座|授業)",
            strong_pattern=r"(教材|講座|授業|カリキュラム|シラバス)",
        )
        food_score = _domain_score(
            r"(食品|食材|冷凍食品|惣菜|給食|厨房|水産|農産|畜産|食品卸|フーズ)",
            strong_pattern=r"(業務用食材|食品卸|商品案内|メニュー提案)",
            strong_bonus=2,
        )

        has_corporate = article_type == "branding" or corporate_score >= 2
        has_finance = finance_score >= 3
        has_legal = legal_score >= 3
        has_technical = technical_score >= 4
        has_medical = medical_score >= 4
        has_education = education_score >= 3

        # 食品流通文脈での単語ノイズ抑制（病院向け配送など）
        if food_score >= 2 and medical_score < 6:
            has_medical = False
        if food_score >= 2 and technical_score < 6:
            has_technical = False
        logger.debug(
            "Interview domain score: corporate=%s finance=%s legal=%s technical=%s medical=%s education=%s food=%s",
            corporate_score,
            finance_score,
            legal_score,
            technical_score,
            medical_score,
            education_score,
            food_score,
        )

        if announcement_like:
            perspective_options = [
                "指定しない",
                "変更点を先に短く示す",
                "対象者と開始時期を先に示す",
                "利用者への影響と確認事項を先に示す",
            ]
        elif article_key == "branding":
            perspective_options = [
                "指定しない",
                "利用シーンから価値を伝える",
                "価値の違いを具体化する",
            ]
            if has_corporate:
                _add_unique(perspective_options, "企業ブランディング担当の知見を混ぜる")
            if has_finance:
                _add_unique(perspective_options, "IR・財務の知見を混ぜる")
            if has_legal:
                _add_unique(perspective_options, "法務・コンプライアンスの知見を混ぜる")
            if has_technical:
                _add_unique(perspective_options, "技術実装の知見を混ぜる")
            if has_medical:
                _add_unique(perspective_options, "医療・患者理解の知見を混ぜる")
            if has_education:
                _add_unique(perspective_options, "教育設計の知見を混ぜる")
            if len(perspective_options) < 4:
                _add_unique(perspective_options, "選ぶ理由を判断軸で示す")
        elif article_key == "corporate_culture":
            perspective_options = [
                "指定しない",
                "理念より日々の行動から伝える",
                "制度より現場の工夫を中心にする",
                "価値観が判断に出る場面を示す",
            ]
            if is_recruiting_intent:
                _add_unique(perspective_options, "採用候補者が社風を想像しやすくする")
            else:
                _add_unique(perspective_options, "既存メンバーにも伝わる実践例を優先する")
        elif article_key == "ai":
            perspective_options = [
                "指定しない",
                "一次情報の要点整理を重視する",
                "仕組みより判断基準を先に示す",
                "できることと限界を分けて説明する",
            ]
            if has_legal:
                _add_unique(perspective_options, "法務・ルール面の影響を補う")
            if has_technical:
                _add_unique(perspective_options, "実装・運用の観点を補う")
            if has_finance:
                _add_unique(perspective_options, "投資対効果の観点を補う")
            if has_education:
                _add_unique(perspective_options, "初学者向けのかみ砕き方を補う")
            if len(perspective_options) < 4:
                _add_unique(perspective_options, "導入時の注意点を先に示す")
        else:
            if has_corporate:
                _add_unique(perspective_options, "企業ブランディング担当の知見を混ぜる")
            if has_finance:
                _add_unique(perspective_options, "IR・財務の知見を混ぜる")
            if has_legal:
                _add_unique(perspective_options, "法務・コンプライアンスの知見を混ぜる")
            if has_technical:
                _add_unique(perspective_options, "技術実装の知見を混ぜる")
            if has_medical:
                _add_unique(perspective_options, "医療・患者理解の知見を混ぜる")
            if has_education:
                _add_unique(perspective_options, "教育設計の知見を混ぜる")
        if len(perspective_options) < 3:
            _add_unique(perspective_options, "一次情報の要点整理を重視する")
        perspective_options = perspective_options[:INTERVIEW_OPTION_MAX]

        target_options: List[str] = []
        if announcement_like:
            target_options.extend(["現在の利用者", "対象端末の利用者", "運用担当者"])
        elif article_key == "branding":
            target_options.extend(["導入を検討する担当者", "比較検討中の読者", "既存顧客"])
            if is_recruiting_intent:
                target_options.append("採用候補者")
        elif article_key == "corporate_culture":
            target_options.extend(["採用候補者", "既存メンバー", "一般読者"])
            if not is_recruiting_intent:
                target_options.append("チームリーダー・管理職")
        elif article_key == "ai":
            target_options.extend(["実務担当者", "導入を判断する担当者", "一般読者"])
            if has_technical:
                target_options.append("開発者")
        elif is_prelaunch:
            target_options.extend(["導入を検討する担当者", "将来の顧客候補", "一般読者"])
        if has_finance:
            target_options.extend(["投資家・株主", "IR/経営企画担当", "一般読者"])
        if has_technical:
            target_options.extend(["現場のエンジニア", "技術導入を判断する担当者", "初心者"])
        if has_medical:
            target_options.extend(["医療従事者", "患者・家族", "一般読者"])
        if has_corporate:
            target_options.extend(["導入を検討する担当者", "既存顧客"])
            if is_recruiting_intent:
                target_options.append("採用候補者")
        if has_education:
            target_options.extend(["学習者・受講者", "教育担当者", "初心者"])
        if not target_options and article_key == "branding":
            target_options.extend(["導入を検討する担当者", "既存顧客", "一般読者"])
        if not target_options:
            target_options.extend(
                [
                    "このテーマに関心のある読者",
                    "関連領域の実務担当者",
                    "一般読者",
                ]
            )
        target_options = list(dict.fromkeys(target_options))
        target_options = self._ensure_interview_escape_option(
            qid="target",
            options=target_options,
            fallback_options=target_options + ["一般読者", "このテーマに関心のある読者"],
        )[:INTERVIEW_OPTION_MAX]

        if announcement_like:
            message_question = (
                "この記事で最初に明示すべき変更点や確認事項を1文で教えてください。"
                "（宣伝ではなく、利用者向けのお知らせとして事実ベースで）"
            )
        elif is_prelaunch or wants_no_experience:
            message_question = (
                "この記事で読後に最も残したい核心メッセージを1文で教えてください。"
                "（体験談は入れず、公式情報・確認可能な事実ベースで伝える前提）"
            )
        elif wants_experience:
            message_question = (
                "この記事で読後に最も残したい核心メッセージを1文で教えてください。"
                "（体験談を入れる場合、どの事実・データに紐づけるかも意識して）"
            )
        else:
            message_question = "この記事で読後に最も残したい核心メッセージを1文で教えてください。"

        return [
            {
                "id": "perspective",
                "question": f"「{display_theme}」をわかりやすく伝えるため、どの視点で書きますか？",
                "options": perspective_options[:INTERVIEW_OPTION_MAX],
            },
            {
                "id": "target",
                "question": f"「{display_theme}」の記事は、主に誰に向けて書きますか？",
                "options": target_options,
            },
            {
                "id": "message",
                "question": message_question,
                "options": None,
            },
        ]

    def _extract_interview_theme_hint(
        self,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
    ) -> str:
        title_hint = ""
        for ctx in contexts:
            title = (ctx.title or "").strip()
            cleaned_title = self._sanitize_interview_theme_candidate(title, max_len=INTERVIEW_THEME_TITLE_MAX_LEN)
            if cleaned_title and cleaned_title != "無題":
                title_hint = cleaned_title
                break
        prompt_text = (user_prompt or "").strip()
        prompt_hint = ""
        if prompt_text:
            cleaned = re.sub(r"[\n\r\t]+", " ", prompt_text)
            cleaned = re.sub(r"https?://\S+", " ", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if re.fullmatch(r"(の)?(note|ブログ|記事).{0,12}", cleaned, re.I):
                cleaned = ""
            prompt_hint = self._sanitize_interview_theme_candidate(cleaned, max_len=INTERVIEW_THEME_PROMPT_MAX_LEN)
        if prompt_hint and len(prompt_hint) >= 6:
            return prompt_hint
        if title_hint and prompt_hint:
            if title_hint in prompt_hint or prompt_hint in title_hint:
                return prompt_hint
            return prompt_hint
        if title_hint:
            return title_hint
        if prompt_hint:
            return prompt_hint
        return _article_type_labels().get(article_type, article_type)[:INTERVIEW_THEME_TITLE_MAX_LEN]

    def _sanitize_interview_theme_candidate(self, text: str, max_len: int = 24) -> str:
        cleaned = str(text or "").strip()
        if not cleaned:
            return ""

        cleaned = re.sub(r"https?://\S+", " ", cleaned)
        cleaned = re.sub(r"[「」『』【】\[\]{}()<>]", " ", cleaned)
        cleaned = re.sub(
            r"[^\s/\\]+\.(pdf|docx?|pptx?|xlsx?|csv|txt|md)",
            " ",
            cleaned,
            flags=re.I,
        )
        cleaned = re.sub(r"\b(?:uploads?|download|file|source)\b", " ", cleaned, flags=re.I)
        cleaned = re.sub(r"[\"'`]+", "", cleaned)
        cleaned = re.sub(r"[|/]+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -_・")
        if len(cleaned) < 3:
            return ""
        cleaned = cleaned.rstrip(" 、。")
        if len(cleaned) <= max_len:
            return cleaned

        clipped = cleaned[:max_len]
        boundary = max(
            clipped.rfind("、"),
            clipped.rfind("。"),
            clipped.rfind("・"),
            clipped.rfind(" "),
            clipped.rfind("："),
            clipped.rfind(":"),
            clipped.rfind("，"),
            clipped.rfind(","),
        )
        if boundary >= int(max_len * 0.55):
            clipped = clipped[:boundary]
        clipped = clipped.rstrip(" 、。・:：,，")
        return clipped or cleaned[:max_len].rstrip(" 、。")

    def _normalize_interview_display_theme(self, theme_hint: str) -> str:
        cleaned = self._sanitize_interview_theme_candidate(theme_hint, max_len=INTERVIEW_THEME_DISPLAY_MAX_LEN)
        if not cleaned:
            return "このテーマ"
        if len(cleaned) < 4:
            return "このテーマ"
        if re.search(r"\.(pdf|docx?|pptx?|xlsx?|csv|txt|md)\b", cleaned, re.I):
            return "このテーマ"
        if "/" in cleaned or "\\" in cleaned:
            return "このテーマ"
        if re.search(r"^[a-z0-9._-]{3,}$", cleaned, re.I):
            return "このテーマ"
        if re.search(r"(して|してください|してほしい|して下さい|教えて|まとめて|作って|書いて|伝えて)$", cleaned):
            return "このテーマ"
        return cleaned

    def _derive_interview_constraints(self, user_prompt: str = "") -> Dict[str, str]:
        """インタビュー回答から、生成時に優先すべき制約を抽出する。"""
        merged_text = " ".join(
            [
                user_prompt or "",
                self._interview_answers.get("perspective", ""),
                self._interview_answers.get("target", ""),
                self._interview_answers.get("message", ""),
            ]
        ).strip()
        if not merged_text:
            return {}

        constraints: Dict[str, str] = {}

        if re.search(r"(発売前|リリース前|ローンチ前|未発売|提供前|準備中|開発中|ベータ|β|beta)", merged_text, re.I):
            constraints["service_stage"] = "prelaunch"
            constraints["focus"] = "explanation"
            constraints["evidence_mode"] = "strict"
            constraints["experience_policy"] = "forbid"
        elif re.search(r"(発売後|リリース後|ローンチ後|販売中|提供中|導入済|既存顧客|運用中)", merged_text, re.I):
            constraints["service_stage"] = "launched"

        if re.search(
            r"(体験談|経験談|エピソード|実体験).{0,12}(不要|なし|避け|入れない|控え|使わない)|"
            r"(公式情報|一次情報|事実ベース|客観的|解説中心)",
            merged_text,
            re.I,
        ):
            constraints["experience_policy"] = "forbid"
            constraints["focus"] = "explanation"
            constraints["evidence_mode"] = "strict"
        elif re.search(
            r"(体験談|経験談|エピソード|実体験).{0,12}(入れたい|入れる|重視|使いたい|欲しい)|"
            r"(共感重視|ストーリー重視)",
            merged_text,
            re.I,
        ):
            if constraints.get("service_stage") != "prelaunch":
                constraints.setdefault("experience_policy", "allow")
                constraints.setdefault("focus", "experience")
                constraints.setdefault("evidence_mode", "normal")

        return constraints

    def _apply_interview_constraints(self, constraints: Dict[str, str]) -> None:
        """抽出した制約を現在のパイプライン方針へ反映する。"""
        if not constraints:
            return
        policy = dict(self._pipeline_policy or {})

        focus_override = constraints.get("focus")
        focus_defaults = {
            "analysis": ("low", "low", 0.4),
            "explanation": ("med", "med", 0.45),
            "experience": ("high", "high", 0.5),
        }
        if focus_override in focus_defaults:
            empathy_level, humanity_level, curiosity_target = focus_defaults[focus_override]
            self._effective_writing_focus = focus_override
            policy["focus"] = focus_override
            policy["empathy_level"] = empathy_level
            policy["humanity_level"] = humanity_level
            policy["curiosity_target"] = curiosity_target

        evidence_override = constraints.get("evidence_mode")
        if evidence_override in ("strict", "normal"):
            policy["evidence_mode"] = evidence_override
            if evidence_override == "strict":
                policy["style_profile"] = "formal"
            elif policy.get("focus") == "experience":
                current_perspective = str(getattr(self, "_current_perspective", "") or "").strip().lower()
                policy["style_profile"] = "balanced" if current_perspective == "corporate" else "casual"
            else:
                policy["style_profile"] = "balanced"

        rationale = list(policy.get("rationale") or [])
        summary = ",".join(f"{k}:{v}" for k, v in sorted(constraints.items()))
        if summary:
            rationale.append(f"interview:{summary}")
        policy["rationale"] = rationale[-10:]
        self._pipeline_policy = policy

    def _build_interview_constraint_guide(self, constraints: Dict[str, str]) -> str:
        """モデル入力に渡す、回答優先の運用ルールを構築する。"""
        if not constraints:
            return ""
        lines = [
            "【インタビュー回答の優先ルール】",
            "- ユーザーの回答指示は、推測より優先して本文方針へ反映する。",
        ]
        if constraints.get("service_stage") == "prelaunch":
            lines.append("- サービス発売前の前提で、断定的な利用体験の記述は行わない。")
        if constraints.get("experience_policy") == "forbid":
            lines.append("- 体験談・個人エピソードの挿入は行わない。公式情報と確認可能な事実を中心に書く。")
        elif constraints.get("experience_policy") == "allow":
            lines.append("- 体験談を使う場合は、参照データ内の具体事実に紐づけて記述する。")
        if constraints.get("evidence_mode") == "strict":
            lines.append("- 根拠が弱い内容は断定せず、推定と事実を明確に分ける。")
        return "\n".join(lines)
    
    def set_interview_answers(self, answers: Dict[str, str]) -> None:
        """インタビュー回答を設定する"""
        sanitized: Dict[str, str] = {}
        for key, value in (answers or {}).items():
            cleaned = sanitize_untrusted_text(value, max_length=240)
            if cleaned:
                sanitized[key] = cleaned
                if key == "perspective":
                    perspective_key = self._normalize_perspective_key(cleaned)
                    if perspective_key:
                        sanitized["perspective_key"] = perspective_key
        self._interview_answers = sanitized

    def _normalize_perspective_key(self, raw_value: str) -> str:
        """インタビュー回答の視点文を内部キーへ正規化する。"""
        text = (raw_value or "").strip()
        if not text:
            return ""

        lowered = text.lower()
        direct_map = {
            "auto": "auto",
            "blogger": "blogger",
            "expert": "expert",
            "corporate": "corporate",
            "educator": "educator",
            "journalist": "journalist",
            "friend": "friend",
        }
        if lowered in direct_map:
            return direct_map[lowered]

        if re.search(r"(指定しない|任せる|おまかせ|自動判定|auto)", text, re.I):
            return "auto"
        if re.search(r"(企業|ブランディング|広報|PR|マーケ|コーポレート|顧客価値|会社紹介)", text, re.I):
            return "corporate"
        if re.search(r"(記者|ジャーナリスト|取材|第三者|一次情報)", text, re.I):
            return "journalist"
        if re.search(r"(教育|教育設計|先生|講師)", text, re.I):
            return "educator"
        if re.search(r"(友人|カジュアル|フランク|親しみ)", text, re.I):
            return "friend"
        if re.search(r"(専門家|有資格|コンサル|アナリスト|IR|財務|法務|コンプライアンス|技術実装|技術)", text, re.I):
            return "expert"
        if re.search(r"(個人|体験者|当事者|ブログ|ブロガー)", text, re.I):
            return "blogger"
        return ""

    def set_term_clarifications(self, clarifications: Dict[str, str]) -> None:
        """曖昧語の語義確認結果を設定する。"""
        sanitized: Dict[str, str] = {}
        for key, value in (clarifications or {}).items():
            term = sanitize_untrusted_text(key, max_length=40)
            meaning = sanitize_untrusted_text(value, max_length=120)
            if term and meaning:
                sanitized[term] = meaning
        self._term_clarifications = sanitized

