# Thin Genre Profile Specification

## Fixed B core

All types use `company_side_blogger_v1`, one Stage 1 draft, and one Stage 2
same-blogger reread. The fixed instructions measure 402 characters for Stage 1
and 404 for Stage 2. Stage 2 checks only low-interest continuation, company-side
voice, uniquely recoverable omitted subjects, and retention of source-specific
scenes/nouns/actions. It may revise a failing paragraph plus one adjacent
sentence; it returns the full article.

## Schema: the only permitted type variance

1. `intro_source_priority` — one to three source-material kinds to prefer at the opening.
2. `reader_arrival_goal` — what a low-interest visitor should be able to grasp.
3. `paragraph_flow` — three or four broad moves, never a generated outline.
4. `subject_omission_handling` — where a responsible speaker must be explicit.
5. `major_risk` — one type-specific human-review focus.
6. `body_floor` / `cta_mode` — numeric floor and either `none` or `source_optional`.

The JSON validator rejects any extra key. In particular it rejects persona,
identity, editor, critic, explainer, Stage 2, repair-loop, and fallback keys.

## Six initial profiles

| type | introduction priority | major risk |
|---|---|---|
| company_service_intro | work, product, scene | outside introduction / mission-only summary |
| announcement | date, audience, change | long blog prose before essential information |
| case_study | problem, response, source-present change | invented result or customer feeling |
| comparison_guide | source-specific difference | ranking, recommendation, generic criteria |
| market_explanation | source-present change or issue | third-party document-summary voice |
| daily_activity | place, tool, action | invented emotion or sense of achievement |

## Hard boundaries

Profiles do not select a new source, add an inference, relax a gate, rewrite a
saved article, or create a type-specific postprocessor. Unsupported claims remain
a hard gate; static replay may only label them `not proven statically`.
