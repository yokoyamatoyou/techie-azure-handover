# ROLLBACK

## Rollback Boundary

This package is docs-only.

Rollback means deleting or superseding:

- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\README.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\TASK.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\ROLLBACK.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\EXECUTION_PROMPT.md`
- the matching `C:\tetie\WORKLOG.md` entry

## Product Runtime Boundary

Runtime files are outside this rollback:

- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\blog_image_auto.py`

## Do-Not-Retry Boundaries

- Do not change product code in this package.
- Do not rerun full-flow validation for this package.
- Do not start the UI server for this package.
- Do not update prompt, threshold, repair count, output guard, quality guard, pipeline, note writer app behavior, or image generation behavior.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.

## Safe Follow-Up

If user trial reveals a failure, create a new narrow package for one issue only.

First likely follow-up candidate:

- `company_introduction` UI/result classification boundary
- symptom: UI visible review-required wording and summary `input_required_block` classification diverge, especially when `blocked_output_redacted=true`
