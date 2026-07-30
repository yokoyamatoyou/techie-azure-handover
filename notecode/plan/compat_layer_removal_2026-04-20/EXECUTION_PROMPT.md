# compat_layer_removal_2026-04-20 EXECUTION_PROMPT

```text
参照ルール:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\README.md
- C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\TASK.md
- C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\PROGRESS.md
- 必要なら:
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md

今回の依頼:
- compat layer removal package の separate-window implementation
- 目的は current success path から `note/newalgorithm_pipeline/pipeline.py` を外し、
  `note/current_mainline_runner.py -> note/simple_note_pipeline/pipeline.py`
  の direct path へ寄せること
- dead code 削除は first move にしない

今回の owner scope:
- production:
  - C:\tetie\notecode\note\current_mainline_runner.py
  - 必要なら owner-local adapter file 1 本まで
- read-only:
  - C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- tests:
  - C:\tetie\notecode\note\tests\test_current_mainline_runner.py
  - C:\tetie\notecode\note\tests\test_current_mainline_regressions.py
  - C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py
  - 必要なら owner-local に関係する最小 test だけ

first diff で触らない:
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\*
- C:\tetie\notecode\docs\*
- AGENTS / WORKLOG

fixed read:
- `simple_note_pipeline` が現行実体
- `newalgorithm_pipeline` は current success path 上の compatibility wrapper
- よって現時点では dead code ではない
- 先に runtime path を直結化し、その後に compatibility surface を inventory する

実装ルール:
1. 先に `current_mainline_runner.py` と `newalgorithm_pipeline/pipeline.py` の責務差分を short map にする
2. `newalgorithm_pipeline` が担っている runtime semantics を列挙する
3. direct path に必要な最小 adapter だけ runner 側へ寄せる
4. `simple_note_pipeline` の意味は変えない
5. `newalgorithm_pipeline` の削除はしない
6. prompt accretion / broad refactor / unrelated cleanup はしない
7. direct path 化のあと、`newalgorithm_pipeline` が success path から外れたことを code path で説明する
8. dead code inventory は separate note として箇条書き化するだけでよい

期待する narrow hypothesis:
- `newalgorithm_pipeline` の wrapper 責務のうち runtime に必要な最小部分を
  `current_mainline_runner.py` に寄せれば、`simple_note_pipeline` へ直結しても
  current success path regression なしで shared checks を通せる

実行順:
1. refs を読む
2. `current_mainline_runner.py` の current call path を short map 化
3. `newalgorithm_pipeline/pipeline.py` の wrapper responsibilities を short map 化
4. direct path diff を実装
5. focused tests
6. shared checks
7. `newalgorithm_pipeline` no-longer-runtime-path の確認
8. dead code inventory の初版を final report に添付

focused / shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
- 必要なら:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_simple_note_pipeline.py -q

pass 条件:
- current success path regression なし
- runner / regressions / ui matrix が green
- direct path が説明できる
- `newalgorithm_pipeline` を current success path から外したと説明できる
- 新しいエラーを増やしていない

stop 条件:
- `newalgorithm_pipeline` が wrapper 以上の runtime semantics を持ち、owner scope を超えないと切れない
- `simple_note_pipeline/pipeline.py` の意味変更が必要
- 複数 owner を同時に触らないと current mainline が壊れる
- shared checks で regression

失敗時:
- narrow rollback
- code は direct path 導入前の状態へ戻す
- `newalgorithm_pipeline` は保持
- stop report に
  - wrapper responsibilities
  - direct path を阻害した責務
  - 次に必要な owner scope
  を明記する

final report に必ず含める項目:
1. 読んだ正本ファイル
2. current runtime path short map
3. wrapper responsibilities short map
4. touched files
5. 実装した narrow hypothesis
6. 実行した tests / shared checks
7. `newalgorithm_pipeline` が current success path から外れたかどうか
8. dead code inventory 初版
9. rollback の有無
10. AGENTS / WORKLOG / unrelated docs を更新していないこと
```
