# Kotomegane UI Reduction Implementation Plan 2026-04-14

## Purpose

この文書は、`kotomegane` の現行 UI を

- `不要な説明を削る`
- `入力を最上段の主役に戻す`
- `分析結果の価値だけを先に見せる`
- `TECHIE HUB` から遷移した 3 サービスの見た目を色でも連続させる

ための実装用 plan です。

今回の計画は、見た目の追加ではなく `削減` と `優先順位の修正` を主目的にする。

## Fixed Decision

- `C:\tetie\techie-hub\start.bat` から 3 サービスへ入る前提を優先する
- 色は `techie-hub` と同じ suite palette に揃える
- `kotomegane` 固有の色差は今回の phase では極小化する
- first view は `質問を入れる -> 実行する` を最優先にする
- `前回の観測サマリー` や `プロダクト間の説明` は first view の主役にしない
- `比較` は補助機能として残すが、主役にはしない
- `論点のつながり` は価値が立つまで main surface に戻さない

## Product Interpretation

この画面の役割は次に固定する。

- 入力した質問に対して
- `AI が誰を先に取り上げたか`
- `何を主な根拠にしたか`
- `次に何を足せば変わりそうか`

を短時間で判断する。

`TECHIE SUITE の関係説明` や `改善への handoff 説明` は正しいが、
この画面で最初に読む情報ではない。

## Design Rule For This Phase

### 1. Color Unification

- shell、背景、card、CTA、active state は `techie-hub` と同じ暖色系 token を使う
- `kotomegane` だけ背景色やブランド色を変えて現在地を伝えようとしない
- 現在地は `サービス名` と `H1` と nav state で伝える
- 状態色だけは用途に応じて維持する
  - `自社系`
  - `比較系`
  - `外部系`

### 2. Input First

- first view の主役は `入力カード` だけにする
- 前回の観測結果は、入力より上に置かない
- 実行前に読ませる説明は 2 行以内に抑える

### 3. Remove Suite Meta

- `TECHIE SUITE`
- `コトメガネは見る、コトミガキは直す`
- `活かす材料`

は main hero から外す。

必要なら将来、`help` や `about` の折りたたみへ移す。

### 4. Scope To User Value

first view で見る価値は次だけに絞る。

1. 何を確認したいか
2. 何を入れればよいか
3. 実行後に何が分かるか

## Problems To Solve

### 1. Competing First Impressions

現状は次が同時に見えている。

- suite の説明
- 前回サマリー
- 入力
- 実行状態

これにより、初見ユーザーが `まず入力する画面` として認識しにくい。

### 2. Ambiguous Labels

現状の文言には次の曖昧さがある。

- `自社優勢`
  - 何と比べて優勢なのか不明
- `今回の根拠`
  - 何が根拠として採用されたのか不明
- `ブランド名`
  - 法人名、屋号、サービス名との関係が不明
- `論点のつながり`
  - 見たあと何に使うのか不明

### 3. Overflow Risk

長い質問、URL、固有名詞、複数語チップが card 幅を超える可能性があり、
main card の読みやすさを崩す。

## Target Information Architecture

## First View

上から次の順に固定する。

1. 共通 top shell
2. 小さい hero
   - サービス名
   - 一文の価値説明
3. 入力 section
   - `質問`
   - `自社URL`
   - `名称（任意）`
   - `重点テーマ（任意）`
   - `比較対象（任意・折りたたみ）`
   - `分析を実行`
4. 実行後 only の result summary
   - `AI が先に取り上げた相手`
   - `主な引用元`
   - `次に足すもの`

## Things Removed From First View

- `TECHIE SUITE` 説明 box
- `活かす材料`
- `直近の観測サマリー` 4 cards
- `論点のつながり`
- 実装上の内部説明が長い補助文

## Input Specification

### Required Fields

- `質問`
- `自社URL`

### Optional Fields

- `名称`
  - 旧 `ブランド名`
- `重点テーマ`
  - 旧 `目立ちたい領域`
- `比較対象`

### Copy Rules

- `ブランド名` は `名称` に変更する
- 必須から外す
- placeholder は `会社名、サービス名、屋号など` にする
- `自社の情報` は `自社URLと補足` に変更する
- `知りたい質問` は `質問` に短縮する
- 入力例は残してよいが、折りたたみのままにする

## Result Summary Specification

first result summary は 3 cards に固定する。

### Card 1

- title: `AIが先に取り上げた相手`
- shown after run only
- label candidate:
  - `自社が主に引用された`
  - `自社も出るが並走`
  - `外部が主に引用された`
  - `自社は確認できず`

`自社優勢 / 自社あり / 外部サイト優勢 / 未露出` は内部判定語としては残してよいが、
first view の main copy には使わない。

### Card 2

- title: `主な引用元`
- 旧 `今回の根拠`
- URL の列挙ではなく
  - `自社引用`
  - `比較対象引用`
  - `外部引用`

の意味を先に読ませる。

### Card 3

- title: `次に足すもの`
- 旧方針を維持してよい
- ただし `今回の根拠` と論理的に接続する短文に揃える

## Items To Defer

### Defer From Main Surface

- `論点のつながり`
- `共起`
- `比較候補`
- suite handoff explanation
- 詳細な citation breakdown

### Move To Detail If Kept

- `論点のつながり`
- `比較候補`
- topic chips の詳細
- 候補URL / 判定保留

## Copy Replacement Table

- `ブランド名` -> `名称`
- `自社の情報` -> `自社URLと補足`
- `目立ちたい領域` -> `重点テーマ`
- `今回の根拠` -> `主な引用元`
- `自社優勢` -> `自社が主に引用された`
- `自社あり` -> `自社も出るが並走`
- `外部サイト優勢` -> `外部が主に引用された`
- `未露出` -> `自社は確認できず`

## Overflow Prevention Rules

全 card / label / chip / input で共通に次を適用する。

- flex child は `min-width: 0`
- card 内本文は `overflow-wrap: anywhere`
- 通常文は `word-break: break-word`
- URL だけ `word-break: break-all`
- card の主値は 2 行まで許容し、必要なら clamp する
- chip は `max-width: 100%` とし、必要時は改行または省略を許す
- 長い質問文は 2 行以上に自然折返しできるようにする

## File Ownership

- `app.py`
  - hero の削減
  - input section の順序変更
  - input label 文言変更
- `ui/result_cards.py`
  - first result summary の 3 card 化
  - `直近の観測サマリー` の撤去または下段移動
- `ui/result_story_builders.py`
  - main copy の比較軸つき文言へ変更
- `ui/detail_views.py`
  - `今回の根拠` など詳細文言の整合
- `ui/runtime_copy_builders.py`
  - onboarding 文言の必須条件更新
- `ui/styles.py`
  - suite 共通 palette への統一
  - overflow / clamp / wrap rule の共通化

## Implementation Order

### Phase 1: Visual Reduction

対象:
- `app.py`
- `ui/styles.py`

実装:
- hero 右側の suite box を削除
- `活かす材料` を削除
- hero 高さを縮める
- 色 token を suite 共通に寄せる

完了条件:
- first view で入力 card が最も大きく見える

### Phase 2: Input Rewrite

対象:
- `app.py`
- `ui/runtime_copy_builders.py`

実装:
- `ブランド名` を `名称` へ変更
- `名称` を任意へ変更
- `自社の情報` を `自社URLと補足` へ変更
- 質問欄を最上部の主役へ再配置

完了条件:
- 必須は `質問 / 自社URL` だけになる

### Phase 3: Result Label Rewrite

対象:
- `ui/result_cards.py`
- `ui/result_story_builders.py`
- `ui/detail_views.py`

実装:
- `自社優勢` などの user-facing main copy を置換
- `今回の根拠` を `主な引用元` に変更
- first summary を 3 card へ絞る

完了条件:
- `何と比べてどうなのか` が card 文言だけで読める

### Phase 4: Remove Weak Value Blocks

対象:
- `ui/result_cards.py`
- 必要なら `app.py`

実装:
- `直近の観測サマリー`
- `論点のつながり`
- `比較候補`

を first view から外す

完了条件:
- 実行前画面で `前回の分析` が主役に見えない

### Phase 5: Overflow Hardening

対象:
- `ui/styles.py`
- 必要なら card renderer 群

実装:
- common overflow utility を追加
- 長文 question / URL / chip の崩れを防ぐ
- desktop / mobile の折返しを確認

完了条件:
- desktop / mobile 両方で card から文字がはみ出さない

## Verification

- desktop first view screenshot
- mobile first view screenshot
- long question を入れた screenshot
- 長い URL を含む result screenshot
- `techie-hub` から遷移したときの top shell / CTA / 背景の連続感確認

## Stop Rules

- 削減 phase 中に新しい分析カードを増やさない
- suite 関係の説明を hero に戻さない
- `比較` を主役に戻さない
- 文言を短くする代わりに意味を曖昧にしない

## Success Criteria

- first view の主役が入力になっている
- `質問` が最初の視線で読める
- 実行後の first summary が 3 つ以内に収まる
- `自社優勢` のような比較軸不明語が main copy に残っていない
- `名称` は任意入力で使える
- 3 サービスをまたいでも色の違和感が小さい
- 長文で card レイアウトが崩れない

## Read With This Plan

- `AGENTS.md`
- `WORKLOG.md`
- `ALGORITHM.md`
- `docs/DOC_STATUS.md`
- `docs/UI_VALUE_REDESIGN_PLAN_2026-04-10.md`
- `C:\tetie\techie-hub\DESIGN_SYSTEM_PLAN_2026-04-01.md`
