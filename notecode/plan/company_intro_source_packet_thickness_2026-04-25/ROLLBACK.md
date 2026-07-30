# company_intro_source_packet_thickness_2026-04-25 ROLLBACK

## Baseline

- Runtime mainline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current planning source of truth remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- This package is a narrow implementation package and does not replace the current naturalness source of truth.

## Rollback Boundary

- Phase 0-1 rollback is docs-only:
  - remove or supersede `C:\tetie\notecode\plan\company_intro_source_packet_thickness_2026-04-25\`
- Phase 2 rollback:
  - remove only the focused regression test added for this package.
- Phase 3+ rollback:
  - revert only the `company_introduction` source packet thickness diff in:
    - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
    - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- Runtime rollback must not touch:
  - pre-2026-04-02 archive
  - frozen architecture package
  - non-company-introduction source contracts
  - target length estimation
  - repair acceptance
  - quality guard thresholds

## Do Not Retry

- Do not retry by broadly increasing article length.
- Do not relax `quality_guard.py`.
- Do not increase repair count.
- Do not change `target_chars` / `length_mode`.
- Do not change repair acceptance.
- Do not add prompt blocks to hide thinness.
- Do not expose persona names, editor names, trial names, source contract wording, `source_limit`, `hidden`, `PATCH_SCOPE`, or validation terms in visible text.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.
- Do not undo `pipeline_responsibility_split_2026-04-24`.
- Do not add source-outside claims or generic padding.
- Do not change all article types' source compression.

## Stop Boundary

- Same phase has `3` repeated failures with the same error.
- Evidence requires multiple owner changes.
- Runtime fix would require source-outside claims or generic padding.
- Current success path regression appears.
- Required source material cannot be kept bounded without prompt accretion or broad source compression changes.

## Expected Failure Modes

- Slot material becomes longer but redundant.
- Source-backed boundaries blur into unsupported claims.
- `source_limit` or other internal terms leak into visible prompt/body.
- Non-company-introduction article types inherit company introduction source packet behavior.
- Additional material increases fail-closed rows by triggering stricter guard paths.

## Kept Diff

- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Test:
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- Behavior:
  - company-introduction-only required slot material now prefers bounded source-document explanation candidates when the slot was otherwise filled by a short grounding item
  - explicit source contracts remain unchanged
  - non-company-introduction source compression remains unchanged
- Keep evidence:
  - focused company intro source contract tests: `15 passed, 219 deselected`
  - owner-local: `256 passed`
  - shared: `343 passed`; `36 passed`; `6 passed`
  - live: `C:\tetie\notecode\logs\company_intro_source_packet_thickness_20260425-103407\classification.md`
    - packet chars `638 -> 1693`
    - body / target avg `0.6146 -> 0.6333`
    - required coverage `5/5`
    - internal leakage `0/10`
    - fail-closed not materially worse

## Residual

- This package does not fully solve body length / depth.
- Remaining issue is now `realization_shallow_suspected`:
  - the source packet has enough bounded material
  - single-pass sections still often compress the explanation to short sections
- Do not continue this package by adding more packet material unless a new packet regression appears.
