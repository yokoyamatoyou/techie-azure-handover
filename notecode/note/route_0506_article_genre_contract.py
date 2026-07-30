"""Pure article genre and article-brief contract helpers for Route 0506."""
from __future__ import annotations

from typing import Any, Iterable, Mapping


COMPANY_INTRO_THICK_TARGET_LENGTH_CHARS = 2200
COMPANY_INTRO_THICK_SECTION_COUNT = 5
COMPANY_INTRO_RICH_CLAIM_COUNT = 18
COMPANY_INTRO_RICH_TARGET_LENGTH_CHARS = 2200
COMPANY_INTRO_MEDIUM_FULLNESS_CLAIM_COUNT = 10
COMPANY_INTRO_MEDIUM_FULLNESS_TARGET_MIN = 1800
COMPANY_INTRO_DENSE_SECTION_CLAIM_COUNT = 8
COMPANY_INTRO_DENSE_SECTION_CLAIM_RATIO = 0.55
COMPANY_INTRO_SOURCE_SHORTAGE_CLAIM_COUNT = 5
COMPANY_INTRO_SOURCE_SHORTAGE_TARGET_MAX = 1500
COMPANY_INTRO_FULLNESS_STYLE_RULES = (
    "target_length_charsはカテゴリとsource-backed fact量に応じた本文量の目安であり、固定必達値ではない。",
    "source-backed factが不足する場合は、数値目安へ水増しせず自然長に収める。",
    "各セクションは見出し直下に原則2段落以上を置き、assigned_claim_idsを読者の判断順に展開する。",
    "接続詞『また』に頼りすぎず、文脈で自然につなぐ。",
)
COMPANY_INTRO_DENSITY_SECTION_RULES = ("高密度セクションはサービス単位・判断材料単位で段落を分ける", "査定・買取・保証・一括査定など異なる相談材料を1段落に圧縮しない")
COMPANY_INTRO_FULLNESS_SECTION_RULES = (
    "1文要約で終えず、見出しの主題を2段落以上で具体化する",
    "各段落は根拠claimを1つ具体化し、80〜140字程度で読者の判断材料まで書く",
    "assigned_claim_idsを列挙で終えず、相談前の判断材料としてつなぐ",
    "section_countを増やさず、関連するassigned_claim_idsは同じ見出し内の段落で展開する",
)
COMPANY_INTRO_NATIVE_SECTION_PLANNING_CONTRACT_ID = "company_service_intro_native_5_section_v1"
COMPANY_INTRO_NATIVE_SECTION_PURPOSES = (
    ("who_we_are", "会社の立ち位置と地域・サービスの入口を示す"),
    ("reader_need", "読者が抱える相談前の不安や判断材料を扱う"),
    ("provided_value", "提供している売却支援・相談メニューを整理する"),
    ("delivery_values", "提案姿勢・地域知見・進め方を説明する"),
    ("inquiry_path", "相談につながる自然な締め方を置く"),
)
COMPANY_INTRO_NATIVE_SECTION_HEADINGS = {
    "who_we_are": "私たちの立ち位置", "reader_need": "相談前に整理したいこと", "provided_value": "提供している支援",
    "delivery_values": "支援で大切にしていること", "inquiry_path": "相談の入口",
}


def build_route_0506_article_genre_contract(input_contract: Mapping[str, Any]) -> dict[str, str | None]:
    genre_id = resolve_route_0506_genre(input_contract)
    return {"genre_id": genre_id, "narrator": resolve_route_0506_narrator(input_contract, genre_id=genre_id)}


def resolve_route_0506_genre(input_contract: Mapping[str, Any]) -> str:
    semantic_key = str(input_contract.get("semantic_article_key") or "").strip().lower()
    article_type = str(input_contract.get("article_type") or "").strip().lower()
    if article_type == "branding" and semantic_key == "company_introduction":
        return "company_service_intro"
    if semantic_key == "product_introduction":
        return "company_service_intro"
    if semantic_key == "announcement" or article_type == "announcement":
        return "announcement"
    if semantic_key in {"implementation_case", "improvement_case", "case_study"} or article_type == "case_study":
        return "case_study"
    if semantic_key == "comparative_review" or article_type == "comparative_review":
        return "comparison_guide"
    if semantic_key == "daily_story" or article_type == "daily_story":
        return "daily_activity"
    if semantic_key in {"explanatory_article", "industry_analysis"} or article_type in {
        "explanatory_article",
        "industry_analysis",
    }:
        return "market_explanation"
    return "company_service_intro"


def resolve_route_0506_narrator(input_contract: Mapping[str, Any], *, genre_id: str | None = None) -> str | None:
    if (genre_id or resolve_route_0506_genre(input_contract)) == "announcement":
        return "当社"
    allowed_pronouns = input_contract.get("self_reference_allowed_pronouns")
    if isinstance(allowed_pronouns, list):
        normalized = [str(item).strip() for item in allowed_pronouns]
        if "私たち" in normalized:
            return "私たち"
        if "当社" in normalized:
            return "当社"
    return "私たち"


def enrich_route_0506_article_brief_builder_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    if str(result.get("genre_id") or "") != "company_service_intro":
        return result

    confirmed_claims = _route_0506_confirmed_claims_from_payload(result)
    if len(confirmed_claims) < COMPANY_INTRO_MEDIUM_FULLNESS_CLAIM_COUNT:
        return result

    result["route_0506_section_planning_contract"] = {
        "contract_id": COMPANY_INTRO_NATIVE_SECTION_PLANNING_CONTRACT_ID,
        "source": "app/config/article_genres.yaml:company_service_intro.section_purposes",
        "source_thickness": "thick",
        "target_length_chars": COMPANY_INTRO_THICK_TARGET_LENGTH_CHARS,
        "target_length_semantics": "soft_natural_reference",
        "natural_length_policy": "Use category, source-backed fact depth, and padding risk; do not treat this as a user-requested hard length.",
        "section_count": COMPANY_INTRO_THICK_SECTION_COUNT,
        "confirmed_claim_count": len(confirmed_claims),
        "confirmed_claim_ids": [
            str(claim.get("claim_id"))
            for claim in confirmed_claims
            if str(claim.get("claim_id") or "").strip()
        ],
        "section_purposes": [
            {"purpose_id": purpose_id, "planning_role": planning_role}
            for purpose_id, planning_role in COMPANY_INTRO_NATIVE_SECTION_PURPOSES
        ],
        "claim_allocation_policy": (
            "Use all five section purposes when claim volume is sufficient. "
            "Assign every confirmed_claim_id exactly once unless it is explicitly unsafe, and do not collapse "
            "reader_need, provided_value, delivery_values, and inquiry_path into fewer headings."
        ),
        "source_grounding_policy": "Use only confirmed claim IDs and do not add unsupported facts or padding.",
    }
    return result


def normalize_route_0506_company_intro_article_brief_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    brief = result.get("article_brief")
    if not isinstance(brief, Mapping):
        return result
    if str(brief.get("genre_id") or "") != "company_service_intro":
        return result
    if not _route_0506_company_intro_fullness_normalization_needed(brief):
        return result

    next_brief = dict(brief)
    next_brief["source_thickness"] = "thick"
    target_length, section_count = _route_0506_company_intro_target_section_policy(next_brief)
    next_brief["target_length_chars"] = target_length
    next_brief["section_count"] = section_count
    style_rules = next_brief.get("style_rules")
    if isinstance(style_rules, list):
        next_brief["style_rules"] = _route_0506_append_unique_strings(
            style_rules,
            COMPANY_INTRO_FULLNESS_STYLE_RULES,
        )
    sections = next_brief.get("sections")
    if isinstance(sections, list):
        policy_sections = _route_0506_apply_company_intro_section_policy(sections, section_count)
        next_brief["sections"] = _route_0506_enrich_company_intro_sections_for_fullness(policy_sections)
        claim_allocation = next_brief.get("claim_allocation")
        if isinstance(claim_allocation, list):
            next_brief["claim_allocation"] = _route_0506_claim_allocation_from_sections(
                claim_allocation,
                next_brief["sections"],
            )
    result["article_brief"] = next_brief
    return result


def apply_route_0506_company_intro_section_planning_contract(
    payload: Mapping[str, Any],
    builder_payload: Mapping[str, Any],
) -> dict[str, Any]:
    contract = builder_payload.get("route_0506_section_planning_contract")
    if not isinstance(contract, Mapping):
        return dict(payload)
    if contract.get("contract_id") != COMPANY_INTRO_NATIVE_SECTION_PLANNING_CONTRACT_ID:
        return dict(payload)

    result = dict(payload)
    brief = result.get("article_brief")
    if not isinstance(brief, Mapping) or str(brief.get("genre_id") or "") != "company_service_intro":
        return result

    target_length = _route_0506_int_value(
        contract.get("target_length_chars"),
        default=COMPANY_INTRO_THICK_TARGET_LENGTH_CHARS,
    )
    section_count = _route_0506_int_value(
        contract.get("section_count"),
        default=COMPANY_INTRO_THICK_SECTION_COUNT,
    )
    if section_count < COMPANY_INTRO_THICK_SECTION_COUNT:
        return result

    claim_ids = _route_0506_unique_string_list(contract.get("confirmed_claim_ids") or [])
    if len(claim_ids) < COMPANY_INTRO_MEDIUM_FULLNESS_CLAIM_COUNT:
        return result

    next_brief = dict(brief)
    next_brief["source_thickness"] = str(contract.get("source_thickness") or "thick")
    next_brief["target_length_chars"] = target_length
    next_brief["section_count"] = section_count
    sections = _route_0506_build_company_intro_contract_sections(
        brief,
        contract,
        claim_ids,
        section_count,
    )
    next_brief["sections"] = _route_0506_enrich_company_intro_sections_for_fullness(sections)
    next_brief["claim_allocation"] = _route_0506_claim_allocation_from_sections(
        list(next_brief.get("claim_allocation") or []),
        next_brief["sections"],
    )
    style_rules = next_brief.get("style_rules")
    if isinstance(style_rules, list):
        next_brief["style_rules"] = _route_0506_append_unique_strings(
            style_rules,
            COMPANY_INTRO_FULLNESS_STYLE_RULES,
        )
    result["article_brief"] = next_brief
    return result


def _route_0506_confirmed_claims_from_payload(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    knowledge_pack = payload.get("knowledge_pack")
    if not isinstance(knowledge_pack, Mapping):
        return []
    pack = knowledge_pack.get("article_knowledge_pack")
    if not isinstance(pack, Mapping):
        return []
    claims = pack.get("confirmed_facts")
    if not isinstance(claims, list):
        return []
    return [claim for claim in claims if isinstance(claim, Mapping)]


def _route_0506_build_company_intro_contract_sections(
    brief: Mapping[str, Any],
    contract: Mapping[str, Any],
    claim_ids: list[str],
    section_count: int,
) -> list[dict[str, Any]]:
    existing_sections = brief.get("sections")
    existing = existing_sections if isinstance(existing_sections, list) else []
    purpose_entries = contract.get("section_purposes")
    purposes = purpose_entries if isinstance(purpose_entries, list) else []
    claim_groups = _route_0506_split_claim_ids_evenly(claim_ids, section_count)
    narrator = str(brief.get("narrator") or "私たち")

    sections: list[dict[str, Any]] = []
    for index in range(section_count):
        purpose_entry = purposes[index] if index < len(purposes) and isinstance(purposes[index], Mapping) else {}
        purpose_id = str(purpose_entry.get("purpose_id") or "").strip()
        planning_role = str(purpose_entry.get("planning_role") or "").strip()
        source_section = existing[index] if index < len(existing) and isinstance(existing[index], Mapping) else {}
        discourse_rules = source_section.get("discourse_rules") if isinstance(source_section, Mapping) else None
        sections.append(
            {
                "section_id": str(source_section.get("section_id") or f"s{index + 1}"),
                "heading": COMPANY_INTRO_NATIVE_SECTION_HEADINGS.get(
                    purpose_id,
                    str(source_section.get("heading") or f"見出し{index + 1}"),
                ),
                "purpose": planning_role or str(source_section.get("purpose") or "根拠claimを整理する"),
                "assigned_claim_ids": claim_groups[index] if index < len(claim_groups) else [],
                "main_subject": str(source_section.get("main_subject") or narrator),
                "discourse_rules": (
                    list(discourse_rules)
                    if isinstance(discourse_rules, list)
                    else ["同社を使わない", "根拠のない効果を足さない"]
                ),
            }
        )
    return sections


def _route_0506_split_claim_ids_evenly(claim_ids: list[str], section_count: int) -> list[list[str]]:
    if section_count <= 1:
        return [claim_ids]
    base_size, remainder = divmod(len(claim_ids), section_count)
    groups: list[list[str]] = []
    offset = 0
    for index in range(section_count):
        group_size = base_size + (1 if index < remainder else 0)
        groups.append(claim_ids[offset : offset + group_size])
        offset += group_size
    return groups


def _route_0506_company_intro_fullness_normalization_needed(brief: Mapping[str, Any]) -> bool:
    source_thickness = str(brief.get("source_thickness") or "")
    if source_thickness == "thick":
        return True
    if source_thickness != "medium":
        return False
    return (
        _route_0506_int_value(brief.get("target_length_chars"), default=0)
        >= COMPANY_INTRO_MEDIUM_FULLNESS_TARGET_MIN
        and _route_0506_int_value(brief.get("section_count"), default=0) >= COMPANY_INTRO_THICK_SECTION_COUNT
        and len(_route_0506_company_intro_unique_claim_ids(brief)) >= COMPANY_INTRO_MEDIUM_FULLNESS_CLAIM_COUNT
    )


def _route_0506_company_intro_target_section_policy(brief: Mapping[str, Any]) -> tuple[int, int]:
    current_target = _route_0506_int_value(brief.get("target_length_chars"), default=0)
    current_sections = _route_0506_int_value(brief.get("section_count"), default=0)
    claim_count = len(_route_0506_company_intro_unique_claim_ids(brief))
    max_section_claim_count, max_section_claim_ratio = _route_0506_company_intro_section_density(brief, claim_count)

    if claim_count <= COMPANY_INTRO_SOURCE_SHORTAGE_CLAIM_COUNT:
        guarded_target = current_target if current_target > 0 else 1200
        guarded_sections = current_sections if current_sections > 0 else 2
        return min(guarded_target, COMPANY_INTRO_SOURCE_SHORTAGE_TARGET_MAX), max(1, min(guarded_sections, 2))

    if claim_count >= COMPANY_INTRO_RICH_CLAIM_COUNT or _route_0506_company_intro_has_dense_section_load(
        max_section_claim_count,
        max_section_claim_ratio,
    ):
        return (
            COMPANY_INTRO_RICH_TARGET_LENGTH_CHARS,
            _route_0506_company_intro_section_floor(brief, current_sections),
        )

    return (
        COMPANY_INTRO_MEDIUM_FULLNESS_TARGET_MIN,
        _route_0506_company_intro_section_floor(brief, current_sections),
    )


def _route_0506_company_intro_section_floor(brief: Mapping[str, Any], current_sections: int) -> int:
    sections = brief.get("sections")
    actual_sections = len(sections) if isinstance(sections, list) else 0
    if actual_sections > 0:
        return min(COMPANY_INTRO_THICK_SECTION_COUNT, max(current_sections, actual_sections))
    return max(current_sections, COMPANY_INTRO_THICK_SECTION_COUNT)


def _route_0506_company_intro_has_dense_section_load(max_claim_count: int, max_claim_ratio: float) -> bool:
    return (
        max_claim_count >= COMPANY_INTRO_DENSE_SECTION_CLAIM_COUNT
        or max_claim_ratio >= COMPANY_INTRO_DENSE_SECTION_CLAIM_RATIO
    )


def _route_0506_company_intro_section_density(brief: Mapping[str, Any], total_claim_count: int) -> tuple[int, float]:
    sections = brief.get("sections")
    if not isinstance(sections, list) or total_claim_count <= 0:
        return 0, 0.0

    max_claim_count = 0
    for section in sections:
        if not isinstance(section, Mapping):
            continue
        max_claim_count = max(max_claim_count, len(_route_0506_section_claim_ids(section)))
    return max_claim_count, max_claim_count / total_claim_count


def _route_0506_int_value(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _route_0506_company_intro_unique_claim_ids(brief: Mapping[str, Any]) -> list[str]:
    claim_ids: list[str] = []
    sections = brief.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, Mapping):
                continue
            assigned_claim_ids = section.get("assigned_claim_ids")
            if isinstance(assigned_claim_ids, list):
                claim_ids.extend(str(item) for item in assigned_claim_ids if str(item).strip())

    claim_allocation = brief.get("claim_allocation")
    if isinstance(claim_allocation, list):
        for allocation in claim_allocation:
            if not isinstance(allocation, Mapping):
                continue
            allocation_claim_ids = allocation.get("claim_ids")
            if isinstance(allocation_claim_ids, list):
                claim_ids.extend(str(item) for item in allocation_claim_ids if str(item).strip())

    return _route_0506_unique_string_list(claim_ids)


def _route_0506_unique_string_list(values: Iterable[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _route_0506_append_unique_strings(values: list[Any], additions: Iterable[str]) -> list[Any]:
    result = list(values)
    existing = {str(value) for value in result}
    for addition in additions:
        if addition not in existing:
            result.append(addition)
            existing.add(addition)
    return result


def _route_0506_section_claim_ids(section: Mapping[str, Any]) -> list[str]:
    assigned_claim_ids = section.get("assigned_claim_ids")
    return _route_0506_unique_string_list(assigned_claim_ids if isinstance(assigned_claim_ids, list) else [])


def _route_0506_apply_company_intro_section_policy(sections: list[Any], section_count: int) -> list[Any]:
    if section_count <= 0 or len(sections) <= section_count:
        return [dict(section) if isinstance(section, Mapping) else section for section in sections]

    retained: list[Any] = [dict(section) if isinstance(section, Mapping) else section for section in sections[:section_count]]
    if not retained or not isinstance(retained[-1], Mapping):
        return retained

    merged_tail = dict(retained[-1])
    for extra_section in sections[section_count:]:
        if not isinstance(extra_section, Mapping):
            continue
        merged_tail["assigned_claim_ids"] = _route_0506_unique_string_list(
            [
                *(
                    merged_tail.get("assigned_claim_ids")
                    if isinstance(merged_tail.get("assigned_claim_ids"), list)
                    else []
                ),
                *(
                    extra_section.get("assigned_claim_ids")
                    if isinstance(extra_section.get("assigned_claim_ids"), list)
                    else []
                ),
            ]
        )
        if isinstance(merged_tail.get("discourse_rules"), list) and isinstance(extra_section.get("discourse_rules"), list):
            merged_tail["discourse_rules"] = _route_0506_append_unique_strings(
                list(merged_tail["discourse_rules"]),
                [str(rule) for rule in extra_section["discourse_rules"]],
            )
    retained[-1] = merged_tail
    return retained


def _route_0506_enrich_company_intro_sections_for_fullness(sections: list[Any]) -> list[Any]:
    enriched: list[Any] = []
    total_claim_count = len(
        _route_0506_unique_string_list(
            claim_id
            for section in sections
            if isinstance(section, Mapping)
            for claim_id in _route_0506_section_claim_ids(section)
        )
    )
    for section in sections:
        if not isinstance(section, Mapping):
            enriched.append(section)
            continue
        next_section = dict(section)
        discourse_rules = next_section.get("discourse_rules")
        if isinstance(discourse_rules, list):
            assigned_claim_count = len(_route_0506_section_claim_ids(next_section))
            additions: list[str] = []
            if total_claim_count > 0 and _route_0506_company_intro_has_dense_section_load(
                assigned_claim_count,
                assigned_claim_count / total_claim_count,
            ):
                additions.extend(COMPANY_INTRO_DENSITY_SECTION_RULES)
            additions.extend(COMPANY_INTRO_FULLNESS_SECTION_RULES)
            next_section["discourse_rules"] = _route_0506_append_unique_strings(
                discourse_rules,
                additions,
            )
        enriched.append(next_section)
    return enriched


def _route_0506_claim_allocation_from_sections(
    claim_allocation: list[Any],
    sections: list[Any],
) -> list[dict[str, Any]]:
    reuse_by_section: dict[str, bool] = {}
    for item in claim_allocation:
        if not isinstance(item, Mapping):
            continue
        section_id = str(item.get("section_id") or "").strip()
        if section_id:
            reuse_by_section[section_id] = bool(item.get("reuse_allowed"))

    normalized: list[dict[str, Any]] = []
    for section in sections:
        if not isinstance(section, Mapping):
            continue
        section_id = str(section.get("section_id") or "").strip()
        if not section_id:
            continue
        assigned_claim_ids = section.get("assigned_claim_ids")
        normalized.append(
            {
                "section_id": section_id,
                "claim_ids": _route_0506_unique_string_list(assigned_claim_ids if isinstance(assigned_claim_ids, list) else []),
                "reuse_allowed": reuse_by_section.get(section_id, False),
            }
        )
    return normalized
