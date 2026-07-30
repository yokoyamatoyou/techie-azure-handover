# company_intro_length_source_diagnosis_2026-04-25 ROLLBACK

## Baseline

- Runtime mainline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current planning source of truth remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- This package is a diagnosis package and does not replace the current source of truth.

## Rollback Boundary

- Phase 0-4 rollback is docs/logs only:
  - remove or supersede `C:\tetie\notecode\plan\company_intro_length_source_diagnosis_2026-04-25\`
  - remove or supersede timestamped logs under `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_*`
- Diagnosis runner files under this package are not runtime code.
- If Phase 5 creates a code fix, rollback is limited to that one owner scope and its focused tests.
- Until Phase 5, current rollback is docs/logs only.

## Diagnosis Artifacts

- Main Kyoto Kogyo diagnosis:
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-095537\metrics.json`
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-095537\metrics.md`
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-095537\classification.json`
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-095537\classification.md`
- Optional Yoshinomore fail-closed supplement:
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-100613\metrics.json`
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-100613\metrics.md`
- Runtime code changes:
  - none

## Do Not Retry

- Do not retry by broadly increasing article length.
- Do not relax `quality_guard.py`.
- Do not increase repair count.
- Do not add prompt blocks to hide thinness.
- Do not move persona names, editor names, trial names, or internal source contract terms into visible text.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.
- Do not use this package to undo `pipeline_responsibility_split_2026-04-24`.
- Do not add source-outside claims or generic padding.

## Stop Boundary

- Same phase has 3 repeated failures with the same error.
- Evidence requires multiple owner changes.
- Runtime fix would require source-outside claims or generic padding.
- Current success path regression appears.
- Required metrics cannot be captured or estimated without changing runtime behavior, and the user has not approved a runtime instrumentation change.

## Future Fix Rollback Candidates

- Source packet material fix:
  - rollback only the company_introduction source packet owner diff and focused tests.
- Target / length-mode fix:
  - rollback only the company_introduction target estimation owner diff and focused tests.
- Section realization fix:
  - rollback only the source-backed realization owner diff and focused tests.
- Repair acceptance fix:
  - rollback only the acceptance connection diff and focused tests.
