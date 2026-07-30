# current_mainline_fail_closed_ux_policy_2026-04-25 EXECUTION_PROMPT

Start in `C:\tetie\notecode`.

Read:

1. `C:\tetie\notecode\AGENTS.md`
2. `C:\tetie\AGENTS.md`
3. `C:\tetie\notecode\plan\current_mainline_fail_closed_ux_policy_2026-04-25\README.md`
4. `C:\tetie\notecode\plan\current_mainline_fail_closed_ux_policy_2026-04-25\TASK.md`
5. `C:\tetie\notecode\plan\current_mainline_fail_closed_ux_policy_2026-04-25\PROGRESS.md`
6. `C:\tetie\notecode\plan\current_mainline_fail_closed_ux_policy_2026-04-25\ROLLBACK.md`
7. `C:\tetie\notecode\plan\current_mainline_article_type_ui_quality_validation_2026-04-25\PROGRESS.md`
8. `C:\tetie\notecode\plan\current_mainline_fingerprint_policy_resolution_2026-04-25\PROGRESS.md`
9. `C:\tetie\notecode\plan\current_mainline_source_grounding_metric_correction_2026-04-25\PROGRESS.md`
10. `C:\tetie\WORKLOG.md`

Implement only this narrow hypothesis:

- In `C:\tetie\notecode\note\note_writer_app.py`, classify eligible `SYS_QUALITY_WARNINGS_UNRESOLVED` blocked output as `review_required_draft`.
- Render the existing title/body into UI text areas with warning copy.
- Keep telemetry non-success and persist with `blocked=True`.
- Do not set runtime reason to `OK`.
- Do not change output guard thresholds, prompts, repair behavior, source contracts, or leakage checks.

Stop before product changes if implementation needs another product owner such as `current_mainline_ui_result_adapter.py`.

Run:

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_result_adapter.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
```
