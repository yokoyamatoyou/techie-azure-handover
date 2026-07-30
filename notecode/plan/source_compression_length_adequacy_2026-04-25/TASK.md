# source_compression_length_adequacy_2026-04-25 TASK

## Global Rules

- First action is audit / measurement.
- `single-pass + optional single repair 1回` remains the baseline.
- `1 issue = 1 narrow hypothesis = 1 owner scope`.
- If an implementation fix is considered, choose only one candidate and add focused coverage.
- Same error may be retried up to 3 times in one phase. Stop after the third same error and report cause, attempted fixes, and residual risk.
- Green phases continue without waiting for user confirmation.

## Phase Map

| Phase | Scope | Owner Files | Behavior Change | Exit |
|---|---|---|---|---|
| 0 | read / baseline / package creation | plan package only | no | required docs read and baseline tests recorded |
| 1 | previous validation metric extraction | logs output only | no | previous metrics json/md written |
| 2 | audit runner | plan package or logs runner, generated logs | no runtime change | 8 types plus watch types generated and reviewed |
| 3 | classification | generated metrics/report | no | each article classified by adequacy and cause |
| 4 | narrow fix only if strong evidence | one owner scope TBD | yes, only if justified | focused test and owner-local regression pass |
| 5 | regression / closeout | plan docs and logs | no, unless Phase 4 used | final judgment recorded |

## Phase 0 Required Checks

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
```

## Phase 1 Outputs

```text
C:\tetie\notecode\logs\source_compression_length_adequacy_YYYYMMDD-HHMMSS\previous_validation_metrics.json
C:\tetie\notecode\logs\source_compression_length_adequacy_YYYYMMDD-HHMMSS\previous_validation_metrics.md
```

Unavailable fields must be recorded as `not available`, not inferred as zero.

## Phase 2 Generation Scope

- Minimum one generation per type:
  - `explanatory_article`
  - `industry_analysis`
  - `branding/company_introduction`
  - `branding/product_introduction`
  - `announcement`
  - `case_study`
  - `comparative_review`
  - `daily_story`
- Additional watch runs if feasible:
  - `industry_analysis`
  - `branding/company_introduction`
  - `case_study`

## Phase 3 Classifications

- `OK`
- `acceptable_but_watch`
- `thin_due_to_source`
- `thin_due_to_compression`
- `thin_due_to_target`
- `thin_due_to_repair_rejection`
- `verbose_or_padded`
- `fail_closed_ok`
- `regression`

## Phase 4 Fix Candidates

Select at most one if evidence is strong:

1. source packet summary drops concrete section-expansion material.
2. article_type-specific `target_chars` / length mode is too low.
3. repair acceptance rejects a candidate that fixes explanation sufficiency.
4. diagnostics do not surface short/thin adequacy risk.

Forbidden:

- Broad length increase.
- quality threshold relaxation.
- repair count increase.
- prompt accretion.
- source-outside claim permission.
