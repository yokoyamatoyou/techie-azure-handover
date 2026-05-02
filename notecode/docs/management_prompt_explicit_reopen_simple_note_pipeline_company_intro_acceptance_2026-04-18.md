# management prompt explicit reopen simple note pipeline company intro acceptance 2026-04-18

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
- C:\tetie\notecode\docs\pipeline_current_first_triage_stop_report_2026-04-18.md
- C:\tetie\notecode\docs\management_stop_report_after_failed_pipeline_current_first_triage_2026-04-18.md
- C:\tetie\notecode\docs\parked_package_prompt_naturalness_recovery_2026-04-18.md

今回の依頼種別:
- management prompt
- `MANAGEMENT_FIXED_REOPEN_SIMPLE_NOTE_PIPELINE_COMPANY_INTRO_ACCEPTANCE`
- implementation prompt ではない

今回の実施範囲:
- explicit reopen decision を source-of-truth に同期する
- reopen owner / narrow hypothesis / do-not / stop conditions を `1 owner / 1 hypothesis` に閉じる
- 次に使う implementation prompt を作成または確認する
- production code は実装しない

current fixed judgment:
- current package は `naturalness_recovery_2026-04-07`
- current success path は維持する
- default route は `grounded generic default`
- planning / skeleton は opt-in only
- structural baseline は `single-pass + optional single repair 1回`
- `prompt_builder.py` simplification-first wording line は failed / rollback 済み / unchanged retry 禁止
- `newalgorithm_pipeline/pipeline.py` current-first triage も failed / rollback 済み / unchanged retry 禁止
- explicit user reopen exception として、`simple_note_pipeline/pipeline.py` owner の narrow reopen を許可する
- reopen scope は downstream repair acceptance / scope gating に閉じる
- `SECTION_SHADOW` first / `quality_guard.py` first / fixed routing / prompt accretion は依然 do-not

このウインドウでやること:
1. explicit reopen decision を package docs に反映する
2. next owner を `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` に固定する
3. next narrow hypothesis を company intro opener の history-first drift を acceptance / scope gating で fail-closed する line に固定する
4. implementation prompt を 1 本だけ current prompt として作る

このウインドウでやらないこと:
- production code の実装
- `prompt_builder.py` retry prompt の再作成
- `newalgorithm_pipeline/pipeline.py` current-first triage の再作成
- multiple owner reopen

最終報告で必ず示すこと:
1. 読んだ正本ファイル
2. 読んだ result docs
3. current situation summary
4. next owner
5. next narrow hypothesis
6. 更新した docs
7. 新しく作った prompt の path
8. AGENTS / WORKLOG 更新の要否
9. production 実装はしていないこと
```
