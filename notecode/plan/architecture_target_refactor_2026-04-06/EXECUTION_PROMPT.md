# architecture_target_refactor_2026-04-06 EXECUTION PROMPT

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\TASK.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md

今回の実施範囲:
- `architecture_target_refactor_2026-04-06` package は implementation + closeout + handoff/freeze completed state として扱う
- current success path を壊さずに、この package を frozen reference として参照する
- repo decision は `keep core, refactor boundaries`
- end-state image は `hybrid target architecture`
- Phase 01-06 の narrow implementation、package closeout、handoff / freeze は完了済みである

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
4. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\TASK.md
5. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
6. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
7. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md
8. C:\tetie\notecode\ALGORITHM.md
9. C:\tetie\WORKLOG.md

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
4. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\TASK.md
5. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
6. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md
7. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md
8. C:\tetie\notecode\ALGORITHM.md
9. C:\tetie\WORKLOG.md

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

現在の package 状態:
- package status:
  - completed
- implementation completion:
  - Phase 01 Canonical Plan State: completed
  - Phase 02 Attributed Fact Slots: completed
  - Phase 03 Section State Promotion: completed
  - Phase 04 Route-Gated Section-First Mainline: completed
  - Phase 05 Constrained Micro-Revision: completed
  - Phase 06 Wrapper Demotion: completed

current architecture verdict:
- adopted:
  - hybrid target architecture
  - repo interpretation: keep core, refactor boundaries
- keep:
  - DiscourseSection を中心にした section contract
  - route-aware source grounding の分類と節配賦
  - section-first writer の逐次生成器
  - diagnostics / guard / quality check の validator 面
- refactor completed in this package:
  - canonical plan state
  - attributed fact slots
  - planner-owned section state
  - constrained micro-revision
  - wrapper demotion telemetry
- closeout status:
  - completed
- handoff / freeze status:
  - completed
- reject:
  - keep as-is
  - replace architecture

再開時の前提:
- prompt accretion をしない
- module accretion をしない
- current success path を壊さない
- completed phase を reopen しない
- rollback 可能な narrow diff だけを許可する
- frozen package のため、この package に新しい implementation phase を勝手に足さない

次に扱う候補タスク:
1. next package creation
   - 新しい task を扱う必要がある場合だけ、新 package の入口を作る
2. artifact review
   - 明示依頼がある場合だけ current success path の実生成物を確認し、telemetry と本文の整合を見る

今回まだ完了していない可能性がある作業:
- 次 package の入口作成要否判断
- current mainline artifact review の明示依頼待ち

shared check commands:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q

開始直後の最初の判断:
1. `README.md` / `PROGRESS.md` / `ROLLBACK.md` / `EXECUTION_PROMPT.md` が frozen / archive-ready state になっているか確認する
2. 今回の作業が new package creation なのか、artifact review なのかを 1 行で固定する
3. owner scope を 1 file または docs-only に閉じられるか確認する
4. completed phase の code を reopen する必要が出たら、この package ではなく新 package を切る

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- 今回の narrow task
- owner scope
- 実施した変更
- 実行した tests
- rollback の有無
- package closeout の進捗
- handoff / freeze の進捗
- frozen reference 化の有無
- AGENTS / WORKLOG 更新の有無
```
