# ROLLBACK

## Boundary

Rollback is limited to the UI owner and helper tests:

- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py`

## Baseline Hash Source

Before baseline:

`C:\tetie\notecode\logs\pre_user_trial_min_ui_confirmation_20260426-221608\product_code_hash_after.json`

`note_writer_app.py`

- before: `11D73D12ACB64D51A652DD36E59A55243B0CF5FCF299901724882AD2E9AAB7D6`
- after: `FCDB40E9EAA9347D2E0ACCCAD09F80493F7AD21D9410B4CDB6D87C919FA6D27D`

## Do Not Roll Back

Do not touch:

- persona / algorithm docs
- source contract
- prompt_builder
- simple/newalgorithm pipeline
- quality_guard / output_guard
- blog_image_auto / image prompt
- threshold / repair count / target length settings

## Rollback Method

Revert only the article type handoff defaults, managed default event suppression, and corresponding helper tests.
