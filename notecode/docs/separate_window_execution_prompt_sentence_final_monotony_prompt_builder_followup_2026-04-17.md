# separate window execution prompt sentence final monotony prompt builder followup 2026-04-17

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
- C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_constraint_20260417-183317\summary.json
- C:\tetie\notecode\logs\sentence_final_monotony_actual_repair_prompt_triage_20260417-185120\summary.json
- C:\tetie\notecode\logs\sentence_final_monotony_actual_repair_prompt_triage_20260417-185120\case_a1_latest_adaptive_explanatory_reconstructed_prompt.txt
- C:\tetie\notecode\logs\sentence_final_monotony_actual_repair_prompt_triage_20260417-185120\case_b_company_intro_guard_reconstructed_prompt.txt
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の依頼種別:
- prompt_builder owner implementation prompt
- source-of-truth update ではない
- deepresearch prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の next owner を `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` に固定する
- actual repair prompt triage で見えた emission / scope gaps を `prompt_builder.py` のみで narrow 実装する
- production code の owner は `prompt_builder.py` に閉じる
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

current exact blocker from triage:
- A1:
  - immutable heading/order contract は actual repair prompt に出ていた
  - closing replacement 禁止 line も出ていた
  - それでも `PATCH_SCOPE` は
    - `ending_bucket_monotony / window=local_run_plus_two`
    の location-free な指定に留まり、actual target sentence / paragraph / heading anchor が弱い
  - さらに title / lead / hashtags freeze line が actual prompt にない
- B:
  - `company_intro_focus=自社の事業内容を紹介する` が repair prompt 生成途中で落ちている
  - 原因は `prompt_builder.py` の section-shadow filter が heading 名一致 line 以外を落とすため
  - その結果、repair prompt 側に `current-business-first keep line` 相当の signal が残っていない

management decision to inherit:
- current first owner:
  - `PROMPT_BUILDER_OWNER`
- primary judge:
  - `PROMPT_EMISSION_MISSING`
- secondary issue:
  - `PATCH_SCOPE_MISMATCH`

first owner and likely touchpoints:
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `_filter_section_shadow_lines()`
  - monotony-only patch scope helper around the heading/order contract lines
  - `build_repair_prompt()`
  - nearby prompt-assembly helpers only if needed

allowed touched files:
- primary:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- tests:
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- docs note:
  - C:\tetie\notecode\docs\separate_window_sentence_final_monotony_prompt_builder_followup_note_2026-04-17.md

do not touch:
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\newalgorithm_pipeline\*.py
- C:\tetie\notecode\note\natural_blog_core.py
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\note_writer_app.py
- AGENTS / WORKLOG / current planning package docs

implementation hypothesis:
- if `prompt_builder.py` is adjusted so that
  - company-intro repair prompt keeps `current-business-first` signal even after section-shadow filtering
  - monotony-only repair prompt explicitly freezes title / lead / hashtags
  - monotony-only local patch wording anchors edits to the flagged heading / paragraph vicinity more concretely
  then the existing strict acceptance helper can stay unchanged and A1/B have a realistic path to `repair_applied=true`

good change shape:
- 1-file narrow prompt-side diff
- no acceptance relaxation
- no threshold change
- no payload/schema expansion in `pipeline.py`
- company-intro keep signal survives filtering
- monotony-only repair prompt becomes more local and more immutable at the visible surface

bad change shape:
- weaken `flagged_scope_drift`
- reopen `pipeline.py` payload boundary in the same step
- add generic prompt accretion unrelated to the observed gaps
- touch route default / planning default / formatter

今回やること:
1. inspect the current prompt-builder paths that emit and then filter:
   - monotony-only patch scope lines
   - section-shadow lines
   - company intro keep signal lines
2. change `_filter_section_shadow_lines()` or nearby assembly so company-intro repair prompt keeps the non-heading keep signal that tells the model to start from current business, not history
3. strengthen monotony-only prompt wording so visible-surface drift is explicitly frozen:
   - title must remain exactly unchanged
   - lead must remain exactly unchanged
   - hashtags must remain exactly unchanged
4. if possible within `prompt_builder.py` only, strengthen locality wording:
   - revise only the flagged sentence cluster and immediately adjacent body sentences
   - do not rewrite other paragraphs under the same heading unless unavoidable
   - do not move content into title / lead / hashtags / other headings
5. add focused tests that prove these lines are present only on the intended paths

minimum acceptance target for this diff:
- A1-oriented prompt text now includes:
  - title freeze line
  - lead freeze line
  - hashtags freeze line
  - stronger local sentence-cluster anchoring line
- B-oriented prompt text now keeps:
  - `company_intro_focus=自社の事業内容を紹介する` or equivalent current-business-first keep signal after filtering
- existing mixed-issue / monotony-only scoping remains narrow

focused tests to inspect first:
- tests covering `build_repair_prompt_from_diagnostics()`
- tests covering `PATCH_SCOPE`
- tests covering section shadow filtering
- tests covering company-intro repair prompt wording

new focused tests to add:
- monotony-only repair prompt includes exact title / lead / hashtags freeze lines
- monotony-only repair prompt includes stronger local-sentence anchor wording
- company-intro shadow prompt keeps `company_intro_focus` or equivalent keep signal after `_filter_section_shadow_lines()`
- mixed issue prompt does not accidentally receive monotony-only heading contract if not intended

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
- diff is 1-file narrow on `prompt_builder.py` plus tests
- company-intro keep signal no longer drops from repair prompt
- monotony-only prompt now freezes title / lead / hashtags explicitly
- stronger local anchoring lines are present
- no regression in existing prompt tests
- next prompt can validly return to live re-validation

stop and report instead of coding if:
- keeping the company-intro signal requires reopening `pipeline.py`
- title / lead / hashtags freeze cannot be added without changing non-prompt owners
- tests show collision with mixed issue or company-intro paths
- same phase fails 3 times

recommended outcomes:
- outcome A:
  - prompt_builder follow-up diff lands safely
  - next prompt is live re-validation
- outcome B:
  - no code diff
  - note explains why `prompt_builder.py` alone is insufficient
  - next prompt is `pipeline.py` payload-boundary implementation or management retriage

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. touched files
4. A1 向けに追加した title / lead / hashtags freeze lines
5. A1 向けに追加した locality anchor wording
6. B 向けに keep した current-business-first signal
7. new or updated focused tests
8. tests の結果
9. AGENTS / WORKLOG / current package docs を更新していないこと
10. 次が live re-validation prompt か、follow-up triage / pipeline payload prompt か
```
