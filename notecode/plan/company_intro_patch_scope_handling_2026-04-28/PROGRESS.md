# PROGRESS

## Current Status

- Package status: implementation complete
- Current phase: company_introduction patch-scope handling implemented and validated
- Date: 2026-04-28 JST
- Product code change: yes, owner-local
- UI server startup: no
- Generation rerun: yes, company_introduction 3 runs plus announcement/comparative smoke
- Image generation: yes, company_introduction 3/3 image pairs succeeded
- Pytest: passed focused helper / company_intro / current_mainline_runner / announcement / comparative smoke suites
- WORKLOG update: completed after implementation
- AGENTS update: not needed unless entrance read order changes

## 2026-04-28 Implementation Closeout

- Artifact:
  - `C:\tetie\notecode\logs\company_intro_patch_scope_handling_20260428-115318\`
- Owner:
  - `company_intro patch-scope helper`
- Product code:
  - added `C:\tetie\notecode\note\simple_note_pipeline\company_intro_patch_scope.py`
  - minimally hooked `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - conditionally replaced company_intro repair preservation wording through `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - focused tests added in `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- Kept untouched:
  - `repair_acceptance.py`
  - `quality_guard.py`
  - `hidden_late_validation.py`
  - `company_intro_source_contract.py`
  - `current_mainline_persona_trial.py`
  - `title_strategy.py`
  - image generation code
  - comparative_review / announcement runtime code
  - target length, repair count, fingerprint threshold, source-grounding threshold

## Implementation Result

- `company_intro_patch_scope.py` owns:
  - `branding` + `company_introduction` scope matching
  - route-drift detection in lead / headings
  - short repair prompt wording for the route-drift surface case
  - patch-scope decision for lead / affected-heading changes
  - rejection of broad rewrite, unflagged heading changes, source-material loss, source-grounding worsening, hard guard failures, and internal leakage
- `pipeline.py` only calls the helper after existing strict/local patch-scope checks fail and records helper telemetry in repair metadata.
- `prompt_builder.py` only delegates existing company-intro repair preservation lines to the helper so `LEAD` / affected route-drift headings are not forced to preserve bad surface.

## Verification

- `py_compile`: passed for helper, pipeline, prompt_builder, and test file.
- Focused helper / prompt:
  - `9 passed, 252 deselected`
- Company intro / patch / repair prompt:
  - `118 passed, 143 deselected`
- Current mainline runner company_intro:
  - `13 passed, 67 deselected`
- Quality guard:
  - `22 passed`
- Announcement smoke:
  - current_mainline_runner: `3 passed, 77 deselected`
  - simple pipeline: `14 passed, 247 deselected`
- Comparative smoke:
  - current_mainline_runner: `2 passed, 78 deselected`
  - simple pipeline comparative bundle: `24 passed, 237 deselected`

## Live Rerun

- `company_introduction`: 3/3 success, body present 3/3.
- `SYS_PIPELINE_FAILURE`: 0/3.
- `blocked_output_redacted=true`: 0/3.
- internal leakage: 0/3.
- lead / heading route-drift phrase hits: 0/3.
- image generation: 3/3 success, with_text / without_text pairs generated.
- announcement smoke: success.
- comparative_review smoke: success.

## Visual / Quality Judgment

- Body:
  - company-introduction axis now stays on business content, products/services, support scope, and service features.
  - run 1 is clearly self-perspective with `私たちは`.
  - runs 2-3 are company-name-centered but not third-party review-like or consultation-funnel-like.
- Titles / headings:
  - 3/3 meet minimum note-readability.
  - no `相談の入口` / `相談前` / `相談窓口` / `導入手順` / `この会社は` / `公開情報では` in lead/headings.
  - some headings remain slightly explanatory-card-like; this is residual craft work, not this owner.
- Images:
  - 3/3 article-aligned.
  - residual: run 1 display text `データ入力のデータ入力` is repetitive.

## Current User Trial Status

- `company_introduction`: `limited_user_trial_ok_with_review_awareness`.
- `announcement`: smoke passed.
- `comparative_review`: smoke passed.
- Residual owners:
  - company_intro first-person / self-perspective craft
  - company_intro title-heading craft
  - image display-copy de-duplication

## Read Files

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
  - `## 4. Single-Pass Generation`
  - `## 5. Repair Algorithm`
  - `## 12. Persona / Source Packet / Editing Persona Contract`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\README.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\TASK.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\ROLLBACK.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\CHECKLIST.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\USER_TRIAL_RUNBOOK.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\PRE_USER_TRIAL_UI_VALIDATION_2026-04-26.md`
- `C:\tetie\notecode\logs\company_intro_repair_prompt_assembly_20260428-112438\diagnosis.md`
- `C:\tetie\notecode\logs\company_intro_repair_prompt_assembly_20260428-112438\repair_prompt_trace.json`
- `C:\tetie\notecode\logs\company_intro_repair_prompt_assembly_20260428-112438\repair_candidate_comparison.json`
- `C:\tetie\notecode\logs\company_intro_repair_prompt_assembly_20260428-112438\owner_decision.md`
- `C:\tetie\notecode\logs\company_intro_repair_prompt_assembly_20260428-112438\next_owner_decision.md`
- `C:\tetie\WORKLOG.md`
- code read-only confirmation:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\repair_acceptance.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## Observed Facts

- `ALGORITHM.md` keeps the baseline as single-pass generation with optional single repair.
- Repair prompt must return full tagged article, not partial patch output.
- Repair is bounded local repair, not whole-article rewrite.
- `SEMANTIC_LEDGER` / `SECTION_SHADOW` / `PATCH_SCOPE` are intended anchors.
- `company_introduction` source packet should support current business / product-service / support scope, while process or pre-contact material remains source-backed and short.
- Direct diagnosis found `B + D mixed`:
  - original lead/body/headings carried `相談の入口` / `相談前` in attempts 1 and 2
  - public source contract material had no tracked route phrase
  - private/raw source packet still had source-backed `相談前`
  - repair prompt SOURCE contained the original bad phrase
  - repair prompt patch surface preserved `TITLE / LEAD / HASHTAGS` and heading names
  - repair candidates were not clean
- `prompt_builder.py` currently adds company-intro surface patch lines that preserve `TITLE / LEAD / HASHTAGS` and heading names.
- `pipeline.py` currently rejects patch-path candidates when `lead` or heading list changes in `_repair_preserves_flagged_scope()` / `_repair_preserves_local_patch_scope()`.
- `repair_acceptance.py` currently contains pure metric predicates and is not where lead / heading patch-scope boundary is decided.

## Decision

現行 patch scope では、lead / heading の route drift phrase は直せない。bad phrase が exactly preserved surface にあるため、repair prompt は bad surface を保持するよう誘導し、pipeline acceptance もそれを保持した candidate だけを通しやすい。

次 implementation は `pipeline.py` への直接 accretion ではなく、`company_intro patch-scope helper` owner に切る。helper は company_introduction 限定で、route drift phrase が lead / affected heading にある場合だけ patch scope を lead / affected heading へ最小拡張する。`pipeline.py` は existing hook から helper を呼び、`prompt_builder.py` は必要最小限の existing wording replacement に留める。

`repair_acceptance.py` は今回も触らない。理由は、今回の artifact では clean repair candidate が over-strict acceptance だけで落ちたとは言えないため。

## Lead / Heading Change Allow Conditions

Allow only when all conditions are true:

- active scope is `article_type=branding` and `semantic_article_key=company_introduction`
- original lead or affected heading contains route drift phrase
- affected heading is the heading named by flagged span or route-drift location
- title / hashtags remain stable
- body remains non-empty
- output contract is complete tagged article
- source grounding is not worse
- output guard / internal leakage is green
- hard source contract remains clear
- current business / product-service / support scope remain visible
- lead / heading change removes route-drift framing without removing source-backed business material
- source-backed short mention of inquiry/contact remains natural and subordinate

## Reject Conditions

Reject if any condition is true:

- body-wide rewrite or broad heading reorder is required
- unflagged headings change
- lead / heading becomes consultation-route, inquiry funnel, implementation procedure, or pre-contact checklist as the main axis
- source-backed current business / product-service / support scope is dropped
- source-outside price, result, customer, award, superiority, legal, or guarantee claim appears
- internal/runtime terms appear in visible output or UI
- candidate requires threshold relaxation
- candidate only removes a tracked word while preserving the same route-drift article axis

## Next Recommended Owner

- owner:
  - `company_intro patch-scope helper`
- product code scope for future implementation:
  - add `C:\tetie\notecode\note\simple_note_pipeline\company_intro_patch_scope.py`
  - minimal hook in `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - minimal conditional wording replacement in `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` only if required
  - tests in `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- not owner:
  - `repair_acceptance.py`
  - `quality_guard.py`
  - output formatter
  - UI
  - image generation

## Current User Trial Status

- `company_introduction`: hold continues.
- Reason:
  - direct repair prompt assembly diagnosis shows route drift phrase retention in lead / heading patch path.
  - current issue spans patch prompt surface and pipeline patch-scope boundary.
  - docs-only planning package created; no product-code fix has been applied.
- `announcement`: unaffected by this planning package.
- `comparative_review`: unaffected by this planning package.

## Verification

- Product code edited: no.
- UI server started: no.
- Pytest executed: no, by request and because this is docs-only.
- Generation rerun: no.
- AGENTS updated: no, entrance route unchanged.
