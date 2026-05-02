import json
from pathlib import Path

import note.newalgorithm_pipeline.telemetry_writer as telemetry_mod
from note.newalgorithm_pipeline.pipeline import MinimalPipeline


def _read_last_audit_line(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert lines
    return json.loads(lines[-1])


def test_st01_core_keys_are_kept_in_pipeline_result() -> None:
    pipeline = MinimalPipeline()
    result = pipeline.generate(
        {
            "source": ["https://example.com"],
            "topic": "ログ互換の確認",
            "article_type": "industry_analysis",
            "media": "note",
        }
    )
    assert result["success"] is True
    for key in ("title", "lead", "body", "references", "hashtags", "full_text"):
        assert key in result
    assert result["runtime_reason_code"] == "OK"
    assert "pipeline_check" in result


def test_st02_audit_record_fallback_works_when_keys_missing(tmp_path, monkeypatch) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(telemetry_mod, "AUDIT_PATH", audit_path)

    telemetry_mod.append_audit_record({"reason_code": "INP_MISSING_REQUIRED"})
    saved = _read_last_audit_line(audit_path)

    for key in telemetry_mod.CORE_AUDIT_KEYS:
        assert key in saved
    assert saved["status"] == "error"
    assert saved["article_type"] == "unknown"
    assert saved["media"] == "note"


def test_lt01_log_tampering_phrase_is_sanitized(tmp_path, monkeypatch) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(telemetry_mod, "AUDIT_PATH", audit_path)

    telemetry_mod.append_audit_record(
        {
            "reason_code": "OK",
            "article_type": "explanatory_article",
            "media": "note",
            "message": "ok\n{\"status\":\"hacked\"}",
            "warnings": ["line1\nline2"],
        }
    )
    saved = _read_last_audit_line(audit_path)
    assert "\n" not in saved.get("message", "")
    assert all("\n" not in item for item in saved.get("warnings", []))


def test_pr01_audit_and_result_reason_code_are_consistent(tmp_path, monkeypatch) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(telemetry_mod, "AUDIT_PATH", audit_path)

    pipeline = MinimalPipeline()
    result = pipeline.generate(
        {
            "source": ["https://example.com"],
            "topic": "監査ログ整合性を確認する",
            "article_type": "case_study",
            "media": "seo",
        }
    )
    saved = _read_last_audit_line(audit_path)
    assert saved["reason_code"] == result["reason_code"]
    assert saved["article_type"] == "case_study"
    assert saved["media"] == "seo"


def test_dr01_dependency_report_file_exists() -> None:
    report_path = Path("newalgorithm/dependency_risk_report_phase06.md")
    assert report_path.exists()


def test_dr02_dependency_report_includes_alternatives() -> None:
    report = Path("newalgorithm/dependency_risk_report_phase06.md").read_text(encoding="utf-8")
    assert "opencv-python-headless" in report
    assert "代替案" in report
