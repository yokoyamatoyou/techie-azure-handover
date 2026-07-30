# PROGRESS

## Current Status

- Package status: limited_user_trial_ready_with_company_intro_review_awareness
- Current phase: pre-user-trial `company_introduction` patch-scope handling implementation complete
- Date: 2026-04-28 JST
- Product code change in this check: yes, owner-local `company_intro patch-scope helper`
- Prompt / threshold / repair-count / guard / UI implementation change: short conditional company_intro repair preservation wording only; no thresholds, repair count, guard, or UI change
- Generation rerun: yes, `company_intro_patch_scope_handling_20260428-115318`
- Image generation: yes, company_introduction 3/3 image pairs succeeded
- UI server startup: no new startup; existing 8080 listener was used/checked
- Additional validation: focused helper / company_intro / current_mainline_runner / announcement / comparative smoke tests passed
- AGENTS update: not needed
- WORKLOG update: completed

## 2026-04-28 Company Introduction Patch-Scope Handling Implementation

- Artifact:
  - `C:\tetie\notecode\logs\company_intro_patch_scope_handling_20260428-115318\`
- Scope:
  - added `note\simple_note_pipeline\company_intro_patch_scope.py`
  - minimal helper call in `note\simple_note_pipeline\pipeline.py`
  - short conditional company_intro repair preservation wording through `note\simple_note_pipeline\prompt_builder.py`
  - focused tests in `note\tests\test_simple_note_pipeline.py`
- Kept untouched:
  - `repair_acceptance.py`
  - `quality_guard.py`
  - `hidden_late_validation.py`
  - `company_intro_source_contract.py`
  - `current_mainline_persona_trial.py`
  - `title_strategy.py`
  - image generation code
  - target length, repair count, fingerprint threshold, source-grounding threshold
- Validation:
  - `py_compile` passed.
  - helper / prompt focused tests: `9 passed, 252 deselected`.
  - company_intro / patch / repair prompt tests: `118 passed, 143 deselected`.
  - current_mainline_runner company_intro tests: `13 passed, 67 deselected`.
  - quality guard regression: `22 passed`.
  - announcement smoke: `3 passed, 77 deselected` and `14 passed, 247 deselected`.
  - comparative smoke: `2 passed, 78 deselected` and `24 passed, 237 deselected`.
- Live rerun:
  - `company_introduction`: `3/3 success`, body present `3/3`.
  - `SYS_PIPELINE_FAILURE`: `0/3`.
  - `blocked_output_redacted=true`: `0/3`.
  - internal leakage: `0/3`.
  - lead / heading route-drift phrase hits: `0/3`.
  - image pairs: `3/3` success.
  - announcement smoke: success.
  - comparative_review smoke: success.
- Manual review:
  - business / product-service / support scope remained visible.
  - titles / headings meet minimum note-readability.
  - no source-outside claim observed in visible review.
  - residual: some company-name-centered voice and explanatory-card heading tone remain; run 1 image display text repeats `データ入力`.
- Current trial decision:
  - `announcement`: `user_trial_ok`.
  - `comparative_review`: `user_trial_ok_with_normal_review`.
  - `company_introduction`: `limited_user_trial_ok_with_review_awareness`.

## 2026-04-28 Company Introduction Patch-Scope Handling Docs-Only Planning

- Artifact:
  - `C:\tetie\notecode\plan\company_intro_patch_scope_handling_2026-04-28\`
- Scope:
  - docs-only design整理
  - product code / prompt / threshold / repair count / guard / UI / image generation は変更していない
  - tests / rerun / UI server startup は行っていない
- Reason:
  - 直前診断の `B + D mixed` を受け、`company_introduction` の route drift phrase が original lead / heading にある場合、現行 patch path が `LEAD` と見出し名を保持するため repair candidate に悪い語が温存される問題を設計化した
  - prompt_builder-only edit は、`pipeline.py` 側の patch-scope acceptance が同じ lead / heading stability を要求するため不足
  - acceptance-only edit も、prompt が bad surface preservation を促すため不足
- Decision:
  - `company_introduction`: hold 継続
  - next implementation owner は `company_intro patch-scope helper` 1つに固定
  - `pipeline.py` へ直接条件を積まず、helper + existing pipeline hook に閉じる
  - `prompt_builder.py` は必要な場合だけ既存 preservation wording の conditional replacement に留める
  - `repair_acceptance.py` は clean candidate が出るまで触らない
- Next gate if implementation starts:
  - company_intro patch-scope helper tests
  - focused company_intro / current_mainline_runner / quality guard tests
  - `company_introduction` 3回 rerun
  - announcement / comparative_review smoke
- AGENTS update:
  - not needed; entrance route unchanged

## 2026-04-28 Company Introduction Repair Prompt Assembly Diagnosis

- Artifact:
  - `C:\tetie\notecode\logs\company_intro_repair_prompt_assembly_20260428-112438\`
- Classification:
  - `B + D` mixed.
  - `D`: `相談の入口` / `相談前` were already present in the original draft or raw source-derived material in attempts 1 and 2.
  - `B`: repair prompt surface / patch-scope behavior made those surfaces too sticky by preserving `LEAD` and heading names while route drift can be located in those exact surfaces.
  - Not `E`: repair candidates were not clean; `repair_acceptance.py` remains untouched.
  - Not pure `C`: public `company_introduction_source_contract` material was neutralized; raw/private source packet still contains source-backed `相談前`, but public contract labels and grounding are not the direct regression.
- Trace summary:
  - attempt 1: original lead/body and repair candidate retained `相談の入口`.
  - attempt 2: original body/headings and repair candidate retained `相談前` / `相談の入口`.
  - attempt 3: no tracked route phrase, but candidate still had no material fingerprint/naturalness improvement.
  - all attempts: `repair_rejected=true`, `acceptance_rejection_reason=company_intro_fingerprint_not_improved`.
- Owner decision:
  - no product-code owner selected for this window.
  - Primary observed owner is `note\simple_note_pipeline\prompt_builder.py` repair prompt surface, but a prompt_builder-only edit would conflict with existing `pipeline.py` patch-scope acceptance rules that also require lead/title/hashtags and heading list stability.
  - Fixing both would violate the one-owner boundary.
- Validation:
  - `py_compile`: passed.
  - company_intro / company_introduction / hidden_late focused tests: `104 passed, 149 deselected`.
  - current_mainline_runner company_intro tests: `13 passed, 67 deselected`.
  - quality guard regression: `22 passed`.
  - announcement smoke: `3 passed, 77 deselected`.
  - comparative_review smoke: `2 passed, 78 deselected`.
- Current trial decision:
  - `company_introduction`: hold.
  - `announcement`: smoke passed.
  - `comparative_review`: smoke passed.
- Next owner:
  - separate owner decision around company-introduction patch-scope handling where route-drift phrases in lead/headings cannot be repaired while patch path requires lead/heading preservation.
  - Do not touch `repair_acceptance.py` alone until a clean repair candidate is shown to be rejected only by over-strict acceptance.

## 2026-04-28 Company Introduction Hidden Late / Repair Boundary

- Artifact:
  - `C:\tetie\notecode\logs\company_intro_hidden_late_repair_boundary_20260428-095429\`
- Classification:
  - `A`: `hidden_late_validation` は route drift を検出して repair に接続していたが、repair direction が会社紹介方向へ戻し切れていなかった。
  - `C` は触らない。repair candidate は `相談の入口` / `相談前` / 相談軸見出しを残す、または自然さが十分改善しないため、acceptance 側で通す候補ではなかった。
- Scope:
  - owner-local to `note\simple_note_pipeline\hidden_late_validation.py`
  - tests in `note\tests\test_simple_note_pipeline.py`
  - no `repair_acceptance.py`, `prompt_builder.py`, `company_intro_source_contract.py`, broad `pipeline.py`, guard/postprocess/image/comparative/announcement code, thresholds, length mode, or repair count changes.
- Fix:
  - company_introduction route drift phrase repair を、現在の事業内容、扱う製品・サービス、対応範囲、事業の特徴、source-backed な体制・拠点・背景・扱う領域へ戻す instruction に限定して強化。
  - source-backed な問い合わせ窓口への短い言及余地は残し、単純禁止にはしなかった。
  - 3回目のより強い A edit は `SYS_PIPELINE_FAILURE` を再発させたため rollback。最終 retained fix は2回目。
- Validation:
  - `py_compile` passed.
  - hidden_late focused tests: `15 passed, 238 deselected`.
  - company_intro / company_introduction tests: `98 passed, 155 deselected`.
  - current_mainline_runner company_intro tests: `13 passed, 67 deselected`.
  - quality guard regression: `22 passed`.
  - announcement smoke: `3 passed, 77 deselected`.
  - comparative_review smoke: `2 passed, 78 deselected`.
- Live rerun:
  - `company_introduction`: `3/3 publishable_success`, body present `3/3`.
  - `SYS_PIPELINE_FAILURE`: `0/3`.
  - `blocked_output_redacted=true`: `0/3`.
  - internal leakage: `0/3`.
  - image pair success: `3/3`.
  - residual: `相談の入口` remained in `2/3`; `相談前` remained in `1/3`; repair rejected `3/3`.
- Product code hash diff:
  - changed: `note\simple_note_pipeline\hidden_late_validation.py` only.
- Judgment:
  - `company_introduction` remains `hold` for user trial.
  - next owner should not be C unless a future artifact shows a clean repair candidate rejected only by an over-strict fingerprint-only condition.

## 2026-04-28 Company Introduction Naturalness Residual

- Artifact:
  - `C:\tetie\notecode\logs\company_intro_naturalness_residual_20260428-085333\`
- Classification:
  - `B`: `company_intro_source_contract` が optional な `pre_contact_decision` / 相談導線系 source material を public/writer-facing contract 側で強く押しすぎ、`相談前` / `相談の入口` へ戻る圧を作っていた。
- Scope:
  - owner-local to `note\simple_note_pipeline\company_intro_source_contract.py`
  - tests in `note\tests\test_simple_note_pipeline.py`
  - no `prompt_builder.py`, `current_mainline_persona_trial.py`, `title_strategy.py`, broad `pipeline.py`, image logic, comparative/announcement code, target length, repair count, fingerprint threshold, or source-grounding threshold changes.
- Fix:
  - company_intro の public source-contract label/value を neutralize し、`pre_contact_decision` の public label を `事前確認材料` に変更。
  - private slot / source grounding は維持しつつ、generation/repair に見える source packet から `相談前` / `相談の入口` / `相談入口` / `問い合わせ前` の直接圧を減らした。
  - `pre_contact_decision_missing_final` は diagnostic boolean のまま残し、hard repair trigger ではなく `optional_late_missing:pre_contact_decision` degraded trigger に変更。
- Validation:
  - `py_compile` passed.
  - source-contract focused tests: `30 passed, 222 deselected`.
  - company_intro / company_introduction / hidden_late_validation tests: `103 passed, 149 deselected`.
  - current_mainline_runner company_intro tests: `13 passed, 67 deselected`.
  - quality guard regression: `22 passed`.
  - announcement smoke: `publishable_success`, `runtime_reason_code=OK`.
  - comparative_review smoke: `publishable_success`, `runtime_reason_code=OK`.
- Live rerun:
  - `company_introduction`: `3/3 publishable_success`, body present `3/3`.
  - `SYS_PIPELINE_FAILURE`: `0/3`.
  - `blocked_output_redacted=true`: `0/3`.
  - internal leakage: `0/3`.
  - image pairs: `3/3` success.
  - residual phrase totals: `相談前=1`, `相談の入口=3`, all other tracked NG phrases `0`.
  - all 3 attempts still had `hidden_late_validation:company_intro`, `repair_required=true`, `repair_applied=false`, `repair_rejected=true`.
- Current trial decision:
  - `company_introduction`: hold. Body/image success is recovered, but naturalness / route-drift / repair-rejected residuals remain.
  - `announcement`: smoke passed.
  - `comparative_review`: smoke passed.
- Next owner:
  - `A / C` boundary: `hidden_late_validation.py` with repair effectiveness / repair trigger handling.
  - Secondary only if route phrase recurrence is gone: `quality_guard.py` for explanation-card rhythm and ending monotony.
- AGENTS update:
  - not needed.

## 2026-04-28 Comparative Review Source-Fit Input Gate Fix

- Artifact:
  - `C:\tetie\notecode\logs\comparative_review_source_fit_input_gate_20260428-073154\`
- Classification:
  - `C`: 評価軸や差分は source にあるが、comparative_review の `source_substance` bucket に入っていなかった。
- Scope:
  - owner-local to `note\newalgorithm_pipeline\input_contract.py`
  - focused tests in `note\tests\test_current_mainline_runner.py`
  - no `prompt_builder.py`, broad `pipeline.py`, quality threshold, output guard, repair acceptance, image logic, UI adapter, length, repair count, or fingerprint / source-grounding threshold changes.
- Fix:
  - comparative_review 限定で raw source content から比較候補、比較前提、評価軸、候補差分、向く条件、注意点 / tradeoff、確認順を確認する source-substance assessor を追加。
  - metadata / filename だけでは通さず、薄い候補概要 source は引き続き `INP_SOURCE_CONTEXT_INSUFFICIENT` / `missing_buckets=["source_substance"]` で止める。
- Before / after:
  - previous `comparative_review` attempt_2: `source_fit.status=block`, `missing_buckets=["source_substance"]`, `input_decision=clarify`.
  - same stronger file source after fix: `source_fit.status=pass`, `source_grounding_status=resolved`, `input_decision.reason_code=OK`.
  - negative thin comparative source: still `source_fit.status=block`, `missing_buckets=["source_substance"]`.
- Validation:
  - `py_compile` passed.
  - focused source-fit tests: `4 passed`.
  - current-mainline comparative/source-fit tests: `5 passed`.
  - simple comparative tests: `24 passed`.
  - newalgorithm comparative tests: `31 passed` after fixing one owner-local regression.
  - full `test_current_mainline_runner.py`: `80 passed`.
  - combined comparative bundle: `57 passed`.
  - targeted regression smoke: `4 passed`.
- Live rerun:
  - `comparative_review`: `3/3 publishable_success`.
  - blocker-equivalent `meeting_transcription_stronger_source`: `publishable_success`, `runtime_reason_code=OK`.
  - body present `3/3`, `blocked_output_redacted=true` `0/3`, internal leakage `0/3`.
  - image from successful comparative body: `with_text=success`, `without_text=success`, title image article-aligned.
  - announcement smoke: `publishable_success`.
  - company_introduction smoke: `publishable_success`, existing naturalness / hidden late validation warnings remain review-awareness residual.
- Current trial decision from this blocker:
  - `comparative_review`: source-fit pre-generation blocker mitigated; user trial can proceed with normal source-backed review.
  - `announcement`: proceedable.
  - `company_introduction`: body smoke passes but remains review-awareness / separate owner for naturalness residual.
- AGENTS update:
  - not needed.

## 2026-04-28 Overnight User Trial Blocker Work

- Artifact:
  - `C:\tetie\notecode\logs\overnight_user_trial_blocker_work_20260428-015609\`
- Scope:
  - Phase A implementation allowed only for `company_introduction` `SYS_PIPELINE_FAILURE`.
  - Phase B/C/D were diagnosis-only.
  - No `pipeline.py`, `prompt_builder.py`, `blog_image_auto.py`, `quality_guard`, fingerprint threshold, source grounding threshold, or repair count changes.
- Phase A diagnosis:
  - Original `company_introduction` failure had a repair candidate, but it was not safe to accept by relaxing acceptance because hidden route-drift wording still remained.
  - Immediate hard fail included `wrong_article_type_drift`; root was a false positive where source-backed `申込書` / `申込書類` matched the announcement-style `申込` trigger.
  - Follow-up rerun exposed a second source-contract close issue, `support_scope_boundary_missing_final`, where final section support scope was too easy to lose.
- Phase A fix:
  - `note\simple_note_pipeline\company_intro_source_contract.py`
    - narrowed the `申込` detector so application-document names do not trigger wrong article type drift.
    - strengthened company-introduction source-contract repair instruction to avoid consultation-route wording and keep source-backed support scope into late/final section.
  - `note\tests\test_simple_note_pipeline.py`
    - added focused regression coverage.
- Phase A validation:
  - `py_compile` passed.
  - `test_simple_note_pipeline.py -k "company_intro or company_introduction or hidden_late_validation"` -> `102 passed`.
  - `test_current_mainline_runner.py -k "company_intro or company_introduction"` -> `13 passed`.
  - `test_simple_note_quality_guard.py -q` -> `22 passed`.
  - Rerun after fix attempt 2:
    - `company_introduction`: `3/3 publishable_success`
    - body present: `3/3`
    - `SYS_PIPELINE_FAILURE`: `0/3`
    - `blocked_output_redacted=true`: `0/3`
    - internal leakage: `0/3`
    - image pairs: `3/3` success
- Residual:
  - `company_introduction` still has `hidden_late_validation:company_intro`, `repair_required=true`, `repair_rejected=true`, and route-drift wording (`相談前`, `相談の入口`, and once `この会社の`).
  - One rerun body included typo-like `量量産前`.
  - Therefore `company_introduction` remains `hold` for user trial even though the `SYS_PIPELINE_FAILURE` blocker is mitigated.
- Phase B diagnosis:
  - `comparative_review` attempt_2 remains `INP_SOURCE_CONTEXT_INSUFFICIENT`.
  - Primary next owner: `comparative_review` source-fit / input gate, because `source_fit.status=block` and `missing_buckets=["source_substance"]` were set before generation despite 3 file sources.
- Phase C diagnosis:
  - Real file upload was not completed; this session did not expose a usable Browser-plugin file-upload callable.
  - Existing artifact still supports source retention and explicit-generation-only behavior, but upload remains manual QA gap.
- Phase D diagnosis:
  - The `小ロ` truncation was already present in `display_text` and the image prompt, so it is a copy-shortening issue, not GPT Image 2 rendering jitter.
  - Next owner: `image_cover_strategy` display-copy token-boundary shortening.
- Current trial decision from this blocker work:
  - `announcement`: proceedable.
  - `comparative_review`: hold.
  - `company_introduction`: hold.
  - AGENTS update: not needed.

## 2026-04-28 Full Commercial Quality Check Before User Test

- Artifact:
  - `C:\tetie\notecode\新しいフォルダー\新しいフォルダー (7)\`
- Scope:
  - `announcement` / `comparative_review` / `company_introduction`
  - current mainline body generation, GPT Image 2 `with_text` and `without_text`, UI operation check, visual/manual review, summary docs
  - no product code, prompt, persona, source contract, hidden late validation, repair acceptance, pipeline, guard, image prompt, or UI implementation changes
- CLI generation:
  - `announcement`: `3/3 publishable_success`, body present, `blocked_output_redacted=false`, internal leakage `0`, image `with_text 3/3`, image `without_text 3/3`
  - `comparative_review`: `2/3 publishable_success`, `1/3 input_required_block`; blocked case remained `INP_SOURCE_CONTEXT_INSUFFICIENT` after stronger-source rerun
  - `company_introduction`: `2/3 publishable_success`, `1/3 SYS_PIPELINE_FAILURE`; successful cases still carry company-intro naturalness / repair rejection warnings
- UI operation:
  - file upload was attempted but not completed through the Browser plugin because the exposed locator API did not provide `setInputFiles`; this is recorded as a validation gap, not as a product-code conclusion.
  - source URL list remained visible through type/detail changes.
  - `内容を確認` / `不足を確認` did not start generation by themselves; explicit generation button was required.
  - `announcement`: body and images completed after image-completion rerun; no fatal visible markers.
  - `comparative_review`: explicit generation reached quality stop; body hidden; no visible internal leakage / redaction / SYS marker.
  - `company_introduction`: body and images completed; no visible internal leakage / redaction / SYS marker.
- Visual review:
  - self-perspective is stable in generated `announcement` and generated `comparative_review`; generated `company_introduction` mostly keeps `私たち` / company self-view but remains somewhat explanation-card-like.
  - source-outside claim was not observed in generated successful drafts; `company_introduction` attempt 3 produced `legal:unverified_legal_citation` warning and needs review.
  - `company_introduction` attempt 3 `with_text` image title is truncated (`小ロ`), so image title owner remains needed.
- Product code hash:
  - `NO_PRODUCT_CODE_HASH_DIFF`
- Current decision from this run:
  - `announcement`: `limited_user_trial_OK`
  - `comparative_review`: `hold`
  - `company_introduction`: `hold`
- Next owner candidates:
  - `comparative_review` source-fit / input gate
  - `comparative_review` UI quality-stop path
  - `company_introduction` hidden late validation / repair acceptance
  - `company_introduction` rhythm / naturalness
  - image title layout/copy truncation
  - manual UI file upload validation
- AGENTS update:
  - not needed.

## 2026-04-28 Company Introduction Image-Copy Blocker Follow-Up

- Artifact:
  - `C:\tetie\notecode\logs\company_intro_image_cover_strategy_gpt_image2_20260428-000938\`
- Scope:
  - `image_cover_strategy.py` company_introduction strategy only.
  - No body-generation changes, no `blog_image_auto.py`, no `image_config.py`, no `llm_client.py`, no GPT Image 2 API parameter changes, no retry/fail-open changes.
- Fix:
  - company_introduction display-copy strategy now favors business content, products/services, handled fields, company characteristics, region/facility cues, and source-backed business terms.
  - consultation / pre-contact / reader-contact framing is rejected for company_introduction while preserved for `branding`.
- Deterministic checks:
  - `LNG、どこから相談する？`: rejected.
  - `Webの相談`: rejected.
  - `支援範囲、どこまで？`: rejected.
  - `ガス・電気・住まいを支える`: allowed.
  - Sanin fallback: `ガス・電気・住まいを支える`.
  - Kyoto fallback: `データ化・デジタル化事業`.
- Live image result:
  - `company_introduction` 2 cases, 4 variants succeeded.
  - `sanin_energy_business`: `with_text` / `without_text` success, display text `LNGまで担う事業内容`, retry `0`.
  - `kyoto_data_business`: `with_text` / `without_text` success, display text `データ化・デジタル化事業`, retry `0`.
  - Visual review: Japanese text readable; copies fit company-introduction cover usage; no-text variants had no observed extra text, numbers, logos, or watermark.
- Checks:
  - `py -m py_compile C:\tetie\notecode\note\image_cover_strategy.py` -> passed.
  - `py -m pytest C:\tetie\notecode\note\tests\test_blog_image_auto.py -q` -> `20 passed`.
  - `py -m pytest C:\tetie\notecode\note\tests\test_image_prompt_mixin_structure.py C:\tetie\notecode\note\tests\test_slice5_image_prompt_quarantine_boundary.py -q` -> `5 passed`.
- Decision:
  - The image-title blocker recorded in the 2026-04-27 final smoke is resolved for limited user trial.
  - First user-trial recommendation remains: proceed with `announcement` / `comparative_review` / `company_introduction`.
  - Residual review awareness for company_introduction remains around body voice / self-perspective, not image copy.
- AGENTS update:
  - not needed.

## 2026-04-27 Final Body/Image Smoke After Hidden Late Validation Owner

- Artifact:
  - `C:\tetie\notecode\logs\pre_user_trial_final_body_image_smoke_20260427-232234\`
- Scope:
  - current mainline generation only; product code was not changed.
  - no prompt / persona / source contract / hidden late validation / repair acceptance / pipeline / guard / image implementation changes.
  - generated `announcement` / `comparative_review` / `company_introduction` three times each.
  - generated one `with_text` + `without_text` image pair from the first successful body per article type.
- Body result:
  - `announcement`: `3/3 publishable_success`, body present, `blocked_output_redacted=false`, internal leakage `0`.
  - `comparative_review`: `3/3 publishable_success`, body present, `blocked_output_redacted=false`, internal leakage `0`.
  - `company_introduction`: `3/3 publishable_success`, body present, `blocked_output_redacted=false`, internal leakage `0`.
- Source retention:
  - `announcement`: source_count `2/2`, `source_types={"file": 2}`.
  - `comparative_review`: source_count `3/3`, `source_types={"url": 3}`.
  - `company_introduction`: source_count `4/4`, `source_types={"url": 4}`.
- Company introduction self-perspective:
  - attempt 2 is clear `私たち` voice.
  - attempts 1 / 3 use company-name-centered company introduction, but do not read as third-party review or consultation-entry articles.
  - current-business / services /対応範囲 first structure held.
- Company introduction NG expression check:
  - requested exact phrases `読者の立場で見ると` / `最初の接点は` / `相談前` / `相談の入口` / `相談窓口` / `導入手順` / `この会社は` / `この会社の` / `公開情報では` / `欠かせない`: `0/3`.
  - `相談` single word remains only in source-backed housing /創エネ /省エネ context and is not treated as stop-level recurrence.
- Image result:
  - `announcement`: both variants success. Copy `2026年4月15日、何を確認する？` fits the notice.
  - `comparative_review`: both variants success. Copy `承認フロー、どこまで回す？` fits the comparison axis.
  - `company_introduction`: both variants success, article success was not affected. However copy `LNG、どこから相談する？` is consultation-oriented and too generic for the improved company-introduction body.
- Runtime / UI stability:
  - 8080 listener alive before / during / after.
  - app log excerpt contained no `deleted client` / `deleted slot` / `ERR_CONNECTION_REFUSED` / `Accept failed`.
  - browser snapshot confirmed the UI exposed `確認後に生成を開始` disabled before confirmation.
  - focused UI gate checks passed: `43 passed`.
- Product code hash:
  - `NO_PRODUCT_CODE_HASH_DIFF`.
- Decision:
  - `announcement`: user trial OK.
  - `comparative_review`: user trial OK with normal source-backed review.
  - `company_introduction`: limited user trial OK with review awareness.
- Residual owner candidates:
  - `image_cover_strategy`: company_introduction title-image copy can still drift toward consultation framing.
  - `repair_acceptance.py` is not promoted from this smoke because company_introduction body NG phrases did not recur.
- AGENTS update:
  - not needed.

## 2026-04-27 Docs-Only Closeout After Company Intro Observability Fix

- Artifact:
  - `C:\tetie\notecode\logs\company_intro_source_grounding_observability_fix_20260427-100546\`
- Evidence files:
  - `visual_review.md`
  - `ui_validation_summary.json`
  - `before_after_grounding_comparison.json`
  - `product_code_hash_diff.json`
- Note:
  - The requested `summary.json` was not present in the artifact directory; the files above are the used evidence.
- Scope:
  - docs-only synchronization of user-trial readiness.
  - No product code, prompt, persona, source contract, algorithm, threshold, repair count, quality/output guard, pipeline, blog image auto, or module split changes.
  - No UI server startup.
  - No additional validation / rerun.
- Latest first-trial recommendation:
  - proceed to limited user trial with all three article types.
- Latest first-trial readiness:
  - `announcement`: user trial OK, 3/3 `publishable_success`, images success.
  - `comparative_review`: user trial OK with normal review, 3/3 `publishable_success`, images success.
  - `company_introduction`: limited user trial OK with review awareness.
- `company_introduction` source grounding fix evidence:
  - existing artifact recompute: `0.2/0.4/0.4` -> `1.0/1.0/1.0`
  - weak reflection: `3/3` -> `0/3`
  - UI rerun: 3/3 `publishable_success`
  - source grounding: `5/5`
  - images generated successfully
  - `product_code_hash_diff.json`: `NO_PRODUCT_CODE_HASH_DIFF`
- Product code relationship:
  - the preceding source grounding observability fix changed product code owner-limited to `quality_observability_mixin.py`.
  - this docs-only closeout changed no product code.
  - validation reports no unexpected hash drift beyond the intended owner.
- Residual:
  - `company_introduction` self-perspective still leans third-party explanatory.
  - `repair_required=true` / `repair_rejected=true` remains 3/3, but does not block publishable output in the latest rerun.
  - title/body may still need human review for note-like voice.
- Next after trial:
  - company_intro self-perspective consumption.
  - repair rejection effectiveness.
- Pytest:
  - not run; docs-only closeout using existing artifacts and WORKLOG.
- AGENTS update:
  - not needed.

## 2026-04-26 Minimal UI Confirmation After Redaction Mismatch Fix

- Artifact:
  - `C:\tetie\notecode\logs\pre_user_trial_min_ui_confirmation_20260426-221608\`
- Scope:
  - `company_introduction` 1 attempt only
  - representative copy button check
  - representative legal panel check
  - runtime stability / app.log / product code hash checks
- Result:
  - `company_introduction`: `publishable_success / OK`
  - saved `article_type`: `branding`
  - `semantic_article_key`: `company_introduction`
  - body exists: yes, `1267` chars
  - `blocked_output_redacted=false`
  - visible redacted block: not observed
  - internal term leakage: not observed in visible article/full_text
  - source-outside claim: not observed in manual visible review
- Representative checks:
  - copy: passed, `記事形式でコピー` showed visible `コピーしました` toast
  - legal panel: passed, panel opened and showed `生成後チェック済み（再計算）` / `問題なし`
- Runtime stability:
  - 8080 listener retained before / during / after
  - deleted client / deleted slot traceback: not observed in current window
  - `ERR_CONNECTION_REFUSED`: not observed
  - `Accept failed`: not observed
  - product code hash diff: `NO_PRODUCT_CODE_HASH_DIFF`
- Decision:
  - user trial can proceed under `USER_TRIAL_RUNBOOK.md` limits.
  - keep first trial limited to `announcement`, `comparative_review`, and `company_introduction`.
  - do not run full-flow rerun or broad smoke matrix before the first user trial.

## 2026-04-26 Pre User Trial UI Validation

- Report:
  - `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\PRE_USER_TRIAL_UI_VALIDATION_2026-04-26.md`
- Artifact:
  - `C:\tetie\notecode\logs\pre_user_trial_ui_validation_20260426-205318\`
- Scope:
  - `announcement` x 3
  - `comparative_review` x 3
  - `company_introduction` x 3
  - image check intended once per article type
- Result:
  - `announcement`: attempts 1-2 `ui_harness_failure`; attempt 3 `publishable_success / OK`
  - `comparative_review`: attempt 1 `publishable_success / OK` with image success; attempt 2 `ui_harness_failure`; attempt 3 `input_required_block / SYS_QUALITY_WARNINGS_UNRESOLVED / blocked_output_redacted=true`
  - `company_introduction`: 3/3 `ui_harness_failure`; attempts 2-3 hit `ERR_CONNECTION_REFUSED`
- Stop conditions:
  - `blocked_output_redacted=true`
  - 8080 listener loss during validation
  - runtime tracebacks around deleted NiceGUI client/slot state
- Not completed:
  - `announcement` image check
  - `company_introduction` image check
  - representative copy button check
  - representative legal panel check
- Negative checks:
  - startup ImportError / ModuleNotFoundError not observed in captured excerpt
  - internal-term leakage not observed in completed captured attempts
  - source-outside claim not observed in completed captured attempts
  - product code hash diff `NO_PRODUCT_CODE_HASH_DIFF`
- Judgment:
  - first user trial should stop until the UI/server stability issue and blocked-output behavior are reviewed.

## 2026-04-26 User Trial Runbook Addendum

- Created docs-only user-facing runbook:
  - `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\USER_TRIAL_RUNBOOK.md`
- Created printable checklist:
  - `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\CHECKLIST.md`
- Scope:
  - startup steps
  - first-trial order limited to `announcement`, `comparative_review`, `company_introduction`
  - source input conditions per article type
  - success / review warning / input block / stop boundaries
  - image generation confirmation and fail-open boundary
  - error report artifacts
  - do-not-use source list
  - hold / source_needed article types
  - result record template
- Product code / prompt / threshold / repair count / guard / pipeline / UI / image generation behavior:
  - unchanged
- AGENTS update:
  - not needed
- Pytest:
  - not run; docs-only runbook/checklist update

## Evidence Summary

- `current_mainline_full_flow_acceptance_review_2026-04-26` classified 10 `publishable_success` and 6 `input_required_block` attempts from existing artifacts, with attempt errors `0`, internal-term leakage `0`, and source-outside claim observed `0`.
- `post_phase06a_success_path_ui_smoke_20260426-200726` confirmed:
  - `announcement`: `publishable_success` / `OK` / image success
  - `comparative_review`: `publishable_success` / `OK` / image success
  - representative copy action OK
  - representative legal panel OK
  - product code hash diff `NO_PRODUCT_CODE_HASH_DIFF`
  - final `18080` listener `NO_LISTENER_18080`
- `article_type_self_perspective_quality_validation_record_continue_rerun_20260427-085139` confirmed:
  - `announcement`: 3/3 `publishable_success`, image 6/6 success
  - `comparative_review`: 3/3 `publishable_success`, image 6/6 success
- `company_intro_source_grounding_observability_fix_20260427-100546` confirmed:
  - `company_introduction`: 3/3 `publishable_success`
  - source grounding `5/5`, ratio `1.0`, no `source_grounding:weak_reflection`
  - images success, 2 files per attempt
  - `repair_required=true` / `repair_rejected=true` remains 3/3
  - self-perspective remains weak / third-party explanatory
- GPT Image 2 image generation remains post-success and fail-open per `ALGORITHM.md` section 13.
- Responsibility split is parked after Phase 06A/06B; no additional split is part of this readiness package.

## Readiness Classification

| Article type | Classification | Reason |
|---|---|---|
| `announcement` | `user_trial_ok` | 3/3 `publishable_success`, images success, no leakage |
| `comparative_review` | `user_trial_ok_with_normal_review` | 3/3 `publishable_success`, images success; keep normal source-backed review |
| `company_introduction` | `limited_user_trial_ok_with_review_awareness` | source grounding weak reflection fixed; UI rerun 3/3 `publishable_success`; source grounding 5/5; images success; self-perspective and repair rejection residual remain |
| `explanatory_article` | `ready_with_review_warning` | 2/2 success; metadata denominator stop not reproduced; thin-watch caveat remains |
| `industry_analysis` | `ready_with_review_warning` | 2/2 success; fixture/thin source caveat remains |
| `product_introduction` | `source_needed` | mixed result, thin source caveat, must-cover miss on blocked attempt |
| `daily_story` | `source_needed` | synthetic source caused source grounding `0.0`; both attempts blocked |
| `case_study` | `hold` | both attempts blocked with legal/guarantee warnings |
| non-company `branding` values stance | `hold` | production UI route mismatch; not a usable generic non-company branding validation |

## First User-Trial Targets

1. `announcement`
   - Best first trial because source is easy to prepare and post-Phase06A evidence covers article success, image success, copy, and legal panel visibility.
2. `comparative_review`
   - Use as the second trial with normal review. It is suitable when 2-3 options and common comparison axes are available.
3. `company_introduction`
   - Use as the third trial with review awareness. Check self-perspective, third-party explanatory lean, title strength, image copy fit, and source-outside claim.

Second-wave candidates:

- `explanatory_article`
- `industry_analysis`

Not first-wave:

- `product_introduction`
- `daily_story`
- `case_study`
- non-company `branding` values stance

## Recommended Source Conditions

- `announcement`
  - change content
  - effective date/time
  - target users
  - old-flow handling
  - preparation items
  - day-of checks
  - preferred shape: one main notice source plus one FAQ/checklist source
- `comparative_review`
  - 2-3 options
  - common evaluation axes
  - option differences
  - fit conditions
  - tradeoffs / cautions
  - next confirmation step
  - price or plan only when source-backed
- `company_introduction`
  - current business
  - customer situation or entry point
  - support scope boundary
  - operating process steps
  - pre-contact decision material
  - optional proof signal
  - avoid history / representative message / philosophy-only source

## Warning / Stop Boundary

Acceptable warning:

- `review_required_draft`
- `SYS_QUALITY_WARNINGS_UNRESOLVED` when body exists and manual review finds no internal leakage or source-outside claim
- repair warning / `repair_required` / `repair_rejected`
- voice weakness
- title weakness
- thin/source caveat warning
- image-only fail-open warning

Stop and report:

- internal-term leakage: `SYS_*`, `source_grounding`, `contract_alignment`, `must_cover`, `PATCH_SCOPE`, `persona`, `trial`, `hidden`
- source-outside claim
- unsupported price / plan / result / vendor superiority claim
- guarantee or legal-risk assertion
- empty body
- `blocked_output_redacted=true`
- UI/server failure
- `case_study` guarantee / stealth-like legal warning
- image failure that blocks article success

## Image Generation Trial Target

- Primary: `announcement`
- Secondary: `comparative_review`
- Third: `company_introduction` with review awareness

Keep image generation as post-success fail-open. `with_text` or `without_text` single-variant failure is a warning, not an article-generation failure.

## Next Action

Proceed with:

- `A: limited user trial with announcement / comparative_review / company_introduction`

Do not run:

- full-flow rerun
- broad smoke matrix
- additional split implementation

If a check is requested before trial despite this package judgment, run only one smoke case and prefer `announcement`.

After the limited user trial, split residual follow-up into:

- `company_intro` self-perspective consumption
- repair rejection effectiveness

## Verification

- Package docs created:
  - `README.md`
  - `TASK.md`
  - `PROGRESS.md`
  - `ROLLBACK.md`
  - `EXECUTION_PROMPT.md`
- `C:\tetie\WORKLOG.md` updated.
- Product code not edited by this docs-only closeout.
- UI server not started by this docs-only closeout.
- Additional validation not run by this docs-only closeout.
- Pytest not run; docs-only readiness closeout using existing artifacts and WORKLOG.

---

## 2026-04-28 Image Display-Copy De-Dup Final Smoke

Artifact:

- `C:\tetie\notecode\logs\image_display_copy_dedup_final_smoke_20260428-122606\`

Status:

- Final polish completed for image display-copy de-duplication.
- The previous company-introduction image copy symptom `データ入力のデータ入力` is now deterministically rejected/falls back.
- No body-generation code, pipeline, prompt_builder, repair, quality, source contract, hidden late validation, image prompt body, image API params, or UI behavior was changed.

Validation:

- `py_compile`: passed
- `note/tests/test_blog_image_auto.py`: `22 passed`
- focused display/fallback/company/announcement/comparative slice: `13 passed, 9 deselected`
- final smoke:
  - `announcement`: body present, `runtime_reason_code=OK`, image success
  - `comparative_review`: body present, `runtime_reason_code=OK`, image success
  - `company_introduction`: body present, `runtime_reason_code=OK`, image success

Image review:

- company-introduction with_text display text: `データ入力と業務整理`
- duplicate display-copy: none observed
- consultation-route image copy: none observed
- with_text Japanese text: readable
- without_text: no readable extra text, digits, logo, signature, or watermark observed

Decision:

- `announcement`: `user_trial_ok`
- `comparative_review`: `user_trial_ok_with_normal_review`
- `company_introduction`: `limited_user_trial_ok_with_review_awareness`
- overall first trial set remains: proceed to limited user trial with `announcement` / `comparative_review` / `company_introduction`

Residual risk:

- GPT Image 2 typography remains model-generated and should be checked during trial.
- broader `company_introduction` voice/title/body craft residuals remain review-awareness items and were intentionally not handled by this image display-copy owner.

---

## 2026-04-28 Limited User Trial Run

Artifact:

- `C:\tetie\notecode\logs\limited_user_trial_run_20260428-123943\`

Scope:

- Normal-mode limited user trial for:
  - `announcement`
  - `comparative_review`
  - `company_introduction`
- Product code was not changed.
- Prompt / persona / source contract / patch-scope / repair / quality / image strategy were not changed.
- UI operation, generation, image generation, visual review, artifact preservation, and status documentation only.

UI result:

- 8080 listener was force-started cleanly and remained alive.
- Real file upload path was usable through the UI harness.
- `deleted client` / `deleted slot` / `ERR_CONNECTION_REFUSED` / `Accept failed` were not observed in the checked log excerpt.
- Full UI generation was blocked for `announcement` and `comparative_review` by required writer-role UI state. The harness timed out waiting for `誰の立場で書くか`.
- One raw UI `company_introduction` run reached `publishable_success`, but it used 9 sources because sources from previous UI attempts remained in the session.
- Clean retry confirmed source reset/delete behavior is unstable under automation.
- Copy operation and legal panel were not rechecked because the full UI path was unstable; this remains manual QA / UI smoke owner scope.

Backend fallback validation:

- Current mainline backend was run once per article type with fixed source packets, then GPT Image 2 image pairs were generated and visually reviewed.
- `announcement`
  - `publishable_success`
  - `runtime_reason_code=OK`
  - body present
  - image success
  - display copy: `2026年の承認手順、何を確認する？`
  - judgment: `user_trial_ok_body_image`
- `comparative_review`
  - `publishable_success`
  - `runtime_reason_code=OK`
  - body present
  - image success
  - display copy: `導入条件で変わる比較軸？`
  - judgment: `user_trial_ok_with_normal_review_body_image`
- `company_introduction`
  - `publishable_success`
  - `runtime_reason_code=OK`
  - body present
  - image success
  - display copy: `データ化の対応範囲は？`
  - judgment: `limited_user_trial_ok_with_review_awareness_body_image`

Image review:

- All backend fallback `with_text` images had readable display copy.
- Display copy did not duplicate in the reviewed backend fallback images.
- Backend fallback `company_introduction` image copy did not return to generic consultation framing.
- Reviewed `without_text` images had no obvious extra readable text, digits, logo, signature, or watermark.
- Actual raw UI `company_introduction` image copy was `RPA、どこから相談する？`; this is recorded as a semantic article-key propagation issue, not fixed in this trial.

Source retention:

- Source retention after article-type changes is over-strong: sources can persist across runs and contaminate later article types.
- This is not a body/image model failure; it is a UI/session isolation risk before wider user testing.

Next owner issues:

- `note_writer_app required input wizard / writer-role UI state`
- `note_writer_app source session isolation / source reset UX`
- `blog_image_auto / image_cover_strategy semantic article-key propagation`
- `manual QA / UI smoke owner for copy/legal after UI path is stable`

Decision:

- Body and image generation are acceptable for limited trial review awareness when run on clean source packets.
- Full UI user trial is not cleared yet because `announcement` / `comparative_review` could not complete through the UI and source isolation is unstable.
- Continue without code changes in this record. Do not mark any of the above owner issues as fixed from this trial.

Verification:

- `product_code_hash_diff_status=NO_PRODUCT_CODE_HASH_DIFF`
- `summary.json`, per-type reviews, UI review, image review, source retention review, next owner decision, app log excerpt, and product code hash diff were saved in the artifact directory.
- `C:\tetie\WORKLOG.md` updated.
- `AGENTS.md` not updated because the entry route did not change.

---

## 2026-04-28 Limited User Trial

Artifact:

- `C:\tetie\notecode\logs\limited_user_trial_20260428-154744\`

Scope:

- Current mainline limited user trial in normal mode.
- Product code / prompt / pipeline / repair / quality / threshold / source contract / image API params / UI implementation were not changed.
- Tested exactly one UI run each for:
  - `announcement`
  - `comparative_review`
  - `company_introduction`

Result:

- Status: `GREEN_WITH_REVIEW_AWARENESS`
- `announcement`
  - `publishable_success`
  - `runtime_reason_code=OK`
  - body `366` chars
  - source count `2/2`
  - image variants `2/2` success
  - `blocked_output_redacted=false`
  - internal leakage not observed in body/UI
- `comparative_review`
  - `publishable_success`
  - `runtime_reason_code=OK`
  - body `1630` chars
  - source count `3/3`
  - image variants `2/2` success
  - `blocked_output_redacted=false`
  - internal leakage not observed in body/UI
  - representative copy action and legal panel passed
- `company_introduction`
  - `publishable_success`
  - `runtime_reason_code=OK`
  - body `1381` chars
  - source count `4/4`
  - image variants `2/2` success
  - `blocked_output_redacted=false`
  - internal leakage not observed in body/UI
  - `repair_required=true` / `repair_rejected=true` recorded as review-awareness only

Representative checks:

- `内容を確認` / `不足を確認` alone did not start generation.
- Explicit generation button was required for generation.
- Source keep/reset did not start generation; reset cleared source markers to `0`.
- Source contamination was not observed.
- Comparative review used source-backed price information; unsupported winner / superiority was not observed.
- Company introduction kept self-perspective with `私たち`, did not read as third-party review, and remained source-backed.
- Company introduction image copy `RPAのデータ化、どこまで任せる？` was accepted as support-scope framing, not excessive consultation-route drift.
- 8080 listener alive; `ERR_CONNECTION_REFUSED` / `Accept failed` / `deleted client` / `deleted slot` not observed in captured app log excerpt.
- Product code hash diff: `NO_PRODUCT_CODE_HASH_DIFF`.

Decision:

- Limited user trial passed under review-awareness limits.
- No immediate product-code owner is required from this trial.
- Carry record-only notes only if repeated user-facing issues appear.
- `AGENTS.md` not updated because the entry route did not change.

---

## 2026-04-28 追記（UI source session isolation / reset UX）

Artifact:

- `C:\tetie\notecode\logs\ui_full_path_source_session_isolation_20260428-132842\`

Scope:

- Primary owner: `B: source session isolation / reset UX`
- Same `note_writer_app.py` state boundary で `A: writer-role required state` も限定対応。
- backend generation pipeline / prompt / comparative source-fit / image strategy / repair / quality / threshold は未変更。

Implemented:

- `note_writer_app.py` に source session state / source signature / keep-reset review state を追加。
- source が残っている場合、UI に `この資料を使う` / `新しく始める` を user-friendly に表示。
- 生成後・別 article type・client refresh の source restore を明示 keep/reset 境界に寄せた。
- fresh upload 中の client refresh は current work として復元し、生成提出後の restore は previous material として review を要求する metadata を追加。
- reader 入力後に `次へ` 済みなら writer step へ進むよう required input wizard の stale state drift を補正。

Verification:

- `py_compile`: pass
- focused generation helper tests: `85 passed`
- UI helper / state adapter / result adapter / confirm adapter / simulation / matrix tests: `118 passed`
- 8080 listener alive after restart.

UI full path results:

- `announcement`
  - UI generated successfully.
  - `runtime_reason_code=OK`
  - source count `2/2`
  - body present
  - image fresh observed
  - `内容を確認` / `不足を確認` did not start generation.
- `company_introduction`
  - UI generated successfully.
  - `runtime_reason_code=OK`
  - source count `4/4`
  - body present
  - image fresh observed
  - `内容を確認` / `不足を確認` did not start generation.
- `comparative_review`
  - original writer-role timeout was not reproduced.
  - still not generated through UI; the remaining failure occurs before explicit generation after comparative confirmation waits and source/session review boundary refresh.
  - no clean comparative UI output was produced, so comparative source contamination is unresolved rather than observed in a generated artifact.

Decision:

- Full 3-type user trial is not cleared yet.
- Source reset UX and partial clean UI full path are improved.
- Next owner remains `note_writer_app comparative UI confirmation/source-session boundary`.
- AGENTS update not needed; entry route unchanged.

---

## 2026-04-28 追記（comparative UI confirmation/source-session boundary）

Artifact:

- `C:\tetie\notecode\logs\comparative_ui_confirmation_source_boundary_20260428-140359\`

Scope:

- Primary owner: `note_writer_app comparative UI confirmation/source-session boundary`
- UI state boundary only.
- backend generation pipeline / prompt / source contract / image strategy / repair / quality / threshold are unchanged.

Implemented:

- Fixed source session acceptance so a fresh, already-confirmed journey keeps generation-ready state.
- Stale or missing confirmation still invalidates and stops before generation.
- Added helper tests for fresh preservation, stale invalidation, and comparative source/session acceptance.

Verification:

- `py_compile`: pass
- focused helper tests: `13 passed, 75 deselected`
- UI helper / simulation / matrix tests: `141 passed`
- confirm / generation state / result adapter tests: `45 passed`

UI full path results:

- `comparative_review`
  - clean UI full path success.
  - explicit generation button visible after confirmation.
  - `内容を確認` / `不足を確認` did not start generation.
  - `runtime_reason_code=OK`
  - source count `3/3`
  - body present (`1883` chars)
  - image generation success (`2` variants, 1280x670)
  - source contamination not observed.
- `announcement`
  - smoke success.
  - `runtime_reason_code=OK`
  - body present.
- `company_introduction`
  - smoke success after providing the existing required company-introduction core message input.
  - `runtime_reason_code=OK`
  - source count `4/4`
  - body present.

Decision:

- The comparative UI confirmation/source-session blocker is cleared.
- Full 3-type clean UI path is now cleared for user trial readiness from this UI boundary.
- Remaining owner candidate is manual QA / copy / legal review after trial handoff.
- `AGENTS.md` not updated because the entry route did not change.

---

## 2026-04-28 追記（final UI representative QA）

Artifact:

- `C:\tetie\notecode\logs\final_ui_representative_qa_20260428-150638\`

Scope:

- Final representative UI QA immediately before the limited user trial.
- Product code was not changed.
- Prompt / pipeline / repair / quality / threshold / source contract / image API params / `blog_image_auto.py` were not changed.
- Tested clean UI full path once for:
  - `announcement`
  - `comparative_review`
  - `company_introduction`
- Also checked source keep/reset, copy action, legal panel, image panel, listener/log stability, and product-code hashes.

Result:

- Status: `GREEN_WITH_IMAGE_WATCH_NOTE`
- `announcement`
  - `publishable_success`
  - `runtime_reason_code=OK`
  - body `478` chars
  - source count `2/2`
  - image variants `2/2` success
  - `blocked_output_redacted=false`
  - internal leakage not observed
- `comparative_review`
  - `publishable_success`
  - `runtime_reason_code=OK`
  - body `1371` chars on canonical copy/legal attempt
  - source count `3/3`
  - image variants `2/2` success
  - `blocked_output_redacted=false`
  - internal leakage not observed
- `company_introduction`
  - `publishable_success`
  - `runtime_reason_code=OK`
  - body `904` chars
  - source count `4/4`
  - image variants `2/2` success
  - `blocked_output_redacted=false`
  - internal leakage not observed

Representative checks:

- `内容を確認` / `不足を確認` alone did not start generation.
- Explicit generation button was required for generation.
- Source keep/reset:
  - `この資料を使う` kept prior Tool A/B/C sources `3/3`.
  - `新しく始める` reset source markers to `0`.
  - generation did not start during keep/reset checks.
  - contamination after reset was not observed.
- Copy action:
  - `記事形式でコピー` clicked successfully.
  - copy toast observed.
  - clipboard read succeeded after browser permission grant, `1900` chars.
  - internal leakage in copy action UI not observed.
- Legal panel:
  - panel opened.
  - `生成結果を再チェック` completed.
  - visible result was `問題なし` / `法的・安全面のリスクは検出されませんでした。`
  - legal / guarantee risk assertion not observed.
- Images:
  - all three article types showed `文字入り画像` / `文字なし画像`.
  - with_text display copy was readable and no duplicate copy was observed.
  - without_text variants had no readable word, digit, logo, signature, or watermark observed.
  - watch note: announcement without_text contains small question-mark-like decorative glyphs; non-blocking image cleanliness watch only, article success unaffected.
- Listener/log:
  - 8080 listener alive on `127.0.0.1:8080`, PID `3920`.
  - `ERR_CONNECTION_REFUSED` / `Accept failed` / `deleted client` / `deleted slot` not observed in captured app log excerpt.
- Product code hash:
  - `NO_PRODUCT_CODE_HASH_DIFF` for the required product-code files.

Decision:

- Limited user trial can proceed for `announcement` / `comparative_review` / `company_introduction` under the existing review-awareness limits.
- No product-code owner is opened from this QA window.
- Image no-text punctuation-like glyphs remain watch-only unless repeated in future user-facing runs.
- `AGENTS.md` not updated because the entry route did not change.

---

## 2026-04-28 Limited User Trial Closeout

Artifact:

- `C:\tetie\notecode\logs\limited_user_trial_20260428-154744\`
- closeout note: `C:\tetie\notecode\logs\limited_user_trial_20260428-154744\closeout_decision.md`

Scope:

- Docs-only closeout for the completed limited user trial.
- No additional generation / QA rerun / full-flow rerun / broad smoke matrix.
- Product code / prompt / pipeline / UI / image / quality / threshold were not changed.

Fixed state:

- first limited user trial: `completed / green`
- immediate product-code owner: `none`
- first-wave usable targets:
  - `announcement`
  - `comparative_review`
  - `company_introduction`
- `company_introduction`: continue with review-awareness
- next product work starts only after a concrete user-reported failure, regression, or unacceptable quality report.

Blocker / watch classification:

- blocker:
  - none
- non-blocking watch:
  - `company_introduction` repair_required / repair_rejected record-only warning
  - `company_introduction` voice / title / image-copy review
  - non-first-wave article types
  - image typography small artifacts

Decision:

- First limited user trial is closed as green with review-awareness.
- Do not create a next owner from record-only warnings alone.
- It is acceptable to hand the first-wave targets to real users.
- `AGENTS.md` not updated because the entry route did not change.
