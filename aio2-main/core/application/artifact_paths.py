from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

RESULT_ARTIFACT_MAX_BYTES = 25 * 1024 * 1024


def resolve_existing_result_path(
    raw_path: Any,
    *,
    runs_dir: Path,
    max_bytes: int = RESULT_ARTIFACT_MAX_BYTES,
) -> Optional[Path]:
    """Return a readable result artifact only when it stays inside runs_dir."""
    if not raw_path:
        return None
    try:
        base = Path(runs_dir).resolve()
        candidate = Path(str(raw_path))
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        resolved = candidate.resolve()
        resolved.relative_to(base)
        if resolved.name != "analysis_result.json" or not resolved.is_file():
            return None
        if max_bytes > 0 and resolved.stat().st_size > max_bytes:
            return None
        return resolved
    except (OSError, RuntimeError, ValueError):
        return None
