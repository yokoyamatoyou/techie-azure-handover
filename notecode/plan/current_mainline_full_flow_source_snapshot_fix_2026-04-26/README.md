# current_mainline_full_flow_source_snapshot_fix_2026-04-26

## Objective

Fix the source reconstruction issue that stopped `current_mainline_full_flow_regression_rerun_2026-04-26` before generation.

The fix is validation-only: freeze full-flow rerun source packets into a canonical manifest and make the next rerun reconstruct sources from that manifest instead of moving files such as `C:\tetie\notecode\logs\latest_generation_output.json`.

## Scope

- Create `source_snapshot_manifest.json` as the only source input for the next full-flow rerun.
- Add a manifest-driven wrapper around the existing log-source UI regression harness.
- Validate only with `--reconstruct-only`.
- Do not restart article generation or image generation in this package.

## Source Snapshot Policy

- Every active record has `moving_target=false`.
- `company_introduction_kyoto_latest_log` uses the fixed Kyoto 4 URL packet from:
  - `C:\tetie\notecode\logs\current_mainline_source_grounding_metric_correction_ui_validation_20260425-214032\ui_live\case1_kyoto_company_introduction_equivalent\attempt_1\latest_generation_output.json`
- `bl-branding-values-stance` stays excluded because production UI has no generic non-company branding route.

## Non-Goals

- Product code changes
- Prompt changes
- Threshold changes
- Repair changes
- UI changes
- Output guard changes
- Image generation implementation changes
- Article or image generation rerun
