# current_mainline_article_type_source_inventory_2026-04-25 ROLLBACK

## Baseline

- Runtime mainline remains unchanged:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current planning source of truth remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- This package is an inventory / handoff package only and does not replace current source of truth.

## Rollback Boundary

- Rollback is docs-only:
  - remove or supersede `C:\tetie\notecode\plan\current_mainline_article_type_source_inventory_2026-04-25\`
  - remove or supersede the matching `C:\tetie\WORKLOG.md` entry
- No product code, tests, fixture files, prompt files, thresholds, repair logic, or UI files are part of this package rollback.

## Do Not Retry

- Do not rerun generation from this package.
- Do not treat source-thin outputs as runtime regressions.
- Do not fix source problems by prompt accretion.
- Do not replace fixtures silently with web candidates.
- Do not use mojibake / encoded-title case_study source as a clean quality-validation source.
- Do not reopen frozen architecture or completed reference packages.

## Stop Boundary

- A next step requires changing product code.
- A next step requires source normalization beyond docs.
- A next step starts UI generation before source replacement decisions are applied.
- A next step attempts to relax repair / threshold / quality guard behavior.
