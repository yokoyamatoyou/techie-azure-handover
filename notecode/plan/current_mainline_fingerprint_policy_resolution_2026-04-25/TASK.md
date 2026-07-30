# current_mainline_fingerprint_policy_resolution_2026-04-25 TASK

## Global Rules

- `1 issue = 1 narrow hypothesis = 1 owner scope`.
- Do not retry product-wide stale/non-strict `output_guard` recomputation.
- Do not relax fingerprint thresholds or quality thresholds.
- Do not increase repair count.
- Do not change prompts, target length, source packet thickness, or article-type routing.
- Preserve public contract tests first.
- Same failure can be retried up to 3 times; stop and report after that.

## Phase Map

| Phase | Scope | Owner files | Behavior change | Exit |
|---|---|---|---|---|
| 0 | read / package / baseline | docs / logs | no | required docs/logs read and baseline green |
| 1 | guard policy map | output guard / UI connection | no | hard-stop promotion point and public contracts documented |
| 2 | artifact quality decision | logs | no | Case 1 / Case 4 visible quality and source grounding classified |
| 3 | policy decision | PROGRESS | no | choose A or B |
| 4 | focused tests | tests | no product behavior | warning-only and hard-stop boundaries covered |
| 5 | narrow implementation | output guard + UI final guard connection | yes, scoped | fingerprint-only eligible guard demotes to warning-only |
| 6 | owner-local regression | tests | no additional | focused and owner-local tests pass |
| 7 | backend rerun | logs | validation | Case 1 / Case 4 backend result saved |
| 8 | actual UI operation validation | UI logs | validation | Case 1 / Case 4 actual UI result saved |
| 9 | shared regression / closeout | docs / WORKLOG | no additional | final state recorded |

## Policy Condition

Fingerprint-only warning-only is allowed only when:

- reason is `SYS_QUALITY_WARNINGS_UNRESOLVED`
- the guard was warning fail-closed
- there are no hard reasons, manual hits, needed input items, or internal leakage
- every blocking reason and soft warning starts with `fingerprint:`
- final quality has no hard failure, semantic issue, instructional fragment, or non-fingerprint warning
- contract alignment has no forbidden topics, category mismatch, section contract issue, or speaker mismatch
- must-cover reflection and source trace coverage meet existing green signals

## Required Checks

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_result_adapter.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
```

## Validation Targets

- backend rerun:
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_policy_resolution_YYYYMMDD-HHMMSS\backend_rerun\`
- UI operation:
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_policy_resolution_YYYYMMDD-HHMMSS\ui\`
