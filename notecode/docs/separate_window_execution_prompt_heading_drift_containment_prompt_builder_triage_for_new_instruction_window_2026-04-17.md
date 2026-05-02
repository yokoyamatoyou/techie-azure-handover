# separate window execution prompt heading drift containment prompt builder triage for new instruction window 2026-04-17

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_instruction_handoff_heading_drift_containment_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_management_planning_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_containment_prompt_builder_triage_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の依頼種別:
- owner-local triage prompt
- 新しい指示ウインドウへ持ち帰る報告を作るための作業 prompt
- source-of-truth update ではない
- implementation prompt ではない
- deepresearch prompt ではない

今回の実施範囲:
- `HEADING_DRIFT_CONTAINMENT_FIRST` line の first owner を `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` に固定し、initial draft 側の frame drift containment に最初に効かせる lever を 1 つに絞る
- docs / logs / code reference 読みだけで判断する
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない
- current source-of-truth は更新しない
- 最終報告は、新しい指示ウインドウがこの thread context を持たなくても読める carry-back 形式で書く

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

management conclusion to inherit:
- current redirect line:
  - `HEADING_DRIFT_CONTAINMENT_FIRST`
- current first owner:
  - `PROMPT_BUILDER_FRAME_CONTAINMENT_OWNER`
- exact read:
  - visible main failure は repair acceptance ではなく single-pass 初稿の
    - title drift
    - lead drift
    - heading wording / sequence drift
    - company intro first heading の history-first reanchor
    にある
- therefore:
  - `quality_guard.py` first をやらない
  - repair acceptance reopen をやらない
  - `sentence-final monotony` continuation に戻らない

今回の core question:
- `prompt_builder.py` のどの lever を first step にすると、最小 diff で initial draft の frame drift containment に最も効くか

candidate levers to compare:
1. `TITLE_LEAD_HEADING_CONTRACT_FIRST`
   - title / lead / heading progress / first heading role の contract lines を generation prompt に狭く追加・強化する
2. `COMPANY_INTRO_FRAME_REUSE_FIRST`
   - blank company intro 用 current-business-first keep line / frame lines を initial generation 側にも再利用または再接続する
3. `SECTION_SHADOW_EMISSION_FIRST`
   - company-introduction で省かれている `SECTION_SHADOW` / related frame lines を initial generation prompt に戻すか narrow 再導入する
4. `STRUCTURE_ONLY_FIRST`
   - heading progress / section role / first-section anchor の構造 line だけを扱い、title / lead には触れない

what to decide:
- first lever を 1 つに絞る
- second lever は optional backlog として短く示す
- 次の implementation prompt に渡せる narrow hypothesis を 1 本に閉じる

evaluation criteria:
- narrowness:
  - 1-file / 1-diff に閉じやすいか
- containment value:
  - title / lead / heading / first-section drift に効きやすいか
- accretion risk:
  - prompt 肥大を増やしすぎないか
- rollback clarity:
  - 失敗時に clean rollback できるか
- company intro relevance:
  - current-business-first reanchor failure に直接効くか
- explanatory relevance:
  - explanatory title / lead / heading drift にも効くか

強い制約:
- `pipeline.py` の compact-plan scaffold / dispatch / acceptance を reopen しない
- `quality_guard.py` の trigger / issue classification を reopen しない
- code edit しない
- test edit しない
- live rerun しない
- 2 lever 以上を first implementation に持ち込まない

見てよい範囲:
- `prompt_builder.py` のうち
  - title / lead intent emission
  - structure / heading progress emission
  - blank company intro current-business-first line
  - company-introduction generation で除外されている `SECTION_SHADOW` / frame-related lines
  - generation prompt assembly path

good outcome:
- first lever が 1 つに閉じる
- next prompt type を `prompt_builder.py` owner の implementation prompt に固定できる
- 新しい指示ウインドウへ、そのまま貼れる報告になる

bad outcome:
- 2 lever 以上を同時採用する
- `prompt_builder.py` と `pipeline.py` の両 reopen を提案する
- 実装や rerun に進む

recommended output file:
- `C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_triage_note_2026-04-17.md`

stopping conditions:
- owner-local triage を超えて implementation したくなった
- code edit しないと判断できないと言いたくなった
- first lever を 1 つに絞れない

最終報告は、新しい指示ウインドウへそのまま持ち帰れる形で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. `prompt_builder.py` 内で見た candidate levers
4. first lever の結論
5. narrow hypothesis
6. second lever を今やらない理由
7. prompt accretion risk の評価
8. next prompt type が implementation prompt でよいか
9. 新しい指示ウインドウ向け carry-back summary
   - current redirect line
   - first owner
   - first lever
   - next prompt type
   - production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
10. AGENTS / WORKLOG / current package docs を更新していないこと
```
