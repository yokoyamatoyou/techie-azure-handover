# Route 0506 Fullness / Article-Brief Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 fullness-control / article-brief 診断・修正ウインドウです。

Route 0506 は shadow-only のままです。Route A replacement / adoption 判断は行いません。実施範囲は、same typed company-introduction source surface で出た article fullness の不安定さを、article brief / final article shaping の狭い owner として見ることだけです。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. `C:\tetie\notecode\docs\route_0506_instruction_window_migration_prompt_2026-05-09.md`
5. `C:\tetie\notecode\docs\route_0506_repeatability_fullness_next_window_prompt_2026-05-09.md`
6. `C:\tetie\notecode\docs\route_0506_visible_output_shape_guard_next_window_prompt_2026-05-09.md`
7. Latest visible-output shape guard fix:
   - `C:\tetie\notecode\logs\route_0506_visible_output_shape_guard_20260509\fix_attempt_01\hypothesis.md`
   - `C:\tetie\notecode\logs\route_0506_visible_output_shape_guard_20260509\fix_attempt_01\evidence.md`
   - `C:\tetie\notecode\logs\route_0506_visible_output_shape_guard_20260509\fix_attempt_01\code_diff_summary.md`
   - `C:\tetie\notecode\logs\route_0506_visible_output_shape_guard_20260509\fix_attempt_01\test_result.txt`
8. Repeatability / fullness artifacts:
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\repeatability_summary.json`
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\manual_review.md`
   - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\preflight.json`
   - run artifacts under:
     - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\run_01\`
     - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\run_02\`
     - `C:\tetie\notecode\logs\route_0506_repeatability_fullness_20260509\run_03\`
9. Code / likely owner files:
   - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
   - `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
   - `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`
10. `C:\tetie\notecode\ALGORITHM.md`
    - `## 4. Single-Pass Generation`
    - `## 5. Repair Algorithm`
    - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current State

- latest decision: `fixed_continue_shadow` for visible-output shape guard
- Route 0506 remains shadow-only.
- Route A replacement / adoption judgment is not active.
- Completed owners:
  - source handoff mismatch
  - `sentence_too_long`
  - manual shadow review
  - repeatability / fullness review
  - visible-output shape guard
- Repeatability / fullness result:
  - decision: `continue_shadow_with_fullness_risk`
  - source snapshot hash: `fd11521c0200f82a3ce77dcda89c4296d55f40f8bb03247e2df07d2ffab0ae80`
  - body chars: `949, 1213, 1227`
  - prior 652-char under-fill did not repeat exactly
  - run_01: compact and QA-red on `model_frequent_word`
  - run_02: strongest visible article in that window
  - run_03: had wrapper / code-fence leakage, now guard-fixed by focused tests without OpenAI rerun

## One Owner

Route 0506 fullness-control / article-brief stability for same typed company-introduction source surface.

The first task is diagnosis. Do not jump straight to prompt or code changes.

Inspect per run:

- `article_brief.json`
- `article_knowledge_pack.json`
- `source_cards.json`
- `source_packets.json`
- `draft.md`
- `edited_draft.md`
- `structural_edited_draft.md`
- `latest_generation_output.md`
- `latest_generation_quality_report.json`
- `validation_summary.json`

Compare:

- brief target length
- section count
- claim allocation per section
- confirmed fact count
- source card fact count
- body char count
- heading count
- QA issues
- manual naturalness / article adequacy notes

## Diagnosis Questions

Answer these before editing:

1. Did compactness come from article brief target length / claim allocation?
2. Did compactness come from editor stages shortening an adequate draft?
3. Did compactness come from source packet / knowledge pack being too thin after typed source handoff?
4. Is `model_frequent_word` in run_01 related to fullness, or a separate quality owner that should not be mixed?
5. After visible-output shape guard fix, is another OpenAI rerun necessary to evaluate fullness, or can this window stop after diagnosis?

## Hard Boundaries

- Do not regenerate Route A.
- Do not refetch URLs.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not reopen source handoff.
- Do not reopen `sentence_too_long`.
- Do not reopen visible-output shape guard unless local tests prove the fix is incomplete.
- Do not reopen Desktop 0506 algorithm.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Do not add broad prompt tuning.
- Do not add new repair loops.
- Do not make Route A replacement / adoption judgment.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Allowed Work

Allowed:

- read-only diagnosis across existing artifacts
- focused tests for the diagnosed owner
- a small owner-local patch only if artifacts prove a concrete notecode-side fullness / article-brief boundary issue

Likely patch owners if proven:

- `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
- focused tests in `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`

Not allowed as a first move:

- broad style prompt rewrite
- broad target length increase
- multi-article matrix
- adoption comparison
- changing Desktop 0506

## Artifact Root

Create:

```text
C:\tetie\notecode\logs\route_0506_fullness_article_brief_20260509\
```

Required before any code edit:

```text
diagnosis.md
stage_compare.json
decision_before_edit.md
```

If code is changed, create:

```text
fix_attempt_01\hypothesis.md
fix_attempt_01\code_diff_summary.md
fix_attempt_01\test_result.txt
fix_attempt_01\rerun_summary.json
```

## Tests

If no product code is changed:

- validate JSON artifacts with `ConvertFrom-Json`
- no pytest required

If product code is changed, run at minimum:

```powershell
.\.venv\Scripts\python.exe -m py_compile note\route_0506_structured_blog_adapter.py note\route_0506_stage_output_guard.py note\tests\test_route_0506_structured_blog_adapter.py
.\.venv\Scripts\python.exe -m pytest -q note\tests\test_route_0506_structured_blog_adapter.py
```

Add more focused tests only for the changed owner.

## Rerun Policy

Default: do not call OpenAI.

Allowed only after diagnosis or a code fix proves a rerun is necessary:

- one same saved-source Route 0506 OpenAI rerun
- `OPENAI_MODEL=gpt-5.4-mini`
- `OPENAI_REASONING_EFFORT=high`
- no Route A regeneration
- no URL refetch

If OpenAI client/key is unavailable, stop as `blocked`; do not invent local/mock fallback output.

## Decision Rules

Use `continue_shadow` if:

- existing evidence shows fullness is adequate after visible-output guard fix
- no code change is needed
- next owner is not active

Use `fixed_continue_shadow` if:

- a narrow article-brief/fullness boundary issue is proven and fixed with focused tests
- guardrails remain false

Use `needs_next_owner` if:

- diagnosis shows the issue is not fullness/article-brief but a separate quality owner, such as `model_frequent_word`

Use `blocked` if:

- required artifacts are missing
- validation cannot proceed without widening scope
- OpenAI rerun is necessary but unavailable

Use `reject` only if:

- existing evidence proves Route 0506 is repeatedly not article-like or too thin as shadow, without needing adoption comparison

## Final Report Contract

Report in this exact shape:

```text
decision: continue_shadow | fixed_continue_shadow | needs_next_owner | blocked | reject
artifact_root:
diagnosis_only: true | false
changed_files:
source_snapshot_hash:
body_char_counts_reviewed:
brief_target_lengths:
section_counts:
claim_allocation_summary:
compactness_cause:
model_frequent_word_mixed: false
route_a_regenerated: false
url_refetched: false
api_send: true | false
source_handoff_reopened: false
sentence_too_long_reopened: false
visible_output_shape_guard_reopened: false
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

If `WORKLOG_update_needed=true`, update only the Route 0506 current state / next owner pointer. Do not rewrite unrelated history.
