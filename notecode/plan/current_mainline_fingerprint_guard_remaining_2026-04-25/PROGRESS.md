# current_mainline_fingerprint_guard_remaining_2026-04-25 PROGRESS

## Current Status

- Package status: stopped / no product behavior change
- Current phase: Phase 4 stop/report
- Behavior change: no
- Current hypothesis:
  - `fingerprint_false_positive_or_guard_policy_residual`
  - predecessor backend OK was not final-guard-equivalent to UI because saved backend artifacts reused an existing non-strict `output_guard`.
  - forcing product-wide recomputation of existing non-strict guards is not an acceptable narrow fix because it breaks current-mainline public-contract success tests.

## Baseline

- Plan-mode read completed:
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\ALGORITHM.md` sections 4, 5, 12
  - current naturalness package README / TASK / PROGRESS / ROLLBACK
  - predecessor package progress and logs
  - `C:\tetie\WORKLOG.md`
- Baseline tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - result: `260 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - result: `141 passed`

## Initial Triage

- Case 1:
  - UI final guard: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - final guard reasons: fingerprint warnings
  - source reflection: `0.6`; previous intermittent `source_grounding:weak_reflection` is a mixed issue and remains separate follow-up if it recurs.
  - repair candidate improved fingerprint from `7` flags to `6`, but final candidate still retained fingerprint flags; adopting candidate alone is not sufficient.
  - visible quality: acceptable but steady / flat.
- Case 4:
  - UI final guard: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - final guard reasons: fingerprint warnings only
  - source reflection: `1.0`
  - no repair candidate; repair not required by current trigger.
  - visible quality: acceptable and source-grounded, but fingerprint-only strict guard fails.
- Cross-case connection finding:
  - UI artifacts include `strict_saas_mode=medium` and final `output_guard.warning_fail_closed=true`.
  - predecessor backend OK artifacts include non-blocking existing `output_guard` without `strict_saas_mode`; final guard was not recomputed against strict mode.

## Runner-Equivalent Guard Triage

- Artifact:
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_guard_remaining_20260425-163600\classification.md`
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_guard_remaining_20260425-163600\runner_equivalent_guard_triage.json`
- Case 1 UI equivalent:
  - stored guard: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - pure recomputed guard: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - final fingerprint flags: `7`
  - repair candidate fingerprint flags: `6`
  - repair rejected: `company_intro_naturalness_not_improved`
- Case 4 UI equivalent:
  - stored guard: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - pure recomputed guard: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - final fingerprint flags: `7`
  - repair not required / no candidate
- Case 1 backend OK artifact:
  - stored guard: non-blocking, no `strict_saas_mode`
  - pure recomputed guard: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - current `apply_generation_output_guard()` result: `OK` because existing non-blocking guard is reused
- Case 4 backend OK artifact:
  - stored guard: non-blocking, no `strict_saas_mode`
  - pure recomputed guard: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - current `apply_generation_output_guard()` result: `OK` because existing non-blocking guard is reused

## Attempted Narrow Fix

- Attempt:
  - Changed `apply_generation_output_guard()` to recompute and prefer current strict guard when existing guard lacked current strict mode or was less strict.
  - Added focused runner regression for stale non-strict guard reuse.
- Focused tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py -q -k "output_guard or soft_warnings or fingerprint"`
  - result: `3 passed, 74 deselected`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "fingerprint or repair or company_intro or case_study"`
  - result: `130 passed, 108 deselected`
- Rejection:
  - Owner-local runner/regression failed `3` existing public-contract tests because product-wide recomputation turns known current-mainline fingerprint-only red guard into fail-closed success regression.
  - Failing tests:
    - `test_execute_current_mainline_generation_keeps_gen_e451e736_company_intro_public_contract`
    - `test_current_mainline_clean_mock_llm_result_passes_pure_output_guard`
    - `test_current_mainline_company_intro_uses_company_outline_headings`
  - The attempted product code/test diff was reverted.
- Recheck after revert:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py -q -k "output_guard or soft_warnings or fingerprint or gen_e451e736"`
  - result: `3 passed, 73 deselected`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_regressions.py -q -k "clean_mock_llm_result or company_intro_uses_company_outline_headings"`
  - result: `2 passed, 27 deselected`

## Phase Ledger

| Phase | Owner files | Changed responsibility | Behavior change | Tests run | Result | Failure attempts | Next phase |
|---|---|---|---|---|---|---|---|
| 0 | plan package / inspection | package creation and baseline | no | baseline commands | `260 passed`; `141 passed` | 0 | Phase 1 |
| 1 | logs / output guard inspection | runner-equivalent final guard triage | no | artifact inspection / pure guard recompute | backend OK artifacts are not strict-final-guard equivalent | 0 | Phase 2 |
| 2 | logs | visible quality review | no | artifact reading | Case 1/4 acceptable; Case 1 repair candidate still fingerprint-red | 0 | Phase 3 |
| 3 | PROGRESS | root cause classification | no | inspection | `fingerprint_false_positive_or_guard_policy_residual`; source reflection separate | 0 | Phase 4 |
| 4 | attempted `output_guard.py` / test diff, reverted | product-wide stale guard recompute | no kept change | focused green, owner-local failed, revert recheck green | rejected as too broad | 1 | stop/report |

## Stop Decision

- No product code fix is kept.
- Passing these UI cases by guard change would require changing current fingerprint warning fail-closed policy or adding a realization improvement path, both outside the allowed narrow connection fix.
- Next acceptable package would be a separate realization-quality package for fingerprint-only acceptable-but-flat artifacts, not threshold relaxation.

## Final Verification

- Required baseline rerun:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - result: `260 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - result: `141 passed`
- Shared closeout:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
  - result: `343 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q`
  - result: `36 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_vnext_current_boundary_freeze.py -q`
  - result: `6 passed`

## WORKLOG / AGENTS

- `C:\tetie\WORKLOG.md` updated.
- `AGENTS.md` update not needed because current source-of-truth remains `naturalness_recovery_2026-04-07`.
