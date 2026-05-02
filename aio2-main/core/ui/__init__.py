# -*- coding: utf-8 -*-
"""UIモジュール"""

from .design_system import (
    COLORS,
    LEGAL_ICONS,
    LEGAL_ICONS_FALLBACK,
    SITE_HEALTH_COLORS,
    SITE_HEALTH_SPACING,
    SITE_HEALTH_TYPOGRAPHY,
    STATUS_ICONS,
    get_color_class,
    get_icon,
    resolve_color,
    resolve_icon,
)
from .components import create_status_card, build_status_card_data, normalize_item, safe_text
from .detail_panels import render_detail_panel, summarize_issues, format_issue_rows
from .help_system import render_faq_section, build_faq_pairs
from .mode_manager import ModeManager, MODE_LABELS

__all__ = [
    "COLORS",
    "LEGAL_ICONS",
    "LEGAL_ICONS_FALLBACK",
    "SITE_HEALTH_COLORS",
    "SITE_HEALTH_TYPOGRAPHY",
    "SITE_HEALTH_SPACING",
    "STATUS_ICONS",
    "get_icon",
    "get_color_class",
    "resolve_color",
    "resolve_icon",
    "create_status_card",
    "build_status_card_data",
    "normalize_item",
    "safe_text",
    "render_detail_panel",
    "summarize_issues",
    "format_issue_rows",
    "render_faq_section",
    "build_faq_pairs",
    "ModeManager",
    "MODE_LABELS",
]
