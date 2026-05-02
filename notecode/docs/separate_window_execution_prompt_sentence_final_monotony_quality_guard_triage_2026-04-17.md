# separate window execution prompt sentence final monotony quality guard triage 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_triage_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_pipeline_acceptance_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_validation_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_validation_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_repair_lane_followup_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_repair_lane_followup_note_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\summary.json

今回の依頼種別:
- quality guard triage / narrow implementation prompt
- deepresearch prompt ではない
- source-of-truth update ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の upstream trigger owner を確認する
- first owner は `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- current questionは
  - `ending_bucket_monotony` 単独
  - `flagged_spans` と `patch_path_candidate` はある
  - しかし `repair_required=false`
  になる explanatory short case を current trigger policy でどう扱うか
  に限定する
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

inherited boundary:
- `pipeline.py` owner の follow-up で分かったこと:
  - focused test は `_run_optional_repair()` に `repair_required=true` を直接渡していた
  - live monotony case は acceptance lane の前で止まっていた
  - actual blocker は `repair_call_unavailable` ではなく `repair_required=false`
- live-like case summary:
  - latest rerun:
    - `ending_bucket_max_run = 11`
    - `ending_bucket_monotony_score = 0.2558`
    - `repair_trigger_score = 0.4258`
    - `repair_required = false`
  - saved rerun:
    - `ending_bucket_max_run = 26`
    - `ending_bucket_monotony_score = 0.5417`
    - `repair_trigger_score = 0.4556`
    - `repair_required = false`
- current quality guard line:
  - base gate is `repair_trigger_score >= 0.58`
  - company intro monotony has a specific promotion line
  - explanatory monotony-only case does not have a dedicated promotion line yet

目的:
- `quality_guard.py` owner で、explanatory short monotony-only case の trigger policy を narrow に説明する
- current threshold / promotion rules のどこが case A を落としているかを特定する
- safe なら `quality_guard.py` 1 owner で narrow fix を入れる
- safe でないなら docs-only boundary note を返し、deepresearch ではなく別 triage に止める

first owner and likely touchpoints:
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
  - `measure_diagnostics()`
  - `evaluate_quality_guard()`
  - `repair_trigger_score`
  - `repair_required`
  - monotony-related promotion conditions

allowed touched files:
- primary:
  - C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
  - C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py
- secondary only if integration proof is needed:
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- docs note:
  - C:\tetie\notecode\docs\separate_window_sentence_final_monotony_quality_guard_triage_note_2026-04-17.md

do not touch:
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
- C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
- C:\tetie\notecode\note\natural_blog_core.py
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\note_writer_app.py
- AGENTS / WORKLOG / current planning package docs

primary question to answer:
- explanatory short case で `ending_bucket_monotony` soft warning と `flagged_spans` は立つのに、
  current `repair_trigger_score` policy が `0.58` に届かず `repair_required=false` のままになるのは妥当か

今回やること:
1. `quality_guard.py` の current trigger construction を読む
   - base score
   - article-type / symptom-specific promotions
   - company intro monotony promotion
   - rhythm flatness cluster promotion
   - sentence integrity promotion
2. explanatory short monotony-only case が current policy 上どこにも乗っていないのか確認する
3. safe candidate があるなら 1 つだけ選ぶ
   - candidate A:
     - explanatory short monotony-only dedicated promotion
   - candidate B:
     - monotony-only + patch-path-candidate style composite promotion
   - candidate C:
     - no code diff
     - current policy keep with explicit rationale
4. candidate を 1 file owner で実装または triage note に落とす
5. mixed issue と company intro guard を壊していないことを確認する

good change shape:
- explanatory short monotony-only case に限定した narrow promotion
- `ending_bucket_max_run` と `ending_bucket_monotony_score` の両方を見る
- `single-pass + optional single repair 1回` の内側で説明できる
- `repair_required` へ届く条件を雑に広げない
- mixed issue や unrelated article types へ波及しない

bad change shape:
- global threshold を単純に下げる
- all article types へ monotony promotion を広げる
- company intro guard を流用して explanatory へ雑に広げる
- prompt accretion / formatter / route default へ逃げる
- deepresearch を理由に giant rewrite を始める

do not:
- deepresearch prompt を作らない
- `reference realization policy` を今回の main line に戻さない
- fixed routing table を足さない
- hidden reviser accretion を入れない
- `pipeline.py` 側の acceptance lane を再度いじらない
- `prompt_builder.py` で表面調整しない

focused tests to inspect first:
- `test_evaluate_quality_guard_promotes_repair_for_short_rhythm_flatness_cluster`
- `test_evaluate_quality_guard_promotes_repair_for_company_intro_ending_bucket_monotony`
- `test_evaluate_quality_guard_promotes_repair_for_sentence_integrity_warning`
- `test_evaluate_quality_guard_promotes_repair_for_single_sentence_paragraph_excess`
- any new test you add must be explanatory short + monotony-only + repair_required expectation

test execution order:
1. owner-local focused run
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -k "short_rhythm_flatness_cluster or company_intro_ending_bucket_monotony or sentence_integrity_warning or single_sentence_paragraph_excess or explanatory" -q`
2. owner-local full file if step 1 passes
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
3. neighbor check if code diff landed
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
4. shared checks only if real code changed
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "not st08b4_industry_analysis_title_and_lead_do_not_echo_prompt" -q`

pass condition:
- explanatory short monotony-only case を current trigger policy で説明できる
- safe なら `quality_guard.py` 1 owner の narrow diff で `repair_required` promotion を入れられる
- company intro monotony promotion と mixed issue guard を壊さない
- current route default / planning default / source-of-truth を変えない

stop and report instead of coding if:
- explanatory monotony-only case の条件が live artifact から再現不能
- safe rule に閉じず global threshold 調整しか残らない
- `quality_guard.py` 単独で説明できない
- second production owner が必要になる
- same phase で 3 回失敗した

recommended outcomes:
- outcome A:
  - `quality_guard.py` owner だけで narrow fix
  - next prompt は live re-validation
- outcome B:
  - no code diff
  - current policy keep の理由と reopen boundary を docs に残す
  - next prompt は deepresearch ではなく management re-triage

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. touched files
4. explanatory short monotony-only case の current trigger read
5. `repair_required=false` になる具体条件
6. `quality_guard.py` owner で直したか、直さなかったか
7. 直した場合は changed conditions と new focused test
8. company intro promotion と mixed issue guard を壊していないこと
9. tests の結果
10. AGENTS / WORKLOG / current package docs を更新していないこと
11. 次が live re-validation prompt か、management re-triage か
```
