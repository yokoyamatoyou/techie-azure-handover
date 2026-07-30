# TASK

## Phase 00: Docs-only Diagnosis

Status: completed

Owner:

- `C:\tetie\notecode\plan\current_mainline_pre_user_trial_ui_runtime_stability_2026-04-26\`
- `C:\tetie\WORKLOG.md`

Scope:

- Read existing readiness docs and validation artifacts.
- Classify observed failures.
- Select the first blocker.
- Produce a next-window implementation prompt.

Exit criteria:

- failure timeline documented
- first blocker classified
- root cause candidates ranked
- not-root-cause list documented
- next owner limited to one scope
- AGENTS update need stated

## Phase 01: UI Lifecycle / Detached Client Boundary

Status: next

Owner:

- `C:\tetie\notecode\note\note_writer_app.py`

Narrow hypothesis:

- async UI paths continue mutating NiceGUI elements after the owning client / slot has been deleted.
- adding an explicit lifecycle boundary around UI mutations prevents deleted client / slot tracebacks without changing generation behavior.

Allowed direction:

- Add a bounded UI lifecycle safety boundary around UI element mutation from async generation, image auto, legal postcheck, cleanup, and notification paths.
- Prefer explicit client-alive / generation-token / detached-client early-exit semantics.
- Preserve article result persistence and GPT Image 2 image fail-open contract.
- Keep responsibilities in `note_writer_app.py`.

Forbidden direction:

- prompt / persona / source contract / algorithm / threshold / repair count changes
- `quality_guard.py`, `output_guard.py`, `pipeline.py`, `blog_image_auto.py` changes
- timeout extension, sleep increase, broad exception swallowing, guard weakening
- full-flow validation rerun as the first action
- additional split / extraction work

Required checks:

- `py_compile` for `note_writer_app.py`
- focused pytest for `note_writer_app` / current-mainline UI helper tests
- static or targeted unit check proving detached UI mutation does not call NiceGUI element setters after client release
- no UI server startup unless explicitly requested after unit/static checks

Stop conditions:

- if fix requires generation-quality or algorithm owner, stop
- if root cause cannot be separated from harness-only selector drift, stop
- if more than one owner is required, choose `note_writer_app.py` lifecycle owner first or stop with reason
- if only viable fix is timeout/sleep/exception swallowing, stop

## Shared Checks

- product code hash should only change in `note_writer_app.py` if Phase 01 is implemented
- AGENTS update is not required for this package
- user trial remains blocked until the lifecycle blocker is fixed and a narrow UI runtime check passes

