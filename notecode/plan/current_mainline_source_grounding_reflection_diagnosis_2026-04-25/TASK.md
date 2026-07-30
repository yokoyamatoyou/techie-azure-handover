# current_mainline_source_grounding_reflection_diagnosis_2026-04-25 TASK

## Global Rules

- `1 issue = 1 narrow hypothesis = 1 owner scope`.
- Diagnose only; do not implement product behavior in this package.
- Keep current success path unchanged.
- Keep `single-pass + optional single repair 1回`.
- Do not reopen completed fingerprint policy.
- Do not change thresholds, prompts, target length, repair triggers, repair count, source packet thickness, or UI demotion policy.
- Do not expose runtime/internal terms in visible body or UI.
- Same diagnostic error can be retried up to 3 times; stop after that.

## Phase Map

| Phase | Scope | Owner files | Behavior change | Exit |
|---|---|---|---|---|
| 0 | package creation | README / TASK / PROGRESS / ROLLBACK | no | minimal package exists |
| 1 | policy / data-flow map | docs / saved artifacts | no | source-use to UI display path documented |
| 2 | saved artifact comparison | logs | no | Case 1 / Case 4 weak and success artifacts classified |
| 3 | owner decision | PROGRESS | no | next owner hypothesis stated or implementation rejected |
| 4 | stop / handoff | docs | no | package stops before code change |

## Required Artifact Checks

- Re-read saved artifacts under:
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_policy_resolution_20260425-165333\`
- Record for each target artifact:
  - source item count
  - reflected count
  - matched anchor terms
  - missing anchor pattern
  - body chars
  - output guard reasons
  - UI status when available
- Confirm Case 4 attempt 2 and attempt 3 use the same 9 source grounding items.
- Confirm saved UI artifacts are fresh enough for diagnosis:
  - `empty_result=false`
  - `stale_result_suspected=false`
  - visible/body internal-term leakage empty

## Classification Buckets

- `true weak reflection`
- `runtime source packet / final guard anchor mismatch`
- `stale / wrong contract evaluation`
- `UI handoff artifact mismatch`
- `acceptable body but observability false positive`

## Stop Criteria

- Stop immediately if the next step would require:
  - `source_grounding:weak_reflection` warning-only demotion
  - threshold relaxation
  - prompt accretion
  - repair trigger or repair count expansion
  - target length tuning
  - broad `output_guard.py` recompute
  - `note_writer_app.py` demotion branch
  - `pipeline.py` ad-hoc branching
- Stop after classification and do not start code changes in this package.

## Next Package Gate

- A follow-up implementation package is allowed only if:
  - exactly one owner file is named
  - the hypothesis does not weaken guard policy
  - the change is observability or source-use correction, not threshold relaxation
  - focused tests are defined before implementation
