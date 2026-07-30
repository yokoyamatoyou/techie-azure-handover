# EXECUTION_PROMPT

Use this prompt in the next implementation window.

```text
C:\tetie\notecode の pre-user-trial UI/runtime stability blocker を 1 owner / 1 narrow hypothesis で実装診断してください。

Mode:
- PLAN から開始し、必要最小の非破壊確認後に通常実装へ移る。
- product code 変更は owner scope 内だけ。
- full-flow validation は実行しない。
- timeout延長、sleep追加、例外握りつぶし、guard緩和、prompt/persona/source contract/algorithm/pipeline/image prompt変更は禁止。

Owner:
- C:\tetie\notecode\note\note_writer_app.py
- UI lifecycle / background task cleanup only.

Hypothesis:
- NiceGUI client/page detach 後も run_generation(), image auto progress, phase UI update, cleanup, ui.notify が古い element / slot を更新し、deleted client/slot traceback を発生させている。
- これが UI操作 timeout と 8080 listener loss の first blocker である。

Must read:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\current_mainline_pre_user_trial_ui_runtime_stability_2026-04-26\README.md
- C:\tetie\notecode\plan\current_mainline_pre_user_trial_ui_runtime_stability_2026-04-26\TASK.md
- C:\tetie\notecode\plan\current_mainline_pre_user_trial_ui_runtime_stability_2026-04-26\PROGRESS.md
- C:\tetie\notecode\plan\current_mainline_pre_user_trial_ui_runtime_stability_2026-04-26\ROLLBACK.md
- C:\tetie\notecode\logs\pre_user_trial_ui_validation_20260426-205318\manual_review_notes.md
- C:\tetie\notecode\logs\pre_user_trial_ui_validation_20260426-205318\summary.json
- C:\tetie\notecode\logs\pre_user_trial_ui_validation_20260426-205318\per_attempt_summary.jsonl
- C:\tetie\notecode\logs\pre_user_trial_ui_validation_20260426-205318\final_app_log_excerpt.txt
- C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md
- C:\tetie\notecode\ALGORITHM.md sections 4, 5, 12, 13

Allowed implementation direction:
- Add a bounded UI lifecycle safety boundary around UI element mutation from async generation/image/legal/cleanup paths.
- Prefer explicit client-alive / generation-token / detached-client early-exit semantics.
- Preserve article result persistence and fail-open image contract.
- Do not convert real failures into silent success.
- Do not move responsibilities into split modules.

Required checks:
- py_compile for note_writer_app.py.
- Focused pytest for note_writer_app / current_mainline UI helper tests only.
- Static log-shape check or targeted unit test proving detached UI mutation does not call NiceGUI element setters after client release.
- No UI server startup unless the implementation window explicitly asks for one after unit/static checks.

Stop conditions:
- If fix requires touching prompt, algorithm, quality/output guard, pipeline, blog_image_auto, or image prompt: stop.
- If only viable fix is timeout/sleep/exception swallowing: stop.
- If root cause cannot be separated from harness-only selector drift: stop and report.
- If more than one owner is required: choose note_writer_app.py lifecycle owner first or stop with reason.
```

