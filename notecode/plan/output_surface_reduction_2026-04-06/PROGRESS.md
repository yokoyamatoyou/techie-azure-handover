# output_surface_reduction_2026-04-06 PROGRESS

## Current Goal

- completed / frozen reference を reopen せず、final output surface を next narrow package として固定する

## Current Status

- Package status: completed
- Current phase: complete
- Status: completed
- Hypothesis:
  - `output_formatter.py` を final output spine に寄せれば、planner / generator core を触らずに次の complexity residual を thin にできる
- Owner scope:
  - none
- Attempts used: 1/3
- Next phase:
  - none

## Baseline

- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- completed reference package:
  - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
- frozen reference package:
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`
- keep decision inherited from frozen reference:
  - `hybrid target architecture`
  - repo-level interpretation: `keep core, refactor boundaries`
- package theme:
  - `keep core, reduce output surface`

## Complexity Assessment

- owner file size:
  - `output_formatter.py`: `1074 lines`
  - `editor_guard.py`: `394 lines`
  - `legal_postcheck.py`: `314 lines`
  - `newalgorithm_pipeline/pipeline.py`: `2074 lines`
- primary concern:
  - formatter local article-type branch density
  - final output shaping residual が completed owner scope の外に残っていること
- keep untouched first:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\section_generator.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`

## Blocked Hypotheses

- `orchestration_surface_reduction_2026-04-06` package を reopen すること
- `architecture_target_refactor_2026-04-06` package を reopen すること
- planner / generator core を初手で触ること
- formatter residual を prompt accretion で吸収すること
- formatter residual を pipeline owner へ戻して解消すること
- article-type heuristic を増やして simplification と見なすこと

## Phase Ledger

| Phase | Status | Hypothesis | Owner scope | Attempts | Evidence | Next phase |
|------|--------|------------|-------------|----------|----------|------------|
| 00 Package Freeze | completed | output surface boundary を docs に先固定すれば、next slice が final-stage fix 増殖に戻らない | package docs only | 0/3 | `README.md` / `TASK.md` / `PROGRESS.md` / `ROLLBACK.md` / `EXECUTION_PROMPT.md` に keep/thin/remove と source-of-truth を固定 | 01 |
| 01 Output Formatter Surface Reduction | completed | formatter の title / lead / scaffold / normalize branching を 1 本に寄せれば final output surface を薄くできる | `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py` | 1/3 | `normalize_output_body()` を body-normalizer spine に整理し、`format_output()` を `resolve title -> resolve lead -> resolve scaffold -> assemble body` に集約。shared checks green | complete |
| 02 Editor Guard Boundary Trim | not needed | formatter / editor boundary duplication が主因なら editor guard owner を薄くできる | `C:\tetie\notecode\note\newalgorithm_pipeline\editor_guard.py` | 0/3 | Phase 01 完了後の owner-local / shared checks で追加 boundary trim を要する evidence なし | complete |

## Phase 00 Evidence

- status:
  - completed
- evidence:
  - new package の objective / read order / source-of-truth / non-goals を固定
  - completed reference と frozen reference は reopen 不可と明記
  - next narrow owner を `output_formatter.py` に固定
- tests:
  - docs only
- rollback note:
  - なし

## Package Outcome

- verdict:
  - keep
- next action:
  - この package は completed reference として keep し、追加 simplification が必要なら新 package を作成する
- entry note:
  - planner / generator core は未着手のまま keep
  - completed / frozen reference package と completed owner scope は reopen しない

## Phase 01 Evidence

- status:
  - completed
- evidence:
  - `_normalize_announcement_output_body()` / `_drop_known_transition_fragments()` / `_apply_article_type_output_body_normalizers()` / `_normalize_output_lines()` を追加し、`normalize_output_body()` を body-normalizer spine に整理した
  - `_resolve_output_title()` / `_resolve_output_lead()` / `_resolve_output_scaffold()` / `_build_output_full_body()` を追加し、`format_output()` を `resolve title -> resolve lead -> resolve scaffold -> assemble body` の spine に整理した
  - article-type behavior は保持したまま、formatter main flow の decision surface を owner-local helper に集約した
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st08c or st07a_06 or st07a_07" -q`
    - `16 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q`
    - `209 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `66 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`
- rollback note:
  - `output_formatter.py` の body-normalizer spine / output projection spine diff を戻せば baseline へ復帰可能
