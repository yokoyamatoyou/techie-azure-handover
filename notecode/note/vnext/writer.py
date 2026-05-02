"""Minimal section writer for vNext."""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from note.llm_client import LLMClient

from .types import FactCard, RenderedSection, SectionBrief, VNextThinContract


def _fact_lookup(contract: VNextThinContract) -> Dict[str, FactCard]:
    return {item.fact_id: item for item in contract.fact_cards}


def _opening_line(contract: VNextThinContract, brief: SectionBrief, index: int) -> str:
    if contract.article_type == "announcement":
        return f"{brief.primary_claim}。"
    if brief.narrator_visibility == "visible":
        return f"{contract.speaker_profile}の立場から見ると、{brief.primary_claim}。"
    if index == 0:
        return f"{brief.primary_claim}。"
    return f"{brief.heading}では、{brief.primary_claim}。"


def _fact_lines(contract: VNextThinContract, brief: SectionBrief, facts: Dict[str, FactCard]) -> List[str]:
    lines: List[str] = []
    for fact_id in brief.supporting_fact_ids[:2]:
        fact = facts.get(fact_id)
        if fact is None:
            continue
        if contract.evidence_style == "fact_first" or contract.article_type == "announcement":
            lines.append(f"{fact.fact_text.rstrip('。')}。")
        else:
            lines.append(f"{fact.fact_text.rstrip('。')}ことが、{brief.primary_claim.rstrip('。')}背景になります。")
    return lines


def _closing_line(contract: VNextThinContract, brief: SectionBrief, index: int, section_count: int) -> str:
    if brief.section_role in {"action", "reuse_condition", "decision_hint", "reader_connection"}:
        return f"{brief.reader_question.rstrip('？')}に向けて、次に確認する順番をそろえておくと判断しやすくなります。"
    if index == section_count - 1:
        return f"{brief.primary_claim.rstrip('。')}という理解を残しておくと、次の判断につなげやすくなります。"
    return f"{brief.reader_question.rstrip('？')}を次の節で受け止めます。"


def _render_without_llm(contract: VNextThinContract, brief: SectionBrief, index: int, section_count: int) -> str:
    facts = _fact_lookup(contract)
    sentences = [_opening_line(contract, brief, index)]
    sentences.extend(_fact_lines(contract, brief, facts))
    if not brief.supporting_fact_ids:
        sentences.append(f"{brief.reader_question.rstrip('？')}を起点に、{brief.primary_claim.rstrip('。')}形で整理します。")
    sentences.append(_closing_line(contract, brief, index, section_count))
    first_chunk = " ".join(sentences[:2]).strip()
    second_chunk = " ".join(sentences[2:]).strip()
    chunks = [chunk for chunk in (first_chunk, second_chunk) if chunk]
    return "\n\n".join(chunks)


def _llm_prompt(contract: VNextThinContract, brief: SectionBrief, facts: Dict[str, FactCard]) -> str:
    fact_lines = [facts[item].fact_text for item in brief.supporting_fact_ids if item in facts][:2]
    evidence = "\n".join(f"- {item}" for item in fact_lines) or "- 追加の根拠はない"
    return (
        "役割に沿って日本語ブログ本文の1節だけを書く。\n"
        f"記事タイプ: {contract.article_type}\n"
        f"discourse_mode: {contract.discourse_mode}\n"
        f"heading: {brief.heading}\n"
        f"role: {brief.section_role}\n"
        f"primary_claim: {brief.primary_claim}\n"
        f"reader_question: {brief.reader_question}\n"
        f"speaker_profile: {contract.speaker_profile}\n"
        f"audience_profile: {contract.audience_profile}\n"
        f"must_keep_terms: {', '.join(brief.must_keep_terms)}\n"
        "source facts:\n"
        f"{evidence}\n"
        "ルール:\n"
        "- 8行以内の短い節にする\n"
        "- 同じ主張を繰り返さない\n"
        "- 見出しは出力しない\n"
        "- 日本語で自然な段落にする"
    )


def _render_with_llm(
    contract: VNextThinContract,
    brief: SectionBrief,
    llm_client: LLMClient,
) -> str:
    facts = _fact_lookup(contract)
    text = llm_client.generate_text(
        _llm_prompt(contract, brief, facts),
        max_tokens=380,
        task_type="section",
    )
    return str(text or "").strip()


def render_sections(
    contract: VNextThinContract,
    briefs: List[SectionBrief],
    *,
    llm_client: Optional[LLMClient] = None,
    allow_llm: bool = False,
) -> List[RenderedSection]:
    rendered: List[RenderedSection] = []
    for index, brief in enumerate(briefs):
        if allow_llm and llm_client is not None:
            body = _render_with_llm(contract, brief, llm_client)
        else:
            body = _render_without_llm(contract, brief, index, len(briefs))
        rendered.append(
            RenderedSection(
                section_id=brief.section_id,
                heading=brief.heading,
                body=str(body or "").strip(),
                supporting_fact_ids=list(brief.supporting_fact_ids),
            )
        )
    return rendered
