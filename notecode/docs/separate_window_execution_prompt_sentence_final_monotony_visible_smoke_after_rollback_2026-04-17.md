# separate window execution prompt sentence final monotony visible smoke after rollback 2026-04-17

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_instruction_window_relocation_prompt_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_instruction_first_request_sentence_final_monotony_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_prompt_builder_constraint_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_actual_repair_prompt_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_followup_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_rollback_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_followup_20260417-195828\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json
- C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\current_mainline_runner.py

今回の依頼種別:
- visible smoke validation prompt
- source-of-truth update ではない
- implementation prompt ではない
- deepresearch prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line について、rollback 後の current branch state を representative live generation で visible smoke validation する
- 目的は keep 判定ではなく、`rollback で visible 悪化が止まったか` を human-visible 基準で読むこと
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない
- generated logs と validation note だけを追加する

current keep-state:
- route default:
  - `grounded generic default`
- planning:
  - `opt-in only`
- structural baseline:
  - `single-pass + optional single repair 1回`
- `reference realization policy`:
  - separate evidence line のまま keep
- モジュール肥大化禁止
- prompt accretion 禁止

current branch read:
- latest followup diff on `prompt_builder.py` was rolled back
- keep しているのは earlier constraint diff only:
  - 見出し列固定
  - 見出し改名・追加・削除・並べ替え禁止
  - closing 概念への差し替え禁止
  - flag span 周辺に留める line
- rollback boundary は clean で、management retriage は不要という前提

core validation question:
- rollback 後の current branch は、followup 追加前より visible にマシか
- 少なくとも
  - 明確な patch 感の増加
  - title / lead / hashtags / heading flow の破綻
  - company intro の history-first drift
  が悪化していないか

重要:
- metrics や telemetry だけで判断しない
- 生成された visible text を必ず読む
- 今回は「Codex が実文を視認して問題がないか」を主判定にする
- 過去失敗パターンが `tests は通るが実生成が悪い` だったことを前提に、見た目の悪さを優先して報告する

validation cases:
- case V1:
  - latest adaptive explanatory baseline rerun
  - source:
    - `C:\tetie\notecode\logs\latest_generation_output.json`
  - role:
    - explanatory visible smoke
- case V2:
  - saved adaptive explanatory replay
  - source:
    - `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
  - role:
    - explanatory fallback visible smoke
- case V3:
  - branding / company_introduction mixed issue case
  - source:
    - `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
  - role:
    - company intro visible smoke / guard read

execution path:
- current success path に固定する
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

what to look for in visible text:
- explanatory cases:
  - 同じ丁寧文の連続が塊で残っていないか
  - repair 後の文だけ浮いていないか
  - title / lead / hashtags が不自然に変わっていないか
  - 見出し flow が再編されていないか
  - 「一文段落だらけ」「継ぎはぎ」になっていないか
- company intro case:
  - 冒頭が history-first に倒れていないか
  - current business 起点が visible に残っているか
  - 会社紹介としての流れが history -> current business 逆転になっていないか
  - broad rewrite 感が強くないか

telemetry is secondary but still record:
- `repair_entry.repair_required`
- `repair_entry.repair_trigger_score`
- `repair_entry.ending_bucket_max_run`
- `repair_entry.ending_bucket_monotony_score`
- `repair_call.patch_path_used`
- `repair_applied`
- `scope_acceptance_path`
- `scope_rejection_reason`
- `acceptance_rejection_reason`

judgment rule:
- `VISIBLE_OK_AFTER_ROLLBACK`
  - visible artifact が followup 時点より悪くない
  - glaring drift が止まっている
  - 次は narrower live/triage に進める
- `VISIBLE_STILL_BAD`
  - visible artifact が引き続き main candidate にできない
  - telemetry pass の有無に関係なく、実文として厳しい
  - 次は management retriage または line freeze 判断が必要

what not to do:
- production code edit
- test edit
- source-of-truth update
- route / planning / formatter policy の議論
- shared checks の再実行を必須化しない
  - rollback 実装直後にすでに通っているため
  - 今回は visible smoke が主目的

allowed touched files:
- generated logs only
- validation note 1本

recommended output file:
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md`

stopping conditions:
- visible smoke 実行のために code edit が必要になった
- current branch state で representative cases を再現できない
- metrics 読みに論点が偏り、visible read が薄くなった

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施した visible smoke cases
3. case ごとの visible summary
4. case ごとの secondary telemetry summary
5. followup 時点より visible が改善 / 同等 / 悪化 のどれか
6. explanatory cases が main candidate として読めるか
7. company intro case が current-business-first を保てているか
8. `VISIBLE_OK_AFTER_ROLLBACK / VISIBLE_STILL_BAD` の結論
9. 次が management retriage prompt か、さらに narrow な live/triage prompt か
10. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
