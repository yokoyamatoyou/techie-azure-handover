# PHASE 06: Orchestrator

## Objective
Define execution order and conflict resolution across Phase 01-05 outputs with predictable behavior.

## Inputs
- phase outputs from P01-P05
- config keys:
  - `phase06_orchestrator_enabled`
  - `global_rewrite_ratio_cap`
  - `conflict_resolution_policy`
  - `quality_gate_min_score`

## Outputs
- `quality_bundle` (scores, alerts, actions)
- `final_adjustment_plan`
- `gate_decision` (pass / hold / fallback)

## Tasks (GPT-5 mini granularity)
1. Define phase execution order and data contract mapping.
2. Merge alerts and deduplicate overlapping corrections.
3. Resolve conflicts (readability vs diversity vs style).
4. Enforce `global_rewrite_ratio_cap`.
5. Emit gate decision and fallback reason when needed.

## DoD
1. Same input and config produce same gate decision.
2. Conflicting suggestions are resolved with explicit policy.
3. Rewrite cap is never exceeded.

## Test View
1. Multi-alert sample -> merged and conflict-resolved output.
2. Low-quality sample -> `hold` or fallback behaves as designed.
3. High-quality sample -> minimal/no edit path.

## Rollback
Disable `phase06_orchestrator_enabled`.

## Failure Handling
1. Try one correction for merge/conflict logic.
2. If unresolved, stop phase and report unresolved conflict set.

