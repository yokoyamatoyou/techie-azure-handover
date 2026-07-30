# コトメイク AGENTS

正本は `C:\tetie\AGENTS.md` です。  
このファイルは `notecode` の作業入口です。

## Current State 2026-06-28 Post-Manual UI Article Type Image Validation

- Latest validation artifact: `notecode/logs/0628/rv_ui_img_20260628_180205/validation_summary.json`.
- Decision: `needs_review`; UI reachability passed; all six article types generated; all six article types produced both text and no-text image variants.
- User feedback before this owner: the previous bundled six-article evaluation set was manually reviewed and judged OK.
- Service invocation counts in this owner: article generation invocations `12`; image generation invocations `12`; successful image variants `24`; Route V/0506 OpenAI terminal send count `52`.
- Accepted/user-visible readiness in this owner: `comparison_guide`, `announcement`, `daily_activity`, and `case_study` passed the validation bundle. `company_service_intro` and `market_explanation` remain `needs_review` because quality gates still fail after allowed regeneration attempts.
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
- Source refetch false; generated article patch false; raw full source handoff false; Route A / writer-only fallback false.
- Focused tests passed (`22 passed`); `py_compile` passed; changed-file bloat passed; prompt bloat none.
- `company_service_intro` remains unaccepted.
- Historical next owner: `route_v_company_intro_draft_writer_live_residual_floor_buffer_one_article_api_validation_after_approval`.

## Historical State 2026-06-27 Post-Diagnosis Override

- Latest diagnosis artifact: `notecode/logs/0627/route_v_company_intro_body_floor_reached_failure_diagnosis_no_api_20260627_160000/diagnosis.md`.
- Source validation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_one_article_api_validation_after_approval_20260627_131500/api_validation_summary.md`.
- Diagnosis decision: `needs_next_owner`; diagnosis API send count `0`; product code changed `false`; source refetch `false`; generated article patch `false`; raw full source handoff `false`.
- Preserved validation facts: decision `reject_or_inconclusive`; validation API send count `1`; DraftWriter `1327/1400`, opening/global/style `1329/1400`, structural API raw/guarded/final `917/1400`, QA `961/1400`; H1 exactly one and H2 sections present; source/persona/selected-excerpt/over-editing/raw-source/fallback guards passed.
- First confirmed gap exactly one: `company_intro_draft_writer_live_residual_floor_miss_after_no_api_replay_gap`.
- Structural editor overcompression is a later observation, not the first owner, because the structural input was already subfloor at `1329/1400`.
- QA/human-readability/sentence issues remain secondary observations; the only QA issue is `body_length_below_floor`.
- `company_service_intro` remains unaccepted.
- Historical next owner: `route_v_company_intro_draft_writer_live_residual_floor_buffer_no_api_impl`.

## Historical State 2026-06-27 Post-Implementation Override

- Latest implementation artifact: `notecode/logs/0627/route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_no_api_impl_20260627_104857/implementation_summary.md`.
- Decision: `implementation_no_api_gate_pass`; API send count `0`; source refetch `false`; generated article patch `false`; raw full source handoff `false`.
- Product code changed only in DraftWriter company-intro residual followthrough scope: `notecode/0506/app/services/company_intro_followthrough.py`; focused test added in `notecode/0506/tests/test_company_intro_residual_followthrough.py`.
- Preserved first_confirmed_gap exactly: `company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough`.
- Saved-artifact replay improved DraftWriter body floor from `1155/1400` to `1409/1400` without API.
- `company_service_intro` remained unaccepted.
- Historical next owner: `route_v_company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough_one_article_api_validation_after_approval`.

## Historical State 2026-06-27 Before Residual Implementation

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
## Current Objective: Route V Main Route

- 通常UIの本文生成主経路は Route V です。
- 可視UIの `記事を生成` は `note\route_v_generation_service.py` から `note\route_v_0506_adapter.py` を通り、workspace 内 `notecode\0506` の structured blog pipeline を実行します。
- Route V route id は `route_v_0506_structured_blog_v1` とします。
- Route A current_mainline / newalgorithm_pipeline / simple_note_pipeline は legacy opt-out 専用です。通常UIの既定値、失敗時 fallback、品質補修の逃げ道として使いません。
- writer-only は旧通常UI本文生成経路として退避します。Route V 失敗時の自動 fallback には使いません。
- 旧本文生成系ファイル群は `C:\tetie\notecode\archive\writer_only_deadcode_archive_20260602\` にarchive済みです。
- rejected route（旧 Route B / Route D / Route E / deepresearch など）は復活させません。
- runtime の既定参照先に Desktop 絶対パスを置きません。Route V は `notecode\0506` のローカル workspace 参照を使います。
- formal UI の Route V は 0506 の configured LLM client boundary を使い、`LocalPipelineClient` を通常UI本文生成の実行 client にしません。
- latest output / quality report / runtime log では `route_v_used=true`, `legacy_body_route_used=false`, `fallback_used=false` を判別できるようにします。
- Route B は廃止済み名称です。`route_b_context_snapshot_2026-06-23` など実在する旧名 artifact / package は legacy-named migration reference としてのみ扱います。
- 現行状態の詳細は `C:\tetie\notecode\ALGORITHM.md` を読む。WORKLOG は履歴です。

## Legacy Route 0506 Notes

以下のRoute 0506記述は履歴参照です。Route V が使う実行 engine の背景ではありますが、通常UI route 方針は上の Current Objective を優先してください。

2026-05-11 時点では、Route 0506 を本文生成の main route として運用し、安定化を継続していました。

## Historical Objective: Route 0506 Main Route Stabilization

- Route 0506 を、安定して良い結果が出ている 0506 ソフトを基準に構築・安定化する。
- 参照元は原則 `C:\tetie\notecode\0506` とする。
- `C:\Users\横山裕明\Desktop\0506` は元の安定参照だが、ローカルコピー `C:\tetie\notecode\0506` に同等の内容がある場合は、Desktop 絶対パスへ依存しない。
- 2026-05-11 に user 明示承認で Route 0506 を UI 本文生成の default main route へ切り替え済み。
- Route A は deprecated legacy opt-out として残すが、Route 0506 失敗時の自動 fallback には使わない。notice は `C:\tetie\notecode\docs\route_a_legacy_opt_out_deprecation_notice_2026-05-12.md` を参照する。
- 次の実作業は、Route 0506 main route の運用信頼性・カテゴリ別品質を `1 issue = 1 narrow hypothesis = 1 owner scope` で安定化する。
- 差分洗い出し後、修正は `1 issue = 1 narrow hypothesis = 1 owner scope` に分ける。

## Required Read Order

Route 0506 / 506 route 構築を触る場合は、次を順番に読む。

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\WORKLOG.md`
4. `C:\tetie\WORKLOG.md`
5. Local 0506 reference:
   - `C:\tetie\notecode\0506\AGENTS.md`
   - `C:\tetie\notecode\0506\README.md`
   - `C:\tetie\notecode\0506\TASK.md`
   - `C:\tetie\notecode\0506\PROGRESS.md`
   - `C:\tetie\notecode\0506\ARCHITECTURE.md`
   - `C:\tetie\notecode\0506\docs\CURRENT_ALGORITHM.md`
   - `C:\tetie\notecode\0506\docs\PIPELINE_SPEC.md`
   - `C:\tetie\notecode\0506\docs\SOURCE_ACQUISITION_POLICY.md`
   - `C:\tetie\notecode\0506\docs\ARTICLE_GENRE_POLICY.md`
   - `C:\tetie\notecode\0506\docs\CONFIG_AND_PERSONA_POLICY.md`
   - `C:\tetie\notecode\0506\docs\JAPANESE_STYLE_POLICY.md`
   - `C:\tetie\notecode\0506\WORKLOG.md`
6. Latest Route 0506 state:
   - `C:\tetie\notecode\docs\route_0506_instruction_window_migration_after_fullness_2026-05-10.md`
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\stage_length_trace.json`
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\claim_allocation_trace.json`
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\decision_before_edit.md`
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\fix_attempt_01\api_validation_summary.json`
   - `C:\tetie\notecode\logs\route_0506_generation_side_fullness_followthrough_20260510\fix_attempt_01\manual_quality_review.md`
7. Prior Route 0506 evidence:
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\article_brief_gap_analysis.json`
   - `C:\tetie\notecode\logs\route_0506_source_surface_article_type_focus_brief_allocation_20260509\selected_span_inventory.json`
   - `C:\tetie\notecode\logs\route_0506_knowledge_pack_single_fact_conflict_20260509\decision.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_saved_source_quality_validation_after_kpfix_20260509\decision.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_api_deep_audit_20260509\instruction_window_report.md`
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\method_check_summary.json`
8. Current notecode Route V implementation:
   - `C:\tetie\notecode\note\route_v_generation_service.py`
   - `C:\tetie\notecode\note\route_v_0506_adapter.py`
   - `C:\tetie\notecode\note\note_writer_app_writer_only_ui.py`
   - `C:\tetie\notecode\note\tests\test_route_v_0506_adapter.py`
   - `C:\tetie\notecode\note\tests\test_note_writer_app_writer_only_ui.py`
   - `C:\tetie\notecode\note\tests\test_note_writer_app_phase01_minimal_ui.py`
9. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`

GPT Image 2 / image generation を触る場合のみ、追加で `C:\tetie\notecode\ALGORITHM.md` の `## 13. GPT Image 2 Image Generation Algorithm` と `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\` を読む。

## Local 0506 Reference Policy

- `C:\tetie\notecode\0506` は Route 0506 構築のローカル安定リファレンス。
- 0506 参照時は、まず次で Desktop 絶対参照を確認する。

```powershell
rg -n -F --glob "!.venv/**" --glob "!**/__pycache__/**" --glob "!*.pyc" -e "Users" -e "Desktop\0506" -e "Desktop\\0506" -e "Desktop/0506" -e "/Users/" "C:\tetie\notecode\0506"
```

- scan は `Users` という一般語も拾うので、行単位で絶対パスかどうかを確認する。
- 2026-05-10 の初回確認では、runtime / docs / tests の Desktop 絶対参照ではなく artifact summary JSON に旧 `Desktop\0506` provenance が残っていた。
- artifact provenance の旧絶対パスは、runtime 依存として扱わない。
- もし runtime / docs / tests に Desktop 絶対参照が見つかった場合は、Route 0506 実装に進む前に、1 owner でローカルコピー参照へ寄せるか、user に block report する。

## Difference Inventory Rule

`C:\tetie\notecode\0506` との差分洗い出しは、実装前に read-only で行う。

推奨 artifact root:

```text
C:\tetie\notecode\logs\route_0506_local_reference_diff_YYYYMMDD\
```

最低限作る artifact:

```text
inventory.md
absolute_reference_scan.txt
file_map_compare.json
pipeline_stage_compare.json
source_surface_compare.json
knowledge_pack_compare.json
article_brief_compare.json
target_length_trace.json
claim_allocation_compare.json
qa_policy_compare.json
decision_before_edit.md
```

比較対象:

- route dispatch / UI bridge
- input contract / saved source handoff
- source acquisition / preprocessing
- source packet density and source identity
- source-card extraction
- knowledge-pack integration and conflict / do-not-infer handling
- article brief target length, section count, source thickness, section purpose, claim allocation
- draft writer payload and prompt handoff
- opening / global consistency / style / structural editor timing
- visible output guard
- QA / stylometry / rewrite trigger
- model, reasoning effort, environment defaults
- observability artifacts and usage ledgers
- tests and fixture coverage

差分 inventory の判断は次のいずれかにする。

```text
decision: needs_next_owner | blocked
next_one_owner:
```

inventory window では product code を変更しない。差分が多くても、次の実装 owner は 1 件だけ選ぶ。

## No-Mixing Rule for Current Owner

For notecode Route V/0506 work, do not mix current handoff, historical records, and evidence artifacts.

- Read current docs first: `notecode/AGENTS.md`, `notecode/0506/AGENTS.md`, `README.md`, `PROGRESS.md`, `docs/CURRENT_ALGORITHM.md`, and owner-specific docs named there.
- Treat `WORKLOG.md` as chronological history. Older owner names in WORKLOG are not current unless the current docs also say so.
- Treat `logs/...` artifacts as evidence. A diagnosis artifact may recommend the next owner, but that owner becomes current only after the current docs are updated.
- If current docs and the newest artifact disagree, stop and report the mismatch. Do not implement, run API validation, or silently choose one source.
- Before implementation or API validation, state one current owner, the files allowed for that owner, and the non-owner boundaries.
- When a validation or diagnosis changes the next owner, update current docs first, then record the handoff in WORKLOG.

## Historical Route V/0506 Quality Owner: 2026-06-23

Route B formal main route dispatch / flags work is historical. Do not use it as the current next owner for 0506 quality work.

Latest Route V evidence:

- baseline validation artifact: `C:\tetie\notecode\logs\0621\route_b_0506_v2_floor_h1_one_api_per_article_20260621_234827\`
- paragraph-depth implementation diagnosis: `C:\tetie\notecode\logs\0621\draft_writer_floor_actuation_runtime_diagnosis_20260622_005034\`
- paragraph-depth API recheck: `C:\tetie\notecode\logs\0622\route_b_0506_v2_paragraph_depth_fix_api_recheck_20260622_122514\`
- latest failure diagnosis: `C:\tetie\notecode\logs\0622\draft_writer_paragraph_depth_fix_api_recheck_failure_diagnosis_20260622_130918\`
- Route V route id: `route_v_0506_structured_blog_v1`
- Route A fallback: false
- writer-only fallback: false
- raw full `source_documents` passed to DraftWriter: false
- H1 contract: reached in 4/4 completed post-fix article types; the 2 missing article types stopped before DraftWriter on API infra errors.
- body floor: reached in 0/4 completed post-fix article types; all completed post-fix articles still emitted `body_length_below_floor`.
- paragraph-depth fix status: implemented and API-rechecked, but did not improve body floor.
- count-based floor actuation redesign: implemented with no-API gate pass (`39 passed`, `py_compile` pass, `inspect_bloat` pass / `failures=[]`).
- count-based API isolation recheck: partial positive but incomplete in `C:\tetie\notecode\logs\0622\route_b_0506_v2_count_based_floor_actuation_api_isolation_recheck_20260622_140222\`; completed 2/6 article types, floor reached 2/2 completed, H1 reached 2/2 completed, quality pass 1/2 completed. Failure diagnosis found likely long artifact path / validation packaging issues plus API 520 infra failures; no rerun was performed in that owner.
- short-path validation packaging recheck: completed in `C:\tetie\notecode\logs\0622\cbsp_1429\`; no-API gate passed (`39 passed`, `py_compile` pass, `inspect_bloat` pass / `failures=[]`), API used yes (`35` sends), product code changed false. The short artifact path fixed the validation packaging gap (`company_service_intro` and `market_explanation` completed), but count-based floor actuation is not user-test ready: completed 5/6 article types, final floor reached 1/5 completed, H1 reached 5/5 completed, quality pass 0/5 completed, body_length_below_floor 4/5 completed. Floor gap improved vs baseline in 5/5 completed comparable types and vs paragraph-depth in 3/3 completed comparable types, but still misses the final floor for most types.
- floor-gap diagnosis: completed in `C:\tetie\notecode\logs\0622\cbsp_1429\floor_gap_diagnosis.md`; API used false, product code changed false. The current count-based paragraph target was met or exceeded in 5/5 completed article types, but draft floor reached only 1/5 and final floor reached 1/5. The residual is not H1 and not a large editor/postprocessor deletion; paragraph count alone is too weak because failing drafts average about 92-98 body chars per paragraph, and small editor reductions can cross the floor when there is no buffer.
- depth-budget contract implementation: complete with no-API gate pass (`39 passed`, `py_compile` pass, `inspect_bloat` pass / `failures=[]`). DraftWriter now adds a bounded source-backed depth budget contract from floor/target chars, section count, assigned claims, and selected excerpts while preserving the H1 contract and representative/selective unassigned-claim boundary. API validation has not been run for this implementation.
- depth-budget one-article API smoke: completed in `C:\tetie\notecode\logs\0622\dbsm_1550\`; API used yes (`6` sends), product code changed false. `market_explanation` reached final floor (`1641/1400`), H1 (`1`), and quality pass, but unassigned-claim enumeration regressed to `true` and manual review found sentence-fragment/punctuation issues.
- depth-budget smoke failure diagnosis: completed in `C:\tetie\notecode\logs\0622\dbsm_1550\smoke_failure_diagnosis.md`; first confirmed gap was `writer_context_assigned_claim_boundary_gap`.
- assigned-claim boundary fix: completed in `C:\tetie\notecode\logs\0622\dbsm_1550\assigned_claim_boundary_fix_summary.md`; no-API gate passed (`143 passed` for full `0506\tests`, focused Route V adapter/UI tests `52 passed`, `py_compile` pass, `inspect_bloat` pass / `failures=[]`).
- assigned-claim boundary API smoke recheck: attempted in `C:\tetie\notecode\logs\0622\dbsm_1550\assigned_claim_boundary_api_smoke_recheck.md`; API used yes (`5` sends), product code changed false, stopped at `article_brief_builder` with OpenAI/API HTTP 520 before DraftWriter, so final floor / H1 / quality / unassigned-claim enumeration were not evaluable.
- Route B context snapshot: `C:\tetie\notecode\plan\route_b_context_snapshot_2026-06-23\`.
- Route B runtime guard: `C:\tetie\notecode\logs\0623\route_b_runtime_legacy_path_guard_20260623_145014\`; focused no-API guard/UI suite passed (`55 passed`), product behavior changed false, API send count 0.
- Source-context handoff diagnosis: completed in `C:\tetie\notecode\logs\0623\route_b_source_context_handoff_diagnosis_20260623_000000\diagnosis.md`; product behavior changed false, API send count 0. First confirmed gap is `draft_writer_excerpt_primary_material_contract_gap`.
- DraftWriter excerpt-primary context contract: completed in `C:\tetie\notecode\logs\0623\route_v_draft_writer_excerpt_primary_context_contract_20260623_154332\implementation_summary.md`; product behavior changed true in `notecode\0506\app\agents\draft_writer.py`, API send count 0, focused DraftWriter tests `8 passed`, Route V guard/UI suite `55 passed`.
- DraftWriter excerpt-primary one-article API smoke: completed in `C:\tetie\notecode\logs\0623\epcs_1557\api_smoke_review.md`; total API terminal sends 12, evaluable retry sends 6 after one harness-only v2 repair, product code changed false, Route A fallback false, writer-only fallback false, raw full `source_documents` passed false, final floor/H1/quality pass true. First confirmed gap is `selected_excerpt_coverage_section_context_gap`.
- Selected excerpt coverage / section-context diagnosis: completed in `C:\tetie\notecode\logs\0623\epcs_1557\selected_excerpt_coverage_section_context_diagnosis.md`; API send count 0, product code changed false, raw full `source_documents` passed false. First confirmed gap remains `selected_excerpt_coverage_section_context_gap`; next one owner is `route_v_selected_excerpt_final_usage_coverage_contract`.
- Selected excerpt final-usage coverage contract: completed in `C:\tetie\notecode\logs\0623\epcs_1557\selected_excerpt_final_usage_coverage_contract_summary.md`; API send count 0, product code changed true in `notecode\0506\app\services\source_excerpt_selector_v2.py` and `source_excerpt_coverage_contract.py`, raw full `source_documents` passed false. No-API replay now covers `S1`/`S2`/`S3` plus final-hinted GENIAC/Gennai excerpts.
- Selected excerpt final-usage one-article API smoke: completed in `C:\tetie\notecode\logs\0623\sefc_1830\api_smoke_review.md`; API send count 6, product code changed false, raw full `source_documents` passed false, final floor/H1/quality pass true, unassigned-claim enumeration false. Live selected excerpts covered `S1`/`S2`/`S3`; live brief/final did not use GENIAC/Gennai, so the prior unexcerpted final-use failure did not recur.
- Selected excerpt final-usage acceptance decision: completed in `C:\tetie\notecode\logs\0623\sefc_1830\selected_excerpt_final_usage_acceptance_decision.md`; API send count 0, product code changed false, raw full `source_documents` passed false. Decision is `accept_with_known_gap`: deterministic replay covers GENIAC/Gennai, but that branch is not live API-exercised.
- Company-introduction source-backed reader bridge + section density validation: completed in `C:\tetie\notecode\logs\0623\company_intro_reader_bridge_section_density_api_validation_20260623_235500\limited_api_validation_summary.md`; API send count 3, product code changed true in Route V/0506 DraftWriter/brief/schema files, raw full `source_documents` passed false, H1 true for all 3. Healthrent passed floor/H1/quality, Sanin reached floor but failed `model_frequent_word`, and Sanrei still missed floor. Decision is `reject`; it left `route_v_company_intro_low_intent_length_floor_contract_repair` as the next owner at the time.
- Company-introduction beat-sheet two-case validation: completed in `C:\tetie\notecode\logs\0623\company_intro_beat_sheet_two_case_corrected_api_validation_20260623_223500\beat_sheet_rejection_diagnosis.md`; corrected API send count 2 after an invalid 2-send run was caught by self-test, raw full `source_documents` passed false, beat instruction present true, but both failed cases still missed floor and quality. The attempted beat-sheet product change was removed after validation. Decision is `reject`; it left `route_v_company_intro_low_intent_length_floor_contract_repair` as the next owner at the time.
- Company-introduction floor feasibility / source-material diagnosis: completed in `C:\tetie\notecode\logs\0623\company_intro_floor_feasibility_source_material_diagnosis_20260623_233500\floor_feasibility_source_material_diagnosis.md`; API send count 0, product code changed false, raw full `source_documents` passed false. It selected `route_v_company_intro_thin_source_excerpt_material_increase` because Sanrei's selected excerpt material was thin (`1531` chars, floor/material ratio `0.914`) while same-shape Healthrent passed with `2600` chars. Beat-sheet remains rejected and removed.
- Company-introduction selector-capacity trace: completed in `C:\tetie\notecode\logs\0624\company_intro_selector_capacity_trace_20260624_000000\selector_capacity_trace.md`; API send count 0, product code changed false, raw full `source_documents` passed false. It confirmed Sanrei is not physically source-thin (`3267` source chars) and can reach `2600` selected chars within current slot/cap limits using high-novelty grounded candidates (`C002`, `C008`, `C012`, `C014`). Decision is `proceed_with_thin_source_excerpt_material_increase`.
- Company-introduction thin source excerpt material increase: completed in `C:\tetie\notecode\logs\0624\route_v_company_intro_thin_source_excerpt_material_increase_20260624_000000\implementation_summary.md`; API send count 0, product code changed true in selector-side files only, raw full `source_documents` passed false. Sanrei selected material increased from `3` / `1531` to `4` / `2600`; Healthrent and Sanin stayed at `2600`; added Sanrei material passed lexical novelty. Decision is `implementation_no_api_gate_pass`.
- Company-introduction thin source excerpt material increase one-article API validation: completed in `C:\tetie\notecode\logs\0624\tmi_sanrei_api_20260624_101500\api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false, Route A fallback false, writer-only fallback false. Sanrei selected excerpts reached `4` / `2600`, H1 reached, unassigned-claim enumeration false, but final floor still failed (`1136/1400`) and quality failed on `body_length_below_floor`.
- Company-introduction floor underproduction after thin material increase diagnosis: completed in `C:\tetie\notecode\logs\0624\route_v_company_intro_floor_underproduction_after_thin_material_increase_failure_diagnosis_20260624_110000\floor_underproduction_diagnosis.md`; API send count 0, product code changed false. It confirmed DraftWriter underproduction (`1300/1400`) plus deterministic edited-stage shrink (`1300` -> `1136`) from `style_postprocessor.postprocess_style()`, not an LLM style-editor prompt.
- Company-introduction stage-floor contract after material increase implementation: completed in `C:\tetie\notecode\logs\0624\route_v_company_intro_stage_floor_contract_after_material_increase_no_api_impl_20260624_112516\implementation_summary.md`; API send count 0, product code changed true in DraftWriter / deterministic style postprocessor only. DraftWriter now uses a stronger company-intro pre-editor floor buffer, and `style_postprocessor` preserves floor-critical reader-meta / bridge material instead of shrinking the surface below the floor-critical range. Focused no-API gates passed.
- Company-introduction stage-floor contract Sanrei API validation: completed in `C:\tetie\notecode\logs\0624\sfc_sanrei_api_20260624_122335\api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false, Route A fallback false, writer-only fallback false. Sanrei reached final floor (`1453/1400`) and H1 (`1`) but failed quality (`sentence_too_long`, `low_density_bridge_sentence`, `abstract_navigation_phrase`). Failure diagnosis selected `route_v_company_intro_floor_success_quality_boundary_repair`.
- Targeted rewrite sentence split grammar safety repair: completed in `C:\tetie\notecode\logs\0624\route_v_targeted_rewrite_sentence_split_grammar_safety_repair_20260624_133328\implementation_summary.md`; API send count 0, product code changed true in `editor_output_safety.py` only. Sanrei no-API replay no longer produces `発足し。` or `（松江会場）」。`.
- Targeted rewrite grammar safety same-source Sanrei API recheck: completed in `C:\tetie\notecode\logs\0624\trg_sanrei_api_20260624_135350\api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false. Grammar break stayed fixed, but final floor failed (`1084/1400`) and quality failed.
- Company-introduction reader-inference to source-action no-API implementation: completed in `C:\tetie\notecode\logs\0624\route_v_company_intro_reader_inference_to_source_action_contract_no_api_20260624_192852\implementation_summary.md`; API send count 0, product code changed true only in `draft_writer.py` plus focused tests. It normalizes company-intro self-authored residual payload fields from reader/outside-observer inference into company-side source-backed action/value guidance without phrase-list growth or Sanrei text patching.
- Company-introduction reader-inference to source-action Sanrei API validation: completed in `C:\tetie\notecode\logs\0624\route_v_company_intro_reader_inference_to_source_action_contract_one_article_api_validation_20260624_194041\api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false, Route A fallback false, writer-only fallback false. Sanrei passed reader-inference bridge review (`0` disallowed frames) and H1 (`1`) but missed final floor (`1166/1400`) and quality failed only on `body_length_below_floor`.
- Company-introduction reader-inference contract floor regression diagnosis: completed in `C:\tetie\notecode\logs\0624\route_v_company_intro_reader_inference_contract_floor_regression_diagnosis_20260624_200131\floor_regression_diagnosis.md`; API send count 0, product code changed false. It found the compact company-side action/value contract removed the target frame without prompt bloat, but the Sanrei floor miss started at DraftWriter underproduction (`1175` draft -> `1166` final), not editor shrink.
- Company-introduction reader-inference contract Sanrei API validation after diagnosis: completed in `C:\tetie\notecode\logs\0624\route_v_company_intro_reader_inference_contract_sanrei_one_article_api_validation_after_diagnosis_20260624_204407\api_validation_summary.md`; API send count 1, product code changed during validation false, raw full `source_documents` passed false, Route A / writer-only fallback false. Sanrei again missed floor at DraftWriter output (`1215/1400` draft, `1219/1400` final), H1 passed (`1`), and quality failed. This was later superseded by the user-approved front/back editor persona trial.
- Company-introduction front/back editor persona two-API trial: completed in `C:\tetie\notecode\logs\0624\route_v_company_intro_front_back_editor_persona_two_api_trial_after_encoding_guard_20260624_213222\api_trial_summary.md`; API send count 2 as a user-approved exploratory exception, encoding preflight pass, product code changed during trial false, raw full `source_documents` passed false, Route A / writer-only fallback false. Sanrei reached final floor (`1452/1400`), H1 (`1`), and reader-frame marker pass (`0` hits), but quality failed (`sentence_too_long`, `model_frequent_word`). This is not acceptance.
- Company-introduction front/back editor persona one-API refinement: completed in `C:\tetie\notecode\logs\0624\route_v_company_intro_front_back_editor_persona_one_api_refinement_trial_after_two_pass_20260624_214820\api_trial_summary.md`; API send count 1, encoding preflight pass, product code changed during trial false, raw full `source_documents` passed false. Sanrei reached final floor (`1502/1400`), H1 (`1`), and reader-frame marker pass (`0` hits), but quality still failed (`sentence_too_long`, `model_frequent_word`). This is not acceptance.
- Cross-genre editor persona contract config no-API implementation: completed in `C:\tetie\notecode\logs\0624\route_v_cross_genre_editor_persona_contract_config_no_api_impl_20260624_223244\implementation_summary.md`; API send count 0, product code changed true only in compact config/persona contract data, renderer/preflight service, and focused tests. The six-genre matrix, rendered prompt bloat check, and encoding preflight check all passed. Full 0506 suite still has existing non-owner bloat failures in `article_brief_source_shape_v2.py` and `style_postprocessor.py`; this owner did not relax thresholds or refactor those modules.
- Cross-genre non-announcement second editor policy no-API revision: completed in `C:\tetie\notecode\logs\0624\route_v_cross_genre_non_announcement_editor_pass_policy_no_api_revision_20260624_225013\policy_revision_summary.md`; API send count 0, product code changed true only in compact persona config, renderer/preflight service, and focused tests. `announcement` has no second pass; the other five genres have short second editor roles; shared second-pass rules live once in config.
- Cross-genre editor persona contract editor-stage wiring no-API implementation: completed in `C:\tetie\notecode\logs\0625\route_v_cross_genre_editor_persona_contract_editor_stage_wiring_no_api_impl_20260625_002659\implementation_summary.md`; API send count 0, product code changed true only in the editor-stage wiring helper, editor agents, pipeline runner wiring, and focused tests. The rendered contract now reaches editor agent instructions; local deterministic editor behavior is preserved through `LocalPipelineClient`; `PipelineObserver` records editor-stage instructions.
- Cross-genre editor persona contract comparison-guide one-API validation after wiring: completed in `C:\tetie\notecode\logs\0625\route_v_cross_genre_editor_persona_contract_comparison_guide_one_api_validation_after_wiring_20260625_090000\api_validation_summary.md`; API send count 1, product code changed false, editor-stage instruction contract present, source_fact / llm_general_context separation acceptable, unsupported ranking / best-claim false, third-party viewpoint false, raw full `source_documents` false, Route A / writer-only fallback false, and quality pass true. Decision is reject_or_inconclusive because H1 count was `3`, not exactly `1`.
- Comparison-guide H1 failure diagnosis: completed in `C:\tetie\notecode\logs\0625\route_v_cross_genre_editor_persona_contract_comparison_guide_failure_diagnosis_no_api_20260625_091412\h1_failure_diagnosis.md`; API send count 0, product code changed false. The first confirmed gap is `draft_writer_local_renderer_section_heading_level_h1_contract_gap`: `comparison_guide` local pre-API draft rendered each `article_brief.sections[].heading` as H1. It selected `route_v_draft_writer_section_heading_level_h1_contract_no_api_impl`.
- DraftWriter/local draft section heading level H1 contract implementation: completed in `C:\tetie\notecode\logs\0625\route_v_draft_writer_section_heading_level_h1_contract_no_api_impl_20260625_093857\implementation_summary.md`; API send count 0, product code changed true only in `notecode\0506\app\services\local_draft_renderer.py` plus focused test. Local deterministic replay from draft through final reached exactly one H1 at every stage and preserved the three `comparison_guide` section headings as H2.
- Comparison-guide heading-level one-article API validation after approval: completed in `C:\tetie\notecode\logs\0625\route_v_comparison_guide_heading_level_one_article_api_validation_after_approval_20260625_101206\api_validation_summary.md`; API send count 1, product code changed during validation false, draft / opening / global / style / OpenAI structural raw / structural guarded / final all preserved exactly one H1, and the three `comparison_guide` section headings stayed H2. source_fact / llm_general_context separation, unsupported ranking / best-claim, third-party viewpoint, raw source handoff, fallback, prompt bloat, algorithm bloat, and quality checks all passed. Decision is `acceptance_candidate`.
- Comparison-guide opening subject-specificity no-API diagnosis: completed in `C:\tetie\notecode\logs\0625\route_v_comparison_guide_opening_subject_specificity_no_api_diagnosis_20260625_105657\opening_subject_specificity_diagnosis.md`; API send count 0, product code changed false. First confirmed gap is `comparison_guide_editor_stage_opening_subject_specificity_contract_gap`; it selected `route_v_comparison_guide_editor_stage_opening_subject_specificity_contract_no_api_impl`.
- Comparison-guide opening subject-specificity editor-stage contract no-API implementation: completed in `C:\tetie\notecode\logs\0625\route_v_comparison_guide_editor_stage_opening_subject_specificity_contract_no_api_impl_20260625_115625\implementation_summary.md`; API send count 0, product code changed true only in `notecode\0506\app\personas\editor_persona_contracts.yaml`, and no-API render / bloat / conflict / focused tests passed.
- Comparison-guide opening subject-specificity one-article API validation: completed in `C:\tetie\notecode\logs\0625\route_v_comparison_guide_opening_subject_specificity_one_article_api_validation_after_approval_20260625_121019\api_validation_summary.md`; API send count 1, product code changed during validation false, editor-stage contract reached the structural editor, candidates and four axes appeared in the opening, H1/H2/source handoff/fallback guards passed, but the opening still omitted the comparison target category and quality failed on `connector_repetition`. Decision is `reject_or_inconclusive`.
- Comparison-guide opening subject-specificity failure diagnosis: completed in `C:\tetie\notecode\logs\0625\route_v_comparison_guide_opening_subject_specificity_no_api_failure_diagnosis_20260625_122602\failure_diagnosis.md`; API send count 0, product code changed false. The first confirmed gap is `comparison_guide_article_brief_comparison_target_category_field_gap`: the category existed in target_reader / C001 but not as a first-class article_brief field. `connector_repetition` was a separate stylometry substring-boundary issue from `部門をまたいで` / `部署をまたいで`, not the same root cause.
- Comparison-guide article_brief category field no-API implementation: completed in `C:\tetie\notecode\logs\0625\route_v_comparison_guide_article_brief_comparison_target_category_field_no_api_impl_20260625_131141\implementation_summary.md`; API send count 0, product code changed true only in article_brief schema/builder plus focused tests. `comparison_target_category` is derived from existing target_reader / confirmed-claim material, excluded from the OpenAI strict response schema, and reaches editor-stage payloads in no-API replay.
- Comparison-guide category field one-article API validation: completed in `C:\tetie\notecode\logs\0625\route_v_comparison_guide_category_field_one_article_api_validation_after_approval_20260625_132712\api_validation_summary.md`; API send count 1, product code changed during validation false, `comparison_target_category` reached the structural editor payload, the final opening naturally included `社内ナレッジ管理ツール`, three candidate names, and three axes, H1/H2/source handoff/fallback guards passed, quality passed, prompt/algorithm bloat false. Decision is `acceptance_candidate`.
- Comparison-guide category field acceptance decision: completed in `C:\tetie\notecode\logs\0625\route_v_comparison_guide_category_field_acceptance_decision_no_api_20260625_134814\acceptance_decision.md`; API send count 0, product code changed false. Decision is `accepted`; next owner selected is `route_v_case_study_editor_persona_contract_one_article_api_validation_after_approval`.
- Case-study editor persona contract one-article API validation: completed in `C:\tetie\notecode\logs\0625\route_v_case_study_editor_persona_contract_one_article_api_validation_after_approval_20260625_140859\api_validation_summary.md`; API send count 1, product code changed false, same saved source packet reused, editor-stage contract and `case_study` structural-editor second pass present, H1/H2/source-boundary/fallback/raw-source guards passed, but final QA failed only on `paragraph_rhythm_monotony`. Decision is `reject_or_inconclusive`; next owner selected is `route_v_case_study_paragraph_rhythm_monotony_failure_diagnosis_no_api`.
- Case-study paragraph-rhythm failure diagnosis: completed in `C:\tetie\notecode\logs\0625\route_v_case_study_paragraph_rhythm_monotony_failure_diagnosis_no_api_20260625_143023\diagnosis.md`; API send count 0, product code changed false. First confirmed gap is `structural_editor_missing_knowledge_pack_payload_for_case_study_rhythm_repair`; next owner selected is `route_v_case_study_structural_editor_knowledge_pack_payload_contract_no_api_impl`.
- Case-study structural-editor knowledge-pack payload contract: completed in `C:\tetie\notecode\logs\0625\route_v_case_study_structural_editor_knowledge_pack_payload_contract_no_api_impl_20260625_151509\implementation_summary.md`; API send count 0, product code changed true only in compact structural-editor payload wiring and focused tests. Payload now carries compact confirmed claims / source card ids / section material without raw source handoff. No-API gates passed; next owner selected is `route_v_case_study_structural_editor_knowledge_pack_payload_contract_one_article_api_validation_after_approval`.
- Historical case-study structural-editor payload contract API validation attempt: attempted in `C:\tetie\notecode\logs\0625\route_v_case_study_structural_editor_knowledge_pack_payload_contract_one_article_api_validation_after_approval_20260625_143720\api_validation_summary.md`; API send count 0, product code changed false, and validation blocked before API by Windows path-length packaging error. Its `route_v_case_study_api_infra_unblock_no_api` handoff is superseded by the compact no-API implementation artifact above.
- Case-study structural-editor knowledge-pack payload contract API validation: completed in `C:\tetie\notecode\logs\0625\route_v_case_study_structural_editor_knowledge_pack_payload_contract_one_article_api_validation_after_approval_20260625_152645\api_validation_summary.md`; API send count 1, product code changed false, compact structural-editor knowledge payload visible, raw full source handoff false, Route A / writer-only fallback false, H1/H2/source-attribution/quality/over-editing gates passed, and decision was `acceptance_candidate`.
- Case-study structural-editor knowledge-pack payload contract acceptance decision: completed in `C:\tetie\notecode\logs\0625\route_v_case_study_structural_editor_knowledge_pack_payload_contract_acceptance_decision_no_api_20260625_154025\acceptance_decision.md`; API send count 0, product code changed false, decision is `accepted`, and next owner selected is `route_v_daily_activity_editor_persona_contract_one_article_api_validation_after_approval`.
- Daily-activity editor persona contract API validation: attempted in `C:\tetie\notecode\logs\0625\route_v_daily_activity_editor_persona_contract_one_article_api_validation_after_approval_20260625_172250\api_validation_summary.md`; API send count 1, product code changed false, prompt/persona preflight passed, source refetch false, raw full source handoff false, Route A / writer-only fallback false, and validation blocked by OpenAI/API HTTP 520 before final article generation. Next owner selected is `route_v_daily_activity_api_infra_failure_diagnosis_no_api`.
- Daily-activity API infra failure diagnosis: completed in `C:\tetie\notecode\logs\0625\route_v_daily_activity_api_infra_failure_diagnosis_no_api_20260625_191006\api_infra_failure_diagnosis.md`; API send count 0, product code changed false, prompt/persona tuning false, source refetch false, raw full source handoff false, Route A / writer-only fallback false. The prior 520 blockage is retry-eligible because the compact knowledge context was present and quality was not evaluable.
- Daily-activity retry after API 520: completed in `C:\tetie\notecode\logs\0625\route_v_daily_activity_editor_persona_contract_one_article_api_validation_retry_after_api_520_20260625_194402\api_validation_summary.md`; API send count 1, product code changed false, same source packet reused, source refetch false, raw full source handoff false, Route A / writer-only fallback false. Final article generated, H1 exactly one, H2 section headings, self-perspective consistency, unsupported emotion/result/numeric claim guard, third-party reviewer voice guard, strong CTA guard, rhythm/ending/connector guard, compact structural-editor knowledge payload visibility, prompt bloat, and algorithm bloat passed. Decision is `reject_or_inconclusive` because `source_near_expansion_only`, `quality_pass`, and `over_editing_absent` failed; first confirmed gap is `source_near_expansion_only`.
- Daily-activity structural-editor scene-material preservation no-API implementation: completed in `C:\tetie\notecode\logs\0625\route_v_daily_activity_structural_editor_scene_material_preservation_no_api_impl_20260625_204042\implementation_summary.md`; API send count 0, product code changed true only in compact structural-editor instruction/payload boundary and focused tests. No-API gate passed; next owner selected is `route_v_daily_activity_structural_editor_scene_material_preservation_one_article_api_validation_after_approval`.
- Daily-activity structural-editor scene-material preservation one-article API validation: completed in `C:\tetie\notecode\logs\0625\route_v_daily_activity_structural_editor_scene_material_preservation_one_article_api_validation_after_approval_20260625_205543\api_validation_summary.md`; API send count 1, product code changed false, source refetch false, raw full source handoff false, Route A / writer-only fallback false, compact knowledge context and `scene_material_preservation` payload visible, scene categories retained, but quality failed on `sentence_too_long` and the article still drifted toward announcement/list guidance. Decision is `reject_or_inconclusive`; next owner selected is `route_v_daily_activity_source_near_expansion_only_failure_diagnosis_no_api`.
- Daily-activity source-near expansion failure diagnosis: completed in `C:\tetie\notecode\logs\0625\route_v_daily_activity_source_near_expansion_only_failure_diagnosis_no_api_20260625_214751\diagnosis.md`; API send count 0, product code changed false, source refetch false, article patch false, prompt/persona tuning false, QA relaxation false. First confirmed gap is `daily_activity_article_brief_auxiliary_notice_source_role_boundary_gap`; next owner selected is `route_v_daily_activity_article_brief_auxiliary_notice_source_role_contract_no_api_impl`.
- Daily-activity article_brief auxiliary notice source-role contract implementation: completed in `C:\tetie\notecode\logs\0625\route_v_daily_activity_article_brief_auxiliary_notice_source_role_contract_no_api_impl_20260625_220845\implementation_summary.md`; API send count 0, product code changed true only in allowed article_brief/source-shape files, source refetch false, article patch false, raw full source handoff false, prompt/persona growth false, and no-API gates passed.
- Daily-activity source-role contract one-article API validation: completed in `C:\tetie\notecode\logs\0625\daily_activity_source_role_contract_one_article_api_validation_after_approval_20260625_231002\api_validation_summary.md`; API send count 1, product code changed false, source refetch false, raw full source handoff false, Route A / writer-only fallback false. Route B runtime env activated `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2`, and live `article_brief` / structural payload carried `daily_activity_source_role_contract`, but final quality failed only on `body_length_below_floor` (`441/1200`).
- Daily-activity source-near expansion failure diagnosis after source-role contract: completed in `C:\tetie\notecode\logs\0625\route_v_daily_activity_source_near_expansion_only_failure_diagnosis_no_api_20260625_232859\diagnosis.md`; API send count 0, product code changed false, source refetch false, article patch false, prompt/persona tuning false, QA relaxation false. First confirmed gap is `daily_activity_draft_writer_selected_excerpt_scene_expansion_followthrough_gap`; next owner selected is `route_v_daily_activity_draft_writer_selected_excerpt_scene_expansion_followthrough_no_api_impl`.
- Daily-activity DraftWriter scene expansion API validation after env-preflight fix: completed in `C:\tetie\notecode\logs\0626\daily_activity_draft_writer_scene_expansion_one_article_api_validation_after_approval_20260626_092626\api_validation_summary.md`; API send count 1, product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. Preflight passed with `ROUTE_V_ARTICLE_BRIEF_ALGORITHM=v2`; `daily_activity_source_role_contract` and `selected_source_excerpts` were visible/effective; H1/H2/source-near/over-editing guards passed. Decision is `reject_or_inconclusive` because quality failed only on `body_length_below_floor` (`884/1200`).
- Daily-activity quality-pass failure no-API diagnosis: completed in `C:\tetie\notecode\logs\0626\route_v_daily_activity_quality_pass_failure_diagnosis_no_api_20260626_095107\diagnosis.md`; API send count 0, product code changed false, source refetch false, generated article patch false. First confirmed gap exactly one: `structural_editor_live_api_floor_loss_guard_gap`. The first below-floor stage is the live structural editor API output (`style` 1200 -> `structural_api_raw` 856), and `guard_editor_output` accepted the subfloor output unchanged (`structural_api_guarded` 856; final 856). DraftWriter, selected excerpt usage, source-role contract, final copy shrink, selector cap, and QA measurement delta are not first owners.
- Daily-activity structural-editor floor-loss guard no-API implementation: completed in `C:\tetie\notecode\logs\0626\route_v_daily_activity_structural_editor_floor_loss_guard_no_api_impl_20260626_100159\implementation_summary.md`; API send count 0, product code changed true only in allowed guard/pipeline/test files. Latest replay reverted structural API raw `856/1200` back to the floor-reaching style input `1200/1200`.
- Daily-activity structural-editor floor-loss guard one-article API validation: completed in `C:\tetie\notecode\logs\0626\daily_activity_structural_editor_floor_loss_guard_one_article_api_validation_after_approval_20260626_100740\api_validation_summary.md`; API send count 1, product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. The live guard blocked structural API raw `704/1200` and final stayed floor-reaching `1200/1200`, but quality failed only on `sentence_too_long`. Decision is `reject_or_inconclusive`.
- Daily-activity quality-pass failure diagnosis after floor-loss guard: completed in `C:\tetie\notecode\logs\0626\route_v_daily_activity_quality_pass_failure_diagnosis_no_api_20260626_102004\diagnosis.md`; API send count 0, product code changed false, source refetch false, generated article patch false. First confirmed gap exactly one: `targeted_rewrite_sentence_split_limit_followthrough_gap`; deterministic targeted rewrite reduced max sentence length from `121` to `96` but left two sentences over the configured `90` char limit.
- Targeted rewrite sentence split followthrough no-API implementation: completed in `C:\tetie\notecode\logs\0626\route_v_targeted_rewrite_sentence_split_limit_followthrough_no_api_impl_20260626_103925\implementation_summary.md`; API send count 0, product code changed true only in `notecode\0506\app\services\editor_output_safety.py` with focused tests in `notecode\0506\tests\test_editor_output_guard.py`. Replay against `20260626_100740` reduced max sentence length to `85` with no over-limit sentences and preserved floor/H1/H2.
- Daily-activity targeted rewrite sentence split followthrough one-article API validation: completed in `C:\tetie\notecode\logs\0626\daily_activity_targeted_rewrite_sentence_split_followthrough_one_article_api_validation_after_approval_20260626_110732\api_validation_summary.md`; API send count 1, product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. Final article generated, H1/H2/body floor/quality/source-near/source-role/selected-excerpt/floor-loss guard/over-editing checks passed, and `sentence_too_long` was absent.
- Daily-activity targeted rewrite sentence split followthrough acceptance decision: completed in `C:\tetie\notecode\logs\0626\route_v_daily_activity_targeted_rewrite_sentence_split_followthrough_acceptance_decision_no_api_20260626_112809\acceptance_decision.md`; API send count 0, product code changed false, decision is `accepted`, and `daily_activity` is recorded as accepted.
- Validation runtime preflight genre-expectation no-API implementation: completed in `C:\tetie\notecode\logs\0626\route_v_validation_runtime_preflight_genre_expectation_no_api_impl_20260626_122213\implementation_summary.md`; API send count 0, product code changed true only in validation harness/test scope, product article generation behavior changed false. `daily_activity_source_role_contract_expected=false` is now normal metadata for `market_explanation`, while the common Route V preflight gates remain required.

Historical completed owner before residual implementation:

```text
route_v_company_intro_body_floor_reached_failure_diagnosis_no_api
```

Completed in `notecode\logs\0627\route_v_company_intro_body_floor_reached_failure_diagnosis_no_api_20260627_092734\diagnosis.md` with `needs_next_owner` and zero API sends. Product code changed false, source refetch false, generated article patch false, prompt/persona tuning false, and QA relaxation false. First below-floor stage is DraftWriter (`1155/1400`), largest later loss is structural API raw (`1157/1400` -> `331/1400`), and first confirmed gap is exactly `company_intro_draft_writer_residual_floor_miss_after_selected_excerpt_followthrough`.

Historical completed owner:

```text
route_v_company_intro_body_floor_reached_failure_diagnosis_no_api
```

Completed in `notecode\logs\0627\route_v_company_intro_body_floor_reached_failure_diagnosis_no_api_20260627_160000\diagnosis.md` with `needs_next_owner` and zero API sends. Product code changed false, source refetch false, generated article patch false, prompt/persona tuning false, and QA relaxation false. First below-floor stage is DraftWriter (`1327/1400`), structural API overcompression is a later observation from already-subfloor input (`1329/1400` -> `917/1400`), and first confirmed gap is exactly `company_intro_draft_writer_live_residual_floor_miss_after_no_api_replay_gap`.

Latest completed owner:

```text
route_v_company_intro_draft_writer_live_residual_floor_buffer_acceptance_decision_no_api
```

Completed in `notecode\logs\0627\route_v_company_intro_draft_writer_live_residual_floor_buffer_acceptance_decision_no_api_20260627_134555\acceptance_decision.md` with `accepted` and zero API sends in the acceptance owner. Product code changed false, source refetch false, generated article patch false, raw full source handoff false, Route A / writer-only fallback false. The source validation used one API send and passed final floor/H1/H2/quality/source/persona/selected-excerpt/over-editing gates. `company_service_intro` is now accepted, and all six intended genres are accepted.

Historical next owner before release readiness inventory:

```text
route_v_all_genres_accepted_release_readiness_inventory_no_api
```

Scope: no-API release/readiness inventory after all six intended Route V genres are accepted.

Allowed files: release/readiness inventory artifact files and current docs/WORKLOG sync if next owner or readiness status changes; product code changes remain out of scope.

Non-owner boundaries: no additional API send, source refetch, generated article patch, raw full source material handoff, Route A / writer-only fallback, selector cap/windowing change, source-shape detection or claim-allocation/cap change, QA threshold or repair-acceptance relaxation, broad prompt/persona tuning, or product-code change.

## Hard Boundaries

- Route A current mainline は frozen / immutable として扱う。
- Route V は UI 本文生成の only normal main route として扱う。
- Route B / Route A / writer-only は廃止済み本文ルートとして復活させない。Route V 失敗時の自動 fallback を入れない。
- Route A を再生成しない。
- URL refetch をしない。
- Route A fallback を使わない。
- old rejected routes を戻さない。
- raw full `source_documents` pass で解決しない。
- QA thresholds を緩めない。
- `repair_acceptance` を緩めない。
- broad prompt tuning をしない。
- persona sprawl をしない。persona を触る場合は単独 owner とし、artifact で必要性を証明する。
- new repair loop を追加しない。
- prompt bloat / module bloat を増やさない。
- Desktop 0506 の絶対パスを runtime 既定参照にしない。

## Allowed Work

- read-only diff inventory
- runtime reachability inventory / allowlist artifacts
- legacy path guard tests, only after an inventory owner selects that implementation owner
- deterministic trace scripts / artifacts
- local 0506 reference の absolute-reference scan
- narrow adapter-side fix, only when the diff proves the owner
- focused tests for the touched owner
- docs / artifact updates needed for handoff

API execution:

- default は no API。
- API が必要な場合は、local preflight と artifact inventory を先に完了する。
- user から明示承認がある場合のみ `OPENAI_API_KEY` environment を使う。
- Route 0506 validation は原則 `gpt-5.4-mini` / reasoning `high`。
- 1 validation window は最大 1 API run を基本とする。

## Current Mainline / Legacy Planning Docs

次は legacy planning reference であり current source of truth ではない。Route V/0506 構築では、上の 0506 read order と `C:\tetie\notecode\plan\route_b_context_snapshot_2026-06-23\` を優先する。

- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\`
- `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\`
- `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
- `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`

pre-2026-04-02 records を current read order に戻さない。2026-05 以前の archive は 2026-06-23 docs cleanup の削除対象。completed reference package / frozen architecture package は reopen しない。

## Current Success Paths

Retired legacy current_mainline reference:

```text
C:\tetie\notecode\note\current_mainline_runner.py
-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
```

Route V main UI body generation path:

```text
C:\tetie\notecode\note\route_v_generation_service.py
-> C:\tetie\notecode\note\route_v_0506_adapter.py
-> C:\tetie\notecode\0506\app\services\pipeline_runner.py
```

Route V は default main route。Route B / Route A / writer-only は通常UI本文生成の fallback として使わない。

## Responsibility Map / Local Worklog

- notecode 固有の責務別ディレクトリ図は `C:\tetie\notecode\docs\directory_map.md` を参照する。
- notecode 固有の責務分け、module split、保持/削除判断の詳細記録は `C:\tetie\notecode\WORKLOG.md` に残す。
- `C:\tetie\WORKLOG.md` は横断の current source of truth と大きな判断に限定し、詳細な分割経緯は notecode 側へ逃がす。

## Report Contract

Route V 作業 window の完了報告には最低限これを含める。

```text
decision: route_v_confirmed | blocked
artifact_root:
product_code_changed:
api_send_count:
absolute_reference_scan:
desktop_absolute_reference_required:
diff_inventory_completed:
first_confirmed_gap:
changed_files:
tests:
manual_japanese_naturalness_note:
next_one_owner:
legacy_body_route_regenerated: false
url_refetched: false
legacy_body_route_fallback_used: false
old_routes_reopened: false
raw_full_source_documents_passed: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
AGENTS_update_needed:
WORKLOG_update_needed:
```

## Failure History

opt-in shadow route / naturalness experiment が reject / park になった場合は、live artifact 配下に `failure_note.md` を残す。必要に応じて `C:\tetie\notecode\docs\shadow_route_failure_history.md` へ要約と参照先を追記する。

失敗履歴は PROGRESS / WORKLOG に詳細展開しない。PROGRESS / WORKLOG には必要な導線だけを置き、失敗原因・Do not repeat・park 判断は artifact と `shadow_route_failure_history.md` に残す。
