# output_surface_reduction_2026-04-06 NEXT INSTRUCTION PROMPT TITLE OWNER ISOLATION

## use

- artifact review の結果、visible residual はあるが owner 1 file に閉じなかった次回再開で使う
- このファイル内の `prompt` ブロックをそのまま開始プロンプトとして貼る
- 今回は `generic title` だけを対象に owner isolation する
- source grounding の薄さ / ending monotony / legal watch は non-goal に固定する

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
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\SEPARATE_WINDOW_PROMPT.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\NEXT_INSTRUCTION_PROMPT_AFTER_NO.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\NEXT_INSTRUCTION_PROMPT_TITLE_OWNER_ISOLATION.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md

今回の実施範囲:
- completed / frozen package は reopen しない
- current success path を壊さない
- code 変更はしない
- package 作成判断もまだしない
- `generic title` symptom だけを owner isolation する
- source grounding の薄さ / ending monotony / legal watch / paragraph variation は今回扱わない
- 最終目的は `title residual が output_formatter.py owner に閉じるか yes/no` を出すこと

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

completed reference:
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\

frozen reference:
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\

completed owner scope:
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py

review target:
- title が `解説` のような generic title になった理由を tracing する

読んでよい artifact:
- C:\tetie\notecode\logs\latest_generation_output.txt
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\latest_generation_quality_report.json
- C:\tetie\notecode\logs\generation_audit_log.jsonl

読んでよい code:
- C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py

確認したいこと:
1. artifact の title は formatter 入力前から generic なのか、formatter fallback で generic 化したのか
2. `format_output()` の
   - `_prefer_generated_title()`
   - `_compact_title()`
   - article_type fallback
   のどこで `解説` に落ちうるか
3. body/headings/topic のどれが generic title を誘発したのか
4. この symptom を `output_formatter.py` owner 1 file に閉じて扱えるか

do-not:
- completed package を reopen しない
- frozen package を reopen しない
- planner / generator core を触らない
- source grounding residual と title residual を同じ task に混ぜない
- ending monotony residual と title residual を同じ task に混ぜない
- code 変更しない
- tests を走らせない

開始直後の最初の判断:
1. latest artifact に generic title が実在することを確認する
2. formatter 呼び出し前後の情報で、title residual が downstream symptom か確認する
3. `output_formatter.py` owner 1 file に閉じるか yes/no を判断する
4. 閉じないなら no で停止する
5. 閉じるなら、その根拠だけを user report する

最終報告で必ず示すこと:
- 読んだ正本ファイル
- 読んだ artifact
- generic title symptom の実在有無
- title residual が output_formatter.py owner に閉じるか yes/no
- yes の場合:
  - evidence chain
  - narrow owner file
  - 次 package が必要か yes/no
- no の場合:
  - 何が混ざっていて 1 file に閉じなかったか
- 実施した変更
- 実行した tests
- rollback の有無
- AGENTS / WORKLOG 更新の有無
```
