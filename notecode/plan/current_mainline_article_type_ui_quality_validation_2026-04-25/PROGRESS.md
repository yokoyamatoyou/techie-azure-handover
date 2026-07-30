# current_mainline_article_type_ui_quality_validation_2026-04-25 PROGRESS

## Current Status

- Package status: completed
- Execution mode: normal actual UI validation
- UI server: `HEADLESS=1`, `PORT=18080`, `C:\tetie\notecode\.venv\Scripts\python.exe -m note.note_writer_app`
- Artifact root: `C:\tetie\notecode\logs\current_mainline_article_type_ui_quality_validation_20260425-223000\`
- Product code change: no
- Prompt / threshold / repair / UI change: no
- AGENTS update: no routing change, not updated

## Source Precheck

| Case | Source | Fit | Thickness | Decision |
|---|---|---:|---:|---|
| `company_introduction_kyoto_4urls` | Kyoto top / profile / history / service URLs | fit | rich | run |
| `bl-announcement-spec-change` | existing spec-change fixture | fit | sufficient | run |
| `bl-explanatory-misread-metric` | existing misread-metric fixture | fit | sufficient, thin watch | run |
| `bl-branding-values-stance` | existing values/stance fixture | fit only as non-company-introduction stance branding | sufficient | attempted, then excluded from quality judgment because UI journey resolved to `company_introduction` |
| `bl-daily-learning-log-grounded` | existing synthetic daily fixture | fit | sufficient | run, synthetic caveat |

Skipped before execution:

- `case_study`
- `comparative_review`
- `product_introduction`
- `industry_analysis`

Reason: source inventory already judged clean source prep is required before full quality validation.

## Attempt Results

| Case | Attempts | Runtime result | Body chars | Evaluation | Classification |
|---|---:|---|---:|---|---|
| `company_introduction_kyoto_4urls` | 2 | 2/2 fail-closed, `SYS_QUALITY_WARNINGS_UNRESOLVED` | 974 / 881 | `fail_unexpected` | runtime quality guard / source-grounding reflection issue on rich source |
| `bl-announcement-spec-change` | 2 | 2/2 fail-closed, `SYS_QUALITY_WARNINGS_UNRESOLVED` | 533 / 292 | `fail_unexpected` | runtime quality guard issue on sufficient source |
| `bl-explanatory-misread-metric` | 2 | 2/2 `OK` | 1672 / 1905 | `acceptable` | usable UI quality evidence |
| `bl-branding-values-stance` | 2 | 2/2 fail-closed, `SYS_PIPELINE_FAILURE` | 0 / 0 | excluded | UI route mismatch: resolved to `semantic_article_key=company_introduction`, not non-company-introduction branding |
| `bl-daily-learning-log-grounded` | 2 | 2/2 fail-closed, `SYS_QUALITY_WARNINGS_UNRESOLVED` | 657 / 856 | `fail_unexpected` | runtime fail-closed observed; synthetic daily, not final production-quality judgment |

## Observations

- Internal-term leakage:
  - UI visible leakage: none across collected attempts
  - body leakage: none across collected attempts
- Source outside claim:
  - no explicit outside-claim evidence recorded in collected bodies
- `explanatory_article` is the only clear pass in this run.
- `company_introduction` and `announcement` failures should not be explained away as source mismatch or thin source.
- `daily_story` failure is recorded, but final production-quality judgment remains blocked by synthetic source status.
- `branding` cannot be judged from this run because the actual UI route converted the stance/value source into `company_introduction`; this is a route/precondition mismatch, not a content-quality verdict for branding.

## Verification

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - `144 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - `260 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_newalgorithm_phase06_logging_compat.py -q`
  - `33 passed`

## Server Closeout

- UI server stopped.
- `Get-NetTCPConnection -LocalPort 18080 -State Listen` after stop:
  - no listener

## Final Judgment

- Validation completed for allowed sources where the UI route remained valid.
- Product code / prompt / threshold / repair / UI were not changed.
- Unexpected fail-closed outcomes are runtime-quality observations, except `branding`, which is classified as UI route mismatch against the requested non-company-introduction branding condition.
