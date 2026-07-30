# current_mainline_log_source_ui_regression_2026-04-26 PROGRESS

## Current Status

- Package status: completed
- Current phase: Phase 9 docs closeout
- Execution timestamp: `20260426-023257`
- Artifact root: `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\`
- UI server: stopped
- 18080 listener after closeout: none
- Product code change: no
- Prompt / threshold / repair / guard / UI implementation change: no
- AGENTS update: no routing change, not planned

## Phase Ledger

| Phase | Result | Notes |
|---|---|---|
| 0 package + artifact root | complete | package docs and artifact dirs created |
| 1 source reconstruction | complete | 9 source packets saved as `source_reconstructed_from_log.json` |
| 2 historical baseline | complete | `historical_baseline.json` written with prior failure/success flags |
| 3 tests before UI | complete | all requested pytest groups passed |
| 4 UI startup | complete | `HEADLESS=1`, `PORT=18080`, reachable at `http://127.0.0.1:18080/` |
| 5 UI generation | complete | 9 article types x 2 attempts saved |
| 6 image validation | complete with caveat | requested 2 validation records saved; UI auto-image also produced extra success-run logs |
| 7 classification | complete | source caveat vs runtime/UI classified |
| 8 server closeout | complete | server stopped; no 18080 listener remains |
| 9 docs closeout | complete | PROGRESS + WORKLOG updated |

## Initial Judgment

- This package intentionally supersedes the previous `current_mainline_full_flow_ui_validation_2026-04-26` source gate for replay purposes only.
- Source insufficiency will be recorded as a caveat, not used alone as a runtime defect.

## Source Reconstruction

| Case | Target | Docs | Source chars | Caveat |
|---|---|---:|---:|---|
| `company_introduction_kyoto_latest_log` | `company_introduction` | 4 | 3242 | latest visible artifact snapshot |
| `bl-branding-service-overview` | `product_introduction / service overview` | 2 | 146 | thin source |
| `bl-branding-values-stance` | `non-company branding / values stance` | 4 | 508 | known route mismatch risk |
| `bl-announcement-spec-change` | `announcement` | 2 | 260 | none |
| `rerun-case-study-rich-source` | `case_study` | 2 | 261 | thin source despite rich-source rerun name |
| `bl-comparative-selection-criteria` | `comparative_review` | 3 | 172 | thin source |
| `bl-explanatory-misread-metric` | `explanatory_article` | 2 | 280 | thin watch |
| `bl-industry-evaluation-shift` | `industry_analysis` | 2 | 127 | thin source |
| `bl-daily-learning-log-grounded` | `daily_story` | 2 | 234 | synthetic daily source |

## Result Summary

- Artifact root: `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\`
- Article attempts saved: 18 / 18
- Requested image validation records saved: 2 / 2
- Product code change: no
- Prompt / threshold / repair / guard / UI implementation change: no
- Internal-term leakage:
  - UI visible: 0 attempts
  - body: 0 attempts

Outcome counts:

- `publishable_success`: 5
- `input_required_block`: 10
- `ui_harness_failure`: 3
- `review_required_draft`: 0
- `technical_failure`: 0

Historical comparison labels:

- `reproduced_existing_issue`: 6
- `regression_candidate`: 4
- `source_caveat`: 13
- `improved_or_ux_recovered`: 2
- `ui_harness_issue`: 3

Per-case summary:

| Case | Attempts | Outcome | Classification |
|---|---:|---|---|
| `company_introduction_kyoto_latest_log` | 2 | 2 `publishable_success` | `improved_or_ux_recovered`, `source_caveat` |
| `bl-branding-service-overview` | 2 | 1 `input_required_block`, 1 `ui_harness_failure` | `regression_candidate`, `source_caveat`, `ui_harness_issue` |
| `bl-branding-values-stance` | 2 | 2 `input_required_block`, body 0 | `reproduced_existing_issue`, `source_caveat` |
| `bl-announcement-spec-change` | 2 | 2 `input_required_block`, body redacted | `reproduced_existing_issue` |
| `rerun-case-study-rich-source` | 2 | 2 `publishable_success` | `source_caveat` |
| `bl-comparative-selection-criteria` | 2 | 2 `ui_harness_failure` | `ui_harness_issue` |
| `bl-explanatory-misread-metric` | 2 | 2 `input_required_block`, body redacted | `regression_candidate`, `source_caveat` |
| `bl-industry-evaluation-shift` | 2 | 1 `publishable_success`, 1 `input_required_block` | `source_caveat`, `regression_candidate` |
| `bl-daily-learning-log-grounded` | 2 | 2 `input_required_block`, body redacted | `reproduced_existing_issue`, `source_caveat` |

## Image Validation

- Requested validation:
  - `company_introduction_kyoto_latest_log` attempt 1: `success`, 2 variants, files exist / non-empty / readable, `1280x670`
  - `company_introduction_kyoto_latest_log` attempt 2: `success`, 2 variants, files exist / non-empty / readable, `1280x670`
- Caveat:
  - Current UI automatically generates images for every publishable success.
  - Because product/UI implementation was not changed, additional automatic image logs were produced for other successful attempts.
  - This is recorded separately in `image_auto_log_inventory.json`.

## Verification

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_result_adapter.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
  - `137 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q`
  - `36 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - `260 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_newalgorithm_phase06_logging_compat.py -q`
  - `33 passed`

## Product Code Hash Snapshot

- `C:\tetie\notecode\note\current_mainline_runner.py`
  - `F2ADF914511D90953361676E609686C5BD0CF980249A1408DBB5BE70FAE6F41F`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `F723C6994F52EB282AF011E9D5D05335857AF6F067993B8ED58BA25EFB22E1F5`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `0FEF136F8A872A69D9FDE807811E988C810F311DB324DB3C1617DEE930C4E7AC`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
  - `50961E41080192C1084BB597AB256A8F973917672D80CA357CC4CDAE203C52F9`
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
  - `CECC784672A524811D9A2AB47ADDCD5F027604E6A7EAE9E01A6A592AA29C43AB`
- `C:\tetie\notecode\note\note_writer_app.py`
  - `A13B73FA16CF284674AB53A76CE2A05418545A0573569BD43BB7C76F7DD43702`

## Final Judgment

- The requested log-source UI regression validation completed with artifacts for all 18 article attempts.
- The strongest runtime-facing regression candidates are:
  - `bl-explanatory-misread-metric`: historical UI OK, current 2/2 `SYS_QUALITY_WARNINGS_UNRESOLVED` with body redacted.
  - `bl-industry-evaluation-shift` attempt 2: historical OK, current warning block; source is thin.
  - `bl-branding-service-overview` attempt 1: historical OK, current warning block; source is thin.
- Reproduced existing issues:
  - `bl-branding-values-stance`: route mismatch / body 0 shape reproduced.
  - `bl-announcement-spec-change`: warning-block shape reproduced.
  - `bl-daily-learning-log-grounded`: warning-block shape reproduced with synthetic source caveat.
- UI harness issues remain for:
  - `bl-comparative-selection-criteria` 2/2
  - `bl-branding-service-overview` attempt 2
- No internal-term leakage was observed in UI visible text or body artifacts.
