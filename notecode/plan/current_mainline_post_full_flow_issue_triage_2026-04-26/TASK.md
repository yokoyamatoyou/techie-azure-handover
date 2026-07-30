# current_mainline_post_full_flow_issue_triage_2026-04-26 TASK

## Global Rules

- This package is docs-only.
- Product code / prompt / threshold / repair / guard / UI implementation must remain unchanged.
- Do not reclassify source shortage alone as a runtime defect.
- Do not mix UI harness failures with generation failures.
- Do not reopen completed or frozen reference packages.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Phase Map

| Phase | Scope | Exit |
|---|---|---|
| 0 | package creation | README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT exist |
| 1 | evidence read | referenced validation package, artifact summary, fail-closed UX policy, and WORKLOG context reviewed |
| 2 | attempt reclassification | all 18 attempts assigned to issue taxonomy |
| 3 | priority decision | remaining issues ranked by SaaS UX / frequency / source adequacy / owner scope |
| 4 | first-fix selection | exactly one first implementation target selected |
| 5 | handoff prompt | next implementation package prompt written |

## Classification Contract

Each attempt group must record:

- case id and attempt count
- observed outcome
- primary classification
- source caveat status
- route / semantic key status where relevant
- whether body exists or is body 0
- whether UI harness prevented a generation judgment
- whether image behavior is relevant

## Priority Rules

Rank higher when:

- source is adequate or source-caveat-free
- issue reproduces 2/2
- route is correct
- body exists and no internal leakage is observed
- SaaS user workflow is common before trial use
- owner scope is narrow and can be verified without changing thresholds, prompts, repairs, or broad UI policy

Rank lower when:

- source is thin, synthetic, or mismatched
- outcome is only a UI harness failure
- body is absent because of route mismatch or precondition failure
- fix would require broad routing, source-contract, prompt, threshold, repair, or UI demotion changes

## Required Outputs

- `README.md`: objective, sources, scope, non-goals, taxonomy, first-fix decision.
- `TASK.md`: rules, phases, classification contract, priority rules, required outputs.
- `PROGRESS.md`: current status, evidence, 18-attempt reclassification, priority table, selected target.
- `ROLLBACK.md`: docs-only rollback boundary.
- `EXECUTION_PROMPT.md`: next implementation package prompt for `bl-announcement-spec-change`.

## Stop Conditions

- If artifact evidence is missing, stop with the missing path and do not invent classification.
- If two issues tie after applying source adequacy and owner-scope rules, keep both as candidates and do not create an implementation prompt.
- If implementing the first fix would require threshold, prompt, repair, or broad UI demote expansion, stop and report that the target is not narrow enough.

