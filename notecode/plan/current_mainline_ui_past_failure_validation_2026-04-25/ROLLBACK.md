# current_mainline_ui_past_failure_validation_2026-04-25 ROLLBACK

## Baseline

- Runtime mainline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current planning source of truth remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- This package is a UI validation package and does not replace the current naturalness source of truth.

## Rollback Boundary

- Docs-only rollback:
  - remove or supersede `C:\tetie\notecode\plan\current_mainline_ui_past_failure_validation_2026-04-25\`
- Validation logs rollback:
  - remove only timestamped logs created by this package if needed.
- UI code rollback:
  - revert only the isolated display diff in `C:\tetie\notecode\note\current_mainline_ui_result_adapter.py`
  - revert the matching assertions in `C:\tetie\notecode\note\tests\test_current_mainline_ui_result_adapter.py`
  - do not revert runtime generation logic; none was changed in this package.

## Do Not Retry

- Do not retry by broadly increasing article length.
- Do not relax `quality_guard.py`.
- Do not increase repair count.
- Do not change `target_chars` / `length_mode`.
- Do not change repair acceptance.
- Do not add prompt blocks to hide thinness.
- Do not expose persona names, editor names, trial names, source contract wording, `source_limit`, `hidden`, `PATCH_SCOPE`, `SEMANTIC_LEDGER`, `SECTION_SHADOW`, or validation terms in visible text.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.
- Do not undo `pipeline_responsibility_split_2026-04-24`.
- Do not add source-outside claims or generic padding.
- Do not broaden source packet thickness.

## Stop Boundary

- Same UI startup or operation error repeats `3` times.
- UI validation cannot distinguish UI route defect from runtime body realization issue.
- Evidence requires multiple owner changes.
- Runtime fix would require source-outside claims or generic padding.
- Current success path regression appears.

## Expected Failure Modes

- UI accepts input but maps article type / semantic key incorrectly.
- URL/text source handoff differs from runner fixtures.
- Fail-closed or input-boundary errors are displayed as blank or stale success.
- latest snapshot/log files are not updated after UI generation.
- Browser automation cannot operate the NiceGUI UI reliably.
- Successful body remains thin, which should be recorded as `realization_shallow_followup` unless it is a regression.
- Output-guard display can expose internal reason names if the adapter rollback is applied.
