# ROLLBACK

## Boundary

This package is docs and live-observation artifacts only.

Rollback means removing or archiving:

- `C:\tetie\notecode\plan\current_mainline_source_grounding_live_observation_2026-04-25\`
- `C:\tetie\notecode\logs\current_mainline_source_grounding_live_observation_20260425-*\`
- the matching `C:\tetie\WORKLOG.md` entry

## Product Code

No product code is in scope.

Do not rollback or edit:

- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`

## Stop Conditions

- UI cannot be reached or started.
- UI harness cannot prove generation start or fresh snapshot after one rerun.
- New telemetry keys are missing from fresh artifacts.
- More than 3 repeated errors occur in the same phase.

