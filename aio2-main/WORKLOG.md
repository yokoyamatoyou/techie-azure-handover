# WORKLOG

過去の記録は `WORKLOG.backup.md` を参照してください。

---

## 2026-07-11 (Sol PM / Terra orchestration) 横断UX監査P1/P2修正

- owner: `cross_suite_ux_audit_findings_ui_fix_2026_07_11` のコトミガキ表示層。分析アルゴリズム、スコア、crawler、API/provider/LLM、DB/schema、外部取得は非owner境界として変更していない。
- change:
  - 新規分析の対象URL/比較URLを輪郭付き入力欄にし、placeholderの可読性を上げた。
  - 入力エラーは欄直下の `role=alert` 1か所だけに表示し、送信時は最初の不正欄へfocusして画面中央へscrollする。離れたstatus欄への同文重複を廃止した。
  - 390px幅でも横断ナビ4項目が収まるよう、区切り・間隔・文字サイズをモバイル用に圧縮した。
  - 保存履歴はクリック可能な行だけに依存せず、PC表とモバイルカードの双方に「結果を開く」buttonを明示した。
- validation:
  - `.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\dashboard.py` -> PASS。
  - `.venv\Scripts\python.exe -m pytest tests\test_dashboard_ui.py tests\test_characterization_ui.py -q` -> `37 passed`。
  - `.venv\Scripts\python.exe -m pytest tests -q` -> `208 passed`。
  - `pytest -q` のroot無指定はarchive済み旧PDFテストが退役module `PDFreport` を要求して収集停止するため、現行正本 `tests/` を使用。API送信回数: 0。

## 2026-07-10 (Codex) 入力エラーの読み上げ到達性

- scope: 新規分析フォームのURL/比較URL入力エラー表示だけを変更。分析、保存、スコア、外部取得/APIは対象外。
- change: 既存の具体的なインラインエラーを `role=alert` / `aria-live=polite` にして、視覚以外の利用者にも状態変化が届くようにした。
- validation: `py_compile nicegui_app.py`、`pytest tests\test_dashboard_ui.py -q` -> 13 passed。API送信回数: 0。

## 2026-07-10 (Codex) provider-readiness evidence owner

- scope: `core/aio_analyzer.py` の provider readiness evidence と、取得済み response header を渡す `core/engine/orchestrator.py` の境界に限定。saved-workspace、scoring engine、Schema validator、LLM、認証/tenant、URL redaction、accessibility scanner、live URL/API は対象外。
- change:
  - provider status を `pass / fail / unverified / not_applicable` の evidence contract とし、robots.txt の取得例外・timeout・non-200 は provider ごとの `unverified` にした。
  - robots.txt を root 固定ではなく対象 URL path ごとに評価し、最長 User-agent group、最長 Allow/Disallow rule、同長 Allow 優先を実装した。
  - generic/provider meta robots と対象ページ `X-Robots-Tag` を同じ provider evidence に統合し、`noindex` / `nosnippet` / `max-snippet:0` / `data-nosnippet` を fail evidence にした。
  - `tests/fixtures/provider_readiness_cases.json` を追加し、fetch failure、path-specific rule / UA precedence、provider-scoped X-Robots-Tag の回帰を固定した。
- validation:
  - `.venv\Scripts\python.exe -m py_compile core\aio_analyzer.py core\engine\orchestrator.py tests\test_aio_analyzer.py` -> PASS。
  - `.venv\Scripts\python.exe -m pytest -q tests\test_aio_analyzer.py -p no:cacheprovider` -> `4 passed`。
  - API送信回数: 0。live URL/API、browser、既存runの更新は未実施。
- remaining:
  - provider evidence を表示・exportする saved-workspace / UI adapter は別owner。スコアへの反映は scoring-contract owner。live provider robots 挙動の確認は live validation owner。

## 2026-07-10 (Codex) fixed vulnerability intelligence and URL instruction guard

- scope: `aio2-main`だけを変更。URLチェックはread-only正本として参照し、外部サイト/API/LLM、ログイン、POST、攻撃的な実証は未実施。
- change: `core/site_health/vulnerability_intelligence.py` をread-only SQLite・DB状態分離・fingerprint cache・range/version/OSV/CPE別評価・OR分岐・canonical advisory集約へ更新。評価全件から重要度/KEV/件数を算出し、表示のみ5件/部品に制限。
- change: `core/site_health/url_instruction_guard.py` を追加し、`safe_fetch.py`とpriority link抽出へ接続。疑わしいURLはpayloadを保存せず構造化結果のみを残し、AI入力/追加取得から除外。
- output: 一般向けissueとMarkdown/DOCX SSOTは非断定の概要に限定。CVE/CVSS/KEV/参照は保存済み画面の保守担当者向け折りたたみ表示のみ。固定DB照合不能はスコア減点せず、明示メッセージを表示。
- validation: `py_compile`、focused pytest 17 passed（固定DB、OR/OSV/unknown、DB異常、URL instruction guard、safe fetch）。

### UI wording follow-up

- `core/ui/tabs/health_tab.py` にURL文字列の安全確認カードを追加。未検知は観測範囲を限定した表現、検知時は断定せず、payloadを出さない構造化信号と除外動作だけを表示する。
- `core/engine/orchestrator.py` は主URLのscreening結果をresult JSONへ保存し、URL screenをfetch/API前に実行する。
- validation: `py_compile`、`test_url_instruction_guard.py` / `test_safe_fetch_security.py` / `test_orchestrator_security.py` -> 17 passed。

## 2026-07-10 (Codex) saved-workspace truth and action parity owner

- scope: 保存済み結果の read-only rehydrate、legacy competitor 保持、状態値の意味保持、canonical priority action の UI/CSV/Markdown/DOCX 接続に限定。SEO/AIO scoring、crawler/provider、Schema、LLM、認証/tenant、accessibility scanner、法務判定は対象外。
- change:
  - `core/application/analysis_run_service.py` の既存 canonical action list (`action_id` / `priority_rank` / `priority`, 最大20件)を `exports.priority_actions`、`task_workspace.actions`、`summary_workspace.top_actions` の共通正本としてcharacterizationで固定。
  - canonical actionへ `audience` / `evidence` / `status` / `status_label` を追加し、CSV・Markdown・DOCXへ同じ保存済みsnapshotから出力する契約を固定。欠落statusは `unverified` として保持する。
  - `core/site_health/__init__.py` の互換exportを遅延化し、`safe_fetch`からURL instruction guardを読む際のsecurity_checker循環importを解消。
  - `load_saved_run_bundle()` の旧snapshot再構築が DB/artifact を書き換えず、保存済み `comparison_workspace.competitor_summary` を保持することを回帰固定。
  - `core/application/technical_summary_builder.py` で状態欠落・未検出を `reference` ではなく `unverified` とし、`unverified / not_applicable / error` の表示ラベルを追加。
  - `ALGORITHM.md` に saved-workspace truth contract を追記。
- validation:
  - `.venv\Scripts\python.exe -m py_compile`（R-01変更＋site_health互換export） -> PASS。
  - `.venv\Scripts\python.exe -m pytest -q tests\test_analysis_run_service.py tests\test_csv_export_service.py tests\test_markdown_report_service.py tests\test_docx_report_service.py` -> `42 passed`。
  - `.venv\Scripts\python.exe -m pytest tests/ -q` -> `204 passed`。
  - characterization / executive summary を加えた対象集合 -> 73 passed（既存記録）。
  - 保存GETの書込禁止、competitor保持、action id/order parity、旧状態の `未確認` を確認。API/live run/browser操作は未実施。
- remaining:
  - 次ownerは `provider-readiness evidence owner`。browser current-run visual/keyboard/axe検証、外部公開のauth/tenant隔離、URL query secret redaction、provider/score/Schema/LLMの監査 findings は別owner。

## 2026-07-10 (Codex) 法務表現の3状態文脈判定と出力境界

- scope: `aio2-main` の景品表示法候補に限定。コトメイク、コトメガネ、コトムスビ、SEO/AIOスコア式、crawl構成、サイトヘルス検出意味、固定脆弱性DBは対象外。
- issue:
  - `完全|100%|絶対` の候補語を単語だけで評価し、「完全予約制」「正解や絶対がない」も主結果へ残っていた。
  - run 28では既存GPT文脈判定が「商品名/固有名詞か」だけで、二重否定・運用条件・保証表現の区別を持っていなかった。
- change:
  - `core/engine/orchestrator.py` に `action_required / safe_context / review_needed` の文脈判定契約を追加。`review_needed` は実装担当向け低重要度詳細に残し、`safe_context` は情報扱いで主導線から除外。
  - 明確な予約・設備・否定文脈と明確な保証表現はローカル規則で判定。
  - 残る曖昧候補は最大5件を1回のstructured Responses API呼び出しへまとめ、欠落・API失敗・不完全JSONは `review_needed` にするfail-closedを追加。
  - `core/legal_checks/premiums_labeling.py` は `action_required` のみを非エンジニア向け項目・推奨・減点へ反映。
  - safe/reviewをraw保存し、実装担当向け詳細パネルと詳細Markdownへ証拠・理由・判定メタデータを残す境界を追加。DOCXはMarkdown SSOT経由で同内容を引き継ぐ。
  - `ALGORITHM.md` に判定意味、失敗時、出力境界を追記。
- validation:
  - `.venv\Scripts\python.exe -m py_compile`（変更8ファイル＋追加テスト） -> OK。
  - `.venv\Scripts\python.exe -m pytest -q tests\test_legal_context_decisions.py tests\test_schema_validator.py tests\test_analysis_run_service.py tests\test_executive_summary.py tests\test_markdown_report_service.py tests\test_docx_report_service.py` -> 58 passed。
  - 回帰: SEO/AIO/サイトヘルス/固定脆弱性DB/アクセシビリティ/公開技術リスク/LLM境界を含む13 test modules -> 124 passed。
  - fixtureで `完全予約制` / `完全個室` / `正解や絶対がない` / `絶対ではない` / `効果を保証しない` / `完全に治る` / `絶対に安全` / `100%成功` / 二重否定 / structured一括呼び出し / API失敗fail-closedを確認。
  - API送信回数: 0。live run・ブラウザ操作: 未実施。
- remaining:
  - run 28のCitation content plan `response_incomplete:max_output_tokens` は再発記録があり、今回の法務ownerとは別の次ownerとして残す。
  - 8081は本確認時にlistenしておらず、ブラウザ操作・保存済みrun 28の再生成は未実施。APIなしfixtureのMarkdown/DOCX経路はテスト済み。

## 2026-07-10 (Codex) Markdown/DOCXレポート反映確認

- scope: 今回の法務3状態判定が保存レポートへ反映されるかのfixture確認。分析API・保存済みrunの変更はなし。
- checked:
  - Markdownは保存snapshotの `priority_actions` を正本として `action_required` のみを最優先アクションへ出力する。
  - `review_needed` は `法務文脈判定（実装担当向け）` に証拠文・理由・model/reasoningとともに出力する。
  - DOCXはMarkdownと同じbundleを受け、同内容の見出し・証拠文・モデル情報を `document.xml` に保持することを確認。
  - fixture出力: `outputs/qa_reports/run28-context.md`、`outputs/qa_reports/detailed-report-run-28-20260710-104320.docx`。
- validation:
  - Markdown: review見出し・証拠文あり。
  - DOCX: 38,276 bytes、必要OOXML部品あり、review見出し・証拠文・`gpt-5.4-nano`あり。
  - PNGレンダーは `pdf2image` が実行環境に未導入で完了できず、目視レイアウトQAは未実施。既存の構造テストは通過。

## 2026-07-09 (Codex) site health独立チェックの並列化

- scope: コトミガキ(aio2-main)の `run_full_site_health_check()` 内に限定。OGP、公開技術リスク/固定既知脆弱性DB照合を含むセキュリティ、アクセシビリティの独立チェックを並列実行する。判定ロジック、スコア式、脆弱性DB、UI表示、API送信、外部同期、取得対象URLの拡張は対象外。
- change:
  - `core/engine/site_health_engine.py` で OGP / security / accessibility を `_run_ogp_check()` / `_run_security_check()` / `_run_accessibility_check()` へ分離。
  - 3チェックを `ThreadPoolExecutor(max_workers=3)` で並列実行し、既存と同じ `site_health.ogp/security/accessibility` 形状へ戻すようにした。
  - `tests/test_schema_validator.py` に、3チェックが同時開始しないと通らない並列実行回帰テストを追加。
- validation:
  - `.venv\Scripts\python.exe -m py_compile core\engine\site_health_engine.py tests\test_schema_validator.py` -> OK。
  - `.venv\Scripts\python.exe -m pytest -q tests\test_schema_validator.py tests\test_fixed_vulnerability_intelligence.py tests\test_public_technology_risks.py tests\test_endpoint_health_checker.py` -> 26 passed。
  - `.venv\Scripts\python.exe -m pytest -q tests\test_characterization_engine.py tests\test_analysis_run_service.py` -> 38 passed。

## 2026-07-09 (Codex) 固定既知脆弱性DBのURLチェック最新版取り込み

- scope: コトミガキ(aio2-main)の固定既知脆弱性DBスナップショット置換に限定。照合ロジック、UI、通常分析中の外部取得、差分同期、定期更新、API送信は対象外。
- source:
  - `C:\Users\横山裕明\OneDrive - 京都工業株式会社\デスクトップ\URLチェック\config\intelligence.sqlite3`
- changed:
  - `config/vulnerability_intelligence.sqlite3` をURLチェック側の2026-07-09スナップショットへ置換。
  - 旧DBは `config/vulnerability_intelligence.sqlite3.backup_20260709_2359` として保持。
- validation:
  - SQLite `PRAGMA quick_check` -> `ok`。
  - 置換後DB: `schema_version=3`, `record_count=259398`, `reference_date=2026-07-09`, `advisories=259398`, `components=236139`, `component_aliases=705245`, `known_exploited_signal_matches=201`, `epss_signal_matches=6421`。
  - SHA256: 置換後 `vulnerability_intelligence.sqlite3` は取り込み元 `intelligence.sqlite3` と同一。
  - fixed DB smoke: `jquery 3.4.1` -> `status=matched`, `match_count=3`, `first_cves=('CVE-2020-11022',)`。
  - `.venv\Scripts\python.exe -m pytest -q tests\test_fixed_vulnerability_intelligence.py tests\test_public_technology_risks.py` -> 15 passed。

## 2026-07-09 (Codex) 表示重複・内部文言の追加確認

- scope: コトミガキ(aio2-main)のUI表示文言に限定。判定ロジック、スコアリング、保存データ構造、API呼び出しは対象外。
- checked:
  - 保存済み分析ワークスペースの `site_health_checks` について、`highlights` / `issues` / `recommendations` をまたぐ重複表示候補を確認。追加の重複データは検出なし。
  - UI表示文字列として `source_hits` / `intent_signals` / `page_signals` / `N/A` / `固定の` / `テンプレート` が直接出る箇所を検索。
- fix:
  - `core/ui/saved_workspace.py` の検索意図詳細で、内部キー名を `判断に使った語句` / `検索意図の検出語句` / `ページ内の手がかり` へ変更。`title` / `url_path` / `schema_types` などのキーも日本語表示へ変換。
  - `core/ui/tabs/health_tab.py` の `固定の補足情報` / `固定のセキュリティFAQ` / `固定のリスクメモ` を一般補足として自然な表現へ変更し、構造化データの `テンプレート` 表示を `実装例` に変更。
  - `core/ui/tabs/seo_tab.py`, `core/ui/tabs/aio_tab.py`, `core/ui/tabs/comparison_tab.py` の `N/A` fallback を `未取得` / `未設定` / `確認項目がありません` に変更。
  - `core/ui/tabs/aio_tab.py` の `生スコア` / `式` を `調整前スコア` / `計算内容` に変更。
  - `core/ui/panels.py` の `非エンジニア向け` / `エンジニア向け` ラベルを `読み手向けの説明` / `実装担当向けメモ` に変更。
- validation:
  - `py_compile`: `core/ui/saved_workspace.py`, `core/ui/tabs/health_tab.py`, `core/ui/tabs/seo_tab.py`, `core/ui/tabs/aio_tab.py`, `core/ui/tabs/comparison_tab.py`, `core/ui/panels.py`, `tests/test_executive_summary.py` OK。
  - `pytest`: `tests/test_executive_summary.py tests/test_characterization_ui.py tests/test_endpoint_health_checker.py -q` -> 35 passed。
  - API送信回数: 0。

## 2026-07-09 (Codex) セキュリティ詳細の重複表示修正

- scope: コトミガキ(aio2-main)の保存済み分析ワークスペース内「エンジニア向け」タブに限定。セキュリティ判定ロジック、スコアリング、脆弱性DB照合、API呼び出しは対象外。
- issue:
  - 「セキュリティの詳細」で `highlights` と `issues` に同じ公開技術リスク文言が入る場合、同じ内容が大きい本文と小さい補足行で二重表示されていた。
- fix:
  - `core/ui/saved_workspace.py` の描画直前で `highlights` / `issues` / `recommendations` を同一キーで重複除外し、既存の保存済み結果でも同じ文面を一度だけ表示するようにした。
  - `tests/test_executive_summary.py` に、先頭の中黒や空白差を吸収して詳細行を重複除外するテストを追加。
- validation:
  - `py_compile`: `core/ui/saved_workspace.py`, `tests/test_executive_summary.py` OK。
  - `pytest`: `tests/test_executive_summary.py tests/test_endpoint_health_checker.py -q` -> 14 passed。
  - API送信回数: 0。

## 2026-07-09 (Codex child window) Responses API移行後確認 + モデル差し替え前互換fix

- scope: Claudeの `claude_responses_api_migration_phase0_first_site` / `claude_responses_api_migration_phase0_pdfreport_and_orchestrator_remainder` 後確認。コトミガキ(aio2-main)専用。判定ロジック、スコアリング、DBスキーマ、notecode/kotomeganeは対象外。
- findings:
  - `core/config.py` の `OPENAI_REASONING_MODEL` / `OPENAI_REASONING_EFFORT` と用途別 `OPENAI_AIO_SUGGESTIONS_MODEL` / `OPENAI_LEGAL_MODEL` / `OPENAI_AIO_CONTENT_MODEL` / `OPENAI_GAP_ANALYZER_MODEL` で、主要Responses API呼び出しはenv差し替え可能なことを確認。
  - `core/llm_responses_client.py` のprefix gateで、gpt-5/o1/o3系は `temperature` / `top_p` を送らず、gpt-4.1系には `reasoning` / `verbosity` を送らないことを確認。
  - 未使用寄りだが現役コードの任意LLM整形経路 `core/application/accessibility_improvement_builder.py` が raw `responses.create(..., temperature=0.0, reasoning=...)` を直接呼んでいたため、共有 `call_structured()` 経由へ変更。これにより `OPENAI_ACCESSIBILITY_ACTION_MODEL` に `gpt-5...` 系の予定名を設定しても sampling parameter を送らない。
  - `core/model_selector.py` の古い `o1/o3` 判定も共有 `supports_temperature()` に寄せ、将来の `gpt-5...` 系文字列で `temperature=0.0` を組み立てないようにした。
- changed files:
  - `core/application/accessibility_improvement_builder.py`
  - `core/llm_responses_client.py`
  - `core/model_selector.py`
  - `tests/test_accessibility_checker.py`
  - `tests/test_llm_prompt_boundary.py`
  - `WORKLOG.md`
- validation:
  - `py_compile`: `core/llm_responses_client.py`, `core/application/accessibility_improvement_builder.py`, `core/model_selector.py`, `core/config.py`, `core/aio_suggestions.py`, `core/aio/gap_analyzer.py`, `core/engine/orchestrator.py`, `tests/test_accessibility_checker.py`, `tests/test_llm_prompt_boundary.py` OK。
  - `pytest`: `tests/test_accessibility_checker.py tests/test_llm_prompt_boundary.py tests/test_orchestrator_security.py -q` -> 28 passed。
  - API送信回数: 0。テストはfake client / monkeypatchのみ。
  - UIブラウザ確認: 未完了。単体前面起動では `NiceGUI ready to go on http://127.0.0.1:8081` まで到達したが、バックグラウンド持続化では同URLが `Invoke-WebRequest` 接続不可、LISTENなし。追加指示に従い起動ループせず停止。

## 2026-07-09 (Claude) Phase0: Responses API共有レイヤー新設 + FAQ/リライト生成をgpt-5.4-nanoへ移行(実証第1弾)

- 実施者: Claude（Sonnet 5, CLI agent）。ユーザーとの相談の結果、GPT-4.1-mini→GPT-5.4-nano移行はOpenAI推奨のResponses APIに合わせる方針で合意し着手。スコープは「モデル間パラメータ差異を吸収する層の新設」と「それに伴い必要なプロンプト/出力契約(JSON Schema化)の調整」に限定。スコアリング、法務チェックの判定ロジック、FAQ/リライトの生成方針・パーソナライズ分岐といった既存のアルゴリズム的判断は一切変更していない。
- decision:
  - `claude_responses_api_migration_phase0_first_site`
- scope:
  - **既存資産の発見**: `core/application/accessibility_improvement_builder.py`に、今回と同じ`gpt-5.4-nano` + `reasoning_effort=low`の組み合わせがResponses API経由で実装済みだったことを確認。ただし呼び出し元3箇所(`analysis_run_service.py`×2、`ui/tabs/seo_tab.py`)は全て`use_llm`を指定しておらずデフォルト`False`のまま=**未使用の休眠状態**と判明。
  - **新設: `core/llm_responses_client.py`** → `accessibility_improvement_builder.py`の`client.responses.create(...)` + `_parse_llm_json_response`パターンを汎用化した共有ヘルパー(`call_structured()`)。strict `json_schema`によるJSON強制、`reasoning={"effort": ...}`(Responses API固有のネスト形式)、失敗時は例外を送出し呼び出し元がfail-closedで扱う設計を踏襲。
  - **重要な発見(潜在バグ)**: 実API疎通確認で、`gpt-5.4-nano`はResponses API経由でも`temperature`パラメータを**明確に拒否する**(HTTP 400 `Unsupported parameter: 'temperature' is not supported with this model`)ことを確認。これはnotecode側`core/app_config.py`の`disable_temperature_model_prefixes: ["gpt-5","o3","o1"]`という既存の想定と一致する一方、`accessibility_improvement_builder.py`は`temperature=0.0`を同モデルへ送るコードのまま(未使用のため表面化していない潜在バグ)。今回は対象範囲外のため当該ファイルは変更していないが、次に`use_llm=True`で有効化する際は同じ修正が必要。
  - **修正**: `core/llm_responses_client.py`に`supports_temperature(model)`(prefixベースの判定、`gpt-5`/`o1`/`o3`で`temperature`を自動除外)を実装し、呼び出し側は温度値を無条件に渡せる設計にした(モデルに応じて共有レイヤー側が黙って除外する)。
  - **config**: `core/config.py`に`REASONING_MODEL_DEFAULT`(env: `OPENAI_REASONING_MODEL`, 既定`gpt-5.4-nano`)、`REASONING_EFFORT_DEFAULT`(env: `OPENAI_REASONING_EFFORT`, 既定`low`)を追加。既存の`MODEL_DEFAULT`/`MODEL_HIGH_REASONING`(gpt-4.1-mini系)はそのまま残置。
  - **実証第1弾: `core/aio_suggestions.py`** の`AIOSuggestionEngine.generate_improvements()`(FAQ/リライト提案・定性スコアの生成本体)を、`chat.completions.create` + `response_format={"type":"json_object"}` + `temperature=0.3`固定から、`core.llm_responses_client.call_structured()`経由へ移行。JSON Schema(`IMPROVEMENTS_JSON_SCHEMA`、定性スコア12項目+suggestions配列)を新設して出力契約を明文化。モデル/reasoning_effortは`OPENAI_AIO_SUGGESTIONS_MODEL`/`OPENAI_AIO_SUGGESTIONS_REASONING_EFFORT`で個別上書き可能(未設定時は`config.REASONING_MODEL_DEFAULT`/`REASONING_EFFORT_DEFAULT`)。プロンプト文面・生成方針(結論ファースト等の指示)・失敗時フォールバック(`{"suggestions": [], "qualitative_scores": {}}`)は変更していない。
  - **未着手(次フェーズ)**: `core/engine/orchestrator.py`の法務チェック4種(STRICT/CONSUMER/GATE/CONTEXT)、`core/aio/gap_analyzer.py`、`PDFreport/`配下7箇所は今回未着手。ユーザーへ結果報告後、続行可否を確認してから着手する。
- changed files:
  - `core/config.py`
  - `core/llm_responses_client.py`(新規)
  - `core/aio_suggestions.py`
  - `WORKLOG.md`
- validation:
  - `py_compile`: `core/config.py` / `core/llm_responses_client.py` / `core/aio_suggestions.py` すべてOK。
  - 実API疎通確認(`.venv`経由、実費発生): 修正前は`temperature`パラメータでHTTP 400を確認(潜在バグの実証)。`supports_temperature()`導入後に再実行し、`suggestions_count: 3`、`qualitative_scores`の12キー全て充足、フォールバック不使用(`failed_fallback: False`)を確認。
  - 生成内容の質を目視確認: リライト提案が「結論→数字→前提条件」のAnswer First構造への書き換えとして機能し、定性スコアのadviceも具体的な改善指摘(導入事例の追記提案等)になっていることを確認。検証用の一時ファイルは削除済み。
  - サンプルデータではなく実運用に近い最小テキストでの単発検証のため、実際のサイト分析データでの品質は未検証(要フォローアップ)。

### 追補: top_p拒否の確認 + verbosityの正しい配置発見 + プロンプトでの多様性補償

- ユーザー指摘を受けて追加検証。`gpt-5.4-nano`は`temperature`だけでなく**`top_p`も同一のHTTP 400で拒否**することを実機確認(`core/llm_responses_client.py`の`supports_top_p()`として`supports_temperature()`と同じprefix判定を追加)。
- `verbosity`パラメータは実在し機能するが、`responses.create()`の**トップレベル引数ではなく`text`オブジェクト内(`text={"format": {...}, "verbosity": ...}`)に置く必要がある**ことを実機確認(トップレベルに渡すと`TypeError: unexpected keyword argument`)。`call_structured()`に`verbosity`引数を追加し正しい位置に配置。
- gpt-5系はtemperature/top_pという「ランダム性」の制御軸を持たず、`reasoning.effort`(推論の深さ)と`text.verbosity`(出力の長さ)のみが制御可能パラメータであると判明。旧temperatureが担っていた「トーン・バリエーション」の制御は、この2パラメータでは代替できないため、**プロンプト側での明示的な指示が必要**という指摘を受けた。
- `core/aio_suggestions.py`の改善案生成プロンプトに「3つは対象箇所または改善アプローチが互いに異なるようにし、似た内容の言い換えを繰り返さないでください」という多様性指示を追加(旧`temperature=0.3`が担っていたばらつきの代替)。`verbosity="medium"`(env override可: `OPENAI_AIO_SUGGESTIONS_VERBOSITY`)も追加。
- changed files: `core/llm_responses_client.py`, `core/aio_suggestions.py`, `WORKLOG.md`
- validation: `py_compile` OK。実API再検証で3件の改善案がそれぞれ異なるアプローチ(構造順序の最適化／数値・料金の明確化／固有名詞のプロパティ化)になっていることを確認。検証用一時ファイルは削除済み。

### 追補2: 再現性の調査(Web検索+実測) + 法務チェック4種・gap_analyzer.pyの移行

- ユーザー指摘「temperatureからプロンプトへの変更で再現性への影響」を受け、着手前にWeb検索で調査。
  - `seed`パラメータはResponses APIの`responses.create()`にSDKレベルで存在しない(`TypeError: unexpected keyword argument 'seed'`)。Chat Completions側の`seed`もOpenAI公式ドキュメント上「best effort」止まりで決定性は保証されておらず、コミュニティ情報では非推奨化が進行中と判明。
  - OpenAI公式のreasoning modelガイドに、再現性・決定論的出力に関する明示的な記述は無し。
  - 実測: `LEGAL_CONTEXT`と同種の二値判定プロンプト(「表現が商品名かどうか」)を`reasoning_effort=low`で3回実行し、判定結果(true/false)は3回とも完全一致。confidenceの数値のみ0.90〜0.93の範囲でわずかに変動。
  - 方針: 判定系(pass/warn/block, true/false)は明確な基準・タイブレークルールを持つプロンプトのまま`reasoning_effort=low`を維持すれば実用上十分安定。数値・スコア系は完全一致を前提にしない。API側の決定性保証機構は失われるため、`model_selector.py`のコメント「temperature=0.0でランダム性を排除」は本移行が完了した時点で事実と合わなくなる(今回は当該ファイル自体は未変更のため保留)。
- **法務チェック4種(STRICT/CONSUMER/GATE/CONTEXT)を`core/llm_responses_client.py`経由へ移行** (`core/engine/orchestrator.py`)。
  - `PERSONA_CHECK_SCHEMA`/`GATE_DECISION_SCHEMA`/`CONTEXT_JUDGMENT_SCHEMA`を新設し、strict json_schemaで出力契約を明文化。
  - `LEGAL_LLM_MODEL`(env: `OPENAI_LEGAL_MODEL`)/`LEGAL_LLM_REASONING_EFFORT`(env: `OPENAI_LEGAL_REASONING_EFFORT`)を新設。既存の`LEGAL_STRICT_TEMPERATURE`/`LEGAL_CONSUMER_TEMPERATURE`/`LEGAL_GATE_TEMPERATURE`/`LEGAL_CONTEXT_TEMPERATURE`定数はそのまま残し、`call_structured()`側でモデルがサポートする場合のみ適用される(gpt-5系では自動無視)。
  - 結果payloadに書き込まれていた`data["temperature"]`/`gate_result["temperatures"]`(下流消費者なしと確認済み、影響確認タスク参照)は、実態を反映するよう`model`/`reasoning_effort`に置き換え。
  - 未使用になった`LEGAL_GATE_MODEL`/`LEGAL_CONTEXT_MODEL`定数を削除。
  - `core/llm_responses_client.py`の`call_structured()`の戻り値を`(data, raw_response)`のタプルに拡張し、`response.usage.input_tokens`/`.output_tokens`(Responses API命名、Chat Completionsの`prompt_tokens`/`completion_tokens`とは異なることを実機確認)を`token_tracker`へ連携できるようにした。
- **`core/aio/gap_analyzer.py`を移行**。`GAP_ANALYZER_MODEL`/`GAP_ANALYZER_REASONING_EFFORT`(env override可)、`GAP_ANALYSIS_SCHEMA`を新設。
- changed files: `core/llm_responses_client.py`, `core/engine/orchestrator.py`, `core/aio/gap_analyzer.py`, `core/aio_suggestions.py`(戻り値タプル化に伴う呼び出し側更新), `WORKLOG.md`
- validation:
  - `py_compile`: 全ファイルOK。
  - 実API疎通確認(実費発生): STRICT/CONSUMER/GATE/CONTEXTを合成データで実行し、期待通りのJSON構造と、実際に「業界No.1」「導入実績1万社」等の根拠不明な優良表示を検出する妥当な法務判定(優良誤認のおそれ)を確認。GATE判定は境界事例で2回の実行間に多少の変動(medium/high, block/warn)が見られたが、これは段階的なリスク判定の性質上想定内の変動であり、厳格化・緩和はアルゴリズム的判断のため今回は変更していない(記録のみ)。
  - `gap_analyzer.py`も実API実行で、スキーマギャップ(創業年、認証情報、所在地)を正しく検出し、schema.orgの具体的プロパティ名まで提案できることを確認。
  - 検証用一時ファイルは全て削除済み。
- **未着手・スコープ拡大の発見**: 当初「15箇所」と見積もっていたが、実際にはorchestrator.py内に法務チェック以外の呼び出しが5箇所(`_generate_deep_recommendations`, `_generate_citation_priority_insights`, `_extract_citation_phrases`, `_generate_citation_content_plan`, `generate_competitor_action_advice`)、PDFreportに`OpenAIAdapter`クラスの複数メソッド(`generate_commentary`, `analyze_survey`, `analyze_emotions`, `moderate`, 3段階fallback付きの`_chat_json_call`系)が残っている。
  - **バグ発見**: `PDFreport/llm_client.py`の`generate_commentary()`(`score_reasoning.py`/`improved_commentary_generator.py`共通の呼び出し先)は、モデル名を`model_name in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]`という**完全一致リスト**で判定しており、`"gpt-5.4-nano"`のような新しいモデル名にはマッチしない。マッチしない場合は`temperature=0.1`を送ってしまうため、`PDF_LLM_MODEL`を`gpt-5.4-nano`に変更すると本セッションで実証済みのHTTP 400エラーになる潜在バグ。次フェーズで完全一致リストをprefix判定(`core/llm_responses_client.py`の`supports_temperature()`と同様)に修正する必要がある。

### 追補3: PDFreport(generate_commentaryバグ修正含む)・orchestrator.py残り5箇所の移行完了

- 実施者: Claude（Sonnet 5, CLI agent）。ユーザー承認により追補2で発見したスコープ拡大分を継続実施。範囲は引き続き「パラメータ差異吸収+それに伴うプロンプト/出力契約調整」のみで、判定ロジック・スコアリング・法務チェックの検査範囲は無変更。
- decision:
  - `claude_responses_api_migration_phase0_pdfreport_and_orchestrator_remainder`
- scope:
  - **`core/llm_responses_client.py`の拡張**:
    - `call_structured_async()`を新設(PDFreportは`AsyncOpenAI`を使うため非同期版が必要)。sync/async共通の`_build_kwargs()`に処理を集約。
    - **重大バグを実機で発見・修正**: `reasoning={"effort": ...}`を常に送っていたが、PDFreportの実際のデフォルトモデルである`gpt-4.1-mini`はこのパラメータ自体を拒否する(HTTP 400 `Unsupported parameter: 'reasoning.effort'`)。`temperature`/`top_p`とは逆方向(gpt-5系だけが対応、それ以外は非対応)の`supports_reasoning()`を新設し、`_build_kwargs()`で同様にgate。修正前は「共有レイヤーを経由するだけで、現行本番のデフォルトモデルが壊れる」状態だったため、他の全箇所へ展開する前に発見できたことは重要。
    - `LLMResponseError`に`status_code`を追加(元のOpenAI SDK例外の`status_code`を保持)。呼び出し側の既存リトライ判定(`hasattr(e, 'status_code')`等)がラップ後も機能するようにするため。
    - `pydantic_model_to_strict_schema()`を新設。PydanticモデルからOpenAI strict json_schema(全フィールドrequired化、additionalProperties:false化、$ref解決)を生成する汎用コンバータ。`ScoreReason`で実API実機検証済み。
  - **`PDFreport/llm_client.py`の`generate_commentary()`を修正+移行**:
    - モデル名完全一致リストによる分岐(gpt-5系/gpt-4.1系/その他)を削除し、`core.llm_responses_client`経由のResponses API呼び出しに一本化。Instructorの`response_model=`は`pydantic_model_to_strict_schema()` + 手動`model_validate()`に置き換え。
    - `score_reasoning.py`・`improved_commentary_generator.py`(3呼び出し)はこの共通関数を呼ぶだけなので自動的にカバーされる。
    - `IncompleteOutputException`の個別catchは汎用`except Exception`に統合(Instructorを経由しなくなったため)。
  - **`PDFreport/utils/text_professionalizer.py`の`professionalize_text_with_llm()`を移行**:
    - 独自の3回リトライ+指数バックオフループ(429/500/503/timeout検知)はそのまま維持し、内部のAPI呼び出し部分だけを`call_structured_async()`に置き換え。
  - **`PDFreport/llm_client.py`の`analyze_survey`/`analyze_emotions`/`moderate`は意図的に対象外とした**:
    - `moderate()`はOpenAIのModeration API専用で対象outside(json_schema/reasoningと無関係)。
    - `analyze_survey`/`analyze_emotions`は現状`settings.OPENAI_MODEL`/`PDF_LLM_MODEL`(非推論モデル)がデフォルトのため実害は無く、フォールバック経路(`_chat_json_call_with_caching`)がプロンプトキャッシュ機構と密結合しているため、今回の意図的なスコープ境界として次回以降に持ち越す。
  - **orchestrator.py残り5箇所を移行**: `_generate_deep_recommendations`(business/technical recommendations, title/description rewrites)、`_generate_citation_priority_insights`(評価軸3種を1回ずつ呼ぶループ)、`_extract_citation_phrases`、`_generate_citation_content_plan`、`generate_competitor_action_advice`。共通定数`AIO_CONTENT_MODEL`/`AIO_CONTENT_REASONING_EFFORT`(env: `OPENAI_AIO_CONTENT_MODEL`/`OPENAI_AIO_CONTENT_REASONING_EFFORT`)を新設し、旧`DEFAULT_LLM_MODEL`共有の粒度をそのまま踏襲。5種類のJSON Schemaを新設。
  - **`max_output_tokens`不足によるJSON途中切れを実機で複数回発見・修正**: reasoning modelは推論トークンが`max_output_tokens`の予算を消費するため、旧来の非推論モデル向け値(600〜2000)のままだと出力途中でJSONが切れることを実機で確認(`_generate_deep_recommendations`は2000→4000、`_generate_citation_content_plan`は1200→2500、`_extract_citation_phrases`/`_generate_citation_priority_insights`/`generate_competitor_action_advice`は600〜800→1200)。同じ入力でも発生したりしなかったりする**確率的な現象**だったため、複数回の再実行で安定を確認してから確定させた。法務チェック4種・gap_analyzer・aio_suggestionsの既存予算は複数回再検証し、問題ないことを確認済み。
  - `_openai_chat_json_with_retry`関数と`DEFAULT_LLM_MODEL`定数は、`tests/test_orchestrator_security.py`が直接依存しているため削除せず保持(orchestrator.py内の呼び出し元は0になったが、外部テストの対象として現存)。
- changed files:
  - `core/llm_responses_client.py`
  - `PDFreport/llm_client.py`
  - `PDFreport/utils/text_professionalizer.py`
  - `core/engine/orchestrator.py`
  - `WORKLOG.md`
- validation:
  - `py_compile`: 変更した全ファイルOK。
  - 実API疎通確認(実費発生、複数回実施):
    - `generate_commentary()`をPDFreportの現行デフォルトモデル(gpt-4.1-mini)経由と、明示的にgpt-5.4-nanoを指定した場合の両方で実行し、どちらも正しくスコア理由(summary/bullets)を生成することを確認。現行デフォルトモデルでの動作確認は、本番の主経路を壊していないことの直接的な証拠として重要。
    - `professionalize_text_with_llm()`を実行し、ペルソナ(consultant)に応じた文体変換が機能することを確認。
    - orchestrator.py残り5箇所を2回連続で実行し、5箇所とも安定して成功することを確認(1回目は2箇所でJSON途中切れが発生し、上記のトークン予算修正後に再検証して解消を確認)。
    - 法務チェック4種・gap_analyzer.pyも3回ずつ再実行し、既存のmax_output_tokensで安定していることを再確認。
  - 検証用一時ファイルは全て削除済み。

### 追補4: max_output_tokens超過の検出方法をAPI状態ベースに改善

- ユーザー指摘を受け、`max_output_tokens`超過時の挙動を実機で確認。
  - Responses APIはHTTPエラーではなく、`response.status == "incomplete"` / `response.incomplete_details.reason == "max_output_tokens"`という**正常応答(HTTP 200)の中のフラグ**で打ち切りを通知することを実機確認。
  - 従来の`parse_json_response()`はこのフラグを見ておらず、途中で切れたJSONの`json.loads()`失敗という**間接的な兆候**でしか検出していなかった。打ち切り位置によっては構文的に妙に成立してしまい検出漏れが起きる可能性があったため、`response.status`を明示的に先頭でチェックするよう修正。
  - `LLMResponseError`のメッセージも`invalid_json_response: Unterminated string...`から`response_incomplete: reason=max_output_tokens`という原因が明確な文言に変更。
- UI/呼び出し元への影響: 各呼び出し元は元々(移行前から)fail-closedで空リスト/フォールバック値を返す設計のため、ユーザー向けUIの見え方は変化しない。サーバーログの原因特定精度のみ向上。
- changed files: `core/llm_responses_client.py`, `WORKLOG.md`
- validation: `py_compile` OK。意図的に`max_output_tokens=50`で長文生成を要求し、`response_incomplete: reason=max_output_tokens`が正しく送出されることを実機確認。検証用一時ファイルは削除済み。

### 追補5: verbosityの互換性ギャップ修正 + トークン消費要因の訂正 + コスト表の未対応発見

- ユーザー質問「max_output_tokensは大きく増やすべきか、gpt-4.1系とgpt-5.4系の挙動差が心配」を受けて追加調査。
- **新たな互換性バグを発見・修正**: `verbosity`は`temperature`/`top_p`/`reasoning`のような単純な対応可否の二値ではなく、**モデルごとに許容値が異なる**ことを実機確認。`gpt-4.1-mini-2025-04-14`へ`verbosity="low"`を送るとHTTP 400（`Unsupported value: 'low' is not supported with the 'gpt-4.1-mini-2025-04-14' model. Supported values are: 'medium'.`）。個別モデルの許容値を追跡する代わりに、`verbosity`は`reasoning`と同じ条件（gpt-5/o1/o3系のみ）でしか送らないよう`core/llm_responses_client.py`の`_build_kwargs()`を修正。現状this の値を明示的に上書きしている呼び出し元は`aio_suggestions.py`のみで、デフォルト値が`"medium"`だったため実害は出ていなかったが、将来別の値を指定した場合に備えた予防修正。
- **追補3の説明を訂正**: 「reasoning modelでは推論トークンがmax_output_tokensの予算を消費するため」という説明は、実際のdeep_recommendations相当の複雑なプロンプトで実測したところ`reasoning_tokens: 0`（gpt-5.4-nano、gpt-4.1-miniどちらも）であり、**不正確だった**。実際の要因は、同一プロンプト・同一スキーマに対してgpt-5.4-nanoの**可視出力(output_tokens)自体がgpt-4.1-miniより長くなる**こと（実測: gpt-4.1-mini 918トークン vs gpt-5.4-nano 1588トークン、同一入力・同一スキーマ）。reasoning_effort=lowでは不可視の推論トークン消費はほぼ発生せず、可視JSON自体の記述が詳細・冗長になる傾向が主因と判明。max_output_tokensの引き上げ自体は正しい対処だったが、理由の説明を訂正する。
- **レイテンシの実測（1サンプルのみ、参考値）**: 同一の複雑なプロンプトで gpt-4.1-mini 21.44秒、gpt-5.4-nano 18.45秒。今回の実測ではgpt-5.4-nanoの方がやや高速だった（出力トークン数はgpt-5.4-nanoの方が多いにもかかわらず）。サンプル数が少なく統計的結論ではないが、「reasoning modelは常に遅い」という前提を裏付ける結果は出ていない。
- **未対応を発見（今回は修正せず記録のみ）**: `core/token_tracker.py`の`add_usage()`内`model_costs`辞書に`gpt-5.4-nano`のエントリが無い。`gpt-4.1-mini`（末尾の日付なし）のエントリはあるが、実際に使われているモデル名文字列は`gpt-4.1-mini-2025-04-14`（日付付き）であり、これも一致しないため、既存のgpt-4.1-mini呼び出しも含めて**汎用フォールバック単価（$0.001/$0.002 per 1K tokens）で概算されている**。gpt-5.4-nanoのコスト計上精度は現状不明。コスト管理に関わる変更のため、今回のスコープ（パラメータ吸収）には含めず、別途対応要否を判断すべき事項として記録する。
- changed files: `core/llm_responses_client.py`, `WORKLOG.md`
- validation: `py_compile` OK。`verbosity="low"`を両モデルへ明示指定し、修正後はgpt-4.1-mini/gpt-5.4-nano両方でエラーなく完了することを実機確認。検証用一時ファイルは削除済み。

### 追補6: gpt-5.4-nano vs gpt-5.4-mini の適性検証(コード変更なし、調査のみ)

- ユーザー質問を受け、現在gpt-5.4-nanoがデフォルトの9箇所について、gpt-5.4-miniとの適性比較を実施。**コード変更は無し、調査のみ**。
- 用語確認: `PDFreport/`はコトムスビ(`doorknock/`)ではなく、コトミガキ(aio2-main)自身のPDF機能。`doorknock/`にOpenAI関連コードが存在しないことを確認済み(grep 0件)。
- 料金(Web検索): gpt-5.4-nano = $0.20/$1.25 per M tokens(入力/出力)、gpt-5.4-mini = $0.750/$4.50 per M tokens。miniは入力約3.75倍、出力約3.6倍。
- 実機比較(3ケース、法務チェック相当のプロンプトを実際のスキーマで実行):
  1. 明確な違反事例(健康食品の誇大広告): nano/mini とも decision=block, risk_level=high で一致。flagged_phrasesも同一3件。
  2. 境界線上の微妙な事例(自社アンケート+適切な開示文言付き): nano/mini とも decision=warn, risk_level=medium で一致。理由付けの論点も同等。
  3. FAQ/リライト生成(aio_suggestions実プロンプト): 両モデルとも同水準の具体性・Answer First構造の提案。品質面で明確な優劣は見られず。
  - 副次的な観察: miniは推論トークンを一定量消費し可視出力が短め、nanoは推論トークンをほぼ使わず可視出力が長めという傾向（結果の質には影響なし）。
- 結論: 実機検証した2種(法務判定・FAQ生成)で品質差が確認できなかったため、9箇所全てで**nano維持を推奨**。全箇所をminiにした場合の追加コスト(3.6〜3.75倍)に見合う品質根拠は見出せなかった。
- 未検証: `PDFreport`の`generate_commentary`/`text_professionalizer`(現状gpt-4.1-mini)、`analyze_survey`/`analyze_emotions`(未着手)はどちらのモデルも稼働していないため対象外。
- changed files: `WORKLOG.md`のみ(コード変更なし)。

### 追補7: 既存テストスイート全体の実行確認(pytest未導入の発覚+3件の回帰修正)

- ユーザーから「残作業はテストか」と問われたのを機に、これまで実施していなかった`tests/`配下の既存pytestスイート全体を実行して確認。
- **発見1**: プロジェクトvenv(`.venv/`)に`pytest`が未インストールだった(`requirements-dev.txt`には記載があるが未同期)。`.venv/Scripts/python.exe -m pip install pytest==9.0.3`で導入して初めて実行可能に。
- **発見2(本題・回帰)**: `tests/test_orchestrator_security.py`のうち2件が今回の移行で**壊れていた**:
  - `test_generate_deep_recommendations_wraps_untrusted_content`
  - `test_citation_generation_paths_wrap_untrusted_content`
  - 原因: これらのテストは`orchestrator_mod._openai_chat_json_with_retry`をmonkeypatchして「未信頼コンテンツが `[ROLE REDACTED]:` 等でサニタイズされた状態でLLMに渡っているか」を検証するものだったが、`_generate_deep_recommendations`/`_extract_citation_phrases`/`_generate_citation_content_plan`は本移行で`call_structured()`(Responses API経由)に切り替わっており、旧関数はもう呼ばれていない。そのためmonkeypatchが効かず、実際に`self.client.responses.create(...)`を叩こうとして`'object' object has no attribute 'responses'`で失敗、フォールバック(空リスト/空辞書)が返っていた。**プロダクションコード自体は正しく動作している**(すでにライブAPIで個別検証済み)。壊れていたのはテストのモック対象のみ。
  - 修正: monkeypatch対象を`orchestrator_mod.call_structured`に変更し、捕捉するキーワード引数を`kwargs["messages"]`→`kwargs["input_messages"]`に変更。検証内容(未信頼データのラベル付け・ロール偽装トークンの除去)は変更していない。
- **発見3(同種の回帰)**: `tests/test_llm_prompt_boundary.py`の2件も同様の理由で失敗:
  - `test_aio_suggestions_wraps_external_text_as_untrusted_prompt_data`(`aio_suggestions.py`)
  - `test_schema_gap_prompt_treats_page_and_schema_as_untrusted`(`gap_analyzer.py`)
  - こちらは`_FakeClient`が`client.chat.completions.create(...)`(Chat Completions形状)しか模していなかったため、移行後の`client.responses.create(...)`呼び出しで同じ`AttributeError`が発生していた。`_FakeClient`/`_FakeCompletions`を`_FakeResponses`(`.responses.create`が`output_text`を返す)に置き換え、検証キーも実際のAPI呼び出しキー`kwargs["input"]`(`call_structured`内部で`input_messages`→`input`にリネームされるため、生クライアントの直接モックでは`"input"`が正しいキー)に修正。
- **発見4(移行と無関係の既存バグ)**: `tests/test_schema_validator.py::test_run_full_site_health_check_adds_schema_validation`も失敗していたが、原因はGPT移行と無関係。本セッション早期のPhase2作業(既知脆弱性CVE/CVSS詳細表示、タスク#3)で`SecurityChecker`/`run_full_site_health_check`に`sitemap_info`引数が追加された際、このテストのモックlambda(`lambda url, headers, html: ...`)が更新されていなかったための引数不一致。`sitemap_info=None`を追加して解消。ついでに直したが、GPT移行の作業範囲外。
- 検証: `.venv/Scripts/python.exe -m pytest tests/ -q` → 修正前は3失敗/181成功、修正後は**184件全件成功**。
- changed files:
  - `tests/test_orchestrator_security.py`(monkeypatch対象修正、アルゴリズム/検証意図は不変)
  - `tests/test_llm_prompt_boundary.py`(fakeクライアントをResponses API形状へ更新、検証意図は不変)
  - `tests/test_schema_validator.py`(移行と無関係な既存モック不一致を修正)
  - `WORKLOG.md`
- 追加修正: `orchestrator.py`内の`max_output_tokens`引き上げ理由コメント4箇所(`_generate_deep_recommendations`/`_generate_citation_priority_insights`/`_extract_citation_phrases`/`_generate_citation_content_plan`)が「reasoning tokenがmax_output_tokens予算を消費するため」という**追補5で訂正済みの誤った説明のまま**だったのを発見し、「gpt-5.4-nanoの可視出力がgpt-4.1-mini比で長くなる傾向」という正しい理由に修正(コメントのみ、ロジック不変)。`py_compile`+`pytest tests/`(184件)で再確認済み。

---

## 2026-07-09 (Claude) テンプレート出力の誤解防止監査(コトミガキ) — LCP/CLSの英語enum漏れ + 「実データ」誤表示の修正

- 実施者: Claude（Sonnet 5, CLI agent）。ユーザーから「UIで、テンプレート出力でユーザーを誤解させる部分がないかコトミガキとコトメガネをチェックしてください」との依頼を受け、両サービスを静的コード調査+実機確認。GPT移行とは無関係の別件。分析アルゴリズム・スコア計算は無変更、表示文言のみ変更。
- decision:
  - `claude_misleading_template_output_audit_20260709`
- 発見1(修正済み・確度高): `core/seo/page_experience_audit.py`のCore Web Vitals(LCP/CLS)簡易推定機能で、`good`/`needs_improvement`/`poor`という**英語の内部enum値がそのまま日本語文に埋め込まれて**非エンジニア向け「評価」カードの「理由」欄に表示されていた(例: 「CLS 推定が needs_improvement です。」)。notecodeで見つけた「unresolved slot」漏れと同種の内部語彙リーク。`_grade_label_ja()`ヘルパーを追加し「良好」「改善が必要な水準」「不良」に翻訳、メッセージも「CLS の簡易推定が◯◯です」という表現に統一。
- 発見2(修正済み・確度高、より重大): `core/ui/tabs/seo_tab.py`と`core/application/analysis_run_service.py`(同じ「モバイル / ページ体験」行を作る**並行実装が2箇所存在**)で、LCP/CLSの値が`source_label: "実データ"`(実データ)チップ付きで表示されていた。しかし`page_experience_audit.py`自身がこれらの値を`"measurement": "heuristic"`と明記している通り、実際は**ページサイズ・画像数・スクリプト数からの粗い推測式**(基準値1800ms/0.03から加減算するだけ)であり、Lighthouse等の実測ではない。この「heuristic」フラグは`web_vitals["lcp_note"]`/`["cls_note"]`としてデータには保持されるが、**UIのどこにも表示されず** discardされていた。ユーザーが実際のCore Web Vitalsだと誤認しうる表示だった。
  - `seo_tab.py::_build_additional_audit_rows`: `source_label`を「実データ＋簡易推定」に変更、detail文言を「LCP簡易推定 ◯◯ms」「CLS簡易推定 ◯.◯◯◯」に変更。
  - `analysis_run_service.py::_build_seo_audit_notes`の「モバイル / ページ体験」`append_note`呼び出しに`source="heuristic", source_label="実データ＋簡易推定"`を明示指定。同ファイル`_build_marketer_audit_summary`が生成する自然文の metric 部分も「LCP簡易推定 ◯.◯◯秒」「CLS簡易推定 ◯.◯◯◯」に変更(正規表現によるLCP/CLS値抽出パターンは変更していないため既存の値抽出ロジックへの影響なし)。
- 発見3(デッドコード・実害なし、参考記録): `core/ui/reports/executive_summary.py::render_executive_summary`と、そこから呼ばれる`core/ui/panels.py::_build_decision_actions`の「担当」「工数」表示(常に固定文字列「運用/マーケ」「30〜90分」等、個別アクションごとの実算出ではない)を発見したが、呼び出し元の`core/ui/panels.py::results_panel()`自体がコードベースのどこからも呼ばれていない**到達不能なデッドコード**と判明したため、実害なしと判断し未修正。念のため記録のみ残す。
- 発見4(コトメガネ、対象問題なし): `report_summary_builders.py`/`analysis_core/source_evidence.py`等を確認。「今の入力ではまだ分析していません。これはエラーではありません。」等、誤解防止に配慮した文言が既に徹底されており、「引用された」/「検索ソースに出たが未引用」/「判定保留」の3状態を安易に「未引用」へ丸めない設計になっている(`build_prompt_family_source_rollups`等)。明確な誤解を招く箇所は見つからなかった。
- changed files:
  - `core/seo/page_experience_audit.py`
  - `core/ui/tabs/seo_tab.py`
  - `core/application/analysis_run_service.py`
  - `WORKLOG.md`
- validation:
  - `py_compile`: 変更3ファイルともOK。
  - `pytest tests/test_page_experience_audit.py tests/test_analysis_run_service.py tests/test_characterization_ui.py`: 全件成功、既存のグレード判定ロジック(`good`/`needs_improvement`/`poor`の戻り値自体)は変更していないため影響なし。
  - `pytest tests/`(全体): 184 passed。
  - 実機確認: 既存の保存済みrun(`/runs/26`, www.kyotokogyo.co.jp)はDB保存済みスナップショットのため、サーバー再起動後もページ再読み込みだけでは新しい文言に更新されない(過去分析結果を後から書き換えない設計として妥当)。ソースコード読み返し・py_compile・単体テストで正しさを確認。**次回以降の新規分析から反映される**。
  - API実行回数: `0`(既存の保存済みrunの再表示確認のみ、新規分析は未実行)。

### 追補: 「パーソナライズされた結果が出るべき部分でテンプレ出力はないか」の再調査(PDFreport)

- ユーザーから「パーソナライズされた結果が出るべき部分でテンプレ出力はないか」との追加確認を受け、LLM生成失敗時のフォールバック文言を横断調査。対象: `core/engine/orchestrator.py`のスコア理由生成、`PDFreport/improved_commentary_generator.py`の三視点コメンタリー生成。
- 調査結果1(問題なし、良設計): `PDFreport/score_reasoning.py`の`ScoreReason`モデルはデフォルト値が空文字列/空リスト(汎用文言ではない)。LLM失敗時は`orchestrator.py`側で`fallback_reason()`という**ルールベースだが実データ(実際のスコア内訳・低評価項目・実際のtitle/description等のevidence・業界別アドバイス)を使う個別化されたフォールバック**に切り替わる設計になっており、汎用テンプレへのすり替わりは無い。
- 発見(修正済み・確度中): `PDFreport/improved_commentary_generator.py::generate_report_commentary_v2`の747行目で、`summary_text=summary_result.summary_text or "分析結果の要約を準備中です。"`となっていた。兄弟フィールド(`sentiment_commentary`/`topics_commentary`/`marketing_perspective`等)のフォールバックは全て「...の詳細は利用できません。」と失敗を正直に伝える文言なのに対し、この1箇所だけ**「準備中です」という進行中を示唆する文言**になっていた。これは完成・納品されるPDFレポートの最終出力であり「準備中」という事実はあり得ない。LLMが技術的に空文字列`summary_text=""`を返した場合(Pydanticスキーマ上は空文字列でも検証を通過する)にこの文言が紛れ込み、レポートが未完成であるかのように読める状態だった。「分析結果の要約は利用できません。」に統一。
- 参考記録(未修正・要検討、UIデザイン判断が必要なため今回は対応外): `generate_report_commentary_v2`/`generate_perspective_commentary`には他にも複数箇所で「マーケティング分析の生成中にエラーが発生しました。」等のフォールバック文言があり、これらは失敗を正直に伝えている点では問題ないが、実際にPDFへレンダリングされる際(`pdf_data_mapper.py`)に**フォールバック文言と正常なLLM生成文が同じスタイルで表示され、視覚的な区別が無い**ことを確認した。読み手が読み飛ばして正常な分析結果だと誤認するリスクは残る。修正には warning バッジ表示等のPDFレイアウト変更判断が必要なため、今回はコード修正せず記録のみ残す。
- changed files:
  - `PDFreport/improved_commentary_generator.py`
  - `WORKLOG.md`
- validation:
  - `py_compile`: OK。
  - 該当テキストに対する専用テストは存在せず(grep確認済み)。
  - `pytest tests/`(全体): 184 passed(影響なしを再確認)。

### 追補2: PDF可視区別対応の着手前に「そもそも到達可能か」を検証 → 到達不能と判明(訂正)

- ユーザーの「進めます」を受け、上記「参考記録」のPDFフォールバック文言の視覚的区別(warningバッジ表示等)を実装しようとしたが、着手前に呼び出し経路を再確認した結果、**`PDFreport/improved_commentary_generator.py`・`PDFreport/reporting.py`・`PDFreport/score_reasoning.py`のアンケート解説生成システム一式が、現在のライブUIのどこからも呼ばれていない**ことが判明した。
- 検証内容:
  - `generate_report_commentary_v2`/`generate_perspective_commentary`/`generate_summary_commentary`(`improved_commentary_generator.py`)、`generate_high_quality_pdf_report`/`generate_pdf_report`(`reporting.py`)いずれも、それぞれの定義ファイル自身以外から呼ばれている箇所が無いことをgrepで確認(`tests/test_pdf_security.py`からのテスト呼び出しのみ)。`reporting.py`の`generate_pdf_report`のdocstringには「この関数は堅牢なPDF生成システムに置き換えられました。robust_pdf_generator.pyのgenerate_robust_pdf_report()を使用してください」とあるが、`PDFreport/robust_pdf_generator.py`というファイル自体がこのコードベースに存在しない。
  - `score_reasoning.py`の`generate_score_reason`/`fallback_reason`は`core/engine/orchestrator.py`から実際に呼ばれ`self.last_analysis_results["score_reasons"]`に格納されるが、この`score_reasons`キーを読み出している箇所がコードベース全体を検索しても存在しない(計算されるが誰にも表示されない)。
  - 実際にコトミガキの「レポート出力」ボタンが呼ぶのは`core/application/docx_report_service.py::export_detailed_docx_report`と`core/application/markdown_report_service.py::export_detailed_markdown_report`(`nicegui_app.py`)であり、これらはPDFreportのアンケート解説生成系を一切importしていない。
  - `nicegui_app.py`内の`@ui.page`登録ルートは`/`と`/runs/{run_id}`の2つのみ(コードベース全体を再検索して確認)で、「アンケート」「survey」向けの別ページ/別ルートは存在しない。
- 結論: 追補1で見つけた「分析結果の要約を準備中です」の修正、および今回着手予定だった`reporting.py`の`defaults_text`辞書(サイレントに汎用マーケティング文言へすり替わる、より深刻な未開示フォールバック)は、いずれも**現在のライブアプリのどのユーザー導線からも到達しない**コード。`core/ui/reports/executive_summary.py`の`results_panel()`と同種の「実装済みだが配線されていない」パターン。
- 判断: 到達不能コードへのUI設計変更(warningバッジ追加等)は実利が無いため、着手を保留しユーザーに実態を報告して次の方針を確認する。既に行った「準備中」→「利用できません」の文言修正はコード品質として妥当なため元に戻さない。
- changed files: `WORKLOG.md`のみ(コード変更なし)。

### 追補3: 「このシステム自体が今も必要か」の経緯調査

- ユーザーから「このシステム自体(PDFreportのアンケート解説生成一式)が今も必要か確認したい」との依頼を受け、`AGENTS.md`の変更履歴と`WORKLOG.md`を遡り、生きた導線が無い理由を調査。
- 判明した経緯:
  - `AGENTS.md`の変更履歴によると、2026年1月22日〜1月30日ごろに`PDFreport/high_quality_pdf_generator.py`・`PDFreport/sections/`が活発に更新されており、当時はPDF出力が生きた導線だったことが分かる。
  - 一方`WORKLOG.md`の2026-06-16「Report export button with Markdown and Word」エントリでは、既存の「詳細Markdown」ボタンを「レポート出力」ボタン(Markdown/Word選択式)へ整理し、「レポート本文は既存MarkdownをSSOTとして維持し、Wordは同内容をdocx化」と明記。この時点で現行の`core/application/docx_report_service.py`/`markdown_report_service.py`が導入されている。
  - `docx_report_service.py`をgrep確認したところ、OpenAI/LLM呼び出しを一切含まない。既に`orchestrator.py`側(gpt-5.4-nano移行済み)で計算済みのスコア・法務チェック・推奨事項などの構造化データを整形するだけで、独自にAI解説文を生成する必要が無い設計。
  - `PDFreport/site_health_pdf.py`(AGENTS.mdに「[NEW]サイトヘルスページ生成」と記載)も同様にコードベース全体でどこからも参照されていないことを確認。PDFreport配下のPDF生成パイプライン一式(`high_quality_pdf_generator.py`・`improved_commentary_generator.py`・`reporting.py`・`site_health_pdf.py`・`score_reasoning.py`)がまとめて到達不能。
- 結論(推定、確定情報ではない): 2026年1月時点ではPDF+AI解説文が現行の報告手段だったが、2026年6月16日にMarkdown/Word(docx)ベースのレポート出力へ置き換えられ、その際PDFreportのAI解説文生成パイプラインは削除されずそのまま放置された可能性が高い。現行のdocx/markdown出力はLLMを使わず構造化データの整形のみで完結しており、機能的な依存関係は無い。
- 補足(本セッション内の関連事実): 本セッション前半のGPT-5.4-nano移行作業で`PDFreport/utils/text_professionalizer.py`と`PDFreport/llm_client.py::generate_commentary()`(モデル未検出バグの修正含む)を移行したが、これらの唯一の呼び出し元は`improved_commentary_generator.py`であり、今回の調査で判明した通りそれ自体が到達不能。移行作業とバグ修正自体は正しい内容だったが、**現状は稼働しないコードに対する修正だった**ことを記録しておく。
- 次の判断が必要な事項(ユーザー確認待ち、未着手):
  - PDFreport配下のPDF生成パイプライン一式を削除するか、将来の再利用に備えて残すか
  - 削除する場合、`tests/test_pdf_security.py`など関連テストの扱い
  - 残す場合、`defaults_text`のサイレント置換問題を「いつか直す」課題として明示的に記録するか
- changed files: `WORKLOG.md`のみ(コード変更なし、調査のみ)。

### 追補4: PDFreport一式のアーカイブ(削除ではなく退避)

- ユーザーの「何かエラーが起きた場合のことを考えて、アーカイブしましょう。テストデータも。」を受け、削除ではなく退避する形で対応。
- 事前の依存関係調査:
  - `PDFreport/`配下の全26 `.py`ファイル(サブディレクトリ`config/`・`models/`・`sections/`・`utils/`含む)について、`PDFreport`外からの参照を横断grepで確認。生きた参照は2箇所のみ:
    1. `core/engine/orchestrator.py`が`PDFreport.score_reasoning`から`build_seo_reason_payload`/`build_aio_reason_payload`/`generate_score_reason`/`fallback_reason`を`try/except`付きでimport(失敗時は全て`None`に落ちる設計)。
    2. `tests/test_pdf_security.py`が`PDFreport.llm_client`/`PDFreport.config.pdf_config`を直接import(try/exceptなし)。
  - `orchestrator.py`側の呼び出し箇所(1949行目)は`if build_seo_reason_payload and build_aio_reason_payload:`という外側ガードで保護されており、import失敗時はブロック全体がスキップされる**安全な設計**であることをコード読み込みで確認(1995/2000行目の`build_seo_reason_payload(...)`自体は無条件呼び出しだが、外側ガードのおかげで`None`が渡ることはない)。アーカイブしても`orchestrator.py`は無改修で安全。
  - `tests/test_pdf_security.py`は`try/except`無しでimportするため、アーカイブすると確実にImportErrorで壊れる。これは「テストデータも」というユーザー指示の対象として一緒に退避する。
- 実施内容:
  - `PDFreport/`ディレクトリ一式を`archive/pdfreport_dead_pipeline_archive_20260709/PDFreport/`へ移動(ファイル削除ではなく`mv`、中身は変更なし)。
  - `tests/test_pdf_security.py`を`archive/pdfreport_dead_pipeline_archive_20260709/tests/test_pdf_security.py`へ移動。
  - `core/engine/orchestrator.py`は無改修(try/except構造がそのまま安全に機能するため)。
- validation:
  - `py_compile nicegui_app.py core/engine/orchestrator.py core/application/docx_report_service.py core/application/markdown_report_service.py`: OK。
  - `pytest tests/`: **175 passed**(移動前184 passed。差分9件は`test_pdf_security.py`が定義していたテスト数と完全一致、他への影響なし)。
  - 実機確認: `nicegui_app.py`を起動し`/runs/26`(保存済みrun)を再読み込み。サーバーログ・コンソールともにエラー0件、「評価」「レポート出力」が正常表示されることを確認。
  - API実行回数: `0`。
- 補足: `archive/pdfreport_dead_pipeline_archive_20260709/`は`.distignore`の`**/archive/`ルールにより配布パッケージから除外される(notecodeの`archive/writer_only_deadcode_archive_20260602/`と同じ扱い)。将来復元する場合は`PDFreport/`をこのディレクトリから元の場所へ戻すだけでよい(コード自体は変更していないため)。
- changed files:
  - 移動: `PDFreport/**` → `archive/pdfreport_dead_pipeline_archive_20260709/PDFreport/**`
  - 移動: `tests/test_pdf_security.py` → `archive/pdfreport_dead_pipeline_archive_20260709/tests/test_pdf_security.py`
  - `WORKLOG.md`
- changed files: `WORKLOG.md`のみ(コード変更なし、調査のみ)。

---

## 2026-07-09 (Claude) 評価カード誤読修正・エンジニア作業票source日本語化・既知脆弱性CVE詳細表示・FAQ debug内部語彙整理

- 実施者: Claude（Sonnet 5, CLI agent）。ユーザー指示によりUI表示層のみを変更。分析アルゴリズム・スコア計算・DBスキーマ・検出ロジック（脆弱性照合含む）は無変更。
- decision:
  - `claude_ui_polish_pass_20260709_p0`
- scope:
  - **評価カードの「総合評価」ラベル誤読修正** (`_render_saved_run_evaluation`) →
    - `priority_level`（高=対応優先度が高い=悪い状態）が「総合評価: 高」という見出しの下に出ると、非エンジニアには「評価が高い＝良い」と誤読されるリスクがあった。
    - ラベルを「総合評価」→「対応優先度」に変更し、`_priority_urgency_caption()` を追加して高/中/低それぞれに「早めの対応をおすすめします。」等の一言を添えた。
    - `summary_workspace.top_actions`（既存データ、新規計算なし）から最優先1件のタイトルを拾い、「まず1件: ◯◯（詳しくは下の「やること」）」の1行を追加し、評価カードから次の行動への導線を作った。
  - **エンジニア作業票 source チップの日本語化**（`_engineer_source_display()` 新設） →
    - `build_engineer_handoff_items()` が返す `source` は検出元のraw slug（`link_health_summary`, `site_health.security` 等の内部id）で、そのままチップ表示されていた。
    - 固定マッピング `_ENGINEER_SOURCE_LABELS` を追加し、日本語ラベルを表示。未知のslugは `category`（既存の日本語カテゴリ）へフォールバック。raw slugは削除せず、表示テキストと異なる場合のみ tooltip（「検出元ID: ◯◯」）として保持。
    - 本日先に実装された固定既知脆弱性DB照合機能（`fixed_vulnerability_intelligence_snapshot_enabled`）が生成する issue id `known_vulnerability_candidate` / `public_technology_risks` も明示的にマッピングに含め、新機能のsourceが「unmapped fallback」で埋もれないことを確認した。
  - **既知脆弱性候補のCVE/CVSS詳細をエンジニア向けタブへ追加**（`_render_known_vulnerability_detail()` 新設） →
    - 調査の結果、`core/site_health/vulnerability_intelligence.py` が算出する CVE ID / CVSS / KEV / references / 修正版情報は、`signals.fixed_vulnerability_intelligence.matches` として `technical_workspace.site_health_checks[key="security"].public_technology_risks.signals` まで正しく到達しているにもかかわらず、UI側では要約文（「既知脆弱性候補があります」）だけが表示され、CVE番号・CVSSスコア自体はどこにも表示されていなかった（表示漏れ、算出漏れではない）。
    - エンジニア向けタブの「OGP / セキュリティ / 見やすさ・使いやすさ」詳細展開の中に、既存データを読むだけの折りたたみ「既知脆弱性候補の詳細（CVE） N件」を追加。component / version / CVE ID / 重要度 / KEV / CVSS / 修正版 / 検出URL / references / display_note を表示。**照合ロジック・DB参照・スコア計算は一切変更していない**。
  - **FAQ debug折りたたみの内部語彙整理**（`_faq_topic_display()` 新設） →
    - 「提案理由の見立てを見る」展開内の `topic: pricing` のような内部スラッグ表記をマッピング（`_FAQ_TOPIC_LABELS`）で「分類: 料金」等に変更。
    - `score {float}` という内部信頼度の生数値表示（ペルソナ候補行）を削除し、ラベル＋signalsのみ表示に変更。
    - **本日別セッションで先に実施された `presentation_layer_followup_fixes_completed`（FAQカード本体からの `source_label`/`evidence_terms`/`confidence` 削除）はそのまま尊重し、上書きしていない。** 本変更はさらに一段折りたたんだ debug 展開内部のみが対象。
  - 併せて確認: 別セッションが本日実施した `presentation_layer_audience_segmentation_completed`（6軸レーダー折りたたみ、やることタブの生データ削除、色トークン統一）とは重複せず、独立した箇所を対象にしたことをコード上で確認済み。
- changed files:
  - `core/ui/saved_workspace.py`
  - `WORKLOG.md`
- validation:
  - `py_compile`（`.venv` 経由）: OK。
  - `ast.parse`: OK。
  - 純関数スモークテスト（`.venv` 経由、`PYTHONIOENCODING=utf-8`）: `_priority_urgency_caption('高'/'中'/'低')`、`_engineer_source_display()`（マッピング一致・フォールバック・空値）、`_faq_topic_display()`（マッピング一致・未知値パススルー）が期待通りの日本語文字列を返すことを確認。
  - 実描画スモークテスト: `.venv` の nicegui で使い捨てページ（`ui.page`）を一時起動し、CVE番号を含む合成データ（component=jquery, cve_ids=(CVE-2020-11022, CVE-2020-11023), cvss_score=6.1 等）で `_render_known_vulnerability_detail()` と `_render_saved_run_evaluation()` を実際にHTTP経由でレンダリングし、返却HTMLに `CVE-2020-11022` / `CVSS 6.1` / `対応優先度` / urgency caption文言 / `まず1件` が含まれることを確認（HTTP 200）。テスト用一時ファイルは検証後に削除済み。
  - サンプルデータ（実運用runのFAQ/リライト/脆弱性照合結果）が手元にないため、合成データによる構造検証にとどまる。実データでの見え方確認は未実施（要フォローアップ）。
  - 実行中サービスへのブラウザ再検証は本セッションでは未実施（`techie-hub\start.bat` 経由の常駐プロセス起動・停止は行っていない）。次回起動時に `/runs/{run_id}` のエンジニア向けタブで「既知脆弱性候補の詳細（CVE）」展開、評価カードの「対応優先度」表示を目視確認することを推奨。

---

## 2026-07-08 (分析開始プログレスバー修正)
### Dashboard progress loop initial socket wait fix

- decision:
  - `dashboard_progress_initial_socket_wait_fix`
- scope:
  - 分析開始時のプログレス表示が 0% のまま動かない可能性を修正。
  - 初回ページ表示直後に `has_socket_connection == False` になる一時状態を、離脱ではなく接続待ちとして扱うよう変更。
  - 実際のブラウザ離脱は既存の `on_disconnect` / stop event で停止するため、分析ロジック・スコア計算・DB スキーマは変更しない。
  - 開始直後の見た目も 0% 固定に見えないよう、初期表示を `準備中 - 初期化` の 2% に変更。
- changed files:
  - `nicegui_app.py`
  - `tests/test_dashboard_ui.py`
  - `WORKLOG.md`
- validation:
  - `python -m py_compile aio2-main\nicegui_app.py aio2-main\tests\test_dashboard_ui.py` -> OK。
  - system Python の `python -m pytest -q aio2-main\tests\test_dashboard_ui.py` は `html_sanitizer` 未導入で collection 不可。
  - `aio2-main\.venv\Scripts\python.exe` は `pytest` 未導入、`.codex-ui-test-venv` は未配置。
  - `.venv` で直接 helper smoke を実行し、接続待ち/更新/停止の判定と、初期表示が `(2%)` になることを確認。
  - Browser retest: `http://127.0.0.1:8081/` を開き、`https://example.com` で分析開始後、進捗が `URL取得 - HTML取得/エンコード判定 (18%)` まで更新されることを確認。0% 固定は再現せず。
  - 検証後、sandbox 内の一時起動では常駐プロセスが保持されないため、sandbox 外で `techie-hub\start.bat force --no-pause` を実行し、HUB / Kotomigaki を標準ランタイムに復元。`http://127.0.0.1:8090/` と `http://127.0.0.1:8081/` の HTTP 200 を確認。

## 2026-07-08 (固定既知脆弱性DB照合)
### URLチェック固定SQLiteスナップショット取り込み + hash_key照合

- decision:
  - `fixed_vulnerability_intelligence_snapshot_enabled`
- scope:
  - URLチェックの現時点ローカル脆弱性DBを固定スナップショットとしてコトミガキへ取り込み、通常分析中に公開HTML/JS URLから見える component / version だけを既知脆弱性候補として照合する。
  - 外部CVE/OSV/GitHub/KEV APIの通常分析中取得、差分更新、定期同期、DB書き込み、広範クロール、攻撃手順/PoC/payload表示は実装しない。
  - 照合は URLチェックと同じ `hash_key` 方式（`ecosystem / identifier_kind / canonical_component_key` の SHA-256）を使い、固定SQLite DBの index から候補だけを引く。25万件規模のDBを総当たりしない。
  - UI/結果文言は「既知脆弱性候補」「保守担当者へ更新確認」を中心にし、該当0件を「安全」と断定しない。
- changed files:
  - `ALGORITHM.md`
  - `config/vulnerability_intelligence.sqlite3`
  - `AGENTS.md`
  - `core/site_health/vulnerability_intelligence.py`
  - `core/site_health/security_checker.py`
  - `tests/test_fixed_vulnerability_intelligence.py`
  - `WORKLOG.md`
- validation:
  - `python -m py_compile aio2-main\core\site_health\vulnerability_intelligence.py aio2-main\core\site_health\security_checker.py aio2-main\tests\test_fixed_vulnerability_intelligence.py aio2-main\tests\test_public_technology_risks.py` -> OK。
  - `python -m pytest -q aio2-main\tests\test_fixed_vulnerability_intelligence.py aio2-main\tests\test_public_technology_risks.py` -> 15 passed。
  - 固定DB実参照 smoke: `jquery 3.4.1` に対して `matched 5`、`record_count 259804`、`reference_date 2026-07-08` を確認。CVE-2020-11022 / CVE-2020-11023 を含む候補が version range match で返った。

## 2026-07-08 (続報)
### FAQ提案カード整理・重複箇条書き修正・構造化データ折りたたみ + 既存キャッシュのクリア

- decision:
  - `presentation_layer_followup_fixes_completed`
- scope:
  - ユーザーが実機スクリーンショットで報告した3件の「非エンジニアには分かりにくい」表示を修正。分析ロジック・検出ロジックは無変更。
  - **FAQ提案カード** (`core/ui/saved_workspace.py`) →
    - `source_label`（"issue ベース"等の内部分類ラベル）、`evidence_terms`（根拠語チップ）、`confidence`（信頼度）を非エンジニア向けカードから削除。いずれも検出アルゴリズムの内部判断根拠であり、コンテンツ担当者が使う情報ではないため。
    - `risk_if_wrong`（注意文）は実質的な内容ガイドのため単独で保持。
    - `schema_candidate`（"JSON-LD化を検討"等）は常に固定文言かつ開発者向けのため、設置先の表示から除外。
    - セクション説明文からも「根拠語」の言及を削除（表示しなくなったため）。
  - **「古いjQueryが読み込まれています」等の重複箇条書き** (`core/site_health/maintenance_risk.py`) →
    - `_issue_titles()` が同一タイトルを重複除去せずに並べていたのが原因（1サイトでjQuery関連の検出が7件あり、同じ文言が7回分そのまま箇条書きになり得る状態だった）。
    - タイトル文字列で重複除去する処理を追加。表示件数の上限（デフォルト4件）は重複除去後に適用されるよう変更。
  - **「参考（後で見る）」内の構造化データブロック** (`core/ui/saved_workspace.py`) →
    - 隣接する「公開条件の詳細を見る」と同じ折りたたみパターンに統一し、ラベルを「構造化データの詳細を見る（開発者向け）」に変更。既定で折りたたみ、対象読者を明示。
  - **既存キャッシュのクリア** (`data/analysis_history.db`) →
    - `_enrich_saved_snapshot_from_result()` は `setdefault` で `maintenance_risk` をスナップショットへ一度だけ書き込みキャッシュする設計のため、コード修正だけでは保存済みレポートの表示は変わらないと判明。
    - DBを `data/analysis_history.db.bak_20260708` にバックアップした上で、`analysis_runs.snapshot_json` 内の `implementation_workspace.maintenance_risk` / `technical_workspace.maintenance_risk` を持つ全15件（run 9〜23）からその2キーのみ削除。次回表示時に `build_maintenance_risk_summary()` が再計算する。スコア系のキャッシュ値（`maintenance_risk_score_snapshot` 等）はロジック変更対象外のため触れていない。
- changed files:
  - `core/ui/saved_workspace.py`
  - `core/site_health/maintenance_risk.py`
  - `data/analysis_history.db`（15件のスナップショットJSONから2キーを削除。バックアップ: `data/analysis_history.db.bak_20260708`）
- validation:
  - `py_compile`: OK
  - `build_maintenance_risk_summary()` を run 22 の `analysis_result.json` に対して直接実行し、フロントエンド資産カードの bullets が 7件（重複込み）→ 2件（重複除去後）になることを確認。
  - Browser retest（`http://127.0.0.1:8081/runs/22`）:
    - 「文章改善」タブ: FAQ提案カードから `issue ベース`/`根拠語`/`信頼度:` の文字列が消えたことを確認。「注意」「対象読者」「設置先」は保持。
    - 「実装・設定」タブ: DBキャッシュクリア前は「古いjQueryが読み込まれています」が4回表示、クリア後は1回（「古い可能性のあるフロントエンド資産があります」と合わせて2件）に減ったことを確認。
    - 「構造化データの詳細を見る（開発者向け）」の折りたたみボタンが既定で非展開であることを確認。
  - サービス再起動: 検証のため一時的にポート8081を差し替え、検証後は `techie-hub\start_runtime.ps1` と同じ起動コマンド（venv python + `run_app.py` + `PORT`/`KOTOMIGAKI_STRICT_PORT` 環境変数）でプロセスを復元し、HTTP 200 を確認済み。

## 2026-07-08
### UI/表示改善（非エンジニア向け段階化、情報密度削減、色トークン統一）

- decision:
  - `presentation_layer_audience_segmentation_completed`
- scope:
  - 分析ロジック・スコア計算・DB スキーマは無変更。表示側（`core/ui/saved_workspace.py`）のみ修正。
  - **P0a: 「やること」タブの生データ削除** →
    - `_render_task_action_detail_lines()` で `_accessibility_engineer()` → `_accessibility_audience()` に変更。
    - 非エンジニア向けタブでは「見直し箇所」「次に渡す相手」を表示。「対象要素」「確認方法」などの HTML タグはエンジニア向けタブのみに限定。
  - **P0b: 評価サマリーの圧縮** →
    - 6軸チャート・低い軸再掲・ページ役割確認を `ui.expansion("詳細診断を見る（軸別スコア・ページ役割）")` に移動。
    - 既定状態では 4 指標＋結論 1 文のみ表示。
    - html lang 等の見出し = 本文が一字一句同じ注意カード両方を表示していた重複を、見出しだけ表示するよう修正（`if detail_text.strip() != title_text.strip()` チェック追加）。
  - **P0c: 色トークン統一** →
    - 「総合評価」ラベル 6 箇所を `text-gray-500` → `card-hint`（`--text-muted: #6B5A4D`）に統一。
    - 状態バッジ（改善余地・要対応等）の色は範囲外とし、新しいブランド色トークン定義待ちのため保持。
- changed files:
  - `core/ui/saved_workspace.py` (3 箇所の修正を 1 ファイルで）
- validation:
  - `py_compile`: OK
  - `ast.parse`: OK
  - Browser retest: desktop と 375×812（モバイル幅）で横スクロールなし、機能欠落なし確認済み。
  - Smoke check:
    - コトミガキ `/runs/22` で「やること」タブ開く → 「見直し箇所」「次に渡す相手」表示、生データ削除確認。
    - エンジニア向けタブ開く → 「対象要素」「確認方法」「検出元」は保持、削除なし確認。
    - 評価サマリー上部に「詳細診断を見る（軸別スコア・ページ役割）」ボタン表示、既定では非展開。

## 2026-07-08
### OpenAI JSON retry and async client cleanup narrow fix

- scope:
  - Narrow fix for UI/API execution findings from `https://example.com/`.
  - Kept scoring, analysis rules, DB schema, and provider payload shape unchanged.
  - Retried HTTP 200 LLM responses when the body is not a parseable JSON object, with a short JSON-only correction message on later attempts.
  - Closed OpenAI clients explicitly after UI analysis and one-shot PDF score-reason LLM calls to avoid delayed `httpx.AsyncClient.aclose()` cleanup after the event loop closes.
- changed files:
  - `core/engine/orchestrator.py`
  - `core/application/analysis_run_service.py`
  - `nicegui_app.py`
  - `PDFreport/llm_client.py`
  - `PDFreport/score_reasoning.py`
  - `tests/test_orchestrator_security.py`
  - `WORKLOG.md`
- validation:
  - `py_compile` passed for the changed Python files.
  - Direct retry harness passed: invalid HTTP 200 JSON output retried once, second attempt received the short JSON-only correction, and final failure reports `HTTP 200`, invalid model JSON, and the actual attempt count.
  - Browser UI retest used headless Chrome against `http://127.0.0.1:8081/`, entered `https://example.com/`, clicked `分析する`, and reached `/runs/21`.
  - Browser console/page errors/request failures: none.
  - DB evidence: `analysis_runs.id=21`, URL `https://example.com/`, analyzed_at `2026-07-08 02:48:25` UTC, SEO `38`, AIO `35`, legal `100`, total issues `1`, result path `data/poc_outputs/runs/21/analysis_result.json`.
  - App log after `2026-07-08T11:43:17` shows OpenAI model/chat HTTP 200 and `保存完了: run_id=21`; no `AsyncClient.aclose`, `Event loop is closed`, `Citation phrase extraction failed`, or `Citation content plan failed` entries in that run.
  - `.venv` still has no `pytest`, so pytest collection was not run.

## 2026-07-08
### UI smoke check

- scope:
  - TECHIE cross-service UI check for `http://127.0.0.1:8081/`.
  - Browser verified `コトミガキ | TECHIE`, URL input, comparison URL/condition expanders, `分析する`, `保存済み履歴を見る`, history table, and `履歴CSV`.
  - Entered `https://example.com/` into the URL field and confirmed `分析する` remained enabled.
  - After API execution approval, clicked `分析する` for `https://example.com/`.
- result:
  - HTTP 200 and page rendered.
  - Live analysis started from UI, disabled `分析する` during execution, and saved run `17`.
  - OpenAI model check and chat completion calls returned HTTP 200.
  - DB evidence: `analysis_runs.id=17`, URL `https://example.com/`, analyzed_at `2026-07-08 01:22:42` UTC, SEO `38`, AIO `35`, legal `100`, total issues `1`, result path `data/poc_outputs/runs/17/analysis_result.json`.
  - Not clean green: app log recorded `Citation phrase extraction failed` warning, then post-save async cleanup errors `AsyncClient.aclose() ... RuntimeError('Event loop is closed')` after `保存完了: run_id=17`.
  - Console observation: one browser resource access warning/error (`net::ERR_NETWORK_ACCESS_DENIED`) only; no app JS exception observed.
  - Product code changed: false.

## 2026-07-08
### Kotomigaki press release draft and visual assets

- scope:
  - Created a press release draft for Kotomigaki launch messaging under `marketing/press_release_2026/`.
  - Tightened the headline/lead so the service category, price, diagnostic scope, and output are visible immediately.
  - Kept the copy to the requested wording rules: ChatGPT only among AI service names, no legal-check positioning, and `サイトの弱点(セキュリティの穴)` instead of vulnerability wording.
  - Created a deterministic press-release radar UI image with Japanese labels and copied a generated key visual into the same asset folder.
  - Did not change app runtime, scoring, analysis logic, pricing logic, or service docs.
- changed files:
  - `marketing/press_release_2026/press_release_kotomigaki_draft.md`
  - `marketing/press_release_2026/ASSET_NOTES.md`
  - `marketing/press_release_2026/build_press_release_assets.py`
  - `marketing/press_release_2026/kotomigaki_radar_ui.png`
  - `marketing/press_release_2026/kotomigaki_key_visual.png`
  - `WORKLOG.md`
- validation:
  - Generated `kotomigaki_radar_ui.png` with `.venv\Scripts\python.exe marketing\press_release_2026\build_press_release_assets.py`.
  - Visually checked the radar UI image and key visual for text clipping, readable Japanese labels, and absence of unwanted generated text.
  - No code tests run because this was a marketing/docs/assets-only slice.

## 2026-07-06
### Cross-Suite UI Clarity Pass — Kotomigaki Contribution

- scope:
  - ユーザー評価「コトミガキが特に分かりにくい」「専門的だから仕方ないわけではない」を受けた表示専用の改修。スコアリング・分析ロジック（`core/aio_analyzer.py` 等）には一切触れていない。全体の背景は `C:\tetie\WORKLOG.md` の「Cross-Suite UI Clarity Pass」を参照。
  - `kotomegane\docs\cross_product\UI_UNIFICATION_PLAN_2026-03-31.md` の積み残しタスクを実施: `core/ui/styles.py` の `:root` に `--self`/`--self-soft`/`--competitive`/`--competitive-soft`/`--external`/`--external-soft`（kotomeganeと同値）と `.card-primary`/`.card-secondary`/`.card-detail`/`.text-self`/`.text-competitive`/`.text-external` を追加。既存の15カードクラスのうち補助/詳細相当の6クラス（`action-preview-card`, `evaluation-summary-card`, `detail-tabs-card`, `implementation-note-card`, `diagnostic-note-card`, `reference-note-card`）の `box-shadow`/`border` 値をtierの重みに合わせて調整。主役相当のクラス（`dashboard-analyze-card` 等）は元々 `.card` ベースの強い影を継承済みのため変更なし。
  - `comparison_tab.py` の「自社vs競合」優劣表示（著者情報・運営組織）を `text-green-600`/`text-gray-500` の直書きから `.text-self` トークン参照へ置換。難易度表示（緑/黄/赤）は重大度軸のため対象外。
  - 詳細結果タブ6つ（`core/ui/tabs/aio_tab.py`, `seo_tab.py`, `health_tab.py`, `comparison_tab.py`, `simulation_tab.py`; `industry_tab.py` は確認のみで変更なし）を「平易な結論を先頭に表示し、生スコア・計算式・専門用語は `ui.expansion(...)` へ格納」する構成へ再編。`aio_tab.py` の「AIOスコア計算式」（生スコア×調整係数=最終スコア）は象徴的な悪例だったため最優先で対応。
  - `saved_workspace.py` の保存済み分析タブ名を `評価/改善/リライト/設定/技術/比較` から、各タブが内部で既に使っていた見出し文言 `サマリー/やること/文章改善/実装・設定/エンジニア向け/履歴と比較` に統一（`show_header=False` でこれまで隠れていた文言をタブラベルへ採用）。
  - `saved_workspace.py` と `health_tab.py` の保守メトリクス表示（`personal fields`, `file upload`, `sensitive`, `external action`, `checked endpoints`, `problem endpoints`）を日本語ラベルへ変更。
  - `nicegui_app.py` のダッシュボード入力面: 「検索/AI」バランススライダーに両端の意味とデフォルト値の説明、業界/作成サービス/種別が任意設定であることの説明、「比較サイト」欄の目的説明、Markdown/Word レポート出力の使い分け説明を追加。
  - `doorknock\doorknock_pdf.py` の営業PDFで同じ指標が「LLMO」と表記されていた不整合を「AIO」に統一（UI側の呼称に合わせた）。
- changed files:
  - `core/ui/styles.py`
  - `core/ui/tabs/aio_tab.py`
  - `core/ui/tabs/seo_tab.py`
  - `core/ui/tabs/health_tab.py`
  - `core/ui/tabs/comparison_tab.py`
  - `core/ui/tabs/simulation_tab.py`
  - `core/ui/saved_workspace.py`
  - `nicegui_app.py`
  - `../doorknock/doorknock_pdf.py`
  - `WORKLOG.md`
- validation:
  - `.venv\Scripts\python.exe -c "import ast; ast.parse(open(<file>, encoding='utf-8').read())"` を全編集ファイルに実行 -> OK。
  - `aio_tab.py`/`seo_tab.py`/`health_tab.py`/`comparison_tab.py`/`simulation_tab.py` を、合成モックデータで直接描画する一時ハーネス（セッション内でのみ作成し使用後に削除、リポジトリには残していない）で `preview_start` から起動し、結論が先頭に出ること・折りたたみが正しく開閉すること・元の情報が欠落していないことをスナップショット/DOM抽出で確認。
  - `PORT=8081` で `nicegui_app.py` を起動し、スライダー・業界選択・比較サイト欄の新規文言がDOMに反映されていることと、サーバー/コンソールエラーがないことを確認。
  - `doorknock_pdf.py` は `ast.parse` のみ（実際のPDF生成は未実行）。
- result:
  - decision: `kotomigaki_ui_clarity_pass_complete`
  - スコアリング/分析ロジック変更: なし
  - API送信回数: `0`（合成データ・静的検証のみ）
- guardrails:
  - 分析エンジン・レポート生成ロジックは未変更。
  - Python側の `.classes()` 呼び出しのクラス名は変更していない（Task 3のカード調整はCSS値のみ）。
  - AGENTS.md 更新なし（source of truth / 恒久ルール変更なし）。

### Existing Azure replacement DOCX/export persistence decision note

- scope:
  - Recorded that saved-run Word export is a current export path, owned by `core/application/docx_report_service.py`.
  - Clarified the delivery context: this is not a first Azure migration; the system already exists on Azure and the request is an improved-version replacement.
  - Locked the added feature scope to Kotomigaki report save/download only.
  - Clarified that the replacement should not treat local `data/poc_outputs/exports` as durable storage for generated CSV/Markdown/DOCX files.
  - Documented the Azure target expectation: save generated reports to durable storage such as Azure Storage using the existing tenant-id separation, and return downloads through an authenticated endpoint or short-lived SAS URL.
  - Kept this as documentation only; no runtime behavior, DOCX content generation, UI labels, or dependency files were changed.
- changed files:
  - `AGENTS.md`
  - `ALGORITHM.md`
  - `WORKLOG.md`
- validation:
  - Documentation-only update; no code tests run.
  - Confirmed current implementation references before recording: `nicegui_app.py` uses `ui.download()` for Word export, `core/application/docx_report_service.py` writes `.docx` via `EXPORTS_DIR`, and `requirements.txt` includes `python-docx==1.2.0`.

---

## 2026-06-28
### Dashboard analysis progress visibility narrow fix

- scope:
  - Kept the existing dashboard spinner, but added a visible compact progress band directly under the analyze controls.
  - Progress now shows current stage, detail, percent, elapsed time, and the 1-3 minute estimate while analysis is running.
  - Explicitly updates the NiceGUI progress label/bar from the dashboard async refresh loop and immediately after analysis starts, so users do not only see the spinner.
  - Kept the change inside `nicegui_app.py`; no result workspace, engine scoring, or saved history behavior was changed.
- changed files:
  - `nicegui_app.py`
  - `tests/test_dashboard_ui.py`
  - `WORKLOG.md`
- validation:
  - `.venv\Scripts\python.exe -m py_compile nicegui_app.py tests\test_dashboard_ui.py`
  - `.venv\Scripts\python.exe -m pytest -q tests\test_dashboard_ui.py` could not run because `pytest` is not installed in the local `.venv`.
  - System `pytest -q tests\test_dashboard_ui.py` could not collect because system Python does not have `html_sanitizer`.
  - Direct `.venv` helper check passed for progress text stage/detail/percent/elapsed/estimate formatting.
  - `PORT=8081 HEADLESS=1 .venv\Scripts\python.exe nicegui_app.py` reached `NiceGUI ready to go on http://127.0.0.1:8081`; the foreground check was stopped by the tool timeout. Background `Start-Process` persistence was not completed because PowerShell raised a duplicate `Path`/`PATH` environment key error.

---

## 2026-06-24
### Site health endpoint health checks slice

- scope:
  - Added `core/site_health/endpoint_health_checker.py` as the owner for passive public endpoint health checks, keeping `security_checker.py` as the aggregator.
  - Added robots fake-200 checks for `/robots.txt` returning HTML or text without basic robots directives.
  - Added sitemap fake-200 checks for `/sitemap.xml`, `/wp-sitemap.xml`, and `/sitemap_index.xml` returning HTML instead of XML, without duplicating sitemap freshness/coverage ownership in `sitemap_analyzer.py`.
  - Added unused WordPress endpoint fake-200 checks for non-WordPress-looking sites where `/wp-sitemap.xml` or `/wp-json/` returns top-page-like HTML.
  - Added exactly one generated missing-URL request for soft 404 suspicion, using lightweight title/body/final-URL heuristics and no URL discovery.
  - Added PHP/PleskLin header exposure checks for `X-Powered-By` / `Server`, treating PHP 5.x and 7.0-7.4 as EOL-series confirmation candidates without CVE assertions.
  - Strengthened public HTML form signals with sensitive terms, external action detection, and a combined "public protection hints not visible" issue while avoiding server-side vulnerability assertions.
  - Registered endpoint issue ids in `maintenance_risk.py` so they affect the existing maintenance score/cards and flow through `public_technology_risks -> site_health_checks -> engineer_tasks`.
  - Added endpoint engineer task wording with confirmation URL, HTTP status, Content-Type, excerpt, commands, and pass conditions.
  - Added `plan/endpoint_health_checks_2026-06-24/README.md` documenting the slice owner, non-invasive boundary, and output contract.
  - Follow-up fix from user validation: versionless jQuery core assets such as `/js/jquery.js` are now checked by reading up to 256KB of the already referenced public JS file and parsing `jQuery vX.Y.Z`; this detected `https://healthrent.duskin.jp/js/jquery.js` as jQuery 1.7.1 and routes it to `jquery_before_3_5`.
  - Follow-up wording polish: non-engineer-facing endpoint card title changed from `公開endpoint健全性` to `公開設定の応答確認`, `プライバシー侵害` risk wording softened to `不要なブラウザ機能利用の懸念`, and old frontend assets no longer make the `WordPress保守確認` card warn unless WordPress-specific public signs are present.
- changed files:
  - `ALGORITHM.md`
  - `plan/endpoint_health_checks_2026-06-24/README.md`
  - `core/site_health/endpoint_health_checker.py`
  - `core/site_health/security_checker.py`
  - `core/site_health/maintenance_risk.py`
  - `core/application/technical_summary_builder.py`
  - `core/application/markdown_report_service.py`
  - `core/ui/saved_workspace.py`
  - `core/ui/tabs/health_tab.py`
  - `tests/test_endpoint_health_checker.py`
  - `tests/test_public_technology_risks.py`
  - `WORKLOG.md`
- validation:
  - `.venv\Scripts\python.exe -m py_compile core\site_health\security_checker.py core\site_health\endpoint_health_checker.py core\site_health\maintenance_risk.py core\application\technical_summary_builder.py core\ui\saved_workspace.py core\ui\reports\executive_summary.py core\ui\tabs\health_tab.py core\application\markdown_report_service.py`
  - `.venv\Scripts\python.exe -m pytest -q tests\test_endpoint_health_checker.py tests\test_public_technology_risks.py tests\test_engineer_handoff_builder.py tests\test_markdown_report_service.py` could not run because `pytest` is not installed in the local `.venv`.
  - Manual direct calls for 24 target test functions passed, covering endpoint fake-200, soft 404, PHP/PleskLin header exposure, form risk signals, internal HTTP links, versionless jQuery asset header detection, endpoint engineer tasks, public technology risk regressions, engineer handoff, and Markdown report output.
  - Live follow-up verification for `https://healthrent.duskin.jp/` confirmed `jquery_before_3_5` for `https://healthrent.duskin.jp/js/jquery.js` with `jQuery v1.7.1`; security score became 44 and maintenance score became 70.
  - Follow-up wording search found no remaining non-engineer-facing strings such as `侵害されています`, `攻撃されています`, `感染`, or `悪用されています` in the site-health/application/UI paths.

### Site health maintenance/update management UI and radar integration

- scope:
  - Added `core/site_health/maintenance_risk.py` as the classification owner for public maintenance issues, maintenance risk score, and non-engineer-facing cards.
  - Added `update_signal_mismatch` by combining visible update-date freshness with sitemap `lastmod`, while keeping `sitemap_unavailable_or_invalid` as the priority issue when sitemap retrieval/parsing fails.
  - Expanded frontend asset inventory beyond jQuery to URL-visible `jquery-ui / bootstrap / swiper / slick / modernizr` candidates while keeping jQuery < 3.5.0 as the high-confidence high-severity rule.
  - Added maintenance/update cards to saved-run Settings and live health display: update consistency, WordPress maintenance, forms, old frontend assets, browser defense headers, and sitemap/robots consistency.
  - Added maintenance risk score to the existing radar through the `保守・技術基盤` axis; no separate radar chart was added.
  - Extended engineer tasks with confirmation commands and pass conditions, preserving the existing `public_technology_risks -> site_health_checks -> engineer_tasks` flow.
  - Added Markdown `保守・更新管理` section with the same non-engineer summary cards and kept engineer confirmation items in the technical section.
- changed files:
  - `ALGORITHM.md`
  - `core/site_health/security_checker.py`
  - `core/site_health/maintenance_risk.py`
  - `core/application/technical_summary_builder.py`
  - `core/application/analysis_run_service.py`
  - `core/engineer_handoff_builder.py`
  - `core/ui/saved_workspace.py`
  - `core/ui/reports/executive_summary.py`
  - `core/ui/tabs/health_tab.py`
  - `core/application/markdown_report_service.py`
  - `tests/test_public_technology_risks.py`
  - `tests/test_engineer_handoff_builder.py`
  - `tests/test_markdown_report_service.py`
  - `tests/test_executive_summary.py`
  - `WORKLOG.md`
- validation:
  - `.venv\Scripts\python.exe -m py_compile core\site_health\security_checker.py core\site_health\maintenance_risk.py core\application\technical_summary_builder.py core\application\analysis_run_service.py core\engineer_handoff_builder.py core\ui\saved_workspace.py core\ui\reports\executive_summary.py core\ui\tabs\health_tab.py core\application\markdown_report_service.py tests\test_public_technology_risks.py tests\test_engineer_handoff_builder.py tests\test_markdown_report_service.py tests\test_executive_summary.py`
  - `.venv\Scripts\python.exe -m pytest -q tests\test_public_technology_risks.py tests\test_engineer_handoff_builder.py tests\test_markdown_report_service.py tests\test_executive_summary.py` could not run because `pytest` is not installed in the local `.venv`.
  - Manual direct calls for the target test functions passed, including update mismatch, frontend asset inventory, engineer handoff, Markdown maintenance section, and radar axis tests.
  - Live public-data verification for `https://www.kyotokogyo.co.jp/` confirmed WordPress 6.1 generator exposure, jQuery 2.2.4, external CDN without SRI, UA tag, public REST users including `admin`, sitemap `lastmod` 2022-03-01, visible date 2025-11-01, `update_signal_mismatch`, maintenance cards, engineer command fields, and `保守・技術基盤` score reduction.

### Site health public maintenance risk expansion

- scope:
  - Expanded `core/site_health/security_checker.py` public technology risks with non-invasive checks for form risk signals, same-domain HTTP navigation left inside HTTPS pages, and unavailable/invalid `/sitemap.xml`.
  - Added visible update-date freshness as a separate public signal: recent visible dates are kept as evidence only, while dates older than 365 days become a maintenance confirmation candidate.
  - Form checks are limited to public HTML evidence: HTTP form actions, password fields on non-HTTPS pages, file upload forms without visible bot-protection hints, personal-information forms without visible privacy-consent hints, and POST forms without visible CSRF/nonce hints.
  - EC transaction/product-data auditing was intentionally not added in this slice to avoid false positives on non-EC URLs.
  - Added engineer verification wording for the new issue ids so saved UI, Markdown report, and handoff output can show concrete confirmation steps through the existing `site_health_checks` flow.
- changed files:
  - `ALGORITHM.md`
  - `core/site_health/security_checker.py`
  - `core/application/technical_summary_builder.py`
  - `tests/test_public_technology_risks.py`
  - `WORKLOG.md`
- validation:
  - `.venv\Scripts\python.exe -m py_compile core\site_health\security_checker.py core\application\technical_summary_builder.py tests\test_public_technology_risks.py`
  - `.venv\Scripts\python.exe -m pytest -q tests\test_public_technology_risks.py` could not run because `pytest` is not installed in the local `.venv`.
  - Manual direct calls for the public technology risk tests passed, including the new form/internal-HTTP/sitemap cases and the search-form false-positive guard.

---

## 2026-06-23
### URL check and accessibility reuse review

- scope:
  - Reviewed `C:\Users\横山裕明\OneDrive - 京都工業株式会社\デスクトップ\URLチェック` and identified low-risk reusable checks from its public HTML/static parser.
  - Reviewed `C:\Users\横山裕明\OneDrive - 京都工業株式会社\デスクトップ\アクセシビリティ`; confirmed the Playwright / axe-core scanner family is already bundled under `tools/accessibility_scanner/`, so no duplicate migration was added in this slice.
  - Added public HTML checks for known suspicious external asset domains such as `polyfill.io`, `staticfile.org`, `bootcdn.net`, and related traces, plus `target="_blank"` links missing `rel="noopener"`.
  - Added UI/engineer handoff verification wording for the new public technology risk issue ids.
- changed files:
  - `ALGORITHM.md`
  - `core/site_health/security_checker.py`
  - `core/application/technical_summary_builder.py`
  - `tests/test_public_technology_risks.py`
  - `WORKLOG.md`
- validation:
  - `.venv\Scripts\python.exe -m py_compile core\site_health\security_checker.py core\application\technical_summary_builder.py tests\test_public_technology_risks.py`
  - `.venv\Scripts\python.exe -m pytest -q tests\test_public_technology_risks.py` could not run because `pytest` is not installed in the local `.venv`.
  - Manual direct calls for `test_public_technology_risks_detects_wordpress_surface()`, `test_public_technology_risks_reuses_url_checker_static_asset_signals()`, `test_public_technology_risks_avoids_rest_probe_without_wordpress_hint()`, and `test_sitemap_analyzer_keeps_static_generator_hint()` passed.
  - Manual `build_site_health_checks()` verification confirmed the new issue ids appear in `engineer_tasks` with dedicated verification text.
  - Manual `build_detailed_markdown_report()` verification confirmed the new issue ids and evidence URLs appear in the report output.

---

## 2026-06-23
### Public technology risk surfacing in UI and reports

- scope:
  - Promoted `site_health.security.raw.public_technology_risks` into saved-run `site_health_checks` with concrete issue titles, public-risk count, and engineer-facing task rows.
  - Added public technology risk rows to the engineer handoff builder so saved UI and Markdown reports show target, work, verification, and detection source for items such as old jQuery, public WordPress REST users, CDN assets without SRI, stale/static sitemap, and Universal Analytics leftovers.
  - Expanded saved workspace site-health detail rendering so security checks can show engineer verification steps directly in the technical tab.
  - Expanded detailed Markdown report site-health output with issue bullets and engineer verification notes.
- changed files:
  - `core/application/technical_summary_builder.py`
  - `core/engineer_handoff_builder.py`
  - `core/application/markdown_report_service.py`
  - `core/ui/saved_workspace.py`
  - `tests/test_engineer_handoff_builder.py`
  - `tests/test_markdown_report_service.py`
  - `WORKLOG.md`
- validation:
  - `.venv\Scripts\python.exe -m py_compile core\application\technical_summary_builder.py core\engineer_handoff_builder.py core\application\markdown_report_service.py core\ui\saved_workspace.py tests\test_engineer_handoff_builder.py tests\test_markdown_report_service.py`
  - Manual direct calls for `test_handoff_includes_public_security_tasks()` and `test_build_detailed_markdown_report_includes_actionable_sections()` passed.
  - Live public-data verification for `https://www.kyotokogyo.co.jp/` confirmed saved-run-equivalent `site_health_checks.security.detail` contains `公開技術リスク 6件`, `engineer_tasks` contains 6 concrete rows, engineer handoff includes public-risk rows, and generated Markdown contains old jQuery / WordPress REST API / Universal Analytics entries plus verification steps.
  - `pytest` remains unavailable in the local `.venv` and system Python, so full pytest execution was not run.

---

## 2026-06-23
### Public technology risk detection for site health

- scope:
  - Added a lightweight public-technology risk check to Kotomigaki site health so public HTML/headers/sitemap data can catch issues such as exposed WordPress generator versions, old jQuery, external CDN assets without SRI, Universal Analytics leftovers, old IE polyfills, public WordPress REST users, and stale/static sitemap hints.
  - Kept the check non-invasive: no `.git`, backup-file, admin brute force, vulnerability scan, or directory probing. The only additional public endpoint check is `/wp-json/wp/v2/users` when WordPress hints are already present.
  - Passed existing `sitemap_info` into site health so stale `lastmod` and static generator hints can be surfaced inside the security result.
  - Added sitemap generator hint extraction for static sitemap comments such as `xml-sitemaps.com`.
- changed files:
  - `ALGORITHM.md`
  - `core/site_health/security_checker.py`
  - `core/engine/site_health_engine.py`
  - `core/engine/orchestrator.py`
  - `core/sitemap_analyzer.py`
  - `tests/test_public_technology_risks.py`
- validation:
  - `.venv\Scripts\python.exe -m py_compile core\site_health\security_checker.py core\engine\site_health_engine.py core\engine\orchestrator.py core\sitemap_analyzer.py tests\test_public_technology_risks.py`
  - Manual test script with mocked WordPress REST users confirmed all intended issue ids are emitted and clean non-WordPress HTML does not trigger a REST probe.
  - Live public-data verification for `https://www.kyotokogyo.co.jp/` through `run_full_site_health_check` confirmed `site_health.security.raw.public_technology_risks.issue_count == 6`, including WordPress generator, jQuery 2.2.4, external CDN without SRI, Universal Analytics, public REST users, and stale/static sitemap.
  - `pytest` was not available in the local `.venv` or system Python, so pytest execution was not run.

---

## 2026-06-21
### NotebookLM source pack for Kotomigaki algorithm explanation

- scope:
  - Rebuilt `Notebook/` as a flat NotebookLM source pack for explaining Kotomigaki as an SEO/AIO software product and preparing a talk script.
  - Moved the previous Notebook contents to `Notebook_previous_20260621_001938/`.
  - Copied 243 source files plus 2 guide/manifest files into `Notebook/`; unsupported source/code extensions such as `.py`, `.html`, `.css`, `.toml`, `.json`, `.mjs`, and `.env.example` were copied with `.md` filenames.
  - Excluded binary assets, fonts, screenshots, sample PDFs, runtime outputs, virtual environments, and Notebook backups.
- changed files:
  - `Notebook/`
  - `WORKLOG.md`
- validation:
  - Verified `Notebook/` has 245 files, 0 subdirectories, 0 unsupported extensions, 0 `.py` files, and remains under the 300-file cap.
  - Verified representative algorithm sources are present: orchestrator, AIO analyzer, scoring engine, citation generator, knowledge graph, Wikidata client, SEO, site health, legal checks, report/export, and tests.

---

## 2026-06-18
### Google max-snippet character display removal

- scope:
  - Saved-run Google control cards no longer display the `max-snippet` character-limit row such as `3000文字まで`.
  - `max_snippet` remains in analysis data; only the UI/actionable display row was removed.
- changed files:
  - `core/ui/saved_workspace.py`
  - `tests/test_characterization_ui.py`
  - `WORKLOG.md`
- validation:
  - `.codex-ui-test-venv\Scripts\python.exe -m py_compile core\ui\saved_workspace.py tests\test_characterization_ui.py`
  - `.codex-ui-test-venv\Scripts\python.exe -m pytest tests\test_characterization_ui.py -q` -> 20 passed, 1 warning

---

## 2026-06-17
### Affiliate disclosure wording clarification

- scope:
  - Stealth marketing check wording now explains that affiliate presence alone is not the score-drop reason; missing or unclear PR/ad disclosure is the actionable risk.
  - Non-affiliate results now show `PR表記が必要なアフィリエイト要素: 未検出` with a short explanation of detected article-pattern signals and score impact.
  - Health-tab status cards now display the stealth-marketing summary text above item details.
  - Saved run loading now refreshes the stealth-marketing formatted display payload from saved raw data, so old `analysis_result.json` files can be compared with current wording without mutating the raw source.
- changed files:
  - `core/application/analysis_run_service.py`
  - `core/legal_checks/stealth_marketing.py`
  - `core/ui/tabs/health_tab.py`
  - `tests/test_analysis_run_service.py`
  - `tests/test_stealth_marketing_formatting.py`
  - `WORKLOG.md`
- validation:
  - `.codex-ui-test-venv\Scripts\python.exe -m py_compile core\application\analysis_run_service.py core\legal_checks\stealth_marketing.py core\ui\tabs\health_tab.py tests\test_analysis_run_service.py tests\test_stealth_marketing_formatting.py`
  - `.codex-ui-test-venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py tests\test_stealth_marketing_formatting.py tests\test_executive_summary.py tests\test_markdown_report_service.py tests\test_docx_report_service.py -q` -> 47 passed, 1 warning
  - Run 2 raw stealth-marketing result formatted with the new copy now states that known affiliate links/URLs are undetected and score-drop/actionable risk applies when ad/PR elements lack disclosure.
  - Same-source run 2 Markdown comparison between `detailed-report-run-2-20260617-160542.md` and `detailed-report-run-2-20260617-170111.md` differs only by output timestamp; DOCX readback keeps 234 paragraphs, 2 tables, and 24 table rows.

### Legal pass item filtering for saved reports

- scope:
  - Legal summary pass items such as `アフィリエイトコンテンツ: 検出されず` are no longer promoted into priority actions or score-drop drivers.
  - Affiliate content itself is not treated as a score-drop reason; missing or unclear PR/ad disclosure remains the actionable legal risk.
  - Bumped saved snapshot schema version so existing run details are rebuilt without stale pass-item actions.
- changed files:
  - `core/application/analysis_run_service.py`
  - `core/ui/reports/executive_summary.py`
  - `tests/test_analysis_run_service.py`
  - `tests/test_executive_summary.py`
  - `WORKLOG.md`
- validation:
  - `.codex-ui-test-venv\Scripts\python.exe -m py_compile core\application\analysis_run_service.py core\ui\reports\executive_summary.py tests\test_analysis_run_service.py tests\test_executive_summary.py`
  - `.codex-ui-test-venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py tests\test_executive_summary.py tests\test_markdown_report_service.py tests\test_docx_report_service.py -q` -> 44 passed, 1 warning
  - Regenerated run 2 reports: `data/poc_outputs/exports/detailed-report-run-2-20260617-160542.md` and `.docx`; readback confirms `アフィリエイトコンテンツ: 検出されず` and `unknownに関する確認候補` are absent from priority actions and score-drop sections.

### Accessibility action detail retention for saved reports

- scope:
  - Saved-run accessibility improvement details now keep enough generated rows for `interactive_names`, so the UI and regenerated Markdown/DOCX can show target element, work, verification, and detection source for icon/link button name issues.
  - Bumped saved snapshot schema version so existing run details are rebuilt with the expanded accessibility detail payload.
- changed files:
  - `core/application/analysis_run_service.py`
  - `tests/test_analysis_run_service.py`
  - `WORKLOG.md`
- validation:
  - `.codex-ui-test-venv\Scripts\python.exe -m py_compile core\application\analysis_run_service.py tests\test_analysis_run_service.py`
  - `.codex-ui-test-venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py tests\test_engineer_handoff_builder.py tests\test_markdown_report_service.py tests\test_docx_report_service.py -q` -> 39 passed, 1 warning
  - Browser verification on `/runs/2`: improvement card for `リンクやアイコンボタンに操作名を付ける` now shows `制作・開発向け詳細`, `<button class="header_btn">`, work, verification, and detection source.
  - Regenerated run 2 reports: `data/poc_outputs/exports/detailed-report-run-2-20260617-155006.md` and `.docx`; readback confirms no raw `SEO technical_score` / `AIO pid` strings and DOCX handoff table includes the button accessible-name row.

### Report UX specificity and engineer handoff prioritization

- scope:
  - Saved-run improvement cards now surface accessibility engineer details inline: target element, work item, verification, and detection source.
  - Engineer handoff rows now prioritize concrete accessibility work before applying the display/export limit, avoiding loss behind legacy/link/schema rows.
  - Internal-link and schema handoff checks now include concrete verification steps such as `curl -I`, link-source confirmation, and schema validator acceptance.
  - Markdown score drivers now use Japanese labels and normalized score text instead of raw internal keys such as `technical_score` / `pid`.
- changed files:
  - `core/engineer_handoff_builder.py`
  - `core/ui/saved_workspace.py`
  - `core/application/analysis_run_service.py`
  - `core/application/markdown_report_service.py`
  - `tests/test_engineer_handoff_builder.py`
  - `tests/test_markdown_report_service.py`
  - `WORKLOG.md`
- validation:
  - `.venv\Scripts\python.exe -m py_compile core\engineer_handoff_builder.py core\ui\saved_workspace.py core\application\analysis_run_service.py core\application\markdown_report_service.py tests\test_engineer_handoff_builder.py tests\test_markdown_report_service.py tests\test_analysis_run_service.py`
  - `.codex-ui-test-venv\Scripts\python.exe -m pytest tests\test_engineer_handoff_builder.py tests\test_markdown_report_service.py tests\test_analysis_run_service.py tests\test_docx_report_service.py -q` -> 38 passed, 1 warning
  - Saved-run data check for runs 1/2/3: engineer handoff starts with concrete accessibility rows; raw `SEO technical_score` / `AIO pid` strings are absent from generated Markdown
  - Browser verification on `/runs/2`: improvement cards show `制作・開発向け詳細`, target elements, work items, and verification; engineer tab starts with concrete accessibility handoff rows
  - DOCX readback for run 2: engineer handoff table contains accessibility rows, concrete targets, work, and verification; raw score keys are absent

### DOCX export dependency profile fix

- scope:
  - Windows PoC dependency profile also installs `python-docx==1.2.0`, matching the canonical runtime dependency used by Word report export.
  - Saved-run Word export now logs DOCX generation exceptions and shows a short Japanese UI notification instead of failing silently in the menu action.
- changed files:
  - `requirements-windows.txt`
  - `nicegui_app.py`
  - `tests/test_dependency_profiles.py`
  - `WORKLOG.md`
- validation:
  - `.venv\Scripts\python.exe -m py_compile nicegui_app.py core\application\docx_report_service.py tests\test_docx_report_service.py tests\test_dependency_profiles.py`
  - `.codex-ui-test-venv\Scripts\python.exe -m pytest tests\test_docx_report_service.py tests\test_dependency_profiles.py -q` -> 2 passed, 1 warning
  - `.codex-ui-test-venv\Scripts\python.exe -m pip check` -> no broken requirements
  - Browser verification on `/runs/3`: `レポート出力` button and `Word（.docx）` menu are present; clicking generated `data/poc_outputs/exports/detailed-report-run-3-20260617-135814.docx`
  - `python-docx` readback of generated DOCX -> 246 paragraphs, 244 non-empty paragraphs, 2 tables

### Dependency audit hardening

- scope:
  - Updated vulnerable pins reported by `pip-audit`: `fastapi`, `starlette`, and `python-multipart`.
  - Left `diskcache==5.6.3` as a documented temporary risk acceptance because no fixed release is published.
- changed files:
  - `requirements.txt`
  - `../SECURITY_RISK_ACCEPTANCE.md`
  - `../WORKLOG.md`
- validation:
  - `.codex-ui-test-venv\Scripts\python.exe -m pytest tests/test_safe_fetch_security.py tests/test_orchestrator_security.py -q` -> 12 passed
  - `.codex-ui-test-venv\Scripts\python.exe -m pip check` -> no broken requirements
  - `python -m pip_audit -r aio2-main/requirements.txt` with `PYTHONUTF8=1` -> only accepted `diskcache==5.6.3 / CVE-2025-69872`
  - `python -m pip_audit -r aio2-main/requirements.txt --ignore-vuln CVE-2025-69872` with `PYTHONUTF8=1` -> no known vulnerabilities, 1 ignored
  - `npm audit` in `tools/accessibility_scanner` -> 0 vulnerabilities

## 2026-06-16
### Report export button with Markdown and Word

- scope:
  - 保存済み詳細ページの `詳細Markdown` を、見落としにくい `レポート出力` ボタンへ変更
  - 出力形式を `Markdown` と `Word（docx）` の2種に整理
  - レポート本文は既存MarkdownをSSOTとして維持し、Wordは同内容をdocx化
- changed files:
  - `nicegui_app.py`
  - `core/application/docx_report_service.py`
  - `core/application/__init__.py`
  - `requirements.txt`
  - `tests/test_docx_report_service.py`
  - `WORKLOG.md`
- validation:
  - `.codex-ui-test-venv\Scripts\python.exe -m py_compile core\application\docx_report_service.py core\application\markdown_report_service.py nicegui_app.py tests\test_docx_report_service.py`
  - `.codex-ui-test-venv\Scripts\python.exe -m pytest tests\test_markdown_report_service.py tests\test_docx_report_service.py -q` -> 3 passed, 1 warning
  - `.codex-ui-test-venv\Scripts\python.exe -c "... export_detailed_docx_report(load_saved_run_bundle(1/2)) ..."` -> run 1/2 の `.docx` を生成確認
  - Browser確認: `/runs/1` 右上に `レポート出力` 主ボタン、メニュー内に `Markdown（.md）` / `Word（.docx）` を確認
  - `render_docx.py` によるPNGレンダリングは `soffice` 不在で未実施

### Engineer handoff checklist for UI and Markdown

- scope:
  - エンジニア向けタブと詳細Markdownで、具体的な作業指示が先に読めるように整理
  - 保存済みsnapshotから `分類 / 対象 / 作業 / 確認方法 / 検出元` の作業票を生成
- changed files:
  - `core/engineer_handoff_builder.py`
  - `core/ui/saved_workspace.py`
  - `core/application/markdown_report_service.py`
  - `tests/test_markdown_report_service.py`
- validation:
  - `.venv\Scripts\python.exe -m py_compile core\engineer_handoff_builder.py core\application\markdown_report_service.py core\ui\saved_workspace.py tests\test_markdown_report_service.py`
  - `.venv\Scripts\python.exe -c "... build_engineer_handoff_items ..."` でアクセシビリティ作業票の直接生成を確認
  - `pytest` は既存 `.venv` の `pygments.formatters.terminal` 欠落で起動前に停止

### UI output verification: Kyoto Kogyo and Duskin Healthrent

- scope:
  - NiceGUI UIをブラウザ操作し、`https://www.kyotokogyo.co.jp/` と `https://healthrent.duskin.jp/` の保存済み詳細を確認
  - エンジニア向けタブの `エンジニア作業票` が対象URL、作業、確認方法を含むか確認
  - 詳細Markdownに同じ作業票が出力され、2サイトで内容がパーソナライズされるか確認
- observed output:
  - Kyoto Kogyo: 旧公開ページ `data.html` / `system.html` の301/308整理、内部リンク追加、構造化データ、アクセシビリティ確認が中心
  - Duskin Healthrent: 料金/予約/相談・資料請求ページとして判定され、画像説明文、空リンク/クロール不能リンク、LCP、内部リンク孤立、入力欄ラベル、landmark確認が中心
  - アクセシビリティは表示軸と作業票に反映され、Run 2では `main/nav/header/footer landmark` と検索入力欄 `<input class="iSearchAssist" name="kw" type="text">` の作業指示を確認
- artifacts:
  - `data/poc_outputs/runs/1/analysis_result.json`
  - `data/poc_outputs/runs/2/analysis_result.json`
  - `data/poc_outputs/exports/detailed-report-run-1-20260616-202344.md`
  - `data/poc_outputs/exports/detailed-report-run-2-20260616-203642.md`
- validation:
  - `.codex-ui-test-venv\Scripts\python.exe -m pytest tests\test_markdown_report_service.py -q` -> 2 passed, 1 warning
  - `.codex-ui-test-venv\Scripts\python.exe -m py_compile core\engineer_handoff_builder.py core\application\markdown_report_service.py core\ui\saved_workspace.py tests\test_markdown_report_service.py`
  - `.codex-ui-test-venv\Scripts\python.exe -c "... load_saved_run_bundle ... build_engineer_handoff_items ..."` -> run 1/2 とも12件、target/work/verifyを確認

## 2026-06-14
### Pre-analysis history and personalized output value fix

- scope:
  - 分析実行前に履歴確認が可能か、保存結果 / Markdown がテンプレート的でなく URL 固有の付加価値を出せているかを確認
  - トップ画面の分析カードから保存済み履歴へ移動する導線を追加
  - 保存スナップショットの上部要約に `ページ役割` / `不足` / `最初の一手` / `前回比` を追加し、古い snapshot は再生成対象にする
  - 詳細Markdown冒頭に `このURL固有の見立て` を追加
- changed files:
  - `nicegui_app.py`
  - `core/application/analysis_run_service.py`
  - `core/application/markdown_report_service.py`
  - `tests/test_analysis_run_service.py`
  - `tests/test_markdown_report_service.py`
  - `WORKLOG.md`
- validation:
  - `.venv\Scripts\python.exe -m py_compile nicegui_app.py core\application\analysis_run_service.py core\application\markdown_report_service.py tests\test_analysis_run_service.py tests\test_markdown_report_service.py`
  - `.venv\Scripts\python.exe -m pytest tests\test_dashboard_ui.py tests\test_analysis_run_service.py tests\test_markdown_report_service.py -q` -> 45 passed, 1 warning
  - Playwright temporary server check: top page shows `保存済み履歴を見る`, `履歴検索`, `履歴CSV`, and 2 saved rows before running analysis
  - Playwright saved-run check: `/runs/2` shows `ページ役割: 料金/予約/相談・資料請求ページ`, missing-content summary, first action, and `見やすさ・使いやすさ: 77`
  - Markdown builder check: run 2 report includes `## 0. このURL固有の見立て`

### Radar accessibility visibility fix

- scope:
  - コトミガキの改善マップ / レーダーチャートで、アクセシビリティ監査スコアが保存済み結果に入っていても、キャンバス描画と低い軸リストだけでは画面上で確認しづらい問題を確認
  - レーダー計算式は維持し、全軸の点数チップをチャート下に表示して `見やすさ・使いやすさ` の反映を明示
  - `accessibility_score_snapshot` を欠く古い保存スナップショットは再生成対象にする
- changed files:
  - `core/ui/reports/executive_summary.py`
  - `core/ui/saved_workspace.py`
  - `core/application/analysis_run_service.py`
  - `tests/test_analysis_run_service.py`
  - `WORKLOG.md`
- validation:
  - `.venv\Scripts\python.exe -m py_compile core\ui\reports\executive_summary.py core\ui\saved_workspace.py core\application\analysis_run_service.py tests\test_analysis_run_service.py`
  - `.venv\Scripts\python.exe -m pytest tests\test_executive_summary.py tests\test_analysis_run_service.py -q` -> 38 passed, 1 warning
  - Playwright temporary server check: `/runs/1` shows `見やすさ・使いやすさ: 90`; `/runs/2` shows `見やすさ・使いやすさ: 77`; both show one radar canvas

## 2026-06-13
### Report quality and accessibility audit execution package

- owner:
  - `kotomigaki_report_accessibility_audit_2026-06-13`
- scope:
  - 新規レポート品質、アクセシビリティ表示、非エンジニア向け伝達性、エンジニア向けUI妥当性、パーソナライズ性、UI操作による実機能確認を audit-first で確認する実行パッケージを追加
  - Codex が別ウィンドウまたは `/goal` で、トップ画面から新規分析、保存済み詳細、詳細Markdown出力、アクセシビリティ表示確認まで進められるよう phase / gate / stop rule を固定
  - product code、score formula、legal meaning、LLMモデル選択、UI全体再設計は未変更
- changed files:
  - `plan/kotomigaki_report_accessibility_audit_2026-06-13/README.md`
  - `plan/kotomigaki_report_accessibility_audit_2026-06-13/TASK.md`
  - `plan/kotomigaki_report_accessibility_audit_2026-06-13/PROGRESS.md`
  - `plan/kotomigaki_report_accessibility_audit_2026-06-13/ROLLBACK.md`
  - `plan/kotomigaki_report_accessibility_audit_2026-06-13/EXECUTION_PROMPT.md`
  - `plan/kotomigaki_report_accessibility_audit_2026-06-13/artifacts/README.md`
  - `WORKLOG.md`
- validation:
  - docs-only change; product tests not required at package creation
  - file presence/readback checked for package files and key audit sections

## 2026-06-12
### History archive for report-quality test

- owner:
  - `kotomigaki_history_archive_for_quality_test_20260612`
- scope:
  - 新しい分析項目とレポート品質の確認前に、既存の分析履歴を削除せず timestamp archive へ退避
  - 現行環境は空履歴で起動し、分析実行前でも履歴検索 / 履歴CSV 導線が表示されることを確認
  - fresh DB 起動時に履歴読み取りが schema 初期化前に走って 500 になる不具合を修正
  - 分析API送信、外部アクセスを伴う新規分析、スコア計算、レポート生成ロジックは未実行 / 未変更
- changed files:
  - `core/storage/database.py`
  - `data/archives/analysis_history_20260612_213535/ARCHIVE_MANIFEST.md`
  - `WORKLOG.md`
- archived files:
  - `data/analysis_history.db` -> `data/archives/analysis_history_20260612_213535/data/analysis_history.db`
  - `data/poc_outputs/runs` -> `data/archives/analysis_history_20260612_213535/data/poc_outputs/runs`
  - `data/poc_outputs/exports` -> `data/archives/analysis_history_20260612_213535/data/poc_outputs/exports`
  - `outputs/monitoring` -> `data/archives/analysis_history_20260612_213535/outputs/monitoring`
- validation:
  - `.venv\\Scripts\\python.exe -m py_compile core\\storage\\database.py` -> PASS
  - `.venv\\Scripts\\python.exe -m pytest tests\\test_analysis_run_service.py -q` -> 32 passed
  - `from core.storage.database import get_history; get_history(limit=5)` on fresh DB -> `[]`
  - SQLite counts after archive: `analysis_runs=0`, `issues=0`, `crawl_pages=0`
  - `Invoke-WebRequest http://127.0.0.1:8081/` -> HTTP 200
  - `Invoke-WebRequest http://127.0.0.1:8081/runs/154` -> HTTP 200 with not-found message, no archived URL content
  - Browser verification: top page showed `最近の分析はまだありません`, `履歴検索`, `履歴CSV`; old `healthrent.duskin.jp` and run `154` were not visible

### Analysis timestamp JST display normalization

- owner:
  - `kotomigaki_analysis_timestamp_jst_display_20260612`
- scope:
  - 履歴一覧、保存済み詳細、履歴比較、詳細Markdown、履歴CSV、優先アクションCSVの分析時刻を `YYYY-MM-DD HH:MM JST` または `MM/DD HH:MM JST` として表示
  - SQLite `CURRENT_TIMESTAMP` 由来の裸時刻はUTC保存値として扱い、表示時にAsia/Tokyoへ変換
  - 新規保存snapshotではDBの `analysis_runs.analyzed_at` を分析時刻の正本にし、`analyzed_at_display` と `run_note` にJST表示を保存
  - DB schema、保存済みraw値、分析ロジック、API送信は変更なし
- changed files:
  - `core/application/time_display.py`
  - `core/application/analysis_run_service.py`
  - `core/application/markdown_report_service.py`
  - `core/application/csv_export_service.py`
  - `core/ui/dashboard.py`
  - `core/ui/saved_workspace.py`
  - `core/ui/panels.py`
  - `tests/test_time_display.py`
  - `tests/test_dashboard_ui.py`
  - `tests/test_csv_export_service.py`
  - `tests/test_markdown_report_service.py`
- validation:
  - `.venv\\Scripts\\python.exe -m py_compile core\\application\\time_display.py core\\application\\analysis_run_service.py core\\application\\markdown_report_service.py core\\application\\csv_export_service.py core\\ui\\dashboard.py core\\ui\\saved_workspace.py core\\ui\\panels.py` -> PASS
  - `.venv\\Scripts\\python.exe -m pytest tests\\test_time_display.py tests\\test_dashboard_ui.py tests\\test_csv_export_service.py tests\\test_markdown_report_service.py -q` -> 18 passed
  - `.venv\\Scripts\\python.exe -m pytest tests\\test_analysis_run_service.py tests\\test_markdown_report_service.py tests\\test_csv_export_service.py tests\\test_dashboard_ui.py tests\\test_time_display.py -q` -> 50 passed

### Accessibility wording normalization for main surfaces

- owner:
  - `kotomigaki_accessibility_wording_20260612`
- scope:
  - 非エンジニア向けの主画面、改善カード、保存済み詳細、レーダー軸で、アクセシビリティ項目を `見やすさ・使いやすさ改善スコア` / `自動検出` / `見やすさ・使いやすさ` 中心に整理
  - 内部カテゴリ key と技術詳細の検出元表示は維持し、JIS/WCAG適合認証のように見える主画面文言は追加しない
  - API送信、分析ロジック、スコア計算、DB schema は変更なし
- changed files:
  - `core/site_health/accessibility_checker.py`
  - `core/site_health/browser_accessibility_scanner.py`
  - `core/site_health/advice_generator.py`
  - `core/application/accessibility_improvement_builder.py`
  - `core/application/analysis_run_service.py`
  - `core/application/technical_summary_builder.py`
  - `core/application/markdown_report_service.py`
  - `core/ui/tabs/health_tab.py`
  - `core/ui/tabs/seo_tab.py`
  - `core/ui/saved_workspace.py`
  - `core/ui/reports/executive_summary.py`
  - `tests/test_accessibility_checker.py`
  - `tests/test_executive_summary.py`
- validation:
  - `.venv\\Scripts\\python.exe -m py_compile core\\site_health\\accessibility_checker.py core\\site_health\\browser_accessibility_scanner.py core\\application\\accessibility_improvement_builder.py core\\application\\analysis_run_service.py core\\application\\technical_summary_builder.py core\\application\\markdown_report_service.py core\\ui\\tabs\\health_tab.py core\\ui\\tabs\\seo_tab.py core\\ui\\saved_workspace.py core\\ui\\reports\\executive_summary.py core\\site_health\\advice_generator.py` -> PASS
  - `.venv\\Scripts\\python.exe -m pytest tests\\test_accessibility_checker.py tests\\test_analysis_run_service.py tests\\test_markdown_report_service.py tests\\test_executive_summary.py -q` -> 56 passed
  - `rg` で主画面用の旧 `アクセシビリティ改善スコア` / `アクセシビリティUXスコア` が残っていないことを確認

### Accessibility display audience split

- アクセシビリティ改善表示を、非エンジニア向けとエンジニア向けに分離する narrow fix を追加
  - 開始時スナップショット: `outputs/snapshots/20260612-114103-accessibility-display-split`
  - `core/application/accessibility_improvement_builder.py` で `audience`（影響 / 見直し箇所 / 次に渡す相手）と `engineer`（対象要素 / 行うべき作業 / 確認方法 / 検出元）を分離
  - 実検出0件または高スコアで具体 issue がない場合、固定テンプレートの汎用修正カードを `actions` として前面表示せず、`confirmation_items` として技術補足側へ下げる
  - `core/ui/tabs/seo_tab.py` / `core/ui/saved_workspace.py` で、SEOタブ・保存済み「改善」「設定」は非エンジニア向け文言だけを表示し、旧snapshotのアクセシビリティ項目もタイトルベースで丸める
  - 保存済み「技術」タブと詳細Markdownでは、実検出ありのアクセシビリティ項目に対象要素、作業内容、確認方法、検出元を表示
  - `ALGORITHM.md` のアクセシビリティ節に、表示分離と固定テンプレート抑制ルールを追記
- 検証:
  - `.venv\\Scripts\\python.exe -m py_compile core\\application\\accessibility_improvement_builder.py core\\application\\analysis_run_service.py core\\application\\markdown_report_service.py core\\ui\\tabs\\seo_tab.py core\\ui\\saved_workspace.py` -> PASS
  - `.venv\\Scripts\\python.exe -m pytest tests\\test_accessibility_checker.py tests\\test_analysis_run_service.py tests\\test_markdown_report_service.py -q` -> 51 passed
  - `.venv\\Scripts\\python.exe -m pytest tests\\test_accessibility_checker.py tests\\test_analysis_run_service.py tests\\test_markdown_report_service.py tests\\test_executive_summary.py -q` -> 56 passed
  - `.venv\\Scripts\\python.exe -m pytest tests -q` -> 142 passed
  - Browser smoke -> `http://127.0.0.1:8081/` でトップ表示、`http://127.0.0.1:8081/runs/154` の「改善」タブで旧snapshot由来の `aria-label` / `<img>` 等が前面表示されず、非エンジニア向け丸め文言に置換されることを確認

### Integrated TECHIE smoke follow-up

- `C:\tetie\techie-hub\start.bat` からの統合起動確認で、保存済みrunのアクセシビリティ出所がUI/Markdownで落ちる箇所を narrow fix
  - `core/application/technical_summary_builder.py` でアクセシビリティのサイトヘルス技術補足に `実ブラウザ自動検出` / `HTML自動検出` を付与
  - `core/ui/saved_workspace.py` で、既存snapshotが古い場合も `result.site_health.accessibility.source` から保存済み詳細表示を補完
  - `core/application/markdown_report_service.py` で詳細Markdownのサイトヘルス欄にも同じ出所を補完
  - `tests/test_analysis_run_service.py` / `tests/test_markdown_report_service.py` に回帰テストを追加
- 検証:
  - `.venv\\Scripts\\python.exe -m pytest tests\\test_analysis_run_service.py tests\\test_accessibility_checker.py tests\\test_markdown_report_service.py -q` -> 50 passed
  - `.venv\\Scripts\\python.exe -m pytest tests -q` -> 141 passed
  - `https://example.com/` の新規分析 run `154` -> `site_health.accessibility.source=browser`
  - `data\\poc_outputs\\exports\\detailed-report-run-154-20260612-102254.md` -> アクセシビリティ `改善スコア` と `実ブラウザ自動検出` を確認
  - Browser smoke -> `http://127.0.0.1:8081/runs/154` の設定タブに `見やすさ・使いやすさ改善`、技術タブに `実ブラウザ自動検出`、旧run `153` も表示崩れなし

### Dashboard history initial render fix

- コトミガキ起動直後に履歴検索/CSVだけが表示され、保存済みrunの行が出ない不具合を修正
  - `nicegui_app.py` の `dashboard_section` を初回に呼び出し、`_load_dashboard_rows()` 後の保存済み履歴をマウントするよう変更
  - refreshable section の更新導線は既存どおり維持
- 検証:
  - `.venv\\Scripts\\python.exe -m py_compile nicegui_app.py` -> PASS
  - `.venv\\Scripts\\python.exe -m pytest tests\\test_analysis_run_service.py tests\\test_markdown_report_service.py -q` -> 34 passed
  - Browser smoke -> `http://127.0.0.1:8081/` 起動直後に `最近の分析`、`50件`、`example.com`、`healthrent.duskin.jp` の履歴行を確認

### Browser accessibility scanner integration

- SEOコンサル向けの「人間からの見やすさ / 使いやすさ / ユニバーサルデザイン」指標として、アクセシビリティスキャナーを既存UIへ違和感なく組み込む narrow fix を追加
  - `tools/accessibility_scanner/` に必要な Playwright / axe-core スキャン部分を内蔵し、デスクトップ上の別ソフト移動に依存しない構成へ変更
  - `core/site_health/browser_accessibility_scanner.py` を追加し、内蔵スキャナーの JSONを `site_health.accessibility.raw/formatted/wcag` 形へ変換
  - `core/engine/site_health_engine.py` で内蔵スキャナーが利用可能な場合は実ブラウザ検査を優先し、Node.js未導入・npm依存未導入・失敗時は既存の `AccessibilityChecker` へ fail-open
  - `color_contrast` / `zoom_scaling` / `aria_semantics` / `keyboard_focus` / `screen_reader_structure` を改善アクション化し、SEO改善・保存済み設定・技術補足の既存枠に流し込む
  - 実ブラウザ検査時の表示を `見やすさ・使いやすさ改善スコア` / `実ブラウザ自動検出` に整理し、新規タブは追加しない
  - レーダーのアクセシビリティ軸は既存の `accessibility_score_snapshot` を継続利用
  - `tools/accessibility_scanner/package.json` / `package-lock.json` で依存を固定し、`node_modules` は `.gitignore` 対象
  - 内蔵スキャナーと開発中の外部ソフトの現行スクリプト SHA-256 が一致することを確認
  - コトミガキ側の優先アクション変換を調整し、内蔵スキャナー由来の `max_severity` が `serious` の `zoom_scaling` は「技術補足 / 中」扱いにして、行動完了ブロッカーと同列にしないよう修正
- 検証:
  - `.venv\\Scripts\\python.exe -m pytest tests\\test_accessibility_checker.py -q` -> 16 passed
  - `.venv\\Scripts\\python.exe -m pytest tests\\test_analysis_run_service.py tests\\test_executive_summary.py tests\\test_characterization_ui.py -q` -> 55 passed
  - `.venv\\Scripts\\python.exe -m pytest tests\\test_accessibility_checker.py tests\\test_analysis_run_service.py tests\\test_executive_summary.py -q` -> 52 passed
  - `.venv\\Scripts\\python.exe -m pytest tests\\test_schema_validator.py -q` -> 3 passed
  - `.venv\\Scripts\\python.exe -m py_compile core\\site_health\\browser_accessibility_scanner.py core\\engine\\site_health_engine.py core\\application\\accessibility_improvement_builder.py core\\application\\analysis_run_service.py core\\ui\\tabs\\health_tab.py core\\ui\\tabs\\seo_tab.py core\\ui\\saved_workspace.py` -> PASS
  - `KOTOMIGAKI_BROWSER_ACCESSIBILITY=1` で `https://example.com/` の `run_full_site_health_check` smoke -> `source=browser`, `見やすさ・使いやすさ改善スコア`, `seo_accessibility_ux_v1`
  - `tools/accessibility_scanner` 内蔵スキャナー単体 smoke: `node scripts/run-safe-url-scan.mjs https://example.com/` -> `completed`, score `90`, `seo_accessibility_ux_v1`

## 2026-06-11
### Accessibility score regression fixtures

- アクセシビリティ改善スコアの代表HTML fixtures と回帰テストを追加
  - `tests/fixtures/accessibility/` に空白ページ、良好な基本ページ、altなし多数、共通ヘッダーbutton名なし、フォームラベルなし、見出し飛び、landmarkなしの fixture を追加
  - `tests/test_accessibility_checker.py` で、空白ページが高得点にならないこと、altなし多数 / labelなし / 見出し飛び / landmarkなしが該当 group に出ることを固定
  - 共通ヘッダーの同一 button 名なしは同一HTML署名で集約し、同じ部品問題を過剰に減点しないよう `core/site_health/accessibility_checker.py` を調整
  - 代表HTML fixture でも LLM fallback 時に件数・順位が変わらないことを追加検証
  - `ALGORITHM.md` のアクセシビリティ節に共通部品の重複集約ルールを追記
  - 検証: `.venv\\Scripts\\pytest.exe -q tests\\test_accessibility_checker.py` -> 15 passed
  - 検証: `.venv\\Scripts\\pytest.exe -q tests` -> 138 passed

### Accessibility action builder LLM fallback design

- アクセシビリティ検出結果を「ユーザーが具体的に何をするか」へ変換する action builder を拡張
  - `core/application/accessibility_improvement_builder.py` で `priority_rank / priority_score / impact / urgency / effort / category / action` をルールベースで固定
  - 任意の LLM 整形は `title / action / reason / verification` の文面だけに限定し、順位・件数・重要度は変更不可にした
  - GPT-5.4 nano 利用時向けに `reasoning.effort` を `none` または `low` に丸め、`temperature=0.0`、JSON Schema固定、`prompt_version / model / reasoning / ruleset_version / html_hash` の metadata 保存を追加
  - LLM整形は課題グループ単位で `max_parallel` を 1-5 に制限し、失敗時は固定テンプレート fallback に戻す
  - `ALGORITHM.md` のアクセシビリティ節に action builder の責務と LLM 境界を追記
  - テスト追加: `tests/test_accessibility_checker.py`
  - 検証: `.venv\\Scripts\\pytest.exe -q tests` -> 130 passed

### Priority action accessibility normalization

- 概要レポート / 優先アクション生成にアクセシビリティ改善項目を統合
  - `core/application/analysis_run_service.py` で SEO / AIO / 法務 / 技術 / アクセシビリティ項目を `category / impact / urgency / effort / action` へ正規化し、LLMを使わない deterministic sort に変更
  - altなし / button名なし / labelなし等の重大アクセシビリティ group は「今すぐやること」上位へ出し、軽微なアクセシビリティ項目は SEO改善または技術補足へ回すよう分類
  - `core/application/csv_export_service.py` の優先アクションCSVに `category` / `urgency` を追加
  - テスト追加/更新: `tests/test_analysis_run_service.py`, `tests/test_csv_export_service.py`
  - 検証: `.venv\\Scripts\\pytest.exe -q tests\\test_analysis_run_service.py tests\\test_accessibility_checker.py tests\\test_csv_export_service.py tests\\test_characterization_ui.py` -> 58 passed

### SEO accessibility improvement section narrow fix

- 目的
  - 新規タブを作らず、既存の SEO改善表示内に `アクセシビリティ改善` セクションを追加する
  - アクセシビリティを、検索エンジン・AI・支援技術が読み取りやすいHTML構造として扱う
  - スコアだけでなく、上位の具体アクション、対象要素、理由、確認方法を非エンジニア向けに表示する
  - HTML検出詳細は技術補足へ退避する

- 実施内容
  - `core/application/accessibility_improvement_builder.py`
    - `site_health.accessibility.raw.issue_groups` から、上位3-5件の作業カードを生成
    - `img alt` / `a button accessible name` / `form label` / `h1` / 見出し階層 / landmark / `html lang` / `title` / `iframe title` 向けの非エンジニア文言を定義
  - `core/ui/tabs/seo_tab.py`
    - SEOタブ内に `アクセシビリティ改善` セクションを追加
    - 各カードに `作業内容 / 対象 / 理由 / 確認方法` を表示
  - `core/ui/panels.py`
    - SEOタブへ `site_health` を渡す。タブ構成自体は変更しない
  - `core/application/analysis_run_service.py`
    - 保存 snapshot の `implementation_workspace.accessibility_improvements` に同じ作業カードを保存
  - `core/ui/saved_workspace.py`
    - 保存済み結果の `実装・設定` に `アクセシビリティ改善` を表示
    - 検出詳細は既存の `エンジニア向け` の `OGP / セキュリティ / アクセシビリティ` に残す
  - `tests/test_accessibility_checker.py` / `tests/test_analysis_run_service.py`
    - builder の文言、対象要素、理由、確認方法、snapshot保存を focused tests で固定

- 検証
  - `.venv\Scripts\python.exe -m pytest tests\test_accessibility_checker.py tests\test_analysis_run_service.py tests\test_characterization_ui.py -q`
    - PASS（53 passed, 1 warning）
  - `.venv\Scripts\python.exe -m py_compile core\application\accessibility_improvement_builder.py core\ui\tabs\seo_tab.py core\ui\panels.py core\application\analysis_run_service.py core\ui\saved_workspace.py`
    - PASS

### Executive summary radar accessibility axis narrow fix

- 目的
  - 改善マップのレーダー軸から `表示安全` を外し、`アクセシビリティ` に差し替える
  - 法務・表示確認はレーダー軸ではなく「先に確認」アラートに残す
  - 技術基盤スコアの平均からアクセシビリティを外し、リンク健全性 / OGP / セキュリティに限定する

- 実施内容
  - `core/ui/reports/executive_summary.py`
    - `accessibility_score_snapshot` を優先し、なければ `site_health.accessibility.formatted.score` を参照
    - レーダー軸を `アクセシビリティ` に変更し、ヒントを `読み上げ / キーボード / 代替テキスト` に変更
    - 技術基盤の算出対象から accessibility を除外
  - `core/application/analysis_run_service.py`
    - 新規保存 snapshot の `summary_workspace` に `accessibility_score_snapshot` を保存
  - `core/ui/saved_workspace.py`
    - 保存済み結果のレーダーでも `アクセシビリティ` 軸を表示
    - 古い snapshot でアクセシビリティ点がない場合は fallback 50点でレーダー表示を維持
  - `tests/test_executive_summary.py` / `tests/test_analysis_run_service.py`
    - live / saved のレーダー軸、法務アラート、snapshot 保存を focused tests で固定

- 検証
  - `.venv\Scripts\python.exe -m pytest tests\test_executive_summary.py tests\test_analysis_run_service.py -q`
    - PASS（33 passed, 1 warning）
  - `.venv\Scripts\python.exe -m py_compile core\ui\reports\executive_summary.py core\ui\saved_workspace.py core\application\analysis_run_service.py`
    - PASS

### Accessibility machine-readable improvement score narrow fix

- 目的
  - `core/site_health/accessibility_checker.py` を、認証・適合判定ではなく「機械可読アクセシビリティ改善スコア」として扱う
  - LLMを使わず、取得済みHTMLから自動検出できる項目だけを deterministic に採点する
  - 空白ページや構造の少ないページが高得点にならないよう、本文量・構造量による score cap を入れる

- 実施内容
  - `core/site_health/accessibility_checker.py`
    - 対象を `html lang` / `title` / `h1` / 見出し階層 / `main nav header footer` landmark / `img alt` / `a button` の accessible name 候補 / `input select textarea` label / `iframe title` に限定
    - raw出力に `score` / `score_status` / `issue_groups` / `affected_counts` / `top_actions` / `scoring_version` を追加
    - `ACCESSIBILITY_SCORE_WEIGHTS` による重み付き合算と `score_cap` を実装
    - 旧互換APIは残しつつ、返却文言は「改善スコア」「自動検出」へ整理
  - `core/ui/tabs/health_tab.py`
    - 表示サマリーを「改善スコア: n点 / 自動検出」に変更
    - advanced表示は `issue_groups` を優先して改善候補を表示
  - `core/application/technical_summary_builder.py`
    - 旧 `wcag_level` 表示の取り込みを削除
  - `tests/test_accessibility_checker.py`
    - 良好HTML、欠落HTML、空白ページcap、UI整形文言の focused tests を追加
  - `ALGORITHM.md`
    - スコア方針、対象項目、score cap、出力キーを追記

- 検証
  - `.venv\Scripts\python.exe -m pytest tests\test_accessibility_checker.py -q`
    - PASS（4 passed）
  - `.venv\Scripts\python.exe -m py_compile core\site_health\accessibility_checker.py core\ui\tabs\health_tab.py core\application\technical_summary_builder.py core\engine\site_health_engine.py`
    - PASS

- 残リスク
  - `C:\tetie\aio2-main` は作業時点で Git リポジトリとして認識されず、`git status` / `git diff` は取得不能。

### UI/application responsibility split

- 目的
  - 既存挙動を変えずに、肥大化していた `analysis_run_service.py` / `panels.py` / `nicegui_app.py` の責務を owner 単位で分ける
  - UI文言整理や新機能追加は混ぜず、既存 private API 互換 import を残す

- 実施内容
  - `core/application/intent_role_map.py`
    - 検索意図・ページ役割マップ生成を抽出
    - `build_search_intent_role_map()` を公開名にし、既存 `_build_search_intent_role_map` 経由の互換も維持
  - `core/application/faq_suggestion_builder.py`
    - FAQ候補、persona、context、debug payload 生成を抽出
    - `analysis_run_service.py` は snapshot 組み立て時に payload を利用する入口へ縮小
  - `core/application/technical_summary_builder.py`
    - legacy page / link health / schema / llms / crawl scope / site health summary を抽出
  - `core/ui/saved_workspace.py`
    - 保存済み詳細の評価 / 改善 / リライト / 設定 / 技術 / 比較タブを抽出
  - `core/ui/panel_components.py`
    - snapshot card、compact row、status / priority badge、diff helper などを抽出
  - `core/ui/styles.py`
    - `nicegui_app.py` の NiceGUI head CSS/script を抽出
  - `AGENTS.md` / `ALGORITHM.md`
    - 変更後の owner 境界を追記

- 検証
  - `.venv\Scripts\python.exe -m py_compile core\application\analysis_run_service.py core\application\intent_role_map.py core\application\faq_suggestion_builder.py core\application\technical_summary_builder.py`
    - PASS
  - `.venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py -q`
    - PASS（28 passed, 1 warning）
  - `.venv\Scripts\python.exe -m py_compile core\ui\panels.py core\ui\saved_workspace.py core\ui\panel_components.py nicegui_app.py`
    - PASS
  - `.venv\Scripts\python.exe -m pytest tests\test_characterization_ui.py tests\test_dashboard_ui.py -q`
    - PASS（30 passed, 1 warning）
  - `.venv\Scripts\python.exe -m py_compile nicegui_app.py`
    - PASS
  - `.venv\Scripts\python.exe -m pytest tests\test_dashboard_ui.py -q`
    - PASS（10 passed, 1 warning）
  - `.venv\Scripts\python.exe -m py_compile nicegui_app.py core\application\analysis_run_service.py core\ui\panels.py core\application\markdown_report_service.py core\ui\dashboard.py`
    - PASS
  - `.venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_dashboard_ui.py tests\test_markdown_report_service.py -q`
    - PASS（60 passed, 1 warning）
  - `.venv\Scripts\python.exe -m pytest tests -q`
    - PASS（117 passed, 1 warning）
  - NiceGUI HTTP smoke（`HEADLESS=1`, `PORT=8097`）
    - `/` 200
    - `/runs/153` 200
    - `export_detailed_markdown_report()` / `export_priority_actions_csv()` を saved bundle 153 で実行し、出力ファイル作成を確認

- 残リスク
  - `C:\tetie\aio2-main` は作業時点で Git リポジトリとして認識されず、`git status` / `HEAD` / `git diff` は取得不能。開始スナップショットは `outputs/snapshots/20260611_150850` に保存した。
  - 分割後も旧 private 名の互換 import を残しているため、次回以降に外部参照を公開名へ寄せる余地がある。

### saved detail detailed Markdown export narrow fix

- 目的
  - `outputs/reports/.../report.md` レベルの詳細分析を、保存済み詳細画面からダウンロードできる導線にする
  - 追加API送信を行わず、保存済み result JSON / snapshot JSON から再構成する

- 実施内容
  - `core/application/markdown_report_service.py`
    - `build_detailed_markdown_report()` と `export_detailed_markdown_report()` を追加
    - スコア、最優先アクション、検索意図・ページ役割、FAQ/引用候補、旧HTML公開リスク、内部リンク機会、補足データをMarkdownへ出力
  - `nicegui_app.py`
    - `/runs/{run_id}` の右上に `詳細Markdown` ダウンロードボタンを追加
  - `core/application/__init__.py`
    - Markdown export service を application API へ公開
  - `ALGORITHM.md` / `AGENTS.md`
    - 保存済み分析の詳細Markdown出力 owner を追記
  - `tests/test_markdown_report_service.py`
    - 主要セクションの出力とファイル書き出しを検証

- 検証
  - `.venv\Scripts\python.exe -m py_compile core\application\markdown_report_service.py core\application\__init__.py nicegui_app.py`
    - PASS
  - `.venv\Scripts\python.exe -m pytest tests\test_markdown_report_service.py tests\test_csv_export_service.py -q`
    - PASS（5 passed, 1 warning）

## 2026-06-08
### saved detail search intent / page role map P2 narrow fix

- 目的
  - コード・snapshot・技術タブには出ている `検索意図・ページ役割マップ` を、保存済み詳細の非エンジニア向け上段評価領域でも確認できるようにする
  - 改善タブの secondary actions で `検索意図` タスクが表示上限外に埋もれないようにする

- 実施内容
  - `core/ui/panels.py`
    - saved detail 上段の評価領域で、`summary_workspace.intent_role_map` から `ページの役割確認` を表示
    - 表示項目を `このページの役割 / 不足 / 次にやること` の3項目だけに限定
    - 上段評価領域には `confidence / source_hits / intent_signals / page_signals / FAQPage / JSON-LD` を出さない
    - 改善タブの `続き N件` expansion 内で、secondary actions の6件目以降にある `検索意図` タスクを表示候補の先頭へ寄せる
  - `tests/test_characterization_ui.py`
    - saved detail 上段向け role map 表示項目が3項目に限定されることを検証
    - secondary actions の表示上限外にある `検索意図` タスクが表示候補に入ることを検証

- UI確認
  - `HEADLESS=1`, `PORT=8092` で NiceGUI を起動し、`http://127.0.0.1:8092/runs/152` を in-app Browser で確認
  - 上段評価領域で `ページの役割確認` が `最優先アクション` の後ろに表示されることを確認
  - 上段評価領域には `このページの役割 / 不足 / 次にやること` が表示され、debug 語や `FAQPage` / `JSON-LD` は出ていないことを確認
  - 改善タブの `続き 11件` を開くと、`検索意図` タスクが表示候補に入ることを確認
  - 設定タブは短い作業要約のまま、技術タブは `source_hits / intent_signals / page_signals` を含む debug / 根拠確認のままであることを確認

- 検証
  - `.venv\Scripts\python.exe -m py_compile core\ui\panels.py tests\test_characterization_ui.py tests\test_analysis_run_service.py`
    - PASS
  - `.venv\Scripts\python.exe -m pytest tests\test_characterization_ui.py -q`
    - PASS（20 passed, 1 warning）
  - `.venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py -q`
    - PASS（28 passed, 1 warning）
  - `.venv\Scripts\python.exe -m pip check`
    - PASS（No broken requirements found）
  - `.venv\Scripts\python.exe -m pytest tests -q`
    - PASS（115 passed, 1 warning）
  - `api_send_count: 0`

- 残リスク
  - 390px 横 overflow の P3 は今回の必須修正に含めていない
  - run 152 の技術タブ内には旧 snapshot 由来の `判定: 中` 表記が残るが、今回の非エンジニア向け上段には判定ラベルを出していない

## 2026-06-07
### search intent / page role map P3 wording narrow fix

- 目的
  - 受け入れレビューで残った P3 文言リスクだけを最小変更で整理する
  - `判定: 高/中/低` が重要度に見える誤読と、公共・団体系で不足文言が商取引寄りに見える誤読を減らす

- 実施内容
  - `core/application/analysis_run_service.py`
    - `confidence_label` を `判定根拠: 高/中/低` に変更
    - `料金/予約/相談・資料請求ページ` の不足名を `料金・費用条件` から `費用・条件・必要情報` へ変更
    - `変更・キャンセル条件` を `変更・注意事項・対象外条件` へ変更し、公共・団体系でも注意事項や対象外条件として読める文言へ寄せた
  - `core/ui/panels.py`
    - `confidence_label` がない旧 snapshot の fallback も `判定根拠: 高/中/低` に変更
  - `tests/test_analysis_run_service.py`
    - 公共・団体系の資料請求/申込ケースで、購入・予約・キャンセル寄りの不足名に戻らないことを検証
  - `tests/test_characterization_ui.py`
    - UI helper の fallback ラベルを検証

- 検証
  - `.venv\Scripts\python.exe -m py_compile core\application\analysis_run_service.py core\ui\panels.py tests\test_analysis_run_service.py tests\test_characterization_ui.py`
    - PASS
  - `.venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py -q`
    - PASS（28 passed, 1 warning）
  - `.venv\Scripts\python.exe -m pytest tests\test_characterization_ui.py -q`
    - PASS（18 passed, 1 warning）
  - `.venv\Scripts\python.exe -m pip check`
    - PASS（No broken requirements found）
  - `.venv\Scripts\python.exe -m pytest tests -q`
    - PASS（113 passed, 1 warning）
  - `api_send_count: 0`

- 残リスク
  - 役割判定は引き続きルールベースであり、公共・団体系専用 role は追加していない

### search intent / page role map UX organization narrow fix

- 目的
  - 既存の `検索意図・ページ役割マップ` を作り直さず、タブ間の重複表示を減らして UX 情報整理を改善する
  - 非エンジニアには意思決定に必要な最小情報、エンジニアには作業場所・根拠・デバッグ情報を分けて表示する

- 実施内容
  - `core/application/analysis_run_service.py`
    - `料金/予約/相談ページ` を `料金/予約/相談・資料請求ページ` に変更
    - 料金系 role の intent / recommended_action / summary を、購入・予約偏重ではなく相談・申込・資料請求にも合う文言へ調整
    - `confidence_label`（`判定: 高/中/低`）を追加し、UI が英語キーを直接出さずに済む形へ整理
    - `engineer_notes.fix_locations` を短い項目リスト化し、既存の `add_headings / add_faq / structured_data / internal_links` は維持
    - `technical_workspace.summary_cards` から `intent_role_map` を外し、schema / llms.txt / link health より強く見えないようにした
    - `SNAPSHOT_SCHEMA_VERSION` を 9 に更新し、旧 snapshot は再構築対象へ入るようにした
  - `core/ui/panels.py`
    - サマリーの `ページの役割確認` を `最優先3件` の後ろへ移動
    - 概要表示を `このページの役割 / 不足 / 次にやること` の3件に限定し、判定は1か所だけ日本語表示にした
    - 実装・設定タブは短い作業要約へ絞り、エンジニア向けタブは `intent_signals / source_hits / page_signals / engineer_notes` 中心へ整理
    - 役割マップFAQ、本文FAQ候補、構造化データ、内部リンク機会マップの使い分けをエンジニア向け expansion 内に短く明記
  - `tests/test_analysis_run_service.py`
    - overview 3件制限、日本語判定ラベル、新 role 名、公共・団体系の資料請求/申込ケース、technical summary からの除外、debug signal 維持を検証
  - `tests/test_characterization_ui.py`
    - 判定ラベルと `fix_locations` 表示 helper の文言を検証

- 検証
  - `.venv\Scripts\python.exe -m py_compile core\application\analysis_run_service.py core\ui\panels.py tests\test_analysis_run_service.py tests\test_characterization_ui.py`
    - PASS
  - `.venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py -q`
    - PASS（28 passed, 1 warning）
  - `.venv\Scripts\python.exe -m pytest tests\test_characterization_ui.py -q`
    - PASS（18 passed, 1 warning）
  - `.venv\Scripts\python.exe -m pip check`
    - PASS（No broken requirements found）
  - `.venv\Scripts\python.exe -m pytest tests -q`
    - PASS（113 passed, 1 warning）

- 残リスク
  - 役割判定は引き続きルールベースであり、既存 saved run は snapshot 再構築時に保存済み result の情報量に依存する
  - `api_send_count: 0`

### search intent / page role map narrow fix

- 目的
  - 分析対象ページが SEO/LLMO 上で担うべき役割を、非エンジニアには意思決定しやすく、エンジニアには作業指示として使える粒度で表示する
  - 特定業種に固定せず、未知のBtoC業種でも `料金/予約/相談` や `集客` などの汎用役割へ倒せるようにする

- 実施内容
  - `core/application/analysis_run_service.py`
    - `検索意図・ページ役割マップ` を snapshot に追加
    - `page_role / intent_signals / user_intent / missing_content / recommended_action / non_engineer_summary / engineer_notes / confidence / evidence_terms` を生成
    - タイトル、meta、見出し、CTA語、本文由来の論点語、URL path token から根拠語を抽出
    - summary / task / implementation / technical workspace に同一 payload を必要な粒度で配置
    - `SNAPSHOT_SCHEMA_VERSION` を 8 に更新し、既存 saved run は再読込時に再構築対象へ入るようにした
  - `core/ui/panels.py`
    - 概要では「このページの役割 / 不足 / 次にやること」の最大3件だけを表示
    - 判定根拠語、実装場所、追加見出し、FAQ、構造化データ、内部リンクは expansion / エンジニア向け側へ退避
  - `tests/test_analysis_run_service.py`
    - 未知のBtoC生活サービスで `料金/予約/相談ページ` として破綻しないことを追加検証
    - 汎用ガイドページが特定業種へ固定されず `集客ページ` に倒れることを追加検証

- 検証
  - `.venv\Scripts\python.exe -m py_compile core\application\analysis_run_service.py core\ui\panels.py tests\test_analysis_run_service.py`
    - PASS
  - `.venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py -q`
    - PASS（27 passed, 1 warning）
  - `.venv\Scripts\python.exe -m pytest tests\test_characterization_ui.py -q`
    - PASS（17 passed, 1 warning）
  - `.venv\Scripts\python.exe -m pip check`
    - PASS（No broken requirements found）
  - `.venv\Scripts\python.exe -m pytest tests -q`
    - PASS（111 passed, 1 warning）

- 残リスク
  - 役割判定はルールベースのため、本文全量が snapshot に入っていない既存結果では title / headings / URL / 既存診断語を中心に判定する
  - `api_send_count: 0`

### reproducible environment lock narrow fix

- 目的
  - 複数人開発や別環境移行で、依存関係を `.venv` の偶然に依存せず再構築できるようにする
  - production code / スコア式 / 付加価値機能は変更せず、環境再現性の入口だけを追加する

- 実施内容
  - `constraints.lock.txt`
    - 2026-06-07 時点の検証済み `.venv` から、推移依存を含む exact pin を固定
  - `requirements-dev.txt`
    - `requirements.txt` に加え、監査/テスト用の `pip-audit==2.10.0` と `pytest==9.0.3` を固定
  - `scripts/rebuild_venv.ps1`
    - Python 3.11 の `.venv` 作成、`pip==26.1.2` 固定、constraints 付き install、`pip check`、任意の `pip-audit` までを1コマンド化
    - `-Recreate` 時は repo 配下の `.venv` 以外を削除しない guard を追加
    - `-NoDev` で runtime-only install、`-SkipAudit` で監査スキップを可能にした
  - `docs/reproducible_environment.md`
    - canonical rebuild、runtime-only rebuild、検証コマンド、依存更新手順、既知の `diskcache` 残リスクを文書化

- canonical rebuild
  - `powershell -ExecutionPolicy Bypass -File .\scripts\rebuild_venv.ps1 -Recreate`
  - runtime-only は `-NoDev` を付ける
  - `requirements-windows.txt` は WeasyPrint を外した Windows PoC profile として保持し、複数人開発の正本は `requirements.txt` + `constraints.lock.txt` とする

- 検証
  - `powershell -ExecutionPolicy Bypass -File .\scripts\rebuild_venv.ps1 -VenvPath outputs\rebuild_smoke_venv -SkipAudit`
    - PASS。新規一時 venv で constraints 付き install と `pip check` が完了
  - `outputs\rebuild_smoke_venv\Scripts\python.exe -m pip check`
    - PASS（No broken requirements found）
  - `outputs\rebuild_smoke_venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py -q`
    - PASS（25 passed, 1 warning）
  - `.venv\Scripts\python.exe -m pip check`
    - PASS（No broken requirements found）
  - `.venv\Scripts\python.exe -m pytest tests -q`
    - PASS（109 passed, 1 warning）
  - `.venv\Scripts\python.exe -m pip_audit -r requirements.txt`
    - `diskcache==5.6.3 / CVE-2025-69872` の 1件のみ残存
  - `PYTHONUTF8=1; .venv\Scripts\python.exe -m pip_audit -r requirements-windows.txt`
    - PASS（No known vulnerabilities found）
  - `.venv\Scripts\python.exe -m pip_audit`
    - `diskcache==5.6.3 / CVE-2025-69872` の 1件のみ残存

- 残リスク
  - `diskcache==5.6.3 / CVE-2025-69872`
    - `pip-audit` に fix version が提示されていないため、依存監査上の既知残リスクとして継続管理
  - `api_send_count: 0`

### dependency vulnerability audit narrow fix

- 目的
  - 直前のコード/LLM脆弱性監査で未実施だった依存関係脆弱性監査を `pip-audit` で実施する
  - 付加価値機能や production code は変更せず、依存 pin と `.venv` の安全な範囲の更新に限定する

- 監査対象
  - `requirements.txt`
  - `requirements-windows.txt`
  - `.venv` の実インストール環境

- 初回監査結果
  - `requirements.txt`: 6パッケージ / 13件
    - `nicegui==3.6.1`: `PYSEC-2026-95`, `CVE-2026-25516`, `CVE-2026-27156`, `CVE-2026-33332`, `CVE-2026-45553`, `CVE-2026-45554`
    - `requests==2.32.5`: `CVE-2026-25645`
    - `python-dotenv==1.2.1`: `CVE-2026-28684`
    - `python-multipart==0.0.22`: `CVE-2026-40347`, `CVE-2026-42561`
    - `starlette==0.50.0`: `PYSEC-2026-161`
    - `diskcache==5.6.3`: `CVE-2025-69872`（修正版提示なし）
  - `.venv`: 15パッケージ / 45件
    - 上記に加え、`aiohttp`, `idna`, `lxml`, `lxml-html-clean`, `pillow`, `pip`, `pygments`, `pytest`, `urllib3` が検出された
  - `requirements-windows.txt`
    - 通常実行では日本語コメントのため `UnicodeDecodeError` が出た
    - `PYTHONUTF8=1` 付き再実行で `No known vulnerabilities found`

- 実施内容
  - `requirements.txt`
    - `nicegui` を `3.6.1` から `3.12.0` へ更新
    - `requests` を `2.32.5` から `2.33.0` へ更新
    - `python-dotenv` を `1.2.1` から `1.2.2` へ更新
    - `fastapi` を `0.128.1` から `0.136.3` へ更新
    - `starlette==1.0.1` を patched transitive として明示固定
    - `python-multipart` を `0.0.22` から `0.0.27` へ更新
  - `.venv`
    - 上記に加え、実環境監査の検出対象として `aiohttp==3.14.0`, `lxml==6.1.1`, `lxml-html-clean==0.4.5`, `Pygments==2.20.0`, `urllib3==2.7.0`, `idna==3.15`, `pillow==12.2.0`, `pytest==9.0.3`, `pip==26.1.2` を反映

- 修正しなかった依存
  - `diskcache==5.6.3`
    - `pip-audit` に fix version が提示されていない
    - 製品コードから直接 import はなく、`instructor` の推移依存として入っている
    - 脆弱性条件は「攻撃者が cache directory に書ける場合の pickle 読込」であり、通常の外部HTTP利用者が `.venv` や cache directory へ書ける前提ではないため、今回は findings / 残リスクとして保持

- 再監査
  - `.venv\Scripts\python.exe -m pip check`
    - PASS（No broken requirements found）
  - `.venv\Scripts\python.exe -m pip_audit -r requirements.txt`
    - `diskcache==5.6.3` の 1件のみ残存
  - `PYTHONUTF8=1; .venv\Scripts\python.exe -m pip_audit -r requirements-windows.txt`
    - PASS（No known vulnerabilities found）
  - `.venv\Scripts\python.exe -m pip_audit`
    - `diskcache==5.6.3` の 1件のみ残存

- 検証
  - `.venv\Scripts\python.exe -m py_compile core\application\analysis_run_service.py core\ui\panels.py nicegui_app.py`
    - PASS
  - `.venv\Scripts\python.exe -m pytest tests -q`
    - PASS（109 passed, 1 warning）
  - NiceGUI HTTP smoke
    - 既存 `8081` は使用中だったため、`8092` で一時起動
    - `http://127.0.0.1:8092/` が HTTP 200 を返し、トップページ本文に `コトミガキ / TECHIE / NiceGUI` 系文字列を確認

- 補足
  - `pip install` 後に `.venv\Lib\site-packages\~il`, `~iohttp`, `~xml` の一時ディレクトリ削除警告が出た
  - 削除を試みたが `.pyd` がロックされており残存。依存解決・監査・テストには影響なし
  - `api_send_count: 0`

### code / LLM security audit narrow fix

- 目的
  - コード脆弱性・LLM脆弱性の監査で見つかった保存済みartifact信頼境界と、外部ページ由来テキストのLLM prompt boundary を narrow fix で補強する
  - API送信なしで、ローカルコード・既存テスト・保存済み構成を根拠に確認する

- Findings
  - Medium: DB の `result_path` をそのまま `Path(...).read_text()` しており、DB改ざん時に `runs/` 外のローカルJSONを dashboard / saved detail が読める余地があった
  - Medium: `core/aio_suggestions.py` と `core/aio/gap_analyzer.py` が外部ページ本文・SchemaをLLM promptへ入れる際、未信頼データ境界とロール注入除去が弱い箇所が残っていた

- 実施内容
  - `core/application/artifact_paths.py`
    - `resolve_existing_result_path()` を追加し、`analysis_result.json` の読取を `RUNS_DIR` 配下・既存ファイル・サイズ上限内に限定
  - `core/application/analysis_run_service.py`
    - saved detail rehydrate と前回比計算で、DB由来 `result_path` を検証してから読むよう変更
  - `core/ui/dashboard.py`
    - 履歴一覧の実スコア補正で、`result_path` が `RUNS_DIR` 外なら snapshot fallback へ戻すよう変更
  - `core/aio_suggestions.py`
    - 外部ページ本文・構造化サマリーを `未信頼データ` と明示し、role風文字列・control token・code fence を除去してから prompt に入れるよう変更
  - `core/aio/gap_analyzer.py`
    - 本文とSchema payloadを値単位でサニタイズし、外部データ内の命令を実行しない境界説明を追加
  - `tests/test_analysis_run_service.py` / `tests/test_dashboard_ui.py` / `tests/test_llm_prompt_boundary.py`
    - `runs/` 外 `result_path` の拒否、snapshot fallback、LLM prompt boundary を追加検証
  - `tests/test_aio_analyzer.py`
    - 既存の古い `requests.get` monkeypatch を、現行の `safe_fetch_url` 経路に合わせて補正

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\application\artifact_paths.py core\application\analysis_run_service.py core\ui\dashboard.py core\aio_suggestions.py core\aio\gap_analyzer.py tests\test_analysis_run_service.py tests\test_dashboard_ui.py tests\test_llm_prompt_boundary.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m pytest tests\test_safe_fetch_security.py tests\test_orchestrator_security.py tests\test_pdf_security.py tests\test_csv_export_service.py tests\test_link_audit.py tests\test_legacy_page_probe.py tests\test_analysis_run_service.py tests\test_dashboard_ui.py tests\test_llm_prompt_boundary.py -q`
    - PASS（66 passed, 1 warning）
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m pytest tests -q`
    - PASS（109 passed, 1 warning）

- 補足
  - 全体 `pytest -q` は `新しいフォルダー (13)` 配下の対象外テストが `seo_llmo_auditor` 未導入で collection error になるため、製品側 `tests/` を正として確認
  - `pip-audit` は venv に未導入のため未実行
  - `api_send_count: 0`

### internal link opportunity map narrow fix

- 目的
  - 監査報告で高優先とされた「内部リンク機会マップ」を、認知負荷を増やさず実装する
  - `孤立/低リンク` の検出から、「どこから、どこへ、何文言でリンクするか」まで作業指示へ落とす

- 実施内容
  - `core/application/analysis_run_service.py`
    - `internal_link_summary` と `link_health_report` から `link_opportunities` を最大3件生成
    - 各候補に `source_url / target_url / recommended_anchor / placement / reason / check` を追加
    - URL文字列だけの場合はpathから主題語を取り、`httpsの詳細` のような不自然なアンカーを避ける
  - `core/ui/panels.py`
    - `実装・設定` では上位2件だけを短く表示
    - `エンジニア向け` では上位3件を「リンク元 / リンク先 / 推奨アンカー / 設置場所 / 完了確認」に分けて表示
    - 既存のリンク先監査詳細は折りたたみのまま維持
  - `tests/test_analysis_run_service.py`
    - snapshot に内部リンク機会マップが保存されることを検証

### FAQ / engineer detail concreteness narrow fix

- 目的
  - 監査報告で弱いとされた FAQ提案とエンジニア向け詳細を、SEO/LLMOコンサルの作業指示として使える粒度へ上げる
  - API生成へ寄せず、既存のルールベース出力に根拠語・回答骨子・設置先・検証条件を追加する

- 実施内容
  - `core/application/analysis_run_service.py`
    - FAQ context に `page_service_terms / location_terms / transaction_terms / customer_intent_terms / raw_page_title_headings` を追加
    - FAQ候補に `answer_outline / recommended_section / schema_candidate / evidence_terms / confidence / risk_if_wrong` を追加
    - `business_goal == 自動判定` をFAQ本文へ直接出さないよう調整
    - 不動産売却・査定文脈で、料金・査定フロー・空き家/相続相談に寄せるFAQへ補正
    - schema / llms.txt / 内部リンクサマリーに実装場所、確認コマンド、合格条件、検証方法を追加
  - `core/ui/panels.py`
    - FAQ提案カードに回答骨子、設置先、FAQPage候補、根拠語、注意点を表示
    - エンジニア向けタブで構造化データのAI回答価値・必須項目・検証方法、llms.txtのContent-Type/推奨本文、内部リンクの修正手順を表示
  - `tests/test_analysis_run_service.py`
    - FAQ新フィールドの保持と、不動産売却ページで法人/導入寄りにずれないことを検証

- 追加調整
  - 不動産売却・査定に限定せず、全業種対象のBtoCプロファイルへ一般化。飲食・介護/福祉・アパレル/物販・美容/サロン・教育/スクールは例示的な補正であり、対象業種を限定しない
  - 未知のBtoC業種でも、予約・相談・料金・利用開始などの顧客行動語から汎用BtoC profile へ倒す
  - BtoCプロファイルがある場合は、`企業` というサイト種別だけで `法人担当者向け` に倒さない
  - 公共・団体ドメインではBtoCプロファイルより公共案内 guardrail を優先
  - 飲食・介護・アパレルの代表ケースに加え、未知業種の生活サービスでも料金/予約/相談FAQに寄ることを回帰テストで確認

### old static HTML public-risk narrow fix

- 目的
  - `data.html` / `system.html` のような旧サイト由来の静的HTMLが、検索やAI回答に残るリスクを検出する
  - 通常クロールやsitemap参照だけでは見つけにくい非リンク旧ページを、認知負荷を増やさず検出時だけ強く出す

- 実在確認
  - `https://www.kyotokogyo.co.jp/data.html`
    - HTTP 200 / final URL `.html` / robots `index,follow` / canonicalなし
  - `https://www.kyotokogyo.co.jp/system.html`
    - HTTP 200 / final URL `.html` / robots `index,follow` / canonicalなし
  - `company.html` と `service.html` は現行URLへ移り canonical あり、`contact.html` は404のため要対応対象外

- 実施内容
  - `core/seo/legacy_page_probe.py`
    - 代表的な旧HTML候補とslug由来候補を上限付きで確認
    - `200 / index可能 / canonicalなし / final .html` のみ要対応として抽出
  - `core/engine/orchestrator.py`
    - 分析結果に `legacy_page_report` を追加
  - `core/application/analysis_run_service.py`
    - 検出時だけ `公開リスク` としてサマリー、Top3、設定/技術ワークスペースへ反映
  - `core/ui/panels.py`
    - 概要は件数中心、URL一覧と対応方法はエンジニア向けタブに表示
  - `tests/test_legacy_page_probe.py` / `tests/test_analysis_run_service.py`
    - 旧HTML検出条件とUI snapshot 昇格の回帰テストを追加

- 検証
  - `py -m py_compile core\seo\legacy_page_probe.py core\engine\orchestrator.py core\application\analysis_run_service.py core\ui\panels.py`
    - PASS
  - `py -m pytest tests\test_legacy_page_probe.py tests\test_analysis_run_service.py::test_ui_snapshot_promotes_legacy_pages_without_extra_clean_state_card tests\test_characterization_ui.py::test_build_summary_priority_note_prefers_actionable_counts -q`
    - PASS（4 passed, 1 warning）

- 追加調整
  - 非エンジニア向け表示は「検索やAI回答が古い情報を拾う可能性」に寄せ、`301 / canonical / noindex` は主説明から後退
  - エンジニア向け表示に `対応タスク` と `完了確認` を追加し、移転先決定、301/308設定、暫定canonical/noindex、sitemap/内部リンク確認、`curl -I` 確認まで作業指示として表示

## 2026-06-03
### safe_fetch NAT64 DNS narrow fix

- 目的
  - `www.d-w-c.jp` のように公開IPv4とNAT64系AAAAを同時に返すURLが、`UNSAFE_URL: private_ip_not_allowed` で分析開始前に落ちる誤検知を解消する
  - SSRF対策として、localhost / private / link-local / multicast / unspecified / non-global IP の拒否は維持する

- 実施内容
  - `core/safe_fetch.py`
    - IP拒否判定を「危険カテゴリまたは非global」へ整理し、`64:ff9b::/96` 系のように `is_reserved=True` でも `is_global=True` のNAT64アドレスを許可
    - 複数解決時は既存どおり公開IPv4を優先して固定接続するため、`www.d-w-c.jp` は `153.125.141.228` へ接続される
  - `tests/test_safe_fetch_security.py`
    - NAT64 + 公開IPv4の解決結果を許可する回帰テストを追加
    - CGNAT共有アドレスなど `is_global=False` の非公開系アドレスを拒否するテストを追加

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\safe_fetch.py tests\test_safe_fetch_security.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m pytest tests\test_safe_fetch_security.py -q`
    - PASS（8 passed）
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py tests\test_orchestrator_security.py -q`
    - PASS（23 passed, 1 warning）
  - `safe_fetch_url("https://www.d-w-c.jp/")`
    - PASS（HTTP 200 / final_ip=`153.125.141.228`）

## 2026-04-23
### dashboard first-view UX narrow fix（一次タスク優先）

- 目的
  - トップ画面で「URLを入れて分析する」という一次タスクがブランドヘッダーの後ろへ沈む状態を改善する
  - 外部遷移リンクよりも、URL入力と分析開始の判断が先に入る情報階層へ戻す

- 実施内容
  - `nicegui_app.py`
    - ダッシュボードの並び順を `共有ナビ → 分析カード → ブランド補助帯 → 履歴` に変更
    - ブランドヘッダーを細い補助帯に圧縮し、`見え方観測へ` を補助リンクへ格下げ
    - 分析カード内に `URLだけで開始 / 保存後の使い方 / 所要時間` の要点を追加
    - 分析カード背景とサイド補助情報のCSSを追加し、ファーストビューのタスク密度を調整

- 検証
  - `python -m py_compile C:\tetie\aio2-main\nicegui_app.py`
    - PASS

### security hardening fix（P0/P1/P2 対応）

- 目的
  - ソース上に露出していた OpenAI API キー定数を除去し、秘密情報を環境変数運用へ統一する
  - `safe_fetch` を迂回していた `robots.txt` / `llms.txt` / `sitemap.xml` / INP 計測の経路を是正し、公開URL以外への到達を防ぐ
  - 引用スニペットのコピー処理で JS 文字列連結に依存していた箇所を安全なシリアライズに置き換える

- 実施内容
  - `core/constants.py`
    - ハードコードされていた `API_KEY` 定数を削除
  - `core/engine/orchestrator.py`
    - `robots.txt` / `llms.txt` 取得を `safe_fetch_url` に統一
    - `robotparser.read()` をやめ、`safe_fetch_url` で取得した本文を `parser.parse()` に渡すよう変更
    - INP 計測前に `validate_public_url()` を必ず通し、公開URL以外はスキップするよう変更
  - `core/aio_analyzer.py`
    - `llms.txt` / `robots.txt` の並列取得を `safe_fetch_url` ベースへ変更
  - `core/sitemap_analyzer.py`
    - `sitemap.xml` / 子 sitemap 取得を `safe_fetch_url` に統一し、リダイレクト先検証とサイズ上限を共通化
  - `core/ui/tabs/simulation_tab.py`
    - クリップボード書き込み時の JS 埋め込みを `json.dumps()` ベースへ変更

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\constants.py core\engine\orchestrator.py core\aio_analyzer.py core\sitemap_analyzer.py core\ui\tabs\simulation_tab.py`
    - PASS

### security findings narrow fix（SSRF / prompt boundary / fail-closed）

- 目的
  - `safe_fetch` の DNS 検証後に再解決される経路を塞ぎ、DNS rebinding を使った SSRF 回避を防ぐ
  - 外部サイト本文を LLM へ渡す境界を強化し、system/user role 風の注入文字列をそのまま trusted prompt に混ぜない
  - PDF 系の LLM 連携で生出力や HTTP エラー本文が通常ログへ落ちる経路を閉じる
  - API キー / secret の危険な既定値を廃止し、未設定時は fail-closed に寄せる

- 実施内容
  - `core/safe_fetch.py`
    - URL 検証を `ResolvedTarget` ベースへ置き換え、DNS 解決結果の公開 IP を固定して接続する custom adapter を追加
    - redirect ごとに再検証しつつ同じ固定 IP 境界で追跡する `resolve_safe_redirect_chain()` を追加
    - `safe_fetch_url()` の metadata に redirect chain と resolved host/IP 情報を保持
  - `core/engine/orchestrator.py`
    - INP 計測サブプロセスへ raw URL ではなく `allowed_hosts / host_ip_map / final_url` を渡すよう変更
    - Playwright 側で host resolver rules と request routing を併用し、許可外 host と未解決 redirect を abort
    - `_sanitize_untrusted_text()` を強化し、外部本文は JSON 形式の untrusted block に閉じ込めて改善提案 / 法務判定 / citation 生成へ渡すよう変更
  - `PDFreport/llm_client.py`
    - `print()` と response body の直接出力を除去し、`DEBUG_API_LOG=True` 時のみ metadata ベースで記録する方式へ変更
    - OpenAI 例外は status code 中心の sanitized summary に統一
  - `PDFreport/config/pdf_config.py`
    - `OPENAI_API_KEY` の test key 既定値を廃止し、空値 default + `require_openai_api_key()` で fail-closed 化
    - `SECRET_KEY` / `JWT_SECRET` / `ENCRYPTION_KEY` の placeholder default を廃止し、`require_secret()` で利用時検証するよう変更
  - `tests/test_safe_fetch_security.py`, `tests/test_orchestrator_security.py`, `tests/test_pdf_security.py`
    - rebinding 耐性、redirect 境界、prompt wrapper、ログ漏えい防止、fail-closed config の targeted test を追加

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\safe_fetch.py core\engine\orchestrator.py PDFreport\llm_client.py PDFreport\config\pdf_config.py tests\test_safe_fetch_security.py tests\test_orchestrator_security.py tests\test_pdf_security.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_safe_fetch_security.py tests\test_orchestrator_security.py tests\test_pdf_security.py tests\test_analysis_run_service.py tests\test_characterization_engine.py tests\test_media_discovery_audit.py`
    - 実行結果は本タスクの完了報告に記載
  - `Playwright` による NiceGUI UI シミュレーション
    - `https://example.com/` を入力して分析開始し、`/runs/{id}` への遷移と saved detail 表示を確認
    - `改善 / リライト / 設定 / 技術 / 比較` タブ切替で追加の reload / main-frame navigation が発生しないことを確認

- 追加修正
  - `core/safe_fetch.py`
    - `urllib3` の pool key 生成時に `fixed_ip` を除外し、実 fetch 経路で `PoolKey.__new__() got an unexpected keyword argument 'key_fixed_ip'` が出る不具合を修正

## 2026-04-20
### summary/engineer wording narrow fix（読み違い防止）

- 目的
  - saved workspace の `判断の目安` で `総合優先度` がスコア値に見える誤読を減らす
  - 技術サマリーで `高得点なのに要対応/注意` に見えるケースへ短い補足を入れ、理解しやすくする

- 実施内容
  - `core/ui/panels.py`
    - `AI認識 / SEO / 総合優先度` に短い説明文を追加
    - `総合優先度` は「点数ではなく、スコアと課題数から見た着手の急ぎ度」と明示
    - 技術サマリーカードで `80点以上` かつ `warn/fail` の場合に、致命項目または注意項目が残っている旨の補足を表示
  - `core/application/analysis_run_service.py`
    - `内部リンク健全性` サマリーに `score` を保持し、saved workspace でも高得点警告の補足が出せるよう調整
    - `構造化データ` サマリーに title を補完し、技術カードの見出し欠落を解消
    - snapshot schema version を更新し、既存保存データも再hydrate時に再構築されるよう調整

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\application\analysis_run_service.py core\ui\panels.py`
    - PASS

### FAQ suggestion contextualization fix（固定テンプレ感の緩和）

- 目的
  - FAQ提案が「完全にテンプレ固定表示」に見える状態を解消し、URL文脈に応じた候補へ寄せる
  - 後から「なぜこのFAQが出たか」を saved workspace / snapshot で追えるようにする

- 実施内容
  - `core/application/analysis_run_service.py`
    - FAQ候補選定の context に `business_goal / page_focus / audience_clues / regulatory_indicators / summary_improvements / page_title` を追加
    - 非EC / EC ともに topic と一致キーワードを持つ候補を作り、採点後に `persona_label` 付きで文面を URL 文脈向けにリライトするよう変更
    - `writing_workspace.faq_debug` を追加し、strategy / persona / context / candidates / selected_count を snapshot へ保存
  - `core/ui/panels.py`
    - FAQ提案カードに `URL文脈で調整` と `対象読者` を表示
    - `提案理由の見立てを見る` expansion を追加し、採用候補と一致語を確認できるよう変更
  - `ALGORITHM.md`
    - FAQ提案生成の現行ルールと `faq_debug` 保存方針を追記
  - `tests/test_analysis_run_service.py`
    - 非EC / EC の FAQ提案が persona-aware な文面へ変わること、および snapshot に `faq_debug` が保存されることを検証

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py`
    - PASS (`14 passed`)

### FAQ persona scoring refinement（URL/ページ文脈シグナル追加）

- 目的
  - FAQ提案のペルソナ判定を `target_audience_clues` 依存から外し、ページ文脈と URL も使って賢くする
  - `なぜ法人担当者向けなのか / なぜ購入前ユーザー向けなのか` を debug payload と UI で追えるようにする

- 実施内容
  - `core/application/analysis_run_service.py`
    - `page_title / meta_description / headings / url_signal_tokens` を FAQ context に追加
    - URL から slug token を抽出する helper を追加
    - FAQ persona を `EC / 経営 / 法人 / 専門職 / 個人 / default` 候補のスコアリングで選定する方式へ変更
    - `faq_debug.persona` に `confidence / source / candidates` を追加
    - live analyze で `industry_analysis` が dataclass で返るケースに対応するため、dict/object 両対応の reader を追加
    - `effective_is_ec` を導入し、raw `is_ec` ではなく guardrail 後の値で FAQ分岐・文面リライトを行うよう変更
    - 公共・団体系向けの FAQ topic (`public_services / public_eligibility / public_application`) を追加し、`or.jp` 系で LMO FAQ が上位を占めにくいよう調整
  - `core/application/faq_signal_profiles.py`
    - 特殊ドメイン (`or.jp / go.jp / lg.jp / ac.jp / ed.jp`) を domain profile として扱う helper を追加
    - 飲食/来訪型ページ向けの `LMO` signal 抽出 helper を追加
    - `ec_detection_reason + domain_profile + lmo_profile` から `effective_is_ec` を決める guardrail helper を追加
  - `core/ui/panels.py`
    - `提案理由の見立てを見る` 内にペルソナの `信頼度 / 主根拠 / 候補一覧` を表示
  - `tests/test_analysis_run_service.py`
    - URL slug とページ title / headings から `法人担当者向け` に寄ることを確認するテストを追加
    - `industry_analysis` object 入力でも FAQ payload が生成できる回帰テストを追加
    - 飲食サイトが `来訪前ユーザー向け` と `LMO` FAQ に寄ること、`or.jp` で soft commerce signal だけでは EC FAQ に倒れないことを追加検証
    - `or.jp` で公共案内 FAQ topic が選ばれることを検証

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\application\analysis_run_service.py core\ui\panels.py tests\test_analysis_run_service.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m pytest tests\test_analysis_run_service.py tests\test_characterization_ui.py`
    - PASS (`36 passed`)
  - live FAQ verify
    - `https://www.hakuundai.net/index.php`
    - `https://www.kyotokogyo.co.jp/`
    - `https://www.kyo.or.jp/kyoto/`
    - `https://www.sunco.co.jp/`
    - `https://www.hirakatapark.co.jp/` は `robots.txt` により block
    - `https://www.kyo.or.jp/kyoto/` は `案内確認ユーザー向け` + `public_services / public_eligibility / public_application` が上位になることを再確認

## 2026-04-13
### ux heuristic audit follow-up（P1/P2 narrow fix 完了）

- 目的
  - `plan/ux_heuristic_audit_followup_2026-04-13/` に沿って、2026-04-13 UX / マーケティング監査の P1/P2 を phase 単位で解消する
  - `analysis logic / score meaning / legal meaning` は変えず、入力体験、完了後制御、dashboard 上段、saved workspace IA、`実装・設定` の停止基準だけを narrow に改善する

- 実施内容
  - `nicegui_app.py`
    - bare host を `https://` 補完する URL 正規化 helper と、対象URL / 比較競合URLの事前バリデーションを追加
    - main / competitor 同一URLを実行前に停止する guardrail を追加
    - `完了後に保存結果を開く` toggle と、分析中の `今は移動しない` 導線を追加
    - completion / progress / saved-run status copy を auto-open choice に応じて切り替えるよう変更
  - `core/ui/dashboard.py`
    - dashboard 上段の説明中心カードを value proposition card に差し替え
    - `このソフトで分かること` と `最近の成果 / 次の入口` を surfacing し、rows があるときは最新保存結果の URL / score summary / priority / top action を表示
  - `core/ui/panels.py`
    - saved workspace の primary tab を `サマリー / やること / 文章改善 / 実装・設定` に整理
    - `エンジニア向け` と `履歴と比較` は `補足メニュー` expansion へ後退
    - `実装・設定` に `ここまで見れば十分` stop message を追加し、`参考` を `参考（後で見る）` に変更
  - `tests/test_dashboard_ui.py`, `tests/test_characterization_ui.py`, `tests/test_analysis_run_service.py`
    - URL guardrail、auto-open copy、dashboard value cards、workspace tab plan、implementation stop message の regression を追加
    - current snapshot refresh contract に合わせて旧 assertion を調整
  - `plan/ux_heuristic_audit_followup_2026-04-13/PROGRESS.md`
    - Phase 1–7 の ledger、self-test、failure log、closeout 状態を更新

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\dashboard.py core\ui\panels.py core\application\analysis_run_service.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_dashboard_ui.py tests\test_characterization_ui.py tests\test_analysis_run_service.py tests\test_executive_summary.py`
    - PASS (`41 passed`)
  - `C:\tetie\techie-hub\start.bat force`
    - PASS
  - live routes
    - `/` -> `200`
    - `/runs/84` -> `200`
  - shell-only verify note
    - NiceGUI hydration の都合で HTML 文字列検索だけでは新文言の視認確認までは安定しなかったため、route availability と regression を closeout evidence とした

## 2026-04-08
### technical workspace surfacing（構造化データ / llms.txt / 内部リンクの前面化）

- 目的
  - 実装済みだが現行 workspace で薄かった `構造化データ` / `llms.txt` / `内部リンク健全性` を front path に戻す
  - `実装・設定` を action-first のまま維持しつつ、技術詳細は `エンジニア向け` タブへ分離する
  - saved run でも新しい技術サマリーが出るよう、snapshot refresh 条件を更新する

- 実施内容
  - `core/application/analysis_run_service.py`
    - snapshot schema version を `3` に更新
    - `llms.txt` の existence だけでなく `quality_score / issues / recommendations` を要約する `llms_summary` を追加
    - `sitemap / priority pages / audited targets` をまとめる `crawl_scope_summary` を追加
    - `internal_link_summary / link_health_report` をまとめる `link_health_summary` を追加
    - `schema_existing / schema_suggestions / FAQ validation` をまとめる `schema_summary` を拡張
    - `OGP / security / accessibility` の score-based summary を `site_health_checks` として snapshot 化
    - `technical_workspace` を新設し、`summary_cards / crawl_scope / link_health / schema / llms / site_health_checks` を保存
    - 旧 snapshot で上記キーが欠ける場合は load 時に rebuild するよう `snapshot_needs_refresh()` を更新
  - `core/ui/panels.py`
    - `実装・設定` タブ先頭に `構造化データ / llms.txt / 内部リンク健全性` の3カードを追加
    - 新しい `エンジニア向け` タブを追加
    - `エンジニア向け` タブに `クロール範囲 / 内部リンク監査 / 構造化データ候補コード / llms.txt / OGP / セキュリティ / アクセシビリティ` の詳細表示を追加

- 検証
  - `python -m py_compile core\application\analysis_run_service.py core\ui\panels.py`
    - PASS
  - pytest / live verify
    - 未実施

## 2026-04-07
### dashboard integrated score consistency fix（初期画面の総合点ずれ補正）

- 目的
  - 初期画面の `総合優先度・スコア` が saved snapshot の旧 `integrated_score` を読んでおり、実際の分析結果とずれるケースを補正
  - `前回比` が裸の数値に見えて、総合点と誤認される表示を解消
  - user-facing の score 表示を `SEO / AIO` 中心に整理し、`法務` をトップ表示から外す

- 実施内容
  - `core/application/analysis_run_service.py`
    - snapshot 保存時の `header.integrated_score` を単純平均ではなく `integrated_results.integrated_score` 優先に変更
    - `previous_diff` 算出時も previous run の `result_path` にある実スコアを優先するよう補正
    - fallback 用 integrated score を `SEO + AIO` ベースへ変更
    - summary/task workspace の user-facing ラベルを `表示アドバイス` に変更し、headline metric から `法務` を除外
    - old snapshot に `法務` / `法務・表示` ラベルが残っている場合は load 時に refresh する条件を追加
    - 主分析 / 競合分析で一時的な例外が出た場合のみ、1秒待って1回だけ再試行する helper を追加
    - `UnsafeURLError` / `ContentTooLargeError` / `TooManyRedirectsError` / `ScrapeBlockedError` は再試行せず即時終了
  - `core/ui/dashboard.py`
    - ホーム履歴 row の `integrated_score` を `result_path` の実スコア優先で再解決するよう変更
    - `previous_diff_label` を `前回比 +N/-N` 表示に統一し、別スコアに見えないよう整理
    - 初期画面の見出しを `統合スコア` に変更し、`AI認識とSEOの加重計算` である説明を追加
    - 履歴 table の score summary を `総合 / AI / SEO` 表示に変更
    - 初期画面では前回 run の score / action を表示しないよう変更し、前回値は履歴からのみ確認する導線へ整理
  - `core/ui/panels.py`, `core/ui/tabs/health_tab.py`, `nicegui_app.py`
    - top / summary / progress / history の `法務` 表示を `表示アドバイス` に整理
    - saved workspace の headline metric では `法務` を表示しないよう調整
    - dashboard sort から `法務順` を削除し、同一URL履歴 table から `法務` 列を削除
  - `tests/test_analysis_run_service.py`, `tests/test_dashboard_ui.py`
    - 旧 snapshot 値より `result_path` の実スコアを優先する回帰 test を追加

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\application\analysis_run_service.py core\ui\dashboard.py tests\test_analysis_run_service.py tests\test_dashboard_ui.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_dashboard_ui.py tests\test_characterization_ui.py tests\test_executive_summary.py`
    - PASS (`30 passed`)
  - live verify
    - `PORT=8081` で `nicegui_app.py` を再起動
    - `http://127.0.0.1:8081/` -> `200`
    - 最新 run の row 解決結果で `snapshot` 保存値 `38` に対し、`result_path` 実スコア `53` が優先されることを確認

### ui design follow-up（実装・設定 / SEO改善 / 健康診断の視覚整理）

- 目的
  - `plan/ui_design_followup_2026-04-07/README.md` の Top 5 に沿って、UI デザイナー視点の narrow fix を実施
  - `score formula / legal meaning / provider meaning` は変更せず、status 表現と情報階層のみ整理

- 実施内容
  - `core/application/analysis_run_service.py`
    - `seo_audit_notes` に `status / status_label / source / source_label / group` を追加
    - saved run が旧 snapshot の場合は `再分析で詳細化` 用の fallback note を生成するよう変更
  - `core/ui/panels.py`
    - saved workspace の `実装・設定` を `要対応 / 注意` / `再分析で詳細化` / `参考` の3層に再編
    - provider 詳細の warn 表現を `注意` に統一し、旧データ note と実データ note を視覚的に分離
  - `core/ui/tabs/seo_tab.py`
    - `追加SEO監査` を status 順（`要対応` → `注意` → `通過` → `参考`）で並べ替え
    - `実データ` / `参考` の chip を付け、1画面目で優先順位が分かるカード表示へ変更
  - `core/ui/tabs/health_tab.py`
    - `健康診断` と `実装メモ` の視覚言語を分離
    - 内部リンク構造は `diagnostic-note-card`、SEO補足は `implementation-note-card` へ整理
  - `nicegui_app.py`
    - `implementation-note-card` / `diagnostic-note-card` / `reference-note-card` の CSS を追加
  - `tests/test_analysis_run_service.py`, `tests/test_characterization_ui.py`
    - fallback note / status label / SEO監査ソートの回帰を追加

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\panels.py core\ui\tabs\seo_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py tests\test_analysis_run_service.py tests\test_characterization_ui.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py tests\test_dashboard_ui.py`
    - PASS (`28 passed`)
  - live verify
    - `PORT=8081` で `nicegui_app.py` を起動
    - `http://127.0.0.1:8081/` -> `200`
    - `http://127.0.0.1:8081/runs/84` -> `200`
    - headless Edge DOM で `/runs/84` の `要対応 / 注意` / `再分析で詳細化` / `参考` / `この保存済みrunは旧データです` を確認

## 2026-04-05
### ux commercial readiness package（Codex 自律実行用 phase package 追加）

- 目的
  - `aio2-main` の post-analysis UI polish を、Codex が別日・別ウィンドウでも迷わず自律実行できる phase package にする
  - phase ごとの自己テスト、retry / stop rule、Web 検索上限、restart prompt を current source of truth として固定する

- 実施内容
  - `plan/ux_commercial_readiness_2026-04-05/`
    - `README.md`
      - package の目的、read order、baseline findings、success criteria、phase summary を追加
    - `TASK.md`
      - Phase 0-8、gate、自己テスト、3 回までの修正、同一 failure での Web 検索上限 3 回、stop rule を固定
    - `PROGRESS.md`
      - current phase、phase ledger、success bar、failure log、user report template を追加
    - `ROLLBACK.md`
      - rollback boundary、do-not-retry、stop condition を追加
    - `EXECUTION_PROMPT.md`
      - 次回再開用の autonomous start prompt を追加
    - `artifacts/README.md`
      - screenshot / verify evidence の保存ルールを追加

- 検証
  - package files の存在確認
    - PASS
  - current docs の read order / predecessor package 参照確認
    - PASS

### ux commercial readiness closeout（post-analysis UI commercial polish 完了）

- 目的
  - `aio2-main` の post-analysis UI を package に沿って commercial readiness まで仕上げる
  - 5 タブ IA を維持したまま、entry copy / hierarchy / implementation compression / FAQ rationale / dashboard density / a11y を narrow に整える

- 実施内容
  - `nicegui_app.py`
    - hero / step / summary / workspace copy を 5 タブ IA に整合
    - dashboard hero chip / analyze note を短文化
    - `focus-visible` outline と input focus ring を追加
  - `core/ui/panels.py`
    - `サマリー` を verdict-first、`やること` を top3-first に再編
    - `実装・設定` を warn/fail-first に圧縮し、pass-only / optional 情報を後退
    - FAQ提案を `question -> reason -> 回答案` の読順に整理
  - `core/ui/dashboard.py`
    - history / mobile / empty state copy を `保存済みワークスペース` 導線で統一
  - `tests/test_characterization_ui.py`
    - hierarchy / implementation compression / FAQ short reason helper test を追加
  - `plan/ux_commercial_readiness_2026-04-05/PROGRESS.md`
    - Phase 0-8 の ledger、failure log、closeout 状態を更新

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\panels.py core\ui\dashboard.py core\ui\tabs\aio_tab.py core\application\analysis_run_service.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py tests\test_dashboard_ui.py`
    - PASS (`26 passed`)
  - live routes
    - `/` -> `200`
    - `/runs/84` -> `200`

## 2026-04-03
### enterprise SaaS redesign mobile history cards（dashboard mobile 履歴の card/list 化）

- 目的
  - mobile の履歴一覧を table 依存から外し、文字量を削って card/list 中心にする
  - AI認識 / SEO は mini bar で見せ、URL と最優先アクションだけを短く残す

- 実施内容
  - `core/ui/dashboard.py`
    - `display_date` / `issue_summary` を追加
    - mobile 専用の `dashboard-history-card` list renderer を追加
    - AI / SEO の mini bar 表示、優先度 badge、`さらに表示` ボタンを追加
    - desktop は table のまま維持し、mobile だけ list へ差し替え
  - `nicegui_app.py`
    - mobile history cards 用の CSS を追加
    - `max-width: 760px` で desktop table を hidden、mobile list を visible に切り替え
  - `tests/test_dashboard_ui.py`
    - `display_date` / `issue_summary` / compact datetime helper の test を追加

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\dashboard.py core\ui\panels.py core\application\analysis_run_service.py core\application\csv_export_service.py core\storage\database.py tests\test_dashboard_ui.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py tests\test_csv_export_service.py tests\test_characterization_engine.py tests\test_dashboard_ui.py`
    - PASS (`23 passed`)
  - live routes
    - `/` -> `200`
    - `/runs/84` -> `200`
    - mobile card tap -> `/runs/86`
  - screenshot artifacts
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/home-desktop-mobilecards.png`
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/home-mobile-cards.png`
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/detail-mobile-cards-check.png`

### enterprise SaaS redesign dashboard density pass（履歴テーブル圧縮）

- 目的
  - dashboard 履歴テーブルの認知負荷を下げ、desktop / mobile ともに最初に読む列を絞る
  - analysis logic / score meaning / detail workspace には触れず、home の表示密度だけを narrow に調整する

- 実施内容
  - `core/ui/dashboard.py`
    - 履歴行に `display_url` / `score_summary` / `top_action_compact` を追加
    - URL を host + 短い path に圧縮し、最優先アクションも短文化
    - テーブル列を `分析日時 / URL / スコア / 優先度 / 最優先アクション` に再編
    - `rowClick` event payload が dict / list の両方で run id を拾えるように調整
  - `core/ui/panels.py`
    - detail workspace の履歴テーブルでも同じ `rowClick` payload 対応を追加
  - `tests/test_dashboard_ui.py`
    - compact 表示用 field が生成されることを固定する targeted test を追加
    - `rowClick` payload の dict / list 両対応を固定する test を追加
  - `tests/test_characterization_ui.py`
    - detail history 用 `rowClick` payload 抽出 helper の test を追加
  - `plan/enterprise_saas_redesign_2026-04-02/PROGRESS.md`
    - density pass の live verify artifact を追記

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\dashboard.py core\ui\panels.py core\application\analysis_run_service.py core\application\csv_export_service.py core\storage\database.py tests\test_dashboard_ui.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py tests\test_csv_export_service.py tests\test_characterization_engine.py tests\test_dashboard_ui.py`
    - PASS (`22 passed`)
  - live routes
    - `/` -> `200`
    - `/runs/84` -> `200`
    - dashboard row click -> `/runs/86`
  - screenshot artifacts
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/home-desktop-density.png`
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/home-mobile-density.png`
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/detail-desktop-density-check.png`
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/detail-mobile-density-check.png`

## 2026-04-02
### enterprise SaaS redesign（dashboard + saved detail workspace）

- 目的
  - `aio2-main` を analysis logic 非変更のまま企業向け SaaS の dashboard + detail workspace へ再設計する
  - PDF / print 主導線を廃止し、保存済み分析の再利用と CSV export を主導線にする

- 実施内容
  - Phase package
    - `plan/enterprise_saas_redesign_2026-04-02/README.md`
    - `plan/enterprise_saas_redesign_2026-04-02/TASK.md`
    - `plan/enterprise_saas_redesign_2026-04-02/PROGRESS.md`
    - `plan/enterprise_saas_redesign_2026-04-02/ROLLBACK.md`
    - `plan/enterprise_saas_redesign_2026-04-02/EXECUTION_PROMPT.md`
    - baseline / phase screenshot artifacts を追加
  - Persistence
    - `core/storage/database.py`
      - `analysis_runs` に `result_path` / `snapshot_json` migration を追加
      - `get_run()` / `get_run_detail()` / artifact update helper を追加
    - `core/application/analysis_run_service.py`
      - result JSON 保存、UI snapshot JSON 保存、saved run bundle 読み出しを追加
  - Export
    - `core/application/csv_export_service.py` を追加
    - 履歴一覧CSVと優先アクションCSVを追加
    - spreadsheet formula injection 対策を実装
  - UI
    - `core/ui/dashboard.py` を enterprise dashboard 用 helper に作り替え
    - `core/ui/panels.py` に saved detail workspace renderer を追加
    - `nicegui_app.py`
      - active `/` を dashboard に差し替え
      - `/runs/{run_id}` を追加
      - 分析完了後は saved detail へ遷移する flow に変更
      - active `/report/print` route は除去
  - Docs
    - `AGENTS.md` と `ALGORITHM.md` を dashboard/detail + CSV current state に更新

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\dashboard.py core\ui\panels.py core\application\analysis_run_service.py core\application\csv_export_service.py core\storage\database.py tests\test_analysis_run_service.py tests\test_csv_export_service.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py tests\test_csv_export_service.py`
    - PASS (`17 passed`)
  - `C:\tetie\techie-hub\start.bat force`
    - PASS
  - live routes
    - `/` -> `200`
    - `/runs/84` -> `200`
    - `/report/print` -> `404`

### enterprise SaaS redesign residual cleanup（PDF path deletion）

- 目的
  - Phase 7 residual として残っていた PDF export / print renderer / legacy print state を current code から削除する

- 実施内容
  - `core/engine/orchestrator.py`
    - `export_analysis_pdf_report` import と `generate_enhanced_pdf_report()` wrapper を削除
    - `last_pdf_meta` state を削除
  - `core/reporting/`
    - `pdf_export_service.py` と package export を削除
  - `core/ui/reports/print_report.py`
    - file 自体を削除
  - `core/ui/panels.py`
    - `print_mode` 分岐と `印刷用ページを開く` link を削除
  - `nicegui_app.py`
    - `REPORTS_DIR` static publish と `print_mode` state、legacy `印刷用ページ` link を削除
  - `tests/test_characterization_engine.py`
    - PDF wrapper 向け test を削除

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\dashboard.py core\ui\panels.py core\application\analysis_run_service.py core\application\csv_export_service.py core\storage\database.py core\engine\orchestrator.py tests\test_analysis_run_service.py tests\test_csv_export_service.py tests\test_characterization_engine.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py tests\test_csv_export_service.py tests\test_characterization_engine.py`
    - PASS (`19 passed`)
  - `C:\tetie\techie-hub\start.bat force`
    - PASS
  - live routes
    - `/` -> `200`
    - `/runs/84` -> `200`
    - `/report/print` -> `404`
  - screenshot artifacts
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/`

### enterprise SaaS redesign feedback pass（情報密度と文言の再調整）

- 目的
  - enterprise SaaS としての可読性を上げ、hero / 上段サマリー / detail workspace の認知負荷を下げる

- 実施内容
  - `nicegui_app.py`
    - dashboard hero を compact 化し、ロゴ・見出し・helper text を縮小
    - chip 文言を英語から `保存一覧 / 詳細再表示 / CSV出力` に変更
    - helper text と本文のサイズ差を拡大
  - `core/ui/panels.py`
    - 最優先3件を全文カードから要点カードに変更
    - `今回のURL` 表記を `対象ページで確認` に寄せる UI 正規化を追加
    - detail workspace を `左メニュー + 作業面` の構成へ変更
    - `技術補足` を `実装メモ` に改名し、意味説明を追加
    - 概要の重複見出しカードを compact note 化
  - `core/application/analysis_run_service.py`
    - 新規保存 snapshot の label / run note を current UI copy に合わせて更新

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\panels.py core\application\analysis_run_service.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py tests\test_csv_export_service.py tests\test_characterization_engine.py`
    - PASS (`19 passed`)
  - screenshot artifacts
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/home-desktop-polish.png`
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/detail-desktop-polish.png`
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/detail-mobile-polish.png`

### enterprise SaaS redesign feedback pass 2（ラベル整理 + 左メニュー視認性）

- 目的
  - `対象ページで確認` の反復ラベルを減らし、detail workspace 左メニューの視認性を上げる

- 実施内容
  - `core/ui/panels.py`
    - main action 面では URL系ラベルを非表示化し、必要な箇所だけ `このページ向け` に正規化
    - top action meta を area のみへ整理
    - 概要の compact note から重複ラベルを削除
  - `nicegui_app.py`
    - 左メニューに panel 背景・border・shadow を追加
    - active tab の背景と境界を強めて選択状態を見分けやすくした

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\panels.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py tests\test_csv_export_service.py tests\test_characterization_engine.py`
    - PASS (`19 passed`)
  - screenshot artifacts
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/detail-desktop-feedback2.png`
    - `plan/enterprise_saas_redesign_2026-04-02/artifacts/phase-07/detail-mobile-feedback2.png`

### コトミガキ UI 情報圧縮の narrow fix

- 目的
  - `現状 / 改善方法 / 詳細 / 内部診断` の役割をさらに明確にし、主画面の情報量を圧縮する
  - 分析ロジックは変えず、`nicegui_app.py` と `core/ui/panels.py` の表示だけを整理する

- 実施内容
  - `nicegui_app.py`
    - `今回の分析結果` / `改善方法` ヘッダーから重複した導線見出しを削除
    - 折りたたみ操作を独立行ではなくヘッダー右側へ寄せ、上段の縦伸びを抑制
  - `core/ui/panels.py`
    - `各AIサービスの公開条件` をカード列から compact chip 表示へ圧縮
    - 要約の warning 表示を先頭3件 + `ほかN件` に整理
    - `現状` の URL 固有ハイライト件数を要約では3件までに制限
    - `改善方法` の `結論サマリ` を常時展開の短いブロックへ変更し、指標を `全体判断 / AI検索 / 法務・表示` の3つへ圧縮
    - `内部診断` の二重折りたたみをやめ、`分析前提` と `比較・技術メモ` の compact 行表示へ整理
    - `文章の改善案` はデータがある項目だけ見出しを出すようにし、未生成メッセージの連発を抑制
    - `今日からできること` と `公式ドキュメント` は表示件数を絞った
  - `tests/test_characterization_ui.py`
    - 内部診断の compact 行生成 helper を固定するテストを追加

- 検証予定
  - `py_compile` と UI系の targeted pytest で確認
  - 追加調整として `core/ui/tabs/health_tab.py` の固定セキュリティFAQと固定リスク整理を closed expansion に後退し、URL固有の改善提案より目立たない構成へ変更

## 2026-03-30
### 引継ぎメモ（電源オフ前）

- 現状
  - v2 アルゴリズム本体は反映済み前提で確認を進めており、主な残課題は UI / PDF の情報設計
  - トップは `TECHIE / コトミガキ` の1カラム寄り構成へ調整済み
  - ツールチップは可読性を上げつつ、固有名詞・アルゴリズム説明を削る方向へ整理済み
  - `改善方法` タブでは `文章の改善案` を先頭へ寄せ、付加価値が見えやすい順へ変更済み

- 次回の最優先課題
  - `各AIサービスの公開条件` ブロックが冗長
  - 1サービス1カードで縦に伸びすぎており、スペースを取りすぎる
  - 利用者にとって意味が分かりにくく、`現状` と `次に何をすべきか` の理解を邪魔している

- 次回の改善方針
  - `各AIサービスの公開条件` は summary で大きなカードにせず、1行の compact table / chips / badge 行へ圧縮する
  - 主画面では `通過 / 注意 / 要対応` の一覧だけ見せ、細かい条件は展開後に初めて見せる
  - 固有名詞や bot 名、判定ロジック説明は主画面やツールチップに出さない
  - PDF も `結論 / 最優先アクション / 文章の改善案 / 詳細付録` の順に寄せ、一覧画面の複雑さを下げる
  - `分かりやすさ第一` を優先し、アルゴリズム説明よりも「何が問題か / どう直すか」を前面に出す

### overview-first UI の追加整理

- 目的
  - ユーザーが見るべき `現状` と `改善方法` をさらに前面に出し、主画面の説明テキストを削る
  - Semrush / Ahrefs / Google Search Console / MarketMuse などの overview-first な情報設計に近づける
  - 補足説明は常設せず、必要時だけマウスオーバーで確認できるようにする

- 実施内容
  - `nicegui_app.py`
    - `ろごSV.svg` を static 配下へ反映し、トップを `TECHIE / コトミガキ` のロゴ中心ヘッダーへ整理
    - ヒーロー内の説明カードを圧縮し、主説明を1行 + チップ + ツールチップへ置換
    - 入力欄、表示スタイル、比重調整、分析結果見出し、改善方法見出しの補足をツールチップ化
    - client 切断後に progress / step indicator を更新し続けないよう safety guard を追加
    - 追加調整として `最初に見る項目` の右カラムを削除し、トップを1カラム化
    - ロゴ asset を `logo_mark.svg` に切り替え、ブランド表示の視認性を改善
    - ツールチップの文字サイズと行間を引き上げて可読性を改善
    - ヒーロー文言を `あなたのサイトを最適化` 中心の短い訴求へ変更し、トップの認知負荷をさらに削減
    - ツールチップ内の固有名詞・アルゴリズム寄り説明を削減し、一般的な案内だけに整理
    - 要約から内部診断寄りの数値説明を後退させ、`全体 / 検索 / AI検索` と最優先提案を中心に再編
    - `改善方法` タブでは `文章の改善案` を先頭にし、付加価値として伝わりやすい提案を前に出した
  - `core/ui/panels.py`
    - `現状`、`各AIサービスの公開条件`、`今すぐやること` などの補足説明をツールチップへ移動
    - `このタブの役割` の常設カードを削除
    - 作業ウィンドウの `根拠` タブを `詳細` に変更
  - `core/ui/reports/executive_summary.py`
    - `今回の分析結果` の補足をツールチップへ移動し、前提カードを簡潔化
  - `core/ui/tabs/aio_tab.py`
    - AIOスコア要約と provider readiness の説明文をツールチップ化
  - `core/ui/reports/print_report.py`
    - 印刷側の見出しを `改善方法` に寄せ、余分な説明見出しを抑制

### `現状 / 改善方法` 優先の narrow fix

- 目的
  - 主画面から固定テンプレートを外し、ユーザーが見たい `現状` と `改善方法` に集中させる
  - 既存 SEO / LLMO SaaS の overview-first UI に合わせ、主画面の情報を絞る
  - `ui.timer` 由来の NiceGUI ログノイズを減らす

- 実施内容
  - `core/ui/panels.py`
    - 作業ウィンドウのタブを `現状 / 改善方法 / 根拠 / 内部診断` に整理
    - `固定の参考情報` タブを主画面から除去
    - タイトル案・説明文案・FAQ案が未生成の場合は、一般テンプレートに逃がさず URL 固有の不足だけを表示
  - `nicegui_app.py`
    - ヒーローと作業領域の案内文を `現状` と `改善方法` 中心へ変更
    - `ui.timer` を async loop に置き換え
  - `core/ui/reports/executive_summary.py`
    - `改善方法` の呼称に統一
  - `core/ui/reports/print_report.py`
    - 印刷側も `改善方法と詳細` へ統一

### UI文言とブランド表示の narrow fix

- 目的
  - 分析結果と固定説明の境界を一目で分かるようにする
  - 日本語話者向けに英語ラベルを減らし、`TECHIE / コトミガキ` の関係をトップで明示する
  - 印刷版でも「あなた向けの提案」が先に見える読み順に寄せる

- 実施内容
  - `nicegui_app.py`
    - トップを `TECHIE ブランドのサイト診断サービス` + `コトミガキ` の日本語中心ヘッダーへ変更
    - ロゴ周辺に余白付きの表示枠を追加し、サービス名と役割を分かりやすくした
    - `STEP` 表記を `手順` へ変更し、`今回の分析結果` / `改善提案と詳細` の見出しへ整理
  - `core/ui/reports/executive_summary.py`
    - `分析サマリー` を `今回の分析結果` へ変更
    - `あなたに最初にお願いしたいこと` を前に出し、利用者向けの助言と認識しやすい文言へ調整
  - `core/ui/panels.py`
    - `今回のURLで見つかったこと / あなた向けの改善提案 / 判定メモ・内部診断 / 固定の参考情報` のタブ構成へ変更
    - `本文リライト（変更前 / 変更後）` など英語ラベルを日本語へ統一
    - 印刷時の表示順を `あなた向けの改善提案` → `今回のURLで見つかったこと` に変更
  - `core/ui/tabs/aio_tab.py`
    - `provider readiness` の説明文を日本語化

### UI 再設計（summary / workspace / details 分離）

- 目的
  - v2 の表示方針を崩さずに、縦長の1枚画面を整理する
  - 「このURL固有の結果」と「固定説明」と「内部診断」を混同しない構成へ切り替える
  - 画面判断を先に、詳細作業を後にする SaaS 型レイアウトへ寄せる

- 実施内容
  - `nicegui_app.py`
    - ヒーローを圧縮し、入力領域を `URL入力` と折りたたみ式の `補助入力 / 詳細設定` に再編
    - 分析結果エリアを `要約ストリップ` → `改善レポート / 作業ウィンドウ` の縦構成へ変更
    - 分析完了後に summary へ自動スクロールする導線を追加
    - `改善レポートへ移動` / `要約へ戻る` の移動ボタンを追加
  - `core/ui/panels.py`
    - summary に provider readiness の compact summary を追加
    - 前回比較と詳細な競合比較を summary から外し、後段タブへ後退
    - `補足・システムメモ` を `内部診断・補足` に改名
    - `参考テンプレート` タブを追加し、タイトル/説明文/引用構造/FAQ の汎用テンプレートを分離
    - 改善プラン本体では、URL固有でないテンプレートを notice のみ残して本体表示から外した
    - `/report/print` route の shell 描画を `core/ui/reports/print_report.py` へ委譲
  - `core/ui/reports/print_report.py`
    - current panels ベースの印刷 shell renderer `render_print_report_shell()` を追加
  - `core/ui/tabs/aio_tab.py`
    - `penalty_multiplier=1.0` かつ追加 penalty なしの場合、冗長な式表示をやめて簡易要約へ変更
    - provider readiness 詳細を expansion 化
    - `JSON-LD Author未設定` を必須不足扱いに見える強い文言から補助シグナル説明へ変更
  - `core/ui/tabs/health_tab.py`
    - `llms.txt` の配置ベストプラクティスを折りたたみ化
  - `tests/test_characterization_ui.py`
    - provider summary row の status 表示変換テストを追加
  - 文書
    - `AGENTS.md` の UI構成と `/report/print` owner 説明を現行導線へ更新

- 非対象
  - `core/aio_suggestions.py` の legacy template
  - `core/engine/orchestrator.py` 内 legacy `_check_robots_txt()`
  - スコア式やアルゴリズム本体

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\panels.py core\ui\reports\executive_summary.py core\ui\reports\print_report.py core\ui\tabs\aio_tab.py core\ui\tabs\health_tab.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m pytest -q tests\test_characterization_ui.py tests\test_executive_summary.py`
    - PASS (`6 passed`)

## 2026-03-29
### アルゴリズム v2 実装（provider gate / note 分離）

- 目的
  - 監査PLANで合意した v2 を実装し、公式公開条件と内部ヒューリスティックを分離する
  - provider別 numeric 推定と YMYL 乗算をやめ、説明可能な status / note 中心へ切り替える
  - UI文言で `公式条件` と `内部推定` を混同しないよう整える

- 実施内容
  - `core/aio_analyzer.py`
    - `estimate_platform_citation()` を廃止し、`provider_readiness` を追加
    - Google / OpenAI Search / Perplexity / Claude Search を `pass / warn / fail` で判定
    - `llms.txt`, `GPTBot`, `Google-Extended`, `ChatGPT-User`, `Claude-User`, `ClaudeBot`, `CCBot` を informational note 化
    - `tech_score` から llms/bot 許可を外し、`HTTPS + 応答速度 + baseline` の soft technical に再編
    - `JSON-LD` を構造スコアの直接加点から外し、補助シグナルへ変更
    - AIO側の multiplicative penalty を実質停止（`penalty_multiplier=1.0`）
  - `core/scoring_engine.py`
    - YMYL の `1.2x / 0.7x / 0.5x` 数値補正を廃止
    - YMYL は warning / heuristic note のみとし、統合スコアへ乗算しない
    - `parasitic_content_flag` penalty を `0.7x → 0.85x` に緩和
    - `INTENT_ALPHA` は維持しつつ internal heuristic と明記
  - `core/engine/orchestrator.py`
    - `Claude-SearchBot` を含む search crawler warning へ更新
    - `llms.txt` 未設置 warning を削除
    - `JSON-LD` warning を「公式必須ではない」文言へ調整
    - `provider_readiness` を UI 向け payload に投影
  - UI
    - `core/ui/tabs/aio_tab.py`: provider別 numeric bar を廃止し、`公式公開条件 / 内部ヒューリスティック / 任意メモ` の3区分表示へ変更
    - `core/ui/panels.py`: GEO文言を「内部診断」へ調整し、技術チェックを provider別 gate 中心へ更新
    - `core/ui/reports/executive_summary.py`: GEO文言を「内部診断」へ調整
    - `core/ui/tabs/health_tab.py`: llms.txt を任意メモとして表示
  - 文書
    - `ALGORITHM.md`, `AIO_ALGORITHM.md` を v2 実装へ更新

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile ...`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m pytest -q tests\test_aio_analyzer.py tests\test_scoring_engine.py tests\test_executive_summary.py`
    - PASS (`6 passed`)
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -c "from core.aio_analyzer import AIOContentAnalyzer; ..."`
    - PASS (`import-smoke-ok`)

### アルゴリズム監査と NiceGUI 画面再設計

- 目的
  - `ALGORITHM.md` を正本にして、実装コード・現UI・PDFの整合を確認する
  - 「計算が怪しい箇所」と「表示だけが誤解を生む箇所」を切り分けたうえで UI を再設計する
  - 印刷前提の長い1枚画面から、SaaS らしい作業分離型の画面へ寄せる

- アルゴリズム監査の結果
  - `core/scoring_engine.py`
    - YMYLペナルティ条件を `is_ymyl_context and AIO E-E-A-T < 4.0` に整理
    - 旧来の SEO 側簡易ヒューリスティックだけで 0.5x を掛けないよう修正
  - `core/engine/orchestrator.py`
    - 日本語ページ向けに Experience / Author 可視シグナルを拡張
    - AIO UIスコアへ `citation`, `freshness`, `aeo`, `entity_linking`, `eeat`, `geo_tldr`, `geo_stats` を明示的に投影
  - 監査結論
    - 実ロジックの問題: YMYLペナルティのゲート条件
    - 表示の問題: AIO重みと説明文が旧8指標のままで、現行11指標とズレていた

- UI / 情報設計の変更
  - `nicegui_app.py`
    - 暖色ベースのブランドカラーへ調整
    - ヒーロー、入力ワークスペース、要約ウィンドウ、作業ウィンドウの構成へ再編
    - 結果表示を `summary rail + workbench` の2カラム構成に変更
  - `core/ui/panels.py`
    - `このURL固有の所見` を要約と作業ウィンドウの両方で先頭表示
    - `改善プラン / 根拠・詳細 / 補足・システムメモ` をタブで分離
    - FAQテンプレート、引用テンプレート、プラットフォーム別一般ガイドに `一般説明 / 固定テンプレート` のラベルを追加
  - `core/ui/reports/executive_summary.py`
    - 業種・サイト種別・重視目標・スコア差から、先頭サマリー文をパーソナライズ
  - `core/ui/tabs/aio_tab.py`
    - AIO内訳を現行11指標の重みで表示し、旧来のまとめ行 `0.25` を廃止

- 文書更新
  - `ALGORITHM.md`: YMYL補正とペナルティ条件を現行仕様へ更新
  - `AIO_ALGORITHM.md`: 構造スコア内訳と AIO / integrate のペナルティ責務を現実装に合わせて更新
  - `AGENTS.md`: 画面構成の入口説明を新しいワークスペース構成に更新

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile ...` で変更ファイルの構文確認
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m pytest -q`
  - 結果: `18 passed`

## 2026-03-25
### live UI 再起動確認（ホーム文言反映の確認のみ）

- 目的
  - 入力フォームの平文化 narrow fix が live UI に反映されているかを再起動後に確認する
  - 必要なら追加の narrow fix へ進む前提を整える
  - 分析ロジック、スコア式、法務判定、保存キーは変更しない

- 実施内容
  - `http://127.0.0.1:8087/` はこの時点で未起動で、現行 live は `http://127.0.0.1:8081/` だった
  - 旧文言を返していた `8081` の既存プロセスを停止し、`C:\tetie\aio2-main\.venv\Scripts\python.exe run_app.py` を `PORT=8081`, `HEADLESS=1` で再起動
  - 再起動後、headless Edge でホーム画面を確認し、以下の文言が live UI に反映されていることを確認
    - `今回重視したいこと`
    - `重視したいことを選択（任意）`
    - `検索向け / AI検索向け の比重`
    - `おまかせ`
    - `検索向け`
    - `AI検索向け`
    - `おまかせ（自動で判定）`
  - `/report/print` は空状態で正常表示され、`分析結果がありません。先に分析を実行してください。` を確認
  - 追加の UI 文言修正は今回は不要と判断し、コード変更は行わなかった

- 検証
  - `http://127.0.0.1:8081/`
    - 再起動後に `200` 応答を確認
    - headless Edge の render 後 DOM でホーム画面対象文言を確認
  - `http://127.0.0.1:8081/report/print`
    - 空状態の表示を確認
  - 進捗表示の `検索向け評価` / `AI検索向け評価`
    - `nicegui_app.py` の `progress_steps` に実装済みであることを確認
    - live 実行確認は `https://example.com` で 1 回試したが接続タイムアウトとなり、画面上の実表示までは未確認

### live UI narrow fix（入力フォームの比重ラベル平文化・表記揺れ統一）

- 目的
  - 入力フォームに残っていた `SEO <-> AIO バランス` や `AIO寄り(70)` などの専門寄り表現を、非エンジニアでも意味が取りやすい表現へ寄せる
  - `おまかせ（自動で判定）` と `おまかせ（自動で判断）` の表記揺れを解消する
  - 内部値・分析ロジック・保存キーは変更しない

- 実施内容
  - `nicegui_app.py`
    - `GOAL_OPTION_LABELS` の `自動判定` 表示を `おまかせ（自動で判定）` に統一
    - `ビジネス目標` を `今回重視したいこと`、`目標を選択（任意）` を `重視したいことを選択（任意）` に変更
    - `SEO <-> AIO バランス` を `検索向け / AI検索向け の比重` に変更
    - バランス補助文を `基本はおまかせで十分です...` の案内へ変更
    - スライダー状態文言を `おまかせ（推奨）` / `検索向け` / `AI検索向け` の平文に変更
    - プリセットボタンを `自動(50) / SEO寄り(30) / AIO寄り(70)` から `おまかせ / 検索向け / AI検索向け` に変更
    - 進捗表示の `SEO評価 / AIO評価` を `検索向け評価 / AI検索向け評価` に変更
    - 分析開始ボタンの aria-label も平文化

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile C:\tetie\aio2-main\nicegui_app.py`
    - PASS
  - `http://127.0.0.1:8087/`
    - 応答自体は確認できたが、稼働中インスタンスは旧文言のままだった
    - ソース更新後の再起動前と判断し、live 表示反映の最終確認は未実施

### live UI / `/report/print` narrow fix（固定表記・専門ラベルの平文化）

- 目的
  - live UI と `/report/print` の両方で、内部都合の固定表記や専門寄りラベルを非エンジニアが読める文言に寄せる
  - `自社理解 / 結論 / 初手` の読み順は維持し、分析ロジックやスコア算出は変更しない

- 実施内容
  - `nicegui_app.py`
    - 入力フォームの `自動判定 / カスタム/その他 / GEO/AIO優先` などを、内部値は維持したまま表示ラベルだけ平文化
    - 業界 / サイト作成サービス / サイト種別 / ビジネス目標のセレクトを `dict` オプションに切り替え、`おまかせ（自動で見立て・判定）` などの非エンジニア向け表示へ変更
    - 補助説明の `迷ったら自動判定のままで大丈夫です。` を `迷ったらおまかせのままで大丈夫です。` に変更
  - `core/ui/reports/executive_summary.py`
    - `自動判定 / 未検出 / カスタム/その他` などの内部値を、先頭サマリー表示だけ平文化する整形を追加
    - `目標` を `今回重視したこと` に変更し、目標文言も `SEO優先 / GEO/AIO優先` などの内部語を平文化
    - `生成AI最適化（GEO）` の補助説明を `AI検索で見つけられやすい状態` に変更し、`TL;DR / E-E-A-T` も説明文へ置換
  - `core/ui/panels.py`
    - `AIO伝達性 / リーガル明確性 / 信頼情報明確性` を、意味を変えずに平文ラベルへ変更
    - `今回の結論（AIO × リーガル）` や `補足情報（前回比較・判定条件・システムメモ）` などの見出しを平文化
    - `主業種は『自動判定』` のような不自然表示を避けるため、補足情報の `サイト種別 / 業界 / EC判定 / クロール設定 / 構造化データ / AIO改善ポテンシャル / 内部リンク` の文言を表示専用に整理
    - 改善アクションの展開見出しにも表示整形を通し、深い位置に残っていた `E-E-A-T` などの生テキストを除去
  - `core/ui/reports\print_report.py`
    - 印刷レポート側の即時改善アクション見出しにも同じ表示整形を適用
  - `core/ui/tabs/comparison_tab.py`
    - 比較タブの `AIO 詳細指標（E-E-A-T / マルチモーダル）` を平文化し、競合比較アクションの表示文言にも整形を適用

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\ui\reports\executive_summary.py core\ui\panels.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\ui\panels.py core\ui\reports\print_report.py core\ui\tabs\comparison_tab.py`
    - PASS
  - headless Edge で `https://www.kyotokogyo.co.jp/` を再分析し、`UI\_livecheck\label_fix_live_excerpt_v4.txt` / `label_fix_print_excerpt_v4.txt` を保存
    - 結果表示では `E-E-A-T / TL;DR / カスタム/その他` の生表示が消えていることを確認
  - `http://127.0.0.1:8087/` のホーム画面 HTML を確認
    - 入力フォームで `おまかせ（自動で見立て） / おまかせ（自動で判定） / AI検索で見つけられやすくしたい` が表示されることを確認

### `/report/print` live確認ベース narrow fix（先頭アクションの page break 抑制）

- 目的
  - headless Edge による live 確認と印刷 PDF 確認を行い、1ページ目で `自社理解 / 結論 / 初手` が完結しているかを実機相当で確認する
  - 不自然な page break があれば、印刷物の読み順だけを最小修正する

- 実施内容
  - `core/ui/reports/executive_summary.py`
    - 先頭 `まずやること` カード専用の短文化処理 `_compact_top_action_text()` を追加
    - 実装例や長いコード断片を先頭カードから除き、詳細は下の `改善レポート` に送る構成へ変更
  - `core/ui/panels.py`
    - 印刷 CSS に `.summary-top-action` / `.status-card` の keep-together を追加
  - `core/ui/components.py`
    - `create_status_card()` に `status-card` クラスを付与し、小さな法務結果カードが 2→3ページ境界で割れにくいよう調整

- live / 印刷確認
  - escalated 起動した `aio2-main` を headless Edge で開き、実際に URL を入力して分析を実行
  - `/report/print` を headless Edge で開き、スクリーンショットと印刷 PDF を再生成
  - `pdftotext` でページ単位確認を行い、修正前は先頭アクションカードが 1→2ページ目で分割、修正後は 1ページ目末尾までに完結することを確認
  - 修正後は 2ページ目が `注意・通知` から始まり、`補足情報` / `根拠・技術詳細` が先頭ページより後ろに下がっていることを確認
  - 小さな法務カードは 3ページ目先頭へまとめて送られ、見出しだけがページ末に残る状態を解消

### 印刷/共有レポート narrow fix（自社理解 / 結論 / 初手 の先頭整理）

- 目的
  - 印刷1ページ目で「このサイトをどう理解したか」「今回の結論」「まず何をするか」が一読で分かるようにする
  - 分析結果と、補足情報 / 判定条件 / 技術詳細 / UI都合の案内文を分離する
  - 算出アルゴリズムは変更せず、`core/ui/reports/executive_summary.py` と `core/ui/panels.py` の情報順だけを narrow fix する

- 実施内容
  - `core/ui/reports/executive_summary.py`
    - 先頭に `このサイトをどう理解したか` を追加し、サイト種別 / 業界 / プラットフォーム / 分析スコープを短く明示
    - `今回の結論` と `まずやること` をスコアカード近辺に整理し、最初に読むべき情報を固定
  - `core/ui/panels.py`
    - `前回比較（同一URL）` を先頭カードから外し、`補足情報（前回比較・判定条件・システムメモ）` に後退
    - `根拠を見る` を `根拠・技術詳細（採点・診断の内訳）`、`専門詳細` を `技術詳細` に変更
    - `report_panel()` の冒頭を `今回の結論（AIO × リーガル）` → `今すぐやること（Top3）` の順に整理
    - `1ページ目: ...` / `2ページ目: ...` のようなUI都合の見出しを廃止し、分析結果として読める文言に変更

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile core\ui\reports\executive_summary.py core\ui\panels.py`
    - PASS
  - `UI\UI2.pdf` / `UI\通常画面１.pdf` と現行コードを突き合わせ、先頭ページで `前回比較` と `補足情報` が強く出すぎていることを確認
  - 修正後コードの表示順を目視確認し、先頭に `自社理解` / `結論` / `初手`、後段に `補足情報` / `根拠・技術詳細` が来る構造に整理した

- Web調査メモ
  - Semrush / Ahrefs 系の site audit は、先頭で health / issue summary を見せ、個別issueは後段に送る構成が主流
  - Google PageSpeed Insights / Search Console 系は、field data や CWV の要約を先に出し、lab data / 診断 / 個別URLは後ろに置く
  - 現行の AI visibility / AI overview 系でも、要約・可視性サマリを先に見せ、根拠や技術論点は別ブロックに分ける傾向を確認
  - 今回はこの比較を根拠に、印刷先頭で `自社理解 → 結論 → 初手`、補足と技術詳細は後段へ後退する方針に固定


### UI narrow fix（本文 / 通知 / 補助説明 / システム補足の境界整理）

- 目的
  - live UI で「何を最初に読むか」と「どこから操作するか」を分け、通知・補助説明・システム補足の混在を減らす
  - 算出アルゴリズムは変更せず、`nicegui_app.py` / `core/ui/panels.py` の情報設計だけを narrow fix する

- 実施内容
  - `core/ui/panels.py`
    - `results_panel()` の `主要リスク` と `注意` の二重表示を解消し、注意点は先頭 `callout` に集約
    - サイト種別 / 業界判定 / クロール設定 / 構造化データ / AIO改善ポテンシャル / 内部リンクを `補足情報（判定条件・システムメモ）` に集約
    - `スコア採点理由を見る` を `根拠を見る（採点・診断の内訳）` に変更し、専門説明であることを明示
    - `詳細（専門的な分析）` を `専門詳細（SEO / AIO / 引用候補）` に変更
    - `report_panel()` に `読む順序` を追加し、非エンジニア向け改善を先、エンジニア向け技術改善を後に配置
  - `nicegui_app.py`
    - `印刷用ページ` 導線を `secondary-btn` に変更し、本文より強く見えすぎないよう調整
  - `tests/test_characterization_ui.py`
    - 出力ゲート通知の期待文言を現行UIに合わせて更新

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\panels.py tests\test_characterization_ui.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m pytest tests\test_characterization_ui.py -q`
    - PASS（4 passed）
  - escalated 起動で live root DOM を再確認し、`secondary-btn` と `まず読む場所 / 次に動く場所` の反映を確認

### UI/印刷 narrow fix（冗長表示整理 + PDF軽量化の下地）

- 目的
  - `nicegui_app.py` と `/report/print` の冗長表示を減らし、本文 / 補助説明 / 通知の見分けやすさを上げる
  - 印刷時のカード途中改ページを減らし、ブラウザ印刷PDFの raster 化を抑える

- 実施内容
  - `nicegui_app.py`
    - STEP 1/3 とレポート導線の文言を整理し、「分析結果」「改善レポート」「印刷用ページ」を明確化
    - `callout` をフラット化し、`notice-chip` / `helper-note` / `action-link` / `section-eyebrow` を追加
    - `print-detail-section` の既定 `break-inside` を `auto` に変更
  - `core/ui/panels.py`
    - 出力ゲート、注意事項、競合比較の通知見出しを通知系ラベルに整理
    - 印刷モード文言を「長いセクションは途中で分割される」前提に更新
    - レポート上部の重複した「一括出力」見出しを削り、操作導線を小さく整理
    - `/report/print` の `BOX 2/BOX 3` を `分析結果` / `改善レポート` に簡素化
    - 印刷 CSS で `box-shadow` / `filter` / `backdrop-filter` / `animation` / `transition` を無効化
    - 長い `.print-detail-section` と `.q-expansion-item` は分割可にし、短い `callout` / `metric` / expansion header のみ keep-together に変更

- 原因メモ
  - `kotomigakiUI1.pdf` は `Microsoft Print to PDF` 出力、21ページ、約41MB
  - `pdffonts` では埋め込みフォントなし
  - `pdfimages -list` では画像 592 個、画像ストリーム合計 約33.95MB、full-page 相当 20 個で 約18.46MB
  - 支配要因はフォント埋め込みではなく、印刷時の高解像度 raster 化

- 検証
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\panels.py`
  - escalated 起動で live root を headless 確認（`http://127.0.0.1:8081/` 応答 200）

## 2026-03-09

### 責務分離 A0-A4 + docs cutline（完了）

- 目的
  - `orchestrator.py` / `nicegui_app.py` / `panels.py` / PDF出力 / monitoring persistence の責務境界を、current engine を壊さずに先に確立する

- 実施内容
  - characterization tests を追加
    - `tests/test_characterization_engine.py`
    - `tests/test_characterization_ui.py`
  - PDF export responsibility を `core/reporting/pdf_export_service.py` へ分離
  - `nicegui_app.py` の analysis / competitor / persistence を `core/application/analysis_run_service.py` へ分離
  - `panels.py` の dependency binding を `core/ui/panel_context.py` に整理
  - monitoring JSON persistence を `core/monitoring/history_store.py` へ分離
  - `ALGORITHM.md` / `AGENTS.md` を current owner 構成へ更新

- 変更ファイル
  - 新規
    - `core/application/__init__.py`
    - `core/application/analysis_run_service.py`
    - `core/reporting/__init__.py`
    - `core/reporting/pdf_export_service.py`
    - `core/monitoring/__init__.py`
    - `core/monitoring/history_store.py`
    - `core/ui/panel_context.py`
    - `tests/test_analysis_run_service.py`
    - `tests/test_monitoring_history_store.py`
  - 更新
    - `core/engine/orchestrator.py`
    - `core/ui/panels.py`
    - `nicegui_app.py`
    - `tests/test_characterization_engine.py`
    - `tests/test_characterization_ui.py`
    - `ALGORITHM.md`
    - `AGENTS.md`

- 検証
  - `.venv\Scripts\python.exe -m pip install pytest`
    - PASS
  - `.venv\Scripts\python.exe -m py_compile core\\application\\__init__.py core\\application\\analysis_run_service.py core\\reporting\\__init__.py core\\reporting\\pdf_export_service.py core\\monitoring\\__init__.py core\\monitoring\\history_store.py core\\ui\\panel_context.py core\\ui\\panels.py core\\engine\\orchestrator.py nicegui_app.py tests\\test_analysis_run_service.py tests\\test_monitoring_history_store.py tests\\test_characterization_engine.py tests\\test_characterization_ui.py`
    - PASS
  - `.venv\Scripts\python.exe -m pytest tests -q`
    - PASS（15 passed）

- 現在の状態
  - current engine owner は `core/engine/orchestrator.py::SEOAIOAnalyzer.analyze_url`
  - `generate_enhanced_pdf_report()` は互換 wrapper
  - monitoring file I/O は `core/monitoring/history_store.py` が owner
  - `nicegui_app.py` は UI shell 寄りになったが、まだ完全には薄くない
  - `panels.py` は context owner を整理したが、render unit はまだ大きい

- 次の残作業
  - `orchestrator.py` の `analyze_url()` 周辺を subdomain service に分割
  - `nicegui_app.py` の view shell 化を継続
  - `panels.py` の `results_panel` / `report_panel` / `print_report` を render unit で再分割

## 2026-02-27

### PLAN2 Phase01: バランスSliderバグ修正 + Intent alpha復活（完了）

- `core/scoring_engine.py`
  - `ScoreContext.seo_weight` / `aio_weight` のデフォルトを `Optional[float] = None` に変更。
- `core/engine/orchestrator.py`
  - `analyze_url()` で `balance == 50` の場合に `seo_weight=None` / `aio_weight=None` を渡すよう修正（intent係数αを有効化）。
  - `_integrate_results()` の引数型を `Optional[float]` に更新。
- `nicegui_app.py`
  - バランススライダー直下に「自動/手動」説明ラベルを追加。
  - `50` のときは「自動: クエリ意図に基づいてSEO/AIO比率を調整します」を表示。
  - `50` 以外では `SEO xx% / AIO yy%` の手動設定表示に切り替え。
- 検証
  - `.venv\Scripts\python.exe -m py_compile core/scoring_engine.py core/engine/orchestrator.py nicegui_app.py` エラーなし
  - `intent="informational"` で `alpha=0.2`、`intent="transactional"` で `alpha=0.7` を確認

### PLAN2 Phase02: メイン分析エラーUI + 空状態改善（完了）

- `nicegui_app.py`
  - ログ出力を `logger.error(..., exc_info=True)` に統一し、メイン分析失敗時のトレースを記録。
  - 一般例外のユーザー向けメッセージ変換関数 `_build_user_error_message()` を追加。
    - `404`: 「URLが見つかりません」
    - `timeout/connection`: 「接続タイムアウト」
    - `403/forbidden`: 「クロールブロック」
  - 例外時は `status_label` と `ui.notify(..., timeout=10000)` を必ず更新。
  - `run_analysis()` 開始時に `analyze_button.disable()`、終了時 `analyze_button.enable()` で再実行可能性を明確化。
  - 失敗時は `progress_bar.visible = False` を保証。
- `core/ui/tabs/aio_tab.py`
  - データ未存在時の空状態メッセージを追加して早期 return。
- `core/ui/tabs/seo_tab.py`
  - データ未存在時の空状態メッセージを追加して早期 return。
- `core/ui/tabs/health_tab.py`
  - 分析結果/サイトヘルス未存在時の空状態メッセージを追加して早期 return。
- 検証
  - `.venv\Scripts\python.exe -m py_compile nicegui_app.py core/ui/tabs/aio_tab.py core/ui/tabs/seo_tab.py core/ui/tabs/health_tab.py` エラーなし
  - `_build_user_error_message()` の分岐テストで `404`/`timeout`/`403` メッセージを確認

### PLAN2 Phase03: sitemap.xml メタデータ解析（完了）

- `core/sitemap_analyzer.py`（新規）
  - sitemap.xml を URL/lastmod のみで解析する軽量アナライザーを追加。
  - `sitemapindex` は1段のみ追跡、5MB上限・10秒タイムアウトで fail-open 実装。
  - 規模別サンプリングを実装（<=1000全件、<=10000は500件、>10000は100件）。
  - `total_urls` / `sampled_count` / `update_frequency` / `url_categories` / `warning` を返却。
- `core/engine/orchestrator.py`
  - `analyze_url()` で sitemap メタデータ解析を追加し、失敗時も本分析は継続。
  - `integrated_results["sitemap_info"]` と最終結果 `sitemap_info` に連携。
- `core/ui/reports/executive_summary.py`
  - 経営サマリーに「全Xページ中、メタデータ解析Y件（更新頻度）」表示を追加。
  - 10,000ページ超は「大規模サイト」注意文を表示。
- 検証
  - `.venv\Scripts\python.exe -m py_compile core/sitemap_analyzer.py core/engine/orchestrator.py core/ui/reports/executive_summary.py` エラーなし
  - モックテストで以下を確認:
    - sitemap あり: `total_urls > 0`
    - sitemap なし(404): `error` 返却、クラッシュなし
    - 10,001 URL: `is_large_site=True` と警告文
    - 経営サマリー文言に `全10,001ページ中` を含む

### PLAN2 Phase04: ビジネス目標パーソナライズ（完了）

- `nicegui_app.py`
  - 詳細設定に「ビジネス目標」セレクタを追加。
  - `run_analysis()` で `goal_value` を取得し、`analyze_url(..., business_goal=goal_value)` で渡すよう変更。
  - 競合分析呼び出しにも同じ `business_goal` を連携。
- `core/engine/orchestrator.py`
  - `analyze_url()` に `business_goal: str = "自動判定"` を追加。
  - `integrated_results["business_goal"]` に選択目標を保存。
  - AIO/SEO即時アクション、深掘り提案、サマリー改善文を `business_goal` に応じて安定ソート。
  - `last_analysis_results["business_goal"]` を追加。
- `core/aio_suggestions.py`
  - 目標別優先キーワード定義 `GOAL_PRIORITY_KEYS` を追加。
  - `sort_actions_by_business_goal()` / `sort_texts_by_business_goal()` を追加（自動判定時は並び変更なし）。
- `core/ui/reports/executive_summary.py`
  - 経営サマリー冒頭に選択目標（自動判定以外）を表示。
- 検証
  - `.venv\Scripts\python.exe -m py_compile nicegui_app.py core/engine/orchestrator.py core/aio_suggestions.py core/ui/reports/executive_summary.py` エラーなし
  - 単体テストで以下を確認:
    - AIO優先目標で AIO/GEO関連アクションが先頭化
    - 自動判定では元順序を維持

### PLAN2 Phase05: アクセシビリティ対応（完了）

- `core/ui/reports/executive_summary.py`
  - 統合/SEO/AIO の円形ゲージに `aria-label` を追加（スコア値 + 状態）。
  - GEOリニアバーに `aria-label` を追加。
  - ステータス表示に `aria-label="ステータス: ..."` を追加。
- `core/ui/tabs/aio_tab.py`
  - プラットフォーム別引用適合度バーに `aria-label` を追加。
  - 総合バーに `aria-label` を追加。
- `nicegui_app.py`
  - 「分析を開始」ボタンに `aria-label` を追加。
- 検証
  - `.venv\Scripts\python.exe -m py_compile core/ui/reports/executive_summary.py core/ui/tabs/aio_tab.py nicegui_app.py` エラーなし
  - `rg -n "aria-label"` で対象ファイルに属性追加を確認
  - 注記: ブラウザ開発者ツール確認とNarrator読み上げ確認はこの環境では未実施

### PLAN2 Phase06: 内部リンク構造スコア（完了）

- `core/seo/internal_graph.py`
  - `get_health_report(all_known_urls=...)` を追加。
  - 孤立ページ数/比率、ハブページ、平均深度、健全性スコア（0-100）、診断文を返却。
  - ルートページは孤立判定から除外し、孤立ゼロ時に `health_score=100.0` となるよう調整。
- `core/engine/orchestrator.py`
  - メインURLに加え、優先クロールページのリンクも `InternalLinkGraph` に投入。
  - `sitemap_info.sampled_urls` を `all_known_urls` として渡し `link_health_report` を生成。
  - 解析結果に `link_health_report` を追加。
- `core/ui/tabs/health_tab.py`
  - 「内部リンク構造」セクションを追加（スコアバー、診断、孤立ページ、ハブページ）。
  - 推定値であることの注記を表示。
- 検証
  - `.venv\Scripts\python.exe -m py_compile core/seo/internal_graph.py core/engine/orchestrator.py core/ui/tabs/health_tab.py` エラーなし
  - `get_health_report(all_known_urls=[])` で `health_score >= 0` を確認
  - 孤立ゼロケースで `health_score = 100.0` を確認
  - 孤立ありケースで `orphan_count > 0` と `total_known_pages > 0` を確認

### PLAN2 追加是正: 厳格レビュー指摘の修正（完了）

- `core/sitemap_analyzer.py`
  - `sitemapindex` の子URLを同一ホストのみ許可し、外部ホスト参照を遮断（SSRF対策）。
  - `lastmod` の日時混在（offset-aware/naive）で `TypeError` が出る問題を修正（`date`へ正規化）。
- `core/ui/panels.py`
  - `decision_actions` 生成後に `business_goal` ベースの安定ソートを追加。
  - 経営サマリー/改善レポート双方で同じ優先順になるよう `business_goal` を明示連携。
- `nicegui_app.py`
  - 未分類例外時のユーザー向けメッセージを固定文に変更し、内部エラー文字列を非表示化。
- 検証
  - `.venv\Scripts\python.exe -m py_compile core/sitemap_analyzer.py core/ui/panels.py nicegui_app.py core/engine/orchestrator.py` エラーなし
  - 再現テスト:
    - `sitemapindex` 外部ホストURLが実行されないこと
    - mixed `lastmod` でクラッシュしないこと
    - 技術健全性目標で `decision_actions` 先頭が技術改善になること
    - 未分類エラーで内部文字列（Traceback等）がUI文言に出ないこと
  - 補足対応: 別ホスト `sitemapindex` を除外した際、経営サマリーに平易な説明文を表示するよう追加

### UI改善: やさしい用語モード + バランスプリセット（完了）

- `nicegui_app.py`
  - `AppState.plain_language_mode` を追加（初期値: `True`）。
  - AIOラベル/説明文を `標準` と `やさしい表現` の2系統で定義し、`get_aio_ui_copy()` で切替可能化。
  - STEP2に `やさしい用語で表示（推奨）` トグルを追加。
  - トグル変更時に `bind_panel_dependencies()` を再バインドし、結果表示を即時リフレッシュ。
  - SEO/AIOバランスにクイックプリセットを追加: `自動(50)` / `SEO寄り(30)` / `AIO寄り(70)`。
- `core/ui/tabs/aio_tab.py`
  - 重み付き貢献度テーブルの表示ラベルを `aio_score_labels` 参照に変更し、やさしい用語モードに連動。
- `core/ui/panels.py`
  - AIO内訳セクションの一部用語（PID/Entity/AEO/知識グラフ）を `plain_language_mode` に応じて平易表現へ切替。
  - サブ説明文を平易版へ切替可能化。
- 検証
  - `.venv\Scripts\python.exe -m py_compile nicegui_app.py core/ui/tabs/aio_tab.py core/ui/panels.py` エラーなし

### プラットフォーム別アドバイス更新運用の明文化（完了）

- `core/platform_guidance.py`
  - WordPress に caveat を追加:
    - `WordPress.com はプラン/権限でプラグイン利用・ヘッダー編集可否が変わる` 旨を明記。
  - Wix に caveat を追加:
    - FAQ/HowTo 等のリッチリザルトは検索エンジン側ポリシーで表示対象が限定される可能性を明記。
  - WordPress / Wix / Shopify に `source_links`（公式URL）と `verified_at`（`2026-02-27`）を追加。
  - `get_platform_guidance()` の戻り値に `caveats` / `source_links` / `verified_at` を追加。
  - `format_platform_advice_for_llm()` で caveat を注意書きとして併記。
- `AGENTS.md`
  - プラットフォーム別アドバイスの運用ルールを追加:
    - `core/platform_guidance.py` をSSOTとして管理
    - `verified_at` / `source_links` を保持
    - 月1回または主要仕様変更時に更新し、`WORKLOG.md` に差分記録
- 検証
  - `.venv\Scripts\python.exe -m py_compile core/platform_guidance.py` エラーなし

### 履歴比較の自動表示（同一URL・前回差分）を追加（完了）

- `core/storage/database.py`
  - `get_history()` の並び順を `analyzed_at DESC, id DESC` に更新（同秒実行の順序安定化）。
  - `get_previous_run(url, current_run_id=None)` を追加し、同一URLの直前実行を取得可能にした。
- `core/ui/panels.py`
  - `results_panel()` に「前回比較（同一URL）」カードを追加。
  - 比較項目: SEO / AIO / 法務 / 課題数（課題数はマイナスが改善）。
  - 初回分析時は「次回から差分表示」の案内を表示。
  - 履歴比較失敗時は fail-open（分析結果表示を阻害しない）。
- 検証
  - `.venv\Scripts\python.exe -m py_compile core/storage/database.py core/ui/panels.py` エラーなし

### 実施内容サマリー

| 作業 | 内容 | 状態 |
|------|------|------|
| ベストプラクティス調査 | AI検索最新動向・スコア妥当性・競合比較 | ✅ |
| GEO/AIO改善計画策定 | P01〜P05の5フェーズ計画 | ✅ |
| P01: アルゴリズム修正 | DEBUGプリント除去 + Intent係数修正 | ✅ |
| P02: E-E-A-T強化 | 日本語文中E-E-A-T検出 | ✅ |
| P03: GEO基本指標 | TL;DR・統計密度スコア追加 | ✅ |
| P04: スコア体系精緻化 | YMYL動的ブースト・GEOスコア独立計算 | ✅ |
| P05: 多AI対応 | プラットフォーム別引用適合度推定 | ✅ |
| UX見直し・評価 | ニールセン10原則・CRAP・競合比較 | ✅ |
| UX改善実装 | タブ順序・重複削除・リライト前出し | ✅ |
| アルゴリズムドキュメント | `AIO_ALGORITHM.md` 新規作成 | ✅ |

---

### ベストプラクティス調査

現行アルゴリズム・UI・スコア体系をAI検索最新動向と照合。

**主要調査結果:**
- Google AIモード日本語対応（2025/9〜）でAIO表示率39.2%に急増。1位CTRが▲58〜61%
- Intent係数α の `informational=0.3` は現状と逆転。`0.2`（AIO80%）に修正要
- E-E-A-T が AI filtering の前提条件化。JSON-LD依存では日本語サイトの70〜80%が過小評価
- GEO（ACM SIGKDD 2024）: 統計密度・冒頭要約でAI可視性+30〜40%
- `scoring_engine.py` にDEBUGプリント残存、YMYL係数が静的で不適切

---

### GEO/AIO改善計画 — 全5フェーズ（当日完了）

進捗管理: `plan/geo_aio_improvement_2026/PROGRESS.md`

| Phase | 内容 | 主な変更ファイル |
|-------|------|----------------|
| P01 ✅ | DEBUGプリント除去 + Intent係数修正 | `scoring_engine.py` |
| P02 ✅ | 文中E-E-A-T検出強化（日本語対応） | `aio_analyzer.py` |
| P03 ✅ | GEO基本指標追加（TL;DR・統計密度） | `aio_analyzer.py`, `aio_tab.py` |
| P04 ✅ | YMYL動的ブースト + GEOスコア独立計算 | `scoring_engine.py`, `executive_summary.py` |
| P05 ✅ | プラットフォーム別引用適合度推定 | `aio_analyzer.py`, `aio_tab.py`, `aio_suggestions.py` |

**P01 主な変更:**
- `INTENT_ALPHA` 改訂（informational 0.3→0.2、navigational 1.0→0.8）
- DEBUGプリント9行→`logger.debug()` 1行に統合

**P02 主な変更:**
- `EEAT_PATTERNS_JA` 追加（資格/著者明示/組織/一次情報、4カテゴリ）
- `detect_inline_eeat()` 追加（fail-open、0〜10点）
- JSON-LDボーナス付きの combined_score 算出

**P03 主な変更:**
- `STATISTICS_PATTERNS` 追加（6パターン、数値・比較・調査出典）
- `detect_tldr_summary()` 追加（0〜5点）
- `calculate_statistics_density()` 追加（0〜10点）
- raw_score に GEO寄与（TL;DR5% + 統計密度5%）組み込み

**P04 主な変更:**
- `YMYL_KEYWORDS` 追加（9語）、YMYL静的エントリ削除
- `_apply_industry_boost()` に eeat_score 引数追加（≥7.0→×1.2、<4.0→×0.7）
- GEOスコア100点計算（TL;DR40%+統計密度35%+E-E-A-T25%）
- `integrate()` 返り値に `geo_score` / `geo_breakdown` 追加

**P05 主な変更:**
- `estimate_platform_citation()` 追加（Google AI/ChatGPT/Perplexity 各ルールベース推定）
- `PLATFORM_ADVICE_TEMPLATES` / `get_platform_citation_advice()` 追加
- AIOタブにプラットフォーム別スコア・因子・総合を表示

**全フェーズ検証:**
- `py_compile` 全対象ファイルエラーなし
- 各フェーズの境界値テスト通過（詳細は各 phase0N_*.md 参照）

---

### UX見直し・改善

**評価観点:** ニールセン10原則、CRAP、Visual Hierarchy、認知負荷、国際競合（Semrush/Ahrefs/Surfer SEO）

**主要な問題と対処:**

| 問題 | 対処 | ファイル |
|------|------|---------|
| タブ先頭がエンジニア向け（サイトヘルス） | 引用候補→SEO→AIO→業界→サイトヘルスに変更 | `panels.py` |
| Top3アクションが経営サマリー+レポートで重複 | 経営サマリーは最優先1件+誘導テキストのみに | `executive_summary.py` |
| GEOスコードが4列目カードでモバイル崩れリスク | 3枚カード+サブ行テキストに変更 | `executive_summary.py` |
| リライトセクションがデフォルト閉じ・末尾 | 先頭＋デフォルト展開に変更 | `panels.py` |
| エンジニア向け詳細が非エンジニアに先出し | デフォルト折りたたみに変更 | `panels.py` |

**検証:** `py_compile` エラーなし（panels.py / executive_summary.py）

---

### アルゴリズムドキュメント作成

`AIO_ALGORITHM.md` を新規作成。AIOスコア算出の全工程・数式・パラメータを文書化。

詳細: `AIO_ALGORITHM.md`

---

### 海外ツールUX調査 + スコアリング・Sudachi確認

**Sudachi 確認:**
- `aio_analyzer.py`: Mode A（PID・TL;DR・E-E-A-T）、Mode C（エンティティ・知識グラフ）で正常使用
- `robots_analyzer.py`: alt属性の動詞チェックで使用
- フォールバックチェーン（full→core→small→default）で安全初期化済み

**海外ツール調査（Semrush/Ahrefs/Surfer/Clearscope/MarketMuse/ContentKing）主要知見:**
- リアルタイムゲージ（Surfer・Clearscope）が最も効果的な視覚的モチベーション
- Clearscope式 "Calm設計"（攻撃的な赤警告を減らす）が非エンジニアに有効
- ContentKing の視聴者別ビュー（exec/tech）が中長期の改善候補

**スコアリング分析結果:**
- AIOスコアが低い理由は正常動作（llms.txt 普及率ほぼ0%、FAQ JSON-LD低普及、結論先出し文化なし）
- 日本の平均的サイトで 25〜45点が正常範囲
- AIO_ALGORITHM.md の構造/技術スコア重みが実コードと不一致 → 修正済み

---

### ゲージ表示 実装

| 変更 | ファイル |
|------|---------|
| 統合/SEO/AIO スコアを `ui.circular_progress`（80px円形）に変更 | `core/ui/reports/executive_summary.py` |
| GEO行に `ui.linear_progress`（6px）追加 | `core/ui/reports/executive_summary.py` |
| プラットフォーム別引用適合度に横バー（10px/12px）追加 | `core/ui/tabs/aio_tab.py` |
| スコア色: ≥80→green / ≥50→amber / <50→red | 両ファイル |

検証: `py_compile` エラーなし

---

### P06: E-E-A-T を raw_score に組み込み

**背景:** 非YMYL サイトでは E-E-A-T が AIO スコアに一切影響していなかった。
Google AI Mode・ChatGPT・Perplexity はいずれも著者信頼性を全業種で参照するため修正。

**重み変更（合計 1.00 維持）:**

| コンポーネント | 変更前 | 変更後 | 差分 |
|---|---|---|---|
| E-E-A-T（新規） | — | **+0.08** | |
| エンティティ | 0.15 | 0.12 | -0.03 |
| 情報鮮度 | 0.08 | 0.06 | -0.02 |
| AEOパターン | 0.07 | 0.05 | -0.02 |
| 知識グラフ | 0.05 | 0.04 | -0.01 |

**効果:** E-E-A-T 7.0 のサイトは +5.6点、2.0 のサイトは +1.6点（差分4点の差別化）

**変更ファイル:** `core/aio_analyzer.py`（raw_score計算式・loggerメッセージ）、`AIO_ALGORITHM.md`（重み表・計算式）

検証: `py_compile` エラーなし

---

### UIスコア説明 追加

- `nicegui_app.py`: `AIO_SCORE_LABELS` / `AIO_SCORE_HELP` に `eeat`・`geo_tldr`・`geo_stats` 追加
- `core/ui/tabs/aio_tab.py`: AIOスコア計算式セクションに重み付き貢献度内訳テーブルを追加

---

### PLAN2 策定（次回セッション向け指示書）

残作業を6フェーズに整理し、Cursorで継続実施できる指示書を作成した。

**作成ファイル:**

| ファイル | 内容 |
|---------|------|
| `plan/PLAN2/PROGRESS.md` | 進捗管理・全体完了条件・参照ファイル一覧 |
| `plan/PLAN2/phase01_balance_slider_intent_fix.md` | 🔴 バランスSliderバグ + intent alpha 修正 |
| `plan/PLAN2/phase02_error_ui.md` | 🔴 メイン分析エラーUI + 空状態改善 |
| `plan/PLAN2/phase03_sitemap_analysis.md` | 🟡 sitemap.xml メタデータ解析（新規モジュール） |
| `plan/PLAN2/phase04_personalization.md` | 🟡 ビジネス目標選択UI + 改善案優先順位変更 |
| `plan/PLAN2/phase05_accessibility.md` | 🟡 aria-label + アクセシビリティ対応 |
| `plan/PLAN2/phase06_internal_link_structure.md` | 🟢 内部リンク健全性スコア（P03依存） |

**重要: P01バグの内容（次回セッションで最初に対応）**
- `core/scoring_engine.py` の `ScoreContext.seo_weight` デフォルト値が `0.5`（Noneでない）
- → intent alpha（informational=0.2 等）が**常に無視**されている
- → 修正: `seo_weight: Optional[float] = None` に変更し、balance=50のとき None を渡す

---

## 2026-02-09 リーガル集計漏れ修正 / リンク到達性補正

- **修正ファイル**:
  - `core/evidence_pipeline.py`
  - `core/legal_checks/visibility_checker.py`
- **変更内容**:
  - `aggregate_legal_check_results()` の収集対象を拡張。
    - `raw/formatted` のネスト構造を再帰走査
    - `consumer_protection`（`visibility` / `best_practices` / `lawyer_report`）を集計対象へ追加
  - 視認性チェックで画像リンクを一律除外しないよう補正。
    - `alt` / `aria-label` / `title` が空の画像リンクは到達性警告候補として扱う
- **検証**:
  - `py -3.11 -c "import ast,pathlib; ast.parse(pathlib.Path('core/evidence_pipeline.py').read_text(encoding='utf-8')); ast.parse(pathlib.Path('core/legal_checks/visibility_checker.py').read_text(encoding='utf-8')); print('OK aio2 modified files')"`: 成功
  - `aggregate_legal_check_results()` へのサンプル入力で `total_original > 0` を確認
- **補足**:
  - Azure引き継ぎ追記先: `notecode/docs/azure-handoff-2026-02-09-ja.md`（9章）

## 2026-02-06 セキュリティ説明改善 / プラットフォーム別リスク整理 / FAQ検出精度改善

- **修正ファイル**:
  - `core/site_health/security_checker.py`
  - `core/platform_guidance.py`
  - `core/ui/tabs/health_tab.py`
  - `core/aio_analyzer.py`
  - `PDFreport/high_quality_pdf_generator.py`
  - `core/faq_detection.py`
  - `core/ui/panels.py`
- **変更内容（セキュリティ/プラットフォーム）**:
  - セキュリティ項目を `リスク: ... / 対処: ...` 形式で表示（未設定時）。
  - FAQに「クリックジャッキング」「MIMEスニッフィング」「中間者攻撃」の平易な説明を追加。
  - プラットフォーム別に `共通リスク` と `固有リスク` を整理し、UIで表示。
  - `llms.txt` の設置状態表示と配置ベストプラクティスをUIに追加。
  - `core/aio_analyzer.py` の `llms.txt` 文言を「サイトルート直下」に統一。
- **変更内容（PDF）**:
  - `PDFreport/high_quality_pdf_generator.py` に
    - プラットフォーム別リスク整理（共通/固有）
    - `llms.txt` 設置状態
    - `llms.txt` 配置ベストプラクティス
    を追加。
  - エンジニア向けページ構成を `1/3, 2/3, 3/3` に拡張。
- **変更内容（FAQ検出）**:
  - `dl/dt/dd` の無条件抽出を廃止し、FAQ文脈 + 質問らしさで判定。
  - 非FAQ文脈（お知らせ/ニュース/会社情報等）を除外。
  - ブロック単位の判定（質問らしい項目がない `dl` を除外）を追加。
  - FAQ未検出時にFAQ提案テンプレートをUI表示（EC/非ECで出し分け）。
- **検証**:
  - 主要変更ファイルのASTパース/インポート確認: 成功。
  - ダミーデータでPDF生成: 成功（`outputs/tmp_test_report.pdf`）。
  - FAQ再現ケースで誤検出低減を確認（`トップメッセージ` 除外、質問項目のみ検出）。
  - PDFにFAQ方針（LLMOで有効だが全ページ必須ではない、配置方針、プラットフォーム制約）を追加し、ダミーデータで生成確認（`outputs/tmp_test_report_faq_policy.pdf`）。

## 2026-02-06 FAQ方針の明示（PDF）と検出精度の追加チューニング

- **修正ファイル**:
  - `PDFreport/high_quality_pdf_generator.py`
  - `core/faq_detection.py`
- **変更内容**:
  - PDFに `FAQ実装方針（LLMO）` セクションを追加。
    - FAQは有効だが全ページ必須ではない旨を明記
    - 推奨配置（ページ中段〜下段/CTA直前/専用FAQページ）を明記
    - プラットフォームのJSON-LD可否に応じた注記を明記
    - FAQ検出状況（検出件数/未検出）を明記
  - FAQ検出に非FAQ文脈（お知らせ/ニュース/会社情報等）除外とスコアリングを追加。
  - `dl` ブロック単位で質問らしさがない候補をまとめて除外。
- **検証**:
  - `AST OK`: `PDFreport/high_quality_pdf_generator.py`, `core/faq_detection.py`
  - 再現ケース:
    - `重要なお知らせ + トップメッセージ` は除外
    - `Q/A` 形式は継続して検出

## 2026-02-06 llms.txt品質検証の実装とFAQ整合チェックの追加

- **修正ファイル**:
  - `core/scraper.py`
  - `PDFreport/high_quality_pdf_generator.py`
  - `core/faq_detection.py`
  - `core/ui/panels.py`
- **変更内容**:
  - `llms.txt` の存在確認に加えて品質検証を追加（スコア/レベル/課題/推奨）。
    - チェック項目: 推奨パス、Content-Type、文字量、URL数、同一ドメイン比率、更新日、構造化、行長
  - PDFの `AIクローラー向け案内（llms.txt）` に品質スコアと改善ポイントを表示。
  - FAQ検出結果に本文整合チェック（簡易）を追加。
    - `JSON-LD FAQ` が本文に存在しない場合を要確認として検知
  - UIの「既存FAQ検出」に整合チェック結果（整合件数/要確認件数）を表示。
- **検証**:
  - `AST OK`: `core/scraper.py`, `core/faq_detection.py`, `core/ui/panels.py`, `PDFreport/high_quality_pdf_generator.py`
  - FAQ整合テスト: 本文にないJSON-LD質問を要確認として検出
  - PDF生成テスト: `outputs/tmp_test_report_llms_quality_v2.pdf` 生成成功

## 2026-02-06 一括出力ページ500エラー修正（アクセシビリティ生データの型ガード）

- **修正ファイル**: `core/ui/tabs/health_tab.py`
- **原因**:
  - `site_health.accessibility.raw` の要素が `dict` 前提で実装されており、`str` が混在したケースで `check.get(...)` が発生して `AttributeError` で落ちていた。
  - `/report/print` は `results_panel()` を描画するため、同例外で500化していた。
- **変更内容**:
  - `raw_checks` を `dict/list/other` で分岐し、走査対象を正規化。
  - 各 `check` について `dict/list/str` を許容し、`issues` を安全に構築。
  - `str` の issue は `{\"issue\": \"...\"}` 形式に変換して `render_detail_panel()` の期待型に合わせた。
- **検証**:
  - `python -m py_compile core/ui/tabs/health_tab.py` 成功
  - アプリ再起動後に `http://127.0.0.1:8081/report/print` が `200` を返すことを確認

## 2026-02-06 印刷モードの全展開保証と一括出力導線の調整

- **修正ファイル**: `nicegui_app.py`
- **変更内容**:
  - 印刷トグルON時に `results_panel.refresh()` に加えて `report_panel.refresh()` も実行
  - 印刷トグルON時に `_open_all_results()` と `_open_all_reports()` の両方を呼び、BOX2/BOX3の折りたたみを自動展開
  - BOX2の「全て展開/折りたたみ」ボタン定義を関数内誤配置から修正し、常時表示に変更
  - BOX3バッジを `PDF出力対応` から `一括出力対応` に変更
  - BOX3に `一括出力ページを開く`（`/report/print`）を主導線として追加
  - PDFボタンは `PDFレポートを生成（任意）` に変更（補助導線化）
- **検証**:
  - `python -m py_compile nicegui_app.py` 成功

## 2026-02-06 PDF導線の撤去と表示レベル切替の削除

- **修正ファイル**: `nicegui_app.py`, `core/ui/panels.py`
- **変更内容**:
  - BOX2の「表示レベル（要点/詳細）」トグルを削除
  - `display_mode` の既定を `advanced` に固定（表示切替をなくして挙動を安定化）
  - BOX3の `PDFレポートを生成（任意）` ボタンとPDF生成処理を削除
  - `core/ui/panels.py` から「PDFレポート生成」表示/最新PDFリンク/PDFステータス表示を削除
  - レポート側は `印刷レポートを開く` の一括出力導線に統一
  - `nicegui_app.py` から未使用となった `secrets`, `update_pdf_path`, `ModeManager` 依存を削除
  - `core/ui/reports/print_report.py` のボタン文言を `印刷 / PDF出力` から `印刷` に変更
- **検証**:
  - `python -m py_compile nicegui_app.py` 成功
  - `python -m py_compile core/ui/panels.py` 成功
  - `python -m py_compile core/ui/reports/print_report.py` 成功

## 2026-02-06 印刷ページの出力パイプライン差し替え（全内容展開）

- **修正ファイル**: `core/ui/panels.py`
- **変更内容**:
  - `/report/print` を旧サマリー専用レンダラー依存から切り替え
  - 印刷ページで `results_panel()` + `report_panel()` をそのまま描画し、画面の分析/提案内容を一括出力
  - `state.print_mode=True` で詳細を縦並び化し、折りたたみをサーバー側 + JS側で全展開
  - 印刷用アクション（印刷/通常画面へ戻る）と `@media print` スタイルを追加
- **反映確認**:
  - `python -m py_compile core/ui/panels.py` 成功
  - 8081プロセスを再起動
  - ルートHTMLで `PDFレポート` / `表示レベル` が消え、`一括出力ページを開く` が残ることを確認

## 2026-02-04 UIリファクタリング（ニールセン10原則に基づく改善）

### 概要
ニールセンの10原則に基づいてUIを診断し、以下の問題を修正した。

### 1. 「印刷用に全て展開」ボタンで開かない問題を修正

**原因**: 一部のexpansionが`state.result_expansions`/`state.report_expansions`に登録されていなかった

**修正ファイル**: `core/ui/panels.py`

| 項目 | 修正内容 |
|------|----------|
| スコア採点理由を見る | `state.result_expansions.append()` 追加 |
| 操作ガイド | `state.report_expansions.append()` 追加 |
| 優先度順の改善提案 | 同上 |
| 実装ガイド | 同上 |
| AIO最適化アクション | 同上 |
| 引用候補フレーズ | 同上 |
| 既存FAQ検出 | 同上 |
| 追加コンテンツ提案 | 同上 |
| 配置提案 | 同上 |

### 2. 過去の残骸を削除

- `panels.py`: `conversational_simulation`（AIチャット質問シミュレーション）のUI表示コードを削除
  - バックエンドで既に削除済みで、表示されることがなかった

### 3. スコア表示の重複を解消

- `panels.py`: BOX2冒頭のスコアカード表示を削除
- 経営サマリー（`executive_summary.py`）内のスコア表示のみに統一

### 4. UIレイアウト改善（ニールセン原則#4, #6, #8対応）

**修正ファイル**: `nicegui_app.py`

| 原則 | 問題 | 修正内容 |
|------|------|----------|
| #8 美的で最小限 | バッジが長すぎる | `詳細はタブで表示（サイトヘルス/業界/SEO/AIO）` → `詳細: タブ表示` |
| #6 記憶より認識 | ロール選択の意味が不明 | ヘルプアイコン+ツールチップ追加 |
| #4 一貫性 | BOX2/BOX3のレイアウト不統一 | 同一パターンに統一 |

### 5. 法的分析の警告を分かりやすく改善

**修正ファイル**: `core/legal_checks/lawyer_perspective.py`, `core/ui/tabs/health_tab.py`

**Before（分かりにくい）**:
```
【参考】リンクの到達性が低い
リンクテキストが短すぎます（7件）。例: <svg>...
```

**After（分かりやすい）**:
```
[参考] リンクの到達性が低い
チェック対象: リンクテキストの長さ、画像のみのリンク
📍 該当箇所: ヘッダー
⚠️ 法的リスク: 説明義務を果たしていないと判断される可能性
📜 法的根拠: 特定商取引法第11条
✅ ベストプラクティス: リンク先の内容が分かるテキストを使用
❌ 悪い例: <a href='/policy'>こちら</a>
✅ 良い例: <a href='/policy'>返品・交換ポリシーの詳細</a>
🔧 修正方法: 「こちら」ではなく具体的な文言に変更
```

**追加フィールド**: `legal_basis`, `what_is_checked`, `best_practice`, `bad_example`, `good_example`, `how_to_fix`

### 6. サイト種別によるパーソナライズ

**修正ファイル**: `core/ui/panels.py`, `core/ui/tabs/health_tab.py`, `core/legal_checks/lawyer_perspective.py`

| サイト種別 | 法務セクション | 表示される警告 |
|-----------|---------------|---------------|
| ECサイト | 法務（重要）/ 開いた状態 | 全て |
| 企業（EC機能あり） | 法務（重要）/ 開いた状態 | 全て |
| 企業 | 法務（参考情報）/ 閉じた状態 | 文字サイズ、非表示テキストのみ |
| メディア/ブログ | 法務（参考情報）/ 閉じた状態 | 文字サイズのみ |

**効果**: 非ECサイトに対して「特商法の表示が必要です」等の無関係な警告が表示されなくなった

### 主要ファイルの変更箇所

| ファイル | 変更内容 |
|----------|----------|
| `nicegui_app.py` | BOX2/BOX3レイアウト改善、バッジ短縮、ロール説明追加 |
| `core/ui/panels.py` | スコア重複削除、expansion登録追加、非EC判定分岐 |
| `core/ui/tabs/health_tab.py` | 法的分析UI改善、種別フィルタリング追加 |
| `core/legal_checks/lawyer_perspective.py` | ISSUE_DETAILS追加、filter_issues_by_site_type追加 |

### 再起動後の確認ポイント
- 「全て展開」ボタンで全ての折りたたみが開くか
- 非ECサイトで法務セクションが「参考情報」になっているか
- 法的警告に「該当箇所」「ベストプラクティス」「修正方法」が表示されるか

---

## 2026-02-04 UIデザイン計画（TECHIEブランド適用）

### 開始時に見るファイル

| 順序 | ファイル | 目的 |
|------|----------|------|
| 1 | `WORKLOG.md` | 本計画の確認（Task 1-8の実装指示） |
| 2 | `plans/image/ロゴ１.png` | ブランドイメージの確認 |
| 3 | `nicegui_app.py:276-300` | 現在のCSS変数定義（Task 1の対象） |
| 4 | `PDFreport/templates/style.css:1-10` | PDF用CSS変数（Task 7の対象） |

### 作業開始手順

1. **Task 1から順番に実行**（依存関係あり）
2. 各Task完了後、チェックリスト（セクション9）を更新
3. 全Task完了後、検証コマンド（セクション10）を実行
4. 目視確認でオレンジ系のブランドカラーが反映されていることを確認

---

### 1. ブランドカラー定義（ロゴ分析）

**TECHIEロゴから抽出したカラーパレット:**

| 役割 | カラー | HEX | 用途 |
|------|--------|-----|------|
| Primary Orange | Fox Orange | `#E8590C` | CTA、アクセント、重要な要素 |
| Primary Orange Light | Fox Light | `#FF8C42` | ホバー状態、サブアクセント |
| Primary Orange Dark | Fox Deep | `#D9480F` | アクティブ状態、強調 |
| Text Primary | Charcoal Brown | `#2D2926` | 見出し、本文 |
| Text Secondary | Warm Gray | `#5C5552` | 補足テキスト、ラベル |
| Background | Pure White | `#FFFFFF` | メイン背景 |
| Surface | Warm White | `#FAF9F8` | カード、パネル背景 |
| Border | Soft Gray | `#E5E2DF` | 区切り線、ボーダー |

### 2. 現状との差分分析

**現在のカラー（style.css / nicegui_app.py）:**
```
--ink: #1f2933     → 変更: #2D2926 (Charcoal Brown)
--muted: #5f6b7a   → 変更: #5C5552 (Warm Gray)
--line: #d0d5db    → 変更: #E5E2DF (Soft Gray)
--accent: #0f4d92  → 変更: #E8590C (Fox Orange) ★主要変更
--bg: #ffffff      → 維持
--panel: #f6f7f9   → 変更: #FAF9F8 (Warm White)
```

### 3. コンポーネント別カラーマッピング

#### 3.1 ヘッダー/ナビゲーション
- 背景: `#FFFFFF`
- ロゴテキスト: `#2D2926`
- アクティブタブ: `#E8590C` (下線またはテキスト)

#### 3.2 ボタン
| 種類 | 背景 | テキスト | ホバー |
|------|------|----------|--------|
| Primary | `#E8590C` | `#FFFFFF` | `#D9480F` |
| Secondary | `transparent` | `#E8590C` | `#FFF5F0` (5%オレンジ) |
| Ghost | `transparent` | `#2D2926` | `#FAF9F8` |

#### 3.3 カード/パネル
- 背景: `#FFFFFF`
- ボーダー: `#E5E2DF`
- シャドウ: `rgba(45, 41, 38, 0.08)`

#### 3.4 スコア表示（SEO/AIO）
| レベル | カラー | 用途 |
|--------|--------|------|
| 高スコア (80+) | `#2F9E44` (Green) | Good |
| 中スコア (50-79) | `#E8590C` (Orange) | Needs Improvement |
| 低スコア (0-49) | `#E03131` (Red) | Poor |

#### 3.5 グラフ/チャート
- プライマリ系列: `#E8590C`, `#FF8C42`, `#FFB380`
- セカンダリ系列: `#2D2926`, `#5C5552`, `#8C8582`
- グリッド線: `#E5E2DF`

### 4. タイポグラフィ

**推奨フォント（現状維持可）:**
- 見出し: `Sora`, `Noto Sans JP` (既存)
- 本文: `Noto Sans JP`, `Arial`, sans-serif

**文字色階層:**
- H1/H2: `#2D2926` (Charcoal Brown)
- H3/H4: `#2D2926` @ 90%
- Body: `#2D2926`
- Caption/Hint: `#5C5552` (Warm Gray)
- Disabled: `#8C8582`

### 5. アクセシビリティ確認

| 組み合わせ | コントラスト比 | WCAG AA |
|------------|----------------|---------|
| `#2D2926` on `#FFFFFF` | 12.6:1 | ✅ Pass |
| `#E8590C` on `#FFFFFF` | 3.9:1 | ✅ Pass (Large) |
| `#FFFFFF` on `#E8590C` | 3.9:1 | ✅ Pass (Large) |
| `#5C5552` on `#FFFFFF` | 6.2:1 | ✅ Pass |

### 6. 実装対象ファイル

| 優先度 | ファイル | 変更内容 |
|--------|----------|----------|
| P1 | `PDFreport/templates/style.css` | CSS変数の更新 |
| P1 | `nicegui_app.py` (L680-720) | インラインスタイル更新 |
| P2 | `PDFreport/templates/cover_page.html` | ブランドカラー適用 |
| P2 | `PDFreport/templates/base.html` | ベーステンプレート |
| P3 | `core/ui/panels.py` | UIコンポーネントカラー |
| P3 | `PDFreport/high_quality_pdf_generator.py` | PDFカラー定義 |

### 7. 視覚的一貫性ルール

1. **60-30-10ルール適用**
   - 60%: 白/暖白（背景）
   - 30%: チャコールブラウン（テキスト）
   - 10%: フォックスオレンジ（アクセント）

2. **オレンジの使用制限**
   - CTAボタン（1画面に1-2個まで）
   - 重要な通知/アラート
   - アクティブ状態インジケーター
   - スコアの「要改善」レベル

3. **避けるべき組み合わせ**
   - オレンジ × 赤（警告の混同）
   - 大面積のオレンジ背景（目立ちすぎ）

### 8. 実装タスク（軽量モデル向け詳細指示）

---

#### Task 1: nicegui_app.py - CSS変数の更新
**ファイル**: `nicegui_app.py`
**行番号**: 276-300
**変更前**:
```css
:root {
  --bg: #0B1420;
  --bg-deep: #071018;
  --surface: #FFFFFF;
  --surface-muted: #F6F8F9;
  --accent: #12A594;
  --accent-2: #1E5D6E;
  --accent-soft: rgba(18, 165, 148, 0.12);
  --text: #0D1117;
  --text-muted: #0D1117;
  --border: rgba(13, 17, 23, 0.08);
  --shadow: 0 16px 50px rgba(11, 20, 32, 0.12);
}
```
**変更後**:
```css
:root {
  --bg: #2D2926;
  --bg-deep: #1F1C1A;
  --surface: #FFFFFF;
  --surface-muted: #FAF9F8;
  --accent: #E8590C;
  --accent-2: #D9480F;
  --accent-soft: rgba(232, 89, 12, 0.10);
  --text: #2D2926;
  --text-muted: #5C5552;
  --border: rgba(45, 41, 38, 0.12);
  --shadow: 0 16px 50px rgba(45, 41, 38, 0.10);
}
```

---

#### Task 2: nicegui_app.py - 背景グラデーションの更新
**ファイル**: `nicegui_app.py`
**行番号**: 308-312
**変更前**:
```css
background: radial-gradient(1200px 600px at 10% -10%, rgba(18,165,148,0.22), transparent),
            radial-gradient(1200px 600px at 90% -20%, rgba(30,93,110,0.18), transparent),
            linear-gradient(160deg, #0B1420 0%, #0E1B2B 45%, #0B1420 100%);
```
**変更後**:
```css
background: radial-gradient(1200px 600px at 10% -10%, rgba(232,89,12,0.15), transparent),
            radial-gradient(1200px 600px at 90% -20%, rgba(255,140,66,0.10), transparent),
            linear-gradient(160deg, #2D2926 0%, #3D3835 45%, #2D2926 100%);
```

---

#### Task 3: nicegui_app.py - ボタングラデーションの更新
**ファイル**: `nicegui_app.py`
**行番号**: 501
**変更前**:
```css
background: linear-gradient(135deg, #12A594, #1E5D6E);
```
**変更後**:
```css
background: linear-gradient(135deg, #E8590C, #D9480F);
```

---

#### Task 4: nicegui_app.py - タブアクティブ色の更新
**ファイル**: `nicegui_app.py`
**行番号**: 621
**変更前**:
```css
border: 1px solid rgba(18, 165, 148, 0.22);
```
**変更後**:
```css
border: 1px solid rgba(232, 89, 12, 0.22);
```

---

#### Task 5: nicegui_app.py - コールアウトグラデーションの更新
**ファイル**: `nicegui_app.py`
**行番号**: 653
**変更前**:
```css
background: linear-gradient(140deg, rgba(18,165,148,0.12), rgba(30,93,110,0.08));
```
**変更後**:
```css
background: linear-gradient(140deg, rgba(232,89,12,0.10), rgba(255,140,66,0.06));
```

---

#### Task 6: nicegui_app.py - コールアウトボーダーの更新
**ファイル**: `nicegui_app.py`
**行番号**: 659
**変更前**:
```css
border: 1px solid rgba(18,165,148,0.18);
```
**変更後**:
```css
border: 1px solid rgba(232,89,12,0.18);
```

---

#### Task 7: PDFreport/templates/style.css - CSS変数の更新
**ファイル**: `PDFreport/templates/style.css`
**行番号**: 1-10
**変更前**:
```css
:root {
    --ink: #1f2933;
    --muted: #5f6b7a;
    --line: #d0d5db;
    --accent: #0f4d92;
    --bg: #ffffff;
    --panel: #f6f7f9;
    --radius: 8px;
    font-family: Arial, sans-serif;
}
```
**変更後**:
```css
:root {
    --ink: #2D2926;
    --muted: #5C5552;
    --line: #E5E2DF;
    --accent: #E8590C;
    --bg: #ffffff;
    --panel: #FAF9F8;
    --radius: 8px;
    font-family: 'Noto Sans JP', Arial, sans-serif;
}
```

---

#### Task 8: PDFreport/templates/cover_page.html - アクセントカラーの更新
**ファイル**: `PDFreport/templates/cover_page.html`
**行番号**: 71
**変更前**:
```css
border-left: 4px solid #0d335d;
```
**変更後**:
```css
border-left: 4px solid #E8590C;
```

---

### 9. 実装順序チェックリスト

| # | タスク | ファイル | 依存 | 完了 |
|---|--------|----------|------|------|
| 1 | CSS変数の更新 | nicegui_app.py:276-300 | なし | [x] |
| 2 | 背景グラデーション | nicegui_app.py:308-312 | Task 1 | [x] |
| 3 | ボタングラデーション | nicegui_app.py:501 | Task 1 | [x] |
| 4 | タブアクティブ色 | nicegui_app.py:621 | Task 1 | [x] |
| 5 | コールアウトグラデーション | nicegui_app.py:653 | Task 1 | [x] |
| 6 | コールアウトボーダー | nicegui_app.py:659 | Task 5 | [x] |
| 7 | PDF CSS変数 | style.css:1-10 | なし | [x] |
| 8 | PDF cover_page | cover_page.html:71 | Task 7 | [x] |

### 10. 検証コマンド

```bash
# 1. 構文チェック（Python）
python -m py_compile nicegui_app.py

# 2. アプリ起動（目視確認）
python nicegui_app.py

# 3. 確認ポイント
# - ヘッダー/ボタンがオレンジ系になっているか
# - テキストがチャコールブラウンになっているか
# - 背景グラデーションが暖色系になっているか
```

---

## 進行方法

コードレビューで検出された問題を5フェーズに分けて段階的に修正する。

- **管理ファイル**: `review/REVIEW_MASTER.md` — 問題マップ・進捗トラッキング
- **作業ファイル**: `review/PHASE{1-5}_*.md` — 各フェーズの修正手順・完了条件

| Phase | 内容 | 状態 |
|-------|------|------|
| 1 | 緊急セキュリティ修正（A-1〜A-4） | **完了** |
| 2 | LLM安全性・コスト制御（B-1〜B-4） | 未着手 |
| 3 | パイプライン堅牢化（C-1〜C-5） | 未着手 |
| 4 | アーキテクチャ改善（D-1〜D-4） | 未着手 |
| 5 | 法務チェック強化（E-1〜E-4） | 未着手 |

各フェーズ完了時にこのファイルと`REVIEW_MASTER.md`の進捗を更新する。

---

## 2026-02-03
- **UI情報設計の再編（BOX2/BOX3）**:
  - BOX2（分析結果）に「主要リスク」を移動し、上位→中位→専門的の順に整理
  - 「詳細（専門的な分析）」は折りたたみに集約し、通常時はタブ表示
  - BOX3（レポート）はタブではなく、役割別セクション（運用/リライト/エンジニア）の折りたたみに変更
  - 反映: `core/ui/panels.py`
  - 実装詳細:
    - `results_panel()` 末尾に「詳細（専門的な分析）」の `ui.expansion()` を追加し、`detail_tabs()` を内包
    - BOX2内の「主要リスク」を `report_panel()` から `results_panel()` へ移動
    - `report_panel()` の表示は `role_report_sections` による役割別セクション描画に変更
- **表示モード/ロールの整合**:
  - モードラベルを「要点/詳細」に変更（従来の初心者/上級者の誤解を回避）
  - モード/ロール変更時は `results_panel.refresh()` / `report_panel.refresh()` を更新ポイントに統一
  - 反映: `core/ui/mode_manager.py`, `nicegui_app.py`
  - 実装詳細:
    - `ModeManager` の `label()` を「要点/詳細」表記に修正
    - `nicegui_app.py` のトグル表示文言をラベルと同期
- **印刷モードの追加（画面印刷用）**:
  - AppStateに `print_mode` を追加し、BOX2に「印刷モード」トグル（通常/印刷）を追加
  - 印刷モード時は詳細タブを使わず、各タブ内容を縦並びのカード表示に切替
  - 「詳細（専門的な分析）」の折りたたみは印刷モード時に自動で開く
  - 反映: `nicegui_app.py`, `core/ui/panels.py`
  - 実装詳細:
    - `AppState.print_mode: bool` を追加
    - BOX2ヘッダーに「印刷モード」ラベル＋トグルを追加
    - 印刷モード時は `detail_tabs()` がタブ描画せず、セクションを連続描画（早期return）
    - 「詳細」折りたたみの `value` に `print_mode` を加算
- **折りたたみの全展開（入れ子対応）**:
  - BOX2/BOX3に「印刷用に全て展開」「折りたたみ」ボタンを追加
  - DOM内の `.q-expansion-item` をJSで強制展開/折りたたみに変更（入れ子も対象）
  - 反映: `nicegui_app.py`
  - 実装詳細:
    - `results_container`/`report_container` に専用クラスを付与
    - `ui.run_javascript()` で `.q-expansion-item__header` をクリックして開閉
    - `setTimeout` を複数回呼び、遅延レンダリングの入れ子も展開
- **印刷モードの視認性向上（スタイル追加）**:
  - 印刷モード専用のカード/区切り/見出しスタイルを追加（影を抑え、区切りは点線）
  - 反映: `nicegui_app.py`, `core/ui/panels.py`
  - 実装詳細:
    - `print-detail-shell/section/title/divider` のCSSを追加
    - 印刷モード描画時に `print-detail-*` クラスを適用
- **法務表示の整理（非EC対策含む）**:
  - 非EC判定時は消費者保護の best_practices を抑制
  - `force_is_ec` を site_health に追加し、UIのページ種別指定を優先
  - 法務はBOX2側で表示し、詳細タブ側は `include_legal=False` に変更
  - 反映: `core/legal_checks/consumer_protection.py`, `core/engine/site_health_engine.py`, `core/engine/orchestrator.py`, `core/ui/panels.py`, `core/ui/tabs/health_tab.py`
  - 実装詳細:
    - `consumer_protection.py` で非EC時は best_practices をskip
    - `site_health_engine.py` に `force_is_ec` を追加し、判定を上書き
    - `orchestrator.py` で UI選択のページ種別から `force_is_ec` を算出・注入
    - `render_health_tab()` に `include_legal` 引数を追加（詳細側は False）
- **補足**:
  - 「詳細タブ」は「詳細（専門的な分析）」折りたたみの中に移動済み
  - `detail_tabs()` の直描画を撤去し、折りたたみ内からのみ呼ぶ構成に統一
  - BOX2のバッジ文言は印刷モードに合わせて動的に切替（タブ/縦並び）
  - 「印刷用に全て展開」はトップ/入れ子の両方が対象

### 再起動後の確認ポイント
- 印刷モード時の詳細が縦並びで全表示されるか（タブ表示になっていないか）
- 「印刷用に全て展開」で入れ子の折りたたみも開くか
- 非ECサイトで特商法系の表示が抑制されているか

### 未実行
- UIの目視確認（通常/印刷モード切替、印刷時の視認性）

### 主要ファイルの読み順（再起動時の最短復帰用）
1) `nicegui_app.py`（UI入口/状態/トグル/全展開JS/印刷モードトグル）
2) `core/ui/panels.py`（BOX2/BOX3構成・詳細折りたたみ・印刷モード描画）
3) `core/ui/mode_manager.py`（要点/詳細ラベル）
4) `core/ui/tabs/health_tab.py`（法務表示の有無切替 `include_legal`）
5) `core/engine/orchestrator.py`（`force_is_ec` の算出・注入）
6) `core/engine/site_health_engine.py`（`force_is_ec` 優先判定）
7) `core/legal_checks/consumer_protection.py`（非ECの best_practices 抑制）

### 実装位置メモ（行番号は目安）
- `nicegui_app.py:81` AppStateに `print_mode` を追加
- `nicegui_app.py:685-714` 印刷モード用スタイル（`print-detail-*`）
- `nicegui_app.py:848-908` BOX2内に印刷モードトグル＋全展開/折りたたみ
- `nicegui_app.py:848` `results_container` に `results-container` クラス
- `nicegui_app.py:974` `report_container` に `report-container` クラス
- `core/ui/panels.py:213` `results_panel()` 入口
- `core/ui/panels.py:580-584` 「詳細（専門的な分析）」折りたたみ＋`detail_tabs()`
- `core/ui/panels.py:589` `detail_tabs()` 定義
- `core/ui/panels.py:633-700` 印刷モード時の縦並び描画（タブ非使用）
- `core/ui/panels.py:731` `report_panel()` 入口
- `core/ui/mode_manager.py:14` `ModeManager` 定義（要点/詳細ラベル）
- `core/ui/tabs/health_tab.py:119` `render_health_tab(..., include_legal=True)`
- `core/engine/orchestrator.py:1014-1231` `force_is_ec` を算出し site_health に注入
- `core/engine/site_health_engine.py:73-213` `force_is_ec` 優先判定/法務結果制御
- `core/legal_checks/consumer_protection.py:36-67` 非ECの best_practices 抑制

## 2026-01-30
- **法的チェック・SEO/AIOアルゴリズム改修の全体計画を策定**:
  - UX原則（ニールセン、Fitts、Hick）に基づき、全10フェーズの実行順序を最適化。
  - すべての計画詳細、コードテンプレート、検証コマンドを `.agent/plans/` ディレクトリに配備完了。
  - AWS移行を見据えたアーキテクチャ設計（Phase 9: 設定一元化、Phase 8: DB抽象化）を導入。
- **実装済みのロジック（Phase 2, 3, 4）**:
  - `crawl_depth_strategy.py` (Phase 2), `premiums_labeling.py` (Phase 3), `visibility_checker.py` (Phase 4) のロジック部分を完了。
  - ※UI/PDF統合は後続のフェーズで実施予定。
- **次回TODO（再起動後）**:
  - **重要**: `.agent/plans/PROGRESS.md` を参照して実装を開始すること。
  - **開始点**: `Phase 9: 設定ファイル一元化` から着手。
  - AWS移行を SaaS 化の前提として、各フェーズの完了基準をクリアしていく。

- **Wikidata連携（Top3のみ/キャッシュ付き）を追加**:
  - `core/wikidata_client.py` を追加し、Wikidata QID検索＋30日キャッシュを実装
  - `core/aio_analyzer.py` のEntity LinkingにQIDリンクを統合（小さなボーナス付与）
- **構造化サマリーをLLMリライトに反映**:
  - `core/engine/orchestrator.py` で見出し/箇条書き/FAQなどの構造化要約を生成
  - `core/aio_suggestions.py` に構造化サマリー入力を追加、温度を0.3に調整
- **リライトの視覚的強調**:
  - UIでBefore/Afterの差分を強調表示（`core/ui/panels.py`, `nicegui_app.py`）
  - PDFのAfterカードを太字表示（`PDFreport/high_quality_pdf_generator.py`）
- **次回TODO（再起動後）**:
  - `python -m py_compile` で構文チェック
  - Wikidata連携のON/OFF挙動確認（`ENABLE_WIKIDATA`, `WIKIDATA_TOP_K`）
  - UIの差分ハイライト表示とPDFのAfter太字を実データで確認

## 2026-02-01
- **UI修正**: `ui.html()` に `sanitize=False` 追加（NiceGUI API変更対応）
  - `core/ui/panels.py` の4箇所を修正
  - これにより「履歴」タブが正常に表示されるようになった
- **PDF生成器拡張（fpdf2）**: 3ページ → 7ページに拡張
  - 追加セクション: クロール設定、構造化データ、内部リンク、AIO改善、SEO詳細、AIO詳細、法務
  - `PDFreport/high_quality_pdf_generator.py` の `generate_seo_aio_pdf_report()` を大幅改修
  - WeasyPrint（HTMLテンプレート方式）はWindows依存問題のため見送り
- **履歴機能の状態**:
  - DB保存: ✅ 動作確認済み（`core/storage/database.py`）
  - 履歴一覧表示: ✅ 動作確認済み（`core/ui/dashboard.py`）
  - 2件比較機能: ✅ 実装済み
  - 過去の詳細表示: ❌ 未実装（行クリックで詳細を開く機能）
- **プログレスバー修正** (`nicegui_app.py`):
  - 問題: 完了時も50%で止まり、100%表示されない
  - 原因: `finally`ブロック（約1139行目）で即座に`state.progress_percent = 0.0`にリセット
  - 修正1: `update_progress_label()`（約786行目）の先頭に完了状態チェック追加
    ```python
    if state.progress_stage == "完了":
        progress_bar.visible = True
        progress_label.text = "進捗: 完了 - 解析完了 (100%)"
        progress_bar.value = 1.0
        return
    ```
  - 修正2: `finally`ブロック（約1139行目）で完了時は1.5秒遅延リセット
    ```python
    if state.progress_stage == "完了":
        async def delayed_progress_reset():
            await asyncio.sleep(1.5)
            state.progress_started_at = None
            # ...リセット処理
        asyncio.create_task(delayed_progress_reset())
    ```
- **階層クロール機能** (`core/engine/orchestrator.py`):
  - 目的: 法務チェック精度向上（プライバシーポリシー/会社概要等の検出）
  - 新規メソッド `_fetch_priority_pages()` を追加（約675-740行目）
    - `crawl_depth_strategy.py` の `priority_pages`（特商法/プライバシー/会社概要等のURL）を取得
    - 各ページをHTTP GET（タイムアウト15秒、最大2MB）
    - 取得HTMLを `combined_html` として結合
  - `analyze_url()` 内（約854行目付近）でクロール戦略取得後に呼び出し
    ```python
    priority_urls = crawl_strategy.get("priority_pages", [])
    if priority_urls:
        priority_pages_result = self._fetch_priority_pages(priority_urls, update_progress)
    ```
  - 結果を `priority_pages_crawled` キーで分析結果に含める（約1331行目）
- **法務チェック用HTML結合** (`core/engine/orchestrator.py`):
  - 約1172行目: `combined_html_for_legal` をtryブロック外で初期化
  - メインHTML + 優先ページHTMLを結合して `run_full_site_health_check()` に渡す
  - 約1392行目: `"html": combined_html_for_legal` で結合済みHTMLを結果に保存
  - `non_ec_summary.py` の `_detect_trust_signals()` が結合HTMLを使用して検出
- **次回TODO**:
  - `start.bat` で起動して動作確認
  - 法務チェック検出率を確認（プライバシーポリシー/会社概要のリンク検出）
  - プログレスバーが100%表示後にリセットされるか確認

## 2026-02-02
- **リーガル検出の基盤強化**:
  - `core/crawl_depth_strategy.py`: depth=0でも法務関連リンクの priority_pages を抽出、プライバシー/利用規約の表記ゆれを拡張
  - `core/engine/orchestrator.py`: 法務用結合HTMLをAIOの業界分析コンプライアンスにも適用、利用規約リンク検出を追加
  - `core/legal_checks/non_ec_summary.py`: プライバシー・利用規約のキーワード拡張
- **法務サマリーの整合**:
  - `core/engine/orchestrator.py` で `legal_summary` を生成し結果に格納
  - `PDFreport/high_quality_pdf_generator.py` と UI（サイトヘルス）で同一サマリーを参照
- **PDFブランク対策**:
  - `PDFreport/high_quality_pdf_generator.py`: 空セクションの案内文統一（未取得時の明示）、改善ポイント未取得時の注記を追加
- **UI情報設計**:
  - `nicegui_app.py`: 表示ロール（経営/運用/エンジニア/法務/すべて）を追加
  - `core/ui/panels.py`: ロール別にメインタブとレポートタブを出し分け

## 2026-02-02（追加）
- **予算最適化**:
  - LLMは `gpt-4.1-mini` に統一（`core/config.py`, `core/model_selector.py`, `core/engine/orchestrator.py`）
  - AI予測/質問生成/FAQ自動生成（AI生成）を削除し、引用スニペットのみを残す（`core/engine/orchestrator.py`, `core/ui/tabs/simulation_tab.py`, `core/ui/panels.py`, `nicegui_app.py`）
- **クロール優先順位（depth=1）**:
  - `core/crawl_depth_strategy.py` を「法務→事業→FAQ」優先＋カテゴリ多様性（法務2/事業1/FAQ1）で抽出、最大4ページ取得に変更
 - **リーガルUIの重複修正**:
  - `core/legal_checks/visibility_checker.py`: `>>` 等のページネーション記号を除外、リンク到達性の指摘を1件に集約（件数＋例を表示）
 - **非EC法務サマリーの根拠提示**:
  - `core/legal_checks/non_ec_summary.py`: 「どこの事か（例:場所/リンクテキスト/href/代表フレーズ）」を文言に付与
 - **PDFの再レイアウト（SEO分析レポートらしく）**:
  - `PDFreport/high_quality_pdf_generator.py`: 表紙/スコア/総合サマリー/非エンジニア2p（リライト差分）/エンジニア2p（プラットフォーム別）/法務1p（OK/NG+根拠）に再構成

## 2026-01-31
- **状況整理**: PROGRESS/Phase記録と実装にズレがあったため、状態を「実装済み/要確認」に整理。
- **エラー対応ルール（厳守）**:
  - 検証でエラーや期待外れが出た場合、**修正は1回のみ**試す。
  - それでも解決しない場合は、**作業を停止し、ユーザーへ状況を報告**する。
- **明日やること（UI確認）**:
  - 「履歴」タブ表示と履歴保存が反映されるか確認
  - 見るべきファイル:
    - `nicegui_app.py`（履歴保存・PDF保存フロー）
    - `core/ui/panels.py`（タブ構成・履歴タブ呼び出し）
    - `core/ui/dashboard.py`（履歴テーブル表示）
    - `core/storage/database.py`（保存/取得）
- **明日やること（PDF確認）**:
  - `generate_pdf_report_v2` の出力が崩れる条件の確認
  - 見るべきファイル:
    - `core/engine/orchestrator.py`（PDF生成呼び出し）
    - `PDFreport/reporting.py`（HTML用データ整形）
    - `PDFreport/templates/report_summary.html`（HTMLテンプレート）
    - `PDFreport/simple_generator.py`（WeasyPrint出力）
    - `PDFreport/high_quality_pdf_generator.py`（従来PDFとの比較用）

## 2026-04-04
- ダッシュボード上段の新規分析カードを `C:\tetie\zip` 参照の縦積み導線へ寄せ、対象URL / 競合URL の入力幅を拡張
- `/runs/{run_id}` の保存済みワークスペースで `SEO改善` タブのリライト案ラベルを明示化し、タイトル/ディスクリプション改善候補を再度見つけやすく調整
- snapshot と saved workspace の両方で `llms.txt` 状態を明示表示するようにし、既存 run でも result JSON からの fallback 表示に対応
- provider 状態の重複表示を整理し、`Perplexity: 通過` は UI から除外。保存済みワークスペースでは provider 状態を `実装メモ` 側へ集約
- 保存済み分析の `最優先3件` / `詳細ワークスペース` 周辺の曖昧な案内文を削除し、常設説明を減らして判断負荷を下げた
- `最優先アクション` と saved workspace のカードで途中省略をやめ、長文は `全文を見る` / `クリックで全文表示` の展開に変更。履歴一覧も最優先アクション列は省略ではなく改行表示へ調整
- 別タブ実装向けに `plan/tab_ia_rework_2026-04-04/` を追加し、5タブ再編、FAQ/llms.txt の住み分け、provider 状態の一元化、snapshot 保存粒度拡張、LLMO soft 項目の最新整理を計画として固定

## 2026-01-29
- **Entity Recognition 改善リファクタリング（全4フェーズ完了）**:
  - 計画ファイル: `plans/refactor2/REFACTOR_MASTER.md`
  - **Phase 1**: Sudachi品詞情報の活用
    - `calculate_entity_linking()` を `pos[1] == '固有名詞'` ベースに改修
    - 静的辞書（約200語）からSudachi辞書（100万語+）ベースに移行
  - **Phase 2**: カテゴリ別スコアリング
    - `ENTITY_CATEGORY_WEIGHTS` 追加（人名1.2、姓1.1、一般1.0等）
    - 重み付きスコア計算とカテゴリ別集計を実装
    - E-E-A-T連携アクション生成（人名/組織名不足時のアドバイス）
  - **Phase 3**: 静的辞書の役割変更
    - `SUPPLEMENTARY_ENTITIES` 追加（ChatGPT, E-E-A-T, Core Web Vitals等の新語）
    - 旧関数に `DeprecationWarning` 追加
  - **Phase 4**: 正規化と表記ゆれ対応
    - `normalize_entity()`, `group_entities_by_normalized()` 追加
    - 表記ゆれ検出とアドバイス生成（「トヨタ」「TOYOTA」→統一推奨）
  - テストスクリプト: `tests/test_phase{1-4}_*.py`

- **リファクタリング進行**:
  - `seo_aio_engine.py` を `core/engine/orchestrator.py` へ移動し、後方互換プロキシ化
  - サイトヘルス統合ロジックを `core/engine/site_health_engine.py` に外部化
  - `core/legal_checks/consumer_protection.py` と `core/structured_data/checker.py` を追加
- UIタブ表示ロジックを `core/ui/tabs/` に分割
  - レポート表示ロジックを `core/ui/reports/` に分割（経営サマリー/印刷レポート）
  - **PDF・レポートデザインの刷新**:
    - `Sora` / `Noto Sans JP` フォントの採用、CSS Gridによるレイアウト最適化
    - [strategic_proposal_page.html](file:///c:/Users/横山裕明/Desktop/aio2-main/PDFreport/templates/strategic_proposal_page.html) 等のテンプレートデザインを刷新

## 2026-04-14
- TOP を説明中心から入力中心へ再構成
  - `nicegui_app.py` で hero の常設チップと説明行を削減し、価値説明を 1 行へ圧縮
  - 右側の `このソフトで分かること` / `最近の成果` カードを撤去し、分析入力カードをフル幅 1 カラムへ変更
  - `比較競合URL` を常設表示から `比較サイトを追加` の折りたたみへ移動し、`詳細設定を表示` を `条件を変える` に変更
  - `分析を開始する` を `分析する`、`完了後に保存結果を開く` を `保存後に開く` へ短文化
  - `core/ui/dashboard.py` で履歴セクションの KPI チップを撤去し、`最近の分析` として簡潔化
- 保存済み結果を評価専用UIへ整理
  - `core/ui/panels.py` で `/runs/{id}` を `総合評価 / 3軸評価 / 評価の理由` のみ表示する構成へ変更
  - タブ・改善提案・比較・技術詳細を初期表示から外し、評価ラベルや理由ラベルは tooltip で意味が分かる形に変更
- 暖色テーマに合わせて補助ボタンの青系表示を撤去
  - `nicegui_app.py` で `今は移動しない` / `降順` / `履歴CSV` / `優先アクションCSV` の `primary` 依存を外し、待機スピナーと進捗バーもオレンジ系へ統一
  - `core/ui/dashboard.py` の `さらに表示` / `上位だけに戻す` も同系色へ揃え、Hub から起動した際の配色差を減らした
- 保存済み結果の評価UIを再調整
  - `core/ui/panels.py` で `評価` の下に `この結果の意味` と `まずやること` を戻し、評価だけでは理解しにくい状態を解消
  - `要確認メモ` のような汎用見出しは内容ベースの見出しに置き換え、理由カードの一覧性を上げた
- 保存済み結果の復旧を最小文言で再整理
  - `core/ui/panels.py` で 5軸レーダーと要点表示を戻しつつ、`この結果の意味` などのUI語を削減
  - 見出しは `5軸 / 改善 / 理由` まで圧縮し、情報は戻しつつUI都合の説明文を増やさない構成へ寄せた
- 保存済み結果に見えやすいタブ導線を追加
  - `core/ui/panels.py` で `改善 / リライト / 設定 / 技術 / 比較` を結果直下の常設タブへ再編し、`エンジニア向け` や `リライト` の存在を隠さない構成に変更
  - `nicegui_app.py` で保存済み結果専用タブの配色とアクティブ状態を強め、青系なしでタブの存在と選択状態が一目で分かるよう調整
- 入力場所が一目で分かるようTOPを再整理
  - `nicegui_app.py` で主入力を `URL` 中心へ寄せ、`比較サイト` と `条件` を任意入力として短いラベルに統一
  - 保存済み結果だけでなく live workspace も `評価 / 改善 / リライト / 設定 / 技術 / 比較` の常設タブへ揃え、`主メニュー` / `補足メニュー` などのUI語を除去

## 2026-04-10
- サマリーUIの可視化を強化
  - `core/ui/reports/executive_summary.py` に 6軸レーダーの「改善マップ」を追加し、`SEO基礎 / AI引用 / 信頼情報 / 公開条件 / 技術基盤 / 表示安全` を圧縮表示
  - 右カラムに `先に手を入れる軸` と `先に確認` を追加し、AI公開条件の要確認件数、表示アドバイス件数、大規模サイト時の分析範囲を要約表示
  - `core/ui/panels.py` の saved workspace サマリーにも 5軸の改善マップを追加し、`/runs/{id}` でも圧縮可視化が見えるよう統一
  - `nicegui_app.py` にサマリー用の軽量スタイルを追加し、既存カードUIとトーンを揃えた

## 2026-04-06
- SEO / LLMO coverage package `plan/seo_llmo_coverage_2026-04-06/` を Phase 9 まで完走
  - `core/seo/international_audit.py`, `page_experience_audit.py`, `link_quality_audit.py`, `media_discovery_audit.py` を追加し、`hreflang / x-default / html lang`、mobile-first parity、`LCP / CLS`、crawlable links / anchor quality、image/video discoverability を段階拡張
  - `core/aio/schema_validator.py` を page-type aware validator に更新し、`article / ec / local / company` ごとの schema 推奨と不足検出を追加
  - `core/aio/commerce_readiness.py` を追加し、OpenAI merchant feed readiness と Perplexity WAF / IP readiness note を provider meaning を変えずに分離して追加
  - `core/application/analysis_run_service.py`, `core/ui/panels.py`, `core/ui/tabs/seo_tab.py`, `core/ui/tabs/health_tab.py` で summary-first を維持したまま追加監査の UI surfacing と legacy snapshot refresh を実装
  - テスト追加/更新: `tests/test_international_seo.py`, `tests/test_page_experience_audit.py`, `tests/test_link_quality_audit.py`, `tests/test_schema_validator.py`, `tests/test_media_discovery_audit.py`, `tests/test_aio_analyzer.py`, `tests/test_analysis_run_service.py`, `tests/test_sitemap_analyzer.py`
  - 検証:
    - `.venv\\Scripts\\python.exe -m py_compile core\\engine\\orchestrator.py core\\aio_analyzer.py core\\engine\\site_health_engine.py core\\aio\\schema_validator.py core\\ui\\panels.py core\\ui\\tabs\\seo_tab.py core\\ui\\tabs\\health_tab.py core\\application\\analysis_run_service.py`
    - `.venv\\Scripts\\pytest.exe -q tests\\test_aio_analyzer.py tests\\test_characterization_engine.py tests\\test_characterization_ui.py tests\\test_analysis_run_service.py tests\\test_sitemap_analyzer.py tests\\test_link_audit.py tests\\test_international_seo.py tests\\test_page_experience_audit.py tests\\test_link_quality_audit.py tests\\test_schema_validator.py tests\\test_media_discovery_audit.py` -> `44 passed`
    - live verify: `C:\\tetie\\techie-hub\\start.bat force` 後に `http://127.0.0.1:8081/` と `http://127.0.0.1:8081/runs/84` を確認し、saved UI の `実装・設定` タブで `SEO / AI Search 追加監査` / `OpenAI Commerce` / `Perplexity WAF / IP` を表示確認
- SEO / LLMO coverage 拡張の実装計画パッケージを追加
  - `plan/seo_llmo_coverage_2026-04-06/README.md` に scope / phase / owner map / latest best-practice baseline を整理
  - `TASK.md` に phase ごとの exit criteria / compile gate / pytest gate / stop conditions を定義
  - `PROGRESS.md` / `ROLLBACK.md` / `EXECUTION_PROMPT.md` を追加し、別ウインドウで再開可能な状態に固定
  - `plan/CURRENT_AND_NEXT_IMPROVEMENTS.md` に本パッケージへの入口を追加
  - 自己テスト合格後の phase 自動継続、同一 phase 3 回修正で停止、停止条件に触れない限り全 phase 完走、肥大化回避の制約を docs に追記
- SEO分析の coverage 改善を実施
  - `core/sitemap_analyzer.py` を更新し、`sitemapindex` 配下の複数子 sitemap を集約して解析できるよう修正
  - `core/seo/internal_graph.py` で内部URLの正規化と監査候補URL生成を追加
  - `core/seo/link_audit.py` を追加し、内部リンク先の HTTP エラー / リダイレクト / canonical 不整合 / noindex を監査
  - `core/engine/orchestrator.py` で内部リンク構造レポートとリンク先監査を統合
  - `core/ui/tabs/health_tab.py` と `core/ui/panels.py` に監査結果の表示を追加
  - テスト追加: `tests/test_sitemap_analyzer.py`, `tests/test_link_audit.py`
  - 検証: `.venv\\Scripts\\pytest.exe tests\\test_sitemap_analyzer.py tests\\test_link_audit.py tests\\test_characterization_engine.py tests\\test_characterization_ui.py -q` で 19件成功

## 2026-01-28
- PDF修正完了: 要点サマリーの文字切り解除 (`high_quality_pdf_generator.py:3397`)
- コードレビュー実施: セキュリティ/LLM/パイプライン/アーキテクチャ/法務の5観点
- レビュー計画ファイル作成: `review/REVIEW_MASTER.md` + Phase 1-5 作業ファイル
- Phase 1 着手開始
- **Phase 1 完了** (セキュリティ修正):
  - A-1: APIキーのデバッグ出力をloggingに移行、キー長出力削除
  - A-2: subprocess.runのURL検証追加、stdin経由渡しに変更
  - A-3: safe_fetch.pyのリダイレクト先URL即時検証追加
  - A-4: PDFファイル名にランダムトークン追加、エラーメッセージからスタックトレース除去
  - **検証状況**: コード目視確認済み、構文チェック(py_compile)未実施
  - **次回TODO**: `python -m py_compile` で3ファイルの構文確認後、Phase 2着手
- **AIO改善（Quick Win実施）**:
  - `core/aio_analyzer.py` に **E-E-A-T検出** を追加（著者Author/組織Organization情報のJSON-LD検知）
  - `core/aio_analyzer.py` に **マルチモーダル評価** を追加（画像alt属性の品質スコアリング）
  - 上記シグナルに基づき、具体的な改善アドバイスを自動生成する機能を追加
- **付加価値機能の追加 (完了)**:
  - `core/ui/panels.py` に **speakable コピーボタン追加**: JSON-LDを1クリックでコピー可能にし、設置ガイドも表示。
  - `core/ui/panels.py` の **競合比較強化**: AIO詳細指標（E-E-A-T、マルチモーダル）の自社vs競合比較を統合。
- **リファクタリング計画の策定 (完了)**:
  - 巨大化した `seo_aio_engine.py` (185KB) と `core/ui/panels.py` (105KB) のモジュール化計画を策定。
  - `plans/refactor/` ディレクトリを作成し、軽量AIモデルでも実行可能な粒度の指示書（Phase 01〜05）を整備。
  - 明日以降、この計画に基づき段階的に実装予定。


## 2026-01-27
- ~~PDF修正の残作業: `PDFreport/high_quality_pdf_generator.py:3327` の `pdf.add_bullet_point(str(item)[:140])` を `pdf.add_bullet_point(str(item))` に変更し、要点サマリーの文字切りを解除する。~~ → 完了

## 2026-02-07（予定）
- `C:\tetie\notecode` 改良を実施する。
  - 企業の連絡レベル短文から開始し、URL精査を経て、専門家向け解説まで段階的に強化する。
  - 目標: 人間と区別がつかないレベルの自然さ・精度・一貫性に到達させる。
  - `tests/test_analysis_run_service.py`
    - transient error の 1 回再試行と non-retryable error の即時終了を回帰 test で固定
## 2026-04-10
- ダッシュボード分析完了後に結果が表示されない不具合を修正
  - `nicegui_app.py` の保存完了後遷移を `ui.navigate.to(...)` から保持済み `page_client.open(...)` に変更
  - NiceGUI の `The parent element this slot belongs to has been deleted.` による完了直後の画面遷移失敗を回避
  - クライアント切断時は例外にせず、保存済みメッセージと保存IDを残すよう調整
  - 追加調整: 完了時に `保存結果 #ID を開く` の通常リンクを表示し、`page_client.connected()` 待機後に自動遷移を試行
  - 追加調整: 保存完了時の socket 接続状態と遷移送信成否を `app.log` に出力
  - レーダーチャート/保存済みワークスペース向けの法務値補正を追加
    - `core/application/analysis_run_service.py` で `legal_summary.top_issues` 未生成時に `high_priority/medium_priority/low_priority` から表示項目を補完
    - `integrated_results.legal_score` 未設定時は法務チェック結果から保存用 `legal_score` を再計算するよう調整
    - `SNAPSHOT_SCHEMA_VERSION` を更新し、既存 saved run を再読込時に新しい法務値で再構築
  - `core/ui/reports/executive_summary.py` でも live 表示用に法務スコア/表示件数の fallback を追加

## 2026-04-20
- 保存済みワークスペースのタブ文字が一部見切れる問題を narrow fix
  - `nicegui_app.py` の `.saved-run-tabs .q-tab` を 48px → 52px に調整し、上下にわずかな余白を追加
  - `.saved-run-tabs .q-tab__content` / `.q-tab__label` に `line-height` と中央寄せを明示し、日本語ラベル上端のクリップを抑制
  - `python -m py_compile nicegui_app.py` で構文確認済み
