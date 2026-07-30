# EXECUTION_PROMPT

Start in Plan mode.

You are working in `C:\tetie\notecode`.

Read first:

1. `C:\tetie\notecode\plan\current_mainline_branding_route_mismatch_diagnosis_2026-04-26\README.md`
2. `C:\tetie\notecode\plan\current_mainline_branding_route_mismatch_diagnosis_2026-04-26\TASK.md`
3. `C:\tetie\notecode\plan\current_mainline_branding_route_mismatch_diagnosis_2026-04-26\PROGRESS.md`
4. `C:\tetie\notecode\plan\current_mainline_branding_route_mismatch_diagnosis_2026-04-26\ROLLBACK.md`
5. `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\source_inventory.json`
6. `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\per_attempt_summary.jsonl`
7. `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py`

Goal:

- Plan the next narrow implementation for `bl-branding-values-stance` route mismatch.
- Owner must be validation harness only.
- Fix or relabel the validation case path so a case expected as `semantic_article_key=branding` is not replayed through UI target `自社・会社紹介`, which resolves to `company_introduction`.

Hard constraints:

- Do not change product code.
- Do not change prompts.
- Do not change thresholds.
- Do not change repair.
- Do not change `pipeline.py`.
- Do not change `note_writer_app.py`.
- Do not change `current_mainline_runner.py`.
- Do not change `newalgorithm_pipeline\input_contract.py`.
- Do not reopen announcement work.
- Do not treat this as source shortage.

Required diagnosis to preserve:

- Primary classification: `validation harness selected wrong UI path`.
- Secondary classification: runtime route mismatch into `branding/company_introduction`.
- Body 0 is explained by company-introduction route redaction/fail-closed behavior after wrong route selection.

Implementation target:

- Validation script / validation case data only.
- Either:
  - make the selected UI path and expected semantic key agree, or
  - relabel/exclude the case from non-company branding validation if current production UI has no generic non-company branding route.

Acceptance criteria:

- The harness no longer reports a generic `non-company branding / values stance` case while selecting `target=自社・会社紹介`.
- No product code changes.
- No prompt / threshold / repair changes.
- New or updated validation evidence clearly separates harness route mismatch from source adequacy.
- WORKLOG is updated.
