# TASK

## Phase Map

| Phase | Owner | Gate |
|---|---|---|
| 0 artifact diagnosis | docs | summary / per_attempt / app log / quality report inspected |
| 1 first blocker classification | docs | true unsafe vs mismatch classified |
| 2 narrow implementation | `note_writer_app.py` | review-required snapshot no longer redacted |
| 3 owner-local tests | tests | py_compile and focused pytest pass |
| 4 closeout | docs | package docs and WORKLOG updated |

## Owner Scope

- Product owner: `C:\tetie\notecode\note\note_writer_app.py`
- Test owner:
  - `C:\tetie\notecode\note\tests\test_note_writer_app_snapshot_helpers.py`
  - `C:\tetie\notecode\note\tests\test_current_mainline_ui_result_adapter.py`

## Non-Goals

- prompt / persona / source contract change
- algorithm / threshold / repair count change
- `quality_guard.py` or `output_guard.py` change
- pipeline change
- `blog_image_auto.py` change
- unconditional redaction解除
- UI server startup
- full-flow validation
- bloat split reopen

## Required Checks

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile C:\tetie\notecode\note\note_writer_app.py
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest C:\tetie\notecode\note\tests\test_note_writer_app_snapshot_helpers.py C:\tetie\notecode\note\tests\test_current_mainline_ui_result_adapter.py -q
```

## Acceptance Criteria

- `review_required_draft` snapshot result has body-backed `full_text`.
- `review_required_draft` snapshot result has `blocked_output_redacted=false`.
- `review_required_draft` UI outcome remains `review_required_draft`.
- `SYS_QUALITY_WARNINGS_UNRESOLVED` remains visible in telemetry/result metadata and is not converted to `OK`.
- true blocked quality guard paths remain redacted.
- output guard thresholds and warning policies are unchanged.

