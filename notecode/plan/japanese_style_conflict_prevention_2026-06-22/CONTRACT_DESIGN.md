# Japanese Style Conflict Contract Design

Status: proposal / non-current

Current owner preserved: `draft_writer_depth_budget_contract_smoke_failure_diagnosis`

Owner executed in this document: `style_conflict_contract_design`

Decision: contract design completed as a proposal artifact only. No product code, prompt template, AGENTS, WORKLOG, or API-validation change is authorized by this document.

## Scope

This document compresses the external Japanese writing reference research in `INVENTORY.md` and `RESEARCH_PLAN.md` into a short, Route B / 0506-safe contract design.

It decides:

- which ideas remain compact contract candidates,
- which ideas belong to future article-brief/profile/QA/rewriter surfaces,
- which ideas are rejected or deferred,
- which genres can receive stricter argument and clarity checks,
- how to prevent collisions with body floor, source-grounding, note/Hatena naturalness, prompt budget, deterministic QA, and existing watchlists.

This is a design artifact for a proposal package. It is not the current notecode algorithm and does not change the current Route B / 0506 next owner.

## Non-goals

- Do not implement product code.
- Do not change prompt templates.
- Do not change AGENTS.md or WORKLOG.md.
- Do not run API validation.
- Do not reopen Route A fallback, writer-only fallback, old repair loops, or raw full `source_documents` pass.
- Do not relax QA thresholds or repair acceptance.
- Do not add broad prompt tuning.
- Do not paste the full Gist or full Web references into any runtime surface.
- Do not replace the current source of truth.
- Do not place new external-reference rules in DraftWriter while `draft_writer_depth_budget_contract_smoke_failure_diagnosis` remains current.

## Current Source-of-truth Boundary

The current source of truth remains:

- `notecode/AGENTS.md`
- `notecode/0506/AGENTS.md`
- `notecode/0506/docs/CURRENT_ALGORITHM.md`
- `notecode/0506/docs/PIPELINE_SPEC.md`
- `notecode/0506/docs/CONFIG_AND_PERSONA_POLICY.md`
- `notecode/0506/docs/JAPANESE_STYLE_POLICY.md`
- `notecode/0506/docs/JAPANESE_STYLOMETRY_POLICY.md`
- `notecode/0506/docs/AI_CODING_RULES.md`
- owner-specific artifacts named by those current docs

If this proposal conflicts with the files above, the current docs win. Stop before implementation or API validation and report the conflict.

The current Route B / 0506 owner remains:

```text
draft_writer_depth_budget_contract_smoke_failure_diagnosis
```

## External Reference Boundary

External writing references are treated as proposal seeds only.

Allowed use:

- summarize rule families,
- derive compact rule IDs,
- identify collision risks,
- propose QA issue candidates,
- propose editor-profile notes.

Forbidden use:

- copying full external text into prompts, config, AGENTS, WORKLOG, or product modules,
- using an external source as a notecode policy replacement,
- converting a technical-writing manual into a general note/Hatena blog style,
- using external concision norms to override `body_length_floor_chars`,
- adding unsupported causal bridges in the name of stronger argumentation.

## Contract Design Principles

1. Preserve the current owner. This package may recommend a future proposal owner, but it does not promote itself into the current Route B / 0506 source of truth.
2. Keep DraftWriter out of scope. DraftWriter is currently tied to body-floor and depth-budget behavior, so external style rules must not be inserted there in this owner.
3. Prefer short contract vocabulary over manuals. Future surfaces should use rule IDs or flags, not long prose.
4. Preserve source-grounded depth. Style cleanup must not remove assigned-claim depth, selected-excerpt texture, section purpose, or body-floor buffer.
5. Treat argument strengthening as narrowing, qualifying, reordering, or clarifying existing support. It must not create a new cause, result, comparison, benefit, number, or third-party feeling.
6. Apply strictness by genre. Technical-document clarity can help `market_explanation`, `comparison_guide`, and `announcement`, but must stay softer for note/Hatena owned-media and daily activity genres.
7. Prefer deterministic QA where possible. LLM/editor judgment may be used only as a local editor decision or flagged-span rewrite input, not as a broad review loop.
8. Avoid watchlist duplication. New wording risks must attach to existing risky phrase, model-frequent word, or issue-type surfaces after audit.

## Adopted Contract Candidates

These are adopted as design candidates only. They are not implemented here.

| Contract candidate | Short value | Future home | Adoption shape | Guard |
|---|---|---|---|---|
| Floor-safe redundancy | `floor_safe_local_only` | article brief metadata / style profile / QA issue wording | Remove only repeated, empty, or decorative text when the fix is length-neutral or floor-safe. | Never make redundancy removal higher priority than body-floor compliance. |
| Source-grounded argument | `source_claims_only` | structural editor / Japanese quality checker / targeted rewriter | Clarify logic by using confirmed claims, assigned claim IDs, selected excerpts, or weaker supported wording. | No new causal bridge, benefit, comparison, result, or unsupported certainty. |
| Genre-weighted strictness | `genre_weighted` | style profile / editor profile | Apply technical-writing strictness only where the genre benefits from it. | Do not harden soft blog genres into technical essays. |
| Rewriter locality | `flagged_spans_only` | targeted rewriter handoff | Rewrite only QA-flagged spans or sections and preserve facts, claim IDs, speaker, and non-target paragraphs. | No whole-article rewrite for style. |
| Paragraph role handoff | `paragraph_role_handoff` | structural editor / QA candidate | Check whether a paragraph receives context, performs one local function, and hands off to the next paragraph. | Do not force rigid paragraph templates or one-sentence-one-line style. |
| Certainty support | `certainty_within_support` | Japanese quality checker | Flag certainty markers that exceed the confirmed support shape. | Do not ban certainty markers globally. |
| Term stability | `term_stability_local` | structural editor / QA candidate | Flag confusing key-term drift across headings and body. | Do not ban natural paraphrase. |
| Heading support fit | `heading_support_fit` | structural editor / QA candidate | Flag headings that promise more proof than assigned claims can support. | Do not expand H1/H2 prompt burden broadly. |
| Reader-burden detail | `reader_burden_detail_local` | editor profile / style editor / targeted rewriter | Flag decorative details that are not reused and are not required for identity, responsibility, dates, prices, schedules, or source anchors. | Do not delete source-required specifics. |

## Rejected / Deferred Candidates

| Candidate | Decision | Reason |
|---|---|---|
| Full external Gist or Web source as prompt text | Rejected | Violates prompt compactness and creates a competing style manual. |
| One sentence per line | Rejected | Conflicts with note/Hatena paragraph rhythm. |
| Footnotes, technical-book columns, universal bold definitions | Rejected | Not a normal Route B blog/article format. |
| Universal paragraph-initial connectors | Rejected | Conflicts with connector-repetition and natural blog rhythm. |
| Compression-first editing | Rejected while body-floor owner is unresolved | Directly risks `body_length_floor_chars`. |
| Hard banned-word deletion | Rejected | Existing policy treats risky phrases as contextual risks, not global bans. |
| Strict technical-writing tone for all genres | Rejected | Conflicts with `daily_activity`, case/story warmth, and low-intent company/service hooks. |
| Broad prompt tuning for style | Rejected | Violates prompt patch discipline and current owner scope. |
| Broad LLM-as-judge style review | Rejected | Conflicts with deterministic QA preference and risks review sprawl. |
| Whole-article style rewrite | Rejected | Violates targeted rewriter locality. |
| DraftWriter placement | Deferred / blocked | Current DraftWriter owner is body-floor depth-budget smoke diagnosis. |
| Style-editor prompt changes | Deferred | Requires future owner proof and prompt budget review. |
| Watchlist expansion | Deferred | Requires deterministic audit proving a recurring uncaught gap. |
| Semantic automatic rewrite for causality or reader burden | Deferred | Start as editor-profile/report-only unless fixtures prove safe locality. |

## Placement Matrix

| Surface | Contract placement | Allowed shape | Not allowed | Future validation |
|---|---|---|---|---|
| `article_brief` | Optional future metadata such as `style_conflict_contract` | Short flags: `floor_safe_local_only`, `source_claims_only`, `genre_weighted`, `flagged_spans_only` | Full manuals, external source text, DraftWriter compression instruction | Schema/config test plus prompt-render check; do not render into DraftWriter while current owner remains. |
| `style_profile` | Genre-weighted strictness and notation/rhythm hints | Compact profile notes for soft vs strict application | Global technical tone, hard banned words, one-sentence-one-line | Profile fixture proving note/Hatena rhythm remains genre-sensitive. |
| `editor_profile` | Local editor notes for paragraph role, reader burden, heading support fit | Short notes that guide structural/style editor attention | Whole-article rewrite instruction, source expansion, source-claim deletion | Editor pass report fixture with unchanged facts and claim IDs. |
| `structural_editor` | Best future home for paragraph role handoff, heading specificity, and local logical continuity | Reorder, split, narrow, or qualify existing text without adding claims | New facts, rigid templates, universal connector starts, full rewrite | Structural report fixture and source-claim preservation check. |
| `japanese_quality_checker` | Deterministic or near-deterministic issue candidates | Issue types with span/section-local reason and fix instruction | Threshold relaxation, duplicate watchlists, broad LLM review loop | Deterministic QA candidate audit and no-threshold-change tests. |
| `targeted_rewriter` | Only consumes flagged issues | Span-limited fixes that preserve facts, numbers, dates, names, claim IDs, speaker, and non-target paragraphs | Rewriting unflagged sections, adding support, changing narrator, weakening acceptance rules | Locality fixture: bounded changed spans, preserved non-target paragraphs, final floor not worse. |

DraftWriter placement is intentionally absent. During the preserved current owner, DraftWriter must not receive new external style, compression, or argument-strengthening rules.

## Genre Applicability Matrix

| Genre | Strong application | Moderate application | Weak / avoid | Placement bias |
|---|---|---|---|---|
| `market_explanation` | Source-grounded argument scope, term stability, supported certainty, causal qualification, paragraph role handoff | Scannable headings and actor clarity | Compression-first editing, technical-book formatting, third-party PDF-summary voice | Structural editor and QA candidates are the safest homes. |
| `company_service_intro` | Unsupported praise detection, first-person consistency, third-party leakage, company-name-as-narrator risk | Heading support fit, decorative detail burden, low-intent reader hook clarity | Technical essay tone, over-compression, deleting source-backed service detail | Style/editor profile and QA; preserve low-intent note/Hatena hook. |
| `announcement` | Explicit dates, actors, targets, changes, cautions, and public-document clarity | Heading clarity and punctuation consistency | Long blog expansion, dramatic rhetoric, unnecessary warmth | Style/editor profile can be stricter; keep concise structure. |
| `case_study` | Customer voice attribution, outcome support, causality qualification, no invented customer feelings | Paragraph role handoff and term stability | Unsupported emotional or result claims, testimonial-ad blending | QA and targeted rewriter with strict attribution preservation. |
| `comparison_guide` | Fair comparison, supported criteria, term stability, no unsupported superiority | Heading specificity and reader-burden detail | Ranking/SEO generic advice, competitor claims without source | Structural editor and QA candidates can be relatively strong. |
| `daily_activity` | Source-near scene detail, natural rhythm, no invented feelings/outcomes | Ending and paragraph rhythm checks | Technical-document rigidity, 1400-char padding from thin sources, hard argument templates | Style profile only lightly; QA focuses on invented outcomes and generic reflection. |

## Collision Prevention Rules

### `body_length_floor_chars` vs compression

- Redundancy removal must be `floor_safe_local_only`.
- Do not place compression rules in DraftWriter while the current owner remains unresolved.
- Do not delete assigned-claim depth, selected-excerpt texture, section purpose, or body-floor buffer.
- If final floor is active, a cleanup must be length-neutral, length-preserving, or allowed only when a sufficient floor buffer exists.

### source-grounding vs論証強化

- Argument improvement means narrowing, qualifying, reordering, or clarifying existing support.
- Use only confirmed claims, assigned claim IDs, selected excerpts, and do-not-infer rules.
- Do not create new causes, benefits, outcomes, numbers, comparisons, rankings, or third-party feelings.
- `oversimplified_causality` fixes should weaken or qualify a claim when support is partial, not add missing support.

### note/Hatena自然さ vs技術文書の硬さ

- Apply technical-writing strictness to claim support, actor clarity, heading support fit, and certainty scope.
- Preserve note/Hatena paragraph rhythm, natural line breaks, genre warmth, and self-perspective.
- Do not apply one-sentence-one-line, footnotes, strict definition formatting, or technical-column conventions globally.
- `announcement` may be stricter; `daily_activity` and low-intent company/service introductions must remain softer.

### prompt budget vs長文規範

- Do not paste external manuals, Gist text, or Web-source text into prompt templates.
- Future prompt rendering, if ever approved, should use at most four compact bullets or rule IDs per stage.
- Long rationale stays in docs. Config/persona surfaces carry short IDs.
- Any prompt template over 120 lines requires prompt-bloat review; over 180 lines is blocked pending review.

Current prompt template line counts checked read-only:

| Prompt template | Lines |
|---|---:|
| `draft_writer.md` | 11 |
| `japanese_quality_checker.md` | 6 |
| `structural_editor.md` | 8 |
| `style_editor.md` | 6 |
| `targeted_rewriter.md` | 4 |

### deterministic QA vs LLM review sprawl

- Deterministic QA should own sentence fragments, connectors, ending/rhythm signals, first-person variants, model-frequent words, body floor, and surface marker candidates.
- Semantic/editor judgment may own paragraph role drift, causality narrowing, reader-burden detail, and rhetorical overstatement.
- Do not add a broad LLM review loop or LLM-as-judge pass.
- Every rewrite-triggering issue must map to a local, fact-preserving fix.

### watchlist duplication

- Keep `JAPANESE_STYLE_POLICY.md` and `JAPANESE_STYLOMETRY_POLICY.md` as the watchlist homes.
- Do not create a second forbidden phrase list.
- Prefer issue families such as `generic_transition_stack` or `unsupported_rhetorical_intensity` over long string lists.
- Add terms only after deterministic audit proves an uncaught recurring failure and maps them to existing issue types.

## Compact Contract Examples

### Article-brief/profile metadata candidate

```json
{
  "style_conflict_contract": {
    "redundancy_mode": "floor_safe_local_only",
    "argument_scope": "source_claims_only",
    "technical_strictness": "genre_weighted",
    "rewrite_scope": "flagged_spans_only"
  }
}
```

### Editor-profile note candidate

```json
{
  "editor_profile_note": {
    "paragraph_role_handoff": "check local receive-do-pass continuity",
    "heading_support_fit": "heading must not promise broader proof than assigned claims",
    "reader_burden_detail": "remove only decorative details that are not source-required and not floor-critical"
  }
}
```

### QA issue candidate shape

```json
{
  "type": "certainty_without_support",
  "severity": "medium",
  "scope": "sentence",
  "fix_instruction": "weaken or qualify the certainty using only confirmed claims"
}
```

### Targeted rewriter handoff candidate

```json
{
  "rewrite_locality": {
    "scope": "flagged_spans_only",
    "preserve_claim_ids": true,
    "preserve_numbers_dates_names": true,
    "preserve_speaker": true,
    "do_not_add_support": true
  }
}
```

## Deterministic QA Candidate List

| Candidate issue type | Detection class | Rewrite trigger stance | Notes |
|---|---|---|---|
| `sentence_fragment_or_broken_predicate` | Deterministic after Japanese sentence-boundary fixture audit | Strong candidate | Directly addresses smoke-review punctuation/fragment findings. Exclude headings and list fragments. |
| `generic_transition_stack` | Deterministic overlap with existing connector metrics | Audit first | Avoid duplicate watchlist; map to existing connector/style issues where possible. |
| `certainty_without_support_marker` | Deterministic marker plus claim-category support check | Candidate after fixture audit | Marker is not a ban. Only flag when support shape does not permit certainty. |
| `heading_specificity_mismatch_candidate` | Heuristic deterministic signal, semantic confirmation likely | Report or medium severity first | Broad promise words plus low assigned-claim/source thickness can flag review. |
| `decorative_summary_sentence_candidate` | Heuristic deterministic signal | Report-only until floor-safe tests pass | Must not shorten floor-active articles below buffer. |
| `term_drift_candidate` | Deterministic surface inventory plus semantic confirmation | Report-only first | Multiple labels for key concepts can be listed; rewrite needs editor judgment. |
| `punctuation_spacing_or_symbol_mismatch` | Deterministic | Safe low-risk candidate | Formatting-only if it does not change content. |
| `pos_phrase_pattern_monotony_candidate` | Deterministic stylometry signal | Report-only | Must not become an AI-detector or publication gate. |
| `unsupported_rhetorical_intensity_marker` | Deterministic marker plus support check | Candidate after audit | Prefer issue family over new banned-word list. |
| `reader_burden_detail_marker` | Weak deterministic signal | Report-only | Needs editor judgment to avoid deleting source-required detail. |

Existing issue types that should be reused before adding new ones:

- `duplication`
- `ai_like_phrase`
- `model_frequent_word`
- `generic_encouragement_phrase`
- `connector_repetition`
- `paragraph_rhythm_monotony`
- `line_break_monotony`
- `ending_bucket_monotony`
- `style_mismatch`
- `formatting_mismatch`

## LLM-editor-only Candidate List

These candidates should not become broad LLM review loops. They belong only to structural/style editor judgment, editor-pass reports, or targeted rewriting after a QA issue provides a local scope.

| Candidate | Safe editor-only shape | Guard |
|---|---|---|
| `oversimplified_causality` | Narrow or qualify a causal sentence using existing claims. | Do not add causes or outcomes. |
| `paragraph_role_drift` | Split, reorder, or add a transition using existing content only. | Do not force fixed paragraph templates. |
| `term_drift_semantic_confirmation` | Normalize confusing concept labels when they refer to the same source-backed concept. | Do not ban natural paraphrase. |
| `reader_burden_detail` | Remove or move decorative detail only when it is not source-required and not floor-critical. | Preserve identity, responsibility, dates, prices, schedules, and source anchors. |
| `rhetorical_overstatement` | Soften unsupported drama or self-praise. | Preserve source-backed achievements. |
| `heading_support_fit_semantic_confirmation` | Narrow a heading so it matches assigned claims. | Do not broaden claims or add proof. |

## Prompt Budget Guard

No prompt-template changes are authorized by this document.

Future prompt-related work must report:

- changed prompt files,
- rendered prompt line count,
- number of style-conflict rules rendered,
- whether external source wording was copied,
- whether the same rule appears in multiple prompts,
- whether the template exceeds 120 lines,
- whether any template exceeds 180 lines and is blocked for review.

Allowed future rendering shape, if a later owner approves prompt work:

```text
style_conflict_contract:
- Preserve floor-safe source-backed depth.
- Keep logical bridges inside confirmed claims.
- Apply technical strictness by genre.
- Rewrite only flagged spans.
```

Maximum rendered contract: four compact bullets or four rule IDs per stage.

## Future Implementation Slice Plan

Any future implementation requires current docs to select a new owner first. Until then, this remains a non-current proposal.

1. `deterministic_qa_candidate_audit`
   - Read current QA/stylometry code and fixtures.
   - Classify candidates as existing coverage, safe deterministic addition, semantic/report-only, or rejected.
   - Product code changed: false unless a later implementation owner is explicitly selected.
   - API used: false.

2. `genre_contract_profile_audit`
   - Compare article genre config, style profiles, and editor profiles against this matrix.
   - Decide whether `genre_weighted` belongs in profile data.
   - Do not edit prompts.

3. `structural_editor_contract_fixture_design`
   - Design fixtures for paragraph role handoff and heading support fit.
   - Prove facts, numbers, dates, names, speaker, and claim IDs stay unchanged.

4. `japanese_quality_checker_issue_type_impl`
   - Only after audit selects deterministic candidates.
   - Add one issue family at a time.
   - Do not relax thresholds or repair acceptance.

5. `targeted_rewriter_locality_guard_impl`
   - Only after QA emits local scopes.
   - Test bounded span edits and preservation of non-target paragraphs.

6. `prompt_budget_collision_check`
   - Count prompt templates and rendered prompts before any prompt change.
   - Block if external manuals or duplicated rules would enter prompt text.

7. `non_current_proposal_handoff`
   - Close or hand off the proposal package without promoting it to current source of truth.
   - Record that current Route B / 0506 owner remains whatever current docs say at that time.

## Recommended Next Owner

Recommended next owner inside this non-current proposal package:

```text
deterministic_qa_candidate_audit
```

Recommended current Route B / 0506 owner remains:

```text
draft_writer_depth_budget_contract_smoke_failure_diagnosis
```

Reason: this design keeps external writing norms compressed into short contracts. The next safe proposal step is to audit which QA candidates are already covered, which are deterministic, and which must stay editor-only or rejected. No implementation should start until current docs select a new current owner.

## Validation Summary

- Status included: yes, proposal / non-current.
- Current owner preserved: yes, `draft_writer_depth_budget_contract_smoke_failure_diagnosis`.
- Scope included: yes.
- Non-goals included: yes.
- Current source-of-truth boundary included: yes.
- External reference boundary included: yes.
- Contract design principles included: yes.
- Adopted contract candidates included: yes.
- Rejected / deferred candidates included: yes.
- Placement matrix included: yes.
- Genre applicability matrix included: yes.
- Collision prevention rules included: yes.
- Compact contract examples included: yes.
- Deterministic QA candidate list included: yes.
- LLM-editor-only candidate list included: yes.
- Prompt budget guard included: yes.
- Future implementation slice plan included: yes.
- Recommended next owner included: yes.
- Product code changed: false.
- Prompt template changed: false.
- API validation used: false.
- Route A fallback used: false.
- Writer-only fallback used: false.
- Raw full `source_documents` passed: false.
- QA threshold relaxed: false.
- Repair acceptance relaxed: false.
- Prompt bloat: none.
- Module bloat: none.
