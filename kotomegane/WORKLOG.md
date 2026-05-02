# Kotomegane Worklog

`kotomegane` 現行 PoC の current snapshot と handoff を残す。  
旧作業履歴は `archive/WORKLOG.md` を参照する。

## Current Source Of Truth

- `AGENTS.md`
- `docs/CURRENT_STATE_2026-03-30.md`
- `docs/DOC_STATUS.md`
- `docs/UI_REDUCTION_IMPLEMENTATION_PLAN_2026-04-14.md`
- `docs/RESULT_UX_IMPLEMENTATION_PLAN_2026-04-14.md`
- `docs/COMPETITIVE_VALUE_VISUALIZATION_PLAN_2026-04-24.md`
- `docs/SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
- `docs/LLM_BATCH_AND_CACHE_RULES_2026-04-05.md`
- `docs/DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md`
- `docs/OPENAI_RUNTIME_NOTES.md`
- `TASK.md`
- `README.md`
- `ALGORITHM.md`

## 2026-04-29 Hero Logo Crop Fix

### What Changed

- `C:\tetie\ロゴかお.png` を `assets/logo_mark_icon.png` として取り込み、hero の 44px ロゴ枠で中央文字だけが出る状態を防いだ
- `app.py` の hero ロゴ参照を `/branding/logo_mark_icon.png` へ変更した
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` に current UI 表示状態を追記した

### Preserved

- ロゴ資産、静的配信 path、LLM 実行、prompt、scoring、DB schema、HUB `/healthz` 判定は変更していない

## 2026-04-29 Result Detail Auto-Expand UX

### What Changed

- 手動分析完了後に、下段の `今回の結果 / 定期分析の推移 / 定期分析 / 設定を見る` expansion を自動展開し、`今回の結果` タブを開くようにした
- 定期分析の `結果を反映` 後も同じく `今回の結果` タブを自動表示するようにした
- 同条件の直近 run を復元した場合も、結果確認の続きとして同じ detail surface を自動展開するようにした
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` に current UX を追記した

### Preserved

- LLM 実行、prompt、query planner、scoring、DB schema、保存形式、HUB `/healthz` 判定は変更していない

## 2026-04-26 Startup And Refresh Root-Cause Fix

### What Changed

- `storage.py` に `keyword_result(analyzed_at DESC)`、`keyword_result(run_id, analyzed_at DESC)`、`source_url(result_id)`、pending enrichment 用 partial index を追加した
- `Storage()` 初期化時の同期 `_backfill_result_enrichment()` を廃止し、起動後 background maintenance の `run_result_enrichment_maintenance(limit=250)` へ分離した
- enrichment maintenance は `source_url` を `result_id IN (...)` で一括取得し、pending がなくなったら `PRAGMA user_version=1` を marker として再実行しない
- dashboard refresh は 1 回作った payload を `refresh_dashboard_surface`、periodic signature、hero status で使い回す形へ寄せた
- `定期分析の推移` タブ内の詳細 Plotly は初期表示で生成せず、タブ表示時に lazy mount / lazy refresh する形へ変更した
- `README.md`、`docs/CURRENT_STATE_2026-03-30.md`、`ALGORITHM.md` を current state に合わせた

### Why

- `/healthz` 分離後も `/` 自体が約 2.7 秒かかっており、初期表示で hidden tab 内の詳細 Plotly まで生成していた
- `list_recent_results(500)` は `keyword_result` の full scan + temp B-tree sort、`source_url WHERE result_id = ?` は full scan になっていた
- refresh / periodic / hero が別々に read-model を作り直すと、画面表示後の refresh でも不要な DB 読みと Plotly 更新が重なる

### Verified

- `.venv\Scripts\python.exe -m py_compile app.py storage.py ui\dashboard_view_models.py ui\dashboard_refreshers.py ui\page_refreshers.py`
- `.venv\Scripts\python.exe -c "import app; print('IMPORT_OK')"`
- `.venv\Scripts\python.exe -m unittest tests.test_security_hardening`
- `EXPLAIN QUERY PLAN` で `list_recent_results` が `idx_keyword_result_analyzed_at`、`source_url WHERE result_id = ?` が `idx_source_url_result_id` を使用することを確認した
- `C:\tetie\techie-hub\start.bat` 経由で起動し、`curl http://127.0.0.1:8083/healthz` は `200 / 0.003027s`、`curl http://127.0.0.1:8083/` は `200 / 0.652714s`
- Playwright headless で HUB のコトメガネカードを確認し、`aria-disabled=false`、button class は `button button-primary` のまま

## 2026-04-26 TECHIE HUB Health Check Stabilization

### What Changed

- `app.py` に lightweight runtime health endpoint の `/healthz` と `/health` を追加した
- `C:\tetie\techie-hub\index.html` のコトメガネ起動判定を `/` ではなく `/healthz` へ変更し、HUB の 3 秒ごとの ping が NiceGUI full page render を起こさないようにした
- `C:\tetie\techie-hub\start.bat` の `KM_URL` を `/healthz` に変更し、起動待機と unresponsive listener 判定も full UI ではなく lightweight health で見るようにした
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` に current runtime health 方針を追記した

### Why

- 8083 は listen していたが、HUB が `http://127.0.0.1:8083/` を health check として 6 秒 timeout で定期取得していた
- コトメガネの `/` は DB 読み込み、Plotly、NiceGUI コンポーネントを含む full UI 生成なので health check として重く、abort されても server 側の画面生成が積み上がって `ConnectionResetError` とボタン非アクティブの原因になっていた
- timeout 延長ではなく、health check と画面生成の責務を分けることで再発条件を外した

### Verified

- `build_dashboard_refresh_payload` の direct timing では DB/read-model 側が約 0.2 秒で、遅延主因が `/` full page health ping の積み上がりであることを確認した
- `.venv\Scripts\python.exe -m py_compile app.py`
- `.venv\Scripts\python.exe -c "import app; print('IMPORT_OK')"`
- `C:\tetie\techie-hub\start.bat` 経由で 8083 を起動し直し、`http://127.0.0.1:8083/healthz` が `200` を返すことを確認した
- HUB 画面の `コトメガネ` ボタンは `aria-disabled=false`、`button-disabled` class なしに戻ることを in-app browser で確認した
- `http://127.0.0.1:8083/` は単発 request で `HTTP 200` を返すことを確認した
- `.venv\Scripts\python.exe -m unittest tests.test_security_hardening`

## 2026-04-26 First-Time UX Boundary Follow-up

### What Changed

- `app.py` の実行カードを `まずは1回だけ確認` の読み順へ寄せ、`1回だけ分析` を大きい主CTA、`定期分析を実行` / `自動定期分析を設定` を `継続的に見るなら定期分析` の補助導線へ移した
- `今回の結果` は未実行時や入力変更後に `今の入力では未分析` を明示し、保存済み旧結果を今回面へ混ぜないことを上段カードと空状態で見せるよう更新した
- `保存済みの累積傾向` と保存済み質問一覧は `過去データ` ラベル、淡い別背景、左罫線、`今回の入力とは別集計` chip で current result と視覚的に分けた
- `ui/detail_views.py` の `改善判断サマリー` 冒頭へ `外部サイト依存 -> 見え方の揺れ -> 弱い質問タイプ` の優先度ストリップを追加し、危ない順番と次に見る場所を先に示すようにした
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を current UI に合わせて更新した

### Preserved

- 新しい LLM 呼び出し、API 実行、prompt、query planner、分析ロジック、スコアリング、DB schema、保存形式は変更していない
- 共通ヘッダ、TECHIE 共通ブランドシェル、`assets/logo_mark.svg` 前提は変更していない
- 内部 ID を user-facing に追加表示していない

## 2026-04-26 Commercial Demo Judgment UI

### What Changed

- `ui/result_story_builders.py` に display-only の `根拠の安定度`、`見え方の安定度`、`弱い質問タイプ` view-model helper を追加した
- `ui/result_cards.py` は first view の `AI回答に使われた主要ソース` カード内へ、根拠比率 bar、依存リスク badge、上位ソース集中度 meter を compact 表示として追加した
- `ui/detail_views.py` は `改善判断サマリー` 冒頭に 3 panel summary を追加し、主要判断の後ろに raw URL、生返答、今回の条件を維持した
- `app.py` は progress / status の user-facing 文言から `実行ID` と `定期分析ID` を外し、内部 ID は内部状態管理にだけ残した
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を current UI に合わせて更新した

### Preserved

- 新しい LLM 呼び出し、prompt、query planner、scoring algorithm、DB schema、保存項目は追加していない
- `ui/styles.py` は body 側の判断 panel / meter class のみ追加し、共通ヘッダの `render_top_nav()`、`.top-shell`、`.nav-link`、`.top-logo-*` は変更していない
- コトミガキ側の文章生成、ページ制作、修正実行、1クリック改善に当たる機能は追加していない

## 2026-04-25 User Simulation PC UI Follow-up

### What Changed

- `ui/detail_views.py` は、`今回の結果` が session-scoped の空状態でも `保存済み質問ごとの結論` の select から保存済み DB の結果詳細を開けるよう更新した
- 保存済み結果として開く場合は detail card の chip を `保存済み結果` とし、current-run 面を旧結果で埋めない方針は維持した
- `app.py` は非表示タブ内 Plotly chart の既知 resize 例外だけを browser error として surface しないようにし、他の console / page error は引き続き検出できる形にした
- `ui/admin_views.py` は `batch_job_id` のような内部 ID を設定タブへ出さないようにし、`__UI_TEST__...` のような test-only 保存名は `保存済み質問セット` / `定期分析` の user-facing label に寄せた

### Preserved

- 新しい LLM 呼び出し、prompt、query planner、scoring algorithm、DB schema は追加していない
- 共通ヘッダの `render_top_nav()`、`.top-shell`、`.nav-link`、`.top-logo-*` は変更していない
- コトミガキ側の文章生成、ページ制作、修正実行、1クリック改善に当たる機能は追加していない

## 2026-04-25 Commercial Value First View Refinement

### What Changed

- `ui/result_cards.py` の `今回の結論` カードで、`AIの主要な参照先` の share bar を自社引用率より上へ移動し、自社 / 比較対象 / 外部サイトの参照バランスを first view の主判断にした
- first view の `頻出論点` カード上部に、既存 `build_losing_prompt_heatmap_rows()` を使った `改善優先の質問` Top 3 を compact 表示として追加した
- `根拠に使われたサイト` の表示を `AI回答に使われた主要ソース` へ寄せ、Top 3 の順位、ページ名、host、所有区分、採用回数、短い influence bar で読める形へ更新した
- `ui/detail_views.py` の冒頭を `改善判断サマリー` にし、今回の結論、改善優先の質問、AI回答に使われた主要ソース、次に強化すべき論点を先に見せる順へ並べ替えた
- `今回の条件` は detail の最下部に維持し、raw URL と生返答は主要判断の後ろに置いた
- `ui/styles.py` は body 側の ranking / priority question / influence bar class のみ追加し、共通ヘッダの `render_top_nav()`、`.top-shell`、`.nav-link`、`.top-logo-*` は変更していない

### Preserved

- 新しい LLM 呼び出し、prompt、query planner、scoring algorithm、DB schema は追加していない
- `keyword_result`、`source_url`、`run_session`、query rollup、topic signal、citation evidence の既存データだけを使っている
- コトミガキ側の文章生成、ページ制作、修正実行、1クリック改善に当たる機能は追加していない

## 2026-04-24 Competitive Value Visualization Plan

### What Changed

- `docs/COMPETITIVE_VALUE_VISUALIZATION_PLAN_2026-04-24.md` を追加し、競合比較後の高付加価値 UI 方針を実装 plan として固定した
- `docs/DOC_STATUS.md` に同 plan を追加し、`UI_REDUCTION` 後続の見せ方改善 plan として参照順へ入れた
- `docs/session_notes/COMPETITIVE_VALUE_VISUALIZATION_NEXT_WINDOW_PROMPT_2026-04-24.md` を追加し、別ウインドウ開始用 prompt と検証手順を固定した
- `docs/session_notes/NEXT_WINDOW_PROMPT.md` を今回の新 prompt へ向けた
- `ui/result_cards.py` に `AIが先に見ている相手` の競合スナップショットと、頻出論点カード内の次の改善 strip を追加した
- `ui/detail_views.py` に `負けている質問` のミニヒートマップと `回答に効いた根拠サイト` ランキングを追加した
- `ui/result_story_builders.py` に、既存 evidence / prompt family / page gap 集計を UI 用に整形する view-model helper を追加した
- `ui/styles.py` に競合スナップショットとミニヒートマップの CSS を追加した。共通ヘッダの `.top-shell` / `.nav-link` / logo 周辺は変更していない

### Decision

- `kotomegane` / `notecode` / `aio2-main` の共通ヘッダ、濃ブラウン nav、orange-brown CTA、ロゴ導線は触らない
- 新しい LLM 呼び出し、prompt、query planner、スコアリング、DB schema は追加しない
- 既存の citation / evidence / topic signal / run_mode を使い、`競合スナップショット`、`負け質問ミニヒートマップ`、`引用元影響ランキング`、`次の改善 strip` を見せ方だけで追加する方針にした
- 手動スポット確認は定期分析 KPI の母数へ混ぜず、必要な場合も参考系列として薄色・点線で扱う
- UI 走査確認は、API key 不要の `Level 2` 描画確認と、API key / コスト許容がある場合のみ実施する `Level 3` live output smoke に分ける

### Verified

- `.\\.venv\\Scripts\\python.exe -m py_compile app.py ui\\result_cards.py ui\\result_story_builders.py ui\\detail_views.py ui\\charts.py ui\\styles.py`
- `.\\.venv\\Scripts\\python.exe -c "import app; print('IMPORT_OK')"`
- `.\\.venv\\Scripts\\python.exe -m unittest tests.test_security_hardening`
- 合成 rows / evidence による view-model smoke で、競合スナップショット、引用元影響ランキング、負け質問ヒートマップ、次の改善 strip の出力を確認した
- Playwright headless で `http://127.0.0.1:8083/` の shell 表示を確認した。起動済みプロセスは session-scoped current result が空だったため、追加した結果内ブロックの DOM 表示は未確認

## 2026-04-23 Security Hardening Follow-up

### What Changed

- `app.py` は `ui_host` が loopback 以外なら warning で継続せず、fail-closed で起動拒否するよう更新した
- `app.py` の `定期リサーチ｜今すぐ実行` は `run_budget_guardrail_usd` 超過を warning で流さず、開始前に停止するよう更新した
- `analysis_core/metrics.py` と `storage.py` は、未import batch の予約コストを `batch_job.reserved_cost_usd` と残件数から日次予算へ織り込み、manual / batch / scheduled の guardrail 判定をそろえた
- `scheduler_runtime.py` は run guardrail だけでなく、日次 guardrail も preflight / query planning 後の両方で再評価してから投入するよう更新した
- `analysis_core/trends.py` は `raw_results.csv` / `weekly_summary.csv` の文字列を spreadsheet formula injection 対策込みで安全化してから出力するよう更新した
- `tests/test_security_hardening.py` を追加し、予約コスト考慮と CSV safe export の最小テストを追加した

### Verified

- `.\\.venv\\Scripts\\python.exe -m py_compile app.py analysis_core\\metrics.py analysis_core\\trends.py scheduler_runtime.py storage.py ui\\dashboard_view_models.py tests\\test_security_hardening.py`
- `.\\.venv\\Scripts\\python.exe -m unittest tests.test_security_hardening`
- `.\\.venv\\Scripts\\python.exe -c "import app; print('IMPORT_OK')"`

## 2026-04-23 Current Result Read-Stability

### What Changed

- `app.py` の periodic refresh は、`今回の結果` を表示中は `refresh_dashboard_surface()` を呼ばず、hero status だけ更新するよう変更した
- `ui/detail_views.py` の `この画面で分かること`、`見つかったが根拠には使われなかったURL`、`まだ確認が必要なURL` は `ui.expansion(...)` をやめ、固定表示の整理済みセクションへ変更した
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を current 実装へ合わせ、分析後の閲覧面は background refresh で崩さない current shape を追記した

### Why

- 分析後にユーザーが読んでいるのは `今回の結果` と `結果詳細` なので、periodic refresh でそこを再描画する必要はなかった
- 結果詳細の折りたたみは、再描画時に閉じて読解を中断させる要因になっていた
- background refresh は軽い status 更新だけに寄せ、詳細は固定レイアウトで安定して読める方が現行 PoC の用途に合う

## 2026-04-23 Security Signal UI Reduction

### What Changed

- `ui/result_cards.py` と `ui/detail_views.py` から `命令文混入` / `要確認` 系の warning 文言と chip を外した
- `llmo_core/openai_client.py` の prompt injection signal は `user query` と `model output` 全文を検知対象から外し、`search source title / URL` 中心へ絞った
- signal 検知時に `recommended_actions` を `人手確認` 系文言へ強制上書きする処理を外し、内部では `confidence=low` と signal 保存だけを維持するよう更新した
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を current 実装へ合わせ、security signal は internal 扱いで UI へ常時露出しない current shape を追記した

### Why

- 現状の warning 文言は、検知が入っただけで user-facing の first view / detail に強い不安文言が出ており、結果の読解を阻害していた
- 検知対象に `user query` や `model output` 全文を含めると、検索由来ではない文字列まで拾って false positive を起こしやすかった
- security signal は内部の保守的な判定に使えば足り、現行 PoC の主要導線では直接見せない方が UX と整合する

### Verified

- `.\\.venv\\Scripts\\python.exe -m py_compile llmo_core\\openai_client.py ui\\result_cards.py ui\\detail_views.py`
- `.\\.venv\\Scripts\\python.exe -c "import app; print('IMPORT_OK')"`

## 2026-04-23 Guardrail And Runtime Hardening

### What Changed

- 手動実行 (`分析を実行`) は、質問数や内部拡張で見積件数が増えても事前 warning toast を出さない current shape に変更した
- `定期リサーチ｜今すぐ実行` と scheduler dispatch は、query plan 展開後の `execution_plan.total_request_count` を使って guardrail を再評価してから投入するよう更新した
- `analysis_core/text_utils.py` の prompt injection 検知は、ゼロ幅文字除去と role-change / context-reset 系の追加パターンを入れて前処理を強化した
- `llmo_core/openai_client.py` の Batch JSONL 一時ファイルは `NamedTemporaryFile(delete=False)` から `mkstemp` ベースへ切り替え、失敗時は即削除するよう更新した
- `storage.py` の migration helper に table / column の allowlist を追加し、`PRAGMA table_info(...)` と `ALTER TABLE ... ADD COLUMN ...` の対象名を固定化した
- `app.py` は `ui_host` が loopback 以外のとき、認証なしでネットワーク公開される旨を起動時 warning で明示するよう更新した

### Why

- 手動実行は exploratory に質問を増やして試すケースが多く、件数増加だけで warning toast を出す方針をやめた
- 一括 / 定期は実際の内部拡張後の送信件数で見積もらないと、run guardrail が過小評価になりやすかった
- prompt injection 検知は page body そのものまでは見られないが、少なくともゼロ幅文字や自然文ベースの典型パターンにはもう少し強くしておくほうが安全だった
- Batch 入力ファイルは短命でもローカル平文で残るため、失敗時 cleanup を明示したほうが安全だった

### Verified

- `.\\.venv\\Scripts\\python.exe -m py_compile app.py analysis_core\\metrics.py analysis_core\\text_utils.py llmo_core\\openai_client.py scheduler_runtime.py storage.py`
- `.\\.venv\\Scripts\\python.exe -c "import app; import scheduler_runtime; print('IMPORT_OK')"`

## 2026-04-21 Periodic Refresh Scroll Stabilization

### What Changed

- `app.py` の client 背景 task で走る periodic refresh を、結果データの signature が変わった時だけ `refresh_dashboard_surface()` する形へ変更した
- periodic refresh で dashboard surface を再描画する場合は、直前の `window.scrollX / scrollY` を保存し、描画後の `requestAnimationFrame` で復元するようにした
- 通常の手動実行完了や設定変更で `refresh_dashboard_surface()` が走った後は、periodic refresh 用 signature も更新するようにした
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` に、分析結果閲覧中の初期位置戻りを抑える current state を追記した

### Why

- `periodic_refresh_loop()` は 180 秒ごとに `refresh_dashboard_surface()` を呼び、結果カード・詳細・根拠セクションの `container.clear()` を伴う再描画をしていた
- 分析結果を読んでいる最中にこの再描画が入ると、ブラウザのスクロールアンカーが崩れて画面が初期位置へ戻る可能性が高い
- データが変わっていない時のフル再描画は不要なので、差分なしの periodic refresh は hero status 更新だけに絞った

### Verified

- `.\\.venv\\Scripts\\python.exe -m py_compile app.py`
- `.\\.venv\\Scripts\\python.exe -c "import app; print('IMPORT_OK')"`

## 2026-04-21 Top-Level Research Access

### What Changed

- `app.py` の `実行` カードに、トップから見える **`定期リサーチ｜今すぐ` / `自動で継続を設定`** quick access を追加した
- 同カードの補助文を、`分析を実行` だけでなく **`今回を確認する / 継続観測を始める`** の二択として読める文言へ更新した
- `ui/admin_views.py` と `app.py` に残っていた `定期チェック` 表示を `定期リサーチ` へそろえ、schedule table / status / compare / delete dialog の語彙を統一した
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を current 実装へ合わせ、トップから定期リサーチへ直接入れる current shape を追記した

### Why

- 継続観測系プロダクトでは、単発分析よりも **継続監視 / トレンド / 競合比較** が主役になりやすい
- `コトメガネ` でも `手動` と `定期リサーチ` は上下関係ではなく並列の主機能として見せたほうが、プロダクトの価値と整合する
- 従来は `定期リサーチ` の認知はできても、開始導線が detail / 設定 側に 1 段深く、トップからの着手性が弱かった

### Verified

- `.\\.venv\\Scripts\\python.exe -m py_compile app.py ui\\admin_views.py`
- `.\\.venv\\Scripts\\python.exe -c "import app; print('IMPORT_OK')"`

## 2026-04-21 Screen-Review Compaction

### What Changed

- `Peec` / `Scrunch` / `Semrush` の現行トップ画面とローカル `8083` を実画面比較し、first fold の重複文言を削った
- `app.py` から `手順 1/2/3` 見出し、`質問を入力する` などの重複タイトル、`継続観測` の説明カードを外し、実行ボタン群へ集約した
- hero copy は 1 文へ短縮し、`前回比` カードの補助説明も外した
- `実行` カードは `実行モード` + 3 CTA の current shape に更新し、右カラムの補足説明も 2 行から 1 行へ圧縮した
- `観測の推移` カードの説明文も削り、見出しとグラフ中心で読めるようにした

### Why

- 他社トップは `カテゴリ名 / 価値訴求 / 主要 CTA / ダッシュボード絵` を first fold で読ませており、重複説明をほとんど置かない
- `コトメガネ` は previous shape だと、同じ意味の説明が hero、stage header、入力導線、実行導線に分散していた
- 文言を削ることで、`単発確認` と `継続観測` の 2 モードが first fold で同格に見え、`今回の結果` と `観測の推移` まで一画面で届きやすくなる

### Verified

- `.\\.venv\\Scripts\\python.exe -m py_compile app.py ui\\admin_views.py`
- `.\\.venv\\Scripts\\python.exe -c "import app; print('IMPORT_OK')"`
- Playwright headless で再取得した `tmp/ui_compare_2026-04-21/kotomegane_local_viewport_compacted.png` を確認

## 2026-04-21 Execution Mode Label Clarification

### What Changed

- トップの実行 CTA を `分析を実行 / 定期リサーチ｜今すぐ / 自動で継続を設定` から **`1回だけ分析 / 複数質問を一括分析 / 自動観測を設定`** へ変更した
- 設定側の expansion も `定期リサーチ｜今すぐ実行（バッチ）` から `定期リサーチ｜複数質問を一括分析` へ変更し、first view から内部語 `バッチ` を外した
- `実行モード` の補助文を `1回だけ見る / 複数質問を見る / 自動で追う` の 3 択に整理した

### Why

- Hick の法則では、見た目上の選択肢が増えるほど判断時間が伸びる。previous shape は `分析を実行` と `定期リサーチ｜今すぐ` が「どちらも今すぐ実行」に見え、選択肢の意味が重なっていた
- Nielsen の `Match between system and real world` と `Recognition rather than recall` の観点では、`バッチ` や `今すぐ` より `1回だけ / 複数質問 / 自動観測` のほうがユーザーの目的に近い
- 他社トップは内部実行方式ではなく、ユーザーの目的・成果で CTA を分けているため、それに寄せた

### Verified

- `.\\.venv\\Scripts\\python.exe -m py_compile app.py ui\\admin_views.py`
- `.\\.venv\\Scripts\\python.exe -c "import app; print('IMPORT_OK')"`

## 2026-04-21 Completion-Based Billing Direction

### What Changed

- `billing_rules.py` の microcopy を `batch 作成時点で消費` から **結果反映完了時に消費** へ更新した
- `docs/SAAS_IMPLEMENTATION_PLAN_2026-04-03.md` の fixed billing rule を、手動も batch も **実行完了時消費** に更新した
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` に、将来の実クレジット台帳での完了条件を追記した

### Completion Rule

- `manual`: 成功結果を保存し、`run_session.finished_at` が入った時点で消費
- `batch / scheduled`: provider batch の作成・投入時点では消費せず、import が終わり、`batch_job.imported_at` が入った時点で消費
- validation error / provider submit failure / user cancel / import 不能の失敗は消費しない
- 将来の台帳実装では `run_id` / `batch_job_id` を idempotency key にして二重消費を防ぐ

### Verified

- `.\\.venv\\Scripts\\python.exe -m py_compile billing_rules.py`

## 2026-04-20 定期リサーチ Rename And Value Surface

### What Changed

- 今回の実装作業は **Cursor セッション** で完了し、この entry はその最終報告を handoff / snapshot として整理した
- `app.py` / `ui/admin_views.py` / `ui/dashboard_refreshers.py` / `config.py` / `run_policy.py` / `billing_rules.py` の UI 文言・microcopy・内部ラベルを `まとめて確認` / `自動更新` / `定期チェック` から **定期リサーチ** に統一した
  - `まとめて確認` → `定期リサーチ｜今すぐ実行（バッチ）`
  - `自動更新` → `定期リサーチ｜自動で継続（スケジュール）`
  - ボタン `まとめて開始` → `今すぐ実行`（accent button にトーンアップ）
  - `batch_job_id` や `run_mode=batch/scheduled` などの DB / 内部キーは互換性のためそのまま残し、表示レイヤだけ差し替えた
- `app.py` の detail expansion に **「定期リサーチ」タブ** を追加（`今回の結果 / 定点計測 / 定期リサーチ / 設定`）。導線説明と `設定タブで開く / 定点計測タブで推移を見る` ショートカットを配置し、設定深部を掘らずに意図を伝えられるようにした
- `app.py` の hero に **ロゴマーク / サブタイトル `LLM見え方観測` / `コトミガキ`・`コトメイク` への cross-link / `前回比` カード** を追加し、sister services（`コトミガキ` / `コトメイク`）と視覚トーンとレイアウトを揃えた
- `app.py` の first view に **`観測の推移` カード（`自社引用率と外部先行率` の折れ線 + 最新 自社引用率）** を常時表示として追加し、定期リサーチで貯まる履歴が expansion を開かずに見えるようにした
- `refresh_hero_status()` を拡張し、scoped rows / `build_previous_delta_summary` / `filter_rows_for_tracking_series` を使って hero 前回比カードと推移グラフを定期的に更新するようにした

### Why

- LLMO ツールとしての価値は「**LLMの見え方を繰り返し観測し、推移として読む**」ことであり、`バッチ設定` は UX 上も名前上もユーザに意図を伝えづらかった。`定期リサーチ` に改名することで、単発の `分析を実行` と明確に役割を分ける
- `定期リサーチ` 系機能は設定タブの深い expansion 二段に閉じていたため、初見では value が伝わらなかった。detail 階層にタブとして surface し、hero 直下に常時見える推移グラフを置くことで「継続観測と推移」を主役に引き上げる
- `techie-hub/start.bat` から立ち上がる `コトメイク` / `コトミガキ` / `コトメガネ` 3 サービスでデザイントークン (brand color / hero layout) は既に揃っていたが、`コトメガネ` の hero だけはロゴマーク非表示・サブタイトル無しで孤立していたため、視覚トーンを合わせた
- suite 内の `観測 → 改善実行` の動線を hero cross-link で明示し、`コトメガネは観測・判断、コトミガキが改善実行` という役割分担を UI で伝えるようにした

### Verified

- `.\\.venv\\Scripts\\python.exe -m py_compile app.py config.py run_policy.py billing_rules.py ui\\admin_views.py ui\\dashboard_refreshers.py` -> `EXIT=0`
- `.\\.venv\\Scripts\\python.exe -c "import app; print('IMPORT_OK')"` で import smoke を確認した
- `http://127.0.0.1:8083/` は `HTTP 200`、`content length 203867` を確認した
- `ReadLints` はエラーなし
- `まとめて確認` / `自動更新` の残存検索は docs/research/archive 以外で 0 件に収束した

## 2026-04-20 Market Mode Query-Only Fix

### What Changed

- `llmo_core/prompts.py` と provider client を更新し、`market` mode の LLM 入力は `user query only`、`owned-only audit` だけが target-aware prompt を使うよう更新した
- `analysis_core/structures.py` と `storage.py` を更新し、`target_domain_hit` は回答文中の単純なドメイン文字列一致ではなく citation URL / source URL ベースで判定するよう補強した
- `app.py` に、`市場観測では自社URLなどを AI に送らずローカル照合に使う` 旨の補助文を追加した
- `README.md`、`docs/CURRENT_STATE_2026-03-30.md`、`ALGORITHM.md` を現物へ合わせて更新した

### Why

- `市場観測` で自社URLや名称を prompt に含めると、user query only の自然な観測ではなく `対象を与えた評価` に寄りやすかった
- 回答文中の `見当たりませんでした` のような否定文でもドメイン文字列だけで `自社が見つかった` と読まれる false positive があり、悪い結果を過小表示するリスクがあった

### Verified

- `market` mode の payload から `target_domain`、`brand_terms`、`competitor_terms`、`market_context_terms` が落ちることをローカル確認した
- 否定文のみで citation に自社URLがないケースで `owned_domain_hit=False` になることをローカル確認した
- `.venv\\Scripts\\python.exe -m py_compile app.py llmo_core\\openai_client.py llmo_core\\gemini_client.py llmo_core\\claude_client.py llmo_core\\prompts.py analysis_core\\structures.py storage.py`
- `.venv\\Scripts\\python.exe -c "import app; print('ok')"`

## 2026-04-20 Analysis Click Response Fix

### What Changed

- `app.py` の manual run は、クリック直後に `refresh_dashboard_surface()` を呼ばず、実行カードの progress / status を先に返すよう更新した
- `app.py` の起動条件は `__main__` のみに絞り、Windows の `__mp_main__` で `ui.run(...)` を再実行しないよう更新した
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を現物へ合わせて更新した

### Why

- `分析を実行` 押下時に全画面再描画が先に走ると、WebSocket の click event を受けても最初の UI 反映が詰まり、`反応なし` に見えていた
- `__mp_main__` での app 起動許可は Windows 子プロセス側の bind 競合要因になりうるため、安全側へ寄せた

### Verified

- `.venv\\Scripts\\python.exe -m py_compile app.py`
- `.venv\\Scripts\\python.exe -c \"import app; print('ok')\"`
- Playwright headless で `分析を実行` 押下後に `分析中です`、activity 文言、`分析を停止` が表示されることを確認した

## 2026-04-20 Click Feedback UX Hardening

### What Changed

- `app.py` の manual run は、クリック直後に CTA 文言を `準備中...` へ切り替え、押下が受理されたことを先に見せるよう更新した
- progress bar の下に activity 行を追加し、query planning 中も `現在 / 状態` を短文で出せる current shape にした
- manual run の初期 progress は 1-2% の控えめな変化ではなく、準備フェーズだと分かる程度に少し進めた
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を現物へ合わせて更新した

### Why

- `分析を実行` 押下から最初の network request まで数秒空く場合、progress bar だけでは `クリックできたのか / 固まったのか` が伝わりにくかった
- Nielsen の `visibility of system status` の観点では、押下直後に `受理済み / 準備中` を複数の手掛かりで返したほうが安全だった

### Verified

- `py_compile` と `import app` を再実行し、manual run 初動の UI 追加で起動が壊れていないことを確認した

## 2026-04-20 Service Worker Cleanup And Click Verification

### What Changed

- `app.py` に `/flutter_service_worker.js` を追加し、旧 Flutter 系 service worker を unregister する no-op script を返すよう更新した
- `render_page()` の head script で、既存 service worker の解除と cache 削除を起動時に走らせるよう更新した
- `分析を実行` の CTA 文言は current 実装に合わせて `分析中...` へ切り替えるよう補正した
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を現物へ合わせて更新した

### Why

- `localhost:8083` に旧アプリの service worker が残ると、古いキャッシュや別画面断片が混ざり、`分析を実行` の反応確認と UI 観測を阻害していた
- click event 自体は通っていても、古い cache が干渉すると `押せていない` のか `画面が汚染されている` のか切り分けにくかった

### Verified

- `.venv\\Scripts\\python.exe -m py_compile app.py`
- `.venv\\Scripts\\python.exe -c "import app; print('import ok')"`
- `stop.ps1` で 8083 を停止後、`.venv\\Scripts\\python.exe app.py` を再起動し、`http://127.0.0.1:8083/` と `http://127.0.0.1:8083/flutter_service_worker.js?v=4252275541` がともに HTTP 200 を返すことを確認した
- Playwright headless で `navigator.serviceWorker.getRegistrations().length == 0`、`flutter_service_worker.js` request 0 件、`分析を実行` click event 後に本文へ `分析中です` / `分析中...` / `分析を停止` が出ることを確認した

## 2026-04-20 Manual Run Warm Start Progress

### What Changed

- `app.py` の `on_run()` は `分析を実行` 押下直後に progress bar を 0 のまま表示せず、query plan 準備中の最初の 1% を先に描画するよう更新した
- run session 発行後にも 2% へ進め、query planning が返るまでの間に `押したが動いていない` と見えにくい current shape にした
- query plan が確定して実母数へ切り替わる時点でも、0% へ戻さず最小 progress を保つよう補強した
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を現物へ合わせて更新した

### Why

- manual run の最初の可視変化が遅く、planner 準備中に bar が空のままだと接続断や無反応に見えやすかった
- 左下の `Connection lost` toast と重なると、実際には準備中でも `落ちた` ように誤読されやすかった

### Verified

- `py_compile` と `import app` を再実行し、manual run 初動の progress 表示ロジックが通ることを確認した

## 2026-04-20 Connection Stability Hardening

### What Changed

- `C:\tetie\techie-hub\start.bat` の `kotomegane` 起動は、`8083` が listen 済みでも `http://127.0.0.1:8083/` に応答しない listener を `already running` 扱いしないよう更新した
- unresponsive listener を検知した場合は `stop.ps1` で 8083 を落としてから `run.ps1` を再起動し、起動後も HTTP health check を待つ current shape にした
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を現物へ合わせて更新した

### Why

- `kotomegane` だけ `techie-hub\logs\kotomegane.log` に `ConnectionResetError: [WinError 10054]` が残っており、ブラウザ切断時の接続揺れが他アプリより表面化していた
- `techie-hub\start.bat` は従来 `8083` の LISTEN だけを見ていたため、壊れた既存 listener を再利用し続けて「接続が不安定」に見えやすかった

### Verified

- `C:\tetie\techie-hub\start.bat force` 後に `http://127.0.0.1:8083/` の HTTP 200 を確認した
- 8083 listener の親子プロセスが `.venv\Scripts\python.exe -> base python.exe -> app.py` の期待どおりで復帰することを確認した

## 2026-04-20 Detail Copy Simplification

### What Changed

- `ui/detail_views.py` の最下部折りたたみを、仕組み説明ではなく `この画面で分かること` を伝える文へ差し替えた
- URL 状態は `判定保留 / 候補` ではなく、`根拠に使われた / 見つかったが未採用 / 確認が必要` の平易な語へ寄せた
- `ui\evidence_presenters.py`、`ui\result_cards.py`、`ui\result_story_builders.py` の関連文言も同じ語彙にそろえ、detail だけ別の言い回しが残らないよう更新した
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を現物に合わせて更新した

### Why

- 現状の折りたたみは内部判断の説明が前面に出ており、非専門ユーザーには「何を見せている画面か」が直感で伝わりにくかった
- detail 側でも first view と同じく、アルゴリズム説明ではなく「根拠に使われたか」「あと一歩だったか」を先に読めることを優先した

## 2026-04-20 Trial Count Fallback Hardening

### What Changed

- `ui/detail_views.py` の結果詳細内訳は `len(group_rows)` ではなく `trial_count / answer_observation_count / result_count` を優先して合算するよう更新した
- raw row が欠けて rollup row に fallback した場合でも、`n=1` に潰れず保存済みの観測回数をそのまま母数に使うよう補強した
- user-facing copy の `質問群` と `回答試行ベース` を `観測回数ベース` へ寄せ、`app.py` の進捗文言からも `質問群` を外した
- `ui/result_story_builders.py` の質問タイプ別サマリーも row 数依存ではなく `trial_count` 重みで計算するよう更新した
- `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を現物へ合わせて更新した

### Why

- 同じ質問でも `n=10` 回と `n=100` 回では観測の確かさが違うため、user-facing の母数は常に実際の観測回数で読む必要がある
- current result 復元や rollup fallback が入ったときに `1件` 扱いへ縮むと、今日直した母数整理が UI 上で壊れて見える

### Verified

- `run_c33c228c91134ed3aa2df7874f296038` の rollup row だけを `build_trial_basis_counts(...)` に渡しても `trial_count=40` を返すことを確認した

## 2026-04-20 First View Citation Simplification

### What Changed

- first view 左カードの主指標を `自社引用率` のみに絞り、`自社露出率` は first view から外した
- 左カードの headline / summary は `露出` ではなく `実際に引用されたか` を中心に読む文へ寄せた
- 中央カードは `主な参照元サイト` を `根拠に使われたサイト` へ寄せ、`観測した n 試行のうち m 回` の説明を外した
- 根拠サイト / 根拠ページの小カードも回数説明をやめ、`今回よく使われた` ことだけが分かる短文へ整理した

### Why

- `自社露出率` と `自社引用率` を並べると、引用されていない候補や言及まで main metric に見えてしまう
- 中央カードはアルゴリズム説明より、`今回はどこが根拠に使われたのか` がすぐ分かることを優先した

### Verified

- `py_compile` と `import app` を再実行し、8083 を再起動して HTTP 200 を確認した

## 2026-04-20 Trial-Based User-Facing Metrics

### What Changed

- user-facing の母数を `distinct executed_query` ではなく `観測した試行数` に切り替えた
- `analysis_core/metrics.py` は rollup row に `trial_count / visible_trial_count / owned_citation_trial_count / external_lead_trial_count` を持たせ、定点計測 KPI も試行合算で計算するよう更新した
- `ui/result_story_builders.py` の first view、参照元サイト頻度、質問タイプ別サマリー、保存済み累積傾向を試行ベースへ更新し、`質問群ベース` `質問率` `全質問 n件中 m件` の copy を外した
- `ui/detail_views.py` は内訳と割合を `試行ベース` へ更新し、`20試行中 12回` の読み方に統一した
- `ui/dashboard_refreshers.py`、`ui/dashboard_views.py`、`app.py`、`ui/charts.py`、`ui/admin_views.py` の KPI / hover / 表ラベルも `観測した n 試行のうち m 回` にそろえた
- `README.md`、`docs/CURRENT_STATE_2026-03-30.md`、`docs/RESULT_UX_IMPLEMENTATION_PLAN_2026-04-14.md`、`ALGORITHM.md` を現物へ合わせて更新した

### Why

- この PoC の価値は、同じ質問を複数回投げたときの揺れそのものにある
- そのため、A を 20 回、B を 20 回試した場合は、user-facing の母数も 40 試行として読むのが自然であり、distinct question 数ではズレが出る

### Verified

- 実装後に `py_compile` / `import app` を実行して最低限の確認を行う

## 2026-04-20 First View Hierarchy And Mobile Compression

### What Changed

- hero の補助文を 1 文へ圧縮し、first view 直前の補助文も 1 行に縮めた
- 主結果 3 カードの hierarchy を再調整し、`今回の結論` を最も強く、`主な参照元サイト` と `頻出論点` を静かな面へそろえた
- `ui/result_story_builders.py` の参照元集計に first view 用の `focus_items` を追加し、中央カードは `ページ名 + サイト名 + 何件の質問で使われたか` の上位 3 件だけを表示する current shape に更新した
- 右カードの論点群は `よく扱われる論点 / 次に足す論点` の 2 群だけに整理し、chip 数を削減した
- `今回だけの整理` と `保存済みの累積傾向` を別 surface に分け、current result と saved aggregate の視覚差を広げた
- `ui/styles.py` で panel-card と expansion のトーンを一段落とし、mobile では hero/status/card の padding と chip サイズを縮めた
- `README.md`、`docs/CURRENT_STATE_2026-03-30.md`、`ALGORITHM.md` を現物に合わせて更新した

### Verified

- `.venv\\Scripts\\python.exe -m py_compile app.py ui\\result_cards.py ui\\result_story_builders.py ui\\detail_views.py ui\\styles.py`
- `.venv\\Scripts\\python.exe -c "import app; print('ok')"`
- Playwright で `logs\\ui_ux_refresh_desktop_2026-04-20.png` と `logs\\ui_ux_refresh_mobile_2026-04-20.png` を再取得し、2026-04-14 の mobile screenshot より hero と first view 上部の縦積みが減っていることを確認した

## 2026-04-20 Nielsen UX Task Breakdown

### What Changed

- heuristic review の結果を `docs/RESULT_UX_IMPLEMENTATION_PLAN_2026-04-14.md` に task 化した
- `desktop = 中程度 / mobile = やや高い` の認知負荷評価を current judgment として固定した
- 実装タスクを `first view 優先度整理 / card 密度削減 / hierarchy 強化 / mobile 圧縮 / recognition cleanup` の 5 群に分けた
- `TASK.md` に current UX tasks の短い実行入口を追加した

### Notes

- 今回は task 化のみで、UI 実装修正は未着手
- 次の実装は `Task Group A: First View Priority Tightening` から着手する

## 2026-04-20 First View Source And Topic Shift

### What Changed

- first view の主結果 3 カードを `今回の結論 / 主な参照元サイト / 頻出論点` に更新した
- `ui/result_story_builders.py` に、引用元を `ページ名 + サイト名 + 何件の質問で使われたか` へ変換する質問数ベース集計を追加した
- `ui/result_cards.py` は `引用されやすい質問` カードを外し、`主な参照元サイト` と `頻出論点` を先に読む構成へ更新した
- support 側の insight card と展開ラベルも `主な参照元サイト` にそろえ、raw URL は詳細側でだけ確認する current shape に更新した
- `README.md`、`docs/CURRENT_STATE_2026-03-30.md`、`ALGORITHM.md` を現物に合わせて更新した

### Verified

- `.venv\\Scripts\\python.exe -m py_compile app.py ui\\result_story_builders.py ui\\result_cards.py`
- `.venv\\Scripts\\python.exe -c "import app; print('ok')"`

## 2026-04-20 Question Count Denominator Unification

### What Changed

- `定点計測` の KPI は `自社露出率 / 自社引用質問率 / 外部先行質問率 / 前回比` に整理し、user-facing の割合と件数をすべて `対象質問数` ベースへ統一した
- `ui/dashboard_refreshers.py` と `analysis_core/metrics.py` の `自社引用シェア` は廃止し、`対象質問 n件中 m件で自社URLが引用` の形へ変更した
- `ui/result_story_builders.py` の質問タイプ別サマリーも `全質問 n件中 m件` 基準へそろえ、各タイプ内だけの別母数を出さない current shape に更新した
- `ui/detail_views.py` は URL 件数ベースの要約 card を外し、質問群ベースの件数と割合だけを表示する形へ整理した
- `README.md`、`docs/CURRENT_STATE_2026-03-30.md`、`ALGORITHM.md` を現物に合わせて更新した

### Verified

- `.venv\\Scripts\\python.exe -m py_compile app.py analysis_core\\metrics.py ui\\dashboard_view_models.py ui\\dashboard_views.py ui\\dashboard_refreshers.py ui\\result_story_builders.py ui\\detail_views.py ui\\result_cards.py ui\\admin_views.py`
- `.venv\\Scripts\\python.exe -c "import app; print('ok')"`

## 2026-04-15 Question Type Denominator Fix

### What Changed

- `ui/result_story_builders.py` の `build_question_axis_summary` は質問タイプ別の件数を raw 行数ではなく `executed_query` 単位で集計するよう修正した
- 同じ拡張質問に対する繰り返し回答は 1 母数にまとめ、`見つかる / 引用される / 外部先行` はその実行クエリ内で OR 集約する形へそろえた
- これにより、左カードの `質問群ベース` 指標と中央カードの `料金説明は 20件中12件` のような件数表現の母数ずれを解消した

### Verified

- `.venv\\Scripts\\python.exe -m py_compile ui\\result_story_builders.py app.py`
- `.venv\\Scripts\\python.exe -c "from ui.result_story_builders import build_question_axis_summary; print('import ok')"`

## 2026-04-14 Manual Parallel Search And Progress Sync

### What Changed

- `app.py` の manual run は、query plan 作成後に `元質問 x 繰り返し` ごとの並列グループを作り、その中の拡張質問を同時実行する形へ更新した
- 進捗バー、`元質問 x/y / 拡張質問 x/y / 繰り返し x/y` の detail、実行中の summary copy は同じ完了数を使うようそろえ、`キャッシュ入力` や `最新エラー` は補助文へ逃がした
- `分析を停止` の best-effort cancel は `現在の並列グループ` 基準の文言へ更新した
- `docs/CURRENT_STATE_2026-03-30.md`、`README.md`、`ALGORITHM.md` を現物に合わせて更新した

### Verified

- `.venv\\Scripts\\python.exe -m py_compile app.py`
- `.venv\\Scripts\\python.exe -c "import app; print('ok')"`

### Notes

- live provider を使った長時間 run の再計測までは未実施
- 並列数は `元質問ごとの拡張質問数` に一致し、繰り返し全体を一度に並列化してはいない

## 2026-04-14 Result UX Implementation Plan

### What Changed

- `docs/RESULT_UX_IMPLEMENTATION_PLAN_2026-04-14.md` を追加し、`見え方観測` の結果画面を質問群ベースへ統一したうえで再構成する実装 plan を固定した
- 対象範囲を `母数の整理 / first view 3 cards の再定義 / 非テキスト可視化 / 進捗表示 / detail への退避` に限定した
- first release の visual component は `Question Type Heatmap / Citation Opportunity Bubble Strip / Page Opportunity Strip` の 3 点を優先する方針で整理した
- `94%` と `自社引用9件` のような別母数の数字を first view で並べない decision と、`元質問 + 拡張質問` を含む質問群ベースの読み方を plan に明記した

### Notes

- これは実装ではなく plan 追加のみ
- 実装は別ウインドウで着手する前提

## 2026-04-14 Analysis Copy And Contrast Fix

### What Changed

- 主結果 1 枚目の `%` は `自社URLが根拠に入った回答率` と断定しないよう、`今回の自社露出率` として再整理し、`元質問 1件 -> 拡張質問数 -> 合計回答数` の母数を先に出す形へ更新した
- 同じカード内で `自社が見つかった回答` と `実際に自社URLが引用された回答` を分けて表示し、`94%` と `自社引用URL 9件` のような別母数の数字がぶつかって誤読されにくい文言へ寄せた
- 主結果 2 枚目の小さい件数は `自社引用` ではなく `自社の引用URL` など URL 件数だと読めるラベルに変更し、補足文でも `回答回数ではなく引用URL数` と明示した
- その後、first view の情報設計自体を `今回の結論 / どの質問で引用されやすいか / 次の改善` へ再構成した。中央カードは `主な引用元` ではなく `引用されやすい質問` を主役にし、`導入手順 / 比較検討` のような質問傾向を first view で読める形へ寄せた
- 主結果の主指標は `回答回ベース` から外し、first view では `自社が見つかる質問率 / 自社URLが引用される質問率` の 2 指標を質問群ベースで読む current shape に更新した
- 手動実行中の status copy は `元質問 x/y / 拡張質問 x/y / 繰り返し x/y` を出すよう更新し、spinner も `分析中 n/N` で全体進捗を追える形へ寄せた
- `次に強化するページ` カードは dark panel をやめ、suite 共通の light surface + accent top border へ戻した。3 カードの面構成を揃え、右端だけが重く見える状態を解消した
- dashboard 再描画は deleted client の RuntimeError を握りつぶせるようにし、長時間 run 中の切断後に `The parent element this slot belongs to has been deleted.` が再度 surface しにくい形へ補強した

### Verified

- `.venv\\Scripts\\python.exe -m py_compile app.py analysis_core\\metrics.py ui\\result_story_builders.py ui\\result_cards.py ui\\styles.py`
- `.venv\\Scripts\\python.exe -c "import app"`
- `data\\llmo_poc.db` の最新 run (`run_4272ec44f27a43208aa1e9f10185a8d5`) で rollup を再計算し、`元質問1件 / 拡張質問5件 / 50回答 / 自社が見つかった回答47件 / 自社URLが実際に引用された回答27件` の内訳を確認した

### Notes

- `phase_ui_run_stdout_2026-04-14.log` では runtime 起動は正常
- `verify_current_server.log` には旧検証時点の deleted client 例外が残っていたため、今回の patch で guard を追加した

## 2026-04-14 UI Reduction Implementation

### What Changed

- `app.py` の hero から `TECHIE SUITE` box と `活かす材料` を外し、first view を `サービス名 + 一文の価値説明 + 対象AI / 最終更新` の最小構成へ縮めた
- 主入力は `質問 / 自社URL / 名称(任意) / 重点テーマ(任意)` に更新し、`runtime/common.py` の必須チェックも `質問 / 自社URL` のみへ揃えた
- `ui/result_cards.py` の first summary を `AIが先に取り上げた相手 / 主な引用元 / 次に足すもの` に固定し、main surface から `比較候補`、topic chips、`直近の観測サマリー` を外した
- `ui/result_story_builders.py` に first view 用の比較軸つきラベルを追加し、内部判定 `自社優勢 / 自社あり / 外部サイト優勢 / 未露出` を user-facing main copy へ直接出さない形へ寄せた
- `ui/detail_views.py`、`ui/admin_views.py`、`ui/dashboard_refreshers.py`、`ui/runtime_copy_builders.py` の文言を `名称 / 重点テーマ / 主な引用元` に揃えた
- `ui/styles.py` に `text-wrap-anywhere`、`headline-clamp-2` などの overflow utility を追加し、長い質問文、URL、chip が card 幅を崩しにくい current shape に更新した
- `README.md`、`docs/CURRENT_STATE_2026-03-30.md`、`ALGORITHM.md` を現物に合わせ、主入力と first view の current description を更新した

### Verified

- `.venv\\Scripts\\python.exe -m py_compile app.py runtime\\common.py ui\\runtime_copy_builders.py ui\\result_story_builders.py ui\\result_cards.py ui\\detail_views.py ui\\styles.py ui\\admin_views.py ui\\dashboard_refreshers.py`
- `.venv\\Scripts\\python.exe -c "import app"`
- `.\\stop.ps1` 後に `.venv\\Scripts\\python.exe app.py` を短時間起動し、`http://127.0.0.1:8083/` の HTTP 200 を確認した

## 2026-04-14 UI Reduction Plan

### What Changed

- `docs/UI_REDUCTION_IMPLEMENTATION_PLAN_2026-04-14.md` を追加し、別ウインドウでそのまま実装に使える削減仕様を固定した
- `techie-hub` から 3 サービスへ遷移する運用を前提に、色は suite 共通 palette に揃える decision を plan へ明記した
- 対象範囲を `hero の削減 / input の再配置 / ブランド名必須解除 / 結果 card の比較軸明示 / overflow hardening` に限定した
- `TECHIE SUITE` box、`活かす材料`、`直近の観測サマリー`、`論点のつながり` を first view から外す方針を phase ごとに整理した

### Notes

- これは実装ではなく plan update
- 現時点では `README.md` と `docs/CURRENT_STATE_2026-03-30.md` の更新対象ではない

## 2026-04-14 UI Refocus Update

### What Changed

- Phase 0 の preflight として、`入力 / 今回の結果 / 定点計測 / 設定` の baseline screenshot と確認ログを `logs/ui_baseline_*` に保存し、長文説明、`競合` 露出、`共起` 主表示を固定観測した
- 主入力を `質問 / 自社URL / ブランド名 / 目立ちたい領域` に再編し、`競合` を user-facing の main surface から外した。比較したい相手は折りたたみの `比較対象` に下げ、旧データは `competitor_terms` のまま互換維持した
- 質問文から `地域 / 業界 / 用途` を軽量推定する helper を追加し、質問欄近くに `候補` と `反映` ボタンを表示できるようにした。推定値で入力欄を勝手に上書きせず、手入力の `目立ちたい領域` を優先する
- 回答文と citation URL タイトルから他社名・媒体名・団体名を `比較候補` として抽出する helper を追加し、`比較サイト / 団体 / 法人 / 媒体` の軽い分類を付けた。手入力の `比較対象` がある場合はそちらを優先する
- 主画面の hero と結果カードの長文説明を削り、最上段は `見えているか / 何が評価されているか / 自社が強い軸 / 次に足すもの` を主役にした
- `共起` は主画面から外し、stopword 除去、brand/domain 除外、alias 正規化を使った軽量 signal を `評価される軸` として整理した
- 主画面の URL 列挙は外し、詳細側だけで `引用 / 候補 / 判定保留` を追える current shape に寄せた
- `今回の結果` 復元条件は `質問 / provider / 自社URL / ブランド名 / 目立ちたい領域 / 比較対象` の一致で判定するよう更新した
- admin/detail/chart/result copy の user-facing 文言を `競合` から `比較対象 / 比較候補 / 市場での位置` に寄せ、`比較候補` の抽出と主画面の評価軸表示に整合するよう揃えた
- 改修後の desktop / mobile screenshot と DOM snapshot を `logs/ui_after_*` に保存し、`競合` と `共起` が main surface から外れたことを確認した

### Verified

- `.venv\\Scripts\\python.exe -m py_compile app.py analysis_lib.py config.py llmo_client.py storage.py ui\\market_context_helpers.py ui\\comparison_candidate_builders.py ui\\result_cards.py ui\\detail_views.py ui\\admin_views.py ui\\charts.py ui\\input_config_builders.py ui\\dashboard_view_models.py llmo_core\\openai_client.py runtime\\common.py`
- `.venv\\Scripts\\python.exe -c "import app"`
- `stop.ps1` -> `run.ps1` 後の `http://127.0.0.1:8083/` HTTP 200
- Playwright headless で、desktop / mobile の first view に `競合` と `共起` が残っていないこと、`目立ちたい領域` と `比較対象を入れる` が見えることを確認した
- Playwright headless で、`大阪の製造業で導入事例が強いAI検索会社を知りたい` に対して `大阪 / 製造業 / 導入事例` の候補表示と反映を確認し、手入力後に自動上書きされないことも再確認した
- synthetic row で `比較候補` 抽出を確認し、手入力 `比較対象` の優先と `Web幹事` のような外部比較サイト候補の抽出を確認した

### Self Repair

- `rg` が環境側で使えなかったため、PowerShell の `Select-String` と `Get-ChildItem` へ切り替えた
- Playwright 実行時の CP932 文字化けで JSON が崩れたため、`PYTHONIOENCODING=utf-8` を付けて再実行した
- `admin_views.py` の文言差し替え時に入った indentation error を修正した
- 質問変更時に候補 UI が更新されなかったため、入力イベントを `.on(\"update:model-value\")` から `.on_value_change(...)` に切り替えて自己修正した

### Notes

- Web 検索は未使用。自己修正はすべてローカル確認で収束した
- Phase 9 として `docs/CURRENT_STATE_2026-03-30.md`、`README.md`、`WORKLOG.md`、`ALGORITHM.md` を現物に合わせて更新する

## 2026-04-14 Review Update

### What Changed

- ページ再読込や socket reconnect 時に `render_page()` がプロセス起動時の stale config snapshot を使い回していたため、入力欄が古い質問へ戻り、旧条件の current result を拾うことがあった。初期 config を毎回 `config/llmo_poc_settings.json` から再読込する形へ修正した
- `techie-hub\start.bat force` で `techie-hub` / `kotomegane` / `notecode` / `aio2-main` を実起動し、TECHIE スイートの実画面比較を実施した
- `kotomegane` は permanent left drawer が main area を圧迫していたため、drawer を廃止して top shell + wide content card の見え方へ戻した
- `設定` タブに `まとめて確認` を復帰し、batch の `開始 / 状態更新 / 反映` と履歴テーブルが本番 UI から見える current shape へ戻した
- `定点計測` の KPI は `対象質問に対する自社露出率 / 自社引用シェア / 外部先行質問率` に整理し、batch job 数ではなく `対象質問数` を分母にすることを microcopy で明示した
- `config/llmo_poc_settings.json` に一時的に残っていた `ui_port=8098` を `8083` に戻し、`techie-hub\start.bat force` から stale port を踏まず再起動できるよう修正した
- 手動 run の長時間処理中に client が切れた場合でも `The parent slot of the element has been deleted.` が連鎖しにくいよう、safe UI update を `app.py` に追加した
- `今回の結果` が page reload / socket reconnect 後に空へ戻る問題に対して、同じ入力条件の run が直近 30 分以内に完了していれば current 面を自動復元するよう修正した。質問 / provider / 自社情報 / 競合語が変わったときだけ current 面を空へ戻す

### Verified

- `python -m py_compile app.py analysis_core\\metrics.py ui\\dashboard_refreshers.py ui\\styles.py`
- `import app`
- `techie-hub\start.bat force` 後の `http://127.0.0.1:8083/` HTTP 200
- Playwright + 画像確認で `8083` の home / `定点計測` / `設定 > まとめて確認` を再視認
- 手動 run は `8083` で `分析中です`、進捗文言、`分析を停止` ボタンの表示まで再確認した
- restore fix 後の `8083` で Playwright headless を再実行し、`2026-04-14 07:55:53` の直近 run が `改善判断を見る` 以下の `今回の結果` へ自動復元されることを確認した

### Remaining Note

- 手動 run は real provider だと数分単位になる。今回も 1 回は約 5 分かかっており、導線は成立しているが体感速度は引き続き注意点

## 2026-04-13 Snapshot

### Product Position

- 現行 `kotomegane` は旧 AI トラフィック解析アプリではなく `LLMO Prompt Loop PoC`
- 主目的は `AI 回答で自社が見えるか` を複数回観測し、次の改善判断につなげること
- 既定 model は `gpt-5.4-nano`
- OpenAI は `Responses API + web_search`
- prompt caching 前提で運用する

### Implemented Shape

- manual / batch / scheduled batch が同じ execution plan と保存経路を使う
- query planning は短文化、拡張質問、planner signature、prompt family 保存に対応
- rule-based の `deterministic_score` を主表示に使い、`raw_llm_score` は保持だけ行う
- `answer_text / citations / mentioned_brands / citation_domains / answer_type` を保存する
- citation URL は `引用された / 未引用 / 判定保留` で整理する
- UI は `入力 -> 今回の結果 -> 定点計測 / 設定` の軽い主導線に寄せている
- desktop では左サイド nav から `入力する / 今回の結果 / 定点計測 / 設定` に移動できる
- 主結果 3 カードは `AIはどう答えたか / なぜその判定か / 次に直すポイント` を先に読む構成へ更新した
- URL は raw list ではなく `自社 / 競合 / 外部 × 引用 / 候補 / 判定保留` の意味で読ませる構成へ更新した
- stopword を考慮した軽量 topic signal を追加し、競合・外部が取った論点と優先して足す論点をチップで表示する
- `C:\textresearch` の共起ネットワーク / BERTopic / 高度トピック抽出は現行 `kotomegane` には未統合で、現状は `analysis_core/topic_signals.py` の軽量 topic signal に留めている
- `定点計測` タブに質問別ヒートマップを追加し、質問ごとの勝敗状態を色で読めるようにした
- ヒートマップのセルから `結果` タブの `詳細を見る質問` へ直結し、該当質問の詳細へすぐ移れるようにした
- 入力は `質問1件` を既定にし、追加質問は任意で増やす文言へ寄せた
- 結果タブ上段は `今回の結果の整理` と `保存済みの累積傾向` を分離し、最新 1 質問と保存済み全体を混同しにくい構成へ更新した
- `今回の結果` は当セッションで新しく実行した分析だけを表示し、起動直後や入力変更後は待機状態に戻す
- `分析を実行` は `resolve_run_policy` import 抜けによる開始前 `NameError` を解消し、起動時例外も UI へ返す
- header / drawer / 主CTA は `techie-hub` / `notecode` / `aio2-main` と同じ `#2F241D` / `#D96B1F -> #B95416` 系へ揃えた
- `config/llmo_poc_settings.json` の `ui_port` は `8083` に戻し、TECHIE HUB 前提の既定ポートへ再整合した
- 空状態見出しは `今回の結果` に統一し、実行カードには長時間待ち時の再実行目安を出す
- 手動実行中は `分析を停止` を出し、現在の並列グループが終わったところで止める
- hero 上段は `コトメガネ = 観測して決める`、`コトミガキ = 改善を実行する` の 2 製品フローへ更新し、文章説明より visual handoff で役割分担を読ませる
- 根拠URLは初期表示を `実際に引用されたURL` のみに絞り、候補URLと判定保留は折りたたみへ分けた
- 主結果 1 枚目は `%` を主役から外し、`今回の結論` を大きく読ませたうえで、補助指標は `今回の回答回ベースの自社露出率` を主表示にし、関連質問を使った run のときだけ `関連質問カバレッジ` を補足表示する形へ更新した
- 主結果 2 枚目は `AIは今回は自社ページを主な根拠にしている / 外部サイトを主に参考にしている` などの平易な文へ差し替え、抽象的な「根拠を押さえる」表現をやめた
- 主結果 2 枚目には `比較 / 料金 / FAQ / 事例` などの質問軸をそのまま並べず、業務判断につながる短文へ変換して添えた
- 主結果 2 枚目の URL 並びは見出しと矛盾しないよう、主な根拠が自社なら自社URLを先に見せる順へ寄せた
- 主結果 3 枚目は `今すぐ直すページ` と `次に強化する候補` を分け、緊急修正がない場合は `いまは大きな欠落なし` と一目で読める構成へ更新した

### Runtime Notes

- 仮想環境は `.venv`
- setup は `setup.ps1`
- 起動は `run.ps1`
- 既定 port は `8083`
- API key は `.env` または環境変数から解決する
- app 単位 provider allowlist は `KOTOMEGANE_ENABLED_PROVIDERS` で制御できる
- `techie-hub\start.bat` は `8083` が既に listen していると force なしでは再起動しない

### Known Gaps

- 自動テストが不足している
- Gemini live batch は quota 429 のため完走確認待ち
- Claude live smoke は API key 設定環境での確認が未了
- external scheduler / worker への分離は未着手
- 料金プランは正式 source of truth をまだ置いていない
- `C:\textresearch` の `semantic_network` / `topic_analysis` 連携は未着手で、現行 repo に import / dependency / 記録がない

### Current Judgment

- 現行状況の確認先として `WORKLOG.md` と `ALGORITHM.md` を新設した
- `AGENTS.md` は運用入口として使い続けるが、詳細の実行フローは `ALGORITHM.md` を参照する
- 詳細な current state は引き続き `docs/CURRENT_STATE_2026-03-30.md` を正本として扱う
- 2026-04-09 に、`コトメガネ = 観測`、`コトミガキ = 改善` の役割差が日本語話者に一目で伝わるよう、ヒーロー、入力導線、結果詳細の文言を更新した
- 2026-04-10 に、URL が並ぶだけで意味が分からない問題に対して、主結果カードの役割を `結論 / 判定理由 / 次アクション` へ寄せ、結果・詳細の両方に URL 意味テーブルを追加した
- 2026-04-10 に、論点差分が文字だらけにならないよう、stopword を前提にした軽量トピック抽出を入れ、競合・外部が取った論点と足すべき論点をチップで見せる current judgment に更新した
- 2026-04-10 に、分析タブの重複していた推移 1 枚を `質問ごとの結果` ヒートマップへ置き換え、`どの質問で負けているか` を一目で読める current judgment に更新した
- 2026-04-11 に、ヒートマップから `詳細を見る質問` を切り替えて `結果` タブの詳細へ戻れる導線を追加し、分析から深掘りへの往復を短くした
- 2026-04-11 に、入力欄は `質問1件` を基本とし、複数質問は `追加質問` として任意で増やす読み方へ微調整した
- 2026-04-11 に、主結果カードの `%` は `検索回数` や単発回答数ではなく `今回確認した質問全体のうち自社URLが根拠に入った割合` と読める形へ更新し、詳細では `自社引用件数` と `引用内シェア` を分離した
- 2026-04-11 に、左サイドは説明パネル寄りの `Quick Jump` から、`入力 / 今回の結果 / 結果タブ / 分析タブ / 設定タブ` を読むタブ型ナビへ寄せた
- 2026-04-11 に、`notecode` / `aio2-main` と同じ暖色トークンへ寄せるため、背景・ナビ・CTA・アクティブ状態のグラデーションを `#F7F1EA / #F1E2D4 / #D96B1F / #B95416 / #2F241D` 系へ統一した
- 2026-04-11 に、左ナビの `結果タブ / 分析タブ / 設定タブ` は見た目だけではなく、実際に下段タブを切り替えて該当位置へスクロールする挙動へ更新した
- 2026-04-11 に、`導入事例ページ` などの不足ページタイプは検索結果の生分類ではなく、質問文・回答要約・推奨アクション・引用URLからの rule-based 推定であることを結果カードと詳細の読み方に明示した
- 2026-04-11 に、ヒーローと結果上段の情報設計を `改善判断ツール` 寄りへ更新し、`AIは誰を薦めたか / その根拠は何か / 次にどのページを直すべきか` を一読目の判断軸へ固定した。結果サマリーの見出しも同じ3点に揃え、主結果上段から `内部検索回数` を外した
- 2026-04-12 に、PC 表示レビューをもとに主結果 1 枚目の raw `answer_snapshot` を外し、deterministic 判定と矛盾しない要約だけに整理した
- 2026-04-12 に、主結果 3 枚目は `priority_label=維持` の場合に `不足している情報タイプ` ではなく `先に厚くする候補` として読ませるよう更新し、カード内の矛盾文言を解消した
- 2026-04-12 に、主結果 2 枚目は根拠URLを 3 件までに減らし、件数や論点ラベルを補助へ下げて、PC で 3 カード比較しやすい高さへ寄せた
- 2026-04-12 に、主結果 1 枚目は具体的な内部質問数を出さず、`今回の結論` を主役にしたうえで `関連質問まで含めた自社露出率` を補助指標として添える current judgment に更新した
- 2026-04-13 に、主結果 1 枚目の補助指標は `50回中8回 = 16%` のような回答回ベースの揺れを優先して読めるよう、`今回の回答回ベースの自社露出率` を主表示に戻した。関連質問を使った run では `関連質問カバレッジ` を別行で補足し、単一質問の繰り返しで `100%` と見えてしまう誤読を避ける current judgment に更新した
- 2026-04-12 に、主結果 2 枚目は `自社ページが根拠を押さえています` のような抽象表現をやめ、`AIは今回は自社ページを主な根拠にしている / 外部サイトを主に参考にしている` などの平易な文へ更新した
- 2026-04-12 に、主結果 2 枚目には current-run 内の質問軸ごとの出やすさ・弱さを短文で添え、`比較 / 料金 / FAQ / 事例` などどこで勝てていてどこが弱いかをマーケ判断へ使いやすくした
- 2026-04-12 に、結果タブ上段は `今回の結果の整理` と `保存済みの累積傾向` を分離し、主結果 3 カードと同じ最新 1 質問だけを上段に揃えた
- 2026-04-12 に、`その根拠は何か` と結果詳細の根拠URL欄は初期表示を `実際に引用されたURL` のみに絞り、候補URLと判定保留は折りたたみへ逃がした
- 2026-04-12 に、`分析` タブは `定点計測` に改称し、単発確認を fallback 表示しない空状態メッセージへ更新した
- 2026-04-12 に、安全な責務分離として `ui/dashboard_views.py` から主結果文言・集計を `ui/result_story_builders.py`、根拠URL整形を `ui/evidence_presenters.py` へ分離した。`dashboard_views.py` は NiceGUI 描画 owner、`app.py` は state / wiring owner の境界を維持し、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に、さらに `ui/dashboard_views.py` から主結果 3 カード描画と `今回の根拠URL` 描画を `ui/result_cards.py` へ分離した。`dashboard_views.py` は refresh orchestration に寄せ、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に、`app.py` から export 用の `build_report_summary_markdown(...)` を `report_summary_builders.py` へ分離し、`dashboard_views.py` の `refresh_dashboard(...)` は summary / decision / table / tracking widget 更新を内部 helper に分けた。`app.py` の非 wiring ロジックを減らしつつ、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に、`app.py` から onboarding / runtime microcopy / provider 表示名まわりを `ui/runtime_copy_builders.py` へ分離した。`app.py` は wiring と state owner に寄せたまま、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に、`app.py` から provider UI policy と runtime panel 更新を `ui/provider_runtime_controls.py` へ分離した。可視 provider 判定、provider config 正規化、provider chip 状態更新、runtime panel 更新を app 外へ寄せ、`app.py` は wiring / state owner にさらに寄せた。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に、`app.py` から入力正規化と実行前チェックを `ui/input_config_builders.py` へ分離した。`build_manual_runtime_config(...)`、`build_config_from_inputs(...)`、`notify_missing_required_fields(...)` を app 外へ寄せ、`app.py` は wiring / state owner にさらに寄せた。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に、`app.py` から legacy export archive と export bundle file 出力を `export_file_writers.py` へ分離した。あわせて provider 選択時の config 更新を `ui/provider_runtime_controls.py` に寄せ、`app.py` は state / wiring / event handler owner に揃えた。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に、`app.py` から dashboard / cluster brief / outcome compare / export preview の再同期手順を `ui/page_refreshers.py` へ分離した。`app.py` は refresh の発火 owner、`ui/page_refreshers.py` は再同期手順 owner に寄せ、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に、`ui/page_refreshers.py` へ question set / schedule admin view の再同期も追加し、`app.py` の保存系 handler から admin view refresh の重複をさらに削減した。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に、`ui/page_refreshers.py` へ batch job table / status / summary の再同期と status panel 更新も追加し、`app.py` の batch handler から batch admin refresh と label 更新の重複を削減した。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に、`ui/dashboard_views.py` から active scope filter、tracking scope filter、前回比判定、結果テーブル行、dashboard refresh 用 read-model 準備を `ui/dashboard_view_models.py` へ分離した。`dashboard_views.py` は描画更新 owner を維持し、既存の `dashboard_views.filter_rows_for_active_scope(...)` などの public 呼び出し境界も維持した。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-13 に、`ui/dashboard_views.py` から summary / decision / tracking widget の UI 更新反映を `ui/dashboard_refreshers.py` へ分離した。`dashboard_views.py` は refresh orchestration owner を維持し、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-13 に、`app.py` の cluster brief 生成 / 読み込み後の select 再同期と payload 表示を `ui/page_refreshers.py` へ寄せた。`app.py` は generate/load の event owner を維持し、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-13 に、`app.py` の cluster brief 生成から selected token 解決、candidate 抽出、cluster rows 組み立てを `ui/cluster_brief_builders.py` へ分離した。`app.py` は generate の event owner を維持し、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-13 に、`ui/cluster_brief_builders.py` へ cluster brief save payload の組み立ても追加し、`app.py` の generate handler から JSON 化と保存引数整形の重複を減らした。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-13 に、`app.py` の outcome compare 表示も `ui/page_refreshers.py` の owner へ揃え、`admin_views.render_outcome_compare(...)` の直呼びを減らした。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-13 に、`resolve_run_policy` import 抜けで `分析を実行` が開始前に失敗する不具合を修正した。手動実行 handler は起動時の例外を UI の status / notify に返すよう補強し、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-13 に、`今回の結果` を session-scoped に寄せ、質問 / provider / 自社情報 / 確認内容が変わった時点で旧結果を current-run 面から外す current judgment に更新した。保存済み結果は `保存済みの累積傾向` と履歴で読む前提に整理した
- 2026-04-13 に、保存済み履歴を含む temp DB と stub manual run で、起動直後は旧結果が `今回の結果` に出ないこと、クリック後にだけ `分析完了` へ進むことを確認した
- 2026-04-13 に、`ui/styles.py` の header / drawer と主CTA の色を `techie-hub` 系列へ再整列し、TECHIE HUB からの遷移で同一 SaaS の連続感を保つ current judgment に更新した
- 2026-04-13 に、`config/llmo_poc_settings.json` の `ui_port` を `8083` へ戻し、TECHIE HUB の `kotomegane` 導線と AGENTS の既定ポート前提に合わせた
- 2026-04-13 に、`ui/result_cards.py` の空状態見出しを `今回の結果` に統一し、`app.py` の実行カードへ `2分以上変化がなければ再実行を検討してください` の回復ガイドを追加した。stub UI で running / complete / stale の導線を再確認した
- 2026-04-13 に、default `8083` を汚さない dedicated live verify server (`8098`) を `tmp/live_verify_server.py` で起動し、real provider の最小 run で `分析完了`、`失敗 0件`、`今回の結果` カード描画まで確認した
- 2026-04-13 に、`app.py` へ `分析を停止` を追加し、stub UI (`8099`) で停止後に途中結果を current 面へ出さないことを確認した。さらに live verify (`8098`) で 2 回連続実行し、入力変更後と 2 回目完了後の両方で前回 current 結果が残らないことを確認した
- 2026-04-13 に、`aio2-main` と役割が重ならないよう `app.py` / `ui/styles.py` の hero を visual flow に更新し、`コトメガネ = 観測と判断`、`コトミガキ = 改善実行` の handoff を文章ではなく 2 枚カードと矢印で読ませる current judgment に更新した
- 2026-04-13 late に runtime と記録を再点検し、`techie-hub\start.bat` は `8083` が既に listen していると force なしでは旧 runtime を再利用するため、`ui/result_cards.py` 更新後でも表示が古いまま残りうることを確認した。`stop.ps1` -> `run.ps1` で再起動し、`http://127.0.0.1:8083/` の HTTP 200 を再確認した
- 2026-04-13 late に `app.py` の periodic refresh を `ui.timer(...)` から client 背景 task へ置き換え、client 切断や page delete と timer element の race で出ていた `The parent slot of the element has been deleted.` を抑止する current judgment に更新した。`py_compile` と `import app` を再確認した
- 2026-04-13 late に `ui/styles.py` / `app.py` / `ui/result_cards.py` / `analysis_core/topic_signals.py` を更新し、`コトメガネ` の左 drawer を明るいカード調へ戻したうえで、hero 直下に `直近の観測サマリー` を追加した。起動直後から `AIは誰を薦めたか / 今回の根拠 / 次に直すページ / 論点のつながり` を見せる current judgment へ変更した
- 同日の更新で `質問と返答から見えた論点` カードを追加し、既存の topic signal に加えて、質問文・回答・引用URLタイトルから作る lightweight な共起ペア表示を導入した。`C:\textresearch` の full semantic network 直移植ではなく最小導線だが、URL列挙以外の付加価値を first view に載せた
- 2026-04-13 late に `py_compile`、`import app`、8083 再起動、Playwright headless による起動確認を行い、明るい drawer、hero 下の観測サマリー 4 カード、論点チップと共起ペア表示まで確認した。スクリーンショットは `logs/kotomegane_ui_check.png`

## Next Read Order

1. `AGENTS.md`
2. `WORKLOG.md`
3. `ALGORITHM.md`
4. `docs/CURRENT_STATE_2026-03-30.md`
5. `docs/DOC_STATUS.md`
6. `docs/SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
7. `docs/LLM_BATCH_AND_CACHE_RULES_2026-04-05.md`
8. `external_engineer_handover_2026-04-05/documents/handover_notes/CODE_MAP.md`

## Archive Reference

- `archive/WORKLOG.md`
- `archive/PROGRESS.md`
- `archive/PLAN_KOTOMEGANE.md`
- `archive/2026-03-30-ai-traffic-analytics/**`
