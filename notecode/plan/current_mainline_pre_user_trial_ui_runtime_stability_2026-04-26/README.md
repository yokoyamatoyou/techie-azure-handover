# current_mainline_pre_user_trial_ui_runtime_stability_2026-04-26

## Objective

user trial 前 UI 実操作 validation で観測された UI/runtime stability blocker を、既存 artifact / log だけで診断する。

この package は docs-only diagnosis から開始する。product code、UI 文言、prompt、persona、source contract、algorithm、threshold、repair count、quality guard、output guard、pipeline、blog image auto logic は変更しない。

## Source Artifacts

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\README.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\USER_TRIAL_RUNBOOK.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\CHECKLIST.md`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\PRE_USER_TRIAL_UI_VALIDATION_2026-04-26.md`
- `C:\tetie\notecode\logs\pre_user_trial_ui_validation_20260426-205318\`
- `C:\tetie\notecode\logs\app.log`
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md`
- `C:\tetie\notecode\ALGORITHM.md` sections 4, 5, 12, 13
- `C:\tetie\WORKLOG.md`

## First Blocker

First blocker is UI lifecycle / background task cleanup in:

- `C:\tetie\notecode\note\note_writer_app.py`

Primary hypothesis:

- NiceGUI client / page detach 後も `run_generation()`, image auto progress, generation phase UI update, cleanup, `ui.notify` が stale UI element / slot を更新している。
- This causes repeated `RuntimeError: The client this element belongs to has been deleted.` and `RuntimeError: The parent element this slot belongs to has been deleted.`
- The deleted client / slot tracebacks are the highest priority blocker before user trial because they correlate with UI operation timeouts and later 8080 listener loss.

## Non-goals

- Do not adjust generation quality, persona, source packet, prompt, repair count, threshold, output guard, quality guard, pipeline, or GPT Image 2 prompt / retry policy.
- Do not restart the note writer app split initiative.
- Do not rerun full-flow validation.
- Do not start a UI server as part of this docs-only diagnosis.
- Do not treat `company_introduction` content quality as actionable until UI runtime stability is fixed.
- Do not fix by extending timeouts, adding sleeps, swallowing exceptions broadly, or weakening guards.

## Decision

User trial must remain blocked.

Next implementation should be one owner / one narrow hypothesis:

- owner: `note_writer_app.py`
- hypothesis: prevent stale NiceGUI client / slot UI mutation from async generation/image/legal/cleanup paths after client release

