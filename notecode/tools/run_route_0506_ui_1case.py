from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from note.route_0506_ui_bridge import (  # noqa: E402
    LOG_ROOT,
    WINDOW3_ARTIFACT_ROOT,
    reset_route_0506_ui_onecase_lock,
    run_route_0506_ui_onecase,
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _input_contract_from_window3(root: Path) -> dict[str, Any]:
    contract_path = root / "input_contract.json"
    if contract_path.exists():
        return _load_json(contract_path)
    route_a_path = PROJECT_ROOT / "logs" / "latest_generation_output.json"
    return dict(_load_json(route_a_path).get("input_contract") or {})


def run_ui_1case(
    output_root: Path,
    *,
    input_contract: Mapping[str, Any],
    window3_artifact_root: Path = WINDOW3_ARTIFACT_ROOT,
    client_mode: str | None = None,
) -> dict[str, Any]:
    reset_route_0506_ui_onecase_lock()
    result = run_route_0506_ui_onecase(
        dict(input_contract),
        artifact_root=output_root,
        window3_artifact_root=window3_artifact_root,
        client_mode=client_mode,
    )
    return dict(result.get("validation_summary") or {})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="")
    parser.add_argument("--window3-artifact-root", default=str(WINDOW3_ARTIFACT_ROOT))
    parser.add_argument("--input-contract", default="")
    parser.add_argument("--route-0506-client-mode", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    window3_root = Path(args.window3_artifact_root)
    input_contract = _load_json(Path(args.input_contract)) if args.input_contract else _input_contract_from_window3(window3_root)
    output_root = Path(args.output_root) if args.output_root else LOG_ROOT / f"route_0506_ui_1case_{_now_stamp()}"
    summary = run_ui_1case(
        output_root,
        input_contract=input_contract,
        window3_artifact_root=window3_root,
        client_mode=args.route_0506_client_mode or None,
    )
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"wrote {output_root}")
    return 0 if summary.get("route_0506_status") == "completed" else 1


def _now_stamp() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y%m%d-%H%M%S")


if __name__ == "__main__":
    raise SystemExit(main())
