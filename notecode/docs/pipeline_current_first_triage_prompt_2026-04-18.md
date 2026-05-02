# pipeline current first triage prompt 2026-04-18

```text
参照ルールファイル:
- current source-of-truth:
  - C:\tetie\AGENTS.md
  - C:\tetie\notecode\AGENTS.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
  - C:\tetie\WORKLOG.md
- separate-window result docs:
  - C:\tetie\notecode\docs\separate_window_instruction_handoff_heading_drift_containment_2026-04-17.md
  - C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_triage_note_2026-04-17.md
  - C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_live_validation_note_2026-04-17.md
  - C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_reconstruction_simplification_first_2026-04-18.md
  - C:\tetie\notecode\logs\heading_drift_reconstruction_simplification_first_20260418-121729\summary.json
- 必要なら:
  - C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - C:\tetie\notecode\note\tests\test_current_mainline_runner.py
  - C:\tetie\notecode\note\tests\test_current_mainline_regressions.py
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の依頼種別:
- implementation prompt
- `PIPELINE_CURRENT_FIRST_TRIAGE`
- source-of-truth update ではない
- `prompt_builder.py` retry prompt ではない

今回の実施範囲:
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` owner の narrow triage を 1 本だけ行う
- 目的は company intro opener の current-first anchor を upstream source ordering / hint ownership で安定化できるかを見ること
- wording accretion で押し切らない
- current success path を壊さない
- production code と owner-local tests は更新可
- AGENTS / WORKLOG / current package docs は更新しない

source-of-truth lock:
- current default route は `grounded generic default`
- planning / skeleton は opt-in only
- structural baseline は `single-pass + optional single repair 1回`
- latest failed hypothesis は `prompt_builder.py` simplification-first wording line
- 上記 failed hypothesis は rollback 済み、kept diff はない
- same failed hypothesis を unchanged で reopen しない
- `prompt_builder.py` と `pipeline.py` の同時 reopen はしない
- `SECTION_SHADOW` reopen を初手で戻さない
- `quality_guard.py` first にしない
- repair acceptance reopen を初手にしない
- sentence-final monotony line を main candidate に戻さない
- `natural_blog_core.py` first section history clamp 仮説は do-not-retry
- `newalgorithm_pipeline/output_formatter.py` formatter-only surface polish 仮説は do-not-retry
- `newalgorithm_pipeline/input_contract.py` upstream distilled summary 単独仮説は do-not-retry
- article-type fixed routing table は追加しない
- prompt accretion 禁止
- fixed routing table 追加禁止

result-doc boundary:
- `separate-window result docs` は evidence-only として読む
- current owner / current do-not / current stop boundary は `naturalness_recovery_2026-04-07` package docs を優先する
- old `prompt_builder.py` line を current owner として復帰させない

current failure read:
- `prompt_builder.py` owner の `heading_drift_reconstruction_simplification_first` は explanatory 側で partial gain を返した
- ただし company intro guard で mandatory gate fail
- fixed facts:
  - V1 は partial / non-worse
  - G1 は no visible regression
  - V2 は still awkward variance
  - V3 は mandatory gate fail
  - V3 run2 は title history-first
  - V3 run3 は first section history-first
- management read:
  - wording simplification 単独では opener reanchor を止められない
  - wrong-anchor consistency が upstream に残っている可能性が高い
  - V3 は variance 1 本でも `title / first heading / first section` のどれかが history-first に戻った時点で fail とみなす
  - V3 run1 の partial pass を current winner 扱いしない

next narrow hypothesis:
- company intro で current-business evidence が source / must-cover に存在する場合、
  - opener 用の source ordering
  - current-first hint
  - title / lead / first section へ渡る anchor
  のどれかを `pipeline.py` owner だけで minimal に補強すると、history-first reanchor を減らせる
- ただし hardcoded article-type routing や broad branch accumulation は増やさない

likely ownership surface to inspect first:
- `generate()` 入口の `resolve_input_contract() -> _hydrate_compatibility_source_documents() -> _reorder_company_intro_current_first_sources()` 順序
- `_company_intro_source_priority_band()`
- `_reorder_company_intro_current_first_sources()`
- `_bridge_anchor_for_section()` と section ledger へ渡る anchor / must-cover bridge
- planned heading / section ordering を組む直前に current-first hint が落ちていないか
- `prompt_builder.py` wording を増やさず、upstream から current-first の優先順が見える形を first diff に閉じる

allowed owner scope for first diff:
- production:
  - C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- tests:
  - C:\tetie\notecode\note\tests\test_current_mainline_runner.py
  - C:\tetie\notecode\note\tests\test_current_mainline_regressions.py
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

do not touch in first diff:
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
- C:\tetie\notecode\note\natural_blog_core.py
- current package docs
- AGENTS / WORKLOG

implementation rules:
1. 先に `pipeline.py` 内で opener anchor に関与する upstream points を棚卸しする
2. source ordering / hint / anchor handoff のどれが最小 diff かを 1 本に絞る
3. company intro で current-business evidence がある場合だけ current-first を優先する
4. history は current anchor 後の背景に回すが、hardcoded route table にはしない
5. `prompt_builder.py` wording を足し増ししない
6. helper を増やしすぎない
7. multiple owner reopen が必要と分かったら広げず停止する

execution order:
1. refs / result docs / current code を読む
2. `pipeline.py` 内の opener-related upstream points を short map にする
3. simplest diff を 1 本だけ実装する
4. owner-local tests を更新 / 追加する
5. focused tests -> shared checks を流す
6. live validation matrix を回す
7. visible text を読んで self-eval する
8. pass のときだけ keep
9. fail のときは narrow rollback して stop report

test / check order:
- owner-local:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py -k "reresolves_stale_company_intro_fields or pipeline_source" -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_regressions.py -k "company_intro_uses_company_outline_headings" -q
- focused simple-note:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "blank_company_intro_generation_prompt_locks_first_section_to_current_business or longform_explanatory or distinguishes_title_and_lead_tone" -q
- shared checks:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q

validation matrix:
- mandatory cases:
  - V1 latest adaptive explanatory baseline rerun
  - V2 saved adaptive explanatory replay
  - V3 company intro guard
  - G1 non-target branding guard
- variance coverage:
  - V3: 3 runs
  - V1: 2 runs
  - V2: 1 run minimum
  - G1: 2 runs
- visible success gate:
  - V3 company intro is mandatory
  - title / first heading / first section が history-first opener に戻らない
  - V1/V2 explanatory は non-worse
  - G1 no visible regression
- telemetry は secondary
  - metrics only では pass にしない

autonomous repair policy:
- エラーが出なければ自律的に実装 -> 検証 -> visible self-eval まで進む
- blocker が出た場合は local code search を先に使う
- external WEB search は blocker 解消に必要な場合だけ最小限にする
- same error は 3 回まで self-fix する
- 3 回で収束しなければ rollback して停止する

stop conditions:
- same owner hypothesis 3 failures
- owner scope を超えないと前進できない
- multiple owner reopen が必要
- current success path regression

if this hypothesis fails:
- code は rollback して停止する
- failed hypothesis と visible failure pattern を報告する
- unchanged retry recommendation は残さない

stop report format:
- 停止時は必ず次の形式を使う
- `### Stop Report`
- `- Blocked item:`
- `- What was confirmed:`
- `- Inconsistency summary:`
- `- Attempt 1:`
- `- Attempt 2:`
- `- Attempt 3:`
- `- Next decision needed:`

final report must include:
1. 読んだ正本ファイル
2. 読んだ separate-window result docs
3. touched files
4. upstream owner に絞った理由
5. 実装した narrow hypothesis
6. 追加 / 更新した tests
7. 実行したコマンド
8. test / check 結果
9. live validation matrix と variance coverage
10. visible self-eval
11. rollback の有無
12. WEB検索を使ったかどうか
13. stop condition に触れず完了したか
14. AGENTS / WORKLOG / current package docs を更新していないこと
```
