# current_mainline_full_flow_ui_validation_2026-04-26 TASK

## Global Rules

- Product code / prompt / threshold / repair / guard / UI implementation must remain unchanged.
- Current success path must remain:
  - `current_mainline_runner.py -> newalgorithm_pipeline\pipeline.py -> simple_note_pipeline\pipeline.py`
- Single-pass + optional single repair 1回を維持する。
- Source不足、記事タイプ不一致、route mismatch は runtime defect と断定しない。
- Error を見て即修正しない。
- `1 issue = 1 narrow hypothesis = 1 owner scope` を維持する。
- Same error retry is capped at 3, but this package does not implement technical retry.

## Phase Map

| Phase | Scope | Owner | Exit |
|---|---|---|---|
| 0 | package + artifact root | docs / logs only | README / TASK / PROGRESS / ROLLBACK and artifact directories exist |
| 1 | historical error inventory | logs only | `historical_error_retest_plan.json` is written |
| 2 | source inventory / source gate | logs only | `source_inventory_used.json` and source precheck stop report are written |
| 3 | UI startup | execution only if source gate passes | skipped while source gate is failing |
| 4 | error retest + 9 article types x 3 | actual UI only if source gate passes | skipped while source gate is failing |
| 5 | image generation verification | post-success only | skipped while no UI generation is run |
| 6 | alignment evaluation | title/body/image only | skipped while no UI generation is run |
| 7 | server closeout | runtime process check | 18080 listener absent |
| 8 | summary / WORKLOG | docs + logs | `full_flow_summary.json`, `PROGRESS.md`, `WORKLOG.md` updated |

## Source Gate Required Fields

For each article type, record:

- `source_exists`
- `article_type_fit`
- `thickness`
- `quality_usable`
- `stop_reason`
- `required_source_items`

## Attempt Record Contract

If UI generation runs in a future continuation, each attempt must record:

- `article_type`
- `semantic_article_key`
- source precheck result
- title
- body chars
- UX classification
- `runtime_reason_code`
- output guard reasons
- repair required / applied / rejected
- source grounding / must-cover / source slot metrics
- UI visible message
- body displayed or hidden
- internal-term leakage
- source outside claim
- generated image path
- image generation status
- image prompt
- title-body-image alignment
- Codex visible evaluation

## Current Execution Result

- Phase 0 completed.
- Phase 1 completed.
- Phase 2 completed with `stop_for_sources`.
- Phases 3-7 are intentionally skipped.
- Phase 8 completed as docs / logs closeout.

## Stop Gate

Stop before UI generation if any target article type lacks clean source for full-flow quality judgment.

Current stop reason:

- 6 of 9 target categories are not ready for full-flow production-quality validation.
