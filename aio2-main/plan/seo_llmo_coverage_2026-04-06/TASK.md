# seo_llmo_coverage_2026-04-06 TASK

このファイルは、別ウィンドウの Codex が迷わず完走するための **phase / gate / retry / stop / official refresh rule** を固定する。

## Global Rules

- analysis logic の意味づけ、score formula、legal meaning は勝手に変えない
- 1 回に 1 phase だけ進める
- phase 開始前に owner scope を固定する
- phase ごとに自己テストする
- phase ごとに `PROGRESS.md` を更新する
- gate green 以外では次 phase に進まない
- gate green なら user 確認待ちにせず、自律的に次 phase へ進む
- 同一 phase 内の自己修正は最大 3 回
- 3 回で直らなければ停止し、failure summary を user に報告する
- stop condition に触れない限り、phase 9 まで完走する
- bug / error で詰まった場合、ローカル修正を優先し、それでも仕様が確定しない場合のみ official source refresh を行う
- official source refresh は **同一 failure につき最大 3 回**
- `C:\tetie\zip` は mock として参照のみ。変更しない
- current phase の owner scope を越える refactor をしない
- 巨大化回避を優先し、既存巨大ファイルに処理を継ぎ足す前に小さな helper module 追加で閉じ込められないか検討する
- UI は first view の summary-first を維持し、新規詳細は tab / expansion / internal diagnosis に後退させる

## Gates

### Entry Gate

- `README.md / TASK.md / PROGRESS.md / ROLLBACK.md / EXECUTION_PROMPT.md` が揃っている
- current scope と non-scope が docs に明記されている
- baseline gap matrix と success criteria が `README.md` にある
- current phase と phase ledger が `PROGRESS.md` にある

### Phase Pass Gate

- phase-specific 実装が owner scope で完了している
- required self-tests が pass している
- required evidence が `PROGRESS.md` に記録されている
- official source refresh を使った場合、query / source / inference / decision が `PROGRESS.md` に記録されている

### Auto-Advance Gate

- current phase の status が `completed`
- next phase の objective / owner / checks / risks が `PROGRESS.md` に初期化済み
- stop condition に該当しない
- ここを満たした場合は、そのまま次 phase へ進む。phase 間で user 確認は挟まない

### Stop Gate

- 同一 phase で 3 回失敗
- official source refresh を 3 回使っても仕様が確定しない
- score / legal / provider meaning の変更が必要
- rollback 不能な差分が必要
- UI で重大 regression が出る

## Shared Check Commands

### Compile Gate

```text
C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\engine\orchestrator.py core\aio_analyzer.py core\engine\site_health_engine.py core\aio\schema_validator.py core\ui\panels.py core\ui\tabs\seo_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py
```

### Targeted Regression Gate

```text
C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_aio_analyzer.py tests\test_characterization_engine.py tests\test_characterization_ui.py tests\test_analysis_run_service.py
```

### SEO / Sitemap / Link Audit Extended Gate

```text
C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_sitemap_analyzer.py tests\test_link_audit.py
```

### Optional New Test Gate

phase 2-8 では対象機能に応じて次を追加してよい。

```text
C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_seo_meta_policy.py tests\test_international_seo.py tests\test_page_experience_audit.py
```

存在しない場合は新規追加してから使う。

## Live Verify Gate

```text
C:\tetie\techie-hub\start.bat force
```

確認対象:

- `http://127.0.0.1:8081/`
- `http://127.0.0.1:8081/runs/{run_id}`

確認ポイント:

- `SEO改善` / `サイトヘルス` / `内部診断` に新しい監査結果が反映されている
- first view で warn/fail が埋もれていない
- live / saved で主要項目の表示差がない

## Official Source Refresh Rule

以下すべてを満たす場合のみ Web 検索 / open を使う。

- local context だけでは仕様が確定しない
- 仕様が変わりうる
- official / primary source が存在する

優先 source:

1. Google Search Central
2. OpenAI official docs / official product pages
3. Perplexity official docs
4. それ以外の official primary source

同一 failure で必ず記録する項目:

- query
- source URL
- confirmed fact
- implementation decision
- 未確定の残り

## Evidence Rule

- phase ごとに最低限 `PROGRESS.md` へ verify memo を残す
- UI 変更 phase では screenshot または live observation memo のどちらかを残す
- official source refresh を使った phase では、参照 source を `artifacts\README.md` または `PROGRESS.md` に残す

## Failure Handling Protocol

### Local Repair Sequence

1. failing test / failing route / failing serializer を固定する
2. owner file のみで narrow fix を試す
3. Compile Gate / affected pytest を再実行する
4. 1-3 を最大 3 回まで繰り返す
5. 3 回失敗したら停止し、user に報告する

### Official Refresh Sequence

以下のどちらかに該当するときだけ使う。

- best practice や supported property が current memory だけでは断定できない
- provider ごとの robots / feed / metadata policy が変化しうる

## Phase Map

### Phase 0: package bootstrap

- Objective:
  - execution package と restart protocol を固定する
- Owner:
  - docs only
- Required checks:
  - Entry Gate review
- Exit:
  - docs 5 点 + artifacts dir が揃っている

### Phase 1: baseline matrix lock

- Objective:
  - current owner map、gap matrix、UI impact matrix、test plan を固定する
- Owner:
  - docs + repository inspection
- Required checks:
  - Compile Gate
- Exit:
  - `PROGRESS.md` に baseline findings と phase order が記録されている

### Phase 2: international and policy audit

- Objective:
  - `hreflang / x-default / html lang / X-Robots-Tag` の監査を追加する
- Owner:
  - new SEO audit helper
  - `core\engine\orchestrator.py`
  - optional `core\aio_analyzer.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - new unit tests
- Exit:
  - page result に international/meta policy summary が存在する
  - `X-Robots-Tag` の主要値が判断できる

### Phase 3: mobile and page experience audit

- Objective:
  - mobile-first parity と `LCP / CLS` を追加する
- Owner:
  - new page experience helper
  - `core\engine\orchestrator.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - new unit tests
- Exit:
  - `INP` だけでなく `LCP / CLS` が返る
  - mobile parity warning を返せる

### Phase 4: crawlable links audit

- Objective:
  - crawlable links / empty anchor / generic anchor / image-as-link alt を追加する
- Owner:
  - new link quality helper
  - `core\engine\orchestrator.py`
  - optional `core\site_health\accessibility_checker.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - `tests\test_link_audit.py`
  - new unit tests
- Exit:
  - Google link best practices に沿う quality warning を返せる

### Phase 5: schema depth refinement

- Objective:
  - `company` 固定から page-type aware な schema validation に寄せる
- Owner:
  - `core\aio\schema_validator.py`
  - `core\engine\site_health_engine.py`
  - optional `core\aio_analyzer.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - new unit tests
- Exit:
  - `article / ec / company / local` で recommended schema が分かれる
  - Article author / URL などの不足が拾える

### Phase 6: image/video discovery audit

- Objective:
  - image/video の discoverability と sitemap 系 warning を追加する
- Owner:
  - new media audit helper
  - `core\engine\orchestrator.py`
  - optional `core\robots_analyzer.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - new unit tests
- Exit:
  - image sitemap / HTML image discoverability / video indexability の summary を返せる

### Phase 7: LLMO and commerce coverage

- Objective:
  - OpenAI merchant feed readiness、Perplexity WAF/IP readiness、provider note の拡張を行う
- Owner:
  - `core\aio_analyzer.py`
  - optional new commerce helper
  - `core\engine\orchestrator.py`
- Required checks:
  - Compile Gate
  - `tests\test_aio_analyzer.py`
  - new unit tests
- Exit:
  - OpenAI Search / GPTBot と merchant feed note が混同されていない
  - Perplexity の robots と WAF/IP note が分離されている

### Phase 8: UI integration

- Objective:
  - 新しい監査結果を live / saved UI に warn/fail 優先で反映する
- Owner:
  - `core\ui\panels.py`
  - `core\ui\tabs\seo_tab.py`
  - `core\ui\tabs\health_tab.py`
  - `core\application\analysis_run_service.py`
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - relevant UI tests
  - live verify
- Exit:
  - first view を壊さず新項目が読める
  - internal diagnosis と tab detail の責務が崩れていない

### Phase 9: regression and closeout

- Objective:
  - docs / tests / residual risks / next action を整理して close する
- Owner:
  - review + docs only
- Required checks:
  - Compile Gate
  - all targeted pytest
  - live verify
- Exit:
  - `PROGRESS.md` ledger complete
  - `WORKLOG.md` 更新
  - `ALGORITHM.md` 更新要否を判断済み

## Required PROGRESS Update Fields Per Phase

各 phase 完了時に最低限これを更新する。

- `Current phase`
- `Status`
- `Attempts used`
- `Official refresh attempts used`
- `Implementation`
- `Self-tests`
- `Evidence`
- `Next action`
- `Failure log` if any

## Do Not Do

- OpenAI Search と GPTBot を同じ gate にする
- `llms.txt` を hard requirement として扱う
- Google の一般 SEO 要件と AI 検索専用 note を同一スコアに混ぜる
- UI で新しい監査項目をそのまま全部並べて可読性を壊す
- unrelated refactor に広げる
- phase をまたいでまとめ実装して ledger を曖昧にする
- 1 つの helper で済む変更を巨大 owner file に直書きして肥大化させる
