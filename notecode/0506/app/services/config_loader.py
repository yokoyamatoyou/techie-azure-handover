from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "app" / "config"


class ConfigError(ValueError):
    """Raised when required config data is missing or malformed."""


@dataclass(frozen=True)
class ProjectConfig:
    default_settings: dict[str, Any]
    article_genres: dict[str, Any]
    quality_thresholds: dict[str, Any]
    source_acquisition: dict[str, Any]
    stylometry: dict[str, Any]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"missing config file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"config file must contain a mapping: {path}")
    return data


def _require_mapping(data: dict[str, Any], key: str, path: Path) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict) or not value:
        raise ConfigError(f"{path.name} must contain non-empty mapping '{key}'")
    return value


def load_project_config(config_dir: Path = CONFIG_DIR) -> ProjectConfig:
    default_settings = _load_yaml(config_dir / "default_settings.yaml")
    article_genres = _load_yaml(config_dir / "article_genres.yaml")
    quality_thresholds = _load_yaml(config_dir / "quality_thresholds.yaml")
    source_acquisition = _load_yaml(config_dir / "source_acquisition.yaml")
    stylometry = _load_yaml(config_dir / "stylometry.yaml")

    _require_mapping(article_genres, "genres", config_dir / "article_genres.yaml")
    _require_mapping(quality_thresholds, "qa_policies", config_dir / "quality_thresholds.yaml")
    _require_mapping(source_acquisition, "source_priority", config_dir / "source_acquisition.yaml")

    if "defaults" not in default_settings:
        raise ConfigError("default_settings.yaml must contain 'defaults'")
    if "model_frequent_words" not in stylometry:
        raise ConfigError("stylometry.yaml must contain 'model_frequent_words'")

    return ProjectConfig(
        default_settings=default_settings,
        article_genres=article_genres,
        quality_thresholds=quality_thresholds,
        source_acquisition=source_acquisition,
        stylometry=stylometry,
    )


def get_genre_config(genre_id: str, config: ProjectConfig | None = None) -> dict[str, Any]:
    loaded = config or load_project_config()
    genres = loaded.article_genres["genres"]
    if genre_id not in genres:
        raise ConfigError(f"unknown genre_id: {genre_id}")
    return genres[genre_id]
