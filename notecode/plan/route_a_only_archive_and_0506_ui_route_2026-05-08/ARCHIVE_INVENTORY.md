# ARCHIVE_INVENTORY

Date: 2026-05-08 JST

## Decision

Route A current mainline stays. Existing non-Route-A experiments are treated as rejected or parked and should be removed from the current execution surface by an archive/code-move window.

This file is an inventory and execution plan only. No archive has been executed by this package.

## Keep Boundary

Keep these current runtime paths in place:

- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\route_b_0506_adapter.py` until the new 0506 adapter contract replaces it
- `C:\tetie\notecode\tools\run_route_b_0506_compare.py` until Window 3 supersedes it
- `C:\tetie\notecode\docs\route_b_0506_candidate_2026-05-08.md`
- `C:\tetie\notecode\docs\shadow_route_failure_history.md`

Do not move saved current Route A artifacts.

## Archive / Code Move Candidates

Move candidates after manifest preflight:

- `C:\tetie\notecode\note\simple_note_pipeline\vnext_materialization.py`
- `C:\tetie\notecode\note\simple_note_pipeline\vnext_prompt_contract.py`
- `C:\tetie\notecode\note\simple_note_pipeline\vnext_route.py`
- `C:\tetie\notecode\tools\run_deepresearch_vnext_compare.py`
- `C:\tetie\notecode\tools\run_deepresearch_generation_only_variant_compare.py`
- `C:\tetie\notecode\note\tests\test_vnext_materialization.py`
- `C:\tetie\notecode\note\tests\test_vnext_prompt_contract.py`
- `C:\tetie\notecode\note\tests\test_vnext_materialized_route.py`
- `C:\tetie\notecode\note\tests\test_deepresearch_vnext_compare_tool.py`
- `C:\tetie\notecode\note\tests\fixtures\vnext_materialization\`
- `C:\tetie\notecode\plan\deepresearch_vnext_route_2026-05-03\`

Also inventory and classify before moving:

- `C:\tetie\notecode\note\vnext\`
- `C:\tetie\notecode\note\vnext_adapters\`
- `C:\tetie\notecode\note\vnext_current_boundary.py`
- `C:\tetie\notecode\vnext_current_integration\`
- `C:\tetie\notecode\tools\run_vnext_overlap_calibration.py`
- `C:\tetie\notecode\tools\run_vnext_current_shared_eval.py`
- `C:\tetie\notecode\note\tests\test_vnext_pipeline.py`
- `C:\tetie\notecode\note\tests\test_vnext_current_boundary_freeze.py`
- `C:\tetie\notecode\note\tests\test_vnext_current_shared_eval.py`
- `C:\tetie\notecode\note\tests\test_vnext_current_ui_contract_adapter.py`
- `C:\tetie\notecode\note\tests\test_vnext_overlap_calibration.py`

These are listed separately because `current_mainline_runner.py` still imports `VNextPipeline` shadow projection today. Window 1 must remove or neutralize current references before moving them.

## Current References To Remove

Window 1 must remove or neutralize current execution references to rejected routes:

- `note/simple_note_pipeline/pipeline.py`
  - imports from `vnext_materialization.py` and `vnext_route.py`
  - `enable_materialized_onepass_editor_route_v1`
  - `enable_materialized_anchor_patch_route_v2`
  - `enable_materialized_simple_onepass_route_v1`
  - `vnext_materialized_route` result metadata for old routes
- `tools/run_deepresearch_vnext_compare.py`
- `tools/run_deepresearch_generation_only_variant_compare.py`
- Route D / Route E opt-in flags in generation-only variant tools.
- vNext/materialized tests that assert old opt-in route behavior as runnable current behavior.
- docs that describe old experiments as adoption candidates or runnable next steps.

Window 1 must also decide how to handle current `VNextPipeline` shadow projection:

- either keep it as a distinct current boundary if still required by current product docs, or
- remove the import/projection path and move `note\vnext*` with tests in the same owner window.

Do not move `note\vnext*` until that decision is made and current owner tests pass.

## Move Target

Use this target:

```text
C:\tetie\notecode\archive\route_experiments_rejected_2026-05-08\
```

Stop if the target already exists and is non-empty.

Required archive files:

- `MANIFEST.json`
- `RESTORE_NOTE.md`
- `PRE_MOVE_INVENTORY.json`
- `HASHES.sha256`

## Manifest Policy

`MANIFEST.json` must record:

- source path
- destination path
- item type: `file` or `directory`
- byte size
- file count for directories
- SHA-256 hash for files
- route family: `materialized`, `deepresearch`, `route_d`, `route_e`, `vnext_shadow`, or `0506_provenance`
- move reason
- keep/restore note

Do not record secret values. If a file path implies `.env`, `.venv`, credentials, or local browser profiles, stop and report before moving.

## Rollback Note

`RESTORE_NOTE.md` must state:

- this is archive-only, not deletion
- original paths and restore command shape
- Route A keep boundary
- tests required after restore
- warning that old experiments are rejected/parked and must not be reactivated without a new approval window

## Window 1 Validation

Required checks after code-reference cleanup and move:

- `C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile note\current_mainline_runner.py note\newalgorithm_pipeline\pipeline.py note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
- targeted import check that `note.route_b_0506_adapter` still imports

If these fail after three focused attempts, stop with blocked status and do not continue to Window 2.
