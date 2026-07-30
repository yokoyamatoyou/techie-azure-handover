# kotomigaki_report_accessibility_audit_2026-06-13 ROLLBACK

## Baseline

This package is docs-first and audit-first. Creating this package does not change product behavior.

Initial files added:

- `plan\kotomigaki_report_accessibility_audit_2026-06-13\README.md`
- `plan\kotomigaki_report_accessibility_audit_2026-06-13\TASK.md`
- `plan\kotomigaki_report_accessibility_audit_2026-06-13\PROGRESS.md`
- `plan\kotomigaki_report_accessibility_audit_2026-06-13\ROLLBACK.md`
- `plan\kotomigaki_report_accessibility_audit_2026-06-13\EXECUTION_PROMPT.md`
- `plan\kotomigaki_report_accessibility_audit_2026-06-13\artifacts\README.md`

## Product Code Boundary

Audit phases should not modify product code.

Allowed without extra approval:

- artifact notes under this package
- final audit report under `artifacts\`
- `PROGRESS.md` updates
- `WORKLOG.md` update recording audit package creation or audit completion

Allowed only for audit blockers:

- narrow fix for UI startup failure
- narrow fix for Markdown generation failure
- narrow fix for a test-only typo that blocks the audit

Before any product code change:

1. Create a snapshot under:

```text
C:\tetie\aio2-main\outputs\snapshots\YYYYMMDD_HHMMSS-kotomigaki-report-accessibility-audit
```

2. Record target files in `PROGRESS.md`
3. Limit owner files to the smallest possible set

## Rollback Method

If only docs/artifacts were added:

- Remove this package directory if the user asks to discard it
- Remove the matching `WORKLOG.md` entry if the user asks for a clean rollback

If product code was changed:

- Do not use `git reset --hard`
- Restore only the changed files from the timestamp snapshot
- Re-run the relevant Compile Gate and Targeted Regression Gate
- Record rollback evidence in `PROGRESS.md`

## Do Not Roll Back

- archived analysis history
- unrelated snapshots
- user-created outputs
- data under `data\archives\`
- unrelated files modified by another process or user

## Stop Conditions

Stop and report instead of editing further if:

- rollback target is ambiguous
- failure requires score formula or legal meaning changes
- external paid API calls are required to proceed
- the same owner area failed 3 repair attempts
- local/private URL scanning restrictions block fixture-based live testing
