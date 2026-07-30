# ux_commercial_readiness_2026-04-05 EXECUTION PROMPT

## autonomous_start_prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\aio2-main\AGENTS.md
- C:\tetie\aio2-main\ALGORITHM.md
- C:\tetie\aio2-main\WORKLOG.md
- C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\README.md
- C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\TASK.md
- C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\PROGRESS.md
- C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\README.md
- C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\TASK.md
- C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\PROGRESS.md
- C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\ROLLBACK.md
- C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\EXECUTION_PROMPT.md

今回の実施範囲:
- `aio2-main` の post-analysis UI を commercial readiness package に沿って自律的に仕上げる
- phase ごとに 1 scope ずつ進め、自己テスト完了後に次 phase へ自動で進む
- analysis logic / score meaning / legal meaning は変更しない
- `C:\tetie\zip` は mock として変更しない

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\aio2-main\AGENTS.md
3. C:\tetie\aio2-main\ALGORITHM.md
4. C:\tetie\aio2-main\WORKLOG.md
5. C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\README.md
6. C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\TASK.md
7. C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\PROGRESS.md
8. C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\README.md
9. C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\TASK.md
10. C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\PROGRESS.md
11. C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\ROLLBACK.md
12. C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\EXECUTION_PROMPT.md

再開時の最初の手順:
1. `PROGRESS.md` の `Current phase` と `Phase Ledger` を読む
2. `Current phase` の owner / objective / gate を `TASK.md` で確認する
3. 対象 owner file だけを読む
4. phase を 1 つだけ進める
5. 自己テストを行う
6. `PROGRESS.md` を更新する
7. gate が green なら次 phase に auto-advance する
8. gate が red なら同一 phase 内で最大 3 回まで修正する

自律実行ルール:
- 1 回に 1 phase だけ進める
- phase 完了ごとに `PROGRESS.md` の
  - `Current phase`
  - `Status`
  - `Attempts used`
  - `Web search attempts used`
  - `Implementation`
  - `Self-tests`
  - `Evidence`
  - `Next action`
  を更新する
- 自己テストが green になるまで次 phase に進まない

bug / error 時のルール:
- まず local context だけで narrow fix を試す
- それでも解けないときだけ Web 検索を使う
- Web 検索は同一 failure あたり最大 3 回
- source は official / primary を優先
- query / source / tried fix / result を `PROGRESS.md` Failure Log に残す
- 3 回でもダメなら停止して user に状況を報告する

shared checks:
- C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\panels.py core\ui\dashboard.py core\ui\tabs\aio_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py
- C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py
- 必要時: C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_dashboard_ui.py

live verify:
- C:\tetie\techie-hub\start.bat force
- http://127.0.0.1:8081/
- http://127.0.0.1:8081/runs/84

phase 完了条件:
- phase-specific 実装が完了
- required tests pass
- evidence が `PROGRESS.md` に残っている
- stop condition に触れていない

stop condition:
- 同一 phase で 3 回失敗
- Web 検索 3 回でも修正不能
- algorithm / score / legal meaning の変更が必要
- rollback 不能な差分が必要
- live verify で重大 regression

この package の目的:
- entry copy と actual IA を一致させる
- first view hierarchy を commercial quality に寄せる
- `実装・設定` を warn/fail 中心で読めるようにする
- FAQ rationale を短く理解できるようにする
- keyboard / contrast / mobile / empty state verify を package 化する

最終報告で必ず示すこと:
- 参照ルールファイル
- 今回の実施範囲
- 現在Phase
- 実施内容
- テスト結果
- 失敗回数
- Web検索回数
- 次アクション
- AGENTS/WORKLOG更新の要否
```
