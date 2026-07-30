# seo_llmo_coverage_2026-04-06 ROLLBACK

## Baseline

- engine owner:
  - `C:\tetie\aio2-main\core\engine\orchestrator.py`
- AI/search owner:
  - `C:\tetie\aio2-main\core\aio_analyzer.py`
- schema/site health owner:
  - `C:\tetie\aio2-main\core\engine\site_health_engine.py`
  - `C:\tetie\aio2-main\core\aio\schema_validator.py`
- UI owner:
  - `C:\tetie\aio2-main\core\ui\panels.py`
  - `C:\tetie\aio2-main\core\ui\tabs\seo_tab.py`
  - `C:\tetie\aio2-main\core\ui\tabs\health_tab.py`
- snapshot owner:
  - `C:\tetie\aio2-main\core\application\analysis_run_service.py`

## Restore Targets

- restore priority 1:
  - `C:\tetie\aio2-main\core\engine\orchestrator.py`
  - `C:\tetie\aio2-main\core\aio_analyzer.py`
  - `C:\tetie\aio2-main\core\engine\site_health_engine.py`
  - `C:\tetie\aio2-main\core\aio\schema_validator.py`
- restore priority 2:
  - new `core\seo\*.py` helpers
  - new `tests\test_*.py`
  - `core\ui\panels.py`
  - `core\ui\tabs\seo_tab.py`
  - `core\ui\tabs\health_tab.py`
  - `core\application\analysis_run_service.py`
- restore priority 3:
  - `plan\seo_llmo_coverage_2026-04-06\PROGRESS.md`
  - `WORKLOG.md`
  - optional `ALGORITHM.md`

## Per-Phase Rollback Boundary

- Phase 0:
  - docs only
- Phase 1:
  - docs + matrix memo only
- Phase 2:
  - international / metadata policy helper と engine wiring のみ
- Phase 3:
  - page experience helper と engine wiring のみ
- Phase 4:
  - link quality helper と engine wiring のみ
- Phase 5:
  - schema validator / site health integration のみ
- Phase 6:
  - media discovery helper と engine wiring のみ
- Phase 7:
  - provider note / commerce helper のみ
- Phase 8:
  - UI / snapshot / wording のみ
- Phase 9:
  - docs / tests / closeout only

## Do-Not-Retry

- score formula を変えて coverage 問題を解決しようとすること
- OpenAI Search と GPTBot を統合して扱うこと
- `llms.txt` を必須要件にすること
- `hreflang` や `X-Robots-Tag` を推測実装し、official source を確認せず断定すること
- UI で新項目を全部 first view に出して情報密度を壊すこと
- live / saved parity を壊すこと

## Stop Conditions Requiring Rollback

- provider meaning の変更が必要になった
- score meaning の変更が必要になった
- helper 導入が unrelated files へ波及しすぎた
- UI integration が primary reading flow を壊した
- targeted tests green でも live verify で重大 regression が残る
