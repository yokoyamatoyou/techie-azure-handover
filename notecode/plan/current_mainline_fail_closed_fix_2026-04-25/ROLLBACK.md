# current_mainline_fail_closed_fix_2026-04-25 ROLLBACK

## Baseline

- Runtime mainline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current planning source of truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`

## Rollback Boundary

- Runtime rollback:
  - revert only this package's changes in `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Test rollback:
  - revert only matching focused assertions in `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- Docs rollback:
  - supersede or remove `C:\tetie\notecode\plan\current_mainline_fail_closed_fix_2026-04-25\`
- Artifact rollback:
  - keep validation logs as historical evidence unless explicitly cleaning local generated artifacts
  - generated artifact root: `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_20260425-144208\`

## Implemented Change Set

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - company-introduction-only source-reflection repair activation / acceptance metadata
  - bounded company-introduction unsupported-claim rejection adjustment for negated source-boundary wording
  - case-study runtime source contract merge into source-backed required slot reflection inputs
  - case-study slot extraction refinement for before/change/after/remaining issue
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - focused regression tests for the above private runtime behavior

## Do Not Retry

- Do not relax `quality_guard.py`.
- Do not increase repair count.
- Do not change target chars / length mode.
- Do not broaden source packet thickness again.
- Do not add source-outside claims, new metrics, customer names, awards, or generic padding.
- Do not expose internal terms in body or UI.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.

## Stop Boundary

- Same error repeats 3 times in the same phase.
- Current success path regression appears.
- Fix requires multiple owner files or all-article behavior changes.
- Live UI cannot distinguish runtime realization failure from UI route failure.

## Current Stop State

- Phase 6 actual UI operation reached the same external stop code for both target cases after backend success.
- Do not continue in this package by adding broader article-type routing, changing thresholds, increasing repair count, or raising target length.
- Rollback candidate if this partial runtime behavior is not wanted:
  - revert this package's edits in `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - revert this package's focused tests in `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
