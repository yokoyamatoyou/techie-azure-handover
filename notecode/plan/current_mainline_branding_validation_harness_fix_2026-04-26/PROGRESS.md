# current_mainline_branding_validation_harness_fix_2026-04-26 PROGRESS

## Status

Completed on 2026-04-26 JST.

## Scope

- Product code change: no
- Files under `C:\tetie\notecode\note\`: unchanged
- Prompt / threshold / repair change: no
- Announcement fix reopened: no
- Owner: validation harness only

## Route Availability Check

Production UI route mapping was inspected in `current_mainline_runner.py`.

Available `introduce` routes:

| ui_journey | article_type | semantic_article_key |
|---|---|---|
| `introduce/company` | `branding` | `company_introduction` |
| `introduce/product_service` | `branding` | `product_introduction` |
| `introduce/activity_project` | `branding` | `activity_introduction` |
| `introduce/recruit_culture` | `branding` | `recruit_culture` |

There is no generic non-company `branding` UI journey route. The harness cannot truthfully validate `semantic_article_key=branding` through production UI selection.

## Changes

Validation harness:

- `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py`
  - Added `EXCLUDED_UI_FULL_FLOW_CASES`.
  - Marked `bl-branding-values-stance` as `excluded_from_ui_full_flow`.
  - Cleared executable route controls for that case.
  - Added `route_mismatch_annotation` preserving the prior wrong path:
    - previous label: `non-company branding / values stance`
    - previous expected key: `branding`
    - previous controls: `会社・サービスの紹介記事を書く` -> `自社・会社紹介`
    - actual route: `branding/company_introduction`
  - Filtered non-active cases before `_run_attempt()`.

Regenerated artifacts:

- `source_inventory.json`
- `historical_baseline.json`
- `ui_live\bl-branding-values-stance\source_reconstructed_from_log.json`

Command:

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py --reconstruct-only
```

Result:

- Exit code 0.
- No UI generation was run.

## Verification

`source_inventory.json` now records:

- `case_id=bl-branding-values-stance`
- `article_type_target=non-company branding / values stance`
- `article_type_for_ui=excluded`
- `semantic_article_key_expected=""`
- `validation_status=excluded_from_ui_full_flow`
- `controls.purpose=""`
- `controls.target=""`
- `exclusion_reason=Production UI has no generic non-company branding route...`

`source_reconstructed_from_log.json` now records:

- `validation_status=excluded_from_ui_full_flow`
- `exclusion_reason`
- `route_mismatch_annotation.classification=validation_harness_selected_wrong_ui_path`

`historical_baseline.json` now records:

- `validation_status=excluded_from_ui_full_flow`
- the same exclusion reason

## Final Judgment

The harness no longer validates `bl-branding-values-stance` as non-company branding while selecting `自社・会社紹介`.

The old 2/2 body 0 artifacts remain historical route-mismatch evidence and are not treated as source shortage, announcement regression, prompt failure, threshold failure, repair failure, or product route-map failure.

## Tests

- Reconstruct-only harness run passed.
- No pytest run because this package modifies validation artifact code and docs only.
