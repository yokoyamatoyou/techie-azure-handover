# current_mainline_post_full_flow_issue_triage_2026-04-26 README

## Objective

- `current_mainline_log_source_ui_regression_20260426-023257` の full-flow validation 後に残った課題を分類し直す。
- `source issue` / `route issue` / `UI harness issue` / `runtime quality issue` / `image issue` / `UX classification issue` を混ぜずに扱う。
- ユーザー試用前に最初に直す 1 件を決め、次の implementation package へ渡す。

## Source Of Truth

- Current runtime mainline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Source validation package:
  - `C:\tetie\notecode\plan\current_mainline_log_source_ui_regression_2026-04-26\`
- Artifact root:
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\`
- Fail-closed UX policy reference:
  - `C:\tetie\notecode\plan\current_mainline_fail_closed_ux_policy_2026-04-25\PROGRESS.md`
- This triage package:
  - `C:\tetie\notecode\plan\current_mainline_post_full_flow_issue_triage_2026-04-26\`

## Scope

- Create docs-only triage package.
- Reclassify all 18 attempts from `per_attempt_summary.jsonl`.
- Rank remaining issues by SaaS UX impact, frequency, source adequacy, and owner scope.
- Select one first implementation target.
- Create `EXECUTION_PROMPT.md` for the next implementation package.

## Non-Goals

- No product code change.
- No threshold change.
- No prompt addition.
- No repair change.
- No UI demote expansion.
- No source replacement.
- No runtime defect conclusion from source shortage alone.
- No mixing of UI harness failures into generation defects.
- No image failure classification when image validation succeeded.

## Issue Taxonomy

- `source issue`: thin, synthetic, mismatched, or caveated source limits the conclusion.
- `route issue`: selected UI route or semantic article key does not match the intended article type.
- `UI harness issue`: browser automation, click, wait, stale snapshot, or harness collection prevented a valid generation judgment.
- `runtime quality issue`: generated body exists but runtime quality warnings block or degrade output without being solely explained by source or harness.
- `image issue`: image generation itself fails or image behavior affects body workflow.
- `UX classification issue`: body exists, route/source are adequate, but UI classifies a warning-only output more harshly than the existing fail-closed UX policy intends.

## First Fix Decision

First implementation target:

- `bl-announcement-spec-change` attempts 1-2
- classification: `UX classification issue`
- current outcome: 2/2 `input_required_block`
- reason: route-matched `announcement`, source-caveat-free, body exists, no internal leakage, and the block prevents a common SaaS operational-announcement workflow.

This target is cleaner than:

- `non-company branding`: important, but a broader route mismatch / body 0 issue.
- `comparative_review`: UI harness failure, not a generation defect.
- `explanatory_article`: runtime regression candidate, but source has a thin-watch caveat.
- `product_introduction`: thin source plus mixed harness outcome.
- `daily_story`: synthetic source caveat.

