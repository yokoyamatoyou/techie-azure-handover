# separate window sentence final monotony live validation note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の live validation / keep judgment note である
- current source-of-truth は更新しない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- validation setup
- case A latest artifact rerun
- case A fallback saved explanatory monotony rerun
- case B company intro guard
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
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_triage_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_triage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_pipeline_acceptance_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_validation_2026-04-17.md`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## 実施範囲

- `sentence-final pattern monotony cap + single repair` line の live validation / keep judgment のみ実施
- current branch state を `MinimalPipeline + LLMClient` の current-success-path で live rerun
- 生成 artifact は `C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\` に保存
- touched files は generated logs とこの docs note のみ

## Validation Setup

- latest baseline artifact
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- live preflight
  - 2026-04-17 に `run_live_preflight(LLMClient())` を実行
  - `passed = true`
  - `selected_model = gpt-5.4-mini`
- generated artifacts
  - root summary:
    - `C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\summary.json`
  - case A latest artifact rerun:
    - `C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\case_a_explanatory_monotony\result.json`
    - `C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\case_a_explanatory_monotony\visible.txt`
  - case A fallback saved explanatory monotony rerun:
    - `C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\case_a_saved_explanatory_monotony\result.json`
    - `C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\case_a_saved_explanatory_monotony\visible.txt`
  - case B company intro guard:
    - `C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\case_b_company_intro_guard\result.json`
    - `C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\case_b_company_intro_guard\visible.txt`

## Case A Latest Artifact Rerun

### Source

- baseline input:
  - `C:\tetie\notecode\logs\latest_generation_output.json`
- baseline telemetry:
  - `attempt_id = gen-4692e32c`
  - `article_type = explanatory_article`
  - `patch_path_used = true`
  - `repair_applied = false`
  - `flagged_issue_types = ["ending_bucket_monotony"]`
  - `scope_rejection_reason = flagged_scope_drift`
  - `ending_bucket_max_run = 27`
  - `ending_bucket_monotony_score = 0.675`
  - `repair_trigger_score = 0.62`

### Visible Summary

- live rerun title / lead / body は自然に読める
- baseline より短い橋渡し文と説明の切り替えが増え、同じ丁寧文が長く塊で続く感じはかなり弱くなった
- headings の流れは崩れていない
- patch 的な継ぎはぎ感はない

### Telemetry Summary

- rerun result:
  - `success = true`
  - `reason_code = OK`
  - `repair_applied = false`
  - `repair_call = {}`
  - `patch_path_used` は出ていない
  - `scope_acceptance_path` は出ていない
  - `scope_rejection_reason` は出ていない
  - `ending_bucket_max_run = 11`
  - `ending_bucket_monotony_score = 0.2558`
  - `repair_trigger_score = 0.4258`
  - `output_guard.blocked = false`
  - soft warnings は
    - `ending:bucket_monotony`
    - `ai:paragraph_variation`
    - `ai:ending_monotony`
    - `ai_index:borderline`

### Read

- visible quality は baseline より改善している
- ただし minimum keep rule の
  - `patch_path_used = true`
  - `repair_applied = true`
  - `scope_acceptance_path = local_monotony_scope`
  を live では確認できなかった
- つまり target lane は改善確認できたのではなく、rerun が first pass の時点で repair lane に入らなかった

## Case A Fallback Saved Explanatory Monotony Rerun

### Source

- replay input:
  - `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
- historical telemetry in saved source:
  - `article_type = explanatory_article`
  - `patch_path_used = true`
  - `flagged_issue_types = ["ending_bucket_monotony"]`
  - `scope_rejection_reason = flagged_scope_drift`
  - `repair_applied = false`
  - `repair_trigger_score = 0.8`

### Visible Summary

- current live rerun でも explanatory としては読める
- ただし文の長短の差はあるものの、丁寧文の連続がまだ目につく
- visible monotony は latest rerun より強く残った
- headings は壊れていない

### Telemetry Summary

- rerun result:
  - `success = true`
  - `reason_code = OK`
  - `repair_applied = false`
  - `repair_call = {}`
  - `patch_path_used` は出ていない
  - `scope_acceptance_path` は出ていない
  - `scope_rejection_reason` は出ていない
  - `ending_bucket_max_run = 26`
  - `ending_bucket_monotony_score = 0.5417`
  - `repair_trigger_score = 0.4556`
  - `output_guard.blocked = false`
  - soft warnings は
    - `ending:bucket_monotony`
    - `ai:paragraph_variation`
    - `ai:ending_monotony`
    - `ai_index:borderline`

### Read

- saved source では `patch_path_used = true` まで行っていた monotony-only case だった
- current live rerun では same contract でも repair lane 自体が発火せず、`local_monotony_scope` acceptance を確認できなかった
- target case の再現は docs-only live validation では十分に接続できなかった

## Case B Company Intro Guard

### Source

- guard input:
  - `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`

### Visible Summary

- current output は company intro として破綻していない
- 構成は
  - 歴史
  - 現在の主力事業
  - 選ばれる理由
  - 実績
  の4段で維持された
- title / lead / hashtags は多少の表現差はあるが malformed drift ではない
- broad rewrite の継ぎはぎ感は見えない

### Telemetry Summary

- rerun result:
  - `success = true`
  - `reason_code = OK`
  - `repair_applied = false`
  - `patch_path_used = true`
  - `flagged_issue_types = ["shadow_section_drift", "ending_bucket_monotony"]`
  - `scope_acceptance_path` は出ていない
  - `scope_rejection_reason = flagged_scope_drift`
  - `ending_monotony_guard_active = false`
  - `local_monotony_scope_preserved = false`
  - `company_intro_local_patch_guard_active = false`
  - `local_patch_scope_preserved = false`
  - `ending_bucket_max_run = 21`
  - `ending_bucket_monotony_score = 0.6176`
  - `repair_trigger_score = 0.6`

### Read

- mixed issue case で `local_monotony_scope` が誤適用された兆候はない
- `scope_acceptance_path` は出ず、`flagged_scope_drift` は残った
- したがって company intro monotony guard は壊れていない
- 少なくとも今回の diff が mixed issue に広く acceptance を通してしまう regression は見えなかった

## Judgment

- verdict:
  - `NEEDS_MORE_WORK`

### Why Not `KEEP`

- minimum keep rule の主条件だった case A live validation で
  - `patch_path_used = true`
  - `repair_applied = true`
  - `scope_acceptance_path = local_monotony_scope`
  を確認できていない
- latest baseline rerun は visible quality が改善し、saved fallback rerun は monotony が残ったが、どちらも repair lane の acceptance 証跡にならなかった
- telemetry 改善ではなく repair acceptance の接続を live で見たい、という今回の目的は未達

### Why Not `ROLLBACK`

- case B で mixed issue に `local_monotony_scope` を誤適用した兆候は出ていない
- company intro guard は維持された
- current diff 起因の visible broad rewrite / heading drift / must-cover drop は今回の live validation では確認していない
- explanatory rerun の1本では baseline より visible monotony は減っており、diff 自体を即 rollback する理由も揃っていない

## Next Step

- source-of-truth update prompt はまだ作らない
- 次はもう 1 本 implementation or follow-up triage prompt が必要
- focus は次のどちらかに限定する
  - `pipeline.py` owner で、live monotony case が current runtime では repair lane に入らない理由を再確認する
  - それでも live target case が `repair_required` に届かないなら、`quality_guard.py` との境界を narrow に再切り分けする
- ただし今回の evidence だけでは `quality_guard.py` reopen を first action に昇格しない

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
