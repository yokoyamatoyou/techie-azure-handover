# Kotomegane Result UX Implementation Plan 2026-04-14

## Purpose

この文書は、`見え方観測` の結果画面を

- `試行数ベースで誤読なく理解できる`
- `どの質問で引用されやすいかが一目で分かる`
- `文字だけに依存せず傾向を視覚で読める`
- `分析中の進捗と詰まりを把握しやすい`

状態へ寄せるための実装 plan です。

今回の対象は `結果の意味が分からない` という UX 問題の解消であり、
スコア改善そのものではなく `理解しやすい観測体験` を先に整えることを目的にする。

## 2026-04-20 Nielsen Review Addendum

2026-04-20 時点の heuristic review では、現行 UI は

- Nielsen の 10 原則を大きく外してはいない
- ただし `Aesthetic and minimalist design`
- `Recognition rather than recall`
- `Visibility of hierarchy`

の観点でまだ改善余地がある、という判断に更新した。

認知負荷の current judgment は次とする。

- desktop: `中程度`
- mobile: `やや高い`

理由は、`左ナビ / hero / 入力 / 結果 3 カード / 下段展開` が一度に見え、
初見ユーザーが `今どこを見ればよいか` を毎回選び直す必要があるため。

今回の addendum は、上記の認知負荷を下げるための実装 task を固定する。

## Fixed Decision

- first view の母数は `distinct question 数` ではなく `観測した試行数` に統一する
- `元質問 + 拡張質問` に対する実際の回答試行を、そのまま観測対象として扱う
- 具体的な質問数や内部アルゴリズムの細部は first view に出しすぎない
- first view では `割合` と `質問傾向` を主役にし、件数は詳細側へ下げる
- `94%` のような単独数値だけを大きく見せる構成はやめる
- `自社引用 9件` のような URL 件数は、試行ベースの率と同じ面で並列主表示しない
- 右端カードの dark brown panel は採用しない
- 色は `C:\tetie\notecode` と `C:\tetie\aio2-main` に揃う suite palette を優先する
- 分析中は `今どこを処理しているか` が文で分かる progress copy を必須にする

## Product Interpretation

結果画面の役割は次の 3 問へ即答することに固定する。

1. AI はこの会社を見つけやすかったのか
2. どんな質問だと自社が引用されやすいのか
3. 次に何を足すと引用されやすさが伸びそうか

`何件引用されたか` や `どのURLが残ったか` は重要だが、
first view で最初に読む情報ではない。

## Problems To Solve

### 1. Denominator Mismatch

- `自社露出率 94%`
- `自社引用 9件`

が同じ card 群に並ぶと、同じ母数の数字だと誤読されやすい。

### 2. Copy Does Not Explain The Action

- `今回の見え方`
- `何を根拠にしたか`
- `次に強化するページ`

だけでは、どの質問傾向が勝ち筋なのかが読めない。

### 3. Too Much Text, Too Little Shape

現状は文章を読まないと理解できない。  
質問傾向や引用傾向を、色・位置・面積で先に理解できる UI へ寄せる必要がある。

### 4. Progress Feedback Is Weak

spinner は出ても、`止まっているのか / 進んでいるのか / 何を処理しているのか` が分かりにくい。

### 5. Too Many Simultaneous Attention Anchors

現状は `左ナビ`、`hero status`、`入力カード`、`first view 3 cards`、`詳細を見る` が
すべて強く見える時間帯がある。

そのため、

- どれが主役か
- どこから読めばよいか
- 何を後回しにしてよいか

が一読で決まりにくい。

### 6. Mobile Compression Is Still Weak

mobile では block 数が多く、

- status chip
- 説明文
- card 見出し
- 補助文

が縦に積み上がるため、`結論に到達するまでのスクロール量` がまだ大きい。

## UX Principle

### 1. One Screen, One Judgment

first view では `数字の説明` より `今回の判断` を先に読む。

### 2. Show Pattern Before Detail

先に `引用されやすい質問の型` を見せ、件数や URL は後で確認させる。

### 3. Use Shape As Well As Text

色、分布、強弱、まとまりで傾向を読ませる。  
文章は視覚化の結論だけに絞る。

### 4. Keep Internal Logic Partially Opaque

ユーザー価値として `質問の傾向` は出すが、
内部の質問数や展開ロジックをそのまま開示しない。

### 5. One Strong Anchor Per Fold

1 スクロール範囲内で `主役` は 1 つに絞る。  
同じ fold 内に、同格の見出し・同格の強い card を増やしすぎない。

### 6. Compress Before Explaining

理解のための説明を増やす前に、

- card 数
- 行数
- chip 数
- status 数

を削る。

## Target Information Architecture

first view の 3 cards は次に固定する。

### Card 1: 今回の結論

- main label: `自社が見つかる試行が多い` などの短文
- sub label: `回答試行ベースで判定`
- support line:
  - `自社露出率`
  - `自社引用率`
- raw 件数は出さない
- 補助文は `今回の観測では、比較より導入・指名系で強い` のように質問傾向へ寄せる

### Card 2: 引用されやすい質問

- 文章中心ではなく `質問タイプの可視化` を主役にする
- `比較検討`
- `導入手順`
- `料金確認`
- `地域指名`
- `事例確認`
などの intent family を並べ、強さを比較できるようにする

### Card 3: 次の改善

- `今すぐ直すもの`
- `次に足すと効きやすいもの`
- `効く理由`

の 3 つを短く読む構成にする

## Visual Components To Add

### 1. Question Type Heatmap

目的:
- `どの質問タイプで自社が引用されやすいか` を一目で見せる

仕様:
- 行は質問タイプ
- 列は `見つかる / 引用される / 外部先行`
- 色の強さで傾向を出す
- 数字は hover or detail only

理由:
- 文字量を減らしつつ、質問ごとの勝ち負けを最も早く理解できる

### 2. Citation Opportunity Bubble Strip

目的:
- `AI が拾いやすい質問の塊` を視覚で見せる

仕様:
- バブルサイズは `観測内での存在感`
- 色は `自社優位 / 並走 / 外部優位`
- ラベルは `比較`, `導入`, `料金`, `地域`, `事例` などの短語に限定する

理由:
- 「どんな質問で引用されるか」を、文章より速く把握できる

### 3. Page Opportunity Strip

目的:
- 次に足すページ候補を `緊急 / 維持 / 追加候補` の 3 状態で見せる

仕様:
- card 内に横並びの short strip
- 各 item は `料金`, `比較`, `FAQ`, `事例`, `導入手順` など
- state color を suite palette 内で統一

理由:
- 右端 card を文章だけで埋めず、判断対象を面で見せられる

### 4. Response Snapshot Carousel

目的:
- 実際の回答例を少数だけ見せ、定量指標への信頼感を補う

仕様:
- 1-3 件だけ
- `この質問ではこう答えた` を short quote で表示
- citation URL 全列挙はしない

理由:
- 抽象化しすぎると納得感が落ちるため、短い実例を添える

## Recommended First Release Scope

最初の実装は次の 3 つに絞る。

1. `Question Type Heatmap`
2. `Citation Opportunity Bubble Strip`
3. `Page Opportunity Strip`

`Response Snapshot Carousel` は phase 2 に回してよい。

## Nielsen-Driven Implementation Tasks

### Task Group A: First View Priority Tightening

目的:
- first view の読み順を `入力 -> 今回の結論 -> 主な参照元サイト -> 頻出論点` へ固定する

実装 task:

1. left nav の説明文量を半分にする
2. left nav では `入力 / 今回の結果 / 定点計測 / 設定` だけを主表示し、補助説明は hover か detail へ下げる
3. hero 内の status block は `対象AI / 最終更新` の 2 つを上限にする
4. hero の補助文は 1 文に固定し、価値説明の重複をなくす
5. first view 3 cards の直前にある説明文は 1 行までに制限する

完了条件:

- first view 上部で同格の見出しブロックが 3 つ以上並ばない
- 初見で `最初に押す場所` と `最初に読む場所` が別れない

対象 file:

- `app.py`
- `ui/styles.py`

### Task Group B: Card Density Reduction

目的:
- 3 cards は保ちつつ、各 card 内の読書量を減らす

実装 task:

1. card 内の説明文は原則 2 行以内に制限する
2. card 内の eyebrow は 2 個までに制限する
3. signal chip の最大表示数を card ごとに決める
4. `basis note` や補助説明は default 表示から外し、必要なら折りたたみへ逃がす
5. 中央 card の `よく使われるサイト / よく使われるページ` は 3 件まで固定する
6. 右 card の論点 chip は 4 + 4 + 4 のように増やさず、`主論点 / 要改善論点` の 2 群までに絞る

完了条件:

- 1 card を 5 秒以内で読み切れる
- card ごとの視線停止回数を減らせる構成になっている

対象 file:

- `ui/result_cards.py`
- `ui/result_story_builders.py`
- `ui/styles.py`

### Task Group C: Hierarchy And Contrast Strengthening

目的:
- `主役 / 補助 / 詳細` の階層差を視覚だけで分かるようにする

実装 task:

1. main headline と support copy の contrast 差を広げる
2. chip の色は意味を残しつつ、背景との差を優先して整理する
3. `section-card` と `panel-card` の視覚的な格差をもっと明確にする
4. expandable section は closed state をもっと静かにする
5. `今回の結果` 3 cards 以外は border / shadow / background の主張を一段弱める

完了条件:

- どこが主表示で、どこが補助表示かを説明なしで判別できる
- 開かれていない panel が主結果 card と競合しない

対象 file:

- `ui/styles.py`
- `app.py`

### Task Group D: Mobile-Specific Simplification

目的:
- mobile で `結論到達まで長い` 問題を下げる

実装 task:

1. mobile では hero status card を 1 列圧縮する
2. mobile では first view 3 cards の上下余白を縮める
3. mobile では card 内補助文を PC より 1 段少なくする
4. mobile では left nav に依存しない導線を保つ
5. mobile では `詳細を見る` 以降の panel 群を fold 下へさらに逃がす

完了条件:

- mobile で最初の結論 card までのスクロール量を現状より減らす
- mobile で 1 画面に入る主要判断要素の数を増やす

対象 file:

- `ui/styles.py`
- `app.py`
- `ui/result_cards.py`

### Task Group E: Recognition Over Recall Cleanup

目的:
- `この画面は何を見る場所か` を記憶ではなく表示で理解できるようにする

実装 task:

1. `今回の結果の整理` と `保存済みの累積傾向` の視覚差をさらに広げる
2. `今回の結果` と `定点計測` の用語差を tab header と説明文の両方で固定する
3. `主な参照元サイト` は `詳細で実URLを見る` ことを短く明示する
4. `頻出論点` は `回答や引用ページで繰り返し出る論点` として固定し、質問タイプ表示と混同させない
5. `質問タイプ別の深掘り` は first view から完全に detail owner へ寄せる

完了条件:

- `今回の結果` と `保存済み集計` の粒度差が見出しだけで分かる
- `参照元サイト` と `実URL` の役割差が画面語彙として固定される

対象 file:

- `app.py`
- `ui/result_cards.py`
- `ui/detail_views.py`

## Copy Rewrite Rules

- `今回の見え方` -> `今回の結論`
- `何を根拠にしたか` -> `引用されやすい質問`
- `次に強化するページ` -> `次の改善`
- `自社が主に引用された` のような結果文は残してよい
- ただし、その直下で `どの質問タイプでそうなったか` を必ず補足する
- `9件` のような URL 件数は first view の大見出しに使わない
- `回答試行ベースで見ています` を microcopy として明示する

## Color And Surface Rules

- dark brown fill card は使わない
- 3 cards は同じ light surface family に揃える
- accent は `notecode` / `aio2-main` と同系の orange-brown token を使う
- eyebrow や sub label は背景との contrast を優先し、薄い brown on dark brown を避ける
- `自社系 / 外部系 / 比較系` の semantic color は維持してよいが、base surface は統一する

## Progress And Logging Plan

### Runtime Copy

分析中は次を固定表示する。

- `分析中 n/N`
- `元質問 x/y`
- `拡張質問 x/y`
- `繰り返し x/y`

加えて、質問文または short label を 1 行で見せる。

### Loading Design

- spinner 単体ではなく progress text を併記する
- step が進んだことが分かるよう、文言を都度更新する
- 待機が長い provider では `回答待ち` と `集計中` を分けて見せてもよい

### Logging

確認対象ログ:

- `logs/phase_ui_run_stdout_*.log`
- `logs/verify_current_server.log`

確認観点:

- deleted client error の再発有無
- progress copy が step ごとに更新されているか
- 完了前に spinner が消えていないか

## File Ownership

- `analysis_core/metrics.py`
  - 試行ベース rollup の正本
- `ui/result_story_builders.py`
  - card copy と試行ベース指標の文言
- `ui/result_cards.py`
  - 3 cards の再構成
  - heatmap / bubble / strip の配置
- `ui/styles.py`
  - hierarchy contrast
  - fold ごとの優先度差
  - mobile 圧縮
- `ui/styles.py`
  - contrast
  - suite palette
  - visualization token
- `app.py`
  - progress copy
  - spinner label
  - 実行中の UI status
- `ui/detail_views.py`
  - raw 件数、URL 件数、具体質問例の退避先

## Phase Order

### Phase 1: Metric Contract Freeze

やること:

- first view で使う指標を `試行ベース` に固定
- URL 件数と試行ベースの率を別レイヤーへ分離

### Phase 1.5: Nielsen Load Reduction

やること:

- first view の主役以外を弱くする
- 1 card あたりの行数・chip 数を削る
- mobile での縦積み負荷を下げる

完了条件:

- desktop を `中程度 -> 低め`
- mobile を `やや高い -> 中程度`

確認方法:

- 実ブラウザ screenshot 比較
- PC / mobile の fold 単位レビュー
- 5 秒レビューで `主役` を即答できるか確認
- detail 側へ退避する数値を決める

完了条件:

- first view に母数違いの数字が並ばない
- copy 上で `回答試行ベース` が明示される

### Phase 2: Information Architecture Rewrite

やること:

- 3 cards を `今回の結論 / 引用されやすい質問 / 次の改善` に固定
- 文章構造を再整理
- raw URL 列挙を first view から追い出す

完了条件:

- 初見で `何が起きたか / なぜか / 次に何をするか` が読める

### Phase 3: Visualization Layer

やること:

- question type heatmap を追加
- citation opportunity bubble strip を追加
- page opportunity strip を追加

完了条件:

- 中央 card が文章を読まずに理解できる
- 右 card が文字量過多にならない

### Phase 4: Progress UX

やること:

- spinner と progress copy を一体化
- step text を更新
- 長時間 run の待機理由を短く表示

完了条件:

- `止まっているように見える` 状態が減る
- latest log と画面表示が矛盾しない

### Phase 5: Detail Rebalance

やること:

- first view から退避した件数や URL 情報を detail に移す
- 実例スナップショットを必要最小限で追加

完了条件:

- first view は軽い
- detail では根拠確認もできる

## Verification Plan

### UX Verification

- 94% と 9件のような誤読が消えている
- 質問傾向が文章なしでも読める
- `次に何をすべきか` が 5 秒以内に理解できる

### Functional Verification

- latest run で試行ベース集計が崩れない
- single question / expanded question の両方で copy が破綻しない
- progress copy が run 完了まで更新される

### Technical Verification

- `.venv\Scripts\python.exe -m py_compile ...`
- `.venv\Scripts\python.exe -c "import app"`
- `http://127.0.0.1:8083/` の HTTP 200
- 必要なら Playwright で desktop / mobile の screenshot 比較

## Non Goals

- アルゴリズム詳細の対外開示
- citation 判定ロジックそのものの再設計
- SaaS 課金や権限設計
- 外部 scheduler への分離

## Implementation Note For Next Window

別ウインドウでは次の順で着手する。

1. `analysis_core/metrics.py` と `ui/result_story_builders.py` の contract 確認
2. `ui/result_cards.py` で card IA を固定
3. `ui/styles.py` で suite palette と visualization token を整理
4. `app.py` で progress copy を再確認
5. 最後に `ui/detail_views.py` へ raw 情報を退避

この順なら、数字の意味を先に固めてから見た目を載せられる。
