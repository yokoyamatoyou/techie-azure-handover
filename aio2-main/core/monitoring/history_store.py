from __future__ import annotations

import json
import os
from typing import Any, Dict, List


def get_monitoring_history_path(*, cwd: str | None = None) -> str:
    base_dir = os.path.join(cwd or os.getcwd(), "outputs", "monitoring")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "aio_monitoring.json")


def load_monitoring_history(*, path: str | None = None, cwd: str | None = None) -> List[Dict[str, Any]]:
    resolved_path = path or get_monitoring_history_path(cwd=cwd)
    if not os.path.exists(resolved_path):
        return []
    try:
        with open(resolved_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_monitoring_history(
    history: List[Dict[str, Any]],
    *,
    path: str | None = None,
    cwd: str | None = None,
) -> None:
    resolved_path = path or get_monitoring_history_path(cwd=cwd)
    try:
        with open(resolved_path, "w", encoding="utf-8") as handle:
            json.dump(history, handle, ensure_ascii=True, indent=2)
    except Exception:
        pass
