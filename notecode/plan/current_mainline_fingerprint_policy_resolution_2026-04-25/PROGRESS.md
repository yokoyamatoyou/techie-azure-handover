# current_mainline_fingerprint_policy_resolution_2026-04-25 PROGRESS

## Current Status

- Package status: completed
- Current phase: Phase 9 closeout
- Behavior change: yes, scoped UI final guard policy classification
- Decision: `B scoped soft warning / observability`

## Baseline

- Required read completed:
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\ALGORITHM.md` sections 4, 5, 12
  - naturalness recovery package README / TASK / PROGRESS / ROLLBACK
  - predecessor progress files and logs
  - `C:\tetie\WORKLOG.md`
- Baseline tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - result: `260 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - result: `141 passed`

## Policy Map

- `note/newalgorithm_pipeline/output_guard.py` computes strict final guard.
- `strict_saas_mode=medium` promotes any remaining soft warnings to `SYS_QUALITY_WARNINGS_UNRESOLVED`.
- `note/note_writer_app.py` re-evaluates final output guard before rendering UI output.
- Existing UI already has `quality_warning_only` success rendering when soft warnings are present and guard is not blocked.
- Public contract tests protect:
  - generic medium strict soft-warning fail-close
  - existing public-contract success artifacts that still carry fingerprint-only pure guard warnings
  - sanitized fail-closed UI wording

## Artifact Decision

- Case 1:
  - visible quality: acceptable but flat
  - source grounded: yes if current run is fingerprint-only; weak reflection remains separate if present
  - source outside claim: no observed
  - internal leakage: no observed
  - fingerprint-only: yes in equivalent UI artifact
  - user-facing body: may be returned only under fingerprint-only warning state
- Case 4:
  - visible quality: acceptable / source-grounded
  - source grounded: yes
  - source outside claim: no observed
  - internal leakage: no observed
  - fingerprint-only: yes
  - user-facing body: yes, with quality warning

## Phase Ledger

| Phase | Owner files | Changed responsibility | Behavior change | Tests run | Result | Failure attempts | Next phase |
|---|---|---|---|---|---|---|---|
| 0 | docs / logs | baseline read and package creation | no | baseline commands | `260 passed`; `141 passed` | 0 | Phase 1 |
| 1 | `output_guard.py`, `note_writer_app.py`, tests | guard policy map | no | inspection | strict final guard connection identified | 0 | Phase 2 |
| 2 | logs | artifact quality decision | no | artifact inspection | Case 4 eligible; Case 1 eligible only when fingerprint-only | 0 | Phase 3 |
| 3 | PROGRESS | chose scoped warning policy | no | inspection | B selected | 0 | Phase 4 |
| 4 | tests | focused expectations | no product behavior | focused tests | `2 passed`; `4 passed` | 0 | Phase 5 |
| 5 | `output_guard.py`, `note_writer_app.py`, `current_mainline_ui_result_adapter.py` | fingerprint-only fail-closed classification to warning-only at UI final guard connection; warning display sanitization | yes | focused tests | initial UI status propagation gap found and fixed; display codes sanitized | 1 | Phase 6 |
| 6 | owner-local tests | regression safety | no additional behavior | owner-local suites | `131 passed`; `260 passed`; `36 passed` | 0 | Phase 7 |
| 7 | backend runner | backend rerun for Case 1 / Case 4 | no additional behavior | backend rerun | Case 1 stayed blocked when `source_grounding:weak_reflection` appeared; Case 4 demoted when fingerprint-only | 0 | Phase 8 |
| 8 | actual UI | actual UI operation validation on `http://127.0.0.1:18080/` | no additional behavior | Selenium UI operation | Case 1 success when current run was fingerprint-only; Case 4 success on attempt 3 when current run was fingerprint-only; attempts with source-grounding remained stopped | 2 source-grounding attempts for Case 4 | Phase 9 |
| 9 | shared tests / records | closeout | no additional behavior | shared suites | `346 passed`; `36 passed`; `6 passed` | 0 | complete |

## Implementation Summary

- Added `is_fingerprint_only_warning_observable()` and `demote_fingerprint_only_output_guard_to_warning()` in `note/newalgorithm_pipeline/output_guard.py`.
- The helper does not change fingerprint thresholds or `evaluate_generation_output_guard()`.
- Eligibility remains narrow:
  - strict guard reason is `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - fail-close is warning-only
  - no guard hard reasons, manual instructional hits, or needed input items
  - blocking reasons and soft warnings are fingerprint-only
  - no non-fingerprint final quality / hard-soft / naturalness / contract / source grounding issue
  - must-cover reflection and source trace coverage satisfy existing green-enough policy signals
- Applied the helper only at the UI final guard connection in `note/note_writer_app.py`.
- Demoted eligible output restores success status and unredacted output fields for UI persistence.
- Sanitized warning summary display so internal warning codes are not shown in UI.

## Validation Artifacts

- Backend rerun:
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_policy_resolution_20260425-165333\backend_rerun\`
  - Case 1: strict guard included `source_grounding:weak_reflection`, so not demoted.
  - Case 4: strict guard was fingerprint-only and was demoted to warning-only.
- Actual UI operation:
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_policy_resolution_20260425-165333\ui_lenient_actual_operation_v2\`
  - Case 1: current run was fingerprint-only and returned success with no stale/empty result and no visible/body internal term leakage.
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_policy_resolution_20260425-165333\ui_lenient_case4_attempt3\`
  - Case 4: attempt 3 was fingerprint-only and returned success with no stale/empty result and no visible/body internal term leakage.
  - Case 4 attempts 1/2:
    - `ui_lenient_actual_operation_v2`
    - `ui_lenient_case4_attempt2`
    - both included `source_grounding:weak_reflection`; stop behavior was preserved.

## Tests

- Baseline:
  - `note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`: `260 passed`
  - `note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`: `141 passed`
- Focused:
  - `note\tests\test_current_mainline_ui_result_adapter.py -q -k "quality_warning_state or fingerprint_only"`: `2 passed`
  - `note\tests\test_current_mainline_regressions.py -q -k "fingerprint_only or output_guard_fail_closes_soft_warnings"`: `4 passed`
- Owner-local:
  - `note\tests\test_current_mainline_ui_result_adapter.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`: `131 passed`
  - `note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`: `260 passed`
  - `note\tests\test_current_mainline_ui_matrix.py -q`: `36 passed`
- Shared closeout:
  - `note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`: `346 passed`
  - `note\tests\test_current_mainline_ui_matrix.py -q`: `36 passed`
  - `note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_vnext_current_boundary_freeze.py -q`: `6 passed`

## Residual Risks

- Case 1 / Case 4 can still fail-closed when current generation includes `source_grounding:weak_reflection`, contract reflection below threshold, internal leakage, or other non-fingerprint warnings.
- The UI operation harness has a known brittle click/wait path around `内容を確認`; lenient collection was used because the UI had actually started generation and produced snapshots.
- Fingerprint warnings remain in internal artifacts for observability, but they are no longer displayed as raw user-facing UI text.
