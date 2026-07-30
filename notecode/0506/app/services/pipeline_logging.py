from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = ROOT / "artifacts" / "runs"


class PipelineLogger:
    def __init__(self, run_id: str | None = None, artifacts_dir: Path = ARTIFACTS_DIR) -> None:
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = artifacts_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, name: str, payload: dict[str, Any] | list[Any]) -> Path:
        path = self.run_dir / f"{name}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def write_text(self, name: str, text: str) -> Path:
        path = self.run_dir / f"{name}.md"
        path.write_text(text, encoding="utf-8")
        return path
