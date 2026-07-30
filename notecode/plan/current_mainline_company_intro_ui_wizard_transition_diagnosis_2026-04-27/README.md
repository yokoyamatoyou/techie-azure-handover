# current_mainline_company_intro_ui_wizard_transition_diagnosis_2026-04-27

## Objective

Diagnose the `company_introduction` UI wizard transition failure from the record-and-continue validation artifact without treating it as a generation-quality, prompt, repair, or product UI implementation failure.

This package is docs-only. It fixes the owner decision and next implementation prompt for a validation-harness-only follow-up.

## Artifact Root

- Run root: `C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_20260427-004338\`
- Main record-and-continue harness: `C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_20260427-004338\run_record_continue_validation.py`
- Replacement harness: `C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_20260427-004338\run_company_intro_replacement_attempt.py`
- Company case folder: `C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_20260427-004338\ui_live\company_introduction_kyoto_latest_log\`

## Primary Classification

- Primary: `validation_harness_selector_state_drift`
- Narrow hypothesis: `company_introduction` wizard transition fails because the harness waits fixed labels and fixed step order instead of deriving active wizard state after managed defaults update.
- Not classified as:
  - product UI state bug
  - generation runtime failure
  - source/input setup issue
  - repair rejection issue
  - self-perspective prompt issue
  - image generation issue
  - listener/runtime crash

## Evidence Summary

- `company_introduction` attempt 1 reached generation and `publishable_success`.
- `company_introduction` attempt 2 reached generation and `review_required_draft`.
- `company_introduction` attempt 3 failed before generation with `UI_HARNESS_OPERATION_ERROR`.
- Replacement attempts 4-6 reproduced pre-generation UI harness transition failures.
- All failed attempts retained `listener_8080_alive_after_attempt=true`.
- Product code hash status in the artifact is `NO_PRODUCT_CODE_HASH_DIFF`.
- Attempt 3/4 visible UI was at `STEP3 読者`, while the harness waited for `誰の立場で書くか`.
- Attempt 5 visible UI was at `STEP4 書き手`, while the harness waited for `STEP2 内容`.
- Attempt 6 `controls_set` screenshot showed `STEP4 書き手` and `確認へ`; later operation-error capture showed default state again, suggesting attempt/session boundary contamination rather than product crash.
- App log showed a generation from the prior company attempt still active while the next attempt began source upload, so the next owner must record attempt boundaries and prevent overlap.

## First Blocker

The first blocker is validation harness handling of company-introduction managed wizard defaults:

- `STEP2 内容` can be skipped or already managed as `自社・会社紹介`.
- `STEP4 書き手` can already display a managed/default writer.
- Waiting for fixed text in a fixed sequence misclassifies an otherwise usable UI state as `UI_HARNESS_OPERATION_ERROR`.

## Owner Decision

No product owner is assigned by this package.

If implementation is requested next, the owner is validation harness / artifact collection only:

- `C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_20260427-004338\run_company_intro_replacement_attempt.py`
- or a new one-off harness artifact under the same validation-log lineage

## Non-Goals

- Do not change product code.
- Do not change `note_writer_app.py`.
- Do not change helper modules.
- Do not change prompt / persona / source contract / algorithm / threshold / repair count / quality guard / output guard / pipeline / blog image auto.
- Do not add timeouts, sleeps, or exception swallowing as the fix.
- Do not run full validation.
- Do not proceed to company-introduction self-perspective or repair rejection fixes from this package.
- Do not create new product helpers or module splits.

