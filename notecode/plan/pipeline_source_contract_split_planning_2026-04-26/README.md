# pipeline_source_contract_split_planning_2026-04-26 README

## Objective

`current_mainline_bloat_control_priority_2026-04-26` Priority 3 として、`C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` に増えた article-type source contract logic を棚卸しし、behavior-preserving extraction の分割方針を固定する。

この package は docs-only planning package であり、product code の extraction 実装ではない。

## Source Of Truth

- Current runtime owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Compatibility path:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- Current global planning source of truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`

## Non-Goals

- product code 変更
- extraction 実装
- prompt 変更
- threshold 変更
- repair policy 変更
- output_guard 変更
- UI 変更
- new behavior 追加
- full-flow 残課題修正
- note_writer_app split
- source contract common helper の先行共通化

## Current Inventory

`pipeline.py` baseline:

- line count observed: `8386`
- SHA256 observed before this docs-only package:
  - `DD4E06CF33EC9D36A96C6ECCF200213F0B90C6EE5400376C35A6B08D342486A8`

| Category | Current `pipeline.py` area | Main symbols | Tests / evidence | Split judgment |
|---|---:|---|---|---|
| `announcement` | constants `155-199`, runtime `1910-2161`, validation `4572-4828`, repair metadata `7044+ / 7571+ / 7767+`, output projection `8220-8238` | `_ANNOUNCEMENT_*`, `_prepare_announcement_runtime_contract`, `_evaluate_announcement_source_contract_validation`, failure/improvement helpers | `test_announcement_*` around `9347-9708`; latest activation package passed focused + owner + shared tests | **Do first**. Move pure/constants/runtime/validation helpers; keep orchestration/projection in `pipeline.py`. |
| `comparative_review` | constants `244-324`, runtime `2972-3314`, validation `3443-3724`, repair metadata `7164+ / 7617+ / 7787+`, output projection `8328-8351` | `_COMPARATIVE_*`, `_prepare_comparative_runtime_contract`, `_evaluate_comparative_source_contract_validation`, fallback axes/slots | `test_comparative_*` around `10261-10599`; latest activation package passed | Do next after announcement. Clear but axes/fallback/must_cover logic is more complex. |
| `company_introduction` | imported constants already split, runtime `2333-2968`, validation `3960-4358`, telemetry/repair helpers `6101+ / 6248+ / 6449+`, repair acceptance/output projection deep in class | `_prepare_company_intro_runtime_contract`, script packet helpers, `_evaluate_company_intro_source_contract_validation` | many focused tests around `7014-8933`; prior split intentionally left runtime builder/evaluator in pipeline | Park for later. Important but broad and coupled to script packet, observability, repair acceptance. |
| `branding` | constants `201-241`, runtime `2164-2329`, validation `3727-3957`, repair metadata/output projection | `_BRANDING_*`, `_prepare_branding_runtime_contract`, `_evaluate_branding_source_contract_validation` | existing branding source contract tests mixed with prompt/craft coverage | Park until announcement/comparative prove pattern. |
| `case_study` | constants `115-152`, runtime `1684-1907`, validation `4367-4569`, repair metadata/output projection | `_CASE_STUDY_*`, `_prepare_case_study_runtime_contract`, `_evaluate_case_study_source_contract_validation` | some coverage exists; not the current bloat priority | Park. |
| `explanatory_article` | runtime `3320-3440`, source digest via `ui_prompt_distillation.py` | `_prepare_explanatory_runtime_contract`, source-use digest/must_cover helpers | mixed explanatory tests; not source-contract guard-heavy | Park; keep separate from source contract extraction. |
| shared grounding / must_cover | repeated source sentence extraction, grounding merge, must_cover merge | `_hidden_late_source_text`, `_clean_inline_text`, grounding item construction patterns | indirect | Park. Do not create `source_contract_common.py` first; premature commonization risks behavior drift. |

## Existing Extracted Modules

- `hidden_late_validation.py`
  - hidden validation constants / contract builder / leakage checks / required-token evaluation.
- `company_intro_source_contract_guard.py`
  - company intro source slot constants / failure-improvement predicates / validation snapshot helper.
- `company_intro_opener_guard.py`
  - company intro visible opener drift evaluation and heading rescue helper.
- `repair_acceptance.py`
  - pure repair acceptance predicates.
- Other modules under `note\simple_note_pipeline\` are not target modules for this source contract split planning package.

## Proposed Module Boundary

### Do First

Create future implementation package for:

- `C:\tetie\notecode\note\simple_note_pipeline\announcement_source_contract.py`

Move in that future package:

- `_ANNOUNCEMENT_SOURCE_SLOTS`
- `_ANNOUNCEMENT_REQUIRED_SOURCE_SLOTS`
- `_ANNOUNCEMENT_SLOT_LABELS`
- `_ANNOUNCEMENT_SLOT_PATTERNS`
- announcement regex constants
- `_announcement_scope_active`
- `_announcement_source_sentences`
- `_announcement_slot_from_bucket`
- `_announcement_slot_candidate_score`
- `_build_announcement_runtime_source_contract`
- `_merge_announcement_runtime_contract_into_payload`
- `_prepare_announcement_runtime_contract`
- `_announcement_text_for_validation`
- `_announcement_slot_value_reflected`
- `_announcement_slot_present`
- `_normalize_announcement_claim_token`
- `_announcement_unsupported_hits`
- `_announcement_wrong_article_type_drift`
- `_announcement_explanatory_drift`
- `_announcement_target_action_buried`
- `_announcement_source_contract_failure_count`
- `_announcement_source_contract_improved`
- `_evaluate_announcement_source_contract_validation`

Keep in `pipeline.py`:

- `_prepare_runtime_source_contracts`
- `_refresh_diagnostics_state`
- `MinimalPipeline._run_optional_repair`
- `MinimalPipeline.generate`
- body_generation projection

Compatibility rule:

- Import moved private `_announcement_*` symbols back into `pipeline.py` so existing tests using `pipeline_mod._prepare_announcement_runtime_contract` and related private names continue to pass.

### Do Next

- `comparative_review_source_contract.py`
- Only after announcement extraction is green.
- Keep private symbol compatibility.
- Do not combine with announcement in the same implementation window.

### Park

- `company_intro_source_contract_runtime.py`
- `branding_source_contract.py`
- `case_study_source_contract.py`
- `explanatory_source_grounding.py`
- `source_contract_common.py`

`source_contract_common.py` is explicitly deferred until at least two article-type extractions prove repeated code can be shared without making behavior harder to audit.

