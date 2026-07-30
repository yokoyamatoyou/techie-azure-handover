# current_mainline_bloat_control_priority_2026-04-26 README

## Objective

- current mainline stabilization workで肥大化している owner を整理し、次に進める順番を固定する。
- full-flow品質修正と split 作業を混ぜない。
- まず docs-only で `full-flow closeout -> split -> source contract planning -> extraction -> later cleanup` の優先順位を固定する。
- product code、prompt、threshold、repair、guard、UI implementation は変更しない。

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
6. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\README.md`
7. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\TASK.md`
8. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md`
9. `C:\tetie\notecode\plan\current_mainline_full_flow_acceptance_review_2026-04-26\PROGRESS.md`
10. `C:\tetie\notecode\plan\current_mainline_announcement_source_contract_activation_2026-04-26\PROGRESS.md`
11. `C:\tetie\notecode\plan\current_mainline_comparative_review_contract_activation_2026-04-26\PROGRESS.md`
12. `C:\tetie\notecode\plan\current_mainline_source_grounding_metadata_cleanup_2026-04-26\PROGRESS.md`
13. `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\PROGRESS.md`
14. `C:\tetie\notecode\plan\current_mainline_bloat_control_priority_2026-04-26\README.md`
15. `C:\tetie\notecode\plan\current_mainline_bloat_control_priority_2026-04-26\TASK.md`
16. `C:\tetie\notecode\plan\current_mainline_bloat_control_priority_2026-04-26\PROGRESS.md`
17. `C:\tetie\notecode\plan\current_mainline_bloat_control_priority_2026-04-26\ROLLBACK.md`
18. `C:\tetie\notecode\plan\current_mainline_bloat_control_priority_2026-04-26\EXECUTION_PROMPT.md`
19. `C:\tetie\WORKLOG.md`

## Source Of Truth

- global current source of truth remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- this package is a docs-only priority package and does not replace global current source of truth.
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\` remains the source of truth for `note_writer_app.py` split.
- `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\` is completed reference; do not reopen it for new behavior work.

## Owner Bloat Inventory

| Owner | Current size | Current observation | Priority decision |
|---|---:|---|---|
| `note\simple_note_pipeline\pipeline.py` | `7745` lines | announcement / comparative / company_intro / branding source contract logic has increased. Prior extraction exists, but runtime source contract builder/evaluator planning remains. | Plan after full-flow closeout and UI split window. |
| `note\note_writer_app.py` | `7787` lines | existing split package is Phase 03 completed; Phase 04 manual legal local helpers is pending. | Use existing package; do not create a competing split line. |
| `note\newalgorithm_pipeline\quality_observability_mixin.py` | `1230` lines | source grounding metadata and group diagnostics were recently expanded. | Park unless another observability false-negative appears. |
| `note\newalgorithm_pipeline\output_guard.py` | `884` lines | current size is lower and recent changes are limited. | Park. |

## Priority Table

| Priority | Class | Package / owner | Decision | Reason |
|---:|---|---|---|---|
| 1 | `do-now` | full-flow acceptance closeout follow-up | Select `company_introduction_kyoto_latest_log` attempt 2 UI/result classification mismatch. | This is a stabilization closeout, not split. It has direct SaaS UX impact and must not be mixed into extraction. |
| 2 | `do-next` | `note_writer_app_split_2026-04-23` Phase 04 | Continue existing package with manual legal local helpers extraction only. | Existing plan is already active and Phase 04 is narrow behavior-preserving extraction. |
| 3 | `do-next` | `pipeline.py` source contract split planning | Create a docs-only inventory for announcement / comparative / company_intro / branding source contract logic. | Prevent further accretion before runtime extraction. |
| 4 | `follow-up` | `pipeline.py` source contract extraction | Separate implementation window after docs-only inventory. | Behavior-preserving extraction first; no function fix mixed in. |
| 5 | `park` | `quality_observability_mixin.py` cleanup | Defer. | Recent metadata cleanup is complete; no immediate UX blocker. |
| 6 | `park` | `output_guard.py` cleanup | Defer. | Smaller owner and limited recent churn. |

## Do Now / Do Next / Park

- do-now:
  - `current_mainline_company_intro_result_classification_closeout_2026-04-26`
  - owner: UI/result classification boundary, likely `current_mainline_ui_result_adapter.py` / validation harness summary mapping area
  - objective: align or document the mismatch between summary `input_required_block` and visible review-required draft wording for `company_introduction_kyoto_latest_log` attempt 2
- do-next:
  - `note_writer_app_split_2026-04-23` Phase 04 only
  - `pipeline.py` source contract split planning docs-only
- follow-up:
  - `pipeline.py` source contract behavior-preserving extraction
- park:
  - `quality_observability_mixin.py` cleanup
  - `output_guard.py` cleanup

## Next Package Summary

- package candidate:
  - `C:\tetie\notecode\plan\current_mainline_company_intro_result_classification_closeout_2026-04-26\`
- owner:
  - UI/result classification boundary
  - likely `current_mainline_ui_result_adapter.py` / validation harness summary mapping area
- non-goals:
  - source contract changes
  - prompt changes
  - threshold changes
  - repair changes
  - guard changes
  - generation rerun
  - split extraction
  - `pipeline.py` source contract cleanup
  - `note_writer_app.py` Phase 04
- required first step:
  - use existing artifacts only and classify the mismatch before any product-code edit.

