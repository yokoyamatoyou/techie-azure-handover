# separate window execution prompt sentence final monotony prompt builder rollback 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_followup_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_prompt_builder_followup_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_followup_20260417-195828\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の依頼種別:
- rollback implementation prompt
- source-of-truth update ではない
- deepresearch prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line について、`prompt_builder.py` owner の followup diff を rollback する
- rollback は narrow に `prompt_builder.py` とその focused tests だけへ閉じる
- `pipeline.py` / `quality_guard.py` / AGENTS / WORKLOG / current package docs は更新しない
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

rollback target:
- `prompt_builder.py` owner の latest followup diff
- specifically remove or revert the lines added for:
  - monotony-only repair prompt の `TITLE` freeze
  - monotony-only repair prompt の `LEAD` freeze
  - monotony-only repair prompt の `HASHTAGS` freeze
  - `local_run_plus_two` sentence-cluster anchor wording
  - `TITLE / LEAD / HASHTAGS / 他見出しへ移動しない` line
  - `_filter_section_shadow_lines()` で `company_intro_focus=自社の事業内容を紹介する` を keep する変更

why rollback is required:
- latest live re-validation after prompt_builder followup is `ROLLBACK`
- case A1:
  - `repair_required = false`
  - repair lane 未到達
- case A2:
  - patch path 到達後も `repair_applied = false`
  - heading/title/hashtags drift が残った
- case B:
  - mixed issue guard は維持したが history-first drift が残った
  - `current-business-first keep line` は visible に戻らなかった
- `scope_acceptance_path = local_monotony_scope` は 3 case とも未出力
- よって latest prompt_builder followup diff は keep しない

first owner:
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`

allowed touched files:
- primary:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- tests:
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- docs note:
  - C:\tetie\notecode\docs\separate_window_sentence_final_monotony_prompt_builder_rollback_note_2026-04-17.md

do not touch:
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\newalgorithm_pipeline\*.py
- C:\tetie\notecode\note\natural_blog_core.py
- C:\tetie\notecode\note\current_mainline_runner.py
- AGENTS / WORKLOG / current planning package docs

implementation rules:
- rollback only the latest followup additions
- keep the earlier prompt_builder constraint diff unless it is inseparable
- do not add replacement wording in the same step
- do not broaden prompt text
- do not add new helpers unless rollback cannot be expressed cleanly without them
- prefer restoring the previous simpler wording over introducing another variant

good rollback shape:
- small diff
- obvious reversal of the latest followup additions
- prompt surface becomes smaller, not larger
- focused tests updated to match the rolled-back state

bad rollback shape:
- partial rollback that leaves dead branches or redundant wording
- compensating with new prompt lines
- reopening `pipeline.py` or `quality_guard.py`
- mixing rollback with fresh experimentation

今回やること:
1. inspect the latest followup diff in `prompt_builder.py`
2. remove the added freeze/locality lines for monotony-only repair prompt
3. revert the `company_intro_focus` keep-through-filter change
4. update focused tests so they assert the restored pre-followup behavior
5. run owner-local and shared checks

tests to update:
- remove or adjust tests that specifically require:
  - title / lead / hashtags freeze lines
  - strengthened locality anchor wording
  - company-intro keep-through-filter line
- keep tests for the earlier monotony-only immutable heading/order contract if that earlier diff remains

test execution order:
1. owner-local focused run
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "repair_prompt or patch_scope or company_intro or heading_count or explanatory_monotony" -q`
2. owner-local full file if step 1 passes
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
3. neighbor check if code diff landed
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
4. shared checks only if real code changed
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "not st08b4_industry_analysis_title_and_lead_do_not_echo_prompt" -q`

pass condition:
- latest prompt_builder followup diff is cleanly rolled back
- prompt surface is reduced
- no regression in existing remaining prompt_builder tests
- next prompt can move to visible smoke validation or management retriage

stop and report instead of coding if:
- the rollback cannot be isolated from the earlier prompt_builder constraint diff
- rollback requires reopening `pipeline.py` or `quality_guard.py`
- same phase fails 3 times

recommended outcome:
- outcome A:
  - rollback lands safely
  - next prompt is visible smoke validation
- outcome B:
  - rollback boundary is not clean
  - note explains why management retriage is needed

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. touched files
4. rollback した prompt lines / filter change
5. updated focused tests
6. tests の結果
7. AGENTS / WORKLOG / current package docs を更新していないこと
8. 次が visible smoke validation prompt か management retriage prompt か
```
