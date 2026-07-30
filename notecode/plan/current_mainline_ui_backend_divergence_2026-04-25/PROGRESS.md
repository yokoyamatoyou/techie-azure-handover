# current_mainline_ui_backend_divergence_2026-04-25 PROGRESS

## Current Status

- Package status: stopped at Phase 6 UI validation
- Current phase: stop/report
- Behavior change: no product behavior change
- Current hypothesis after validation:
  - initial: `ui_input_mapping_diff`
  - final: `backend_ui_input_equivalent_but_ui_live_guard_still_fails`
- Stop reason:
  - actual UI operation with equivalent `length_mode=short` and intended speaker still returned `SYS_QUALITY_WARNINGS_UNRESOLVED` 3 times for both target cases.
  - direct backend rerun from the exact UI `input_contract` succeeded for both target cases.
- Artifact root:
  - `C:\tetie\notecode\logs\current_mainline_ui_backend_divergence_20260425-155544\`

## Baseline

- Plan-mode read completed:
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\ALGORITHM.md` sections 4, 5, 12
  - current naturalness package README / TASK / PROGRESS / ROLLBACK
  - `pipeline_responsibility_split_2026-04-24\PROGRESS.md`
  - `company_intro_source_packet_thickness_2026-04-25\PROGRESS.md`
  - `current_mainline_ui_past_failure_validation_2026-04-25\PROGRESS.md`
  - current fail-closed fix README / TASK / PROGRESS / ROLLBACK
  - predecessor logs under `current_mainline_fail_closed_fix_20260425-144208`
  - `C:\tetie\WORKLOG.md`
- Baseline tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - result: `260 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - result: `141 passed`

## Initial Diff Read

- Case 1 backend OK vs UI fail:
  - backend `length_mode=short`; UI `length_mode=adaptive`
  - backend `speaker_profile=企業広報として語る`; UI `speaker_profile=自動判定`
  - source inputs/documents/grounding/must-cover broadly aligned
  - UI fail reasons include fingerprint warnings and `source_grounding:weak_reflection`
- Case 4 backend OK vs UI fail:
  - backend `length_mode=short`; UI `length_mode=adaptive`
  - backend `speaker_profile=導入支援担当として語る`; UI `speaker_profile=編集担当として語る`
  - source inputs/documents/grounding/must-cover broadly aligned
  - old `contract_alignment_must_cover_reflection_rate<0.50` symptom is gone; UI fail reasons are fingerprint warnings and `source_grounding:weak_reflection`
- Current classification before new validation:
  - Case 1: `ui_input_mapping_diff`
  - Case 4: `ui_input_mapping_diff`

## Phase 1 Diff Artifacts

- Saved:
  - `C:\tetie\notecode\logs\current_mainline_ui_backend_divergence_20260425-155544\backend_ui_diff_summary.json`
  - `C:\tetie\notecode\logs\current_mainline_ui_backend_divergence_20260425-155544\backend_ui_diff_summary.md`
  - per-case `*_diff.json`
- Result:
  - predecessor backend/UI artifacts were not equivalent.
  - `source_inputs`, source document counts, grounding item counts, and must-cover counts were broadly aligned.
  - `length_mode` and `speaker_profile` differed in both target cases.

## Phase 2 Classification

- Case 1:
  - initial classification: `ui_input_mapping_diff`
  - after equivalence validation: `fingerprint_guard_remaining` with intermittent `source_grounding:weak_reflection`
  - reason:
    - equivalent UI contract had `length_mode=short`, `speaker_profile=企業広報として語る`, source document chars equal to backend, must-cover equal, source grounding equal.
    - direct backend rerun from that exact UI contract returned `OK`.
    - UI live runs still returned `SYS_QUALITY_WARNINGS_UNRESOLVED`.
- Case 4:
  - initial classification: `ui_input_mapping_diff`
  - after equivalence validation: `fingerprint_guard_remaining`
  - reason:
    - equivalent UI contract had `length_mode=short`, `speaker_profile=導入支援担当として語る`.
    - direct backend rerun from that exact UI contract returned `OK`.
    - UI live runs still returned `SYS_QUALITY_WARNINGS_UNRESOLVED`.

## Phase 3 / 4 Fix Scope Decision

- Product runtime fix: not applied.
- UI product fix: not applied.
- Validation harness fix:
  - created `C:\tetie\notecode\logs\current_mainline_ui_backend_divergence_20260425-155544\ui_validate_equivalence.py`
  - corrected the predecessor harness gap by explicitly setting:
    - `length_mode=short`
    - Case 1 speaker `企業広報として語る`
    - Case 4 speaker `導入支援担当として語る`
  - corrected stale read risk by waiting for `latest_generation_output.json` mtime to advance before copying results.
- Reason no product fix was applied:
  - the input mapping mismatch was proven in the predecessor validation harness, not in the product handoff after explicit controls.
  - once product UI controls were set explicitly, values survived into `input_contract`.
  - remaining issue is not a narrow UI/source handoff diff.

## Phase 5 Backend Equivalence Rerun

- Saved:
  - `C:\tetie\notecode\logs\current_mainline_ui_backend_divergence_20260425-155544\backend_rerun\backend_from_ui_contract_summary.json`
- Case 1:
  - input: exact UI equivalent `input_contract`
  - result: `OK`
  - `length_mode=short`
  - `speaker_profile=企業広報として語る`
  - `must_cover_reflection_rate=0.75`
  - `source_trace_coverage=0.6`
  - output guard reasons: none
- Case 4:
  - input: exact UI equivalent `input_contract`
  - result: `OK`
  - `length_mode=short`
  - `speaker_profile=導入支援担当として語る`
  - `must_cover_reflection_rate=0.7143`
  - `source_trace_coverage=1.0`
  - output guard reasons: none

## Phase 6 UI Operation Validation

- UI URL:
  - `http://127.0.0.1:18080/`
- UI server:
  - old process on port `18080` was restarted.
  - new server stdout confirmed: `NiceGUI ready to go on http://127.0.0.1:18080`
- Equivalent UI run attempts:
  - attempt 1 fresh wait:
    - Case 1: `SYS_QUALITY_WARNINGS_UNRESOLVED`, `length_mode=short`, `speaker_profile=企業広報として語る`, output guard included fingerprint warnings and `source_grounding:weak_reflection`
    - Case 4: `SYS_QUALITY_WARNINGS_UNRESOLVED`, `length_mode=short`, `speaker_profile=導入支援担当として語る`, output guard fingerprint warnings
  - attempt 2:
    - Case 1: `SYS_QUALITY_WARNINGS_UNRESOLVED`, fingerprint warnings
    - Case 4: `SYS_QUALITY_WARNINGS_UNRESOLVED`, fingerprint warnings
  - attempt 3 after UI server restart:
    - Case 1: `SYS_QUALITY_WARNINGS_UNRESOLVED`, fingerprint warnings
    - Case 4: `SYS_QUALITY_WARNINGS_UNRESOLVED`, fingerprint warnings
- Visible UI checks:
  - empty result: no
  - stale result after harness correction: no
  - visible/body internal-term leakage: none observed
  - user-facing error display: sanitized fail-closed message

## Stop Report

- phase:
  - Phase 6 UI operation validation
- failing operation:
  - actual UI operation with explicit equivalent controls through Selenium at `http://127.0.0.1:18080/`
- error excerpt:
  - `runtime_reason_code=SYS_QUALITY_WARNINGS_UNRESOLVED`
  - recurring guard family: fingerprint warnings
  - Case 1 sometimes also included `source_grounding:weak_reflection`
- tried corrections / validations:
  - fixed validation harness to wait for fresh `latest_generation_output.json` instead of copying a stale result
  - set explicit UI controls to match backend (`short` length and intended speaker)
  - restarted UI server and reran equivalent UI operation
  - direct backend rerun from exact UI `input_contract` succeeded for both cases
- blocked responsibility:
  - no remaining narrow UI input mapping / source handoff diff was proven.
  - remaining failure is live UI generation output guard behavior under equivalent inputs, while direct backend samples can pass.
- rollback candidate:
  - no product code rollback required.
  - package/docs/logs can be superseded if a future runtime guard package is opened.
- residual risk:
  - UI still cannot produce a success artifact for Case 1 / Case 4 in three equivalent attempts.
  - fixing this now would require a new runtime hypothesis around fingerprint/source-reflection guard behavior, which this package explicitly stops before changing.

## Phase Ledger

| Phase | Owner files | Changed responsibility | Behavior change | Tests run | Result | Failure attempts | Next phase |
|---|---|---|---|---|---|---|---|
| 0 | plan package / inspection | package creation and baseline | no | baseline pytest commands | `260 passed`; `141 passed` | 0 | Phase 1 |
| 1 | logs | backend/UI payload diff | no | artifact inspection | initial non-equivalence found in length/speaker controls | 0 | Phase 2 |
| 2 | logs / PROGRESS | root-cause classification | no | diff review | initial `ui_input_mapping_diff`, then equivalent UI showed remaining guard failures | 0 | Phase 3/4 |
| 3 | validation harness only | Case 1 equivalent UI control path | no product change | actual UI operation | input equivalent but still `SYS_QUALITY_WARNINGS_UNRESOLVED` | 3 UI observations | Phase 5/6 stop |
| 4 | validation harness only | Case 4 equivalent UI control path | no product change | actual UI operation | input equivalent but still `SYS_QUALITY_WARNINGS_UNRESOLVED` | 3 UI observations | Phase 5/6 stop |
| 5 | backend rerun logs | backend rerun from exact UI contract | no | live backend runner | both target cases `OK` | 0 | Phase 6 |
| 6 | UI logs/screenshots | actual UI validation | no | Selenium UI operation | both target cases fail-closed after 3 equivalent attempts | 3 | stop/report |

## Next Action

- Do not continue this package by changing runtime thresholds, repair count, target chars, prompt, or source packet thickness.
- Open a separate runtime guard package only if management chooses to address equivalent-input live UI fingerprint/source-reflection instability.
