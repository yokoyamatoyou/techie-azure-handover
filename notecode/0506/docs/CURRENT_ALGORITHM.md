# Current Algorithm

Last updated: 2026-06-28

## Current Route V Override: 2026-06-28 Post-Manual UI Article Type Image Validation

Latest validation artifact:

```text
notecode/logs/0628/rv_ui_img_20260628_180205/validation_summary.json
```

Decision: `needs_review`. UI reachability passed; all six article types generated; all six article types produced text/no-text image variants.

Service invocation counts in this owner: article generation invocations `12`; image generation invocations `12`; successful image variants `24`; Route V/0506 OpenAI terminal send count `52`.

Route V is the only normal UI body-generation route. Route B is a retired name; legacy `route_b_*` artifact paths remain historical evidence only.

Article readiness by genre: `comparison_guide=pass`, `company_service_intro=needs_review`, `market_explanation=needs_review`, `announcement=pass`, `daily_activity=pass`, `case_study=pass`.

Image readiness by genre: all six genres `success` with `with_text_success=true`.

First confirmed gap: `company_service_intro:article`; final quality issues include `model_frequent_word` and `duplication`. Secondary gap: `market_explanation:article`; final quality issues include `model_frequent_word` and `ending_bucket_monotony`.

Product code changed `false`; source refetch `false`; generated article patch `false`; raw full source handoff `false`; Route A fallback `false`; writer-only fallback `false`; QA threshold relaxed `false`; repair acceptance relaxed `false`; prompt bloat `none`; module bloat `none`.

Current next owner is `route_v_first_gap_review`.

Allowed next scope: diagnose the saved artifacts for the first confirmed `company_service_intro` article quality failure and identify one narrow owner before any further API execution or implementation.

Non-owner boundaries before/within the next owner: no source refetch, generated article patch, raw full source handoff, Route A / writer-only fallback, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or broad module/prompt expansion.

## Historical Route V Override: 2026-06-28 Post-Guarded User Evaluation Artifact

Latest user evaluation artifact:

```text
notecode/logs/0628/route_v_guarded_user_evaluation_artifact_no_api_20260628_134325/review_index.md
```

Source inventory artifact:

```text
notecode/logs/0628/route_v_article_set_readiness_inventory_no_api_20260628_134223/article_set_readiness_inventory.md
```

Decision: `user_evaluation_artifact_ready`. API send count `0`; copied article count `6`; all copy hashes match in `copy_manifest.json`; product code changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.

The bundled article set is ready for manual user evaluation. It preserves daily_activity caveats and case_study user-review caveat.

Historical next owner was `route_v_user_evaluation_waiting_for_manual_review`.

Historical non-owner boundaries before/within that owner: no API execution, source refetch, generated article patch, accepted-status mutation, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or product-code edits before user feedback.

## Historical Route V Override: 2026-06-28 Post-Case-Study Acceptance And Gate Enablement

Latest acceptance artifact:

```text
notecode/logs/0628/route_v_case_study_local_surface_sanitization_acceptance_decision_no_api_20260628_133650/acceptance_decision.md
```

Decision: `accepted_for_user_evaluation`. Acceptance owner API send count `0`; upstream validation API send count `1`; product code changed in acceptance owner false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false. Historical next owner was `route_v_article_set_readiness_inventory_no_api`.

## Historical Route V Override: 2026-06-28 Post-Case-Study Local Surface Sanitization Implementation

Latest implementation artifact:

```text
notecode/logs/0628/route_v_case_study_local_surface_sanitization_no_api_impl_20260628_132141/implementation_summary.md
```

Decision: `implementation_completed_needs_one_article_api_validation_after_approval`. API send count `0`; product code changed true; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false. Historical next owner was `route_v_case_study_local_surface_sanitization_one_article_api_validation_after_approval`.

## Historical Route V Override: 2026-06-28 Post-Case-Study Human-Visible Surface Diagnosis

Latest diagnosis artifact:

```text
notecode/logs/0628/route_v_case_study_human_visible_surface_repair_diagnosis_no_api_20260628_131533/diagnosis.md
```

Decision: `diagnosis_completed_needs_next_owner`. API send count `0`; product code changed false; accepted status changed false; source refetch false; generated article patch false. First confirmed gap was `case_study_local_surface_sanitization_gap`.

## Historical Route V Override: 2026-06-28 Post-Daily-Activity User Tolerance Record

Latest user tolerance artifact:

```text
notecode/logs/0628/route_v_daily_activity_user_tolerance_record_no_api_20260628_130737/user_tolerance_record.md
```

Decision: `user_visible_acceptable_with_caveats`. API send count `0` for this owner; source validation API send count `1`; product code changed false; accepted status changed false; source refetch false; generated article patch false. Preserved caveats: `duplicate_long_sentence`, `model_frequent_word`, `duplication`, no `私たち`, and slight third-party feel in the later half.

## Historical Route V Override: 2026-06-28 Post-Daily-Activity Local Surface Sanitization API Validation

Latest validation artifact:

```text
notecode/logs/0628/route_v_daily_activity_local_surface_sanitization_one_article_api_validation_after_approval_20260628_123856/api_validation_summary.md
```

Decision: `reject_or_inconclusive`. API send count `1`; retry count `0`; product code changed false; accepted status changed false; source refetch false; generated article patch false. Final article generated with H1 exactly one, H2 sections present, and body floor reached `1234/1200`. Human-visible surface gate failed on `duplicate_long_sentence`; quality failed with `model_frequent_word` and `duplication`; self-perspective consistency failed because the final article contains no `私たち`.

## Historical Route V Override: 2026-06-28 Post-Market-Explanation Acceptance Decision

Latest acceptance artifact:

```text
notecode/logs/0628/route_v_market_explanation_acceptance_decision_no_api_20260628_094825/acceptance_decision.md
```

Source validation artifact:

```text
notecode/logs/0628/route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_one_article_api_validation_after_approval_20260628_014124/api_validation_summary.md
```

Decision: `accepted`. The acceptance owner used no API execution and made no product code, source refetch, generated article patch, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation, broad prompt/persona, or QA threshold / repair-acceptance changes.

The latest same-source `market_explanation` validation had decision `acceptance_candidate` with API send count `1`. Stage trace body floor was draft/opening/global/style `1397/1200`, structural API raw `932/1200`, structural API guarded `1397/1200`, and final `1393/1200`. Quality issues were `[]`; max sentence length was `81`; over-limit count was `0`; human-visible surface gate findings were `[]`. Source boundary, selected excerpt usage, structural floor-loss guard, prompt bloat, and algorithm bloat passed.

`market_explanation` can be treated as accepted / user-visible release-ready for this same-source validation chain. All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`.

Historical next owner was `route_v_announcement_human_visible_surface_repair_diagnosis_no_api`.

Non-owner boundaries before the next owner: no API execution, source refetch, generated article text patch, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or product-code change as the first move.

## Historical Route V Override: 2026-06-28 Post-Market-Explanation Targeted Rewrite Sentence Split Suru-Event API Validation

Latest validation artifact:

```text
notecode/logs/0628/route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_one_article_api_validation_after_approval_20260628_014124/api_validation_summary.md
```

Decision: `acceptance_candidate`. API send count `1` for this validation owner; product code changed false; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.

The same saved `market_explanation` source packet was reused. The validation did not change DraftWriter, sanitizer, source selection, structural editor, prompts, personas, QA thresholds, or accepted status.

Stage trace body floor: draft/opening/global/style `1397/1200`; structural API raw `932/1200`; structural API guarded `1397/1200`; final `1393/1200`. The structural editor again over-compressed below floor, and the existing floor-loss guard correctly restored the floor-reaching input before deterministic targeted rewrite split the remaining long sentence without breaking the floor.

Quality passed with issues `[]`. Sentence split followthrough max sentence length was `81` with over-limit count `0`; human-visible surface gate findings were `[]`. Source boundary and selected excerpt usage passed. Prompt bloat and algorithm bloat checks passed, and no broad prompt/persona tuning was used.

All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`.

Historical next owner was `route_v_market_explanation_acceptance_decision_no_api`.

Non-owner boundaries before the next owner: no API execution, source refetch, generated article text patch, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or accepted-status mutation without an explicit acceptance decision record.

## Historical Route V Override: 2026-06-28 Post-Market-Explanation Targeted Rewrite Sentence Split Suru-Event No-API Implementation

Latest implementation artifact:

```text
notecode/logs/0628/route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_followthrough_no_api_impl_20260628_013345/implementation_summary.md
```

Decision: `implementation_no_api_gate_pass`. API send count `0`; product code changed true only in `notecode/0506/app/services/editor_output_safety.py` and `notecode/0506/tests/test_editor_output_guard.py`; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.

The deterministic targeted rewrite sentence split followthrough closes long split segments ending in `することにより` as `します。` before the existing recursive splitter continues. This did not change DraftWriter, sanitizer, source selection, structural editor, prompts, personas, QA thresholds, or accepted status.

Saved-artifact replay against the residual floor buffer validation changed the article, kept body floor `1393/1200`, removed `sentence_too_long`, passed quality, reduced max sentence length to `80`, and kept human-visible surface gate findings `[]`.

Focused tests passed (`20 passed` plus `14 passed` additional pipeline/quality focused tests); `py_compile` passed; changed product-file bloat passed (`editor_output_safety.py` 249/300); prompt bloat remained none.

All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`.

Historical next owner was `route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_one_article_api_validation_after_approval`.

## Historical Route V Override: 2026-06-28 Post-Market-Explanation Quality Pass Failure Diagnosis

Latest diagnosis artifact:

```text
notecode/logs/0628/route_v_market_explanation_quality_pass_failure_diagnosis_no_api_20260628_012133/diagnosis.md
```

Decision: `needs_next_owner`. API send count `0`; product code changed false; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.

The source validation artifact is `notecode/logs/0628/route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_one_article_api_validation_after_approval_20260628_005719/api_validation_summary.md`. It reached final body floor `1397/1200`, passed human-visible surface gate, source boundary, selected excerpt usage (`2/2`), structural compression guard, and over-editing. Structural raw compressed to `1132/1200`, and the floor-loss guard restored guarded/final output to `1397/1200`.

The only quality issue was `sentence_too_long`. No-API replay confirmed current deterministic targeted rewrite leaves the single `137` char suru-event sentence unchanged.

First confirmed gap: `market_explanation_targeted_rewrite_sentence_split_suru_event_followthrough_gap`.

All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`.

Historical next owner was `route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_followthrough_no_api_impl`.

Non-owner boundaries before the next implementation: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or generated-article patch.

## Historical Route V Override: 2026-06-28 Post-Market-Explanation Residual Floor Buffer API Validation

Latest validation artifact:

```text
notecode/logs/0628/route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_one_article_api_validation_after_approval_20260628_005719/api_validation_summary.md
```

Decision: `reject_or_inconclusive`. API send count `1`; product code changed false; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.

The validation reused the same saved `market_explanation` source packet. Final article generation completed with exactly one H1 and H2 sections. Final body floor reached `1397/1200`; structural API raw compressed to `1132/1200`, and the floor-loss guard restored the floor-reaching input to `1397/1200`.

Human-visible surface gate passed with finding codes `[]`. Source boundary passed with compact knowledge visible, assigned claim coverage `8/8`, and no unsupported ranking / best / numeric claims. Selected excerpt usage passed (`2/2`), structural compression guard passed, and over-editing was absent.

The validation did not reach acceptance-candidate state because quality failed only on `sentence_too_long`: one sentence exceeded the configured limit (`max=137`, limit `90`).

All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`.

Historical next owner was `route_v_market_explanation_quality_pass_failure_diagnosis_no_api`.

Non-owner boundaries before the next diagnosis: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or immediate generated-article patch.

## Historical Route V Override: 2026-06-28 Post-Market-Explanation DraftWriter Residual Floor Buffer No-API Implementation

Latest implementation artifact:

```text
notecode/logs/0628/route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_no_api_impl_20260628_001740/implementation_summary.md
```

Decision: `implementation_no_api_gate_pass`. API send count `0`; product code changed true; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.

The implementation adds a narrow `market_explanation` DraftWriter residual floor buffer under sanitized writer context. `DraftWriter` now passes sanitized `knowledge_pack` into market-explanation followthrough, and the owner-specific followthrough is split into `app/services/market_explanation_followthrough.py` to avoid module bloat.

Saved-artifact replay improved DraftWriter-stage body chars from `1096/1200` to `1519/1200`, reaching the `1500` pre-editor buffer target. Focused tests passed (`24 passed`), `py_compile` passed, touched product-file bloat passed, and prompt bloat remained none.

All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`.

Historical next owner was `route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_one_article_api_validation_after_approval`.

Non-owner boundaries before the next validation: no source refetch, generated article text patch, accepted-status change before a separate acceptance owner, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, or QA threshold / repair-acceptance relaxation.

## Historical Route V Override: 2026-06-27 Post-Market-Explanation Body-Floor Diagnosis

Latest diagnosis artifact:

```text
notecode/logs/0627/route_v_market_explanation_body_floor_reached_failure_diagnosis_no_api_20260627_230000/diagnosis.md
```

Decision: `needs_next_owner`. API send count `0`; product code changed false; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.

Source validation artifact:

```text
notecode/logs/0627/route_v_market_explanation_writer_context_surface_sanitization_one_article_api_validation_after_approval_20260627_221924/api_validation_summary.md
```

First below-floor stage is DraftWriter (`1096/1200` body chars excluding headings). Structural API raw later compressed an already-subfloor input to `891/1200`; quality report also remained below floor (`951/1200`). Selected excerpts were visible and used (`2/2`), DraftWriter received structured claims (`15`) and the floor/depth contract, and final surface/source/fallback guards passed.

First confirmed gap: `market_explanation_draft_writer_sanitized_context_residual_floor_miss_gap`.

All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`.

Historical next owner was `route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_no_api_impl`.

Non-owner boundaries before the next implementation: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, structural-editor floor-loss guard change as first owner, selector/source-shape/claim-allocation change, broad prompt/persona tuning, or QA threshold / repair-acceptance relaxation.

## Historical Route V Override: 2026-06-27 Post-Market-Explanation Writer-Context Surface Sanitization API Validation

Latest validation artifact:

```text
notecode/logs/0627/route_v_market_explanation_writer_context_surface_sanitization_one_article_api_validation_after_approval_20260627_221924/api_validation_summary.md
```

Decision: `reject_or_inconclusive`. API send count `1`; product code changed false; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.

The same saved `market_explanation` source packet was reused after writer-context surface sanitization. Final article generation completed with exactly one H1 and H2 sections. Selected-source usage, source boundary, raw-source handoff absence, Route A fallback absence, and writer-only fallback absence passed. The final human-visible surface gate passed with finding codes `[]`.

The validation did not reach acceptance-candidate state because body floor failed (`951/1200` in quality report; final stage trace `891/1200` body chars excluding headings). Quality failed on `body_length_below_floor`, `sentence_too_long`, `low_density_bridge_sentence`, and `abstract_navigation_phrase`.

First confirmed gap: `body_floor_reached`.

All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`.

Historical next owner was `route_v_market_explanation_body_floor_reached_failure_diagnosis_no_api`.

Historical non-owner boundaries before that diagnosis: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, broad prompt/persona/QA/selector/source-shape/claim-allocation change, or QA threshold / repair-acceptance relaxation.

## Historical Route V Override: 2026-06-27 Post-Market-Explanation Writer-Context Surface Sanitization Implementation

Latest implementation artifact:

```text
notecode/logs/0627/route_v_market_explanation_writer_context_surface_sanitization_no_api_impl_20260627_214859/implementation_summary.md
```

Decision: `implementation_no_api_gate_pass`. Product code changed true only in the narrow `market_explanation` writer-context surface sanitization boundary, DraftWriter wiring, followthrough sanitization, and focused tests. API send count `0`; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.

`DraftWriter` now sanitizes `market_explanation` writer-facing `knowledge_pack` and `selected_source_excerpts` before payload construction. Market-explanation selected-excerpt followthrough also sanitizes excerpt text before turning it into appended reader-facing paragraphs. The boundary removes OCR/PDF surface forms such as spaced Japanese source text, spaced ASCII source surface, standalone source-title/metadata/outline lines, and unmatched Japanese quote fragments while keeping the saved source packet as the evidence base.

Saved-artifact replay against `notecode/logs/0626/mxrq_api_20260626_161500` produced sanitized context with no surface-gate spaced text or spaced ASCII surface and a no-API replay output that passed the human-visible surface gate.

First confirmed gap preserved: `market_explanation_writer_context_surface_sanitization_gap`.

All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`.

Historical next owner was `route_v_market_explanation_writer_context_surface_sanitization_one_article_api_validation_after_approval`.

Non-owner boundaries before the next validation: no source refetch, generated article text patch, accepted-status change before a separate acceptance owner, raw full source handoff, Route A / writer-only fallback, broad prompt/persona/QA/selector/source-shape/claim-allocation change, or QA threshold / repair-acceptance relaxation.

## Historical Route V Override: 2026-06-27 Post-Market-Explanation Human-Visible Surface Diagnosis

Latest diagnosis artifact:

```text
notecode/logs/0627/route_v_market_explanation_human_visible_surface_repair_diagnosis_no_api_20260627_211533/diagnosis.md
```

Decision: `diagnosis_completed_needs_next_owner`. Product code changed false; accepted status changed false; source refetch false; generated article patch false; API send count `0`; raw full source handoff false; Route A / writer-only fallback false.

The saved `market_explanation` accepted validation article is blocked by the final human-visible surface gate on `ocr_spaced_source_text`, `dangling_japanese_quote_fragment`, and `duplicate_long_sentence`. The same findings originate in the DraftWriter-stage saved artifact. `structural_editor_api_raw.md` removes the surface findings, but it falls below floor (`1083/1200`), so the floor-loss guard correctly restores the floor-reaching draft (`1233/1200`).

First confirmed gap: `market_explanation_writer_context_surface_sanitization_gap`.

All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`.

Historical next owner was `route_v_market_explanation_writer_context_surface_sanitization_no_api_impl`.

Non-owner boundaries before the next implementation: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, broad prompt/persona/QA/selector/source-shape/claim-allocation change, or QA threshold / repair-acceptance relaxation.

## Historical Route V Override: 2026-06-27 Post-Human-Visible Surface Gate Implementation

Latest implementation artifact:

```text
notecode/logs/0627/route_v_human_visible_surface_gate_no_api_impl_20260627_200358/implementation_summary.md
```

Decision: `implementation_no_api_gate_pass`. Product code changed true only in final human-visible surface gate / quality wiring / pipeline artifact output / focused tests. API send count `0`; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.

The final Markdown surface gate now blocks local-renderer fingerprints, dangling Japanese quote fragments, OCR-spaced source text, duplicate long source-title/sentence carryover, and unrelated local CTA carryover before Route V artifacts can be treated as user-visible release-ready. It reports compatible existing quality issue types and writes `human_visible_surface_gate.json` from the pipeline.

Saved-artifact replay passed `comparison_guide` and `company_service_intro`; it blocked `market_explanation`, `announcement`, `daily_activity`, and `case_study`. All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`.

Historical next owner was `route_v_market_explanation_human_visible_surface_repair_diagnosis_no_api`.

Non-owner boundaries before the next diagnosis: no API execution, product-code change, accepted-status change, generated article text patch, source refetch, raw full source handoff, Route A / writer-only fallback, broad prompt/persona/QA/selector/source-shape/claim-allocation change, or QA threshold / repair-acceptance relaxation.

## Historical Route V Override: 2026-06-27 Post-Human-Visible Surface Gap Diagnosis

Latest diagnosis artifact:

```text
notecode/logs/0627/route_v_human_visible_article_surface_gap_diagnosis_no_api_20260627_194037/diagnosis.md
```

Decision: `diagnosis_completed_needs_next_owner`. Product code changed false; accepted status changed false; source refetch false; generated article patch false; API send count `0`.

All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`. The diagnosis preserved the article set human visual review result: `company_service_intro` and `comparison_guide` are visually acceptable with caveats, while `market_explanation`, `announcement`, `daily_activity`, and `case_study` require follow-up before user-visible release readiness.

First confirmed gap: `human_visible_surface_gate_missing_after_validation_acceptance_green`. Historical next owner was `route_v_human_visible_surface_gate_no_api_impl`.

Non-owner boundaries before the next implementation: no API execution, accepted-status change, generated article text patch, source refetch, raw full source handoff, Route A / writer-only fallback, broad prompt/persona/QA/selector/source-shape/claim-allocation change, or QA threshold / repair-acceptance relaxation.

## Historical Route V Override: 2026-06-27 Post-Article Set Human Visual Review

Latest human visual review artifact:

```text
notecode/logs/0627/route_v_article_set_human_visual_review_no_api_20260627_191820/human_visual_review.md
```

Decision: `human_visual_review_completed_followup_required`. Product code changed false; accepted status changed false; source refetch false; generated article patch false; API send count `0`.

All six accepted Route V genres remain accepted and remaining unaccepted genres remain `[]`. `company_service_intro` remains visually acceptable with carried caveats and keeps the normal UI user-test article as the human-visible source of truth. `comparison_guide` is visually acceptable with inventory caveats. `market_explanation`, `announcement`, `daily_activity`, and `case_study` require follow-up before being treated as user-visible release-ready because the saved accepted artifacts still show source-fragment leakage, duplication, unrelated CTA carryover, or formatting artifacts.

First confirmed gap: `accepted_validation_green_but_human_visible_article_surface_gap`. Historical next owner was `route_v_human_visible_article_surface_gap_diagnosis_no_api`.

## Historical Route V Override: 2026-06-27 Post-User-Visible Article Set Inventory

Latest user-visible article set inventory artifact:

```text
notecode/logs/0627/route_v_user_visible_article_set_inventory_no_api_20260627_185826/article_set_inventory.md
```

Decision: `article_set_inventory_created`. The inventory records human-visible article paths for all six accepted Route V genres. Product code changed false; accepted status changed false; source refetch false; generated article patch false; API send count `0`.

`company_service_intro` uses the normal UI user-test article as the human-visible source of truth: `notecode/logs/0627/route_v_guarded_release_user_test_manual_ui_20260627_154813/human_review_articles/company_service_intro.md`. It remains user visual accepted as a natural kintone introduction, and its self-perspective plus low-interest reader introduction remain accepted by human visual review. The two unsupported-claim candidates remain visual-review caveats, not product fix blockers.

The other five genres use accepted validation generated articles as human-review candidates. `comparison_guide` and `daily_activity` clean normal UI articles were not generated; this is not a failure because normal UI `CATEGORY_OPTIONS` does not directly expose their Route V IDs and monkeypatching was avoided. Accepted genres remain all six intended Route V genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, and `company_service_intro`. Remaining unaccepted genres: `[]`. Historical next owner at that time was `route_v_article_set_human_visual_review_no_api`.

## Historical Route V Override: 2026-06-27 Post-Human Visual Acceptance Record

Latest human visual acceptance artifact:

```text
notecode/logs/0627/route_v_company_intro_human_visual_acceptance_record_no_api_20260627_182719/human_visual_acceptance_record.md
```

Decision: `human_visual_acceptance_recorded`. The `company_service_intro` article is accepted by user visual review as natural kintone introduction. The same human visual review accepts the `company_service_intro` self-perspective and low-interest reader introduction. Product code changed false; accepted status changed false; source refetch false; generated article patch false; API send count `0`.

The two unsupported-claim candidates from the guarded user-test remain recorded, but they are now visual-review caveats rather than product fix blockers. They do not reopen prompt, persona, QA, selector, source-shape, claim allocation, generated article patching, source refetch, Route A fallback, writer-only fallback, or raw full source handoff.

`comparison_guide` and `daily_activity` were not generated in this clean normal UI test. This is not a failure: normal UI `CATEGORY_OPTIONS` does not directly expose their Route V IDs, and monkeypatching was avoided. Accepted genres remain all six intended Route V genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, and `company_service_intro`. Remaining unaccepted genres: none. Historical next owner at that time was `route_v_user_visible_article_set_inventory_no_api`.

## Historical Route V Override: 2026-06-27 Post-Guarded User-Test

Latest guarded user-test artifact:

```text
notecode/logs/0627/route_v_guarded_release_user_test_manual_ui_20260627_154813/user_test_decision_summary.md
```

Decision: `needs_no_api_diagnosis`. Human-review article saved at `notecode/logs/0627/route_v_guarded_release_user_test_manual_ui_20260627_154813/human_review_articles/company_service_intro.md`; review summary saved at `notecode/logs/0627/route_v_guarded_release_user_test_manual_ui_20260627_154813/review_summaries/company_service_intro_review_summary.md`. Product code changed false; accepted status changed false; source refetch false; generated article patch false.

The normal UI service path invoked Route V/0506 with route id `route_v_0506_structured_blog_v1`. Route A / fallback / writer-only flags were all false. H1 exactly one and H2 sections were present. `company_service_intro` kept self-perspective with narrator `私たち`, self-viewpoint owner `サイボウズ kintone サービス提供者`, and a low-intent reader brief. Raw full source handoff was not observed in nested 0506 artifacts; final-stage artifacts used `article_brief`, `article_knowledge_pack`, and `selected_source_excerpts`.

Stop condition hit: two unsupported-claim candidates were found in `company_service_intro`; after human visual acceptance, these are carried as visual-review caveats. UI service invocations were final run `1` and goal total `3`; OpenAI ledger terminal success rows were final run `6` and goal total `12`; service-reported `api_send_count` on success was `0`. `comparison_guide` and `daily_activity` were not generated through normal UI in this slice because the current `route_v_generation_service.CATEGORY_OPTIONS` path does not directly expose their Route V IDs without a monkeypatch. Historical next owner was `route_v_company_intro_unsupported_claim_no_api_diagnosis`.

## Historical Route V Override: 2026-06-27 Post-User-Test Handoff

Latest user-test handoff artifact:

```text
notecode/logs/0627/route_v_release_user_test_handoff_no_api_20260627_153021/user_test_handoff.md
```

Decision: `proceed_to_guarded_user_test`. API send count `0`; product code changed false; source refetch false; generated article patch false; accepted status changed false; raw full source handoff false; Route A / writer-only fallback changed false. Accepted genres cover all six intended Route V genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, and `company_service_intro`. Remaining unaccepted genres: none. Additional no-API blocker before guarded user-test: none. The historical next owner was `route_v_guarded_release_user_test_manual_ui`.

The handoff checklist requires user-test confirmation of normal UI Route V/0506, route id `route_v_0506_structured_blog_v1`, no Route A / writer-only fallback, no raw full source handoff, exactly one H1 with H2 sections, source_fact / llm_general_context separation, stable self-perspective for `company_service_intro`, no unsupported ranking/date/schedule/price/responsibility claims, and body floor / quality report / over-editing behavior.

Known caveats remain preserved for user-test: early `comparison_guide` / `case_study` evidence gaps, module-bloat debt in `article_brief_source_shape_v2.py`, 0506 validation defaults versus normal UI Route V forced defaults, and the GENIAC/Gennai validation gap.

## Historical Route V Override: 2026-06-27 Post-Readiness Inventory

Latest readiness inventory artifact:

```text
notecode/logs/0627/route_v_all_genres_accepted_release_readiness_inventory_no_api_20260627_150315/readiness_inventory.md
```

Decision: `proceed_to_guarded_release_user_test_handoff`. API send count `0`; product code changed false; source refetch false; generated article patch false; accepted status changed false; raw full source handoff false; Route A / writer-only fallback false. Accepted genres cover all six intended Route V genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, and `company_service_intro`. Remaining unaccepted genres: none. No additional no-API cleanup is required before a guarded user-test handoff. The historical next owner was `route_v_release_user_test_handoff_no_api`.

Known caveats remain preserved for handoff: early `comparison_guide` / `case_study` evidence gaps, module-bloat debt in `article_brief_source_shape_v2.py`, 0506 validation defaults versus normal UI Route V forced defaults, and the GENIAC/Gennai validation gap.

## Historical Route V Override: 2026-06-27 Post-Acceptance Decision

Latest acceptance artifact:

```text
notecode/logs/0627/route_v_all_genres_accepted_release_readiness_inventory_no_api_20260627_150315/readiness_inventory.md
```

Decision: `accepted`; accepted article type: `company_service_intro`. Acceptance owner API send count `0`; validation API send count `1`; product code changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false. The accepted source validation had decision `acceptance_candidate`, final article generated, H1 exactly one, H2 sections present, body floor reached (`1401/1400` final), quality passed (`score=100`, issues none), selected excerpts used, source/persona/over-editing and unsupported-claim guards passed. Accepted genres now cover all six intended Route V genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, and `company_service_intro`. Remaining unaccepted genres: none. The historical next owner was `route_v_all_genres_accepted_release_readiness_inventory_no_api`.

## Historical Route V Override: 2026-06-27 Post-API Validation

Latest validation artifact:

```text
notecode/logs/0627/route_v_company_intro_draft_writer_live_residual_floor_buffer_one_article_api_validation_after_approval_20260627_132914/api_validation_summary.md
```

Decision: `acceptance_candidate`. API send count `1`; product code changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false. The same saved `company_service_intro` source packet was reused and `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2` preflight passed. Final article generated, H1 exactly one, H2 sections present, body floor reached (`1401/1400` final), quality passed (`score=100`, issues none), selected excerpts were used, source/persona/over-editing guards passed, and `company_service_intro` remained unaccepted until the separate acceptance decision. The historical next owner was `route_v_company_intro_draft_writer_live_residual_floor_buffer_acceptance_decision_no_api`.

## Historical Route V Override: 2026-06-27 Post-Implementation

Latest implementation artifact:

```text
notecode/logs/0627/route_v_company_intro_draft_writer_live_residual_floor_buffer_no_api_impl_20260627_170000/implementation_summary.md
```

Decision: `implementation_no_api_gate_pass`. API send count `0`; product code changed true only in DraftWriter company-intro live residual floor buffer scope. Source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false. The first confirmed gap remains `company_intro_draft_writer_live_residual_floor_miss_after_no_api_replay_gap`. DraftWriter followthrough now targets a bounded `floor + live residual buffer` using existing selected excerpts and confirmed facts only. Focused tests and `py_compile` passed. `company_service_intro` remained unaccepted; historical next owner was `route_v_company_intro_draft_writer_live_residual_floor_buffer_one_article_api_validation_after_approval`.

## Historical Route V Override: 2026-06-27 Post-Diagnosis

Latest diagnosis artifact:

```text
notecode/logs/0627/route_v_company_intro_body_floor_reached_failure_diagnosis_no_api_20260627_160000/diagnosis.md
```

Source validation artifact:

```text
notecode/logs/0627/route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_one_article_api_validation_after_approval_20260627_131500/api_validation_summary.md
```

Diagnosis decision: `needs_next_owner`. Diagnosis API send count `0`; product code changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false. The source validation decision was `reject_or_inconclusive` with validation API send count `1`. Preserved validation facts: DraftWriter `1327/1400`, opening/global/style `1329/1400`, structural API raw/guarded/final `917/1400`, QA `961/1400`, H1 exactly one, H2 sections present, and source/persona/selected-excerpt/over-editing guards passed. The first confirmed gap is exactly `company_intro_draft_writer_live_residual_floor_miss_after_no_api_replay_gap`. Structural editor overcompression is a later observation, not the first owner, because the structural input was already below floor at `1329/1400`. QA/human-readability/sentence findings remain secondary observations; the only QA issue is `body_length_below_floor`. `company_service_intro` is not accepted; next owner is `route_v_company_intro_draft_writer_live_residual_floor_buffer_no_api_impl`.

## Historical Route V Override: 2026-06-27 Post-Implementation

Latest implementation artifact:

```text
notecode/logs/0627/route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_no_api_impl_20260627_104857/implementation_summary.md
```

Decision: `implementation_no_api_gate_pass`. API send count `0`; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false. DraftWriter company-intro residual followthrough now uses a bounded residual confirmed-fact backfill after assigned claims when the selected-excerpt followthrough still misses the floor. The first confirmed gap remained exactly `company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough`. Saved-artifact replay reached `1409/1400` from the prior `1155/1400`. `company_service_intro` was not accepted; historical next owner was `route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_one_article_api_validation_after_approval`.

This document records the current implemented algorithm for the Japanese blog generation app. It describes runtime behavior, not only the ideal architecture.

## Default Runtime Mode

The app has two generation modes.

### Local deterministic mode

This is the default unless `BLOGGEN_LLM_MODE=openai` is set.

- Client: `app/services/local_llm_client.py`
- Purpose: repeatable validation of source handoff, persona timing, QA, and UI behavior.
- It does not call an external model.
- It is useful for tests and controlled trial-and-error, but it is not the intended final writing quality path.

### OpenAI mode

Enabled only when:

```powershell
$env:BLOGGEN_LLM_MODE = "openai"
$env:OPENAI_API_KEY = "..."
```

0506 standalone / validation defaults:

- Model: `gpt-5.4-mini`
- Reasoning effort: `high`
- Override model with `OPENAI_MODEL`.
- Override reasoning effort with `OPENAI_REASONING_EFFORT`.
- Route V genre-acceptance validations currently recorded for `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, and `announcement` were run under the 0506 validation assumption of `gpt-5.4-mini` / `high`, not the normal UI Route V forced runtime defaults below.

Normal UI Route V forced defaults:

- `notecode/note/route_v_generation_service.py` forces `OPENAI_MODEL=gpt-4.1` for normal UI Route V generation calls.
- The same UI wrapper clears `OPENAI_REASONING_EFFORT`.
- The same UI wrapper sets `ROUTE_0506_OPENAI_TEMPERATURE` from its code constant; current code is `0.7`.
- This is an intentional UI runtime override, so do not read 0506 validation defaults as proof that normal UI output is generated under `gpt-5.4-mini` / `high`.

The OpenAI client is `app/services/llm_client.py`.

## Pipeline Order

The implemented pipeline is:

```text
Extracted sources
  -> generation source packets
  -> source cards
  -> article knowledge pack
  -> article brief
  -> draft writer
  -> opening editor
  -> global consistency editor
  -> style editor
  -> structural editor
  -> Japanese quality checker
  -> targeted rewriter, only when QA requires rewrite
  -> final quality check
  -> final article artifact
```

Runtime owner: `app/services/pipeline_runner.py`.

## Source Acquisition

Source acquisition converts input sources into `ExtractedSource`.

Supported inputs:

- manual text
- public URL
- PDF
- Word document

Rules:

- Source extraction must preserve source spans.
- URL extraction uses deterministic public HTML extraction first.
- Restricted URLs, login pages, internal APIs, archive/search surfaces, and low-confidence sources must not proceed silently.
- PDF extraction currently uses PyMuPDF text blocks first and falls back to pypdf.
- PDF image pages are noted, but OCR is not currently in scope.

Important files:

- `app/services/source_acquisition.py`
- `app/services/pdf_text_extractor.py`
- `app/services/source_preprocessor.py`

## Generation Source Packets

Each extracted source becomes a generation-facing packet.

The packet:

- caps source text per source,
- chunks long text,
- keeps source span IDs and source locations,
- carries extraction confidence and proceed/block metadata,
- attaches the note/Hatena style target.

The draft writer does not receive raw URLs or raw PDF files. It receives structured claims after the source-card and knowledge-pack stages.

## Source Card Extraction

The source card stage extracts blog-usable facts from one source at a time.

Local deterministic behavior:

- For ordinary sources, `source_fact_segmenter` splits source text into clean fact candidates.
- For PDFs, `local_source_card_builder` samples representative pages and prioritizes known slide themes.
- PDF slide facts are normalized when raw slide text would otherwise produce diagram/table fragments.
- Noise such as navigation labels, fragment headings, and Business Model Canvas diagram labels is filtered.

The source card stage must not:

- infer unsupported facts,
- merge different sources,
- write article prose.

Important files:

- `app/agents/source_card_extractor.py`
- `app/services/source_fact_segmenter.py`
- `app/services/local_source_card_builder.py`

## Knowledge Pack Integration

Source cards are merged into `article_knowledge_pack`.

The knowledge pack owns:

- confirmed facts,
- claim IDs,
- supporting fact IDs,
- conflicts,
- deduped themes,
- do-not-infer rules.

The draft stage uses confirmed claims, not raw source text.

## Article Brief Algorithm

The article brief is the design contract for generation.

Inputs:

- genre ID,
- target reader,
- article goal,
- knowledge pack,
- optional narrator override,
- optional `self_viewpoint_owner`.

Resolved from config/persona data:

- default persona,
- writer role,
- viewpoint profile,
- narrator,
- self-viewpoint owner,
- style profile,
- editor profile,
- QA policy.

The brief includes:

- target length,
- section count,
- source thickness,
- comparison target category for `comparison_guide`,
- headings,
- section purposes,
- assigned claim IDs,
- discourse rules,
- style edit policy,
- editor pass policy.

For self-perspective company/service articles, `self_viewpoint_owner` is the speaker identity behind the narrator.
For example, `私たち` must mean the company/service owner itself, not a third-party reviewer reading that owner.
In Route V / article brief v2, non-price company/service introductions also carry a low-intent visitor hook: the reader may have arrived from search results or a thumbnail without strong prior interest, so the draft should open from a daily, work, or selection context before company-profile explanation. Price/table sources keep the table/list hook instead of being overwritten by this company-intro hook.
The compact company-intro writing contract is maintained in `docs/ARTICLE_BRIEF_V2_SOURCE_SHAPE_ALGORITHM.md`; avoid adding parallel DraftWriter prompt rules for the same self-perspective / low-interest / thin-source behavior.

Important files:

- `app/agents/article_brief_builder.py`
- `app/services/local_llm_client.py`
- `app/config/article_genres.yaml`
- `app/personas/persona_registry.yaml`

### Route V Active Boundary: 2026-06-26

Latest validation and read-only diagnosis:

```text
notecode/logs/0621/route_b_0506_v2_floor_h1_one_api_per_article_20260621_234827/
notecode/logs/0621/draft_writer_floor_actuation_runtime_diagnosis_20260622_005034/
notecode/logs/0622/route_b_0506_v2_paragraph_depth_fix_api_recheck_20260622_122514/
notecode/logs/0622/draft_writer_paragraph_depth_fix_api_recheck_failure_diagnosis_20260622_130918/
```

Operational decision:

- Treat `source_shape` changes across API runs, such as `service_catalog` to `narrative`, as source-card / claim extraction variance unless a new diagnosis proves a deterministic source-shape bug.
- Do not fix the current body-floor issue by changing source-shape detection, claim allocation caps, QA thresholds, or repair acceptance.
- In Route V representative/selective modes, assigned claims are the draft writer's depth anchors. Unassigned claims are retained for trace and guard use, not for enumeration in the article body.
- For `company_service_intro`, the low-intent contract may keep `body_length_floor_chars=1400` even when `source_shape=narrative`; the draft writer must satisfy that floor through source-grounded depth.
- H1 is no longer the active failure owner. Post-fix validation reached exactly one H1 in all 4 completed article types; 2 article types stopped before DraftWriter on API infra errors.
- Body floor remains the active failure owner. Post-fix validation reached final floor in 0/4 completed article types; all 4 failed with `body_length_below_floor`.
- The floor miss usually starts at DraftWriter output. Later deterministic editor/postprocessor stages can reduce text further, but they do not provide a growth path.
- The implemented paragraph-depth fix was transmitted to DraftWriter, but did not improve floor. The latest diagnosis found that paragraph count guidance is followed more reliably than chars-per-anchor depth guidance.
- `draft_writer_floor_actuation_count_based_depth_redesign` is implemented and passed the no-API gate (`39 passed`, `py_compile` pass, `inspect_bloat` pass / `failures=[]`).
- Count-based API isolation recheck artifact: `notecode/logs/0622/route_b_0506_v2_count_based_floor_actuation_api_isolation_recheck_20260622_140222/`.
- Count-based API isolation recheck was partial positive but incomplete: completed 2/6 article types; floor reached 2/2 completed; H1 reached 2/2 completed; quality pass 1/2 completed; 4 article types failed before full evaluation due artifact packaging or API infra errors.
- Failure diagnosis found likely long artifact path / validation packaging issues plus API 520 infra failures.
- Short-path validation packaging recheck artifact: `notecode/logs/0622/cbsp_1429/`.
- Short-path recheck fixed the validation packaging issue, but count-based floor actuation still does not satisfy the output contract: completed 5/6 article types, final floor reached 1/5 completed, H1 reached 5/5 completed, quality pass 0/5 completed, `body_length_below_floor` 4/5 completed. The floor gap improved vs baseline in 5/5 completed comparable types and vs paragraph-depth in 3/3 completed comparable types, but the current output is not ready for user testing.
- Floor-gap diagnosis artifact: `notecode/logs/0622/cbsp_1429/floor_gap_diagnosis.md`.
- Floor-gap diagnosis found that the current paragraph target was met or exceeded in 5/5 completed article types, but draft floor and final floor were only reached in 1/5. The residual is paragraph depth/final-floor buffer, not H1 and not large editor/postprocessor deletion.
- `draft_writer_floor_actuation_depth_budget_contract_impl` is implemented and passed the no-API gate (`39 passed`, `py_compile` pass, `inspect_bloat` pass / `failures=[]`). DraftWriter now uses a bounded source-backed depth budget contract from floor/target chars, section count, assigned claims, and selected excerpts rather than paragraph count alone.
- Depth-budget one-article API smoke artifact: `notecode/logs/0622/dbsm_1550/`. `market_explanation` reached final floor (`1641/1400`), H1 (`1`), and quality pass, but unassigned-claim enumeration regressed to `true` and manual review found sentence-fragment/punctuation issues.
- Source-context handoff diagnosis artifact: `notecode/logs/0623/route_b_source_context_handoff_diagnosis_20260623_000000/diagnosis.md`. First confirmed gap was `draft_writer_excerpt_primary_material_contract_gap`; the excerpt-primary and selected-excerpt coverage owners are now complete.
- Company-introduction thin source material Sanrei validation artifact: `notecode/logs/0624/tmi_sanrei_api_20260624_101500/api_validation_summary.md`. Sanrei selected excerpts reached `4` / `2600`, H1 passed, raw full `source_documents` stayed false, but final floor still failed at `1136/1400`.
- Floor underproduction diagnosis artifact: `notecode/logs/0624/route_v_company_intro_floor_underproduction_after_thin_material_increase_failure_diagnosis_20260624_110000/floor_underproduction_diagnosis.md`. The current confirmed gap is DraftWriter underproduction (`1300/1400`) plus deterministic `style_postprocessor.postprocess_style()` shrink (`1300` -> `1136`).
- Stage-floor contract implementation artifact: `notecode/logs/0624/route_v_company_intro_stage_floor_contract_after_material_increase_no_api_impl_20260624_112516/implementation_summary.md`. DraftWriter now uses a stronger company-intro pre-editor floor buffer, and deterministic `style_postprocessor` preserves floor-critical reader-meta / bridge material instead of causing large floor-critical shrink. API send count was 0.
- Stage-floor Sanrei API validation artifact: `notecode/logs/0624/sfc_sanrei_api_20260624_122335/api_validation_summary.md`. Sanrei reached final floor (`1453/1400`) and H1 (`1`), but quality failed on long sentence / low-density bridge / abstract navigation behavior.
- Targeted rewrite grammar-safety implementation artifact: `notecode/logs/0624/route_v_targeted_rewrite_sentence_split_grammar_safety_repair_20260624_133328/implementation_summary.md`. The narrow comma-split grammar gap is fixed without broad prompt tuning.
- Same-source Sanrei API recheck artifact: `notecode/logs/0624/trg_sanrei_api_20260624_135350/api_validation_summary.md`. The grammar break stayed fixed, but draft/final floor regressed to `1084/1400`, H1 passed, and quality failed. This points back to DraftWriter floor variance, not targeted rewrite grammar safety.
- DraftWriter floor variance diagnosis artifact: `notecode/logs/0624/route_v_company_intro_draft_floor_variance_diagnosis_20260624_144005/diagnosis_summary.md`. Same-source Sanrei reached draft/final floor in the new run (`1606` -> `1488/1400`) but still failed quality on `sentence_too_long`, `ending_bucket_monotony`, and `viewpoint_owner_mismatch`. The diagnosis confirmed DraftWriter floor variance and moved the active owner to the floor-reaching self-viewpoint / dense-bridge quality boundary.
- Self-viewpoint / dense-bridge boundary probe artifact: `notecode/logs/0624/route_v_company_intro_self_viewpoint_dense_bridge_boundary_probe_20260624_000000/position_distribution_analysis.md`. It found late-half ending convergence as model-followthrough, but self-viewpoint drift as prompt/algorithm boundary because `と案内しています` appears in both early and late positions.
- Model-followthrough simple late-rhythm fix artifact: `notecode/logs/0624/route_v_company_intro_model_followthrough_simple_late_rhythm_fix_no_api_20260624_000000/implementation_summary.md`. The implementation kept prompts unchanged and extended only the existing deterministic late-ending safety net in `style_postprocessor.py`; no-API replay removed `ending_bucket_monotony` while leaving `sentence_too_long` and `viewpoint_owner_mismatch` for the bridge/self-viewpoint owner.
- Bridge contract position-aware rewrite artifact: `notecode/logs/0624/route_v_company_intro_bridge_contract_position_aware_rewrite_no_api_20260624_155529/implementation_summary.md`. The implementation kept prompts unchanged, isolated company-intro page-summary voice rewriting in `style_postprocessor.py`, and isolated the historical long-sentence split in `editor_output_safety.py`; no-API replay reached quality pass (`score=100`, final `1480/1400`).
- Bridge contract position-aware rewrite Sanrei API validation artifact: `notecode/logs/0624/bcpr_sanrei_api_20260624_160044/api_validation_summary.md`. Sanrei passed final floor (`1453/1400`), H1 (`1`), and quality (`score=100`, issues none) in one approved API send; product code changed during validation false, raw full `source_documents` passed false, Route A / writer-only fallback false.
- Interest bridge positive contract Sanrei API validation artifact: `notecode/logs/0624/ibpc_sanrei_api_20260624_164909/api_validation_summary.md`. The reader-navigation bridge target improved, but Sanrei failed final floor (`1298/1400`) with quality failing only on `body_length_below_floor`.
- Interest bridge floor regression diagnosis artifact: `notecode/logs/0624/route_v_company_intro_interest_bridge_positive_contract_floor_regression_diagnosis_20260624_170346/floor_regression_diagnosis.md`. It found the negative reader-navigation clause removed paragraph volume without redirecting budget into source-grounded claim backfill.
- Paragraph-budget backfill no-API implementation artifact: `notecode/logs/0624/route_v_company_intro_interest_bridge_paragraph_budget_backfill_contract_no_api_20260624_172154/implementation_summary.md`. DraftWriter now redirects blocked navigation framing into assigned-claim depth or relevant unassigned confirmed claims as context, not inventory, and normalizes legacy company-intro `paragraph_function_plan` payload slots before send; source-shape detection, claim allocation, QA threshold, and repair acceptance remain unchanged.
- Paragraph-budget backfill Sanrei API validation artifact: `notecode/logs/0624/pbb_sanrei_api_20260624_185848/api_validation_summary.md`. Sanrei failed final floor (`1326/1400`) and quality (`score=52`) while H1 passed (`1`); product code changed during validation false, raw full `source_documents` passed false, Route A / writer-only fallback false. The DraftWriter payload no longer had the legacy `paragraph_function_plan` exact markers, so the next boundary is residual navigation-shaped cues in other payload fields.
- Residual payload navigation cue boundary diagnosis artifact: `notecode/logs/0624/route_v_company_intro_interest_bridge_residual_payload_navigation_cue_boundary_no_api_diagnosis_20260624_191224/diagnosis_summary.md`. Web research and local trace found the remaining `分かります` / `見えてきます` problem is a reader-inference frame, not a global phrase-ban problem; the next control should be a positive replacement contract from reader cognition to company-side source-backed action/value.
- Reader-inference to source-action no-API implementation artifact: `notecode/logs/0624/route_v_company_intro_reader_inference_to_source_action_contract_no_api_20260624_192852/implementation_summary.md`. DraftWriter now normalizes company-intro self-authored residual payload fields from reader/outside-observer inference into company-side source-backed action/value guidance before send. This is category-specific replacement, not phrase-list growth; source-shape detection, claim allocation/caps, QA threshold, repair acceptance, and H1 contract remain unchanged.
- Reader-inference to source-action Sanrei API validation artifact: `notecode/logs/0624/route_v_company_intro_reader_inference_to_source_action_contract_one_article_api_validation_20260624_194041/api_validation_summary.md`. API send count 1, product code changed during validation false, raw full `source_documents` passed false, Route A / writer-only fallback false. Sanrei passed reader-inference bridge review (`0` disallowed frames) and H1 (`1`) but missed final floor (`1166/1400`); quality failed only on `body_length_below_floor`.
- Reader-inference contract floor regression diagnosis artifact: `notecode/logs/0624/route_v_company_intro_reader_inference_contract_floor_regression_diagnosis_20260624_200131/floor_regression_diagnosis.md`. API send count 0, product code changed false. The compact company-side action/value contract removed the target frame without prompt bloat, but the Sanrei floor miss started at DraftWriter underproduction (`1175` draft -> `1166` final), so one same-contract Sanrei API validation was selected before any implementation owner.
- Reader-inference contract Sanrei API validation after diagnosis artifact: `notecode/logs/0624/route_v_company_intro_reader_inference_contract_sanrei_one_article_api_validation_after_diagnosis_20260624_204407/api_validation_summary.md`. API send count 1, product code changed during validation false, raw full `source_documents` passed false, Route A / writer-only fallback false. Sanrei again missed floor at DraftWriter output (`1215/1400` draft, `1219/1400` final), H1 passed (`1`), quality failed (`score=76`), and paragraph metrics showed draft `14` non-heading paragraphs with `82.1` average chars.
- Front/back editor persona two-API trial artifact: `notecode/logs/0624/route_v_company_intro_front_back_editor_persona_two_api_trial_after_encoding_guard_20260624_213222/api_trial_summary.md`. API send count 2 as a user-approved exploratory exception, encoding preflight passed, product code changed during trial false, raw full `source_documents` passed false, Route A / writer-only fallback false. Sanrei reached final floor (`1452/1400`), H1 (`1`), and reader-frame marker pass (`0` hits), but quality failed (`score=84`, `sentence_too_long`, `model_frequent_word`). This is trial observation, not acceptance.
- Front/back editor persona one-API refinement artifact: `notecode/logs/0624/route_v_company_intro_front_back_editor_persona_one_api_refinement_trial_after_two_pass_20260624_214820/api_trial_summary.md`. API send count 1, encoding preflight passed, product code changed during trial false, raw full `source_documents` passed false, Route A / writer-only fallback false. Sanrei reached final floor (`1502/1400`), H1 (`1`), and reader-frame marker pass (`0` hits), but quality failed (`score=84`, `sentence_too_long`, `model_frequent_word`). This is trial observation, not acceptance.
- Cross-genre editor persona contract config no-API implementation artifact: `notecode/logs/0624/route_v_cross_genre_editor_persona_contract_config_no_api_impl_20260624_223244/implementation_summary.md`. API send count 0, compact six-genre config/renderer/preflight passed.
- Cross-genre non-announcement second editor policy artifact: `notecode/logs/0624/route_v_cross_genre_non_announcement_editor_pass_policy_no_api_revision_20260624_225013/policy_revision_summary.md`. API send count 0, `announcement` keeps no second pass, and the other five genres have short configured second editor roles.
- Cross-genre editor persona contract editor-stage wiring artifact: `notecode/logs/0625/route_v_cross_genre_editor_persona_contract_editor_stage_wiring_no_api_impl_20260625_002659/implementation_summary.md`. API send count 0, editor agents now receive the rendered contract, `pipeline_runner` calls editor agents, local deterministic behavior is preserved, and observer/OpenAI-capable boundaries can see editor-stage instructions.
- Cross-genre editor persona contract comparison-guide one-API validation artifact: `notecode/logs/0625/route_v_cross_genre_editor_persona_contract_comparison_guide_one_api_validation_after_wiring_20260625_090000/api_validation_summary.md`. API send count 1, product code changed false, editor-stage instruction contract present, source_fact / llm_general_context separation acceptable, unsupported ranking / best-claim false, third-party viewpoint false, raw full `source_documents` false, Route A / writer-only fallback false, and quality pass true.
- Comparison-guide heading-level validation artifact: `notecode/logs/0625/route_v_comparison_guide_heading_level_one_article_api_validation_after_approval_20260625_101206/api_validation_summary.md`. API send count 1, product code changed false, exactly one H1 and H2 section headings passed, source_fact / llm_general_context separation passed, quality passed, and decision was `acceptance_candidate`.
- Comparison-guide opening subject-specificity validation artifact: `notecode/logs/0625/route_v_comparison_guide_opening_subject_specificity_one_article_api_validation_after_approval_20260625_121019/api_validation_summary.md`. API send count 1, product code changed false, editor-stage contract reached the structural editor, candidates and four axes appeared in the opening, H1/H2/source handoff/fallback guards passed, but the opening omitted the comparison target category and quality failed on `connector_repetition`.
- Comparison-guide category-field no-API implementation artifact: `notecode/logs/0625/route_v_comparison_guide_article_brief_comparison_target_category_field_no_api_impl_20260625_131141/implementation_summary.md`. API send count 0, product code changed only in the article_brief schema/builder plus focused tests. `comparison_target_category` is derived from existing target_reader / confirmed-claim material, excluded from the OpenAI strict response schema, and reaches editor-stage payloads in no-API replay.
- Comparison-guide category-field one-article API validation artifact: `notecode/logs/0625/route_v_comparison_guide_category_field_one_article_api_validation_after_approval_20260625_132712/api_validation_summary.md`. API send count 1, product code changed false, `comparison_target_category` reached the OpenAI structural-editor payload, the final opening included the comparison target category, three candidate names, and three axes, H1/H2/source handoff/fallback guards passed, quality passed, and decision was `acceptance_candidate`.
- Comparison-guide category-field acceptance decision artifact: `notecode/logs/0625/route_v_comparison_guide_category_field_acceptance_decision_no_api_20260625_134814/acceptance_decision.md`. API send count 0, product code changed false, decision accepted, and the next owner moved to case-study validation.
- Case-study editor persona contract one-article API validation artifact: `notecode/logs/0625/route_v_case_study_editor_persona_contract_one_article_api_validation_after_approval_20260625_140859/api_validation_summary.md`. API send count 1, product code changed false, editor-stage contract and `case_study` structural-editor second pass were present, H1/H2/source-boundary/fallback/raw-source guards passed, and final QA failed only on `paragraph_rhythm_monotony`.
- Case-study paragraph-rhythm failure diagnosis artifact: `notecode/logs/0625/route_v_case_study_paragraph_rhythm_monotony_failure_diagnosis_no_api_20260625_143023/diagnosis.md`. API send count 0, product code changed false, and the first confirmed gap was `structural_editor_missing_knowledge_pack_payload_for_case_study_rhythm_repair`.
- Case-study structural-editor knowledge-pack payload contract implementation artifact: `notecode/logs/0625/route_v_case_study_structural_editor_knowledge_pack_payload_contract_no_api_impl_20260625_143533/implementation_summary.md`. API send count 0, product code changed true only in structural-editor payload wiring and focused tests. The structural editor now receives existing structured `knowledge_pack` material without raw source handoff.
- Daily-activity structural-editor floor-loss guard validation artifact: `notecode/logs/0626/daily_activity_structural_editor_floor_loss_guard_one_article_api_validation_after_approval_20260626_100740/api_validation_summary.md`. API send count 1, product code changed false, source refetch false, generated article patch false, and the live guard preserved the floor-reaching structural input (`1200/1200`) after structural API raw fell to `704/1200`.
- Daily-activity quality-pass failure diagnosis after floor-loss guard artifact: `notecode/logs/0626/route_v_daily_activity_quality_pass_failure_diagnosis_no_api_20260626_102004/diagnosis.md`. API send count 0, product code changed false, source refetch false, generated article patch false, and the first confirmed gap is exactly `targeted_rewrite_sentence_split_limit_followthrough_gap`.
- Historical market-explanation body-floor diagnosis artifact: `notecode/logs/0626/route_v_market_explanation_one_article_api_validation_after_approval_20260626_130000/diagnosis.md`. API send count 0, product code changed false, source refetch false, generated article patch false. First confirmed gap was exactly `draft_writer_selected_excerpt_floor_followthrough_gap`; DraftWriter received the floor/depth contract and selected excerpts but stopped at `434/1200` body chars excluding headings, while the structural editor increased length to `703/1200`.
- Historical market-explanation DraftWriter selected-excerpt floor followthrough implementation artifact: `notecode/logs/0626/route_v_market_explanation_draft_writer_selected_excerpt_floor_followthrough_no_api_impl_20260626_134109/implementation_summary.md`. API send count 0, product code changed true, source refetch false, generated article patch false. The old market-explanation next owner `route_v_market_explanation_draft_writer_selected_excerpt_floor_followthrough_one_article_api_validation_after_approval` is completed history, not the current next owner.
- Announcement body-floor diagnosis artifact: `notecode/logs/0626/route_v_announcement_body_floor_reached_failure_diagnosis_no_api_20260626_173000/diagnosis.md`. API send count 0, product code changed false, source refetch false, generated article patch false. First confirmed gap is exactly `announcement_draft_writer_selected_excerpt_floor_followthrough_gap`.
- DraftWriter is the first below-floor stage for the announcement case: draft body was `335/900` chars excluding headings. DraftWriter received `body_length_floor_chars=900`, `target_length_chars=1200`, selected excerpt context, and 18 confirmed claims, but stopped below floor.
- The structural editor floor-loss guard is not the first owner for the announcement miss because the structural editor received an already-subfloor input (`330/900`) before structural API raw shortened it further.
- Announcement DraftWriter selected-excerpt floor followthrough implementation artifact: `notecode/logs/0626/route_v_announcement_draft_writer_selected_excerpt_floor_followthrough_no_api_impl_20260626_190839/implementation_summary.md`. API send count 0, product code changed true, source refetch false, generated article patch false. No-API replay improved DraftWriter body chars excluding headings from `335/900` to `963/900` using selected excerpt and confirmed-claim material while preserving compact formal notice tone.
- Announcement DraftWriter selected-excerpt floor followthrough API validation artifact: `notecode/logs/0626/route_v_announcement_draft_writer_selected_excerpt_floor_followthrough_one_article_api_validation_after_approval_20260626_194056/api_validation_summary.md`. API send count 1, product code changed false, source refetch false, generated article patch false. Final article generated, H1 exactly one, H2 sections present, body floor reached `958/900`, quality passed, source/persona/selected-excerpt/over-editing checks passed, and the structural editor floor-loss guard preserved the floor-reaching input after structural API raw fell to `671/900`. Decision was `acceptance_candidate`; this API validation owner is completed history.
- Announcement acceptance decision artifact: `notecode/logs/0626/route_v_announcement_draft_writer_selected_excerpt_floor_followthrough_acceptance_decision_no_api_20260626_202716/acceptance_decision.md`. API send count 0, product code changed false, source refetch false, generated article patch false. Decision is `accepted`; accepted genres are now `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, and `announcement`; remaining unaccepted genre is `company_service_intro`.
- Company-introduction front/back editor persona contract config implementation artifact: `notecode/logs/0626/route_v_company_intro_front_back_editor_persona_contract_config_no_api_impl_20260626_214957/implementation_summary.md`. Decision `implementation_no_api_gate_pass`; API send count 0; product code changed true only in compact editor persona config/renderer/preflight/stage-boundary focused test scope; source refetch false; generated article patch false. This no-API implementation owner is completed history.
- Company-introduction front/back editor persona contract retry after API 520 artifact: `notecode/logs/0626/route_v_company_intro_front_back_editor_persona_contract_one_article_api_validation_retry_after_api_520_20260626_231500/api_validation_summary.md`. Decision `reject_or_inconclusive`; API send count 1; product code changed false; source refetch false; generated article patch false. Final article generated, H1 exactly one, H2 section headings, source/persona/selected-excerpt/over-editing/raw-source/fallback guards passed, but body floor failed (`718/1400`) and quality failed only on `body_length_below_floor`.
- Company-introduction body-floor diagnosis artifact: `notecode/logs/0627/route_v_company_intro_body_floor_reached_failure_diagnosis_no_api_20260627_000000/diagnosis.md`. Decision `needs_next_owner`; API send count 0; product code changed false; source refetch false; generated article patch false; prompt/persona tuning false; QA relaxation false. First below-floor stage was DraftWriter (`328/1400`), and first confirmed gap is exactly `company_intro_draft_writer_selected_excerpt_floor_followthrough_gap`.
- Company-introduction DraftWriter selected-excerpt floor followthrough implementation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_selected_excerpt_floor_followthrough_no_api_impl_20260627_010000/implementation_summary.md`. Decision `implementation_no_api_gate_pass`; API send count 0; source refetch false; generated article patch false. The implementation changed product code only in DraftWriter selected-excerpt floor followthrough scope, passed focused tests (`20 passed`), `py_compile`, changed-file bloat, and prompt-bloat gates, and selected the next API validation owner.
- Company-introduction DraftWriter selected-excerpt floor followthrough API validation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_selected_excerpt_floor_followthrough_one_article_api_validation_after_approval_20260627_091448/api_validation_summary.md`. Decision `reject_or_inconclusive`; API send count 1; product code changed false; source refetch false; generated article patch false. The same saved source packet was reused and `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2` preflight passed. Final article generated, H1 exactly one, H2 sections present, source/persona/selected-excerpt/over-editing/raw-source/fallback guards passed, but body floor failed (`draft 1155/1400`, final 331/1400, QA 375/1400) and quality failed on `body_length_below_floor` plus `ending_bucket_monotony`.
- Company-introduction body-floor diagnosis after selected-excerpt followthrough artifact: `notecode/logs/0627/route_v_company_intro_body_floor_reached_failure_diagnosis_no_api_20260627_092734/diagnosis.md`. Decision `needs_next_owner`; API send count 0; product code changed false; source refetch false; generated article patch false; prompt/persona tuning false; QA relaxation false. First below-floor stage is DraftWriter (`1155/1400`), largest later loss is structural API raw (`1157/1400` -> `331/1400`), and first confirmed gap is exactly `company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough`.
- Accepted genres remain `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, and `announcement`.
- Remaining unaccepted genre: `company_service_intro`.
- Evidence caveat from `route_v_docs_evidence_settings_consistency_audit_no_api_20260627_150000`: accepted status is unchanged, but the earliest accepted `comparison_guide` and `case_study` chains do not contain an explicit body-floor pass/fail field. `comparison_guide` also has an unreconciled same-run `structural_quality_report.json` concern that may be normal repair-loop behavior but was not traced in that audit. `case_study` has body-char count variation across artifacts (`775` / `819` / `848`). These are evidence gaps to preserve, not acceptance-status changes in this docs-sync owner.
- Historical next owner before residual implementation: `route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_no_api_impl`.
- Non-owner boundaries: no API retry before implementation gate, source refetch, generated article patch, raw full source handoff, Route A / writer-only fallback, selector cap/windowing change, source-shape or claim-allocation/cap change, QA threshold or repair-acceptance relaxation, broad prompt/persona tuning, structural-editor prompt/persona growth as first owner, or `company_service_intro` acceptance without a new evaluable validation and separate acceptance decision.

## Genre and Persona Rules

The current supported genres are:

| Genre ID | UI label | Persona meaning | Default narrator | Style |
|---|---|---|---|---|
| `market_explanation` | 解説・市場を伝える | We are the explainer reading and unpacking the material for readers. | 私たち | note/Hatena owned-media |
| `company_service_intro` | 会社・サービスの紹介記事を書く | We are the company or service owner. | 私たち | note/Hatena owned-media |
| `announcement` | お知らせを伝える | We are the formal notice issuer. | 当社 | compact formal notice |
| `case_study` | 事例・お客様の声を伝える | We narrate as the provider and keep customer voice attributed. | 私たち | note/Hatena owned-media |
| `comparison_guide` | 比較・選び方を整理する | We guide readers through supported selection criteria. | 私たち | note/Hatena owned-media |
| `daily_activity` | 日常のできごとを伝える | We share daily activity warmly but factually. | 私たち | note/Hatena owned-media |

Route V genre-specific arrival and source-derived expansion contracts are tracked in `docs/GENRE_ARRIVAL_CONTRACT_MATRIX.md`. In particular, `daily_activity` may use diary-style source-near expansion from place, action, object, sequence, and constraint, but must not invent third-party feelings, outcomes, numbers, or strong causality.

### Announcement special handling

Announcements are intentionally separate.

They use:

- narrator: `当社`
- style profile: `formal_notice_compact`
- shorter local deterministic length planning,
- explicit dates, targets, actors, and notes when present.

They should not be warmed up into a long blog essay unless the user explicitly changes the mode.

## Draft and Editor Timing

The current editor timing is:

```text
draft_writer
  -> opening_editor
  -> global_consistency_editor
  -> style_editor
  -> structural_editor
```

As of 2026-06-25, `pipeline_runner` calls the editor agents for these editor stages. The editor agents render the compact cross-genre editor persona contract into the stage instruction boundary. Local deterministic mode still executes deterministic editor services through `LocalPipelineClient`, while observer/OpenAI-capable boundaries can now see editor-stage instructions.

As of 2026-06-26, `company_service_intro` has a compact front/back editor persona contract. The front half keeps `私たち` as the company/service provider and opens from source-present work, life, selection, or operation contact points for low-interest readers. The structural-editor second pass acts as a source-backed back-half editor and may deepen product handling, operations, exhibitions, history, integration, or philosophy only when those materials are present in selected excerpts or confirmed claims. This does not change source-shape detection, selector caps/windowing, claim allocation/caps, QA thresholds, repair acceptance, or raw source handoff.

`announcement` has no second editor persona. For the other five genres, the conditional second editor persona is wired only at `structural_editor`, where the late-half pass naturally belongs. Added-text guidance is intentionally compact: added text should increase source-backed meaning density, not filler.

### Draft writer

Writes the first body from:

- `article_brief`,
- `article_knowledge_pack`.

It must use only confirmed claims.

### Opening editor

Focus:

- front-half naturalness,
- removal of implementation-meta openings,
- persona-specific opening alignment.

For `market_explanation`, the opening treats `私たち` as the explainer, not the PDF author or company.

### Global consistency editor

Focus:

- whole-article voice after opening edits,
- duplicate motif reduction,
- self-praise softening,
- repeated ending reduction in known deterministic paths.

### Style editor

Focus:

- paragraph grouping,
- safe subject omission,
- ending-bucket variation,
- avoiding mechanical note/Hatena rhythm.

It must not add facts.

### Structural editor

Focus:

- late-half structure,
- paragraph splitting,
- first-person consistency,
- heading-to-body continuity.

It must not add claims.

## QA and Rewrite

The Japanese quality checker uses deterministic stylometry signals plus explicit risky phrase checks.

It checks:

- sentence length,
- paragraph rhythm,
- ending bucket concentration,
- connector repetition,
- first-person variants,
- third-party viewpoint leakage,
- self-viewpoint owner mismatch,
- model-frequent words,
- risky AI-like phrases.

If `rewrite_needed=false`, targeted rewriting is skipped.

If `rewrite_needed=true`, the targeted rewriter should fix only flagged spans and preserve facts.

The final article is checked again after rewriting.

Important files:

- `app/agents/japanese_quality_checker.py`
- `app/services/stylometry.py`
- `app/agents/targeted_rewriter.py`

## Artifact Outputs

Each run writes artifacts under `artifacts/runs/<run_id>/`.

Typical outputs:

- `source_packets.json`
- `source_cards.json`
- `article_knowledge_pack.json`
- `article_brief.json`
- `draft.md`
- `opening_edited_draft.md`
- `global_consistency_edited_draft.md`
- `edited_draft.md`
- `structural_edited_draft.md`
- `editor_pass_report.json`
- `latest_generation_quality_report.json`
- `latest_generation_output.md`

Quality review packages may copy selected final artifacts into a stable directory such as:

- `artifacts/quality_review_package_kyotokogyo/`
- `artifacts/quality_review_package_pdf_1371322/`
- `artifacts/GPT5.4mini/`

## Current Validation State

Latest Route V owner artifact:

```text
notecode/logs/0628/route_v_daily_activity_user_tolerance_record_no_api_20260628_130737/user_tolerance_record.md
```

Decision: `user_visible_acceptable_with_caveats`. API send count `0` for this owner; source validation API send count `1`; product code changed false; source refetch false; generated article patch false; accepted status changed false; raw full source handoff false; Route A / writer-only fallback false. The user reviewed the latest `daily_activity` article and said it is almost acceptable; the later half still feels somewhat third-party, but is barely acceptable. Preserved caveats are `duplicate_long_sentence`, `model_frequent_word`, `duplication`, no `私たち`, and slight third-party feel in the later half. Historical next owner was `route_v_case_study_human_visible_surface_repair_diagnosis_no_api`.

Latest owner validation / checks:

```powershell
no API or product-code command was run for the user tolerance owner
```

Result:

```text
artifact consistency check passed; user tolerance recorded with api_send_count=0
```

Module bloat status:

- The 300-line service-module threshold has not been changed or weakened.
- Current code is not fully under that threshold: `app/agents/article_brief_builder.py` recounts at `311` lines, `app/services/article_brief_source_shape_v2.py` at `415` lines, and `app/services/style_postprocessor.py` at `334` lines.
- These files remain known non-owner bloat debt; the latest validation changed no product files.
- Prompt templates remain compact.
- Source-grounding and QA thresholds have not been weakened.

## Known Current Limitations

- Local deterministic mode is useful for pipeline validation, not final prose quality.
- 0506 standalone OpenAI mode and normal UI Route V use the same staged client boundary, but normal UI Route V forces `gpt-4.1`, clears reasoning effort, and sets the temperature via `notecode/note/route_v_generation_service.py`; usage/cost logging is not yet persisted.
- PDF extraction does not perform OCR.
- Route V paragraph-depth OpenAI outputs missed `body_length_floor_chars`; count-based floor actuation was implemented and then refined into a DraftWriter depth-budget contract. The latest no-API implementation makes bounded selected source excerpts the DraftWriter primary section context before any further API isolation recheck.
- Route V genre acceptance records currently cover all six intended genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, and `company_service_intro`.
- Remaining unaccepted genres: `[]`. User-visible readiness now treats latest `daily_activity` as acceptable with caveats; `case_study` remains the next human-visible blocker owner.
