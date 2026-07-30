# pipeline_source_contract_split_planning_2026-04-26 ROLLBACK

## Phase 00 Rollback Boundary

This package is docs-only.

Rollback for this package is limited to:

- remove `C:\tetie\notecode\plan\pipeline_source_contract_split_planning_2026-04-26\`
- remove the matching `C:\tetie\WORKLOG.md` entry

No product code rollback is needed for Phase 00 because no product code is changed.

## Product Code Boundary

Untouched in this package:

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
- prompt files
- threshold / repair / guard policy

## Future Phase 01 Rollback Boundary

If announcement extraction is implemented and fails, rollback is:

- delete or stop using `note\simple_note_pipeline\announcement_source_contract.py`
- restore announcement helper definitions in `pipeline.py`
- remove announcement imports from `pipeline.py`
- keep `_prepare_runtime_source_contracts`, `_refresh_diagnostics_state`, `_run_optional_repair`, and `generate()` behavior equivalent to the pre-extraction state

## Do Not Retry Unchanged

- Do not start with `source_contract_common.py`.
- Do not combine announcement and comparative extraction in one phase.
- Do not extract company intro runtime source contract first.
- Do not treat full-flow residual fixes as part of source contract split.
- Do not change prompt / threshold / repair / output_guard / UI to make extraction tests pass.

