# source_compression_length_adequacy_2026-04-25 ROLLBACK

## Baseline

- Runtime mainline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current planning source of truth remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- This package is an audit package and does not replace the current source of truth.

## Rollback Boundary

- Phase 0-3 rollback is docs/logs only:
  - remove or supersede `C:\tetie\notecode\plan\source_compression_length_adequacy_2026-04-25\`
  - remove or supersede the timestamped logs under `C:\tetie\notecode\logs\source_compression_length_adequacy_*`
- If Phase 4 creates a code fix, rollback is limited to that one owner scope and its focused tests.
- This run did not create a runtime code fix. Current rollback is docs/logs only.

## Audit Artifacts

- Previous validation extraction:
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-092448\previous_validation_metrics.json`
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-092448\previous_validation_metrics.md`
- Live audit:
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\audit_metrics.json`
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\audit_metrics.md`
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\classification.json`
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\classification.md`

## Do Not Retry

- Do not retry by broadening article length globally.
- Do not relax `quality_guard.py`.
- Do not increase repair count.
- Do not add prompt blocks to hide thinness.
- Do not move persona names, editor names, trial names, or internal source contract terms into visible text.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.
- Do not use this package to undo the `pipeline_responsibility_split_2026-04-24` extraction.

## Stop Boundary

- Same phase has 3 repeated failures with the same error.
- Evidence requires multiple owner changes.
- Runtime fix would require source-outside claims or generic padding.
- Current success path regression appears.
