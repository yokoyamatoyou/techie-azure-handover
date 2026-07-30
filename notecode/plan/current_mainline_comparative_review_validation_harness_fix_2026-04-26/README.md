# current_mainline_comparative_review_validation_harness_fix_2026-04-26

## Objective

Fix the `comparative_review` UI validation harness failure identified by `current_mainline_comparative_review_ui_harness_diagnosis_2026-04-26`.

The fix is validation-harness-only. It must not change product code, prompts, thresholds, repair behavior, output guard behavior, or the comparative runtime contract.

## Owner

- `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py`

## Finding

The previous comparative attempts stopped before generation because the harness selected writer role `比較検証担当として語る`. The UI accepted it as a selectable value but then showed the writer-role validation bubble and disabled `確認へ`.

Primary prior classification:

- `validation_bubble_blocked_action`
- downstream `click_or_wait_timeout`

## Fix Direction

For `bl-comparative-selection-criteria` only, the harness uses a UI-accepted writer role:

- `編集担当として語る`

This avoids the writer-role validation bubble and lets the rerun reach actual generation so quality can be classified for the first time.

## Non-Goals

- Do not change product code under `C:\tetie\notecode\note\`.
- Do not change `note_writer_app.py`, `output_guard.py`, or any `pipeline.py`.
- Do not change prompt, threshold, repair, or comparative runtime contract.
- Do not broaden this fix to other article types.
- Do not request image validation for this rerun.

## Acceptance

- `確認へ` is not disabled for `bl-comparative-selection-criteria`.
- Generation reaches a fresh `latest_generation_output.json` for attempts 1 and 2, or stops with a newly explicit harness classification.
- Source 3 docs are present.
- `article_type=comparative_review`.
- UI/body internal-term leakage is absent.
- Price, approval flow, and support density are reflected in the body.

## Outcome

Focused rerun completed for `bl-comparative-selection-criteria` attempts 1 and 2.

- The writer-role validation bubble no longer blocked `確認へ`.
- Fresh `latest_generation_output.json` and `latest_generation_quality_report.json` were saved for both attempts.
- Both attempts generated `article_type=comparative_review` / `semantic_article_key=comparative_review`.
- Both attempts are now classified as generation-quality results:
  - outcome: `input_required_block`
  - runtime reason: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - historical classification: `regression_candidate`, `source_caveat`
- The source caveat remains because the historical source is thin.
- UI/body internal-term leakage was empty.
- Image validation was not requested.
