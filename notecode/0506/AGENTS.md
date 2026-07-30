# AGENTS.md

## Current State 2026-06-28 Post-Manual UI Article Type Image Validation

- Latest validation artifact: `notecode/logs/0628/rv_ui_img_20260628_180205/validation_summary.json`.
- Decision: `needs_review`; UI reachability passed; all six article types generated; all six article types produced both text and no-text image variants.
- Service invocation counts in this owner: article generation invocations `12`; image generation invocations `12`; successful image variants `24`; Route V/0506 OpenAI terminal send count `52`.
- Accepted/user-visible readiness in this owner: `comparison_guide`, `announcement`, `daily_activity`, and `case_study` passed. `company_service_intro` and `market_explanation` remain `needs_review` after allowed regeneration attempts.
- First confirmed gap: `company_service_intro:article`; final quality issues include `model_frequent_word` and `duplication`. Secondary gap: `market_explanation:article`; final quality issues include `model_frequent_word` and `ending_bucket_monotony`.
- Product code changed `false`; source refetch `false`; generated article patch `false`; raw full source handoff `false`; Route A fallback `false`; writer-only fallback `false`; QA threshold relaxed `false`; repair acceptance relaxed `false`; prompt bloat `none`; module bloat `none`.
- Current next owner: `route_v_first_gap_review`.
- Allowed next scope: diagnose the saved artifacts for the first confirmed `company_service_intro` article quality failure and identify one narrow owner before any further API execution or implementation.
- Non-owner boundaries before/within the next owner: no source refetch, generated article patch, raw full source handoff, Route A / writer-only fallback, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or broad module/prompt expansion.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-28 Post-Guarded User Evaluation Artifact

- Latest user evaluation artifact: `notecode/logs/0628/route_v_guarded_user_evaluation_artifact_no_api_20260628_134325/review_index.md`. `copy_manifest.json` has all six article hashes matching their source artifacts.
- Source inventory artifact: `notecode/logs/0628/route_v_article_set_readiness_inventory_no_api_20260628_134223/article_set_readiness_inventory.md`.
- Latest acceptance artifact: `notecode/logs/0628/route_v_case_study_local_surface_sanitization_acceptance_decision_no_api_20260628_133650/acceptance_decision.md`.
- Source validation artifact: `notecode/logs/0628/route_v_case_study_local_surface_sanitization_one_article_api_validation_after_approval_20260628_132909/api_validation_summary.md`.
- Gate enablement artifact: `notecode/logs/0628/route_v_human_visible_surface_gate_case_study_enablement_no_api_impl_20260628_133549/implementation_summary.md`.
- Decision: `user_evaluation_artifact_ready`.
- Evaluation artifact owner API send count `0`; copied article count `6`; all copy hashes match; upstream case_study API send count `1`; product code changed in evaluation owner `false`; source refetch `false`; generated article patch `false`; raw full source handoff `false`; Route A / writer-only fallback `false`.
- Runtime brief human-visible surface gate recheck after enablement: `pass=true`, `enabled_for_brief=true`, findings `[]`.
- Gate enablement changed only `notecode/0506/app/services/human_visible_surface_gate.py` and `notecode/0506/tests/test_human_visible_surface_gate.py`; broad non-hardening regression passed `205 passed`.
- Historical next owner: `route_v_user_evaluation_waiting_for_manual_review`.
- Allowed next scope: wait for manual user review of the bundled article set; do not run API or change product code before the user gives evaluation feedback.
- Non-owner boundaries before/within the next owner: no API execution, source refetch, generated article patch, accepted-status mutation, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or product-code edits.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-28 Post-Case-Study Local Surface Sanitization Implementation

- Latest implementation artifact: `notecode/logs/0628/route_v_case_study_local_surface_sanitization_no_api_impl_20260628_132141/implementation_summary.md`.
- Source diagnosis artifact: `notecode/logs/0628/route_v_case_study_human_visible_surface_repair_diagnosis_no_api_20260628_131533/diagnosis.md`.
- Decision: `implementation_completed_needs_one_article_api_validation_after_approval`.
- API send count `0`; product code changed `true`; accepted status changed `false`; source refetch `false`; generated article patch `false`; raw full source handoff `false`; Route A / writer-only fallback `false`.
- Changed files: `notecode/0506/app/services/draft_followthrough.py`, `notecode/0506/app/agents/draft_writer.py`, `notecode/0506/tests/test_draft_writer.py`.
- Saved-artifact replay after sanitizer: human-visible surface gate passed with finding codes `[]`; H1 count `1`; H2 count `3`; body chars excluding headings `576`.
- Tests passed: `22 passed`, `31 passed`, `py_compile`, and `205 passed` with `tests --ignore=tests/test_phase7_hardening.py`.
- Historical next owner: `route_v_case_study_local_surface_sanitization_one_article_api_validation_after_approval`.
- Allowed next scope: run one guarded same-source `case_study` API validation after approval/guarded continuation; reuse the saved source packet and keep API send count to one for this owner.
- Non-owner boundaries before/within the next owner: no source refetch, generated article patch, accepted-status mutation, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or additional product-code edits as part of validation.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-28 Post-Case-Study Human-Visible Surface Diagnosis

- Latest diagnosis artifact: `notecode/logs/0628/route_v_case_study_human_visible_surface_repair_diagnosis_no_api_20260628_131533/diagnosis.md`.
- Source gate replay: `notecode/logs/0627/route_v_human_visible_surface_gate_no_api_impl_20260627_200358/surface_gate_replay_report.json`.
- Source validation artifact: `notecode/logs/0625/route_v_case_study_structural_editor_knowledge_pack_payload_contract_one_article_api_validation_after_approval_20260625_152645/api_validation_summary.md`.
- Decision: `diagnosis_completed_needs_next_owner`.
- API send count `0`; product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`; raw full source handoff `false`; Route A / writer-only fallback `false`.
- Human-visible blocker: `generic_local_opening`, `unrelated_local_cta`, and `dangling_japanese_quote_fragment`.
- First confirmed gap: `case_study_local_surface_sanitization_gap`.
- Historical next owner: `route_v_case_study_local_surface_sanitization_no_api_impl`.
- Allowed next scope: implement a narrow case-study local surface sanitizer/followthrough that removes the confirmed local opening, unrelated local CTA, and dangling quote source-fragment from case-study drafts/replays while preserving H1/H2, source grounding, narrator boundary, and quality gates.
- Non-owner boundaries before/within the next owner: no API execution, source refetch, generated article text patch, accepted-status mutation, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or broad phrase-list growth beyond the confirmed local surface defects.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-28 Post-Daily-Activity User Tolerance Record

- Latest user tolerance artifact: `notecode/logs/0628/route_v_daily_activity_user_tolerance_record_no_api_20260628_130737/user_tolerance_record.md`.
- Source validation artifact: `notecode/logs/0628/route_v_daily_activity_local_surface_sanitization_one_article_api_validation_after_approval_20260628_123856/api_validation_summary.md`.
- Decision: `user_visible_acceptable_with_caveats`.
- API send count `0` for this owner; source validation API send count `1`; retry count `0`; product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`; raw full source handoff `false`; Route A / writer-only fallback `false`.
- User review: the latest `daily_activity` article is almost acceptable. The later half still feels somewhat third-party, but is barely acceptable.
- Preserved caveats: `duplicate_long_sentence`, `model_frequent_word`, `duplication`, no `私たち` in the final article, and slight third-party feel in the later half.
- This is a user-visible tolerance record, not a code fix, generated-output patch, threshold relaxation, or clean mechanical acceptance.
- Historical next owner: `route_v_case_study_human_visible_surface_repair_diagnosis_no_api`.
- Allowed next scope: diagnose the saved accepted `case_study` candidate and human-visible surface gate blocker from existing artifacts only; identify the first responsible owner for `generic_local_opening`, `unrelated_local_cta`, and `dangling_japanese_quote_fragment`.
- Non-owner boundaries before/within the next owner: no API execution, source refetch, generated article text patch, accepted-status mutation, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or symptom-only phrase replacement.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-28 Post-Daily-Activity Local Surface Sanitization API Validation

- Latest validation artifact: `notecode/logs/0628/route_v_daily_activity_local_surface_sanitization_one_article_api_validation_after_approval_20260628_123856/api_validation_summary.md`.
- Decision: `reject_or_inconclusive`; API send count `1`; retry count `0`; product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`.
- Final article generated with H1 exactly one, H2 sections present, and final body floor reached `1234/1200`.
- Failed gates: human-visible surface gate `pass=false` with `duplicate_long_sentence`; quality pass `false` with `model_frequent_word` and `duplication`; self-perspective consistency `false` because the final article contains no `私たち`.

## Historical State 2026-06-28 Post-Market-Explanation Acceptance Decision

- Latest acceptance artifact: `notecode/logs/0628/route_v_market_explanation_acceptance_decision_no_api_20260628_094825/acceptance_decision.md`.
- Source validation artifact: `notecode/logs/0628/route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_one_article_api_validation_after_approval_20260628_014124/api_validation_summary.md`.
- Decision: `accepted`; `market_explanation` can be treated as accepted / user-visible release-ready for the latest same-source validation chain.
- Acceptance owner API send count `0`; source validation API send count `1`; product code changed `false`; source refetch `false`; generated article patch `false`.
- Raw full source handoff / Route A fallback / writer-only fallback remained absent.
- Preserved validation facts: body floor draft/opening/global/style `1397/1200`; structural API raw `932/1200`; structural API guarded `1397/1200`; final `1393/1200`; quality issues `[]`; max sentence length `81`; over-limit count `0`; human-visible surface gate findings `[]`.
- Source boundary, selected excerpt usage, structural floor-loss guard, prompt bloat, and algorithm bloat passed.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_announcement_human_visible_surface_repair_diagnosis_no_api`.
- Non-owner boundaries before the next owner: no API execution, source refetch, generated article text patch, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or product-code change as the first move.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-28 Post-Market-Explanation Targeted Rewrite Sentence Split Suru-Event API Validation

- Latest validation artifact: `notecode/logs/0628/route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_one_article_api_validation_after_approval_20260628_014124/api_validation_summary.md`.
- Decision: `acceptance_candidate`.
- API send count `1` for this validation owner; product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`.
- Raw full source handoff / Route A fallback / writer-only fallback remained absent.
- Same saved `market_explanation` source packet was reused.
- Stage trace body floor: draft/opening/global/style `1397/1200`; structural API raw `932/1200`; structural API guarded `1397/1200`; final `1393/1200`.
- Quality passed with issues `[]`; sentence split followthrough max sentence length `81`, over-limit count `0`.
- Human-visible surface gate passed with findings `[]`; source boundary and selected excerpt usage passed; structural floor-loss guard blocked harmful compression.
- Prompt bloat and algorithm bloat checks passed; no broad prompt/persona tuning was used.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_acceptance_decision_no_api`.
- Non-owner boundaries before the next owner: no API execution, source refetch, generated article text patch, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or accepted-status mutation without an explicit acceptance decision record.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-28 Post-Market-Explanation Targeted Rewrite Sentence Split Suru-Event No-API Implementation

- Latest implementation artifact: `notecode/logs/0628/route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_followthrough_no_api_impl_20260628_013345/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`.
- API send count `0`; product code changed `true`; accepted status changed `false`; source refetch `false`; generated article patch `false`.
- Changed files: `notecode/0506/app/services/editor_output_safety.py`, `notecode/0506/tests/test_editor_output_guard.py`.
- Implementation: deterministic targeted rewrite can close a long split segment ending in `することにより` as `します。`, then continue existing recursive sentence splitting.
- Saved-artifact replay against the `market_explanation` residual floor buffer validation changed the article, kept body floor `1393/1200`, removed `sentence_too_long`, reached quality pass, max sentence length `80`, and kept human-visible surface gate findings `[]`.
- Focused tests passed (`20 passed` plus `14 passed` additional pipeline/quality focused tests); `py_compile` passed; changed product-file bloat passed (`editor_output_safety.py` 249/300); prompt bloat none.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_one_article_api_validation_after_approval`.
- Non-owner boundaries before the validation: no source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or more than one API send for the validation owner.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-28 Post-Market-Explanation Quality Pass Failure Diagnosis

- Latest diagnosis artifact: `notecode/logs/0628/route_v_market_explanation_quality_pass_failure_diagnosis_no_api_20260628_012133/diagnosis.md`.
- Decision: `needs_next_owner`.
- API send count `0`; product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`.
- Source validation artifact: `notecode/logs/0628/route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_one_article_api_validation_after_approval_20260628_005719/api_validation_summary.md`.
- Preserved validation facts: final body floor `1397/1200`; structural raw `1132/1200` was blocked and guarded/final stayed `1397/1200`; human-visible surface gate passed; source boundary passed; selected excerpt usage `2/2`; over-editing absent.
- Quality failed only on `sentence_too_long`; current replay showed `_split_one_sentence` left the single `137` char suru-event sentence unchanged.
- First confirmed gap: `market_explanation_targeted_rewrite_sentence_split_suru_event_followthrough_gap`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_targeted_rewrite_sentence_split_suru_event_followthrough_no_api_impl`.
- Non-owner boundaries before the next implementation: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or generated-article patch.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-28 Post-Market-Explanation Residual Floor Buffer API Validation

- Latest validation artifact: `notecode/logs/0628/route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_one_article_api_validation_after_approval_20260628_005719/api_validation_summary.md`.
- Decision: `reject_or_inconclusive`.
- API send count `1`; product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`.
- Raw full source handoff / Route A fallback / writer-only fallback remained absent.
- Same saved `market_explanation` source packet was reused: `notecode/logs/0621/same_source_no_overcompression_tone_fixed/artifacts/market_explanation/market_explanation_20260621_122946_attempt1/source_packets.json`.
- Body floor passed after editors: final body chars excluding headings `1397/1200`; structural API raw compressed to `1132/1200`, and the floor-loss guard restored the floor-reaching input to `1397/1200`.
- Quality failed only on `sentence_too_long`; sentence split followthrough still has `1` over-limit sentence (`max=137`, limit `90`).
- Human-visible surface gate passed with finding codes `[]`.
- Source boundary passed: compact knowledge visible, assigned claim coverage `8/8`, unsupported ranking/best/numeric claims `[]`.
- Selected excerpt usage passed (`2/2`); structural compression guard passed; over-editing absent.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_quality_pass_failure_diagnosis_no_api`.
- Non-owner boundaries before the next diagnosis: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, QA threshold / repair-acceptance relaxation, or immediate generated-article patch.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-28 Post-Market-Explanation DraftWriter Residual Floor Buffer No-API Implementation

- Latest implementation artifact: `notecode/logs/0628/route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_no_api_impl_20260628_001740/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`.
- API send count `0`; product code changed `true`; accepted status changed `false`; source refetch `false`; generated article patch `false`.
- Raw full source handoff / Route A fallback / writer-only fallback remained absent.
- Implementation scope: narrow `market_explanation` DraftWriter sanitized-context residual floor buffer. `DraftWriter` passes sanitized `knowledge_pack` to the market-explanation followthrough, and owner-specific followthrough lives in `app/services/market_explanation_followthrough.py` to avoid module bloat.
- Saved-artifact replay: `1096/1200` -> `1519/1200` body chars excluding headings, reaching the `1500` pre-editor buffer target with `+319` chars over floor.
- Focused tests passed (`24 passed`), `py_compile` passed, and touched product-file bloat passed (`draft_writer.py` 270, `draft_followthrough.py` 68, `market_explanation_followthrough.py` 250).
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_one_article_api_validation_after_approval`.
- Non-owner boundaries before the next validation: no source refetch, generated article text patch, accepted-status change before a separate acceptance owner, raw full source handoff, Route A / writer-only fallback, selector/source-shape/claim-allocation change, broad prompt/persona tuning, or QA threshold / repair-acceptance relaxation.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-27 Post-Market-Explanation Body-Floor Diagnosis

- Latest diagnosis artifact: `notecode/logs/0627/route_v_market_explanation_body_floor_reached_failure_diagnosis_no_api_20260627_230000/diagnosis.md`.
- Decision: `needs_next_owner`.
- API send count `0`; product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`.
- Source validation artifact: `notecode/logs/0627/route_v_market_explanation_writer_context_surface_sanitization_one_article_api_validation_after_approval_20260627_221924/api_validation_summary.md`.
- First below-floor stage: DraftWriter (`1096/1200` body chars excluding headings). Structural API raw later compressed an already-subfloor input to `891/1200`; quality report also remained below floor (`951/1200`).
- Selected excerpts were visible and used (`2/2`), DraftWriter received structured claims (`15`) and the floor/depth contract, and raw full source handoff / Route A fallback / writer-only fallback remained absent.
- First confirmed gap: `market_explanation_draft_writer_sanitized_context_residual_floor_miss_gap`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_no_api_impl`.
- Non-owner boundaries before the next implementation: no API execution, source refetch, generated article text patch, accepted-status change, raw full source handoff, Route A / writer-only fallback, structural-editor floor-loss guard change as first owner, selector/source-shape/claim-allocation change, broad prompt/persona tuning, or QA threshold / repair-acceptance relaxation.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-27 Post-Market-Explanation Writer-Context Surface Sanitization API Validation

- Latest validation artifact: `notecode/logs/0627/route_v_market_explanation_writer_context_surface_sanitization_one_article_api_validation_after_approval_20260627_221924/api_validation_summary.md`.
- Decision: `reject_or_inconclusive`.
- API send count `1`; product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`.
- The same saved `market_explanation` source packet was reused; final article generated; H1 exactly one; H2 sections present; selected-source usage, source boundary, raw-source handoff absence, Route A fallback absence, and writer-only fallback absence passed.
- Final human-visible surface gate passed with finding codes `[]`.
- Body floor failed (`951/1200` in quality report; final stage trace `891/1200` body chars excluding headings), and quality failed on `body_length_below_floor`, `sentence_too_long`, `low_density_bridge_sentence`, and `abstract_navigation_phrase`.
- First confirmed gap: `body_floor_reached`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_body_floor_reached_failure_diagnosis_no_api`.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-27 Post-Market-Explanation Writer-Context Surface Sanitization Implementation

- Latest implementation artifact: `notecode/logs/0627/route_v_market_explanation_writer_context_surface_sanitization_no_api_impl_20260627_214859/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`.
- Product code changed `true`, limited to the narrow `market_explanation` writer-context surface sanitization boundary, DraftWriter wiring, followthrough sanitization, and focused tests.
- API send count `0`; accepted status changed `false`; source refetch `false`; generated article patch `false`.
- Saved-artifact replay sanitizes writer-facing `selected_source_excerpts` and `knowledge_pack` so OCR-spaced source text, spaced ASCII source surface, and unmatched Japanese quote fragments are not handed to DraftWriter/followthrough as reader-facing prose.
- Replay output from sanitized context passed the final human-visible surface gate with finding codes `[]`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_writer_context_surface_sanitization_one_article_api_validation_after_approval`.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-27 Post-Market-Explanation Human-Visible Surface Diagnosis

- Latest diagnosis artifact: `notecode/logs/0627/route_v_market_explanation_human_visible_surface_repair_diagnosis_no_api_20260627_211533/diagnosis.md`.
- Decision: `diagnosis_completed_needs_next_owner`.
- Product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`; API send count `0`.
- `market_explanation` saved accepted validation article is blocked by the final human-visible surface gate on `ocr_spaced_source_text`, `dangling_japanese_quote_fragment`, and `duplicate_long_sentence`.
- The same findings originate in the DraftWriter-stage saved artifact; `structural_editor_api_raw.md` removes them but falls below floor (`1083/1200`), so the floor-loss guard correctly restores the floor-reaching draft (`1233/1200`).
- First confirmed gap: `market_explanation_writer_context_surface_sanitization_gap`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_writer_context_surface_sanitization_no_api_impl`.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-27 Post-Human-Visible Surface Gate Implementation

- Latest implementation artifact: `notecode/logs/0627/route_v_human_visible_surface_gate_no_api_impl_20260627_200358/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`.
- Product code changed `true`, limited to the final human-visible surface gate, final quality wiring, pipeline artifact output, and focused tests.
- API send count `0`; accepted status changed `false`; source refetch `false`; generated article patch `false`.
- The deterministic final Markdown gate now blocks local-renderer fingerprints, dangling Japanese quote fragments, OCR-spaced source text, duplicate long source-title/sentence carryover, and unrelated local CTA carryover before Route V artifacts can be treated as user-visible release-ready.
- Saved-artifact replay passed `comparison_guide` and `company_service_intro`; it blocked `market_explanation`, `announcement`, `daily_activity`, and `case_study`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Historical next owner: `route_v_market_explanation_human_visible_surface_repair_diagnosis_no_api`.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-27 Post-Human-Visible Surface Gap Diagnosis

- Latest diagnosis artifact: `notecode/logs/0627/route_v_human_visible_article_surface_gap_diagnosis_no_api_20260627_194037/diagnosis.md`.
- Decision: `diagnosis_completed_needs_next_owner`.
- Product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`; API send count `0`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- Diagnosis preserved the article set human visual review result: `company_service_intro` and `comparison_guide` are visually acceptable with caveats, while `market_explanation`, `announcement`, `daily_activity`, and `case_study` require follow-up before user-visible release readiness.
- First confirmed gap: `human_visible_surface_gate_missing_after_validation_acceptance_green`.
- Historical next owner: `route_v_human_visible_surface_gate_no_api_impl`.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-27 Post-Article Set Human Visual Review

- Latest human visual review artifact: `notecode/logs/0627/route_v_article_set_human_visual_review_no_api_20260627_191820/human_visual_review.md`.
- Decision: `human_visual_review_completed_followup_required`.
- Product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`; API send count `0`.
- All six accepted Route V genres remain accepted; remaining unaccepted genres remain `[]`.
- `company_service_intro` remains visually acceptable with carried caveats and keeps the normal UI user-test article as the human-visible source of truth.
- `comparison_guide` is visually acceptable with inventory caveats.
- `market_explanation`, `announcement`, `daily_activity`, and `case_study` require follow-up before being treated as user-visible release-ready because the saved accepted artifacts still show source-fragment leakage, duplication, unrelated CTA carryover, or formatting artifacts.
- First confirmed gap: `accepted_validation_green_but_human_visible_article_surface_gap`.
- Historical next owner: `route_v_human_visible_article_surface_gap_diagnosis_no_api`.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-27 Post-User-Visible Article Set Inventory

- Latest user-visible article set inventory artifact: `notecode/logs/0627/route_v_user_visible_article_set_inventory_no_api_20260627_185826/article_set_inventory.md`.
- Decision: `article_set_inventory_created`.
- Product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`; API send count `0`.
- All six accepted Route V genres now have human-visible article paths recorded.
- `company_service_intro` uses the normal UI user-test article as the human-visible source of truth: `notecode/logs/0627/route_v_guarded_release_user_test_manual_ui_20260627_154813/human_review_articles/company_service_intro.md`.
- `company_service_intro` remains user visual accepted as a natural kintone introduction; its self-perspective and low-interest reader introduction remain accepted.
- The two unsupported-claim candidates are preserved as visual-review caveats, not product fix blockers.
- `comparison_guide` and `daily_activity` clean normal UI articles were not generated; this is not a failure. Their accepted validation generated articles are the human-review candidates.
- Accepted genres remain all six intended genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, `company_service_intro`.
- Remaining unaccepted genres: `[]`.
- Historical next owner: `route_v_article_set_human_visual_review_no_api`.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-27 Post-Human Visual Acceptance Record Override

- Latest human visual acceptance artifact: `notecode/logs/0627/route_v_company_intro_human_visual_acceptance_record_no_api_20260627_182719/human_visual_acceptance_record.md`.
- Decision: `human_visual_acceptance_recorded`.
- User visual review result: `company_service_intro` article is accepted by user visual review as natural kintone introduction.
- `company_service_intro` self-perspective and low-interest reader introduction are accepted by human visual review.
- Product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`; API send count `0`.
- The two unsupported-claim candidates from the guarded user-test are preserved as visual-review caveats, not product fix blockers.
- `comparison_guide` and `daily_activity` were not generated in the clean normal UI test. This is not a failure: normal UI `CATEGORY_OPTIONS` does not directly expose their Route V IDs, and monkeypatching was avoided.
- Accepted genres remain all six intended genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, `company_service_intro`.
- Remaining unaccepted genres: none.
- Historical next owner: `route_v_user_visible_article_set_inventory_no_api`.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-27 Post-Guarded User-Test Override

- Latest guarded user-test artifact: `notecode/logs/0627/route_v_guarded_release_user_test_manual_ui_20260627_154813/user_test_decision_summary.md`.
- Decision: `needs_no_api_diagnosis`.
- Human-review article: `notecode/logs/0627/route_v_guarded_release_user_test_manual_ui_20260627_154813/human_review_articles/company_service_intro.md`.
- Review summary: `notecode/logs/0627/route_v_guarded_release_user_test_manual_ui_20260627_154813/review_summaries/company_service_intro_review_summary.md`.
- Product code changed `false`; accepted status changed `false`; source refetch `false`; generated article patch `false`.
- Normal UI service path invoked Route V/0506 with route id `route_v_0506_structured_blog_v1`; Route A / fallback / writer-only flags were all false.
- H1 exactly one and H2 sections were present; `company_service_intro` kept self-perspective with narrator `私たち` and a low-intent reader brief.
- Raw full source handoff was not observed in nested 0506 artifacts; final-stage artifacts used `article_brief`, `article_knowledge_pack`, and `selected_source_excerpts`.
- Stop condition hit: two unsupported-claim candidates were found in `company_service_intro`, so release/user visual review was not ready before the later human visual acceptance record.
- UI service invocations: final run `1`, goal total `3`. OpenAI ledger terminal success rows: final run `6`, goal total `12`. Service-reported `api_send_count` on success: `0`.
- `comparison_guide` and `daily_activity` were not generated through normal UI in this slice because the current `route_v_generation_service.CATEGORY_OPTIONS` path does not directly expose their Route V IDs without a monkeypatch.
- Historical next owner: `route_v_company_intro_unsupported_claim_no_api_diagnosis`.
- Older next-owner references later in this file are historical unless repeated by `TASK.md` and `PROGRESS.md`.

## Historical State 2026-06-27 Post-User-Test Handoff Override

- Latest user-test handoff artifact: `notecode/logs/0627/route_v_release_user_test_handoff_no_api_20260627_153021/user_test_handoff.md`.
- Source readiness inventory artifact: `notecode/logs/0627/route_v_all_genres_accepted_release_readiness_inventory_no_api_20260627_150315/readiness_inventory.md`.
- Decision: `proceed_to_guarded_user_test`.
- API send count `0`; product code changed `false`; source refetch `false`; generated article patch `false`; accepted status changed `false`.
- Accepted genres remain all six intended genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, `company_service_intro`.
- Remaining unaccepted genres: none.
- User-test checklist covers normal UI Route V/0506, route id `route_v_0506_structured_blog_v1`, Route A / writer-only fallback absence, raw full source handoff absence, H1/H2 structure, source_fact / llm_general_context separation, company_service_intro self-perspective, unsupported claim absence, body floor, quality report, and over-editing.
- Known caveats preserved: early `comparison_guide` / `case_study` evidence gaps, current module-bloat debt in `article_brief_source_shape_v2.py`, 0506 validation defaults versus normal UI Route V forced defaults, and the GENIAC/Gennai validation gap.
- Historical next owner: `route_v_guarded_release_user_test_manual_ui`.
- Older next-owner references later in this file are historical unless repeated by this current override, `TASK.md`, and `PROGRESS.md`.

## Historical State 2026-06-27 Post-Readiness Inventory Override

- Latest readiness inventory artifact: `notecode/logs/0627/route_v_all_genres_accepted_release_readiness_inventory_no_api_20260627_150315/readiness_inventory.md`.
- Decision: `proceed_to_guarded_release_user_test_handoff`.
- API send count `0`; product code changed `false`; source refetch `false`; generated article patch `false`; accepted status changed `false`.
- Accepted genres remain all six intended genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, `company_service_intro`.
- Remaining unaccepted genres: none.
- Known caveats preserved: early `comparison_guide` / `case_study` evidence gaps, current module-bloat debt in `article_brief_source_shape_v2.py`, 0506 validation defaults versus normal UI Route V forced defaults, and the GENIAC/Gennai validation gap.
- UI handoff boundary preserved: normal UI uses Route V/0506; Route A / writer-only fallback remains closed; raw full source handoff has not returned.
- Historical next owner: `route_v_release_user_test_handoff_no_api`.

## Historical State 2026-06-27 Post-Acceptance Decision Override

- Latest acceptance artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_live_residual_floor_buffer_acceptance_decision_no_api_20260627_134555/acceptance_decision.md`.
- Source validation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_live_residual_floor_buffer_one_article_api_validation_after_approval_20260627_132914/api_validation_summary.md`.
- Decision: `accepted`; accepted article type: `company_service_intro`.
- Acceptance owner API send count `0`; validation API send count `1`; product code changed `false`.
- Source refetch false; generated article patch false; raw full source_documents/source_packets/source_cards handoff false; Route A / writer-only fallback false.
- Accepted evidence: validation decision `acceptance_candidate`, final article generated, H1 exactly one, H2 sections present, body floor reached (`1401/1400` final), quality passed (`score=100`, issues none), source/persona/selected-excerpt/over-editing and unsupported-claim guards passed.
- Accepted genres are now all six intended genres: `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`, `company_service_intro`.
- Remaining unaccepted genres: none.
- Historical next owner: `route_v_all_genres_accepted_release_readiness_inventory_no_api`.

## Historical State 2026-06-27 Post-API Validation Override

- Latest validation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_live_residual_floor_buffer_one_article_api_validation_after_approval_20260627_132914/api_validation_summary.md`.
- Decision: `acceptance_candidate`; API send count `1`; product code changed `false`.
- The same saved `company_service_intro` source packet was reused and `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2` preflight passed.
- Source refetch false; generated article patch false; raw full source_documents/source_packets/source_cards handoff false; Route A / writer-only fallback false.
- Final article generated, H1 exactly one, H2 sections present, body floor reached (`1401/1400` final), quality passed (`score=100`, issues none).
- Source_fact / llm_general_context separation, company_service_intro self-perspective boundary, selected source excerpts used, and over-editing checks passed.
- Structural editor raw output fell below floor (`409/1400`) after a floor-reaching input, and the floor-loss guard restored the guarded/final article to `1401/1400`.
- `company_service_intro` remained unaccepted until the separate acceptance decision owner completed.
- Historical next owner: `route_v_company_intro_draft_writer_live_residual_floor_buffer_acceptance_decision_no_api`.

## Historical State 2026-06-27 Post-Implementation Override

- Latest implementation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_live_residual_floor_buffer_no_api_impl_20260627_170000/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`; API send count `0`; product code changed true only in DraftWriter company-intro live residual floor buffer scope.
- Preserved first confirmed gap: `company_intro_draft_writer_live_residual_floor_miss_after_no_api_replay_gap`.
- Source refetch false; generated article patch false; raw full source_documents/source_packets/source_cards handoff false; Route A / writer-only fallback false.
- Focused tests passed (`22 passed`); `py_compile` passed; changed-file bloat passed; prompt bloat none.
- Known pre-existing non-owner bloat remains in `article_brief_source_shape_v2.py` and `style_postprocessor.py`.
- `company_service_intro` remains unaccepted.
- Historical next owner: `route_v_company_intro_draft_writer_live_residual_floor_buffer_one_article_api_validation_after_approval`.

## Historical State 2026-06-27 Post-Diagnosis Override

- Latest diagnosis artifact: `notecode/logs/0627/route_v_company_intro_body_floor_reached_failure_diagnosis_no_api_20260627_160000/diagnosis.md`.
- Source validation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_one_article_api_validation_after_approval_20260627_131500/api_validation_summary.md`.
- Diagnosis decision: `needs_next_owner`; diagnosis API send count `0`; product code changed `false`; source refetch `false`; generated article patch `false`; raw full source_documents/source_packets/source_cards handoff `false`.
- Preserved validation facts: decision `reject_or_inconclusive`; validation API send count `1`; DraftWriter `1327/1400`, opening/global/style `1329/1400`, structural API raw/guarded/final `917/1400`, QA `961/1400`; H1 exactly one and H2 sections present; source/persona/selected-excerpt/over-editing/raw-source/fallback guards passed.
- First confirmed gap exactly one: `company_intro_draft_writer_live_residual_floor_miss_after_no_api_replay_gap`.
- Structural editor overcompression is a later observation, not the first owner, because the structural input was already subfloor at `1329/1400`.
- QA/human-readability/sentence issues remain secondary observations; the only QA issue is `body_length_below_floor`.
- Accepted genres remain `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, and `announcement`; `company_service_intro` remains unaccepted.
- Historical next owner: `route_v_company_intro_draft_writer_live_residual_floor_buffer_no_api_impl`.
- Non-owner boundaries remain: no source refetch, no generated article text patch, no raw full source_documents/source_packets/source_cards handoff, no Route A / writer-only fallback, no selector cap/windowing change, no source-shape detection or claim-allocation/cap change, no QA threshold or repair-acceptance relaxation, no broad prompt/persona tuning, and no `company_service_intro` acceptance without a separate acceptance decision after passing validation.

## Historical State 2026-06-27 Post-Implementation Override

- Latest implementation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_no_api_impl_20260627_104857/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`; API send count `0`; source refetch `false`; generated article patch `false`; raw full source handoff `false`.
- Product code changed only in DraftWriter company-intro residual followthrough scope: `app/services/company_intro_followthrough.py`; focused test added in `tests/test_company_intro_residual_followthrough.py`.
- Preserved first_confirmed_gap exactly: `company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough`.
- Saved-artifact replay improved DraftWriter body floor from `1155/1400` to `1409/1400` without API.
- Accepted genres remained `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, and `announcement`; `company_service_intro` remained unaccepted.
- Historical next owner: `route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_one_article_api_validation_after_approval`.

## Purpose

This file is the first document an AI coding agent should read in this workspace.

## Historical State 2026-06-27

- Latest validation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_selected_excerpt_floor_followthrough_one_article_api_validation_after_approval_20260627_091448/api_validation_summary.md`.
- Source implementation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_selected_excerpt_floor_followthrough_no_api_impl_20260627_010000/implementation_summary.md`.
- Latest diagnosis artifact: `notecode/logs/0627/route_v_company_intro_body_floor_reached_failure_diagnosis_no_api_20260627_092734/diagnosis.md`.
- Decision: `needs_next_owner`; diagnosis API send count `0`; product code changed `false`; source refetch `false`; generated article patch `false`.
- The same saved `company_service_intro` source packet was reused and `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2` preflight passed.
- Final article generated, H1 exactly one, H2 sections present, source/persona/selected-excerpt/over-editing/raw-source/fallback guards passed.
- Body floor failed after the selected-excerpt followthrough: DraftWriter `1155/1400`, opening/global/style `1157/1400`, structural API raw/guarded/final `331/1400`, QA `375/1400`.
- Quality failed on `body_length_below_floor` and `ending_bucket_monotony`; human readability check also failed.
- First confirmed gap: `company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough`; first below-floor stage `draft`; largest floor loss stage `structural_api_raw`.
- Accepted genres are now `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`.
- Remaining unaccepted genre: `company_service_intro`.
- Historical next owner before residual implementation: `route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_no_api_impl`.

## Historical State 2026-06-26

- Latest acceptance artifact: `notecode/logs/0626/route_v_announcement_draft_writer_selected_excerpt_floor_followthrough_acceptance_decision_no_api_20260626_202716/acceptance_decision.md`.
- Source validation artifact: `notecode/logs/0626/route_v_announcement_draft_writer_selected_excerpt_floor_followthrough_one_article_api_validation_after_approval_20260626_194056/api_validation_summary.md`.
- Decision: `accepted`; acceptance owner API send count `0`; product code changed `false`; source refetch `false`; generated article patch `false`.
- Accepted evidence: announcement final article generated, H1 exactly one, H2 sections present, body floor reached `958/900`, quality passed, source/persona/selected-excerpt/over-editing reviews passed.
- Structural editor floor-loss guard was accepted as protective: floor-reaching input `958/900`, structural API raw `671/900`, guarded/final `958/900`.
- Gates passed: H1 exactly one, H2 sections, announcement self-perspective `当社`, source boundary, selected excerpt / confirmed claim usage, raw full source handoff false, Route A false, writer-only false, focused tests, `py_compile`, and bloat check.
- Accepted genres are now `comparison_guide`, `case_study`, `daily_activity`, `market_explanation`, `announcement`.
- Remaining unaccepted genre: `company_service_intro`.
- Latest company-introduction API validation artifact: `notecode/logs/0626/route_v_company_intro_front_back_editor_persona_contract_one_article_api_validation_retry_after_api_520_20260626_231500/api_validation_summary.md`.
- Decision: `reject_or_inconclusive`; API send count `1`; product code changed false; source refetch false; generated article patch false. Final article generated, H1 exactly one, H2 section headings, source/persona/selected-excerpt/over-editing/raw-source/fallback guards passed, but body floor failed (`718/1400`) and quality failed only on `body_length_below_floor`.
- Historical next owner at the time: `route_v_company_intro_body_floor_reached_failure_diagnosis_no_api`.
Project goal: build a Japanese blog generation application that accepts multiple sources such as URLs, PDFs, Word files, and manual text, then generates natural Japanese blog articles grounded only in those sources.

The project must favor structured intermediate data over one-shot long prompting.

## Agent Instruction Source

`AGENTS.md` is the single source of truth for Codex and Claude.

- Codex should read this file directly.
- Claude should read `CLAUDE.md`, which imports this file.
- Do not create parallel tool-specific instruction files unless the user explicitly adds another coding tool.
- If `CLAUDE.md` and `AGENTS.md` ever conflict, update `CLAUDE.md` to point back to `AGENTS.md` rather than duplicating rules.

## Required Read Order

1. `AGENTS.md`
2. `README.md`
3. `docs/GOAL_PLAN.md`
4. `TASK.md`
5. `PROGRESS.md`
6. `ARCHITECTURE.md`
7. `docs/CURRENT_ALGORITHM.md`
8. `docs/ARTICLE_BRIEF_V2_SOURCE_SHAPE_ALGORITHM.md`
9. `docs/GENRE_ARRIVAL_CONTRACT_MATRIX.md`
10. `docs/PIPELINE_SPEC.md`
11. `docs/TECH_STACK.md`
12. `docs/SOURCE_ACQUISITION_POLICY.md`
13. `docs/JAPANESE_STYLE_POLICY.md`
14. `docs/ARTICLE_GENRE_POLICY.md`
15. `docs/CONFIG_AND_PERSONA_POLICY.md`
16. `docs/JAPANESE_STYLOMETRY_POLICY.md`
17. `docs/AI_CODING_RULES.md`
18. `WORKLOG.md`

Read the original seed document only when historical wording is needed:

- `blog_generation_agents_and_task.md`

## Repository State

- This workspace now has an implementation, tests, runtime artifacts, and active Route V/0506 work.
- This folder may not be a git repository in local windows; use direct file inspection, file timestamps, artifact roots, and content checks when git metadata is unavailable.
- Use direct file inspection, file timestamps, and content checks instead of git status or git diff.
- Treat `blog_generation_agents_and_task.md` as the original source note, not the operating entrypoint.
- Do not delete or rewrite the original seed document unless explicitly requested.

## Current Route V Boundary

- Route V/0506 is the active structured blog path for this workspace.
- Route B is a retired name. Legacy artifact/package paths containing `route_b` are historical evidence or migration references only; they are not current route identifiers.
- For source-shape, floor-length, H1, and DraftWriter work, read `docs/CURRENT_ALGORITHM.md`, `docs/ARTICLE_BRIEF_V2_SOURCE_SHAPE_ALGORITHM.md`, the latest `WORKLOG.md` entries, and the newest diagnosis artifact before editing code.
- As of 2026-06-21, `source_shape` drift across API runs is treated as LLM extraction variance, not a source-shape fix owner. Do not change source-shape detection or claim allocation unless a new diagnosis proves that owner.
- As of 2026-06-23, the latest one-API-per-article validation, post-fix recheck, and read-only diagnoses are:
  - `notecode/logs/0621/route_b_0506_v2_floor_h1_one_api_per_article_20260621_234827/`
  - `notecode/logs/0621/draft_writer_floor_actuation_runtime_diagnosis_20260622_005034/`
  - `notecode/logs/0622/route_b_0506_v2_paragraph_depth_fix_api_recheck_20260622_122514/`
  - `notecode/logs/0622/draft_writer_paragraph_depth_fix_api_recheck_failure_diagnosis_20260622_130918/`
- H1 contract is no longer the current owner: post-fix validation reached `h1_count=1` for all 4 completed article types; the 2 incomplete article types stopped before DraftWriter on API infra errors.
- Body floor remains unresolved: post-fix validation reached final floor in 0/4 completed article types, with 4/4 `body_length_below_floor=true`.
- The implemented paragraph-depth fix did not improve body floor.
- `draft_writer_floor_actuation_count_based_depth_redesign` is implemented with no-API gate pass (`39 passed`, `py_compile` pass, `inspect_bloat` pass / `failures=[]`).
- Count-based API isolation recheck artifact: `notecode/logs/0622/route_b_0506_v2_count_based_floor_actuation_api_isolation_recheck_20260622_140222/`.
- Count-based recheck result is partial positive but incomplete: completed 2/6 article types; floor reached 2/2 completed; H1 reached 2/2 completed; quality pass 1/2 completed; 4 article types failed before full evaluation due artifact packaging or API infra errors.
- Failure diagnosis found likely long artifact path / validation packaging issues for `company_service_intro` and `market_explanation`, and API 520 infra failures for `comparison_guide` and `daily_activity`.
- Short-path validation packaging recheck artifact: `notecode/logs/0622/cbsp_1429/`.
- Short-path recheck fixed the packaging gap but did not pass body floor overall: completed 5/6 article types, final floor reached 1/5 completed, H1 reached 5/5 completed, quality pass 0/5 completed, `body_length_below_floor` appeared in 4/5 completed. Floor gap improved vs baseline in 5/5 completed comparable types and vs paragraph-depth in 3/3 completed comparable types, but this is not user-test ready.
- Floor-gap diagnosis artifact: `notecode/logs/0622/cbsp_1429/floor_gap_diagnosis.md`.
- Floor-gap diagnosis found the current paragraph target was met or exceeded in 5/5 completed article types, but draft floor and final floor were only reached in 1/5. The residual is paragraph depth/final-floor buffer, not H1 and not large editor/postprocessor deletion.
- `draft_writer_floor_actuation_depth_budget_contract_impl` is implemented with no-API gate pass (`39 passed`, `py_compile` pass, `inspect_bloat` pass / `failures=[]`). It keeps DraftWriter as the only product-code owner, adds a bounded source-backed depth budget from floor/target chars, section count, assigned claims, and selected excerpts, and does not run API validation.
- Depth-budget one-article API smoke artifact: `notecode/logs/0622/dbsm_1550/`. `market_explanation` reached final floor (`1641/1400`), H1 (`1`), and quality pass, but unassigned-claim enumeration regressed to `true` and manual review found sentence-fragment/punctuation issues.
- Depth-budget smoke diagnosis artifact: `notecode/logs/0622/dbsm_1550/smoke_failure_diagnosis.md`; first confirmed gap was `writer_context_assigned_claim_boundary_gap`.
- Assigned-claim boundary fix artifact: `notecode/logs/0622/dbsm_1550/assigned_claim_boundary_fix_summary.md`; no-API gates passed.
- Assigned-claim boundary API smoke recheck artifact: `notecode/logs/0622/dbsm_1550/assigned_claim_boundary_api_smoke_recheck.md`; stopped before DraftWriter on OpenAI/API HTTP 520, so target behavior was not evaluable.
- Legacy-named Route V context snapshot package: `notecode/plan/route_b_context_snapshot_2026-06-23/`.
- The runtime legacy path guard is complete in `notecode/logs/0623/route_b_runtime_legacy_path_guard_20260623_145014/`; focused no-API Route V guard/UI suite passed (`55 passed`), product behavior changed false, API send count 0.
- Source-context handoff diagnosis is complete in `notecode/logs/0623/route_b_source_context_handoff_diagnosis_20260623_000000/diagnosis.md`; first confirmed gap is `draft_writer_excerpt_primary_material_contract_gap`.
- DraftWriter excerpt-primary context contract is complete in `notecode/logs/0623/route_v_draft_writer_excerpt_primary_context_contract_20260623_154332/implementation_summary.md`; `selected_source_excerpts` are now the primary section context where present, assigned/confirmed claims remain verification anchors, no raw full `source_documents` are passed, and focused no-API tests passed.
- DraftWriter excerpt-primary one-article API smoke is complete in `notecode/logs/0623/epcs_1557/api_smoke_review.md`; total API terminal sends 12, evaluable retry sends 6 after one harness-only v2 repair, product code changed false, Route A fallback false, writer-only fallback false, raw full `source_documents` passed false, final floor/H1/quality pass true.
- Selected excerpt coverage / section-context diagnosis is complete in `notecode/logs/0623/epcs_1557/selected_excerpt_coverage_section_context_diagnosis.md`; API send count 0, product code changed false, raw full `source_documents` passed false. It selected `route_v_selected_excerpt_final_usage_coverage_contract` as the next owner.
- Selected excerpt final-usage coverage contract is complete in `notecode/logs/0623/epcs_1557/selected_excerpt_final_usage_coverage_contract_summary.md`; API send count 0, product code changed true in selector-side coverage files only, raw full `source_documents` passed false. It selected `route_v_selected_excerpt_final_usage_coverage_contract_one_article_api_smoke_after_approval` as the next API-smoke owner, now completed.
- Selected excerpt final-usage one-article API smoke is complete in `notecode/logs/0623/sefc_1830/api_smoke_review.md`; API send count 6, product code changed false, raw full `source_documents` passed false, final floor/H1/quality pass true, unassigned-claim enumeration false.
- Selected excerpt final-usage acceptance decision is complete in `notecode/logs/0623/sefc_1830/selected_excerpt_final_usage_acceptance_decision.md`; API send count 0, product code changed false, raw full `source_documents` passed false. Decision is `accept_with_known_gap`; GENIAC/Gennai final-hinted live exercise remains a known validation gap.
- Company-introduction three-source API generation after acceptance is complete in `notecode/logs/0623/company_intro_three_sources_after_acceptance_20260623_230000/api_generation_summary.md`; API send count 23, product code changed false, raw full `source_documents` passed false, selected excerpts present true, H1 true for all 3, but final floor and quality failed for all 3 (`1161`, `1215`, `1000` chars). This selected `route_v_company_intro_low_intent_length_floor_contract`.
- Company-introduction low-intent length/floor contract limited API validation is complete in `notecode/logs/0623/company_intro_low_intent_length_floor_contract_20260623_233000/limited_api_validation_summary.md`; API send count 3, product code changed true in `draft_writer.py` and `article_brief_source_shape_v2.py`, raw full `source_documents` passed false, selected excerpt counts matched prior validation, H1 true for all 3, but final floor and quality still failed for all 3 (`1310`, `1361`, `985` chars). Decision: `reject`; it selected `route_v_company_intro_low_intent_length_floor_contract_repair` as the next owner at the time.
- Company-introduction source-backed reader bridge + section density limited API validation is complete in `notecode/logs/0623/company_intro_reader_bridge_section_density_api_validation_20260623_235500/limited_api_validation_summary.md`; API send count 3, product code changed true in `draft_writer.py`, `article_brief_source_shape_v2.py`, and `article_brief.schema.json`, raw full `source_documents` passed false, selected excerpt counts matched prior validation, H1 true for all 3. Healthrent passed floor/H1/quality (`1584` chars), Sanin reached floor but failed `model_frequent_word` (`1450` chars), and Sanrei still missed floor (`1202` chars). Decision: `reject`; it left `route_v_company_intro_low_intent_length_floor_contract_repair` as the next owner at the time.
- Company-introduction beat-sheet two-case validation is complete in `notecode/logs/0623/company_intro_beat_sheet_two_case_corrected_api_validation_20260623_223500/beat_sheet_rejection_diagnosis.md`; corrected API send count 2 after one invalid 2-send run caught by self-test, raw full `source_documents` passed false, selected excerpt counts matched, beat instruction present true, H1 true for both failed cases, but Sanrei and Sanin both failed floor and quality (`1168`, `1282` chars). Decision: `reject`; the attempted beat-sheet product change was removed after validation, leaving `route_v_company_intro_low_intent_length_floor_contract_repair` as the next owner at the time.
- Company-introduction floor feasibility / source-material diagnosis is complete in `notecode/logs/0623/company_intro_floor_feasibility_source_material_diagnosis_20260623_233500/floor_feasibility_source_material_diagnosis.md`; API send count 0, product code changed false, raw full `source_documents` passed false. It selected `route_v_company_intro_thin_source_excerpt_material_increase` as the current next one owner because Sanrei's selected excerpt material was thin (`1531` chars) while same-shape Healthrent passed with `2600` chars.
- Company-introduction selector-capacity trace is complete in `notecode/logs/0624/company_intro_selector_capacity_trace_20260624_000000/selector_capacity_trace.md`; API send count 0, product code changed false, raw full `source_documents` passed false. It confirmed Sanrei has selector headroom (`3267` source chars, best current-slot candidate set `2600` chars) and retained `route_v_company_intro_thin_source_excerpt_material_increase` as the current next one owner.
- Company-introduction thin source excerpt material increase is complete in `notecode/logs/0624/route_v_company_intro_thin_source_excerpt_material_increase_20260624_000000/implementation_summary.md`; API send count 0, product code changed true in selector-side files only, raw full `source_documents` passed false. Sanrei selected material increased from `3` / `1531` to `4` / `2600`; Healthrent and Sanin stayed at `2600`; added Sanrei material passed lexical novelty.
- Company-introduction thin source excerpt material increase one-article API validation is complete in `notecode/logs/0624/tmi_sanrei_api_20260624_101500/api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false, Route A fallback false, writer-only fallback false. Sanrei selected excerpts reached `4` / `2600`, H1 reached, unassigned-claim enumeration false, but final floor still failed (`1136/1400`) and quality failed on `body_length_below_floor`.
- Company-introduction floor underproduction after thin material increase diagnosis is complete in `notecode/logs/0624/route_v_company_intro_floor_underproduction_after_thin_material_increase_failure_diagnosis_20260624_110000/floor_underproduction_diagnosis.md`; API send count 0, product code changed false. It confirmed DraftWriter underproduction (`1300/1400`) plus deterministic edited-stage shrink (`1300` -> `1136`) from `style_postprocessor.postprocess_style()`, not an LLM style-editor prompt.
- Company-introduction stage-floor contract after material increase implementation is complete in `notecode/logs/0624/route_v_company_intro_stage_floor_contract_after_material_increase_no_api_impl_20260624_112516/implementation_summary.md`; API send count 0, product code changed true in `draft_writer.py` and `style_postprocessor.py`, raw full `source_documents` passed false. Focused no-API gates passed, and Sanrei no-API replay reduced deterministic postprocessor shrink from the prior `1300 -> 1136` pattern to `1333 -> 1329`.
- Company-introduction stage-floor contract Sanrei API validation is complete in `notecode/logs/0624/sfc_sanrei_api_20260624_122335/api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false, Route A fallback false, writer-only fallback false. Sanrei reached final floor (`1453/1400`) and H1 (`1`) but failed quality (`sentence_too_long`, `low_density_bridge_sentence`, `abstract_navigation_phrase`). Failure diagnosis is `notecode/logs/0624/sfc_sanrei_api_20260624_122335/failure_diagnosis.md`.
- Targeted rewrite sentence split grammar safety repair is complete in `notecode/logs/0624/route_v_targeted_rewrite_sentence_split_grammar_safety_repair_20260624_133328/implementation_summary.md`; API send count 0, product code changed true in `editor_output_safety.py` only. Sanrei no-API replay no longer produces `発足し。` or `（松江会場）」。`.
- Targeted rewrite grammar safety same-source Sanrei API recheck is complete in `notecode/logs/0624/trg_sanrei_api_20260624_135350/api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false. Grammar break stayed fixed, but final floor failed (`1084/1400`) and quality failed.
- Company-introduction DraftWriter floor variance diagnosis is complete in `notecode/logs/0624/route_v_company_intro_draft_floor_variance_diagnosis_20260624_144005/diagnosis_summary.md`; API send count 1, product code / prompt changed during validation false, raw full `source_documents` passed false, Route A fallback false, writer-only fallback false. Sanrei reached final floor (`1488/1400`) and H1 (`1`) but failed quality (`sentence_too_long`, `ending_bucket_monotony`, `viewpoint_owner_mismatch`). It selected `route_v_company_intro_self_viewpoint_dense_bridge_boundary_diagnosis`.
- Company-introduction self-viewpoint / dense-bridge boundary probe is complete in `notecode/logs/0624/route_v_company_intro_self_viewpoint_dense_bridge_boundary_probe_20260624_000000/position_distribution_analysis.md`; API send count 0, product code / prompt changed false. It found late-half `ます` convergence as model-followthrough, but `と案内しています` appears in both early and late sentences, so self-viewpoint drift is prompt/algorithm boundary.
- Company-introduction model-followthrough simple late-rhythm fix is complete in `notecode/logs/0624/route_v_company_intro_model_followthrough_simple_late_rhythm_fix_no_api_20260624_000000/implementation_summary.md`; API send count 0, product code changed true only in `style_postprocessor.py` plus focused test, prompt changed false. No-API replay removed `ending_bucket_monotony`; remaining issues are `sentence_too_long` and `viewpoint_owner_mismatch`.
- Company-introduction bridge contract position-aware rewrite is complete in `notecode/logs/0624/route_v_company_intro_bridge_contract_position_aware_rewrite_no_api_20260624_155529/implementation_summary.md`; API send count 0, product code changed true only in deterministic guards plus focused tests, prompt changed false. No-API replay passed quality (`score=100`) and removed `sentence_too_long` / `viewpoint_owner_mismatch`.
- Company-introduction bridge contract position-aware rewrite one-article API validation is complete in `notecode/logs/0624/bcpr_sanrei_api_20260624_160044/api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false. Sanrei passed final floor (`1453/1400`), H1 (`1`), and quality (`score=100`, issues none).
- Company-introduction interest bridge / reader-navigation diagnosis is complete in `notecode/logs/0624/route_v_company_intro_interest_bridge_not_reader_navigation_diagnosis_20260624_161936/diagnosis_summary.md`; API send count 0, product code changed false. It found draft-origin reader-navigation sentences that QA did not detect.
- Company-introduction interest bridge positive contract no-API implementation is complete in `notecode/logs/0624/route_v_company_intro_interest_bridge_positive_contract_no_api_20260624_164044/implementation_summary.md`; API send count 0, product code changed true in `draft_writer.py` and `article_brief_source_shape_v2.py`, banned phrase-list growth false, one-off Sanrei patch false, related tests passed.
- Company-introduction interest bridge positive contract one-article API validation is complete in `notecode/logs/0624/ibpc_sanrei_api_20260624_164909/api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false. Sanrei improved the targeted reader-navigation phrases but failed final floor (`1298/1400`), H1 passed (`1`), quality failed only on `body_length_below_floor`.
- Company-introduction interest bridge positive contract floor regression diagnosis is complete in `notecode/logs/0624/route_v_company_intro_interest_bridge_positive_contract_floor_regression_diagnosis_20260624_170346/floor_regression_diagnosis.md`; API send count 0, product code changed false. It found the negative reader-navigation clause removed paragraph volume without redirecting budget into source-grounded claim backfill.
- Company-introduction interest bridge paragraph-budget backfill no-API implementation is complete in `notecode/logs/0624/route_v_company_intro_interest_bridge_paragraph_budget_backfill_contract_no_api_20260624_172154/implementation_summary.md`; API send count 0, product code changed true only in `draft_writer.py` plus focused tests. It adopted ClaudeCode diagnosis by redirecting blocked reader-navigation paragraph volume into assigned-claim depth / source-grounded confirmed-claim context and normalizing legacy company-intro `paragraph_function_plan` payload slots, without phrase-list growth or source-shape/claim/QA changes.
- Company-introduction interest bridge paragraph-budget backfill one-article API validation is complete in `notecode/logs/0624/pbb_sanrei_api_20260624_185848/api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false, Route A fallback false, writer-only fallback false. Sanrei failed final floor (`1326/1400`) and quality (`score=52`) while H1 passed (`1`); legacy `paragraph_function_plan` exact markers were absent from the DraftWriter payload, but residual navigation-shaped cues remained in other payload fields.
- Company-introduction residual payload navigation cue boundary diagnosis is complete in `notecode/logs/0624/route_v_company_intro_interest_bridge_residual_payload_navigation_cue_boundary_no_api_diagnosis_20260624_191224/diagnosis_summary.md`; API send count 0, product code changed false, web research used. It found that the remaining `分かります` / `見えてきます` issue is a reader-inference frame, not a phrase-ban problem, and selected a positive replacement contract.
- Company-introduction reader-inference to source-action contract no-API implementation is complete in `notecode/logs/0624/route_v_company_intro_reader_inference_to_source_action_contract_no_api_20260624_192852/implementation_summary.md`; API send count 0, product code changed true only in `draft_writer.py` plus focused tests. It normalizes company-intro self-authored residual payload fields from reader/outside-observer inference into company-side source-backed action/value guidance without phrase-list growth or Sanrei text patching.
- Company-introduction reader-inference to source-action Sanrei API validation is complete in `notecode/logs/0624/route_v_company_intro_reader_inference_to_source_action_contract_one_article_api_validation_20260624_194041/api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false, Route A fallback false, writer-only fallback false. Sanrei passed reader-inference bridge review (`0` disallowed frames) and H1 (`1`) but missed final floor (`1166/1400`) and quality failed only on `body_length_below_floor`.
- Company-introduction reader-inference contract floor regression diagnosis is complete in `notecode/logs/0624/route_v_company_intro_reader_inference_contract_floor_regression_diagnosis_20260624_200131/floor_regression_diagnosis.md`; API send count 0, product code changed false. It found a DraftWriter depth followthrough risk after the reader-inference frame was removed, with no prompt bloat, banned phrase-list growth, or one-off Sanrei patch.
- Company-introduction reader-inference contract Sanrei API validation after diagnosis is complete in `notecode/logs/0624/route_v_company_intro_reader_inference_contract_sanrei_one_article_api_validation_after_diagnosis_20260624_204407/api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false, Route A / writer-only fallback false. Sanrei again missed the floor at DraftWriter output (`1215/1400` draft, `1219/1400` final), H1 passed (`1`), quality failed, and paragraph depth metrics were draft `14` non-heading paragraphs / `82.1` average chars.
- Company-introduction front/back editor persona two-API trial is complete in `notecode/logs/0624/route_v_company_intro_front_back_editor_persona_two_api_trial_after_encoding_guard_20260624_213222/api_trial_summary.md`; API send count 2 as a user-approved exploratory exception, product code changed during trial false, raw full `source_documents` passed false, Route A / writer-only fallback false. Sanrei reached final floor (`1452/1400`), H1 (`1`), and reader-frame marker pass (`0` hits), but quality still failed (`sentence_too_long`, `model_frequent_word`). This is not acceptance.
- Company-introduction front/back editor persona one-API refinement is complete in `notecode/logs/0624/route_v_company_intro_front_back_editor_persona_one_api_refinement_trial_after_two_pass_20260624_214820/api_trial_summary.md`; API send count 1, product code changed during trial false, raw full `source_documents` passed false, Route A / writer-only fallback false. Sanrei reached final floor (`1502/1400`), H1 (`1`), and reader-frame marker pass (`0` hits), but quality still failed (`sentence_too_long`, `model_frequent_word`). This is not acceptance and keeps the same no-API design owner.
- Cross-genre editor persona contract config no-API implementation is complete in `notecode/logs/0624/route_v_cross_genre_editor_persona_contract_config_no_api_impl_20260624_223244/implementation_summary.md`; API send count 0, product code changed true only in compact config/persona contract data, renderer/preflight service, and focused tests. Matrix, rendered prompt bloat, and encoding preflight checks passed.
- Cross-genre non-announcement second editor policy no-API revision is complete in `notecode/logs/0624/route_v_cross_genre_non_announcement_editor_pass_policy_no_api_revision_20260624_225013/policy_revision_summary.md`; API send count 0, product code changed true only in compact persona config, renderer/preflight service, and focused tests. `announcement` has no second pass; the other five genres have short genre-specific second editor roles; shared second-pass rules live once in config.
- Cross-genre editor persona contract editor-stage wiring no-API implementation is complete in `notecode/logs/0625/route_v_cross_genre_editor_persona_contract_editor_stage_wiring_no_api_impl_20260625_002659/implementation_summary.md`; API send count 0, product code changed true only in the editor-stage wiring helper, editor agents, pipeline runner wiring, and focused tests. The rendered contract now reaches editor agent instructions; local deterministic editor behavior is preserved through `LocalPipelineClient`; `PipelineObserver` records editor-stage instructions.
- Cross-genre editor persona contract comparison-guide one-API validation after wiring is complete in `notecode/logs/0625/route_v_cross_genre_editor_persona_contract_comparison_guide_one_api_validation_after_wiring_20260625_090000/api_validation_summary.md`; API send count 1, product code changed false, editor-stage instruction contract present, source_fact / llm_general_context separation acceptable, unsupported ranking / best-claim false, third-party viewpoint false, raw full `source_documents` false, Route A / writer-only fallback false, and quality pass true. Decision is reject_or_inconclusive because H1 count was `3`, not exactly `1`.
- Comparison-guide H1 failure diagnosis and local heading-level implementation are complete; the approved comparison-guide heading-level one-article API validation is complete in `notecode/logs/0625/route_v_comparison_guide_heading_level_one_article_api_validation_after_approval_20260625_101206/api_validation_summary.md`. API send count 1, product code changed during validation false, all observed stages preserved exactly one H1 and the three section headings stayed H2, source_fact / llm_general_context separation and quality passed, and decision is `acceptance_candidate`.
- Comparison-guide opening subject-specificity no-API diagnosis is complete in `notecode/logs/0625/route_v_comparison_guide_opening_subject_specificity_no_api_diagnosis_20260625_105657/opening_subject_specificity_diagnosis.md`; API send count 0, product code changed false. It selected `route_v_comparison_guide_editor_stage_opening_subject_specificity_contract_no_api_impl`.
- Comparison-guide opening subject-specificity editor-stage contract no-API implementation is complete in `notecode/logs/0625/route_v_comparison_guide_editor_stage_opening_subject_specificity_contract_no_api_impl_20260625_115625/implementation_summary.md`; API send count 0, product code changed true only in `notecode/0506/app/personas/editor_persona_contracts.yaml`, and no-API render / bloat / conflict / focused tests passed.
- Comparison-guide opening subject-specificity one-article API validation is complete in `notecode/logs/0625/route_v_comparison_guide_opening_subject_specificity_one_article_api_validation_after_approval_20260625_121019/api_validation_summary.md`; API send count 1, product code changed during validation false, editor-stage contract reached the structural editor, candidates and four axes appeared in the opening, H1/H2/source handoff/fallback guards passed, but the opening still omitted the comparison target category and quality failed on `connector_repetition`. Decision is `reject_or_inconclusive`.
- Comparison-guide opening subject-specificity no-API failure diagnosis is complete in `notecode/logs/0625/route_v_comparison_guide_opening_subject_specificity_no_api_failure_diagnosis_20260625_122602/failure_diagnosis.md`; API send count 0, product code changed false. It found the category existed in target_reader / C001 / source artifacts but not as a first-class article_brief field; `connector_repetition` was a separate stylometry substring-boundary issue from `部門をまたいで` / `部署をまたいで`.
- Comparison-guide article_brief category field no-API implementation is complete in `notecode/logs/0625/route_v_comparison_guide_article_brief_comparison_target_category_field_no_api_impl_20260625_131141/implementation_summary.md`; API send count 0, product code changed true only in article_brief schema/builder plus focused tests. `comparison_target_category` is derived from existing target_reader / confirmed-claim material, excluded from the OpenAI strict response schema, and reaches editor-stage payloads in no-API replay.
- Comparison-guide category field one-article API validation is complete in `notecode/logs/0625/route_v_comparison_guide_category_field_one_article_api_validation_after_approval_20260625_132712/api_validation_summary.md`; API send count 1, product code changed during validation false, the final opening included `社内ナレッジ管理ツール`, three candidates, and three axes, H1/H2/source handoff/fallback guards passed, quality passed, and decision is `acceptance_candidate`.
- Comparison-guide category field acceptance decision is complete in `notecode/logs/0625/route_v_comparison_guide_category_field_acceptance_decision_no_api_20260625_134814/acceptance_decision.md`; API send count 0, product code changed false, and decision is `accepted`.
- Case-study editor persona contract one-article API validation is complete in `notecode/logs/0625/route_v_case_study_editor_persona_contract_one_article_api_validation_after_approval_20260625_140859/api_validation_summary.md`; API send count `1`, product code changed false, persona/source-boundary checks passed, and final QA failed only on `paragraph_rhythm_monotony`.
- Case-study paragraph-rhythm failure diagnosis is complete in `notecode/logs/0625/route_v_case_study_paragraph_rhythm_monotony_failure_diagnosis_no_api_20260625_143023/diagnosis.md`; API send count `0`, product code changed false, and first confirmed gap is `structural_editor_missing_knowledge_pack_payload_for_case_study_rhythm_repair`.
- Case-study structural-editor knowledge-pack payload contract implementation is complete in `notecode/logs/0625/route_v_case_study_structural_editor_knowledge_pack_payload_contract_no_api_impl_20260625_143533/implementation_summary.md`; API send count `0`, product code changed true only in structural-editor payload wiring and focused tests, and no-API gates passed.
- Case-study structural-editor payload contract API validation is attempted in `notecode/logs/0625/route_v_case_study_structural_editor_knowledge_pack_payload_contract_one_article_api_validation_after_approval_20260625_143720/api_validation_summary.md`; API send count `0`, product code changed false, and validation blocked before API by Windows path-length packaging error.
- The old `route_v_case_study_api_infra_unblock_no_api` handoff is historical; it is superseded by the completed short-path validation artifact from `20260625_152645`.
- Case-study structural-editor compact knowledge payload acceptance decision is complete in `notecode/logs/0625/route_v_case_study_structural_editor_knowledge_pack_payload_contract_acceptance_decision_no_api_20260625_154025/acceptance_decision.md`; API send count `0`, product code changed false, and decision is `accepted`.
- Daily-activity editor persona contract API validation is attempted in `notecode/logs/0625/route_v_daily_activity_editor_persona_contract_one_article_api_validation_after_approval_20260625_172250/api_validation_summary.md`; API send count `1`, product code changed false, prompt/persona preflight passed, source refetch false, raw full source handoff false, Route A / writer-only fallback false, and validation blocked by OpenAI/API HTTP 520 before final article generation.
- Daily-activity API infra failure diagnosis is complete in `notecode/logs/0625/route_v_daily_activity_api_infra_failure_diagnosis_no_api_20260625_191006/api_infra_failure_diagnosis.md`; API send count `0`, product code changed false, retry eligibility passed, and the output remained quality-unevaluable.
- Daily-activity retry after API 520 is complete in `notecode/logs/0625/route_v_daily_activity_editor_persona_contract_one_article_api_validation_retry_after_api_520_20260625_194402/api_validation_summary.md`; API send count `1`, product code changed false, same saved source packet reused, source refetch false, raw full source handoff false, Route A / writer-only fallback false, final article generated, H1 exactly one, H2 section headings, compact structural-editor knowledge context visible, but decision is `reject_or_inconclusive`.
- Daily-activity structural-editor scene-material preservation no-API implementation is complete in `notecode/logs/0625/route_v_daily_activity_structural_editor_scene_material_preservation_no_api_impl_20260625_204042/implementation_summary.md`; API send count `0`, product code changed true only in compact structural-editor instruction/payload boundary and focused tests. No-API gate passed: instruction boundary present, payload boundary present, compact knowledge context maintained, raw full source handoff false, H1/H2 preserved, and no structural overcompression in replay.
- Daily-activity structural-editor scene-material preservation one-article API validation is complete in `notecode/logs/0625/route_v_daily_activity_structural_editor_scene_material_preservation_one_article_api_validation_after_approval_20260625_205543/api_validation_summary.md`; API send count `1`, product code changed false, same saved source packet reused, source refetch false, raw full source handoff false, Route A / writer-only fallback false. Scene material payload reached the structural editor and all six scene categories were retained, but final QA failed on `sentence_too_long` and the article remained too close to announcement/list guidance. Decision is `reject_or_inconclusive`.
- Daily-activity source-near expansion failure diagnosis is complete in `notecode/logs/0625/route_v_daily_activity_source_near_expansion_only_failure_diagnosis_no_api_20260625_214751/diagnosis.md`; API send count `0`, product code changed false, source refetch false, article patch false, prompt/persona tuning false, QA relaxation false. First confirmed gap is `daily_activity_article_brief_auxiliary_notice_source_role_boundary_gap`.
- Daily-activity article_brief auxiliary notice source-role contract no-API implementation is complete in `notecode/logs/0625/route_v_daily_activity_article_brief_auxiliary_notice_source_role_contract_no_api_impl_20260625_220845/implementation_summary.md`; API send count `0`, product code changed true only in allowed article_brief/source-shape files, and no-API gates passed.
- Daily-activity source-role live payload visibility no-API diagnosis is complete in `notecode/logs/0625/route_v_daily_activity_source_role_contract_live_payload_visibility_failure_diagnosis_no_api_20260625_223300/diagnosis.md`; API send count `0`, product code changed false. First confirmed gap is `live_validation_harness_missing_route_v_source_shape_v2_env`.
- Daily-activity source-role contract one-article API validation is complete in `notecode/logs/0625/daily_activity_source_role_contract_one_article_api_validation_after_approval_20260625_231002/api_validation_summary.md`; API send count `1`, product code changed false, source refetch false, raw full source handoff false, Route A / writer-only fallback false. Route B runtime env activated `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2`, and live `article_brief` / structural payload carried `daily_activity_source_role_contract`. Final article generated with H1 exactly one and H2 headings, but `source_near_expansion_only`, scene material retention, quality, and over-editing failed; quality failed only on `body_length_below_floor` (`441/1200`).
- Daily-activity source-near expansion failure diagnosis after source-role contract is complete in `notecode/logs/0625/route_v_daily_activity_source_near_expansion_only_failure_diagnosis_no_api_20260625_232859/diagnosis.md`; API send count `0`, product code changed false. First confirmed gap is `daily_activity_draft_writer_selected_excerpt_scene_expansion_followthrough_gap`.
- Daily-activity DraftWriter scene expansion API validation after env-preflight fix is complete in `notecode/logs/0626/daily_activity_draft_writer_scene_expansion_one_article_api_validation_after_approval_20260626_092626/api_validation_summary.md`; API send count `1`, product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. Preflight passed with `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2`; `daily_activity_source_role_contract` and `selected_source_excerpts` were visible/effective; H1/H2/source-near/over-editing guards passed. Decision is `reject_or_inconclusive` because quality failed only on `body_length_below_floor` (`884/1200`).
- Daily-activity quality-pass failure no-API diagnosis is complete in `notecode/logs/0626/route_v_daily_activity_quality_pass_failure_diagnosis_no_api_20260626_095107/diagnosis.md`; API send count `0`, product code changed false, source refetch false, generated article patch false. First confirmed gap exactly one: `structural_editor_live_api_floor_loss_guard_gap`. The first below-floor stage is the live structural editor API output (`style` 1200 -> `structural_api_raw` 856), and `guard_editor_output` accepted the subfloor output unchanged (`structural_api_guarded` 856; final 856). DraftWriter, selected excerpt usage, source-role contract, final copy shrink, selector cap, and QA measurement delta are not first owners.
- Daily-activity structural-editor floor-loss guard no-API implementation is complete in `notecode/logs/0626/route_v_daily_activity_structural_editor_floor_loss_guard_no_api_impl_20260626_100159/implementation_summary.md`; API send count `0`, product code changed true only in allowed guard/pipeline/test files, and focused no-API gates passed. The latest replay reverted structural API raw `856/1200` back to the floor-reaching style input `1200/1200`.
- Daily-activity structural-editor floor-loss guard one-article API validation is complete in `notecode/logs/0626/daily_activity_structural_editor_floor_loss_guard_one_article_api_validation_after_approval_20260626_100740/api_validation_summary.md`; API send count `1`, product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. Live guard blocked structural API raw `704/1200` and final stayed floor-reaching `1200/1200`, but quality failed only on `sentence_too_long`; decision is `reject_or_inconclusive`.
- Daily-activity quality-pass failure diagnosis after floor-loss guard is complete in `notecode/logs/0626/route_v_daily_activity_quality_pass_failure_diagnosis_no_api_20260626_102004/diagnosis.md`; API send count `0`, product code changed false, source refetch false, generated article patch false. First confirmed gap exactly one: `targeted_rewrite_sentence_split_limit_followthrough_gap`.
- Targeted rewrite sentence split followthrough no-API implementation is complete in `notecode/logs/0626/route_v_targeted_rewrite_sentence_split_limit_followthrough_no_api_impl_20260626_103925/implementation_summary.md`; API send count `0`, product code changed true only in `app/services/editor_output_safety.py` with focused tests in `tests/test_editor_output_guard.py`. Replay against `20260626_100740` reduced max sentence length to `85` with no over-limit sentences and preserved floor/H1/H2.
- Daily-activity targeted rewrite sentence split followthrough one-article API validation is complete in `notecode/logs/0626/daily_activity_targeted_rewrite_sentence_split_followthrough_one_article_api_validation_after_approval_20260626_110732/api_validation_summary.md`; API send count `1`, product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. Final article generated, H1/H2/body floor/quality/source-near/source-role/selected-excerpt/floor-loss guard/over-editing checks passed, and `sentence_too_long` was absent.
- Daily-activity targeted rewrite sentence split followthrough acceptance decision is complete in `notecode/logs/0626/route_v_daily_activity_targeted_rewrite_sentence_split_followthrough_acceptance_decision_no_api_20260626_112809/acceptance_decision.md`; API send count `0`, product code changed false, decision is `accepted`, and `daily_activity` is recorded as accepted.
- Validation runtime preflight genre-expectation no-API implementation is complete in `notecode/logs/0626/route_v_validation_runtime_preflight_genre_expectation_no_api_impl_20260626_122213/implementation_summary.md`; API send count `0`, product code changed true only in validation harness/test scope, product article generation behavior changed false. `daily_activity_source_role_contract_expected=false` is now metadata, not a required failed check, for `market_explanation`.
- Market-explanation DraftWriter selected-excerpt floor followthrough one-article API validation is complete in `notecode/logs/0626/mxse_api_20260626_153053/api_validation_summary.md`; API send count `1`, product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. Preflight passed with `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2`; final article generated, H1 exactly one, H2 headings, body floor reached (`1244/1200`), selected excerpts both used, source-boundary/unsupported-expansion/sentence-length/over-editing guards passed. Decision is `reject_or_inconclusive` because quality failed on `low_density_bridge_sentence` and `abstract_navigation_phrase`.
- Market-explanation quality-pass failure diagnosis is complete in `notecode/logs/0626/route_v_market_explanation_quality_pass_failure_diagnosis_no_api_20260626_154500/diagnosis.md`; API send count `0`, product code changed false, source refetch false, generated article patch false. First confirmed gap exactly one: `market_explanation_followthrough_reader_meta_quality_gate_gap`.
- Market-explanation followthrough reader-meta quality gate no-API implementation is complete in `notecode/logs/0626/route_v_market_explanation_followthrough_reader_meta_quality_gate_no_api_impl_20260626_160057/implementation_summary.md`; API send count `0`, product code changed true only in `app/services/draft_followthrough.py` plus focused tests. Replay against `mxse_api_20260626_153053` removed `low_density_bridge_sentence` / `abstract_navigation_phrase`, preserved H1/H2, reached body floor (`1233/1200`), and kept selected excerpts used.
- Market-explanation followthrough reader-meta quality gate one-article API validation is complete in `notecode/logs/0626/mxrq_api_20260626_161500/api_validation_summary.md`; API send count `1`, product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. Preflight passed with `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2`; final article generated, H1 exactly one, H2 `3`, body floor reached (`1233/1200`), quality passed with no issues, selected excerpts used, and human-readability/source-boundary/unsupported-claim/sentence-length/over-editing guards passed.
- Market-explanation acceptance decision is complete in `notecode/logs/0626/route_v_market_explanation_acceptance_decision_no_api_20260626_162756/acceptance_decision.md`; API send count `0`, product code changed false, source refetch false, generated article patch false. Decision is `accepted`, and `market_explanation` is recorded as accepted.
- Announcement editor persona contract one-article API validation is complete in `notecode/logs/0626/route_v_announcement_editor_persona_contract_one_article_api_validation_after_approval_20260626_170000/api_validation_summary.md`; API send count `1`, product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. Preflight passed with `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2`; final article generated, H1 exactly one, H2 sections present, source boundary and announcement self-perspective / notice tone boundary passed, selected excerpt used, but body floor failed (`203` excluding headings; QA `226/900`) and quality failed only on `body_length_below_floor`. Decision is `reject_or_inconclusive`.
- Announcement body-floor no-API diagnosis is complete in `notecode/logs/0626/route_v_announcement_body_floor_reached_failure_diagnosis_no_api_20260626_173000/diagnosis.md`; API send count `0`, product code changed false, source refetch false, generated article patch false. First confirmed gap exactly one: `announcement_draft_writer_selected_excerpt_floor_followthrough_gap`.
- Announcement DraftWriter selected-excerpt floor followthrough one-article API validation is complete in `notecode/logs/0626/route_v_announcement_draft_writer_selected_excerpt_floor_followthrough_one_article_api_validation_after_approval_20260626_194056/api_validation_summary.md`; API send count `1`, product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. Final article generated, H1 exactly one, H2 sections present, body floor reached (`958/900`), quality passed, selected excerpt used, and structural editor floor-loss guard preserved floor-reaching input after structural API raw fell to `671/900`. Decision was `acceptance_candidate`; this API validation owner is completed history.
- Announcement acceptance decision is complete in `notecode/logs/0626/route_v_announcement_draft_writer_selected_excerpt_floor_followthrough_acceptance_decision_no_api_20260626_202716/acceptance_decision.md`; API send count `0`, product code changed false, source refetch false, generated article patch false. Decision is `accepted`.
- Company-introduction front/back editor persona contract retry after API 520 is complete in `notecode/logs/0626/route_v_company_intro_front_back_editor_persona_contract_one_article_api_validation_retry_after_api_520_20260626_231500/api_validation_summary.md`; API send count `1`, product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. Final article generated and H1/H2/source/persona/selected-excerpt/over-editing guards passed, but final body floor failed (`718/1400`) and quality failed only on `body_length_below_floor`.
- Company-introduction body-floor diagnosis is complete in `notecode/logs/0627/route_v_company_intro_body_floor_reached_failure_diagnosis_no_api_20260627_000000/diagnosis.md`; API send count `0`, product code changed false, source refetch false, generated article patch false, prompt/persona tuning false, QA relaxation false. First below-floor stage is DraftWriter (`328/1400`) and first confirmed gap is exactly `company_intro_draft_writer_selected_excerpt_floor_followthrough_gap`.
- Company-introduction DraftWriter selected-excerpt floor followthrough no-API implementation is complete in `notecode/logs/0627/route_v_company_intro_draft_writer_selected_excerpt_floor_followthrough_no_api_impl_20260627_010000/implementation_summary.md`; decision is `implementation_no_api_gate_pass`, API send count `0`, and focused tests / `py_compile` / bloat gates passed.
- Company-introduction DraftWriter selected-excerpt floor followthrough one-article API validation is complete in `notecode/logs/0627/route_v_company_intro_draft_writer_selected_excerpt_floor_followthrough_one_article_api_validation_after_approval_20260627_091448/api_validation_summary.md`; decision is `reject_or_inconclusive`, API send count `1`, product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. Final article generated, H1/H2/source/persona/selected-excerpt/over-editing guards passed, but body floor failed (`331/1400`, QA `375/1400`) and quality failed on `body_length_below_floor` plus `ending_bucket_monotony`.
- Company-introduction body-floor diagnosis after selected-excerpt followthrough is complete in `notecode/logs/0627/route_v_company_intro_body_floor_reached_failure_diagnosis_no_api_20260627_092734/diagnosis.md`; API send count `0`, product code changed false, source refetch false, generated article patch false, prompt/persona tuning false, QA relaxation false. First below-floor stage is DraftWriter (`1155/1400`), largest later loss is structural API raw (`1157/1400` -> `331/1400`), and first confirmed gap is exactly `company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough`.
- Historical next one owner before residual implementation was `route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_no_api_impl`.
- Non-owner boundaries: do not retry API before implementation gate, refetch sources, patch generated article text, pass raw full source documents/source_packets/source_cards, use Route A/writer-only fallback, grow structural-editor prompt/persona as the first owner, relax QA, add phrase-list growth as a substitute, broaden prompt/persona tuning, change selector cap/windowing, or change source-shape detection / claim allocation / caps. Do not accept `company_service_intro` without a new evaluable validation and separate acceptance decision.

## Core Product Rules

- Do not generate final articles directly from long raw sources.
- Convert sources into structured facts before article generation.
- Do not add facts that are not supported by source cards or confirmed claims.
- Keep source extraction, knowledge integration, brief creation, draft writing, style editing, quality checking, and targeted rewriting as separate responsibilities.
- `article_brief` is the single design contract for draft generation.
- `article_knowledge_pack` is the fact contract for generation, editing, checking, and rewriting.
- Japanese first person must be explicit and consistent. Do not mix forms such as `当社`, `弊社`, `私たち`, and `当店`.
- Subject omission is allowed only when the actor remains clear.
- Responsibility, achievements, dates, prices, schedules, promises, and requests must not omit the responsible subject.
- URL acquisition should prefer deterministic public HTML extraction; GPT/web-search retrieval is a fallback, not a way to bypass site restrictions.
- note and Hatena Blog are initial output-style targets. Do not crawl restricted pages, internal APIs, login pages, search pages, or archive pages.
- Check paragraph rhythm, line-break monotony, ending-bucket monotony, and GPT-like frequent words such as `効く` and `第一歩`.
- Use deterministic Japanese stylometry metrics as QA signals: sentence length, paragraph rhythm, endings, connectors, POS patterns, character ratios, lexical diversity, and viewpoint terms.
- Use genre-specific roles and personas, but keep the article in self-perspective mode unless third-party mode is explicitly selected.
- Default first person for company/service/product introduction is `私たち`; use `当社` only when a formal corporate tone is selected.
- Keep config, personas, prompt templates, and runtime code separate. Do not hard-code large persona tables or prompt bodies in Python modules.
- Quality checking must detect unsupported claims, first-person inconsistency, subject ambiguity, zero-anaphora risk, duplication, AI-like phrasing, style mismatch, CTA issues, forbidden phrases, long sentences, ending repetition, and connector repetition.

## AI Coding Rules

- Work from the documents before inventing architecture.
- For Codex CLI `/goal`, follow `docs/GOAL_PLAN.md` phase by phase and slice by slice.
- Keep each change narrow: one issue, one hypothesis, one owner scope.
- Test every slice. On failure, attempt focused repair up to 3 times; after 3 failed attempts, stop and report.
- Do not combine implementation, quality tuning, and broad refactoring in one window.
- Prefer concrete schemas, typed interfaces, and deterministic services over prompt-only behavior.
- Prevent module and prompt bloat: split modules by owner, render prompts from config/persona data, and stop before one prompt or one file owns multiple pipeline stages.
- Add or update tests for behavior that changes.
- Keep instructions concise and verifiable. Move detailed specs out of `AGENTS.md`.
- Stop and report if a task would require weakening source-grounding, lowering QA thresholds, or adding prompt hacks instead of fixing the responsible owner.
- Do not solve quality failures with symptomatic patches such as phrase-by-phrase replacements, one-off prompt additions, or case-specific output tweaks. Diagnose the responsible owner and fix the underlying stage behavior.
- Record meaningful progress in `PROGRESS.md` and implementation history in `WORKLOG.md`.

## Expected Project Shape

```text
app/
  agents/
  config/
  personas/
  schemas/
  prompts/
  services/
  evals/
docs/
  AI_CODING_RULES.md
  ARTICLE_GENRE_POLICY.md
  CONFIG_AND_PERSONA_POLICY.md
  GOAL_PLAN.md
  JAPANESE_STYLE_POLICY.md
  JAPANESE_STYLOMETRY_POLICY.md
  PIPELINE_SPEC.md
  SOURCE_ACQUISITION_POLICY.md
  TECH_STACK.md
```

## Validation Expectations

For documentation-only slices, validation is documentation consistency:

- Required documents exist.
- `AGENTS.md` remains short enough to be reliably loaded by coding agents.
- `TASK.md` describes current executable work.
- `PROGRESS.md` identifies the next narrow owner.
- `ARCHITECTURE.md`, `docs/PIPELINE_SPEC.md`, `docs/CURRENT_ALGORITHM.md`, and Route V docs do not contradict each other.

After implementation starts, each coding slice should report:

- Changed files
- Owner scope
- Tests run
- Remaining blockers
- Whether source-grounding or QA policy changed
