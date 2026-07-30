# current_mainline_announcement_fail_block_diagnosis_2026-04-26 EXECUTION_PROMPT

```text
C:\tetie\notecode の announcement fail-block diagnosis 後、source contract activation の narrow fix だけを実装してください。

Package:
C:\tetie\notecode\plan\current_mainline_announcement_source_contract_activation_2026-04-26\

Read first:
- C:\tetie\notecode\plan\current_mainline_announcement_fail_block_diagnosis_2026-04-26\README.md
- C:\tetie\notecode\plan\current_mainline_announcement_fail_block_diagnosis_2026-04-26\PROGRESS.md
- C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\ui_live\bl-announcement-spec-change\attempt_1\attempt_summary.json
- C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\ui_live\bl-announcement-spec-change\attempt_2\attempt_summary.json
- C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\ui_live\bl-announcement-spec-change\attempt_1\latest_generation_output.json
- C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\ui_live\bl-announcement-spec-change\attempt_2\latest_generation_output.json

Owner:
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

Target:
- Make announcement source contract activate from fallback source sentences when required slots are discoverable from source text.
- Ensure FAQ facts become bounded `source_grounding_items` / `must_cover` inputs:
  - `承認者の再設定`
  - `通知先の確認`
  - `下書き保存`
  - `差し戻し通知`
  - `公開日時の再指定`

Constraints:
- 1 issue = 1 narrow hypothesis = 1 owner scope.
- Do not change thresholds.
- Do not add prompt text.
- Do not add repair attempts.
- Do not change UI demote behavior.
- Do not mark warning drafts as success.
- Do not edit `note_writer_app.py` unless diagnosis proves the app classifier is wrong; current diagnosis says it is not the first owner.
- Do not edit `prompt_builder.py`.

Required validation:
- Focused unit tests for announcement source contract activation from the two source docs.
- Artifact-based check that FAQ facts enter `source_grounding_items` / `must_cover`.
- Verify app classification remains `review_required_draft`, not `success`.
- Verify non-announcement article types are unchanged.
- Run owner-local tests and shared current-mainline checks.
```

