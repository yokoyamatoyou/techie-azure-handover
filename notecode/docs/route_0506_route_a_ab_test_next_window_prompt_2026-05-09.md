# Route 0506 / Route A AB Test Next Window Prompt

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 / Route A ABテスト実行ウインドウです。

記録を読み、実行し、blocked / error 時は記録と実挙動を見て、notecode 側の blocker を最大 5 回まで自己修正してください。5 回目の blocked / error でも解消できない場合は停止し、blocked artifact と `C:\tetie\WORKLOG.md` への記録を残してください。

## Objective

`C:\Users\横山裕明\Desktop\0506` の current algorithm をお手本として、`C:\tetie\notecode` の Route 0506 が Route A frozen saved artifact / saved source と同じ入力で動作するかをAB比較する。

各 article type は原則 3 回ずつ Route 0506 を生成し、Route A saved artifact と比較する。Route A は再生成しない。

## Required Read Order

1. `C:\tetie\notecode\AGENTS.md`
2. `C:\tetie\WORKLOG.md`
   - 2026-05-09 の Route 0506 entries を確認する
   - 特に latest blocked cause / stage-output guard fix / next window handoff を読む
3. `C:\tetie\notecode\docs\route_0506_route_a_compare_3x_next_window_prompt_2026-05-09.md`
4. `C:\tetie\notecode\logs\route_0506_audit_high_editor_fire_20260509\blocked.json`
5. `C:\tetie\notecode\logs\route_0506_audit_high_editor_fire_20260509\validation_summary.json`
6. `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
7. `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
8. `C:\tetie\notecode\note\route_0506_ui_bridge.py`
9. `C:\tetie\notecode\note\route_0506_saved_source_cli_validation.py`
10. `C:\Users\横山裕明\Desktop\0506\AGENTS.md`
11. `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
12. `C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md`
13. `C:\Users\横山裕明\Desktop\0506\WORKLOG.md`
14. `C:\Users\横山裕明\Desktop\0506\PROGRESS.md`
15. `C:\Users\横山裕明\Desktop\0506\artifacts\runs\`

## Hard Rules

- Route A は frozen。Route A を再生成しない。
- Route A compare は saved artifact / saved source only。
- URL refetch しない。
- local file locator / external file ingestion を有効化しない。
- Route A fallback / old route fallback を Route 0506 成功として数えない。
- threshold relaxation、prompt accretion、repair_acceptance 変更、追加 repair loop で解決しない。
- `1 issue = 1 narrow hypothesis = 1 owner scope` を維持する。
- blocked したら `C:\Users\横山裕明\Desktop\0506` 側を正とし、notecode 側の bridge / adapter / schema / source packet 接続 blocker を修正する。
- 修正は小分けにする。1 回の修正で複数 owner に広げない。
- 自己修正は最大 5 回。5 回目の blocked / error 後は停止する。

## Latest Known Blocker

Latest notecode artifact:

- `C:\tetie\notecode\logs\route_0506_audit_high_editor_fire_20260509\blocked.json`

Known observed blocker:

- `model=gpt-5.4-mini`
- `reasoning_effort=high`
- `api_send=true`
- Source hash matched Route A saved source:
  - `ca2055f4b02a73c3ad94dce625cc85be3df06d848ba7aea9321e6d1bae33c1bb`
- OpenAI structured schema validation failed because `confirmed_facts[12].supporting_fact_ids` had duplicate values:
  - `['F1008', 'F1009', 'F1003', 'F1008', 'F1009', 'F1013', 'F111', 'F127']`
- Stage output reached only:
  - `source_cards.json`
  - `source_packets.json`
- Draft / editor stages did not run in that blocked attempt.

First fix target:

- Compare `C:\Users\横山裕明\Desktop\0506` behavior and notecode behavior around supporting fact IDs.
- If Desktop 0506 deduplicates or tolerates duplicate supporting facts, port only the minimum equivalent behavior into notecode bridge / adapter / schema boundary.
- Do not solve this by prompt wording, threshold relaxation, or repair loop addition.

## Recent Fix Already Applied

The editor-stage two-step firing issue was already fixed in the previous window.

Changed files:

- `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
- `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
- `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`

Expected behavior:

- opening / global / style / structural editor stages call the API first.
- If the editor output collapses into meta-review, loses required headings, or becomes invalid, Route 0506 fails open to the previous article for that stage.
- The guard must not skip editor API calls simply because `previous_article` exists.

Previously passed checks:

```powershell
.\.venv\Scripts\python.exe -m py_compile note\route_0506_structured_blog_adapter.py note\route_0506_stage_output_guard.py note\tests\test_route_0506_structured_blog_adapter.py
.\.venv\Scripts\python.exe -m pytest -q note\tests\test_route_0506_structured_blog_adapter.py note\tests\test_route_0506_ui_bridge.py note\tests\test_route_0506_saved_source_cli_validation.py
```

Result:

- `30 passed`

## AB Test Execution Plan

### Step 1: Inventory records before execution

Create an inventory artifact before any API call:

```text
C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\inventory.json
```

Inventory fields:

- available saved Route A artifact per article type
- available saved source contract / source_documents per article type
- Route 0506 mapped genre per article type
- Desktop 0506 reference artifacts consulted
- source hash
- whether Route A baseline exists
- whether Route 0506 can run without URL refetch
- estimated API call count

Target article types:

- `company_introduction`
- `product_introduction`
- `announcement`
- `case_study`
- `comparative_review`
- `explanatory_article`
- `daily_story`

If saved Route A artifact or saved source is missing for an article type, mark it as `source_needed` and do not regenerate Route A.

### Step 2: Execute the first blocked-case recovery

Before the full AB matrix, rerun or reproduce the latest blocked one-case as narrowly as possible.

If it blocks on duplicate `supporting_fact_ids`, fix only that owner.

After every code fix, run at minimum:

```powershell
.\.venv\Scripts\python.exe -m py_compile note\route_0506_structured_blog_adapter.py note\route_0506_stage_output_guard.py note\route_0506_ui_bridge.py note\route_0506_saved_source_cli_validation.py
.\.venv\Scripts\python.exe -m pytest -q note\tests\test_route_0506_structured_blog_adapter.py note\tests\test_route_0506_ui_bridge.py note\tests\test_route_0506_saved_source_cli_validation.py
```

Then rerun the exact same one-case. Do not move to the full AB test until the blocker is fixed or the 5-error stop rule is reached.

### Step 3: Blocked / error self-fix loop

Use this loop for any blocked / error during the one-case recovery or AB test.

For each blocked / error:

1. Increment `error_count`.
2. Save an attempt artifact:

```text
C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\blocked_attempt_XX\
```

Required files per attempt:

- `blocked.json`
- `trace_or_error.txt`
- `observed_stage_artifacts.json`
- `desktop_0506_reference_note.md`
- `hypothesis.md`
- `fix_summary.md`
- `test_result.txt`

3. Read the record and actual behavior:
   - latest notecode blocked artifact
   - stage artifacts
   - stack trace / validation error
   - corresponding Desktop 0506 docs / artifact behavior
4. State one narrow hypothesis.
5. Patch only the owner required for that hypothesis.
6. Run focused compile/tests.
7. Rerun the exact failed case.

Stop condition:

- If `error_count >= 5`, stop immediately.
- Do not start another fix.
- Do not continue to other article types.
- Write final blocked artifact.
- Update `C:\tetie\WORKLOG.md`.
- Final report decision must be `blocked`.

### Step 4: Run AB test after recovery

For each available article type:

- run Route 0506 OpenAI candidate 3 times
- use `model=gpt-5.4-mini`
- use `reasoning_effort=high`
- preserve saved source hash in every artifact
- do not refetch URLs
- do not regenerate Route A
- compare each Route 0506 output against the saved Route A artifact for the same article type

Suggested artifact root:

```text
C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\
```

Per-run artifact fields:

- `article_type`
- `route_0506_genre`
- `run_index`
- `source_hash`
- `route_a_artifact_path`
- `route_0506_output_path`
- `blocked`
- `blocked_reason`
- `api_send`
- `model`
- `reasoning_effort`
- `stage_artifacts`
- `editor_stage_fired`
- `fallback_stage_used`
- `title_visible`
- `body_visible`
- `toc_markdown_heading_ok`
- `source_grounding_ok`
- `meta_review_leak`
- `source_contract_leak`
- `naturalness_manual_note`
- `decision`

Allowed per-run decisions:

- `route_0506_better`
- `route_a_better`
- `tie`
- `blocked`
- `source_needed`

### Step 5: Summarize

Create:

```text
C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\compare_summary.json
C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\manual_review.md
```

Summary must include:

- article types attempted
- article types skipped as `source_needed`
- Route 0506 run count
- blocked / error count
- self-fix count
- whether 5-error stop rule was reached
- per article type 3-run stability
- Route A vs Route 0506 winner distribution
- editor-stage firing proof
- source hash match proof
- UI mapping collision check
- prompt bloat check
- module bloat check
- manual Japanese naturalness note
- final decision

Allowed final decisions:

- `continue_shadow`
- `reject`
- `blocked`

## Cost / Request Estimate

This is an API request-count estimate, not a reliable yen/dollar estimate. Current notecode artifacts do not consistently persist token usage.

Formula:

```text
api_calls_per_run ~= source_document_count + 7 + optional_targeted_rewriter
total_api_calls ~= available_article_type_count * 3 * api_calls_per_run
```

If all 7 article types are available and each has about 5 source documents:

```text
api_calls_per_run ~= 12 to 13
total_api_calls ~= 7 * 3 * 12 to 13 = 252 to 273 API calls
```

If only the 6 Route 0506 genre families are available:

```text
total_api_calls ~= 6 * 3 * 12 to 13 = 216 to 234 API calls
```

Print the actual estimated request count from `inventory.json` before running the full matrix. Do not stop for approval unless the operator explicitly asks for a cost gate.

## Final Report Contract

Report in this exact shape:

```text
decision: continue_shadow | reject | blocked
artifact_root:
article_types_attempted:
article_types_source_needed:
total_route_0506_runs:
total_blocked_or_errors:
self_fix_attempts:
five_error_stop_reached: true | false
latest_blocked_reason:
editor_stage_fired: true | false
route_a_regenerated: false
url_refetched: false
source_hash_policy:
desktop_0506_reference_used:
prompt_bloat: none | found
module_bloat: none | found
tests:
worklog_updated: true | false
manual_japanese_naturalness_note:
next_one_owner:
```

If final decision is `blocked`, include:

- smallest reproducible case
- exact failed owner
- why Desktop 0506 behavior indicates notecode-side blocker
- what was attempted in each of the 5 self-fix attempts
- why the window stopped
