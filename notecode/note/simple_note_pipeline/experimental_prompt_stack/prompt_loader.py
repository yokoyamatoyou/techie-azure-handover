"""Markdown prompt asset loader for the experimental prompt stack."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


_ASSET_ROOT = Path(__file__).resolve().parent


def _parse_markdown_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current_section = ""
    for raw_line in str(text or "").splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            current_section = line[3:].strip()
            sections[current_section] = []
            continue
        if not current_section:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        sections[current_section].append(stripped)
    return sections


@lru_cache(maxsize=None)
def load_prompt_asset_sections(relative_path: str) -> dict[str, list[str]]:
    """Load a markdown asset file and return section -> lines."""

    asset_path = _ASSET_ROOT / relative_path
    return _parse_markdown_sections(asset_path.read_text(encoding="utf-8"))
