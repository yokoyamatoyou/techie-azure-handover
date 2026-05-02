"""Compact writing-profile resolver for the simple note refactor."""

from __future__ import annotations

from typing import Any, Dict, Iterable

BRANDING_SUBTYPE_LABELS: Dict[str, str] = {
    "company": "会社紹介を中心にする",
    "product": "製品紹介を中心にする",
    "service": "サービス紹介を中心にする",
}
BRANDING_FOCUS_LABELS: Dict[str, str] = {
    "awareness_build": "まず知ってもらう",
    "difference_proof": "違いを伝える",
    "choice_criteria": "選ぶ基準を作る",
    "category_creation": "新しい見方を作る",
}
PATTERN_SELECT_LABELS: Dict[str, str] = {
    "auto": "自動（自由入力を優先）",
    "difference_first": "違いから入る",
    "scene_first": "場面から入る",
    "criteria_first": "判断軸から入る",
    "story_then_point": "体験から要点へ",
}

_GOAL_HINTS: Dict[str, str] = {
    "interest": "読者の興味が自然に続く導入を優先する。",
    "explain": "背景と要点の理解が進む順番を優先する。",
    "action": "読後に次の一歩が見える構成を優先する。",
    "trust": "断定を抑え、整合性と根拠の見え方を優先する。",
}
_BRANDING_FOCUS_HINTS: Dict[str, str] = {
    "awareness_build": "まず存在と利用場面を迷わず理解できる構成にする。",
    "difference_proof": "違いが伝わる比較軸と根拠を先に置く。",
    "choice_criteria": "選ぶ判断軸を整理し、読者が比較しやすい順番にする。",
    "category_creation": "既存の見方をずらし、新しい解釈の入口を作る。",
}
_PATTERN_HINTS: Dict[str, str] = {
    "difference_first": "冒頭で違いか変化点を置き、その後で理由を説明する。",
    "scene_first": "冒頭は場面や状況から入り、後段で意味を整理する。",
    "criteria_first": "冒頭で判断軸を置き、本文は軸ごとに前進させる。",
    "story_then_point": "短い体験や観察から入り、後で要点を明示する。",
}
_BRANDING_SUBTYPE_HINTS: Dict[str, str] = {
    "company": "会社紹介として、背景・提供価値・信頼材料を自然につなぐ。",
    "product": "製品紹介として、用途・違い・選定理由を具体化する。",
    "service": "サービス紹介として、利用場面・伴走価値・継続理由を具体化する。",
}
_SEMANTIC_ARTICLE_HINTS: Dict[str, str] = {
    "explanatory_article": "解説記事として、前提・要点・実務での使い方を順序立てる。",
    "industry_analysis": "業界や市場の話題として、動向の整理だけで終わらず判断材料までつなぐ。",
    "announcement": "お知らせとして、変更点・対象と時期・必要な行動を混線させない。",
    "implementation_case": "事例記事として、課題・対応・得られた変化を追いやすく並べる。",
    "improvement_case": "改善事例として、見直し前後の差と学びをわかりやすく整理する。",
    "incident_case": "共有が必要な事例として、経緯・影響・再発防止を落ち着いて整理する。",
    "learning_case": "学習用の事例として、状況・判断・学べる点を順番に示す。",
    "comparative_review": "比較記事として、違いの列挙だけでなく選び分け条件まで示す。",
    "daily_story": "日常のできごととして、出来事・気づき・共有したい意味を自然につなぐ。",
}
_QUESTION_POLICY_COPY_BY_ARTICLE_TYPE: Dict[str, str] = {
    "announcement": "追加質問: 告知に必要な不足項目だけを確認します。",
    "case_study": "追加質問: 事例成立に必要な入力不足だけを確認します。",
    "comparative_review": "追加質問: 比較条件の不足だけを確認します。",
}


def _normalize_choice(value: Any, allowed: Iterable[str], default: str) -> str:
    allowed_set = {str(item).strip() for item in allowed}
    normalized = str(value or "").strip()
    return normalized if normalized in allowed_set else default


def _dedupe_items(items: Iterable[Any], *, limit: int = 3) -> list[str]:
    normalized: list[str] = []
    for item in items:
        text = str(item or "").strip()
        if not text or text in normalized:
            continue
        normalized.append(text[:120])
        if len(normalized) >= limit:
            break
    return normalized


def _should_keep_generic_branding_semantic(
    *,
    semantic_key: str,
    branding_subtype_key: Any,
) -> bool:
    if semantic_key != "branding":
        return False
    if str(branding_subtype_key or "").strip():
        return False
    return True


def resolve_compact_writing_profile(
    *,
    article_type: str,
    semantic_article_key: str = "",
    content_goal_key: str = "auto",
    writing_focus_key: str = "auto",
    tone_profile_key: str = "auto",
    perspective_key: str = "auto",
    relationship_mode: str = "guide",
    branding_subtype_key: str = "",
    branding_focus_key: str = "",
    pattern_key: str = "auto",
    system_hint_items: Iterable[Any] | None = None,
) -> Dict[str, Any]:
    article_type_key = str(article_type or "").strip() or "explanatory_article"
    semantic_key = str(semantic_article_key or "").strip() or article_type_key
    subtype_key = _normalize_choice(branding_subtype_key, BRANDING_SUBTYPE_LABELS.keys(), "company")
    focus_key = _normalize_choice(branding_focus_key, BRANDING_FOCUS_LABELS.keys(), "awareness_build")
    pattern_select_key = _normalize_choice(pattern_key, PATTERN_SELECT_LABELS.keys(), "auto")
    base_hints = list(system_hint_items or [])

    if article_type_key == "branding":
        keep_generic_branding_semantic = _should_keep_generic_branding_semantic(
            semantic_key=semantic_key,
            branding_subtype_key=branding_subtype_key,
        )
        if semantic_key == "product_introduction" and not str(branding_subtype_key or "").strip():
            subtype_key = "product"
        if semantic_key not in {"company_introduction", "product_introduction", "activity_introduction", "recruit_culture"}:
            semantic_key = (
                "branding"
                if keep_generic_branding_semantic
                else "company_introduction" if subtype_key == "company" else "product_introduction"
            )
        if keep_generic_branding_semantic:
            subtype_key = ""
        base_hints.append(_BRANDING_SUBTYPE_HINTS.get(subtype_key, ""))
        base_hints.append(_BRANDING_FOCUS_HINTS.get(focus_key, ""))
    elif semantic_key in _SEMANTIC_ARTICLE_HINTS:
        base_hints.append(_SEMANTIC_ARTICLE_HINTS[semantic_key])
    if content_goal_key in _GOAL_HINTS:
        base_hints.append(_GOAL_HINTS[content_goal_key])
    if pattern_select_key in _PATTERN_HINTS:
        base_hints.append(_PATTERN_HINTS[pattern_select_key])

    unresolved_slot_fields = ["audience_profile", "core_message"]
    if article_type_key not in {"announcement"}:
        unresolved_slot_fields.insert(0, "speaker_profile")

    return {
        "article_type": article_type_key,
        "semantic_article_key": semantic_key,
        "content_goal_key": str(content_goal_key or "auto"),
        "writing_focus_key": str(writing_focus_key or "auto"),
        "tone_profile_key": str(tone_profile_key or "auto"),
        "perspective_key": str(perspective_key or "auto"),
        "relationship_mode": str(relationship_mode or "guide") or "guide",
        "branding_subtype_key": subtype_key if article_type_key == "branding" else "",
        "branding_focus_key": focus_key if article_type_key == "branding" else "",
        "pattern_key": pattern_select_key,
        "system_hint_items": _dedupe_items(base_hints),
        "unresolved_slot_fields": unresolved_slot_fields,
        "question_policy_copy": _QUESTION_POLICY_COPY_BY_ARTICLE_TYPE.get(
            article_type_key,
            (
                "追加質問: unresolved slot だけを確認します。"
                if article_type_key == "branding"
                else "追加質問: 必要な入力不足だけを確認します。"
            ),
        ),
    }
