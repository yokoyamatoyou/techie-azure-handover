# -*- coding: utf-8 -*-
"""PDF report section renderers."""

from .report_sections import (
    render_decision_summary_section,
    render_immediate_actions_section,
    render_improvement_section,
)

__all__ = [
    "render_decision_summary_section",
    "render_immediate_actions_section",
    "render_improvement_section",
]
