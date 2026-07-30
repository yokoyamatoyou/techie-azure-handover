from note.note_writer_quality_report_helpers import _extract_fingerprint_phase_report


def test_extract_fingerprint_phase_report_supports_nested_reports() -> None:
    report = _extract_fingerprint_phase_report(
        {
            "reports": [
                {"phase": "other"},
                {
                    "phase_reports": [
                        {
                            "phase": "fingerprint",
                            "flat_zone_flags": ["flat"],
                            "overall_unpredictability": "0.123456",
                            "correction_hints": ["hint"],
                            "fingerprint_correction_applied": True,
                            "nominalization_rate": 0.2,
                            "sentence_ending_entropy": 0.3,
                            "sentence_ending_fine_entropy": 0.4,
                            "subject_explicit_rate": 0.5,
                            "mtld": 6.78901,
                        }
                    ]
                },
            ]
        }
    )

    assert report["flat_zone_flags"] == ["flat"]
    assert report["overall_unpredictability"] == 0.1235
    assert report["correction_hints"] == ["hint"]
    assert report["fingerprint_correction_applied"] is True
    assert report["mtld"] == 6.789


def test_extract_fingerprint_phase_report_returns_empty_when_missing() -> None:
    assert _extract_fingerprint_phase_report({"reports": [{"phase": "body"}]}) == {}
