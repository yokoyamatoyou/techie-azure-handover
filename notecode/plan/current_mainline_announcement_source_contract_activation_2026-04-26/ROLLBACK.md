# ROLLBACK

## Rollback Boundary

This package changed one product owner file and one focused test file:

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

Docs / records:

- `C:\tetie\notecode\plan\current_mainline_announcement_source_contract_activation_2026-04-26\`
- `C:\tetie\WORKLOG.md` entry for this package

Validation artifact:

- `C:\tetie\notecode\logs\current_mainline_announcement_source_contract_activation_20260426-103445\`

## Runtime Rollback

If rollback is required, revert only the announcement fallback source contract activation changes in `pipeline.py` and the two focused tests added for this package.

Do not revert unrelated current-mainline work.

## Do Not Roll Back

- Do not change thresholds.
- Do not add prompt text.
- Do not add repair attempts.
- Do not change UI demote / app classification.
- Do not reopen the diagnosis package as a product fix.

## Expected After Rollback

The old failure mode may return:

- `_announcement_source_contract.scope_match=false` or `source_contract_available=false`
- FAQ facts omitted from `source_grounding_items` / `must_cover`
- `bl-announcement-spec-change` body may omit the FAQ preparation and day-of checklist facts
