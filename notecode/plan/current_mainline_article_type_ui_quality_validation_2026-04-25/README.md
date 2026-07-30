# current_mainline_article_type_ui_quality_validation_2026-04-25 README

## Objective

- Validate current mainline article-type output quality through the actual UI.
- Use only sources approved by `current_mainline_article_type_source_inventory_2026-04-25`.
- Do not change product code, prompt, thresholds, repair count, repair trigger, output guard, or UI.

## Scope

Run:

- `company_introduction`: Kyoto 4 URLs
- `announcement`: existing spec-change fixture
- `explanatory_article`: existing misread-metric fixture
- `branding`: existing values/stance fixture only if it stays non-company-introduction
- `daily_story`: existing synthetic daily fixture, not final production-quality evidence

Do not run:

- `case_study`
- `comparative_review`
- `product_introduction`
- `industry_analysis`

## Artifact

- `C:\tetie\notecode\logs\current_mainline_article_type_ui_quality_validation_20260425-223000\`

## Non-Goals

- No product implementation fix.
- No prompt / threshold / repair / UI demote change.
- No source prep for replace-needed article types.
- No AGENTS routing update.
