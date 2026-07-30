from __future__ import annotations

import re
from dataclasses import asdict, is_dataclass
from typing import Any

from app.services.source_excerpt_material_supplement import build_source_excerpt, supplement_company_intro_thin_material
from app.services.source_excerpt_coverage_contract import build_assigned_claim_groups, build_final_usage_support_claim_sections

MAX_EXCERPTS = 6
MAX_EXCERPT_CHARS = 650
MAX_TOTAL_CHARS_SELECTIVE = 2600
MAX_TOTAL_CHARS_EXHAUSTIVE = 3400

def build_selected_source_excerpts_v2(
    article_brief: dict[str, Any],
    knowledge_pack: dict[str, Any],
    source_cards: list[dict[str, Any]],
    source_packets: list[Any],
) -> list[dict[str, Any]]:
    """Build bounded source excerpts for Route V writer context only."""
    brief = article_brief.get("article_brief", {}) if isinstance(article_brief, dict) else {}
    if not _is_route_v_brief(brief):
        return []

    assigned_claim_groups = build_assigned_claim_groups(brief)
    if not assigned_claim_groups:
        return []

    claims = _claims_by_id(knowledge_pack)
    chunks = _packet_chunks(source_packets)
    if not claims or not chunks:
        return []

    fact_refs = _fact_refs(source_cards)
    section_count = int(brief.get("section_count") or 0)
    max_excerpts = min(MAX_EXCERPTS, max(3, section_count + 2))
    total_limit = (
        MAX_TOTAL_CHARS_EXHAUSTIVE
        if str(brief.get("source_use_mode") or "") == "exhaustive"
        else MAX_TOTAL_CHARS_SELECTIVE
    )

    excerpts: list[dict[str, Any]] = []
    seen_texts: set[str] = set()
    attempted_claims: set[str] = set()
    used_chars = 0
    for section_id, claim_ids in assigned_claim_groups:
        for claim_id in claim_ids:
            attempted_claims.add(claim_id)
            added, used_chars = _try_append_excerpt(
                excerpts, seen_texts, used_chars, total_limit, max_excerpts, claims, chunks, fact_refs, claim_id, [section_id]
            )
            if added:
                break

    assigned_ids = {claim_id for _section_id, claim_ids in assigned_claim_groups for claim_id in claim_ids}
    support_claim_sections = build_final_usage_support_claim_sections(brief, knowledge_pack, assigned_ids)
    for claim_id, section_ids in support_claim_sections.items():
        attempted_claims.add(claim_id)
        _added, used_chars = _try_append_excerpt(
            excerpts, seen_texts, used_chars, total_limit, max_excerpts, claims, chunks, fact_refs, claim_id, section_ids
        )

    for section_id, claim_ids in assigned_claim_groups:
        for claim_id in claim_ids:
            if claim_id in attempted_claims:
                continue
            _added, used_chars = _try_append_excerpt(
                excerpts, seen_texts, used_chars, total_limit, max_excerpts, claims, chunks, fact_refs, claim_id, [section_id]
    )
    supplement_company_intro_thin_material(
        brief,
        excerpts,
        seen_texts,
        used_chars,
        total_limit,
        max_excerpts,
        claims,
        chunks,
        assigned_ids,
        assigned_claim_groups,
        build_excerpt=lambda claim_id, section_ids, max_chars: build_source_excerpt(
            claims, chunks, fact_refs, claim_id, section_ids, max_chars,
            best_chunk_for_claim=_best_chunk_for_claim, refs_for_claim=_refs_for_claim,
            anchor_texts=_anchor_texts, excerpt_text=_excerpt_text,
        ),
        dedupe_key=_dedupe_key,
        clean_text=_clean_text,
    )
    return excerpts


def _try_append_excerpt(
    excerpts: list[dict[str, Any]],
    seen_texts: set[str],
    used_chars: int,
    total_limit: int,
    max_excerpts: int,
    claims: dict[str, dict[str, Any]],
    chunks: list[dict[str, Any]],
    fact_refs: dict[str, list[dict[str, Any]]],
    claim_id: str,
    section_ids: list[str],
) -> tuple[bool, int]:
    if len(excerpts) >= max_excerpts or used_chars >= total_limit:
        return False, used_chars
    excerpt = build_source_excerpt(
        claims, chunks, fact_refs, claim_id, section_ids, min(MAX_EXCERPT_CHARS, total_limit - used_chars),
        best_chunk_for_claim=_best_chunk_for_claim, refs_for_claim=_refs_for_claim,
        anchor_texts=_anchor_texts, excerpt_text=_excerpt_text,
    )
    if not excerpt:
        return False, used_chars
    key = _dedupe_key(excerpt["text"])
    if key in seen_texts:
        return False, used_chars
    seen_texts.add(key)
    excerpt["excerpt_id"] = f"E{len(excerpts) + 1:03d}"
    excerpts.append(excerpt)
    return True, used_chars + len(excerpt["text"])


def _is_route_v_brief(brief: dict[str, Any]) -> bool:
    return (
        isinstance(brief, dict)
        and brief.get("voice_mode") == "self_authored_blogger"
        and bool(brief.get("source_shape"))
        and bool(brief.get("source_use_mode"))
    )


def _claims_by_id(knowledge_pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pack = knowledge_pack.get("article_knowledge_pack", {}) if isinstance(knowledge_pack, dict) else {}
    claims = pack.get("confirmed_facts") if isinstance(pack, dict) else []
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(claims, list):
        return result
    for claim in claims:
        if isinstance(claim, dict) and claim.get("claim_id"):
            result[str(claim["claim_id"])] = claim
    return result


def _fact_refs(source_cards: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    refs: dict[str, list[dict[str, Any]]] = {}
    for card in source_cards:
        if not isinstance(card, dict):
            continue
        for fact in card.get("facts") or []:
            if not isinstance(fact, dict) or not fact.get("fact_id"):
                continue
            refs.setdefault(str(fact["fact_id"]), []).append(
                {
                    "source_id": str(card.get("source_id") or ""),
                    "source_span": str(fact.get("source_span") or ""),
                    "claim": str(fact.get("claim") or ""),
                }
            )
    return refs


def _packet_chunks(source_packets: list[Any]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for packet in source_packets:
        packet_dict = _as_dict(packet)
        title = str(packet_dict.get("title") or "")
        for chunk in packet_dict.get("chunks") or []:
            chunk_dict = _as_dict(chunk)
            chunk_dict["title"] = title
            chunks.append(chunk_dict)
    return chunks


def _best_chunk_for_claim(
    chunks: list[dict[str, Any]],
    fact_refs: dict[str, list[dict[str, Any]]],
    claim: dict[str, Any],
) -> dict[str, Any] | None:
    refs = _refs_for_claim(claim, fact_refs)
    anchors = _anchor_texts(claim, refs)
    scored: list[tuple[int, int, dict[str, Any]]] = []
    for index, chunk in enumerate(chunks):
        score = 0
        span_ids = {str(value) for value in chunk.get("source_span_ids") or []}
        locations = {str(value) for value in chunk.get("source_locations") or []}
        source_id = str(chunk.get("source_id") or "")
        for ref in refs:
            source_span = str(ref.get("source_span") or "")
            if source_span and (source_span in span_ids or source_span in locations):
                score += 6
            if source_id and source_id == str(ref.get("source_id") or ""):
                score += 2
        if any(_find_anchor(chunk.get("text") or "", anchor) >= 0 for anchor in anchors):
            score += 3
        if score:
            scored.append((score, -index, chunk))
    return max(scored, key=lambda item: (item[0], item[1]))[2] if scored else None


def _refs_for_claim(claim: dict[str, Any], fact_refs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    refs = [ref for fact_id in claim.get("supporting_fact_ids") or [] for ref in fact_refs.get(str(fact_id), [])]
    if len(refs) <= 1:
        return refs
    claim_terms = set(_meaningful_terms(" ".join([str(claim.get("preferred_expression") or ""), str(claim.get("claim") or "")])))
    scored = [(_term_overlap_score(claim_terms, str(ref.get("claim") or "")), ref) for ref in refs]
    best = max((score for score, _ref in scored), default=0)
    return [ref for score, ref in scored if score == best] if best > 0 else []

def _anchor_texts(claim: dict[str, Any], refs: list[dict[str, Any]]) -> list[str]:
    values = [str(claim.get("preferred_expression") or ""), str(claim.get("claim") or "")]
    values.extend(str(ref.get("claim") or "") for ref in refs)
    anchors: list[str] = []
    for value in values:
        text = _clean_text(value)
        if not text:
            continue
        anchors.append(text)
        anchors.extend(_meaningful_terms(text))
    return _unique_strings(anchors)

def _excerpt_text(source_text: str, anchors: list[str], max_chars: int) -> str:
    text = _clean_text(source_text)
    if not text:
        return ""
    if len(text) <= max(160, max_chars):
        return text[:max_chars]
    anchor_index = -1
    for anchor in anchors:
        anchor_index = _find_anchor(text, anchor)
        if anchor_index >= 0:
            break
    if anchor_index < 0:
        anchor_index = 0
    start = max(0, anchor_index - 180)
    end = min(len(text), start + max_chars)
    start = max(0, end - max_chars)
    excerpt = text[start:end].strip()
    if start > 0:
        excerpt = "..." + excerpt
    if end < len(text):
        excerpt = excerpt + "..."
    if len(excerpt) > max_chars:
        excerpt = excerpt[:max_chars].rstrip()
    return excerpt

def _find_anchor(text: str, anchor: str) -> int:
    if not text or not anchor:
        return -1
    if anchor in text:
        return text.find(anchor)
    for term in _meaningful_terms(anchor):
        index = text.find(term)
        if index >= 0:
            return index
    return -1

def _term_overlap_score(terms: set[str], text: str) -> int:
    return sum(1 for term in terms if term and term in text)

def _meaningful_terms(text: str) -> list[str]:
    terms = [match.strip() for match in re.findall(r"[「『]([^」』]{2,32})[」』]", text)]
    for piece in re.split(r"[\s,，、。:：;；/|()（）\[\]「」『』]+", text):
        cleaned = piece.strip()
        if len(cleaned) >= 5:
            terms.append(cleaned[:32])
            if len(cleaned) >= 12:
                terms.extend([cleaned[:16], cleaned[:10]])
        elif len(cleaned) >= 3 and re.search(r"[A-Za-z0-9]", cleaned):
            terms.append(cleaned)
    if not terms and len(text) >= 8:
        terms.append(text[:32])
    return terms[:8]

def _clean_text(text: str) -> str:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    return "\n".join(lines).strip()

def _dedupe_key(text: str) -> str:
    return re.sub(r"\s+", "", text)[:240]

def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result

def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if is_dataclass(value):
        return asdict(value)
    return {}
