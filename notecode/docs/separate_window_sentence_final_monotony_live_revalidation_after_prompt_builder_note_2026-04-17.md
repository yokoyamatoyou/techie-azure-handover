# separate window sentence final monotony live revalidation after prompt builder note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の `prompt_builder.py` constraint 後 live re-validation note である
- source-of-truth update ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- validation setup
- shared checks
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
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_prompt_builder_constraint_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_instruction_window_relocation_prompt_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_instruction_first_request_sentence_final_monotony_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_quality_guard_triage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_adaptive_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_prompt_builder_constraint_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_adaptive_reopen_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_constraint_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_adaptive_reopen_20260417-174409\summary.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
- `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\current_mainline_ui_matrix.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py`

## 実施範囲

- `sentence-final pattern monotony cap + single repair` line の live re-validation を `prompt_builder.py` constraint 後の current branch state で再実施した
- 実行経路は current success path に固定した
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- rerun は `execute_current_mainline_generation(MinimalPipeline(LLMClient()), input_contract, prompt_raw)` で A1 / A2 / B の 3 case に閉じた
- production code edit / test edit は行っていない
- touched files は generated logs とこの docs note のみ

## Validation Setup

- generated artifact root:
  - `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_constraint_20260417-183317\`
- root summary:
  - `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_constraint_20260417-183317\summary.json`
- preflight:
  - `run_live_preflight(LLMClient())`
  - `passed = true`
  - `selected_model = gpt-5.4-mini`
- cases:
  - A1:
    - `C:\tetie\notecode\logs\latest_generation_output.json`
  - A2:
    - `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
  - B:
    - `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
    - `rerun` section

## Shared Checks

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - `122 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
  - `83 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "not st08b4_industry_analysis_title_and_lead_do_not_echo_prompt" -q`
  - `233 passed, 1 deselected`
- known unrelated failure 以外の新規 shared-check regression は確認していない

## Case A1 Latest Adaptive Explanatory Rerun

### Visible Summary

- 本文自体は読めるが、visible monotony improvement は確認しづらい
- `新しい取り組みを始めるとき、ゼロから市場をつくるのは負荷が大きいものです。`
- `この「一体で見られる」ことは、実務上かなり大きな判断材料です。`
  のような一文段落が増え、baseline より patch 的な継ぎはぎ感が強い
- title は `実務目線で` が落ち、hashtags も入れ替わった
- heading sequence は消えておらず、5 heading の意味役割も再編されている
  - baseline:
    - `株式会社リソグラとは何を支援する会社か`
    - `リソグラの支援領域と強み`
    - `システム開発で重視している3つの観点`
    - `杉山 満軌はどんな役割を担うのか`
    - `実務でどう読み解けばよいか`
  - rerun:
    - `株式会社リソグラとは何を支援する会社か`
    - `リソグラが提供する支援領域と強み`
    - `成果につなげるための支援の進め方`
    - `システム開発で重視する考え方と杉山 満軌の役割`
    - `株式会社リソグラをどう見れば実務の判断材料になるか`

### `repair_entry` Summary

- `repair_required = true`
- `repair_trigger_score = 0.62`
- `ending_bucket_max_run = 12`
- `ending_bucket_monotony_score = 0.3`
- `flagged_issue_types = ["ending_bucket_monotony"]`
- `patch_path_candidate = true`
- `skip_reason = ""`

### `repair_call` Summary

- `patch_path_used = true`
- `repair_applied = false`
- `ending_monotony_improved = false`
- `scope_rejection_reason = flagged_scope_drift`
- `scope_acceptance_path = null`
- `acceptance_rejection_reason = ending_monotony_not_improved`

### Read

- prompt_builder constraint 後も `repair_applied = true` と `scope_acceptance_path = local_monotony_scope` には届いていない
- live blocker は `flagged_scope_drift` だけでなく `ending_monotony_not_improved` も併発している
- A1 は keep rule ではなく `repair_required true だが repair_applied まで届かない` 側に残った

## Case A2 Saved Adaptive Explanatory Replay

### Visible Summary

- lead は維持され、読み味自体は破綻していない
- ただし heading は全面的に組み替わり、baseline になかった `## まとめ` が追加された
- repair lane は起動しておらず、prompt_builder constraint の効果を示す keep evidence にはなっていない

### `repair_entry` Summary

- `repair_required = false`
- `repair_trigger_score = 0.3478`
- `ending_bucket_max_run = 14`
- `ending_bucket_monotony_score = 0.3182`
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

- A2 は current branch state でも gate 未満に止まった
- A1 の downstream failure を補完する positive evidence にはならない
- `heading sequence changed` は消えていないが、今回は repair lane 不発なので prompt_builder constraint 自体の pass/fail 材料としては弱い

## Case B Company Intro Mixed-Issue Guard

### Visible Summary

- visible artifact は baseline より history-first に寄った
- title / lead / first heading が `130年余りの歴史` 起点へ移動し、`current-business-first keep line` を守れていない
- result headings は baseline 4 本から 5 本へ広がり、broad rewrite 感も強まった
- ただし final acceptance 上は `local_monotony_scope` を mixed issue に誤 accept していない

### `repair_entry` Summary

- `repair_required = true`
- `repair_trigger_score = 0.6`
- `ending_bucket_max_run = 18`
- `ending_bucket_monotony_score = 0.6207`
- `flagged_issue_types = ["shadow_section_drift", "ending_bucket_monotony"]`
- `patch_path_candidate = true`
- `skip_reason = ""`

### `repair_call` Summary

- `patch_path_used = true`
- `repair_applied = false`
- `ending_monotony_improved = true`
- `scope_rejection_reason = flagged_scope_drift`
- `scope_acceptance_path = null`
- `controlled_realization_drift_headings = ["130年余りの歴史を、今の価値へつなぐ会社"]`

### Read

- mixed issue case に `local_monotony_scope` を誤適用した形跡はない
- その意味で scope policy の guard は維持された
- ただし final visible output は history-first drift が強く、case B も keep evidence にはならない

## `scope_acceptance_path` Summary

- case A1:
  - not emitted
- case A2:
  - not emitted
- case B:
  - not emitted
- 今回の live rerun では `scope_acceptance_path = local_monotony_scope` は 1 本も確認できなかった
- `heading sequence changed` も消えていない

## Judgment

- verdict:
  - `NEEDS_MORE_WORK`

### Why Not `KEEP`

- minimum keep rule の主条件だった
  - `repair_entry.repair_required = true`
  - `repair_call.patch_path_used = true`
  - `repair_applied = true`
  - `scope_acceptance_path = local_monotony_scope`
  - visible monotony improvement without heading / lead / hashtag drift
  を A1 / A2 のどちらでも満たしていない
- A1 は prompt_builder constraint 後も `flagged_scope_drift` と `ending_monotony_not_improved` で止まった
- B も `local_monotony_scope` の誤 accept はないが、visible keep line を支える結果になっていない

### Why Not `ROLLBACK`

- mixed issue case で `local_monotony_scope` を誤 accept したわけではなく、acceptance guard 自体は strict のまま維持されている
- shared checks は current branch state で通っている
- A2 は repair lane 自体が未発火で、prompt_builder constraint diff の live effect を rollback 判断まで切り分ける材料が足りない

### Exact Read

- prompt_builder constraint だけでは live A1 を acceptance lane へ押し込めなかった
- 現在の blocker は
  - monotony-only contract が live repair でなお heading drift を止め切れていないこと
  - A1 では `ending_monotony_improved` まで false に落ちたこと
  の 2 点である
- よって current judgment は source-of-truth update でも rollback 断定でもなく、follow-up triage を要する `NEEDS_MORE_WORK`

## Next Step

- 次は source-of-truth update prompt ではない
- 次は follow-up triage prompt が必要
- next triage question は narrow に
  - A1 live run で immutable heading/order contract が actual repair prompt にどう出ていたか
  - それでも heading rename / merge / closing replacement が起きたのか
  - `ending_monotony_improved = false` まで落ちたのは prompt obedience か repair target wording か
  を切るべき
- owner は即 reopen ではなく、まず prompt capture / emitted constraint の follow-up triage が妥当

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
