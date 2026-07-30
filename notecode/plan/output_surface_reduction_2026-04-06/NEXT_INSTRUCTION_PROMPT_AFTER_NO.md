# output_surface_reduction_2026-04-06 NEXT INSTRUCTION PROMPT AFTER NO

## use

- 「次 package は不要」という判断の次回再開で使う
- このファイル内の `prompt` ブロックをそのまま開始プロンプトとして貼る
- completed package を reopen しない
- fresh regression / fresh artifact evidence がない限り、新 package を切らない

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\TASK.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\ROLLBACK.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\SEPARATE_WINDOW_PROMPT.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\NEXT_INSTRUCTION_PROMPT_AFTER_NO.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md

今回の実施範囲:
- `output_surface_reduction_2026-04-06` package は completed reference として扱う
- `orchestration_surface_reduction_2026-04-06` package は completed reference として扱う
- `architecture_target_refactor_2026-04-06` package は frozen reference として扱う
- current success path を壊さない
- completed / frozen package を reopen しない
- 新 package を切るかどうかは、fresh regression / fresh artifact evidence がある場合にだけ再判定する
- fresh evidence がなければ変更を入れずに停止して user report する

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
4. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\TASK.md
5. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
6. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\ROLLBACK.md
7. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\SEPARATE_WINDOW_PROMPT.md
8. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\NEXT_INSTRUCTION_PROMPT_AFTER_NO.md
9. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
10. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
11. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
12. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
13. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
14. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md
15. C:\tetie\notecode\ALGORITHM.md
16. C:\tetie\WORKLOG.md

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

current standing decision:
- 次 package を切る判断は `no`
- 根拠:
  - current package は completed
  - `Phase 02` は not needed で閉じている
  - fresh regression / fresh artifact evidence がない
  - 今 package を切ると completed owner scope の reopen か planner / generator core 再着手に寄りやすい

次に着手してよい task:
1. fresh evidence check
   - 新しい regression
   - 新しい live artifact
   - 新しい quality break
   のいずれかが明示された場合だけ確認する
2. explicit artifact review
   - user が artifact path / run result / failure symptom を明示した場合だけ扱う
3. explicit bug fix
   - user が owner file と failure を明示した場合だけ narrow に扱う

do-not:
- completed package を reopen しない
- frozen architecture package を reopen しない
- planner / generator core を初手で触らない
- prompt accretion をしない
- module accretion をしない
- helper 増殖を simplification と見なさない
- fresh evidence なしで新 package を切らない
- current success path を壊さない

開始直後の最初の判断:
1. completed boundary を確認する
2. fresh regression / fresh artifact evidence があるか確認する
3. ない場合は変更なしで停止し user report する
4. ある場合だけ owner scope を 1 file または docs-only に閉じられるか確認する
5. completed owner scope の reopen か planner / generator core 再着手が必要なら停止して user report する

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- completed reference として扱った package
- frozen reference として扱った package
- fresh evidence の有無
- 次 package を切るかどうかの yes/no
- 実施した変更
- 実行した tests
- rollback の有無
- AGENTS / WORKLOG 更新の有無
```
