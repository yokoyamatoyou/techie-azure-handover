# current_mainline_source_grounding_observability_2026-04-25 ROLLBACK

## Baseline

- Current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current source of truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`

## Rollback Boundary

- Product rollback target:
  - source grounding diagnostic telemetry in `quality_observability_mixin.py`
  - focused tests added in `test_newalgorithm_phase06_logging_compat.py`
- Roll back only the new internal telemetry and tests.

## Do Not Roll Back For

- Existing `source_grounding:weak_reflection` remaining fail-closed.
- Existing fingerprint-only warning policy remaining scoped.
- Diagnostics showing anchor mismatch without changing pass/fail state.

## Do-Not-Retry

- `source_grounding:weak_reflection` warning-only demotion.
- Source grounding threshold relaxation.
- Fingerprint threshold relaxation.
- Prompt accretion.
- Repair trigger / repair count change.
- Target length change.
- Source packet broadening.
- UI display of raw diagnostics.
- `note_writer_app.py` or `output_guard.py` demotion branch.

## Stop Boundary

- More than one product owner file is required.
- Existing reflection ratio or warning emission changes.
- Product success/fail behavior changes.
- Diagnostics become unbounded or reader-facing.
