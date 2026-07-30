from __future__ import annotations

import re
from typing import Any


def live_residual_buffer_chars(floor_chars: int) -> int:
    return min(180, max(96, floor_chars // 10))


def company_intro_live_buffer_paragraphs(
    brief: dict[str, Any],
    knowledge_pack: dict[str, Any] | None,
    existing: str,
) -> list[str]:
    facts = _confirmed_fact_texts(knowledge_pack)
    if not facts:
        return []
    narrator = str(brief.get("narrator") or "私たち")
    candidates = [
        _compose_buffer_paragraph(
            narrator,
            facts,
            primary_terms=("アプリ", "業務", "ノーコード", "AI"),
            secondary_terms=("データベース機能", "コミュニケーション機能", "プロセス管理機能", "情報"),
            bridge="業務に必要な情報をまとめる場面まで扱っています",
        ),
        _compose_buffer_paragraph(
            narrator,
            facts,
            primary_terms=("コース", "プラン", "料金"),
            secondary_terms=("初期費用", "1か月", "契約", "ユーザー"),
            bridge="利用規模や目的を確認する材料として示しています",
        ),
    ]
    paragraphs: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        compact = "".join(candidate.split())
        if not candidate or compact in existing or compact in seen:
            continue
        paragraphs.append(candidate)
        seen.add(compact)
    return paragraphs[:2]


def _confirmed_fact_texts(knowledge_pack: dict[str, Any] | None) -> list[str]:
    pack = knowledge_pack.get("article_knowledge_pack", {}) if isinstance(knowledge_pack, dict) else {}
    facts = pack.get("confirmed_facts") if isinstance(pack, dict) else []
    if not isinstance(facts, list):
        return []
    texts: list[str] = []
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        text = str(fact.get("preferred_expression") or fact.get("claim") or "").strip(" \t.。…")
        if text and _is_usable_company_intro_fact(text):
            texts.append(text)
    return texts


def _compose_buffer_paragraph(
    narrator: str,
    facts: list[str],
    *,
    primary_terms: tuple[str, ...],
    secondary_terms: tuple[str, ...],
    bridge: str,
) -> str:
    primary = _first_fact_with_terms(facts, primary_terms)
    secondary = _first_fact_with_terms(facts, secondary_terms, exclude=primary)
    if not primary or not secondary:
        return ""
    return f"{narrator}は、{_strip_company_subject(primary)}ことに加えて、{_strip_company_subject(secondary)}点も、{bridge}。"


def _first_fact_with_terms(facts: list[str], terms: tuple[str, ...], *, exclude: str = "") -> str:
    for fact in facts:
        if fact == exclude:
            continue
        if any(term in fact for term in terms):
            return fact
    return ""


def _strip_company_subject(text: str) -> str:
    sentence = text.strip(" \t.。…")
    sentence = re.sub(r"^(当社|弊社|私たち)(?:では|は|が|を)?", "", sentence)
    sentence = re.sub(r"^((?:株式会社|有限会社|合同会社)[^、。]{1,40}|[^、。]{1,30}(?:株式会社|有限会社|合同会社))(?:では|は|が)", "", sentence)
    return sentence.strip(" \t、")


def _is_usable_company_intro_fact(text: str) -> bool:
    compact = "".join(text.split()).strip("。")
    if len(compact) < 10:
        return False
    return not text.startswith(("http://", "https://", "Copyright", "COPYRIGHT", "現在位置", "ホーム"))
