"""Adapter for semantic dedupe in minimal pipeline."""
from __future__ import annotations

from typing import Any, Dict, Tuple

from core.app_config import get_semantic_dedupe_config
from note.zero_base.semantic_dedupe import semantic_dedupe_text


def run_semantic_dedupe(body: str, contract: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Run semantic dedupe with config-driven rewrite/observe behavior."""
    config = dict(get_semantic_dedupe_config())
    if not bool(contract.get("semantic_dedupe_enabled", False)):
        config["enabled"] = False
    deduped, audit = semantic_dedupe_text(body, contract, config=config)
    if isinstance(audit, dict):
        if not config["enabled"]:
            audit["adapter_mode"] = "disabled"
        elif bool(config.get("rewrite_enabled", False)):
            audit["adapter_mode"] = "rewrite_active"
        else:
            audit["adapter_mode"] = "observe_only"
        audit["rewrite_enabled"] = bool(config.get("rewrite_enabled", False))
    if not bool(config.get("rewrite_enabled", False)):
        return body, audit
    return deduped, audit
