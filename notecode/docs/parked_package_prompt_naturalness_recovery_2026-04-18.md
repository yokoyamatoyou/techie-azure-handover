# parked package prompt naturalness recovery 2026-04-18

## Status

- superseded after explicit reopen decision
- current startup prompt としては使わない
- historical park snapshot として保持する

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

current state:
- current package `naturalness_recovery_2026-04-07` は parked
- current success path は keep
- `prompt_builder.py` simplification-first は failed / rollback 済み / unchanged retry 禁止
- `pipeline.py` current-first triage も failed / rollback 済み / unchanged retry 禁止
- next owner は not fixed
- next narrow hypothesis も not fixed

instruction:
- この package では、新しい implementation を開始しない
- production code を編集しない
- reopen は user が明示的に別 owner または別 package 方針を指定した場合だけ行う
- 現状確認や handoff 整理が必要なら docs-only で行う

stop rule:
- explicit reopen decision がなければ、この package は parked のまま維持する
```
