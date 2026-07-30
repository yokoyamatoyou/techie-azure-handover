# current_mainline_company_intro_source_grounding_weak_reflection_diagnosis_2026-04-27 TASK

## Phase Map

| Phase | Scope | Status |
|---|---|---|
| Phase 0 | Read rules and current status docs | completed |
| Phase 1 | Inspect rerun artifact and per-attempt summaries | completed |
| Phase 2 | Compare source grounding diagnostics across 3 attempts | completed |
| Phase 3 | Inspect visible bodies against source anchors | completed |
| Phase 4 | Classify true weak reflection vs observability mismatch | completed |
| Phase 5 | Record repair rejection relationship | completed |
| Phase 6 | Create docs-only package and next implementation prompt | completed |

## Gate

- Product code change: forbidden.
- Prompt / persona / source contract / algorithm change: forbidden.
- Threshold relaxation: forbidden.
- Repair count / repair acceptance change: forbidden.
- Quality guard / output guard / pipeline / blog image auto change: forbidden.
- Full validation rerun: forbidden.
- UI server start: forbidden.
- One issue must be reduced to one owner and one narrow hypothesis.

## Diagnostic Targets

For each `company_introduction` attempt:

- source grounding item count
- reflected count
- reflection ratio
- matched / partial / missing anchor groups
- metadata excluded count
- title-like / duplicate diagnostics
- source excerpts
- visible body reflection
- company-introduction source contract validation
- contract alignment
- review warnings
- repair required / rejected relationship

## Completion Criteria

- Attempt comparison table recorded.
- Body/source reflection notes recorded.
- Classification recorded.
- First blocker selected.
- Next implementation prompt prepared.
- WORKLOG updated.
- AGENTS update decision recorded.
