# Route 0506 Instruction Window Migration After Fullness 2026-05-10

このプロンプトを新しい Codex 指示ウインドウに貼り付けて開始してください。  
このウインドウは実作業ウインドウではありません。状態確認、境界管理、次ウインドウ prompt 作成、完了報告の受け取りを担当してください。

日本語で出力してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 / Desktop 0506 品質差分改善を管理する新しい指示ウインドウです。

目的は、`C:\Users\横山裕明\Desktop\0506` で安定している品質へ Route 0506 を近づけるため、作業ウインドウの結果を受け取り、境界を守りながら次の one-owner prompt を作ることです。

実装・API実行・ファイル修正はこの指示ウインドウでは行いません。必要な場合は、別の作業ウインドウ用 prompt を作成してください。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. Latest Route 0506 result:
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\stage_length_trace.json`
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\claim_allocation_trace.json`
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\decision_before_edit.md`
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\fix_attempt_01\api_validation_summary.json`
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\fix_attempt_01\manual_quality_review.md`
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\fix_attempt_01\test_result.txt`
5. Prior source-focus result:
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\article_brief_gap_analysis.json`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\selected_span_inventory.json`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\fix_attempt_01\api_validation_summary.json`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\fix_attempt_01\manual_quality_review.md`
6. Prior blocker/fix chain:
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\decision.md`
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\normalized_capture_summary.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\decision.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\stage_compare.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\instruction_window_report.md`
7. Initial source-surface / method evidence:
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\surface_compare.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\README.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\method_check_summary.json`
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\compare_summary.json`
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\manual_review.md`
8. Desktop 0506 quality reference:
   - `C:\Users\横山裕明\Desktop\0506\AGENTS.md`
   - `C:\Users\横山裕明\Desktop\0506\PROGRESS.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_persona_timing_trials\persona_timing_trial_05_global_then_late_best_candidate\latest_generation_output.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_persona_timing_trials\persona_timing_trial_05_global_then_late_best_candidate\latest_generation_quality_report.json`
9. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current Route 0506 State

- Route A current mainline: frozen / immutable
- Route 0506: shadow-only
- Route A replacement / adoption judgment: not made
- Desktop 0506 quality reference remains stronger and stable
- Route 0506 has improved materially but is not adoption-ready

Latest decision:

```text
decision: continue_shadow
artifact_root: C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\
```

Latest result:

- product_code_changed: true
- api_send_count: 1
- api_key_source: environment
- underfill_stage_before: draft_writer
- target/body before: 3000 / 1138
- target/body after: 2200 / 1347
- QA after: pass=true / score=100 / issues=[]
- model_frequent_word recurrence: false
- first_person_inconsistency recurrence: false
- company/service focus regression: false
- Route A regenerated: false
- URL refetched: false
- Route A fallback used: false
- raw full source documents passed: false
- threshold relaxed: false
- repair_acceptance relaxed: false

Interpretation:

- Fullness improved from 1138 to 1347 chars.
- However, output remains compact.
- New OpenAI article brief target dropped from 3000 to 2200.
- Fullness is not fixed.
- Route 0506 remains shadow-only.

## Completed / Closed Owners

Do not reopen these unless a new artifact proves the exact owner is broken again:

- source handoff mismatch
- `sentence_too_long`
- manual shadow review
- repeatability / fullness review
- visible-output shape guard
- fullness / article-brief diagnosis
- post-guard AB test
- non-0506 route archive cleanup
- Desktop 0506 method check
- source-surface parity diagnosis
- Desktop-like source surface adapter design
- full-pipeline audit
- `knowledge_pack` single-fact conflict boundary
- Desktop-like saved-source article-quality validation after KP fix
- source-surface article-type focus / article brief allocation

## Current Improvement Chain

1. Initial post-guard Route 0506 AB was `reject`.
   - all 3 runs QA-red
   - `model_frequent_word` x2
   - `first_person_inconsistency` x1
2. Desktop method check showed:
   - same core engine: yes
   - same end-to-end source surface: no
3. Source-surface parity diagnosis confirmed:
   - Desktop native source surface is richer
   - notecode Route 0506 had thin/manual source surface
4. Desktop-like saved-source surface probe:
   - source-card extraction reached 5 cards / 39 facts
   - blocked at `knowledge_pack` because single-fact caveats entered `conflicts`
5. `knowledge_pack` single-fact conflict boundary fixed:
   - single-fact caveats moved/preserved under `do_not_infer`
   - true 2+ fact conflict preserved
   - schema validation green
6. After-KP-fix quality validation:
   - article generation reached
   - QA green
   - old QA-red symptoms disappeared
   - but article drifted toward selling-method guide
7. Source-surface article-type focus / brief allocation fixed:
   - company/service bucket coverage 0.5419 -> 1.0
   - sell-method guide ratio 0.4324 -> 0.0599
   - target length 620 -> 3000
   - QA green
   - company/service focus improved
   - remaining issue: compact output
8. Generation-side fullness followthrough:
   - body 1138 -> 1347
   - QA green
   - focus did not regress
   - still compact
   - target fell 3000 -> 2200 in latest API run

## Current First Open Problem

The current open problem is:

```text
Route 0506 still under-follows fullness / length despite improved source focus and QA green output.
```

Evidence:

- prior target/body: 3000 / 1138
- latest target/body: 2200 / 1347
- draft was the original underfill stage
- latest fix improved draft/body size but did not reach stable Desktop-like fullness
- output is readable and focused, but still compact

The next work should continue comparing Desktop 0506 vs Route 0506, but must choose exactly one owner.

Likely next owner candidates:

1. `article_brief_target_stability_and_claim_allocation_parity`
   - why did OpenAI article brief target drop from 3000 to 2200?
   - does Route 0506 pass target length / source thickness / section intent differently from Desktop?
2. `draft_writer_fullness_compliance`
   - why does draft writer underfill even when brief target is high?
   - are section claim counts and per-section expansion instructions reaching the draft writer?
3. `editor_stage_length_preservation`
   - lower priority now, because earlier evidence showed draft is already compact and editors only mildly shrink

Instruction window should not choose a broad multi-owner task. If the user asks for next prompt, prefer owner 1 unless newer artifacts prove otherwise:

```text
article_brief_target_stability_and_claim_allocation_parity
```

## Hard Boundaries

- Do not regenerate Route A.
- Do not refetch URLs.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not pass raw full `source_documents`.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Do not add broad prompt tuning.
- Do not edit personas unless a later artifact proves persona mapping is the single owner.
- Do not add new repair loops.
- Do not make Route A replacement / adoption judgment.
- Do not treat QA green alone as adoption-ready.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Instruction Window Closeout Rules

When a work-window report arrives:

1. First check `decision`.
2. Check guardrail booleans:
   - `route_a_regenerated`
   - `url_refetched`
   - `route_a_fallback_used`
   - `old_routes_reopened`
   - `raw_full_source_documents_passed`
   - `threshold_relaxed`
   - `repair_acceptance_relaxed`
   - `prompt_bloat`
   - `module_bloat`
3. If the report widened into Route A adoption, broad prompt tuning, threshold relaxation, old routes, raw full source pass, or persona sprawl, classify it as scope drift.
4. If it stays in the current owner chain, decide only:
   - `fixed_continue_shadow`
   - `continue_shadow`
   - `needs_next_owner`
   - `blocked`
   - `reject`
5. Do not output `adopt` or `replace_route_a` from this instruction window.

## Suggested Next Work-Window Prompt

If the user asks for a next work-window prompt, create a prompt for this one owner:

```text
Route 0506 article_brief target stability and claim allocation parity
```

Required goal:

- Compare Desktop 0506 and Route 0506 article-brief construction / target length / source thickness / section claim allocation.
- Explain why Route 0506 target length can fall from 3000 to 2200 after the fullness followthrough fix.
- Determine whether target length and section allocation are unstable before draft writer.
- Do not run API by default.
- Do not touch source selection unless evidence proves brief construction consumes the selected source surface incorrectly.

Expected artifacts:

```text
C:\tetie\notecode\logs\route_0506_article_brief_target_stability_20260510\
diagnosis.md
desktop_vs_route0506_brief_compare.json
target_length_trace.json
claim_allocation_compare.json
decision_before_edit.md
```

Allowed:

- read-only inspection
- deterministic trace scripts/artifacts
- narrow adapter-side fix only if target length / claim allocation loss is concretely proven
- focused tests

API:

- default no API
- if a later prompt allows API, use environment `OPENAI_API_KEY`, `gpt-5.4-mini`, reasoning `high`
- no more than 1 validation run

Final report contract for that work window should include:

```text
decision: fixed_continue_shadow | continue_shadow | needs_next_owner | blocked | reject
artifact_root:
product_code_changed:
api_send_count:
diagnosis_completed:
target_length_drop_confirmed:
desktop_brief_reference:
route0506_brief_before:
route0506_brief_after:
claim_allocation_gap:
first_underfill_owner:
changed_files:
tests:
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
WORKLOG_update_needed:
```
