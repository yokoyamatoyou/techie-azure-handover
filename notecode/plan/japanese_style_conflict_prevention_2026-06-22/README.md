# Japanese Style Conflict Prevention Proposal

Status: proposal / non-current
Created: 2026-06-22 JST

This package is a planning note for using the external `japanese-tech-writing/SKILL` reference as a conflict-prevention aid for Japanese writing quality.

It does not replace Route B / 0506 current source of truth.
It does not replace `notecode/0506/docs/CURRENT_ALGORITHM.md`, `PIPELINE_SPEC.md`, `JAPANESE_STYLE_POLICY.md`, or `JAPANESE_STYLOMETRY_POLICY.md`.
It does not change the current Route B / 0506 owner.

Current owner preserved:

```text
draft_writer_depth_budget_contract_smoke_failure_diagnosis
```

## Purpose

Use the external Japanese writing reference only where it helps prevent collisions between:

- algorithm-level contracts,
- prompt-level instructions,
- genre/persona/style profiles,
- deterministic QA,
- targeted rewriting.

The goal is not to make the output more technical or more compressed.
The goal is to keep writing-quality rules from fighting the active Route V body-floor and source-grounding contracts.

## Current Source Of Truth Boundary

Current source-of-truth files remain:

- `notecode/AGENTS.md`
- `notecode/0506/AGENTS.md`
- `notecode/0506/docs/CURRENT_ALGORITHM.md`
- `notecode/0506/docs/PIPELINE_SPEC.md`
- `notecode/0506/docs/CONFIG_AND_PERSONA_POLICY.md`
- `notecode/0506/docs/JAPANESE_STYLE_POLICY.md`
- `notecode/0506/docs/JAPANESE_STYLOMETRY_POLICY.md`
- `notecode/0506/docs/AI_CODING_RULES.md`
- owner-specific diagnosis artifacts named by the current docs

This proposal must not be cited as the current algorithm.
If this proposal conflicts with current docs, current docs win and the conflict must be reported before implementation or API validation.

## External Reference Boundary

External reference:

```text
https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d
```

The external reference is treated as:

- external reference / proposal seed,
- not a runtime prompt body,
- not a policy replacement,
- not a direct source-of-truth document for notecode.

Do not copy the full reference into prompts, config files, AGENTS files, or runtime modules.

## Collision Guard

Before any implementation based on this package, state exactly one next owner and its non-owner boundaries.

The following collisions must be prevented:

1. `body_length_floor_chars` vs compression
   - Do not let "remove redundancy" or "shorten prose" reduce body-floor compliance.
   - Do not place compression-heavy rules in DraftWriter while the depth-budget owner is unresolved.

2. source-grounded depth vs abstract style rules
   - Do not make style rules override confirmed claims, assigned claim anchors, selected excerpts, or do-not-infer rules.
   - Do not add unsupported causal explanations to satisfy "logical connection" checks.

3. note/Hatena naturalness vs technical-writing rigidity
   - Do not apply one-sentence-one-line, footnote, technical-column, or strict definition rules across blog genres.
   - Do not harden `daily_activity`, `announcement`, or low-intent company/service hooks into technical essays.

4. prompt compactness vs full style manual
   - Do not paste the external reference into prompts.
   - Render at most a few compact genre-specific instructions when a later owner proves the need.

5. deterministic QA vs LLM judgment sprawl
   - Prefer deterministic issue detection where possible.
   - Do not add a broad LLM review loop for style judgments.

6. watchlist duplication
   - Do not create a second independent forbidden-phrase list that competes with `JAPANESE_STYLE_POLICY.md` and `JAPANESE_STYLOMETRY_POLICY.md`.
   - Extend existing issue types only after an inventory proves the gap.

## Adopt Candidate Map

Only compact, contract-like or issue-type-like rules are adoption candidates.

| Candidate | Possible Home | Collision Guard |
|---|---|---|
| Paragraph role handoff: what a paragraph receives, does, and passes onward | structural editor diagnosis / future QA issue | Must not force rigid paragraph templates |
| Unsupported certainty | QA issue candidate such as `certainty_without_support` | Must use source-backed evidence, not generic suspicion |
| Oversimplified causality | market/comparison QA candidate | Must not invent extra causes |
| Term drift / concept blur | market explanation QA candidate | Must not ban natural paraphrase globally |
| Empty LLM-like phrasing | existing model-frequent/generic phrase policy | Must not create duplicate watchlists |
| Heading specificity mismatch | structural editor / QA candidate | Must respect article type and source thickness |
| Reader burden from unnecessary names/details | editor profile note | Must not delete source-required details |

## Non-Adopted Rules

Do not adopt the following as general notecode rules:

- full external reference as a prompt,
- one sentence per line,
- footnote and technical-book conventions,
- universal bold definition rules,
- universal connector-at-paragraph-start rules,
- compression-first editing,
- hard banned-word deletion,
- strict technical-writing tone for `daily_activity`, `announcement`, or low-intent company/service introductions.

## Placement Strategy

Default placement:

- DraftWriter: do not place new external-reference rules here while the current depth-budget smoke regression is unresolved.
- Style editor: only small empty-phrase or generic-summary adjustments, if a later owner proves the gap.
- Structural editor: paragraph role handoff, heading specificity, and local logical continuity are the safest future homes.
- Japanese quality checker: deterministic or near-deterministic issue candidates only.
- Targeted rewriter: fix only spans flagged by QA, preserving facts, claim IDs, section purpose, speaker, and non-target paragraphs.

## Slice Plan

Use one owner per slice.
Do not combine inventory, prompt design, QA implementation, and API validation.

1. `external_japanese_style_reference_inventory`
   - Produce a table of overlap, gap, non-adoption reason, and possible home.
   - Product code changed: false.
   - API used: false.

2. `style_conflict_contract_design`
   - Decide which ideas remain docs-only, which become brief/profile/QA flags, and which stay rejected.
   - Product code changed: false unless explicitly approved later.

3. `deterministic_qa_candidate_audit`
   - Identify only candidates detectable without LLM review.
   - Do not change QA thresholds.

4. `genre_applicability_matrix`
   - Mark strong, weak, and forbidden application by genre.
   - Preserve soft blog genres.

5. `prompt_budget_collision_check`
   - Inspect prompt templates and rendered instruction budget.
   - Do not add broad prompt tuning.

6. `non_current_proposal_handoff`
   - Close or hand off this proposal without changing current source of truth.

## Exit Conditions

This proposal can advance only if all of the following remain true:

- current owner is preserved until current docs change it,
- no product code is changed during inventory-only owners,
- no API validation is run during planning owners,
- no Route A, writer-only, old repair loop, or raw-source fallback is reopened,
- no QA threshold or repair acceptance is relaxed,
- prompt and module bloat remain absent or explicitly blocked,
- any future implementation owner is narrow and independently testable.

## Next Command

Use `NEXT_COMMAND.md` in this package for the next separate-window command.

