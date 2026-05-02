# separate window sentence final monotony live revalidation after adaptive note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の adaptive reopen 後 live re-validation note である
- current source-of-truth は更新しない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- validation setup
- case A1 latest adaptive explanatory rerun
- case A2 saved adaptive explanatory replay
- case B company intro mixed-issue guard
- scope_acceptance_path summary
- judgment
- next step
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
- `C:\tetie\notecode\docs\separate_window_instruction_window_relocation_prompt_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_instruction_first_request_sentence_final_monotony_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_quality_guard_triage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_target_boundary_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_adaptive_quality_guard_followup_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_adaptive_reopen_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_quality_guard_20260417-170631\summary.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py`

## 実施範囲

- adaptive explanatory monotony-only promotion 追加後の live rerun だけを実施した
- 実行経路は current success path に固定した
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- validation cases は prompt 指定どおり A1 / A2 / B の 3 本に閉じた
- production code edit / test edit は行っていない
- touched files は generated logs とこの docs note のみ

## Validation Setup

- generated artifact root:
  - `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_adaptive_reopen_20260417-174409\`
- root summary:
  - `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_adaptive_reopen_20260417-174409\summary.json`
- preflight:
  - `run_live_preflight(LLMClient())`
  - `passed = true`
  - `selected_model = gpt-5.4-mini`
- validation cases:
  - case A1:
    - `C:\tetie\notecode\logs\latest_generation_output.json`
  - case A2:
    - `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
  - case B:
    - `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
    - `rerun` section

## Case A1 Latest Adaptive Explanatory Rerun

### Visible Summary

- visible text は explanatory として自然に読める
- title / lead / hashtags / heading flow は崩れていない
- 同じ丁寧文が極端に塊で続く感じは強くない
- patch 的な継ぎはぎ感も目立たない
- ただし
  - `ここで重要なのは、支援の範囲が広いこと自体ではありません。`
  - `とくに、企業ごとに課題の形が違う場面では、決まった型をそのまま当てはめるより、状況を見ながら伴走できるかどうかが重要です。`
  の周辺には still-flat な説明リズムが残る

### `repair_entry` Summary

- `repair_required = true`
- `repair_trigger_score = 0.62`
- `ending_bucket_max_run = 10`
- `ending_bucket_monotony_score = 0.2778`
- `flagged_issue_types = ["ending_bucket_monotony"]`
- `patch_path_candidate = true`
- `skip_reason = ""`

### `repair_call` Summary

- `patch_path_used = true`
- `repair_applied = false`
- `ending_monotony_improved = true`
- `local_monotony_scope_preserved = false`
- `effective_scope_preserved = false`
- `scope_rejection_reason = flagged_scope_drift`
- `scope_acceptance_path = null`

### Read

- adaptive reopen により upstream trigger までは接続した
- ただし `repair_applied = true` と `scope_acceptance_path = local_monotony_scope` には届いていない
- したがって A1 は keep rule 達成ではなく、`repair_required is true but repair_applied まで届かない` という needs-more-work rule の形に入っている

## Case A2 Saved Adaptive Explanatory Replay

### Visible Summary

- visible text は読みやすく、patch 的な継ぎはぎ感はない
- mild な丁寧文終止の似通いは残るが、A1 よりは弱い
- title / lead / heading flow の崩れは見えていない

### `repair_entry` Summary

- `repair_required = false`
- `repair_trigger_score = 0.3261`
- `ending_bucket_max_run = 9`
- `ending_bucket_monotony_score = 0.2308`
- `flagged_issue_types = ["ending_bucket_monotony"]`
- `patch_path_candidate = true`
- `skip_reason = repair_not_required`

### `repair_call` Summary

- `repair_call = {}`
- `patch_path_used` は未発生
- `repair_applied = false`
- `scope_acceptance_path = null`
- `scope_rejection_reason = null`

### Read

- A2 は adaptive reopen 後も gate 未満に止まった
- visible quality は悪化していないが、A1 の downstream acceptance 詰まりを補完する keep evidence にもなっていない

## Case B Company Intro Mixed-Issue Guard

### Visible Summary

- company intro としては読める
- broad rewrite の継ぎはぎ感は強くない
- ただし first heading が `130年余りの歩みを土台に、時代に合わせて進化してきた会社` で history-first 寄りに寄っている
- そのため `current-business-first keep line` を明確に守れたとは言いにくい

### `repair_entry` Summary

- `repair_required = true`
- `repair_trigger_score = 0.6`
- `ending_bucket_max_run = 7`
- `ending_bucket_monotony_score = 0.2333`
- `flagged_issue_types = ["shadow_section_drift", "ending_bucket_monotony"]`
- `patch_path_candidate = true`
- `skip_reason = ""`

### `repair_call` Summary

- `patch_path_used = true`
- `repair_applied = false`
- `controlled_realization_drift_headings = ["130年余りの歩みを土台に、時代に合わせて進化してきた会社"]`
- `local_monotony_scope_preserved = false`
- `effective_scope_preserved = false`
- `scope_rejection_reason = flagged_scope_drift`
- `scope_acceptance_path = null`

### Read

- mixed issue case に `local_monotony_scope` が accepted された形跡はなく、scope policy としての guard は保たれている
- 一方で visible output 側では history-first drift が残っているため、guard を完全に keep と言い切れる状態ではない

## `scope_acceptance_path` Summary

- case A1:
  - not emitted
- case A2:
  - not emitted
- case B:
  - not emitted
- 今回の live rerun では `scope_acceptance_path = local_monotony_scope` は 1 本も確認できなかった

## Judgment

- verdict:
  - `NEEDS_MORE_WORK`

### Why Not `KEEP`

- minimum keep rule の主条件だった
  - `repair_required = true`
  - `patch_path_used = true`
  - `repair_applied = true`
  - `scope_acceptance_path = local_monotony_scope`
  - visible monotony improvement without drift
  を A1 / A2 のどちらでも満たしていない
- A1 は upstream trigger までは接続したが、downstream acceptance lane で `flagged_scope_drift` に止められている
- B でも mixed issue 誤適用はないが、current-business-first keep line を visible に十分守れていない

### Why Not `ROLLBACK`

- A1 では `repair_required = true` かつ `patch_path_used = true` まで進んでおり、prompt の rollback rule で想定された
  - `A1 / A2 とも adaptive reopen 後でも repair_required = false`
  の形ではなくなった
- A1 / A2 の visible text は patch 的な継ぎはぎで悪化していない
- mixed issue case で `local_monotony_scope` を誤 accept した形跡もない

### Exact Read

- adaptive reopen は upstream mismatch を一段前進させた
- 現在の blocker は `quality_guard.py` ではなく、A1 で patch path 実行後も `scope_rejection_reason = flagged_scope_drift` になる downstream acceptance 境界に移っている
- よって結論は rollback ではなく、pipeline-side triage を要する `NEEDS_MORE_WORK` である

## Next Step

- 次は source-of-truth update prompt ではない
- 次は follow-up triage prompt が必要
- 問いは narrow に次へ閉じるべき
  - A1 で `repair_required = true` と `patch_path_used = true` まで届いたのに、なぜ `scope_acceptance_path = local_monotony_scope` が出ず `flagged_scope_drift` で reject されるのか
  - owner は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` の acceptance boundary 読み直しを先に置くのが妥当
- current evidence だけでは keep も source-of-truth update も出せない

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
