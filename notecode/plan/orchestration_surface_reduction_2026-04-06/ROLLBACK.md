# orchestration_surface_reduction_2026-04-06 ROLLBACK

## Baseline

- restore target:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current package boundary:
  - package docs:
    - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md`
    - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\TASK.md`
    - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md`
    - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\ROLLBACK.md`
    - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\EXECUTION_PROMPT.md`
  - entry docs:
    - `C:\tetie\AGENTS.md`
    - `C:\tetie\notecode\AGENTS.md`
    - `C:\tetie\WORKLOG.md`
- frozen reference boundary:
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`
  - reopen しない

## Rollback Rule

- simplification package の verdict が変わっても、frozen architecture package は先に動かさない
- 各 implementation phase は owner 1 file に閉じる
- rollback は phase owner の narrow diff 単位で行う
- helper を追加して surface を見かけ上分散しただけの diff は keep しない

## Do-Not-Retry Hypotheses

- `keep as-is` のまま wrapper / repair branch を積み増すこと
- `replace architecture` を初手で採ること
- frozen architecture package を reopen すること
- `newalgorithm_pipeline/pipeline.py` に article-type stabilizer を増やして complexity を救うこと
- `simple_note_pipeline/pipeline.py` に repair fallback を増やして complexity を救うこと
- prompt accretion / telemetry accretion で simplification を代替すること

## Expected Failure Modes

- wrapper surface reduction のつもりで別 helper 群を増やし、実際の decision density が減らない
- compatibility rebuild が main flow から隠れただけで owner ambiguity が残る
- repair surface reduction のつもりで accept 条件が複数箇所に残る
- runner trim 前に current success path regression を起こす

## Per-Phase Rollback Intention

### Phase 00 Package Freeze

- rollback:
  - package docs / AGENTS / WORKLOG の wording を package creation 前の状態へ戻す

### Phase 01 Wrapper Surface Reduction

- rollback:
  - `newalgorithm_pipeline/pipeline.py` の `_editor_report_to_dict()` / `_apply_compatibility_rebuild()` / `_apply_article_type_postprocess()` と main-flow replacement diff のみ戻す

### Phase 02 Repair Surface Reduction

- rollback:
  - `simple_note_pipeline/pipeline.py` の `_refresh_diagnostics_state()` / `_run_optional_repair()` と main-flow replacement diff のみ戻す

### Phase 03 Boundary Projection Trim

- rollback:
  - `current_mainline_runner.py` の `_normalize_execution_input_contract()` / `_run_current_mainline_pipeline()` / `_finalize_current_mainline_result()` と main-flow replacement diff のみ戻す
  - boundary artifact schema 自体は変えず、runner spine 整理 diff のみ rollback 対象とする
