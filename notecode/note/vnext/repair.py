"""Local repair operations for vNext."""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

from .types import FactCard, RenderedSection, SectionBrief, VNextThinContract


def _fact_lookup(contract: VNextThinContract) -> Dict[str, FactCard]:
    return {item.fact_id: item for item in contract.fact_cards}


def _rewrite_from_brief(contract: VNextThinContract, brief: SectionBrief) -> str:
    facts = _fact_lookup(contract)
    lines = [f"{brief.primary_claim}。"]
    for fact_id in brief.supporting_fact_ids[:2]:
        fact = facts.get(fact_id)
        if fact is None:
            continue
        lines.append(f"{fact.fact_text.rstrip('。')}。")
    lines.append(f"{brief.reader_question.rstrip('？')}に対しては、{brief.must_keep_terms[0] if brief.must_keep_terms else '判断材料'}を基準に整理すると重複しにくくなります。")
    first_chunk = " ".join(lines[:2]).strip()
    second_chunk = " ".join(lines[2:]).strip()
    return "\n\n".join(chunk for chunk in (first_chunk, second_chunk) if chunk)


def _restore_ambiguous_subjects(text: str, contract: VNextThinContract, brief: SectionBrief) -> str:
    sentences = [item.strip() for item in re.split(r"(?<=[。！？])", str(text or "")) if item.strip()]
    if not sentences:
        return text
    subject = brief.must_keep_terms[0] if brief.must_keep_terms else (contract.topic_statement or contract.speaker_profile)
    repaired: List[str] = []
    for index, sentence in enumerate(sentences):
        if index == 0 and re.match(r"^(この|その|それ|こちら|これら)", sentence):
            repaired.append(f"{subject}について言えば、{sentence}")
        else:
            repaired.append(sentence)
    return " ".join(repaired).strip()


def _reflow_paragraphs(text: str) -> str:
    sentences = [item.strip() for item in re.split(r"(?<=[。！？])", str(text or "")) if item.strip()]
    if len(sentences) <= 2:
        return text
    paragraphs: List[str] = []
    chunk: List[str] = []
    for sentence in sentences:
        chunk.append(sentence)
        if len(chunk) >= 2:
            paragraphs.append(" ".join(chunk).strip())
            chunk = []
    if chunk:
        if paragraphs:
            paragraphs[-1] = f"{paragraphs[-1]} {' '.join(chunk).strip()}".strip()
        else:
            paragraphs.append(" ".join(chunk).strip())
    return "\n\n".join(paragraphs)


def _vary_sentence_endings(text: str) -> str:
    replacements = {
        "です。": "といえます。",
        "ます。": "ました。",
        "でした。": "です。",
        "となります。": "です。",
    }
    sentences = [item.strip() for item in re.split(r"(?<=[。！？])", str(text or "")) if item.strip()]
    if len(sentences) < 3:
        return text
    repaired: List[str] = []
    previous_ending = ""
    run_length = 0
    for sentence in sentences:
        ending = next((suffix for suffix in replacements if sentence.endswith(suffix)), "")
        if ending and ending == previous_ending:
            run_length += 1
        else:
            run_length = 1
            previous_ending = ending
        if ending and run_length >= 3:
            repaired.append(sentence[: -len(ending)] + replacements[ending])
            previous_ending = replacements[ending]
            run_length = 1
        else:
            repaired.append(sentence)
    return " ".join(repaired).strip()


def apply_local_repairs(
    contract: VNextThinContract,
    briefs: List[SectionBrief],
    sections: List[RenderedSection],
    evaluation_report: Dict[str, object],
) -> Tuple[List[RenderedSection], Dict[str, object]]:
    evaluation_lookup = {
        str(item.get("section_id") or ""): item
        for item in list(evaluation_report.get("section_evaluations") or [])
        if isinstance(item, dict)
    }
    brief_lookup = {item.section_id: item for item in briefs}
    repaired_sections: List[RenderedSection] = []
    actions: List[Dict[str, object]] = []
    for section in sections:
        body = str(section.body or "")
        evaluation = dict(evaluation_lookup.get(section.section_id) or {})
        brief = brief_lookup.get(section.section_id)
        mandatory_repairs = list(evaluation.get("mandatory_repairs") or [])
        for action in mandatory_repairs:
            if action == "replace_overlapped_section":
                if contract.preservation_policy == "high_preservation":
                    actions.append(
                        {
                            "section_id": section.section_id,
                            "action": action,
                            "applied": False,
                            "blocked_reason": "high_preservation_surface_only",
                        }
                    )
                    continue
                if brief is not None:
                    body = _rewrite_from_brief(contract, brief)
                    actions.append({"section_id": section.section_id, "action": action, "applied": True})
            elif action == "restore_ambiguous_subjects" and brief is not None:
                updated = _restore_ambiguous_subjects(body, contract, brief)
                actions.append(
                    {
                        "section_id": section.section_id,
                        "action": action,
                        "applied": updated != body,
                    }
                )
                body = updated
            elif action == "reflow_paragraphs":
                updated = _reflow_paragraphs(body)
                actions.append({"section_id": section.section_id, "action": action, "applied": updated != body})
                body = updated
            elif action == "vary_sentence_endings":
                updated = _vary_sentence_endings(body)
                actions.append({"section_id": section.section_id, "action": action, "applied": updated != body})
                body = updated
        repaired_sections.append(
            RenderedSection(
                section_id=section.section_id,
                heading=section.heading,
                body=body,
                supporting_fact_ids=list(section.supporting_fact_ids),
            )
        )
    return repaired_sections, {"actions": actions, "surface_only_preservation": contract.preservation_policy == "high_preservation"}
