"""vNext blog generation core package."""

from .contract import (
    VNEXT_THIN_CONTRACT_MUST_FIELDS,
    VNEXT_THIN_CONTRACT_OPTIONAL_FIELDS,
    build_vnext_thin_contract,
)
from .pipeline import VNextPipeline
from .types import CanonicalDocument, FactCard, RenderedSection, SectionBrief, VNextThinContract

__all__ = [
    "CanonicalDocument",
    "FactCard",
    "RenderedSection",
    "SectionBrief",
    "VNextPipeline",
    "VNextThinContract",
    "VNEXT_THIN_CONTRACT_MUST_FIELDS",
    "VNEXT_THIN_CONTRACT_OPTIONAL_FIELDS",
    "build_vnext_thin_contract",
]
