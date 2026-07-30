# current_mainline_source_grounding_observability_2026-04-25 TASK

## Global Rules

- `1 issue = 1 narrow hypothesis = 1 owner scope`.
- Owner is `quality_observability_mixin.py`.
- Product behavior must not change.
- Do not change thresholds, prompt, repair, target length, source packet, output guard, UI demotion, or current success path.
- Same error may be retried up to 3 times.

## Phase Map

| Phase | Scope | Owner files | Behavior change | Exit |
|---|---|---|---|---|
| 0 | package docs / schema | docs | no | README / TASK / PROGRESS / ROLLBACK exist |
| 1 | focused failing tests | `test_newalgorithm_phase06_logging_compat.py` | no | tests describe duplicate/title-like and partial-match diagnostics |
| 2 | minimal telemetry | `quality_observability_mixin.py` | no | diagnostics added without changing reflection ratio |
| 3 | validation | tests / saved artifacts | no | focused and owner-local checks pass |
| 4 | closeout | PROGRESS / WORKLOG | no | test results and artifact summary recorded |

## Required Checks

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q -k "source_grounding"
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_newalgorithm_phase06_logging_compat.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
```

## Stop Criteria

- Stop if implementation requires a second product owner file.
- Stop if existing reflection ratio, warning code, success/fail state, or output guard policy changes.
- Stop if diagnostics need to be shown in UI or body.
