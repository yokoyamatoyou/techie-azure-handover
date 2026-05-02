# PHASE 04: Style Drift Guard

## Objective
Prevent domain/tone mismatch and keep style aligned with topic, audience, and article purpose.

## Inputs
- user topic / URL / writing intent
- extracted domain signals (industry and audience hints)
- config keys:
  - `phase04_style_drift_enabled`
  - `style_alignment_min_score`
  - `domain_guard_strictness`

## Outputs
- `style_alignment_score`
- `drift_alerts` (domain, audience, tone)
- `style_corrections` (purpose-aware)

## Tasks (GPT-5 mini granularity)
1. Infer domain profile from URL/topic hints.
2. Infer article purpose (explain / branding / casual / thought leadership).
3. Detect mismatch terms (example: medical vocabulary in food-company context).
4. Generate minimal replacements aligned to inferred purpose.
5. Keep key brand message and factual statements unchanged.

## DoD
1. Non-medical domains do not leak medical audience assumptions.
2. Purpose-aware tone selection is reflected in corrections.
3. Corrections remain minimal and auditable.

## Test View
1. Food-company input with medical lexicon -> drift alerts and fixes.
2. Medical-company input -> medical terms are not falsely removed.
3. Branding vs explanation intent -> tone shifts appropriately.

## Rollback
Disable `phase04_style_drift_enabled`.

## Failure Handling
1. Try one correction for domain inference conflict.
2. If unresolved, stop phase and report conflict and fallback path.

