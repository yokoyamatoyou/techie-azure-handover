# Expansion + Delta Next Window Prompt 2026-04-03

更新日: 2026-04-03  
用途: 次ウインドウで `拡張検索` と `前回比サマリ` を実装するための専用開始プロンプト

## この文書で固定すること

- 長文クエリの要約条件
- 拡張検索の生成方針
- 前回比サマリの比較条件
- 保存すべき内部データ
- UI でどこまで見せるか

## 参照ルールファイル

- `C:\tetie\AGENTS.md`
- `C:\tetie\kotomegane\AGENTS.md`

## 今回の実施範囲

- `kotomegane` に `拡張検索` を追加する
- `kotomegane` に `前回比サマリ` を追加する
- 対象は `kotomegane` のみ
- `aio2-main` と `notecode` は触らない
- 上段デザインの大枠は維持し、最小差分で入れる

## 最初に読む

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\kotomegane\AGENTS.md`
3. `C:\tetie\kotomegane\docs\DOC_STATUS.md`
4. `C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md`
5. `C:\tetie\kotomegane\docs\TOMORROW_WORK_PLAN_2026-04-01.md`
6. `C:\tetie\kotomegane\docs\TOMORROW_FIRST_PROMPT_2026-04-03.md`
7. `C:\tetie\kotomegane\README.md`
8. `C:\tetie\kotomegane\Saas\LLMO対策SaaS 低コスト構築提案.md`
9. `C:\tetie\kotomegane\app.py`
10. `C:\tetie\kotomegane\analysis_lib.py`
11. `C:\tetie\kotomegane\storage.py`
12. `C:\tetie\kotomegane\config.py`
13. `C:\tetie\kotomegane\llmo_client.py`

## 実装ゴール

### 1. 拡張検索

- ユーザーが入れた質問から、内部用の派生質問を生成して計測する
- 企業が `どの質問のされ方なら自社が出るか` を見つけやすくする
- UI 上はユーザーが入れた元質問を主表示のまま維持する

### 2. 前回比サマリ

- 直近 run と前回 run を比較して、改善 / 悪化 / 横ばいを一読で分かるようにする
- 既存の履歴と上段 KPI をつなぐ

## 固定仕様

### A. 長文クエリ要約

- ユーザーの元質問が `日本語 50 文字超` の場合だけ、内部で短文化する
- UI の入力欄には元質問をそのまま残す
- 計測に使う内部 query は `要約版` を使ってよい
- 要約時に絶対に落としてはいけない要素:
  - ブランド名
  - 競合名
  - 地域
  - 価格 / 料金条件
  - 対象読者
  - 比較軸
- 要約で意味が変わるくらい情報が多い場合は、無理に短くしすぎない
- 要約の実装は `gpt-5.4-nano` を使ってよい
- 推論の深さは `reasoning_effort=medium` を使う
- 要約結果は DB に残す

### B. 拡張検索

- 拡張検索は `gpt-5.4-nano` で生成する
- 推論の深さは `reasoning_effort=medium`
- 将来 `Claude` や `Gemini` を実装しても、拡張検索を作る役は各 provider に分散しない
- 拡張検索の生成器は引き続き `gpt-5.4-nano` に固定する
- つまり `OpenAI / Claude / Gemini` に投げる質問セットは、共通の expansion layer が先に作る
- 生成本数は `元質問 1 件あたり最大 5 件`
- 構成は次:
  - 元質問または要約質問 1 件
  - 派生質問 最大 4 件
- 派生質問の基本軸:
  - `比較`
  - `料金`
  - `FAQ`
  - `事例`
- ただし、元質問に合わない軸を無理に作らない
- `比較 / 料金 / FAQ / 事例` が不自然な場合は、最も近い軸へ置き換えてよい
- 置き換え候補:
  - `評判・イメージ`
  - `導入不安`
  - `使い方 / how-to`
- つまり、`4軸固定` ではなく `最大4件の relevant expansion` として実装する
- 展開後クエリは重複除去する
- 正規化して同一に近いものは 1 件に潰す

### C. 実行方式

- PoC では `拡張 -> 各質問を個別に API 実行` の流れを使う
- 拡張後 5 件になったら、5 件を個別に送る
- 送信は並列でよい
- ただし prompt caching を崩さないよう、system prompt と prefix は固定する
- prompt caching は provider ごとの流儀に合わせて adapter 層で吸収する
- provider 共通の product policy は `静的 prefix を先頭に置く` `動的な user query は後段へ置く` `同一 expansion_signature では同一 prefix を保つ`
- 結果表示は `元質問 1 件` の塊としてまとめる

### D. provider 差分の扱い

- `OpenAI / Claude / Gemini` では batch API と prompt caching の仕様が一致しない前提で実装する
- そのため `expansion generation policy` と `provider execution policy` を分離する
- 前者は共通、後者は adapter ごとに持つ
- 最低限 provider ごとに吸収する項目:
  - batch 投入方法
  - batch 完了待ちの状態管理
  - prompt caching の有効化方法
  - cache hit の取得方法
  - TTL / retention の扱い
  - batch 制限と上限件数
- UI と保存スキーマは provider 非依存に保つ
- ただし実行ログには provider 固有の batch/cache 情報を残してよい

### E. 保存仕様

- `run ごとの expanded queries` とは、各 run で実際に内部送信した質問一覧を保存すること
- 保存する理由:
  - 後で `なぜこの結果になったか` を説明できる
  - 前回比を apples-to-apples で比べられる
  - 要約や expansion のドリフトを検知できる
- 最低限保存する項目:
  - `user_query_raw`
  - `user_query_short` 要約した場合のみ
  - `query_was_shortened`
  - `shortening_note` 何を残したかの短い説明
  - `expanded_queries_json`
  - `expansion_mode` raw / shortened / expanded
  - `expansion_signature` 比較用の安定キー
  - `scheduler_mode` immediate / scheduled
  - `scheduled_dispatch_at` API を投げ始める予定時刻
  - `provider_batch_mode` none / provider_batch / app_queue
  - `provider_batch_id` 使った場合のみ
  - `provider_cache_policy`

### F. 前回比サマリ

- 比較対象は `同一 question_set の直近 2 run`
- ただし `expansion_signature` が一致する場合だけ厳密比較とする
- signature が一致しない場合は、無理に前回比を出さない
- その場合は `比較条件が変わったため前回比なし` の扱いにする
- 指標は次の 3 つに固定:
  - `自社露出率`
  - `平均 visibility スコア`
  - `外部サイト優勢率`

### G. 同じ質問の再実行時

- ユーザーの元質問が変わっていなければ、前回の expansion を優先再利用する
- 毎回 expansion を作り直さない
- これで前回比の比較条件を安定させる
- ユーザーが元質問を編集した場合だけ、要約と expansion を再生成する

### H. バッチ実行と日時設定

- UI で設定する日時は `API に投げ始める時刻` を意味する
- バッチ結果はその時刻に即時完成する前提ではなく、provider によっては完了まで最大 24 時間かかることを明示する
- UI 文言は `この時刻から処理を開始します。結果の反映には最大24時間かかる場合があります` を基本にする
- provider の batch API に future schedule 機能がある前提では実装しない
- 予約実行は `アプリ側の scheduler / queue / worker` で実現する
- batch API の作成後は provider 側で処理が始まる前提で扱う
- そのため `未来時刻に provider batch を直接予約する` 設計にはしない

### I. Azure 以降と PoC ローカルの運用差

- Azure 以降:
  - UI で受けた予約を DB に保存
  - scheduler が指定時刻に job を dispatch
  - worker が provider API を叩き、完了確認を行う
  - Web アプリを開きっぱなしにする必要はない
- ローカル PoC:
  - アプリ内 scheduler を常駐させるか
  - OS のタスクスケジューラから定期実行する
  - どちらも無い構成なら、指定時刻に API を叩くにはプロセスが動いている必要がある
- したがって PoC では `予約時刻を過ぎた未実行 job を起動時に回収して実行する` 保険を入れる

### J. UI 方針

- 入力欄にはユーザーの元質問をそのまま表示する
- 主画面で内部 query を前面には出さない
- ただし結果側には次の短い通知を出してよい
  - `この質問は内部で短く整えて計測しました`
  - `この質問は関連する派生質問も含めて確認しました`
- 詳細側では説明可能な粒度で見せてよい
- 表示候補:
  - `内部で使った質問`
  - `要約あり / なし`
  - `前回と同じ拡張条件で比較`

## 実装順

1. 既存の run/session 保存構造を確認する
2. expansion 保存用の最小 DB 拡張を入れる
3. `gpt-5.4-nano` の短文化 helper を作る
4. `gpt-5.4-nano` の expansion helper を作る
5. 重複除去と signature 生成を作る
6. provider adapter ごとの batch/cache ポリシー差分を切り出す
7. scheduler 用の保存項目と dispatch 判定を追加する
8. main run の API 実行を `expanded queries` 単位へ拡張する
9. run 結果を元質問単位に集約する
10. 前回比サマリを追加する
11. UI に最小表示を足す
12. README と CURRENT_STATE を最小同期する

## Do Not

- `aio2-main` / `notecode` を触らない
- H1 や provider 表示を作り直さない
- consulted-only source を user-facing に出さない
- 毎回 expansion を作り直して前回比を不安定にしない
- 無理に 4 軸を埋めるため不自然な質問を作らない
- ユーザーの元質問を UI 上で書き換えない
- provider batch API に future schedule 機能がある前提で設計しない
- Web アプリが開いていれば予約実行できる、という前提に依存しない

## 最低限の検証

1. `.venv\\Scripts\\python.exe -m py_compile app.py analysis_lib.py config.py llmo_client.py storage.py`
2. `.venv\\Scripts\\python.exe -c "import app"`
3. 短文クエリで:
   - 要約が走らない
   - expansion が保存される
4. 51文字以上の長文クエリで:
   - 要約が走る
   - 必須要素が落ちていない
5. 同一 question_set を 2 回走らせて:
   - expansion_signature 一致時だけ前回比が出る
6. UI で:
   - 元質問表示が維持される
   - 結果側だけに `内部で整えて計測` の補足が出る
7. 予約実行ありで:
   - 指定時刻前は dispatch されない
   - 指定時刻以降に dispatch される
   - `開始時刻` と `完了待ち` の文言が分かれている

## 次ウインドウ用プロンプト

以下を次ウインドウへそのまま貼ってください。

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\kotomegane\AGENTS.md

今回の実施範囲:
- kotomegane に `拡張検索` と `前回比サマリ` を実装する
- 対象は kotomegane のみ
- 上段デザインの大枠は維持し、最小差分で入れる

必ず最初に読む:
- C:\tetie\AGENTS.md
- C:\tetie\kotomegane\AGENTS.md
- C:\tetie\kotomegane\docs\DOC_STATUS.md
- C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
- C:\tetie\kotomegane\docs\TOMORROW_WORK_PLAN_2026-04-01.md
- C:\tetie\kotomegane\docs\TOMORROW_FIRST_PROMPT_2026-04-03.md
- C:\tetie\kotomegane\docs\EXPANSION_DELTA_NEXT_WINDOW_PROMPT_2026-04-03.md
- C:\tetie\kotomegane\README.md
- C:\tetie\kotomegane\Saas\LLMO対策SaaS 低コスト構築提案.md
- C:\tetie\kotomegane\app.py
- C:\tetie\kotomegane\analysis_lib.py
- C:\tetie\kotomegane\storage.py
- C:\tetie\kotomegane\config.py
- C:\tetie\kotomegane\llmo_client.py

固定仕様:
- ユーザーの元質問が日本語50文字超なら内部で短文化する
- UI には元質問をそのまま残す
- 要約時に落としてはいけない要素は、ブランド名、競合名、地域、価格/料金条件、対象読者、比較軸
- 要約と expansion は gpt-5.4-nano を使い、reasoning_effort=medium
- 将来 Claude / Gemini を実装しても、拡張検索を作る役は gpt-5.4-nano に固定する
- 拡張検索は元質問1件あたり最大5件
- 構成は 元質問または要約質問1件 + 派生質問最大4件
- 基本軸は 比較 / 料金 / FAQ / 事例
- ただし不自然なら 評判・イメージ / 導入不安 / 使い方-how-to などへ置換してよい
- 4軸を無理に埋めず、relevant expansion を優先する
- 展開後クエリは重複除去する
- PoC では 拡張 -> 各質問を個別にAPI実行 の流れを使う
- 拡張後の質問は並列でよい
- prompt caching は provider ごとの流儀に adapter 層で合わせる
- provider 共通では 静的prefixを前に、動的queryを後ろに寄せる
- OpenAI / Claude / Gemini で batch API と prompt caching の仕様差がある前提で、expansion layer と provider execution layer を分離する
- run ごとに実際に使った expanded queries を保存する
- 保存項目は user_query_raw, user_query_short, query_was_shortened, shortening_note, expanded_queries_json, expansion_mode, expansion_signature, scheduler_mode, scheduled_dispatch_at, provider_batch_mode, provider_batch_id, provider_cache_policy
- 前回比サマリは同一 question_set の直近2 run を比較対象にする
- ただし expansion_signature が一致する場合だけ厳密比較とする
- signature が違うときは 比較条件が変わったため前回比なし とする
- 前回比指標は 自社露出率 / 平均 visibility スコア / 外部サイト優勢率
- ユーザーの元質問が変わっていなければ、前回の expansion を優先再利用する
- ユーザーが元質問を編集したときだけ再生成する
- user-facing の URL 表示は citation として実際に出た URL だけを扱う
- UI の日時設定は API に投げ始める時刻を意味する
- 結果反映には provider により最大24時間かかる場合があることを明示する
- 予約実行は provider batch API の未来予約ではなく、アプリ側 scheduler / queue / worker で実現する
- Azure 以降では scheduler + worker 前提、ローカル PoC では常駐プロセスまたは OS スケジューラ前提で実装する
- ローカル PoC では 予約時刻を過ぎた未実行jobを起動時に回収して実行する

UI 方針:
- 入力欄には元質問をそのまま表示
- 主画面では内部 query を前面に出さない
- 結果側には `内部で短く整えて計測しました` `関連する派生質問も含めて確認しました` のような短い補足だけ出してよい
- 日時設定まわりでは `この時刻から処理を開始します。結果の反映には最大24時間かかる場合があります` を出す
- 詳細側でのみ、内部で使った質問と比較条件を見せてよい

実装順:
1. 既存の run/session 保存構造を確認
2. expansion 保存用の最小 DB 拡張
3. 長文短文化 helper
4. expansion helper
5. 重複除去と signature 生成
6. provider adapter の batch/cache 差分切り出し
7. scheduler 用保存項目と dispatch 判定追加
8. main run を expanded queries 単位へ拡張
9. 元質問単位の集約
10. 前回比サマリ追加
11. UI 最小追加
12. README / CURRENT_STATE 同期

Do not:
- aio2-main / notecode を触らない
- H1 や provider 表示を作り直さない
- consulted-only source を user-facing に出さない
- 毎回 expansion を作り直して前回比を不安定にしない
- 4軸を無理に埋めない
- 元質問を UI 上で書き換えない
- provider batch API に future schedule がある前提で設計しない

最低限の検証:
1. .venv\\Scripts\\python.exe -m py_compile app.py analysis_lib.py config.py llmo_client.py storage.py
2. .venv\\Scripts\\python.exe -c "import app"
3. 短文クエリで要約が走らないこと
4. 51文字以上の長文クエリで要約が走ること
5. expansion が保存されること
6. 同一 question_set の直近2 run で signature 一致時だけ前回比が出ること
7. UI で元質問が維持されること
8. 予約実行ありで指定時刻以降に dispatch されること

完了時に報告すること:
- 保存スキーマをどう拡張したか
- 長文短文化ルールをどう実装したか
- expansion の軸をどう選んだか
- 前回比をどう判定したか
- 更新ファイル
- 検証内容
- AGENTS/WORKLOG更新の要否
```
