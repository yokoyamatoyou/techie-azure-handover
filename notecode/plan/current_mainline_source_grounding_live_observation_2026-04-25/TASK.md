# TASK

## Rules

- Product code must not be changed.
- Metric correction must not be implemented in this package.
- Keep current success path unchanged:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Keep `single-pass + optional single repair 1回`.
- Do not change thresholds, prompts, target length, output guard policy, UI demote policy, or repair behavior.
- Keep raw telemetry internal to artifacts only.

## Phase Map

| Phase | Scope | Done When |
|---|---|---|
| 0 | package docs | README / TASK / PROGRESS / ROLLBACK exist |
| 1 | UI smoke | `http://127.0.0.1:18080/` is reachable or blocker is recorded |
| 2 | live attempts | Case 1 / Case 4 attempts saved under a timestamped log root |
| 3 | evidence classification | telemetry table and case-level classification recorded |
| 4 | hard decision / closeout | PROGRESS and WORKLOG updated |

## Run Budget

- Run Case 1 and Case 4 at least 3 times each.
- If a case has no `source_grounding:weak_reflection` after 3 attempts, run up to 2 additional attempts.
- Stop a case early if 2 `source_grounding:weak_reflection` attempts are captured.
- Maximum valid attempts per case: 5.

## Attempt Validity

An attempt can be counted as evidence only when:

- UI generation was triggered or a fresh snapshot was produced.
- A body exists.
- `pipeline_check.quality_metrics` is present.
- The new source-grounding group telemetry keys are present.
- Freshness can be confirmed by attempt id, snapshot modified time, or saved latest output copy.

## Classification

- `true weak reflection`: missing groups dominate and the body visibly omits main source facts.
- `anchor-shape false positive`: partial / duplicate / title-like groups dominate while the body remains source-aware and acceptable.
- `mixed`: both anchor-shape evidence and visible omission are present.
- `control`: no `source_grounding:weak_reflection`; fingerprint-only warning remains predecessor policy and is not reopened.

## Required Closeout

- Record artifact root.
- Record per-attempt table.
- Record Case 1 / Case 4 hard decisions.
- Update `C:\tetie\WORKLOG.md`.
- Do not update AGENTS unless current source-of-truth routing changes.

