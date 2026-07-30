# current_mainline_explanatory_article_regression_diagnosis_2026-04-26 TASK

## Phase Map

| Phase | Scope | Status |
|---|---|---|
| Phase 0 | Read required docs and target artifacts | completed |
| Phase 1 | Compare historical OK artifacts with latest blocked attempts | completed |
| Phase 2 | Verify route, source reconstruction, and source facts in body | completed |
| Phase 3 | Separate runtime metric issue from UI/harness classification | completed |
| Phase 4 | Create docs-only package and update WORKLOG | completed |

## Gate

- Product code remains unchanged.
- Thresholds remain unchanged.
- Prompts remain unchanged.
- Repair behavior remains unchanged.
- UI demotion behavior remains unchanged.
- `output_guard.py` remains unchanged.
- `note_writer_app.py` remains unchanged.
- `simple_note_pipeline/pipeline.py` remains unchanged.
- Findings are backed by artifact paths and not inferred from source shortage alone.

## Diagnosis Checks

| Check | Required conclusion |
|---|---|
| UI route / semantic key | latest attempts are `explanatory_article`; no route mismatch |
| source reconstruction | latest source packet is not equivalent to historical OK because uploaded-file metadata entered `source_grounding_items` |
| source docs | required facts are present in source and reflected in body |
| output guard | direct block trigger is `SYS_QUALITY_WARNINGS_UNRESOLVED` with `source_grounding:weak_reflection` |
| body | source facts are present; not a true missing-source-facts case |
| UI visible | latest UI text says `確認が必要なドラフトです` |
| harness summary | reports `input_required_block` because the runtime output is blocked/redacted |

## Retry Stop

This package is docs-only and completed without runtime changes. If future implementation is opened, it must be a separate owner-limited package with a retry stop defined there.

## Future Implementation Guard

If a future fix is approved, start with:

- Owner: `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- Narrow hypothesis: ignore path/hash-like metadata items in source grounding denominator while preserving current thresholds and unsupported-claim safety.

Do not use this diagnosis package to modify:

- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
- prompts
- repair policy
- thresholds
