# Live A/B One-Run Result

- date: `2026-07-10 JST`
- model / effort: `gpt-5.6-luna / low`
- source: one saved Sanrei packet, 4 compact excerpts / 2,600 chars
- preflight: `pass`
- completed sends: `3` (`A`, `B1`, `B2`)
- retries: `0`
- status: `completed`
- Route V connected: `false`

## Runtime

| arm | calls | latency | estimated cost |
|---|---:|---:|---:|
| A | 1 | 8.270 sec | $0.00913475 |
| B | 2 | 12.188 sec | $0.01769735 |

B/A: latency `1.474x`; cost `1.937x`.

Pricing uses official Luna rates: input `$1/MTok`, cached input `$0.10/MTok`, cache writes `1.25x` uncached input, output `$6/MTok`. Output usage includes reasoning tokens.

## Mechanical comparison

| metric | A | B final |
|---|---:|---:|
| body chars / floor | 1230 / 1200 | 1228 / 1200 |
| H1 / H2 | 1 / 3 | 1 / 3 |
| max sentence chars | 101 | 67 |
| narrator terms | 7 | 5 |
| specified template phrases | 0 | 0 |
| zero-anaphora candidates | 0 | 1 |
| opening source-overlap proxy | 0.557 | 0.706 |
| whole-body source-overlap proxy | 0.613 | 0.598 |

The A-side `説明` hit was `個別説明会`, a source-specific event name, not a generic explanatory sentence.

## Decision

Arm A is the provisional winner for this single run. Arm B improved opening specificity and sentence length, but the second stage introduced one paragraph-boundary subject-omission risk and cost nearly twice as much. Both arms also retain small source-role conflation concerns requiring human review.

The same-blogger two-stage algorithm is technically feasible, but is not adopted from this evidence. No further API run is authorized in this owner.

## Boundary

- source refetch: `false`
- raw full source handoff: `false`
- generated article patch: `false`
- fallback / image generation: `false`
- Route V code/config/default/UI/current owner/accepted state changed: `false`
