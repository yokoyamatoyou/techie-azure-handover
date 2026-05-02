# Slim Audit After Product Introduction Close 2026-04-29

## Current Status Summary

- judgment: `SLIM_AUDIT_READY_NO_CODE`
- text mainline: `COMPLETION_CANDIDATE_WITH_COMPLEXITY_RISK`
- branding anchor: `BRANDING_ANCHOR_FIX_VALIDATED_NO_FURTHER_OWNER`
- product_introduction: `PRODUCT_INTRODUCTION_ACCEPT_BODY_VALIDATED`
- latest product_introduction artifact: `C:\tetie\notecode\logs\product_introduction_accept_body_validation_20260429-003843`
- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- product code changed: `NO`
- full-flow rerun / broad smoke matrix: `not_run`

## Read-Only Scope

- This audit inventories responsibility overlap and possible slim-down candidates only.
- No product code, prompt, persona, repair, threshold, source contract, retry, UI, image, or pipeline behavior was changed.
- No cleanup implementation owner was opened in this window.
- Watch items remain watch items and were not promoted to blockers.
- `product_introduction` validation close and code cleanup were kept separate.

## Inspected Files

- required rule / status docs:
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
  - `C:\tetie\notecode\ALGORITHM.md`
  - `C:\tetie\WORKLOG.md`
- audit targets:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- read-only support checks:
  - `C:\tetie\notecode\note\current_mainline_persona_trial.py`
  - `C:\tetie\notecode\note\current_mainline_profile_resolver.py`
  - `C:\tetie\notecode\note\current_mainline_runner.py`

## Responsibility Map

| Area | Primary owner | Responsibility read |
| --- | --- | --- |
| semantic resolution / source readiness | `newalgorithm_pipeline/input_contract.py` | Determines semantic key, source grounding status, source fit, source substance, product subject anchor, and pre-generation block / warn readiness. This remains the primary owner for source readiness. |
| writer-facing generation / repair prompt | `simple_note_pipeline/prompt_builder.py` | Converts resolved contract, system hints, article style, persona guard lines, source packet, and repair diagnostics into writer-facing prompt blocks. |
| runtime contract / diagnostics / acceptance | `simple_note_pipeline/pipeline.py` | Prepares and evaluates runtime source contracts, hidden late validation, diagnostics, optional single repair, acceptance / rejection, hard fail payload, and final telemetry. Treat as freeze. |
| persona compression | `current_mainline_persona_trial.py` | Compresses article-type persona into lead focus, heading flow, late return, guard lines, source packet, and repair guard. Not a deletion target because prompt_builder consumes it directly. |
| compact UI profile hints | `current_mainline_profile_resolver.py` | Resolves UI-facing article profile hints and semantic fallback. Small file, but it protects generic branding / product_introduction / company_introduction routing. |
| mainline entry and input stop projection | `current_mainline_runner.py` | Projects resolved input contract, source_fit, stop result, and mainline execution. Not part of cleanup owner. |

## Duplication Inventory

### 1. Generic Branding Hint

- observed in `current_mainline_profile_resolver.py`:
  - generic branding can inherit subtype hints such as `会社紹介として、背景・提供価値・信頼材料を自然につなぐ。`
- observed in `prompt_builder.py`:
  - `_normalize_generation_system_hints()` filters older company/product-ish generic hints and injects `ブランド記事として、迷いが生まれる場面と判断材料を自然につなぐ。`
  - `build_article_style_lines()` also emits generic branding craft lines from `_branding_source_contract`.
- read:
  - This is the narrowest accidental duplication candidate.
  - It is not deletion-safe because the post-validation generic branding pass depends on preserving generic branding behavior and explicit company/product/announcement/comparative guards.
  - The likely safe shape is behavior-preserving cleanup around normalization / dedupe, not removing the semantic hint outright.

### 2. Company Introduction Craft / Source Packet / Late Return

- observed in `input_contract.py`:
  - resolves company-introduction-like semantic key, source grounding items, source substance, and source_fit.
- observed in `current_mainline_persona_trial.py`:
  - company_intro family defines current business / product-service / support scope / company posture late return.
- observed in `prompt_builder.py`:
  - emits company introduction craft lines, topic surface cleanup, structure lines, generation guard lines, and repair guard lines.
- observed in `pipeline.py`:
  - prepares / evaluates company introduction runtime source contract, hidden late validation, naturalness enrichment, repair acceptance, failure payload.
- read:
  - This is role-separated duplication, not accidental deletion surface.
  - `input_contract.py` decides readiness and source fit; `prompt_builder.py` exposes writer-facing shape; `pipeline.py` enforces runtime guard / fail-closed behavior.
  - Do not touch in slim cleanup.

### 3. Product Introduction Source Readiness / Branding Family Borrow

- observed in `input_contract.py`:
  - product subject anchor extraction and `product_subject_anchor` block logic.
- observed in persona / resolver:
  - product_introduction uses branding-family persona posture and hints.
- read:
  - This was just closed by focused accept body validation.
  - The borrowed branding-family behavior is intentional until a new artifact-backed blocker appears.
  - Do not treat as cleanup target.

### 4. Comparative Review Source Fit / Writer Guard

- observed in `input_contract.py`:
  - comparative source substance assesses comparison context, axes, differences, fit conditions, caution, and next step.
- observed in `prompt_builder.py`:
  - comparative writer rules guard against ranking, absolute winner, unsupported price / plan / result / vendor claims.
- observed in `pipeline.py`:
  - comparative runtime source contract validation and repair acceptance boundary remain centralized.
- read:
  - This is a layered contract, not deletion-safe duplication.
  - Keep fixed checks because previous comparative source-fit blocker was real.

### 5. Announcement Guard

- observed in `prompt_builder.py`:
  - announcement craft lines keep target / change / next action visible and stop unsupported date / price / result / customer / partnership additions.
- observed in `pipeline.py`:
  - announcement runtime source contract validation exists with scope-local triggers.
- read:
  - Role-separated runtime guard plus writer-facing surface.
  - Do not touch from generic branding cleanup.

### 6. Source Contract / Hidden Late / Repair Acceptance / Hard Fail

- observed in `pipeline.py`:
  - `_refresh_diagnostics_state()` centralizes quality guard merge, hidden late validation, source contract validations, and flagged spans.
  - repair metadata and failure payload preserve source contract and hidden late diagnostics.
  - hard failure remains `SYS_PIPELINE_FAILURE` with failure candidate payload.
- read:
  - This area is dense and duplicated-looking, but currently protects fail-closed behavior.
  - Treat as observe only / freeze.

## Classification

### Immediate Deletion Safe

- `none`

Reason: Every observed duplication either guards a recently validated article type or separates pre-generation readiness, writer-facing surface, and runtime acceptance. "削れそう" alone is not deletion-safe.

### Behavior-Preserving Cleanup Candidate

1. `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` generic branding hint cleanup
   - scope:
     - `_normalize_generation_system_hints()` and only adjacent generic branding hint normalization / dedupe.
   - allowed shape:
     - behavior-preserving rewrite / clearer dedupe.
     - no deletion of product_introduction, company_introduction, comparative_review, announcement, source contract, repair, or acceptance wording.
   - required safety:
     - generic branding with source anchor remains pass.
     - no-anchor generic branding remains blocked before body / LLM call.
     - explicit company_introduction / product_introduction / announcement / case_study / comparative_review guards remain pass.

### Observe Only / Freeze

- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - source fit / source readiness / prompt surface / semantic routing are co-located, but source readiness is the primary responsibility here.
  - do not turn source readiness into deletion candidate.
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - source contract, hidden late, repair acceptance, failure payload, hard fail, and telemetry are centralized.
  - first cleanup target should not be this file.
- `C:\tetie\notecode\note\current_mainline_persona_trial.py`
  - persona contract and late return duplicate prompt direction by design.
  - observe only unless a later owner proves exact prompt equivalence.
- `C:\tetie\notecode\note\current_mainline_profile_resolver.py`
  - small, but generic branding semantic fallback and UI profile hints are routing-sensitive.

### Do-Not-Touch

- `simple_note_pipeline/pipeline.py` acceptance / hard-fail / repair boundary.
- company_introduction source contract / hidden late / prompt / retry boundary.
- product_introduction source readiness and accept body anchor behavior.
- input_contract.py source readiness / pre-generation stop.
- prompt_builder.py product_introduction / company_introduction / comparative_review / announcement contract wording.
- GPT Image 2 / UI / note_writer_app.
- full retry, broad smoke matrix, thresholds.

## Rank 1 Next Owner

- current window: `no implementation owner`
- if a next implementation window is explicitly opened:
  - owner: `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - hypothesis: `generic branding hint cleanup is behavior-preserving when limited to hint normalization / dedupe`
  - judgment label for that future window: `SLIM_CLEANUP_READY_SINGLE_OWNER`
  - no second owner should be opened in the same window.

## Future Implementation Instruction Draft

Use only if management chooses to move from audit to cleanup.

```text
Implement a behavior-preserving cleanup in:
C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py

Scope:
- Only generic branding hint normalization / dedupe around _normalize_generation_system_hints().
- Do not change product_introduction, company_introduction, comparative_review, announcement, source contract, repair, acceptance, threshold, retry, UI, or image logic.
- Do not delete a hint unless equivalence tests prove the resulting prompt surface and guards are unchanged for the fixed cases.

Required fixed checks before completed:
- generic branding with source anchor remains pass.
- generic branding without source anchor remains pre-generation block with no body and no LLM call.
- explicit company_introduction guard remains pass.
- product_introduction accept body behavior remains pass.
- announcement / case_study / comparative_review non-target guards remain pass.
- prompt diff/equivalence check confirms only generic branding duplicated hint wording is normalized.

Stop:
- any product_introduction, company_introduction, comparative_review, announcement, or source readiness behavior changes.
- any need to edit input_contract.py or pipeline.py.
- any need to rerun broad matrix or adjust thresholds.
```

## Equivalence Check Plan

- Static / prompt-surface check:
  - build generation prompt for fixed generic branding anchor case before / after.
  - assert no extra product/company/comparative/announcement contract text is removed.
  - assert generic branding hint still appears once and old company/product-ish generic hints do not reappear.
- Focused regression checks:
  - product_introduction accept body focused tests from the close artifact.
  - generic branding anchor pass and no-anchor pre-generation block.
  - explicit company_introduction / product_introduction / announcement / case_study / comparative_review guard tests.
- No broad rerun:
  - do not run full-flow live generation or broad smoke matrix for the cleanup itself unless a focused check exposes behavior drift.
- Artifact requirement:
  - save before/after prompt-surface diff and focused test summary under a new cleanup artifact path.

## Fixed Checks To Preserve

- product_introduction:
  - accept body with provider business / SaaS source anchor.
  - accept body with clear onboarding service category.
  - old no-anchor product_introduction remains `INP_SOURCE_CONTEXT_INSUFFICIENT`, body `0`, LLM call `0`.
- company_introduction:
  - source contract / hidden late / hard fail / repair boundary unchanged.
  - no persona / editor / trial leakage.
  - no visible `source_limit`.
- generic branding:
  - anchor-present pass.
  - anchor-absent pre-generation block.
  - semantic remains `branding`, not accidental company_introduction.
- comparative_review:
  - comparative source-substance and non-target guard remain pass.
  - no ranking / absolute winner / unsupported price-plan-result-vendor relaxation.
- announcement:
  - target / change / next action guard remains pass.
  - unsupported date / price / result / customer / partnership guard remains active.

## Stop Conditions

- Any cleanup needs `input_contract.py` source readiness changes.
- Any cleanup needs `pipeline.py` acceptance, hard fail, hidden late, or repair boundary changes.
- Any product_introduction accept body behavior changes.
- Any company_introduction source contract / hidden late behavior changes.
- Any generic branding no-anchor block starts returning body or making LLM calls.
- Any non-target guard regression appears.
- More than one owner file is needed.

## AGENTS / WORKLOG Update Need

- AGENTS update: `not_required`
  - Entry route did not change.
- PROGRESS update: `required_and_done`
  - Record this audit after product_introduction close.
- WORKLOG update: `required_and_done`
  - Record docs-only audit artifact.
- ALGORITHM update: `not_required`
  - No algorithm change.
