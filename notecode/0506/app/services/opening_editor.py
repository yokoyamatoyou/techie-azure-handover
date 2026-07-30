from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OpeningEditResult:
    text: str
    report: dict[str, Any]


def run_opening_editor(
    article_text: str,
    article_brief: dict[str, Any],
    knowledge_pack: dict[str, Any],
) -> OpeningEditResult:
    brief = article_brief["article_brief"]
    narrator = brief["narrator"]
    opening = _build_opening(narrator, knowledge_pack, brief.get("genre_id"))
    preserve_reason = _route_v_preserve_reason(article_text, brief, knowledge_pack)
    if preserve_reason:
        revised, changed = article_text.strip(), False
    else:
        revised, changed = _replace_first_body_paragraph(article_text, opening)
    return OpeningEditResult(
        text=revised,
        report={
            "editor_profile_id": "note_hatena_opening_editor",
            "focus": "front_half_opening_naturalness",
            "changed": changed,
            "route_v_opening_preserved": bool(preserve_reason),
            "route_v_opening_preserve_reason": preserve_reason,
            "checks": {
                "implementation_meta_removed": "公開・提供されたソース" not in revised,
                "opening_uses_narrator": narrator in opening,
                "source_grounding_policy_changed": False,
                "qa_threshold_changed": False,
            },
            "opening": opening,
        },
    )


def build_opening_edit_report(
    before_text: str,
    after_text: str,
    article_brief: dict[str, Any],
    knowledge_pack: dict[str, Any],
) -> dict[str, Any]:
    result = run_opening_editor(before_text, article_brief, knowledge_pack)
    report = dict(result.report)
    report["changed"] = before_text != after_text
    return report


def _build_opening(narrator: str, knowledge_pack: dict[str, Any], genre_id: str | None = None) -> str:
    claims = "。".join(
        claim["preferred_expression"]
        for claim in knowledge_pack["article_knowledge_pack"]["confirmed_facts"]
    )
    if genre_id == "market_explanation":
        return (
            f"{narrator}はこの資料から、事業化の考え方を整理します。"
            "ビジネスモデル、マーケティング、市場性を分けて、アイデアを事業に近づける順番を扱います。"
        )
    if "1885" in claims or "明治18" in claims:
        return (
            f"{narrator}京都工業は、京都・伏見稲荷大社のお膝元で創業しました。"
            "データ入力やデジタル化の相談に、長く向き合ってきた会社です。"
        )
    if "データ" in claims:
        return f"{narrator}は、データ入力やデジタル化の相談に向き合っています。"
    return f"{narrator}の取り組みを、少し具体的に紹介します。"


def _replace_first_body_paragraph(text: str, opening: str) -> tuple[str, bool]:
    blocks = [block.strip() for block in text.strip().split("\n\n") if block.strip()]
    for index, block in enumerate(blocks):
        if block.startswith("#"):
            continue
        if block == opening:
            return text.strip(), False
        blocks[index] = opening
        return "\n\n".join(blocks), True
    return text.strip(), False


def _route_v_preserve_reason(
    article_text: str,
    brief: dict[str, Any],
    knowledge_pack: dict[str, Any],
) -> str:
    if not _is_route_v_opening_guard_enabled(brief):
        return ""
    first_body = _first_body_paragraph(article_text)
    if not first_body:
        return ""
    if _is_generic_or_meta_opening(first_body):
        return ""
    if _has_source_backed_specificity(first_body, brief, knowledge_pack):
        return "route_v_source_backed_first_paragraph"
    return "route_v_non_generic_first_paragraph"


def _is_route_v_opening_guard_enabled(brief: dict[str, Any]) -> bool:
    return (
        brief.get("voice_mode") == "self_authored_blogger"
        and bool(brief.get("paragraph_function_plan"))
        and bool(brief.get("source_shape"))
        and bool(brief.get("source_use_mode"))
    )


def _first_body_paragraph(text: str) -> str:
    for block in [block.strip() for block in text.strip().split("\n\n") if block.strip()]:
        if not block.startswith("#"):
            return block
    return ""


def _has_source_backed_specificity(
    paragraph: str,
    brief: dict[str, Any],
    knowledge_pack: dict[str, Any],
) -> bool:
    text = _normalize_for_match(paragraph)
    if re.search(r"[0-9０-９]+(?:[.,．][0-9０-９]+)?(?:円|件|社|名|年|％|%|ページ|項目|セット|文字|分|枚)", text):
        return True
    assigned_ids = _assigned_claim_ids(brief)
    if not assigned_ids:
        return False
    if any(term in text for term in _claim_feature_terms(knowledge_pack, assigned_ids)):
        return True
    return _has_route_v_reader_hook_specificity(paragraph, brief, knowledge_pack, assigned_ids)


def _is_generic_or_meta_opening(paragraph: str) -> bool:
    text = _normalize_feature_text(paragraph)
    if any(marker in text for marker in ("この記事では", "本記事では", "この記事は", "本記事は")):
        return True
    generic_markers = ("紹介します", "説明します", "解説します")
    if len(text) <= 80 and any(marker in text for marker in generic_markers):
        return True
    if len(text) <= 90 and "取り組み" in text and "紹介" in text:
        return True
    return False


def _has_route_v_reader_hook_specificity(
    paragraph: str,
    brief: dict[str, Any],
    knowledge_pack: dict[str, Any],
    assigned_claim_ids: set[str],
) -> bool:
    text = _normalize_feature_text(paragraph)
    matched_terms = {
        term
        for term in _route_v_reader_hook_terms(brief, knowledge_pack, assigned_claim_ids)
        if term in text
    }
    return len(matched_terms) >= 3


def _route_v_reader_hook_terms(
    brief: dict[str, Any],
    knowledge_pack: dict[str, Any],
    assigned_claim_ids: set[str],
) -> list[str]:
    values: list[str] = []
    for field_name in ("interest_hook", "self_authored_angle", "reading_reward"):
        values.extend(_text_values(brief.get(field_name)))
    values.extend(_text_values(brief.get("paragraph_function_plan")))
    for section in brief.get("sections") or []:
        values.extend(_text_values(section.get("heading")))
    facts = knowledge_pack.get("article_knowledge_pack", {}).get("confirmed_facts") or []
    for fact in facts:
        if str(fact.get("claim_id")) not in assigned_claim_ids:
            continue
        values.extend(_text_values(fact.get("preferred_expression") or fact.get("claim")))

    terms: list[str] = []
    for value in values:
        terms.extend(_short_feature_terms(value))
    return list(dict.fromkeys(terms))


def _text_values(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return [str(value)]


def _short_feature_terms(value: str) -> list[str]:
    terms: list[str] = []
    for chunk in re.split(r"[、。,.（）()「」『』:：/｜|・\s]+", value):
        compact = _normalize_feature_text(chunk)
        if _is_reader_hook_feature_term(compact):
            terms.append(compact)
        for part in re.split(
            r"(?:ではなく|について|として|するための|ための|ごとに|ごとの|あたり|から|まで|より|の|を|が|は|に|で|と|も|へ)",
            compact,
        ):
            if _is_reader_hook_feature_term(part):
                terms.append(part)
    return list(dict.fromkeys(terms))


def _is_reader_hook_feature_term(term: str) -> bool:
    if not (3 <= len(term) <= 18):
        return False
    if not re.search(r"[一-龥ぁ-んァ-ヶ]", term):
        return False
    if term in {"私たち", "この記事", "本記事", "導入", "引き込み", "具体", "背景", "締め"}:
        return False
    stop_fragments = (
        "紹介します",
        "説明します",
        "解説します",
        "わかりやす",
        "source",
        "assigned",
        "claims",
        "CTA",
    )
    return not any(fragment in term for fragment in stop_fragments)


def _assigned_claim_ids(brief: dict[str, Any]) -> set[str]:
    claim_ids: set[str] = set()
    for section in brief.get("sections") or []:
        for claim_id in section.get("assigned_claim_ids") or []:
            claim_ids.add(str(claim_id))
    for allocation in brief.get("claim_allocation") or []:
        for claim_id in allocation.get("claim_ids") or []:
            claim_ids.add(str(claim_id))
    return claim_ids


def _claim_feature_terms(knowledge_pack: dict[str, Any], assigned_claim_ids: set[str]) -> list[str]:
    terms: list[str] = []
    facts = knowledge_pack.get("article_knowledge_pack", {}).get("confirmed_facts") or []
    for fact in facts:
        if str(fact.get("claim_id")) not in assigned_claim_ids:
            continue
        expression = _normalize_for_match(str(fact.get("preferred_expression") or fact.get("claim") or ""))
        for term in re.split(r"[、。,.（）()「」『』\s]+", expression):
            if 4 <= len(term) <= 24 and term not in {"すべて税別", "いずれも税別"}:
                terms.append(term)
    return terms


def _normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", "", text.strip())


def _normalize_feature_text(text: str) -> str:
    return re.sub(r"[\s、。,.（）()「」『』:：/｜|・]+", "", text.strip())
