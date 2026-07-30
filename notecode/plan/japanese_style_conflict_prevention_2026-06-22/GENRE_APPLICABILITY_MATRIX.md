# Genre Applicability Matrix

Status: proposal / non-current

Current owner preserved: `draft_writer_depth_budget_contract_smoke_failure_diagnosis`

Owner executed in this document: `genre_applicability_matrix`

Decision: genre applicability matrix completed as a proposal artifact only. No product code, prompt template, AGENTS, WORKLOG, or API-validation change is authorized by this document.

## Scope

This document converts the proposal-package style candidates into genre-specific application strength.

It uses these application levels:

- `strong`: safe and useful for the genre when implemented by a later approved owner.
- `moderate`: useful, but must remain genre-sensitive and source-backed.
- `weak`: allowed only lightly; avoid turning it into a global rule.
- `report-only`: useful as a diagnostic or reviewer signal, but not an automatic rewrite trigger.
- `forbidden`: must not be applied for this genre because it collides with current Route B / 0506 contracts.

This document does not promote the proposal package into the current Route B / 0506 source of truth.

## Inputs Read

- `AGENTS.md`
- `notecode/AGENTS.md`
- `notecode/0506/AGENTS.md`
- `notecode/plan/japanese_style_conflict_prevention_2026-06-22/README.md`
- `notecode/plan/japanese_style_conflict_prevention_2026-06-22/INVENTORY.md`
- `notecode/plan/japanese_style_conflict_prevention_2026-06-22/RESEARCH_PLAN.md`
- `notecode/plan/japanese_style_conflict_prevention_2026-06-22/CONTRACT_DESIGN.md`
- `notecode/plan/japanese_style_conflict_prevention_2026-06-22/QA_CANDIDATE_AUDIT.md`
- `notecode/0506/docs/CURRENT_ALGORITHM.md`
- `notecode/0506/docs/PIPELINE_SPEC.md`
- `notecode/0506/docs/ARTICLE_GENRE_POLICY.md`
- `notecode/0506/docs/GENRE_ARRIVAL_CONTRACT_MATRIX.md`
- `notecode/0506/docs/JAPANESE_STYLE_POLICY.md`
- `notecode/0506/docs/JAPANESE_STYLOMETRY_POLICY.md`
- `notecode/0506/docs/CONFIG_AND_PERSONA_POLICY.md`
- `notecode/0506/docs/AI_CODING_RULES.md`

## Non-goals

- Do not implement product code.
- Do not change prompt templates.
- Do not change AGENTS.md or WORKLOG.md.
- Do not run API validation.
- Do not reopen Route A fallback, writer-only fallback, old repair loops, or raw full `source_documents` pass.
- Do not relax QA thresholds or repair acceptance.
- Do not copy a full Gist or full Web source into any runtime surface.
- Do not propose broad prompt tuning.
- Do not add module bloat or prompt bloat.
- Do not place new external-reference style rules in DraftWriter while the current owner remains `draft_writer_depth_budget_contract_smoke_failure_diagnosis`.

## Current Boundary

The current Route B / 0506 owner remains:

```text
draft_writer_depth_budget_contract_smoke_failure_diagnosis
```

Non-owner boundaries remain unchanged:

- source-shape detection
- claim allocation and caps
- QA thresholds
- repair acceptance
- Route A fallback
- writer-only fallback
- raw source handoff
- reader-meta filtering
- style postprocessor behavior
- H1 contract
- DraftWriter prompt or depth-budget behavior

This matrix is allowed to recommend only the next docs-only owner inside this non-current proposal package.

## Shared Collision Guards

| Collision area | Guard for all genres |
|---|---|
| body floor | Never turn redundancy removal into compression-first editing. Do not delete source-backed depth, selected-excerpt texture, section purpose, or body-floor buffer. For genres whose current contract allows shorter natural output, report that as a genre boundary rather than weakening QA thresholds here. |
| source-grounding | Argument improvement means narrowing, qualifying, reordering, or clarifying existing support. Do not add new causes, benefits, outcomes, numbers, comparisons, rankings, customer feelings, or third-party reactions. |
| note/Hatena自然さ | Preserve self-perspective, natural paragraph rhythm, uneven but intentional line breaks, and genre warmth. Technical-writing strictness applies to actor clarity, support scope, and formatting safety only. |
| prompt budget | Do not paste external manuals or full source text into prompts. Future rendering, if ever approved by current docs, must use compact rule IDs or at most four short bullets per stage. |
| deterministic QA | New signals must be additive and local. They must not become a broad LLM review loop, an AI-detector gate, or a second forbidden-word list. |
| targeted rewriting | Any rewrite-triggering issue must carry local scope and preserve facts, claim IDs, speaker, numbers, dates, names, section purpose, and non-target paragraphs. |

## Cross-genre Summary

| Genre | Strong | Moderate | Weak | Report-only | Forbidden |
|---|---|---|---|---|---|
| `market_explanation` | argument scope, certainty support, term stability, causal qualification | heading support fit, paragraph role handoff | connector/ending rhythm | paragraph role drift, POS phrase monotony | compression-first editing, third-party PDF-summary voice, unsupported causality |
| `company_service_intro` | narrator consistency, unsupported praise, company-name-as-narrator risk | low-intent hook clarity, heading support fit, decorative detail review | reader-burden detail | term drift, transition stack | technical essay tone, over-compression, deleting source-backed service details |
| `announcement` | dates, actors, targets, changes, cautions, formatting clarity | heading fit, punctuation consistency | rhythm variation | paragraph role drift | long blog expansion, dramatic warmth, body-floor padding, vague actors |
| `case_study` | attribution, supported outcomes, causality qualification | paragraph role handoff, term stability | rhythm and overstatement checks | reader-burden detail | invented customer feelings/results, testimonial-ad blending, unsupported causal success |
| `comparison_guide` | fair criteria, supported selection axes, term stability, unsupported superiority guard | heading support fit, reader-burden detail | connector/rhythm checks | paragraph role drift | ranking/SEO generic advice, unsupported competitor claims, generic recommendation padding |
| `daily_activity` | source-near scene detail, natural rhythm, no invented feelings/outcomes | punctuation/fragments, light ending variation | term stability | connector stack, POS monotony | technical-document rigidity, hard argument templates, 1400-char padding from thin sources |

## market_explanation

Purpose from current docs: explain a market, issue, trend, or background from self-perspective, with light expert commentary and source-grounded explanation.

| Level | Application | Guard |
|---|---|---|
| strong | `source_claims_only`, `certainty_within_support`, `term_stability_local`, causal qualification, supported market-scope wording. | Keep every broader market statement tied to confirmed claims, selected excerpts, or weak supported phrasing. |
| moderate | `heading_support_fit`, paragraph role handoff, heading-to-body continuity, scannable structure. | Do not make headings promise broader proof than assigned claims can support. |
| weak | Connector repetition, ending variation, paragraph rhythm smoothing. | Use only as note/Hatena naturalness signals, not technical essay formatting. |
| report-only | `paragraph_role_drift`, POS/phrase monotony, generic transition stack. | Report shape problems before making rewrite-triggering rules. |
| forbidden | Compression-first editing, one-sentence-one-line, third-party PDF-summary voice, unsupported trend or causality claims, external manual text in prompts. | These collide with body floor, source-grounding, and current `market_explanation` self-perspective. |

### market_explanation collision check

| Check | Result |
|---|---|
| body floor | No conflict if style candidates preserve source-backed depth. Conflict if redundancy cleanup removes explanatory anchors or selected-excerpt texture. |
| source-grounding | Strong application is safe only when argument polish narrows or qualifies claims. Unsupported market trends remain forbidden. |
| note/Hatena自然さ | Technical strictness must not turn the article into a detached analyst report or PDF abstract. |
| prompt budget | Use compact rule IDs only in a future owner. Do not add market-style manuals to prompts. |

## company_service_intro

Purpose from current docs: introduce a company, service, shop, facility, or product/service line from self-perspective, usually with `私たち`, while preserving low-intent reader arrival.

| Level | Application | Guard |
|---|---|---|
| strong | Narrator consistency, third-party leakage detection, unsupported praise/intensity, company-name-as-narrator risk, first-person stability. | Preserve `私たち` or the configured local name as the speaker; do not drift into `同社` profile tone. |
| moderate | Low-intent hook clarity, heading support fit, local decorative detail review, generic strength phrase review. | Keep reader entry natural and source-near; do not delete service details needed by first-time readers. |
| weak | Reader-burden detail and term stability when the source has many names, plans, or features. | Apply only when details are decorative, not required for identity, responsibility, price, schedule, or service understanding. |
| report-only | Transition stack, term drift inventory, reader-burden candidates, heading breadth candidates. | Use as diagnosis before schema, prompt, or rewrite changes. |
| forbidden | Technical essay tone, over-compression, self-praise expansion, unsupported culture/recruiting/backstage additions, deleting source-backed service detail. | These collide with low-intent note/Hatena naturalness, body floor, and source-grounding. |

### company_service_intro collision check

| Check | Result |
|---|---|
| body floor | No conflict if cleanup is local and floor-safe. Conflict if "reader burden" becomes deletion of service detail or body-floor buffer. |
| source-grounding | Strong viewpoint and praise checks support source-grounding. New culture, employee voice, or backstage claims are forbidden unless sourced. |
| note/Hatena自然さ | Must remain a blog introduction for low-intent readers, not a stiff technical profile or sales page. |
| prompt budget | Future profile flags must stay compact; do not add company-intro style essays to prompt templates. |

## announcement

Purpose from current docs: communicate a factual update, event, release, schedule, campaign, or operational notice. Accuracy and clarity override warmth.

| Level | Application | Guard |
|---|---|---|
| strong | Explicit dates, actors, targets, changes, cautions, eligibility, contact/next action, formatting clarity, punctuation/symbol consistency. | Keep subjects explicit for responsibility, schedules, prices, and requests. |
| moderate | Heading support fit, concise heading clarity, certainty support, public-document style clarity. | Use formality only to improve necessary information, not to add stiffness for its own sake. |
| weak | Sentence/paragraph rhythm variation. | Announcement compactness may naturally reduce rhythm variety. Do not over-optimize. |
| report-only | Paragraph role drift, POS/phrase monotony, decorative summary sentence. | Report only unless it hides required information or creates broken sentences. |
| forbidden | Long blog expansion, dramatic warmth, padding to satisfy a blog-length floor, vague actors/dates, invented background, broad CTA escalation. | These collide with the genre's compact notice contract and source-grounding. |

### announcement collision check

| Check | Result |
|---|---|
| body floor | Potential conflict if a generic body floor forces unnecessary expansion. This matrix does not loosen thresholds; it records that announcement should remain concise under current genre policy. |
| source-grounding | Strong application reinforces source-grounding by requiring explicit dates, actors, targets, and cautions. |
| note/Hatena自然さ | Blog warmth is secondary. Naturalness here means clear official notice tone, not diary-like rhythm. |
| prompt budget | No prompt change. Future rules should be formatting and actor-clarity IDs, not a public-document manual. |

## case_study

Purpose from current docs: explain a customer case, testimonial, implementation story, or interview-style outcome while separating customer statements from provider narration.

| Level | Application | Guard |
|---|---|---|
| strong | Customer voice attribution, supported outcome checks, causality qualification, no invented customer feelings, narrator separation. | Keep customer viewpoint only in attributed quotes, paraphrases, or marked sections. |
| moderate | Paragraph role handoff, source-near sequence, term stability, heading support fit. | Connect issue, response, and result using existing claims only. |
| weak | Rhetorical overstatement softening, rhythm/ending variation, reader-burden detail. | Preserve case-story readability and supported achievements. |
| report-only | Reader-burden detail, paragraph role drift, unsupported intensity markers. | Report before rewrite because deletion can remove attribution or sequence. |
| forbidden | Invented satisfaction, invented emotions, unsupported numerical results, testimonial-ad blending, strong causality without support, deleting attribution. | These collide with source-grounding and case-study attribution. |

### case_study collision check

| Check | Result |
|---|---|
| body floor | No conflict if depth comes from source-near sequence and attribution. Conflict if redundancy cleanup removes useful case chronology or floor buffer. |
| source-grounding | Strong application protects grounding by separating provider narration, customer voice, supported outcomes, and allowed inference strength. |
| note/Hatena自然さ | Keep story warmth, but do not inflate emotions or results. |
| prompt budget | Future compact flags are enough; do not add testimonial-writing manuals to prompts. |

## comparison_guide

Purpose from current docs: help readers compare options, choose a service/product, or understand selection criteria from self-perspective without exaggeration.

| Level | Application | Guard |
|---|---|---|
| strong | Fair comparison criteria, supported selection axes, term stability, unsupported superiority guard, no unknown competitor facts. | Use only supported differences and category-level criteria. |
| moderate | Heading support fit, reader-burden detail, paragraph role handoff, causal/criteria qualification. | Headings should match assigned claim depth and source thickness. |
| weak | Connector repetition, ending variation, POS/phrase monotony. | Keep as naturalness signals, not SEO template enforcement. |
| report-only | Paragraph role drift, decorative summary sentence, generic transition stack. | Report before rewrite to avoid removing necessary comparison axes. |
| forbidden | Ranking/SEO generic advice, unsupported competitor claims, hidden sales pitch, "best" claims without support, generic recommendation padding. | These collide with fair comparison and source-grounding. |

### comparison_guide collision check

| Check | Result |
|---|---|
| body floor | No conflict if depth expands supported axes. Conflict if article is padded with generic SEO advice or shortened by removing comparison criteria. |
| source-grounding | Strong application is safe because it blocks unsupported superiority and competitor facts. |
| note/Hatena自然さ | Should remain reader-supportive, not a mechanical ranking article. |
| prompt budget | Future rules should be compact criteria-support IDs, not a comparison-writing prompt expansion. |

## daily_activity

Purpose from current docs: share daily activity, behind-the-scenes scenes, event reports, small updates, or team atmosphere in a natural note/Hatena-like style.

| Level | Application | Guard |
|---|---|---|
| strong | Source-near scene detail, natural rhythm, no invented feelings/outcomes, subject clarity for schedules/responsibility, sentence fragment/punctuation safety. | Expand only from place, action, object, sequence, constraint, and close self-perspective. |
| moderate | Light ending variation, paragraph rhythm checks, safe subject omission checks. | Daily style may use softer rhythm and clipped warmth; do not over-standardize. |
| weak | Term stability and heading support fit. | Apply only when drift confuses the source activity. |
| report-only | Connector stack, POS/phrase monotony, reader-burden detail. | Report as naturalness signals; avoid automatic rewrite unless a local broken sentence is clear. |
| forbidden | Technical-document rigidity, hard argument templates, one-sentence-one-line, padding thin sources to 1400 chars, invented emotions/results, generic reflection closers. | These collide with daily note/Hatena naturalness, source-grounding, and genre length boundary. |

### daily_activity collision check

| Check | Result |
|---|---|
| body floor | Potential conflict if a uniform large body floor forces padding from thin sources. This matrix does not loosen thresholds; it records that daily activity should remain source-near and may be naturally shorter under current genre policy. |
| source-grounding | Strong application is safe only when expansion stays close to source elements. Third-party emotions, outcomes, numbers, and strong causality are forbidden. |
| note/Hatena自然さ | This genre has the strongest naturalness protection. Technical-writing strictness must stay low. |
| prompt budget | No prompt change. Future handling should be a compact genre profile, not extra prompt prose. |

## Candidate-by-genre Matrix

| Candidate | market_explanation | company_service_intro | announcement | case_study | comparison_guide | daily_activity |
|---|---|---|---|---|---|---|
| `floor_safe_local_only` | strong | strong | moderate | strong | strong | moderate |
| `source_claims_only` | strong | strong | strong | strong | strong | strong |
| `genre_weighted` | strong | strong | strong | strong | strong | strong |
| `flagged_spans_only` | strong | strong | strong | strong | strong | strong |
| `paragraph_role_handoff` | moderate | report-only | report-only | moderate | moderate | report-only |
| `certainty_within_support` | strong | moderate | strong | strong | strong | moderate |
| `term_stability_local` | strong | weak | weak | moderate | strong | weak |
| `heading_support_fit` | moderate | moderate | moderate | moderate | moderate | weak |
| `reader_burden_detail_local` | report-only | weak | report-only | report-only | moderate | report-only |
| `sentence_fragment_or_broken_predicate` | moderate | moderate | strong | moderate | moderate | strong |
| `punctuation_spacing_or_symbol_mismatch` | moderate | moderate | strong | moderate | moderate | moderate |
| `generic_transition_stack` | report-only | report-only | weak | report-only | report-only | report-only |
| `decorative_summary_sentence_candidate` | report-only | report-only | report-only | report-only | report-only | report-only |
| `pos_phrase_pattern_monotony_candidate` | report-only | report-only | report-only | report-only | report-only | report-only |
| compression-first redundancy | forbidden | forbidden | forbidden | forbidden | forbidden | forbidden |
| broad LLM style review | forbidden | forbidden | forbidden | forbidden | forbidden | forbidden |
| hard banned-word deletion | forbidden | forbidden | forbidden | forbidden | forbidden | forbidden |
| one-sentence-one-line | forbidden | forbidden | forbidden | forbidden | forbidden | forbidden |
| external manual prompt paste | forbidden | forbidden | forbidden | forbidden | forbidden | forbidden |

## Body Floor Compatibility

| Genre | Compatibility decision |
|---|---|
| `market_explanation` | Compatible only if style checks preserve source-backed explanatory depth and final body-floor buffer. |
| `company_service_intro` | Compatible only if low-intent hook and service detail remain source-backed and are not compressed away. |
| `announcement` | Potential conflict with any generic blog-length expansion. Keep the conflict documented; do not lower thresholds here. |
| `case_study` | Compatible when added depth comes from source-near sequence, attribution, and supported outcome context. |
| `comparison_guide` | Compatible when added depth comes from supported comparison axes, not SEO-style generic advice. |
| `daily_activity` | Potential conflict with uniform large floor on thin sources. Keep source-near natural length boundary; do not pad. |

## Source-grounding Compatibility

| Genre | Compatibility decision |
|---|---|
| `market_explanation` | Strong checks are allowed because they restrict certainty and causality to confirmed claims. |
| `company_service_intro` | Strong checks are allowed for narrator, praise, and third-party leakage; extra culture/backstage claims remain forbidden. |
| `announcement` | Strong checks are allowed for dates, actors, targets, changes, and cautions. |
| `case_study` | Strong checks are allowed for attribution and outcome support. Customer feelings/results without source remain forbidden. |
| `comparison_guide` | Strong checks are allowed for supported criteria and superiority guard. Competitor facts without source remain forbidden. |
| `daily_activity` | Strong checks are allowed for source-near scene detail and no invented feelings/outcomes. |

## note/Hatena Naturalness Compatibility

| Genre | Compatibility decision |
|---|---|
| `market_explanation` | Preserve explanatory owned-media voice; do not become a neutral PDF summary. |
| `company_service_intro` | Preserve low-intent owned-media warmth; do not become a corporate technical profile. |
| `announcement` | Naturalness means concise formal clarity, not diary warmth. |
| `case_study` | Preserve readable story sequence, but keep attribution clear. |
| `comparison_guide` | Preserve reader-support tone, not ranking/SEO template tone. |
| `daily_activity` | Preserve soft blog rhythm most strongly; technical strictness stays minimal. |

## Prompt Budget Compatibility

| Genre | Compatibility decision |
|---|---|
| `market_explanation` | Compatible only as compact rule IDs; no market-writing manual in prompts. |
| `company_service_intro` | Compatible only as compact profile or issue IDs; no low-intent hook prompt expansion. |
| `announcement` | Compatible as compact actor/date/formatting IDs. |
| `case_study` | Compatible as compact attribution/support IDs. |
| `comparison_guide` | Compatible as compact fair-criteria/support IDs. |
| `daily_activity` | Compatible as compact naturalness/source-near IDs. |

## Open Conflicts

No blocking doc conflict was found for continuing to the next docs-only owner.

The matrix does identify two genre-sensitive collision risks that must remain guarded:

- `announcement`: do not use style-conflict work to force long blog expansion.
- `daily_activity`: do not use style-conflict work to pad thin sources to a large uniform floor.

These are not blockers for the next docs-only owner because the next owner is read-only prompt budget inspection, not implementation or threshold change.

## Recommended Next Owner

Recommended next owner inside this non-current proposal package:

```text
prompt_budget_collision_check
```

Reason: the genre matrix leaves no unresolved doc conflict that requires `blocked_by_doc_conflict`. The next safe step is read-only prompt budget inspection, with no prompt-template edits, no product-code edits, and no API validation.

Recommended current Route B / 0506 owner remains:

```text
draft_writer_depth_budget_contract_smoke_failure_diagnosis
```

## Validation Summary

- Status included: yes, proposal / non-current.
- Current owner preserved: yes, `draft_writer_depth_budget_contract_smoke_failure_diagnosis`.
- Owner executed included: yes, `genre_applicability_matrix`.
- Required genres separated: yes, `market_explanation`, `company_service_intro`, `announcement`, `case_study`, `comparison_guide`, `daily_activity`.
- Strong / moderate / weak / report-only / forbidden levels included: yes.
- Body floor collision check included: yes.
- Source-grounding collision check included: yes.
- note/Hatena naturalness collision check included: yes.
- Prompt budget collision check included: yes.
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
