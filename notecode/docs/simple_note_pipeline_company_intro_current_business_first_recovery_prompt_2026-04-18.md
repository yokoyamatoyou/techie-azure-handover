# simple note pipeline company intro current business first recovery prompt 2026-04-18

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
- result docs:
  - C:\tetie\notecode\docs\pipeline_current_first_triage_stop_report_2026-04-18.md
  - C:\tetie\notecode\docs\management_stop_report_after_failed_pipeline_current_first_triage_2026-04-18.md
  - C:\tetie\notecode\logs\simple_note_company_intro_acceptance_reopen_live_validation_20260418-171330\summary.json
- 必要なら:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
  - C:\tetie\notecode\note\tests\test_current_mainline_regressions.py
  - C:\tetie\notecode\note\tests\test_current_mainline_runner.py
  - C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py

今回の依頼種別:
- implementation prompt
- `SIMPLE_NOTE_PIPELINE_COMPANY_INTRO_CURRENT_BUSINESS_FIRST_RECOVERY`
- post fail-closed keep

今回の実施範囲:
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` owner の narrow implementation を 1 本だけ行う
- 目的は company intro opener を history-first success から守りつつ、可能なら current-business-first success artifact へ戻すこと
- current fail-closed keep を baseline として維持する
- current success path を壊さない
- production code と owner-local tests は更新可
- AGENTS / WORKLOG / current package docs は更新しない

source-of-truth lock:
- current default route は `grounded generic default`
- planning / skeleton は opt-in only
- structural baseline は `single-pass + optional single repair 1回`
- `prompt_builder.py` simplification-first wording line は failed / rollback 済み / unchanged retry 禁止
- `newalgorithm_pipeline/pipeline.py` current-first source ordering / hint triage も failed / rollback 済み / unchanged retry 禁止
- current keep diff:
  - company intro opener drift が visible に残るときは `SYS_PIPELINE_FAILURE` へ fail-closed する
  - この keep diff は捨てない
- explicit reopen / continue exception は `simple_note_pipeline/pipeline.py` 1 file に限る
- `SECTION_SHADOW` reopen を初手に戻さない
- `quality_guard.py` first にしない
- fixed routing table を追加しない
- prompt accretion 禁止
- `natural_blog_core.py` first section history clamp は do-not-retry
- `output_formatter.py` formatter-only surface polish は do-not-retry
- `input_contract.py` upstream distilled summary only は do-not-retry

current fixed read:
- latest same-owner reopen では unsafe success path は blocked できた
- V3 company intro guard は `3/3` で `SYS_PIPELINE_FAILURE`
- V1 は `2/2 non-worse`
- V2 は `1/1 non-worse`
- G1 は `2/2 no visible regression`
- 残差は `history-first success を止めること` ではなく、
  `fail-closed のまま止まらず current-business-first success を返せる path` をまだ持てていないこと

next narrow hypothesis:
- company intro opener drift が local patch scope の範囲で回復可能なケースでは、
  `simple_note_pipeline/pipeline.py` owner の acceptance / local patch adoption 条件を narrow に補強すれば、
  fail-closed に倒す前に current-business-first opener を持つ success artifact を keep できる
- target は broad branch accumulation ではなく、
  - company intro local patch adoption 条件
  - opener-alignment acceptance 条件
  - fail-closed 前の narrow rescue path
  のどれか 1 本に閉じる

allowed owner scope for first diff:
- production:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- tests:
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
  - C:\tetie\notecode\note\tests\test_current_mainline_regressions.py
  - C:\tetie\notecode\note\tests\test_current_mainline_runner.py
  - C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py

do not touch in first diff:
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
- C:\tetie\notecode\note\natural_blog_core.py
- current package docs
- AGENTS / WORKLOG

implementation rules:
1. 先に current keep diff を読む
   - fail-closed guard を baseline として維持する
2. `simple_note_pipeline/pipeline.py` 内の company-intro local patch adoption / acceptance / fail-closed 順序を short map にする
3. current-business-first success を返せる最小 diff を 1 本だけ実装する
4. history-first success artifact を再び通さない
5. broad repair branch accumulation はしない
6. `prompt_builder.py` wording 追加に逃がさない
7. `newalgorithm_pipeline/pipeline.py` retry に戻さない
8. multiple owner reopen が必要と分かったら広げず停止する

execution order:
1. refs / result docs / current code を読む
2. `simple_note_pipeline/pipeline.py` の current keep diff と rescue 候補点を short map にする
3. simplest diff を 1 本だけ実装する
4. owner-local tests を更新 / 追加する
5. focused tests -> shared checks を流す
6. live validation matrix を回す
7. visible text を読んで self-eval する
8. V3 が current-business-first success に戻れば keep
9. そうでなければ narrow rollback して stop report

test / check order:
- focused owner-local:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "company_intro or patch_path or repair or acceptance" -q
- focused runner/regression:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -k "company or branding" -q
- shared checks:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q

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
  - V3 は `success=true` に戻ること
  - title / first heading / first section が history-first opener に戻らないこと
  - opener は current-business-first または first shadow claim と整合すること
  - V1/V2 explanatory は non-worse
  - G1 no visible regression
- telemetry は secondary
  - metrics only では pass にしない

stop conditions:
- same owner hypothesis 3 failures
- owner scope を超えないと前進できない
- multiple owner reopen が必要
- current success path regression
- history-first success artifact が再流出する

if this hypothesis fails:
- code は rollback して停止する
- current fail-closed keep diff は baseline として守る
- failed hypothesis と visible failure pattern を報告する
- unchanged retry recommendation は残さない

final report must include:
1. 読んだ正本ファイル
2. 読んだ result docs
3. touched files
4. `simple_note_pipeline/pipeline.py` owner に絞った理由
5. current keep diff を baseline にした理由
6. 実装した narrow hypothesis
7. 追加 / 更新した tests
8. 実行したコマンド
9. test / check 結果
10. live validation matrix と variance coverage
11. visible self-eval
12. rollback の有無
13. WEB検索を使ったかどうか
14. stop condition に触れず完了したか
15. AGENTS / WORKLOG / current package docs を更新していないこと
```
