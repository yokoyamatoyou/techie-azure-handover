# current_mainline_log_source_ui_regression_2026-04-26 TASK

## Global Rules

- Product code / prompt / threshold / repair / guard / UI implementation must remain unchanged.
- Use historical source as-is; thin or mismatched source is allowed for replay comparison.
- Record source caveats separately from runtime/UI defects.
- Stop on technical errors after preserving artifact and classification; do not fix in-place.
- UI execution is primary. Backend harness is not used for generation.
- Lenient collection is allowed only after confirming a fresh latest snapshot.

## Phase Map

| Phase | Scope | Exit |
|---|---|---|
| 0 | package + artifact root | README / TASK / PROGRESS / ROLLBACK and artifact dirs exist |
| 1 | source reconstruction | 9 source packets saved with `source_reconstructed_from_log.json` |
| 2 | historical baseline | comparable prior status recorded |
| 3 | regression tests before UI | requested pytest groups recorded |
| 4 | UI startup | `HEADLESS=1 PORT=18080` server reachable |
| 5 | UI article generation | 9 article types x 2 attempts saved |
| 6 | image validation | 2 eligible article image results saved |
| 7 | classification | per-attempt outcome and historical comparison complete |
| 8 | server closeout | UI process stopped and no 18080 listener remains |
| 9 | docs closeout | PROGRESS and WORKLOG updated |

## Attempt Record Contract

Each attempt records:

- final screenshot
- latest_generation_output.json
- latest_generation_quality_report.json
- source_reconstructed_from_log.json
- UI visible text
- title / lead / body / references / hashtags
- runtime_reason_code
- outcome
- blocked flag
- blocked_output_redacted
- repair_required / repair_applied / repair_rejected
- output_guard reasons
- soft warnings
- source grounding / must-cover / source slot metrics
- internal-term leakage
- source outside claim evidence
- Codex visible evaluation
- historical comparison classification

## Image Record Contract

For each image validation article, record:

- image_generation_status
- image prompts
- generated image paths
- file exists / non-empty / readable
- title-body-image alignment
- whether image failure affected body generation
- UI visible wording

## Required Checks

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_result_adapter.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_newalgorithm_phase06_logging_compat.py -q`

## Stop Conditions

- UI server cannot start or is unreachable.
- A non-harness technical failure prevents fresh artifact collection.
- Image generation raises a non-recoverable infrastructure error; preserve article result and classify image separately.
- Same phase reaches 3 failed correction attempts; this package should not perform code corrections.
