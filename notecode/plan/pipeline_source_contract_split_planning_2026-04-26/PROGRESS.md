# pipeline_source_contract_split_planning_2026-04-26 PROGRESS

## Current Status

- Package status: active implementation checkpoint
- Current phase: Phase 03 company_introduction behavior-preserving extraction completed
- Date: 2026-04-26 JST
- Product code change: yes
- Extraction implementation: completed for announcement, comparative_review, and company_introduction
- Prompt / threshold / repair / output_guard / UI change: no
- Generation rerun: no
- UI server startup: no
- AGENTS update: no
- WORKLOG update: completed

## Inspected Evidence

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\current_mainline_bloat_control_priority_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_announcement_source_contract_activation_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_comparative_review_contract_activation_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\announcement_source_contract.py`
- `C:\tetie\notecode\note\simple_note_pipeline\comparative_review_source_contract.py`
- `C:\tetie\notecode\note\simple_note_pipeline\company_intro_source_contract.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\hidden_late_validation.py`
- `C:\tetie\notecode\note\simple_note_pipeline\company_intro_source_contract_guard.py`
- `C:\tetie\notecode\note\simple_note_pipeline\company_intro_opener_guard.py`
- `C:\tetie\notecode\note\simple_note_pipeline\repair_acceptance.py`

## Baseline

- `pipeline.py` line count observed: `8386`
- `pipeline.py` SHA256 observed before docs-only creation:
  - `DD4E06CF33EC9D36A96C6ECCF200213F0B90C6EE5400376C35A6B08D342486A8`

## Inventory Result

| Category | Decision | Reason |
|---|---|---|
| `announcement` | do-first | narrow scope, recent fix, focused tests, lower coupling than company intro / comparative |
| `comparative_review` | do-next | clear scope, but fallback axes / slots / must_cover are more complex |
| `company_introduction` | park | broad runtime/script packet/observability/repair coupling; prior split intentionally left runtime builder/evaluator in `pipeline.py` |
| `branding` | park | source contract exists but less urgent than announcement/comparative; tests are mixed with craft/prompt coverage |
| `case_study` | park | not current bloat priority |
| `explanatory_article` | park | source-use digest rather than source-contract guard-heavy flow |
| shared common helpers | park | premature commonization risks behavior drift |

## Selected First Extraction

- Future module:
  - `C:\tetie\notecode\note\simple_note_pipeline\announcement_source_contract.py`
- Future implementation type:
  - behavior-preserving extraction only
- Future implementation package:
  - separate from this docs-only planning package

## Phase 00 Explicit Non-Changes

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` unchanged
- product behavior unchanged
- prompt unchanged
- threshold unchanged
- repair policy unchanged
- output_guard unchanged
- UI unchanged
- no tests run because Phase 00 is docs-only

## Next Action

Phase 03 is green. If continued later, reassess remaining parked source contract cleanup separately; do not combine branding / case_study / explanatory / common helper work into this completed company_introduction extraction.

## 2026-04-26 Re-Inventory Decision

- Re-measured owner sizes before Phase 03:
  - `pipeline.py`: `7190` lines, SHA256 `A1D4573F22FAC165A3C3BFDE40D0D4C72CA26AB72416E20A8FD6F06CFF89D67B`
  - `announcement_source_contract.py`: `577` lines
  - `comparative_review_source_contract.py`: `751` lines
  - `note_writer_app.py`: `8352` lines
  - `quality_observability_mixin.py`: `1273` lines
  - `output_guard.py`: `965` lines
- Decision:
  - select `company_introduction` as the next and only extraction.
- Reason:
  - it was the largest remaining article-type source contract block in `pipeline.py`.
  - extraction could be limited to source contract runtime / script packet / validation helpers.
  - repair orchestration, failure payloads, observability projection, and generation orchestration could remain in `pipeline.py`.
  - existing focused tests around company_intro source contract / repair acceptance were sufficient to guard behavior.
- `18080` listener:
  - none observed during re-inventory.
- AGENTS update:
  - not needed; routing and current source-of-truth did not change.

## Phase 01 Implementation Result

- Created:
  - `C:\tetie\notecode\note\simple_note_pipeline\announcement_source_contract.py`
- Updated:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\plan\pipeline_source_contract_split_planning_2026-04-26\PROGRESS.md`
  - `C:\tetie\WORKLOG.md`
- Extracted responsibility:
  - `_ANNOUNCEMENT_*` constants
  - announcement runtime source contract preparation
  - announcement source slot / fallback source sentence / must-cover activation helpers
  - announcement validation helpers
  - announcement failure / improvement helper logic
- Left in `pipeline.py`:
  - `_prepare_runtime_source_contracts`
  - `_refresh_diagnostics_state`
  - `MinimalPipeline._run_optional_repair`
  - `MinimalPipeline.generate`
  - body_generation / diagnostics projection
  - current success path connection
- Compatibility:
  - moved private `_ANNOUNCEMENT_*` and `_announcement_*` symbols are imported into `pipeline.py` for existing private imports/tests.
  - `_normalize_announcement_claim_token` remains available through `pipeline.py` and continues to serve existing branding / company_intro / comparative helpers.
- Behavior:
  - behavior-preserving extraction only.
  - no prompt, threshold, repair count, output_guard, quality_guard, UI, target_chars, length_mode, or non-announcement expansion change.

## Phase 01 Verification

- `C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile note\simple_note_pipeline\pipeline.py note\simple_note_pipeline\announcement_source_contract.py`
  - pass
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "announcement"`
  - `14 passed, 228 deselected`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - `264 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - `144 passed`

## Phase 02 Implementation Result

- Created:
  - `C:\tetie\notecode\note\simple_note_pipeline\comparative_review_source_contract.py`
- Updated:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\plan\pipeline_source_contract_split_planning_2026-04-26\PROGRESS.md`
  - `C:\tetie\WORKLOG.md`
- Extracted responsibility:
  - `_COMPARATIVE_*` constants
  - comparative source facts / comparison axes extraction helpers
  - source-backed fallback slots / fallback must-cover activation helpers
  - comparative runtime source contract preparation / payload merge helpers
  - comparative validation helpers
  - comparative failure / improvement helper logic
- Left in `pipeline.py`:
  - `_prepare_runtime_source_contracts`
  - `_refresh_diagnostics_state`
  - `MinimalPipeline._run_optional_repair`
  - `MinimalPipeline.generate`
  - body_generation / diagnostics projection
  - current success path connection
  - experimental comparative prompt echo stabilizer outside source contract extraction scope
- Compatibility:
  - moved private `_COMPARATIVE_*` and `_comparative_*` symbols are imported into `pipeline.py` for existing private imports/tests.
  - `_prepare_comparative_runtime_contract`, `_evaluate_comparative_source_contract_validation`, `_comparative_source_contract_failure_count`, and `_comparative_source_contract_improved` remain available through `pipeline.py`.
- Behavior:
  - behavior-preserving extraction only.
  - no prompt, threshold, repair count, output_guard, quality_guard, UI, target_chars, length_mode, or non-comparative expansion change.

## Phase 02 Verification

- `C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile note\simple_note_pipeline\pipeline.py note\simple_note_pipeline\comparative_review_source_contract.py`
  - pass
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "comparative"`
  - `24 passed, 218 deselected`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - `264 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - `144 passed`

## Phase 03 Implementation Result

- Created:
  - `C:\tetie\notecode\note\simple_note_pipeline\company_intro_source_contract.py`
- Updated:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\plan\pipeline_source_contract_split_planning_2026-04-26\PROGRESS.md`
  - `C:\tetie\notecode\plan\pipeline_source_contract_split_planning_2026-04-26\EXECUTION_PROMPT.md`
  - `C:\tetie\WORKLOG.md`
- Extracted responsibility:
  - company_intro source contract scope / sentence / slot / scoring helpers
  - company_intro quote-backed script packet helpers
  - company_intro runtime source contract preparation / payload merge helpers
  - company_intro validation helpers
  - company_intro unsupported-claim / source-limit leakage / brochure-generic-profile drift predicates
- Left in `pipeline.py`:
  - `_prepare_runtime_source_contracts`
  - `_refresh_diagnostics_state`
  - `MinimalPipeline._run_optional_repair`
  - `MinimalPipeline.generate`
  - company_intro naturalness enrichment
  - company_intro fingerprint / source-reflection repair activation
  - failure payload / observability projection
  - body_generation projection
  - current success path connection
- Compatibility:
  - moved private `_company_intro_*`, `_build_company_intro_*`, `_prepare_company_intro_runtime_contract`, `_evaluate_company_intro_source_contract_validation`, and `_merge_company_intro_runtime_contract_into_payload` symbols are imported into `pipeline.py` for existing private imports/tests.
- Behavior:
  - behavior-preserving extraction only.
  - no prompt, threshold, repair count, output_guard, quality_guard, UI, target_chars, length_mode, or non-company-introduction expansion change.
- Size after extraction:
  - `pipeline.py`: `6174` lines, SHA256 `A6556109E5408197EE118936F474146E76EFCAFDE7568E614CBCA722F46E57FD`
  - `company_intro_source_contract.py`: `1111` lines, SHA256 `17ACADFCA0AB81FA37293200D509FBFB3094B4FC9C99779B41AE091EDCD57AED`

## Phase 03 Verification

- `C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile note\simple_note_pipeline\pipeline.py note\simple_note_pipeline\company_intro_source_contract.py`
  - pass
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "company_intro or company_introduction"`
  - `87 passed, 155 deselected`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - `264 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - `144 passed`

## Post-Extraction UI Smoke Validation

- Date:
  - `2026-04-26 JST`
- Artifact root:
  - `C:\tetie\notecode\logs\current_mainline_source_contract_extraction_smoke_20260426-182438\`
- Scope:
  - current mainline source contract extraction 後の実UI smoke validation。
  - product code / prompt / threshold / repair count / quality_guard / output_guard / note_writer_app / source contract modules / target_chars / length_mode 変更なし。
- UI route:
  - `http://127.0.0.1:18080/`
  - fixed manifest source snapshot を使用。
- Attempts:
  - `company_introduction_kyoto_latest_log` attempt 1: `publishable_success`, `runtime_reason_code=OK`, `body_chars=1467`, `blocked=false`, `blocked_output_redacted=false`
  - `company_introduction_kyoto_latest_log` attempt 2: `publishable_success`, `runtime_reason_code=OK`, `body_chars=1428`, `blocked=false`, `blocked_output_redacted=false`
  - `bl-announcement-spec-change` attempt 1: `publishable_success`, `runtime_reason_code=OK`, `body_chars=540`, `blocked=false`, `blocked_output_redacted=false`
  - `bl-announcement-spec-change` attempt 2: `publishable_success`, `runtime_reason_code=OK`, `body_chars=398`, `blocked=false`, `blocked_output_redacted=false`
  - `bl-comparative-selection-criteria` attempt 1: `publishable_success`, `runtime_reason_code=OK`, `body_chars=1275`, `blocked=false`, `blocked_output_redacted=false`
  - `bl-comparative-selection-criteria` attempt 2: `publishable_success`, `runtime_reason_code=OK`, `body_chars=1704`, `blocked=false`, `blocked_output_redacted=false`
- Stop conditions:
  - `input_required_block`: not observed.
  - empty body: not observed.
  - internal term leakage: not observed in UI visible text or body.
  - source outside claim: not observed in visible review.
  - image generation breaking mainline result: not observed.
- Source reflection visual check:
  - company_introduction reflected Kyoto 4 URL source facts: Kyoto 工業, data entry / analysis / RPA, scanning, inquiry / hearing / NDA / Zoom / estimate flow.
  - announcement reflected FAQ facts: 2026-04-15 10:00, two-step approval, editors / approvers, old procedure reference through 2026-04-30, draft save / rejection notification / publish time reset / notification destination.
  - comparative_review reflected price, approval flow, support density, and selection criteria across Tool A / B / C.
- Image auto generation:
  - six post-success image generation logs were observed and copied under `image_artifacts\`.
  - each attempt produced `with_text` and `without_text` variants with `success`.
  - no image failure affected body generation.
- Verification:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
    - `264 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `144 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_newalgorithm_phase06_logging_compat.py -q`
    - `35 passed`
- AGENTS update:
  - not needed; routing and current source-of-truth did not change.
- WORKLOG update:
  - completed.
- UI server:
  - stopped after validation.
  - `18080` listener: none observed after stop.

## Post-Smoke Park Decision

- Date:
  - `2026-04-26 JST`
- Decision:
  - do not auto-chain into branding / case_study / explanatory_article / common helper extraction.
  - park further `pipeline.py` source-contract extraction after announcement / comparative_review / company_introduction extraction and post-extraction smoke green.
  - next bloat-control priority moves back to `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\` `Phase 05`.
- Reason:
  - `note_writer_app.py` is the largest remaining owner at `8352` lines.
  - the existing split package has Phase 04 completed and a decision-complete Phase 05 execution prompt.
  - continuing `pipeline.py` extraction immediately would risk mixing with the just-validated source-contract smoke path.
- Product code change:
  - no.
- AGENTS update:
  - not needed.
