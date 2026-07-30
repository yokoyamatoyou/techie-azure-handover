# company_intro_self_perspective_tuning_cycle_2026-04-27

## Objective

Validate whether current mainline output for `announcement`, `comparative_review`, and `company_introduction` reads from a clear first-party/self-side speaker position, and tune only the writer prompt consumption if needed.

This package focuses on self-perspective, title fit, and title-image display copy. It does not change source contracts, guards, image prompts, UI defaults, repair count, thresholds, or pipeline structure.

## Target Article Types

- `announcement`
- `comparative_review`
- `company_introduction`

## Source

Use the fixed source manifest:

`C:\tetie\notecode\logs\post_phase06a_success_path_ui_smoke_20260426-200726\source_snapshot_manifest_used.json`

Do not use moving `latest_generation_output` as source.

## Artifact Root

`C:\tetie\notecode\新しいフォルダー\新しいフォルダー (6)\`

Cycle directories:

- `00_no_fix_baseline\`
- `01_fix1\`
- `02_fix2\`

## Owner Boundary

Product code owner is limited to:

`C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`

If improvement requires any other runtime owner, stop without implementation and report the split.

