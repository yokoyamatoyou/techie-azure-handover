# -*- coding: utf-8 -*-
"""Legal tab rendering logic."""

from typing import Any, Dict

from core.ui.tabs.health_tab import render_legal_section


def render_legal_tab(analysis_result: Dict[str, Any], display_mode: str) -> None:
    """Render the legal tab."""
    _ = display_mode
    render_legal_section(analysis_result, leading_separator=False)
