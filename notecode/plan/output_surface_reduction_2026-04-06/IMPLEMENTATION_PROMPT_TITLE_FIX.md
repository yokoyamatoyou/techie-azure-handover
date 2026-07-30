# output_surface_reduction_2026-04-06 IMPLEMENTATION PROMPT TITLE FIX

## use

- `generic title -> 解説` 症状の narrow fix を実装するときに使う
- このファイル内の `prompt` ブロックをそのまま開始プロンプトとして貼る
- 新 package は切らない
- `output_formatter.py` owner の explicit bug fix として扱う

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
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\IMPLEMENTATION_PROMPT_TITLE_FIX.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md

今回の実施範囲:
- completed / frozen package は reopen しない
- current success path を壊さない
- package creation 判断はしない
- `generic title -> 解説` の narrow fix だけを扱う
- owner scope は `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py` に閉じる
- test 追加は必要なら `C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py` に限定する
- source grounding / ending monotony / legal watch / paragraph variation は今回扱わない

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

confirmed evidence:
- latest artifact title is `解説`
- `explanatory_article` では `_prefer_generated_title()` は使われず、`_compact_title()` に流れる
- topic / prompt_raw / topic_statement が空だと `_compact_title()` が `_ARTICLE_LABELS["explanatory_article"]` を返して generic title になる
- body / headings / must_cover は存在していても、empty topic short-circuit が先に走る

実装 objective:
- `explanatory_article` で topic が空でも、body / headings / must_cover から generic でない title seed を組めるようにする
- empty topic の場合でも `解説` への即 fallback を避ける
- ただし announcement / branding / case_study / comparative / daily_story / industry_analysis の既存 title behavior は壊さない

期待する fix の方向:
1. `_compact_title()` の empty topic fallback を narrow に見直す
2. explanatory_article に限り、topic が空でも
   - body heading
   - must_cover
   - contract
   のいずれかから non-generic title seed を取る
3. signal が本当に何もない場合だけ最後に `解説` fallback を許可する

do-not:
- completed package を reopen しない
- frozen package を reopen しない
- planner / generator core を触らない
- pipeline.py / simple_note_pipeline.py / current_mainline_runner.py を変更しない
- source grounding residual と混ぜない
- ending monotony residual と混ぜない
- helper 増殖を simplification と見なさない

必要なら追加してよい test:
- explanatory_article + empty topic + heading/bodyあり で generic title にならない test
- explanatory_article + empty topic + must_coverあり で generic title にならない test
- signal が何もない時だけ `解説` fallback を許可する test
- 既存 title behavior を壊していないことの focused test

実行してよい tests:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "title or st08b2 or explanatory" -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q

開始直後の最初の判断:
1. current evidence chain を再確認する
2. fix を `output_formatter.py` owner だけに閉じられるか確認する
3. focused test を先に見て、足りない test があれば narrow に追加する
4. code change -> focused test -> shared checks の順で進める

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- evidence chain
- 実施した変更
- 実行した tests
- rollback の有無
- AGENTS / WORKLOG 更新の有無
```
