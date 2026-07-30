# route_a_only_archive_and_0506_ui_route_2026-05-08

Date: 2026-05-08 JST

## Objective

Route A current mainline remains the only kept current execution path while rejected non-Route-A experiments are prepared for archive/code move. After that cleanup, the validated `C:\Users\横山裕明\Desktop\0506` staged algorithm will be adapted as a separate UI body-generation route.

This package is planning only. It does not execute archive moves, send API requests, regenerate Route A, tune 0506 quality, or change product code.

## Source of Truth Read

- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\docs\route_b_0506_candidate_2026-05-08.md`
- `C:\tetie\notecode\ALGORITHM.md`
  - `## 4. Single-Pass Generation`
  - `## 5. Repair Algorithm`
  - `## 12. Persona / Source Packet / Editing Persona Contract`
- `C:\Users\横山裕明\Desktop\0506\AGENTS.md`
- `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
- `C:\Users\横山裕明\Desktop\0506\PROGRESS.md`
- `C:\tetie\notecode\logs\route_b_0506_single_saved_route_a_compare_20260508-224655\compare_summary.json`
- `C:\tetie\notecode\logs\route_b_0506_single_saved_route_a_compare_20260508-224655\blocked.json`

## Route A Keep Boundary

Keep this current success path unchanged:

```text
C:\tetie\notecode\note\current_mainline_runner.py
-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
```

Do not change:

- Route A prompt or prompt assets.
- Route A repair prompt or `repair_acceptance.py`.
- Route A quality thresholds, acceptance policy, or final guard policy.
- Current UI default generation behavior.
- Saved Route A artifacts, including `logs\latest_generation_output.*`.

Route A must not be regenerated in Window 1 through Window 5.

## 0506 Current Evidence

The 0506 candidate has already been wired as `route_b_0506_structured_blog_v1` through:

- `C:\tetie\notecode\note\route_b_0506_adapter.py`
- `C:\tetie\notecode\tools\run_route_b_0506_compare.py`

Latest saved-source live compare artifact:

- `C:\tetie\notecode\logs\route_b_0506_single_saved_route_a_compare_20260508-224655\compare_summary.json`

Result:

- status: `blocked`
- selected Route A artifact: `C:\tetie\notecode\logs\latest_generation_output.json`
- Route A regenerated: `false`
- source refetch: `false`
- Route B external LLM send: `true`
- model: `gpt-5.4-mini`
- reason: 0506 source-card schema validation blocked because `facts[0].importance` was `10` while schema maximum is `5`

This blocker belongs to the adapter/schema compatibility owner. It is not evidence to tune 0506 writing quality.

## Package Docs

- `ARCHIVE_INVENTORY.md`: archive/code-move candidates, keep list, current references to remove, move target, manifest and rollback policy.
- `NEW_ROUTE_CONTRACT.md`: new route ID, input contract, grounding, artifact, usage ledger, 0506 adapter responsibilities.
- `SECURITY_GATE.md`: threat model, blocking criteria, required evidence, hold rules.
- `IMPLEMENTATION_WINDOWS.md`: Window 1 through Window 6 split and next-window prompts.

## Non-Goals

- Do not archive or move code in this package window.
- Do not implement the new route in this package window.
- Do not send OpenAI API requests.
- Do not refetch URLs.
- Do not relax thresholds or repair acceptance.
- Do not add prompts to hide quality failures.
- Do not revive old `materialized_*`, deepresearch, Route D, Route E, or old Route B experiments.
- Do not make `AGENTS.md` larger unless a future read-order change is explicitly needed.

## Completion Status

- mode: docs-only implementation package
- product code changed: false
- archive executed: false
- API send: false
- Route A changed: false
- Route A regenerated: false
- 0506 product code changed: false
- AGENTS update: not needed
- WORKLOG update: recorded in `C:\tetie\WORKLOG.md`
