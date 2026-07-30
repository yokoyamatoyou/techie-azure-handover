# Goal Plan

## Purpose

This is the execution plan for Codex CLI `/goal`.

Product goal: build a Windows-first Python 3.11 / NiceGUI application for note/Hatena-style owned-media blog generation. The system must generate source-grounded Japanese blog articles, detect AI-like writing, and reduce AI-like phrasing through bounded quality checks and targeted rewrites.

## Operating Mode

- Mode: Default / execution-first.
- Start from the first executable slice.
- Work phase by phase and slice by slice.
- Run tests at the end of every slice.
- If a test or implementation error occurs, attempt focused self-repair up to 3 times.
- If the same slice still fails after 3 repair attempts, stop and report to the user.
- Do not widen scope to adjacent owners while repairing.

## Ready-to-Paste `/goal`

```text
/goal このワークスペースで、note/はてなブログ向けオウンドメディア用の日本語ブログ生成ソフトを実装する。AGENTS.mdの読書順とdocs/GOAL_PLAN.mdに従い、Phase/Slice単位で自律実行する。各Sliceごとにテストし、失敗時は同一Slice内で最大3回まで自己修正する。3回失敗したら停止して、失敗Slice、実行コマンド、エラー要約、試した修正、次の候補ownerを報告する。今回の実行範囲はPhase 1 Contracts、Phase 2 Deterministic Foundation、Phase 3 Source Acquisitionまで。Phase 4 LLM Pipeline、NiceGUI MVP、生成品質チューニングには進まず、Phase 3完了時点で停止して報告する。
```

## Execution Boundary

This `/goal` run may complete:

- Phase 1: Contracts
- Phase 2: Deterministic Foundation
- Phase 3: Source Acquisition

This `/goal` run must not start:

- Phase 4: LLM Pipeline
- Phase 5: NiceGUI MVP
- Phase 6: Quality Evaluation
- Phase 7: Tuning and Hardening

After Phase 3 validation passes, stop and report before any LLM, UI, or generation-quality work.

## Global Stop Rules

Stop and report before continuing if:

- the same slice fails after 3 focused repair attempts,
- a fix would require weakening source-grounding,
- a fix would lower QA thresholds to pass tests,
- a fix would add broad prompt text before owner diagnosis,
- a slice starts touching multiple pipeline owners,
- a module or prompt crosses the anti-bloat thresholds in `docs/CONFIG_AND_PERSONA_POLICY.md`,
- URL acquisition would require bypassing robots.txt, login, paywall, or internal APIs,
- external API calls are needed but the phase did not explicitly allow them.

## Completion Report Format

Each slice should close with:

```text
Phase/Slice:
Changed files:
Tests run:
Result:
Next slice:
```

If stopped after failures, report:

```text
Stopped slice:
Failure command:
Error summary:
Repair attempts 1-3:
Files touched:
Likely next owner:
User decision needed:
```

## Phase 1: Contracts

Goal: define data contracts before implementation behavior.

Allowed:

- JSON Schema files
- Pydantic models if useful
- schema fixtures
- schema validation tests
- config/persona/stylometry reference fields

Forbidden:

- UI
- URL fetching
- PDF/Word real extraction
- LLM calls
- prompt implementation
- quality tuning

Slices:

1. `P1-S1 Source Card Schema`
   - Files: `app/schemas/source_card.schema.json`, tests/fixtures if needed.
   - DoD: source facts, spans, warnings, metadata, reliability, and source type validate.
   - Test: schema validation on valid and invalid examples.

2. `P1-S2 Knowledge Pack Schema`
   - Files: `app/schemas/knowledge_pack.schema.json`.
   - DoD: confirmed claims, supporting fact IDs, conflicts, do-not-infer rules, confidence validate.
   - Test: schema validation on merge/conflict examples.

3. `P1-S3 Article Brief Schema`
   - Files: `app/schemas/article_brief.schema.json`.
   - DoD: `genre_id`, `persona_id`, `writer_role`, `viewpoint_mode`, `narrator`, `qa_policy_id`, claim allocation, discourse rules validate.
   - Test: self-perspective company/service example and formal notice example.

4. `P1-S4 Quality and Stylometry Schemas`
   - Files: `app/schemas/quality_check.schema.json`, stylometry schema if separate.
   - DoD: QA issues include source, style, viewpoint, rhythm, frequent-word, and stylometry issue candidates.
   - Test: issue-type validation.

5. `P1-S5 Publish Readiness Schema`
   - Files: `app/schemas/publish_readiness.schema.json`.
   - DoD: score, auto-publish flag, high-risk category lockout, reasons validate.
   - Test: auto-publish false for high-risk content.

Phase validation:

- Run all schema tests.
- Confirm no UI, URL fetching, LLM prompt, or article generation code was added.
- Update `PROGRESS.md` and `WORKLOG.md`.

## Phase 2: Deterministic Foundation

Goal: implement local deterministic services without LLM calls.

Allowed:

- config loader
- persona loader
- prompt renderer without real LLM calls
- stylometry service
- static fixtures
- pytest

Slices:

1. `P2-S1 Project Scaffold and Dependencies`
   - Create Python package structure, `.venv` instructions, requirements files, and test setup.
   - Test: import smoke and pytest discovery.

2. `P2-S2 Config and Persona Loaders`
   - Load genre config, persona profiles, viewpoint profiles, QA thresholds.
   - Test: valid config loads, invalid config fails clearly.

3. `P2-S3 Prompt Renderer`
   - Render templates from article brief + config + persona data.
   - Test: no duplicated long policy lists; rendered prompt contains selected persona and viewpoint constraints.

4. `P2-S4 Stylometry`
   - Deterministic sentence, paragraph, ending, connector, watchlist, and viewpoint metrics.
   - Test: fixtures for `効く`, `第一歩`, repeated endings, and narrator mixing.

Phase validation:

- Run deterministic tests.
- Confirm no LLM calls.
- Confirm module and prompt size thresholds are respected.

## Phase 3: Source Acquisition

Goal: create source inputs that are traceable and safe.

Allowed:

- manual text ingestion
- URL public HTML fetch
- Beautiful Soup extraction
- PDF/Word minimal extraction or placeholders
- source acquisition warnings

Forbidden:

- login scraping
- paywall bypass
- internal APIs
- browser automation scraping
- broad crawling

Slices:

1. `P3-S1 Manual Source Intake`
2. `P3-S2 URL Public HTML Extraction`
3. `P3-S3 PDF/Word Minimal Extraction`
4. `P3-S4 Source Confidence and Warnings`

Phase validation:

- Fixture-based extraction tests.
- Low-confidence URL extraction blocks or warns.
- note/Hatena restrictions remain encoded as policy, not bypass logic.

## Phase 4: LLM Pipeline

Goal: implement the staged blog generation pipeline.

Allowed:

- LLM client boundary
- structured outputs
- source card extractor
- knowledge pack integrator
- article brief builder
- draft writer
- style editor
- quality checker
- targeted rewriter

Rules:

- No agent may own multiple pipeline stages.
- LLM calls go through the client boundary.
- Each stage logs input/output.
- GPT/web search remains fallback only.

Slices:

1. `P4-S1 LLM Client Boundary`
2. `P4-S2 Source Card Extractor`
3. `P4-S3 Knowledge Pack Integrator`
4. `P4-S4 Article Brief Builder`
5. `P4-S5 Draft Writer`
6. `P4-S6 Style Editor`
7. `P4-S7 Japanese Quality Checker`
8. `P4-S8 Targeted Rewriter`
9. `P4-S9 End-to-End CLI Smoke`

Phase validation:

- Run one fixture-only generation path.
- Verify source claim traceability.
- Verify self-perspective does not leak into third-party narrator terms.
- Verify quality checker flags known AI-like samples.

## Phase 5: NiceGUI MVP

Goal: provide a local UI for owned-media blog generation.

Allowed:

- NiceGUI local app
- source input UI
- genre selector
- viewpoint/narrator confirmation
- QA issue display
- final article preview
- artifact links

Slices:

1. `P5-S1 NiceGUI Shell`
2. `P5-S2 Source Input UI`
3. `P5-S3 Genre and Persona UI`
4. `P5-S4 Generation Run UI`
5. `P5-S5 QA and Article Preview UI`

Phase validation:

- Run NiceGUI locally.
- Confirm no text overflow or incoherent UI overlap.
- Confirm explicit generation button is required.
- Confirm QA issues and final article are visible.

## Phase 6: Quality Evaluation

Goal: test generation quality for note/Hatena-style owned-media use.

Allowed:

- eval fixtures
- generated before/after artifacts
- manual review sheets
- AI-like writing rubric
- style and source-grounding reports

Slices:

1. `P6-S1 Eval Corpus Design`
2. `P6-S2 AI-like Writing Rubric`
3. `P6-S3 Generation Quality Test`
4. `P6-S4 Targeted Rewrite Effect Test`
5. `P6-S5 note/Hatena Owned-Media Review`

Evaluation axes:

- source-grounding
- self-perspective consistency
- first-person consistency
- third-party viewpoint leakage
- paragraph rhythm
- line-break naturalness
- ending bucket monotony
- model-frequent words
- generic encouragement
- note/Hatena readability
- CTA naturalness

Phase validation:

- Save artifacts under `artifacts/runs/<run_id>/`.
- Report pass/fail and unresolved issues.
- Do not tune prompts broadly from one failure.

## Phase 7: Tuning and Hardening

Goal: improve quality without prompt or module bloat.

Rules:

- One issue = one narrow hypothesis = one owner scope.
- Diagnose owner before editing.
- Do not lower thresholds.
- Do not add broad prompt patches.
- Preserve no-code-change proof where relevant.

Potential owners:

- source extraction
- source card extraction
- knowledge pack integration
- article brief builder
- persona selection
- draft prompt
- style editor
- quality checker
- targeted rewriter
- UI state

Phase validation:

- Before/after artifacts.
- Focused tests.
- Worklog and progress sync.
