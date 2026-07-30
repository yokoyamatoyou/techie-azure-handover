# TASK

## Phase Map

| Phase | Gate |
|---|---|
| 0 artifact review | Required planning docs and existing validation artifacts inspected |
| 1 classification | Article types assigned to `ready`, `ready_with_review_warning`, `source_needed`, or `hold` |
| 2 first-trial selection | Maximum three initial user-trial article types fixed |
| 3 source / warning boundary | Recommended source conditions and stop/report errors documented |
| 4 closeout | Product code unchanged, `18080` listener absent, WORKLOG updated |

## Owner Scope

- Owner: docs package only.
- Runtime owner: none.
- Product code owner: none.

## Required Decisions

- First trial targets:
  - `announcement`
  - `comparative_review`
  - `company_introduction`
- Image trial targets:
  - primary: `announcement`
  - secondary: `comparative_review`
  - optional third: `company_introduction`
- Next action:
  - `A: ユーザー試行へ進む`

## Non-Goals

- Product code changes.
- UI wording changes.
- Prompt changes.
- Threshold changes.
- Repair count changes.
- Pipeline / note writer app / output guard / quality guard / blog image auto implementation changes.
- Additional responsibility split implementation.
- Full-flow rerun.
- Reopening pre-2026-04-02 archive or frozen architecture package.

## Required Checks

No pytest is required for this docs-only package.

Final verification:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath C:\tetie\notecode\note\current_mainline_runner.py,C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py,C:\tetie\notecode\note\simple_note_pipeline\pipeline.py,C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py,C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py,C:\tetie\notecode\note\note_writer_app.py,C:\tetie\notecode\note\blog_image_auto.py
netstat -ano | Select-String 'LISTENING' | Select-String ':18080'
```

## Acceptance Criteria

- User-trial readiness summary exists.
- All listed article types are classified.
- First user-trial target list is limited to at most three article types.
- Recommended source conditions are documented.
- Warning / stop boundaries are documented.
- Image generation trial target is documented.
- AGENTS update need is explicitly recorded.
- WORKLOG update is completed.
