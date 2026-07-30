# enterprise_saas_redesign_2026-04-02 EXECUTION PROMPT

## tomorrow_first_prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\aio2-main\AGENTS.md
- C:\tetie\aio2-main\ALGORITHM.md
- C:\tetie\aio2-main\WORKLOG.md
- C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\README.md
- C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\TASK.md
- C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\PROGRESS.md
- C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\ROLLBACK.md
- C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\EXECUTION_PROMPT.md

今回の実施範囲:
- `aio2-main` の enterprise SaaS redesign は Phase 7 まで完了済み
- 明日は completed state を前提に、残る UX polish を narrow に進める
- analysis logic / score meaning / legal meaning は変更しない
- PDF / print は削除済み。CSV only を維持する

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\aio2-main\AGENTS.md
3. C:\tetie\aio2-main\ALGORITHM.md
4. C:\tetie\aio2-main\WORKLOG.md
5. C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\README.md
6. C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\TASK.md
7. C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\PROGRESS.md
8. C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\ROLLBACK.md
9. C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\EXECUTION_PROMPT.md

再開時に最初に確認する artifact:
- C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\artifacts\phase-07\home-desktop-polish.png
- C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\artifacts\phase-07\detail-desktop-polish.png
- C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\artifacts\phase-07\detail-mobile-polish.png
- C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\artifacts\phase-07\detail-desktop-feedback2.png
- C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\artifacts\phase-07\detail-mobile-feedback2.png

current state summary:
- `/` は enterprise dashboard として稼働中
- `/runs/{run_id}` は saved detail workspace として稼働中
- `result_path` / `snapshot_json` 保存は実装済み
- CSV export 2 系統は実装済み
- `/report/print` は削除済みで `404`
- Phase 7 gate は green

明日の最初の目的:
- 現状 UI を live で再確認し、残る認知負荷を narrow に 1 つずつ潰す
- completed redesign を壊さず、visual / copy / density の polish だけに絞る

明日の優先候補:
1. dashboard 履歴テーブルの密度を下げる
   - 列数を再検討する
   - URL / score / priority / main action だけで十分か見直す
   - mobile でのテーブル見え方をさらに改善する
2. detail 上段 `最優先3件` の高さと情報量をさらに揃える
   - card height を統一する
   - 1 card 内の title / summary / meta を一定にする
3. `AI認識改善` / `SEO改善` / `実装メモ` のカード粒度を揃える
   - 同じ重要度の情報が同じ強さで見えるようにする
   - `参考情報` の後退を徹底する

やらないこと:
- アルゴリズム変更
- スコア計算変更
- 判定意味変更
- PDF 復活
- 任意 FAQ / 一般論を主導線へ戻すこと

実行ルール:
- 1 回で 1 つの narrow scope だけ進める
- 実装前に対象 screenshot と current UI を見て論点を固定する
- 変更後は必ず self-test / screenshot / PROGRESS.md 更新を行う
- 同一 scope で 3 回失敗したら停止して報告する

shared checks:
- C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\dashboard.py core\ui\panels.py core\application\analysis_run_service.py core\application\csv_export_service.py core\storage\database.py
- C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py tests\test_csv_export_service.py tests\test_characterization_engine.py

live verify:
- C:\tetie\techie-hub\start.bat force
- http://127.0.0.1:8081/
- http://127.0.0.1:8081/runs/84

UI fixed rules:
- 上部で分かるのは URL、AI認識、SEO、総合優先度、最優先3件、前回比 のみ
- KPI は 3 つまで
- 主CTA は 3 つまで
- 見出し階層は 3 段まで
- helper text は本文より 1 段小さく muted
- personalized advice と fixed/reference を同格に見せない
- 企業向け SaaS として情報階層、可読性、認知負荷低減を優先する

再開直後の作業順:
1. required docs と phase-07 artifacts を読む
2. `/` と `/runs/84` を live で確認する
3. 明日進める narrow scope を 1 つだけ宣言する
4. 実装
5. py_compile / pytest / screenshot / PROGRESS.md 更新
6. その scope だけで終了する

最終報告で必ず示すこと:
- 参照ルールファイル
- 今回の実施範囲
- 現在Phase
- 実施内容
- テスト結果
- 失敗回数
- 次アクション
- AGENTS/WORKLOG更新の要否
```
