# management prompt after failed pipeline current first triage 2026-04-18

## Status

- consumed
- superseded by park decision
- current startup prompt としては使わない
- current canonical prompt は `C:\tetie\notecode\docs\parked_package_prompt_naturalness_recovery_2026-04-18.md`

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
- latest result docs:
  - C:\tetie\notecode\docs\pipeline_current_first_triage_stop_report_2026-04-18.md
  - C:\tetie\notecode\docs\pipeline_current_first_triage_prompt_2026-04-18.md
  - C:\tetie\notecode\docs\separate_window_instruction_handoff_heading_drift_containment_2026-04-17.md
  - C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_triage_note_2026-04-17.md
  - C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_live_validation_note_2026-04-17.md
  - C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_reconstruction_simplification_first_2026-04-18.md
  - C:\tetie\notecode\logs\heading_drift_reconstruction_simplification_first_20260418-121729\summary.json

今回の依頼種別:
- management prompt
- `MANAGEMENT_REEVALUATE_AFTER_FAILED_PIPELINE_CURRENT_FIRST_TRIAGE`
- implementation prompt ではない
- production code 実装依頼ではない

今回の実施範囲:
- management / instruction only
- current source-of-truth と latest stop report を照合する
- `pipeline.py` current-first triage fail を source-of-truth に固定する
- 次に合法な `1 owner / 1 hypothesis` がまだ残っているかを判定する
- 残っている場合だけ next implementation prompt を 1 本作る
- 残っていない場合は block を明記して stop report で止める
- production code / tests は編集しない

current fixed judgment:
- current package は `naturalness_recovery_2026-04-07`
- current package は未 close
- current success path は維持する
- default route は `grounded generic default`
- planning / skeleton は opt-in only
- structural baseline は `single-pass + optional single repair 1回`
- `prompt_builder.py` simplification-first wording line は failed hypothesis / rollback 済み / kept diff なし / unchanged retry 禁止
- `pipeline.py` current-first source ordering / hint ownership triage も failed hypothesis / rollback 済み / kept diff なし / unchanged retry 禁止
- V1 は partial/non-worse
- V2 は still awkward variance
- V3 は mandatory gate fail
- G1 は no visible regression
- V3 run2 は title history-first
- V3 run3 は first section history-first
- pipeline triage stop report では V3 が 3/3 fail
- よって `pipeline.py` wording/hint/source-ordering 単独 triage も current winner ではない

このウインドウの役割:
- 状況把握
- source-of-truth の確認
- failed hypothesis の固定確認
- next owner がまだ 1 file に閉じるかの確認
- 次の prompt が implementation か management stop report かを決める
- prompt / docs の不整合があれば narrow に修正する
- production 実装は別ウインドウに委譲する

このウインドウでやること:
1. current source-of-truth と latest stop report が整合しているか確認する
2. `prompt_builder.py` と `pipeline.py` の failed hypotheses が rollback / do-not-retry に固定されているか確認する
3. current package で合法な next owner がまだ 1 file に閉じるか確認する
4. 閉じるなら next implementation prompt を 1 本だけ作る
5. 閉じないなら package block を明記し、次 decision を user に返す management stop report を作る

このウインドウでやらないこと:
- production code の実装
- `prompt_builder.py` failed hypothesis の unchanged retry
- `pipeline.py` failed hypothesis の unchanged retry
- multiple owner を同時に reopen した implementation prompt の作成
- `SECTION_SHADOW` reopen first
- `quality_guard.py` first
- repair acceptance reopen first
- sentence-final monotony line の main candidate 復帰
- fixed routing table 追加
- broad pipeline branch accumulation
- article-type 固定分岐の増設
- prompt accretion で押し切る方針

stop conditions:
- source-of-truth 同士が衝突しており、このウインドウでは決め切れない
- next owner が 1 file に閉じない
- current package の next prompt が multiple owner reopen 前提でしか成立しない
- same inconsistency を 3 回修正しても収束しない

最終成果物:
- current state summary
- failed hypothesis summary
- next owner summary または `not fixed` judgment
- next narrow hypothesis summary または `blocked pending user decision`
- current implementation prompt の keep / retire judgment
- 必要なら新しい prompt doc path
- AGENTS / WORKLOG 更新の要否

停止時は必ず次の形式:
### Stop Report
- Blocked item:
- What was confirmed:
- Inconsistency summary:
- Attempt 1:
- Attempt 2:
- Attempt 3:
- Next decision needed:
```
