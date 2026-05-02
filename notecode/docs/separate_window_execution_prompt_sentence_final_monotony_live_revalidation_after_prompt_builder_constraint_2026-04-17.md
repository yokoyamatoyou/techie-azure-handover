# separate window execution prompt sentence final monotony live revalidation after prompt builder constraint 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_quality_guard_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_adaptive_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_prompt_builder_constraint_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_adaptive_reopen_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_adaptive_reopen_20260417-174409\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json
- C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py

今回の依頼種別:
- live re-validation prompt
- source-of-truth update ではない
- deepresearch prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の live re-validation を再実施する
- owner diff は次の 3 file owner に閉じた状態として扱う
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
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
  - `repair_not_required` を live で読めるようにした
- `quality_guard.py`
  - explanatory short monotony-only promotion は keep
  - explanatory adaptive monotony-only promotion を追加
  - adaptive reopen conditions:
    - `article_type == explanatory_article`
    - `length_mode == adaptive`
    - `ending_bucket_max_run >= 20`
    - `ending_bucket_monotony_score >= 0.6`
    - mixed-issue exclusions and existing guard exclusions remain
  - global threshold is unchanged
- `prompt_builder.py`
  - monotony-only repair prompt に immutable heading/order contract を追加
  - hard constraints:
    - current heading list fixed
    - heading rename/add/drop/reorder forbidden
    - closing section replacement forbidden
    - rewrite scope limited to flagged span and nearby body sentences

core validation question:
- adaptive explanatory live target で upstream trigger, repair prompt constraint, downstream acceptance lane が finally 接続するか

目的:
- case A1 / A2 で本当に
  - `repair_entry.repair_required = true`
  - `repair_call.patch_path_used = true`
  - `repair_applied = true`
  - `scope_acceptance_path = local_monotony_scope`
  を確認する
- repaired output が heading rename / reorder を起こさず、acceptance が通るかを確認する
- case B mixed issue guard が壊れていないか確認する
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
    - heading sequence unchanged
- case A2:
  - fallback target
  - saved adaptive explanatory replay
  - source:
    - `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
  - want:
    - same telemetry goals as A1
    - visible monotony improvement
    - heading sequence unchanged
- case B:
  - guard
  - branding / company_introduction mixed issue case
  - source:
    - `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
  - want:
    - no broad rewrite
    - no heading drift regression
    - `local_monotony_scope` not wrongly applied to mixed issue
- case C:
  - optional smoke
  - cheap short case only if needed

judge points:
- visible text:
  - 同じ丁寧文が塊で続く感じが減ったか
  - patch 的な継ぎはぎになっていないか
  - title / lead / hashtags / heading flow が崩れていないか
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
- acceptance-specific:
  - heading sequence changed or not
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
  - heading / lead / hashtags drift なし
- case B で mixed issue guard regression なし
- known unrelated failure 以外の新規 shared-check regression なし

rollback rule:
- case A1 / A2 とも prompt_builder constraint 後でも heading drift が残り、`scope_rejection_reason = flagged_scope_drift` のまま
- case B で mixed issue guard regression が出る
- visible quality が悪化し、patch 的な継ぎはぎが増える

needs-more-work rule:
- `repair_required` は true になるが `repair_applied` まで届かない
- `repair_applied` は true だが visible improvement が弱い
- A1/A2 の再現条件が不安定で keep judgment まで届かない

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
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_note_2026-04-17.md`

stopping conditions:
- live validation のために code edit が必要になった
- adaptive target case を current branch state で再現できない
- formatter / prompt / route policy へ論点が逸れた
- prompt constraint diff の effect と live variability の境界が説明できない

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施した validation cases
3. case ごとの visible summary
4. case ごとの `repair_entry` summary
5. case ごとの `repair_call` summary
6. heading sequence changed が消えたか
7. `scope_acceptance_path` が出たか
8. company intro mixed issue guard が維持されたか
9. `KEEP / ROLLBACK / NEEDS_MORE_WORK` の結論
10. 次が source-of-truth update prompt か、follow-up triage prompt か
11. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
