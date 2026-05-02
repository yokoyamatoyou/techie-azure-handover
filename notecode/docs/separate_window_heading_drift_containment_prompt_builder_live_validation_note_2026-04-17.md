# separate window heading drift containment prompt builder live validation note 2026-04-17

## Position

- この文書は `HEADING_DRIFT_CONTAINMENT_FIRST` line の `prompt_builder.py` first implementation に対する live validation note である
- source-of-truth update ではない
- implementation prompt ではない
- deepresearch prompt ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない
- 実行日は `2026-04-18 JST`、対象 prompt は `2026-04-17` 付けの live validation prompt

## 目次

- 読んだ参照ルールファイル
- 今回の実施範囲
- touched files
- 実施した validation cases
- 実行したコマンド
- case ごとの visible summary
- case ごとの secondary telemetry summary
- overall judgment
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
- `C:\tetie\notecode\docs\separate_window_instruction_handoff_heading_drift_containment_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_heading_drift_containment_management_planning_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_triage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_containment_prompt_builder_implementation_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## 今回の実施範囲

- current branch state で `TITLE_LEAD_HEADING_CONTRACT_FIRST` 実装の live rerun / replay compare を行った
- 実行経路は current success path に固定した
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- 主判定は metrics 単独ではなく generated visible text の読みに置いた
- production code / tests / AGENTS / WORKLOG / current package docs は更新していない

## Touched Files

- generated logs:
  - `C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\summary.json`
  - `C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\case_v1_latest_adaptive_explanatory.json`
  - `C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\case_v1_latest_adaptive_explanatory.txt`
  - `C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\case_v2_saved_adaptive_explanatory.json`
  - `C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\case_v2_saved_adaptive_explanatory.txt`
  - `C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\case_v3_company_intro_guard.json`
  - `C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\case_v3_company_intro_guard.txt`
  - `C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\case_g1_non_target_branding_guard.json`
  - `C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\case_g1_non_target_branding_guard.txt`
  - `C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\newalgorithm_pipeline_audit.jsonl`
- docs note:
  - `C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_live_validation_note_2026-04-17.md`

## 実施した Validation Cases

- case V1:
  - latest adaptive explanatory baseline rerun
  - source:
    - `C:\tetie\notecode\logs\latest_generation_output.json`
- case V2:
  - saved adaptive explanatory replay
  - source:
    - `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
- case V3:
  - company intro guard
  - source:
    - `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
    - `rerun`
- case G1:
  - non-target branding guard
  - source:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\20260322-123339-short\ui-short-branding-trust.json`

## 実行したコマンド

- source / implementation read:
  - `Get-Content -Raw <source docs / logs / prompt_builder.py / test_simple_note_pipeline.py>`
- live validation:
  - `C:\tetie\notecode\.venv\Scripts\python.exe - < inline live validation runner >`
- runner の中身:
  - `execute_current_mainline_generation(MinimalPipeline(LLMClient()), contract, prompt_raw)` を 4 case に対して実行
  - audit path は `C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\newalgorithm_pipeline_audit.jsonl` に切り替えた

## Case ごとの Visible Summary

### Case V1 latest adaptive explanatory baseline rerun

- title は baseline より lead / first heading と同じ論点に寄り、`何を強みにする会社か` で first frame を見せやすくなった
- first heading と 2〜5 heading の wording も baseline より役割差が見え、`支援内容 -> 3つの視点 -> 伴走支援 -> 判断軸` の流れは前より自然
- ただし lead は旧 baseline のままで、`会社情報、株式会社リソグラ、杉山 満軌を順に整理し...` が still metadata-first に見える
- 本文は前よりつぎはぎ感が減ったが、explanatory main candidate と言い切るほど柔らかくはなく、やや説明カード調が残る
- explanatory target としては `前進はあるが keep には不足`

### Case V2 saved adaptive explanatory replay

- title と first heading の framing は baseline より素直で、`減少だけで判断しない` 軸は分かりやすい
- ただし 5 本目の closing heading が増え、heading sequence は baseline よりむしろ整理し切れていない
- 本文は readable だが、`なぜ誤解が起きるのか -> 3つの数値 -> 場面ごとの読み方 -> どう評価に置き直すか` がやや教科書調で、main candidate まで届かない
- lead は baseline 据え置きで、title / lead / heading の frame separation は V1 より弱い
- explanatory fallback としては成立するが、`visible gain が弱い`

### Case V3 company intro guard

- lead 冒頭だけ見ると `現在の事業` に触れており、一見 current-business-first に戻したように見える
- しかし title が `歴史を土台に` に寄り、first heading は `130年余りの歩み` で開始しており、guard の中心である first heading / first section が history-first に再アンカーしている
- 2 heading 目も `データ入力へ転換しました` と history bridge を続けており、saved rerun の `何をしている会社なのか` からは明確に後退している
- 3 heading 目で current business に戻るが、そこまでの導線が長く、company intro の current-business-first keep line を保てたとは読めない
- main target company intro としては `guard fail`

### Case G1 non-target branding guard

- title と heading sequence は保たれ、non-target で heading drift は見えない
- lead は baseline の不自然な echo より改善し、`機能の多さ` から `運用の迷い` へ自然に入れている
- 本文全体も `課題 -> 価値 -> 工夫 -> 判断基準 -> 次の一歩` を維持しており、target diff に引っ張られた明確な regression は読めない
- 非 target guard としては `pass`

## Case ごとの Secondary Telemetry Summary

### Case V1

- `repair_entry`
  - `repair_required = true`
  - `repair_trigger_score = 0.62`
  - `ending_bucket_max_run = 11`
  - `ending_bucket_monotony_score = 0.2683`
  - `flagged_issue_types = ["heading_reanchor", "ending_bucket_monotony"]`
  - `patch_path_candidate = true`
- `repair_call`
  - `patch_path_used = true`
  - `repair_applied = false`
  - `scope_acceptance_path = null`
  - `scope_rejection_reason = flagged_scope_drift`
  - `repair_trigger_improved = true`
- change read:
  - `title_same = false`
  - `lead_same = true`
  - `hashtags_same = false`
  - `heading_sequence_changed = true`

### Case V2

- `repair_entry`
  - `repair_required = true`
  - `repair_trigger_score = 0.58`
  - `ending_bucket_max_run = 10`
  - `ending_bucket_monotony_score = 0.2174`
  - `flagged_issue_types = ["heading_reanchor", "ending_bucket_monotony"]`
  - `patch_path_candidate = true`
- `repair_call`
  - `patch_path_used = true`
  - `repair_applied = false`
  - `scope_acceptance_path = null`
  - `scope_rejection_reason = flagged_scope_drift`
  - `repair_trigger_improved = true`
- change read:
  - `title_same = false`
  - `lead_same = true`
  - `hashtags_same = false`
  - `heading_sequence_changed = true`

### Case V3

- `repair_entry`
  - `repair_required = true`
  - `repair_trigger_score = 0.6`
  - `ending_bucket_max_run = 8`
  - `ending_bucket_monotony_score = 0.32`
  - `flagged_issue_types = ["shadow_section_drift", "ending_bucket_monotony"]`
  - `patch_path_candidate = true`
- `repair_call`
  - `patch_path_used = true`
  - `repair_applied = false`
  - `scope_acceptance_path = null`
  - `scope_rejection_reason = flagged_scope_drift`
  - `controlled_realization_drift_headings = ["130年余りの歴史を受け継ぎ、今の価値へつなぐ会社"]`
  - `repair_trigger_improved = true`
- change read:
  - `title_same = false`
  - `lead_same = false`
  - `hashtags_same = false`
  - `heading_sequence_changed = true`

### Case G1

- `repair_entry`
  - `repair_required = true`
  - `repair_trigger_score = 0.2193`
  - `ending_bucket_max_run = 15`
  - `ending_bucket_monotony_score = 0.5172`
  - `flagged_issue_types = []`
  - `patch_path_candidate = null`
- `repair_call`
  - `patch_path_used = null`
  - `repair_applied = false`
  - `scope_acceptance_path = null`
  - `scope_rejection_reason = null`
- change read:
  - `title_same = true`
  - `lead_same = false`
  - `hashtags_same = false`
  - `heading_sequence_changed = false`

## Overall Judgment

- explanatory target:
  - `partially closer`
  - V1 は main candidate に少し近づいた
  - V2 は gain が弱く、main candidate には届かない
- company intro current-business-first:
  - `kept ではない`
  - V3 は first heading / first section が history-first に戻っており、minimum keep rule を満たさない
- non-target guard:
  - `clear regression なし`
  - G1 は title / heading sequence を保った
- verdict:
  - `REGRESSION`

### Why Not `KEEP_CANDIDATE`

- explanatory で前進はあるが、V1 / V2 のどちらも `main candidate` と言い切る visible quality に届いていない
- V3 で current-business-first keep line を守れていない
- minimum keep rule の `V3 company intro guard pass` を満たしていない

### Why `REGRESSION` Instead Of `NEEDS_MORE_WORK`

- regression rule の
  - `V3 で current-business-first が壊れる`
  - `history-first が残る`
  に直接当たっている
- current line の主 target は company intro first heading drift containment であり、そこで fail しているため `gain はあるが未達` より強く `regression` と読むのが妥当

## Next Step

- next prompt:
  - `next implementation / triage prompt`
- exact read:
  - source-of-truth update prompt へは進まない
  - V1 explanatory gain と V3 company intro regression が割れているため、same owner `prompt_builder.py` で
    - company intro first heading を current-business-first に固定する narrower line
    - explanatory gain を壊さない wording boundary
    を切り直す triage / narrower re-implementation が必要
- WEB検索:
  - `not used`

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
