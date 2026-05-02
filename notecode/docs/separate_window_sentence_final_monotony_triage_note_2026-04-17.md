# separate window sentence final monotony triage note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の docs-only triage note である
- current source-of-truth は更新しない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ入力
- current symptom summary
- detector / telemetry / repair scope split
- owner candidate shortlist
- first production owner candidate
- why not `reference realization policy`
- decision

## 読んだ入力

- rule files
- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\WORKLOG.md`
- separate docs
- `C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_instruction_window_relocation_prompt_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_instruction_first_request_sentence_final_monotony_2026-04-17.md`
- artifacts
- `C:\tetie\notecode\logs\latest_generation_output.txt`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\latest_generation_quality_report.json`

## Current Symptom Summary

- current package docs に残っている historical symptom summary は、
  `ending_bucket_max_run = 29` /
  `ending_bucket_monotony_score = 1.0` /
  `repair_applied = false` /
  `patch_path_used = false` /
  `patch_path_refusal_reason = compact_plan_scope_ineligible`
  である
- latest artifact は `2026-04-15 00:25:07` の `gen-4692e32c` で、対象は `explanatory_article`
- latest artifact の body-generation telemetry は以下だった
- `writer_of_record = simple_note_pipeline`
- `route_branch = single_pass_default`
- `section_path_used = false`
- `style_profile_source = newalgorithm_pipeline.default_style_profile`
- `ending_bucket_max_run = 27`
- `ending_bucket_monotony_score = 0.675`
- `repair_trigger_score = 0.62`
- `flagged_issue_types = ["ending_bucket_monotony"]`
- `patch_path_used = true`
- `scope_rejection_reason = flagged_scope_drift`
- `repair_applied = false`
- `runtime_reason_code = SYS_QUALITY_WARNINGS_UNRESOLVED`
- したがって current live-like state は
  `patch path unavailable` ではなく
  `patch path attempted, but acceptance/scope rejection kept repair unapplied`
  と読むのが正確である

## Detector / Telemetry / Repair Scope Split

### Detector Problem

- first blocker ではない
- `note\simple_note_pipeline\quality_guard.py` には `ending_bucket_counts / ending_bucket_max_run / ending_bucket_monotony_score` の計測があり、`ending:bucket_monotony` soft warning も出る
- latest artifact でも `flagged_issue_types = ["ending_bucket_monotony"]` まで到達しているため、`sentence-final monotony を検知できていない` 状態ではない

### Telemetry Visibility Problem

- first blocker ではない
- latest artifact には
  `pipeline_check.quality_metrics.*` /
  `pipeline_check.body_generation.*` /
  `repair_call.*` /
  `scope_rejection_reason`
  が残っている
- そのため `detected but not repaired` の停止点は docs-only でも追える

### Repair Trigger Problem

- secondary
- `repair_trigger_score = 0.62` で `repair_required` に入っているため、current latest artifact では trigger 自体は発火している
- `quality_guard.py` 側の threshold 見直しは second candidate にはなりうるが、first candidate ではない
- 例外として、future case で `ending_bucket_monotony` が見えても `repair_required` に届かない run が続くなら、その時だけ trigger owner を reopen する

### Repair Acceptance / Scope Problem

- main blocker
- latest artifact では `patch_path_used = true` にもかかわらず `repair_applied = false`
- `note\simple_note_pipeline\pipeline.py` の optional repair acceptance は
  `scope_preserved` /
  `effective_scope_preserved` /
  `ending_monotony_improved`
  を見て採否を決めている
- しかも `local_monotony_scope_preserved` の fallback は
  `branding + company_introduction + ending_bucket_monotony`
  に閉じている
- そのため current latest artifact の `explanatory_article` では、
  monotony patch が試行されても local monotony acceptance lane に入れず、`flagged_scope_drift` で落ちる構図が最有力である

### Prompt Surface Problem

- reserve だが first blocker ではない
- `note\simple_note_pipeline\prompt_builder.py` は generation prompt に
  `同じ文末を3回以上続けない`
  をすでに入れており、repair prompt にも `文末単調を局所補修する` を含めている
- したがって initial generation / repair prompt の文面だけを先に強めるのは、acceptance failure の説明にならず prompt accretion 寄りになる

## Owner Candidate Shortlist

### 1. `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

- reason
- latest artifact の停止点が
  `patch_path_used = true`
  から
  `repair_applied = false`
  への acceptance lane にある
- owner scope
- optional single repair の patch-path activation
- flagged-span based repair acceptance
- monotony-local scope preservation fallback
- acceptance telemetry
- rollback unit
- `_run_optional_repair()` とその local acceptance helper 群だけで 1 file rollback に閉じられる

### 2. `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`

- reason
- ending bucket detector と `repair_trigger_score` はここが owner
- latest artifact では first blocker ではないが、future implementation 後も `repair_required` に届かない monotony case が残るなら second owner になる
- owner scope
- `ending_bucket_*` metric
- `ending:bucket_monotony` soft warning
- `repair_trigger_score`
- `repair_instructions`
- rollback unit
- detector / trigger diff だけを 1 file rollback に閉じられる

## First Production Owner Candidate

- first production owner candidate は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- narrow hypothesis は次のとおり
- current problem は detector 不足ではなく、`sentence-final monotony` repair が patch path まで進んだあと acceptance で落ちている
- したがって first step は `quality_guard.py` の threshold を先にいじることではなく、
  `pipeline.py` 側で `ending_bucket_monotony` の local acceptance lane を
  `branding/company_introduction` 専用から
  `single-pass + optional single repair 1回`
  の汎用 sentence-final patch に narrow 拡張できるかを検証することになる
- guard 条件は維持する
- title / lead / hashtags は固定
- heading order は固定
- must-cover / prompt anchor / section focus は回帰させない
- change scope は flagged span とその近傍に閉じる
- rollback も `pipeline.py` 単独で戻せる

## Why Not `Reference Realization Policy`

- current live blocker は referential continuity ではなく、artifact 上ですでに見えている `ending_bucket_monotony -> patch_path_used -> scope rejection` の連鎖である
- `reference realization policy` を main line に戻すと、zero pronoun / topic continuity / proper noun repetition まで論点が広がり、sentence-final monotony の責任 owner がぼける
- 今回は already-detected symptom を `single-pass + optional single repair 1回` の内側で詰められる
- そのため `reference realization policy` は separate evidence line のまま keep し、main line へ戻さない

## Decision

- `GO_TO_IMPLEMENT`
- first implementation line
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- first implementation objective
- `sentence-final monotony` repair の acceptance / scope lane を narrow に再設計し、`patch_path_used = true` なのに `repair_applied = false` で止まる current failure を 1 file owner で詰める
- not first
- `quality_guard.py` threshold retune
- `prompt_builder.py` での追加 prompt accretion
- `reference realization policy`
- `formatter-only polish`

