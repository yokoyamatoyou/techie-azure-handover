# current_mainline_branding_validation_harness_fix_2026-04-26 ROLLBACK

## Baseline

- Product runtime files are not changed.
- Prompt / threshold / repair / guard / UI implementation are not changed.
- Announcement fix remains closed.

## Rollback Boundary

Rollback may remove or supersede only:

- `C:\tetie\notecode\plan\current_mainline_branding_validation_harness_fix_2026-04-26\`
- the harness edits in:
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py`
- regenerated validation artifact annotations in:
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\source_inventory.json`
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\historical_baseline.json`
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\ui_live\bl-branding-values-stance\source_reconstructed_from_log.json`
- the matching `C:\tetie\WORKLOG.md` entry

## Do Not Roll Back

- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- announcement source contract activation work
- route mismatch diagnosis package

## Do Not Retry By Editing

- Do not add generic branding route to product UI as part of this package.
- Do not change prompt, threshold, or repair to make the old case pass.
- Do not add article-type-specific branches to `pipeline.py`.
- Do not reclassify old body 0 as source shortage.

## Safe Reversal

If this exclusion is superseded by a real production generic branding route later, create a new validation package that reintroduces a matching UI route and expected semantic key together.
