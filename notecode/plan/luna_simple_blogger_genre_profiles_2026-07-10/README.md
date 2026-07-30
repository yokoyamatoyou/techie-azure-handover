# Luna Simple Blogger B Genre Profiles 2026-07-10

## Scope and boundary

This is an isolated, no-API feasibility package for putting six UI article types
behind thin profiles on the existing Luna Simple Blogger B concept. It does not
replace the Route V planning source of truth and does not connect to the Route V
UI, runtime, default, model, prompt, persona, accepted state, or current owner.

The common B core is fixed: `company_side_blogger_v1` writes once, then the same
blogger rereads once under the existing four questions. The call count is always
two. Stage 2 can change only a failed paragraph and one adjacent sentence and
returns the whole article. No editor/critic/explainer identity, third stage,
repair loop, fallback, source refetch, raw full-source handoff, or body patch is
introduced here.

## Package map

- `GENRE_PROFILE_SPEC.md` — allowed six-field type differences and rejection rules
- `DECISIONS.md` — isolated decisions; it does not overwrite the earlier Luna package
- `EVAL_PLAN.md` — static replay/human review gates and limits
- `PROGRESS.md` — exactly one current next owner for this package
- `prototype/genre_profiles_no_api.py` — standard-library schema validator and compact renderer
- `prototype/profiles.json` — six thin profiles
- `prototype/replay_manifest.json` — saved Route V source/article references only
- `prototype/test_genre_profiles_no_api.py` — no-API contract/replay tests
- `artifacts/replay/` — rendered prompts, six review cards, profile comparison, and no-API report

## Result

The technical feasibility result remains `conditionally_possible`; the product
decision recorded on 2026-07-10 is `closed_not_adopted_route_v_remains`.

The profile schema keeps the identity, B core, two-call shape, hard source
boundary, and Stage 2 scope invariant across all six types. Profiles add 235–258
characters of type framing. This is small enough to remain a thin layer, but the
result does **not** prove generated quality, semantic grounding, or
unsupported-claim absence for six types. Only company/service introduction has a
saved Luna B article; no new article was generated in this package.

Route V remains the product route. This package is closed and must not be used
to propose a Route V connection, UI adoption, default change, or another Luna
validation without a new explicit user decision.
