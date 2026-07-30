# TASK

## Phase Map

- **Phase 00: docs-only diagnosis.** Completed by this package. No product code changes.
- **Phase 01: company-introduction persona trial owner.** Proposed next implementation window.

## Phase 01 Owner

- Owner file: `C:\tetie\notecode\note\current_mainline_persona_trial.py`
- Narrow hypothesis: company-introduction persona guidance is making `相談の入口` / `相談前判断` / pre-contact late return the default article direction even when `pre_contact_decision` is missing from the source packet.

## Phase 01 Required Behavior

- Company introduction defaults to current business, service/product scope, support posture, and source-backed company facts.
- Consultation-entry and pre-contact decision wording is not an always-on heading, title, fact-priority, or late-return target.
- Source-backed consultation wording can still be used as a factual support point, but not as the article's organizing frame unless the relevant source slot exists.

## Gate

Phase 01 is complete only when all are true:

- Focused tests prove missing `reader_decision` / `pre_contact_decision` does not produce `相談前判断`, `相談の入口`, or `導入` as default steering.
- Reconstructed prompt for the 4 repro URLs no longer contains consultation-entry or pre-contact decision framing as the company-introduction default.
- One UI real-generation validation with the 4 repro URLs completes without consultation-entry title/heading/body framing.
- Quality guard and source grounding remain non-relaxed.

## Retry / Stop Rule

- Try at most 3 fixes within the same owner and hypothesis.
- If `current_mainline_persona_trial.py` cannot remove the default consultation framing without breaking current source-contract behavior, stop and report owner decomposition.
- Do not move to `prompt_builder.py`, `title_strategy.py`, repair trigger logic, or hidden late validation in the same phase.

## Focused Checks

Use focused tests only:

- Persona/prompt composition tests for company introduction.
- Current mainline company-introduction runner tests if already available.
- A real UI generation check with the repro URLs.

Do not run broad suites unless the focused tests reveal a shared-surface risk.

## Forbidden Changes

- No repair count increase.
- No always-on editing persona.
- No threshold relaxation.
- No broad source contract change.
- No new registry.
- No `pipeline.py`, `prompt_builder.py`, or `note_writer_app.py` bloat.
- No runtime/internal terms in article body or UI.
