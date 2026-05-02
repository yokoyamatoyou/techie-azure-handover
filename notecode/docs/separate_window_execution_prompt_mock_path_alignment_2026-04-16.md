# separate window execution prompt mock path alignment 2026-04-16

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_ui_direction_test_algorithm_2026-04-16.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_pure_output_guard_triage_2026-04-16.md

今回の実施範囲:
- `test_current_mainline_clean_mock_llm_result_passes_pure_output_guard` failure の mock path alignment だけを narrow に扱う
- current mainline production path を stale mock に合わせて壊さない
- AGENTS / WORKLOG / current package docs は更新しない
- current source-of-truth は上書きしない

対象 failure:
- `pytest note\tests\test_current_mainline_regressions.py -k "clean_mock_llm_result_passes_pure_output_guard" -q`
- 現在の判定:
  - `natural_blog_core.py` owner では閉じなかった
  - `reference realization policy` を無効化しても failure は不変
  - failure run は `simple_note_pipeline` prompt path を通っており、mock LLM が現行 prompt surface を十分に読めていない疑いが強い

目的:
- `_CleanCurrentMainlineLLM` と現行 prompt format のずれを narrow に解消する
- production code を test double に合わせて歪めず、test double または test expectation を現行仕様に沿って更新する

first owner:
- C:\tetie\notecode\note\tests\test_current_mainline_regressions.py

optional second owner:
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py

重要方針:
- 初手では production owner を触らない
- `_CleanCurrentMainlineLLM` の読取ロジックが stale なら、まず test double を直す
- test expectation 自体が stale なら、その妥当性を先に説明してから更新する
- output_guard threshold を緩めて通すことは禁止
- formatter / input_contract / route default へ責任を広げない

first hypothesis:
- `_CleanCurrentMainlineLLM` は current prompt の `section goal / must-cover / source grounding / subject rule` の構造を読めておらず、単調で低多様性な本文を返してしまう

実施手順:
1. failure を単独再現する
2. `_CleanCurrentMainlineLLM` が prompt のどの label / line を前提にしているかを確認する
3. actual current prompt と期待する clean output の差を説明する
4. owner-local test を先に追加または更新する
5. 修正する場合は first owner に閉じる
   - `_extract_line()` の対象追加
   - must-cover / source fact / heading / subject hint の読み取り改善
   - 同型文や抽象文を返しすぎない deterministic output へ調整
6. 単独 failure を再実行する
7. 必要最小限の shared checks を回す

今回許可する touched files:
- C:\tetie\notecode\note\tests\test_current_mainline_regressions.py

second owner に進んでよい条件:
- `_CleanCurrentMainlineLLM` を current prompt に合わせても failure が残る
- そのとき初めて `prompt_builder.py` 側の mock-unfriendly surface を narrow に検討してよい

second owner でやってよいこと:
- current prompt の semantic label を 1つだけ stable にする
- mock path でも拾える短い structural marker を bounded に追加する

second owner でやってはいけないこと:
- prompt 全体の長文化
- production quality を落として test を通すこと
- route / formatter / input_contract へ責任を逃がすこと

今回の shared checks 最小セット:
- `pytest note\tests\test_current_mainline_regressions.py -k "clean_mock_llm_result_passes_pure_output_guard" -q`
- `pytest note\tests\test_current_mainline_regressions.py -q`
- `pytest note\tests\test_current_mainline_runner.py -q`
- second owner に進んだ場合のみ
  - `pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`

停止条件:
- same hypothesis で 3 回失敗
- output_guard threshold 調整なしでは通らない
- production prompt を stale test に寄せるしかなくなった
- touched files が 2 owner を超えそうになった

最終報告で必ず示すこと:
1. mock path mismatch の具体点
2. first owner だけで閉じたか
3. 触った files
4. 追加 / 更新した test
5. 単独 failure rerun 結果
6. shared checks 結果
7. second owner に進んだかどうか
8. production path を壊していないこと
9. rollback 要否
10. current source-of-truth を更新していないこと
```
