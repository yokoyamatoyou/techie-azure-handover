# separate window execution prompt sentence final monotony live revalidation after prompt builder followup 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_actual_repair_prompt_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_constraint_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_prompt_builder_constraint_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_followup_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_constraint_20260417-183317\summary.json
- C:\tetie\notecode\logs\sentence_final_monotony_actual_repair_prompt_triage_20260417-185120\summary.json
- C:\tetie\notecode\logs\sentence_final_monotony_actual_repair_prompt_triage_20260417-185120\case_a1_latest_adaptive_explanatory_reconstructed_prompt.txt
- C:\tetie\notecode\logs\sentence_final_monotony_actual_repair_prompt_triage_20260417-185120\case_b_company_intro_guard_reconstructed_prompt.txt
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py

今回の依頼種別:
- live re-validation prompt
- source-of-truth update ではない
- deepresearch prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の live re-validation を再実施する
- owner diff は次の 3 file owner に閉じた状態として扱う
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- 今回の新規 diff は実質 `prompt_builder.py` followup に限定される
- production code / tests は追加編集しない
- AGENTS / WORKLOG / current package docs は更新しない
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

implemented state to validate:
- `pipeline.py`
  - monotony-only patch で `local_monotony_scope` acceptance lane を許可
  - `scope_acceptance_path` telemetry を追加
  - `repair_entry` telemetry を追加
- `quality_guard.py`
  - explanatory short monotony-only promotion は keep
  - explanatory adaptive monotony-only promotion は keep
  - adaptive reopen conditions は維持
- `prompt_builder.py`
  - monotony-only repair prompt に immutable heading/order contract は既に追加済み
  - 追加 followup diff:
    - `TITLE` freeze line
    - `LEAD` freeze line
    - `HASHTAGS` freeze line
    - `local_run_plus_two` の sentence-cluster anchor wording
    - `TITLE / LEAD / HASHTAGS / 他見出しへ移動しない` line
    - company-intro repair prompt で `company_intro_focus=自社の事業内容を紹介する` が filter 後も残るように修正

core validation question:
- prompt_builder followup 後に、A1 で finally
  - `repair_entry.repair_required = true`
  - `repair_call.patch_path_used = true`
  - `repair_applied = true`
  - `scope_acceptance_path = local_monotony_scope`
  へ届くか
- B で `current-business-first keep line` が visible に維持されるか

目的:
- A1 / A2 / B の 3 case を current success path で rerun し、followup diff の live effect を確認する
- A1 では heading drift だけでなく title / lead / hashtags drift も抑えられたかを確認する
- B では mixed issue guard を壊さずに history-first drift が減ったかを確認する
- `KEEP / ROLLBACK / NEEDS_MORE_WORK` を判定する

絶対条件:
- production code edit 禁止
- test edit 禁止
- AGENTS / WORKLOG / current package docs 更新禁止
- route default / planning default / formatter / reference realization policy に触れない
- metrics だけで判断しない
- visible text を必ず読む

validation cases:
- case A1:
  - main target
  - latest adaptive explanatory baseline rerun
  - source:
    - `C:\tetie\notecode\logs\latest_generation_output.json`
  - want:
    - `repair_entry.repair_required = true`
    - `repair_call.patch_path_used = true`
    - `repair_applied = true`
    - `scope_acceptance_path = local_monotony_scope`
    - visible monotony improvement
    - title unchanged
    - lead unchanged
    - hashtags unchanged
    - heading sequence unchanged
- case A2:
  - fallback target
  - saved adaptive explanatory replay
  - source:
    - `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
  - want:
    - same telemetry goals as A1
    - visible monotony improvement
    - title / lead / hashtags / heading sequence unchanged
- case B:
  - guard
  - branding / company_introduction mixed issue case
  - source:
    - `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
  - want:
    - no broad rewrite
    - no heading drift regression
    - `local_monotony_scope` not wrongly applied to mixed issue
    - visible output stays current-business-first rather than history-first
- case C:
  - optional smoke
  - cheap short case only if needed

judge points:
- visible text:
  - 同じ丁寧文が塊で続く感じが減ったか
  - patch 的な継ぎはぎになっていないか
  - title / lead / hashtags / heading flow が崩れていないか
  - B が history-first に倒れず、current business 起点を保てているか
- telemetry:
  - `repair_entry.repair_required`
  - `repair_entry.repair_trigger_score`
  - `repair_entry.ending_bucket_max_run`
  - `repair_entry.ending_bucket_monotony_score`
  - `repair_entry.flagged_issue_types`
  - `repair_entry.patch_path_candidate`
  - `repair_entry.skip_reason`
  - `repair_call.patch_path_used`
  - `repair_applied`
  - `scope_acceptance_path`
  - `scope_rejection_reason`
  - `acceptance_rejection_reason`
- acceptance-specific:
  - heading sequence changed or not
  - title changed or not
  - lead changed or not
  - hashtags changed or not
  - closing section replaced or not
- guard:
  - company intro mixed issue に `local_monotony_scope` を誤適用していないか
  - `current-business-first keep line` を明確に壊していないか

minimum keep rule:
- case A1 or A2 の少なくとも 1 本で
  - `repair_entry.repair_required = true`
  - `repair_call.patch_path_used = true`
  - `repair_applied = true`
  - `scope_acceptance_path = local_monotony_scope`
  - visible monotony improvement
  - title / lead / hashtags drift なし
  - heading drift なし
- case B で mixed issue guard regression なし
- case B で current-business-first keep が visible に残る
- known unrelated failure 以外の新規 shared-check regression なし

rollback rule:
- A1 / A2 とも followup 後でも heading or title/lead/hashtags drift が残り、`repair_applied = false` のまま
- case B で mixed issue guard regression が出る
- case B が followup 後も明確に history-first drift を起こす
- visible quality が悪化し、patch 的な継ぎはぎが増える

needs-more-work rule:
- `repair_required` は true になるが `repair_applied` まで届かない
- `repair_applied` は true だが visible improvement が弱い
- A1/A2 の再現条件が不安定で keep judgment まで届かない
- B の history-first drift は減ったが current-business-first keep を言い切れない

allowed touched files:
- generated logs only
- validation note 1本

do not touch:
- production code
- tests
- AGENTS
- WORKLOG
- current planning package docs

recommended output file:
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_followup_note_2026-04-17.md`

stopping conditions:
- live validation のために code edit が必要になった
- adaptive target case を current branch state で再現できない
- formatter / prompt / route policy へ論点が逸れた
- followup diff の effect と live variability の境界が説明できない

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施した validation cases
3. case ごとの visible summary
4. case ごとの `repair_entry` summary
5. case ごとの `repair_call` summary
6. title / lead / hashtags drift が消えたか
7. heading sequence changed が消えたか
8. `scope_acceptance_path` が出たか
9. company intro mixed issue guard が維持されたか
10. current-business-first keep line が visible に戻ったか
11. `KEEP / ROLLBACK / NEEDS_MORE_WORK` の結論
12. 次が source-of-truth update prompt か、follow-up triage / implementation prompt か
13. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
