from __future__ import annotations

import re
from typing import Any

from app.services.draft_followthrough import append_paragraphs_to_h2_sections, body_chars_excluding_headings
from app.services.company_intro_live_buffer import (
    company_intro_live_buffer_paragraphs,
    live_residual_buffer_chars,
)


def company_intro_selected_excerpt_floor_followthrough(
    draft: str,
    article_brief: dict[str, Any],
    selected_source_excerpts: list[dict[str, Any]] | None,
    knowledge_pack: dict[str, Any] | None = None,
) -> str:
    brief = article_brief.get("article_brief", {}) if isinstance(article_brief, dict) else {}
    floor_chars = int(brief.get("body_length_floor_chars") or 0)
    if (
        str(brief.get("genre_id") or "") != "company_service_intro"
        or str(brief.get("voice_mode") or "") != "self_authored_blogger"
        or not selected_source_excerpts
        or floor_chars <= 0
    ):
        return draft
    current_chars = body_chars_excluding_headings(draft)
    if current_chars >= floor_chars:
        return draft
    target_chars = floor_chars + live_residual_buffer_chars(floor_chars)

    headings = {str(s.get("section_id")): str(s.get("heading")) for s in brief.get("sections") or [] if isinstance(s, dict)}
    paragraphs: dict[str, list[str]] = {}
    existing = "".join(draft.split())
    last_heading = ""
    for excerpt in selected_source_excerpts:
        section_id = str((excerpt.get("section_ids") or [""])[0])
        heading = headings.get(section_id)
        if not heading:
            continue
        last_heading = heading
        for paragraph in _excerpt_company_intro_paragraphs(str(excerpt.get("text") or ""), brief, existing):
            paragraphs.setdefault(heading, []).append(paragraph)
            existing += "".join(paragraph.split())
            current_chars += body_chars_excluding_headings(paragraph)
            if current_chars >= target_chars:
                break
        if current_chars >= target_chars:
            break

    claim_heading = last_heading or next(iter(headings.values()), "")
    if current_chars < target_chars and claim_heading:
        for paragraph in _company_intro_claim_paragraphs(brief, knowledge_pack, existing):
            paragraphs.setdefault(claim_heading, []).append(paragraph)
            existing += "".join(paragraph.split())
            current_chars += body_chars_excluding_headings(paragraph)
            if current_chars >= target_chars:
                break

    if current_chars < target_chars and claim_heading:
        for paragraph in company_intro_live_buffer_paragraphs(brief, knowledge_pack, existing):
            paragraphs.setdefault(claim_heading, []).append(paragraph)
            existing += "".join(paragraph.split())
            current_chars += body_chars_excluding_headings(paragraph)
            if current_chars >= target_chars:
                break

    if not paragraphs:
        return draft
    return append_paragraphs_to_h2_sections(draft, paragraphs)

def _excerpt_company_intro_paragraphs(text: str, brief: dict[str, Any], existing: str) -> list[str]:
    paragraphs: list[str] = []
    for raw_line in text.replace("\r\n", "\n").replace("。", "。\n").splitlines():
        line = raw_line.strip(" \t.。…")
        if not _is_usable_company_intro_line(line):
            continue
        paragraph = _company_intro_self_voice(line, brief)
        compact = "".join(paragraph.split())
        if len(compact) < 24 or compact in existing:
            continue
        paragraphs.append(paragraph if paragraph.endswith(("。", "．", ".")) else paragraph + "。")
    return paragraphs[:10]


def _company_intro_claim_paragraphs(
    brief: dict[str, Any],
    knowledge_pack: dict[str, Any] | None,
    existing: str,
) -> list[str]:
    pack = knowledge_pack.get("article_knowledge_pack", {}) if isinstance(knowledge_pack, dict) else {}
    facts = pack.get("confirmed_facts") if isinstance(pack, dict) else []
    if not isinstance(facts, list):
        return []
    assigned_ids = _brief_assigned_claim_ids(brief)
    ordered_ids = assigned_ids + [str(f.get("claim_id")) for f in facts if isinstance(f, dict) and str(f.get("claim_id")) not in assigned_ids]
    fact_by_id = {str(f.get("claim_id")): f for f in facts if isinstance(f, dict)}
    paragraphs: list[str] = []
    seen: set[str] = set()
    for claim_id in ordered_ids:
        fact = fact_by_id.get(claim_id)
        if not fact:
            continue
        raw_claim = str(fact.get("preferred_expression") or fact.get("claim") or "")
        short_residual = claim_id not in assigned_ids and _is_short_residual_table_claim(raw_claim)
        if not _is_usable_company_intro_line(raw_claim) and not short_residual:
            continue
        paragraph = (
            _company_intro_short_residual_voice(raw_claim, brief)
            if short_residual
            else _company_intro_self_voice(raw_claim, brief)
        )
        if claim_id not in assigned_ids and not (
            _is_useful_unassigned_company_claim(paragraph)
            or _is_residual_table_company_claim(paragraph)
        ):
            continue
        compact = "".join(paragraph.split())
        if compact in existing or compact in seen:
            continue
        paragraphs.append(paragraph if paragraph.endswith(("。", "．", ".")) else paragraph + "。")
        seen.add(compact)
    max_paragraphs = max(10, min(len(facts), len(assigned_ids) + 8))
    return paragraphs[:max_paragraphs]


def _brief_assigned_claim_ids(brief: dict[str, Any]) -> list[str]:
    claim_ids: list[str] = []
    for allocation in brief.get("claim_allocation") or []:
        if isinstance(allocation, dict):
            claim_ids.extend(str(claim_id) for claim_id in allocation.get("claim_ids") or [] if claim_id)
    if claim_ids:
        return claim_ids
    for section in brief.get("sections") or []:
        if isinstance(section, dict):
            claim_ids.extend(str(claim_id) for claim_id in section.get("assigned_claim_ids") or [] if claim_id)
    return claim_ids


def _company_intro_self_voice(text: str, brief: dict[str, Any]) -> str:
    sentence = text.strip(" \t.。…")
    narrator = str(brief.get("narrator") or "私たち")
    owner = str(brief.get("self_viewpoint_owner") or "").strip()
    if owner:
        sentence = re.sub(rf"^{re.escape(owner)}(?:では|は|が)", f"{narrator}は", sentence)
    sentence = re.sub(r"^(当社|弊社)(?:では|は|が)", f"{narrator}は", sentence)
    sentence = re.sub(r"^(私たち)(?:では|は|が)", f"{narrator}は", sentence)
    sentence = re.sub(r"^((?:株式会社|有限会社|合同会社)[^、。]{1,40}|[^、。]{1,30}(?:株式会社|有限会社|合同会社))(?:では|は|が)", f"{narrator}は", sentence)
    if not sentence.startswith(narrator):
        sentence = f"{narrator}は、{sentence}"
    return sentence


def _is_usable_company_intro_line(line: str) -> bool:
    compact = "".join(line.split()).strip("。")
    if len(compact) < 10:
        return False
    blocked_prefixes = (
        "http://",
        "https://",
        "現在位置",
        "ホーム",
        "Copyright",
        "COPYRIGHT",
        "資料",
        "関連情報",
        "シェア",
        "お問い合わせ",
        "CTA",
        "参考",
        "補助メモ",
    )
    if line.startswith(blocked_prefixes) or _mostly_spaced_ascii(line):
        return False
    blocked_exact = {"会社概要", "事業内容", "製品情報", "サービス", "採用情報", "お知らせ"}
    return compact not in blocked_exact


def _is_useful_unassigned_company_claim(paragraph: str) -> bool:
    return any(
        term in paragraph
        for term in (
            "提供",
            "運営",
            "製造",
            "販売",
            "サービス",
            "商品",
            "理念",
            "地域",
            "歴史",
            "創業",
            "展示",
            "事業",
            "技術",
            "対応",
            "支援",
        )
    )


def _is_residual_table_company_claim(paragraph: str) -> bool:
    return any(
        term in paragraph
        for term in (
            "譁咎≡",
            "繝励Λ繝ｳ",
            "繧ｳ繝ｼ繧ｹ",
            "繝・・繧ｿ",
            "繝・・繧ｿ繝吶・繧ｹ",
            "繧ｳ繝溘Η繝九こ繝ｼ繧ｷ繝ｧ繝ｳ",
            "AI",
            "データ",
            "コミュニケーション",
            "プラン",
            "コース",
            "料金",
            "初期費用",
            "情報",
            "業務",
        )
    )


def _is_short_residual_table_claim(text: str) -> bool:
    compact = "".join(text.split()).strip("。")
    return 4 <= len(compact) < 24 and any(term in compact for term in ("コース", "ユーザー", "プラン"))


def _company_intro_short_residual_voice(text: str, brief: dict[str, Any]) -> str:
    narrator = str(brief.get("narrator") or "私たち")
    fragment = text.strip(" \t.。…")
    return f"{narrator}は、確認材料として{fragment}という情報も示しています"


def _mostly_spaced_ascii(text: str) -> bool:
    letters = sum(1 for char in text if char.isascii() and char.isalpha())
    spaces = sum(1 for char in text if char == " ")
    return letters >= 12 and spaces >= max(6, letters // 2)
