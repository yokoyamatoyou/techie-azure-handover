# current_mainline_fingerprint_guard_remaining_2026-04-25 ROLLBACK

## Baseline

- Current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current planning source of truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- Predecessor artifact roots:
  - `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_20260425-144208\`
  - `C:\tetie\notecode\logs\current_mainline_ui_backend_divergence_20260425-155544\`

## Rollback Boundary

- Product rollback target if a future Phase 4 diff is retried:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
  - `C:\tetie\notecode\note\tests\test_current_mainline_runner.py`
- Rollback only the stale/non-strict guard refresh diff and matching focused test.
- Plan docs/logs can remain as historical evidence unless explicitly superseded.

## Current Stop State

- Product code changes kept:
  - none
- Attempted and reverted:
  - product-wide recomputation of existing non-strict `output_guard`
  - matching focused regression test
- Product rollback required:
  - none
- Generated artifacts:
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_guard_remaining_20260425-163600\`

## Do Not Roll Back For

- A runner-equivalent backend result changing from predecessor `OK` to `SYS_QUALITY_WARNINGS_UNRESOLVED` when the only difference is correct strict final guard recomputation.
- Case 1 source grounding weak reflection residual without a fingerprint guard connection regression.
- Visible body preference issues that do not prove a source-contract or final-guard connection bug.

## Do-Not-Retry

- Do not relax `quality_guard.py`.
- Do not relax fingerprint thresholds.
- Do not increase repair count.
- Do not tune target chars / length mode as a workaround.
- Do not broaden source packet thickness.
- Do not add prompt-builder growth, persona registry, or article-type fixed routing.
- Do not expose internal terms in visible body or UI.

## Stop Boundary

- Same `fingerprint_guard_remaining` UI failure repeats 3 times after final guard recomputation is proven.
- Required fix crosses multiple product owners.
- Required fix is threshold relaxation or prompt accretion.
- Candidate and final body are both visibly flat/bad and cannot be made acceptable with a single existing repair pass.
