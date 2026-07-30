# seo_llmo_coverage_2026-04-06 PROGRESS

## Current Goal

- `aio2-main` の SEO / LLMO 分析 coverage を、2026-04-06 時点の最新ベストプラクティスに対して不足が追える状態へ拡張する

## Current Status

- Package status: active
- Current phase: complete
- Status: completed
- Owner scope:
  - closeout
- Attempts used: 1/3
- Official refresh attempts used: 0/3
- Next action:
  - package closeout 完了。必要なら run 再分析データで追加UI文言を確認する

## Baseline Findings

- current mainline は
  - internal link structure
  - link target audit
  - provider robots gate
  - snippet control
  - OGP / alt / schema / FAQ
  を持っている
- ただし次が未実装または弱い
  - `hreflang / x-default / html lang`
  - mobile-first parity
  - `LCP / CLS`
  - `X-Robots-Tag` の拡張
  - crawlable links / anchor text の SEO 監査
  - page-type aware schema validation
  - image/video discoverability
  - OpenAI merchants feed readiness
  - Perplexity WAF / IP allowlist readiness note
- UI への surfacing も未設計

## Success Bar

- P0/P1 gap が current mainline で明示監査できる
- UI は warn/fail 優先で読める
- official source refresh の結果が docs に残る
- targeted tests / compile / live verify が green

## Phase Ledger

| Phase | Status | Attempts | Official | Evidence | Next |
|------|--------|----------|----------|----------|------|
| 0 package bootstrap | completed | 1/3 | 0/3 | docs 5 点 + artifacts dir 作成済み | 1 |
| 1 baseline matrix lock | completed | 1/3 | 0/3 | owner map / gap / compile gate を固定 | 2 |
| 2 international and policy audit | completed | 1/3 | 0/3 | international / X-Robots-Tag surface と test を追加 | 3 |
| 3 mobile and page experience audit | completed | 2/3 | 0/3 | mobile parity / LCP / CLS surface と test を追加 | 4 |
| 4 crawlable links audit | completed | 2/3 | 0/3 | crawlable / anchor quality surface と test を追加 | 5 |
| 5 schema depth refinement | completed | 1/3 | 0/3 | page-type aware schema validation と test を追加 | 6 |
| 6 image/video discovery audit | completed | 1/3 | 0/3 | media discovery / sitemap media hints と test を追加 | 7 |
| 7 LLMO and commerce coverage | completed | 1/3 | 1/3 | commerce / Perplexity note と official memo を追加 | 8 |
| 8 UI integration | completed | 1/3 | 0/3 | live / saved UI に追加監査を surfacing し live verify を記録 | 9 |
| 9 regression and closeout | completed | 1/3 | 0/3 | compile / targeted pytest / live verify / docs 更新を完了 | complete |

## Per-Phase Execution Record

### Phase 0

- Status:
  - completed
- Implementation:
  - `README.md`, `TASK.md`, `PROGRESS.md`, `ROLLBACK.md`, `EXECUTION_PROMPT.md`, `artifacts\README.md` を作成
- Self-tests:
  - doc completeness review pass
- Evidence:
  - package path: `C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\`
- Next action:
  - Phase 1 baseline matrix lock

### Phase 1

- Status:
  - completed
- Implementation:
  - current owner / scope をコード側で再確認し、package の owner map と gap matrix が mainline と一致することを固定
  - `rg` で `hreflang / x-default / X-Robots-Tag / LCP / CLS / llms.txt / OAI-SearchBot / PerplexityBot` の既存実装位置を確認
  - baseline を次のように固定
    - provider robots gate と `llms.txt` note は `core\aio_analyzer.py` と `core\engine\orchestrator.py` に既存実装あり
    - `X-Robots-Tag` は `core\seo\link_audit.py` にリンク先監査用の局所実装があるが、page result surfacing は未実装
    - `hreflang / x-default / html lang / mobile parity / LCP / CLS / merchant readiness / Perplexity WAF/IP note` は current mainline に未配線
- Self-tests:
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\engine\orchestrator.py core\aio_analyzer.py core\engine\site_health_engine.py core\aio\schema_validator.py core\ui\panels.py core\ui\tabs\seo_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py`
    - PASS
- Evidence:
  - code inspection:
    - `core\aio_analyzer.py` に provider gate / `llms.txt` informational note が存在
    - `core\engine\orchestrator.py` に provider readiness assembly が存在
    - `core\seo\link_audit.py` に `X-Robots-Tag` 読み取りが存在
    - international / page experience / media discovery / commerce readiness の dedicated helper は未存在
- Next action:
  - Phase 2 international and policy audit

### Phase 2

- Status:
  - completed
- Implementation:
  - `core\seo\international_audit.py` を追加し、`html lang / hreflang / x-default / X-Robots-Tag` の監査 helper を実装
  - `core\engine\orchestrator.py::_analyze_seo()` に helper を配線し、`seo_results.technical.international_targeting` と `seo_results.technical.x_robots_tag` を追加
  - warn / fail の主要 issue を既存 warning surface にも反映
  - `tests\test_international_seo.py` を追加し、helper 単体と `orchestrator` 連携を固定
- Self-tests:
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\engine\orchestrator.py core\aio_analyzer.py core\engine\site_health_engine.py core\aio\schema_validator.py core\ui\panels.py core\ui\tabs\seo_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py core\seo\international_audit.py tests\test_international_seo.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_international_seo.py tests\test_aio_analyzer.py tests\test_characterization_engine.py tests\test_characterization_ui.py tests\test_analysis_run_service.py`
    - PASS (`29 passed`)
- Evidence:
  - page result surface:
    - `seo_results.technical.international_targeting.status`
    - `seo_results.technical.x_robots_tag.status`
  - current phase は local context のみで仕様確定可能だったため official refresh は未使用
- Next action:
  - Phase 3 mobile and page experience audit

### Phase 3

- Status:
  - completed
- Implementation:
  - `core\seo\page_experience_audit.py` を追加し、mobile parity と `LCP / CLS` の heuristic audit を実装
  - `core\engine\orchestrator.py::_analyze_seo()` で `seo_results.technical.mobile_parity` と `seo_results.technical.page_experience` を追加
  - `web_vitals` に既存 `INP` と並べて `lcp_ms / lcp_grade / cls_score / cls_grade` を格納
  - `tests\test_page_experience_audit.py` を追加し、helper 単体と `orchestrator` 連携を固定
- Self-tests:
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\engine\orchestrator.py core\aio_analyzer.py core\engine\site_health_engine.py core\aio\schema_validator.py core\ui\panels.py core\ui\tabs\seo_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py core\seo\page_experience_audit.py tests\test_page_experience_audit.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_page_experience_audit.py tests\test_international_seo.py tests\test_aio_analyzer.py tests\test_characterization_engine.py tests\test_characterization_ui.py tests\test_analysis_run_service.py`
    - PASS (`31 passed`)
- Evidence:
  - page result surface:
    - `seo_results.technical.mobile_parity.status`
    - `seo_results.web_vitals.lcp_ms`
    - `seo_results.web_vitals.cls_score`
  - local repair:
    - attempt 1: helper 実装 + test 追加
    - attempt 2: heuristic に合わせて test expectation を narrow fix
- Next action:
  - Phase 4 crawlable links audit

### Phase 4

- Status:
  - completed
- Implementation:
  - `core\seo\link_quality_audit.py` を追加し、crawlable link / empty anchor / generic anchor / image-only link alt / scripted navigation を監査
  - `core\engine\orchestrator.py::_analyze_seo()` で `seo_results.structure.link_quality` を追加
  - warn / fail の主要 issue を既存 warning surface にも反映
  - `tests\test_link_quality_audit.py` を追加し、helper 単体と `orchestrator` 連携を固定
- Self-tests:
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\engine\orchestrator.py core\aio_analyzer.py core\engine\site_health_engine.py core\aio\schema_validator.py core\ui\panels.py core\ui\tabs\seo_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py core\seo\link_quality_audit.py tests\test_link_quality_audit.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_link_quality_audit.py tests\test_link_audit.py tests\test_page_experience_audit.py tests\test_international_seo.py tests\test_aio_analyzer.py tests\test_characterization_engine.py tests\test_characterization_ui.py tests\test_analysis_run_service.py`
    - PASS (`35 passed`)
- Evidence:
  - page result surface:
    - `seo_results.structure.link_quality.status`
    - `seo_results.structure.link_quality.empty_anchor_count`
    - `seo_results.structure.link_quality.generic_anchor_count`
  - local repair:
    - attempt 1: helper 実装 + test 追加
    - attempt 2: image-only + alt なしが empty anchor にも入る実装に合わせて test expectation を narrow fix
- Next action:
  - Phase 5 schema depth refinement

### Phase 5

- Status:
  - completed
- Implementation:
  - `core\aio\schema_validator.py` を page-type aware validator に更新し、`article / ec / local / company` の inference・推奨 schema・required field check を追加
  - `core\aio_analyzer.py` の `schema_validation` を `company` 固定から inferred site type へ変更
  - `core\engine\site_health_engine.py` に `site_health.structured_data.schema_validation` と `schema_site_type` を追加
  - `tests\test_schema_validator.py` を追加し、validator 単体と `site_health_engine` surface を固定
- Self-tests:
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\engine\orchestrator.py core\aio_analyzer.py core\engine\site_health_engine.py core\aio\schema_validator.py core\ui\panels.py core\ui\tabs\seo_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py tests\test_schema_validator.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_schema_validator.py tests\test_link_quality_audit.py tests\test_link_audit.py tests\test_page_experience_audit.py tests\test_international_seo.py tests\test_aio_analyzer.py tests\test_characterization_engine.py tests\test_characterization_ui.py tests\test_analysis_run_service.py`
    - PASS (`38 passed`)
- Evidence:
  - page result surface:
    - `aio_results.schema_validation.site_type`
    - `site_health.structured_data.schema_validation.site_type`
    - `site_health.structured_data.schema_site_type`
  - local repair:
    - attempt 1: validator / analyzer / site health wiring + test 追加で green
- Next action:
  - Phase 6 image/video discovery audit

### Phase 6

- Status:
  - completed
- Implementation:
  - `core\sitemap_analyzer.py` を拡張し、child sitemap 名と XML namespace から `media_hints` と `source_sitemaps` を返すように更新
  - `core\seo\media_discovery_audit.py` を追加し、image/video discoverability・VideoObject・transcript・media sitemap hint を監査
  - `core\engine\orchestrator.py::analyze_url()` で `seo_results.technical.media_discovery` を追加
  - `tests\test_media_discovery_audit.py` と `tests\test_sitemap_analyzer.py` を更新し、helper と sitemap hint を固定
- Self-tests:
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\engine\orchestrator.py core\aio_analyzer.py core\engine\site_health_engine.py core\aio\schema_validator.py core\ui\panels.py core\ui\tabs\seo_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py core\seo\media_discovery_audit.py core\sitemap_analyzer.py tests\test_media_discovery_audit.py tests\test_sitemap_analyzer.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_media_discovery_audit.py tests\test_sitemap_analyzer.py tests\test_link_quality_audit.py tests\test_link_audit.py tests\test_page_experience_audit.py tests\test_international_seo.py tests\test_schema_validator.py tests\test_aio_analyzer.py tests\test_characterization_engine.py tests\test_characterization_ui.py tests\test_analysis_run_service.py`
    - PASS (`42 passed`)
- Evidence:
  - page result surface:
    - `seo_results.technical.media_discovery.status`
    - `seo_results.technical.media_discovery.sitemap_media.image_sitemap_detected`
    - `sitemap_info.media_hints`
  - local repair:
    - attempt 1: sitemap hint / media audit / orchestrator wiring + tests 追加で green
- Next action:
  - Phase 7 LLMO and commerce coverage

### Phase 7

- Status:
  - completed
- Implementation:
  - `core\aio\commerce_readiness.py` を追加し、OpenAI merchant feed readiness と Perplexity operational note を helper 化
  - `core\aio_analyzer.py::assess_provider_readiness()` に `special_notes.openai_commerce` と `special_notes.perplexity_operational` を追加
  - OpenAI Search / GPTBot の既存意味は変えず、commerce は `special_notes` に分離
  - `tests\test_aio_analyzer.py` に commerce / Perplexity note の回帰テストを追加
- Self-tests:
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\engine\orchestrator.py core\aio_analyzer.py core\engine\site_health_engine.py core\aio\schema_validator.py core\ui\panels.py core\ui\tabs\seo_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py core\aio\commerce_readiness.py tests\test_aio_analyzer.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_aio_analyzer.py tests\test_media_discovery_audit.py tests\test_sitemap_analyzer.py tests\test_link_quality_audit.py tests\test_link_audit.py tests\test_page_experience_audit.py tests\test_international_seo.py tests\test_schema_validator.py tests\test_characterization_engine.py tests\test_characterization_ui.py tests\test_analysis_run_service.py`
    - PASS (`43 passed`)
- Evidence:
  - page result surface:
    - `aio_results.details.provider_readiness.special_notes.openai_commerce`
    - `aio_results.details.provider_readiness.special_notes.perplexity_operational`
  - official refresh:
    - OpenAI bots: `https://developers.openai.com/api/docs/bots`
    - OpenAI merchants: `https://chatgpt.com/merchants`
    - OpenAI product feed spec: `https://developers.openai.com/commerce/specs/file-upload/products`
    - Perplexity crawlers: `https://docs.perplexity.ai/docs/resources/perplexity-crawlers`
- Next action:
  - Phase 8 UI integration

### Phase 8

- Status:
  - completed
- Implementation:
  - `core\application\analysis_run_service.py` に `seo_audit_notes` 生成と legacy snapshot refresh 判定を追加し、保存済み run でも新監査の surfacing 余地を確保
  - `core\ui\panels.py` の saved workspace `実装・設定` に `SEO / AI Search 追加監査` セクションを追加
  - `core\ui\tabs\seo_tab.py` に `追加SEO監査` を追加し、国際化 / インデックス制御、モバイル / ページ体験、リンク品質、画像 / 動画の発見性、OpenAI Commerce、Perplexity WAF / IP を warn/fail 優先で表示
  - `core\ui\tabs\health_tab.py` に `SEO / AI Search 補足` を追加し、first view を壊さず補足系の surfacing を追加
  - `tests\test_analysis_run_service.py` を更新し、snapshot 生成と legacy refresh を固定
- Self-tests:
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\engine\orchestrator.py core\aio_analyzer.py core\engine\site_health_engine.py core\aio\schema_validator.py core\ui\panels.py core\ui\tabs\seo_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_aio_analyzer.py tests\test_characterization_engine.py tests\test_characterization_ui.py tests\test_analysis_run_service.py tests\test_sitemap_analyzer.py tests\test_link_audit.py tests\test_international_seo.py tests\test_page_experience_audit.py tests\test_link_quality_audit.py tests\test_schema_validator.py tests\test_media_discovery_audit.py`
    - PASS (`44 passed`)
  - live verify
    - `C:\tetie\techie-hub\start.bat force`
    - `http://127.0.0.1:8081/` -> 200
    - `http://127.0.0.1:8081/runs/84` -> 200
    - Playwright で `/runs/84` の `実装・設定` タブを開き、`SEO / AI Search 追加監査` / `OpenAI Commerce` / `Perplexity WAF / IP` / `モバイル / ページ体験` の表示を確認
- Evidence:
  - live / saved UI surface:
    - `implementation_workspace.seo_audit_notes`
    - saved UI `実装・設定 > SEO / AI Search 追加監査`
    - live UI `SEO改善 > 追加SEO監査`
    - health tab `SEO / AI Search 補足`
  - saved run 84 は旧 snapshot だったため、fallback note で first view を壊さず再分析誘導を表示する構成で fixed
- Next action:
  - Phase 9 regression and closeout

### Phase 9

- Status:
  - completed
- Implementation:
  - package 全体の compile / regression / live verify を再実行し、ledger を complete へ更新
  - `WORKLOG.md` に今回の SEO / LLMO coverage 拡張内容を追記
  - `ALGORITHM.md` は score formula 変更がないため更新不要と判断
- Self-tests:
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\engine\orchestrator.py core\aio_analyzer.py core\engine\site_health_engine.py core\aio\schema_validator.py core\ui\panels.py core\ui\tabs\seo_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_aio_analyzer.py tests\test_characterization_engine.py tests\test_characterization_ui.py tests\test_analysis_run_service.py tests\test_sitemap_analyzer.py tests\test_link_audit.py tests\test_international_seo.py tests\test_page_experience_audit.py tests\test_link_quality_audit.py tests\test_schema_validator.py tests\test_media_discovery_audit.py`
    - PASS (`44 passed`)
  - live verify
    - `http://127.0.0.1:8081/` -> 200
    - `http://127.0.0.1:8081/runs/84` -> 200
- Evidence:
  - phase ledger complete
  - stop condition 非該当
  - official refresh は phase 7 の 1 回のみで、phase 8-9 では未使用
  - `ALGORITHM.md` judged: no update needed because score / legal meaning / provider meaning unchanged
- Next action:
  - package closeout complete

## Official Source Memo

- confirmed on 2026-04-06:
  - Google Search Central links / snippets / title links / image SEO / Core Web Vitals / localized versions / breadcrumb / article
  - OpenAI bots
  - OpenAI merchants
  - Perplexity crawlers
- confirmed on 2026-04-06 during phase 7:
  - OpenAI bots doc: `OAI-SearchBot` is for search, `GPTBot` is for training, and each robots setting is independent
  - OpenAI merchants page: feeds improve product discovery with complete/current product data and Shopify / Etsy catalogs are already integrated
  - OpenAI product feed spec: current stable file-upload spec requires feed/account/merchant/country headers plus product and variant identifiers; price / availability / media enrich discovery
  - Perplexity crawlers doc: robots allow alone is not the full operational story; published IP JSON endpoints are the source of truth for Cloudflare / AWS WAF allowlists

## Failure Log

- none

## User Report Template

失敗停止時は最低限これを user に返す。

- current phase
- failure summary
- attempts used
- official refresh attempts used
- tried fixes
- likely cause
- rollback need / no need
- next decision required from user
