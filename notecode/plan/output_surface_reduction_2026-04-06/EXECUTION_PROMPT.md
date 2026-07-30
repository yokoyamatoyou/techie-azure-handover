# output_surface_reduction_2026-04-06 EXECUTION PROMPT

## next startup use

- 次回起動時は、このファイル内の `prompt` ブロックをそのまま使う
- `output_surface_reduction_2026-04-06` package は completed reference として扱い、reopen しない
- current planning source-of-truth はこの completed package の docs を keep する
- `orchestration_surface_reduction_2026-04-06` package は completed reference として扱い、reopen しない
- `architecture_target_refactor_2026-04-06` package は frozen reference として扱い、reopen しない

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
- planning theme / implementation theme は `keep core, reduce output surface`
- current success path を壊さない
- `1 phase = 1 narrow hypothesis = 1 owner scope` を崩さない

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
4. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\TASK.md
5. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
6. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\ROLLBACK.md
7. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\EXECUTION_PROMPT.md
8. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
9. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
10. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
11. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
12. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
13. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md
14. C:\tetie\notecode\ALGORITHM.md
15. C:\tetie\WORKLOG.md

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
4. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\TASK.md
5. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
6. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\ROLLBACK.md
7. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\EXECUTION_PROMPT.md
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
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\

frozen reference として keep する package:
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\

current package status:
- package status:
  - completed
- current phase:
  - complete
- status:
  - completed

package completion note:
- completed owner scope:
  - C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
- next action:
  - この package を reopen せず、追加 simplification が必要なら新 package を作成する

next startup primary question:
- 次 package は本当に必要か
- 必要なら package objective を 1 行で何に固定するか
- 最初の narrow phase をどの owner file に置くか
- completed reference package を reopen しないと進まない場合は停止して user report するか

do-not:
- この completed package を reopen しない
- completed reference package を reopen しない
- frozen architecture package を reopen しない
- planner / generator core を初手で触らない
- prompt accretion をしない
- module accretion をしない
- helper 増殖を simplification と見なさない
- current success path を壊さない

shared check commands:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st08c or st07a_06 or st07a_07" -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q

開始直後の最初の判断:
1. `README.md` / `TASK.md` / `PROGRESS.md` / `ROLLBACK.md` の output-surface boundary を確認する
2. この package に未完了 phase がないことを確認する
3. completed / frozen reference package を reopen しないことを再確認する
4. 追加 residual がある場合でも package objective を広げず、新 package 作成要否を先に判断する

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- completed reference / frozen reference として扱った package
- 次 phase の narrow task
- 実施した変更
- 実行した tests
- rollback の有無
- AGENTS / WORKLOG 更新の有無
```
