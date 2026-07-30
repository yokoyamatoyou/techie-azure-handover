# ux_commercial_readiness_2026-04-05 ROLLBACK

## Baseline

- UI shell:
  - `C:\tetie\aio2-main\nicegui_app.py`
- workspace owner:
  - `C:\tetie\aio2-main\core\ui\panels.py`
- dashboard owner:
  - `C:\tetie\aio2-main\core\ui\dashboard.py`
- snapshot / FAQ owner:
  - `C:\tetie\aio2-main\core\application\analysis_run_service.py`
- current predecessor package:
  - `C:\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\`

## Restore Targets

- restore priority 1:
  - `C:\tetie\aio2-main\nicegui_app.py`
  - `C:\tetie\aio2-main\core\ui\panels.py`
  - `C:\tetie\aio2-main\core\ui\dashboard.py`
  - `C:\tetie\aio2-main\core\application\analysis_run_service.py`
- restore priority 2:
  - `C:\tetie\aio2-main\tests\`
  - `C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\PROGRESS.md`
  - `C:\tetie\aio2-main\WORKLOG.md`

## Per-Phase Rollback Boundary

- Phase 0:
  - docs / progress / prompt only
- Phase 1:
  - baseline verify memo only
- Phase 2:
  - hero / guide copy and related CSS only
- Phase 3:
  - `サマリー` / `やること` visual hierarchy only
- Phase 4:
  - `実装・設定` wording / disclosure / compression only
- Phase 5:
  - FAQ rationale label / explanation only
- Phase 6:
  - dashboard density / mobile / CSS only
- Phase 7:
  - accessibility / focus / contrast narrow fix only
- Phase 8:
  - review / residual cleanup only

## Do-Not-Retry

- algorithm change で UI 問題を解決しようとすること
- score / legal / provider meaning を変えること
- 5 タブ IA を再び抽象タブへ戻すこと
- pass noise を減らすために重要な warn/fail まで隠すこと
- live / saved parity を壊すこと
- user-facing bug を docs 上の説明でごまかして phase を進めること

## Stop Conditions Requiring Rollback

- hero / IA copy 修正が route / workflow regression を生む
- hierarchy 修正のために unrelated owner へ差分が広がる
- accessibility fix が情報密度や可読性を悪化させる
- phase gate 未通過のまま temporary workaround が積み上がる
- web search 3 回でも解けない browser / NiceGUI behavior mismatch が残る
