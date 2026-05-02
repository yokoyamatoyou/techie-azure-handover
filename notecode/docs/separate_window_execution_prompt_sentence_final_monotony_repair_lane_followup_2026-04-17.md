# separate window execution prompt sentence final monotony repair lane followup 2026-04-17

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
- C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\summary.json

今回の依頼種別:
- follow-up triage / implementation prompt
- source-of-truth update ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の follow-up を行う
- focus は `live monotony case が current runtime で repair lane に入らない理由` の切り分け
- first owner は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `quality_guard.py` は reserve owner とし、first action では触らない
- current source-of-truth は更新しない
- AGENTS / WORKLOG / current package docs は更新しない

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

current finding to inherit:
- previous `pipeline.py` diff は focused tests では通った
- live validation verdict は `NEEDS_MORE_WORK`
- why not keep:
  - case A live で
    - `patch_path_used = true`
    - `repair_applied = true`
    - `scope_acceptance_path = local_monotony_scope`
    を確認できなかった
- why not rollback:
  - case B mixed issue で `local_monotony_scope` の誤適用 regression は見えていない
  - company intro guard は壊れていない

live validation で見えた事実:
- case A latest artifact rerun:
  - visible quality は baseline より改善
  - ただし `repair_call = {}`
  - `repair_applied = false`
  - `patch_path_refusal_reason = repair_call_unavailable`
  - `ending_bucket_max_run = 11`
  - `ending_bucket_monotony_score = 0.2558`
  - `repair_trigger_score = 0.4258`
- case A saved explanatory monotony rerun:
  - `repair_applied = false`
  - `repair_call = {}`
  - `ending_bucket_max_run = 26`
  - `ending_bucket_monotony_score = 0.5417`
  - `repair_trigger_score = 0.4556`
- case B company intro guard:
  - `patch_path_used = true`
  - `flagged_issue_types = ["shadow_section_drift", "ending_bucket_monotony"]`
  - `scope_rejection_reason = flagged_scope_drift`
  - `repair_applied = false`
  - `scope_acceptance_path` は出ていない

primary question:
- なぜ focused test では `patch_path_used = true -> repair_applied = true -> scope_acceptance_path = local_monotony_scope` が成立したのに、
  live monotony case では `repair_call_unavailable` になり repair lane に入らないのか

目的:
- `pipeline.py` owner だけで説明できる差分を先に詰める
- live case と focused test case の entry condition のずれを narrow に特定する
- ずれが `pipeline.py` 側で吸収可能なら実装する
- ずれが `quality_guard.py` の `repair_required` / trigger owner にあると分かった場合だけ、そこで止めて boundary note を返す

first owner and likely touchpoints:
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `generate()`
  - `_run_optional_repair()`
  - `patch_path_refusal_reason` / `repair_call` emission path
  - repair lane entry telemetry

reserve owner only if strictly needed:
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
  - `repair_required`
  - `repair_trigger_score`
  - `ending:bucket_monotony`
  - only after `pipeline.py` owner で explanation が閉じないと確認できた場合

今回やること:
1. live validation artifacts と focused test を比較する
2. live case で `repair_call_unavailable` になる具体条件を `pipeline.py` 側で特定する
   - `diagnostics["repair_required"]`
   - `flagged_spans`
   - `patch_path_refusal_reason`
   - `repair_call` emission
   - `_run_optional_repair()` の early return
3. focused test が直接 `_run_optional_repair()` を叩いていることによるギャップを明文化する
4. `pipeline.py` owner だけで詰められる narrow fix があるか判断する
5. ある場合のみ `pipeline.py` と `test_simple_note_pipeline.py` に閉じて実装する
6. ない場合は code diff を広げず、`quality_guard.py` reopen の boundary note を docs に残して停止する

allowed touched files:
- primary:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- docs note:
  - C:\tetie\notecode\docs\separate_window_sentence_final_monotony_repair_lane_followup_note_2026-04-17.md

do not touch:
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
- C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
- C:\tetie\notecode\note\natural_blog_core.py
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\note_writer_app.py
- AGENTS / WORKLOG / current planning package docs

implementation rules:
- `quality_guard.py` の threshold 調整を first step にしない
- `prompt_builder.py` の prompt accretion に逃げない
- fixed routing table を足さない
- hidden reviser accretion を入れない
- formatter-only polish に流れない
- giant rewrite をしない
- mixed issue に `local_monotony_scope` を広く通さない
- telemetry 追加は最小限にし、repair lane 未到達の理由が読めることを優先する

good next-step shapes inside `pipeline.py` only:
- `repair_required` false で `_run_optional_repair()` に入らないケースの refusal reason を明示する
- live monotony case と focused test case の差分を runtime telemetry で見えるようにする
- `repair_required` に届かないが monotony soft warning が残るケースを、pipeline owner だけで safe に扱える narrow fallback があるなら検討する
- ただし fallback は
  - `ending_bucket_monotony` 単独
  - heading / title / lead / hashtags drift なし
  - mixed issue 不可
  - rollback が 1 file に閉じる
  を満たす場合だけ

stop and report instead of coding if:
- live failure の主因が `quality_guard.py` owner だと分かった
- `repair_required` 判定に触れないと前進できない
- `pipeline.py` 単独では safe fallback を説明できない
- mixed issue guard を壊さずに直せる見込みがない
- second production owner が必要になる

focused checks:
- existing:
  - `test_simple_note_pipeline_repairs_explanatory_monotony_with_local_scope_acceptance`
  - `test_simple_note_pipeline_rejects_company_intro_repair_without_ending_monotony_improvement`
  - `test_local_monotony_scope_allows_small_multi_section_repair_without_heading_drift`
  - `test_local_monotony_scope_allows_company_intro_wide_surface_repair_when_sections_stay_close`
  - `test_local_monotony_scope_rejects_wide_repair_when_section_surface_drifts`
  - `test_local_patch_scope_allows_company_intro_repair_within_flagged_headings`
  - `test_simple_note_pipeline_rejects_patch_repair_that_rewrites_unflagged_section`
- add only if needed:
  - live-like case that proves `repair_call_unavailable` reason
  - or pipeline-local fallback gate for monotony-only warning path

test execution order:
1. owner-local focused run
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "explanatory_monotony or ending_monotony or local_monotony_scope or local_patch_scope or rewrites_unflagged_section" -q`
2. owner-local full file if step 1 passes
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
3. if code diff remains narrow and owner-local is green:
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
4. shared checks only if a real code change landed:
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "not st08b4_industry_analysis_title_and_lead_do_not_echo_prompt" -q`

pass condition:
- live monotony case が repair lane に入らない理由を説明できる
- その理由が `pipeline.py` owner だけで解消できるなら narrow diff で通る
- もしくは `quality_guard.py` reopen が必要な boundary を docs だけで明確にできる
- company intro mixed issue guard を壊さない
- route default / planning default / source-of-truth を変更しない

recommended outcomes:
- outcome A:
  - `pipeline.py` owner だけで narrow fix
  - focused tests pass
  - next prompt は live re-validation
- outcome B:
  - no code diff
  - `quality_guard.py` boundary note を作って停止
  - next prompt は `quality_guard.py` triage

停止条件:
- `quality_guard.py` を first action で触りたくなった
- `prompt_builder.py` や formatter に論点が逸れた
- live target case と focused case の差分が `pipeline.py` ではなく upstream diagnostics owner に閉じると判断できた
- same phase で 3 回失敗した

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. touched files
4. live case と focused test case の差分
5. `repair_call_unavailable` の具体理由
6. `pipeline.py` owner で直せたかどうか
7. code diff があるなら changed functions と focused tests
8. code diff がないなら `quality_guard.py` reopen が必要な boundary
9. company intro mixed issue guard を壊していないこと
10. AGENTS / WORKLOG / current package docs を更新していないこと
11. 次に必要なのが live re-validation prompt か `quality_guard.py` triage prompt か
```
