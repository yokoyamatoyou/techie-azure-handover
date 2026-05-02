# separate window sentence final monotony management retriage after visible smoke note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の management retriage note である
- source-of-truth update ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- touched files
- owner / validation flow の短い要約
- latest visible smoke の exact read
- continuation cost / continuation value
- visible risk
- source-of-truth fit
- conclusion
- deepresearch 要否
- next prompt
- non-updates

## 読んだ参照ルールファイル

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_instruction_window_relocation_prompt_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_instruction_first_request_sentence_final_monotony_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_prompt_builder_constraint_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_actual_repair_prompt_triage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_followup_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_rollback_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_visible_smoke_after_rollback_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_management_retriage_after_visible_smoke_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_followup_20260417-195828\summary.json`
- `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`

## 実施範囲

- `sentence-final pattern monotony cap + single repair` line を docs / logs / code reference 読みだけで management retriage した
- current question を
  - この line を main candidate として続ける価値があるか
  - freeze で十分か
  - stop して別 line に資源を戻すべきか
  に限定した
- 新しい code edit / test edit / source-of-truth update には進んでいない

## Touched Files

- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_after_visible_smoke_note_2026-04-17.md`

## Owner / Validation Flow の短い要約

- 起点は deepresearch reflection 後の priority shift で、main candidate を `sentence-final pattern monotony cap + single repair` に寄せた
- その後の separate-window flow は
  - `pipeline.py` の local monotony acceptance lane
  - `quality_guard.py` の explanatory monotony promotion
  - `prompt_builder.py` の immutable heading/order contract
  - actual repair prompt triage
  - `prompt_builder.py` followup
  - live re-validation
  - rollback
  - rollback 後 visible smoke validation
  まで進んだ
- 代表 validation の共通 read は
  - `scope_acceptance_path = local_monotony_scope` が 1 回も出ていない
  - `repair_applied = false` が続いている
  - visible text 側では title / hashtags / heading flow drift と company intro の history-first drift が残った

## Latest Visible Smoke の Exact Read

- verdict:
  - `VISIBLE_STILL_BAD`
- V1 / V2:
  - followup 時点よりは改善寄り
  - ただし title / hashtags / heading flow drift は止まっていない
  - explanatory fallback smoke としては読めても、main candidate quality とは言いにくい
- V3:
  - followup 比では戻った
  - ただし `current-business-first` は visible に回復していない
  - first heading と本文運びは still history-first 寄り
- telemetry:
  - 3 case とも `patch_path_used = true`
  - 3 case とも `repair_applied = false`
  - 3 case とも `scope_acceptance_path` は未出力
  - 3 case とも `heading_sequence_changed = true`

## Continuation Cost / Continuation Value

- continuation cost:
  - すでに 3 owner にまたがる separate-window change を踏んでいる
  - live re-validation と followup、rollback、visible smoke まで回しており、phase-local retry としては十分にコストを使っている
  - rollback 後でも representative 3 case が main candidate quality に戻っていない
- continuation value:
  - 低い
  - まだ未試行の細い 1-file step として想定できるのは `pipeline.py` payload anchoring のような follow-up だけだが、それはもはや `sentence-final monotony` 単独 line ではなく `heading_reanchor / mixed-issue containment` 側へ論点がずれる
  - representative cases が `ending_bucket_monotony` 単独ではなく `heading_reanchor + ending_bucket_monotony` に寄っているため、line の narrowness が崩れている
- management read:
  - `owner-local narrow continuation value が残っている` とは言いにくい

## Visible Risk

- 高い
- この line を main candidate に戻すと
  - explanatory で title / hashtags / heading flow drift を許容しやすい
  - company intro で `current-business-first keep line` を壊す
  - `single repair` の名目で broad rewrite を繰り返す
  という実害がある
- current package が守っている
  - `grounded generic default`
  - `single-pass + optional single repair 1回`
  - blank company intro の current-business-first keep line
  に対する visible risk が大きい

## Source-Of-Truth Fit

- fit:
  - `retry-stop` 寄り
- 理由:
  - `naturalness_recovery_2026-04-07` current route は docs-first / rollback-first / grounded generic default を keep している
  - この line は separate evidence / phase-local narrow experiment として始まったが、現時点では mixed issue と visible drift の方が前景化している
  - これ以上続けると `sentence-final monotony` line ではなく、別 owner / 別 symptom / 別 package line の reopen になる

## Conclusion

- conclusion:
  - `STOP_AND_REDIRECT`
- why:
  - repeated visible failure pattern があり、rollback 後でも `main candidate` として回復していない
  - continuation value より continuation cost と visible risk のほうが明確に大きい
  - remaining work は narrow continuation ではなく、別 symptom を主語にした line へ移すべき内容になっている
- why not `KEEP_IN_QUEUE`:
  - 代表 3 case で positive keep evidence が 1 本もない
  - `scope_acceptance_path` も `repair_applied` も出ておらず、queue に残す根拠が弱い
- why not `FREEZE_LINE`:
  - 単に凍結するだけでは次 action が曖昧に残る
  - 現状は「今は追わない」ではなく、「この line から資源を外して別 line に戻す」が必要な段階である

## Deepresearch 要否

- deepresearch:
  - `不要`
- 理由:
  - いま不足しているのは theory ではなく local visible payoff
  - local docs / logs / code read だけで repeated visible failure と low continuation value を十分に説明できる
  - deepresearch を足しても、`rollback 後でも still bad` という management fact は変わらない

## Next Prompt

- next prompt type:
  - `management / planning prompt for a different line`
- exact read:
  - 次はこの line の continuation prompt ではない
  - 次は別 owner / 別 symptom / 別 package line に redirect するための prompt を作るべき
  - source-of-truth update prompt でも implementation prompt でもなく、まず redirect 先を narrow に決める management prompt が妥当

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
