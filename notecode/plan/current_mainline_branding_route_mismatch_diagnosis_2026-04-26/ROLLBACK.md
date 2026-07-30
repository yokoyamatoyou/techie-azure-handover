# current_mainline_branding_route_mismatch_diagnosis_2026-04-26 ROLLBACK

## Baseline

- Runtime files are not changed.
- Prompt / threshold / repair / guard / UI implementation are not changed.
- Announcement fix remains closed.
- Current success path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Rollback Boundary

Remove or supersede only:

- `C:\tetie\notecode\plan\current_mainline_branding_route_mismatch_diagnosis_2026-04-26\`
- the matching `C:\tetie\WORKLOG.md` entry

## Do Not Roll Back

- `current_mainline_announcement_source_contract_activation_2026-04-26`
- `current_mainline_log_source_ui_regression_2026-04-26`
- current mainline runtime files
- product UI route mapping
- input contract resolver
- source fit logic
- company introduction source contract behavior
- `pipeline.py`
- AGENTS files

## Do Not Retry By Editing

- Do not adjust product code.
- Do not relax guards or thresholds.
- Do not change prompts.
- Do not increase repair count.
- Do not add article-type-specific branching.
- Do not change UI demotion/display policy.
- Do not reopen announcement work.

## Safe Reversal

This package is docs-only. Reversal is limited to removing the package directory and its WORKLOG entry, or marking the package superseded by a later validation-harness package.
