# orchestration_surface_reduction_2026-04-06 README

## Objective

- current success path を壊さず、`keep core, refactor boundaries` を維持したまま orchestration surface の削減を次 package として固定する
- `keep core, reduce orchestration surface` を docs-first の narrow package に落とし、何を残し、何を削り、どこを thin にするかを先に明文化する
- frozen reference である `architecture_target_refactor_2026-04-06` を reopen せず、wrapper / repair / boundary projection の責務整理だけを次の実施対象にする

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md`
4. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\TASK.md`
5. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md`
6. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\ROLLBACK.md`
7. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\EXECUTION_PROMPT.md`
8. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md`
9. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md`
10. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md`
11. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md`
12. `C:\tetie\notecode\ALGORITHM.md`
13. `C:\tetie\WORKLOG.md`

## Source Of Truth

- current runtime baseline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current planning package:
  - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
- frozen architecture reference:
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`
- completed baseline / freeze package:
  - `C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\`
  - `C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\`
  - `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\`

## Current Decision

- verdict:
  - `new package required`
- repo decision:
  - `keep core, refactor boundaries`
- package theme:
  - `keep core, reduce orchestration surface`
- frozen reference kept:
  - `hybrid target architecture`
- not adopted:
  - `keep as-is`
  - `replace architecture`
  - `quality-first next package`

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
  - completed
- phase 03 status:
  - completed
- next action:
  - この package は completed reference として keep し、追加 simplification が必要なら新 package を切る
- reuse mode:
  - `architecture_target_refactor_2026-04-06` は frozen reference として再利用する
  - completed implementation phase は reopen しない
  - current package は simplification-first の docs / phase owner package として扱う

## Why

- `newalgorithm_pipeline/pipeline.py` は wrapper / compatibility rebuild / article-type stabilizer / telemetry aggregation が 1 file に集中している
- `simple_note_pipeline/pipeline.py` は repair activation / patch-path / acceptance / experimental fallback を抱え、single-pass owner としては orchestration surface が厚い
- `discourse_planner.py` と `section_generator.py` の core primitive は architecture package で keep 判断が固まっている
- 先に quality を追うと wrapper と repair に local fix が積み増され、`prompt accretion` / `module accretion` 禁止に反しやすい

## Complexity Snapshot

- owner file size:
  - `current_mainline_runner.py`: 929 lines
  - `newalgorithm_pipeline/pipeline.py`: 2040 lines
  - `simple_note_pipeline/pipeline.py`: 1349 lines
  - `discourse_planner.py`: 900 lines
  - `section_generator.py`: 909 lines
- primary concern:
  - `newalgorithm_pipeline/pipeline.py` の article-type specific branch と compatibility rebuild ownership
  - `simple_note_pipeline/pipeline.py` の repair orchestration ownership
- keep core:
  - `DiscourseSection` section contract
  - route-aware source grounding
  - section-first writer
  - diagnostics / guard / quality validator 面

## Simplification Direction

### Keep

- `DiscourseSection` を中心にした section contract
- route-aware source grounding の分類と section 配賦
- section-first writer の逐次生成器
- diagnostics / guard / quality check の validator 面

### Thin

- `newalgorithm_pipeline/pipeline.py` の wrapper-local article-type branching
- `newalgorithm_pipeline/pipeline.py` の compatibility rebuild decision surface
- `simple_note_pipeline/pipeline.py` の repair activation / acceptance branching
- `current_mainline_runner.py` の boundary projection surface

### Remove As Default Assumption

- wrapper が article-type ごとの stabilizer owner を抱え続ける前提
- repair が hidden rewrite chain のように増えてよい前提
- quality 改善のためなら postprocess branch を足してよい前提

## Non-Goals

- frozen architecture package を reopen すること
- `discourse_planner.py` / `section_generator.py` の core mechanism を置換すること
- 新 route / 新 feature / 新 prompt block を追加すること
- prompt accretion / telemetry accretion で surface 削減を代替すること
- current success path の順序を変えること
