# current_mainline_announcement_fail_block_diagnosis_2026-04-26 TASK

## Global Rules

- Diagnosis only.
- Product code remains unchanged.
- Do not change thresholds, prompts, repair count, or UI demote policy.
- Treat `source` as sufficient for this case.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.
- Distinguish validation-script classification from product UI classification.

## Phase Map

| Phase | Scope | Exit |
|---|---|---|
| 0 | package creation | README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT exist |
| 1 | evidence read | triage package, log-source artifacts, fail-closed UX policy, WORKLOG reviewed |
| 2 | attempt diagnosis | attempts 1 and 2 diagnosed by route, body, source facts, guard reasons, repair, and metrics |
| 3 | classification | reported block and underlying article-quality issue separated |
| 4 | owner selection | exactly one owner and one hypothesis selected |
| 5 | handoff prompt | next implementation prompt written |

## Artifact Checks

For `bl-announcement-spec-change` attempt 1 and attempt 2, record:

- UI route and `semantic_article_key`
- title / lead / body presence
- reflected source facts
- missing FAQ source facts
- output guard reasons / soft warnings
- `repair_required` / `repair_applied` / `repair_rejected`
- `source_grounding` and `must_cover`
- `_announcement_source_contract` state
- product app classification vs validation script outcome

## Classification Candidates

- `true_missing_must_cover`
- `source_reflection_metric_false_negative`
- `review_draft_classification_too_strict`
- `announcement_contract_gap`
- `repair_not_actuating`
- `UI_harness_or_snapshot_issue`

## Required Outputs

- `README.md`: objective, sources, non-goals, diagnosis conclusion.
- `TASK.md`: phase map, artifact checks, classification candidates, stop conditions.
- `PROGRESS.md`: attempt 1/2 diagnosis table, source fact coverage table, classification and owner decision.
- `ROLLBACK.md`: docs-only rollback boundary.
- `EXECUTION_PROMPT.md`: next implementation prompt for one owner only.
- `C:\tetie\WORKLOG.md`: docs-only diagnosis entry.

## Stop Conditions

- Stop if artifact files for either attempt are missing.
- Stop if product app classification cannot be distinguished from validation script classification.
- Stop if owner cannot be narrowed to one file without threshold, prompt, repair, or UI demote changes.

