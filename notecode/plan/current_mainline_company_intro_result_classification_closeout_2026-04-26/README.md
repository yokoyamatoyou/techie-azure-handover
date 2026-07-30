# current_mainline_company_intro_result_classification_closeout_2026-04-26 README

## Objective

- Close out the classification mismatch for `company_introduction_kyoto_latest_log` attempt 2 from the full-flow acceptance artifacts.
- Explain why the validation summary reports `input_required_block` while visible UI says `確認が必要なドラフトです`.
- Decide the full-flow acceptance treatment without changing product code.
- Keep this package docs-only.

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\current_mainline_full_flow_acceptance_review_2026-04-26\PROGRESS.md`
4. `C:\tetie\notecode\plan\current_mainline_bloat_control_priority_2026-04-26\PROGRESS.md`
5. `C:\tetie\notecode\plan\current_mainline_bloat_control_priority_2026-04-26\EXECUTION_PROMPT.md`
6. `C:\tetie\notecode\logs\current_mainline_full_flow_regression_from_manifest_20260426-000000\post_run_acceptance_report.json`
7. `C:\tetie\notecode\logs\current_mainline_full_flow_regression_from_manifest_20260426-000000\ui_live\company_introduction_kyoto_latest_log\attempt_2\`
8. `C:\tetie\WORKLOG.md`

## Scope

- Only `company_introduction_kyoto_latest_log` attempt 2.
- Existing artifacts only.
- No product code, prompt, threshold, repair, guard, generation rerun, UI server startup, split extraction, `pipeline.py` source contract cleanup, or `note_writer_app.py` Phase 04.

## Artifact Root

- Full-flow root:
  - `C:\tetie\notecode\logs\current_mainline_full_flow_regression_from_manifest_20260426-000000\`
- Attempt root:
  - `C:\tetie\notecode\logs\current_mainline_full_flow_regression_from_manifest_20260426-000000\ui_live\company_introduction_kyoto_latest_log\attempt_2\`

## Attempt 2 Classification

| Check | Artifact result | Closeout judgment |
|---|---|---|
| UI visible wording | `確認が必要なドラフトです。公開前に資料と照らし合わせて確認してください。` appears in `ui_visible_text.txt`, DOM, toast, and screenshot | visible UI is review-required wording |
| Summary outcome | `attempt_summary.json` says `input_required_block` | summary is stricter than visible UI |
| Runtime reason | `SYS_QUALITY_WARNINGS_UNRESOLVED` | quality warning path, not input precondition |
| `blocked_output_redacted` | `true`; `full_text=[BLOCKED_OUTPUT_REDACTED]` | likely drives summary mapping toward `input_required_block` |
| Result-side UI fields | `latest_generation_output.json` does not contain `ui_review_required_draft` / `ui_fail_closed_ux_classification` | persisted generation artifact lacks adapter classification |
| `needs_input_items` | empty in summary and output | not an actual input-required block |
| Body | `body_chars=1282`; `output_body.txt` exists | generated body exists internally |
| UI body visibility | final DOM/text show placeholder, not article body | review-draft body rendering is not proven by this artifact |
| Internal-term leakage | none in summary/body/UI scan | no leakage issue |
| Source outside claim | `not_observed` | no outside-claim issue |
| Source | fixed Kyoto 4 URL manifest, `moving_target=false` | source reconstruction is not the cause |

## Decision

- Primary classification:
  - `validation_harness_summary_mapping_issue`
- Secondary classification:
  - `review_required_draft_candidate`
- Not supported:
  - `actual_runtime_input_block`
- Full-flow acceptance treatment:
  - not `publishable_success`
  - not a source reconstruction recurrence
  - not a product generation rerun target
  - count as a review-required candidate whose summary label needs distinction from true input blocks

## Owner Decision

- First owner:
  - validation harness / package runner artifact collector only
- Do not choose as first owner:
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\current_mainline_ui_result_adapter.py`
- Escalate to product owner only if a later artifact-replay check proves product classification or body rendering is wrong.

## Non-Goals

- no source contract changes
- no prompt changes
- no threshold changes
- no repair changes
- no guard changes
- no generation rerun
- no UI server startup
- no split extraction
- no `pipeline.py` source contract cleanup
- no `note_writer_app.py` Phase 04
