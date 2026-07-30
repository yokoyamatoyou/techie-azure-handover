# current_mainline_fail_closed_fix_2026-04-25 PROGRESS

## Current Status

- Package status: stopped at Phase 6 UI validation
- Current phase: stop/report
- Behavior change: yes, private runtime behavior only
- Stop reason: both target cases still returned `SYS_QUALITY_WARNINGS_UNRESOLVED` through actual UI operation after narrow runtime fixes and backend success
- UI artifact root: `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_20260425-144208\ui\`
- Backend artifact root: `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_20260425-144208\`

## Baseline

- Plan-mode baseline:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - result: `256 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - result: `141 passed`

## Phase 1 Triage

- Case 1 Kyoto company introduction:
  - runtime reason: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - body chars: `1034`
  - must-cover reflection: `0.625`
  - source trace: `0.2`
  - repair required/applied/rejected: `false / false / false`
  - hard warnings: `source_grounding:weak_reflection` plus fingerprint warnings
  - classification: source-backed material exists, but source reflection / flatness did not enter optional repair
- Case 4 rich case study:
  - runtime reason: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - body chars: `1109`
  - must-cover reflection: `0.3333`
  - source trace: `0.6667`
  - repair required/applied/rejected: `false / false / false`
  - hard warnings: `contract_alignment_must_cover_reflection_rate<0.50` plus fingerprint warnings
  - classification: case-study source slots reach grounding, but source-backed required slots were not connected to `must_cover` / shadow inputs

## Implemented Runtime Changes

- Company introduction:
  - owner: `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - added a company-introduction-only weak source-reflection repair activation using existing diagnostics and existing optional repair path
  - tightened acceptance metadata for source reflection / fingerprint improvement
  - kept repair count unchanged and did not relax quality thresholds or target length
  - added bounded rejection coverage for unsupported claims and internal/source-limit leakage
- Case study:
  - owner: `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - updated only case-study runtime contract merging so source-backed required slot values enter `must_cover` and shadow inputs
  - improved case-study source slot extraction for before/change/after/remaining issue without all-article routing
  - kept source-outside metrics, customer names, awards, and unbacked outcomes prohibited
- Tests:
  - owner: `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - added focused coverage for company-introduction weak reflection repair activation, rejection, and negated source-boundary wording
  - added focused coverage for rich case-study source-backed `must_cover` / shadow inputs and leakage / unsupported-claim rejection

## Test Results

- Focused company introduction:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "company_intro or company_introduction"`
  - result: `87 passed, 151 deselected`
- Focused case study:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "case_study"`
  - result: `9 passed, 229 deselected`
- Owner-local regression:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - result: `260 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
  - result: `105 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q`
  - result: `36 passed`
- Phase 7 shared regression:
  - not run because Phase 6 reached stop boundary before green closeout

## Backend Live Rerun

- Artifact: `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_20260425-144208\backend_validation_summary.json`
- Case 1 Kyoto company introduction:
  - success: `true`
  - runtime reason: `OK`
  - body chars: `1079`
  - repair required/applied/rejected: `false / false / false`
  - output guard reasons: none
  - visible internal leakage: none
  - old/new classification: `success`
- Case 4 rich case study:
  - success: `true`
  - runtime reason: `OK`
  - body chars: `880`
  - repair required/applied/rejected: `false / false / false`
  - output guard reasons: none
  - visible internal leakage: none
  - old/new classification: `success`

## UI Operation Validation

- UI: `http://127.0.0.1:18080/`
- Operation script: `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_20260425-144208\ui_validate_rerun4.py`
- Summary: `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_20260425-144208\ui\ui_validation_summary_rerun4.json`
- Case 1 Kyoto company introduction:
  - UI status: `failed`
  - runtime success: `false`
  - runtime reason: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - body chars: `1122`
  - must-cover reflection: `0.625`
  - source trace: `0.2`
  - output guard reasons: fingerprint warnings plus `source_grounding:weak_reflection`
  - empty result: `false`
  - stale result suspected: `false`
  - visible/body internal leakage: none
  - additional observation: optional repair ran and applied in the latest UI output, but final output guard still detected weak source reflection after acceptance
- Case 4 rich case study:
  - UI status: `failed`
  - runtime success: `false`
  - runtime reason: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - body chars: `1289`
  - must-cover reflection: `0.5714`
  - source trace: `0.4444`
  - output guard reasons: fingerprint warnings plus `source_grounding:weak_reflection`
  - empty result: `false`
  - stale result suspected: `false`
  - visible/body internal leakage: none
  - additional observation: old `contract_alignment_must_cover_reflection_rate<0.50` symptom is gone, but source-reflection / fingerprint failure remains and optional repair did not activate

## Phase Ledger

| Phase | Owner files | Changed responsibility | Behavior change | Tests run | Result | Failure attempts | Next phase |
|---|---|---|---|---|---|---|---|
| 0 | plan package | package / baseline | no | baseline commands | `256 passed`; `141 passed` | 0 | Phase 1 |
| 1 | logs | fail-closed payload classification | no | log inspection | Case 1 / Case 4 causes split | 0 | Phase 2 |
| 2 | `note\simple_note_pipeline\pipeline.py`; `note\tests\test_simple_note_pipeline.py` | company-introduction-only weak source-reflection repair activation and acceptance guards | yes | focused company intro; owner-local shared | passed | 1 runtime fix attempt | Phase 3 |
| 3 | `note\simple_note_pipeline\pipeline.py`; `note\tests\test_simple_note_pipeline.py` | case-study source-backed required slots into contract alignment inputs | yes | focused case study; owner-local shared | passed | 1 runtime fix attempt | Phase 4 |
| 4 | test suite | owner-local regression | no | owner-local regression commands | `260 passed`; `105 passed`; `36 passed` | 0 | Phase 5 |
| 5 | backend live logs | backend live rerun | no | live backend runner | both target cases `OK` | 0 | Phase 6 |
| 6 | UI operation logs | actual UI validation | no | Selenium UI operation | both target cases still fail-closed | Case 1: 3 same-error observations; Case 4: 3 same-error observations | stop/report |

## Stop Analysis

- Case 1 repeated same error:
  - historical UI validation: `SYS_QUALITY_WARNINGS_UNRESOLVED`, no repair
  - backend after fix: `OK`
  - actual UI after fix: `SYS_QUALITY_WARNINGS_UNRESOLVED`; repair applied, but final guard still reports weak source reflection plus fingerprint warnings
  - likely connection issue: final output-guard source reflection is detected after the current company-introduction repair acceptance path, so acceptance metadata can be green while final guard remains red
- Case 4 repeated same error:
  - historical UI validation: `SYS_QUALITY_WARNINGS_UNRESOLVED` with `contract_alignment_must_cover_reflection_rate<0.50`
  - backend after fix: `OK`
  - actual UI after fix: `SYS_QUALITY_WARNINGS_UNRESOLVED`; old contract-alignment warning removed and must-cover reflection improved from `0.3333` to `0.5714`, but source reflection / fingerprint warnings remain
  - likely connection issue: case-study contract slot wiring was fixed, but rich UI case still lacks a case-study-scoped source-reflection repair trigger or equivalent final acceptance connection

## Follow-up Outside Scope

- Case 3 insufficient case-study UI precheck boundary remains a separate follow-up.
- New follow-up needed for UI-only source-reflection/fingerprint fail-closed after backend success:
  - Case 1: connect final source-reflection guard to company-introduction repair acceptance / rejection timing.
  - Case 4: decide whether a case-study-scoped source-reflection repair trigger is needed after contract slot wiring.
