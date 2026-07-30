# current_mainline_comparative_review_contract_activation_2026-04-26 TASK

## Phase Map

| Phase | Owner | Status | Gate |
|---|---|---|---|
| 0 Read / baseline | docs | complete | Diagnosis package, ALGORITHM sections, pipeline contract code read |
| 1 Package docs | docs | complete | README / TASK / PROGRESS / ROLLBACK created |
| 2 Focused failing tests | tests | complete | Comparative fallback activation test failed before product fix |
| 3 Runtime fix | `simple_note_pipeline/pipeline.py` | complete | Comparative fallback slots and must-cover are source-backed |
| 4 Focused tests | tests | complete | Focused comparative tests pass |
| 5 Focused UI rerun | harness | complete | attempts 1/2 are `publishable_success` / `OK` |
| 6 Shared regression | tests | complete | Required shared test commands pass |
| 7 Closeout | docs | complete | PROGRESS and WORKLOG updated |

## Required Checks

- Focused comparative tests first.
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
- Focused UI rerun:
  - `C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py --case-ids bl-comparative-selection-criteria --attempts 1,2`

## Stop Boundary

Stop and report if:

- Fix requires editing `note_writer_app.py`, `output_guard.py`, or `quality_observability_mixin.py`.
- Fix requires threshold, prompt, or repair changes.
- Same phase needs more than 3 repair attempts.
- The UI rerun remains `input_required_block`; classify the remaining cause before proceeding.

## Final Result

- `comparative_review` fallback source contract now activates from source facts plus comparison axes.
- Generic `総合` must-cover collapse is replaced with concrete comparative anchors.
- Final focused UI rerun:
  - attempt 1: `publishable_success`, `runtime_reason_code=OK`
  - attempt 2: `publishable_success`, `runtime_reason_code=OK`
- No prompt / threshold / repair / UI demote / output guard changes.
