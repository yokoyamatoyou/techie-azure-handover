# Route 0506 Instruction Window Migration Prompt 2026-05-09

あなたは `C:\tetie\notecode` の Route 0506 / Route A 比較を管理する指示ウインドウです。実作業ウインドウではなく、状態確認、境界管理、次ウインドウ prompt 作成、完了報告の受け取りを担当してください。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`
5. Latest Route 0506 artifacts:
   - `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\fix_attempt_01\rerun_summary.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\desktop_vs_notecode_log_diff.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\desktop_vs_notecode_stage_diff.json`
6. Prior AB artifacts:
   - `C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\compare_summary.json`
   - `C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\manual_review.md`

## Current State

- decision: `fixed_continue_shadow`
- Route 0506 is not adopted over Route A.
- Route A remains frozen.
- Desktop reference:
  - `C:\Users\横山裕明\Desktop\0506`
- Latest artifact root:
  - `C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\`
- Latest fixed cause:
  - notecode bridge used 5 raw `source_documents` instead of typed company-introduction contract.
  - fixed by building Route 0506 source records from `_company_introduction_script_packet`, `_company_introduction_source_contract.slots`, and `source_grounding_items` when typed contract exists.
- After fix:
  - source changed from `5 raw pages` to `3 typed records`
  - source chars changed to `319, 524, 524`
  - article direction returned from broad real-estate selling guide to company/service introduction
- Still not solved:
  - OpenAI one-case completed with `gpt-5.4-mini high`, but QA failed: `false / 92 / sentence_too_long`

## Hard Boundaries

- Do not regenerate Route A.
- Do not refetch URLs.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Do not add broad prompt tuning.
- Do not add new repair loops.
- Do not reopen Desktop 0506 algorithm.
- Do not reopen source handoff unless a new artifact proves a new source-handoff blocker.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Next One Owner

The next execution window should focus only on:

```text
OpenAI candidate final article quality, specifically sentence_too_long.
```

The worker should inspect the exact QA issue, long sentence span, final article shape, and the smallest owner-local correction needed to prevent the long-sentence fail. The worker must not alter Route A, Desktop 0506, source handoff, thresholds, `repair_acceptance`, or broad prompts.

## Execution Window Policy

When creating the next work-window prompt:

- Tell the worker to read records first, then execute.
- If blocked, assume the current Route 0506 algorithm is directionally correct and look for a notecode-side blocker in adapter / bridge / schema / final output shaping.
- Allow up to 5 self-fix attempts.
- Stop after 5 errors and record:
  - artifact root
  - exact blocker
  - files touched
  - tests run
  - guardrail booleans
  - next owner
- Require a focused report with:
  - `decision: fixed_continue_shadow | continue_shadow | blocked | reject`
  - `artifact_root`
  - `source_handoff_reopened: false` unless proven otherwise
  - `route_a_regenerated: false`
  - `url_refetched: false`
  - `threshold_relaxed: false`
  - `repair_acceptance_relaxed: false`
  - `prompt_bloat`
  - `module_bloat`
  - `tests`
  - `manual_japanese_naturalness_note`
  - `next_one_owner`

## Suggested Next Work-Window Prompt

```text
C:\tetie\notecode で Route 0506 の final article quality だけを修正してください。

最初に必ず次を読んでください。
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\WORKLOG.md
4. C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\fix_attempt_01\rerun_summary.json
5. C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\desktop_vs_notecode_log_diff.md
6. C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\desktop_vs_notecode_stage_diff.json
7. C:\tetie\notecode\ALGORITHM.md の ## 4 / ## 5 / ## 12

現状:
- decision は fixed_continue_shadow。
- source handoff mismatch は修正済み。
- source は 5 raw pages から 3 typed records に変わり、chars は 319,524,524。
- article direction は broad real-estate selling guide から company/service introduction に戻った。
- OpenAI one-case は gpt-5.4-mini high で completed したが、QA が false / 92 / sentence_too_long のため採用不可。

今回の one owner:
- OpenAI candidate の sentence_too_long だけ。

禁止:
- Route A を再生成しない。
- URL refetch しない。
- Route A fallback / old route fallback を使わない。
- Desktop 0506 algorithm を触らない。
- source handoff を再度広げない。
- threshold を緩めない。
- repair_acceptance を緩めない。
- broad prompt tuning や新 repair loop を追加しない。

進め方:
- 記録を見る。
- 必要なら実行する。
- ブロック時は、現在の Route 0506 algorithm が正しい前提で、adapter / bridge / schema / final output shaping の挙動を見て修正する。
- 自己修正は最大5回。
- 5回エラーで停止し、artifact と blocker を記録する。

完了報告:
- decision
- artifact_root
- changed_files
- route_a_regenerated
- url_refetched
- source_handoff_reopened
- threshold_relaxed
- repair_acceptance_relaxed
- prompt_bloat
- module_bloat
- tests
- OpenAI rerun result
- manual_japanese_naturalness_note
- next_one_owner
```

## Instruction Window Closeout Rule

作業報告を受け取ったら、まず `decision` と guardrail booleans を確認してください。`sentence_too_long` 以外へ広がっている場合は、採用判断ではなく scope drift として止めてください。
