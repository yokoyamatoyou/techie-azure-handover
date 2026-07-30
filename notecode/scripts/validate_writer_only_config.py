from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from note.writer_only_config import load_writer_only_model_config


def main() -> int:
    cfg = load_writer_only_model_config()
    print(f"writer_only config OK: family={cfg.family} model={cfg.model} api={cfg.api}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
