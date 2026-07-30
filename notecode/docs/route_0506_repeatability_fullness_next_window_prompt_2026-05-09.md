# Route 0506 Repeatability / Fullness Stability Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 repeatability / fullness stability 検証ウインドウです。

実施範囲は、same typed company-introduction source surface で Route 0506 OpenAI candidate が安定して十分な本文量・記事形を返すかを見ることだけです。Route A replacement / adoption 判断、source handoff 修正、`sentence_too_long` 再修正、広い prompt tuning はしません。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. `C:\tetie\notecode\docs\route_0506_instruction_window_migration_prompt_2026-05-09.md`
5. `C:\tetie\notecode\docs\route_0506_sentence_too_long_next_window_prompt_2026-05-09.md`
6. `C:\tetie\notecode\docs\route_0506_manual_shadow_review_next_window_prompt_2026-05-09.md`
7. Latest sentence-too-long fix:
   - `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_summary.json`
   - `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\evidence.md`
   - `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\validation_summary.json`
   - `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\source_snapshot.json`
   - `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\input_contract.json`
   - `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\route_0506\latest_generation_output.md`
   - `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\route_0506\latest_generation_quality_report.json`
8. Latest manual shadow review:
   - `C:\tetie\notecode\logs\route_0506_manual_shadow_review_20260509\manual_review.md`
   - `C:\tetie\notecode\logs\route_0506_manual_shadow_review_20260509\review_summary.json`
9. Prior AB / compare references:
   - `C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\compare_summary.json`
   - `C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\manual_review.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\fix_attempt_01\rerun_summary.json`
10. `C:\tetie\notecode\ALGORITHM.md`
    - `## 4. Single-Pass Generation`
    - `## 5. Repair Algorithm`
    - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current State

- decision: `continue_shadow`
- Route 0506 is not adopted over Route A.
- Route A remains frozen.
- Source handoff owner is complete.
- `sentence_too_long` owner is complete.
- Manual shadow review result:
  - article_adequacy: `acceptable`
  - source_faithfulness: `pass`
  - shortness_handling: `acceptable_shadow`
- Latest candidate was coherent and source-faithful, but short:
  - `body_char_count=652`
  - `quality_pass=true`
  - `score=100`
  - `issues=[]`
- Next question:
  - Is the 652-char under-fill a one-off acceptable shadow output, or a repeatable shortness / fullness stability regression?

## One Owner

Route 0506 repeatability / fullness stability on the same typed company-introduction source surface.

Review only:

- body length distribution across repeated same-source OpenAI candidates
- whether each output remains a coherent company/service introduction
- source-faithfulness / source leak checks
- QA issue stability, including `sentence_too_long`
- whether shortness should remain `acceptable_shadow`, become `continue_shadow_with_fullness_risk`, or become `reject`

## Hard Boundaries

- Do not regenerate Route A.
- Do not refetch URLs.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not reopen source handoff.
- Do not reopen `sentence_too_long` threshold.
- Do not reopen Desktop 0506 algorithm.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Do not add broad prompt tuning.
- Do not add new repair loops.
- Do not change product code unless a pure harness/artifact blocker prevents validation and the fix is explicitly owner-local.
- Do not make Route A replacement / adoption judgment.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## API Send Scope

This window may run OpenAI only for this exact validation:

- same saved typed company-introduction source surface
- Route 0506 OpenAI candidate only
- max `3` reruns
- `OPENAI_MODEL=gpt-5.4-mini`
- `OPENAI_REASONING_EFFORT=high`
- no URL refetch
- no Route A generation

Before sending, create a preflight artifact and state:

- selected source snapshot path
- selected input contract path
- source snapshot hash
- planned run count
- estimated API request count if available
- guardrail booleans

If the runtime lacks a working OpenAI client or key, stop as `blocked`. Do not invent local/mock fallback output.

## Suggested Artifact Root

```text
C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\
```

Create before any API call:

```text
preflight.json
```

For each run, create or preserve:

```text
run_01\
run_02\
run_03\
```

Per-run review should record:

- `api_send`
- `model`
- `reasoning_effort`
- `source_snapshot_hash`
- `body_char_count`
- `heading_count`
- `quality_pass`
- `quality_score`
- `quality_issues`
- `max_sentence_length`
- `article_adequacy`: `acceptable | thin | failed`
- `source_faithfulness`: `pass | concern | blocked`
- `shortness_handling`: `acceptable_shadow | fullness_risk | too_thin`
- `manual_japanese_naturalness_note`

After all completed runs, create:

```text
repeatability_summary.json
manual_review.md
```

## Decision Rules

Use `continue_shadow` if:

- at least two completed runs are acceptable as company/service introductions
- source-faithfulness remains pass
- shortness is not repeatedly too thin
- QA remains green or only minor non-blocking issues appear

Use `continue_shadow_with_fullness_risk` if:

- outputs are coherent and source-faithful
- but body length / fullness is unstable or repeatedly compact enough to be a known risk
- next owner should be a narrow fullness-control or article-brief owner

Use `reject` if:

- repeated candidates are too thin, incomplete, or not article-like
- source-faithfulness concerns recur
- the route is not stable enough even as shadow

Use `blocked` if:

- artifacts are missing
- OpenAI execution cannot run
- validation cannot complete without widening scope

## Final Report Contract

Report in this exact shape:

```text
decision: continue_shadow | continue_shadow_with_fullness_risk | reject | blocked
artifact_root:
runs_completed:
api_send_count:
source_snapshot_hash:
body_char_counts:
quality_results:
article_adequacy_by_run:
source_faithfulness_by_run:
shortness_handling_by_run:
route_a_regenerated: false
url_refetched: false
source_handoff_reopened: false
sentence_too_long_reopened: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
product_code_changed: true | false
tests:
manual_japanese_naturalness_note:
next_one_owner:
WORKLOG_update_needed: true | false
```

If `WORKLOG_update_needed=true`, update only the Route 0506 current state / next owner pointer. Do not rewrite unrelated history.
