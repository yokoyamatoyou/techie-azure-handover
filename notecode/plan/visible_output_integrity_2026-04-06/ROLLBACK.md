# visible_output_integrity_2026-04-06 ROLLBACK

## Baseline

- restore target:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current visible artifact baseline:
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
  - attempt id: `gen-61a76943`
- archive boundary:
  - `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\`
- current package boundary:
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md`
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\TASK.md`
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md`
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\ROLLBACK.md`
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\EXECUTION_PROMPT.md`
- reference boundary:
  - completed:
    - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\`
    - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
  - frozen:
    - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`
  - reopen しない

## Rollback Rule

- archive snapshot を current read order に戻さない
- 各 implementation phase は owner 1 file に閉じる
- rollback は phase owner の narrow diff 単位で行う
- visible red symptom を warning-only success に戻す diff は keep しない

## Do-Not-Retry Hypotheses

- prompt-only strengthening を先にやること
- planner / generator core を初手で触ること
- pre-2026-04-02 records を current planning surface に戻すこと
- title corruption を observe-only で keep すること
- selected visible symptom を warning-only success で render し続けること

## Expected Failure Modes

- title fallback trim のつもりで explanatory title helper が増えるだけになる
- output guard が warning label を増やすだけで blocking boundary が変わらない
- UI surface まで広げなくてよい症状を `note_writer_app.py` へ早戻しする
- pre-2026-04-02 rationale が current source-of-truth に再混入する

## Per-Phase Rollback Intention

### Phase 00 Archive Boundary And Current Snapshot Freeze

- rollback:
  - archive snapshot README/manifest と current package docs を package creation 前の状態へ戻す

### Phase 01 Output Formatter Title Integrity Trim

- rollback:
  - `output_formatter.py` の title fallback trim diff と focused title tests だけを戻す
- latest keep diff:
  - explanatory heading seed の predicate-tail trim helper
  - malformed warm-title reproduction test

### Phase 02 Output Guard Visible Boundary Hardening

- rollback:
  - `output_guard.py` の title integrity / selected visible symptom guard diff と focused tests だけを戻す

### Phase 03 UI Warning Surface Trim

- rollback:
  - `note_writer_app.py` の success / blocked projection diff だけを戻す
