from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from nicegui_app import (
    _build_auto_open_note,
    _build_completion_progress_text,
    _build_running_progress_text,
    _build_saved_run_status_text,
    _dashboard_progress_refresh_action,
    _format_progress_elapsed,
    _normalize_input_url,
    _validate_analysis_input_url,
)
from core.ui.dashboard import (
    _compact_datetime,
    _extract_row_id_from_event_args,
    build_dashboard_value_cards,
    build_history_rows,
)


def test_build_history_rows_adds_compact_dashboard_fields() -> None:
    rows = build_history_rows(
        [
            {
                "id": 12,
                "analyzed_at": "2026-04-03 10:20:30",
                "url": "https://example.com/very/long/path/to/a/resource/that/should/be/shortened",
                "seo_score": 78,
                "aio_score": 64,
                "legal_score": 80,
                "total_issues": 4,
                "result_path": "outputs/reports/run-12.json",
                "snapshot_json": {
                    "meta": {"site_type": "企業", "industry": "IT・SaaS"},
                    "header": {
                        "integrated_score": 71,
                        "priority_level": "中",
                        "top_actions": [
                            {
                                "title": "冒頭で結論を先出しし、引用向け要約と数値根拠を整理して、CTAまでの導線を一文で理解できる構成へ直す",
                            }
                        ],
                    },
                },
            }
        ]
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["analyzed_at"] == "2026-04-03 19:20 JST"
    assert row["display_date"] == "04/03 19:20 JST"
    assert row["display_url"].startswith("example.com/")
    assert row["display_url"].endswith("…")
    assert row["score_summary"] == "総合 71 / AI 64 / SEO 78"
    assert row["issue_summary"] == "4件"
    assert row["top_action"] == "冒頭で結論を先出しし、引用向け要約と数値根拠を整理して、CTAまでの導線を一文で理解できる構成へ直す"
    assert row["top_action_compact"].endswith("…")


def test_compact_datetime_formats_saved_run_timestamps() -> None:
    assert _compact_datetime("2026-04-03 10:20:30") == "04/03 19:20 JST"
    assert _compact_datetime("2026-04-03T10:20:30") == "04/03 19:20 JST"
    assert _compact_datetime("2026-04-03T10:20:30+09:00") == "04/03 10:20 JST"


def test_extract_row_id_from_event_args_supports_dict_and_list_payloads() -> None:
    assert _extract_row_id_from_event_args({"row": {"id": 84}}) == 84
    assert _extract_row_id_from_event_args([{"row": {"id": 96}}]) == 96
    assert _extract_row_id_from_event_args([{"x": 1}, {"id": 73}, 0]) == 73


def test_normalize_input_url_adds_https_for_bare_host() -> None:
    assert _normalize_input_url("example.com/path") == "https://example.com/path"


def test_validate_analysis_input_url_rejects_invalid_format() -> None:
    normalized, error = _validate_analysis_input_url(
        "not a url",
        label="対象URL",
        required=True,
    )

    assert normalized == "not a url"
    assert error == "対象URLに空白が含まれています。"


def test_validate_analysis_input_url_allows_optional_empty_competitor() -> None:
    normalized, error = _validate_analysis_input_url(
        "",
        label="比較競合URL",
        required=False,
    )

    assert normalized == ""
    assert error is None


def test_auto_open_copy_helpers_switch_between_auto_open_and_stay_mode() -> None:
    assert "自動で開きます" in _build_auto_open_note(True)
    assert "この画面にとどまり" in _build_auto_open_note(False)
    assert "保存済みワークスペースを開きます" in _build_completion_progress_text(True)
    assert "この画面にとどまります" in _build_completion_progress_text(False)
    assert "自動で開かない場合" in _build_saved_run_status_text(True)
    assert "この画面にとどまっています" in _build_saved_run_status_text(False)


def test_running_progress_text_includes_stage_detail_percent_and_elapsed() -> None:
    started_at = datetime(2026, 6, 28, 10, 0, 0)
    now = started_at + timedelta(seconds=75)

    text = _build_running_progress_text(
        "AIO評価",
        0.6,
        "AIOスコア算出",
        started_at,
        now=now,
    )

    assert "AIO評価" in text
    assert "AIOスコア算出" in text
    assert "(60%)" in text
    assert "経過 1分15秒" in text
    assert "目安 1〜3分" in text
    assert _format_progress_elapsed(None, now=now) == "0秒"


def test_dashboard_progress_loop_waits_for_initial_socket_connection() -> None:
    assert _dashboard_progress_refresh_action(False, False) == "wait"
    assert _dashboard_progress_refresh_action(False, True) == "refresh"
    assert _dashboard_progress_refresh_action(True, True) == "stop"
    assert _dashboard_progress_refresh_action(True, False) == "stop"


def test_dashboard_input_errors_use_a_live_region() -> None:
    source = Path(__file__).resolve().parents[1].joinpath("nicegui_app.py").read_text(encoding="utf-8")

    assert source.count('props("role=alert aria-live=polite")') >= 2


def test_dashboard_input_error_is_not_duplicated_and_returns_focus() -> None:
    source = Path(__file__).resolve().parents[1].joinpath("nicegui_app.py").read_text(encoding="utf-8")

    assert 'status_label.text = url_error or competitor_error or ""' not in source
    assert 'invalid_input.run_method("focus")' in source
    assert "scrollIntoView" in source


def test_dashboard_url_field_and_mobile_nav_have_clear_affordances() -> None:
    source = Path(__file__).resolve().parents[1].joinpath("nicegui_app.py").read_text(encoding="utf-8")

    assert '"outlined input-debounce=0 aria-describedby=analysis-url-error"' in source
    assert ".analysis-url-input .q-field__control" in source
    assert ".hub-nav .hub-nav-sep { display: none; }" in source
    assert "justify-content: space-between" in source


def test_dashboard_history_has_explicit_keyboard_accessible_open_actions() -> None:
    source = Path(__file__).resolve().parents[1].joinpath("core", "ui", "dashboard.py").read_text(encoding="utf-8")

    assert '"label": "操作"' in source
    assert 'label="結果を開く"' in source
    assert 'table.on("open_run"' in source
    assert 'table.on("rowClick"' not in source


def test_build_history_rows_prefers_actual_integrated_score_from_result_path(monkeypatch, tmp_path) -> None:
    runs_dir = tmp_path / "runs"
    result_path = runs_dir / "21" / "analysis_result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps({"integrated_results": {"integrated_score": 88}}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr("core.ui.dashboard.RUNS_DIR", runs_dir)

    rows = build_history_rows(
        [
            {
                "id": 21,
                "analyzed_at": "2026-04-03 10:20:30",
                "url": "https://example.com",
                "seo_score": 78,
                "aio_score": 64,
                "legal_score": 80,
                "total_issues": 4,
                "result_path": str(result_path),
                "snapshot_json": {
                    "meta": {"site_type": "企業", "industry": "IT・SaaS"},
                    "header": {
                        "integrated_score": 74,
                        "priority_level": "中",
                        "previous_diff": {"label": "+5"},
                        "top_actions": [],
                    },
                },
            }
        ]
    )

    assert rows[0]["integrated_score"] == 88
    assert rows[0]["score_summary"] == "総合 88 / AI 64 / SEO 78"
    assert rows[0]["previous_diff_label"] == "前回比 +5"


def test_build_history_rows_ignores_result_path_outside_runs_dir(monkeypatch, tmp_path) -> None:
    unsafe_path = tmp_path / "outside" / "analysis_result.json"
    unsafe_path.parent.mkdir(parents=True)
    unsafe_path.write_text(
        json.dumps({"integrated_results": {"integrated_score": 5}}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr("core.ui.dashboard.RUNS_DIR", tmp_path / "runs")

    rows = build_history_rows(
        [
            {
                "id": 22,
                "analyzed_at": "2026-04-03 10:20:30",
                "url": "https://example.com",
                "seo_score": 78,
                "aio_score": 64,
                "legal_score": 80,
                "total_issues": 4,
                "result_path": str(unsafe_path),
                "snapshot_json": {
                    "meta": {"site_type": "企業", "industry": "IT・SaaS"},
                    "header": {
                        "integrated_score": 74,
                        "priority_level": "中",
                        "previous_diff": {"label": "+5"},
                        "top_actions": [],
                    },
                },
            }
        ]
    )

    assert rows[0]["integrated_score"] == 74
    assert rows[0]["score_summary"] == "総合 74 / AI 64 / SEO 78"


def test_build_dashboard_value_cards_highlights_latest_outcome() -> None:
    cards = build_dashboard_value_cards(
        [
            {
                "display_url": "example.com/service",
                "score_summary": "総合 82 / AI 79 / SEO 85",
                "priority_level": "中",
                "issue_summary": "3件",
                "top_action_compact": "冒頭で結論を先出しする…",
                "previous_diff_label": "前回比 +6",
            }
        ]
    )

    assert cards[0]["title"].startswith("検索と AI 回答")
    assert cards[1]["eyebrow"] == "最近の成果"
    assert "example.com/service" in cards[1]["body"]
    assert "冒頭で結論を先出しする" in cards[1]["body"]
    assert cards[1]["chips"] == ["保存済み 1件", "前回比 +6"]
