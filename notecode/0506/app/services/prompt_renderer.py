from __future__ import annotations

import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PROMPT_DIR = ROOT / "app" / "prompts"
TOKEN_RE = re.compile(r"{{\s*([a-zA-Z0-9_.]+)\s*}}")


class PromptRenderError(ValueError):
    """Raised when a prompt template cannot be rendered deterministically."""


def _resolve(context: dict[str, Any], dotted_key: str) -> Any:
    value: Any = context
    for part in dotted_key.split("."):
        if not isinstance(value, dict) or part not in value:
            raise PromptRenderError(f"missing template value: {dotted_key}")
        value = value[part]
    return value


def _stringify(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value)
    if isinstance(value, dict):
        return "\n".join(f"- {key}: {item}" for key, item in value.items())
    return str(value)


def render_template(template_name: str, context: dict[str, Any], prompt_dir: Path = PROMPT_DIR) -> str:
    template_path = prompt_dir / template_name
    if not template_path.exists():
        raise PromptRenderError(f"missing prompt template: {template_name}")
    template = template_path.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        return _stringify(_resolve(context, match.group(1)))

    rendered = TOKEN_RE.sub(replace, template)
    unresolved = TOKEN_RE.findall(rendered)
    if unresolved:
        raise PromptRenderError(f"unresolved template values: {unresolved}")
    return rendered


def prompt_line_count(template_name: str, prompt_dir: Path = PROMPT_DIR) -> int:
    return len((prompt_dir / template_name).read_text(encoding="utf-8").splitlines())
