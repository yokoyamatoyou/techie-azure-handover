# enterprise_saas_redesign_2026-04-02

`aio2-main` を分析ロジック非変更のまま、企業向け SaaS の dashboard + detail workspace 構成へ作り直す current execution package。

## Objective

- SEO / AIO / 法務 / サイトヘルスの分析ロジック、スコア計算、判定意味は維持する
- `/` を enterprise dashboard、`/runs/{run_id}` を保存済み分析の detail workspace に置き換える
- 既存 SQLite を活かしつつ `result_path` と `snapshot_json` を追加し、保存済み run を再表示できるようにする
- PDF / print route を撤去し、CSV export を `優先アクションCSV` と `履歴一覧CSV` の 2 系統で置き換える
- progress はこの package に集約し、各 phase ごとに screenshot と gate 結果を残す

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\aio2-main\AGENTS.md`
3. `C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\README.md`
4. `C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\TASK.md`
5. `C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\PROGRESS.md`
6. `C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\ROLLBACK.md`
7. `C:\tetie\aio2-main\ALGORITHM.md`
8. `C:\tetie\aio2-main\WORKLOG.md`

## Source-Of-Truth Priority

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\aio2-main\AGENTS.md`
3. `C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\README.md`
4. `C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\TASK.md`
5. `C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\PROGRESS.md`
6. `C:\tetie\aio2-main\ALGORITHM.md`
7. `C:\tetie\aio2-main\WORKLOG.md`

## Global Policy

- analysis engine / score meaning / legal meaning は変更しない
- brand base color と logo asset は維持する
- `dashboard + detail workspace` の IA を優先し、固定 FAQ / 一般論 / 任意項目は主導線に置かない
- personalized advice と fixed/reference information を同格に見せない
- 1 phase ごとに gate / self-test / screenshot / `PROGRESS.md` 更新を完了してから次へ進む
- 同一 phase の自己修正は最大 3 回。3 回失敗したら停止して user report する
- screenshot と live verify は `desktop + mobile` を基本にする

## Current Baseline

- current UI shell:
  - `C:\tetie\aio2-main\nicegui_app.py`
- current panel owner:
  - `C:\tetie\aio2-main\core\ui\panels.py`
- current simple history table:
  - `C:\tetie\aio2-main\core\ui\dashboard.py`
- current persistence owner:
  - `C:\tetie\aio2-main\core\application\analysis_run_service.py`
  - `C:\tetie\aio2-main\core\storage\database.py`
- current PDF / print owner:
  - deleted in current package

## Baseline Artifacts

- desktop:
  - `C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\artifacts\baseline\home-desktop.png`
  - `C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\artifacts\baseline\print-desktop.png`
- mobile:
  - `C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\artifacts\baseline\home-mobile.png`
  - `C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\artifacts\baseline\print-mobile.png`

## Baseline Findings

- `/`
  - hero + step card + input card の構成で、enterprise dashboard の履歴中心導線にはなっていない
  - dashboard data table は mounted されておらず、履歴一覧は主導線に存在しない
- `/report/print`
  - state 依存の長尺 print shell で、保存済み run の単独再表示 route にはなっていない
  - mobile screenshot でも極端に縦長で、progressive disclosure がない
- persistence
  - `analysis_runs` は `pdf_path` 前提で、`result_path` / `snapshot_json` / saved detail rehydrate が未実装
- test gate
  - `python -m py_compile ...` は通る
  - `.venv\Scripts\pytest.exe -q ...` は `ModuleNotFoundError: core` で失敗し、Phase 0 で修正が必要

## Removal Targets

- `/report/print` route
- `印刷用ページ` / `印刷用ページを開く` link
- `print_mode` 依存 UI
- `core/reporting/pdf_export_service.py` と `generate_enhanced_pdf_report()` 経由の PDF export path
- `pdf_path` を current feature として扱う UI / service / test

## Inheritance Targets

- existing analysis execution flow in `core/application/analysis_run_service.py`
- current result payload from `core/engine/orchestrator.py`
- existing UI section content in `core/ui/panels.py` を SaaS IA 用に再編した payload
- existing SQLite file and `analysis_runs` table
- current label / score presentation rules that reflect `ALGORITHM.md`

## Non-Goals

- authentication / RBAC / multi-tenant 化
- score formula の変更
- PDF の代替として新たな document export format を増やすこと
- FAQ 一般論を primary surface に戻すこと
