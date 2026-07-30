# Route 0506 Source-Surface Parity Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 source-surface parity check 実行ウインドウです。

Route 0506 は shadow-only のままです。Route A replacement / adoption 判断は行いません。今回の one owner は、notecode Route 0506 が Desktop 0506 core pipeline を呼んでいるにもかかわらず、end-to-end source surface が薄くなっている可能性を検証することだけです。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. 指示ウインドウ移行 prompt:
   - `C:\tetie\notecode\docs\route_0506_instruction_window_migration_prompt_after_ab_2026-05-09.md`
5. 作業ウインドウ結果報告:
   - `C:\tetie\notecode\docs\route_0506_work_window_result_report_to_instruction_window_2026-05-09.md`
6. Latest AB / method artifacts:
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\compare_summary.json`
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\manual_review.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\README.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\method_check_summary.json`
7. Desktop 0506 reference:
   - `C:\Users\横山裕明\Desktop\0506\AGENTS.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md`
   - `C:\Users\横山裕明\Desktop\0506\WORKLOG.md`
   - `C:\Users\横山裕明\Desktop\0506\PROGRESS.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\GPT5.4mini\`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\`
8. Notecode Route 0506 owners / artifacts:
   - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
   - `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
   - `C:\tetie\notecode\tools\run_route_0506_saved_source_cli_validation.py`
   - `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\source_snapshot.json`
   - `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\input_contract.json`
9. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current State

- post-guard AB test: `reject`
- Route A: frozen / immutable
- Route 0506: shadow-only
- Route A replacement / adoption judgment: not made
- product code changed in latest report window: false
- Desktop 0506 method check:
  - same core engine: yes
  - same end-to-end generation surface: no
- current bottleneck hypothesis:
  - `source_surface_parity_gap`

## Evidence To Preserve

AB result:

- `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\compare_summary.json`
- decision: `reject`
- winner_distribution:
  - Route A better: `2`
  - tie: `1`
  - Route 0506 better: `0`
  - blocked: `0`
- all Route 0506 candidates were QA-red:
  - run_01: `model_frequent_word`
  - run_02: `model_frequent_word`
  - run_03: `first_person_inconsistency`

Method check result:

- notecode Route 0506 imports Desktop 0506 and calls `BlogPipelineRunner.run_extracted_sources(...)`
- model / reasoning are aligned:
  - `gpt-5.4-mini`
  - `high`
- post-guard AB source snapshot was only:
  - `notecode_typed_contract:company_introduction_script_packet`: `319 chars`
  - `notecode_typed_contract:company_introduction_source_contract`: `524 chars`
  - `notecode_typed_contract:source_grounding_items`: `524 chars`
- Desktop 0506 good company-introduction artifacts under `C:\Users\横山裕明\Desktop\0506\artifacts\GPT5.4mini\` are around `2.5k-3.0k bytes`.

## One Owner

Route 0506 source-surface parity check only.

Answer these questions before any code edit:

1. What exact object shape does Desktop 0506 native flow pass into source cards / knowledge pack / article brief for good company-introduction outputs?
2. What exact object shape does notecode Route 0506 pass after typed source conversion?
3. Is the compact notecode typed source surface missing fields or density that Desktop 0506 relies on?
4. Can parity be tested using saved artifacts only?
5. If a run is necessary, can it be done with saved source / saved Desktop-like source-card or knowledge-pack artifacts and no URL refetch?
6. Are `model_frequent_word` and narrator inconsistency downstream symptoms of source surface thinness, or separate owners?

## Hard Boundaries

- Do not regenerate Route A.
- Do not refetch URLs.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not restore old Route B / Route D / Route E / deepresearch routes from archive.
- Do not reopen `sentence_too_long`.
- Do not reopen visible-output shape guard.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Do not add broad prompt tuning.
- Do not add new repair loops.
- Do not make Route A replacement / adoption judgment.
- Do not treat source hash equality alone as quality parity.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Allowed Work

Allowed:

- read-only comparison of Desktop 0506 native artifacts and notecode Route 0506 artifacts
- artifact-only reconstruction of surface differences
- local deterministic checks if they do not call external APIs
- a saved-source-only parity run if needed and if no URL refetch / Route A generation occurs
- a small owner-local adapter patch only if diagnosis proves a concrete source-surface shape gap and the patch does not reopen prompt tuning

Default expectation:

- start with diagnosis-only
- do not patch unless the artifact evidence identifies a precise adapter/surface gap

## Suggested Artifact Root

```text
C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\
```

Required before any code edit:

```text
diagnosis.md
surface_compare.json
decision_before_edit.md
```

`surface_compare.json` should include:

- Desktop 0506 artifact paths inspected
- notecode Route 0506 artifact paths inspected
- Desktop native source surface summary
- notecode typed source surface summary
- char counts / fact counts / section counts when available
- fields present in Desktop native flow but absent from notecode handoff
- parity_gap_confirmed: true | false
- whether a saved-source parity run is needed

If code is changed, create:

```text
fix_attempt_01\hypothesis.md
fix_attempt_01\code_diff_summary.md
fix_attempt_01\test_result.txt
fix_attempt_01\rerun_summary.json
```

## Rerun / API Policy

Default: no OpenAI API call.

Allowed only if diagnosis proves it is necessary:

- Route 0506 saved-source-only parity run
- no Route A generation
- no URL refetch
- no old route fallback
- `OPENAI_MODEL=gpt-5.4-mini`
- `OPENAI_REASONING_EFFORT=high`

If OpenAI client/key is unavailable when a live run is necessary, stop as `blocked`; do not invent local/mock fallback output.

## Tests

If no product code changes:

- validate JSON artifacts with `ConvertFrom-Json`
- no pytest required

If product code changes:

```powershell
.\.venv\Scripts\python.exe -m py_compile note\route_0506_structured_blog_adapter.py note\route_0506_stage_output_guard.py tools\run_route_0506_saved_source_cli_validation.py note\tests\test_route_0506_structured_blog_adapter.py
.\.venv\Scripts\python.exe -m pytest -q note\tests\test_route_0506_structured_blog_adapter.py note\tests\test_route_0506_saved_source_cli_validation.py
```

Add or update focused tests only for the changed owner.

## Decision Rules

Use `continue_shadow` if:

- source-surface parity gap is plausible or confirmed but not fixed in this window
- or the route remains useful as a shadow diagnostic but not adoption-ready

Use `fixed_continue_shadow` if:

- a precise source-surface adapter gap is fixed with focused tests and guardrails remain false

Use `needs_next_owner` if:

- diagnosis proves source-surface parity is not the bottleneck and the next issue is recurring `model_frequent_word` or narrator consistency

Use `reject` if:

- source-surface parity check shows the Route 0506 path cannot be made comparable without broad prompt tuning / acceptance relaxation / old route revival

Use `blocked` if:

- required artifacts are missing
- comparison cannot proceed without URL refetch / Route A regeneration / adoption decision
- necessary API execution is unavailable

## Final Report Contract

Report in this exact shape:

```text
decision: continue_shadow | fixed_continue_shadow | needs_next_owner | reject | blocked
artifact_root:
diagnosis_only: true | false
changed_files:
source_surface_compared:
desktop_native_surface:
notecode_typed_surface:
parity_gap_confirmed: true | false
parity_gap_summary:
desktop_artifacts_used:
notecode_artifacts_used:
route_a_regenerated: false
url_refetched: false
route_a_fallback_used: false
old_routes_reopened: false
sentence_too_long_reopened: false
visible_output_shape_guard_reopened: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
api_send: true | false
tests:
manual_japanese_naturalness_note:
next_one_owner:
WORKLOG_update_needed: true | false
```

If `WORKLOG_update_needed=true`, update only the Route 0506 current state / next owner pointer. Do not rewrite unrelated history.
