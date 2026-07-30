# current_mainline_full_flow_regression_rerun_2026-04-26

## Objective

Rerun current mainline full-flow UI validation against restored historical log sources after the 2026-04-26 announcement, comparative_review, and explanatory_article fixes.

## Scope

- Use actual UI flow on `http://127.0.0.1:18080/`.
- Run active article types twice each:
  - company_introduction
  - product_introduction / service overview
  - announcement
  - case_study
  - comparative_review
  - explanatory_article
  - industry_analysis
  - daily_story
- Exclude non-company generic branding because production UI has no route for that article type.
- Validate image generation for two articles only:
  - company_introduction
  - comparative_review

## Source

Primary reuse:

- `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py`
- `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\source_inventory.json`
- `C:\tetie\notecode\logs\multi_type_current_mainline_validation_20260425-013935\`
- `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\`

Artifact root:

- `C:\tetie\notecode\logs\current_mainline_full_flow_regression_rerun_20260426-132807\`

## Non-Goals

- No product code changes.
- No prompt, threshold, repair, output guard, UI demote, or image generation implementation changes.
- Do not fix errors observed during the rerun in this package.
- Do not classify source caveats alone as runtime defects.
