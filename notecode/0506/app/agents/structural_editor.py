from __future__ import annotations

from typing import Any

from app.services.llm_client import LLMClient
from app.services.editor_stage_instructions import build_editor_stage_instructions


BASE_INSTRUCTIONS = (
    "Return only the complete edited Markdown article. Improve late-half structure and consistency while preserving facts, names, dates, numbers, and source grounding. Do not explain."
)

DAILY_ACTIVITY_SCENE_CATEGORIES = {
    "time": ("日", "時", "午前", "午後", "開催", "年度", "月"),
    "place": ("室", "会場", "センター", "教室", "園庭", "体育館", "地域"),
    "object_tool": ("ライト", "紙", "ペーパー", "商品", "道具", "瓶", "金属", "カメラ", "資材"),
    "action": ("準備", "置", "照ら", "撮", "確認", "説明", "聞", "実技", "実習", "学"),
    "sequence": ("講義", "実技", "二部構成", "順番", "から", "へ"),
    "constraint": ("定員", "参加費", "対象", "持ち物", "時間", "日時", "受講料"),
}


class StructuralEditor:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def edit(self, article_text: str, article_brief: dict[str, Any], knowledge_pack: dict[str, Any]) -> str:
        instructions = build_editor_stage_instructions("structural_editor", BASE_INSTRUCTIONS, article_brief)
        return self.client.generate_text(
            "structural_editor",
            instructions,
            {
                "article_text": article_text,
                "article_brief": article_brief,
                "knowledge_pack": build_structural_editor_knowledge_context(article_brief, knowledge_pack),
            },
        )


def build_structural_editor_knowledge_context(article_brief: dict[str, Any], knowledge_pack: dict[str, Any]) -> dict[str, Any]:
    pack = knowledge_pack.get("article_knowledge_pack", {})
    facts = list(pack.get("confirmed_facts", []))
    brief = article_brief.get("article_brief", {})
    sections = brief.get("sections", [])
    assigned_ids = {
        claim_id
        for section in sections
        for claim_id in section.get("assigned_claim_ids", [])
        if isinstance(claim_id, str)
    }
    visible_facts = [fact for fact in facts if not assigned_ids or fact.get("claim_id") in assigned_ids]
    context = {
        "article_knowledge_pack": {
            "confirmed_facts": visible_facts,
            "source_card_ids": list(pack.get("source_card_ids", [])),
            "do_not_infer": list(pack.get("do_not_infer", [])),
        },
        "section_claim_material": [
            {
                "section_id": section.get("section_id"),
                "heading": section.get("heading"),
                "purpose": section.get("purpose"),
                "assigned_claim_ids": list(section.get("assigned_claim_ids", [])),
            }
            for section in sections
        ],
    }
    scene_contract = _daily_activity_scene_material_preservation_contract(brief, facts)
    if scene_contract:
        context["scene_material_preservation"] = scene_contract
    return context


def _daily_activity_scene_material_preservation_contract(
    brief: dict[str, Any],
    facts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if brief.get("genre_id") != "daily_activity":
        return None
    matched = _classify_scene_material(facts)
    return {
        "applies_to": "daily_activity_structural_editor",
        "instruction": "Preserve source-near scene material during structural editing; do not compress the article into announcement/list guidance.",
        "preserve_categories": ["time", "place", "object_tool", "action", "sequence", "constraint"],
        "minimum_categories_to_keep_when_present": 4,
        "unsupported_additions_disallowed": ["emotion", "result", "participant_reaction", "atmosphere", "numeric_claim"],
        "notice_list_drift_disallowed": True,
        "matched_source_near_material": matched,
    }


def _classify_scene_material(facts: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    matched: dict[str, list[dict[str, str]]] = {category: [] for category in DAILY_ACTIVITY_SCENE_CATEGORIES}
    for fact in facts:
        claim_id = str(fact.get("claim_id") or "").strip()
        text = str(fact.get("preferred_expression") or fact.get("claim") or "").strip()
        if not claim_id or not text:
            continue
        compact = text[:120]
        for category, markers in DAILY_ACTIVITY_SCENE_CATEGORIES.items():
            if len(matched[category]) >= 4:
                continue
            if any(marker in text for marker in markers):
                matched[category].append({"claim_id": claim_id, "text": compact})
    return {category: items for category, items in matched.items() if items}
