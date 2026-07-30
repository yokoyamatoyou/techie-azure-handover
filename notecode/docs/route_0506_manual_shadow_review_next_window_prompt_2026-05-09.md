# Route 0506 Manual Shadow Review Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 manual shadow review ウインドウです。

実施範囲は、最新 OpenAI candidate の article adequacy / source-faithfulness / 短さの扱いだけです。Route A replacement / adoption 判断、追加生成、コード修正はこの window の目的ではありません。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. `C:\tetie\notecode\docs\route_0506_instruction_window_migration_prompt_2026-05-09.md`
5. `C:\tetie\notecode\docs\route_0506_sentence_too_long_next_window_prompt_2026-05-09.md`
6. `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_summary.json`
7. `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\evidence.md`
8. `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\validation_summary.json`
9. `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\source_snapshot.json`
10. `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\input_contract.json`
11. `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\route_0506\latest_generation_output.md`
12. `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\route_0506\latest_generation_quality_report.json`
13. Prior comparison references:
    - `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\fix_attempt_01\rerun_summary.json`
    - `C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\compare_summary.json`
    - `C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\manual_review.md`
14. `C:\tetie\notecode\ALGORITHM.md`
    - `## 4. Single-Pass Generation`
    - `## 5. Repair Algorithm`
    - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current State

- decision: `fixed_continue_shadow`
- Route 0506 is not adopted over Route A.
- Route A remains frozen.
- Source handoff owner is complete.
- `sentence_too_long` owner is complete.
- Latest OpenAI candidate:
  - artifact: `C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\`
  - `api_send=true`
  - `model=gpt-5.4-mini`
  - `reasoning_effort=high`
  - `quality_pass=true`
  - `score=100`
  - `issues=[]`
  - `max_sentence_length=54`
  - `body_char_count=652`
- Manual note from previous window:
  - `sentence_too_long` は解消。
  - 記事方向は company/service introduction に戻っている。
  - 652 chars と短いため Route A adoption 判断はまだしない。

## One Owner

OpenAI candidate の manual shadow review。

見る対象は次の 3 点だけです。

- article adequacy: 会社紹介記事として十分か、短すぎて読者価値が落ちていないか
- source-faithfulness: source にない claim / 過度な言い換え / source contract leak がないか
- shortness handling: 652 chars を acceptable shadow / continue_shadow / reject のどれで扱うべきか

## Hard Boundaries

- Do not regenerate Route A.
- Do not refetch URLs.
- Do not call the OpenAI API.
- Do not run a new Route 0506 generation.
- Do not run a full AB matrix.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Do not change product code.
- Do not add prompt tuning.
- Do not reopen `sentence_too_long`.
- Do not reopen source handoff.
- Do not reopen Desktop 0506 algorithm.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Review Inputs

Latest candidate:

```text
C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\route_0506\latest_generation_output.md
```

Candidate quality report:

```text
C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\route_0506\latest_generation_quality_report.json
```

Source / contract:

```text
C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\source_snapshot.json
C:\tetie\notecode\logs\route_0506_sentence_too_long_fix_20260509\fix_attempt_01\rerun_openai_onecase_after_markdown_quality_boundary\input_contract.json
```

Prior Route A / Route 0506 comparison:

```text
C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\compare_summary.json
C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\manual_review.md
```

## Required Artifact

Create:

```text
C:\tetie\notecode\logs\route_0506_manual_shadow_review_20260509\manual_review.md
C:\tetie\notecode\logs\route_0506_manual_shadow_review_20260509\review_summary.json
```

`manual_review.md` must include:

- candidate article path
- source / contract paths read
- article adequacy note
- source-faithfulness note
- shortness handling note
- Japanese naturalness note
- explicit non-adoption note
- next one owner

`review_summary.json` must include:

- `decision`: `continue_shadow | reject | blocked`
- `artifact_root`
- `candidate_artifact`
- `article_adequacy`: `acceptable | thin | blocked`
- `source_faithfulness`: `pass | concern | blocked`
- `shortness_handling`: `acceptable_shadow | too_thin | blocked`
- `route_a_regenerated`: `false`
- `url_refetched`: `false`
- `api_send`: `false`
- `product_code_changed`: `false`
- `threshold_relaxed`: `false`
- `repair_acceptance_relaxed`: `false`
- `prompt_bloat`: `none | found`
- `module_bloat`: `none | found`
- `manual_japanese_naturalness_note`
- `next_one_owner`

## Decision Rules

Use `continue_shadow` if:

- the article is short but coherent as a shadow candidate
- no source-faithfulness concern is found
- the next risk is broader stability or repeatability, not this one article

Use `reject` if:

- 652 chars makes the article too thin for the company-introduction purpose
- important source-backed elements are missing enough that this candidate should not continue
- source-faithfulness concern is material

Use `blocked` only if:

- required artifacts are missing
- source / contract cannot be read
- the candidate cannot be reviewed without rerunning generation

## Final Report Contract

Report in this exact shape:

```text
decision: continue_shadow | reject | blocked
artifact_root:
candidate_artifact:
article_adequacy:
source_faithfulness:
shortness_handling:
route_a_regenerated: false
url_refetched: false
api_send: false
product_code_changed: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
manual_japanese_naturalness_note:
next_one_owner:
WORKLOG_update_needed: true | false
```

If `WORKLOG_update_needed=true`, update only the Route 0506 current state / next owner pointer. Do not rewrite unrelated history.
