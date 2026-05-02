"""Tests for zero-base phase02 dependency map and cutline."""

from __future__ import annotations

from importlib import import_module

from core import app_config
from note.zero_base.phase02_dependency_map import (
    build_dependency_index,
    detect_cycles,
)


def test_phase02_dependency_graph_has_no_cycles() -> None:
    entries = build_dependency_index()
    cycles = detect_cycles(entries)
    assert cycles == []


def test_phase02_dependency_output_format_fields() -> None:
    entries = build_dependency_index()
    for entry in entries:
        assert set(entry.keys()) == {
            "module",
            "depended_by",
            "role_in_zero_base",
            "decision",
        }
        assert entry["decision"] in {"keep", "drop", "observe_only"}


def test_phase02_feature_flag_unknown_mode_falls_back_without_import_error() -> None:
    original_loader = app_config._load_config_file
    try:
        app_config._load_config_file = lambda: {"generation_mode": "invalid_mode"}  # type: ignore[assignment]
        assert app_config.get_generation_mode() == "zero_base_v2"
        module = import_module("note.article_generator")
        assert module is not None
    finally:
        app_config._load_config_file = original_loader  # type: ignore[assignment]
