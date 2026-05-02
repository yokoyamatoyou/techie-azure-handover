# separate window execution prompt sentence final monotony management retriage 2026-04-17

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
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_quality_guard_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_adaptive_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_pipeline_acceptance_after_adaptive_note_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_adaptive_reopen_20260417-174409\summary.json
- C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\helper_analysis.json
- C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\repair_capture.json
- C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\probe.json

今回の依頼種別:
- management retriage prompt
- source-of-truth update ではない
- deepresearch prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の next owner を management で再判断する
- current question は
  - A1 で `repair_required = true`
  - `patch_path_used = true`
  - `ending_monotony_improved = true`
  なのに
  - repair output が heading rename / section reorder を起こし
  - `flagged_scope_drift` で reject される
  という状態で、次の owner をどこに置くべきか
- 初手は docs / artifacts 読みだけに閉じる
- production code は変更しない
- AGENTS / WORKLOG / current package docs は更新しない

current keep-state:
- route default:
  - `grounded generic default`
- planning:
  - `opt-in only`
- structural baseline:
  - `single-pass + optional single repair 1回`
- blank company intro keep line:
  - `prompt_builder.py` の `current-business-first keep line`
- `reference realization policy`:
  - separate evidence line のまま keep
  - 今回の main line にはしない

already-fixed boundary:
- upstream trigger side:
  - `quality_guard.py` で explanatory short / adaptive monotony promotion は narrow に入っている
- acceptance helper side:
  - `pipeline.py` helper は heading sequence drift を correctly reject している
- current blocker:
  - repair output itself is not local enough
  - monotony-only lane に対して repaired draft が
    - heading rename
    - section reorder
    - closing section replacement
    を起こしている

primary management question:
- acceptance boundary を緩めるのではなく、repair output を heading-local に縛る next owner はどこか

candidate owners to judge:
- candidate A:
  - `simple_note_pipeline/prompt_builder.py`
  - repair prompt constraint owner
  - monotony-only patch path で heading rename / reorder を explicitly 禁止する line
- candidate B:
  - `simple_note_pipeline/pipeline.py`
  - repair prompt assembly / patch scope payload owner
  - flagged headings / immutable headings / preserve-order contract を prompt に渡す line
- candidate C:
  - no immediate code diff
  - current line stop
  - management hold / split out

目的:
- どの owner が最小 diff で `heading_sequence_changed` を抑えられるかを判断する
- acceptance boundary を緩めない方針を keep する
- next implementation prompt を 1 owner に閉じて作れる状態にする

judgment guidance:
- choose `PROMPT_BUILDER_OWNER` if:
  - 問題の本質は repair output instruction が広すぎることであり、
    monotony-only repair に heading rename / reorder prohibition を明示すべき
  - `build_repair_prompt_from_diagnostics()` 1 owner に閉じられる
- choose `PIPELINE_PROMPT_ASSEMBLY_OWNER` if:
  - prompt wording aloneより、flagged headings / preserve-order metadata を pipeline から渡す必要がある
  - それでも `pipeline.py` 1 owner に閉じられる
- choose `MANAGEMENT_HOLD` if:
  - owner 1 file に閉じられず、複数 owner 同時 edit が必要
  - next diff の narrow hypothesis が立たない

今回やること:
1. `helper_analysis.json` と repair capture を読み、
   actual rejection reason が `heading_sequence_changed` であることを確認する
2. current repair prompt / patch scope contract が
   heading rename / reorder を防いでいるか、artifact と code references で判断する
3. candidate A/B/C を比較し、
   next owner を 1 つ選ぶ
4. docs note を 1 本作る
5. 次に使う prompt の type を決める

allowed touched files:
- docs only
- recommended:
  - C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_note_2026-04-17.md

do not touch:
- production code
- tests
- AGENTS
- WORKLOG
- current planning package docs

do not:
- acceptance boundary を緩める方向で入らない
- global threshold を再調整しない
- route default / planning default を触らない
- `reference realization policy` を main line に戻さない
- deepresearch に逸れない

recommended output structure:
- current blocker read
- why pipeline acceptance should stay strict
- candidate A/B/C comparison
- decision
- next prompt type

stopping conditions:
- candidate owner を 1 file に閉じられない
- management judgment なしに code diff へ入りたくなった
- monotony line から別論点へ逸れた

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. touched files
4. current blocker の正確な read
5. `PROMPT_BUILDER_OWNER` / `PIPELINE_PROMPT_ASSEMBLY_OWNER` / `MANAGEMENT_HOLD` の結論
6. なぜその owner なのか
7. 次に必要なのがどの implementation prompt か
8. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
