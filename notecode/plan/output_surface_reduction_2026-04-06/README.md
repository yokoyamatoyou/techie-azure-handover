# output_surface_reduction_2026-04-06 README

## Objective

- current success path を壊さず、`keep core, refactor boundaries` を維持したまま final output surface の削減を次 package として固定する
- `output_formatter.py` owner に残っている article-type specific title / lead / scaffold shaping を docs-first の narrow package に落とし、何を keep し、どこを thin にするかを先に明文化する
- completed reference である `orchestration_surface_reduction_2026-04-06` と frozen reference である `architecture_target_refactor_2026-04-06` を reopen せず、formatter / final-stage boundary だけを次の実施対象にする

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md`
4. `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\TASK.md`
5. `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md`
6. `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\ROLLBACK.md`
7. `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\EXECUTION_PROMPT.md`
8. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md`
9. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md`
10. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md`
11. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md`
12. `C:\tetie\notecode\ALGORITHM.md`
13. `C:\tetie\WORKLOG.md`

## Source Of Truth

- current runtime baseline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- next owner residual:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- current planning package:
  - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\`
- completed reference package:
  - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
- frozen architecture reference:
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`

## Current Decision

- verdict:
  - `new package required`
- repo decision:
  - `keep core, refactor boundaries`
- package theme:
  - `keep core, reduce output surface`
- first owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- not adopted:
  - `keep as-is`
  - `reopen completed package`
  - `planner / generator core first`

## Package State

- package status:
  - completed
- package mode:
  - implementation completed
- current phase:
  - complete
- phase 00 status:
  - completed
- phase 01 status:
  - completed
- phase 02 status:
  - not needed
- next action:
  - この package は completed reference として keep し、追加 final-stage simplification が必要なら新 package を切る
- reuse mode:
  - `orchestration_surface_reduction_2026-04-06` は completed reference として keep する
  - `architecture_target_refactor_2026-04-06` は frozen reference として keep する
  - `output_formatter.py` owner diff は completed owner scope として keep する

## Why

- `output_formatter.py` は `1074 lines` あり、article-type specific title / lead / scaffold / body shaping が 1 file に集中している
- wrapper の quality spine でも final stage は `output_formatter` として残っており、completed owner scope の外に final shaping surface がまだ残っている
- `ALGORITHM.md` では branding title echo residual を `output_formatter.py` owner の別 mechanism として扱うと固定されている
- planner / generator core を初手で reopen せずに次の narrow owner を切るなら、formatter surface が最も自然な入口になる

## Complexity Snapshot

- owner file size:
  - `output_formatter.py`: `1074 lines`
  - `editor_guard.py`: `394 lines`
  - `legal_postcheck.py`: `314 lines`
  - `newalgorithm_pipeline/pipeline.py`: `2074 lines`
- primary concern:
  - final output shaping の article-type decision density
  - formatter 内に残る body normalize / title seed / lead seed / scaffold projection の重なり
- keep untouched first:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\section_generator.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`

## Simplification Direction

### Keep

- current success path の順序
- wrapper quality spine の stage order
- `format_output()` が返す current contract
- `editor_guard.py` / `legal_postcheck.py` の既存責務境界

### Thin

- `output_formatter.py` の article-type specific title seed branching
- `output_formatter.py` の lead / scaffold mode branching
- `output_formatter.py` の body normalize と final projection の境界面

### Remove As Default Assumption

- final quality residual は `output_formatter.py` に article-type rule を足せば救える前提
- formatter が hidden repair owner を抱え続けてよい前提
- branding / announcement / comparative ごとに別 heuristic を積み増しても surface reduction と見なせる前提

## Completion Note

- completed owner scope:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- completion summary:
  - formatter main flow を `normalize body -> project head -> add scaffold` の spine に整理した
  - owner-local / shared checks は green
- next action:
  - final-stage residual が残るなら新 package を切り、この package 自体は reopen しない

## Non-Goals

- completed reference package を reopen すること
- frozen architecture package を reopen すること
- `discourse_planner.py` / `section_generator.py` の core mechanism を置換すること
- `current_mainline_runner.py` / `newalgorithm_pipeline/pipeline.py` / `simple_note_pipeline/pipeline.py` を package objective に戻すこと
- prompt accretion / module accretion で final output residual を隠すこと
- current success path の順序を変えること
