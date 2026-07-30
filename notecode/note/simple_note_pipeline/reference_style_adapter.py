from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


ADAPTER_VERSION = "reference_style_projection_adapter_v1"


@dataclass(frozen=True)
class StyleCardValidationResult:
    ok: bool
    issues: tuple[str, ...] = ()


def load_reference_style_card(path: str | Path) -> dict[str, Any]:
    """Load a metrics-only style card from disk."""

    card_path = Path(path)
    return json.loads(card_path.read_text(encoding="utf-8"))


def validate_metrics_only_style_card(card: Mapping[str, Any]) -> StyleCardValidationResult:
    issues: list[str] = []
    if card.get("schema_version") != "reference_style_card_v1":
        issues.append("schema_version_mismatch")

    source_policy = card.get("source_policy")
    if not isinstance(source_policy, Mapping):
        issues.append("source_policy_missing")
    else:
        if source_policy.get("raw_text_stored") is not False:
            issues.append("raw_text_storage_not_false")
        if source_policy.get("prompt_examples_allowed") is not False:
            issues.append("prompt_examples_allowed_not_false")
        if source_policy.get("named_creator_imitation_allowed") is not False:
            issues.append("named_creator_imitation_allowed_not_false")

    extraction_notes = card.get("extraction_notes")
    if isinstance(extraction_notes, Mapping):
        if extraction_notes.get("article_text_in_prompt") is not False:
            issues.append("article_text_in_prompt_not_false")
        if extraction_notes.get("copied_expressions_recorded") is not False:
            issues.append("copied_expressions_recorded_not_false")
        if extraction_notes.get("named_creator_imitation") is not False:
            issues.append("named_creator_imitation_not_false")
        if extraction_notes.get("route_created") is not False:
            issues.append("route_created_not_false")
        if extraction_notes.get("live_generation_executed") is not False:
            issues.append("live_generation_executed_not_false")

    if "raw_text" in card or "article_text" in card or "prompt_examples" in card:
        issues.append("forbidden_top_level_text_payload")

    return StyleCardValidationResult(ok=not issues, issues=tuple(issues))


def build_reference_style_projection_constraints(card: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a metrics-only style card into compact, non-imitation constraints."""

    validation = validate_metrics_only_style_card(card)
    if not validation.ok:
        raise ValueError("invalid metrics-only style card: " + ",".join(validation.issues))

    paragraph = _mapping(card.get("paragraph_rhythm"))
    sentence = _mapping(card.get("sentence_rhythm"))
    heading = _mapping(card.get("heading_shape"))
    viewpoint = _mapping(card.get("viewpoint"))
    connectors = _mapping(card.get("connectors"))
    endings = _mapping(card.get("endings"))
    stock = _mapping(card.get("gpt_stock_phrases"))
    sample_set = _mapping(card.get("sample_set"))

    explicit_subject_ratio = _float(viewpoint.get("explicit_subject_ratio"))
    ending_run_p90 = _float(endings.get("max_same_ending_bucket_run_p90"))
    stock_density = _float(stock.get("stock_phrase_density_per_1000_chars"))
    heading_density = _float(heading.get("heading_density_per_1000_chars"))
    list_ratio = _float(heading.get("list_section_ratio"))

    return {
        "adapter_version": ADAPTER_VERSION,
        "source_policy": {
            "raw_text_stored": False,
            "prompt_examples_allowed": False,
            "named_creator_imitation_allowed": False,
            "urls_allowed_in_generation_prompt": False,
        },
        "reference_fit": {
            "sample_count": int(_float(sample_set.get("count"))),
            "article_type_fit": "weak_note_writing_reference_for_company_intro",
            "use_as": "style_rhythm_metrics_only",
            "do_not_use_as": "prose_style_or_creator_imitation",
        },
        "generation_constraints": {
            "paragraph_rhythm": {
                "target": "moderate_note_like_blocks",
                "reference_paragraph_count_p50": paragraph.get("paragraph_count_p50", 0),
                "short_paragraph_ratio_reference": paragraph.get("short_paragraph_ratio", 0),
                "application_note": "Use as rhythm signal only; do not force 29 paragraphs for company introduction.",
            },
            "sentence_rhythm": {
                "variance_bucket": sentence.get("sentence_length_variance_bucket", "mid"),
                "chars_per_sentence_p50_reference": sentence.get("chars_per_sentence_p50", 0),
                "chars_per_sentence_p90_reference": sentence.get("chars_per_sentence_p90", 0),
            },
            "viewpoint": {
                "explicit_subject_ceiling": round(min(max(explicit_subject_ratio, 0.0), 0.32), 4),
                "company_name_as_first_person_allowed": False,
                "first_person_reference_downweighted": True,
            },
            "connectors": {
                "connector_density_reference_per_1000_chars": connectors.get(
                    "connector_density_per_1000_chars", 0
                ),
                "late_half_connector_ratio_reference": connectors.get("late_half_connector_ratio", 0),
            },
            "endings": {
                "max_same_ending_bucket_run_target": max(4, min(7, round(ending_run_p90))),
                "soft_assertive_ending_ratio_reference": endings.get("soft_assertive_ending_ratio", 0),
            },
            "gpt_stock_phrases": {
                "density_reference_per_1000_chars": stock_density,
                "policy": "track_and_reduce_without_expanding_hard_ban_list",
            },
            "heading_shape": {
                "heading_density_reference_per_1000_chars": heading_density,
                "list_ratio_reference": list_ratio,
                "application_note": "Downweight for company introduction; avoid listicle transfer.",
            },
        },
        "ignored_or_downweighted_metrics": [
            "source_urls",
            "sample_metrics.body_char_count_as_style_target",
            "first_person_presence_ratio_for_company_name",
            "heading_count_p50_as_direct_target",
            "list_section_ratio_as_direct_target",
        ],
    }


def build_reference_style_prompt_payload(card: Mapping[str, Any]) -> dict[str, Any]:
    constraints = build_reference_style_projection_constraints(card)
    return {
        "adapter_version": constraints["adapter_version"],
        "reference_fit": constraints["reference_fit"],
        "generation_constraints": constraints["generation_constraints"],
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
