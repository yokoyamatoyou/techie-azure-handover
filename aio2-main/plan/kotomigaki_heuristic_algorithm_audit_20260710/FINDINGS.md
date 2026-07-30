# Findings

## 1. 重大度定義

| 優先度 | 定義 |
|---|---|
| P0 | 現行利用で重大な漏えい、破壊、または安全上の緊急停止が確認された状態 |
| P1 | 意思決定の真偽、公開前の安全、主要導線、アクセシビリティを壊す。次の bounded owner で修正する状態 |
| P2 | 誤解、保守負債、基準ずれ、二次的な安全性を生む。P1 の契約確定後に修正する状態 |
| P3 | polish、説明補強、低頻度 edge case |

P0 は確定していない。以下の P1 12 件、P2 8 件を記録する。

## 2. P1 findings

### F-01 Provider bot 判定が取得失敗を合格へ変換する

- 状態: fail
- 根拠: `core/aio_analyzer.py:278-343` は provider を pass で初期化し、bot access が明示的に `False` の場合だけ fail にする。robots 取得失敗/non-200 は `:1117-1146` で error と空 map になり、pass が残る。parser は `:141-174` で root の `/` / `/*` しか見ず、分析対象 path の規則を評価しない。`X-Robots-Tag` は `core/engine/orchestrator.py:3151-3164` の別系統で provider gate に入らない。
- 安全な再現: `bot_access={}`, `errors=['robots fetch failed']` を判定器へ渡すと全 provider が pass。`Disallow: /private` では対象 path に対する access が `None`。
- 影響: 「利用可能」と「確認できない」を逆転させ、LLMO 対応判断を誤らせる。
- owner / 対象: provider-readiness owner / `core/aio_analyzer.py`, `core/engine/orchestrator.py`。
- 受入条件: provider ごとに `pass/fail/unverified/not-applicable`。robots の対象 URL path、user-agent precedence、HTTP/meta `X-Robots-Tag` を一つの証拠モデルへ統合し、timeout/non-200 は明示的 unverified になる。

### F-02 業界補正後のスコアが 100 を超え、重点配分が逆になる

- 状態: fail
- 根拠: `core/scoring_engine.py:71-93,132-160` は industry boost を上限なしで加算し、`seo_focus` / `aio_focus` を不足側ではなく高得点側へ寄せる。
- 安全な再現: SEO=90, AIO=90, ecommerce で SEO=117、integrated=103.5。SEO=90, AIO=50 で SEO focus=83%、AIO focus=17%。
- 影響: 100 点尺度の意味が壊れ、優先投資が不足領域と逆になる。
- owner / 対象: scoring-contract owner / `core/scoring_engine.py`。
- 受入条件: 全公開点数を `[0,100]` に clamp する前に補正規則を明文化。focus は gap、risk、effort を基にし、低 AIO の fixture で AIO 側が高くなる。旧結果 migration 表示も定義する。

### F-03 公開 SEO スコアが重要所見と分離している

- 状態: fail
- 根拠: `core/engine/orchestrator.py:3371-3391` は title、description、H1、word count、canonical、内部/外部 link の 7 加点。canonical は非空なら加点 (`:3521-3525`)。日本語に不向きな空白区切り語数 (`:3169-3172,3487-3493`) と link count (`:3495-3501`) を用いる。noindex、malformed canonical、broken link、国際 SEO、mobile、media、sitemap の詳細所見は別経路 (`:3038-3290,1340-1474`)。
- 影響: 検索不可や正規 URL の誤りがあっても高得点に見える。
- owner / 対象: SEO score owner / orchestrator の SEO evidence と score builder。
- 受入条件: hard gate、graded evidence、unverified を分離。日本語本文量は文字/形態素/DOM main-content のいずれかを明示。各公開点数から根拠所見へ追跡できる。

### F-04 Schema.org `@graph` / 入れ子を正しく評価できず、複数 validator が競合する

- 状態: fail
- 根拠: `core/aio/schema_validator.py:52-69,119-172,190-201` は top-level `@type` 前提。正しい `@graph` 内 Product/Offer fixture が `found_types=['']`、全推奨 missing、score=30 になる。一方 `core/engine/orchestrator.py:3064-3144` と `core/application/technical_summary_builder.py:909-916` に別判定がある。
- 影響: 正しい実装を未実装と誤認し、修正提案と点数が画面ごとに変わる。
- owner / 対象: structured-data evidence owner / validator と各 adapter。
- 受入条件: JSON-LD graph を再帰的に正規化する単一 parser。複数 block、配列、`@graph`、nested Offer、invalid JSON の contract fixture を全 consumer で共用する。

### F-05 LLM 文章改善が根拠との entailment を検証しない

- 状態: fail
- 根拠: `core/aio_suggestions.py:273-284` は具体的事実・数値を強めるよう求めるが、`:88-103,303-318` の検証は schema/文字列 sanitize で、source evidence との一致を確認しない。結果は `core/engine/orchestrator.py:3803-3813` で High impact へ昇格する。deep citation prompt は強い境界を持つ (`orchestrator.py:5103-5432`) が、`core/citation_generator.py:91-108` は `sample_sentence` を根拠照合せず採用する。
- 安全な再現: fixture の `sample_sentence` に source にない数値を入れても受理される。
- 影響: 公開文章へ架空の実績・数値・因果を持ち込む可能性。
- owner / 対象: grounded-rewrite owner / suggestion、citation、technical summary。
- 受入条件: sentence ごとに source span / URL / evidence id を必須化。根拠なしの固有名・数値・比較級を reject または「要確認」へ隔離する。

### F-06 優先アクションが UI と export で同じリストではない

- 状態: fail
- 根拠: `core/application/analysis_run_service.py:906-926` が priority actions を作り、`:1520-1574` の workspace 構築で法務を再追加し UI 専用 search-intent も追加する。`core/ui/saved_workspace.py:371-405` は先頭 3 件、最大 5 件だけを表示する一方、CSV/Markdown は `exports.priority_actions` (`analysis_run_service.py:1928-1930`, `csv_export_service.py:33-54`, `markdown_report_service.py:583-590`) を使用する。
- 影響: 画面で見た「最優先」と持ち出した文書の「最優先」が一致しない。9 件目以降は UI から到達不能になり得る。
- owner / 対象: **次実装 owner** / `analysis_run_service.py`, `saved_workspace.py`, export services。
- 受入条件: canonical action list に stable id、priority、audience、evidence、status を持たせ、全 surface は同じ slice/order/count rule を使う。snapshot contract test で UI/CSV/MD/DOCX の上位 ID を一致させる。

### F-07 保存結果の GET が snapshot を書換え、競合情報を失い得る

- 状態: fail
- 根拠: `core/application/analysis_run_service.py:2034-2049` は初回 competitor 引数を受けるが、旧 bundle refresh は `:2101-2109` で competitor を渡さず再構築し、`:2111-2118` で DB へ書き戻す。欠落値は `:1747-1748` で空になる。ルートは `nicegui_app.py:1180-1225`。
- 影響: 閲覧だけで監査証跡が変わり、比較対象が消える。再現性と read-only expectation を破る。
- owner / 対象: **次実装 owner** / saved bundle load/migration。
- 受入条件: GET は無書込。旧 snapshot の変換は memory-only view adapter とし、明示 migration command だけが versioned backup とともに書く。競合 fixture の before/after byte equality を検証する。

### F-08 `unknown/unverified` が「参考」へ丸められる

- 状態: fail
- 根拠: `core/ui/panel_components.py:212-231`、`core/ui/tabs/seo_tab.py:11-46`、`core/application/analysis_run_service.py:396-415` は absent/unknown を reference 表示へ寄せる。一方 `core/ui/tabs/aio_tab.py:47-53` は未確認を明示する。
- 影響: 実測できていないリスクを低リスクの参考情報に見せる。
- owner / 対象: **次実装 owner** / snapshot semantic adapter と UI badge。
- 受入条件: `pass/fail/unverified/not-applicable/error` を end-to-end で保持し、色だけでなく日本語ラベル・理由・取得時刻を表示する。

### F-09 コトミガキ UI 自身の支援技術対応が不足する

- 状態: fail（コード監査。実ブラウザは未確認）
- 根拠: `nicegui_app.py:652-669` の見出し風 label と別置き error、`:746-869` の状態更新に `aria-live` / `role=status` がなく、`:776-808` に `aria-invalid` / `aria-describedby` / focus 移動がない。`core/ui/dashboard.py:281-318` の mobile history は click card だが button/link semantics、tabindex、Enter/Space handler がない。focus-visible 基本 CSS は `core/ui/styles.py:6` にある。
- 影響: キーボード利用者が履歴へ入れず、screen reader 利用者が進行・完了・失敗を把握しにくい。
- owner / 対象: NiceGUI accessibility owner。
- 受入条件: landmark/heading、live region、入力-error 関連付け、native interactive history。ホーム→分析→完了→保存結果→export を keyboard only で完走し、axe WCAG 2.2 AA Critical/Serious 0。

### F-10 内蔵 browser accessibility 検査が現環境で無効、かつ基準が古い

- 状態: fail
- 根拠: `core/site_health/browser_accessibility_scanner.py:44-52` は Node 依存が揃う場合だけ有効。現環境は `browser_accessibility_enabled() == False` で `tools/accessibility_scanner/node_modules` がない。fallback は `core/site_health/accessibility_checker.py:13-23,459-518` の HTML 軽量項目に限る。scanner の `safeUrlScanner.mjs:23-25` と `scoring.mjs:4,744` は WCAG 2.0 A/AA / JIS 2016 profile で、WCAG 2.2 AA ではない。
- 影響: contrast、focus、keyboard、zoom 等を検査せず高評価になり得る。
- owner / 対象: accessibility scanner packaging owner。
- 受入条件: 配布物で browser source が既定有効。欠落時は「HTML 限定」と未確認項目を表示し、同じ score scale を使わない。WCAG 2.2 AA tags/profile と manual-check list を versioned 出力する。

### F-11 外部公開時の認証・tenant 境界がない

- 状態: fail（ローカル `127.0.0.1` 既定では緩和、外部公開前 P1 blocker）
- 根拠: `core/storage/database.py:53-64` の run に tenant id がなく、`:227-234` は integer id だけで取得。`nicegui_app.py:1180-1225` の `/runs/{run_id}` と download に認証/認可条件がない。既定 bind は `nicegui_app.py:1247-1269` の localhost。
- 影響: 現状のまま Azure/共有公開すると、他 tenant の run や artifact を列挙参照できる可能性。
- owner / 対象: Azure/auth owner / schema、query、history、compare、download。
- 受入条件: authentication subject から tenant を決定し、全 run/artifact query で tenant 条件を強制。cross-tenant id は 403/404。download は認証 endpoint または短期限 SAS。local-only mode は別 profile として明示する。

### F-12 URL query の秘密値が DB と成果物へ残る

- 状態: fail
- 根拠: `nicegui_app.py:209-225` は scheme/host の検証だけ。`core/safe_fetch.py:106-113` は query を保持し、`core/storage/database.py:123-140` と `analysis_run_service.py:1982-2049` は URL をそのまま保存。CSV は `csv_export_service.py:33-74`、Markdown は `markdown_report_service.py:538-555` へ出す。
- 影響: signed URL、token、session、auth code が DB/JSON/UI/export/log に永続化され得る。
- owner / 対象: URL privacy owner / validator、persistence、logging、全 export。
- 受入条件: fetch 用 raw URL は run-memory 内だけ。表示・保存・log・export 前に一元 redaction。userinfo を拒否し、代表的 key と case/encoding の fixture を追加する。

## 3. P2 findings

### F-13 将来日付を最高 freshness とする

- 根拠: `core/aio_analyzer.py:1660-1722` はページ内最大日付を採用し、将来日付で months が負でも score=1.0。2099 fixture で再現。
- 対応: future skew tolerance を設け、将来日付は invalid/unverified。published/modified/copyright を役割別に扱う。

### F-14 link timeout を broken と断定する

- 根拠: `core/seo/link_audit.py:116-132` と `core/application/technical_summary_builder.py:519-526`。
- 対応: `broken/unverified/blocked/rate-limited` を分け、status・attempt・timestamp を保持する。

### F-15 Core Web Vitals 風の数値が固定 proxy である

- 根拠: `core/seo/page_experience_audit.py:81-101,156-165` の固定計算、`core/ui/tabs/seo_tab.py:103-114` と `analysis_run_service.py:1173-1189` の表示。
- 対応: field/lab source、device、sample、timestamp がない場合は LCP/CLS 数値を出さず「未測定」と risk factors を表示する。

### F-16 FAQ / speakable / AI 可視性の表現が現行仕様より強い

- 根拠: `core/structured_data/schema_suggester.py:19-46`、`technical_summary_builder.py:887-905`、`citation_generator.py:119-151`、`simulation_tab.py:15-68`。`nicegui_app.py:386-388` 等には「AI引用率+30〜40%」「直結」の因果表現がある。
- 公式差分: Google は 2026-06-15 に FAQ rich result 文書を削除し、`llms.txt` は不要で visibility への正負効果がないと更新した。speakable は beta / 限定条件。AI 機能にも特別 schema や AI file の要件・掲載保証はない。
- 対応: 「実装可能」と「効果実証」を分け、適用 eligibility、公式更新日、保証なしを表示する。

### F-17 JS scanner に port / DNS rebinding 残余がある

- 根拠: `tools/accessibility_scanner/urlSafety.mjs:110-147` は private IP を検査するが port allowlist がない。`safeUrlScanner.mjs:93-133,267-277` は hostname 単位の DNS 判定を cache し、Chromium の接続先 IP を pin しない。
- 対応: port allowlist、request/hop ごとの再検証、hostname-only cache の廃止または IP pin、mock rebind 回帰。

### F-18 CSV 境界と履歴 export のローカルパス露出

- 根拠: `core/application/csv_export_service.py:14-18` は ASCII `=+-@`、tab、CR を apostrophe prefix するが、Unicode whitespace/control 境界は未検証。history export は `:77-98` で `result_path` を出す。
- 対応: OWASP 想定の delimiter/newline/encoding fixture を追加。履歴 export から内部絶対 path を除外し artifact id に置換する。

### F-19 DOCX は視覚的見出し・表だが文書アクセシビリティ metadata が不足する

- 根拠: `core/application/docx_report_service.py:93-152,242-317`。先頭 title は通常段落で、document language/core title、table header semantics/description がない。
- 対応: Word Accessibility Checker を acceptance に含め、title/heading/lang/table/link semantics を追加する。

### F-20 固定脆弱性 DB と current docs に残余不整合がある

- 根拠: `core/vulnerability_intelligence.py:165-201,250-269` は `sqlite3.connect(db_path)` で `mode=ro` / `query_only` を強制しない。range parser (`:369-405`) は数値比較中心。robots owner が `core/robots_analyzer.py` と orchestrator に重複し、`core/config.py:31` の既定 model と `core/llm_responses_client.py:51-56,185-190` の temperature drop は docs の温度表現とずれる。
- 対応: DB を immutable/read-only URI で開き、複雑 range/prerelease fixture を追加。robots と LLM parameter の current owner を docs と code で一つにする。

## 4. 確認できた強み

- `core/safe_fetch.py:20-374` は scheme/port/private・非 global IP制限、検証済み IP への接続固定、各 redirect 再検証、byte/timeout/redirect 上限を持つ。`tests/test_safe_fetch_security.py:65-166` に DNS rebind、private redirect、localhost、port 回帰がある。
- `core/engine/orchestrator.py:1120-1230` の優先 crawl は最大 8 page、各 2 MB、15 秒、15,000 文字に制限される。endpoint health も固定少数 endpoint、256 KB、4 秒、redirect 2。
- unsafe HTML の主要入力は escape/sanitize を通る。Markdown table/HTML escape と CSV formula prefix が存在する。
- 固定脆弱性 intelligence は exploit 本文を保持しない設計境界を持つ。
- `run_app.py:37-60` に 10 MB × 5 世代の log rotation がある。

## 5. 未確認

- 実ブラウザ視覚 QA、console/page error、screen reader、keyboard、zoom、axe
- live URL/API 分析、provider robots の実ネットワーク挙動
- dependency advisory/CVE scan（`pip check` は整合確認のみ）
- Azure authentication/SAS/tenant isolation の実環境
- Word Accessibility Checker
- 背景 runtime が監査中に更新した data file の意味。監査はそれらを入力証拠として使用していない

