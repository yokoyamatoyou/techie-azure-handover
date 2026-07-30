# current_mainline_comparative_review_contract_activation_2026-04-26 PROGRESS

## Current Status

- Package status: completed
- Current phase: closeout
- Date: 2026-04-26 JST
- Owner: `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Product code change: yes, owner-limited
- Prompt / threshold / repair / UI demote / output guard change: no

## Baseline

Diagnosis source:

- `C:\tetie\notecode\plan\current_mainline_comparative_review_runtime_block_diagnosis_2026-04-26\PROGRESS.md`

Observed failing runtime:

- attempt 1: `input_required_block`, `SYS_QUALITY_WARNINGS_UNRESOLVED`, body 1429 chars, source grounding 1.0, must-cover 0.3333
- attempt 2: `input_required_block`, `SYS_QUALITY_WARNINGS_UNRESOLVED`, body 1763 chars, source grounding 1.0, must-cover 0.3333

Primary failure driver:

- `contract_alignment_must_cover_reflection_rate<0.50`

## Phase Ledger

| Phase | Status | Notes |
|---|---|---|
| 0 read / baseline | complete | Diagnosis docs, ALGORITHM sections, comparative runtime contract code read |
| 1 package docs | complete | README / TASK / PROGRESS / ROLLBACK created |
| 2 focused failing tests | complete | Added Tool A/B/C comparative fallback test and non-comparative control; fallback test failed before runtime fix |
| 3 runtime fix | complete | Activated comparative fallback contract from source facts + axes in `simple_note_pipeline/pipeline.py` |
| 4 focused tests | complete | Comparative slice and requested focused suites passed |
| 5 UI rerun | complete | comparative attempts 1/2 are `publishable_success` / `OK` |
| 6 shared regression | complete | Requested shared pytest suites passed |
| 7 closeout | complete | PROGRESS and WORKLOG updated |

## Implemented Change

`comparative_contract_gap` was fixed in the comparative-only runtime contract path.

The change:

- normalizes comparative axis labels inside `simple_note_pipeline/pipeline.py`
- ignores generic axes such as `overall` / `総合`
- derives fallback axes from source facts when UI axes are generic
- fills bounded comparative slots for:
  - price / plan
  - approval flow
  - support density / onboarding support
  - fit conditions
  - tradeoffs / cautions
  - decision next step
- replaces generic `must_cover=総合, 差分, 用途別の結論` with concrete comparative anchors
- keeps the scope limited to `article_type=comparative_review`

## Files Changed

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- `C:\tetie\notecode\plan\current_mainline_comparative_review_contract_activation_2026-04-26\`
- `C:\tetie\WORKLOG.md`

No changes were made to:

- `note_writer_app.py`
- `output_guard.py`
- `quality_observability_mixin.py`
- prompt files
- threshold or repair policy

## Final UI Result

Focused UI rerun:

`C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py --case-ids bl-comparative-selection-criteria --attempts 1,2`

| Attempt | Outcome | Runtime reason | Body chars | Source grounding | Must-cover | Contract guard |
|---:|---|---|---:|---:|---:|---|
| 1 | `publishable_success` | `OK` | 1631 | 1.0 | 1.0 | absent |
| 2 | `publishable_success` | `OK` | 1696 | 1.0 | 1.0 | absent |

Runtime input contract now records:

- `must_cover=価格, 承認フロー, 導入支援, 向く条件, 注意点, 確認順`
- comparative source contract `scope_match=true`
- `source_contract_available=true`
- `evaluation_axes=価格、承認フロー、導入支援を見る。`

UI/body internal-term leakage remained 0 for both attempts.

## Verification

- Focused failing test before fix:
  - `test_comparative_runtime_contract_activates_from_source_facts_and_axes_without_explicit_contract`
  - initial result: failed with `scope_match is False`
- Focused comparative slice:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "comparative"`
  - `24 passed`
- Owner-focused suites:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - `264 passed`
- Shared regression:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - `144 passed`
- Focused UI rerun:
  - attempts 1 and 2: `publishable_success`, `runtime_reason_code=OK`
- UI server:
  - started with `HEADLESS=1`, `PORT=18080`
  - stopped after rerun
  - no `18080` listener remains

## Final Judgment

The comparative contract/must-cover gap is fixed for the diagnosed runtime path. The failure no longer appears as `input_required_block`, and the contract/must-cover warning no longer fires.
