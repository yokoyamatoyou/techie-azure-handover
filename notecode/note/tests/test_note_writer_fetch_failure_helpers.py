from types import SimpleNamespace

from note.note_writer_fetch_failure_helpers import (
    _classify_reason_code,
    _collect_source_notices,
    _extract_403_urls,
    _format_fetch_failures,
    _prepare_current_mainline_fetch_summary,
)


def test_classify_reason_code_groups_known_prefixes() -> None:
    assert _classify_reason_code("INP_MISSING_REQUIRED") == "user_input"
    assert _classify_reason_code("POL_BLOCKED") == "policy"
    assert _classify_reason_code("SEC_BLOCKED") == "policy"
    assert _classify_reason_code("TRN_TIMEOUT") == "transient"
    assert _classify_reason_code("SYS_ERROR") == "system"


def test_format_fetch_failures_infers_pdf_reason_from_generic_detail() -> None:
    text = _format_fetch_failures(
        [
            SimpleNamespace(
                reason="fetch_failed",
                source="sample.pdf",
                detail="pdf extractor not available",
            )
        ]
    )

    assert "PDF抽出ライブラリが見つかりません" in text
    assert "sample.pdf" in text


def test_extract_403_urls_deduplicates_http_sources_only() -> None:
    failures = [
        SimpleNamespace(reason="http_403_forbidden", source="https://example.com/a"),
        SimpleNamespace(reason="http_403_forbidden", source="https://example.com/a"),
        SimpleNamespace(reason="http_403_forbidden", source="file.txt"),
        SimpleNamespace(reason="network_error", source="https://example.com/b"),
    ]

    assert _extract_403_urls(failures) == ["https://example.com/a"]


def test_collect_source_notices_uses_best_source_label_and_limits() -> None:
    contexts = [
        SimpleNamespace(title="Title A", notices=["trimmed", ""]),
        SimpleNamespace(source_path="source.txt", notices=["too long"]),
        SimpleNamespace(url="https://example.com", notices=["notice3", "notice4", "notice5", "notice6"]),
    ]

    assert _collect_source_notices(contexts) == [
        "Title A: trimmed",
        "source.txt: too long",
        "https://example.com: notice3",
        "https://example.com: notice4",
        "https://example.com: notice5",
    ]


def test_prepare_current_mainline_fetch_summary_projects_counts_and_failures() -> None:
    summary = _prepare_current_mainline_fetch_summary(
        contents=[
            SimpleNamespace(content="abc"),
            SimpleNamespace(content="defgh"),
        ],
        failures=[
            SimpleNamespace(
                reason="http_403_forbidden",
                source="https://example.com/blocked",
                detail="forbidden",
            )
        ],
        elapsed_ms=123,
    )

    assert summary["success_count"] == 2
    assert summary["failure_count"] == 1
    assert summary["elapsed_ms"] == 123
    assert summary["total_source_chars"] == 8
    assert summary["event_extra"]["total_source_chars"] == 8
    assert "アクセス拒否" in summary["failure_details"]
    assert summary["blocked_urls"] == ["https://example.com/blocked"]
