from __future__ import annotations

from core.application.csv_export_service import (
    export_history_csv,
    export_priority_actions_csv,
    sanitize_csv_cell,
)


def test_sanitize_csv_cell_guards_formula_injection() -> None:
    assert sanitize_csv_cell("=SUM(A1:A2)") == "'=SUM(A1:A2)"
    assert sanitize_csv_cell("+1") == "'+1"
    assert sanitize_csv_cell("@cmd") == "'@cmd"
    assert sanitize_csv_cell("safe") == "safe"


def test_export_history_csv_writes_sanitized_rows(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("core.application.csv_export_service.EXPORTS_DIR", tmp_path)

    path = export_history_csv(
        [
            {
                "id": 1,
                "analyzed_at": "2026-04-02 12:00:00",
                "url": "https://example.com",
                "site_type": "企業",
                "industry": "IT",
                "seo_score": 80,
                "aio_score": 70,
                "legal_score": 90,
                "integrated_score": 80,
                "priority_level": "中",
                "total_issues": 3,
                "top_action": "=malicious()",
                "result_path": "C:/tmp/run.json",
            }
        ]
    )

    content = path.read_text(encoding="utf-8-sig")
    assert "'=malicious()" in content
    assert "https://example.com" in content
    assert "2026-04-02 21:00 JST" in content


def test_export_priority_actions_csv_writes_expected_columns(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("core.application.csv_export_service.EXPORTS_DIR", tmp_path)
    snapshot = {
        "exports": {
            "priority_actions": [
                {
                    "action_id": "act_example",
                    "area": "AI認識改善",
                    "category": "AIO",
                    "label": "今回のURL",
                    "title": "冒頭要約を追加",
                    "action": "結論を先頭3文に集約する",
                    "detail": "AI検索向け",
                    "role": "運用",
                    "effort": "1h",
                    "urgency": "中",
                    "kpi": "AI認識",
                    "impact": "High",
                }
            ]
        }
    }
    run_row = {"id": 10, "analyzed_at": "2026-04-02 12:00:00", "url": "https://example.com"}

    path = export_priority_actions_csv(snapshot, run_row)
    content = path.read_text(encoding="utf-8-sig")

    assert "priority_rank" in content
    assert "action_id" in content
    assert "act_example" in content
    assert "category" in content
    assert "urgency" in content
    assert "audience" in content
    assert "evidence" in content
    assert "status" in content
    assert "冒頭要約を追加" in content
    assert "https://example.com" in content
    assert "2026-04-02 21:00 JST" in content
