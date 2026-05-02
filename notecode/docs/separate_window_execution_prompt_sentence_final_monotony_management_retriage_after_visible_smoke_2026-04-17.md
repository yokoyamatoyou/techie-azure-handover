# separate window execution prompt sentence final monotony management retriage after visible smoke 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_actual_repair_prompt_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_followup_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_rollback_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_visible_smoke_after_rollback_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_followup_20260417-195828\summary.json
- C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json
- C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py

今回の依頼種別:
- management retriage prompt
- source-of-truth update ではない
- implementation prompt ではない
- deepresearch prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line を docs / logs / code reference 読みだけで management retriage する
- 新しい code edit / test edit はしない
- 目的は、この line を main candidate として続行するか、freeze / stop / de-prioritize するかを narrow に判定すること
- AGENTS / WORKLOG / current package docs は更新しない
- current source-of-truth は更新しない

current keep-state:
- route default:
  - `grounded generic default`
- planning:
  - `opt-in only`
- structural baseline:
  - `single-pass + optional single repair 1回`
- `reference realization policy`:
  - separate evidence line のまま keep
- モジュール肥大化禁止
- prompt accretion 禁止

what happened so far:
- docs triage:
  - blocker was narrowed from detector/telemetry to repair line
- `pipeline.py`:
  - local monotony acceptance lane was added
- `quality_guard.py`:
  - explanatory short/adaptive monotony promotion was added
- `prompt_builder.py`:
  - monotony-only heading/order constraint was added
- followup prompt-builder changes:
  - freeze/locality/company-intro keep signal additions
  - later rolled back after live regression
- live / visible results:
  - even after multiple owner-local fixes and rollback, representative live generations still show visible drift
  - `scope_acceptance_path = local_monotony_scope` never appeared in the representative validation set
  - `repair_applied` stayed false in the representative validation set

latest visible smoke read to inherit:
- verdict:
  - `VISIBLE_STILL_BAD`
- exact read:
  - V1/V2:
    - followup 比では改善寄り
    - but `title / hashtags / heading` drift still remains
    - main candidate quality とは言いにくい
  - V3:
    - mixed-issue guard remains
    - but `current-business-first` does not visibly recover
    - history-first drift remains
  - telemetry:
    - `scope_acceptance_path` not emitted in all 3 cases
    - `repair_applied = false` in all 3 cases

core management question:
- この line は
  - まだ continuation value がある narrow candidate か
  - main candidate から外して freeze すべきか
  - stop して別 line に資源を戻すべきか
を判定する

what to decide:
1. `KEEP_IN_QUEUE`
   - main candidate ではないが、後順位で narrow continuation value はある
2. `FREEZE_LINE`
   - 現時点では mainline candidate から外し、これ以上は追わない
3. `STOP_AND_REDIRECT`
   - この line は stop し、別 owner / 別 symptom / 別 package line に戻す
4. `DEEPRESEARCH_NEEDED`
   - local docs / code read だけでは次判断が作れない

strong bias:
- deepresearch を安易に選ばない
- random variability ではなく repeated visible failure pattern があるなら、management judgment を優先する
- `tests pass but visible is bad` を軽視しない

things to evaluate explicitly:
- continuation cost:
  - ここまでの separate-window prompts / owner changes / reruns の回数
- continuation value:
  - まだ 1-file owner で narrow に効きそうな未試行手が残っているか
- visible risk:
  - main candidate にしたときの実害は大きいか
- rollback position:
  - rollback 後でも still bad なら、followup 実装の問題ではなく line 自体の value が低い可能性
- source-of-truth fit:
  - `naturalness_recovery_2026-04-07` current route に照らして、この line は phase-local narrow experiment のままか
  - それとも retry-stop に近いか

do not do:
- implementation proposalを長く書く
- 新しい code changes を提案前提で進める
- prompt accretion を再提案する
- route default / planning default / formatter policy を reopen する

preferred output shape:
- management note 1本
- conclusion is one of:
  - `KEEP_IN_QUEUE`
  - `FREEZE_LINE`
  - `STOP_AND_REDIRECT`
  - `DEEPRESEARCH_NEEDED`
- if not `DEEPRESEARCH_NEEDED`, state why deepresearch is not justified now

recommended output file:
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_after_visible_smoke_note_2026-04-17.md`

stopping conditions:
- management retriage を超えて code edit に進みたくなった
- source-of-truth update の話に逸れた
- conclusion を 2 つ以上にぼかしたくなった

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. ここまでの owner / validation の流れの短い要約
4. latest visible smoke の exact read
5. continuation cost と continuation value
6. visible risk の判定
7. `KEEP_IN_QUEUE / FREEZE_LINE / STOP_AND_REDIRECT / DEEPRESEARCH_NEEDED` の結論
8. deepresearch を入れるべきかどうか
9. 次が何の prompt か
10. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
