# visible_output_integrity_2026-04-06 PROGRESS

## Current Goal

- pre-2026-04-02 records を archive-only に切り替えた上で、visible red symptom を narrow owner で止める implementation package を固定する

## Current Status

- Package status: active
- Current phase: 01 completed
- Status: phase 01 completed + subtraction investigation completed
- Hypothesis:
  - title corruption は `output_formatter.py` owner、warning-only success は `output_guard.py` owner に閉じる
- Owner scope:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- Attempts used: 1/3
- Next phase:
  - 02 Output Guard Visible Boundary Hardening（fresh artifact rerun / subtractive rerun で必要と判明した場合のみ）

## Baseline

- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current visible artifact baseline:
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- archive snapshot:
  - `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\`
- completed reference package:
  - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\`
  - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
- frozen reference package:
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`
- keep decision inherited from frozen reference:
  - `hybrid target architecture`
  - repo-level interpretation: `keep core, refactor boundaries`
- package theme:
  - `keep core, enforce visible output integrity`

## Current Evidence

- latest visible red title:
  - `生成AI投資では、まずROIの説明が求められるをそろえて迷いを減らす実務の見方`
- latest attempt id:
  - `gen-61a76943`
- latest visible metrics:
  - `must_cover_reflection_rate=0.6667`
  - `source_grounding_reflection_ratio=0.8333`
  - `ending_bucket_monotony_score=0.8182`
  - `flat_zone_count=6`
  - `soft_warning_count=1`
- current interpretation:
  - body は yellow だが title は red
  - warning は出ているが blocked ではなく success render されている

## Complexity Assessment

- owner file size:
  - `output_formatter.py`: `1074 lines`
  - `output_guard.py`: `692 lines`
  - `current_mainline_runner.py`: `960 lines`
  - `note_writer_app.py`: `7140 lines`
- primary concern:
  - title fallback が malformed visible title を作ること
  - output guard が selected visible red symptom を soft warning に留めること
  - pre-2026-04-02 records が implementation judgment に混ざること
- keep untouched first:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`

## Blocked Hypotheses

- prompt-only strengthening から先に始めること
- planner / generator core を初手で触ること
- pre-2026-04-02 packages を current read order に戻すこと
- title corruption を warning-only success のまま観測で済ませること
- output guard の selected visible symptom を observe-only で keep すること

## Phase Ledger

| Phase | Status | Hypothesis | Owner scope | Attempts | Evidence | Next phase |
|------|--------|------------|-------------|----------|----------|------------|
| 00 Archive Boundary And Current Snapshot Freeze | completed | pre-2026-04-02 records を archive-only に切れば、implementation judgment が current package と latest artifact に閉じる | package docs + archive snapshot only | 0/3 | archive snapshot README/manifest を作成し、current package を visible-output package に固定 | 01 |
| 01 Output Formatter Title Integrity Trim | completed | explanatory title fallback を trim すれば visible red title を narrow owner で止められる | `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py` | 1/3 | malformed title reproduction test を追加し、heading seed の predicate tail を narrow trim して same malformed shape を再現しないことを固定 | 02 |
| 02 Output Guard Visible Boundary Hardening | pending | selected visible red symptom を blocking reason に寄せれば warning-only success が減る | `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py` | 0/3 | output guard は final artifact を見るが title integrity / visible monotony を hard boundary にしていない | 03 |
| 03 UI Warning Surface Trim | conditional | guard decision と UI success projection を揃えれば warning-only success render path を閉じられる | `C:\tetie\notecode\note\note_writer_app.py` | 0/3 | Phase 02 後も symptom が render される場合だけ着手 | complete |

## Phase 00 Evidence

- status:
  - completed
- evidence:
  - `pre_2026-04-02_work_records_2026-04-06` archive snapshot を作成
  - current package read order から pre-2026-04-02 records を外す方針を固定
  - latest visible artifact baseline と current success path を docs に固定
- tests:
  - docs only
- rollback note:
  - なし

## Package Outcome

- verdict:
  - keep
- next action:
  - Phase 01 は completed とし、fresh artifact rerun なしで Phase 02 へは進まない
- entry note:
  - archive snapshot は reference only
  - completed / frozen reference package は reopen しない

## Phase 01 Evidence

- status:
  - completed
- touched owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- focused test:
  - `test_st08b2aa_explanatory_warm_heading_seed_trims_stitched_predicate_title`
- keep diff:
  - heading seed が `Xでは、まずYが求められる` 形の explanatory fallback を compact に変換する narrow helper を追加
  - warm tone shaping で `生成AI投資では、まずROIの説明が求められるをそろえて...` の stitched title が再現しないことを固定
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st08b2aa or st08b2a or st16a or st16aa" -q`
    - `4 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q`
    - `214 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_runner.py -q`
    - `60 passed`
- rollback note:
  - owner-local diff は `output_formatter.py` と focused title test に閉じている
- fresh rerun evidence:
  - artifact:
    - `C:\tetie\notecode\logs\codex_phase01_rerun_result_2026-04-07.json`
  - result:
    - `success=true`
    - `reason_code=OK`
    - title は `生成AIのROIが問われる背景をそろえて迷いを減らす実務の見方`
    - malformed title `生成AI投資では、まずROIの説明が求められるをそろえて...` は再現しなかった
    - `output_guard.blocked=false`
    - `soft_warning_count=2`
    - `ending_bucket_monotony_score=0.2973`
    - `must_cover_reflection_ratio=0.6667`

## 2026-04-07 Subtractive Investigation

- scope:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
  - `C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py`
- method:
  - baseline 3 genres（explanatory / branding / announcement）を live 生成
  - `format_output()` 前後 capture で owner を切り分け
  - cumulative 3 cycles の引き算 diff を当て、各 cycle ごとに同じ 3 genres を live rerun
- cycle diff:
  - cycle 1: `_extract_headings()` から `目次` を除外し、body に markdown TOC がある場合は formatter summary/toc を追加しない
  - cycle 2: explanatory では formatter scaffold を止め、clean existing title を優先
  - cycle 3: announcement では synthetic lead を追加しない
  - cycle 4: announcement では source-grounded fallback を使い、duplicate must-cover sentence と壊れた timing sentence だけを section-local に差し替える
- artifacts:
  - baseline: `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-three-article-eval-20260407\`
  - cycle 1: `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-three-cycle1-20260407\`
  - cycle 2: `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-three-cycle2-20260407\`
  - cycle 3: `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-three-cycle3-20260407\`
  - probes: `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-three-article-probe-20260407\`, `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-cycle3-probe-20260407\`
- conclusion:
  - explanatory の visible title / toc surface は `output_formatter.py` owner と確定
  - branding の sentence break は formatter owner と断定できず、cycle 2/3 rerun では再現しなかった
  - announcement の fixed lead は formatter の足し算で、body owner ではなかった
  - announcement の残る topic-echo / timing drift は `section_generation_body` で既に発生しており、current keep は `newalgorithm_pipeline/pipeline.py` の announcement postprocess で narrow fallback backfill する形
- verification:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q`
    - `217 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
    - `60 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
    - `278 passed`

## Tomorrow Session Plan

- target date:
  - `2026-04-07`
- session objective:
  - `Phase 01 Output Formatter Title Integrity Trim` を owner-local に完了させるか、rollback 可能な narrow diff で停止判断まで持っていく
- first read:
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md`
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\TASK.md`
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md`
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\ROLLBACK.md`
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\EXECUTION_PROMPT.md`
  - `C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-07.md`
- first artifact check:
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
  - attempt id `gen-61a76943`
- execution order:
  - latest malformed title の reproduction path を `output_formatter.py` owner の focused test で固定する
  - `_resolve_output_title()` / `_compact_title()` / weak-title fallback chain を確認する
  - stitched explanatory fallback を trim し、empty / weak title path を fail-closed か compact seed に寄せる
  - owner-local test と shared checks を実行する
  - Phase 01 が通ったら docs を更新して停止する
- do-not:
  - `output_guard.py` を同時に触らない
  - `note_writer_app.py` を同時に触らない
  - prompt accretion を足さない
  - 英語の AI-ism 辞書をそのまま移植しない
  - Phase 01 完了前に Phase 02 を開始しない
- stop condition:
  - malformed title の再現固定ができない
  - current success path regression が出る
  - rollback が owner-local diff に閉じない
  - `output_guard.py` を触らないと前進しないと判明する
- success condition:
  - latest malformed title shape が focused test で再現しなくなる
  - shared checks が通る
  - rollback 手順が `output_formatter.py` owner diff に閉じる
