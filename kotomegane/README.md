# LLMO Prompt Loop PoC

`deep-research-report (11).md` を参考仕様として使いつつ、現行の実装運用は `AGENTS.md` と `docs/` 配下を正本にした PoC 構成です。

## What It Does

- `gpt-5.4-nano` を既定モデルとして Responses API を利用
- `web_search` を強制実行してキーワードごとの可視性を評価
- `市場観測` ではユーザークエリだけを LLM へ送り、`自社URL / 名称 / 比較対象 / 重点テーマ` は返答後のローカル照合にだけ使う
- 2026-06-08 時点の既定入力は `介護保険 / 福祉用具レンタル` 市場向けで、対象URLは `https://healthrent.duskin.jp/`、比較対象プリセットはヤマシタコーポレーション、パナソニック エイジフリー、フランスベッド、フロンティア
- 現行 UI は市場観測 backend を使いつつ、first view を `質問入力 -> 実行 -> 今回の結論 / 主な参照元サイト / 頻出論点` の 3 カードへ絞っている
- 2026-07-11 の横断UX監査対応で、390px幅の共通ナビを1行へ圧縮し、desktopは入力1/2の2列を保ったまま `結果を見る` だけを次行全幅へ移した。設定の対象AI / 保存済み条件も縦の読み順へ変更し、read-onlyでも他製品への文脈リンクは通常リンクとして見える。provider/API、DB、scoringは変更していない
- first view の主指標は `自社引用率` に絞り、`自社露出率` は混同を避けるため first view から外している
- current result と詳細の件数は raw row 数ではなく保存済みの `trial_count` を優先し、同じ質問を `n=10` 回と `n=100` 回で回した差がそのまま母数に出る
- first view の `AI回答に使われた主要ソース` は raw URL を並べず、`順位 / ページ名 / サイト名 / 自社・比較対象・外部サイト / 採用回数` の Top 3 だけを先に見せる
- first view の `頻出論点` は `改善優先の質問 / 次に強化すべき論点 / よく扱われる論点` を短く見せ、質問タイプ別の深掘りと実URLは詳細側へ下げている
- first view では `AIの主要な参照先` を自社引用率より先に置き、自社 / 比較対象 / 外部サイトの引用・候補バランスを share bar で短く可視化する
- first view と詳細では `改善優先の質問` を表示し、どの質問を優先して改善判断するかを既存データだけで読めるようにしている
- 詳細では `AI回答に使われた主要ソース` ランキングを表示し、どの根拠サイトやページが回答に使われたかを URL 羅列なしで読めるようにしている
- 2026-04-26 の商用デモ向け判断 UI 追加で、first view の `AI回答に使われた主要ソース` カード内に `根拠の安定度` を追加し、自社 / 比較対象 / 外部サイトの比率、依存リスク、上位ソース集中度を短く表示する
- 同日の追加で、詳細の `改善判断サマリー` 冒頭に `根拠の安定度 / 見え方の安定度 / 弱い質問タイプ` の 3 panel を置き、既存データだけで次に見るべき箇所を判断しやすくした
- 2026-04-26 の初見 UX 補強で、未実行時や入力変更後の `今回の結果` は `今の入力では未分析` と明示し、`保存済みの累積傾向` は `過去データ` ラベルと別背景で今回面から分けている
- 2026-05-24 の UI/UX refactor O-03..O-09 で、`今の入力` と `保存済み条件`、今回結果と `全実行履歴` / `保存済みの結果`、外部送信ボタン helper、曜日ベース自動チェック表示、複数質問詳細ラベルを分離した。DB schema / provider payload / scheduler dispatch / scoring は変更していない
- 2026-05-24 の UX-ADD-01 で、`KOTOMEGANE_READONLY_DEMO=1` の read-only/demo 起動モードを追加した。この mode では startup scheduler と background maintenance を開始せず、manual LLM/API send、provider batch submit、provider batch retrieve/import は provider client creation 前に block する
- 2026-05-24 の最終 UI/UX 実機改善で、mobile の入力カラムと重点テーマ候補ボタンを縦積み/全幅化し、保存済み集計の `今回 1 問` 表現を `今の入力で実行した結果ではない` 表現へ更新した。まとめて分析の状態表示は `対象質問` と `実送信` を分けて表示する。DB schema / provider payload / scheduler dispatch / scoring は変更していない
- 同日の補強で、first view の主CTAは `1回だけ分析` に集中させ、複数質問は `まとめて分析の画面を開く`、継続観測は `曜日を決めて自動チェック` の補助エリアへ下げた
- 同日の補強で、詳細の `改善判断サマリー` 冒頭に `外部サイト依存 -> 見え方の揺れ -> 弱い質問タイプ` の優先度ストリップを追加し、危ない順番と次に見る場所を先に示す
- 2026-04-26 の調整でも、新しい LLM 呼び出し、prompt、query planner、scoring algorithm、DB schema、保存項目は追加していない
- 2026-04-29 の UI 修正で、hero のロゴは `assets/logo_mark_icon.png` の顔マーク画像へ切り替え、ロゴ枠に `EC` だけが見える状態を解消した
- 同日の UX 修正で、手動分析完了後、定期分析の結果反映後、同条件の直近 run 復元後は、下段の `今回の結果 / 定期分析の推移 / 定期分析 / 設定を見る` を自動展開し、`今回の結果` タブを開く
- 2026-04-26 の起動・refresh 根本修正で、`keyword_result(analyzed_at DESC)` と `source_url(result_id)` の index を追加し、`/` の初期表示では詳細タブ内 Plotly を作らず、表示時に lazy mount する current shape へ更新した
- 同日の修正で、dashboard refresh は 1 回の `list_recent_results(500)` から payload / signature / hero 更新を使い回す。`Storage()` import 時の enrichment backfill は同期実行せず、起動後 background maintenance として小分け実行する
- 2026-04-25 の調整では、コトミガキ側の文章生成、ページ制作、修正実行、1クリック改善に当たる機能は追加していない。新しい LLM 呼び出し、prompt、scoring、DB schema も追加していない
- 2026-04-25 の操作確認で、`今回の結果` が空状態に戻っている場合でも、下段の `保存済み質問ごとの結論` から保存済み DB の詳細を選び、`改善判断サマリー`、根拠URL、生返答、今回の条件を確認できるようにした
- 2026-04-25 の商用デモ向け cleanup で、設定タブでは `batch_job_id` のような内部 ID を見せず、`__UI_TEST__...` のような test-only 保存名は `保存済み質問セット` / `定期分析` の平易なラベルへ寄せている
- 結果詳細の折りたたみと URL 状態ラベルは、`判定保留` や `候補` のような内部語を避け、`根拠に使われた / 見つかったが未採用 / 確認が必要` の平易な文言へ寄せている
- 主入力は `質問 / 自社URL / 名称(任意) / 重点テーマ(任意)` を正本とし、`比較対象` は折りたたみの任意入力へ下げている
- 質問文から `地域 / 業界 / 用途` の候補を軽量推定し、`候補を反映` ボタンでだけ `重点テーマ` へ取り込める
- 回答文や citation URL タイトルに出た他社名・媒体名・団体名は `競合` と断定せず `比較候補` として扱う
- 同一 prefix を保って prompt caching を狙う
- 通常実行は、複数質問がある場合も同一質問を連続送信する順序にして prompt caching 効率を優先
- 手動実行では、各繰り返しの中で拡張質問を並列送信し、進捗表示もその並列グループ完了数に合わせて更新する
- prompt cache は 24時間保持を優先要求し、使えない条件では `in_memory` へ自動 fallback する
- 定点計測は内部で `20` 回、単発確認は `5` 回を既定にし、UI には回数を出さない
- 単発確認は、質問数や内部拡張で見積件数が増えても事前の warning toast は出さない
- 手動 / 定期リサーチ（今すぐ） / 定期リサーチ（自動）の guardrail は、未import batch の予約コストも含めて再評価する
- `run_budget_guardrail_usd` を超える見込みの実行は、`budget_guardrail_mode=warn` では警告して続行し、`stop` のときだけ手動 / 一括 / 自動ともに開始前に止める
- 通常実行とは別に、provider ごとの Batch API へ投入する `Batchモード` を追加
- Batch モードでは `Batch投入` / `Batch状態確認` / `Batch結果取り込み` を UI から実行可能
- Batch 取り込み後の結果は通常実行と同じ SQLite 保存経路に入り、既存の一覧・カード・履歴に反映される
- 質問セットを `保存済み条件` として保存し、手動実行 / まとめて分析 / 自動チェックの各実行で再利用できる
- `保存済み条件` は `アーカイブ` でき、履歴を残したまま新規の自動チェック候補から外せる
- 検索結果内の命令文は system prompt で無視する前提にし、注入らしい文言は `security_signals` として内部保存する
- prompt injection 検知はゼロ幅文字除去と role-change / context-reset 系パターンを追加して補強している
- security signal は internal 判定にだけ使い、結果画面には warning 文言として常時表示しない
- 同じ元質問は前回の expansion を優先再利用し、比較条件を安定させる
- 日本語 50 文字超の長文質問は内部で短文化し、UI には元質問を残したまま計測する
- `拡張検索` として、元質問ごとに最大 4 件（元質問 + 関連質問 3 件）へ広げて実行できる
- 拡張質問は `managed prompt taxonomy` で `比較 / 料金 / 事例 / FAQ / サポート / 評判 / 導入不安 / 手順` の意図へ寄せて保存できる
- `前回比サマリ` では、同じ expansion signature の直近 2 run に限って `自社露出率 / 平均 visibility スコア / 外部サイト優勢率` を比較できる
- user-facing の割合と件数は `試行数` を唯一の母数にそろえ、`自社露出率 / 自社引用率 / 外部先行率` を同じ観測試行数ベースで読む
- `自動チェック` を追加し、曜日 + 時刻 + 週あたり回数で自動実行できる
- 2026-05-23 のUI確認で、自動チェックの曜日指定は dropdown ではなく月〜日のチェックボックスへ変更した。選択した曜日数に合わせて `週あたり回数` を保存時に揃えるため、複数曜日を選んだのに先頭曜日だけで保存される状態を避けている
- この変更の詳細は `docs/SCHEDULE_UI_CHANGE_2026-05-23.md` を参照する。1つの自動チェックは1つの保存済み条件を参照し、その保存済み条件に複数質問が入っていれば複数質問を実行対象にできる
- 同日の追加修正で、3質問など内部拡張後の送信件数が `run_budget_guardrail_usd` を超える見込みでも、既定の `budget_guardrail_mode=warn` では単発 / 今すぐ一括 / 自動定期を止めず、警告だけで実行へ進む
- scheduled batch はバックグラウンドで状態確認と結果 import まで自動で行う
- UI 診断やデモで provider/API/LLM を動かしたくない場合は、起動前に `KOTOMEGANE_READONLY_DEMO=1` を設定する。この mode では UI 上部に `read-only/demo mode` banner が出て、scheduler / provider submit / retrieve / import / LLM/API send は開始されない。通常起動では従来どおり scheduler と provider 経路を使う
- provider capability registry で `default model / 総質問数上限 / batch timeout / partial display policy / cache policy / expansion mode` を保持する
- config で provider 系の custom model 名を指定した場合は、registry の候補リスト完全一致でなくても維持する。UI の provider 切替では切替先 provider の既定 model に戻す
- `KOTOMEGANE_ENABLED_PROVIDERS` または config の `enabled_provider_keys` で app 単位の provider allowlist をかけられる
- `plan_catalog / billing_rules / run_policy` を module 化し、provider ごとの総質問数上限、手動と batch の内部課金単位、partial display 方針を分離している
- 手動 / 定期リサーチ（今すぐ） / 定期リサーチ（自動）の microcopy と内部課金説明は mode 別に出し分ける
- query planner は `plan_catalog` にある provider ごとの `総質問数上限` と `max_expansion_queries` を見て拡張質問数を制御する
- manual / batch / scheduled batch は同じ execution plan と送信順序を使う
- query plan 再利用は `planner_signature` 一致時だけ行い、provider / planner 条件差をまたいだ再利用を避ける
- batch import は `executed_query` と `user_query_raw` を分けて保持し、manual / batch / scheduled の query identity を揃える
- LLM の `visibility_score` は `raw_llm_score` として保持し、UI 主表示は rule-based の `deterministic_score` を使う
- deterministic score は `自社URL hit / ブランド hit / 自社引用数 / 自社引用シェア / 競合出現 / external only / answer type` から算出する
- run / query rollup では `median / min / max / stddev / variance_label` を持ち、detail では揺れ幅を確認できる
- 詳細側は `結果 / 分析 / 設定` の 3 タブに整理し、主画面の読み量を減らしている
- stage header は `入力する / 結果を見る / 詳細` の 3 段導線を保ちつつ、短い補助文だけを出す
- 必須入力不足などの通知は短文化し、主CTA は `分析を実行` に固定している
- config を `config/llmo_poc_settings.json` に保存
- 結果を `data/llmo_poc.db` に保存
- run ごとに snapshot を保存し、`run_session` と `keyword_result` で時系列を追える
- run ごとに `query_plan` を保存し、`user_query_raw / user_query_short / expanded_queries_json / expansion_signature` を追える
- `query_plan` には `prompt_taxonomy_json` も保存し、内部で使った質問がどの prompt family に属するかを detail / export で追える
- 生返答を `answer_text`、引用元を `citations` として保存し、一覧は軽く、detail card で深掘りできる
- `answer_text` と `citations` から `言及ブランド / 引用ドメイン / 自社出現 / 競合出現 / 返答タイプ` を構造化して保存する
- `target_domain_hit` は回答文中の単純なドメイン文字列一致ではなく、引用URLや検索ソースURLに自社ドメインがあるかを優先して判定する
- raw answer 構造化では brand alias 展開、citation domain 正規化、answer type の rule-based scoring を使い、過剰検出と揺れを減らす
- `コトメガネ` は改善判断に必要な見え方確認を担当し、改善施策の実制作や文書改善は `コトミガキ` 側へ役割を分ける
- 日本語話者向けに、`コトメガネ = 改善判断のための見え方確認`、`コトミガキ = 改善実装` が画面内だけで分かる文言へ寄せる
- 入力は `質問1件` を既定にし、複数質問は必要なときだけ追加で作る導線にしている
- `クラスタ下書き作成` は PoC 機能として backend に残しつつ、通常導線には出さない
- NiceGUI で、圧縮したヒーロー、入力先行の主導線、`見えているか / 何が評価されているか / 自社が強い軸 / 次に足すもの` を中心にした結果カード、結果詳細カード、`詳細を見る` 展開を表示
- ヒーローは `コトミガキ` 寄りの compact H1 に寄せ、上段は `コトメガネ` のブランド名だけを短く見せる構成にしている
- ヒーローでは `改善判断ツール` と `AIは誰を薦めたか / その根拠は何か / 次にどのページを直すべきか` を先に読ませ、右側は `対象AI / 最終更新 / 先に見ること` の最小情報に絞っている
- UI の接続表示は `ChatGPT / Gemini / Claude` の provider 名だけに絞り、内部モデル名は出さない
- 主結果の下に `全体の見え方` として `自社露出率 / 自社引用率 / 外部先行率 / 前回比` の 4 指標と主要推移を出し、保存済み結果がある場合は起動直後から確認できる
- 2026-04-04 の UI 再整理で、上段を `入力または実行条件`、中段を `今回の結果` 3 カード、下段を `分析 / 設定` に寄せ、`zip\src\pages\Megane.tsx` に近い読み順へ更新した
- 固定UIの説明や設定は muted なラベル / カードで弱く見せ、主結果3カードは `自社の露出 / 外部との比較 / 次に見る論点` の用途別ラベルで見分けやすくした
- 2026-04-05 の UI 追加整理で、desktop は左サイドの dashboard nav から `入力する / 今回の結果 / 定点計測 / 設定` へ直接移動できる
- 2026-04-11 の UI 微調整で、主結果カードの `%` は誤読しにくい補助指標として整理し、詳細では `自社引用件数` と `引用内シェア` を分けて表示している
- 2026-04-11 の追加整理で、ヒーローと結果上段は `観測ツール` ではなく `改善判断ツール` として読めるように更新し、`AIは誰を薦めたか / その根拠は何か / 次にどのページを直すべきか` を一読目の判断軸へ固定した
- 2026-04-12 の PC 向け調整で、主結果 1 枚目は raw `answer_snapshot` を外して deterministic 判定と整合する要約だけに絞り、`自社優勢` と本文が食い違う状態を解消した
- 2026-04-12 の PC 向け調整で、主結果 3 枚目は `不足` と `強化候補` を `priority_label` に応じて言い分けるよう更新し、`導入事例ページを直すべき` と `不足はまだない` が同時に出る矛盾を解消した
- 2026-04-12 の PC 向け調整で、主結果 2 枚目は根拠URLを 3 件までに絞り、件数や論点ラベルを補助へ下げて 3 カード比較しやすい高さへ寄せた
- 2026-04-12 の PC 向け整理で、主結果 1 枚目は `%` を主役から外し、`今回の結論` を大きく読ませたうえで補助指標に下げた
- 2026-04-13 の表示修正で、主結果 1 枚目の補助指標は `関連質問まで含めた自社露出率` ではなく `今回の回答回ベースの自社露出率` を主表示に戻し、関連質問を使った run のときだけ `関連質問カバレッジ` を補足表示するよう更新した
- 2026-04-14 の追加調整で、主結果 1 枚目は `今回の自社露出率` を `元質問 / 拡張質問 / 合計回答数` の母数つきで説明し、`自社が見つかった回答` と `実際に自社URLが引用された回答` を分けて見せるよう更新した
- 2026-04-14 の追加調整で、主結果 2 枚目の件数ラベルは `自社の引用URL / 比較対象の引用URL / 外部の引用URL` に変更し、回答率と URL 件数の混同を避けるようにした
- 2026-04-14 の再構成で、主結果 3 カードは `今回の結論 / 主な参照元サイト / 頻出論点` を読む形へ更新した。first view では URL 数や raw URL ではなく、ページ名・サイト名・論点を先に読む current shape にしている
- first view の主指標は `自社露出率 / 自社引用率` の回答試行ベースに更新し、内部の回答回数や URL 件数は detailed view 側へ下げている
- 2026-04-20 の first view 再整理で、主結果 3 カードは `今回の結論 / 主な参照元サイト / 頻出論点` に更新した。URL は生で並べず、`ページ名 + サイト名 + 何回の試行で参照元になったか` の形で要約し、実URLは詳細側へ下げている
- 2026-04-20 の UX 追加調整で、hero と stage header をさらに圧縮し、first view 直前の補助文を 1 行に縮めた。主結果 3 カードでは `今回の結論` を最も強く見せ、中央カードは上位 3 件、右カードは 2 群の論点だけに絞っている
- 2026-04-20 の `定期リサーチ` リネームで、`まとめて確認 / 自動更新 / 定期チェック` の UI 文言を **定期リサーチ** に統一した。ボタンは `今すぐ実行`、スケジュール側は `自動で継続`、内部 DB キー（`batch_job_id` / `run_mode=batch|scheduled`）は互換維持のためそのまま残している
- 2026-04-20 の追加整理で、detail expansion に **`定期リサーチ` タブ** を追加し（`今回の結果 / 定点計測 / 定期リサーチ / 設定`）、単発の `分析を実行` と継続観測用の `定期リサーチ` の役割を UI 上で分けた
- 2026-04-20 の hero 整列で、hero にロゴマーク + `LLM見え方観測` サブタイトル + `コトミガキ` / `コトメイク` への cross-link を追加し、`techie-hub/start.bat` 配下 3 サービス（コトメイク / コトミガキ / コトメガネ）の視覚トーンを揃えた
- 2026-04-20 の value surface 追加で、hero 直下に **常時表示の `観測の推移` カード**（`自社引用率 / 外部先行率` の折れ線 + 最新 自社引用率 + hero の `前回比` カード）を置き、定期リサーチで貯まる履歴が expansion を開かなくても見えるようにした
- 2026-04-21 のトップ導線追加で、`実行` カードの文言を `今回を確認する / 継続観測を始める` に更新し、トップから `定期リサーチ｜今すぐ` と `自動で継続を設定` へ直接入れる quick access を追加した
- 2026-04-21 の画面比較後の圧縮で、`手順` 見出し、重複する説明文、`継続観測` の補助ブロックを削り、first view を `hero / 入力 / 実行モード / 今回の結果 / 観測の推移` まで一画面で読みやすい密度へ寄せた
- 2026-04-21 の実行モード整理で、トップ CTA を `1回だけ分析 / 複数質問を一括分析 / 自動観測を設定` に変更し、内部語の `バッチ` や曖昧な `今すぐ` を first view から外した。2026-04-26 の補強では `1回だけ分析` を主役にし、定期分析系は初回確認後の補助導線へ下げた
- 2026-04-21 の billing 方針整理で、将来の実クレジット消費は `実行完了時` に固定した。手動は成功結果保存後、定期リサーチは結果反映完了後に消費し、投入時点や開始前失敗では消費しない
- 2026-04-12 の PC 向け整理で、主結果 2 枚目は `自社ページが根拠を押さえています` のような抽象表現をやめ、`AIは今回は自社ページを主な根拠にしている / 外部サイトを主に参考にしている` などの平易な文へ差し替えた
- 2026-04-12 の PC 向け整理で、主結果 2 枚目には `比較 / 料金 / FAQ / 事例` などの質問軸をそのままラベルで並べず、`比較検討では自社が見つかりやすい / 料金説明は外部を見られやすい` のような業務判断向けの短文へ寄せた
- 2026-04-12 の PC 向け整理で、主結果 2 枚目の URL 並びは見出しと矛盾しないよう、`自社が主な根拠` のときは自社URLを先に見せる順へ更新した
- 2026-04-12 の PC 向け整理で、主結果 3 枚目は `今すぐ直すページ` と `次に強化する候補` を明示的に分け、緊急修正がない場合は `いまは大きな欠落なし` と一目で読める構成へ更新した
- 2026-04-12 の PC 向け整理で、結果タブ上段は `今回の結果の整理` と `保存済みの累積傾向` に分け、後者が今回 1 問の結果ではなく保存済み質問の累積集計だと分かる見出しへ更新した
- 2026-04-12 の PC 向け整理で、`その根拠は何か` と結果タブの根拠URL欄は初期表示を `実際に引用されたURL` のみに絞り、候補URLと判定保留は折りたたみへ退避した
- 2026-04-12 の PC 向け整理で、`分析` タブは `定点計測` に改称し、単発確認を fallback 表示しない空状態メッセージへ更新した
- 2026-04-13 の UX 調整で、`今回の結果` はこのセッションで新しく `分析を実行` した内容だけを表示する。起動直後や入力変更後は待機状態メッセージを出し、前回保存済みの内容は `保存済みの累積傾向` と履歴側で確認する
- 2026-04-14 の current-result 復元調整で、同じ入力条件の run が直近 30 分以内に完了していれば、ページ再読込や接続張り直し後でも `今回の結果` を自動復元する。質問 / provider / 自社URL / 名称 / 重点テーマ / 比較対象を変えた場合は従来どおり待機状態へ戻す
- 2026-04-14 の再接続修正で、ページの再読込時は起動時の固定スナップショットではなく `config/llmo_poc_settings.json` の最新保存値を読み直す。これにより、直前に実行した質問と自社URLに一致する `今回の結果` を復元しやすくし、古い質問へ巻き戻る状態を避ける
- 2026-04-14 の UI 再定義で、主入力から `競合` を外し、`質問 / 自社URL / 名称 / 重点テーマ` を正本にした。比較したい相手は折りたたみの `比較対象` に下げ、質問文から `地域 / 業界 / 用途` の候補を軽量推定して `候補を反映` で取り込める
- 2026-04-14 の UI 削減実装で、hero の `TECHIE SUITE` box、`活かす材料`、`直近の観測サマリー`、`論点のつながり` を first view から外し、入力カードを最上段の主役へ戻した
- 同日の追加実装で、主画面の結果カードは first view で `今回の結論 / 主な参照元サイト / 頻出論点` を先に読む形にそろえ、`自社優勢` などの内部判定語は main copy から外した
- 2026-04-13 の安全補強で、`分析を実行` 開始前の予期しない例外は UI の status / notify に返す。開始直後は spinner と進捗を先に描画し、見た目だけ無反応に見えにくくしている
- 2026-04-13 の追加調整で、空状態見出しは `今回の結果` に統一し、実行カードには `2分以上変化がなければ再実行を検討してください` の回復ガイドを追加した
- 2026-04-13 の追加補強で、手動実行中は `分析を停止` を表示し、現在の並列グループが終わった時点で止める best-effort cancel に対応した。停止した run の途中結果は `今回の結果` 面に出さない
- 2026-04-13 の役割整理で、hero は `コトメガネ = 観測して決める`、`コトミガキ = 改善を実行する` の visual flow を表示する。TECHIE HUB 配下の SaaS として、重複説明より役割分担を図で理解させる方向を優先する
- 左サイドは説明パネルではなく、`入力 / 今回の結果 / 今回の結果タブ / 定点計測タブ / 設定タブ` を先頭に置くタブ型ナビへ寄せている
- 左ナビの `今回の結果タブ / 定点計測タブ / 設定タブ` は実際に下段タブを切り替える
- `導入事例ページ` などの不足ページタイプは検索エンジンの生分類ではなく、質問文・回答要約・推奨アクション・引用URLからの rule-based 推定であることをUI内で説明する
- 配色トークンは `notecode` / `aio2-main` / `techie-hub` と同じ暖色シリーズに合わせ、背景・ナビ・CTA・アクティブ状態の勾配を共通化している。濃いブラウンは `#2F241D`、主CTA は `#D96B1F -> #B95416` を基準にする
- 検索回数、繰り返し回数、内部質問、cache / reasoning などの内部指標は主導線に出さない
- `定期リサーチ`（旧称 `まとめて確認` / `自動更新` / `定期チェック`）と `クラスタ下書き` は detail expansion の `定期リサーチ` タブと `設定` タブにまとめ、単発の `分析を実行` と混ざらないようにしている
- `コトメガネ` では「何を直すかを決めるための改善判断」までに止め、改善メモ生成やページ下書きは前面に出さない
- 入力欄は `質問` 側を広くし、`自社の情報` 側は補助入力に寄せて、最初にどこへ書くか迷いにくい幅へ調整している
- 手動実行カードは `分析中` スピナーを出し、進捗は `0-1` ではなく `%` と `件数` で読めるようにしている
- 手動実行中の status copy は `元質問 x/y / 拡張質問 x/y / 繰り返し x/y` を出し、各繰り返しでは `拡張質問の完了数` を進捗バーと同じ母数で読むようにしている
- `分析を実行` を押した直後は、ボタン表示を `分析中...` に切り替え、activity 表示と progress bar の初期進みを先に描画する
- query plan 準備中でも `現在 / 状態` を progress 下に出し、`押したが無反応` に見えにくいようにしている
- manual run 開始前に全画面の重い再描画は挟まず、実行カードの progress と status を先に返す
- Windows の子プロセス側 `__mp_main__` では `ui.run(...)` を再実行しない
- `localhost:8083` に旧 Flutter 系 service worker が残っていても、起動時に解除と cache 削除を走らせ、`flutter_service_worker.js` には unregister 用の no-op script を返す
- `定点計測` タブの KPI と推移は `定点計測` だけを集計し、`単発確認` はグラフに混ぜず履歴でだけ見られるようにしている
- `質問ごとの結論` 一覧は `質問 / 結論 / 市場での位置 / 不足している情報タイプ` の要点だけに絞っている
- `ダッシュボード概要` の主役KPIは `自社露出率` を優先し、履歴は `AI visibility スコア推移` と `自社露出率 / 外部サイト優勢率の推移` を先に見る構成に寄せている
- user-facing の URL 表示は `回答で実際に citation として出た URL` を中心に扱い、consulted-only の内部 source は前面に出さない
- detail では URL 状態を `引用された / 検索ソースに出たが未引用 / 不明` に分け、fallback 混在や legacy row は `不明` を優先する
- `不明` は user-facing では `判定保留` として説明し、保存条件の違いなどで未引用と断定しない方が安全な URL をまとめる
- 2026-04-10 の UI 改修で、URL は生の一覧ではなく `自社 / 比較対象 / 外部` と `引用 / 候補 / 判定保留` の意味ラベル付きで表示する
- 結果タブと詳細タブに `根拠URLの意味` / `URLごとの意味` テーブルを追加し、どの URL が回答の根拠なのか、候補止まりなのかを読めるようにした
- 主結果の 2 枚目は `なぜこの判定か` に更新し、件数や候補情報は補助へ下げつつ、`AIが何を根拠にそう判断したか` を自然文で先に読む構成にしている
- 2026-04-10 の追加改修で、stopword を考慮した軽量トピック抽出を導入した。主画面では語句チップを減らし、detail 側で必要時だけ論点差分を読む方針に寄せている
- トピック抽出は保存済みの `answer_text`、引用URLタイトル、検索候補URLタイトルから runtime 生成し、長文説明を増やさずに論点差分だけを読む方針にしている
- `C:\textresearch` の `semantic_network` / `topic_analysis` にある `networkx` / `pyvis` / `sklearn` ベースの共起ネットワークや高度トピック抽出は、現行 `kotomegane` には未統合である。現在の論点表示は `analysis_core/topic_signals.py` の軽量 runtime 集計で、結果詳細の chip 表示に留めている
- `定点計測` タブには `質問ごとの結果` ヒートマップを追加し、`判定 / 自社引用 / 比較対象引用 / 外部引用 / 自社候補` を質問行ごとに色で読めるようにした
- ヒートマップのセルを押すと、`結果` タブの `詳細を見る質問` が同じ質問へ切り替わり、そのまま詳細へ戻れる
- `managed prompt taxonomy` は `prompt family` を主軸に `外部引用優勢 / 自社は出るが未引用 / 判定保留` を軽く集計し、detail で深掘りしつつ main の `質問の系統ベースの優先アクション` 3 件へ反映する
- `prompt_taxonomy_json` がない既存 row でも、`executed_query / keyword_raw` から runtime で `prompt family` を推定し、detail / export の family 表示を維持する
- 入力カードには `最初の進め方` を置き、初回ユーザーが `何を入れるか / どこを見るか` を画面内だけで判断できるようにしている
- 結果詳細には `この結果の読み方` を置き、判定スコア・URL 状態・`判定保留` の意味を画面内で説明する
- export は `raw_results.csv`, `weekly_summary.csv`, `raw_results.json` に加えて `report_summary.md` を出力し、画面内でも報告用まとめをプレビューできる
- CSV export は spreadsheet formula injection を避けるため、`=`, `+`, `-`, `@`, タブ / 改行始まりの文字列を安全化してから出力する
- 主画面は `入力 -> 分析を実行 -> 主結果3カード` を先に見せ、`結果を見る` は実行後だけ表示し、深い確認は `詳細を見る` の `結果 / 分析 / 設定` タブへ集約している
- `意図マップ` と `不足ページナビ` は `詳細を見る > 詳細` 側で `判断 -> 制作着手` に寄せている
- 推移グラフは `全体の推移`、`意図クラスタの推移`、`不足ページの推移`、`質問別の推移` を優先表示する
- 主導線を `入力する / 結果を見る / 詳細` の 3 段に分け、初見の操作と詳細運用が混ざらないようにしている
- 上部ナビは raw URL を見せず、`assets/kotomegane-logo.svg` のフルロゴを薄いクリームの台座に載せて表示し、小さい幅でも縦に崩れにくい並びへ整理している
- 主結果3カードは狭い幅では縦積みで読めるようにしている
- `質問ごとの判断一覧` は主画面に出さず、`詳細を見る` の `詳細` タブ側へ下げている
- export は `raw_results.csv`、`weekly_summary.csv`、`raw_results.json` を `exports/` 配下へ出力する
- `定期リサーチ` では `削除 / 複製 / 定期リサーチ diff / 質問セット diff` を同一カード内で扱える
- `実行結果比較` では定期実行 / 質問セット系列から 2 回分を選び、可視率 / 意図分布 / 不足ページ分布 / 自社言及 / 競合言及 / 引用ドメインを軽く比較できる
- 質問ごとに `比較 / 料金 / FAQ / 事例 / 地域 / 指名 / How-to` の意図を付与し、弱い意図クラスタを一覧化
- `recommended_actions` を制作タスクへ寄せ、`比較ページ / 料金ページ / FAQページ / 導入事例ページ / 地域LP` などの不足ページに変換
- 実行ガードは内部に残しつつ、画面上は金額ではなく `今日の実行件数 / 今回の投入件数 / ガード挙動 / キャッシュ方針` を表示する
- prompt caching は 24時間保持を優先要求し、使えない条件では自動で `in_memory` へ切り替える
- `定期リサーチ（今すぐ）` は一括割引を優先する別導線として維持する
- ヒーローは初期表示の占有高さを抑え、起動直後に「自社が出るか / どこが出るか / 次に直すページ」が短く読める構成にしている
- 直近の見え方と次に確認する点は、非技術者でも読める平易な日本語で返す
- 入力欄は「このキーワード・質問で自社が出るか / どこが出るか」を測る意図が分かる表現に寄せている
- ヒーロー、入力前説明、結果詳細の読み方で、`ここは改善判断`、`改善の実作業はコトミガキ` を明示する
- 直近結果では、「見えているか」「何が評価されているか」「次に足すもの」を分けて表示し、根拠URLは「自社 / 比較対象 / 外部サイト」で見分けられる
- 直近結果では、監査モード、意図ラベル、不足している情報タイプ、不足理由を前面に表示する
- 上段の「優先アクション」は質問名つきで表示し、どの質問のための施策かを一目で追える
- 判定ラベルは `自社優勢 / 自社あり / 外部サイト優勢 / 未露出` の4段階で表示し、旧 `拮抗` の曖昧な中間判定は使わない
- グラフは `全体の推移`、`意図クラスタの推移`、`不足ページの推移`、`質問別の推移` を先に表示する
- 配色は、ブラウン / クリーム基調 + オレンジ強調へ戻しつつ、ブランド強調と状態表示を分離し、`自社 / 比較対象 / 外部` と補助情報の意味が画面全体でぶれないように揃える
- フォントは `Sora + Noto Sans JP` を前提にし、`card-primary / card-secondary / card-detail` の階層へ寄せている
- ロゴとファビコンは `aio2-main` / `notecode` と同じ共通ブランド資産へ揃えている
- 上部ナビの `TECHIE HUB` 文字はロゴへ置き換え、最終的に 3 サービス共通H1へ寄せやすい形にしている
- 詳細設定では `比較対象` を任意入力でき、推論やキャッシュ設定は内部既定値を使う
- 金額は UI に出さず、内部の guardrail とログだけに残す。既定の警告モードでは上限超過見込みを理由に実行を止めず、明示的な停止モードだけが hard stop になる
- 実行履歴、出力、根拠URL、対象AIの切り替えは主画面から下げ、必要なときだけ `分析 / 設定` 側で確認する
- 接続AIは `ChatGPT / Gemini / Claude` の provider 名だけを表示し、内部モデル名や検索回数は表に出さない
- 今後 `aio2-main` と `notecode` を含めて同一 SaaS として見えるよう、暖色系の共有トークンへ寄せる前提で整理している

## Read First

- `AGENTS.md`
- `docs/CURRENT_STATE_2026-03-30.md`
- `docs/DOC_STATUS.md`
- `docs/LLM_BATCH_AND_CACHE_RULES_2026-04-05.md`
- `external_engineer_handover_2026-04-05/`
  - 外部エンジニア向けの最小共有パッケージ

Default config file is already included:

- `config/llmo_poc_settings.json`

Current default highlights:

- `provider`: `openai`
- `model`: `gpt-5.4-nano`
- `reasoning_effort`: `low`
- `prompt_cache_key`: `llmo-poc-v1`
- `prompt_cache_retention`: `24h` を優先要求し、未対応条件では `in_memory` に補正
- `max_output_tokens`: `1200`
- `analysis_mode`: `market`
- `plan_key`: `upper`
- `daily_budget_usd`: `1.0`
- `run_budget_guardrail_usd`: `1.2`
- `budget_guardrail_mode`: `warn`
- `pricing.usd_to_jpy`: `160.0`

## Setup

```powershell
.\setup.ps1
```

前提:

- セットアップ時のみローカルの Python 3.11 系を使って `.venv` を作成すること
- アプリ本体の runtime は `run.ps1` 経由で `.venv\Scripts\python.exe` を使うこと

Then set:

```dotenv
OPENAI_API_KEY=your_api_key_here
GEMINI_API_KEY=your_api_key_here
ANTHROPIC_API_KEY=your_api_key_here
```

`.env` が空でも、シェルの process / user / machine 環境変数に `OPENAI_API_KEY`、`GEMINI_API_KEY`、`ANTHROPIC_API_KEY` のいずれかがあれば起動できます。
`run.ps1` は起動前に、`.env` と環境変数のどちらを使うかを表示します。
`.env` と環境変数の両方に値があり異なる場合は、環境変数が優先されます。
`KOTOMEGANE_ENABLED_PROVIDERS=openai,gemini` のように設定すると、app 単位で provider 表示を絞れます。

## Run

```powershell
.\run.ps1
```

Open `http://127.0.0.1:8083`.

停止:

```powershell
.\stop.ps1
```

同じシェルで `run.ps1` を前面起動している場合は `Ctrl+C` でも停止できます。
Windows では `run.ps1` が runtime process tree を kill-on-close job で管理するため、host の PowerShell を終了したときも 8083 listener が残りにくい構成にしています。

TECHIE HUB から確認する場合:

```powershell
C:\tetie\techie-hub\start.bat
```

`techie-hub\start.bat` の `kotomegane` 起動は `run.ps1` を経由し、PATH 上の `python.exe` / `py` を直接 runtime に使いません。
`techie-hub\start.bat` は `8083` がすでに listen していても、軽量な `http://127.0.0.1:8083/healthz` に応答しない `kotomegane` listener は自動で再起動します。HUB のカード状態確認も `/healthz` を使い、NiceGUI の full page `/` を定期 ping しないことで初期画面描画の backlog を避けます。UI 変更を確実に反映したいときは従来どおり `C:\tetie\techie-hub\start.bat force` か、`.\stop.ps1` 後の再起動を使ってください。
2026-04-14 時点の current config は再び `8083` 固定に戻しています。一時検証で別 port を使う場合も、保存済み config をそのまま残さない運用に戻しました。

## Notes

- The app uses one combined call per keyword to keep cost and implementation surface smaller than a two-stage pipeline.
- `Page Brief` は row / cluster ともに手動導線からだけ生成し、常時自動では動かしません。
- `gpt-5.4-nano` は `reasoning_effort=none / low / medium` を使える。UI は `none` も出すが、既定値は安定性優先で `low`。
- `市場観測` では `allowed_domains` を soft preference として扱い、指定外ドメインを完全には排除しません。
- 自社監査系の backend は残しているが、現行 UI では市場観測の最小導線を優先し、表面の切り替え導線は出していません。
- 通常の `分析を実行` は同期 + prompt caching 前提のまま残し、Batch モードには置き換えていません。
- 定期リサーチ（今すぐ / 自動）は provider ごとの Batch API を使う別導線です。1件ごとの request body は通常実行と同じ分析 payload / system prompt 方針を使い、単発の `分析を実行` とは分けてあります。
- `定期リサーチ（自動）` は保存済み質問セットを前提にし、選択中 provider の Batch API を自動投入する運用です。
- 定期リサーチ（自動）の日時は `この時刻から処理を開始する` 意味です。結果反映は provider により最大 24 時間かかる場合があります。
- schedule 管理UIでは `フォーム読込 / 複製 / 削除 / 差分比較` を扱います。複製直後は停止状態で保存します。
- `実行結果比較` は 2 run 比較の初期版で、系列は `定期実行` と `質問セット` から選びます。
- `週あたり回数` は、選択した曜日数に保存時点で揃えます。曜日は月〜日のチェックボックスで指定し、複数曜日を選んだ場合はその曜日数が保存されます。
- `budget_guardrail_mode=warn` のままなら、3質問などで query planning 後の送信件数が増えても `run_budget_guardrail_usd` 超過見込みだけでは単発 / 今すぐ一括 / 自動定期を停止しません。`stop` に変更した場合だけ開始前に止めます。
- raw answer retention のために `answer_text` と `citations` を保存します。返答全文は一覧に出さず、結果詳細カードで確認します。
- raw answer の構造化項目は `mentioned_brands_json`, `citation_domains_json`, `owned_mention_hit`, `competitor_mention_hit`, `answer_type_label` を使います。
- timezone DB がない Windows でも schedule 保存が止まらないよう、`Asia/Tokyo` など主要 timezone には固定オフセット fallback を入れています。
- export ファイルは `exports/raw_results.csv`, `exports/weekly_summary.csv`, `exports/raw_results.json` を上書き更新します。
- export は raw answer の構造化項目を含みます。金額列は user-facing export から外しています。
- `query_plan` の詳細項目は `raw_results.csv` / `raw_results.json` に露出し、`weekly_summary.csv` には週次集約に加えて `median / min / max / stddev / variance_label` を出します。detail UI では内部質問列挙を前面に出しません。
- detail の `内部で使った質問` には `prompt family / prompt label / purpose` を出し、generic expansion だけでなく管理された prompt 群として読めるようにしています。
- OpenAI の prompt caching は `prompt_cache_key` を使う explicit cache です。`prompt_cache_retention=24h` は全モデルで使えるわけではなく、`gpt-5.4-nano` では `in_memory` に補正して実行します。
- OpenAI の未登録 custom model 名も config から維持しますが、24時間 cache 対応は断定せず、未対応または未確認の場合は `in_memory` に補正します。
- provider ごとの既定モデルは registry から解決し、user-facing UI にはモデル名を出しません。
- `OpenAI 30 / Gemini 30 / Claude 15` の総質問数上限は `plan_catalog` で保持します。
- `Gemini` は `Google Search grounding` を使う manual/live と Batch に対応します。`Gemini 2.5+` は implicit caching が既定で、explicit cache の既定 TTL は `1時間` です。Batch でも context caching が有効です。
- `Claude` は `Messages API + web search tool` を使う manual/live と Batch に対応します。automatic prompt caching は既定 `5分`、`1時間` cache は未接続で、Batch の cache hit は best-effort として扱います。
- `app.py` の UI責務は `ui/` package へ分離済みで、画面 wiring / state / event handler は `app.py` に残しています。
- legacy export archive と export bundle の CSV / JSON / Markdown 出力は `export_file_writers.py` に分離しています。
- export 用の `report_summary.md` 文言組み立ては `report_summary_builders.py` に分離しています。
- onboarding / runtime microcopy / provider 表示名まわりの copy builder は `ui/runtime_copy_builders.py` に分離しています。
- provider 選択 UI の可視 provider 判定、provider config 正規化、provider 選択時の config 更新、provider chip 状態更新、runtime panel 更新は `ui/provider_runtime_controls.py` に分離しています。
- UI 入力からの `AppConfig` 組み立て、manual 用 repeat 補正、必須入力チェックは `ui/input_config_builders.py` に分離しています。
- question set / schedule / batch / cluster brief の admin view、dashboard / cluster brief / outcome compare / export preview の再同期手順は `ui/page_refreshers.py` に分離しています。
- active scope filter、tracking scope filter、前回比判定、結果テーブル行、dashboard refresh 用 read-model 準備は `ui/dashboard_view_models.py` に分離しています。
- summary / decision / tracking widget の UI 更新反映は `ui/dashboard_refreshers.py` に分離しています。
- selected cluster token の解決、candidate 抽出、cluster rows の組み立て、cluster brief save payload の組み立ては `ui/cluster_brief_builders.py` に分離しています。
- `ui/dashboard_views.py` は NiceGUI の描画 owner、`ui/result_story_builders.py` は主結果文言と結果タブ集計、`ui/evidence_presenters.py` は根拠URL整形の owner として分離しています。
- `ui/result_cards.py` は主結果 3 カードと `主な参照元サイト` セクションの描画 owner として分離しています。
- client 切断時は periodic refresh timer を停止し、delete 時に cancel します。`techie-hub` から離脱したあとに `The parent slot of the element has been deleted.` が継続しにくいようにしています。
- 2026-04-13 late に、periodic refresh を `ui.timer(...)` から client 背景 task へ置き換えた。client 切断や page delete と timer element の race で出ていた `The parent slot of the element has been deleted.` の抑止が目的です。
- 2026-04-21 に、periodic refresh は結果データの signature が変わった場合だけ dashboard surface を再描画する形へ更新しました。再描画時はブラウザの scroll position を保存・復元し、分析結果を読んでいる途中で初期位置へ戻る挙動を抑えています。
- 2026-04-23 に、`今回の結果` を表示中は periodic refresh が `今回の結果 / 結果詳細 / 根拠URL` を再描画しない current shape へ更新しました。分析後に読んでいる内容を background refresh で崩さず、hero status だけを軽く更新します。
- 2026-04-26 に、periodic refresh と手動 refresh は同じ dashboard payload を使い、payload 内の signature で差分判定します。定期分析の推移タブが非表示の間は詳細 Plotly を mount / update せず、表示時だけ cached payload で描画します。
- 同日の DB 側修正で、`list_recent_results` は `idx_keyword_result_analyzed_at`、`list_sources` は `idx_source_url_result_id` を使います。古い row の enrichment 補完は `PRAGMA user_version` marker で完了後に再実行しない maintenance に移しました。
- 2026-04-23 に、結果詳細の `この画面で分かること / 見つかったが根拠には使われなかったURL / まだ確認が必要なURL` は折りたたみをやめ、固定表示で整理して読む current shape へ更新しました。
- 2026-04-13 late に、`ui/styles.py` の drawer / hero 配色比率を見直し、左全面ダークだった `Quick Move` を明るいカード調へ戻した。`コトメイク` / `コトミガキ` と同じく「クリーム地が主役、濃いブラウンは上部ナビ中心」のトーンへ寄せている。
- 同日の UI 修正で、いったん追加していた `直近の観測サマリー` と `質問と返答から見えた論点` は 2026-04-14 の UI 削減実装で first view から外し、必要時だけ詳細側で追う current shape に戻した。
- 2026-04-14 の TECHIE スイート比較レビューで、`kotomegane` だけ main area を圧迫していた permanent left drawer を廃止し、`techie-hub` / `notecode` / `aio2-main` と同じ shared top shell + wide content card の見え方へ寄せた。
- 同日の UI 修正で、`設定` タブから `まとめて確認` を再度開けるよう戻し、`まとめて開始 / 進み具合を更新 / 結果を反映` と batch 履歴テーブルを同じ画面から確認できるようにした。
- 2026-04-20 の表示整理で、`定点計測` の主役 KPI は `回答試行ベースの自社露出率 / 回答試行ベースの自社引用率 / 回答試行ベースの外部先行率` に統一した。user-facing の割合と件数は batch job 数や URL 件数を使わず、すべて観測試行数を分母にする。
- 同日の runtime 修正で、一時検証中に `config/llmo_poc_settings.json` へ残っていた `ui_port=8098` を `8083` に戻し、`techie-hub\start.bat force` から本番導線を確実に踏める状態へ戻した。
- 同日の手動 run 補強で、client 切断後の `The parent slot of the element has been deleted.` 連鎖を避ける safe UI update を追加し、長時間 run 中の disconnect が runtime 全体の例外になりにくいようにした。
- `analysis_lib.py` と `llmo_client.py` は facade で、実装本体は `analysis_core/` と `llmo_core/` に分離しています。
- `analysis_core/scoring.py` も facade で、classification は `analysis_core/classification.py`、deterministic scoring は `analysis_core/deterministic_scoring.py` が owner です。
- 手動 / 定期リサーチ（今すぐ） / 定期リサーチ（自動）の可否と partial display は `run_policy` で解決します。
- 手動 2 単位、定期リサーチ 1 単位の内部 billing rule は `billing_rules` で解決します。
- `docs/` 直下は `kotomegane` 本体の正本を優先し、セッション用メモは `docs/session_notes/`、横断資料は `docs/cross_product/` に整理しています。
- Windows のプロセス監視では listener の `python.exe` が `.venv\Scripts\python.exe` ではなく、`.venv\pyvenv.cfg` に記録された base interpreter に見えることがあります。runtime 自体は `.venv` の `sys.prefix` / site-packages で動きます。

## Verification

- `run.ps1` で `http://127.0.0.1:8083/` の起動を確認済み
- read-only/demo 起動は PowerShell で `.\run.ps1 -ReadOnlyDemo` とする。この mode では API key check を skip でき、画面表示確認だけを行える。環境変数を直接設定する場合も `KOTOMEGANE_READONLY_DEMO=1` を引き継ぐ
- runtime health は `http://127.0.0.1:8083/healthz` で確認できる。HUB と `start.bat` はこの lightweight endpoint を使い、full UI `/` を health check に使わない
- 2026-04-26 の起動改善後も HUB と `start.bat` は `/healthz` を使う。`/` はユーザーが開いた時だけ NiceGUI UI を描画し、定期 health check には戻さない
- `ui_host` は loopback (`127.0.0.1` / `::1` / `localhost`) のみで起動する。loopback 以外は認証未実装のため fail-closed で起動拒否する
- 実ブラウザエンジンの headless 実行で、デスクトップ/モバイルの主要 UI 導線、上段サマリー、最新結果カード、結果一覧を確認済み
- `gpt-5.4-nano` の live run を 2026-03-30 に実行し、結果を `data/llmo_poc.db` に保存済み
- 2026-03-31 に OpenAI Batch API の live smoke を別DBで実行し、`Batch投入` 相当の submit / status retrieve / result import / 既存一覧相当への保存まで確認済み
- 2026-04-01 に `question_set` / `schedule_plan` / `answer_text` / `citations` を含む DB migration、scheduled batch runtime、推移グラフ差し替え、export 生成、結果詳細カードの import smoke を確認済み
- 2026-04-01 に `mentioned_brands_json` / `citation_domains_json` / `owned_mention_hit` / `competitor_mention_hit` / `answer_type_label` の DB 拡張、結果詳細カードの `ページ下書き`、定期実行の `複製 / 削除 / diff` helper、金額表示の UI 撤去、export の構造化項目追加、`python -m py_compile`、`.venv\\Scripts\\python.exe -c \"import app\"`、`HTTP 200` を確認済み
- 2026-04-01 に `cluster_brief` 保存、`意図 / 不足ページ / 質問セット` 単位のクラスタ下書き、`実行結果比較`、brand alias / citation domain / answer type tuning、schedule 初回保存の `None` bug 修正、timezone fallback を追加し、temp DB で保存・比較ロジックを確認済み
- 2026-04-01 に主画面を `入力する / 結果を見る / 詳細を使う` の 3 段導線へ再整理し、主結果を 3 カードに絞り、詳細側を `運用` / `詳細` の 2 タブに分けたうえで HTTP 200 応答を確認済み
- 2026-04-01 に実ブラウザ headless で `質問セット保存 -> schedule 保存 -> 複製 -> diff 表示 -> detail brief -> export -> cluster brief 導線` を確認し、`browser_validation.png` を取得済み
- 2026-04-03 に `query_plan` 保存、長文短文化、拡張検索、同一 expansion signature 条件での前回比サマリ、定期チェックの開始時刻文言を追加し、`py_compile`、`import app`、HTTP 200 を確認済み
- 2026-04-03 に provider capability registry、provider ごとの総質問数上限、shared execution plan、Batch request 生成の共通化を追加し、`py_compile`、`import app`、HTTP 200、request plan のローカル smoke を確認済み
- 2026-04-03 に `planner_signature` による query plan 再利用の絞り込み、batch import の `executed_query` / `user_query_raw` 分離、manual / batch / scheduled 共通の query plan 準備 helper を追加し、`py_compile`、`import app`、HTTP 200、batch identity smoke を確認済み
- 2026-04-03 に `raw_llm_score / deterministic_score / owned_citation_count / owned_citation_share / external_only_result` を保存するよう更新し、UI 主表示を deterministic 側へ寄せ、`median / min / max / stddev / variance_label` を rollup / export / detail に追加したうえで `py_compile`、`import app`、HTTP 200、scoring smoke を確認済み
- 2026-04-03 に `運用` タブの `確認内容 / 定期チェック / まとめて確認 / 出力` を折りたたみ化し、helper text と通知文を短くし、主画面の主CTAを `分析を実行` に寄せたうえで `py_compile`、`import app`、HTTP 200 を確認済み
- 2026-04-03 に `plan_catalog / billing_rules / run_policy` を追加し、manual / batch / scheduled batch の可否、provider ごとの質問数上限、batch partial display 方針の owner を分離したうえで `py_compile`、`import app`、HTTP 200、policy smoke を確認済み
- 2026-04-03 に `save_keyword_result` の INSERT placeholder mismatch を修正し、OpenAI live manual / batch submit / batch refresh / batch import を最小構成で確認済み。live manual で JSON truncation が出たため `max_output_tokens` の既定値を `1200` に引き上げた
- 2026-04-04 に desktop / mobile screenshot を `logs/screenshot_desktop_2026-04-04.png` と `logs/screenshot_mobile_2026-04-04.png` へ再取得し、HTTP 200 を再確認済み
- 2026-04-04 に temp DB で長文短文化 + 拡張検索の live validation を 1 例実行し、`query_was_shortened=true`、内部質問 5 件、`query_then_repeat`、`fallback_count=0` を確認済み
- 2026-04-04 に `llmo_client.py` へ truncated JSON recovery と source-based citation backfill を追加し、citation_urls 末尾切れ時でも fallback せず verdict / answer / citations を保持できることを live rerun で確認済み
- 2026-04-04 に temp DB で OpenAI live manual / batch verification を追加実行し、manual は `fallback_used=false`、batch は `completed -> imported_result_count=1` まで確認済み
- 2026-04-04 に `weekly_summary.csv` へ `median_visibility_score / min_visibility_score / max_visibility_score / score_stddev / variance_label` を追加し、ローカル smoke で出力列を確認済み
- 2026-04-04 に Gemini manual/live adapter、provider allowlist hook、起動時の複数 provider API key 検出を追加し、manual 導線で Gemini を選べる状態へ更新した
- 2026-04-04 に `logs/gemini_live_manual_verification_2026-04-04.json` を出力し、`gemini-2.5-flash-lite` の live request で citation 付き応答を確認済み
- 2026-04-04 に `手動 / まとめ確認 / 定期チェック` の mode 別 microcopy と内部課金説明へ整理し、batch panel の provider 固定文言を除去した
- 2026-04-04 に Gemini / Claude の provider batch adapter を追加し、`py_compile`、`import app`、local import smoke を確認した。Gemini live batch は provider quota 429 のため完走未確認、Claude live smoke は Anthropic key 未設定のため未実施
- 2026-04-04 に `app.py` の UI責務を `ui/` へ、`analysis_lib.py` を `analysis_core/` へ、`llmo_client.py` を `llmo_core/` へ、`analysis_core/common.py` を内部 submodule へ、`analysis_core/scoring.py` を `classification.py` / `deterministic_scoring.py` owner へ分離し、`py_compile`、`import analysis_lib, app`、HTTP 200 を確認済み
- 2026-04-04 に provider ごとの cache policy 表示を整理し、OpenAI は explicit prompt cache、Gemini は implicit default + explicit 1時間、Claude は automatic 5分 + Batch best-effort として UI / detail / runtime 文言へ反映した。`py_compile`、`import app`、HTTP 200 を確認済み
- 2026-04-04 に `prompt_catalog.py` を追加し、fallback expansion と query plan 保存を `managed prompt taxonomy` へ寄せた。`prompt_taxonomy_json` を `query_plan` に保存し、detail / export で `prompt family / label / purpose` を確認できるようにした。`py_compile`、`import app`、HTTP 200 を確認済み
- 2026-04-04 に `analysis_core/source_evidence.py` を追加し、`citations_json / output_json.citation_urls / source_url` から URL 状態を `引用 / 未引用 / 不明` に整理した。detail は quoted を先に、未引用と不明を折りたたみへ下げ、主画面の優先アクションは source 根拠ベース 3 件へ更新した。`py_compile`、`import app, analysis_lib`、HTTP 200、temp DB smoke を確認済み
- 2026-04-05 に `prompt_taxonomy_json` がない既存 row でも `executed_query / keyword_raw` から `prompt family` を runtime 推定できるよう更新し、detail の `質問の系統ごとの見え方` を family-first に整理した。`不明` は `判定保留` として説明し、`py_compile`、`import app`、family 集計 smoke、fallback synthetic smoke を確認済み
- 2026-04-05 に onboarding 用の `最初の進め方`、detail の `この結果の読み方`、`report_summary.md` 出力と画面内プレビューを追加した。`py_compile`、`import app`、報告用 markdown smoke を確認済み
- 2026-04-05 に左サイド dashboard nav と切断時 timer stop/cancel を追加し、`py_compile`、`import app` を確認済み
- 2026-04-13 に `resolve_run_policy` import 抜けによる `分析を実行` の silent failure を修正し、`py_compile`、`import app`、HTTP 200、保存済み履歴を入れた temp DB + stub manual run での `分析完了` 到達と待機状態 UX を確認済み
- 2026-04-13 late に、`py_compile`、`import app`、8083 再起動、Playwright headless による起動確認を行い、明るい drawer / hero 直下の観測サマリー 4 カード / 論点チップと共起ペア表示まで確認した。スクリーンショットは `logs/kotomegane_ui_check.png`
- 2026-04-13 に `今回の結果` 見出し統一と実行カードの長時間待ちガイドを追加し、stub UI で `分析中です` 表示、`分析完了`、入力変更後の stale 表示を再確認済み
- 2026-04-13 に temporary live verify server (`8098`) で real provider の最小構成 run を実行し、`分析完了`、`失敗 0件`、`今回の結果` カード描画まで確認済み
- 2026-04-13 に stub UI (`8099`) で `分析を停止` 導線を確認し、live verify (`8098`) で 2 回連続実行して、質問変更後は前回 current 結果が残らず、2 回目完了後も 1 回目の current 表示が残らないことを確認済み
