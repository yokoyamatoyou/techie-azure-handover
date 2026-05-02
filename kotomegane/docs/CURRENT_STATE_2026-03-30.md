# Current State 2026-03-30

## Summary

`kotomegane` は `LLMO Prompt Loop PoC` に再編済みです。  
旧 AI トラフィック解析アプリは `archive/2026-03-30-ai-traffic-analytics/` に退避しています。

2026-03-30 の更新で、PoC UI の再整理、`USD + JPY(160)` 表示、価値訴求を先に出す日本語UI、接続先候補の折りたたみ表示、`gpt-5.4-nano` 実動確認に加えて、provider adapter 入口、`.env` / 環境変数の runtime 明示、`allowed_domains` soft constraint 明示まで完了しました。
2026-04-20 の市場観測補正で、`market` mode は `query-only` に切り替えました。`自社URL / 名称 / 比較対象 / 重点テーマ` は LLM に送らず、返答後に citation URL と source URL へローカル照合して可視性を判定します。これにより、`自社URLを prompt に渡したことで LLM が追従する` 形を避けています。
2026-04-14 の UI 削減実装で、hero の `TECHIE SUITE` box、`活かす材料`、`直近の観測サマリー`、`論点のつながり` を first view から外し、入力を最上段の主役へ戻しました。主入力は `質問 / 自社URL / 名称(任意) / 重点テーマ(任意)` へ更新し、first result summary は `今回の結論 / 主な参照元サイト / 頻出論点` の 3 カードに固定しています。
同日の追加調整で、主結果 1 枚目は `今回の自社露出率` の母数を `元質問 / 拡張質問 / 合計回答数` まで含めて表示し、`自社が見つかった回答` と `実際に自社URLが引用された回答` を分けて説明する形へ更新しました。主結果 2 枚目の件数は `自社の引用URL` など URL 件数であることを明示し、`94%` と `自社引用9件` のような別母数が同種の数字に見えない current shape へ寄せています。
同日の再構成で、first result summary はさらに `今回の結論 / 主な参照元サイト / 頻出論点` へ更新しました。中央カードは URL を生表示せず `ページ名 + サイト名 + 何回の試行で参照元になったか` で要約し、右カードは `AIがよく扱う論点 / 自社が取れている論点 / 外部が取りやすい論点` を先に読む current shape に寄せています。
2026-04-20 の母数整理で、user-facing の割合と件数は `試行数` を唯一の母数に統一しました。`定点計測` の KPI は `自社露出率 / 自社引用率 / 外部先行率 / 前回比` にそろえ、詳細や質問タイプ別サマリーも `観測した n 試行のうち m 回` の読み方へ更新しています。引用 URL 件数ベースの割合や平均シェアは user-facing KPI から外しました。
同日の追加補強で、結果詳細の内訳は raw row 数ではなく保存済みの `trial_count` を優先して合算するよう更新しました。これにより、current result 復元や rollup fallback が入っても、`n=10` 回と `n=100` 回の差が `1件` 扱いに潰れず、観測回数をそのまま母数として表示します。
同日の first view 追加整理で、左カードの主指標は `自社引用率` だけに絞りました。`自社露出率` は引用されていない候補や言及と混同しやすいため first view から外し、中央カードの参照元説明も回数説明を出さず `今回よく使われた根拠サイト / 根拠ページ` だけが直感で読める形へ簡素化しました。
同日の詳細 UX 追加整理で、結果詳細の折りたたみと URL 状態ラベルから `判定保留` や `候補` といった内部寄りの語を外しました。`根拠に使われた / 見つかったが未採用 / 確認が必要` を軸に、SEO の前提知識なしでも「何を表示しているか」が読める説明へ寄せています。
2026-04-20 の UX 追加実装で、hero と stage header をさらに圧縮し、first view の読み順を `入力 -> 今回の結論 -> 主な参照元サイト -> 頻出論点` に固定しました。`今回の結論` カードを最も強く見せ、中央カードは `ページ名 + サイト名 + 何回の試行で参照元になったか` の上位 3 件に絞り、右カードは `よく扱われる論点 / 次に足す論点` の 2 群だけに圧縮しています。`今回だけの整理` と `保存済みの累積傾向` も別 surface に分け、実URLや質問タイプ別の深掘りは詳細側へ寄せました。
同日の `定期リサーチ` rename と value surface 追加で、`まとめて確認 / 自動更新 / 定期チェック` の UI 語彙は **定期リサーチ** へ統一しました。detail expansion は `今回の結果 / 定点計測 / 定期リサーチ / 設定` の 4 タブ構成になり、hero にはロゴマーク、`LLM見え方観測` サブタイトル、`コトミガキ` / `コトメイク` への cross-link、`前回比` カードを追加しています。
同日の追加整理で、hero 直下には常時表示の **`観測の推移`** カードを置き、`自社引用率 / 外部先行率` の折れ線と最新 `自社引用率` を開閉なしで読めるようにしました。`refresh_hero_status()` は scoped rows から推移グラフ、前回比、hint を動的に更新する current state に変わっています。
2026-04-21 のトップ導線追加で、`実行` カードは `今回を確認する / 継続観測を始める` を同時に読める文言へ更新しました。トップから `定期リサーチ｜今すぐ` と `自動で継続を設定` の quick access を置き、手動実行と定期リサーチを並列の主機能として認知しやすい current state に寄せています。
同日の画面比較後の追加圧縮で、`手順 1/2/3` 見出し、`質問を入力する` などの重複タイトル、`継続観測` の説明ブロックを外しました。現在の first view は `hero / 入力 / 実行モード / 今回の結果 / 観測の推移` を先に読ませ、同じ意味を繰り返す説明を減らしています。
同日の実行モード整理で、トップ CTA は `1回だけ分析 / 複数質問を一括分析 / 自動観測を設定` に更新しました。`定期リサーチ｜今すぐ` や `バッチ` のような内部寄り表現は first view から外し、ユーザーが目的で選べる 3 択にしています。
2026-04-26 の初見 UX 補強で、実行カードは `まずは1回だけ確認` を見出しにし、`1回だけ分析` を主ボタンとして大きく表示する current state へ更新しました。`定期分析を実行` と `自動定期分析を設定` は `継続的に見るなら定期分析` の補助エリアへ下げ、初回行動と継続観測を視覚的に分けています。
2026-04-29 の UI 修正で、hero のロゴ表示は `assets/logo_mark_icon.png` の顔マーク画像へ切り替え、横長SVGの中央文字だけが正方形枠に出て `EC` と見える状態を解消しました。
同日の UX 修正で、手動分析完了後、定期分析の結果反映後、同条件の直近 run 復元後は、下段の `今回の結果 / 定期分析の推移 / 定期分析 / 設定を見る` を自動展開し、`今回の結果` タブを開く current state に更新しました。分析後は結果確認が主行動になるため、詳細を閉じたままにしません。
同日の billing 方針整理で、将来の実クレジット消費は **実行完了時** に固定しました。手動は成功結果保存後、定期リサーチは結果反映完了後に消費し、投入時点・開始前 validation error・provider submit failure・ユーザー停止では消費しない前提です。
同日の表示安定化で、client 背景 task の periodic refresh は結果データに変化がある時だけ dashboard surface を再描画するよう更新しました。再描画が必要な場合もブラウザのスクロール位置を保存・復元するため、分析結果を読んでいる最中に初期位置へ戻りにくい current state です。
2026-04-23 の追加調整で、`今回の結果` を表示中は periodic refresh が `今回の結果 / 結果詳細 / 根拠URL` を再描画しない current state に更新しました。分析後に読んでいる面は固定し、background refresh では hero status の軽更新だけを行います。
同日の詳細整理で、結果詳細の `この画面で分かること`、`見つかったが根拠には使われなかったURL`、`まだ確認が必要なURL` は折りたたみをやめ、固定表示の整理済みセクションとして読む current state に更新しました。
2026-04-23 の安全補強で、prompt injection 検知はゼロ幅文字除去と role-change / context-reset 系パターン追加を含む前処理へ更新しました。あわせて Batch JSONL 一時ファイルは `mkstemp` ベースに切り替え、書き込み失敗時は即削除する current state に更新しています。同日の表示調整で、security signal は internal の保守判定に留め、結果画面には warning 文言として常時表示しない current state に更新しました。検知対象も user query や model output 全文ではなく、検索由来の source title / URL 中心へ絞って false positive を減らしています。
同日の実行方針変更で、単発確認は質問数や内部拡張で見積件数が増えても事前 warning toast を出さない current state に更新しました。現在は manual / batch / scheduled すべてで、query plan 展開後の実送信件数ベースと未import batch の予約コストを含めて guardrail を再評価します。`run_budget_guardrail_usd` を超える見込みの run は開始前に止めます。
同日の起動安全補強はさらに更新され、`ui_host` は loopback 以外では起動しない current state です。認証未実装のため、非loopback は warning ではなく fail-closed で拒否します。
2026-04-24 の競合価値可視化で、first view に `AIが先に見ている相手` の競合スナップショット、詳細に `負けている質問` のミニヒートマップと `回答に効いた根拠サイト` ランキング、頻出論点カードに次の改善 strip を追加しました。既存の citation / source evidence / topic signal / page gap 集計の再表示に留め、新しい LLM 呼び出し、prompt、query planner、スコアリング、DB schema は追加していません。共通ヘッダと TECHIE 共通ブランドシェルも変更していません。
2026-04-25 の商用デモ向け調整で、first view は `AIの主要な参照先` を自社引用率より先に読み、`AI回答に使われた主要ソース` と `改善優先の質問` Top 3、`次に強化すべき論点` までを 3 カード内で判断できる構成へ更新しました。詳細冒頭も `改善判断サマリー` として同じ順序に寄せ、raw URL、生返答、今回の条件は下段へ置いています。コトミガキ側の制作・改善実行機能は追加せず、新しい LLM 呼び出し、prompt、scoring、DB schema も追加していません。共通ヘッダも変更していません。
同日の操作確認で、`今回の結果` が session-scoped の空状態に戻っている場合でも、下段の `保存済み質問ごとの結論` から保存済み DB の結果詳細を選べるようにしました。これにより、新しい LLM 実行を行わずに `改善判断サマリー`、`根拠URLの状態`、`今回の回答と根拠`、`今回の条件` を確認できます。
同日の商用デモ向け cleanup で、設定タブでは `batch_job_id` のような内部 ID を user-facing 文言へ出さず、`__UI_TEST__...` のような test-only 保存名も `保存済み質問セット` / `定期分析` の平易なラベルへ寄せました。
2026-04-26 の商用デモ向け判断 UI 追加で、first view の `AI回答に使われた主要ソース` カード内に `根拠の安定度` を追加しました。自社 / 比較対象 / 外部サイトの比率、依存リスク badge、上位ソース集中度を既存 evidence / citation 集計だけで表示し、raw URL は引き続き詳細側へ下げています。
同日の詳細整理で、`改善判断サマリー` の冒頭に `根拠の安定度 / 見え方の安定度 / 弱い質問タイプ` の 3 panel を追加しました。`見え方の安定度` は保存済み rollup の観測回数、自社引用回数、外部先行率、揺れ幅を読み替え、`弱い質問タイプ` は既存の質問タイプ別 heatmap を user-facing の Top 3 として見せています。新しい LLM 呼び出し、prompt、query planner、scoring algorithm、DB schema、保存項目は追加していません。
同日の初見 UX 補強で、未実行時や入力変更後の `今回の結果` は `今の入力では未分析` と明示し、保存済みの旧結果を今回面に混ぜないことをカード上部と空状態で示す current state に更新しました。`保存済みの累積傾向` は `過去データ` ラベル、淡い別背景、左罫線、`今回の入力とは別集計` chip で分け、詳細冒頭には `外部サイト依存 -> 見え方の揺れ -> 弱い質問タイプ` の優先度ストリップを追加しています。これらはすべて既存保存データの見せ方変更で、新しい LLM 呼び出し、分析ロジック、DB schema、保存形式は変更していません。
2026-04-26 の起動・refresh 根本修正で、`keyword_result(analyzed_at DESC)`、`keyword_result(run_id, analyzed_at DESC)`、`source_url(result_id)` の index を追加し、`list_recent_results` と `list_sources` の full scan を解消しました。あわせて `Storage()` import 時の同期 enrichment backfill をやめ、起動後 background maintenance で最大 250 件ずつ、source URL は一括取得して補完します。完了後は `PRAGMA user_version` marker で同じ backfill を再実行しません。
同日の修正で、dashboard refresh は 1 回作った payload から current result 復元、refresh signature、hero status、主要カード、詳細を更新する current state へ変わりました。`定期分析の推移` タブ内の詳細 Plotly は初期表示で生成せず、タブ表示時に lazy mount / lazy refresh します。HUB と `techie-hub\start.bat` は引き続き `/healthz` を使い、full UI `/` を定期 health check に戻しません。
2026-03-31 の最終調整で、最新結果カードの判定基準明示、結果一覧の列名見直し、棒グラフ見出しの整合、`reasoning_effort=none` の UI 選択肢追加、実ブラウザエンジンでの live run / stop 確認まで完了しました。
同日の追加調整で、上段を「現状判定 / 競合との位置 / 優先アクション」に再構成し、質問ごとの verdict-first UI と根拠URLの「自社 / 競合 / 外部サイト」分類表示まで反映しました。
同日の追加実装で、通常の同期実行を維持したまま OpenAI Batch API を使う `Batchモード` を追加し、`Batch投入` / `Batch状態確認` / `Batch結果取り込み`、ローカルDBでの Batch job 追跡、既存一覧への取り込みまで反映しました。
同日の追加調整で、通常実行の送信順を `keyword -> repeat` に変更し、複数質問時も同一質問を連続送信することで prompt caching 効率を優先する形に更新しました。
同日の表示調整で、曖昧だった `拮抗` を廃止し、判定ラベルを `自社優勢 / 自社あり / 外部サイト優勢 / 未露出` の4段階に整理しました。
同日のUI調整で、勝ち筋グラフを横棒化し、グラフ対象を現在入力中の質問と自社URLに合う結果へ絞って、過去の試験質問が混ざらないようにしました。
同日の追加調整で、上段の `優先アクション` は質問名つき表示へ寄せ、Batch 操作は通常実行の主導線から折りたたみ側へ退避しました。
同日のヒーロー調整で、ロゴの横にサービス名と価値要約を置き、起動直後に何が分かるツールかを読み取りやすくしました。
2026-03-31 の追加整理で、ヒーローを初期画面の 25% 以内に収まる薄い構成へ圧縮し、主画面は visibility trend を先に見る構成へ寄せました。
同日の配色整理で、ブランド強調色と状態表示色を分離し、自社 / 競合 / 外部 と補助情報の意味が画面全体でぶれない方向へ揃えています。
2026-04-01 の追加実装で、`市場観測` と `自社監査 (Owned-only Audit)` の切り替え、`Intent Map`、`Page Gap Navigator`、`Run Guardrail` を追加し、結果一覧と最新結果カードを `判断 -> 制作着手` 寄りに更新しました。
同日の UI 整理で、フォントを `Sora + Noto Sans JP` へ寄せ、`card-primary / card-secondary / card-detail` を含む共通トークン名へ再編し、3製品共通シェルの基準実装に近づけました。
同日の追加整理で、`techie-hub` を中心にした TECHIE 共通デザイン原則と、`kotomegane` を先行実装にする design implementation plan を新設し、次回セッションでは `kotomegane` をデザイン込みで完成させてから他サービスへ展開する方針を固定しました。
同日の PoC 拡張で、`Question Sets`、`Scheduled Batch Run`、`run_session` snapshot、`answer_text + citations` 保存、`全体 visibility trend / Intent Cluster Trend / Page Gap Trend / Query Drill-down`、`raw_results.csv / weekly_summary.csv / raw_results.json` export まで反映しました。
同日の追加実装で、detail card の手動 `Page Brief Generator`、`answer_text + citations` からの構造化抽出、schedule の `削除 / 複製 / diff` UI、既存 row の backfill、金額表示を外した `Run Guardrail` まで反映しました。
同日の追加拡張で、`Intent / Page Gap / Question Set` 単位の `Cluster Brief Generator`、保存済み brief の再表示、schedule / question set 系列から辿る `Outcome Compare`、raw answer tuning、schedule 初回保存の bug fix、timezone fallback、実ブラウザでの主要導線確認まで完了しました。
同日の UI 改善で、主要見出しと操作名を日本語へ統一し、主画面を `入力する / 結果を見る / 詳細を使う` の 3 段導線に再整理して、初見の操作と詳細運用が混ざらないようにしました。
2026-04-01 のブランド調整で、ヒーローのロゴを `aio2-main` / `notecode` と共通の `assets/logo_mark.svg` に揃え、ファビコンも同一の `favicon_v2.png` へ統一しました。
2026-04-01 の追加整理で、入力を最初に固定し、主結果を `自社が出たか / 外部名・外部サイト / 次に見直す質問` の 3 カードへ絞り、詳細側を `運用` / `詳細` の 2 タブへ再編しました。
2026-04-01 の micro polish で、上部ナビを小さい幅でも崩れにくい並びへ圧縮し、ヒーロー文言を「何を入れて何を見るか」が一読で分かる表現へ更新し、主結果3カードを先に読ませる順序へ寄せました。
同日の最小化調整で、UI から `自社監査` 切り替えと `確認回数` 表示を外し、内部では 20 回反復しつつ、`質問ごとの判断一覧` を詳細タブへ下げ、`詳細設定` も競合語だけに絞りました。
2026-04-01 の追加最小化で、主画面は `入力 -> 分析を実行 -> 主結果3カード` を先に見る構成へさらに絞り、`全体の傾向`、意図/不足ページ、推移グラフ、比較/下書き、根拠URL、結果一覧は `詳細を見る` の詳細タブ側へ集約しました。
同日の追加調整で、`workflow rail` を外し、`設定を保存` を主画面から退避し、主結果3カードの入れ子ブロックを減らして Google / Notion 寄りの静かな見え方へ寄せました。
同日の追加調整で、`結果を見る` は実行後だけ表示する形にし、`一括実行` を `まとめて確認`、`定期バッチ実行` を `定期チェック` に言い換え、`接続先` は `ChatGPT / Gemini / Claude` の chip 表示へ縮小しました。
2026-04-02 の UI 再編で、`ai_studio_code.py` を参照したダッシュボード骨格を現行 `app.py` に取り込み、ブラウン / クリーム基調 + オレンジ強調へ配色を戻しつつ、ヒーローは `コトミガキ` 寄りの compact H1 に圧縮し、上段は `コトメガネ` のブランド名だけを短く見せる構成へ更新しました。右側は `ChatGPT / Gemini / Claude` の文字ベース接続表示で、現在は OpenAI / Gemini / Claude の手動確認導線を持ちます。
同日の追加整理で、ユーザー向け UI では内部モデル名を出さず `ChatGPT / Gemini / Claude` の provider 名だけを表示し、OpenAI は explicit prompt cache、Gemini は implicit cache 既定 + explicit cache 1時間、Claude は automatic cache 5分 + Batch best-effort という provider 差分を registry と runtime 文言側へ寄せました。
同日の追加整理で、主結果の下に `ダッシュボード概要` の KPI 群と主要推移を追加し、保存済み結果がある場合は起動直後から上段ダッシュボードを表示する形へ寄せました。
2026-04-03 の追加整理で、`ダッシュボード概要` の主役KPIを `自社露出率` 優先へ寄せ、履歴の主役を `AI visibility スコア推移` と `自社露出率 / 外部サイト優勢率の推移` に整理しました。
同日の source 表示整理で、user-facing の URL は `回答で実際に citation として出た URL` を中心に扱い、consulted-only の内部 source は前面に出さない方針へ揃えました。
同日の追加実装で、`query_plan` 保存、長文質問の内部短文化、`拡張検索`、同一 `expansion_signature` 条件での `前回比サマリ`、定期チェックの `開始時刻` 文言まで反映しました。
同日の SaaS 実装着手で、provider capability registry に `default model / 総質問数上限 / batch timeout / partial display policy / cache policy / expansion mode` を追加し、manual / batch / scheduled batch が同じ execution plan と送信順序を使うよう揃えました。query planner は provider ごとの上限を見て拡張質問数を抑える形へ更新しています。
同日の追加補強で、query plan 再利用は `planner_signature` 一致時だけに絞り、provider / planner 条件差をまたいだ再利用を避ける形へ更新しました。batch import では `executed_query` と `user_query_raw` を分けて保持し、manual / batch / scheduled の query identity を揃えています。
同日の追加整理で、`prompt_catalog.py` を追加し、fallback expansion を `managed prompt taxonomy` へ寄せました。`比較 / 料金 / 事例 / FAQ / サポート / 評判 / 導入不安 / 手順` の prompt family を保存し、generic expansion だけでなく管理された内部質問セットとして detail / export で読めるようにしています。
2026-04-04 の追加実装で、`analysis_core/source_evidence.py` を追加し、`citations_json / output_json.citation_urls / source_url` を突き合わせて URL 状態を `引用された / 検索ソースに出たが未引用 / 不明` に整理しました。主画面では quoted external を先に見せ、未引用と不明は detail の折りたたみへ下げています。同時に managed prompt taxonomy の `prompt family` ごとの source 集計を追加し、source 根拠ベースの優先アクション 3 件へ反映しました。
2026-04-05 の追加整理で、`prompt_taxonomy_json` がない既存 row も `executed_query / keyword_raw` から prompt family を runtime 推定できるようにし、detail は `質問の系統ごとの見え方 -> 改善メモ -> 根拠URL` の順で読む構成へ寄せました。`不明` は失敗ではなく `判定保留` として説明し、main 側の優先アクションも family 主体の文言へ更新しました。
同日の追加整理で、入力カードに `最初の進め方` を追加し、detail に `この結果の読み方` を追加しました。あわせて export は `report_summary.md` を含む形へ拡張し、運用タブ内で報告用まとめのプレビューを見られるようにしました。
同日の追加実装で、LLM が返した `visibility_score` は `raw_llm_score` として保存し、UI 主表示は rule-based の `deterministic_score` へ切り替えました。deterministic score は `自社URL hit / ブランド hit / 自社引用数 / 自社引用シェア / 競合出現 / external only / answer type` から算出します。
同日の追加整理で、run / query rollup に `median / min / max / stddev / variance_label` を追加し、主画面 KPI、前回比、detail、比較、export で揺れ幅を確認できるよう更新しました。
同日の UI 整理で、`運用` タブ内の `確認内容 / 定期チェック / まとめて確認 / 出力` を折りたたみ化し、主画面では `分析を実行` を主CTAに固定したまま、補助文と通知文を短くして初見の読み量を減らしました。
同日の追加整理で、`手動 / まとめ確認 / 定期チェック` の mode 別 microcopy と内部課金説明を明示的に分け、表示と内部ルールが混ざらないようにしました。
同日の追加整理で、desktop では左サイドの dashboard nav を表示し、`入力する / 今回の結果 / 定点計測 / 設定` へ直接移動できるよう更新しました。初見ユーザー向けに「まず何をするか」を左導線でも読める形へ寄せています。
同日の runtime 調整で、ページ切断時は periodic refresh timer を停止し、client delete 時に cancel するよう更新しました。`techie-hub` からの遷移や切断後に `The parent slot of the element has been deleted.` が連発しにくい形へ寄せています。
同日の UI 最終整理で、ヒーローには `対象AI / 最終更新` だけを残し、provider 切り替えは `設定` 側へ移しました。詳細側は `分析 / 設定` の 2 タブへ改称し、KPI は `自社露出率 / 自社引用率 / 外部先行率 / 前回比` の 4 つに絞っています。検索回数、繰り返し回数、内部質問、cache / reasoning、`クラスタ下書き作成` など内部寄りの表示は主導線から外しています。
同日の追加整理で、入力欄は `質問` 側を広く、`自社の情報` 側を補助入力寄りの幅に調整しました。`質問ごとの結論` 一覧は `質問 / 結論 / 競合との位置 / 不足している情報タイプ` へ絞り、分析タブ内の情報密度を下げています。
同日の局所修正で、手動実行カードに `分析中` スピナーを追加し、進行中かどうかが画面内で分かるようにしました。さらに進捗は `0-1` ではなく `%` と `件数` で表示し、単発確認の内部反復数は定点計測の半分へ落として体感時間を縮めています。あわせて OpenAI adapter の `SourceItem` import 抜けを修正し、引用ソース抽出時に `name 'SourceItem' is not defined` で全体が 0 判定に崩れる状態を解消しています。
2026-04-14 の progress copy 補強で、manual run 中の status は `元質問 x/y / 拡張質問 x/y / 繰り返し x/y` を出し、spinner も `分析中 n/N` で全体位置を追えるよう更新しました。さらに同日の runtime 調整で、manual run は各繰り返し内の拡張質問を並列実行し、進捗バー・進捗説明・停止文言は同じ並列グループ完了数を基準にそろえています。deleted client の RuntimeError に対しては dashboard 再描画側でも guard を追加し、長時間 run 中の切断後に `The parent element this slot belongs to has been deleted.` が surface しにくい current state に更新しました。
2026-04-20 の manual run 初動補強で、`分析を実行` を押した直後は query plan 準備中でも progress bar を 0 のまま出さず、わずかに進んだ状態を先に描画する current state に更新しました。run session 発行後にももう一段だけ進めてから planner 準備へ入るため、押下直後の無反応感を減らしています。
同日の追加 UX 補強で、manual run のクリック直後は CTA 表示を `分析中...` に切り替え、progress bar 下に `現在 / 状態` の activity 文言を出すよう更新しました。初期 progress も 1-2% ではなく視認しやすい準備量へ寄せ、Nielsen の visibility of system status を満たしやすい current state に寄せています。
同日の追加安定化で、manual run 開始前に `refresh_dashboard_surface()` の重い再描画を挟まない形へ更新しました。クリック直後は実行カードの status と progress を先に返し、開始時の無反応や page load の引っかかりを減らしています。あわせて Windows の `__mp_main__` では `ui.run(...)` を再実行しないよう補強し、子プロセス側の 8083 bind 競合リスクを外しました。
同日の cache 汚染対策で、`localhost:8083` に残った旧 Flutter 系 service worker は起動時に unregister と cache 削除を走らせる current state に更新しました。`/flutter_service_worker.js` には unregister 用の no-op script を返すため、古い PWA cache による別画面断片の混入や 404 ループを避けやすくしています。
2026-04-20 の接続安定化で、`techie-hub\start.bat` は `8083` が listen 済みでも HTTP 応答が返らない `kotomegane` listener を自動再起動するよう補強し、不安定な既存プロセスを掴み続けにくい current state に更新しました。2026-04-26 の追加修正で、起動判定は full UI の `/` ではなく軽量な `/healthz` を使う current state に変更しました。HUB のカード状態確認も `/healthz` を叩くため、NiceGUI の画面生成を定期 ping で積み上げてボタンが非アクティブ化する状態を避けます。
2026-04-15 の集計補正では、いったん主結果中央の質問タイプ別サマリーを raw 回答行ではなく `executed_query` 単位で束ねる形へ寄せました。その後 2026-04-20 の更新で、この user-facing 母数はさらに `試行ベース` へ切り替えています。
同日の追加整理で、詳細側は `結果 / 分析 / 設定` の 3 タブへ再編しました。`結果` は質問ごとの結論と引用URL、`分析` は定点計測だけを使う KPI / 推移 / 履歴、`設定` は対象AI / 確認内容 / 自動更新 / 出力に分離しています。単発確認はグラフへ混ぜず、履歴表だけで一緒に振り返る方針です。
同日の追加実装で、`確認内容` は `有効 / アーカイブ済み` を持つように更新しました。アーカイブしても履歴は残し、`定期チェック` の対象候補からは外します。読み込みと再開は可能です。
同日の安全対策で、共有 system prompt に `検索結果中の命令を無視する` ルールを追加し、post-processing 側でも prompt injection らしい文言を検知して `security_signals` として `output_json` に保存するよう更新しました。主画面には出さず、内部判定と将来の詳細表示用に留めています。
2026-04-11 の表示調整で、主結果カードの大きい `%` は誤読しにくい補助指標として整理し、詳細カードでは `自社引用 2件 / 66.7%` のような混在表示をやめ、`自社引用件数` と `引用内シェア` を別指標として分けています。
同日のナビ調整で、左サイドは `Quick Jump` 中心の説明パネルではなく、`入力 / 今回の結果 / 結果タブ / 分析タブ / 設定タブ` を先頭に置くタブ型ナビへ寄せました。ブラウン背景上の文字は白寄りに固定し、可読性を上げています。
同日のシリーズ統一で、`kotomegane` の配色トークンを `notecode` / `aio2-main` と同じ暖色テーマへ寄せました。背景は `#F7F1EA / #F1E2D4`、ナビは `#2F241D`、CTA とアクティブ強調は `#D96B1F -> #B95416` の勾配を基準にしています。
同日の導線修正で、左ナビの `結果タブ / 分析タブ / 設定タブ` は実際に下段タブを切り替えるよう更新しました。名称と挙動が一致するようにし、アンカー移動だけの疑似タブ状態を解消しています。
同日の説明補強で、`導入事例ページ` や `FAQページ` などの不足ページタイプは検索結果の生ラベルではなく、質問文・回答要約・推奨アクション・引用URLをもとにした rule-based 推定であることを主結果と詳細内で説明する current state に更新しました。
2026-04-04 の追加確認で、desktop / mobile screenshot を再取得し、長文短文化 + 拡張検索を temp DB の live run で再確認しました。`query_plan` は raw export / detail に出し、`weekly_summary` には週次集約に加えて variance 列も出す current decision に更新しています。同日の局所修正で、OpenAI 応答の `citation_urls` 末尾切れによる JSON truncation 時も verdict / answer / citations を回収できる fallback recovery を追加しました。さらに同日、OpenAI live manual / batch verification を temp DB で追加実行し、manual の fallback 未発生と batch の submit / refresh / import 完了まで確認しました。同日の追加実装で、Gemini manual/live adapter、Claude manual/live adapter、Gemini / Claude provider batch adapter、app 単位の provider allowlist hook、起動時の複数 provider API key 検出を追加しました。Gemini は `gemini-2.5-flash-lite` + `google_search`、Claude は `claude-3-5-haiku-latest` + `web_search tool` 前提です。
同日の UI 再整理で、`zip\src\pages\Megane.tsx` を見本に、上段を `入力または実行条件`、中段を `今回の結果` 3 カード、下段を `分析 / 設定` に寄せました。固定UIは muted chip / card、実行結果は `今回の結果` chip と強い背景差で分け、主画面で「まず何を見るか」が分かるよう調整しています。
2026-04-05 の追加整理で、外部エンジニア向けの最小共有用として `external_engineer_handover_2026-04-05/` を追加し、概要、コードマップ、DB概要、設定サンプル、sample export、ディレクトリ構造図をまとめました。
同日の docs 整理で、`Saa S基盤設計.docx` を補助元にしつつ、Azure移行 / 3製品共通基盤方針を `docs/cross_product/TECHIE_SUITE_PLATFORM_PLAN_2026-04-05.md`、LLM の Batch / prompt cache 運用方針を `docs/LLM_BATCH_AND_CACHE_RULES_2026-04-05.md` に markdown 正本として分離しました。料金プランは引き続き検討中です。
同日の追加整理で、`docs/` 直下は `kotomegane` 本体の正本だけを残し、セッション用メモは `docs/session_notes/`、横断資料は `docs/cross_product/` へ移動しました。
2026-04-09 の役割整理で、主画面・入力前説明・結果詳細の読み方を `コトメガネ = 観測`、`コトミガキ = 改善` と明示する日本語文言へ更新しました。`aio2-main` 側と同じ改善UIに見えないよう、`ここはAI回答での見え方を測る画面` であることを画面内で読める形へ寄せています。
2026-04-10 の UI 改修で、主結果 3 カードを `AIはどう答えたか / なぜその判定か / 次に直すポイント` へ更新しました。URL は生の一覧ではなく `自社 / 競合 / 外部` と `引用 / 候補 / 判定保留` の意味ラベル付きで読ませる構成へ寄せ、`根拠URLの意味` と `URLごとの意味` テーブルを追加しています。同日の追加改修で、stopword を考慮した軽量トピック抽出を導入し、`競合・外部が取った論点`、`自社候補に出た論点`、`優先して足す論点` をチップで表示するよう更新しました。これは `C:\textresearch` の `semantic_network` / `topic_analysis` を移植したものではなく、network graph や BERTopic を含まない軽量版です。さらに `分析` タブに `質問ごとの結果` ヒートマップを追加し、質問ごとの勝敗状態を色で直感的に読める構成へ更新しました。2026-04-11 の追加調整で、ヒートマップのセルから `結果` タブの `詳細を見る質問` へ直接連動し、その質問の詳細へすぐ戻れる導線を追加しました。
2026-04-11 の追加整理で、ヒーローと主画面上段は `観測ツール` よりも `改善判断ツール` として読めるよう文言を更新しました。起動直後の一読目を `AIは誰を薦めたか / その根拠は何か / 次にどのページを直すべきか` に固定し、結果サマリーと主結果3カードの見出しも同じ判断軸に揃えています。あわせて主結果上段から `内部検索回数` チップを外し、判断に不要な内部寄り情報を減らしました。
2026-04-12 の PC 向け修正で、主結果 1 枚目は raw `answer_snapshot` の表示を外し、deterministic 判定と整合する要約だけを残すよう更新しました。これにより、カード内で `自社優勢` と `第三者が優勢` が同時に読めてしまう矛盾を解消しています。同日の追加修正で、主結果 3 枚目は `priority_label` が `維持` のときに `不足` ではなく `先に厚くする候補` として読ませるよう変更し、`導入事例ページを直すべき` と `不足している見え方はまだありません` が同居する状態を解消しました。さらに主結果 2 枚目は根拠URLを 3 件までに絞り、件数や論点ラベルを補助へ下げて、PC で 3 カードを比較しやすい密度へ寄せています。
同日の追加整理で、主結果 1 枚目は `%` を主役から外し、`今回の結論` を大きく読ませたうえで補助指標に下げる形へ更新しました。
2026-04-13 の表示修正で、主結果 1 枚目の補助指標は `今回の回答回ベースの自社露出率` を主表示に戻し、`50回中8回 = 16%` のような揺れをそのまま読めるようにしました。関連質問を含む run では `関連質問カバレッジ` を別行で補足し、単一質問の繰り返しで `100%` と誤読される状態を避けています。
同日の追加整理で、主結果 2 枚目は `自社ページが根拠を押さえています` のような抽象表現をやめ、`AIは今回は自社ページを主な根拠にしている / 外部サイトを主に参考にしている` などの平易な文へ差し替えました。
同日の追加整理で、主結果 2 枚目には current-run 内の `比較 / 料金 / FAQ / 事例` などの質問軸をそのまま並べず、`比較検討では自社が見つかりやすい / 料金説明は外部を見られやすい` のような短文へ変換して添える形へ更新しました。
同日の追加整理で、主結果 2 枚目の URL 並びは見出しと矛盾しないよう、`自社が主な根拠` のときは自社URLを先に見せる順へ更新しました。
同日の追加整理で、主結果 3 枚目は `今すぐ直すページ` と `次に強化する候補` を明示的に分け、緊急修正がない場合は `いまは大きな欠落なし` と一目で読める構成へ更新しました。
同日の追加整理で、結果タブ上段は `今回の結果の整理` と `保存済みの累積傾向` に分離し、後者が今回 1 問の結果ではなく保存済み質問の累積集計だと分かる見出しへ更新しました。2026-04-20 の UX 追加実装では、これをさらに `今回だけの整理` と muted surface に分け、current result と saved aggregate の粒度差を見た目で分かるように更新しています。
同日の追加整理で、`その根拠は何か` カードと結果詳細の根拠URL欄は初期表示を `実際に引用されたURL` のみに絞り、候補URLと判定保留は折りたたみへ逃がしました。
同日の追加整理で、`分析` タブは `定点計測` に改称し、単発確認を fallback 表示しない空状態メッセージへ更新しました。
2026-04-14 の再接続修正で、ページ再描画時の初期 config はアプリ起動時の固定 snapshot ではなく `config/llmo_poc_settings.json` の最新保存値を読み直すよう更新しました。これにより、直前に実行した質問 / 自社URL に一致する current result の復元を優先し、古い質問が入力欄へ戻る状態を避けます。
2026-04-13 の局所修正で、`分析を実行` が `resolve_run_policy` の import 抜けにより開始直後の `NameError` で止まり、見た目だけ無反応になる不具合を修正しました。`on_run` は開始直後に `分析中` スピナーと進捗表示を先に更新し、起動時の予期しない例外も UI の status / notify へ返すようにしています。
同日の UX 調整で、`今回の結果` は「このセッションで直前に実行した分析結果」だけを表示する current decision に更新しました。起動直後や質問・対象AI・自社情報・確認内容を変えた直後は待機状態メッセージを出し、保存済みの旧結果は `保存済みの累積傾向` と履歴側で確認する形へ寄せています。
同日の SaaS 系列統一で、`top-shell` と左 drawer の濃いブラウンを `techie-hub` / `notecode` / `aio2-main` と同じ `#2F241D` 基調へ揃え、主CTA の勾配も `#D96B1F -> #B95416` に統一しました。TECHIE HUB から遷移したときの同一サービス感を優先しています。
同日の runtime 整合で、`config/llmo_poc_settings.json` の `ui_port` を `8083` に戻し、`techie-hub\start.bat` と AGENTS の既定ポート前提に合わせました。
同日の追加調整で、主結果カードの空状態見出しは `最新結果` ではなく `今回の結果` に統一し、実行カードには `2分以上変化がなければ再実行を検討してください` の回復ガイドを追加しました。見出しの一貫性と長時間待ち時の判断材料を優先しています。
同日の追加補強で、手動実行中は `分析を停止` ボタンを表示し、現在の並列グループが終わった時点で止める best-effort cancel を追加しました。停止時は途中結果を `今回の結果` 面へ昇格させず、同条件での再実行を促します。
同日の SaaS 役割整理で、hero を `コトメガネ = 観測して決める`、`コトミガキ = 改善を実行する` の 2 製品フローとして再構成しました。説明文を増やすのではなく、2 枚カードと handoff 矢印で `ここで見る / 向こうで直す` を視覚的に読ませる方針へ寄せています。
2026-04-14 の実画面レビューで、`techie-hub` / `notecode` / `aio2-main` と見比べた結果、shared top shell に対して `kotomegane` の permanent left drawer が別ソフト感を強めていると判断しました。current state は drawer を持たない wide content layout へ更新し、上段の観測サマリーと下段の `入力 -> 今回の結果 -> 必要なときだけ詳しく見る` に集中する構成へ寄せています。
同日の追加修正で、`設定` タブから `まとめて確認` を再度開けるよう戻し、batch の `開始 / 進み具合更新 / 結果反映` と履歴テーブルを本番 UI で追えるようにしました。当時はいったん質問単位の KPI 整理を行いましたが、現在の user-facing はさらに `観測試行数` ベースへ更新済みです。
同日の runtime 修正で、一時検証用に残っていた `config/llmo_poc_settings.json` の `ui_port=8098` を `8083` へ戻しました。さらに、長時間の手動 run 中に client が切断された際は safe UI update で `The parent slot of the element has been deleted.` を握り、runtime 全体の例外連鎖を避ける current state へ更新しました。
同日の UI 再定義で、主入力は `質問 / 自社URL / 名称 / 重点テーマ` を正本とし、`名称` は任意入力へ更新しました。比較したい相手は折りたたみの `比較対象` に下げ、回答文や citation URL タイトルから見つかった他社名・媒体名・団体名は断定せず `比較候補` として扱います。
同日の追加実装で、質問文から `地域 / 業界 / 用途` の候補を軽量推定し、質問欄近くで `候補` と `反映` ボタンを表示できるようにしました。推定値で入力欄を自動上書きせず、ユーザー手入力の `重点テーマ` を優先します。
同日の主画面整理で、first view は `質問を入れる -> 実行する -> 今回の結論 / 主な参照元サイト / 頻出論点` を主役に再編しました。`直近の観測サマリー`、`論点のつながり`、`比較候補` は main surface から外し、詳細で追う構成へ寄せています。2026-04-20 の UX 追加実装では、first view 直前の補助文を 1 行までに縮め、中央カードは上位 3 件、右カードの論点 chip は 2 群までに制限しました。

## Current Product Shape

- サービス名: `コトメガネ`
- 目的: 設定した質問に対して `自社が見えているか / 何が評価されているか / 自社が強い軸 / 次に足すもの` を短時間で判断し、改善判断につなげる
- UI: NiceGUI ベースのブランド付き PoC ダッシュボード
- UI トーン: ブラウン / クリーム基調 + オレンジ強調。ロゴ資産は現行のまま利用
- ブランド資産: `assets/logo_mark.svg`、`assets/logo_mark_icon.png`、`assets/favicon_v2.png`
- 補助の旧ロゴ資産: `assets/kotomegane-logo.svg`
- 既定ポート: `8083`
- 主入力: `質問 / 自社URL / 名称(任意) / 重点テーマ(任意)`
- 補助入力: `比較対象` は任意かつ折りたたみで扱う
- `市場観測` では主入力の `自社URL / 名称 / 比較対象 / 重点テーマ` を LLM に渡さず、post-hoc のローカル照合だけに使う
- 推定補助: 質問文から `地域 / 業界 / 用途` の候補を出し、明示操作で `重点テーマ` へ反映できる
- 主画面の見せ方: 入力を最上段に置き、`実行` カードでは `1回だけ分析` を主ボタンとして見せる。`定期分析を実行 / 自動定期分析を設定` は継続観測の補助導線へ下げる。first view は `hero / 入力 / 1回だけ分析 / 今回の結果 / 観測の推移` を優先し、未実行時や入力変更後の `今回の結果` は `今の入力では未分析` と明示する。実行後は `今回の結論 / 主な参照元サイト / 頻出論点` の 3 カードを先に読む。hero の補助情報は `対象AI / 最終更新 / 前回比` に固定する

## Main Files

- `app.py`
  - ブランド UI、本体画面、入力 / 結果 / 分析 / 設定の導線、compact H1、`改善判断ツール` ヒーロー、`AIは誰を薦めたか / その根拠は何か / 次にどのページを直すべきか` の主結果 3 カード、KPI 4 枚、質問別ヒートマップ、主要グラフ、質問セット、定期リサーチ、結果詳細カード、推移グラフ、export、テーブル
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
- `ui/page_refreshers.py`
  - question set / schedule / batch / cluster brief の admin view、dashboard / cluster brief / outcome compare / export preview の再同期手順
- `ui/dashboard_view_models.py`
  - active scope filter、tracking scope filter、前回比判定、結果テーブル行、dashboard refresh 用 read-model 準備
- `ui/dashboard_refreshers.py`
  - summary / decision / tracking widget の UI 更新反映
- `ui/cluster_brief_builders.py`
  - selected cluster token の解決、candidate 抽出、cluster rows の組み立て、cluster brief save payload の組み立て
- `ui/dashboard_views.py`
  - ダッシュボードの refresh orchestration、集計結果の反映、各描画 section の呼び出し
- `ui/result_story_builders.py`
- 主結果 3 カードの文言、参照元サイト/ページの試行数ベース集計、結果タブ集計文言、優先アクション、不足情報の集計
- `ui/evidence_presenters.py`
  - 根拠URLの owner/status 整形、意味ラベル、並び順、テーブル行の shared helper
- `ui/result_cards.py`
  - 主結果 3 カードと `主な参照元サイト` セクションの NiceGUI 描画
- `ui/market_context_helpers.py`
  - `重点テーマ` の分解/正規化、`地域 / 業界 / 用途` の軽量推定、候補表示用 helper
- `ui/comparison_candidate_builders.py`
  - 手入力 `比較対象` の優先表示と、回答文 / citation タイトルからの `比較候補` 抽出・軽量分類
- `llmo_client.py`
  - OpenAI / Gemini / Claude の provider client
  - `web_search`
  - prompt caching 設定
  - provider ごとの Batch request 生成 / batch create / retrieve / result import
  - provider client factory
- `query_planning.py`
  - 長文短文化、拡張検索、前回 plan 再利用、expansion signature 生成
- `prompt_catalog.py`
  - fallback expansion の source of truth
  - prompt family / label / purpose の taxonomy owner
- `市場観測` では `allowed_domains` を soft preference として扱う
- `自社監査` backend は残るが、現行 UI の主導線は市場観測固定
  - `answer_text` と `citations` を返す compact JSON を要求する
  - `reasoning=minimal` が残っていても `low` へ fail-safe 補正
- `analysis_lib.py`
  - スコア算出、履歴整形、内部コスト計算補助
  - intent 分類、page gap 推定、run guardrail 集計
  - raw answer 構造化、brand alias / citation domain / answer type tuning
  - URL 状態の整形、prompt taxonomy ごとの source 集計、source 根拠ベース action 整形
  - 軽量 topic signal 集計と stopword ベースの論点チップ生成
  - row / cluster page brief draft 生成
  - schedule 計算、run snapshot 集計、outcome compare、trend/export 用の整形
- `storage.py`
  - SQLite 保存
  - `question_set` / `schedule_plan` / `query_plan` / 拡張 `run_session` / 拡張 `keyword_result`
  - raw answer 構造化列の migration/backfill
  - `cluster_brief` 保存
  - `batch_job` / `batch_job_item` で Batch job と request item を追跡
- `scheduler_runtime.py`
  - scheduled batch submit
  - scheduled batch poll / import
  - schedule 状態更新
- `config.py`
  - 設定ロード、保存、価格設定、provider catalog、`run_budget_guardrail_usd`
  - API キー解決状態の判定（`.env` / 環境変数）
- `config/llmo_poc_settings.json`
  - 現行設定ファイル
- `exports/`
  - `raw_results.csv`, `weekly_summary.csv`, `raw_results.json` の出力先
- `setup.ps1`
  - ローカル Python を使った `.venv` 作成と依存導入
  - `.env` / 環境変数の案内
- `run.ps1`
  - `.venv` 固定の起動導線
  - kill-on-close job wrapper で runtime process tree を管理
  - runtime launcher / base interpreter の表示
  - API キーソースの事前表示
- `stop.ps1`
  - 8083 listener と runtime process tree をまとめて止める終了導線

## Confirmed Changes

- `techie-hub/start.bat` は `kotomegane/run.ps1` と `kotomegane/stop.ps1` を使って起動/force-stop するよう更新済み
- `techie-hub/start.bat` は `8083` が既に listen している場合も `http://127.0.0.1:8083/healthz` で runtime health を確認し、応答しない既存 listener は `stop.ps1` 後に再起動する。UI 変更を確実に反映したいときは `start.bat force` か `stop.ps1` 後の再起動が必要
- 2026-04-14 時点の current config は `ui_port=8083` に戻してあり、TECHIE HUB の `見え方観測` 導線からそのまま同じ port を開く
- `techie-hub/index.html` の `コトメガネ` 表示文言は現行 PoC 向けに調整済み。カードの起動判定は `/healthz` を使い、full UI `/` を定期的に生成しない
- root は PoC 中心構成に整理済み
- UI は compact hero / 入力 / 主結果 / `詳細を見る` の情報階層に整理済み
- permanent left drawer は current UI から外し、top shell + wide content card を TECHIE スイート共通の見え方に寄せた
- 主入力は `質問 / 自社URL / 名称 / 重点テーマ` を正本とし、`競合` は main surface から外した
- `比較対象` は任意入力として折りたたみ側へ下げ、回答や citation URL から出た他社名・媒体名・団体名は `比較候補` として表示する
- 質問文から `地域 / 業界 / 用途` の候補を軽量推定し、`候補を反映` でだけ `重点テーマ` に取り込む。手入力後は自動上書きしない
- 露出サマリーは、数字の列挙ではなく「現状判定 / 競合との位置 / 優先アクション」を先に読む構成へ更新済み
- 主結果 3 カードはさらに、`今回の結論 / なぜそう言えるか / 今すぐ直すか次に強化するか` を先に読む構成へ更新済み
- URL は raw list ではなく `自社 / 競合 / 外部 × 引用 / 候補 / 判定保留` の意味で表示する current decision に更新済み
- `根拠URLの意味` と `URLごとの意味` テーブルを追加し、どのURLが根拠なのか、候補止まりなのかを説明なしでも読める形へ更新済み
- 主画面では `共起` を主役にせず、stopword 除去・brand/domain 除外・alias 正規化を使った `評価される軸` を先に表示する
- 主画面の URL 露出は最小化し、詳細側で `引用 / 候補 / 判定保留` を追う current decision に更新済み
- `定期リサーチ` タブは概要とショートカットだけを置き、実操作は `設定` タブの `定期リサーチ｜今すぐ実行（バッチ）` / `定期リサーチ｜自動で継続（スケジュール）` へ寄せている
- `定点計測` の user-facing KPI は `観測試行数` を唯一の分母にし、`自社露出率 / 自社引用率 / 外部先行率 / 前回比` を同じ試行数ベースで読む
- `answer_text` と根拠URLタイトルから stopword を考慮した軽量トピック抽出を行い、`競合・外部が取った論点`、`自社候補に出た論点`、`優先して足す論点` をチップで読める current decision に更新済み
- `C:\textresearch` の `semantic_network` / `topic_analysis` にある共起ネットワーク、BERTopic、高度トピック抽出は現行 `kotomegane` には未統合で、現状は軽量 topic signal のみ
- `定点計測` タブに `質問ごとの結果` ヒートマップを追加し、`判定 / 自社引用 / 競合引用 / 外部引用 / 自社候補` を質問行ごとに色で読める current decision に更新済み
- ヒートマップのセルを押すと `今回の結果` タブの `詳細を見る質問` が同じ質問へ切り替わり、定点計測から深掘りへそのまま移れるようにした
- 入力欄は `質問1件` を既定にし、2件目以降は `追加質問` として必要時だけ足す読み方へ更新した
- `意図マップ` を追加し、質問ごとに `比較 / 料金 / FAQ / 事例 / 地域 / 指名 / 手順` の意図を付与し、弱い意図クラスタを `詳細を見る > 詳細` で一覧化できる
- `不足ページナビ` を追加し、結果を `比較ページ / 料金ページ / FAQページ / 導入事例ページ / 地域LP / 指名FAQ・信頼ページ / 解説ページ` の不足へ変換し、`詳細を見る > 詳細` で確認できる
- `実行ガード` は `詳細を見る > 設定` の `定期リサーチ｜今すぐ実行（バッチ）` 側で、今日の実行件数、今回の投入件数、ガード挙動、cache retention を確認できる
- 自社監査系の backend は維持しつつ、現行 UI は市場観測固定の最小導線に寄せた
- 自社監査の切り替え導線は表面から外し、目的を「設定キーワードの LLM 露出測定」に絞って伝える形へ更新した
- `優先アクション` は bare な施策文ではなく、どの質問に対する施策かが分かる質問名つき表示へ更新済み
- 結果一覧に `意図` と `不足ページ` を追加し、質問単位でも制作タスクへ寄せて読めるようにした
- 文字サイズを維持し、dense table をやめて視認性を上げた
- 「起動状態」「まずやること」などの説明カードを外し、画面の並び自体で価値と読み順が伝わる構成にした
- KPI、入力欄、結果一覧、引用 URL の主要見出しと補助文を日本語話者向けに再整理した
- 接続AIは `ChatGPT / Gemini / Claude` の provider 名だけを表示し、切り替えは `設定` 側で行う
- 上部ナビは raw URL を見せず、`assets/kotomegane-logo.svg` のフルロゴを薄いクリームの台座に載せて表示する
- ユーザー向け UI では小型モデル名や tier 名は表示しない
- 価値訴求を「自社URLが出るか / ブランド名が出るか / どの見え方が不足しているかが分かる」に再構成した
- 入力欄は「このキーワード・質問で自社が出るか / どこが出るか」を測る用途が伝わる表現に変更した
- 入力欄は `質問 / 自社URL / ブランド名` を中心にし、`監査モード` と `確認回数` の表示は外した
- 直近結果カードは、英語の原文要約をそのまま前面に出さず、平易な日本語の判定文を主表示にした
- 直近結果カードは、判定基準を「AIの回答本文か引用URLに自社URLが出たか」と明示し、質問と判定を主表示に寄せつつ条件やメモは結果詳細側へ下げた
- 直近結果カードは、「今回の質問の結論」「今回の競合比較」「不足している見え方」の3分割に再整理し、競合入力の意味が画面上で分かる形に更新した
- 直近結果カードは、意図ラベルと不足している情報タイプを残しつつ、監査モード表示は前面から外してミニマムに寄せた
- 根拠URLセクションは `詳細を見る > 詳細` で確認できるようにし、自社 / 競合 / 外部サイトの内訳を短く表示する形へ更新した
- 推移グラフは `詳細を見る > 詳細` 内で `全体の推移` と `質問別の推移` を確認できる
- 推移グラフは `詳細を見る > 詳細` 内で `Intent Cluster Trend` と `Page Gap Trend` も確認できる
- ブランドのオレンジは主CTAとブランド強調に寄せ、状態表示は 自社=緑系 / 競合=琥珀系 / 外部=赤茶系 / 補助=ブラウン系 へ分離する方向に整理済み
- 小さな補助文、補助カード、主役カードの階層差を強め、主画面の視線誘導を安定させる方向に調整済み
- ヒーローは説明カードを外して圧縮し、起動直後の占有高さを抑えた
- 接続AI表示、まとめて確認、細かいコスト説明、根拠URL、結果一覧、原文メモ、条件情報は主画面から一段下げて `詳細を見る` 導線へ寄せた
- 棒グラフ見出しを、表示内容に合わせて「どの質問で見つかりやすいか」に修正した
- 棒グラフ見出しはさらに「どの質問が勝ち筋か」へ調整し、スコアは evidence として扱う位置づけに寄せた
- 結果一覧の列名を「現状判定」「競合との位置」「自社URL」「ブランド名」「参考スコア」に寄せ、判断寄りに並び替えた
- 結果一覧と実行履歴に `実行方式` を追加し、通常実行と Batch import の混同を避ける形に更新した
- 一覧には返答全文を出さず、`結果詳細カード` で `answer_text` と `citations` を確認する構成にした
- `結果詳細カード` は `返答分析 / 根拠URL / 条件確認` を中心にし、改善施策の実制作は `コトミガキ` 側へ役割を分ける current decision に更新した
- `質問セット` を追加し、保存済み設定を手動実行 / 定期リサーチ（今すぐ） / 定期リサーチ（自動）で再利用できるようにした
- `定期リサーチ（自動）` を追加し、曜日 + 時刻 + 週あたり回数で batch 実行を投入できるようにした
- scheduled batch はバックグラウンドで status retrieve と result import まで自動で行う
- `run_session` を snapshot 単位へ拡張し、`question_set_id` / `schedule_id` / `scheduled_for` / `config_json` を保存する
- `keyword_result` に `answer_text` と `citations_json` を追加し、生返答保持を行う
- `keyword_result` に `mentioned_brands_json` / `citation_domains_json` / `owned_mention_hit` / `competitor_mention_hit` / `answer_type_label` を追加し、既存 row も backfill する
- raw answer 構造化では、brand alias 展開、boundary-aware match、citation domain 正規化、answer type の rule-based scoring を使い、過剰検出と揺れを減らす方向へ調整した
- schedule 管理UIに `フォーム読込 / 複製 / 削除 / diff` を追加し、軽い AB 比較に寄せた
- `クラスタ下書き作成` を追加し、`意図 / 不足ページ / 質問セット` 単位で手動下書きを生成して `cluster_brief` に保存し、UI から再表示できる
- `実行結果比較` を追加し、定期実行 / 質問セット系列から 2 run を選んで `visibility rate / avg visibility / intent distribution / page gap distribution / owned mention / competitor mention / citation domain` を軽く比較できる
- 主画面では `stage header` のみを短く残し、`入力する / 結果を見る / 詳細` を最小限で示す
- 主結果の最上段は `自社が出たか / 外部名・外部サイト / 次に見直す質問` の 3 カードに絞った
- `質問セット / 定期リサーチ / 実行履歴 / 出力ファイル / 根拠URL / 対象AI切り替え` は詳細側へ下げ、現在の detail expansion は `今回の結果 / 定点計測 / 定期リサーチ / 設定` の 4 タブで整理している
- 上部ナビは `TECHIE HUB` とサービスリンクを2段構えにせず1ブロック内で整理し、小さい幅でも高さを使いすぎない形へ調整した
- 上部ナビの `TECHIE HUB` 文字は共通ロゴへ置き換え、将来 3 サービスで H1 を統一しやすい構成へ寄せた
- ヒーローと入力欄は「キーワード1件 / 自社URL / ブランド名から始める」ことがすぐ分かる文言へ寄せ、反復回数は UI に出さず、定点計測は 20 回・単発確認は 10 回の既定にした
- `質問ごとの判断一覧` は主画面から外し、`詳細を見る > 詳細` タブで確認する形へ下げた
- `詳細設定` は `競合語` のみを変更できる形へ絞った
- `全体の傾向` は `詳細を見る > 詳細` 側の先頭へ下げ、条件やメモも結果詳細側へ集約した
- 主結果3カードは狭い幅で縦積みになり、モバイルでも見出しが極端に縦崩れしにくい形へ調整した
- schedule 初回保存時に `existing_schedule=None` で落ちる bug を修正した
- timezone DB がない Windows 環境でも `Asia/Tokyo` など主要 timezone で schedule 保存と次回実行計算が止まらないよう fallback を追加した
- export は `exports/raw_results.csv`, `exports/weekly_summary.csv`, `exports/raw_results.json` を上書き生成する
- CSV export は spreadsheet formula injection を避けるため、`=`, `+`, `-`, `@`, タブ / 改行始まりの user / LLM / web 由来文字列を安全化してから書き出す
- export は raw answer の構造化項目を含み、金額列は user-facing 出力から外した
- 詳細設定の `reasoning_effort` に `none` を追加した。既定値は `low` のまま維持
- `prompt_cache_retention=24h` は対応モデルだけに適用し、`gpt-5.4-nano` では `in_memory` へ fail-safe 補正する
- prompt caching は 24時間保持を優先要求し、使えない条件だけ `in_memory` へ fail-safe 補正する
- `llmo_client.py` の `answer_snapshot` と `recommended_actions` は平易な日本語出力に更新した
- `llmo_client.py` の `answer_snapshot` は verdict で始まる形式に寄せ、`recommended_actions` は経営/マーケ会議でそのまま読める平易な日本語へ寄せた
- 通常の `分析を実行` は同期 + prompt caching 前提のまま維持し、`Batch投入` / `Batch状態確認` / `Batch結果取り込み` は Batch 折りたたみ内の別導線へ退避した
- Batch モードは `/v1/responses` 向け JSONL を OpenAI Batch API に投入し、結果取り込み後は既存の `save_keyword_result(...)` 経路へ流す形にした
- Batch job の状態、OpenAI batch id、input/output/error file id、request count、import count は local DB で追跡できる
- Batch の error line も既存結果行として保存し、失敗が結果一覧側で見える構成にした
- `query_plan` を追加し、`user_query_raw / user_query_short / query_was_shortened / shortening_note / expanded_queries_json / prompt_taxonomy_json / expansion_mode / expansion_signature / scheduler_mode / scheduled_dispatch_at / provider_batch_mode / provider_batch_id / provider_cache_policy` を保存するよう更新した
- provider registry に `supports_batch / supports_prompt_cache / supports_query_planner_reuse / preferred_batch_mode / cache_policy_mode / default_model / default_total_question_budget / batch_timeout_hours / partial_display_policy` を追加した
- `plan_catalog / billing_rules / run_policy` を module 化し、総質問数上限、手動と batch の内部課金単位、partial display 方針の owner を分離した
- `OpenAI 30 / Gemini 30 / Claude 15` の総質問数上限は provider registry 直参照ではなく `plan_catalog` から取得するよう更新した
- `save_keyword_result` の INSERT placeholder mismatch を修正し、Phase 7 の temp DB smoke で `question_set / schedule / run / batch metadata / export` を通した
- OpenAI live manual / batch submit / batch refresh / batch import を最小構成で確認し、live manual の JSON truncation を避けるため `max_output_tokens` の既定値を `1200` へ更新した
- query planner は provider ごとの `max_expansion_queries` と run 全体の `総質問数上限` を見て拡張質問数を制御する
- manual / batch / scheduled batch は同じ execution plan を共有し、`query_then_repeat` の送信順序を共通で使う
- query plan 再利用は `planner_signature` が一致する場合だけ許可する
- query plan 準備ロジックを `run_planning.py` に寄せ、app と scheduler の重複をなくした
- batch import と batch error row は `executed_query` を主 query として扱い、`analysis_context` に `user_query_raw` と `executed_query` の両方を保持する
- `keyword_result` と `batch_job_item` に `query_plan_id / executed_query / executed_query_index` を追加し、UI 主表示の元質問と内部実行質問を分離して追えるようにした
- 同じ元質問は最新の saved query plan を優先再利用し、毎回 expansion を作り直さないよう更新した
- 主結果カードと結果詳細に `内部で短く整えて計測` / `関連する派生質問も含めて確認` の通知、内部質問一覧、前回比サマリを追加した
- 前回比サマリは、同じ raw question set かつ同じ `expansion_signature` の直近 2 run に限って `自社露出率 / 平均 visibility スコア / 外部サイト優勢率` を比較するよう更新した
- `keyword_result` に `raw_llm_score / deterministic_score / owned_citation_count / owned_citation_share / external_only_result` を追加し、保存時と backfill 時に deterministic 側へ再計算するよう更新した
- `visibility_score` 列は user-facing 主表示用の deterministic score として扱い、LLM の元スコアは detail / export で参照する形へ更新した
- `build_run_outcome_snapshot`、query rollup、trend series、weekly summary、raw export は deterministic score を主軸に集計し、`score_stddev` と `variance_label` を持つ
- `query_plan` の詳細項目は `raw_results.csv` / `raw_results.json` に露出し、detail UI では内部質問列挙を主表示にしない current decision に更新した。`weekly_summary.csv` には `median / min / max / stddev / variance_label` を追加した
- `運用` タブの主要セクションは expansion 化し、平置きカードを減らして `入力 -> 結果 -> 詳細` の 3 段導線を維持した
- `prompt_taxonomy_json` が空の既存 row でも、`executed_query / keyword_raw` を使う runtime fallback で `prompt family` を推定し、detail / export の family 表示が空になりにくいよう更新した
- `質問の系統ごとの見え方` は `prompt family` 主体で `外部引用優勢 / 自社は出るが未引用 / 判定保留` を読めるよう更新し、`prompt label` は補助情報へ下げた
- `判定が不明なURL` は `保存条件の違いなどで未引用と断定しない方が安全なURL` と説明し、user-facing では `判定保留` として扱う方針へ揃えた
- main の `優先アクション` は card 数を増やさず、`質問の系統ベースの優先アクション` という family-first の文言へ更新した
- 入力カードに `最初の進め方` を追加し、初回ユーザーが `質問1件 -> 分析を実行 -> 主結果3カード -> 必要なら詳細` の順を画面内だけで追えるよう更新した
- detail の `この結果の読み方` で、判定スコアは一般検索順位ではないこと、`引用 / 未引用 / 判定保留` の意味を説明するよう更新した
- export は `raw_results.csv / weekly_summary.csv / raw_results.json` に加えて `report_summary.md` を生成し、画面内で共有前の報告用まとめをプレビューできるよう更新した
- stage header は短い補助文つきに整理し、入力カードの status 文も `分析を実行` 前提の短い案内へ更新した
- 必須入力不足の notify は `context` 句を外して短文化した
- 定期リサーチ（自動）UI に `この時刻から処理を開始します。結果の反映には最大24時間かかる場合があります。` を追加し、future schedule 前提ではないことを明示した
- provider ごとの env var 名と adapter 入口を catalog に集約済み
- `.env` が空でも process / user / machine 環境変数で起動できることを UI / script / docs で明示
- `run.ps1` は API キーの参照元を起動時に表示
- `run.ps1` は kill-on-close job wrapper で host shell 終了時の listener 残留を抑止
- `run.ps1` は runtime launcher と `.venv` の base interpreter も起動時に表示
- runtime は `.venv` 固定で、`setup.ps1` だけが `.venv` 作成のためにローカル Python を使う
- `allowed_domains` 入力欄は `soft preference` 表示に変更済み
- `allowed_domains` が hard filter ではないことは詳細設定内に限定して明示した
- 内部コスト計算と block 判定は残しつつ、金額表示は UI から外した
- 実データ 4件を SQLite に保存済み
- `run.ps1` で `http://127.0.0.1:8083/` 応答確認済み
- `http://127.0.0.1:8083/healthz` は lightweight runtime health として応答確認済み。`techie-hub/start.bat` と HUB カードの起動判定はこの endpoint を使う
- `stop.ps1` で 8083 listener の停止確認ができる状態に整理済み
- headless screenshot で UI 表示階層と日本語導線を確認済み
- headless screenshot で desktop / mobile の表示崩れがないことを確認済み
- `techie-hub/start.bat` の `kotomegane` 起動相当コマンドで 8083 listener 起動確認済み
- `gpt-5.4-nano` + Responses API + `web_search` の最小実動確認済み
- `python -m py_compile` で `app.py`, `analysis_lib.py`, `config.py`, `llmo_client.py`, `storage.py` の構文確認済み
- `.venv\Scripts\python.exe -c "import app"` で import smoke 確認済み
- `.venv\Scripts\python.exe app.py` の短時間起動と `http://127.0.0.1:8083/` の HTTP 200 応答を確認済み
- `Storage()` の migration/backfill 後に `mentioned_brands_json` / `citation_domains_json` / `answer_type_label` が埋まることを確認済み
- `write_export_files(...)` 後の `raw_results.json` に raw answer 構造化項目が含まれることを確認済み
- temp DB で `Cluster Brief Generator` の候補生成 / draft 生成 / `cluster_brief` 保存 / 再取得を確認済み
- temp DB で `Outcome Compare` の 2 run 比較スナップショット生成を確認済み
- temp DB で `query_plan` 保存、expanded query rollup、前回比サマリ計算を確認済み
- temp config で provider registry の既定モデル / 総質問数上限 / shared execution plan / Batch request 件数整合を確認済み
- temp smoke で `planner_signature` 差分検出と batch import の `executed_query` / `user_query_raw` 保持を確認済み
- temp smoke で deterministic score 算出、owned citation count/share、variance metrics、`Storage().list_recent_results()` の新列取得を確認済み
- `Phase 5` 相当の UI 整理後も `py_compile`、`import app`、HTTP 200 を確認済み
- 実ブラウザ headless で `質問セット保存 -> schedule 保存 -> 複製 -> diff 表示 -> detail raw answer / brief -> export -> cluster brief 導線` を確認し、`logs/browser_validation.png` を取得済み
- 実ブラウザ相当の短時間起動確認で `入力する / 結果を見る / 詳細を使う` の 3 段導線と主要ラベルの応答を確認済み
- 2026-03-30 の live check では `AI visibility platform for SaaS` を実行し、`visibility_score=28`, `cost_usd=0.012652`, `cost_jpy=2.02` を保存確認済み
- 2026-03-31 の live smoke では OpenAI Batch API に 1件投入し、submit / status retrieve / result import / 既存一覧相当への保存まで別DBで確認済み
- 2026-04-04 に `logs/screenshot_desktop_2026-04-04.png` と `logs/screenshot_mobile_2026-04-04.png` を再取得し、最新 phase 後の desktop / mobile 表示を確認済み
- 2026-04-04 に temp DB live validation で長文質問 1 件を `query_was_shortened=true`、内部質問 5 件、`query_then_repeat` で実行し、保持要素と派生質問の自然さを確認済み
- 2026-04-04 に `llmo_client.py` へ truncated JSON recovery を追加し、`citation_urls` 末尾切れがあっても `fallback_count=0` で保存できることを live rerun で確認済み
- 2026-04-04 に temp DB で OpenAI live manual verification を追加実行し、`fallback_used=false`、短文化後 1 query 実行、citation 保存まで確認済み
- 2026-04-04 に temp DB で OpenAI live batch verification を追加実行し、`completed`、`request_counts_completed=1/1`、`imported_result_count=1`、citation 保存まで確認済み
- 2026-04-04 に `weekly_summary.csv` へ `median_visibility_score / min_visibility_score / max_visibility_score / score_stddev / variance_label` を追加し、ローカル smoke で列出力を確認済み
- 2026-04-04 に `logs/gemini_live_manual_verification_2026-04-04.json` を出力し、Gemini manual/live で citation 付き応答が返ることを確認済み
- 2026-04-04 に Gemini / Claude provider batch adapter を追加し、`py_compile`、`import app`、Gemini / Claude の local import smoke を確認済み
- 2026-04-04 に `logs/gemini_live_batch_verification_2026-04-04.json` を出力し、Gemini live batch を試行した。provider quota 429 により完走確認は未了
- 2026-04-04 に Claude manual/live adapter を追加し、`py_compile` と `import app` は通過済み。Anthropic key 未設定のため live smoke は未実施
- 2026-04-04 に `app.py` の UI責務を `ui/styles.py`, `ui/charts.py`, `ui/dashboard_views.py`, `ui/detail_views.py`, `ui/admin_views.py` へ分離し、`runtime/common.py` に共通 helper を寄せた。`app.py` は state / wiring / event handler owner に寄せて `py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-04 に `analysis_lib.py` を facade 化し、`analysis_core/metrics.py`, `analysis_core/schedule.py`, `analysis_core/structures.py`, `analysis_core/briefs.py`, `analysis_core/trends.py` へ責務を分離した。既存の `from analysis_lib import ...` は維持し、`py_compile` と `import analysis_lib, app` を確認した
- 2026-04-04 に `llmo_client.py` を facade 化し、`llmo_core/prompts.py`, `llmo_core/models.py`, `llmo_core/openai_client.py`, `llmo_core/gemini_client.py`, `llmo_core/claude_client.py`, `llmo_core/factory.py` へ provider 実装と prompt owner を分離した。request 数と prompt 構成は維持し、`import app, scheduler_runtime` を確認した
- 2026-04-04 に `analysis_core/common.py` を facade 化し、`analysis_core/common_constants.py`, `analysis_core/text_utils.py`, `analysis_core/domain_utils.py`, `analysis_core/common_io.py`, `analysis_core/scoring.py` へ横分割した。underscore helper の direct import 互換も維持し、HTTP 200 を再確認した
- 2026-04-04 に `analysis_core/scoring.py` を facade 化し、`analysis_core/classification.py` と `analysis_core/deterministic_scoring.py` へ責務を分離した。既存の `from analysis_lib import ...` と `from analysis_core.common import ...` は維持し、`py_compile`、`import analysis_lib, app`、HTTP 200 を再確認した
- 2026-04-04 に provider ごとの cache policy を一次情報ベースで整理し、OpenAI は explicit prompt cache、Gemini は implicit default + explicit 1時間、Claude は automatic 5分 + Batch best-effort として `config.py` / `app.py` / `ui/` / `runtime/common.py` / `analysis_context` に反映した。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-04 に `prompt_catalog.py` を追加し、fallback expansion と query plan 保存を `managed prompt taxonomy` へ寄せた。`prompt_taxonomy_json` を `query_plan` に保存し、detail の `内部で使った質問` と raw export で `prompt family / label / purpose` を確認できるようにした。temp DB smoke、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-04 に `analysis_core/source_evidence.py` を追加し、`citations_json / output_json.citation_urls / source_url` を使う URL 状態 helper、detail の quoted / searched-only / unknown 表示、prompt taxonomy ごとの source 集計、source 根拠ベース priority actions を追加した。`py_compile`、`import app, analysis_lib`、HTTP 200、temp DB smoke を再確認した
- 2026-04-12 に `ui/dashboard_views.py` から主結果文言・結果タブ集計を `ui/result_story_builders.py`、根拠URL整形を `ui/evidence_presenters.py` へ分離した。`dashboard_views.py` は描画 owner と更新処理へ寄せ、`detail_views.py` と `charts.py` も shared helper を直接参照する形へ揃えた。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に `ui/dashboard_views.py` から主結果 3 カード描画と `主な参照元サイト` セクション描画を `ui/result_cards.py` へ分離した。`dashboard_views.py` は orchestration owner に寄せ、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に `app.py` から export 用の `build_report_summary_markdown(...)` を `report_summary_builders.py` へ分離し、`dashboard_views.py` の `refresh_dashboard(...)` は summary / decision / table / tracking widget 更新ごとの内部 helper に整理した。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に `app.py` から onboarding / runtime microcopy / provider 表示名まわりを `ui/runtime_copy_builders.py` へ分離した。`app.py` は wiring / state owner に寄せたまま、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に `app.py` から provider UI policy と runtime panel 更新を `ui/provider_runtime_controls.py` へ分離した。可視 provider 判定、provider config 正規化、provider chip 状態更新、runtime panel 更新を app 外へ寄せ、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に `app.py` から入力正規化と実行前チェックを `ui/input_config_builders.py` へ分離した。`build_manual_runtime_config(...)`、`build_config_from_inputs(...)`、`notify_missing_required_fields(...)` を app 外へ寄せ、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に `app.py` から export archive / file 出力を `export_file_writers.py` へ分離し、provider 選択時の config 更新も `ui/provider_runtime_controls.py` へ揃えた。`app.py` は export トリガーと state / wiring owner に寄せたまま、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に `app.py` から dashboard / cluster brief / outcome compare / export preview の再同期手順を `ui/page_refreshers.py` へ分離した。`app.py` はいつ refresh するかの owner、`ui/page_refreshers.py` はどう refresh するかの owner とし、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に `ui/page_refreshers.py` へ question set / schedule admin view の再同期も追加し、`app.py` の保存系 handler から `refresh_question_set_views(...)` / `refresh_schedule_views(...)` の直呼びを減らした。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に `ui/page_refreshers.py` へ batch job table / status / summary の再同期と status panel 更新も追加し、`app.py` の batch handler から `refresh_batch_job_views(...)` と label 更新の重複を削減した。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-12 に `ui/dashboard_views.py` から active scope filter、tracking scope filter、前回比判定、結果テーブル行、dashboard refresh 用 read-model 準備を `ui/dashboard_view_models.py` へ分離した。`dashboard_views.py` は描画更新 owner を維持し、既存の `dashboard_views.filter_rows_for_active_scope(...)` などの public 呼び出し境界は import 経由で維持した。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-13 に `ui/dashboard_views.py` から summary / decision / tracking widget の UI 更新反映を `ui/dashboard_refreshers.py` へ分離した。`dashboard_views.py` は refresh orchestration owner を維持し、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-13 に `app.py` の cluster brief 生成 / 読み込み後の select 再同期と payload 表示を `ui/page_refreshers.py` へ寄せた。`app.py` は generate/load の event owner を維持し、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-13 に `app.py` の cluster brief 生成から selected token 解決、candidate 抽出、cluster rows 組み立てを `ui/cluster_brief_builders.py` へ分離した。`app.py` は generate の event owner を維持し、`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-13 に `ui/cluster_brief_builders.py` へ cluster brief save payload の組み立ても追加し、`app.py` の generate handler から JSON 化と保存引数整形の重複を減らした。`py_compile`、`import app`、HTTP 200 を再確認した
- 2026-04-13 に `run_policy.resolve_run_policy` の import 抜けで `分析を実行` が開始前に落ちる不具合を修正し、`app.py` の手動実行 handler 全体を UI へ失敗通知を返せる形へ補強した。`py_compile`、`import app`、8083 の HTTP 200、temp DB を使った stub manual run 完走まで再確認した
- 2026-04-13 に `今回の結果` は当セッションの新規実行後だけ出す current decision へ更新し、入力変更後は待機状態に戻すよう `app.py` / `ui/dashboard_views.py` / `ui/detail_views.py` / `ui/result_cards.py` / `ui/dashboard_refreshers.py` を更新した。temp DB の保存済み履歴を事前投入した stub app で、起動直後は旧結果を current-run 面へ出さず、クリック後にだけ `分析完了` へ進むことを確認した
- 2026-04-14 に `今回の結果` の復元条件を補強し、同じ入力条件の run が直近 30 分以内に完了していれば、ページ再読込やソケット再接続後でも current 面へ自動復元する current decision へ更新した。質問 / provider / 自社URL / ブランド / 競合語が変わった場合は従来どおり待機状態へ戻す
- 2026-04-13 に `ui/styles.py` の header / drawer を `techie-hub` と同じ `#2F241D` へ揃え、主CTA も `#D96B1F -> #B95416` に統一した。3製品横断の SaaS shell としての連続感を優先した
- 2026-04-13 に `config/llmo_poc_settings.json` の `ui_port` を `8083` へ戻し、`run.ps1` の再起動で `http://127.0.0.1:8083/` 応答を確認した
- 2026-04-13 に `最新結果` と `今回の結果` の混在を解消し、`app.py` の実行カードへ長時間待ち時の再実行目安を追加した。stub UI で `分析中です -> 分析完了 -> 入力を更新しました` と見出し統一を再確認した
- 2026-04-13 に dedicated temporary live verify server (`8098`) で real provider の最小 run を追加実行し、`分析完了`、`失敗 0件`、`今回の結果` カード群の描画まで確認した。既定の `8083` runtime config は変更せず、live verify 用の `tmp/live_verify_server.py` で実施した
- 2026-04-13 に `app.py` へ manual run の `分析を停止` を追加し、stub UI (`8099`) で停止導線を確認した。さらに live verify (`8098`) で 2 回連続実行し、質問変更後は前回 current 結果を隠し、2 回目完了後も 1 回目の current 表示が残らないことを確認した
- 2026-04-13 late に periodic refresh を `ui.timer(...)` から client 背景 task へ置き換え、client 切断や page delete と timer element の race で出ていた `The parent slot of the element has been deleted.` の再発条件を減らした。`.venv\Scripts\python.exe -m py_compile app.py` と `import app` を再確認した
- 2026-04-13 late に `ui/styles.py` / `app.py` / `ui/result_cards.py` を更新し、`コトメガネ` の左 drawer を全面ダークから明るいカードトーンへ戻した。`コトメイク` / `コトミガキ` と同じく、濃いブラウンは上部ナビ中心、本文面はクリーム背景主体の比率へ寄せた
- 同日の UI 更新で hero 直下へ `直近の観測サマリー` を追加したが、2026-04-14 の UI 削減実装で first view から外し、現在は入力先行 + 3 カード要約を優先する current judgment に戻している
- 同日の UI 更新で `質問と返答から見えた論点` カードを追加し、既存の lightweight topic extraction に加えて、質問文・回答・引用URLタイトルから出した上位共起ペアを `A ↔ B` 形式で表示するようにした。`C:\textresearch` の full semantic network 直移植ではないが、URL列挙だけで終わらない最小の観測導線はこの時点で入った
- 2026-04-13 late に 8083 を再起動し、Playwright headless で起動画面を確認した。light drawer、hero 下の観測サマリー 4 カード、論点チップと共起ペア表示を確認し、スクリーンショットを `logs/kotomegane_ui_check.png` に保存した

## Known Gaps

- 実ブラウザエンジンでの主要導線確認は完了したが、長時間の人手回遊と運用負荷観察は未実施
- scheduled batch は in-process runtime 前提で、Windows service / cron などの外部常駐化は未着手
- Batch は create / retrieve / import と scheduled auto-import まで実装済みだが、cancel 導線や高度な監視UIまでは広げていない
- `意図マップ` と `不足ページナビ`、raw answer 構造化は rule-based のため、実データに合わせた語彙追加調整は今後も必要
- `Page Brief` は row / cluster ともに rule-based draft の初期版で、LLM ベース再構成や bulk 生成は未着手
- `実行結果比較` は 2 run 比較の初期版で、settings diff と統合された run history 比較や series export は未着手
- `cluster_brief` は保存再表示までで、run snapshot や report export との恒久紐付けは未着手
- ブラウザ終了時に NiceGUI の timer が `parent slot deleted` warning を出すことがあり、長時間運用向けの timer 後始末は今後の改善候補
- `Gemini` は manual/live と provider batch adapter まで実装済み。live batch 完走確認は provider quota 解消後に再実施が必要
- provider ごとの利用可否は、現段階では `KOTOMEGANE_ENABLED_PROVIDERS` / `enabled_provider_keys` による app 単位の allowlist hook まで。auth / tenant / user 単位の制御は未着手
- `Claude` は manual/live と provider batch adapter まで実装済み。Anthropic key 未設定のため live manual / batch smoke は未実施
- `Claude` の `1時間` cache と request payload への `cache_control` 接続は未着手
- facade 化した `analysis_lib.py` / `llmo_client.py` / `analysis_core/common.py` / `analysis_core/scoring.py` は互換維持のため re-export owner として残している

## Active Runtime Assumptions

- model: `gpt-5.4-nano`
- API: `Responses API`
- tool: `web_search`
- prompt cache retention: `24h` を優先要求し、未対応条件では `in_memory` に補正
- prompt cache 24h support: `gpt-5.4-nano` では未対応。24h 指定時は `in_memory` で実行
- analysis mode surface: `market` fixed
- owned_only backend: remains available internally
- reasoning default: `low`
- reasoning options in UI: `none`, `low`, `medium`
- run budget guardrail default: internal only
- setup: ローカル Python 3.11 で `.venv` を作成
- runtime: `run.ps1` / `techie-hub` ともに `.venv` を入口に使う
- Windows process view: listener は `.venv` の base interpreter に見える場合があるが、runtime context は `.venv`
- pricing notes: `docs/OPENAI_RUNTIME_NOTES.md`

## Immediate Next Actions

1. Anthropic key が入った環境で Claude live manual / batch smoke を実行する
2. Gemini live batch を quota 解消後に再実行して submit / refresh / import 完走を確認する
3. Claude の `1時間` cache を request payload に接続するか判断する
4. prompt family ごとの重みづけと executive view 用の集約指標を設計する

## Next Restart Pointer

- 次回再開の初回 prompt: `docs/session_notes/TOMORROW_FIRST_PROMPT_2026-04-05.md`
