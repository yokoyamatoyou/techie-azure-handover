# seo_llmo_coverage_2026-04-06

`aio2-main` の分析機能を、2026-04-06 時点の **一般 SEO / AI Search / LLMO の最新ベストプラクティス** に照らして不足なく拡張するための execution package。

この package は、別ウィンドウの Codex がそのまま実装に入れるように次を current source of truth として固定する。

- phase map
- owner scope
- baseline gap matrix
- official-source refresh rule
- self-test gate
- retry / stop / rollback rule
- restart prompt

## Objective

- `aio2-main` の SEO / AIO 分析を、現時点の主要ベストプラクティスに対して「何を見ているか」「何を見ていないか」が曖昧でない状態にする
- 一般 SEO と LLMO / AI Search を混同せず、`official check / heuristic note / informational note` の境界を維持したまま coverage を拡張する
- UI でも新しい監査結果が読めるようにし、非エンジニアが「今どこが抜けているか」を短時間で判断できるようにする
- Codex が phase ごとに narrow fix し、自己テストを通したあとにだけ次 phase へ進める

## Package Role

- `README.md`
  - package の目的、read order、baseline findings、phase summary、success criteria を定義する
- `TASK.md`
  - phase / gate / retry / stop / self-test / web refresh rule を固定する
- `PROGRESS.md`
  - current phase、attempt、evidence、phase ledger、failure log を管理する
- `ROLLBACK.md`
  - rollback boundary、do-not-retry、stop condition を固定する
- `EXECUTION_PROMPT.md`
  - 別ウィンドウでそのまま貼れる再開 prompt を保持する
- `artifacts\`
  - verify memo、official source memo、必要時 screenshot の置き場

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\aio2-main\AGENTS.md`
3. `C:\tetie\aio2-main\ALGORITHM.md`
4. `C:\tetie\aio2-main\WORKLOG.md`
5. `C:\tetie\aio2-main\plan\CURRENT_AND_NEXT_IMPROVEMENTS.md`
6. `C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\README.md`
7. `C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\TASK.md`
8. `C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\PROGRESS.md`
9. `C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\ROLLBACK.md`
10. `C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\EXECUTION_PROMPT.md`

## Latest Confirmed External Baseline

2026-04-06 時点で確認済みの primary / official source:

- Google Search Central
  - links: `https://developers.google.com/search/docs/crawling-indexing/links-crawlable`
  - snippets: `https://developers.google.com/search/docs/appearance/snippet`
  - title links: `https://developers.google.com/search/docs/appearance/title-link`
  - image SEO: `https://developers.google.com/search/docs/appearance/google-images`
  - Core Web Vitals: `https://developers.google.com/search/docs/appearance/core-web-vitals`
  - localized versions / hreflang: `https://developers.google.com/search/docs/specialty/international/localized-versions`
  - breadcrumb: `https://developers.google.com/search/docs/appearance/structured-data/breadcrumb`
  - article structured data: `https://developers.google.com/search/docs/appearance/structured-data/article`
- OpenAI
  - bots: `https://developers.openai.com/api/docs/bots`
  - merchants / product discovery: `https://chatgpt.com/merchants`
- Perplexity
  - crawlers: `https://docs.perplexity.ai/docs/resources/perplexity-crawlers`

この package の実行中、仕様変更が疑われる場合は上記 official source を起点に refresh してよい。

## Current Baseline

2026-04-06 current code 状態:

- internal link structure と link target audit は実装済み
  - `sitemapindex` 集約
  - internal link orphan / depth / hub
  - target HTTP error / redirect / canonical mismatch / noindex
- Google / OpenAI Search / Perplexity / Claude Search の robots gate は実装済み
- `noindex / nosnippet / max-snippet / data-nosnippet` は実装済み
- OGP / Twitter / structured data / FAQ / image alt / llms.txt note は実装済み

ただし、最新ベストプラクティス観点では次が残っている。

### Gap Matrix

| Area | Current State | Gap | Priority |
|------|---------------|-----|----------|
| international SEO | 用語集にあるが分析実装なし | `hreflang`, `x-default`, `html lang`, reciprocal consistency 監査なし | P0 |
| mobile-first | `viewport` のみ | mobile/desktop parity、mobile metadata parity、主要コンテンツ露出確認なし | P0 |
| Core Web Vitals | INP のみ | LCP / CLS 未監査 | P0 |
| robots / metadata policy | page meta は一部監査 | `X-Robots-Tag`, `noimageindex`, `max-image-preview`, `max-video-preview` など未監査 | P0 |
| links SEO quality | structure と a11y のみ | crawlable link element, empty anchor, image-as-link alt, generic anchor text の SEO 監査不足 | P1 |
| schema depth | company 固定が多い | page-type 別 (`article`, `ec`, `local`) の妥当性チェックが弱い | P1 |
| image discovery | alt と OGP 中心 | image sitemap, HTML image discoverability, image URL consistency の監査不足 | P1 |
| video discovery | `VideoObject` note はある | video sitemap / transcript / indexability の一般 SEO 監査が弱い | P2 |
| OpenAI commerce readiness | bots は実装済み | ChatGPT shopping 向け product feed readiness 未監査 | P1 |
| Perplexity operational readiness | robots は実装済み | published IP / WAF allowlist readiness note 未監査 | P2 |
| UI surfacing | current cards に未項目 | 新しい監査結果の表示場所・圧縮方法の設計が必要 | P0 |

## Scope

この package が扱うのは次だけ。

- `core/engine/orchestrator.py` の SEO 分析対象拡張
- 新規 SEO audit module 追加
- `core/aio_analyzer.py` の provider / informational note 拡張
- `core/engine/site_health_engine.py` の structured data / health 連携改善
- `core/application/analysis_run_service.py` の snapshot / workspace 整形反映
- `core/ui/panels.py`, `core/ui/tabs/seo_tab.py`, `core/ui/tabs/health_tab.py` の表示追加
- 必要最小限の test 追加
- progress / execution docs

この package が扱わないもの:

- score formula の全面改定
- LLM prompt strategy の全面改修
- legal meaning の変更
- unrelated UI redesign
- `C:\tetie\zip` mock 変更

## Design Constraints

- `official check / heuristic / informational` の境界は維持する
- `llms.txt` を hard requirement にしない
- OpenAI Search と GPTBot を混同しない
- general SEO と AI Search 専用条件を混同しない
- 新しい監査項目を増やしても first view を overload しない
- live / saved parity を崩さない
- 既存 owner file の責務を保ち、巨大ファイルへの追記で逃げず、必要なら小さな helper module を追加する
- 1 phase で複数領域をまとめて広げない。変更面積は current phase の owner scope に閉じる
- UI は summary-first を維持し、詳細は tab / internal diagnosis / expansion に逃がして肥大化を避ける
- ALGORITHM とズレる場合は最後に更新要否を明示する

## Success Criteria

- `hreflang / mobile-first / X-Robots-Tag / LCP / CLS / crawlable links / schema depth / image discovery / commerce readiness` のうち、少なくとも P0/P1 領域で current mainline が明示監査できる
- UI で新しい監査結果が読めるが、warn/fail 優先の圧縮表示になっている
- official source refresh を phase ごとに記録できる
- targeted tests / compile が green
- 別ウィンドウの Codex が `PROGRESS.md` と `TASK.md` だけで再開できる

## Phase Summary

| Phase | Name | Goal |
|------|------|------|
| 0 | package bootstrap | docs / ledger / prompt を固定する |
| 1 | baseline matrix lock | current gaps と owner map を固定する |
| 2 | international and policy audit | `hreflang / html lang / X-Robots-Tag` を追加する |
| 3 | mobile and page experience audit | mobile-first parity と `LCP / CLS` を追加する |
| 4 | crawlable links audit | crawlable links / anchor text / image-as-link を追加する |
| 5 | schema depth refinement | page-type 別 schema validation を拡張する |
| 6 | image/video discovery audit | image/video discovery と sitemap 系を追加する |
| 7 | LLMO and commerce coverage | OpenAI merchants / Perplexity operational readiness を追加する |
| 8 | UI integration | live / saved UI に warn/fail 優先で反映する |
| 9 | regression and closeout | tests / docs / residual risk を確定する |

## Owner Map

- engine owner:
  - `C:\tetie\aio2-main\core\engine\orchestrator.py`
- AI/search gate owner:
  - `C:\tetie\aio2-main\core\aio_analyzer.py`
- site health / schema owner:
  - `C:\tetie\aio2-main\core\engine\site_health_engine.py`
  - `C:\tetie\aio2-main\core\aio\schema_validator.py`
- UI owner:
  - `C:\tetie\aio2-main\core\ui\panels.py`
  - `C:\tetie\aio2-main\core\ui\tabs\seo_tab.py`
  - `C:\tetie\aio2-main\core\ui\tabs\health_tab.py`
- snapshot owner:
  - `C:\tetie\aio2-main\core\application\analysis_run_service.py`
- test owner:
  - `C:\tetie\aio2-main\tests\`

## Operating Rule

- Codex は 1 回に 1 phase だけ進める
- 各 phase で official source refresh の要否を確認する
- 各 phase は `実装 -> 自己テスト -> `PROGRESS.md` 更新 -> gate 判定` の順で処理する
- gate green の場合は user に都度確認せず、次 phase へ自律的に進む
- エラー時は同一 phase 内で最大 3 回まで自力修正する
- 3 回でも修正不能なら停止し、user に failure summary を返す
- 停止条件に触れない限り、phase 9 まで完走する
- bug / error は local repair を優先し、仕様不明時のみ official source を再参照する
- 同一 failure で official source refresh は最大 3 回
