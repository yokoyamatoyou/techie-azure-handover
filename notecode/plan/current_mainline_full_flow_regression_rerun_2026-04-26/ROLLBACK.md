# ROLLBACK

## Boundary

This package is validation-only. Product code is not changed, so rollback is limited to deleting or ignoring validation artifacts from:

- `C:\tetie\notecode\plan\current_mainline_full_flow_regression_rerun_2026-04-26\`
- `C:\tetie\notecode\logs\current_mainline_full_flow_regression_rerun_20260426-132807\`

## Product Files Out Of Scope

Do not edit:

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- prompt files
- threshold / repair / image generation implementation

## Stop Rule

If failures remain, stop after saving artifacts and classify them. Do not open a fix inside this package.
