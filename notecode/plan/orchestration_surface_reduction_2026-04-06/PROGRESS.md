# orchestration_surface_reduction_2026-04-06 PROGRESS

## Current Goal

- simplification-first package を narrow completion まで閉じ、frozen architecture reference を reopen せずに owner-local surface reduction を完了させる

## Current Status

- Package status: completed
- Current phase: complete
- Status: completed
- Hypothesis:
  - `current_mainline_runner.py` を projection-only に寄せれば、package 全体の orchestration surface をさらに閉じられる
- Owner scope:
-  - none
- Attempts used: 1/3
- Next phase:
  - none

## Baseline

- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- frozen reference package:
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`
- keep decision inherited from frozen reference:
  - `hybrid target architecture`
  - repo-level interpretation: `keep core, refactor boundaries`
- package theme:
  - `keep core, reduce orchestration surface`

## Complexity Assessment

- owner file size:
  - `current_mainline_runner.py`: `929 lines`
  - `newalgorithm_pipeline/pipeline.py`: `2040 lines`
  - `simple_note_pipeline/pipeline.py`: `1349 lines`
  - `discourse_planner.py`: `900 lines`
  - `section_generator.py`: `909 lines`
- primary concern:
  - wrapper local branch density
  - repair local branch density
- keep untouched first:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\section_generator.py`

## Blocked Hypotheses

- `keep as-is` のまま wrapper / repair に局所 fix を足し続けること
- `replace architecture` を初手で採ること
- frozen architecture package を reopen して phase を継ぎ足すこと
- `newalgorithm_pipeline/pipeline.py` に route-local stabilizer を足して simplification と見なすこと
- `simple_note_pipeline/pipeline.py` に repair branch を足して quality を救うこと
- prompt accretion / telemetry accretion で complexity を隠すこと

## Phase Ledger

| Phase | Status | Hypothesis | Owner scope | Attempts | Evidence | Next phase |
|------|--------|------------|-------------|----------|----------|------------|
| 00 Package Freeze | completed | simplification boundary を docs に先固定すれば、next slice が再肥大化しない | package docs only | 0/3 | `README.md` / `TASK.md` / `PROGRESS.md` / `ROLLBACK.md` / `EXECUTION_PROMPT.md` に keep/thin/remove と source-of-truth を固定 | 01 |
| 01 Wrapper Surface Reduction | completed | wrapper の compatibility rebuild / stabilizer branching を 1 本の spine に寄せれば surface を減らせる | `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` | 1/3 | compatibility rebuild と final-body postprocess を owner-local helpers に集約し、main flow の article-type branching と editor-report merge 重複を削減。shared checks green | 02 |
| 02 Repair Surface Reduction | completed | repair activation / patch-path / acceptance を 1 本の accept rule に畳めば surface を減らせる | `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` | 1/3 | diagnostics refresh と optional repair を owner-local helpers に集約し、main flow の repair branch を削減。shared checks green | 03 |
| 03 Boundary Projection Trim | completed | Phase 01-02 後も残る duplication が runner owner に限られるなら projection-only に薄くできる | `C:\tetie\notecode\note\current_mainline_runner.py` | 1/3 | `input_contract normalize / pipeline call / boundary finalize` を owner-local helpers に集約し、runner main flow を projection spine に整理。shared checks green | complete |

## Phase 00 Evidence

- status:
  - completed
- evidence:
  - new package の objective / read order / source-of-truth priority / non-goals を固定
  - frozen architecture package は reopen 不可の reference として明記
  - complexity concern を file-size ベースで package に固定
- tests:
  - docs only
- rollback note:
  - なし

## Package Outcome

- verdict:
  - keep
- package completion:
  - `newalgorithm_pipeline/pipeline.py` / `simple_note_pipeline/pipeline.py` / `current_mainline_runner.py` の owner-local surface reduction を narrow completion として確定
- next action:
  - 追加 simplification が必要なら新 package を作成し、この package 自体は reopen しない
- entry note:
  - planner / generator core は未着手のまま keep

## Phase 01 Evidence

- status:
  - completed
- evidence:
  - `pipeline.py` に `_editor_report_to_dict()` を追加し、repeated editor-report conversion を owner-local helper に集約
  - `_apply_compatibility_rebuild()` を追加し、compatibility rebuild decision と article-type merge を main flow から外した
  - `_apply_article_type_postprocess()` を追加し、`branding / announcement / comparative_review / case_study / thin-source-grounded` の final-body postprocess branching を 1 本にまとめた
  - `generate()` 本体は `section generation -> compatibility rebuild -> stage passes -> article-type postprocess -> format` の spine に整理した
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q`
    - `209 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `66 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`
- rollback note:
  - `newalgorithm_pipeline/pipeline.py` の `_editor_report_to_dict()` / `_apply_compatibility_rebuild()` / `_apply_article_type_postprocess()` diff を戻せば baseline へ復帰可能

## Phase 02 Evidence

- status:
  - completed
- evidence:
  - `_refresh_diagnostics_state()` を追加し、`measure_diagnostics -> controlled realization -> quality guard -> controlled realization -> omission repair -> flagged spans` を owner-local helper に集約
  - `MinimalPipeline._run_optional_repair()` を追加し、repair entrypoint / patch-path metadata / acceptance / adopt decision を main flow から切り出した
  - `generate()` 本体は `surface guards -> diagnostics refresh -> optional repair -> comparative stabilizer -> build_result` の spine に整理した
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `66 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q`
    - `209 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`
- rollback note:
  - `simple_note_pipeline/pipeline.py` の `_refresh_diagnostics_state()` / `_run_optional_repair()` と main-flow replacement diff を戻せば baseline へ復帰可能

## Phase 03 Evidence

- status:
  - completed
- evidence:
  - `_normalize_execution_input_contract()` を追加し、prompt hydration / input contract resolve / compatibility source hydrate を owner-local helper に集約
  - `_run_current_mainline_pipeline()` を追加し、runner の fail-closed pipeline call を main flow から切り出した
  - `_finalize_current_mainline_result()` を追加し、output guard / vnext shadow / cutover rehearsal / boundary freeze projection を 1 本の finalize spine に集約した
  - `execute_current_mainline_generation()` 本体は `normalize input -> build payload -> run pipeline -> finalize result` の projection spine に整理した
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `66 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q`
    - `209 passed`
- rollback note:
  - `current_mainline_runner.py` の `_normalize_execution_input_contract()` / `_run_current_mainline_pipeline()` / `_finalize_current_mainline_result()` と main-flow replacement diff を戻せば baseline へ復帰可能
