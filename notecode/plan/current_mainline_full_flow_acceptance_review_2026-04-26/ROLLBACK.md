# ROLLBACK

## Rollback Boundary

This package is docs-only.

Rollback means deleting or superseding:

- `C:\tetie\notecode\plan\current_mainline_full_flow_acceptance_review_2026-04-26\README.md`
- `C:\tetie\notecode\plan\current_mainline_full_flow_acceptance_review_2026-04-26\TASK.md`
- `C:\tetie\notecode\plan\current_mainline_full_flow_acceptance_review_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_full_flow_acceptance_review_2026-04-26\ROLLBACK.md`
- the matching `C:\tetie\WORKLOG.md` entry

## Product Runtime Boundary

Do not rollback or modify product runtime files for this package.

Runtime files explicitly outside this rollback:

- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`

## Do-not-retry Boundaries

- Do not rerun generation as part of this package.
- Do not start the UI server as part of this package.
- Do not reinterpret the source manifest from moving `latest_generation_output.json`.
- Do not change prompt, threshold, repair, guard, or UI behavior in this package.

## Safe Follow-up

If implementation is needed later, create a separate package for the first candidate only:

- `company_introduction_kyoto_latest_log` attempt 2
- owner: UI/result classification boundary
- hypothesis: review-required draft UI wording and summary `input_required_block` classification diverge when `blocked_output_redacted=true`
