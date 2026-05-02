"""vNext pipeline implementation."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

from note.llm_client import LLMClient

from .evaluator import evaluate_sections
from .formatter import format_vnext_output
from .planner import build_section_briefs
from .repair import apply_local_repairs
from .types import VNextThinContract
from .writer import render_sections


class VNextPipeline:
    """Thin-plan-first pipeline used for shadow integration and future cutover."""

    def __init__(self, llm_client: Optional[LLMClient] = None, *, allow_llm: bool = False) -> None:
        self.llm_client = llm_client
        self.allow_llm = allow_llm

    def generate(self, contract: VNextThinContract) -> Dict[str, Any]:
        briefs, planner_report = build_section_briefs(contract)
        rendered_sections = render_sections(
            contract,
            briefs,
            llm_client=self.llm_client,
            allow_llm=self.allow_llm,
        )
        evaluation_report = evaluate_sections(
            contract,
            briefs,
            rendered_sections,
            overlap_policy=dict(planner_report.get("overlap_policy") or {}),
        )
        repaired_sections, repair_report = apply_local_repairs(
            contract,
            briefs,
            rendered_sections,
            evaluation_report,
        )
        formatted = format_vnext_output(contract, repaired_sections)
        return {
            **formatted,
            "success": True,
            "thin_contract": contract.to_dict(),
            "planner_report": planner_report,
            "evaluation_report": evaluation_report,
            "repair_report": repair_report,
            "rendered_sections": [asdict(item) for item in repaired_sections],
        }
