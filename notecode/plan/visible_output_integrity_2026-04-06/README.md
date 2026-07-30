# visible_output_integrity_2026-04-06 README

## Objective

- current success path を壊さず、user-visible な赤症状を `warning-only success` のまま通さない narrow package を固定する
- pre-2026-04-02 work records を archive-only surface に切り替え、implementation 判断を current package と latest artifact に閉じる
- `output_formatter.py` と `output_guard.py` の境界で、何を keep し、何を fail-closed / trim するかを docs-first に先固定する

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md`
4. `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\TASK.md`
5. `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md`
6. `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\ROLLBACK.md`
7. `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\EXECUTION_PROMPT.md`
8. `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md`
9. `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md`
10. `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md`
11. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md`
12. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md`
13. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md`
14. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md`
15. `C:\tetie\notecode\ALGORITHM.md`
16. `C:\tetie\WORKLOG.md`

## Source Of Truth

- current runtime baseline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current visible artifact baseline:
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- first owner residual:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- second owner residual:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
- conditional owner residual:
  - `C:\tetie\notecode\note\note_writer_app.py`
- current planning package:
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\`
- archive snapshot:
  - `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\`
- completed / frozen reference:
  - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\`
  - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`

## Current Decision

- verdict:
  - `new package required`
- repo decision:
  - `keep core, refactor boundaries`
- package theme:
  - `keep core, enforce visible output integrity`
- first owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- second owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
- conditional owner:
  - `C:\tetie\notecode\note\note_writer_app.py`
- not adopted:
  - `prompt-only strengthening first`
  - `multi-stage generator redesign first`
  - `reopen pre-2026-04-02 packages`

## Package State

- package status:
  - active
- package mode:
  - phase 01 completed
- current phase:
  - 01 completed
- phase 00 status:
  - completed
- phase 01 status:
  - completed
- subtraction investigation status:
  - completed
- phase 02 status:
  - pending
- phase 03 status:
  - conditional
- next action:
  - fresh artifact rerun と 3-cycle subtractive rerun の両方で `output_formatter.py` owner の visible accretion を削ったため、Phase 02 は開始しない。新しい visible red symptom が残った場合だけ次 phase を再評価する

## Why

- latest visible artifact では title が `生成AI投資では、まずROIの説明が求められるをそろえて迷いを減らす実務の見方` になっており、user-visible red symptom のまま成功扱いで残っている
- same artifact では `must_cover_reflection_rate=0.6667`、`ending_bucket_monotony_score=0.8182`、`flat_zone_count=6` が残り、warning-only success のまま render されている
- `output_guard.py` は final artifact を見ているが、title integrity を hard boundary にしておらず、soft warning は UI success path へ流れている
- pre-2026-04-02 work records が current reading surface に残ると、deletion-first の narrow implementation 判断がぶれやすい

## Complexity Snapshot

- owner file size:
  - `output_formatter.py`: `1074 lines`
  - `output_guard.py`: `692 lines`
  - `current_mainline_runner.py`: `960 lines`
  - `note_writer_app.py`: `7140 lines`
- primary concern:
  - title stitching / title fallback が visible red symptom を作ること
  - output guard が warning-only success を残したまま user-visible output を通すこと
  - current planning surface に pre-2026-04-02 records が混ざること
- keep untouched first:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\discourse_planner.py`

## Simplification Direction

### Keep

- current success path の順序
- current mainline owner split
- single-pass body generation 本体
- output guard entrypoint 自体

### Thin

- `output_formatter.py` の stitched explanatory title fallback
- `output_formatter.py` の summary / toc / synthetic lead など visible scaffold accretion
- `output_guard.py` の warning-only success surface
- current read order へ pre-2026-04-02 records を直接持ち込む導線

### Remove As Default Assumption

- visible red symptom でも soft warning なら success でよい前提
- title corruption は body quality と切り離して放置してよい前提
- AI-feel は prompt accretion を足せば先に救える前提
- pre-2026-04-02 records を current planning surface に残したまま narrow implementation ができる前提

## Non-Goals

- `simple_note_pipeline/pipeline.py` の本文生成骨格を置換すること
- experimental prompt stack を本 package の primary task に戻すこと
- completed / frozen reference package を reopen すること
- pre-2026-04-02 work records の runtime file move を始めること
- prompt accretion / module accretion で visible red symptom を隠すこと
