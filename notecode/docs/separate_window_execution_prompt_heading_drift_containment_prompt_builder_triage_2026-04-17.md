# separate window execution prompt heading drift containment prompt builder triage 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_targeted_deepresearch_redirect_after_sentence_final_stop_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_compare_result_reference_realization_policy_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_management_planning_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_containment_management_planning_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_after_visible_smoke_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の依頼種別:
- owner-local triage prompt
- source-of-truth update ではない
- implementation prompt ではない
- deepresearch prompt ではない

今回の実施範囲:
- `HEADING_DRIFT_CONTAINMENT_FIRST` line の first owner を `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` に固定し、initial draft 側の frame drift をどの prompt lever で最初に containment するべきかを narrow に triage する
- docs / logs / code reference 読みだけで判断する
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない
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

management conclusion to inherit:
- conclusion:
  - `PROMPT_BUILDER_FRAME_CONTAINMENT_OWNER`
- narrow hypothesis:
  - `prompt_builder.py` で title / lead / first heading / first-section anchor を article-frame contract として generation prompt に明示的に固定すれば、short/adaptive explanatory と blank company intro の heading drift を repair acceptance reopen なしで initial draft 側から containment できる
- next prompt type:
  - `owner-local triage prompt`

current exact failure read:
- representative 3 case すべてで
  - `flagged_issue_types = ["heading_reanchor", "ending_bucket_monotony"]`
  - `ending_monotony_improved = true`
  - `repair_applied = false`
  - `scope_acceptance_path = null`
  - `scope_rejection_reason = flagged_scope_drift`
- `latest_generation_output.json` でも
  - `writer_of_record = simple_note_pipeline`
  - `route_branch = single_pass_default`
  - `section_path_used = false`
  - `primary_generation_owner = simple_note_pipeline`
  - `primary_generation_mode = single_pass`
- visible main failure は repair 後ではなく initial draft 側の
  - title drift
  - lead drift
  - heading wording / heading sequence drift
  - company intro first heading の history-first reanchor
  にある

first triage question:
- `prompt_builder.py` のどの lever を最初に触ると、最小 diff で initial draft の frame drift containment に最も効くか

candidate levers to compare inside `prompt_builder.py`:
1. `TITLE_LEAD_HEADING_CONTRACT_FIRST`
   - title / lead / heading progress / first heading role の contract lines を generation prompt に狭く追加・強化する
2. `COMPANY_INTRO_FRAME_REUSE_FIRST`
   - blank company intro 用 current-business-first keep line / frame lines を initial generation 側にも再利用または再接続する
3. `SECTION_SHADOW_EMISSION_FIRST`
   - company-introduction で省かれている `SECTION_SHADOW` / related frame lines を initial generation prompt に戻すか narrow 再導入する
4. `STRUCTURE_ONLY_FIRST`
   - heading progress / section role / first-section anchor の構造 line だけを扱い、title / lead には触れない

what to decide:
- first lever を 1 つに絞る
- second lever は optional backlog として短く示す
- implementation prompt へ渡す narrow hypothesis を 1 本に閉じる

evaluation criteria:
- narrowness:
  - 1-file / 1-diff に閉じやすいか
- containment value:
  - title / lead / heading / first-section drift に効きやすいか
- accretion risk:
  - prompt 肥大を増やしすぎないか
- rollback clarity:
  - 失敗時に clean rollback できるか
- company intro relevance:
  - current-business-first reanchor failure に直接効くか
- explanatory relevance:
  - explanatory title / lead / heading drift にも効くか

strong constraints:
- `pipeline.py` の compact-plan scaffold / dispatch / acceptance を reopen しない
- `quality_guard.py` の trigger / issue classification を reopen しない
- repair line continuation に戻さない
- prompt 肥大で雑に囲わない
- 1 phase = 1 narrow hypothesis = 1 owner scope を守る

what this triage must inspect in code:
- `prompt_builder.py` のうち
  - title / lead intent emission
  - structure / heading progress emission
  - blank company intro current-business-first line
  - company-introduction generation で除外されている `SECTION_SHADOW` / frame-related lines
  - generation prompt assembly path
- ただし implementation には進まない

what not to do:
- code edit
- test edit
- live rerun
- new telemetry proposal
- formatter / route / planning policy discussion

good outcome:
- next owner-local implementation prompt が 1 lever に閉じる
- why that lever is first なのかが明確
- non-chosen levers は今やらない理由が短く整理される

bad outcome:
- 2 lever 以上を同時採用する
- `prompt_builder.py` と `pipeline.py` の両方 reopen を提案する
- title / lead / heading / company intro frame を全部一度に触る implementation を提案する

recommended output file:
- `C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_triage_note_2026-04-17.md`

stopping conditions:
- owner-local triage を超えて implementation したくなった
- code edit しないと判断できないと言いたくなった
- first lever を 1 つに絞れない

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. `prompt_builder.py` 内で見た candidate levers
4. first lever の結論
5. narrow hypothesis
6. second lever を今やらない理由
7. prompt accretion risk の評価
8. next prompt type が implementation prompt でよいか
9. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
