# current_mainline_ui_past_failure_validation_2026-04-25 PROGRESS

## Current Status

- Package status: validation complete
- Current phase: Phase 7 closeout
- Behavior change: yes, UI error-display only
- Current hypothesis:
  - Past failure inputs should be validated through the actual UI -> current mainline path before opening any new realization fix. UI route defects should be separated from runtime body thinness.

## Baseline Notes

- Current success path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current mainline remains `single-pass + optional single repair 1回`.
- `company_introduction_operational_source_contract_v1` remains runtime keep.
- `company_intro_source_packet_thickness_2026-04-25` remains partial improvement keep.

## Phase Ledger

| Phase | Owner files | Changed responsibility / validation responsibility | Behavior change | Tests run | Result | Failure attempts | Next phase |
|---|---|---|---|---|---|---|---|
| 0 | `plan/current_mainline_ui_past_failure_validation_2026-04-25/*` | package creation, baseline record | no | `pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`; `pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q` | `256 passed`; `343 passed` | 0 | Phase 1 |
| 1 | `note/note_writer_app.py` startup path | UI startup command and port validation | no | manual server start | UI served at `http://127.0.0.1:18080/` | 0 | Phase 2 |
| 2 | Browser Use / timestamped logs | Actual UI operation and artifact capture | no | Browser Use screenshots/DOM | startup, filled states, result states saved under `logs/current_mainline_ui_past_failure_validation_20260425-110220/` | 0 | Phase 3 |
| 3 | UI -> current mainline | Case 1-4 validation through UI controls and URL source inputs | no | live UI runs | Case 1 fail-closed; Case 2 UI input-boundary; Case 3 fail-closed; Case 4 fail-closed | 0 | Phase 4 |
| 4 | `note/current_mainline_ui_result_adapter.py` | Visible quality/error review; generation error display classification | yes | visual DOM review | pre-fix output-guard display leaked internal reason/fingerprint/contract terms | 1 narrow UI display fix | Phase 5 |
| 5 | `note/current_mainline_ui_result_adapter.py`; `note/tests/test_current_mainline_ui_result_adapter.py` | Sanitize visible blocked-output explanation while preserving runtime/log payload | yes | `pytest note\tests\test_current_mainline_ui_result_adapter.py -q` | `22 passed`; retry UI display had no internal terms in visible excerpt | 1/3 | Phase 6 |
| 6 | shared UI/runtime tests | Regression after UI display fix | yes | `pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`; `pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`; `pytest note\tests\test_current_mainline_ui_matrix.py -q` | `256 passed`; `105 passed`; `36 passed` | 0 | Phase 7 |
| 7 | plan/log docs | Closeout records and summary | yes | record review | `validation_records.json` and `summary.md` saved | 0 | close |

## Phase 0 Read Notes

- Read before package creation:
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\ALGORITHM.md` sections 4, 5, 12
  - current naturalness package README/TASK/PROGRESS/ROLLBACK
  - pipeline responsibility split PROGRESS
  - company intro length diagnosis PROGRESS
  - company intro source packet thickness README/TASK/PROGRESS/ROLLBACK
  - specified prior logs
  - `C:\tetie\WORKLOG.md`

## UI Startup Plan

- Command:

```text
$env:HEADLESS='1'; $env:PORT='18080'; C:\tetie\notecode\.venv\Scripts\python.exe -m note.note_writer_app
```

- Expected URL:

```text
http://127.0.0.1:18080/
```

## Validation Log Target

- Actual:

```text
C:\tetie\notecode\logs\current_mainline_ui_past_failure_validation_20260425-110220\
```

## UI Run Results

- Case 1 `branding / company_introduction / grounded` with Kyoto URLs:
  - UI route accepted URL inputs and mapped `semantic_article_key=company_introduction`.
  - Result: fail-closed, `SYS_QUALITY_WARNINGS_UNRESOLVED`, no visible success article.
  - Classification: `fail_closed_ok`; next action `realization_shallow_followup`.
- Case 2 company-profile style source:
  - Restored text sources were added as `httpbingo.org/base64/...` URLs because Browser Use upload automation was not stable and local/private URLs are blocked by URL safety.
  - Result: UI input-boundary before generation; no weak success.
  - Classification: `fail_closed_ok`; next action `no_fix`.
- Case 3 `case_study / implementation_case` insufficient source:
  - UI precheck passed where the historical direct runner had `INP_SOURCE_CONTEXT_INSUFFICIENT`.
  - Generation did not return success; it fail-closed on quality warnings.
  - Classification: no false-positive success, but input-boundary weakness remains follow-up.
- Case 4 rich case-study rerun source:
  - UI route accepted sufficient source and mapped `semantic_article_key=implementation_case`.
  - Result: fail-closed on quality warnings, so expected success was not met.
  - Classification: not a UI source handoff failure; record as `realization_shallow_followup`.

## Narrow Fix Applied

- Owner:
  - `C:\tetie\notecode\note\current_mainline_ui_result_adapter.py`
  - `C:\tetie\notecode\note\tests\test_current_mainline_ui_result_adapter.py`
- Change:
  - Visible blocked-output UI no longer prints internal keys or metric names such as `error_class`, `reason_code`, `SYS_*`, `fingerprint`, `contract_alignment`, or `must_cover`.
  - Runtime/log payload fields are unchanged.
- Retry:
  - Re-ran Case 3 after server restart.
  - UI displayed: `品質確認で停止しました。本文は表示していません。`
  - Visible excerpt had no internal terms.

## Saved Artifacts

- `C:\tetie\notecode\logs\current_mainline_ui_past_failure_validation_20260425-110220\validation_records.json`
- `C:\tetie\notecode\logs\current_mainline_ui_past_failure_validation_20260425-110220\summary.md`
- Case screenshots / DOM snapshots / audit entries are stored in the same directory.

## Next Action

- Do not broaden source packet thickness in this package.
- Treat the remaining Case 1 / Case 4 fail-closed results as `realization_shallow_followup` unless a separate direct-run regression proves otherwise.
- Treat Case 3 UI precheck accepting insufficient source as a separate input-boundary follow-up; it did not become a false-positive success in this run.
