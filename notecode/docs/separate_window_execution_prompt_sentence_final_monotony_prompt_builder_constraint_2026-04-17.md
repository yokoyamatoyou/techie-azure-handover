# separate window execution prompt sentence final monotony prompt builder constraint 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_pipeline_acceptance_after_adaptive_note_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_adaptive_reopen_20260417-174409\summary.json
- C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\helper_analysis.json
- C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\repair_capture.json
- C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\probe.json
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の依頼種別:
- prompt_builder owner implementation prompt
- source-of-truth update ではない
- deepresearch prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の next owner を `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` に固定する
- monotony-only repair prompt に immutable heading/order contract を追加し、repair output が heading rename / add / drop / reorder / closing replacement を起こさないようにする
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

current blocker to solve:
- adaptive reopen 後の A1 live rerun では
  - `repair_required = true`
  - `patch_path_used = true`
  - `ending_monotony_improved = true`
  まで進んでいる
- それでも `repair_applied = false` で止まる理由は、
  repaired output が monotony-only local patch の範囲を超えて
  - heading rename
  - closing section replacement
  - section reorder
  を起こし、実質 `heading_sequence_changed` として `flagged_scope_drift` で reject されるため
- `pipeline.py` acceptance helper は意図どおり strict に動いているので、次に触るべきは repair prompt constraint owner

management decision to inherit:
- next owner:
  - `PROMPT_BUILDER_OWNER`
- why:
  - `pipeline.py` は patch-path payload をすでに repair prompt へ渡している
  - 欠けているのは `immutable heading/order contract` の明示である
  - acceptance を緩めるのではなく、repair output を heading-local に縛るのが正しい

first owner and likely touchpoints:
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `_repair_structure_guard_lines()`
  - `build_repair_prompt()`
  - `_build_shadow_patch_scope_lines()` and nearby patch scope wording only if needed
  - `build_repair_prompt_from_diagnostics()` only if needed for passing extra guard lines

allowed touched files:
- primary:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- tests:
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- docs note:
  - C:\tetie\notecode\docs\separate_window_sentence_final_monotony_prompt_builder_constraint_note_2026-04-17.md

do not touch:
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\newalgorithm_pipeline\*.py
- C:\tetie\notecode\note\natural_blog_core.py
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\note_writer_app.py
- AGENTS / WORKLOG / current planning package docs

implementation hypothesis:
- if the monotony-only repair prompt explicitly states
  - current heading list is immutable
  - heading rename/add/drop/reorder is forbidden
  - closing section replacement is forbidden
  - allowed edits are only within flagged span and nearby body sentences
  then A1-like repair output will stay section-local enough for existing acceptance helper to pass

good change shape:
- prompt-side hard constraints only
- monotony-only path remains local
- no acceptance boundary relaxation
- no global rewrite instruction
- rollback remains 1 file

bad change shape:
- weaken `flagged_scope_drift` handling
- reopen `pipeline.py` acceptance in the same step
- add generic verbose prompt accretion unrelated to heading/order lock
- touch route default / planning default / formatter

今回やること:
1. inspect current repair prompt wording around:
   - `_repair_structure_guard_lines()`
   - `PATCH_SCOPE`
   - section shadow / target headings
2. add hard constraints for monotony-only repair:
   - keep current heading text exactly unchanged
   - do not add headings
   - do not drop headings
   - do not reorder headings
   - do not replace the closing section with a new closing concept
   - revise only flagged span and nearby body sentences
3. if needed, scope these lines so they apply when patch path is monotony-only local repair
4. add or update focused tests that assert the repair prompt now includes these constraints

focused tests to inspect first:
- tests covering `build_repair_prompt_from_diagnostics()`
- tests covering patch scope lines
- tests covering shadow patch scope lines
- add one focused assertion that monotony-only repair prompt contains immutable heading/order contract lines

test execution order:
1. owner-local focused run
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "repair_prompt or patch_scope or heading_count or explanatory_monotony" -q`
2. owner-local full file if step 1 passes
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
3. neighbor check if code diff landed
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
4. shared checks only if real code changed
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "not st08b4_industry_analysis_title_and_lead_do_not_echo_prompt" -q`

pass condition:
- prompt_builder diff is 1-file narrow
- repair prompt contains immutable heading/order contract for monotony-only repair
- no regression in existing prompt tests
- next prompt can validly return to live re-validation

stop and report instead of coding if:
- immutable heading/order contract cannot be added without reopening `pipeline.py`
- tests show the new constraints would collide with shadow/comparative/company-intro paths
- second owner is needed
- same phase fails 3 times

recommended outcomes:
- outcome A:
  - prompt_builder constraint diff lands safely
  - next prompt is live re-validation
- outcome B:
  - no code diff
  - note explains why prompt_builder owner is insufficient
  - next prompt is management retriage

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. touched files
4. added immutable heading/order contract lines
5. new or updated focused tests
6. tests の結果
7. AGENTS / WORKLOG / current package docs を更新していないこと
8. 次が live re-validation prompt か management retriage prompt か
```
