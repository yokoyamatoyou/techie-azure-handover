# separate window execution prompt sentence final monotony pipeline acceptance after adaptive reopen 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_adaptive_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_quality_guard_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_repair_lane_followup_note_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_adaptive_reopen_20260417-174409\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の依頼種別:
- follow-up triage / narrow implementation prompt
- source-of-truth update ではない
- deepresearch prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の downstream acceptance boundary を詰める
- first owner は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current questionは
  - A1 で `repair_required = true`
  - `patch_path_used = true`
  まで到達したのに、
  - `repair_applied = false`
  - `scope_acceptance_path = null`
  - `scope_rejection_reason = flagged_scope_drift`
  で止まる理由を narrow に説明し、safe なら直すこと
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

current boundary to inherit:
- upstream trigger mismatch is no longer the first blocker
- adaptive reopen moved A1 to:
  - `repair_entry.repair_required = true`
  - `repair_call.patch_path_used = true`
- current blocker is now downstream acceptance:
  - `ending_monotony_improved = true`
  - but `local_monotony_scope_preserved = false`
  - `effective_scope_preserved = false`
  - `scope_rejection_reason = flagged_scope_drift`
- case B mixed issue guard still must remain protected

primary question:
- why does A1 monotony-only repair still fail `local_monotony_scope` acceptance after adaptive reopen, and can that be fixed in `pipeline.py` without weakening mixed-issue guard

目的:
- `pipeline.py` owner だけで A1 の rejection reason を explainable にする
- safe なら local monotony scope acceptance boundary を narrow に調整する
- mixed issue / company intro guard を壊さない
- next prompt を live re-validation に戻せる状態にする

first owner and likely touchpoints:
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `_repair_preserves_local_monotony_scope()`
  - `_run_optional_repair()`
  - related scope / alignment / acceptance telemetry only when needed

allowed touched files:
- primary:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- docs note:
  - C:\tetie\notecode\docs\separate_window_sentence_final_monotony_pipeline_acceptance_after_adaptive_note_2026-04-17.md

do not touch:
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\newalgorithm_pipeline\*.py
- C:\tetie\notecode\note\natural_blog_core.py
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\note_writer_app.py
- AGENTS / WORKLOG / current planning package docs

good change shape:
- monotony-only acceptance remains local
- mixed issue remains excluded
- title / lead / hashtags / heading order are still protected
- rollback remains 1 file
- telemetry remains readable

bad change shape:
- disable `flagged_scope_drift` broadly
- let `local_monotony_scope` through for mixed issues
- reopen `quality_guard.py` again in the same step
- widen patch acceptance beyond monotony-only local fixes
- prompt accretion / formatter / route policy changes

今回やること:
1. inspect A1 live rejection path in `pipeline.py`
2. compare current A1 behavior with the focused acceptance test path
3. identify whether the miss is caused by:
   - changed heading count / section identity
   - section token overlap threshold
   - max changed heading count
   - length ratio bounds
   - acceptance helper being too strict for adaptive explanatory prose
4. if safe, implement one narrow adjustment in `pipeline.py`
5. add focused tests for:
   - adaptive explanatory monotony repair accepted via `local_monotony_scope`
   - mixed issue still rejected
   - over-broad rewrite still rejected

preferred implementation shape:
- keep `_repair_preserves_local_monotony_scope()` readable
- if adjusting thresholds, do it for monotony-only local acceptance path only
- if needed, add a narrower explanatory-local helper instead of weakening the generic helper globally
- preserve current company intro and mixed-issue guard behavior

focused tests to inspect first:
- `test_simple_note_pipeline_repairs_explanatory_monotony_with_local_scope_acceptance`
- existing local monotony scope tests
- company intro rejection tests
- patch rewrite rejection tests
- add adaptive explanatory acceptance test only if current one does not cover the live rejection shape

test execution order:
1. owner-local focused run
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "explanatory_monotony or local_monotony_scope or rewrites_unflagged_section or company_intro" -q`
2. owner-local full file if step 1 passes
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
3. neighbor check if code diff landed
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
4. shared checks only if real code changed
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "not st08b4_industry_analysis_title_and_lead_do_not_echo_prompt" -q`

pass condition:
- A1-like monotony-only case can be explained or fixed in `pipeline.py`
- if changed, `repair_applied = true` and `scope_acceptance_path = local_monotony_scope` become reachable in focused validation
- mixed issue / company intro guard remains intact
- next prompt can validly return to live re-validation

stop and report instead of coding if:
- safe acceptance reopen would require touching `quality_guard.py` again
- mixed issue guard cannot be preserved
- second owner is needed
- same phase fails 3 times

recommended outcomes:
- outcome A:
  - `pipeline.py` narrow fix lands safely
  - next prompt is live re-validation
- outcome B:
  - no code diff
  - note explains why current acceptance boundary should stay
  - next prompt is management retriage

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. touched files
4. A1 rejection の具体理由
5. changed acceptance condition or telemetry
6. new focused tests
7. company intro / mixed issue guard を壊していないこと
8. tests の結果
9. AGENTS / WORKLOG / current package docs を更新していないこと
10. 次が live re-validation prompt か management retriage prompt か
```
