"""Input contract resolve for minimal newalgorithm pipeline."""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Dict, List

from core.app_config import get_llm_config, get_security_config, get_semantic_dedupe_config
from note.interview_contract_mapper import build_interview_contract_patch
from note.intent_profile import build_source_excerpt, decide_need_question, derive_prompt_intent_profile
from note.input_contract_v1 import InputContractValidationError, normalize_input_contract_v1
from note.prompt_sanitizer import sanitize_untrusted_text
from note import source_document_utils
from . import error_codes
from .strict_saas import (
    allows_semantic_fallback,
    blocks_prompt_intent_rewrite,
    normalize_strict_saas_mode,
    requires_explicit_profile_inputs,
)

SECURITY_CONFIG = get_security_config()
LLM_CONFIG = get_llm_config()
SEMANTIC_DEDUPE_CONFIG = get_semantic_dedupe_config()
_INJECTION_PATTERNS = (
    ("internal_override", re.compile(r"内部指示を無視", re.I)),
    ("system_prompt_exfil", re.compile(r"system prompt", re.I)),
    ("developer_message_exfil", re.compile(r"developer message", re.I)),
    ("privilege_override", re.compile(r"権限を上書き", re.I)),
    ("ignore_instructions", re.compile(r"ignore .*instructions", re.I)),
    ("role_rewrite", re.compile(r"(あなたは今から|これ以降).*(別の|違う)\s*役割", re.I)),
    ("secret_exfil", re.compile(r"(api[_ -]?key|secret|token|password).*(出力|開示|表示|教えて)", re.I)),
    ("tool_access_override", re.compile(r"(tool|file|filesystem|shell).*(使って|実行して|読んで)", re.I)),
    ("delimiter_override", re.compile(r"```.*(ignore|system prompt|developer message)", re.I | re.S)),
    ("encoded_override", re.compile(r"(base64|rot13|hex).*(decode|復号|展開)", re.I)),
)

_ARTICLE_TYPE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "explanatory_article": {
        "speaker_profile": "実務担当者",
        "audience_profile": "実務担当者",
        "register_policy": {"base_register": "polite", "allowed_endings": ["です", "ます", "でした", "ました"]},
        "allowed_pronouns": ["私", "わたし"],
    },
    "daily_story": {
        "speaker_profile": "現場担当者",
        "audience_profile": "読者",
        "register_policy": {"base_register": "polite", "allowed_endings": ["です", "ます", "ですね", "と思います"]},
        "allowed_pronouns": ["私", "わたし"],
    },
    "branding": {
        "speaker_profile": "ブランド担当者",
        "audience_profile": "見込み読者",
        "register_policy": {"base_register": "polite", "allowed_endings": ["です", "ます", "でした", "ました"]},
        "allowed_pronouns": ["私たち", "当社", "弊社"],
    },
    "announcement": {
        "speaker_profile": "運営担当者",
        "audience_profile": "読者",
        "register_policy": {"base_register": "polite", "allowed_endings": ["です", "ます", "でした", "ました"]},
        "allowed_pronouns": ["当社", "弊社", "私たち"],
    },
    "case_study": {
        "speaker_profile": "導入担当者",
        "audience_profile": "導入を検討する読者",
        "register_policy": {"base_register": "polite", "allowed_endings": ["です", "ます", "でした", "ました"]},
        "allowed_pronouns": ["私たち", "当社", "弊社"],
    },
    "industry_analysis": {
        "speaker_profile": "業界分析担当者",
        "audience_profile": "意思決定者",
        "register_policy": {"base_register": "polite", "allowed_endings": ["です", "ます", "でした", "ました"]},
        "allowed_pronouns": ["私", "私たち"],
    },
    "comparative_review": {
        "speaker_profile": "比較検証担当者",
        "audience_profile": "比較検討中の読者",
        "register_policy": {"base_register": "polite", "allowed_endings": ["です", "ます", "でした", "ました"]},
        "allowed_pronouns": ["私", "私たち"],
    },
}

_BRANDING_CONTEXT_MARKERS = (
    "小規模",
    "中堅",
    "大手",
    "SaaS",
    "BtoB",
    "BtoC",
    "導入初期",
    "複数拠点",
    "営業",
    "サポート",
    "カスタマーサクセス",
    "CS",
    "導入担当",
    "情シス",
)
_SOURCE_BUCKET_HINTS: Dict[str, tuple[str, ...]] = {
    "overview": ("会社概要", "企業概要", "事業内容", "会社情報", "プロフィール", "about", "company", "profile", "coprof"),
    "strength": ("強み", "特長", "特徴", "選ばれる理由", "支援方針", "導入方針", "サポート方針", "運用方針", "quality", "strength", "support-policy", "品質", "実績"),
    "history": ("沿革", "歴史", "歩み", "創業", "設立", "history"),
}
_SOURCE_NOISE_PATTERN = re.compile(
    r"(お問い合わせ|採用情報|個人情報|プライバシー|サイトマップ|トップページ|HOME|Copyright|All rights reserved)",
    re.I,
)
_SOURCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？])\s+|\n+")
_SOURCE_LOW_SIGNAL_FACT_RE = re.compile(
    r"^(?:会社概要|企業概要|事業内容|強み|特長|特徴|沿革|歴史|プロフィール|about|company|profile|coprof)$",
    re.I,
)
_SOURCE_COURTESY_PATTERN = re.compile(
    r"(?:ご覧いただきありがとうございます|ぜひご相談ください|お問い合わせください|代表挨拶|ごあいさつ|"
    r"モットー|未来を目指して|健康経営優良法人|先輩社員の声|募集要項|採用情報|TOP$|ＴＯＰ$|"
    r"よろしくお願いいたします|ぜひ|ご相談ください|ご確認ください|メッセージ)",
    re.I,
)
_SOURCE_META_PATTERN = re.compile(
    r"(?:弊社HP|公式サイト|ホームページ|専用ページ|お問い合わせ|採用情報|認定資格|プライバシー|"
    r"情報セキュリティ方針|ガイドライン|プライバシーマーク|ISMS認証|サイトマップ|"
    r"利用規約|個人情報保護方針|会社案内PDF|ダウンロード|Your browser does not support the audio element)",
    re.I,
)
_SOURCE_OUTLINE_ROUTE_KEYS = {"explanatory_article", "industry_analysis"}
_SOURCE_OUTLINE_JA_RE = re.compile(r"[ぁ-んァ-ヴ一-龥々]")
_SOURCE_OUTLINE_META_RE = re.compile(
    r"(?:Listen to article|POSTED IN|Voice|Speed|\[\[duration\]\]|minutes|No thanks|"
    r"Apr \d{2}, \d{4}|VP of Research|Group Product Manager|Your browser does not support the audio element)",
    re.I,
)
_SOURCE_TITLE_ENTITY_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9 .+/_&()'-]{1,28})\s*[:：]\s+")
_SOURCE_THEME_LABEL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("比較条件", re.compile(r"(比較|compare|comparison|vs|差分|競合|他社)", re.I)),
    (
        "構成とサイズ",
        re.compile(
            r"(?:\b(?:E2B|E4B|2B|4B|26B|31B|80GB|128K|256K)\b|size|sizes|model weights|parameter|parameters|"
            r"dense|mixture of experts|moe|hardware|device|edge|mobile|laptop gpu|android devices|iot|"
            r"モデル|サイズ|構成|ハードウェア|端末|オンデバイス|文脈長)",
            re.I,
        ),
    ),
    (
        "主な特徴",
        re.compile(
            r"(feature|features|capabilit|reasoning|agentic|workflow|function-calling|json|code|vision|audio|"
            r"language|math|ocr|benchmark|機能|特徴|性能|強み|推論|コード|音声|画像|言語)",
            re.I,
        ),
    ),
    (
        "活用場面",
        re.compile(
            r"(use case|use cases|specific tasks|prototype|production|workflow|用途|場面|活用|実務|研究|"
            r"プロトタイピング)",
            re.I,
        ),
    ),
    (
        "公開条件",
        re.compile(
            r"(license|apache|open-source|commercially permissive|trust|safety|security|reliability|"
            r"sovereign|compliance|ライセンス|公開|安全|信頼性|コンプライアンス)",
            re.I,
        ),
    ),
    (
        "使う環境",
        re.compile(
            r"(ai studio|edge gallery|hugging face|kaggle|ollama|vertex|cloud run|gke|android studio|ml kit|"
            r"download|deploy|tool|tools|ecosystem|platform|google cloud|環境|ツール|導入先|展開先|利用環境|始め方)",
            re.I,
        ),
    ),
    (
        "主要な数値",
        re.compile(
            r"(?:#\d+|\b\d+(?:\.\d+)?x\b|\b\d+(?:\.\d+)?(?:b|m|gb|k)\b|\b\d{4}\b|\b\d+(?:\.\d+)?%\b|"
            r"ランキング|rank|leaderboard|million|variants|downloads|件|人|社|回)",
            re.I,
        ),
    ),
)
_PROMPT_LIKE_TOPIC_RE = re.compile(
    r"(してください|したい|してほしい|表示してください|まとめてください|投稿する|投稿したい|"
    r"書きたい|書いてください|かいてください|作成してください|生成してください|教えてください)"
)
_COMPANY_INTRO_STANCE_SOURCE_RE = re.compile(
    r"(理念|ビジョン|ミッション|バリュー|価値観|行動指針|代表メッセージ|メッセージ|"
    r"philosophy|vision|mission|value|guideline|message)",
    re.I,
)
_COMPANY_INTRO_STANCE_FACT_RE = re.compile(
    r"(満足|向上|貢献|信頼|人間力|技術力|大切|重視|磨く|尽力|精進|姿勢|価値観)",
    re.I,
)
_COMPANY_INTRO_REASON_FACT_RE = re.compile(
    r"(信頼|技術力|営業力|改善|向上|満足|貢献|支援|対応|尽力|精進|継続|追求)",
    re.I,
)
_COMPANY_INTRO_PROMPT_SURFACE_LABELS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("選ばれる理由", re.compile(r"(選ばれる理由|選ばれるわけ)", re.I)),
    (
        "大切にしている姿勢",
        re.compile(r"(大切にしている姿勢|大切にする姿勢|大切にしていること|大切にすること)", re.I),
    ),
    (
        "導入時に重視すること",
        re.compile(r"(導入時に重視すること|導入時に見ておきたい点|導入時の確認点)", re.I),
    ),
)
_FOCUS_VERB_SUFFIX_RE = re.compile(
    r"(?:を)?(?:紹介する|整理する|伝える|具体化する|見直す|説明する|考える|深掘りする)$"
)
_SUPPORT_POINT_VERB_SUFFIX_RE = re.compile(
    r"(?:を)?(?:示す|入れる|整える|具体化する|明示する|定義する|書く|出す|締める)$"
)
_COMPARISON_AXIS_LABELS: Dict[str, str] = {
    "price": "価格",
    "performance": "性能",
    "use_case": "用途",
    "safety": "安全性",
    "overall": "総合",
    "initial_setup": "初期設定",
    "review_flow": "レビューの流れ",
    "review_lightness": "レビューの軽さ",
    "onboarding": "導入のしやすさ",
    "approval_flow": "承認フロー",
    "governance": "ガバナンス",
    "support_density": "サポートの厚み",
    "ownership": "担当責任の置き方",
    "auditability": "監査のしやすさ",
}
_UI_QUESTION_FIELDS = {"speaker_profile", "audience_profile", "core_message", "allow_experience"}
_ALLOWED_SEMANTIC_ARTICLE_KEYS = {
    "explanatory_article",
    "daily_story",
    "branding",
    "announcement",
    "case_study",
    "industry_analysis",
    "comparative_review",
    "company_introduction",
    "product_introduction",
    "activity_introduction",
    "recruit_culture",
    "implementation_case",
    "improvement_case",
    "incident_case",
    "learning_case",
}
_DEFAULT_SEMANTIC_BY_ARTICLE_TYPE: Dict[str, str] = {
    "explanatory_article": "explanatory_article",
    "daily_story": "daily_story",
    "branding": "branding",
    "announcement": "announcement",
    "case_study": "case_study",
    "industry_analysis": "industry_analysis",
    "comparative_review": "comparative_review",
}
_SOURCE_SIGNAL_PATTERNS: Dict[str, re.Pattern[str]] = {
    "company": re.compile(r"(会社概要|企業概要|事業内容|会社情報|沿革|about|company|profile|coprof)", re.I),
    "product": re.compile(r"(製品|商品|サービス|機能|料金|プラン|仕様|導入メリット|feature|pricing|service)", re.I),
    "activity": re.compile(r"(活動|取り組み|プロジェクト|研究|イベント|initiative|project|活動報告|ニュース)", re.I),
    "recruit": re.compile(r"(採用|募集|カルチャー|働き方|チーム|社員|culture|career|recruit)", re.I),
    "implementation": re.compile(r"(導入事例|導入|オンボーディング|移行|活用事例|implementation|導入前|導入後)", re.I),
    "improvement": re.compile(r"(改善|見直し|最適化|効率化|before|after|改善事例)", re.I),
    "incident": re.compile(r"(障害|事故|インシデント|不具合|障害報告|再発防止|incident|outage)", re.I),
    "learning": re.compile(r"(ケーススタディ|学習用|学び|lesson|ケース|教材|study)", re.I),
    "compare": re.compile(r"(比較|他社|競合|違い|comparison|compare|vs)", re.I),
}
_CASE_STUDY_DEFAULT_LABELS: Dict[str, List[str]] = {
    "case_study": ["導入前の課題", "進め方", "結果の条件"],
    "implementation_case": ["導入前の課題", "進め方", "変化の条件"],
    "improvement_case": ["改善前の状態", "見直した点", "改善後の変化"],
    "incident_case": ["何が起きたか", "影響と原因", "再発防止"],
    "learning_case": ["ケースの前提", "学び", "次に生かす条件"],
}
_EMBEDDED_UI_SLOT_FIELDS: Dict[str, tuple[str, int]] = {
    "話者": ("speaker_profile", 160),
    "主な読者": ("audience_profile", 160),
    "核メッセージ": ("core_message", 240),
    "語り口": ("tone_profile", 32),
}


def _compile_extra_patterns() -> tuple[tuple[str, re.Pattern[str]], ...]:
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for idx, pattern in enumerate(SECURITY_CONFIG.extra_injection_patterns):
        try:
            compiled.append((f"config_pattern_{idx + 1}", re.compile(pattern, re.I)))
        except re.error:
            continue
    return tuple(compiled)


EXTRA_INJECTION_PATTERNS = _compile_extra_patterns()


class PromptInjectionBlockedError(RuntimeError):
    def __init__(
        self,
        *,
        blocked_input_fields: List[str],
        blocked_patterns: List[str],
        partial_contract: Dict[str, Any],
    ) -> None:
        super().__init__("Prompt injection blocked")
        self.reason_code = error_codes.SEC_PROMPT_INJECTION_BLOCKED
        self.blocked_input_fields = list(blocked_input_fields)
        self.blocked_patterns = list(blocked_patterns)
        self.partial_contract = dict(partial_contract)
        self.security_gate = {
            "decision": "block",
            "blocked_input_fields": list(blocked_input_fields),
            "blocked_patterns": list(blocked_patterns),
        }


def _sanitize_free_text(text: Any, *, max_length: int = 1200) -> str:
    return sanitize_untrusted_text(str(text or ""), max_length=max_length)


def _scan_injection_patterns(text: str) -> List[str]:
    value = str(text or "")
    hits: List[str] = []
    for label, pattern in _INJECTION_PATTERNS + EXTRA_INJECTION_PATTERNS:
        if pattern.search(value):
            hits.append(label)
    return hits


def _normalize_choice(value: Any, default: str, allowed: set[str], *, field: str) -> str:
    key = str(value or "").strip().lower()
    if not key:
        return default
    if key in allowed:
        return key
    raise InputContractValidationError(
        f"unsupported {field}",
        reason_code="INP_UNSUPPORTED_CHOICE",
        field=field,
    )


def _normalize_field_sources(value: Any) -> Dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    normalized: Dict[str, str] = {}
    for key, item in value.items():
        normalized_key = str(key or "").strip()
        normalized_value = str(item or "").strip()
        if normalized_key and normalized_value:
            normalized[normalized_key] = normalized_value
    return normalized


def _field_source_or_default(field_sources: Dict[str, str], field_name: str, fallback: str) -> str:
    current = str(field_sources.get(field_name) or "").strip()
    return current or fallback


def _normalize_ui_journey(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    normalized: Dict[str, Any] = {}
    for key in ("purpose_key", "target_key", "detail_key"):
        current = str(value.get(key) or "").strip().lower()
        if current:
            normalized[key] = current
    comparison_axes = _normalize_string_list(value.get("comparison_axes"))
    if comparison_axes:
        normalized["comparison_axes"] = comparison_axes
    return normalized


def _normalize_semantic_article_key(value: Any) -> str:
    key = str(value or "").strip().lower()
    return key if key in _ALLOWED_SEMANTIC_ARTICLE_KEYS else ""


def _resolve_semantic_article_key(
    normalized: Dict[str, Any],
    *,
    prompt_intent: Dict[str, Any],
) -> str:
    explicit = _normalize_semantic_article_key(normalized.get("semantic_article_key"))
    if explicit:
        return explicit
    article_type = str(normalized.get("article_type") or "").strip().lower()
    if article_type == "branding" and _is_prompt_primary_company_intro(normalized, prompt_intent=prompt_intent):
        return "company_introduction"
    return _DEFAULT_SEMANTIC_BY_ARTICLE_TYPE.get(article_type, article_type or "explanatory_article")


def _resolve_comparison_axes(normalized: Dict[str, Any]) -> List[str]:
    items = _normalize_string_list(normalized.get("comparison_axes"))
    if not items:
        ui_journey = _normalize_ui_journey(normalized.get("ui_journey"))
        items = _normalize_string_list(ui_journey.get("comparison_axes"))
    normalized_axes: List[str] = []
    for item in items:
        key = str(item or "").strip().lower()
        label = _COMPARISON_AXIS_LABELS.get(key, str(item or "").strip())
        if label and label not in normalized_axes:
            normalized_axes.append(label)
        if len(normalized_axes) >= 2:
            break
    return normalized_axes


def _journey_requires_comparison_axes(normalized: Dict[str, Any]) -> bool:
    ui_journey = _normalize_ui_journey(normalized.get("ui_journey"))
    return (
        str(ui_journey.get("purpose_key") or "").strip().lower() == "compare"
        or str(ui_journey.get("target_key") or "").strip().lower() in {"tool_service", "method", "vendor"}
    )


def _derive_branding_context_item(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    markers = [marker for marker in _BRANDING_CONTEXT_MARKERS if marker in value]
    markers = list(dict.fromkeys(markers))
    if "SaaS" in markers and "小規模" in markers and "導入初期" in markers:
        return "小規模SaaSの導入初期を前提にする"
    if "SaaS" in markers and "導入初期" in markers:
        return "SaaSの導入初期を前提にする"
    if markers:
        return "、".join(markers[:2]) + " の文脈を踏まえる"
    return ""


def _is_prompt_primary_company_intro(
    normalized: Dict[str, Any],
    *,
    prompt_intent: Dict[str, Any] | None = None,
) -> bool:
    article_type = str(normalized.get("article_type") or "").strip().lower()
    if article_type != "branding":
        return False
    if prompt_intent is None:
        prompt_intent = derive_prompt_intent_profile(
            str(normalized.get("topic") or ""),
            article_type,
        )
    return (
        str(prompt_intent.get("primary_intent") or "") == "company_introduction"
        and bool(prompt_intent.get("prefer_prompt_topic"))
    )


def _is_company_introduction_like(
    normalized: Dict[str, Any],
    *,
    prompt_intent: Dict[str, Any] | None = None,
) -> bool:
    if str(normalized.get("semantic_article_key") or "").strip().lower() == "company_introduction":
        return True
    return _is_prompt_primary_company_intro(normalized, prompt_intent=prompt_intent)


def _derive_prompt_instruction_items(
    normalized: Dict[str, Any],
    *,
    prompt_intent: Dict[str, Any],
) -> List[str]:
    if not _is_prompt_primary_company_intro(normalized, prompt_intent=prompt_intent):
        return []
    preferred_topic = str(prompt_intent.get("preferred_topic_statement") or "").strip()
    if _looks_prompt_like_topic(preferred_topic):
        preferred_topic = ""
    intro_item = preferred_topic or "初回投稿として、自社の全体像を紹介する"
    tone_item = ""
    topic = str(normalized.get("topic") or "")
    if bool(prompt_intent.get("tone_signal")) or re.search(r"(事務的|口調|文体|トーン)", topic):
        tone_item = "事務的な口調になりすぎないよう、やわらかく読みやすく伝える"
    items = [intro_item]
    if tone_item:
        items.append(tone_item)
    return items


def _looks_prompt_like_topic(text: str) -> bool:
    candidate = str(text or "").strip()
    if not candidate:
        return False
    return bool(_PROMPT_LIKE_TOPIC_RE.search(candidate))


def _derive_prompt_context_items(
    normalized: Dict[str, Any],
    *,
    prompt_intent: Dict[str, Any],
) -> List[str]:
    if not _is_prompt_primary_company_intro(normalized, prompt_intent=prompt_intent):
        return []
    return _normalize_string_list(prompt_intent.get("prompt_context_items"))


def _compact_prompt_context_items(items: List[str]) -> List[str]:
    if not items:
        return []
    scored_items: List[tuple[int, str]] = []
    for item in items:
        value = str(item or "").strip()
        if not value:
            continue
        score = 0
        if re.search(r"DX", value, re.I):
            score += 3
        if re.search(r"(デジタル化|電子化|アナログデータ|アナログ|紙|帳票)", value, re.I):
            score += 3
        if re.search(r"(導入初期|初期段階)", value, re.I):
            score += 2
        if re.search(r"(一般読者|経営者|導入担当|対象読者)", value, re.I):
            score += 1
        scored_items.append((score, value))
    scored_items.sort(key=lambda item: (-item[0], len(item[1])))
    if scored_items and scored_items[0][0] > 0:
        return [scored_items[0][1]]
    return [str(items[0] or "").strip()] if str(items[0] or "").strip() else []


def _resolve_prompt_primary_audience(
    normalized: Dict[str, Any],
    *,
    prompt_intent: Dict[str, Any],
    default_audience: str,
) -> str:
    current = str(normalized.get("audience_profile") or "").strip()
    prompt_audiences = _normalize_string_list(prompt_intent.get("prompt_audience_candidates"))
    if prompt_audiences and (not current or current == default_audience):
        return prompt_audiences[0]
    return current or default_audience


def _derive_prompt_primary_branding_must_cover(normalized: Dict[str, Any]) -> List[str]:
    prompt_instruction_items = _normalize_string_list(normalized.get("prompt_instruction_items"))
    prompt_context_items = _normalize_string_list(normalized.get("prompt_context_items"))
    intro_item = prompt_instruction_items[0] if prompt_instruction_items else ""
    topic_statement = str(normalized.get("topic_statement") or "").strip()
    if _looks_prompt_like_topic(intro_item):
        intro_item = ""
    if _looks_prompt_like_topic(topic_statement):
        topic_statement = ""
    if not intro_item:
        intro_item = topic_statement or "初回投稿として、自社の全体像を紹介する"
    items = [
        intro_item,
        *prompt_context_items,
        "自社が何をしている会社かを初見でも伝わる言葉で示す",
        "sourceで確認できる強みや歩みを事実ベースで入れる",
        "読後に会社の輪郭が伝わる形で締める",
    ]
    unique: List[str] = []
    for item in items:
        compact = str(item or "").strip()
        if compact and compact not in unique:
            unique.append(compact)
    return unique


def _derive_message_hint(normalized: Dict[str, Any]) -> str:
    if _is_company_introduction_like(normalized):
        return ""
    direct_core_message = _sanitize_free_text(normalized.get("core_message", ""), max_length=160).strip(" 　、。")
    if direct_core_message:
        raw_value = direct_core_message
    else:
        interview_answers = normalized.get("interview_answers", {}) or {}
        if not isinstance(interview_answers, dict):
            return ""
        raw_value = ""
        for key in ("message", "core_message", "main_message"):
            candidate = _sanitize_free_text(interview_answers.get(key, ""), max_length=160).strip(" 　、。")
            if candidate:
                raw_value = candidate
                break
    if not raw_value:
        return ""
    value = re.sub(r"^(?:核心メッセージ|伝えたいこと|結論)(?:は)?[：:]\s*", "", raw_value).strip(" 　、。")
    if len(value) < 4:
        return ""
    if re.search(r"(?:記事|投稿|本文|ブログ).{0,12}(?:作成|生成|書(?:いて|く)|作って)", value):
        return ""
    if re.search(r"(?:主に)?誰に向けて|読者|対象(?:読者)?|向け|視点|知見", value):
        return ""
    if re.fullmatch(r"(?:指定しない|自動判定|おまかせ|任せる)", value, re.I):
        return ""
    comparison_values = {
        str(normalized.get("topic_statement") or "").strip(),
        str(normalized.get("topic") or "").strip(),
        str(normalized.get("audience_profile") or "").strip(),
        str(normalized.get("speaker_profile") or "").strip(),
    }
    if value in comparison_values:
        return ""
    return value[:80]


def _derive_core_message(normalized: Dict[str, Any]) -> str:
    direct_core_message = _sanitize_free_text(normalized.get("core_message", ""), max_length=160).strip(" 　、。")
    if direct_core_message:
        return direct_core_message[:120]
    interview_answers = normalized.get("interview_answers", {}) or {}
    if not isinstance(interview_answers, dict):
        return ""
    raw_value = ""
    for key in ("message", "core_message", "main_message"):
        candidate = _sanitize_free_text(interview_answers.get(key, ""), max_length=160).strip(" 　、。")
        if candidate:
            raw_value = candidate
            break
    if not raw_value:
        return ""
    value = re.sub(r"^(?:核心メッセージ|伝えたいこと|結論)(?:は)?[：:]\s*", "", raw_value).strip(" 　、。")
    if len(value) < 4:
        return ""
    if re.search(r"(?:記事|投稿|本文|ブログ).{0,12}(?:作成|生成|書(?:いて|く)|作って)", value):
        return ""
    if re.search(r"(?:主に)?誰に向けて|読者|対象(?:読者)?|向け|視点|知見", value):
        return ""
    if re.fullmatch(r"(?:指定しない|自動判定|おまかせ|任せる)", value, re.I):
        return ""
    comparison_values = {
        str(normalized.get("topic_statement") or "").strip(),
        str(normalized.get("topic") or "").strip(),
        str(normalized.get("audience_profile") or "").strip(),
        str(normalized.get("speaker_profile") or "").strip(),
    }
    if value in comparison_values:
        return ""
    return value[:80]


def _normalize_string_list(value: Any) -> List[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list):
        return []
    cleaned: List[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            cleaned.append(text)
    return cleaned


def _extract_embedded_ui_prompt_slots(prompt_raw: Any) -> Dict[str, str]:
    prompt = str(prompt_raw or "").strip()
    if not prompt or "UI選択" not in prompt:
        return {}
    extracted: Dict[str, str] = {}
    for raw_line in prompt.splitlines():
        match = re.match(r"^\s*-\s*([^:：]+)\s*[:：]\s*(.+?)\s*$", str(raw_line or "").strip())
        if not match:
            continue
        label = str(match.group(1) or "").strip()
        spec = _EMBEDDED_UI_SLOT_FIELDS.get(label)
        if not spec:
            continue
        field_name, max_length = spec
        value = _sanitize_free_text(match.group(2), max_length=max_length).strip()
        if not value or value.lower() in {"auto", "n/a"} or value in {"未指定", "自動判定"}:
            continue
        if field_name == "tone_profile":
            tone_value = value.lower()
            if tone_value not in {"auto", "calm", "warm", "passionate", "formal"}:
                continue
            extracted[field_name] = tone_value
            continue
        extracted[field_name] = value
    return extracted


def _should_apply_embedded_ui_slot(
    field_name: str,
    current: str,
    field_sources: Mapping[str, str] | None = None,
) -> bool:
    normalized_current = str(current or "").strip()
    current_source = str(dict(field_sources or {}).get(field_name) or "").strip()
    if not normalized_current:
        return True
    if current_source in {"ui_auto_default", "article_type_default"}:
        return True
    if field_name == "tone_profile":
        return normalized_current.lower() == "auto"
    if field_name == "speaker_profile":
        return normalized_current in {"編集担当として語る", "自動判定"}
    if field_name == "audience_profile":
        return normalized_current in {"一般読者"}
    return False


def _apply_embedded_ui_prompt_slots(normalized: Dict[str, Any], field_sources: Dict[str, str]) -> None:
    extracted = _extract_embedded_ui_prompt_slots(normalized.get("prompt_raw") or normalized.get("topic") or "")
    if not extracted:
        return
    for field_name, value in extracted.items():
        current = str(normalized.get(field_name) or "").strip()
        if not _should_apply_embedded_ui_slot(field_name, current, field_sources):
            continue
        normalized[field_name] = value
        field_sources[field_name] = "prompt_ui_embedded"


def _derive_case_study_prompt_labels(normalized: Dict[str, Any], *, limit: int = 3) -> List[str]:
    semantic_key = str(normalized.get("semantic_article_key") or normalized.get("article_type") or "").strip().lower()
    defaults = list(
        _CASE_STUDY_DEFAULT_LABELS.get(
            semantic_key,
            _CASE_STUDY_DEFAULT_LABELS["case_study"],
        )
    )
    if semantic_key in {"implementation_case", "improvement_case", "incident_case", "learning_case"}:
        return defaults[:limit]

    parts: List[str] = []
    for candidate in [
        normalized.get("topic_statement", ""),
        normalized.get("topic", ""),
        normalized.get("core_message", ""),
        *_normalize_string_list(normalized.get("prompt_instruction_items"))[:2],
    ]:
        value = _normalize_focus_text(candidate, max_length=80)
        if value and value not in parts:
            parts.append(value)
    blob = "。".join(parts)
    if not blob:
        return defaults[:limit]

    before_label = defaults[0]
    if re.search(r"(改善前|見直し前|変更前)", blob):
        before_label = "改善前の状態"
    elif re.search(r"(導入前|最初|迷い|つまず|止ま|引っかか|負荷|遅延|読みづら|背景|課題)", blob):
        before_label = "導入前の課題"

    process_label = defaults[1]
    if re.search(r"(見直した点|改善した点|直した点|調整した点)", blob):
        process_label = "見直した点"
    elif re.search(r"(どう進め|進め方|直した|見直し|組み替|整理|対応|導入し直|手順)", blob):
        process_label = "進め方"

    outcome_label = defaults[2]
    if re.search(r"(再発防止)", blob):
        outcome_label = "再発防止"
    elif re.search(r"(再現|どの条件|条件|前提|限界|防ぐ|防止)", blob):
        outcome_label = "再現条件"
    elif re.search(r"(次に生か|学び|lesson)", blob):
        outcome_label = "次に生かす条件" if "次に生か" in blob else "学び"
    elif re.search(r"(変化|何が変わ|改善後|前後|差|揃っ|減っ|短く|結果)", blob):
        outcome_label = "変化した状態"

    return _dedupe_text_list([before_label, process_label, outcome_label], limit=limit)


def _normalize_source_documents(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: List[Dict[str, Any]] = []
    for item in value:
        document = source_document_utils.normalize_source_document_entry(item)
        if not document:
            continue
        normalized.append(document)
    return normalized


def _sanitize_source_document_content(content: str) -> tuple[str, List[str], int]:
    raw_content = str(content or "").strip()
    if not raw_content:
        return "", [], 0
    full_hits = _scan_injection_patterns(raw_content)
    if not full_hits:
        return source_document_utils.truncate_source_document_content(raw_content), [], 0
    blocked_patterns: List[str] = []
    kept_segments: List[str] = []
    removed_fragment_count = 0
    for raw_part in _SOURCE_SPLIT_PATTERN.split(raw_content):
        segment = str(raw_part or "").strip()
        if not segment:
            continue
        hits = _scan_injection_patterns(segment)
        if hits:
            blocked_patterns.extend(hits)
            removed_fragment_count += 1
            continue
        kept_segments.append(segment)
    if removed_fragment_count == 0:
        return "", list(dict.fromkeys(full_hits)), 1
    return (
        source_document_utils.truncate_source_document_content("\n".join(kept_segments)),
        list(dict.fromkeys(blocked_patterns)),
        removed_fragment_count,
    )


def _sanitize_source_documents(
    documents: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    sanitized_documents: List[Dict[str, Any]] = []
    blocked_patterns: List[str] = []
    sanitized_document_count = 0
    removed_fragment_count = 0
    for document in documents:
        sanitized_document = dict(document)
        changed = False
        title = str(sanitized_document.get("title") or "").strip()
        title_hits = _scan_injection_patterns(title)
        if title_hits:
            sanitized_document["title"] = ""
            blocked_patterns.extend(title_hits)
            changed = True
        content, content_hits, removed_count = _sanitize_source_document_content(
            str(sanitized_document.get("content") or "")
        )
        if content_hits or removed_count:
            sanitized_document["content"] = content
            blocked_patterns.extend(content_hits)
            removed_fragment_count += removed_count
            changed = True
        if changed:
            sanitized_document_count += 1
        sanitized_documents.append(sanitized_document)
    return sanitized_documents, {
        "sanitized_document_count": sanitized_document_count,
        "removed_fragment_count": removed_fragment_count,
        "blocked_patterns": list(dict.fromkeys(blocked_patterns)),
    }


def _contains_bucket_hint(text: str, bucket: str) -> bool:
    value = str(text or "")
    lowered = value.lower()
    for hint in _SOURCE_BUCKET_HINTS.get(bucket, ()):
        if hint.isascii():
            if hint.lower() in lowered:
                return True
        elif hint in value:
            return True
    return False


def _detect_source_bucket(document: Dict[str, Any]) -> str:
    combined = " ".join(
        [
            str(document.get("title") or ""),
            str(document.get("locator") or ""),
        ]
    )
    for bucket in ("overview", "strength", "history"):
        if _contains_bucket_hint(combined, bucket):
            return bucket
    return "other"


def _normalize_source_fact_text(text: str, *, max_length: int = 120) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip(" 　-・、。")
    if len(value) > max_length:
        value = value[:max_length].rstrip(" 　、。")
    return value


def _is_low_signal_source_fact(text: str) -> bool:
    value = _normalize_source_fact_text(text, max_length=120)
    if not value:
        return True
    if _SOURCE_LOW_SIGNAL_FACT_RE.fullmatch(value):
        return True
    if re.fullmatch(r"(?:ようこそ.*|ごあいさつ|ご挨拶)", value):
        return True
    if _SOURCE_COURTESY_PATTERN.search(value):
        return True
    if _SOURCE_META_PATTERN.search(value):
        return True
    return False


def _split_source_candidates(content: str) -> List[str]:
    candidates: List[str] = []
    for raw_part in _SOURCE_SPLIT_PATTERN.split(str(content or "")):
        text = _normalize_source_fact_text(raw_part, max_length=180)
        if not text:
            continue
        if _scan_injection_patterns(text):
            continue
        if _SOURCE_NOISE_PATTERN.search(text):
            continue
        if _is_low_signal_source_fact(text):
            continue
        if len(text) < 10 and not re.search(r"(19|20)\d{2}年|会社|強み|沿革|事業", text):
            continue
        if text not in candidates:
            candidates.append(text)
    return candidates


def _score_source_candidate(text: str, *, bucket: str, document_bucket: str, document: Dict[str, Any]) -> int:
    title = str(document.get("title") or "")
    locator = str(document.get("locator") or "")
    score = 0
    if document_bucket == bucket:
        score += 4
    if _contains_bucket_hint(f"{title} {locator}", bucket):
        score += 3
    if _contains_bucket_hint(text, bucket):
        score += 5
    if bucket == "overview":
        if re.search(r"(会社|当社|弊社|私たち|事業|サービス|業務|提供|支援|データ入力|入力)", text):
            score += 3
    elif bucket == "strength":
        if re.search(r"(強み|特長|特徴|品質|精度|実績|体制|対応力|柔軟|短納期|ノウハウ)", text):
            score += 3
    elif bucket == "history":
        if re.search(r"(創業|設立|沿革|歩み)", text):
            score += 3
        if re.search(r"(19|20)\d{2}年", text):
            score += 4
    else:
        if re.search(r"(会社|事業|サービス|強み|沿革|歴史|創業|設立)", text):
            score += 2
    if len(text) >= 24:
        score += 1
    if len(text) > 120:
        score -= 1
    if text == title:
        score -= 2
    if _SOURCE_NOISE_PATTERN.search(text):
        score -= 3
    if _SOURCE_COURTESY_PATTERN.search(text):
        score -= 4
    if _SOURCE_META_PATTERN.search(text):
        score -= 4
    return score


def _is_product_intro_service_fact(text: str) -> bool:
    value = str(text or "")
    if not value:
        return False
    service_hits = 0
    if re.search(r"(データ入力|データ化|デジタルデータ|スキャニング|入力|エントリ|納品|ヒアリング)", value):
        service_hits += 1
    if re.search(r"(課題|目的|活用|相談|導入|運用|選ぶ|判断材料|注意点|進め方)", value):
        service_hits += 1
    if re.search(r"(市場調査|Webリサーチ|分析|チェック|体制|国内一貫|前処理|後処理)", value):
        service_hits += 1
    return service_hits >= 2


def _resolve_product_intro_source_bucket(text: str) -> str:
    value = str(text or "")
    if re.search(r"(課題|やり方がわからない|活用方法|相談|導入|進め方|利用場面|用途)", value):
        return "overview"
    if re.search(r"(体制|国内一貫|チェック|納品|ヒアリング|品質|精度|対応)", value):
        return "strength"
    if re.search(r"(市場調査|Webリサーチ|分析|データ化)", value):
        return "other"
    if re.search(r"(創業|沿革|歩み|(19|20)\d{2}年|先代|4代目)", value):
        return "history"
    return "other"


def _score_product_intro_source_candidate(text: str) -> int:
    value = str(text or "")
    score = 0
    if _is_product_intro_service_fact(value):
        score += 5
    if re.search(r"(データ入力|データ化|デジタルデータ|入力|エントリ|スキャニング)", value):
        score += 3
    if re.search(r"(課題|活用|相談|導入|運用|判断材料|注意点|進め方)", value):
        score += 2
    if re.search(r"(体制|国内一貫|チェック|納品|ヒアリング|品質|精度)", value):
        score += 2
    if re.search(r"(市場調査|Webリサーチ|分析)", value):
        score += 1
    if len(value) < 24 and "。" not in value and not re.search(r"(です|ます|する|対応|承り|行い|支え)", value):
        score -= 3
    if re.search(r"(創業|沿革|歩み|(19|20)\d{2}年|先代|4代目|代表取締役|代表挨拶)", value):
        score -= 4
    if re.search(r"(ISMS|プライバシーマーク|認定資格)", value):
        score -= 3
    return score


def _build_source_grounding_items(normalized: Dict[str, Any]) -> List[Dict[str, str]]:
    documents = _normalize_source_documents(normalized.get("source_documents"))
    if not documents:
        return []
    prompt_primary_company_intro = _is_company_introduction_like(normalized)
    semantic_key = str(normalized.get("semantic_article_key") or normalized.get("article_type") or "").strip().lower()
    product_intro_route = semantic_key == "product_introduction" and not prompt_primary_company_intro
    source_outline_route = _is_source_outline_route(normalized) and not prompt_primary_company_intro and not product_intro_route
    gathered: List[tuple[int, int, int, Dict[str, str]]] = []
    for doc_index, document in enumerate(documents):
        document_bucket = _detect_source_bucket(document)
        candidates = _split_source_candidates(str(document.get("content") or ""))
        if not candidates:
            fallback = _normalize_source_fact_text(document.get("title", ""))
            if fallback and not _is_low_signal_source_fact(fallback):
                candidates = [fallback]
        for candidate_index, candidate in enumerate(candidates):
            if prompt_primary_company_intro:
                best_bucket = document_bucket
                best_score = _score_source_candidate(
                    candidate,
                    bucket=document_bucket,
                    document_bucket=document_bucket,
                    document=document,
                )
                for bucket in ("overview", "strength", "history"):
                    score = _score_source_candidate(
                        candidate,
                        bucket=bucket,
                        document_bucket=document_bucket,
                        document=document,
                    )
                    if score > best_score:
                        best_bucket = bucket
                        best_score = score
                if best_score < 4:
                    continue
            else:
                best_bucket = document_bucket if document_bucket in {"overview", "strength", "history"} else "other"
                if source_outline_route and _SOURCE_OUTLINE_META_RE.search(candidate):
                    continue
                best_score = _score_source_candidate(
                    candidate,
                    bucket="other",
                    document_bucket=document_bucket,
                    document=document,
                )
                if re.search(r"(19|20)\d{2}年|\d+(?:\.\d+)?%|\d+件|\d+人|\d+社", candidate):
                    best_score += 2
                if re.search(r"(調査|報告|発表|公表|導入|運用|対策|被害|攻撃|検知|リスク|事例)", candidate):
                    best_score += 2
                if len(candidate) < 18:
                    best_score -= 2
                if len(candidate) > 160:
                    best_score -= 2
                if product_intro_route:
                    best_bucket = _resolve_product_intro_source_bucket(candidate)
                    best_score += _score_product_intro_source_candidate(candidate)
                    if best_bucket == "history" and _score_product_intro_source_candidate(candidate) <= 0:
                        best_score -= 2
                if source_outline_route:
                    best_bucket = _resolve_source_outline_fact_bucket(candidate)
                    best_score += _score_source_outline_candidate(candidate)
                if best_score < 3:
                    continue
            gathered.append(
                (
                    -best_score,
                    doc_index,
                    candidate_index,
                    {
                        "bucket": best_bucket,
                        "fact_text": candidate,
                        "source_title": str(document.get("title") or "").strip(),
                        "locator": str(document.get("locator") or "").strip(),
                    },
                )
            )
    if not gathered:
        return []
    gathered.sort(key=lambda item: item[:3])
    by_bucket_limits = (
        {"overview": 2, "strength": 2, "history": 2, "other": 1}
        if prompt_primary_company_intro
        else (
            {"overview": 2, "strength": 2, "history": 1, "other": 3}
            if product_intro_route
            else (
                {
                    "構成とサイズ": 2,
                    "主な特徴": 2,
                    "活用場面": 1,
                    "公開条件": 1,
                    "使う環境": 1,
                    "主要な数値": 2,
                    "other": 1,
                }
                if source_outline_route
                else {"overview": 2, "strength": 2, "history": 2, "other": 3}
            )
        )
    )
    counts = {key: 0 for key in by_bucket_limits}
    doc_counts: Dict[str, int] = {}
    selected: List[Dict[str, str]] = []
    seen_texts: set[str] = set()
    for _, _, _, item in gathered:
        bucket = str(item.get("bucket") or "other")
        fact_text = _normalize_source_fact_text(item.get("fact_text", ""))
        dedupe_key = re.sub(r"\s+", "", fact_text)
        if not fact_text or dedupe_key in seen_texts:
            continue
        doc_key = str(item.get("locator") or item.get("source_title") or "").strip()
        max_doc_items = 3 if product_intro_route else (6 if source_outline_route else 2)
        if not prompt_primary_company_intro and doc_key and doc_counts.get(doc_key, 0) >= max_doc_items:
            continue
        limit = by_bucket_limits.get(bucket, 1)
        if counts.get(bucket, 0) >= limit:
            continue
        seen_texts.add(dedupe_key)
        counts[bucket] = counts.get(bucket, 0) + 1
        if doc_key:
            doc_counts[doc_key] = doc_counts.get(doc_key, 0) + 1
        selected.append(
            {
                "bucket": bucket,
                "fact_text": fact_text,
                "source_title": str(item.get("source_title") or "").strip(),
                "locator": str(item.get("locator") or "").strip(),
            }
        )
        if len(selected) >= 6:
            break
    return selected


def _derive_source_grounding_status(normalized: Dict[str, Any]) -> str:
    if not bool(normalized.get("source_grounding_required")):
        return "not_required"
    documents = _normalize_source_documents(normalized.get("source_documents"))
    if not documents:
        return "pending_documents"
    items = normalized.get("source_grounding_items", []) or []
    return "resolved" if len(items) >= 2 else "insufficient"


def _is_source_outline_route(normalized: Dict[str, Any]) -> bool:
    semantic_key = str(normalized.get("semantic_article_key") or normalized.get("article_type") or "").strip().lower()
    return semantic_key in _SOURCE_OUTLINE_ROUTE_KEYS


def _normalize_source_outline_label(text: str) -> str:
    value = _normalize_source_fact_text(text, max_length=48)
    value = re.sub(r"^[#*・●■◆\-–—]+\s*", "", value)
    value = re.sub(r"^\d+[\.\)]\s*", "", value)
    value = re.sub(r"\s*[:：]\s*$", "", value)
    value = value.strip(" 　-・")
    if not value or len(value) < 4 or len(value) > 18:
        return ""
    if not _SOURCE_OUTLINE_JA_RE.search(value):
        return ""
    if _is_low_signal_source_fact(value):
        return ""
    if _SOURCE_NOISE_PATTERN.search(value) or _SOURCE_COURTESY_PATTERN.search(value) or _SOURCE_META_PATTERN.search(value):
        return ""
    if _SOURCE_OUTLINE_META_RE.search(value):
        return ""
    if re.search(r"[。！？.!?]$", value):
        return ""
    return value


def _extract_source_heading_labels(normalized: Dict[str, Any], *, limit: int = 4) -> List[str]:
    if not _is_source_outline_route(normalized):
        return []
    documents = _normalize_source_documents(normalized.get("source_documents"))
    labels: List[str] = []
    for document in documents:
        raw_lines = re.split(r"\n+", str(document.get("content") or ""))
        for raw_line in raw_lines:
            label = _normalize_source_outline_label(raw_line)
            if not label or label in labels:
                continue
            labels.append(label)
            if len(labels) >= limit:
                return labels
    return labels


def _iter_source_theme_texts(normalized: Dict[str, Any]) -> List[str]:
    texts: List[str] = []
    documents = _normalize_source_documents(normalized.get("source_documents"))
    for document in documents:
        title = _normalize_source_fact_text(str(document.get("title") or ""), max_length=120)
        if title:
            texts.append(title)
        for raw_part in _SOURCE_SPLIT_PATTERN.split(str(document.get("content") or "")):
            compact = _normalize_source_fact_text(raw_part, max_length=180)
            if not compact:
                continue
            if _scan_injection_patterns(compact):
                continue
            if _SOURCE_NOISE_PATTERN.search(compact) or _SOURCE_COURTESY_PATTERN.search(compact) or _SOURCE_META_PATTERN.search(compact):
                continue
            if _SOURCE_OUTLINE_META_RE.search(compact):
                continue
            texts.append(compact)
    return texts


def _derive_source_theme_labels(normalized: Dict[str, Any], *, limit: int = 4) -> List[str]:
    if not _is_source_outline_route(normalized):
        return []
    labels: List[str] = []
    for text in _iter_source_theme_texts(normalized):
        for label, pattern in _SOURCE_THEME_LABEL_PATTERNS:
            if not pattern.search(text):
                continue
            if label not in labels:
                labels.append(label)
            break
        if len(labels) >= limit:
            break
    return labels


def _score_source_outline_candidate(text: str) -> int:
    value = _normalize_source_fact_text(text, max_length=180)
    if not value:
        return -4
    score = 0
    theme_hits = 0
    for _, pattern in _SOURCE_THEME_LABEL_PATTERNS:
        if pattern.search(value):
            theme_hits += 1
    score += min(6, theme_hits * 3)
    if re.search(
        r"\b(?:E2B|E4B|2B|4B|26B|31B|128K|256K|apache 2\.0|ai studio|ai edge gallery|hugging face|ollama)\b",
        value,
        re.I,
    ):
        score += 3
    if re.search(r"\d", value):
        score += 2
    if re.search(r"(comes in|available under|supports|developers can|download from|available in|family supports|includes)", value, re.I):
        score += 2
    if len(value) < 24 and not re.search(r"\d", value):
        score -= 2
    if _SOURCE_OUTLINE_META_RE.search(value):
        score -= 6
    return score


def _resolve_source_outline_fact_bucket(text: str) -> str:
    value = _normalize_source_fact_text(text, max_length=180)
    for label, pattern in _SOURCE_THEME_LABEL_PATTERNS:
        if pattern.search(value):
            return label
    return "other"


def _derive_source_outline_labels(normalized: Dict[str, Any], *, limit: int = 4) -> List[str]:
    if not _is_source_outline_route(normalized):
        return []
    labels: List[str] = []
    for candidate in [
        *_extract_source_heading_labels(normalized, limit=limit),
        *_derive_source_theme_labels(normalized, limit=limit),
    ]:
        compact = str(candidate or "").strip()
        if not compact or compact in labels:
            continue
        labels.append(compact)
        if len(labels) >= limit:
            break
    return labels


def _clean_source_title(title: str) -> str:
    value = _normalize_source_fact_text(title, max_length=120)
    value = re.sub(r"\s*(?:\||｜| - | – | — ).*$", "", value)
    return value.strip(" 　-・")


def _extract_source_title_anchor(title: str) -> str:
    value = _clean_source_title(title)
    if not value or _SOURCE_OUTLINE_META_RE.search(value):
        return ""
    match = _SOURCE_TITLE_ENTITY_RE.match(value)
    if match:
        return match.group(1).strip(" 　-・")
    if _SOURCE_OUTLINE_JA_RE.search(value) and 4 <= len(value) <= 28:
        return value
    if re.search(r"[A-Za-z]", value) and len(value) <= 28:
        return value
    return ""


def _derive_source_main_focus(normalized: Dict[str, Any]) -> str:
    if not _is_source_outline_route(normalized):
        return ""
    documents = sorted(
        _normalize_source_documents(normalized.get("source_documents")),
        key=lambda item: -len(str(item.get("content") or "")),
    )
    for document in documents:
        anchor = _extract_source_title_anchor(str(document.get("title") or ""))
        if not anchor:
            continue
        normalized_anchor = _normalize_focus_text(anchor, max_length=36)
        if not normalized_anchor:
            continue
        if _FOCUS_VERB_SUFFIX_RE.search(normalized_anchor):
            return normalized_anchor
        suffix = "を整理する" if _SOURCE_OUTLINE_JA_RE.search(normalized_anchor) else "の要点を整理する"
        return f"{normalized_anchor}{suffix}"[:72]
    for label in _derive_source_outline_labels(normalized, limit=2):
        if label:
            return f"{label}を整理する"[:72]
    return ""


def _collect_source_signals(documents: List[Dict[str, Any]]) -> Dict[str, int]:
    scores: Dict[str, int] = {}
    for document in documents:
        blob = " ".join(
            [
                str(document.get("title") or ""),
                str(document.get("locator") or ""),
                str(document.get("content") or "")[:1200],
            ]
        )
        for key, pattern in _SOURCE_SIGNAL_PATTERNS.items():
            if pattern.search(blob):
                scores[key] = int(scores.get(key, 0)) + 1
    return scores


def _rank_source_fit_candidates(signal_scores: Dict[str, int]) -> List[str]:
    semantic_scores = {
        "company_introduction": int(signal_scores.get("company", 0)),
        "product_introduction": int(signal_scores.get("product", 0)),
        "activity_introduction": int(signal_scores.get("activity", 0)),
        "recruit_culture": int(signal_scores.get("recruit", 0)),
        "implementation_case": int(signal_scores.get("implementation", 0)),
        "improvement_case": int(signal_scores.get("improvement", 0)),
        "incident_case": int(signal_scores.get("incident", 0)),
        "learning_case": int(signal_scores.get("learning", 0)),
        "comparative_review": int(signal_scores.get("compare", 0)),
    }
    ranked = sorted(
        (
            (score, semantic_key)
            for semantic_key, score in semantic_scores.items()
            if score > 0
        ),
        key=lambda item: (-item[0], item[1]),
    )
    return [semantic_key for _, semantic_key in ranked[:3]]


def _build_source_fit(normalized: Dict[str, Any]) -> Dict[str, Any]:
    semantic_key = str(normalized.get("semantic_article_key") or "").strip().lower()
    documents = _normalize_source_documents(normalized.get("source_documents"))
    source_grounding_items = [
        dict(item)
        for item in list(normalized.get("source_grounding_items") or [])
        if isinstance(item, dict)
    ]
    available_buckets = {
        str(item.get("bucket") or "").strip()
        for item in source_grounding_items
        if str(item.get("bucket") or "").strip()
    }
    document_buckets = {
        _detect_source_bucket(document)
        for document in documents
        if _detect_source_bucket(document)
    }
    signal_scores = _collect_source_signals(documents)
    candidate_targets = _rank_source_fit_candidates(signal_scores)
    required_actions: List[str] = []
    missing_buckets: List[str] = []
    status = "pass"

    if not documents and not bool(normalized.get("source_grounding_required")):
        return {
            "status": "pass",
            "missing_buckets": [],
            "required_actions": [],
            "candidate_targets": candidate_targets,
            "matched_signals": signal_scores,
            "summary": "ソース適合: URLだけの段階では追加確認を保留しています。",
        }
    if bool(normalized.get("source_grounding_required")) and not documents:
        status = "block"
        required_actions.append("ソース本文を取得できるURLまたは資料を追加してください。")
    elif semantic_key == "company_introduction":
        has_overview = "overview" in available_buckets or "overview" in document_buckets or int(signal_scores.get("company", 0)) > 0
        has_strength_or_history = bool({"strength", "history"} & (available_buckets | document_buckets))
        if not has_overview:
            status = "block"
            missing_buckets.append("overview")
            required_actions.append("会社概要または事業内容が分かる公式ソースを追加してください。")
        if not has_strength_or_history:
            status = "warn" if status == "pass" else status
            missing_buckets.append("strength_or_history")
            required_actions.append("強みまたは沿革が分かる公式ソースを追加すると精度が安定します。")
    elif semantic_key == "product_introduction":
        if int(signal_scores.get("product", 0)) <= 0:
            status = "block"
            required_actions.append("商品・サービスの機能や用途が分かる公式ページを追加してください。")
    elif semantic_key == "activity_introduction":
        if int(signal_scores.get("activity", 0)) <= 0:
            status = "block"
            required_actions.append("活動内容やプロジェクトの実態が分かるソースを追加してください。")
    elif semantic_key == "recruit_culture":
        if int(signal_scores.get("recruit", 0)) <= 0:
            status = "block"
            required_actions.append("採用情報やカルチャー紹介など、働き方が分かるソースを追加してください。")
    elif semantic_key == "implementation_case":
        if int(signal_scores.get("implementation", 0)) <= 0:
            status = "block"
            required_actions.append("導入前後や進め方が分かる事例ソースを追加してください。")
    elif semantic_key == "improvement_case":
        if int(signal_scores.get("improvement", 0)) <= 0:
            status = "block"
            required_actions.append("改善前後の変化が分かるソースを追加してください。")
    elif semantic_key == "incident_case":
        if int(signal_scores.get("incident", 0)) <= 0:
            status = "block"
            required_actions.append("障害内容、原因、再発防止が分かるソースを追加してください。")
    elif semantic_key == "learning_case":
        if int(signal_scores.get("learning", 0)) <= 0 and int(signal_scores.get("implementation", 0)) <= 0:
            status = "block"
            required_actions.append("学習用ケースや振り返りが分かるソースを追加してください。")
    elif semantic_key == "comparative_review":
        comparison_axes = _resolve_comparison_axes(normalized)
        if _journey_requires_comparison_axes(normalized) and not comparison_axes:
            status = "block"
            required_actions.append("比較軸を1つ以上指定してください。")
        elif len(documents) < 2:
            status = "warn"
            required_actions.append("比較対象の差分が分かるソースを2件以上そろえると安定します。")

    summary_map = {
        "pass": "ソース適合: 現在の選択と大きな矛盾はありません。",
        "warn": "ソース適合: 生成は可能ですが、補足ソースがあると安定します。",
        "block": "ソース適合: 現状のままでは選択内容を安全に確定できません。",
    }
    return {
        "status": status,
        "missing_buckets": list(dict.fromkeys(missing_buckets)),
        "required_actions": list(dict.fromkeys(required_actions)),
        "candidate_targets": candidate_targets,
        "matched_signals": signal_scores,
        "summary": summary_map.get(status, ""),
    }


def _derive_narrative_axis(normalized: Dict[str, Any]) -> str:
    if _is_company_introduction_like(normalized):
        return ""
    interview_patch = _build_interview_contract_patch(normalized)
    comparison_values = {
        str(normalized.get("topic_statement") or "").strip(),
        str(normalized.get("topic") or "").strip(),
        str(normalized.get("audience_profile") or "").strip(),
        str(normalized.get("speaker_profile") or "").strip(),
    }
    candidates = [
        normalized.get("narrative_axis", ""),
        interview_patch.get("narrative_axis", ""),
    ]
    for candidate in candidates:
        value = _sanitize_free_text(candidate, max_length=160).strip(" 　、。")
        if not value:
            continue
        if value in comparison_values:
            continue
        return value[:80]
    return ""


def _derive_knowledge_lenses(normalized: Dict[str, Any]) -> List[str]:
    if _is_company_introduction_like(normalized):
        return []
    raw_values: List[str] = []
    raw_values.extend(_normalize_string_list(normalized.get("knowledge_lenses")))
    raw_values.extend(_build_interview_contract_patch(normalized).get("knowledge_lenses", []))
    comparison_values = {
        str(normalized.get("topic_statement") or "").strip(),
        str(normalized.get("topic") or "").strip(),
        str(normalized.get("audience_profile") or "").strip(),
        str(normalized.get("speaker_profile") or "").strip(),
        _derive_narrative_axis(normalized),
    }
    normalized_values: List[str] = []
    for item in raw_values:
        value = _sanitize_free_text(item, max_length=120).strip(" 　、。")
        if (
            not value
            or value in comparison_values
            or value in normalized_values
        ):
            continue
        normalized_values.append(value[:80])
    return normalized_values[:2]


def _build_interview_contract_patch(normalized: Dict[str, Any]) -> Dict[str, Any]:
    interview_answers = normalized.get("interview_answers", {}) or {}
    if not isinstance(interview_answers, dict):
        interview_answers = {}
    writer_role = str(
        normalized.get("writer_role")
        or normalized.get("speaker_profile")
        or ""
    ).strip()
    return build_interview_contract_patch(
        interview_answers,
        writer_role=writer_role,
    )


def _knowledge_lens_to_must_cover_hint(lens: str) -> str:
    value = str(lens or "").strip()
    if not value:
        return ""
    if re.search(r"(法務|コンプライアンス|リーガル)", value, re.I):
        return "法務・コンプライアンスの観点から安心材料と注意点を言語化する"
    if re.search(r"(ブランド|ブランディング|広報)", value, re.I):
        return "企業ブランディングの観点で価値の伝え方を整える"
    if re.search(r"(編集|記者|ジャーナリスト)", value, re.I):
        return "編集の観点で論点の見せ方と流れを整える"
    compact = re.sub(r"を混ぜる$", "", value).strip(" 　、。")
    return (compact[:32] + "も判断材料に含める").strip()


def _normalize_focus_text(text: Any, *, max_length: int = 72) -> str:
    value = _sanitize_free_text(text, max_length=max_length + 40).strip(" 　、。")
    if not value:
        return ""
    value = re.sub(r"^(?:今回は|今回はまず|この記事では|この記事で|noteに初めて投稿するので|初回投稿として)", "", value)
    value = re.sub(r"^(?:会社紹介記事(?:を)?|自社説明(?:を)?|自社紹介(?:を)?)", "", value)
    value = re.sub(
        r"(?:を)?(?:表示してください|まとめてください|作成してください|生成してください|書いてください|かいてください|教えてください)$",
        "",
        value,
    )
    value = value.strip(" 　、。")
    if len(value) > max_length:
        value = value[:max_length].rstrip(" 　、。")
    return value


def _normalize_focus_main_focus(text: Any) -> str:
    value = _normalize_focus_text(text, max_length=72)
    if not value:
        return ""
    if re.search(r"(会社紹介|自社紹介|自社説明)", value):
        if re.search(r"(歴史|沿革|歩み)", value) and re.search(r"(事業|事業内容|サービス)", value):
            return "自社の事業と歩みを紹介する"
        return "自社の全体像を紹介する"
    if re.search(r"(事業内容|サービス)", value) and re.search(r"(歴史|沿革|歩み)", value):
        return "自社の事業と歩みを紹介する"
    if re.search(r"(事業内容|サービス)", value):
        return "自社の事業内容を紹介する"
    if re.search(r"(歴史|沿革|歩み)", value):
        return "自社の歩みを紹介する"
    if _looks_prompt_like_topic(value):
        compact = re.sub(_PROMPT_LIKE_TOPIC_RE, "", value).strip(" 　、。")
        if compact:
            if _FOCUS_VERB_SUFFIX_RE.search(compact):
                return compact
            return f"{compact}を整理する"[:72]
    if (
        len(value) > 40
        or "。" in value
        or re.search(r"(解説記事|比較レビュー|お知らせ|資料|ソース|事実を使いながら|資料に沿って|簡潔に|読みやすく)", value)
    ):
        compact = _compact_instruction_like_focus(value)
        if compact:
            return compact[:72]
    if _FOCUS_VERB_SUFFIX_RE.search(value):
        return value[:72]
    return value[:72]


def _compact_instruction_like_focus(text: Any) -> str:
    value = _normalize_focus_text(text, max_length=72)
    if not value:
        return ""
    value = re.sub(r"。.*$", "", value)
    value = re.sub(
        r"(?:資料|ソース|本文|事実).*(?:使いながら|を使って|に沿って|を踏まえて|をもとに).*$",
        "",
        value,
    )
    value = re.sub(r"(?:資料|ソース).*$", "", value)
    value = re.sub(r"(?:解説記事|比較レビュー|事例記事|事例紹介|お知らせ)$", "", value)
    value = re.sub(r"(?:として整理する|として説明する)$", "", value)
    value = value.strip(" 　、。")
    if "、" in value:
        first_clause = value.split("、", 1)[0].strip(" 　、。")
        if 8 <= len(first_clause) <= 40 and (first_clause.endswith("か") or len(value) > 40):
            value = first_clause
    return value[:48].rstrip(" 　、。")


def _focus_bucket_anchor(bucket: str) -> str:
    key = str(bucket or "").strip().lower()
    if key == "overview":
        return "事業内容"
    if key == "strength":
        return "強み"
    if key == "history":
        return "歩み"
    if key == "構成とサイズ":
        return "構成とサイズ"
    if key == "主な特徴":
        return "主な特徴"
    if key == "活用場面":
        return "活用場面"
    if key == "公開条件":
        return "公開条件"
    if key == "使う環境":
        return "使う環境"
    if key == "主要な数値":
        return "主要な数値"
    return "具体例"


def _derive_company_intro_bucket_items(normalized: Dict[str, Any], *, limit: int = 3) -> List[str]:
    if not _is_company_introduction_like(normalized):
        return []
    labels: List[str] = []
    for item in list(normalized.get("source_grounding_items") or []):
        if not isinstance(item, dict):
            continue
        anchor = _focus_bucket_anchor(str(item.get("bucket") or "other"))
        if not anchor or anchor == "具体例":
            continue
        labels.append(anchor)
    return _dedupe_text_list(labels, limit=limit)


def _derive_source_backed_company_intro_surface_labels(
    normalized: Dict[str, Any],
    *,
    limit: int = 2,
) -> List[str]:
    if not _is_company_introduction_like(normalized):
        return []
    source_grounding_items = [
        dict(item)
        for item in list(normalized.get("source_grounding_items") or [])
        if isinstance(item, dict)
    ]
    source_documents = _normalize_source_documents(normalized.get("source_documents"))
    source_blob = "\n".join(
        [
            *[
                " ".join(
                    [
                        str(item.get("source_title") or "").strip(),
                        str(item.get("fact_text") or "").strip(),
                    ]
                ).strip()
                for item in source_grounding_items
            ],
            *[
                " ".join(
                    [
                        str(document.get("title") or "").strip(),
                        str(document.get("locator") or "").strip(),
                        _normalize_source_fact_text(str(document.get("content") or ""), max_length=220),
                    ]
                ).strip()
                for document in source_documents
            ],
        ]
    )
    if not source_blob:
        return []

    labels: List[str] = []
    if _COMPANY_INTRO_STANCE_SOURCE_RE.search(source_blob) or _COMPANY_INTRO_STANCE_FACT_RE.search(source_blob):
        labels.append("大切にしている姿勢")
    if _COMPANY_INTRO_REASON_FACT_RE.search(source_blob):
        labels.append("選ばれる理由")
    return _dedupe_text_list(labels, limit=limit)


def _derive_blank_prompt_company_intro_surface_labels(normalized: Dict[str, Any]) -> List[str]:
    if not _is_company_introduction_like(normalized):
        return []
    if str(normalized.get("prompt_raw") or normalized.get("topic") or "").strip():
        return []
    if _normalize_string_list(normalized.get("prompt_instruction_items")):
        return []
    if _normalize_string_list(normalized.get("prompt_context_items")):
        return []

    source_fit = dict(normalized.get("source_fit", {}) or {})
    missing_buckets = {
        str(item or "").strip()
        for item in list(source_fit.get("missing_buckets") or [])
        if str(item or "").strip()
    }
    if "strength_or_history" not in missing_buckets:
        return []
    return _derive_source_backed_company_intro_surface_labels(normalized, limit=2)


def _derive_prompt_company_intro_surface_labels(normalized: Dict[str, Any]) -> List[str]:
    if not _is_company_introduction_like(normalized):
        return []
    prompt_raw = str(normalized.get("prompt_raw") or normalized.get("topic") or "").strip()
    if not prompt_raw:
        return []
    labels: List[str] = []
    for label, pattern in _COMPANY_INTRO_PROMPT_SURFACE_LABELS:
        if pattern.search(prompt_raw):
            labels.append(label)
    return _dedupe_text_list(labels, limit=3)


def _derive_company_intro_reader_surface_items(
    normalized: Dict[str, Any],
    *,
    limit: int = 3,
) -> List[str]:
    if not _is_company_introduction_like(normalized):
        return []
    bucket_items = _derive_company_intro_bucket_items(normalized, limit=3)
    source_backed_surface_items = _derive_source_backed_company_intro_surface_labels(normalized, limit=2)
    prompt_surface_items = _derive_prompt_company_intro_surface_labels(normalized)
    supplemental_items = _derive_blank_prompt_company_intro_surface_labels(normalized)
    requested_surfaces = set(prompt_surface_items)

    if not requested_surfaces:
        return _dedupe_text_list(
            [*bucket_items, *source_backed_surface_items, *supplemental_items],
            limit=limit,
        )

    prioritized: List[str] = []
    if "事業内容" in bucket_items:
        prioritized.append("事業内容")
    if "選ばれる理由" in requested_surfaces and ("強み" in bucket_items or "選ばれる理由" in source_backed_surface_items):
        prioritized.append("選ばれる理由")
    elif "強み" in bucket_items:
        prioritized.append("強み")

    if "大切にしている姿勢" in requested_surfaces:
        prioritized.append("大切にしている姿勢")
    elif "大切にしている姿勢" in source_backed_surface_items:
        prioritized.append("大切にしている姿勢")
    elif "導入時に重視すること" in requested_surfaces:
        prioritized.append("導入時に重視すること")

    if "大切にしている姿勢" in supplemental_items:
        prioritized.append("大切にしている姿勢")

    for item in [*bucket_items, *source_backed_surface_items, *prompt_surface_items, *supplemental_items]:
        if item == "強み" and "選ばれる理由" in prioritized:
            continue
        if item == "導入時に重視すること" and "大切にしている姿勢" in prioritized:
            continue
        prioritized.append(item)
    return _dedupe_text_list(prioritized, limit=limit)


def _derive_prompt_surface_items(normalized: Dict[str, Any]) -> Dict[str, Any]:
    raw_items: List[str] = []
    if _is_company_introduction_like(normalized):
        raw_items.extend(_derive_prompt_company_intro_surface_labels(normalized))
    raw_items = _dedupe_text_list(raw_items, limit=6)

    kept_items: List[str] = []
    dropped_items: List[Dict[str, str]] = []
    for item in raw_items:
        if item in kept_items:
            dropped_items.append({"item": item, "reason": "duplicate"})
            continue
        if len(kept_items) >= 3:
            dropped_items.append({"item": item, "reason": "bounded_limit"})
            continue
        kept_items.append(item)

    return {
        "raw_items": raw_items,
        "kept_items": kept_items,
        "dropped_items": dropped_items,
    }


def _dedupe_text_list(items: List[str], *, limit: int) -> List[str]:
    unique: List[str] = []
    for item in items:
        value = str(item or "").strip()
        if not value or value in unique:
            continue
        unique.append(value)
        if len(unique) >= limit:
            break
    return unique


def _derive_goal_bias(normalized: Dict[str, Any]) -> str:
    article_type = str(normalized.get("article_type") or "").strip().lower()
    semantic_key = str(normalized.get("semantic_article_key") or article_type).strip().lower()
    content_goal = str(normalized.get("content_goal") or "").strip().lower()
    if article_type == "announcement":
        return "clear_action"
    if article_type == "case_study":
        return "practical_replay"
    if content_goal == "action":
        return "next_step"
    if content_goal == "trust":
        return "evidence_first"
    if semantic_key == "product_introduction":
        return "balanced"
    if article_type == "branding":
        return "human_company_outline"
    return "balanced"


def _derive_focus_bundle(normalized: Dict[str, Any]) -> Dict[str, Any]:
    article_type = str(normalized.get("article_type") or "").strip().lower()
    semantic_key = str(normalized.get("semantic_article_key") or article_type).strip().lower()
    prompt_primary = _is_company_introduction_like(normalized)
    source_outline_labels = _derive_source_outline_labels(normalized, limit=4)
    source_grounding_items = [
        item
        for item in list(normalized.get("source_grounding_items", []) or [])
        if isinstance(item, dict) and str(item.get("fact_text") or "").strip()
    ]
    source_fact_pool = [
        _normalize_source_fact_text(item.get("fact_text", ""), max_length=120)
        for item in source_grounding_items
    ]
    main_focus_candidates: List[str] = []
    if prompt_primary:
        main_focus_candidates.extend(
            [
                _normalize_focus_main_focus(normalized.get("topic_statement", "")),
                _normalize_focus_main_focus(_normalize_string_list(normalized.get("prompt_instruction_items"))[0] if _normalize_string_list(normalized.get("prompt_instruction_items")) else ""),
            ]
        )
    else:
        main_focus_candidates.extend(
            [
                _normalize_focus_main_focus(normalized.get("topic_statement", "")),
                _normalize_focus_main_focus(normalized.get("core_message", "")),
                _normalize_focus_main_focus(normalized.get("narrative_axis", "")),
                _normalize_focus_main_focus(normalized.get("topic", "")),
                _derive_source_main_focus(normalized),
            ]
        )
    if prompt_primary and not any(main_focus_candidates):
        if any(str(item.get("bucket") or "") == "overview" for item in source_grounding_items) and any(
            str(item.get("bucket") or "") == "history" for item in source_grounding_items
        ):
            main_focus_candidates.append("自社の事業と歩みを紹介する")
        else:
            main_focus_candidates.append("自社の全体像を紹介する")
    main_focus = next((candidate for candidate in main_focus_candidates if candidate), "")

    support_points: List[str] = []
    if prompt_primary:
        support_points.extend(_derive_company_intro_reader_surface_items(normalized, limit=2))
    else:
        for label in source_outline_labels:
            if label:
                support_points.append(label)
        for candidate in (
            _normalize_focus_text(normalized.get("core_message", ""), max_length=40),
            _normalize_focus_text(normalized.get("narrative_axis", ""), max_length=40),
            _derive_branding_context_item(str(normalized.get("topic") or "")),
        ):
            if semantic_key == "product_introduction" and candidate and candidate == main_focus:
                continue
            if candidate:
                support_points.append(candidate)
        if article_type == "case_study":
            support_points.extend(_derive_case_study_prompt_labels(normalized, limit=3)[1:])
        for lens in _derive_knowledge_lenses(normalized):
            lens_hint = _knowledge_lens_to_must_cover_hint(lens)
            compact_lens = _normalize_focus_text(lens_hint, max_length=36)
            if compact_lens and not _is_product_intro_branding_lens_hint(normalized, compact_lens):
                support_points.append(compact_lens)
    support_points = _dedupe_text_list(support_points, limit=2)
    return {
        "main_focus": main_focus,
        "support_points": support_points,
        "goal_bias": _derive_goal_bias(normalized),
        "source_fact_pool": _dedupe_text_list(source_fact_pool, limit=6),
    }


def _is_announcement_meta_support_point(text: Any) -> bool:
    value = str(text or "").strip()
    if not value:
        return False
    if re.search(r"(迷わず|誤解なく|分かりやすく)", value):
        return True
    if re.search(r"(?:できる|確認できる|把握できる|伝わる)ようにする$", value):
        return True
    if re.search(r"(?:確認|把握|整理|周知).*(?:ようにする|ように伝える)$", value):
        return True
    return False


def _is_product_intro_rescue_focus_support_point(normalized: Dict[str, Any], text: Any) -> bool:
    semantic_key = str(normalized.get("semantic_article_key") or normalized.get("article_type") or "").strip().lower()
    if semantic_key != "product_introduction":
        return False
    value = str(text or "").strip()
    if not value:
        return False
    return value in {
        str(normalized.get("topic_statement") or "").strip(),
        str(normalized.get("core_message") or "").strip(),
    }


def _is_product_intro_branding_lens_hint(normalized: Dict[str, Any], text: Any) -> bool:
    semantic_key = str(normalized.get("semantic_article_key") or normalized.get("article_type") or "").strip().lower()
    if semantic_key != "product_introduction":
        return False
    return str(text or "").strip() == "企業ブランディングの観点で価値の伝え方を整える"


def _derive_must_cover(normalized: Dict[str, Any]) -> List[str]:
    article_type = str(normalized.get("article_type") or "").strip().lower()
    semantic_key = str(normalized.get("semantic_article_key") or article_type).strip().lower()
    prompt_primary = _is_company_introduction_like(normalized)
    focus_bundle = dict(normalized.get("focus_bundle", {}) or {})
    source_outline_labels = _derive_source_outline_labels(normalized, limit=4)
    support_points = [
        str(item or "").strip()
        for item in (focus_bundle.get("support_points", []) or [])
        if str(item or "").strip()
        and not _is_product_intro_rescue_focus_support_point(normalized, item)
        and not _is_product_intro_branding_lens_hint(normalized, item)
    ]
    if article_type == "announcement":
        support_points = [
            item
            for item in support_points
            if not _is_announcement_meta_support_point(item)
        ]
    if prompt_primary:
        merged_items = _derive_company_intro_reader_surface_items(normalized, limit=3)
        return merged_items or ["事業内容", "強み", "歩み"]

    defaults: Dict[str, List[str]] = {
        "explanatory_article": ["前提", "判断軸", "実務での使いどころ"],
        "daily_story": ["背景", "変化", "学び"],
        "branding": ["価値の背景", "現場の工夫", "読後の輪郭"],
        "company_introduction": ["事業内容", "強み", "歩み"],
        "product_introduction": ["誰のどんな課題に合うか", "選ぶ判断材料", "導入時の注意点"],
        "activity_introduction": ["何に取り組んでいるか", "取り組みの背景", "今後の広がり"],
        "recruit_culture": ["どんな働き方か", "チームの価値観", "向いている人"],
        "announcement": ["変更点", "対象と時期", "必要な行動"],
        **_CASE_STUDY_DEFAULT_LABELS,
        "industry_analysis": ["前提", "差分", "意思決定の示唆"],
        "comparative_review": ["比較条件", "差分", "用途別の結論"],
    }
    goal_bias = str(focus_bundle.get("goal_bias") or "")
    if semantic_key == "comparative_review":
        items: List[str] = []
        items.extend(_resolve_comparison_axes(normalized) or ["比較条件"])
        items.extend(["差分", "用途別の結論"])
        return _dedupe_text_list(items, limit=3)
    if semantic_key in _CASE_STUDY_DEFAULT_LABELS:
        return _derive_case_study_prompt_labels(normalized, limit=3)
    items: List[str] = list(support_points)
    if _is_source_outline_route(normalized):
        items = [*source_outline_labels, *items]
    if goal_bias == "next_step":
        items.append("必要な行動")
    if goal_bias == "evidence_first":
        items.append("根拠")
    items.extend(defaults.get(semantic_key, defaults.get(article_type, defaults["explanatory_article"])))
    return _dedupe_text_list(items, limit=3)


def _build_shadow_spec_inputs(normalized: Dict[str, Any]) -> Dict[str, Any]:
    focus_bundle = dict(normalized.get("focus_bundle", {}) or {})
    prompt_surface_items = dict(normalized.get("prompt_surface_items") or {})
    register_policy = dict(normalized.get("register_policy") or {})
    shadow_register_policy = {
        "base_register": str(register_policy.get("base_register") or "polite").strip() or "polite",
        "allowed_endings": _dedupe_text_list(register_policy.get("allowed_endings") or [], limit=4),
        "banned_endings": _dedupe_text_list(register_policy.get("banned_endings") or [], limit=4),
        "max_consecutive_same_ending": int(register_policy.get("max_consecutive_same_ending", 2) or 2),
    }
    source_fact_pool = [
        _normalize_source_fact_text(item, max_length=96)
        for item in list(focus_bundle.get("source_fact_pool") or [])[:6]
        if str(item or "").strip()
    ]
    return {
        "article_type": str(normalized.get("article_type") or "").strip().lower(),
        "semantic_article_key": str(normalized.get("semantic_article_key") or "").strip().lower(),
        "main_focus": _normalize_focus_text(
            focus_bundle.get("main_focus") or normalized.get("topic_statement") or "",
            max_length=72,
        ),
        "support_points": _dedupe_text_list(focus_bundle.get("support_points") or [], limit=3),
        "prompt_surface_items": _dedupe_text_list(prompt_surface_items.get("kept_items") or [], limit=2),
        "goal_bias": str(focus_bundle.get("goal_bias") or "").strip(),
        "must_cover": _dedupe_text_list(normalized.get("must_cover") or [], limit=4),
        "comparison_axes": _dedupe_text_list(normalized.get("comparison_axes") or [], limit=2),
        "source_fact_pool": _dedupe_text_list(source_fact_pool, limit=6),
        "allowed_pronouns": _dedupe_text_list(normalized.get("allowed_pronouns") or [], limit=4),
        "relationship_mode": str(normalized.get("relationship_mode") or "guide").strip() or "guide",
        "register_policy": shadow_register_policy,
    }


def _derive_need_question(normalized: Dict[str, Any]) -> Dict[str, Any]:
    article_type = str(normalized.get("article_type") or "")
    source_inputs = normalized.get("source_inputs", []) or []
    source_documents = normalized.get("source_documents", []) or []
    source_grounding_items = normalized.get("source_grounding_items", []) or []
    interview_answers = normalized.get("interview_answers", {}) or {}
    topic = str(normalized.get("topic") or "")
    answered = 0
    source_chars = max(
        sum(len(str(item or "")) for item in source_inputs),
        len(source_inputs) * 400,
        sum(
            len(str(item.get("content") or ""))
            for item in source_documents[:4]
            if isinstance(item, dict)
        ),
    )
    if isinstance(interview_answers, dict):
        answered = sum(1 for value in interview_answers.values() if str(value or "").strip())
    prompt_only_fact_score = 0
    if len(topic) >= 48:
        prompt_only_fact_score += 1
    if len(topic) >= 96:
        prompt_only_fact_score += 1
    prompt_only_fact_score += min(4, len(source_inputs))
    prompt_only_fact_score += min(
        4,
        len(
            [
                item
                for item in source_grounding_items
                if isinstance(item, dict) and str(item.get("fact_text") or "").strip()
            ]
        ),
    )
    source_excerpt = build_source_excerpt(
        [
            f"{str(item.get('title') or '').strip()} {str(item.get('content') or '')[:280]}".strip()
            for item in source_documents[:3]
            if isinstance(item, dict)
        ]
    )
    decision = decide_need_question(
        article_type=article_type,
        user_prompt=topic,
        source_count=len(source_inputs),
        source_chars=source_chars,
        fact_score=prompt_only_fact_score,
        answered=answered,
        source_excerpt=source_excerpt,
    )
    if article_type == "announcement":
        decision["ask"] = False
        if str(decision.get("reason") or "").startswith("announcement_"):
            decision["reason"] = "announcement_skip_default"
    return decision


def _resolve_speaker_profile(
    normalized: Dict[str, Any],
    *,
    defaults: Dict[str, Any],
    strict_saas_mode: str,
    field_sources: Dict[str, str],
) -> str:
    speaker_profile = str(normalized.get("speaker_profile") or "").strip()
    if speaker_profile:
        field_sources["speaker_profile"] = _field_source_or_default(field_sources, "speaker_profile", "input_contract")
        return speaker_profile
    writer_role = str(normalized.get("writer_role") or "").strip()
    if writer_role:
        field_sources["speaker_profile"] = _field_source_or_default(field_sources, "speaker_profile", "interview_answers")
        return writer_role
    if requires_explicit_profile_inputs(strict_saas_mode):
        field_sources.pop("speaker_profile", None)
        return ""
    field_sources["speaker_profile"] = "article_type_default"
    return str(defaults.get("speaker_profile") or "").strip()


def _resolve_audience_profile(
    normalized: Dict[str, Any],
    *,
    defaults: Dict[str, Any],
    prompt_intent: Dict[str, Any],
    strict_saas_mode: str,
    field_sources: Dict[str, str],
) -> str:
    audience_profile = str(normalized.get("audience_profile") or "").strip()
    if audience_profile:
        field_sources["audience_profile"] = _field_source_or_default(field_sources, "audience_profile", "input_contract")
        return audience_profile
    interview_answers = normalized.get("interview_answers", {}) or {}
    if isinstance(interview_answers, Mapping):
        interview_target = str(interview_answers.get("target") or "").strip()
        if interview_target:
            field_sources["audience_profile"] = _field_source_or_default(
                field_sources,
                "audience_profile",
                "interview_answers",
            )
            return interview_target
    if not requires_explicit_profile_inputs(strict_saas_mode):
        prompt_audiences = _normalize_string_list(prompt_intent.get("prompt_audience_candidates"))
        if prompt_audiences:
            field_sources["audience_profile"] = "prompt_intent"
            return prompt_audiences[0]
        field_sources["audience_profile"] = "article_type_default"
        return str(defaults.get("audience_profile") or "").strip()
    field_sources.pop("audience_profile", None)
    return ""


def _resolve_topic_statement(
    normalized: Dict[str, Any],
    *,
    interview_patch: Dict[str, Any],
    prompt_intent: Dict[str, Any],
    strict_saas_mode: str,
    field_sources: Dict[str, str],
) -> tuple[str, str]:
    explicit_topic_statement = str(normalized.get("topic_statement") or "").strip()
    if explicit_topic_statement:
        return explicit_topic_statement, _field_source_or_default(field_sources, "topic_statement", "input_contract")
    interview_topic_statement = str(interview_patch.get("topic_statement") or "").strip()
    if interview_topic_statement:
        return interview_topic_statement, _field_source_or_default(field_sources, "topic_statement", "interview_answers")
    if prompt_intent.get("prefer_prompt_topic") and not blocks_prompt_intent_rewrite(strict_saas_mode):
        preferred_topic = str(prompt_intent.get("preferred_topic_statement") or "").strip()
        if preferred_topic and not _looks_prompt_like_topic(preferred_topic):
            return preferred_topic, "user_prompt"
    article_type = str(normalized.get("article_type") or "").strip().lower()
    semantic_key = str(normalized.get("semantic_article_key") or article_type).strip().lower()
    core_message = str(normalized.get("core_message") or "").strip()
    if article_type == "branding" and semantic_key == "product_introduction" and core_message:
        return core_message, _field_source_or_default(field_sources, "core_message", "input_contract")
    return "", ""


def _build_strict_saas_missing_items(contract: Dict[str, Any]) -> List[Dict[str, str]]:
    strict_saas_mode = normalize_strict_saas_mode(contract.get("strict_saas_mode"))
    field_sources = _normalize_field_sources(contract.get("field_sources"))
    missing_items: List[Dict[str, str]] = []
    semantic_key = str(contract.get("semantic_article_key") or contract.get("article_type") or "").strip().lower()
    has_comparative_source_context = bool(contract.get("source_grounding_required")) or bool(
        _normalize_source_documents(contract.get("source_documents"))
    )
    if (
        semantic_key == "comparative_review"
        and has_comparative_source_context
        and _journey_requires_comparison_axes(contract)
        and not _resolve_comparison_axes(contract)
    ):
        missing_items.append(
            {
                "field": "comparison_axes",
                "issue_type": "missing",
                "required_format": "比較軸を1つ以上選ぶ（例: 価格 / 性能 / 用途）",
                "question_template": "比較軸を1つ以上選択してください。",
                "example_answer": "価格と用途を比較軸にする",
            }
        )
    if not requires_explicit_profile_inputs(strict_saas_mode):
        return missing_items
    article_type = str(contract.get("article_type") or "").strip().lower()
    speaker_examples = {
        "explanatory_article": (
            "どの立場から解説しますか？",
            "誰の立場で解説するか（例: 編集担当として語る）",
            "編集担当として、実務で迷いやすい点を整理する",
        ),
        "industry_analysis": (
            "どの立場から分析しますか？",
            "誰の立場で分析するか（例: アナリストとして語る）",
            "アナリストとして、市場の変化点を整理する",
        ),
        "comparative_review": (
            "どの立場から比較しますか？",
            "誰の立場で比較するか（例: 比較検証担当として語る）",
            "比較検証担当として、選定軸を整理する",
        ),
        "branding": (
            "誰の立場で紹介しますか？",
            "誰の立場で紹介するか（例: 運営担当として語る）",
            "運営担当として、自社の価値を紹介する",
        ),
        "announcement": (
            "誰の立場で知らせますか？",
            "誰の立場で知らせるか（例: 広報担当として語る）",
            "広報担当として、変更点を正確に知らせる",
        ),
        "case_study": (
            "誰の立場で事例を説明しますか？",
            "誰の立場で事例を説明するか（例: 導入支援担当として語る）",
            "導入支援担当として、導入時の判断ポイントを振り返る",
        ),
        "daily_story": (
            "誰の立場で書きますか？",
            "誰の立場で書くか（例: 現場担当として語る）",
            "現場担当として、日々の気づきを共有する",
        ),
    }
    audience_examples = {
        "explanatory_article": "実務担当者向けに、基本と判断軸を整理する",
        "industry_analysis": "意思決定者向けに、市場の変化を要約する",
        "comparative_review": "比較検討中の担当者向けに、選び方を整理する",
        "branding": "初めて会社を知る読者向けに、事業と強みを伝える",
        "announcement": "既存ユーザー向けに、変更点と影響を伝える",
        "case_study": "同じ課題を持つ担当者向けに、再現条件を伝える",
        "daily_story": "普段の取り組みに関心がある読者向けに、気づきを共有する",
    }
    core_message_examples = {
        "branding": "自社の強みと提供価値を初めて読む人にも伝えたい",
        "announcement": "変更点と対応の要否を誤解なく伝えたい",
        "case_study": "どこで迷い、どう改善し、何が判断材料になったかを伝えたい",
    }
    speaker_profile = str(contract.get("speaker_profile") or "").strip()
    if not speaker_profile or str(field_sources.get("speaker_profile") or "") == "article_type_default":
        speaker_question, speaker_required, speaker_example = speaker_examples.get(
            article_type,
            (
                "誰の立場で語る記事にしますか？",
                "誰の立場で語るか（例: 編集担当として語る）",
                "編集担当として、要点を整理する",
            ),
        )
        missing_items.append(
            {
                "field": "speaker_profile",
                "issue_type": "missing",
                "required_format": speaker_required,
                "question_template": speaker_question,
                "example_answer": speaker_example,
            }
        )
    audience_profile = str(contract.get("audience_profile") or "").strip()
    if not audience_profile or str(field_sources.get("audience_profile") or "") in {"", "article_type_default", "prompt_intent"}:
        missing_items.append(
            {
                "field": "audience_profile",
                "issue_type": "missing",
                "required_format": "誰向けか（例: 実務担当者）",
                "question_template": "主な読者は誰ですか？",
                "example_answer": audience_examples.get(article_type, "実務担当者向けに、判断軸を示す"),
            }
        )
    content_goal = str(contract.get("content_goal") or "").strip().lower()
    core_message = str(contract.get("core_message") or "").strip()
    if (
        article_type in {"branding", "case_study", "announcement"}
        and content_goal not in {"", "auto"}
        and not core_message
        and not _can_skip_strict_core_message_requirement(contract)
    ):
        missing_items.append(
            {
                "field": "core_message",
                "issue_type": "missing",
                "required_format": "今回いちばん伝えたい核メッセージを1文で入力する",
                "question_template": "この文章で最終的に何を伝えたいですか？",
                "example_answer": core_message_examples.get(
                    article_type,
                    "今回いちばん伝えたい核メッセージを1文でまとめる",
                ),
            }
        )
    return missing_items


def _can_skip_strict_core_message_requirement(contract: Dict[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or article_type).strip().lower()
    if article_type != "branding" or semantic_key != "company_introduction":
        return False
    if str(contract.get("source_grounding_status") or "").strip().lower() != "resolved":
        return False
    source_fit = dict(contract.get("source_fit") or {})
    if str(source_fit.get("status") or "").strip().lower() == "block":
        return False
    focus_bundle = dict(contract.get("focus_bundle") or {})
    main_focus = str(focus_bundle.get("main_focus") or "").strip()
    support_points = _normalize_string_list(focus_bundle.get("support_points"))
    must_cover = _normalize_string_list(contract.get("must_cover"))
    return bool(main_focus) and (len(support_points) >= 2 or len(must_cover) >= 2)


def build_contract_missing_input_items(contract: Dict[str, Any]) -> List[Dict[str, str]]:
    """Expose current-mainline required-input checks without duplicating UI rules."""
    return _build_strict_saas_missing_items(contract)


def build_contract_question_items(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    question_items: List[Dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if str(item.get("field") or "").strip() not in _UI_QUESTION_FIELDS:
            continue
        question_items.append(dict(item))
    return question_items


def build_contract_clarification_items(
    contract: Dict[str, Any],
    *,
    prompt_intent: Dict[str, Any] | None = None,
) -> List[Dict[str, str]]:
    article_type = str(contract.get("article_type") or "").strip().lower()
    profile = dict(prompt_intent or {})
    if article_type == "branding" and bool(profile.get("ambiguity_detected")):
        return [
            {
                "field": "topic",
                "issue_type": "ambiguous",
                "required_format": "今回は『自社紹介記事そのもの』か『会社紹介記事の書き方ガイド』のどちらか1つに絞る",
                "question_template": "今回は自社紹介記事を書きたいですか、それとも書き方を整理したいですか？",
                "example_answer": "初回投稿としての自社紹介記事を書きたいです",
            }
        ]
    if (
        article_type == "case_study"
        and not bool(contract.get("allow_experience"))
        and not _normalize_source_documents(contract.get("source_documents"))
    ):
        return [
            {
                "field": "allow_experience",
                "issue_type": "ambiguous",
                "required_format": "case study として書くには source を追加するか、経験談の利用を許可する",
                "question_template": "case study として書くには source か経験談許可のどちらかが必要です。source を追加するか、経験談を許可してください。",
                "example_answer": "source を追加するか、経験談を許可する",
            }
        ]
    return []


def build_contract_source_context_items(contract: Dict[str, Any]) -> List[Dict[str, str]]:
    source_fit = dict(contract.get("source_fit") or {})
    if not bool(contract.get("source_grounding_required")) and not source_fit:
        return []
    actions = _normalize_string_list(source_fit.get("required_actions"))
    if actions:
        return [
            {
                "field": "source",
                "issue_type": "insufficient",
                "required_format": " / ".join(actions[:2]),
                "question_template": actions[0],
                "example_answer": actions[0],
            }
        ]
    article_type = str(contract.get("article_type") or "").strip().lower()
    if article_type == "branding":
        return [
            {
                "field": "source",
                "issue_type": "insufficient",
                "required_format": "会社概要・事業内容・強み・沿革のいずれかが分かる公式ソースを2件以上そろえる",
                "question_template": "会社概要・強み・沿革が分かる公式ページを追加できますか？",
                "example_answer": "会社概要、強み、沿革の3ページを追加します",
            }
        ]
    return [
        {
            "field": "source",
            "issue_type": "insufficient",
            "required_format": "本文の主張を裏付ける一次情報（公式発表、調査、運用資料など）を2件以上そろえる",
            "question_template": "根拠として使えるURLや資料を追加できますか？",
            "example_answer": "公式発表と業界レポートの2件を追加します",
        }
    ]


def _requires_strict_source_context_gate(contract: Dict[str, Any]) -> bool:
    return _is_company_introduction_like(contract)


def build_contract_input_decision(
    contract: Dict[str, Any],
    *,
    prompt_intent: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    profile = dict(prompt_intent or {})
    article_type = str(contract.get("article_type") or "").strip().lower()
    if (
        str(profile.get("primary_intent") or "") == "meta_request"
        or (
            bool(profile.get("meta_request_signal"))
            and not bool(profile.get("content_generation_signal"))
        )
    ):
        return {
            "action": "block",
            "reason": "meta_request_blocked",
            "reason_code": error_codes.INP_NON_GENERATION_REQUEST,
            "needs_input_items": [],
            "question_items": [],
        }

    missing_items = build_contract_missing_input_items(contract)
    if missing_items:
        return {
            "action": "clarify",
            "reason": "missing_required_inputs",
            "reason_code": error_codes.INP_MISSING_REQUIRED,
            "needs_input_items": list(missing_items),
            "question_items": build_contract_question_items(list(missing_items)),
        }

    clarification_items = build_contract_clarification_items(contract, prompt_intent=profile)
    if clarification_items:
        return {
            "action": "clarify",
            "reason": (
                "case_study_requires_source_or_experience"
                if article_type == "case_study"
                and any(str(item.get("field") or "").strip() == "allow_experience" for item in clarification_items)
                else "intent_ambiguous"
            ),
            "reason_code": error_codes.INP_NEEDS_CLARIFICATION,
            "needs_input_items": list(clarification_items),
            "question_items": build_contract_question_items(list(clarification_items)),
        }

    source_fit = dict(contract.get("source_fit") or {})
    source_fit_blocked = str(source_fit.get("status") or "") == "block"
    strict_source_context_blocked = (
        _requires_strict_source_context_gate(contract)
        and bool(contract.get("source_grounding_required"))
        and str(contract.get("source_grounding_status") or "") in {"insufficient", "pending_documents"}
    )
    if (
        source_fit_blocked
        or strict_source_context_blocked
    ):
        source_items = build_contract_source_context_items(contract)
        return {
            "action": "clarify",
            "reason": "source_context_insufficient",
            "reason_code": error_codes.INP_SOURCE_CONTEXT_INSUFFICIENT,
            "needs_input_items": list(source_items),
            "question_items": [],
        }

    return {
        "action": "accept",
        "reason": "default_sufficient_input",
        "reason_code": "OK",
        "needs_input_items": [],
        "question_items": [],
    }


@dataclass
class ContractResolveResult:
    contract: Dict[str, Any]
    warnings: List[str]
    blocked_injection: bool
    security_gate: Dict[str, Any]


def resolve_input_contract(payload: Dict[str, Any]) -> ContractResolveResult:
    normalized = normalize_input_contract_v1(payload, allow_legacy_aliases=False)
    warnings: List[str] = []
    normalized["prompt_raw"] = str(normalized.get("prompt_raw") or normalized.get("topic") or "").strip()
    normalized["topic"] = str(normalized.get("prompt_raw") or normalized.get("topic") or "").strip()
    normalized["system_hint_items"] = _normalize_string_list(normalized.get("system_hint_items"))
    normalized["retry_memo"] = _normalize_string_list(normalized.get("retry_memo"))
    normalized["strict_saas_mode"] = normalize_strict_saas_mode(normalized.get("strict_saas_mode"))
    field_sources = _normalize_field_sources(normalized.get("field_sources"))
    article_type = str(normalized.get("article_type") or "explanatory_article")
    defaults = _ARTICLE_TYPE_DEFAULTS.get(article_type, _ARTICLE_TYPE_DEFAULTS["explanatory_article"])
    security_gate = {
        "decision": "pass",
        "blocked_input_fields": [],
        "blocked_patterns": [],
        "sanitized_source_documents": {
            "sanitized_document_count": 0,
            "removed_fragment_count": 0,
            "blocked_patterns": [],
        },
    }

    max_length_by_field = {
        "prompt_raw": 1200,
        "topic": 1200,
        "speaker_profile": 240,
        "audience_profile": 240,
        "topic_statement": 240,
        "core_message": 240,
    }
    blocked_input_fields = list(dict.fromkeys([*SECURITY_CONFIG.blocked_input_fields, "prompt_raw", "core_message"]))
    for field in blocked_input_fields:
        if field not in normalized:
            continue
        cleaned = _sanitize_free_text(normalized.get(field, ""), max_length=max_length_by_field.get(field, 240))
        normalized[field] = cleaned
        hits = _scan_injection_patterns(cleaned)
        if hits:
            security_gate["blocked_input_fields"].append(field)
            security_gate["blocked_patterns"].extend(hits)
            normalized[field] = "[BLOCKED]"
    normalized["prompt_raw"] = str(normalized.get("prompt_raw") or normalized.get("topic") or "").strip()
    normalized["topic"] = normalized["prompt_raw"]
    _apply_embedded_ui_prompt_slots(normalized, field_sources)

    normalized["writing_focus"] = _normalize_choice(
        normalized.get("writing_focus"),
        "auto",
        {"auto", "explanation", "experience", "analysis"},
        field="writing_focus",
    )
    normalized["tone_profile"] = _normalize_choice(
        normalized.get("tone_profile"),
        "auto",
        {"auto", "calm", "warm", "passionate", "formal"},
        field="tone_profile",
    )
    normalized["length_mode"] = _normalize_choice(
        normalized.get("length_mode"),
        "normal",
        {"adaptive", "short", "normal", "long"},
        field="length_mode",
    )
    normalized["structure"] = "auto"
    normalized["content_goal"] = _normalize_choice(
        normalized.get("content_goal"),
        "auto",
        {"auto", "interest", "explain", "action", "trust"},
        field="content_goal",
    )
    normalized["length_mode_requested"] = str(
        normalized.get("length_mode_requested") or normalized.get("length_mode") or ""
    ).strip()
    normalized["relationship_mode"] = str(normalized.get("relationship_mode") or "guide").strip() or "guide"
    normalized["source_documents"] = _normalize_source_documents(normalized.get("source_documents"))
    normalized["source_documents"], source_sanitization = _sanitize_source_documents(
        list(normalized.get("source_documents") or [])
    )
    security_gate["sanitized_source_documents"] = source_sanitization
    prompt_intent = derive_prompt_intent_profile(str(normalized.get("prompt_raw") or normalized.get("topic") or ""), article_type)
    normalized["ui_journey"] = _normalize_ui_journey(normalized.get("ui_journey"))
    normalized["comparison_axes"] = _resolve_comparison_axes(normalized)
    normalized["semantic_article_key"] = _resolve_semantic_article_key(
        normalized,
        prompt_intent=prompt_intent,
    )
    if str(normalized.get("semantic_article_key") or "").strip():
        field_sources["semantic_article_key"] = _field_source_or_default(
            field_sources,
            "semantic_article_key",
            "prompt_intent" if str(normalized.get("semantic_article_key") or "") == "company_introduction" else "article_type",
        )
    interview_patch = _build_interview_contract_patch(normalized)
    normalized["speaker_profile"] = _resolve_speaker_profile(
        normalized,
        defaults=defaults,
        strict_saas_mode=str(normalized.get("strict_saas_mode") or ""),
        field_sources=field_sources,
    )
    normalized["audience_profile"] = _resolve_audience_profile(
        normalized,
        defaults=defaults,
        prompt_intent=prompt_intent,
        strict_saas_mode=str(normalized.get("strict_saas_mode") or ""),
        field_sources=field_sources,
    )
    normalized["core_message"] = _derive_core_message(normalized)
    if normalized["core_message"]:
        field_sources["core_message"] = _field_source_or_default(
            field_sources,
            "core_message",
            "input_contract",
        )
    else:
        field_sources.pop("core_message", None)
    normalized["primary_topic_source"] = "topic"
    normalized["prompt_instruction_items"] = _derive_prompt_instruction_items(
        normalized,
        prompt_intent=prompt_intent,
    )
    normalized["prompt_context_items"] = _compact_prompt_context_items(
        _derive_prompt_context_items(
            normalized,
            prompt_intent=prompt_intent,
        )
    )
    normalized["topic_statement"], normalized["primary_topic_source"] = _resolve_topic_statement(
        normalized,
        interview_patch=interview_patch,
        prompt_intent=prompt_intent,
        strict_saas_mode=str(normalized.get("strict_saas_mode") or ""),
        field_sources=field_sources,
    )
    if normalized["topic_statement"]:
        field_sources["topic_statement"] = normalized["primary_topic_source"]
    else:
        field_sources.pop("topic_statement", None)
    if not str(normalized.get("narrative_axis") or "").strip():
        normalized["narrative_axis"] = str(interview_patch.get("narrative_axis") or "").strip()
        if normalized["narrative_axis"]:
            field_sources["narrative_axis"] = _field_source_or_default(field_sources, "narrative_axis", "interview_answers")
    normalized["narrative_axis"] = _derive_narrative_axis(normalized)
    if not _normalize_string_list(normalized.get("knowledge_lenses")):
        normalized["knowledge_lenses"] = list(interview_patch.get("knowledge_lenses") or [])
    normalized["knowledge_lenses"] = _derive_knowledge_lenses(normalized)
    normalized["register_policy"] = {
        "base_register": defaults["register_policy"]["base_register"],
        "allowed_endings": list(defaults["register_policy"]["allowed_endings"]),
        "banned_endings": [],
        "max_consecutive_same_ending": 2,
    }
    normalized["allowed_pronouns"] = list(defaults["allowed_pronouns"])
    normalized["field_sources"] = field_sources
    normalized["source_grounding_required"] = bool(list(normalized.get("source_documents", []) or []))
    normalized["source_grounding_items"] = _build_source_grounding_items(normalized)
    normalized["source_fit"] = _build_source_fit(normalized)
    source_fit_status = str(dict(normalized.get("source_fit") or {}).get("status") or "")
    if source_fit_status == "block":
        normalized["source_grounding_status"] = "insufficient"
    else:
        normalized["source_grounding_status"] = _derive_source_grounding_status(normalized)
    normalized["focus_bundle"] = _derive_focus_bundle(normalized)
    normalized["prompt_surface_items"] = _derive_prompt_surface_items(normalized)
    normalized["must_cover"] = _derive_must_cover(normalized)
    normalized["_shadow_spec_inputs"] = _build_shadow_spec_inputs(normalized)
    normalized["need_question"] = _derive_need_question(normalized)
    normalized["input_decision"] = build_contract_input_decision(
        normalized,
        prompt_intent=prompt_intent,
    )
    normalized["question_items"] = list(normalized["input_decision"].get("question_items", []) or [])
    normalized["semantic_dedupe_enabled"] = bool(SEMANTIC_DEDUPE_CONFIG.get("enabled", False))
    normalized["media"] = "note"

    # Preserve Phase01 fixed behavior.
    normalized["style_compact_for_seo"] = bool(
        normalized.get("article_type") == "daily_story" and normalized.get("media") == "seo"
    )
    normalized["question_mode"] = (
        "skip_default" if normalized.get("article_type") == "announcement" else "standard"
    )
    normalized["llm_runtime_policy"] = {
        "allow_model_fallback": bool(LLM_CONFIG.allow_model_fallback),
        "max_same_model_retries": int(LLM_CONFIG.max_same_model_retries),
        "retryable_error_classes": list(LLM_CONFIG.retryable_error_classes),
        "allow_prompt_truncation": allows_semantic_fallback(normalized.get("strict_saas_mode")),
        "strict_saas_mode": str(normalized.get("strict_saas_mode") or ""),
    }
    security_gate["blocked_input_fields"] = list(dict.fromkeys(str(item) for item in security_gate["blocked_input_fields"]))
    security_gate["blocked_patterns"] = list(dict.fromkeys(str(item) for item in security_gate["blocked_patterns"]))
    if security_gate["blocked_input_fields"]:
        if SECURITY_CONFIG.prompt_injection_mode == "block":
            raise PromptInjectionBlockedError(
                blocked_input_fields=security_gate["blocked_input_fields"],
                blocked_patterns=security_gate["blocked_patterns"],
                partial_contract=normalized,
            )
        warnings.append(error_codes.SEC_PROMPT_INJECTION_BLOCKED)
        security_gate["decision"] = "shadow"

    return ContractResolveResult(
        contract=normalized,
        warnings=warnings,
        blocked_injection=bool(security_gate["blocked_input_fields"]),
        security_gate=security_gate,
    )


def to_input_error(exc: InputContractValidationError) -> Dict[str, str]:
    return {
        "reason_code": str(getattr(exc, "reason_code", "") or error_codes.INP_MISSING_REQUIRED),
        "field": str(getattr(exc, "field", "") or ""),
        "message": str(exc),
    }
