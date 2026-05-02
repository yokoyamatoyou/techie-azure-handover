# separate window execution prompt heading drift containment management planning 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_after_visible_smoke_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_targeted_deepresearch_redirect_after_sentence_final_stop_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_compare_result_reference_realization_policy_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py

今回の依頼種別:
- management planning prompt
- `HEADING_DRIFT_CONTAINMENT_FIRST` line の phase-local planning
- source-of-truth update ではない
- implementation prompt ではない
- deepresearch prompt ではない

今回の実施範囲:
- deepresearch と local evidence を踏まえて、`HEADING_DRIFT_CONTAINMENT_FIRST` を次の redirect line として本当に開くべきかを narrow に planning する
- docs / logs / code reference 読みだけで first owner candidate と narrow hypothesis を決める
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない
- docs note 1 本だけを作る

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
- module accretion 禁止
- prompt accretion 禁止

already decided and must inherit:
- `sentence-final pattern monotony cap + single repair` line は `STOP_AND_REDIRECT`
- targeted deepresearch の結論は `HEADING_DRIFT_CONTAINMENT_FIRST`
- ただしこれは実装許可ではなく、next planning line の優先順位 judgment である
- `DISCOURSE_PARAGRAPH_SEAM_FIRST` は promising だが second
- `reference realization policy first` は戻さない

local failure pattern to inherit:
- rollback 後 representative 3 case すべてで
  - `flagged_issue_types = ["heading_reanchor", "ending_bucket_monotony"]`
  - `repair_applied = false`
  - `scope_acceptance_path = null`
  - `scope_rejection_reason = flagged_scope_drift`
  が残った
- visible main failure は
  - title drift
  - lead drift
  - heading wording / heading sequence drift
  - company intro first heading の history-first reanchor
  であり、sentence-final variation 自体ではない

core planning question:
- `HEADING_DRIFT_CONTAINMENT_FIRST` を次に開くとして、
  current package を壊さず `1 phase = 1 narrow hypothesis = 1 owner scope` に閉じる first owner はどこか
- また、その hypothesis は
  - repair acceptance reopen ではなく
  - upstream drafting or containment design
  に本当に閉じられるか

what to decide:
1. `PIPELINE_DRAFT_CONTAINMENT_OWNER`
   - `simple_note_pipeline/pipeline.py`
   - title / lead / heading / first-section anchor の containment を upstream drafting / repair dispatch 境界で扱う
2. `PROMPT_BUILDER_FRAME_CONTAINMENT_OWNER`
   - `simple_note_pipeline/prompt_builder.py`
   - article frame contract の emission / framing を first owner として扱う
3. `REPLAN_BEFORE_OWNER`
   - 現時点では owner を 1 file に閉じられず、別の docs planning が先

strong bias:
- repair acceptance threshold reopen を first step にしない
- `quality_guard.py` を first owner にしない
- `sentence-final monotony` continuation proposalに戻らない
- `reference realization policy first` に戻らない
- discourse / paragraph seam を first owner にしない
- fixed routing table / planning default / formatter-only / prompt-only / hidden reviser を reopen しない

what to inspect explicitly:
- `pipeline.py`
  - flagged scope / local monotony scope / repair dispatch / draft rebuild / heading preservation boundary
- `prompt_builder.py`
  - title / lead / body / section shadow / heading-related framing and contract emission
- `quality_guard.py`
  - trigger classification は読むだけ
  - first owner にすべきかどうかを否定する材料としてだけ使う
- logs / notes
  - actual visible drift が first generated draft 由来か
  - repair-side rewrite / containment failure 由来か
  - mixed issue の扱いがどこで広がっているか

planning output must include:
- first owner candidate
- narrow hypothesis 1 本
- why this owner before others
- what this phase will not touch
- rollback boundary
- next prompt type

do not do:
- implementation proposalを長く書く
- code edit に進む
- test edit に進む
- source-of-truth update を始める
- giant rewrite を前提にする
- paragraph seam line を first owner に昇格させる
- acceptance threshold を first remedy として提案する

preferred output shape:
- management planning note 1本
- conclusion is exactly one of:
  - `PIPELINE_DRAFT_CONTAINMENT_OWNER`
  - `PROMPT_BUILDER_FRAME_CONTAINMENT_OWNER`
  - `REPLAN_BEFORE_OWNER`
- if not `REPLAN_BEFORE_OWNER`:
  - first owner file を 1 つに固定する
  - next hypothesis を 1 文で固定する
  - next prompt type を `implementation prompt` か `owner-local triage prompt` のどちらかに固定する
- if `REPLAN_BEFORE_OWNER`:
  - why owner cannot yet be narrowed
  - what missing planning artifact is needed

recommended output file:
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_management_planning_note_2026-04-17.md

stopping conditions:
- owner を 1 file に閉じられない
- route / planning / formatter / reference realization policy に論点が逸れた
- implementation diff を書きたくなった
- conclusion を 2 つ以上にぼかしたくなった

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. inherited local failure pattern の短い要約
4. candidate 3 つの比較
5. `PIPELINE_DRAFT_CONTAINMENT_OWNER / PROMPT_BUILDER_FRAME_CONTAINMENT_OWNER / REPLAN_BEFORE_OWNER` の結論
6. なぜ `quality_guard.py` first ではないか
7. なぜ repair acceptance reopen ではないか
8. なぜ `sentence-final monotony` continuation ではないか
9. 次が implementation prompt か owner-local triage prompt か
10. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
