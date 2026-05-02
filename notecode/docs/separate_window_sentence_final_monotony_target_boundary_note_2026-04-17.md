# separate window sentence final monotony target boundary note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の validation target boundary triage note である
- current source-of-truth は更新しない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- current read
- 実施範囲
- why A1/A2 missed the short-only promotion
- option A: short target first
- option B: adaptive scope reopen
- decision
- next prompt type
- non-updates

## Current Read

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_instruction_window_relocation_prompt_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_instruction_first_request_sentence_final_monotony_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_quality_guard_triage_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_quality_guard_triage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_quality_guard_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_note_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_quality_guard_20260417-170631\summary.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_quality_guard_20260417-170631\case_a1_latest_explanatory_monotony\result.json`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_quality_guard_20260417-170631\case_a2_saved_explanatory_monotony\result.json`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`

## 実施範囲

- `sentence-final pattern monotony cap + single repair` line の validation target boundary を docs / artifact だけで切り分けた
- A:
  - live validation target を `length_mode = short` explanatory case に差し替えるべきか
- B:
  - current production-like `adaptive` explanatory case まで trigger 対象を広げるべきか
- production code は変更していない
- AGENTS / WORKLOG / current planning package docs は変更していない

## Why A1/A2 Missed The Short-Only Promotion

- miss の主因は acceptance lane 再失敗ではなく、validation target と promotion boundary の不一致だった
- current `quality_guard.py` の explanatory monotony promotion は
  - `_is_explanatory_short_ending_bucket_monotony_candidate()`
  - `738-763`
 で `article_type == "explanatory_article"` かつ `length_mode == "short"` を必須にしている
- その promotion floor の反映も
  - `quality_guard.py`
  - `828-855`
 で short-only branch に閉じている
- しかし A1 / A2 は source artifact も current rerun も一貫して `adaptive` だった
  - `C:\tetie\notecode\logs\latest_generation_output.json`
    - `length_mode = "adaptive"`
    - `length_mode_requested = "adaptive"`
  - `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
    - `length_mode_key = "adaptive"`
    - `length_mode = "adaptive"`
  - `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_quality_guard_20260417-170631\case_a1_latest_explanatory_monotony\result.json`
    - `length_mode = "adaptive"`
    - `length_mode_requested = "adaptive"`
  - `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_quality_guard_20260417-170631\case_a2_saved_explanatory_monotony\result.json`
    - `length_mode = "adaptive"`
    - `length_mode_requested = "adaptive"`
- そのため A1 / A2 は short-only promotion branch に入らず、
  - `repair_required = false`
  - `skip_reason = repair_not_required`
 で止まった
- これは `short branch が live で壊れた` というより、
  `current live validation target が short branch を検証していない`
  と読むのが正確

## Option A: Short Target First

- 良い点:
  - current narrow hypothesis は short explanatory monotony-only に閉じている
  - rollback-first で最も安全
  - owner を reopen せず、まず line の局所有効性だけを証明できる
- 弱い点:
  - A1 / A2 の production-like explanatory target はどちらも `adaptive`
  - current baseline の explanatory problem を main line として説明するには弱い
  - short case だけの勝利では、今回の live revalidation mismatch を解消したことにならない
- read:
  - short target first は `line の unit proof` にはなる
  - ただし `main candidate の production relevance proof` にはなりにくい

## Option B: Adaptive Scope Reopen

- 良い点:
  - current production-like explanatory targets が実際に `adaptive` で動いている
  - A1 は current visible baseline
  - A2 は saved explanatory replay
  の両方が adaptive なので、main line の live validation を meaningful に戻せる
  - reopen owner は `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py` 1 file に閉じられる
- 注意点:
  - short-only より scope は広がる
  - ただし route default / planning default / repair architecture を触らず、
    `quality_guard.py` の explanatory monotony promotion boundary だけを再評価するなら narrow に保てる
- read:
  - 今回の mismatch は `target side を short に寄せれば解決` でもある
  - しかし current main concern が production-like explanatory baseline にある以上、
    adaptive を外したままでは next validation の意味が薄い

## Decision

- verdict:
  - `ADAPTIVE_SCOPE_REOPEN`

## Why This Decision

- current line の narrow implementation は short-only だったが、
  実際に keep / rollback を決めたい target は A1 / A2 の adaptive explanatory case で動いている
- latest baseline である
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  が adaptive である以上、short-only case の勝利だけでは `main candidate` の妥当性が弱い
- A1 / A2 が short-only promotion に乗らなかった理由は docs / artifacts だけで明確で、
  `quality_guard.py` owner 1 file で boundary reopen を検討できる
- よって次の main step は
  - `short synthetic target で先に証明し直す`
  ではなく
  - `adaptive explanatory も monotony trigger 対象に含めるべきか`
  を narrow に詰めるほうが current production-like problem に整合する

## Next Prompt Type

- next prompt:
  - `adaptive quality_guard follow-up prompt`
- recommended owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- question to narrow:
  - explanatory monotony promotion を `short` 専用のまま keep するのではなく、
    current production-like `adaptive` explanatory case にどう reopen するか
  - global threshold ではなく explanatory monotony boundary だけを 1 file owner で再設計できるか

## Non-Updates

- touched files:
  - `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_target_boundary_note_2026-04-17.md`
- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
