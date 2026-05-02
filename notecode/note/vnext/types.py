"""Core datatypes for the vNext pipeline."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class FactCard:
    fact_id: str
    fact_text: str
    fact_type: str = "general"
    entity: str = ""
    date_or_period: str = ""
    source_title: str = ""
    locator: str = ""
    confidence: float = 0.5
    critical: bool = False


@dataclass
class CanonicalDocument:
    raw_text: str
    norm_text: str
    blocks: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    critical_spans: List[Dict[str, Any]] = field(default_factory=list)
    source_type: str = "url"
    ocr_mode: str = "text"
    fact_cards: List[FactCard] = field(default_factory=list)


@dataclass
class VNextThinContract:
    article_type: str
    semantic_subtype: str
    discourse_mode: str
    evidence_style: str
    emotion_level: int
    speaker_profile: str
    audience_profile: str
    prompt_raw: str
    topic_statement: str
    length_mode: str
    allow_experience: bool
    relationship_mode: str
    comparison_axes: List[str] = field(default_factory=list)
    canonical_documents: List[CanonicalDocument] = field(default_factory=list)
    fact_cards: List[FactCard] = field(default_factory=list)
    preservation_policy: str = "normal"
    ui_signal_trace: Dict[str, Any] = field(default_factory=dict)
    core_message: str = ""
    content_goal: str = "auto"
    writing_focus: str = "auto"
    tone_profile: str = "auto"
    source_context_summary: Dict[str, Any] = field(default_factory=dict)
    mode_resolution_evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SectionBrief:
    section_id: str
    heading: str
    section_role: str
    target_chars: int
    primary_claim: str
    supporting_fact_ids: List[str] = field(default_factory=list)
    reader_question: str = ""
    transition_target: str = ""
    forbidden_overlap_ids: List[str] = field(default_factory=list)
    narrator_visibility: str = "implicit"
    emotion_target: int = 0
    must_keep_terms: List[str] = field(default_factory=list)


@dataclass
class RenderedSection:
    section_id: str
    heading: str
    body: str
    supporting_fact_ids: List[str] = field(default_factory=list)
