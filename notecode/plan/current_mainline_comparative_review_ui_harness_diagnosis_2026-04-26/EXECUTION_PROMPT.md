# Next Prompt: comparative_review validation harness only

Use this only if implementation is requested after this diagnosis.

```text
作業場所: C:\tetie\notecode
現在日時: 2026-04-26 JST

目的:
- `current_mainline_comparative_review_ui_harness_diagnosis_2026-04-26` の診断結果を受け、comparative_review の UI harness failure を validation harness owner だけで修正する。
- product code / prompt / threshold / repair / comparative runtime contract は変更しない。

必読:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\current_mainline_comparative_review_ui_harness_diagnosis_2026-04-26\README.md
- C:\tetie\notecode\plan\current_mainline_comparative_review_ui_harness_diagnosis_2026-04-26\PROGRESS.md
- C:\tetie\WORKLOG.md

Owner:
- C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py

Allowed changes:
- For `bl-comparative-selection-criteria`, use a UI-accepted writer role such as `編集担当として語る`.
- Or add harness-side preflight classification that records `validation_bubble_blocked_action` when `確認へ` is disabled, instead of generic `UI_HARNESS_OPERATION_ERROR`.

Forbidden changes:
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- prompts
- thresholds
- repair logic
- comparative runtime contract

Focused rerun:
- C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py --case-ids bl-comparative-selection-criteria --attempts 1,2

Acceptance:
- The comparative attempts no longer fail at `_click_button("確認へ")`.
- If generation starts, classify the resulting generation artifact separately from the old harness failure.
- Product code remains untouched.
```

