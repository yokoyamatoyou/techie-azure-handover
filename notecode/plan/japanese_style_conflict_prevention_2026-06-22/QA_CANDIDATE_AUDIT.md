# Deterministic QA Candidate Audit

Status: proposal / non-current

Current owner preserved: `draft_writer_depth_budget_contract_smoke_failure_diagnosis`

Owner executed in this document: `deterministic_qa_candidate_audit`

Decision: QA candidate audit completed as a proposal artifact only. No product code, prompt template, AGENTS, WORKLOG, or API-validation change is authorized by this document.

## Scope

This audit classifies the QA candidates in `CONTRACT_DESIGN.md` into:

- deterministic candidates that can be detected from characters, sentence/paragraph shape, headings, connector/endings, existing watchlists, subject/viewpoint terms, symbols, or other surface patterns;
- near-deterministic candidates where surface detection is possible, but source support or genre context is needed before rewrite;
- LLM-editor-only candidates that require semantic judgment about argument sufficiency, reader burden, causal adequacy, or paragraph function;
- rejected or deferred candidates that collide with body floor, source-grounding, note/Hatena naturalness, prompt budget, current owner boundaries, or existing watchlist ownership.

The audit is read-only except for this proposal artifact.

## Non-goals

- Do not implement product code.
- Do not change prompt templates.
- Do not change AGENTS.md or WORKLOG.md.
- Do not run API validation.
- Do not reopen Route A fallback, writer-only fallback, old repair loops, or raw full `source_documents` pass.
- Do not relax QA thresholds or repair acceptance.
- Do not propose broad prompt tuning or a broad LLM review loop.
- Do not create a second forbidden-word/watchlist surface.
- Do not replace current source-of-truth docs or the current Route B / 0506 owner.
- Do not make redundancy removal or compression compete with `body_length_floor_chars`.

## Current QA/stylometry baseline

Read-only files checked:

- `notecode/0506/app/agents/japanese_quality_checker.py`
- `notecode/0506/app/services/stylometry.py`
- `notecode/0506/app/agents/targeted_rewriter.py`
- `notecode/0506/app/config/stylometry.yaml`
- `notecode/0506/app/schemas/quality_check.schema.json`
- related tests in `tests/test_phase2_foundation.py`, `tests/test_phase4_llm_pipeline.py`, `tests/test_phase6_quality_evaluation.py`, and `tests/test_editor_output_guard.py`

Current deterministic stylometry signals:

- sentence count, average/median/max sentence length, sentence-length variance;
- paragraph count and paragraph shape from blank-line paragraphs;
- sentence ending buckets: `できます`, `ました`, `ます`, `です`, `でしょう`, `ください`, question, noun ending, other;
- repeated configured connectors, currently counted across the whole text;
- first-person variants and third-party viewpoint terms from config;
- repeated model-frequent words from the existing watchlist;
- issue candidates for `sentence_too_long`, `narrator_mixing`, `third_party_viewpoint_leakage`, `connector_repetition`, `model_frequent_word`, `ending_bucket_monotony`, and `paragraph_rhythm_monotony`.

Current quality checker additions:

- converts stylometry issue candidates into QA issues;
- flags a small hardcoded risky phrase subset as `ai_like_phrase`;
- checks narrator mismatch and self-viewpoint owner mismatch;
- flags reader-meta / low-density bridge sentences through `reader_meta_sentence`;
- checks `body_length_below_floor` and `missing_h1` when `body_length_floor_chars` is present.

Current gaps relevant to this audit:

- `quality_check.schema.json` already permits more issue types than the code emits, including `unsupported_claim`, `duplication`, `line_break_monotony`, `generic_encouragement_phrase`, `nominalization_overuse`, and `formatting_mismatch`.
- New proposal-specific issue types such as `certainty_without_support`, `sentence_fragment_or_broken_predicate`, and `heading_support_fit` are not currently in the schema.
- Current stylometry policy mentions Sudachi/POS signals, but the implemented `stylometry.py` does not currently tokenize with Sudachi or compute POS metrics.
- `targeted_rewriter.py` instructs "Rewrite only flagged spans" but does not itself enforce span locality; any future rewrite-triggering issue should carry local scope and fixtures.

## Deterministic candidate table

| Candidate | Existing coverage | Suggested issue surface | Audit decision | Rewrite stance |
|---|---|---|---|---|
| `sentence_fragment_or_broken_predicate` | Not covered by current QA; manual smoke noted sentence-fragment/punctuation issues. | New issue type later, or map only very narrow cases to `formatting_mismatch` after schema review. | Strong deterministic candidate after fixture audit. | Rewrite-trigger candidate only for sentence-local spans, excluding headings/lists. |
| `punctuation_spacing_or_symbol_mismatch` | Schema has `formatting_mismatch`, but code does not emit it. | Reuse `formatting_mismatch`. | Safe deterministic candidate if kept formatting-only. | Rewrite-trigger candidate for punctuation-only fixes. |
| `generic_transition_stack` | Partial overlap through `connector_repetition`; current count is whole-text repetition. | Prefer existing `connector_repetition` / `ai_like_phrase`. | Deterministic overlap; audit before adding a new family. | Rewrite only repeated paragraph-initial or transition-only spans. |
| `pos_phrase_pattern_monotony_candidate` | Policy mentions POS n-grams, code does not implement POS. | Existing `sentence_rhythm_monotony`, `nominalization_overuse`, or `style_mismatch` depending on signal. | Deterministic report-only candidate until tokenizer/POS fixtures exist. | Report-only first; no AI-detector-style gate. |
| `line_break_monotony` | Schema and docs mention it; current code does not emit it. | Existing `line_break_monotony`. | Deterministic candidate via blank-line interval / repeated line count. | Rewrite only if local line-break fix preserves facts and floor. |
| Existing watchlist repetition | Current `model_frequent_word` detects count >= 2. | Existing `model_frequent_word` / `generic_encouragement_phrase`. | Already deterministic; do not duplicate watchlist. | Current rewrite path may reduce repeated terms; preserve source-backed terms. |
| Existing narrator/viewpoint terms | Current `narrator_mixing`, `third_party_viewpoint_leakage`, `first_person_inconsistency`, `viewpoint_owner_mismatch`. | Existing issue types. | Already deterministic enough for current use. | Rewrite can normalize narrator if source and speaker are preserved. |
| Body floor and H1 | Current `body_length_below_floor`, `missing_h1`. | Existing issue types. | Baseline guard only, not a style-conflict adoption candidate. | Do not let any style QA fix reduce body-floor compliance. |

## Near-deterministic candidate table

| Candidate | Surface signal | Context needed | Audit decision | Rewrite stance |
|---|---|---|---|---|
| `certainty_without_support_marker` | Strong certainty words such as `必ず`, `すべて`, `唯一`, `No.1`, `確実に`. | Confirmed claims, source category, genre, and whether the marker is quoted or source-backed. | Near-deterministic candidate. Marker detection is deterministic, but support check is required. | Rewrite by weakening or qualifying only when support is insufficient; never add support. |
| `unsupported_rhetorical_intensity_marker` | Intensifiers, superlatives, dramatic setup, unsupported praise terms. | Source support and genre tolerance, especially case study / daily activity warmth. | Near-deterministic candidate. Prefer issue family over new banned terms. | Report or local softening only; preserve supported achievements. |
| `heading_specificity_mismatch_candidate` | Broad promise words in headings, duplicate/generic headings, heading claims broader than source thickness. | Assigned claim IDs, source thickness, article genre, and whether heading is intentionally broad. | Near-deterministic candidate; report or medium severity first. | Narrow heading only after semantic confirmation. |
| `decorative_summary_sentence_candidate` | Summary-only closer, transition-only sentence, no source term/claim noun/reader action. | Body-floor buffer, section purpose, genre ending style. | Near-deterministic report-only candidate until floor-safe fixtures pass. | Do not shorten floor-active articles below buffer. |
| `term_drift_candidate` | Same key concept appears under multiple surface labels across headings/body. | Whether labels are synonyms, natural paraphrases, or source-backed distinct terms. | Near-deterministic inventory/report candidate. | Rewrite only after semantic confirmation. |
| `reader_burden_detail_marker` | Parenthetical detail, unused proper names, repeated minor details, list-like side detail. | Whether detail anchors identity/responsibility/dates/prices/schedules/source support. | Weak near-deterministic candidate; high false-positive risk. | Report-only; editor judgment before deletion. |
| `decorative_detail_floor_safe_local_only` | Repeated decorative sentence with no claim or transition role. | Floor buffer and assigned-claim depth. | Deferred near-deterministic candidate. | Length-neutral replacement only unless sufficient floor buffer exists. |

## LLM-editor-only candidate table

| Candidate | Why deterministic QA is insufficient | Safe home | Guard |
|---|---|---|---|
| `oversimplified_causality` | Surface markers cannot decide whether a causal account is sufficient for the source set. | Structural/style editor judgment or local targeted rewrite after a scoped issue. | Narrow or qualify using existing claims; do not add causes, effects, outcomes, or comparisons. |
| `paragraph_role_drift` | Receive-do-pass continuity depends on paragraph function and neighboring context. | Structural editor report / local editor decision. | Do not force rigid paragraph templates or one-sentence-one-line style. |
| `term_drift_semantic_confirmation` | Surface label variation may be natural paraphrase or a real concept blur. | Structural editor or reviewer confirmation. | Preserve natural paraphrase and source terminology. |
| `reader_burden_detail` | Deciding whether a detail burdens the reader depends on source role and later reuse. | Style editor / structural editor judgment. | Do not delete identity, responsibility, dates, prices, schedules, or source anchors. |
| `rhetorical_overstatement` | Drama/self-praise may be appropriate when source-backed or genre-supported. | Style editor judgment. | Soften unsupported intensity; preserve supported achievements and case-study voice. |
| `heading_support_fit_semantic_confirmation` | Heading-to-support fit needs claim semantics and reader expectation. | Structural editor report / local heading rewrite. | Narrow headings; do not broaden proof or add claims. |
| Argument sufficiency / reader load / causal adequacy as a broad review | Requires semantic judgment over the article and source set. | Not a broad loop; only local editor decision when already scoped. | No LLM-as-judge pass and no threshold relaxation. |

## Rejected / deferred candidate table

| Candidate or tendency | Decision | Reason |
|---|---|---|
| Compression-first redundancy QA | Rejected while body-floor owner is unresolved. | Collides with `body_length_floor_chars` and depth-budget contract. |
| DraftWriter placement for external style rules | Deferred / blocked. | Current owner is depth-budget smoke diagnosis; style rules must not enter DraftWriter now. |
| Full external Gist or Web source as prompt/config text | Rejected. | Prompt bloat and competing policy surface. |
| Broad prompt tuning for style | Rejected. | Violates prompt patch discipline and current owner scope. |
| Broad LLM style review loop / LLM-as-judge QA | Rejected. | Conflicts with deterministic QA preference and risks review sprawl. |
| QA threshold relaxation | Rejected. | Explicitly forbidden; new signals must be additive, not a way to pass weaker output. |
| Repair acceptance relaxation | Rejected. | Explicitly forbidden. |
| Duplicate forbidden-word list | Rejected. | Existing risky phrase and model-frequent policy remain the watchlist home. |
| Hard banned-word deletion | Rejected. | Current policy treats words as contextual risks. |
| One sentence per line / footnotes / technical-book formatting | Rejected. | Conflicts with note/Hatena blog naturalness. |
| Strict technical-writing tone for all genres | Rejected. | Would harden `daily_activity`, case/story warmth, and low-intent company/service intros. |
| AI-detector-style stylometry gate | Rejected. | Stylometry is a signal for concrete fixable issues, not a publication gate. |
| Route A fallback / writer-only fallback / raw full source handoff | Rejected. | Explicitly outside current Route B / 0506 boundaries. |

## Required signals per candidate

| Candidate | Minimum required signals before implementation |
|---|---|
| `sentence_fragment_or_broken_predicate` | Sentence split; heading/list/table exclusion; fragment-ending regex; fixture examples including `は。`, `で。`, `を。`, `なのは。`; false-positive examples for acceptable noun endings. |
| `punctuation_spacing_or_symbol_mismatch` | Symbol inventory; repeated punctuation; unbalanced brackets/quotes; markdown heading/list exclusion; formatting-only fix proof. |
| `generic_transition_stack` | Paragraph-initial connector positions; transition-only sentence detection; connector count by paragraph/window; reuse of current connector config. |
| `pos_phrase_pattern_monotony_candidate` | Tokenizer/POS fixture; repeated POS n-gram window; mapping to a concrete issue type; no binary AI-detector acceptance rule. |
| `line_break_monotony` | Blank-line interval distribution; paragraph line count; repeated section shape; genre-specific tolerance. |
| `certainty_without_support_marker` | Certainty marker list or family; quote/source-span exclusion; confirmed-claim support category; genre allowance; local sentence scope. |
| `unsupported_rhetorical_intensity_marker` | Intensity marker family; source-backed achievement/support check; genre warmth allowance; local sentence scope. |
| `heading_specificity_mismatch_candidate` | Markdown heading inventory; heading promise-word family; assigned claim count; source thickness; section purpose; genre. |
| `decorative_summary_sentence_candidate` | Sentence role heuristic; absence of source terms/claim nouns/reader action; body-floor buffer; section ending position. |
| `term_drift_candidate` | Key-term extraction from headings/body; term frequency; alias inventory; source terminology list; semantic confirmation path. |
| `reader_burden_detail_marker` | Detail type marker; whether detail repeats or anchors identity/responsibility/date/price/schedule/source; genre; floor buffer. |
| `oversimplified_causality` | Local causal claim; confirmed support relation; source conflict/do-not-infer check; editor-only judgment. |
| `paragraph_role_drift` | Neighboring paragraph context; section purpose; receive-do-pass function; editor-only judgment. |
| `rhetorical_overstatement` | Overstatement span; support evidence; genre tolerance; editor-only judgment. |

## False positive risks

- Fragment detection can mistake acceptable Japanese noun endings, headings, captions, or intentionally clipped blog rhythm for broken predicates.
- Connector detection can over-penalize ordinary cohesive writing if it only counts total occurrences instead of local stacking or paragraph-initial repetition.
- Certainty markers can be source-backed, quoted, or appropriate in announcements; marker presence alone is not enough.
- Heading support heuristics can punish intentionally broad, reader-friendly headings in note/Hatena articles.
- Decorative summary detection can remove useful reader orientation or late-section closure, and can reduce articles below body floor.
- Term drift detection can punish natural paraphrase or source-provided alternate labels.
- Reader-burden detection can delete source-required identity, dates, prices, schedules, roles, and responsibility anchors.
- POS/phrase monotony can become an AI-detector proxy if it is not tied to a concrete span-local rewrite.
- Technical-writing strictness can flatten `daily_activity`, case-study voice, and low-intent company/service introductions.

## Genre applicability notes

| Genre | Strong candidates | Weak / careful candidates | Avoid |
|---|---|---|---|
| `market_explanation` | Certainty support, term stability, causal qualification, heading support fit, paragraph role report. | Generic transition stack and POS monotony as report-only signals. | Compression of source-backed depth; third-party PDF-summary voice. |
| `company_service_intro` | Unsupported praise/intensity, narrator/viewpoint consistency, heading support fit, generic phrase repetition. | Reader-burden detail only when not source-required and floor-safe. | Technical essay tone; deleting service details needed for low-intent readers. |
| `announcement` | Dates/actors/targets, formatting consistency, certainty support, concise heading fit. | Rhythm/line-break checks with higher tolerance for compactness. | Long blog expansion, dramatic warmth, body-floor style padding. |
| `case_study` | Customer voice attribution, supported outcomes, causality qualification. | Rhetorical overstatement only with source support review. | Invented customer feelings/results; deleting attribution. |
| `comparison_guide` | Supported criteria, term stability, heading support fit, unsupported superiority markers. | Reader-burden detail when comparison axes remain intact. | Ranking/SEO generic claims without source. |
| `daily_activity` | Fragment/punctuation safety, natural rhythm, no invented feelings/outcomes. | Connector/ending checks only lightly. | Technical-document rigidity, hard argument templates, padding thin sources to a large floor. |

## Collision prevention notes

- `body_length_floor_chars` is a protected output contract. QA must not demand redundancy deletion that reduces assigned-claim depth, selected-excerpt texture, section purpose, or floor buffer.
- Source-grounding wins over argument polish. QA must not require a causal bridge, benefit, comparison, result, number, or third-party feeling that is not supported by confirmed claims or selected excerpts.
- note/Hatena naturalness wins over generic technical-document rigidity except for actor clarity, support scope, and formatting safety.
- Existing risky phrase / model-frequent policy remains the watchlist home. Do not create a second list.
- New issue types require schema review, tests, and locality fixtures. This audit does not authorize schema changes.
- New deterministic signals must be additive. They must not relax QA thresholds or repair acceptance.
- Any rewrite-triggering issue must carry local scope and a fact-preserving fix instruction.

## Suggested future implementation slices

These are proposal-package slices only. Current Route B / 0506 owner remains unchanged until current docs update it.

1. `genre_applicability_matrix`
   - Convert this audit's genre notes into strong / moderate / weak / forbidden application by genre.
   - No product code, prompt, AGENTS, WORKLOG, or API changes.

2. `qa_fragment_punctuation_fixture_design`
   - Design fixtures for `sentence_fragment_or_broken_predicate` and `formatting_mismatch`.
   - Include false positives for headings, captions, noun endings, and lists.

3. `qa_existing_signal_overlap_map`
   - Map `generic_transition_stack`, watchlist repetition, line-break monotony, and POS/phrase monotony to existing issue types before any schema expansion.

4. `qa_support_context_candidate_design`
   - Define non-implementation contracts for certainty/intensity/heading support candidates that require `article_brief` and `knowledge_pack` context.

5. `targeted_rewriter_locality_fixture_design`
   - Design fixtures proving bounded changed spans, preserved non-target paragraphs, unchanged numbers/dates/names, unchanged narrator, and no body-floor regression.

6. `prompt_budget_collision_check`
   - Count prompt templates and rendered prompt surfaces only.
   - Confirm no external manual text, duplicate rules, or broad prompt tuning enters prompts.

7. `non_current_proposal_handoff`
   - Close or hand off this package without promoting it to current source of truth.

## Recommended next owner

Recommended next owner inside this non-current proposal package:

```text
genre_applicability_matrix
```

Recommended current Route B / 0506 owner remains:

```text
draft_writer_depth_budget_contract_smoke_failure_diagnosis
```

Reason: the deterministic audit identifies candidate classes and false-positive risks, but genre boundaries still decide which signals can be strong, weak, report-only, or forbidden. No implementation should start before the current docs select a new current owner.

## Validation summary

- Status included: yes, proposal / non-current.
- Current owner preserved: yes, `draft_writer_depth_budget_contract_smoke_failure_diagnosis`.
- Scope included: yes.
- Non-goals included: yes.
- Current QA/stylometry baseline included: yes.
- Deterministic candidate table included: yes.
- Near-deterministic candidate table included: yes.
- LLM-editor-only candidate table included: yes.
- Rejected / deferred candidate table included: yes.
- Required signals per candidate included: yes.
- False positive risks included: yes.
- Genre applicability notes included: yes.
- Collision prevention notes included: yes.
- Suggested future implementation slices included: yes.
- Recommended next owner included: yes.
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
