from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass
class PanelContext:
    state: Any
    trim_text: Callable[..., str]
    format_reason_text_ui: Callable[[str], str]
    calc_citation_index: Callable[[Dict[str, Any] | None], Any]
    aio_score_labels: Dict[str, str]
    aio_score_help: Dict[str, str]


def build_panel_context(
    *,
    state: Any,
    trim_text: Callable[..., str],
    format_reason_text_ui: Callable[[str], str],
    calc_citation_index: Callable[[Dict[str, Any] | None], Any],
    aio_score_labels: Dict[str, str] | None,
    aio_score_help: Dict[str, str] | None,
) -> PanelContext:
    return PanelContext(
        state=state,
        trim_text=trim_text,
        format_reason_text_ui=format_reason_text_ui,
        calc_citation_index=calc_citation_index,
        aio_score_labels=dict(aio_score_labels or {}),
        aio_score_help=dict(aio_score_help or {}),
    )
