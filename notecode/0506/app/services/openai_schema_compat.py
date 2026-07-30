from __future__ import annotations

import json
import re
from typing import Any


OPENAI_UNSUPPORTED_SCHEMA_KEYS = {
    "$id",
    "$schema",
    "allOf",
    "contains",
    "dependentRequired",
    "dependentSchemas",
    "else",
    "exclusiveMaximum",
    "exclusiveMinimum",
    "format",
    "if",
    "maxContains",
    "maxItems",
    "maxLength",
    "maximum",
    "minContains",
    "minItems",
    "minLength",
    "minimum",
    "multipleOf",
    "not",
    "pattern",
    "patternProperties",
    "propertyNames",
    "then",
    "unevaluatedProperties",
    "uniqueItems",
    "x-openai-exclude",
}

TRACE_ID_PREFIX_BY_KEY = {
    "fact_id": "F",
    "supporting_fact_ids": "F",
    "involved_fact_ids": "F",
    "claim_id": "C",
    "claim_ids": "C",
    "source_claim_ids": "C",
    "assigned_claim_ids": "C",
    "bridge_id": "B",
}

NUMERIC_BOUNDS_BY_KEY = {
    "importance": (1, 5),
    "source_priority": (1, 5),
    "score": (0, 100),
    "sentence_count": (0, None),
    "paragraph_count": (0, None),
    "target_length_chars": (600, 3000),
    "section_count": (1, 5),
    "max_items": (0, 3),
    "max_sentences_each": (1, 2),
    "max_article_ratio_percent": (1, 10),
    "preferred_sentences_per_paragraph": (1, 4),
    "max_sentences_per_paragraph": (1, 5),
    "split_late_paragraph_over_sentences": (1, 5),
}

UNIQUE_ARRAY_KEYS = {
    "assigned_claim_ids",
    "claim_ids",
    "config_refs",
    "deduped_themes",
    "forbidden_viewpoint_terms",
    "involved_fact_ids",
    "main_topics",
    "persona_refs",
    "protected_subject_terms",
    "risk_categories",
    "risk_flags",
    "source_card_ids",
    "source_claim_ids",
    "supporting_fact_ids",
}


def schema_for_openai_response_format(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if key in OPENAI_UNSUPPORTED_SCHEMA_KEYS:
                continue
            if key == "properties" and isinstance(item, dict):
                cleaned[key] = {
                    property_name: schema_for_openai_response_format(property_schema)
                    for property_name, property_schema in item.items()
                    if not _is_openai_excluded_schema(property_schema)
                }
                continue
            cleaned[key] = schema_for_openai_response_format(item)
        if cleaned.get("type") == "object" and isinstance(cleaned.get("properties"), dict):
            cleaned["required"] = list(cleaned["properties"].keys())
            cleaned["additionalProperties"] = False
        return cleaned
    if isinstance(value, list):
        return [schema_for_openai_response_format(item) for item in value]
    return value


def _is_openai_excluded_schema(value: Any) -> bool:
    return isinstance(value, dict) and value.get("x-openai-exclude") is True


def normalize_openai_json_for_local_schema(value: Any, schema_name: str) -> Any:
    if schema_name not in {
        "source_card.schema.json",
        "knowledge_pack.schema.json",
        "article_brief.schema.json",
        "quality_check.schema.json",
        "publish_readiness.schema.json",
    }:
        return value

    normalized = _dedupe_unique_arrays(_normalize_bounded_numbers(_normalize_trace_ids(value)))
    if schema_name == "knowledge_pack.schema.json" and isinstance(normalized, dict):
        return _drop_single_fact_conflicts(normalized)
    if schema_name == "source_card.schema.json" and isinstance(normalized, dict):
        return _normalize_source_card_source_id(normalized)
    return normalized


def _normalize_trace_ids(value: Any, active_key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_trace_ids(item, key) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_trace_ids(item, active_key) for item in value]
    if isinstance(value, str) and active_key in TRACE_ID_PREFIX_BY_KEY:
        return _normalize_trace_id(value, TRACE_ID_PREFIX_BY_KEY[active_key])
    return value


def _normalize_trace_id(value: str, prefix: str) -> str:
    text = value.strip()
    match = re.fullmatch(rf"{prefix}([0-9]{{3,}})", text, flags=re.IGNORECASE)
    if match:
        return f"{prefix}{match.group(1)}"
    match = re.search(r"([0-9]+)", text)
    if not match:
        return text
    return f"{prefix}{match.group(1).zfill(3)}"


def _normalize_bounded_numbers(value: Any, active_key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_bounded_numbers(item, key) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_bounded_numbers(item, active_key) for item in value]
    if active_key in NUMERIC_BOUNDS_BY_KEY:
        return _coerce_bounded_int(value, NUMERIC_BOUNDS_BY_KEY[active_key])
    return value


def _coerce_bounded_int(value: Any, bounds: tuple[int, int | None]) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        integer = int(value)
    elif isinstance(value, str) and re.fullmatch(r"-?[0-9]+", value.strip()):
        integer = int(value.strip())
    else:
        return value
    lower, upper = bounds
    if integer < lower:
        return lower
    if upper is not None and integer > upper:
        return upper
    return integer


def _dedupe_unique_arrays(value: Any, active_key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {key: _dedupe_unique_arrays(item, key) for key, item in value.items()}
    if isinstance(value, list):
        items = [_dedupe_unique_arrays(item, active_key) for item in value]
        if active_key in UNIQUE_ARRAY_KEYS:
            return _dedupe_preserving_order(items)
        return items
    return value


def _dedupe_preserving_order(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    deduped: list[Any] = []
    for item in values:
        marker = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(item)
    return deduped


def _normalize_source_card_source_id(value: dict[str, Any]) -> dict[str, Any]:
    source_id = value.get("source_id")
    if not isinstance(source_id, str):
        return value
    normalized = re.sub(r"[^a-z0-9_-]+", "_", source_id.strip().lower()).strip("_-")
    if normalized:
        return {**value, "source_id": normalized}
    return value


def _drop_single_fact_conflicts(value: dict[str, Any]) -> dict[str, Any]:
    pack = value.get("article_knowledge_pack")
    if not isinstance(pack, dict):
        return value
    conflicts = pack.get("conflicts")
    if not isinstance(conflicts, list):
        return value
    filtered = [
        conflict
        for conflict in conflicts
        if not isinstance(conflict, dict) or len(conflict.get("involved_fact_ids", [])) >= 2
    ]
    if len(filtered) == len(conflicts):
        return value
    return {**value, "article_knowledge_pack": {**pack, "conflicts": filtered}}
