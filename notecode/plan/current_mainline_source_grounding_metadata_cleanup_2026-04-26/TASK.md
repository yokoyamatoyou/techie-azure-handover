# current_mainline_source_grounding_metadata_cleanup_2026-04-26 TASK

## Phase Map

| Phase | Scope | Status |
|---|---|---|
| Phase 0 | Create package docs scaffold | completed |
| Phase 1 | Add focused failing tests | completed |
| Phase 2 | Implement denominator cleanup in owner file | completed |
| Phase 3 | Run focused tests | completed |
| Phase 4 | Run explanatory focused rerun | completed |
| Phase 5 | Run shared regression | completed |
| Phase 6 | Close PROGRESS and WORKLOG | completed |

## Gate

- Product change is limited to `quality_observability_mixin.py` and focused tests.
- No threshold changes.
- No prompt changes.
- No repair changes.
- No UI demotion changes.
- No `output_guard.py` changes.
- No `note_writer_app.py` changes.
- No `simple_note_pipeline/pipeline.py` changes.
- Metadata-like items are not written into body text.
- If no substantive source fact remains after filtering, do not pass automatically.

## Focused Test Requirements

Positive cleanup test:

- `source_grounding_items` contains:
  - 2 substantive facts
  - `C:\tetie\notecode\note\uploads\xxxx_01.txt`
  - `xxxx_01`
  - hash-like filename item
- body reflects the 2 substantive facts.
- expected:
  - denominator counts substantive facts only
  - source reflection ratio is `1.0`
  - `source_grounding:weak_reflection` is absent

Negative preservation test:

- A short substantive fact that is not URL/path/hash/filename-like remains in denominator.
- A fact with a natural date such as `2026年4月15日` is not treated as hash metadata.

## Verification Commands

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q -k "source_grounding"`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_newalgorithm_phase06_logging_compat.py -q`
- `C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py --case-ids bl-explanatory-misread-metric --attempts 1,2`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
