# output_surface_reduction_2026-04-06 ROLLBACK

## Baseline

- restore target:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- next owner target:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- current package boundary:
  - package docs:
    - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md`
    - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\TASK.md`
    - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md`
    - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\ROLLBACK.md`
    - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\EXECUTION_PROMPT.md`
  - entry docs:
    - `C:\tetie\AGENTS.md`
    - `C:\tetie\notecode\AGENTS.md`
    - `C:\tetie\WORKLOG.md`
- reference boundary:
  - completed:
    - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
  - frozen:
    - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`
  - reopen しない

## Rollback Rule

- output surface package の verdict が変わっても、completed / frozen reference package は先に動かさない
- 各 implementation phase は owner 1 file に閉じる
- rollback は phase owner の narrow diff 単位で行う
- helper を増やして surface を見かけ上分散しただけの diff は keep しない

## Do-Not-Retry Hypotheses

- completed reference package を reopen すること
- frozen architecture package を reopen すること
- planner / generator core を初手で触ること
- formatter residual を article-type rule 増殖で救うこと
- prompt accretion / module accretion で final surface を隠すこと
- pipeline owner へ final-stage residual を戻して薄くなったように見せること

## Expected Failure Modes

- formatter surface reduction のつもりで title / lead / scaffold helper 群だけが増え、decision density が減らない
- body normalize と final projection の境界が曖昧なまま残る
- formatter 側の hidden repair assumption が editor guard と重なったまま残る
- planner / generator core を reopen しないと前に進めない状態になる

## Per-Phase Rollback Intention

### Phase 00 Package Freeze

- rollback:
  - package docs / AGENTS / WORKLOG の wording を package creation 前の状態へ戻す

### Phase 01 Output Formatter Surface Reduction

- rollback:
  - `output_formatter.py` の `_normalize_announcement_output_body()` / `_drop_known_transition_fragments()` / `_apply_article_type_output_body_normalizers()` / `_normalize_output_lines()` / `_resolve_output_title()` / `_resolve_output_lead()` / `_resolve_output_scaffold()` / `_build_output_full_body()` と main-flow replacement diff のみ戻す

### Phase 02 Editor Guard Boundary Trim

- rollback:
  - `editor_guard.py` の acceptance / budget / warning surface 整理 diff のみ戻す
