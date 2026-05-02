"""Prompt asset loader for the regular simple-note mainline."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Sequence


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
    """Load a markdown prompt asset and return section -> prompt lines."""

    asset_path = (_ASSET_ROOT / str(relative_path or "")).resolve()
    if not asset_path.is_file() or _ASSET_ROOT not in asset_path.parents:
        raise FileNotFoundError(f"Prompt asset not found: {relative_path}")
    return _parse_markdown_sections(asset_path.read_text(encoding="utf-8"))


def collect_prompt_asset_lines(relative_path: str, *section_names: str) -> list[str]:
    sections = load_prompt_asset_sections(relative_path)
    lines: list[str] = []
    selected_sections: Sequence[str] = section_names or tuple(sections.keys())
    for section_name in selected_sections:
        lines.extend(str(line).strip() for line in sections.get(section_name, []) if str(line).strip())
    return lines
