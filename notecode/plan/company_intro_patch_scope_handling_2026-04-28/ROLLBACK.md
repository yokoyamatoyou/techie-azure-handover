# ROLLBACK

## Product Code Change

This package made no product code change.

Runtime files are outside this package rollback:

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\repair_acceptance.py`
- `C:\tetie\notecode\note\simple_note_pipeline\company_intro_source_contract.py`
- `C:\tetie\notecode\note\simple_note_pipeline\hidden_late_validation.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## Docs Rollback Boundary

Rollback for this package means deleting or superseding:

- `C:\tetie\notecode\plan\company_intro_patch_scope_handling_2026-04-28\README.md`
- `C:\tetie\notecode\plan\company_intro_patch_scope_handling_2026-04-28\TASK.md`
- `C:\tetie\notecode\plan\company_intro_patch_scope_handling_2026-04-28\PROGRESS.md`
- `C:\tetie\notecode\plan\company_intro_patch_scope_handling_2026-04-28\ROLLBACK.md`
- `C:\tetie\notecode\plan\company_intro_patch_scope_handling_2026-04-28\EXECUTION_PROMPT.md`
- matching entries in:
  - `C:\tetie\WORKLOG.md`
  - `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\PROGRESS.md`

## Implementation Rollback Boundary

If implementation is started later, rollback only the next owner diff:

- new helper:
  - `C:\tetie\notecode\note\simple_note_pipeline\company_intro_patch_scope.py`
- minimal pipeline hook:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- minimal prompt wording replacement if used:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- tests:
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

Do not rollback unrelated keep diffs:

- `company_introduction_operational_source_contract_v1`
- `hidden_late_validation_v1`
- `branding_operational_source_contract_v1`
- `comparative_review_source_contract_v1`
- image cover strategy fixes
- current mainline readiness docs

## Do-Not-Retry Hypotheses

- prompt_builder-only preservation wording tweak without pipeline acceptance boundary
- pipeline-only acceptance relaxation while prompt still instructs lead / heading preservation
- `repair_acceptance.py` first without a clean candidate rejected only by fingerprint / acceptance strictness
- route phrase single-word ban
- body-wide rewrite
- repair count increase
- fingerprint / quality / source grounding threshold relaxation
- source contract hard guard relaxation
- output formatter fix for this symptom
- UI or image owner for this symptom
- article-type fixed routing table
- persona / trial name injection into runtime prompt or visible output

## Stop Boundary For Future Implementation

Stop and report if:

- owner scope expands beyond helper + minimal hook + tests
- implementation needs broad prompt_builder accretion
- implementation needs repair_acceptance change before clean candidate evidence exists
- company_introduction 3-run rerun keeps route phrase in lead / heading
- current business / product-service / support scope is lost
- source-outside claim or internal leakage appears
- announcement / comparative smoke regresses

