# separate window sentence final monotony repair lane followup note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の follow-up note である
- current source-of-truth は更新しない
- AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- live case と focused test case の差分
- `repair_call_unavailable` の具体理由
- code diff
- tests
- boundary
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
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_validation_note_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\summary.json`

## 実施範囲

- focus は `live monotony case が current runtime で repair lane に入らない理由` の切り分け
- first owner は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `quality_guard.py` は first action では触っていない
- telemetry を narrow に追加し、focused test と live case の entry gap を `pipeline.py` 返却で読めるようにした

## Live Case と Focused Test Case の差分

### Focused Test Side

- `test_simple_note_pipeline_repairs_explanatory_monotony_with_local_scope_acceptance`
  は `_run_optional_repair()` を直接呼ぶ
- test input diagnostics は最初から
  - `repair_required = true`
  - `repair_trigger_score = 0.62`
  - `flagged_spans = [{"issue_type": "ending_bucket_monotony"}]`
  - `ending_bucket_max_run = 9`
  - `ending_bucket_monotony_score = 1.0`
  を持っている
- そのため test は repair lane entry 以降だけを検証しており、
  `generate() -> _refresh_diagnostics_state() -> quality_guard merge`
  の gate を通っていない

### Live Case Side

- live validation case A latest rerun / saved rerun はどちらも
  - `repair_call = {}`
  - `repair_applied = false`
  - wrapper 上は `patch_path_refusal_reason = repair_call_unavailable`
  で止まっていた
- しかし actual blocker は `repair call unavailable` そのものではなく、
  `_run_optional_repair()` に入る前の `repair_required` gate である

## `repair_call_unavailable` の具体理由

- `pipeline.py` の `_run_optional_repair()` は
  - `if not bool(diagnostics.get("repair_required")):`
  で即 return する
- live monotony case は `ending_bucket_monotony` soft warning と flagged span を持ちうるが、
  current `quality_guard.py` owner の trigger では
  `repair_trigger_score >= 0.58`
  に届かないと `repair_required = true` にならない
- live validation で残っていた case A は
  - latest rerun:
    - `repair_trigger_score = 0.4258`
    - `ending_bucket_max_run = 11`
    - `ending_bucket_monotony_score = 0.2558`
  - saved rerun:
    - `repair_trigger_score = 0.4556`
    - `ending_bucket_max_run = 26`
    - `ending_bucket_monotony_score = 0.5417`
  で、どちらも `repair_required` gate を超えていない
- つまり current mismatch は
  - focused test:
    - `repair_required=true` を injected して acceptance lane を検証
  - live case:
    - `ending_bucket_monotony` は見えても `repair_required=false` で lane entry 前に停止
  という差である

## Code Diff

### Changed Files

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

### Changed Functions

- `pipeline.py`
  - `_flagged_issue_types()` を追加
  - `_build_repair_entry_telemetry()` を追加
  - `generate()` で pre-repair diagnostics snapshot を保持し、
    `pipeline_check.body_generation.repair_entry` を追加
- `test_simple_note_pipeline.py`
  - `test_simple_note_pipeline_generate_emits_repair_entry_for_untriggered_explanatory_monotony`
    を追加

### What The New Telemetry Shows

- `body_generation.repair_entry` に以下を出すようにした
  - `repair_required`
  - `repair_trigger_score`
  - `ending_bucket_max_run`
  - `ending_bucket_monotony_score`
  - `flagged_span_count`
  - `flagged_issue_types`
  - `patch_path_candidate`
  - `skip_reason`
- live-like non-entry case では
  - `repair_required = false`
  - `flagged_issue_types = ["ending_bucket_monotony"]`
  - `patch_path_candidate = true`
  - `skip_reason = repair_not_required`
  と読める

## Tests

- focused run
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "explanatory_monotony or ending_monotony or local_monotony_scope or local_patch_scope or rewrites_unflagged_section" -q`
  - `8 passed`
- full file
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `98 passed`
- owner-neighbor
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - `115 passed`
- shared checks
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
  - `83 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "not st08b4_industry_analysis_title_and_lead_do_not_echo_prompt" -q`
  - `233 passed, 1 deselected`

## Boundary

- `pipeline.py` owner だけでは repair lane entry 自体は直していない
- current behavior change は入れていない
- company intro mixed issue guard は今回 diff で広げていない
- existing mixed issue focused checks は維持された
- したがって current boundary は次のとおり
  - acceptance lane bug ではなく
  - upstream `repair_required` / trigger owner の判断で lane に入っていない
- この boundary は `quality_guard.py` owner にある

## Next Step

- next prompt は live re-validation ではなく `quality_guard.py` triage prompt が妥当
- first question は
  - `ending_bucket_monotony` 単独で
  - `flagged_spans` と `patch_path_candidate` はあるのに
  - `repair_required` へ届かない explanatory short case を
  current trigger policy でどう扱うか
  に限定する

## Non-Updates

- `quality_guard.py` は更新していない
- `prompt_builder.py` は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
