# separate window execution prompt sentence final monotony target boundary triage 2026-04-17

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_instruction_window_relocation_prompt_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_instruction_first_request_sentence_final_monotony_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_quality_guard_triage_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_quality_guard_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_quality_guard_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_note_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_quality_guard_20260417-170631\summary.json

今回の依頼種別:
- follow-up triage prompt
- source-of-truth update ではない
- deepresearch prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の validation target boundary を切り分ける
- 目的は
  - A: live validation target を `length_mode = short` explanatory case に差し替える
  - B: current production-like `adaptive` explanatory case まで trigger 対象を広げる
  のどちらを main line にするか判断すること
- 初手は docs / artifact 読みと判断に閉じる
- production code は初手で変更しない
- AGENTS / WORKLOG / current package docs は更新しない

current keep-state:
- route default:
  - `grounded generic default`
- planning:
  - `opt-in only`
- structural baseline:
  - `single-pass + optional single repair 1回`
- blank company intro keep line:
  - `prompt_builder.py` の `current-business-first keep line`
- `reference realization policy`:
  - separate evidence line のまま keep
  - 今回の main line にはしない

current boundary to inherit:
- `pipeline.py` acceptance lane は focused で成立済み
- `quality_guard.py` の explanatory monotony promotion は narrow に追加済み
- ただし live re-validation では A1/A2 の current rerun contract が
  - `length_mode = adaptive`
  のままで、short-only promotion branch に乗っていない
- live re-validation note verdict は `NEEDS_MORE_WORK`
- immediate rollback reason はない
- immediate keep reason もまだない

primary question:
- main candidate として次に詰めるべきなのは
  - `short explanatory live case` を新たに target にして line を証明すること
  か
  - `adaptive explanatory` も monotony trigger 対象に含めるよう owner を reopen すること
  か

目的:
- `short-only promotion` を validation target mismatch の問題として扱うか
- それとも current production-like target への未接続として扱うか
- その判断を docs-first で出す
- 次の実装 owner を開くなら 1 file に閉じる

初手でやること:
1. live re-validation note と summary を読む
2. A1 / A2 の rerun contract が `adaptive` だった理由を artifact から確認する
3. current package objective と keep-state に照らして、
   次の validation target は short case に寄せるべきか、adaptive まで広げるべきかを判断する
4. docs note を 1 本作り、次を
   - `SHORT_TARGET_FIRST`
   - `ADAPTIVE_SCOPE_REOPEN`
   - `NEEDS_MANAGEMENT_RETRIAGE`
   のいずれかで結論づける

judgment guidance:
- `SHORT_TARGET_FIRST` を選ぶ条件:
  - current narrow hypothesis は short explanatory monotony-only に閉じている
  - adaptive まで広げると scope が広がる
  - line の有効性をまず short live case で証明するほうが rollback-first
- `ADAPTIVE_SCOPE_REOPEN` を選ぶ条件:
  - actual production-like explanatory target の大半が adaptive で、short case だけの勝利では main candidate として弱い
  - adaptive を外したままだと live validation が意味を持たない
  - owner を 1 file に閉じて narrow に reopen できる
- `NEEDS_MANAGEMENT_RETRIAGE` を選ぶ条件:
  - short と adaptive のどちらを main target にするか docs / artifacts だけでは決めきれない
  - line 自体の objective が再定義を要する

allowed touched files:
- docs only
- recommended:
  - C:\tetie\notecode\docs\separate_window_sentence_final_monotony_target_boundary_note_2026-04-17.md

do not touch:
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\newalgorithm_pipeline\*.py
- C:\tetie\notecode\note\natural_blog_core.py
- C:\tetie\notecode\note\current_mainline_runner.py
- tests
- AGENTS
- WORKLOG
- current planning package docs

do not:
- deepresearch を始めない
- global threshold を動かし始めない
- adaptive reopen を即実装しない
- short-only line を source-of-truth に昇格しない
- route default / planning default を触らない
- `reference realization policy` を main line に戻さない

recommended output structure:
- current read
- why A1/A2 missed the short-only promotion
- option A: short target first
- option B: adaptive scope reopen
- decision
- next prompt type

stopping conditions:
- docs / artifact だけでは target boundary を判断できない
- target boundary の判断前に code edit をしたくなった
- sentence-final line から別論点へ逸れた

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. touched files
4. A1/A2 が short-only promotion に乗らなかった理由
5. `SHORT_TARGET_FIRST` / `ADAPTIVE_SCOPE_REOPEN` / `NEEDS_MANAGEMENT_RETRIAGE` の結論
6. なぜその結論なのか
7. 次に必要なのが
   - short live revalidation prompt
   - adaptive quality_guard follow-up prompt
   - management retriage prompt
   のどれか
8. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
