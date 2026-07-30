# current_mainline_article_type_source_inventory_2026-04-25 README

## Objective

- UI quality validation before the next current mainline article-type run must not start from mismatched or thin source material.
- Inventory existing logs / fixtures / rerun artifacts by article type and decide whether each source is usable, replace-only, or user-provided-source-needed.
- Do not run generation in this package.
- Do not change product code, prompt, threshold, repair, UI, or fixtures.

## Source Of Truth

- Current naturalness package:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- Current runtime mainline remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Primary evidence:
  - `C:\tetie\notecode\logs\multi_type_current_mainline_validation_20260425-013935\`
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\`
  - `C:\tetie\notecode\logs\current_mainline_source_grounding_metric_correction_ui_validation_20260425-214032\`
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  - `C:\tetie\notecode\note\tests\fixtures\current_mainline_genre_sweep_casebook_2026-03-30.json`
  - `C:\tetie\WORKLOG.md`

## Read Order

1. `C:\tetie\notecode\AGENTS.md`
2. `C:\tetie\AGENTS.md`
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
6. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
7. `C:\tetie\notecode\plan\source_compression_length_adequacy_2026-04-25\README.md`
8. `C:\tetie\notecode\plan\source_compression_length_adequacy_2026-04-25\PROGRESS.md`
9. This package README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT
10. `C:\tetie\WORKLOG.md`

## Thickness Labels

- `rich`: real URLs or enough concrete slots for article-type quality validation.
- `sufficient`: usable for the article type, but still watch source depth.
- `thin`: too weak for full UI quality validation; use only for smoke / boundary checks.

## Source Inventory

| Article type | Existing source | Fit | Thickness | Boundary / failure | UI quality use |
|---|---|---:|---:|---|---|
| `company_introduction` | Kyoto 4 URLs: kyotokogyo top / profile / history / service | OK | rich | repeat1 has fail-closed suspicion; latest/UI live OK | use OK, watch |
| `company_introduction` | `bl-branding-company-overview` fixture | NG | thin | `SYS_PIPELINE_FAILURE` | replace |
| `company_introduction` | `rerun-company-introduction-operational-source` fixture | partial | thin | `INP_SOURCE_CONTEXT_INSUFFICIENT` | replace |
| `product_introduction / service overview` | `bl-branding-service-overview` fixture | OK | thin | `thin_due_to_source` | smoke only |
| `branding` | `bl-branding-values-stance` fixture | OK | sufficient | near out-of-run target | use OK only for stance/value branding |
| `announcement` | `bl-announcement-spec-change` fixture | OK | sufficient | type expected short | use OK |
| `case_study` | `bl-case-introduction` fixture | NG | thin | `INP_SOURCE_CONTEXT_INSUFFICIENT` | replace |
| `case_study` | `rerun-case-study-rich-source` / UI live httpbingo source | partial | sufficient | UI live source has mojibake / encoded title contamination | replace recommended |
| `comparative_review` | `bl-comparative-selection-criteria` fixture | OK | thin | `thin_due_to_source` | smoke only |
| `explanatory_article` | `bl-explanatory-misread-metric` fixture | OK | sufficient | classification OK | use OK, thin watch |
| `industry_analysis` | `bl-industry-evaluation-shift` fixture | OK | thin | `thin_due_to_source` | replace recommended |
| `daily_story` | `bl-daily-learning-log-grounded` fixture | OK | sufficient | type expected short | use OK if synthetic daily is acceptable |

## Use OK

- `company_introduction`: Kyoto 4 URLs from latest/UI live.
- `announcement`: existing spec-change fixture.
- `explanatory_article`: existing misread-metric fixture.
- `daily_story`: existing grounded daily fixture, only when synthetic diary source is acceptable.
- `branding`: `bl-branding-values-stance`, only for non-company-introduction stance/value article.

## Replace / Do Not Use For Full UI Quality

- `bl-branding-company-overview`
- `rerun-company-introduction-operational-source`
- `bl-case-introduction`
- UI live case_study httpbingo/base64 source
- `industry_analysis` current fixture before quality judgment
- `comparative_review` and `product_introduction` if the validation target is long-form depth rather than smoke coverage

## Web Candidate Sources

These are candidate source URLs only. They are not written into fixtures and must not be treated as adopted runtime source until a separate source-prep step selects and normalizes them.

- product/service:
  - `https://www.helpfeel.com/feature-start`
  - `https://smarthr.jp/about/feature/`
- announcement:
  - `https://jinjer.zendesk.com/hc/ja/articles/54052272236441--%E3%83%AA%E3%83%AA%E3%83%BC%E3%82%B9-2026%E5%B9%B41%E6%9C%8820%E6%97%A5-%E7%81%AB-%E3%83%AF%E3%83%BC%E3%82%AF%E3%83%95%E3%83%AD%E3%83%BC%E6%A9%9F%E8%83%BD%E3%82%A2%E3%83%83%E3%83%97%E3%83%87%E3%83%BC%E3%83%88-%E4%BB%95%E6%A7%98%E5%A4%89%E6%9B%B4-%E8%BF%BD%E8%A8%98`
- case_study:
  - `https://www.freee.co.jp/cases/hskm/`
  - `https://www.freee.co.jp/cases/hukusia/`
- explanatory:
  - `https://www.hubspot.jp/products/service/customer-success-kpi`
- industry/comparative:
  - `https://solutions.system-exe.co.jp/appremo/blog/workflow-tool-comparison`
- daily_story support only:
  - `https://life.minoeng.com/review_aday/`

## User-Provided Source Needed

- `daily_story`: 2-3 real daily notes. Web articles are support material only, not a substitute for first-person experience source.
- `branding`: if testing company stance/values, provide material that includes operating posture, customer contact point, and decision criteria, not only mission wording.
- `comparative_review`: provide target-by-target price, approval/review behavior, support density, and fit conditions.
- `case_study`: provide clean source containing before issue, implementation process, after change, and reproducibility conditions.

## Non-Goals

- Do not run generation tests in this package.
- Do not change product code, prompt, threshold, repair, UI, or fixture files.
- Do not treat source-thin shortness as runtime quality regression.
- Do not use candidate web URLs to silently replace fixtures.
- Do not reopen completed reference packages or frozen architecture package.
