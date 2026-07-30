# ARCHITECTURE.md

## Core Architecture

The system must use a staged pipeline instead of one-shot article generation.

```text
Source Upload
  -> Text Extraction / Noise Removal
  -> Source Card Extraction
  -> Knowledge Pack Integration
  -> Article Brief Generation
  -> Draft Writer
  -> Style Editor
  -> Structural Editor
  -> Japanese Quality Checker
  -> Targeted Rewriter
  -> Final Article
```

## Why This Shape

Directly passing long raw sources into one generation prompt creates predictable failures:

- duplicated meaning
- unstable first person
- repeated topics across headings
- unclear actors caused by Japanese subject omission
- zero-anaphora ambiguity
- unsupported facts
- generic AI-like summaries
- inconsistent tone across generated sections

The system therefore converts source material into structured generation contracts before writing article text.

## Responsibility Boundaries

### Config and Persona Loading

Load project settings, genre presets, persona profiles, viewpoint profiles, style profiles, and QA thresholds.

This layer does not generate article text and does not call the LLM.

Config and personas are data inputs to the article brief builder and prompt renderer.
Style profiles are also persona data inputs; they define paragraph rhythm, line-break policy, subject omission, and ending-bucket handling without adding prompt patches.

### Text Extraction

Extract text and source spans from URL, PDF, Word, and manual sources.

This layer does not decide article structure.

### Source Card Extraction

Extract source-grounded facts, phrases, and warnings from one source at a time.

This layer does not merge multiple sources.

### Knowledge Pack Integration

Merge source cards into confirmed claims, conflicts, deduped themes, and do-not-infer rules.

This layer does not write article prose.

### Article Brief Builder

Convert UI settings and knowledge pack into a section-by-section article plan.

This layer owns:

- article category
- target reader
- article goal
- first person
- tone
- section structure
- claim allocation
- discourse rules
- selected persona
- viewpoint mode
- selected style profile
- style edit policy
- QA policy references

### Draft Writer

Write only the initial article draft from the article brief and confirmed claims.

This layer prioritizes source accuracy and structure over polish.

### Style Editor

Improve Japanese readability without changing facts.

This layer owns:

- sentence length
- paragraph flow
- natural subject omission
- ending variation
- connector repetition
- AI-like phrasing

### Structural Editor

Apply a final editor pass focused on the late half of the article and whole-article consistency.

This layer owns:

- late-half paragraph splitting
- first-person consistency across the full article
- heading-to-body continuity checks
- CTA strength consistency checks
- editor-pass reporting

It must not add claims, change facts, weaken source grounding, or lower QA thresholds.

### Japanese Quality Checker

Return structured quality findings.

This layer owns detection, not rewriting.

It may use deterministic stylometry output for rhythm, ending, lexical, viewpoint, and formatting issue candidates.

### Targeted Rewriter

Fix only the issue spans identified by the quality checker.

This layer must not regenerate the whole article unless the QA result explicitly requires regeneration.

## Data Contracts

Primary contracts:

- `source_card`
- `article_knowledge_pack`
- `article_brief`
- `quality_check`
- `publish_readiness`

JSON schema should be the first implementation slice.

## Anti-Bloat Architecture

Do not let one module or one prompt become the project.

- Config values live under `app/config/`.
- Persona and writer-role data live under `app/personas/`.
- Prompt templates live under `app/prompts/`.
- Runtime assembly lives under `app/services/`.
- Stylometry metrics live under `app/services/stylometry.py` and should not call the LLM.
- Agents should perform one pipeline responsibility each.

If a module starts owning multiple stages, split it before adding behavior.

If a prompt starts containing genre tables, source policy, QA policy, and rewrite policy together, move the shared rules into config/persona data and render only the needed subset.

## Risk Policy

Auto-publish must be conservative.

Do not auto-publish:

- medical content
- legal or professional services content
- financial content
- hiring conditions
- price-sensitive content
- claims with high legal or compliance risk

Even when the score is high, these categories require human review.
