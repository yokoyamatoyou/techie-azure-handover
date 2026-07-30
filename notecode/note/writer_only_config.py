"""Config validation for the notecode writer-only route."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_ENV = "TECHIE_CONFIG_PATH"


@dataclass(frozen=True)
class WriterOnlyModelConfig:
    family: str
    model: str
    api: str
    parameters: Dict[str, Any]


class WriterOnlyConfigError(ValueError):
    pass


_ALLOWED_PARAMETER_KEYS = {
    "gpt-4.1": {
        "temperature",
        "top_p",
        "max_output_tokens",
        "text.format",
        "store",
        "prompt_cache_key",
        "prompt_cache_retention",
    },
    "gpt-5.4": {
        "text.verbosity",
        "text.format",
        "reasoning.effort",
        "reasoning.summary",
        "max_output_tokens",
        "store",
        "prompt_cache_key",
        "prompt_cache_retention",
    },
}


def _config_path() -> Path:
    override = str(os.getenv(CONFIG_ENV) or "").strip()
    return Path(override) if override else PROJECT_ROOT / "config.json"


def _flatten_parameter_keys(parameters: Dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for key, value in parameters.items():
        if key in {"text", "reasoning"} and isinstance(value, dict):
            for nested_key in value:
                keys.add(f"{key}.{nested_key}")
        else:
            keys.add(str(key))
    return keys


def _expand_parameter_keys(parameters: Dict[str, Any]) -> Dict[str, Any]:
    expanded: Dict[str, Any] = {}
    for key, value in parameters.items():
        if "." not in key:
            expanded[key] = value
            continue
        head, tail = key.split(".", 1)
        nested = expanded.setdefault(head, {})
        if not isinstance(nested, dict):
            raise WriterOnlyConfigError(f"parameter conflict: {key}")
        nested[tail] = value
    return expanded


def load_writer_only_model_config(path: str | Path | None = None) -> WriterOnlyModelConfig:
    config_path = Path(path) if path else _config_path()
    try:
        root = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise WriterOnlyConfigError(f"failed to read config: {exc}") from exc

    section = root.get("writer_only")
    if not isinstance(section, dict):
        raise WriterOnlyConfigError("writer_only config section is missing")

    family = str(section.get("family") or "").strip()
    model = str(section.get("model") or "").strip()
    api = str(section.get("api") or "responses").strip()
    parameters = section.get("parameters") or {}
    if not isinstance(parameters, dict):
        raise WriterOnlyConfigError("writer_only.parameters must be an object")
    if family not in _ALLOWED_PARAMETER_KEYS:
        raise WriterOnlyConfigError(f"unsupported writer_only family: {family}")
    if not model or "placeholder" in model.lower():
        raise WriterOnlyConfigError("writer_only.model must be a real model name")
    if api != "responses":
        raise WriterOnlyConfigError("writer_only.api must be responses")

    actual_keys = _flatten_parameter_keys(parameters)
    unsupported = sorted(actual_keys - _ALLOWED_PARAMETER_KEYS[family])
    if unsupported:
        raise WriterOnlyConfigError(
            f"unsupported writer_only parameters for {family}: {', '.join(unsupported)}"
        )
    if family == "gpt-4.1" and any(key.startswith("reasoning.") for key in actual_keys):
        raise WriterOnlyConfigError("gpt-4.1 writer_only config must not include reasoning parameters")
    if family == "gpt-5.4" and any(key in {"temperature", "top_p"} for key in actual_keys):
        raise WriterOnlyConfigError("gpt-5.4 writer_only config must not include sampling parameters")

    return WriterOnlyModelConfig(
        family=family,
        model=model,
        api=api,
        parameters=_expand_parameter_keys(parameters),
    )
