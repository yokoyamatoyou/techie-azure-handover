# current_mainline_announcement_source_contract_activation_2026-04-26

## Objective

`current_mainline_announcement_fail_block_diagnosis_2026-04-26` の診断結果を受け、announcement の sufficient source で FAQ facts が `source_grounding_items` / `must_cover` に入らない narrow issue を修正する。

Target case:

- `bl-announcement-spec-change`
- article type: `announcement`
- source adequacy: sufficient
- underlying issue: `announcement_contract_gap`

## Source of Truth

- `C:\tetie\notecode\plan\current_mainline_announcement_fail_block_diagnosis_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_announcement_fail_block_diagnosis_2026-04-26\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\`
- `C:\tetie\WORKLOG.md`

## Owner Scope

Product owner:

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

Test owner:

- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## Non-Goals

- No threshold changes.
- No `prompt_builder.py` changes.
- No repair count changes.
- No UI demote / `note_writer_app.py` changes.
- No `output_guard.py` changes.
- No `quality_guard.py` changes.
- No source-shortage reclassification.
- No expansion to non-announcement article types.

## Fix Summary

Announcement runtime source contract activation now uses fallback source sentences from both source document content and existing grounding fact text. Fallback slot filling chooses better announcement-specific sentence candidates instead of the first broad pattern match.

When an announcement contract is activated from fallback source text, the same bounded slot facts are merged into:

- `source_grounding_items`
- `must_cover`

This lets FAQ preparation and day-of checklist facts reach the runtime contract without adding prompt text or changing guard thresholds.

## Outcome

The targeted FAQ facts now enter both runtime grounding and must-cover inputs:

- `承認者の再設定`
- `通知先の確認`
- `下書き保存`
- `差し戻し通知`
- `公開日時の再指定`

Announcement UI rerun completed 2/2 as `publishable_success` with all five FAQ facts present in body and no internal term leakage.

Artifact:

- `C:\tetie\notecode\logs\current_mainline_announcement_source_contract_activation_20260426-103445\`

The earlier `input_required_block` misunderstanding remains classified as a validation-script / harness outcome issue, not part of this product fix.
