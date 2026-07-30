# output_surface_reduction_2026-04-06 SEPARATE WINDOW PROMPT

## use

- 次の作業を別ウインドウで始めるときは、このファイル内の `prompt` ブロックをそのまま使う
- `output_surface_reduction_2026-04-06` package は completed reference として扱い、reopen しない
- `orchestration_surface_reduction_2026-04-06` package は completed reference として扱い、reopen しない
- `architecture_target_refactor_2026-04-06` package は frozen reference として扱い、reopen しない
- 次ウインドウの primary task は「次 package が本当に必要かの判断」に限定する

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\TASK.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\ROLLBACK.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\SEPARATE_WINDOW_PROMPT.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md

今回の実施範囲:
- `output_surface_reduction_2026-04-06` package は completed reference として扱う
- `orchestration_surface_reduction_2026-04-06` package は completed reference として扱う
- `architecture_target_refactor_2026-04-06` package は frozen reference として扱う
- repo decision は `keep core, refactor boundaries`
- current success path を壊さない
- completed / frozen package を reopen しない
- 次 package が本当に必要かを判断する
- 必要なら narrow planning package の新規作成だけを行う
- 不要なら変更を入れずに停止して user report する

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
4. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\TASK.md
5. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
6. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\ROLLBACK.md
7. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\EXECUTION_PROMPT.md
8. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\SEPARATE_WINDOW_PROMPT.md
9. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
10. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
11. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
12. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
13. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
14. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md
15. C:\tetie\notecode\ALGORITHM.md
16. C:\tetie\WORKLOG.md

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
4. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\TASK.md
5. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
6. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\ROLLBACK.md
7. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\SEPARATE_WINDOW_PROMPT.md
8. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
9. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
10. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
11. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
12. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
13. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md
14. C:\tetie\notecode\ALGORITHM.md
15. C:\tetie\WORKLOG.md

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

completed reference として keep する package:
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\

frozen reference として keep する package:
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\

completed owner scope:
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py

next startup primary question:
- 次 package は本当に必要か
- 必要なら package objective を 1 行で何に固定するか
- 最初の narrow phase をどの owner file に置くか
- 何を non-goal に固定しないと再肥大化するか

do-not:
- completed package を reopen しない
- frozen architecture package を reopen しない
- planner / generator core を初手で触らない
- prompt accretion をしない
- module accretion をしない
- helper 増殖を simplification と見なさない
- current success path を壊さない

開始直後の最初の判断:
1. `README.md` / `TASK.md` / `PROGRESS.md` / `ROLLBACK.md` の completed boundary を確認する
2. この completed package に未完了 phase がないことを確認する
3. current success path の complexity residual が新 package を要するか判断する
4. planner / generator core を reopen しないと進まない場合は、それを package objective にせず停止して user report する

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- completed reference として扱った package
- frozen reference として扱った package
- completed owner scope
- 次 package を切るかどうかの yes/no
- 切るなら package 名案 / objective / 最初の narrow phase
- 実施した変更
- 実行した tests
- rollback の有無
- AGENTS / WORKLOG 更新の有無
```
