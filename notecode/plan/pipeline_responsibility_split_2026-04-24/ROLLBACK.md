# pipeline_responsibility_split_2026-04-24 ROLLBACK

## Baseline

- Runtime mainline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Baseline check:
  - `254 passed` for `test_simple_note_pipeline.py` and `test_simple_note_quality_guard.py`.

## Rollback Boundary

- Phase rollback is file-level because no `.git` repository was found in `C:\tetie` or `C:\tetie\notecode`.
- Reverting a phase means removing that phase's new helper module and restoring the corresponding helper definitions in `pipeline.py`.
- Do not rollback current naturalness keep diffs solely because this split package exists.

## Phase 7 Rollback Note

- To rollback only the behavior fix, remove `alignment_acceptance_clear` / `company_intro_alignment_source_contract_clear` from `note\simple_note_pipeline\pipeline.py` and restore the acceptance condition to require `effective_alignment_preserved` directly.
- Also remove `test_company_intro_source_contract_clear_accepts_when_alignment_metric_drops` from `note\tests\test_simple_note_pipeline.py`.
- Extraction rollback remains separate from the Phase 7 behavior rollback.

## Do Not Retry

- Do not use this package to change thresholds, repair count, persona design, or prompt policy.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.
- Do not fix the final-validation connection before extraction passes owner-local and shared checks.
