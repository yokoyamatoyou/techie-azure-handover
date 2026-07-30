# current_mainline_post_full_flow_issue_triage_2026-04-26 EXECUTION_PROMPT

```text
C:\tetie\notecode の current mainline post-full-flow triage 後、最初の1件だけ実装してください。

Package:
C:\tetie\notecode\plan\current_mainline_announcement_fail_closed_ux_restore_2026-04-26\

Read first:
- C:\tetie\notecode\plan\current_mainline_post_full_flow_issue_triage_2026-04-26\README.md
- C:\tetie\notecode\plan\current_mainline_post_full_flow_issue_triage_2026-04-26\PROGRESS.md
- C:\tetie\notecode\plan\current_mainline_fail_closed_ux_policy_2026-04-25\PROGRESS.md
- C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\per_attempt_summary.jsonl

Target:
- Fix only `bl-announcement-spec-change` 2/2 `input_required_block`.
- Treat it as a fail-closed UX classification regression, not a prompt/threshold/repair problem.
- Expected behavior: route-matched announcement, source-caveat-free, body exists, no internal leakage, warning-only blocked output should surface according to the existing review-required draft policy instead of being hidden as input-required.

Constraints:
- 1 issue = 1 narrow hypothesis = 1 owner scope.
- Do not change thresholds.
- Do not add prompt text.
- Do not add repair attempts.
- Do not expand UI demote policy beyond the existing announcement-eligible contract.
- Do not classify source-thin or harness cases as fixed by this package.
- Stop after 3 failed correction attempts and report.

Required validation:
- Focused unit tests for the announcement fail-closed classification.
- Existing UI result adapter / runner / regression tests.
- One UI replay or artifact-based validation proving announcement changes from `input_required_block` to the intended review-required draft state.
- Verify branding route mismatch, comparative harness failure, explanatory regression, product source caveat, and daily synthetic caveat remain separately classified.
```

