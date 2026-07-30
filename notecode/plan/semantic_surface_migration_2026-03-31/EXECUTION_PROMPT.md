# semantic_surface_migration_2026-03-31 execution prompt

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md

今回の実施範囲:
- C:\tetie\notecode\GPTPRO.txt を前提に、meaning-layer / surface-layer 分離を current mainline へ段階導入すること
- 実行 package は C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\ を正本とする
- current success path を維持し、phase pass 後だけ次へ進む

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\GPTPRO.txt
4. C:\tetie\notecode\ALGORITHM.md
5. C:\tetie\WORKLOG.md
6. C:\tetie\notecode_current_mainline_handoff_2026-03-31.md
7. C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\README.md
8. C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\TASK.md
9. C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\PROGRESS.md

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> super().generate(...)
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

前提:
- prompt accretion を禁止する
- module accretion を禁止する
- human_resonance* は初手で触らない
- rollback 可能な narrow diff だけを許可する
- same phase の自己修正は 3 回まで
- 3 回失敗したら停止し、ユーザーへ報告する

phase progression rule:
1. PROGRESS.md で current phase を in_progress に更新する
2. phase の objective / owner / rollback を確認する
3. 実装する
4. phase required checks を実行する
5. 以下 4 系統が green のときだけ次 phase へ進む
   - prompt injection / policy
   - code readability
   - UI integration
   - pipeline
6. PROGRESS.md に evidence / tests / rollback note を追記する

必須チェックコマンド:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q

停止条件:
- 同一 phase で 3 回自己修正しても gate を越えられない
- announcement kept fix regression
- comparative rollback 済み仮説の再投入
- owner file 増加が narrow slice を超える
- rollback 不能な diff が必要になった

phase 実行方針:
- Phase 00 から順に進む
- phase pass まで次へ進まない
- 各 phase は 1 narrow hypothesis に固定する
- 増やすより、削る・短くする・責務を戻す・rollback する、を優先する

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- 実施した phase
- 各 phase の evidence
- 実行した tests
- keep した修正
- rollback した仮説
- 停止した場合は failed attempts / reason / next narrow slice
- AGENTS / WORKLOG 更新の有無
```
