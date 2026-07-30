# ROLLBACK

## Rollback Boundary

Rollback this package by reverting only:

- `C:\tetie\notecode\note\note_writer_app.py`
  - review-required draft result restoration
  - review-required draft snapshot `blocked=false` persistence
- `C:\tetie\notecode\note\tests\test_note_writer_app_snapshot_helpers.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_ui_result_adapter.py`
- `C:\tetie\notecode\plan\current_mainline_company_intro_blocked_redaction_diagnosis_2026-04-26\`
- matching `C:\tetie\WORKLOG.md` entry

## Do Not Roll Back

Do not roll back or edit:

- `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\blog_image_auto.py`

## Preserved Redaction Boundary

Redaction must remain enabled for:

- true blocked output guard results
- failed generation results
- guard retry failure results
- policy / legal / internal leakage / source-outside claim cases

## Stop Boundary

Stop and report instead of widening the change if:

- the fix requires changing output guard thresholds
- the fix requires changing source contract or prompt behavior
- true blocked output starts appearing as review-required draft
- owner scope expands beyond `note_writer_app.py`

