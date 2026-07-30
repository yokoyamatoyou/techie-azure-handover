# seo_llmo_coverage_2026-04-06 EXECUTION PROMPT

## autonomous_start_prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\aio2-main\AGENTS.md
- C:\tetie\aio2-main\ALGORITHM.md
- C:\tetie\aio2-main\WORKLOG.md
- C:\tetie\aio2-main\plan\CURRENT_AND_NEXT_IMPROVEMENTS.md
- C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\README.md
- C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\TASK.md
- C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\PROGRESS.md
- C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\ROLLBACK.md
- C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\EXECUTION_PROMPT.md

今回の実施範囲:
- `aio2-main` の SEO / LLMO 分析 coverage を package に沿って段階拡張する
- phase ごとに 1 scope ずつ進め、各 phase 完了後に必ず自己テストする
- 自己テスト合格後は user 確認待ちにせず、自律的に次 phase へ進む
- エラー時は同一 phase 内で最大 3 回まで自力修正する
- 3 回でも直らない場合だけ停止して user に報告する
- stop condition に触れない限り、phase 9 まで完走する
- score formula / legal meaning / provider meaning は変えない
- official source が必要な場合のみ Web 検索を使い、同一 failure で最大 3 回までに制限する
- `C:\tetie\zip` は mock として変更しない
- phase をまたぐ一括実装や unrelated refactor はしない
- 既存 owner file の肥大化を避け、必要なら小さな helper module へ分離する
- UI は summary-first を維持し、first view を過密化させない

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\aio2-main\AGENTS.md
3. C:\tetie\aio2-main\ALGORITHM.md
4. C:\tetie\aio2-main\WORKLOG.md
5. C:\tetie\aio2-main\plan\CURRENT_AND_NEXT_IMPROVEMENTS.md
6. C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\README.md
7. C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\TASK.md
8. C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\PROGRESS.md
9. C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\ROLLBACK.md
10. C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\EXECUTION_PROMPT.md

再開時の最初の手順:
1. `PROGRESS.md` の `Current phase` と `Phase Ledger` を読む
2. current phase の objective / owner / checks / risks を `TASK.md` で確認する
3. 対象 owner file だけを読む
4. phase を 1 つだけ進める
5. 自己テストを行う
6. `PROGRESS.md` を更新する
7. gate が green なら次 phase に auto-advance する
8. gate が red なら同一 phase 内で最大 3 回まで修正する
9. 3 回でも gate が green にならなければ停止して user に報告する

自律実行ルール:
- 1 回に 1 phase だけ進める
- current phase が green になったら、そのまま次 phase へ進む
- 停止条件に触れない限り、phase 9 完了まで継続する
- phase 完了ごとに `PROGRESS.md` の
  - `Current phase`
  - `Status`
  - `Attempts used`
  - `Official refresh attempts used`
  - `Implementation`
  - `Self-tests`
  - `Evidence`
  - `Next action`
  を更新する
- 自己テストが green になるまで次 phase に進まない
- phase ごとに owner scope を守り、不要な横断リファクタをしない
- file size が膨らみそうな場合は helper module を追加し、責務を分ける

bug / error 時のルール:
- まず local context だけで narrow fix を試す
- それでも仕様が確定しないときだけ official source を検索する
- source は Google Search Central / OpenAI official / Perplexity official を優先する
- official source refresh は同一 failure あたり最大 3 回
- query / source / confirmed fact / implementation decision / result を `PROGRESS.md` Failure Log に残す
- 3 回でもダメなら停止して user に状況を報告する

shared checks:
- C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\engine\orchestrator.py core\aio_analyzer.py core\engine\site_health_engine.py core\aio\schema_validator.py core\ui\panels.py core\ui\tabs\seo_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py
- C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_aio_analyzer.py tests\test_characterization_engine.py tests\test_characterization_ui.py tests\test_analysis_run_service.py
- C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_sitemap_analyzer.py tests\test_link_audit.py
- 必要に応じて対象 phase の新規 unit test を追加し、コマンドを `PROGRESS.md` に記録する

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
- official source refresh 3 回でも仕様確定不能
- score / legal / provider meaning の変更が必要
- rollback 不能な差分が必要
- live verify で重大 regression

この package の current target:
- `hreflang / x-default / html lang`
- mobile-first parity
- `LCP / CLS`
- `X-Robots-Tag` 拡張
- crawlable links / anchor text quality
- page-type aware schema validation
- image/video discoverability
- OpenAI merchant feed readiness
- Perplexity WAF / IP readiness note
- UI surfacing

最終報告で必ず示すこと:
- 参照ルールファイル
- 今回の実施範囲
- 現在Phase
- 実施内容
- テスト結果
- 失敗回数
- official refresh 回数
- 次アクション
- AGENTS/WORKLOG更新の要否
```
