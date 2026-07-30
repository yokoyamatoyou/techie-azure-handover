# Japanese Style Conflict Prevention Handoff

Status: proposal / non-current

Current owner preserved: `draft_writer_depth_budget_contract_smoke_failure_diagnosis`

Decision: this package is closed as a docs-only proposal handoff. It does not replace the current Route B / 0506 source of truth, does not authorize implementation, and does not start a new implementation owner.

## Package artifact list

| Artifact | Status | Role |
|---|---|---|
| `README.md` | proposal / non-current | Package entry, boundary, collision guard, and initial slice plan. |
| `INVENTORY.md` | proposal / non-current | External Japanese style reference inventory, overlap/gap/non-adoption map, and collision-risk table. |
| `RESEARCH_PLAN.md` | proposal / non-current | External-source research summary and Route B / 0506-safe mapping. |
| `CONTRACT_DESIGN.md` | proposal / non-current | Compact contract candidates, rejected/deferred candidates, placement matrix, and future slice plan. |
| `QA_CANDIDATE_AUDIT.md` | proposal / non-current | Deterministic, near-deterministic, editor-only, and rejected QA candidate classification. |
| `GENRE_APPLICABILITY_MATRIX.md` | proposal / non-current | Genre-specific strong / moderate / weak / report-only / forbidden application matrix. |
| `PROMPT_BUDGET_COLLISION_CHECK.md` | proposal / non-current | Read-only prompt size, duplicate-rule, and external-reference contamination check. |
| `NEXT_COMMAND.md` | proposal / non-current | Earlier command handoff reference. This file is superseded for package closure by `HANDOFF.md`. |
| `HANDOFF.md` | proposal / non-current | Final docs-only closure handoff for this package. |

## What this package decided

- The package remains proposal / non-current and must not be cited as the current algorithm.
- Current Route B / 0506 owner remains `draft_writer_depth_budget_contract_smoke_failure_diagnosis`.
- External Japanese writing references may be used only as summarized proposal seeds, not as runtime prompt text or policy replacements.
- Safe contract vocabulary is compact and optional for future owners only: `floor_safe_local_only`, `source_claims_only`, `genre_weighted`, `flagged_spans_only`, plus local candidates such as paragraph role handoff, certainty support, term stability, heading support fit, and reader-burden detail.
- DraftWriter receives no new external style, compression, or argument-strengthening rules while the current depth-budget smoke failure diagnosis remains active.
- Genre applicability matters. `market_explanation`, `comparison_guide`, and `announcement` can accept stronger clarity/support checks than `daily_activity` or low-intent `company_service_intro`.
- Deterministic QA candidates are possible later, but only after schema, fixture, false-positive, and locality review.
- Existing prompt templates are far below the 120-line preferred limit and contain no external manual text or style-conflict contract IDs.

## What this package rejected

- Full Gist or Web-source text in prompts, config, AGENTS, WORKLOG, or product modules.
- Treating any external writing reference as a notecode policy replacement.
- One sentence per line, footnotes, technical-book columns, universal bold definitions, universal paragraph-initial connectors, or strict technical tone across all genres.
- Compression-first editing while `body_length_floor_chars` and the depth-budget contract remain unresolved.
- Broad prompt tuning, broad LLM-as-judge style review, AI-detector-style stylometry gates, hard banned-word deletion, and duplicate forbidden-phrase lists.
- Whole-article style rewrite instead of flagged-span targeted rewriting.
- Route A fallback, writer-only fallback, old repair loop revival, raw full `source_documents` pass, QA threshold relaxation, and repair acceptance relaxation.
- Any current-source-of-truth promotion from this package without current-doc updates.

## Current source-of-truth boundary

Current source-of-truth remains outside this package:

- `notecode/AGENTS.md`
- `notecode/0506/AGENTS.md`
- `notecode/0506/docs/CURRENT_ALGORITHM.md`
- `notecode/0506/docs/PIPELINE_SPEC.md`
- `notecode/0506/docs/CONFIG_AND_PERSONA_POLICY.md`
- `notecode/0506/docs/JAPANESE_STYLE_POLICY.md`
- `notecode/0506/docs/JAPANESE_STYLOMETRY_POLICY.md`
- `notecode/0506/docs/AI_CODING_RULES.md`
- owner-specific artifacts named by the current docs

If this package and the current docs disagree, the current docs win. Stop before implementation or API validation and report `blocked_by_doc_conflict`.

## Do-not-promote boundary

- Do not promote this package, `HANDOFF.md`, or any package artifact into the current algorithm by reference alone.
- Do not update AGENTS, WORKLOG, current algorithm docs, prompt templates, config, schemas, QA code, editor code, or DraftWriter from this package without a later current-doc owner change.
- Do not treat the parked candidates below as selected work.
- Do not start a style-conflict implementation owner while `draft_writer_depth_budget_contract_smoke_failure_diagnosis` remains current.
- Do not use this package to bypass body-floor, source-grounding, targeted-rewrite, prompt-budget, or owner-hygiene rules.

## Implementation preconditions

Implementation may start only after all of these are true:

- Current docs finish or replace `draft_writer_depth_budget_contract_smoke_failure_diagnosis` and select exactly one new current owner.
- The new owner states allowed files and non-owner boundaries before code or API work.
- No current-doc conflict exists. If a conflict exists, stop with `blocked_by_doc_conflict`.
- The owner proves why the selected surface is responsible: structural editor, QA checker, style/editor profile, targeted rewriter, or another narrow home.
- Prompt work, if selected, passes prompt-budget review before edits: no external manual text, no duplicated style tables, at most four compact rule IDs or bullets per stage, and no template over the prompt-bloat threshold.
- QA work, if selected, includes schema review, deterministic fixtures, false-positive fixtures, local issue scope, and no threshold or repair-acceptance relaxation.
- Rewriter work, if selected, proves flagged-span locality, preserved facts, numbers, dates, names, claim IDs, speaker, section purpose, and non-target paragraphs.
- Any API validation is explicitly approved later and happens only after local preflight, tests, and artifact inventory. This package did not run API validation.

## Safe future owners

These are parked candidate owners only. They are not current and not recommended as the immediate next owner.

| Parked candidate owner | Safe only if | Main guard |
|---|---|---|
| `qa_fragment_punctuation_fixture_design` | Current docs select QA fixture design after the smoke diagnosis is closed. | Exclude headings, lists, captions, and acceptable Japanese noun endings. |
| `qa_existing_signal_overlap_map` | Current docs select read-only QA overlap mapping. | Reuse existing issue types before adding schema surface. |
| `qa_support_context_candidate_design` | Current docs select support-context design. | Marker presence alone is never a ban; source support and genre context are required. |
| `targeted_rewriter_locality_fixture_design` | QA emits local scopes first. | Preserve facts, claim IDs, speaker, and non-target paragraphs. |
| `genre_contract_profile_audit` | Current docs allow profile/config audit. | Do not edit prompts or DraftWriter. |
| `structural_editor_contract_fixture_design` | Current docs select structural-editor fixture design. | No new facts, rigid templates, or whole-article rewrites. |
| `japanese_quality_checker_issue_type_impl` | A prior audit selects exactly one deterministic issue family. | Additive signals only; no QA threshold or repair-acceptance relaxation. |

## Blocked / forbidden owners

The following owner shapes are blocked or forbidden from this package:

- `draft_writer_external_style_prompt_impl`
- `compression_first_redundancy_impl`
- `broad_prompt_tuning`
- `external_manual_prompt_paste`
- `broad_llm_style_review_loop`
- `ai_detector_stylometry_gate`
- `duplicate_forbidden_word_watchlist`
- `whole_article_style_rewrite`
- `route_a_fallback_revival`
- `writer_only_fallback_revival`
- `old_repair_loop_revival`
- `raw_full_source_documents_handoff`
- `qa_threshold_relaxation`
- `repair_acceptance_relaxation`

## Prompt bloat guard

- Prompt bloat status: none.
- No prompt templates were changed by this package.
- `PROMPT_BUDGET_COLLISION_CHECK.md` records current templates as under 120 lines with no external manual contamination.
- Future prompt work must not paste external references, copy genre tables into prompts, duplicate watchlists, or render more than four compact style-conflict rules per stage.
- DraftWriter prompt changes remain blocked while the current owner is `draft_writer_depth_budget_contract_smoke_failure_diagnosis`.

## Module bloat guard

- Module bloat status: none.
- No product modules, schemas, tests, prompt templates, config files, AGENTS files, WORKLOG files, or API artifacts were changed by this package closure.
- Future implementation must use one issue, one hypothesis, and one owner scope.
- Do not create a new style-policy module when existing homes can own the behavior: style policy, stylometry policy, Japanese quality checker, structural editor, style editor, targeted rewriter, or profile/config data.
- Do not hard-code large prompt bodies, persona tables, external reference text, or duplicate watchlists in Python modules.

## QA / repair / threshold guard

- QA thresholds were not relaxed.
- Repair acceptance was not relaxed.
- New QA candidates remain proposal candidates only.
- Any future QA signal must be additive, local, and mapped to a concrete fact-preserving fix or report-only output.
- Do not add a broad LLM review loop.
- Do not use stylometry as a binary AI-written publication gate.
- Targeted rewriting must remain flagged-spans-only and must preserve source-grounded facts, claim IDs, speaker, numbers, dates, names, section purpose, and non-target paragraphs.
- Style cleanup must not reduce body-floor compliance or delete source-backed depth.

## Recommended next action

Close this package as `handoff_completed` and return attention to the current Route B / 0506 owner before any style-conflict implementation.

Recommended next owner, one only:

```text
draft_writer_depth_budget_contract_smoke_failure_diagnosis
```

## Final validation checklist

- Required headings present: yes.
- `Status: proposal / non-current` present: yes.
- `Current owner preserved: draft_writer_depth_budget_contract_smoke_failure_diagnosis` present: yes.
- Product code changed: false.
- Prompt template changed: false.
- AGENTS changed: false.
- WORKLOG changed: false.
- API validation used: false.
- Route A fallback used: false.
- Writer-only fallback used: false.
- Raw full `source_documents` passed: false.
- QA threshold relaxed: false.
- Repair acceptance relaxed: false.
- Prompt bloat: none.
- Module bloat: none.
- Recommended next owner count: one.
- Current source-of-truth promotion: false.
- Implementation owner started: false.
- Current-doc conflict found: false.
