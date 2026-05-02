# PHASE 03: Nominalization

## Objective
Reduce excessive abstract noun-heavy phrasing and recover natural verb-centered flow.

## Inputs
- article body text
- config keys:
  - `phase03_nominalization_enabled`
  - `nominalization_alert_threshold`
  - `max_nominalization_rewrite_ratio`

## Outputs
- `nominalization_score`
- `nominalization_alerts` (sentence-level)
- `rewrite_candidates` (minimal, meaning-preserving)

## Tasks (GPT-5 mini granularity)
1. Detect nominalization-heavy patterns with lightweight rules.
2. Flag passive or abstract chains that reduce clarity.
3. Generate minimal verb-centered rewrite candidates.
4. Keep rewrite ratio under `max_nominalization_rewrite_ratio`.
5. Preserve domain terms that must remain nouns.

## DoD
1. Alerts are explainable with source sentence references.
2. Rewrites improve clarity without semantic drift.
3. Domain terminology loss does not occur.

## Test View
1. Abstract explanatory text -> alerts and improved candidates.
2. Technical terms text -> low false positive rate.
3. Verify no change to legal/disclaimer sections.

## Rollback
Disable `phase03_nominalization_enabled`.

## Failure Handling
1. Try one correction for detection false positives.
2. If unresolved, stop phase and report examples and rule gap.

