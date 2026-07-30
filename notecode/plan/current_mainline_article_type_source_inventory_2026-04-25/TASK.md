# current_mainline_article_type_source_inventory_2026-04-25 TASK

## Global Rules

- Inventory first; no generation.
- Product code / prompt / threshold / repair / UI / fixture edits are forbidden.
- Source adequacy must be judged before UI quality validation.
- Thin source may be used only for smoke or boundary checks, not for full quality conclusions.
- Same phase stops after 3 repeated same-error attempts if future automation is added.

## Phase Map

| Phase | Scope | Owner files | Behavior change | Exit |
|---|---|---|---|---|
| 0 | package creation | this plan package only | no | README/TASK/PROGRESS/ROLLBACK/EXECUTION_PROMPT exist |
| 1 | source inventory | docs only | no | article-type inventory table recorded |
| 2 | use/replace decision | docs only | no | use OK / replace / user-needed source lists recorded |
| 3 | next UI prompt | docs only | no | normal-mode UI validation prompt recorded |
| 4 | closeout | docs + WORKLOG | no | package status recorded |

## Phase 1 Inventory Inputs

- `C:\tetie\notecode\logs\multi_type_current_mainline_validation_20260425-013935\`
- `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\`
- `C:\tetie\notecode\logs\current_mainline_source_grounding_metric_correction_ui_validation_20260425-214032\`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\note\tests\fixtures\current_mainline_genre_sweep_casebook_2026-03-30.json`
- `C:\tetie\WORKLOG.md`

## Phase 2 Decisions Required

- For each target article type, record:
  - source exists / missing
  - source fits article type / mismatched
  - `thin` / `sufficient` / `rich`
  - previous input-boundary failure or fail-closed history
  - UI quality validation use decision
- Do not infer runtime defects from source-thin outputs.

## Phase 3 Next UI Validation Prompt Requirements

- Must explicitly forbid product changes.
- Must require use of `Use OK` source only.
- Must require case_study clean source before full validation.
- Must mark daily_story as synthetic if no user daily notes are supplied.
- Must keep source replacement separate from runtime implementation.

## Verification

No pytest or generation run is required for this docs-only package.

Required checks:

```text
Read back README.md / TASK.md / PROGRESS.md / ROLLBACK.md / EXECUTION_PROMPT.md.
Confirm no files under note/ were modified.
Confirm no fixture files were modified.
```
