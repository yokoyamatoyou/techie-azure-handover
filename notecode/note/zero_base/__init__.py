"""Zero-base rebuild utilities for incremental migration phases."""

from .phase01_baseline_contract import (
    DEFAULT_QUESTION_SOURCE_PRIORITY,
    REQUIRED_INTENT_FIELDS,
    build_intent_contract,
    build_intent_contract_schema,
    compute_contract_kpis,
    extract_recent_baseline,
    load_jsonl_records,
    summarize_kpis,
    write_phase01_artifacts,
)
from .phase02_dependency_map import (
    DEPENDENCY_ENTRIES,
    EMBEDDING_PLAN,
    build_dependency_index,
    detect_cycles,
    render_dependency_map_markdown,
    write_phase02_dependency_map,
)
from .semantic_dedupe import (
    DEFAULT_SEMANTIC_DEDUPE_CONFIG,
    OpenAIEmbeddingProvider,
    semantic_dedupe_text,
)
from .phase07_shadow_eval import (
    DEFAULT_PHASE07_THRESHOLDS,
    ShadowSample,
    aggregate_shadow_metrics,
    build_shadow_sample,
    compare_category_metrics,
    evaluate_phase07_gate,
    render_ab_report_markdown,
    split_by_category,
    to_dict_list,
    validate_shadow_samples,
)

__all__ = [
    "DEFAULT_QUESTION_SOURCE_PRIORITY",
    "REQUIRED_INTENT_FIELDS",
    "build_intent_contract",
    "build_intent_contract_schema",
    "compute_contract_kpis",
    "extract_recent_baseline",
    "load_jsonl_records",
    "summarize_kpis",
    "write_phase01_artifacts",
    "DEPENDENCY_ENTRIES",
    "EMBEDDING_PLAN",
    "build_dependency_index",
    "detect_cycles",
    "render_dependency_map_markdown",
    "write_phase02_dependency_map",
    "DEFAULT_SEMANTIC_DEDUPE_CONFIG",
    "OpenAIEmbeddingProvider",
    "semantic_dedupe_text",
    "DEFAULT_PHASE07_THRESHOLDS",
    "ShadowSample",
    "aggregate_shadow_metrics",
    "build_shadow_sample",
    "compare_category_metrics",
    "evaluate_phase07_gate",
    "render_ab_report_markdown",
    "split_by_category",
    "to_dict_list",
    "validate_shadow_samples",
]
