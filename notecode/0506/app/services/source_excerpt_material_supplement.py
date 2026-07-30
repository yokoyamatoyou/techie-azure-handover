from __future__ import annotations

import re
from typing import Any, Callable

COMPANY_INTRO_MIN_SELECTED_MATERIAL_CHARS = 2300
COMPANY_INTRO_NOVELTY_OVERLAP_MAX = 0.72

BuildExcerpt = Callable[[str, list[str], int], dict[str, Any] | None]
DedupeKey = Callable[[str], str]
CleanText = Callable[[str], str]
BestChunkForClaim = Callable[[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]], dict[str, Any] | None]
RefsForClaim = Callable[[dict[str, Any], dict[str, list[dict[str, Any]]]], list[dict[str, Any]]]
AnchorTexts = Callable[[dict[str, Any], list[dict[str, Any]]], list[str]]
ExcerptText = Callable[[str, list[str], int], str]


def supplement_company_intro_thin_material(
    brief: dict[str, Any],
    excerpts: list[dict[str, Any]],
    seen_texts: set[str],
    used_chars: int,
    total_limit: int,
    max_excerpts: int,
    claims: dict[str, dict[str, Any]],
    chunks: list[dict[str, Any]],
    assigned_ids: set[str],
    assigned_claim_groups: list[tuple[str, list[str]]],
    *,
    build_excerpt: BuildExcerpt,
    dedupe_key: DedupeKey,
    clean_text: CleanText,
) -> None:
    if not _should_supplement(brief, excerpts, chunks, used_chars, total_limit, clean_text):
        return
    section_ids = [section_id for section_id, _claim_ids in assigned_claim_groups]
    support_section_ids = [section_ids[-1]] if section_ids else []
    selected_claim_ids = {claim_id for excerpt in excerpts for claim_id in excerpt.get("claim_ids") or []}
    candidates = _supplement_candidates(
        brief,
        excerpts,
        claims,
        selected_claim_ids,
        support_section_ids,
        total_limit,
        build_excerpt,
    )
    for candidate in candidates:
        if used_chars >= COMPANY_INTRO_MIN_SELECTED_MATERIAL_CHARS:
            break
        if len(excerpts) < max_excerpts:
            if not _is_novel_excerpt(candidate["text"], [excerpt["text"] for excerpt in excerpts]):
                continue
            _append_built_excerpt(excerpts, seen_texts, candidate, dedupe_key)
            used_chars += len(candidate["text"])
            continue
        replace_index = _replaceable_short_excerpt_index(excerpts, assigned_ids, candidate)
        if replace_index is None:
            continue
        replacement_basis = [excerpt["text"] for index, excerpt in enumerate(excerpts) if index != replace_index]
        if not _is_novel_excerpt(candidate["text"], replacement_basis):
            continue
        used_chars += len(candidate["text"]) - len(str(excerpts[replace_index].get("text") or ""))
        seen_texts.discard(dedupe_key(str(excerpts[replace_index].get("text") or "")))
        excerpts[replace_index] = candidate
        seen_texts.add(dedupe_key(candidate["text"]))
        _renumber_excerpts(excerpts)


def lexical_overlap(left: str, right: str) -> float:
    left_terms = set(_text_ngrams(left))
    right_terms = set(_text_ngrams(right))
    if not left_terms or not right_terms:
        return 0.0
    return len(left_terms & right_terms) / max(1, min(len(left_terms), len(right_terms)))


def build_source_excerpt(
    claims: dict[str, dict[str, Any]],
    chunks: list[dict[str, Any]],
    fact_refs: dict[str, list[dict[str, Any]]],
    claim_id: str,
    section_ids: list[str],
    max_chars: int,
    *,
    best_chunk_for_claim: BestChunkForClaim,
    refs_for_claim: RefsForClaim,
    anchor_texts: AnchorTexts,
    excerpt_text: ExcerptText,
) -> dict[str, Any] | None:
    claim = claims.get(claim_id)
    if not claim:
        return None
    chunk = best_chunk_for_claim(chunks, fact_refs, claim)
    if not chunk:
        return None
    refs = refs_for_claim(claim, fact_refs)
    text = excerpt_text(str(chunk.get("text") or ""), anchor_texts(claim, refs), max_chars)
    if not text:
        return None
    return {
        "excerpt_id": "",
        "source_id": str(chunk.get("source_id") or ""),
        "source_type": str(chunk.get("source_type") or ""),
        "title": str(chunk.get("title") or ""),
        "chunk_id": str(chunk.get("chunk_id") or ""),
        "source_span_ids": list(chunk.get("source_span_ids") or []),
        "source_locations": list(chunk.get("source_locations") or []),
        "claim_ids": [claim_id],
        "section_ids": section_ids,
        "usage": "route_v_writer_context",
        "text": text,
    }


def _should_supplement(
    brief: dict[str, Any],
    excerpts: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    used_chars: int,
    total_limit: int,
    clean_text: CleanText,
) -> bool:
    return (
        str(brief.get("genre_id") or "") == "company_service_intro"
        and str(brief.get("source_use_mode") or "") == "selective"
        and str(brief.get("source_shape") or "") != "table_or_list"
        and total_limit == 2600
        and used_chars < COMPANY_INTRO_MIN_SELECTED_MATERIAL_CHARS
        and sum(len(clean_text(str(chunk.get("text") or ""))) for chunk in chunks) >= COMPANY_INTRO_MIN_SELECTED_MATERIAL_CHARS
        and bool(excerpts)
    )


def _supplement_candidates(
    brief: dict[str, Any],
    excerpts: list[dict[str, Any]],
    claims: dict[str, dict[str, Any]],
    selected_claim_ids: set[str],
    section_ids: list[str],
    total_limit: int,
    build_excerpt: BuildExcerpt,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    current_texts = [str(excerpt.get("text") or "") for excerpt in excerpts]
    for claim_id in [str(value) for value in brief.get("unassigned_claim_ids") or [] if str(value)]:
        if claim_id in selected_claim_ids:
            continue
        claim = claims.get(claim_id)
        if not claim or claim.get("risk_flags"):
            continue
        candidate = build_excerpt(claim_id, section_ids, min(650, total_limit))
        if not candidate or not _is_novel_excerpt(candidate["text"], current_texts):
            continue
        result.append(candidate)
    result.sort(key=lambda item: (-len(str(item.get("text") or "")), item["claim_ids"][0]))
    return result


def _append_built_excerpt(
    excerpts: list[dict[str, Any]],
    seen_texts: set[str],
    excerpt: dict[str, Any],
    dedupe_key: DedupeKey,
) -> None:
    excerpt["excerpt_id"] = f"E{len(excerpts) + 1:03d}"
    seen_texts.add(dedupe_key(str(excerpt.get("text") or "")))
    excerpts.append(excerpt)


def _replaceable_short_excerpt_index(
    excerpts: list[dict[str, Any]],
    assigned_ids: set[str],
    candidate: dict[str, Any],
) -> int | None:
    candidate_len = len(str(candidate.get("text") or ""))
    replaceable: list[tuple[int, int]] = []
    for index, excerpt in enumerate(excerpts):
        claim_ids = {str(claim_id) for claim_id in excerpt.get("claim_ids") or []}
        if claim_ids & assigned_ids:
            continue
        excerpt_len = len(str(excerpt.get("text") or ""))
        if candidate_len > excerpt_len:
            replaceable.append((excerpt_len, index))
    return min(replaceable)[1] if replaceable else None


def _is_novel_excerpt(text: str, existing_texts: list[str]) -> bool:
    return all(lexical_overlap(text, existing) <= COMPANY_INTRO_NOVELTY_OVERLAP_MAX for existing in existing_texts if existing)


def _text_ngrams(text: str) -> list[str]:
    normalized = re.sub(r"\s+", "", str(text or ""))
    ngram_size = 6
    if len(normalized) < ngram_size:
        return [normalized] if normalized else []
    return [normalized[index : index + ngram_size] for index in range(len(normalized) - ngram_size + 1)]


def _renumber_excerpts(excerpts: list[dict[str, Any]]) -> None:
    for index, excerpt in enumerate(excerpts, start=1):
        excerpt["excerpt_id"] = f"E{index:03d}"
