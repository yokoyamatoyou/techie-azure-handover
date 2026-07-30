# pipeline_source_contract_split_planning_2026-04-26 TASK

## Phase Map

| Phase | Status | Scope | Owner | Gate |
|---:|---|---|---|---|
| 00 | completed | docs-only source contract inventory and split decision | `plan\pipeline_source_contract_split_planning_2026-04-26\` | README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT created; WORKLOG updated |
| 01 | next | announcement behavior-preserving extraction | `note\simple_note_pipeline\pipeline.py` + new `announcement_source_contract.py` | focused announcement tests, owner tests, shared regression pass |
| 02 | follow-up | comparative_review behavior-preserving extraction | future package | only after Phase 01 green |
| 03 | parked reassessment | company_intro / branding / case_study / explanatory / common helper | future planning | only after two article-type extractions prove a safe pattern |

## Phase 00 Requirements

- Create package docs:
  - `README.md`
  - `TASK.md`
  - `PROGRESS.md`
  - `ROLLBACK.md`
  - `EXECUTION_PROMPT.md`
- Record source contract inventory table.
- Select exactly one first extraction target.
- Record do-first / do-next / park.
- Record rollback boundary.
- Record test matrix.
- Update `C:\tetie\WORKLOG.md`.

## Phase 01 Requirements

Future implementation window only:

- Extract only announcement source contract logic.
- Preserve behavior.
- Preserve private symbol compatibility through imports in `pipeline.py`.
- Do not change prompt / threshold / repair / output_guard / UI.
- Do not fix full-flow residual issues.
- Do not extract comparative / company_intro / branding / case_study / explanatory / shared common helpers.

## Required Checks For Phase 01

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "announcement"
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
```

## Retry Stop

- Phase 00 docs-only: no retry loop needed; product code untouched.
- Future implementation phases: maximum 3 correction attempts within one narrow phase.
- If Phase 01 tests fail after 3 correction attempts, stop and report with rollback instructions.

## Completion Criteria

- First extraction target is fixed as `announcement_source_contract.py`.
- Behavior-preserving extraction boundary is explicit.
- Product code remains unchanged in Phase 00.
- `WORKLOG.md` has this planning package entry.
- AGENTS remains unchanged unless routing changes.

