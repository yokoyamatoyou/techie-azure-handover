# コトミガキ ALGORITHM

最終更新: 2026-07-10
対象: `C:\tetie\aio2-main`

このドキュメントは、コトミガキ（SEO/AIO分析）の現行アルゴリズム仕様を管理する正本です。  
実装の一次参照は `core/engine/orchestrator.py`, `core/aio_analyzer.py`, `core/scoring_engine.py`。

## 1. 目的

- Webページを対象に、SEO・AIO・法務・サイトヘルスを統合診断する
- スコアだけでなく、実行可能な改善提案と UI / CSV / Markdown / DOCX 出力を提供する

## 2. 分析フロー（概要）

1. 取得・前処理  
URLをクロールし、本文・構造・メタデータを抽出。

2. SEO分析  
SEO系指標を算出し `seo_results` を生成。

3. AIO分析（`AIOContentAnalyzer.analyze()`）  
主に以下を評価:
- PID（命題密度）
- HTML構造（見出し/セマンティック/FAQ）
- エンティティ重要度
- Soft technical（HTTPS / 応答速度など）
- 文中E-E-A-T
- Citation readiness
- Contextual freshness
- AEO pattern
- Entity linking
- GEO補助（TL;DR、統計密度）
- provider別の公開条件チェック（Google / OpenAI Search / Perplexity / Claude Search）
- informational note（llms.txt, GPTBot, Google-Extended, CCBot など）

4. AIO raw score 計算  
`core/aio_analyzer.py` の重み付き合算を実施。

5. 統合スコア計算（`ScoringEngine.integrate`）  
- intent係数 `alpha` を適用（SEO/AIO配分）
- 業界ブースト（通常業界のみ。YMYL数値補正は行わない）
- 軽いヒューリスティック補正（寄生コンテンツ疑義のみ）
- YMYLは warning / note として扱い、点数乗算しない
- `integrated_score = seo_score * seo_weight + aio_score_after_penalty * aio_weight`

6. レポート化  
UI（NiceGUI）と saved snapshot / CSV 向け形式へ整形し、改善アクションを出力。

## 2.1 Current owner / 責務境界（2026-03-09）

- current engine owner: `core/engine/orchestrator.py::SEOAIOAnalyzer.analyze_url`
- UI shell / route registration: `nicegui_app.py`
- NiceGUI head CSS/script owner: `core/ui/styles.py`
- UI向け分析実行・履歴保存・saved detail rehydrate の application owner: `core/application/analysis_run_service.py`
- 検索意図・ページ役割マップ owner: `core/application/intent_role_map.py`
- FAQ候補/persona/debug payload owner: `core/application/faq_suggestion_builder.py`
- legacy page / link health / schema / llms / site health summary owner: `core/application/technical_summary_builder.py`
- CSV export owner: `core/application/csv_export_service.py`
- DOCX export owner: `core/application/docx_report_service.py`
- monitoring persistence owner: `core/monitoring/history_store.py`
- panel dependency context owner: `core/ui/panel_context.py`
- live result panel入口 / 既存互換import owner: `core/ui/panels.py`
- saved detail workspace rendering owner: `core/ui/saved_workspace.py`
- saved/live共通描画helper owner: `core/ui/panel_components.py`
- `SEOAIOAnalyzer._get/_load/_save_monitoring_history()` は monitoring store の互換 wrapper

### 2.1.1 Provider-readiness evidence contract（2026-07-10）

- provider-readiness の単一判定 owner は `core/aio_analyzer.py::AIOContentAnalyzer`。`core/engine/orchestrator.py` は取得済みの対象ページ HTTP header を渡すだけで、robots/provider 判定を重複実装しない。
- 各 provider（Google / OpenAI Search / Perplexity / Claude Search）は `pass / fail / unverified / not_applicable` のいずれかを保持する。robots.txt の timeout・取得例外・non-200 は `unverified` であり、`pass` として扱わない。
- robots.txt は分析対象 URL の path（query を含む）に対し、最長一致の User-agent group と最長一致の Allow/Disallow rule（同長なら Allow）で評価する。個別 agent group は `*` より優先する。
- `robots.txt` の provider crawler rule、HTML meta robots / provider bot meta、対象ページの `X-Robots-Tag` を同じ provider evidence に統合する。`noindex`、`nosnippet`、`max-snippet:0`、`data-nosnippet` は該当 provider の `fail` evidence である。
- fixture regression は `tests/fixtures/provider_readiness_cases.json` と `tests/test_aio_analyzer.py` が担当する。ネットワークを使わず、fetch failure、path-specific rule / UA precedence、provider-scoped X-Robots-Tag を固定する。

## 2.2 出力経路

- 画面表示は `nicegui_app.py` が dashboard と `/runs/{run_id}` route を担当し、dashboard 描画は `core/ui/dashboard.py`、live result 入口は `core/ui/panels.py`、保存済み詳細描画は `core/ui/saved_workspace.py` が担当する。
- 履歴DB保存は `core/storage/database.py`、saved detail の result file / snapshot JSON 保存は `core/application/analysis_run_service.py` を正本とする。
- CSV出力は `core/application/csv_export_service.py` が担当する。
- 保存済み分析の詳細Markdown出力は `core/application/markdown_report_service.py` が担当し、既存 result JSON / snapshot JSON から生成する。追加API送信は行わない。
- 保存済み分析の詳細Word出力は `core/application/docx_report_service.py` が担当し、詳細MarkdownをSSOTとして同内容を `.docx` 化する。追加API送信は行わない。
- 既存Azure環境への改良版差し替え時は、追加機能範囲をコトミガキのレポート保存/ダウンロードに限定する。local `data/poc_outputs/exports` を永続保存先とみなさず、生成したCSV/Markdown/DOCXを既存のテナントID分離に沿って Azure Storage などの永続ストレージへ保存し、認証付きdownload endpointまたは短期限SAS URLで配信する。
- AIO monitoring JSON 保存は `core/monitoring/history_store.py` を正本とする。

### 2.2.1 saved-workspace truth contract（2026-07-10）

- `analysis_run_service._build_priority_actions()` が SEO / AIO / 法務 / 技術 / アクセシビリティ / 検索意図を deterministic に正規化・重複除去・順位付けし、最大20件の canonical action list を作る。
- canonical action は `action_id`、`priority_rank`、`priority`、`audience`、`evidence`、`status` を持ち、snapshot の `exports.priority_actions`、`task_workspace.actions`、`summary_workspace.top_actions` が同じ list の slice を参照する。CSV は `exports.priority_actions`、Markdown は同じ snapshot、DOCX は Markdown SSOT を参照する。旧snapshotはこれらの必須キーが欠ける場合に表示時だけ再構築する。
- 保存済み結果の GET rehydrate は read-only。旧 `snapshot_json` が不足している場合も、result JSON から表示用 snapshot を memory 上で再構築するだけで、DB/artifact を書き換えない。旧 comparison の `competitor_summary` は再構築後も保持する。
- 状態値は `pass / warn / fail / unverified / not_applicable / error` を保持する。状態欠落、取得不能、構造化データ未検出を `参考` や `通過` に丸めず、必要に応じて `未確認` と表示する。`reference` は適用外または補助的な参考情報に限定する。
- この契約を変える場合は、`tests/test_analysis_run_service.py` の read-only / competitor / action parity characterization、CSV/Markdown/DOCX の出力テスト、snapshot schema の影響を同時に更新する。

## 2.3 FAQ提案生成（2026-04-20）

- FAQ未検出時の提案生成 owner は `core/application/faq_suggestion_builder.py`。`core/application/analysis_run_service.py` は snapshot 組み立て時にこの payload を利用する。
- 現行は「固定テンプレートをそのまま表示」ではなく、以下の 2 段構成で生成する。
  1. `industry / site_type / platform / legal_notes / citation_phrases / summary_improvements / target_audience_clues` などから FAQ候補を採点する
  2. 採用候補を `business_goal / page_focus / audience_clues` に応じて文面リライトし、`persona_label` と `presentation_mode=contextualized` を付与する
- ペルソナは単純な `if/elif` ではなく、`page_title / meta_description / headings / context_text / url slug / audience_clues / site_type / industry / business_goal` を信号として候補を採点する。
- URL slug は補助信号として扱い、`b2b / enterprise / pricing / clinic / shop` などの語を低ウェイトで加点する。
- 特殊ドメイン (`or.jp / go.jp / lg.jp / ac.jp / ed.jp`) は `domain_profile` として別扱いし、公共・団体寄りの prior と FAQ guardrail に使う。
- 飲食・来訪型ページは `LMO` signal として `アクセス / 営業時間 / 予約 / 現地設備` を優先し、`来訪前ユーザー向け` のペルソナ候補を別に持つ。
- EC FAQ は raw `is_ec` のみで出さず、`ec_detection_reason` と `domain_profile / lmo_profile` を使った guardrail で `effective_is_ec` を決めてから出し分ける。
- 公共・団体系では `public_services / public_eligibility / public_application` を優先候補に加え、`LMO` の `access / hours / reservation` は補助候補へ後退させる。
- 2026-06-07 以降、FAQ候補は質問だけでなく `answer_outline / recommended_section / schema_candidate / evidence_terms / confidence / risk_if_wrong` を保持する。
- `page_service_terms / location_terms / transaction_terms / customer_intent_terms` をページタイトル・meta・見出し・URL・監査文脈から抽出し、FAQ候補の根拠語と設置先判断に使う。
- `business_goal == 自動判定` はFAQ本文へ直接入れず、比較検討などの一般表現へ置き換える。
- BtoC文脈は全業種対象。飲食・介護/福祉・アパレル/物販・美容/サロン・教育/スクール・不動産売却/査定などのプロファイルは例示的な補正であり、対象業種を限定しない。
- 未知のBtoC業種でも、`初めて / 予約 / 相談 / 料金 / 費用 / 来店 / 購入 / 利用開始 / アクセス` などの顧客行動語から汎用BtoC profile に倒し、明示的なB2B文脈がない限り `導入 / 法人担当者` 寄りのFAQへ倒さない。
- `or.jp / go.jp / lg.jp` など公共・団体寄りのドメインでは、BtoCプロファイルより公共案内 guardrail を優先する。
- 生成根拠は `writing_workspace.faq_debug` として snapshot JSON に保存する。
- `faq_debug` には少なくとも `strategy / persona / context / candidates / selected_count` を保持し、`persona` 内に `confidence / source / candidates` も保持して saved workspace の「文章改善」から確認できるようにする。
- fallback は残すが、具体候補がある場合は generic glossary を優先しない。

## 2.4 古い公開ページチェック（2026-06-07）

- 旧サイト由来の `.html` が検索・AI回答に残るリスクを確認する owner は `core/seo/legacy_page_probe.py`。
- `core/engine/orchestrator.py` は分析中に代表的な候補だけを上限付きで確認し、`legacy_page_report` として保存する。
- 候補は `data.html / system.html / company.html / service.html / contact.html` などの固定候補と、取得済みURLの slug から作る `slug.html` を使う。
- 要対応として扱う条件:
  - HTTP 200
  - 最終URLが `.html`
  - `noindex` がない

## 2.5 内部リンク機会マップ（2026-06-07）

- owner は `core/application/technical_summary_builder.py::build_link_health_summary`。
- 入力は既存の `internal_link_summary` と `link_health_report` のみ。追加クロールやAPI送信は行わない。
- `orphan_pages / low_link_pages` をリンク先候補、`hub_pages` または分析対象URLをリンク元候補として、最大3件の `link_opportunities` を生成する。
- 各候補は `source_url / target_url / recommended_anchor / placement / reason / check` を持つ。
- UIでは認知負荷を抑えるため、「実装・設定」では上位2件だけを短く表示し、詳細は「エンジニア向け」へ退避する。
  - canonical がない
- 現行URLへリダイレクトされるもの、canonical があるもの、404 は要対応にしない。
- UIでは検出時だけ `公開リスク` として概要/設定に出し、URL一覧と対応方法はエンジニア向けタブに後退させる。

## 2.6 アクセシビリティ改善スコア（2026-06-11）

- owner は `core/site_health/accessibility_checker.py`。
- 目的は認証や適合判定ではなく、HTMLから自動検出できる改善余地を deterministic に点数化すること。
- LLMは使わず、BeautifulSoupで取得済みHTMLを解析する。内蔵ブラウザスキャナーが利用可能な環境では `core/site_health/browser_accessibility_scanner.py` から `tools/accessibility_scanner/` の Playwright / axe-core 検査を呼び、実ブラウザ検査を優先する。失敗時はHTML検査へ戻す。
- 実ブラウザ検査の表示名は SEOコンサル向けに「見やすさ・使いやすさ改善スコア」とし、正式なJIS/WCAG適合判定ではなく `実ブラウザ自動検出` の改善指標として扱う。
- 実ブラウザ検査の入力は1URL。内蔵スキャナーの `seo_accessibility_ux_v1` スコア、Critical/Serious件数、手動確認リスク、Tab順序サンプル、読み上げ構造サマリーを、既存の `site_health.accessibility.raw/formatted/wcag` 形式へ変換して保存する。
- 内蔵スキャナーは `tools/accessibility_scanner/` を既定とし、必要時のみ `KOTOMIGAKI_ACCESSIBILITY_SCANNER_DIR` で別配置を指定できる。Node.js未導入、npm依存未導入、タイムアウト、スキャン失敗時は既存の軽量HTML検査へ fail-open する。
- 優先アクションでは内蔵スキャナー由来の `max_severity` を尊重する。`meta-viewport` の拡大制限やコントラスト不足のような Serious の見やすさリスクは、改善対象として表示するが、問い合わせ・検索・申込などの行動完了を阻害する Critical ブロッカーとは同列に扱わない。
- 対象は次に限定する:
  - `html lang`
  - `title`
  - `h1`
  - 見出し階層
  - `main` / `nav` / `header` / `footer` landmark
  - `img alt`
  - `a` / `button` の accessible name 候補
  - `input` / `select` / `textarea` の label 候補
  - `iframe title`
- 実ブラウザ検査時は上記に加え、axe-core由来の `color-contrast`、`meta-viewport`、ARIAの意味づけ、キーボード/フォーカス関連候補も `issue_groups` へ正規化する。
- スコアは `ACCESSIBILITY_SCORE_WEIGHTS` の重み付き合算で100点満点。各グループは検出対象数に対する不足数から充足率を計算する。
- `a` / `button` の accessible name 欠落は、同じ共通部品が複数回出るケースで過剰減点しないよう、同一HTML署名の missing control を1課題として集約する。
- 空白ページや極端に小さいページが高得点にならないよう、可視テキスト量と構造タグ量から `score_cap` を適用する。
  - text `< 20` かつ structure `< 5`: 最大35点
  - text `< 80` かつ structure `< 8`: 最大60点
  - text `< 200` かつ structure `< 12`: 最大80点
- raw出力の正本キー:
  - `score`
  - `score_status`
  - `issue_groups`
  - `affected_counts`
  - `top_actions`
  - `scoring_version`
- UI向け文言は「アクセシビリティ改善スコア」と「自動検出」を中心にし、認証・適合を想起させるラベルは出さない。
- 改善アクション変換 owner は `core/application/accessibility_improvement_builder.py`。
  - `site_health.accessibility.raw.issue_groups` を、非エンジニア向けの `audience.action` / `audience.impact` / `audience.review_area` / `audience.handoff_to` と、エンジニア向けの `engineer.target_element` / `engineer.task` / `engineer.verification` / `engineer.detection_source` へ分けて変換する。
  - SEOタブ、保存済み詳細の「実装・設定」、最優先アクションでは、具体コード・HTML・セレクタ・実装修正手順を出さず、影響・見直し箇所・次に渡す相手を表示する。
  - 保存済み詳細の「技術」タブと詳細Markdownでは、対象要素、行うべき作業、確認方法、検出元を出す。
  - 実検出0件または高スコアで `issue_groups` 由来の対象がない場合、固定テンプレートの汎用修正カードを `actions` として前面化せず、必要に応じて `confirmation_items` として技術補足へ下げる。
  - `priority_score` / `priority_rank` / `impact` / `urgency` / `effort` / `category` はルールベースで固定し、LLMに順位・件数・重要度を決めさせない。
  - LLMを使う場合も表示文の整形だけに限定し、`prompt_version` / `model` / `reasoning` / `ruleset_version` / `html_hash` を `metadata` に保存する。
  - LLM失敗時は固定テンプレートへ fallback し、LLMなしと同じ件数・同じ順位を維持する。
  - LLM並列実行は課題グループ単位で行い、`max_parallel` は 1-5 に丸める。

## 2.7 公開技術リスクチェック（2026-06-23）

- owner は `core/site_health/security_checker.py`。
- 目的は、侵入的な脆弱性診断ではなく、取得済みHTTPヘッダー・HTML・既存sitemap情報と、CMSが標準公開するwell-known endpointから外部公開状態の設定ミスを検出すること。
- 本チェックは軽量な公開情報検査に限定する。`.git`、バックアップファイル、管理画面総当たり、既知脆弱性スキャン、ディレクトリ探索は行わない。
- 対象は次に限定する:
  - WordPress など CMS generator / asset version の公開
  - 古い jQuery / Swiper など主要フロントエンドライブラリのバージョン露出
  - 外部CDN script / stylesheet の `integrity` 欠落
  - Universal Analytics (`UA-...`) の残存
  - `html5shiv` / `respond.js` など旧IE向けポリフィルの残存
  - WordPress痕跡がある場合の `/wp-json/wp/v2/users` 公開状態
  - sitemap が静的生成または古い `lastmod` のまま残っている可能性
  - WordPress標準 sitemap と別sitemapの併存など、検索エンジン向け導線の混乱
  - HTTPSページ内に残る同一ドメイン `http://` の内部リンク / フォーム送信先
  - 問い合わせ・資料請求・アップロード等のフォームにおける HTTP送信、個人情報同意表示、CSRF/nonce痕跡、bot対策痕跡の確認候補
  - `/sitemap.xml` の取得失敗・XML解析失敗など、公開サイトマップの運用不備
  - 公開HTML上で見える最新日付が古い場合の更新停滞サイン
- スコアへの反映は既存のセキュリティ基本設定スコア内で小さく行う。高リスク項目がある場合も、実害の断定ではなく「要確認」として出す。
- UI向け文言は、非エンジニアには「管理画面・制作会社に渡す確認事項」、エンジニアには「確認URL / 該当タグ / 推奨確認コマンド」を出す。
- 現在の最新バージョン判定はハードコードで断定しない。明確に危険域が知られる古い系列（例: jQuery < 3.5.0）や明らかな運用停止タグ（Universal Analytics）だけを警告する。
- EC取引安全・商品データ監査は、誤検知時の影響が大きいため本チェックへ混ぜない。EC高信頼判定条件が別途固まるまで、通常URLに対してEC不備を出さない。

追加メモ（2026-06-23）:
- `URLチェック` 由来の公開HTML静的解析として、`polyfill.io` / `staticfile.org` / `bootcdn.net` など既知の要確認外部アセットドメインと、`target="_blank"` の `rel="noopener"` 不足を検出する。侵入的なスキャンではなく、ページソース上の参照棚卸しとして扱う。
- `アクセシビリティ` 由来の Playwright / axe-core 系スキャナ、手動確認キュー、重複グルーピング、スコアリングは `tools/accessibility_scanner/` に既に同梱済み。今回の追加実装対象は未同梱だった URLチェック由来の公開HTMLセキュリティ信号に限定する。

追加メモ（2026-06-24）:
- フォーム監査は公開HTMLから見える確認候補に限定し、サーバー側の実装不備や脆弱性を断定しない。検索フォームは問い合わせ/個人情報フォーム扱いにしない。
- 見える更新日は `YYYY.MM.DD` / `YYYY/MM/DD` / `YYYY-MM-DD` / `YYYY年M月D日` を公開HTML本文から抽出し、365日未満なら signal のみ、365日以上なら確認候補として出す。sitemap `lastmod` とは別根拠として扱う。
- EC向けの特商法・商品データ・決済導線監査は既存の法務/EC判定の境界を優先し、この公開技術リスクチェックには追加しない。

追加メモ（2026-06-24 / 保守・更新管理）:
- `public_technology_risks -> site_health_checks -> engineer_tasks` の既存フローを使い、公開HTML/HTTPヘッダー/sitemap/WordPress標準公開endpointから分かる「保守会社に確認すべき公開サイン」を一般機能として表示する。侵害・脆弱性の断定はしない。
- 更新整合性は `visible_update_freshness` と sitemap `lastmod` を組み合わせる。見える最新日付が365日未満で sitemap `lastmod` が365日以上古い場合は `update_signal_mismatch`（要確認）、両方365日以上古い場合は更新停滞サインとして扱う。sitemap取得/解析不可時は `sitemap_unavailable_or_invalid` を優先する。
- 古いフロントエンド資産は、既存の `jquery_before_3_5` を維持しつつ、URLから分かる `jquery-ui / bootstrap / swiper / slick / modernizr / html5shiv / respond.js` を棚卸し候補として扱う。jQuery < 3.5.0 は high、それ以外は medium/low の確認候補で、具体的なCVEや最新バージョンは断定しない。
- 追加補足（2026-06-24）: `jquery.js` / `jquery.min.js` のようにURLからバージョンが分からないjQuery本体候補は、ページが実際に読み込む公開JSに限り、最大3件・各256KBまで先頭コメントを取得して `jQuery vX.Y.Z` を確認する。プラグインや `jquery-ui` は取得対象にしない。これは `jquery_before_3_5` の既存明確ルールを補完するためで、広範なアセット探索にはしない。
- 一般向け表示は `core/site_health/maintenance_risk.py` が分類する。カードは `更新整合性チェック`、`WordPress保守確認`、`フォーム確認`、`古いフロントエンド資産`、`ブラウザ防御設定`、`sitemap/robots整合性`。
- `maintenance risk score` は初期100点から high issue: -18、medium issue: -10、low issue: -4 を減点し、最低0点とする。対象は公開技術リスク内の保守系issueに限定する。
- 既存レーダーに別チャートは追加しない。`技術基盤` は `保守・技術基盤` として扱い、`リンク健全性 / OGP / セキュリティ / 保守更新` を平均対象に含める。軸数は最大6軸以内に留める。
- EC取引安全・商品データ監査は誤検知時の影響が大きいため対象外。既存の法務/EC判定側の責務境界を優先する。

### 2.7.1 公開endpoint健全性チェック（2026-06-24）

- owner は `core/site_health/endpoint_health_checker.py`。`core/site_health/security_checker.py` は呼び出しと既存HTML/headers由来issueの集約に留める。
- 目的は、SEO/AIO以前の公開設定ミスや保守放置サインを、非エンジニアにも分かる「保守会社に確認すべき公開サイン」として出すこと。脆弱性診断・侵入テスト・総当たりではない。
- チェック対象は公開HTML、HTTPヘッダー、`/robots.txt`、代表的なsitemap endpoint（`/sitemap.xml`、`/wp-sitemap.xml`、`/sitemap_index.xml`）、WordPressでない可能性が高いサイトの `/wp-json/`、および存在しないURL 1件だけに限定する。ランダムな存在しないURLのリクエストは1分析につき1件のみ。
- `robots.txt` が 200 OK でもHTMLを返す、または `User-agent` / `Disallow` / `Allow` / `Sitemap` の基本行が見えない場合は、`robots_txt_html_fake_200` / `robots_txt_invalid_or_empty` として確認候補にする。
- sitemap endpoint が 200 OK でもXMLではなくHTMLを返す場合は `sitemap_endpoint_html_fake_200` として扱う。sitemap内URLの網羅性・lastmod鮮度は既存 `sitemap_analyzer.py` / `stale_or_static_sitemap` 側の責務とし、このチェックでは偽200/HTML返却の公開endpoint状態に限定する。
- WordPressでない可能性が高いサイトで `/wp-sitemap.xml` や `/wp-json/` がトップページ相当HTMLを 200 OK で返す場合は、`unused_endpoint_fake_200` として「不要endpointの偽200」確認候補にする。
- 存在しないURLが 404/410 以外でトップページ相当HTMLを返す場合は、title一致、本文類似、canonical/noindex痕跡の有無だけを軽量に見て `soft_404_missing_url_200` とする。大量のURL探索は行わない。
- `X-Powered-By` / `Server` に PHPバージョンや PleskLin が見える場合は `server_environment_header_exposed` とする。PHP 5.x / 7.0-7.4 のようなEOL系列は high/medium の優先確認候補にするが、最新バージョンや具体的CVEは断定しない。
- フォーム安全性は公開HTMLから見える痕跡だけを見る。file upload、個人情報項目、センシティブ語、captcha、CSRF/nonce/token、privacy同意、HTTP送信先、外部送信先を検出するが、サーバー側対策の有無は「公開HTML上では確認できない」と表現する。
- HTTPSサイト内の同一ホスト `http://` 導線は、mixed contentとは別に、ユーザー導線・SEO正規化の確認候補として `internal_http_navigation_link` に流す。
- endpoint健全性由来のissueは既存どおり `public_technology_risks.issues` に追加し、`maintenance_risk.py` で保守系issueとしてscore/cardへ分類し、`site_health_checks[].engineer_tasks` に確認URL・HTTP status・Content-Type・根拠抜粋・確認コマンド・合格条件を出す。

### 2.7.2 固定既知脆弱性DB照合（2026-07-08）

- owner は `core/site_health/vulnerability_intelligence.py`。`core/site_health/security_checker.py` は公開HTML/JSから検出した component / version を渡し、返却された安全な候補サマリーを `public_technology_risks.issues` と `signals.fixed_vulnerability_intelligence` に集約する。
- 目的は、URLチェックの現時点ローカル脆弱性DBを固定スナップショットとして参照し、公開ページ上で見えるフロントエンド部品が既知脆弱性の影響範囲に入る可能性を「保守会社に渡す確認事項」として出すこと。
- 取り込みDBは `config/vulnerability_intelligence.sqlite3` を既定とする。これは固定スナップショットであり、通常分析中の外部API取得、差分更新、定期同期、DB書き込みは行わない。
- 照合は URLチェックと同じ考え方で、`ecosystem / identifier_kind / canonical_component_key` から SHA-256 の `hash_key` を作り、SQLite の `components.hash_key` / `component_aliases.hash_key` index で候補を引く。25万件規模のDBを総当たりしない。
- 検出対象は、既存の公開技術リスクチェックが公開HTML/JS URLから把握できる component / version に限定する。サーバー内部依存、認証後画面、管理画面、非公開ファイル、SBOM/lockfile は対象外。
- 2026-07-10: SQLite は `file:<path>?mode=ro` の明示read-onlyで開き、DB fingerprint（size/mtime）を候補キャッシュkeyに含める。`checked_no_match`、`db_missing`、`db_unreadable`、`schema_incompatible`、`query_failed` を分離し、照合不能を「脆弱性なし」とは表示しない。
- `affected_ranges` は `range`、明示 `version`、`osv_ranges_json`、CPE等metadataを別々に扱う。比較可能なrangeはOR分岐ごとに評価し、CPE・未対応構文・比較不能は `unknown`／保守担当者確認とする。全候補をcanonical advisory単位で集約して重要度・KEV・件数を計算し、画面だけを安全な表示件数に制限する。
- 一般向けUI、Markdown、Wordはコンポーネント、検出バージョン、候補件数、重要度の目安、更新確認・保守依頼、固定DB基準日、非断定注記だけを基本表示とする。CVE/CVSS/KEV/参照URLは保存済み画面の保守担当者向け折りたたみ表示に限定し、攻撃手順・PoC・payloadは出力しない。
- URL文字列は fetch/追加クロール前に決定的にscreeningする。percent/HTML entity/NFKC/Unicode escape/限定Base64・hex/ゼロ幅/bidi/confusableを最大2段・長さ/時間上限内で正規化し、複合的な命令・秘密持出し・tool/追加取得信号があれば本文を残さずAI入力・追加取得から除外する。HTML等の取得本文も不信データであり、このURL screeningだけで本文対策完了とは扱わない。
- UIは未検知を安全保証や「存在しない」とは表現せず、「確認したURL文字列には、AIへの不審な指示と判断できるパターンは観測できませんでした」と限定表示する。検知時もプロンプトインジェクションと断定せず、payload本文を再掲せずに検出箇所と構造化信号だけを表示する。
- version range が比較可能な候補だけを「既知脆弱性候補」として出す。version が未検出、範囲比較不能、DBに候補がない場合は「安全」ではなく「固定DBでは該当候補なし / 要確認」と扱う。
- UI向け文言は、非エンジニアには「既知脆弱性候補」「更新確認」「制作会社/保守担当者へ確認」を中心にする。CVE ID、影響範囲、修正版目安、参照元はエンジニア向け詳細へ後退させる。
- exploit手順、PoC、payload、悪用条件、認証回避手順、攻撃再現に使える具体情報は保存・表示しない。
- シングルテナント環境でも、脆弱性DB自体は共通固定マスタとして扱い、分析結果側だけ `tenant_id / run_id` に紐づける。将来Azureへ差し替える場合も、固定DBを読み取り専用の永続ストレージまたはDBへ配置し、通常分析から外部更新ジョブを呼ばない。

### 2.8 法務表現の文脈判定（2026-07-10）

- `core/legal_checks/premiums_labeling.py` は候補語を機械抽出するが、単語だけで主画面の警告・減点を確定しない。
- `core/engine/orchestrator.py` の文脈判定は、候補を次の3状態へ分類する。
  - `action_required`: 効果・品質・安全・順位・価格の明確な保証/誇張
  - `safe_context`: 予約・設備・営業時間などの運用条件、否定・注意喚起、商品名/固有名詞
  - `review_needed`: 二重否定、係り受け不明、前後文不足、判定失敗
- 明確な安全文脈と明確な保証表現はローカル規則で先に判定する。
- 残る曖昧候補は最大5件を1回のstructured Responses API呼び出しへまとめる。重複候補は同一リクエストへ増やさない。
- APIエラー・タイムアウト・不完全JSON・返却候補不足は `review_needed` とし、安全確定にはしない。
- 主画面、法務スコア、優先アクション、非エンジニア向けレポートには `action_required` のみを反映する。`review_needed` は減点せず、保存済みrawと実装担当向け詳細Markdown/DOCXへ証拠文・理由・モデル・reasoningとともに残す。
- この判定は法律適合や違反を断定するものではなく、公開文面の確認優先度を整理する内部ヒューリスティックである。

## 3. AIO raw score（v2）

`core/aio_analyzer.py` の実装に従い、以下を 0〜1 正規化で加重合算:

- PID: 0.20
- Structure: 0.15
- Entity: 0.12
- Tech: 0.10
- Inline E-E-A-T: 0.08
- Citation readiness: 0.10
- Freshness: 0.06
- AEO patterns: 0.05
- Entity linking: 0.04
- GEO TL;DR: 0.05
- GEO stats density: 0.05

補足:
- raw score は soft score 層のみで構成する
- provider別の公開条件は raw score に加点しない
- `llms.txt`, `Google-Extended`, `GPTBot`, `ClaudeBot`, `CCBot` は informational note として保持する
- `INTENT_ALPHA` の数値自体は official primary source の係数ではなく、内部ヒューリスティックとして維持する

注: 重みや式の更新時は、コードと本ファイルを同時更新する。

## 4. GEO score（統合側）

`core/scoring_engine.py` で100点換算:
- TL;DR: 40%
- 統計密度: 35%
- E-E-A-T: 25%

補足:
- `geo_score` は内部診断値であり、provider gate や Google の公式要件そのものではない
- UI では「内部診断（GEO）」として表示する

## 4.1 YMYL補正とペナルティ条件

- YMYL業界判定は `core/scoring_engine.py::YMYL_KEYWORDS` と `seo_results.eeat.is_ymyl` を併用する。
- YMYL は **点数乗算しない**。`aio_score` / `integrated_score` に対して `1.2x / 0.7x / 0.5x` の補正は適用しない。
- 現行は `is_ymyl_context and aio eeat_score < 4.0` の場合に warning / heuristic note を出す。
- 目的:
  - 日本語ページでの過剰減点を避ける
  - 「公式に方向性があること」と「内部ヒューリスティックによる注意喚起」を分離する

## 4.2 penalty / note の扱い

- hard gate:
  - Google: `Googlebot`, `noindex`, `nosnippet`, `max-snippet`, `data-nosnippet`
  - OpenAI Search: `OAI-SearchBot`
  - Perplexity: `PerplexityBot`
  - Claude Search: `Claude-SearchBot`
- soft score:
  - AIO raw score の 11指標
- informational note:
  - `llms.txt`
  - `Google-Extended`
  - `GPTBot`
  - `ChatGPT-User`
  - `Claude-User`
  - `ClaudeBot`
  - `CCBot`

## 4.3 provider別出力

- `core/aio_analyzer.py` は provider別の numeric score / overall score を出さない
- 代わりに `details.provider_readiness` として次を返す
  - `status`: `pass / warn / fail`
  - `official_checks`: 公式に確認できた条件
  - `heuristic_notes`: 内部ヒューリスティック
  - `informational_notes`: 任意メモ / 情報目的

## 5. 変更管理

- スコア式や重みを変更した場合は本ファイルを必ず更新。
- engine / ui / report / persistence の owner を変更した場合も本ファイルを更新。
- 変更履歴は `aio2-main/WORKLOG.md` に追記。
- 全体導線に影響する場合のみ `C:\tetie\ALGORITHM.md` / `C:\tetie\AGENTS.md` も更新。
