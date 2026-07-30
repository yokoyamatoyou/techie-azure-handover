# Progress

## Completed owner

- owner: `luna_simple_blogger_no_api_feasibility`
- status: `completed`
- decision: `conditionally_possible`
- API send count: `0`
- product code changed: `false`
- source refetch: `false`
- generated article patch: `false`
- raw full source handoff: `false`
- Route V current owner changed: `false`

Completed scope:

- required past-evidence audit
- compact same-blogger one/two-stage specification
- isolated standard-library prototype
- saved-artifact replay and static metrics
- human-reviewable historical/control bundle
- tests and boundary validation

No-API run evidence:

- saved replay cases: `9` (`6` current human-review baselines + `3` Sanrei historical/control stages)
- Arm A / Arm B fixed calls: `1 / 2`
- Stage 1 / Stage 2 rendered prompt chars: `268 / 281`
- same role ID in both stages: `true`
- tests: `5 passed`
- current baseline observations surfaced by replay include narrator absence in `daily_activity`, high meta-sentence ratio in `announcement`, and a saved `case_study` body-floor concern; these are review signals, not acceptance-status changes

## Completed live owner

- owner: `luna_simple_blogger_live_ab_sanrei_one_run`
- state: `completed`
- model / effort: `gpt-5.6-luna / low`
- saved source: one Sanrei packet, 4 excerpts / 2,600 chars
- completed Responses API sends: `3` (`A`, `B1`, `B2`)
- retry count: `0`
- Route V connected: `false`
- raw full source handoff: `false`
- decision: `Arm A provisional winner; Arm B not adopted`

Live evidence:

- A: one call, `8.270 sec`, estimated `$0.00913475`
- B: two calls, `12.188 sec`, estimated `$0.01769735`
- B/A latency: `1.474x`; cost: `1.937x`
- A/B final both passed body floor, exact H1, and H2 structure
- B improved max sentence length `101 -> 67` and opening source-overlap proxy `0.557 -> 0.706`
- B2 introduced one paragraph-boundary zero-anaphora candidate
- both have low-severity source-role inference concerns; neither is a clean adoption proof

## Current next owner: exactly one

`luna_simple_blogger_b_preference_followup_wait`

State: `waiting_for_user_direction_no_more_api`

Allowed scope:

- inspect the saved past-A/current-B comparison and its remaining one zero-anaphora review candidate
- decide whether a separately approved, multi-source variance owner should ever be opened
- no API, implementation, Route V connection, or acceptance mutation in this owner

Non-owner boundaries:

- no Route V code/config/default model/prompt/persona/current owner/accepted-state change
- no Route V UI connection
- no Route A, writer-only, archive, or fallback revival
- no source refetch, raw full source handoff, generated-body patch, threshold relaxation, or repair-acceptance relaxation
- no additional send, retry, second source, repeat, extra repair pass, or fallback

## Completed past-A/current-B comparison owner

- owner: `luna_simple_blogger_past_a_vs_current_b_no_api`
- state: `completed`
- A: saved 2026-06-24 Sanrei Route V article
- B: current Luna same-blogger two-stage final article
- source: same four saved Sanrei excerpts; normalized texts and claim sequence match
- new API send count: `0`
- user preference: `B`
- decision: `B preferred for this one-source human comparison`
- common analyzer changes A -> B:
  - opening source-overlap proxy: `0.489 -> 0.706`
  - body source-overlap proxy: `0.513 -> 0.598`
  - maximum sentence chars: `91 -> 67`
  - narrator total: `8 -> 5`
  - meta-sentence ratio: `0.037 -> 0.000`
  - zero-anaphora candidates: `0 -> 1`
- fairness note: past Route V used a `1400` floor and also received article brief / knowledge pack; current B used a `1200` floor and compact ledger, so source lineage matches but generation contracts are not identical
- Route V code/config/default/UI/current owner/accepted state changed: `false`
