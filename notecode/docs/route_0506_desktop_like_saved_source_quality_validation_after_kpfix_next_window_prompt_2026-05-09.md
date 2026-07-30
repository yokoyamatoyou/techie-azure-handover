# Route 0506 Desktop-Like Saved-Source Quality Validation After KP Fix Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 Desktop-like saved-source article-quality validation 実行ウインドウです。

前回の品質診断 window は、`knowledge_pack single-fact conflict boundary` の結果 artifact が未作成だったため preflight で `blocked` になりました。  
その後、`knowledge_pack` 境界 owner は `fixed_continue_shadow` になり、saved raw capture の schema validation は green です。

今回の one owner は、同じ Desktop-like saved-source surface を使って記事生成まで到達させ、Route 0506 の残る品質差を診断することです。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. Prior blocked quality diagnosis:
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_diagnosis_20260509\instruction_window_report.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_diagnosis_20260509\preflight.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_diagnosis_20260509\decision.md`
5. Knowledge-pack boundary green evidence:
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\decision.md`
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\normalized_capture_summary.json`
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\schema_boundary_diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\code_diff_summary.md`
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\test_result.txt`
6. API deep audit / Desktop-like surface:
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\instruction_window_report.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\desktop_like_source_surface.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\desktop_like_source_surface_preflight.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\failed_full_pipeline_probe_summary.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\knowledge_pack_raw_capture.json`
7. Source-surface / adapter evidence:
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\surface_compare.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_source_surface_adapter_design_20260509\adapter_contract.json`
8. Current AB baseline:
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\compare_summary.json`
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\manual_review.md`
9. Desktop 0506 quality reference:
   - `C:\Users\横山裕明\Desktop\0506\AGENTS.md`
   - `C:\Users\横山裕明\Desktop\0506\PROGRESS.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_persona_timing_trials\persona_timing_trial_05_global_then_late_best_candidate\latest_generation_output.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_persona_timing_trials\persona_timing_trial_05_global_then_late_best_candidate\latest_generation_quality_report.json`
10. Runtime / tests:
    - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
    - `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
    - `C:\tetie\notecode\tools\run_route_0506_saved_source_cli_validation.py`
    - `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`
11. `C:\tetie\notecode\ALGORITHM.md`
    - `## 4. Single-Pass Generation`
    - `## 5. Repair Algorithm`
    - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current State

- Route A: frozen / immutable
- Route 0506: shadow-only
- post-guard AB test: `reject`
- Desktop-like source surface:
  - saved-source only
  - 5 URL records
  - 2292 selected chars from 19633 saved chars
  - URL locators preserved
  - no URL refetch
  - no raw full `source_documents` pass
- source-card extraction in previous API probe:
  - completed
  - 5 cards / 39 facts
- `knowledge_pack` boundary:
  - fixed for saved raw capture validation
  - single-fact caveats before: 2
  - single-fact conflicts after: 0
  - true 2+ fact conflict preserved
  - single-fact caveats preserved as `article_knowledge_pack.do_not_infer`
  - schema validation after: pass

## One Owner

Desktop-like saved-source article-quality validation after `knowledge_pack` fix.

Do not combine this with prompt tuning, persona edits, source-surface implementation redesign, threshold relaxation, or adoption decisions.

## API Policy

Allowed:

- Use `OPENAI_API_KEY` from environment. Do not print the key.
- Use `BLOGGEN_LLM_MODE=openai`.
- Use `OPENAI_MODEL=gpt-5.4-mini`.
- Use `OPENAI_REASONING_EFFORT=high`.
- Run exactly one Desktop-like saved-source Route 0506 article-quality validation.

Optional:

- Run one thin typed-source control only if it can be done with the same saved-source-only/no-refetch constraints and without Route A. If this would add complexity, skip it.

Forbidden:

- URL refetch
- Route A generation
- Route A fallback
- old route fallback
- raw full `source_documents` pass
- threshold relaxation
- `repair_acceptance` relaxation
- broad prompt tuning
- article prompt edits
- persona edits
- new repair loops
- Route A adoption / replacement judgment

## Required Preflight

Before any API call, create:

```text
C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\preflight.json
```

Preflight must confirm:

- `OPENAI_API_KEY` exists in environment, without printing it.
- `knowledge_pack` boundary green evidence exists.
- `normalized_capture_summary.json` shows:
  - `invalid_single_fact_conflicts_after=0`
  - `schema_validation_after=pass`
  - valid inter-fact conflict preserved
- Desktop-like source surface exists.
- Desktop-like source surface is saved-source-only.
- selected text is substring-backed.
- URL refetch is false.
- Route A regenerated is false.
- Route A fallback is false.
- raw full source documents passed is false.
- source count is 5.
- selected chars are 2292 or explicitly explained if recomputed.

If preflight fails, stop as `blocked` and do not call API.

## Required Artifact Root

```text
C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\
```

Required files:

```text
preflight.json
run_plan.md
desktop_like_run_summary.json
desktop_like_latest_generation_output.md
desktop_like_latest_generation_quality_report.json
stage_compare.json
manual_quality_review.md
decision.md
instruction_window_report.md
```

If the run blocks before article generation, create:

```text
blocked_stage_report.md
```

If a thin control run is executed, create:

```text
thin_control_run_summary.json
thin_control_latest_generation_output.md
thin_control_latest_generation_quality_report.json
```

## Diagnosis Questions

Answer these with artifact evidence:

1. Did article generation complete?
2. Did `knowledge_pack_integration` remain green in the full run?
3. Did QA pass?
4. Did `model_frequent_word` recur?
5. Did `first_person_inconsistency` recur?
6. Did visible-output wrapper / fenced article leakage recur?
7. Was source faithfulness preserved?
8. Did body length / heading continuity improve against post-guard Route 0506 AB runs?
9. Which stage is now the first remaining bottleneck?
   - source surface
   - knowledge-pack
   - article brief
   - prompt handoff
   - persona/style/editor mapping
   - editor timing
   - quality checker / targeted rewriter
   - observability gap
10. Is the next owner implementation, diagnosis, or rejection?

## Manual Japanese Review

Classify:

- `desktop_like_improved`
- `still_route_0506_red`
- `blocked_before_quality`
- `inconclusive`

Review:

- title specificity
- lead naturalness
- company/service focus
- narrator consistency
- source-grounded concrete detail
- repetition / model-like frequent words
- paragraph rhythm
- final paragraph fit

Compare against:

- Desktop 0506 Kyoto Kogyo final candidate
- notecode post-guard AB Route 0506 runs

Do not require identical wording or identical length.

## Decision Rules

Use `continue_shadow` if:

- Desktop-like source surface reaches article generation and improves Route 0506 quality, but adoption is still not decided.

Use `needs_next_owner` if:

- article generation reaches quality review and identifies a clear next first owner.

Use `blocked` if:

- preflight fails
- API unavailable
- full run blocks before article quality

Use `reject` if:

- Desktop-like source surface does not improve and the remaining path would require broad prompt tuning, threshold relaxation, `repair_acceptance` relaxation, raw-source drift, old route revival, or unsupported source reconstruction.

Do not output `adopt` or `replace_route_a`.

## Tests

Required:

- Validate all JSON artifacts with `ConvertFrom-Json`.
- If no product code changes, no pytest required.
- If product code changes unexpectedly become necessary, stop and report `blocked` or `needs_next_owner`; do not patch in this window.

## Final Report Contract

Report in this exact shape:

```text
decision: continue_shadow | needs_next_owner | blocked | reject
artifact_root:
product_code_changed: false
api_send_count:
api_key_source: environment
preflight_passed: true | false
knowledge_pack_boundary_green: true | false
article_generation_reached: true | false
desktop_like_surface_used:
thin_control_run_used: true | false
desktop_like_quality_pass: true | false | not_reached
desktop_like_quality_score:
desktop_like_quality_issues:
model_frequent_word_recurred: true | false | not_reached
first_person_inconsistency_recurred: true | false | not_reached
visible_output_shape_ok: true | false | not_reached
source_faithfulness:
manual_japanese_naturalness_note:
quality_classification: desktop_like_improved | still_route_0506_red | blocked_before_quality | inconclusive
first_next_owner:
parked_later_owners:
route_a_regenerated: false
url_refetched: false
route_a_fallback_used: false
old_routes_reopened: false
raw_full_source_documents_passed: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
tests:
WORKLOG_update_needed: true | false
```

If `WORKLOG_update_needed=true`, update only the Route 0506 current state / next owner pointer in `C:\tetie\WORKLOG.md`.
