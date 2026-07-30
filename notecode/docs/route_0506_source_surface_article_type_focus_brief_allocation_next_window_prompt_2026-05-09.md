# Route 0506 Source Surface Article-Type Focus And Brief Allocation Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 source-surface article-type focus / article-brief allocation 実行ウインドウです。

前回の after-KP-fix validation で、Desktop-like saved-source surface は記事生成まで到達し、QA `pass=true / score=100` になりました。`model_frequent_word` と `first_person_inconsistency` も再発していません。

ただし、出力は会社・サービス紹介というより、不動産売却方法ガイド寄りでした。今回の one owner は、prompt tuning や persona edit ではなく、source surface の article-type focus と、その後の article brief target length / section allocation を診断・最小修正することです。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. after-KP-fix quality validation result:
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\instruction_window_report.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\decision.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\manual_quality_review.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\stage_compare.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\desktop_like_run_summary.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\desktop_like_latest_generation_output.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\desktop_like_latest_generation_quality_report.json`
5. knowledge-pack boundary result:
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\decision.md`
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\normalized_capture_summary.json`
6. Desktop-like source surface / design evidence:
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\desktop_like_source_surface.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\desktop_like_source_surface_preflight.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_source_surface_adapter_design_20260509\adapter_contract.json`
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\surface_compare.json`
7. Current Route 0506 AB baseline:
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\compare_summary.json`
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\manual_review.md`
8. Desktop 0506 quality reference:
   - `C:\Users\横山裕明\Desktop\0506\AGENTS.md`
   - `C:\Users\横山裕明\Desktop\0506\PROGRESS.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_persona_timing_trials\persona_timing_trial_05_global_then_late_best_candidate\latest_generation_output.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_persona_timing_trials\persona_timing_trial_05_global_then_late_best_candidate\latest_generation_quality_report.json`
9. Runtime code:
   - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
   - `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
   - `C:\tetie\notecode\tools\run_route_0506_saved_source_cli_validation.py`
   - `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`
10. `C:\tetie\notecode\ALGORITHM.md`
    - `## 4. Single-Pass Generation`
    - `## 5. Repair Algorithm`
    - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current Evidence

- after-KP-fix Desktop-like validation:
  - article_generation_reached: true
  - QA pass: true
  - score: 100
  - quality issues: []
  - `model_frequent_word`: not recurred
  - `first_person_inconsistency`: not recurred
  - visible output shape: ok
  - source faithfulness: grounded to selected sources, but article-type focus drift
- manual issue:
  - title generic: `私たちがご案内する不動産売却の基本`
  - lead readable but guide-like
  - company/service focus weak-to-medium
  - final paragraph is general consultation advice, not brand/company close
- stage evidence:
  - selected_total_chars: 2292
  - original_saved_total_chars: 19633
  - source_card_count: 5
  - source_card_fact_count: 38
  - knowledge_pack_confirmed_fact_count: 24
  - article_brief_source_thickness: `thick`
  - article_brief_target_length_chars: `620`
  - article_brief_section_count: `4`
  - body_char_count: `1046`
  - heading_count: `7`
- first remaining bottleneck:
  - `source_surface_article_type_focus_then_article_brief_length_allocation`

## One Owner

`source_surface_article_type_focus_then_article_brief_length_allocation`

This owner may diagnose and minimally adjust:

1. which saved-source excerpts enter the Desktop-like surface for `company_introduction`
2. how article-type buckets are represented before source-card extraction
3. how the article brief target length / section allocation is derived from that surface

Do not edit article prompts, persona definitions, QA thresholds, or repair acceptance.

## Required Diagnosis Questions

Answer before any code edit:

1. Which selected source excerpts caused sell-method guide drift?
2. Which selected excerpts directly support company/service introduction?
3. Are `current_business`, `customer_situation_or_entry_point`, and `support_scope_boundary` underweighted relative to sell-method how-to content?
4. Is `source_limit` or broad guide content leaking into selected article material?
5. Why did `article_brief_target_length_chars` become `620` despite `source_thickness=thick`?
6. Why did `article_brief_section_count=4` lead to 7 visible headings?
7. Can a deterministic preflight reject or downweight generic sell-method guide spans while preserving URL identity and grounding?
8. Can target length / section allocation be corrected without prompt tuning?
9. What should be tested before any API rerun?

## Hard Boundaries

- Do not tune article prompts.
- Do not edit persona files.
- Do not relax QA thresholds.
- Do not relax `repair_acceptance`.
- Do not refetch URLs.
- Do not regenerate Route A.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not pass raw full `source_documents`.
- Do not make Route A adoption / replacement judgment.
- Do not widen into `model_frequent_word` or narrator owners; those did not recur in after-KP-fix validation.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Allowed Work

Default: diagnosis and deterministic preflight first.

Allowed:

- inspect saved source documents and selected spans
- compute bucket coverage / drift scores
- add or adjust a narrow deterministic selected-span filter for company-introduction source surface
- adjust article brief length/allocation only if the cause is the Route 0506 Desktop-like surface handoff or derived brief metadata
- add focused tests
- run one API validation after deterministic checks are green

API is allowed only after:

- deterministic preflight confirms company/service bucket coverage improved
- generic sell-method guide dominance is reduced
- URL refetch remains false
- raw full source pass remains false
- Route A remains untouched

Use:

- `OPENAI_API_KEY` from environment, without printing it
- `OPENAI_MODEL=gpt-5.4-mini`
- `OPENAI_REASONING_EFFORT=high`

Do not run more than 1 API article-generation attempt in this window.

## Suggested Artifact Root

```text
C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\
```

Required before code edit:

```text
diagnosis.md
selected_span_inventory.json
article_brief_gap_analysis.json
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

## Deterministic Preflight Expectations

Create a preflight that reports:

- selected source count
- selected total chars
- company/service bucket coverage
- sell-method guide span ratio
- source_limit material excluded
- URL identity preserved
- substring-backed selected text
- target length proposal
- section allocation proposal
- expected title/lead/final-paragraph anchors
- no URL refetch
- no Route A generation/fallback
- no raw full source documents

Suggested target:

- keep selected chars above current thin 1367, but reduce generic guide dominance
- preserve company/service identity from saved sources
- ensure required buckets are stronger than sell-method how-to material
- target length should not collapse to `620` for thick source unless explicitly justified

## Decision Rules

Use `fixed_continue_shadow` if:

- deterministic source focus / brief allocation fix lands
- tests pass
- optional API validation improves company/service focus without QA regression

Use `continue_shadow` if:

- diagnosis identifies the issue and Route 0506 remains useful, but no safe fix lands in this window

Use `needs_next_owner` if:

- the next first owner moves downstream after this diagnosis

Use `blocked` if:

- required saved source artifacts are missing
- the issue cannot be diagnosed without URL refetch or Route A generation
- API is required but unavailable

Use `reject` if:

- company/service focus cannot be recovered without prompt tuning, persona edits, threshold relaxation, raw-source drift, old route revival, or unsupported source reconstruction

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
selected_span_inventory_created: true | false
article_brief_gap_confirmed: true | false
sell_method_guide_drift_confirmed: true | false
company_service_bucket_coverage_before:
company_service_bucket_coverage_after:
selected_total_chars_before:
selected_total_chars_after:
article_brief_target_length_before:
article_brief_target_length_after:
article_brief_section_count_before:
article_brief_section_count_after:
api_validation_run: true | false
quality_pass_after:
quality_score_after:
quality_issues_after:
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
