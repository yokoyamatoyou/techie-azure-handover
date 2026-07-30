from __future__ import annotations

import json

from core.monitoring.history_store import (
    get_monitoring_history_path,
    load_monitoring_history,
    save_monitoring_history,
)


def test_monitoring_history_store_roundtrip(tmp_path) -> None:
    path = get_monitoring_history_path(cwd=str(tmp_path))
    history = [{"url": "https://example.com", "aio_score": 80.0}]

    save_monitoring_history(history, path=path)

    assert load_monitoring_history(path=path) == history


def test_load_monitoring_history_returns_empty_for_invalid_json(tmp_path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{invalid", encoding="utf-8")

    assert load_monitoring_history(path=str(path)) == []


def test_get_monitoring_history_path_uses_outputs_monitoring_directory(tmp_path) -> None:
    path = get_monitoring_history_path(cwd=str(tmp_path))

    assert path.endswith("outputs\\monitoring\\aio_monitoring.json")
    assert json.loads(json.dumps({"path": path}))["path"] == path
