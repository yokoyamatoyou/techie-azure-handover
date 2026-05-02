# separate window execution prompt sentence final monotony actual repair prompt triage 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_prompt_builder_constraint_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_constraint_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_prompt_builder_constraint_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_constraint_20260417-183317\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json
- C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の依頼種別:
- follow-up triage prompt
- source-of-truth update ではない
- implementation prompt ではない
- deepresearch prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line について、`prompt_builder.py` constraint 後の live failure を docs / artifacts / code reference 読みと必要最小限の non-edit probe で切り分ける
- 焦点は `actual repair prompt` に immutable heading/order contract がどう出ていたかの確認だけに閉じる
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない
- current source-of-truth は更新しない

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

current exact blocker:
- A1 はついに
  - `repair_required = true`
  - `patch_path_used = true`
  まで進んだ
- それでも
  - `repair_applied = false`
  - `scope_acceptance_path = null`
  - `scope_rejection_reason = flagged_scope_drift`
  - `acceptance_rejection_reason = ending_monotony_not_improved`
  で止まった
- B は mixed issue で `local_monotony_scope` の誤適用は出ていないが、visible は history-first drift が強い
- したがって次の問いは
  - `prompt_builder.py` の hard constraint が actual repair prompt に本当に入っていたのか
  - 入っていたなら、どの wording が heading rename / merge / closing replacement を防げなかったのか
  - 入っていなかったなら、どの prompt assembly boundary で落ちたのか
  の 3 点である

first owner candidate:
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`

second owner candidate only if unavoidable:
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

do not do in this prompt:
- production code edit
- test edit
- acceptance threshold 緩和
- quality guard threshold 調整
- route / planning / formatter policy の議論

primary questions to answer:
1. A1 actual repair prompt には monotony-only contract がどう埋め込まれていたか
2. その prompt は明示的に
   - heading rename/add/drop/reorder 禁止
   - closing section replacement 禁止
   - flagged span 近傍だけを書き換える
   を表現できていたか
3. B actual repair prompt では `current-business-first keep line` が repair prompt 側にも維持されていたか
4. failure の主体は
   - contract emission missing
   - contract wording too weak
   - patch target / flagged span wording mismatch
   - model obedience variability
   のどれに最も近いか

allowed work:
- docs / code reference 読み
- existing logs / artifacts の精査
- 必要最小限の non-edit probe
  - 例:
    - repair prompt string を再構成して保存するだけの読み取り
    - 既存 helper / test fixture / REPL で prompt text を出力するだけの確認
- generated logs only
- triage note 1本

allowed touched files:
- generated logs only
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_actual_repair_prompt_triage_note_2026-04-17.md`

do not touch:
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\tests\*.py`
- AGENTS / WORKLOG / current planning package docs

minimum work plan:
1. read the prompt-builder constraint diff note and the latest live revalidation note
2. inspect `prompt_builder.py` around the monotony-only repair prompt construction
3. identify how the repair prompt text is actually assembled for A1 and B
4. recover the actual repair prompt text if possible without code edits
5. compare:
   - intended contract lines
   - actual emitted prompt lines
   - visible repair output drift
6. conclude whether next step should stay on `prompt_builder.py` owner or move to `pipeline.py` prompt assembly / payload boundary

strong preference:
- A1 and B の actual repair prompt text を両方確認する
- ただし recovery が難しい場合は A1 を最優先にする

if you can recover actual repair prompt text:
- 必ず次を示すこと
  - heading contract lines の実文
  - closing replacement 禁止 line の実文
  - local patch scope line の実文
  - company intro keep line の有無
  - それらが system/user prompt のどちらに寄っていたかの推定

if you cannot recover actual repair prompt text:
- 推測で埋めない
- 代わりに
  - どの artifact には無かったか
  - どの helper / assembly path までは確認できたか
  - prompt capture には何が追加で必要か
  を narrow に書く

judge options:
- `PROMPT_EMISSION_MISSING`
  - intended constraint が actual repair prompt に載っていない
- `PROMPT_WORDING_TOO_WEAK`
  - constraint は載っているが heading/locality を守らせる wording が弱い
- `PATCH_SCOPE_MISMATCH`
  - flagged span / target section wording が repair target と噛み合っていない
- `MODEL_VARIABILITY_STILL_PRIMARY`
  - prompt text は十分だが live variability が主因
- `NEEDS_IMPLEMENTATION`
  - triage 結果として次は implementation prompt が必要

good outcome:
- next owner が 1 file に閉じて再特定される
- `prompt_builder.py` 継続か `pipeline.py` へ移すかを narrow に決められる

bad outcome:
- acceptance / quality guard / route policy まで論点が広がる
- prompt を見ないまま impression で owner を決める

stopping conditions:
- actual repair prompt recovery に code edit が必要になった
- 2 file 以上の owner を同時 reopen しないと説明できない
- triage 中に source-of-truth update の話へ逸れた

recommended output file:
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_actual_repair_prompt_triage_note_2026-04-17.md`

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. actual repair prompt を回収できたか
4. A1 actual repair prompt の要点
5. B actual repair prompt の要点
6. immutable heading/order contract が actual prompt に出ていたか
7. closing section replacement 禁止 line が actual prompt に出ていたか
8. `current-business-first keep line` が B の prompt に残っていたか
9. current blocker の owner 判定
10. `PROMPT_EMISSION_MISSING / PROMPT_WORDING_TOO_WEAK / PATCH_SCOPE_MISMATCH / MODEL_VARIABILITY_STILL_PRIMARY / NEEDS_IMPLEMENTATION` のどれか
11. 次が implementation prompt か、さらに triage prompt か
12. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
