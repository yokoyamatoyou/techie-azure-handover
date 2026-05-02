# separate window sentence final monotony live revalidation note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の live re-validation note である
- current source-of-truth は更新しない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- validation setup
- case A1 latest explanatory monotony rerun
- case A2 saved explanatory monotony replay
- case B company intro mixed-issue guard
- scope_acceptance_path summary
- judgment
- next step

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
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_pipeline_acceptance_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_validation_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_validation_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_repair_lane_followup_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_repair_lane_followup_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_quality_guard_triage_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_quality_guard_triage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_quality_guard_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\summary.json`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py`

## 実施範囲

- `sentence-final pattern monotony cap + single repair` line の再 live validation だけを実施
- current branch state の current success path
  - `execute_current_mainline_generation()`
  - `note.newalgorithm_pipeline.pipeline.MinimalPipeline`
  - `note.simple_note_pipeline.pipeline.MinimalPipeline`
  を live rerun に使用
- production code edit / test edit は行っていない
- case C optional smoke guard は skip した
- touched files は generated logs とこの docs note のみ

## Validation Setup

- generated artifact root:
  - `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_quality_guard_20260417-170631\`
- root summary:
  - `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_quality_guard_20260417-170631\summary.json`
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
- per-case artifacts:
  - case A1:
    - `...\case_a1_latest_explanatory_monotony\baseline_summary.json`
    - `...\case_a1_latest_explanatory_monotony\baseline_visible.txt`
    - `...\case_a1_latest_explanatory_monotony\result.json`
    - `...\case_a1_latest_explanatory_monotony\visible.txt`
  - case A2:
    - `...\case_a2_saved_explanatory_monotony\baseline_summary.json`
    - `...\case_a2_saved_explanatory_monotony\baseline_visible.txt`
    - `...\case_a2_saved_explanatory_monotony\result.json`
    - `...\case_a2_saved_explanatory_monotony\visible.txt`
  - case B:
    - `...\case_b_company_intro_guard\baseline_summary.json`
    - `...\case_b_company_intro_guard\baseline_visible.txt`
    - `...\case_b_company_intro_guard\result.json`
    - `...\case_b_company_intro_guard\visible.txt`

## Case A1 Latest Explanatory Monotony Rerun

### Visible Summary

- source baseline visible text は `baseline_visible.txt` 上で `[BLOCKED_OUTPUT_REDACTED]` だったため、source 側は title / lead / telemetry だけ参照した
- rerun visible text は explanatory として自然に読める
- 同じ丁寧文が長く塊で続く感じは強くなく、patch 的な継ぎはぎ感もない
- title / lead / hashtags / heading flow は崩れていない

### `repair_entry` Summary

- source baseline:
  - source telemetry は `repair_call.patch_path_used = true`
  - `scope_rejection_reason = flagged_scope_drift`
  - `reason_code = SYS_QUALITY_WARNINGS_UNRESOLVED`
- rerun:
  - `repair_required = false`
  - `repair_trigger_score = 0.1944`
  - `ending_bucket_max_run = 8`
  - `ending_bucket_monotony_score = 0.1951`
  - `flagged_issue_types = ["ending_bucket_monotony"]`
  - `patch_path_candidate = true`
  - `skip_reason = repair_not_required`

### `repair_call` Summary

- source baseline:
  - `patch_path_used = true`
  - `flagged_issue_types = ["ending_bucket_monotony"]`
  - `scope_rejection_reason = flagged_scope_drift`
- rerun:
  - `repair_call = {}`
  - `repair_applied = false`
  - `patch_path_refusal_reason = repair_call_unavailable`

### Read

- target telemetry chain
  - `repair_required = true`
  - `patch_path_used = true`
  - `repair_applied = true`
  - `scope_acceptance_path = local_monotony_scope`
  は出ていない
- rerun 自体は読み味が改善しており、repair lane に入る前に first pass で軽くなったと読むほうが自然

## Case A2 Saved Explanatory Monotony Replay

### Visible Summary

- source baseline は explanatory monotony case として読めるが、丁寧文の連続と説明リズムの単調さが残る
- rerun visible text は A1 と同様に読みやすく、patch 的な継ぎはぎ感はない
- ただし monotony repair acceptance の live 証跡にはなっていない

### `repair_entry` Summary

- source baseline:
  - source telemetry は `repair_call.patch_path_used = true`
  - `scope_rejection_reason = flagged_scope_drift`
  - `flagged_issue_types = ["ending_bucket_monotony"]`
- rerun:
  - `repair_required = false`
  - `repair_trigger_score = 0.286`
  - `ending_bucket_max_run = 9`
  - `ending_bucket_monotony_score = 0.1957`
  - `flagged_issue_types = ["ending_bucket_monotony"]`
  - `patch_path_candidate = true`
  - `skip_reason = repair_not_required`

### `repair_call` Summary

- source baseline:
  - `patch_path_used = true`
  - `scope_rejection_reason = flagged_scope_drift`
- rerun:
  - `repair_call = {}`
  - `repair_applied = false`
  - `patch_path_refusal_reason = repair_call_unavailable`

### Read

- target telemetry chain は case A2 でも出ていない
- source baseline は patch path rejection まで進んでいたのに、current rerun は repair lane entry 前で止まっている
- visible text は悪化していないが、keep judgment に必要な live 接続確認には届かない

## Case B Company Intro Mixed-Issue Guard

### Visible Summary

- rerun visible text は broad rewrite の継ぎはぎ感はなく、company intro として読める
- mixed issue case なのに `local_monotony_scope` が誤適用された形跡はない
- ただし first heading が `130年余の歩み...` で history-first 寄りになっており、`current-business-first keep line` を強く維持したとは言いにくい

### `repair_entry` Summary

- rerun:
  - `repair_required = true`
  - `repair_trigger_score = 0.6`
  - `ending_bucket_max_run = 23`
  - `ending_bucket_monotony_score = 0.7667`
  - `flagged_issue_types = ["shadow_section_drift", "ending_bucket_monotony"]`
  - `patch_path_candidate = true`
  - `skip_reason = ""`

### `repair_call` Summary

- source baseline rerun section:
  - `repair_applied = true`
  - `patch_path_used = false`
  - mixed issue ではなかった
- current rerun:
  - `patch_path_used = true`
  - `repair_applied = false`
  - `scope_preserved = false`
  - `local_monotony_scope_preserved = false`
  - `local_patch_scope_preserved = false`
  - `effective_scope_preserved = false`
  - `scope_rejection_reason = flagged_scope_drift`

### Read

- mixed issue case で `local_monotony_scope` を誤適用していないので、guard は scope policy として維持されている
- 一方で visible output は keep line を十分には固定できておらず、quality line の final keep judgment を支える guard-side visible win までは言えない

## `scope_acceptance_path` Summary

- case A1:
  - not emitted
- case A2:
  - not emitted
- case B:
  - not emitted
- 今回 rerun では `scope_acceptance_path = local_monotony_scope` は 1 本も確認できていない

## Additional Boundary Found During Revalidation

- case A1 / A2 の current rerun result では
  - `pipeline_check.input_contract.length_mode = adaptive`
  が維持されていた
- 一方で explanatory monotony promotion は
  - `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
  - `_is_explanatory_short_ending_bucket_monotony_candidate()`
  - `738-760`
  で `length_mode == "short"` を要求している
- 実際の promotion floor 反映も
  - `quality_guard.py`
  - `828-855`
  に閉じており、A1/A2 は current runtime contract 上その branch に乗っていない
- `pipeline.py`
  - `1255-1284`
  の `repair_entry` telemetry と
  - `1952-1957`
  の emission により
  - `repair_not_required`
  までは live で読めた
- したがって今回の miss は
  - acceptance lane 不全の再発
  ではなく
  - validation target case が short-only promotion と噛み合っていない
  という boundary mismatch を含んでいる

## Judgment

- verdict:
  - `NEEDS_MORE_WORK`

### Why Not `KEEP`

- minimum keep rule の主条件だった
  - `repair_entry.repair_required = true`
  - `repair_call.patch_path_used = true`
  - `repair_applied = true`
  - `scope_acceptance_path = local_monotony_scope`
  を A1/A2 のどちらでも確認できていない
- case B でも mixed issue guard は維持されたが、`scope_acceptance_path` は出ていない

### Why Not Immediate `ROLLBACK`

- visible quality は A1/A2 で悪化していない
- patch 的な継ぎはぎの悪化も見えていない
- case B で mixed issue guard regression は見えていない
- 今回の失敗は `quality_guard.py` diff が live で誤作動したというより、
  A1/A2 の runtime contract が `adaptive` のままで short-only promotion と噛み合っていないこと、
  かつ first pass 出力が trigger floor 未満まで軽くなったことが主因だった

### Exact Read

- prompt の rollback rule に近い表面結果ではある
- ただし live artifact を読むと、
  - quality line の visible regression
  - mixed issue guard collapse
  は確認していない
- よって今回の判断は
  - `diff should be kept as source-of-truth`
    ではなく
  - `validation target mismatch / live variability を先に詰めるべき`
  としての `NEEDS_MORE_WORK`

## Next Step

- 次は source-of-truth update prompt ではない
- 次は follow-up triage prompt が必要
- first question は次のどちらかに narrow に閉じるべき
  - A:
    - live validation target を `length_mode = short` explanatory case に差し替える
  - B:
    - current production-like explanatory `adaptive` case も対象にしたいなら、
      short-only promotion boundary を management / owner で再評価する
- current evidence だけでは `KEEP` も `source-of-truth update` も出せない

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
