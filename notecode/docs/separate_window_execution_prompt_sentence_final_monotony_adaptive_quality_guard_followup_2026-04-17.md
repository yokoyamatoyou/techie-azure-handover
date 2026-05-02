# separate window execution prompt sentence final monotony adaptive quality guard followup 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_quality_guard_triage_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_quality_guard_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_quality_guard_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_target_boundary_triage_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_target_boundary_note_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_quality_guard_20260417-170631\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json

今回の依頼種別:
- adaptive quality_guard follow-up prompt
- source-of-truth update ではない
- deepresearch prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の `ADAPTIVE_SCOPE_REOPEN` を narrow に詰める
- first owner は `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- current production-like explanatory target が `adaptive` のため、
  short-only explanatory monotony promotion boundary を reopen するかどうかを判断し、safe なら実装する
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

boundary already fixed:
- `pipeline.py` acceptance lane is not the current blocker
- `quality_guard.py` short-only explanatory promotion landed
- live re-validation missed because A1/A2 contracts were `adaptive`
- target boundary triage verdict:
  - `ADAPTIVE_SCOPE_REOPEN`

current evidence to inherit:
- case A1 current rerun:
  - `length_mode = adaptive`
  - `repair_required = false`
  - `repair_trigger_score = 0.1944`
  - `ending_bucket_max_run = 8`
  - `ending_bucket_monotony_score = 0.1951`
  - `flagged_issue_types = ["ending_bucket_monotony"]`
  - `patch_path_candidate = true`
  - `skip_reason = repair_not_required`
- case A2 current rerun:
  - `length_mode = adaptive`
  - `repair_required = false`
  - `repair_trigger_score = 0.286`
  - `ending_bucket_max_run = 9`
  - `ending_bucket_monotony_score = 0.1957`
  - `flagged_issue_types = ["ending_bucket_monotony"]`
  - `patch_path_candidate = true`
  - `skip_reason = repair_not_required`
- case B guard:
  - mixed issue guard remains intact
  - `local_monotony_scope` misapplication not observed

primary question:
- should explanatory monotony promotion remain short-only, or should current production-like `adaptive` explanatory cases also be eligible under a narrow monotony-only rule

目的:
- `quality_guard.py` owner だけで explanatory monotony promotion boundary を re-evaluate する
- global threshold は変えずに、adaptive explanatory monotony-only case へ narrow reopen が可能か判断する
- safe なら 1 file owner で実装する
- safe でなければ docs-only note に落として停止する

first owner and likely touchpoints:
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
  - `_is_explanatory_short_ending_bucket_monotony_candidate()`
  - `evaluate_quality_guard()`
  - explanatory monotony promotion condition only

allowed touched files:
- primary:
  - C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
  - C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py
- secondary only if integration proof is required:
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- docs note:
  - C:\tetie\notecode\docs\separate_window_sentence_final_monotony_adaptive_quality_guard_followup_note_2026-04-17.md

do not touch:
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\newalgorithm_pipeline\*.py
- C:\tetie\notecode\note\natural_blog_core.py
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\note_writer_app.py
- AGENTS / WORKLOG / current planning package docs

good change shape:
- explanatory monotony promotion is still monotony-only
- adaptive reopen is limited to explanatory article only
- mixed issue remains excluded
- global threshold stays `0.58`
- company intro monotony promotion remains unchanged
- rollback remains 1 file

bad change shape:
- lower the global trigger threshold
- open promotion to all adaptive articles
- reuse company intro branch broadly
- reopen pipeline acceptance lane again
- prompt accretion / formatter / route policy changes
- deepresearch detour

今回やること:
1. compare short-only branch and adaptive live targets
2. decide whether an adaptive explanatory monotony-only candidate helper should replace or extend the short-only helper
3. if safe, implement one narrow rule only
4. add focused tests for:
   - strong adaptive explanatory monotony-only case promotes to `repair_required=true`
   - weak adaptive explanatory monotony case stays below gate
   - existing short/company-intro/mixed-issue protections still hold
5. stop if safe boundary cannot be defended

preferred implementation shape:
- keep the existing short-specific logic readable
- either:
  - rename helper to explanatory monotony candidate and handle `short` + `adaptive` explicitly
  - or add a second adaptive helper with tighter thresholds
- if adaptive is reopened, require stricter conditions than short when needed
  - example dimensions to evaluate:
    - `ending_bucket_max_run`
    - `ending_bucket_monotony_score`
    - mixed-issue exclusions
    - repeated opening / duplicate paragraph exclusion
    - sentence integrity exclusion
    - proposition density exclusion
- do not guess: justify thresholds from A1/A2 artifacts and existing guard logic

focused tests to inspect first:
- `test_evaluate_quality_guard_promotes_repair_for_company_intro_ending_bucket_monotony`
- `test_evaluate_quality_guard_promotes_repair_for_short_rhythm_flatness_cluster`
- the two explanatory short monotony tests added in the previous step
- add adaptive-only focused tests if you change adaptive eligibility

test execution order:
1. owner-local focused run
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -k "company_intro_ending_bucket_monotony or short_rhythm_flatness_cluster or explanatory or adaptive" -q`
2. owner-local full file if step 1 passes
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
3. neighbor check if code diff landed
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
4. shared checks only if real code changed
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "not st08b4_industry_analysis_title_and_lead_do_not_echo_prompt" -q`

pass condition:
- adaptive explanatory monotony-only case can be explained by current or updated trigger policy
- if changed, `quality_guard.py` remains 1-file narrow
- company intro promotion and mixed-issue guard remain intact
- next prompt can validly return to live re-validation

stop and report instead of coding if:
- adaptive reopen would require lowering the global threshold
- adaptive explanatory monotony cannot be separated from broader AI-feel problems
- second owner is needed
- same phase fails 3 times

recommended outcomes:
- outcome A:
  - adaptive explanatory monotony promotion lands safely
  - next prompt is live re-validation
- outcome B:
  - no code diff
  - note explains why short-only should remain
  - next prompt is management retriage

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. touched files
4. adaptive reopen を採用したかどうか
5. current or changed adaptive trigger conditions
6. new focused tests
7. company intro promotion と mixed-issue guard を壊していないこと
8. tests の結果
9. AGENTS / WORKLOG / current package docs を更新していないこと
10. 次が live re-validation prompt か management retriage prompt か
```
