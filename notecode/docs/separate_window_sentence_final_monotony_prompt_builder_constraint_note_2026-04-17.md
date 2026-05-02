# separate window sentence final monotony prompt builder constraint note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の `prompt_builder.py` owner implementation note である
- source-of-truth update ではない
- production code の owner は `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` に閉じた

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- touched files
- landed constraint diff
- focused tests
- decision
- non-updates

## 読んだ参照ルールファイル

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_constraint_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_pipeline_acceptance_after_adaptive_note_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_adaptive_reopen_20260417-174409\summary.json`
- `C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\helper_analysis.json`
- `C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\repair_capture.json`
- `C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\probe.json`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## 実施範囲

- `prompt_builder.py` owner だけで monotony-only repair prompt の immutable heading/order contract を追加した
- acceptance boundary や `pipeline.py` には触れず、repair output を heading-local に縛る line だけを足した
- focused tests を追加し、shared checks まで実行した

## Touched Files

- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_prompt_builder_constraint_note_2026-04-17.md`

## Landed Constraint Diff

- `prompt_builder.py` に `_extract_body_headings()` を追加し、current body から見出し列を抽出できるようにした
- `prompt_builder.py` に `_build_local_monotony_patch_scope_lines()` を追加し、`flagged_spans.issue_type` が `ending_bucket_monotony` だけの patch path でのみ hard constraint を出すようにした
- `build_repair_prompt()` の `[PATCH_SCOPE]` block に monotony-only local repair 向けの constraint lines を追加した
- 追加した hard lines:
  - `monotony_patch=見出し列をこの順番で固定する: ...`
  - `monotony_patch=見出し名は一字一句変えない。見出しの改名・追加・削除・並べ替えをしない。`
  - `monotony_patch=最後の見出しを別のまとめ見出しへ差し替えず、結びの節を新しい closing 概念で置き換えない。`
  - `monotony_patch=書き換えは flag span とその前後本文だけにとどめ、別節へ論点を逃がさない。`
- scope は monotony-only patch に限定し、`heading_reanchor` / `shadow_section_drift` / `comparative_thin_section` には新 line を広げていない

## Focused Tests

- added:
  - `test_repair_prompt_adds_immutable_heading_contract_for_local_monotony_patch`
  - `test_repair_prompt_scopes_heading_contract_to_monotony_only_patch`
- executed:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "repair_prompt or patch_scope or heading_count or explanatory_monotony" -q`
  - `13 passed, 87 deselected`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `100 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - `122 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
  - `83 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "not st08b4_industry_analysis_title_and_lead_do_not_echo_prompt" -q`
  - `233 passed, 1 deselected`

## Decision

- outcome:
  - constraint diff landed safely
- current judgment:
  - `prompt_builder.py` owner is sufficient for this step
  - acceptance boundary を reopen する必要はない
- next prompt type:
  - live re-validation prompt

## Non-Updates

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` は更新していない
- `quality_guard.py` は更新していない
- `newalgorithm_pipeline` 配下は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
