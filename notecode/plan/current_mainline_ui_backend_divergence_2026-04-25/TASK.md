# current_mainline_ui_backend_divergence_2026-04-25 TASK

## Global Rules

- Start from backend/UI payload diff before changing runtime.
- Company introduction and case study are classified separately.
- `1 phase = 1 narrow hypothesis = 1 owner scope`.
- Keep current success path unchanged.
- Same UI failure may be retried up to `3` times, then stop and report.
- Do not change thresholds, repair count, target chars, source packet thickness, or prompt strategy.

## Phase Map

| Phase | Scope | Owner files | Behavior change | Exit |
|---|---|---|---|---|
| 0 | read / package / baseline | plan package | no | required docs/logs read and baseline tests recorded |
| 1 | backend vs UI payload diff | logs | no | Case 1 / Case 4 JSON and Markdown diff saved |
| 2 | root cause classification | logs / PROGRESS | no | each case classified independently |
| 3 | Case 1 narrow fix | UI/runner/harness, or runtime only if proven | conditional | one owner-scope hypothesis applied or no code fix needed |
| 4 | Case 4 narrow fix | UI/runner/harness, or runtime only if proven | conditional | one owner-scope hypothesis applied or no code fix needed |
| 5 | backend equivalence rerun | logs | validation | backend run uses same input contract shape as UI |
| 6 | UI operation validation | UI logs/screenshots | validation | Case 1 / Case 4 actual UI results saved |
| 7 | regression / closeout | PROGRESS / ROLLBACK / WORKLOG if needed | no additional | final state and residual risks recorded |

## Required Diff Fields

- `input_contract`
- `source_inputs` / `source_documents`
- `source_trace` / `source_trace_policy`
- `article_type` / `semantic_article_key`
- `content_goal` / `writing_focus` / `structure`
- `length_mode` / `target_chars`
- company-introduction / case-study source contract snapshots
- `source_grounding_items`
- `must_cover`
- repair required / applied / rejected and metadata
- final diagnostics
- output guard reasons
- hard / soft warnings
- body candidate summary

## Classification Candidates

- `ui_input_mapping_diff`
- `ui_source_handoff_diff`
- `ui_source_fetch_trace_diff`
- `ui_contract_resolution_diff`
- `backend_runner_not_equivalent`
- `final_guard_after_repair_connection`
- `repair_acceptance_connection`
- `source_reflection_guard_false_positive`
- `fingerprint_guard_remaining`
- `unknown`

## Required Checks

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
```

If a product code fix is made:

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_vnext_current_boundary_freeze.py -q
```

## Log Targets

- Diff and rerun logs:
  - `C:\tetie\notecode\logs\current_mainline_ui_backend_divergence_YYYYMMDD-HHMMSS\`
- UI validation logs:
  - `C:\tetie\notecode\logs\current_mainline_ui_backend_divergence_YYYYMMDD-HHMMSS\ui\`
- UI URL:
  - `http://127.0.0.1:18080/`

## Stop Boundary

- Same `SYS_QUALITY_WARNINGS_UNRESOLVED` UI failure repeats 3 times after equivalent input is proven.
- More than one product owner must be changed.
- Fix requires quality threshold relaxation, target length tuning, or repair count increase.
- Fix requires source-outside claims, generic padding, or visible internal terms.
