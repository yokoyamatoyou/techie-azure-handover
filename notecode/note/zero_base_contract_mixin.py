"""zero_base_contract_mixin.py - contract resolution helpers for ArticleGenerator."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from note.article_fetcher import FetchedContent

logger = logging.getLogger(__name__)

ZERO_BASE_CATEGORY_CONTRACT_PROFILES: Dict[str, Dict[str, Any]] = {
    "ai_explanatory": {
        "article_types": {"ai", "explanatory_article"},
        "default_speaker_profile": "編集担当として語る",
        "default_relationship_mode": "guide",
        "default_register_policy": {
            "base_register": "polite",
            "allowed_endings": ["です", "ます", "でした", "ました"],
            "banned_endings": [],
            "max_consecutive_same_ending": 2,
        },
        "default_allowed_pronouns": ["私"],
        "forbidden_topics_base": [],
    },
    "branding": {
        "article_types": {"branding", "daily_happenings"},
        "default_speaker_profile": "運営担当として語る",
        "default_relationship_mode": "guide",
        "default_register_policy": {
            "base_register": "polite",
            "allowed_endings": ["です", "ます", "でした", "ました"],
            "banned_endings": [],
            "max_consecutive_same_ending": 2,
        },
        "default_allowed_pronouns": ["私たち", "当社", "弊社"],
        "forbidden_topics_base": ["採用候補者", "採用活動", "福利厚生"],
    },
    "corporate_culture": {
        "article_types": {"corporate_culture", "corporate", "company_profile"},
        "default_speaker_profile": "運営担当として語る",
        "default_relationship_mode": "guide",
        "default_register_policy": {
            "base_register": "polite",
            "allowed_endings": ["です", "ます", "でした", "ました"],
            "banned_endings": [],
            "max_consecutive_same_ending": 2,
        },
        "default_allowed_pronouns": ["私たち", "当社", "弊社"],
        "forbidden_topics_base": ["採用候補者", "採用活動", "福利厚生"],
    },
    "announcement": {
        "article_types": {"announcement"},
        "default_speaker_profile": "広報担当として語る",
        "default_relationship_mode": "guide",
        "default_register_policy": {
            "base_register": "polite",
            "allowed_endings": ["です", "ます", "でした", "ました"],
            "banned_endings": [],
            "max_consecutive_same_ending": 2,
        },
        "default_allowed_pronouns": ["当社", "弊社"],
        "forbidden_topics_base": [],
    },
    "case_study": {
        "article_types": {"case_study"},
        "default_speaker_profile": "導入支援担当として語る",
        "default_relationship_mode": "guide",
        "default_register_policy": {
            "base_register": "polite",
            "allowed_endings": ["です", "ます", "でした", "ました"],
            "banned_endings": [],
            "max_consecutive_same_ending": 2,
        },
        "default_allowed_pronouns": ["私たち", "当社", "弊社"],
        "forbidden_topics_base": [],
    },
}

_SPEAKER_ROLE_HINT_PATTERN = re.compile(
    r"(担当|編集|筆者|執筆|運営|代表|取締役|経営者|広報|責任者|監修|アナリスト|コンサル|記者|ジャーナリスト|講師|先生|管理者)"
)
_THEME_LIKE_SPEAKER_PATTERN = re.compile(
    r"(活用法|方法|とは|について|解説|比較|ポイント|戦略|課題|テーマ|文章|投稿|読者|このテーマ|するため|を維持|を高め|である)"
)


class ZeroBaseContractMixin:
    @staticmethod
    def _zero_base_normalize_question_source_priority(priority: Any) -> List[str]:
        allowed = ("interview_answers", "user_prompt", "unresolved_items")
        default_order = list(allowed)
        if not isinstance(priority, list):
            return default_order

        cleaned: List[str] = []
        for item in priority:
            key = str(item).strip()
            if key in allowed and key not in cleaned:
                cleaned.append(key)
        for key in default_order:
            if key not in cleaned:
                cleaned.append(key)
        return cleaned

    def _zero_base_extract_prompt_answer(
        self,
        *,
        question_id: str,
        question_text: str,
        user_prompt: str,
        article_type: str,
    ) -> str:
        prompt = self._safe_contract_value(user_prompt)
        if not prompt:
            return ""
        compact = re.sub(r"\s+", " ", prompt).strip()
        if not compact:
            return ""
        compact_sanitized = self._sanitize_contract_text(compact, max_length=180)
        if not compact_sanitized:
            return ""
        compact_signal = self._strip_instructional_clauses(compact_sanitized, max_length=180)
        if not compact_signal:
            compact_signal = compact_sanitized

        qid = (question_id or "").strip().lower()
        if qid == "message":
            segments = [
                seg.strip()
                for seg in re.split(r"(?<=[。！？!?])\s*|\n+", compact_signal)
                if seg and seg.strip()
            ]
            for segment in segments:
                if re.search(
                    r"(?:メッセージ|文言|フレーズ).{0,12}(?:使いたい|使う|入れたい|入れる|盛り込みたい)",
                    segment,
                ):
                    continue
                normalized = re.sub(r"^【[^】]+】", "", segment).strip()
                normalized = re.sub(
                    r"^(?:.+?として)?(?:初投稿(?:で)?|今回は|今回)\s*",
                    "",
                    normalized,
                )
                normalized = re.sub(
                    r"(.+?)(?:を|について)(?:行います|行う|します|する|伝えたい|伝える|紹介したい|紹介する|"
                    r"整理したい|整理する|解説したい|解説する|共有したい|共有する|明確にしたい|明確にする)"
                    r"(?:[。！？!?])?$",
                    r"\1",
                    normalized,
                )
                normalized = self._sanitize_contract_text(normalized, max_length=72)
                normalized = self._normalize_must_cover_item(normalized, max_length=72)
                if not normalized:
                    continue
                if self._is_low_signal_must_cover_item(normalized):
                    continue
                return normalized
            return ""
        if qid == "target":
            # LLM推定は使わず、ユーザー文面から明示シグナルのみ抽出する。
            explicit_patterns = [
                r"([^\s、。]{2,24})(?:向け|向けに|向けの)",
                r"(?:対象|読者)[は:：]?\s*([^\s、。]{2,24})",
                r"(初心者|実務担当者|開発者|経営者|意思決定者|一般読者)",
            ]
            for pattern in explicit_patterns:
                match = re.search(pattern, compact_signal)
                if match:
                    return self._sanitize_contract_text(match.group(1), max_length=32)
            return ""
        if qid == "evidence":
            if re.search(r"(一次情報|公式|出典|根拠|データ|統計|論文)", compact_signal):
                return "一次情報・公式情報を優先する"
            return ""

        # unknown質問は短い要約だけ返す（過剰注入を避ける）
        if question_text:
            return self._sanitize_outline_seed(compact_signal, max_length=72)
        return ""

    def _zero_base_to_reader_question(self, *, question_id: str, answer: str) -> str:
        text = self._safe_contract_value(answer)
        if not text:
            return ""
        qid = (question_id or "").strip().lower()
        announcement_like = (
            self._safe_contract_value(getattr(self, "_current_type", "")).lower() == "announcement"
            or self._safe_contract_value((getattr(self, "_category_policy", {}) or {}).get("base_template")).lower() == "announcement"
        )
        if announcement_like:
            if qid == "message":
                return "何が変わるか"
            if qid == "target":
                return "誰が対象か"
            if qid == "evidence":
                return "いつから・どこで確認できるか"
            if any(token in qid for token in ("impact", "effect", "influence")):
                return "利用者への影響は何か"
            if any(token in qid for token in ("action", "check", "confirm")):
                return "何を確認すべきか"
            return "確認すべき事実は何か"
        if qid == "message":
            return f"{text}を読者が自分ごと化するには？"
        if qid == "target":
            return "読者が自分の状況へ当てはめやすい説明順は何か？"
        if qid == "evidence":
            return f"{text}を裏づける事実は何か？"
        return f"{text}をどう説明すると伝わるか？"

    def _normalize_announcement_fact_item(self, value: str) -> str:
        text = self._sanitize_contract_text(value, max_length=180)
        if not text:
            return ""
        replacements = (
            ("を重視する視点", ""),
            ("を重視する", ""),
            ("を伝える視点", ""),
            ("を整理する視点", ""),
            ("という視点", ""),
            ("の視点", ""),
            ("をどう活用できるか", ""),
            ("どう説明すると伝わるか", ""),
            ("自分ごと化", ""),
        )
        for old, new in replacements:
            text = text.replace(old, new)
        text = re.sub(r"(読者|利用者)が[^\s。]{0,24}(判断|活用|理解)できる", "", text)
        text = re.sub(r"[、。]+$", "", text).strip()
        if any(
            marker in text
            for marker in ("視点", "自分ごと", "どう活用", "どう説明", "判断材料")
        ):
            return ""
        return self._sanitize_outline_seed(text, max_length=120)

    def _extract_announcement_source_fact_items(
        self,
        contexts: List[FetchedContent],
        *,
        limit: int = 3,
    ) -> List[str]:
        facts: List[str] = []
        date_or_time = re.compile(r"\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}:\d{2}|午前\d{1,2}時|午後\d{1,2}時")
        route_markers = (
            "公式サイト",
            "専用ページ",
            "申込",
            "申し込み",
            "フォーム",
            "問い合わせ先",
            "対象",
            "開始",
        )
        for ctx in contexts or []:
            content = self._safe_contract_value(getattr(ctx, "content", ""))
            if not content:
                continue
            sentences = [s.strip() for s in re.split(r"(?<=[。！？])\s*", content) if s.strip()]
            for sentence in sentences:
                compact = self._sanitize_contract_text(sentence, max_length=120)
                if not compact:
                    continue
                if not date_or_time.search(compact) and not any(marker in compact for marker in route_markers):
                    continue
                normalized = self._normalize_announcement_fact_item(compact)
                if not normalized or normalized in facts:
                    continue
                facts.append(normalized)
                if len(facts) >= limit:
                    return facts
        return facts

    def _zero_base_enforce_announcement_fact_consistency(
        self,
        text: str,
        contract: Dict[str, Any],
    ) -> str:
        sample = text or ""
        if not sample:
            return sample
        article_type = self._safe_contract_value(contract.get("article_type")).lower()
        base_template = self._safe_contract_value(contract.get("category_base_template")).lower()
        if article_type != "announcement" and base_template != "announcement":
            return sample

        must_cover = contract.get("must_cover", [])
        must_cover_items = [
            self._safe_contract_value(item)
            for item in (must_cover if isinstance(must_cover, list) else [])
            if self._safe_contract_value(item)
        ]
        authoritative_dates: List[str] = []
        route_phrase = ""
        for item in must_cover_items:
            for literal in re.findall(r"\d{4}年\d{1,2}月\d{1,2}日", item):
                if literal and literal not in authoritative_dates:
                    authoritative_dates.append(literal)
            if not route_phrase and "公式サイトの専用ページ" in item:
                route_phrase = "公式サイトの専用ページ"

        normalized = sample
        if len(authoritative_dates) == 1:
            authoritative_date = authoritative_dates[0]
            short_authoritative_date = re.sub(r"^\d{4}年", "", authoritative_date)

            def _replace_date(match: re.Match[str]) -> str:
                literal = match.group(0)
                return authoritative_date if literal != authoritative_date else literal

            normalized = re.sub(r"\d{4}年\d{1,2}月\d{1,2}日", _replace_date, normalized)
            normalized = re.sub(
                r"(?<!\d{4}年)(\d{1,2}月\d{1,2}日)",
                lambda match: short_authoritative_date if match.group(1) != short_authoritative_date else match.group(1),
                normalized,
            )

        if route_phrase:
            normalized = re.sub(
                r"申し込みは(?:当社の)?(?:指定の|専用の)?(?:ウェブ)?フォームから(行(?:っていただきます|えます|います)|受け付けます)",
                f"申し込みは{route_phrase}から\\1",
                normalized,
            )
            normalized = re.sub(
                r"当社専用ウェブサイトの申込フォーム",
                f"当社{route_phrase}",
                normalized,
            )
            normalized = re.sub(
                r"申込ページが公開されますので、そちらよりお手続きください",
                f"{route_phrase}からお手続きください",
                normalized,
            )

        normalized = re.sub(
            r"多くの場合([^。]{0,32}(?:ご確認|お確かめ)(?:ください|願います|いただきますようお願いいたします))",
            r"\1",
            normalized,
        )
        normalized = re.sub(
            r"多くの場合(?=[^。]{0,40}(?:公式|専用|ご確認|お申し込み|お手続き))",
            "",
            normalized,
        )
        return normalized

    @staticmethod
    def _normalize_register_policy(value: Any) -> Dict[str, Any]:
        default_policy = {
            "base_register": "polite",
            "allowed_endings": ["です", "ます", "でした", "ました"],
            "banned_endings": [],
            "max_consecutive_same_ending": 2,
        }
        if not isinstance(value, dict):
            return dict(default_policy)
        base_register = str(value.get("base_register", default_policy["base_register"]) or "").strip().lower()
        if base_register not in {"polite", "plain"}:
            base_register = default_policy["base_register"]
        allowed_endings = value.get("allowed_endings", default_policy["allowed_endings"])
        banned_endings = value.get("banned_endings", default_policy["banned_endings"])
        if not isinstance(allowed_endings, list):
            allowed_endings = list(default_policy["allowed_endings"])
        if not isinstance(banned_endings, list):
            banned_endings = list(default_policy["banned_endings"])
        allowed_clean = [str(item).strip() for item in allowed_endings if str(item).strip()]
        banned_clean = [str(item).strip() for item in banned_endings if str(item).strip()]
        if not allowed_clean:
            allowed_clean = list(default_policy["allowed_endings"])
        max_consecutive = int(value.get("max_consecutive_same_ending", 2) or 2)
        max_consecutive = max(1, min(4, max_consecutive))
        return {
            "base_register": base_register,
            "allowed_endings": allowed_clean[:12],
            "banned_endings": banned_clean[:12],
            "max_consecutive_same_ending": max_consecutive,
        }

    def _resolve_zero_base_contract_profile(
        self,
        *,
        article_type: str,
        category_base_template: str = "",
    ) -> Dict[str, Any]:
        article_key = self._safe_contract_value(article_type).lower()
        base_key = self._safe_contract_value(category_base_template).lower()
        selected_key = "ai_explanatory"

        for profile_key, profile in ZERO_BASE_CATEGORY_CONTRACT_PROFILES.items():
            article_types = profile.get("article_types", set())
            if isinstance(article_types, set) and article_key in article_types:
                selected_key = profile_key
                break
        else:
            if base_key == "announcement":
                selected_key = "announcement"
            elif base_key == "branding":
                if article_key in {"corporate_culture", "corporate", "company_profile"}:
                    selected_key = "corporate_culture"
                else:
                    selected_key = "branding"
            elif base_key == "ai":
                selected_key = "ai_explanatory"

        profile = dict(ZERO_BASE_CATEGORY_CONTRACT_PROFILES.get(selected_key, ZERO_BASE_CATEGORY_CONTRACT_PROFILES["ai_explanatory"]))
        profile["profile_key"] = selected_key
        return profile

    def _looks_theme_like_speaker_profile(self, value: str) -> bool:
        text = self._safe_contract_value(value)
        if not text:
            return False
        if _THEME_LIKE_SPEAKER_PATTERN.search(text):
            return True
        if len(text) > 28 and re.search(r"(の|を|が|は|に|で|から)", text):
            if not re.search(r"(として|の立場|視点|目線)", text):
                return True
        return False

    def _is_valid_zero_base_speaker_profile(self, value: str) -> bool:
        text = self._safe_contract_value(value)
        if not text:
            return False
        if len(text) > 60:
            return False
        if re.match(r"^#+\s+", text) or text.startswith(("-", "*")):
            return False
        if self._looks_instructional_fragment(text):
            return False
        if self._looks_theme_like_speaker_profile(text):
            return False
        if re.search(r"(として|の立場|視点|目線).{0,10}(語|書|伝|説明)", text):
            return True
        if _SPEAKER_ROLE_HINT_PATTERN.search(text) and len(text) <= 28 and not re.search(r"[。！？!?]", text):
            return True
        return False

    def _resolve_zero_base_speaker_profile_fields(
        self,
        *,
        article_type: str,
        category_base_template: str,
        runtime_input_contract: Dict[str, Any],
        resolved_perspective: str,
    ) -> Dict[str, Any]:
        profile = self._resolve_zero_base_contract_profile(
            article_type=article_type,
            category_base_template=category_base_template,
        )
        interview_answers = runtime_input_contract.get("interview_answers", {})
        if not isinstance(interview_answers, dict):
            interview_answers = {}

        raw_topic_statement = self._normalize_topic_statement_value(
            runtime_input_contract.get("topic_statement")
            or interview_answers.get("perspective")
            or self._interview_answers.get("perspective"),
            max_length=180,
        )
        raw_writer_role = self._sanitize_contract_text(
            runtime_input_contract.get("writer_role")
            or interview_answers.get("writer_role")
            or "",
            max_length=80,
        )
        raw_viewpoint = self._safe_contract_value(
            runtime_input_contract.get("article_viewpoint")
            or runtime_input_contract.get("perspective")
            or resolved_perspective
            or "auto"
        )
        article_viewpoint = self._normalize_perspective_key(raw_viewpoint)

        candidates = [
            self._sanitize_contract_text(runtime_input_contract.get("speaker_profile"), max_length=80),
            raw_writer_role,
            self._sanitize_contract_text(interview_answers.get("speaker_profile"), max_length=80),
            self._sanitize_contract_text(interview_answers.get("perspective"), max_length=80),
        ]
        if article_viewpoint and article_viewpoint != "auto":
            candidates.append(self._label_for_perspective_key(article_viewpoint))

        resolved_speaker_profile = ""
        for candidate in candidates:
            if self._is_valid_zero_base_speaker_profile(candidate):
                resolved_speaker_profile = candidate
                break

        default_speaker_profile = self._safe_contract_value(profile.get("default_speaker_profile"))
        if not resolved_speaker_profile:
            resolved_speaker_profile = default_speaker_profile or "編集担当として語る"

        if not raw_writer_role and self._is_valid_zero_base_speaker_profile(resolved_speaker_profile):
            raw_writer_role = resolved_speaker_profile
        if not raw_writer_role:
            raw_writer_role = default_speaker_profile or resolved_speaker_profile

        if not raw_topic_statement:
            raw_topic_statement = self._derive_topic_statement_from_prompt(
                runtime_input_contract.get("user_instruction")
                or getattr(self, "_latest_user_prompt", ""),
                must_cover=list(runtime_input_contract.get("must_cover", []) or []),
                max_length=180,
            )

        return {
            "profile": profile,
            "speaker_profile": resolved_speaker_profile,
            "writer_role": raw_writer_role,
            "article_viewpoint": article_viewpoint or "auto",
            "topic_statement": raw_topic_statement,
        }

    def _zero_base_contract_base(
        self,
        *,
        article_type: str,
        user_prompt: str,
        target_audience: str,
        writing_focus: str,
        input_contract: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raw_contract = input_contract if isinstance(input_contract, dict) else {}
        resolved_article_type = (
            self._safe_contract_value(article_type).lower()
            or self._safe_contract_value(raw_contract.get("article_type")).lower()
            or self._safe_contract_value(getattr(self, "_current_type", "")).lower()
            or "ai"
        )
        resolved_audience = (
            self._normalize_audience_profile_value(raw_contract.get("audience_profile"))
            or self._normalize_audience_profile_value(target_audience)
            or "一般読者"
        )
        resolved_focus = self._safe_contract_value(raw_contract.get("writing_focus")) or self._safe_contract_value(
            writing_focus
        ) or "auto"
        resolved_perspective = self._safe_contract_value(raw_contract.get("perspective")) or "auto"
        profile_seed = self._safe_contract_value(raw_contract.get("category_base_template"))
        contract_profile = self._resolve_zero_base_contract_profile(
            article_type=resolved_article_type,
            category_base_template=profile_seed,
        )
        speaker_fields = self._resolve_zero_base_speaker_profile_fields(
            article_type=resolved_article_type,
            category_base_template=profile_seed,
            runtime_input_contract=raw_contract,
            resolved_perspective=resolved_perspective,
        )
        prompt_topic_statement = self._derive_topic_statement_from_prompt(
            user_prompt,
            must_cover=list(raw_contract.get("must_cover", []) or []),
            max_length=180,
        )
        current_topic_statement = self._safe_contract_value(speaker_fields.get("topic_statement"))
        must_cover_candidates = {
            self._safe_contract_value(item)
            for item in list(raw_contract.get("must_cover", []) or [])
            if self._safe_contract_value(item)
        }
        if prompt_topic_statement and (
            not current_topic_statement or current_topic_statement in must_cover_candidates
        ):
            speaker_fields["topic_statement"] = prompt_topic_statement
        resolved_tone_profile = self._safe_contract_value(raw_contract.get("tone_profile")) or "auto"
        resolved_content_goal = self._safe_contract_value(raw_contract.get("content_goal")) or "auto"
        resolved_structure = self._safe_contract_value(raw_contract.get("structure")) or "auto"
        resolved_length_mode = self._safe_contract_value(raw_contract.get("length_mode")) or "adaptive"
        audience_profile = self._normalize_audience_profile_value(raw_contract.get("audience_profile")) or resolved_audience
        relationship_mode = self._safe_contract_value(raw_contract.get("relationship_mode")) or self._safe_contract_value(
            contract_profile.get("default_relationship_mode")
        ) or "guide"
        register_policy_seed = raw_contract.get("register_policy")
        if not isinstance(register_policy_seed, dict):
            register_policy_seed = contract_profile.get("default_register_policy", {})
        register_policy = self._normalize_register_policy(register_policy_seed)
        source_inputs = raw_contract.get("source_inputs", [])
        if not isinstance(source_inputs, list):
            source_inputs = []
        interview_answers = raw_contract.get("interview_answers", {})
        if not isinstance(interview_answers, dict):
            interview_answers = {}
        user_instruction = self._sanitize_contract_text(user_prompt, max_length=240)
        user_instruction_terms = self._extract_alignment_anchor_terms(
            user_instruction,
            max_terms=8,
        )
        return {
            "article_type": resolved_article_type,
            "category_base_template": "",
            "category_policy_source": "",
            "contract_profile_key": self._safe_contract_value(contract_profile.get("profile_key")),
            "thesis": self._sanitize_outline_seed(user_prompt, max_length=120) or "読者の意思決定に役立つ論点を整理する",
            "user_instruction": user_instruction,
            "user_instruction_terms": user_instruction_terms[:10],
            "forbidden_topics": [],
            "audience": resolved_audience,
            "speaker_profile": self._safe_contract_value(speaker_fields.get("speaker_profile")),
            "writer_role": self._safe_contract_value(speaker_fields.get("writer_role")),
            "article_viewpoint": self._safe_contract_value(speaker_fields.get("article_viewpoint")) or "auto",
            "topic_statement": self._normalize_topic_statement_value(speaker_fields.get("topic_statement"), max_length=180),
            "audience_profile": audience_profile,
            "relationship_mode": relationship_mode,
            "register_policy": register_policy,
            "allowed_pronouns_hint": list(contract_profile.get("default_allowed_pronouns", []) or [])[:6],
            "intent": "判断材料を整理し、次の行動を明確化する",
            "style": "balanced",
            "must_cover": [],
            "must_not_repeat": ["同義反復", "断定過多"],
            "pre_generation_questions": [],
            "pre_generation_answers": {},
            "unresolved_items": [],
            "cta": "",
            "evidence_mode": "normal",
            "content_goal": resolved_content_goal,
            "structure": resolved_structure,
            "length_mode": resolved_length_mode,
            "tone_profile": resolved_tone_profile,
            "perspective": resolved_perspective,
            "allow_experience": bool(raw_contract.get("allow_experience", getattr(self, "_allow_experience", False))),
            "source_inputs": source_inputs,
            "input_interview_answers": interview_answers,
            "question_source_priority": [
                "interview_answers",
                "user_prompt",
                "unresolved_items",
            ],
            "focus": resolved_focus,
        }

    def _zero_base_resolve_pre_generation_questions(
        self,
        *,
        contexts: List[FetchedContent],
        user_prompt: str,
        article_type: str,
        question_source_priority: Any,
    ) -> Dict[str, Any]:
        announcement_like = str(article_type or "").strip().lower() == "announcement"
        need_question_decision = self.should_ask_pre_generation_questions(contexts, user_prompt, article_type)
        normalized_priority = self._zero_base_normalize_question_source_priority(
            question_source_priority
        )
        has_existing_answers = bool(
            isinstance(getattr(self, "_interview_answers", None), dict)
            and any(str(v or "").strip() for v in getattr(self, "_interview_answers", {}).values())
        )
        if not bool(need_question_decision.get("ask", True)) and not has_existing_answers:
            prompt_audience = self._normalize_audience_profile_value(
                self._zero_base_extract_prompt_answer(
                    question_id="target",
                    question_text="主に誰に向けて書きますか？",
                    user_prompt=user_prompt,
                    article_type=article_type,
                )
            )
            return {
                "pre_generation_questions": [],
                "pre_generation_answers": {"target": prompt_audience} if prompt_audience else {},
                "must_cover": [],
                "unresolved_items": [],
                "question_source_priority": normalized_priority,
                "reader_question_candidates": [],
                "resolved_question_sources": {"target": "user_prompt"} if prompt_audience else {},
                "resolved_audience": prompt_audience,
                "need_question_decision": need_question_decision,
            }
        try:
            questions = self._build_dynamic_interview_fallback(contexts, user_prompt, article_type)
        except Exception as exc:
            logger.debug("Zero-base question fallback generation failed.", exc_info=exc)
            questions = [
                {"id": "message", "question": "核心メッセージを1文で教えてください。"},
                {"id": "target", "question": "主に誰に向けて書きますか？"},
                {"id": "evidence", "question": "優先する根拠は何ですか？"},
            ]

        normalized_questions: List[Dict[str, str]] = []
        for item in questions:
            if not isinstance(item, dict):
                continue
            qid = self._safe_contract_value(item.get("id"))
            question_text = self._sanitize_contract_text(item.get("question"), max_length=180)
            if not qid:
                continue
            if self._looks_instructional_fragment(question_text):
                continue
            normalized_questions.append({"id": qid, "question": question_text})
        if not normalized_questions:
            normalized_questions = [
                {"id": "message", "question": "この投稿で最も伝えたいことは何ですか？"},
                {"id": "target", "question": "読者に期待する理解や行動は何ですか？"},
                {"id": "evidence", "question": "優先して示す根拠は何ですか？"},
            ]

        interview_answers: Dict[str, str] = {}
        for key, value in (self._interview_answers or {}).items():
            qid = self._safe_contract_value(key)
            if qid:
                normalized_value = self._sanitize_contract_text(value, max_length=180)
                interview_answers[qid] = normalized_value
                qrole = self._classify_pre_generation_question_role(qid)
                if qrole in {"target", "perspective", "message", "evidence"}:
                    interview_answers[qrole] = normalized_value

        resolved_answers: Dict[str, str] = {}
        resolved_question_sources: Dict[str, str] = {}
        must_cover: List[str] = []
        reader_question_candidates: List[str] = []
        unresolved_items: List[str] = []
        resolved_audience = ""

        for question in normalized_questions:
            qid = self._safe_contract_value(question.get("id"))
            qtext = self._safe_contract_value(question.get("question"))
            qrole = self._classify_pre_generation_question_role(qid)
            if not qid:
                continue

            selected_answer = ""
            selected_source = "unresolved_items"
            for source in normalized_priority:
                candidate = ""
                if source == "interview_answers":
                    candidate = self._safe_contract_value(interview_answers.get(qid, ""))
                elif source == "user_prompt":
                    candidate = self._zero_base_extract_prompt_answer(
                        question_id=qid,
                        question_text=qtext,
                        user_prompt=user_prompt,
                        article_type=article_type,
                    )
                elif source == "unresolved_items":
                    candidate = ""
                candidate = self._sanitize_contract_text(candidate, max_length=180)
                if qrole == "target":
                    candidate = self._normalize_audience_profile_value(candidate, max_length=80)
                elif qrole == "perspective":
                    candidate = self._normalize_topic_statement_value(candidate, max_length=180)
                else:
                    candidate = self._sanitize_outline_seed(candidate, max_length=180)
                if candidate:
                    selected_answer = candidate
                    selected_source = source
                    break

            if selected_answer:
                selected_answer = self._normalize_must_cover_item(selected_answer, max_length=180)
                if announcement_like:
                    selected_answer = self._normalize_announcement_fact_item(selected_answer)
                    if qrole == "target":
                        resolved_audience = selected_answer or resolved_audience
                        if selected_answer:
                            resolved_answers[qid] = selected_answer
                        resolved_question_sources[qid] = selected_source
                        continue
                    if not selected_answer:
                        resolved_question_sources[qid] = selected_source
                        continue
                resolved_answers[qid] = selected_answer
                resolved_question_sources[qid] = selected_source
                if qrole == "target":
                    resolved_audience = selected_answer or resolved_audience
                elif qrole == "perspective":
                    continue
                else:
                    if self._is_low_signal_must_cover_item(selected_answer):
                        continue
                    if selected_answer == resolved_audience:
                        continue
                    if selected_answer not in must_cover:
                        must_cover.append(selected_answer)
                    if announcement_like:
                        if qrole == "message":
                            reader_q = "何が変わるか"
                        elif qrole == "evidence":
                            reader_q = "いつから・どこで確認できるか"
                        elif any(token in qid for token in ("impact", "effect", "influence")):
                            reader_q = "利用者への影響は何か"
                        elif any(token in qid for token in ("action", "check", "confirm")):
                            reader_q = "何を確認すべきか"
                        else:
                            reader_q = "確認すべき事実は何か"
                    else:
                        reader_q = self._zero_base_to_reader_question(
                            question_id=qid,
                            answer=selected_answer,
                        )
                    if reader_q and reader_q not in reader_question_candidates:
                        reader_question_candidates.append(reader_q)
            else:
                unresolved_label = (
                    self._sanitize_contract_text(f"{qid}: {qtext}", max_length=180)
                    if qtext
                    else self._sanitize_contract_text(qid, max_length=180)
                )
                if unresolved_label not in unresolved_items:
                    unresolved_items.append(unresolved_label)
                resolved_question_sources[qid] = "unresolved_items"

        must_cover = [
            item
            for item in must_cover
            if item
            and item != resolved_audience
            and not self._is_low_signal_must_cover_item(item)
        ]
        if announcement_like:
            for fact_item in self._extract_announcement_source_fact_items(contexts, limit=3):
                if fact_item and fact_item not in must_cover:
                    must_cover.append(fact_item)
        if not must_cover:
            fallback_map = {
                "branding": "自社の価値を読者の生活文脈に結びつける視点",
                "corporate_culture": "現場の取り組みを具体例で伝える視点",
                "ai": "導入判断に使える要点を整理する",
            }
            if announcement_like:
                must_cover.extend(["変更点", "対象者と開始時期", "確認事項"])
                reader_question_candidates.extend(["何が変わるか", "いつから・誰が対象か", "何を確認すべきか"])
            else:
                fallback = fallback_map.get(str(article_type or "").lower(), "読者が判断に使える具体的な要点")
                must_cover.append(fallback)
                reader_question_candidates.append(f"{fallback}を読者はどう活用できるか？")

        return {
            "pre_generation_questions": normalized_questions,
            "pre_generation_answers": resolved_answers,
            "must_cover": must_cover,
            "unresolved_items": unresolved_items,
            "question_source_priority": normalized_priority,
            "reader_question_candidates": reader_question_candidates,
            "resolved_question_sources": resolved_question_sources,
            "resolved_audience": resolved_audience,
            "need_question_decision": need_question_decision,
        }
