# current_mainline_source_grounding_metadata_cleanup_2026-04-26 PROGRESS

## Current Status

- Package status: completed
- Current phase: Phase 6 closeout
- Date: `2026-04-26 JST`
- Owner: `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- Product code change: completed, owner-limited
- Prompt / threshold / repair / UI demote / output guard change: no
- Target case: `bl-explanatory-misread-metric`
- Source diagnosis package:
  - `C:\tetie\notecode\plan\current_mainline_explanatory_article_regression_diagnosis_2026-04-26\`

## Baseline

Diagnosis found that latest `source_grounding_items` contained two real facts plus three metadata-like items:

- `C:\tetie\notecode\note\uploads\b0296d34e5ad47b18185d251855fa430_01.txt`
- `C:\tetie\notecode\note\uploads\b4e7920fe6374363bec490bde9124752_02.txt`
- `b0296d34e5ad47b18185d251855fa430_01`

The body reflected the two real facts, but source reflection was computed as `2/5 = 0.4`, causing `source_grounding:weak_reflection`.

## Phase Ledger

| Phase | Status | Notes |
|---|---|---|
| Phase 0 docs scaffold | completed | README / TASK / PROGRESS / ROLLBACK created |
| Phase 1 focused failing tests | completed | metadata denominator positive and true-fact negative tests failed before fix as expected |
| Phase 2 owner fix | completed | `quality_observability_mixin.py` only |
| Phase 3 focused tests | completed | phase06 source grounding slice passed |
| Phase 4 UI rerun | completed | `bl-explanatory-misread-metric` attempts 1/2 passed after starting local UI server |
| Phase 5 shared regression | completed | requested shared pytest suites passed |
| Phase 6 closeout | completed | PROGRESS and WORKLOG updated |

## Implementation

- Added metadata-like source grounding filtering in `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`.
- Metadata-like items are excluded from the denominator, while raw count and excluded examples are retained for observability.
- Matching examples:
  - Windows paths such as `C:\...`
  - Unix-like paths
  - URL-only locator strings
  - filename-only locator strings
  - hash-like basename / upload ID strings
- Natural Japanese source facts, including facts with dates such as `2026年4月15日`, remain in the denominator.
- If filtering leaves no substantive source facts and multiple metadata items were present, `source_grounding:weak_reflection` still fires. This avoids a metadata-only packet passing automatically.

## Files Changed

- `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- `C:\tetie\notecode\note\tests\test_newalgorithm_phase06_logging_compat.py`
- `C:\tetie\notecode\plan\current_mainline_source_grounding_metadata_cleanup_2026-04-26\README.md`
- `C:\tetie\notecode\plan\current_mainline_source_grounding_metadata_cleanup_2026-04-26\TASK.md`
- `C:\tetie\notecode\plan\current_mainline_source_grounding_metadata_cleanup_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_source_grounding_metadata_cleanup_2026-04-26\ROLLBACK.md`
- `C:\tetie\WORKLOG.md`

## Guardrails Kept

- Threshold change: no
- Prompt change: no
- Repair change: no
- UI demote change: no
- `output_guard.py` change: no
- `note_writer_app.py` change: no
- `simple_note_pipeline/pipeline.py` change: no
- Source facts removed: no
- Unsupported claim guard relaxed: no

## Verification

Initial focused test run before implementation:

- Command: `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q -k "metadata_like_items_are_excluded or metadata_filter_keeps"`
- Result: failed as expected before fix.
  - Metadata denominator test saw `source_grounding_item_count=5` instead of expected `2`.
  - Metadata exclusion count was missing.

Focused tests after implementation:

- Command: `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q -k "metadata_like_items_are_excluded or metadata_filter_keeps"`
- Result: `2 passed, 30 deselected`

Source grounding slice:

- Command: `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q -k "source_grounding"`
- Result: `7 passed, 25 deselected`

Observability suites:

- Command: `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_newalgorithm_phase06_logging_compat.py -q`
- Result: `35 passed`

Explanatory UI rerun:

- Command: `C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py --case-ids bl-explanatory-misread-metric --attempts 1,2`
- First run: `ui_harness_failure` because the local UI server on `127.0.0.1:18080` was not running.
- Rerun after starting local UI server:
  - attempt 1: `publishable_success`, runtime reason `OK`, `blocked_output_redacted=false`, body chars `1993`
  - attempt 2: `publishable_success`, runtime reason `OK`, `blocked_output_redacted=false`, body chars `1678`
- UI server stopped after verification. Confirmed no `18080` listener remains.

Source grounding outcome in rerun:

| Attempt | raw items | effective denominator | metadata excluded | reflected | ratio | `source_grounding:weak_reflection` |
|---|---:|---:|---:|---:|---:|---|
| attempt 1 | 5 | 2 | 3 | 2 | 1.0 | absent |
| attempt 2 | 5 | 2 | 3 | 2 | 1.0 | absent |

Shared regression:

- Command: `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
- Result: `144 passed`

## Final Classification

- Fixed: `source_reflection_metric_false_negative` caused by metadata-like source grounding items polluting the denominator.
- Preserved: true source facts remain evaluated.
- Focused rerun result: no `input_required_block`; both attempts returned `publishable_success`.
- No separate UI demote, prompt, repair, threshold, or output guard change is needed for this issue.
