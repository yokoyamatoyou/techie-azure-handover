# PHASE 07: Integration & Rollout

## Objective
Integrate `human_resonance2` quality layer into existing generation flow with safe rollout and rollback.

## Inputs
- integration contract (`integration_contract.md`)
- config contract (`config_contract.md`)
- existing pipeline entry: `ArticleGenerator._apply_resonance()`
- config keys:
  - `quality_pipeline.enabled`
  - `quality_pipeline.mode` (`off` / `shadow` / `enforce`)
  - `quality_pipeline.rollout_percent`

## Outputs
- integration plan (code touchpoints and order)
- rollout checklist
- monitoring and rollback criteria

## Tasks (GPT-5 mini granularity)
1. Add `shadow` mode path (measure only, no user-visible rewrite).
2. Add `enforce` mode path (apply approved adjustments).
3. Add per-request isolation for temporary state/cache.
4. Add logs for score deltas, drift alerts, and gate decisions.
5. Document operational handoff in:
   - `C:\tetie\azure-handoff-2026-02-09-ja.md`
   - `C:\tetie\WORKLOG.md`

## DoD
1. `off/shadow/enforce` modes switch by config only.
2. Multi-user runs do not leak prior request artifacts.
3. Rollback is immediate by config (`enabled=false` or `mode=off`).

## Test View
1. Shadow run -> metrics recorded, output unchanged.
2. Enforce run -> guarded adjustments applied and logged.
3. Consecutive different domains -> no style/cache bleed-through.

## Rollback
1. Set `quality_pipeline.mode=off` or `enabled=false`.
2. If needed, disable per-phase flags in descending order (P06 -> P01).

## Failure Handling
1. Try one correction for integration wiring error.
2. If unresolved, stop rollout and report:
   - failing touchpoint
   - fallback mode set (`shadow` or `off`)
   - impact scope

