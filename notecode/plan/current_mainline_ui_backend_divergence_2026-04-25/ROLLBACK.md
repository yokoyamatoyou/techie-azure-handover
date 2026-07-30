# current_mainline_ui_backend_divergence_2026-04-25 ROLLBACK

## Baseline

- Current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current planning source of truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- Predecessor artifact root:
  - `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_20260425-144208\`

## Rollback Boundary

- If no product code changes are made, rollback is docs/log-only:
  - supersede or remove `C:\tetie\notecode\plan\current_mainline_ui_backend_divergence_2026-04-25\`
  - keep logs as historical evidence unless explicitly cleaning generated artifacts
- If UI / runner product code is changed, rollback only that narrow diff.
- If runtime is changed after equivalence proof, rollback only the case-scoped runtime diff and matching focused tests.

## Current Stop State

- No product code changes were made.
- Generated artifact root:
  - `C:\tetie\notecode\logs\current_mainline_ui_backend_divergence_20260425-155544\`
- Validation harness:
  - `C:\tetie\notecode\logs\current_mainline_ui_backend_divergence_20260425-155544\ui_validate_equivalence.py`
- Product rollback required:
  - none
- Docs/log rollback:
  - future package can supersede this record.
  - keep generated logs as evidence unless explicitly cleaning local artifacts.

## Classification Outcome

- Initial predecessor diff:
  - `ui_input_mapping_diff`
  - predecessor UI validation did not match backend length/speaker controls.
- After equivalent UI validation:
  - Case 1: `fingerprint_guard_remaining` with intermittent `source_grounding:weak_reflection`
  - Case 4: `fingerprint_guard_remaining`
- Direct backend rerun from exact UI `input_contract`:
  - Case 1: `OK`
  - Case 4: `OK`
- Actual UI operation:
  - Case 1: 3 equivalent attempts still `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - Case 4: 3 equivalent attempts still `SYS_QUALITY_WARNINGS_UNRESOLVED`

## Current Do-Not-Retry

- Do not relax `quality_guard.py`.
- Do not increase repair count.
- Do not tune target chars / length mode as a quality workaround.
- Do not broaden source packet thickness.
- Do not add prompt_builder growth, persona registry, or article-type fixed routing.
- Do not expose internal terms in visible body or UI.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.

## Stop Boundary

- Same UI failure repeats 3 times after equivalent input is proven.
- Required fix crosses multiple product owners.
- Runtime change is requested before payload equivalence is proven.
- Fix requires source-outside claims or generic padding.
