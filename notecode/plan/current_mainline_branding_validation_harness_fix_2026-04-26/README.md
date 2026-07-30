# current_mainline_branding_validation_harness_fix_2026-04-26 README

## Objective

- Implement the validation-harness-only follow-up from `current_mainline_branding_route_mismatch_diagnosis_2026-04-26`.
- Prevent `bl-branding-values-stance` from being recorded as `non-company branding / values stance` while the harness selects UI target `自社・会社紹介`.
- Keep product code, prompts, thresholds, repair behavior, and announcement work unchanged.

## Source Of Truth

- Diagnosis package:
  - `C:\tetie\notecode\plan\current_mainline_branding_route_mismatch_diagnosis_2026-04-26\`
- Validation artifact root:
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\`
- Harness owner:
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py`

## Finding

Production UI route mapping has no generic non-company `branding` journey route.

Available introduce routes:

- `introduce/company` -> `article_type=branding`, `semantic_article_key=company_introduction`
- `introduce/product_service` -> `article_type=branding`, `semantic_article_key=product_introduction`
- compatibility introduce routes cover `activity_introduction` and `recruit_culture`

There is no production UI route that maps a selected journey to `semantic_article_key=branding`.

## Change

- Mark `bl-branding-values-stance` as `excluded_from_ui_full_flow` in the validation harness.
- Clear executable UI controls for that case:
  - `controls.purpose=""`
  - `controls.target=""`
- Clear `semantic_article_key_expected` for that excluded case.
- Preserve source reconstruction and historical evidence, but annotate it as route-mismatch history.
- Filter excluded cases out before UI attempts are executed.
- Regenerate source inventory with `--reconstruct-only`; no UI generation was run.

## Classification

- Primary: `validation harness selected wrong UI path`
- Resolution: excluded from full-flow UI article-type validation because current production UI has no generic non-company branding route.
- Not changed:
  - product route map
  - `note_writer_app.py`
  - `current_mainline_runner.py`
  - `newalgorithm_pipeline\input_contract.py`
  - `simple_note_pipeline\pipeline.py`
  - prompts / thresholds / repair
  - announcement fix

## Updated Artifacts

- `source_inventory.json`
  - `bl-branding-values-stance.article_type_for_ui=excluded`
  - `bl-branding-values-stance.semantic_article_key_expected=""`
  - `bl-branding-values-stance.validation_status=excluded_from_ui_full_flow`
  - `bl-branding-values-stance.controls.purpose=""`
  - `bl-branding-values-stance.controls.target=""`
- `ui_live\bl-branding-values-stance\source_reconstructed_from_log.json`
  - includes `validation_status`, `exclusion_reason`, and `route_mismatch_annotation`
- `historical_baseline.json`
  - includes the exclusion status and reason for the historical case

## Non-Goals

- Do not make a generic branding production route.
- Do not reinterpret old body 0 attempts as source shortage.
- Do not rerun full UI generation for the excluded case.
- Do not change product behavior to satisfy validation harness coverage.
