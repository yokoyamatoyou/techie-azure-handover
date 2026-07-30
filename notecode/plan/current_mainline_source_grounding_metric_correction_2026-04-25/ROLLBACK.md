# ROLLBACK

## Boundary

Rollback is limited to:

- `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- focused tests added to `C:\tetie\notecode\note\tests\test_newalgorithm_phase06_logging_compat.py`
- this package docs
- `C:\tetie\WORKLOG.md`

## Stop Conditions

Stop and report if any of these become necessary:

- changing prompt, generation, repair, target length, or source packet construction
- changing source grounding threshold or fingerprint threshold
- changing `quality_guard.py`
- changing `output_guard.py`
- changing UI demote policy
- broad pass for duplicate/title-like source items
- passing Case 1 mixed or true omission fixtures
- touching a second product owner file

## Rollback Action

Revert the auxiliary metrics and weak-warning condition change in `quality_observability_mixin.py`, remove focused tests for this package, and mark this package stopped with `observe-only` or a new narrow owner decision.
