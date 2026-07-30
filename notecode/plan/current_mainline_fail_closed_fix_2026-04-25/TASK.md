# current_mainline_fail_closed_fix_2026-04-25 TASK

## Global Rules

- `1 issue = 1 narrow hypothesis = 1 owner scope`.
- Company introduction and case study are fixed separately and not mixed as one behavior.
- Current success path remains unchanged.
- Same phase may retry the same error up to `3` times, then stop and report.
- Green / no issue cases continue without user confirmation.

## Phase Map

| Phase | Scope | Owner files | Behavior change | Exit |
|---|---|---|---|---|
| 0 | read / package / baseline | plan package | no | required files/logs read and baseline tests recorded |
| 1 | fail-closed triage | logs / PROGRESS | no | Case 1 and Case 4 failure payloads classified |
| 2 | company intro fix | `note/simple_note_pipeline/pipeline.py`, focused tests | yes | source-backed weak reflection can enter existing optional repair once |
| 3 | case study fix | `note/simple_note_pipeline/pipeline.py`, focused tests | yes | rich case-study required slots reach `must_cover` / shadow inputs |
| 4 | owner-local regression | tests | no additional | focused and owner-local checks pass |
| 5 | backend live rerun | timestamped logs | validation | Case 1 / Case 4 backend results recorded |
| 6 | UI operation validation | UI logs/screenshots | validation | Case 1 / Case 4 actual UI runs recorded |
| 7 | closeout | PROGRESS / ROLLBACK / optional WORKLOG | no additional | final state and residual risks recorded |

## Required Checks

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "company_intro or company_introduction"
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "case_study"
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
```

## Live Validation

- Backend logs:
  - `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_YYYYMMDD-HHMMSS\`
- UI logs:
  - `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_YYYYMMDD-HHMMSS\ui\`
- UI URL:
  - `http://127.0.0.1:18080/`

## Stop Boundary

- Same target keeps the same failure after 3 attempts.
- Fix requires quality threshold relaxation, target length change, or repair count increase.
- Fix requires source-outside claims or generic padding.
- Fix requires multiple owner files beyond the narrow runtime/test scope.
