# WORKLOG

過去の記録は `WORKLOG.backup.md` を参照してください。

---

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
