# Route 0506 / Route A 3x Compare Next Window Prompt

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Objective

`C:\Users\横山裕明\Desktop\0506` の current algorithm をお手本として、`C:\tetie\notecode` の Route 0506 が Route A saved artifact / saved source と同じ入力で動作するかを比較する。

各 article type を原則 3 回ずつ生成し、Route A frozen saved artifact と Route 0506 OpenAI candidate を比較する。途中で blocked した場合は、現在の Route 0506 algorithm が正しい前提で、notecode 側の bridge / adapter / schema / source packet 接続を狭く修正する。

## Required Read Order

1. `C:\tetie\notecode\AGENTS.md`
2. `C:\tetie\WORKLOG.md`
   - 2026-05-09 の Route 0506 entries を確認する
3. `C:\tetie\notecode\logs\route_0506_audit_high_editor_fire_20260509\blocked.json`
4. `C:\tetie\notecode\logs\route_0506_audit_high_editor_fire_20260509\validation_summary.json`
5. `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
6. `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
7. `C:\tetie\notecode\note\route_0506_ui_bridge.py`
8. `C:\tetie\notecode\note\route_0506_saved_source_cli_validation.py`
9. `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
10. `C:\Users\横山裕明\Desktop\0506\WORKLOG.md`
11. `C:\Users\横山裕明\Desktop\0506\PROGRESS.md`
12. `C:\Users\横山裕明\Desktop\0506\artifacts\runs\`

## Hard Rules

- Route A は frozen。Route A を再生成しない。
- Route A compare は saved artifact / saved source only。
- URL refetch しない。
- local file locator / external file ingestion を有効化しない。
- Route A fallback / old route fallback を Route 0506 成功として数えない。
- threshold relaxation、prompt accretion、repair_acceptance 変更、追加 repair loop で解決しない。
- `1 issue = 1 narrow hypothesis = 1 owner scope` を維持する。
- blocked したら `C:\Users\横山裕明\Desktop\0506` 側を正とし、notecode 側の接続 blocker を修正する。
- 同じ blocker の修正試行は最大 3 回。無理なら blocked artifact と WORKLOG を残して停止する。

## Latest Known Blocker

Latest artifact:

- `C:\tetie\notecode\logs\route_0506_audit_high_editor_fire_20260509\blocked.json`

Observed blocker:

- `model=gpt-5.4-mini`
- `reasoning_effort=high`
- `api_send=true`
- Source hash matched Route A saved source:
  - `ca2055f4b02a73c3ad94dce625cc85be3df06d848ba7aea9321e6d1bae33c1bb`
- Structured schema validation failed because `confirmed_facts[12].supporting_fact_ids` had duplicate values:
  - `['F1008', 'F1009', 'F1003', 'F1008', 'F1009', 'F1013', 'F111', 'F127']`
- Stage output reached only:
  - `source_cards.json`
  - `source_packets.json`
- Draft / editor stages did not run in that blocked attempt.

First narrow hypothesis:

- Duplicate `supporting_fact_ids` should be normalized or prevented at the notecode bridge / schema adapter boundary before structured output validation fails.
- Confirm how `C:\Users\横山裕明\Desktop\0506` handles duplicate supporting facts. Port only the minimum compatible behavior into notecode.

## Recent Fix Already Applied

The editor-stage two-step firing issue was fixed before this handoff.

Changed files:

- `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
- `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
- `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`

Behavior after fix:

- opening / global / style / structural editor stages call the API first.
- If the editor output collapses into meta-review, loses required headings, or becomes invalid, Route 0506 fails open to the previous article for that stage.
- The guard no longer skips editor API calls simply because `previous_article` exists.

Verification already passed:

```powershell
.\.venv\Scripts\python.exe -m py_compile note\route_0506_structured_blog_adapter.py note\route_0506_stage_output_guard.py note\tests\test_route_0506_structured_blog_adapter.py
.\.venv\Scripts\python.exe -m pytest -q note\tests\test_route_0506_structured_blog_adapter.py note\tests\test_route_0506_ui_bridge.py note\tests\test_route_0506_saved_source_cli_validation.py
```

Result:

- `30 passed`

## Work Plan

### Step 1: Inventory

Create a run inventory before any API call:

- available saved Route A artifacts per article type
- available saved source contract / source_documents per article type
- Route 0506 mapped genre per article type
- whether Route A baseline exists
- whether Route 0506 can run without URL refetch

Target article types:

- `company_introduction`
- `product_introduction`
- `announcement`
- `case_study`
- `comparative_review`
- `explanatory_article`
- `daily_story`

If a saved Route A artifact or saved source is missing for an article type, mark that type as `source_needed` and do not regenerate Route A.

### Step 2: Fix the latest blocker first

Before the 3x compare, rerun the latest blocked one-case if needed and fix only the duplicate `supporting_fact_ids` schema blocker.

Required checks after the fix:

```powershell
.\.venv\Scripts\python.exe -m py_compile note\route_0506_structured_blog_adapter.py note\route_0506_stage_output_guard.py
.\.venv\Scripts\python.exe -m pytest -q note\tests\test_route_0506_structured_blog_adapter.py note\tests\test_route_0506_ui_bridge.py note\tests\test_route_0506_saved_source_cli_validation.py
```

Do not start multi-article generation until the duplicate-ID blocker is either fixed or explicitly classified as blocked with evidence.

### Step 3: Generate 3x per available article type

For each available article type:

- run Route 0506 OpenAI candidate 3 times
- use `model=gpt-5.4-mini`
- use `reasoning_effort=high`
- preserve saved source hash in every artifact
- do not refetch URLs
- do not run Route A generation
- compare each Route 0506 output against the saved Route A artifact for the same article type

Suggested artifact root:

```text
C:\tetie\notecode\logs\route_0506_route_a_3x_compare_20260509\
```

Suggested per-run fields:

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

Allowed decisions:

- `route_0506_better`
- `route_a_better`
- `tie`
- `blocked`
- `source_needed`

### Step 4: Compare and summarize

Create:

```text
C:\tetie\notecode\logs\route_0506_route_a_3x_compare_20260509\compare_summary.json
C:\tetie\notecode\logs\route_0506_route_a_3x_compare_20260509\manual_review.md
```

Summary must include:

- per article type 3-run stability
- Route A vs Route 0506 winner distribution
- blocked count and exact blocked causes
- editor-stage firing proof
- source hash match proof
- UI mapping collision check
- prompt/module bloat check
- whether the result supports `continue_shadow`, `reject`, or `blocked`

## Cost Estimate

This is a request-count estimate, not a reliable yen/dollar estimate. The current notecode artifacts do not consistently persist actual token usage, so exact cost requires token usage capture or provider billing data.

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

Before running the full matrix, print the estimated call count from the actual inventory and ask for continuation only if the next-window operator wants a cost gate.

## Final Report Contract

Report in this exact shape:

```text
decision: continue_shadow | reject | blocked
artifact_root:
article_types_attempted:
article_types_source_needed:
total_route_0506_runs:
total_blocked:
latest_blocked_reason:
editor_stage_fired: true | false
route_a_regenerated: false
url_refetched: false
source_hash_policy:
prompt_bloat: none | found
module_bloat: none | found
tests:
worklog_updated: true | false
manual_japanese_naturalness_note:
next_one_owner:
```

If blocked:

- Keep the current Route 0506 algorithm as correct by default.
- Name the notecode bridge / adapter / schema / source-packet owner.
- Leave a blocked artifact with the smallest reproducible case.
- Update `C:\tetie\WORKLOG.md`.
