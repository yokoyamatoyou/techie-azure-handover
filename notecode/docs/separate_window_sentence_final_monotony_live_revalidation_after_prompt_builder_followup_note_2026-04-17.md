# separate window sentence final monotony live revalidation after prompt builder followup note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の `prompt_builder.py` followup 後 live re-validation note である
- source-of-truth update ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- validation setup
- shared checks
- case A1 latest adaptive explanatory rerun
- case A2 saved adaptive explanatory replay
- case B company intro mixed-issue guard
- scope_acceptance_path / drift summary
- judgment
- next step
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
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_actual_repair_prompt_triage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_constraint_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_prompt_builder_constraint_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_followup_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_prompt_builder_followup_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_constraint_20260417-183317\summary.json`
- `C:\tetie\notecode\logs\sentence_final_monotony_actual_repair_prompt_triage_20260417-185120\summary.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
- `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\current_mainline_ui_matrix.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py`

## 実施範囲

- `sentence-final pattern monotony cap + single repair` line の live re-validation を current code state で再実施した
- 実行経路は current success path に固定した
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- rerun は `execute_current_mainline_generation(MinimalPipeline(LLMClient()), input_contract, prompt_raw)` で A1 / A2 / B の 3 case に閉じた
- production code edit / test edit は行っていない
- touched files は generated logs とこの docs note のみ

## Validation Setup

- generated artifact root:
  - `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_followup_20260417-195828\`
- root summary:
  - `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_followup_20260417-195828\summary.json`
- preflight:
  - `run_live_preflight(LLMClient())`
  - `passed = true`
  - `selected_model = gpt-5.4-mini`
- cases:
  - A1:
    - `C:\tetie\notecode\logs\latest_generation_output.json`
  - A2:
    - `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
  - B:
    - `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
    - `rerun` section

## Shared Checks

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - `123 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
  - `83 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "not st08b4_industry_analysis_title_and_lead_do_not_echo_prompt" -q`
  - `233 passed, 1 deselected`
- known unrelated failure 以外の新規 shared-check regression は確認していない

## Case A1 Latest Adaptive Explanatory Rerun

### Visible Summary

- 本文は読めるが、followup diff の keep evidence にはならない
- repair lane 自体が起動しておらず、冒頭から broad rewrite になっている
- title / lead / hashtags はすべて baseline から変わった
- heading sequence も変わっており、`current body を local repair した` 読みにはならない
- visible monotony improvement を `single repair` の効果として読むことはできない

### `repair_entry` Summary

- `repair_required = false`
- `repair_trigger_score = 0.1873`
- `ending_bucket_max_run = 20`
- `ending_bucket_monotony_score = 0.4444`
- `flagged_issue_types = ["ending_bucket_monotony"]`
- `patch_path_candidate = true`
- `skip_reason = repair_not_required`

### `repair_call` Summary

- `repair_call = {}`
- `patch_path_used = false`
- `repair_applied = false`
- `scope_acceptance_path = null`
- `scope_rejection_reason = null`

### Read

- A1 は followup diff の core target だったが、`repair_required = true` にすら届いていない
- title / lead / hashtags freeze line の効果も live では確認不能だった
- keep rule の main target としては failure

## Case A2 Saved Adaptive Explanatory Replay

### Visible Summary

- 本文は読み物としては成立している
- ただし repair lane が動いた後も heading rename / closing rewrite が残っている
- title は変わり、hashtags も新規に出ている
- `## 問い合わせの減少は、出発点として扱う` まで含めて broad rewrite 寄りで、local patch に見えない

### `repair_entry` Summary

- `repair_required = true`
- `repair_trigger_score = 0.58`
- `ending_bucket_max_run = 11`
- `ending_bucket_monotony_score = 0.2444`
- `flagged_issue_types = ["heading_reanchor", "ending_bucket_monotony"]`
- `patch_path_candidate = true`
- `skip_reason = ""`

### `repair_call` Summary

- `patch_path_used = true`
- `repair_applied = false`
- `ending_monotony_improved = true`
- `scope_rejection_reason = flagged_scope_drift`
- `scope_acceptance_path = null`

### Read

- A2 は repair lane までは到達したが、acceptance には届いていない
- followup diff 後でも `title / hashtags drift + heading sequence changed` が残った
- minimum keep rule の positive evidence にはならない

## Case B Company Intro Mixed-Issue Guard

### Visible Summary

- mixed issue に `local_monotony_scope` を誤 accept してはいない
- ただし visible output は依然として history-first 寄りで、`current-business-first keep line` は戻っていない
- title / lead / first heading が `130年余りの歩み` 起点で、guard case としては regression 寄り
- 5 heading へ広がっており、broad rewrite 感も消えていない

### `repair_entry` Summary

- `repair_required = true`
- `repair_trigger_score = 0.8`
- `ending_bucket_max_run = 27`
- `ending_bucket_monotony_score = 0.931`
- `flagged_issue_types = ["shadow_section_drift", "ending_bucket_monotony"]`
- `patch_path_candidate = true`
- `skip_reason = ""`

### `repair_call` Summary

- `patch_path_used = true`
- `repair_applied = false`
- `ending_monotony_improved = true`
- `scope_rejection_reason = flagged_scope_drift`
- `scope_acceptance_path = null`
- `controlled_realization_drift_headings = ["130年余りの歩みが今の京都工業をつくる"]`

### Read

- mixed issue guard の strictness 自体は維持された
- しかし visible keep line は守れておらず、history-first drift が明確に残った
- B も keep evidence ではなく rollback side の evidence になった

## `scope_acceptance_path` / Drift Summary

- case A1:
  - not emitted
- case A2:
  - not emitted
- case B:
  - not emitted
- 今回の live rerun では `scope_acceptance_path = local_monotony_scope` は 1 本も確認できなかった
- title / lead / hashtags drift が消えた case もなかった
- heading sequence changed も消えていない

## Judgment

- verdict:
  - `ROLLBACK`

### Why Not `KEEP`

- minimum keep rule の主条件だった
  - `repair_entry.repair_required = true`
  - `repair_call.patch_path_used = true`
  - `repair_applied = true`
  - `scope_acceptance_path = local_monotony_scope`
  - visible monotony improvement without title / lead / hashtags / heading drift
  を A1 / A2 のどちらでも満たしていない
- B でも `current-business-first keep line` は visible に戻っていない

### Why `ROLLBACK` Rather Than `NEEDS_MORE_WORK`

- rollback rule の
  - `A1 / A2 とも followup 後でも heading or title/lead/hashtags drift が残り、repair_applied = false のまま`
  を満たした
- さらに case B も followup 後に明確な history-first drift を残した
- mixed issue guard の strictness が維持されていても、followup diff を keep する理由には足りない

### Exact Read

- followup diff は live keep gate を通過できなかった
- A1 では repair lane 不発で効果を示せず、A2 では repair lane 到達後も drift を止められず、B では company intro keep line を戻せなかった
- current judgment は `ROLLBACK` が妥当

## Next Step

- 次は source-of-truth update prompt ではない
- 次は follow-up implementation prompt が必要
- ただし内容は keep continuation ではなく rollback implementation prompt として扱うのが筋である
- rollback owner は first read 上 `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` に閉じる

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
