# separate window sentence final monotony visible smoke after rollback note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の rollback 後 visible smoke validation note である
- source-of-truth update ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 今回の実施範囲
- touched files
- visible smoke cases
- case ごとの visible summary
- case ごとの secondary telemetry summary
- followup 時点との比較
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
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_prompt_builder_constraint_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_actual_repair_prompt_triage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_followup_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_rollback_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_visible_smoke_after_rollback_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_followup_20260417-195828\summary.json`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_followup_20260417-195828\case_a1_latest_adaptive_explanatory.txt`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_followup_20260417-195828\case_a2_saved_adaptive_explanatory.txt`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_followup_20260417-195828\case_b_company_intro_guard.txt`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
- `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\current_mainline_ui_matrix.py`

## 今回の実施範囲

- rollback 後 current branch state で representative live generation を 3 case 実施した
- 実行経路は current success path に固定した
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- 主判定は telemetry ではなく generated visible text の目視に置いた
- production code / tests / AGENTS / WORKLOG / current package docs は更新していない

## Touched Files

- generated logs:
  - `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json`
  - `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\case_v1_latest_adaptive_explanatory.json`
  - `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\case_v1_latest_adaptive_explanatory.txt`
  - `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\case_v2_saved_adaptive_explanatory.json`
  - `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\case_v2_saved_adaptive_explanatory.txt`
  - `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\case_v3_company_intro_guard.json`
  - `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\case_v3_company_intro_guard.txt`
- docs note:
  - `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md`

## Visible Smoke Cases

- case V1:
  - latest adaptive explanatory baseline rerun
  - source:
    - `C:\tetie\notecode\logs\latest_generation_output.json`
- case V2:
  - saved adaptive explanatory replay
  - source:
    - `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
- case V3:
  - branding / company_introduction mixed issue guard
  - source:
    - `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
    - `rerun`

## Case ごとの Visible Summary

### Case V1 latest adaptive explanatory baseline rerun

- visible read:
  - followup 時点よりはやや持ち直した
  - lead は baseline と同じで、followup の broad rewrite 感は少し弱まった
  - ただし title / hashtags / heading flow は still drift している
  - `第二に、目標と予算に合わせて。戦略立案から実行まで...` のような patch 感のあるつなぎが残る
  - `noteで実務の判断材料として見るなら` の一文段落も浮いており、explanatory main candidate とまでは読めない

### Case V2 saved adaptive explanatory replay

- visible read:
  - followup 時点よりは改善
  - followup にあった extra closing heading は消え、4 heading に戻った
  - lead は baseline 維持だが、title / hashtags / heading wording は still drift している
  - 本文は読めるが、一文段落が混ざり、`説明カード調を薄くした broad rewrite` の域を出ていない
  - explanatory fallback smoke としては成立しても、main candidate として keep できる visible quality ではない

### Case V3 company intro mixed issue guard

- visible read:
  - followup 時点よりは改善
  - title と lead の入りは followup より current business 寄りに戻った
  - ただし first heading が `130年余りの歩み...` で始まり、body も history-first へ引かれている
  - baseline の `何をしている会社なのか` から入る line は戻っていない
  - broad rewrite 感は followup より弱いが、company intro の current-business-first keep line を保てているとは言えない

## Case ごとの Secondary Telemetry Summary

### Case V1

- `repair_entry`
  - `repair_required = true`
  - `repair_trigger_score = 0.58`
  - `ending_bucket_max_run = 9`
  - `ending_bucket_monotony_score = 0.2308`
  - `flagged_issue_types = ["heading_reanchor", "ending_bucket_monotony"]`
  - `patch_path_candidate = true`
- `repair_call`
  - `patch_path_used = true`
  - `repair_applied = false`
  - `scope_acceptance_path = null`
  - `scope_rejection_reason = flagged_scope_drift`
  - `acceptance_rejection_reason = null`
  - `ending_monotony_improved = true`
- acceptance read:
  - `title_same = false`
  - `lead_same = true`
  - `hashtags_same = false`
  - `heading_sequence_changed = true`

### Case V2

- `repair_entry`
  - `repair_required = true`
  - `repair_trigger_score = 0.8`
  - `ending_bucket_max_run = 21`
  - `ending_bucket_monotony_score = 0.525`
  - `flagged_issue_types = ["heading_reanchor", "ending_bucket_monotony"]`
  - `patch_path_candidate = true`
- `repair_call`
  - `patch_path_used = true`
  - `repair_applied = false`
  - `scope_acceptance_path = null`
  - `scope_rejection_reason = flagged_scope_drift`
  - `acceptance_rejection_reason = null`
  - `ending_monotony_improved = true`
- acceptance read:
  - `title_same = false`
  - `lead_same = true`
  - `hashtags_same = false`
  - `heading_sequence_changed = true`

### Case V3

- `repair_entry`
  - `repair_required = true`
  - `repair_trigger_score = 0.6`
  - `ending_bucket_max_run = 16`
  - `ending_bucket_monotony_score = 0.5714`
  - `flagged_issue_types = ["heading_reanchor", "ending_bucket_monotony"]`
  - `patch_path_candidate = true`
- `repair_call`
  - `patch_path_used = true`
  - `repair_applied = false`
  - `scope_acceptance_path = null`
  - `scope_rejection_reason = flagged_scope_drift`
  - `acceptance_rejection_reason = null`
  - `ending_monotony_improved = true`
- acceptance read:
  - `title_same = false`
  - `lead_same = false`
  - `hashtags_same = false`
  - `heading_sequence_changed = true`

## Followup 時点との比較

- overall:
  - `改善`
- exact read:
  - rollback 後の current branch は followup 時点より visible 悪化を少し止めた
  - V1 は lead 復帰で改善、V2 は extra closing 消失で改善、V3 は title / lead の入りだけは改善した
  - ただし 3 case とも `title / hashtags / heading flow drift` は止まっていない
  - V3 の history-first drift も residual として明確に残る
- therefore:
  - `followup よりは改善`
  - `current main candidate としては未回復`

## Judgment

- explanatory cases:
  - main candidate としては `読めない`
  - V1 / V2 とも readable ではあるが、local repair の成果として keep できる visible state に届いていない
- company intro case:
  - `current-business-first` は `保てていない`
  - followup よりは戻ったが、先頭見出しと本文運びは still history-first 寄り
- verdict:
  - `VISIBLE_STILL_BAD`

### Why Not `VISIBLE_OK_AFTER_ROLLBACK`

- followup 比で改善はあるが、`glaring drift stopped` とまでは言えない
- 3 case とも `scope_acceptance_path` は未出力で、`repair_applied = false` のまま
- V1 / V2 は title / hashtags / heading sequence drift が残った
- V3 は history-first drift が visible に残り、guard read として still unsafe

### Exact Read

- rollback は `followup diff の visible worsening` を少し軽くした
- しかし `single repair line が visible に main candidate を作れるか` という問いにはまだ `no`
- current state は `keep 判定` ではなく `line freeze or management retriage` 側の読みになる

## Next Step

- next prompt:
  - `management retriage prompt`
- reason:
  - rollback 後でも explanatory main candidate は作れていない
  - company intro guard も current-business-first keep を言い切れない
  - これ以上 narrow live/triage を重ねる前に、この line を freeze するか management judgment を取り直すほうが筋

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
