# current_mainline_article_type_source_inventory_2026-04-25 PROGRESS

## Current Status

- Package status: completed
- Current phase: Phase 4 closeout
- Behavior change: no
- Generation run: no
- Product code change: no
- Fixture change: no
- Runtime decision:
  - Do not start UI quality validation with thin / mismatched source as if it were full-quality evidence.
  - Use the inventory decision before normal-mode UI validation.

## Phase Ledger

| Phase | Owner files | Changed responsibility | Behavior change | Verification | Result |
|---|---|---|---|---|---|
| 0 | `plan/current_mainline_article_type_source_inventory_2026-04-25/*` | new docs package | no | docs created | complete |
| 1 | README | article-type inventory | no | source evidence read from specified logs / fixture / WORKLOG | complete |
| 2 | README | use/replace/user-needed source decisions | no | decisions recorded | complete |
| 3 | EXECUTION_PROMPT | next normal-mode UI validation prompt | no | prompt recorded | complete |
| 4 | PROGRESS, `C:\tetie\WORKLOG.md` | closeout record | no | docs-only | complete |

## Evidence Summary

- `source_compression_length_adequacy_20260425-093131` already classified:
  - `industry_analysis`, `case_study`, `product_introduction`, `comparative_review`: mostly `thin_due_to_source`
  - `announcement`, `daily_story`, `explanatory_article`: acceptable for type-specific expectations
  - `company_introduction`: `acceptable_but_watch` with rich Kyoto source but short output tendency
- `multi_type_current_mainline_validation_20260425-013935` showed:
  - `bl-branding-company-overview`: `SYS_PIPELINE_FAILURE`
  - `bl-case-introduction`: `INP_SOURCE_CONTEXT_INSUFFICIENT`
  - `rerun-company-introduction-operational-source`: `INP_SOURCE_CONTEXT_INSUFFICIENT`
  - Kyoto URL company introduction rerun: OK
- `current_mainline_source_grounding_metric_correction_ui_validation_20260425-214032` showed:
  - Kyoto company introduction UI live attempts OK
  - case_study UI live source usable as runtime evidence but contaminated by encoded/mojibake title/source presentation, so not clean enough for next article-type quality validation
- `latest_generation_output.json` currently points to:
  - `article_type=branding`
  - `semantic_article_key=company_introduction`
  - Kyoto 4 URL source
  - runtime `OK`

## Final Inventory Judgment

- Start next UI quality validation with:
  - Kyoto company introduction source
  - existing announcement fixture
  - existing explanatory fixture
  - existing daily fixture only if synthetic daily is acceptable
  - existing branding values/stance fixture for non-company-introduction branding only
- Replace before full quality validation:
  - company introduction thin fixtures
  - baseline case study fixture
  - case study httpbingo/base64 UI source
  - industry analysis current fixture
  - comparative/product fixtures if the validation target is long-form depth

## Residual Risk

- Web candidate URLs are not normalized source packets yet.
- `daily_story` remains synthetic unless the user supplies real daily notes.
- `company_introduction` remains a watch item: source is rich, but successful bodies trend around 1000-1300 chars.
- This package does not decide any runtime fix.

## Next Action

- Use `EXECUTION_PROMPT.md` as the handoff prompt for the next normal-mode UI validation window.
- Before running full UI quality validation for case_study / comparative_review / product_introduction / industry_analysis, prepare clean source inputs in a separate source-prep step.
