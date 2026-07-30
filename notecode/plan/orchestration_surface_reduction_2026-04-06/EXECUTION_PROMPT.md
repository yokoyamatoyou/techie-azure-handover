# orchestration_surface_reduction_2026-04-06 EXECUTION PROMPT

## next startup use

- 次回起動時は、このファイル内の `prompt` ブロックをそのまま使う
- `orchestration_surface_reduction_2026-04-06` package は completed reference として扱い、reopen しない
- 次回の primary task は「新 package を切る必要があるかの判断」と「必要なら narrow planning package を新規作成すること」に限定する

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\TASK.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\ROLLBACK.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md

今回の実施範囲:
- `orchestration_surface_reduction_2026-04-06` package を current planning package として扱う
- frozen reference である `architecture_target_refactor_2026-04-06` package は reopen しない
- repo decision は `keep core, refactor boundaries`
- planning theme / implementation theme は `keep core, reduce orchestration surface`
- current success path を壊さない
- `1 phase = 1 narrow hypothesis = 1 owner scope` を崩さない

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
4. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\TASK.md
5. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
6. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\ROLLBACK.md
7. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\EXECUTION_PROMPT.md
8. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
9. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
10. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
11. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md
12. C:\tetie\notecode\ALGORITHM.md
13. C:\tetie\WORKLOG.md

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
4. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\TASK.md
5. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
6. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\ROLLBACK.md
7. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\EXECUTION_PROMPT.md
8. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
9. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
10. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
11. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md
12. C:\tetie\notecode\ALGORITHM.md
13. C:\tetie\WORKLOG.md

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

frozen reference として keep する判断:
- adopted:
  - hybrid target architecture
  - keep core, refactor boundaries
- keep:
  - DiscourseSection を中心にした section contract
  - route-aware source grounding の分類と節配賦
  - section-first writer の逐次生成器
  - diagnostics / guard / quality check の validator 面
- reject:
  - keep as-is
  - replace architecture

current package status:
- package status:
  - completed
- current phase:
  - complete
- status:
  - completed

package completion note:
- completed owner scopes:
  - C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - C:\tetie\notecode\note\current_mainline_runner.py
- completion summary:
  - wrapper / repair / boundary projection の orchestration surface reduction は完了
- next action:
  - この package を reopen せず、追加 simplification が必要なら新 package を作成する

next startup primary question:
- 次 package は本当に必要か
- 必要なら package objective を 1 行で何に固定するか
- 最初の narrow phase をどの owner file に置くか
- 何を non-goal に固定しないと再肥大化するか

do-not:
- frozen architecture package を reopen しない
- planner / generator core を初手で触らない
- prompt accretion をしない
- module accretion をしない
- helper 増殖を simplification と見なさない
- current success path を壊さない

shared check commands:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q

開始直後の最初の判断:
1. `README.md` / `TASK.md` / `PROGRESS.md` / `ROLLBACK.md` の simplification boundary を確認する
2. この package に未完了 phase がないことを確認する
3. current success path の complexity residual が新 package を要するか判断する
4. planner / generator core を reopen しないと進まない場合は、それを package objective にせず停止して user report する

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- frozen reference として扱った package
- completed owner scope
- 次 package を切るかどうかの yes/no
- 切るなら package 名案 / objective / 最初の narrow phase
- 実施した変更
- 実行した tests
- rollback の有無
- AGENTS / WORKLOG 更新の有無
```
