"""Evaluator and repair trigger mapping for vNext."""
from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any, Dict, List

from core.app_config import get_vnext_overlap_runtime_config

from .types import RenderedSection, SectionBrief, VNextThinContract

_TOKEN_RE = re.compile(r"[A-Za-z0-9一-龥ぁ-んァ-ヶー]{2,24}")
_STOPWORDS = {"こと", "もの", "ため", "これ", "それ", "ここ", "そこ", "読者", "記事", "判断", "整理"}
_ENDING_RE = re.compile(r"(です|ます|でした|ました|でしょう|といえます|となります)[。！?]?$")
_AMBIGUOUS_SUBJECT_RE = re.compile(r"^(この|その|それ|こちら|これら)")
_EXPLANATION_MARKER_RE = re.compile(r"(つまり|要するに|たとえば|具体的には|まず|次に|最後に)")


def _tokenize(text: str) -> List[str]:
    tokens: List[str] = []
    for token in _TOKEN_RE.findall(str(text or "")):
        if token not in _STOPWORDS:
            tokens.append(token)
    return tokens


def _jaccard_similarity(text_a: str, text_b: str) -> float:
    terms_a = set(_tokenize(text_a))
    terms_b = set(_tokenize(text_b))
    if not terms_a or not terms_b:
        return 0.0
    return round(len(terms_a & terms_b) / max(1, len(terms_a | terms_b)), 4)


def _content_overlap(text_a: str, text_b: str) -> float:
    terms_a = set(_tokenize(text_a))
    terms_b = set(_tokenize(text_b))
    if not terms_a or not terms_b:
        return 0.0
    return round(len(terms_a & terms_b) / max(1, min(len(terms_a), len(terms_b))), 4)


def _sentence_list(text: str) -> List[str]:
    return [item.strip() for item in re.split(r"(?<=[。！？])", str(text or "")) if item.strip()]


def _paragraph_break_score(text: str) -> float:
    paragraphs = [item.strip() for item in str(text or "").split("\n\n") if item.strip()]
    if not paragraphs:
        return 0.0
    sentence_counts = [len(_sentence_list(paragraph)) for paragraph in paragraphs]
    if len(paragraphs) == 1 and sentence_counts[0] >= 4:
        return 0.2
    average = sum(sentence_counts) / max(1, len(sentence_counts))
    if 1.5 <= average <= 3.0:
        return 1.0
    if 1.0 <= average <= 4.0:
        return 0.6
    return 0.3


def _ending_repetition_count(text: str) -> int:
    endings: List[str] = []
    for sentence in _sentence_list(text):
        match = _ENDING_RE.search(sentence)
        endings.append(match.group(1) if match else sentence[-2:])
    repetition = 0
    current_run = 1
    for index in range(1, len(endings)):
        if endings[index] == endings[index - 1]:
            current_run += 1
            if current_run >= 3:
                repetition += 1
        else:
            current_run = 1
    return repetition


def _ambiguous_subject_count(text: str) -> int:
    count = 0
    for sentence in _sentence_list(text):
        if _AMBIGUOUS_SUBJECT_RE.match(sentence):
            count += 1
    return count


def _warning_repairs(text: str) -> List[str]:
    warnings: List[str] = []
    sentences = _sentence_list(text)
    if any(len(sentence) >= 90 for sentence in sentences):
        warnings.append("split_long_sentences")
    short_streak = 0
    for sentence in sentences:
        if len(sentence) <= 16:
            short_streak += 1
            if short_streak >= 3 and "merge_short_sentences" not in warnings:
                warnings.append("merge_short_sentences")
        else:
            short_streak = 0
    if len(_EXPLANATION_MARKER_RE.findall(text)) >= 3:
        warnings.append("compress_explanations")
    if re.search(r"(私たち|当社|弊社).{0,16}(私たち|当社|弊社)", text):
        warnings.append("omit_redundant_subjects")
    return warnings


def _resolve_seed_thresholds(overlap_policy: Dict[str, Any]) -> Dict[str, float]:
    runtime_seed = get_vnext_overlap_runtime_config()
    incoming = dict(overlap_policy.get("seed_thresholds") or {})
    return {
        "similarity_threshold": float(
            incoming.get("similarity_threshold", runtime_seed["similarity_threshold"])
        ),
        "content_overlap_threshold": float(
            incoming.get("content_overlap_threshold", runtime_seed["content_overlap_threshold"])
        ),
        "high_overlap_shortcut_threshold": float(
            incoming.get(
                "high_overlap_shortcut_threshold",
                runtime_seed["high_overlap_shortcut_threshold"],
            )
        ),
    }


def evaluate_sections(
    contract: VNextThinContract,
    briefs: List[SectionBrief],
    sections: List[RenderedSection],
    *,
    overlap_policy: Dict[str, Any],
) -> Dict[str, Any]:
    evaluations: List[Dict[str, Any]] = []
    seed_thresholds = _resolve_seed_thresholds(overlap_policy)
    similarity_threshold = float(seed_thresholds.get("similarity_threshold", 0.62))
    overlap_threshold = float(seed_thresholds.get("content_overlap_threshold", 0.77))
    for index, section in enumerate(sections):
        previous = sections[index - 1] if index > 0 else None
        similarity = _jaccard_similarity(previous.body, section.body) if previous else 0.0
        overlap = _content_overlap(previous.body, section.body) if previous else 0.0
        ambiguous_subjects = _ambiguous_subject_count(section.body)
        paragraph_break_score = _paragraph_break_score(section.body)
        ending_repetition = _ending_repetition_count(section.body)
        mandatory_repairs: List[str] = []
        if previous and (similarity >= similarity_threshold or overlap >= overlap_threshold):
            mandatory_repairs.append("replace_overlapped_section")
        if ambiguous_subjects > 0:
            mandatory_repairs.append("restore_ambiguous_subjects")
        if paragraph_break_score < 0.55:
            mandatory_repairs.append("reflow_paragraphs")
        if ending_repetition > 0:
            mandatory_repairs.append("vary_sentence_endings")
        evaluations.append(
            {
                "section_id": section.section_id,
                "heading": section.heading,
                "overlap_score": similarity,
                "content_overlap_score": overlap,
                "overlap_with_section_id": previous.section_id if previous else "",
                "ambiguous_subject_count": ambiguous_subjects,
                "paragraph_break_score": paragraph_break_score,
                "ending_repetition_count": ending_repetition,
                "mandatory_repairs": mandatory_repairs,
                "warning_repairs": _warning_repairs(section.body),
                "provisional_overlap_policy": {
                    "status": str(overlap_policy.get("status") or "provisional"),
                    "calibration_required": bool(overlap_policy.get("calibration_required", True)),
                    "seed_source": str(overlap_policy.get("seed_source") or ""),
                    "seed_thresholds": dict(seed_thresholds),
                },
                "brief": asdict(briefs[index]),
            }
        )
    return {
        "section_evaluations": evaluations,
        "mandatory_scope": [
            "replace_overlapped_section",
            "restore_ambiguous_subjects",
            "reflow_paragraphs",
            "vary_sentence_endings",
        ],
        "warning_first_scope": [
            "split_long_sentences",
            "merge_short_sentences",
            "compress_explanations",
            "omit_redundant_subjects",
        ],
    }
