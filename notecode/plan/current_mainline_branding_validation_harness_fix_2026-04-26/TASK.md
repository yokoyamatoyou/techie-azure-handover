# current_mainline_branding_validation_harness_fix_2026-04-26 TASK

## Global Rules

- Owner is validation harness only.
- Do not modify files under `C:\tetie\notecode\note\`.
- Do not change product code, prompts, thresholds, repair, or announcement work.
- Do not add article-type-specific branches to `pipeline.py`.
- If production UI has no generic branding route, exclude or relabel the validation case instead of changing product code.

## Phase Map

| Phase | Scope | Exit |
|---|---|---|
| 0 | package setup | README / TASK / PROGRESS / ROLLBACK exist |
| 1 | route availability check | production UI route map inspected |
| 2 | harness patch | excluded case cannot execute with `target=自社・会社紹介` |
| 3 | lightweight regeneration | `--reconstruct-only` updates source inventory annotations |
| 4 | verification | inventory and reconstructed packet show exclusion |
| 5 | closeout | WORKLOG updated |

## Implementation Decision

Generic non-company `branding` is not available as a production UI journey route.

Therefore:

- Do not map this case to another product route.
- Exclude `bl-branding-values-stance` from full-flow UI article-type validation.
- Keep historical source and failure artifacts as diagnostic evidence only.

## Acceptance Criteria

- The harness no longer reports an executable `non-company branding` case with `controls.target=自社・会社紹介`.
- Excluded case has:
  - `validation_status=excluded_from_ui_full_flow`
  - `article_type_for_ui=excluded`
  - `semantic_article_key_expected=""`
  - blank `controls.purpose` and `controls.target`
- UI run loop filters the excluded case before attempts.
- `source_inventory.json`, `source_reconstructed_from_log.json`, and `historical_baseline.json` contain exclusion annotations.
- Product files under `C:\tetie\notecode\note\` are unchanged.

## Checks

Run:

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py --reconstruct-only
```

Then inspect:

- `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\source_inventory.json`
- `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\ui_live\bl-branding-values-stance\source_reconstructed_from_log.json`
- `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\historical_baseline.json`

No pytest is required because no product code is changed.
