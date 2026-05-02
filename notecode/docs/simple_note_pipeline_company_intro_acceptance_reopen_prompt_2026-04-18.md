# simple note pipeline company intro acceptance reopen prompt 2026-04-18

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
  - C:\tetie\notecode\logs\heading_drift_reconstruction_simplification_first_20260418-121729\summary.json
- 必要なら:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
  - C:\tetie\notecode\note\tests\test_current_mainline_regressions.py
  - C:\tetie\notecode\note\tests\test_current_mainline_runner.py
  - C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py

今回の依頼種別:
- implementation prompt
- `SIMPLE_NOTE_PIPELINE_COMPANY_INTRO_ACCEPTANCE_REOPEN`
- explicit reopen exception

今回の実施範囲:
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` owner の narrow implementation を 1 本だけ行う
- 目的は company intro opener の history-first drift を downstream acceptance / scope gating で fail-closed できるかを見ること
- current success path を壊さない
- production code と owner-local tests は更新可
- AGENTS / WORKLOG / current package docs は更新しない

source-of-truth lock:
- current default route は `grounded generic default`
- planning / skeleton は opt-in only
- structural baseline は `single-pass + optional single repair 1回`
- `prompt_builder.py` simplification-first wording line は failed / rollback 済み / unchanged retry 禁止
- `newalgorithm_pipeline/pipeline.py` current-first source ordering / hint triage も failed / rollback 済み / unchanged retry 禁止
- explicit reopen exception は `simple_note_pipeline/pipeline.py` 1 file に限る
- `SECTION_SHADOW` reopen を初手に戻さない
- `quality_guard.py` first にしない
- fixed routing table を追加しない
- prompt accretion 禁止
- `natural_blog_core.py` first section history clamp は do-not-retry
- `output_formatter.py` formatter-only surface polish は do-not-retry
- `input_contract.py` upstream distilled summary only は do-not-retry

current failure read:
- upstream source ordering / hint ownership だけでは `V3 company intro guard` が 3/3 fail
- V1 / V2 / G1 は non-worse
- したがって残差は source ordering より downstream acceptance / scope gating の可能性が高い
- target visible symptom は `title / first heading / first section` のいずれかが history-first に戻ること

next narrow hypothesis:
- company intro opener で history-first drift が visible target を壊す場合、
  `simple_note_pipeline/pipeline.py` の repair acceptance / scope gating を narrow に補強すれば、
  V3 を fail-closed できるか、または current-business-first へ戻す path を選べる
- target は broad repair 拡張ではなく、
  - opener drift の検出条件
  - acceptance reject 条件
  - company intro だけの narrow scope gating
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
1. 先に `simple_note_pipeline/pipeline.py` の company-intro repair dispatch / patch path / acceptance points を棚卸しする
2. opener drift を reject または fail-closed する最小 diff を 1 本に絞る
3. title / first heading / first section の history-first を visible gate として扱う
4. broad repair branch accumulation はしない
5. `prompt_builder.py` wording 追加に逃がさない
6. `newalgorithm_pipeline/pipeline.py` retry に戻さない
7. multiple owner reopen が必要と分かったら広げず停止する

execution order:
1. refs / result docs / current code を読む
2. `simple_note_pipeline/pipeline.py` 内の repair acceptance / scope gating points を short map にする
3. simplest diff を 1 本だけ実装する
4. owner-local tests を更新 / 追加する
5. focused tests -> shared checks を流す
6. live validation matrix を回す
7. visible text を読んで self-eval する
8. pass のときだけ keep
9. fail のときは narrow rollback して stop report

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
  - title / first heading / first section が history-first opener に戻らない
  - V1/V2 explanatory は non-worse
  - G1 no visible regression
- telemetry は secondary
  - metrics only では pass にしない

stop conditions:
- same owner hypothesis 3 failures
- owner scope を超えないと前進できない
- multiple owner reopen が必要
- current success path regression

if this hypothesis fails:
- code は rollback して停止する
- failed hypothesis と visible failure pattern を報告する
- unchanged retry recommendation は残さない

final report must include:
1. 読んだ正本ファイル
2. 読んだ result docs
3. touched files
4. `simple_note_pipeline/pipeline.py` owner に絞った理由
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
