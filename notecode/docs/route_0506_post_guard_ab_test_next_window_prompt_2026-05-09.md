# Route 0506 Post-Guard AB Test Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 post-fix AB test 実行ウインドウです。

目的は、修正後 Route 0506 OpenAI candidate と frozen Route A saved artifact を、同じ saved / typed company-introduction source surface で比較することです。Route A replacement / adoption 判断は行いません。結果は shadow 継続可否と残リスクの整理に限定します。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. Current instruction / prior prompts:
   - `C:\tetie\notecode\docs\route_0506_instruction_window_migration_prompt_2026-05-09.md`
   - `C:\tetie\notecode\docs\route_0506_repeatability_fullness_next_window_prompt_2026-05-09.md`
   - `C:\tetie\notecode\docs\route_0506_visible_output_shape_guard_next_window_prompt_2026-05-09.md`
   - `C:\tetie\notecode\docs\route_0506_fullness_article_brief_next_window_prompt_2026-05-09.md`
5. Latest fixed / diagnosis artifacts:
   - `C:\tetie\notecode\logs\route_0506_visible_output_shape_guard_20260509\fix_attempt_01\hypothesis.md`
   - `C:\tetie\notecode\logs\route_0506_visible_output_shape_guard_20260509\fix_attempt_01\evidence.md`
   - `C:\tetie\notecode\logs\route_0506_visible_output_shape_guard_20260509\fix_attempt_01\code_diff_summary.md`
   - `C:\tetie\notecode\logs\route_0506_visible_output_shape_guard_20260509\fix_attempt_01\test_result.txt`
   - `C:\tetie\notecode\logs\route_0506_fullness_article_brief_20260509\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_fullness_article_brief_20260509\stage_compare.json`
   - `C:\tetie\notecode\logs\route_0506_fullness_article_brief_20260509\decision_before_edit.md`
6. Source / prior compare artifacts:
   - `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\source_snapshot.json`
   - `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\input_contract.json`
   - `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\route_a_saved\latest_generation_output.json`
   - `C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\compare_summary.json`
   - `C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\manual_review.md`
7. Runtime owners:
   - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
   - `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
   - `C:\tetie\notecode\note\route_0506_ui_bridge.py`
   - `C:\tetie\notecode\tools\run_route_0506_saved_source_cli_validation.py`
   - `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`
8. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current State

- Route 0506 remains `shadow-only`.
- Route A replacement / adoption judgment is not active.
- Completed and closed:
  - source handoff mismatch
  - `sentence_too_long`
  - manual shadow review
  - repeatability / fullness review
  - visible-output shape guard
  - fullness / article-brief diagnosis
- Latest source surface:
  - typed company-introduction source records
  - source chars: `319, 524, 524`
  - source snapshot hash: `fd11521c0200f82a3ce77dcda89c4296d55f40f8bb03247e2df07d2ffab0ae80`
- Known fixed guard behavior:
  - structural editor wrapper / `### 修正版` / fenced article block must fail-open to previous clean article
- Known residual observations:
  - previous same-source Route 0506 body chars: `949, 1213, 1227`
  - compactness was diagnosed as generation-side fullness variability, not brief/source/editor structural bug
  - `model_frequent_word` appeared once and should be treated as a separate quality owner only if it recurs

## One Owner

Post-fix AB test:

```text
Frozen Route A saved artifact
vs
Route 0506 OpenAI candidate after source handoff / sentence boundary / visible-output guard fixes
```

Default target:

- article type: `company_introduction`
- source: same saved typed company-introduction source surface
- runs: `3` Route 0506 OpenAI candidate reruns
- Route A: saved artifact only

Do not expand to other article types unless inventory proves they have completed saved Route A artifacts and saved source contracts without URL refetch. If uncertain, keep this AB test company-introduction only.

## Hard Boundaries

- Do not regenerate Route A.
- Do not refetch URLs.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not reopen source handoff.
- Do not reopen `sentence_too_long`.
- Do not reopen visible-output shape guard unless a post-fix rerun proves guard leakage still reaches reader-facing output.
- Do not reopen fullness / article-brief diagnosis unless under-fill recurs in this AB run.
- Do not reopen Desktop 0506 algorithm.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Do not add broad prompt tuning.
- Do not add new repair loops.
- Do not make Route A replacement / adoption judgment.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## API Send Scope

Allowed API sends:

- Route 0506 OpenAI candidate only
- max `3` same-source runs
- `OPENAI_MODEL=gpt-5.4-mini`
- `OPENAI_REASONING_EFFORT=high`
- no URL refetch
- no Route A generation

Before sending, create and inspect preflight:

```text
C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\preflight.json
```

Preflight must include:

- selected Route A saved artifact path
- selected input contract path
- selected source snapshot path
- source snapshot hash
- planned Route 0506 run count
- estimated API request count if available
- guardrail booleans
- OpenAI client/key availability status if checked

If OpenAI client/key is unavailable, stop as `blocked`. Do not invent local/mock fallback output.

## Artifact Root

Use:

```text
C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\
```

Per run:

```text
run_01\
run_02\
run_03\
```

Each run record must include:

- `api_send`
- `model`
- `reasoning_effort`
- `source_snapshot_hash`
- `route_a_artifact_path`
- `route_0506_output_path`
- `body_char_count`
- `heading_count`
- `quality_pass`
- `quality_score`
- `quality_issues`
- `max_sentence_length`
- `visible_output_shape_ok`
- `source_faithfulness`
- `article_adequacy`
- `fullness_handling`
- `manual_japanese_naturalness_note`
- per-run decision: `route_a_better | route_0506_better | tie | blocked`

After all completed runs, create:

```text
C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\compare_summary.json
C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\manual_review.md
```

## Review Criteria

Compare Route A and each Route 0506 run on:

- article shape: title/heading/body visibility, no wrapper/code fence leakage
- source-faithfulness: no source-outside claims, no source contract leak
- company/service introduction fit
- Japanese naturalness
- body fullness / under-fill
- QA pass / score / issue types
- repeated quality issues, especially `model_frequent_word`
- whether Route 0506 is consistently better, worse, or mixed

Do not treat hash equality alone as quality equality. Inspect visible article shape.

## Blocked / Error Policy

If a run blocks or errors:

1. Record the blocked artifact under:

```text
C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\blocked_attempt_XX\
```

2. Identify one narrow owner.
3. Patch only if it is an execution blocker or guard regression inside the current owner.
4. Run focused tests.
5. Rerun the exact failed case.

Stop after 5 blocked/error self-fix attempts. Do not start a sixth fix.

Do not patch article quality, prompt tone, target length, threshold, or repair policy inside this AB window. If quality is the issue, record it and close with `continue_shadow` or `reject`.

## Required Tests

If no product code changes:

- validate JSON artifacts with `ConvertFrom-Json`
- no pytest required

If product code changes:

```powershell
.\.venv\Scripts\python.exe -m py_compile note\route_0506_structured_blog_adapter.py note\route_0506_stage_output_guard.py note\route_0506_ui_bridge.py tools\run_route_0506_saved_source_cli_validation.py note\tests\test_route_0506_structured_blog_adapter.py
.\.venv\Scripts\python.exe -m pytest -q note\tests\test_route_0506_structured_blog_adapter.py note\tests\test_route_0506_ui_bridge.py note\tests\test_route_0506_saved_source_cli_validation.py
```

## Decision Rules

Use `continue_shadow` if:

- Route 0506 is mixed, promising, or not clearly worse, but not stable enough for adoption
- any quality risk remains but does not justify reject

Use `reject` if:

- Route 0506 is repeatedly worse than frozen Route A on visible article quality
- source-faithfulness concerns recur
- visible-output leakage recurs despite the guard fix
- repeated under-fill or repeated quality issue makes it unsuitable even as shadow

Use `blocked` if:

- the AB test cannot complete due to execution/runtime issues
- required artifacts are missing
- OpenAI send is unavailable

Do not output `adopt` or `replace_route_a`.

## Final Report Contract

Report in this exact shape:

```text
decision: continue_shadow | reject | blocked
artifact_root:
article_types_attempted:
runs_completed:
api_send_count:
source_snapshot_hash:
route_a_artifact:
route_0506_artifacts:
body_char_counts:
quality_results:
visible_output_shape_ok_by_run:
source_faithfulness_by_run:
article_adequacy_by_run:
winner_by_run:
winner_distribution:
route_a_regenerated: false
url_refetched: false
route_a_fallback_used: false
source_handoff_reopened: false
sentence_too_long_reopened: false
visible_output_shape_guard_reopened: false
fullness_article_brief_reopened: false
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
