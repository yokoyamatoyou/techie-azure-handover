# Decisions

## Accepted for this isolated package

- Express all six UI types through one compact profile schema.
- Keep the same `company_side_blogger_v1` identity in both B stages and every type.
- Keep exactly two calls, H1/H2, source grounding, full-article return, and the
  bounded Stage 2 rewrite scope.
- Use saved source-packet and baseline-article paths as replay fixtures without
  copying raw full source content.
- Make profiles human-reviewable before any proposal for a generated six-type run.

## Rejected

- Type persona, type editor, type critic/explainer, a type-specific Stage 2,
  third stage, repair loop, fallback, phrase-ban expansion, or article patch.
- Connecting this candidate to Route V or its UI.
- Calling the static replay evidence of semantic grounding or generated quality.

## Decision

`conditionally_possible`

The profile layer is structurally thin: each profile is 235–258 rendered
characters and the B core/call shape remain identical. The condition is that it
still lacks output evidence for five types and must not advance to UI adoption,
default selection, or live validation without a separate approved owner.

## Final product decision 2026-07-10

`closed_not_adopted_route_v_remains`

The user selected Route V as the continuing Kotomake route and marked this Luna
candidate work complete. The one-source B evidence remains historical research,
not an adoption justification. No Route V code, UI, default, current owner, or
accepted state changed as a result of this decision.
