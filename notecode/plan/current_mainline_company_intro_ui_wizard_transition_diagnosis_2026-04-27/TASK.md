# current_mainline_company_intro_ui_wizard_transition_diagnosis_2026-04-27 TASK

## Phase Map

| Phase | Owner | Status | Gate |
|---|---|---|---|
| 0 Read required docs | docs | complete | Root/service AGENTS, validation PROGRESS, related UI/defaults/runtime PROGRESS, WORKLOG read |
| 1 Inspect artifacts | docs | complete | Summary, per-attempt summaries, replacement summaries, screenshots, DOM/text snapshots, app excerpts inspected |
| 2 Build failure timeline | docs | complete | Attempts 3-6 separated by waited selector and visible UI state |
| 3 Classify first blocker | docs | complete | Harness selector/state drift separated from product UI bug and generation quality |
| 4 Owner decision | docs | complete | Product owner rejected; validation harness owner selected |
| 5 Docs closeout | docs | complete | README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT / WORKLOG updated |

## Narrow Hypothesis

`company_introduction` wizard transition failure is caused by the harness waiting for fixed labels and a fixed wizard step order while the UI uses managed defaults for company-introduction target and writer state.

## Required Checks

- Confirm attempts 1 and 2 reached generation.
- Confirm attempt 3 failed before generation.
- Confirm replacement attempts 4-6 failed before generation.
- Confirm `listener_8080_alive_after_attempt=true` for failed attempts.
- Confirm product code hash diff is `NO_PRODUCT_CODE_HASH_DIFF`.
- Compare harness wait condition with visible UI text for attempts 3-6.
- Confirm attempt 3/4 waited for `誰の立場で書くか` while UI remained at `STEP3 読者`.
- Confirm attempt 5 waited for `STEP2 内容` while UI already showed `STEP4 書き手`.
- Confirm attempt 6 reached `STEP4 書き手` / `確認へ` in `controls_set`, then later captured default state.
- Confirm app log evidence of prior generation overlapping next source upload.

## Stop / Retry Rule

- This package is docs-only and completed after diagnosis.
- Do not attempt product fixes from this package.
- If a minimal company-only transition harness still fails after active-state handling, stop and reclassify as possible product wizard state bug in a new package.

## Owner Boundaries

Allowed for next implementation only:

- validation harness / artifact collection for a single company-introduction transition check

Forbidden:

- `C:\tetie\notecode\note\note_writer_app.py`
- helper modules
- prompt / persona / source contract
- repair count / thresholds
- `quality_guard.py`
- `output_guard.py`
- `pipeline.py`
- `blog_image_auto.py`
- full validation rerun

