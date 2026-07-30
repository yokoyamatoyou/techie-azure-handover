# ROLLBACK

## Baseline

Runtime baseline remains the current mainline:

- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

Latest diagnostic artifact:

- attempt: `gen-75fac897`
- source fetch: 4 URLs succeeded
- generation core: completed
- issue: final company-introduction output still uses consultation-entry framing

## Docs-Only Rollback

This package is docs-only. If the diagnosis package itself is wrong, remove or revise only:

- `C:\tetie\notecode\plan\current_mainline_company_intro_persona_packet_diagnosis_2026-04-27\`
- the matching `C:\tetie\WORKLOG.md` entry

Do not touch product code for docs-only rollback.

## Next Implementation Rollback Boundary

For Phase 01 implementation, rollback is limited to:

- `C:\tetie\notecode\note\current_mainline_persona_trial.py`
- focused tests added or changed for that owner
- progress notes for this package

Do not roll back accepted source contract changes from the pre-generation UX preflight.

## Do Not Reopen

- pre-2026-04-02 archive records
- frozen architecture package
- completed reference packages
- failed `prompt_builder.py` prompt-surface patch

## Stop Conditions

Stop and report instead of widening scope if:

- removing default consultation framing from `current_mainline_persona_trial.py` does not change the reconstructed prompt
- the prompt improves but UI real generation still shows `相談の入口` / `相談前判断` as the article frame
- title contamination remains and requires a separate `title_strategy.py` owner
- semantic repair must be changed to catch residual bridge wording
