# current_mainline_post_full_flow_issue_triage_2026-04-26 ROLLBACK

## Baseline

- Runtime files are not changed.
- This package is docs-only.
- Current success path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Rollback Boundary

Remove only:

- `C:\tetie\notecode\plan\current_mainline_post_full_flow_issue_triage_2026-04-26\`

## Do Not Roll Back

- current mainline runtime files
- GPT Image 2 implementation
- fail-closed UX implementation
- source grounding metric correction
- existing validation packages
- `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\`
- AGENTS files

## Do Not Retry By Editing

- Do not relax guards or thresholds.
- Do not add prompt text.
- Do not increase repair count.
- Do not change product code inside this package.
- Do not expand UI demotion/display policy inside this package.
- Do not classify source-thin or UI harness cases as fixed by the announcement selection.

