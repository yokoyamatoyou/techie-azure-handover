# Japanese Blog Generation Pipeline

## Overview

This workspace defines a Japanese blog generation application.

The application will accept multiple sources such as URLs, PDFs, Word files, and manual text. Users select an article category and UI settings, and the system generates a natural Japanese blog article grounded in the uploaded sources.

The main quality target is not just fluent Japanese. The system must also control:

- source-grounding
- duplicated or conflicting source information
- first-person consistency
- Japanese subject omission
- zero-anaphora risk
- category-specific tone, structure, and CTA
- AI-like generic phrasing

## Operating Principle

Do not use this shape:

```text
Long sources + huge prompt -> final blog
```

Use this shape:

```text
Sources
  -> structured facts
  -> knowledge pack
  -> article brief
  -> draft
  -> style edit
  -> quality check
  -> targeted rewrite
  -> final article
```

## Document Map

- `AGENTS.md`: AI coding agent entrypoint and project rules.
- `docs/GOAL_PLAN.md`: Codex CLI `/goal` execution plan with phases, slices, tests, and stop rules.
- `TASK.md`: current task plan and acceptance criteria.
- `PROGRESS.md`: current status and next owner.
- `ARCHITECTURE.md`: system architecture and responsibility boundaries.
- `docs/PIPELINE_SPEC.md`: detailed pipeline contracts and agent outputs.
- `docs/CURRENT_ALGORITHM.md`: current implemented algorithm, runtime modes, genre/persona rules, and editor timing.
- `docs/TECH_STACK.md`: Python, Windows, NiceGUI, Sudachi, and dependency decisions.
- `docs/SOURCE_ACQUISITION_POLICY.md`: URL acquisition, robots/terms, and GPT/web-search fallback policy.
- `docs/JAPANESE_STYLE_POLICY.md`: note/Hatena-style rhythm, line breaks, and GPT-like frequent word policy.
- `docs/ARTICLE_GENRE_POLICY.md`: article genres, prompt personas, viewpoint, and first-person defaults.
- `docs/CONFIG_AND_PERSONA_POLICY.md`: config/persona separation and module/prompt anti-bloat rules.
- `docs/JAPANESE_STYLOMETRY_POLICY.md`: deterministic Japanese stylometry metrics for QA signals.
- `docs/AI_CODING_RULES.md`: AI coding workflow rules and external references.
- `WORKLOG.md`: chronological work record.
- `blog_generation_agents_and_task.md`: original combined seed document.

## Current Status

Current Route V note (2026-06-28):

- Latest validation artifact: `notecode/logs/0628/route_v_market_explanation_draft_writer_sanitized_context_residual_floor_buffer_one_article_api_validation_after_approval_20260628_005719/api_validation_summary.md`.
- Decision: `reject_or_inconclusive`.
- API send count `1`; product code changed false; accepted status changed false; source refetch false; generated article patch false.
- Raw full source handoff false; Route A / writer-only fallback false.
- Final body floor reached `1397/1200`; structural API raw compressed to `1132/1200`, and the floor-loss guard restored the floor-reaching input.
- Human-visible surface gate passed with finding codes `[]`; source boundary passed with assigned claim coverage `8/8`; selected excerpt usage passed (`2/2`).
- Quality failed only on `sentence_too_long`, with one over-limit sentence (`max=137`, limit `90`).
- All six accepted Route V genres remain accepted, and remaining unaccepted genres remain `[]`.
- Current next owner: `route_v_market_explanation_quality_pass_failure_diagnosis_no_api`.
- Read `PROGRESS.md`, `TASK.md`, `docs/CURRENT_ALGORITHM.md`, and the validation artifact before changing owner state.

## Historical Status

Current Route V note (2026-06-22):

- Route V/0506 is active for the current floor-depth work. Route B is retired naming; legacy `route_b_*` artifact paths are historical evidence only.
- The paragraph-depth floor fix was implemented and API-rechecked, but did not improve body floor.
- Latest post-fix H1 validation passed in all 4 completed article types; 2 article types stopped before DraftWriter on API infra errors.
- Body floor reached final floor in 0/4 completed post-fix article types.
- `draft_writer_floor_actuation_count_based_depth_redesign` is implemented and passed the no-API gate.
- Count-based API isolation recheck is partial positive but incomplete: completed 2/6 article types; floor reached 2/2 completed; H1 reached 2/2 completed; quality pass 1/2 completed.
- Short-path validation packaging recheck is complete in `notecode/logs/0622/cbsp_1429/`: the packaging gap is fixed, but body floor is still not user-test ready (`1/5` completed types reached final floor; `5/5` reached H1; `0/5` quality passed).
- Floor-gap diagnosis is complete in `notecode/logs/0622/cbsp_1429/floor_gap_diagnosis.md`: the current paragraph target was met in all completed article types, but draft/final floor only reached `1/5`.
- `draft_writer_floor_actuation_depth_budget_contract_impl` is implemented and passed the no-API gate (`39 passed`, `py_compile` pass, `inspect_bloat` pass / `failures=[]`).
- Depth-budget one-article API smoke is complete in `notecode/logs/0622/dbsm_1550/`: `market_explanation` reached final floor/H1/quality pass, but unassigned-claim enumeration and sentence-fragment issues require `draft_writer_depth_budget_contract_smoke_failure_diagnosis` before full API isolation recheck.
- Source-shape, claim allocation, QA thresholds, repair acceptance, Route A/writer-only fallback, raw source handoff, and H1 changes are outside the current owner.
- Read `PROGRESS.md`, `docs/CURRENT_ALGORITHM.md`, and `docs/ARTICLE_BRIEF_V2_SOURCE_SHAPE_ALGORITHM.md` before touching DraftWriter, source-shape, or floor behavior.

Phase 1 to Phase 5 implementation is complete for the current execution boundary.

Implemented:

- Phase 1 Contracts: JSON Schema contracts and schema validation tests.
- Phase 2 Deterministic Foundation: project scaffold, config/persona loaders, prompt renderer, and stylometry service.
- Phase 3 Source Acquisition: manual text intake, public HTML URL extraction, minimal PDF/Word extraction, and confidence/policy warnings.
- Phase 3.5 / Phase 4 preprocessing: one-source 12000-character cap, chunking, source-span traceability, and note/Hatena style target metadata.
- Phase 4 LLM Pipeline: client boundary, stage owners, source card extraction, knowledge pack integration, article brief building, draft writing, style editing, quality checking, targeted rewriting, CLI smoke path, and artifacts.
- Phase 5 NiceGUI MVP: local UI with source input, genre/persona controls, explicit generation button, QA issue display, final article preview, and artifact path display.
- Phase 6 Quality Evaluation: eval corpus, AI-like writing rubric, generated artifacts, targeted rewrite effect test, and note/Hatena review report.
- Phase 7 Tuning and Hardening: owner diagnosis, claim traceability verifier, module/prompt bloat inspection, and readiness gate for later quality tuning.
- Focused persona/style-profile adjustment: style profiles now carry paragraph rhythm, line-break, subject-omission, and ending-bucket policy into `article_brief`.
- Structural editor pass: a final editor profile now checks late-half structure and whole-article consistency before quality checking.

Current quality status:

- The pipeline works end to end.
- Quality evaluation is intentionally strict.
- Current Phase 6 fixture evaluation passes after persona/style-profile based style editing.
- Broader naturalness tuning should still proceed one owner at a time; do not add phrase-specific patches.

Length planning:

- Article briefs now include `target_length_chars`, `section_count`, and `source_thickness`.
- The local deterministic baseline varies target length by source thickness and genre.
- Source length still remains capped at `12000` extracted characters per source before generation preprocessing.

Style profile visibility:

- `app/personas/style_profiles.yaml` owns compact style policy data.
- `article_brief` includes `style_profile_id` and `style_edit_policy`.
- Current local style editing uses those fields for paragraph grouping, safe first-person subject omission, and ending-bucket variation.
- `article_brief` also includes `editor_profile_id` and `editor_pass_policy`.
- `structural_edited_draft.md` and `editor_pass_report.json` are written as artifacts for Codex-visible review.

Current implementation assumptions:

- Python 3.11
- Windows first
- repo-local `.venv`
- NiceGUI
- SudachiPy with `sudachidict_core`
- deterministic URL extraction first, GPT/web search as fallback

Default execution uses a deterministic local client for tests and no-key MVP runs. Set `BLOGGEN_LLM_MODE=openai` with `OPENAI_API_KEY` to use the OpenAI Responses API boundary.

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run evaluation suite:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; from app.evals.evaluator import run_eval_suite; print(run_eval_suite(Path('artifacts/runs/phase6_after_persona_style_profile_v4')))"
```

Run CLI smoke:

```powershell
.\.venv\Scripts\python.exe -m app.cli
```

Run local UI:

```powershell
.\.venv\Scripts\python.exe -m app.ui.main
```

Open:

```text
http://127.0.0.1:18080
```

## First Implementation Rule

Start with data contracts. Do not start by building a UI or a giant generation prompt.
