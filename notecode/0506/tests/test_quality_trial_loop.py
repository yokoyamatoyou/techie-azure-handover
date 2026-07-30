from pathlib import Path

from app.evals.quality_trial_loop import run_url_quality_trial
from app.services.source_acquisition import ExtractedSource, SourceSpan


def test_url_quality_trial_writes_trial_log(monkeypatch, tmp_path: Path):
    def fake_extract(url: str) -> ExtractedSource:
        text = "京都工業はデータ入力を支援しています。入力から納品まで対応します。"
        return ExtractedSource(
            source_id="url_fake",
            source_type="url",
            title="京都工業テスト",
            extracted_text=text,
            source_spans=[SourceSpan("url_001", text, "html:main")],
            metadata={
                "url": url,
                "canonical_url": url,
                "fetch_status": 200,
                "extraction_method": "public_html",
            },
            warnings=[],
            extraction_confidence="medium",
            can_proceed=True,
        )

    monkeypatch.setattr("app.evals.quality_trial_loop.extract_url_source", fake_extract)

    log = run_url_quality_trial(
        ["https://example.test/"],
        trial_id="trial_test",
        artifacts_dir=tmp_path,
        web_research=[{"title": "official", "url": "https://example.test/", "note": "public official source"}],
        hypothesis="log structure smoke",
    )

    artifact_dir = Path(log["artifacts"]["artifact_dir"])
    assert log["trial_id"] == "trial_test"
    assert log["source_totals"]["source_count"] == 1
    assert log["source_readiness"][0]["can_proceed"] is True
    assert (artifact_dir / "trial_log.json").exists()
    assert (artifact_dir / "source_readiness.json").exists()
    assert (artifact_dir / "pipeline_observer_report.json").exists()
    assert (artifact_dir / "pipeline_diagnostics.json").exists()
    assert (artifact_dir / "latest_generation_output.md").exists()
    assert log["pipeline_diagnostics"]["checks"]["editing_persona_fired"]["pass"] is True
    assert log["pipeline_diagnostics"]["checks"]["structured_source_passed_to_generation"]["pass"] is True
