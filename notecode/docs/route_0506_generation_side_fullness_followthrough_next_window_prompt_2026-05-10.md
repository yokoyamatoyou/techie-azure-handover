# Route 0506 Generation-Side Fullness Followthrough Next Window Prompt 2026-05-10

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 generation-side fullness followthrough 実行ウインドウです。

前回の source-surface article-type focus / brief allocation window で、会社・サービス焦点は改善し、QA `pass=true / score=100`、`model_frequent_word` と `first_person_inconsistency` は再発しませんでした。  
ただし、`article_brief.target_length_chars=3000` / `section_count=5` に対して、最終本文は `1138` chars で止まりました。

今回の one owner は、source surface や prompt tuning ではなく、article brief の length / section / claim allocation が draft writer / editor stages で本文量へ追従しているかを診断・最小修正することです。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. latest source-focus result:
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\article_brief_gap_analysis.json`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\selected_span_inventory.json`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\fix_attempt_01\preflight_after_fix.json`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\fix_attempt_01\api_validation_summary.json`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\fix_attempt_01\latest_generation_output.md`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\fix_attempt_01\latest_generation_quality_report.json`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\fix_attempt_01\manual_quality_review.md`
5. previous after-KP-fix validation:
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\stage_compare.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\manual_quality_review.md`
6. knowledge-pack boundary result:
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\decision.md`
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\normalized_capture_summary.json`
7. Desktop 0506 quality reference:
   - `C:\Users\横山裕明\Desktop\0506\AGENTS.md`
   - `C:\Users\横山裕明\Desktop\0506\PROGRESS.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_persona_timing_trials\persona_timing_trial_05_global_then_late_best_candidate\latest_generation_output.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_persona_timing_trials\persona_timing_trial_05_global_then_late_best_candidate\latest_generation_quality_report.json`
8. Runtime code:
   - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
   - `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
   - `C:\tetie\notecode\tools\run_route_0506_saved_source_cli_validation.py`
   - `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`
9. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current State

- Route A: frozen / immutable
- Route 0506: shadow-only
- latest decision: `fixed_continue_shadow`
- source focus result:
  - company_service_bucket_coverage: `0.5419 -> 1.0`
  - sell_method_guide_span_ratio: `0.4324 -> 0.0599`
  - selected_total_chars: `2292 -> 2072`
  - article_brief_target_length: `620 -> 3000`
  - article_brief_section_count: `4 -> 5`
  - API validation: 1 run
  - QA: pass / score 100 / issues []
  - body chars: `1138`
  - manual note: company/service focus improved, but output remains compact despite target length 3000

## One Owner

`generation_side_fullness_followthrough_after_source_focus`

Diagnose and fix only the gap between:

- article brief target length / section allocation / claim allocation
- draft writer output length
- editor stage length preservation or shortening
- final visible output body length

Do not reopen source surface focus, `knowledge_pack`, prompt/persona tuning, QA thresholds, or Route A decisions.

## Required Diagnosis Questions

Answer before any code edit:

1. Did `article_brief.json` in the latest raw run actually contain `target_length_chars=3000` and `section_count=5`?
2. How many claim IDs were allocated per section?
3. How many confirmed facts / source-card facts were available?
4. What were the char counts at each stage:
   - draft
   - opening editor output
   - global consistency output
   - style editor output
   - structural editor output
   - final latest_generation_output
5. Did the draft writer underfill first, or did a later editor shorten an adequate draft?
6. Did stage guards or output normalization truncate content?
7. Is the issue a target-length signal not reaching the Desktop runner, a draft-writer compliance issue, or an editor-stage compression issue?
8. Can the fix be deterministic / adapter-local without prompt bloat?
9. What should be verified before any API rerun?

## Hard Boundaries

- Do not refetch URLs.
- Do not regenerate Route A.
- Do not use Route A fallback.
- Do not revive old routes.
- Do not pass raw full `source_documents`.
- Do not relax QA thresholds.
- Do not relax `repair_acceptance`.
- Do not add broad prompt tuning.
- Do not edit persona files.
- Do not add new repair loops.
- Do not make Route A adoption / replacement judgment.
- Do not reopen `model_frequent_word` or narrator owners unless the new run reintroduces them.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Allowed Work

Default: diagnosis first.

Allowed:

- inspect latest raw run stage artifacts
- compute stage-by-stage char counts and section/claim utilization
- add or adjust a narrow adapter/runtime signal if the length target is being lost before Desktop runner stages
- add focused tests
- run one API validation after deterministic checks are green

API is allowed only after:

- stage diagnosis identifies a concrete fullness followthrough issue
- deterministic/focused tests pass
- no URL refetch / Route A / fallback / raw full source pass

Use:

- `OPENAI_API_KEY` from environment, without printing it
- `OPENAI_MODEL=gpt-5.4-mini`
- `OPENAI_REASONING_EFFORT=high`

Do not run more than 1 API article-generation attempt in this window.

## Suggested Artifact Root

```text
C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\
```

Required before code edit:

```text
diagnosis.md
stage_length_trace.json
claim_allocation_trace.json
decision_before_edit.md
```

If code changes:

```text
fix_attempt_01\hypothesis.md
fix_attempt_01\code_diff_summary.md
fix_attempt_01\test_result.txt
fix_attempt_01\preflight_after_fix.json
```

If API validation is run:

```text
fix_attempt_01\api_validation_summary.json
fix_attempt_01\latest_generation_output.md
fix_attempt_01\latest_generation_quality_report.json
fix_attempt_01\manual_quality_review.md
```

## Decision Rules

Use `fixed_continue_shadow` if:

- fullness followthrough issue is fixed or materially improved
- QA remains green
- company/service focus does not regress
- no guardrails are violated

Use `continue_shadow` if:

- diagnosis identifies the issue but no safe fix lands

Use `needs_next_owner` if:

- a new first owner emerges after stage diagnosis or validation

Use `blocked` if:

- required raw run stage artifacts are missing
- API is required but unavailable
- diagnosis cannot proceed without forbidden actions

Use `reject` if:

- increasing fullness requires broad prompt tuning, threshold relaxation, raw-source drift, old-route revival, or unsupported source reconstruction

Do not output `adopt` or `replace_route_a`.

## Tests

If product code changes:

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile C:\tetie\notecode\note\route_0506_structured_blog_adapter.py C:\tetie\notecode\tools\run_route_0506_saved_source_cli_validation.py
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest -q C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py C:\tetie\notecode\note\tests\test_route_0506_saved_source_cli_validation.py
```

If new focused tests are added, run them too.

Always validate JSON artifacts with `ConvertFrom-Json`.

## Final Report Contract

Report in this exact shape:

```text
decision: fixed_continue_shadow | continue_shadow | needs_next_owner | blocked | reject
artifact_root:
changed_files:
product_code_changed: true | false
api_send_count:
api_key_source: environment | not_used
diagnosis_completed: true | false
stage_length_trace_created: true | false
claim_allocation_trace_created: true | false
underfill_stage: draft_writer | opening_editor | global_consistency_editor | style_editor | structural_editor | output_guard | unknown
target_length_before:
body_chars_before:
target_length_after:
body_chars_after:
qa_pass_after:
quality_score_after:
quality_issues_after:
company_service_focus_regressed: true | false | not_run
model_frequent_word_recurred: true | false | not_run
first_person_inconsistency_recurred: true | false | not_run
manual_japanese_naturalness_note:
next_one_owner:
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
