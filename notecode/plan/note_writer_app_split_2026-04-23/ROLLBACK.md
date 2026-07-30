# note_writer_app_split_2026-04-23 ROLLBACK

## Baseline

- restore target:
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\current_mainline_runtime_logging.py`
- current package boundary:
  - `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\README.md`
  - `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\TASK.md`
  - `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md`
  - `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\ROLLBACK.md`
  - `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\EXECUTION_PROMPT.md`
- global current source of truth remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- reference boundary:
  - `C:\tetie\notecode\current_mainline_owner_split\`
  - `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\`
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\`
  - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\`
  - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`
  - reopen しない

## Locked Keep Boundary

- current success path:
  - `current_mainline_runner -> newalgorithm_pipeline -> simple_note_pipeline`
- `note_writer_app.py` remains:
  - UI shell owner
  - confirm-before-generate flow owner
  - actual widget mutation owner
  - logging trigger timing owner
- `input_decision` source of truth remains outside UI shell
- logging schema / file persistence remains in `current_mainline_runtime_logging.py`
- GPT Image 2 remains post-success work
- `single-pass + optional single repair 1回` remains fixed
- `naturalness_recovery_2026-04-07` remains global current source of truth

## Rollback Rule

- rollback is phase-local and owner-local
- one phase equals one rollback unit
- if a phase requires cross-owner edits to recover, stop and do not widen the rollback unit
- if runtime drift appears, revert only the touched phase diff and keep other phases parked
- docs package itself is not a reason to reopen `current_mainline_owner_split`

## Phase-Local Rollback Targets

- Phase 01:
  - revert head asset extraction only
  - do not mix with source helper or `main_page()` builder edits
- Phase 02:
  - revert source/upload/bootstrap helper extraction only
  - restore import-time cleanup behavior exactly
- Phase 03:
  - revert subview extraction only
  - restore source/blur/generated-image UI inline definitions
- Phase 04:
  - revert manual legal helper extraction only
  - keep `_resolve_current_mainline_auto_legal_postcheck` untouched
- Phase 05:
  - revert pre-generation builder extraction only
  - restore journey/source-mode/wizard blocks inline
- Phase 06:
  - revert post-generation builder extraction only
  - do not widen into `run_generation()` timing owner

## Do-Not-Retry

- `run_generation()` body 本体を初手に分割すること
- completion / exception / finally cleanup timing を early phase に入れること
- `_run_current_mainline_image_prompt_step` を early phase に入れること
- `_resolve_current_mainline_auto_legal_postcheck` を early phase に入れること
- confirm state mutation を builder extraction と同時に動かすこと
- `input_decision` source of truth を UI 側へ戻すこと
- logging schema / file persistence を UI shell helper module へ寄せること
- `naturalness_recovery_2026-04-07` とこの split package を混ぜること
- `current_mainline_owner_split` completed judgment を雑に reopen すること
- completed / frozen reference package を reopen すること
- algorithm contract を変えること

## Current Stop Boundary

- same phase fails `2/2`
- rollback cannot be done within one phase unit
- current success path regression appears
- phase requires `run_generation()` timing owner change
- phase requires `current_mainline_runner.py`, `input_contract.py`, or `current_mainline_runtime_logging.py` ownership change
- phase requires GPT Image 2 to move into article mainline

## Park Boundary

- if the next useful edit is late-phase only, park the package and wait for a new decision
- do not hide a parked state by widening the current phase
- keep the docs package as source of truth even when runtime execution is paused
