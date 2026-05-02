# separate window sentence final monotony pipeline acceptance after adaptive note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の downstream acceptance boundary triage note である
- current source-of-truth は更新しない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- inspected artifacts
- A1 rejection path
- comparison with focused acceptance test path
- decision
- focused tests
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
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_adaptive_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_quality_guard_triage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_repair_lane_followup_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_pipeline_acceptance_after_adaptive_reopen_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_adaptive_reopen_20260417-174409\summary.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## 実施範囲

- owner は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` に限定した
- A1 の `repair_required = true` / `patch_path_used = true` 後に `local_monotony_scope` へ進まない理由だけを詰めた
- `quality_guard.py` / `prompt_builder.py` / `newalgorithm_pipeline` / current package docs には触れていない
- safe reopen が見えなければ no-diff で止める前提で進めた

## Inspected Artifacts

- prior live revalidation summary:
  - `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_adaptive_reopen_20260417-174409\summary.json`
- owner-local probe artifacts generated in this triage:
  - `C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\repair_capture.json`
  - `C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\repair_capture_result.json`
  - `C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\helper_analysis.json`
  - `C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\probe.json`
  - `C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\result.json`

## A1 Rejection Path

### Prior Live Evidence To Explain

- `sentence_final_monotony_live_revalidation_after_adaptive_reopen_20260417-174409\summary.json` では A1 が
  - `repair_entry.repair_required = true`
  - `repair_call.patch_path_used = true`
  - `repair_call.ending_monotony_improved = true`
  - `repair_call.local_monotony_scope_preserved = false`
  - `repair_call.scope_rejection_reason = flagged_scope_drift`
  で止まっていた

### Current Owner-Local Probe Read

- current probe run では repair raw を直接保存し、current draft と repaired draft を helper にそのまま通して比較した
- saved repair raw:
  - `repair_capture.json`
  - `repair_raw`
- helper inspection:
  - `helper_analysis.json`

### Exact A1 Rejection Reason

- current draft と repaired draft は
  - `title_same = true`
  - `lead_same = true`
  - `hashtags_same = true`
  だった
- それでも `_repair_preserves_local_monotony_scope()` が false になった直接理由は、section identity / order drift である
- `helper_analysis.json` で確認した current headings:
  - `株式会社リソグラとは何を支援する会社か`
  - `リソグラの強みは新規事業・マーケティング・開発をつなげること`
  - `成果につなげるために重視している判断軸`
  - `実務で見るなら、どんな会社に向いているか`
  - `杉山 満軌が体現するリソグラの伴走姿勢`
- repaired headings:
  - `株式会社リソグラとは何を支援する会社か`
  - `リソグラの強みは新規事業・マーケティング・開発をつなげる支援体制`
  - `成果につなげるために重視している視点`
  - `杉山 満軌が体現するリソグラの伴走姿勢`
  - `株式会社リソグラの特徴をどう見るか`
- つまり repaired draft は
  - heading text を 2 本差し替え
  - closing 2 sections の順序まで入れ替え
  - 新しい closing heading を追加
  しており、monotony-only local patch の範囲を超えている
- `_repair_preserves_local_monotony_scope()` は heading sequence equality で落ちるため、overlap threshold や length ratio を調整してもこのケースは reopen されない

## Comparison With Focused Acceptance Test Path

- existing accepted path:
  - `test_simple_note_pipeline_repairs_explanatory_monotony_with_local_scope_acceptance`
- この test path では
  - title / lead / hashtags は不変
  - heading sequence も不変
  - 変わるのは各見出し本文の局所 surface だけ
  - そのため `scope_acceptance_path = local_monotony_scope` が通る
- live A1 miss は
  - adaptive explanatory prose だから helper が厳しすぎる
  というより
  - repaired output 側が section identity と order を動かしている
  ことが主因

## Decision

- outcome:
  - no code diff

### Why No Safe Fix Landed

- monotony-only acceptance を reopen したい理由は section-local surface repair を受けるためであり、heading rename / section reorder まで許すためではない
- A1 の current miss は helper threshold の微差ではなく、scope boundary の本丸である heading sequence drift に当たっている
- ここで `pipeline.py` 側を緩めると
  - monotony-only lane から section identity rewrite が通りうる
  - mixed issue / company intro guard と衝突しやすい
  - prompt で禁じられている broad acceptance widening に近づく
- よって current acceptance boundary は維持するのが妥当

### Explainable Read

- A1 rejection は `flagged_scope_drift` の中でも
  - `heading_sequence_changed`
  と説明するのが正確
- safe reopen をやるなら owner は `pipeline.py` ではなく、repair output を section-local に閉じる prompt / generation behavior 側へ戻る必要がある

## Focused Tests

- owner-local focused:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "explanatory_monotony or local_monotony_scope or rewrites_unflagged_section or company_intro" -q`
  - `23 passed, 75 deselected`

## Next Step

- 次は live re-validation prompt ではない
- 次は management retriage prompt が妥当
- narrow question は次に閉じるべき
  - monotony-only patch path で heading rename / section reorder を起こさないように repair output constraint をどう tighten するか
  - acceptance boundary を緩めずに A1 を直す owner はどこか
- current evidence では `pipeline.py` acceptance reopen を keep-side code diff として出す根拠は足りない

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
