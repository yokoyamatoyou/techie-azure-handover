# AI Coding Rules

## Source Basis

This document adapts current AI coding-agent documentation patterns for this project.

External references checked on 2026-05-08:

- AGENTS.md open format: https://github.com/agentsmd/agents.md
- Claude Code memory / CLAUDE.md guidance: https://code.claude.com/docs/en/memory

## Adopted Rules

### Keep Agent Instructions Short

`AGENTS.md` must stay concise and operational. Put detailed product specs in `docs/PIPELINE_SPEC.md`.

Reason: coding-agent instruction files are loaded into model context, so concise and concrete rules are followed more reliably than long mixed documents.

### Use One Entry Point

`AGENTS.md` is the shared entrypoint for Codex and Claude.

Tool-specific files must point back to it instead of duplicating rules:

- `CLAUDE.md`

Do not add `.github/copilot-instructions.md` unless GitHub Copilot becomes an active tool for this workspace. Extra instruction surfaces create avoidable drift.

### Use a Fixed Read Order

Agents must read project state before editing:

1. `AGENTS.md`
2. `README.md`
3. `docs/GOAL_PLAN.md`
4. `TASK.md`
5. `PROGRESS.md`
6. `ARCHITECTURE.md`
7. `docs/PIPELINE_SPEC.md`
8. `docs/TECH_STACK.md`
9. `docs/SOURCE_ACQUISITION_POLICY.md`
10. `docs/JAPANESE_STYLE_POLICY.md`
11. `docs/ARTICLE_GENRE_POLICY.md`
12. `docs/CONFIG_AND_PERSONA_POLICY.md`
13. `docs/JAPANESE_STYLOMETRY_POLICY.md`
14. `docs/AI_CODING_RULES.md`
15. `WORKLOG.md`

### Keep Work Narrow

Use this default execution shape:

```text
1 issue = 1 narrow hypothesis = 1 owner scope
```

Do not combine:

- implementation and broad refactoring
- schema design and UI implementation
- prompt writing and quality tuning
- source extraction and article generation
- validation and opportunistic cleanup

### Bounded Self-Repair

For `/goal` execution, every slice must end in a test or validation check.

If a slice fails:

- attempt focused repair inside the same owner,
- do not widen into adjacent owners,
- retry at most 3 times,
- after 3 failed attempts, stop and report the failure using `docs/GOAL_PLAN.md`.

### Prevent Bloat

Do not let one module or prompt absorb multiple owners.

Follow `docs/CONFIG_AND_PERSONA_POLICY.md` for:

- config/persona separation
- prompt rendering boundaries
- module size thresholds
- prompt size thresholds
- stop conditions before broad prompt patches

Stylometry and QA metrics should be deterministic where possible. Do not call the LLM to compute sentence length, ending repetition, connector repetition, first-person variants, or watchlist counts.

### Prefer Contracts Before Prompts

Build schemas and deterministic service boundaries before writing prompts.

Prompt-only solutions are not acceptable when the behavior belongs in:

- JSON schema
- typed models
- validators
- deterministic preprocessing
- quality checkers
- evals

### Plan Before Complex Coding

For complex features, refactors, or ambiguous requirements, produce a plan first and wait for approval if the user requested planning.

For already-scoped implementation slices, proceed with the narrow owner.

### Validate Every Slice

Each implementation window must report:

- changed files
- tests run
- validation result
- known blockers
- whether product behavior changed
- whether source-grounding or QA policy changed

### Do Not Weaken Safety Policies

Do not solve failures by:

- lowering quality thresholds
- allowing unsupported facts
- deleting final guards
- adding broad prompt patches
- making the article generator responsible for every downstream fix

Fix the owner responsible for the failure.

## Tool-Specific Notes

### Codex

Codex-compatible agents should read `AGENTS.md` first and follow the document map before coding.

Codex-specific runtime behavior should not be copied into product rules unless it affects the project itself.

### Claude Code

Claude Code reads `CLAUDE.md`. If a project uses `AGENTS.md`, use a small `CLAUDE.md` that imports `AGENTS.md`.

This workspace uses that approach.

Claude-specific tool behavior should stay in `CLAUDE.md` only when it cannot be expressed in `AGENTS.md`.
