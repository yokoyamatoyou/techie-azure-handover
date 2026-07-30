"""Pure writer-role and handoff default helpers for note_writer_app."""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Mapping, Optional, Set


CustomGenreLookup = Callable[[str], object]

WRITER_ROLE_AUTO_LABEL = "自動（おすすめ）"
WRITER_ROLE_COMPANY_INTRO_NEUTRAL_LABEL = "立場を前に出さない（おすすめ）"


def _handoff(
    writer_role: str,
    perspective: str,
    writing_focus: str,
    self_reference_policy: str = "watashitachi",
) -> Dict[str, str]:
    return {
        "writer_role": writer_role,
        "perspective": perspective,
        "writing_focus": writing_focus,
        "self_reference_policy": self_reference_policy,
    }


ARTICLE_TYPE_HANDOFF_DEFAULTS: Dict[str, Dict[str, str]] = {
    "explanatory_article": _handoff("自社の知見を持つ解説担当として語る", "expert", "explanation"),
    "industry_analysis": _handoff("自社の観察を整理する分析担当として語る", "expert", "analysis"),
    "comparative_review": _handoff("自社の知見を持つ編集担当として語る", "expert", "analysis"),
    "branding": _handoff("自社の企業担当者として語る", "corporate", "explanation"),
    "announcement": _handoff("運営担当として語る", "corporate", "explanation"),
    "case_study": _handoff("導入支援担当として語る", "corporate", "explanation"),
    "daily_story": _handoff("現場担当として語る", "blogger", "experience"),
    "default": _handoff("編集担当として語る", "expert", "explanation"),
}
SEMANTIC_ARTICLE_HANDOFF_DEFAULTS: Dict[str, Dict[str, str]] = {
    "announcement": _handoff("運営担当として語る", "corporate", "explanation"),
    "company_introduction": _handoff("自社の企業担当者として語る", "corporate", "explanation"),
    "product_introduction": _handoff("提供担当として語る", "corporate", "explanation"),
    "daily_story": _handoff("現場担当として語る", "blogger", "experience"),
}
WRITER_ROLE_OPTIONS_BY_ARTICLE_TYPE: Dict[str, List[str]] = {
    "explanatory_article": [WRITER_ROLE_AUTO_LABEL, "編集担当として語る", "解説担当として語る", "専門家として語る"],
    "industry_analysis": [WRITER_ROLE_AUTO_LABEL, "編集担当として語る", "アナリストとして語る", "専門家として語る"],
    "comparative_review": [WRITER_ROLE_AUTO_LABEL, "自社の知見を持つ編集担当として語る", "編集担当として語る", "比較検証担当として語る", "専門家として語る"],
    "branding": [WRITER_ROLE_AUTO_LABEL, "自社の企業担当者として語る", "企業広報として語る", "ブランド担当として語る", "導入支援担当として語る"],
    "announcement": [WRITER_ROLE_AUTO_LABEL, "運営担当として語る", "広報担当として語る", "編集担当として語る"],
    "case_study": [WRITER_ROLE_AUTO_LABEL, "導入支援担当として語る", "運営担当として語る", "編集担当として語る"],
    "daily_story": [WRITER_ROLE_AUTO_LABEL, "運営担当として語る", "現場担当として語る", "編集担当として語る"],
    "default": [WRITER_ROLE_AUTO_LABEL, "編集担当として語る", "運営担当として語る", "専門家として語る"],
}
WRITER_ROLE_OPTIONS_BY_SEMANTIC_KEY: Dict[str, List[str]] = {
    "announcement": [WRITER_ROLE_AUTO_LABEL, "運営担当として語る", "編集担当として語る"],
    "company_introduction": ["自社の企業担当者として語る", WRITER_ROLE_COMPANY_INTRO_NEUTRAL_LABEL, "企業広報として語る"],
    "daily_story": [WRITER_ROLE_AUTO_LABEL, "現場担当として語る", "編集担当として語る"],
    "product_introduction": [WRITER_ROLE_AUTO_LABEL, "ブランド担当として語る", "導入支援担当として語る"],
}
WRITER_ROLE_DEFAULT_BY_SEMANTIC_KEY: Dict[str, str] = {
    "announcement": "運営担当として語る",
    "company_introduction": "自社の企業担当者として語る",
    "daily_story": "現場担当として語る",
    "product_introduction": "ブランド担当として語る",
}
WRITER_ROLE_ARTICLE_TYPE_MANAGED_DEFAULT_LABELS: Set[str] = {
    str(defaults.get("writer_role") or "").strip()
    for defaults in (
        list(ARTICLE_TYPE_HANDOFF_DEFAULTS.values())
        + list(SEMANTIC_ARTICLE_HANDOFF_DEFAULTS.values())
    )
    if str(defaults.get("writer_role") or "").strip()
} | set(WRITER_ROLE_DEFAULT_BY_SEMANTIC_KEY.values()) | {"企業担当者として語る"}
_THEME_LIKE_WRITER_ROLE_PATTERN = re.compile(
    r"(活用法|方法|とは|について|比較|ポイント|戦略|課題|テーマ|読者|するため|を維持|を高め|目的|記事構成)"
)
_CORPORATE_WRITER_ROLE_PATTERN = re.compile(
    r"(広報|運営|導入支援|ブランド|会社|企業|当社|弊社|代表|取締役|経営|人事|カルチャー)"
)
_PERSONAL_WRITER_ROLE_PATTERN = re.compile(
    r"(編集|筆者|解説|専門家|講師|記者|アナリスト|コンサル|監修|現場)"
)


def _lookup_custom_genre(custom_genre_lookup: Optional[CustomGenreLookup], key: str) -> object:
    if custom_genre_lookup is None:
        return None
    try:
        return custom_genre_lookup(key)
    except Exception:
        return None


def _resolve_writer_role_option_key(
    article_type_key: str,
    *,
    custom_genre_lookup: Optional[CustomGenreLookup] = None,
) -> str:
    key = str(article_type_key or "").strip()
    legacy_aliases = {
        "ai": "explanatory_article",
        "company_introduction": "branding",
        "corporate_culture": "branding",
        "daily_happenings": "daily_story",
    }
    key = legacy_aliases.get(key, key)
    if key in WRITER_ROLE_OPTIONS_BY_ARTICLE_TYPE:
        return key
    custom_genre = _lookup_custom_genre(custom_genre_lookup, key)
    if isinstance(custom_genre, dict):
        meta = custom_genre.get("meta")
        if isinstance(meta, dict) and meta:
            base_template = str(meta.get("base_template", "")).strip().lower()
            if base_template == "ai":
                return "explanatory_article"
            if base_template in WRITER_ROLE_OPTIONS_BY_ARTICLE_TYPE:
                return base_template
    return "default"


def _get_writer_role_options(
    article_type_key: str,
    semantic_article_key: str = "",
    *,
    custom_genre_lookup: Optional[CustomGenreLookup] = None,
) -> List[str]:
    semantic_key = str(semantic_article_key or "").strip()
    semantic_options = WRITER_ROLE_OPTIONS_BY_SEMANTIC_KEY.get(semantic_key)
    if semantic_options:
        options = semantic_options
    else:
        key = _resolve_writer_role_option_key(article_type_key, custom_genre_lookup=custom_genre_lookup)
        options = WRITER_ROLE_OPTIONS_BY_ARTICLE_TYPE.get(key) or WRITER_ROLE_OPTIONS_BY_ARTICLE_TYPE["default"]
    unique_options: List[str] = []
    for item in options:
        text = str(item or "").strip()
        if not text or text in unique_options:
            continue
        unique_options.append(text)
    return unique_options[:4]


def _get_default_writer_role_label(
    article_type_key: str,
    semantic_article_key: str = "",
    *,
    custom_genre_lookup: Optional[CustomGenreLookup] = None,
) -> str:
    options = _get_writer_role_options(
        article_type_key,
        semantic_article_key,
        custom_genre_lookup=custom_genre_lookup,
    )
    semantic_default = WRITER_ROLE_DEFAULT_BY_SEMANTIC_KEY.get(str(semantic_article_key or "").strip())
    if semantic_default in options:
        return semantic_default
    for option in options:
        if option != WRITER_ROLE_AUTO_LABEL:
            return option
    return options[0] if options else WRITER_ROLE_AUTO_LABEL


def _is_article_type_managed_writer_role_label(label: str) -> bool:
    text = str(label or "").strip()
    return bool(text and text in WRITER_ROLE_ARTICLE_TYPE_MANAGED_DEFAULT_LABELS)


def _writer_role_label_to_profile(label: str) -> str:
    text = str(label or "").strip()
    if not text or text in {WRITER_ROLE_AUTO_LABEL, WRITER_ROLE_COMPANY_INTRO_NEUTRAL_LABEL}:
        return ""
    return text[:80]


def _resolve_article_type_handoff_defaults(article_type_key: str, semantic_article_key: str = "") -> Dict[str, str]:
    article_key = str(article_type_key or "").strip()
    semantic_key = str(semantic_article_key or "").strip()
    defaults = dict(ARTICLE_TYPE_HANDOFF_DEFAULTS.get(article_key) or ARTICLE_TYPE_HANDOFF_DEFAULTS["default"])
    semantic_defaults = SEMANTIC_ARTICLE_HANDOFF_DEFAULTS.get(semantic_key)
    if semantic_defaults:
        defaults.update(semantic_defaults)
    return defaults


def _resolve_defaulted_handoff_value(
    selected_key: str,
    *,
    defaults: Mapping[str, str],
    field: str,
    auto_value: str = "auto",
) -> str:
    normalized = str(selected_key or auto_value).strip() or auto_value
    if normalized != auto_value:
        return normalized
    return str(defaults.get(field) or auto_value).strip() or auto_value


def _resolve_article_type_handoff_settings(
    *,
    article_type_key: str,
    semantic_article_key: str = "",
    writing_focus_key: str = "auto",
    perspective_key: str = "auto",
    self_reference_policy_key: str = "auto",
    writer_role_text: str = "",
) -> Dict[str, str]:
    defaults = _resolve_article_type_handoff_defaults(article_type_key, semantic_article_key)
    resolved_writer_role = str(writer_role_text or "").strip()
    if not resolved_writer_role:
        resolved_writer_role = str(defaults.get("writer_role") or "").strip()
    return {
        "writer_role": resolved_writer_role[:80],
        "perspective": _resolve_defaulted_handoff_value(perspective_key, defaults=defaults, field="perspective"),
        "writing_focus": _resolve_defaulted_handoff_value(writing_focus_key, defaults=defaults, field="writing_focus"),
        "self_reference_policy": _resolve_defaulted_handoff_value(
            self_reference_policy_key,
            defaults=defaults,
            field="self_reference_policy",
        ),
    }


def _resolve_writer_role_auto_profile(
    article_type_key: str,
    semantic_article_key: str = "",
    *,
    custom_genre_lookup: Optional[CustomGenreLookup] = None,
) -> str:
    semantic_key = str(semantic_article_key or "").strip()
    default = _resolve_article_type_handoff_defaults(article_type_key, semantic_key)
    default_role = str(default.get("writer_role") or "").strip()
    if default_role:
        return default_role
    fallback_label = _get_default_writer_role_label(
        article_type_key,
        semantic_key,
        custom_genre_lookup=custom_genre_lookup,
    )
    return _writer_role_label_to_profile(fallback_label)


def _looks_theme_like_writer_role(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    return bool(_THEME_LIKE_WRITER_ROLE_PATTERN.search(text))


def _predict_pronoun_hint(
    article_type_key: str,
    writer_role_text: str,
    self_reference_policy_key: str = "auto",
    *,
    custom_genre_lookup: Optional[CustomGenreLookup] = None,
) -> str:
    explicit_hint = _describe_self_reference_hint(self_reference_policy_key)
    if explicit_hint:
        return explicit_hint
    role_text = str(writer_role_text or "").strip()
    if role_text:
        if _CORPORATE_WRITER_ROLE_PATTERN.search(role_text):
            return "推奨一人称: 私たち / 当社"
        if _PERSONAL_WRITER_ROLE_PATTERN.search(role_text):
            return "推奨一人称: 私"

    key = _resolve_writer_role_option_key(article_type_key, custom_genre_lookup=custom_genre_lookup)
    if key in {"explanatory_article", "industry_analysis", "comparative_review"}:
        return "推奨一人称: 私"
    if key in {"announcement", "branding", "case_study", "daily_story"}:
        return "推奨一人称: 私たち / 当社"
    return "推奨一人称: 自動判定"


def _describe_self_reference_hint(policy_key: str) -> str:
    key = str(policy_key or "").strip().lower()
    if key == "watashi":
        return "自己参照: 『私』を優先（必要な箇所だけ）"
    if key == "watashitachi":
        return "自己参照: 『私たち』を優先（必要な箇所だけ）"
    if key == "tousha":
        return "自己参照: 『当社』を優先（必要な箇所だけ）"
    if key == "heisha":
        return "自己参照: 『弊社』を優先（必要な箇所だけ）"
    if key == "minimal":
        return "自己参照: 一人称をなるべく使わない"
    return ""
