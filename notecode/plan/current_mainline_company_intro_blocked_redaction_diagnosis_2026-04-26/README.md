# current_mainline_company_intro_blocked_redaction_diagnosis_2026-04-26

## Objective

Diagnose and fix the `company_introduction` `blocked_output_redacted=true` stop condition observed in:

- `C:\tetie\notecode\logs\pre_user_trial_ui_runtime_validation_rerun_20260426-214042\`

The first implementation is intentionally narrow:

- owner: `C:\tetie\notecode\note\note_writer_app.py`
- hypothesis: `review_required_draft` was persisted as a redacted blocked snapshot even though the UI classification remained review-required and the body existed.

## Source Artifacts

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\current_mainline_pre_user_trial_ui_runtime_stability_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\logs\pre_user_trial_ui_runtime_validation_rerun_20260426-214042\summary.json`
- `C:\tetie\notecode\logs\pre_user_trial_ui_runtime_validation_rerun_20260426-214042\per_attempt_summary.jsonl`
- `C:\tetie\notecode\logs\pre_user_trial_ui_runtime_validation_rerun_20260426-214042\manual_review_notes.md`
- `C:\tetie\notecode\logs\pre_user_trial_ui_runtime_validation_rerun_20260426-214042\final_app_log_excerpt.txt`
- attempt-local `latest_generation_output.json` and `latest_generation_quality_report.json`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\notecode\ALGORITHM.md` sections 4, 5, 12, 13
- `C:\tetie\WORKLOG.md`

## Diagnosis

Primary classification:

- `review_required_draft` snapshot / harness classification mismatch.

Evidence:

- company_introduction attempt 2/3 had non-empty body.
- `needs_input_items=[]`, `hard_reasons=[]`, `manual_instructional_hits=[]`.
- internal leakage count was `0`.
- source-outside claim was not observed.
- app log recorded `outcome=review_required_draft phase=quality_output_guard`.
- latest snapshot was persisted with `blocked=True`, causing `full_text=[BLOCKED_OUTPUT_REDACTED]` and `blocked_output_redacted=true`.
- summary/per_attempt then classified it as `input_required_block`.

Not first blocker:

- true unsafe/input invalid block
- legal-risk block
- internal leakage
- unconditional redaction policy
- source contract / algorithm tuning
- threshold relaxation
- image generation

## Attempt Difference

| Item | Attempt 1 | Attempt 2 | Attempt 3 |
|---|---:|---:|---:|
| runtime_reason_code | `OK` | `SYS_QUALITY_WARNINGS_UNRESOLVED` | `SYS_QUALITY_WARNINGS_UNRESOLVED` |
| app outcome | success / quality warning | `review_required_draft` | `review_required_draft` |
| summary outcome | `publishable_success` | `input_required_block` | `input_required_block` |
| body_chars | 1224 | 1271 | 1126 |
| internal leakage | 0 | 0 | 0 |
| source-outside claim | not observed | not observed | not observed |
| needs_input_items | empty | empty | empty |
| hard_reasons | empty | empty | empty |
| source_grounding ratio | 0.6 | 0.4 | 0.2 |
| blocked_output_redacted | false | true | true |

## Implementation Summary

Changed only the review-required draft path in `note_writer_app.py`:

- rebuild `full_text` / `full_body` for the review-required draft result
- set `blocked_output_redacted=false` on that result
- persist the `review_required_draft` latest snapshot with `blocked=false`

Preserved:

- `runtime_reason_code=SYS_QUALITY_WARNINGS_UNRESOLVED`
- `ui_review_required_draft=true`
- `ui_fail_closed_ux_classification=review_required_draft`
- output guard `blocked`, `warning_fail_closed`, and soft warnings inside `pipeline_check`
- redaction for true `blocked_generation`, `failed_generation`, and `guard_retry_failure`

## Decision

User trial is still not reopened by this package alone.

Next required user-trial readiness work:

- complete copy representative check
- complete legal representative check
- if runtime validation is requested, run only the smallest smoke shape and do not run full-flow validation

