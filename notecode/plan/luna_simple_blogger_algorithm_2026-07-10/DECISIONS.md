# Decisions

## Accepted

- Keep `company_side_blogger_v1` unchanged across both candidate stages.
- Separate persona identity from stage task.
- Target a low-interest accidental visitor rather than a reader already comparing options.
- Start from source-present scenes, objects, actions, friction, work, or daily-life contact points.
- Treat speaker continuity and zero anaphora as explicit review dimensions.
- Treat user-specified model phrases and repeated meta verbs as signals that source-specific material may have been displaced.
- Keep the second stage bounded to failed paragraphs plus at most one adjacent sentence.
- Return a full article from Stage 2 so partial output cannot be mistaken for the deliverable.
- Keep a one-call Arm A so the value of the second call can be measured.

## Rejected

- Changing the second-stage identity to editor, reviewer, critic, or explainer.
- Adding more passes because the 2026-06-24 three-call sequence still scored `84`.
- Global phrase bans or synonym substitution as the core mechanism.
- Whole-article rewriting for rhythm-only or phrase-only concerns.
- Using first-person counts as a sufficient self-perspective test.
- Treating static source overlap as proof that every claim is supported.
- Connecting the prototype to Route V or using Route V fallback paths.

## Deferred

- Broader multi-source Luna quality and variance.
- Product adoption, UI, defaults, or migration.

## Final no-API decision

`conditionally_possible`

The simple algorithm is coherent, compact, renderable, testable, and reviewable without touching Route V. Historical evidence supports persona continuity, source-derived interest, and bounded repair as credible mechanisms, while also showing that editor-role pass count alone is insufficient. Adoption is not justified until a real same-source Luna A/B passes source and human gates.

## Live A/B decision 2026-07-10

- model / effort: `gpt-5.6-luna / low`
- source: one saved Sanrei packet
- completed sends: `3` (`A`, `B1`, `B2`)
- retry: `0`
- decision: `Arm A provisional winner; Arm B not adopted`

Both final articles passed H1/H2/body floor and avoided the specified template phrases. B improved maximum sentence length and opening source specificity, but B2 introduced one paragraph-boundary zero-anaphora candidate. B also cost `1.937x` and took `1.474x` A. The extra pass did not achieve a clean hard-gate improvement, so the simpler one-call arm remains preferred for this evidence.

This live result upgrades overall feasibility from no-API-only to `technically demonstrated on one source`, but does not authorize Route V adoption or another API run.

The decision above was a machine-only provisional decision before user review. It is retained as history, not treated as the final human preference.

## User review and past-A comparison 2026-07-10

- comparison A: the saved 2026-06-24 Sanrei Route V article
- comparison B: the current Luna same-blogger two-stage final article
- source lineage: the same four saved Sanrei excerpts, claim IDs `C002`, `C008`, `C014`, `C012`; normalized excerpt texts match exactly
- new API sends: `0`
- user preference: `B`
- decision: `B preferred for this one-source human comparison`

This human judgment supersedes the earlier machine-only provisional preference when discussing visible article quality. The common analyzer also favors B on opening source-overlap proxy (`0.489 -> 0.706`), maximum sentence length (`91 -> 67`), H2 count (`2 -> 3`), narrator repetition (`8 -> 5`), and meta-sentence ratio (`0.037 -> 0.000`). B retains one paragraph-boundary zero-anaphora review candidate.

Past A and current B share source lineage but not an identical prompt payload: past Route V also received an article brief and knowledge pack, whereas B received the compact ledger. Past A's official `1400` floor and current B's `1200` floor are therefore reported separately. This one-source preference does not authorize Route V adoption or accepted-state mutation.
