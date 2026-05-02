# separate window execution prompt heading drift pipeline contract hint consumer triage 2026-04-18

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_heading_drift_upstream_current_first_hint_pipeline_triage_note_2026-04-18.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_upstream_current_first_hint_pipeline_implementation_2026-04-18.md
- C:\tetie\notecode\logs\heading_drift_upstream_current_first_hint_live_validation_20260418-142418\summary.json
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py
- C:\tetie\notecode\note\tests\test_current_mainline_runner.py
- C:\tetie\notecode\note\tests\test_current_mainline_regressions.py

今回の依頼種別:
- owner-local triage prompt
- `CONTRACT_HINT_BEFORE_DISCOURSE_PLAN` re-triage after source-order stop
- source-of-truth update ではない
- implementation prompt ではない

今回の実施範囲:
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` を owner に固定したまま、
  next lever を `contract hint via existing consumer fields` に narrowing する
- code edit / test edit / live rerun はしない
- triage note 1 本だけを作る

inherited stop result:
- `SOURCE_GROUNDING_ORDER_ONLY` generate-level hook は 3 回失敗で rollback 済み
- rolled back files:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py`
  - `C:\tetie\notecode\note\tests\test_current_mainline_regressions.py`
- rollback 後 checks:
  - focused: `10 passed`
  - `test_current_mainline_ui_matrix.py -q`: `25 passed`
  - shared: `318 passed / 1 failed`
  - remaining failure is known owner-outside:
    - `test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt`
- live validation summary:
  - V3 first heading は改善した
  - しかし title が 2/3 run で history-frontloaded のまま
  - same hypothesis は phase rule どおり stop

what changed in diagnosis:
- source ordering は section / heading 側には効いた
- しかし title は十分には動かなかった
- したがって次の question は
  - `source order` を続けるか
  ではなく
  - `pipeline.py` から `simple_note_pipeline` の title / lead consumer に届く既存 contract surface はどれか
  に変わった

current package constraints:
- current default route:
  - `grounded generic default`
- planning / skeleton:
  - opt-in only
  - default reopen しない
- structural baseline:
  - `single-pass + optional single repair 1回`
- prompt accretion 禁止
- hidden reviser accretion 禁止
- same failed hypothesis を unchanged で再投入しない
- `prompt_builder.py` と `newalgorithm_pipeline/pipeline.py` の同時 reopen はしない
- next owner is still:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`

core triage question:
- `pipeline.py` の post-hydration / pre-plan slot で、
  new field を増やさず
  existing contract fields のどれを narrow に current-first hint 化すれば、
  single-pass default の title / lead まで最も届きやすいか

exact owner slot:
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2400-2441`
- `MinimalPipeline.generate()`
- after:
  - `contract = _hydrate_compatibility_source_documents(dict(resolved.contract or {}))`
- before:
  - `sections = list(build_discourse_plan(contract))`

read-only consumer evidence in `prompt_builder.py`:
- raw topic consumer:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py:1985-2012`
  - `topic or prompt_raw or topic_statement or core_message`
- hard contract topic/core consumer:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py:947-958`
  - `topic=...`
  - `core=...`
  - `must_cover=...`
- company intro writer brief:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py:805-819`
  - must_cover / core_message / current_first が writer brief に入る
- UI/runtime summary lines:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py:1096-1122`

candidate levers to compare explicitly:
1. `TOPIC_STATEMENT_CURRENT_FIRST_HINT_ONLY`
   - `pipeline.py` の owner slot で
     `topic_statement` を current-business-first に narrow に補正する
   - `prompt_builder.py` の raw topic consumer に最短で届くかを判定する
2. `CORE_MESSAGE_CURRENT_FIRST_HINT_ONLY`
   - owner slot で `core_message` を narrow に current-first 補正する
   - hard contract `core=` と company intro writer brief に届くかを判定する
3. `MUST_COVER_PRIORITY_ONLY`
   - owner slot で `must_cover` の current/history 順を narrow に整理する
   - company intro focus / heading progress / writer brief に届くかを判定する
4. `REPLAN_BEFORE_LEVER`
   - existing consumer fields のどれも title まで十分届かない場合

strong bias:
- `SOURCE_GROUNDING_ORDER_ONLY` continuation に戻らない
- `prompt_builder.py` wording retry に戻らない
- new contract field は first answer にしない
- `discourse_planner.py` を first owner にしない
- `input_contract.py` を first owner にしない
- compact-plan bridge enable 拡張に戻らない
- implementation に進まない

what to inspect:
- `pipeline.py`
  - owner slot の前後
  - contract がこの後どこへ流れるか
- `prompt_builder.py`
  - `topic_statement`
  - `core_message`
  - `must_cover`
  が title / lead / company intro brief にどう効くか
- tests
  - company intro and title/lead related tests
  - read only

what to decide:
1. next lever 名
2. why this lever reaches title / lead better than source ordering did
3. exact contract field to touch
4. exact owner slot
5. what this next phase will not touch
6. next prompt type
   - implementation prompt
   - or replan

preferred output shape:
- triage note 1 本
- conclusion is exactly one of:
  - `TOPIC_STATEMENT_CURRENT_FIRST_HINT_ONLY`
  - `CORE_MESSAGE_CURRENT_FIRST_HINT_ONLY`
  - `MUST_COVER_PRIORITY_ONLY`
  - `REPLAN_BEFORE_LEVER`
- if not `REPLAN_BEFORE_LEVER`:
  - exact field
  - chosen function and line block
  - narrow hypothesis 1 文
  - why it can reach title / lead
  - rollback boundary
  - next prompt type

recommended output file:
- C:\tetie\notecode\docs\separate_window_heading_drift_pipeline_contract_hint_consumer_triage_note_2026-04-18.md

do not do:
- code edit
- test edit
- live rerun
- docs source-of-truth update
- AGENTS / WORKLOG update
- prompt wording redesign
- giant upstream reopen proposal

WEB search policy:
- 原則不要
- local code だけで切れない場合のみ 1 回だけ許可
- 使った場合は query と採用理由を短く示す

stopping conditions:
- lever を 1 本に絞れない
- `pipeline.py` owner だけでは title / lead へ届かないと判断した
- implementation を始めたくなった
- conclusion を 2 本以上にぼかしたくなった

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. inherited stop result の短い要約
4. candidate levers の比較
5. conclusion
6. exact field
7. exact owner slot
8. narrow hypothesis
9. what this next phase will not touch
10. next prompt type
11. WEB検索を使ったかどうか
12. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
