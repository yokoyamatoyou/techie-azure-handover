# -*- coding: utf-8 -*-
"""構造化データモジュール"""

from .schema_suggester import (
    SchemaSuggester,
    SCHEMA_TEMPLATES,
    generate_schema_template,
    analyze_existing_schema,
    validate_schema
)
from .schema_explainer import (
    SCHEMA_EXPLANATIONS,
    get_schema_explanation
)
from .schema_faq import (
    SCHEMA_FAQ,
    get_schema_faq
)
from .checker import StructuredDataChecker

__all__ = [
    "SchemaSuggester",
    "SCHEMA_TEMPLATES",
    "generate_schema_template",
    "analyze_existing_schema",
    "validate_schema",
    "SCHEMA_EXPLANATIONS",
    "get_schema_explanation",
    "SCHEMA_FAQ",
    "get_schema_faq",
    "StructuredDataChecker",
]
