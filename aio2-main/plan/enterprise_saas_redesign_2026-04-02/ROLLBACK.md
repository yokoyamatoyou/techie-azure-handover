# enterprise_saas_redesign_2026-04-02 ROLLBACK

## Baseline

- current UI shell:
  - `C:\tetie\aio2-main\nicegui_app.py`
- current panel owner:
  - `C:\tetie\aio2-main\core\ui\panels.py`
- current simple dashboard table:
  - `C:\tetie\aio2-main\core\ui\dashboard.py`
- current persistence:
  - `C:\tetie\aio2-main\core\application\analysis_run_service.py`
  - `C:\tetie\aio2-main\core\storage\database.py`
- current PDF / print path:
  - deleted in current package

## Restore Targets

- restore priority 1:
  - `C:\tetie\aio2-main\nicegui_app.py`
  - `C:\tetie\aio2-main\core\ui\panels.py`
  - `C:\tetie\aio2-main\core\ui\dashboard.py`
  - `C:\tetie\aio2-main\core\application\analysis_run_service.py`
  - `C:\tetie\aio2-main\core\storage\database.py`
- restore priority 2:
  - `C:\tetie\aio2-main\tests\`
  - `C:\tetie\aio2-main\plan\enterprise_saas_redesign_2026-04-02\PROGRESS.md`
  - `C:\tetie\aio2-main\WORKLOG.md`

## Per-Phase Rollback Boundary

- Phase 0:
  - package docs / test bootstrap / artifact capture only
- Phase 1:
  - dashboard shell and visual system diff only
- Phase 2:
  - DB migration / result file / snapshot save-load diff only
- Phase 3:
  - home dashboard assembly only
- Phase 4:
  - `/runs/{run_id}` route and detail workspace only
- Phase 5:
  - CSV export service and PDF removal only
- Phase 6:
  - CSS / accessibility / responsive diff only
- Phase 7:
  - review-driven narrow cleanup only

## Do-Not-Retry

- score formula を変えて UI を整えようとすること
- PDF を残したまま CSV を追加して主導線を二重化すること
- fixed/reference 情報を primary panel に戻すこと
- detail route なしで in-memory state のみから saved history を再表示しようとすること
- `analysis_runs` を作り直して既存 SQLite を捨てること

## Stop Conditions Requiring Rollback

- saved result の再表示で current analysis execution が壊れる
- dashboard 化のために algorithm owner の変更が必要になる
- Phase gate を越えないまま unrelated owner へ差分が広がる
- responsive/accessibility 修正が新たな情報過多を生む
