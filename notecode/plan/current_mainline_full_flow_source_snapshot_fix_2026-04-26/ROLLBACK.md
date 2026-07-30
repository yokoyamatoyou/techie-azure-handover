# ROLLBACK

## Boundary

This is a validation-only package. Rollback is limited to deleting or ignoring:

- `C:\tetie\notecode\plan\current_mainline_full_flow_source_snapshot_fix_2026-04-26\`
- reconstruct-only logs created by `run_full_flow_regression_from_manifest.py`

## Product Files

No rollback is expected for product files because this package must not change:

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- prompt files
- threshold / repair / image implementation

## Stop Rule

If manifest validation fails, stop with artifact and classification. Do not fix product runtime in this package.
