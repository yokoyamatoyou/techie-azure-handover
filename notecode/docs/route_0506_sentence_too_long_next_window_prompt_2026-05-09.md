# Route 0506 Sentence Too Long Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 final article quality 修正ウインドウです。

実施範囲は OpenAI candidate の `sentence_too_long` だけです。Route A replacement / adoption 判断はしません。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. `C:\tetie\notecode\docs\route_0506_instruction_window_migration_prompt_2026-05-09.md`
5. `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\fix_attempt_01\rerun_summary.json`
6. `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\desktop_vs_notecode_log_diff.md`
7. `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\desktop_vs_notecode_stage_diff.json`
8. `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_h1\validation_summary.json`
9. `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_h1\route_0506\latest_generation_quality_report.json`
10. `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_h1\route_0506\latest_generation_output.md`
11. `C:\tetie\notecode\ALGORITHM.md`
    - `## 4. Single-Pass Generation`
    - `## 5. Repair Algorithm`
    - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current State

- decision: `fixed_continue_shadow`
- Route 0506 is not adopted over Route A.
- Route A remains frozen.
- Desktop 0506 reference remains closed:
  - `C:\Users\横山裕明\Desktop\0506`
- Latest artifact root:
  - `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\`
- Fixed previous owner:
  - `source_handoff_mismatch`
- After the previous fix:
  - source changed from `5 raw pages` to `3 typed records`
  - source chars changed to `319, 524, 524`
  - article direction returned from broad real-estate selling guide to company/service introduction
- Still failing:
  - OpenAI one-case completed with `gpt-5.4-mini high`
  - QA result is `pass=false / score=92 / issue=sentence_too_long`
  - latest quality report shows `max_sentence_length=94`, `avg_sentence_length=45.2`, and empty issue text/span

## One Owner

OpenAI candidate final article quality, specifically `sentence_too_long`.

Your first job is diagnosis, not broad tuning:

- identify the exact long sentence or recover it from the final article / QA logic
- inspect whether the final output shaping, stage artifact, QA artifact, or targeted rewrite path loses the span
- apply the smallest notecode-side correction needed to prevent the long-sentence fail

## Hard Boundaries

- Do not regenerate Route A.
- Do not refetch URLs.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Do not add broad prompt tuning.
- Do not add a new repair loop.
- Do not reopen Desktop 0506 algorithm.
- Do not reopen source handoff unless a new artifact proves a new source-handoff blocker.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Evidence To Inspect

OpenAI one-case artifact:

```text
C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_h1\
```

Required files:

```text
validation_summary.json
route_0506\latest_generation_output.md
route_0506\latest_generation_quality_report.json
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\article_brief.json
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\draft.md
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\opening_edited_draft.md
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\global_consistency_edited_draft.md
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\edited_draft.md
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\structural_edited_draft.md
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\editor_pass_report.json
```

Known final article shape:

- `body_char_count=1179`
- `sentence_count=25`
- `max_sentence_length=94`
- `quality_issues=["sentence_too_long"]`
- `source_snapshot_hash=fd11521c0200f82a3ce77dcda89c4296d55f40f8bb03247e2df07d2ffab0ae80`
- `route_a_regenerated=false`
- `url_refetch=false`
- `threshold_relaxed=false`
- `repair_acceptance_relaxed=false`

## Diagnosis Rules

If the QA issue has no persisted span:

- first inspect the QA checker / artifact persistence path
- persist or report enough evidence to identify the exact long sentence
- do not solve by lowering the configured sentence length limit

If the long sentence is introduced by final output shaping:

- patch only the final output shaping / route bridge boundary
- preserve the typed source handoff
- do not change Desktop 0506

If the long sentence is present before final shaping:

- compare draft and editor-stage artifacts
- identify the first stage where the sentence appears
- patch only the stage/output contract needed for this owner

If the fix would require prompt tuning across article style:

- stop and report scope drift
- propose the next one owner instead of widening this window

## Self-Fix Policy

- Allow up to 5 self-fix attempts.
- Save each attempt under:

```text
C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_XX\
```

Each attempt should record:

- `hypothesis.md`
- `evidence.md`
- `code_diff_summary.md`
- `test_result.txt`
- `rerun_summary.json` if a rerun was performed

Stop after 5 errors or quality-regression attempts. Do not start a sixth attempt.

## Required Checks

Run focused checks for any touched owner. At minimum, after code changes run:

```powershell
.\.venv\Scripts\python.exe -m py_compile note\route_0506_structured_blog_adapter.py note\route_0506_stage_output_guard.py note\route_0506_ui_bridge.py tools\run_route_0506_saved_source_cli_validation.py
.\.venv\Scripts\python.exe -m pytest -q note\tests\test_route_0506_structured_blog_adapter.py note\tests\test_route_0506_ui_bridge.py note\tests\test_route_0506_saved_source_cli_validation.py
```

Add or update focused tests only for the changed owner.

## Rerun Policy

Rerun the same saved-source one-case only.

Allowed:

- saved source only
- Route 0506 OpenAI candidate
- `OPENAI_MODEL=gpt-5.4-mini`
- `OPENAI_REASONING_EFFORT=high`

Forbidden:

- Route A regeneration
- URL refetch
- full AB matrix
- broader article-type matrix
- threshold relaxation
- `repair_acceptance` relaxation
- prompt bloat

## Final Report Contract

Report in this exact shape:

```text
decision: fixed_continue_shadow | continue_shadow | blocked | reject
artifact_root:
changed_files:
long_sentence_identified: true | false
long_sentence_source_stage:
route_a_regenerated: false
url_refetched: false
source_handoff_reopened: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
tests:
OpenAI rerun result:
manual_japanese_naturalness_note:
next_one_owner:
```

If blocked, include:

- exact blocker
- artifact root
- files touched
- tests run
- guardrail booleans
- why this remains a notecode-side adapter / bridge / schema / final output shaping issue
