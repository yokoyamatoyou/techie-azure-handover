# separate window execution prompt pure output guard triage 2026-04-16

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\docs\ui_role_clarity_record_2026-04-08.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_test_algorithm_by_ui_direction_2026-04-16.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_ui_direction_test_algorithm_2026-04-16.md

今回の実施範囲:
- `pure output guard` failure 1件だけを narrow に切り分ける
- current experimental line の follow-up として実施する
- AGENTS / WORKLOG / current package docs は更新しない
- route default / formatter / input_contract / output_guard の owner へ広げない
- current source-of-truth は上書きしない

対象 failure:
- `pytest note\tests\test_current_mainline_regressions.py -k "clean_mock_llm_result_passes_pure_output_guard" -q`
- 現状:
  - `result["success"] = True`
  - `guard["blocked"] = True`
  - `reason_code = SYS_QUALITY_WARNINGS_UNRESOLVED`
  - soft warnings には
    - `fingerprint:particle_entropy_low`
    - `fingerprint:bigram_mono_low`
    - `fingerprint:mtld_low`
    - `fingerprint:vocab_repetition`
    - `fingerprint:nominalization_rate_high`
    - `fingerprint:sentence_ending_entropy_low`
    - `fingerprint:syntactic_complexity_low`
    が出ている

目的:
- 今回追加した `reference realization policy` が current mainline regression を悪化させたのか、
  それとも mock LLM / pure output guard の既存脆さなのかを narrow に判定する
- 判定不能のまま scope を広げない

first owner:
- C:\tetie\notecode\note\natural_blog_core.py

first hypothesis:
- `reference realization policy` の prompt hint が weakly-grounded section まで一律に出ることで、
  mock LLM output が単調・抽象化し、pure output guard の fingerprint warnings を超過させている

do not:
- formatter を触らない
- input_contract を触らない
- output_guard の threshold を変えない
- route default を変えない
- failure を owner 外と即断しない
- same hypothesis を unchanged で 3 回超 retry しない

実施手順:
1. failure を単独再現する
2. `natural_blog_core.py` の今回 diff だけを読み、どの prompt hint が mock LLM output を単調化しうるか説明する
3. owner-local test を先に足す
4. 修正する場合は `natural_blog_core.py` 1 file に閉じる
5. 修正は bounded にする
   - 例:
     - `reference realization hint` を source-backed section に限定
     - `trust_intro` の closing では hint を弱める
     - `proper_noun_repeat_cap` の文言を prompt から外し、plan field だけ keep する
     - `no_first_person` 以外の hint を long sentence 化させない短文へ縮める
6. 再度 failure を単独実行する
7. owner-local tests と shared checks を最小限回す

今回許可する touched files:
- C:\tetie\notecode\note\natural_blog_core.py
- C:\tetie\notecode\note\tests\test_natural_blog_core.py

今回の shared checks 最小セット:
- `pytest note\tests\test_natural_blog_core.py -q`
- `pytest note\tests\test_current_mainline_regressions.py -k "clean_mock_llm_result_passes_pure_output_guard" -q`
- `pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`

停止条件:
- same hypothesis で 3 回失敗
- owner 1 file で閉じなくなった
- output_guard threshold 調整なしでは通らないと分かった
- formatter / input_contract / pipeline route へ責任が逃げ始めた

最終報告で必ず示すこと:
1. failure が owner 内で再現したか
2. root cause 仮説
3. 触った files
4. 追加した test
5. failure 単独 rerun 結果
6. shared checks 結果
7. `industry_analysis_title_and_lead_do_not_echo_prompt` は今回対象外としてどう扱ったか
8. rollback 要否
9. current source-of-truth を更新していないこと
10. 次に live compare へ進めるか、ここで停止すべきか
```
