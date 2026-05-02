"""Phase 05 layout guard for structural coherence and supplement placement."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import re
from typing import Dict, List, Sequence, Tuple


HEADING_PATTERN = re.compile(r"(?m)^(#{2,6})\s+(.+?)\s*$")
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+|[一-龯]+|[ぁ-ん]+|[ァ-ヶー]+")
TRANSITION_PATTERN = re.compile(r"^(次に|一方で|一方|さらに|また|そのうえ|このため|ここで|まず|では)", re.I)

SUPPLEMENT_HEADING_PATTERN = re.compile(
    r"(補足|注釈|注意点|FAQ|Q&A|よくある質問|豆知識|Tips|追加情報|付録|参考資料)",
    re.I,
)
INTRO_HEADING_PATTERN = re.compile(r"(導入|はじめに|イントロ|背景|前提)", re.I)
CONCLUSION_HEADING_PATTERN = re.compile(r"(まとめ|結論|おわりに|最後に|総括|次の一歩)", re.I)


@dataclass(frozen=True)
class SupplementPositionAlert:
    section_index: int
    heading: str
    position_ratio: float
    min_position_ratio: float
    reason: str


@dataclass(frozen=True)
class ReorderStep:
    section_index: int
    target_index: int
    heading: str
    reason: str


@dataclass(frozen=True)
class LowCoherencePair:
    from_section: int
    to_section: int
    pair_score: float
    reason: str


@dataclass
class LayoutValidationReport:
    section_count: int
    role_distribution: Dict[str, int]
    intro_section_index: int
    intro_length_ratio: float
    intro_max_length_ratio: float
    intro_within_limit: bool
    coherence_score: float
    section_coherence_min_score: float
    coherence_within_limit: bool
    supplement_section_indexes: Tuple[int, ...] = ()
    early_supplement_count: int = 0
    low_coherence_pairs: List[LowCoherencePair] = field(default_factory=list)
    overall_pass: bool = True


@dataclass
class LayoutGuardResult:
    layout_score: float
    layout_validation_report: LayoutValidationReport
    supplement_position_alerts: List[SupplementPositionAlert] = field(default_factory=list)
    reorder_plan: List[ReorderStep] = field(default_factory=list)


@dataclass(frozen=True)
class _Section:
    original_index: int
    heading_line: str
    heading_text: str
    content: str
    role: str


class Phase05LayoutGuard:
    """Detect layout drift and produce minimal section reorder plans."""

    def __init__(
        self,
        supplement_min_position_ratio: float = 0.45,
        intro_max_length_ratio: float = 0.35,
        section_coherence_min_score: float = 0.40,
    ) -> None:
        self.supplement_min_position_ratio = max(0.2, min(0.9, float(supplement_min_position_ratio)))
        self.intro_max_length_ratio = max(0.1, min(0.8, float(intro_max_length_ratio)))
        self.section_coherence_min_score = max(0.0, min(1.0, float(section_coherence_min_score)))

    def analyze(self, text: str) -> LayoutGuardResult:
        if not text.strip():
            report = LayoutValidationReport(
                section_count=0,
                role_distribution={},
                intro_section_index=0,
                intro_length_ratio=0.0,
                intro_max_length_ratio=self.intro_max_length_ratio,
                intro_within_limit=True,
                coherence_score=1.0,
                section_coherence_min_score=self.section_coherence_min_score,
                coherence_within_limit=True,
                overall_pass=True,
            )
            return LayoutGuardResult(layout_score=1.0, layout_validation_report=report)

        _, raw_sections = self._split_sections(text)
        if not raw_sections:
            report = LayoutValidationReport(
                section_count=0,
                role_distribution={},
                intro_section_index=0,
                intro_length_ratio=0.0,
                intro_max_length_ratio=self.intro_max_length_ratio,
                intro_within_limit=True,
                coherence_score=1.0,
                section_coherence_min_score=self.section_coherence_min_score,
                coherence_within_limit=True,
                overall_pass=True,
            )
            return LayoutGuardResult(layout_score=1.0, layout_validation_report=report)

        sections = self._assign_roles(raw_sections, strict=True)
        if self._is_role_distribution_unstable(sections):
            sections = self._assign_roles(raw_sections, strict=False)

        section_count = len(sections)
        min_position_index = self._supplement_min_index(section_count)
        first_conclusion_index = self._first_conclusion_index(sections)

        supplement_alerts: List[SupplementPositionAlert] = []
        for section in sections:
            if section.role != "supplement":
                continue
            if section.original_index >= first_conclusion_index:
                continue
            if section.original_index >= min_position_index:
                continue
            position_ratio = round(section.original_index / max(1, section_count), 4)
            supplement_alerts.append(
                SupplementPositionAlert(
                    section_index=section.original_index,
                    heading=section.heading_text,
                    position_ratio=position_ratio,
                    min_position_ratio=round(self.supplement_min_position_ratio, 4),
                    reason=(
                        f"supplement section appears too early ({section.original_index} < {min_position_index})"
                    ),
                )
            )

        reordered_sections = self._reorder_sections_for_layout(
            sections=sections,
            min_position_index=min_position_index,
            first_conclusion_index=first_conclusion_index,
        )
        reorder_plan = self._build_reorder_plan(sections, reordered_sections)

        intro_index = self._intro_section_index(sections)
        intro_length_ratio = self._intro_length_ratio(sections, intro_index)
        intro_within_limit = intro_length_ratio <= self.intro_max_length_ratio

        coherence_score, low_pairs = self._coherence_score(sections)
        coherence_within_limit = coherence_score >= self.section_coherence_min_score

        role_distribution = self._role_distribution(sections)
        report = LayoutValidationReport(
            section_count=section_count,
            role_distribution=role_distribution,
            intro_section_index=intro_index,
            intro_length_ratio=intro_length_ratio,
            intro_max_length_ratio=round(self.intro_max_length_ratio, 4),
            intro_within_limit=intro_within_limit,
            coherence_score=coherence_score,
            section_coherence_min_score=round(self.section_coherence_min_score, 4),
            coherence_within_limit=coherence_within_limit,
            supplement_section_indexes=tuple(
                section.original_index for section in sections if section.role == "supplement"
            ),
            early_supplement_count=len(supplement_alerts),
            low_coherence_pairs=low_pairs,
            overall_pass=(not supplement_alerts and intro_within_limit and coherence_within_limit),
        )

        score = self._layout_score(
            early_supplement_count=len(supplement_alerts),
            intro_length_ratio=intro_length_ratio,
            coherence_score=coherence_score,
        )
        return LayoutGuardResult(
            layout_score=score,
            layout_validation_report=report,
            supplement_position_alerts=supplement_alerts,
            reorder_plan=reorder_plan,
        )

    def apply_minimal_reordering(
        self,
        text: str,
        reorder_plan: Sequence[ReorderStep],
    ) -> Tuple[str, List[ReorderStep]]:
        if not text.strip() or not reorder_plan:
            return text, []

        prefix, raw_sections = self._split_sections(text)
        if not raw_sections:
            return text, []

        section_map = {section.original_index: section for section in raw_sections}
        ordered: List[_Section] = list(raw_sections)
        applied: List[ReorderStep] = []

        for step in sorted(reorder_plan, key=lambda item: (item.target_index, item.section_index)):
            if step.section_index not in section_map:
                continue
            current_pos = next(
                (idx for idx, section in enumerate(ordered) if section.original_index == step.section_index),
                -1,
            )
            if current_pos < 0:
                continue

            section = ordered.pop(current_pos)
            target_pos = max(0, min(len(ordered), step.target_index - 1))
            ordered.insert(target_pos, section)
            applied.append(step)

        rebuilt = self._compose_text(prefix, ordered)
        return rebuilt, applied

    def _split_sections(self, text: str) -> Tuple[str, List[_Section]]:
        matches = list(HEADING_PATTERN.finditer(text))
        if not matches:
            return text.strip(), []

        prefix = text[: matches[0].start()].strip()
        sections: List[_Section] = []
        for idx, match in enumerate(matches, start=1):
            start = match.end()
            end = matches[idx].start() if idx < len(matches) else len(text)
            content = text[start:end].strip()
            sections.append(
                _Section(
                    original_index=idx,
                    heading_line=match.group(0).strip(),
                    heading_text=(match.group(2) or "").strip(),
                    content=content,
                    role="core",
                )
            )
        return prefix, sections

    def _assign_roles(self, sections: Sequence[_Section], strict: bool) -> List[_Section]:
        assigned: List[_Section] = []
        total = len(sections)

        for idx, section in enumerate(sections, start=1):
            heading = section.heading_text
            role = "core"

            if SUPPLEMENT_HEADING_PATTERN.search(heading):
                role = "supplement"
            elif CONCLUSION_HEADING_PATTERN.search(heading):
                role = "conclusion"
            elif INTRO_HEADING_PATTERN.search(heading):
                role = "intro"
            elif idx == 1 and not strict:
                role = "intro"
            elif idx == total and not strict:
                role = "conclusion"
            elif idx == 1 and not SUPPLEMENT_HEADING_PATTERN.search(heading):
                role = "intro"

            assigned.append(
                _Section(
                    original_index=section.original_index,
                    heading_line=section.heading_line,
                    heading_text=section.heading_text,
                    content=section.content,
                    role=role,
                )
            )
        return assigned

    def _is_role_distribution_unstable(self, sections: Sequence[_Section]) -> bool:
        if not sections:
            return False
        non_supplement = [section for section in sections if section.role != "supplement"]
        if not non_supplement:
            return True
        has_intro = any(section.role == "intro" for section in sections)
        has_core_like = any(section.role in ("core", "conclusion") for section in sections)
        return not has_intro or not has_core_like

    def _first_conclusion_index(self, sections: Sequence[_Section]) -> int:
        for section in sections:
            if section.role == "conclusion":
                return section.original_index
        return len(sections) + 1

    def _supplement_min_index(self, section_count: int) -> int:
        return max(2, int(math.ceil(section_count * self.supplement_min_position_ratio)))

    def _reorder_sections_for_layout(
        self,
        sections: Sequence[_Section],
        min_position_index: int,
        first_conclusion_index: int,
    ) -> List[_Section]:
        early_supplements = [
            section
            for section in sections
            if section.role == "supplement"
            and section.original_index < min_position_index
            and section.original_index < first_conclusion_index
        ]
        if not early_supplements:
            return list(sections)

        remaining = [section for section in sections if section not in early_supplements]
        first_conclusion_in_remaining = next(
            (idx for idx, section in enumerate(remaining) if section.role == "conclusion"),
            len(remaining),
        )
        insert_at = max(0, min_position_index - 1)
        insert_at = min(insert_at, first_conclusion_in_remaining)
        return remaining[:insert_at] + early_supplements + remaining[insert_at:]

    def _build_reorder_plan(
        self,
        original_sections: Sequence[_Section],
        reordered_sections: Sequence[_Section],
    ) -> List[ReorderStep]:
        target_positions = {
            section.original_index: idx
            for idx, section in enumerate(reordered_sections, start=1)
        }
        plan: List[ReorderStep] = []
        for section in original_sections:
            target_index = target_positions.get(section.original_index, section.original_index)
            if target_index == section.original_index:
                continue
            if section.role != "supplement":
                continue
            plan.append(
                ReorderStep(
                    section_index=section.original_index,
                    target_index=target_index,
                    heading=section.heading_text,
                    reason="move supplement section to middle-or-late position",
                )
            )
        plan.sort(key=lambda item: (item.target_index, item.section_index))
        return plan

    def _intro_section_index(self, sections: Sequence[_Section]) -> int:
        for section in sections:
            if section.role == "intro":
                return section.original_index
        return sections[0].original_index if sections else 0

    def _intro_length_ratio(self, sections: Sequence[_Section], intro_index: int) -> float:
        if not sections:
            return 0.0
        total_tokens = sum(len(TOKEN_PATTERN.findall(section.content)) for section in sections)
        if total_tokens <= 0:
            return 0.0
        intro_section = next((section for section in sections if section.original_index == intro_index), None)
        if intro_section is None:
            return 0.0
        intro_tokens = len(TOKEN_PATTERN.findall(intro_section.content))
        return round(intro_tokens / max(1, total_tokens), 4)

    def _coherence_score(self, sections: Sequence[_Section]) -> Tuple[float, List[LowCoherencePair]]:
        if len(sections) <= 1:
            return 1.0, []

        pair_scores: List[float] = []
        low_pairs: List[LowCoherencePair] = []

        for first, second in zip(sections[:-1], sections[1:]):
            first_tokens = self._topic_tokens(f"{first.heading_text} {first.content[:220]}")
            second_tokens = self._topic_tokens(f"{second.heading_text} {second.content[:220]}")
            overlap = self._jaccard(first_tokens, second_tokens)

            heading_score = 0.25 if first.heading_text != second.heading_text else 0.10
            lexical_score = min(0.5, overlap * 1.6)
            transition_score = 0.25 if TRANSITION_PATTERN.search(second.content.strip()) else 0.1
            pair_score = round(min(1.0, heading_score + lexical_score + transition_score), 4)
            pair_scores.append(pair_score)

            if pair_score < 0.35:
                low_pairs.append(
                    LowCoherencePair(
                        from_section=first.original_index,
                        to_section=second.original_index,
                        pair_score=pair_score,
                        reason="adjacent section transition looks weak",
                    )
                )

        avg_score = round(sum(pair_scores) / max(1, len(pair_scores)), 4)
        return avg_score, low_pairs

    def _topic_tokens(self, text: str) -> set[str]:
        tokens = [token.lower() for token in TOKEN_PATTERN.findall(text or "")]
        return {token for token in tokens if len(token) >= 2}

    def _jaccard(self, first: set[str], second: set[str]) -> float:
        if not first or not second:
            return 0.0
        union = first | second
        if not union:
            return 0.0
        return len(first & second) / len(union)

    def _role_distribution(self, sections: Sequence[_Section]) -> Dict[str, int]:
        counts = {"intro": 0, "core": 0, "supplement": 0, "conclusion": 0}
        for section in sections:
            counts[section.role] = counts.get(section.role, 0) + 1
        return counts

    def _layout_score(
        self,
        early_supplement_count: int,
        intro_length_ratio: float,
        coherence_score: float,
    ) -> float:
        penalty = 0.0
        penalty += min(0.45, early_supplement_count * 0.14)
        if intro_length_ratio > self.intro_max_length_ratio:
            penalty += min(0.30, (intro_length_ratio - self.intro_max_length_ratio) * 1.6)
        if coherence_score < self.section_coherence_min_score:
            penalty += min(0.35, (self.section_coherence_min_score - coherence_score) * 1.4)
        return round(max(0.0, 1.0 - penalty), 4)

    def _compose_text(self, prefix: str, sections: Sequence[_Section]) -> str:
        blocks: List[str] = []
        if prefix:
            blocks.append(prefix.strip())
        for section in sections:
            if section.content:
                blocks.append(f"{section.heading_line}\n\n{section.content}".strip())
            else:
                blocks.append(section.heading_line.strip())
        return "\n\n".join(block for block in blocks if block.strip()).strip()
