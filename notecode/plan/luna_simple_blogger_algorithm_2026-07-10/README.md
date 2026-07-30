# Luna Simple Blogger Algorithm 2026-07-10

This began as a separate no-API feasibility package for a simple GPT-5.6 Luna blog algorithm. It now also retains the one explicitly approved live A/B and the later no-API comparison with a past Route V article.

It does not replace or connect to Route V. It does not change Route V code, config, prompts, personas, defaults, accepted state, or current planning source of truth.

## Package map

- `past_evidence_audit.md`: required historical evidence and what it does or does not prove
- `SIMPLE_BLOGGER_ALGORITHM.md`: isolated one-pass baseline and same-blogger two-pass candidate
- `DECISIONS.md`: accepted, rejected, and deferred design decisions
- `EVAL_PLAN.md`: no-API and later live A/B gates
- `PROGRESS.md`: this package's single current/next owner
- `PAST_A_VS_CURRENT_B_EVALUATION.md`: saved 2026-06-24 Sanrei Route V A vs current Luna B
- `prototype/simple_blogger_no_api.py`: standard-library-only contract renderer and saved-artifact replay evaluator
- `prototype/fixtures/replay_manifest.json`: saved articles and source packets used for replay
- `prototype/tests/test_simple_blogger_no_api.py`: no-API contract and metric tests
- `artifacts/`: generated prompts, replay metrics, run summary, and human-review bundle

## Boundary

- initial no-API feasibility sends: `0`
- completed explicitly approved live A/B responses: `3`
- new sends for the past-A/current-B comparison: `0`
- source refetch: `false`
- generated article patching: `false`
- raw full source handoff: `false`
- Route V product code changed: `false`
- Route V UI connection: `false`
- Route A / writer-only / archived route revival: `false`

The historical editor-persona outputs are included only as negative/control evidence. They are not represented as outputs from the new same-blogger candidate.
