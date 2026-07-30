from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(PROJECT_ROOT))

from note.persona_iterative_trial_tooling import (  # noqa: E402
    DEFAULT_RUN_ROOT,
    initialize_trial_artifact_dir,
    run_persona_iterative_trial,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Persona iterative trial driver for current mainline.")
    parser.add_argument("--live", action="store_true", help="Run live LLM sweeps instead of offline sweeps.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the loop sweep. Without this flag the command only initializes manifests/logs.",
    )
    parser.add_argument(
        "--run-root",
        default=str(DEFAULT_RUN_ROOT),
        help="Artifact root for manifests and loop outputs.",
    )
    parser.add_argument("--max-loops", type=int, default=5, help="Maximum loop count per article type.")
    args = parser.parse_args()

    if args.execute:
        payload = run_persona_iterative_trial(
            live=bool(args.live),
            run_root=args.run_root,
            max_loops=max(1, min(5, int(args.max_loops))),
        )
    else:
        payload = initialize_trial_artifact_dir(
            run_root=args.run_root,
            max_loops=max(1, min(5, int(args.max_loops))),
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
