# Route 0506 Knowledge-Pack Single-Fact Conflict Boundary Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 OpenAI compatibility 実行ウインドウです。

今回の one owner は、Desktop-like saved URL source surface の API probe で露出した `knowledge_pack_integration` の schema / semantic boundary だけです。

品質低下の入口原因は `source_surface_mismatch` として維持します。ただし、記事生成へ進む前に `knowledge_pack` が single-fact caveat を `conflicts` に入れて schema validation block したため、次はこの blocker を先に解消します。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. API deep audit report:
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\instruction_window_report.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\api_deep_audit.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\decision.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\knowledge_pack_raw_capture.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\knowledge_pack_raw_capture_summary.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\failed_full_pipeline_probe_summary.json`
5. Prior parity/design evidence:
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\surface_compare.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_source_surface_adapter_design_20260509\adapter_contract.json`
6. Desktop 0506 reference:
   - `C:\Users\横山裕明\Desktop\0506\AGENTS.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md`
   - `C:\Users\横山裕明\Desktop\0506\app\schemas\knowledge_pack.schema.json`
   - `C:\Users\横山裕明\Desktop\0506\app\agents\knowledge_pack_integrator.py`
   - `C:\Users\横山裕明\Desktop\0506\app\services\pipeline_runner.py`
7. notecode Route 0506 integration:
   - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
   - `C:\tetie\notecode\tools\run_route_0506_saved_source_cli_validation.py`
   - Route 0506 tests under `C:\tetie\notecode\note\tests\`

## Current Evidence

- API probe used:
  - saved-source only
  - 5 URL records
  - selected 2292 chars from 19633 saved chars
  - no URL refetch
  - no Route A generation
  - no Route A fallback
  - no raw full `source_documents` pass
- source-card extraction completed:
  - 5 source cards
  - 39 facts
- blocked stage:
  - `knowledge_pack_integration`
- blocker:
  - Desktop `knowledge_pack.schema.json` requires `conflicts[].involved_fact_ids` to have at least 2 fact ids.
  - OpenAI emitted single-fact caveats under `conflicts`, e.g. `["F313"]`, `["F144"]`.
  - A true conflict shape also appeared, e.g. `["F111", "F1208"]`.
- article generation was not reached.
- Therefore `model_frequent_word` / `first_person_inconsistency` after source-surface repair remain untested.

## One Owner

`knowledge_pack single-fact conflict boundary for Route 0506 OpenAI compatibility`

Handle only this semantic/schema boundary:

- `conflicts` should represent inter-fact conflict, requiring 2+ fact ids.
- single-fact caveats should become warning / risk / do-not-infer handling, or be filtered by a narrow OpenAI compatibility normalizer before Desktop schema validation.

## Required Diagnosis Questions

Answer these before patching:

1. Does Desktop schema intentionally define `conflicts` as inter-fact only?
2. Where is schema validation called in the Desktop runner path used by Route 0506?
3. Is it safer to patch Desktop 0506 core, notecode Route 0506 adapter, or an owner-local compatibility normalizer?
4. Can single-fact caveats be preserved without weakening source-grounding?
5. Can true 2+ fact conflicts remain unchanged?
6. Can the fix be tested with saved `knowledge_pack_raw_capture.json` without another API call?
7. Does the fix avoid prompt tuning and threshold relaxation?

## Hard Boundaries

- Do not tune article prompts.
- Do not change article-generation prompts.
- Do not relax QA thresholds.
- Do not relax `repair_acceptance`.
- Do not refetch URLs.
- Do not regenerate Route A.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not pass raw full `source_documents`.
- Do not continue into article generation in this owner unless explicitly approved in a later prompt.
- Do not decide Route A adoption / replacement.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Allowed Work

Allowed:

- diagnose schema and validation boundary
- add a narrow compatibility normalizer or equivalent minimal patch
- preserve single-fact caveat text in a non-conflict bucket if an existing schema field allows it
- if no schema-safe bucket exists, filter single-fact caveats from `conflicts` and record them in artifact evidence / warning telemetry without weakening generated article grounding
- add focused tests using saved raw capture
- run local tests only

Default expectation:

- no OpenAI API call
- no article generation
- no URL refetch
- no Route A generation

## Suggested Artifact Root

```text
C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\
```

Required artifacts:

```text
hypothesis.md
schema_boundary_diagnosis.md
code_diff_summary.md
test_result.txt
normalized_capture_summary.json
decision.md
```

`normalized_capture_summary.json` should include:

- input_raw_capture_path
- invalid_single_fact_conflicts_before
- valid_inter_fact_conflicts_before
- invalid_single_fact_conflicts_after
- valid_inter_fact_conflicts_after
- single_fact_caveats_preserved_as
- schema_validation_after
- api_send: false

## Tests

Run only local deterministic tests.

Recommended checks:

```powershell
C:\Users\横山裕明\Desktop\0506\.venv\Scripts\python.exe -m py_compile C:\Users\横山裕明\Desktop\0506\app\agents\knowledge_pack_integrator.py C:\Users\横山裕明\Desktop\0506\app\services\pipeline_runner.py
```

If the patch is in notecode, use the notecode venv and focused Route 0506 tests:

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile C:\tetie\notecode\note\route_0506_structured_blog_adapter.py C:\tetie\notecode\tools\run_route_0506_saved_source_cli_validation.py
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest -q C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py C:\tetie\notecode\note\tests\test_route_0506_saved_source_cli_validation.py
```

If a new focused test file is added, run that file too.

Validate JSON artifacts:

```powershell
Get-Content -LiteralPath "<artifact>\normalized_capture_summary.json" -Raw | ConvertFrom-Json | Out-Null
```

Do not run OpenAI API in this owner.

## Decision Rules

Use `fixed_continue_shadow` if:

- single-fact caveats no longer block schema validation
- true 2+ fact conflicts remain as conflicts
- tests pass
- no API/article generation was run
- guardrails remain false

Use `needs_next_owner` if:

- the correct fix owner is elsewhere or requires a separate implementation window

Use `blocked` if:

- schema-safe preservation is impossible without changing broader Desktop schema semantics
- required artifacts are missing

Use `reject` only if:

- fixing this boundary requires broad prompt tuning, schema weakening, threshold relaxation, old route revival, or unsupported source reconstruction

Do not output `adopt` or `replace_route_a`.

## Final Report Contract

Report in this exact shape:

```text
decision: fixed_continue_shadow | needs_next_owner | blocked | reject
artifact_root:
changed_files:
product_code_changed: true | false
api_send: false
article_generation_reached: false
blocked_stage_before:
blocked_stage_after:
single_fact_conflicts_before:
single_fact_conflicts_after:
valid_inter_fact_conflicts_preserved:
single_fact_caveats_preserved_as:
schema_validation_after:
route_a_regenerated: false
url_refetched: false
route_a_fallback_used: false
old_routes_reopened: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
tests:
manual_japanese_naturalness_note:
next_one_owner:
WORKLOG_update_needed: true | false
```

If `WORKLOG_update_needed=true`, update only the Route 0506 current state / next owner pointer in `C:\tetie\WORKLOG.md`.
