# External Japanese Style Reference Inventory

Status: proposal / non-current

Current owner preserved: `draft_writer_depth_budget_contract_smoke_failure_diagnosis`

Inventory owner: `external_japanese_style_reference_inventory`

Created: 2026-06-22 JST

Decision: inventory completed; no product-code, prompt-template, AGENTS, WORKLOG, or API-validation changes.

## External Reference Boundary

External reference checked:

```text
https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d
```

This external reference is treated only as a proposal seed for Japanese-writing conflict prevention.

It is not:

- the current notecode algorithm,
- a runtime prompt body,
- a prompt-template replacement,
- a config/persona replacement,
- a QA threshold policy,
- a permission to compress generated articles below `body_length_floor_chars`.

This inventory does not reproduce the full reference. It uses only summarized rule families: technical-document formatting, paragraph argument structure, logical strictness, reader-burden control, viewpoint/narration, restrained rhetoric, empty LLM-like phrasing, and redundancy reduction.

## Current Source-Of-Truth Boundary

The current source-of-truth remains:

- `notecode/AGENTS.md`
- `notecode/0506/AGENTS.md`
- `notecode/0506/docs/CURRENT_ALGORITHM.md`
- `notecode/0506/docs/PIPELINE_SPEC.md`
- `notecode/0506/docs/CONFIG_AND_PERSONA_POLICY.md`
- `notecode/0506/docs/JAPANESE_STYLE_POLICY.md`
- `notecode/0506/docs/JAPANESE_STYLOMETRY_POLICY.md`
- `notecode/0506/docs/AI_CODING_RULES.md`
- current owner artifacts named by the current docs

If this proposal conflicts with those files, current docs win. The current Route B / 0506 next owner remains `draft_writer_depth_budget_contract_smoke_failure_diagnosis`.

Non-owner boundaries for this inventory:

- Do not change product code.
- Do not change prompt templates.
- Do not change AGENTS or WORKLOG.
- Do not run API validation.
- Do not reopen Route A fallback, writer-only fallback, old repair loop, or raw full `source_documents` pass.
- Do not relax QA thresholds or repair acceptance.
- Do not propose broad prompt tuning.

## Overlap Table

| External rule family | Current overlap | Current home | Inventory decision |
|---|---|---|---|
| Empty LLM-like phrasing | Existing risky phrases, model-frequent words, generic encouragement checks | `JAPANESE_STYLE_POLICY.md`, `JAPANESE_STYLOMETRY_POLICY.md`, Japanese quality checker | Overlaps; do not create a second watchlist. Future additions must extend existing issue types narrowly. |
| Connector repetition and mechanical transitions | Connector metrics already track repeated connectors and paragraph-initial connector risk | Stylometry and Japanese quality checker | Overlaps; only candidate if framed as deterministic issue detection, not prose-wide connector bans. |
| Sentence/paragraph rhythm | Existing policy checks sentence length, paragraph rhythm, line-break monotony, ending buckets | Style editor, structural editor, stylometry | Overlaps; keep genre-sensitive, especially for note/Hatena rhythm. |
| Viewpoint and narrator control | Current docs enforce first-person consistency, self-viewpoint owner, narrator mismatch checks | Article brief, style editor, structural editor, QA | Overlaps; external viewpoint rules may inform issue wording only. |
| Avoid unsupported certainty | Current source-grounding forbids unsupported facts and risky unsupported strengths | Knowledge pack, draft writer, QA, targeted rewriter | Overlaps partly; a narrower certainty-without-support issue may be a gap candidate. |
| Redundancy reduction | Existing duplication, repeated claims, repeated abstract nouns, and motif reduction controls | Global consistency editor, style editor, QA | Overlaps; must not become compression-first editing while body floor is unresolved. |
| Reader burden control | Current source thickness, assigned claims, section purposes, and style policy already limit irrelevant detail | Article brief, style editor, structural editor | Partial overlap; candidate only as local relevance/over-detail issue, not deletion of source-required specifics. |
| Logical continuity across paragraphs | Structural editor already owns heading-to-body continuity and late-half structure | Structural editor, QA issue candidates | Partial overlap; paragraph role handoff is a candidate. |

## Gap Table

| Gap candidate | Why it may help | Safe adoption shape | Collision guard | Possible home |
|---|---|---|---|---|
| Paragraph role handoff | Current structural checks cover rhythm and continuity, but do not explicitly record what each paragraph receives, does, and passes onward. | Diagnose paragraph role drift as a structural-editor or QA issue candidate. | Do not force rigid paragraph templates or one-sentence-one-line style. | Structural editor / Japanese quality checker |
| Unsupported certainty | Current `unsupported_claim` catches facts, but certainty level can still exceed the support shape. | Add a candidate issue such as `certainty_without_support` only when a sentence asserts certainty not supported by confirmed claims. | Preserve source-grounding; do not invent uncertainty or remove supported claims. | Japanese quality checker / targeted rewriter |
| Oversimplified causality | Market explanations and comparison guides can over-compress multi-factor causes. | Add a candidate issue such as `oversimplified_causality` when one stated cause is not enough for the supported claim set. | Do not add new causes; only narrow or qualify claims using existing support. | Japanese quality checker / structural editor |
| Term drift / concept blur | Existing lexical diversity checks may not catch same-concept drift across sections. | Candidate issue for repeated key concepts whose labels change in a confusing way. | Do not ban natural paraphrase globally; preserve genre naturalness. | Japanese quality checker / structural editor |
| Heading specificity mismatch | Current heading-to-body continuity exists, but heading specificity vs source thickness can be sharper. | Flag headings that promise broader proof than assigned claims can support. | Do not increase H1/H2 prompt burden broadly; avoid prompt bloat. | Structural editor / Japanese quality checker |
| Unnecessary proper-name/detail burden | External reference highlights reader attention cost. | Flag decorative or non-reused details only if not source-required for responsibility, dates, prices, schedules, or identity. | Do not delete required details or source anchors. | Style editor / targeted rewriter |
| Rhetorical overstatement | Current model-frequent list catches some generic encouragement, but not all dramatic setup. | Treat as a low-priority style issue when unsupported drama appears in ordinary blog genres. | Do not flatten `daily_activity` warmth or case-study voice. | Style editor / Japanese quality checker |

## Non-Adopted Table

| External rule or tendency | Non-adoption reason | Boundary |
|---|---|---|
| Full external reference as prompt text | Violates prompt compactness and would create a competing style manual. | Do not paste into prompts, config, AGENTS, or product modules. |
| One sentence per line | Conflicts with note/Hatena blog naturalness and current paragraph-rhythm policy. | Not a general notecode rule. |
| Technical-book footnotes and column conventions | Product output is blog/article content, not technical-book manuscript formatting. | Not adopted for normal Route B articles. |
| Universal bolding of first definitions | Can produce unnatural blog formatting and distract from source-grounded article flow. | Not adopted globally. |
| Universal paragraph-initial connector requirement | Conflicts with current connector-repetition risk and natural blog rhythm. | Do not require connectors at every paragraph start. |
| Compression-first editing | Directly risks `body_length_floor_chars` and depth-budget contract compliance. | Rejected while body-floor owner is unresolved; later only local redundancy fixes. |
| Hard banned-word deletion | Current policy treats risky phrases as contextual risks, not absolute bans. | Do not create absolute global bans. |
| Strict technical-writing tone | Conflicts with `daily_activity`, `announcement`, and low-intent company/service introductions. | Genre applicability must be explicit before any adoption. |
| Broad prompt tuning for style | Violates current owner discipline and prompt patch rule. | Future prompt changes require a narrow proven owner. |
| Rewriting whole articles for style | Violates targeted rewriter contract. | Rewrite only flagged spans and preserve facts, claim IDs, section purpose, speaker, and non-target paragraphs. |

## Collision-Risk Table

| Collision area | Risk from external reference | Current protected contract | Inventory decision |
|---|---|---|---|
| `body_length_floor_chars` | Redundancy removal and compression can reduce body length below floor. | Depth-budget contract and final body-floor compliance. | Keep compression rules out of DraftWriter now; use only local duplication flags later. |
| Depth-budget contract | Style strictness may compete with source-backed paragraph depth. | DraftWriter depth budget from floor/target chars, sections, assigned claims, and selected excerpts. | No DraftWriter adoption during current smoke-failure diagnosis. |
| Source-grounding | Logical-connection rules may tempt unsupported causal bridges. | Use only confirmed claims, assigned claim anchors, selected excerpts, and do-not-infer rules. | Any causality fix must narrow or qualify claims, not invent support. |
| Genre naturalness | Technical-writing rigidity can harden soft blog genres into essays. | note/Hatena owned-media style, low-intent hooks, genre-specific personas. | Require genre applicability matrix before implementation. |
| Prompt compactness | Full style manual creates prompt bloat and competing instructions. | Prompt templates under compact budget; config/persona separation. | No broad prompt tuning; render only short proven rules later. |
| QA threshold integrity | New style issues could be used to lower pass criteria or accept weaker repairs. | QA thresholds and repair acceptance are not to be relaxed. | Candidate issue types must be additive signals, not threshold weakening. |
| Watchlist duplication | External empty-phrase list could duplicate current risky phrase/model-frequent policy. | Existing style and stylometry watchlists. | Extend existing lists only after deterministic audit proves a gap. |
| Targeted rewrite scope | Logic/style cleanup can become full rewrite. | Targeted rewriter fixes only flagged spans and preserves non-target paragraphs. | Keep fixes span-limited and fact-preserving. |

## Candidate Home Table

| Home | Candidate status | Allowed candidate | Not allowed in this home | Validation needed before implementation |
|---|---|---|---|---|
| Draft writer | Mostly blocked for now | None during `draft_writer_depth_budget_contract_smoke_failure_diagnosis`; possible future compact depth-neutral guard only if diagnosis selects it. | Compression-first rules, broad style manual, one-sentence-one-line, extra claim enumeration, unsupported logic bridges. | Current owner diagnosis must finish first; no-API tests before any API run. |
| Style editor | Limited candidate | Local removal of empty filler, rhetorical overstatement softening, unnecessary decorative detail reduction. | Adding facts, changing numbers/dates/names, deleting source-required details, shrinking below floor. | Rendered prompt-size check if prompts change; stylometry/fixture test for unchanged facts. |
| Structural editor | Strongest future candidate | Paragraph role handoff, heading specificity, local logical continuity, late-half paragraph split decisions. | Whole-article rewrite, new claims, rigid paragraph templates, universal connector starts. | Structural report fixture plus source-claim preservation check. |
| Japanese quality checker | Strong candidate | Deterministic or near-deterministic issue candidates: `certainty_without_support`, `oversimplified_causality`, `term_drift`, `heading_specificity_mismatch`, `reader_burden_detail`. | Broad LLM review loop, threshold relaxation, duplicate watchlists. | Deterministic QA candidate audit; issue severity and rewrite trigger policy reviewed without loosening thresholds. |
| Targeted rewriter | Conditional candidate | Span-limited fixes for QA-flagged certainty, causality narrowing, term drift, or decorative detail. | Rewriting unflagged sections, changing facts, adding support, changing speaker or claim IDs. | Fixture proving facts, claim IDs, section purpose, speaker, and non-target paragraphs are preserved. |

## Candidate Classification Summary

| Classification | Items |
|---|---|
| Adopt candidate | Paragraph role handoff; unsupported certainty; oversimplified causality; term drift / concept blur; heading specificity mismatch; unnecessary detail burden; restrained unsupported rhetoric. |
| Current overlap | Empty LLM-like phrasing; connector repetition; sentence/paragraph rhythm; viewpoint/narrator consistency; duplication; generic encouragement. |
| Non-adopted | Full reference as prompt; one sentence per line; footnotes/technical-book conventions; universal bold definitions; universal paragraph-initial connectors; compression-first editing; hard banned-word deletion; strict technical tone across genres. |
| Collision risk | Body floor compression; source-grounding drift; soft-genre hardening; prompt bloat; QA/repair weakening; watchlist duplication; whole-article rewrite. |

## Recommended Next Owner

Recommended next owner inside this non-current proposal package:

```text
style_conflict_contract_design
```

Reason: the inventory leaves several candidates, but none should be implemented before a contract-design slice decides which remain docs-only, which become article-brief/profile/QA issue candidates, and which stay rejected.

Current Route B / 0506 owner remains preserved:

```text
draft_writer_depth_budget_contract_smoke_failure_diagnosis
```

## Inventory Validation

- Required proposal status included: yes.
- Current owner preserved: yes.
- External reference boundary included: yes.
- Current source-of-truth boundary included: yes.
- Overlap table included: yes.
- Gap table included: yes.
- Non-adopted table included: yes.
- Collision-risk table included: yes.
- Candidate home table included: yes.
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
