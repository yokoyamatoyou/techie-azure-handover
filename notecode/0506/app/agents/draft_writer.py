from __future__ import annotations
from copy import deepcopy
from typing import Any
from app.services.llm_client import LLMClient
from app.services.announcement_followthrough import announcement_selected_excerpt_floor_followthrough
from app.services.company_intro_followthrough import company_intro_selected_excerpt_floor_followthrough
from app.services.draft_followthrough import (
    case_study_surface_followthrough,
    daily_activity_scene_followthrough,
)
from app.services.market_explanation_followthrough import market_explanation_selected_excerpt_floor_followthrough
from app.services.market_explanation_context_sanitizer import sanitize_market_explanation_writer_context
class DraftWriter:
    def __init__(self, client: LLMClient) -> None:
        self.client = client
    def write(
        self,
        article_brief: dict[str, Any],
        knowledge_pack: dict[str, Any],
        selected_source_excerpts: list[dict[str, Any]] | None = None,
    ) -> str:
        draft_article_brief = _draft_writer_article_brief(article_brief)
        draft_knowledge_pack, draft_selected_source_excerpts = sanitize_market_explanation_writer_context(
            draft_article_brief,
            knowledge_pack,
            selected_source_excerpts,
        )
        payload: dict[str, Any] = {"article_brief": draft_article_brief, "knowledge_pack": draft_knowledge_pack}
        if draft_selected_source_excerpts:
            payload["selected_source_excerpts"] = draft_selected_source_excerpts
        draft = self.client.generate_text(
            "draft_writer",
            _build_draft_writer_instructions(draft_article_brief, draft_knowledge_pack, draft_selected_source_excerpts),
            payload,
        )
        draft = company_intro_selected_excerpt_floor_followthrough(
            draft,
            draft_article_brief,
            draft_selected_source_excerpts,
            draft_knowledge_pack,
        )
        draft = daily_activity_scene_followthrough(draft, draft_article_brief, draft_selected_source_excerpts)
        draft = case_study_surface_followthrough(draft, draft_article_brief)
        draft = market_explanation_selected_excerpt_floor_followthrough(
            draft,
            draft_article_brief,
            draft_selected_source_excerpts,
            draft_knowledge_pack,
        )
        return announcement_selected_excerpt_floor_followthrough(
            draft,
            draft_article_brief,
            draft_selected_source_excerpts,
            draft_knowledge_pack,
        )
_COMPANY_INTRO_PARAGRAPH_PLAN_OVERRIDES = { 0: "導入: 会社に強い関心がある前提にせず、検索・サムネイル経由の人にも触れる日々の場面・運用・知見から入る。", 1: "引き込み: 会社の事業・商品・対象者・運用を、source事実に沿って私たちの仕事・行動・価値としてつなぐ。", 4: "締め: 本文で扱った会社の仕事・商品・背景から、私たちが何を大切にしているかへ静かに結ぶ。", }
_COMPANY_INTRO_STYLE_RULES = [ "本文では私たちを基準にし、外部レビューのような語り口にしない。", "商品・サービス・人物・理念は、sourceに基づく私たちの仕事・行動・価値として書く。", "商品は掲載ページの範囲に限り、全商品や代表商品と断定しない。", "段落は2文前後を基本にし、話題が変わるところで改行する。", "読点は打ちすぎず、自然なリズムを優先する。", "数字、年月日、固有名詞は改変しない。", "売上、規模、優位性、効果、成功は推定しない。", "締めは本文で扱った仕事・商品・背景から、私たちが何を大切にしているかへ静かに結ぶ。", "未使用claimは根拠確認用に保持し、本文へ全項目として詰め込まない。", ]
_COMPANY_INTRO_ACTION_VALUE_FIELDS = { "article_goal": "検索結果やサムネイルから訪れた人にも、私たちが何を扱い、どんな場面を支え、どんな運用・人・考え方で届けているかを、source事実に基づいて伝える会社紹介記事を書く。", "interest_hook": "会社説明から始めず、暮らし・仕事・選定・運用・知見と私たちの仕事がつながる小さな接点から入る。", "reading_reward": "会社の肩書きではなく、私たちがどの場面を支え、どんな人・運用・考え方で届けているかを本文で扱う。", "self_authored_angle": "私たちは、プロフィールや商品カタログの紹介だけでなく、日々の接点とsource事実から自分たちの仕事・行動・価値を伝える。", "source_derived_aside_policy": "濃い事実ブロック後は、source内の事実を私たちの仕事・運用・価値へつなぐ一文だけを置く。余談は最大2文、体験談・感想・顧客事例・成果・優位性は足さない。", "company_action_value_bridge_contract": "source事実は、商品・人・理念を含めて、私たちが何を扱い、どう届け、何を大切にするかへ橋渡しする。", }
_COMPANY_INTRO_RHYTHM_BREAK_PLAN = [ "事実説明が続いた後は、source内の隣接事実を私たちの仕事・運用・価値へつなぐ一文を置く。" ]
def _draft_writer_article_brief(article_brief: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(article_brief, dict):
        return article_brief
    brief = article_brief.get("article_brief")
    if not isinstance(brief, dict):
        return article_brief
    if str(brief.get("genre_id") or "") != "company_service_intro":
        return article_brief
    if str(brief.get("voice_mode") or "") != "self_authored_blogger":
        return article_brief
    if str(brief.get("source_shape") or "") == "table_or_list":
        return article_brief
    normalized_article_brief = deepcopy(article_brief)
    normalized_brief = normalized_article_brief.get("article_brief")
    if not isinstance(normalized_brief, dict):
        return article_brief
    plan = brief.get("paragraph_function_plan")
    if isinstance(plan, list):
        normalized_plan = list(plan)
        for index, replacement in _COMPANY_INTRO_PARAGRAPH_PLAN_OVERRIDES.items():
            if index < len(normalized_plan):
                normalized_plan[index] = replacement
        normalized_brief["paragraph_function_plan"] = normalized_plan
    normalized_brief["style_rules"] = list(_COMPANY_INTRO_STYLE_RULES)
    normalized_brief["rhythm_break_plan"] = list(_COMPANY_INTRO_RHYTHM_BREAK_PLAN)
    normalized_brief.update(_COMPANY_INTRO_ACTION_VALUE_FIELDS)
    normalized_brief.pop("source_backed_reader_bridge_policy", None)
    return normalized_article_brief
def _build_draft_writer_instructions(
    article_brief: dict[str, Any],
    knowledge_pack: dict[str, Any] | None = None,
    selected_source_excerpts: list[dict[str, Any]] | None = None,
) -> str:
    brief = article_brief.get("article_brief", {}) if isinstance(article_brief, dict) else {}
    target_chars = int(brief.get("target_length_chars") or 0)
    floor_chars = int(brief.get("body_length_floor_chars") or 0)
    source_thickness = str(brief.get("source_thickness") or "")
    section_count = int(brief.get("section_count") or 0)
    claim_count = _confirmed_claim_count(knowledge_pack)
    assigned_claim_count = _assigned_claim_count(brief)
    voice_mode = str(brief.get("voice_mode") or "")
    genre_id = str(brief.get("genre_id") or "")
    source_shape = str(brief.get("source_shape") or "")
    if selected_source_excerpts:
        base = (
            "Write a complete Markdown blog article from article_brief. "
            "Use selected_source_excerpts as primary section context: bounded primary material for matching sections, preserving source order/relationships. "
            "Use assigned/confirmed claims as verification anchors, not main prose source. "
            "Return article text only. Do not add facts absent from selected_source_excerpts or confirmed claims. "
            "Treat self_viewpoint_owner as speaker, not outside subject. "
            "No third-party review or source-summary voice."
        )
    else:
        base = (
            "Write a complete Markdown blog article from article_brief and confirmed claims only. "
            "Return article text only. Do not add facts that are not present in confirmed claims. "
            "Treat self_viewpoint_owner as the speaker, not as an outside subject. "
            "Do not use third-party review or source-summary voice."
        )
    if voice_mode == "self_authored_blogger":
        h1_instruction = (
            ' Start with exactly one H1 heading line ("# " + title) before H2 sections; no second H1. '
            if floor_chars > 0
            else ""
        )
        source_excerpt_instruction = ""
        company_intro_instruction = (
            " For company/service/product introductions, open from source-backed daily/work/selection/operations context; use people, culture, recruitment, or behind-the-scenes angles only when source-supported, and avoid visible meta/source labels such as 参考, CTA, Copyright, ポイント, or 同社."
            + _company_intro_reader_bridge_instruction(source_shape)
            if genre_id == "company_service_intro"
            else ""
        )
        genre_contract_instruction = _genre_contract_instruction(genre_id)
        floor_actuation_instruction = _floor_actuation_instruction(
            brief,
            floor_chars=floor_chars,
            target_chars=target_chars,
            section_count=section_count,
            assigned_claim_count=assigned_claim_count,
            selected_source_excerpts=selected_source_excerpts,
        )
        return (
            base
            + " Write as a self-authored Japanese organization blog/notice for readers casually browsing. "
            "Use reader_arrival_context, interest_hook, reading_reward, self_authored_angle, paragraph_function_plan, and company_action_value_bridge_contract as design guidance. Do not mention those field names. "
            "Start from a source-backed reason to keep reading, not a generic article announcement. "
            "Keep self-perspective; do not invent personal experience, feelings, usage, customer stories, outcomes, or guarantees. "
            "If rhythm_break_plan exists, use at most 2 one-sentence source-derived asides after dense fact blocks; no anecdotes or new claims. "
            "Do not exhaust table/list/FAQ/catalog items unless source_use_mode is exhaustive. "
            + h1_instruction
            + source_excerpt_instruction
            + company_intro_instruction
            + genre_contract_instruction
            + floor_actuation_instruction
            + _route_v_length_instruction(floor_chars=floor_chars, target_chars=target_chars)
            + f"For {section_count or 'the planned'} sections, {assigned_claim_count or 'the assigned'} assigned claims, and {claim_count or 'available'} confirmed claims, develop paragraphs with source-grounded context, no filler."
        )
    if target_chars >= 1800 or source_thickness == "thick":
        return (
            base
            + " Use target_length_chars as a soft depth target, not as padding. "
            "When confirmed claims are sufficient, aim for at least about 85 percent of that target by naturally "
            "deepening each substantial section with source-grounded context, reader relevance, and transitions. "
            f"For {section_count or 'each'} planned sections and {claim_count or 'all'} confirmed claims, write a full article rather than a short summary. "
            "If a section rule asks for concise organization, keep it organized but do not shrink the article below the depth target. "
            "Prefer two paragraphs in substantial sections, cover all assigned claims, and avoid filler."
        )
    return (
        base
        + " Keep the article concise, but still cover the assigned claims with natural transitions."
    )
def _confirmed_claim_count(knowledge_pack: dict[str, Any] | None) -> int:
    if not isinstance(knowledge_pack, dict):
        return 0
    pack = knowledge_pack.get("article_knowledge_pack")
    if not isinstance(pack, dict):
        return 0
    claims = pack.get("confirmed_facts")
    return len(claims) if isinstance(claims, list) else 0
def _assigned_claim_count(brief: dict[str, Any]) -> int:
    claim_ids: set[str] = set()
    allocations = brief.get("claim_allocation")
    if isinstance(allocations, list):
        for allocation in allocations:
            if isinstance(allocation, dict):
                claim_ids.update(str(claim_id) for claim_id in allocation.get("claim_ids") or [] if claim_id)
    if claim_ids:
        return len(claim_ids)
    sections = brief.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if isinstance(section, dict):
                claim_ids.update(str(claim_id) for claim_id in section.get("assigned_claim_ids") or [] if claim_id)
    return len(claim_ids)
def _floor_actuation_instruction(
    brief: dict[str, Any],
    *,
    floor_chars: int,
    target_chars: int,
    section_count: int,
    assigned_claim_count: int,
    selected_source_excerpts: list[dict[str, Any]] | None = None,
) -> str:
    if floor_chars <= 0:
        return ""
    source_use_mode = str(brief.get("source_use_mode") or "")
    representative_note = (
        " Representative/selective mode is not short-summary mode: deepen assigned claims; do not enumerate unassigned claims. "
        if source_use_mode in {"representative", "selective"}
        else ""
    )
    section_paragraph_target = max(2, int(section_count or 1) * 2)
    claim_paragraph_target = min(assigned_claim_count, 10)
    floor_paragraph_target = max(2, (floor_chars + 109) // 110)
    paragraph_target = max(section_paragraph_target, claim_paragraph_target, floor_paragraph_target)
    pre_editor_buffer = _pre_editor_floor_buffer_chars(brief, floor_chars)
    depth_budget = max(target_chars, floor_chars + pre_editor_buffer)
    section_depth_budget = max(260, (depth_budget + max(section_count, 1) - 1) // max(section_count, 1))
    excerpt_count = len(selected_source_excerpts or [])
    excerpt_note = (
        f" Use {excerpt_count} selected_source_excerpts as primary section context, not extra inventory. "
        "Keep assigned claims as verification anchors. "
        if excerpt_count
        else ""
    )
    backfill_note = (
        "Backfill paragraphs with assigned-claim depth or relevant unassigned confirmed claims as company-side context, not inventory. "
        if str(brief.get("genre_id") or "") == "company_service_intro" and str(brief.get("source_shape") or "") != "table_or_list"
        else "If assigned claims are fewer than paragraphs, split dense assigned claims into adjacent context, example, or transition paragraphs tied to confirmed claims. "
    )
    return (
        f" Body floor actuation: write at least {paragraph_target} source-grounded body paragraphs. "
        f"Depth budget contract: draft about {depth_budget} source-backed body chars before editors, roughly {section_depth_budget} per section when supported, preserving a {pre_editor_buffer}-char floor buffer. "
        "Use assigned claims as anchors; each section needs claim context, source detail, and source-tied relevance, not micro-paragraphs. "
        + backfill_note
        + "Do not stop below floor_chars. Floor_chars is not padding; no unsupported claims."
        + excerpt_note
        + representative_note
    )
def _pre_editor_floor_buffer_chars(brief: dict[str, Any], floor_chars: int) -> int:
    if str(brief.get("genre_id") or "") != "company_service_intro":
        return min(420, max(280, floor_chars // 4))
    return min(900, max(520, floor_chars // 2))
def _route_v_length_instruction(*, floor_chars: int, target_chars: int) -> str:
    minimum = floor_chars or 1200
    if floor_chars > 0 and target_chars and target_chars < floor_chars:
        return (
            f"Treat body_length_floor_chars={floor_chars} as the minimum body length after editors; "
            f"target_length_chars={target_chars} is below that floor, so do not use it as a shortening or upper-limit cue. "
        )
    return (
        f"Treat body_length_floor_chars={minimum} as the minimum body length after editors when source claims support it; "
        "use target_length_chars only as a soft depth guide, never as a reason to stop below the floor. "
    )
def _company_intro_reader_bridge_instruction(source_shape: str) -> str:
    if source_shape == "table_or_list":
        return ""
    return (
        " Source-backed company bridge: turn source-present customers, products, operations, history, or philosophy into company-side work/action/value statements; "
        "avoid page/category/official-info navigation and outside-observer inference. "
        "Treat page/category/source labels as material, not the subject. "
        "Each H2 needs source detail plus relevance; in 2-section plans, make both H2s substantial. "
        "Do not add market share, centrality, indispensability, outcomes, feelings, superiority, guarantees, unsupported places/industries, or overclaims like 一手に, 中心企業, 不可欠, トップ. "
    )
def _genre_contract_instruction(genre_id: str) -> str:
    instructions = {
        "daily_activity": " For daily activity, diary style is allowed; expand only from source-near place, action, object, sequence, and constraint, and do not assert third-party feelings, outcomes, or strong causality.",
        "case_study": " For case studies, connect source-derived issue, action, and change order, but do not assert outcomes, customer feelings, strong causality, numbers, or evaluations unless the source states them.",
        "announcement": " For announcements, keep it compact and factual; do not warm it into a diary or long blog essay.",
        "comparison_guide": " For comparison guides, avoid point-list article drift, rankings, and unsupported recommendations; show how to read source-supported differences.",
        "market_explanation": " For market explanations, avoid third-party source-summary voice; explain the source-supported points from the self-authored perspective.",
    }
    return instructions.get(genre_id, "")
