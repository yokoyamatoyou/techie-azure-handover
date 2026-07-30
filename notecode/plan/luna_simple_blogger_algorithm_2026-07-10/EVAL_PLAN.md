# Evaluation Plan

## Phase 0: completed no-API gate

Inputs:

- saved Route V human-review articles
- their saved compact source packets where available
- the 2026-06-24 Sanrei input and editor-persona outputs as historical control evidence

Checks:

- contract rendering and prompt character count
- same role ID in both candidate stages
- one fixed call for A and two fixed calls for B
- full-article Stage 2 output contract
- H1/H2/body floor proxies
- narrator presence/overuse signals
- meta-term counts and meta-sentence ratio
- paragraph/sentence rhythm
- zero-anaphora candidate scan
- source-overlap and opening-overlap proxies
- cross-article repeated character n-grams
- human-review bundle generation

Static overlap and zero-anaphora scans are triage aids, not semantic acceptance.

## Phase 1: sealed live pilot, not authorized

Prerequisites, all required:

1. separate current owner
2. explicit API approval
3. official Luna identifier/availability rechecked
4. prompts and source packet hashes frozen
5. API send cap and retry policy recorded
6. usage, latency, output, reasoning, and cost telemetry enabled

Pilot:

- 6 saved source packets, one per genre
- Arm A: one blogger call
- Arm B: same first call plus same-blogger bounded second call
- one repeat initially
- `12` articles total
- no images, source refetch, generated-body patch, fallback, or acceptance mutation

## Mechanical hard gates

- source grounding / unsupported claim: `100% pass`
- numbers, dates, prices, promises, requests, and responsibility subjects: `100% pass`
- high-severity zero-anaphora ambiguity: `0`
- narrator missing or speaker role switch: `0`
- exact H1: `1`
- required H2 and body floor: pass
- user-specified five phrases outside source quotation: `0`
- no raw source handoff or fallback

## Comparative gates

Arm B must beat or tie Arm A without a hard-gate regression:

- lower third-party/explainer voice
- lower ambiguous-subject count
- lower meta-sentence ratio
- no increase in unsupported claims
- no material floor loss
- better or equal blind human publishability

If Arm B does not materially improve at least two human-language axes, prefer Arm A because it uses one fewer call.

## Blind human review

Reviewers receive source excerpts plus anonymized A/B articles. Score 1-5:

- source-grounded and specific
- sounds like the company-side person
- opening creates interest for a low-interest visitor
- omitted subjects are unambiguous
- concrete scenes and source-specific actions survive
- meta/explanatory language does not dominate
- paragraph and sentence rhythm feels human
- publishable with no substantive rewrite

Acceptance target: median `>=4` on publishability and no axis median below `3.5`, with hard gates green.

## Decision mapping

- `possible`: live A/B hard gates pass and one arm meets human acceptance
- `conditionally_possible`: no-API package is sound but live Luna evidence is absent
- `reject`: both live arms fail hard gates, or Arm B adds cost without material quality gain and Arm A is not publishable
