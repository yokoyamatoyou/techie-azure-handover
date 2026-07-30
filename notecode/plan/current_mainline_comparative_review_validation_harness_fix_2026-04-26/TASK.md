# current_mainline_comparative_review_validation_harness_fix_2026-04-26 TASK

## Phase Map

| Phase | Owner | Status | Gate |
|---|---|---|---|
| 0 Read / baseline | docs | complete | Diagnosis package and harness owner read; product hashes captured |
| 1 Package docs | docs | complete | README / TASK / PROGRESS / ROLLBACK created |
| 2 Harness fix | validation harness | complete | Comparative case writer role changed to UI-accepted value only |
| 3 Static check | validation harness | complete | `py_compile` passed |
| 4 Focused UI rerun | validation harness | complete | comparative attempts 1 and 2 rerun through actual UI |
| 5 Classification / closeout | docs | complete | Results classified, WORKLOG updated, product files verified untouched |

## Narrow Hypothesis

Only `bl-comparative-selection-criteria` is blocked by an invalid harness-selected writer role. Replaying the same comparative source and route with `編集担当として語る` should avoid the UI validation bubble and reach generation.

## Required Checks

- `確認へ` does not remain disabled due to writer-role validation.
- The generation button path is reached.
- Fresh `latest_generation_output.json` is saved per attempt.
- `source_documents_count=3` or source packet records 3 docs.
- `article_type=comparative_review`.
- UI/body internal-term leakage is empty.
- Body reflects:
  - price
  - approval flow
  - support density
- Image generation is not requested as validation evidence.

## Stop Boundary

Stop and report if:

- A product code change appears necessary.
- The same validation bubble remains after the harness writer-role change.
- UI server cannot start or `18080` remains occupied by an unknown process.
- Both attempts stop with a new unexplained harness failure before generation.

## Final Result

- Harness bubble fix succeeded.
- Both attempts reached generation and saved fresh snapshots.
- Both attempts classified as:
  - `input_required_block`
  - `regression_candidate`
  - `source_caveat`
- No product owner is assigned from this package.
