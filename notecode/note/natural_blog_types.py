from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class NaturalStyleProfile:
    profile_name: str
    article_tone: str
    base_register: str
    linebreak_profile: str
    paragraph_min: int
    paragraph_max: int
    sentence_length_mix: str = "short_medium_long"
    opening_variation_target: str = "high"
    information_density: str = "balanced"
    punctuation_profile: str = "balanced_japanese"
    subject_omission_policy: str = "balanced"
    paragraph_break_policy: str = "topic_shift_only"
    ending_distribution_hint: str = "balanced"
    preferred_endings: List[str] = field(default_factory=list)
    prompt_rules: List[str] = field(default_factory=list)
    banned_openings: List[str] = field(default_factory=list)
    keyword_policy: str = "stable_keywords"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DiscourseSectionPlan:
    heading: str
    intent: str
    target_chars: int
    topic_seed: str
    fact_slot: str = ""
    related_terms: List[str] = field(default_factory=list)
    reader_question: str = ""
    bridge_hint: str = ""
    must_cover: List[str] = field(default_factory=list)
    new_information: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
