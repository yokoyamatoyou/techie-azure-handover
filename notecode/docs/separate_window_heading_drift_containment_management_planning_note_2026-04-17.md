# separate window heading drift containment management planning note 2026-04-17

## Position

- この文書は `HEADING_DRIFT_CONTAINMENT_FIRST` line の management planning note である
- current source-of-truth update ではない
- implementation prompt ではない
- deepresearch prompt ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- inherited local failure pattern の短い要約
- candidate 3 つの比較
- conclusion
- first owner と narrow hypothesis
- why this owner before others
- what this phase will not touch
- rollback boundary
- なぜ `quality_guard.py` first ではないか
- なぜ repair acceptance reopen ではないか
- なぜ `sentence-final monotony` continuation ではないか
- next prompt
- non-updates

## 読んだ参照ルールファイル

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_after_visible_smoke_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_targeted_deepresearch_redirect_after_sentence_final_stop_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_compare_result_reference_realization_policy_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_containment_management_planning_2026-04-17.md`

## 実施範囲

- deepresearch reflection と local docs / logs / code reference を読み、`HEADING_DRIFT_CONTAINMENT_FIRST` を next redirect line として本当に開くべきかを narrow に planning した
- current question を
  - first owner を 1 file に閉じられるか
  - hypothesis を upstream drafting / containment design に閉じられるか
  - next prompt type を implementation ではなく owner-local triage で止めるべきか
  に限定した
- production code / tests / AGENTS / WORKLOG / current package docs の更新には進んでいない

## inherited local failure pattern の短い要約

- rollback 後 representative 3 case すべてで `flagged_issue_types = ["heading_reanchor", "ending_bucket_monotony"]` が残った
- 3 case すべてで `ending_monotony_improved = true` だが、`repair_applied = false`、`scope_acceptance_path = null`、`scope_rejection_reason = flagged_scope_drift` のままだった
- `latest_generation_output.json` でも `writer_of_record = simple_note_pipeline`、`route_branch = single_pass_default`、`section_path_used = false`、`primary_generation_owner = simple_note_pipeline`、`primary_generation_mode = single_pass` であり、visible drift は repair 適用後ではなく single-pass 初稿側で残っている
- visible main failure は sentence-final variation 自体ではなく
  - title drift
  - lead drift
  - heading wording / heading sequence drift
  - company intro first heading の history-first reanchor
  である

## candidate 3 つの比較

### 1. `PIPELINE_DRAFT_CONTAINMENT_OWNER`

- good:
  - `pipeline.py` は `_compact_plan_safe_scope()`、flagged span 生成、repair dispatch、scope acceptance を持っており、upstream drafting と downstream containment の境界 owner ではある
  - explanatory short/adaptive では compact-plan 入口に近い
- limit:
  - current failure は `repair_applied = false` のまま残っており、acceptance や patch-path reopen を first remedy にすると論点が downstream に寄る
  - blank `company_introduction` の現行 keep line は `prompt_builder.py` 側で出しており、pipeline first は compact-plan scaffold / dispatch boundary の reopen に近づきやすい
  - first step としては `upstream drafting` と `repair dispatch boundary` を同時に抱えやすく、phase-local narrowness が落ちる
- rank:
  - `second`

### 2. `PROMPT_BUILDER_FRAME_CONTAINMENT_OWNER`

- good:
  - `prompt_builder.py` は title / lead / structure / heading progress / company-intro current-first brief の現行 owner である
  - blank `company_introduction` の current-business-first keep line もこの file から出ている
  - `prompt_builder.py` では company-intro blank prompt に current-first line を入れている一方、initial generation では `SECTION_SHADOW` を `semantic_key != "company_introduction"` 条件で外しており、article frame containment が薄いまま残っている
  - 3 case とも `repair_applied = false` なので、first draft の title / lead / first heading / first-section anchor を狭く強める owner として筋が通る
  - `quality_guard` や acceptance threshold を触らず、`single-pass + optional single repair 1回` baseline を壊さずに進められる
- limit:
  - compact-plan plan 自体の drift は後順位課題として残る
  - paragraph seam residual はこの phase の外に残る
- rank:
  - `first`

### 3. `REPLAN_BEFORE_OWNER`

- good:
  - redirect line 自体をさらに docs planning へ送る安全策ではある
- limit:
  - code read まで含めると owner は 1 file に閉じられる
  - `prompt_builder.py` で current-business-first frame と generation frame omission が同居しており、missing planning artifact がない
  - ここで replan に戻すと judgment を先送りするだけで、owner-local next step が曖昧に残る
- rank:
  - `third`

## Conclusion

- conclusion:
  - `PROMPT_BUILDER_FRAME_CONTAINMENT_OWNER`

## first owner と narrow hypothesis

- first owner file:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- narrow hypothesis:
  - prompt_builder.py で title / lead / first heading / first-section anchor を article-frame contract として generation prompt に明示的に固定すれば、short/adaptive explanatory と blank company intro の heading drift を repair acceptance reopen なしで initial draft 側から containment できる。

## why this owner before others

- `summary.json` の representative 3 case はすべて `repair_applied = false` で終わっており、visible drift は repair 採択後ではなく初稿の frame 側で残っている
- `prompt_builder.py` は
  - company-intro current-first brief
  - structure / heading progress
  - title / lead intent
  - `SECTION_SHADOW` / `SEMANTIC_LEDGER`
  の emission owner であり、article frame を upstream drafting に閉じて扱える
- company intro では `current-business-first keep line` が同 file にあり、しかも generation 側で company-intro `SECTION_SHADOW` を省いているため、「現行 keep line を強める」 narrow step に閉じられる
- pipeline first にすると
  - compact-plan scaffold reopen
  - repair dispatch / acceptance boundary reopen
  のどちらかへ寄りやすく、current prompt が求める `repair acceptance reopen ではなく upstream drafting or containment design` から外れやすい

## what this phase will not touch

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` の patch-path acceptance / scope threshold
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py` の trigger threshold / issue classification
- route default
  - `grounded generic default`
- planning default
  - `opt-in only`
- `single-pass + optional single repair 1回` baseline
- formatter-only line
- `reference realization policy`
- discourse / paragraph seam line
- AGENTS / WORKLOG / current package docs

## rollback boundary

- rollback boundary は `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` の generation / repair prompt emission diff のみとする
- `pipeline.py` の compact-plan gating、patch dispatch、acceptance threshold には触れない
- `quality_guard.py` の trigger / telemetry には触れない
- current runtime mainline
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  は維持する

## なぜ `quality_guard.py` first ではないか

- `quality_guard.py` は `heading_reanchor` と `ending_bucket_monotony` を測り、`repair_trigger_score` と `repair_required` を立てる detect / trigger owner である
- しかし current failure では trigger 自体は立っており、3 case とも `patch_path_used = true` まで進んでいる
- それでも `repair_applied = false` で終わっているため、first concern は「検知不足」ではなく「初稿 frame が drift したまま repair を呼んでいること」である
- よって `quality_guard.py` first は current failure を downstream の signal 調整に誤読する

## なぜ repair acceptance reopen ではないか

- 3 case とも `scope_acceptance_path = null`、`scope_rejection_reason = flagged_scope_drift` であり、repair candidate は scope drift 扱いで reject されている
- ここで acceptance を reopen すると、「visible drift を含む repair output を通すか」の話になり、current prompt の強い bias と逆行する
- 現状必要なのは reject された repair を通すことではなく、reject 前の初稿 title / lead / heading / first-section anchor を drift しにくくすること
- したがって first remedy は acceptance threshold ではなく upstream frame containment である

## なぜ `sentence-final monotony` continuation ではないか

- `ending_monotony_improved = true` が出ても、visible main failure は
  - title drift
  - heading wording / sequence drift
  - company intro history-first reanchor
  に残っている
- separate note でも `sentence-final pattern monotony cap + single repair` line は `STOP_AND_REDIRECT` で止まっている
- current redirect の目的は sentence-final variation を続けることではなく、その payoff を吸っている upstream frame drift を先に containment することにある

## Next Prompt

- next prompt type:
  - `owner-local triage prompt`
- exact read:
  - 次は implementation prompt ではなく、`prompt_builder.py` の中で
    - company-intro blank prompt の current-first lines
    - title / lead / heading progress contract
    - company-intro generation 時に省かれている frame lines
    のどこを first lever にするかを narrow に切る owner-local triage prompt が妥当
- why not immediate implementation prompt:
  - same file 内に
    - HARD_CONTRACT
    - STRUCTURE
    - title / lead intent
    - section shadow omission
    の複数 lever があり、1 diff に絞る前の owner-local triage が phase discipline に合う

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
