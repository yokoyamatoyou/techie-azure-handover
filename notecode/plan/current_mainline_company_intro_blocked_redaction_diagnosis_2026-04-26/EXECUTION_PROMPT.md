# EXECUTION_PROMPT

Use this only for the next minimal validation window after the current implementation is checked.

```text
C:\tetie\notecode の company_introduction review_required_draft snapshot mismatch fix を最小確認してください。

制約:
- UI server を勝手に起動しない。既存の user 指示がある場合のみ使用する。
- full-flow validation を実行しない。
- prompt / persona / source contract / algorithm / threshold / repair count / quality_guard / output_guard / pipeline / blog_image_auto を変更しない。
- 1 issue = 1 narrow hypothesis = 1 owner scope。

確認対象:
- review_required_draft の latest_generation_output.json が body-backed full_text を保持すること
- blocked_output_redacted=false であること
- runtime_reason_code=SYS_QUALITY_WARNINGS_UNRESOLVED は保持されること
- output_guard blocked / warning_fail_closed / soft_warnings は pipeline_check に残ること
- true blocked_generation は従来通り redacted されること

最初に読む:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\current_mainline_company_intro_blocked_redaction_diagnosis_2026-04-26\README.md
- C:\tetie\notecode\plan\current_mainline_company_intro_blocked_redaction_diagnosis_2026-04-26\PROGRESS.md
- C:\tetie\notecode\logs\pre_user_trial_ui_runtime_validation_rerun_20260426-214042\

完了報告:
- product code 変更有無
- UI server 起動有無
- full-flow validation 実行有無
- review_required_draft redaction mismatch が解消したか
- copy / legal representative checks へ進めるか
```

