# current_mainline_company_intro_result_classification_closeout_2026-04-26 EXECUTION_PROMPT

`C:\tetie\notecode` の `company_introduction_kyoto_latest_log` attempt 2 classification closeout follow-up を進めてください。

This package has already completed the docs-only diagnosis. If implementation is authorized, keep the work limited to validation summary / artifact collector classification. Do not change product generation behavior.

## 最初に読む

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\current_mainline_company_intro_result_classification_closeout_2026-04-26\README.md`
4. `C:\tetie\notecode\plan\current_mainline_company_intro_result_classification_closeout_2026-04-26\TASK.md`
5. `C:\tetie\notecode\plan\current_mainline_company_intro_result_classification_closeout_2026-04-26\PROGRESS.md`
6. `C:\tetie\notecode\plan\current_mainline_company_intro_result_classification_closeout_2026-04-26\ROLLBACK.md`
7. `C:\tetie\notecode\logs\current_mainline_full_flow_regression_from_manifest_20260426-000000\ui_live\company_introduction_kyoto_latest_log\attempt_2\attempt_summary.json`
8. `C:\tetie\notecode\logs\current_mainline_full_flow_regression_from_manifest_20260426-000000\ui_live\company_introduction_kyoto_latest_log\attempt_2\ui_visible_text.txt`
9. `C:\tetie\notecode\logs\current_mainline_full_flow_regression_from_manifest_20260426-000000\ui_live\company_introduction_kyoto_latest_log\attempt_2\latest_generation_output.json`
10. `C:\tetie\WORKLOG.md`

## Objective

- Distinguish validation summary `input_required_block` from `review_required_draft_candidate` for artifacts like `company_introduction_kyoto_latest_log` attempt 2.
- Keep true input blocks unchanged.
- Do not turn this result into `publishable_success`.

## Required Behavior

Classify as `review_required_draft_candidate` when all are true:

- `needs_input_items=[]`
- body exists
- no internal-term leakage
- no source outside claim
- visible UI says `確認が必要なドラフトです`
- runtime reason is `SYS_QUALITY_WARNINGS_UNRESOLVED`

Keep `input_required_block` when the artifact has actual input-precondition failure, body absence, route mismatch, unsafe leakage, source outside claim, legal/guarantee stop, manual instructional hits, or any other condition requiring user correction before review.

## Owner

- First owner only:
  - validation harness / package runner artifact collector

Do not edit first:

- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\current_mainline_ui_result_adapter.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Non-Goals

- no product generation behavior change
- no prompt change
- no threshold change
- no repair change
- no guard change
- no source contract change
- no generation rerun
- no UI server startup
- no split extraction
- no `note_writer_app.py` Phase 04

## Verification

- Add focused summary mapping test or artifact-based assertion.
- Expected for this attempt:
  - `review_required_draft_candidate`
  - `validation_harness_summary_mapping_issue`
  - not `publishable_success`
  - not true `input_required_block`
- Confirm product runtime files remain untouched.
