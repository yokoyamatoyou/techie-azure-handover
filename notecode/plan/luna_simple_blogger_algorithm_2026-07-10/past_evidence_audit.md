# Past Evidence Audit

- owner: `luna_simple_blogger_no_api_feasibility`
- date: `2026-07-10 JST`
- API send count: `0`
- product code changed: `false`

## Current-owner audit

The current Route V documents agree on `route_v_first_gap_review` as the Route V next owner. This package does not take or replace that owner. Its owner exists only inside this separate package.

Route V non-owner boundary preserved:

- no code, config, default model, prompt, persona, accepted-state, or current-owner change
- no UI connection
- no source refetch, generated-body patch, raw full source handoff, fallback revival, threshold relaxation, or repair-acceptance relaxation

## Required historical evidence

### 2026-06-24 front/back two-API trial

Source: `notecode/logs/0624/route_v_company_intro_front_back_editor_persona_two_api_trial_after_encoding_guard_20260624_213222/api_trial_summary.md`

- two API sends, observational only
- body floor improved from `1219` to `1452` against a `1400` floor
- H1 stayed exactly one
- reader-frame hits fell from `1` to `0`
- quality remained non-accepting at `84`
- remaining issues: `sentence_too_long`, `model_frequent_word`

Interpretation: a second pass can restore length and reader-frame behavior, but more passes did not by themselves produce acceptable natural Japanese.

### 2026-06-24 additional one-API refinement

Source: `notecode/logs/0624/route_v_company_intro_front_back_editor_persona_one_api_refinement_trial_after_two_pass_20260624_214820/api_trial_summary.md`

- one additional API send after the two-pass output
- body increased from `1452` to `1502`
- H1 and reader-frame checks remained green
- quality still stayed at `84`
- the same two issues remained

Interpretation: the third pass added volume but did not remove the model fingerprint. Call count alone is not the missing mechanism.

### 2026-06-26 front/back contract design

Source: `notecode/logs/0626/route_v_company_intro_front_back_editor_persona_contract_no_api_design_20260626_211645/contract_design.md`

The design used an in-house blogger in the front half and a source-backed company editor in the back half. It correctly preserved source bounds, self-perspective, floor, H1, and compact prompt intent. Its limitation for this experiment is the role transition itself: the second stage is invited to normalize and explain from an editorial stance. The new candidate therefore keeps one blogger identity in both stages and changes only the task.

### WORKLOG policy history

`Writer-only Natural Blog Reader Intent / Context Bridge Policy` moved away from repeated `判断材料` / `判断軸` framing toward curiosity, background, company posture, and reader interest. It also showed that a low-interest reader is a materially different target from a comparison/decision reader.

`Writer-only Source-derived Bridge / Editorial Review Policy Revision` replaced external calendar/weather bridges with source-derived topic, scene, posture, material detail, history, or use case. Its editorial persona was review-only and did not rewrite, repair, regenerate, or add a model call. This is evidence against treating that earlier review policy as proof for a second-pass editor rewrite.

`Route B Temperature Persona Image Followthrough` showed that a selected blog persona can be transmitted as a compact `style_rule` while the source/self-perspective contract remains separate. This supports a compact persona contract instead of persona prose bloat.

### `ALGORITHM.md` 12.1-12.5

The current algorithm document says persona names are design inputs, not reader-visible text; they should be compressed into source contract, craft guard, validation trigger, bounded repair scope, and late return. It also requires source-use packets to be the common grounding basis and keeps repair bounded. The separate candidate follows those principles while declining the editor-role switch.

### 2026-07-10 Luna feasibility report

Sources:

- `notecode/logs/0710/route_v_gpt56_luna_human_japanese_feasibility_no_api_20260710/feasibility_report.md`
- `notecode/logs/0710/route_v_gpt56_luna_human_japanese_feasibility_no_api_20260710/baseline_summary.json`

Confirmed reusable gaps:

- runtime zero-anaphora checking is declared but incomplete
- required narrator absence can escape runtime QA
- single and cross-article model phrases can escape the current checker
- current six-genre static observations include heavy `確認` / `整理` repetition
- live Luna quality, latency, and cost have not been measured

The earlier report proposed a more elaborate discourse pipeline. This package tests the smaller hypothesis first: one compact blogger contract plus either one call or a same-blogger bounded second call.

## Evidence limit

No saved artifact is a genuine output of the proposed same-blogger Luna candidate. The historical editor outputs are control evidence only. Static replay can validate inputs, stage boundaries, metrics, and review packaging; it cannot establish Luna output quality, semantic source support, or causal improvement from the second pass.
