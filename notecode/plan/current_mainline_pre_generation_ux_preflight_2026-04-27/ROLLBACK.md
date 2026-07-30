# ROLLBACK

## Boundary

There is no Git repo in `C:\tetie\notecode` or `C:\tetie`. Rollback must use file-level restore from backup / hashes / WORKLOG notes.

## Preserve

Keep the accepted launch-blocker source contract files unless a later owner explicitly changes them:

- `C:\tetie\notecode\note\simple_note_pipeline\company_intro_source_contract.py`
- `C:\tetie\notecode\note\simple_note_pipeline\company_intro_source_contract_guard.py`

## Revert If Needed

For Phase 1 UI separation rollback, revert only these files to their previous local state:

- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\note_writer_app_main_page_sections.py`
- `C:\tetie\notecode\note\current_mainline_ui_result_adapter.py`
- `C:\tetie\notecode\note\tests\test_note_writer_app_generation_gate_helpers.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_ui_result_adapter.py`
- `C:\tetie\notecode\note\tests\test_newalgorithm_phase06_logging_compat.py`

For Phase 0 rollback hygiene rollback, restore `prompt_builder.py` and matching prompt tests from the accepted launch-blocker baseline if an exact `82DC095B...` artifact is later found:

- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## Do Not Do

- Do not roll back `company_intro_source_contract*.py` as part of Phase 1 rollback.
- Do not reopen pre-2026-04-02 archive / frozen architecture package.
- Do not replace this package as current source-of-truth.
- Do not add prompt bans / few-shot examples to compensate for Phase 1 issues.
