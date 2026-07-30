from __future__ import annotations

import re
from typing import Any

from app.services.config_loader import get_genre_config, load_project_config
from app.services.article_brief_source_shape_v2 import apply_source_shape_v2, use_source_shape_v2
from app.services.llm_client import LLMClient
from app.services.persona_loader import load_persona_bundle
from app.services.schema_validator import validate_payload


EDITORIAL_BRIDGE_FORBIDDEN_CLAIMS = [
    "unsupported_numbers",
    "prices",
    "outcomes",
    "superiority_claims",
    "market_trends",
    "customer_cases",
    "legal_medical_financial_advice",
]

DEFAULT_FORBIDDEN_VIEWPOINT_TERMS = (
    "\u540c\u793e",
    "\u540c\u30b5\u30fc\u30d3\u30b9",
    "\u540c\u5e97",
    "\u540c\u9662",
    "\u7b2c\u4e09\u8005\u3068\u3057\u3066",
)


def build_editorial_bridge_policy() -> dict[str, Any]:
    return {
        "enabled": False,
        "max_items": 0,
        "max_sentences_each": 1,
        "max_article_ratio_percent": 1,
        "required_grounding": "source_claim_ids",
        "factual_status": "not_a_fact_claim",
        "allowed_kinds": [],
        "forbidden_claims": list(EDITORIAL_BRIDGE_FORBIDDEN_CLAIMS),
    }


class ArticleBriefBuilder:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def build(
        self,
        knowledge_pack: dict[str, Any],
        genre_id: str,
        target_reader: str,
        article_goal: str,
        narrator: str | None = None,
        self_viewpoint_owner: str | None = None,
        blog_persona_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        config = load_project_config()
        genre = get_genre_config(genre_id, config)
        persona_id = genre["default_persona_id"]
        persona = load_persona_bundle(persona_id)
        resolved_narrator = narrator or genre["default_narrator"]
        resolved_owner = str(self_viewpoint_owner or resolved_narrator).strip()
        result = self.client.generate_json(
            "article_brief_builder",
            "Build an article brief. The narrator speaks as self_viewpoint_owner, not as an outside reviewer. Allocate claim IDs by section. Keep editorial_bridge_candidates empty.",
            {
                "knowledge_pack": knowledge_pack,
                "genre_id": genre_id,
                "persona_id": persona_id,
                "writer_role": genre["default_writer_role"],
                "viewpoint_mode": persona.viewpoint_profile["viewpoint_mode"],
                "style_profile": persona.style_profile,
                "editor_profile": persona.editor_profile,
                "narrator": resolved_narrator,
                "self_viewpoint_owner": resolved_owner,
                "qa_policy_id": genre["qa_policy_id"],
                "target_reader": target_reader,
                "article_goal": article_goal,
                "editorial_bridge_policy": build_editorial_bridge_policy(),
                "blog_persona_profile": _normalize_blog_persona_profile(blog_persona_profile),
            },
            "article_brief.schema.json",
        )
        _disable_editorial_bridges(result)
        _enforce_self_perspective_contract(
            result,
            genre_id=genre_id,
            genre=genre,
            persona=persona,
            persona_id=persona_id,
            narrator=resolved_narrator,
            self_viewpoint_owner=resolved_owner,
            blog_persona_profile=blog_persona_profile,
        )
        if use_source_shape_v2():
            apply_source_shape_v2(result, knowledge_pack, article_goal=article_goal)
        else:
            _enforce_depth_contract(result, knowledge_pack)
        _enforce_comparison_target_category(result, knowledge_pack)
        validate_payload("article_brief.schema.json", result)
        return result


def _disable_editorial_bridges(article_brief: dict[str, Any]) -> None:
    brief = article_brief.get("article_brief", {})
    brief["editorial_bridge_policy"] = build_editorial_bridge_policy()
    brief["editorial_bridge_candidates"] = []


def _enforce_self_perspective_contract(
    article_brief: dict[str, Any],
    *,
    genre_id: str,
    genre: dict[str, Any],
    persona: Any,
    persona_id: str,
    narrator: str,
    self_viewpoint_owner: str,
    blog_persona_profile: dict[str, Any] | None = None,
) -> None:
    brief = article_brief.get("article_brief", {})
    if not isinstance(brief, dict):
        return

    brief["genre_id"] = genre_id
    brief["persona_id"] = persona_id
    brief["writer_role"] = genre["default_writer_role"]
    brief["viewpoint_mode"] = "self_perspective"
    brief["narrator"] = narrator
    brief["self_viewpoint_owner"] = self_viewpoint_owner
    brief["qa_policy_id"] = genre["qa_policy_id"]
    brief["style_profile_id"] = persona.style_profile.get("style_profile_id", brief.get("style_profile_id"))
    brief["editor_profile_id"] = persona.editor_profile.get("editor_profile_id", brief.get("editor_profile_id"))

    allowed_voice = persona.viewpoint_profile.get("allowed_external_voice")
    if allowed_voice:
        brief["allowed_external_voice"] = allowed_voice

    terms = []
    terms.extend(DEFAULT_FORBIDDEN_VIEWPOINT_TERMS)
    terms.extend(persona.viewpoint_profile.get("forbidden_terms", []))
    terms.extend(brief.get("forbidden_viewpoint_terms", []))
    brief["forbidden_viewpoint_terms"] = _unique_strings(terms)
    profile = _normalize_blog_persona_profile(blog_persona_profile)
    style_rule = profile.get("style_rule")
    if style_rule:
        style_rules = brief.get("style_rules")
        if not isinstance(style_rules, list):
            style_rules = []
        brief["style_rules"] = _unique_strings([*style_rules, style_rule])
        persona_refs = brief.get("persona_refs")
        if not isinstance(persona_refs, list):
            persona_refs = []
        brief["persona_refs"] = _unique_strings([*persona_refs, str(profile.get("label") or "")])


def _normalize_blog_persona_profile(value: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    label = str(value.get("label") or "").strip()
    style_rule = str(value.get("style_rule") or "").strip()
    profile_id = str(value.get("profile_id") or "").strip()
    return {
        "label": label,
        "profile_id": profile_id,
        "style_rule": style_rule,
    }


def _enforce_depth_contract(article_brief: dict[str, Any], knowledge_pack: dict[str, Any]) -> None:
    brief = article_brief.get("article_brief", {})
    if not isinstance(brief, dict):
        return
    target_chars = _safe_int(brief.get("target_length_chars"))
    source_thickness = str(brief.get("source_thickness") or "")
    claim_count = _confirmed_claim_count(knowledge_pack)
    if target_chars < 1800 and source_thickness != "thick":
        return
    if claim_count < 8:
        return

    style_rules = brief.get("style_rules")
    if not isinstance(style_rules, list):
        style_rules = []
    brief["style_rules"] = _unique_strings(
        [
            *style_rules,
            "厚いソースでは短い要約で終えず、各見出しで根拠・背景・読者にとっての意味を自然に展開する。",
            "target_length_charsは水増しではなく、confirmed claimsを使い切るための深さ目安として扱う。",
        ]
    )

    sections = brief.get("sections")
    if not isinstance(sections, list):
        return
    for section in sections:
        if not isinstance(section, dict):
            continue
        rules = section.get("discourse_rules")
        current_rules = [str(item) for item in rules] if isinstance(rules, list) else []
        revised_rules = [_expand_concise_rule(rule) for rule in current_rules]
        assigned_claims = section.get("assigned_claim_ids")
        claim_total = len(assigned_claims) if isinstance(assigned_claims, list) else 0
        revised_rules.append(
            f"割り当てclaim {claim_total}件を短く列挙して終えず、本文段落で背景・使われ方・読者への意味を添える。"
        )
        section["discourse_rules"] = _unique_strings(revised_rules)


def _enforce_comparison_target_category(article_brief: dict[str, Any], knowledge_pack: dict[str, Any]) -> None:
    brief = article_brief.get("article_brief", {})
    if not isinstance(brief, dict):
        return
    if brief.get("genre_id") != "comparison_guide":
        return
    current = str(brief.get("comparison_target_category") or "").strip()
    if current:
        brief["comparison_target_category"] = current
        return
    category = _derive_comparison_target_category(
        target_reader=str(brief.get("target_reader") or ""),
        knowledge_pack=knowledge_pack,
    )
    if category:
        brief["comparison_target_category"] = category


def _derive_comparison_target_category(*, target_reader: str, knowledge_pack: dict[str, Any]) -> str:
    from_reader = _category_from_target_reader(target_reader)
    if from_reader:
        return from_reader
    return _category_from_confirmed_claims(knowledge_pack)


def _category_from_target_reader(target_reader: str) -> str:
    text = target_reader.strip()
    if not text:
        return ""
    patterns = (
        r"(?P<category>[^、。]{2,40}?)を比較(?:している|する|したい|中|検討)",
        r"(?P<category>[^、。]{2,40}?)の比較(?:を|で|に)",
        r"(?P<category>[^、。]{2,40}?)を選(?:んでいる|ぶ|びたい)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return _clean_comparison_target_category(match.group("category"))
    return ""


def _category_from_confirmed_claims(knowledge_pack: dict[str, Any]) -> str:
    pack = knowledge_pack.get("article_knowledge_pack", {}) if isinstance(knowledge_pack, dict) else {}
    claims = pack.get("confirmed_facts", []) if isinstance(pack, dict) else []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        text = str(claim.get("preferred_expression") or claim.get("claim") or "")
        match = re.search(r"は、[^。]{0,80}?(?P<category>[^、。]{2,40}?(?:ツール|サービス|プラン|製品|システム))です。", text)
        if match:
            return _clean_comparison_target_category(match.group("category"))
    return ""


def _clean_comparison_target_category(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^(?:この|その|複数の|三つの|3つの|各)\s*", "", text)
    text = re.sub(r"^(?:候補|選択肢|サービス|製品)の", "", text)
    text = re.sub(r"^.*?(?:利用できる|対応する|対応した|使える|向けの)", "", text)
    return text.strip(" 、。")


def _expand_concise_rule(rule: str) -> str:
    text = str(rule or "")
    replacements = (
        ("一例を簡潔に列挙", "代表例を整理し、それぞれの見方を短く添える"),
        ("簡潔に列挙", "分類して説明し、主要項目には1文ずつ文脈を添える"),
        ("箇条書き的にまとめる", "読みやすく整理しつつ、必要な背景を短く添える"),
    )
    for before, after in replacements:
        text = text.replace(before, after)
    return text


def _confirmed_claim_count(knowledge_pack: dict[str, Any]) -> int:
    if not isinstance(knowledge_pack, dict):
        return 0
    pack = knowledge_pack.get("article_knowledge_pack")
    if not isinstance(pack, dict):
        return 0
    claims = pack.get("confirmed_facts")
    return len(claims) if isinstance(claims, list) else 0


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _unique_strings(values: list[Any] | tuple[Any, ...]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result
