"""Coverage planner for vNext."""
from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any, Dict, List, Tuple

from core.app_config import get_vnext_overlap_runtime_config

from .types import FactCard, SectionBrief, VNextThinContract

_TOKEN_RE = re.compile(r"[A-Za-z0-9一-龥ぁ-んァ-ヶー]{2,24}")

_SKELETONS: Dict[tuple[str, str], List[str]] = {
    ("announcement", "standard_notice"): ["change", "target_and_when", "impact", "check", "action"],
    ("announcement", "maintenance_notice"): ["change", "target_and_when", "impact", "check", "action"],
    ("announcement", "policy_change_notice"): ["change", "target_and_when", "impact", "check", "action"],
    ("announcement", "release_note"): ["change", "target_and_when", "impact", "check", "action"],
    ("branding", "fact_profile"): ["company_or_offer_outline", "problem_background", "concrete_strength", "why_it_matters", "closing"],
    ("branding", "problem_value"): ["problem_scene", "problem_cost", "value_explained", "concrete_support", "closing"],
    ("branding", "story_driven"): ["scene", "tension_or_question", "action_or_choice", "realized_value", "reader_connection"],
    ("branding", "founder_voice"): ["origin", "problem_background", "choice", "value_realized", "closing"],
    ("daily_story", "observation_reflection"): ["observation", "felt_shift", "concrete_scene", "later_insight", "quiet_close"],
    ("daily_story", "event_then_learning"): ["event", "turning_point", "lesson", "application", "quiet_close"],
    ("explanatory_article", "concept_breakdown"): ["question", "concept_definition", "mechanism", "practical_example", "takeaway"],
    ("explanatory_article", "problem_solution"): ["question", "problem_background", "solution_path", "practical_example", "takeaway"],
    ("case_study", "implementation_case"): ["initial_problem", "approach", "adjustment", "result", "reuse_condition"],
    ("case_study", "improvement_case"): ["initial_problem", "approach", "adjustment", "result", "reuse_condition"],
    ("case_study", "incident_case"): ["incident", "impact", "response", "prevention", "reuse_condition"],
    ("comparative_review", "criteria_first"): ["comparison_frame", "criteria", "differences", "fit_by_usecase", "conclusion"],
    ("comparative_review", "usecase_first"): ["comparison_frame", "fit_by_usecase", "differences", "criteria", "conclusion"],
    ("industry_analysis", "structure_shift"): ["market_context", "structure_change", "implication", "decision_hint", "closing"],
    ("industry_analysis", "trend_implication"): ["market_context", "trend_signal", "implication", "decision_hint", "closing"],
}

_ROLE_HEADINGS = {
    "change": "変更点の要点",
    "target_and_when": "対象と時期",
    "impact": "影響の整理",
    "check": "確認しておきたい点",
    "action": "次のアクション",
    "company_or_offer_outline": "まず輪郭をそろえる",
    "problem_background": "なぜ必要になるのか",
    "concrete_strength": "具体的な強み",
    "why_it_matters": "読者にとっての意味",
    "closing": "最後に押さえたいこと",
    "problem_scene": "課題が立ち上がる場面",
    "problem_cost": "放置コスト",
    "value_explained": "価値の中身",
    "concrete_support": "価値を支える根拠",
    "scene": "場面から入る",
    "tension_or_question": "そこで何が引っかかったか",
    "action_or_choice": "どう選んだか",
    "realized_value": "見えてきた価値",
    "reader_connection": "読者に引き寄せる",
    "origin": "出発点",
    "value_realized": "形になった価値",
    "observation": "観察したこと",
    "felt_shift": "感覚が動いた点",
    "concrete_scene": "場面を具体化する",
    "later_insight": "あとから分かったこと",
    "quiet_close": "静かに締める",
    "event": "出来事の整理",
    "turning_point": "転換点",
    "lesson": "学び",
    "application": "次に活かせること",
    "question": "最初の問い",
    "concept_definition": "まず定義をそろえる",
    "mechanism": "仕組みをほどく",
    "practical_example": "具体例でつかむ",
    "takeaway": "判断材料として残す",
    "solution_path": "解き方の筋道",
    "initial_problem": "最初の課題",
    "approach": "どう進めたか",
    "adjustment": "途中で調整した点",
    "result": "見えた変化",
    "reuse_condition": "再現条件",
    "incident": "起きたこと",
    "response": "どう対処したか",
    "prevention": "再発防止",
    "comparison_frame": "比較の前提",
    "criteria": "評価軸",
    "differences": "差分の見方",
    "fit_by_usecase": "用途別の向き不向き",
    "conclusion": "結論",
    "market_context": "市場の前提",
    "structure_change": "構造変化",
    "implication": "示唆",
    "decision_hint": "判断の置き方",
    "trend_signal": "いま起きている兆し",
}


def _normalize_terms(text: str, *, limit: int = 5) -> List[str]:
    terms: List[str] = []
    for token in _TOKEN_RE.findall(str(text or "")):
        if token not in terms:
            terms.append(token)
        if len(terms) >= limit:
            break
    return terms


def _length_target(contract: VNextThinContract) -> int:
    if contract.length_mode == "short":
        return 300
    if contract.length_mode in {"long", "note_4000"}:
        return 520
    return 420


def _role_heading(role: str) -> str:
    return _ROLE_HEADINGS.get(role, role.replace("_", " "))


def _build_primary_claim(contract: VNextThinContract, role: str) -> str:
    topic = contract.topic_statement or contract.prompt_raw
    if contract.article_type == "announcement":
        if role == "change":
            return f"{topic}の変更点を最初に明確にする"
        if role == "action":
            return "読者が迷わず次の行動を選べる形で締める"
    if role in {"result", "realized_value", "implication", "takeaway", "closing", "conclusion"}:
        return f"{topic}から読者の判断につながる要点を残す"
    return f"{topic}について、{_role_heading(role)}の役割を担う"


def _reader_question(contract: VNextThinContract, role: str) -> str:
    audience = contract.audience_profile or "読者"
    if role in {"criteria", "differences"}:
        return f"{audience}が比較で見落としやすい点は何か"
    if role in {"action", "reuse_condition", "decision_hint"}:
        return f"{audience}は次に何を確認すべきか"
    return f"{audience}がここで知りたいことは何か"


def _narrator_visibility(contract: VNextThinContract, role: str) -> str:
    if contract.article_type in {"announcement", "industry_analysis", "comparative_review"}:
        return "implicit"
    if contract.discourse_mode in {"story_driven", "founder_voice"} and role in {"scene", "origin", "observation"}:
        return "visible"
    if contract.article_type == "daily_story":
        return "visible"
    return "implicit"


def _emotion_target(contract: VNextThinContract, index: int, section_count: int) -> int:
    if section_count <= 1:
        return contract.emotion_level
    if index == 0 or index == section_count - 1:
        return max(0, contract.emotion_level - 1)
    return contract.emotion_level


def _build_must_keep_terms(contract: VNextThinContract, facts: List[FactCard], role: str) -> List[str]:
    terms = _normalize_terms(contract.topic_statement or contract.prompt_raw, limit=3)
    if role in {"change", "target_and_when", "impact"}:
        for fact in facts:
            if fact.date_or_period and fact.date_or_period not in terms:
                terms.append(fact.date_or_period)
    for fact in facts[:2]:
        if fact.entity and fact.entity not in terms:
            terms.append(fact.entity)
    return terms[:5]


def _select_fact_ids(contract: VNextThinContract, role_count: int) -> List[List[str]]:
    if not contract.fact_cards:
        return [[] for _ in range(role_count)]
    fact_id_sets: List[List[str]] = [[] for _ in range(role_count)]
    for index, fact_card in enumerate(contract.fact_cards):
        target_index = index % role_count
        fact_id_sets[target_index].append(fact_card.fact_id)
    return fact_id_sets


def _runtime_overlap_policy() -> Dict[str, Any]:
    cfg = get_vnext_overlap_runtime_config()
    return {
        "status": "promoted_seed",
        "calibration_required": False,
        "seed_source": "core.app_config.get_vnext_overlap_runtime_config",
        "seed_thresholds": {
            "similarity_threshold": float(cfg.get("similarity_threshold", 0.62)),
            "content_overlap_threshold": float(cfg.get("content_overlap_threshold", 0.77)),
            "high_overlap_shortcut_threshold": float(cfg.get("high_overlap_shortcut_threshold", 0.83)),
        },
    }


def build_section_briefs(contract: VNextThinContract) -> Tuple[List[SectionBrief], Dict[str, Any]]:
    skeleton = _SKELETONS.get(
        (contract.article_type, contract.discourse_mode),
        _SKELETONS.get((contract.article_type, contract.article_type), ["question", "concept_definition", "takeaway"]),
    )
    target_chars = _length_target(contract)
    supporting_fact_ids = _select_fact_ids(contract, len(skeleton))
    briefs: List[SectionBrief] = []
    for index, role in enumerate(skeleton):
        section_id = f"section_{index + 1:02d}"
        brief_facts = [
            fact for fact in contract.fact_cards if fact.fact_id in supporting_fact_ids[index]
        ]
        briefs.append(
            SectionBrief(
                section_id=section_id,
                heading=_role_heading(role),
                section_role=role,
                target_chars=target_chars,
                primary_claim=_build_primary_claim(contract, role),
                supporting_fact_ids=supporting_fact_ids[index][:2],
                reader_question=_reader_question(contract, role),
                transition_target=f"section_{index + 2:02d}" if index + 1 < len(skeleton) else "",
                forbidden_overlap_ids=[item.section_id for item in briefs],
                narrator_visibility=_narrator_visibility(contract, role),
                emotion_target=_emotion_target(contract, index, len(skeleton)),
                must_keep_terms=_build_must_keep_terms(contract, brief_facts, role),
            )
        )
    planner_report = {
        "section_count": len(briefs),
        "skeleton": list(skeleton),
        "overlap_policy": _runtime_overlap_policy(),
        "ordered_section_briefs": [asdict(item) for item in briefs],
    }
    return briefs, planner_report
