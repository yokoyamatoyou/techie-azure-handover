# TASK

## Phase Map

| Phase | Gate |
|---|---|
| 0 package scaffold | README / TASK / PROGRESS / ROLLBACK created |
| 1 source reconstruction | historical log sources restored into the new artifact root |
| 2 UI server | `HEADLESS=1`, `PORT=18080`, app reachable |
| 3 full-flow UI attempts | active 8 article types x 2 attempts saved |
| 4 image validation | 2 requested image validation records saved |
| 5 regression tests | requested pytest groups completed |
| 6 classification | outcomes and issue classes recorded |
| 7 closeout | server stopped, no 18080 listener, PROGRESS + WORKLOG updated |

## Retry Stop

- Do not modify product code in response to failures.
- If a failure occurs, save artifact and classify it as one of:
  - source issue
  - route issue
  - UI harness issue
  - runtime quality issue
  - image issue
- If UI click/wait is brittle, use fresh snapshot confirmation and lenient collection only.

## Required Checks

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_result_adapter.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_newalgorithm_phase06_logging_compat.py -q
```

## Acceptance

- All active article attempts have saved attempt artifacts.
- Announcement FAQ facts are checked.
- Comparative concrete axes are checked and not collapsed to generic `総合`.
- Explanatory metadata denominator cleanup is checked.
- Fail-closed UX shape is checked.
- Two image validation records are saved.
- UI/body internal-term leakage is absent or explicitly recorded.
- Product code hashes are compared before and after.
