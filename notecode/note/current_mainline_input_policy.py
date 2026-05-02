"""Shared current mainline input normalization policies."""
from __future__ import annotations

import re
from typing import Tuple

_DEFAULT_SPEAKER_PROFILE_BY_ARTICLE_TYPE = {
    "explanatory_article": "編集担当として語る",
    "industry_analysis": "編集担当として語る",
    "comparative_review": "編集担当として語る",
    "branding": "企業広報として語る",
    "announcement": "広報担当として語る",
    "case_study": "導入支援担当として語る",
    "daily_story": "運営担当として語る",
}
_ROLE_HINT_PATTERN = re.compile(
    r"(担当|編集|運営|広報|導入支援|ブランド|専門家|アナリスト|比較検証|記者|講師|代表|取締役|経営|監修|筆者|現場)"
)
_THEME_LIKE_SPEAKER_PATTERN = re.compile(
    r"(活用法|方法|とは|について|比較|ポイント|戦略|課題|テーマ|読者|するため|を維持|を高め|目的|記事構成|事業内容|歴史|沿革|会社紹介)"
)
_ARTICLE_TASK_PATTERN = re.compile(
    r"(記事|投稿|書き方|紹介する|説明する|作成|生成|かいて|書いて|してください)"
)
_AUTO_SPEAKER_PROFILE_MARKERS = {
    "おすすめ",
    "自動判定",
    "自動（おすすめ）",
    "自動（役割語を前面に出さない）",
    "立場を前に出さない（おすすめ）",
}


def _normalize_auto_speaker_profile_marker(value: str) -> str:
    text = str(value or "").strip()
    if text in _AUTO_SPEAKER_PROFILE_MARKERS:
        return ""
    return text


def looks_theme_like_speaker_profile(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if _ROLE_HINT_PATTERN.search(text):
        return False
    if _THEME_LIKE_SPEAKER_PATTERN.search(text):
        return True
    return bool(
        _ARTICLE_TASK_PATTERN.search(text)
        and re.search(r"(自社|会社|事業内容|歴史|沿革|紹介|解説|比較)", text)
    )


def get_default_speaker_profile(article_type_key: str) -> str:
    key = str(article_type_key or "").strip()
    return _DEFAULT_SPEAKER_PROFILE_BY_ARTICLE_TYPE.get(key, "編集担当として語る")


def resolve_effective_speaker_profile(
    *,
    article_type_key: str,
    speaker_profile_input: str = "",
    interview_writer_role: str = "",
) -> Tuple[str, str]:
    explicit_value = _normalize_auto_speaker_profile_marker(speaker_profile_input)[:80]
    interview_value = _normalize_auto_speaker_profile_marker(interview_writer_role)[:80]

    if looks_theme_like_speaker_profile(explicit_value):
        explicit_value = ""
    if looks_theme_like_speaker_profile(interview_value):
        interview_value = ""

    if explicit_value:
        return explicit_value, "ui"
    if interview_value:
        return interview_value, "interview_answers"
    return get_default_speaker_profile(article_type_key), "ui_auto_default"
