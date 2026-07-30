# Past Route V A vs Current Luna B

## Outcome

User preference: **B**. For this saved Sanrei source comparison, current Luna B is the human-preferred article.

This supersedes the earlier machine-only provisional preference for the one-call live arm. It does not alter Route V or prove multi-source adoption readiness.

## Source comparability

- Same saved Sanrei source lineage: 4 excerpts, claim IDs `C002, C008, C014, C012`.
- Normalized excerpt texts match exactly: `True`.
- Important caveat: the prompt payloads are not identical. Past Route V also received its article brief and knowledge pack; current B received the compact ledger.
- New API sends for this comparison: `0`.

## Common analyzer

| article | body chars | H1/H2 | max sentence | narrator | meta ratio | zero candidates | opening proxy | body proxy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A: past Route V | 1153 | 1/2 | 91 | 8 | 0.037 | 0 | 0.489 | 0.512 |
| B: current Luna two-stage | 1228 | 1/3 | 67 | 5 | 0.000 | 1 | 0.706 | 0.598 |

The common analyzer supports the user's preference on opening source specificity, maximum sentence length, H2 structure, narrator repetition, and meta-language. B's remaining regression is one paragraph-boundary zero-anaphora candidate; a human should read that sentence with the preceding paragraph rather than treating the heuristic as an automatic rejection.

## Historical record kept separate

Past A's original Route V record was `1219/1400`, quality score `76`, with `sentence_too_long`, `model_frequent_word`, and `body_length_below_floor`; it also had one disallowed reader-inference frame ending in 「確認できます」.

Current B reaches its own 1200-character contract under the common analyzer, but does not reach 1400. Therefore floor status is not used as evidence that B is universally better; the contracts differ.

## Decision

`B preferred for this one-source human comparison`.

The result is evidence for the same-blogger second stage, not authorization to connect it to Route V. A multi-source variance check and direct grounding review would still be required before any adoption proposal.
