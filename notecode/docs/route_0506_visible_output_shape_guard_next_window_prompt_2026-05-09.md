# Route 0506 Visible Output Shape Guard Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 final visible-output shape guard 修正ウインドウです。

実施範囲は、Route 0506 structural editor 由来の editor-wrapper / code-fence leakage を reader-facing output へ出さない境界だけです。Route A replacement / adoption 判断、source handoff、`sentence_too_long`、fullness tuning、Desktop 0506 algorithm は触りません。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. `C:\tetie\notecode\docs\route_0506_instruction_window_migration_prompt_2026-05-09.md`
5. `C:\tetie\notecode\docs\route_0506_repeatability_fullness_next_window_prompt_2026-05-09.md`
6. Latest repeatability / fullness artifacts:
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\repeatability_summary.json`
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\manual_review.md`
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\run_03\route_0506\latest_generation_output.md`
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\run_03\route_0506\latest_generation_quality_report.json`
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\run_03\route_0506\pipeline_stage_artifacts\route_0506_saved_source_cli_validation\draft.md`
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\run_03\route_0506\pipeline_stage_artifacts\route_0506_saved_source_cli_validation\opening_edited_draft.md`
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\run_03\route_0506\pipeline_stage_artifacts\route_0506_saved_source_cli_validation\global_consistency_edited_draft.md`
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\run_03\route_0506\pipeline_stage_artifacts\route_0506_saved_source_cli_validation\edited_draft.md`
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\run_03\route_0506\pipeline_stage_artifacts\route_0506_saved_source_cli_validation\structural_edited_draft.md`
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\run_03\route_0506\pipeline_stage_artifacts\route_0506_saved_source_cli_validation\editor_pass_report.json`
7. Code owner:
   - `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
   - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
   - `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`
8. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current State

- decision: `continue_shadow_with_fullness_risk`
- Route 0506 is not adopted over Route A.
- Route A remains frozen.
- Source handoff owner is complete.
- `sentence_too_long` owner is complete.
- Manual shadow review is complete.
- Repeatability / fullness rerun result:
  - runs completed: `3`
  - body chars: `949, 1213, 1227`
  - source-faithfulness: `pass, pass, pass`
  - run_03 article adequacy: `failed`
- Confirmed bug candidate:
  - `run_03` final visible output starts with editor-wrapper explanation.
  - It includes `### 修正版` and a fenced ```text article block.
  - QA still reports `pass=true / score=100 / issues=[]`.

## Evidence

Run 03 final output begins with:

```text
以下の点を整えて、後半の流れと全体の統一感をそろえました。

- 5章は、...

### 修正版
```text
## 私たちが大切にしていること
...
```

Stage evidence:

- `draft.md`, `opening_edited_draft.md`, `global_consistency_edited_draft.md`, and `edited_draft.md` are clean article-only markdown.
- `structural_edited_draft.md` introduces the wrapper / fenced article.
- `latest_generation_output.md` preserves that wrapper / fenced article.
- Existing `route_0506_stage_output_guard.py` catches meta-review markers and collapse, but does not catch this wrapper/code-fence article contract failure.

## One Owner

Patch only the final visible-output shape guard for Route 0506 stage outputs.

Primary expected owner:

```text
C:\tetie\notecode\note\route_0506_stage_output_guard.py
```

Expected behavior:

- For article-output stages, reject/fail-open to previous article when generated output wraps the article in explanatory text or fenced code.
- A generated output that starts with explanation bullets and then `### 修正版` + ```text must not become reader-facing output.
- Valid markdown article output without wrapper/fence must still pass.
- Do not strip wrapper text as a broad cleanup unless the existing Route 0506 contract already has a safe extraction boundary. Prefer fail-open to previous article for this owner.

## Hard Boundaries

- Do not regenerate Route A.
- Do not refetch URLs.
- Do not use Route A fallback.
- Do not call OpenAI unless a same-run confirmation is explicitly necessary after tests and remains within one saved-source rerun.
- Do not revive old rejected routes.
- Do not reopen source handoff.
- Do not reopen `sentence_too_long`.
- Do not reopen repeatability / fullness tuning.
- Do not reopen Desktop 0506 algorithm.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Do not add broad prompt tuning.
- Do not add new repair loops.
- Do not make Route A replacement / adoption judgment.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Required Artifact

Create:

```text
C:\tetie\notecode\logs\route_0506_visible_output_shape_guard_20260509\fix_attempt_01\
```

Required files:

- `hypothesis.md`
- `evidence.md`
- `code_diff_summary.md`
- `test_result.txt`
- `rerun_summary.json` if a rerun is performed

## Required Tests

Add focused tests for:

- structural editor output with explanation + `### 修正版` + fenced article fails open to previous article
- fenced article wrapper is rejected
- valid markdown article remains accepted

Run at minimum:

```powershell
.\.venv\Scripts\python.exe -m py_compile note\route_0506_stage_output_guard.py note\route_0506_structured_blog_adapter.py note\tests\test_route_0506_structured_blog_adapter.py
.\.venv\Scripts\python.exe -m pytest -q note\tests\test_route_0506_structured_blog_adapter.py
```

If you touch other files, add them to compile/tests.

## Rerun Policy

Default: no OpenAI rerun is required if the focused guard tests reproduce and fix the wrapper leakage.

Allowed only if needed:

- one same saved-source Route 0506 rerun
- `OPENAI_MODEL=gpt-5.4-mini`
- `OPENAI_REASONING_EFFORT=high`
- no Route A regeneration
- no URL refetch

## Final Report Contract

Report in this exact shape:

```text
decision: fixed_continue_shadow | blocked | needs_next_owner
artifact_root:
changed_files:
bug_confirmed: true | false
leak_source_stage: structural_editor
route_a_regenerated: false
url_refetched: false
api_send: true | false
source_handoff_reopened: false
sentence_too_long_reopened: false
repeatability_reopened: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
tests:
rerun_result:
manual_japanese_naturalness_note:
next_one_owner:
WORKLOG_update_needed: true | false
```

If blocked, include the exact blocker and the smallest reproducible failing artifact.
