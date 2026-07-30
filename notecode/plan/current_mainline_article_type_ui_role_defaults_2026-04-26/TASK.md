# TASK

## Phase 01 - UI Handoff Defaults

Status: completed

- Add app-local article type handoff defaults.
- Apply defaults to confirm preview, question policy, and generation request handoff.
- Preserve explicit user choices.
- Keep implementation in `note_writer_app.py`.

## Phase 02 - UI Default Selection Stability

Status: completed

- Replace stale managed default role labels when article type changes.
- Suppress programmatic default update events so journey wizard does not return to the reader step.
- Keep legacy `企業担当者として語る` as managed default compatibility label.

## Phase 03 - Validation

Status: partial

- py_compile: passed
- focused pytest: passed
- 8080 listener: recovered and retained at final check
- first-trial UI generation:
  - announcement: OK
  - comparative_review: OK
  - company_introduction: generated, but review-required quality warning remains

## Stop / Hold

Company-introduction visible quality is not green:

- `runtime_reason_code=SYS_QUALITY_WARNINGS_UNRESOLVED`
- `outcome=review_required_draft`
- image generation was requested but not observed because the article was blocked as review-required

Do not escalate into prompt / pipeline / guard changes inside this package.
