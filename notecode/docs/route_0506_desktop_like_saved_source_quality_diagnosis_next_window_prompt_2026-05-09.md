# Route 0506 Desktop-Like Saved-Source Quality Diagnosis Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 続きの品質診断ウインドウです。

目的は、Desktop-like saved-source surface で `knowledge_pack_integration` blocker を越えた後、記事生成まで到達させ、Route 0506 の残る品質差がどの工程に残っているかを診断することです。

APIキーは環境変数 `OPENAI_API_KEY` から取得してよいです。  
ただし API 実行はこの prompt の範囲に限定し、URL refetch、Route A 再生成、Route A fallback、old route fallback、threshold relaxation、`repair_acceptance` relaxation、broad prompt tuning は禁止です。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. Current Route 0506 reports:
   - `C:\tetie\notecode\docs\route_0506_work_window_result_report_to_instruction_window_2026-05-09.md`
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\compare_summary.json`
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\manual_review.md`
5. Source-surface / adapter design evidence:
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\surface_compare.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_source_surface_adapter_design_20260509\adapter_contract.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_source_surface_adapter_design_20260509\validation_plan.md`
6. API deep audit blocker evidence:
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\instruction_window_report.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\api_deep_audit.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\decision.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\desktop_like_source_surface.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\desktop_like_source_surface_preflight.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\knowledge_pack_raw_capture.json`
7. Knowledge-pack boundary owner result, if present:
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\decision.md`
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\normalized_capture_summary.json`
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\test_result.txt`
8. Desktop 0506 quality reference:
   - `C:\Users\横山裕明\Desktop\0506\AGENTS.md`
   - `C:\Users\横山裕明\Desktop\0506\PROGRESS.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_persona_timing_trials\persona_timing_trial_05_global_then_late_best_candidate\latest_generation_output.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_persona_timing_trials\persona_timing_trial_05_global_then_late_best_candidate\latest_generation_quality_report.json`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\quality_review_package_pdf_1371322\final_article.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\quality_review_package_pdf_1371322\latest_generation_quality_report.json`
9. Runtime / adapter code:
   - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
   - `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
   - `C:\tetie\notecode\tools\run_route_0506_saved_source_cli_validation.py`
   - relevant Route 0506 tests under `C:\tetie\notecode\note\tests\`
10. `C:\tetie\notecode\ALGORITHM.md`
    - `## 4. Single-Pass Generation`
    - `## 5. Repair Algorithm`
    - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current Known State

- Desktop 0506 quality is stable enough to be the quality reference:
  - Kyoto Kogyo final candidate: QA pass / score 100 / no issues
  - PDF explainer final: QA pass / score 100 / no issues
- notecode Route 0506 post-guard AB:
  - decision: `reject`
  - 3 Route 0506 candidates all QA-red
  - `model_frequent_word` recurred
  - `first_person_inconsistency` appeared
- source-surface parity:
  - current thin typed surface: 3 manual typed records / 1367 chars
  - Desktop-like probe surface: 5 URL records / 2292 selected chars from 19633 saved chars
  - source-card extraction completed with 5 cards / 39 facts
- latest blocker:
  - `knowledge_pack_integration`
  - single-fact caveats emitted under `conflicts`
  - Desktop schema requires `conflicts[].involved_fact_ids` to have 2+ fact ids

## One Owner

Desktop-like saved-source Route 0506 article-quality diagnosis.

This owner starts only after the `knowledge_pack single-fact conflict boundary` is green or locally verified as non-blocking. If that blocker is still present, stop as `blocked` and do not run article generation.

## API Policy

Allowed:

- Use `OPENAI_API_KEY` from environment.
- Use `BLOGGEN_LLM_MODE=openai`.
- Use `OPENAI_MODEL=gpt-5.4-mini`.
- Use `OPENAI_REASONING_EFFORT=high`.
- Run Route 0506 saved-source-only validation using the Desktop-like saved-source surface.

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
- Route A replacement / adoption judgment

## Required Preflight Before API

Create and save preflight evidence before any API call.

Preflight must confirm:

- `OPENAI_API_KEY` exists in environment, without printing the key.
- `knowledge_pack` single-fact conflict boundary is fixed or non-blocking.
- `desktop_like_source_surface.json` exists.
- `desktop_like_source_surface_preflight.json` exists.
- source surface is saved-source only.
- selected source text is substring-backed by saved `input_contract.source_documents`.
- URL refetch is false.
- Route A regenerated is false.
- Route A fallback is false.
- raw full source documents are not passed.
- source count is 3-5.
- selected chars are greater than 1367.
- current thin hash and Desktop-like hash are recorded separately.

If any preflight item fails, stop as `blocked`.

## What To Run

Run only one narrow quality diagnosis set:

1. One Desktop-like saved-source Route 0506 API run.
2. Optionally, one current thin typed-source Route 0506 control run only if the same script can do it without Route A and without URL refetch.

Do not run more than 2 API article-generation attempts in this window.

If a run blocks before article generation, stop and record the blocked stage. Do not perform repair loops.

## Required Artifact Root

```text
C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_diagnosis_20260509\
```

Required artifacts:

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

If a thin control run is executed, also create:

```text
thin_control_run_summary.json
thin_control_latest_generation_output.md
thin_control_latest_generation_quality_report.json
```

If article generation is not reached, create:

```text
blocked_stage_report.md
```

## Quality Diagnosis Questions

Answer these using artifacts:

1. Does Desktop-like source surface reach article generation?
2. Does QA pass?
3. Does `model_frequent_word` recur?
4. Does `first_person_inconsistency` recur?
5. Is body length / heading continuity closer to Desktop 0506 than prior Route 0506?
6. Is source faithfulness preserved?
7. Does visible-output wrapper / fenced article leakage recur?
8. Are opening / global consistency / style / structural stages firing in the expected order?
9. If QA-red remains, which first owner is responsible:
   - source surface
   - knowledge-pack
   - article brief
   - prompt handoff
   - persona/style/editor profile mapping
   - editor timing
   - quality checker / targeted rewriter
   - observability gap
10. Is the next owner still `desktop_like_saved_source_surface_v1`, or has the bottleneck moved downstream?

## Manual Japanese Review

Do a short manual Japanese naturalness review. Compare against Desktop 0506 quality references, but do not require identical wording or length.

Classify:

- `desktop_like_improved`
- `still_route_0506_red`
- `blocked_before_quality`
- `inconclusive`

Review dimensions:

- title specificity
- lead naturalness
- company/service focus
- narrator consistency
- source-grounded concrete detail
- repetition / model-like frequent words
- paragraph rhythm
- final paragraph fit

## Decision Rules

Use `continue_shadow` if:

- Desktop-like source surface reaches article generation and improves quality, but is not adoption-ready.

Use `needs_next_owner` if:

- a new first owner is clearly identified after generation.

Use `blocked` if:

- preflight fails
- knowledge-pack blocker remains
- API is unavailable
- article generation blocks before quality diagnosis

Use `reject` if:

- Desktop-like source surface does not improve and the remaining path would require broad prompt tuning, threshold relaxation, `repair_acceptance` relaxation, raw-source drift, old route revival, or unsupported source reconstruction.

Do not output `adopt`, `replace_route_a`, or Route A adoption judgment.

## Tests

Required:

- Validate all JSON artifacts with `ConvertFrom-Json`.
- Run only focused local tests for changed product code, if any.

If no product code changes, no pytest is required.

If product code changes were necessary, report exactly why and run focused tests only. Do not broaden test scope unless the changed files require it.

## Final Report Contract

Report in this exact shape:

```text
decision: continue_shadow | needs_next_owner | blocked | reject
artifact_root:
product_code_changed: true | false
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
