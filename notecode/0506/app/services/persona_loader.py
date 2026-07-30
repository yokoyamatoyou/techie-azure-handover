from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
PERSONA_DIR = ROOT / "app" / "personas"


class PersonaError(ValueError):
    """Raised when persona data cannot be resolved."""


@dataclass(frozen=True)
class PersonaBundle:
    persona_id: str
    writer_role: dict[str, Any]
    viewpoint_profile: dict[str, Any]
    style_profile: dict[str, Any]
    editor_profile: dict[str, Any]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise PersonaError(f"missing persona file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise PersonaError(f"persona file must contain a mapping: {path}")
    return data


def load_persona_bundle(persona_id: str, persona_dir: Path = PERSONA_DIR) -> PersonaBundle:
    registry = _load_yaml(persona_dir / "persona_registry.yaml").get("personas", {})
    writer_roles = _load_yaml(persona_dir / "writer_roles.yaml").get("writer_roles", {})
    viewpoints = _load_yaml(persona_dir / "viewpoint_profiles.yaml").get("viewpoint_profiles", {})
    style_profiles = _load_yaml(persona_dir / "style_profiles.yaml").get("style_profiles", {})
    editor_profiles = _load_yaml(persona_dir / "editor_profiles.yaml").get("editor_profiles", {})

    if persona_id not in registry:
        raise PersonaError(f"unknown persona_id: {persona_id}")
    entry = registry[persona_id]
    writer_role_id = entry.get("writer_role_id")
    viewpoint_profile_id = entry.get("viewpoint_profile_id")
    style_profile_id = entry.get("style_profile_id")
    editor_profile_id = entry.get("editor_profile_id")

    if writer_role_id not in writer_roles:
        raise PersonaError(f"unknown writer_role_id: {writer_role_id}")
    if viewpoint_profile_id not in viewpoints:
        raise PersonaError(f"unknown viewpoint_profile_id: {viewpoint_profile_id}")
    if style_profile_id not in style_profiles:
        raise PersonaError(f"unknown style_profile_id: {style_profile_id}")
    if editor_profile_id not in editor_profiles:
        raise PersonaError(f"unknown editor_profile_id: {editor_profile_id}")

    return PersonaBundle(
        persona_id=persona_id,
        writer_role=writer_roles[writer_role_id],
        viewpoint_profile=viewpoints[viewpoint_profile_id],
        style_profile={"style_profile_id": style_profile_id, **style_profiles[style_profile_id]},
        editor_profile={"editor_profile_id": editor_profile_id, **editor_profiles[editor_profile_id]},
    )
