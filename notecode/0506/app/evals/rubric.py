from __future__ import annotations

from dataclasses import dataclass


QUALITY_AXES = [
    "source_grounding",
    "self_perspective_consistency",
    "first_person_consistency",
    "third_party_viewpoint_leakage",
    "paragraph_rhythm",
    "line_break_naturalness",
    "ending_bucket_monotony",
    "model_frequent_words",
    "generic_encouragement",
    "note_hatena_readability",
    "cta_naturalness",
]


ISSUE_TO_OWNER = {
    "unsupported_claim": "source_card_extractor",
    "first_person_inconsistency": "article_brief_builder",
    "subject_ambiguity": "japanese_quality_checker",
    "zero_anaphora_risk": "japanese_quality_checker",
    "duplication": "knowledge_pack_integrator",
    "ai_like_phrase": "style_editor",
    "style_mismatch": "style_editor",
    "cta_issue": "article_brief_builder",
    "forbidden_phrase": "style_editor",
    "sentence_too_long": "style_editor",
    "ending_repetition": "style_editor",
    "connector_repetition": "style_editor",
    "paragraph_rhythm_monotony": "style_editor",
    "line_break_monotony": "style_editor",
    "ending_bucket_monotony": "style_editor",
    "model_frequent_word": "style_editor",
    "generic_encouragement_phrase": "style_editor",
    "third_party_viewpoint_leakage": "article_brief_builder",
    "narrator_mixing": "article_brief_builder",
    "company_name_overuse_as_narrator": "article_brief_builder",
    "unattributed_customer_voice": "source_card_extractor",
    "genre_role_mismatch": "persona_selection",
    "sentence_rhythm_monotony": "style_editor",
    "nominalization_overuse": "style_editor",
    "formatting_mismatch": "style_editor",
    "body_length_below_floor": "draft_writer",
    "missing_h1": "draft_writer",
}


@dataclass(frozen=True)
class RubricResult:
    axis: str
    passed: bool
    reason: str


def evaluate_rubric(article_text: str, quality_check: dict, expected: dict) -> list[RubricResult]:
    issues = quality_check["quality_check"]["issues"]
    issue_types = {issue["type"] for issue in issues}
    forbidden_terms = expected.get("forbidden_terms", [])
    required_narrator = expected.get("required_narrator")

    return [
        RubricResult(
            "source_grounding",
            "unsupported_claim" not in issue_types,
            "unsupported_claim issue must be absent for fixture acceptance",
        ),
        RubricResult(
            "self_perspective_consistency",
            all(term not in article_text for term in forbidden_terms),
            "forbidden third-party viewpoint terms must not appear",
        ),
        RubricResult(
            "first_person_consistency",
            bool(required_narrator and required_narrator in article_text),
            "required narrator must appear in final article",
        ),
        RubricResult(
            "third_party_viewpoint_leakage",
            "third_party_viewpoint_leakage" not in issue_types,
            "third-party viewpoint leakage must be absent",
        ),
        RubricResult(
            "paragraph_rhythm",
            "paragraph_rhythm_monotony" not in issue_types,
            "paragraph rhythm monotony should be flagged if present",
        ),
        RubricResult(
            "line_break_naturalness",
            "line_break_monotony" not in issue_types,
            "line-break monotony should be flagged if present",
        ),
        RubricResult(
            "ending_bucket_monotony",
            "ending_bucket_monotony" not in issue_types,
            "ending bucket monotony should be flagged if present",
        ),
        RubricResult(
            "model_frequent_words",
            "model_frequent_word" not in issue_types,
            "model-frequent words should be flagged if repeated",
        ),
        RubricResult(
            "generic_encouragement",
            "generic_encouragement_phrase" not in issue_types,
            "generic encouragement should be flagged if present",
        ),
        RubricResult(
            "note_hatena_readability",
            len(article_text.splitlines()) >= 3,
            "final article should keep readable line structure",
        ),
        RubricResult(
            "cta_naturalness",
            "cta_issue" not in issue_types,
            "CTA issues should be absent or explicitly reported",
        ),
    ]


def diagnose_issue_owners(quality_check: dict) -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for issue in quality_check["quality_check"]["issues"]:
        issue_type = issue["type"]
        owner = ISSUE_TO_OWNER.get(issue_type, "unknown")
        owners.setdefault(owner, []).append(issue_type)
    return owners
