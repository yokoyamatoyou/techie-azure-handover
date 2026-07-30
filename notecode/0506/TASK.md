# TASK.md

## Current Override 2026-06-28 Post-Manual UI Article Type Image Validation

- Latest validation artifact: `notecode/logs/0628/rv_ui_img_20260628_180205/validation_summary.json`.
- Decision: `needs_review`; UI reachability passed; all six article types generated; all six article types produced both text and no-text image variants.
- Service invocation counts in this owner: article generation invocations `12`; image generation invocations `12`; successful image variants `24`; Route V/0506 OpenAI terminal send count `52`.
- Current normal UI body generation route is Route V (`route_v_0506_structured_blog_v1`). Route B is retired naming; legacy `route_b_*` artifact paths are historical evidence only.
- Article readiness by genre: `comparison_guide=pass`, `company_service_intro=needs_review`, `market_explanation=needs_review`, `announcement=pass`, `daily_activity=pass`, `case_study=pass`.
- Image readiness by genre: all six genres `success` with `with_text_success=true`.
- First confirmed gap: `company_service_intro:article`; final quality issues include `model_frequent_word` and `duplication`. Secondary gap: `market_explanation:article`; final quality issues include `model_frequent_word` and `ending_bucket_monotony`.
- Product code changed `false`; source refetch `false`; generated article patch `false`; raw full source handoff `false`; Route A fallback `false`; writer-only fallback `false`; QA threshold relaxed `false`; repair acceptance relaxed `false`; prompt bloat `none`; module bloat `none`.
- Current next owner: `route_v_first_gap_review`.
- Allowed next scope: diagnose the saved artifacts for the first confirmed `company_service_intro` article quality failure and identify one narrow owner before any further API execution or implementation.
- Non-owner boundaries before/within the next owner: no source refetch, generated article patch, raw full source handoff, Route A / writer-only fallback, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or broad module/prompt expansion.

## Historical Override 2026-06-28 Post-Guarded User Evaluation Artifact

- Latest user evaluation artifact: `notecode/logs/0628/route_v_guarded_user_evaluation_artifact_no_api_20260628_134325/review_index.md`. `copy_manifest.json` has all six article hashes matching their source artifacts.
- Source inventory artifact: `notecode/logs/0628/route_v_article_set_readiness_inventory_no_api_20260628_134223/article_set_readiness_inventory.md`.
- Latest acceptance artifact: `notecode/logs/0628/route_v_case_study_local_surface_sanitization_acceptance_decision_no_api_20260628_133650/acceptance_decision.md`.
- Source validation artifact: `notecode/logs/0628/route_v_case_study_local_surface_sanitization_one_article_api_validation_after_approval_20260628_132909/api_validation_summary.md`.
- Gate enablement artifact: `notecode/logs/0628/route_v_human_visible_surface_gate_case_study_enablement_no_api_impl_20260628_133549/implementation_summary.md`.
- Decision: `user_evaluation_artifact_ready`.
- Evaluation artifact owner API send count `0`; copied article count `6`; all copy hashes match; upstream case_study API send count `1`; product code changed in evaluation owner false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Runtime brief human-visible surface gate recheck after enablement passed with findings `[]`.
- Historical next owner: `route_v_user_evaluation_waiting_for_manual_review`.
- Allowed next scope: wait for manual user review of the bundled article set; do not run API or change product code before the user gives evaluation feedback.
- Non-owner boundaries before/within the next owner: no API execution, source refetch, generated article patch, accepted-status mutation, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or product-code edits.

## Historical Override 2026-06-28 Post-Case-Study Local Surface Sanitization Implementation

- Latest implementation artifact: `notecode/logs/0628/route_v_case_study_local_surface_sanitization_no_api_impl_20260628_132141/implementation_summary.md`.
- Source diagnosis artifact: `notecode/logs/0628/route_v_case_study_human_visible_surface_repair_diagnosis_no_api_20260628_131533/diagnosis.md`.
- Decision: `implementation_completed_needs_one_article_api_validation_after_approval`.
- API send count `0`; product code changed true; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Changed files: `notecode/0506/app/services/draft_followthrough.py`, `notecode/0506/app/agents/draft_writer.py`, `notecode/0506/tests/test_draft_writer.py`.
- Saved-artifact replay after sanitizer passed human-visible surface gate with finding codes `[]`.
- Historical next owner: `route_v_case_study_local_surface_sanitization_one_article_api_validation_after_approval`.
- Allowed next scope: run one guarded same-source `case_study` API validation after approval/guarded continuation; reuse the saved source packet and keep API send count to one for this owner.
- Non-owner boundaries before/within the next owner: no source refetch, generated article patch, accepted-status mutation, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or additional product-code edits as part of validation.

## Historical Override 2026-06-28 Post-Case-Study Human-Visible Surface Diagnosis

- Latest diagnosis artifact: `notecode/logs/0628/route_v_case_study_human_visible_surface_repair_diagnosis_no_api_20260628_131533/diagnosis.md`.
- Source gate replay: `notecode/logs/0627/route_v_human_visible_surface_gate_no_api_impl_20260627_200358/surface_gate_replay_report.json`.
- Source validation artifact: `notecode/logs/0625/route_v_case_study_structural_editor_knowledge_pack_payload_contract_one_article_api_validation_after_approval_20260625_152645/api_validation_summary.md`.
- Decision: `diagnosis_completed_needs_next_owner`.
- API send count `0`; product code changed false; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Human-visible blocker: `generic_local_opening`, `unrelated_local_cta`, and `dangling_japanese_quote_fragment`.
- First confirmed gap: `case_study_local_surface_sanitization_gap`.
- Historical next owner: `route_v_case_study_local_surface_sanitization_no_api_impl`.
- Allowed next scope: implement a narrow case-study local surface sanitizer/followthrough that removes the confirmed local opening, unrelated local CTA, and dangling quote source-fragment from case-study drafts/replays while preserving H1/H2, source grounding, narrator boundary, and quality gates.
- Non-owner boundaries before/within the next owner: no API execution, source refetch, generated article text patch, accepted-status mutation, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or broad phrase-list growth beyond the confirmed local surface defects.

## Historical Override 2026-06-28 Post-Daily-Activity User Tolerance Record

- Latest user tolerance artifact: `notecode/logs/0628/route_v_daily_activity_user_tolerance_record_no_api_20260628_130737/user_tolerance_record.md`.
- Source validation artifact: `notecode/logs/0628/route_v_daily_activity_local_surface_sanitization_one_article_api_validation_after_approval_20260628_123856/api_validation_summary.md`.
- Decision: `user_visible_acceptable_with_caveats`.
- API send count `0` for this owner; source validation API send count `1`; product code changed false; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- User review: the latest `daily_activity` article is almost acceptable; the later half still feels somewhat third-party, but is barely acceptable.
- Preserve caveats: `duplicate_long_sentence`, `model_frequent_word`, `duplication`, no `私たち`, and slight third-party feel in the later half.
- Historical next owner: `route_v_case_study_human_visible_surface_repair_diagnosis_no_api`.
- Allowed next scope: diagnose the saved accepted `case_study` candidate and human-visible surface gate blocker from existing artifacts only; identify the first responsible owner for `generic_local_opening`, `unrelated_local_cta`, and `dangling_japanese_quote_fragment`.
- Non-owner boundaries before/within the next owner: no API execution, source refetch, generated article text patch, accepted-status mutation, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or symptom-only phrase replacement.

## Historical Override 2026-06-28 Post-Daily-Activity Local Surface Sanitization API Validation

- Latest validation artifact: `notecode/logs/0628/route_v_daily_activity_local_surface_sanitization_one_article_api_validation_after_approval_20260628_123856/api_validation_summary.md`.
- Decision: `reject_or_inconclusive`; API send count `1`; retry count `0`; product code changed false; accepted status changed false; source refetch false; generated article patch false.
- Final body floor reached `1234/1200`; human-visible surface gate failed on `duplicate_long_sentence`; quality failed with `model_frequent_word` and `duplication`; self-perspective consistency failed because no `私たち` appears in the final article.

## Historical Override 2026-06-28 Post-Market-Explanation Acceptance Decision

- Latest acceptance artifact: `notecode/logs/0628/route_v_market_explanation_acceptance_decision_no_api_20260628_094825/acceptance_decision.md`.
- Source validation artifact: `notecode/logs/0628/route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_one_article_api_validation_after_approval_20260628_014124/api_validation_summary.md`.
- Decision: `accepted`.
- Acceptance owner API send count `0`; source validation API send count `1`; product code changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- `market_explanation` can be treated as accepted / user-visible release-ready for the latest same-source validation chain.
- Preserved validation facts: body floor draft/opening/global/style `1397/1200`; structural API raw `932/1200`; structural API guarded `1397/1200`; final `1393/1200`; quality issues `[]`; max sentence length `81`; over-limit count `0`; human-visible surface gate findings `[]`.
- Source boundary, selected excerpt usage, structural floor-loss guard, prompt bloat, and algorithm bloat passed.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_announcement_human_visible_surface_repair_diagnosis_no_api`.
- Non-owner boundaries before the next owner: no API execution, source refetch, generated article text patch, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or product-code change as the first move.

## Historical Override 2026-06-28 Post-Market-Explanation Targeted Rewrite Sentence Split Suru-Event API Validation

- Latest validation artifact: `notecode/logs/0628/route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_one_article_api_validation_after_approval_20260628_014124/api_validation_summary.md`.
- Decision: `acceptance_candidate`.
- API send count `1` for this validation owner; product code changed false; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Same saved `market_explanation` source packet reused.
- Stage trace body floor: draft/opening/global/style `1397/1200`; structural API raw `932/1200`; structural API guarded `1397/1200`; final `1393/1200`.
- Quality passed with issues `[]`; sentence split followthrough max sentence length `81`, over-limit count `0`; human-visible surface gate findings `[]`.
- Source boundary and selected excerpt usage passed; structural floor-loss guard blocked harmful compression; prompt/algorithm bloat checks passed.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_acceptance_decision_no_api`.
- Non-owner boundaries before the next owner: no API execution, source refetch, generated article text patch, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or accepted-status mutation without an explicit acceptance decision record.

## Historical Override 2026-06-28 Post-Market-Explanation Targeted Rewrite Sentence Split Suru-Event No-API Implementation

- Latest implementation artifact: `notecode/logs/0628/route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_followthrough_no_api_impl_20260628_013345/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`.
- API send count `0`; product code changed true; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Changed files: `notecode/0506/app/services/editor_output_safety.py`, `notecode/0506/tests/test_editor_output_guard.py`.
- Saved-artifact replay kept body floor `1393/1200`, quality passed, max sentence length became `80`, and human-visible surface gate findings remained `[]`.
- Focused tests passed (`20 passed` plus `14 passed`); `py_compile` passed; changed product-file bloat passed; prompt bloat none.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_one_article_api_validation_after_approval`.
- Non-owner boundaries before the validation: no source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or more than one API send for the validation owner.

## Historical Override 2026-06-28 Post-Market-Explanation Quality Pass Failure Diagnosis

- Latest diagnosis artifact: `notecode/logs/0628/route_v_market_explanation_quality_pass_failure_diagnosis_no_api_20260628_012133/diagnosis.md`.
- Decision: `needs_next_owner`.
- API send count `0`; product code changed false; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Source validation artifact: `notecode/logs/0628/route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_one_article_api_validation_after_approval_20260628_005719/api_validation_summary.md`.
- Preserved validation facts: final body floor `1397/1200`; structural raw `1132/1200` was blocked and guarded/final stayed `1397/1200`; human-visible surface gate passed; source boundary passed; selected excerpt usage `2/2`; over-editing absent.
- Quality failed only on `sentence_too_long`; current replay showed `_split_one_sentence` left the single `137` char suru-event sentence unchanged.
- First confirmed gap: `market_explanation_targeted_rewrite_sentence_split_suru_event_followthrough_gap`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_followthrough_no_api_impl`.
- Non-owner boundaries before the next implementation: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or generated-article patch.

## Historical Override 2026-06-28 Post-Market-Explanation Residual Floor Buffer API Validation

- Latest validation artifact: `notecode/logs/0628/route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_one_article_api_validation_after_approval_20260628_005719/api_validation_summary.md`.
- Decision: `reject_or_inconclusive`.
- API send count `1`; product code changed false; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Same saved `market_explanation` source packet reused.
- Final article generated; H1 exactly one; H2 sections present; final body floor reached `1397/1200`.
- Structural API raw compressed to `1132/1200`, and the floor-loss guard restored the floor-reaching input to `1397/1200`.
- Human-visible surface gate passed with finding codes `[]`; source boundary passed with assigned claim coverage `8/8`; selected excerpt usage passed (`2/2`); over-editing was absent.
- Quality failed only on `sentence_too_long`; sentence split followthrough still has `1` over-limit sentence (`max=137`, limit `90`).
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_quality_pass_failure_diagnosis_no_api`.
- Non-owner boundaries before the next diagnosis: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or immediate generated-article patch.

## Historical Override 2026-06-28 Post-Market-Explanation DraftWriter Residual Floor Buffer No-API Implementation

- Latest implementation artifact: `notecode/logs/0628/route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_no_api_impl_20260628_001740/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`.
- API send count `0`; product code changed true; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Saved-artifact replay against the prior writer-context sanitization validation draft improved DraftWriter-stage body chars from `1096/1200` to `1519/1200`, reaching the `1500` pre-editor buffer target.
- Focused tests passed (`24 passed`), `py_compile` passed, bloat check passed for touched product files, and prompt bloat remained none.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_one_article_api_validation_after_approval`.
- Non-owner boundaries before the next validation: no source refetch, generated article text patch, accepted-status change before a separate acceptance owner, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, or QA threshold / repair-acceptance relaxation.

## Historical Override 2026-06-27 Post-Market-Explanation Body-Floor Diagnosis

- Latest diagnosis artifact: `notecode/logs/0627/route_v_market_explanation_body_floor_reached_failure_diagnosis_no_api_20260627_230000/diagnosis.md`.
- Decision: `needs_next_owner`.
- API send count `0`; product code changed false; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Source validation artifact: `notecode/logs/0627/route_v_market_explanation_writer_context_surface_sanitization_one_article_api_validation_after_approval_20260627_221924/api_validation_summary.md`.
- First below-floor stage: DraftWriter (`1096/1200` body chars excluding headings). Structural API raw later compressed an already-subfloor input to `891/1200`; quality report also remained below floor (`951/1200`).
- Selected excerpts were visible and used (`2/2`), DraftWriter received structured claims (`15`) and the floor/depth contract, and final surface/source/fallback guards passed.
- First confirmed gap: `market_explanation_draft_writer_sanitized_context_residual_floor_miss_gap`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_no_api_impl`.
- Non-owner boundaries before the next implementation: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, structural-editor floor-loss guard change as first owner, selector/source-shape/claim-allocation change, broad prompt/persona tuning, or QA threshold / repair-acceptance relaxation.

## Historical Override 2026-06-27 Post-Market-Explanation Writer-Context Surface Sanitization API Validation

- Latest validation artifact: `notecode/logs/0627/route_v_market_explanation_writer_context_surface_sanitization_one_article_api_validation_after_approval_20260627_221924/api_validation_summary.md`.
- Decision: `reject_or_inconclusive`.
- API send count `1`; product code changed false; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Same saved `market_explanation` source packet reused. H1 exactly one, H2 sections, final human-visible surface gate, selected-source usage, source boundary, and fallback absence passed.
- Body floor failed (`951/1200` in quality report; final stage trace `891/1200` body chars excluding headings). Quality failed on `body_length_below_floor`, `sentence_too_long`, `low_density_bridge_sentence`, and `abstract_navigation_phrase`.
- First confirmed gap: `body_floor_reached`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_body_floor_reached_failure_diagnosis_no_api`.
- Historical non-owner boundaries before that diagnosis: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, broad prompt/persona/QA/selector/source-shape/claim-allocation change, or QA threshold / repair-acceptance relaxation.

## Historical Override 2026-06-27 Post-Market-Explanation Writer-Context Surface Sanitization Implementation

- Latest implementation artifact: `notecode/logs/0627/route_v_market_explanation_writer_context_surface_sanitization_no_api_impl_20260627_214859/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`.
- Product code changed true only in the narrow `market_explanation` writer-context surface sanitization boundary, DraftWriter wiring, followthrough sanitization, and focused tests.
- API send count `0`; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Saved-artifact replay confirms sanitized writer-facing `selected_source_excerpts` and `knowledge_pack` no longer carry surface-gate spaced text, spaced ASCII source surface, or unmatched quote fragments; the no-API replay output passes the final human-visible surface gate.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_writer_context_surface_sanitization_one_article_api_validation_after_approval`.
- Non-owner boundaries before the next validation: no source refetch, generated article text patch, accepted-status change before a separate acceptance owner, raw full source handoff, Route A / writer-only fallback, broad prompt/persona/QA/selector/source-shape/claim-allocation change, or QA threshold / repair-acceptance relaxation.

## Historical Override 2026-06-27 Post-Market-Explanation Human-Visible Surface Diagnosis

- Latest diagnosis artifact: `notecode/logs/0627/route_v_market_explanation_human_visible_surface_repair_diagnosis_no_api_20260627_211533/diagnosis.md`.
- Decision: `diagnosis_completed_needs_next_owner`.
- Product code changed false; accepted status changed false; source refetch false; generated article patch false; API send count `0`.
- The saved `market_explanation` accepted validation article is blocked by the final human-visible surface gate on OCR-spaced source text, a dangling Japanese quote fragment, and duplicate source-title carryover.
- Stage trace confirms DraftWriter/final writer context carries the findings, while structural raw removes them but falls below floor (`1083/1200`); the floor-loss guard correctly restores the floor-reaching draft (`1233/1200`).
- First confirmed gap: `market_explanation_writer_context_surface_sanitization_gap`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_writer_context_surface_sanitization_no_api_impl`.
- Non-owner boundaries before the next implementation: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, broad prompt/persona/QA/selector/source-shape/claim-allocation change, or QA threshold / repair-acceptance relaxation.

## Historical Override 2026-06-27 Post-Human-Visible Surface Gate Implementation

- Latest implementation artifact: `notecode/logs/0627/route_v_human_visible_surface_gate_no_api_impl_20260627_200358/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`.
- Product code changed true only in final human-visible surface gate / quality wiring / pipeline artifact output / focused tests.
- API send count `0`; accepted status changed false; source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Saved-artifact replay passed `comparison_guide` and `company_service_intro`; it blocked `market_explanation`, `announcement`, `daily_activity`, and `case_study`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_human_visible_surface_repair_diagnosis_no_api`.
- Non-owner boundaries before the next diagnosis: no API execution, product-code change, accepted-status change, generated article text patch, source refetch, raw full source handoff, Route A / writer-only fallback, broad prompt/persona/QA/selector/source-shape/claim-allocation change, or QA threshold / repair-acceptance relaxation.

## Historical Override 2026-06-27 Post-Human-Visible Surface Gap Diagnosis

- Latest diagnosis artifact: `notecode/logs/0627/route_v_human_visible_article_surface_gap_diagnosis_no_api_20260627_194037/diagnosis.md`.
- Decision: `diagnosis_completed_needs_next_owner`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Preserved human visual review result: `company_service_intro` and `comparison_guide` are visually acceptable with caveats, while `market_explanation`, `announcement`, `daily_activity`, and `case_study` require follow-up before user-visible release readiness.
- First confirmed gap: `human_visible_surface_gate_missing_after_validation_acceptance_green`.
- Product code changed false; accepted status changed false; source refetch false; generated article patch false; API send count `0`.
- Historical next owner: `route_v_human_visible_surface_gate_no_api_impl`.
- Non-owner boundaries before the next implementation: no API execution, accepted-status change, generated article text patch, source refetch, raw full source handoff, Route A / writer-only fallback, broad prompt/persona/QA/selector/source-shape/claim-allocation change, or QA threshold / repair-acceptance relaxation.

## Historical Override 2026-06-27 Post-Article Set Human Visual Review

- Latest human visual review artifact: `notecode/logs/0627/route_v_article_set_human_visual_review_no_api_20260627_191820/human_visual_review.md`.
- Decision: `human_visual_review_completed_followup_required`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- `company_service_intro` remains visually acceptable with carried caveats and keeps the normal UI user-test article as the human-visible source of truth.
- `comparison_guide` is visually acceptable with inventory caveats.
- `market_explanation`, `announcement`, `daily_activity`, and `case_study` require follow-up before being treated as user-visible release-ready.
- First confirmed gap: `accepted_validation_green_but_human_visible_article_surface_gap`.
- Product code changed false; accepted status changed false; source refetch false; generated article patch false; API send count `0`.
- Historical next owner: `route_v_human_visible_article_surface_gap_diagnosis_no_api`.
- Non-owner boundaries before the next diagnosis: no API execution, product-code change, accepted-status change, generated article text patch, source refetch, raw full source handoff, Route A / writer-only fallback, broad prompt/persona/QA/selector/source-shape/claim-allocation change, or QA threshold / repair-acceptance relaxation.

## Historical Override 2026-06-27 Post-User-Visible Article Set Inventory

- Latest user-visible article set inventory artifact: `notecode/logs/0627/route_v_user_visible_article_set_inventory_no_api_20260627_185826/article_set_inventory.md`.
- Decision: `article_set_inventory_created`.
- All six accepted Route V genres have human-visible article paths recorded.
- `company_service_intro` uses the normal UI user-test article as the human-visible source of truth and remains user visual accepted as a natural kintone introduction.
- `company_service_intro` self-perspective and low-interest reader introduction remain accepted by human visual review.
- Unsupported-claim candidates `2` remain visual-review caveats, not product fix blockers.
- `comparison_guide` / `daily_activity` clean normal UI articles were not generated; this is not a failure. Their accepted validation generated articles are the human-review candidates.
- Accepted genres remain all six intended genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, `company_service_intro`.
- Remaining unaccepted genres: `[]`.
- Product code changed false; accepted status changed false; source refetch false; generated article patch false; API send count `0`.
- Historical next owner: `route_v_article_set_human_visual_review_no_api`.
- Non-owner boundaries before the next human visual review: no API execution, product-code change, accepted-status change, generated article text patch, source refetch, raw full source handoff, Route A / writer-only fallback, or broad prompt/persona/QA/selector/source-shape/claim-allocation change.

## Historical Override 2026-06-27 Post-Human Visual Acceptance Record

- Latest human visual acceptance artifact: `notecode/logs/0627/route_v_company_intro_human_visual_acceptance_record_no_api_20260627_182719/human_visual_acceptance_record.md`.
- Decision: `human_visual_acceptance_recorded`.
- User visual review result: `company_service_intro` article is accepted by user visual review as natural kintone introduction.
- `company_service_intro` self-perspective and low-interest reader introduction are accepted by human visual review.
- Unsupported-claim candidates `2` are carried as visual-review caveats, not product fix blockers.
- `comparison_guide` / `daily_activity` were not generated in this clean normal UI test. This is not a failure; normal UI `CATEGORY_OPTIONS` does not directly expose the Route V IDs, and monkeypatching was avoided.
- Accepted genres remain all six intended genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, `company_service_intro`.
- Remaining unaccepted genres: none.
- Product code changed false; accepted status changed false; source refetch false; generated article patch false; API send count `0`.
- Historical next owner: `route_v_user_visible_article_set_inventory_no_api`.
- Non-owner boundaries before the next inventory: no API execution, product-code change, accepted-status change, generated article text patch, source refetch, raw full source handoff, Route A / writer-only fallback, or broad prompt/persona/QA/selector/source-shape/claim-allocation change.

## Historical Override 2026-06-27 Post-Guarded User-Test

- Latest guarded user-test artifact: `notecode/logs/0627/route_v_guarded_release_user_test_manual_ui_20260627_154813/user_test_decision_summary.md`.
- Decision: `needs_no_api_diagnosis`.
- Human-review article: `notecode/logs/0627/route_v_guarded_release_user_test_manual_ui_20260627_154813/human_review_articles/company_service_intro.md`.
- Review summary: `notecode/logs/0627/route_v_guarded_release_user_test_manual_ui_20260627_154813/review_summaries/company_service_intro_review_summary.md`.
- Normal UI Route V/0506 path, route id, fallback absence, H1/H2, source separation, `company_service_intro` self-perspective, and low-intent reader brief passed.
- Stop condition hit: unsupported-claim candidates were found in the generated `company_service_intro`; release/user visual review did not proceed before the later human visual acceptance record.
- UI service invocations: final run `1`, goal total `3`. OpenAI ledger terminal success rows: final run `6`, goal total `12`. Service-reported `api_send_count` on success: `0`.
- Product code changed false; accepted status changed false; source refetch false; generated article patch false.
- Historical next owner: `route_v_company_intro_unsupported_claim_no_api_diagnosis`.
- Non-owner boundaries before diagnosis evidence: no product-code change, no accepted-status change, no generated article text patch, no raw full source handoff, no Route A / writer-only fallback, no broad prompt/persona/QA/selector/source-shape/claim-allocation change.

## Historical Override 2026-06-27 Post-User-Test Handoff

- Latest user-test handoff artifact: `notecode/logs/0627/route_v_release_user_test_handoff_no_api_20260627_153021/user_test_handoff.md`.
- Source readiness inventory artifact: `notecode/logs/0627/route_v_all_genres_accepted_release_readiness_inventory_no_api_20260627_150315/readiness_inventory.md`.
- Decision: `proceed_to_guarded_user_test`.
- API send count `0`; product code changed false; source refetch false; generated article patch false; accepted status changed false.
- Accepted genres are all six intended genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, `company_service_intro`.
- Remaining unaccepted genres: none.
- Additional no-API blocker before guarded user-test: none.
- Historical next owner: `route_v_guarded_release_user_test_manual_ui`.
- Non-owner boundaries before user-test evidence: no product-code change, no accepted-status change, no broad prompt/persona/QA/selector/source-shape/claim-allocation change, no raw full source handoff, and no Route A / writer-only fallback.

## Historical Override 2026-06-27 Post-Readiness Inventory

- Latest readiness inventory artifact: `notecode/logs/0627/route_v_all_genres_accepted_release_readiness_inventory_no_api_20260627_150315/readiness_inventory.md`.
- Decision: `proceed_to_guarded_release_user_test_handoff`.
- API send count `0`; product code changed false; source refetch false; generated article patch false.
- Accepted genres are all six intended genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, `company_service_intro`.
- Remaining unaccepted genres: none.
- No additional no-API cleanup is required before a guarded user-test handoff; caveats must be carried forward.
- Historical next owner: `route_v_release_user_test_handoff_no_api`.

## Historical Override 2026-06-27 Post-Acceptance Decision

- Latest acceptance artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_live_residual_floor_buffer_acceptance_decision_no_api_20260627_134555/acceptance_decision.md`.
- Source validation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_live_residual_floor_buffer_one_article_api_validation_after_approval_20260627_132914/api_validation_summary.md`.
- Decision: `accepted`; accepted article type: `company_service_intro`.
- Acceptance owner API send count `0`; validation API send count `1`; product code changed false.
- Source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Accepted genres are now all six intended genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, `company_service_intro`.
- Remaining unaccepted genres: none.
- Historical next owner: `route_v_all_genres_accepted_release_readiness_inventory_no_api`.

## Historical Override 2026-06-27 Post-API Validation

- Latest validation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_live_residual_floor_buffer_one_article_api_validation_after_approval_20260627_132914/api_validation_summary.md`.
- Decision: `acceptance_candidate`; API send count `1`; product code changed false.
- The same saved `company_service_intro` source packet was reused and `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2` preflight passed.
- Source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Final article generated, H1 exactly one, H2 sections present, body floor reached (`1401/1400` final), quality passed, selected excerpts used, source/persona/over-editing guards passed.
- Historical next owner: `route_v_company_intro_draft_writer_live_residual_floor_buffer_acceptance_decision_no_api`.
- `company_service_intro` remained unaccepted until the separate acceptance decision artifact was created.

## Historical Override 2026-06-27 Post-Implementation

- Latest implementation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_live_residual_floor_buffer_no_api_impl_20260627_170000/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`; API send count `0`; product code changed true only in DraftWriter company-intro live residual floor buffer scope.
- Preserved first confirmed gap: `company_intro_draft_writer_live_residual_floor_miss_after_no_api_replay_gap`.
- Source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Focused tests passed (`22 passed`); `py_compile` passed; changed-file bloat passed; prompt bloat none.
- Historical next owner: `route_v_company_intro_draft_writer_live_residual_floor_buffer_one_article_api_validation_after_approval`.
- Do not accept `company_service_intro` in this owner.

## Historical Override 2026-06-27 Post-Diagnosis

- Latest diagnosis artifact: `notecode/logs/0627/route_v_company_intro_body_floor_reached_failure_diagnosis_no_api_20260627_160000/diagnosis.md`.
- Source validation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_one_article_api_validation_after_approval_20260627_131500/api_validation_summary.md`.
- Diagnosis decision: `needs_next_owner`; diagnosis API send count `0`; product code changed false; source refetch false; generated article patch false.
- Preserved validation facts: validation decision `reject_or_inconclusive`; validation API send count `1`; DraftWriter `1327/1400`, opening/global/style `1329/1400`, structural API raw/guarded/final `917/1400`, QA `961/1400`; H1 exactly one and H2 sections present; source/persona/selected-excerpt/over-editing/raw-source/fallback guards passed.
- First confirmed gap exactly one: `company_intro_draft_writer_live_residual_floor_miss_after_no_api_replay_gap`.
- Historical next owner: `route_v_company_intro_draft_writer_live_residual_floor_buffer_no_api_impl`.
- Do not accept `company_service_intro` in this owner.

## Historical Override 2026-06-27 Post-API Validation

- Latest validation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_one_article_api_validation_after_approval_20260627_131500/api_validation_summary.md`.
- Decision: `reject_or_inconclusive`; API send count `1`; product code changed false; source refetch false; generated article patch false.
- Body floor failed after residual followthrough: DraftWriter `1327/1400`, opening/global/style `1329/1400`, structural API raw/guarded/final `917/1400`, QA `961/1400`.
- Quality failed on `body_length_below_floor`; first diagnosis owner at the time was `route_v_company_intro_body_floor_reached_failure_diagnosis_no_api`, now completed.

## Historical Override 2026-06-27 Post-Implementation

- Latest implementation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_no_api_impl_20260627_104857/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`; API send count `0`; product code changed true only in DraftWriter residual followthrough scope.
- Source refetch false; generated article patch false; raw full source_documents/source_packets/source_cards handoff false; Route A / writer-only fallback false.
- First confirmed gap preserved exactly: `company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough`.
- Saved-artifact replay reached body floor: `1155/1400` -> `1409/1400`.
- Historical next owner: `route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_one_article_api_validation_after_approval`.
- `company_service_intro` remained unaccepted.

## Historical Override 2026-06-27

- Latest validation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_selected_excerpt_floor_followthrough_one_article_api_validation_after_approval_20260627_091448/api_validation_summary.md`.
- Source implementation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_selected_excerpt_floor_followthrough_no_api_impl_20260627_010000/implementation_summary.md`.
- Latest diagnosis artifact: `notecode/logs/0627/route_v_company_intro_body_floor_reached_failure_diagnosis_no_api_20260627_092734/diagnosis.md`.
- Source validation artifact: `notecode/logs/0626/route_v_company_intro_front_back_editor_persona_contract_one_article_api_validation_retry_after_api_520_20260626_231500/api_validation_summary.md`.
- Decision: `needs_next_owner`; diagnosis API send count `0`; product code changed false; source refetch false; generated article patch false.
- The same saved `company_service_intro` source packet was reused and `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2` preflight passed.
- Final article generated, H1 exactly one, H2 sections present, source/persona/selected-excerpt/over-editing/raw-source/fallback guards passed.
- Body floor failed after selected-excerpt followthrough: DraftWriter `1155/1400`, opening/global/style `1157/1400`, structural API raw/guarded/final `331/1400`, QA `375/1400`.
- Quality failed on `body_length_below_floor` and `ending_bucket_monotony`.
- First confirmed gap: `company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough`; first below-floor stage `draft`; largest floor loss stage `structural_api_raw`.
- Accepted genres are now `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, and `announcement`.
- Remaining unaccepted genre: `company_service_intro`.
- Historical next owner before residual implementation: `route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_no_api_impl`.

## Historical Override 2026-06-26

- Latest acceptance artifact: `notecode/logs/0626/route_v_announcement_draft_writer_selected_excerpt_floor_followthrough_acceptance_decision_no_api_20260626_202716/acceptance_decision.md`.
- Source validation artifact: `notecode/logs/0626/route_v_announcement_draft_writer_selected_excerpt_floor_followthrough_one_article_api_validation_after_approval_20260626_194056/api_validation_summary.md`.
- Decision: `accepted`; acceptance owner API send count `0`; product code changed false; source refetch false; generated article patch false.
- Accepted evidence: announcement final article generated, H1 exactly one, H2 sections present, body floor reached `958/900`, quality passed, source/persona/selected-excerpt/over-editing reviews passed.
- Structural editor floor-loss guard was accepted as protective: floor-reaching input `958/900`, structural API raw `671/900`, guarded/final `958/900`.
- Gates passed: H1 exactly one, H2 sections, announcement self-perspective `当社`, source boundary, selected excerpt / confirmed claim usage, raw full source handoff false, Route A false, writer-only false, focused tests, `py_compile`, and bloat check.
- Accepted genres are now `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, and `announcement`.
- Remaining unaccepted genre: `company_service_intro`.
- Latest company-introduction API validation artifact: `notecode/logs/0626/route_v_company_intro_front_back_editor_persona_contract_one_article_api_validation_retry_after_api_520_20260626_231500/api_validation_summary.md`.
- Decision: `reject_or_inconclusive`; API send count `1`; product code changed false; source refetch false; generated article patch false. Final article generated, H1 exactly one, H2 section headings, source/persona/selected-excerpt/over-editing/raw-source/fallback guards passed, but body floor failed (`718/1400`) and quality failed only on `body_length_below_floor`.
- Historical next owner at the time: `route_v_company_intro_body_floor_reached_failure_diagnosis_no_api`.

## Task

Build a Japanese blog generation pipeline that uses structured intermediate data to produce natural, source-grounded Japanese blog articles from multiple sources.

## MVP Objective

Implement a pipeline that can:

1. Accept multiple input sources.
2. Extract usable source text with source spans.
3. Generate one source card per source.
4. Integrate source cards into an article knowledge pack.
5. Build an article brief from UI settings and the knowledge pack.
6. Generate a draft from the brief and confirmed claims.
7. Edit the draft without changing facts.
8. Run Japanese quality checks.
9. Apply targeted rewrites only to flagged issues.
10. Return final article text, QA score, and issues.

## Functional Requirements

### Source Input

Supported source types:

- URL
- PDF
- Word file
- manual text

Each source must receive a stable `source_id`.

### Text Extraction

- URL extraction should remove navigation, footer, ads, and boilerplate where possible.
- URL extraction should prefer deterministic public HTML extraction with `httpx` and Beautiful Soup before GPT/web-search fallback.
- URL extraction must respect robots.txt, public access boundaries, and platform restrictions.
- note and Hatena Blog are initial output-style targets; do not crawl restricted pages, login pages, internal APIs, search pages, or archive pages.
- PDF extraction should preserve page/source span information.
- Word extraction should preserve headings, paragraphs, and tables where possible.
- Manual text should still receive source metadata and source spans.

### Source Card Extraction

Each source card must include:

- `source_id`
- `source_type`
- `title`
- `published_or_updated_at`
- `reliability`
- `main_topics`
- `facts`
- `quotes_or_phrases`
- `warnings`

Rules:

- Do not infer missing facts.
- Preserve numbers, dates, and proper nouns.
- Put old, ambiguous, or risky information into `warnings`.

### Knowledge Pack Integration

The knowledge pack must include:

- confirmed facts with `claim_id`
- supporting source fact IDs
- confidence
- conflicts
- deduped themes
- do-not-infer rules

Rules:

- Merge equivalent facts.
- Detect source conflicts.
- Prefer newer official sources when clearly available.
- Separate usable claims from risky or unsupported information.

### Article Brief

The article brief must include:

- article category
- genre-specific writer role
- viewpoint mode
- target reader
- article goal
- narrator / first person
- persona and tone
- section structure
- heading purpose
- assigned claim IDs per section
- main subject and discourse rules per section
- style rules and forbidden/risky phrases
- config references
- persona references

Rules:

- The draft writer must follow the brief.
- Do not reuse the same claim ID across multiple headings unless explicitly allowed.
- First person must be explicit.
- Self-perspective is the default viewpoint. Do not mix third-party terms such as `同社` or `同サービス` unless third-party mode is explicitly selected.
- Company/service/product introduction should default to `私たち`; formal announcements may use `当社`.
- Genre, persona, viewpoint, and QA defaults should be loaded from config/persona files, not hard-coded into the prompt.

### Draft, Edit, Check, Rewrite

- `draft_writer` produces the first draft from the brief and confirmed claims only.
- `style_editor` improves Japanese style without changing facts.
- `japanese_quality_checker` returns JSON with `pass`, `score`, `issues`, and `rewrite_needed`.
- `targeted_rewriter` changes only the flagged parts and then triggers another quality check.

## Non-Functional Requirements

- Keep every agent input and output logged.
- Save `article_knowledge_pack` and `article_brief`.
- Preserve traceability from final article sections back to `claim_id`.
- Do not auto-publish medical, legal, financial, hiring-condition, price, or high-risk content.
- Build evals before claiming quality acceptance.
- Keep config, personas, prompt templates, and runtime code separate.
- Prevent module bloat and prompt bloat according to `docs/CONFIG_AND_PERSONA_POLICY.md`.
- Keep stylometry deterministic and LLM-free.

## Acceptance Criteria

### MVP Acceptance

- Multiple source records can enter the pipeline.
- Source cards are generated.
- A knowledge pack is generated.
- UI settings create an article brief.
- Draft -> style edit -> quality check -> targeted rewrite can run.
- Final article text is returned.
- QA score and issues are visible.

### Quality Acceptance

- First-person inconsistency is detected and corrected.
- Obvious unsupported claims are detected.
- Subject ambiguity from Japanese omission is detected.
- AI-like phrases such as `いかがでしたでしょうか` are detected.
- GPT-like frequent words such as `効く` and `第一歩` are detected when repeated or generic.
- Uniform line breaks, paragraph rhythm monotony, and ending-bucket monotony are detected.
- Third-party viewpoint leakage and narrator mixing are detected.
- Stylometry issue candidates are available to the Japanese quality checker.
- Reuse of the same claim across headings is reduced or flagged.
- Category-specific style differences are visible.

## Development Order

Follow `docs/GOAL_PLAN.md` for executable phase and slice order.

High-level order:

1. Contracts.
2. Deterministic foundation.
3. Source acquisition.
4. LLM pipeline.
5. NiceGUI MVP.
6. Quality evaluation.
7. Tuning and hardening.

## Historical Narrow Owner

Phase 1 Contracts through Phase 7 Tuning and Hardening are implemented and tested.

Use `docs/GOAL_PLAN.md` as the exact execution plan for later phases.

The completed execution boundary covered:

- Phase 1 Contracts
- Phase 2 Deterministic Foundation
- Phase 3 Source Acquisition
- Phase 3.5 / Phase 4 preprocessing
- Phase 4 LLM Pipeline
- Phase 5 NiceGUI MVP
- Phase 6 Quality Evaluation
- Phase 7 Tuning and Hardening

Stop state: Phase 7 validation passed. The next work is quality adjustment based on the Phase 6/7 reports. Do not tune multiple owners in one window.
