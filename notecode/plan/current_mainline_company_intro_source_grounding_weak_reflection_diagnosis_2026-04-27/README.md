# current_mainline_company_intro_source_grounding_weak_reflection_diagnosis_2026-04-27

## Objective

Diagnose why `company_introduction` returned `source_grounding:weak_reflection` in all 3 record-and-continue rerun attempts, without changing product code.

This package separates source-grounding failure from self-perspective consumption and repair rejection.

## Artifact

- `C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_rerun_20260427-085139\`

## Scope

Docs-only diagnosis:

- compare 3 `company_introduction` attempts
- inspect artifact, quality report, source grounding diagnostics, source excerpts, visible body, source contract validation, contract alignment, review warnings, and repair relationship
- classify first blocker
- prepare next implementation prompt

No changes to:

- product code
- prompt / persona / source contract / algorithm
- threshold / repair count
- quality guard / output guard / pipeline / blog image auto
- self-perspective consumption
- repair acceptance / rejection

## Diagnosis Summary

`company_introduction` `source_grounding:weak_reflection` is classified as:

- primary: `observability_anchor_mismatch`
- secondary: `source_packet_shape_issue`
- related but not first blocker: `repair_rejection_secondary`

The visible bodies reflect the company-introduction operational slots semantically, and runtime company-introduction source contract validation reports all required slots as present and strong. The weak reflection metric is instead pulled down by long composite source grounding groups, including title/URL/catchcopy-like material, multi-line service lists, and long process chunks.

## First Blocker

The first blocker is source-grounding observability, not article generation content, not self-perspective, and not repair acceptance.

Next owner candidate:

- `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`

Narrow hypothesis:

- source grounding anchor extraction/grouping for `company_introduction` overweights composite source excerpts and title/URL-like fragments, causing false weak reflection when the runtime company-introduction source contract is actually satisfied.

## Decision

- Keep `company_introduction` on hold.
- Do not loosen the source grounding threshold.
- Do not mark `weak_reflection` as warning-success.
- Do not repair self-perspective or repair rejection in this package.
- Create a next implementation prompt for a single owner / single hypothesis source-grounding observability change.
