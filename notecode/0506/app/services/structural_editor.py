from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.stylometry import analyze_text, split_sentences


FIRST_PERSON_VARIANTS = ("私たち", "当社", "弊社", "当店")
THIRD_PARTY_SELF_TERMS = ("同社", "同サービス", "同店", "同院")


@dataclass(frozen=True)
class StructuralEditResult:
    text: str
    report: dict[str, Any]


def run_structural_editor(text: str, article_brief: dict[str, Any]) -> StructuralEditResult:
    brief = article_brief["article_brief"]
    policy = brief.get("editor_pass_policy", {})
    narrator = brief["narrator"]

    revised = text
    if policy.get("align_first_person_to_narrator", True):
        revised = _align_first_person(revised, narrator)
    if policy.get("focus_late_half", True):
        revised = _split_late_long_paragraphs(
            revised,
            int(policy.get("split_late_paragraph_over_sentences", 2)),
        )

    return StructuralEditResult(
        text=revised,
        report=build_structural_edit_report(text, revised, article_brief),
    )


def build_structural_edit_report(before_text: str, after_text: str, article_brief: dict[str, Any]) -> dict[str, Any]:
    brief = article_brief["article_brief"]
    narrator = brief["narrator"]
    before = analyze_text(before_text)
    after = analyze_text(after_text)
    return {
        "editor_profile_id": brief.get("editor_profile_id"),
        "focus": "late_half_structure_and_whole_article_consistency",
        "changed": after_text != before_text,
        "checks": {
            "late_half_paragraph_split": before["paragraph_shape"] != after["paragraph_shape"],
            "first_person_aligned": _variants_outside_narrator(after_text, narrator) == [],
            "source_grounding_policy_changed": False,
            "qa_threshold_changed": False,
        },
        "before": {
            "paragraph_shape": before["paragraph_shape"],
            "ending_distribution": before["ending_distribution"],
            "first_person_variants": before["first_person_variants"],
            "third_party_terms": before["third_party_terms"],
        },
        "after": {
            "paragraph_shape": after["paragraph_shape"],
            "ending_distribution": after["ending_distribution"],
            "first_person_variants": after["first_person_variants"],
            "third_party_terms": after["third_party_terms"],
        },
    }


def _align_first_person(text: str, narrator: str) -> str:
    result = text
    for term in FIRST_PERSON_VARIANTS:
        if term != narrator:
            result = result.replace(term, narrator)
    for term in THIRD_PARTY_SELF_TERMS:
        result = result.replace(term, narrator)
    return result


def _split_late_long_paragraphs(text: str, split_over: int) -> str:
    blocks = [block.strip() for block in text.strip().split("\n\n") if block.strip()]
    body_indexes = [index for index, block in enumerate(blocks) if not block.startswith("#")]
    if not body_indexes:
        return text.strip()
    late_start = body_indexes[len(body_indexes) // 2]
    output: list[str] = []
    for index, block in enumerate(blocks):
        if block.startswith("#") or index < late_start:
            output.append(block)
            continue
        sentences = split_sentences(block)
        if len(sentences) <= split_over:
            output.append(block)
            continue
        output.append("".join(sentences[:split_over]))
        output.append("".join(sentences[split_over:]))
    return "\n\n".join(output)


def _variants_outside_narrator(text: str, narrator: str) -> list[str]:
    variants = [term for term in FIRST_PERSON_VARIANTS if term != narrator and term in text]
    variants.extend(term for term in THIRD_PARTY_SELF_TERMS if term in text)
    return variants
