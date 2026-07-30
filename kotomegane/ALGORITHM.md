# Kotomegane Algorithm

`kotomegane` の現行 PoC における実行アルゴリズムと責務分担をまとめる。  
旧 AI トラフィック解析アプリの `archive/**/ALGORITHM.md` とは別物として扱う。

## Purpose

- `AI 回答で自社が見えるか` を複数回観測する
- LLM の単発自己採点に依存しすぎず、rule-based の判定へ寄せる
- `manual / batch / scheduled batch` を同じ query planning と保存経路で扱う
- prompt caching を前提にしてコストと揺れを抑える

## Current Runtime Shape

- 既定 provider: `openai`
- 既定 model: `gpt-5.4-nano`
- OpenAI は `Responses API + web_search`
- UI の主導線は `市場観測`
- UI 診断 / デモ時は `KOTOMEGANE_READONLY_DEMO=1` で read-only/demo mode にできる。この mode では startup scheduler / maintenance を開始せず、provider client creation を block して manual LLM/API send、provider batch submit、provider batch retrieve/import に進まない
- `自社監査 (owned-only audit)` backend は残るが、現行 UI 主導線では前面に出さない
- 主表示スコアは `deterministic_score`
- LLM 返却の `visibility_score` は `raw_llm_score` として保持する
- 既定市場は `介護保険 / 福祉用具レンタル` に寄せる。`config/llmo_poc_settings.json` と `AppConfig` は、`https://healthrent.duskin.jp/` を対象URLにし、ヤマシタコーポレーション、パナソニック エイジフリー、フランスベッド、フロンティアを比較対象プリセットとして持つ
- パナソニック エイジフリー、フランスベッド、フロンティアのように福祉用具以外の事業も同一または近接ドメインにある会社は、全ドメインを競合評価対象にせず、`official_url_scopes` と `domain_scope_type` で path / business scope を明示する

## End-to-End Flow

1. UI で質問、自社 URL、任意の `名称`、任意の `重点テーマ`、任意の `比較対象`、provider 設定を受け取る
2. `config.py` が設定を読み込み、provider registry と budget guardrail を確定する
3. `ui/market_context_helpers.py` が質問文から `地域 / 業界 / 用途` の候補を軽量推定し、明示操作でだけ `重点テーマ` に反映する
4. `run_planning.py` が run mode ごとの execution plan を組み立てる
5. `run_policy.py` が run mode ごとの表示・batch import 可否・partial display 方針を適用する
6. `query_planning.py` が元質問を短文化し、必要に応じて拡張質問を作る
7. `prompt_catalog.py` が拡張質問を `prompt family` に対応づける
8. `plan_catalog.py` が provider ごとの総質問数上限を適用する
9. `manual` は元質問ごとに繰り返しを回し、その各回では拡張質問を並列送信する。`batch / scheduled batch` は shared execution plan を provider batch として扱う
10. guardrail は事前見積だけで終わらせず、`manual / batch / scheduled batch` すべてで query planning 後の実送信件数でも再評価する。日次予算は未import batch の予約コストも含めて判定し、`budget_guardrail_mode=warn` では警告して続行、`stop` では開始前に停止する
11. `llmo_client.py` と `llmo_core/*` が provider ごとの live request または batch request を送る。`market` mode の LLM 入力は `user query only` とし、`自社URL / 名称 / 比較対象 / 重点テーマ` は渡さない。`owned-only audit` だけが target-aware prompt を使う
12. 応答から `answer_text / citations / raw_llm_score / source URLs / security_signals` を抽出する
13. `analysis_lib.py` と `analysis_core/*` が、保存済みの citation URL / source URL / answer text に対してローカル照合を行い、rule-based の指標へ変換する
14. `ui/comparison_candidate_builders.py` が回答文や citation URL タイトルから `比較候補` を抽出し、手入力 `比較対象` と `competitor_presets` がある場合はそちらを優先する
15. `storage.py` が `run_session / query_plan / keyword_result / batch_job` などへ保存する
16. `billing_rules.py` が内部 billing unit を計算し、UI は microcopy だけ参照する
17. `app.py` が state / wiring を持ち、`ui/dashboard_views.py` が NiceGUI 描画を再構成する
18. `ui/result_story_builders.py` と `ui/evidence_presenters.py` が主結果文言、根拠URL整形、結果タブ集計の view-model を組み立てる
19. export 実行時は `export_file_writers.py` が `exports/` への CSV / JSON / Markdown summary 出力と legacy export archive を担う

## Query Planning Algorithm

### Inputs

- `user_query_raw`
- provider key
- repeat count
- expansion setting
- owned domains / brand aliases / `重点テーマ` / comparison terms
- ただし `market` mode の LLM request は `user_query_raw` だけを送る。owned / brand / comparison / market context は post-hoc matching 用の local context として保持する

### Planning Rules

- 長文質問は内部で短文化して `user_query_short` を作る
- 質問文から `地域 / 業界 / 用途` の候補を軽量推定するが、入力欄は自動上書きしない
- provider ごとの `総質問数上限` と `max_expansion_queries` を超えない範囲で拡張する
- query plan 再利用は `planner_signature` が一致するときだけ許可する
- `user_query_raw` と `executed_query` は分けて保存する
- `prompt_taxonomy_json` を持たせ、各拡張質問の intent family を追跡できるようにする

### Ordering Rule

- `manual` は `同じ元質問を連続で送る -> 次の質問へ進む` を基本にしつつ、各繰り返しでは同じ元質問に属する拡張質問を並列送信する
- 標準の単発確認は `元質問 + 拡張質問 3 件` を `5` 回実行し、1元質問あたり合計 `20` 件の分析リクエストとする
- `batch / scheduled batch` は shared execution plan の request 集合をそのまま provider batch 化する
- 狙いは prompt caching 効率を保ちつつ、manual の体感待ち時間を拡張質問単位で短くすること

## Provider Execution Algorithm

### Shared Rules

- `manual / batch / scheduled batch` は同じ execution plan を使う
- `manual` の live dispatch だけは、進捗表示と体感速度のため `元質問 x 繰り返し` ごとに拡張質問を並列グループとして送る
- provider 差分は `llmo_core/*` と capability registry に閉じ込める
- user-facing には provider 名を出し、内部 model 名は主導線に出さない
- config で指定された provider 系の custom model 名は、registry の候補リスト完全一致でなくても維持する。provider を UI で切り替える場合は、切替先 provider の既定 model に戻す
- app 単位の provider allowlist は `KOTOMEGANE_ENABLED_PROVIDERS` または config で制御する
- `market` mode の provider request は query-only とし、owned context は送らない。owned visibility は response 後に local scoring で計算する
- `competitor_presets` は provider request の制約として送らない。表示名・alias は post-hoc の競合名照合に使い、`official_url_scopes` / `domain_scope_evaluation_axes` は混在ドメインを評価するときの読み取り軸として保持する
- `KOTOMEGANE_READONLY_DEMO=1` の場合、`llmo_core.factory.build_provider_client(...)` は provider adapter を返さず例外にする。これにより UI handler や scheduler から呼ばれても provider submit / retrieve / import / live LLM/API send に到達しない

### OpenAI

- `Responses API + web_search`
- explicit `prompt_cache_key`
- `prompt_cache_retention=24h` を優先要求
- 未対応または未確認の model では `in_memory` へ自動 fallback
- `market` mode では query-only prompt を送り、`owned-only audit` だけが target-aware prompt を使う

### Gemini

- `google_search` 前提
- implicit cache を既定とし、provider 側挙動を優先
- explicit cache は 1 時間前提の扱い

### Claude

- `Messages API + web search tool`
- automatic prompt cache `5分` 前提
- batch 時の cache hit は best-effort

## Response Parsing Algorithm

### Extraction Targets

- `answer_text`
- `citations`
- `visibility_score` from model output
- source URLs
- security / injection-like signals

### Fallback Rules

- citation JSON が欠けても verdict / answer / citation URL を可能な範囲で回収する
- provider ごとのレスポンス差異は adapter で吸収する
- `consulted-only` source は主表示せず、citation として実際に出た URL を優先する
- prompt injection らしい文言は、検索由来の source title / URL 中心で `security_signals` として `output_json` に保持する
- `security_signals` は internal の保守判定に使い、user-facing の first view / detail に warning 文言として常時表示しない

## Scoring Algorithm

### Primary Decision

主表示は `deterministic_score` を使う。  
LLM の自己採点値は参照用として残す。

### Deterministic Inputs

- owned URL hit
- owned brand mention
- owned citation count
- owned citation share
- comparison / external mention
- external-only pattern
- answer type

### Score Intent

- `自社 URL とブランドが出る`
- `引用に自社が含まれる`
- `外部だけが強い`
- `比較対象や外部が前面に出る`
を同時に見て、可視性を 1 つの rule-based 指標に寄せる。

### Matching Rule

- `owned URL hit` は回答文中の単純なドメイン文字列一致ではなく、citation URL と source URL に自社ドメインがあるかを優先して判定する
- `owned brand mention` は answer text / citation title / source title に対する alias 正規化済みの文字照合で判定する
- `market` mode では、LLM が返した target-aware 自己申告値は主判定に使わず、保存後の local matching を正本とする

### Verdict Labels

- `自社優勢`
- `自社あり`
- `外部サイト優勢`
- `未露出`

これらは内部判定ラベルとして保持する。  
first view の main copy では `自社が主に引用された / 自社も出るが並走 / 外部が主に引用された / 自社は確認できず` を使う。

## Source Evidence Algorithm

- `citations_json`
- `output_json.citation_urls`
- `source_url`
を突き合わせ、URL 状態を次で整理する。

- `引用された`
- `検索ソースに出たが未引用`
- `不明`

`不明` は user-facing では `判定保留` として扱い、保存条件差や legacy row の混在時に未引用と断定しない。
user-facing では各 URL を `自社 / 競合 / 外部` と `引用 / 候補 / 判定保留` の意味ラベルで読む。
user-facing の主要文言では `競合` を避け、`自社 / 比較対象 / 外部` と `引用 / 候補 / 判定保留` の意味ラベルで読む。

## Topic Signals Algorithm

- `answer_text`
- `keyword_raw`
- 引用URLタイトル
- 検索候補URLタイトル
を対象に、stopword を考慮した軽量トピック抽出を行う。

### Topic Signal Rules

- 重い topic model は使わず、runtime では軽量な語句抽出だけを行う
- `data/stopwords_ja.txt` と `data/exclude_words_preset.json` を基底 stopword として使う
- `brand_terms`、`competitor_terms`、`market_context_terms`、`target_domain` 由来の語も動的 stopword に加える
- alias 正規化、brand/domain 除外、長すぎるタイトル断片の抑制を通してノイズを減らす
- user-facing には raw token list や `共起` を主役で見せず、`よく評価される軸`、`自社が取れている軸`、`比較候補・外部が取っている軸`、`優先して足す軸` として出す
- 初回実装では persistence を増やさず、保存済み row から runtime 生成する

## Scheduler Algorithm

- `scheduled batch` は in-process scheduler 前提
- `scheduler_runtime.py` が約 60 秒ごとに schedule を監視する
- `KOTOMEGANE_READONLY_DEMO=1` の read-only/demo mode では `app.py` startup が scheduler を開始しない。`ScheduledMonitorService.start()` / `tick()` も同 mode では no-op とし、poll / import / provider batch submit に進まない
- `schedule_plan` は 1つの保存済み `question_set` を参照する。`question_set.config_json` には `keywords` list が入るため、1 schedule は 1質問固定ではなく、選択した確認内容に含まれる複数質問を実行対象にできる
- 自動チェックの曜日 UI は月〜日のチェックボックスを正本とする。保存時は選択された曜日数を `weekly_run_count` に反映してから `normalize_schedule_weekdays(...)` に渡し、複数曜日を選んでも先頭曜日だけに丸められないようにする
- due な質問セットを provider batch として投入する
- provider batch 投入前に、query planning 後の実送信件数でも run guardrail を再評価する。`budget_guardrail_mode=warn` では 1 回上限の超過見込みだけでは投入を止めず、`stop` のときだけ停止する。日次 guardrail は `batch_job` に残る未import 分の予約コストを含めて判定する
- その後 poll / import を行い、`batch_job` と `batch_job_item` を正本として状態管理する
- partial display policy は timeout 後に pending provider を灰色表示する

## Draft Generation Algorithm

- row 単位では `Page Brief` の draft を rule-based に組み立てる
- cluster 単位では `Intent / Page Gap / Question Set` を起点に `Cluster Brief` draft を作る
- これらは backend capability として残し、通常の主導線では前面に出しすぎない

## Persistence Algorithm

### Main Tables

- `run_session`
- `query_plan`
- `keyword_result`
- `question_set`
- `schedule_plan`
- `batch_job`
- `batch_job_item`
- `cluster_brief`

### Persistence Rules

- live / batch / scheduled の結果は最終的に同じ `keyword_result` 系へ集約する
- `query identity` をそろえるため `executed_query` と `user_query_raw` を保持する
- `answer_text` と `citations` を raw 保存する
- 後段の集計用に `mentioned_brands_json`、`citation_domains_json` などの構造化列を持つ

## UI Read Model

### Primary Surface

- 入力
- 入力は `質問 / 自社URL / 名称(任意) / 重点テーマ(任意)` を基本にし、`比較対象` は必要時だけ開く
- 質問欄近くで `地域 / 業界 / 用途` の候補を表示し、明示操作でだけ入力へ反映する
- 今回の結果カード
- `AIが先に取り上げた相手`
- `主な参照元サイト`
- `頻出論点`
- first view の補助指標は `自社露出率 / 自社引用率` に固定し、どちらも同じ回答試行数を母数にする
- `今回の結論` を最も強く見せ、`対象AI / 最終更新` は hero の補助情報に固定する
- 参照元は raw URL の羅列ではなく `ページ名 + サイト名 + 何回の試行で参照元になったか` の上位 3 件で読む
- 頻出論点は first view では `よく扱われる論点 / 次に足す論点` の 2 群に絞って読む
- 詳細な `質問タイプ別の見え方 / 比較候補 / topic chips / 候補URL / 判定保留` は必要時だけ詳細で読む
- `今回だけの整理` と `保存済みの累積傾向` は別 surface に分け、粒度差を見た目だけで分かるようにする

### Analysis Surface

- `結果`
- `分析`
- `設定`
- `分析` では `質問ごとの結果` ヒートマップを置き、`判定 / 自社引用 / 比較対象引用 / 外部引用 / 自社候補` を質問行ごとに読む
- ヒートマップのセル選択は `結果` タブの `詳細を見る質問` と連動し、必要時だけ同じ質問の詳細へ切り替える
- `設定` では `保存済み条件` / `今回だけまとめて分析` / `曜日を決めて自動チェック` を開けるようにし、単発の `1回だけ分析` と継続観測の `自動チェック` を画面語彙で分ける
- `detail expansion` には `今回の結果 / 自動チェックの推移 / まとめて分析 / 設定` の 4 タブを置き、`まとめて分析` タブは概要 + `設定` / `自動チェックの推移` へのショートカットのみ（実操作は `設定` タブの expansion で行う）
- `定点計測` の user-facing KPI は `自社露出率 / 自社引用率 / 外部先行率 / 前回比` に固定し、すべて `観測試行数` を分母にする
- URL 件数ベースの割合や平均シェアは user-facing KPI から外し、必要時だけ URL 一覧を詳細で確認する

単発確認は履歴で振り返り、推移グラフは主に定点計測を使う。

### Refresh / Startup Performance

- `list_recent_results` は `keyword_result(analyzed_at DESC)` index を前提に読み、`source_url` は `result_id` index で result 単位に読む
- dashboard refresh は `ui/dashboard_view_models.py` の payload を 1 回作り、current result 復元、refresh signature、hero status、主要カード、詳細表示へ使い回す
- periodic refresh は payload の signature に変化がある場合だけ dashboard surface を再描画し、`今回の結果` を読んでいる間は hero status の軽更新に留める
- `定期分析の推移` タブ内の詳細 Plotly は初期表示で作らず、タブ表示時に lazy mount / lazy refresh する。非表示中の Plotly update は行わない
- 既存 row の enrichment 補完は `Storage()` 初期化時には走らせず、起動後 background maintenance として小分けに実行する。source URL は result_id 群で一括取得し、完了後は `PRAGMA user_version` marker で同じ補完を再実行しない
- read-only/demo mode では startup background maintenance も開始しない。UI 表示は既存 DB の read-model を読むだけに留め、診断起動中に schema / enrichment write が起きないようにする

### Export Surface

- `raw_results.csv`
- `weekly_summary.csv`
- `raw_results.json`
- `report_summary.md`
- CSV は spreadsheet formula injection を避けるため、先頭が `= / + / - / @ / tab / newline` の文字列を安全化して出力する

## File Ownership

- `app.py`
  - UI state と画面 wiring
- `export_file_writers.py`
  - legacy export archive、export bundle の CSV / JSON / Markdown 出力
- `report_summary_builders.py`
  - export 用 `report_summary.md` の文言組み立て
- `ui/runtime_copy_builders.py`
  - onboarding、runtime microcopy、provider 表示名、runtime 補助 markdown の文言組み立て
- `ui/provider_runtime_controls.py`
  - provider 選択 UI の可視 provider 判定、provider config 正規化、provider 選択時の config 更新、provider chip 状態更新、runtime panel 更新
- `ui/input_config_builders.py`
  - UI 入力からの `AppConfig` 組み立て、manual 用 repeat 補正、必須入力チェック
- `ui/market_context_helpers.py`
  - `重点テーマ` の分解/正規化、`地域 / 業界 / 用途` の軽量推定、候補表示用 helper
- `ui/page_refreshers.py`
  - question set / schedule / batch / cluster brief の admin view、dashboard / cluster brief / outcome compare / export preview の再同期手順
- `ui/dashboard_view_models.py`
  - active scope filter、tracking scope filter、前回比判定、結果テーブル行、dashboard refresh 用 read-model 準備
- `ui/comparison_candidate_builders.py`
  - 手入力 `比較対象` と回答/citation 由来の `比較候補` をまとめ、主画面・詳細で使う view-model を返す
- `ui/dashboard_refreshers.py`
  - summary / decision / tracking widget の UI 更新反映
- `ui/cluster_brief_builders.py`
  - selected cluster token の解決、candidate 抽出、cluster rows の組み立て、cluster brief save payload の組み立て
- `ui/dashboard_views.py`
  - ダッシュボード再描画、集計結果の反映、各描画 section の orchestration owner
- `ui/result_story_builders.py`
  - 主結果 3 カードの文言、参照元サイト/ページの試行数ベース集計、結果タブ集計文言、優先アクション、不足情報の集計
- `ui/evidence_presenters.py`
  - 根拠URLの owner/status 判定、強調順、意味ラベル、テーブル行整形、shared evidence helper
- `ui/result_cards.py`
  - 主結果 3 カードと `主な参照元サイト` セクションの NiceGUI 描画 owner
- `config.py`
  - 設定、provider registry、guardrail
- `runtime_mode.py`
  - `KOTOMEGANE_READONLY_DEMO` 判定と read-only/demo block message
- `plan_catalog.py`
  - provider ごとの総質問数上限
- `billing_rules.py`
  - 内部 billing unit と mode 別課金ルール
- `run_policy.py`
  - partial display と mode policy
- `run_planning.py`
  - mode ごとの execution plan
- `query_planning.py`
  - 短文化、拡張、signature
- `prompt_catalog.py`
  - prompt taxonomy の正本
- `llmo_client.py`
  - provider facade
- `llmo_core/*`
  - provider adapter と prompt owner
- `analysis_lib.py`
  - 分析 facade
- `analysis_core/*`
  - score、trend、classification、source evidence
- `storage.py`
  - SQLite schema と保存
- `scheduler_runtime.py`
  - scheduled batch submit / poll / import

## Read With This File

- `AGENTS.md`
- `docs/CURRENT_STATE_2026-03-30.md`
- `docs/DOC_STATUS.md`
- `docs/SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
- `docs/LLM_BATCH_AND_CACHE_RULES_2026-04-05.md`
- `external_engineer_handover_2026-04-05/documents/handover_notes/CODE_MAP.md`
