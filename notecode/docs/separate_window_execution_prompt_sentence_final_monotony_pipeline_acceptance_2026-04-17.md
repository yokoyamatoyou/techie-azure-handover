# separate window execution prompt sentence final monotony pipeline acceptance 2026-04-17

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

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の first implementation を行う
- first production owner は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- target は `patch_path_used = true` まで進んだ monotony repair が acceptance / scope rejection で落ちる current blocker を narrow に詰めること
- `single-pass + optional single repair 1回` は維持する
- route default / planning default / current source-of-truth は変更しない
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

triage verdict:
- `GO_TO_IMPLEMENT`
- first owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- second owner reserve only:
  - `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- live-like blocker:
  - latest artifact `2026-04-15 00:25:07`
  - attempt id `gen-4692e32c`
  - `writer_of_record = simple_note_pipeline`
  - `route_branch = single_pass_default`
  - `ending_bucket_max_run = 27`
  - `ending_bucket_monotony_score = 0.675`
  - `repair_trigger_score = 0.62`
  - `flagged_issue_types = ["ending_bucket_monotony"]`
  - `patch_path_used = true`
  - `repair_applied = false`
  - `scope_rejection_reason = flagged_scope_drift`
  - `runtime_reason_code = SYS_QUALITY_WARNINGS_UNRESOLVED`

目的:
- detector / telemetry / trigger ではなく、`pipeline.py` の repair acceptance / scope lane を narrow に直す
- `sentence-final monotony` repair が patch path 後に不必要に reject される current failure を 1 file owner で改善する
- `branding/company_introduction` 専用だった local monotony acceptance lane を、guard を壊さずに `sentence-final monotony` の narrow reusable lane として扱えるか検証する
- title / lead / hashtags / heading order / must-cover / prompt anchor / section focus を守ったまま repair を受理できることを目指す

narrow hypothesis:
- current failure は `sentence-final monotony` を検知できていないことではなく、`_run_optional_repair()` の acceptance 条件が `ending_bucket_monotony` の local patch を過剰に reject していることにある
- したがって first step は `quality_guard.py` の threshold を動かすことではなく、`pipeline.py` で local monotony scope / alignment / acceptance lane を narrow に再設計すること
- first target は `explanatory_article` を含む `single_pass_default` path だが、company intro 用 guard を壊さずに general monotony patch として閉じる

primary owner and likely touchpoints:
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `_run_optional_repair()`
  - `_repair_preserves_local_monotony_scope()`
  - `_repair_preserves_local_patch_scope()`
  - related acceptance / telemetry lines only when needed

touched files:
- required:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- allowed:
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- do not touch:
  - `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
  - `C:\tetie\notecode\note\natural_blog_core.py`
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\note_writer_app.py`
  - AGENTS / WORKLOG / current planning package docs

今回やること:
1. `pipeline.py` の current acceptance lane を読む
   - `scope_preserved`
   - `effective_scope_preserved`
   - `ending_monotony_guard_active`
   - `ending_monotony_improved`
   - `local_monotony_scope_preserved`
   - `scope_rejection_reason`
2. `ending_bucket_monotony` が検知され patch path まで進んだ case で、
   local scope が保たれるなら acceptance できる narrow condition を作る
3. `branding/company_introduction` 既存 guard は維持する
4. `explanatory_article` でも local monotony patch を受け入れられる focused test を追加する
5. company intro の既存 monotony guard / local scope guard が壊れていないことを確認する
6. telemetry は必要最小限だけ追加または調整する
   - payload を肥大化させない
   - rejection / acceptance の理由が読めることを優先する

do not:
- `article-type fixed routing table` を追加しない
- `planning / skeleton default` を再主張しない
- `reference realization policy` を今回の main line に戻さない
- `formatter-only surface polish` に流さない
- `input_contract only` で直そうとしない
- `prompt_builder.py` へ prompt accretion を足さない
- hidden reviser accretion を入れない
- giant rewrite を始めない
- scope rejection を雑に無効化しない
- flagged span 外まで広く rewrite する acceptance にしない
- title / lead / hashtags / headings の drift を許容しない

focused tests:
- existing focused targets:
  - `test_simple_note_pipeline_rejects_company_intro_repair_without_ending_monotony_improvement`
  - `test_local_monotony_scope_allows_small_multi_section_repair_without_heading_drift`
  - `test_local_monotony_scope_allows_company_intro_wide_surface_repair_when_sections_stay_close`
  - `test_local_monotony_scope_rejects_wide_repair_when_section_surface_drifts`
  - `test_local_patch_scope_allows_company_intro_repair_within_flagged_headings`
  - `test_simple_note_pipeline_rejects_patch_repair_that_rewrites_unflagged_section`
- add one new focused test for this line:
  - `explanatory_article` or equivalent live-like monotony case
  - `patch_path_used = true`
  - `flagged_issue_types` includes `ending_bucket_monotony`
  - local scope preserved
  - `repair_applied = true`
  - no title / lead / hashtags / heading drift

test execution order:
1. owner-local focused run
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "ending_monotony or local_monotony_scope or local_patch_scope or rewrites_unflagged_section" -q`
2. owner-local full file if step 1 passes
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
3. shared checks if code diff remains narrow and owner-local is green
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
   - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`

pass condition:
- `pipeline.py` 1 owner で diff が閉じる
- new focused test で `patch_path_used = true` かつ `repair_applied = true` を説明できる
- existing company intro monotony tests が維持される
- `scope_rejection_reason = flagged_scope_drift` の current failure を narrow acceptance logic で説明できる
- title / lead / hashtags / heading order / alignment guard を壊さない
- route default / planning default / source-of-truth を変更しない

stop conditions:
- `quality_guard.py` を first step で触らないと進めない
- `prompt_builder.py` の prompt accretion が必要になった
- second production owner が必要になった
- local scope guard を説明できないまま acceptance を緩めるしかなくなった
- fixed routing / formatter / reference realization line に論点が逸れた
- same phase で 3 回失敗した
- shared checks で current success path regression が出た

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. touched files
4. `pipeline.py` で変えた関数と narrow hypothesis
5. 新規または更新した focused test
6. owner-local tests と shared checks の実行結果
7. `patch_path_used = true` から `repair_applied = true` へ進めたかどうか
8. company intro の monotony guard が維持されたか
9. `quality_guard.py` を触らなかったこと
10. AGENTS / WORKLOG / current package docs を更新していないこと
11. 失敗した場合は、どの stop condition で止めたか
```
