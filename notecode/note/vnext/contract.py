"""Thin contract resolution for vNext."""
from __future__ import annotations

import re
from typing import Any, Mapping

from .source import (
    build_canonical_documents_from_current_contract,
    build_fact_cards_from_current_contract,
    build_source_context_summary,
)
from .types import VNextThinContract

VNEXT_THIN_CONTRACT_MUST_FIELDS = (
    "article_type",
    "semantic_subtype",
    "discourse_mode",
    "evidence_style",
    "emotion_level",
    "speaker_profile",
    "audience_profile",
    "prompt_raw",
    "topic_statement",
    "length_mode",
    "allow_experience",
    "relationship_mode",
    "comparison_axes",
    "canonical_documents",
    "fact_cards",
    "preservation_policy",
    "ui_signal_trace",
)

VNEXT_THIN_CONTRACT_OPTIONAL_FIELDS = (
    "core_message",
    "content_goal",
    "writing_focus",
    "tone_profile",
    "source_context_summary",
    "mode_resolution_evidence",
)


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _normalize_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _resolve_topic_statement(contract: Mapping[str, Any]) -> str:
    for key in ("topic_statement", "core_message", "topic", "prompt_raw"):
        value = _normalize_text(contract.get(key) or "")
        if value:
            return value
    return "テーマを整理する"


def _resolve_preservation_policy(article_type: str) -> str:
    return "high_preservation" if article_type == "announcement" else "normal"


def _resolve_discourse_mode(article_type: str, semantic_subtype: str, contract: Mapping[str, Any], fact_card_count: int) -> tuple[str, str]:
    prompt_raw = _normalize_text(contract.get("prompt_raw") or contract.get("topic") or "")
    speaker_profile = _normalize_text(contract.get("speaker_profile") or "")
    if article_type == "announcement":
        if re.search(r"(停止|メンテナンス|保守)", prompt_raw):
            return "maintenance_notice", "prompt_signal"
        if re.search(r"(規約|料金|方針|ポリシー)", prompt_raw):
            return "policy_change_notice", "prompt_signal"
        if re.search(r"(新機能|リリース|公開|提供開始)", prompt_raw):
            return "release_note", "prompt_signal"
        return "standard_notice", "article_default"
    if article_type == "branding":
        if re.search(r"(代表|創業|founder|CEO|社長)", speaker_profile, re.IGNORECASE):
            return "founder_voice", "speaker_profile"
        if re.search(r"(場面|現場|きっかけ|背景|エピソード|ストーリー)", prompt_raw) and fact_card_count > 0:
            return "story_driven", "prompt_plus_source"
        if semantic_subtype in {"company_introduction", "product_introduction", "activity_introduction", "recruit_culture"}:
            return "fact_profile", "semantic_subtype"
        if re.search(r"(課題|悩み|困りごと|必要性|価値)", prompt_raw):
            return "problem_value", "prompt_signal"
        return "fact_profile", "article_default"
    if article_type == "daily_story":
        if re.search(r"(学び|気づき|振り返り)", prompt_raw):
            return "event_then_learning", "prompt_signal"
        return "observation_reflection", "article_default"
    if article_type == "explanatory_article":
        if re.search(r"(解決|対策|改善|手順)", prompt_raw):
            return "problem_solution", "prompt_signal"
        return "concept_breakdown", "article_default"
    if article_type == "case_study":
        if semantic_subtype in {"implementation_case", "improvement_case", "incident_case"}:
            return semantic_subtype, "semantic_subtype"
        return "implementation_case", "article_default"
    if article_type == "comparative_review":
        if re.search(r"(用途|向いて|向く|使い分け)", prompt_raw):
            return "usecase_first", "prompt_signal"
        return "criteria_first", "article_default"
    if article_type == "industry_analysis":
        if re.search(r"(トレンド|潮流|今後|示唆)", prompt_raw):
            return "trend_implication", "prompt_signal"
        return "structure_shift", "article_default"
    return article_type, "article_default"


def _resolve_evidence_style(article_type: str, discourse_mode: str, contract: Mapping[str, Any], fact_card_count: int) -> tuple[str, str]:
    prompt_raw = _normalize_text(contract.get("prompt_raw") or "")
    if article_type in {"announcement", "industry_analysis", "comparative_review"} and fact_card_count >= 2:
        return "fact_first", "article_policy"
    if article_type == "daily_story" or discourse_mode == "story_driven":
        return "story_first", "mode_policy"
    if bool(contract.get("allow_experience")) and re.search(r"(体験|経験|現場)", prompt_raw):
        return "story_first", "experience_signal"
    if fact_card_count >= 3:
        return "fact_first", "source_density"
    return "balanced", "article_default"


def _resolve_emotion_level(article_type: str, contract: Mapping[str, Any], preservation_policy: str) -> tuple[int, str]:
    base = {
        "announcement": 0,
        "industry_analysis": 1,
        "comparative_review": 1,
        "explanatory_article": 1,
        "branding": 2,
        "case_study": 2,
        "daily_story": 3,
    }.get(article_type, 1)
    tone_profile = _normalize_text(contract.get("tone_profile") or "auto", "auto")
    reason = "article_default"
    if tone_profile in {"formal", "calm"}:
        base = max(0, base - 1)
        reason = "tone_profile_cap"
    elif tone_profile == "warm":
        base = min(3, base + 1)
        reason = "tone_profile_boost"
    if preservation_policy == "high_preservation":
        base = min(base, 1)
        reason = "preservation_policy"
    return base, reason


def build_vnext_thin_contract(current_contract: Mapping[str, Any]) -> VNextThinContract:
    article_type = _normalize_text(current_contract.get("article_type") or "explanatory_article")
    semantic_subtype = _normalize_text(current_contract.get("semantic_article_key") or article_type)
    fact_cards = build_fact_cards_from_current_contract(current_contract)
    canonical_documents = build_canonical_documents_from_current_contract(current_contract, fact_cards)
    preservation_policy = _resolve_preservation_policy(article_type)
    discourse_mode, discourse_reason = _resolve_discourse_mode(
        article_type,
        semantic_subtype,
        current_contract,
        len(fact_cards),
    )
    evidence_style, evidence_reason = _resolve_evidence_style(
        article_type,
        discourse_mode,
        current_contract,
        len(fact_cards),
    )
    emotion_level, emotion_reason = _resolve_emotion_level(article_type, current_contract, preservation_policy)
    source_context_summary = build_source_context_summary(fact_cards, canonical_documents)
    return VNextThinContract(
        article_type=article_type,
        semantic_subtype=semantic_subtype,
        discourse_mode=discourse_mode,
        evidence_style=evidence_style,
        emotion_level=emotion_level,
        speaker_profile=_normalize_text(current_contract.get("speaker_profile") or "編集担当として語る"),
        audience_profile=_normalize_text(current_contract.get("audience_profile") or "一般読者"),
        prompt_raw=_normalize_text(current_contract.get("prompt_raw") or current_contract.get("topic") or ""),
        topic_statement=_resolve_topic_statement(current_contract),
        length_mode=_normalize_text(current_contract.get("length_mode") or "adaptive"),
        allow_experience=bool(current_contract.get("allow_experience", False)),
        relationship_mode=_normalize_text(current_contract.get("relationship_mode") or "guide", "guide"),
        comparison_axes=_normalize_list(current_contract.get("comparison_axes")),
        canonical_documents=canonical_documents,
        fact_cards=fact_cards,
        preservation_policy=preservation_policy,
        ui_signal_trace={
            "ui_journey": dict(current_contract.get("ui_journey") or {}),
            "content_goal": _normalize_text(current_contract.get("content_goal") or "auto", "auto"),
            "writing_focus": _normalize_text(current_contract.get("writing_focus") or "auto", "auto"),
            "tone_profile": _normalize_text(current_contract.get("tone_profile") or "auto", "auto"),
            "speaker_profile": _normalize_text(current_contract.get("speaker_profile") or ""),
            "audience_profile": _normalize_text(current_contract.get("audience_profile") or ""),
            "semantic_article_key": semantic_subtype,
        },
        core_message=_normalize_text(current_contract.get("core_message") or ""),
        content_goal=_normalize_text(current_contract.get("content_goal") or "auto", "auto"),
        writing_focus=_normalize_text(current_contract.get("writing_focus") or "auto", "auto"),
        tone_profile=_normalize_text(current_contract.get("tone_profile") or "auto", "auto"),
        source_context_summary=source_context_summary,
        mode_resolution_evidence={
            "discourse_mode_reason": discourse_reason,
            "evidence_style_reason": evidence_reason,
            "emotion_level_reason": emotion_reason,
            "fact_card_count": len(fact_cards),
            "document_count": len(canonical_documents),
        },
    )
