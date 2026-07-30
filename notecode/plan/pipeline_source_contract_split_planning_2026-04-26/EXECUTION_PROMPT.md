# pipeline_source_contract_split_planning_2026-04-26 EXECUTION_PROMPT

Phase 03 company_introduction extraction is completed. Use this prompt only if a separate implementation window needs to replay or inspect the completed Phase 03 boundary.

```text
C:\tetie\notecode の pipeline source contract split Phase 03 company_introduction boundary です。

現在日時: 2026-04-26 JST
作業場所: C:\tetie\notecode

Read first:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\pipeline_source_contract_split_planning_2026-04-26\README.md
- C:\tetie\notecode\plan\pipeline_source_contract_split_planning_2026-04-26\TASK.md
- C:\tetie\notecode\plan\pipeline_source_contract_split_planning_2026-04-26\PROGRESS.md
- C:\tetie\notecode\plan\pipeline_source_contract_split_planning_2026-04-26\ROLLBACK.md

Completed goal:
- Phase 03 extracted only company_introduction source contract logic from `note\simple_note_pipeline\pipeline.py` into `note\simple_note_pipeline\company_intro_source_contract.py`.

Hard constraints:
- No behavior change.
- No prompt change.
- No threshold change.
- No repair policy change.
- No output_guard change.
- No quality_guard change.
- No UI change.
- Do not fix full-flow residual issues.
- Do not extract branding, case_study, explanatory, or common helpers in this window.
- Do not create persona registry, central registry, or `source_contract_common.py`.
- Preserve private symbol compatibility through imports in `pipeline.py`.

Moved in Phase 03:
- company_intro source contract scope / sentence / slot / scoring helpers.
- company_intro quote-backed script packet helpers.
- company_intro runtime preparation / payload merge helpers.
- company_intro validation helpers.
- company_intro unsupported-claim / source-limit leakage / brochure-generic-profile drift predicates.

Kept in `pipeline.py`:
- `_prepare_runtime_source_contracts`
- `_refresh_diagnostics_state`
- `_run_optional_repair`
- `generate()` body_generation projection
- company_intro naturalness enrichment
- company_intro fingerprint / source-reflection repair activation
- failure payload / observability projection
- current success path connection

Completed checks:
- `C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile note\simple_note_pipeline\pipeline.py note\simple_note_pipeline\company_intro_source_contract.py`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "company_intro or company_introduction"`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`

Next action:
- Do not continue to another extraction automatically.
- Reassess remaining parked branding / case_study / explanatory / common-helper cleanup in a separate planning window before any further product code change.
```
